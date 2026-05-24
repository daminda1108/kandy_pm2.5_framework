"""
convcnp_loader.py — Stage C per-station data loaders for ConvCNP LOOCV.

Reads the canonical v11 per-station parquets produced by
`scripts/rebuild_perstation_extended.py --version v11` and the static
terrain NPZs in `data/processed/pinn_inputs/`.

Schemas
-------
Input parquet (`{city}_perstation_v11.parquet`):
    datetime_utc, location_id, station_id, station_name, provider, sensor_type,
    lat, lon, x_norm, y_norm, pm25_raw, pm25, calib_slope, calib_intercept,
    calib_r, n_samples, c_prior, c_prior_scaled, u10, v10, t2m, blh, blh_norm

Input NPZ (`{city}_terrain_tpi_svf_100m.npz`):
    lat_grid (lat, lon), lon_grid (lat, lon), delta_z (lat, lon) — local
    elevation above the valley floor in metres. SVF is in the NPZ but unused
    (gotcha #21: SVF is near-uniform across all cities).

Output (load_city return):
    feature_df  — MultiIndex (time, lat, lon); columns
                  pm25 (= pm25_obs − c_prior_scaled, the residual target)
                  blh_norm, c_prior_norm, sin_h, cos_h, sin_doy, cos_doy
    raw_df      — MultiIndex (time, lat, lon); columns
                  pm25_raw (original observed PM2.5)
                  c_prior_scaled_raw (used to add the prior back at inference)

The residual target convention is **additive** (`pm25 − c_prior_scaled`)
per the post-v7 pivot. v7/v8 used log-ratio and regressed on KTM.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import xarray as xr


# Default PM2.5 sanity cap. Drops obvious sensor errors (≥500 µg/m³ is rare
# even for KTM dust events) without truncating the legitimate top decile.
PM25_CAP_DEFAULT = 500.0


def load_terrain_da(npz_path: Path) -> xr.DataArray:
    """
    Load and normalise a delta_z terrain NPZ into an xarray DataArray
    (dims: lat, lon).

    The NPZ has lat_grid/lon_grid as 2D meshgrids. Lat is forced to be
    ascending (some NPZs were saved descending). delta_z is divided by its
    own max for [0, 1] normalisation — this matches the v11 kernel.

    Parameters
    ----------
    npz_path : Path
        Path to `{city}_terrain_tpi_svf_100m.npz`.

    Returns
    -------
    xarray.DataArray
        delta_z normalised to [0, 1], dims = ("lat", "lon"),
        coords = (lat_1d ascending, lon_1d ascending).
    """
    t      = np.load(npz_path, allow_pickle=True)
    lat_1d = t["lat_grid"][:, 0].astype(np.float64)
    lon_1d = t["lon_grid"][0, :].astype(np.float64)
    dz     = t["delta_z"].astype(np.float32)

    if lat_1d[0] > lat_1d[-1]:
        lat_1d = lat_1d[::-1]
        dz     = dz[::-1, :]

    dz_max = float(dz.max()) if dz.max() > 0 else 1.0
    dz     = dz / dz_max

    return xr.DataArray(
        dz,
        dims=["lat", "lon"],
        coords={"lat": lat_1d, "lon": lon_1d},
        name="delta_z",
    )


def load_city(parquet_path: Path,
              pm25_cap: float = PM25_CAP_DEFAULT,
              ) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load a v11 per-station hourly parquet, compute residual + harmonic features,
    and return (feature_df, raw_df) — both indexed by (time, lat, lon).

    Steps
    -----
    1. Parse `datetime_utc` → naïve `time` (drop tz info).
    2. Filter `0 < pm25 < pm25_cap` (drop NaN, negatives, obvious sensor errors).
    3. Add diurnal harmonics (sin/cos of hour-of-day / 24) and
       annual harmonics (sin/cos of day-of-year / 365).
    4. Subtract `c_prior_scaled` from `pm25` to form the residual target.
       Save the original observed PM2.5 + the c_prior_scaled column under
       `raw_df` so they can be added back at inference.
    5. Fill any NaN in `blh_norm` with 0.5 (a reasonable mid-range value;
       no NaN should remain post-v11 rebuild but defence-in-depth).

    Parameters
    ----------
    parquet_path : Path
        Path to `{city}_perstation_v11.parquet`.
    pm25_cap : float
        Drop rows where pm25 ≥ pm25_cap or pm25 ≤ 0. Default 500 µg/m³.

    Returns
    -------
    (feature_df, raw_df) : Tuple[pd.DataFrame, pd.DataFrame]
        feature_df: MultiIndex (time, lat, lon); float32 columns
                    pm25 (residual), blh_norm, c_prior_norm, sin_h, cos_h,
                    sin_doy, cos_doy.
        raw_df:     MultiIndex (time, lat, lon); float32 columns
                    pm25_raw, c_prior_scaled_raw.
    """
    df = pd.read_parquet(parquet_path)
    df["time"] = pd.to_datetime(df["datetime_utc"], utc=True).dt.tz_localize(None)
    df = df[(df["pm25"] > 0) & (df["pm25"] < pm25_cap) & df["pm25"].notna()].copy()

    df["sin_h"]   = np.sin(2 * np.pi * df["time"].dt.hour      / 24 ).astype(np.float32)
    df["cos_h"]   = np.cos(2 * np.pi * df["time"].dt.hour      / 24 ).astype(np.float32)
    df["sin_doy"] = np.sin(2 * np.pi * df["time"].dt.dayofyear / 365).astype(np.float32)
    df["cos_doy"] = np.cos(2 * np.pi * df["time"].dt.dayofyear / 365).astype(np.float32)

    c_prior_scaled = df["c_prior_scaled"].values.astype(np.float64)
    df["c_prior_norm"]       = (c_prior_scaled / 100.0).astype(np.float32)
    df["c_prior_scaled_raw"] = c_prior_scaled.astype(np.float32)

    pm25_raw     = df["pm25"].values.astype(np.float64)
    df["pm25_raw"] = pm25_raw.astype(np.float32)
    df["pm25"]     = (pm25_raw - c_prior_scaled).astype(np.float32)

    df["blh_norm"] = df["blh_norm"].fillna(0.5).astype(np.float32)

    df = df.set_index(["time", "lat", "lon"]).sort_index()
    feature_cols = ["pm25", "blh_norm", "c_prior_norm",
                    "sin_h", "cos_h", "sin_doy", "cos_doy"]
    raw_cols     = ["pm25_raw", "c_prior_scaled_raw"]
    return df[feature_cols].astype(np.float32), df[raw_cols].astype(np.float32)
