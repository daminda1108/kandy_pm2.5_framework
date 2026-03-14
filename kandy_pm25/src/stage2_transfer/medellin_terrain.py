"""
medellin_terrain.py — Terrain processing for Medellín Stage 2 PINN.

Produces two files:
  data/processed/pinn_inputs/medellin_elev_grid_100m.npz
    Arrays: elev (150×150), elev_norm (150×150), lat_grid, lon_grid
    elev_norm = (elev - elev_min) / (elev_max - elev_min) ∈ [0, 1]

  data/processed/pinn_inputs/medellin_road_kernel_100m.npz
    Arrays: R (150×150), lat_grid, lon_grid
    R(x,y) ∈ [0,1] — normalised emission kernel for S = alpha(t) × R(x,y)

WHY TERRAIN MATTERS FOR MEDELLÍN
----------------------------------
The PINN domain (15×15km) spans the Aburrá valley floor (1,475m ASL)
to the surrounding Andean ridges (2,500–3,100m ASL). Elevation drop of
~1,000–1,800m within the domain.

1. Elevation → DiffusionSubNetV3 (elev_norm input):
   K(x,y) is conditioned on elevation — valley floor has lower K (trapped
   air mass), ridge tops have higher K (free troposphere mixing).

2. Road kernel → AlphaNet source term:
   S(x,y,t) = alpha(t) × R(x,y). Fixes spatial structure of emissions,
   breaks K–S degeneracy. Medellín has heavy traffic on valley floor roads
   (Autopista Norte/Sur, Av. El Poblado) — road kernel captures this.

3. Valley wind decomposition (N-S axis, 0°):
   Along-valley = N-S ERA5 wind component (v10); cross-valley = E-W (u10).
   Used in PDE advection term u·∇C. Built into medellin_build_dataset.py.

USAGE
-----
    # Build both (first run)
    python src/stage2_transfer/medellin_terrain.py

    # Check status
    python src/stage2_transfer/medellin_terrain.py --check

    # Rebuild road kernel only (force)
    python src/stage2_transfer/medellin_terrain.py --no-elev --force

    # Save diagnostic PNG
    python src/stage2_transfer/medellin_terrain.py --plot
"""

import argparse
import logging
import sys
import time
from pathlib import Path

