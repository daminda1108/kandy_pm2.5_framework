"""
train_medellin_pinn.py — FourierPINNV3 training on Medellín with SIATA ground truth.

PURPOSE
-------
This is Stage 2's validation pipeline. Medellín has 11 SIATA ground-truth PM2.5
stations, enabling real spatial R² measurement — the only opportunity in this thesis
to verify the PINN is physically correct before applying it to station-free Kandy.

Gate conditions (must pass before proceeding to Stage 3 Kandy):
  (1) Spatial R² > 0.5 on Medellín 11-station data
  (2) K–BLH Pearson r > 0.5
  (3) Zero-shot Chiang Mai RMSE < 15 µg/m³

ARCHITECTURE
------------
FourierPINNV3 (76,261 params) — same architecture as Stage 3 Kandy train.py.
  - Road kernel: medellin_road_kernel_100m.npz  → S = alpha(t) × R(x,y)
  - Elev grid:   medellin_elev_grid_100m.npz    → K_aniso(x,y,elev)
  - BLH:         ERA5 BLH / 2000.0              → K_base(BLH,t)

DATA APPROACH (key design decision)
------------------------------------
BC uses SIATA city-mean directly (not Stage 1 CAMS-BC predictions).
  Reason: for the training period (Aug 2018–Sep 2019) we have ground truth.
  r(CAMS, SIATA) = 0.411 — SIATA city-mean is strictly better as BC.
  Stage 1 XGBoost (R²=0.217) is needed only for post-SIATA generalization.

Data loss: 11 SIATA stations × ~423 days = ~4,653 daily observations.
  C_pred_daily = mean over 8 hourly snapshots of C(x_sta, y_sta, h/24).
  L_data = MSE(C_pred_daily, C_obs_daily) / pm25_var  (normalised).

CURRICULUM (learning from v8 experience)
------------------------------------------
Phase 1 (0–25%):  λ_pde=0.00, λ_data=0.75, λ_bc=0.20, λ_kblh=0.05
  Pure data dominance — establish correct station-to-station ordering before
  physics constraints. v8 showed this is CRITICAL: PDE at Phase 1 pushes C flat.

Phase 2 (25–60%):  linear ramp λ_pde 0→0.38, λ_data 0.75→0.30

Phase 3 (60–100%): λ_pde=0.38, λ_data=0.35, λ_bc=0.15, λ_kblh=0.10
  L_div intentionally absent: road kernel (B4) breaks K–S degeneracy.
  Expert recommendation (Antigravity 2026-03-14): λ_data≥0.35 to prevent
  PDE from undoing station fit as weights shift in Phase 3 (v8 lesson).
  If spatial_R² < 0.3 at ep 25%: consider L_div = (std_C_sta - σ_obs)²/σ_obs²
  (data-anchored form, not floor penalty — ties constraint to observations).

SPATIAL VALIDATION (key metric)
---------------------------------
Every 50 epochs, evaluate C at 11 stations for all training dates.
Reports: spatial_R² (C_pred_mean vs C_obs_mean across 11 stations),
         std_C_sta (inter-station std of mean predicted C),
         K–BLH r (correlation of domain-mean K with BLH across dates).

USAGE
-----
    # With v8 backbone warm-start (recommended)
    python src/stage2_transfer/pretrain/train_medellin_pinn.py --epochs 2000

    # Cold start (comparison experiment)
    python src/stage2_transfer/pretrain/train_medellin_pinn.py --epochs 2000 --cold-start

    # W&B tracking
    python src/stage2_transfer/pretrain/train_medellin_pinn.py --epochs 2000 --wandb

    # Check gate conditions only
    python src/stage2_transfer/pretrain/train_medellin_pinn.py --check-gates
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    LOG_FORMAT, LOG_DATEFMT,
    MODELS_DIR, PINN_INPUT_DIR,
    MEDELLIN_PINN_BBOX, PINN_BLH_NORM_SCALE,
    N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("train_medellin_pinn")

# ── Paths ─────────────────────────────────────────────────────────────────────
STAGE2_PROC_DIR   = Path(__file__).parents[3] / "data" / "processed" / "stage2"
PERSTATION_PARQ   = STAGE2_PROC_DIR / "medellin_stage2_perstation.parquet"
ROAD_KERNEL_NPZ   = PINN_INPUT_DIR  / "medellin_road_kernel_100m.npz"
ELEV_GRID_NPZ     = PINN_INPUT_DIR  / "medellin_elev_grid_100m.npz"
CHECKPOINT_DIR    = MODELS_DIR / "stage2_medellin_pinn"
ERA5_SIATA_NC     = Path(__file__).parents[3] / "data" / "external" / "medellin" / "era5" / "medellin_era5_siata_period.nc"

# Domain dimensions for PDE coordinate scaling (Fix D) — from MEDELLIN_PINN_BBOX
# L_y = Δlat × 111320 m/° = 0.1351° × 111320 ≈ 15040 m
# L_x = Δlon × cos(lat_ctr°) × 111320 m/° = 0.1360° × cos(6.23°) × 111320 ≈ 15050 m
LX_M = 15050.0   # domain width  [m]
LY_M = 15040.0   # domain height [m]

WANDB_PROJECT = "kandy-pinn"

# ── Training defaults ─────────────────────────────────────────────────────────
DEFAULT_EPOCHS    = 2000
DEFAULT_LR        = 3e-4
SAVE_EVERY        = 100
SNAPSHOT_HOURS    = [0, 3, 6, 9, 12, 15, 18, 21]
SPATIAL_EVAL_EVERY = 50


# ─────────────────────────────────────────────────────────────────────────────
# CURRICULUM
# ─────────────────────────────────────────────────────────────────────────────

def get_weights(epoch: int, n_epochs: int) -> dict:
    """
    Three-phase curriculum — canonical v7 values (both gates passed).

    Phase 1 (0–30%):  λ_pde=0.00, λ_data=0.75, λ_bc=0.20, λ_kblh=0.05
      Pure data dominance — establish correct station-to-station ordering.
      CRITICAL: PDE at Phase 1 pushes C to a flat trivial solution (v4/v5 lesson).
      Extended from 25%→30% for the v8 run: extra time for spatial ordering.

    Phase 2 (30–60%):  linear ramp λ_pde 0→0.15, λ_data 0.75→0.55
      Gentle PDE onset. λ_data=0.55 at end keeps data dominant (≥0.50).

    Phase 3 (60–100%): λ_pde=0.15, λ_data=0.55, λ_bc=0.15, λ_kblh=0.10
      Data dominance maintained: λ_data=0.55 > λ_pde=0.15.
      Road kernel (B4) breaks K–S degeneracy — L_div not needed.
      Key v5/v6 lesson: λ_pde > λ_data in Phase 3 → station fit degrades.
    """
    p1_end = int(0.30 * n_epochs)
    p2_end = int(0.60 * n_epochs)

    if epoch < p1_end:
        return dict(pde=0.00, data=0.75, bc=0.20, kblh=0.05)
    elif epoch < p2_end:
        t = (epoch - p1_end) / max(1, p2_end - p1_end)
        pde  = t * 0.15
        data = 0.75 + t * (0.55 - 0.75)
        bc   = 0.20 + t * (0.15 - 0.20)
        kblh = 0.05 + t * (0.10 - 0.05)
        return dict(pde=pde, data=data, bc=bc, kblh=kblh)
    else:
        return dict(pde=0.15, data=0.55, bc=0.15, kblh=0.10)


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_siata_daily() -> tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    Load SIATA per-station hourly data and aggregate to daily per station.

    Returns
    -------
    daily_sta : DataFrame, MultiIndex (date, station_id).
        Columns: pm25, x_norm, y_norm, lat, lon, blh, u10, v10, tp
    city_mean : Series (date → city-mean PM2.5). Used as BC target.
    pm25_var  : float — PM2.5 variance for loss normalisation.
    """
    if not PERSTATION_PARQ.exists():
        raise FileNotFoundError(f"Per-station parquet not found: {PERSTATION_PARQ}")

    df = pd.read_parquet(PERSTATION_PARQ)

    # Parse datetime and set as index
    df["date"] = pd.to_datetime(df["datetime_utc"]).dt.tz_localize(None).dt.normalize()

    # Aggregate hourly → daily per station
    agg_cols = {
        "pm25":  "mean",
        "x_norm": "first",
        "y_norm": "first",
        "lat":    "first",
        "lon":    "first",
        "blh":    "mean",
        "u10":    "mean",
        "v10":    "mean",
        "tp":     "sum",
    }
    # Keep only columns that exist
    agg_cols = {k: v for k, v in agg_cols.items() if k in df.columns}

    daily_sta = (
        df.groupby(["date", "station_id"])
        .agg(agg_cols)
        .reset_index()
    )

    # Drop rows with missing PM2.5
    n_before = len(daily_sta)
    daily_sta = daily_sta.dropna(subset=["pm25"])
    log.info(f"SIATA daily: {len(daily_sta)} station-days ({n_before - len(daily_sta)} dropped for NaN PM2.5)")
    log.info(f"  Stations: {daily_sta['station_id'].nunique()}, Dates: {daily_sta['date'].nunique()}")
    log.info(f"  Date range: {daily_sta['date'].min().date()} – {daily_sta['date'].max().date()}")
    log.info(f"  PM2.5: mean={daily_sta['pm25'].mean():.1f}, std={daily_sta['pm25'].std():.1f}, "
             f"range=[{daily_sta['pm25'].min():.1f}, {daily_sta['pm25'].max():.1f}] µg/m³")

    # City-mean per day (all-station average — BC target)
    city_mean = daily_sta.groupby("date")["pm25"].mean()

    pm25_var = float(daily_sta["pm25"].std() ** 2)
    log.info(f"  PM2.5 variance (normalisation): {pm25_var:.2f} µg²/m⁶")

    return daily_sta, city_mean, pm25_var


