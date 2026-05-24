"""
train.py — Master training loop for Stage 3 Kandy PINN.

Orchestrates all components: domain, collocation, loss functions, curriculum.
Loads Stage 1 predictions as boundary conditions and data supervision.

Three initialisation paths (from transfer_decision.json):
  A. use_pretrained_frozen  — load backbone, freeze, fine-tune head
  B. use_pretrained_unfrozen — load backbone, full fine-tune
  C. random_init            — cold start training

Gap fixes implemented (2026-03-02):
  B1 — Quasi-steady-state 8-snapshot training loop (per epoch: sample date,
        loop ERA5 snapshots at h=0,3,...,21, call steady_state_pde_loss per
        snapshot, average PDE loss over 8 snapshots).
  B2 — BLH plumbing: blh_norm = BLH_m / 2000.0 passed to all model() calls
        and to steady_state_pde_loss.
  B3 — t_norm = h/24 per snapshot (not t=0 hardcoded). Data loss evaluates C
        at all 8 hours and compares the mean to Stage 1 daily-mean PM2.5.
  B5 — K–BLH correlation regulariser: within-epoch temporal correlation of
        domain-mean K vs BLH across the 8 snapshots. λ_kblh = 0.01.
  C2 — model.source_subnet.t_max_hours = 24.0 set after backbone loading so
        SourceSubNet interprets t_norm as h/24 (hour of day in [0,1]).

Best practice: run with --profile first (20 epochs) to confirm GPU memory.

Usage:
    python train.py --init A --epochs 1000 --lr 5e-4
    python train.py --init C --epochs 1000  # Cold start fallback
"""

import argparse
import json
import logging
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    LOG_FORMAT, LOG_DATEFMT, MODELS_DIR, MERGED_DIR, PINN_GRID_RESOLUTION_M,
    N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY, PINN_EPOCHS, PINN_LR,
    PINN_PRETRAINED_BACKBONE, PINN_BLH_NORM_SCALE, PINN_INPUT_DIR,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("train_pinn")

CHECKPOINT_DIR   = MODELS_DIR / "stage3_pinn"
TRANSFER_DECISION_JSON = MODELS_DIR / "stage2_pretrain" / "chiangmai_validation" / "transfer_decision.json"

WANDB_PROJECT = "kandy-pinn"
WANDB_ENTITY  = None   # set to your W&B username/team if needed

# ERA5 3-hourly snapshot hours (quasi-steady-state: 8 snapshots per day)
SNAPSHOT_HOURS = [0, 3, 6, 9, 12, 15, 18, 21]

# K–BLH correlation regularisation weight (B5).
# Soft prior that penalises K not correlating positively with BLH.
# λ=0.01 is small — enforces a direction, not a magnitude.
LAMBDA_KBLH = 0.01

# Default model version for Stage 3 (v4 = FourierPINNV3 + deviation-from-prior + KOALA anchor)
DEFAULT_MODEL_VERSION = "v4"


def _get_stage3_v3_weights(epoch: int, n_epochs: int) -> dict:
    """
    Stage 3 v3 three-phase data-dominant curriculum (I4 fix — validated against v8/v2 explosion lessons).

    LESSON from Stage 2 v8/v2: λ_pde ramp to majority weight causes PDE explosion regardless
    of λ_pde absolute value. Data must dominate at ALL epochs. λ_data > λ_pde always.

    Phase 1 (0–40%):  PDE inoculation — λ_pde=0.001, λ_data=0.70, λ_bc=0.20, λ_kblh=0.05
      With EMA-normalised L_pde≈1.0, pde contribution = 0.001×1.0 = 0.001 (negligible vs data).
      Network learns BLH/data structure before any PDE pressure.

    Phase 2 (40–70%): Gentle PDE onset — ramp λ_pde 0.001→0.10, λ_data 0.70→0.55.
      EMA keeps raw L_pde O(1) at phase transition — no gradient spike.

    Phase 3 (70–100%): Data-dominant steady state — λ_pde=0.10, λ_data=0.55.
      λ_data=0.55 > λ_pde=0.10 at all times. Physics guides structure, data anchors magnitude.
    """
    p1_end = int(0.40 * n_epochs)
    p2_end = int(0.70 * n_epochs)
    if epoch < p1_end:
        return dict(bc=0.20, pde=0.001, data=0.70, kblh=0.05, kb=0.05, phys=0.0, mean_anchor=0.0)
    elif epoch < p2_end:
        t = (epoch - p1_end) / max(1, p2_end - p1_end)
        return dict(
            bc          = 0.20 + t * (0.15 - 0.20),
            pde         = 0.001 + t * (0.10 - 0.001),
            data        = 0.70  + t * (0.55 - 0.70),
            kblh        = 0.05  + t * (0.15 - 0.05),
            kb          = 0.05,
            phys        = 0.0,
            mean_anchor = 0.0,
        )
    else:
        return dict(bc=0.15, pde=0.10, data=0.55, kblh=0.15, kb=0.05, phys=0.0, mean_anchor=0.0)


