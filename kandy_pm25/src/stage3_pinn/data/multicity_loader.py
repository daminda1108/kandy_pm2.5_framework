"""
multicity_loader.py — Multi-city DataLoader for SharedTerrainAnsatz training.

Each item in the dataset is one station-hour observation containing:
    delta_z     : float  — elevation above valley floor at station [m]
    wind_speed  : float  — |wind| at this timestep [m/s]
    blh         : float  — boundary layer height [m]
    lat_norm    : float  — station lat normalised to [-1, 1] within city PINN bbox
    lon_norm    : float  — station lon normalised to [-1, 1] within city PINN bbox
    t_norm      : float  — hour-of-day / 24 ∈ [0, 1]
    sin_h, cos_h: float  — diurnal harmonics
    pm25_obs    : float  — observed PM2.5 [µg/m³]
    pm25_anom   : float  — per-city anomaly (pm25_obs − city_mean) / city_std
    c_prior     : float  — temporal background = hourly domain-mean across stations
    city_id     : int    — city index (0=medellin, 1=chiangmai, 2=kathmandu)

C_prior(t) is computed as the hourly mean across all active stations at time t.
This is a valid proxy for the "background" concentration at each timestep.
When GEOS-CF becomes available for source cities it can replace this.

Usage:
    from src.stage3_pinn.data.multicity_loader import build_multicity_dataset
    dataset = build_multicity_dataset(["medellin", "chiangmai"])
    loader  = DataLoader(dataset, batch_size=512, shuffle=True)
"""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader

from .city_config import CityConfig, get_city, CITY_REGISTRY

log = logging.getLogger(__name__)


# ── Parquet schema unification ─────────────────────────────────────────────────

def _load_station_parquet(cfg: CityConfig) -> pd.DataFrame:
    """
    Load per-station hourly parquet and return unified schema:
    datetime_utc, station_name, lat, lon, pm25, blh, u10, v10
    """
    if cfg.station_path is None or not cfg.station_path.exists():
        raise FileNotFoundError(f"Station data not found for {cfg.name}: {cfg.station_path}")

    df = pd.read_parquet(cfg.station_path)
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True)

    # Rename to canonical columns
    rename = {}
    if cfg.station_pm25_col != "pm25":
        rename[cfg.station_pm25_col] = "pm25"
    if cfg.station_lat_col != "lat":
        rename[cfg.station_lat_col] = "lat"
    if cfg.station_lon_col != "lon":
        rename[cfg.station_lon_col] = "lon"
    if rename:
        df = df.rename(columns=rename)

    # Ensure blh/u10/v10 columns exist
    for col in ["blh", "u10", "v10"]:
        src = {"blh": cfg.tier_c_blh_col, "u10": cfg.tier_c_u10_col, "v10": cfg.tier_c_v10_col}[col]
        if col not in df.columns and src in df.columns:
            df = df.rename(columns={src: col})
        elif col not in df.columns:
            raise KeyError(f"City {cfg.name}: missing column '{col}' (tried '{src}')")

    # Keep only needed columns
    keep = ["datetime_utc", "station_name", "lat", "lon", "pm25", "blh", "u10", "v10"]
    if "station_id" in df.columns:
        keep = ["station_id"] + keep
    df = df[[c for c in keep if c in df.columns]].copy()

    # Basic QC
    df = df[(df["pm25"] > 0) & (df["pm25"] <= 500)].copy()
    df = df.dropna(subset=["pm25", "blh", "u10", "v10"])

    log.info("  %s: loaded %d station-hours from %d stations",
             cfg.name, len(df), df["station_name"].nunique())
    return df


def _interpolate_delta_z(cfg: CityConfig, df: pd.DataFrame) -> np.ndarray:
    """
    Interpolate delta_z from the terrain NPZ at station lat/lon coordinates.
    Uses nearest-grid-point lookup (100m resolution → sub-100m error acceptable).
    """
    terrain = np.load(cfg.terrain_path)
    delta_z_grid = terrain["delta_z"]           # (ny, nx)
    lat_grid = terrain["lat_grid"]               # (ny, nx)
    lon_grid = terrain["lon_grid"]               # (ny, nx)

    lat_min = lat_grid.min()
    lat_max = lat_grid.max()
    lon_min = lon_grid.min()
    lon_max = lon_grid.max()
    ny, nx = delta_z_grid.shape

    # Clip station coords to grid (stations on the rim may be slightly outside)
    lats = np.clip(df["lat"].values, lat_min, lat_max)
    lons = np.clip(df["lon"].values, lon_min, lon_max)

    row_idx = np.round((lats - lat_min) / (lat_max - lat_min) * (ny - 1)).astype(int)
    col_idx = np.round((lons - lon_min) / (lon_max - lon_min) * (nx - 1)).astype(int)
    row_idx = np.clip(row_idx, 0, ny - 1)
    col_idx = np.clip(col_idx, 0, nx - 1)

    return delta_z_grid[row_idx, col_idx].astype(np.float32)


