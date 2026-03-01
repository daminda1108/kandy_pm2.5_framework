"""
wind_downscaling.py — Downscale ERA5 wind from 0.25° (~28 km) to PINN grid (100 m).

ERA5 wind cannot drive a 100 m PINN directly: it sees the entire domain as a single
grid point with no knowledge of valley channelling, terrain deflection, or katabatic
drainage. This module applies a terrain-following correction to produce a spatially
heterogeneous wind field suitable as the advection input u(x,y,t) to the PINN.

Physics reference: Whiteman (2000) Mountain Meteorology, Ch. 3–5
See also: RESEARCH_PROJECT_DESIGN.md Section 2.10

Three-stage pipeline:
    Stage 1: Bilinear interpolation of ERA5 onto the PINN grid
    Stage 2: Terrain speed-up and direction deflection from DEM slope/aspect
    Stage 3: Nocturnal katabatic override using Whiteman parameterization

FIXME(Stage 2): Before Medellín pre-training, verify:
    - Medellín SRTM DEM is downloaded and path is correct
    - MEDELLIN_CONFIG bbox/resolution match Stage 2 domain setup
    - build_daily_wind_field() supports 48 half-hourly timesteps (currently 24)

Usage:
    from wind_downscaling import WindDownscaler
    ds = WindDownscaler(dem_path="data/raw/dem/srtm_elevation_30m.tif")
    u, v = ds.downscale(u_era5, v_era5, blh, skin_t, t2m, t_slope, hour_utc)
    # For Medellín:
    ds = WindDownscaler(dem_path="...", domain_config=MEDELLIN_CONFIG)
"""

import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import uniform_filter

import sys
sys.path.insert(0, str(Path(__file__).parents[3]))
from config import KANDY_PINN_BBOX, PINN_GRID_RESOLUTION_M, LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("wind_downscaling")

# ──────────────────────────────────────────────────────────────────────────────
# Domain configuration presets
# ──────────────────────────────────────────────────────────────────────────────
# Wind downscaling is city-specific: valley orientation, grid extent, and
# characteristic wind speed all differ between domains. Medellín pre-training
# (Stage 2) uses a completely different DEM, slope angles, and valley geometry
# (NW–SE orientation) from Kandy (NE–SW). Passing the wrong config silently
# produces incorrect katabatic parameterisation for the pre-training city.

KANDY_CONFIG = {
    "bbox":                 KANDY_PINN_BBOX,
    "resolution_m":         PINN_GRID_RESOLUTION_M,
    "valley_axis_azimuth":  270.0,    # E–W long axis (westward down-valley)
    "valley_tpi_threshold": -15.0,    # m — valley floor TPI threshold
    "char_wind_speed":       1.5,     # m/s — typical Kandy 10m wind (Pemathilaka 2020)
    "katabatic_scale":       3.0,     # m/s per unit KFP
}

MEDELLIN_CONFIG = {
    "bbox":                 {"lat_min": 6.10, "lat_max": 6.40, "lon_min": -75.70, "lon_max": -75.48},
    "resolution_m":         250,
    "valley_axis_azimuth":  315.0,    # NW–SE Aburrá Valley long axis
    "valley_tpi_threshold": -20.0,    # m — deeper/wider valley than Kandy
    "char_wind_speed":       3.0,     # m/s — Medellín valley floor (SIATA climatology)
    "katabatic_scale":       4.0,     # m/s per unit KFP (steeper Andes slopes)
}

# Re-export the Kandy domain constants for backward compatibility with existing imports
KATABATIC_SCALE_FACTOR   = KANDY_CONFIG["katabatic_scale"]
VALLEY_FLOOR_TPI_THRESHOLD = KANDY_CONFIG["valley_tpi_threshold"]
VALLEY_AXIS_AZIMUTH      = KANDY_CONFIG["valley_axis_azimuth"]
SLOPE_SPEEDUP_MAX        = 2.5   # maximum terrain speed-up factor (same for all domains)
KATABATIC_HOURS          = set(range(21, 24)) | set(range(0, 7))  # 21:00–06:00 LST


