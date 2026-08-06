"""anchor_choice_sensitivity.py — how much does the ANCHOR CHOICE flatter the
transfer validation? (2026-08-06)

THE CONCERN
-----------
Every headline transfer number in this project comes from running the model at a
"two-sensor information budget that reproduces Kandy's data scarcity". But the two
anchors are not drawn at random. The rule is explicit:

    well    = cov[cov.n > 3000].sort_values("pm")
    anchors = [well.index[-1], well.index[0]]      # dirtiest + cleanest

That is a deliberate MAXIMAL-GRADIENT choice: the two extremes of a 24-station network,
selected with full knowledge of every station's mean. It brackets the network range, so
the held-out network mean is guaranteed to lie between the two training anchors, which
is exactly the configuration most likely to produce a small level bias.

Kandy never had that luxury. Its two sensors are wherever FECT happened to put them.
If the extremal choice materially outperforms a random pair, then the panel's reported
level skill is optimistic relative to what Kandy can expect, and the transfer claim is
weaker than stated by that margin.

THE TEST
--------
At Medellin (24 stations, the flagship proving ground): rebuild the two-anchor T(t)
exactly as the validated recipe does, once for the shipped extremal pair and once for
each of N random well-sampled pairs. Score every version against the SAME held-out
stations -- always excluding whichever two are acting as anchors -- and report where the
shipped pair sits in the random distribution.

Only the temporal anchor depends on the sensor choice; the spatial pattern P_local never
sees a sensor, so spatial rank is untouched and is not evaluated here.

READING THE RESULT
------------------
If the shipped pair sits near the median of the random distribution, the concern is
answered and the transfer numbers are representative. If it sits in the favourable tail,
the margin is the amount by which the panel flatters Kandy, and it should be reported.

Run:  .venv/Scripts/python.exe scripts/anchor_choice_sensitivity.py [--n-random 30]
Out:  data/processed/stage1_v3/training/anchor_choice_sensitivity.{csv,json}
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

REPO = Path(__file__).resolve().parents[1]
STG = REPO / "data" / "processed" / "stage2"
OUT = REPO / "data" / "processed" / "stage1_v3" / "training"

FEATURES = ["sin_h", "cos_h", "sin_doy", "cos_doy", "dow",
            "blh", "u10", "v10", "wspd", "t2m", "c_prior_scaled"]
LGBM = dict(objective="regression", learning_rate=0.05, num_leaves=63,
            n_estimators=400, min_child_samples=20, subsample=0.8,
            colsample_bytree=0.8, verbose=-1, n_jobs=-1)
MIN_HOURS = 3000


def calendar(df):
    dt = df["valid"]
    df["sin_h"] = np.sin(2 * np.pi * dt.dt.hour / 24)
    df["cos_h"] = np.cos(2 * np.pi * dt.dt.hour / 24)
    doy = dt.dt.dayofyear
    df["sin_doy"] = np.sin(2 * np.pi * doy / 365.25)
    df["cos_doy"] = np.cos(2 * np.pi * doy / 365.25)
    df["dow"] = dt.dt.dayofweek
    return df


def shape_r(a, b, by):
    g = pd.DataFrame({"a": a, "b": b, "by": by}).groupby("by").mean()
    return float(np.corrcoef(g.a, g.b)[0, 1])


def run_pair(d, drv, anchors, year):
    """Train the 2-anchor T(t) on `anchors` and score against everyone else."""
    an = d[d.station_id.isin(anchors)].dropna(subset=["pm25", "c_prior"])
    if an.empty:
        return None
    ratio = float(an.pm25.mean() / an.c_prior.mean())        # row-mean (gotcha #39)
    anchor_obs = an.groupby("valid").pm25.mean().rename("anchor_pm")

    tr = drv.merge(anchor_obs, on="valid")
    tr = tr[tr.valid.dt.year < year]                          # clean temporal split
    tr = tr.copy()
    tr["c_prior_scaled"] = tr.c_prior * ratio
    tr = tr.dropna(subset=FEATURES + ["anchor_pm"])
    if len(tr) < 500:
        return None
    m = LGBMRegressor(**LGBM).fit(tr[FEATURES], tr.anchor_pm - tr.c_prior_scaled)

    ev = drv[drv.valid.dt.year == year].copy()
    ev["c_prior_scaled"] = ev.c_prior * ratio
    ev = ev.dropna(subset=FEATURES)
    if ev.empty:
        return None
    ev["T"] = ev.c_prior_scaled + m.predict(ev[FEATURES])

    held = d[(~d.station_id.isin(anchors)) & (d.valid.dt.year == year)]
    obs = held.groupby("valid").pm25.mean().rename("obs")
    j = ev.merge(obs, on="valid").dropna(subset=["T", "obs"])
    if len(j) < 500:
        return None
    return {"n": int(len(j)),
            "rmse": float(np.sqrt(np.mean((j["T"] - j.obs) ** 2))),
            "r": float(np.corrcoef(j["T"], j.obs)[0, 1]),
            "level_bias_pct": float(100 * (j["T"].mean() / j.obs.mean() - 1)),
            "abs_level_bias_pct": float(abs(100 * (j["T"].mean() / j.obs.mean() - 1))),
            "seasonal_r": shape_r(j.obs, j["T"], j.valid.dt.month),
            "diurnal_r": shape_r(j.obs, j["T"], j.valid.dt.hour)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="medellin")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--n-random", type=int, default=30)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== anchor-choice sensitivity: does the extremal pair flatter the panel? ===")

    d = pd.read_parquet(STG / f"{a.city}_perstation_v13.parquet")
    d["valid"] = pd.to_datetime(d.datetime_utc, utc=True)
    d = d.dropna(subset=["pm25"])

    cov = (d[d.valid.dt.year == a.year].groupby("station_id")
           .agg(n=("pm25", "size"), pm=("pm25", "mean")))
    well = cov[cov.n > MIN_HOURS].sort_values("pm")
    print(f"  {a.city} {a.year}: {len(cov)} stations, {len(well)} well-sampled "
          f"(>{MIN_HOURS} h), mean PM {well.pm.min():.1f}-{well.pm.max():.1f}")
    if len(well) < 6:
        raise SystemExit("too few well-sampled stations for a meaningful sensitivity test")

    drv = (d.groupby("valid")
             .agg(c_prior=("c_prior", "mean"), blh=("blh", "mean"),
                  u10=("u10", "mean"), v10=("v10", "mean"), t2m=("t2m", "mean"))
             .reset_index())
    drv["wspd"] = np.hypot(drv.u10, drv.v10)
    drv = calendar(drv)

    shipped = [well.index[-1], well.index[0]]          # dirtiest + cleanest
    base = run_pair(d, drv, shipped, a.year)
    if base is None:
        raise SystemExit("the shipped anchor pair did not produce a scorable run")
    print(f"\n  SHIPPED pair (dirtiest+cleanest): {shipped}")
    print(f"    RMSE {base['rmse']:.3f} | r {base['r']:.3f} | level bias "
          f"{base['level_bias_pct']:+.2f}% | seasonal {base['seasonal_r']:.3f} "
          f"| diurnal {base['diurnal_r']:.3f}")

    rng = np.random.default_rng(a.seed)
    pool = list(well.index)
    allpairs = [p for p in itertools.combinations(pool, 2) if set(p) != set(shipped)]
    rng.shuffle(allpairs)
    rows = []
    print(f"\n  scoring {min(a.n_random, len(allpairs))} random pairs from "
          f"{len(allpairs)} available ...")
    for p in allpairs[:a.n_random]:
        r = run_pair(d, drv, list(p), a.year)
        if r:
            r["pair"] = f"{p[0]}|{p[1]}"
            rows.append(r)
    if len(rows) < 5:
        raise SystemExit("too few random pairs scored")
    R = pd.DataFrame(rows)
    print(f"  {len(R)} random pairs scored\n")

    print("  metric            shipped     random median   random p10-p90     percentile")
    res = {"city": a.city, "year": a.year, "shipped_pair": shipped,
           "n_random": int(len(R)), "shipped": base, "random": {}}
    for k, lower_is_better in (("rmse", True), ("abs_level_bias_pct", True),
                               ("seasonal_r", False), ("diurnal_r", False),
                               ("r", False)):
        v = R[k].to_numpy(float)
        pct = float(100 * (v < base[k]).mean()) if lower_is_better else \
              float(100 * (v < base[k]).mean())
        # percentile of the shipped value among random pairs, expressed as
        # "% of random pairs that the shipped pair BEATS"
        beat = float(100 * ((v > base[k]) if lower_is_better else (v < base[k])).mean())
        res["random"][k] = {"median": round(float(np.median(v)), 4),
                            "p10": round(float(np.percentile(v, 10)), 4),
                            "p90": round(float(np.percentile(v, 90)), 4),
                            "shipped_beats_pct": round(beat, 1)}
        print(f"  {k:<18}{base[k]:>8.3f}{np.median(v):>15.3f}"
              f"{np.percentile(v, 10):>10.3f}-{np.percentile(v, 90):<8.3f}"
              f"  beats {beat:.0f}% of random")

    # Per-metric verdict. Averaging across metrics is WRONG here and was the first
    # thing this script did: the extremal choice helps some metrics and hurts others,
    # and the mean hides exactly the structure the test exists to find.
    flat, pen = [], []
    for k, v in res["random"].items():
        b = v["shipped_beats_pct"]
        if b >= 75:
            flat.append(k)
        elif b <= 25:
            pen.append(k)
    res["flattered_metrics"] = flat
    res["penalised_metrics"] = pen
    res["verdict"] = {
        "flattered": ("the extremal pair sits in the favourable tail for "
                      + ", ".join(flat) + "; an arbitrary 2-sensor city should expect "
                      "the random median instead") if flat else "none",
        "penalised": ("the extremal pair is WORSE than a random pair for "
                      + ", ".join(pen) + "; averaging the two extremes is a biased "
                      "estimator of the network mean when the station distribution is "
                      "skewed, so the panel's level claim is conservative, not flattered")
                     if pen else "none"}
    print("\n  PER-METRIC VERDICT (averaging across metrics would hide this)")
    print(f"    flattered by the extremal choice : {flat or 'none'}")
    print(f"    penalised by the extremal choice : {pen or 'none'}")
    print("\n  Absolute values are not comparable to the scorecard (clean temporal")
    print("  split, no amplitude sharpening, no full field build) -- only the POSITION")
    print("  of the shipped pair within the random distribution is meaningful.")

    OUT.mkdir(parents=True, exist_ok=True)
    R.to_csv(OUT / "anchor_choice_sensitivity.csv", index=False)
    (OUT / "anchor_choice_sensitivity.json").write_text(
        json.dumps(res, indent=1), encoding="utf-8")
    print(f"\nwrote anchor_choice_sensitivity.{{csv,json}}")


if __name__ == "__main__":
    main()
