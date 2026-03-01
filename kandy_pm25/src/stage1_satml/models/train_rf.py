"""
train_rf.py — Random Forest comparison model for Stage 1.

Provides a non-boosting baseline alongside XGBoost and LightGBM.
Random Forest does not natively support quantile regression, so we use
sklearn's QuantileRegressor or conformal prediction for UQ.

Usage:
    python train_rf.py [--no-shap]
"""

import argparse
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    MERGED_DIR, MODELS_DIR, TABLES_DIR, LOG_FORMAT, LOG_DATEFMT,
    RANDOM_FOREST_DEFAULT_PARAMS, RANDOM_SEED,
)

warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("train_rf")


def load_dataset() -> pd.DataFrame:
    path = MERGED_DIR / "dataset_daily.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Merged dataset not found: {path}")
    return pd.read_parquet(path)


def compute_metrics(y_true, y_pred, label=""):
    mask = ~pd.isna(y_true)
    yt, yp = np.asarray(y_true)[mask], np.asarray(y_pred)[mask]
    return {
        "label": label,
        "n":     int(mask.sum()),
        "R2":    round(float(r2_score(yt, yp)), 4),
        "RMSE":  round(float(np.sqrt(mean_squared_error(yt, yp))), 4),
        "MAE":   round(float(mean_absolute_error(yt, yp)), 4),
    }


def train_rf_with_uq(X_train, y_train) -> dict:
    """
    Train Random Forest with per-tree prediction variance for UQ.

    RF UQ approach: standard deviation across individual tree predictions
    gives a rough epistemic uncertainty estimate (Breiman 2001).
    """
    params = dict(RANDOM_FOREST_DEFAULT_PARAMS)
    params["random_state"] = RANDOM_SEED
    model = RandomForestRegressor(**params)
    model.fit(X_train, y_train)
    log.info(f"RF trained: {model.n_estimators} trees, OOB not enabled")
    return {"model": model}


def predict_with_intervals(model: RandomForestRegressor, X: pd.DataFrame, z: float = 1.645) -> dict:
    """
    Generate predictions and confidence intervals from individual tree outputs.

    Uses per-tree prediction distribution (std across trees) as uncertainty proxy.
    A 90% interval: mean ± 1.645 × std is an approximation (not a coverage guarantee).
    For rigorous UQ use conformal prediction or the XGBoost quantile models.

    Args:
        model : Fitted RandomForestRegressor
        X     : Feature DataFrame
        z     : Z-score for interval width (1.645 ≈ 90% normal)

    Returns:
        Dict with 'mean', 'std', 'q05', 'q95' arrays.
    """
    tree_preds = np.stack([tree.predict(X) for tree in model.estimators_], axis=1)
    mean_pred = tree_preds.mean(axis=1)
    std_pred  = tree_preds.std(axis=1)
    return {
        "mean": mean_pred,
        "std":  std_pred,
        "q05":  mean_pred - z * std_pred,
        "q95":  mean_pred + z * std_pred,
    }


def main():
    parser = argparse.ArgumentParser(description="Train Random Forest Stage 1 model")
    parser.add_argument("--no-shap", action="store_true", help="Skip SHAP analysis")
    args = parser.parse_args()

    df = load_dataset()
    target = "pm25_observed"
    if target not in df.columns:
        log.error(f"Target '{target}' not found. Run build_dataset.py first.")
        sys.exit(1)

    df_labelled = df.dropna(subset=[target])
    n_train = int(0.8 * len(df_labelled))
    df_train = df_labelled.iloc[:n_train]
    df_test  = df_labelled.iloc[n_train:]

    feature_cols = [c for c in df.columns if c not in (
        target, "date", "lat", "lon", "pm25_q05", "pm25_q95"
    ) and df[c].dtype in (np.float32, np.float64, np.int64)]

    X_tr, y_tr = df_train[feature_cols], df_train[target]
    X_te, y_te = df_test[feature_cols],  df_test[target]

    log.info(f"Training RF: {len(X_tr)} train / {len(X_te)} test, {len(feature_cols)} features")
    result = train_rf_with_uq(X_tr, y_tr)
    model  = result["model"]

    rf_preds = predict_with_intervals(model, X_te)
    metrics  = compute_metrics(y_te, rf_preds["mean"], label="rf_test")
    log.info(f"RF test: R²={metrics['R2']:.4f}  RMSE={metrics['RMSE']:.4f}")

    # Save
    import joblib
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODELS_DIR / "rf_kandy_pm25.joblib")
    log.info(f"RF model saved → {MODELS_DIR / 'rf_kandy_pm25.joblib'}")

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([metrics]).to_csv(TABLES_DIR / "rf_metrics.csv", index=False)
    log.info("✅ Random Forest training complete.")


if __name__ == "__main__":
    main()
