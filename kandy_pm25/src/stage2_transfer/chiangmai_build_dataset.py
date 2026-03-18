"""
chiangmai_build_dataset.py — Build the Chiang Mai Stage 1 XGBoost dataset.

PURPOSE
-------
Builds a daily feature matrix (ERA5 + satellite + terrain) for Chiang Mai 2022,
with Air4Thai city-mean as the PM2.5 label. Non-burning season only (May–Dec).

This is the input to `chiangmai_train_stage1.py`, whose XGBoost pixel predictions
become the PINN training pseudo-labels (same approach as the actual Kandy workflow).

LABELS
------
Air4Thai city-mean (3 stations): used directly, no CAMS needed.
Fallback: if <2 stations valid on a given day, that day is dropped.
Non-burning season only: months 5–12 (May–December 2022).

SATELLITE FEATURES (requires GEE .tif files to be present locally)
-------------------
  MODIS AOD monthly → daily interpolated
  TROPOMI NO2, CO, AER_AI monthly → daily interpolated
  Expected in: data/external/chiangmai/satellite/{modis,tropomi}/

OUTPUT
------
  data/processed/stage2/chiangmai_stage1_dataset.parquet
    ~245 rows × ~30 features (non-burning season days with ≥1 satellite obs)

Usage
-----
    python src/stage2_transfer/chiangmai_build_dataset.py
    python src/stage2_transfer/chiangmai_build_dataset.py --no-satellite  # ERA5+labels only
    python src/stage2_transfer/chiangmai_build_dataset.py --force
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import (
    CHIANGMAI_ERA5_DIR,
    CHIANGMAI_MODIS_DIR,
    CHIANGMAI_TROPOMI_DIR,
    CHIANGMAI_PM25_DIR,
    CHIANGMAI_BROAD_BBOX,
    CHIANGMAI_VALLEY_DEPTH_M,
    CHIANGMAI_VALLEY_AXIS_DEG,
    PROC_DIR,
    LOG_FORMAT, LOG_DATEFMT,
)

sys.path.insert(0, str(Path(__file__).parents[1]))
from stage1_satml.features.topo_features import (
    compute_vvc,
    compute_rwp,
    compute_valley_wind_decomposition,
)
from stage1_satml.data.process_gee_exports import spatial_mean_over_bbox

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("chiangmai_build_dataset")

# ── Paths ─────────────────────────────────────────────────────────────────────
STAGE2_PROC_DIR  = PROC_DIR / "stage2"
AIR4THAI_CSV     = CHIANGMAI_PM25_DIR / "chiangmai_pm25_raw_2022.csv"
ERA5_NC          = CHIANGMAI_ERA5_DIR / "chiangmai_era5_2022.nc"
OUTPUT_PARQUET   = STAGE2_PROC_DIR / "chiangmai_stage1_dataset.parquet"

# Non-burning season: May–December
NON_BURNING_MONTHS = [5, 6, 7, 8, 9, 10, 11, 12]


# ─────────────────────────────────────────────────────────────────────────────
# 1. LABELS — Air4Thai city-mean (direct, no CAMS BC needed)
# ─────────────────────────────────────────────────────────────────────────────

def load_air4thai_labels() -> pd.Series:
    """
    Load Air4Thai hourly PM2.5 → daily city-mean.
    3 stations → average across stations then across hours.
    Returns pd.Series named 'pm25_observed', tz-naive daily DatetimeIndex.
    Non-burning season only (months 5–12).
    """
    df = pd.read_csv(AIR4THAI_CSV)
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True)
    df["date"] = df["datetime_utc"].dt.tz_localize(None).dt.normalize()

    # Non-burning season filter
    df = df[df["datetime_utc"].dt.month.isin(NON_BURNING_MONTHS)].copy()

    # Physical filter
    df = df[(df["pm25"] >= 0) & (df["pm25"] <= 200)].copy()

    # Daily city-mean: average across stations per day
    daily = (
        df.groupby(["date", "location_id"])["pm25"]
        .mean()              # per-station daily mean
        .groupby("date")     # then city average
        .mean()
        .rename("pm25_observed")
    )
    daily.index = pd.DatetimeIndex(daily.index)

    # Drop days with very few observations (< 2 stations reporting)
    n_sta_per_day = (
        df.groupby("date")["location_id"].nunique()
    )
    valid_days = n_sta_per_day[n_sta_per_day >= 2].index
    daily = daily[daily.index.isin(valid_days)]

    log.info(
        f"Air4Thai labels: {len(daily)} days (≥2 stations), "
        f"mean={daily.mean():.1f}, std={daily.std():.1f} µg/m³"
    )
    return daily


# ─────────────────────────────────────────────────────────────────────────────
# 2. ERA5 FEATURES
# ─────────────────────────────────────────────────────────────────────────────

def _process_era5_ds(ds: xr.Dataset) -> pd.DataFrame:
    """ERA5 xarray Dataset → hourly DataFrame, spatial-averaged."""
    time_dim = next((d for d in ds.dims if d in ("time", "valid_time")), None)
    if time_dim is None:
        raise ValueError(f"No time dimension found. Dims: {list(ds.dims)}")

    spatial_dims = [d for d in ds.dims if d not in (time_dim,)]
    ds_mean = ds.mean(dim=spatial_dims)
    df = ds_mean.to_dataframe()

    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    df.index = idx
    df.index.name = "datetime"

    rename = {
        "u10": "u10", "v10": "v10", "t2m": "t2m", "d2m": "d2m",
        "blh": "blh", "sp": "sp", "tp": "tp", "skt": "skt",
    }
    return df.rename(columns={k: v for k, v in rename.items() if k in df.columns})


def _aggregate_era5_daily(df: pd.DataFrame) -> pd.DataFrame:
    """ERA5 hourly → daily aggregates with derived variables."""
    agg = {
        "u10": "mean", "v10": "mean",
        "t2m": "mean", "d2m": "mean",
        "blh": ["min", "max"],
        "sp":  "mean",
        "tp":  "sum",
    }
    agg = {k: v for k, v in agg.items() if k in df.columns}
    df["date"] = df.index.normalize()
    daily = df.groupby("date").agg(agg)

    # Flatten multi-index columns
    daily.columns = [
        f"{c[0]}_{c[1]}" if isinstance(c, tuple) and c[1] else c[0]
        for c in daily.columns
    ]
    for raw, final in [
        ("u10_mean", "u10"), ("v10_mean", "v10"),
        ("t2m_mean", "t2m"), ("d2m_mean", "d2m"),
        ("sp_mean", "sp"), ("tp_sum", "tp"),
    ]:
        if raw in daily.columns:
            daily = daily.rename(columns={raw: final})

    # Derived: wind speed and direction
    daily["wind_speed"] = np.sqrt(daily["u10"] ** 2 + daily["v10"] ** 2)
    daily["wind_dir"]   = (270 - np.degrees(np.arctan2(daily["v10"], daily["u10"]))) % 360

    # Relative humidity from dewpoint
    if "t2m" in daily.columns and "d2m" in daily.columns:
        tc  = daily["t2m"] - 273.15
        tdc = daily["d2m"] - 273.15
        daily["rh"] = (
            100 * np.exp((17.625 * tdc) / (243.04 + tdc)) /
                  np.exp((17.625 * tc)  / (243.04 + tc))
        ).clip(0, 100)

    if "sp" in daily.columns:
        daily["sp"] = daily["sp"] / 100.0  # Pa → hPa

    # Temporal encodings
    daily["month"]     = daily.index.month
    daily["month_sin"] = np.sin(2 * np.pi * daily.index.month / 12)
    daily["month_cos"] = np.cos(2 * np.pi * daily.index.month / 12)
    daily["doy"]       = daily.index.dayofyear
    daily["doy_sin"]   = np.sin(2 * np.pi * daily.index.dayofyear / 365)
    daily["doy_cos"]   = np.cos(2 * np.pi * daily.index.dayofyear / 365)
    daily["dow_sin"]   = np.sin(2 * np.pi * daily.index.dayofweek / 7)
    daily["dow_cos"]   = np.cos(2 * np.pi * daily.index.dayofweek / 7)

    return daily


def load_era5_features() -> pd.DataFrame:
    """Load ERA5 2022 for Chiang Mai → daily aggregates (non-burning season)."""
    if not ERA5_NC.exists():
        raise FileNotFoundError(f"ERA5 NC not found: {ERA5_NC}")

    log.info(f"Loading ERA5: {ERA5_NC}")
    ds = xr.open_dataset(str(ERA5_NC))
    df = _process_era5_ds(ds)
    ds.close()

    daily = _aggregate_era5_daily(df)

    # Filter to non-burning season
    daily = daily[daily.index.month.isin(NON_BURNING_MONTHS)]
    log.info(f"ERA5 (non-burning): {len(daily)} days, {len(daily.columns)} raw cols")
    return daily


# ─────────────────────────────────────────────────────────────────────────────
# 3. SATELLITE — MODIS + TROPOMI from monthly GeoTIFFs
# ─────────────────────────────────────────────────────────────────────────────

def load_satellite_features() -> pd.DataFrame:
    """
    Load MODIS AOD + TROPOMI monthly GeoTIFFs → daily interpolated features.
    Expects files in CHIANGMAI_MODIS_DIR and CHIANGMAI_TROPOMI_DIR.
    Raises RuntimeError if no files found (satellite is required for Stage 1).
    """
    bbox = CHIANGMAI_BROAD_BBOX
    series_list = []

    # MODIS AOD
    modis_files = sorted(CHIANGMAI_MODIS_DIR.glob("modis_aod_chiangmai_*.tif"))
    if modis_files:
        records = {}
        for f in modis_files:
            yyyymm = next((p for p in f.stem.split("_") if len(p) == 6 and p.isdigit()), None)
            if yyyymm is None:
                continue
            val = spatial_mean_over_bbox(f, bbox)
            if val is not None:
                records[pd.Timestamp(f"{yyyymm[:4]}-{yyyymm[4:]}-01")] = val
        if records:
            s = pd.Series(records, name="aod_modis").sort_index()
            daily_idx = pd.date_range(s.index.min(), s.index.max() + pd.offsets.MonthEnd(0), freq="D")
            series_list.append(s.reindex(daily_idx).interpolate(method="time"))
            log.info(f"MODIS AOD: {len(s)} monthly → {len(daily_idx)} daily records")
    else:
        log.warning(f"No MODIS GeoTIFFs found in {CHIANGMAI_MODIS_DIR}")

    # TROPOMI products
    tropomi_map = {
        "no2":    ("tropomi_no2",    "tropomi_no2_chiangmai_*.tif"),
        "co":     ("tropomi_co",     "tropomi_co_chiangmai_*.tif"),
        "aer_ai": ("tropomi_aer_ai", "tropomi_aer_ai_chiangmai_*.tif"),
    }
    for prod, (col_name, pattern) in tropomi_map.items():
        tif_files = sorted(CHIANGMAI_TROPOMI_DIR.glob(pattern))
        if not tif_files:
            log.warning(f"No TROPOMI {prod.upper()} GeoTIFFs found in {CHIANGMAI_TROPOMI_DIR}")
            continue
        records = {}
        for f in tif_files:
            yyyymm = next((p for p in f.stem.split("_") if len(p) == 6 and p.isdigit()), None)
            if yyyymm is None:
                continue
            val = spatial_mean_over_bbox(f, bbox)
            if val is not None:
                records[pd.Timestamp(f"{yyyymm[:4]}-{yyyymm[4:]}-01")] = val
        if records:
            s = pd.Series(records, name=col_name).sort_index()
            daily_idx = pd.date_range(s.index.min(), s.index.max() + pd.offsets.MonthEnd(0), freq="D")
            series_list.append(s.reindex(daily_idx).interpolate(method="time"))
            log.info(f"TROPOMI {prod.upper()}: {len(s)} monthly → {len(daily_idx)} daily")

    if not series_list:
        raise RuntimeError(
            "No satellite GeoTIFF files found.\n"
            f"  MODIS dir:   {CHIANGMAI_MODIS_DIR}\n"
            f"  TROPOMI dir: {CHIANGMAI_TROPOMI_DIR}\n"
            "Download from Google Drive folders: ChiangmaiPM25_MODIS/ and ChiangmaiPM25_TROPOMI/\n"
            "Then re-run this script. Or use --no-satellite to build ERA5-only dataset."
        )

    df = pd.concat(series_list, axis=1)
    df.index.name = "date"
    # Filter to non-burning season
    df = df[df.index.month.isin(NON_BURNING_MONTHS)]
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 4. TOPO FEATURES
# ─────────────────────────────────────────────────────────────────────────────

def compute_topo_features(era5: pd.DataFrame) -> pd.DataFrame:
    """Compute VVC, RWP, valley wind decomposition for Chiang Mai (N-S axis, 800m depth)."""
    feats = pd.DataFrame(index=era5.index)

    blh_col = "blh_min" if "blh_min" in era5.columns else "blh"
    ws_col  = "wind_speed"

    if blh_col in era5.columns and ws_col in era5.columns:
        feats["vvc"] = compute_vvc(
            era5[ws_col], era5[blh_col],
            valley_depth_m=CHIANGMAI_VALLEY_DEPTH_M,
        )
        feats["blh_ratio"] = era5[blh_col] / 1000.0

    if "tp" in era5.columns and ws_col in era5.columns:
        feats["rwp"] = compute_rwp(era5["tp"], era5[ws_col])

    if "u10" in era5.columns and "v10" in era5.columns:
        vw = compute_valley_wind_decomposition(
            era5["u10"], era5["v10"],
            blh_m=era5.get(blh_col),
            valley_axis_deg=CHIANGMAI_VALLEY_AXIS_DEG,
        )
        feats = pd.concat([feats, vw], axis=1)

    log.info(f"Topo features: {feats.shape[1]} columns")
    return feats


# ─────────────────────────────────────────────────────────────────────────────
# 5. INTERACTION FEATURES
# ─────────────────────────────────────────────────────────────────────────────

def compute_interaction_features(merged: pd.DataFrame) -> pd.DataFrame:
    """AOD/BLH + NO2/BLH + CO/BLH ratio features."""
    feats = pd.DataFrame(index=merged.index)
    blh_col = "blh_min" if "blh_min" in merged.columns else "blh"
    eps = 1e-3

    if "aod_modis" in merged.columns and blh_col in merged.columns:
        feats["aod_blh_ratio"] = merged["aod_modis"] / (merged[blh_col] + eps)
    if "aod_modis" in merged.columns and "rh" in merged.columns:
        feats["aod_rh"] = merged["aod_modis"] * (1 + merged["rh"] / 100.0)
    if "tropomi_no2" in merged.columns and blh_col in merged.columns:
        feats["no2_blh_ratio"] = merged["tropomi_no2"] / (merged[blh_col] + eps)
    if "tropomi_co" in merged.columns and blh_col in merged.columns:
        feats["co_blh_ratio"] = merged["tropomi_co"] / (merged[blh_col] + eps)

    log.info(f"Interaction features: {feats.shape[1]} columns")
    return feats


# ─────────────────────────────────────────────────────────────────────────────
# MAIN BUILD
# ─────────────────────────────────────────────────────────────────────────────

def build_dataset(use_satellite: bool = True) -> pd.DataFrame:
    """Build full Chiang Mai Stage 1 dataset and save to parquet."""
    STAGE2_PROC_DIR.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Labels ────────────────────────────────────────────────────────
    labels = load_air4thai_labels()

    # ── Step 2: ERA5 ──────────────────────────────────────────────────────────
    era5 = load_era5_features()

    # ── Step 3: Topo features ─────────────────────────────────────────────────
    topo = compute_topo_features(era5)

    # ── Step 4: Satellite ─────────────────────────────────────────────────────
    if use_satellite:
        satellite = load_satellite_features()
    else:
        log.warning("--no-satellite: skipping MODIS/TROPOMI features")
        satellite = pd.DataFrame(index=era5.index)

    # ── Step 5: Merge ─────────────────────────────────────────────────────────
    merged = era5.join(topo, how="left", lsuffix="", rsuffix="_topo")
    if not satellite.empty:
        merged = merged.join(satellite, how="left")
    interaction = compute_interaction_features(merged)
    merged = merged.join(interaction, how="left")

    # ── Step 6: Merge labels ──────────────────────────────────────────────────
    merged = merged.join(labels, how="inner")

    # Drop rows with missing labels
    n_before = len(merged)
    merged = merged.dropna(subset=["pm25_observed"])
    log.info(f"After label merge: {len(merged)} days ({n_before - len(merged)} dropped for missing labels)")

    # Drop rows missing all satellite features if satellite was requested
    if use_satellite and "aod_modis" in merged.columns:
        sat_cols = [c for c in merged.columns if c in ("aod_modis", "tropomi_no2", "tropomi_co", "tropomi_aer_ai")]
        n_before = len(merged)
        merged = merged.dropna(subset=sat_cols, how="all")
        if n_before > len(merged):
            log.warning(f"  Dropped {n_before - len(merged)} days missing all satellite features")

    # ── Summary ───────────────────────────────────────────────────────────────
    log.info("─" * 60)
    log.info("Chiang Mai Stage 1 dataset summary:")
    log.info(f"  Rows:     {len(merged)}")
    log.info(f"  Columns:  {len(merged.columns)}")
    log.info(f"  Period:   {merged.index.min().date()} – {merged.index.max().date()}")
    log.info(f"  PM2.5:    mean={merged['pm25_observed'].mean():.1f}, std={merged['pm25_observed'].std():.1f} µg/m³")
    log.info(f"  Columns:  {sorted(merged.columns.tolist())}")
    log.info("─" * 60)

    merged.index.name = "date"
    merged.to_parquet(OUTPUT_PARQUET)
    log.info(f"Saved: {OUTPUT_PARQUET}  ({OUTPUT_PARQUET.stat().st_size / 1e3:.0f} KB)")
    return merged


def main():
    parser = argparse.ArgumentParser(
        description="Build Chiang Mai Stage 1 XGBoost dataset (non-burning season 2022)"
    )
    parser.add_argument("--no-satellite", action="store_true",
                        help="Skip satellite features (ERA5+labels only)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing output")
    args = parser.parse_args()

    if OUTPUT_PARQUET.exists() and not args.force:
        log.info(f"Output already exists: {OUTPUT_PARQUET}  (use --force to rebuild)")
        return

    build_dataset(use_satellite=not args.no_satellite)


if __name__ == "__main__":
    main()
