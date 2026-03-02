"""
collocation.py — Collocation point sampling strategies for the Kandy PINN.

Two strategies (§2.11 of RESEARCH_PROJECT_DESIGN.md):

1. RANDOM UNIFORM (early training):
   Sample N_c points uniformly in the Kandy domain × time window.
   Simple, unbiased, but may under-sample high-residual regions.

2. RESIDUAL-ADAPTIVE REFINEMENT (RAR, after epoch 200):
   Evaluate PDE residual on a coarse grid, then oversample regions
   where |R|² is high. Implements the RAR approach from Lu et al. (2021).
   Concentrates collocation points where the physics is most violated.

The transition from uniform → RAR is triggered by the curriculum scheduler.
"""

import logging
from typing import Optional, Tuple

import numpy as np

log = logging.getLogger("collocation")


def sample_uniform(
    n_interior: int,
    n_boundary: int,
    domain_bbox: dict,
    t_max_norm:  float = 1.0,
    seed:        Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Sample collocation points uniformly within the PINN domain.

    Args:
        n_interior   : Number of interior (x, y, t) points
        n_boundary   : Number of boundary spatial points
        domain_bbox  : Dict with lon_min/max, lat_min/max (used only for shape)
        t_max_norm   : Maximum normalised time (default 1.0)
        seed         : RNG seed for reproducibility

    Returns:
        xy_int  : (n_interior, 2)  normalised [x, y] interior points
        t_int   : (n_interior, 1)  normalised time interior points
        xy_bnd  : (n_boundary, 2)  normalised [x, y] boundary points
        t_bnd   : (n_boundary, 1)  normalised time boundary points
    """
    rng = np.random.default_rng(seed)
    xy_int = rng.uniform(-1, 1, (n_interior, 2)).astype(np.float32)
    t_int  = rng.uniform(0, t_max_norm, (n_interior, 1)).astype(np.float32)

    n_side = n_boundary // 4
    wall   = np.linspace(-1, 1, n_side, dtype=np.float32)
    north  = np.column_stack([wall, np.ones(n_side)])
    south  = np.column_stack([wall, -np.ones(n_side)])
    east   = np.column_stack([np.ones(n_side),  wall])
    west   = np.column_stack([-np.ones(n_side), wall])
    xy_bnd = np.vstack([north, south, east, west]).astype(np.float32)
    t_bnd  = rng.uniform(0, t_max_norm, (len(xy_bnd), 1)).astype(np.float32)

    return xy_int, t_int, xy_bnd, t_bnd


def sample_rar(
    model,
    n_coarse:  int,
    n_add:     int,
    n_keep:    int,
    xy_current: np.ndarray,
    t_current:  np.ndarray,
    wind_u:     np.ndarray,
    wind_v:     np.ndarray,
    device=None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Residual-Adaptive Refinement (RAR) collocation update.

    1. Evaluate PDE residual on a coarse random grid (n_coarse points)
    2. Select the top n_add points with highest |R|²
    3. Combine with n_keep randomly retained existing points
    4. Return updated collocation set

    Reference: Lu et al. (2021) "Residual-adaptive refinement for solving
    partial differential equations." SIAM Review.

    Args:
        model       : FourierPINN model
        n_coarse    : Evaluation grid size
        n_add       : Points to add from high-residual regions
        n_keep      : Points to retain from existing set
        xy_current  : Current interior points (N_curr, 2)
        t_current   : Current interior times (N_curr, 1)
        wind_u, v   : Wind fields at current points

    Returns:
        xy_new : Updated interior xy (n_keep + n_add, 2)
        t_new  : Updated interior t  (n_keep + n_add, 1)
    """
    try:
        import torch
        from src.stage3_pinn.physics.advection_diffusion import pde_residual
    except ImportError:
        log.warning("RAR requires PyTorch and advection_diffusion module. Falling back to uniform.")
        rng = np.random.default_rng()
        idx = rng.choice(len(xy_current), size=min(n_keep, len(xy_current)), replace=False)
        return xy_current[idx], t_current[idx]

    dev = device or torch.device("cpu")

    # Evaluate residual on coarse random grid
    rng       = np.random.default_rng()
    xy_coarse = rng.uniform(-1, 1, (n_coarse, 2)).astype(np.float32)
    t_coarse  = rng.uniform(0, 1, (n_coarse, 1)).astype(np.float32)
    xyt_c     = np.hstack([xy_coarse, t_coarse])

    n_wu     = wind_u.shape[0] if hasattr(wind_u, "shape") else n_coarse
    wu_coarse = np.ones((n_coarse, 1), dtype=np.float32) * (wind_u.mean() if hasattr(wind_u, "mean") else wind_u)
    wv_coarse = np.ones((n_coarse, 1), dtype=np.float32) * (wind_v.mean() if hasattr(wind_v, "mean") else wind_v)

    model.eval()
    with torch.no_grad():
        xyt_t = torch.tensor(xyt_c, device=dev)
        wu_t  = torch.tensor(wu_coarse, device=dev)
        wv_t  = torch.tensor(wv_coarse, device=dev)
        R = pde_residual(model, xyt_t, wu_t, wv_t)
        residuals = R.abs().squeeze().cpu().numpy()

    # Top-n_add high-residual points
    top_idx = np.argsort(residuals)[-n_add:]
    xy_add  = xy_coarse[top_idx]
    t_add   = t_coarse[top_idx]

    # Keep random subset of existing
    keep_n  = min(n_keep, len(xy_current))
    keep_idx = rng.choice(len(xy_current), size=keep_n, replace=False)
    xy_new  = np.vstack([xy_current[keep_idx], xy_add])
    t_new   = np.vstack([t_current[keep_idx],  t_add])

    log.info(f"RAR: kept {keep_n} existing + added {n_add} high-residual points "
             f"(max |R|={residuals[top_idx].max():.4f})")
    return xy_new, t_new


def to_tensors(
    xy: np.ndarray,
    t:  np.ndarray,
    wind_u: float,
    wind_v: float,
    device=None,
):
    """Convert numpy collocation arrays to PyTorch tensors."""
    try:
        import torch
    except ImportError:
        raise ImportError("PyTorch required")

    dev  = device or torch.device("cpu")
    xyt  = torch.tensor(np.hstack([xy, t]), dtype=torch.float32, device=dev)
    wu   = torch.full((len(xy), 1), wind_u, dtype=torch.float32, device=dev)
    wv   = torch.full((len(xy), 1), wind_v, dtype=torch.float32, device=dev)
    return xyt, wu, wv
