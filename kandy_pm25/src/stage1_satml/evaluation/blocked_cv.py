"""
blocked_cv.py — Rigorous blocked cross-validation for the Kandy PM2.5 Stage 1 model.

Three mandatory CV strategies (§1.5 of RESEARCH_PROJECT_DESIGN.md):
  1. Temporal CV       — TimeSeriesSplit, no future leakage
  2. Spatial Blocked CV — Leave-one-quadrant-out (4 spatial blocks)
  3. Leave-Season-Out CV — Train on 3 seasons, test on held-out season

Do NOT use random splits. Spatially adjacent pixels share correlated errors.
Random splits overestimate R² by 10–25% (Valavi et al. 2019, Methods Ecol Evol).

Usage:
    results = run_all_cv(df, features, target="pm25_observed")
    print(results)  # DataFrame with R², RMSE, MAE per fold/strategy
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import CV_FOLDS, LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("blocked_cv")

# Sri Lanka monsoon season definitions
SEASONS = {
    "NE_Monsoon":   [12, 1, 2, 3],      # Dec–Mar: Northeast Monsoon (drier in Kandy)
    "SW_Monsoon":   [5, 6, 7, 8, 9],    # May–Sep: Southwest Monsoon (heavy cloud, low AOD)
    "Inter_Monsoon": [4, 10, 11],        # Apr + Oct–Nov: Inter-Monsoon (convective)
}


# ─────────────────────────────────────────────────────────────────────────────
# METRIC HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def compute_metrics(y_true: pd.Series, y_pred: np.ndarray, label: str = "") -> Dict:
    """Return dict of standard evaluation metrics."""
    mask = ~pd.isna(y_true)
    y_t = y_true[mask].values
    y_p = y_pred[mask]
    if len(y_t) < 5:
        return {"label": label, "n": len(y_t), "R2": np.nan, "RMSE": np.nan, "MAE": np.nan}
    return {
        "label": label,
        "n":     len(y_t),
        "R2":    round(float(r2_score(y_t, y_p)), 4),
        "RMSE":  round(float(np.sqrt(mean_squared_error(y_t, y_p))), 4),
        "MAE":   round(float(mean_absolute_error(y_t, y_p)), 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY 1: TEMPORAL CV
# ─────────────────────────────────────────────────────────────────────────────

def temporal_cv(
    df: pd.DataFrame,
    features: List[str],
    target: str,
    model_factory,
    n_splits: int = CV_FOLDS,
    date_col: str = "date",
) -> List[Dict]:
    """
    Temporal (time-series) cross-validation — expanding window.

    Sorts by date and uses TimeSeriesSplit so that each test fold is always
    in the future relative to the training folds.

    Args:
        df            : DataFrame with features, target, and date column
        features      : Feature column names
        target        : Target column name
        model_factory : Callable() → fitted-or-unfitted model (with fit/predict)
        n_splits      : Number of CV folds
        date_col      : Name of date column

    Returns:
        List of metric dicts, one per fold.
    """
    log.info(f"Temporal CV ({n_splits} folds) …")
    df_sorted = df.dropna(subset=[target]).sort_values(date_col).reset_index(drop=True)
    X = df_sorted[features]
    y = df_sorted[target]

    tscv = TimeSeriesSplit(n_splits=n_splits)
    results = []
    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        model = model_factory()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = compute_metrics(y_test, y_pred, label=f"temporal_fold{fold+1}")
        log.info(f"  Fold {fold+1}: R²={metrics['R2']:.3f}  RMSE={metrics['RMSE']:.3f}")
        results.append(metrics)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY 2: SPATIAL BLOCKED CV (leave-one-quadrant-out)
# ─────────────────────────────────────────────────────────────────────────────

def assign_spatial_block(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
) -> pd.Series:
    """
    Assign each row to one of four spatial quadrants (NW, NE, SW, SE).

    Kandy bounding box is divided at its centroid. Provides 4 spatial folds
    for leave-one-quadrant-out cross-validation.
    """
    lat_mid = df[lat_col].median()
    lon_mid = df[lon_col].median()
    conditions = [
        (df[lat_col] >= lat_mid) & (df[lon_col] <  lon_mid),  # NW
        (df[lat_col] >= lat_mid) & (df[lon_col] >= lon_mid),  # NE
        (df[lat_col] <  lat_mid) & (df[lon_col] <  lon_mid),  # SW
        (df[lat_col] <  lat_mid) & (df[lon_col] >= lon_mid),  # SE
    ]
    block_names = ["NW", "NE", "SW", "SE"]
    return np.select(conditions, block_names, default="NW")


def spatial_blocked_cv(
    df: pd.DataFrame,
    features: List[str],
    target: str,
    model_factory,
    lat_col: str = "lat",
    lon_col: str = "lon",
) -> List[Dict]:
    """
    Spatial blocked (leave-one-quadrant-out) CV.

    Each fold holds out one geographical quadrant as the test set.
    This tests generalisation to unobserved spatial locations.

    Returns:
        List of metric dicts, one per quadrant.
    """
    log.info("Spatial blocked CV (4 quadrants) …")
    df_cv = df.dropna(subset=[target]).copy()
    if lat_col not in df_cv.columns or lon_col not in df_cv.columns:
        log.warning("lat/lon columns not found — skipping spatial blocked CV")
        return []

    df_cv["_block"] = assign_spatial_block(df_cv, lat_col, lon_col)
    results = []
    for block in ["NW", "NE", "SW", "SE"]:
        train_mask = df_cv["_block"] != block
        X_train = df_cv.loc[train_mask, features]
        y_train = df_cv.loc[train_mask, target]
        X_test  = df_cv.loc[~train_mask, features]
        y_test  = df_cv.loc[~train_mask, target]
        if len(y_test) < 5:
            log.warning(f"  Block {block}: too few test samples ({len(y_test)}) — skipping")
            continue
        model = model_factory()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = compute_metrics(y_test, y_pred, label=f"spatial_block_{block}")
        log.info(f"  Block {block}: R²={metrics['R2']:.3f}  RMSE={metrics['RMSE']:.3f}  n_test={len(y_test)}")
        results.append(metrics)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY 3: LEAVE-SEASON-OUT CV
# ─────────────────────────────────────────────────────────────────────────────

def leave_season_out_cv(
    df: pd.DataFrame,
    features: List[str],
    target: str,
    model_factory,
    date_col: str = "date",
) -> List[Dict]:
    """
    Leave-season-out cross-validation.

    Trains on all months EXCEPT the held-out season; tests on the held-out season.
    Three folds: hold-out NE Monsoon, SW Monsoon, and Inter-Monsoon.

    Key diagnostic: if SW Monsoon R² is much lower than other seasons, it
    confirms the cloud-gap bias propagation risk flagged in §3.10.

    Returns:
        List of metric dicts, one per season.
    """
    log.info("Leave-season-out CV (3 seasons) …")
    df_cv = df.dropna(subset=[target]).copy()

    if date_col not in df_cv.columns:
        log.warning(f"'{date_col}' column not found — skipping season CV")
        return []

    df_cv["_month"] = pd.to_datetime(df_cv[date_col]).dt.month
    results = []
    for season_name, test_months in SEASONS.items():
        test_mask  = df_cv["_month"].isin(test_months)
        train_mask = ~test_mask
        X_train, y_train = df_cv.loc[train_mask, features], df_cv.loc[train_mask, target]
        X_test,  y_test  = df_cv.loc[test_mask,  features], df_cv.loc[test_mask,  target]
        if len(y_test) < 5:
            log.warning(f"  Season {season_name}: too few test samples — skipping")
            continue
        model = model_factory()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = compute_metrics(y_test, y_pred, label=f"season_{season_name}")
        log.info(f"  Season {season_name}: R²={metrics['R2']:.3f}  RMSE={metrics['RMSE']:.3f}  n_test={len(y_test)}")
        results.append(metrics)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# MASTER RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_all_cv(
    df: pd.DataFrame,
    features: List[str],
    model_factory,
    target: str = "pm25_observed",
    date_col: str = "date",
    lat_col: str = "lat",
    lon_col: str = "lon",
) -> pd.DataFrame:
    """
    Run all three CV strategies and return a combined results DataFrame.

    Reports the lowest R² prominently — that is the scientifically honest number.
    """
    log.info("═══ BLOCKED CROSS-VALIDATION SUITE ═══")
    all_results = []
    all_results.extend(temporal_cv(df, features, target, model_factory, date_col=date_col))
    all_results.extend(spatial_blocked_cv(df, features, target, model_factory, lat_col=lat_col, lon_col=lon_col))
    all_results.extend(leave_season_out_cv(df, features, target, model_factory, date_col=date_col))

    results_df = pd.DataFrame(all_results)
    if not results_df.empty:
        log.info("═══ CV SUMMARY ═══")
        log.info(f"  Temporal CV mean R²:      {results_df[results_df['label'].str.startswith('temporal')]['R2'].mean():.3f}")
        log.info(f"  Spatial blocked CV mean R²:{results_df[results_df['label'].str.startswith('spatial')]['R2'].mean():.3f}")
        log.info(f"  Season CV mean R²:         {results_df[results_df['label'].str.startswith('season')]['R2'].mean():.3f}")
        log.info(f"  ⚠  Lowest R² (honest number): {results_df['R2'].min():.3f}")

    return results_df