import numpy as np
import requests
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import (
    LOG_FORMAT, LOG_DATEFMT,
    MEDELLIN_PINN_BBOX, MEDELLIN_DEM_DIR,
    PINN_GRID_RESOLUTION_M, PROC_DIR,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("medellin_terrain")

# ── Grid parameters ────────────────────────────────────────────────────────────
BBOX     = MEDELLIN_PINN_BBOX
GRID_RES = PINN_GRID_RESOLUTION_M   # 100 m

# Degrees per metre at Medellín latitude (~6.22°N)
M_PER_DEG_LAT = 111_200.0
M_PER_DEG_LON = 111_200.0 * np.cos(np.radians(6.22))   # ≈ 110,580 m/deg

GRID_STEP_DEG_LAT = GRID_RES / M_PER_DEG_LAT
GRID_STEP_DEG_LON = GRID_RES / M_PER_DEG_LON

# ── Road kernel parameters ─────────────────────────────────────────────────────
DEFAULT_SIGMA_M  = 150.0   # emission footprint σ (same as Kandy)
WORLDCOVER_BETA  = 0.15    # built-up background fraction

# Road class emission weights (COPERT/EMEP fractions)
ROAD_WEIGHTS = {
    "motorway":      1.0,
    "trunk":         0.9,
    "primary":       1.0,
    "secondary":     0.6,
    "tertiary":      0.3,
    "unclassified":  0.15,
    "residential":   0.2,
    "living_street": 0.10,
    "service":       0.10,
}
DEFAULT_ROAD_WEIGHT = 0.10

# ── Paths ─────────────────────────────────────────────────────────────────────
PINN_INPUT_DIR = PROC_DIR / "pinn_inputs"
DEM_TIF        = MEDELLIN_DEM_DIR / "medellin_dem.tif"
OUT_ELEV_NPZ   = PINN_INPUT_DIR / "medellin_elev_grid_100m.npz"
OUT_ROAD_NPZ   = PINN_INPUT_DIR / "medellin_road_kernel_100m.npz"
OUT_ROAD_TIF   = PINN_INPUT_DIR / "medellin_road_kernel_100m.tif"
OUT_ELEV_TIF   = PINN_INPUT_DIR / "medellin_elev_grid_100m.tif"

OVERPASS_URL     = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT = 90


# ─────────────────────────────────────────────────────────────────────────────
# GRID CONSTRUCTION
# ─────────────────────────────────────────────────────────────────────────────

def make_grid() -> tuple[np.ndarray, np.ndarray, int, int]:
    """Build the 150×150 100m Medellín PINN grid."""
    lat_min = BBOX["lat_min"]
    lat_max = BBOX["lat_max"]
    lon_min = BBOX["lon_min"]
    lon_max = BBOX["lon_max"]

    lats = np.arange(lat_min, lat_max + GRID_STEP_DEG_LAT / 2, GRID_STEP_DEG_LAT)
    lons = np.arange(lon_min, lon_max + GRID_STEP_DEG_LON / 2, GRID_STEP_DEG_LON)

    lats = lats[:150]
    lons = lons[:150]

    ny, nx = len(lats), len(lons)
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    log.info(
        f"Grid: {ny}×{nx} at {GRID_RES}m  "
        f"(lat {lats[0]:.4f}–{lats[-1]:.4f}, lon {lons[0]:.4f}–{lons[-1]:.4f})"
    )
    return lat_grid, lon_grid, ny, nx


# ─────────────────────────────────────────────────────────────────────────────
# ELEVATION GRID
# ─────────────────────────────────────────────────────────────────────────────

def build_elev_grid(lat_grid: np.ndarray, lon_grid: np.ndarray, force: bool = False) -> np.ndarray:
    """
    Crop and resample medellin_dem.tif to the 150×150 PINN grid.

    Returns elev (ny, nx) in metres ASL.
    """
    if OUT_ELEV_NPZ.exists() and not force:
        log.info(f"Elevation grid already built: {OUT_ELEV_NPZ}  (use --force to rebuild)")
        data = np.load(str(OUT_ELEV_NPZ))
        return data["elev"]

    if not DEM_TIF.exists():
        raise FileNotFoundError(
            f"DEM not found: {DEM_TIF}\n"
            "Download SRTM 1-arc-sec for Medellín bbox from Copernicus/EarthData."
        )

    import rasterio
    import rasterio.warp as rwarp
    from rasterio.transform import from_bounds

    ny, nx = lat_grid.shape
    log.info(f"Resampling DEM {DEM_TIF.name} → {ny}×{nx} at {GRID_RES}m...")

    with rasterio.open(str(DEM_TIF)) as src:
        log.info(
            f"  Source DEM: {src.width}×{src.height} px, res={src.res}, "
            f"CRS={src.crs}, range=[{src.read(1, masked=True).min():.0f},"
            f"{src.read(1, masked=True).max():.0f}] m"
        )

        transform = from_bounds(
            west=lon_grid[0, 0],  south=lat_grid[0, 0],
            east=lon_grid[-1, -1], north=lat_grid[-1, -1],
            width=nx, height=ny,
        )

        elev = np.zeros((ny, nx), dtype=np.float32)
        rwarp.reproject(
            source=rasterio.band(src, 1),
            destination=elev,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs="EPSG:4326",
            resampling=rwarp.Resampling.bilinear,
        )

    # Replace no-data fill values (typically -32768 or 0 at ocean edges)
    elev = np.where(elev < 0, np.nan, elev)
    nan_count = np.isnan(elev).sum()
    if nan_count > 0:
        log.warning(f"  {nan_count} NaN cells in DEM → filling with nearest neighbour")
        from scipy.ndimage import generic_filter
        def _nanmean(x):
            v = x[~np.isnan(x)]
            return v.mean() if len(v) > 0 else np.nan
        # Simple fill: replace NaN with column mean (valley floor estimate)
        col_means = np.nanmean(elev, axis=0)
        for j in range(nx):
            mask = np.isnan(elev[:, j])
            elev[mask, j] = col_means[j]

    elev_min = float(np.nanmin(elev))
    elev_max = float(np.nanmax(elev))
    elev_norm = ((elev - elev_min) / (elev_max - elev_min)).clip(0.0, 1.0)

    log.info(
        f"  Elevation: min={elev_min:.0f} m, max={elev_max:.0f} m, "
        f"mean={np.nanmean(elev):.0f} m, range={elev_max - elev_min:.0f} m"
    )

    # Save NPZ
    PINN_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(
        str(OUT_ELEV_NPZ),
        elev=elev.astype(np.float32),
        elev_norm=elev_norm.astype(np.float32),
        lat_grid=lat_grid.astype(np.float32),
        lon_grid=lon_grid.astype(np.float32),
        elev_min=np.float32(elev_min),
        elev_max=np.float32(elev_max),
        bbox_lat_min=np.float32(BBOX["lat_min"]),
        bbox_lat_max=np.float32(BBOX["lat_max"]),
        bbox_lon_min=np.float32(BBOX["lon_min"]),
        bbox_lon_max=np.float32(BBOX["lon_max"]),
        grid_resolution_m=np.float32(GRID_RES),
    )
    log.info(f"Saved: {OUT_ELEV_NPZ}")

    # Save GeoTIFF
    try:
        from rasterio.transform import from_bounds as fb
        transform = fb(
            west=lon_grid[0, 0], south=lat_grid[0, 0],
            east=lon_grid[-1, -1], north=lat_grid[-1, -1],
            width=nx, height=ny,
        )
        with rasterio.open(
            str(OUT_ELEV_TIF), "w",
            driver="GTiff", height=ny, width=nx,
            count=1, dtype=np.float32,
            crs="EPSG:4326", transform=transform,
        ) as dst:
            data = elev[::-1, :] if lat_grid[0, 0] < lat_grid[-1, 0] else elev
            dst.write(data, 1)
        log.info(f"Saved: {OUT_ELEV_TIF}")
    except Exception as exc:
        log.warning(f"GeoTIFF save failed: {exc}")

    return elev


# ─────────────────────────────────────────────────────────────────────────────
# ROAD KERNEL
# ─────────────────────────────────────────────────────────────────────────────

def download_osm_roads(retries: int = 3) -> list[dict]:
    """Download road network for MEDELLIN_PINN_BBOX from Overpass API."""
    query = f"""
[out:json][timeout:{OVERPASS_TIMEOUT}];
(
  way["highway"]({BBOX['lat_min']},{BBOX['lon_min']},{BBOX['lat_max']},{BBOX['lon_max']});
);
out body;
>;
out skel qt;
"""
    log.info("Querying Overpass API for Medellín road network...")

    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                OVERPASS_URL,
                data={"data": query},
                timeout=OVERPASS_TIMEOUT + 10,
            )
            resp.raise_for_status()
            osm = resp.json()
            break
        except requests.RequestException as exc:
            log.warning(f"  Attempt {attempt}/{retries} failed: {exc}")
            if attempt < retries:
                time.sleep(5 * attempt)
            else:
                raise RuntimeError("Overpass API failed") from exc

    nodes = {
        el["id"]: (el["lat"], el["lon"])
        for el in osm["elements"]
        if el["type"] == "node"
    }
    ways = []
    for el in osm["elements"]:
        if el["type"] != "way":
            continue
        hw_type = el.get("tags", {}).get("highway", "")
        if not hw_type:
            continue
        coords = [nodes[nid] for nid in el.get("nodes", []) if nid in nodes]
        if len(coords) < 2:
            continue
        ways.append({"highway": hw_type, "coords": coords})

    log.info(f"  Downloaded {len(ways)} road segments ({len(nodes)} nodes)")
    highway_counts: dict[str, int] = {}
    for w in ways:
        highway_counts[w["highway"]] = highway_counts.get(w["highway"], 0) + 1
    for hw, cnt in sorted(highway_counts.items(), key=lambda x: -x[1])[:10]:
        log.info(f"    {hw}: {cnt} segments")
    return ways


