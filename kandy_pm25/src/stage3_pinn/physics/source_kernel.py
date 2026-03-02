"""
source_kernel.py — OSM road kernel for Stage 3 PINN source term S(x,y).

WHY THIS EXISTS
---------------
The PINN source term is S(x,y,t) = α(t) × R(x,y) where:
  - R(x,y) is a FIXED spatial kernel encoding where emissions occur (roads + built-up)
  - α(t) is a LEARNED scalar amplitude (diurnal traffic cycle)

Fixing R(x,y) removes the K–S degeneracy: the PINN cannot adjust S spatially
to fit the data — only the overall amplitude α changes with time. K(x,y) must
then account for spatial concentration gradients through the PDE.

SPATIAL KERNEL COMPONENTS
--------------------------
1. OSM road proximity kernel:
   For each 100m grid point, compute distance to nearest road segment.
   Weight by road class: primary=1.0, secondary=0.6, tertiary=0.3, residential=0.2
   Apply distance decay: w_road(x,y) = Σ_class weight × exp(-dist_class / sigma)
   σ = 150m (emission footprint of a road lane at 100m resolution)

2. ESA WorldCover built-up background:
   Class 50 (built-up) → background PM2.5 from non-road urban sources.
   Aggregated from 10m to 100m. Added at fraction β=0.15 of road kernel max.

3. Combined kernel:
   R(x,y) = w_road(x,y) + β × w_worldcover(x,y)
   Normalised to [0, 1] (max = 1).

OUTPUT
------
  data/processed/pinn_inputs/kandy_road_kernel_100m.npz
    Arrays: R (150×150), lon_grid (150×150), lat_grid (150×150)

  data/processed/pinn_inputs/kandy_road_kernel_100m.tif
    GeoTIFF: same R array, EPSG:4326, 100m resolution

USAGE
-----
    python source_kernel.py [--force] [--sigma 150] [--plot]
    python source_kernel.py --check    # verify output exists and show stats

DEPENDENCIES
------------
  requests, shapely, rasterio, scipy, numpy (all in venv)
  Optional: osmnx (pip install osmnx) for richer road type filtering

NOTES
-----
  - Uses Overpass API (free, no key needed) to download Kandy road network
  - Overpass rate limit: 1 request per city is fine; ~5s download
  - If WorldCover GeoTIFF not present, road kernel only is used (logged as warning)
  - Run ONCE before Stage 3 training; result is fixed for all epochs
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np
import requests
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    LOG_FORMAT, LOG_DATEFMT,
    KANDY_PINN_BBOX, PINN_GRID_RESOLUTION_M,
    PROC_DIR,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("source_kernel")

# ── Grid parameters ───────────────────────────────────────────────────────────
BBOX      = KANDY_PINN_BBOX
GRID_RES  = PINN_GRID_RESOLUTION_M       # 100 m

# Approximate degrees per metre at Kandy latitude (~7.29°N)
M_PER_DEG_LAT = 111_200.0               # metres per degree latitude
M_PER_DEG_LON = 111_200.0 * np.cos(np.radians(7.29))   # ≈ 110,330 m/deg

DEG_PER_M_LAT = 1.0 / M_PER_DEG_LAT
DEG_PER_M_LON = 1.0 / M_PER_DEG_LON

GRID_STEP_DEG_LAT = GRID_RES * DEG_PER_M_LAT   # ~0.000899°
GRID_STEP_DEG_LON = GRID_RES * DEG_PER_M_LON   # ~0.000907°

# ── Emission decay parameter ──────────────────────────────────────────────────
DEFAULT_SIGMA_M = 150.0    # road emission footprint σ in metres
WORLDCOVER_BETA = 0.15     # weight of built-up background vs. road kernel max

# ── Road class emission weights ───────────────────────────────────────────────
# Based on relative emission intensity (COPERT/EMEP road type fractions)
ROAD_WEIGHTS = {
    "motorway":       1.0,
    "trunk":          0.9,
    "primary":        1.0,
    "secondary":      0.6,
    "tertiary":       0.3,
    "unclassified":   0.15,
    "residential":    0.2,
    "living_street":  0.10,
    "service":        0.10,
}
DEFAULT_ROAD_WEIGHT = 0.10   # for any highway type not in the dict above

# ── Paths ─────────────────────────────────────────────────────────────────────
PINN_INPUT_DIR = PROC_DIR / "pinn_inputs"
OUT_NPZ  = PINN_INPUT_DIR / "kandy_road_kernel_100m.npz"
OUT_TIF  = PINN_INPUT_DIR / "kandy_road_kernel_100m.tif"
WORLDCOVER_TIF = PROC_DIR / "pinn_inputs" / "kandy_worldcover_100m.tif"


# ─────────────────────────────────────────────────────────────────────────────
# GRID CONSTRUCTION
# ─────────────────────────────────────────────────────────────────────────────

def make_grid() -> tuple[np.ndarray, np.ndarray, int, int]:
    """
    Build the 100m Kandy PINN grid.
    Returns: lat_grid (ny, nx), lon_grid (ny, nx), ny, nx
    """
    lat_min = BBOX["lat_min"]
    lat_max = BBOX["lat_max"]
    lon_min = BBOX["lon_min"]
    lon_max = BBOX["lon_max"]

    lats = np.arange(lat_min, lat_max + GRID_STEP_DEG_LAT / 2, GRID_STEP_DEG_LAT)
    lons = np.arange(lon_min, lon_max + GRID_STEP_DEG_LON / 2, GRID_STEP_DEG_LON)

    # Clip to expected 150 × 150
    lats = lats[:150]
    lons = lons[:150]

    ny, nx = len(lats), len(lons)
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    log.info(f"Grid: {ny}×{nx} at {GRID_RES}m  (lat {lats[0]:.4f}–{lats[-1]:.4f}, lon {lons[0]:.4f}–{lons[-1]:.4f})")
    return lat_grid, lon_grid, ny, nx


# ─────────────────────────────────────────────────────────────────────────────
# OVERPASS API DOWNLOAD
# ─────────────────────────────────────────────────────────────────────────────

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT = 90   # seconds

def download_osm_roads(bbox: dict, retries: int = 3) -> list[dict]:
    """
    Download road network from Overpass API for KANDY_PINN_BBOX.
    Returns list of way dicts with geometry (list of [lon, lat] nodes).
    """
    # Overpass QL: all highway ways in bbox, with their geometry
    query = f"""
