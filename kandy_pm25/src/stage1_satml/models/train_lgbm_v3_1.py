"""
train_lgbm_v3_1.py — LightGBM-quantile v3.1 with lag-dropout augmentation.

Pre-reg amendment #8 locks: during training, randomly mask the four lag
features (lag_1h, lag_3h, lag_24h, lag_168h) to NaN for p_drop = 0.10 of
training samples. This forces the model to learn non-lag-dependent splits,
improving outage robustness without harming in-sample skill.

Same protocol otherwise: hourly LOMO on residual target, α = 0.05/0.50/0.95.
The mask is applied per (fold, training-row) — calibration and inference use
original features unchanged.

Output:
  data/processed/stage1_v3/training/predictions_lomo_v3_1_lgbm.parquet
  data/processed/stage1_v3/training/summary_v3_1_lgbm.csv
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
DATASET_PATH = DATA / "dataset_v3_hourly.parquet"

DROP_COLS = {
    "pm25_observed", "residual_target", "fold",
    "sensor_name", "datetime_utc", "qc_flag",
    "geos_cf_pm25_raw", "c_prior_scaled", "c_prior_anchored", "b_FECT",
    "t925_minus_t2m_04LT_yesterday",
}
LAG_COLS = ["lag_1h", "lag_3h", "lag_24h", "lag_168h"]
P_DROP = 0.10  # pre-reg-locked


def get_features(df):
    return [c for c in df.columns if c not in DROP_COLS]


def pinball(y, q, a): e = y - q; return np.where(e >= 0, a*e, (a-1)*e).mean()
def crps(y, q05, q50, q95):
    return (pinball(y, q05, 0.05) + pinball(y, q50, 0.50)
            + pinball(y, q95, 0.95)) / 1.5


def apply_lag_dropout(X: pd.DataFrame, p_drop: float, rng) -> pd.DataFrame:
    """Wipe all four lag columns to NaN on a random p_drop fraction of rows."""
    mask = rng.random(len(X)) < p_drop
    X = X.copy()
    X.loc[mask, LAG_COLS] = np.nan
    return X


def main():
    import lightgbm as lgb

    print(f"Lag-dropout v3.1 — p_drop = {P_DROP}")
    df = pd.read_parquet(DATASET_PATH)
    df = df.dropna(subset=["residual_target"]).reset_index(drop=True)
    df["fold"] = (
        df["sensor_id"].astype(str)
        + "_" + df["datetime_utc"].dt.year.astype(str)
        + "_" + df["datetime_utc"].dt.month.astype(str).str.zfill(2)
    )
    print(f"  rows: {len(df):,}  folds: {df['fold'].nunique()}")

    feat = get_features(df)
    rng = np.random.default_rng(seed=42)
    folds = sorted(df["fold"].unique())
    preds_all, fold_metric_rows = [], []
    base = dict(
        learning_rate=0.05, num_leaves=63, min_data_in_leaf=20,
        feature_fraction=0.85, bagging_fraction=0.85, bagging_freq=5,
        n_estimators=600, verbose=-1, n_jobs=-1,
    )
    t0 = time.time()
    for i, fold in enumerate(folds, 1):
        tr = df[df["fold"] != fold]; te = df[df["fold"] == fold]
        if len(te) < 24: continue
        X_tr_raw = tr[feat]
        # Apply lag-dropout augmentation at training time only
        X_tr = apply_lag_dropout(X_tr_raw, P_DROP, rng)
        X_te = te[feat]   # inference unchanged
        y_tr = tr["residual_target"].values
        y_te = te["residual_target"].values
        c_te = te["c_prior_anchored"].values

        preds_q = {}
        for alpha in (0.05, 0.50, 0.95):
            m = lgb.LGBMRegressor(objective="quantile", alpha=alpha, **base)
            m.fit(X_tr, y_tr, categorical_feature=["sensor_id"])
            preds_q[alpha] = m.predict(X_te)

        q05 = np.minimum.reduce([preds_q[0.05], preds_q[0.50], preds_q[0.95]])
        q95 = np.maximum.reduce([preds_q[0.05], preds_q[0.50], preds_q[0.95]])
        q50 = np.clip(preds_q[0.50], q05, q95)

        pm_true = c_te + y_te; err = (c_te + q50) - pm_true
        m_ = dict(
            fold=fold, n=int(len(y_te)),
            rmse=float(np.sqrt((err**2).mean())),
            mae=float(np.abs(err).mean()),
            bias=float(err.mean()),
            r2=float(1 - (err**2).sum() / ((pm_true - pm_true.mean())**2).sum()),
            cov90=float(((pm_true >= c_te+q05) & (pm_true <= c_te+q95)).mean()),
            pi_width=float((q95 - q05).mean()),
            crps=float(crps(y_te, q05, q50, q95)),
        )
        fold_metric_rows.append(m_)
        preds_all.append(pd.DataFrame({
            "datetime_utc": te["datetime_utc"].values,
            "sensor_id": te["sensor_id"].values,
            "fold": fold,
            "residual_true": y_te,
            "residual_q05": q05, "residual_q50": q50, "residual_q95": q95,
            "c_prior_anchored": c_te,
            "pm25_observed": te["pm25_observed"].values,
            "pm25_pred_q05": c_te + q05,
            "pm25_pred_q50": c_te + q50,
            "pm25_pred_q95": c_te + q95,
        }))
        if i % 10 == 0 or i == len(folds):
            print(f"  [{i:3d}/{len(folds)}] {fold}  rmse={m_['rmse']:.2f} "
                  f"r2={m_['r2']:+.3f} cov90={m_['cov90']:.3f}  "
                  f"({time.time()-t0:.0f}s)")

    preds = pd.concat(preds_all, ignore_index=True)
    fold_df = pd.DataFrame(fold_metric_rows)
    err = preds["pm25_pred_q50"] - preds["pm25_observed"]
    pooled = {
        "model": "lgbm_v3_1_quantile_lagdrop_010",
        "p_drop": P_DROP,
        "n_folds": int(fold_df["fold"].nunique()),
        "n_obs": int(len(preds)),
        "rmse_pooled": float(np.sqrt((err**2).mean())),
        "mae_pooled": float(np.abs(err).mean()),
        "bias_pooled": float(err.mean()),
        "r2_pooled": float(1 - (err**2).sum()
                            / ((preds["pm25_observed"] - preds["pm25_observed"].mean())**2).sum()),
        "cov90_pooled": float(((preds["pm25_observed"] >= preds["pm25_pred_q05"]) &
                                (preds["pm25_observed"] <= preds["pm25_pred_q95"])).mean()),
        "pi_width_pooled": float((preds["pm25_pred_q95"] - preds["pm25_pred_q05"]).mean()),
        "crps_pooled": float(crps(
            preds["residual_true"], preds["residual_q05"],
            preds["residual_q50"], preds["residual_q95"])),
        "n_features": len(feat),
    }
    preds.to_parquet(OUT / "predictions_lomo_v3_1_lgbm.parquet", index=False)
    fold_df.to_csv(OUT / "metrics_per_fold_v3_1_lgbm.csv", index=False)
    pd.DataFrame([pooled]).to_csv(OUT / "summary_v3_1_lgbm.csv", index=False)
    print("\n── v3.1 LightGBM POOLED ──")
    for k, v in pooled.items(): print(f"  {k:<24}{v}")


if __name__ == "__main__":
    main()
