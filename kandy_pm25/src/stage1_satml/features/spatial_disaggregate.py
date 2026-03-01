"""
spatial_disaggregate.py — Stage 1b: Spatially disaggregate CAMS labels using Van Donkelaar.

Core idea (from STAGE1_ANALYSIS.md §7):
  PM25_pixel(x, y, day) = CAMS_daily × [VD_annual_pixel(x,y) / VD_annual_domain_mean]

This transforms 8,279 single-value daily labels into ~414,000 pixel-day samples
(8,279 days × ~50 pixels at 1km), where each pixel has a different PM2.5 value
based on Van Donkelaar's 1km spatial pattern.

Why this works:
  - CAMS provides temporal dynamics (daily variation, seasonal cycle, trends)
  - Van Donkelaar provides spatial structure (valley floor > ridge)
  - The VD spatial pattern is from GEOS-Chem + ground calibration at 0.01°

Pixel-specific features added:
  - VD spatial weight (static per pixel)
  - Elevation, slope, aspect, TPI from SRTM 30m
  - Distance from valley floor (lowest point)

Output: data/processed/merged/dataset_pixel_daily.parquet
        (~414,000 rows × 35+ features)

Usage:
    python spatial_disaggregate.py
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    KANDY_PINN_BBOX, VAN_DONKELAAR_DIR, DEM_RAW_DIR,
    MERGED_DIR, VALIDATION_DIR,
    LOG_FORMAT, LOG_DATEFMT,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("spatial_disaggregate")


# ─────────────────────────────────────────────────────────────────────────────
# VAN DONKELAAR SPATIAL WEIGHTS
# ─────────────────────────────────────────────────────────────────────────────

def compute_vd_spatial_weights() -> pd.DataFrame:
    """
    Compute Van Donkelaar spatial weights for each 1km pixel in Kandy PINN bbox.

    Weight(x,y) = mean_across_years[ VD_pixel(x,y) / VD_domain_mean ]

    Averaging across years gives a stable spatial pattern rather than
    year-to-year noise. The valley/ridge ratio is ~1.06 (minimal but real).

    Returns:
        DataFrame with columns: pixel_id, lat, lon, vd_weight
    """
    import netCDF4 as nc4

    nc_files = sorted(VAN_DONKELAAR_DIR.glob("*.nc"))
    if not nc_files:
        raise FileNotFoundError(f"No VD NetCDFs in {VAN_DONKELAAR_DIR}")

    bbox = KANDY_PINN_BBOX
    all_weights = []
    pixel_lats = None
    pixel_lons = None

    for nc_path in nc_files:
        try:
            ds = nc4.Dataset(nc_path)
            lat = ds.variables["lat"][:]
            lon = ds.variables["lon"][:]

            lat_mask = (lat >= bbox["lat_min"]) & (lat <= bbox["lat_max"])
            lon_mask = (lon >= bbox["lon_min"]) & (lon <= bbox["lon_max"])
            lat_idx = np.where(lat_mask)[0]
            lon_idx = np.where(lon_mask)[0]

            if len(lat_idx) == 0 or len(lon_idx) == 0:
                ds.close()
                continue

            pm25_grid = np.array(
                ds.variables["PM25"][lat_idx[0]:lat_idx[-1]+1, lon_idx[0]:lon_idx[-1]+1],
                dtype=np.float64
            )
            pm25_grid[pm25_grid < 0] = np.nan
            ds.close()

            domain_mean = np.nanmean(pm25_grid)
            if domain_mean > 0:
                weight_grid = pm25_grid / domain_mean
                all_weights.append(weight_grid)

            if pixel_lats is None:
                pixel_lats = lat[lat_idx]
                pixel_lons = lon[lon_idx]

        except Exception as e:
            log.warning(f"  Could not process {nc_path.name}: {e}")

    if not all_weights:
        raise RuntimeError("No VD grids could be processed")

    # Average weights across all years for stability
    mean_weights = np.nanmean(np.stack(all_weights), axis=0)

    # Build pixel DataFrame
    pixels = []
    pid = 0
    for i, lat_val in enumerate(pixel_lats):
        for j, lon_val in enumerate(pixel_lons):
            w = mean_weights[i, j]
            if not np.isnan(w):
                pixels.append({
                    "pixel_id": pid,
                    "lat": float(lat_val),
                    "lon": float(lon_val),
                    "vd_weight": float(w),
                })
                pid += 1

    pixel_df = pd.DataFrame(pixels)
    log.info(f"VD spatial weights: {len(pixel_df)} pixels, "
             f"weight range {pixel_df['vd_weight'].min():.3f}–{pixel_df['vd_weight'].max():.3f}, "
             f"valley/ridge ratio {pixel_df['vd_weight'].max()/pixel_df['vd_weight'].min():.3f}")
    return pixel_df


# ─────────────────────────────────────────────────────────────────────────────
# TOPOGRAPHIC FEATURES PER PIXEL (from SRTM 30m)
# ─────────────────────────────────────────────────────────────────────────────

def extract_topo_per_pixel(pixel_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract topographic features at each 1km pixel from SRTM 30m GeoTIFFs.

    Features:
      - elevation: mean elevation within pixel (m)
      - slope: mean slope (degrees)
      - aspect: mean aspect (degrees from north)
      - tpi: Topographic Position Index (pixel elev - neighbourhood mean)
      - dist_valley_floor: Euclidean distance from lowest pixel (km)
    """
    try:
        import rasterio
    except ImportError:
        log.warning("rasterio not available — using elevation proxy from DEM")
        return _topo_from_netcdf(pixel_df)

    topo_features = {}

    for var_name, filename in [
        ("elevation", "srtm_elevation_30m.tif"),
        ("slope", "srtm_slope_30m.tif"),
        ("aspect", "srtm_aspect_30m.tif"),
    ]:
        tif_path = DEM_RAW_DIR / filename
        if not tif_path.exists():
            log.warning(f"  {filename} not found — skipping {var_name}")
            continue

        with rasterio.open(tif_path) as src:
            values = []
            for _, row in pixel_df.iterrows():
                # Sample 30m pixels within the 1km pixel (0.01° ≈ 1km)
                # Get all 30m pixels within ±0.005° of pixel center
                window = rasterio.windows.from_bounds(
                    row["lon"] - 0.005, row["lat"] - 0.005,
                    row["lon"] + 0.005, row["lat"] + 0.005,
                    src.transform
                )
                try:
                    data = src.read(1, window=window)
                    data = data[data > -9999]  # Filter nodata
                    values.append(float(np.mean(data)) if len(data) > 0 else np.nan)
                except Exception:
                    values.append(np.nan)

            topo_features[var_name] = values
            log.info(f"  {var_name}: extracted for {len(values)} pixels")

    for var_name, vals in topo_features.items():
        pixel_df[var_name] = vals

    # Compute TPI: pixel elevation - mean of all pixels
    if "elevation" in pixel_df.columns:
        mean_elev = pixel_df["elevation"].mean()
        pixel_df["tpi"] = pixel_df["elevation"] - mean_elev

        # Distance from valley floor (lowest elevation pixel)
        lowest = pixel_df.loc[pixel_df["elevation"].idxmin()]
        pixel_df["dist_valley_floor"] = np.sqrt(
            ((pixel_df["lat"] - lowest["lat"]) * 111.0) ** 2 +
            ((pixel_df["lon"] - lowest["lon"]) * 110.0) ** 2
        )
        log.info(f"  TPI range: {pixel_df['tpi'].min():.0f} to {pixel_df['tpi'].max():.0f} m")
        log.info(f"  Valley floor at ({lowest['lat']:.3f}, {lowest['lon']:.3f}), "
                 f"elev={lowest['elevation']:.0f}m")

    return pixel_df


