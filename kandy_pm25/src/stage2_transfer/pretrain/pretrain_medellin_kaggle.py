#!/usr/bin/env python3
"""
pretrain_medellin_kaggle.py  —  v2
Stage 2 Physics-Dominant Pre-training on Medellín Data (Kaggle GPU version).

Architecture v2 changes vs v1:
  - DiffusionSubNet: separate 3-layer MLP for Kx/Ky taking [x,y,t,blh_norm,elev_norm]
  - SourceSubNet   : separate 4-layer MLP for S with cyclic hour/weekday encoding
  - Loss schedule  : λ_physics=0.7, λ_data=0.2, λ_bc=0.1, λ_k_bound=0.05
  - BLH extracted from ERA5 and passed through pde_residual to model.forward()
  - TrainingLogger appended at end of each run

Self-contained — imports only torch, numpy, pandas, pathlib.
Run on Kaggle with GPU accelerator enabled (T4 or P100).

Kaggle setup:
  1. Attach dataset 'kandy-stage2-data' (contains medellin_stage2_perstation.parquet)
  2. Enable GPU accelerator in notebook settings
  3. Run as script (not interactive)

Input  : /kaggle/input/<dataset-slug>/medellin_stage2_perstation.parquet
         Falls back to medellin_stage2_training.parquet if per-station not found.
Output :
  /kaggle/working/checkpoints/epoch_XXXX.pt   (every SAVE_EVERY epochs)
  /kaggle/working/pretrained_physics_backbone.pt   (final backbone)
  /kaggle/working/pretrain_losses.csv

Architecture matches src/stage3_pinn/models/fourier_pinn.py v2 exactly.
Physics matches src/stage3_pinn/physics/advection_diffusion.py exactly.
"""

import logging
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("pretrain_medellin")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION  (v2)
# ═══════════════════════════════════════════════════════════════════════════

N_EPOCHS        = 500
LR              = 5e-4
N_COLLOCATION   = 8000      # Interior PDE collocation points per epoch
N_BOUNDARY      = 1500      # Boundary condition points per epoch
N_DATA          = 8000      # Data fidelity points per epoch (sampled from 89k station-hour pairs)
SAVE_EVERY      = 50        # Save checkpoint at epochs 50, 100, 150, …
WARMUP_EPOCHS   = 100       # Steady-state PDE warm-up (no ∂C/∂t)
RANDOM_SEED     = 42

# Architecture — matches config.py
FOURIER_M      = 256
FOURIER_SIGMA  = 1.0
HIDDEN_UNITS   = 128        # C_medium ablation winner (2026-03-01)
HIDDEN_LAYERS  = 6
K_MIN          = 1.0        # m²/s
K_MAX          = 100.0      # m²/s
DIFF_HIDDEN    = 32         # DiffusionSubNet hidden size
SRC_HIDDEN     = 48         # SourceSubNet hidden size
BLH_NORM_SCALE = 2000.0     # m — BLH normalisation denominator

# Physics constants (fixed from literature — do NOT learn)
LAMBDA_WET  = 4.5e-4    # Below-cloud scavenging [s⁻¹·(mm/h)⁻¹]
LAMBDA_DRY  = 1.0e-4    # λ_dry = v_d / H_mix = 0.003 / 30 [s⁻¹]

# Loss schedule v2 (from config.py LOSS_SCHEDULE["medellin_pretrain"])
LOSS_SCHEDULE = {
    "lambda_physics": 0.7,   # reduced from 0.9 — avoids trivial collapse
    "lambda_data":    0.2,   # increased from 0.1 — data constrains spatial field
    "lambda_bc":      0.1,
    "lambda_k_bound": 0.05,  # DiffusionSubNet soft bound penalty
}
LAMBDA_PHYSICS  = LOSS_SCHEDULE["lambda_physics"]
LAMBDA_DATA     = LOSS_SCHEDULE["lambda_data"]
LAMBDA_BC       = LOSS_SCHEDULE["lambda_bc"]
LAMBDA_K_BOUND  = LOSS_SCHEDULE["lambda_k_bound"]

# Medellín 15×15 km PINN sub-domain (matches KANDY_PINN_BBOX scale)
MEDELLIN_PINN_BBOX = {
    "lat_min": 6.1635,
    "lat_max": 6.2986,
    "lon_min": -75.6426,
    "lon_max": -75.5066,
}

# Kaggle I/O paths
DATA_DIR = Path("/kaggle/input")
OUT_DIR  = Path("/kaggle/working")

# Architecture version tag saved in checkpoints
ARCH_VERSION = "v2_C_medium_perstation"   # per-station L_data, weighted by n_obs

# ── W&B configuration ────────────────────────────────────────────────────────
WANDB_PROJECT      = "kandy-pinn"
WANDB_ENTITY       = None        # set to your W&B username/team, or leave None
WANDB_ENABLED      = True        # set False to disable entirely
SPATIAL_LOG_EVERY  = 50          # log spatial field snapshots every N epochs
SPATIAL_GRID_N     = 20          # grid resolution for spatial snapshots (20×20)

# ═══════════════════════════════════════════════════════════════════════════
# W&B HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _setup_wandb(run_config: dict):
    """
    Initialise a W&B run.

    Auth priority:
      1. Kaggle Secrets key named "wandb"
      2. WANDB_API_KEY environment variable
      3. wandb.login() interactive (local only)

    Returns a wandb.Run or None if unavailable/disabled.
    """
    if not WANDB_ENABLED:
        return None
    try:
        import wandb
    except ImportError:
        log.warning("wandb not installed — skipping experiment tracking.")
        return None

    api_key = None
    try:
        from kaggle_secrets import UserSecretsClient
        api_key = UserSecretsClient().get_secret("wandb")
        log.info("W&B API key loaded from Kaggle Secrets.")
    except Exception:
        api_key = os.environ.get("WANDB_API_KEY")
        if api_key:
            log.info("W&B API key loaded from WANDB_API_KEY env var.")

    try:
        if api_key:
            wandb.login(key=api_key, relogin=True)
        run = wandb.init(
            project=WANDB_PROJECT,
            entity=WANDB_ENTITY,
            name=f"medellin-pretrain-{datetime.now().strftime('%Y%m%d-%H%M')}",
            config=run_config,
            tags=["stage2", "medellin", "pretrain", ARCH_VERSION],
        )
        log.info(f"W&B run: {run.url}")
        return run
    except Exception as exc:
        log.warning(f"W&B init failed ({exc}) — continuing without tracking.")
        return None


