"""
train_chiangmai_pinn.py — FourierPINNV3 training on Chiang Mai (Experiment B).

PURPOSE — EXPERIMENT B DESIGN
-------------------------------
Chiang Mai is the HELD-OUT transfer test for the full three-stage pipeline:
  Stage 1 → XGBoost city-mean predictions → pixel pseudo-labels (elevation gradient)
  Stage 2 → PINN trained on pseudo-labels (NOT station obs)
  Validation → Compare PINN C output vs Air4Thai ground truth (3 stations, HELD OUT from data loss)

This exactly mirrors the Kandy workflow, where no station observations exist during training.
The key question: can PDE physics (road kernel + BLH + terrain) produce spatial structure that
matches real ground-truth observations, even when trained only on coarse pseudo-labels?

DATA APPROACH
-------------
Data loss  : 256 random pixels per epoch from chiangmai_stage1_pixel_preds.npz (150×150×236 days)
             Pseudo-label = C_city(t) × exp(−λ × (elev−mean)/1000), λ=0.20
BC loss    : Air4Thai city-mean (3-station daily average) — accurate magnitude constraint
Validation : 3 Air4Thai stations (individual obs, NEVER used in any loss)

The Air4Thai individual station obs are held out from ALL loss functions.
Only the city-mean (average) enters the BC loss — individual spatial variation is latent.

WARM-START
----------
Warm-start from Medellín v7 best checkpoint (epoch_03800.pt, spatial_R²=0.959, r_kblh=0.761).
Road kernel swapped to Chiang Mai OSM: chiangmai_road_kernel_100m.npz.
Spatial Fourier features (SpatialEmbedding) encode coordinates, not city-specific knowledge —
they transfer as random initialisation anchored by the v7 trunk/diffusion weights.

COORDINATE CONVENTION
---------------------
[-1, 1] throughout — consistent with FourierPINNV3 docstring and per-station parquet.
  x_norm = (lon - lon_ctr) / lon_half  ∈ [-1, 1]  (West-East)
  y_norm = (lat - lat_ctr) / lat_half  ∈ [-1, 1]  (South-North)
  t_norm = h / 24.0                   ∈ [0, 1]   (hour of day)

GATE CONDITIONS (Chiang Mai Experiment B)
------------------------------------------
G1: spatial R² > 0.30 on 3 Air4Thai stations (lower than Medellín's 0.50 — only 3 pts)
G2: K–BLH r > 0.50 (BLH conditioning active; same threshold as Medellín)
G3: mean bias < ±5 µg/m³ across Air4Thai stations

USAGE
-----
    # Warm-start from Medellín v7 (default — recommended)
    python src/stage2_transfer/train_chiangmai_pinn.py

    # Cold start (ablation)
    python src/stage2_transfer/train_chiangmai_pinn.py --cold-start

    # With W&B tracking
    python src/stage2_transfer/train_chiangmai_pinn.py --wandb

    # Custom epoch count
    python src/stage2_transfer/train_chiangmai_pinn.py --epochs 3000
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import (
    LOG_FORMAT, LOG_DATEFMT,
    MODELS_DIR, PINN_INPUT_DIR,
    CHIANGMAI_PINN_BBOX, PINN_BLH_NORM_SCALE,
    N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("train_chiangmai_pinn")

# ── Paths ─────────────────────────────────────────────────────────────────────
STAGE2_PROC_DIR  = Path(__file__).parents[2] / "data" / "processed" / "stage2"
PERSTATION_PARQ  = STAGE2_PROC_DIR / "chiangmai_stage2_perstation.parquet"
PIXEL_PREDS_NPZ  = STAGE2_PROC_DIR / "chiangmai_stage1_pixel_preds.npz"
CITY_PREDS_PARQ  = STAGE2_PROC_DIR / "chiangmai_stage1_predictions.parquet"
ROAD_KERNEL_NPZ  = PINN_INPUT_DIR  / "chiangmai_road_kernel_100m.npz"
ELEV_GRID_NPZ    = PINN_INPUT_DIR  / "chiangmai_elev_grid_100m.npz"
CHECKPOINT_DIR   = MODELS_DIR / "stage2_chiangmai_pinn"
ERA5_NC          = Path(__file__).parents[2] / "data" / "external" / "chiangmai" / "era5" / "chiangmai_era5_2022.nc"

# Medellín v7 warm-start path (best checkpoint — R²=0.959, r_kblh=0.761)
MEDELLIN_V7_CKPT = MODELS_DIR / "stage2_medellin_pinn" / "v7" / "checkpoints" / "epoch_03800.pt"

# Domain physical dimensions (for PDE coordinate scaling)
# LY_M = Δlat × 111320 m/° = 0.1351° × 111320 ≈ 15040 m
# LX_M = Δlon × cos(lat_ctr°) × 111320 = 0.1428° × cos(18.78°) × 111320 ≈ 15010 m
_bbox = CHIANGMAI_PINN_BBOX
LX_M = (_bbox["lon_max"] - _bbox["lon_min"]) * np.cos(np.radians((_bbox["lat_min"] + _bbox["lat_max"]) / 2)) * 111320.0
LY_M = (_bbox["lat_max"] - _bbox["lat_min"]) * 111320.0

# Coordinate centroid for [-1,1] normalisation
LON_CTR  = (_bbox["lon_min"] + _bbox["lon_max"]) / 2.0
LAT_CTR  = (_bbox["lat_min"] + _bbox["lat_max"]) / 2.0
LON_HALF = (_bbox["lon_max"] - _bbox["lon_min"]) / 2.0
LAT_HALF = (_bbox["lat_max"] - _bbox["lat_min"]) / 2.0

WANDB_PROJECT = "kandy-pinn"

# ── Training defaults ──────────────────────────────────────────────────────────
DEFAULT_EPOCHS     = 5000
DEFAULT_LR         = 3e-4
SAVE_EVERY         = 100
SNAPSHOT_HOURS     = [0, 3, 6, 9, 12, 15, 18, 21]
SPATIAL_EVAL_EVERY = 50
N_PIXELS_PER_EPOCH = 256   # random pixels sampled from pseudo-label grid per epoch
NON_BURNING_MONTHS = [5, 6, 7, 8, 9, 10, 11, 12]


# ─────────────────────────────────────────────────────────────────────────────
# CURRICULUM
# ─────────────────────────────────────────────────────────────────────────────

def get_weights(epoch: int, n_epochs: int) -> dict:
    """
    Three-phase curriculum — v2 fixes applied (v1 collapse at ep1250 diagnosed).

    Phase 1 (0–40%):  Pure data — pixel pseudo-labels establish temporal magnitude.
                       Extended from 25%→40%: 3-station regime needs more time to
                       anchor before any PDE onset (v1 lesson: PDE at ep1250 collapsed).
    Phase 2 (40–65%): Linear ramp λ_pde 0→0.05. λ_data 0.75→0.60.
                       λ_pde_max=0.05 (NOT 0.15): 3 stations vs Medellín's 11 means
                       the data anchor is weaker — lower PDE weight prevents bias drift.
    Phase 3 (65–100%): λ_pde=0.05, λ_data=0.60, λ_bc=0.15, λ_kblh=0.15.
                        Data dominance maintained: λ_data=0.60 >> λ_pde=0.05.
    """
    p1_end = int(0.40 * n_epochs)
    p2_end = int(0.65 * n_epochs)

    if epoch < p1_end:
        return dict(pde=0.00, data=0.75, bc=0.20, kblh=0.05)
    elif epoch < p2_end:
        t = (epoch - p1_end) / max(1, p2_end - p1_end)
        pde  = t * 0.05
        data = 0.75 + t * (0.60 - 0.75)
        bc   = 0.20 + t * (0.15 - 0.20)
        kblh = 0.05 + t * (0.15 - 0.05)
        return dict(pde=pde, data=data, bc=bc, kblh=kblh)
    else:
        return dict(pde=0.05, data=0.60, bc=0.15, kblh=0.15)


# ─────────────────────────────────────────────────────────────────────────────
# COORDINATE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def lat_to_ynorm(lat: np.ndarray) -> np.ndarray:
    """Convert latitude → y_norm ∈ [-1, 1]."""
    return ((lat - LAT_CTR) / LAT_HALF).astype(np.float32)


def lon_to_xnorm(lon: np.ndarray) -> np.ndarray:
    """Convert longitude → x_norm ∈ [-1, 1]."""
    return ((lon - LON_CTR) / LON_HALF).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_chiangmai_data() -> tuple:
    """
    Load Chiang Mai training data for PINN Experiment B.

    Returns
    -------
    daily_sta_a4t : DataFrame — Air4Thai per-station daily data (validation only).
        Columns: date, station_id, pm25, x_norm, y_norm, blh, u10, v10, tp
    city_mean     : Series (date → city-mean PM2.5 from Air4Thai) — BC target.
    pm25_var      : float — PM2.5 variance for loss normalisation.
    pixel_preds   : np.ndarray (N_days, 150, 150) — Stage 1 pseudo-labels.
    pixel_dates   : np.ndarray of str '2022-MM-DD' — dates for pixel_preds rows.
    pixel_xnorm   : np.ndarray (150,) — x_norm values for pixel columns.
    pixel_ynorm   : np.ndarray (150,) — y_norm values for pixel rows.
    pixel_elev    : np.ndarray (150, 150) — elev_norm values (for elev_interp in data loss).
    """
    # ── Per-station (Air4Thai only) ──────────────────────────────────────────
    if not PERSTATION_PARQ.exists():
        raise FileNotFoundError(f"Per-station parquet not found: {PERSTATION_PARQ}")

    df = pd.read_parquet(PERSTATION_PARQ)
    df["date"] = pd.to_datetime(df["datetime_utc"]).dt.tz_localize(None).dt.normalize()

    # Keep Air4Thai only for spatial validation
    a4t = df[df["provider"] == "Air4Thai"].copy()

    agg_cols = {k: v for k, v in {
        "pm25":   "mean",
        "x_norm": "first",
        "y_norm": "first",
        "lat":    "first",
        "lon":    "first",
        "blh":    "mean",
        "u10":    "mean",
        "v10":    "mean",
        "tp":     "sum",
    }.items() if k in a4t.columns}

    daily_sta = (
        a4t.groupby(["date", "station_id"])
        .agg(agg_cols)
        .reset_index()
    )
    daily_sta = daily_sta.dropna(subset=["pm25"])

    # Ensure x_norm/y_norm are in [-1,1] convention (computed at build time)
    # Re-derive from lat/lon to guarantee consistency with PINN coordinate system
    if "lat" in daily_sta.columns:
        daily_sta["y_norm"] = lat_to_ynorm(daily_sta["lat"].values)
    if "lon" in daily_sta.columns:
        daily_sta["x_norm"] = lon_to_xnorm(daily_sta["lon"].values)

    city_mean = daily_sta.groupby("date")["pm25"].mean()
    pm25_var  = float(daily_sta["pm25"].std() ** 2)

    log.info(f"Air4Thai daily: {len(daily_sta)} station-days, "
             f"{daily_sta['station_id'].nunique()} stations, "
             f"{daily_sta['date'].nunique()} dates")
    log.info(f"  Date range: {daily_sta['date'].min().date()} – {daily_sta['date'].max().date()}")
    log.info(f"  PM2.5: mean={daily_sta['pm25'].mean():.1f}±{daily_sta['pm25'].std():.1f} µg/m³")
    log.info(f"  PM2.5 variance (loss normalisation): {pm25_var:.2f}")

    # ── Pixel pseudo-labels ──────────────────────────────────────────────────
    if not PIXEL_PREDS_NPZ.exists():
        raise FileNotFoundError(
            f"Pixel pseudo-labels not found: {PIXEL_PREDS_NPZ}\n"
            "Run: python src/stage2_transfer/chiangmai_train_stage1.py"
        )
    pix_data    = np.load(str(PIXEL_PREDS_NPZ))
    pixel_preds = pix_data["pixel_preds"]   # (N_days, 150, 150)
    pixel_dates = pix_data["dates"]         # str array 'YYYY-MM-DD'

    log.info(f"Pixel pseudo-labels: shape={pixel_preds.shape}, "
             f"mean={pixel_preds.mean():.1f}, std={pixel_preds.std():.2f} µg/m³")

    # ── Elev grid for pixel coordinate mapping ───────────────────────────────
    if not ELEV_GRID_NPZ.exists():
        raise FileNotFoundError(f"Elev grid not found: {ELEV_GRID_NPZ}")

    elev_data    = np.load(str(ELEV_GRID_NPZ))
    elev_norm    = elev_data["elev_norm"].astype(np.float32)  # (150, 150) normalised [0,1]
    lat_grid     = elev_data["lat_grid"]   # (150, 150)
    lon_grid     = elev_data["lon_grid"]   # (150, 150)

    # Build pixel coordinate arrays in [-1,1]
    lat_1d      = lat_grid[:, 0]   # (150,) — row → lat (row 0 = lat_min, row 149 = lat_max)
    lon_1d      = lon_grid[0, :]   # (150,) — col → lon
    pixel_ynorm = lat_to_ynorm(lat_1d)   # (150,)
    pixel_xnorm = lon_to_xnorm(lon_1d)   # (150,)

    log.info(f"Pixel grid coords: x_norm=[{pixel_xnorm.min():.3f},{pixel_xnorm.max():.3f}], "
             f"y_norm=[{pixel_ynorm.min():.3f},{pixel_ynorm.max():.3f}]")

    return (daily_sta, city_mean, pm25_var,
            pixel_preds, pixel_dates, pixel_xnorm, pixel_ynorm, elev_norm)


def load_era5_blh_hourly() -> dict:
    """
    Load ERA5 hourly BLH for Chiang Mai 2022.

    Returns { pd.Timestamp(midnight) → { hour → blh_m } }.
    Falls back to empty dict (daily-mean from perstation parquet) if file missing.
    """
    if not ERA5_NC.exists():
        log.warning(f"ERA5 nc not found: {ERA5_NC} — per-snapshot BLH disabled.")
        return {}
    try:
        import xarray as xr
    except ImportError:
        log.warning("xarray not installed — per-snapshot BLH disabled.")
        return {}

    ds      = xr.open_dataset(str(ERA5_NC))
    blh_da  = ds["blh"]
    spatial_dims = [d for d in blh_da.dims if d != "valid_time"]
    blh_ts  = blh_da.mean(dim=spatial_dims).values.ravel()
    times   = pd.to_datetime(ds["valid_time"].values).tz_localize(None)
    ds.close()

    result: dict = {}
    for t, b in zip(times, blh_ts):
        date_key = t.normalize()
        result.setdefault(date_key, {})[t.hour] = float(b)

    all_blh = list(blh_ts)
    log.info(f"ERA5 hourly BLH loaded: {len(result)} dates, "
             f"range=[{min(all_blh):.0f}, {max(all_blh):.0f}] m")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# TERRAIN HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def build_elev_interpolator():
    """
    Build 2D bilinear interpolator for elev_norm over CHIANGMAI_PINN_BBOX.
    Coordinates in [-1, 1] (consistent with FourierPINNV3 input convention).
    """
    from scipy.interpolate import RegularGridInterpolator

    if not ELEV_GRID_NPZ.exists():
        raise FileNotFoundError(f"Elev grid not found: {ELEV_GRID_NPZ}")

    elev_data = np.load(str(ELEV_GRID_NPZ))
    elev_norm = elev_data["elev_norm"]   # (150, 150)
    lat_grid  = elev_data["lat_grid"]
    lon_grid  = elev_data["lon_grid"]

    lat_1d = lat_grid[:, 0]
    lon_1d = lon_grid[0, :]
    y_vals = lat_to_ynorm(lat_1d)   # [-1, 1]
    x_vals = lon_to_xnorm(lon_1d)   # [-1, 1]

    interp = RegularGridInterpolator(
        (y_vals, x_vals), elev_norm,
        method="linear", bounds_error=False, fill_value=0.5,
    )

    def query(x_norm_arr: np.ndarray, y_norm_arr: np.ndarray) -> np.ndarray:
        pts = np.stack([y_norm_arr.ravel(), x_norm_arr.ravel()], axis=1)
        return interp(pts).reshape(x_norm_arr.shape).astype(np.float32)

    log.info(f"Elev interpolator built ([-1,1] coords): "
             f"elev_norm range=[{elev_norm.min():.3f}, {elev_norm.max():.3f}]")
    return query


# ─────────────────────────────────────────────────────────────────────────────
# MODEL
# ─────────────────────────────────────────────────────────────────────────────

def build_model(device, warm_start_path=None, cold_start=False):
    """
    Build FourierPINNV3 for Chiang Mai.

    Default: warm-start from Medellín v7 best checkpoint (epoch_03800.pt).
    Road kernel swapped to chiangmai_road_kernel_100m.npz.
    """
    import torch
    from src.stage3_pinn.models.fourier_pinn_v3 import FourierPINNV3

    if not ROAD_KERNEL_NPZ.exists():
        raise FileNotFoundError(
            f"Road kernel not found: {ROAD_KERNEL_NPZ}\n"
            "Run: python src/stage2_transfer/chiangmai_terrain.py"
        )

    model = FourierPINNV3(road_kernel_path=ROAD_KERNEL_NPZ).to(device)
    log.info(f"FourierPINNV3: {sum(p.numel() for p in model.parameters()):,} params "
             f"(road_kernel=chiangmai)")

    if cold_start:
        log.info("Cold start: full random Xavier initialisation")
        return model

    # Resolve warm-start path
    ws_path = warm_start_path or str(MEDELLIN_V7_CKPT)
    if Path(ws_path).exists():
        ckpt  = torch.load(str(ws_path), map_location=device, weights_only=False)
        state = ckpt.get("model_state_dict", ckpt)
        model.load_state_dict(state)
        log.info(f"Warm-started from Medellín v7: {Path(ws_path).name}")
        log.info("  Road kernel buffer replaced with Chiang Mai OSM kernel.")
    else:
        log.warning(f"Warm-start path not found: {ws_path} — using cold start.")

    return model


# ─────────────────────────────────────────────────────────────────────────────
# COLLOCATION SAMPLING ([-1, 1] domain)
# ─────────────────────────────────────────────────────────────────────────────

def sample_collocation(n_interior: int, n_boundary: int, rng) -> tuple:
    """Sample (x_norm, y_norm) in [-1,1]² for interior and boundary."""
    xy_int = rng.uniform(-1.0, 1.0, (n_interior, 2)).astype(np.float32)

    n_each = n_boundary // 4
    edge0  = np.stack([rng.uniform(-1, 1, n_each), np.full(n_each, -1.0)], 1)  # bottom
    edge1  = np.stack([rng.uniform(-1, 1, n_each), np.full(n_each,  1.0)], 1)  # top
    edge2  = np.stack([np.full(n_each, -1.0),       rng.uniform(-1, 1, n_each)], 1)  # left
    edge3  = np.stack([np.full(n_each,  1.0),        rng.uniform(-1, 1, n_each)], 1)  # right
    xy_bnd = np.concatenate([edge0, edge1, edge2, edge3], axis=0).astype(np.float32)

    return xy_int, xy_bnd


# ─────────────────────────────────────────────────────────────────────────────
# SPATIAL VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def spatial_validation(model, daily_sta: pd.DataFrame, elev_interp, device) -> dict:
    """
    Compute spatial validation metrics across 3 Air4Thai stations.

    Evaluates C at station locations at noon (t=0.5) for all available dates.
    Returns: spatial_R², std_C_sta, r_kblh, mean_bias, per-station stats.

    Note: With only 3 stations, spatial_R² has high variance. Gate threshold is 0.30.
    """
    import torch
    from sklearn.metrics import r2_score

    model.eval()
    dates = sorted(daily_sta["date"].unique())

    sta_pred_means = {}
    sta_obs_means  = {}
    sta_residuals  = {}
    k_vals   = []
    blh_vals = []

    with torch.no_grad():
        for date in dates:
            day_df = daily_sta[daily_sta["date"] == date]
            if len(day_df) < 2:
                continue

            x_np    = day_df["x_norm"].values.astype(np.float32)
            y_np    = day_df["y_norm"].values.astype(np.float32)
            elev_np = elev_interp(x_np, y_np)
            blh_day = float(day_df["blh"].mean()) if "blh" in day_df.columns else 1000.0
            blh_n   = blh_day / PINN_BLH_NORM_SCALE

            xyt   = torch.tensor(
                np.stack([x_np, y_np, np.full_like(x_np, 0.5)], axis=1),   # noon
                dtype=torch.float32, device=device,
            )
            blh_t  = torch.full((len(x_np), 1), blh_n,  dtype=torch.float32, device=device)
            elev_t = torch.tensor(elev_np[:, None],      dtype=torch.float32, device=device)

            C, (Kx, Ky, _) = model(xyt, blh=blh_t, elev=elev_t)
            C_np = C.squeeze().cpu().numpy()
            if C_np.ndim == 0:
                C_np = C_np[np.newaxis]

            for i, (sid, obs) in enumerate(zip(day_df["station_id"].values, day_df["pm25"].values)):
                sta_pred_means.setdefault(sid, []).append(float(C_np[i]))
                sta_obs_means.setdefault(sid, []).append(float(obs))
                sta_residuals.setdefault(sid, []).append(float(C_np[i]) - float(obs))

            k_vals.append(float((Kx.mean() + Ky.mean()) / 2.0))
            blh_vals.append(blh_n)

    model.train()

    station_ids = sorted(sta_pred_means.keys())
    pred_means  = np.array([np.mean(sta_pred_means[s]) for s in station_ids])
    obs_means   = np.array([np.mean(sta_obs_means[s])  for s in station_ids])

    # With 3 stations, R² has high variance — report alongside n_stations
    spatial_r2 = float(r2_score(obs_means, pred_means)) if len(pred_means) >= 2 else float("nan")
    std_C_sta  = float(np.std(pred_means))
    mean_bias  = float(np.mean([np.mean(sta_residuals[s]) for s in station_ids]))

    if len(k_vals) >= 5 and np.std(blh_vals) > 1e-3:
        r_kblh = float(np.corrcoef(blh_vals, k_vals)[0, 1])
    else:
        r_kblh = float("nan")

    per_station_bias = {s: float(np.mean(sta_residuals[s])) for s in station_ids}
    per_station_rmse = {s: float(np.sqrt(np.mean(np.array(sta_residuals[s])**2))) for s in station_ids}

    log.info("  Per-station residuals (Air4Thai):")
    log.info(f"  {'Station':>12}  {'obs_mean':>8}  {'pred_mean':>9}  {'bias':>7}  {'RMSE':>7}")
    for s in station_ids:
        log.info(
            f"  {s:>12}  {np.mean(sta_obs_means[s]):8.1f}  "
            f"{np.mean(sta_pred_means[s]):9.1f}  "
            f"{per_station_bias[s]:+7.1f}  {per_station_rmse[s]:7.2f}"
        )

    return {
        "spatial_R2":        spatial_r2,
        "std_C_sta":         std_C_sta,
        "r_kblh":            r_kblh,
        "mean_bias":         mean_bias,
        "n_stations":        len(pred_means),
        "obs_means":         obs_means.tolist(),
        "pred_means":        pred_means.tolist(),
        "per_station_bias":  per_station_bias,
        "per_station_rmse":  per_station_rmse,
    }


def check_gates(val: dict) -> dict:
    """Check Chiang Mai Experiment B gate conditions."""
    return {
        "G1_spatial_R2_pass": val["spatial_R2"] > 0.30,
        "G2_r_kblh_pass":     val["r_kblh"]     > 0.50,
        "G3_bias_pass":       abs(val.get("mean_bias", 999)) < 5.0,
        "spatial_R2":         val["spatial_R2"],
        "r_kblh":             val["r_kblh"],
        "mean_bias":          val.get("mean_bias", float("nan")),
    }


# ─────────────────────────────────────────────────────────────────────────────
# PEARSON CORRELATION (differentiable)
# ─────────────────────────────────────────────────────────────────────────────

def _pearson_corr(a, b):
    a_c = a - a.mean()
    b_c = b - b.mean()
    return (a_c * b_c).sum() / (a_c.norm() * b_c.norm() + 1e-8)


# ─────────────────────────────────────────────────────────────────────────────
# TRAINING LOOP
# ─────────────────────────────────────────────────────────────────────────────

def train(
    model,
    daily_sta:    pd.DataFrame,
    city_mean:    pd.Series,
    pm25_var:     float,
    elev_interp,
    pixel_preds:  np.ndarray,
    pixel_dates:  np.ndarray,
    pixel_xnorm:  np.ndarray,
    pixel_ynorm:  np.ndarray,
    pixel_elev:   np.ndarray,
    n_epochs:     int,
    lr:           float,
    device,
    wandb_run=None,
    save_every:   int = SAVE_EVERY,
) -> list:
    """
    Chiang Mai PINN training loop (Experiment B).

    KEY DIFFERENCE from Medellín:
      Data loss = pixel pseudo-labels (NOT Air4Thai station observations).
      City-mean from Air4Thai used only as BC loss target.
      Air4Thai individual station obs are NEVER seen during training.
    """
    import torch
    import torch.optim as optim
    from src.stage3_pinn.physics.pde_residual_v3 import pde_residual_v3

    blh_hourly = load_era5_blh_hourly()
    log.info(f"Per-snapshot BLH: {'ENABLED' if blh_hourly else 'DISABLED (daily-mean fallback)'}")

    optimizer = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()), lr=lr
    )
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_epochs, eta_min=1e-6)

    rng     = np.random.default_rng(42)
    n_days  = len(pixel_dates)

    # Unique dates with Air4Thai obs (for BC loss and kblh computation)
    a4t_dates = np.array(sorted(daily_sta["date"].unique()))

    # Pre-flatten pixel grid for sampling
    H, W = 150, 150
    row_grid, col_grid = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
    pix_rows_all = row_grid.ravel()   # (22500,)
    pix_cols_all = col_grid.ravel()

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    loss_history = []
    pm25_var_t   = max(pm25_var, 1.0)

    # Pre-build collocation layout in [-1,1]
    xy_int_np, xy_bnd_np = sample_collocation(N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY, rng)
    elev_int_np = elev_interp(xy_int_np[:, 0], xy_int_np[:, 1])

    log.info(f"Training: {n_epochs} epochs, {n_days} pixel dates, "
             f"{len(a4t_dates)} Air4Thai dates, device={device}")
    log.info(f"Domain: LX={LX_M:.0f}m, LY={LY_M:.0f}m")
    log.info(f"Collocation: {len(xy_int_np)} interior + {len(xy_bnd_np)} boundary ([-1,1]²)")

    t_start = time.time()

    for epoch in range(n_epochs):
        model.train()
        w = get_weights(epoch, n_epochs)

        # Refresh collocation every 200 epochs
        if epoch > 0 and epoch % 200 == 0:
            xy_int_np, xy_bnd_np = sample_collocation(
                N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY, rng
            )
            elev_int_np = elev_interp(xy_int_np[:, 0], xy_int_np[:, 1])

        # ── Sample a random date ───────────────────────────────────────────
        # Sample from pixel_dates (236 days); also need Air4Thai data for same date
        # Try to find a date that exists in both pixel_preds and Air4Thai
        day_idx  = rng.integers(0, n_days)
        date_str = str(pixel_dates[day_idx])
        date_ts  = pd.Timestamp(date_str)

        # Get Air4Thai data for BC loss (may be missing → fallback)
        day_df_a4t  = daily_sta[daily_sta["date"] == date_ts]
        has_a4t     = len(day_df_a4t) >= 1
        city_mean_today = float(city_mean.get(date_ts, np.nan))
        if np.isnan(city_mean_today) and has_a4t:
            city_mean_today = float(day_df_a4t["pm25"].mean())

        # ERA5 met for this date
        blh_today  = float(day_df_a4t["blh"].mean()) if has_a4t and "blh" in day_df_a4t.columns else 1000.0
        wind_u     = float(day_df_a4t["u10"].mean()) if has_a4t and "u10" in day_df_a4t.columns else 0.5
        wind_v     = float(day_df_a4t["v10"].mean()) if has_a4t and "v10" in day_df_a4t.columns else 0.5
        precip_raw = float(day_df_a4t["tp"].sum())   if has_a4t and "tp" in day_df_a4t.columns else 0.0
        precip_mmh = max(0.0, precip_raw * 1000.0 / 24.0)

        # ── Sample N_PIXELS_PER_EPOCH random pixels for data loss ─────────
        pix_idx    = rng.integers(0, H * W, size=N_PIXELS_PER_EPOCH)
        pix_rows   = pix_rows_all[pix_idx]   # (N_PIX,)
        pix_cols   = pix_cols_all[pix_idx]
        x_pix_np   = pixel_xnorm[pix_cols].astype(np.float32)  # (N_PIX,)
        y_pix_np   = pixel_ynorm[pix_rows].astype(np.float32)
        C_pseudo   = pixel_preds[day_idx, pix_rows, pix_cols].astype(np.float32)   # (N_PIX,)
        elev_pix_np = pixel_elev[pix_rows, pix_cols].astype(np.float32)            # (N_PIX,)

        optimizer.zero_grad()

        # ── 8-snapshot quasi-steady-state loop ────────────────────────────
        L_pde_day = torch.zeros(1, device=device)
        C_hourly  = []   # C at pixel locations per snapshot → daily mean
        k_means   = []

        for h in SNAPSHOT_HOURS:
            t_norm = h / 24.0

            blh_h_m = float(blh_hourly.get(date_ts, {}).get(h, blh_today))
            blh_h_n = blh_h_m / PINN_BLH_NORM_SCALE

            # Interior PDE
            if w["pde"] > 0:
                t_int_np = np.full((len(xy_int_np), 1), t_norm, dtype=np.float32)
                xyt_int  = torch.tensor(
                    np.hstack([xy_int_np, t_int_np]),
                    dtype=torch.float32, device=device,
                ).requires_grad_(True)
                blh_int  = torch.full((len(xy_int_np), 1), blh_h_n, dtype=torch.float32, device=device)
                blh_m_int = torch.full((len(xy_int_np), 1), blh_h_m, dtype=torch.float32, device=device)
                elev_int  = torch.tensor(elev_int_np[:, None], dtype=torch.float32, device=device)
                wu_int    = torch.full((len(xy_int_np), 1), wind_u, dtype=torch.float32, device=device)
                wv_int    = torch.full((len(xy_int_np), 1), wind_v, dtype=torch.float32, device=device)
                prec_int  = torch.full((len(xy_int_np), 1), precip_mmh, dtype=torch.float32, device=device) \
                            if precip_mmh > 0 else None

                R = pde_residual_v3(
                    model, xyt_int, wu_int, wv_int,
                    precip=prec_int, blh=blh_int, elev=elev_int,
                    lx_m=LX_M, ly_m=LY_M, blh_m=blh_m_int,
                )
                L_pde_day = L_pde_day + (R ** 2).mean()

            # Data loss at pseudo-label pixel locations
            if w["data"] > 0:
                t_pix_np = np.full((N_PIXELS_PER_EPOCH, 1), t_norm, dtype=np.float32)
                xyt_pix  = torch.tensor(
                    np.stack([x_pix_np, y_pix_np, t_pix_np.ravel()], axis=1),
                    dtype=torch.float32, device=device,
                )
                blh_pix  = torch.full((N_PIXELS_PER_EPOCH, 1), blh_h_n, dtype=torch.float32, device=device)
                elev_pix = torch.tensor(elev_pix_np[:, None], dtype=torch.float32, device=device)
                C_h, _   = model(xyt_pix, blh=blh_pix, elev=elev_pix)
                C_hourly.append(C_h)

            # K accumulation (for kblh diagnostic — no grad needed)
            with torch.no_grad():
                t_diag_np = np.full((64, 1), t_norm, dtype=np.float32)
                xy_diag   = rng.uniform(-1.0, 1.0, (64, 2)).astype(np.float32)
                xyt_diag  = torch.tensor(
                    np.hstack([xy_diag, t_diag_np]),
                    dtype=torch.float32, device=device,
                )
                elev_diag_np = elev_interp(xy_diag[:, 0], xy_diag[:, 1])
                elev_diag  = torch.tensor(elev_diag_np[:, None], dtype=torch.float32, device=device)
                blh_diag   = torch.full((64, 1), blh_h_n, dtype=torch.float32, device=device)
                _, (Kx_h, Ky_h, _) = model(xyt_diag, blh=blh_diag, elev=elev_diag)
                k_means.append(float((Kx_h.mean() + Ky_h.mean()) / 2.0))

        # ── Loss assembly ──────────────────────────────────────────────────
        L_pde = (L_pde_day / len(SNAPSHOT_HOURS)) if w["pde"] > 0 else torch.zeros(1, device=device)

        # Data loss: daily-mean C_pred vs pseudo-labels
        L_data = torch.zeros(1, device=device)
        if w["data"] > 0 and len(C_hourly) > 0:
            C_daily    = torch.stack(C_hourly, dim=0).mean(dim=0).squeeze()   # (N_PIX,)
            C_pseudo_t = torch.tensor(C_pseudo, dtype=torch.float32, device=device)
            L_data     = ((C_daily - C_pseudo_t) ** 2).mean() / pm25_var_t

        # BC loss: domain-mean vs Air4Thai city-mean
        L_bc = torch.zeros(1, device=device)
        if w["bc"] > 0 and len(C_hourly) > 0 and not np.isnan(city_mean_today):
            C_domain_mean = torch.stack(C_hourly, dim=0).mean()
            L_bc = ((C_domain_mean - city_mean_today) ** 2) / pm25_var_t

        # K–BLH correlation regulariser (sample 8 dates with different BLH values)
        L_kblh = torch.zeros(1, device=device)
        if w["kblh"] > 0 and len(a4t_dates) >= 4:
            N_KBLH = 8
            kblh_dates = a4t_dates[rng.integers(0, len(a4t_dates), size=N_KBLH)]
            k_kblh_list   = []
            blh_kblh_list = []
            xy_kb   = rng.uniform(-1.0, 1.0, (64, 2)).astype(np.float32)
            t_kb    = np.full((64, 1), 0.5, dtype=np.float32)
            elev_kb = elev_interp(xy_kb[:, 0], xy_kb[:, 1])
            elev_kb_t = torch.tensor(elev_kb[:, None], dtype=torch.float32, device=device)

            for kd in kblh_dates:
                kd_df    = daily_sta[daily_sta["date"] == kd]
                blh_kd   = float(kd_df["blh"].mean()) if len(kd_df) > 0 and "blh" in kd_df.columns else 1000.0
                blh_kn   = blh_kd / PINN_BLH_NORM_SCALE
                xyt_kb   = torch.tensor(np.hstack([xy_kb, t_kb]), dtype=torch.float32, device=device)
                blh_kb_t = torch.full((64, 1), blh_kn, dtype=torch.float32, device=device)
                _, (Kx_k, Ky_k, _) = model(xyt_kb, blh=blh_kb_t, elev=elev_kb_t)
                k_kblh_list.append((Kx_k.mean() + Ky_k.mean()) / 2.0)
                blh_kblh_list.append(blh_kn)

            blh_kblh_t = torch.tensor(blh_kblh_list, dtype=torch.float32, device=device)
            k_kblh_t   = torch.stack(k_kblh_list)
            if blh_kblh_t.std() > 1e-6:
                r_kblh_train = _pearson_corr(blh_kblh_t, k_kblh_t)
                L_kblh = w["kblh"] * (1.0 - r_kblh_train) ** 2

        L_total = w["pde"] * L_pde + w["data"] * L_data + w["bc"] * L_bc + L_kblh

        L_total.backward()
        import torch.nn as nn
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=10.0)
        optimizer.step()
        scheduler.step()

        # ── Logging ────────────────────────────────────────────────────────
        record = {
            "epoch":   epoch,
            "L_total": float(L_total),
            "L_pde":   float(L_pde),
            "L_data":  float(L_data),
            "L_bc":    float(L_bc),
            "L_kblh":  float(L_kblh),
            "lr":      scheduler.get_last_lr()[0],
        }
        loss_history.append(record)

        if epoch % 50 == 0:
            elapsed = (time.time() - t_start) / 60.0
            log.info(
                f"Ep {epoch:5d}/{n_epochs} | "
                f"L={float(L_total):.4f} pde={float(L_pde):.4f} "
                f"data={float(L_data):.4f} bc={float(L_bc):.4f} | "
                f"{elapsed:.1f} min"
            )

        # ── Spatial validation ─────────────────────────────────────────────
        if epoch % SPATIAL_EVAL_EVERY == 0 and epoch > 0:
            val   = spatial_validation(model, daily_sta, elev_interp, device)
            gates = check_gates(val)
            log.info(
                f"  [spatial] R²={val['spatial_R2']:.3f} "
                f"std_C={val['std_C_sta']:.2f} µg/m³  "
                f"r_kblh={val['r_kblh']:.3f}  "
                f"bias={val.get('mean_bias', float('nan')):+.2f} µg/m³  "
                f"{'✓G1' if gates['G1_spatial_R2_pass'] else '✗G1'} "
                f"{'✓G2' if gates['G2_r_kblh_pass'] else '✗G2'} "
                f"{'✓G3' if gates['G3_bias_pass'] else '✗G3'}"
            )
            record.update(val)

            if wandb_run is not None:
                wandb_run.log({**record, "epoch": epoch})

        # ── Checkpointing ──────────────────────────────────────────────────
        if epoch % save_every == 0 and epoch > 0:
            import torch as _torch
            ckpt_path = CHECKPOINT_DIR / "checkpoints" / f"epoch_{epoch:05d}.pt"
            ckpt_path.parent.mkdir(parents=True, exist_ok=True)
            _torch.save({
                "epoch":               epoch,
                "model_state_dict":    model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "loss_history":        loss_history,
            }, str(ckpt_path))
            log.info(f"  Checkpoint saved: {ckpt_path.name}")

    return loss_history


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def _setup_wandb(config: dict):
    api_key = os.environ.get("WANDB_API_KEY")
    try:
        import wandb
        if api_key:
            wandb.login(key=api_key, relogin=True)
        run = wandb.init(
            project=WANDB_PROJECT,
            name=f"chiangmai-pinn-{'warm' if not config.get('cold_start') else 'cold'}",
            config=config,
            tags=["stage2", "chiangmai", "v3", "experiment-b"],
        )
        log.info(f"W&B run: {run.url}")
        return run
    except Exception as exc:
        log.warning(f"W&B init failed ({exc}) — continuing without tracking")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Train FourierPINNV3 on Chiang Mai pseudo-labels (Experiment B)"
    )
    parser.add_argument("--epochs",      type=int,   default=DEFAULT_EPOCHS)
    parser.add_argument("--lr",          type=float, default=DEFAULT_LR)
    parser.add_argument("--cold-start",  action="store_true",
                        help="Random Xavier init instead of Medellín v7 warm-start")
    parser.add_argument("--warm-start",  type=str,   default=None, metavar="CKPT_PATH",
                        help="Custom warm-start checkpoint path (overrides default v7)")
    parser.add_argument("--save-every",  type=int,   default=SAVE_EVERY)
    parser.add_argument("--wandb",       action="store_true")
    args = parser.parse_args()

    import torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info(f"Device: {device}")
    log.info(f"Domain: LX={LX_M:.0f}m, LY={LY_M:.0f}m")

    (daily_sta, city_mean, pm25_var,
     pixel_preds, pixel_dates, pixel_xnorm, pixel_ynorm, pixel_elev) = load_chiangmai_data()

    elev_interp = build_elev_interpolator()
    model = build_model(
        device, warm_start_path=args.warm_start, cold_start=args.cold_start
    )

    run_config = dict(
        epochs=args.epochs, lr=args.lr,
        cold_start=args.cold_start,
        warm_start=args.warm_start or str(MEDELLIN_V7_CKPT),
        n_pixels_per_epoch=N_PIXELS_PER_EPOCH,
    )
    wandb_run = _setup_wandb(run_config) if args.wandb else None

    t0 = time.time()
    loss_history = train(
        model, daily_sta, city_mean, pm25_var, elev_interp,
        pixel_preds, pixel_dates, pixel_xnorm, pixel_ynorm, pixel_elev,
        n_epochs=args.epochs, lr=args.lr, device=device,
        wandb_run=wandb_run, save_every=args.save_every,
    )
    elapsed = (time.time() - t0) / 60.0
    log.info(f"Training complete in {elapsed:.1f} min")

    # Final spatial validation
    val   = spatial_validation(model, daily_sta, elev_interp, device)
    gates = check_gates(val)
    log.info("─── Final Gate Check (Experiment B) ───")
    log.info(f"  G1 spatial_R² > 0.30: {val['spatial_R2']:.3f} → {'PASS ✓' if gates['G1_spatial_R2_pass'] else 'FAIL ✗'}")
    log.info(f"  G2 K–BLH r   > 0.50: {val['r_kblh']:.3f}    → {'PASS ✓' if gates['G2_r_kblh_pass'] else 'FAIL ✗'}")
    log.info(f"  G3 |bias|    < 5 µg: {val.get('mean_bias', float('nan')):+.2f} µg/m³ → {'PASS ✓' if gates['G3_bias_pass'] else 'FAIL ✗'}")
    log.info(f"  n_stations: {val['n_stations']}")

    # Save final model
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    final_path = CHECKPOINT_DIR / "chiangmai_pinn_final.pt"
    torch.save({
        "epoch":              args.epochs,
        "model_state_dict":   model.state_dict(),
        "loss_history":       loss_history,
        "spatial_R2":         val["spatial_R2"],
        "r_kblh":             val["r_kblh"],
        "mean_bias":          val.get("mean_bias"),
        "gates":              gates,
        "config":             run_config,
    }, str(final_path))
    log.info(f"Saved: {final_path}")

    # Save loss CSV
    import csv
    csv_path = CHECKPOINT_DIR / "chiangmai_pinn_losses.csv"
    if loss_history:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(loss_history[0].keys()))
            writer.writeheader()
            writer.writerows(loss_history)
    log.info(f"Loss CSV: {csv_path}")

    if wandb_run is not None:
        wandb_run.summary.update({
            "final_spatial_R2": val["spatial_R2"],
            "final_r_kblh":     val["r_kblh"],
            "final_mean_bias":  val.get("mean_bias"),
            "G1_pass":          gates["G1_spatial_R2_pass"],
            "G2_pass":          gates["G2_r_kblh_pass"],
            "G3_pass":          gates["G3_bias_pass"],
        })
        wandb_run.finish()


if __name__ == "__main__":
    main()