def _get_stage3_v4_weights(epoch: int, n_epochs: int) -> dict:
    """
    Stage 3 v4 curriculum — validated on Kaggle T4×2 (ALL 5 GATES PASS, 2026-04-19).

    Key difference from v3: adds L_mean_anchor to pull domain-mean toward KOALA 24.5 µg/m³.
    Phase 2 ends earlier (50% vs 70%) so anchor reaches full weight sooner.

    Phase 1 (0–20%):  Pure data, no PDE, no anchor. Model inherits Stage-1 structure via
                       deviation-from-prior (C_prior must be passed to model.forward).
    Phase 2 (20–50%): Ramp PDE 0→0.40, temp 0→0.20, anchor 0→0.30. Data fixed at 0.15.
    Phase 3 (50–100%): Full weights. w_anchor=0.30 overrides LR-collapse-induced drift.
    """
    p1_end = int(0.20 * n_epochs)
    p2_end = int(0.50 * n_epochs)
    if epoch < p1_end:
        return dict(pde=0.00, data=0.15, temp=0.00, mean_anchor=0.00, bc=0.0, kblh=0.0, kb=0.0, phys=0.0)
    elif epoch < p2_end:
        t = (epoch - p1_end) / max(1, p2_end - p1_end)
        return dict(
            pde         = t * 0.40,
            data        = 0.15,
            temp        = t * 0.20,
            mean_anchor = t * 0.30,
            bc=0.0, kblh=0.0, kb=0.0, phys=0.0,
        )
    else:
        return dict(pde=0.40, data=0.10, temp=0.20, mean_anchor=0.30, bc=0.0, kblh=0.0, kb=0.0, phys=0.0)


def _setup_wandb(run_config: dict):
    """
    Initialise a W&B run. Returns run object or None if unavailable/disabled.
    API key is read from WANDB_API_KEY env var or wandb.login() interactive.
    """
    api_key = os.environ.get("WANDB_API_KEY")
    try:
        import wandb
        if api_key:
            wandb.login(key=api_key, relogin=True)
        run = wandb.init(
            project=WANDB_PROJECT,
            entity=WANDB_ENTITY,
            name=f"stage3-kandy-{run_config.get('init_mode','?')}",
            config=run_config,
            tags=["stage3", "kandy", run_config.get("init_mode", "unknown")],
            resume="allow",
        )
        log.info(f"W&B run: {run.url}")
        return run
    except Exception as exc:
        log.warning(f"W&B init failed ({exc}) — continuing without tracking.")
        return None


def _get_device():
    try:
        import torch
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    except ImportError:
        raise ImportError("PyTorch required. Run: pip install torch")


def load_init_decision() -> dict:
    """Read transfer_decision.json to determine initialisation path."""
    if not TRANSFER_DECISION_JSON.exists():
        log.warning("transfer_decision.json not found — defaulting to cold start (C)")
        return {"decision": "C_cold_start", "stage3_init": "random_init"}
    with open(TRANSFER_DECISION_JSON) as f:
        return json.load(f)


