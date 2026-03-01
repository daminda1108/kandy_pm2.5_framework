"""
meteo_features.py — Extract and engineer meteorological features from ERA5 data.

Reads downloaded ERA5 NetCDF files, extracts hourly fields at Kandy,
computes derived meteorological variables, and returns a clean DataFrame.
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.interpolate import RegularGridInterpolator

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    KANDY_BBOX, KANDY_CENTER, ERA5_RAW_DIR,
    DATA_START_YEAR, DATA_END_YEAR, LOG_FORMAT, LOG_DATEFMT
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("meteo_features")


def _nearest_point(ds: xr.Dataset, lat: float, lon: float) -> xr.Dataset:
    """Select nearest grid cell to Kandy centre."""
    return ds.sel(
        latitude=lat, longitude=lon, method="nearest"
    )


def load_era5_single(year: int) -> xr.Dataset:
    fpath = ERA5_RAW_DIR / f"era5_single_{year}.nc"
    if not fpath.exists():
        raise FileNotFoundError(f"ERA5 single levels not found: {fpath}\nRun download_era5.py first.")
    log.info(f"Loading ERA5 single levels: {fpath.name}")
    return xr.open_dataset(fpath)


def load_era5_pressure(year: int) -> xr.Dataset:
    fpath = ERA5_RAW_DIR / f"era5_pressure_{year}.nc"
    if not fpath.exists():
        return None  # Pressure levels are optional (TII only)
    log.info(f"Loading ERA5 pressure levels: {fpath.name}")
    return xr.open_dataset(fpath)


def load_era5_land(year: int) -> xr.Dataset:
    fpath = ERA5_RAW_DIR / f"era5_land_{year}.nc"
    if not fpath.exists():
        return None  # ERA5-Land optional
    log.info(f"Loading ERA5-Land: {fpath.name}")
    return xr.open_dataset(fpath)


def compute_relative_humidity(t2m_k: np.ndarray, d2m_k: np.ndarray) -> np.ndarray:
    """
    Compute RH (%) from 2m temperature and dewpoint temperature.
    Uses the Magnus formula approximation.
    """
    t_c  = t2m_k - 273.15
    td_c = d2m_k - 273.15
    rh = 100 * np.exp((17.625 * td_c) / (243.04 + td_c)) / \
                np.exp((17.625 * t_c)  / (243.04 + t_c))
    return np.clip(rh, 0, 100)


def compute_wind_speed_direction(u10: np.ndarray, v10: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Wind speed (m/s) and direction (degrees from North, meteorological convention)."""
    speed = np.sqrt(u10 ** 2 + v10 ** 2)
    direction = (270 - np.degrees(np.arctan2(v10, u10))) % 360
    return speed, direction


def sin_cos_encode(values: np.ndarray, period: float) -> tuple[np.ndarray, np.ndarray]:
    """Cyclical encoding: sin and cos of a periodic variable."""
    angle = 2 * np.pi * values / period
    return np.sin(angle), np.cos(angle)


