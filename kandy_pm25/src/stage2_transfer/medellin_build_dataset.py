"""
medellin_build_dataset.py — Build the Medellín Stage 1 XGBoost dataset.

Two label modes (--labels flag):

  siata  (default, short period):
    Labels : SIATA daily city-mean (real PM2.5 ground truth, Aug 2018–Sep 2019)
    ERA5   : medellin_era5_siata_period.nc (Aug 2018–Sep 2019)
    Output : ~366 rows × 36 features
    Use    : Quick baseline; valid only for 1-year LOMO

  cams  (recommended, full period):
    Labels : CAMS EAC4 bias-corrected with SIATA overlap ratio
             ratio = mean(SIATA 2018-08:2019-09) / mean(CAMS same period)
    ERA5   : annual NC files in era5/annual/ (2018–2025)
    Output : ~2,922 rows × 36 features (7 years × 365 days)
    Use    : Statistically valid LOMO, directly comparable to Kandy 2018-2025

Output: data/processed/stage2/medellin_stage1_dataset.parquet        (siata mode)
        data/processed/stage2/medellin_stage1_dataset_cams.parquet   (cams mode)

Usage:
    cd kandy_pm25/
    python src/stage2_transfer/medellin_build_dataset.py                 # SIATA labels
    python src/stage2_transfer/medellin_build_dataset.py --labels cams   # CAMS+BC labels
    python src/stage2_transfer/medellin_build_dataset.py --no-satellite  # skip satellite
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
    MEDELLIN_ERA5_DIR,
    MEDELLIN_MODIS_DIR,
    MEDELLIN_TROPOMI_DIR,
    MEDELLIN_CAMS_DIR,
    MEDELLIN_BROAD_BBOX,
    MEDELLIN_VALLEY_DEPTH_M,
    MEDELLIN_VALLEY_AXIS_DEG,
    PROC_DIR,
    LOG_FORMAT, LOG_DATEFMT,
)

STAGE2_PROC_DIR = PROC_DIR / "stage2"

# Reuse feature computation functions from Stage 1
sys.path.insert(0, str(Path(__file__).parents[1]))
from stage1_satml.features.topo_features import (
    compute_vvc,
    compute_rwp,
    compute_valley_wind_decomposition,
)
from stage1_satml.data.process_gee_exports import spatial_mean_over_bbox

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("medellin_build_dataset")

# ─── Paths ────────────────────────────────────────────────────────────────────
PERSTATION_PARQUET   = STAGE2_PROC_DIR / "medellin_stage2_perstation.parquet"
ERA5_NC_LEGACY       = MEDELLIN_ERA5_DIR / "medellin_era5_siata_period.nc"   # Aug 2018–Sep 2019
ERA5_ANNUAL_DIR      = MEDELLIN_ERA5_DIR / "annual"                          # era5_medellin_YYYY.nc
OUTPUT_SIATA_PARQUET = STAGE2_PROC_DIR / "medellin_stage1_dataset.parquet"
OUTPUT_CAMS_PARQUET  = STAGE2_PROC_DIR / "medellin_stage1_dataset_cams.parquet"


# ─────────────────────────────────────────────────────────────────────────────
# 1A. LABELS — SIATA daily city-mean (Aug 2018–Sep 2019 only)
# ─────────────────────────────────────────────────────────────────────────────

def load_siata_labels() -> pd.Series:
    """
    Load SIATA per-station hourly data → daily city-mean PM2.5.
    Returns pd.Series named 'pm25_observed', tz-naive DatetimeIndex.
    """
    df = pd.read_parquet(PERSTATION_PARQUET)

    # datetime_utc column → tz-naive DatetimeIndex
    if "datetime_utc" in df.columns:
        dt = pd.to_datetime(df["datetime_utc"])
        if dt.dt.tz is not None:
            dt = dt.dt.tz_localize(None)
        df["date"] = dt.dt.normalize()
    else:
        dt = pd.to_datetime(df.index)
        if dt.tz is not None:
            dt = dt.tz_localize(None)
        df["date"] = dt.normalize()

    # Average all stations, then average across hours → daily city-mean
    daily = (
        df.groupby(["date", "station_id"])["pm25"]
        .mean()
        .groupby("date")
        .mean()
        .rename("pm25_observed")
    )
    daily.index = pd.DatetimeIndex(daily.index)
    if daily.index.tz is not None:
        daily.index = daily.index.tz_localize(None)
    log.info(f"SIATA labels: {len(daily)} days, mean={daily.mean():.1f}, std={daily.std():.1f} µg/m³")
    return daily


# ─────────────────────────────────────────────────────────────────────────────
# 1B. LABELS — CAMS EAC4 + SIATA bias correction (2018–2025)
# ─────────────────────────────────────────────────────────────────────────────

def load_cams_labels() -> pd.Series:
    """
    Load CAMS EAC4 daily PM2.5 CSVs (2018–2025) → bias-correct using SIATA overlap.

    Bias correction:
      ratio = mean(SIATA Aug 2018–Sep 2019) / mean(CAMS same period)
      pm25_observed = CAMS × ratio

    This is more robust than Kandy's KOALA anchor because we have 366 daily
    observations to validate the correction against.

    Returns pd.Series named 'pm25_observed', tz-naive DatetimeIndex.
    """
    # Load CAMS daily CSVs
    csv_files = sorted(MEDELLIN_CAMS_DIR.glob("cams_pm25_medellin_daily_*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CAMS daily CSVs found in {MEDELLIN_CAMS_DIR}\n"
            "Run: python scripts/download_cams_medellin.py --all --process"
        )

    dfs = []
    for f in csv_files:
        df = pd.read_csv(f, parse_dates=["date"])
        dfs.append(df)
    cams_df = pd.concat(dfs, ignore_index=True)
    cams_df["date"] = pd.to_datetime(cams_df["date"])
    cams_df = cams_df.sort_values("date").drop_duplicates("date").set_index("date")
    cams = cams_df["cams_pm25"].rename("pm25_cams")
    log.info(f"CAMS loaded: {len(cams)} days ({cams.index.min().date()} to "
             f"{cams.index.max().date()}), raw mean={cams.mean():.1f} µg/m³")

    # Load SIATA ground truth for bias correction
    siata = load_siata_labels()

    # Compute overlap period for bias correction
    overlap = pd.concat([cams, siata], axis=1).dropna()
    if len(overlap) < 30:
        raise ValueError(
            f"Only {len(overlap)} days of CAMS–SIATA overlap. "
            "Check CAMS CSV date range includes Aug 2018–Sep 2019."
        )
    siata_mean = overlap["pm25_observed"].mean()
    cams_mean  = overlap["pm25_cams"].mean()
    ratio      = siata_mean / cams_mean
    r_corr     = overlap["pm25_cams"].corr(overlap["pm25_observed"])

    log.info(f"CAMS–SIATA overlap: {len(overlap)} days "
             f"({overlap.index.min().date()} to {overlap.index.max().date()})")
    log.info(f"  SIATA mean = {siata_mean:.2f} µg/m³")
    log.info(f"  CAMS mean  = {cams_mean:.2f} µg/m³  (raw)")
    log.info(f"  Bias ratio = {ratio:.4f}  (SIATA/CAMS)")
    log.info(f"  r(CAMS, SIATA) = {r_corr:.3f}  (temporal structure quality)")

    if r_corr < 0.3:
        log.warning(
            f"r(CAMS, SIATA) = {r_corr:.3f} — CAMS temporal structure is weak over Medellín. "
            "Bias correction will fix the mean but not day-to-day variability."
        )

    # Apply flat ratio to all years
    pm25_bc = (cams * ratio).rename("pm25_observed")
    log.info(f"Bias-corrected CAMS: {len(pm25_bc)} days, "
             f"mean={pm25_bc.mean():.1f}, std={pm25_bc.std():.1f} µg/m³")
    return pm25_bc


# ─────────────────────────────────────────────────────────────────────────────
# 2. ERA5 FEATURES
# ─────────────────────────────────────────────────────────────────────────────

def _process_era5_ds(ds: xr.Dataset) -> pd.DataFrame:
    """Common processing for any ERA5 xarray Dataset → daily DataFrame."""
    time_dim = next((d for d in ds.dims if d in ("time", "valid_time")), None)
    if time_dim is None:
        raise ValueError(f"No time dimension found. Dims: {list(ds.dims)}")

    spatial_dims = [d for d in ds.dims if d not in (time_dim,)]
    ds_mean = ds.mean(dim=spatial_dims)
    df = ds_mean.to_dataframe()

    # Strip timezone
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    df.index = idx.normalize()
    df.index.name = "date"

    # Rename to project conventions
    rename = {
        "u10": "u10", "u_component_of_wind_10m": "u10",
        "v10": "v10", "v_component_of_wind_10m": "v10",
        "t2m": "t2m", "temperature_2m": "t2m",
        "d2m": "d2m", "dewpoint_temperature_2m": "d2m",
        "blh": "blh", "boundary_layer_height": "blh",
        "sp":  "sp",  "surface_pressure": "sp",
        "tp":  "tp",  "total_precipitation": "tp",
        "skt": "skt", "skin_temperature": "skt",
    }
    return df.rename(columns={k: v for k, v in rename.items() if k in df.columns})


def _aggregate_era5_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Group ERA5 hourly DataFrame → daily aggregates with derived variables."""
    agg = {
        "u10": "mean", "v10": "mean",
        "t2m": "mean", "d2m": "mean",
        "blh": ["min", "max"],
        "sp":  "mean",
        "tp":  "sum",
        "skt": "mean",
    }
    agg = {k: v for k, v in agg.items() if k in df.columns}
    daily = df.groupby(df.index).agg(agg)

    # Flatten MultiIndex columns
    daily.columns = [
        f"{c[0]}_{c[1]}" if isinstance(c, tuple) and c[1] else c[0]
        for c in daily.columns
    ]

    # Standardise column names after aggregation
    for raw, final in [
        ("u10_mean", "u10"), ("v10_mean", "v10"),
        ("t2m_mean", "t2m"), ("d2m_mean", "d2m"),
        ("sp_mean", "sp"), ("tp_sum", "tp"), ("skt_mean", "skt"),
    ]:
        if raw in daily.columns:
            daily = daily.rename(columns={raw: final})

    # Derived: wind speed and direction
    daily["wind_speed"] = np.sqrt(daily["u10"] ** 2 + daily["v10"] ** 2)
    daily["wind_dir"]   = (270 - np.degrees(np.arctan2(daily["v10"], daily["u10"]))) % 360

    # Relative humidity
    if "t2m" in daily.columns and "d2m" in daily.columns:
        tc  = daily["t2m"] - 273.15
        tdc = daily["d2m"] - 273.15
        daily["rh"] = (
            100 * np.exp((17.625 * tdc) / (243.04 + tdc)) /
                  np.exp((17.625 * tc)  / (243.04 + tc))
        ).clip(0, 100)

    # Surface pressure Pa → hPa
    if "sp" in daily.columns:
        daily["sp"] = daily["sp"] / 100.0

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