def _rasterise_segment(
    lat0: float, lon0: float,
    lat1: float, lon1: float,
    lat_grid: np.ndarray, lon_grid: np.ndarray,
    presence: np.ndarray,
) -> None:
    lat_min_g = lat_grid[0, 0]
    lon_min_g = lon_grid[0, 0]
    dlat = lat_grid[1, 0] - lat_grid[0, 0] if lat_grid.shape[0] > 1 else GRID_STEP_DEG_LAT
    dlon = lon_grid[0, 1] - lon_grid[0, 0] if lat_grid.shape[1] > 1 else GRID_STEP_DEG_LON
    ny, nx = presence.shape

    def to_idx(lat, lon):
        return (lat - lat_min_g) / dlat, (lon - lon_min_g) / dlon

    iy0, ix0 = to_idx(lat0, lon0)
    iy1, ix1 = to_idx(lat1, lon1)
    n_steps = max(int(np.ceil(max(abs(iy1 - iy0), abs(ix1 - ix0)))), 1) * 2

    for k in range(n_steps + 1):
        t  = k / n_steps
        iy = iy0 + t * (iy1 - iy0)
        ix = ix0 + t * (ix1 - ix0)
        r, c = int(round(iy)), int(round(ix))
        if 0 <= r < ny and 0 <= c < nx:
            presence[r, c] = True


