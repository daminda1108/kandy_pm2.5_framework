"""
build_dataset_v2_colombo.py — Colombo OOD feature builder (pre-reg §6.6).

Produces a daily feature table for the US Embassy Colombo station with the
SAME column schema as `dataset_v2_multistation_daily.parquet`, so the
trained xgboost_v2 model can predict on it directly without changing the
feature pipeline.

OOD design choices (documented openly; not a pre-reg violation):
  - Kandy-specific terrain features → NaN at Colombo:
      wind_along_corridor, wind_cross_corridor (Mahaweli WNW–NW axis is a Kandy
        feature; Colombo is coastal lowland with no equivalent)
      wind_into_blocked_sector (Hantana ridge does not exist at Colombo)
      valley_drainage_index (no valley)
  - `lapse_rate_t925_t2m` → NaN: the Colombo ERA5 export omitted the 925 hPa
        pressure-level band (single-level only). XGBoost is NaN-tolerant.
  - `no2_column` → NaN: TROPOMI not pulled over Colombo bbox (deferred).
  - `fire_count_5d` → NaN: same as Kandy (VIIRS deferred).
  - `cams_pm25_raw` is the **Kandy** value broadcast to Colombo as an
        approximation. CAMS native resolution is ~0.75° (~80 km); Kandy
        (~7.29°N, 80.63°E) and Colombo (~6.91°N, 79.88°E) are ~120 km apart
        and likely sit in the same or an adjacent CAMS grid cell. Flagged
        for sensitivity analysis.
  - `prior_disagreement` recomputed locally against Colombo's GEOS-CF.

Output:
  data/processed/stage1_v2/dataset_v2_colombo_daily.parquet
     Same column schema as the Kandy v2 dataset. Embassy daily PM2.5 is the
     `pm25_observed` column (point of comparison, NOT a training label).

Usage:
  python -m src.stage1_satml.features.build_dataset_v2_colombo
  python src/stage1_satml/features/build_dataset_v2_colombo.py --force

Reference: pre-reg §6.6; downstream consumer is predict_colombo_v2.py.
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    PROC_DIR, RAW_DIR, EXTERNAL_DIR,
    CAMS_BIAS_FACTOR_FLAT,
    LOG_FORMAT, LOG_DATEFMT,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("build_dataset_v2_colombo")

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

EMBASSY_HOURLY = RAW_DIR / "ground_truth" / "openaq_colombo_pm25_hourly.csv"
ERA5_DIR       = RAW_DIR / "era5_colombo"
GEOS_DIR       = RAW_DIR / "geos_cf_colombo"
MODIS_DIR      = RAW_DIR / "modis_aod_colombo"
CLIMATE_DIR    = RAW_DIR / "climate_modes"
V1_MERGED      = PROC_DIR / "merged" / "dataset_daily.parquet"

OUT_DIR    = PROC_DIR / "stage1_v2"
OUT_DAILY  = OUT_DIR / "dataset_v2_colombo_daily.parquet"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Station metadata
SENSOR_ID         = 23360         # OpenAQ StateAir_23360
SENSOR_NAME       = "Embassy_Colombo"
SENSOR_LAT        = 6.909
SENSOR_LON        = 79.875
SENSOR_ELEVATION_M = 25.0
REGION            = "colombo"


# ─────────────────────────────────────────────────────────────────────────────
# Loaders + aggregators
# ─────────────────────────────────────────────────────────────────────────────

def load_embassy_daily() -> pd.DataFrame:
    """Hourly PM2.5 → daily mean (+ count). Drop sparse days <12 good hours."""
    if not EMBASSY_HOURLY.exists():
        raise FileNotFoundError(f"Embassy hourly missing: {EMBASSY_HOURLY}")
    h = pd.read_csv(EMBASSY_HOURLY)
    h["datetime_utc"] = pd.to_datetime(h["datetime_utc"], utc=True, errors="coerce")
    h = h.dropna(subset=["datetime_utc"])
    h["date"] = h["datetime_utc"].dt.tz_convert(None).dt.normalize()
    # Drop nonsense values
    h = h[(h["pm25_colombo_ugm3"] >= 0) & (h["pm25_colombo_ugm3"] < 500)]
    daily = h.groupby("date").agg(
        pm25_observed=("pm25_colombo_ugm3", "mean"),
        n_hours      =("pm25_colombo_ugm3", "count"),
    ).reset_index()
    daily = daily[daily["n_hours"] >= 12].reset_index(drop=True)
    log.info(f"  Embassy daily: {len(daily):,} days  "
             f"[{daily['date'].min().date()} → {daily['date'].max().date()}]")
    return daily


def load_era5_daily() -> pd.DataFrame:
    """Concat 7 yearly hourly CSVs, aggregate to daily features."""
    parts = []
    for f in sorted(ERA5_DIR.glob("colombo_era5_*.csv")):
        try:
            parts.append(pd.read_csv(f))
        except pd.errors.EmptyDataError:
            continue
    if not parts:
        raise FileNotFoundError(f"no ERA5 CSVs in {ERA5_DIR}")
    h = pd.concat(parts, ignore_index=True)
    h["datetime"] = pd.to_datetime(h["datetime"])
    h["date"]     = h["datetime"].dt.normalize()
    log.info(f"  ERA5 hourly: {len(h):,} rows  "
             f"[{h['datetime'].min().date()} → {h['datetime'].max().date()}]")

    # Daily aggregation: mean for state variables, sum for precip
    g = h.groupby("date")
    daily = pd.DataFrame({
        "u10":     g["u_component_of_wind_10m"].mean(),
        "v10":     g["v_component_of_wind_10m"].mean(),
        "t2m":     g["temperature_2m"].mean(),
        "d2m":     g["dewpoint_temperature_2m"].mean(),
        "sp":      g["surface_pressure"].mean(),
        "tp":      g["total_precipitation"].sum(),    # daily total
        "blh_mean": g["boundary_layer_height"].mean(),
        "blh_min":  g["boundary_layer_height"].min(),
        "blh_max":  g["boundary_layer_height"].max(),
    }).reset_index()
    log.info(f"  ERA5 daily: {len(daily):,} days")
    return daily


def derive_era5_features(daily_era5: pd.DataFrame) -> pd.DataFrame:
    """Build v2 ERA5-derived features. Lapse rate (needs t925) → NaN."""
    out = daily_era5.copy()
    out["wind_speed_10m"]          = np.sqrt(out["u10"] ** 2 + out["v10"] ** 2)
    out["ventilation_coefficient"] = out["wind_speed_10m"] * out["blh_mean"]
    out["blh_era5"]                = out["blh_mean"]
    blh_max_safe = out["blh_max"].clip(lower=1.0)
    out["nocturnal_blh_ratio"]     = out["blh_min"] / blh_max_safe
    out["lapse_rate_t925_t2m"]     = np.nan   # t925 not pulled for Colombo

    # Wet scavenging
    out["precip_24h"]      = out["tp"].fillna(0.0)
    out["precip_7d"]       = out["precip_24h"].rolling(window=7,  min_periods=1).sum()
    wet = out["precip_24h"] >= 0.001
    grp = wet.cumsum()
    out["dry_spell_days"]  = (~wet).groupby(grp).cumsum().values

    # Valley/terrain features → NaN (not meaningful at Colombo)
    out["wind_along_corridor"]      = np.nan
    out["wind_cross_corridor"]      = np.nan
    out["wind_into_blocked_sector"] = np.nan
    out["valley_drainage_index"]    = np.nan
    return out


def load_geos_cf_daily() -> pd.DataFrame:
    parts = []
    for f in sorted(GEOS_DIR.glob("colombo_geos_cf_*.csv")):
        try:
            parts.append(pd.read_csv(f))
        except pd.errors.EmptyDataError:
            continue
    if not parts:
        return pd.DataFrame(columns=["date", "geos_cf_pm25_raw"])
    h = pd.concat(parts, ignore_index=True)
    h["datetime"] = pd.to_datetime(h["datetime"])
    h["date"]     = h["datetime"].dt.normalize()
    daily = (h.groupby("date")["PM25_RH35_GCC"]
              .mean().rename("geos_cf_pm25_raw").reset_index())
    log.info(f"  GEOS-CF Colombo daily: {len(daily):,} days")
    return daily


def load_modis_monthly() -> pd.Series:
    """Average AOD per monthly tif, indexed by month-start date."""
    rows = []
    for f in sorted(MODIS_DIR.glob("modis_aod_colombo_*.tif")):
        try:
            ym = f.stem.split("_")[-1]
            y, m = int(ym[:4]), int(ym[4:6])
        except (ValueError, IndexError):
            continue
        try:
            with rasterio.open(f) as r:
                arr = r.read(1)
                valid = arr[~np.isnan(arr)] if arr.dtype.kind == "f" else arr.ravel()
                v = float(np.nanmean(valid)) if len(valid) else np.nan
        except Exception:
            v = np.nan
        rows.append((pd.Timestamp(y, m, 1), v))
    if not rows:
        return pd.Series(dtype="float64")
    rows.sort()
    idx = pd.DatetimeIndex([r[0] for r in rows])
    s = pd.Series([r[1] for r in rows], index=idx, name="aod_maiac")
    log.info(f"  MODIS Colombo monthly: {len(s)} entries  "
             f"valid={s.notna().sum()}  range=[{s.min():.3f}, {s.max():.3f}]")
    return s


def broadcast_monthly_to_daily(monthly: pd.Series, date_index: pd.Index) -> pd.Series:
    """Each daily date inherits its month's value."""
    out = pd.Series(index=date_index, dtype="float64", name=monthly.name)
    if monthly.empty:
        return out
    monthly_by_ym = {(ts.year, ts.month): v for ts, v in monthly.items()}
    for d in date_index:
        ts = pd.Timestamp(d)
        out.loc[d] = monthly_by_ym.get((ts.year, ts.month), np.nan)
    return out