def load_era5_features(mode: str = "siata") -> pd.DataFrame:
    """
    Load ERA5 → daily aggregates.

    mode='siata': uses legacy medellin_era5_siata_period.nc (Aug 2018–Sep 2019)
    mode='cams':  uses annual NC files in era5/annual/ (2018–2025), concatenated
    """
    if mode == "cams":
        annual_files = sorted(ERA5_ANNUAL_DIR.glob("era5_medellin_*.nc"))
        if not annual_files:
            raise FileNotFoundError(
                f"No annual ERA5 NC files in {ERA5_ANNUAL_DIR}\n"
                "Run: python scripts/download_era5_medellin.py --all"
            )
        log.info(f"Loading {len(annual_files)} annual ERA5 NC files …")
        parts = []
        for f in annual_files:
            ds = xr.open_dataset(f)
            df = _process_era5_ds(ds)
            parts.append(df)
        df_all = pd.concat(parts).sort_index()
        df_all = df_all[~df_all.index.duplicated(keep="first")]
    else:
        # Legacy: single merged NC for SIATA period
        if not ERA5_NC_LEGACY.exists():
            raise FileNotFoundError(f"ERA5 NC not found: {ERA5_NC_LEGACY}")
        ds = xr.open_dataset(ERA5_NC_LEGACY)
        log.info(f"ERA5 NC: dims={dict(ds.dims)}, vars={list(ds.data_vars)}")
        df_all = _process_era5_ds(ds)

    daily = _aggregate_era5_daily(df_all)
    log.info(f"ERA5 features: {daily.shape[0]} days, {daily.shape[1]} columns.")
    return daily


