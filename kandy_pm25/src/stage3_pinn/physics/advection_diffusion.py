"""
DEPRECATED — pre-FourierPINNV3 PDE residual.

Status (2026-05-08, audit §B.5): superseded by `pde_residual_v3.py`. NOT in the active
import graph except for the deprecated prototype `models/pinn_transient.py` and a
diagnostic `analysis/uncertainty_maps.py`. Do not import from new code paths.

────────────────────────────────────────────────────────────────────────────

advection_diffusion.py — PDE residual for the anisotropic advection-diffusion equation
with wet and dry removal sinks.

The governing PDE for PM2.5 in the Kandy valley (§3.4 of RESEARCH_PROJECT_DESIGN.md):

    ∂C/∂t + u·∇C = ∇·(K∇C) − (v_d + Λ·P(x,t))·C + S(x,t)

Where:
    C(x,y,t)    : PM2.5 concentration [µg/m³]
    u(x,y,t)    : Downscaled zonal wind [m/s] (from wind_downscaling.py)
    v(x,y,t)    : Downscaled meridional wind [m/s]
    Kx(x,y,t)  : Anisotropic along-valley diffusivity [m²/s] (learned)
    Ky(x,y,t)  : Anisotropic cross-valley diffusivity [m²/s] (learned)
    S(x,y,t)    : Emission source term [µg/m³/s] (from source_term.py)
    v_d         : Dry deposition velocity [m/s] → first-order loss λ_dry = v_d / H_mix
    Λ           : Below-cloud scavenging coefficient = 4.5×10⁻⁴ s⁻¹·(mm/h)⁻¹
                  (Seinfeld & Pandis, Atmospheric Chemistry and Physics, Table 20.1, 3rd ed.)
    P(x,t)      : ERA5 precipitation rate [mm/h] at collocation points

Wet removal — why it's non-negotiable:
    During SW Monsoon (May–Sep) wet scavenging dominates over dry deposition by ~1 order of
    magnitude during rain events. A PINN trained on monsoon-period data without this term
    will learn systematically inflated K values to compensate for the missing sink.
    The discovered K field will then be physically wrong for monsoon months.
    Λ is FIXED from literature (not learned) because free Λ trades off with K and breaks
    identifiability (Seinfeld & Pandis §19.4).

Anisotropy: Kx ≠ Ky reflects valley channelling — diffusion is stronger
along the valley axis than perpendicular to it (Stull 1988 §8.2).
"""

import logging
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT, V_DEPOSITION

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("advection_diffusion")

# Below-cloud scavenging coefficient for PM2.5 (fixed from Seinfeld & Pandis Table 20.1).
# Units: s⁻¹ · (mm/h)⁻¹  →  effective loss rate = LAMBDA_WET × precip_mm_per_h × C
LAMBDA_WET: float = 4.5e-4

# Dry-deposition first-order loss rate: λ_dry = v_d / H_mix
# v_d = V_DEPOSITION = 0.003 m/s (urban PM2.5, Seinfeld & Pandis)
# H_mix = 30 m — reference near-surface mixed layer depth for deposition scaling
# Result: 0.003 / 30 = 1e-4 s⁻¹ — do NOT learn this (trades off with K)
_LAMBDA_DRY_DEFAULT: float = V_DEPOSITION / 30.0  # = 1e-4 s⁻¹


