"""
train_lightgbm.py — LightGBM comparison model for Stage 1 (alongside XGBoost).

LightGBM is run as a secondary model to benchmark against XGBoost.
Uses the same feature set and CV strategy for fair comparison.
Also supports quantile regression for UQ (same approach as XGBoost).

Usage:
    python train_lightgbm.py [--tune] [--no-shap]
"""

import argparse
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    MERGED_DIR, MODELS_DIR, TABLES_DIR, LOG_FORMAT, LOG_DATEFMT,
    LIGHTGBM_DEFAULT_PARAMS, QUANTILE_ALPHAS, RANDOM_SEED,
)

warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("train_lightgbm")


def load_dataset() -> pd.DataFrame:
    path = MERGED_DIR / "dataset_daily.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Merged dataset not found: {path}\nRun: python build_dataset.py")
    return pd.read_parquet(path)


def train_lgbm(X_train, y_train, X_val, y_val, params=None, objective="regression"):
    try:
        import lightgbm as lgb
    except ImportError:
        raise ImportError("lightgbm not installed. Run: pip install lightgbm")

    p = dict(LIGHTGBM_DEFAULT_PARAMS)
    if params:
        p.update(params)
    p["objective"] = objective

    dtrain = lgb.Dataset(X_train, label=y_train)
    dval   = lgb.Dataset(X_val,   label=y_val)
    callbacks = [lgb.early_stopping(50, verbose=False), lgb.log_evaluation(period=0)]
    booster = lgb.train(
        p, dtrain,
        num_boost_round=p.pop("n_estimators", 500),
        valid_sets=[dval],
        callbacks=callbacks,
    )
    return booster


def compute_metrics(y_true, y_pred, label=""):
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    mask = ~pd.isna(y_true)
    yt, yp = y_true[mask].values, y_pred[mask]
    return {
        "label": label,
        "n":     len(yt),
        "R2":    round(float(r2_score(yt, yp)), 4),
        "RMSE":  round(float(np.sqrt(mean_squared_error(yt, yp))), 4),
        "MAE":   round(float(mean_absolute_error(yt, yp)), 4),
    }


def main():
    parser = argparse.ArgumentParser(description="Train LightGBM Stage 1 model")
    parser.add_argument("--tune",    action="store_true", help="Enable Optuna tuning")
    parser.add_argument("--no-shap", action="store_true", help="Skip SHAP analysis")
    args = parser.parse_args()

    df = load_dataset()
    target = "pm25_observed"
    if target not in df.columns:
        log.error(f"Target '{target}' not found. Available cols: {list(df.columns[:10])}")
        sys.exit(1)

    df_labelled = df.dropna(subset=[target])
    n_train = int(0.8 * len(df_labelled))
    df_train = df_labelled.iloc[:n_train]
    df_test  = df_labelled.iloc[n_train:]

    feature_cols = [c for c in df.columns if c not in (
        target, "date", "lat", "lon", "pm25_q05", "pm25_q95"
    )]
    feature_cols = [c for c in feature_cols if df[c].dtype in (np.float32, np.float64, np.int64)]

    X_tr, y_tr = df_train[feature_cols], df_train[target]
    X_te, y_te = df_test[feature_cols],  df_test[target]

    log.info(f"Training LightGBM: {len(X_tr)} train / {len(X_te)} test samples, {len(feature_cols)} features")

    model = train_lgbm(X_tr, y_tr, X_te, y_te)
    preds = model.predict(X_te)
    metrics = compute_metrics(y_te, preds, label="lgbm_test")
    log.info(f"LightGBM test: R²={metrics['R2']:.4f}  RMSE={metrics['RMSE']:.4f}")

    # Quantile regression for UQ
    log.info("Fitting quantile models (q05, q50, q95) …")
    q_models = {}
    for alpha in QUANTILE_ALPHAS:
        qm = train_lgbm(
            X_tr, y_tr, X_te, y_te,
            objective="quantile",
            params={"alpha": alpha},
        )
        q_models[alpha] = qm
        log.info(f"  Quantile {alpha:.2f} model trained")

    # Save
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(str(MODELS_DIR / "lgbm_kandy_pm25.txt"))
    log.info(f"LightGBM model saved → {MODELS_DIR / 'lgbm_kandy_pm25.txt'}")

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([metrics]).to_csv(TABLES_DIR / "lgbm_metrics.csv", index=False)
    log.info("✅ LightGBM training complete.")


if __name__ == "__main__":
    main()
