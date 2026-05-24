"""
run_pinn_chiangmai_validation.py — PINN v5 inference at real Air4Thai + PurpleAir stations.

This is the core validation script for the Chiang Mai validation report:
  "Does FourierPINNV3 (v5, fine-tuned on 2022 pseudo-labels) accurately predict
   PM2.5 at held-out real stations across 2021-2025?"

Strategy:
  - Load PINN v5 checkpoint (ep1100, R²=0.823, r_kblh=0.614 — best combined metrics)
  - For each (station, date) in chiangmai_all_stations_2021_2025.csv:
      1. Aggregate hourly obs → daily mean (skip days with <4 hourly obs)
      2. Load ERA5 for that year (per-year NC files)
      3. Bilinear interpolate ERA5 BLH, u10, v10, tp to station lat/lon
      4. Normalize coords: x/y ← CHIANGMAI_PINN_BBOX, blh ← BLH/2000
      5. Run PINN at 4 time steps (t=0, 6, 12, 18h/24), average → daily C_pinn
      6. Extract K (diffusivity), compare K vs BLH for physics validation
  - Compute per-station and per-season metrics (R², RMSE, MAE, bias, r)
  - Save:
      data/processed/stage2/chiangmai_pinn_vs_observations.parquet
      results/tables/chiangmai_pinn_station_metrics.json
      results/tables/chiangmai_pinn_seasonal_metrics.json

Usage:
    python run_pinn_chiangmai_validation.py
    python run_pinn_chiangmai_validation.py --checkpoint epoch_04000.pt  # Phase 3 best
    python run_pinn_chiangmai_validation.py --no-era5  # use only 2022 ERA5 for all years

Data requirements:
    - data/external/chiangmai/pm25/chiangmai_all_stations_2021_2025.csv  (Phase 1 ✅)
    - data/external/chiangmai/era5/chiangmai_era5_{year}.nc  (Phase 2a — 2022 ✅, others pending)
    - data/processed/pinn_inputs/chiangmai_elev_grid_100m.npz  (✅)
    - results/models/stage2_chiangmai_pinn/v5/checkpoints/epoch_01200.pt  (✅, closest to ep1100 peak)

Burning season definition:
    - burning: Feb–May (months 2-5) — biomass burning season in Chiang Mai
    - non-burning: Jun–Nov (months 6-11) — inter-monsoon, comparable to Kandy regime
    - other: Dec–Jan (months 12, 1) — cool season
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
    DATA_DIR, EXTERNAL_DIR, RESULTS_DIR,
    CHIANGMAI_PINN_BBOX,
    PINN_BLH_NORM_SCALE,
)

PROCESSED_DIR = DATA_DIR / "processed"

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("run_pinn_chiangmai_validation")

# ── Paths ─────────────────────────────────────────────────────────────────────
PM25_CSV    = EXTERNAL_DIR / "chiangmai" / "pm25" / "chiangmai_all_stations_2021_2025.csv"
ERA5_DIR    = EXTERNAL_DIR / "chiangmai" / "era5"
ELEV_NPZ    = PROCESSED_DIR / "pinn_inputs" / "chiangmai_elev_grid_100m.npz"
CKPT_DIR    = RESULTS_DIR / "models" / "stage2_chiangmai_pinn" / "v5" / "checkpoints"
OUT_PARQUET = PROCESSED_DIR / "stage2" / "chiangmai_pinn_vs_observations.parquet"
OUT_STATION = RESULTS_DIR / "tables" / "chiangmai_pinn_station_metrics.json"
OUT_SEASON  = RESULTS_DIR / "tables" / "chiangmai_pinn_seasonal_metrics.json"

DEFAULT_CHECKPOINT = "epoch_01200.pt"   # Closest to best combined ep1100 (R²=0.823, r_kblh=0.614)

# ── Season labels ─────────────────────────────────────────────────────────────
def get_season(month: int) -> str:
    if month in (2, 3, 4, 5):
        return "burning"       # Feb–May biomass burning season
    elif month in (6, 7, 8, 9, 10, 11):
        return "non-burning"   # Jun–Nov inter-monsoon (PINN training regime)
    else:
        return "cool"          # Dec–Jan cool/dry season

# Burning season definition for PINN training: only non-burning months (Jun-Nov)
# We validate ALL months to show how far off the PINN is during burning season.

MIN_HOURLY_OBS = 4    # Minimum hourly obs to compute daily mean


# ══════════════════════════════════════════════════════════════════════════════
# ERA5 Loading + Interpolation
# ══════════════════════════════════════════════════════════════════════════════

class ERA5Reader:
    """Cache ERA5 files by year and provide bilinear interpolation to station coords."""

    def __init__(self, era5_dir: Path, fallback_year: int = 2022):
        self.era5_dir = era5_dir
        self.fallback_year = fallback_year
        self._cache: dict = {}   # year → xarray.Dataset

    def _load(self, year: int):
        import xarray as xr
        path = self.era5_dir / f"chiangmai_era5_{year}.nc"
        if not path.exists():
            if year != self.fallback_year:
                log.warning("ERA5 %d not found — using %d as fallback", year, self.fallback_year)
                return self._load(self.fallback_year)
            else:
                raise FileNotFoundError(f"ERA5 file missing: {path}")
        log.info("Loading ERA5 %d...", year)
        ds = xr.open_dataset(str(path))
        return ds

    def get(self, year: int):
        if year not in self._cache:
            self._cache[year] = self._load(year)
        return self._cache[year]

    def interpolate(self, year: int, date: pd.Timestamp,
                    lat: float, lon: float) -> dict:
        """
        Bilinear interpolation of ERA5 daily mean at (lat, lon) for a given date.

        Returns dict with keys: blh, u10, v10, tp
        All values are daily means (averaging all hours in the date).
        """
        ds = self.get(year)

        # ERA5 time dimension (may be 'valid_time' or 'time')
        time_dim = "valid_time" if "valid_time" in ds.dims else "time"

        # Select date slice (all hours on this UTC date)
        date_slice = ds.sel(
            {time_dim: slice(
                f"{date.date()}T00:00:00",
                f"{date.date()}T23:59:59"
            )}
        )

        # Interpolate to station location
        try:
            interp_kwargs = {"latitude": lat, "longitude": lon, "method": "linear"}
            if "latitude" in ds.coords:
                point = date_slice.interp(**interp_kwargs)
            else:
                # Some ERA5 files use 'lat'/'lon'
                point = date_slice.interp(lat=lat, lon=lon, method="linear")
        except Exception as e:
            log.debug("ERA5 interp failed for %s at (%.4f, %.4f): %s", date.date(), lat, lon, e)
            return {"blh": 500.0, "u10": 0.0, "v10": 0.0, "tp": 0.0}

        def _get(var, alt_name=None, default=0.0):
            v = None
            for name in ([var] + ([alt_name] if alt_name else [])):
                if name in point.data_vars or name in point.coords:
                    arr = point[name].values
                    arr = arr[~np.isnan(arr)]
                    v = float(arr.mean()) if len(arr) > 0 else default
                    break
            return v if v is not None else default

        blh = max(_get("blh", default=500.0), 50.0)   # floor at 50m; ERA5 short name
        u10 = _get("u10", default=0.0)
        v10 = _get("v10", default=0.0)
        tp  = max(_get("tp", default=0.0), 0.0)    # no negative precip; ERA5 short name

        return {"blh": blh, "u10": u10, "v10": v10, "tp": tp}


# ══════════════════════════════════════════════════════════════════════════════
# Station coord normalisation
# ══════════════════════════════════════════════════════════════════════════════

def lat_lon_to_xy_norm(lat: float, lon: float) -> tuple[float, float]:
    """
    Convert geographic (lat, lon) → normalised (x, y) ∈ [-1, 1] in CHIANGMAI_PINN_BBOX.

    PINN input convention: x=lon-axis, y=lat-axis.
    """
    bbox = CHIANGMAI_PINN_BBOX
    x = 2.0 * (lon - bbox["lon_min"]) / (bbox["lon_max"] - bbox["lon_min"]) - 1.0
    y = 2.0 * (lat - bbox["lat_min"]) / (bbox["lat_max"] - bbox["lat_min"]) - 1.0
    return x, y


def load_station_elev(lat: float, lon: float, elev_grid: dict) -> float:
    """
    Sample elevation at station (lat, lon) from ChiangMai 150×150 elevation grid.

    elev_grid: loaded from chiangmai_elev_grid_100m.npz
    Keys: 'elev' (raw m), 'elev_norm' (0-1), 'lat_grid', 'lon_grid', 'elev_min', 'elev_max'
    Returns normalised elevation ∈ [0, 1].
    """
    bbox = CHIANGMAI_PINN_BBOX
    nx = ny = 150
    lat_arr = np.linspace(bbox["lat_min"], bbox["lat_max"], ny)
    lon_arr = np.linspace(bbox["lon_min"], bbox["lon_max"], nx)

    # Find nearest grid point
    i_lat = np.argmin(np.abs(lat_arr - lat))
    i_lon = np.argmin(np.abs(lon_arr - lon))

    # Use pre-computed normalised elevation from the grid file
    return float(np.clip(elev_grid["elev_norm"][i_lat, i_lon], 0.0, 1.0))


# ══════════════════════════════════════════════════════════════════════════════
# PINN Inference
# ══════════════════════════════════════════════════════════════════════════════

def load_model(ckpt_path: Path, device: str = "cpu"):
    """Load FourierPINNV3 from checkpoint."""
    import torch
    sys.path.insert(0, str(Path(__file__).parents[3]))
    from src.stage3_pinn.models.fourier_pinn_v3 import FourierPINNV3

    model = FourierPINNV3()
    state = torch.load(str(ckpt_path), map_location=device, weights_only=False)
    # Handle checkpoint format (may be full training state or just model state)
    if isinstance(state, dict) and "model_state_dict" in state:
        state = state["model_state_dict"]
    elif isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    model.load_state_dict(state, strict=False)
    model.eval()
    model.to(device)
    log.info("Model loaded: %d params", sum(p.numel() for p in model.parameters()))
    return model


def pinn_daily_mean(
    model,
    x_norm: float,
    y_norm: float,
    blh_norm: float,
    elev_norm: float,
    device: str = "cpu",
) -> tuple[float, float]:
    """
    Compute daily-mean PINN PM2.5 at a point.

    Runs model at 4 time steps (t=0, 6, 12, 18h / 24) and averages.
    Returns (C_pinn_mean, K_pinn_mean).
    """
    import torch
    t_hours = [0, 6, 12, 18]
    C_vals, K_vals = [], []
    with torch.no_grad():
        for h in t_hours:
            t_norm = h / 24.0
            xyt = torch.tensor(
                [[x_norm, y_norm, t_norm]], dtype=torch.float32, device=device
            )
            blh_t = torch.tensor([[blh_norm]], dtype=torch.float32, device=device)
            elev_t = torch.tensor([[elev_norm]], dtype=torch.float32, device=device)
            C, (Kx, Ky, _S) = model(xyt, blh=blh_t, elev=elev_t)
            C_vals.append(float(C.item()))
            K_vals.append(float((Kx + Ky).mean().item() / 2))
    return float(np.mean(C_vals)), float(np.mean(K_vals))


# ══════════════════════════════════════════════════════════════════════════════
# Metrics
# ══════════════════════════════════════════════════════════════════════════════

def compute_metrics(obs: np.ndarray, pred: np.ndarray) -> dict:
    """R², RMSE, MAE, bias, Pearson r for a pair of arrays."""
    from scipy import stats
    mask = np.isfinite(obs) & np.isfinite(pred)
    o, p = obs[mask], pred[mask]
    if len(o) < 2:
        return {"R2": np.nan, "RMSE": np.nan, "MAE": np.nan,
                "bias": np.nan, "r": np.nan, "n": len(o)}
    ss_res = np.sum((o - p) ** 2)
    ss_tot = np.sum((o - o.mean()) ** 2)
    r2 = 1 - ss_res / (ss_tot + 1e-10)
    rmse = float(np.sqrt(np.mean((o - p) ** 2)))
    mae  = float(np.mean(np.abs(o - p)))
    bias = float(np.mean(p - o))
    r, _ = stats.pearsonr(o, p)
    return {"R2": round(float(r2), 3), "RMSE": round(rmse, 2), "MAE": round(mae, 2),
            "bias": round(bias, 2), "r": round(float(r), 3), "n": int(len(o))}


# ══════════════════════════════════════════════════════════════════════════════
# Main Pipeline
# ══════════════════════════════════════════════════════════════════════════════

def run_validation(checkpoint: str = DEFAULT_CHECKPOINT, use_fallback_era5: bool = False):
    """Full validation pipeline."""
    ckpt_path = CKPT_DIR / checkpoint
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")
    if not PM25_CSV.exists():
        raise FileNotFoundError(f"Station obs not found: {PM25_CSV} — run Phase 1 first")

    # ── 1. Load observations ─────────────────────────────────────────────────
    log.info("Loading station observations from %s...", PM25_CSV)
    obs_df = pd.read_csv(PM25_CSV)
    obs_df["datetime_utc"] = pd.to_datetime(obs_df["datetime_utc"], utc=True)
    log.info("Obs: %d hourly rows, %d stations", len(obs_df), obs_df["location_name"].nunique())

    # Aggregate hourly → daily mean (skip days with < MIN_HOURLY_OBS obs)
    obs_df["date"] = obs_df["datetime_utc"].dt.date
    daily = (
        obs_df.groupby(["date", "location_id", "location_name", "lat", "lon", "provider"])
        .agg(pm25_obs=("pm25", "mean"), n_obs=("pm25", "count"))
        .reset_index()
    )
    daily = daily[daily["n_obs"] >= MIN_HOURLY_OBS].copy()
    daily["date"] = pd.to_datetime(daily["date"], utc=True)
    log.info("Daily obs: %d rows (≥%d hourly obs/day)", len(daily), MIN_HOURLY_OBS)

    # ── 2. Load elevation grid ──────────────────────────────────────────────
    log.info("Loading ChiangMai elevation grid...")
    elev_data = np.load(str(ELEV_NPZ))

    # ── 3. Load PINN model ──────────────────────────────────────────────────
    log.info("Loading PINN v5 checkpoint: %s", checkpoint)
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = load_model(ckpt_path, device)
    except Exception as e:
        log.error("Failed to load model: %s", e)
        raise

    # ── 4. Build ERA5 reader ────────────────────────────────────────────────
    era5_reader = ERA5Reader(ERA5_DIR, fallback_year=2022)

    # ── 5. Run inference ────────────────────────────────────────────────────
    log.info("Running PINN inference for %d station-days...", len(daily))

    results = []
    # Group by station for efficiency (avoid re-normalizing coords each row)
    station_elev_cache: dict = {}
    era5_cache_hits = {}

    for idx, row in daily.iterrows():
        date = row["date"]
        year = date.year
        lat, lon = float(row["lat"]), float(row["lon"])
        stn_id = row["location_id"]

        # Station coord normalisation (cached per station)
        if stn_id not in station_elev_cache:
            x_norm, y_norm = lat_lon_to_xy_norm(lat, lon)
            elev_norm = load_station_elev(lat, lon, elev_data)
            station_elev_cache[stn_id] = (x_norm, y_norm, elev_norm)
        x_norm, y_norm, elev_norm = station_elev_cache[stn_id]

        # ERA5 interpolation (fallback to 2022 if year missing)
        if use_fallback_era5:
            era5_year = 2022
            # Remap date to 2022 (same month-day, year=2022) so the date exists in the 2022 file
            try:
                era5_date = date.replace(year=2022)
            except ValueError:
                # Feb 29 in a leap year → use Feb 28
                era5_date = date.replace(year=2022, day=28)
        else:
            era5_year = year
            era5_date = date
        era5_key = (era5_year, str(era5_date.date()), stn_id)
        if era5_key not in era5_cache_hits:
            try:
                era5 = era5_reader.interpolate(era5_year, era5_date, lat, lon)
            except Exception as e:
                log.debug("ERA5 failed for %s: %s — skipping", era5_key, e)
                continue
            era5_cache_hits[era5_key] = era5
        era5 = era5_cache_hits[era5_key]

        blh_norm = era5["blh"] / PINN_BLH_NORM_SCALE

        # PINN inference
        try:
            C_pinn, K_pinn = pinn_daily_mean(
                model, x_norm, y_norm, blh_norm, elev_norm, device
            )
        except Exception as e:
            log.debug("PINN inference failed for %s: %s", era5_key, e)
            continue

        month = date.month
        results.append({
            "date":          date,
            "location_id":   stn_id,
            "location_name": row["location_name"],
            "lat":           lat,
            "lon":           lon,
            "provider":      row["provider"],
            "pm25_obs":      float(row["pm25_obs"]),
            "pm25_pinn":     float(C_pinn),
            "K_pinn":        float(K_pinn),
            "blh":           float(era5["blh"]),
            "blh_norm":      float(blh_norm),
            "u10":           float(era5["u10"]),
            "v10":           float(era5["v10"]),
            "tp":            float(era5["tp"]),
            "month":         month,
            "year":          year,
            "season":        get_season(month),
            "n_obs_hours":   int(row["n_obs"]),
        })

        if idx % 500 == 0:
            log.info("  Progress: %d / %d rows", idx, len(daily))

    if not results:
        log.error("No valid inference results — check ERA5 files and checkpoint")
        return

    result_df = pd.DataFrame(results)
    log.info("Inference complete: %d station-days", len(result_df))

    # ── 6. Compute metrics ──────────────────────────────────────────────────
    obs_arr  = result_df["pm25_obs"].values
    pred_arr = result_df["pm25_pinn"].values

    overall_metrics = compute_metrics(obs_arr, pred_arr)
    log.info("Overall metrics: R²=%.3f, RMSE=%.2f, bias=%.2f, r=%.3f (n=%d)",
             overall_metrics["R2"], overall_metrics["RMSE"],
             overall_metrics["bias"], overall_metrics["r"], overall_metrics["n"])

    # Per-station
    station_metrics = {}
    for stn, grp in result_df.groupby("location_name"):
        m = compute_metrics(grp["pm25_obs"].values, grp["pm25_pinn"].values)
        station_metrics[stn] = {**m, "lat": float(grp["lat"].iloc[0]),
                                "lon": float(grp["lon"].iloc[0]),
                                "provider": grp["provider"].iloc[0]}

    # Per-season
    season_metrics = {"overall": overall_metrics}
    for season in ["burning", "non-burning", "cool"]:
        sub = result_df[result_df["season"] == season]
        season_metrics[season] = compute_metrics(
            sub["pm25_obs"].values, sub["pm25_pinn"].values
        )

    # K–BLH correlation (physics gate: r > 0.50)
    kblh_mask = np.isfinite(result_df["K_pinn"]) & np.isfinite(result_df["blh"])
    if kblh_mask.sum() > 10:
        from scipy import stats
        r_kblh, p_kblh = stats.pearsonr(
            result_df.loc[kblh_mask, "blh"].values,
            result_df.loc[kblh_mask, "K_pinn"].values,
        )
        season_metrics["K_BLH_r"] = round(float(r_kblh), 3)
        season_metrics["K_BLH_p"] = round(float(p_kblh), 4)
        log.info("K–BLH r = %.3f (physics gate: >0.50 → %s)",
                 r_kblh, "PASS" if r_kblh > 0.50 else "FAIL")

    # ── 7. Save outputs ─────────────────────────────────────────────────────
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_parquet(str(OUT_PARQUET), index=False)
    log.info("Saved parquet: %s (%d rows)", OUT_PARQUET, len(result_df))

    OUT_STATION.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_STATION, "w") as f:
        json.dump(station_metrics, f, indent=2)
    with open(OUT_SEASON, "w") as f:
        json.dump(season_metrics, f, indent=2)
    log.info("Saved station metrics → %s", OUT_STATION)
    log.info("Saved season metrics  → %s", OUT_SEASON)

    # ── 8. Print summary ─────────────────────────────────────────────────────
    log.info("\n=== VALIDATION SUMMARY ===")
    log.info("Overall:      R²=%.3f, RMSE=%.2f, bias=%.2f, r=%.3f",
             overall_metrics["R2"], overall_metrics["RMSE"],
             overall_metrics["bias"], overall_metrics["r"])
    log.info("Non-burning:  R²=%.3f, RMSE=%.2f (gate: >0.50 → %s)",
             season_metrics["non-burning"]["R2"], season_metrics["non-burning"]["RMSE"],
             "PASS" if season_metrics["non-burning"]["R2"] > 0.50 else "FAIL")
    log.info("Burning:      R²=%.3f, RMSE=%.2f (expected lower — OOD regime)",
             season_metrics["burning"]["R2"], season_metrics["burning"]["RMSE"])
    log.info("Per-station:")
    for stn, m in sorted(station_metrics.items(), key=lambda x: -x[1]["R2"]):
        log.info("  %-45s R²=%.3f RMSE=%.2f bias=%.2f n=%d",
                 stn[:45], m["R2"], m["RMSE"], m["bias"], m["n"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint",   default=DEFAULT_CHECKPOINT,
                        help="Checkpoint filename in v5/checkpoints/ dir")
    parser.add_argument("--no-era5",      action="store_true",
                        help="Use only 2022 ERA5 for all years (fallback mode)")
    args = parser.parse_args()
    run_validation(args.checkpoint, use_fallback_era5=args.no_era5)


if __name__ == "__main__":
    main()