class WindDownscaler:
    """
    Downscales ERA5 wind vectors to a PINN's domain grid.

    Domain-agnostic: pass `domain_config=KANDY_CONFIG` (default) or
    `domain_config=MEDELLIN_CONFIG` for Medellín Stage 2 pre-training.
    Do not rely on the module-level VALLEY_AXIS_AZIMUTH constant when using
    a non-Kandy domain — it will silently produce wrong katabatic flow direction.

    Attributes:
        dem    : elevation array at DEM native resolution (30 m)
        slope  : slope angle (degrees)
        aspect : aspect angle (degrees, 0=N, 90=E, 180=S, 270=W)
        tpi    : Topographic Position Index (2 km radius)
        x_grid : 1-D longitude array of PINN grid
        y_grid : 1-D latitude array of PINN grid
        cfg    : domain config dict used at construction
    """

    def __init__(
        self,
        dem_path: str | Path,
        domain_config: dict | None = None,
        slope_path: str | Path | None = None,
        aspect_path: str | Path | None = None,
        tpi_path: str | Path | None = None,
        tpi_radius_m: float = 2000.0,
    ) -> None:
        self.cfg = domain_config or KANDY_CONFIG
        dem_path = Path(dem_path)
        log.info(f"Loading DEM for wind downscaling: {dem_path}")

        with rasterio.open(dem_path) as src:
            self.dem = src.read(1).astype(np.float32)
            self.transform_dem = src.transform
            self.crs = src.crs
            self.dem_res_m = abs(src.transform.a) * 111_319   # degrees → metres

        self.dem[self.dem < -9000] = np.nan

        # Compute derived terrain attributes if not provided separately
        self.slope, self.aspect = self._compute_slope_aspect()

        if tpi_path and Path(tpi_path).exists():
            with rasterio.open(tpi_path) as src:
                self.tpi = src.read(1).astype(np.float32)
        else:
            self.tpi = self._compute_tpi(tpi_radius_m)

        # Build PINN grid from domain config
        bbox   = self.cfg["bbox"]
        res_m  = self.cfg["resolution_m"]
        n_x = int((bbox["lon_max"] - bbox["lon_min"]) * 111_319 / res_m)
        n_y = int((bbox["lat_max"] - bbox["lat_min"]) * 111_319 / res_m)
        self.x_grid = np.linspace(bbox["lon_min"], bbox["lon_max"], n_x)
        self.y_grid = np.linspace(bbox["lat_min"], bbox["lat_max"], n_y)
        self.XX, self.YY = np.meshgrid(self.x_grid, self.y_grid)

        # Pre-interpolate static terrain arrays onto PINN grid (done once at init)
        self.slope_grid  = self._resample_to_pinn_grid(self.slope)
        self.aspect_grid = self._resample_to_pinn_grid(self.aspect)
        self.tpi_grid    = self._resample_to_pinn_grid(self.tpi)
        self.dem_grid    = self._resample_to_pinn_grid(self.dem)

        log.info(f"PINN grid: {n_y}×{n_x} pixels at {res_m} m (domain: {bbox})")

    # ─────────────────────────────────────────────────────────────────────────
    # TERRAIN ATTRIBUTE COMPUTATION
    # ─────────────────────────────────────────────────────────────────────────

    def _compute_slope_aspect(self) -> Tuple[np.ndarray, np.ndarray]:
        """Compute slope (degrees) and aspect (degrees) from DEM using finite differences."""
        dx = self.dem_res_m
        dz_dx = np.gradient(self.dem, dx, axis=1)
        dz_dy = np.gradient(self.dem, dx, axis=0)
        slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
        slope_deg = np.degrees(slope_rad)
        # Aspect: 0=N, 90=E (meteorological convention)
        aspect_deg = (np.degrees(np.arctan2(dz_dx, -dz_dy)) + 360) % 360
        return slope_deg, aspect_deg

    def _compute_tpi(self, radius_m: float) -> np.ndarray:
        """Topographic Position Index: elevation relative to neighbourhood mean."""
        radius_px = max(1, int(radius_m / self.dem_res_m))
        window = 2 * radius_px + 1
        mean_elev = uniform_filter(self.dem, size=window, mode="nearest")
        return (self.dem - mean_elev).astype(np.float32)

    # ─────────────────────────────────────────────────────────────────────────
    # GRID RESAMPLING
    # ─────────────────────────────────────────────────────────────────────────

    def _resample_to_pinn_grid(self, arr: np.ndarray) -> np.ndarray:
        """Bilinear interpolation of a DEM-resolution array onto the PINN grid."""
        # Build DEM coordinate arrays
        nrows, ncols = arr.shape
        lons = np.array([self.transform_dem.c + i * self.transform_dem.a for i in range(ncols)])
        lats = np.array([self.transform_dem.f + j * self.transform_dem.e for j in range(nrows)])

        arr_clean = np.nan_to_num(arr, nan=0.0)
        interp = RegularGridInterpolator(
            (lats[::-1], lons), arr_clean[::-1], method="linear",
            bounds_error=False, fill_value=0.0,
        )
        pts = np.column_stack([self.YY.ravel(), self.XX.ravel()])
        return interp(pts).reshape(self.YY.shape).astype(np.float32)

    def _interp_era5_scalar(
        self,
        era5_lats: np.ndarray,
        era5_lons: np.ndarray,
        values: np.ndarray,
    ) -> np.ndarray:
        """Bilinear interpolation of a 2-D ERA5 field onto the PINN grid."""
        interp = RegularGridInterpolator(
            (era5_lats, era5_lons), values,
            method="linear", bounds_error=False, fill_value=float(np.nanmean(values)),
        )
        pts = np.column_stack([self.YY.ravel(), self.XX.ravel()])
        return interp(pts).reshape(self.YY.shape).astype(np.float32)

    # ─────────────────────────────────────────────────────────────────────────
    # MAIN DOWNSCALING METHOD
    # ─────────────────────────────────────────────────────────────────────────

    def downscale(
        self,
        u_era5: np.ndarray,
        v_era5: np.ndarray,
        hour_utc: float,
        era5_lats: np.ndarray | None = None,
        era5_lons: np.ndarray | None = None,
        blh: float = 500.0,
        skin_t: float = 295.0,
        t2m: float = 293.0,
        dt_slope: float = 2.0,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Downscale ERA5 wind to PINN grid for a single time step.

        Args:
            u_era5     : U wind component, shape [n_era5_lat, n_era5_lon] or scalar
            v_era5     : V wind component (same shape as u_era5)
            hour_utc   : UTC hour (0–23) for katabatic timing
            era5_lats  : ERA5 latitude grid (needed if u_era5 is 2-D)
            era5_lons  : ERA5 longitude grid
            blh        : Boundary layer height (m) — modulates katabatic
            skin_t     : Skin temperature (K)
            t2m        : 2m air temperature (K)
            dt_slope   : Temperature difference slope minus valley floor (K)

        Returns:
            u_out, v_out: Wind fields on PINN grid [n_y, n_x]
        """
        # ── Stage 1: Interpolate ERA5 onto PINN grid ─────────────────────
        if np.isscalar(u_era5) or (hasattr(u_era5, "ndim") and u_era5.ndim == 0):
            # Single-point ERA5 (common in narrow bbox) — broadcast uniformly
            u_base = np.full_like(self.dem_grid, float(u_era5))
            v_base = np.full_like(self.dem_grid, float(v_era5))
        else:
            assert era5_lats is not None and era5_lons is not None, \
                "era5_lats and era5_lons required when u_era5/v_era5 are 2-D"
            u_base = self._interp_era5_scalar(era5_lats, era5_lons, u_era5)
            v_base = self._interp_era5_scalar(era5_lats, era5_lons, v_era5)

        # ── Stage 2: Terrain speed-up and direction deflection ────────────
        slope_rad  = np.radians(self.slope_grid)
        aspect_rad = np.radians(self.aspect_grid)

        # Speed-up factor: terrain compression/expansion along wind path
        # Increases as slope steepens; capped to avoid unrealistic values
        era5_wind_speed = np.sqrt(u_base**2 + v_base**2) + 1e-6
        era5_wind_dir   = np.arctan2(v_base, u_base)

        # Terrain alignment factor: how much the slope faces into/away from the wind
        alignment = np.cos(aspect_rad - era5_wind_dir)
        speedup = np.clip(1.0 + np.sin(slope_rad) * alignment, 0.5, SLOPE_SPEEDUP_MAX)
        u_terrain = u_base * speedup
        v_terrain = v_base * speedup

        # Valley floor channelling: rotate to valley axis on flat valley bottom
        tpi_thresh      = self.cfg.get("valley_tpi_threshold", VALLEY_FLOOR_TPI_THRESHOLD)
        valley_axis_deg = self.cfg.get("valley_axis_azimuth",  VALLEY_AXIS_AZIMUTH)
        valley_mask = self.tpi_grid < tpi_thresh
        if valley_mask.any():
            valley_axis_rad = np.radians(valley_axis_deg)
            speed_valley    = np.sqrt(u_terrain**2 + v_terrain**2)
            u_terrain[valley_mask] = speed_valley[valley_mask] * np.cos(valley_axis_rad)
            v_terrain[valley_mask] = speed_valley[valley_mask] * np.sin(valley_axis_rad)

        # ── Stage 3: Nocturnal katabatic override ─────────────────────────
        hour_lst = (hour_utc + 5.5) % 24   # UTC → LST
        is_katabatic_period = (hour_lst >= 21) or (hour_lst < 7)
        blh_suppression = np.clip(blh / 300.0, 0.5, 1.0)
        katabatic_scale = self.cfg.get("katabatic_scale", KATABATIC_SCALE_FACTOR)

        if is_katabatic_period and dt_slope > 0:
            # Whiteman (2000): katabatic speed ∝ ΔT × sin(α) / √(BLH)
            katabatic_speed = (
                katabatic_scale
                * dt_slope
                * np.sin(slope_rad)
                * blh_suppression
                * (1.0 - min(hour_lst - 7, 0) / 2.0)   # fade in/out near boundaries
            )
            # Direction: downslope (opposite to aspect direction)
            katabatic_u = -katabatic_speed * np.sin(aspect_rad)   # downslope u
            katabatic_v = -katabatic_speed * np.cos(aspect_rad)   # downslope v

            # Blend: katabatic overrides only where slope > 5° (meaningful drainage)
            significant_slope = self.slope_grid > 5.0
            u_terrain[significant_slope] = (
                0.3 * u_terrain[significant_slope] + 0.7 * katabatic_u[significant_slope]
            )
            v_terrain[significant_slope] = (
                0.3 * v_terrain[significant_slope] + 0.7 * katabatic_v[significant_slope]
            )

        return u_terrain, v_terrain

    def build_daily_wind_field(
        self,
        u_era5_hourly: list[float],
        v_era5_hourly: list[float],
        blh_hourly: list[float],
        skin_t: float,
        t2m: float,
        n_steps: int = 48,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Build wind field arrays for a full diurnal cycle.

        Args:
            n_steps: Number of temporal steps per day (48 for 30-min, 24 for hourly).
                     ERA5 hourly inputs are linearly interpolated to match n_steps.

        Returns:
            u_out, v_out: shape [n_steps, n_y, n_x]
        """
        n_y, n_x = self.dem_grid.shape
        n_era5 = len(u_era5_hourly)

        # Interpolate ERA5 hourly → n_steps if needed
        if n_steps != n_era5:
            era5_hours = np.linspace(0, 24, n_era5, endpoint=False)
            out_hours  = np.linspace(0, 24, n_steps, endpoint=False)
            u_interp = np.interp(out_hours, era5_hours, u_era5_hourly)
            v_interp = np.interp(out_hours, era5_hours, v_era5_hourly)
            blh_interp = np.interp(out_hours, era5_hours, blh_hourly) if blh_hourly else [500.0] * n_steps
        else:
            u_interp, v_interp = u_era5_hourly, v_era5_hourly
            blh_interp = blh_hourly if blh_hourly else [500.0] * n_steps

        u_out = np.zeros((n_steps, n_y, n_x), dtype=np.float32)
        v_out = np.zeros((n_steps, n_y, n_x), dtype=np.float32)
        for s in range(n_steps):
            hour_utc = s * 24.0 / n_steps
            u_out[s], v_out[s] = self.downscale(
                u_era5=u_interp[s],
                v_era5=v_interp[s],
                hour_utc=hour_utc,
                blh=blh_interp[s],
                skin_t=skin_t,
                t2m=t2m,
            )
        return u_out, v_out


# ─────────────────────────────────────────────────────────────────────────────
# QUICK VISUAL TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from pathlib import Path
    dem_candidates = list(Path("data/raw/dem").glob("srtm_elevation_30m.tif"))
    if not dem_candidates:
        log.warning("No DEM found. Run download_gee.py --product dem first.")
        sys.exit(0)

    ds = WindDownscaler(dem_path=dem_candidates[0])

    # Synthetic ERA5 westerly at 5 m/s
    u_test, v_test = ds.downscale(u_era5=5.0, v_era5=0.0, hour_utc=3)
    log.info(f"Daytime westerly — mean speed: {np.sqrt(u_test**2+v_test**2).mean():.2f} m/s")

    u_night, v_night = ds.downscale(u_era5=2.0, v_era5=0.0, hour_utc=2, dt_slope=4.0)
    log.info(f"Nocturnal katabatic — mean speed: {np.sqrt(u_night**2+v_night**2).mean():.2f} m/s")

    try:
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        axes[0].streamplot(
            ds.x_grid, ds.y_grid, u_test, v_test, density=1.5,
            color=np.sqrt(u_test**2+v_test**2), cmap="viridis"
        )
        axes[0].set_title("Daytime Wind (ERA5 + terrain correction)")
        axes[1].streamplot(
            ds.x_grid, ds.y_grid, u_night, v_night, density=1.5,
            color=np.sqrt(u_night**2+v_night**2), cmap="plasma"
        )
        axes[1].set_title("Nocturnal Katabatic Wind")
        plt.tight_layout()
        plt.savefig("results/figures/wind_downscaling_test.png", dpi=150)
        log.info("Test figure saved to results/figures/wind_downscaling_test.png")
    except Exception:
        log.info("matplotlib not available for test plot.")
