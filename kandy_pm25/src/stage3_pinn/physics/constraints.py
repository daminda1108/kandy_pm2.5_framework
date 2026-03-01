"""
constraints.py — Physical constraint losses for the Kandy PINN.

These hard/soft constraints prevent physically implausible solutions (§2.11):

1. NON-NEGATIVITY: C ≥ 0, Kx ≥ ε, Ky ≥ ε, S ≥ 0
   Enforced via softplus activation (hard) or penalty (soft).

2. DIFFUSIVITY BOUNDS: Kx, Ky ∈ [1, 500] m²/s
   From Stull (1988) atmospheric diffusivity table for valley flows.
   Kx > Ky expected (along-valley diffusion > cross-valley).

3. K ANISOTROPY: Kx / Ky ∈ [1.5, 10]
   Physical expectation from valley channelling theory.
   If Kx/Ky < 1.5 → domain is not valley-dominated → flag.

4. DAILY MEAN CONSTRAINT: mean(C_PINN over domain) ≈ Stage1 daily mean
   This prevents the PINN from drifting away from the satellite estimate.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("constraints")

# Physical diffusivity bounds [m²/s] — Stull (1988) Table 8-2
K_MIN = 1.0
K_MAX = 500.0
K_ANISOTROPY_MIN = 1.5   # Kx/Ky must be at least this
K_ANISOTROPY_MAX = 10.0


def positivity_loss(
    C: "torch.Tensor",
    Kx: "torch.Tensor",
    Ky: "torch.Tensor",
    S: "torch.Tensor",
) -> "torch.Tensor":
    """
    Penalty for negative concentrations, diffusivities, or source strengths.

    Uses ReLU(-x) = max(0, -x) as a soft penalty:
        L_pos = mean(relu(-C)) + mean(relu(-Kx)) + mean(relu(-Ky)) + mean(relu(-S))

    Note: In the FourierPINN architecture, softplus activations on the output
    heads should make this zero at convergence. This loss serves as an extra
    safeguard during early training.
    """
    try:
        import torch
        import torch.nn.functional as F
    except ImportError:
        raise ImportError("PyTorch required")

    loss  = F.relu(-C).mean()
    loss += F.relu(-Kx).mean()
    loss += F.relu(-Ky).mean()
    loss += F.relu(-S).mean()
    return loss


def diffusivity_bounds_loss(
    Kx: "torch.Tensor",
    Ky: "torch.Tensor",
) -> "torch.Tensor":
    """
    Penalise Kx or Ky outside the physically plausible range [K_MIN, K_MAX].

        L_bounds = mean(relu(K_MIN - Kx)) + mean(relu(Kx - K_MAX))
                 + mean(relu(K_MIN - Ky)) + mean(relu(Ky - K_MAX))
    """
    try:
        import torch
        import torch.nn.functional as F
    except ImportError:
        raise ImportError("PyTorch required")

    loss  = F.relu(K_MIN - Kx).mean() + F.relu(Kx - K_MAX).mean()
    loss += F.relu(K_MIN - Ky).mean() + F.relu(Ky - K_MAX).mean()
    return loss


def anisotropy_loss(
    Kx: "torch.Tensor",
    Ky: "torch.Tensor",
) -> "torch.Tensor":
    """
    Soft penalty for anisotropy ratio Kx/Ky outside [K_ANISOTROPY_MIN, K_ANISOTROPY_MAX].

    Expected for a confined valley: along-valley K (Kx) > cross-valley K (Ky).
    """
    try:
        import torch
        import torch.nn.functional as F
    except ImportError:
        raise ImportError("PyTorch required")

    ratio = Kx / (Ky + 1e-6)
    loss  = F.relu(K_ANISOTROPY_MIN - ratio).mean()
    loss += F.relu(ratio - K_ANISOTROPY_MAX).mean()
    return loss


def daily_mean_constraint_loss(
    C_pinn: "torch.Tensor",
    C_stage1_daily_mean: float,
    weight: float = 1.0,
) -> "torch.Tensor":
    """
    Enforce that the spatial mean of the PINN output matches the Stage 1 daily mean.

        L_mean = w × (mean(C_PINN) - C_Stage1)²

    This prevents the PINN from hallucinating a completely different "level" of
    PM2.5 from Stage 1. The mean is well-constrained by Stage 1; the PINN's
    job is to add spatial structure within the valley.

    Args:
        C_pinn              : PINN concentration predictions (N,) for a given day
        C_stage1_daily_mean : Stage 1 domain-average PM2.5 for that day [µg/m³]
        weight              : Loss weight (reduce if Stage 1 is uncertain)

    Returns:
        Scalar loss tensor
    """
    try:
        import torch
    except ImportError:
        raise ImportError("PyTorch required")

    target = torch.tensor(C_stage1_daily_mean, dtype=C_pinn.dtype, device=C_pinn.device)
    return weight * (C_pinn.mean() - target) ** 2


def compute_all_constraints(
    C: "torch.Tensor",
    Kx: "torch.Tensor",
    Ky: "torch.Tensor",
    S: "torch.Tensor",
    C_stage1_mean: float,
    weights: dict = None,
) -> dict:
    """
    Compute all physical constraint losses and return a dict.

    Args:
        C, Kx, Ky, S   : PINN output tensors
        C_stage1_mean   : Stage 1 daily mean PM2.5 [µg/m³]
        weights         : Dict of loss weights, defaults to all 1.0

    Returns:
        Dict with individual losses and total constraint loss.
    """
    w = {"positivity": 1.0, "bounds": 1.0, "anisotropy": 0.5, "mean": 2.0}
    if weights:
        w.update(weights)

    losses = {
        "positivity":  positivity_loss(C, Kx, Ky, S),
        "bounds":      diffusivity_bounds_loss(Kx, Ky),
        "anisotropy":  anisotropy_loss(Kx, Ky),
        "mean":        daily_mean_constraint_loss(C, C_stage1_mean, w["mean"]),
    }
    try:
        import torch
        total = sum(w.get(k, 1.0) * v for k, v in losses.items())
        losses["total"] = total
    except ImportError:
        pass

    return losses