[out:json][timeout:{OVERPASS_TIMEOUT}];
(
  way["highway"]({bbox['lat_min']},{bbox['lon_min']},{bbox['lat_max']},{bbox['lon_max']});
);
out body;
>;
out skel qt;
"""
    log.info("Querying Overpass API for Kandy road network...")

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
                raise RuntimeError(f"Overpass API failed after {retries} attempts") from exc

    # Build node lookup {node_id: (lat, lon)}
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
    highway_counts = {}
    for w in ways:
        highway_counts[w["highway"]] = highway_counts.get(w["highway"], 0) + 1
    for hw, cnt in sorted(highway_counts.items(), key=lambda x: -x[1])[:10]:
        log.info(f"    {hw}: {cnt} segments")

    return ways


# ─────────────────────────────────────────────────────────────────────────────
# KERNEL RASTERISATION
# ─────────────────────────────────────────────────────────────────────────────

def rasterise_roads(
    ways: list[dict],
    lat_grid: np.ndarray,
    lon_grid: np.ndarray,
    sigma_m: float = DEFAULT_SIGMA_M,
) -> np.ndarray:
    """
    Rasterise OSM road ways onto the 100m grid using distance decay.

    Strategy:
      For each road class, build a binary presence raster (1 where a road segment
      passes through the cell), then apply distance_transform_edt to get distance
      to nearest road in that class. Decay: w = weight × exp(-dist / sigma).
      Sum across all classes.

    Parameters
    ----------
    ways     : road segment list from download_osm_roads()
    lat_grid : (ny, nx) latitude grid
    lon_grid : (ny, nx) longitude grid
    sigma_m  : emission decay scale in metres (default 150m)

    Returns
    -------
    kernel : (ny, nx) float array in [0, ∞), before normalisation
    """
    ny, nx = lat_grid.shape

    # Group ways by weight (merge similar classes to reduce computation)
    from collections import defaultdict
    class_ways: dict[float, list] = defaultdict(list)
    for w in ways:
        wt = ROAD_WEIGHTS.get(w["highway"], DEFAULT_ROAD_WEIGHT)
        class_ways[wt].append(w["coords"])

    kernel = np.zeros((ny, nx), dtype=float)

    for weight, coord_lists in class_ways.items():
        # Build binary presence raster for this road class
        presence = np.zeros((ny, nx), dtype=bool)

        for coords in coord_lists:
            # Rasterise each way segment by segment
            for i in range(len(coords) - 1):
                lat0, lon0 = coords[i]
                lat1, lon1 = coords[i + 1]
                _rasterise_segment(
                    lat0, lon0, lat1, lon1,
                    lat_grid, lon_grid,
                    presence,
                )

        if not presence.any():
            continue

        # Distance transform: distance from each cell to nearest road in this class
        # EDT works in pixel units; convert to metres using grid resolution
        # (grid is ~100m, so pixel distance × 100 ≈ metres)
        not_road = ~presence
        # distance_transform_edt returns distance in pixel units
        dist_px = distance_transform_edt(not_road)
        dist_m  = dist_px * GRID_RES

        # Gaussian decay
        decay = np.exp(-dist_m / sigma_m)
        kernel += weight * decay

        log.info(f"    weight={weight:.2f}: {presence.sum()} road cells, max_decay={decay.max():.3f}")

    return kernel


def _rasterise_segment(
    lat0: float, lon0: float,
    lat1: float, lon1: float,
    lat_grid: np.ndarray, lon_grid: np.ndarray,
    presence: np.ndarray,
) -> None:
    """
    Mark all grid cells that a road segment (lat0,lon0)→(lat1,lon1) passes through.
    Uses a simple pixel-walk (Bresenham-like) approach in grid-index space.
    """
    lat_min_g = lat_grid[0, 0]
    lon_min_g = lon_grid[0, 0]
    dlat = lat_grid[1, 0] - lat_grid[0, 0] if lat_grid.shape[0] > 1 else GRID_STEP_DEG_LAT
    dlon = lon_grid[0, 1] - lon_grid[0, 0] if lat_grid.shape[1] > 1 else GRID_STEP_DEG_LON

    ny, nx = presence.shape

    # Convert endpoints to (fractional) grid indices
    def to_idx(lat, lon):
        iy = (lat - lat_min_g) / dlat
        ix = (lon - lon_min_g) / dlon
        return iy, ix

    iy0, ix0 = to_idx(lat0, lon0)
    iy1, ix1 = to_idx(lat1, lon1)

    # Number of interpolation steps = max pixel distance
    n_steps = max(int(np.ceil(max(abs(iy1 - iy0), abs(ix1 - ix0)))), 1) * 2

    for k in range(n_steps + 1):
        t  = k / n_steps
        iy = iy0 + t * (iy1 - iy0)
        ix = ix0 + t * (ix1 - ix0)
        r  = int(round(iy))
        c  = int(round(ix))
        if 0 <= r < ny and 0 <= c < nx:
            presence[r, c] = True


# ─────────────────────────────────────────────────────────────────────────────
# WORLDCOVER INTEGRATION
# ─────────────────────────────────────────────────────────────────────────────

def add_worldcover(kernel: np.ndarray, lat_grid: np.ndarray, lon_grid: np.ndarray) -> np.ndarray:
    """
    Add ESA WorldCover built-up fraction as background emission layer.

    WorldCover class 50 = built-up. Aggregated from 10m to 100m.
    The built-up layer adds WORLDCOVER_BETA × kernel_max × f_buildup(x,y)
    to represent non-road urban sources (construction, domestic heating, etc.).

    Requires: data/processed/pinn_inputs/kandy_worldcover_100m.tif
    If not present, returns kernel unchanged (with a warning).
    """
    if not WORLDCOVER_TIF.exists():
        log.warning(
            f"WorldCover GeoTIFF not found: {WORLDCOVER_TIF}\n"
            "  Proceeding with road kernel only (no built-up background).\n"
            "  Download WorldCover via GEE: ee.Image('ESA/WorldCover/v200/2021')\n"
            "  Export to data/processed/pinn_inputs/kandy_worldcover_100m.tif"
        )
        return kernel

    try:
        import rasterio
        from rasterio.transform import from_bounds
    except ImportError:
        log.warning("rasterio not installed — skipping WorldCover integration")
        return kernel

    log.info(f"Adding WorldCover built-up layer: {WORLDCOVER_TIF}")
    ny, nx = kernel.shape

    with rasterio.open(str(WORLDCOVER_TIF)) as src:
        import rasterio.warp as warp
        # Reproject/resample WorldCover to match our 100m grid
        buildup_100m = np.zeros((ny, nx), dtype=np.float32)
        transform = rasterio.transform.from_bounds(
            west=lon_grid[0, 0], south=lat_grid[0, 0],
            east=lon_grid[-1, -1], north=lat_grid[-1, -1],
            width=nx, height=ny,
        )
        warp.reproject(
            source=src.read(1).astype(np.float32),
            destination=buildup_100m,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs="EPSG:4326",
            resampling=warp.Resampling.average,
        )
        # WorldCover class 50 = built-up; remap to [0, 1] fraction
        # After average resampling of a binary (50/not-50) raster,
        # values range from 0 (no built-up) to 50 (fully built-up) → normalise
        buildup_frac = np.where(
            buildup_100m > 0,
            buildup_100m / 50.0,
            0.0,
        ).clip(0.0, 1.0)

    log.info(f"  Built-up fraction: mean={buildup_frac.mean():.3f}, max={buildup_frac.max():.3f}")

    # Add to kernel as background
    kernel_max = kernel.max() if kernel.max() > 0 else 1.0
    kernel_with_buildup = kernel + WORLDCOVER_BETA * kernel_max * buildup_frac

    log.info(
        f"  Combined kernel: max road={kernel.max():.3f}, "
        f"background contribution={WORLDCOVER_BETA * kernel_max * buildup_frac.mean():.4f}"
    )
    return kernel_with_buildup


# ─────────────────────────────────────────────────────────────────────────────
# SAVE OUTPUT
# ─────────────────────────────────────────────────────────────────────────────

def save_kernel(
    kernel: np.ndarray,
    lat_grid: np.ndarray,
    lon_grid: np.ndarray,
    sigma_m: float,
) -> None:
    """Save normalised kernel as .npz and GeoTIFF."""
    PINN_INPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Normalise to [0, 1]
    k_max = kernel.max()
    if k_max > 0:
        kernel_norm = kernel / k_max
    else:
        log.warning("Kernel is all zeros — check OSM download")
        kernel_norm = kernel

    # ── npz ──────────────────────────────────────────────────────────────────
    np.savez(
        str(OUT_NPZ),
        R=kernel_norm.astype(np.float32),
        lat_grid=lat_grid.astype(np.float32),
        lon_grid=lon_grid.astype(np.float32),
        sigma_m=np.float32(sigma_m),
        bbox_lat_min=np.float32(BBOX["lat_min"]),
        bbox_lat_max=np.float32(BBOX["lat_max"]),
        bbox_lon_min=np.float32(BBOX["lon_min"]),
        bbox_lon_max=np.float32(BBOX["lon_max"]),
        grid_resolution_m=np.float32(GRID_RES),
    )
    log.info(f"Saved: {OUT_NPZ}")

    # ── GeoTIFF ───────────────────────────────────────────────────────────────
    try:
        import rasterio
        from rasterio.transform import from_bounds
        ny, nx = kernel_norm.shape
        transform = from_bounds(
            west=lon_grid[0, 0], south=lat_grid[0, 0],
            east=lon_grid[-1, -1], north=lat_grid[-1, -1],
            width=nx, height=ny,
        )
        with rasterio.open(
            str(OUT_TIF), "w",
            driver="GTiff",
            height=ny, width=nx,
            count=1,
            dtype=np.float32,
            crs="EPSG:4326",
            transform=transform,
        ) as dst:
            # rasterio uses row 0 = north; flip if lats are ascending
            data = kernel_norm[::-1, :] if lat_grid[0, 0] < lat_grid[-1, 0] else kernel_norm
            dst.write(data.astype(np.float32), 1)
        log.info(f"Saved: {OUT_TIF}")
    except Exception as exc:
        log.warning(f"GeoTIFF save failed: {exc} — npz is the authoritative output")

    log.info(
        f"Kernel stats: non-zero cells = {(kernel_norm > 0.01).sum()} / {kernel_norm.size}, "
        f"mean = {kernel_norm.mean():.4f}, max = {kernel_norm.max():.4f}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# LOAD FUNCTION (called from PINN training)
# ─────────────────────────────────────────────────────────────────────────────

def load_road_kernel() -> np.ndarray:
    """
    Load the pre-computed road kernel for Stage 3 PINN training.

    Returns
    -------
    R : np.ndarray, shape (150, 150), values in [0, 1]
        Normalised emission spatial kernel.  R[row, col] is the relative
        emission intensity at grid point (row, col).

    Raises
    ------
    FileNotFoundError if kernel has not been built yet.
    """
    if not OUT_NPZ.exists():
        raise FileNotFoundError(
            f"Road kernel not found: {OUT_NPZ}\n"
            "Build it first: python src/stage3_pinn/physics/source_kernel.py"
        )
    data = np.load(str(OUT_NPZ))
    R = data["R"].astype(np.float32)
    log.info(f"Loaded road kernel: {R.shape}, non-zero: {(R > 0.01).sum()}")
    return R


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def build_kernel(sigma_m: float = DEFAULT_SIGMA_M, force: bool = False, plot: bool = False) -> np.ndarray:
    """
    Full pipeline: download OSM → rasterise → add WorldCover → save.
    Returns the normalised kernel array.
    """
    if OUT_NPZ.exists() and not force:
        log.info(f"Kernel already built: {OUT_NPZ}  (use --force to rebuild)")
        return load_road_kernel()

    # ── Step 1: Build 100m grid ───────────────────────────────────────────────
    lat_grid, lon_grid, ny, nx = make_grid()

    # ── Step 2: Download OSM roads ────────────────────────────────────────────
    ways = download_osm_roads(BBOX)
    if not ways:
        raise RuntimeError("No road ways returned from Overpass API — check bbox and internet connection")

    # ── Step 3: Rasterise ─────────────────────────────────────────────────────
    log.info(f"Rasterising {len(ways)} road ways at σ={sigma_m}m...")
    kernel_raw = rasterise_roads(ways, lat_grid, lon_grid, sigma_m=sigma_m)

    # ── Step 4: Add WorldCover background ─────────────────────────────────────
    kernel_combined = add_worldcover(kernel_raw, lat_grid, lon_grid)

    # ── Step 5: Save ──────────────────────────────────────────────────────────
    save_kernel(kernel_combined, lat_grid, lon_grid, sigma_m)

    # ── Step 6: Optional plot ─────────────────────────────────────────────────
    if plot:
        _plot_kernel(kernel_combined / kernel_combined.max(), lat_grid, lon_grid)

    return kernel_combined / kernel_combined.max()


def _plot_kernel(kernel_norm: np.ndarray, lat_grid: np.ndarray, lon_grid: np.ndarray) -> None:
    """Quick diagnostic plot of the source kernel."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not installed — skipping plot")
        return

    fig, ax = plt.subplots(1, 1, figsize=(7, 7))
    im = ax.pcolormesh(
        lon_grid, lat_grid, kernel_norm,
        cmap="hot_r", vmin=0, vmax=1,
    )
    plt.colorbar(im, ax=ax, label="Normalised emission intensity R(x,y)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Kandy PINN Source Kernel R(x,y)\n(OSM roads + WorldCover built-up)")
    plt.tight_layout()

    plot_path = PINN_INPUT_DIR / "kandy_road_kernel_100m.png"
    plt.savefig(str(plot_path), dpi=150, bbox_inches="tight")
    log.info(f"Plot saved: {plot_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Build Kandy PINN source emission kernel")
    parser.add_argument("--force",    action="store_true", help="Rebuild even if output exists")
    parser.add_argument("--sigma",    type=float, default=DEFAULT_SIGMA_M,
                        help=f"Road emission decay σ in metres (default {DEFAULT_SIGMA_M})")
    parser.add_argument("--plot",     action="store_true", help="Save diagnostic PNG")
    parser.add_argument("--check",    action="store_true", help="Check output status, do not rebuild")
    args = parser.parse_args()

    if args.check:
        if OUT_NPZ.exists():
            R = load_road_kernel()
            log.info(f"✓ Kernel present: {OUT_NPZ}")
            log.info(f"  Shape:       {R.shape}")
            log.info(f"  Non-zero:    {(R > 0.01).sum()} / {R.size} cells ({100*(R > 0.01).mean():.1f}%)")
            log.info(f"  Mean / Max:  {R.mean():.4f} / {R.max():.4f}")
        else:
            log.info(f"✗ Kernel NOT built yet: {OUT_NPZ}")
            log.info("  Run: python source_kernel.py")
        return

    build_kernel(sigma_m=args.sigma, force=args.force, plot=args.plot)


if __name__ == "__main__":
    main()
