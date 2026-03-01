"""
train_pixel_xgboost.py — Train Stage 1b pixel-level XGBoost on spatially disaggregated labels.

This model extends Stage 1a (temporal, domain-mean) to Stage 1b (spatiotemporal, per-pixel).
The key difference: each of the 50 VD pixels now has its own PM2.5 target value (via VD weight)
and pixel-specific topographic features (elevation, TPI, slope, aspect, dist_valley_floor).

Training dataset: dataset_pixel_daily.parquet (413,950 samples = 50 pixels × 8,279 days)
Target: pm25_observed_pixel = pm25_observed × vd_weight(pixel)

Validation strategies:
  1. Spatial blocked CV: hold out N pixels, train on the rest
  2. Temporal blocked CV: hold out year blocks, train on the rest
  3. LOMO CV: hold out calendar months

The spatial blocked CV is the key new test — can the model predict PM2.5 at pixels
it has never seen, using only their topographic features?

Usage:
    python train_pixel_xgboost.py
    python train_pixel_xgboost.py --no-shap
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    MERGED_DIR, MODELS_DIR, FIGURES_DIR, TABLES_DIR,
    XGBOOST_DEFAULT_PARAMS, RANDOM_SEED,
    LOG_FORMAT, LOG_DATEFMT,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("train_pixel_xgboost")

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE DEFINITIONS (extends Stage 1a with pixel-specific features)
# ─────────────────────────────────────────────────────────────────────────────

# Shared features (identical across pixels on a given day)
SHARED_FEATURES = [
    # Meteorological
    "wind_speed", "wind_dir", "blh_min", "blh_max",
    "t2m", "d2m", "skt", "rh", "sp", "tp", "ssrd",
    "u10", "v10", "wdir_sin", "wdir_cos",
    # Satellite
    "aod_modis", "tropomi_no2", "tropomi_co", "tropomi_aer_ai",
    # Interaction
    "aod_blh_ratio", "aod_rh", "no2_blh_ratio", "co_blh_ratio",
    # Climate (mei_month_sin/cos replace dropped enso_mei scalar)
    "mei_month_sin", "mei_month_cos",
    # Topographic (domain-level, vary temporally)
    "vvc", "vvc_revised", "kfp", "kfp_v2", "dsc", "rwp",
    # Valley wind decomposition
    "wind_along", "wind_cross", "valley_flow_ratio",
    # Stability
    "richardson_number", "ri_stable_flag",
    # Terrain blocking (spatial signal, low temporal variance — kept for Stage 3)
    "terrain_blocking_idx",
    # Temporal encoding
    "month_sin", "month_cos", "dow_sin", "dow_cos",
]

# Pixel-specific features (vary spatially, static per pixel)
PIXEL_FEATURES = [
    "elevation",          # Mean elevation within 1km pixel (m)
    "slope",              # Mean slope (degrees)
    "aspect",             # Mean aspect (degrees from north)
    "tpi",                # Topographic Position Index (m)
    "dist_valley_floor",  # Distance from lowest pixel (km)
    "vd_weight",          # Van Donkelaar spatial weight (normalized)
]

ALL_FEATURES = SHARED_FEATURES + PIXEL_FEATURES

TARGET = "pm25_observed_pixel"


def load_pixel_dataset() -> pd.DataFrame:
    path = MERGED_DIR / "dataset_pixel_daily.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Pixel dataset not found: {path}\n"
            "Run spatial_disaggregate.py first."
        )
    df = pd.read_parquet(path)
    log.info(f"Pixel dataset loaded: {df.shape[0]:,} samples, {df.shape[1]} columns")
    return df


def select_features(df: pd.DataFrame) -> list[str]:
    available = [c for c in ALL_FEATURES if c in df.columns]
    missing = [c for c in ALL_FEATURES if c not in df.columns]
    if missing:
        log.warning(f"Missing features: {missing}")
    log.info(f"Using {len(available)} features ({len(PIXEL_FEATURES)} pixel-specific)")
    return available


def compute_metrics(y_true, y_pred, label: str = "") -> dict:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    r2 = r2_score(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    mae = mean_absolute_error(y_true, y_pred)
    mbe = float(np.mean(y_pred - y_true))
    n = len(y_true)

    obs_mean = y_true.mean()
    ioa_denom = np.sum((np.abs(y_pred - obs_mean) + np.abs(y_true - obs_mean)) ** 2)
    ioa = 1 - (np.sum((y_pred - y_true) ** 2) / (ioa_denom + 1e-10))

    prefix = f"[{label}] " if label else ""
    log.info(f"{prefix}R²={r2:.3f}  RMSE={rmse:.2f}  MAE={mae:.2f}  MBE={mbe:+.2f}  IoA={ioa:.3f}  N={n:,}")
    return {"r2": r2, "rmse": rmse, "mae": mae, "mbe": mbe, "ioa": ioa, "n": n}


# ─────────────────────────────────────────────────────────────────────────────
# SPATIAL BLOCKED CV
# ─────────────────────────────────────────────────────────────────────────────

def run_spatial_blocked_cv(
    df: pd.DataFrame,
    features: list[str],
    n_folds: int = 5,
) -> pd.DataFrame:
    """
    Spatial blocked cross-validation: hold out groups of pixels.

    This tests the key question: can the model predict PM2.5 at unseen
    spatial locations using only their topographic features?
    """
    params = XGBOOST_DEFAULT_PARAMS.copy()
    params.pop("early_stopping_rounds", None)

    pixels = sorted(df["pixel_id"].unique())
    np.random.seed(RANDOM_SEED)
    np.random.shuffle(pixels)

    fold_size = len(pixels) // n_folds
    fold_metrics = []

    for fold in range(n_folds):
        start = fold * fold_size
        end = start + fold_size if fold < n_folds - 1 else len(pixels)
        test_pixels = set(pixels[start:end])

        train_mask = ~df["pixel_id"].isin(test_pixels)
        test_mask = df["pixel_id"].isin(test_pixels)

        X_tr = df.loc[train_mask, features]
        y_tr = df.loc[train_mask, TARGET]
        X_te = df.loc[test_mask, features]
        y_te = df.loc[test_mask, TARGET]

        model = xgb.XGBRegressor(**params)
        model.fit(X_tr, y_tr, verbose=False)
        pred = model.predict(X_te)

        m = compute_metrics(y_te, pred, label=f"Spatial Fold {fold+1} ({len(test_pixels)} pixels)")
        m["fold"] = fold + 1
        m["test_pixels"] = len(test_pixels)
        fold_metrics.append(m)

    cv_df = pd.DataFrame(fold_metrics)
    log.info(f"\nSpatial Blocked CV Summary:")
    for col in ["r2", "rmse", "mae", "ioa"]:
        log.info(f"  {col}: {cv_df[col].mean():.3f} ± {cv_df[col].std():.3f}")
    return cv_df


# ─────────────────────────────────────────────────────────────────────────────
# TEMPORAL BLOCKED CV (adapted for pixel data)
# ─────────────────────────────────────────────────────────────────────────────

def run_temporal_blocked_cv(
    df: pd.DataFrame,
    features: list[str],
    n_folds: int = 5,
) -> pd.DataFrame:
    """
    Temporal blocked CV on pixel data: hold out contiguous year blocks.
    All pixels for held-out years are in the test set.
    """
    params = XGBOOST_DEFAULT_PARAMS.copy()
    params.pop("early_stopping_rounds", None)

    years = sorted(df["date"].dt.year.unique())
    fold_size = len(years) // n_folds
    fold_metrics = []

    for fold in range(n_folds):
        start = fold * fold_size
        end = start + fold_size if fold < n_folds - 1 else len(years)
        test_years = set(years[start:end])

        train_mask = ~df["date"].dt.year.isin(test_years)
        test_mask = df["date"].dt.year.isin(test_years)

        X_tr = df.loc[train_mask, features]
        y_tr = df.loc[train_mask, TARGET]
        X_te = df.loc[test_mask, features]
        y_te = df.loc[test_mask, TARGET]

        model = xgb.XGBRegressor(**params)
        model.fit(X_tr, y_tr, verbose=False)
        pred = model.predict(X_te)

        m = compute_metrics(y_te, pred,
                            label=f"Temporal Fold {fold+1} ({min(test_years)}-{max(test_years)})")
        m["fold"] = fold + 1
        m["test_years"] = f"{min(test_years)}-{max(test_years)}"
        fold_metrics.append(m)

    cv_df = pd.DataFrame(fold_metrics)
    log.info(f"\nTemporal Blocked CV Summary:")
    for col in ["r2", "rmse", "mae", "ioa"]:
        log.info(f"  {col}: {cv_df[col].mean():.3f} ± {cv_df[col].std():.3f}")
    return cv_df


# ─────────────────────────────────────────────────────────────────────────────
# LOMO CV (adapted for pixel data)
# ─────────────────────────────────────────────────────────────────────────────

def run_lomo_cv(
    df: pd.DataFrame,
    features: list[str],
) -> pd.DataFrame:
    """LOMO CV on pixel data: hold out one calendar month at a time."""
    params = XGBOOST_DEFAULT_PARAMS.copy()
    params.pop("early_stopping_rounds", None)

    months = sorted(df["date"].dt.month.unique())
    fold_metrics = []

    for month in months:
        test_mask = df["date"].dt.month == month
        train_mask = ~test_mask

        X_tr = df.loc[train_mask, features]
        y_tr = df.loc[train_mask, TARGET]
        X_te = df.loc[test_mask, features]
        y_te = df.loc[test_mask, TARGET]

        model = xgb.XGBRegressor(**params)
        model.fit(X_tr, y_tr, verbose=False)
        pred = model.predict(X_te)

        m = compute_metrics(y_te, pred, label=f"LOMO Month {month}")
        m["month"] = month
        fold_metrics.append(m)

    cv_df = pd.DataFrame(fold_metrics)
    log.info(f"\nLOMO CV Summary:")
    for col in ["r2", "rmse", "mae", "ioa"]:
        log.info(f"  {col}: {cv_df[col].mean():.3f} ± {cv_df[col].std():.3f}")
    return cv_df


# ─────────────────────────────────────────────────────────────────────────────
# SPATIAL PATTERN ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def analyze_spatial_predictions(df: pd.DataFrame, pred_col: str = "pm25_pixel_pred"):
    """Check whether predictions show valley-bottom > ridge pattern."""
    if pred_col not in df.columns:
        return

    pixel_summary = df.groupby("pixel_id").agg(
        lat=("lat", "first"),
        lon=("lon", "first"),
        elevation=("elevation", "first"),
        tpi=("tpi", "first"),
        vd_weight=("vd_weight", "first"),
        pm25_obs_mean=(TARGET, "mean"),
        pm25_pred_mean=(pred_col, "mean"),
    ).reset_index()

    pixel_summary = pixel_summary.sort_values("elevation")

    log.info("\n── Spatial Pattern Analysis ──")
    log.info(f"{'PID':>4} {'Elev':>6} {'TPI':>7} {'VDwt':>6} {'ObsMean':>8} {'PredMean':>9}")
    for _, px in pixel_summary.iterrows():
        log.info(f"{int(px['pixel_id']):>4} {px['elevation']:>6.0f} {px['tpi']:>7.0f} "
                 f"{px['vd_weight']:>6.3f} {px['pm25_obs_mean']:>8.2f} {px['pm25_pred_mean']:>9.2f}")

    # Valley floor vs ridge comparison
    low_elev = pixel_summary.nsmallest(10, "elevation")
    high_elev = pixel_summary.nlargest(10, "elevation")

    log.info(f"\n  Valley floor (10 lowest pixels): pred mean = {low_elev['pm25_pred_mean'].mean():.2f} µg/m³")
    log.info(f"  Ridge top (10 highest pixels):   pred mean = {high_elev['pm25_pred_mean'].mean():.2f} µg/m³")
    ratio = low_elev['pm25_pred_mean'].mean() / high_elev['pm25_pred_mean'].mean()
    log.info(f"  Valley/Ridge ratio: {ratio:.3f}")

    if ratio > 1.0:
        log.info("  Valley-bottom PM2.5 > ridge — spatial pattern is physically correct.")
    else:
        log.warning("  Ridge PM2.5 >= valley — model may not be learning spatial pattern correctly.")

    # Correlation between predicted and observed spatial pattern
    corr = pixel_summary["pm25_pred_mean"].corr(pixel_summary["pm25_obs_mean"])
    log.info(f"  Spatial correlation (pred vs obs pixel means): r = {corr:.3f}")

    return pixel_summary


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train Stage 1b pixel-level XGBoost")
    parser.add_argument("--no-shap", action="store_true", help="Skip SHAP analysis")
    args = parser.parse_args()

    # ── Load data ─────────────────────────────────────────────────────────────
    df = load_pixel_dataset()
    features = select_features(df)

    if not features:
        log.error("No features found.")
        return

    # ── Spatial blocked CV (THE key test for Stage 1b) ────────────────────────
    log.info("\n" + "=" * 60)
    log.info("── Spatial Blocked Cross-Validation ──")
    log.info("=" * 60)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    spatial_cv = run_spatial_blocked_cv(df, features)
    spatial_cv.to_csv(TABLES_DIR / "cv_results_spatial_pixel.csv", index=False)

    # ── Temporal blocked CV ───────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("── Temporal Blocked Cross-Validation ──")
    log.info("=" * 60)
    temporal_cv = run_temporal_blocked_cv(df, features)
    temporal_cv.to_csv(TABLES_DIR / "cv_results_temporal_pixel.csv", index=False)

    # ── LOMO CV ───────────────────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("── Leave-One-Month-Out Cross-Validation ──")
    log.info("=" * 60)
    lomo_cv = run_lomo_cv(df, features)
    lomo_cv.to_csv(TABLES_DIR / "cv_results_lomo_pixel.csv", index=False)

    # ── Train final model on ALL data ─────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info(f"── Training Final Pixel Model on All {len(df):,} Samples ──")
    log.info("=" * 60)

    X_all = df[features]
    y_all = df[TARGET]

    params = XGBOOST_DEFAULT_PARAMS.copy()
    n_val = max(1000, len(X_all) // 10)

    # Use last N samples as early-stopping validation
    model = xgb.XGBRegressor(**params)
    model.fit(
        X_all.iloc[:-n_val], y_all.iloc[:-n_val],
        eval_set=[(X_all.iloc[-n_val:], y_all.iloc[-n_val:])],
        verbose=50,
    )
    log.info(f"Best iteration: {model.best_iteration}")

    # ── Train-fit metrics ─────────────────────────────────────────────────────
    y_pred_all = model.predict(X_all)
    df["pm25_pixel_pred"] = y_pred_all
    compute_metrics(y_all, y_pred_all, label="Train-fit (all pixels)")

    # ── Spatial pattern analysis ──────────────────────────────────────────────
    pixel_summary = analyze_spatial_predictions(df)

    # ── SHAP Analysis ─────────────────────────────────────────────────────────
    if not args.no_shap:
        log.info("\n── SHAP Analysis (Pixel Model) ──")
        try:
            import shap
            X_sample = X_all.sample(min(1000, len(X_all)), random_state=RANDOM_SEED)
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample)

            importance = pd.DataFrame({
                "feature": features,
                "mean_abs_shap": np.abs(shap_values).mean(axis=0),
            }).sort_values("mean_abs_shap", ascending=False)
            importance["rank"] = range(1, len(importance) + 1)

            log.info("Top 15 features by mean |SHAP|:")
            for _, row in importance.head(15).iterrows():
                marker = " *PIXEL*" if row["feature"] in PIXEL_FEATURES else ""
                log.info(f"  {int(row['rank']):>2}. {row['feature']:<22} {row['mean_abs_shap']:.4f}{marker}")

            # Pixel-specific group importance
            total_shap = importance["mean_abs_shap"].sum()
            pixel_shap = importance[importance["feature"].isin(PIXEL_FEATURES)]["mean_abs_shap"].sum()
            log.info(f"\nPixel-specific features: {pixel_shap/total_shap:.1%} of total SHAP")

            importance.to_csv(TABLES_DIR / "shap_pixel_importance.csv", index=False)

            # Save SHAP summary plot
            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                FIGURES_DIR.mkdir(parents=True, exist_ok=True)
                plt.figure(figsize=(10, 8))
                shap.summary_plot(shap_values, X_sample, show=False, max_display=20)
                plt.tight_layout()
                plt.savefig(FIGURES_DIR / "shap_pixel_summary.png", dpi=150, bbox_inches="tight")
                plt.close()
                log.info(f"SHAP plot saved -> {FIGURES_DIR / 'shap_pixel_summary.png'}")
            except Exception as e:
                log.warning(f"Could not save SHAP plot: {e}")
        except ImportError:
            log.warning("shap not installed — skipping SHAP analysis")

    # ── Save model ────────────────────────────────────────────────────────────
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "xgboost_pixel_pm25.ubj"
    model.save_model(str(model_path))
    log.info(f"\nPixel model saved -> {model_path}")

    # ── Save pixel-level predictions ──────────────────────────────────────────
    pred_path = MERGED_DIR / "pm25_pixel_predictions.parquet"
    save_cols = ["date", "pixel_id", "lat", "lon", "elevation", "tpi",
                 "vd_weight", TARGET, "pm25_pixel_pred"]
    df[save_cols].to_parquet(pred_path, index=False)
    log.info(f"Pixel predictions saved -> {pred_path}")

    # ── Save pixel summary ────────────────────────────────────────────────────
    if pixel_summary is not None:
        pixel_summary.to_csv(TABLES_DIR / "pixel_spatial_summary.csv", index=False)
        log.info(f"Pixel summary saved -> {TABLES_DIR / 'pixel_spatial_summary.csv'}")

    # ── Final summary ─────────────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("STAGE 1b PIXEL MODEL — FINAL SUMMARY")
    log.info("=" * 60)
    log.info(f"  Spatial CV R²:  {spatial_cv['r2'].mean():.3f} ± {spatial_cv['r2'].std():.3f}")
    log.info(f"  Temporal CV R²: {temporal_cv['r2'].mean():.3f} ± {temporal_cv['r2'].std():.3f}")
    log.info(f"  LOMO CV R²:     {lomo_cv['r2'].mean():.3f} ± {lomo_cv['r2'].std():.3f}")
    log.info(f"  Train-fit R²:   {r2_score(y_all, y_pred_all):.3f}")
    log.info(f"  Total samples:  {len(df):,}")
    log.info(f"  Pixels:         {df['pixel_id'].nunique()}")


if __name__ == "__main__":
    main()
