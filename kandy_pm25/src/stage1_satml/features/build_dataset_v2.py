"""
build_dataset_v2.py — Stage 1 v2 mechanistic multi-station feature builder.

OSF pre-registration: docs/osf_prereg_stage1_v2.md (working-lock 2026-05-17).
Project rules: .claude/rules/stage1-data.md v2 section.

Produces a multi-station daily training table where each row is
  (date, sensor_id, ..., 28 mechanistic features, pm25_observed)

The target (`pm25_observed`) is the FECT-calibrated PurpleAir reading
(`pm25_observed_barkjohn_clim_rh` from calibrate_fect.py). Reanalysis
products (CAMS, GEOS-CF) are FEATURES — model learns the residual.

────────────────────────────────────────────────────────────────────────
v2 vs v1 semantic flip
────────────────────────────────────────────────────────────────────────
v1: pm25_observed = KOALA-corrected CAMS (label = bias-corrected reanalysis)
v2: pm25_observed = FECT-calibrated PurpleAir reading (label = station obs)
    cams_pm25_raw  = back-out of v1 pm25_observed / CAMS_BIAS_FACTOR_FLAT
    geos_cf_pm25_raw = pulled directly from GEE export (when available)

────────────────────────────────────────────────────────────────────────
28-feature mechanistic taxonomy (pre-reg §4)
────────────────────────────────────────────────────────────────────────
A. Ventilation (5):
    wind_speed_10m, blh_era5, ventilation_coefficient,
    lapse_rate_t925_t2m, nocturnal_blh_ratio
B. Valley transport (4):
    wind_along_corridor, wind_cross_corridor,
    wind_into_blocked_sector, valley_drainage_index
C. Wet scavenging (3):
    precip_24h, precip_7d, dry_spell_days
D. Source / column (4):
    aod_maiac, aod_blh_ratio, no2_column, fire_count_5d
E. Multi-fidelity priors (3):
    cams_pm25_raw, geos_cf_pm25_raw, prior_disagreement
F. Climate modes (4):
    mei_sin, mei_cos, iod_dmi, mjo_amplitude
G. Temporal (4):
    pm25_lag_1d, pm25_lag_7d_mean, pm25_lag_30d_mean, doy_sin, doy_cos

────────────────────────────────────────────────────────────────────────
v2.0 NaN-tolerant feature availability (2026-05-17)
────────────────────────────────────────────────────────────────────────
PRESENT today (built from v1 merged parquet + climate CSVs + FECT):
  A:  all 5
  B:  3 of 4 (wind_into_blocked_sector built via vector projection;
              v1 had only the scalar TBI — see compute_wind_into_blocked_sector)
  C:  all 3
  D:  3 of 4 (aod_maiac, aod_blh_ratio, no2_column — TROPOMI 2018+ only;
              fire_count_5d → NaN, pending VIIRS GEE export)
  E:  2 of 3 (cams_pm25_raw via back-out; prior_disagreement → NaN;
              geos_cf_pm25_raw → NaN until GEE export downloads)
  F:  3 of 4 (mei_sin/cos, iod_dmi, mjo_amplitude — MJO has 2024-02-24 cutoff)
  G:  all 5

XGBoost handles NaN natively. After GEOS-CF lands, re-run with `--force`
to slot in `geos_cf_pm25_raw` and `prior_disagreement` without changing
the rest of the pipeline.

────────────────────────────────────────────────────────────────────────
Outputs
────────────────────────────────────────────────────────────────────────
  data/processed/stage1_v2/dataset_v2_multistation_daily.parquet
      ~32 columns × N rows (one row per qc-good sensor-day, inner-joined
      against feature availability). Date as both index and column.

  data/processed/stage1_v2/feature_provenance_v2.csv
      Per-feature: source file, derivation, NaN count, range.

Usage:
  python -m src.stage1_satml.features.build_dataset_v2
  python src/stage1_satml/features/build_dataset_v2.py
  python src/stage1_satml/features/build_dataset_v2.py --force

Reference: pre-reg §3, §4; calibrate_fect.py; download_climate_modes.py.
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    PROC_DIR, RAW_DIR, EXTERNAL_DIR,
    CAMS_BIAS_FACTOR_FLAT,
    LOG_FORMAT, LOG_DATEFMT,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("build_dataset_v2")

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

V1_MERGED        = PROC_DIR / "merged" / "dataset_daily.parquet"
FECT_DAILY       = EXTERNAL_DIR / "purpleair" / "processed" / "fect_kandy_calibrated_daily.parquet"
CLIMATE_DIR      = RAW_DIR / "climate_modes"
GEOS_CF_PROC_DIR = RAW_DIR / "geos_cf"          # populated post-GEE download
MODIS_RAW_DIR    = RAW_DIR / "modis_aod"        # MAIAC tifs (monthly)

OUT_DIR        = PROC_DIR / "stage1_v2"
OUT_DAILY      = OUT_DIR / "dataset_v2_multistation_daily.parquet"
OUT_PROVENANCE = OUT_DIR / "feature_provenance_v2.csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# Hantana ridge blocking sector (gotcha #10, build_dataset.py):
# S/SSW, 175°–195° — winds blowing FROM this direction are blocked by the ridge.
BLOCKED_SECTOR_MIN_DEG = 175.0
BLOCKED_SECTOR_MAX_DEG = 195.0

# Per-sensor elevation (m ASL) from `ingest_purpleair_history.py` sensor catalog.
# Could be replaced with DEM lookup if needed; hardcoded for determinism.
SENSOR_ELEVATION_M: dict[int, float] = {
    12451: 1538.0,   # FECT_Akurana
    33495: 1698.0,   # FECT_Hantana_TR4
    21923: 1504.0,   # FECT_Kandy_TR7  (dropped — sparse)
    29677: 39.0,     # Gregorys_Road    (Colombo OOD)
}


# ─────────────────────────────────────────────────────────────────────────────
# Loaders
# ─────────────────────────────────────────────────────────────────────────────

def load_v1_features() -> pd.DataFrame:
    """v1 merged parquet — date INDEX, 50 columns, 2003–2025."""
    if not V1_MERGED.exists():
        raise FileNotFoundError(f"v1 merged parquet missing: {V1_MERGED}")
    df = pd.read_parquet(V1_MERGED)
    log.info(f"  v1 merged: {df.shape[0]:>5,} rows × {df.shape[1]} cols  "
             f"[{df.index.min().date()} → {df.index.max().date()}]")
    return df


def load_fect_daily() -> pd.DataFrame:
    """FECT calibrated daily — date COLUMN, multi-station."""
    if not FECT_DAILY.exists():
        raise FileNotFoundError(f"FECT daily missing — run calibrate_fect.py first: {FECT_DAILY}")
    df = pd.read_parquet(FECT_DAILY)
    df["date"] = pd.to_datetime(df["date"])
    log.info(f"  FECT daily: {df.shape[0]:>5,} sensor-day rows  "
             f"[{df['date'].min().date()} → {df['date'].max().date()}]  "
             f"sensors: {sorted(df['sensor_id'].unique().tolist())}")
    return df


def load_climate_modes() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """MEI + DMI (monthly) + MJO RMM (daily). Missing files → empty DF."""
    mei = pd.read_csv(CLIMATE_DIR / "mei_v2.csv") if (CLIMATE_DIR / "mei_v2.csv").exists() else pd.DataFrame()
    dmi = pd.read_csv(CLIMATE_DIR / "dmi.csv")    if (CLIMATE_DIR / "dmi.csv").exists()    else pd.DataFrame()
    mjo = pd.read_csv(CLIMATE_DIR / "mjo_rmm.csv") if (CLIMATE_DIR / "mjo_rmm.csv").exists() else pd.DataFrame()
    log.info(f"  climate modes: MEI={len(mei):,}, DMI={len(dmi):,}, MJO={len(mjo):,}")
    if not mjo.empty:
        mjo["date"] = pd.to_datetime(mjo["date"])
    return mei, dmi, mjo


def load_modis_aod_monthly() -> pd.Series:
    """Load all MODIS MAIAC AOD monthly tifs from data/raw/modis_aod/, take
    the bbox mean per file, return a Series indexed by month_start date.

    Bypasses v1's broken `aod_modis` column. Re-export 2026-05-17 populated
    the 2019+ tifs (previously empty due to MODIS/006 deprecation)."""
    if not MODIS_RAW_DIR.exists():
        return pd.Series(dtype="float64", name="aod_maiac_monthly")
    try:
        import rasterio
    except ImportError:
        log.warning("  rasterio not installed — falling back to v1 aod_modis column")
        return pd.Series(dtype="float64", name="aod_maiac_monthly")

    rows: list[tuple[pd.Timestamp, float]] = []
    for f in sorted(MODIS_RAW_DIR.glob("modis_aod_kandy_*.tif")):
        name = f.stem.split("_")[-1]   # YYYYMM
        if len(name) != 6 or not name.isdigit():
            continue
        year, month = int(name[:4]), int(name[4:])
        try:
            with rasterio.open(f) as r:
                a = r.read(1)
                v = a[~np.isnan(a)] if a.dtype.kind == "f" else a.ravel()
                mean = float(v.mean()) if len(v) > 0 else np.nan
        except Exception as e:
            log.warning(f"  tif read failed {f.name}: {e}")
            mean = np.nan
        rows.append((pd.Timestamp(year=year, month=month, day=1), mean))

    if not rows:
        return pd.Series(dtype="float64", name="aod_maiac_monthly")
    s = pd.Series({d: v for d, v in rows}, name="aod_maiac_monthly").sort_index()
    n_valid = s.notna().sum()
    log.info(f"  MODIS AOD monthly: {len(s)} files, {n_valid} non-NaN  "
             f"[{s.index.min().date()} → {s.index.max().date()}]")
    return s


def load_geos_cf_kandy() -> pd.DataFrame:
    """GEOS-CF Kandy CSVs (one per year, populated by download_geos_cf_kandy.py
    after GEE → Drive → local download). Returns hourly DataFrame with columns
    [date, geos_cf_pm25_raw] aggregated to daily means; empty if not yet downloaded."""
    if not GEOS_CF_PROC_DIR.exists():
        log.info(f"  GEOS-CF dir not present yet: {GEOS_CF_PROC_DIR}  → geos_cf_pm25_raw = NaN")
        return pd.DataFrame()
    csvs = sorted(GEOS_CF_PROC_DIR.glob("kandy_geos_cf_*.csv"))
    if not csvs:
        log.info(f"  GEOS-CF CSVs not downloaded yet  → geos_cf_pm25_raw = NaN")
        return pd.DataFrame()
    parts = []
    for f in csvs:
        try:
            d = pd.read_csv(f)
            parts.append(d)
        except Exception as e:
            log.warning(f"  failed to read {f.name}: {e}")
    if not parts:
        return pd.DataFrame()
    raw = pd.concat(parts, ignore_index=True)
    raw["datetime"] = pd.to_datetime(raw["datetime"])
    raw["date"] = raw["datetime"].dt.normalize()
    # Daily mean across hourly values
    daily = (raw.groupby("date")["PM25_RH35_GCC"]
                .mean()
                .rename("geos_cf_pm25_raw")
                .reset_index())
    log.info(f"  GEOS-CF daily: {len(daily):,} rows  "
             f"[{daily['date'].min().date()} → {daily['date'].max().date()}]")
    return daily


# ─────────────────────────────────────────────────────────────────────────────
# Feature builders
# ─────────────────────────────────────────────────────────────────────────────

def build_ventilation(v1: pd.DataFrame) -> pd.DataFrame:
    """Group A — 5 features."""
    out = pd.DataFrame(index=v1.index)
    out["wind_speed_10m"]         = v1["wind_speed"]
    out["blh_era5"]               = v1["blh_mean"]
    out["ventilation_coefficient"] = v1["wind_speed"] * v1["blh_mean"]
    out["lapse_rate_t925_t2m"]    = v1["t925"] - v1["t2m"]
    # Guard against degenerate blh_max=0
    blh_max_safe = v1["blh_max"].clip(lower=1.0)
    out["nocturnal_blh_ratio"]    = v1["blh_min"] / blh_max_safe
    return out


def compute_wind_into_blocked_sector(wind_dir_deg: pd.Series, wind_speed: pd.Series) -> pd.Series:
    """Vector TBI: wind speed × fraction-into-blocked-sector smooth indicator.

    The Hantana ridge blocks winds blowing FROM the S/SSW (175°–195°). Compute:
        f(ψ) = max(0, cos(ψ − 185°))                # smooth 1-at-center, 0 at ±90°
                                                    # restricted to the blocked arc
        wind_into_blocked_sector = f(ψ) × ws        # weighted by speed

    This replaces v1's scalar `terrain_blocking_idx` (SHAP #35, low signal) with
    a feature that actually responds to today's wind direction.
    """
    psi = np.deg2rad(wind_dir_deg.values)
    center = np.deg2rad(0.5 * (BLOCKED_SECTOR_MIN_DEG + BLOCKED_SECTOR_MAX_DEG))   # 185°
    # Smooth weight peaking at center, zero outside ±10° of arc.
    half_arc = np.deg2rad(0.5 * (BLOCKED_SECTOR_MAX_DEG - BLOCKED_SECTOR_MIN_DEG))  # 10°
    delta = np.abs(np.arctan2(np.sin(psi - center), np.cos(psi - center)))          # |angle diff| in [0, π]
    weight = np.where(delta < half_arc, np.cos(delta * np.pi / (2 * half_arc)), 0.0)
    return pd.Series(weight * wind_speed.values, index=wind_dir_deg.index,
                     name="wind_into_blocked_sector")


def build_valley_transport(v1: pd.DataFrame) -> pd.DataFrame:
    """Group B — 4 features."""
    out = pd.DataFrame(index=v1.index)
    out["wind_along_corridor"] = v1["wind_along"]
    out["wind_cross_corridor"] = v1["wind_cross"]
    out["wind_into_blocked_sector"] = compute_wind_into_blocked_sector(
        v1["wind_dir"], v1["wind_speed"])
    # Valley drainage proxy: stable layer × low wind allows cold-air drainage.
    lapse = (v1["t925"] - v1["t2m"]).clip(lower=0.0)    # only stable cases contribute
    ws_safe = v1["wind_speed"].clip(lower=0.1)
    out["valley_drainage_index"] = lapse / ws_safe
    return out


def build_wet_scavenging(v1: pd.DataFrame) -> pd.DataFrame:
    """Group C — 3 features. v1 has daily `tp` (total precip)."""
    out = pd.DataFrame(index=v1.index)
    tp = v1["tp"].fillna(0.0)
    out["precip_24h"] = tp
    out["precip_7d"]  = tp.rolling(window=7,  min_periods=1).sum()
    # dry_spell_days: consecutive days with tp < 1mm. Reset to 0 on wet days.
    wet = tp >= 0.001          # ERA5 tp is in m; 1mm = 0.001m
    # Build running counter of dry-days-since-last-wet:
    grp = wet.cumsum()         # increments on wet day → groups dry runs
    out["dry_spell_days"] = (~wet).groupby(grp).cumsum()
    return out


def build_source_column(v1: pd.DataFrame, aod_monthly: pd.Series) -> pd.DataFrame:
    """Group D — 4 features.

    aod_maiac: monthly-mean MAIAC AOD broadcast to every day in that month
               (per pre-reg 2026-05-17 amendment — MODIS raw is monthly).
               Bypasses v1's broken `aod_modis` column.
    aod_blh_ratio: computed from new monthly AOD / BLH (replaces v1's column
               which was also dependent on the broken AOD).
    no2_column: TROPOMI 2018+ from v1 (OMI backfill pending for pre-2018).
    fire_count_5d: NaN pending VIIRS GEE export (v2.1 follow-up).
    """
    out = pd.DataFrame(index=v1.index)

    # Broadcast monthly AOD to daily by (year, month)
    if not aod_monthly.empty:
        aod_indexed = aod_monthly.copy()
        aod_indexed.index = pd.MultiIndex.from_arrays(
            [aod_indexed.index.year, aod_indexed.index.month],
            names=["year", "month"]
        )
        months = pd.MultiIndex.from_arrays(
            [v1.index.year, v1.index.month], names=["year", "month"]
        )
        out["aod_maiac"] = aod_indexed.reindex(months).values
    else:
        out["aod_maiac"] = np.nan

    # Re-derive AOD/BLH ratio on the new AOD column
    blh_safe = v1["blh_mean"].clip(lower=1.0)
    out["aod_blh_ratio"] = out["aod_maiac"] / blh_safe

    out["no2_column"]    = v1["tropomi_no2"]
    out["fire_count_5d"] = np.nan
    return out


def build_priors(v1: pd.DataFrame, geos: pd.DataFrame) -> pd.DataFrame:
    """Group E — 3 features.

    cams_pm25_raw is backed out from v1's KOALA-corrected `pm25_observed`:
    v1 applies a single flat multiplier (CAMS_BIAS_FACTOR_FLAT = 0.5984) to
    raw CAMS, so cams_pm25_raw = pm25_observed / 0.5984.

    Verified via config.py: ratio = KOALA_ANCHOR / CAMS_2019_mean = 24.5225/40.98."""
    out = pd.DataFrame(index=v1.index)
    out["cams_pm25_raw"] = v1["pm25_observed"] / CAMS_BIAS_FACTOR_FLAT

    if not geos.empty:
        g = geos.set_index("date")["geos_cf_pm25_raw"]
        out["geos_cf_pm25_raw"] = g.reindex(out.index)
    else:
        out["geos_cf_pm25_raw"] = np.nan

    out["prior_disagreement"] = (out["cams_pm25_raw"] - out["geos_cf_pm25_raw"]).abs()
    return out


def build_climate_modes(v1: pd.DataFrame, mei: pd.DataFrame, dmi: pd.DataFrame,
                        mjo: pd.DataFrame) -> pd.DataFrame:
    """Group F — 4 features.

    MEI and DMI are monthly → broadcast to daily by (year, month) merge.
    MJO RMM is daily → direct date merge.
    MJO has a 2024-02-24 cutoff (BoM stopped public realtime updates)."""
    out = pd.DataFrame(index=v1.index)
    months = pd.DataFrame({
        "year":  v1.index.year,
        "month": v1.index.month,
    }, index=v1.index)

    if not mei.empty:
        mei_indexed = mei.set_index(["year", "month"])["mei"]
        mei_daily = months.apply(lambda r: mei_indexed.get((int(r["year"]), int(r["month"])), np.nan), axis=1)
        # Sin/cos of MEI phase by month (12-month cycle)
        out["mei_sin"] = np.sin(2 * np.pi * months["month"] / 12.0)
        out["mei_cos"] = np.cos(2 * np.pi * months["month"] / 12.0)
        # Modulate by MEI value (this preserves v1's mei_month_sin/cos semantics)
        out["mei_sin"] = out["mei_sin"] * mei_daily.values
        out["mei_cos"] = out["mei_cos"] * mei_daily.values
    else:
        out["mei_sin"] = np.nan
        out["mei_cos"] = np.nan

    if not dmi.empty:
        dmi_indexed = dmi.set_index(["year", "month"])["dmi"]
        out["iod_dmi"] = months.apply(
            lambda r: dmi_indexed.get((int(r["year"]), int(r["month"])), np.nan), axis=1).values
    else:
        out["iod_dmi"] = np.nan

    if not mjo.empty:
        mjo_indexed = mjo.set_index("date")["amplitude"]
        out["mjo_amplitude"] = mjo_indexed.reindex(out.index).values
    else:
        out["mjo_amplitude"] = np.nan

    return out


def build_temporal_date_keyed(v1: pd.DataFrame) -> pd.DataFrame:
    """Group G — 2 of 5 features that are pure date-keyed (doy sin/cos).
    The lag features are per-station and computed AFTER the multi-station merge."""
    out = pd.DataFrame(index=v1.index)
    doy = v1.index.dayofyear.astype(float)
    out["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    out["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    return out


def add_per_station_lags(merged: pd.DataFrame) -> pd.DataFrame:
    """Per-sensor lag features. Sorted by sensor then date; rolling per group.

    pm25_lag_1d:     previous day's obs at the same sensor
    pm25_lag_7d_mean: rolling mean of last 7 days at the same sensor
    pm25_lag_30d_mean: rolling mean of last 30 days at the same sensor

    Lags are computed from OBSERVED PM2.5 only (per pre-reg §4 footnote — never
    from model predictions). On the first day of each sensor's coverage, lags
    are NaN; XGBoost handles natively."""
    merged = merged.sort_values(["sensor_id", "date"]).reset_index(drop=True)
    g = merged.groupby("sensor_id", sort=False)["pm25_observed"]
    merged["pm25_lag_1d"]      = g.shift(1)
    merged["pm25_lag_7d_mean"] = g.shift(1).rolling(window=7,  min_periods=1).mean().reset_index(level=0, drop=True)
    merged["pm25_lag_30d_mean"] = g.shift(1).rolling(window=30, min_periods=1).mean().reset_index(level=0, drop=True)
    return merged


# ─────────────────────────────────────────────────────────────────────────────
# Multi-station expansion
# ─────────────────────────────────────────────────────────────────────────────

def assemble_multi_station(features_daily: pd.DataFrame, fect: pd.DataFrame) -> pd.DataFrame:
    """Inner-join FECT daily (sensor-keyed) against features_daily (date-keyed).
    Adds per-sensor elevation; canonical label = pm25_observed_barkjohn_clim_rh."""
    # FECT daily has lat/lon/sensor_id/sensor_name/region.
    f = fect.copy()
    f["pm25_observed"] = f["pm25_observed_barkjohn_clim_rh"]
    f["elevation_m"]   = f["sensor_id"].map(SENSOR_ELEVATION_M).astype(float)

    keep_fect = [
        "date", "sensor_id", "sensor_name", "lat", "lon", "elevation_m", "region",
        "pm25_observed",
        # Calibration variants retained for sensitivity (pre-reg §6.1)
        "pm25_observed_barkjohn",
        "pm25_observed_anchor_self",
        "pm25_observed_anchor_hantana",
        "n_hours", "frac_high_rh",
    ]
    keep_fect = [c for c in keep_fect if c in f.columns]
    f = f[keep_fect]

    # features_daily is indexed by date — make it a column
    feats = features_daily.reset_index().rename(columns={"index": "date"})
    if "date" not in feats.columns:
        # Index name may be 'date' already; reset_index put it as a column
        feats = features_daily.copy()
        feats.index.name = "date"
        feats = feats.reset_index()

    merged = f.merge(feats, on="date", how="left")
    log.info(f"  multi-station merged: {merged.shape[0]:,} rows × {merged.shape[1]} cols")
    return merged


# ─────────────────────────────────────────────────────────────────────────────
# Provenance
# ─────────────────────────────────────────────────────────────────────────────

PROVENANCE = [
    # (col_name, group, source, derivation, notes)
    ("wind_speed_10m",          "A", "ERA5 u10/v10",                 "v1.wind_speed (copy)",                              ""),
    ("blh_era5",                "A", "ERA5 BLH",                     "v1.blh_mean (copy)",                                ""),
    ("ventilation_coefficient", "A", "ERA5",                          "v1.wind_speed * v1.blh_mean",                       "Holzworth 1967"),
    ("lapse_rate_t925_t2m",     "A", "ERA5 t925/t2m",                "v1.t925 - v1.t2m",                                  "static stability"),
    ("nocturnal_blh_ratio",     "A", "ERA5 BLH",                     "v1.blh_min / clip(v1.blh_max, lower=1)",            "diurnal mixing collapse"),

    ("wind_along_corridor",     "B", "ERA5 wind decomp",             "v1.wind_along (copy)",                              "Mahaweli WNW-NW"),
    ("wind_cross_corridor",     "B", "ERA5 wind decomp",             "v1.wind_cross (copy)",                              ""),
    ("wind_into_blocked_sector","B", "ERA5 wind_dir + ws + DEM",     "smooth-weighted projection into S/SSW arc",         "vector TBI replacing v1 scalar"),
    ("valley_drainage_index",   "B", "ERA5 t925/t2m, ws",            "max(lapse,0) / clip(ws, 0.1)",                      "cold-air drainage"),

    ("precip_24h",              "C", "ERA5 tp",                      "v1.tp (copy, NaN→0)",                               ""),
    ("precip_7d",               "C", "ERA5 tp",                      "rolling 7d sum of tp",                              ""),
    ("dry_spell_days",          "C", "ERA5 tp",                      "running count of consecutive days with tp<1mm",     ""),

    ("aod_maiac",               "D", "MODIS MAIAC",                  "v1.aod_modis (renamed)",                            "1km daily; many NaN"),
    ("aod_blh_ratio",           "D", "MODIS/ERA5",                   "v1.aod_blh_ratio (copy)",                           "Liu 2005"),
    ("no2_column",              "D", "TROPOMI L3",                   "v1.tropomi_no2 (copy)",                             "2018-10+ only"),
    ("fire_count_5d",           "D", "VIIRS",                         "**PENDING** GEE VIIRS export",                      "Phase 2"),

    ("cams_pm25_raw",           "E", "CAMS EAC4",                    "v1.pm25_observed / CAMS_BIAS_FACTOR_FLAT",          "back-out of KOALA-corrected v1 label"),
    ("geos_cf_pm25_raw",        "E", "GEOS-CF replay tavg1hr",        "daily mean of GEE export (download_geos_cf_kandy)", "PENDING GEE → Drive → local download"),
    ("prior_disagreement",      "E", "derived",                       "|cams - geos|",                                     "NaN until GEOS-CF arrives"),

    ("mei_sin",                 "F", "NOAA PSL MEI v2",              "sin(2π·month/12) · MEI",                            "v1 had pure sin/cos; v2 modulates by MEI value"),
    ("mei_cos",                 "F", "NOAA PSL MEI v2",              "cos(2π·month/12) · MEI",                            "see above"),
    ("iod_dmi",                 "F", "NOAA PSL HadISST DMI",         "monthly DMI broadcast to daily",                    "Saji 1999"),
    ("mjo_amplitude",           "F", "BoM RMM",                       "daily amplitude",                                   "**2024-02-24 cutoff** (BoM paused)"),

    ("pm25_lag_1d",             "G", "FECT calibrated obs",          "groupby(sensor_id).shift(1)",                       "per-station"),
    ("pm25_lag_7d_mean",        "G", "FECT calibrated obs",          "shift(1).rolling(7).mean() per sensor",             "per-station"),
    ("pm25_lag_30d_mean",       "G", "FECT calibrated obs",          "shift(1).rolling(30).mean() per sensor",            "per-station"),
    ("doy_sin",                 "G", "calendar",                      "sin(2π·doy/365.25)",                                ""),
    ("doy_cos",                 "G", "calendar",                      "cos(2π·doy/365.25)",                                ""),
]


def write_provenance(merged: pd.DataFrame) -> None:
    rows = []
    for col, grp, src, deriv, notes in PROVENANCE:
        s = merged[col] if col in merged.columns else pd.Series(dtype="float64")
        rows.append({
            "feature":  col,
            "group":    grp,
            "source":   src,
            "derivation": deriv,
            "n_rows":   len(s),
            "n_nan":    int(s.isna().sum()),
            "frac_nan": float(s.isna().mean()) if len(s) else float("nan"),
            "min":      float(s.min()) if s.notna().any() else float("nan"),
            "max":      float(s.max()) if s.notna().any() else float("nan"),
            "notes":    notes,
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT_PROVENANCE, index=False)
    log.info(f"  wrote {OUT_PROVENANCE}  ({len(out)} features)")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite outputs")
    args = ap.parse_args()

    if OUT_DAILY.exists() and not args.force:
        log.warning(f"{OUT_DAILY} exists — use --force to rebuild")
        return

    log.info("── load ──")
    v1 = load_v1_features()
    fect = load_fect_daily()
    mei, dmi, mjo = load_climate_modes()
    geos = load_geos_cf_kandy()
    aod_monthly = load_modis_aod_monthly()

    log.info("── build features (date-keyed) ──")
    features = pd.concat([
        build_ventilation(v1),
        build_valley_transport(v1),
        build_wet_scavenging(v1),
        build_source_column(v1, aod_monthly),
        build_priors(v1, geos),
        build_climate_modes(v1, mei, dmi, mjo),
        build_temporal_date_keyed(v1),
    ], axis=1)
    log.info(f"  features (date-keyed): {features.shape[0]:>5,} rows × {features.shape[1]} cols")

    log.info("── multi-station expansion + per-sensor lags ──")
    merged = assemble_multi_station(features, fect)
    merged = add_per_station_lags(merged)

    # Final column ordering: meta → features grouped → label
    feature_order = [c for c, *_ in PROVENANCE]
    meta_cols = ["date", "sensor_id", "sensor_name", "lat", "lon", "elevation_m", "region"]
    label_col = ["pm25_observed"]
    calib_variants = ["pm25_observed_barkjohn", "pm25_observed_anchor_self",
                      "pm25_observed_anchor_hantana", "n_hours", "frac_high_rh"]
    final_cols = (meta_cols
                  + [c for c in feature_order if c in merged.columns]
                  + label_col
                  + [c for c in calib_variants if c in merged.columns])
    merged = merged[[c for c in final_cols if c in merged.columns]].copy()

    merged.to_parquet(OUT_DAILY, index=False)
    log.info(f"  wrote {OUT_DAILY}  ({merged.shape[0]:,} rows × {merged.shape[1]} cols)")

    write_provenance(merged)

    # ── summary ──
    log.info("── feature availability summary ──")
    feat_only = [c for c in feature_order if c in merged.columns]
    n_total = len(merged)
    for c in feat_only:
        n_nan = int(merged[c].isna().sum())
        pct = 100.0 * n_nan / max(n_total, 1)
        flag = " ← all NaN, source missing" if n_nan == n_total else ""
        log.info(f"  {c:<28}  n_nan={n_nan:>5}  ({pct:5.1f}%){flag}")
    log.info(f"label pm25_observed:  n_nan={int(merged['pm25_observed'].isna().sum())} of {n_total}")
    log.info(f"date range: {merged['date'].min().date()} → {merged['date'].max().date()}")
    log.info(f"sensors:    {sorted(merged['sensor_id'].unique().tolist())}")


if __name__ == "__main__":
    main()
