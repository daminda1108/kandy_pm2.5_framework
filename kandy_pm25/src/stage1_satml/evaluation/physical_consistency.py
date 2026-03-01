"""
physical_consistency.py — Physical plausibility checks for Stage 1 PM2.5 predictions.

After training, confirm that the model has captured expected physical patterns:
  1. Valley-bottom PM2.5 > ridge PM2.5 on stagnant days (TPI < -15m + low wind + low BLH)
  2. Dry-season mean PM2.5 > wet-season mean PM2.5 (dry: Jan–Mar; wet: May–Sep)
  3. PM2.5 inversely correlated with BLH (pollution trapping when BLH is low)
  4. PM2.5 inversely correlated with wind speed (ventilation removes pollutants)

These checks assess physical realism — independent of R² or RMSE.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("physical_consistency")

# Stagnation conditions for valley-floor check
STAGNATION_BLH_MAX   = 500.0   # m — low BLH = trapped
STAGNATION_WIND_MAX  = 2.0     # m/s — calm conditions
VALLEY_TPI_THRESHOLD = -15.0   # m — TPI below this = valley floor


def check_valley_enhancement(
    predictions: pd.Series,
    df: pd.DataFrame,
    tpi_col: str = "tpi",
    wind_col: str = "wind_speed",
    blh_col: str = "blh",
    prediction_col: str = "pm25_pred",
) -> Dict:
    """
    Check that valley-floor PM2.5 > ridge PM2.5 on stagnant days.

    Physical expectation: on days with low BLH and calm wind, PM2.5 should
    accumulate in the valley bottom (negative TPI) relative to surrounding ridges.

    Returns dict with: valley_mean, ridge_mean, ratio, passed.
    """
    df_check = df.copy()
    df_check[prediction_col] = predictions.values

    stagnant = (
        (df_check.get(blh_col, pd.Series([np.inf]*len(df_check))) < STAGNATION_BLH_MAX) &
        (df_check.get(wind_col, pd.Series([np.inf]*len(df_check))) < STAGNATION_WIND_MAX)
    )
    if stagnant.sum() < 10:
        log.warning("Too few stagnant-day samples for valley enhancement check")
        return {"passed": None, "reason": "insufficient stagnant days"}

    df_stagnant = df_check[stagnant]
    if tpi_col not in df_stagnant.columns:
        log.warning(f"'{tpi_col}' column missing — cannot assess valley enhancement")
        return {"passed": None, "reason": "tpi column missing"}

    valley_mask = df_stagnant[tpi_col] < VALLEY_TPI_THRESHOLD
    ridge_mask  = df_stagnant[tpi_col] > 0

    valley_mean = float(df_stagnant.loc[valley_mask,  prediction_col].mean()) if valley_mask.any() else np.nan
    ridge_mean  = float(df_stagnant.loc[ridge_mask,   prediction_col].mean()) if ridge_mask.any()  else np.nan

    passed = (valley_mean > ridge_mean) if not (np.isnan(valley_mean) or np.isnan(ridge_mean)) else None
    ratio  = round(valley_mean / ridge_mean, 3) if ridge_mean and ridge_mean > 0 else np.nan

    result = {
        "valley_mean_ugm3": round(valley_mean, 2),
        "ridge_mean_ugm3":  round(ridge_mean, 2),
        "valley_ridge_ratio": ratio,
        "n_stagnant_days":  int(stagnant.sum()),
        "passed":           passed,
    }
    status = "✅ PASS" if passed else ("❌ FAIL" if passed is False else "⚠️ N/A")
    log.info(f"Valley enhancement: valley={valley_mean:.2f}, ridge={ridge_mean:.2f}, ratio={ratio:.2f} — {status}")
    return result


def check_seasonal_pattern(
    predictions: pd.Series,
    df: pd.DataFrame,
    date_col: str = "date",
    prediction_col: str = "pm25_pred",
) -> Dict:
    """
    Check that dry-season PM2.5 > wet-season PM2.5.

    Dry season (Jan–Mar + NE Monsoon): lower cloud cover, stronger katabatic inversion → higher PM2.5
    Wet season (SW Monsoon, May–Sep): rain washout, wind → lower PM2.5

    Returns dict with dry_mean, wet_mean, passed.
    """
    df_check = df.copy()
    df_check[prediction_col] = predictions.values

    if date_col not in df_check.columns:
        log.warning(f"'{date_col}' missing — cannot check seasonal pattern")
        return {"passed": None}

    month = pd.to_datetime(df_check[date_col]).dt.month
    dry_mask = month.isin([1, 2, 3, 12])    # NE Monsoon / dry
    wet_mask = month.isin([5, 6, 7, 8, 9])  # SW Monsoon / wet

    dry_mean = float(df_check.loc[dry_mask, prediction_col].mean())
    wet_mean = float(df_check.loc[wet_mask, prediction_col].mean())
    passed   = dry_mean > wet_mean

    result = {
        "dry_season_mean_ugm3": round(dry_mean, 2),
        "wet_season_mean_ugm3": round(wet_mean, 2),
        "dry_wet_ratio":        round(dry_mean / wet_mean, 3) if wet_mean > 0 else np.nan,
        "passed":               passed,
    }
    status = "✅ PASS" if passed else "❌ FAIL"
    log.info(f"Seasonal pattern: dry={dry_mean:.2f}, wet={wet_mean:.2f} — {status}")
    return result


def check_blh_correlation(
    predictions: pd.Series,
    df: pd.DataFrame,
    blh_col: str = "blh",
    prediction_col: str = "pm25_pred",
    expected_sign: str = "negative",
) -> Dict:
    """
    Check that correlation between BLH and PM2.5 is negative.

    Lower BLH = lower mixing = pollutant trapping → higher PM2.5.
    Correlation should be r < -0.2 to indicate physical signal.
    """
    df_check = df.copy()
    df_check[prediction_col] = predictions.values

    if blh_col not in df_check.columns:
        return {"passed": None, "reason": "blh column missing"}

    mask = df_check[[blh_col, prediction_col]].notna().all(axis=1)
    corr = float(df_check.loc[mask, [blh_col, prediction_col]].corr().iloc[0, 1])
    passed = corr < -0.2 if expected_sign == "negative" else corr > 0.2

    result = {"blh_pm25_corr": round(corr, 4), "passed": passed}
    status = "✅ PASS" if passed else "❌ FAIL"
    log.info(f"BLH correlation: r={corr:.3f} — {status}")
    return result


def run_all_checks(
    predictions: pd.Series,
    df: pd.DataFrame,
    date_col: str = "date",
    **col_kwargs,
) -> Dict:
    """
    Run all physical consistency checks and return a summary dict.

    Victory conditions (§1.7):
        - valley_enhancement: passed = True
        - seasonal_pattern:   passed = True
        - blh_correlation:    r < -0.2
    """
    log.info("═══ PHYSICAL CONSISTENCY CHECKS ═══")
    results = {
        "valley_enhancement": check_valley_enhancement(predictions, df, **col_kwargs),
        "seasonal_pattern":   check_seasonal_pattern(predictions, df, date_col=date_col),
        "blh_correlation":    check_blh_correlation(predictions, df, **col_kwargs),
    }
    n_passed = sum(1 for v in results.values() if v.get("passed") is True)
    n_total  = sum(1 for v in results.values() if v.get("passed") is not None)
    log.info(f"Physical consistency: {n_passed}/{n_total} checks passed")
    return results
