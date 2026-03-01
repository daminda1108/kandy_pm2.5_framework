"""
train_xgboost.py — Train the primary Tier 1 XGBoost model for Kandy PM2.5 estimation.

Pipeline:
  1. Load the merged feature dataset
  2. Define feature columns and target
  3. Temporal train/test split (no data leakage)
  4. Baseline comparison (median predictor)
  5. XGBoost training with early stopping
  6. SHAP feature importance analysis
  7. Validation metrics and plots
  8. Save model + results

Usage:
    python train_xgboost.py
    python train_xgboost.py --tune      # Run Optuna hyperparameter search
    python train_xgboost.py --no-shap   # Skip SHAP (faster, if no ground truth yet)
"""

import argparse
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    MERGED_DIR, MODELS_DIR, FIGURES_DIR, TABLES_DIR,
    XGBOOST_DEFAULT_PARAMS, CV_FOLDS, RANDOM_SEED,
    LOG_FORMAT, LOG_DATEFMT
)

warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("train_xgboost")

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

# Satellite features (the primary predictors)
SATELLITE_FEATURES = [
    "aod_modis",
    "tropomi_no2",
    "tropomi_co",
    "tropomi_aer_ai",
]

# ERA5 meteorological features (daily values from GEE point CSV exports)
# Note: blh_mean removed — averages 124m nocturnal with 1036m daytime, diluting signal.
# blh_min (nocturnal minimum) captures inversion strength; blh_max captures daytime ventilation.
METEO_FEATURES = [
    "wind_speed", "wind_dir",
    "blh_min", "blh_max",
    "t2m", "d2m", "skt",
    "rh",
    "sp",
    "tp",
    "ssrd",
    "u10", "v10",
    "wdir_sin", "wdir_cos",
]

# Physically motivated interaction terms
INTERACTION_FEATURES = [
    "aod_blh_ratio",  # AOD / blh_min — high AOD in shallow BL = high surface PM2.5
    "aod_rh",         # AOD × (1 + RH/100) — hygroscopic growth correction
    "no2_blh_ratio",  # TROPOMI NO2 / blh_min — trace gas in shallow nocturnal BL
    "co_blh_ratio",   # TROPOMI CO / blh_min — combustion tracer in shallow BL
]

# Climate-mode features (ENSO decomposed into seasonal phase interactions)
CLIMATE_FEATURES = [
    "mei_month_sin",  # ENSO MEI × sin(month) — seasonal phase of ENSO forcing
    "mei_month_cos",  # ENSO MEI × cos(month) — seasonal phase of ENSO forcing
]

# Regional anchor (Colombo BAM sensor — 115km away, shared regional signals)
ANCHOR_FEATURES = [
    "pm25_colombo",       # Same-day Colombo PM2.5 (lag-0)
    "pm25_colombo_lag1",  # Previous-day Colombo PM2.5 (no leakage)
    "pm25_colombo_7d",    # 7-day rolling mean (background level)
]

# Topography-aware atmospheric features
TOPO_FEATURES = [
    "vvc",                   # Valley Ventilation Coefficient (original)
    "vvc_revised",           # VVC using |wind_along| instead of total wind speed
    "kfp",                   # Katabatic Flow Proxy v1 (skt-t2m gradient)
    "kfp_v2",                # Katabatic Flow Proxy v2 (Richardson-based; skipped if no t925)
    "dsc",                   # Diurnal Stability Cycle
    "rwp",                   # Rain Washout Potential
    "terrain_blocking_idx",  # Terrain Blocking Index — SRTM 30m DEM radial scan
    "wind_along",            # Along-valley wind component (valley axis 45°)
    "wind_cross",            # Cross-valley wind component
    "valley_flow_ratio",     # |wind_along| / total wind (0–1)
    "richardson_number",     # Bulk Richardson Number (skipped if no t925)
    "ri_stable_flag",        # Binary: Ri > 0.25 → stable BL (skipped if no t925)
]

# Temporal features (cyclically encoded)
TEMPORAL_FEATURES = [
    "month_sin", "month_cos",
    "dow_sin", "dow_cos",
]

# All features (filter to those actually present in the dataset)
ALL_FEATURES = (
    SATELLITE_FEATURES +
    METEO_FEATURES +
    INTERACTION_FEATURES +
    CLIMATE_FEATURES +
    ANCHOR_FEATURES +
    TOPO_FEATURES +
    TEMPORAL_FEATURES
)

TARGET = "pm25_observed"


