"""Fetch SRTM DEM -> delta_z + VIIRS-NTL for new valley candidates via GEE
getDownloadURL (synchronous, no Drive/Task latency). Builds the same NPZ format as
build_station_terrain.py so scripts/calibrate_terrain_solver.py can screen them.

Only the v2-regime-plausible candidates (magnitude near Kandy's 24.5 area mean) are
built — per user 2026-06-01: 4 new cities must pass PVAF v2.

Output: data/processed/pinn_inputs/{slug}_terrain_stations.npz (delta_z, svf,
lat_grid, lon_grid) + {slug}_viirs_ntl_stations.npz (NTL, lat_grid, lon_grid).
"""
from __future__ import annotations
import io
import sys
import time
from pathlib import Path

import ee
import numpy as np
import rasterio
import requests

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from build_source_city_terrain import compute_delta_z

PINN = REPO / "data" / "processed" / "pinn_inputs"

# v2-regime-plausible valley candidates (drop Lhasa too-clean, Yibin too-dirty,
# Chongqing too-large). bbox = (lat_min, lat_max, lon_min, lon_max) from stations.
CANDIDATES = {
    "panzhihua": (26.40, 26.69, 101.48, 101.84),
    "zunyi":     (27.49, 27.83, 106.75, 107.14),
    "guiyang":   (26.20, 26.73, 106.52, 106.91),
    "shiyan":    (32.30, 32.94, 110.63, 111.14),
    "changzhi":  (35.95, 36.45, 112.78, 113.34),
    "leshan":    (29.45, 29.70, 103.63, 103.87),
    "lanzhou":   (35.85, 36.21, 103.53, 104.24),
}


def _download_tif(image, region, scale):
    url = image.getDownloadURL({"scale": scale, "region": region,
                                "format": "GEO_TIFF", "crs": "EPSG:4326"})
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            return r.content
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def _grids_from_tif(content):
    with rasterio.open(io.BytesIO(content)) as src:
        arr = src.read(1).astype(np.float32)
        t = src.transform
        rows, cols = arr.shape
        lon = t.c + t.a * (np.arange(cols) + 0.5)
        lat = t.f + t.e * (np.arange(rows) + 0.5)   # e<0 -> descending
        lon_g, lat_g = np.meshgrid(lon, lat)
    return arr, lat_g.astype(np.float32), lon_g.astype(np.float32)


def process(slug, bbox):
    region = ee.Geometry.Rectangle([bbox[2], bbox[0], bbox[3], bbox[1]])
    # SRTM -> elevation -> delta_z (TPI)
    dem = ee.Image("USGS/SRTMGL1_003").select("elevation")
    elev, lat_g, lon_g = _grids_from_tif(_download_tif(dem, region, 100))
    elev = np.nan_to_num(elev, nan=float(np.nanmedian(elev)))
    dz = compute_delta_z(elev)
    np.savez(PINN / f"{slug}_terrain_stations.npz",
             delta_z=dz.astype(np.float32),
             delta_z_norm=(dz / max(dz.max(), 1.0)).astype(np.float32),
             svf=np.zeros_like(dz, np.float32),   # unused by the solver
             lat_grid=lat_g, lon_grid=lon_g, res_m=np.float32(100.0),
             bbox_lat_min=np.float32(bbox[0]), bbox_lat_max=np.float32(bbox[1]),
             bbox_lon_min=np.float32(bbox[2]), bbox_lon_max=np.float32(bbox[3]))
    # VIIRS NTL 2018-2023 mean
    ntl = (ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
           .filterDate("2018-01-01", "2024-01-01").select("avg_rad").mean().clip(region))
    NL, nlat_g, nlon_g = _grids_from_tif(_download_tif(ntl, region, 500))
    NL = np.nan_to_num(NL, nan=0.0)
    np.savez(PINN / f"{slug}_viirs_ntl_stations.npz",
             NTL=NL.astype(np.float32), NTL_log=np.log1p(np.clip(NL, 0, None)).astype(np.float32),
             lat_grid=nlat_g, lon_grid=nlon_g)
    print(f"  {slug:<10} dem{elev.shape} dz[{dz.min():.0f},{dz.max():.0f}]  "
          f"ntl{NL.shape}[{NL.min():.1f},{NL.max():.1f}]")


def main():
    ee.Initialize(project="kandypinn")
    print(f"Building terrain+NTL for {len(CANDIDATES)} valley candidates via GEE ...")
    for slug, bbox in CANDIDATES.items():
        try:
            process(slug, bbox)
        except Exception as e:
            print(f"  [ERR] {slug}: {repr(e)[:160]}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