# ─────────────────────────────────────────────────────────────────────────────
# 3. SATELLITE — MODIS + TROPOMI from GeoTIFFs
# ─────────────────────────────────────────────────────────────────────────────

def load_satellite_features() -> pd.DataFrame:
    """
    Load MODIS AOD + TROPOMI monthly GeoTIFFs → interpolated to daily.
    Handles any date range (2018-08 to 2025-12 once all files downloaded).
    """
    bbox = MEDELLIN_BROAD_BBOX
    series_list = []

    # MODIS AOD
    modis_files = sorted(MEDELLIN_MODIS_DIR.glob("modis_aod_medellin_*.tif"))
    if modis_files:
        records = {}
        for f in modis_files:
            parts = f.stem.split("_")
            yyyymm = next((p for p in parts if len(p) == 6 and p.isdigit()), None)
            if yyyymm is None:
                continue
            val = spatial_mean_over_bbox(f, bbox)
            if val is not None:
                records[pd.Timestamp(f"{yyyymm[:4]}-{yyyymm[4:]}-01")] = val
        if records:
            s = pd.Series(records, name="aod_modis").sort_index()
            daily_idx = pd.date_range(s.index.min(), s.index.max() + pd.offsets.MonthEnd(0), freq="D")
            series_list.append(s.reindex(daily_idx).interpolate(method="time"))
            log.info(f"MODIS AOD: {len(s)} monthly → {len(daily_idx)} daily records.")
    else:
        log.warning(f"No MODIS GeoTIFFs in {MEDELLIN_MODIS_DIR}.")

    # TROPOMI products
    tropomi_map = {
        "no2":    ("tropomi_no2",    "tropomi_no2_medellin_*.tif"),
        "co":     ("tropomi_co",     "tropomi_co_medellin_*.tif"),
        "aer_ai": ("tropomi_aer_ai", "tropomi_aer_ai_medellin_*.tif"),
    }
    for prod, (col_name, pattern) in tropomi_map.items():
        tif_files = sorted(MEDELLIN_TROPOMI_DIR.glob(pattern))
        if not tif_files:
            log.warning(f"No TROPOMI {prod.upper()} GeoTIFFs found.")
            continue
        records = {}
        for f in tif_files:
            parts = f.stem.split("_")
            yyyymm = next((p for p in parts if len(p) == 6 and p.isdigit()), None)
            if yyyymm is None:
                continue
            val = spatial_mean_over_bbox(f, bbox)
            if val is not None:
                records[pd.Timestamp(f"{yyyymm[:4]}-{yyyymm[4:]}-01")] = val
        if records:
            s = pd.Series(records, name=col_name).sort_index()
            daily_idx = pd.date_range(s.index.min(), s.index.max() + pd.offsets.MonthEnd(0), freq="D")
            series_list.append(s.reindex(daily_idx).interpolate(method="time"))
            log.info(f"TROPOMI {prod.upper()}: {len(s)} monthly → {len(daily_idx)} daily.")

    if not series_list:
        log.warning("No satellite data available. Returning empty DataFrame.")
        return pd.DataFrame()

    df = pd.concat(series_list, axis=1)
    df.index.name = "date"
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 4. TOPO FEATURES
# ─────────────────────────────────────────────────────────────────────────────