def build_model(init_mode: str, device, model_version: str = DEFAULT_MODEL_VERSION):
    """Build FourierPINN model with appropriate initialisation.

    model_version='v3' (default): FourierPINNV3 — redesigned architecture with
        separate spatial/temporal embeddings, BLH in trunk, factored K.
        Warm-start from v8 backbone: only head_C transfers (dim mismatch elsewhere).
        cold-start: full random Xavier init.

    model_version='v2' (legacy): FourierPINN v2 — preserved for cold-start/warm-start
        comparison experiments and backward compat with v8 backbone loading.
        C2 fix applied: model.source_subnet.t_max_hours set to 24.0.
    """
    import torch

    road_kernel_path = PINN_INPUT_DIR / "kandy_road_kernel_100m.npz"

    if model_version in ("v3", "v4"):  # v4 uses same FourierPINNV3 architecture
        from src.stage3_pinn.models.fourier_pinn_v3 import (
            FourierPINNV3, load_partial_backbone,
            reinit_diffusion_subnet_v3, reinit_alpha_net,
        )
        model = FourierPINNV3(road_kernel_path=road_kernel_path)
        model = model.to(device)

        if init_mode in ("use_pretrained_frozen", "use_pretrained_unfrozen", "use_pretrained_v13"):
            ckpt_path = Path(PINN_PRETRAINED_BACKBONE) if PINN_PRETRAINED_BACKBONE else None
            if ckpt_path is None or not ckpt_path.exists():
                log.warning(f"Pretrained backbone not found: {ckpt_path} — cold start")
            else:
                ckpt = torch.load(str(ckpt_path), map_location=device, weights_only=False)
                v2_state = ckpt.get("model_state_dict", ckpt)
                n_loaded, n_skipped = load_partial_backbone(model, v2_state)
                log.info(f"v3 warm-start: {n_loaded} keys from v8 backbone; {n_skipped} reinit")
            # Always reinit city-specific components regardless of backbone availability
            reinit_diffusion_subnet_v3(model)
            reinit_alpha_net(model)
        else:
            log.info("v3 cold-start: full random Xavier initialisation")

    else:
        # v2 legacy path — unchanged for backward compat
        from src.stage3_pinn.models.fourier_pinn import build_fourier_pinn
        model = build_fourier_pinn()
        model = model.to(device)

        if init_mode in ("use_pretrained_frozen", "use_pretrained_unfrozen"):
            ckpt_path = Path(PINN_PRETRAINED_BACKBONE) if PINN_PRETRAINED_BACKBONE else None
            if ckpt_path is None or not ckpt_path.exists():
                log.warning(f"Pretrained checkpoint not found: {ckpt_path} — falling back to random init")
            else:
                ckpt = torch.load(str(ckpt_path), map_location=device, weights_only=False)
                missing, unexpected = model.load_state_dict(
                    ckpt["model_state_dict"], strict=False
                )
                if missing:
                    log.info(f"Backbone keys not found (reinitialised): {missing[:3]}...")
                if unexpected:
                    log.info(f"Checkpoint keys discarded: {unexpected[:3]}...")
                log.info(f"Loaded v8 backbone (v2 model, strict=False)")
                from src.stage3_pinn.models.fourier_pinn import (
                    reinit_source_subnet, reinit_diffusion_subnet
                )
                reinit_source_subnet(model)
                reinit_diffusion_subnet(model)
                if init_mode == "use_pretrained_frozen":
                    from src.stage2_transfer.pretrain.layer_freezing import freeze_backbone
                    model = freeze_backbone(model, n_frozen_layers=4)
        else:
            log.info("v2 cold-start: random Xavier initialisation")

        # C2: reset SourceSubNet time scale to 24h for Stage 3
        model.source_subnet.t_max_hours = torch.tensor(24.0)
        log.info("C2: model.source_subnet.t_max_hours set to 24.0")

    return model, init_mode


def load_stage1_data() -> "pd.DataFrame":
    """Load Stage 1b pixel-level predictions for boundary condition supervision.

    Source: pm25_pixel_predictions.parquet produced by train_pixel_xgboost.py.
    Columns required by DirichletBC: date, lat, lon, pm25_pred.
    Optional columns for uncertainty weighting: pm25_q05, pm25_q95.
    """
    import pandas as pd
    pred_path = MERGED_DIR / "pm25_pixel_predictions.parquet"
    if not pred_path.exists():
        raise FileNotFoundError(
            f"Stage 1b pixel predictions not found: {pred_path}\n"
            "Run: python src/stage1_satml/models/train_pixel_xgboost.py"
        )
    df = pd.read_parquet(pred_path)
    # Rename pixel prediction column to the name DirichletBC expects
    if "pm25_pixel_pred" in df.columns and "pm25_pred" not in df.columns:
        df = df.rename(columns={"pm25_pixel_pred": "pm25_pred"})
    # Ensure date is a plain column (not index) for date-string filtering
    if df.index.name == "date":
        df = df.reset_index()
    log.info(f"Loaded {len(df):,} Stage 1b pixel prediction rows "
             f"({df['date'].nunique()} dates, {df['pixel_id'].nunique()} pixels)")
    return df


def _extract_blh_m(df_today: "pd.DataFrame") -> float:
    """Return a representative BLH in metres from a Stage-1 date slice.

    Uses blh_max (daytime peak BLH) as the daily representative value for
    diffusivity conditioning. Falls back gracefully if columns are absent.
    With daily-mean ERA5, all 8 intra-day snapshots share this same BLH —
    the K–BLH diurnal signal requires 3-hourly ERA5 (future improvement).
    """
    if "blh_max" in df_today.columns:
        return float(df_today["blh_max"].mean())
    if "blh_min" in df_today.columns:
        return float(df_today["blh_min"].mean())
    # Neutral fallback → blh_norm = 1000/2000 = 0.5
    return 1000.0


def _extract_wind(df_today: "pd.DataFrame"):
    """Return (u10, v10) daily-mean wind in m/s."""
    u = float(df_today["u10"].mean()) if "u10" in df_today.columns else 0.5
    v = float(df_today["v10"].mean()) if "v10" in df_today.columns else 0.5
    return u, v