def extract_meteo_features(years: list[int] | None = None) -> pd.DataFrame:
    """
    Extract and engineer ERA5 meteorological features for Kandy centre.

    Args:
        years: List of years to process. Defaults to DATA_START_YEAR–DATA_END_YEAR.

    Returns:
        pd.DataFrame with hourly meteorological features indexed by time.
    """
    if years is None:
        years = list(range(DATA_START_YEAR, DATA_END_YEAR + 1))

    all_frames: list[pd.DataFrame] = []
    lat, lon = KANDY_CENTER["lat"], KANDY_CENTER["lon"]

    for year in years:
        try:
            ds_sl  = load_era5_single(year)
            ds_pl  = load_era5_pressure(year)
            ds_lnd = load_era5_land(year)
        except FileNotFoundError as e:
            log.warning(str(e))
            continue

        # ── Single-level variables ────────────────────────────────────────
        sl = _nearest_point(ds_sl, lat, lon)
        time_index = pd.DatetimeIndex(sl["time"].values)

        u10  = sl["u10"].values.flatten()
        v10  = sl["v10"].values.flatten()
        t2m  = sl["t2m"].values.flatten()  # K
        d2m  = sl["d2m"].values.flatten()  # K
        blh  = sl["blh"].values.flatten()
        sp   = sl["sp"].values.flatten()   # Pa
        tp   = sl["tp"].values.flatten()   # m/hr (accumulated, may need diff)
        ssr  = sl["ssrd"].values.flatten() # J/m² (accumulated)

        wind_speed, wind_dir = compute_wind_speed_direction(u10, v10)
        rh = compute_relative_humidity(t2m, d2m)

        # De-accumulate ERA5 accumulated fields (convert to hourly)
        # ERA5 accumulates from 00:00 UTC; we take the hourly difference
        tp_hourly  = np.maximum(0.0, np.diff(tp,  prepend=tp[0]))
        ssr_hourly = np.maximum(0.0, np.diff(ssr, prepend=ssr[0]))

        hour_of_day = time_index.hour.values
        day_of_week = time_index.dayofweek.values  # Mon=0, Sun=6
        month       = time_index.month.values

        # Cyclical time encodings
        hour_sin,  hour_cos  = sin_cos_encode(hour_of_day, 24)
        dow_sin,   dow_cos   = sin_cos_encode(day_of_week, 7)
        month_sin, month_cos = sin_cos_encode(month, 12)

        # Wind direction cyclical encoding
        wdir_rad = np.radians(wind_dir)
        wdir_sin, wdir_cos = np.sin(wdir_rad), np.cos(wdir_rad)

        frame: dict[str, np.ndarray] = {
            # Core meteorological -> ML features
            "u10":       u10,
            "v10":       v10,
            "wind_speed": wind_speed,
            "wind_dir":  wind_dir,
            "wdir_sin":  wdir_sin,
            "wdir_cos":  wdir_cos,
            "t2m":       t2m,
            "d2m":       d2m,
            "rh":        rh,
            "blh":       blh,
            "sp":        sp / 100.0,  # Pa → hPa
            "tp":        tp_hourly,
            "ssr":       ssr_hourly,
            # Time features
            "hour":      hour_of_day,
            "hour_sin":  hour_sin,
            "hour_cos":  hour_cos,
            "dow":       day_of_week,
            "dow_sin":   dow_sin,
            "dow_cos":   dow_cos,
            "month":     month,
            "month_sin": month_sin,
            "month_cos": month_cos,
        }

        # ── Pressure-level variables (925 hPa) for TII ───────────────────
        if ds_pl is not None:
            pl = _nearest_point(ds_pl, lat, lon)
            try:
                t925 = pl["t"].sel(pressure_level=925, method="nearest").values.flatten()
                frame["t925"] = t925
            except Exception as e:
                log.warning(f"Could not extract t925: {e}")

        # ── ERA5-Land (skin temperature for KFP) ─────────────────────────
        if ds_lnd is not None:
            lnd = _nearest_point(ds_lnd, lat, lon)
            try:
                frame["skin_temp"] = lnd["skt"].values.flatten()
            except Exception as e:
                log.warning(f"Could not extract skin_temp: {e}")

        df_year = pd.DataFrame(frame, index=time_index)
        df_year.index.name = "time"
        all_frames.append(df_year)

        ds_sl.close()
        if ds_pl is not None:
            ds_pl.close()
        if ds_lnd is not None:
            ds_lnd.close()

        log.info(f"Year {year}: {len(df_year)} hourly records extracted.")

    if not all_frames:
        raise RuntimeError("No ERA5 data could be loaded. Run download_era5.py first.")

    result = pd.concat(all_frames, axis=0).sort_index()
    result = result[~result.index.duplicated(keep="first")]  # Remove leap-year duplicates
    log.info(f"Total ERA5 meteorological records: {len(result)}")
    return result


def load_era5_t925(pl_dir: Path | None = None) -> pd.Series:
    """
    Load 925 hPa temperature from CDS pressure-level downloads and return a daily mean Series.

    Reads kandy_t925_YYYY.nc files from data/raw/era5/pressure_levels/.
    Returns a pd.Series named 't925' with a daily DatetimeIndex (temperatures in Kelvin).
    Returns an empty Series if no files are found (graceful — caller left-joins).

    Usage:
        from src.stage1_satml.features.meteo_features import load_era5_t925
        t925 = load_era5_t925()
        print(t925['2023-01-01':'2023-01-07'])
    """
    pl_dir = pl_dir or (ERA5_RAW_DIR / "pressure_levels")
    nc_files = sorted(pl_dir.glob("kandy_t925_*.nc"))

    if not nc_files:
        log.warning(f"No kandy_t925_*.nc files found in {pl_dir}. Download with download_era5_t925().")
        return pd.Series(dtype=float, name="t925")

    lat, lon = KANDY_CENTER["lat"], KANDY_CENTER["lon"]
    daily_frames: list[pd.Series] = []

    for fpath in nc_files:
        log.info(f"Loading t925: {fpath.name}")
        ds = xr.open_dataset(fpath)
        pt = _nearest_point(ds, lat, lon)

        # CDS ERA5 may use 'valid_time' (new API) or 'time' (legacy)
        time_coord = "valid_time" if "valid_time" in pt.coords else "time"

        # Extract temperature at 925 hPa (dimension name: 'pressure_level')
        t_var = pt["t"].sel(pressure_level=925, method="nearest")

        hourly = pd.Series(
            t_var.values.flatten(),
            index=pd.DatetimeIndex(pt[time_coord].values),
            name="t925",
        )
        daily_frames.append(hourly.resample("D").mean())
        ds.close()

    if not daily_frames:
        return pd.Series(dtype=float, name="t925")

    result = pd.concat(daily_frames).sort_index()
    result = result[~result.index.duplicated(keep="first")]
    result.index = result.index.normalize()  # Strip time component → pure dates
    log.info(f"t925 loaded: {len(result)} daily records, range {result.index[0].date()} – {result.index[-1].date()}")
    return result


if __name__ == "__main__":
    df = extract_meteo_features([2022])
    print(df.head())
    print(df.dtypes)
    print(f"\nShape: {df.shape}")