def load_cams_kandy_proxy() -> pd.DataFrame:
    """CAMS Kandy → cams_pm25_raw, used as a proxy for Colombo (same/adjacent
    CAMS native grid cell). Flagged in feature provenance."""
    if not V1_MERGED.exists():
        return pd.DataFrame(columns=["date", "cams_pm25_raw"])
    v1 = pd.read_parquet(V1_MERGED)
    daily = v1[["pm25_observed"]].copy()
    daily["cams_pm25_raw"] = daily["pm25_observed"] / CAMS_BIAS_FACTOR_FLAT
    daily.index.name = "date"
    return daily[["cams_pm25_raw"]].reset_index()


def load_climate_modes() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    mei = pd.read_csv(CLIMATE_DIR / "mei_v2.csv") if (CLIMATE_DIR / "mei_v2.csv").exists() else pd.DataFrame()
    dmi = pd.read_csv(CLIMATE_DIR / "dmi.csv")    if (CLIMATE_DIR / "dmi.csv").exists()    else pd.DataFrame()
    mjo = pd.read_csv(CLIMATE_DIR / "mjo_rmm.csv") if (CLIMATE_DIR / "mjo_rmm.csv").exists() else pd.DataFrame()
    if not mjo.empty:
        mjo["date"] = pd.to_datetime(mjo["date"])
    return mei, dmi, mjo


