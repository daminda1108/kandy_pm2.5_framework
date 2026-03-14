"""
pde_residual_v3.py — Steady-state PDE residual for FourierPINNV3.

PDE (quasi-steady-state advection-diffusion with anisotropic K and wet removal):
    R = u·∂C/∂x + v·∂C/∂y
          - ∂(Kx·∂C/∂x)/∂x - ∂(Ky·∂C/∂y)/∂y
          - S + (v_d + Λ·P)·C

Physical constants:
    v_d = 0.003 m/s dry deposition velocity (Seinfeld & Pandis, fixed)
    H   = 30.0 m  representative mixed-layer depth for removal rate
    λ_dry = v_d / H = 1.0e-4 s⁻¹

    Λ   = 4.5e-4 s⁻¹·(mm/h)⁻¹  below-cloud scavenging coefficient
    P   = precipitation [mm/h] (from ERA5 'tp')

Gradient flow notes:
    xyt.requires_grad_(True) must be set BEFORE calling this function
    (or the caller must pass xyt with requires_grad already True).

    K decomposition in v3 (factored):
      Kx = K_base(blh_norm, t_norm) × gx(x_norm, y_norm, elev_norm)
    where t_norm = xyt[:,2:3] and x_norm, y_norm are xyt[:,0:1], xyt[:,1:2].

    Both K_base and gx depend on components of xyt:
      - K_base depends on t_norm = xyt[:,2:3] → propagates ∂K_base/∂t through autograd
      - gx depends on x_norm = xyt[:,0:1] → propagates ∂gx/∂x (the correct physical gradient)
    So ∂(Kx·∂C/∂x)/∂x accounts for both ∂gx/∂x and ∂(K_base·gx)/∂x correctly.

    blh is passed as a separate tensor (NOT from xyt), so ∂Kx/∂blh is NOT
    included in the xyt gradient graph. This is physically correct: BLH is an
    external ERA5 input, not a PDE variable being solved for.

Residual magnitude guard:
    If max(|R|) > 1e6, R is rescaled to prevent v12-type gradient explosion
    when PDE weight activates after a period without PDE supervision.
    This is a soft safety net — the curriculum should keep residuals bounded
    by maintaining λ_pde > 0 throughout training (v8/v13 lesson).
"""

import logging
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("pde_residual_v3")

# Physical constants
LAMBDA_DRY   = 1.0e-4    # s⁻¹  dry removal rate (v_d=0.003 m/s / H=30m)
LAMBDA_WET   = 4.5e-4    # s⁻¹·(mm/h)⁻¹  below-cloud scavenging

# Explosion guard threshold
_R_MAX_GUARD = 1.0e6


def pde_residual_v3(
    model,
    xyt:      "torch.Tensor",   # (N, 3) [x_norm, y_norm, t_norm] — requires_grad=True
    wind_u:   "torch.Tensor",   # (N, 1) zonal wind u [m/s]
    wind_v:   "torch.Tensor",   # (N, 1) meridional wind v [m/s]
    precip:   "torch.Tensor",   # (N, 1) precipitation [mm/h]; None → no wet removal
    blh:      "torch.Tensor",   # (N, 1) normalised BLH = BLH_m / 2000.0
    elev:     "torch.Tensor",   # (N, 1) normalised elevation ∈ [0, 1]; None → 0.5
) -> "torch.Tensor":
    """
    Compute steady-state PDE residual R(x,y) at collocation points.

    Args:
        model   : FourierPINNV3 instance
        xyt     : (N, 3) MUST have requires_grad=True before calling
        wind_u  : (N, 1) u-component wind [m/s]
        wind_v  : (N, 1) v-component wind [m/s]
        precip  : (N, 1) precipitation [mm/h]; pass None or zeros for dry conditions
        blh     : (N, 1) normalised BLH (BLH_m / 2000.0)
        elev    : (N, 1) normalised elevation; None → defaults to 0.5 in model.forward

    Returns:
        R : (N, 1) PDE residual — ideally near zero at solution
    """
    import torch

    # Ensure xyt is in the autograd graph
    if not xyt.requires_grad:
        xyt = xyt.requires_grad_(True)

    # Forward pass — all outputs depend on xyt through the autograd graph:
    #   C: through SpatialEmbedding(xyt[:,0:2]) + TemporalEncoding(xyt[:,2:3]) → trunk
    #   Kx,Ky: through KAnisoNet(xyt[:,0:1], xyt[:,1:2], elev) ×
    #                  KBaseNet(blh, xyt[:,2:3])
    #   S: through AlphaNet(xyt[:,2:3]) × R_interp(xyt[:,0:1], xyt[:,1:2])
    C, (Kx, Ky, S) = model(xyt, blh=blh, elev=elev)

    go = torch.ones_like(C)

    # ── First-order spatial derivatives of C ─────────────────────────────────
    # Intentionally omit the t-column gradient (∂C/∂t ≡ 0 in steady-state).
    grads = torch.autograd.grad(
        C, xyt, grad_outputs=go, create_graph=True
    )[0]                       # (N, 3)
    dC_dx = grads[:, 0:1]     # (N, 1)
    dC_dy = grads[:, 1:2]     # (N, 1)

    # ── Diffusive flux divergence ─────────────────────────────────────────────
    # d/dx(Kx · ∂C/∂x): Kx depends on xyt[:,0:1] via KAnisoNet → product rule
    # ∂/∂x(Kx · dC_dx) = (∂Kx/∂x)(dC_dx) + Kx(∂²C/∂x²)
    flux_x = Kx * dC_dx       # (N, 1)
    flux_y = Ky * dC_dy       # (N, 1)

    d_flux_x = torch.autograd.grad(
        flux_x, xyt, grad_outputs=go, create_graph=True
    )[0][:, 0:1]               # ∂(Kx·∂C/∂x)/∂x — (N, 1)

    d_flux_y = torch.autograd.grad(
        flux_y, xyt, grad_outputs=go, create_graph=True
    )[0][:, 1:2]               # ∂(Ky·∂C/∂y)/∂y — (N, 1)

    # ── Removal term ──────────────────────────────────────────────────────────
    # (λ_dry + Λ·P) · C
    if precip is not None:
        removal_rate = LAMBDA_DRY + LAMBDA_WET * precip   # (N, 1)
    else:
        removal_rate = LAMBDA_DRY                          # scalar

    # ── PDE residual ─────────────────────────────────────────────────────────
    # R = advection - diffusion divergence - S + removal·C
    R = (wind_u * dC_dx
         + wind_v * dC_dy
         - d_flux_x
         - d_flux_y
         - S
         + removal_rate * C)

    # ── Explosion guard ───────────────────────────────────────────────────────
    r_max = R.abs().max()
    if r_max.item() > _R_MAX_GUARD:
        scale = _R_MAX_GUARD / r_max.detach()
        R = R * scale
        log.warning(
            f"PDE residual explosion guard triggered: "
            f"max|R|={r_max.item():.3e} > {_R_MAX_GUARD:.0e}. "
            f"Rescaled by {scale.item():.3e}. "
            "Check curriculum λ_pde — should remain > 0 throughout training."
        )

    return R
