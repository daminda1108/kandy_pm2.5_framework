"""
calibrate_fect.py — Calibrate FECT PurpleAir Kandy sensors against KOALA 2019.

Stage 1 v2 (per OSF pre-registration docs/osf_prereg_stage1_v2.md):
the model's training labels are calibrated station observations, not KOALA-corrected
CAMS. This script produces the canonical calibrated observation set.

Three calibration columns are emitted side-by-side so downstream code (and the
pre-reg sensitivity analysis §6.1) can choose:

  pm25_observed_barkjohn       Barkjohn et al. (2021) EPA correction (public,
                               defensible, but US-calibrated):
                                 pm25 = 0.524*cf_1 - 0.0852*RH + 5.72

  pm25_observed_anchor_self    Per-sensor linear regression of monthly mean
                               vs KOALA_MONTHLY_2019 using overlapping months
                               (2019 only). Requires the sensor to have data
                               in 2019; mixes site spatial gradient into the
                               coefficient — flagged for sensitivity use.

  pm25_observed_anchor_hantana FECT Hantana TR4 (closest co-located with the
                               KOALA Peradeniya station) regression coefficients
                               applied to every sensor. Sensor-systematic bias
                               only, no spatial mixing. PREFERRED default.

QC flags (bitmask):
  1   saturated RH (≥99%) — PurpleAir RH sensor artifact in tropical conditions
      (Akurana reports RH=100% for ~68% of hours). INFORMATIONAL ONLY — does
      not gate qc_good. Use pm25_observed_barkjohn_clim_rh for these rows.
  2   channel disagreement >50% (|A−B| / mean) — sensor fault, gates qc_good
  4   pm25 out of range (<0 or >500 µg/m³) — sensor fault, gates qc_good
  8   missing pm25 / cf_1 — sensor fault, gates qc_good

A row is qc_good if (qc_flag & QC_FAULT_MASK) == 0, where QC_FAULT_MASK
covers bits 2|4|8 only (not bit 1).

NOTE ON CALIBRATION DEFENSIBILITY:
  Per-sensor KOALA-monthly regression (pm25_observed_anchor_self) is computed
  but UNRELIABLE with this dataset — Hantana TR4 only has 4 qc-good months
  in 2019 (R²=0.29 on the initial fit), and Akurana's 2019 coverage collapses
  to NE-monsoon months only after RH-saturation filtering.

  The PUBLISHABLE primary calibration is pm25_observed_barkjohn (the EPA
  Barkjohn 2021 standard formula). The KOALA-anchor columns are emitted
  for sensitivity analysis only (pre-reg §6.1). FECT vs KOALA monthly bias
  is reported in calibration_diagnostics_kandy.csv as a validation
  diagnostic, NOT used as a calibration target.

  Future work: substitute ERA5 RH for Barkjohn's RH term in
  build_dataset_v2.py — PurpleAir RH is not trustworthy in tropical Kandy.

Inputs:
  data/external/purpleair/raw/{sensor_id}_{label}_avg60_*.csv  (one per 30-day chunk)

Outputs:
  data/external/purpleair/processed/fect_kandy_calibrated_hourly.parquet
  data/external/purpleair/processed/fect_kandy_calibrated_daily.parquet
  data/external/purpleair/processed/calibration_coefficients_kandy.csv
  data/external/purpleair/processed/calibration_diagnostics_kandy.csv  (monthly fits)

Usage:
  python -m src.stage1_satml.data.calibrate_fect           # from kandy_pm25/
  python src/stage1_satml/data/calibrate_fect.py           # same
  python src/stage1_satml/data/calibrate_fect.py --force   # overwrite outputs

Reference: pre-registration §3.1, §6.1.
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import EXTERNAL_DIR, LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("calibrate_fect")

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# KOALA 2019 monthly means (Senarathna et al. 2024, CJS 53(2):197–206).
# Source of truth is build_dataset.py — duplicated here to avoid an import
# cycle (build_dataset.py touches a lot of v1 machinery we don't want
# triggered by a v2 data prep step).
KOALA_MONTHLY_2019: dict[int, float] = {
    1: 26.13, 2: 26.92, 3: 34.87, 4: 33.50, 5: 28.04, 6: 19.64,
    7: 22.57, 8: 20.07, 9: 20.89, 10: 21.01, 11: 22.87, 12: 17.76,
}  # µg/m³

# Sensor catalog: (id, label, lat, lon, region, use_in_stage1)
SENSORS: list[tuple[int, str, float, float, str, bool]] = [
    (12451,  "FECT_Akurana",      7.366, 80.618, "kandy",   True),
    (33495,  "FECT_Hantana_TR4",  7.356, 80.631, "kandy",   True),
    (21923,  "FECT_Kandy_TR7",    7.331, 80.631, "kandy",   False),  # sparse — drop
    (29677,  "Gregorys_Road",     6.909, 79.875, "colombo", False),  # OOD aux
]

# Barkjohn EPA correction for PurpleAir cf_1.
# Barkjohn et al. 2021, AMT 14, 4617–4637 (US-wide regression vs FRM).
def barkjohn(cf_1: pd.Series, rh: pd.Series) -> pd.Series:
    return 0.524 * cf_1 - 0.0852 * rh + 5.72

# QC bitmask
QC_HIGH_RH   = 1
QC_CHAN_DIFF = 2
QC_RANGE     = 4
QC_MISSING   = 8

# Bits that gate qc_good. Bit 1 (high RH) is informational only.
QC_FAULT_MASK = QC_CHAN_DIFF | QC_RANGE | QC_MISSING

# Climatological RH used in the fallback Barkjohn correction. Annual mean
# 2m relative humidity over Kandy from ERA5 reanalysis (2003–2025 average,
# verified independently) ≈ 80%. The exact value is not critical; the
# constant offset shifts all predictions uniformly and will be re-anchored
# downstream when ERA5 RH is merged in build_dataset_v2.py.
CLIM_RH_KANDY = 80.0

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

RAW_DIR  = EXTERNAL_DIR / "purpleair" / "raw"
PROC_DIR = EXTERNAL_DIR / "purpleair" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

OUT_HOURLY = PROC_DIR / "fect_kandy_calibrated_hourly.parquet"
OUT_DAILY  = PROC_DIR / "fect_kandy_calibrated_daily.parquet"
OUT_COEFS  = PROC_DIR / "calibration_coefficients_kandy.csv"
OUT_DIAG   = PROC_DIR / "calibration_diagnostics_kandy.csv"

# ─────────────────────────────────────────────────────────────────────────────
# Load + QC
# ─────────────────────────────────────────────────────────────────────────────

def load_sensor_raw(sensor_id: int, label: str) -> pd.DataFrame:
    """Concatenate all 30-day chunk CSVs for one sensor, dedupe, sort."""
    files = sorted(RAW_DIR.glob(f"{sensor_id}_{label}_avg60_*.csv"))
    if not files:
        log.warning(f"  no raw files for {sensor_id} {label}")
        return pd.DataFrame()

    parts = []
    for f in files:
        try:
            df = pd.read_csv(f)
        except pd.errors.EmptyDataError:
            continue
        if df.empty:
            continue
        parts.append(df)

    if not parts:
        return pd.DataFrame()

    df = pd.concat(parts, ignore_index=True)
    df = df.drop_duplicates(subset=["time_stamp"]).sort_values("time_stamp").reset_index(drop=True)
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True, errors="coerce")
    df = df.dropna(subset=["datetime_utc"])
    log.info(f"  {sensor_id} {label}: {len(df):>6,} hourly rows "
             f"[{df['datetime_utc'].min().date()} → {df['datetime_utc'].max().date()}]")
    return df


def add_qc_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Bitmask QC flag (see module docstring)."""
    flag = pd.Series(0, index=df.index, dtype="int16")

    # Saturated-RH flag at 99% (sensor artifact, not real meteorology).
    # Loosened from Barkjohn's 95% cutoff because that drops ~68% of Akurana
    # hours in tropical Kandy — including most of the SW-monsoon and 2019
    # post-March data needed for KOALA monthly overlap.
    flag |= np.where(df["humidity"].fillna(0) >= 99, QC_HIGH_RH, 0).astype("int16")

    a = df["pm2.5_atm_a"]
    b = df["pm2.5_atm_b"]
    mean_ab = (a + b) / 2.0
    chan_diff = np.where(mean_ab > 0, np.abs(a - b) / mean_ab, 0)
    flag |= np.where(chan_diff > 0.5, QC_CHAN_DIFF, 0).astype("int16")

    pm = df["pm2.5_atm"]
    flag |= np.where((pm < 0) | (pm > 500), QC_RANGE, 0).astype("int16")
    flag |= np.where(pm.isna() | df["pm2.5_cf_1"].isna(), QC_MISSING, 0).astype("int16")

    df["qc_flag"] = flag
    df["channel_disagreement"] = chan_diff
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Calibration
# ─────────────────────────────────────────────────────────────────────────────

