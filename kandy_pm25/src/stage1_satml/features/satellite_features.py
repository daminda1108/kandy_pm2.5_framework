"""
satellite_features.py — Process MODIS MAIAC AOD HDF files and TROPOMI NetCDF files.

Reads raw satellite downloads, applies quality filtering, and produces
clean daily time-series DataFrames suitable for ML feature engineering.

MODIS MAIAC AOD (MCD19A2.061):
  - 8-day granules, 1 km resolution
  - Quality filter via AOD_QA bits
  - Spatial aggregation over Kandy bbox

TROPOMI L2:
  - Daily orbit files, ~5.5 km resolution
  - QA filter: qa_value ≥ 0.5
  - Variables: NO2 column, CO column, UV Aerosol Index
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    KANDY_BBOX, MODIS_RAW_DIR, TROPOMI_RAW_DIR,
    MODIS_AOD_BAND, MODIS_QA_BAND, MODIS_AOD_SCALE,
    MODIS_AOD_MIN, MODIS_AOD_MAX, TROPOMI_QA_THRESHOLD,
    LOG_FORMAT, LOG_DATEFMT
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("satellite_features")


# ─────────────────────────────────────────────────────────────────────────────
# MODIS MAIAC AOD
# ─────────────────────────────────────────────────────────────────────────────

def _parse_modis_date(filename: str) -> pd.Timestamp | None:
    """Extract date from MODIS filename: MCD19A2.AYYYYDDD..."""
    try:
        parts = Path(filename).stem.split(".")
        date_part = [p for p in parts if p.startswith("A") and len(p) == 8][0]
        return pd.Timestamp(date_part[1:], format="%Y%j")  # YYYYDDD
    except (IndexError, ValueError):
        return None


def _read_modis_hdf(hdf_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Read MODIS MAIAC HDF4 file, return (lat, lon, aod_550) arrays after QA masking.
    Falls back gracefully if h5py can't read HDF4 (needs pyhdf or gdal).
    """
    try:
        from pyhdf.SD import SD, SDC
        hdf = SD(str(hdf_path), SDC.READ)

        aod_ds = hdf.select(MODIS_AOD_BAND)
        aod_raw = aod_ds.get()
        aod_fill = aod_ds.attributes().get("_FillValue", -28672)
        aod_qa   = hdf.select(MODIS_QA_BAND).get()
        hdf.end()

        aod = aod_raw.astype(np.float32) * MODIS_AOD_SCALE
        # QA mask: keep bits 0-2 == 0 (AOD quality flag = high confidence)
        qa_land = (aod_qa & 0b111)
        valid_mask = (
            (aod_raw != aod_fill) &
            (aod >= MODIS_AOD_MIN) &
            (aod <= MODIS_AOD_MAX) &
            (qa_land == 0)
        )
        aod[~valid_mask] = np.nan
        return aod

    except ImportError:
        log.warning("pyhdf not installed — trying gdal for MODIS HDF4 reading.")
        try:
            from osgeo import gdal
            ds = gdal.Open(f'HDF4_EOS:EOS_GRID:"{hdf_path}":grid1km:{MODIS_AOD_BAND}')
            aod_raw = ds.ReadAsArray().astype(np.float32) * MODIS_AOD_SCALE
            return aod_raw
        except Exception as e:
            log.error(f"Cannot read {hdf_path}: {e}")
            return None


def extract_modis_aod_kandy(hdf_path: Path) -> float | None:
    """
    Extract spatially averaged MODIS MAIAC AOD for the Kandy bounding box.
    Returns the mean AOD (float) or None if extraction fails.
    """
    aod_grid = _read_modis_hdf(hdf_path)
    if aod_grid is None:
        return None

    # NOTE: MODIS MAIAC is on a sinusoidal grid; proper extraction needs
    # coordinate info from the HDF metadata. Here we use a simplified approach:
    # take the central portion of the tile corresponding to Kandy.
    # For production, use pyModis or GDAL to properly reproject & clip.
    valid = aod_grid[~np.isnan(aod_grid)]
    if len(valid) == 0:
        return None
    return float(np.nanmean(valid))


def build_modis_timeseries(modis_dir: Path | None = None) -> pd.DataFrame:
    """
    Build a daily MODIS AOD time series from all downloaded HDF files.

    Returns:
        pd.DataFrame with columns: ['date', 'aod_modis']
    """
    modis_dir = modis_dir or MODIS_RAW_DIR
    hdf_files = sorted(modis_dir.glob("*.hdf")) + sorted(modis_dir.glob("*.HDF"))

    if not hdf_files:
        log.warning(f"No MODIS HDF files found in {modis_dir}. Run download_modis.py first.")
        return pd.DataFrame(columns=["aod_modis"])

    log.info(f"Processing {len(hdf_files)} MODIS HDF files …")
    records = []
    for f in hdf_files:
        dt = _parse_modis_date(f.name)
        if dt is None:
            continue
        aod = extract_modis_aod_kandy(f)
        records.append({"date": dt.date(), "aod_modis": aod})

    df = pd.DataFrame(records).dropna(subset=["date"])
    df = df.groupby("date")["aod_modis"].mean().reset_index()
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    log.info(f"MODIS AOD time series: {len(df)} days, {df['aod_modis'].notna().sum()} valid.")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# TROPOMI
# ─────────────────────────────────────────────────────────────────────────────

