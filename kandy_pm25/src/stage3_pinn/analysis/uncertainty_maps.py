"""
uncertainty_maps.py — Dual uncertainty quantification for Stage 3 PINN output.

Two sources of uncertainty (§2.12 of RESEARCH_PROJECT_DESIGN.md):

1. EPISTEMIC UQ (MC Dropout): model weight uncertainty from limited training data.
   Run T=50 stochastic forward passes with dropout active at inference time.
   σ²_epistemic = Var_T[C(x,y,t)]

2. ALEATORIC UQ (PDE residual): local physics constraint violation.
   High PDE residual = the model is uncertain about the local physics.
   σ²_aleatoric = |R(x,y,t)|² / |R|²_max  (normalised residual)

COMBINED uncertainty:
   σ²_total = σ²_epistemic + σ²_aleatoric

Produces:
  - Epistemic uncertainty map (where the model "doesn't know")
  - Aleatoric uncertainty map (where physics is violated)
  - Combined uncertainty map
  - Uncertainty-weighted PM2.5 estimate

Victory condition (§3.2): Combined uncertainty < 3 µg/m³ over 85% of the domain.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT, MODELS_DIR, FIGURES_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("uncertainty_maps")

# MC Dropout settings
MC_PASSES = 50
DROPOUT_RATE_INFERENCE = 0.1   # Keep low to avoid distribution shift

# Victory condition threshold
UQ_COVERAGE_THRESHOLD  = 0.85  # 85% of domain must have σ_total < 3 µg/m³
UQ_VALUE_THRESHOLD     = 3.0   # µg/m³


def mc_dropout_uncertainty(
    model,
    domain,
    t_norm: float = 0.5,
    n_passes: int = MC_PASSES,
    device=None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Estimate epistemic uncertainty via Monte Carlo Dropout.

    Keeps dropout ACTIVE at inference (model.train() mode but no gradient).
    Returns mean and standard deviation across T forward passes.

    Args:
        model    : FourierPINN (must have dropout layers)
        domain   : KandyDomain
        t_norm   : Normalised time
        n_passes : Number of MC samples T
        device   : torch.device

    Returns:
        (mean_C, std_C) — arrays of shape (n_grid_points,)
    """
    try:
        import torch
    except ImportError:
        raise ImportError("PyTorch required")

    dev     = device or torch.device("cpu")
    inputs  = torch.tensor(domain.flat_inputs(t_norm), dtype=torch.float32, device=dev)

    model.train()   # Keeps BatchNorm/Dropout stochastic
    preds = []
    with torch.no_grad():
        for _ in range(n_passes):
            C, _ = model(inputs)
            preds.append(C.squeeze().cpu().numpy())

    preds_arr = np.stack(preds, axis=0)   # (T, N)
    mean_C    = preds_arr.mean(axis=0)
    std_C     = preds_arr.std(axis=0)

    log.info(f"MC Dropout ({n_passes} passes): mean C={mean_C.mean():.3f}, "
             f"epistemic σ={std_C.mean():.3f} µg/m³")
    return mean_C, std_C


def pde_residual_uncertainty(
    model,
    domain,
    wind_u_mean: float,
    wind_v_mean: float,
    t_norm: float = 0.5,
    device=None,
) -> np.ndarray:
    """
    Compute normalised PDE residual as a measure of aleatoric uncertainty.

    σ²_aleatoric(x,y) ∝ |R(x,y)|² / max(|R|²)

    High residual = physics equation is locally violated = model uncertain about
    the advection/diffusion balance in that region.

    Returns:
        residual_norm : (N,) normalised residual [0, 1]
    """
    try:
        import torch
        from src.stage3_pinn.physics.advection_diffusion import pde_residual
    except ImportError:
        log.warning("Cannot compute PDE residual uncertainty — returning zeros")
        return np.zeros(domain.n_points())

    dev    = device or torch.device("cpu")
    n      = domain.n_points()
    inputs = torch.tensor(domain.flat_inputs(t_norm), dtype=torch.float32, device=dev)
    inputs = inputs.requires_grad_(True)

    wu = torch.full((n, 1), wind_u_mean, dtype=torch.float32, device=dev)
    wv = torch.full((n, 1), wind_v_mean, dtype=torch.float32, device=dev)

    model.eval()
    R = pde_residual(model, inputs, wu, wv)
    R_np = R.detach().cpu().numpy().ravel()
    R2   = R_np ** 2
    residual_norm = R2 / (R2.max() + 1e-9)  # Normalise to [0,1]

    log.info(f"PDE residual uncertainty: max={R2.max():.4f}, mean={R2.mean():.4f}")
    return residual_norm


