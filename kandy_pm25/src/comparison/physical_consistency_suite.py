"""
physical_consistency_suite.py — End-to-end physical consistency tests across all stages.

Runs a battery of physics-based checks on the Stage 1 and Stage 3 outputs
to confirm that both models respect well-established atmospheric science.
Tests are drawn from Stull (1988), Seinfeld & Pandis (2006), and WHO guidelines.

SUITE STRUCTURE:
  Test 1 — NON-NEGATIVITY: All PM2.5 values ≥ 0.
  Test 2 — REASONABLE RANGE: PM2.5 ∈ [0, 500] µg/m³ (WHO alert level).
  Test 3 — BLH ANTICORRELATION: PM2.5 should decrease as BLH rises (r < -0.3).
  Test 4 — PRECIP ANTICORRELATION: Rain days should have lower PM2.5 (t-test p < 0.05).
  Test 5 — VALLEY ENHANCEMENT: Valley-centre PM2.5 > upland (spatial mean ratio > 1.1).
  Test 6 — WIND DILUTION: High-wind hours should have lower PM2.5 (r < -0.2).
  Test 7 — K BOUNDS: Diffusivity Kx, Ky ∈ [1, 100] m²/s (Stage 3 only).
  Test 8 — PDE RESIDUAL: Normalised |R|² < 0.1 at convergence (Stage 3 only).

Each test returns pass/fail with the measured value and expected direction.
The full suite is logged as a table and saved to TABLES_DIR.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import LOG_FORMAT, LOG_DATEFMT, TABLES_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("physical_consistency_suite")


def _pearson_r(x: np.ndarray, y: np.ndarray) -> float:
    """Pearson r, returning 0.0 on failure."""
    try:
        from scipy.stats import pearsonr
        mask = ~(np.isnan(x) | np.isnan(y))
        if mask.sum() < 5:
            return np.nan
        return float(pearsonr(x[mask], y[mask])[0])
    except Exception:
        return np.nan


_RESULTS: list = []


def _record(name: str, passed: bool, value, expected: str, note: str = "") -> dict:
    icon = "✅" if passed else "❌"
    row  = {"test": name, "passed": passed, "value": value, "expected": expected, "note": note}
    _RESULTS.append(row)
    log.info(f"  {icon} {name}: {value} (expected {expected}) {note}")
    return row


# ── Individual tests ────────────────────────────────────────────────────────

def test_non_negativity(pm25: np.ndarray, stage: str = "S1") -> dict:
    frac_neg = float((pm25 < 0).mean())
    return _record(f"Non-negativity [{stage}]", frac_neg == 0, f"{frac_neg:.2%} negative", "0%")


def test_reasonable_range(pm25: np.ndarray, stage: str = "S1") -> dict:
    frac_out = float(((pm25 < 0) | (pm25 > 500)).mean())
    return _record(f"Reasonable range 0–500 µg/m³ [{stage}]", frac_out < 0.01,
                   f"{frac_out:.2%} out-of-range", "<1%")


def test_blh_anticorrelation(pm25_series: pd.Series, blh_series: pd.Series, stage: str = "S1") -> dict:
    r = _pearson_r(pm25_series.values, blh_series.values)
    return _record(f"BLH anticorrelation [{stage}]", r < -0.3, f"r={r:.3f}", "r < -0.3",
                   "PM2.5 should decline as BLH rises")


def test_precip_suppression(pm25_series: pd.Series, precip_series: pd.Series, stage: str = "S1") -> dict:
    """Rain days (tp > 1 mm) should have significantly lower PM2.5."""
    try:
        from scipy.stats import ttest_ind
        rain_mask = precip_series > 1.0
        dry_vals  = pm25_series[~rain_mask].dropna().values
        wet_vals  = pm25_series[rain_mask].dropna().values
        if len(wet_vals) < 5 or len(dry_vals) < 5:
            return _record(f"Precip suppression [{stage}]", None, "insufficient data", "p < 0.05")
        stat, p = ttest_ind(dry_vals, wet_vals, alternative="greater")
        passed   = p < 0.05 and dry_vals.mean() > wet_vals.mean()
        return _record(f"Precip suppression [{stage}]", passed,
                       f"dry={dry_vals.mean():.1f}, wet={wet_vals.mean():.1f} µg/m³, p={p:.3f}",
                       "dry > wet, p < 0.05")
    except ImportError:
        return _record(f"Precip suppression [{stage}]", None, "scipy not available", "p < 0.05")


def test_valley_enhancement(valley_pm25: np.ndarray, upland_pm25: np.ndarray, stage: str = "S1") -> dict:
    ratio = float(np.nanmean(valley_pm25) / (np.nanmean(upland_pm25) + 1e-9))
    return _record(f"Valley enhancement [{stage}]", ratio > 1.1,
                   f"ratio={ratio:.3f}", ">1.1 (valley > upland)",
                   "Kandy bowl should trap PM2.5")


def test_wind_dilution(pm25_series: pd.Series, wind_speed: pd.Series, stage: str = "S1") -> dict:
    ws = np.sqrt(wind_speed ** 2) if wind_speed.ndim == 1 else wind_speed
    r  = _pearson_r(pm25_series.values, ws.values)
    return _record(f"Wind dilution [{stage}]", r < -0.2, f"r={r:.3f}", "r < -0.2",
                   "Higher wind → lower PM2.5")


def test_k_bounds(Kx: np.ndarray, Ky: np.ndarray, k_min: float = 1.0, k_max: float = 100.0) -> dict:
    frac_kx = float(np.mean((Kx >= k_min) & (Kx <= k_max)))
    frac_ky = float(np.mean((Ky >= k_min) & (Ky <= k_max)))
    passed  = frac_kx > 0.9 and frac_ky > 0.9
    return _record("K bounds [S3]", passed,
                   f"Kx={frac_kx:.1%} valid, Ky={frac_ky:.1%} valid",
                   ">90% in [1,100] m²/s")


def test_pde_residual(residual_norm: np.ndarray) -> dict:
    max_r = float(np.nanmax(residual_norm))
    mean_r = float(np.nanmean(residual_norm))
    return _record("PDE residual [S3]", mean_r < 0.1,
                   f"mean |R|²_norm={mean_r:.4f}, max={max_r:.4f}",
                   "mean < 0.1 at convergence")


# ── Master runner ────────────────────────────────────────────────────────────

def run_full_suite(
    pm25_s1:     np.ndarray,
    pm25_s3:     Optional[np.ndarray] = None,
    era5_df:     Optional[pd.DataFrame] = None,
    valley_mask: Optional[np.ndarray] = None,
    Kx:          Optional[np.ndarray] = None,
    Ky:          Optional[np.ndarray] = None,
    residual:    Optional[np.ndarray] = None,
    save:        bool = True,
) -> pd.DataFrame:
    """
    Run all physical consistency tests and return a pass/fail table.

    Args:
        pm25_s1     : Stage 1 PM2.5 values (1D array, any date range)
        pm25_s3     : Stage 3 PM2.5 values (optional)
        era5_df     : ERA5 DataFrame with blh, tp, u10, v10 aligned to pm25 dates
        valley_mask : Boolean mask for valley interior points
        Kx, Ky      : Learned diffusivity fields (Stage 3 only)
        residual    : Normalised PDE residual (Stage 3 only)
        save        : Save results table to CSV

    Returns:
        DataFrame with test results
    """
    global _RESULTS
    _RESULTS = []

    log.info("═══ PHYSICAL CONSISTENCY SUITE ═══")

    # Stage 1 tests
    test_non_negativity(pm25_s1, "S1")
    test_reasonable_range(pm25_s1, "S1")

    if era5_df is not None:
        pm_s = pd.Series(pm25_s1[:len(era5_df)])
        if "blh" in era5_df.columns:
            test_blh_anticorrelation(pm_s, era5_df["blh"], "S1")
        if "tp" in era5_df.columns:
            test_precip_suppression(pm_s, era5_df["tp"], "S1")
        if "u10" in era5_df.columns and "v10" in era5_df.columns:
            ws = np.sqrt(era5_df["u10"] ** 2 + era5_df["v10"] ** 2)
            test_wind_dilution(pm_s, pd.Series(ws.values), "S1")

    if valley_mask is not None and valley_mask.any():
        test_valley_enhancement(pm25_s1[valley_mask], pm25_s1[~valley_mask], "S1")

    # Stage 3 tests (optional)
    if pm25_s3 is not None:
        test_non_negativity(pm25_s3, "S3")
        test_reasonable_range(pm25_s3, "S3")
        if valley_mask is not None:
            test_valley_enhancement(pm25_s3[valley_mask], pm25_s3[~valley_mask], "S3")

    if Kx is not None and Ky is not None:
        test_k_bounds(Kx, Ky)

    if residual is not None:
        test_pde_residual(residual)

    result_df = pd.DataFrame(_RESULTS)
    n_pass = result_df["passed"].eq(True).sum()
    n_fail = result_df["passed"].eq(False).sum()
    log.info(f"\nSuite complete: {n_pass} passed, {n_fail} failed out of {len(result_df)} tests.")

    if save:
        TABLES_DIR.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(TABLES_DIR / "physical_consistency_suite.csv", index=False)
        log.info(f"Suite results saved → {TABLES_DIR / 'physical_consistency_suite.csv'}")

    return result_df
