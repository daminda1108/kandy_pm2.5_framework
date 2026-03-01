"""
topo_features.py — Compute topography-aware atmospheric features for Kandy PM2.5 modeling.

These features are the KEY NOVELTY of the Tier 1 model, encoding valley-specific
atmospheric physics as engineered features that any ML model can use.

Features computed:
  - Valley Ventilation Coefficient (VVC)   — ventilation potential of valley
  - Katabatic Flow Proxy v1/v2 (KFP)      — nighttime drainage wind strength
  - Bulk Richardson Number (Ri)            — boundary-layer thermal stability index
  - Thermal Inversion Index (TII)          — temperature inversion strength
  - Diurnal Stability Cycle (DSC)          — time-of-day inversion state
  - Rain Washout Potential (RWP)           — wet deposition efficiency
  - Cloud Gap Index (CGI)                  — satellite data availability indicator
  - Terrain Blocking Index (TBI)           — radial terrain blocking of wind flow
  - Valley Wind Decomposition              — along/cross-valley components + revised VVC

Reference: Whiteman (2000) Mountain Meteorology, OUP
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    KANDY_VALLEY_DEPTH_M, INVERSION_PRESSURE_LEVEL,
    KATABATIC_TEMP_LAPSE, T0_K, LOG_FORMAT, LOG_DATEFMT,
    DEM_RAW_DIR,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("topo_features")


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 1: Valley Ventilation Coefficient (VVC)
# ─────────────────────────────────────────────────────────────────────────────

def compute_vvc(
    wind_speed_ms: pd.Series,
    blh_m: pd.Series,
    valley_depth_m: float = KANDY_VALLEY_DEPTH_M,
    eps: float = 1.0,
) -> pd.Series:
    """
    Valley Ventilation Coefficient = (wind_speed × BLH) / valley_depth

    A dimensionless ratio of the atmosphere's flushing capacity vs. valley volume.
      - VVC → 0 : stagnant, poorly ventilated (pollution accumulates)
      - VVC → 1+ : well-ventilated (pollution disperses)

    Args:
        wind_speed_ms : 10m wind speed (m/s)
        blh_m         : Planetary Boundary Layer Height (m)
        valley_depth_m: Reference depth of Kandy bowl (m)
        eps           : Small value to avoid division by zero

    Returns:
        pd.Series: dimensionless VVC values
    """
    vvc = (wind_speed_ms * blh_m) / (valley_depth_m + eps)
    vvc.name = "vvc"
    log.debug(f"VVC: mean={vvc.mean():.3f}, min={vvc.min():.3f}, max={vvc.max():.3f}")
    return vvc.clip(lower=0.0)


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 2: Katabatic Flow Proxy (KFP)
# ─────────────────────────────────────────────────────────────────────────────

def compute_kfp(
    skin_temp_k: pd.Series,
    air_temp_2m_k: pd.Series,
    mean_slope_deg: float,
    cloud_fraction: pd.Series,
) -> pd.Series:
    """
    Katabatic Flow Proxy — estimates nocturnal drainage wind strength.

    Based on Whiteman (2000): k ~ ΔT × sin(α) × (1 - n)
    where ΔT = skin cooling below air, α = mean valley slope, n = cloud cover.

    Physical meaning:
      - Large skin cooling (ΔT > 0) → strong radiative cooling → strong drainage
      - Steep slopes (large sin α) → faster gravity-driven flow
      - Clear skies (n → 0) → more radiative cooling → stronger drainage
      - Higher KFP = more katabatic flow = more nocturnal valley PM2.5 pooling

    Args:
        skin_temp_k   : Land surface (skin) temperature (K)
        air_temp_2m_k : 2m air temperature (K)
        mean_slope_deg: Mean slope of valley walls (degrees), a static constant
        cloud_fraction: Sky fraction covered by cloud (0–1)

    Returns:
        pd.Series: KFP values (K, proportional to drainage wind intensity)
    """
    slope_sin = np.sin(np.radians(mean_slope_deg))
    dt = (air_temp_2m_k - skin_temp_k).clip(lower=0.0)          # Only cooling events
    clear_sky = (1.0 - cloud_fraction.clip(0.0, 1.0)).clip(lower=0.0)
    kfp = dt * slope_sin * clear_sky
    kfp.name = "kfp"
    log.debug(f"KFP: mean={kfp.mean():.3f}, max={kfp.max():.3f}")
    return kfp.clip(lower=0.0)


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 3: Thermal Inversion Index (TII)
# ─────────────────────────────────────────────────────────────────────────────

def compute_tii(
    temp_925hpa_k: pd.Series,
    temp_surface_k: pd.Series,
) -> pd.Series:
    """
    Thermal Inversion Index = T_925hPa − T_surface

    In normal atmospheric conditions, temperature decreases with height (TII < 0).
    During a temperature inversion, warm air sits above cool valley-floor air (TII > 0).
    Inversions act as a physical lid, trapping PM2.5 near the surface.

    Args:
        temp_925hpa_k  : Temperature at 925 hPa pressure level (K)  [from ERA5 pressure levels]
        temp_surface_k : 2m or skin surface temperature (K)          [from ERA5 single levels]

    Returns:
        pd.Series: TII (K) — positive values indicate inversions
    """
    tii = temp_925hpa_k - temp_surface_k
    tii.name = "tii"
    log.debug(f"TII: mean={tii.mean():.3f}, inversions: {(tii > 0).sum()} / {len(tii)}")
    return tii


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 4: Diurnal Stability Cycle (DSC)
# ─────────────────────────────────────────────────────────────────────────────

def compute_dsc(
    ssrd_current: pd.Series,
    hour_of_day: pd.Series,
    ssrd_daily_max: pd.Series | None = None,
) -> pd.Series:
    """
    Diurnal Stability Cycle — normalised solar heating relative to daily peak.

    Tracks the daily progression of atmospheric stability:
      - DSC ~ 0 at night: stable, inversion present, PM2.5 accumulates
      - DSC ~ 1 at solar noon: unstable, well-mixed, PM2.5 disperses

    Args:
        ssrd_current  : Instantaneous surface solar radiation downwards (J/m²)
        hour_of_day   : Hour of day (0-23) — used for night detection
        ssrd_daily_max: Optional — daily maximum SSRD. If None, computed from data.

    Returns:
        pd.Series: DSC (0 to 1)
    """
    if ssrd_daily_max is None:
        ssrd_daily_max = ssrd_current.rolling(window=24, center=True, min_periods=1).max()

    # Avoid division by zero on completely cloudy days
    dsc = (ssrd_current / ssrd_daily_max.clip(lower=1.0)).clip(0.0, 1.0)
    # Force DSC = 0 at night (hours where sun is below horizon in Sri Lanka ~ 18:00-06:00 local)
    night_mask = (hour_of_day < 6) | (hour_of_day >= 18)
    dsc[night_mask] = 0.0
    dsc.name = "dsc"
    return dsc


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 5: Rain Washout Potential (RWP)
# ─────────────────────────────────────────────────────────────────────────────

def compute_rwp(
    total_precipitation_m: pd.Series,
    wind_speed_ms: pd.Series,
) -> pd.Series:
    """
    Rain Washout Potential — combined wet deposition efficiency.

    High RWP means heavy rain + wind → effective wet removal of PM2.5.
    RWP is highest during monsoonal periods (May-Sept).

    Args:
        total_precipitation_m : ERA5 total precipitation (m per hour)
        wind_speed_ms         : 10m wind speed (m/s)

    Returns:
        pd.Series: RWP (dimensionless)
    """
    # Convert precip m → mm
    precip_mm = (total_precipitation_m * 1000.0).clip(lower=0.0)
    rwp = np.log1p(precip_mm) * np.log1p(wind_speed_ms)
    rwp.name = "rwp"
    return rwp.clip(lower=0.0)


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 6: Cloud Gap Index (CGI) — Tier 1 Reliability Indicator
# ─────────────────────────────────────────────────────────────────────────────

def compute_cloud_gap_index(
    aod_modis: pd.Series,
    aod_tropomi: pd.Series | None = None,
) -> pd.Series:
    """
    Cloud Gap Index — fraction of days where satellite AOD is unavailable (cloud-masked).

    This feature serves dual purpose:
      1. As an ML feature: model can learn that PM2.5 estimates are uncertain on these days
      2. As a QC flag: identifies days where PINN training signal (Tier 1 output) is
         systematically biased by cloud gaps (especially during SW Monsoon, May-Sept)

    Critical for interpreting Tier 1→Tier 2 error propagation (Section 2.9 of design doc).

    CGI = 0 : AOD valid from ≥1 source (reliable Tier 1 estimate)
    CGI = 1 : AOD unavailable from ALL sources (estimate is extrapolated — high uncertainty)

    Args:
        aod_modis  : Daily MODIS MAIAC AOD (NaN = cloud-flagged)
        aod_tropomi: Daily TROPOMI AER_AI (NaN = unavailable) — backup source
                     TROPOMI can penetrate thin cloud

    Returns:
        pd.Series: CGI (0 = data available, 1 = all sources cloud-gapped)
    """
    modis_valid   = aod_modis.notna().astype(float)
    tropomi_valid = aod_tropomi.notna().astype(float) if aod_tropomi is not None \
                    else pd.Series(0.0, index=aod_modis.index)

    # CGI = 1 only if BOTH MODIS and TROPOMI are missing
    any_valid = (modis_valid + tropomi_valid).clip(upper=1.0)
    cgi = 1.0 - any_valid
    cgi.name = "cloud_gap_index"

    n_gap = cgi.sum()
    pct_gap = 100 * cgi.mean()
    log.info(f"Cloud Gap Index: {n_gap:.0f} fully-gapped days ({pct_gap:.1f}%)")
    if pct_gap > 40:
        log.warning(
            f"Cloud gap rate is {pct_gap:.0f}% — likely SW Monsoon data in range.\n"
            "  Tier 1 PM2.5 estimates will be biased low for these days.\n"
            "  Tier 2 PINN will inherit this bias. See design doc Section 2.9."
        )
    return cgi


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 9: Bulk Richardson Number (Ri) + Stability Flag
# ─────────────────────────────────────────────────────────────────────────────

def compute_richardson_number(
    t2m: pd.Series,
    t925: pd.Series,
    wind_speed: pd.Series,
    delta_z: float = 250.0,
    g: float = 9.81,
    eps: float = 1e-3,
) -> tuple[pd.Series, pd.Series]:
    """
    Bulk Richardson Number — thermal stability of the sub-inversion layer.

    Ri = (g / T_mean) × (ΔT / Δz) × Δz² / u²
       = g × ΔT × Δz / (T_mean × u²)

    where:
        ΔT     = T_925hPa − T_2m  (positive = stable/inversion, negative = unstable)
        Δz     = 250 m (925 hPa ≈ 800 m ASL − valley floor 550 m ASL)
        u      = 10 m wind speed (m/s) — proxy for vertical wind shear
        T_mean = arithmetic mean of T_2m and T_925hPa (K)

    Stability regimes:
        Ri < 0    : Convectively unstable (strong surface heating, turbulent mixing)
        0 ≤ Ri < 0.25: Mechanically turbulent (wind shear dominant, some mixing)
        Ri ≥ 0.25: Stable (laminar flow — PM2.5 trapping likely)
        Ri ≥ 1    : Strongly stable (complete turbulence suppression)

    The critical value Ri = 0.25 (Richardson criterion) is the classical threshold
    above which turbulence cannot be sustained by mechanical mixing alone.

    Args:
        t2m       : 2 m air temperature (K)
        t925      : Temperature at 925 hPa (K)  [ERA5 pressure-level variable]
        wind_speed: 10 m wind speed (m/s)
        delta_z   : Layer thickness (m); 250 m for 925 hPa above Kandy floor
        g         : Gravitational acceleration (m/s²)
        eps       : Floor on u² to avoid division by zero in calm conditions

    Returns:
        (richardson_number, ri_stable_flag)
        richardson_number : pd.Series — Ri clipped to [−20, 20]
        ri_stable_flag    : pd.Series — 1.0 where Ri > 0.25, else 0.0
    """
    t_mean = 0.5 * (t2m + t925)
    delta_t = t925 - t2m          # positive = warmer air aloft = temperature inversion
    u2 = (wind_speed ** 2).clip(lower=eps ** 2)

    ri = (g * delta_t * delta_z) / (t_mean * u2)
    ri = ri.clip(-20.0, 20.0)
    ri.name = "richardson_number"

    ri_flag = (ri > 0.25).astype(float)
    ri_flag.name = "ri_stable_flag"

    n_stable = int(ri_flag.sum())
    log.info(
        f"Richardson Number: mean={ri.mean():.3f}, "
        f"stable (Ri>0.25): {n_stable}/{len(ri)} days ({100*n_stable/len(ri):.1f}%)"
    )
    return ri, ri_flag


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 10: KFP_v2 — Stability-Gated Katabatic Flow Proxy
# ─────────────────────────────────────────────────────────────────────────────

def compute_kfp_v2(
    richardson_number: pd.Series,
    cloud_fraction: pd.Series,
) -> pd.Series:
    """
    KFP_v2 — stability-gated katabatic flow proxy.

    Extends KFP_v1 (compute_kfp) by replacing the ΔT × sin(α) driving term
    with the Bulk Richardson Number excess above the critical threshold.
    This directly encodes whether the atmospheric layer is stable enough for
    drainage winds to persist rather than being eroded by mechanical turbulence.

    Formula: kfp_v2 = (Ri − 0.25).clip(0) × sin(15°) × (1 − cloud_fraction).clip(0)

    Physical meaning:
        - Only activates when Ri > 0.25 (laminar/stable layer sustains drainage)
        - sin(15°) ≈ 0.259 scales by mean valley wall slope (same as KFP_v1)
        - (1 − n) factor: clear skies amplify radiative cooling → stronger drainage
        - kfp_v2 = 0 in convectively unstable or turbulent regimes (Ri ≤ 0.25)
        - Larger kfp_v2 → stronger stable-layer katabatic drainage → more PM2.5 pooling

    The original kfp (kfp_v1) is retained in the dataset for SHAP comparison.

    Args:
        richardson_number : Bulk Richardson Number (from compute_richardson_number)
        cloud_fraction    : Sky fraction covered by cloud (0–1)

    Returns:
        pd.Series: kfp_v2 values ≥ 0
    """
    slope_sin = np.sin(np.radians(15.0))
    stable_excess = (richardson_number - 0.25).clip(lower=0.0)
    clear_sky = (1.0 - cloud_fraction.clip(0.0, 1.0)).clip(lower=0.0)
    kfp_v2 = stable_excess * slope_sin * clear_sky
    kfp_v2.name = "kfp_v2"
    log.debug(f"KFP_v2: mean={kfp_v2.mean():.4f}, max={kfp_v2.max():.4f}")
    return kfp_v2


# ─────────────────────────────────────────────────────────────────────────────
# Valley axis constant (used by wind decomposition below)
# ─────────────────────────────────────────────────────────────────────────────

_VALLEY_AXIS_DEG = 45.0  # NE-SW valley axis bearing (°N)

# Module-level cache: precomputed once per Python session, O(1) lookup per day
_TBI_LOOKUP_CACHE: np.ndarray | None = None


def _precompute_tbi_lookup(
    dem_path: Path,
    valley_centre_latlon: tuple[float, float] = (7.2906, 80.6337),
    valley_floor_elev_m: float = 550.0,
    blocking_radius_km: float = 30.0,
    n_directions: int = 360,
    n_scan_points: int = 120,
) -> np.ndarray:
    """
    Precompute terrain blocking lookup table from real SRTM DEM.

    Scans n_directions wind directions at blocking_radius_km radius.
    For each direction the maximum terrain elevation along the radial
    profile is found and normalised against the Hantana-height reference
    (360 m above valley floor = 910 m − 550 m ASL).

    30 km radius captures: Hantana SW ~7 km, S valley wall ~5-7 km,
    Knuckles NE ~22-24 km, Deltota SW ~20 km, Gomaragala SE ~15 km —
    covering all sub-grid terrain that ERA5 smooths over.

    Returns:
        np.ndarray of shape (n_directions,) — TBI 0–1 per integer degree.
        Precomputed once at import; O(1) lookup per day at runtime.
    """
    import rasterio

    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(float)
        transform = src.transform
        nodata = src.nodata

    if nodata is not None:
        dem[dem == nodata] = 0.0

    lat0, lon0 = valley_centre_latlon
    # Normalisation: Hantana crest (910 m) − valley floor (550 m) = 360 m.
    # Any terrain > 360 m above valley floor clips to 1.0 (e.g. Knuckles).
    reference_height_m = 360.0

    lookup = np.zeros(n_directions, dtype=float)

    for wdir_int in range(n_directions):
        wdir_rad = np.radians(float(wdir_int))
        dx = np.sin(wdir_rad)    # eastward fraction of unit step
        dy = np.cos(wdir_rad)    # northward fraction of unit step

        max_blocking = 0.0
        for step_km in np.linspace(0.5, blocking_radius_km, n_scan_points):
            lat = lat0 + (step_km * dy) / 111.0
            lon = lon0 + (step_km * dx) / (111.0 * np.cos(np.radians(lat0)))
            try:
                col_f, row_f = ~transform * (lon, lat)
                row_i, col_i = int(row_f), int(col_f)
                if 0 <= row_i < dem.shape[0] and 0 <= col_i < dem.shape[1]:
                    elev = dem[row_i, col_i]
                    blocking = float(np.clip(
                        (elev - valley_floor_elev_m) / reference_height_m,
                        0.0, 1.0,
                    ))
                    if blocking > max_blocking:
                        max_blocking = blocking
            except Exception:
                continue

        lookup[wdir_int] = max_blocking

    log.info(
        f"TBI lookup precomputed from {dem_path.name}: "
        f"mean={lookup.mean():.3f}, min={lookup.min():.3f}, max={lookup.max():.3f}"
    )
    return lookup


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 7: Terrain Blocking Index (TBI)
# ─────────────────────────────────────────────────────────────────────────────

def compute_terrain_blocking_index(
    wind_dir_deg: pd.Series,
    dem_path: Path | None = None,
    blocking_radius_km: float = 30.0,
    valley_floor_m: float = 550.0,
) -> pd.Series:
    """
    Terrain Blocking Index (TBI) — normalised maximum terrain elevation along
    the upwind radial from Kandy valley centre (7.2906°N, 80.6337°E).

    Uses a precomputed 360-entry lookup table derived from the real SRTM 30 m
    DEM (srtm_elevation_30m.tif).  The lookup is computed once per Python
    session (cached in _TBI_LOOKUP_CACHE) and is O(1) per day thereafter.

    TBI = clip((max_terrain_elevation − valley_floor) / 360, 0, 1)
    where 360 m = Hantana crest (910 m) − valley floor (550 m ASL).
    Terrain higher than Hantana (e.g. Knuckles 1863 m) clips to 1.0.

    30 km scan radius captures all terrain features ERA5 (~28 km grid) masks:
      - S/SSW valley wall: ~5-7 km, ~1000-1260 m ASL   (closest blocking)
      - NE Knuckles massif: ~22-24 km, ~1540-1860 m ASL (major regional block)
      - 225° SW: distant peak ~28 km, ~1007 m ASL       (note: not Hantana itself)

    Args:
        wind_dir_deg      : ERA5 10 m wind direction (degrees from north, 0–360).
                            Convention: direction FROM which wind blows.
        dem_path          : Path to SRTM elevation GeoTIFF. If None, resolved
                            from DEM_RAW_DIR config constant.
        blocking_radius_km: Radial scan distance passed to _precompute_tbi_lookup.
                            Only used on first call (cache miss).
        valley_floor_m    : Valley floor reference elevation (m ASL). Only used
                            on first call (cache miss).

    Returns:
        pd.Series named "terrain_blocking_idx", values 0–1.
    """
    global _TBI_LOOKUP_CACHE

    if _TBI_LOOKUP_CACHE is None:
        if dem_path is None:
            candidates = sorted(DEM_RAW_DIR.glob("srtm_elevation*.tif"))
            if not candidates:
                candidates = sorted(DEM_RAW_DIR.glob("*.tif"))
            if not candidates:
                raise FileNotFoundError(
                    f"No SRTM elevation GeoTIFF found in {DEM_RAW_DIR}. "
                    "Expected srtm_elevation_30m.tif."
                )
            dem_path = candidates[0]
            log.info(f"TBI: using DEM {dem_path.name}")

        _TBI_LOOKUP_CACHE = _precompute_tbi_lookup(
            dem_path,
            valley_floor_elev_m=valley_floor_m,
            blocking_radius_km=blocking_radius_km,
        )

    wdir_int = wind_dir_deg.round().astype(int) % 360
    tbi = wdir_int.map(lambda d: float(_TBI_LOOKUP_CACHE[d]))
    tbi.name = "terrain_blocking_idx"
    log.info(f"TBI: mean={tbi.mean():.3f}, max={tbi.max():.3f}, min={tbi.min():.3f}")
    return tbi


def _test_tbi() -> None:
    """
    Diagnostic test: print real-DEM TBI values for four canonical directions.

    Expected physics (from SRTM 30 m scan, 30 km radius):
      SW 225°: high (S/SSW valley wall + distant SW peak)   → > 0.80
      NE  45°: high (Knuckles massif 1540-1860 m at 22 km) → > 0.50
      SE 135°: moderate-high (SE ridges)                   → informational
      N    0°: low  (open Mahaweli corridor)               → < 0.50
    """
    test_dirs = pd.Series([225.0, 45.0, 135.0, 0.0])
    labels    = ["SW/225° (Hantana dir)", "NE/45° (Knuckles)", "SE/135° (Gomaragala)", "N/0° (open)"]

    result = compute_terrain_blocking_index(test_dirs)

    print("TBI diagnostic (real SRTM DEM):")
    for label, val in zip(labels, result):
        print(f"  {label}: TBI = {val:.3f}")

    tbi_sw = result.iloc[0]
    tbi_ne = result.iloc[1]
    assert tbi_sw >= 0.80, f"SW TBI unexpectedly low: {tbi_sw:.3f} (expected >= 0.80)"
    assert tbi_ne >= 0.50, f"NE TBI unexpectedly low: {tbi_ne:.3f} (expected >= 0.50)"
    print("Assertions PASSED: SW >= 0.80, NE >= 0.50")


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 8: Terrain-Relative Valley Wind Decomposition
# ─────────────────────────────────────────────────────────────────────────────

def compute_valley_wind_decomposition(
    u10: pd.Series,
    v10: pd.Series,
    blh_m: pd.Series | None = None,
    valley_axis_deg: float = _VALLEY_AXIS_DEG,
    eps: float = 1e-3,
) -> pd.DataFrame:
    """
    Decompose ERA5 10 m wind into along-valley and cross-valley components.

    Valley axis: 45° NE–SW (Kandy bowl alignment from DEM analysis).
    Projection uses standard (East, North) vector components:
      along-valley unit vector  = (sin 45°, cos 45°) = (√2/2, √2/2)  → toward NE
      cross-valley unit vector  = (cos 45°, −sin 45°)                 → toward SE

    Features returned:
        wind_along        : Signed along-valley wind (m/s); +ve = toward NE
        wind_cross        : Signed cross-valley wind (m/s); +ve = toward SE
        valley_flow_ratio : |wind_along| / total_wind_speed (0–1)
        vvc_revised       : VVC recomputed with |wind_along| instead of total
                            wind speed — only along-valley winds flush the valley
                            (only present when blh_m is supplied)

    Original VVC (using total wind speed) is retained for SHAP comparison.

    Args:
        u10            : ERA5 10 m eastward wind (m/s)
        v10            : ERA5 10 m northward wind (m/s)
        blh_m          : Boundary layer height (m); if supplied, vvc_revised
                         is computed and included in the output
        valley_axis_deg: Valley axis bearing in degrees from north
        eps            : Small value to avoid division-by-zero in ratio

    Returns:
        pd.DataFrame with columns [wind_along, wind_cross, valley_flow_ratio]
        and optionally vvc_revised when blh_m is provided.
    """
    ax = np.radians(valley_axis_deg)

    # Project onto along-valley unit vector (toward NE)
    wind_along = u10 * np.sin(ax) + v10 * np.cos(ax)
    wind_along.name = "wind_along"

    # Cross-valley component (perpendicular, toward SE = bearing 135°)
    wind_cross = u10 * np.cos(ax) - v10 * np.sin(ax)
    wind_cross.name = "wind_cross"

    wind_speed_total = np.sqrt(u10 ** 2 + v10 ** 2)
    valley_flow_ratio = wind_along.abs() / (wind_speed_total + eps)
    valley_flow_ratio = valley_flow_ratio.clip(0.0, 1.0)
    valley_flow_ratio.name = "valley_flow_ratio"

    result = pd.DataFrame({
        "wind_along": wind_along,
        "wind_cross": wind_cross,
        "valley_flow_ratio": valley_flow_ratio,
    })

    if blh_m is not None:
        result["vvc_revised"] = compute_vvc(wind_along.abs(), blh_m)

    log.info(
        f"Valley wind decomp: along mean={wind_along.mean():.2f} m/s, "
        f"cross mean={wind_cross.mean():.2f} m/s, "
        f"ratio mean={valley_flow_ratio.mean():.2f}"
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MASTER FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def compute_all_topo_features(df: pd.DataFrame, mean_slope_deg: float = 15.0) -> pd.DataFrame:
    """
    Compute all topography-aware atmospheric features and add to dataframe.

    Expected input columns:
        wind_speed    : 10 m wind speed (m/s) — computed from u10, v10
        blh           : Boundary layer height (m)
        t2m           : 2m air temperature (K)
        d2m           : 2m dewpoint temp (K)  [used for cloud fraction estimate]
        sp            : Surface pressure (Pa)
        ssr           : Surface solar radiation (J/m²)
        skin_temp     : Skin temperature (K)
        t925          : Temperature at 925 hPa (K)
        tp            : Total precipitation (m/hr)
        hour          : Hour of day (0–23)
        cloud_fraction: Cloud fraction (0–1)  [from ERA5 total_cloud_cover or estimated]

    Args:
        df             : DataFrame with the above columns
        mean_slope_deg : Average slope of surrounding valley walls (degrees)

    Returns:
        DataFrame with additional feature columns appended
    """
    result = df.copy()

    # VVC — Valley Ventilation Coefficient
    result["vvc"] = compute_vvc(
        wind_speed_ms=result["wind_speed"],
        blh_m=result["blh"],
    )

    # KFP — Katabatic Flow Proxy
    if "skin_temp" in result.columns:
        result["kfp"] = compute_kfp(
            skin_temp_k=result["skin_temp"],
            air_temp_2m_k=result["t2m"],
            mean_slope_deg=mean_slope_deg,
            cloud_fraction=result.get("cloud_fraction", pd.Series(0.5, index=result.index)),
        )
    else:
        log.warning("skin_temp not available — KFP will be set to 0.")
        result["kfp"] = 0.0

    # TII — Thermal Inversion Index
    if "t925" in result.columns:
        result["tii"] = compute_tii(
            temp_925hpa_k=result["t925"],
            temp_surface_k=result["t2m"],
        )
    else:
        log.warning("t925 not available — TII will not be computed.")

    # Richardson Number + Stability Flag (needs t925 + wind_speed)
    if "t925" in result.columns and "wind_speed" in result.columns:
        result["richardson_number"], result["ri_stable_flag"] = compute_richardson_number(
            t2m=result["t2m"],
            t925=result["t925"],
            wind_speed=result["wind_speed"],
        )
        # KFP_v2 (stability-gated katabatic proxy)
        cf = result.get("cloud_fraction", pd.Series(0.5, index=result.index))
        result["kfp_v2"] = compute_kfp_v2(result["richardson_number"], cf)
    else:
        log.warning("t925 or wind_speed not available — Richardson Number and KFP_v2 skipped.")

    # DSC — Diurnal Stability Cycle
    result["dsc"] = compute_dsc(
        ssrd_current=result["ssr"],
        hour_of_day=result["hour"],
    )

    # RWP — Rain Washout Potential
    result["rwp"] = compute_rwp(
        total_precipitation_m=result["tp"],
        wind_speed_ms=result["wind_speed"],
    )

    # TBI — Terrain Blocking Index
    if "wind_dir" in result.columns:
        result["tbi"] = compute_terrain_blocking_index(result["wind_dir"])
    else:
        log.warning("wind_dir not available — TBI skipped.")

    # Valley wind decomposition + revised VVC
    if "u10" in result.columns and "v10" in result.columns:
        blh = result["blh"] if "blh" in result.columns else None
        decomp = compute_valley_wind_decomposition(result["u10"], result["v10"], blh_m=blh)
        for col in decomp.columns:
            result[col] = decomp[col]
    else:
        log.warning("u10/v10 not available — valley wind decomposition skipped.")

    new_cols = [
        c for c in [
            "vvc", "kfp", "kfp_v2", "tii", "dsc", "rwp",
            "richardson_number", "ri_stable_flag",
            "tbi", "wind_along", "wind_cross", "valley_flow_ratio", "vvc_revised",
        ]
        if c in result.columns
    ]
    log.info(f"Topography-aware features computed: {new_cols}")
    return result


if __name__ == "__main__":
    # TBI unit test
    _test_tbi()

    # Quick sanity-check with synthetic data
    import pandas as pd
    np.random.seed(42)
    n = 100
    dummy = pd.DataFrame({
        "wind_speed":     np.random.uniform(0, 5, n),
        "blh":            np.random.uniform(100, 2000, n),
        "t2m":            np.random.uniform(295, 308, n),
        "skin_temp":      np.random.uniform(290, 310, n),
        "t925":           np.random.uniform(290, 305, n),
        "ssr":            np.random.uniform(0, 2e6, n),
        "tp":             np.random.uniform(0, 0.005, n),
        "hour":           np.tile(np.arange(24), n // 24 + 1)[:n],
        "cloud_fraction": np.random.uniform(0, 1, n),
    })
    out = compute_all_topo_features(dummy)
    print("Topo features preview:")
    print(out[["vvc", "kfp", "tii", "dsc", "rwp"]].describe())