def compute_combined_uncertainty(
    sigma_epistemic: np.ndarray,
    sigma_aleatoric_norm: np.ndarray,
    aleatoric_scale: float = 3.0,
) -> np.ndarray:
    """
    Combine epistemic and aleatoric uncertainties.

        σ_total = sqrt(σ²_epistemic + (scale × σ_aleatoric_norm)²)

    The aleatoric_scale converts the normalised residual to µg/m³ units.
    Default scale=3.0 µg/m³ is based on RMSE of Stage 1 predictions.

    Returns:
        sigma_total: (N,) combined uncertainty [µg/m³]
    """
    sigma_aleatoric = aleatoric_scale * sigma_aleatoric_norm
    sigma_total     = np.sqrt(sigma_epistemic ** 2 + sigma_aleatoric ** 2)
    coverage = (sigma_total < UQ_VALUE_THRESHOLD).mean()
    passed   = coverage >= UQ_COVERAGE_THRESHOLD
    log.info(f"Combined UQ: σ_total mean={sigma_total.mean():.3f} µg/m³, "
             f"coverage <{UQ_VALUE_THRESHOLD}: {coverage:.1%} — {'✅ PASS' if passed else '❌ FAIL'}")
    return sigma_total


def plot_uncertainty_maps(
    domain,
    mean_C:     np.ndarray,
    sigma_epist: np.ndarray,
    sigma_aleat: np.ndarray,
    sigma_total: np.ndarray,
    save_path: Optional[str] = None,
) -> None:
    """Plot 4-panel uncertainty map: mean C, epistemic, aleatoric, total."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not available"); return

    lat = domain.lat_grid.ravel()
    lon = domain.lon_grid.ravel()
    fig, axes = plt.subplots(1, 4, figsize=(22, 5), constrained_layout=True)
    panels = [
        (mean_C,      "Mean PM2.5 (µg/m³)", "YlOrRd"),
        (sigma_epist, "Epistemic σ (µg/m³)", "Blues"),
        (sigma_aleat, "Aleatoric σ (norm)",   "Oranges"),
        (sigma_total, "Total σ (µg/m³)",       "Purples"),
    ]
    fig.suptitle("Stage 3 PINN — Dual Uncertainty Quantification", fontsize=13)
    for ax, (data, title, cmap) in zip(axes, panels):
        sc = ax.scatter(lon, lat, c=data, cmap=cmap, s=4, alpha=0.85)
        plt.colorbar(sc, ax=ax)
        ax.set_title(title, fontsize=10); ax.grid(alpha=0.3)

    out = save_path or str(FIGURES_DIR / "uncertainty_maps.png")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close()
    log.info(f"Uncertainty maps saved → {out}")


def run_uq_analysis(
    model, domain,
    wind_u: float = 1.0, wind_v: float = 0.5,
    t_norm: float = 0.5, save: bool = True,
) -> pd.DataFrame:
    """Master runner: epistemic + aleatoric UQ → combined map → plot."""
    mean_C, sigma_e = mc_dropout_uncertainty(model, domain, t_norm)
    sigma_a_norm    = pde_residual_uncertainty(model, domain, wind_u, wind_v, t_norm)
    sigma_total     = compute_combined_uncertainty(sigma_e, sigma_a_norm)

    out_df = pd.DataFrame({
        "lat":     domain.lat_grid.ravel(),
        "lon":     domain.lon_grid.ravel(),
        "pm25_mean":        mean_C,
        "sigma_epistemic":  sigma_e,
        "sigma_aleatoric":  sigma_a_norm * 3.0,
        "sigma_total":      sigma_total,
    })
    if save:
        plot_uncertainty_maps(domain, mean_C, sigma_e, sigma_a_norm, sigma_total)
        out_df.to_csv(MODELS_DIR / "stage3_pinn" / "uncertainty_maps.csv", index=False)
        log.info("UQ analysis complete.")
    return out_df