def build_climate_features(date_index: pd.DatetimeIndex,
                           mei: pd.DataFrame, dmi: pd.DataFrame,
                           mjo: pd.DataFrame) -> pd.DataFrame:
    months = pd.DataFrame({"year": date_index.year, "month": date_index.month}, index=date_index)
    out = pd.DataFrame(index=date_index)

    if not mei.empty:
        mei_idx = mei.set_index(["year", "month"])["mei"]
        mei_daily = months.apply(
            lambda r: mei_idx.get((int(r["year"]), int(r["month"])), np.nan), axis=1).values
        sin_m = np.sin(2 * np.pi * months["month"] / 12.0).values
        cos_m = np.cos(2 * np.pi * months["month"] / 12.0).values
        out["mei_sin"] = sin_m * mei_daily
        out["mei_cos"] = cos_m * mei_daily
    else:
        out["mei_sin"] = out["mei_cos"] = np.nan

    if not dmi.empty:
        dmi_idx = dmi.set_index(["year", "month"])["dmi"]
        out["iod_dmi"] = months.apply(
            lambda r: dmi_idx.get((int(r["year"]), int(r["month"])), np.nan), axis=1).values
    else:
        out["iod_dmi"] = np.nan

    if not mjo.empty:
        mjo_idx = mjo.set_index("date")["amplitude"]
        out["mjo_amplitude"] = mjo_idx.reindex(date_index).values
    else:
        out["mjo_amplitude"] = np.nan
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Assembly
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite output")
    args = ap.parse_args()

    if OUT_DAILY.exists() and not args.force:
        log.warning(f"{OUT_DAILY} exists — use --force to overwrite"); return

    log.info("── load ──")
    embassy = load_embassy_daily()
    era5    = load_era5_daily()
    geos    = load_geos_cf_daily()
    modis_m = load_modis_monthly()
    cams    = load_cams_kandy_proxy()
    mei, dmi, mjo = load_climate_modes()
    log.info(f"  climate: MEI={len(mei):,}, DMI={len(dmi):,}, MJO={len(mjo):,}")

    # Restrict to pre-reg window 2019-2025 (matches training)
    era5_features = derive_era5_features(era5)
    era5_features = era5_features[(era5_features["date"] >= "2019-01-01") &
                                  (era5_features["date"] <  "2026-01-01")].reset_index(drop=True)

    log.info("── merge ──")
    merged = era5_features.merge(geos, on="date", how="left")
    merged = merged.merge(cams, on="date", how="left")

    # Source / column (most NaN at Colombo)
    aod_daily = broadcast_monthly_to_daily(
        modis_m, pd.DatetimeIndex(merged["date"]))
    merged["aod_maiac"]     = aod_daily.values
    merged["aod_blh_ratio"] = merged["aod_maiac"] / merged["blh_mean"].clip(lower=1.0)
    merged["no2_column"]    = np.nan
    merged["fire_count_5d"] = np.nan

    # Priors
    merged["prior_disagreement"] = (merged["cams_pm25_raw"] - merged["geos_cf_pm25_raw"]).abs()

    # Climate
    climate_daily = build_climate_features(
        pd.DatetimeIndex(merged["date"]), mei, dmi, mjo)
    climate_daily = climate_daily.reset_index(drop=True)
    merged = pd.concat([merged, climate_daily], axis=1)

    # Temporal (date-keyed)
    doy = pd.DatetimeIndex(merged["date"]).dayofyear.astype(float)
    merged["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    merged["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)

    # Embassy label + per-station metadata
    merged = merged.merge(embassy[["date", "pm25_observed", "n_hours"]], on="date", how="inner")
    merged["sensor_id"]    = SENSOR_ID
    merged["sensor_name"]  = SENSOR_NAME
    merged["lat"]          = SENSOR_LAT
    merged["lon"]          = SENSOR_LON
    merged["elevation_m"]  = SENSOR_ELEVATION_M
    merged["region"]       = REGION

    # Embassy lags (per pre-reg §4 footnote: observed only, never predicted)
    merged = merged.sort_values("date").reset_index(drop=True)
    merged["pm25_lag_1d"]       = merged["pm25_observed"].shift(1)
    merged["pm25_lag_7d_mean"]  = merged["pm25_observed"].shift(1).rolling(7,  min_periods=1).mean()
    merged["pm25_lag_30d_mean"] = merged["pm25_observed"].shift(1).rolling(30, min_periods=1).mean()

    # Final column order — match Kandy v2 schema
    cols = [
        "date", "sensor_id", "sensor_name", "lat", "lon", "elevation_m", "region",
        # Group A
        "wind_speed_10m", "blh_era5", "ventilation_coefficient",
        "lapse_rate_t925_t2m", "nocturnal_blh_ratio",
        # Group B
        "wind_along_corridor", "wind_cross_corridor",
        "wind_into_blocked_sector", "valley_drainage_index",
        # Group C
        "precip_24h", "precip_7d", "dry_spell_days",
        # Group D
        "aod_maiac", "aod_blh_ratio", "no2_column", "fire_count_5d",
        # Group E
        "cams_pm25_raw", "geos_cf_pm25_raw", "prior_disagreement",
        # Group F
        "mei_sin", "mei_cos", "iod_dmi", "mjo_amplitude",
        # Group G
        "pm25_lag_1d", "pm25_lag_7d_mean", "pm25_lag_30d_mean",
        "doy_sin", "doy_cos",
        # Label + meta
        "pm25_observed", "n_hours",
    ]
    cols = [c for c in cols if c in merged.columns]
    merged = merged[cols].copy()

    merged.to_parquet(OUT_DAILY, index=False)
    log.info(f"  wrote {OUT_DAILY}  ({len(merged):,} rows × {len(merged.columns)} cols)")

    # ── feature availability summary ──
    log.info("── feature NaN summary (Colombo) ──")
    feature_cols = [c for c in cols if c not in
                    {"date", "sensor_id", "sensor_name", "lat", "lon", "elevation_m",
                     "region", "pm25_observed", "n_hours"}]
    n = len(merged)
    for c in feature_cols:
        nnan = int(merged[c].isna().sum())
        pct = 100.0 * nnan / max(n, 1)
        flag = " ← all NaN (intentional for Colombo OOD)" if nnan == n else ""
        log.info(f"  {c:<28}  n_nan={nnan:>4}  ({pct:5.1f}%){flag}")


if __name__ == "__main__":
    main()