def load_era5_blh_hourly() -> dict:
    """
    Load ERA5 hourly BLH for the SIATA training period (Aug 2018–Sep 2019).

    Fix I/A: provides per-snapshot BLH so each of the 8 quasi-steady-state
    hourly snapshots receives the correct ERA5 boundary layer height instead
    of sharing one daily-mean value.

    Returns
    -------
    blh_hourly : dict { pd.Timestamp (midnight) → { hour_int → blh_m (float) } }
        Falls back to empty dict if ERA5 file not found — training then uses
        the daily-mean BLH from the per-station parquet (same as before this fix).
    """
    if not ERA5_SIATA_NC.exists():
        log.warning(
            f"ERA5 nc not found: {ERA5_SIATA_NC} — "
            "per-snapshot BLH disabled; falling back to daily-mean BLH."
        )
        return {}

    try:
        import xarray as xr
    except ImportError:
        log.warning("xarray not installed — per-snapshot BLH disabled.")
        return {}

    ds = xr.open_dataset(str(ERA5_SIATA_NC))
    blh_da = ds["blh"]   # (valid_time, latitude, longitude)

    # Spatial mean over the 2×2 ERA5 coarse grid
    spatial_dims = [d for d in blh_da.dims if d != "valid_time"]
    blh_ts = blh_da.mean(dim=spatial_dims).values.ravel()   # (10224,)
    times   = pd.to_datetime(ds["valid_time"].values).tz_localize(None)
    ds.close()

    result: dict = {}
    for t, b in zip(times, blh_ts):
        date_key = t.normalize()     # midnight timestamp
        result.setdefault(date_key, {})[t.hour] = float(b)

    n_dates = len(result)
    all_blh = list(blh_ts)
    log.info(
        f"ERA5 hourly BLH loaded: {n_dates} dates, "
        f"BLH range=[{min(all_blh):.0f}, {max(all_blh):.0f}] m "
        f"(mean={sum(all_blh)/len(all_blh):.0f} m)"
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# TERRAIN HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def build_elev_interpolator():
    """
    Build a 2D bilinear interpolator for elev_norm over the PINN domain.

    The 150×150 elev_norm grid is defined on normalised [0,1]² coords.
    Returns a callable: interp(x_norm_arr, y_norm_arr) → elev_norm_arr.
    """
    from scipy.interpolate import RegularGridInterpolator

    if not ELEV_GRID_NPZ.exists():
        raise FileNotFoundError(
            f"Elev grid not found: {ELEV_GRID_NPZ}\n"
            "Run: python src/stage2_transfer/medellin_terrain.py"
        )
    data      = np.load(str(ELEV_GRID_NPZ))
    elev_norm = data["elev_norm"]          # (150, 150)
    lat_grid  = data["lat_grid"]           # (150, 150)
    lon_grid  = data["lon_grid"]           # (150, 150)

    # Normalised coords on [0, 1] matching how model receives x_norm, y_norm
    bbox    = MEDELLIN_PINN_BBOX
    lat_1d  = lat_grid[:, 0]
    lon_1d  = lon_grid[0, :]
    y_vals  = (lat_1d - bbox["lat_min"]) / (bbox["lat_max"] - bbox["lat_min"])
    x_vals  = (lon_1d - bbox["lon_min"]) / (bbox["lon_max"] - bbox["lon_min"])

    # RegularGridInterpolator expects (row_axis, col_axis) = (y_vals, x_vals)
    interp = RegularGridInterpolator(
        (y_vals, x_vals), elev_norm,
        method="linear", bounds_error=False, fill_value=0.5,
    )

    def query(x_norm_arr: np.ndarray, y_norm_arr: np.ndarray) -> np.ndarray:
        """Query elev_norm at arbitrary (x_norm, y_norm) arrays."""
        pts = np.stack([y_norm_arr.ravel(), x_norm_arr.ravel()], axis=1)
        return interp(pts).reshape(x_norm_arr.shape).astype(np.float32)

    log.info(
        f"Elev interpolator built: range=[{elev_norm.min():.3f}, {elev_norm.max():.3f}] "
        f"(elev {data['elev_min']:.0f}–{data['elev_max']:.0f} m)"
    )
    return query


# ─────────────────────────────────────────────────────────────────────────────
# MODEL
# ─────────────────────────────────────────────────────────────────────────────

def build_model(device, warm_start_path=None):
    """
    Build FourierPINNV3 for Medellín training.

    FourierPINNV3 is a fully redesigned architecture (76K params, separate spatial+temporal
    embeddings, factored K). The old FourierPINN v2 backbone (stage2_pretrain/v8/) has a
    different architecture and 0 keys transfer — v2 is obsolete.

    warm_start_path: optional path to a FourierPINNV3 checkpoint (e.g. previous Medellín run)
                     from which to load model_state_dict. Only use same-architecture checkpoints.
    """
    import torch
    from src.stage3_pinn.models.fourier_pinn_v3 import FourierPINNV3

    if not ROAD_KERNEL_NPZ.exists():
        raise FileNotFoundError(
            f"Road kernel not found: {ROAD_KERNEL_NPZ}\n"
            "Run: python src/stage2_transfer/medellin_terrain.py"
        )

    model = FourierPINNV3(road_kernel_path=ROAD_KERNEL_NPZ).to(device)
    log.info(f"FourierPINNV3: {sum(p.numel() for p in model.parameters()):,} params")

    if warm_start_path is not None and Path(warm_start_path).exists():
        ckpt = torch.load(str(warm_start_path), map_location=device, weights_only=False)
        state = ckpt.get("model_state_dict", ckpt)
        model.load_state_dict(state)
        log.info(f"Warm-started from FourierPINNV3 checkpoint: {warm_start_path}")
    else:
        log.info("Cold start: full random Xavier initialisation (FourierPINNV3)")

    return model


# ─────────────────────────────────────────────────────────────────────────────
# SPATIAL VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def spatial_validation(model, daily_sta: pd.DataFrame, elev_interp, device) -> dict:
    """
    Compute spatial validation metrics across 11 SIATA stations.

    Evaluates C(x_sta, y_sta, t=0.5) for each station on a random sample
    of 50 training dates (or all if fewer). Returns:
      spatial_R²       : R² between C_pred_mean and C_obs_mean per station
      std_C_sta        : inter-station std of time-averaged predicted C
      r_kblh           : correlation of domain-mean K with BLH across dates
      per_station_bias : dict station_id → mean residual (pred - obs)
      per_station_rmse : dict station_id → RMSE
    """
    import torch
    from sklearn.metrics import r2_score

    model.eval()
    dates = sorted(daily_sta["date"].unique())
    sample_dates = np.random.default_rng(0).choice(dates, size=min(50, len(dates)), replace=False)

    sta_pred_means = {}   # station_id → list of daily mean C_pred
    sta_obs_means  = {}
    sta_residuals  = {}   # station_id → list of (pred - obs)
    k_vals = []
    blh_vals = []

    with torch.no_grad():
        for date in sample_dates:
            day_df = daily_sta[daily_sta["date"] == date]
            if len(day_df) < 3:
                continue

            x_np  = day_df["x_norm"].values.astype(np.float32)
            y_np  = day_df["y_norm"].values.astype(np.float32)
            elev_np = elev_interp(x_np, y_np)
            blh_day = float(day_df["blh"].mean()) if "blh" in day_df.columns else 1000.0
            blh_n   = blh_day / PINN_BLH_NORM_SCALE

            t_noon = 0.5
            xyt    = torch.tensor(
                np.stack([x_np, y_np, np.full_like(x_np, t_noon)], axis=1),
                dtype=torch.float32, device=device,
            )
            blh_t  = torch.full((len(x_np), 1), blh_n, dtype=torch.float32, device=device)
            elev_t = torch.tensor(elev_np[:, None], dtype=torch.float32, device=device)

            C, (Kx, Ky, _) = model(xyt, blh=blh_t, elev=elev_t)
            C_np = C.squeeze().cpu().numpy()
            if C_np.ndim == 0:
                C_np = C_np[np.newaxis]

            for i, (sid, obs) in enumerate(zip(day_df["station_id"].values, day_df["pm25"].values)):
                sta_pred_means.setdefault(sid, []).append(float(C_np[i]))
                sta_obs_means.setdefault(sid, []).append(float(obs))
                sta_residuals.setdefault(sid, []).append(float(C_np[i]) - float(obs))

            # K–BLH accumulation (across dates → std > 0, unlike same-day snapshots)
            k_vals.append(float((Kx.mean() + Ky.mean()) / 2.0))
            blh_vals.append(blh_n)

    model.train()

    # Station-mean aggregation
    station_ids = sorted(sta_pred_means.keys())
    pred_means  = np.array([np.mean(sta_pred_means[s]) for s in station_ids])
    obs_means   = np.array([np.mean(sta_obs_means[s])  for s in station_ids])

    spatial_r2 = float(r2_score(obs_means, pred_means)) if len(pred_means) >= 3 else float("nan")
    std_C_sta  = float(np.std(pred_means))

    # K–BLH correlation (across dates — each date has a different BLH value)
    if len(k_vals) >= 5 and np.std(blh_vals) > 1e-3:
        r_kblh = float(np.corrcoef(blh_vals, k_vals)[0, 1])
    else:
        r_kblh = float("nan")

    # Per-station residuals (expert recommendation: identify outlier stations)
    per_station_bias = {s: float(np.mean(sta_residuals[s])) for s in station_ids}
    per_station_rmse = {s: float(np.sqrt(np.mean(np.array(sta_residuals[s])**2))) for s in station_ids}

    # Log per-station table
    log.info("  Per-station residuals:")
    log.info(f"  {'Station':>10}  {'obs_mean':>8}  {'pred_mean':>9}  {'bias':>7}  {'RMSE':>7}")
    for s in station_ids:
        log.info(
            f"  {s:>10}  {np.mean(sta_obs_means[s]):8.1f}  "
            f"{np.mean(sta_pred_means[s]):9.1f}  "
            f"{per_station_bias[s]:+7.1f}  {per_station_rmse[s]:7.2f}"
        )

    return {
        "spatial_R2":        spatial_r2,
        "std_C_sta":         std_C_sta,
        "r_kblh":            r_kblh,
        "n_stations":        len(pred_means),
        "obs_means":         obs_means.tolist(),
        "pred_means":        pred_means.tolist(),
        "per_station_bias":  per_station_bias,
        "per_station_rmse":  per_station_rmse,
    }


def check_gates(val: dict) -> dict:
    """Check Stage 2 gate conditions."""
    return {
        "spatial_R2_pass":  val["spatial_R2"] > 0.50,
        "r_kblh_pass":      val["r_kblh"]     > 0.50,
        "spatial_R2":       val["spatial_R2"],
        "r_kblh":           val["r_kblh"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# PEARSON CORRELATION (differentiable)
# ─────────────────────────────────────────────────────────────────────────────

def _pearson_corr(a, b):
    a_c = a - a.mean()
    b_c = b - b.mean()
    return (a_c * b_c).sum() / (a_c.norm() * b_c.norm() + 1e-8)


# ─────────────────────────────────────────────────────────────────────────────
# COLLOCATION SAMPLING
# ─────────────────────────────────────────────────────────────────────────────

def sample_collocation(n_interior: int, n_boundary: int, rng) -> tuple[np.ndarray, np.ndarray]:
    """
    Sample (x_norm, y_norm) in [0,1]² for interior and boundary.
    Boundary: points on the four edges of the unit square.
    """
    xy_int = rng.uniform(0.0, 1.0, (n_interior, 2)).astype(np.float32)

    # Four edges equally
    n_each  = n_boundary // 4
    edge0   = np.stack([rng.uniform(0,1,n_each), np.zeros(n_each)], 1)           # bottom
    edge1   = np.stack([rng.uniform(0,1,n_each), np.ones(n_each)],  1)           # top
    edge2   = np.stack([np.zeros(n_each),         rng.uniform(0,1,n_each)], 1)   # left
    edge3   = np.stack([np.ones(n_each),          rng.uniform(0,1,n_each)], 1)   # right
    xy_bnd  = np.concatenate([edge0, edge1, edge2, edge3], axis=0).astype(np.float32)

    return xy_int, xy_bnd


# ─────────────────────────────────────────────────────────────────────────────
# TRAINING LOOP
# ─────────────────────────────────────────────────────────────────────────────

def train(
    model,
    daily_sta:   pd.DataFrame,
    city_mean:   pd.Series,
    pm25_var:    float,
    elev_interp,
    n_epochs:    int,
    lr:          float,
    device,
    wandb_run=None,
    save_every:  int = SAVE_EVERY,
) -> list[dict]:
    """Main Medellín PINN training loop."""
    import torch
    import torch.optim as optim
    from src.stage3_pinn.physics.pde_residual_v3 import pde_residual_v3

    # Load per-snapshot BLH from hourly ERA5 (Fix I/A)
    blh_hourly = load_era5_blh_hourly()
    log.info(
        f"Per-snapshot BLH: {'ENABLED (hourly ERA5)' if blh_hourly else 'DISABLED (daily-mean fallback)'}"
    )

    optimizer = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()), lr=lr
    )
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_epochs, eta_min=1e-6)

    rng   = np.random.default_rng(42)
    dates = np.array(sorted(daily_sta["date"].unique()))
    n_dates = len(dates)

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    loss_history = []
    pm25_var_t   = max(pm25_var, 1.0)   # avoid division by zero

    # Pre-build collocation layout (refresh every 200 epochs with new random sample)
    xy_int_np, xy_bnd_np = sample_collocation(N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY, rng)

    sta_ids     = sorted(daily_sta["station_id"].unique())
    elev_int_np = elev_interp(xy_int_np[:, 0], xy_int_np[:, 1])

    log.info(f"Training: {n_epochs} epochs, {n_dates} SIATA dates, "
             f"{len(sta_ids)} stations, device={device}")
    log.info(f"Collocation: {len(xy_int_np)} interior + {len(xy_bnd_np)} boundary")

    t_start = time.time()

    for epoch in range(n_epochs):
        model.train()
        w = get_weights(epoch, n_epochs)

        # Refresh collocation every 200 epochs to avoid overfitting one layout
        if epoch > 0 and epoch % 200 == 0:
            xy_int_np, xy_bnd_np = sample_collocation(
                N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY, rng
            )
            elev_int_np = elev_interp(xy_int_np[:, 0], xy_int_np[:, 1])

        # ── Sample a random date ───────────────────────────────────────────
        date_today = dates[rng.integers(0, n_dates)]
        day_df     = daily_sta[daily_sta["date"] == date_today]

        blh_today  = float(day_df["blh"].mean()) if "blh" in day_df.columns else 1000.0
        wind_u     = float(day_df["u10"].mean()) if "u10" in day_df.columns else 0.5
        wind_v     = float(day_df["v10"].mean()) if "v10" in day_df.columns else 0.5
        precip_raw = float(day_df["tp"].sum()) if "tp" in day_df.columns else 0.0
        precip_mmh = max(0.0, precip_raw * 1000.0 / 24.0)

        # Get SIATA observations for this date (subset of stations with valid PM2.5)
        sta_today  = day_df.dropna(subset=["pm25"])
        C_obs      = sta_today["pm25"].values.astype(np.float32)
        x_sta_np   = sta_today["x_norm"].values.astype(np.float32)
        y_sta_np   = sta_today["y_norm"].values.astype(np.float32)
        e_sta_np   = elev_interp(x_sta_np, y_sta_np)

        city_mean_today = float(city_mean.get(date_today, C_obs.mean())) if len(C_obs) > 0 else 0.0

        has_data = len(sta_today) >= 2

        optimizer.zero_grad()

        # ── 8-snapshot quasi-steady-state loop ────────────────────────────
        L_pde_day  = torch.zeros(1, device=device)
        C_hourly   = []    # C at station locations per snapshot → daily mean
        k_means    = []
        blh_values = []

        for h in SNAPSHOT_HOURS:
            t_norm = h / 24.0

            # Per-snapshot BLH (Fix I/A): use hourly ERA5 BLH if available;
            # fall back to daily-mean blh_today when hourly data is absent.
            blh_h_m = float(blh_hourly.get(date_today, {}).get(h, blh_today))
            blh_h_n = blh_h_m / PINN_BLH_NORM_SCALE

            # Interior collocation tensors
            t_int_np  = np.full((len(xy_int_np), 1), t_norm, dtype=np.float32)
            xyt_int   = torch.tensor(
                np.hstack([xy_int_np, t_int_np]),
                dtype=torch.float32, device=device,
            ).requires_grad_(True)
            blh_int   = torch.full((len(xy_int_np), 1), blh_h_n, dtype=torch.float32, device=device)
            blh_m_int = torch.full((len(xy_int_np), 1), blh_h_m, dtype=torch.float32, device=device)
            elev_int  = torch.tensor(elev_int_np[:, None], dtype=torch.float32, device=device)
            wu_int    = torch.full((len(xy_int_np), 1), wind_u, dtype=torch.float32, device=device)
            wv_int    = torch.full((len(xy_int_np), 1), wind_v, dtype=torch.float32, device=device)
            prec_int  = torch.full((len(xy_int_np), 1), precip_mmh, dtype=torch.float32, device=device) \
                        if precip_mmh > 0 else None

            # PDE residual — with coordinate scaling (Fix D) + BLH-dependent λ_dry (Fix F)
            if w["pde"] > 0:
                R = pde_residual_v3(
                    model, xyt_int, wu_int, wv_int,
                    precip=prec_int, blh=blh_int, elev=elev_int,
                    lx_m=LX_M, ly_m=LY_M, blh_m=blh_m_int,
                )
                L_pde_day = L_pde_day + (R ** 2).mean()

            # Station data (evaluate C at station locations for this snapshot)
            if w["data"] > 0 and has_data:
                t_sta_np  = np.full((len(x_sta_np), 1), t_norm, dtype=np.float32)
                xyt_sta   = torch.tensor(
                    np.stack([x_sta_np, y_sta_np, t_sta_np.ravel()], axis=1),
                    dtype=torch.float32, device=device,
                )
                blh_sta   = torch.full((len(x_sta_np), 1), blh_h_n, dtype=torch.float32, device=device)
                elev_sta  = torch.tensor(e_sta_np[:, None], dtype=torch.float32, device=device)
                C_h, _    = model(xyt_sta, blh=blh_sta, elev=elev_sta)
                C_hourly.append(C_h)

            # K accumulation (no grad needed)
            with torch.no_grad():
                _, (Kx_h, Ky_h, _) = model(xyt_int.detach(), blh=blh_int, elev=elev_int)
                k_means.append(float((Kx_h.mean() + Ky_h.mean()) / 2.0))
            blh_values.append(blh_h_n)

        # ── Loss assembly ─────────────────────────────────────────────────
        L_pde  = (L_pde_day / len(SNAPSHOT_HOURS)) if w["pde"] > 0 else torch.zeros(1, device=device)

        # Data loss: compare daily-mean C_pred to SIATA observations
        L_data = torch.zeros(1, device=device)
        if w["data"] > 0 and len(C_hourly) > 0:
            C_daily = torch.stack(C_hourly, dim=0).mean(dim=0).squeeze()   # (N_sta,)
            C_obs_t = torch.tensor(C_obs, dtype=torch.float32, device=device)
            L_data  = ((C_daily - C_obs_t) ** 2).mean() / pm25_var_t

        # BC loss: domain-mean C prediction vs SIATA city-mean (magnitude constraint)
        L_bc = torch.zeros(1, device=device)
        if w["bc"] > 0 and len(C_hourly) > 0:
            C_domain_mean = torch.stack(C_hourly, dim=0).mean()
            L_bc = ((C_domain_mean - city_mean_today) ** 2) / pm25_var_t

        # K–BLH correlation regulariser
        # IMPORTANT: sample MULTIPLE DATES (not same-day snapshots) so that BLH varies.
        # Same-day snapshots all share one daily-mean BLH → std=0 → correlation undefined.
        # Using N_KBLH_DATES random dates with different BLH values gives a valid gradient.
        L_kblh = torch.zeros(1, device=device)
        if w["kblh"] > 0:
            N_KBLH_DATES = 8
            kblh_dates = dates[rng.integers(0, n_dates, size=N_KBLH_DATES)]
            k_grads_list = []
            blh_kblh_list = []
            xy_kblh = rng.uniform(0.0, 1.0, (64, 2)).astype(np.float32)   # 64-point subset
            t_kblh_np = np.full((64, 1), 0.5, dtype=np.float32)           # noon
            elev_kblh_np = elev_interp(xy_kblh[:, 0], xy_kblh[:, 1])
            elev_kblh_t = torch.tensor(elev_kblh_np[:, None], dtype=torch.float32, device=device)

            for kd in kblh_dates:
                kd_df    = daily_sta[daily_sta["date"] == kd]
                blh_kd   = float(kd_df["blh"].mean()) if "blh" in kd_df.columns else 1000.0
                blh_kn   = blh_kd / PINN_BLH_NORM_SCALE
                xyt_kblh = torch.tensor(
                    np.hstack([xy_kblh, t_kblh_np]),
                    dtype=torch.float32, device=device,
                )
                blh_kblh_t = torch.full((64, 1), blh_kn, dtype=torch.float32, device=device)
                _, (Kx_k, Ky_k, _) = model(xyt_kblh, blh=blh_kblh_t, elev=elev_kblh_t)
                k_grads_list.append((Kx_k.mean() + Ky_k.mean()) / 2.0)
                blh_kblh_list.append(blh_kn)

            blh_kblh_arr = torch.tensor(blh_kblh_list, dtype=torch.float32, device=device)
            k_kblh_t     = torch.stack(k_grads_list)
            if blh_kblh_arr.std() > 1e-6:
                r_kblh_train = _pearson_corr(blh_kblh_arr, k_kblh_t)
                L_kblh = w["kblh"] * (1.0 - r_kblh_train) ** 2

        L_total = w["pde"] * L_pde + w["data"] * L_data + w["bc"] * L_bc + L_kblh

        L_total.backward()
        import torch.nn as nn
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=10.0)
        optimizer.step()
        scheduler.step()

        # ── Logging ───────────────────────────────────────────────────────
        record = {
            "epoch":    epoch,
            "L_total":  float(L_total),
            "L_pde":    float(L_pde),
            "L_data":   float(L_data),
            "L_bc":     float(L_bc),
            "L_kblh":   float(L_kblh),
            "lr":       scheduler.get_last_lr()[0],
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
            val = spatial_validation(model, daily_sta, elev_interp, device)
            gates = check_gates(val)
            log.info(
                f"  [spatial] R²={val['spatial_R2']:.3f} "
                f"std_C={val['std_C_sta']:.2f} µg/m³  "
                f"r_kblh={val['r_kblh']:.3f}  "
                f"{'✓R²' if gates['spatial_R2_pass'] else '✗R²'}  "
                f"{'✓K-BLH' if gates['r_kblh_pass'] else '✗K-BLH'}"
            )
            record.update(val)

            if wandb_run is not None:
                wandb_run.log({**record, "epoch": epoch})

        # ── Checkpointing ─────────────────────────────────────────────────
        if epoch % save_every == 0 and epoch > 0:
            import torch
            ckpt_path = CHECKPOINT_DIR / f"epoch_{epoch:05d}.pt"
            torch.save({
                "epoch":          epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "loss_history":   loss_history,
            }, str(ckpt_path))
            log.info(f"  Checkpoint saved: {ckpt_path.name}")

    return loss_history


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def k_field_diagnostic(model, daily_sta: pd.DataFrame, elev_interp, device) -> dict:
    """
    K-field validation before Stage 3 (expert pre-Stage-3 checklist, Q3).

    Checks:
      (a) Diurnal K ratio: K(noon) / K(midnight) > 5 × (Stull 1988 Ch.9)
          If ratio < 2: DiffusionSubNetV3 hasn't learned BLH conditioning.
      (b) K–BLH spatial correlation across dates: should be positive.
          Computed at domain-centroid point (x=0.5, y=0.5).
      (c) K magnitude range: should span [1, 100] m²/s (physical plausibility).
          If K clusters at K_MIN=1: floor is doing all the work.

    Prints results as a checklist. Returns dict of diagnostic values.
    """
    import torch
    from src.stage3_pinn.models.fourier_pinn_v3 import K_MAX_V3
    from config import K_MIN_MS2 as K_MIN_V3

    model.eval()
    dates = sorted(daily_sta["date"].unique())
    N_SAMPLE = min(50, len(dates))
    sample_dates = np.random.default_rng(1).choice(dates, size=N_SAMPLE, replace=False)

    # Use domain centroid and a 5×5 grid for spatial coverage
    xs = np.linspace(0.1, 0.9, 5, dtype=np.float32)
    ys = np.linspace(0.1, 0.9, 5, dtype=np.float32)
    xx, yy = np.meshgrid(xs, ys)
    xy_grid = np.stack([xx.ravel(), yy.ravel()], axis=1)   # (25, 2)
    elev_grid_np = elev_interp(xy_grid[:, 0], xy_grid[:, 1])
    elev_grid_t = torch.tensor(elev_grid_np[:, None], dtype=torch.float32, device=device)

    k_noon_list    = []
    k_midnight_list = []
    k_all          = []   # all K values for magnitude range check
    k_daily_mean   = []   # domain-mean K per date (for K–BLH correlation)
    blh_daily      = []   # BLH per date

    with torch.no_grad():
        for date in sample_dates:
            day_df = daily_sta[daily_sta["date"] == date]
            blh_d  = float(day_df["blh"].mean()) if "blh" in day_df.columns else 1000.0
            blh_n  = blh_d / PINN_BLH_NORM_SCALE
            blh_t  = torch.full((len(xy_grid), 1), blh_n, dtype=torch.float32, device=device)

            # Noon (t=0.5)
            xyt_noon = torch.tensor(
                np.hstack([xy_grid, np.full((len(xy_grid), 1), 0.5, dtype=np.float32)]),
                dtype=torch.float32, device=device,
            )
            _, (Kx_n, Ky_n, _) = model(xyt_noon, blh=blh_t, elev=elev_grid_t)
            k_n = float(((Kx_n + Ky_n) / 2.0).mean())
            k_noon_list.append(k_n)
            k_all.extend(((Kx_n + Ky_n) / 2.0).cpu().numpy().ravel().tolist())

            # Midnight (t=0.0)
            xyt_mid = torch.tensor(
                np.hstack([xy_grid, np.zeros((len(xy_grid), 1), dtype=np.float32)]),
                dtype=torch.float32, device=device,
            )
            _, (Kx_m, Ky_m, _) = model(xyt_mid, blh=blh_t, elev=elev_grid_t)
            k_m = float(((Kx_m + Ky_m) / 2.0).mean())
            k_midnight_list.append(k_m)

            k_daily_mean.append(k_n)   # noon K as representative
            blh_daily.append(blh_n)

    model.train()

    k_noon_arr     = np.array(k_noon_list)
    k_midnight_arr = np.array(k_midnight_list)
    k_all_arr      = np.array(k_all)

    # (a) Diurnal ratio
    diurnal_ratio = float(np.mean(k_noon_arr) / (np.mean(k_midnight_arr) + 1e-8))

    # (b) K–BLH correlation
    if np.std(blh_daily) > 1e-3:
        r_kblh_diag = float(np.corrcoef(blh_daily, k_daily_mean)[0, 1])
    else:
        r_kblh_diag = float("nan")

    # (c) Magnitude range
    k_min_obs = float(k_all_arr.min())
    k_max_obs = float(k_all_arr.max())
    k_mean_obs = float(k_all_arr.mean())
    frac_at_floor = float(np.mean(k_all_arr < K_MIN_V3 + 0.5))  # fraction within 0.5 of floor

    # Print checklist
    log.info("─── K-field Diagnostic (pre-Stage 3 checklist) ───")
    diurnal_pass = diurnal_ratio >= 2.0
    kblh_pass    = (not np.isnan(r_kblh_diag)) and r_kblh_diag > 0.0
    mag_pass     = k_min_obs >= 0.5 and k_max_obs <= K_MAX_V3 * 1.1 and frac_at_floor < 0.5
    log.info(
        f"  (a) Diurnal ratio K(noon)/K(midnight) = {diurnal_ratio:.2f}× "
        f"(target ≥5×, warn <2×): {'PASS ✓' if diurnal_pass else 'WARN ✗'}"
    )
    log.info(
        f"  (b) K–BLH correlation = {r_kblh_diag:.3f} "
        f"(target >0): {'PASS ✓' if kblh_pass else 'FAIL ✗'}"
    )
    log.info(
        f"  (c) K magnitude: min={k_min_obs:.1f}, mean={k_mean_obs:.1f}, max={k_max_obs:.1f} m²/s "
        f"(floor={K_MIN_V3}, ceil={K_MAX_V3})"
    )
    log.info(
        f"       fraction at floor (<K_MIN+0.5): {frac_at_floor:.1%} "
        f"(warn if >50%): {'OK ✓' if mag_pass else 'WARN — floor dominant'}"
    )
    log.info(
        f"  → DiffusionSubNetV3 status: "
        f"{'BLH conditioning ACTIVE' if diurnal_pass and kblh_pass else 'BLH conditioning WEAK — check K_aniso + K_base'}"
    )

    return {
        "diurnal_ratio":   diurnal_ratio,
        "r_kblh_diag":     r_kblh_diag,
        "k_min_obs":       k_min_obs,
        "k_max_obs":       k_max_obs,
        "k_mean_obs":      k_mean_obs,
        "frac_at_floor":   frac_at_floor,
        "diurnal_pass":    diurnal_pass,
        "kblh_pass":       kblh_pass,
        "mag_pass":        mag_pass,
    }


def _setup_wandb(config: dict):
    api_key = os.environ.get("WANDB_API_KEY")
    try:
        import wandb
        if api_key:
            wandb.login(key=api_key, relogin=True)
        run = wandb.init(
            project=WANDB_PROJECT,
            name=f"medellin-pinn-{'warm' if config.get('warm_start') else 'cold'}",
            config=config,
            tags=["stage2", "medellin", "v3"],
        )
        log.info(f"W&B run: {run.url}")
        return run
    except Exception as exc:
        log.warning(f"W&B init failed ({exc}) — continuing without tracking")
        return None


def main():
    parser = argparse.ArgumentParser(description="Train FourierPINNV3 on Medellín SIATA data")
    parser.add_argument("--epochs",      type=int,   default=DEFAULT_EPOCHS)
    parser.add_argument("--lr",          type=float, default=DEFAULT_LR)
    parser.add_argument("--warm-start",  type=str, default=None, metavar="CKPT_PATH",
                        help="Path to FourierPINNV3 checkpoint to warm-start from (same architecture only)")
    parser.add_argument("--save-every",  type=int,   default=SAVE_EVERY)
    parser.add_argument("--wandb",       action="store_true")
    parser.add_argument("--check-gates", action="store_true",
                        help="Load latest checkpoint and evaluate gate conditions only")
    parser.add_argument("--k-diagnostic", action="store_true",
                        help="Run K-field diagnostic on latest checkpoint (pre-Stage 3 checklist)")
    args = parser.parse_args()

    import torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info(f"Device: {device}")

    daily_sta, city_mean, pm25_var = load_siata_daily()
    elev_interp = build_elev_interpolator()
    model = build_model(device=device, warm_start_path=args.warm_start)

    if args.check_gates or args.k_diagnostic:
        # Load most recent checkpoint
        ckpts = sorted(CHECKPOINT_DIR.glob("epoch_*.pt"))
        if not ckpts:
            # Also check for final model
            final_path = CHECKPOINT_DIR / "medellin_pinn_final.pt"
            if final_path.exists():
                ckpts = [final_path]
            else:
                log.error(f"No checkpoints found in {CHECKPOINT_DIR}")
                return
        ckpt = torch.load(str(ckpts[-1]), map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])
        log.info(f"Loaded checkpoint: {ckpts[-1].name}")

        if args.check_gates:
            val   = spatial_validation(model, daily_sta, elev_interp, device)
            gates = check_gates(val)
            log.info(f"Gate (1) spatial_R² > 0.50: {val['spatial_R2']:.3f} → {'PASS ✓' if gates['spatial_R2_pass'] else 'FAIL ✗'}")
            log.info(f"Gate (2) K–BLH r > 0.50:   {val['r_kblh']:.3f}    → {'PASS ✓' if gates['r_kblh_pass'] else 'FAIL ✗'}")
            log.info(f"Gate (3) zero-shot Chiang Mai: run validate_chiangmai.py separately")

        if args.k_diagnostic:
            k_diag = k_field_diagnostic(model, daily_sta, elev_interp, device)
            log.info("K-field diagnostic complete. See above for checklist.")
        return

    run_config = dict(epochs=args.epochs, lr=args.lr, warm_start=args.warm_start)
    wandb_run  = _setup_wandb(run_config) if args.wandb else None

    t0 = time.time()
    loss_history = train(
        model, daily_sta, city_mean, pm25_var, elev_interp,
        n_epochs=args.epochs, lr=args.lr, device=device,
        wandb_run=wandb_run, save_every=args.save_every,
    )
    elapsed = (time.time() - t0) / 60.0
    log.info(f"Training complete in {elapsed:.1f} min")

    # Final spatial validation
    val   = spatial_validation(model, daily_sta, elev_interp, device)
    gates = check_gates(val)
    log.info("─── Final Gate Check ───")
    log.info(f"  (1) spatial_R² > 0.50: {val['spatial_R2']:.3f} → {'PASS ✓' if gates['spatial_R2_pass'] else 'FAIL ✗'}")
    log.info(f"  (2) K–BLH r  > 0.50:  {val['r_kblh']:.3f}    → {'PASS ✓' if gates['r_kblh_pass'] else 'FAIL ✗'}")

    # K-field diagnostic (expert pre-Stage-3 checklist)
    k_diag = k_field_diagnostic(model, daily_sta, elev_interp, device)

    # Save final model
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    final_path = CHECKPOINT_DIR / "medellin_pinn_final.pt"
    torch.save({
        "epoch":            args.epochs,
        "model_state_dict": model.state_dict(),
        "loss_history":     loss_history,
        "spatial_R2":       val["spatial_R2"],
        "r_kblh":           val["r_kblh"],
        "gates":            gates,
        "k_diag":           k_diag,
        "config":           run_config,
    }, str(final_path))
    log.info(f"Saved: {final_path}")

    # Save loss CSV
    import csv
    csv_path = CHECKPOINT_DIR / "medellin_pinn_losses.csv"
    if loss_history:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(loss_history[0].keys()))
            writer.writeheader()
            writer.writerows(loss_history)
    log.info(f"Loss CSV: {csv_path}")

    if wandb_run is not None:
        wandb_run.summary.update({
            "final_spatial_R2":    val["spatial_R2"],
            "final_r_kblh":        val["r_kblh"],
            "gate_1_pass":         gates["spatial_R2_pass"],
            "gate_2_pass":         gates["r_kblh_pass"],
            "k_diurnal_ratio":     k_diag["diurnal_ratio"],
            "k_r_kblh_diag":       k_diag["r_kblh_diag"],
            "k_frac_at_floor":     k_diag["frac_at_floor"],
        })
        wandb_run.finish()


if __name__ == "__main__":
    main()
