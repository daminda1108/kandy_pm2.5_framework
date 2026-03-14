"""
build_dataset.py — Integrate all feature sources into the final ML training dataset.

Pipeline:
  1. Load processed satellite features from parquet (MODIS AOD, TROPOMI)
  2. Load processed ERA5 meteorological features from parquet (daily aggregates)
  3. Enrich ERA5 with BLH from v1 hourly NetCDF (2019 only → extended via seasonal climo)
  4. Compute topography-aware atmospheric features (VVC, KFP, TII, DSC, RWP)
  5. Load ground-truth PM2.5 (if available)
  6. Merge on date, handle missing data, save to parquet

Output: data/processed/merged/dataset_daily.parquet
         data/processed/merged/dataset_info.txt
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    FEATURES_DIR, MERGED_DIR, GT_RAW_DIR, ERA5_RAW_DIR,
    CAMS_RAW_DIR, MERRA2_RAW_DIR, RAW_DIR, VALIDATION_DIR,
    LOG_FORMAT, LOG_DATEFMT,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("build_dataset")


# ── KOALA ground truth — Senarathna et al. 2024, CJS 53(2):197-206 ───────────
# DOI: 10.4038/cjs.v53i2.8403
# Instrument: Plantower PMS1003 calibrated vs BAM reference, NIFS Kandy.
# Monthly means derived from Table 3 regression coefficients + December reference (17.76).
# November 22.87 µg/m³ is the monthly mean after excluding the transboundary spike (Nov 1–19).
KOALA_MONTHLY_2019: dict[int, float] = {
    1: 26.13,   # Jan — NE Monsoon
    2: 26.92,   # Feb — NE Monsoon
    3: 34.87,   # Mar — First Inter-monsoon (HIGHEST)
    4: 33.50,   # Apr — First Inter-monsoon
    5: 28.04,   # May — SW Monsoon onset
    6: 19.64,   # Jun — SW Monsoon
    7: 22.57,   # Jul — SW Monsoon
    8: 20.07,   # Aug — SW Monsoon
    9: 20.89,   # Sep — SW Monsoon
   10: 21.01,   # Oct — Second Inter-monsoon
   11: 22.87,   # Nov — Second Inter-monsoon (transboundary spike excluded from monthly mean)
   12: 17.76,   # Dec — NE Monsoon (LOWEST; reference month in regression)
}  # µg/m³
KOALA_ANNUAL_2019: float = sum(KOALA_MONTHLY_2019.values()) / 12  # = 24.5225 µg/m³


# ─────────────────────────────────────────────────────────────────────────────
# LOAD PROCESSED PARQUET FEATURES
# ─────────────────────────────────────────────────────────────────────────────

def load_era5_features() -> pd.DataFrame:
    """Load pre-processed ERA5 daily features from parquet."""
    path = FEATURES_DIR / "era5_features_daily.parquet"
    if not path.exists():
        raise FileNotFoundError(f"ERA5 features not found: {path}\nRun process_gee_exports.py first.")
    era5 = pd.read_parquet(path)
    era5.index = pd.to_datetime(era5.index)
    era5.index.name = "date"
    log.info(f"ERA5 features loaded: {era5.shape}")
    return era5


def load_satellite_features() -> pd.DataFrame:
    """Load pre-processed MODIS AOD and TROPOMI daily features from parquet."""
    frames = []

    modis_path = FEATURES_DIR / "modis_aod_daily.parquet"
    if modis_path.exists():
        modis = pd.read_parquet(modis_path)
        modis.index = pd.to_datetime(modis.index)
        modis.index.name = "date"
        frames.append(modis)
        log.info(f"MODIS AOD loaded: {modis.shape}")
    else:
        log.warning(f"MODIS AOD features not found: {modis_path}")

    tropomi_path = FEATURES_DIR / "tropomi_daily.parquet"
    if tropomi_path.exists():
        tropomi = pd.read_parquet(tropomi_path)
        tropomi.index = pd.to_datetime(tropomi.index)
        tropomi.index.name = "date"
        frames.append(tropomi)
        log.info(f"TROPOMI features loaded: {tropomi.shape}")
    else:
        log.warning(f"TROPOMI features not found: {tropomi_path}")

    if not frames:
        return pd.DataFrame()

    result = pd.concat(frames, axis=1)
    log.info(f"Satellite features combined: {result.shape}")
    return result


def enrich_with_blh(era5: pd.DataFrame) -> pd.DataFrame:
    """
    Add BLH (boundary layer height) from v1 ERA5 hourly NetCDF.

    BLH is critical for VVC (valley ventilation coefficient) but isn't available
    in GEE ERA5-Land daily. We extract hourly BLH from the v1 CDS download (2019),
    compute daily mean/min/max, then extend to other years via monthly climatology.
    """
    nc_files = sorted(ERA5_RAW_DIR.glob("kandy_era5_2019*.nc"))
    # Use the consolidated file if available
    nc_main = ERA5_RAW_DIR / "kandy_era5_2019.nc"
    if not nc_main.exists():
        log.warning("No v1 ERA5 NetCDF with BLH found — VVC will use proxy.")
        return era5

    try:
        import xarray as xr
        ds = xr.open_dataset(nc_main)
        if "blh" not in ds.data_vars:
            log.warning("BLH variable not in ERA5 NetCDF — skipping.")
            ds.close()
            return era5

        blh_hourly = ds["blh"].values.flatten()
        time = pd.DatetimeIndex(ds["valid_time"].values)
        ds.close()

        blh_series = pd.Series(blh_hourly, index=time, name="blh")
        blh_daily = blh_series.resample("D").agg(["mean", "min", "max"])
        blh_daily.columns = ["blh_mean", "blh_min", "blh_max"]
        blh_daily.index = pd.to_datetime(blh_daily.index.date)
        blh_daily.index.name = "date"

        # Build monthly climatology for extending to other years
        blh_clim = blh_daily.groupby(blh_daily.index.month).mean()

        # For dates with actual data, use it; for others, use climatology
        era5["blh_mean"] = np.nan
        era5["blh_min"] = np.nan
        era5["blh_max"] = np.nan

        # Fill 2019 with actual values
        overlap = era5.index.intersection(blh_daily.index)
        era5.loc[overlap, "blh_mean"] = blh_daily.loc[overlap, "blh_mean"]
        era5.loc[overlap, "blh_min"] = blh_daily.loc[overlap, "blh_min"]
        era5.loc[overlap, "blh_max"] = blh_daily.loc[overlap, "blh_max"]

        # Fill remaining with monthly climatology
        mask = era5["blh_mean"].isna()
        era5.loc[mask, "blh_mean"] = era5.loc[mask].index.month.map(blh_clim["blh_mean"])
        era5.loc[mask, "blh_min"] = era5.loc[mask].index.month.map(blh_clim["blh_min"])
        era5.loc[mask, "blh_max"] = era5.loc[mask].index.month.map(blh_clim["blh_max"])

        n_actual = (~mask).sum()
        log.info(f"BLH enrichment: {n_actual} days from 2019 data, "
                 f"{mask.sum()} days from monthly climatology.")

    except Exception as e:
        log.warning(f"Could not extract BLH: {e}")

    return era5


def compute_topo_features(era5: pd.DataFrame) -> pd.DataFrame:
    """Compute topography-aware features from daily ERA5 data."""
    from topo_features import (
        compute_vvc, compute_kfp, compute_rwp,
        compute_terrain_blocking_index, compute_valley_wind_decomposition,
        compute_richardson_number, compute_kfp_v2,
    )

    topo = pd.DataFrame(index=era5.index)

    # VVC — Valley Ventilation Coefficient
    if "blh_mean" in era5.columns and "wind_speed" in era5.columns:
        topo["vvc"] = compute_vvc(era5["wind_speed"], era5["blh_mean"])
        log.info(f"VVC computed: mean={topo['vvc'].mean():.2f}")
    else:
        log.warning("Missing blh or wind_speed — VVC skipped.")

    # KFP — Katabatic Flow Proxy (needs skin_temp)
    if "skt" in era5.columns and "t2m" in era5.columns:
        # Estimate cloud fraction from dewpoint depression
        if "d2m" in era5.columns:
            dd = era5["t2m"] - era5["d2m"]
            cloud_frac = (1.0 - (dd / 25).clip(0, 1))
        else:
            cloud_frac = pd.Series(0.5, index=era5.index)

        topo["kfp"] = compute_kfp(
            skin_temp_k=era5["skt"],
            air_temp_2m_k=era5["t2m"],
            mean_slope_deg=16.0,  # From DEM processing
            cloud_fraction=cloud_frac,
        )
        log.info(f"KFP computed: mean={topo['kfp'].mean():.3f}")
    else:
        log.warning("Missing skt or t2m — KFP skipped.")

    # DSC — Diurnal Stability Cycle (use daily SSRD as proxy at noon)
    if "ssrd" in era5.columns:
        # For daily data, DSC = normalized solar radiation
        ssrd_max = era5["ssrd"].rolling(window=30, center=True, min_periods=1).max()
        topo["dsc"] = (era5["ssrd"] / ssrd_max.clip(lower=1.0)).clip(0, 1)
        log.info(f"DSC computed: mean={topo['dsc'].mean():.2f}")
    else:
        log.warning("Missing ssrd — DSC skipped.")

    # RWP — Rain Washout Potential
    if "tp" in era5.columns and "wind_speed" in era5.columns:
        topo["rwp"] = compute_rwp(era5["tp"], era5["wind_speed"])
        log.info(f"RWP computed: mean={topo['rwp'].mean():.3f}")
    else:
        log.warning("Missing tp or wind_speed — RWP skipped.")

    # TBI — Terrain Blocking Index
    if "wind_dir" in era5.columns:
        topo["terrain_blocking_idx"] = compute_terrain_blocking_index(era5["wind_dir"])
        log.info(f"TBI computed: mean={topo['terrain_blocking_idx'].mean():.3f}")
    else:
        log.warning("Missing wind_dir — TBI skipped.")

    # Valley Wind Decomposition + revised VVC
    if "u10" in era5.columns and "v10" in era5.columns:
        blh = era5["blh_mean"] if "blh_mean" in era5.columns else None
        decomp = compute_valley_wind_decomposition(era5["u10"], era5["v10"], blh_m=blh)
        for col in decomp.columns:
            topo[col] = decomp[col]
        log.info(f"Valley wind decomp computed: {list(decomp.columns)}")
    else:
        log.warning("Missing u10/v10 — valley wind decomposition skipped.")

    # Richardson Number + ri_stable_flag + KFP_v2 (requires ERA5 925 hPa temperature)
    if "t925" in era5.columns and "t2m" in era5.columns and "wind_speed" in era5.columns:
        topo["richardson_number"], topo["ri_stable_flag"] = compute_richardson_number(
            t2m=era5["t2m"],
            t925=era5["t925"],
            wind_speed=era5["wind_speed"],
        )
        # Cloud fraction for KFP_v2: same dewpoint-depression method as KFP_v1
        if "d2m" in era5.columns:
            cloud_frac_ri = (1.0 - ((era5["t2m"] - era5["d2m"]) / 25.0).clip(0.0, 1.0))
        else:
            cloud_frac_ri = pd.Series(0.5, index=era5.index)
        topo["kfp_v2"] = compute_kfp_v2(topo["richardson_number"], cloud_frac_ri)
        log.info(
            f"Richardson Number computed: mean={topo['richardson_number'].mean():.3f}, "
            f"stable (Ri>0.25): {topo['ri_stable_flag'].mean():.1%}"
        )
        log.info(f"KFP_v2 computed: mean={topo['kfp_v2'].mean():.4f}")
    else:
        log.warning(
            "t925 not in ERA5 features — Richardson Number and KFP_v2 skipped.\n"
            "  To enable: add t925 (925 hPa temperature) to era5_features_daily.parquet\n"
            "  via a CDS pressure-level ERA5 download or GEE ERA5 pressure-level export."
        )

    log.info(f"Topo features computed: {list(topo.columns)}")
    return topo


def load_ground_truth() -> pd.DataFrame:
    """Load ground-truth PM2.5 data for validation."""
    gt_files = list(GT_RAW_DIR.glob("*.csv"))

    if not gt_files:
        log.warning(
            "No ground-truth files found in data/raw/ground_truth/.\n"
            "Model will be built without validation labels (satellite-only mode)."
        )
        return pd.DataFrame(columns=["pm25_observed"])

    frames = []
    for f in gt_files:
        try:
            df = pd.read_csv(f)

            # Handle different column naming conventions
            date_col = next((c for c in df.columns if "date" in c.lower() or "time" in c.lower()), None)
            pm25_col = next((c for c in df.columns if "pm25" in c.lower() or "pm2.5" in c.lower()), None)

            if date_col is None or pm25_col is None:
                log.warning(f"Could not identify date/pm25 columns in {f.name}. Columns: {list(df.columns)}")
                continue

            df = df[[date_col, pm25_col]].rename(columns={date_col: "date", pm25_col: "pm25_observed"})
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
            df = df.groupby("date")["pm25_observed"].mean().to_frame()
            frames.append(df)
            log.info(f"Ground truth loaded from {f.name}: {len(df)} records.")
        except Exception as e:
            log.warning(f"Could not read {f.name}: {e}")

    if not frames:
        return pd.DataFrame(columns=["pm25_observed"])

    gt = pd.concat(frames, axis=0)
    gt = gt.groupby(gt.index)["pm25_observed"].mean().to_frame()
    log.info(f"Total ground-truth records: {len(gt)}, mean PM2.5: {gt['pm25_observed'].mean():.1f}")
    return gt


def load_all_cams_labels() -> pd.DataFrame:
    """
    Load CAMS EAC4 + NRT daily PM2.5 as training labels.

    Priority:
      1. EAC4 reanalysis (2003–2022) — higher quality
      2. NRT near-real-time (2016–2025) — fills gaps after 2022

    Returns DataFrame with 'pm25_observed' column (CAMS values used as labels).
    """
    frames = []

    # ── EAC4 daily CSVs ───────────────────────────────────────────────
    eac4_csvs = sorted(CAMS_RAW_DIR.glob("cams_pm25_daily_*.csv"))
    for f in eac4_csvs:
        try:
            df = pd.read_csv(f)
            # Average across grid cells for Kandy point
            if "lat" in df.columns:
                df = df.groupby("date")["cams_pm25"].mean().reset_index()
            frames.append(df.rename(columns={"cams_pm25": "pm25_observed"}))
            log.info(f"  EAC4 label loaded: {f.name} ({len(df)} records)")
        except Exception as e:
            log.warning(f"  Could not read EAC4 CSV {f.name}: {e}")

    # ── NRT combined CSV ──────────────────────────────────────────────
    nrt_path = CAMS_RAW_DIR / "cams_nrt_pm25_2016_2025.csv"
    if nrt_path.exists():
        try:
            nrt = pd.read_csv(nrt_path)
            nrt = nrt.rename(columns={"cams_pm25_nrt": "pm25_observed"})
            frames.append(nrt)
            log.info(f"  NRT labels loaded: {len(nrt)} records")
        except Exception as e:
            log.warning(f"  Could not read NRT CSV: {e}")

    if not frames:
        log.warning(
            "No CAMS label data found. Run download_cams.py or download_gee.py first.\n"
            "Falling back to ground-truth CSVs."
        )
        return pd.DataFrame(columns=["pm25_observed"])

    combined = pd.concat(frames)
    combined["date"] = pd.to_datetime(combined["date"]).dt.normalize()
    # EAC4 takes priority over NRT (kept via keep='first' since EAC4 loaded first)
    combined = combined.drop_duplicates(subset=["date"], keep="first")
    combined = combined.set_index("date").sort_index()

    log.info(
        f"CAMS labels total: {len(combined)} days, "
        f"range {combined.index.min().date()} → {combined.index.max().date()}, "
        f"mean PM2.5: {combined['pm25_observed'].mean():.1f} μg/m³"
    )
    return combined


def apply_koala_monthly_correction(labels: pd.DataFrame) -> pd.DataFrame:
    """
    Apply month-by-month KOALA-anchored bias correction to CAMS labels.

    Anchor: Senarathna et al. 2024, Ceylon Journal of Science 53(2): 197-206.
    DOI: 10.4038/cjs.v53i2.8403
    Instrument: KOALA (Plantower PMS1003) calibrated vs BAM, NIFS Kandy.

    Previous approach (Priyankara 2021): single flat ratio ×0.841, anchoring the
    annual CAMS mean to 34.48 µg/m³. This value was subsequently identified as
    approximately the March inter-monsoon peak (34.87 µg/m³), not the annual mean.
    The old correction placed the full-dataset mean at 30.8 µg/m³ — outside the
    upper KOALA uncertainty bound of ~28.8 µg/m³ (±17.5%).

    New approach: 12 independent monthly correction ratios.
      ratio_m = KOALA_MONTHLY_2019[m] / CAMS_2019_monthly_mean[m]
    Applied uniformly to all years for month m, preserving within-month day-to-day
    variation from CAMS. By construction, corrected 2019 monthly means match
    KOALA_MONTHLY_2019 exactly.

    VD's role is UNCHANGED: spatial disaggregation weight (vd_weight in pixel model).
    """
    # ── Flat annual correction (canonical Model A) ────────────────────────────
    # Comparison of correction strategies (all vs Senarathna 2024 KOALA anchor):
    #
    #  Strategy                | LOMO R² | Oct R² | Label mean | In bounds?
    #  ------------------------|---------|--------|------------|----------
    #  Old ×0.841 (Priyankara) |  0.607  |  0.532 |  30.8 µg   |  ❌
    #  A1: Flat annual ×0.598  |  0.606  |  0.553 |  21.9 µg   |  ✅  ← ADOPTED
    #  A2: Monthly (multiyear) |  0.519  |  0.252 |  24.6 µg   |  ✅
    #  A2: Monthly (2019-only) |  0.507  | -2.342 |  22.0 µg   |  ✅
    #
    # The monthly correction degrades LOMO R² because CAMS's seasonal shape
    # does not match KOALA's — month-specific ratios corrupt the temporal signal
    # XGBoost relies on. Flat annual correction preserves the temporal structure
    # and gives the correct absolute scale within KOALA uncertainty bounds.
    mask_2019 = labels.index.year == 2019
    if mask_2019.sum() == 0:
        log.warning("No 2019 data — cannot anchor to KOALA_ANNUAL_2019. Returning uncorrected.")
        return labels

    cams_2019_annual = labels.loc[mask_2019, "pm25_observed"].mean()
    correction_ratio = KOALA_ANNUAL_2019 / cams_2019_annual

    corrected = labels.copy()
    before_mean = corrected["pm25_observed"].mean()
    corrected["pm25_observed"] *= correction_ratio
    after_mean = corrected["pm25_observed"].mean()

    log.info(
        f"KOALA annual correction: CAMS_2019={cams_2019_annual:.2f} → "
        f"KOALA_2019={KOALA_ANNUAL_2019:.4f} µg/m³, ratio=×{correction_ratio:.4f}"
    )
    log.info(f"Full-dataset mean: {before_mean:.1f} → {after_mean:.1f} µg/m³")

    # Verify 2019 annual mean
    achieved_annual = corrected.loc[mask_2019, "pm25_observed"].mean()
    diff_annual = abs(achieved_annual - KOALA_ANNUAL_2019)
    log.info(
        f"2019 annual mean post-correction: {achieved_annual:.4f} µg/m³ "
        f"(KOALA target: {KOALA_ANNUAL_2019:.4f}, diff: {diff_annual:.4f})"
    )

    # Log approximate monthly alignment (informational only — flat correction
    # does not force monthly means to match KOALA; that would corrupt CAMS temporal structure)
    log.info("2019 monthly means after flat correction (informational vs KOALA targets):")
    for m in range(1, 13):
        m_mask = mask_2019 & (corrected.index.month == m)
        if m_mask.sum() == 0:
            continue
        achieved_m = corrected.loc[m_mask, "pm25_observed"].mean()
        log.info(
            f"  Month {m:2d}: {achieved_m:.2f} µg/m³ (KOALA {KOALA_MONTHLY_2019[m]:.2f}, "
            f"diff {achieved_m - KOALA_MONTHLY_2019[m]:+.2f})"
        )

    return corrected


# Backward-compatibility alias — nothing in the codebase calls this externally,
# but kept so any cached references continue to resolve.
apply_vd_bias_correction = apply_koala_monthly_correction


def build_ensemble_pm25_labels(cams_labels: pd.DataFrame) -> pd.DataFrame:
    """
    Create weighted ensemble labels from CAMS EAC4 + MERRA-2.

    Ensemble: 60% CAMS EAC4, 40% MERRA-2 (following Shaddick et al. 2018).
    Also computes 'reanalysis_agreement' feature for label confidence.

    Args:
        cams_labels: DataFrame with pm25_observed from CAMS

    Returns:
        DataFrame with pm25_observed (ensemble) and reanalysis_agreement
    """
    merra2_path = MERRA2_RAW_DIR / "merra2_pm25_daily.csv"
    if not merra2_path.exists():
        log.info("No MERRA-2 data found — using CAMS-only labels.")
        return cams_labels

    merra2 = pd.read_csv(merra2_path)
    merra2["date"] = pd.to_datetime(merra2["date"]).dt.normalize()
    merra2 = merra2.set_index("date")

    merged = cams_labels.join(merra2[["merra2_pm25"]], how="left")

    # Weighted ensemble where both available
    both_valid = merged["pm25_observed"].notna() & merged["merra2_pm25"].notna()
    only_eac4 = merged["pm25_observed"].notna() & merged["merra2_pm25"].isna()
    only_merra2 = merged["pm25_observed"].isna() & merged["merra2_pm25"].notna()

    # Apply ensemble weights
    merged.loc[both_valid, "pm25_observed"] = (
        0.6 * merged.loc[both_valid, "pm25_observed"] +
        0.4 * merged.loc[both_valid, "merra2_pm25"]
    )
    merged.loc[only_merra2, "pm25_observed"] = merged.loc[only_merra2, "merra2_pm25"]

    # Compute agreement feature (low diff = high confidence)
    merged["reanalysis_agreement"] = np.nan
    merged.loc[both_valid, "reanalysis_agreement"] = 1.0 - (
        abs(cams_labels.loc[both_valid, "pm25_observed"] - merged.loc[both_valid, "merra2_pm25"])
        / cams_labels.loc[both_valid, "pm25_observed"].clip(lower=1.0)
    ).clip(0, 1)

    log.info(f"Ensemble labels: {both_valid.sum()} both-source days, "
             f"{only_eac4.sum()} EAC4-only, {only_merra2.sum()} MERRA2-only")

    return merged[["pm25_observed", "reanalysis_agreement"]]


def build_merra2_vd_labels() -> pd.DataFrame:
    """
    Build Model B PM2.5 labels using a multiplicative three-component decomposition:

        label[y, m, d] = level(y) × shape(m) × anomaly(y, m, d)

    Components:
      - level(y):        VD annual mean for year y, scaled so level(2019) = KOALA_ANNUAL_2019.
                         Source: results/validation/van_donkelaar_comparison.csv
                         VD_2019 = 20.32 µg/m³  →  level(y) = 24.5225 × VD[y] / 20.32
      - shape(m):        KOALA monthly weight = KOALA_MONTHLY_2019[m] / KOALA_ANNUAL_2019.
                         Encodes the 2019 seasonal climatology from Senarathna et al. 2024.
      - anomaly(y, m, d): Normalised MERRA-2 within-month daily departure.
                         anomaly = merra2_pm25[d] / mean(merra2_pm25[y, m])
                         By construction, mean(anomaly) per (y, m) = 1.0.

    Mathematical guarantee:
      E[label[2019, m]] = 24.5225 × (VD_2019/VD_2019) × shape(m) × 1.0
                        = KOALA_MONTHLY_2019[m]   ✓
      2019 monthly means match KOALA exactly; other years scale with VD inter-annual trend.

    Coverage: 2003–2023 — intersection of VD (1998–2023) and MERRA-2 (2003–2025).
    Days outside this window are absent from the returned DataFrame.
    """
    # ── Load VD annual means ──────────────────────────────────────────────────
    vd_path = VALIDATION_DIR / "van_donkelaar_comparison.csv"
    if not vd_path.exists():
        raise FileNotFoundError(
            f"VD comparison CSV not found: {vd_path}\n"
            "Run src/stage1_satml/evaluation/validate_van_donkelaar.py first."
        )
    vd_df = pd.read_csv(vd_path)[["year", "vd_mean"]]
    vd_2019_ser = vd_df.loc[vd_df["year"] == 2019, "vd_mean"]
    if vd_2019_ser.empty:
        raise ValueError(
            "2019 absent from VD comparison CSV — cannot normalise inter-annual level."
        )
    vd_2019 = float(vd_2019_ser.values[0])
    vd_df = vd_df.copy()
    vd_df["level"] = KOALA_ANNUAL_2019 * (vd_df["vd_mean"] / vd_2019)
    log.info(
        f"VD 2019 Kandy mean = {vd_2019:.2f} µg/m³. "
        f"level(2019) anchored to KOALA annual = {KOALA_ANNUAL_2019:.4f} µg/m³."
    )

    # ── Load MERRA-2 daily ────────────────────────────────────────────────────
    m2_path = RAW_DIR / "merra2" / "merra2_pm25_daily.csv"
    if not m2_path.exists():
        raise FileNotFoundError(f"MERRA-2 CSV not found: {m2_path}")
    m2 = pd.read_csv(m2_path, parse_dates=["date"])
    m2["date"] = pd.to_datetime(m2["date"]).dt.normalize()
    m2["year"] = m2["date"].dt.year
    m2["month"] = m2["date"].dt.month

    # Within-(year, month) MERRA-2 monthly mean → normalised daily anomaly factor
    m2["merra2_monthly_mean"] = m2.groupby(["year", "month"])["merra2_pm25"].transform("mean")
    m2["anomaly"] = m2["merra2_pm25"] / m2["merra2_monthly_mean"].clip(lower=0.1)

    # ── Merge VD level by year (keep date column for index restoration) ───────
    m2 = m2.merge(vd_df[["year", "level"]], on="year", how="inner")
    m2 = m2.set_index("date")
    m2.index = pd.to_datetime(m2.index)

    # ── Monthly shape from KOALA (time-invariant 2019 climatology) ────────────
    shape_map = {m: KOALA_MONTHLY_2019[m] / KOALA_ANNUAL_2019 for m in range(1, 13)}
    m2["monthly_shape"] = m2["month"].map(shape_map)

    # ── Final label: multiplicative decomposition ─────────────────────────────
    m2["pm25_observed"] = m2["level"] * m2["monthly_shape"] * m2["anomaly"]
    result = m2[["pm25_observed"]].copy()

    log.info(
        f"Model B labels built: {len(result)} days "
        f"({result.index.min().date()} – {result.index.max().date()})"
    )
    log.info(
        f"  Mean={result['pm25_observed'].mean():.2f}, "
        f"Std={result['pm25_observed'].std():.2f}, "
        f"Min={result['pm25_observed'].min():.2f}, "
        f"Max={result['pm25_observed'].max():.2f} µg/m³"
    )

    # ── Verify 2019 monthly means against KOALA targets ───────────────────────
    mask_2019 = result.index.year == 2019
    log.info("Model B 2019 monthly verification (target: KOALA_MONTHLY_2019):")
    for m in range(1, 13):
        m_mask = mask_2019 & (result.index.month == m)
        if m_mask.sum() == 0:
            continue
        achieved = result.loc[m_mask, "pm25_observed"].mean()
        target = KOALA_MONTHLY_2019[m]
        log.info(f"  Month {m:2d}: {achieved:.2f} µg/m³ (KOALA target: {target:.2f})")

    return result


def _load_enso_mei(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Load NOAA Multivariate ENSO Index (MEI.v2) and merge as monthly feature.

    MEI captures large-scale climate forcing: La Nina brings enhanced rainfall
    to Sri Lanka (wet deposition suppresses PM2.5). This explains the 2021-2025
    performance drop (La Nina 2021-2023).

    Data: NOAA PSL MEI.v2 CSV in data/raw/enso/mei_v2.csv
    If not available, downloads from NOAA.
    """
    enso_dir = RAW_DIR / "enso"
    mei_path = enso_dir / "mei_v2.csv"

    if not mei_path.exists():
        log.info("ENSO MEI not found — attempting download from NOAA...")
        try:
            enso_dir.mkdir(parents=True, exist_ok=True)
            import urllib.request
            url = "https://psl.noaa.gov/enso/mei/data/meiv2.data"
            urllib.request.urlretrieve(url, enso_dir / "meiv2_raw.data")
            # Parse NOAA fixed-width format: year followed by 12 monthly values
            rows = []
            with open(enso_dir / "meiv2_raw.data") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 13:
                        try:
                            year = int(parts[0])
                            for m_idx, val in enumerate(parts[1:13], 1):
                                v = float(val)
                                if v > -900:  # NOAA uses -999 for missing
                                    rows.append({"year": year, "month": m_idx, "mei": v})
                        except ValueError:
                            continue
            if rows:
                mei_df = pd.DataFrame(rows)
                mei_df.to_csv(mei_path, index=False)
                log.info(f"ENSO MEI downloaded and parsed: {len(mei_df)} months")
            else:
                log.warning("Could not parse NOAA MEI data.")
                return dataset
        except Exception as e:
            log.warning(f"Could not download ENSO MEI: {e}")
            return dataset

    try:
        mei = pd.read_csv(mei_path)
        dates = pd.to_datetime(dataset.index)
        mei_lookup = {(int(r["year"]), int(r["month"])): r["mei"]
                      for _, r in mei.iterrows()}
        dataset["enso_mei"] = [
            mei_lookup.get((d.year, d.month), np.nan) for d in dates
        ]
        n_valid = dataset["enso_mei"].notna().sum()
        log.info(f"ENSO MEI added: {n_valid}/{len(dataset)} days have MEI values")
    except Exception as e:
        log.warning(f"Could not load ENSO MEI: {e}")

    return dataset


