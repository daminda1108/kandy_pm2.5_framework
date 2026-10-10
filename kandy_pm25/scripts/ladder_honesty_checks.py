"""ladder_honesty_checks.py -- do the ladder's headline effects survive the design choices a
reviewer would question? (verification pass 2026-09-25, items A7, B2, B3)

Production ``ladder()`` makes three choices that flatter it or tie it to one draw:
  B2  the affine (and background) coefficients are fitted over the SAME period that is scored;
  B3  the shrinkage weight w is chosen against the HELD-OUT stations -- the scoring target --
      on 80 % subsamples of the scored days. A city without a dense network could not do this;
  A7  every city is scored on ONE station split (one seed picks the held-out set and the order).

Variants, all on one Bud0c fit (leave-one-city-out, identical to production):
  prod       production ladder, scored on all days                         (reproduces ladder())
  prod_T     production ladder, scored on the LATER half of days only       (comparison for temporal)
  temporal   coefficients AND w fitted on the EARLIER half, scored on the later half
  no_shrink  w = 1 at every rung: no use of the held-out stations at all
  loco_w     w = the median production w of the OTHER cities, per rung

Headline effects reported for each (median over cities, city bootstrap):
  first2 = gain Bud0->Bud1, s36 = gain Bud1->Bud2, bg = gain Bud2->Bud3,
  bg_minus_first2 (paired within city), pooled and deep-tropical.
Then A7: the prod variant over 20 split seeds.

Usage: python scripts/ladder_honesty_checks.py [--stream maiac|ghap] [--seeds 20]
Out:   data/processed/modular/verify_2026-09-25/honesty_{stream}.csv / .json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
warnings.filterwarnings("ignore")

from ladder_frames import SEED, build_bud0_frame, fit_loco           # noqa: E402
from modular_validation_all import _affine, ladder                    # noqa: E402
from src.modular import shrinkage as sh                               # noqa: E402
from src.modular.city_meta import city_meta                           # noqa: E402

VERIFY = REPO / "data" / "processed" / "modular" / "verify_2026-09-25"
RUNGS = ("Bud1", "Bud2", "Bud3")


def rung_predictions(city, st, bud0, seed, calib_mask_fn=None):
    """Raw (unshrunk) rung predictions, as in ladder(). ``calib_mask_fn(index) -> bool mask``
    restricts the days used to FIT the affine/background coefficients."""
    rng = np.random.default_rng(seed)
    ids = np.array(sorted(st.station_id.unique()))
    rng.shuffle(ids)
    n_hold = max(3, len(ids) // 3)
    held, pool = ids[:n_hold], ids[n_hold:]
    roles = {"b1": pool[:2], "b2": pool[:min(6, len(pool))], "reg": pool[min(6, len(pool)):]}
    if not len(roles["reg"]):
        return None
    daily = lambda k: st[st.station_id.isin(k)].groupby("date").pm25.mean()
    target = daily(held).rename("obs")
    p0 = bud0[bud0.city == city].set_index("date").bud0
    fr = pd.concat([p0, target], axis=1).dropna().sort_index()
    if len(fr) < 120:
        return None
    sel = (lambda j: j[calib_mask_fn(j.index)]) if calib_mask_fn else (lambda j: j)

    pred = {"Bud0": fr.bud0.to_numpy()}
    for rung, key in (("Bud1", "b1"), ("Bud2", "b2")):
        j = sel(pd.concat([p0, daily(roles[key]).rename("fit")], axis=1).dropna())
        a, b = _affine(j.fit.to_numpy(), j.bud0.to_numpy())
        pred[rung] = a + b * fr.bud0.to_numpy()
    bg = st[st.station_id.isin(roles["reg"])].groupby("date").pm25.quantile(0.10).rename("bg")
    j = sel(pd.concat([p0, bg, daily(roles["b2"]).rename("fit")], axis=1).dropna())
    if len(j) <= 60:
        return None
    A = np.vstack([np.ones(len(j)), j.bud0.to_numpy(), j.bg.to_numpy()]).T
    c, *_ = np.linalg.lstsq(A, j.fit.to_numpy(), rcond=None)
    k = pd.concat([p0, bg], axis=1).reindex(fr.index)
    # production fills missing background days with the mean over the SCORED days (ladder());
    # the out-of-period variant may only use the fitting days.
    fill = j.bg.mean() if calib_mask_fn else k.bg.mean()
    pred["Bud3"] = c[0] + c[1] * k.bud0.to_numpy() + c[2] * k.bg.fillna(fill).to_numpy()
    return fr, pred


def chain(fr, pred, seed, w_mode, w_given=None, choose_mask=None, score_mask=None):
    """Shrink rung by rung. w_mode: 'cv' (production), 'one', 'given'."""
    obs = fr.obs.to_numpy()
    days = fr.index.astype(str).to_numpy()
    cm = np.ones(len(obs), bool) if choose_mask is None else choose_mask
    smk = np.ones(len(obs), bool) if score_mask is None else score_mask
    rmse = lambda x: float(np.sqrt(np.mean((x[smk] - obs[smk]) ** 2)))
    cur = pred["Bud0"]
    out = {"rmse_Bud0": rmse(cur)}
    for r in RUNGS:
        if w_mode == "cv":
            w = sh.optimal_weight(cur[cm], pred[r][cm], obs[cm], groups=days[cm], seed=seed).w
        elif w_mode == "one":
            w = 1.0
        else:
            w = float(w_given[r])
        cur = sh.combine(cur, pred[r], w)
        out[f"rmse_{r}"], out[f"w_{r}"] = rmse(cur), w
    return out


def effects(d: pd.DataFrame, boot: int, rng) -> dict:
    g = lambda a, b: 100 * (d[a] - d[b]) / d[a]
    cols = {"first2": g("rmse_Bud0", "rmse_Bud1"), "s36": g("rmse_Bud1", "rmse_Bud2"),
            "bg": g("rmse_Bud2", "rmse_Bud3")}
    cols["bg_minus_first2"] = cols["bg"] - cols["first2"]
    res = {}
    for stratum, mask in (("pooled", np.ones(len(d), bool)),
                          ("deep_tropical", (d.band == "deep_tropical").to_numpy())):
        for k, v in cols.items():
            x = v.to_numpy()[mask]; x = x[np.isfinite(x)]
            if len(x) < 4:
                continue
            m = np.median(x[rng.integers(0, len(x), (boot, len(x)))], axis=1)
            res[f"{stratum}.{k}"] = dict(median=round(float(np.median(x)), 2),
                                         lo=round(float(np.percentile(m, 2.5)), 2),
                                         hi=round(float(np.percentile(m, 97.5)), 2), n=len(x))
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stream", choices=("maiac", "ghap"), default="maiac")
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--boot", type=int, default=4000)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)
    VERIFY.mkdir(parents=True, exist_ok=True)

    print(f"=== ladder honesty checks, {a.stream} ===")
    st, p, met, geo_f, sat_feats = build_bud0_frame(a.stream)
    b0 = fit_loco(p, met + geo_f + sat_feats, seed=SEED, label="Bud0c")
    meta = city_meta(list(st)).set_index("city")
    cities = [c for c in st if c in set(b0.city)]

    # ── variants on the production split ─────────────────────────────────────────────────
    rows = {v: [] for v in ("prod", "prod_T", "temporal", "no_shrink")}
    prod_w, stash = {}, {}
    for city in cities:
        s, bc = st[city], b0[b0.city == city]
        rp = rung_predictions(city, s, bc, SEED)
        if rp is None:
            continue
        fr, pred = rp
        ref = ladder(city, s, bc, SEED)                      # production, for a parity check
        prod = chain(fr, pred, SEED, "cv")
        assert abs(prod["rmse_Bud3"] - ref["rmse_Bud3"]) < 1e-9, f"parity failed at {city}"
        rows["prod"].append({"city": city, **prod})
        prod_w[city] = {r: prod[f"w_{r}"] for r in RUNGS}
        stash[city] = (fr, pred)

        cut = fr.index[len(fr) // 2]
        early = (fr.index < cut)
        rows["prod_T"].append({"city": city, **chain(fr, pred, SEED, "cv", score_mask=~early)})
        rpt = rung_predictions(city, s, bc, SEED, calib_mask_fn=lambda idx: idx < cut)
        if rpt is not None:
            fr2, pred2 = rpt
            e2 = fr2.index < cut
            rows["temporal"].append({"city": city, **chain(fr2, pred2, SEED, "cv",
                                                           choose_mask=e2, score_mask=~e2)})
        rows["no_shrink"].append({"city": city, **chain(fr, pred, SEED, "one")})
    print(f"    parity with ladder(): OK on {len(rows['prod'])} cities")

    rows["loco_w"] = []
    wdf = pd.DataFrame(prod_w).T
    for city, (fr, pred) in stash.items():
        w_other = wdf.drop(index=city).median()
        rows["loco_w"].append({"city": city, **chain(fr, pred, SEED, "given", w_given=w_other)})

    summary, frames = {"stream": a.stream}, []
    for v, r in rows.items():
        d = pd.DataFrame(r)
        d["band"] = d.city.map(meta.band)
        d["variant"] = v
        frames.append(d)
        summary[v] = effects(d, a.boot, rng)
    print("\n    variant       first2          s36          bg      bg-first2 (paired)   DT bg-first2")
    for v in rows:
        e = summary[v]
        f = lambda k: (f"{e[k]['median']:+6.1f} [{e[k]['lo']:+.1f},{e[k]['hi']:+.1f}]"
                       if k in e else "   --")
        print(f"    {v:<10} {e['pooled.first2']['median']:6.1f} {e['pooled.s36']['median']:10.2f} "
              f"{e['pooled.bg']['median']:10.1f}   {f('pooled.bg_minus_first2')}   "
              f"{f('deep_tropical.bg_minus_first2')}")

    # ── A7: the production ladder over split seeds ────────────────────────────────────────
    print(f"\n[A7] production ladder over {a.seeds} station-split seeds")
    seed_rows = []
    for k in range(a.seeds):
        sd = SEED + 1000 * (k + 1)
        rr = []
        for city in cities:
            r = ladder(city, st[city], b0[b0.city == city], sd)
            if r:
                rr.append(r)
        d = pd.DataFrame(rr)
        d["band"] = d.city.map(meta.band)
        e = effects(d, 1000, rng)
        seed_rows.append({"seed": sd, **{f"{kk}.{q}": vv[q] for kk, vv in e.items()
                                          for q in ("median", "lo", "hi")}})
        print(f"    seed {sd}: first2 {e['pooled.first2']['median']:5.1f}  "
              f"bg-first2 {e['pooled.bg_minus_first2']['median']:+6.1f} "
              f"[{e['pooled.bg_minus_first2']['lo']:+.1f},{e['pooled.bg_minus_first2']['hi']:+.1f}]  "
              f"DT {e['deep_tropical.bg_minus_first2']['median']:+6.1f} "
              f"[{e['deep_tropical.bg_minus_first2']['lo']:+.1f},"
              f"{e['deep_tropical.bg_minus_first2']['hi']:+.1f}]", flush=True)
    sdf = pd.DataFrame(seed_rows)
    agg = {}
    for key in ("pooled.first2", "pooled.s36", "pooled.bg", "pooled.bg_minus_first2",
                "deep_tropical.first2", "deep_tropical.bg", "deep_tropical.bg_minus_first2"):
        m = sdf[f"{key}.median"]
        agg[key] = dict(min=float(m.min()), p10=float(m.quantile(0.1)), median=float(m.median()),
                        p90=float(m.quantile(0.9)), max=float(m.max()),
                        frac_interval_excludes_zero=float(((sdf[f"{key}.lo"] > 0)
                                                           | (sdf[f"{key}.hi"] < 0)).mean()))
    summary["A7_split_seeds"] = agg
    for key, v in agg.items():
        print(f"    {key:<32} median over seeds {v['median']:+6.2f}  range [{v['min']:+.2f}, "
              f"{v['max']:+.2f}]  interval excludes 0 in {100 * v['frac_interval_excludes_zero']:.0f}%")

    pd.concat(frames).to_csv(VERIFY / f"honesty_{a.stream}.csv", index=False)
    sdf.to_csv(VERIFY / f"honesty_seeds_{a.stream}.csv", index=False)
    jp = VERIFY / f"honesty_{a.stream}.json"; tmp = jp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(summary, indent=2), encoding="utf-8"); os.replace(tmp, jp)
    print(f"\n-> {jp}")


if __name__ == "__main__":
    main()
