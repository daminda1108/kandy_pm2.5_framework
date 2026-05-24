"""
burning_season_analysis.py — Chiang Mai biomass burning season analysis.

Phase 5 of the Chiang Mai PINN validation report.

Inputs (all from prior phases):
    - chiangmai_pinn_vs_observations.parquet  (Phase 4 ✅)
    - chiangmai_all_stations_2021_2025.csv    (Phase 1 ✅)
    - chiangmai_era5_{year}.nc                (Phase 2a — 2022 ✅, others downloading)

Analysis:
    1. Seasonal labelling: burning (Feb–May), non-burning (Jun–Nov), cool (Dec–Jan)
    2. Counterfactual baseline: fit PM2.5 = f(BLH, wind_speed, T, DOY) on non-burning days
       per station → apply to burning days → "what PM2.5 would be without fires"
    3. Three-way comparison table: C_obs | C_pinn | C_baseline for each season
    4. Monthly PM2.5 statistics (mean, 5th/95th percentile) across all stations
    5. Burning detection summary: which months and stations most affected

Outputs:
    - data/processed/stage2/chiangmai_burning_mask.csv
    - results/tables/chiangmai_burning_analysis.json
    - Printed summary tables

Usage:
    python burning_season_analysis.py
    python burning_season_analysis.py --obs-only   # skip counterfactual fitting
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    LOG_FORMAT, LOG_DATEFMT,
    DATA_DIR, RESULTS_DIR,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("burning_season_analysis")

PROCESSED_DIR = DATA_DIR / "processed"

# ── Paths ─────────────────────────────────────────────────────────────────────
PINN_PARQUET = PROCESSED_DIR / "stage2" / "chiangmai_pinn_vs_observations.parquet"
PM25_CSV     = DATA_DIR / "external" / "chiangmai" / "pm25" / "chiangmai_all_stations_2021_2025.csv"
OUT_MASK     = PROCESSED_DIR / "stage2" / "chiangmai_burning_mask.csv"
OUT_JSON     = RESULTS_DIR / "tables" / "chiangmai_burning_analysis.json"

# ── Burning season definition ─────────────────────────────────────────────────
# Climatological: Feb–May = biomass burning in northern Thailand
# Reference: GFED, MODIS FIRMS, Thailand Pollution Control Department
BURNING_MONTHS     = {2, 3, 4, 5}    # Feb–May
NON_BURNING_MONTHS = {6, 7, 8, 9, 10, 11}   # Jun–Nov (PINN training regime)
COOL_MONTHS        = {12, 1}         # Dec–Jan

# PM2.5 threshold for classifying a day as "burning-affected"
BURNING_PM25_THRESHOLD = 50.0   # µg/m³ (≈2× WHO annual guideline)


def season_label(month: int) -> str:
    if month in BURNING_MONTHS:
        return "burning"
    elif month in NON_BURNING_MONTHS:
        return "non-burning"
    else:
        return "cool"


# ══════════════════════════════════════════════════════════════════════════════
# Data Loading
# ══════════════════════════════════════════════════════════════════════════════

def load_pinn_obs() -> pd.DataFrame:
    """
    Load the Phase 4 PINN-vs-observations parquet.
    Falls back to building from raw obs if parquet not yet available.
    """
    if PINN_PARQUET.exists():
        log.info("Loading PINN observations from %s", PINN_PARQUET)
        df = pd.read_parquet(str(PINN_PARQUET))
        log.info("  %d station-days, %d stations", len(df), df["location_name"].nunique())
        return df

    log.warning("PINN parquet not found — loading raw obs only (no PINN predictions)")
    df = pd.read_csv(str(PM25_CSV))
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True)
    df["date"] = df["datetime_utc"].dt.date
    daily = (
        df.groupby(["date", "location_id", "location_name", "lat", "lon", "provider"])
        .agg(pm25_obs=("pm25", "mean"), n_obs=("pm25", "count"))
        .reset_index()
    )
    daily = daily[daily["n_obs"] >= 4].copy()
    daily["date"] = pd.to_datetime(daily["date"], utc=True)
    daily["month"] = daily["date"].dt.month
    daily["year"]  = daily["date"].dt.year
    daily["season"] = daily["month"].apply(season_label)
    return daily


# ══════════════════════════════════════════════════════════════════════════════
# Counterfactual Baseline
# ══════════════════════════════════════════════════════════════════════════════

def fit_counterfactual(df: pd.DataFrame) -> dict:
    """
    Fit PM2.5 baseline = f(BLH, wind_speed, month_sin, month_cos, DOY_sin, DOY_cos)
    on non-burning season days (Jun–Nov) per station.
    Apply the baseline to burning-season days to estimate "what PM2.5 would be without fires".

    Returns dict: station_name → fitted sklearn LinearRegression model.
    If BLH/ERA5 not available in df (obs-only mode), uses month-of-year mean as baseline.
    """
    from sklearn.linear_model import Ridge

    has_era5 = "blh" in df.columns
    station_models = {}

    for stn, grp in df.groupby("location_name"):
        non_burn = grp[grp["season"] == "non-burning"].copy()
        if len(non_burn) < 20:
            log.warning("  Station %s: too few non-burning days (%d) — skip baseline",
                        stn[:40], len(non_burn))
            station_models[stn] = None
            continue

        if has_era5:
            wind_speed = np.sqrt(non_burn["u10"].values**2 + non_burn["v10"].values**2)
            blh = non_burn["blh"].values / 2000.0   # normalise
        else:
            # Fallback: use month as only predictor (climatological mean)
            wind_speed = np.zeros(len(non_burn))
            blh = np.zeros(len(non_burn))

        month = non_burn["month"].values
        doy   = non_burn["date"].dt.day_of_year.values

        # Fourier features for month + DOY (capture seasonal cycle)
        X = np.column_stack([
            blh,
            wind_speed,
            np.sin(2 * np.pi * month / 12),
            np.cos(2 * np.pi * month / 12),
            np.sin(2 * np.pi * doy / 365),
            np.cos(2 * np.pi * doy / 365),
        ])
        y = non_burn["pm25_obs"].values

        model = Ridge(alpha=1.0)
        model.fit(X, y)
        r2_train = model.score(X, y)
        log.info("  Baseline %s: n=%d, R²=%.3f", stn[:40], len(non_burn), r2_train)
        station_models[stn] = model

    return station_models


def apply_counterfactual(df: pd.DataFrame, station_models: dict) -> pd.DataFrame:
    """
    Apply baseline models to compute C_baseline for each row.
    For non-burning rows, C_baseline ≈ C_obs (in-sample).
    For burning rows, C_baseline = what model predicts (counterfactual).
    """
    has_era5 = "blh" in df.columns
    baselines = []

    for stn, grp in df.groupby("location_name"):
        model = station_models.get(stn)
        if model is None:
            baselines.extend([np.nan] * len(grp))
            continue

        if has_era5:
            wind_speed = np.sqrt(grp["u10"].values**2 + grp["v10"].values**2)
            blh = grp["blh"].values / 2000.0
        else:
            wind_speed = np.zeros(len(grp))
            blh = np.zeros(len(grp))

        month = grp["month"].values
        doy   = grp["date"].dt.day_of_year.values

        X = np.column_stack([
            blh,
            wind_speed,
            np.sin(2 * np.pi * month / 12),
            np.cos(2 * np.pi * month / 12),
            np.sin(2 * np.pi * doy / 365),
            np.cos(2 * np.pi * doy / 365),
        ])
        pred = model.predict(X)
        baselines.extend(pred.tolist())

    df = df.copy()
    df["pm25_baseline"] = baselines
    df["pm25_baseline"] = df["pm25_baseline"].clip(lower=0.0)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# Summary Statistics
# ══════════════════════════════════════════════════════════════════════════════

def seasonal_summary(df: pd.DataFrame) -> dict:
    """Compute mean ± std and percentiles for obs/pinn/baseline by season."""
    has_pinn = "pm25_pinn" in df.columns
    has_baseline = "pm25_baseline" in df.columns

    seasons = ["burning", "non-burning", "cool", "all"]
    summary = {}

    for season in seasons:
        if season == "all":
            sub = df
        else:
            sub = df[df["season"] == season]
        if len(sub) == 0:
            continue

        s = {"n": int(len(sub)), "n_days": int(sub["date"].nunique() if "date" in sub.columns else len(sub))}

        obs = sub["pm25_obs"].dropna().values
        s["obs"] = {
            "mean": round(float(np.mean(obs)), 2),
            "std":  round(float(np.std(obs)), 2),
            "p05":  round(float(np.percentile(obs, 5)), 2),
            "p50":  round(float(np.percentile(obs, 50)), 2),
            "p95":  round(float(np.percentile(obs, 95)), 2),
        }

        if has_pinn and "pm25_pinn" in sub.columns:
            pinn = sub["pm25_pinn"].dropna().values
            if len(pinn) > 0:
                s["pinn"] = {
                    "mean": round(float(np.mean(pinn)), 2),
                    "std":  round(float(np.std(pinn)), 2),
                    "bias": round(float(np.mean(pinn) - np.mean(obs)), 2),
                }

        if has_baseline:
            bl = sub["pm25_baseline"].dropna().values
            bl = bl[np.isfinite(bl)]
            if len(bl) > 0:
                s["baseline"] = {
                    "mean": round(float(np.mean(bl)), 2),
                    "std":  round(float(np.std(bl)), 2),
                    "fire_increment": round(
                        float(np.mean(obs)) - float(np.mean(bl)), 2
                    ),  # positive = fire contribution
                }

        summary[season] = s

    return summary


def monthly_summary(df: pd.DataFrame) -> list:
    """Monthly mean PM2.5 obs across all stations."""
    has_pinn = "pm25_pinn" in df.columns
    rows = []
    for m in range(1, 13):
        sub = df[df["month"] == m]
        if len(sub) == 0:
            continue
        obs_mean = float(sub["pm25_obs"].mean())
        row = {"month": m, "season": season_label(m), "n_days": int(len(sub)),
               "obs_mean": round(obs_mean, 2),
               "obs_p95": round(float(sub["pm25_obs"].quantile(0.95)), 2)}
        if has_pinn:
            row["pinn_mean"] = round(float(sub["pm25_pinn"].mean()), 2)
        if "pm25_baseline" in df.columns:
            bl = sub["pm25_baseline"].dropna()
            if len(bl) > 0:
                row["baseline_mean"] = round(float(bl.mean()), 2)
                row["fire_increment"] = round(obs_mean - float(bl.mean()), 2)
        rows.append(row)
    return rows


def burning_day_fraction(df: pd.DataFrame) -> dict:
    """
    Fraction of days in each month where PM2.5_obs > BURNING_PM25_THRESHOLD.
    Confirms that Feb–May has highest burning signal.
    """
    result = {}
    for m in range(1, 13):
        sub = df[df["month"] == m]
        if len(sub) == 0:
            continue
        frac = float((sub["pm25_obs"] > BURNING_PM25_THRESHOLD).mean())
        result[m] = {"frac_above_50": round(frac, 3),
                     "season": season_label(m),
                     "n": int(len(sub))}
    return result


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--obs-only", action="store_true",
                        help="Skip counterfactual fitting (useful if ERA5 not in parquet)")
    args = parser.parse_args()

    # ── 1. Load data ─────────────────────────────────────────────────────────
    df = load_pinn_obs()

    # ── 2. Burning mask ──────────────────────────────────────────────────────
    df["is_burning_month"] = df["month"].isin(BURNING_MONTHS)
    df["is_burning_day"]   = (df["pm25_obs"] > BURNING_PM25_THRESHOLD) & df["is_burning_month"]

    log.info("Burning season months (Feb–May): %d days",
             df[df["is_burning_month"]].shape[0])
    log.info("Burning-affected days (PM2.5 > %.0f µg/m³ in Feb–May): %d days",
             BURNING_PM25_THRESHOLD, df[df["is_burning_day"]].shape[0])

    # ── 3. Counterfactual baseline ────────────────────────────────────────────
    if not args.obs_only:
        try:
            from sklearn.linear_model import Ridge  # noqa: F401
            log.info("Fitting counterfactual baseline models per station...")
            station_models = fit_counterfactual(df)
            df = apply_counterfactual(df, station_models)
            log.info("Counterfactual baseline applied.")
        except ImportError:
            log.warning("scikit-learn not found — skipping counterfactual baseline")

    # ── 4. Summary statistics ─────────────────────────────────────────────────
    season_stats = seasonal_summary(df)
    monthly_stats = monthly_summary(df)
    burning_frac  = burning_day_fraction(df)

    # ── 5. Print summary ──────────────────────────────────────────────────────
    log.info("\n=== BURNING SEASON SUMMARY ===")
    for season, stats in season_stats.items():
        obs_mean = stats["obs"]["mean"]
        obs_p95  = stats["obs"]["p95"]
        pinn_str = ""
        bl_str   = ""
        if "pinn" in stats:
            pinn_str = f"  PINN={stats['pinn']['mean']:.1f} (bias={stats['pinn']['bias']:+.1f})"
        if "baseline" in stats:
            bl_str = f"  Baseline={stats['baseline']['mean']:.1f} (fire_Δ={stats['baseline']['fire_increment']:+.1f})"
        log.info("  %-12s OBS=%.1f µg/m³ (p95=%.1f)%s%s  n=%d",
                 season, obs_mean, obs_p95, pinn_str, bl_str, stats["n"])

    log.info("\nMonthly obs PM2.5 (all stations):")
    for row in monthly_stats:
        fire_str = ""
        if "fire_increment" in row:
            fire_str = f"  fire_Δ={row['fire_increment']:+.1f}"
        log.info("  Month %02d (%-12s): OBS=%.1f µg/m³ (p95=%.1f)%s  n=%d",
                 row["month"], row["season"], row["obs_mean"], row["obs_p95"],
                 fire_str, row["n_days"])

    log.info("\nFraction of burning-season days > %.0f µg/m³:", BURNING_PM25_THRESHOLD)
    for m, info in burning_frac.items():
        if info["season"] in ("burning", "cool"):
            log.info("  Month %02d: %.0f%%  (n=%d)", m, info["frac_above_50"]*100, info["n"])

    # ── 6. Save outputs ───────────────────────────────────────────────────────
    OUT_MASK.parent.mkdir(parents=True, exist_ok=True)
    mask_cols = ["date", "location_id", "location_name", "lat", "lon",
                 "pm25_obs", "month", "year", "season",
                 "is_burning_month", "is_burning_day"]
    if "pm25_pinn" in df.columns:
        mask_cols += ["pm25_pinn", "K_pinn", "blh"]
    if "pm25_baseline" in df.columns:
        mask_cols.append("pm25_baseline")
    mask_cols = [c for c in mask_cols if c in df.columns]
    df[mask_cols].to_csv(str(OUT_MASK), index=False)
    log.info("Saved burning mask → %s (%d rows)", OUT_MASK, len(df))

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    analysis_result = {
        "seasonal_summary":   season_stats,
        "monthly_summary":    monthly_stats,
        "burning_day_fraction": burning_frac,
        "params": {
            "burning_months": sorted(BURNING_MONTHS),
            "non_burning_months": sorted(NON_BURNING_MONTHS),
            "cool_months": sorted(COOL_MONTHS),
            "burning_pm25_threshold": BURNING_PM25_THRESHOLD,
        }
    }
    with open(OUT_JSON, "w") as f:
        json.dump(analysis_result, f, indent=2)
    log.info("Saved burning analysis → %s", OUT_JSON)


if __name__ == "__main__":
    main()
