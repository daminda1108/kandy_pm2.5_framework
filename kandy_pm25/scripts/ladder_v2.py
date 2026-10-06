"""ladder_v2.py -- the redesigned information-budget ladder (docs/redesign_ladder_v2_plan_2026-09-25.md).

What changes from v1 (`modular_validation_all.ladder`), each for a stated reason:
  E1  per-city effect = median over S station splits           (A7: one split moved the headline)
  E2  Bud0c = median prediction over B learner seeds           (A8: one seed moved first-two 11-23 %)
  E3  shrinkage weight CROSS-FITTED: the median w learned on the OTHER cities, per rung
                                                               (B3: v1 chose w against the scoring target)
  E4  static geography from a regular grid in the urban centre (--geo grid; B1)   [needs the grid file]
  E5  station-day valid with >= 18 of 24 hours, equal weight per station  (A6; EPA 40 CFR 50 App. N)
  E6  reconstruction arm (calibration over the scored period) AND prospective arm (calibration and
      w on the earlier half, scored on the later half)
  E7  background = "same-network background series" (naming; the construction is unchanged)
  E8  moderator: cluster-bootstrapped median regression of each per-city effect on |latitude| and
      reference fraction jointly
  E9  primary loss RMSE; secondaries tail RMSE (obs >= the city's 90th percentile) and balanced
      exceedance error at 15 ug/m3
  E10 two-level cluster bootstrap primary; city bootstrap beside it

Parity: with --splits 1 --bag 1 --w cv --no-complete --geo sites the reconstruction arm reproduces
v1 ladder() exactly (asserted by scripts/tests/test_ladder_v2.py).

Usage: python scripts/ladder_v2.py --stream maiac [--splits 21] [--bag 5] [--w crossfit]
Out:   data/processed/modular/ladder_v2/{tag}_percity.csv, {tag}_splits.csv, {tag}_summary.json
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

from ladder_frames import SEED, build_bud0_frame, fit_loco            # noqa: E402
from modular_validation_all import _affine                             # noqa: E402
from src.modular import shrinkage as sh                                # noqa: E402
from src.modular.city_meta import city_meta                            # noqa: E402

OUTD = REPO / "data" / "processed" / "modular" / "ladder_v2"
RUNGS = ("Bud1", "Bud2", "Bud3")
MIN_HOURS = 18
WHO_24H = 15.0
TAIL_Q = 0.90


# ── data ──────────────────────────────────────────────────────────────────────────────────
def complete_station_days(s: pd.DataFrame) -> pd.DataFrame:
    """E5: one row per station-day with >= 18 valid hours, value = the station's daily mean."""
    g = s.groupby(["station_id", "date"]).pm25.agg(["mean", "size"]).reset_index()
    return g[g["size"] >= MIN_HOURS].rename(columns={"mean": "pm25"})[["station_id", "date", "pm25"]]


def load(stream: str, complete: bool, geo: str, cnemc_drivers: str = "v2"):
    st, p, met, geo_f, sat_feats = build_bud0_frame(stream, verbose=True, cnemc_drivers=cnemc_drivers)
    if complete:
        st = {c: complete_station_days(s) for c, s in st.items()}
        cc = pd.concat([s.groupby("date").pm25.mean().rename("pm25_c").reset_index().assign(city=c)
                        for c, s in st.items()], ignore_index=True)
        cc["date"] = pd.to_datetime(cc.date)
        p = p.merge(cc, on=["city", "date"], how="inner")
        p["pm25_city"] = p.pop("pm25_c")
    if geo == "grid":
        gp = REPO / "data" / "processed" / "modular" / "static_geo_grid.csv"
        if not gp.exists():
            raise SystemExit(f"--geo grid needs {gp} (E4 grid pipeline not yet run)")
        g = pd.read_csv(gp); g["city"] = g.city.astype(str)
        missing = set(p.city) - set(g.city)
        if missing:
            raise SystemExit(f"grid geography missing for {sorted(missing)}")
        p = p.drop(columns=geo_f).merge(g[["city", *geo_f]], on="city", how="left")
    return st, p, met, geo_f, sat_feats