def _extract_precip_mmh(df_today: "pd.DataFrame") -> float:
    """Return daily total precipitation in mm/h (0 if unavailable)."""
    # ERA5 'tp' column in the pixel dataset may be in m (ERA5 convention).
    # Divide by 24 to get mm/h daily average (×1000 to m→mm, /24h).
    for col, scale in [("tp_mmh", 1.0), ("tp", 1000.0 / 24.0), ("total_precipitation", 1000.0 / 24.0)]:
        if col in df_today.columns:
            return max(0.0, float(df_today[col].mean()) * scale)
    return 0.0


def _pearson_corr(a: "torch.Tensor", b: "torch.Tensor") -> "torch.Tensor":
    """Differentiable Pearson correlation between two 1-D tensors."""
    a_c = a - a.mean()
    b_c = b - b.mean()
    return (a_c * b_c).sum() / (a_c.norm() * b_c.norm() + 1e-8)


def train_pinn(
    model,
    stage1_df:  "pd.DataFrame",
    n_epochs:   int,
    lr:         float,
    device,
    use_rar:    bool = True,
    rar_start:  int  = 200,
    save_every: int  = 100,
    wandb_run=None,
    model_version: str = DEFAULT_MODEL_VERSION,
    steady:     bool = False,   # False=TD-PDE (default); True=QSS for baseline comparison
) -> list:
    """
    Main PINN training loop — Stage 3 quasi-steady-state (gaps B1–B5+C2).

    Per-epoch procedure:
      1. Sample one random date from Stage 1 training dates.
      2. For each of the 8 ERA5 3-hourly snapshots (h=0,3,...,21):
           a. Set t_norm = h / 24.0
           b. Build collocation tensors with this t_norm (same for all N pts)
           c. Pass blh_norm = BLH_m / 2000.0 to model and PDE loss (B2)
           d. Compute steady_state_pde_loss (B1) — drops ∂C/∂t algebraically
           e. Evaluate C at Stage 1 pixel locations for daily-mean constraint (B3)
           f. Compute domain-mean K for K–BLH correlation accumulation (B5)
      3. L_pde = mean(L_pde_h) over 8 snapshots.
      4. C_daily_pred = mean(C_h) over 8 snapshots — compared to Stage 1
         daily-mean PM2.5 (B3 fix: was t=0 hardcoded, now 8-hour average).
      5. L_kblh = λ × (1 − Pearson_r(BLH_values, K_means))² (B5).
      6. total_loss + L_kblh → backward → optimizer step.

    Args:
        model      : FourierPINN model (C2 fix already applied in build_model)
        stage1_df  : Stage 1 PM2.5 predictions DataFrame
        n_epochs   : Total training epochs
        lr         : Initial learning rate (Adam)
        device     : torch.device
        use_rar    : Enable RAR after rar_start epoch (spatial collocation only)
        rar_start  : Epoch to switch from uniform to RAR collocation
        save_every : Checkpoint save frequency

    Returns:
        loss_history : List of dicts with per-epoch loss breakdown
    """
    import torch
    import torch.optim as optim

    from src.stage3_pinn.training.curriculum    import CurriculumScheduler
    from src.stage3_pinn.training.loss_functions import (
        data_fidelity_loss, total_loss, LossTracker,
    )
    from src.stage3_pinn.training.collocation   import sample_uniform, sample_rar
    from src.stage3_pinn.physics.advection_diffusion import steady_state_pde_loss
    from src.stage3_pinn.physics.pde_residual_v3 import pde_residual_v3
    from src.stage3_pinn.physics.constraints    import compute_all_constraints
    from src.stage3_pinn.domain.boundary_conditions import DirichletBC
    from config import KANDY_PINN_BBOX

    use_v3 = (model_version == "v3")
    use_v4 = (model_version == "v4")

    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=lr)
    if use_v4:
        # v4: warm restarts prevent LR collapse that caused G5 FAIL in v3
        scheduler_opt = optim.lr_scheduler.CosineAnnealingWarmRestarts(
            optimizer, T_0=2000, T_mult=2, eta_min=1e-5
        )
    else:
        scheduler_opt = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_epochs, eta_min=1e-6)
    curriculum    = CurriculumScheduler(total_epochs=n_epochs)
    bc_handler    = DirichletBC(stage1_df)
    tracker       = LossTracker()

    dates   = sorted(stage1_df["date"].unique())
    n_dates = len(dates)
    rng     = np.random.default_rng(42)

    log.info(f"Starting PINN training: {n_epochs} epochs, {n_dates} training dates, device={device}")
    curriculum.log_schedule(every=200)

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    # S4: Load Kandy elevation grid for real DEM wiring (replaces 0.5 placeholder)
    from config import PINN_INPUT_DIR
    from scipy.interpolate import RegularGridInterpolator as _RGI
    _elev_npz     = np.load(str(PINN_INPUT_DIR / "kandy_elev_grid_100m.npz"))
    _elev_norm_2d = _elev_npz['elev_norm'].astype(np.float32)  # (150, 150), ∈ [0,1]
    _lat_vec      = _elev_npz['lat_grid'][:, 0].astype(np.float64)   # (150,) S→N or N→S
    _lon_vec      = _elev_npz['lon_grid'][0, :].astype(np.float64)   # (150,) W→E
    # Sort ascending so RegularGridInterpolator axes are monotonically increasing
    if _lat_vec[0] > _lat_vec[-1]:
        _lat_vec      = _lat_vec[::-1].copy()
        _elev_norm_2d = _elev_norm_2d[::-1, :].copy()
    _elev_interp = _RGI(
        (_lat_vec, _lon_vec), _elev_norm_2d,
        method='linear', bounds_error=False, fill_value=0.2,
    )
    # Pre-compute domain centroid/half-extents for xy_norm → lat/lon conversion
    _LAT_CTR  = (KANDY_PINN_BBOX['lat_max'] + KANDY_PINN_BBOX['lat_min']) / 2.0
    _LAT_HALF = (KANDY_PINN_BBOX['lat_max'] - KANDY_PINN_BBOX['lat_min']) / 2.0
    _LON_CTR  = (KANDY_PINN_BBOX['lon_max'] + KANDY_PINN_BBOX['lon_min']) / 2.0
    _LON_HALF = (KANDY_PINN_BBOX['lon_max'] - KANDY_PINN_BBOX['lon_min']) / 2.0
    log.info("S4: Elevation grid loaded — real DEM wired (kandy_elev_grid_100m.npz)")

    # I1: EMA of raw L_pde — keeps normalised L_pde ≈ O(1) at Phase 2 onset
    _pde_ema = 1.0

    # Initial spatial collocation layout (xy only — t is overridden per snapshot)
    xy_int_np, _, xy_bnd_np, t_bnd_np = sample_uniform(
        N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY, KANDY_PINN_BBOX
    )

    # Pre-compute elevation at interior collocation points (static for uniform grid)
    _lats_int = (xy_int_np[:, 1] * _LAT_HALF + _LAT_CTR).astype(np.float64)
    _lons_int = (xy_int_np[:, 0] * _LON_HALF + _LON_CTR).astype(np.float64)
    _elev_int_np = _elev_interp(np.column_stack([_lats_int, _lons_int])).astype(np.float32)

    for epoch in range(n_epochs):
        model.train()
        # v4: KOALA-anchored curriculum; v3: data-dominant; v2: legacy
        if use_v4:
            _w      = _get_stage3_v4_weights(epoch, n_epochs)
            lambdas = type('W', (), _w)()
        elif use_v3:
            _w      = _get_stage3_v3_weights(epoch, n_epochs)
            lambdas = type('W', (), _w)()
        else:
            lambdas = curriculum.step(epoch)
        current_lr = scheduler_opt.get_last_lr()[0] if epoch > 0 else lr

        # Sample one random date for this epoch
        date_today = dates[rng.integers(0, n_dates)]
        df_today   = stage1_df[stage1_df["date"].astype(str) == str(date_today)]

        # Extract daily ERA5 scalars for this date
        blh_m       = _extract_blh_m(df_today)
        blh_norm    = blh_m / PINN_BLH_NORM_SCALE   # e.g. 800m → 0.40
        wind_u_d, wind_v_d = _extract_wind(df_today)
        precip_mmh  = _extract_precip_mmh(df_today)
        c1_mean     = float(df_today["pm25_pred"].mean()) if "pm25_pred" in df_today else 0.0

        # RAR update (spatial collocation refinement, BLH=default for heuristic)
        if use_rar and epoch >= rar_start and epoch % 50 == 0:
            try:
                xy_int_np, _ = sample_rar(
                    model, n_coarse=5000, n_add=200,
                    n_keep=N_COLLOCATION_INTERIOR - 200,
                    xy_current=xy_int_np,
                    t_current=np.full((len(xy_int_np), 1), 0.5, dtype=np.float32),
                    wind_u=wind_u_d, wind_v=wind_v_d, device=device,
                )
            except Exception as e:
                log.debug(f"RAR update failed at epoch {epoch}: {e}")
            # S4: recompute elevation at updated collocation points after RAR
            _lats_int    = (xy_int_np[:, 1] * _LAT_HALF + _LAT_CTR).astype(np.float64)
            _lons_int    = (xy_int_np[:, 0] * _LON_HALF + _LON_CTR).astype(np.float64)
            _elev_int_np = _elev_interp(np.column_stack([_lats_int, _lons_int])).astype(np.float32)

        # Pre-build Stage-1 pixel tensors (same x,y for all 8 snapshots)
        x_s1 = torch.tensor(df_today["x_norm"].values[:, None],
                             dtype=torch.float32, device=device) if len(df_today) > 0 else None
        y_s1 = torch.tensor(df_today["y_norm"].values[:, None],
                             dtype=torch.float32, device=device) if len(df_today) > 0 else None
        if x_s1 is not None:
            C_target_s1 = torch.tensor(df_today["pm25_pred"].values,
                                       dtype=torch.float32, device=device)
            if "weight" in df_today.columns:
                w_s1 = torch.tensor(df_today["weight"].values,
                                    dtype=torch.float32, device=device)
            else:
                w_s1 = None

        optimizer.zero_grad()

        # ── 8-snapshot quasi-steady-state loop (B1 + B2 + B3) ──────────────
        L_pde_day   = torch.zeros(1, device=device)
        C_hourly    = []    # for daily-mean data constraint (B3)
        k_means     = []    # for K–BLH correlation regulariser (B5)
        blh_values  = []    # BLH scalars per snapshot (for B5 correlation)

        for h in SNAPSHOT_HOURS:
            t_norm = h / 24.0   # t_norm ∈ {0, 1/8, 2/8, ..., 7/8}

            # Per-snapshot BLH and wind (daily-mean; 3-hourly ERA5 is a future improvement)
            # blh_norm is the same for all 8 snapshots when using daily-mean ERA5
            blh_h = blh_norm  # scalar

            # Build interior collocation tensor with t_norm = h/24 for this snapshot
            t_snap_np  = np.full((len(xy_int_np), 1), t_norm, dtype=np.float32)
            xyt_int    = torch.tensor(
                np.hstack([xy_int_np, t_snap_np]),
                dtype=torch.float32, device=device
            ).requires_grad_(True)

            wu_int = torch.full((len(xy_int_np), 1), wind_u_d, dtype=torch.float32, device=device)
            wv_int = torch.full((len(xy_int_np), 1), wind_v_d, dtype=torch.float32, device=device)

            # B2: blh_tensor for this snapshot — shape (N, 1) matching collocation pts
            blh_tensor = torch.full(
                (len(xy_int_np), 1), blh_h, dtype=torch.float32, device=device
            )

            precip_tensor = None
            if precip_mmh > 0:
                precip_tensor = torch.full(
                    (len(xy_int_np), 1), precip_mmh, dtype=torch.float32, device=device
                )

            # B1: quasi-steady-state PDE loss for this snapshot
            # v3: use pde_residual_v3 with real DEM elevation (S4 fix — was 0.5 placeholder)
            # v2: use legacy steady_state_pde_loss
            if lambdas.pde > 0:
                if use_v3:
                    elev_int = torch.tensor(
                        _elev_int_np[:, None], dtype=torch.float32, device=device
                    )
                    R_pde = pde_residual_v3(
                        model, xyt_int, wu_int, wv_int,
                        precip=precip_tensor,
                        blh=blh_tensor,
                        elev=elev_int,
                        steady=steady,
                    )
                    L_pde_h = (R_pde ** 2).mean()
                else:
                    L_pde_h = steady_state_pde_loss(
                        model, xyt_int, wu_int, wv_int,
                        precip=precip_tensor,
                        blh=blh_tensor,
                    )
                L_pde_day = L_pde_day + L_pde_h

            # B3: evaluate C at Stage-1 pixel locations for daily-mean constraint
            if lambdas.data > 0 and x_s1 is not None:
                t_s1_h   = torch.full_like(x_s1, t_norm)
                xyt_s1_h = torch.cat([x_s1, y_s1, t_s1_h], dim=1)
                blh_s1_h = torch.full_like(x_s1, blh_h)
                C_h, _   = model(xyt_s1_h, blh=blh_s1_h)
                C_hourly.append(C_h)

            # B5: accumulate domain-mean K for K–BLH correlation regulariser.
            # Separate forward pass (no spatial grad needed for K alone).
            with torch.no_grad():
                _, (Kx_h, Ky_h, _) = model(xyt_int.detach(), blh=blh_tensor)
                k_means.append(((Kx_h.mean() + Ky_h.mean()) / 2.0).item())
            blh_values.append(blh_h)

        # Mean PDE loss over 8 snapshots (B1) — I1: EMA normalisation
        if lambdas.pde > 0:
            raw_L_pde = L_pde_day / len(SNAPSHOT_HOURS)
            _pde_ema  = 0.99 * _pde_ema + 0.01 * float(raw_L_pde.detach())
            L_pde     = raw_L_pde / max(_pde_ema, 1e-6)
        else:
            raw_L_pde = L_pde_day / len(SNAPSHOT_HOURS) if L_pde_day is not None else torch.zeros(1, device=device)
            L_pde     = torch.zeros(1, device=device)

        # Daily-mean data loss (B3): compare mean(C_h) to Stage-1 daily mean
        L_data = torch.zeros(1, device=device)
        if lambdas.data > 0 and len(C_hourly) > 0:
            # C_daily_pred: (N_pixels, 1) — mean over 8 hourly evaluations
            C_daily_pred = torch.stack(C_hourly, dim=0).mean(dim=0)
            L_data = data_fidelity_loss(C_daily_pred.squeeze(), C_target_s1, w_s1)

        # BC loss (uses DirichletBC at domain boundary)
        L_bc = bc_handler.compute_bc_loss(model, str(date_today), device) if lambdas.bc > 0 else torch.zeros(1, device=device)

        # Physics constraints (K bounds, C positivity, S positivity)
        L_phys = torch.zeros(1, device=device)
        if lambdas.phys > 0:
            try:
                blh_phys = torch.full(
                    (len(xy_int_np), 1), blh_norm, dtype=torch.float32, device=device
                )
                t_phys_np = np.full((len(xy_int_np), 1), 0.5, dtype=np.float32)
                xyt_phys  = torch.tensor(
                    np.hstack([xy_int_np, t_phys_np]),
                    dtype=torch.float32, device=device
                )
                with torch.no_grad():
                    C_int, (Kx_p, Ky_p, S_p) = model(xyt_phys, blh=blh_phys)
                c_losses = compute_all_constraints(C_int, Kx_p, Ky_p, S_p, c1_mean)
                L_phys   = c_losses["total"]
            except Exception as e:
                log.debug(f"Physics constraint failed: {e}")

        # K–BLH correlation regulariser (B5)
        # Soft prior: domain-mean K should correlate positively with BLH across
        # the 8 intra-day snapshots. With daily-mean ERA5 (blh_values all equal),
        # variance is zero — regulariser is skipped to avoid NaN.
        L_kblh = torch.zeros(1, device=device)
        blh_arr = np.array(blh_values, dtype=np.float32)
        if blh_arr.std() > 1e-6 and len(k_means) >= 2:
            blh_t = torch.tensor(blh_arr, dtype=torch.float32, device=device)
            # Recompute K with gradients for a differentiable regulariser
            k_means_grad = []
            for h_idx, h in enumerate(SNAPSHOT_HOURS):
                t_norm_h  = h / 24.0
                t_snap_np = np.full((len(xy_int_np), 1), t_norm_h, dtype=np.float32)
                xyt_h     = torch.tensor(
                    np.hstack([xy_int_np, t_snap_np]),
                    dtype=torch.float32, device=device
                )
                blh_h_t = torch.full(
                    (len(xy_int_np), 1), blh_arr[h_idx], dtype=torch.float32, device=device
                )
                _, (Kx_g, Ky_g, _) = model(xyt_h, blh=blh_h_t)
                k_means_grad.append((Kx_g.mean() + Ky_g.mean()) / 2.0)
            k_t   = torch.stack(k_means_grad)
            r_kblh = _pearson_corr(blh_t, k_t)
            # v3: use curriculum kblh weight; v2: use constant LAMBDA_KBLH
            lam_kblh = getattr(lambdas, 'kblh', LAMBDA_KBLH)
            L_kblh = lam_kblh * (1.0 - r_kblh) ** 2

        L_total = total_loss(L_pde, L_data, L_bc, L_phys,
                             lambdas.pde, lambdas.data, lambdas.bc, lambdas.phys)
        L_total = L_total + L_kblh

        # v4: KOALA mean-anchor loss — pulls domain-mean toward 24.5225 µg/m³
        L_mean_anchor = torch.zeros(1, device=device)
        w_anchor = getattr(lambdas, 'mean_anchor', 0.0)
        if use_v4 and w_anchor > 0 and len(C_hourly) > 0:
            from config import KOALA_PM25_ANCHOR
            C_daily_mean = torch.stack(C_hourly).mean()
            L_mean_anchor = ((C_daily_mean - KOALA_PM25_ANCHOR) ** 2) / (KOALA_PM25_ANCHOR ** 2)
            L_total = L_total + w_anchor * L_mean_anchor

        L_total.backward()
        # max_norm=5.0 (S2 fix: was 10.0 — Kaggle kernels use 5.0; tighter clip for stability)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        optimizer.step()
        if use_v4:
            scheduler_opt.step(epoch)   # CosineAnnealingWarmRestarts takes epoch as arg
        else:
            scheduler_opt.step()

        tracker.record(
            epoch,
            float(L_pde), float(L_data), float(L_bc), float(L_phys), float(L_total), current_lr
        )
        tracker.log_epoch(epoch, every=50)

        # ── W&B per-epoch logging ──────────────────────────────────────────
        if wandb_run is not None:
            wandb_run.log({
                "train/L_total":        float(L_total),
                "train/L_pde":          float(L_pde),
                "train/L_data":         float(L_data),
                "train/L_bc":           float(L_bc),
                "train/L_phys":         float(L_phys),
                "train/L_kblh":         float(L_kblh),
                "train/L_mean_anchor":  float(L_mean_anchor),
                "train/blh_m":          blh_m,
                "train/lr":             current_lr,
                "train/lambda_pde":     lambdas.pde,
                "train/lambda_data":    lambdas.data,
                "train/lambda_bc":      lambdas.bc,
                "epoch":                epoch,
            }, step=epoch)

        # Checkpoint
        if epoch % save_every == 0 or epoch == n_epochs - 1:
            ckpt = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "loss": float(L_total),
            }
            torch.save(ckpt, CHECKPOINT_DIR / f"kandy_pinn_epoch{epoch:04d}.pt")
            log.info(f"Checkpoint saved (epoch {epoch})")

    log.info("═══ PINN TRAINING COMPLETE ═══")
    return tracker.history


