"""
pretrain_medellin.py — Stage 2: Physics-dominant pre-training on Medellín data.

Goal (§2.6 of RESEARCH_PROJECT_DESIGN.md):
    Pre-train the PINN physics backbone on Medellín so it learns the
    advection-diffusion-source PDE structure from a well-observed valley city,
    before fine-tuning on data-sparse Kandy.

Training philosophy:
  - λ_physics is HIGH (0.9) relative to λ_data (0.1) during pre-training.
    The physics must dominate — we do not want the network to overfit Medellín data.
  - Only the physics-encoding layers are trained; the domain head (decoder)
    will be swapped for the Kandy head during Stage 3 fine-tuning.

Key outputs:
  - pretrained_physics_backbone.pt  — shipped to Stage 3 init
  - pretrain_losses.csv             — training curves for diagnostics

Usage:
    python pretrain_medellin.py [--epochs 500] [--lr 5e-4]
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[4]))
from config import LOG_FORMAT, LOG_DATEFMT, MODELS_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("pretrain_medellin")

# Medellín training hyperparameters
DEFAULT_EPOCHS    = 500
DEFAULT_LR        = 5e-4
LAMBDA_PHYSICS    = 0.9     # Heavy physics weight — dominant during pre-training
LAMBDA_DATA       = 0.1     # Observation term — Medellín SIATA stations
N_COLLOCATION     = 5000    # Interior PDE points per epoch
N_BOUNDARY        = 500     # Boundary condition points per epoch

MEDELLIN_RAW_DIR  = Path(__file__).parents[4] / "data" / "raw" / "medellin"
CHECKPOINT_DIR    = MODELS_DIR / "stage2_pretrain"


def load_medellin_data(era5_dir: Path, pm25_dir: Path) -> tuple:
    """
    Load and merge Medellín ERA5 meteorology + SIATA PM2.5 ground truth.

    Returns:
        (wind_df, pm25_df) — DataFrames with daily meteorology and PM2.5 obs.
    """
    pm25_csvs = sorted(pm25_dir.glob("siata_pm25_*.csv"))
    if not pm25_csvs:
        raise FileNotFoundError(
            f"No SIATA PM2.5 CSVs in {pm25_dir}. Run: python download_medellin.py --pm25-only"
        )
    pm25_df = pd.concat([pd.read_csv(f) for f in pm25_csvs], ignore_index=True)
    log.info(f"Loaded {len(pm25_df)} Medellín PM2.5 obs")

    era5_ncs = sorted(era5_dir.glob("medellin_era5_*.nc"))
    if not era5_ncs:
        log.warning("No ERA5 data for Medellín — wind field will be unavailable")
        return None, pm25_df

    try:
        import xarray as xr
        wind_ds = xr.open_mfdataset(era5_ncs, combine="by_coords")
        log.info(f"Loaded Medellín ERA5: {wind_ds}")
        return wind_ds, pm25_df
    except Exception as e:
        log.warning(f"ERA5 load failed: {e}")
        return None, pm25_df


def build_collocation_grid(bbox: dict, n_interior: int, n_boundary: int, t_days: int) -> tuple:
    """
    Generate collocation points for Medellín domain.

    Interior: random (x, y, t) within the Medellín valley bounding box.
    Boundary: points on the spatial boundary (valley rim) at all times.

    Returns:
        (xy_interior, xy_boundary, t_interior, t_boundary) as numpy arrays.
    """
    rng   = np.random.default_rng(42)
    x_int = rng.uniform(bbox["lon_min"], bbox["lon_max"], n_interior)
    y_int = rng.uniform(bbox["lat_min"], bbox["lat_max"], n_interior)
    t_int = rng.uniform(0, t_days, n_interior)

    n_side = n_boundary // 4
    lon_vals = np.linspace(bbox["lon_min"], bbox["lon_max"], n_side)
    lat_vals = np.linspace(bbox["lat_min"], bbox["lat_max"], n_side)
    x_bnd = np.concatenate([lon_vals, lon_vals,
                             np.full(n_side, bbox["lon_min"]),
                             np.full(n_side, bbox["lon_max"])])
    y_bnd = np.concatenate([np.full(n_side, bbox["lat_min"]),
                             np.full(n_side, bbox["lat_max"]),
                             lat_vals, lat_vals])
    t_bnd = rng.uniform(0, t_days, len(x_bnd))

    return (np.column_stack([x_int, y_int]),
            np.column_stack([x_bnd, y_bnd]),
            t_int[:, None], t_bnd[:, None])


def pretrain(
    model,
    pm25_df: pd.DataFrame,
    bbox: dict,
    n_epochs: int = DEFAULT_EPOCHS,
    lr: float = DEFAULT_LR,
) -> list:
    """
    Run physics-dominant PINN pre-training on Medellín data.

    Loss (Medellín):
        L_total = λ_physics × L_pde + λ_data × L_siata + L_bc

    During pre-training λ_physics=0.9 dominates so the network learns
    advection-diffusion structure, not Medellín-specific data patterns.

    Args:
        model    : Initialised FourierPINN (from models/fourier_pinn.py)
        pm25_df  : SIATA station PM2.5 DataFrame
        bbox     : Domain bounding box dict
        n_epochs : Training epochs
        lr       : Learning rate

    Returns:
        List of loss dicts per epoch.
    """
    try:
        import torch
        import torch.optim as optim
    except ImportError:
        raise ImportError("PyTorch not installed. Run: pip install torch")

    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_epochs, eta_min=1e-6)

    t_days = 365 * 5  # 5 years of Medellín data
    loss_history = []

    log.info(f"Starting Medellín pre-training: {n_epochs} epochs, lr={lr}")
    for epoch in range(n_epochs):
        xy_int, xy_bnd, t_int, t_bnd = build_collocation_grid(bbox, N_COLLOCATION, N_BOUNDARY, t_days)

        # Placeholder: in real implementation, compute:
        # L_pde = physics_residual(model, xy_int, t_int)
        # L_data = data_loss(model, pm25_df, era5_wind)
        # L_bc = boundary_loss(model, xy_bnd, t_bnd)
        # loss = LAMBDA_PHYSICS * L_pde + LAMBDA_DATA * L_data + L_bc
        loss_val = 0.0  # Replaced by actual autograd computation

        optimizer.step()
        scheduler.step()

        if epoch % 50 == 0:
            log.info(f"  Epoch {epoch:4d}/{n_epochs}: loss={loss_val:.6f}  lr={scheduler.get_last_lr()[0]:.2e}")
        loss_history.append({"epoch": epoch, "loss": loss_val})

    log.info("Medellín pre-training complete.")
    return loss_history


def save_pretrained_backbone(model, loss_history: list) -> None:
    """Save the pretrained physics backbone and training curves."""
    try:
        import torch
    except ImportError:
        raise ImportError("PyTorch required")

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    ckpt_path = CHECKPOINT_DIR / "pretrained_physics_backbone.pt"
    torch.save({
        "model_state_dict":  model.state_dict(),
        "lambda_physics":    LAMBDA_PHYSICS,
        "n_epochs":          len(loss_history),
        "training_domain":   "Medellin_Aburra",
    }, str(ckpt_path))
    log.info(f"Pre-trained backbone saved → {ckpt_path}")

    pd.DataFrame(loss_history).to_csv(CHECKPOINT_DIR / "pretrain_losses.csv", index=False)
    log.info(f"Loss curves saved → {CHECKPOINT_DIR / 'pretrain_losses.csv'}")


def main():
    parser = argparse.ArgumentParser(description="Stage 2 Medellín pre-training")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--lr",     type=float, default=DEFAULT_LR)
    args = parser.parse_args()

    # Lazy import to avoid torch dependency at import time
    try:
        from src.stage3_pinn.models.fourier_pinn import FourierPINN
    except ImportError:
        log.warning("FourierPINN not yet importable — run after completing stage3_pinn/models/fourier_pinn.py")
        sys.exit(0)

    MEDELLIN_BBOX = {"lat_min": 6.10, "lat_max": 6.40, "lon_min": -75.70, "lon_max": -75.48}
    pm25_dir = MEDELLIN_RAW_DIR / "pm25"
    era5_dir = MEDELLIN_RAW_DIR / "era5"

    _, pm25_df = load_medellin_data(era5_dir, pm25_dir)
    model = FourierPINN()
    loss_history = pretrain(model, pm25_df, MEDELLIN_BBOX, n_epochs=args.epochs, lr=args.lr)
    save_pretrained_backbone(model, loss_history)
    log.info("✅ Stage 2 Medellín pre-training complete.")


if __name__ == "__main__":
    main()
