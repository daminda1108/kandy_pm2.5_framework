"""
build_source_city_terrain.py — Compute delta_z (TPI) and SVF for source cities.

Reads the existing *_elev_grid_100m.npz for each city and produces
*_terrain_tpi_svf_100m.npz with identical schema to kandy_terrain_tpi_svf_100m.npz.

Outputs:
  data/processed/pinn_inputs/medellin_terrain_tpi_svf_100m.npz
  data/processed/pinn_inputs/chiangmai_terrain_tpi_svf_100m.npz
  (kathmandu added when its DEM is downloaded)

Usage:
    python scripts/build_source_city_terrain.py
    python scripts/build_source_city_terrain.py --city medellin
    python scripts/build_source_city_terrain.py --plot
    python scripts/build_source_city_terrain.py --force
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import minimum_filter

sys.path.insert(0, str(Path(__file__).parents[1]))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PINN_INPUT_DIR = Path(__file__).parents[1] / "data/processed/pinn_inputs"

RES_M = 100.0
DELTA_Z_RADII_M = [500, 1000, 2000]
DELTA_Z_WEIGHTS = [0.5, 0.3, 0.2]
SVF_N_DIRS = 16
SVF_MAX_DIST_M = 2000

CITIES = ["medellin", "chiangmai", "kathmandu"]


def compute_delta_z(elev: np.ndarray, res_m: float = RES_M) -> np.ndarray:
    """Multi-scale elevation above local valley floor (Whiteman 2014)."""
    weighted = np.zeros_like(elev, dtype=np.float64)
    w_total = 0.0
    for r_m, w in zip(DELTA_Z_RADII_M, DELTA_Z_WEIGHTS):
        r_px = max(1, int(r_m / res_m))
        size = 2 * r_px + 1
        valley_floor = minimum_filter(elev, size=size, mode="nearest")
        dz = np.maximum(0.0, elev - valley_floor).astype(np.float64)
        weighted += w * dz
        w_total += w
        log.info("  dz @ %dm: min=%.1f max=%.1f mean=%.1f", r_m, dz.min(), dz.max(), dz.mean())
    return (weighted / w_total).astype(np.float32)


def compute_svf(elev: np.ndarray, res_m: float = RES_M,
                n_dirs: int = SVF_N_DIRS,
                max_dist_m: float = SVF_MAX_DIST_M) -> np.ndarray:
    """Sky-view factor via horizon-angle scan (cos² formula, Dozier & Frew 1990)."""
    H, W = elev.shape
    max_steps = int(max_dist_m / res_m)
    angles = np.linspace(0, 2 * np.pi, n_dirs, endpoint=False)
    cos2_sum = np.zeros((H, W), dtype=np.float64)

    for k, angle in enumerate(angles):
        dx = np.cos(angle)
        dy = np.sin(angle)
        max_tan = np.full((H, W), -np.inf, dtype=np.float64)
        for step in range(1, max_steps + 1):
            dist_m = step * res_m
            rows_src = np.clip(np.arange(H)[:, None] + dy * step, 0, H - 1).astype(int)
            cols_src = np.clip(np.arange(W)[None, :] + dx * step, 0, W - 1).astype(int)
            tan_angle = (elev[rows_src, cols_src] - elev) / dist_m
            np.maximum(max_tan, tan_angle, out=max_tan)
        max_tan_pos = np.maximum(0.0, max_tan)
        cos2_sum += 1.0 / (1.0 + max_tan_pos ** 2)
        if (k + 1) % 4 == 0:
            log.info("  SVF: %d/%d directions", k + 1, n_dirs)

    svf = (cos2_sum / n_dirs).astype(np.float32)
    log.info("  SVF: min=%.3f max=%.3f mean=%.3f", svf.min(), svf.max(), svf.mean())
    return svf


def process_city(city: str, force: bool = False, plot: bool = False):
    elev_npz = PINN_INPUT_DIR / f"{city}_elev_grid_100m.npz"
    out_npz = PINN_INPUT_DIR / f"{city}_terrain_tpi_svf_100m.npz"

    if not elev_npz.exists():
        log.warning("Elevation NPZ not found for %s: %s", city, elev_npz)
        return False

    if out_npz.exists() and not force:
        log.info("Already exists: %s  (--force to rebuild)", out_npz.name)
        return True

    log.info("=" * 55)
    log.info("Processing: %s", city.upper())
    d = np.load(elev_npz)
    elev = d["elev"].astype(np.float32)
    lat_grid = d["lat_grid"]
    lon_grid = d["lon_grid"]
    log.info("  elev: %s  range %.0f–%.0f m", elev.shape, elev.min(), elev.max())

    log.info("Computing delta_z ...")
    delta_z = compute_delta_z(elev)
    delta_z_norm = (delta_z / max(delta_z.max(), 1.0)).astype(np.float32)
    log.info("  delta_z: %.1f–%.1f m (mean %.1f)", delta_z.min(), delta_z.max(), delta_z.mean())

    log.info("Computing SVF (%d dirs, max %dm) ...", SVF_N_DIRS, SVF_MAX_DIST_M)
    svf = compute_svf(elev)

    np.savez(
        out_npz,
        delta_z=delta_z,
        delta_z_norm=delta_z_norm,
        svf=svf,
        lat_grid=lat_grid,
        lon_grid=lon_grid,
        res_m=np.float32(RES_M),
    )
    log.info("Saved: %s", out_npz)

    if plot:
        _plot(city, elev, delta_z, svf, out_npz.with_suffix(".png"))

    return True


def _plot(city, elev, delta_z, svf, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f"{city.title()} — Terrain Inputs for SharedTerrainAnsatz", fontsize=12)
    for ax, data, title, cmap in zip(
        axes,
        [elev, delta_z, svf],
        ["Elevation [m ASL]", "delta_z — above valley floor [m]", "SVF (low=enclosed)"],
        ["terrain", "YlOrRd_r", "Blues_r"],
    ):
        im = ax.imshow(data, origin="lower", cmap=cmap)
        ax.set_title(title, fontsize=10)
        plt.colorbar(im, ax=ax)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    log.info("Saved plot: %s", out_png)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=CITIES + ["all"], default="all")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    cities = CITIES if args.city == "all" else [args.city]
    for city in cities:
        process_city(city, force=args.force, plot=args.plot)


if __name__ == "__main__":
    main()
