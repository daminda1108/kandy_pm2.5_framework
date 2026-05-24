"""
predict_extrapolation_v2.py — 2003-2018 inference-only extrapolation.

OSF pre-registration §3.4 + §5.6: the v2 training window is 2019-2025
(GEOS-CF era). The 2003-2018 backward extension is "inference-only with
geos_cf_pm25_raw masked + predictive variance inflated by f_extrap = 1.5
+ extrapolation_flag = True".

Architecture:
  1. Build feature DataFrame from v1 merged parquet (2003-2018), climate
     modes, and the two FECT sensor coordinates. Lags + GEOS-CF + pre-2018
     TROPOMI = NaN per pre-reg §4 (no observed PM₂.₅ in the extrapolation
     window — XGBoost handles NaN natively).
  2. Apply trained quantile XGBoost (`xgboost_v2_full_kandy.ubj`) to the
     cartesian product of dates × sensors.
  3. Inflate PI width by f_extrap = 1.5 to reflect extrapolation uncertainty.
  4. Concatenate with in-window 2019-2025 LOMO predictions for a single
     22-year reconstruction series.
  5. Validate annual means against Van Donkelaar V6GL02.04 (from §6.3
     cross-product table).

Outputs:
  data/processed/stage1_v2/training/predictions_extrapolation_2003_2018.parquet
  data/processed/stage1_v2/training/predictions_22yr_2003_2025.parquet
  data/processed/stage1_v2/eda/cross_product_22yr_v2.csv

Usage:
  python -m src.stage1_satml.models.predict_extrapolation_v2
  python src/stage1_satml/models/predict_extrapolation_v2.py --force
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import PROC_DIR, RAW_DIR, MODELS_DIR, CAMS_BIAS_FACTOR_FLAT, LOG_FORMAT, LOG_DATEFMT

from src.stage1_satml.features.build_dataset_v2 import (
    compute_wind_into_blocked_sector, SENSOR_ELEVATION_M,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("predict_extrapolation_v2")

# ─────────────────────────────────────────────────────────────────────────────
# Constants & paths
# ─────────────────────────────────────────────────────────────────────────────

V1_MERGED   = PROC_DIR / "merged" / "dataset_daily.parquet"
CLIMATE_DIR = RAW_DIR / "climate_modes"
MODEL_PATH  = MODELS_DIR / "xgboost_v2_full_kandy.ubj"

LOMO_PREDS  = PROC_DIR / "stage1_v2" / "training" / "predictions_lomo_v2.parquet"
CROSS_PROD  = PROC_DIR / "stage1_v2" / "eda" / "cross_product_annual_means_v2.csv"

OUT_DIR     = PROC_DIR / "stage1_v2" / "training"
OUT_EXTRA   = OUT_DIR / "predictions_extrapolation_2003_2018.parquet"
OUT_22YR    = OUT_DIR / "predictions_22yr_2003_2025.parquet"
OUT_VALID   = PROC_DIR / "stage1_v2" / "eda" / "cross_product_22yr_v2.csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Pre-reg §5.6: predictive variance inflated by f_extrap=1.5 in the
# extrapolation window to reflect missing observed lags + missing GEOS-CF.
F_EXTRAP = 1.5

# FECT sensors that the trained model expects in (lat, lon, elevation) form
# (excluding TR7 which is the dropped sensor per pre-reg §3.1).
EXTRAP_SENSORS = [
    (12451, "FECT_Akurana",      7.366, 80.618, 1538.0, "kandy"),
    (33495, "FECT_Hantana_TR4",  7.356, 80.631, 1698.0, "kandy"),
]

EXTRAP_START = "2003-01-01"
EXTRAP_END   = "2018-12-31"


# ─────────────────────────────────────────────────────────────────────────────
# Feature builders (date-keyed)
# ─────────────────────────────────────────────────────────────────────────────

def build_extrapolation_features() -> pd.DataFrame:
    """Build the date-keyed feature table for 2003-2018 from v1 merged + climate modes."""
    log.info("── load v1 merged parquet (2003-2018) ──")
    v1 = pd.read_parquet(V1_MERGED)
    v1 = v1.loc[EXTRAP_START:EXTRAP_END].copy()
    log.info(f"  v1 2003-2018: {v1.shape}")

    f = pd.DataFrame(index=v1.index)

    # Group A — Ventilation
    f["wind_speed_10m"]          = v1["wind_speed"]
    f["blh_era5"]                = v1["blh_mean"]
    f["ventilation_coefficient"] = v1["wind_speed"] * v1["blh_mean"]
    f["lapse_rate_t925_t2m"]     = v1["t925"] - v1["t2m"]
    f["nocturnal_blh_ratio"]     = v1["blh_min"] / v1["blh_max"].clip(lower=1.0)

    # Group B — Valley transport
    f["wind_along_corridor"] = v1["wind_along"]
    f["wind_cross_corridor"] = v1["wind_cross"]
    f["wind_into_blocked_sector"] = compute_wind_into_blocked_sector(
        v1["wind_dir"], v1["wind_speed"])
    lapse = (v1["t925"] - v1["t2m"]).clip(lower=0.0)
    ws_safe = v1["wind_speed"].clip(lower=0.1)
    f["valley_drainage_index"] = lapse / ws_safe

    # Group C — Wet scavenging
    tp = v1["tp"].fillna(0.0)
    f["precip_24h"] = tp
    f["precip_7d"]  = tp.rolling(window=7, min_periods=1).sum()
    wet = tp >= 0.001
    grp = wet.cumsum()
    f["dry_spell_days"] = (~wet).groupby(grp).cumsum()

    # Group D — Source / column
    f["aod_maiac"]     = v1["aod_modis"]
    f["aod_blh_ratio"] = v1["aod_blh_ratio"]
    f["no2_column"]    = v1["tropomi_no2"]   # NaN before Oct 2017
    f["fire_count_5d"] = np.nan

    # Group E — Multi-fidelity priors
    f["cams_pm25_raw"]    = v1["pm25_observed"] / CAMS_BIAS_FACTOR_FLAT
    f["geos_cf_pm25_raw"] = np.nan           # Per pre-reg §3.4 — masked in extrapolation
    f["prior_disagreement"] = np.nan

    # Group F — Climate modes (broadcast monthly → daily)
    mei = pd.read_csv(CLIMATE_DIR / "mei_v2.csv") if (CLIMATE_DIR / "mei_v2.csv").exists() else pd.DataFrame()
    dmi = pd.read_csv(CLIMATE_DIR / "dmi.csv")    if (CLIMATE_DIR / "dmi.csv").exists()    else pd.DataFrame()
    mjo = pd.read_csv(CLIMATE_DIR / "mjo_rmm.csv") if (CLIMATE_DIR / "mjo_rmm.csv").exists() else pd.DataFrame()
    if not mjo.empty:
        mjo["date"] = pd.to_datetime(mjo["date"])

    months = pd.DataFrame({"year": f.index.year, "month": f.index.month}, index=f.index)
    if not mei.empty:
        mei_idx = mei.set_index(["year", "month"])["mei"]
        mei_daily = months.apply(
            lambda r: mei_idx.get((int(r["year"]), int(r["month"])), np.nan), axis=1)
        f["mei_sin"] = np.sin(2 * np.pi * months["month"] / 12.0) * mei_daily.values
        f["mei_cos"] = np.cos(2 * np.pi * months["month"] / 12.0) * mei_daily.values
    else:
        f["mei_sin"] = np.nan; f["mei_cos"] = np.nan

    if not dmi.empty:
        dmi_idx = dmi.set_index(["year", "month"])["dmi"]
        f["iod_dmi"] = months.apply(
            lambda r: dmi_idx.get((int(r["year"]), int(r["month"])), np.nan), axis=1).values
    else:
        f["iod_dmi"] = np.nan

    if not mjo.empty:
        mjo_idx = mjo.set_index("date")["amplitude"]
        f["mjo_amplitude"] = mjo_idx.reindex(f.index).values
    else:
        f["mjo_amplitude"] = np.nan

    # Group G — Temporal (lags = NaN per pre-reg §4 footnote; doy from calendar)
    f["pm25_lag_1d"]       = np.nan
    f["pm25_lag_7d_mean"]  = np.nan
    f["pm25_lag_30d_mean"] = np.nan
    doy = f.index.dayofyear.astype(float)
    f["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    f["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)

    log.info(f"  built {len(f)} daily feature rows ({f.shape[1]} cols)")
    return f


def cross_with_sensors(features: pd.DataFrame) -> pd.DataFrame:
    """Cartesian product: per (date, sensor) row carries the sensor's (lat, lon, elev)."""
    rows = []
    f_reset = features.reset_index().rename(columns={"index": "date"})
    if "date" not in f_reset.columns:
        f_reset = features.copy()
        f_reset.index.name = "date"
        f_reset = f_reset.reset_index()
    for sid, name, lat, lon, elev, region in EXTRAP_SENSORS:
        sub = f_reset.copy()
        sub["sensor_id"]   = sid
        sub["sensor_name"] = name
        sub["lat"]         = lat
        sub["lon"]         = lon
        sub["elevation_m"] = elev
        sub["region"]      = region
        rows.append(sub)
    out = pd.concat(rows, ignore_index=True)
    log.info(f"  cartesian (date × {len(EXTRAP_SENSORS)} sensors): {len(out):,} rows")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Inference
