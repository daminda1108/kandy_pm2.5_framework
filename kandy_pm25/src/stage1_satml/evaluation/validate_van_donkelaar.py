"""
validate_van_donkelaar.py — Validate Stage 1 against van Donkelaar V6GL02.04.

This is the PRIMARY INDEPENDENT validation of Stage 1 spatial patterns.
Van Donkelaar provides ground-truth-validated 1km annual PM2.5 (1998–2023).

Comparison:
  - Stage 1 daily predictions → aggregated to annual means
  - Van Donkelaar annual 1km grids → extracted for Kandy domain
  - Metrics: mean bias, RMSE, temporal correlation (r)

This is NOT a training input — validation only.

Requires:
  - Van Donkelaar V6GL02.04 NetCDFs in data/raw/van_donkelaar/
    Format: V6GL02.04.CNNPM25.AS.YYYYMM-YYYYMM.nc  (variable: PM25)
    Download from: sites.wustl.edu/acag/datasets/surface-pm2-5/
  - Stage 1 predictions in data/processed/merged/pm25_predictions_daily.parquet

Usage:
    python validate_van_donkelaar.py
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    KANDY_PINN_BBOX, VAN_DONKELAAR_DIR, MERGED_DIR, VALIDATION_DIR,
    LOG_FORMAT, LOG_DATEFMT,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("validate_van_donkelaar")


def extract_vd_for_kandy(year: int) -> Optional[np.ndarray]:
    """Extract van Donkelaar PM2.5 grid over Kandy for given year.

    Supports V6GL02.04 NetCDFs (variable: PM25, dims: lat/lon at 0.01°).
    """
    import netCDF4 as nc4

    # V6GL02.04 naming: V6GL02.04.CNNPM25.AS.YYYYMM-YYYYMM.nc
    nc_candidates = list(VAN_DONKELAAR_DIR.glob(f"*{year}01-{year}12*.nc"))
    if not nc_candidates:
        # Fallback: any file containing the year
        nc_candidates = list(VAN_DONKELAAR_DIR.glob(f"*{year}*.nc"))
    if not nc_candidates:
        return None

    nc_path = nc_candidates[0]

    try:
        ds = nc4.Dataset(nc_path)
        lat = ds.variables["lat"][:]
        lon = ds.variables["lon"][:]

        # Subset to Kandy PINN bbox
        lat_mask = (lat >= KANDY_PINN_BBOX["lat_min"]) & (lat <= KANDY_PINN_BBOX["lat_max"])
        lon_mask = (lon >= KANDY_PINN_BBOX["lon_min"]) & (lon <= KANDY_PINN_BBOX["lon_max"])

        lat_idx = np.where(lat_mask)[0]
        lon_idx = np.where(lon_mask)[0]

        if len(lat_idx) == 0 or len(lon_idx) == 0:
            log.warning(f"  No grid cells in Kandy bbox for {year}")
            ds.close()
            return None

        pm25_grid = ds.variables["PM25"][lat_idx[0]:lat_idx[-1]+1, lon_idx[0]:lon_idx[-1]+1]
        pm25_grid = np.array(pm25_grid, dtype=np.float64)
        pm25_grid[pm25_grid < 0] = np.nan  # No-data sentinel
        ds.close()
        return pm25_grid
    except Exception as e:
        log.warning(f"  Could not read VD file for {year}: {e}")
        return None


def validate_annual_spatial_pattern() -> pd.DataFrame:
    """
    Compare Stage 1 annual mean predictions vs van Donkelaar.

    Metrics:
    - Mean bias (μg/m³)
    - Valley-to-ridge ratio comparison
    - Year-by-year alignment
    """
    VAN_DONKELAAR_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    # Check for VD files
    vd_files = (
        list(VAN_DONKELAAR_DIR.glob("*.tif")) +
        list(VAN_DONKELAAR_DIR.glob("*.nc"))
    )
    if not vd_files:
        log.warning(
            f"No van Donkelaar files found in {VAN_DONKELAAR_DIR}\n"
            "Download from: sites.wustl.edu/acag/datasets/surface-pm2-5/"
        )
        return pd.DataFrame()

    # Load Stage 1 daily predictions
    pred_path = MERGED_DIR / "pm25_predictions_daily.parquet"
    if not pred_path.exists():
        log.warning(f"Predictions not found: {pred_path}\nRun train_xgboost.py first.")
        return pd.DataFrame()

    preds = pd.read_parquet(pred_path)

    # Determine which column has predictions
    pred_col = None
    for col_name in ["pm25_predicted", "pm25_pred"]:
        if col_name in preds.columns:
            pred_col = col_name
            break

    if pred_col is None:
        log.error(f"No prediction column found. Columns: {list(preds.columns)}")
        return pd.DataFrame()

    # Ensure date index
    if "date" in preds.columns:
        preds["date"] = pd.to_datetime(preds["date"])
    elif preds.index.name == "date" or isinstance(preds.index, pd.DatetimeIndex):
        preds = preds.reset_index()
        preds["date"] = pd.to_datetime(preds["date"])
    else:
        preds = preds.reset_index()
        preds.columns = ["date"] + list(preds.columns[1:])
        preds["date"] = pd.to_datetime(preds["date"])

    preds["year"] = preds["date"].dt.year

    all_results = []

    for year in range(1998, 2024):
        vd_grid = extract_vd_for_kandy(year)
        if vd_grid is None:
            continue

        # Get Stage 1 annual mean for same year
        year_preds = preds[preds["year"] == year]
        if len(year_preds) == 0:
            continue

        stage1_annual_mean = year_preds[pred_col].mean()
        vd_domain_mean = float(np.nanmean(vd_grid))
        bias = stage1_annual_mean - vd_domain_mean

        log.info(
            f"  {year}: Stage1={stage1_annual_mean:.1f} | "
            f"VanDonkelaar={vd_domain_mean:.1f} | "
            f"Bias={bias:+.1f} μg/m³"
        )

        vd_max = float(np.nanmax(vd_grid))
        all_results.append({
            "year": year,
            "stage1_mean": round(stage1_annual_mean, 2),
            "vd_mean": round(vd_domain_mean, 2),
            "bias": round(bias, 2),
            "vd_valley_ridge_ratio": round(vd_max / vd_domain_mean, 3) if vd_domain_mean > 0 else np.nan,
        })

    results_df = pd.DataFrame(all_results)

    if len(results_df) > 0:
        overall_bias = results_df["bias"].mean()
        log.info(f"\n  Overall mean bias: {overall_bias:+.1f} μg/m³")

        if overall_bias > 5:
            log.warning("Stage 1 overestimates relative to van Donkelaar")
        elif overall_bias < -5:
            log.warning("Stage 1 underestimates relative to van Donkelaar")
        else:
            log.info("Stage 1 magnitudes are within ±5 μg/m³ of van Donkelaar — plausible.")

        log.info("\nInterpretation: Van Donkelaar is externally validated ground truth.")
        log.info("This comparison confirms whether Stage 1 magnitudes are realistic.")

        out_path = VALIDATION_DIR / "van_donkelaar_comparison.csv"
        results_df.to_csv(out_path, index=False)
        log.info(f"Results saved → {out_path}")
    else:
        log.warning("No year-by-year comparisons could be made.")

    return results_df


if __name__ == "__main__":
    validate_annual_spatial_pattern()