def main():
    parser = argparse.ArgumentParser(description="Stage 3 Kandy PINN training")
    parser.add_argument("--init",     choices=["A", "B", "B3", "C"], default=None,
                        help="Init strategy: A=frozen, B=warm-start v8, B3=warm-start v13, C=cold. "
                             "Auto from transfer_decision.json if omitted")
    parser.add_argument("--model",    choices=["v4", "v3", "v2"], default=DEFAULT_MODEL_VERSION,
                        help="Model version: v4=FourierPINNV3+deviation-from-prior+KOALA anchor (default), "
                             "v3=FourierPINNV3 data-dominant, v2=legacy FourierPINN")
    parser.add_argument("--epochs",   type=int, default=PINN_EPOCHS)
    parser.add_argument("--lr",       type=float, default=PINN_LR)
    parser.add_argument("--no-rar",   action="store_true", help="Disable RAR collocation")
    parser.add_argument("--profile",  action="store_true", help="Quick 20-epoch smoke-test")
    parser.add_argument("--wandb",    action="store_true", help="Enable W&B experiment tracking")
    parser.add_argument("--no-wandb", action="store_true", help="Disable W&B even if WANDB_API_KEY is set")
    parser.add_argument("--steady",   action="store_true",
                        help="Use quasi-steady-state PDE (no ∂C/∂t). Default: time-dependent TD-PDE.")
    args = parser.parse_args()

    device = _get_device()
    log.info(f"Device: {device}")

    # Determine initialisation
    if args.init:
        init_map = {
            "A":  "use_pretrained_frozen",
            "B":  "use_pretrained_unfrozen",
            "B3": "use_pretrained_v13",
            "C":  "random_init",
        }
        init_mode = init_map[args.init]
    else:
        decision   = load_init_decision()
        init_mode  = decision.get("stage3_init", "random_init")
    log.info(f"Initialisation mode: {init_mode}, model version: {args.model}")

    model, init_mode = build_model(init_mode, device, model_version=args.model)

    stage1_df = load_stage1_data()

    n_epochs = 20 if args.profile else args.epochs

    # W&B: enabled if --wandb flag given, OR if WANDB_API_KEY is set and --no-wandb not given
    use_wandb = (args.wandb or bool(os.environ.get("WANDB_API_KEY"))) and not args.no_wandb
    wandb_run = None
    if use_wandb:
        wandb_run = _setup_wandb({
            "stage":          "stage3_kandy_pinn",
            "model_version":  args.model,
            "init_mode":      init_mode,
            "n_epochs":       n_epochs,
            "lr":             args.lr,
            "use_rar":        not args.no_rar,
            "rar_start":      200,
            "profile_run":    args.profile,
            "snapshot_hours": SNAPSHOT_HOURS,
            "lambda_kblh":    LAMBDA_KBLH,
        })

    history  = train_pinn(
        model, stage1_df, n_epochs, args.lr, device,
        use_rar=not args.no_rar,
        wandb_run=wandb_run,
        model_version=args.model,
        steady=args.steady,
    )

    import pandas as pd
    hist_df = pd.DataFrame(history)
    hist_df.to_csv(CHECKPOINT_DIR / "training_losses.csv", index=False)
    log.info(f"Loss history saved → {CHECKPOINT_DIR / 'training_losses.csv'}")

    if wandb_run is not None:
        try:
            wandb_run.finish()
        except Exception:
            pass
    log.info("Stage 3 PINN training complete.")


if __name__ == "__main__":
    main()
