"""build_xichang_windninja.py — WindNinja diagnostic-wind library for Xichang,
mirroring the Kandy build (scripts/build_windninja_library.py) on the city-centred
Xichang domain (urban core 27.894 N, 102.264 E — west shore of Qionghai Lake, foot
of Lushan).  Same conditions grid (16 dir × 2 speed × night/day), mass-consistent
solver + Forthofer diurnal slope-flow (katabatic drainage off Lushan, lake breeze).

Stage 1: export the SRTM DEM → UTM 48N (EPSG:32648) 90 m GeoTIFF over the city box.
Stage 2: run WindNinja for each condition, resample to a 64×64 lat/lon grid.
Out: data/processed/pinn_inputs/xichang_dem_utm48n_90m.tif
     data/processed/pinn_inputs/xichang_windninja_library.npz
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

CLI = Path("d:/ProjectCD/tools/wn/bin/WindNinja_cli.exe")
CITY = "xichang"            # overridden by --city via _setup()
SRTM = REPO / "data" / "external" / "xichang" / "dem" / "xichang_srtm_dem.tif"
DEM = REPO / "data" / "processed" / "pinn_inputs" / "xichang_dem_utm48n_90m.tif"
WORK = Path("d:/ProjectCD/tools/wn_lib_xichang")
OUT = REPO / "data" / "processed" / "pinn_inputs" / "xichang_windninja_library.npz"
UTM = "EPSG:32648"
TZ = "Asia/Shanghai"
BB = dict(lat_min=27.770, lat_max=27.950, lon_min=102.160, lon_max=102.360)


def _setup(city):
    """Point all module globals at `city` (from city_config)."""
    global CITY, SRTM, DEM, WORK, OUT, UTM, TZ, BB
    sys.path.insert(0, str(REPO / "scripts"))
    from city_config import cfg
    c = cfg(city); b = c["box"]
    CITY = city
    SRTM = REPO / "data" / "external" / city / "dem" / c["dem"]
    DEM = REPO / "data" / "processed" / "pinn_inputs" / f"{city}_dem_utm90m.tif"
    WORK = Path(f"d:/ProjectCD/tools/wn_lib_{city}")
    OUT = REPO / "data" / "processed" / "pinn_inputs" / f"{city}_windninja_library.npz"
    UTM = c["utm"]; TZ = c["tz"]
    BB = dict(lat_min=b[0], lat_max=b[1], lon_min=b[2], lon_max=b[3])
N = 64
DIRS = np.arange(0, 360, 22.5)
SPEEDS = [1.0, 4.0]
REGIMES = [("night", 3, 2.0), ("day", 13, 12.0)]    # winter temps (C)
MESH = 90


def export_dem():
    """Crop the SRTM tile to the box (+buffer) and warp to UTM 48N at 90 m."""
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    from rasterio.windows import from_bounds as win_from_bounds
    buf = 0.03
    with rasterio.open(SRTM) as src:
        win = win_from_bounds(BB["lon_min"] - buf, BB["lat_min"] - buf,
                              BB["lon_max"] + buf, BB["lat_max"] + buf, src.transform)
        elev = src.read(1, window=win)
        wtf = src.window_transform(win)
        elev = np.where(elev < -1000, np.nan, elev).astype("float32")
        col = np.nanmean(elev, axis=0)
        idx = np.where(np.isnan(elev))
        elev[idx] = np.take(col, idx[1])
        ny, nx = elev.shape
        dst_tf, w, h = calculate_default_transform(
            src.crs, UTM, nx, ny,
            *rasterio.transform.array_bounds(ny, nx, wtf), resolution=90.0)
        DEM.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(DEM, "w", driver="GTiff", height=h, width=w, count=1,
                           dtype="float32", crs=UTM, transform=dst_tf, nodata=-9999.0) as dst:
            reproject(source=elev, destination=rasterio.band(dst, 1),
                      src_transform=wtf, src_crs=src.crs,
                      dst_transform=dst_tf, dst_crs=UTM, resampling=Resampling.bilinear)
    with rasterio.open(DEM) as d:
        a = d.read(1); a = a[a > -9000]
        print(f"  DEM {d.width}x{d.height} UTM48N 90 m  elev {a.min():.0f}..{a.max():.0f} m")


def read_asc(p: Path):
    h = {}
    with open(p) as f:
        for _ in range(6):
            k, v = f.readline().split(); h[k.lower()] = float(v)
        A = np.loadtxt(f)
    return A, h


def run_one(direction, speed, hour, temp):
    import glob as _glob
    WORK.mkdir(parents=True, exist_ok=True)
    cmd = [str(CLI), "--elevation_file", str(DEM),
           "--initialization_method", "domainAverageInitialization",
           "--input_speed", str(speed), "--input_speed_units", "mps",
           "--input_direction", str(int(direction)),
           "--input_wind_height", "10", "--units_input_wind_height", "m",
           "--output_wind_height", "10", "--units_output_wind_height", "m",
           "--vegetation", "grass", "--mesh_resolution", str(MESH),
           "--units_mesh_resolution", "m",
           "--diurnal_winds", "true", "--uni_air_temp", str(temp), "--air_temp_units", "C",
           "--uni_cloud_cover", "0", "--cloud_cover_units", "percent",
           "--year", "2025", "--month", "12", "--day", "29", "--hour", str(hour), "--minute", "0",
           "--time_zone", TZ, "--write_ascii_output", "true",
           "--output_path", str(WORK), "--num_threads", "4"]
    sp_i = int(round(speed))
    pat = str(WORK / f"{DEM.stem}_{int(direction)}_{sp_i}_*_{hour:02d}00_{MESH}m_vel.asc")
    for _ in range(2):
        subprocess.run(cmd, capture_output=True, text=True)
        hits = sorted(_glob.glob(pat), key=lambda f: Path(f).stat().st_mtime)
        if hits:
            vf = Path(hits[-1])
            vel, hv = read_asc(vf)
            ang, _ = read_asc(Path(str(vf).replace("_vel.asc", "_ang.asc")))
            return vel, ang, hv
    raise FileNotFoundError(pat)


def main():
    import pyproj
    from scipy.interpolate import RegularGridInterpolator
    assert CLI.exists(), f"WindNinja CLI not found at {CLI}"
    if not DEM.exists():
        print("Stage 1: export UTM DEM"); export_dem()
    lats = np.linspace(BB["lat_min"], BB["lat_max"], N)
    lons = np.linspace(BB["lon_min"], BB["lon_max"], N)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    tf = pyproj.Transformer.from_crs("EPSG:4326", UTM, always_xy=True)
    X, Y = tf.transform(LO.ravel(), LA.ravel())

    U = np.zeros((len(DIRS), len(SPEEDS), len(REGIMES), N, N)); V = np.zeros_like(U)
    total = U.shape[0] * U.shape[1] * U.shape[2]; k = 0
    print("Stage 2: WindNinja library")
    for di, d in enumerate(DIRS):
        for si, s in enumerate(SPEEDS):
            for ri, (rname, hour, temp) in enumerate(REGIMES):
                vel, ang, h = run_one(d, s, hour, temp)
                nc, nr, x0, y0, cs = (int(h["ncols"]), int(h["nrows"]),
                                      h["xllcorner"], h["yllcorner"], h["cellsize"])
                ax = x0 + (np.arange(nc) + 0.5) * cs
                ay = y0 + (np.arange(nr) + 0.5) * cs
                gv = RegularGridInterpolator((ay[::-1], ax), vel, bounds_error=False, fill_value=None)
                ga = RegularGridInterpolator((ay[::-1], ax), ang, bounds_error=False, fill_value=None)
                pts = np.stack([Y, X], axis=1)
                spd = gv(pts).reshape(N, N)
                a_from = np.deg2rad(ga(pts).reshape(N, N))
                U[di, si, ri] = -spd * np.sin(a_from)
                V[di, si, ri] = -spd * np.cos(a_from)
                k += 1
                if k % 8 == 0 or k == total:
                    print(f"  {k}/{total}  dir={int(d)} s={s} {rname}  "
                          f"core|domain spd {spd[N//2,N//2]:.2f}|{spd.mean():.2f}")
    np.savez_compressed(OUT, u=U, v=V, dirs=DIRS, speeds=np.array(SPEEDS),
                        regimes=np.array([r[0] for r in REGIMES]), lats=lats, lons=lons,
                        regime_hours=np.array([r[1] for r in REGIMES]),
                        bbox=np.array([BB["lat_min"], BB["lat_max"], BB["lon_min"], BB["lon_max"]]))
    print(f"\nlibrary {U.shape} -> {OUT}")


if __name__ == "__main__":
    import argparse
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("--city", default="xichang")
    _setup(ap.parse_args().city)
    main()
