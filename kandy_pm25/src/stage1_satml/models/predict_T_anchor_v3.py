"""
predict_T_anchor_v3.py — build the deployable temporal anchor T(t) for the
spatial-temporal decomposition (plan 2026-05-29 §3.1).

    PM(x, y, t) = T(t) · S_emit(x, y) · M(x, y, t)

T(t) is the FECT-anchored, KOALA-levelled, conformal-wrapped hourly PM2.5 level
over Kandy for a full calendar year, produced from EXOGENOUS drivers only
(lag-free) so it is evaluable at every hour — including the ~70% of 2024 hours
with no FECT observation (Akurana-only, 30.5% coverage).

Pipeline:
  1. Full-data fit — 3 LightGBM quantile heads (α=0.05/0.50/0.95), lag-free,
     trained on ALL FECT rows (no LOMO holdout). Persisted to results/models/.
  2. Mondrian conformal correction table — fit on the lag-free LOMO OOF
     (predictions_lomo_v3_lgbm_lagfree.parquet) per (month × hour-of-day bin),
     identical method to conformal_v3.py.
  3. Inference — predict residual q05/q50/q95 on the gapless inference grid,
     reconstruct pm25 = c_prior_anchored + residual, enforce monotonicity,
     apply the conformal correction.
  4. Area-level re-anchor — additive level shift so annual-mean q50 equals the
     per-year VanD basin *area* mean L(year) (area anchor, beta=1; 2026-06-04
     area-vs-floor correction). KOALA 24.5225 is a valley-floor diagnostic the
     confinement field M reproduces at the NIFS pixel, NOT the basin-mean target.
     mean(S·M)=1, so the map mean lands on the area level L(year).

Output:
  data/processed/stage1_v3/T_anchor/T_kandy_hourly_{year}.parquet
  data/processed/stage1_v3/T_anchor/T_anchor_summary_{year}.csv
  results/models/stage1_v3/lgbm_lagfree_q{05,50,95}.txt
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

from config import KOALA_ANCHOR_UG_M3
from src.stage1_satml.models.train_lgbm_v3 import get_feature_cols, DATASET_PATH
from src.stage1_satml.features.vandonkelaar import level_for_year

DATA = HERE / "data" / "processed" / "stage1_v3"
OUT_DIR = DATA / "T_anchor"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR = HERE / "results" / "models" / "stage1_v3"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
LOMO_LAGFREE = DATA / "training" / "predictions_lomo_v3_lgbm_lagfree.parquet"

ALPHA = 0.10
MIN_CAL_SAMPLES = 25
HOD_BINS = [(0, 5), (6, 9), (10, 14), (15, 18), (19, 23)]
QUANTILES = (0.05, 0.50, 0.95)
LGBM_PARAMS = dict(
    objective="quantile", learning_rate=0.05, num_leaves=63,
    min_data_in_leaf=20, feature_fraction=0.85, bagging_fraction=0.85,
    bagging_freq=5, max_depth=-1, n_estimators=600, verbose=-1,
)


def _hod_bin(h: int) -> int:
    for i, (lo, hi) in enumerate(HOD_BINS):
        if lo <= h <= hi:
            return i
    return -1


# ── 1. full-data lag-free fit ───────────────────────────────────────────────
def fit_full_data():
    import lightgbm as lgb

    df = pd.read_parquet(DATASET_PATH)
    df = df.dropna(subset=["residual_target"]).reset_index(drop=True)
    feat_cols = get_feature_cols(df, lag_free=True)
    feat_cols = [c for c in feat_cols if c != "fold" and not c.startswith("fold_")]
    print(f"Full-data fit: {len(df):,} rows × {len(feat_cols)} lag-free features")

    X, y = df[feat_cols], df["residual_target"].values
    models = {}
    for a in QUANTILES:
        m = lgb.LGBMRegressor(alpha=a, **LGBM_PARAMS)
        m.fit(X, y, categorical_feature=["sensor_id"])
        path = MODEL_DIR / f"lgbm_lagfree_q{int(a*100):02d}.txt"
        m.booster_.save_model(str(path))
        models[a] = m
        print(f"  fit + saved α={a}: {path.name}")
    json.dump({"features": feat_cols},
              open(MODEL_DIR / "lgbm_lagfree_features.json", "w"), indent=2)
    return models, feat_cols


# ── 2. Mondrian conformal correction table (from lag-free LOMO OOF) ──────────
def fit_conformal_table() -> tuple[dict, float, float]:
    if not LOMO_LAGFREE.exists():
        raise FileNotFoundError(
            f"Lag-free LOMO OOF missing: {LOMO_LAGFREE}. "
            f"Run: train_lgbm_v3.py --lag-free")
    p = pd.read_parquet(LOMO_LAGFREE)
    p["datetime_utc"] = pd.to_datetime(p["datetime_utc"], utc=True)
    p["month"] = p["datetime_utc"].dt.month
    p["hod_bin"] = p["datetime_utc"].dt.hour.apply(_hod_bin)
    # One-sided miss scores (same convention as conformal_v3.py)
    p["score_lo"] = p["pm25_pred_q05"] - p["pm25_observed"]
    p["score_hi"] = p["pm25_observed"] - p["pm25_pred_q95"]

    cell = {}
    for (mo, hod), g in p.groupby(["month", "hod_bin"]):
        if len(g) >= MIN_CAL_SAMPLES:
            cell[(int(mo), int(hod))] = (
                float(np.quantile(g["score_lo"], 1 - ALPHA / 2)),
                float(np.quantile(g["score_hi"], 1 - ALPHA / 2)),
            )
    c_lo_g = float(np.quantile(p["score_lo"], 1 - ALPHA / 2))
    c_hi_g = float(np.quantile(p["score_hi"], 1 - ALPHA / 2))
    print(f"Conformal: {len(cell)} of {12*len(HOD_BINS)} Mondrian cells "
          f"(≥{MIN_CAL_SAMPLES}); global c_lo={c_lo_g:.2f} c_hi={c_hi_g:.2f}")
    return cell, c_lo_g, c_hi_g


# ── 3+4. inference + conformal + re-anchor ───────────────────────────────────
def build_T(year: int = 2024, sensor_id: int = 12451):
    grid_path = DATA / f"inference_grid_{year}_s{sensor_id}.parquet"
    if not grid_path.exists():
        raise FileNotFoundError(
            f"Inference grid missing: {grid_path}. Run: "
            f"build_dataset_v3_hourly.py --inference-grid --year {year} --sensor {sensor_id}")

    models, feat_cols = fit_full_data()
    cell, c_lo_g, c_hi_g = fit_conformal_table()

    g = pd.read_parquet(grid_path)
    g["datetime_utc"] = pd.to_datetime(g["datetime_utc"], utc=True)
    Xg = g[feat_cols]
    r = {a: models[a].predict(Xg) for a in QUANTILES}
    # monotonic residual quantiles
    r05 = np.minimum.reduce([r[0.05], r[0.50], r[0.95]])
    r95 = np.maximum.reduce([r[0.05], r[0.50], r[0.95]])
    r50 = np.clip(r[0.50], r05, r95)

    c = g["c_prior_anchored"].values
    q05 = c + r05
    q50 = c + r50
    q95 = c + r95

    # conformal correction per (month, hod_bin)
    mo = g["datetime_utc"].dt.month.values
    hb = g["datetime_utc"].dt.hour.map(_hod_bin).values
    c_lo = np.array([cell.get((int(m), int(h)), (c_lo_g, c_hi_g))[0]
                     for m, h in zip(mo, hb)])
    c_hi = np.array([cell.get((int(m), int(h)), (c_lo_g, c_hi_g))[1]
                     for m, h in zip(mo, hb)])
    q05_conf = q05 - c_lo
    q95_conf = q95 + c_hi

    # Level re-anchor: target = VanD basin *area* mean for `year` (area anchor,
    # beta=1; KOALA is a floor diagnostic, not the target — 2026-06-04 correction).
    # Additive shift preserves the model's diurnal/seasonal µg/m³ amplitude.
    L, linfo = level_for_year(year)
    raw_mean = float(np.nanmean(q50))
    shift = L - raw_mean
    print(f"VanD level re-anchor: target L({year})={L:.2f} "
          f"(proxy_year={linfo['proxy_year']}, proxied={linfo['proxied']}, "
          f"beta={linfo['beta']:.4f}); raw mean(q50)={raw_mean:.2f} "
          f"→ shift {shift:+.2f} µg/m³")

    out = pd.DataFrame({
        "datetime_utc": g["datetime_utc"].values,
        "T_q05": q05_conf + shift,
        "T_q50": q50 + shift,
        "T_q95": q95_conf + shift,
        "T_q05_preanchor": q05_conf,
        "T_q50_preanchor": q50,
        "T_q95_preanchor": q95_conf,
        "c_prior_anchored": c,
        "level_shift": shift,
    })
    # floor PI lower bound at 0 (physical); keep q50 honest
    out["T_q05"] = out["T_q05"].clip(lower=0.0)
    # .values above strips tz → re-localize to UTC (wall-times are UTC)
    out["datetime_utc"] = pd.to_datetime(out["datetime_utc"], utc=True)
    out_path = OUT_DIR / f"T_kandy_hourly_{year}.parquet"
    out.to_parquet(out_path, index=False)

    # summary diagnostics
    out["lt"] = out["datetime_utc"].dt.tz_convert("Asia/Colombo")
    out["hour"] = out["lt"].dt.hour
    out["season"] = out["lt"].dt.month.map(
        {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
         6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"})
    pi_w = float((out["T_q95"] - out["T_q05"]).mean())
    summ = dict(
        year=year, sensor_ref=sensor_id, n_hours=len(out),
        annual_mean=float(out["T_q50"].mean()),
        level_target_L=L, level_proxy_year=linfo["proxy_year"],
        level_proxied=linfo["proxied"], beta=linfo["beta"],
        koala_anchor=KOALA_ANCHOR_UG_M3, level_shift=shift,
        pi_width_mean=pi_w,
        neg_q50_frac=float((out["T_q50"] < 0).mean()),
        **{f"season_{s}": float(out.loc[out.season == s, "T_q50"].mean())
           for s in ("DJF", "MAM", "JJA", "SON")},
        peak_hour_lt=int(out.groupby("hour")["T_q50"].mean().idxmax()),
        trough_hour_lt=int(out.groupby("hour")["T_q50"].mean().idxmin()),
    )
    pd.DataFrame([summ]).to_csv(OUT_DIR / f"T_anchor_summary_{year}.csv", index=False)

    print(f"\n── T(t) {year} ──")
    for k, v in summ.items():
        print(f"  {k:<18}{v}")
    print(f"\nWrote {out_path} ({len(out):,} rows)")
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Build deployable T(t) temporal anchor.")
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--sensor", type=int, default=12451)
    args = ap.parse_args()
    build_T(year=args.year, sensor_id=args.sensor)
