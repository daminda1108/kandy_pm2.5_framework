"""
DEPRECATED — pre-FourierPINNV3 transient PINN prototype.

Status (2026-05-08, audit §B.5): NOT in the active import graph except by `synthetic_inverse_validation.py`
(a one-off validation script). The current TD-PDE PINN is `models/fourier_pinn_v3.py` (76,261 params,
verified architecture; canonical for paper §3.2). This older prototype predates the v3 architecture
redesign and uses the deprecated `physics/advection_diffusion.py` PDE residual rather than the active
`physics/pde_residual_v3.py`.

Do not import from current code paths. Retained only to keep `synthetic_inverse_validation.py` runnable
for archival purposes.

────────────────────────────────────────────────────────────────────────────

pinn_transient.py — Time-dependent PINN option for Kandy PM2.5 (Option B, §2.10).

Solves the full transient advection-diffusion PDE including ∂C/∂t:
    ∂C/∂t + u·∂C/∂x + v·∂C/∂y = ∂/∂x(Kx·∂C/∂x) + ∂/∂y(Ky·∂C/∂y) + S - λC

Enables:
  - Full diurnal PM2.5 cycle (katabatic flushing at night, daytime accumulation)
  - Time-varying K(x,y,t) — captures morning/evening mixing transitions
  - Propagation of rush-hour S peaks across the valley

Use when:
  - Hourly TROPOMI/sensor data becomes available (post-2024)
  - Diurnal cycle is scientifically important for the paper

Note: ~2× more collocation points needed (adds t dimension). Training is slower.
Initial training uses the steady-state warm-up (pinn_steady.py) then continues transient.

See §2.10 of RESEARCH_PROJECT_DESIGN.md for the design decision.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("pinn_transient")


def solve_transient(
    model,
    stage1_df: "pd.DataFrame",
    n_epochs:    int = 1000,
    lr:          float = 5e-4,
    warm_up_steady: bool = True,
    steady_epochs:  int = 100,
    device=None,
) -> list:
    """
    Transient PINN training loop (full PDE including ∂C/∂t).

    Two-phase strategy (§2.10):
      Phase 1 (optional warm-up): Train steady-state PDE for steady_epochs.
                This gives a good initialisation for K and S before introducing ∂C/∂t.
      Phase 2: Continue with full transient PDE. Collocations span all times
               t ∈ [0, 1] uniformly.

    Args:
        model           : FourierPINN model
        stage1_df       : Stage 1 predictions DataFrame
        n_epochs        : Total transient epochs (excluding steady warm-up)
        lr              : Learning rate
        warm_up_steady  : Run steady-state warm-up first
        steady_epochs   : Number of warm-up steady epochs
        device          : torch.device

    Returns:
        loss_history : Combined (steady + transient) loss history
    """
    try:
        import torch
        import torch.optim as optim
    except ImportError:
        raise ImportError("PyTorch required")

    from src.stage3_pinn.training.collocation import sample_uniform, to_tensors
    from src.stage3_pinn.physics.advection_diffusion import pde_loss
    from src.stage3_pinn.training.loss_functions import LossTracker
    from config import KANDY_PINN_BBOX, N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY

    dev       = device or torch.device("cpu")
    model.to(dev)
    history   = []

    # ── Phase 1: Steady warm-up ──────────────────────────────────────────────
    if warm_up_steady:
        log.info(f"Phase 1: Steady-state warm-up ({steady_epochs} epochs) …")
        from src.stage3_pinn.models.pinn_steady import solve_steady_state
        steady_hist = solve_steady_state(model, stage1_df, steady_epochs, lr, device)
        history.extend(steady_hist)
        log.info("Phase 1 complete → proceeding to transient training")

    # ── Phase 2: Full transient PINN ─────────────────────────────────────────
    log.info(f"Phase 2: Transient PINN training ({n_epochs} epochs) …")
    optimizer = optim.Adam(model.parameters(), lr=lr * 0.5)   # Lower LR after warm-up
    tracker   = LossTracker()

    wind_u = float(stage1_df.get("u10", 1.0).mean()) if "u10" in stage1_df.columns else 1.0
    wind_v = float(stage1_df.get("v10", 0.5).mean()) if "v10" in stage1_df.columns else 0.5

    for epoch in range(n_epochs):
        model.train()
        optimizer.zero_grad()

        # Transient: sample t uniformly in [0, 1]
        xy_int, t_int, _, _ = sample_uniform(
            N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY, KANDY_PINN_BBOX, t_max_norm=1.0
        )
        xyt_int, wu_int, wv_int = to_tensors(xy_int, t_int, wind_u, wind_v, dev)
        xyt_int = xyt_int.requires_grad_(True)

        L_pde   = pde_loss(model, xyt_int, wu_int, wv_int)
        L_pde.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        tracker.record(epoch + len(history), float(L_pde), 0.0, 0.0, 0.0, float(L_pde), lr * 0.5)
        tracker.log_epoch(epoch, every=100)

    history.extend(tracker.history)
    log.info("✅ Transient PINN training complete.")
    return history