def rasterise_roads(
    ways: list[dict],
    lat_grid: np.ndarray,
    lon_grid: np.ndarray,
    sigma_m: float = DEFAULT_SIGMA_M,
) -> np.ndarray:
    from collections import defaultdict
    ny, nx = lat_grid.shape
    class_ways: dict[float, list] = defaultdict(list)
    for w in ways:
        wt = ROAD_WEIGHTS.get(w["highway"], DEFAULT_ROAD_WEIGHT)
        class_ways[wt].append(w["coords"])

    kernel = np.zeros((ny, nx), dtype=float)
    for weight, coord_lists in class_ways.items():
        presence = np.zeros((ny, nx), dtype=bool)
        for coords in coord_lists:
            for i in range(len(coords) - 1):
                lat0, lon0 = coords[i]
                lat1, lon1 = coords[i + 1]
                _rasterise_segment(lat0, lon0, lat1, lon1, lat_grid, lon_grid, presence)
        if not presence.any():
            continue
        dist_m = distance_transform_edt(~presence) * GRID_RES
        decay   = np.exp(-dist_m / sigma_m)
        kernel += weight * decay
        log.info(f"    weight={weight:.2f}: {presence.sum()} road cells")
    return kernel


def build_road_kernel(
    lat_grid: np.ndarray,
    lon_grid: np.ndarray,
    sigma_m: float = DEFAULT_SIGMA_M,
    force: bool = False,
) -> np.ndarray:
    if OUT_ROAD_NPZ.exists() and not force:
        log.info(f"Road kernel already built: {OUT_ROAD_NPZ}  (use --force to rebuild)")
        data = np.load(str(OUT_ROAD_NPZ))
        return data["R"]

    ways = download_osm_roads()
    if not ways:
        raise RuntimeError("No road ways returned from Overpass API")

    log.info(f"Rasterising {len(ways)} road ways at σ={sigma_m}m...")
    kernel_raw = rasterise_roads(ways, lat_grid, lon_grid, sigma_m=sigma_m)

    # Normalise
    k_max = kernel_raw.max()
    if k_max > 0:
        kernel_norm = (kernel_raw / k_max).astype(np.float32)
    else:
        log.warning("Kernel is all zeros — check OSM download")
        kernel_norm = kernel_raw.astype(np.float32)

    ny, nx = lat_grid.shape
    PINN_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(
        str(OUT_ROAD_NPZ),
        R=kernel_norm,
        lat_grid=lat_grid.astype(np.float32),
        lon_grid=lon_grid.astype(np.float32),
        sigma_m=np.float32(sigma_m),
        bbox_lat_min=np.float32(BBOX["lat_min"]),
        bbox_lat_max=np.float32(BBOX["lat_max"]),
        bbox_lon_min=np.float32(BBOX["lon_min"]),
        bbox_lon_max=np.float32(BBOX["lon_max"]),
        grid_resolution_m=np.float32(GRID_RES),
    )
    log.info(f"Saved: {OUT_ROAD_NPZ}")
    log.info(
        f"Kernel stats: non-zero={( kernel_norm > 0.01).sum()}/{kernel_norm.size} cells "
        f"({100*(kernel_norm > 0.01).mean():.1f}%), mean={kernel_norm.mean():.4f}"
    )

    # GeoTIFF
    try:
        import rasterio
        from rasterio.transform import from_bounds
        transform = from_bounds(
            west=lon_grid[0, 0], south=lat_grid[0, 0],
            east=lon_grid[-1, -1], north=lat_grid[-1, -1],
            width=nx, height=ny,
        )
        with rasterio.open(
            str(OUT_ROAD_TIF), "w",
            driver="GTiff", height=ny, width=nx,
            count=1, dtype=np.float32,
            crs="EPSG:4326", transform=transform,
        ) as dst:
            data = kernel_norm[::-1, :] if lat_grid[0, 0] < lat_grid[-1, 0] else kernel_norm
            dst.write(data, 1)
        log.info(f"Saved: {OUT_ROAD_TIF}")
    except Exception as exc:
        log.warning(f"GeoTIFF save failed: {exc}")

    return kernel_norm