def load_dataset() -> pd.DataFrame:
    data_path = MERGED_DIR / "dataset_daily.parquet"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {data_path}\nRun build_dataset.py first."
        )
    df = pd.read_parquet(data_path)
    log.info(f"Dataset loaded: {df.shape[0]} days, {df.shape[1]} columns.")
    return df


def select_features(df: pd.DataFrame) -> tuple[list[str], bool]:
    """
    Return the list of feature columns that are actually present in the dataset.
    Also returns has_target: whether PM2.5 observations are available.
    """
    available = [c for c in ALL_FEATURES if c in df.columns]
    missing   = [c for c in ALL_FEATURES if c not in df.columns]
    has_target = TARGET in df.columns and df[TARGET].notna().sum() >= 30

    if missing:
        log.warning(f"Features not yet available (will be added as data downloads): {missing}")
    log.info(f"Using {len(available)} features: {available}")

    return available, has_target


def temporal_split(
    df: pd.DataFrame,
    features: list[str],
    test_fraction: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Temporal train/test split — last `test_fraction` of the labelled data is the test set.
    This avoids data leakage that would occur with random splitting of time series.
    """
    if TARGET not in df.columns:
        raise ValueError(f"No target column '{TARGET}' in dataset.")

    labelled = df[df[TARGET].notna()].copy()
    if len(labelled) < 60:
        raise ValueError(
            f"Only {len(labelled)} labelled days — need ≥ 60 for reliable train/test split.\n"
            "Collect more ground-truth data or use cross-validation only."
        )

    split_idx = int(len(labelled) * (1 - test_fraction))
    train = labelled.iloc[:split_idx]
    test  = labelled.iloc[split_idx:]

    X_train = train[features]
    X_test  = test[features]
    y_train = train[TARGET]
    y_test  = test[TARGET]

    log.info(f"Train: {len(X_train)} days ({X_train.index.min().date()} – {X_train.index.max().date()})")
    log.info(f"Test:  {len(X_test)} days ({X_test.index.min().date()} – {X_test.index.max().date()})")
    return X_train, X_test, y_train, y_test


def compute_metrics(y_true: pd.Series, y_pred: np.ndarray, label: str = "") -> dict:
    """Compute standard air quality model evaluation metrics."""
    r2   = r2_score(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    mae  = mean_absolute_error(y_true, y_pred)
    mbe  = float(np.mean(y_pred - y_true.values))
    n    = len(y_true)

    # Index of Agreement (Willmott 1981)
    obs_mean = y_true.mean()
    ioa_denom = np.sum((np.abs(y_pred - obs_mean) + np.abs(y_true.values - obs_mean)) ** 2)
    ioa = 1 - (np.sum((y_pred - y_true.values) ** 2) / (ioa_denom + 1e-10))

    metrics = {"r2": r2, "rmse": rmse, "mae": mae, "mbe": mbe, "ioa": ioa, "n": n}
    prefix = f"[{label}] " if label else ""
    log.info(
        f"{prefix}R²={r2:.3f}  RMSE={rmse:.2f}  MAE={mae:.2f}  MBE={mbe:+.2f}  IOA={ioa:.3f}  N={n}"
    )
    return metrics


def baseline_median(y_train: pd.Series, y_test: pd.Series) -> dict:
    """Baseline: always predict the training median PM2.5."""
    median_val = y_train.median()
    pred = np.full(len(y_test), median_val)
    log.info(f"Baseline (median predict): {median_val:.2f} µg/m³")
    return compute_metrics(y_test, pred, label="Baseline")


def train_xgboost(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    params: dict | None = None,
) -> xgb.XGBRegressor:
    """Train XGBoost with early stopping on validation set."""
    params = params or XGBOOST_DEFAULT_PARAMS.copy()
    log.info(f"Training XGBoost with params: {params}")

    model = xgb.XGBRegressor(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=50,
    )
    log.info(f"Best round: {model.best_iteration}")
    return model


def run_cross_validation(
    df: pd.DataFrame,
    features: list[str],
    params: dict | None = None,
    n_splits: int = CV_FOLDS,
) -> pd.DataFrame:
    """
    Time-series cross-validation (expanding window — no leakage).
    Returns a DataFrame of per-fold metrics.
    """
    params = params or XGBOOST_DEFAULT_PARAMS.copy()
    params_cv = {k: v for k, v in params.items() if k != "early_stopping_rounds"}

    labelled = df[df[TARGET].notna()].copy()
    X = labelled[features]
    y = labelled[TARGET]

    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_metrics = []

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
        X_tr, X_te = X.iloc[train_idx], X.iloc[test_idx]
        y_tr, y_te = y.iloc[train_idx], y.iloc[test_idx]

        model = xgb.XGBRegressor(**params_cv)
        model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)
        pred = model.predict(X_te)
        m = compute_metrics(y_te, pred, label=f"CV Fold {fold}")
        fold_metrics.append(m)

    cv_df = pd.DataFrame(fold_metrics)
    log.info(f"\nCross-Validation Summary (mean ± std):")
    for col in ["r2", "rmse", "mae", "ioa"]:
        log.info(f"  {col}: {cv_df[col].mean():.3f} ± {cv_df[col].std():.3f}")
    return cv_df


def run_lomo_cv(
    df: pd.DataFrame,
    features: list[str],
    params: dict | None = None,
) -> pd.DataFrame:
    """
    Leave-One-Month-Out cross-validation — better for seasonal data.

    Each fold holds out one month as test, trains on the other 8 months.
    This tests whether the model can generalize across seasons.
    """
    params = params or XGBOOST_DEFAULT_PARAMS.copy()
    params_cv = {k: v for k, v in params.items() if k != "early_stopping_rounds"}

    labelled = df[df[TARGET].notna()].copy()
    X = labelled[features]
    y = labelled[TARGET]
    months = labelled.index.month

    fold_metrics = []
    all_preds = pd.Series(dtype=float, name="pred")

    for month in sorted(months.unique()):
        test_mask = months == month
        X_tr, X_te = X[~test_mask], X[test_mask]
        y_tr, y_te = y[~test_mask], y[test_mask]

        model = xgb.XGBRegressor(**params_cv)
        model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)
        pred = model.predict(X_te)
        all_preds = pd.concat([all_preds, pd.Series(pred, index=X_te.index)])
        m = compute_metrics(y_te, pred, label=f"LOMO Month {month}")
        m["month"] = month
        fold_metrics.append(m)

    cv_df = pd.DataFrame(fold_metrics)
    log.info(f"\nLOMO Cross-Validation Summary (mean ± std):")
    for col in ["r2", "rmse", "mae", "ioa"]:
        log.info(f"  {col}: {cv_df[col].mean():.3f} ± {cv_df[col].std():.3f}")

    # Overall metrics across all months
    overall = compute_metrics(y, all_preds.reindex(y.index).values, label="LOMO Overall")
    return cv_df


def run_shap_analysis(
    model: xgb.XGBRegressor,
    X: pd.DataFrame,
    n_samples: int = 500,
) -> pd.DataFrame:
    """Compute SHAP values and return feature importance DataFrame."""
    try:
        import shap
    except ImportError:
        log.warning("shap not installed — skipping SHAP analysis. pip install shap")
        return pd.DataFrame()

    log.info("Running SHAP analysis …")
    X_sample = X.sample(min(n_samples, len(X)), random_state=RANDOM_SEED)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)

    importance = pd.DataFrame({
        "feature": X.columns.tolist(),
        "mean_abs_shap": np.abs(shap_values).mean(axis=0),
    }).sort_values("mean_abs_shap", ascending=False)

    log.info("Top 10 features by mean |SHAP|:")
    log.info(importance.head(10).to_string(index=False))

    # Save SHAP summary plot
    try:
        import matplotlib.pyplot as plt
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(10, 7))
        shap.summary_plot(shap_values, X_sample, show=False, max_display=20)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "shap_summary.png", dpi=150, bbox_inches="tight")
        plt.close()
        log.info(f"SHAP plot saved → {FIGURES_DIR / 'shap_summary.png'}")
    except Exception as e:
        log.warning(f"Could not save SHAP plot: {e}")

    return importance


def save_model(model: xgb.XGBRegressor, name: str = "xgboost_kandy_pm25") -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    out = MODELS_DIR / f"{name}.ubj"
    model.save_model(str(out))
    log.info(f"Model saved → {out}")
    return out


def tune_hyperparameters(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    n_trials: int = 50,
) -> dict:
    """Optuna hyperparameter search."""
    try:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
    except ImportError:
        log.warning("optuna not installed — skipping hyperparameter tuning. pip install optuna")
        return XGBOOST_DEFAULT_PARAMS

    def objective(trial):
        params = {
            "n_estimators":     trial.suggest_int("n_estimators", 200, 1000),
            "learning_rate":    trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "max_depth":        trial.suggest_int("max_depth", 3, 9),
            "subsample":        trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "reg_alpha":        trial.suggest_float("reg_alpha", 1e-4, 10.0, log=True),
            "reg_lambda":       trial.suggest_float("reg_lambda", 1e-4, 10.0, log=True),
            "objective":        "reg:squarederror",
            "n_jobs":           -1,
            "random_state":     RANDOM_SEED,
        }
        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        pred = model.predict(X_val)
        return mean_squared_error(y_val, pred) ** 0.5  # Minimise RMSE

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
    best = study.best_params
    best.update({"objective": "reg:squarederror", "n_jobs": -1, "random_state": RANDOM_SEED})
    log.info(f"Best hyperparameters: {best}")
    return best


# ─────────────────────────────────────────────────────────────────────────────
# QUANTILE REGRESSION
# ─────────────────────────────────────────────────────────────────────────────

def train_quantile_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_full: pd.DataFrame,
    df: pd.DataFrame,
    features: list,
) -> list:
    """
    Train XGBoost quantile regression models for q05, q50, q95.

    Uses native XGBoost quantile loss (reg:quantileerror). Each quantile
    requires a separate model. The q50 (median) model typically has less
    variance compression than the mean model (reg:squarederror).

    Returns list of column names added to df.
    """
    from config import QUANTILE_ALPHAS

    quantile_cols = []
    n_val = max(int(len(X_train) * 0.2), 50)

    for alpha in QUANTILE_ALPHAS:
        label = f"q{int(alpha*100):02d}"
        col_name = f"pm25_{label}"
        log.info(f"  Training quantile α={alpha} ({label})...")

        q_params = XGBOOST_DEFAULT_PARAMS.copy()
        q_params["objective"] = "reg:quantileerror"
        q_params["quantile_alpha"] = alpha
        q_params.pop("eval_metric", None)

        q_model = xgb.XGBRegressor(**q_params)
        q_model.fit(
            X_train.iloc[:-n_val], y_train.iloc[:-n_val],
            eval_set=[(X_train.iloc[-n_val:], y_train.iloc[-n_val:])],
            verbose=False,
        )

        df[col_name] = q_model.predict(X_full)
        quantile_cols.append(col_name)

        # Save quantile model
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        q_model.save_model(str(MODELS_DIR / f"xgboost_{label}.ubj"))
        log.info(f"    {label}: range {df[col_name].min():.1f}–{df[col_name].max():.1f}, "
                 f"mean={df[col_name].mean():.1f} µg/m³")

    # Assess calibration on labeled data
    if all(c in df.columns for c in ["pm25_q05", "pm25_q95"]):
        labeled_mask = df["pm25_observed"].notna()
        y_obs = df.loc[labeled_mask, "pm25_observed"].values
        q05 = df.loc[labeled_mask, "pm25_q05"].values
        q95 = df.loc[labeled_mask, "pm25_q95"].values
        inside = ((y_obs >= q05) & (y_obs <= q95)).mean()
        width = (q95 - q05).mean()
        log.info(f"  90% PI coverage: {inside:.1%} (target: 90%)")
        log.info(f"  Mean PI width: {width:.1f} µg/m³")

    return quantile_cols


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train XGBoost PM2.5 model for Kandy")
    parser.add_argument("--tune",    action="store_true", help="Run Optuna hyperparameter search")
    parser.add_argument("--no-shap", action="store_true", help="Skip SHAP analysis")
    parser.add_argument("--cv-only", action="store_true", help="Cross-validate only, no train/test split")
    parser.add_argument("--n-trials", type=int, default=50, help="Optuna trials (default 50)")
    args = parser.parse_args()

    # ── Load data ─────────────────────────────────────────────────────────────
    df = load_dataset()
    features, has_target = select_features(df)

    if not features:
        log.error("No feature columns found. Run the data pipeline first.")
        return

    # ── Satellite-only mode (no ground truth yet) ─────────────────────────────
    if not has_target:
        log.warning(
            "═══ SATELLITE-ONLY MODE ═══\n"
            "No PM2.5 ground-truth data available yet.\n"
            "Running feature exploration only. Model will be trained\n"
            "when ground-truth data is placed in data/raw/ground_truth/."
        )
        # Still useful: print data coverage, correlations
        log.info(f"\nFeature data coverage (non-null %):\n{(df[features].notna().mean()*100).round(1).to_string()}")
        return

    # ── Leave-One-Month-Out CV (primary — suited for seasonal data) ──────────
    log.info("\n── Leave-One-Month-Out Cross-Validation ──")
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    lomo_results = run_lomo_cv(df, features)
    lomo_results.to_csv(TABLES_DIR / "cv_results_lomo.csv", index=False)

    # ── Expanding-window temporal CV (secondary) ──────────────────────────────
    log.info("\n── Temporal Cross-Validation ──")
    cv_results = run_cross_validation(df, features)
    cv_results.to_csv(TABLES_DIR / "cv_results_temporal.csv", index=False)

    if args.cv_only:
        return

    # ── Train final model on ALL labeled data ─────────────────────────────────
    # With only 273 labeled days, we train on all data and report LOMO CV as
    # the primary performance metric (no held-out test set).
    labelled = df[df[TARGET].notna()].copy()
    X_all = labelled[features]
    y_all = labelled[TARGET]

    log.info(f"\n── Training Final Model on All {len(X_all)} Labeled Days ──")

    # Use last 20% as early-stopping validation (for tree count only)
    n_val = max(30, len(X_all) // 5)
    params = XGBOOST_DEFAULT_PARAMS

    # ── Optional hyperparameter tuning ────────────────────────────────────────
    if args.tune:
        log.info("\n── Hyperparameter Tuning ──")
        params = tune_hyperparameters(
            X_all.iloc[:-n_val], y_all.iloc[:-n_val],
            X_all.iloc[-n_val:], y_all.iloc[-n_val:],
            n_trials=args.n_trials,
        )

    model = train_xgboost(
        X_all.iloc[:-n_val], y_all.iloc[:-n_val],
        X_all.iloc[-n_val:], y_all.iloc[-n_val:],
        params=params,
    )

    # ── Report training-set fit (sanity check, not the real metric) ───────────
    y_pred_train = model.predict(X_all)
    train_fit = compute_metrics(y_all, y_pred_train, label="Train-fit (sanity)")

    # ── Summary ───────────────────────────────────────────────────────────────
    log.info("\n═══ FINAL SUMMARY ═══")
    lomo_mean_r2   = lomo_results["r2"].mean()
    lomo_mean_rmse = lomo_results["rmse"].mean()
    log.info(f"LOMO CV R²:   {lomo_mean_r2:.3f}")
    log.info(f"LOMO CV RMSE: {lomo_mean_rmse:.2f} µg/m³")
    log.info(f"Train-fit R²: {train_fit['r2']:.3f} (should be high — this is in-sample)")

    # ── Save metrics ──────────────────────────────────────────────────────────
    lomo_results.to_csv(TABLES_DIR / "model_comparison.csv", index=False)
    log.info(f"Metrics saved → {TABLES_DIR / 'model_comparison.csv'}")

    # ── SHAP Analysis ─────────────────────────────────────────────────────────
    if not args.no_shap:
        log.info("\n── SHAP Analysis ──")
        importance = run_shap_analysis(model, X_all)
        if not importance.empty:
            importance.to_csv(TABLES_DIR / "shap_importance.csv", index=False)

    # ── Save model ────────────────────────────────────────────────────────────
    save_model(model)

    # ── Generate predictions for ALL days (labeled + unlabeled) ───────────────
    log.info("\n── Generating PM2.5 Predictions for Full Time Range ──")
    X_full = df[features]
    df["pm25_predicted"] = model.predict(X_full)

    # ── Quantile regression (q05/q50/q95) for prediction intervals ─────────
    log.info("\n── Quantile Regression (90% Prediction Intervals) ──")
    quantile_cols = train_quantile_models(X_all, y_all, X_full, df, features)

    # ── Save predictions ───────────────────────────────────────────────────
    save_cols = ["pm25_observed", "pm25_predicted"] + quantile_cols
    pred_path = MERGED_DIR / "pm25_predictions_daily.parquet"
    df[save_cols].to_parquet(pred_path)
    log.info(f"Predictions saved → {pred_path}")
    log.info(f"  Predicted range: {df['pm25_predicted'].min():.1f} – {df['pm25_predicted'].max():.1f} µg/m³")
    log.info(f"  Predicted mean:  {df['pm25_predicted'].mean():.1f} µg/m³")
    if "pm25_q05" in df.columns:
        width = (df["pm25_q95"] - df["pm25_q05"]).mean()
        log.info(f"  90% PI width:    {width:.1f} µg/m³ (mean)")

    log.info("\n✅ Training complete.")


if __name__ == "__main__":
    main()