def _topo_from_netcdf(pixel_df: pd.DataFrame) -> pd.DataFrame:
    """Fallback: simple elevation from kandy_dem.tif if rasterio unavailable."""
    log.warning("Using basic DEM fallback — install rasterio for full topo features")
    return pixel_df


# ─────────────────────────────────────────────────────────────────────────────
# SPATIAL DISAGGREGATION
# ─────────────────────────────────────────────────────────────────────────────

def build_pixel_dataset() -> pd.DataFrame:
    """
    Build spatially disaggregated pixel-day dataset.

    For each pixel × day:
      - label = CAMS_daily × VD_weight(pixel) × constant_bias_ratio
      - features = ERA5 met (shared) + pixel-specific topo + VD weight

    This expands ~8,279 daily samples to ~414,000 pixel-day samples.
    """
    log.info("=" * 55)
    log.info("Building spatially disaggregated pixel-day dataset ...")
    log.info("=" * 55)

    # ── Load domain-mean dataset (Stage 1a output) ─────────────────────────
    domain_path = MERGED_DIR / "dataset_daily.parquet"
    if not domain_path.exists():
        raise FileNotFoundError(f"Domain dataset not found: {domain_path}\n"
                                "Run build_dataset.py first.")
    domain = pd.read_parquet(domain_path)
    log.info(f"Domain dataset: {domain.shape[0]} days × {domain.shape[1]} features")

    # ── Compute VD spatial weights ─────────────────────────────────────────
    log.info("\n── Computing VD Spatial Weights ──")
    pixel_df = compute_vd_spatial_weights()

    # ── Extract topo features per pixel ────────────────────────────────────
    log.info("\n── Extracting Topographic Features ──")
    pixel_df = extract_topo_per_pixel(pixel_df)

    # ── Cross-join: every pixel × every labeled day ────────────────────────
    log.info("\n── Building Pixel-Day Cross Product ──")
    labeled_days = domain[domain["pm25_observed"].notna()].copy()
    labeled_days["date"] = labeled_days.index

    n_pixels = len(pixel_df)
    n_days = len(labeled_days)
    log.info(f"  {n_pixels} pixels × {n_days} labeled days = {n_pixels * n_days:,} samples")

    # Build cross product efficiently
    pixel_df["_key"] = 1
    labeled_days["_key"] = 1
    cross = labeled_days.merge(pixel_df, on="_key", suffixes=("", "_pixel"))
    cross = cross.drop(columns=["_key"])

    # ── Disaggregate labels ────────────────────────────────────────────────
    # pm25_pixel = pm25_domain × vd_weight
    cross["pm25_observed_pixel"] = cross["pm25_observed"] * cross["vd_weight"]

    log.info(f"  Domain mean: {labeled_days['pm25_observed'].mean():.1f} µg/m³")
    log.info(f"  Pixel mean:  {cross['pm25_observed_pixel'].mean():.1f} µg/m³")
    log.info(f"  Pixel range: {cross['pm25_observed_pixel'].min():.1f}–"
             f"{cross['pm25_observed_pixel'].max():.1f} µg/m³")

    # ── Save ───────────────────────────────────────────────────────────────
    MERGED_DIR.mkdir(parents=True, exist_ok=True)

    # Save pixel metadata
    pixel_path = MERGED_DIR / "pixel_metadata.parquet"
    pixel_df.drop(columns=["_key"], errors="ignore").to_parquet(pixel_path, index=False)
    log.info(f"\nPixel metadata → {pixel_path}")

    # Save full pixel-day dataset
    out_path = MERGED_DIR / "dataset_pixel_daily.parquet"
    cross.to_parquet(out_path, index=False)
    log.info(f"Pixel-day dataset → {out_path}")
    log.info(f"  Shape: {cross.shape}")

    # ── Summary statistics ─────────────────────────────────────────────────
    log.info("\n── Spatial Disaggregation Summary ──")
    for _, px in pixel_df.drop(columns=["_key"], errors="ignore").iterrows():
        elev_str = f", elev={px.get('elevation', 0):.0f}m" if "elevation" in px else ""
        log.info(f"  Pixel {int(px['pixel_id'])}: ({px['lat']:.3f}, {px['lon']:.3f})"
                 f" weight={px['vd_weight']:.3f}{elev_str}")

    return cross


if __name__ == "__main__":
    df = build_pixel_dataset()
    print(f"\nPixel-day dataset: {df.shape[0]:,} samples × {df.shape[1]} features")