def compute_topo_features(era5: pd.DataFrame) -> pd.DataFrame:
    """Compute VVC, RWP, valley wind decomposition for Medellín (N-S axis, 800m depth)."""
    feats = pd.DataFrame(index=era5.index)

    if "blh_min" in era5.columns and "wind_speed" in era5.columns:
        feats["vvc"] = compute_vvc(
            era5["wind_speed"], era5["blh_min"],
            valley_depth_m=MEDELLIN_VALLEY_DEPTH_M,
        )
    if "blh_min" in era5.columns:
        feats["blh_ratio"] = era5["blh_min"] / 1000.0

    if "tp" in era5.columns and "wind_speed" in era5.columns:
        feats["rwp"] = compute_rwp(era5["tp"], era5["wind_speed"])

    if "u10" in era5.columns and "v10" in era5.columns:
        vw = compute_valley_wind_decomposition(
            era5["u10"], era5["v10"],
            blh_m=era5.get("blh_min"),
            valley_axis_deg=MEDELLIN_VALLEY_AXIS_DEG,
        )
        feats = pd.concat([feats, vw], axis=1)

    log.info(f"Topo features: {feats.shape[1]} columns computed.")
    return feats


# ─────────────────────────────────────────────────────────────────────────────
# 5. INTERACTION FEATURES
# ─────────────────────────────────────────────────────────────────────────────