def pde_residual(
    model,
    xyt: "torch.Tensor",
    wind_u: "torch.Tensor",
    wind_v: "torch.Tensor",
    lambda_dry: float = _LAMBDA_DRY_DEFAULT,
    precip: Optional["torch.Tensor"] = None,
    blh:   Optional["torch.Tensor"] = None,
    elev:  Optional["torch.Tensor"] = None,
    steady: bool = False,
) -> "torch.Tensor":
    """
    Compute the anisotropic advection-diffusion PDE residual via autograd.

    Full transient form (steady=False):
        R = ∂C/∂t + u·∂C/∂x + v·∂C/∂y
              - ∂/∂x(Kx·∂C/∂x) - ∂/∂y(Ky·∂C/∂y)
              - S
              + (λ_dry + Λ·P) · C      ← combined dry + wet removal

    Quasi-steady-state form (steady=True):
        R = u·∂C/∂x + v·∂C/∂y
              - ∂/∂x(Kx·∂C/∂x) - ∂/∂y(Ky·∂C/∂y)
              - S
              + (λ_dry + Λ·P) · C      ← ∂C/∂t dropped algebraically

    With steady=True, xyt[:, 2] retains its h/24 value so SourceSubNet
    sees the correct hour-of-day for each ERA5 snapshot. The time-derivative
    term is suppressed in the residual formula, not by zeroing the t-column.

    Args:
        model      : FourierPINN — forward pass returns (C, (Kx, Ky, S))
        xyt        : (N, 3) tensor [x_norm, y_norm, t_norm] with requires_grad=True
        wind_u     : (N, 1) zonal wind [m/s]
        wind_v     : (N, 1) meridional wind [m/s]
        lambda_dry : Dry-deposition first-order loss rate λ_dry = v_d / H_mix [1/s].
                     Fixed = 1e-4 s⁻¹ (v_d=0.003 m/s, H_mix≈30m near surface).
                     Do NOT learn — trades off with K (Seinfeld & Pandis §19.4).
        precip     : (N, 1) ERA5 precipitation rate [mm/h] at collocation points.
                     None → wet deposition omitted (dry-season subset or unit tests).
        blh        : (N, 1) normalised BLH = BLH_m / 2000.0, ∈ [0, 1].
                     None → model uses its internal default (0.5).
        elev       : (N, 1) normalised elevation ∈ [0, 1].
                     None → model uses its internal default (0.5).
        steady     : If True, drop ∂C/∂t from residual (quasi-steady-state PDE).
                     Use for Stage 3 Kandy training with 3-hourly ERA5 snapshots.
                     If False, full transient PDE (Stage 2 Medellín pre-training).

    Returns:
        residual   : (N, 1) PDE residual at each collocation point
    """
    try:
        import torch
    except ImportError:
        raise ImportError("PyTorch required")

    xyt = xyt.requires_grad_(True)
    C, (Kx, Ky, S) = model(xyt, blh=blh, elev=elev)

    grad_outputs = torch.ones_like(C)

    # First derivatives of C
    grads_C = torch.autograd.grad(C, xyt, grad_outputs=grad_outputs, create_graph=True)[0]
    dC_dx = grads_C[:, 0:1]
    dC_dy = grads_C[:, 1:2]
    dC_dt = grads_C[:, 2:3]   # Zero for steady-state (dropped in residual when steady=True)

    # Diffusive flux: Kx·∂C/∂x and Ky·∂C/∂y
    flux_x = Kx * dC_dx
    flux_y = Ky * dC_dy

    # Second derivatives (divergence of diffusive flux)
    d_flux_x = torch.autograd.grad(
        flux_x, xyt, grad_outputs=grad_outputs, create_graph=True
    )[0][:, 0:1]
    d_flux_y = torch.autograd.grad(
        flux_y, xyt, grad_outputs=grad_outputs, create_graph=True
    )[0][:, 1:2]

    # Advection terms
    advection = wind_u * dC_dx + wind_v * dC_dy

    # Combined removal rate: dry deposition + wet scavenging
    # Units: [1/s] = [1/s] + [s⁻¹·(mm/h)⁻¹] × [mm/h]
    if precip is not None:
        removal_rate = lambda_dry + LAMBDA_WET * precip
    else:
        removal_rate = lambda_dry   # Dry-season or test mode (no wet removal)

    # PDE residual
    if steady:
        # Quasi-steady-state: drop ∂C/∂t. SourceSubNet still sees t=h/24.
        residual = advection - d_flux_x - d_flux_y - S + removal_rate * C
    else:
        # Full transient PDE: ∂C/∂t + advection − ∇·(K∇C) − S + removal·C = 0
        residual = dC_dt + advection - d_flux_x - d_flux_y - S + removal_rate * C
    return residual


def pde_loss(
    model,
    xyt: "torch.Tensor",
    wind_u: "torch.Tensor",
    wind_v: "torch.Tensor",
    lambda_dry: float = _LAMBDA_DRY_DEFAULT,
    precip: Optional["torch.Tensor"] = None,
    blh:   Optional["torch.Tensor"] = None,
    elev:  Optional["torch.Tensor"] = None,
) -> "torch.Tensor":
    """
    Mean squared PDE residual (full transient) — used as L_pde in Stage 2 training.

        L_pde = E[R(x,y,t)²]

    For Stage 3 quasi-steady-state training, use steady_state_pde_loss() instead.

    Args:
        blh    : (N, 1) normalised BLH. None → model default (0.5).
        elev   : (N, 1) normalised elevation. None → model default (0.5).
        precip : ERA5 precipitation rate [mm/h]. Pass None for dry-season data.

    Returns:
        Scalar mean-squared residual tensor
    """
    try:
        import torch
    except ImportError:
        raise ImportError("PyTorch required")

    R = pde_residual(model, xyt, wind_u, wind_v,
                     lambda_dry=lambda_dry, precip=precip, blh=blh, elev=elev)
    return torch.mean(R ** 2)


def steady_state_pde_loss(
    model,
    xyt: "torch.Tensor",
    wind_u: "torch.Tensor",
    wind_v: "torch.Tensor",
    precip: Optional["torch.Tensor"] = None,
    blh:   Optional["torch.Tensor"] = None,
    elev:  Optional["torch.Tensor"] = None,
) -> "torch.Tensor":
    """
    Quasi-steady-state PDE loss — drops ∂C/∂t algebraically from the residual.

    Use for Stage 3 Kandy training where the PDE is solved at discrete ERA5
    snapshots (h = 0, 3, 6, ..., 21). The t-column in xyt should be h/24 as
    set by the caller; it is NOT zeroed here, so SourceSubNet sees the correct
    hour-of-day for each snapshot.

    The steady-state approximation (∂C/∂t ≈ 0) is justified by:
      - ERA5 forcing varies on 3-h timescale; PINN concentration should
        track forcing without lag in the quasi-static limit.
      - Daily-mean observations cannot constrain ∂C/∂t directly.
      - 6× fewer collocation points vs. full transient formulation.

    Args:
        model  : FourierPINN
        xyt    : (N, 3) tensor with t ∈ {0/24, 3/24, …, 21/24} (requires_grad=True)
        wind_u : (N, 1) ERA5 zonal wind [m/s] for this snapshot
        wind_v : (N, 1) ERA5 meridional wind [m/s] for this snapshot
        precip : (N, 1) ERA5 precipitation rate [mm/h]. None → no wet removal.
        blh    : (N, 1) BLH / 2000.0. None → model default (0.5, BLH–K link inert).
        elev   : (N, 1) normalised DEM elevation. None → model default (0.5).

    Returns:
        Scalar mean-squared quasi-steady-state PDE residual
    """
    try:
        import torch
    except ImportError:
        raise ImportError("PyTorch required")

    R = pde_residual(model, xyt, wind_u, wind_v,
                     lambda_dry=_LAMBDA_DRY_DEFAULT, precip=precip,
                     blh=blh, elev=elev, steady=True)
    return torch.mean(R ** 2)
