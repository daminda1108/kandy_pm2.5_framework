"""build_xichang_core_terrain.py — city-centred terrain raster for Xichang, on the
SAME box as the WindNinja library (urban core central; Kandy-analogous ~16 km box),
so the decomposition field grid, traffic surface and WindNinja winds all align and
the maps focus on the Liangshan/Xichang urban core (not the off-centre station box).

Out: data/processed/pinn_inputs/xichang_terrain_core.npz  (station-NPZ schema)
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from build_source_city_terrain import compute_delta_z, compute_svf, RES_M
from build_station_terrain import resample_dem

SRTM = REPO / "data" / "external" / "xichang" / "dem" / "xichang_srtm_dem.tif"
OUT = REPO / "data" / "processed" / "pinn_inputs" / "xichang_terrain_core.npz"
# re-framed south (2026-06-27) to include Qionghai Lake (~27.81) + the full Anning
# valley: city in the N half, lake S, Lushan W. (was the city-centred 27.819–27.969.)
BB = dict(lat_min=27.770, lat_max=27.950, lon_min=102.160, lon_max=102.360)
M_PER_DEG_LAT = 111_200.0


def main(city="xichang"):
    sys.path.insert(0, str(REPO / "scripts"))
    from city_config import cfg
    c = cfg(city)
    b = c["box"]
    BB = dict(lat_min=b[0], lat_max=b[1], lon_min=b[2], lon_max=b[3])
    srtm = REPO / "data" / "external" / city / "dem" / c["dem"]
    out = REPO / "data" / "processed" / "pinn_inputs" / f"{city}_terrain_core.npz"
    lat_c = 0.5 * (BB["lat_min"] + BB["lat_max"])
    dlat = RES_M / M_PER_DEG_LAT
    dlon = RES_M / (M_PER_DEG_LAT * np.cos(np.radians(lat_c)))
    lats = np.arange(BB["lat_min"], BB["lat_max"] + dlat / 2, dlat)
    lons = np.arange(BB["lon_min"], BB["lon_max"] + dlon / 2, dlon)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    elev = resample_dem(srtm, lat_grid.astype("f4"), lon_grid.astype("f4"))[::-1]  # N-S flip
    print(f"{city}: grid {lat_grid.shape} elev {elev.min():.0f}..{elev.max():.0f} m")
    dz = compute_delta_z(elev); svf = compute_svf(elev)
    np.savez(out, delta_z=dz.astype("f4"),
             delta_z_norm=(dz / max(dz.max(), 1.0)).astype("f4"), svf=svf,
             lat_grid=lat_grid.astype("f4"), lon_grid=lon_grid.astype("f4"),
             res_m=np.float32(RES_M),
             bbox_lat_min=np.float32(BB["lat_min"]), bbox_lat_max=np.float32(BB["lat_max"]),
             bbox_lon_min=np.float32(BB["lon_min"]), bbox_lon_max=np.float32(BB["lon_max"]))
    cy, cx = c["cen"]
    i = np.abs(lat_grid[:, 0] - cy).argmin(); j = np.abs(lon_grid[0, :] - cx).argmin()
    print(f"  Δz at urban core ({cy},{cx})={dz[i,j]:.0f}  range {dz.min():.0f}..{dz.max():.0f}")
    print(f"  wrote {out}")


if __name__ == "__main__":
    import argparse
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("--city", default="xichang")
    main(ap.parse_args().city)
