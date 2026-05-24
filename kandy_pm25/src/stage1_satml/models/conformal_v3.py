"""
conformal_v3.py — Mondrian conformal-quantile wrapper for v3 LightGBM predictions.

For each LOMO fold:
  1. Hold out 20 % of the fold's predictions as a calibration split (chronologically
     first, so test = chronologically last 80 % — keeps temporal causality intact).
  2. Per Mondrian bucket (calendar_month × hour_of_day_bin), compute the empirical
     correction quantiles:
        c_lo = quantile_(1-α/2)(c_prior_anchored + q05 − pm25_obs)  [low miss]
        c_hi = quantile_(1-α/2)(pm25_obs − (c_prior_anchored + q95)) [high miss]
  3. Apply corrections to the 80 % test split:
        pm25_pred_q05_conf = pm25_pred_q05 − c_lo
        pm25_pred_q95_conf = pm25_pred_q95 + c_hi
  4. Buckets with < MIN_CAL_SAMPLES fall back to a global per-fold quantile.

Reports cov90 / PI width / R² before-and-after on the 80 % test split only.

Pre-reg lock (§5.3): Mondrian bins = (calendar_month × hour_of_day_5bin).
Coverage target: α = 0.10 (so cov90 ∈ [0.85, 0.95] by construction).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

PRED_PATH = HERE / "data" / "processed" / "stage1_v3" / "training" / "predictions_lomo_v3_lgbm.parquet"
OUT_DIR = HERE / "data" / "processed" / "stage1_v3" / "training"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ALPHA = 0.10                 # 90 % PI → coverage target 0.90
CAL_FRAC = 0.20              # 20 % per fold for calibration
MIN_CAL_SAMPLES = 25         # minimum per Mondrian cell before falling back
HOD_BINS = [(0, 5), (6, 9), (10, 14), (15, 18), (19, 23)]


def _hod_bin(h: int) -> int:
    for i, (lo, hi) in enumerate(HOD_BINS):
        if lo <= h <= hi:
            return i
    return -1


def conformal_wrap():
    p = pd.read_parquet(PRED_PATH)
    p["datetime_utc"] = pd.to_datetime(p["datetime_utc"], utc=True)
    p["month"] = p["datetime_utc"].dt.month
    p["hod_bin"] = p["datetime_utc"].dt.hour.apply(_hod_bin)
    p = p.sort_values(["fold", "datetime_utc"]).reset_index(drop=True)

    cal_rows, test_rows = [], []
    for fold, sub in p.groupby("fold"):
        n = len(sub)
        n_cal = max(int(n * CAL_FRAC), 5)
        cal_rows.append(sub.iloc[:n_cal])
        test_rows.append(sub.iloc[n_cal:])
    cal = pd.concat(cal_rows, ignore_index=True)
    test = pd.concat(test_rows, ignore_index=True)
    print(f"Cal: {len(cal):,}  Test: {len(test):,}")

    # Conformity scores on calibration set: how much we MISSED the PI
    cal["score_lo"] = cal["pm25_pred_q05"] - cal["pm25_observed"]   # positive = q05 too high
    cal["score_hi"] = cal["pm25_observed"] - cal["pm25_pred_q95"]   # positive = q95 too low

    # Per-Mondrian bucket quantile corrections
    cell_lookup = {}
    for (mo, hod), grp in cal.groupby(["month", "hod_bin"]):
        if len(grp) >= MIN_CAL_SAMPLES:
            c_lo = float(np.quantile(grp["score_lo"], 1 - ALPHA / 2))
            c_hi = float(np.quantile(grp["score_hi"], 1 - ALPHA / 2))
            cell_lookup[(mo, hod)] = (c_lo, c_hi, len(grp))

    # Global fallback (one-sided q_{1-α/2} on each tail)
    c_lo_global = float(np.quantile(cal["score_lo"], 1 - ALPHA / 2))
    c_hi_global = float(np.quantile(cal["score_hi"], 1 - ALPHA / 2))
    print(f"Mondrian cells: {len(cell_lookup):,} of {12*len(HOD_BINS)} "
          f"with ≥{MIN_CAL_SAMPLES} samples")
    print(f"Global fallback: c_lo={c_lo_global:.3f}  c_hi={c_hi_global:.3f}")

    # Apply
    def _apply(row):
        key = (row["month"], row["hod_bin"])
        c_lo, c_hi, _ = cell_lookup.get(key, (c_lo_global, c_hi_global, 0))
        return pd.Series({
            "pm25_pred_q05_conf": row["pm25_pred_q05"] - c_lo,
            "pm25_pred_q95_conf": row["pm25_pred_q95"] + c_hi,
        })

    test = test.assign(**test.apply(_apply, axis=1))

    # ── before vs after metrics on TEST split only ────────────────────────
    def _metrics(t, q05c, q95c, label):
        err = t["pm25_pred_q50"] - t["pm25_observed"]
        cov = ((t["pm25_observed"] >= t[q05c]) &
               (t["pm25_observed"] <= t[q95c])).mean()
        width = (t[q95c] - t[q05c]).mean()
        rmse = float(np.sqrt((err**2).mean()))
        r2 = 1 - (err**2).sum() / ((t["pm25_observed"] - t["pm25_observed"].mean())**2).sum()
        return dict(label=label, n=len(t), rmse=rmse, r2=float(r2),
                    cov90=float(cov), pi_width=float(width))

    before = _metrics(test, "pm25_pred_q05", "pm25_pred_q95", "pre-conformal")
    after = _metrics(test, "pm25_pred_q05_conf", "pm25_pred_q95_conf", "post-conformal")
    print("\n── BEFORE / AFTER conformal on 80% test split ──")
    for d in (before, after):
        print(f"  {d['label']:<18} n={d['n']:,}  rmse={d['rmse']:.2f}  "
              f"r2={d['r2']:+.3f}  cov90={d['cov90']:.3f}  "
              f"pi_width={d['pi_width']:.2f}")

    # cov90 by month after conformal
    test["covered_post"] = ((test["pm25_observed"] >= test["pm25_pred_q05_conf"]) &
                             (test["pm25_observed"] <= test["pm25_pred_q95_conf"]))
    monthly_after = test.groupby("month")["covered_post"].agg(["mean", "count"])
    print("\nPost-conformal cov90 by month:")
    print(monthly_after.to_string())

    diurnal_after = test.groupby("hod_bin")["covered_post"].agg(["mean", "count"])
    print("\nPost-conformal cov90 by hour-of-day bin:")
    print(diurnal_after.to_string())

    # Save
    test.to_parquet(OUT_DIR / "predictions_lomo_v3_lgbm_conformal.parquet", index=False)
    pd.DataFrame([before, after]).to_csv(
        OUT_DIR / "conformal_summary_v3.csv", index=False
    )
    print(f"\nWrote: {OUT_DIR / 'predictions_lomo_v3_lgbm_conformal.parquet'}")


if __name__ == "__main__":
    conformal_wrap()