def _log_spatial_snapshot(model, device, epoch: int, wandb_run, t_norm: float = 0.5):
    """
    Sample a SPATIAL_GRID_N × SPATIAL_GRID_N grid, run inference, log C/Kx/Ky
    heatmaps + scalar statistics to W&B.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        n = SPATIAL_GRID_N
        xs = np.linspace(-1.0, 1.0, n, dtype=np.float32)
        ys = np.linspace(-1.0, 1.0, n, dtype=np.float32)
        xg, yg = np.meshgrid(xs, ys)  # (n, n)
        tg = np.full_like(xg, t_norm)
        xyt = np.stack([xg.ravel(), yg.ravel(), tg.ravel()], axis=1)

        xyt_t = torch.tensor(xyt, dtype=torch.float32, device=device)
        model.eval()
        with torch.no_grad():
            C, (Kx, Ky, _) = model(xyt_t)
        model.train()

        C_grid  = C.cpu().numpy().reshape(n, n)
        Kx_grid = Kx.cpu().numpy().reshape(n, n)
        Ky_grid = Ky.cpu().numpy().reshape(n, n)

        # Scalar diagnostics
        metrics = {
            "spatial/std_C":    float(C_grid.std()),
            "spatial/mean_C":   float(C_grid.mean()),
            "spatial/mean_Kx":  float(Kx_grid.mean()),
            "spatial/mean_Ky":  float(Ky_grid.mean()),
            "spatial/std_Kx":   float(Kx_grid.std()),
            "epoch":            epoch,
        }

        # Heatmap figures
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
        for ax, grid, title, vmax in zip(
            axes,
            [C_grid, Kx_grid, Ky_grid],
            ["C (µg/m³)", "Kx (m²/s)", "Ky (m²/s)"],
            [None, K_MAX, K_MAX],
        ):
            im = ax.imshow(
                grid, origin="lower", aspect="equal",
                vmin=0, vmax=vmax, cmap="plasma",
            )
            plt.colorbar(im, ax=ax, fraction=0.046)
            ax.set_title(f"{title}  [epoch {epoch}]", fontsize=9)
            ax.axis("off")
        plt.tight_layout()

        import wandb
        metrics["spatial/fields"] = wandb.Image(fig)
        plt.close(fig)

        wandb_run.log(metrics, step=epoch)
    except Exception as exc:
        log.debug(f"Spatial snapshot failed at epoch {epoch}: {exc}")


# ═══════════════════════════════════════════════════════════════════════════
# PATH RESOLUTION
# ═══════════════════════════════════════════════════════════════════════════

def find_parquet(data_dir: Path, filename: str) -> Path:
    """Search recursively under data_dir, fall back to local stage2 dir."""
    if data_dir.exists():
        matches = sorted(data_dir.rglob(filename))
        if matches:
            return matches[0]
    try:
        local = Path(__file__).parents[3] / "data" / "processed" / "stage2" / filename
        if local.exists():
            log.info(f"Using local path: {local}")
            return local
    except IndexError:
        pass
    raise FileNotFoundError(
        f"'{filename}' not found under {data_dir}.\n"
        "On Kaggle: attach the 'kandy-stage2-data' dataset.\n"
        "Locally: ensure data/processed/stage2/{filename} exists."
    )


def find_medellin_parquet(data_dir: Path) -> tuple[Path, bool]:
    """
    Locate Medellín training parquet. Prefer per-station over city-averaged.
    Returns (path, is_per_station).
    """
    for fname, per_station in [
        ("medellin_stage2_perstation.parquet", True),
        ("medellin_stage2_training.parquet",   False),
    ]:
        try:
            p = find_parquet(data_dir, fname)
            log.info(f"Medellín data: {fname}  (per_station={per_station})")
            return p, per_station
        except FileNotFoundError:
            continue
    raise FileNotFoundError(
        "Neither medellin_stage2_perstation.parquet nor medellin_stage2_training.parquet found.\n"
        "On Kaggle: attach 'kandy-stage2-data'. Locally: run build_medellin_perstation.py."
    )


# ═══════════════════════════════════════════════════════════════════════════
# MODEL — FourierPINN v2
# Self-contained copy of src/stage3_pinn/models/fourier_pinn.py v2.
# Keep in sync if the original changes.
# ═══════════════════════════════════════════════════════════════════════════

class FourierEmbedding:
    """Random Fourier feature embedding (Tancik et al. 2020). Fixed B matrix."""
    def __init__(self, in_dim: int = 3, m: int = FOURIER_M,
                 sigma: float = FOURIER_SIGMA, seed: int = RANDOM_SEED):
        rng = np.random.default_rng(seed)
        self.B = rng.normal(0, sigma, size=(m, in_dim)).astype(np.float32)
        self.out_dim = 2 * m

    def embed(self, x: torch.Tensor) -> torch.Tensor:
        B = torch.tensor(self.B, dtype=x.dtype, device=x.device)
        proj = 2.0 * math.pi * x @ B.T
        return torch.cat([torch.sin(proj), torch.cos(proj)], dim=-1)


def _build_residual_mlp(in_dim: int, hidden: int, n_layers: int) -> nn.Module:
    """Tanh MLP with skip connections every 2 layers. Output dim = hidden."""
    class ResidualMLP(nn.Module):
        def __init__(self):
            super().__init__()
            self.input_proj = nn.Linear(in_dim, hidden)
            self.layers = nn.ModuleList(
                [nn.Linear(hidden, hidden) for _ in range(n_layers)]
            )
            self.act = nn.Tanh()

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            h = self.act(self.input_proj(x))
            for i, layer in enumerate(self.layers):
                h_new = self.act(layer(h))
                h = h + h_new if (i % 2 == 1) else h_new
            return h

    return ResidualMLP()


class DiffusionSubNet(nn.Module):
    """
    Terrain+BLH-aware 3-layer MLP for anisotropic diffusivity [Kx, Ky].
    Inputs : [x_norm, y_norm, t_norm, blh_norm, elev_norm]  (5 features)
    Arch   : Linear(5→32) → Tanh → Linear(32→32) → Tanh → Linear(32→2)
    Params : 192 + 1056 + 66 = 1,314
    Init   : Xavier normal; final bias → K_initial ≈ 10 m²/s
    """
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(5, DIFF_HIDDEN)
        self.fc2 = nn.Linear(DIFF_HIDDEN, DIFF_HIDDEN)
        self.fc3 = nn.Linear(DIFF_HIDDEN, 2)
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.zeros_(m.bias)
        # Init final bias so K ≈ 10 m²/s: softplus(b) + K_MIN = 10
        bias_init = math.log(math.exp(10.0 - K_MIN) - 1.0)
        nn.init.constant_(self.fc3.bias, bias_init)

    def forward(self, x_n, y_n, t_n, blh_n, elev_n):
        inp = torch.cat([x_n, y_n, t_n, blh_n, elev_n], dim=1)
        h = torch.tanh(self.fc1(inp))
        h = torch.tanh(self.fc2(h))
        out = self.fc3(h)
        Kx = F.softplus(out[:, 0:1]) + K_MIN
        Ky = F.softplus(out[:, 1:2]) + K_MIN
        return Kx, Ky

    def bound_penalty(self, Kx, Ky):
        """Soft squared penalty for K outside [K_MIN, K_MAX]."""
        low  = F.relu(K_MIN - Kx) ** 2 + F.relu(K_MIN - Ky) ** 2
        high = F.relu(Kx - K_MAX) ** 2 + F.relu(Ky - K_MAX) ** 2
        return torch.mean(low + high)


class SourceSubNet(nn.Module):
    """
    Cyclic-time source term MLP.
    Inputs : [x_norm, y_norm, sin(2π·h/24), cos(2π·h/24), sin(2π·d/7), cos(2π·d/7)]
    Arch   : Linear(6→48) → Tanh ×3 → Linear(48→1) → Softplus
    Params : 336 + 2352 + 2352 + 49 = 5,089
    """
    def __init__(self, t_max: float = 8760.0):
        super().__init__()
        self.fc1 = nn.Linear(6, SRC_HIDDEN)
        self.fc2 = nn.Linear(SRC_HIDDEN, SRC_HIDDEN)
        self.fc3 = nn.Linear(SRC_HIDDEN, SRC_HIDDEN)
        self.fc4 = nn.Linear(SRC_HIDDEN, 1)
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.zeros_(m.bias)
        self.register_buffer("t_max_hours", torch.tensor(t_max, dtype=torch.float32))

    def forward(self, x_n, y_n, t_n):
        t_h   = t_n * self.t_max_hours
        h_day = t_h % 24.0
        d_wk  = (t_h / 24.0) % 7.0
        pi2   = 2.0 * math.pi
        sin_h = torch.sin(pi2 * h_day / 24.0)
        cos_h = torch.cos(pi2 * h_day / 24.0)
        sin_d = torch.sin(pi2 * d_wk  / 7.0)
        cos_d = torch.cos(pi2 * d_wk  / 7.0)
        inp = torch.cat([x_n, y_n, sin_h, cos_h, sin_d, cos_d], dim=1)
        h = torch.tanh(self.fc1(inp))
        h = torch.tanh(self.fc2(h))
        h = torch.tanh(self.fc3(h))
        return F.softplus(self.fc4(h))


class FourierPINNModule(nn.Module):
    """
    FourierPINN v2 — matches src/stage3_pinn/models/fourier_pinn.py.

    forward(xyt, blh=None, elev=None) → C (N,1), (Kx (N,1), Ky (N,1), S (N,1))
    All outputs non-negative. blh/elev default to 0.5 if not provided.
    """

    def __init__(self, t_max: float = 8760.0):
        super().__init__()
        self.embedding = FourierEmbedding()
        embed_dim = self.embedding.out_dim          # 2 × FOURIER_M = 512
        self.net              = _build_residual_mlp(embed_dim, HIDDEN_UNITS, HIDDEN_LAYERS)
        self.head_C           = nn.Linear(HIDDEN_UNITS, 1)
        self.diffusion_subnet = DiffusionSubNet()
        self.source_subnet    = SourceSubNet(t_max=t_max)
        # Xavier init for head_C
        nn.init.xavier_uniform_(self.head_C.weight)
        nn.init.zeros_(self.head_C.bias)

    def forward(self, xyt: torch.Tensor,
                blh: torch.Tensor = None,
                elev: torch.Tensor = None):
        N, device = xyt.shape[0], xyt.device
        if blh  is None: blh  = torch.full((N, 1), 0.5, dtype=xyt.dtype, device=device)
        if elev is None: elev = torch.full((N, 1), 0.5, dtype=xyt.dtype, device=device)

        emb  = self.embedding.embed(xyt)
        feat = self.net(emb)
        C    = F.softplus(self.head_C(feat))

        x_n, y_n, t_n = xyt[:, 0:1], xyt[:, 1:2], xyt[:, 2:3]
        Kx, Ky = self.diffusion_subnet(x_n, y_n, t_n, blh, elev)
        S      = self.source_subnet(x_n, y_n, t_n)
        return C, (Kx, Ky, S)

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def parameter_breakdown(self) -> dict:
        def _c(m): return sum(p.numel() for p in m.parameters() if p.requires_grad)
        return {
            "net (main trunk)": _c(self.net),
            "head_C":           _c(self.head_C),
            "diffusion_subnet": _c(self.diffusion_subnet),
            "source_subnet":    _c(self.source_subnet),
            "total":            self.count_parameters(),
        }


# ═══════════════════════════════════════════════════════════════════════════
# PHYSICS — PDE residual  (v2: accepts blh/elev, passes to model.forward)
# ═══════════════════════════════════════════════════════════════════════════

def pde_residual(
    model:   nn.Module,
    xyt:     torch.Tensor,   # (N, 3) normalised [x, y, t] — must have requires_grad
    wind_u:  torch.Tensor,   # (N, 1) zonal wind [m/s]
    wind_v:  torch.Tensor,   # (N, 1) meridional wind [m/s]
    precip:  torch.Tensor,   # (N, 1) precipitation [mm/h]
    blh:     torch.Tensor = None,   # (N, 1) normalised BLH (blh_m / 2000.0)
    elev:    torch.Tensor = None,   # (N, 1) normalised elevation; None → 0.5
    steady:  bool = False,
) -> torch.Tensor:
    """
    Anisotropic advection-diffusion PDE residual (§3.4):
        R = ∂C/∂t + u·∂C/∂x + v·∂C/∂y
              − ∂/∂x(Kx·∂C/∂x) − ∂/∂y(Ky·∂C/∂y)
              − S + (λ_dry + Λ·P)·C

    steady=True zeros ∂C/∂t for the warm-up phase.
    blh and elev are passed to model.forward() for DiffusionSubNet.
    """
    if steady:
        xyt = xyt.detach().clone()
        xyt[:, 2] = 0.0
    xyt = xyt.requires_grad_(True)

    C, (Kx, Ky, S) = model(xyt, blh=blh, elev=elev)
    go = torch.ones_like(C)

    # First derivatives of C
    grads = torch.autograd.grad(C, xyt, grad_outputs=go, create_graph=True)[0]
    dC_dx, dC_dy, dC_dt = grads[:, 0:1], grads[:, 1:2], grads[:, 2:3]

    # Diffusive flux divergence
    flux_x = Kx * dC_dx
    flux_y = Ky * dC_dy
    d_flux_x = torch.autograd.grad(
        flux_x, xyt, grad_outputs=go, create_graph=True
    )[0][:, 0:1]
    d_flux_y = torch.autograd.grad(
        flux_y, xyt, grad_outputs=go, create_graph=True
    )[0][:, 1:2]

    removal = LAMBDA_DRY + LAMBDA_WET * precip

    R = dC_dt + wind_u * dC_dx + wind_v * dC_dy \
        - d_flux_x - d_flux_y \
        - S + removal * C
    return R


# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════

def load_medellin_data(data_dir: Path) -> tuple:
    """
    Load Medellín training data (per-station preferred, city-averaged fallback).

    Returns
    -------
    df_era5   : pd.DataFrame — time-unique ERA5 rows, columns include u10, v10,
                blh, tp_mmh, pm25 (city-mean per timestamp). Used for PDE/BC loss.
    t_hours   : np.ndarray float32 — elapsed hours from t_origin for each ERA5 row.
    t_max     : float — last t_hours value.
    sta_data  : dict | None — per-station arrays for L_data; None if city-averaged.
                Keys: x_norm, y_norm, t_hours (per row), pm25, weight, n_total.
    """
    path, per_station = find_medellin_parquet(data_dir)
    df = pd.read_parquet(path)
    log.info(f"Loaded Medellín data: {df.shape} from {path.name}")

    if per_station:
        # ── Per-station parquet ────────────────────────────────────────────
        # datetime_utc is a column (not index), multiple rows per timestamp
        df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True)

        # Time-unique ERA5 (deduplicate on datetime_utc, keep first row's ERA5 values)
        era5_cols = ["datetime_utc", "u10", "v10", "blh", "t2m", "tp", "sp"]
        df_era5 = (
            df[era5_cols]
            .drop_duplicates("datetime_utc")
            .sort_values("datetime_utc")
            .reset_index(drop=True)
        )
        # tp in perstation parquet is already mm/h (converted in build_medellin_perstation.py)
        df_era5["tp_mmh"] = df_era5["tp"].clip(lower=0.0)

        # Merge city-mean PM2.5 per timestamp for BC target
        pm25_mean = df.groupby("datetime_utc")["pm25"].mean().rename("pm25")
        df_era5 = df_era5.merge(pm25_mean, on="datetime_utc", how="left")

        # t_hours array (one entry per unique ERA5 row)
        t_origin = df_era5["datetime_utc"].iloc[0]
        t_hours  = ((df_era5["datetime_utc"] - t_origin)
                    .dt.total_seconds() / 3600).astype(np.float32).values
        t_max    = float(t_hours[-1])

        # Per-station arrays for L_data
        t_hours_sta = ((df["datetime_utc"] - t_origin)
                       .dt.total_seconds() / 3600).astype(np.float32).values
        n_obs_max   = float(df["n_obs"].max()) if "n_obs" in df.columns else 1.0
        sta_data = {
            "x_norm":  df["x_norm"].astype(np.float32).values,
            "y_norm":  df["y_norm"].astype(np.float32).values,
            "t_hours": t_hours_sta,
            "pm25":    df["pm25"].astype(np.float32).values,
            "weight":  (df["n_obs"].astype(np.float32).values / n_obs_max
                        if "n_obs" in df.columns
                        else np.ones(len(df), dtype=np.float32)),
            "n_total": len(df),
        }

        log.info(f"  ERA5 rows : {len(df_era5):,} unique hours")
        log.info(f"  Period    : {df_era5['datetime_utc'].iloc[0]} → {df_era5['datetime_utc'].iloc[-1]}")
        log.info(f"  L_data pts: {sta_data['n_total']:,}  (11 stations × ~8k hours)")
        log.info(f"  PM2.5     : mean={sta_data['pm25'].mean():.1f}  std={sta_data['pm25'].std():.1f} µg/m³")
        log.info(f"  BLH       : mean={df_era5['blh'].mean():.0f} m")
        log.info(f"  Precip    : mean={df_era5['tp_mmh'].mean():.4f} mm/h")

    else:
        # ── City-averaged parquet (backward compat) ────────────────────────
        t_origin = df.index[0]
        t_hours  = ((df.index - t_origin).total_seconds() / 3600).astype(np.float32).values
        t_max    = float(t_hours[-1])
        df["tp_mmh"] = (df["tp"] * 1000.0).clip(lower=0.0)
        df_era5 = df.copy()
        df_era5["datetime_utc"] = df_era5.index
        df_era5 = df_era5.reset_index(drop=True)
        sta_data = None

        log.info(f"  Period  : {df.index[0]} → {df.index[-1]}  ({len(df)} hours)")
        log.info(f"  PM2.5   : mean={df['pm25'].mean():.1f}  std={df['pm25'].std():.1f} µg/m³")
        log.info(f"  BLH     : mean={df['blh'].mean():.0f} m")
        log.info(f"  Precip  : mean={df['tp_mmh'].mean():.4f} mm/h")
        log.warning("  Using city-averaged parquet — spatial K(x,y) learning will be limited.")

    return df_era5, t_hours, t_max, sta_data


# ═══════════════════════════════════════════════════════════════════════════
# COORDINATE NORMALISATION
# ═══════════════════════════════════════════════════════════════════════════

_LON_CENTER = (MEDELLIN_PINN_BBOX["lon_min"] + MEDELLIN_PINN_BBOX["lon_max"]) / 2.0
_LAT_CENTER = (MEDELLIN_PINN_BBOX["lat_min"] + MEDELLIN_PINN_BBOX["lat_max"]) / 2.0
_LON_HALF   = (MEDELLIN_PINN_BBOX["lon_max"] - MEDELLIN_PINN_BBOX["lon_min"]) / 2.0
_LAT_HALF   = (MEDELLIN_PINN_BBOX["lat_max"] - MEDELLIN_PINN_BBOX["lat_min"]) / 2.0


def norm_lon(lon):  return ((lon - _LON_CENTER) / _LON_HALF).astype(np.float32)
def norm_lat(lat):  return ((lat - _LAT_CENTER) / _LAT_HALF).astype(np.float32)
def norm_t(t_h, t_max): return (t_h / t_max).astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════
# COLLOCATION SAMPLING
# ═══════════════════════════════════════════════════════════════════════════

def sample_collocation(rng, n_interior, n_boundary):
    """Sample interior (uniform) and boundary (domain edges) collocation points."""
    x_int = rng.uniform(-1.0, 1.0, n_interior).astype(np.float32)
    y_int = rng.uniform(-1.0, 1.0, n_interior).astype(np.float32)
    t_int = rng.uniform( 0.0, 1.0, n_interior).astype(np.float32)

    n_side = n_boundary // 4
    vals   = np.linspace(-1.0, 1.0, n_side, dtype=np.float32)
    t_bnd  = rng.uniform(0.0, 1.0, n_side * 4).astype(np.float32)
    x_bnd  = np.concatenate([vals, vals,
                              np.full(n_side, -1.0, dtype=np.float32),
                              np.full(n_side,  1.0, dtype=np.float32)])
    y_bnd  = np.concatenate([np.full(n_side, -1.0, dtype=np.float32),
                              np.full(n_side,  1.0, dtype=np.float32),
                              vals, vals])
    return np.column_stack([x_int, y_int, t_int]), np.column_stack([x_bnd, y_bnd, t_bnd])


# ═══════════════════════════════════════════════════════════════════════════
# ERA5 INTERPOLATION  (nearest-hour lookup)
# ═══════════════════════════════════════════════════════════════════════════

def interp_era5(t_norm, t_max, t_hours, df, columns):
    """Nearest-hour lookup of ERA5 fields. Returns float32 (N, len(columns))."""
    t_phys   = np.clip(t_norm * t_max, 0.0, t_max)
    idx      = np.searchsorted(t_hours, t_phys)
    idx      = np.clip(idx, 0, len(t_hours) - 1)
    idx_left = np.maximum(idx - 1, 0)
    use_left = np.abs(t_hours[idx_left] - t_phys) < np.abs(t_hours[idx] - t_phys)
    idx      = np.where(use_left, idx_left, idx)
    return df[columns].values[idx].astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════
# LOSS FUNCTIONS  (v2: loss_pde extracts BLH and passes to pde_residual)
# ═══════════════════════════════════════════════════════════════════════════

def loss_pde(model, xyt_int, t_max, t_hours, df_era5, device, steady):
    """Physics loss: mean squared PDE residual at interior collocation points.
    v2: extracts BLH from ERA5 alongside wind; passes to pde_residual/model.forward.
    """
    t_norm = xyt_int[:, 2]
    era5   = interp_era5(t_norm, t_max, t_hours, df_era5, ["u10", "v10", "tp_mmh", "blh"])
    wind_u = torch.tensor(era5[:, 0:1], device=device)
    wind_v = torch.tensor(era5[:, 1:2], device=device)
    precip = torch.tensor(era5[:, 2:3], device=device)
    blh    = torch.tensor(era5[:, 3:4] / BLH_NORM_SCALE, device=device)  # normalise
    xyt_t  = torch.tensor(xyt_int, dtype=torch.float32, device=device)
    R = pde_residual(model, xyt_t, wind_u, wind_v, precip, blh=blh, elev=None, steady=steady)
    return torch.mean(R ** 2)


def loss_data(model, rng, n_pts, t_max, t_hours, df_era5, device, sta_data=None):
    """
    Data fidelity loss at observed PM2.5 locations.

    Per-station mode (preferred):
      Sample n_pts rows from sta_data (each row = one station × one hour).
      Evaluate C at exact station (x_norm, y_norm, t_norm).
      Weight MSE by n_obs / n_obs_max (observation quality).
      → Provides spatial constraint: C(x_i, y_i, t_j) ≈ pm25_ij

    City-averaged mode (fallback):
      Sample random (x, y) from the domain; compare to city-mean PM2.5(t).
      → Only a magnitude constraint (no spatial K learning signal).
    """
    if sta_data is not None:
        # ── Per-station: spatial constraint at actual monitoring locations ──
        idx         = rng.integers(0, sta_data["n_total"], size=n_pts)
        x_data      = sta_data["x_norm"][idx]
        y_data      = sta_data["y_norm"][idx]
        t_norm_data = norm_t(sta_data["t_hours"][idx], t_max)
        pm25_vals   = sta_data["pm25"][idx]
        weights     = sta_data["weight"][idx]

        xyt_data = np.column_stack([x_data, y_data, t_norm_data])
        xyt_t    = torch.tensor(xyt_data, dtype=torch.float32, device=device)
        C, _     = model(xyt_t)

        pm25_obs = torch.tensor(pm25_vals.reshape(-1, 1), dtype=torch.float32, device=device)
        w_t      = torch.tensor(weights.reshape(-1, 1),   dtype=torch.float32, device=device)
        return torch.mean(w_t * (C - pm25_obs) ** 2)

    else:
        # ── City-averaged fallback: random spatial points ──────────────────
        row_idx     = rng.integers(0, len(df_era5), size=n_pts)
        t_norm_data = norm_t(t_hours[row_idx], t_max)
        x_data      = rng.uniform(-1.0, 1.0, n_pts).astype(np.float32)
        y_data      = rng.uniform(-1.0, 1.0, n_pts).astype(np.float32)
        xyt_data    = np.column_stack([x_data, y_data, t_norm_data])

        xyt_t    = torch.tensor(xyt_data, dtype=torch.float32, device=device)
        C, _     = model(xyt_t)
        pm25_obs = torch.tensor(
            df_era5["pm25"].values[row_idx].astype(np.float32).reshape(-1, 1),
            device=device,
        )
        return torch.mean((C - pm25_obs) ** 2)


def loss_bc(model, xyt_bnd, t_max, t_hours, df_era5, device):
    """Dirichlet BC loss: at domain boundary, C ≈ city-mean PM2.5(t).
    Uses df_era5["pm25"] which is the time-mean PM2.5 across all stations per hour.
    """
    t_norm  = xyt_bnd[:, 2]
    row_idx = np.clip(
        np.searchsorted(t_hours, t_norm * t_max), 0, len(df_era5) - 1
    ).astype(int)
    pm25_bc = df_era5["pm25"].values[row_idx].astype(np.float32).reshape(-1, 1)

    xyt_t    = torch.tensor(xyt_bnd, dtype=torch.float32, device=device)
    C_bnd, _ = model(xyt_t)
    target   = torch.tensor(pm25_bc, device=device)
    return torch.mean((C_bnd - target) ** 2)


# ═══════════════════════════════════════════════════════════════════════════
# CHECKPOINT SAVING
# ═══════════════════════════════════════════════════════════════════════════

def save_checkpoint(model, optimizer, scheduler, epoch, loss_history, out_dir, final=False):
    ckpt_dir = out_dir / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "epoch":                epoch,
        "model_state_dict":     model.state_dict(),
        "optimizer_state":      optimizer.state_dict(),
        "scheduler_state":      scheduler.state_dict(),
        "architecture_version": ARCH_VERSION,
        "upgrades": ["DiffusionSubNet_BLH_elev", "SourceSubNet_cyclic_time",
                     "loss_schedule_v2", "K_bound_penalty"],
        "loss_schedule":        LOSS_SCHEDULE,
        "training_domain":      "Medellin_PINN_bbox",
        "bbox":                 MEDELLIN_PINN_BBOX,
        "fourier_m":            FOURIER_M,
        "fourier_sigma":        FOURIER_SIGMA,
        "hidden_units":         HIDDEN_UNITS,
        "hidden_layers":        HIDDEN_LAYERS,
        "loss_tail":            loss_history[-min(10, len(loss_history)):],
    }

    path = ckpt_dir / f"epoch_{epoch:04d}.pt"
    torch.save(state, path)
    log.info(f"  ✔ Checkpoint → {path}")

    if final:
        final_path = out_dir / "pretrained_physics_backbone.pt"
        torch.save(state, final_path)
        log.info(f"  ✔ Final backbone → {final_path}")


# ═══════════════════════════════════════════════════════════════════════════
# TRAINING LOOP  (v2)
# ═══════════════════════════════════════════════════════════════════════════

def train(model, df_era5, t_hours, t_max, out_dir, device, sta_data=None, wandb_run=None):
    """
    Physics-dominant PINN pre-training on Medellín data (v2).

    Phase 1 (0–WARMUP_EPOCHS)  : steady-state PDE (no ∂C/∂t)
    Phase 2 (WARMUP_EPOCHS–end): full transient PDE

    Loss: L = λ_p·L_pde + λ_d·L_data + λ_bc·L_bc + λ_kb·L_k_bound

    Args:
        df_era5   : time-unique ERA5 DataFrame (for PDE/BC loss)
        sta_data  : per-station arrays for L_data (None → city-avg fallback)
        wandb_run : optional wandb.Run for experiment tracking
    """
    optimizer = optim.Adam(model.parameters(), lr=LR)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=N_EPOCHS, eta_min=1e-6)
    rng = np.random.default_rng(RANDOM_SEED)
    loss_history = []

    log.info("=" * 70)
    log.info(f" Medellín pre-training v2  |  N_epochs={N_EPOCHS}  lr={LR}")
    log.info(f" λ_physics={LAMBDA_PHYSICS}  λ_data={LAMBDA_DATA}"
             f"  λ_bc={LAMBDA_BC}  λ_k_bound={LAMBDA_K_BOUND}")
    log.info(f" Collocation: {N_COLLOCATION} interior + {N_BOUNDARY} boundary")
    log.info(f" Steady-state warm-up: epochs 0–{WARMUP_EPOCHS}")
    log.info(f" Architecture: {ARCH_VERSION}")
    log.info("=" * 70)

    for epoch in range(N_EPOCHS):
        model.train()
        steady = epoch < WARMUP_EPOCHS

        xyt_int, xyt_bnd = sample_collocation(rng, N_COLLOCATION, N_BOUNDARY)

        # ── Physics loss ───────────────────────────────────────────────────
        L_pde = loss_pde(model, xyt_int, t_max, t_hours, df_era5, device, steady)

        # ── Data fidelity loss ─────────────────────────────────────────────
        L_dat = loss_data(model, rng, N_DATA, t_max, t_hours, df_era5, device, sta_data)

        # ── Boundary condition loss ────────────────────────────────────────
        L_bc  = loss_bc(model, xyt_bnd, t_max, t_hours, df_era5, device)

        # ── K bound penalty (DiffusionSubNet) ──────────────────────────────
        # Separate forward pass to get Kx, Ky for bound penalty
        # (DiffusionSubNet is tiny: 1,314 params — negligible overhead)
        xyt_kb = torch.tensor(xyt_int, dtype=torch.float32, device=device)
        era5_kb = interp_era5(xyt_int[:, 2], t_max, t_hours, df_era5, ["blh"])
        blh_kb  = torch.tensor(era5_kb / BLH_NORM_SCALE, device=device)
        _, (Kx_kb, Ky_kb, _) = model(xyt_kb, blh=blh_kb)
        L_k_bound = model.diffusion_subnet.bound_penalty(Kx_kb, Ky_kb)

        # ── Total loss ─────────────────────────────────────────────────────
        L_total = (LAMBDA_PHYSICS * L_pde
                   + LAMBDA_DATA  * L_dat
                   + LAMBDA_BC    * L_bc
                   + LAMBDA_K_BOUND * L_k_bound)

        # ── Backprop ───────────────────────────────────────────────────────
        optimizer.zero_grad()
        L_total.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()

        record = {
            "epoch":      epoch,
            "L_total":    float(L_total.detach()),
            "L_pde":      float(L_pde.detach()),
            "L_data":     float(L_dat.detach()),
            "L_bc":       float(L_bc.detach()),
            "L_k_bound":  float(L_k_bound.detach()),
            "lr":         float(scheduler.get_last_lr()[0]),
            "steady":     int(steady),
        }
        loss_history.append(record)

        if epoch % 10 == 0:
            log.info(
                f"  Ep {epoch:4d}/{N_EPOCHS}"
                f"  L={L_total:.5f}"
                f"  pde={L_pde:.5f}"
                f"  dat={L_dat:.5f}"
                f"  bc={L_bc:.5f}"
                f"  kb={L_k_bound:.5f}"
                f"  lr={scheduler.get_last_lr()[0]:.2e}"
                + ("  [steady]" if steady else "")
            )

        # ── W&B per-epoch logging ──────────────────────────────────────────
        if wandb_run is not None:
            wandb_run.log({
                "train/L_total":   float(L_total.detach()),
                "train/L_pde":     float(L_pde.detach()),
                "train/L_data":    float(L_dat.detach()),
                "train/L_bc":      float(L_bc.detach()),
                "train/L_k_bound": float(L_k_bound.detach()),
                "train/lr":        float(scheduler.get_last_lr()[0]),
                "train/steady":    int(steady),
                "epoch":           epoch,
            }, step=epoch)
            # Spatial snapshots at regular intervals
            if (epoch + 1) % SPATIAL_LOG_EVERY == 0 or epoch == N_EPOCHS - 1:
                _log_spatial_snapshot(model, device, epoch, wandb_run)

        if (epoch + 1) % SAVE_EVERY == 0:
            save_checkpoint(model, optimizer, scheduler, epoch + 1, loss_history, out_dir)

    return loss_history


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    torch.manual_seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    t_wall_start = time.time()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info(f"Device: {device}")
    if device.type == "cuda":
        log.info(f"  GPU : {torch.cuda.get_device_name(0)}")
        log.info(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    # ── Load data ──────────────────────────────────────────────────────────
    df_era5, t_hours, t_max, sta_data = load_medellin_data(DATA_DIR)
    if sta_data is not None:
        log.info(f"Per-station L_data: {sta_data['n_total']:,} station-hour pairs, "
                 f"weight range [{sta_data['weight'].min():.2f}, {sta_data['weight'].max():.2f}]")

    # ── Build model ────────────────────────────────────────────────────────
    model = FourierPINNModule(t_max=t_max).to(device)
    n_params   = model.count_parameters()
    breakdown  = model.parameter_breakdown()
    log.info(f"FourierPINN v2: {n_params:,} trainable parameters")
    log.info(
        f"  Architecture: FourierEmbed({FOURIER_M}, σ={FOURIER_SIGMA}) → "
        f"ResidualMLP({HIDDEN_LAYERS}×{HIDDEN_UNITS}) → head_C + DiffusionSubNet + SourceSubNet"
    )
    log.info(f"  trunk={breakdown['net (main trunk)']:,}  "
             f"head_C={breakdown['head_C']:,}  "
             f"DiffSubNet={breakdown['diffusion_subnet']:,}  "
             f"SrcSubNet={breakdown['source_subnet']:,}")

    # ── W&B init ───────────────────────────────────────────────────────────
    wandb_run = _setup_wandb({
        "arch_version":   ARCH_VERSION,
        "n_epochs":       N_EPOCHS,
        "lr":             LR,
        "fourier_m":      FOURIER_M,
        "fourier_sigma":  FOURIER_SIGMA,
        "hidden_units":   HIDDEN_UNITS,
        "hidden_layers":  HIDDEN_LAYERS,
        "n_collocation":  N_COLLOCATION,
        "n_boundary":     N_BOUNDARY,
        "n_data":         N_DATA,
        "warmup_epochs":  WARMUP_EPOCHS,
        "lambda_physics": LAMBDA_PHYSICS,
        "lambda_data":    LAMBDA_DATA,
        "lambda_bc":      LAMBDA_BC,
        "lambda_k_bound": LAMBDA_K_BOUND,
        "n_params":       n_params,
        "device":         str(device),
        "stage":          "stage2_medellin_pretrain",
    })

    # ── Train ──────────────────────────────────────────────────────────────
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    loss_history = train(model, df_era5, t_hours, t_max, OUT_DIR, device,
                         sta_data=sta_data, wandb_run=wandb_run)

    t_wall_end = time.time()
    wall_clock = t_wall_end - t_wall_start

    # ── Save final backbone ────────────────────────────────────────────────
    final_state = {
        "epoch":                N_EPOCHS,
        "model_state_dict":     model.state_dict(),
        "architecture_version": ARCH_VERSION,
        "upgrades": ["DiffusionSubNet_BLH_elev", "SourceSubNet_cyclic_time",
                     "loss_schedule_v2", "K_bound_penalty"],
        "loss_schedule":        LOSS_SCHEDULE,
        "training_domain":      "Medellin_PINN_bbox",
        "bbox":                 MEDELLIN_PINN_BBOX,
        "n_params":             n_params,
        "fourier_m":            FOURIER_M,
        "fourier_sigma":        FOURIER_SIGMA,
        "hidden_units":         HIDDEN_UNITS,
        "hidden_layers":        HIDDEN_LAYERS,
        "wall_clock_sec":       wall_clock,
    }
    final_path = OUT_DIR / "pretrained_physics_backbone.pt"
    torch.save(final_state, final_path)
    log.info(f"Final backbone → {final_path}")

    # ── Save loss CSV ──────────────────────────────────────────────────────
    loss_csv = OUT_DIR / "pretrain_losses.csv"
    pd.DataFrame(loss_history).to_csv(loss_csv, index=False)
    log.info(f"Loss history → {loss_csv}")

    # ── Final loss summary ─────────────────────────────────────────────────
    tail = loss_history[-20:]
    log.info("Final 20-epoch mean losses:")
    final_losses = {}
    for key in ["L_pde", "L_data", "L_bc", "L_k_bound", "L_total"]:
        vals = [r[key] for r in tail]
        mean_v, std_v = np.mean(vals), np.std(vals)
        final_losses[key] = {"mean": float(mean_v), "std": float(std_v)}
        log.info(f"  {key:12s}: {mean_v:.6f} ± {std_v:.6f}")

    # ── Append to TrainingLogger ───────────────────────────────────────────
    try:
        sys.path.insert(0, str(Path(__file__).parents[3] / "src"))
        from utils.training_logger import TrainingLogger
        logger = TrainingLogger(wandb_run=wandb_run)
        logger.append_session({
            "session_type":      "medellin_pretrain_v2",
            "timestamp":         datetime.now(timezone.utc).isoformat(),
            "platform":          (f"Kaggle {torch.cuda.get_device_name(0)}"
                                  if device.type == "cuda" else "Local CPU"),
            "architecture_ver":  ARCH_VERSION,
            "n_epochs":          N_EPOCHS,
            "wall_clock_sec":    wall_clock,
            "data_period":       f"{df_era5['datetime_utc'].iloc[0]} → {df_era5['datetime_utc'].iloc[-1]}",
            "n_samples":         sta_data["n_total"] if sta_data else len(df_era5),
            "loss_schedule":     LOSS_SCHEDULE,
            "final_losses":      final_losses,
            "checkpoints":       [str(p) for p in sorted(
                                   (OUT_DIR / "checkpoints").glob("epoch_*.pt"))],
            "recommended_ckpt":  "epoch_0450.pt",  # update after diagnosing new run
            "arch_mismatches":   [],
            "notes": (
                "v2 run: DiffusionSubNet with BLH inputs, SourceSubNet cyclic time, "
                "updated loss schedule (λ_p=0.7, λ_d=0.2, λ_bc=0.1, λ_kb=0.05). "
                "Recommended checkpoint TBD — run run_diagnostic.py after download."
            ),
            "verdict": "PASS — proceed",  # to be confirmed by post-run diagnostic
        })
        logger.print_summary_table()
    except Exception as e:
        log.warning(f"TrainingLogger unavailable (expected on Kaggle): {e}")

    # ── W&B finish ─────────────────────────────────────────────────────────
    if wandb_run is not None:
        try:
            wandb_run.finish()
        except Exception:
            pass

    log.info(f"Wall-clock: {wall_clock:.1f}s  ({wall_clock/60:.1f} min)")
    log.info("✅ Medellín pre-training v2 complete.")


if __name__ == "__main__":
    main()
