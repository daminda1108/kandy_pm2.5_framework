"""loss_sensitivity.py -- does the ladder's ordering survive a change of loss function?

THE OBJECTION, from an external reviewer, and the largest methodological limitation left after the
identifiability wording:

    "Your entire observation-value framework uses daily RMSE. A station that contributes almost
     nothing to ordinary daily RMSE might be extremely valuable for high-PM episodes, exceedance
     detection, public-health alerts. The value ranking is only the ranking for one loss function."

That is correct, and the thesis says so, but saying so is weaker than measuring it. RMSE is a
surrogate for loss chosen because it is the quantity the estimator already optimises. Nothing about
the construction requires it: the tiers are nested and the shrinkage is fitted the same way
whatever the scoring rule, so the ladder can simply be re-scored.

FOUR LOSSES, chosen because they disagree about which errors matter:

  rmse        the production metric. Quadratic, so it is dominated by the largest errors, but it
              is an AVERAGE over all days and a rare episode contributes little of the total.
  mae         linear. Down-weights the tail relative to RMSE and reports a typical day.
  tail        root mean square error computed ONLY on days whose observed concentration is in the
              city's top decile. This is the episode question stated as directly as this frame
              allows: how well is the model doing on the days a health authority would act on?
  exceedance  one minus balanced accuracy at the WHO 24-hour guideline of 15 ug/m3, so the loss is
              a CLASSIFICATION error rather than a magnitude error. Balanced rather than raw
              accuracy because exceedance base rates differ enormously across the panel and raw
              accuracy would reward predicting the majority class.

WHAT WOULD OVERTURN WHAT, stated before running:

  * If the background rung is largest under every loss, the headline is loss-robust.
  * If stations three to six stay near zero under every loss, the redundancy null is loss-robust,
    which is the result most exposed to this objection: the natural counter-argument is that extra
    stations earn their keep on episodes rather than on average days, and `tail` and `exceedance`
    are exactly where that would show.
  * If the deep-tropical inversion reverses under a tail or exceedance loss, then the Kandy
    recommendation is a statement about average days only, and must say so.

A rung can legitimately be NEGATIVE here. Shrinkage weights are fitted on the production metric,
so a tier optimised for average error can be worse than the tier below it on the tail. That is not
a bug; it is the finding the objection predicts, and it is reported rather than clipped.

Usage: .venv/Scripts/python.exe scripts/loss_sensitivity.py [--boot 4000]
Out:   data/processed/modular/loss_sensitivity.csv
       data/processed/modular/loss_sensitivity.json
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
warnings.filterwarnings("ignore")

from modular_validation_all import FEATS, build_frame, _affine  # noqa: E402
from src.modular import shrinkage as sh                         # noqa: E402
from ladder_order_and_bootstrap import fit_bud0c                # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "loss_sensitivity.csv"
OUT_JSON = MOD / "loss_sensitivity.json"

SEED = 20260823          # the seed the production ladder was fitted under
WHO_24H = 15.0           # WHO 2021 24-hour guideline, ug/m3
TAIL_Q = 0.90


def losses(pred: np.ndarray, obs: np.ndarray) -> dict:
    """All four scoring rules on one city's held-out days. Lower is worse-to-better throughout,
    so a percentage reduction means the same thing in every column."""
    e = pred - obs
    out = {"rmse": float(np.sqrt(np.mean(e ** 2))), "mae": float(np.mean(np.abs(e)))}
    thr = np.quantile(obs, TAIL_Q)
    m = obs >= thr
    out["tail"] = float(np.sqrt(np.mean(e[m] ** 2))) if m.sum() >= 5 else np.nan
    # balanced error at the guideline; undefined if the city never crosses it or always does
    yt, yp = obs >= WHO_24H, pred >= WHO_24H
    if yt.all() or (~yt).any() is False or yt.sum() < 5 or (~yt).sum() < 5:
        out["exceedance"] = np.nan
    else:
        tpr = float((yp & yt).sum() / yt.sum())
        tnr = float(((~yp) & (~yt)).sum() / (~yt).sum())
        out["exceedance"] = float(1.0 - 0.5 * (tpr + tnr))
    return out


def ladder_multiloss(city, st, bud0, seed):
    """The production ladder, but every tier's prediction is retained and scored under all four
    losses. The shrinkage weight is still fitted on RMSE, because that is what production does and
    changing it would confound a change of scoring rule with a change of estimator."""
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
    fr = pd.concat([p0, target], axis=1).dropna()
    if len(fr) < 120:
        return None
    bg = st[st.station_id.isin(roles["reg"])].groupby("date").pm25.quantile(0.10).rename("bg")

    obs = fr.obs.to_numpy()
    days = fr.index.astype(str).to_numpy()
    cur = fr.bud0.to_numpy()
    rows = {"city": city, "n_days": len(fr)}
    for k, v in losses(cur, obs).items():
        rows[f"Bud0_{k}"] = v

    for label, key, use_bg in (("Bud1", "b1", False), ("Bud2", "b2", False),
                               ("Bud3", "b2", True)):
        fit_s = daily(roles[key]).rename("fit")
        if not use_bg:
            j = pd.concat([p0, fit_s], axis=1).dropna()
            a, b = _affine(j.fit.to_numpy(), j.bud0.to_numpy())
            pred = a + b * fr.bud0.to_numpy()
        else:
            j = pd.concat([p0, bg, fit_s], axis=1).dropna()
            if len(j) <= 60:
                return None
            A = np.vstack([np.ones(len(j)), j.bud0.to_numpy(), j.bg.to_numpy()]).T
            c, *_ = np.linalg.lstsq(A, j.fit.to_numpy(), rcond=None)
            k2 = pd.concat([p0, bg], axis=1).reindex(fr.index)
            pred = (c[0] + c[1] * k2.bud0.to_numpy()
                    + c[2] * k2.bg.fillna(k2.bg.mean()).to_numpy())
        r = sh.optimal_weight(cur, pred, obs, groups=days, seed=seed)
        cur = sh.combine(cur, pred, r.w)
        for k3, v in losses(cur, obs).items():
            rows[f"{label}_{k3}"] = v
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=4000)
    ap.add_argument("--stream", choices=("ghap", "maiac"), default="maiac",
                    help="which satellite stream feeds Bud0c. MAIAC is the default because it is "
                         "the honest stream the thesis quotes: the fused GHAP product trains on "
                         "this panel's own monitors, and scoring a loss comparison on the stream "
                         "the thesis has retired would not answer the question that was asked.")
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)

    print("=== does the ladder's ordering survive a change of loss function? ===\n")
    sample = pd.read_csv(MOD / "validation_sample.csv")
    manifest = pd.read_csv(MOD / "openaq_manifest.csv") if (MOD / "openaq_manifest.csv").exists() \
        else None
    st, pool = build_frame(sample, manifest)
    doy = pool.date.dt.dayofyear
    pool["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    pool["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    met = [c for c in FEATS if c in pool.columns]
    pool = pool.dropna(subset=met + ["pm25_city"])
    pool["city"] = pool.city.astype(str)
    geo = pd.read_csv(MOD / "bud0_static_geo.csv"); geo["city"] = geo.city.astype(str)
    sat = pd.read_csv(MOD / "bud0_satellite_level.csv"); sat["city"] = sat.city.astype(str)
    geo_f = [c for c in geo.columns if c not in ("city", "geo_n_stations")]
    p = pool.merge(geo, on="city", how="left")
    if a.stream == "maiac":
        # the daily raw retrieval, exactly as ladder_maiac.py admits it
        aod = pd.read_csv(MOD / "bud0_maiac_aod.csv")
        aod["city"] = aod.city.astype(str)
        aod["date"] = pd.to_datetime(aod.date)
        p["date"] = pd.to_datetime(p.date)
        p = p.merge(aod[["city", "date", "aod"]], on=["city", "date"], how="left")
        sat_feats = ["aod"]
    else:
        p = p.merge(sat, on="city", how="left")
        sat_feats = ["sat_level"]
    b0 = fit_bud0c(p, met + geo_f + sat_feats)
    print(f"[1] Bud0c fitted for {b0.city.nunique()} cities on the {a.stream.upper()} stream")

    rows = []
    for city, s in st.items():
        city = str(city)
        if city not in set(b0.city):
            continue
        try:
            r = ladder_multiloss(city, s, b0[b0.city == city], SEED)
        except Exception:
            continue
        if r:
            rows.append(r)
    d = pd.DataFrame(rows)
    band = pd.read_csv(MOD / "ladder_revalidated.csv")
    band = band[band.bottom == "Bud0c"][["city", "band"]].drop_duplicates()
    band["city"] = band.city.astype(str)
    d = d.merge(band, on="city", how="left")
    tag = "" if a.stream == "maiac" else "_ghap"
    out_csv = OUT.with_name(OUT.stem + tag + OUT.suffix)
    d.to_csv(out_csv, index=False)
    print(f"[2] {len(d)} cities scored under four losses -> {OUT.name}\n")

    steps = (("first two sensors", "Bud0", "Bud1"),
             ("stations three to six", "Bud1", "Bud2"),
             ("a background series", "Bud2", "Bud3"))
    LOSSES = ("rmse", "mae", "tail", "exceedance")

    def boot(v):
        v = v[np.isfinite(v)]
        if len(v) < 4:
            return np.nan, np.nan, np.nan, len(v)
        idx = rng.integers(0, len(v), (a.boot, len(v)))
        m = np.median(v[idx], axis=1)
        return (float(np.median(v)), float(np.percentile(m, 2.5)),
                float(np.percentile(m, 97.5)), len(v))

    print("=== percentage reduction in each loss, median over cities [95%] ===")
    print(f"    {'step':<24}" + "".join(f"{L:>24}" for L in LOSSES))
    out, table = {}, []
    for label, lo, hi in steps:
        line = f"    {label:<24}"
        for L in LOSSES:
            g = 100.0 * (d[f"{lo}_{L}"] - d[f"{hi}_{L}"]) / d[f"{lo}_{L}"]
            m, l95, h95, n = boot(g.to_numpy())
            table.append(dict(step=label, loss=L, n=n, median=m, lo=l95, hi=h95))
            out[f"{label}|{L}"] = dict(median=None if not np.isfinite(m) else round(m, 2),
                                       lo=None if not np.isfinite(l95) else round(l95, 2),
                                       hi=None if not np.isfinite(h95) else round(h95, 2), n=n)
            line += f"{m:>10.2f} [{l95:>5.1f},{h95:>5.1f}]" if np.isfinite(m) else f"{'--':>24}"
        print(line)

    # the deep-tropical inversion, under each loss, paired within city
    print("\n=== the deep-tropical inversion, paired within city, under each loss ===")
    dt = d[d.band == "deep_tropical"]
    inv = {}
    for L in LOSSES:
        g1 = 100.0 * (dt[f"Bud0_{L}"] - dt[f"Bud1_{L}"]) / dt[f"Bud0_{L}"]
        g3 = 100.0 * (dt[f"Bud2_{L}"] - dt[f"Bud3_{L}"]) / dt[f"Bud2_{L}"]
        v = (g1 - g3).to_numpy()
        m, l95, h95, n = boot(v)
        if not np.isfinite(m):
            continue
        inv[L] = dict(median=round(m, 2), lo=round(l95, 2), hi=round(h95, 2), n=n,
                      favours_local=bool(m > 0), excludes_zero=bool(l95 > 0))
        print(f"    {L:<12} n={n:>2}   local minus background {m:>+8.2f} pp   "
              f"[{l95:>+7.2f},{h95:>+7.2f}]   {'favours local' if m > 0 else 'favours background'}")

    pd.DataFrame(table).to_csv(MOD / f"loss_sensitivity_steps{tag}.csv", index=False)
    print("\n=== the answer ===")
    bg_biggest = all(out[f"a background series|{L}"]["median"] is not None
                     and out[f"a background series|{L}"]["median"]
                     >= out[f"first two sensors|{L}"]["median"] for L in ("rmse", "mae"))
    red = {L: out[f"stations three to six|{L}"]["median"] for L in LOSSES}
    print(f"    Redundancy of stations three to six, by loss: "
          + ", ".join(f"{L} {v}" for L, v in red.items() if v is not None))
    print(f"    Background largest under rmse and mae: {bg_biggest}")

    out_json = OUT_JSON.with_name(OUT_JSON.stem + tag + OUT_JSON.suffix)
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(dict(cities=int(len(d)), boot=a.boot, seed=SEED, stream=a.stream,
                       who_24h=WHO_24H, tail_quantile=TAIL_Q,
                       steps=out, inversion=inv), fh, indent=2)
    print(f"\n-> {OUT.name}, loss_sensitivity_steps.csv, {OUT_JSON.name}")


if __name__ == "__main__":
    main()
