"""
medellin_train_stage1.py — Train XGBoost Stage 1 model for Medellín.

Mirrors the Kandy train_xgboost.py methodology:
  - Leave-One-Month-Out (LOMO) cross-validation
  - Optuna hyperparameter tuning (LOMO RMSE objective)
  - SHAP feature importance analysis
  - Saves city-mean predictions for use as PINN boundary conditions

Input:  data/processed/stage2/medellin_stage1_dataset.parquet
Output: results/models/medellin_stage1_xgboost.ubj
        data/processed/stage2/medellin_stage1_predictions.parquet
        results/tables/medellin_stage1_lomo_cv.csv
        results/figures/publication/medellin_stage1_shap.png

Usage:
    cd kandy_pm25/
    python src/stage2_transfer/medellin_train_stage1.py
    python src/stage2_transfer/medellin_train_stage1.py --tune       # run Optuna
    python src/stage2_transfer/medellin_train_stage1.py --no-shap    # skip SHAP
    python src/stage2_transfer/medellin_train_stage1.py --shap-only  # only SHAP
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error, r2_score

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import (
    PROC_DIR,
    MODELS_DIR,
    TABLES_DIR,
    FIGURES_DIR,
    LOG_FORMAT, LOG_DATEFMT,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("medellin_train_stage1")

# ─── Paths ────────────────────────────────────────────────────────────────────
STAGE2_PROC_DIR   = PROC_DIR / "stage2"
DATASET_PARQUET   = STAGE2_PROC_DIR / "medellin_stage1_dataset.parquet"
PREDICTIONS_OUT   = STAGE2_PROC_DIR / "medellin_stage1_predictions.parquet"
MODEL_OUT         = MODELS_DIR / "medellin_stage1_xgboost.ubj"
CV_TABLE_OUT      = TABLES_DIR / "medellin_stage1_lomo_cv.csv"
OPTUNA_TRIALS_OUT = TABLES_DIR / "medellin_stage1_optuna_trials.csv"
BEST_PARAMS_OUT   = MODELS_DIR / "medellin_stage1_best_params.json"
SHAP_FIGURE_OUT   = FIGURES_DIR / "publication" / "medellin_stage1_shap.png"
KANDY_BEST_PARAMS = MODELS_DIR / "xgboost_best_params.json"

TARGET       = "pm25_observed"
RANDOM_SEED  = 42

# Non-feature columns (never used as predictors)
NON_FEATURE_COLS = {TARGET, "month", "doy"}

# Kandy tuned params as starting point (may be overridden by --tune)
DEFAULT_PARAMS = {
    "n_estimators":      1184,
    "learning_rate":     0.00822,
    "max_depth":         5,
    "subsample":         0.767,
    "colsample_bytree":  0.910,
    "colsample_bylevel": 0.974,
    "min_child_weight":  3,
    "gamma":             1.98,
    "reg_alpha":         12.4,
    "reg_lambda":        2.7e-5,
    "objective":         "reg:squarederror",
    "eval_metric":       "rmse",
    "n_jobs":            -1,
    "random_state":      RANDOM_SEED,
}


# ─────────────────────────────────────────────────────────────────────────────
def load_dataset() -> tuple[pd.DataFrame, list[str]]:
    """Load Medellín Stage 1 dataset and determine feature columns."""
    if not DATASET_PARQUET.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PARQUET}\n"
            "Run medellin_build_dataset.py first."
        )
    df = pd.read_parquet(DATASET_PARQUET)
    log.info(f"Loaded: {df.shape[0]} rows × {df.shape[1]} cols")
    log.info(f"Date range: {df.index.min().date()} to {df.index.max().date()}")
    log.info(f"PM2.5 stats: mean={df[TARGET].mean():.1f}, std={df[TARGET].std():.1f} µg/m³")

    features = [c for c in df.columns if c not in NON_FEATURE_COLS]
    # Drop columns that are all NaN
    valid_features = [f for f in features if df[f].notna().any()]
    dropped = set(features) - set(valid_features)
    if dropped:
        log.warning(f"Dropping all-NaN feature columns: {dropped}")
    log.info(f"Features ({len(valid_features)}): {valid_features}")
    return df, valid_features


# ─────────────────────────────────────────────────────────────────────────────
def compute_metrics(y_true, y_pred, label: str = "") -> dict:
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    r2   = r2_score(y_true, y_pred)
    mae  = float(np.abs(y_true - y_pred).mean())
    bias = float((y_pred - y_true).mean())
    if label:
        log.info(f"{label}: R²={r2:.3f}  RMSE={rmse:.2f}  MAE={mae:.2f}  Bias={bias:+.2f}")
    return {"r2": r2, "rmse": rmse, "mae": mae, "bias": bias}


# ─────────────────────────────────────────────────────────────────────────────
def run_lomo_cv(df: pd.DataFrame, features: list[str], params: dict) -> pd.DataFrame:
    """
    Leave-One-Month-Out cross-validation.
    For Medellín: 13 months (Aug 2018–Sep 2019) → 13 folds.
    Reports per-month and overall R², RMSE, MAE, bias.
    """
    labelled = df[df[TARGET].notna()].copy()
    X, y     = labelled[features], labelled[TARGET]
    months   = labelled.index.month

    params_cv = {k: v for k, v in params.items() if k != "early_stopping_rounds"}
    fold_results = []
    all_preds    = pd.Series(dtype=float, index=labelled.index, name="pm25_pred")

    for month in sorted(months.unique()):
        test_mask = months == month
        X_tr, X_te = X[~test_mask], X[test_mask]
        y_tr, y_te = y[~test_mask], y[test_mask]

        model = xgb.XGBRegressor(**params_cv)
        model.fit(X_tr, y_tr, verbose=False)
        pred = model.predict(X_te)
        all_preds[X_te.index] = pred

        m = compute_metrics(y_te.values, pred, label=f"LOMO Month {month:02d}")
        m["month"]    = month
        m["n_days"]   = len(y_te)
        fold_results.append(m)

    cv_df = pd.DataFrame(fold_results)

    log.info("\n── LOMO Summary ──────────────────────────────")
    for col in ["r2", "rmse", "mae", "bias"]:
        log.info(f"  {col:5s}: mean={cv_df[col].mean():.3f}  std={cv_df[col].std():.3f}")

    # Overall (all held-out predictions concatenated)
    compute_metrics(y.values, all_preds.reindex(y.index).values, label="LOMO Overall")

    return cv_df, all_preds


# ─────────────────────────────────────────────────────────────────────────────
def tune_hyperparameters(df: pd.DataFrame, features: list[str], n_trials: int = 50) -> dict:
    """Optuna LOMO RMSE minimisation — same objective as Kandy."""
    try:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
    except ImportError:
        log.warning("optuna not installed — using default params. pip install optuna")
        return DEFAULT_PARAMS.copy()

    labelled = df[df[TARGET].notna()].copy()
    X, y     = labelled[features], labelled[TARGET]
    months   = labelled.index.month

    def objective(trial):
        p = {
            "n_estimators":      trial.suggest_int("n_estimators", 200, 1500),
            "learning_rate":     trial.suggest_float("learning_rate", 0.005, 0.3, log=True),
            "max_depth":         trial.suggest_int("max_depth", 3, 10),
            "subsample":         trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree":  trial.suggest_float("colsample_bytree", 0.4, 1.0),
            "colsample_bylevel": trial.suggest_float("colsample_bylevel", 0.5, 1.0),
            "min_child_weight":  trial.suggest_int("min_child_weight", 1, 20),
            "gamma":             trial.suggest_float("gamma", 0.0, 5.0),
            "reg_alpha":         trial.suggest_float("reg_alpha", 1e-5, 50.0, log=True),
            "reg_lambda":        trial.suggest_float("reg_lambda", 1e-5, 50.0, log=True),
            "objective":         "reg:squarederror",
            "n_jobs":            -1,
            "random_state":      RANDOM_SEED,
        }
        fold_rmses = []
        for month in sorted(months.unique()):
            test_mask = months == month
            model = xgb.XGBRegressor(**p)
            model.fit(X[~test_mask], y[~test_mask], verbose=False)
            pred = model.predict(X[test_mask])
            fold_rmses.append(mean_squared_error(y[test_mask], pred) ** 0.5)
        return float(np.mean(fold_rmses))

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED),
    )
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    best = study.best_params
    best.update({
        "objective":   "reg:squarederror",
        "eval_metric": "rmse",
        "n_jobs":      -1,
        "random_state": RANDOM_SEED,
    })

    log.info(f"Best LOMO RMSE: {study.best_value:.3f} µg/m³ (trial #{study.best_trial.number})")

    # Save params
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(BEST_PARAMS_OUT, "w") as f:
        json.dump(best, f, indent=2)
    log.info(f"Best params saved → {BEST_PARAMS_OUT}")

    # Save trial history
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    cols = ["number", "value", "params_n_estimators", "params_learning_rate",
            "params_max_depth", "params_gamma", "params_reg_alpha"]
    trials_df = study.trials_dataframe()[[c for c in cols if c in study.trials_dataframe().columns]]
    trials_df.to_csv(OPTUNA_TRIALS_OUT, index=False)

    return best


# ─────────────────────────────────────────────────────────────────────────────
def run_shap(model: xgb.XGBRegressor, X: pd.DataFrame) -> None:
    try:
        import shap
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("shap / matplotlib not installed — skipping SHAP.")
        return

    log.info("Running SHAP analysis …")
    X_sample  = X.sample(min(300, len(X)), random_state=RANDOM_SEED)
    explainer = shap.TreeExplainer(model)
    sv        = explainer.shap_values(X_sample)

    importance = pd.DataFrame({
        "feature":       X.columns.tolist(),
        "mean_abs_shap": np.abs(sv).mean(axis=0),
    }).sort_values("mean_abs_shap", ascending=False)

    log.info("Top 15 features by mean |SHAP|:")
    log.info(importance.head(15).to_string(index=False))

    SHAP_FIGURE_OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 8))
    shap.summary_plot(sv, X_sample, show=False, max_display=20)
    plt.title("Medellín Stage 1 — Feature Importance (SHAP)", fontsize=12)
    plt.tight_layout()
    plt.savefig(SHAP_FIGURE_OUT, dpi=150, bbox_inches="tight")
    plt.close()
    log.info(f"SHAP plot → {SHAP_FIGURE_OUT}")


# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Train Medellín Stage 1 XGBoost")
    parser.add_argument("--labels",     choices=["siata", "cams"], default="siata",
                        help="Dataset mode: 'siata' (366 days) or 'cams' (2018-2025 BC CAMS)")
    parser.add_argument("--tune",       action="store_true", help="Run Optuna (50 trials)")
    parser.add_argument("--n-trials",   type=int, default=50, help="Optuna trial count")
    parser.add_argument("--no-shap",    action="store_true", help="Skip SHAP")
    parser.add_argument("--shap-only",  action="store_true", help="Only run SHAP on saved model")
    args = parser.parse_args()

    # Override module-level path constants based on --labels
    suffix = "_cams" if args.labels == "cams" else ""
    global DATASET_PARQUET, MODEL_OUT, PREDICTIONS_OUT, CV_TABLE_OUT
    global BEST_PARAMS_OUT, OPTUNA_TRIALS_OUT, SHAP_FIGURE_OUT
    DATASET_PARQUET   = STAGE2_PROC_DIR / f"medellin_stage1_dataset{suffix}.parquet"
    MODEL_OUT         = MODELS_DIR      / f"medellin_stage1_xgboost{suffix}.ubj"
    PREDICTIONS_OUT   = STAGE2_PROC_DIR / f"medellin_stage1_predictions{suffix}.parquet"
    CV_TABLE_OUT      = TABLES_DIR      / f"medellin_stage1_lomo_cv{suffix}.csv"
    BEST_PARAMS_OUT   = MODELS_DIR      / f"medellin_stage1_best_params{suffix}.json"
    OPTUNA_TRIALS_OUT = TABLES_DIR      / f"medellin_stage1_optuna_trials{suffix}.csv"
    SHAP_FIGURE_OUT   = FIGURES_DIR / "publication" / f"medellin_stage1_shap{suffix}.png"
    log.info(f"Labels mode: {args.labels} | Dataset: {DATASET_PARQUET.name}")

    df, features = load_dataset()

    # ── SHAP only mode ────────────────────────────────────────────────────────
    if args.shap_only:
        if not MODEL_OUT.exists():
            raise FileNotFoundError(f"Model not found: {MODEL_OUT}. Run training first.")
        model = xgb.XGBRegressor()
        model.load_model(str(MODEL_OUT))
        labelled = df[df[TARGET].notna()]
        run_shap(model, labelled[features])
        return

    # ── Resolve hyperparameters ────────────────────────────────────────────────
    params = DEFAULT_PARAMS.copy()

    # Prefer mode-specific tuned params; fall back to Kandy's if not available
    if BEST_PARAMS_OUT.exists() and not args.tune:
        with open(BEST_PARAMS_OUT) as f:
            params.update(json.load(f))
        log.info(f"Loaded tuned params from {BEST_PARAMS_OUT}")
    elif KANDY_BEST_PARAMS.exists() and not args.tune:
        with open(KANDY_BEST_PARAMS) as f:
            params.update(json.load(f))
        log.info(f"Loaded Kandy best params from {KANDY_BEST_PARAMS}")

    if args.tune:
        log.info(f"Running Optuna tuning ({args.n_trials} trials) …")
        params = tune_hyperparameters(df, features, n_trials=args.n_trials)

    # ── LOMO Cross-Validation ─────────────────────────────────────────────────
    log.info("\n── LOMO Cross-Validation ────────────────────────────────────────")
    cv_df, lomo_preds = run_lomo_cv(df, features, params)

    # Save CV table
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    cv_df.to_csv(CV_TABLE_OUT, index=False)
    log.info(f"CV table → {CV_TABLE_OUT}")

    # ── Train final model on full dataset ─────────────────────────────────────
    log.info("\n── Training final model on full dataset ─────────────────────────")
    labelled = df[df[TARGET].notna()]
    X_full = labelled[features]
    y_full = labelled[TARGET]

    final_params = {k: v for k, v in params.items() if k != "early_stopping_rounds"}
    model = xgb.XGBRegressor(**final_params)
    model.fit(X_full, y_full, verbose=False)

    train_pred = model.predict(X_full)
    compute_metrics(y_full.values, train_pred, label="Train-fit (in-sample)")

    # ── Save model ────────────────────────────────────────────────────────────
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(str(MODEL_OUT))
    log.info(f"Model → {MODEL_OUT}")

    # ── Save predictions ──────────────────────────────────────────────────────
    preds_df = pd.DataFrame({
        "pm25_observed": y_full,
        "pm25_pred":     train_pred,
        "pm25_pred_lomo": lomo_preds.reindex(y_full.index),
    })
    STAGE2_PROC_DIR.mkdir(parents=True, exist_ok=True)
    preds_df.to_parquet(PREDICTIONS_OUT)
    log.info(f"Predictions → {PREDICTIONS_OUT}")

    # ── SHAP ──────────────────────────────────────────────────────────────────
    if not args.no_shap:
        run_shap(model, X_full)

    log.info("\n── Done ─────────────────────────────────────────────────────────")
    log.info(f"LOMO R²:   {cv_df['r2'].mean():.3f} ± {cv_df['r2'].std():.3f}")
    log.info(f"LOMO RMSE: {cv_df['rmse'].mean():.2f} ± {cv_df['rmse'].std():.2f} µg/m³")
    log.info(f"Model: {MODEL_OUT}")
    log.info(f"Predictions: {PREDICTIONS_OUT}")


if __name__ == "__main__":
    main()
