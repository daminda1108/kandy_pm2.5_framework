"""
train_catboost_v3.py — CatBoost-quantile RECAP v3 hourly residual model.

Same protocol as train_lgbm_v3.py: hourly LOMO on residual target.
CatBoost native handling of `sensor_id` as categorical; oblivious trees give
smoother quantile predictions (less crossing) than LightGBM.

Output:
  data/processed/stage1_v3/training/predictions_lomo_v3_catboost.parquet
  data/processed/stage1_v3/training/summary_v3_catboost.csv
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
}


def get_feature_cols(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if c not in DROP_COLS]


def pinball_loss(y, q, alpha):
    e = y - q
    return np.where(e >= 0, alpha * e, (alpha - 1) * e).mean()


def crps_quantile_approx(y, q05, q50, q95):
    return (pinball_loss(y, q05, 0.05)
            + pinball_loss(y, q50, 0.50)
            + pinball_loss(y, q95, 0.95)) / 1.5


def fold_metrics(y, q05, q50, q95, c_p):
    err = (c_p + q50) - (c_p + y)
    rmse = float(np.sqrt((err ** 2).mean()))
    mae = float(np.abs(err).mean())
    bias = float(err.mean())
    pm_true = c_p + y
    pm_q05 = c_p + q05; pm_q95 = c_p + q95
    r2 = float(1 - ((pm_true - (c_p + q50)) ** 2).sum() /
                ((pm_true - pm_true.mean()) ** 2).sum())
    cov90 = float(((pm_true >= pm_q05) & (pm_true <= pm_q95)).mean())
    pi_width = float((pm_q95 - pm_q05).mean())
    crps = float(crps_quantile_approx(y, q05, q50, q95))
    top10 = pm_true >= np.quantile(pm_true, 0.90)
    mae_p90 = float(np.abs(err[top10]).mean()) if top10.sum() > 5 else float("nan")
    return dict(rmse=rmse, mae=mae, bias=bias, r2=r2, cov90=cov90,
                pi_width=pi_width, crps=crps, mae_p90=mae_p90, n=int(len(y)))


def main():
    from catboost import CatBoostRegressor

    print("Loading dataset...")
    df = pd.read_parquet(DATASET_PATH)
    df = df.dropna(subset=["residual_target"]).reset_index(drop=True)
    df["fold"] = (
        df["sensor_id"].astype(str)
        + "_"
        + df["datetime_utc"].dt.year.astype(str)
        + "_"
        + df["datetime_utc"].dt.month.astype(str).str.zfill(2)
    )
    print(f"  rows: {len(df):,}  folds: {df['fold'].nunique()}")

    feat = get_feature_cols(df)
    cat_idx = [feat.index("sensor_id")]
    folds = sorted(df["fold"].unique())
    preds_all, fold_metric_rows = [], []
    base = dict(
        iterations=600,
        learning_rate=0.05,
        depth=6,
        l2_leaf_reg=3.0,
        verbose=0,
        thread_count=-1,
    )
    t0 = time.time()
    for i, fold in enumerate(folds, 1):
        tr = df[df["fold"] != fold]
        te = df[df["fold"] == fold]
        if len(te) < 24: continue
        X_tr, X_te = tr[feat], te[feat]
        y_tr, y_te = tr["residual_target"].values, te["residual_target"].values
        c_te = te["c_prior_anchored"].values

        preds_q = {}
        for alpha in (0.05, 0.50, 0.95):
            mdl = CatBoostRegressor(
                loss_function=f"Quantile:alpha={alpha}",
                cat_features=cat_idx, **base,
            )
            # Convert NaN-bearing numeric columns to float, NaN OK in CatBoost
            X_tr_cb = X_tr.copy(); X_tr_cb["sensor_id"] = X_tr_cb["sensor_id"].astype(str)
            X_te_cb = X_te.copy(); X_te_cb["sensor_id"] = X_te_cb["sensor_id"].astype(str)
            mdl.fit(X_tr_cb, y_tr)
            preds_q[alpha] = mdl.predict(X_te_cb)

        q05 = np.minimum.reduce([preds_q[0.05], preds_q[0.50], preds_q[0.95]])
        q95 = np.maximum.reduce([preds_q[0.05], preds_q[0.50], preds_q[0.95]])
        q50 = np.clip(preds_q[0.50], q05, q95)

        m = fold_metrics(y_te, q05, q50, q95, c_te)
        m["fold"] = fold
        fold_metric_rows.append(m)

        out = pd.DataFrame({
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
        })
        preds_all.append(out)

        if i % 10 == 0 or i == len(folds):
            elapsed = time.time() - t0
            print(f"  [{i:3d}/{len(folds)}] {fold} "
                  f"rmse={m['rmse']:.2f} r2={m['r2']:+.3f} "
                  f"cov90={m['cov90']:.3f} crps={m['crps']:.3f}  "
                  f"({elapsed:.0f}s)")

    preds = pd.concat(preds_all, ignore_index=True)
    fold_df = pd.DataFrame(fold_metric_rows)
    err = preds["pm25_pred_q50"] - preds["pm25_observed"]
    pooled = {
        "model": "catboost_v3_quantile",
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
        "cov90_mean_per_fold": float(fold_df["cov90"].mean()),
        "mae_p90_mean": float(fold_df["mae_p90"].mean()),
        "n_features": len(feat),
    }

    preds.to_parquet(OUT / "predictions_lomo_v3_catboost.parquet", index=False)
    fold_df.to_csv(OUT / "metrics_per_fold_v3_catboost.csv", index=False)
    pd.DataFrame([pooled]).to_csv(OUT / "summary_v3_catboost.csv", index=False)

    print("\n── POOLED ──")
    for k, v in pooled.items():
        print(f"  {k:<24}{v}")


if __name__ == "__main__":
    main()
