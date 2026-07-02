"""
build_station_terrain.py — Build wide-footprint terrain (delta_z + SVF) NPZ
for each source city, aligned to the station-coverage bbox (same as
`{city}_road_kernel_stations_100m.npz`).

Why: the original `{city}_terrain_tpi_svf_100m.npz` is sized to the 15x15 km
Stage 2 PINN bbox; many source-city stations fall outside that footprint and
receive zero local terrain context in the ConvCNP convolutional encoder.

Output: data/processed/pinn_inputs/{city}_terrain_stations.npz
        keys: delta_z, delta_z_norm, svf, lat_grid, lon_grid, res_m,
              bbox_lat_min, bbox_lat_max, bbox_lon_min, bbox_lon_max

Reuses compute_delta_z + compute_svf from build_source_city_terrain.py
(same multi-scale TPI weights + 16-direction horizon scan).

Usage:
    python scripts/build_station_terrain.py                  # all 3 source cities
    python scripts/build_station_terrain.py --city kathmandu
    python scripts/build_station_terrain.py --force
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import rasterio
import rasterio.warp as rwarp
from rasterio.transform import from_bounds

sys.path.insert(0, str(Path(__file__).parent))
from build_source_city_terrain import (
    compute_delta_z, compute_svf, RES_M, SVF_N_DIRS, SVF_MAX_DIST_M,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger("station_terrain")

PINN_INPUT_DIR = Path(__file__).parents[1] / "data/processed/pinn_inputs"
EXT_DIR        = Path(__file__).parents[1] / "data/external"

# DEM source TIFs (already on disk)
DEM_PATHS = {
    "medellin":   EXT_DIR / "medellin"   / "dem" / "medellin_dem.tif",
    "chiangmai":  EXT_DIR / "chiangmai"  / "dem" / "chiangmai_dem.tif",
    "kathmandu":  EXT_DIR / "kathmandu"  / "dem" / "kathmandu_srtm_30m.tif",
    # PVAF v15 source set (amendment 10i)
    "xichang":    EXT_DIR / "xichang"    / "dem" / "xichang_srtm_dem.tif",
    "bazhou":     EXT_DIR / "bazhou"     / "dem" / "bazhou_srtm_dem.tif",
    "jincheng":   EXT_DIR / "jincheng"   / "dem" / "jincheng_srtm_dem.tif",
    "baoji":      EXT_DIR / "baoji"      / "dem" / "baoji_srtm_dem.tif",
    "yichang":    EXT_DIR / "yichang"    / "dem" / "yichang_srtm_dem.tif",
    "taian":      EXT_DIR / "taian"      / "dem" / "taian_srtm_dem.tif",
    "chandigarh": EXT_DIR / "chandigarh" / "dem" / "chandigarh_srtm_dem.tif",
}

M_PER_DEG_LAT = 111_200.0


def load_station_bbox(city: str) -> dict:
    """Pull station-footprint bbox from the wide road kernel NPZ."""
    npz = PINN_INPUT_DIR / f"{city}_road_kernel_stations_100m.npz"
    d = np.load(str(npz))
    return {
        "lat_min": float(d["bbox_lat_min"]),
        "lat_max": float(d["bbox_lat_max"]),
        "lon_min": float(d["bbox_lon_min"]),
        "lon_max": float(d["bbox_lon_max"]),
    }


def build_grid(bbox: dict, res_m: float = RES_M):
    """Build a regular lat/lon grid at res_m metres for the station bbox."""
    lat_c = 0.5 * (bbox["lat_min"] + bbox["lat_max"])
    m_per_deg_lon = 111_200.0 * np.cos(np.radians(lat_c))
    dlat = res_m / M_PER_DEG_LAT
    dlon = res_m / m_per_deg_lon

    lats = np.arange(bbox["lat_min"], bbox["lat_max"] + dlat / 2, dlat)
    lons = np.arange(bbox["lon_min"], bbox["lon_max"] + dlon / 2, dlon)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    return lat_grid.astype(np.float32), lon_grid.astype(np.float32)


def resample_dem(dem_tif: Path, lat_grid: np.ndarray, lon_grid: np.ndarray) -> np.ndarray:
    ny, nx = lat_grid.shape
    transform = from_bounds(
        west=float(lon_grid[0, 0]),  south=float(lat_grid[0, 0]),
        east=float(lon_grid[-1, -1]), north=float(lat_grid[-1, -1]),
        width=nx, height=ny,
    )
    elev = np.zeros((ny, nx), dtype=np.float32)
    with rasterio.open(str(dem_tif)) as src:
        rwarp.reproject(
            source=rasterio.band(src, 1),
            destination=elev,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs="EPSG:4326",
            resampling=rwarp.Resampling.bilinear,
        )
    # Fill NaN / no-data
    elev = np.where(elev < 0, np.nan, elev)
    if np.isnan(elev).any():
        col_means = np.nanmean(elev, axis=0)
        for j in range(nx):
            mask = np.isnan(elev[:, j])
            elev[mask, j] = col_means[j]
    return elev


def process(city: str, force: bool = False) -> None:
    out_npz = PINN_INPUT_DIR / f"{city}_terrain_stations.npz"
    if out_npz.exists() and not force:
        log.info(f"Already exists: {out_npz.name}  (--force to rebuild)")
        return

    dem_tif = DEM_PATHS[city]
    if not dem_tif.exists():
        log.error(f"DEM missing: {dem_tif}")
        return

    bbox = load_station_bbox(city)
    lat_grid, lon_grid = build_grid(bbox)
    ny, nx = lat_grid.shape
    log.info(
        f"{city.upper()}: bbox lat[{bbox['lat_min']:.3f}, {bbox['lat_max']:.3f}] "
        f"lon[{bbox['lon_min']:.3f}, {bbox['lon_max']:.3f}], grid {ny}x{nx} @ {RES_M:.0f} m"
    )

    log.info("Resampling DEM ...")
    elev = resample_dem(dem_tif, lat_grid, lon_grid)
    log.info(f"  elev range: {elev.min():.0f}–{elev.max():.0f} m")

    log.info("Computing delta_z ...")
    delta_z = compute_delta_z(elev)
    delta_z_norm = (delta_z / max(delta_z.max(), 1.0)).astype(np.float32)

    log.info(f"Computing SVF ({SVF_N_DIRS} dirs, max {SVF_MAX_DIST_M} m) ...")
    svf = compute_svf(elev)

    np.savez(
        str(out_npz),
        delta_z=delta_z.astype(np.float32),
        delta_z_norm=delta_z_norm,
        svf=svf,
        lat_grid=lat_grid,
        lon_grid=lon_grid,
        res_m=np.float32(RES_M),
        bbox_lat_min=np.float32(bbox["lat_min"]),
        bbox_lat_max=np.float32(bbox["lat_max"]),
        bbox_lon_min=np.float32(bbox["lon_min"]),
        bbox_lon_max=np.float32(bbox["lon_max"]),
    )
    log.info(f"Saved: {out_npz}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", choices=sorted(DEM_PATHS))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    cities = [args.city] if args.city else list(DEM_PATHS)
    for c in cities:
        process(c, force=args.force)


if __name__ == "__main__":
    main()
