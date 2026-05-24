"""
DEPRECATED — pre-FourierPINNV3 source term implementation.

Status (2026-05-08, audit §B.5): superseded by `source_kernel.py` and the AlphaNet
defined inline in `models/fourier_pinn_v3.py`. Do not import from new code paths.

────────────────────────────────────────────────────────────────────────────

source_term.py — OSM-anchored parameterized emission source term S(x,y,t).

Fixes the K–S co-identification problem in the PINN inverse problem.
See RESEARCH_PROJECT_DESIGN.md Section 2.11.

The problem:
    If K(x,y,t) and S(x,y,t) are both free neural networks, the training finds
    degenerate solutions where high K + low S ≡ low K + high S in terms of the
    observed PM2.5 field. The inverse problem is underdetermined.

The solution:
    Fix the SPATIAL STRUCTURE of S to the OSM road network.
    Only learn its TEMPORAL AMPLITUDE (4–6 scalars).
    This makes K the uniquely-determined free field.

    S(x, y, t)  =  A_θ(t)  ×  R(x, y)

    R(x,y) = road proximity kernel  [fixed, from OSM + WorldCover]
    A_θ(t) = temporal amplitude      [learned, 4–6 PyTorch parameters]

Usage:
    kernel = SourceKernel(dem_path=..., pinn_x=..., pinn_y=...)
    kernel.build()  # downloads OSM roads, rasterizes, saves R(x,y)

    # In PINN training:
    from source_term import ParameterizedSourceTerm
    source_model = ParameterizedSourceTerm(R=kernel.R_grid)
    S = source_model(t_hours)  # returns [1, n_y, n_x] tensor
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import KANDY_PINN_BBOX, PINN_GRID_RESOLUTION_M, LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("source_term")

# Physical constants
SIGMA_ROAD_M  = 200.0    # road influence radius (m) — Gaussian decay
SIGMA_INDUS_M = 500.0    # industrial zone influence radius (m)
BACKGROUND_EMISSION = 0.1  # fraction of emission from non-road sources (diffuse)

# Road categories and their relative emission weights
ROAD_WEIGHTS = {
    "motorway":      1.5,
    "trunk":         1.5,
    "primary":       1.2,
    "secondary":     1.0,
    "tertiary":      0.7,
    "residential":   0.4,
    "unclassified":  0.3,
}


# ─────────────────────────────────────────────────────────────────────────────
# ROAD PROXIMITY KERNEL (Static — computed once)
# ─────────────────────────────────────────────────────────────────────────────

class SourceKernel:
    """
    Build and cache the static spatial emission kernel R(x,y).

    R(x,y) encodes the spatial distribution of emission sources:
      - Road proximity (Gaussian decay from each road segment, weighted by type)
      - Industrial zones from ESA WorldCover (class 50)
      - Background (uniform low-level diffuse emission)

    R is normalized to [0, 1] so that the learned amplitude A_θ controls
    the absolute emission rate.
    """

    def __init__(
        self,
        pinn_x: np.ndarray,
        pinn_y: np.ndarray,
        cache_dir: str | Path = "data/processed/pinn_inputs",
        worldcover_path: str | Path | None = None,
    ) -> None:
        self.x = pinn_x               # 1-D longitude array
        self.y = pinn_y               # 1-D latitude array
        self.XX, self.YY = np.meshgrid(pinn_x, pinn_y)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.worldcover_path = Path(worldcover_path) if worldcover_path else None
        self.R_grid: Optional[np.ndarray] = None

    def build(self, force_rebuild: bool = False) -> np.ndarray:
        """
        Build R(x,y) from OSM roads and WorldCover land cover.
        Caches result to disk so subsequent runs skip the OSM download.
        """
        cache_file = self.cache_dir / "source_kernel_R.npy"
        if cache_file.exists() and not force_rebuild:
            log.info(f"Loading cached source kernel from {cache_file}")
            self.R_grid = np.load(cache_file)
            return self.R_grid

        # ── Download OSM road network for Kandy ──────────────────────────
        try:
            import osmnx as ox
        except ImportError:
            raise ImportError("osmnx not installed. Run: pip install osmnx")

        log.info("Downloading OSM road network for Kandy (one-time) …")
        bbox = KANDY_PINN_BBOX
        G = ox.graph_from_bbox(
            north=bbox["lat_max"], south=bbox["lat_min"],
            east=bbox["lon_max"],  west=bbox["lon_min"],
            network_type="drive",
        )
        edges = ox.graph_to_gdfs(G, nodes=False)
        log.info(f"Downloaded {len(edges)} road segments.")

        # ── Rasterize: for each pixel, compute weighted distance to roads ─
        R = np.zeros_like(self.XX, dtype=np.float32)

        # Pixel size in degrees
        dx_deg = self.x[1] - self.x[0]
        dy_deg = self.y[1] - self.y[0]
        dx_m   = dx_deg * 111_319
        dy_m   = dy_deg * 111_319

        # For each road segment, mark points within sigma_road
        from shapely.geometry import Point
        log.info(f"Building road kernel ({self.XX.shape[0]}×{self.XX.shape[1]} grid) …")

        for _, row in edges.iterrows():
            road_type = str(row.get("highway", "residential"))
            if isinstance(road_type, list):
                road_type = road_type[0]
            weight = ROAD_WEIGHTS.get(road_type, 0.3)

            geom = row.geometry
            if geom is None:
                continue

            # Get bounding box of road segment + buffer
            minx, miny, maxx, maxy = geom.bounds
            buffer_deg = SIGMA_ROAD_M / 111_319 * 3   # 3-sigma buffer

            ix_min = max(0, int((minx - buffer_deg - self.x[0]) / dx_deg))
            ix_max = min(self.XX.shape[1]-1, int((maxx + buffer_deg - self.x[0]) / dx_deg))
            iy_min = max(0, int((miny - buffer_deg - self.y[0]) / dy_deg))
            iy_max = min(self.XX.shape[0]-1, int((maxy + buffer_deg - self.y[0]) / dy_deg))

            for iy in range(iy_min, iy_max + 1):
                for ix in range(ix_min, ix_max + 1):
                    pt = Point(self.XX[iy, ix], self.YY[iy, ix])
                    dist_m = geom.distance(pt) * 111_319
                    contribution = weight * np.exp(-0.5 * (dist_m / SIGMA_ROAD_M)**2)
                    R[iy, ix] += contribution

        # ── WorldCover: add industrial zone contribution ──────────────────
        if self.worldcover_path and self.worldcover_path.exists():
            import rasterio
            from scipy.interpolate import RegularGridInterpolator
            with rasterio.open(self.worldcover_path) as src:
                wc = src.read(1).astype(np.float32)
                lons_wc = np.linspace(src.bounds.left, src.bounds.right, wc.shape[1])
                lats_wc = np.linspace(src.bounds.top, src.bounds.bottom, wc.shape[0])
            # Class 50 = Built-up in WorldCover v200
            industrial = (wc == 50).astype(np.float32)
            interp_wc = RegularGridInterpolator(
                (lats_wc, lons_wc), industrial, method="nearest",
                bounds_error=False, fill_value=0.0,
            )
            pts = np.column_stack([self.YY.ravel(), self.XX.ravel()])
            industrial_grid = interp_wc(pts).reshape(self.XX.shape)

            # Gaussian blur to spread industrial influence
            from scipy.ndimage import gaussian_filter
            sigma_px = SIGMA_INDUS_M / (dx_m)
            industrial_smooth = gaussian_filter(industrial_grid, sigma=sigma_px)
            R += 0.5 * industrial_smooth / (industrial_smooth.max() + 1e-8)

        # ── Background + normalize ────────────────────────────────────────
        R += BACKGROUND_EMISSION
        R = R / (R.max() + 1e-8)   # normalize to [0, 1]

        np.save(cache_file, R)
        log.info(f"Source kernel saved → {cache_file}  (max={R.max():.3f})")
        self.R_grid = R
        return R


# ─────────────────────────────────────────────────────────────────────────────
# PARAMETERIZED SOURCE TERM (PyTorch module — used in PINN training)
# ─────────────────────────────────────────────────────────────────────────────

class ParameterizedSourceTerm(nn.Module):
    """
    Learned temporal amplitude multiplied by the fixed spatial kernel R(x,y).

    S(x, y, t) = A_θ(t) × R(x, y)

    A_θ(t) decomposes the diurnal emission cycle into:
      - background level  (constant)
      - morning rush      (Gaussian peak at ~07:30 LST, width ~1.5 h)
      - evening rush      (Gaussian peak at ~17:30 LST, width ~1.5 h)
      - nighttime minimum (scalar multiplier on background)

    Only 5 trainable parameters — makes the inverse problem well-posed.
    """

    def __init__(self, R: np.ndarray, device: str = "cpu") -> None:
        super().__init__()
        self.device = torch.device(device)

        # Register fixed spatial kernel (non-trainable)
        R_tensor = torch.from_numpy(R.astype(np.float32)).to(self.device)
        self.register_buffer("R", R_tensor)   # shape [n_y, n_x]

        # Trainable diurnal parameters (initialized to physically plausible values)
        # All are log-transformed to ensure positivity
        self.log_base     = nn.Parameter(torch.tensor([  0.0]))  # base emission [exp(0)=1]
        self.log_am_peak  = nn.Parameter(torch.tensor([  1.0]))  # morning rush amplitude
        self.log_pm_peak  = nn.Parameter(torch.tensor([  0.8]))  # evening rush amplitude
        self.am_hour      = nn.Parameter(torch.tensor([  7.5]))  # morning peak hour (LST)
        self.pm_hour      = nn.Parameter(torch.tensor([ 17.5]))  # evening peak hour (LST)
        self.log_sigma    = nn.Parameter(torch.tensor([  0.4]))  # log(peak width in hours)

    def diurnal_amplitude(self, t_hours_lst: torch.Tensor) -> torch.Tensor:
        """
        Compute diurnal emission amplitude A(t) for a batch of LST hours.

        Args:
            t_hours_lst: shape [N] or scalar, Local Standard Time in hours [0, 24)

        Returns:
            amplitude: shape [N] or scalar, positive scalar multiplier
        """
        sigma  = torch.exp(self.log_sigma).clamp(0.3, 3.0)
        base   = torch.exp(self.log_base).clamp(0.01, 10.0)
        am_amp = torch.exp(self.log_am_peak).clamp(0.1, 20.0)
        pm_amp = torch.exp(self.log_pm_peak).clamp(0.1, 20.0)

        am_peak = torch.exp(-0.5 * ((t_hours_lst - self.am_hour) / sigma) ** 2)
        pm_peak = torch.exp(-0.5 * ((t_hours_lst - self.pm_hour) / sigma) ** 2)

        return base + am_amp * am_peak + pm_amp * pm_peak

    def forward(self, t_hours_lst: torch.Tensor) -> torch.Tensor:
        """
        Compute S(x, y, t) for given time(s).

        Args:
            t_hours_lst: LST hours, shape [N] (one value per batch element)

        Returns:
            S: shape [N, n_y, n_x] — emission field at each time step
        """
        A = self.diurnal_amplitude(t_hours_lst)   # [N]
        # Broadcast: [N] × [n_y, n_x] → [N, n_y, n_x]
        S = A.view(-1, 1, 1) * self.R.unsqueeze(0)
        return S

    def get_diurnal_profile(self, resolution: int = 48) -> dict:
        """Return the learned diurnal emission profile for visualization."""
        hours = torch.linspace(0, 24, resolution)
        with torch.no_grad():
            A = self.diurnal_amplitude(hours)
        return {
            "hours": hours.numpy(),
            "amplitude": A.numpy(),
            "am_peak_hour": float(self.am_hour),
            "pm_peak_hour": float(self.pm_hour),
            "peak_width_h": float(torch.exp(self.log_sigma)),
        }


# ─────────────────────────────────────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bbox = KANDY_PINN_BBOX
    n_x = int((bbox["lon_max"] - bbox["lon_min"]) * 111_319 / PINN_GRID_RESOLUTION_M)
    n_y = int((bbox["lat_max"] - bbox["lat_min"]) * 111_319 / PINN_GRID_RESOLUTION_M)
    x_grid = np.linspace(bbox["lon_min"], bbox["lon_max"], n_x)
    y_grid = np.linspace(bbox["lat_min"], bbox["lat_max"], n_y)

    kernel = SourceKernel(pinn_x=x_grid, pinn_y=y_grid)
    R = kernel.build()

    log.info(f"Source kernel shape: {R.shape}")
    log.info(f"  Max (road pixel): {R.max():.3f}")
    log.info(f"  Mean (background): {R.mean():.3f}")

    source = ParameterizedSourceTerm(R=R)
    t_test = torch.tensor([7.5, 12.0, 17.5, 22.0])
    S_test = source(t_test)
    log.info(f"Source field shape: {S_test.shape}")

    profile = source.get_diurnal_profile()
    log.info(f"AM peak: {profile['am_peak_hour']:.1f}h LST")
    log.info(f"PM peak: {profile['pm_peak_hour']:.1f}h LST")
    log.info(f"Peak width: {profile['peak_width_h']:.1f}h")

    try:
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        axes[0].imshow(R, origin="lower", cmap="hot_r",
                       extent=[x_grid[0], x_grid[-1], y_grid[0], y_grid[-1]])
        axes[0].set_title("Spatial Source Kernel R(x,y)\n(road network + built-up)")
        axes[0].set_xlabel("Longitude"); axes[0].set_ylabel("Latitude")
        plt.colorbar(axes[0].images[0], ax=axes[0], label="Relative emission intensity")

        axes[1].plot(profile["hours"], profile["amplitude"])
        axes[1].axvline(profile["am_peak_hour"], color="r", ls="--", label=f"AM rush {profile['am_peak_hour']:.1f}h")
        axes[1].axvline(profile["pm_peak_hour"], color="b", ls="--", label=f"PM rush {profile['pm_peak_hour']:.1f}h")
        axes[1].set_title("Learned Diurnal Emission Profile A_θ(t)")
        axes[1].set_xlabel("LST (hours)"); axes[1].set_ylabel("Relative emission amplitude")
        axes[1].legend()
        axes[1].grid(alpha=0.3)

        plt.tight_layout()
        Path("results/figures").mkdir(parents=True, exist_ok=True)
        plt.savefig("results/figures/source_term_test.png", dpi=150, bbox_inches="tight")
        log.info("Test figure saved to results/figures/source_term_test.png")
    except Exception as e:
        log.info(f"Plot skipped: {e}")