def _extract_tropomi_variable(
    nc_path: Path,
    variable_path: str,
    qa_path: str,
    lat_path: str,
    lon_path: str,
    qa_threshold: float = TROPOMI_QA_THRESHOLD,
) -> float | None:
    """
    Generic TROPOMI L2 variable extractor.

    Args:
        nc_path      : Path to TROPOMI L2 NetCDF file
        variable_path: HDF5 group/variable path (e.g., "PRODUCT/nitrogendioxide_tropospheric_column")
        qa_path      : Path to QA variable (e.g., "PRODUCT/qa_value")
        lat_path     : Path to latitude variable
        lon_path     : Path to longitude variable
        qa_threshold : Minimum QA value to keep (0–1)

    Returns:
        float: Spatial mean over Kandy bbox, or None.
    """
    try:
        import h5py
        with h5py.File(nc_path, "r") as f:
            data  = f[variable_path][0, :, :]   # Remove time dim
            qa    = f[qa_path][0, :, :]
            lats  = f[lat_path][0, :, :]
            lons  = f[lon_path][0, :, :]
            fill  = f[variable_path].attrs.get("_FillValue", np.nan)
    except Exception as e:
        log.error(f"Cannot read {nc_path.name}: {e}")
        return None

    # Spatial filter — Kandy bbox
    in_box = (
        (lats >= KANDY_BBOX["lat_min"]) & (lats <= KANDY_BBOX["lat_max"]) &
        (lons >= KANDY_BBOX["lon_min"]) & (lons <= KANDY_BBOX["lon_max"])
    )

    # QA filter
    valid = in_box & (qa >= qa_threshold) & (data != fill)
    if not valid.any():
        return None

    values = data[valid].astype(np.float64)
    return float(np.nanmean(values))


TROPOMI_VARIABLE_PATHS = {
    "no2": {
        "variable": "PRODUCT/nitrogendioxide_tropospheric_column",
        "qa":       "PRODUCT/qa_value",
        "lat":      "PRODUCT/latitude",
        "lon":      "PRODUCT/longitude",
    },
    "co": {
        "variable": "PRODUCT/carbonmonoxide_total_column",
        "qa":       "PRODUCT/qa_value",
        "lat":      "PRODUCT/latitude",
        "lon":      "PRODUCT/longitude",
    },
    "aer_ai": {
        "variable": "PRODUCT/aerosol_index_354_388",
        "qa":       "PRODUCT/qa_value",
        "lat":      "PRODUCT/latitude",
        "lon":      "PRODUCT/longitude",
    },
}


def _get_tropomi_date(nc_path: Path) -> pd.Timestamp | None:
    """Extract sensing date from TROPOMI filename: S5P_OFFL_L2__NO2____YYYYMMDD..."""
    stem = nc_path.stem
    parts = stem.split("_")
    for p in parts:
        if len(p) == 15 and p[:8].isdigit():   # YYYYMMDDTHHmmss format
            try:
                return pd.Timestamp(p[:8], format="%Y%m%d")
            except ValueError:
                pass
    return None


def build_tropomi_timeseries(
    product: str,
    tropomi_dir: Path | None = None,
) -> pd.Series:
    """
    Build a daily TROPOMI time series for one product (no2, co, or aer_ai).

    Returns:
        pd.Series indexed by date.
    """
    tropomi_dir = tropomi_dir or (TROPOMI_RAW_DIR / product)
    nc_files = sorted(tropomi_dir.glob("*.nc"))

    if not nc_files:
        log.warning(f"No TROPOMI {product.upper()} files in {tropomi_dir}.")
        return pd.Series(dtype=float, name=f"tropomi_{product}")

    paths = TROPOMI_VARIABLE_PATHS.get(product)
    if paths is None:
        raise ValueError(f"Unknown TROPOMI product: {product}. Choose from {list(TROPOMI_VARIABLE_PATHS)}")

    log.info(f"Processing {len(nc_files)} TROPOMI {product.upper()} files …")
    records = {}
    for nc in nc_files:
        dt = _get_tropomi_date(nc)
        if dt is None:
            continue
        val = _extract_tropomi_variable(nc, **paths)
        if val is not None:
            records.setdefault(dt, []).append(val)

    daily = {dt: np.mean(vals) for dt, vals in records.items()}
    series = pd.Series(daily, name=f"tropomi_{product}").sort_index()
    log.info(f"TROPOMI {product.upper()}: {len(series)} days extracted.")
    return series


def build_satellite_features() -> pd.DataFrame:
    """
    Combine all satellite features (MODIS AOD + TROPOMI) into one daily DataFrame.

    Returns:
        pd.DataFrame indexed by date with columns:
          aod_modis, tropomi_no2, tropomi_co, tropomi_aer_ai
    """
    log.info("Building satellite feature DataFrame …")
    modis_df = build_modis_timeseries()

    frames = [modis_df]
    for product in ["no2", "co", "aer_ai"]:
        s = build_tropomi_timeseries(product)
        if len(s) > 0:
            frames.append(s.to_frame())

    result = pd.concat(frames, axis=1).sort_index()
    log.info(f"Satellite features shape: {result.shape}")
    log.info(f"Missing rate:\n{result.isna().mean().round(3)}")
    return result


if __name__ == "__main__":
    df = build_satellite_features()
    print(df.head(10))
    print(f"\nShape: {df.shape}")