def compute_interaction_features(merged: pd.DataFrame) -> pd.DataFrame:
    """AOD/BLH + NO2/BLH + CO/BLH ratio features (same as Kandy)."""
    feats = pd.DataFrame(index=merged.index)
    eps = 1e-3

    if "aod_modis" in merged.columns and "blh_min" in merged.columns:
        feats["aod_blh_ratio"] = merged["aod_modis"] / (merged["blh_min"] + eps)
    if "aod_modis" in merged.columns and "rh" in merged.columns:
        feats["aod_rh"] = merged["aod_modis"] * (1 + merged["rh"] / 100.0)
    if "tropomi_no2" in merged.columns and "blh_min" in merged.columns:
        feats["no2_blh_ratio"] = merged["tropomi_no2"] / (merged["blh_min"] + eps)
    if "tropomi_co" in merged.columns and "blh_min" in merged.columns:
        feats["co_blh_ratio"] = merged["tropomi_co"] / (merged["blh_min"] + eps)

    log.info(f"Interaction features: {feats.shape[1]} columns.")
    return feats


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def build_dataset(label_mode: str = "siata", use_satellite: bool = True) -> pd.DataFrame:
    """
    Build the full Medellín Stage 1 dataset and save to parquet.

    label_mode : 'siata' (366 days, ground truth) | 'cams' (2918 days, BC CAMS)
    use_satellite : include MODIS + TROPOMI features
    """
    era5_mode = label_mode  # 'siata' uses legacy NC; 'cams' uses annual NCs

    # 1. Labels
    if label_mode == "cams":
        labels = load_cams_labels()
        output_parquet = OUTPUT_CAMS_PARQUET
    else:
        labels = load_siata_labels()
        output_parquet = OUTPUT_SIATA_PARQUET

    # 2. ERA5
    era5 = load_era5_features(mode=era5_mode)

    # 3. Topo features
    topo = compute_topo_features(era5)

    # 4. Satellite
    sat = pd.DataFrame()
    if use_satellite:
        sat = load_satellite_features()

    # 5. Merge
    parts = [era5, topo]
    if not sat.empty:
        parts.append(sat)
    merged = pd.concat(parts, axis=1)
    merged.index.name = "date"

    # 5b. Fill temporal features for ALL rows from index (not just ERA5 days)
    #     _aggregate_era5_daily computes these from ERA5 DatetimeIndex, so they
    #     are NaN for dates without ERA5. Re-derive from the merged index.
    merged["month_sin"] = np.sin(2 * np.pi * merged.index.month / 12)
    merged["month_cos"] = np.cos(2 * np.pi * merged.index.month / 12)
    merged["doy_sin"]   = np.sin(2 * np.pi * merged.index.dayofyear / 365)
    merged["doy_cos"]   = np.cos(2 * np.pi * merged.index.dayofyear / 365)
    merged["dow_sin"]   = np.sin(2 * np.pi * merged.index.dayofweek / 7)
    merged["dow_cos"]   = np.cos(2 * np.pi * merged.index.dayofweek / 7)
    merged["month"]     = merged.index.month
    merged["doy"]       = merged.index.dayofyear

    # 6. Interaction features
    interact = compute_interaction_features(merged)
    merged = pd.concat([merged, interact], axis=1)

    # 7. Add labels (inner join — only days with labels)
    merged["pm25_observed"] = labels
    n_before = len(merged)
    merged = merged.dropna(subset=["pm25_observed"])
    log.info(f"Rows after label join: {len(merged)} (dropped {n_before - len(merged)} unlabelled)")

    # 8. Satellite NaN coverage report
    sat_cols = [c for c in merged.columns if c.startswith(("aod_", "tropomi_"))]
    if sat_cols:
        missing_pct = merged[sat_cols].isna().mean() * 100
        for col, pct in missing_pct.items():
            if pct > 0:
                log.info(f"  {col}: {pct:.1f}% NaN (cloud / instrument gap — will be imputed by XGBoost)")

    # 9. Save
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(output_parquet)
    log.info(f"Saved: {output_parquet} — {merged.shape[0]} rows × {merged.shape[1]} cols")
    log.info(f"Columns: {list(merged.columns)}")

    return merged


def main():
    parser = argparse.ArgumentParser(description="Build Medellín Stage 1 dataset")
    parser.add_argument(
        "--labels", choices=["siata", "cams"], default="siata",
        help="Label source: 'siata' (366 days ground truth) or "
             "'cams' (2018-2025, CAMS+SIATA bias correction)"
    )
    parser.add_argument(
        "--no-satellite", action="store_true",
        help="Skip satellite features (use if GeoTIFFs not yet downloaded)"
    )
    args = parser.parse_args()
    build_dataset(label_mode=args.labels, use_satellite=not args.no_satellite)


if __name__ == "__main__":
    main()
