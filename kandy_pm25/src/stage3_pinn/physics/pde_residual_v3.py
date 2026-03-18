"""
pde_residual_v3.py — Steady-state PDE residual for FourierPINNV3.

PDE (quasi-steady-state advection-diffusion with anisotropic K and wet removal):
    R = u·∂C/∂x + v·∂C/∂y
          - ∂(Kx·∂C/∂x)/∂x - ∂(Ky·∂C/∂y)/∂y
          - S + (λ_dry + Λ·P)·C

All derivatives are in PHYSICAL coordinates [m].
xyt is in NORMALISED coordinates x_norm ∈ [-1,1], y_norm ∈ [-1,1].
Coordinate scaling (I3 fix — [-1,1] convention; domain spans 2 normalised units):
    x_phys = (x_norm + 1) / 2 × lx_m  →  ∂/∂x_phys = (2/lx_m) × ∂/∂x_norm
    alpha_x = 2 / lx_m  (applied twice for 2nd-order diffusion divergence)

    Physical advection  : u × dC_dx_norm × alpha_x
    Physical divergence : d_flux_x_norm × alpha_x²
    where flux_x = Kx × dC_dx_norm (keeps chain rule intact through autograd)

Physical constants:
    v_d = 0.003 m/s  dry deposition velocity (Seinfeld & Pandis, fixed)
    λ_dry = v_d / max(BLH_m, 30.0)  [s⁻¹]  (Fix F — BLH-dependent)
      If blh_m not supplied: λ_dry = 1.0e-4 s⁻¹ (fixed H=30m fallback)

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

    blh_m is physical BLH in metres (distinct from blh_norm = BLH_m / 2000.0).
    blh_m is detached from the autograd graph — used only for λ_dry computation.

Residual magnitude guard:
    If max(|R|) > 1e6, R is rescaled to prevent v12-type gradient explosion
    when PDE weight activates after a period without PDE supervision.
    This is a soft safety net — the curriculum should keep residuals bounded
    by maintaining λ_pde > 0 throughout training (v8/v13 lesson).
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("pde_residual_v3")

# Physical constants
_V_D         = 0.003      # m/s  dry deposition velocity
LAMBDA_DRY   = 1.0e-4    # s⁻¹  fallback: v_d=0.003 m/s / H=30m (used when blh_m=None)
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
    lx_m:     float = 15000.0,  # domain width  [m] — for coordinate scaling (Fix D)
    ly_m:     float = 15000.0,  # domain height [m] — for coordinate scaling (Fix D)
    blh_m:    "torch.Tensor | None" = None,  # (N,1) or (1,1) physical BLH [m] (Fix F)
) -> "torch.Tensor":
    """
    Compute steady-state PDE residual R(x,y) at collocation points.

    All gradient operations are applied in normalised coordinates, then scaled
    to physical units via alpha_x = 1/lx_m, alpha_y = 1/ly_m.

    Args:
        model   : FourierPINNV3 instance
        xyt     : (N, 3) MUST have requires_grad=True before calling
        wind_u  : (N, 1) u-component wind [m/s]
        wind_v  : (N, 1) v-component wind [m/s]
        precip  : (N, 1) precipitation [mm/h]; pass None or zeros for dry conditions
        blh     : (N, 1) normalised BLH (BLH_m / 2000.0) — enters model for K_base
        elev    : (N, 1) normalised elevation; None → defaults to 0.5 in model.forward
        lx_m    : domain width in metres (default 15000 m for Medellín/Kandy)
        ly_m    : domain height in metres (default 15000 m for Medellín/Kandy)
        blh_m   : physical BLH in metres for BLH-dependent λ_dry (Fix F).
                  If None: falls back to fixed LAMBDA_DRY = v_d/30m = 1e-4 s⁻¹.
                  Should be detached from grad graph (external ERA5 input).

    Returns:
        R : (N, 1) PDE residual — ideally near zero at solution
    """
    import torch

    # Coordinate scaling factors: ∂C/∂x_phys = dC_dx_norm * alpha_x
    # I3 fix: [-1,1] convention → domain spans 2 normalised units → alpha = 2/L_m
    alpha_x = 2.0 / lx_m
    alpha_y = 2.0 / ly_m

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

    # ── First-order spatial derivatives of C (in normalised coords) ──────────
    # Intentionally omit the t-column gradient (∂C/∂t ≡ 0 in steady-state).
    grads = torch.autograd.grad(
        C, xyt, grad_outputs=go, create_graph=True
    )[0]                       # (N, 3)
    dC_dx = grads[:, 0:1]     # ∂C/∂x_norm  (N, 1)
    dC_dy = grads[:, 1:2]     # ∂C/∂y_norm  (N, 1)

    # ── Diffusive flux divergence (physical coordinates) ─────────────────────
    # flux_x = Kx × dC_dx_norm  (normalised-coord flux — keeps Kx in autograd)
    # d/dx_phys(Kx × dC_dx_phys) = alpha_x² × ∂/∂x_norm(Kx × dC_dx_norm)
    # Derivation: dC_dx_phys = dC_dx_norm × alpha_x
    #   flux_phys = Kx × dC_dx_phys = Kx × dC_dx_norm × alpha_x
    #   d/dx_phys(flux_phys) = alpha_x × ∂/∂x_norm(Kx × dC_dx_norm × alpha_x)
    #                        = alpha_x² × ∂(Kx × dC_dx_norm)/∂x_norm
    flux_x = Kx * dC_dx       # (N, 1) normalised-coord flux
    flux_y = Ky * dC_dy       # (N, 1) normalised-coord flux

    d_flux_x_norm = torch.autograd.grad(
        flux_x, xyt, grad_outputs=go, create_graph=True
    )[0][:, 0:1]               # ∂(Kx·dC_dx_norm)/∂x_norm — (N, 1)

    d_flux_y_norm = torch.autograd.grad(
        flux_y, xyt, grad_outputs=go, create_graph=True
    )[0][:, 1:2]               # ∂(Ky·dC_dy_norm)/∂y_norm — (N, 1)

    # Scale to physical divergence
    d_flux_x = d_flux_x_norm * (alpha_x ** 2)
    d_flux_y = d_flux_y_norm * (alpha_y ** 2)

    # ── Removal term ──────────────────────────────────────────────────────────
    # λ_dry = v_d / max(BLH_m, 30.0)  — Fix F: BLH-dependent
    if blh_m is not None:
        # blh_m: physical BLH [m]; clamp to avoid division-by-zero near-surface
        lambda_dry = _V_D / blh_m.clamp(min=30.0)    # (N, 1) or broadcast
    else:
        lambda_dry = LAMBDA_DRY                        # scalar fallback

    if precip is not None:
        removal_rate = lambda_dry + LAMBDA_WET * precip   # (N, 1)
    else:
        removal_rate = lambda_dry                          # (N,1) or scalar

    # ── PDE residual (physical coordinates) ──────────────────────────────────
    # R = u·∂C/∂x_phys + v·∂C/∂y_phys
    #     - ∂(Kx·∂C/∂x_phys)/∂x_phys - ∂(Ky·∂C/∂y_phys)/∂y_phys
    #     - S + (λ_dry + Λ·P)·C
    R = (wind_u * dC_dx * alpha_x        # advection x  [µg/m³/s]
         + wind_v * dC_dy * alpha_y      # advection y
         - d_flux_x                      # diffusion x  [µg/m³/s]
         - d_flux_y                      # diffusion y
         - S                             # source       [µg/m³/s]
         + removal_rate * C)             # removal      [µg/m³/s]

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
