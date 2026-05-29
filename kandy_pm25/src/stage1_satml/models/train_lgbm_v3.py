"""
train_lgbm_v3.py — LightGBM-quantile RECAP v3 hourly residual model.

Targets the RESIDUAL `r_t = pm25_observed - c_prior_anchored` (per v3 pre-reg).
At inference time: pm25_pred = c_prior_anchored + r_pred.

Three quantile heads (α = 0.05, 0.50, 0.95) trained independently with pinball
loss. Hourly LOMO CV (leave-one-(sensor, calendar-month) out).

Per-reg locks:
  - Selection metric: pooled CRPS across LOMO folds (primary)
  - Tie-breakers: top-decile MAE, |cov90 − 0.90|
  - H1: RMSE_v3 ≤ 0.85 × RMSE_GEOS at hourly resolution
  - H2: pooled cov90 ∈ [0.85, 0.95]
  - H3: pooled R² ≥ 0.60
  - H7: var(pred) ≥ 0.2 × var(c_prior_scaled) during synthetic 7-day outages
  - H8: |E[r_train]| < 0.5 µg/m³  (already satisfied: −0.028)

Output:
  data/processed/stage1_v3/training/predictions_lomo_v3_lgbm.parquet
  data/processed/stage1_v3/training/summary_v3_lgbm.csv
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

warnings.filterwarnings("ignore")

DATA = HERE / "data" / "processed" / "stage1_v3"
OUT = DATA / "training"
OUT.mkdir(parents=True, exist_ok=True)

DATASET_PATH = DATA / "dataset_v3_hourly.parquet"


# ── feature selection ──────────────────────────────────────────────────────
# Columns that must NOT enter X (target leak, identity, level-features):
DROP_COLS = {
    # target + identity
    "pm25_observed", "residual_target",
    "sensor_name", "datetime_utc", "qc_flag",
    # level GEOS-CF features (Option B: keep derivatives only)
    "geos_cf_pm25_raw", "c_prior_scaled", "c_prior_anchored",
    "b_FECT",
}


# Autoregressive pm25 lags — dropped in lag-free mode (production T(t) must be
# evaluable at every hour of 2024, but FECT coverage is only 30.5% / Akurana-only,
# so observed lags are unavailable for 70% of target hours).
LAG_COLS = {"lag_1h", "lag_3h", "lag_24h", "lag_168h"}


def get_feature_cols(df: pd.DataFrame, lag_free: bool = False) -> List[str]:
    drop = DROP_COLS | (LAG_COLS if lag_free else set())
    keep = [c for c in df.columns if c not in drop]
    # sensor_id stays as a categorical proxy (LightGBM handles it natively)
    return keep


# ── metrics ────────────────────────────────────────────────────────────────
def pinball_loss(y, q, alpha):
    e = y - q
    return np.where(e >= 0, alpha * e, (alpha - 1) * e).mean()


def crps_quantile_approx(y, q05, q50, q95):
    """CRPS approximation from three quantiles (Laio-Tamea style)."""
    return (
        pinball_loss(y, q05, 0.05)
        + pinball_loss(y, q50, 0.50)
        + pinball_loss(y, q95, 0.95)
    ) / 1.5  # normalisation so CRPS ≈ MAE when q05=q50=q95


def fold_metrics(y, q05, q50, q95, c_prior_anchored):
    """Compute per-fold metrics on the FULL pm25 scale (not residual)."""
    pm25_pred_q05 = c_prior_anchored + q05
    pm25_pred_q50 = c_prior_anchored + q50
    pm25_pred_q95 = c_prior_anchored + q95
    pm25_true = c_prior_anchored + y    # y is residual; reconstruct
    err = pm25_pred_q50 - pm25_true
    rmse = float(np.sqrt((err ** 2).mean()))
    mae = float(np.abs(err).mean())
    bias = float(err.mean())
    ss_res = ((pm25_true - pm25_pred_q50) ** 2).sum()
    ss_tot = ((pm25_true - pm25_true.mean()) ** 2).sum()
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    cov90 = float(((pm25_true >= pm25_pred_q05) &
                   (pm25_true <= pm25_pred_q95)).mean())
    pi_width = float((pm25_pred_q95 - pm25_pred_q05).mean())
    crps = float(crps_quantile_approx(y, q05, q50, q95))
    # top-decile MAE (heavy-tail tie-breaker)
    top10 = pm25_true >= np.quantile(pm25_true, 0.90)
    mae_p90 = float(np.abs(err[top10]).mean()) if top10.sum() > 5 else float("nan")
    return dict(
        rmse=rmse, mae=mae, bias=bias, r2=r2,
        cov90=cov90, pi_width=pi_width, crps=crps, mae_p90=mae_p90,
        n=int(len(y)),
    )


# ── training ───────────────────────────────────────────────────────────────
def train_lomo(lag_free: bool = False):
    import lightgbm as lgb

    suffix = "_lagfree" if lag_free else ""
    print(f"Loading dataset... (lag_free={lag_free})")
    df = pd.read_parquet(DATASET_PATH)
    df = df.dropna(subset=["residual_target"]).reset_index(drop=True)
    df["fold_year"] = df["datetime_utc"].dt.year
    df["fold_month"] = df["datetime_utc"].dt.month
    df["fold"] = (
        df["sensor_id"].astype(str)
        + "_"
        + df["fold_year"].astype(str)
        + "_"
        + df["fold_month"].astype(str).str.zfill(2)
    )
    print(f"  rows: {len(df):,}  folds: {df['fold'].nunique()}")

    feat_cols = get_feature_cols(df, lag_free=lag_free)
    feat_cols = [c for c in feat_cols if c != "fold"
                  and not c.startswith("fold_")]
    print(f"  features ({len(feat_cols)}): {feat_cols}")

    folds = sorted(df["fold"].unique())
    preds_all = []
    fold_metric_rows = []
    base_params = dict(
        objective="quantile",
        learning_rate=0.05,
        num_leaves=63,
        min_data_in_leaf=20,
        feature_fraction=0.85,
        bagging_fraction=0.85,
        bagging_freq=5,
        max_depth=-1,
        n_estimators=600,
        verbose=-1,
    )
    t0 = time.time()
    for i, fold in enumerate(folds, 1):
        train_mask = df["fold"] != fold
        test_mask = ~train_mask
        train, test = df[train_mask], df[test_mask]
        if len(test) < 24:        # skip thin folds
            continue
        X_tr, X_te = train[feat_cols], test[feat_cols]
        y_tr, y_te = train["residual_target"].values, test["residual_target"].values
        c_te = test["c_prior_anchored"].values

        # Three quantile fits
        preds_q = {}
        for alpha in (0.05, 0.50, 0.95):
            model = lgb.LGBMRegressor(alpha=alpha, **base_params)
            model.fit(X_tr, y_tr, categorical_feature=["sensor_id"])
            preds_q[alpha] = model.predict(X_te)

        # Enforce quantile monotonicity (q05 ≤ q50 ≤ q95)
        q05 = np.minimum.reduce([preds_q[0.05], preds_q[0.50], preds_q[0.95]])
        q95 = np.maximum.reduce([preds_q[0.05], preds_q[0.50], preds_q[0.95]])
        q50 = preds_q[0.50]
        q50 = np.clip(q50, q05, q95)

        m = fold_metrics(y_te, q05, q50, q95, c_te)
        m["fold"] = fold
        fold_metric_rows.append(m)

        # Store per-row predictions for the pooled report
        out = pd.DataFrame({
            "datetime_utc": test["datetime_utc"].values,
            "sensor_id": test["sensor_id"].values,
            "fold": fold,
            "residual_true": y_te,
            "residual_q05": q05,
            "residual_q50": q50,
            "residual_q95": q95,
            "c_prior_anchored": c_te,
            "pm25_observed": test["pm25_observed"].values,
            "pm25_pred_q05": c_te + q05,
            "pm25_pred_q50": c_te + q50,
            "pm25_pred_q95": c_te + q95,
        })
        preds_all.append(out)

        if i % 10 == 0 or i == len(folds):
            elapsed = time.time() - t0
            print(f"  [{i:3d}/{len(folds)}] {fold} "
                  f"rmse={m['rmse']:.2f} r2={m['r2']:+.3f} "
                  f"cov90={m['cov90']:.3f} mae_p90={m['mae_p90']:.2f} "
                  f"crps={m['crps']:.3f}  ({elapsed:.0f}s elapsed)")

    preds = pd.concat(preds_all, ignore_index=True)
    fold_df = pd.DataFrame(fold_metric_rows)

    # ── pooled metrics ─────────────────────────────────────────────────────
    err = preds["pm25_pred_q50"] - preds["pm25_observed"]
    pooled = {
        "model": "lgbm_v3_quantile",
        "n_folds": int(fold_df["fold"].nunique()),
        "n_obs": int(len(preds)),
        "rmse_pooled": float(np.sqrt((err ** 2).mean())),
        "mae_pooled": float(np.abs(err).mean()),
        "bias_pooled": float(err.mean()),
        "r2_pooled": float(1 - (err ** 2).sum() /
                           ((preds["pm25_observed"] - preds["pm25_observed"].mean()) ** 2).sum()),
        "cov90_pooled": float(((preds["pm25_observed"] >= preds["pm25_pred_q05"]) &
                                (preds["pm25_observed"] <= preds["pm25_pred_q95"])).mean()),
        "pi_width_pooled": float((preds["pm25_pred_q95"] - preds["pm25_pred_q05"]).mean()),
        "crps_pooled": float(crps_quantile_approx(
            preds["residual_true"], preds["residual_q05"],
            preds["residual_q50"], preds["residual_q95"])),
        "rmse_mean_per_fold": float(fold_df["rmse"].mean()),
        "rmse_median_per_fold": float(fold_df["rmse"].median()),
        "cov90_mean_per_fold": float(fold_df["cov90"].mean()),
        "mae_p90_mean": float(fold_df["mae_p90"].mean()),
        "n_features": len(feat_cols),
    }

    # ── persist ────────────────────────────────────────────────────────────
    pooled["lag_free"] = lag_free
    preds.to_parquet(OUT / f"predictions_lomo_v3_lgbm{suffix}.parquet", index=False)
    fold_df.to_csv(OUT / f"metrics_per_fold_v3_lgbm{suffix}.csv", index=False)
    pd.DataFrame([pooled]).to_csv(OUT / f"summary_v3_lgbm{suffix}.csv", index=False)

    print("\n── POOLED METRICS ──")
    for k, v in pooled.items():
        print(f"  {k:<24}{v}")
    print(f"\nSaved predictions ({len(preds):,} rows) to {OUT}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Stage-1 v3 LightGBM-quantile RECAP (LOMO CV).")
    ap.add_argument("--lag-free", action="store_true",
                    help="Drop autoregressive pm25 lags (lag_{1,3,24,168}h) — for deployable T(t).")
    args = ap.parse_args()
    train_lomo(lag_free=args.lag_free)