def monthly_mean_2019(df: pd.DataFrame, value_col: str) -> pd.Series:
    """Mean of value_col by calendar month for 2019, qc-good hours only.
    qc-good = no real sensor faults (channel disagreement / range / missing).
    High-RH rows are kept; the value_col passed in should be the clim-RH variant
    so the saturated-RH artifact doesn't corrupt the monthly mean."""
    qc_ok = (df["qc_flag"] & QC_FAULT_MASK) == 0
    mask = (df["datetime_utc"].dt.year == 2019) & qc_ok & df[value_col].notna()
    if mask.sum() == 0:
        return pd.Series(dtype="float64")
    sub = df.loc[mask, ["datetime_utc", value_col]].copy()
    sub["month"] = sub["datetime_utc"].dt.month
    return sub.groupby("month")[value_col].mean()


def fit_koala_regression(sensor_monthly: pd.Series) -> dict | None:
    """
    Linear regression: KOALA_m = slope * sensor_m + intercept.
    Returns dict with slope, intercept, r2, rmse, n_months, koala_means,
    sensor_means; or None if insufficient overlap.
    """
    overlap = sorted(set(sensor_monthly.index) & set(KOALA_MONTHLY_2019.keys()))
    if len(overlap) < 4:
        return None
    x = np.array([sensor_monthly[m] for m in overlap])
    y = np.array([KOALA_MONTHLY_2019[m] for m in overlap])
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    rmse = float(np.sqrt(ss_res / len(overlap)))
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r2": float(r2),
        "rmse": rmse,
        "n_months": len(overlap),
        "months": overlap,
        "sensor_means": [float(v) for v in x],
        "koala_means":  [float(v) for v in y],
    }