# ─────────────────────────────────────────────────────────────────────────────

def run_inference(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the trained quantile XGBoost. Inflate PI by F_EXTRAP."""
    log.info(f"── load model: {MODEL_PATH.name} ──")
    model = xgb.XGBRegressor()
    model.load_model(MODEL_PATH)
    feats = model.get_booster().feature_names or []
    log.info(f"  model expects {len(feats)} features")

    # Align column set (NaN-fill any missing)
    missing = [f for f in feats if f not in df.columns]
    if missing:
        log.warning(f"  features missing from extrap dataset (set to NaN): {missing}")
        for c in missing:
            df[c] = np.nan
    X = df[feats].astype(np.float32)
    q = model.predict(X)            # (n, 3) = [q05, q50, q95]
    df["xgb_q05_raw"] = q[:, 0]
    df["xgb_q50"]     = q[:, 1]
    df["xgb_q95_raw"] = q[:, 2]

    # Inflate PI width by F_EXTRAP around the median, per pre-reg §5.6
    df["xgb_q05"] = df["xgb_q50"] - F_EXTRAP * (df["xgb_q50"] - df["xgb_q05_raw"])
    df["xgb_q95"] = df["xgb_q50"] + F_EXTRAP * (df["xgb_q95_raw"] - df["xgb_q50"])
    df["xgb_q05"] = df["xgb_q05"].clip(lower=0)      # PM cannot be negative
    df["extrapolation_flag"] = True

    log.info(f"  inferred {len(df):,} predictions  "
             f"q50: mean={df['xgb_q50'].mean():.2f}, "
             f"p05-p95 band mean width={(df['xgb_q95']-df['xgb_q05']).mean():.2f} µg/m³")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 22-year time-series assembly + Van Donkelaar validation
# ─────────────────────────────────────────────────────────────────────────────

def assemble_22yr(extra: pd.DataFrame) -> pd.DataFrame:
    """Concatenate 2003-2018 extrapolation + 2019-2025 in-window LOMO."""
    log.info("── assemble 22-yr series ──")
    in_window = pd.read_parquet(LOMO_PREDS)
    in_window["date"] = pd.to_datetime(in_window["date"])
    in_window["extrapolation_flag"] = False
    in_window["xgb_q05_raw"] = in_window["xgb_q05"]
    in_window["xgb_q95_raw"] = in_window["xgb_q95"]
    log.info(f"  in-window (2019-2025): {len(in_window):,} rows")

    extra = extra.copy()
    extra["date"] = pd.to_datetime(extra["date"])

    common_cols = ["date", "sensor_id", "xgb_q05", "xgb_q50", "xgb_q95",
                   "xgb_q05_raw", "xgb_q95_raw", "extrapolation_flag"]
    full = pd.concat([extra[common_cols], in_window[common_cols]], ignore_index=True)
    full = full.sort_values(["date", "sensor_id"]).reset_index(drop=True)
    log.info(f"  22-yr full: {len(full):,} sensor-day rows  "
             f"[{full['date'].min().date()} → {full['date'].max().date()}]")
    return full


def validate_vs_vand(full: pd.DataFrame) -> pd.DataFrame:
    """Compare extrapolated annual means against Van Donkelaar V6GL02.04."""
    log.info("── validate 2003-2018 annual means vs Van Donkelaar ──")
    full = full.copy()
    full["year"] = pd.to_datetime(full["date"]).dt.year

    # Domain-mean annual (mean of sensor predictions per day, then annual mean)
    daily_mean = full.groupby(["date"])["xgb_q50"].mean().reset_index()
    daily_mean["year"] = pd.to_datetime(daily_mean["date"]).dt.year
    annual_v2 = daily_mean.groupby("year")["xgb_q50"].mean().rename("v2_q50_22yr")

    # Merge with cross-product CSV
    cp = pd.read_csv(CROSS_PROD)
    out = cp.merge(annual_v2.reset_index(), on="year", how="outer").sort_values("year")
    out["v2_q50_22yr"] = out["v2_q50_22yr"].fillna(out["v2_q50"])  # use new if missing
    out.to_csv(OUT_VALID, index=False)
    log.info(f"  wrote {OUT_VALID}  ({len(out)} years)")

    # Triangulation: 2003-2018 v2_q50_22yr vs Van Donkelaar
    extrap_yrs = out[(out["year"] >= 2003) & (out["year"] <= 2018)].dropna(subset=["v2_q50_22yr", "van_donkelaar"])
    if len(extrap_yrs) > 3:
        v = extrap_yrs["v2_q50_22yr"].to_numpy()
        d = extrap_yrs["van_donkelaar"].to_numpy()
        r = float(np.corrcoef(v, d)[0, 1])
        bias = float((v - d).mean())
        rmse = float(np.sqrt(((v - d) ** 2).mean()))
        log.info(f"  extrapolation (2003-2018) vs VanD: n={len(extrap_yrs)}  "
                 f"r={r:+.3f}  bias={bias:+.2f}  RMSE={rmse:.2f} µg/m³")
        log.info(f"  v2 annual range:  {v.min():.1f}–{v.max():.1f}  (mean {v.mean():.2f})")
        log.info(f"  VanD annual range: {d.min():.1f}–{d.max():.1f}  (mean {d.mean():.2f})")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite existing outputs")
    args = ap.parse_args()

    if OUT_EXTRA.exists() and not args.force:
        log.warning(f"{OUT_EXTRA} exists — use --force to rebuild")
        return

    log.info("── build features (2003-2018) ──")
    features = build_extrapolation_features()

    log.info("── cartesian × sensors ──")
    df = cross_with_sensors(features)

    log.info("── inference (PI inflate × {:.1f}) ──".format(F_EXTRAP))
    df = run_inference(df)

    df.to_parquet(OUT_EXTRA, index=False)
    log.info(f"  wrote {OUT_EXTRA}  ({len(df):,} rows × {len(df.columns)} cols)")

    full = assemble_22yr(df)
    full.to_parquet(OUT_22YR, index=False)
    log.info(f"  wrote {OUT_22YR}  ({len(full):,} rows)")

    validate_vs_vand(full)

    log.info("done")


if __name__ == "__main__":
    main()
