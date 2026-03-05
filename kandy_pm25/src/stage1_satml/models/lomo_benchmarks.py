"""
lomo_benchmarks.py — LOMO CV comparison (XGBoost vs LightGBM vs RandomForest)
                     + Reliability diagram (calibration of 90% prediction intervals)

Usage:
    python src/stage1_satml/models/lomo_benchmarks.py

Outputs:
    results/tables/model_comparison_lomo.csv
    results/figures/publication/reliability_diagram.pdf+png
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor

warnings.filterwarnings("ignore")

# ── Path setup ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(ROOT))

import xgboost as xgb
try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    print("[WARN] lightgbm not installed — LightGBM benchmark skipped")
    HAS_LGB = False

from src.utils.plot_style import apply_style, save_figure
apply_style("ieee")

from config import (
    MERGED_DIR, TABLES_DIR, FIGURES_DIR,
    XGBOOST_DEFAULT_PARAMS, RANDOM_SEED
)

TARGET = "pm25_observed"

# ── Identical feature list to train_xgboost.py ─────────────────────────────
ALL_FEATURES = [
    # Satellite
    "aod_modis", "tropomi_no2", "tropomi_co", "tropomi_aer_ai",
    # Meteo
    "wind_speed", "wind_dir", "blh_min", "blh_max",
    "t2m", "d2m", "skt", "rh", "sp", "tp", "ssrd",
    "u10", "v10", "wdir_sin", "wdir_cos",
    # Interaction
    "aod_blh_ratio", "aod_rh", "no2_blh_ratio", "co_blh_ratio",
    # Climate
    "mei_month_sin", "mei_month_cos",
    # Anchor
    "pm25_colombo", "pm25_colombo_lag1", "pm25_colombo_7d",
    # Topo
    "vvc", "vvc_revised", "kfp", "kfp_v2", "dsc", "rwp",
    "terrain_blocking_idx", "wind_along", "wind_cross",
    "valley_flow_ratio", "richardson_number", "ri_stable_flag",
    # Temporal
    "month_sin", "month_cos", "dow_sin", "dow_cos",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def load_data():
    df = pd.read_parquet(MERGED_DIR / "dataset_daily.parquet")
    df.index = pd.to_datetime(df.index)
    features = [c for c in ALL_FEATURES if c in df.columns]
    labeled = df[df[TARGET].notna()].copy()
    X = labeled[features].fillna(labeled[features].median())
    y = labeled[TARGET]
    months = labeled.index.month
    print(f"Loaded {len(labeled)} labelled rows, {len(features)} features")
    return X, y, months, features


def lomo_cv(model_factory, X, y, months, label="model"):
    """Leave-One-Month-Out cross-validation."""
    all_preds = np.full(len(y), np.nan)
    all_obs   = y.values.copy()

    for m in range(1, 13):
        test_mask  = (months == m)
        train_mask = ~test_mask
        if train_mask.sum() < 50 or test_mask.sum() < 5:
            continue
        X_tr, X_te = X[train_mask], X[test_mask]
        y_tr, y_te = y[train_mask], y[test_mask]

        model = model_factory()
        model.fit(X_tr, y_tr)
        all_preds[test_mask] = model.predict(X_te)

    valid = ~np.isnan(all_preds)
    r2   = r2_score(all_obs[valid], all_preds[valid])
    rmse = np.sqrt(mean_squared_error(all_obs[valid], all_preds[valid]))
    mae  = mean_absolute_error(all_obs[valid], all_preds[valid])
    print(f"  {label:20s}  LOMO R²={r2:.3f}  RMSE={rmse:.2f}  MAE={mae:.2f}")
    return {"model": label, "lomo_r2": round(r2, 4),
            "lomo_rmse": round(rmse, 4), "lomo_mae": round(mae, 4),
            "cv_scheme": "LOMO", "n": int(valid.sum())}


# ─────────────────────────────────────────────────────────────────────────────
# XGBoost — load Optuna params if available
# ─────────────────────────────────────────────────────────────────────────────
import json
optuna_path = TABLES_DIR / "optuna_best_params.json"
if optuna_path.exists():
    with open(optuna_path) as f:
        optuna_params = json.load(f)
    print(f"Loaded Optuna params from {optuna_path}")
else:
    optuna_params = XGBOOST_DEFAULT_PARAMS.copy()
    print("Using default XGBoost params (no Optuna file found)")

optuna_params.setdefault("verbosity", 0)
optuna_params.setdefault("random_state", RANDOM_SEED)
optuna_params.setdefault("seed", RANDOM_SEED)
# early_stopping_rounds needs an eval_set — drop for LOMO (no eval set in fold loop)
optuna_params.pop("early_stopping_rounds", None)

def xgb_factory():
    return xgb.XGBRegressor(**optuna_params)

def lgb_factory():
    return lgb.LGBMRegressor(n_estimators=500, learning_rate=0.05,
                              num_leaves=63, min_child_samples=20,
                              random_state=RANDOM_SEED, verbose=-1)

def rf_factory():
    return RandomForestRegressor(n_estimators=300, max_features=0.6,
                                  min_samples_leaf=5, random_state=RANDOM_SEED,
                                  n_jobs=-1)


# ─────────────────────────────────────────────────────────────────────────────
# Run LOMO benchmarks
# ─────────────────────────────────────────────────────────────────────────────
def main():
    X, y, months, features = load_data()
    results = []

    print("\n── LOMO CV Benchmarks ──")
    results.append(lomo_cv(xgb_factory, X, y, months, label="XGBoost_v2"))
    if HAS_LGB:
        results.append(lomo_cv(lgb_factory, X, y, months, label="LightGBM"))
    results.append(lomo_cv(rf_factory, X, y, months, label="RandomForest"))

    out = pd.DataFrame(results)
    out_path = TABLES_DIR / "model_comparison_lomo.csv"
    out.to_csv(out_path, index=False)
    print(f"\nSaved LOMO comparison → {out_path}")
    print(out.to_string(index=False))

    # ── Reliability diagram ──────────────────────────────────────────────────
    pred_path = MERGED_DIR / "pm25_predictions_daily.parquet"
    if not pred_path.exists():
        print(f"\n[SKIP] Predictions file not found: {pred_path}")
        return

    preds = pd.read_parquet(pred_path)
    required = {"pm25_observed", "pm25_q05", "pm25_q95"}
    if not required.issubset(preds.columns):
        print(f"\n[SKIP] Expected columns {required} not in predictions file: {preds.columns.tolist()}")
        return

    p = preds[["pm25_observed", "pm25_q05", "pm25_q95"]].dropna()
    obs   = p["pm25_observed"].values
    q05   = p["pm25_q05"].values
    q95   = p["pm25_q95"].values
    pi90_width = q95 - q05

    nominal_levels = np.arange(0.10, 0.95, 0.10)
    observed_cov   = []
    for alpha in nominal_levels:
        # Symmetric interval: scale 90% PI by alpha/0.9 from the median (q50 if available)
        if "pm25_q50" in preds.columns:
            q50 = preds.loc[p.index, "pm25_q50"].values
        else:
            q50 = (q05 + q95) / 2
        half = (pi90_width / 2) * (alpha / 0.90)
        lo = q50 - half
        hi = q50 + half
        cov = np.mean((obs >= lo) & (obs <= hi))
        observed_cov.append(cov)
    observed_cov = np.array(observed_cov)

    actual_90 = np.mean((obs >= q05) & (obs <= q95))
    print(f"\n90% PI actual coverage: {actual_90*100:.1f}%  (target: 88.5%)")

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    ax.plot(nominal_levels * 100, observed_cov * 100,
            "o-", color="steelblue", lw=1.5, ms=5, label="XGBoost (this study)")
    ax.plot([10, 90], [10, 90], "k--", lw=1.0, alpha=0.7, label="Perfect calibration")
    ax.fill_between([10, 90], [10, 90], [0, 80],
                    alpha=0.07, color="red", label="Under-confident region")
    ax.fill_between([10, 90], [10, 90], [20, 100],
                    alpha=0.07, color="blue", label="Over-confident region")
    ax.text(0.04, 0.96,
            f"90% PI coverage = {actual_90*100:.1f}%",
            transform=ax.transAxes, fontsize=8, va="top",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))
    ax.set_xlabel("Nominal coverage (%)")
    ax.set_ylabel("Observed coverage (%)")
    ax.set_title("Reliability diagram\n(PI calibration, LOMO holdouts)")
    ax.set_xlim(5, 95); ax.set_ylim(0, 105)
    ax.legend(fontsize=6.5, loc="lower right")
    fig.tight_layout()

    fig_dir = FIGURES_DIR / "publication"
    fig_dir.mkdir(parents=True, exist_ok=True)
    save_figure(fig, "reliability_diagram")
    plt.close(fig)
    print(f"Saved reliability diagram → {fig_dir}")


if __name__ == "__main__":
    main()