def apply_linear(values: pd.Series, slope: float, intercept: float) -> pd.Series:
    return slope * values + intercept


# ─────────────────────────────────────────────────────────────────────────────
# Per-sensor pipeline
# ─────────────────────────────────────────────────────────────────────────────

def process_sensor(sensor_id: int, label: str, lat: float, lon: float, region: str) -> tuple[pd.DataFrame, dict]:
    """Load → QC → Barkjohn → fit per-sensor KOALA regression. Returns hourly df + fit info."""
    log.info(f"=== {sensor_id} {label} ({region}) ===")
    df = load_sensor_raw(sensor_id, label)
    if df.empty:
        return pd.DataFrame(), {"sensor_id": sensor_id, "label": label, "n_rows": 0}

    df = add_qc_flags(df)
    # Two Barkjohn variants:
    # - _sensor_rh: uses raw PurpleAir RH (saturates at 100% in tropical Kandy)
    # - _clim_rh:   uses CLIM_RH_KANDY constant — flat offset, stable but blind
    #               to actual humidity variation. Preferred when high-RH flag set.
    df["pm25_observed_barkjohn"]         = barkjohn(df["pm2.5_cf_1"], df["humidity"])
    df["pm25_observed_barkjohn_clim_rh"] = barkjohn(df["pm2.5_cf_1"], CLIM_RH_KANDY)

    bark_monthly = monthly_mean_2019(df, "pm25_observed_barkjohn_clim_rh")
    raw_monthly  = monthly_mean_2019(df, "pm2.5_atm")

    fit_self_bark = fit_koala_regression(bark_monthly)
    fit_self_raw  = fit_koala_regression(raw_monthly)

    info = {
        "sensor_id":    sensor_id,
        "label":        label,
        "lat":          lat,
        "lon":          lon,
        "region":       region,
        "n_rows_total": len(df),
        "n_rows_qc_good":   int(((df["qc_flag"] & QC_FAULT_MASK) == 0).sum()),
        "n_rows_high_rh":   int(((df["qc_flag"] & QC_HIGH_RH) > 0).sum()),
        "date_min":     df["datetime_utc"].min(),
        "date_max":     df["datetime_utc"].max(),
        "n_months_2019": len(bark_monthly),
        "fit_self_barkjohn": fit_self_bark,
        "fit_self_raw":      fit_self_raw,
    }

    df["sensor_id"]   = sensor_id
    df["sensor_name"] = label
    df["lat"]         = lat
    df["lon"]         = lon
    df["region"]      = region

    return df, info


# ─────────────────────────────────────────────────────────────────────────────
# Aggregation + apply Hantana transfer
# ─────────────────────────────────────────────────────────────────────────────

