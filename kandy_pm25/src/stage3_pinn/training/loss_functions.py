"""
loss_functions.py — Composite PINN loss function for Stage 3 Kandy training.

Total loss (§2.11 of RESEARCH_PROJECT_DESIGN.md):

    L_total = λ_pde × L_pde
            + λ_data × L_data
            + λ_bc × L_bc
            + λ_phys × L_physics_constraints

Where:
    L_pde   : PDE residual (advection-diffusion equation, from advection_diffusion.py)
    L_data  : Weighted data fidelity against Stage 1 daily-aggregated predictions
    L_bc    : Dirichlet BC at valley rim (Stage 1 rim predictions)
    L_phys  : Physical constraints (non-negativity, K bounds, daily mean)

Loss weights (λ) are scheduled by curriculum.py — λ_pde starts high,
λ_data is introduced after 100 warm-up epochs.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("loss_functions")


def data_fidelity_loss(
    C_pred: "torch.Tensor",
    C_stage1: "torch.Tensor",
    weights: Optional["torch.Tensor"] = None,
) -> "torch.Tensor":
    """
    Weighted observation fidelity loss.

        L_data = E_i[ w_i × (C_PINN(x_i,y_i,t_i) - C_Stage1_i)² ]

    Args:
        C_pred    : PINN predictions at Stage 1 pixel locations (N,)
        C_stage1  : Stage 1 PM2.5 predictions (N,)
        weights   : Inverse-variance weights from Stage 1 PI (N,)
                    If None, uniform weights.

    Returns:
        Scalar mean weighted MSE tensor
    """
    try:
        import torch
    except ImportError:
        raise ImportError("PyTorch required")

    residual = (C_pred - C_stage1) ** 2
    if weights is not None:
        return (weights * residual).mean()
    return residual.mean()


def total_loss(
    L_pde:   "torch.Tensor",
    L_data:  "torch.Tensor",
    L_bc:    "torch.Tensor",
    L_phys:  "torch.Tensor",
    lambda_pde:  float = 1.0,
    lambda_data: float = 0.1,
    lambda_bc:   float = 1.0,
    lambda_phys: float = 0.5,
) -> "torch.Tensor":
    """
    Combine all loss terms with their scheduled weights.

    Args:
        L_pde, L_data, L_bc, L_phys : Individual loss tensors (scalars)
        lambda_*                      : Loss weights from curriculum scheduler

    Returns:
        L_total: Scalar loss tensor for backprop
    """
    return (lambda_pde  * L_pde  +
            lambda_data * L_data +
            lambda_bc   * L_bc   +
            lambda_phys * L_phys)


class LossTracker:
    """Track and log individual loss components during training."""

    def __init__(self):
        self.history = []

    def record(
        self,
        epoch: int,
        L_pde:   float,
        L_data:  float,
        L_bc:    float,
        L_phys:  float,
        L_total: float,
        lr:      float,
    ) -> None:
        self.history.append({
            "epoch":   epoch,
            "L_pde":   round(L_pde,  6),
            "L_data":  round(L_data, 6),
            "L_bc":    round(L_bc,   6),
            "L_phys":  round(L_phys, 6),
            "L_total": round(L_total, 6),
            "lr":      lr,
        })

    def to_dataframe(self):
        import pandas as pd
        return pd.DataFrame(self.history)

    def last(self) -> dict:
        return self.history[-1] if self.history else {}

    def log_epoch(self, epoch: int, every: int = 50) -> None:
        if self.history and epoch % every == 0:
            r = self.last()
            log.info(
                f"Epoch {epoch:5d}: L_total={r['L_total']:.4f}  "
                f"L_pde={r['L_pde']:.4f}  L_data={r['L_data']:.4f}  "
                f"L_bc={r['L_bc']:.4f}  L_phys={r['L_phys']:.4f}  "
                f"lr={r['lr']:.2e}"
            )
