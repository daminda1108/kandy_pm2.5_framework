"""
city_config.py — CityConfig dataclass + registry for multi-city meta-learning.

Usage:
    from src.stage3_pinn.data.city_config import CITY_REGISTRY, get_city

    cfg = get_city("medellin")
    print(cfg.bbox, cfg.station_path)
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Repository root → kandy_pm25/
_REPO = Path(__file__).parents[3]   # src/stage3_pinn/data/city_config.py → 3 up = kandy_pm25/


@dataclass
class CityConfig:
    """All city-specific paths and normalisation constants."""

    name: str
    role: str                   # "source" | "target"
    bbox: dict                  # full domain bbox (satellite / met)
    pinn_bbox: dict             # PINN training bbox

    elev_path: Path             # *_elev_grid_100m.npz
    terrain_path: Path          # *_terrain_tpi_svf_100m.npz
    road_path: Path             # *_road_kernel_100m.npz

    station_path: Optional[Path]   # parquet with hourly station PM2.5. None for target.
    tier_c_path: Optional[Path]    # merged hourly met+GEOS parquet. None until built.

    # Normalisation (computed from training data)
    pm25_mean: float = 0.0
    pm25_std:  float = 1.0

    # Station schema: column names in station_path parquet
    station_datetime_col: str = "datetime_utc"
    station_lat_col:      str = "lat"
    station_lon_col:      str = "lon"
    station_pm25_col:     str = "pm25"

    # Met schema: column names in tier_c_path parquet
    tier_c_datetime_col: str = "datetime_utc"
    tier_c_geos_col:     str = "geos_pm25"
    tier_c_blh_col:      str = "blh_m"
    tier_c_u10_col:      str = "u10"
    tier_c_v10_col:      str = "v10"

    # Grid size
    grid_nx: int = 150
    grid_ny: int = 150

    @property
    def lat_min(self) -> float:
        return self.pinn_bbox["lat_min"]

    @property
    def lat_max(self) -> float:
        return self.pinn_bbox["lat_max"]

    @property
    def lon_min(self) -> float:
        return self.pinn_bbox["lon_min"]

    @property
    def lon_max(self) -> float:
        return self.pinn_bbox["lon_max"]

    def has_stations(self) -> bool:
        return self.station_path is not None and self.station_path.exists()

    def has_tier_c(self) -> bool:
        return self.tier_c_path is not None and self.tier_c_path.exists()


# ── Data paths ────────────────────────────────────────────────────────────────
_PINN_INPUTS = _REPO / "data/processed/pinn_inputs"
_STAGE2      = _REPO / "data/processed/stage2"
_TIER_C_KTM  = _REPO / "data/external/kathmandu"
_TIER_C_KAN  = _REPO / "data/processed/tier_c"


CITY_REGISTRY: dict[str, CityConfig] = {

    "medellin": CityConfig(
        name="medellin",
        role="source",
        bbox={
            "lat_min": 6.10, "lat_max": 6.40,
            "lon_min": -75.70, "lon_max": -75.45,
        },
        pinn_bbox={
            "lat_min": 6.1635, "lat_max": 6.2986,
            "lon_min": -75.6426, "lon_max": -75.5066,
        },
        elev_path=_PINN_INPUTS / "medellin_elev_grid_100m.npz",
        terrain_path=_PINN_INPUTS / "medellin_terrain_tpi_svf_100m.npz",
        road_path=_PINN_INPUTS / "medellin_road_kernel_100m.npz",
        station_path=_STAGE2 / "medellin_stage2_perstation.parquet",
        tier_c_path=None,    # No separate tier_c yet; uses station parquet BLH
        pm25_mean=20.7,
        pm25_std=12.5,
        station_pm25_col="pm25",
        tier_c_blh_col="blh",
        tier_c_u10_col="u10",
        tier_c_v10_col="v10",
    ),

    "chiangmai": CityConfig(
        name="chiangmai",
        role="source",
        bbox={
            "lat_min": 18.60, "lat_max": 19.00,
            "lon_min": 98.80, "lon_max": 99.20,
        },
        pinn_bbox={
            "lat_min": 18.7446, "lat_max": 18.8797,
            "lon_min": 98.8808, "lon_max": 99.0236,
        },
        elev_path=_PINN_INPUTS / "chiangmai_elev_grid_100m.npz",
        terrain_path=_PINN_INPUTS / "chiangmai_terrain_tpi_svf_100m.npz",
        road_path=_PINN_INPUTS / "chiangmai_road_kernel_100m.npz",
        # chiangmai_stage3_perstation has station PM2.5 + ERA5 BLH/wind merged
        station_path=_STAGE2 / "chiangmai_stage3_perstation.parquet",
        tier_c_path=None,   # GEOS-CF pending GEE exports (ChiangMaiTierC_Data)
        pm25_mean=26.8,
        pm25_std=26.8,
        station_datetime_col="datetime_utc",
        station_pm25_col="pm25",
        tier_c_blh_col="blh",
        tier_c_u10_col="u10",
        tier_c_v10_col="v10",
    ),

    "kathmandu": CityConfig(
        name="kathmandu",
        role="source",
        bbox={
            "lat_min": 27.55, "lat_max": 27.85,
            "lon_min": 85.20, "lon_max": 85.45,
        },
        pinn_bbox={
            "lat_min": 27.620, "lat_max": 27.800,
            "lon_min": 85.220, "lon_max": 85.420,
        },
        elev_path=_PINN_INPUTS / "kathmandu_elev_grid_100m.npz",   # pending DEM download
        terrain_path=_PINN_INPUTS / "kathmandu_terrain_tpi_svf_100m.npz",
        road_path=_PINN_INPUTS / "kathmandu_road_kernel_100m.npz",
        station_path=_STAGE2 / "kathmandu_stage3_perstation.parquet",
        tier_c_path=None,
        pm25_mean=61.0,
        pm25_std=42.0,
        station_datetime_col="datetime_utc",
        station_pm25_col="pm25",
        tier_c_blh_col="blh",
        tier_c_u10_col="u10",
        tier_c_v10_col="v10",
        grid_nx=200,    # 20km at 100m
        grid_ny=200,
    ),

    "kandy": CityConfig(
        name="kandy",
        role="target",
        bbox={
            "lat_min": 7.00, "lat_max": 7.60,
            "lon_min": 80.40, "lon_max": 80.90,
        },
        pinn_bbox={
            "lat_min": 7.2230, "lat_max": 7.3582,
            "lon_min": 80.5660, "lon_max": 80.7014,
        },
        elev_path=_PINN_INPUTS / "kandy_elev_grid_100m.npz",
        terrain_path=_PINN_INPUTS / "kandy_terrain_tpi_svf_100m.npz",
        road_path=_PINN_INPUTS / "kandy_road_kernel_100m.npz",
        station_path=None,   # no stations in domain
        tier_c_path=_TIER_C_KAN / "kandy_tier_c_merged.parquet",
        pm25_mean=21.9,
        pm25_std=10.0,
        tier_c_geos_col="geos_pm25",
        tier_c_blh_col="blh_m",
        tier_c_u10_col="u10",
        tier_c_v10_col="v10",
    ),
}


def get_city(name: str) -> CityConfig:
    if name not in CITY_REGISTRY:
        raise KeyError(f"Unknown city '{name}'. Available: {list(CITY_REGISTRY)}")
    return CITY_REGISTRY[name]


SOURCE_CITIES = [cfg for cfg in CITY_REGISTRY.values() if cfg.role == "source"]