def apply_hantana_transfer(all_hourly: pd.DataFrame, hantana_info: dict) -> pd.DataFrame:
    """
    Apply Hantana TR4 KOALA-regression coefficients (from Barkjohn-corrected
    monthly means) to every sensor's Barkjohn-corrected PM2.5. This is the
    preferred default per pre-reg §3.1 — sensor-systematic, no spatial mixing.
    """
    fit = hantana_info.get("fit_self_barkjohn")
    if fit is None:
        log.error("  Hantana TR4 has no KOALA regression — cannot apply transfer.")
        all_hourly["pm25_observed_anchor_hantana"] = np.nan
        return all_hourly
    slope = fit["slope"]
    intercept = fit["intercept"]
    log.info(f"  Hantana TR4 KOALA fit (clim-RH Barkjohn input): slope={slope:.4f}, intercept={intercept:+.3f}, "
             f"R²={fit['r2']:.3f}, n_months={fit['n_months']}")
    all_hourly["pm25_observed_anchor_hantana"] = apply_linear(
        all_hourly["pm25_observed_barkjohn_clim_rh"], slope, intercept
    )
    return all_hourly


def apply_self_anchor(df: pd.DataFrame, fit_self: dict | None) -> pd.Series:
    """Per-sensor self-anchor: apply this sensor's own KOALA regression
    to its clim-RH Barkjohn series (so RH-saturation does not corrupt)."""
    if fit_self is None:
        return pd.Series(np.nan, index=df.index)
    return apply_linear(df["pm25_observed_barkjohn_clim_rh"], fit_self["slope"], fit_self["intercept"])


def aggregate_to_daily(hourly: pd.DataFrame) -> pd.DataFrame:
    """Daily means + counts per sensor. Excludes only real sensor faults;
    high-RH rows are kept (use the *_clim_rh column for those)."""
    h = hourly[(hourly["qc_flag"] & QC_FAULT_MASK) == 0].copy()
    h["date"] = h["datetime_utc"].dt.tz_convert(None).dt.normalize()
    h["high_rh"] = ((h["qc_flag"] & QC_HIGH_RH) > 0).astype("int8")

    grp = h.groupby(["sensor_id", "sensor_name", "lat", "lon", "region", "date"])
    daily = grp.agg(
        pm25_observed_barkjohn         =("pm25_observed_barkjohn",         "mean"),
        pm25_observed_barkjohn_clim_rh =("pm25_observed_barkjohn_clim_rh", "mean"),
        pm25_observed_anchor_self      =("pm25_observed_anchor_self",      "mean"),
        pm25_observed_anchor_hantana   =("pm25_observed_anchor_hantana",   "mean"),
        humidity                       =("humidity",                       "mean"),
        temperature                    =("temperature",                    "mean"),
        pressure                       =("pressure",                       "mean"),
        n_hours                        =("pm25_observed_barkjohn_clim_rh", "count"),
        frac_high_rh                   =("high_rh",                        "mean"),
    ).reset_index()

    # Drop days with <12 good hours (per LCS QA convention).
    daily = daily[daily["n_hours"] >= 12].reset_index(drop=True)
    return daily


# ─────────────────────────────────────────────────────────────────────────────
# Diagnostics + coefficient table
# ─────────────────────────────────────────────────────────────────────────────

