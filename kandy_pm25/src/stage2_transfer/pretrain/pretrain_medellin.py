"""
pretrain_medellin.py — Stage 2: Physics-dominant pre-training on Medellín data.

Goal (§2.6 of RESEARCH_PROJECT_DESIGN.md):
    Pre-train the PINN physics backbone on Medellín so it learns the
    advection-diffusion-source PDE structure from a well-observed valley city,
    before fine-tuning on data-sparse Kandy.

Training philosophy:
  - λ_physics is HIGH (0.7) relative to λ_data (0.2) during pre-training.
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

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT, MODELS_DIR, MEDELLIN_PINN_BBOX, LOSS_SCHEDULE

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("pretrain_medellin")

# Medellín training hyperparameters
DEFAULT_EPOCHS    = 500
DEFAULT_LR        = 5e-4
LAMBDA_PHYSICS    = LOSS_SCHEDULE["medellin_pretrain"]["lambda_physics"]  # 0.7
LAMBDA_DATA       = LOSS_SCHEDULE["medellin_pretrain"]["lambda_data"]    # 0.2
N_COLLOCATION     = 5000    # Interior PDE points per epoch
N_BOUNDARY        = 500     # Boundary condition points per epoch

# NOTE: Runnable pre-training is in pretrain_medellin_kaggle.py (Kaggle GPU).
# This module retains the scaffold for local inspection and Stage 3 wiring.
MEDELLIN_STAGE2_DIR = Path(__file__).parents[3] / "data" / "processed" / "stage2"
MEDELLIN_EXT_DIR    = Path(__file__).parents[3] / "data" / "external" / "medellin"
CHECKPOINT_DIR      = MODELS_DIR / "stage2_pretrain"


def load_medellin_data() -> pd.DataFrame:
    """
    Load the processed Medellín Stage 2 training parquet.

    Returns:
        df — merged hourly PM2.5 + ERA5 DataFrame (DatetimeIndex, UTC).
             Columns: pm25, n_stations, pm25_std, good_coverage,
                      u10, v10, t2m, d2m, blh, sp, tp, skt
    """
    parquet = MEDELLIN_STAGE2_DIR / "medellin_stage2_training.parquet"
    if not parquet.exists():
        raise FileNotFoundError(
            f"Stage 2 training parquet not found: {parquet}\n"
            "Run the Stage 2 data pipeline or use pretrain_medellin_kaggle.py on Kaggle."
        )
    df = pd.read_parquet(parquet)
    log.info(f"Loaded {len(df)} Medellín hourly records from {parquet.name}")
    return df


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

    # Compute t_days from actual data span (~11 months: Oct 2018–Aug 2019)
    t_days = max((pm25_df.index.max() - pm25_df.index.min()).days, 1)  # ~334 days
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

    # MEDELLIN_PINN_BBOX imported from config (15×15km sub-domain, urban core)
    pm25_df = load_medellin_data()
    model = FourierPINN()
    loss_history = pretrain(model, pm25_df, MEDELLIN_PINN_BBOX, n_epochs=args.epochs, lr=args.lr)
    save_pretrained_backbone(model, loss_history)
    log.info("✅ Stage 2 Medellín pre-training complete.")


if __name__ == "__main__":
    main()