def bagged_bud0(p, feats, bag):
    """E2: median prediction over `bag` learner seeds (the first is the production seed)."""
    fits = [fit_loco(p, feats, seed=(SEED if k == 0 else k), label=f"Bud0c seed {k}")
            for k in range(bag)]
    b0 = fits[0][["city", "date"]].copy()
    for f in fits[1:]:
        assert (f[["city", "date"]].to_numpy() == b0[["city", "date"]].to_numpy()).all()
    b0["bud0"] = np.median(np.vstack([f.bud0.to_numpy() for f in fits]), axis=0)
    return b0


# ── one city, one split ───────────────────────────────────────────────────────────────────
def rungs(city, st, bud0, seed, calib_before=None):
    """Raw rung predictions exactly as v1 ladder(); `calib_before` restricts coefficient fitting to
    days before that date (prospective arm). Returns (fr, pred, cut) or None."""
    rng = np.random.default_rng(seed)
    ids = np.array(sorted(st.station_id.unique()))
    rng.shuffle(ids)
    n_hold = max(3, len(ids) // 3)
    held, pool = ids[:n_hold], ids[n_hold:]
    roles = {"b1": pool[:2], "b2": pool[:min(6, len(pool))], "reg": pool[min(6, len(pool)):]}
    daily = lambda k: st[st.station_id.isin(k)].groupby("date").pm25.mean()
    p0 = bud0[bud0.city == city].set_index("date").bud0
    fr = pd.concat([p0, daily(held).rename("obs")], axis=1).dropna().sort_index()
    if len(fr) < 120:
        return None
    sel = (lambda j: j[j.index < calib_before]) if calib_before is not None else (lambda j: j)
    pred = {"Bud0": fr.bud0.to_numpy()}
    for r, key in (("Bud1", "b1"), ("Bud2", "b2")):
        j = sel(pd.concat([p0, daily(roles[key]).rename("fit")], axis=1).dropna())
        a, b = _affine(j.fit.to_numpy(), j.bud0.to_numpy())
        pred[r] = a + b * fr.bud0.to_numpy()
    if len(roles["reg"]):
        bg = st[st.station_id.isin(roles["reg"])].groupby("date").pm25.quantile(0.10).rename("bg")
        j = sel(pd.concat([p0, bg, daily(roles["b2"]).rename("fit")], axis=1).dropna())
        if len(j) > 60:
            A = np.vstack([np.ones(len(j)), j.bud0.to_numpy(), j.bg.to_numpy()]).T
            c, *_ = np.linalg.lstsq(A, j.fit.to_numpy(), rcond=None)
            k = pd.concat([p0, bg], axis=1).reindex(fr.index)
            fill = j.bg.mean() if calib_before is not None else k.bg.mean()   # v1 parity
            pred["Bud3"] = c[0] + c[1] * k.bud0.to_numpy() + c[2] * k.bg.fillna(fill).to_numpy()
    return fr, pred


def losses(x, obs):
    e = x - obs
    out = {"rmse": float(np.sqrt(np.mean(e ** 2)))}
    m = obs >= np.quantile(obs, TAIL_Q)
    out["tail"] = float(np.sqrt(np.mean(e[m] ** 2))) if m.sum() >= 5 else np.nan
    yt, yp = obs >= WHO_24H, x >= WHO_24H
    if yt.sum() < 5 or (~yt).sum() < 5:
        out["exceed"] = np.nan
    else:
        out["exceed"] = float(1 - 0.5 * ((yp & yt).sum() / yt.sum() + ((~yp) & (~yt)).sum() / (~yt).sum()))
    return out


def chain(fr, pred, seed, w_mode, w_given=None, choose=None, score=None):
    """Shrink rung by rung; return losses at each rung and the weights used."""
    obs = fr.obs.to_numpy()
    days = fr.index.astype(str).to_numpy()
    cm = np.ones(len(obs), bool) if choose is None else choose
    sm = np.ones(len(obs), bool) if score is None else score
    cur = pred["Bud0"]
    row = {f"Bud0_{k}": v for k, v in losses(cur[sm], obs[sm]).items()}
    for r in RUNGS:
        if r not in pred:
            row.update({f"{r}_{k}": np.nan for k in ("rmse", "tail", "exceed")}); row[f"w_{r}"] = np.nan
            continue
        if w_mode == "cv":
            w = sh.optimal_weight(cur[cm], pred[r][cm], obs[cm], groups=days[cm], seed=seed).w
        elif w_mode == "one":
            w = 1.0
        else:
            w = float(w_given[r])
        cur = sh.combine(cur, pred[r], w)
        row.update({f"{r}_{k}": v for k, v in losses(cur[sm], obs[sm]).items()})
        row[f"w_{r}"] = w
    return row


# ── effects ───────────────────────────────────────────────────────────────────────────────
def add_effects(d: pd.DataFrame) -> pd.DataFrame:
    for L in ("rmse", "tail", "exceed"):
        g = lambda a, b: 100 * (d[f"{a}_{L}"] - d[f"{b}_{L}"]) / d[f"{a}_{L}"]
        d[f"first2_{L}"] = g("Bud0", "Bud1")
        d[f"s36_{L}"] = g("Bud1", "Bud2")
        d[f"bg_{L}"] = g("Bud2", "Bud3")
        d[f"bgm2_{L}"] = d[f"bg_{L}"] - d[f"first2_{L}"]
    # a parent loss of exactly zero (possible for the exceedance error) makes a % gain undefined
    return d.replace([np.inf, -np.inf], np.nan)


def boot_city(v, rng, n):
    return np.median(v[rng.integers(0, len(v), (n, len(v)))], axis=1)


def boot_cluster(v, grp, rng, n):
    keys = np.unique(grp)
    idx = {k: np.flatnonzero(grp == k) for k in keys}
    out = np.empty(n)
    for i in range(n):
        take = np.concatenate([rng.choice(idx[k], len(idx[k]), replace=True)
                               for k in rng.choice(keys, len(keys), replace=True)])
        out[i] = np.median(v[take])
    return out


def summarise(C: pd.DataFrame, rng, nboot: int) -> dict:
    out = {}
    cols = [c for c in C.columns if c.split("_")[0] in ("first2", "s36", "bg", "bgm2")]
    for stratum, sub in (("pooled", C), ("deep_tropical", C[C.band == "deep_tropical"])):
        for col in cols:
            s = sub[[col, "cluster"]].dropna()
            if len(s) < 4:
                continue
            v, g = s[col].to_numpy(), s.cluster.to_numpy()
            bc, bk = boot_city(v, rng, nboot), boot_cluster(v, g, rng, nboot)
            out[f"{stratum}.{col}"] = dict(
                n=int(len(v)), n_clusters=int(len(np.unique(g))), median=float(np.median(v)),
                city=[float(np.percentile(bc, 2.5)), float(np.percentile(bc, 97.5))],
                cluster=[float(np.percentile(bk, 2.5)), float(np.percentile(bk, 97.5))],
                positive=int((v > 0).sum()))
    return out


def moderator(C: pd.DataFrame, col: str, rng, nboot: int) -> dict:
    """E8: median regression of a per-city effect on |lat| and reference fraction, jointly;
    percentile intervals from a two-level cluster bootstrap."""
    import statsmodels.formula.api as smf
    d = C[[col, "abs_lat", "frac_reference", "cluster"]].dropna().rename(columns={col: "y"})
    import warnings as _w
    from statsmodels.tools.sm_exceptions import IterationLimitWarning
    nonconv = [0]

    def fit(x):
        with _w.catch_warnings(record=True) as ws:
            _w.simplefilter("always", IterationLimitWarning)
            r = smf.quantreg("y ~ abs_lat + frac_reference", x).fit(q=0.5, max_iter=20000).params
        if any(issubclass(w.category, IterationLimitWarning) for w in ws):
            nonconv[0] += 1
        return r
    est = fit(d)
    est_nonconv = nonconv[0]
    keys = d.cluster.unique()
    idx = {k: d.index[d.cluster == k] for k in keys}
    bs = []
    for _ in range(nboot):
        take = np.concatenate([rng.choice(idx[k], len(idx[k]), replace=True)
                               for k in rng.choice(keys, len(keys), replace=True)])
        try:
            bs.append(fit(d.loc[take]))
        except Exception:                                                   # noqa: BLE001
            continue
    B = pd.DataFrame(bs)
    return {k: dict(est=float(est[k]), lo=float(B[k].quantile(0.025)), hi=float(B[k].quantile(0.975)),
                    n_boot=int(len(B)))
            for k in ("abs_lat", "frac_reference")} | {"n": int(len(d)),
            "point_fit_converged": est_nonconv == 0,
            "bootstrap_nonconverged": int(nonconv[0] - est_nonconv)}


# ── main ──────────────────────────────────────────────────────────────────────────────────
def run(stream="maiac", splits=21, bag=5, w_mode="crossfit", complete=True, geo="sites",
        nboot=4000, prospective=True, verbose=True, cnemc_drivers="v2",
        frame=None, meta=None, score_cities=None):
    """frame/meta/score_cities are used by ladder_v2_confirm.py: `frame` is a prebuilt
    (st, p, met, geo_f, sat_feats) for the discovery + confirmation union, `meta` its per-city
    band/cluster/frac_reference/lat, and summaries cover `score_cities` only. Leave-one-city-out
    fitting and weight cross-fitting still use every city in the frame."""
    st, p, met, geo_f, sat_feats = frame if frame is not None else load(stream, complete, geo,
                                                                         cnemc_drivers)
    b0 = bagged_bud0(p, met + geo_f + sat_feats, bag)
    meta = meta if meta is not None else city_meta(list(st)).set_index("city")
    seeds = [SEED] + [SEED + 1000 * (k + 1) for k in range(splits - 1)]
    cities = [c for c in st if c in set(b0.city)]

    # pass 1: raw rungs for every city x split (and each city's OWN cv weights, used only to
    # cross-fit weights for OTHER cities -- never for itself)
    cache, own_w = {}, []
    for c in cities:
        for sd in seeds:
            rr = rungs(c, st[c], b0, sd)
            if rr is None:
                continue
            fr, pred = rr
            cache[(c, sd)] = (fr, pred)
            if w_mode == "crossfit":
                row = chain(fr, pred, sd, "cv")
                own_w.append({"city": c, **{r: row[f"w_{r}"] for r in RUNGS}})
    W = pd.DataFrame(own_w).set_index("city") if own_w else None

    rows = []
    for (c, sd), (fr, pred) in cache.items():
        wg = W.drop(index=c).median() if W is not None else None       # E3: other cities only
        rec = chain(fr, pred, sd, w_mode, w_given=wg)
        rows.append({"city": c, "seed": sd, "arm": "reconstruction", **rec})
        if prospective:
            cut = fr.index[len(fr) // 2]
            rp = rungs(c, st[c], b0, sd, calib_before=cut)
            if rp is not None:
                fr2, pred2 = rp
                late = (fr2.index >= cut)
                if w_mode == "cv":
                    rec2 = chain(fr2, pred2, sd, "cv", choose=~late, score=late)
                else:
                    rec2 = chain(fr2, pred2, sd, w_mode, w_given=wg, score=late)
                rows.append({"city": c, "seed": sd, "arm": "prospective", **rec2})
    S = add_effects(pd.DataFrame(rows))

    res = {"config": dict(stream=stream, splits=splits, bag=bag, w_mode=w_mode, complete18=complete,
                          geo=geo, nboot=nboot, cities=len(cities), cnemc_drivers=cnemc_drivers,
                          scored=(len(score_cities) if score_cities is not None else len(cities)))}
    rng = np.random.default_rng(SEED)
    percity = {}
    for arm, sub in S.groupby("arm"):
        eff = [c for c in S.columns if c.split("_")[0] in ("first2", "s36", "bg", "bgm2")]
        C = sub.groupby("city")[eff].median()
        C["n_splits"] = sub.groupby("city").size()
        C = C.join(meta[["band", "cluster", "frac_reference", "lat"]])
        C["abs_lat"] = C.lat.abs()
        if score_cities is not None:
            C = C[C.index.isin(set(score_cities))]
        percity[arm] = C
        res[arm] = summarise(C, rng, nboot)
        res[arm]["moderator.bgm2_rmse"] = moderator(C.reset_index(), "bgm2_rmse", rng,
                                                     max(500, nboot // 4))
    return S, percity, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stream", choices=("maiac", "ghap"), default="maiac")
    ap.add_argument("--splits", type=int, default=21)
    ap.add_argument("--bag", type=int, default=5)
    ap.add_argument("--w", choices=("crossfit", "cv", "one"), default="crossfit")
    ap.add_argument("--no-complete", action="store_true")
    ap.add_argument("--geo", choices=("sites", "grid"), default="sites")
    ap.add_argument("--boot", type=int, default=4000)
    ap.add_argument("--no-prospective", action="store_true")
    ap.add_argument("--cnemc-drivers", choices=("v2", "pull_city", "met_raw"), default="v2",
                    help="v2 = every city from drivers_v2 (fixed pull); met_raw = v1")
    a = ap.parse_args()
    S, percity, res = run(a.stream, a.splits, a.bag, a.w, not a.no_complete, a.geo, a.boot,
                          not a.no_prospective, cnemc_drivers=a.cnemc_drivers)
    tag = (f"{a.stream}_s{a.splits}_b{a.bag}_{a.w}_{'c18' if not a.no_complete else 'allh'}_{a.geo}"
           f"_{ {'v2': 'dv2', 'pull_city': 'pc', 'met_raw': 'mr'}[a.cnemc_drivers] }")
    OUTD.mkdir(parents=True, exist_ok=True)
    S.to_csv(OUTD / f"{tag}_splits.csv", index=False)
    for arm, C in percity.items():
        C.to_csv(OUTD / f"{tag}_percity_{arm}.csv")
    jp = OUTD / f"{tag}_summary.json"; tmp = jp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(res, indent=2), encoding="utf-8"); os.replace(tmp, jp)

    for arm in ("reconstruction", "prospective"):
        if arm not in res:
            continue
        print(f"\n=== {tag} | {arm} ===")
        print(f"    {'effect':<26}{'n':>3}{'median':>9}{'city 95%':>20}{'cluster 95%':>20}")
        for k, v in res[arm].items():
            if k.startswith("moderator"):
                continue
            print(f"    {k:<26}{v['n']:>3}{v['median']:>+9.2f}   [{v['city'][0]:+7.2f},{v['city'][1]:+7.2f}]"
                  f"   [{v['cluster'][0]:+7.2f},{v['cluster'][1]:+7.2f}]")
        m = res[arm]["moderator.bgm2_rmse"]
        print(f"    moderator (bg - first2 ~ |lat| + ref): |lat| {m['abs_lat']['est']:+.3f} "
              f"[{m['abs_lat']['lo']:+.3f}, {m['abs_lat']['hi']:+.3f}] per degree; ref "
              f"{m['frac_reference']['est']:+.2f} [{m['frac_reference']['lo']:+.2f}, "
              f"{m['frac_reference']['hi']:+.2f}]  n={m['n']}")
    print(f"\n-> {jp}")


if __name__ == "__main__":
    main()