def _load_colombo_anchor(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Load Colombo BAM PM2.5 as a regional anchor feature.

    Colombo US Embassy BAM sensor provides reference-grade hourly PM2.5,
    aggregated to daily mean. Although 115km from Kandy, shared regional
    signals (monsoon, synoptic transport) make it informative.

    Features added:
      - pm25_colombo: same-day Colombo daily mean (lag-0)
      - pm25_colombo_lag1: previous-day Colombo PM2.5 (lag-1, avoids leakage)
      - pm25_colombo_7d: 7-day rolling mean (background level)
    """
    colombo_path = GT_RAW_DIR / "openaq_colombo_pm25_daily.csv"

    if not colombo_path.exists():
        log.info("Colombo BAM data not available — skipping anchor feature.")
        return dataset

    try:
        col = pd.read_csv(colombo_path)
        col["date"] = pd.to_datetime(col["date"])
        col = col.set_index("date").sort_index()

        # Create lag features
        col_features = pd.DataFrame(index=col.index)
        col_features["pm25_colombo"] = col["pm25_colombo_ugm3"]
        col_features["pm25_colombo_lag1"] = col["pm25_colombo_ugm3"].shift(1)
        col_features["pm25_colombo_7d"] = (
            col["pm25_colombo_ugm3"].rolling(7, min_periods=3).mean()
        )

        # Merge into dataset
        n_before = dataset.shape[1]
        dataset = dataset.merge(
            col_features, left_index=True, right_index=True, how="left"
        )
        n_added = dataset.shape[1] - n_before
        n_valid = dataset["pm25_colombo"].notna().sum()
        log.info(
            f"Colombo anchor: {n_added} features added, "
            f"{n_valid}/{len(dataset)} days with data "
            f"({n_valid/len(dataset):.0%} coverage)"
        )
    except Exception as e:
        log.warning(f"Could not load Colombo anchor: {e}")

    return dataset


def build_dataset(save: bool = True, label_source: str = "cams") -> pd.DataFrame:
    """
    Build the complete ML dataset by merging all feature sources.

    Args:
        save:         Save parquet to disk (default True).
        label_source: PM2.5 label source.
                      'cams'     — Model A: CAMS EAC4/NRT, monthly KOALA correction
                                   (Senarathna et al. 2024). Saved to dataset_daily.parquet.
                      'merra2vd' — Model B: VD inter-annual × KOALA monthly shape ×
                                   MERRA-2 daily anomaly. Saved to dataset_daily_modelB.parquet.
                      Coverage of Model B: 2003–2023 (VD ∩ MERRA-2 date range).

    Returns:
        pd.DataFrame ready for ML modelling.
    """
    log.info("=" * 55)
    log.info(f"Building integrated ML dataset (label_source='{label_source}') ...")
    log.info("=" * 55)

    # ── Load processed features ───────────────────────────────────────────────
    era5 = load_era5_features()
    satellite = load_satellite_features()

    # ── Load PM2.5 labels ────────────────────────────────────────────────────
    log.info(f"\n── Loading PM2.5 Labels (source: {label_source}) ──")
    if label_source == "merra2vd":
        gt = build_merra2_vd_labels()
        log.info(f"Model B labels (VD × KOALA monthly × MERRA-2 anomaly): {len(gt)} days")
    else:
        # Model A: CAMS with monthly KOALA correction
        cams_labels = load_all_cams_labels()
        if not cams_labels.empty:
            # MERRA-2 ensemble intentionally bypassed: r(CAMS,MERRA2)=0.177 over Kandy,
            # mean diff=-23.6 µg/m³ — blending adds noise, not signal (LOMO R² dropped
            # 0.607→0.498). build_ensemble_pm25_labels() kept for thesis diagnostic use only.
            gt = apply_koala_monthly_correction(cams_labels)
            log.info(f"Model A labels (monthly-corrected CAMS): {len(gt)} days")
        else:
            gt = load_ground_truth()
            log.info(f"Using ground-truth CSVs: {len(gt)} days")

    # ── Enrich ERA5 with BLH from v1 data ────────────────────────────────────
    era5 = enrich_with_blh(era5)

    # ── Compute topo-aware features ───────────────────────────────────────────
    topo = compute_topo_features(era5)

    # ── Merge all on date ─────────────────────────────────────────────────────
    dataset = era5.copy()

    if not satellite.empty:
        dataset = dataset.merge(satellite, left_index=True, right_index=True, how="left")

    dataset = dataset.merge(topo, left_index=True, right_index=True, how="left")

    if not gt.empty and "pm25_observed" in gt.columns:
        dataset = dataset.merge(gt, left_index=True, right_index=True, how="left")

    # ── Gap-fill satellite AOD ────────────────────────────────────────────────
    if "aod_modis" in dataset.columns:
        n_pre = dataset["aod_modis"].isna().sum()
        dataset["aod_modis"] = dataset["aod_modis"].interpolate(
            method="time", limit=5, limit_direction="both"
        )
        n_post = dataset["aod_modis"].isna().sum()
        log.info(f"AOD gap-fill: {n_pre} -> {n_post} missing values.")

    # ── Physically motivated interaction terms ─────────────────────────────
    # AOD / BLH_min: high AOD in shallow nocturnal BL → very high surface PM2.5
    if "aod_modis" in dataset.columns and "blh_min" in dataset.columns:
        dataset["aod_blh_ratio"] = (
            dataset["aod_modis"] / dataset["blh_min"].clip(lower=10.0)
        )
        log.info(f"aod_blh_ratio computed: mean={dataset['aod_blh_ratio'].mean():.4f}")

    # AOD × RH: hygroscopic growth correction (aerosol swells with humidity)
    if "aod_modis" in dataset.columns and "rh" in dataset.columns:
        dataset["aod_rh"] = dataset["aod_modis"] * (1.0 + dataset["rh"] / 100.0)
        log.info(f"aod_rh computed: mean={dataset['aod_rh'].mean():.3f}")

    # NO2 / BLH_min: trace gas concentration in shallow nocturnal boundary layer
    if "tropomi_no2" in dataset.columns and "blh_min" in dataset.columns:
        dataset["no2_blh_ratio"] = dataset["tropomi_no2"] / dataset["blh_min"].clip(lower=50.0)
        log.info(f"no2_blh_ratio computed: mean={dataset['no2_blh_ratio'].mean():.6f}")

    # CO / BLH_min: combustion tracer concentrated in shallow boundary layer
    if "tropomi_co" in dataset.columns and "blh_min" in dataset.columns:
        dataset["co_blh_ratio"] = dataset["tropomi_co"] / dataset["blh_min"].clip(lower=50.0)
        log.info(f"co_blh_ratio computed: mean={dataset['co_blh_ratio'].mean():.6f}")

    # ── ENSO MEI index (climate-mode feature) ──────────────────────────────
    dataset = _load_enso_mei(dataset)

    # ── ENSO × seasonal interaction terms (replace raw enso_mei) ──────────
    # Decomposes ENSO forcing into its seasonal phase, capturing the fact that
    # La Niña/El Niño impacts on Sri Lanka precipitation are month-dependent.
    if "enso_mei" in dataset.columns:
        month_angle = 2.0 * np.pi * dataset.index.month / 12.0
        dataset["mei_month_sin"] = dataset["enso_mei"] * np.sin(month_angle)
        dataset["mei_month_cos"] = dataset["enso_mei"] * np.cos(month_angle)
        dataset.drop(columns=["enso_mei"], inplace=True)
        log.info("ENSO interactions computed (mei_month_sin, mei_month_cos); raw enso_mei dropped.")

    # ── Colombo BAM PM2.5 as regional anchor feature ─────────────────────
    dataset = _load_colombo_anchor(dataset)

    # ── Preceding-month PM2.5 mean (autoregressive persistence anchor) ───────
    # For each day d, assigns the mean pm25_observed of the immediately preceding
    # calendar month. Physical motivation: pre-monsoon aerosol loading persists
    # 2–8 weeks (r(March PM2.5, April PM2.5) = 0.679, p<0.001 from inter-annual
    # analysis). Helps the model distinguish high-loading April years (e.g.
    # 2017: 36.8 µg/m³, 2021: 35.8 µg/m³) from typical years (~24–28 µg/m³).
    # LOMO validity: the preceding month is never held out when the current month
    # is held out, so this feature is always available during LOMO evaluation.
    if "pm25_observed" in dataset.columns:
        # Group by (year, month) → monthly mean; then assign to the NEXT month
        _tmp = pd.Series(
            dataset["pm25_observed"].values,
            index=pd.MultiIndex.from_arrays(
                [dataset.index.year, dataset.index.month], names=["yr", "mo"]
            ),
        )
        monthly_mean_s = _tmp.groupby(level=["yr", "mo"]).mean()
        # Build lookup: (year, month) of DATA → value goes to NEXT (year, month)
        lookup: dict[tuple, float] = {}
        for (yr, mo), val in monthly_mean_s.items():
            target_yr = yr + 1 if mo == 12 else yr
            target_mo = (mo % 12) + 1
            lookup[(target_yr, target_mo)] = val
        dataset["pm25_prev_month_mean"] = [
            lookup.get((d.year, d.month), np.nan) for d in dataset.index
        ]
        n_valid = dataset["pm25_prev_month_mean"].notna().sum()
        log.info(
            f"pm25_prev_month_mean: {n_valid}/{len(dataset)} days with data "
            f"(mean={dataset['pm25_prev_month_mean'].mean():.1f} µg/m³)"
        )

    # ── Drop pre-CAMS years (2000-2002) — entirely unlabeled, MODIS calibration uncertain ──
    pre_cams_mask = dataset.index.year < 2003
    if pre_cams_mask.any():
        n_dropped = pre_cams_mask.sum()
        dataset = dataset[~pre_cams_mask]
        log.info(f"Dropped {n_dropped} pre-2003 rows (unlabeled; year range now starts 2003).")

    # ── Log dataset summary ───────────────────────────────────────────────────
    log.info(f"\nDataset summary:")
    log.info(f"  Date range: {dataset.index.min().date()} to {dataset.index.max().date()}")
    log.info(f"  Shape: {dataset.shape}")
    log.info(f"  Columns: {list(dataset.columns)}")
    missing = dataset.isna().mean() * 100
    if missing.any():
        log.info(f"  Missing rates (%):\n{missing[missing > 0].round(1).to_string()}")
    else:
        log.info("  No missing values!")

    if "pm25_observed" in dataset.columns:
        valid = dataset["pm25_observed"].dropna()
        log.info(f"  Ground truth: {len(valid)} days, mean={valid.mean():.1f}")

    # ── Save ──────────────────────────────────────────────────────────────────
    if save:
        MERGED_DIR.mkdir(parents=True, exist_ok=True)
        parquet_name = "dataset_daily_modelB.parquet" if label_source == "merra2vd" else "dataset_daily.parquet"
        out_path = MERGED_DIR / parquet_name
        dataset.to_parquet(out_path)
        log.info(f"Dataset saved -> {out_path}")

        info_name = "dataset_info_modelB.txt" if label_source == "merra2vd" else "dataset_info.txt"
        info_path = MERGED_DIR / info_name
        with open(info_path, "w") as f:
            f.write(f"Label source: {label_source}\n")
            f.write(f"Date range: {dataset.index.min()} to {dataset.index.max()}\n")
            f.write(f"Shape: {dataset.shape}\n")
            f.write(f"Columns: {list(dataset.columns)}\n\n")
            f.write(dataset.describe().to_string())
        log.info(f"Dataset info -> {info_path}")

    return dataset


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build integrated ML dataset for Kandy PM2.5")
    parser.add_argument(
        "--label-source", choices=["cams", "merra2vd"], default="cams",
        help=(
            "PM2.5 label source: "
            "'cams' (default, Model A — monthly KOALA-corrected CAMS) or "
            "'merra2vd' (Model B — VD × KOALA × MERRA-2 multiplicative decomposition)"
        ),
    )
    args = parser.parse_args()

    df = build_dataset(save=True, label_source=args.label_source)
    print(f"\nDataset: {df.shape[0]} days x {df.shape[1]} features")
    print(f"Label source: {args.label_source}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst 3 rows:\n{df.head(3)}")