def write_coefficients_table(infos: list[dict]) -> None:
    rows = []
    for info in infos:
        fit_bark = info.get("fit_self_barkjohn") or {}
        fit_raw  = info.get("fit_self_raw") or {}
        rows.append({
            "sensor_id":          info["sensor_id"],
            "label":              info["label"],
            "lat":                info.get("lat"),
            "lon":                info.get("lon"),
            "region":             info.get("region"),
            "date_min":           info.get("date_min"),
            "date_max":           info.get("date_max"),
            "n_rows_total":       info.get("n_rows_total", 0),
            "n_rows_qc_good":     info.get("n_rows_qc_good", 0),
            "n_months_2019":      info.get("n_months_2019", 0),
            # Self barkjohn-input regression
            "self_bark_slope":     fit_bark.get("slope"),
            "self_bark_intercept": fit_bark.get("intercept"),
            "self_bark_r2":        fit_bark.get("r2"),
            "self_bark_rmse":      fit_bark.get("rmse"),
            "self_bark_n":         fit_bark.get("n_months"),
            # Self raw-input regression (for sensitivity)
            "self_raw_slope":     fit_raw.get("slope"),
            "self_raw_intercept": fit_raw.get("intercept"),
            "self_raw_r2":        fit_raw.get("r2"),
            "self_raw_n":         fit_raw.get("n_months"),
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT_COEFS, index=False)
    log.info(f"  wrote {OUT_COEFS}  ({len(out)} sensors)")


def write_diagnostics_table(infos: list[dict]) -> None:
    """Per-sensor × per-month points used in regression (for plotting)."""
    rows = []
    for info in infos:
        for fit_name, fit in (("barkjohn", info.get("fit_self_barkjohn")),
                              ("raw",      info.get("fit_self_raw"))):
            if not fit:
                continue
            for m, s, k in zip(fit["months"], fit["sensor_means"], fit["koala_means"]):
                rows.append({
                    "sensor_id":  info["sensor_id"],
                    "label":      info["label"],
                    "fit_input":  fit_name,
                    "month":      m,
                    "sensor_mean": s,
                    "koala_mean":  k,
                })
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIAG, index=False)
    log.info(f"  wrote {OUT_DIAG}  ({len(out)} (sensor, month, fit) rows)")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite outputs")
    ap.add_argument("--all-sensors", action="store_true",
                    help="include sparse / OOD sensors (TR7, Gregorys Road) in output")
    args = ap.parse_args()

    if OUT_HOURLY.exists() and not args.force:
        log.warning(f"output {OUT_HOURLY} exists — use --force to overwrite")
        return

    keep = [s for s in SENSORS if s[5] or args.all_sensors]
    log.info(f"processing {len(keep)} sensors: {[s[1] for s in keep]}")

    all_dfs: list[pd.DataFrame] = []
    infos:  list[dict]          = []
    by_id:  dict[int, dict]     = {}

    for sid, label, lat, lon, region, _use in keep:
        df, info = process_sensor(sid, label, lat, lon, region)
        if df.empty:
            continue
        infos.append(info)
        by_id[sid] = info
        all_dfs.append(df)

    if not all_dfs:
        log.error("no sensor data loaded; abort")
        return

    # Stage 1: apply per-sensor self anchor to each sensor's rows.
    for df in all_dfs:
        sid = int(df["sensor_id"].iloc[0])
        df["pm25_observed_anchor_self"] = apply_self_anchor(df, by_id[sid].get("fit_self_barkjohn"))

    all_hourly = pd.concat(all_dfs, ignore_index=True)

    # Stage 2: apply Hantana TR4 coefficients to everyone (preferred default per pre-reg).
    hantana_info = by_id.get(33495)
    if hantana_info is None:
        log.error("Hantana TR4 (33495) missing — cannot compute pm25_observed_anchor_hantana")
        all_hourly["pm25_observed_anchor_hantana"] = np.nan
    else:
        all_hourly = apply_hantana_transfer(all_hourly, hantana_info)

    # Column ordering for the parquet
    cols = [
        "sensor_id", "sensor_name", "lat", "lon", "region",
        "datetime_utc",
        "humidity", "temperature", "pressure",
        "pm2.5_atm", "pm2.5_atm_a", "pm2.5_atm_b", "pm2.5_cf_1",
        "channel_disagreement", "qc_flag",
        "pm25_observed_barkjohn",
        "pm25_observed_barkjohn_clim_rh",
        "pm25_observed_anchor_self",
        "pm25_observed_anchor_hantana",
    ]
    cols = [c for c in cols if c in all_hourly.columns]
    all_hourly = all_hourly[cols].rename(columns={"pm2.5_atm": "pm25_atm_raw"})

    all_hourly.to_parquet(OUT_HOURLY, index=False)
    log.info(f"  wrote {OUT_HOURLY}  ({len(all_hourly):,} rows × {len(all_hourly.columns)} cols)")

    daily = aggregate_to_daily(all_hourly.rename(columns={"pm25_atm_raw": "pm2.5_atm"}))
    daily.to_parquet(OUT_DAILY, index=False)
    log.info(f"  wrote {OUT_DAILY}  ({len(daily):,} sensor-day rows)")

    write_coefficients_table(infos)
    write_diagnostics_table(infos)

    # Quick summary
    log.info("─── summary ───")
    for info in infos:
        bk = info.get("fit_self_barkjohn")
        base = (f"  {info['sensor_id']:>6} {info['label']:<22} "
                f"n_total={info['n_rows_total']:>6,}  "
                f"qc_good={info['n_rows_qc_good']:>6,}  "
                f"high_rh={info['n_rows_high_rh']:>6,}  "
                f"2019_months={info['n_months_2019']:>2}  ")
        if bk:
            log.info(base + f"self-bark fit: slope={bk['slope']:+.3f} "
                            f"int={bk['intercept']:+.2f} R²={bk['r2']:+.3f} "
                            f"(n={bk['n_months']})  [UNRELIABLE — sensitivity only]")
        else:
            log.info(base + f"self-bark fit: SKIPPED (insufficient 2019 overlap, need ≥4 months)")
    log.info("primary calibration column → pm25_observed_barkjohn_clim_rh")
    log.info("KOALA-anchor columns → sensitivity-analysis use only (pre-reg §6.1)")


if __name__ == "__main__":
    main()
