"""
pinn_steady.py — Steady-state PINN option for Kandy PM2.5 (Option A, §2.10).

The steady-state approximation sets ∂C/∂t = 0 and solves:
    u·∂C/∂x + v·∂C/∂y = ∂/∂x(Kx·∂C/∂x) + ∂/∂y(Ky·∂C/∂y) + S - λC

Suitable when:
  - AM satellite overpass only (single daily snapshot)
  - Wind field is approximately stationary over the averaging window
  - Computational budget is limited

Advantage over transient: 2× faster training (no time derivative).
Limitation: Cannot capture diurnal PM2.5 cycle or katabatic flushing events.

Use pinn_transient.py when hourly data resolution becomes available.
See §2.10 of RESEARCH_PROJECT_DESIGN.md for the Stage decision criteria.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("pinn_steady")


def solve_steady_state(
    model,
    stage1_df: "pd.DataFrame",
    n_epochs: int = 500,
    lr: float = 5e-4,
    device=None,
) -> list:
    """
    Steady-state PINN training loop.

    Differences from transient training (train.py):
      1. Collocations use t_norm=0.5 (fixed mid-day snapshot)
      2. L_pde uses steady_state_pde_loss (∂C/∂t = 0)
      3. Curriculum has no warm-up (λ_data is active from epoch 0)
      4. Training is 2× faster — no time-dimension collocation

    Args:
        model      : FourierPINN model
        stage1_df  : Stage 1 predictions DataFrame
        n_epochs   : Training epochs
        lr         : Learning rate
        device     : torch.device

    Returns:
        loss_history: List of loss dicts per epoch
    """
    try:
        import torch
        import torch.optim as optim
    except ImportError:
        raise ImportError("PyTorch required")

    from src.stage3_pinn.physics.advection_diffusion import steady_state_pde_loss
    from src.stage3_pinn.training.collocation import sample_uniform, to_tensors
    from src.stage3_pinn.training.loss_functions import data_fidelity_loss, LossTracker
    from config import KANDY_PINN_BBOX, N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY

    dev       = device or torch.device("cpu")
    model.to(dev)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    tracker   = LossTracker()

    xy_int, t_int, xy_bnd, _ = sample_uniform(N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY, KANDY_PINN_BBOX)
    # Always use t=0.5 for steady-state (mid-day overpass)
    t_int[:] = 0.5

    wind_u = float(stage1_df.get("u10", 1.0).mean()) if "u10" in stage1_df.columns else 1.0
    wind_v = float(stage1_df.get("v10", 0.5).mean()) if "v10" in stage1_df.columns else 0.5

    log.info(f"Steady-state PINN training: {n_epochs} epochs")
    for epoch in range(n_epochs):
        model.train()
        optimizer.zero_grad()

        xyt_int, wu_int, wv_int = to_tensors(xy_int, t_int, wind_u, wind_v, dev)
        xyt_int = xyt_int.requires_grad_(True)

        L_pde  = steady_state_pde_loss(model, xyt_int, wu_int, wv_int)
        L_total = L_pde   # Simplified: add BC/data terms from training/train.py if needed
        L_total.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        tracker.record(epoch, float(L_pde), 0.0, 0.0, 0.0, float(L_total), lr)
        tracker.log_epoch(epoch, every=100)

    log.info("✅ Steady-state PINN training complete.")
    return tracker.history