class MulticityStationDataset(Dataset):
    """
    PyTorch Dataset yielding per-station-hour feature vectors.

    Each item is a dict of float32 tensors (shape () — scalar):
        delta_z, wind_speed, blh, lat_norm, lon_norm,
        t_norm, sin_h, cos_h,
        pm25_obs, pm25_anom, c_prior,
        city_id (int)
    """

    def __init__(self, records: np.ndarray, city_id: int):
        """
        records: (N, 10) float32 array —
            [delta_z, wind_speed, blh, lat_norm, lon_norm,
             t_norm, sin_h, cos_h, pm25_obs, pm25_anom, c_prior]
        city_id: int city index
        """
        self.records = torch.from_numpy(records)
        self.city_id = city_id

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> dict:
        r = self.records[idx]
        return {
            "delta_z":    r[0],
            "wind_speed": r[1],
            "blh":        r[2],
            "lat_norm":   r[3],
            "lon_norm":   r[4],
            "t_norm":     r[5],
            "sin_h":      r[6],
            "cos_h":      r[7],
            "pm25_obs":   r[8],
            "pm25_anom":  r[9],
            "c_prior":    r[10],
            "city_id":    torch.tensor(self.city_id, dtype=torch.long),
        }


def _build_city_records(cfg: CityConfig, city_id: int) -> np.ndarray:
    """Build (N, 11) float32 array for one city."""

    df = _load_station_parquet(cfg)

    # ── Spatial normalisation to [-1, 1] ─────────────────────────────────────
    lat_norm = 2.0 * (df["lat"].values - cfg.lat_min) / (cfg.lat_max - cfg.lat_min) - 1.0
    lon_norm = 2.0 * (df["lon"].values - cfg.lon_min) / (cfg.lon_max - cfg.lon_min) - 1.0

    # ── Temporal features ─────────────────────────────────────────────────────
    hours = df["datetime_utc"].dt.hour.values.astype(np.float32)
    t_norm = hours / 24.0
    sin_h = np.sin(2 * np.pi * hours / 24.0).astype(np.float32)
    cos_h = np.cos(2 * np.pi * hours / 24.0).astype(np.float32)

    # ── Met features ──────────────────────────────────────────────────────────
    wind_speed = np.sqrt(df["u10"].values ** 2 + df["v10"].values ** 2).astype(np.float32)
    blh = df["blh"].values.astype(np.float32)

    # ── Terrain: delta_z at station location ──────────────────────────────────
    delta_z = _interpolate_delta_z(cfg, df)

    # ── PM2.5 features ────────────────────────────────────────────────────────
    pm25_obs = df["pm25"].values.astype(np.float32)

    # Per-city normalised anomaly (removes city mean, scales by city std)
    pm25_anom = (pm25_obs - cfg.pm25_mean) / max(cfg.pm25_std, 1.0)

    # C_prior(t) = hourly domain-mean observed PM2.5 across all active stations
    df["datetime_floor"] = df["datetime_utc"].dt.floor("h")
    hourly_mean = df.groupby("datetime_floor")["pm25"].mean()
    df["c_prior"] = df["datetime_floor"].map(hourly_mean)
    c_prior = df["c_prior"].values.astype(np.float32)

    log.info("  %s city_id=%d: delta_z %.1f-%.1f m | wind %.2f m/s | BLH %.0f m | "
             "PM2.5 %.1f±%.1f",
             cfg.name, city_id, delta_z.min(), delta_z.max(),
             wind_speed.mean(), blh.mean(), pm25_obs.mean(), pm25_obs.std())

    return np.column_stack([
        delta_z, wind_speed, blh,
        lat_norm.astype(np.float32), lon_norm.astype(np.float32),
        t_norm.astype(np.float32), sin_h, cos_h,
        pm25_obs, pm25_anom.astype(np.float32), c_prior,
    ]).astype(np.float32)


def build_multicity_dataset(
    city_names: List[str],
) -> "ConcatCityDataset":
    """
    Build a concatenated dataset from multiple source cities.

    Returns a ConcatCityDataset that samples city-balanced mini-batches.
    """
    datasets = []
    for city_id, name in enumerate(city_names):
        cfg = get_city(name)
        log.info("Loading city: %s (id=%d)", name, city_id)
        records = _build_city_records(cfg, city_id)
        ds = MulticityStationDataset(records, city_id)
        log.info("  %s: %d samples", name, len(ds))
        datasets.append(ds)

    return ConcatCityDataset(datasets, city_names)


class ConcatCityDataset(Dataset):
    """Wraps per-city datasets; exposes city_datasets for balanced sampling."""

    def __init__(self, datasets: list, city_names: list):
        self.city_datasets = datasets
        self.city_names = city_names
        # Flat offset index for __getitem__
        self._offsets = [0]
        for ds in datasets:
            self._offsets.append(self._offsets[-1] + len(ds))

    def __len__(self) -> int:
        return self._offsets[-1]

    def __getitem__(self, idx: int) -> dict:
        for city_id, ds in enumerate(self.city_datasets):
            start = self._offsets[city_id]
            end = self._offsets[city_id + 1]
            if start <= idx < end:
                return ds[idx - start]
        raise IndexError(f"Index {idx} out of range")

    def summary(self) -> str:
        lines = ["Multi-city dataset:"]
        for name, ds in zip(self.city_names, self.city_datasets):
            lines.append(f"  {name}: {len(ds):,} samples")
        lines.append(f"  Total: {len(self):,} samples")
        return "\n".join(lines)