# ─────────────────────────────────────────────────────────────────────────────
# LOAD FUNCTIONS (called from PINN training)
# ─────────────────────────────────────────────────────────────────────────────

def load_elev_grid() -> tuple[np.ndarray, np.ndarray]:
    """
    Load pre-computed Medellín elevation grid.
    Returns (elev, elev_norm) each shape (150, 150).
    elev in metres ASL. elev_norm ∈ [0, 1].
    """
    if not OUT_ELEV_NPZ.exists():
        raise FileNotFoundError(
            f"Elevation grid not found: {OUT_ELEV_NPZ}\n"
            "Build it first: python src/stage2_transfer/medellin_terrain.py"
        )
    data = np.load(str(OUT_ELEV_NPZ))
    return data["elev"], data["elev_norm"]


def load_road_kernel() -> np.ndarray:
    """
    Load pre-computed Medellín road kernel.
    Returns R shape (150, 150), values ∈ [0, 1].
    """
    if not OUT_ROAD_NPZ.exists():
        raise FileNotFoundError(
            f"Road kernel not found: {OUT_ROAD_NPZ}\n"
            "Build it first: python src/stage2_transfer/medellin_terrain.py"
        )
    data = np.load(str(OUT_ROAD_NPZ))
    return data["R"].astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# PLOT
# ─────────────────────────────────────────────────────────────────────────────

def _plot(lat_grid, lon_grid, elev, kernel_norm) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not installed — skipping plot")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    im0 = axes[0].pcolormesh(lon_grid, lat_grid, elev, cmap="terrain")
    plt.colorbar(im0, ax=axes[0], label="Elevation (m ASL)")
    axes[0].set_title("Medellín PINN Domain — Elevation (100m grid)")
    axes[0].set_xlabel("Longitude"); axes[0].set_ylabel("Latitude")

    im1 = axes[1].pcolormesh(lon_grid, lat_grid, kernel_norm, cmap="hot_r", vmin=0, vmax=1)
    plt.colorbar(im1, ax=axes[1], label="Normalised emission intensity R(x,y)")
    axes[1].set_title("Medellín PINN Domain — Road Emission Kernel")
    axes[1].set_xlabel("Longitude"); axes[1].set_ylabel("Latitude")

    plt.tight_layout()
    plot_path = PINN_INPUT_DIR / "medellin_terrain_100m.png"
    plt.savefig(str(plot_path), dpi=150, bbox_inches="tight")
    log.info(f"Plot saved: {plot_path}")
    plt.close()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build Medellín PINN terrain inputs")
    parser.add_argument("--force",    action="store_true", help="Rebuild even if outputs exist")
    parser.add_argument("--no-elev",  action="store_true", help="Skip elevation grid")
    parser.add_argument("--no-road",  action="store_true", help="Skip road kernel")
    parser.add_argument("--sigma",    type=float, default=DEFAULT_SIGMA_M,
                        help=f"Road decay σ in metres (default {DEFAULT_SIGMA_M})")
    parser.add_argument("--plot",     action="store_true", help="Save diagnostic PNG")
    parser.add_argument("--check",    action="store_true", help="Check output status only")
    args = parser.parse_args()

    if args.check:
        for path, label in [(OUT_ELEV_NPZ, "Elev grid"), (OUT_ROAD_NPZ, "Road kernel")]:
            if path.exists():
                sz = path.stat().st_size / 1e3
                log.info(f"  ✓ {label}: {path.name}  ({sz:.1f} KB)")
            else:
                log.info(f"  ✗ {label}: NOT built — {path}")
        return

    lat_grid, lon_grid, ny, nx = make_grid()
    elev = None
    kernel_norm = None

    if not args.no_elev:
        elev = build_elev_grid(lat_grid, lon_grid, force=args.force)

    if not args.no_road:
        kernel_norm = build_road_kernel(lat_grid, lon_grid, sigma_m=args.sigma, force=args.force)

    if args.plot and elev is not None and kernel_norm is not None:
        _plot(lat_grid, lon_grid, elev, kernel_norm)
    elif args.plot:
        log.warning("--plot requires both elev and road kernel to be built")


if __name__ == "__main__":
    main()
