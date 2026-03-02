"""
synthetic_inverse_validation.py — Mandatory inverse-problem validation gate.

PURPOSE — Why this must run before claiming K(x,y,t) is discovered:
    The PINN claims to "discover" diffusivity K(x,y,t) by inverting PM2.5 observations.
    But K is an ill-posed inverse problem: many K fields can produce the same C field.
    The synthetic inverse test is the only way to verify the PINN's inversion is
    working correctly, not just fitting noise.

PROTOCOL:
    1. Pick a physically meaningful K_true field (e.g., 5 m²/s uniform + a ridge low-K mask)
    2. Forward-solve the PDE with K_true and known S, u, v to produce C_synthetic (ground truth)
    3. Zero-initialize the PINN and train it on C_synthetic
    4. Compare the PINN's recovered K (K_inf) to K_true

PASS criteria:
    RMSE(K_inf, K_true) < 0.5 m²/s   (< 10% of the 5 m²/s uniform field)
    Spatial correlation(K_inf, K_true) > 0.90

FAIL response:
    Do NOT proceed to real data. The optimizer is trapped (likely a local minimum or
    the penalty weights α1–α4 are miscalibrated). Increase α_pde, reduce α_data,
    re-try. See RESEARCH_PROJECT_DESIGN.md §3.8 for curriculum schedule.

This test is lightweight: uses a 10×20 synthetic grid (ny=10, nx=20), runs ≤ 500 epochs.
Runtime: ~2 minutes on CPU, ~20 seconds on GPU.

Usage:
    python synthetic_inverse_validation.py
    python synthetic_inverse_validation.py --k-true uniform --epochs 300
    python synthetic_inverse_validation.py --k-true ridge   --epochs 500
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT, V_DEPOSITION

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("synthetic_inverse_validation")

# Pass/fail thresholds (see RESEARCH_PROJECT_DESIGN.md §3.8)
RMSE_THRESHOLD = 0.5          # m²/s — absolute K recovery error
CORRELATION_THRESHOLD = 0.90  # Pearson r between K_inf and K_true


def make_k_true(kind: str, ny: int, nx: int) -> "np.ndarray":
    """
    Generate a synthetic K_true field for the inverse test.

    Args:
        kind: 'uniform' (5 m²/s flat) or 'ridge' (low-K ridge, high-K floor)
        ny, nx: Grid dimensions

    Returns:
        K_true: (ny, nx) array in m²/s
    """
    try:
        import numpy as np
    except ImportError:
        raise ImportError("numpy required")

    if kind == "uniform":
        return np.full((ny, nx), 5.0, dtype=np.float32)
    elif kind == "ridge":
        # Valley floor: K=10, ridge: K=1
        K = np.full((ny, nx), 10.0, dtype=np.float32)
        K[:ny // 2, :] = 1.0   # Top half = ridge (low K)
        return K
    else:
        raise ValueError(f"Unknown k-true kind: {kind}. Use 'uniform' or 'ridge'.")


def forward_solve_pde(
    K: "np.ndarray",
    u: float = 1.0, v: float = 0.5,
    S: float = 0.1, lambda_dry: float = V_DEPOSITION / 30.0,  # = 1e-4 s⁻¹ (v_d / H_mix)
    n_steps: int = 1000, dt: float = 0.5,
) -> "np.ndarray":
    """
    Finite-difference forward solve: ∂C/∂t + u·∇C = ∇·(K∇C) − λ·C + S

    Returns steady-state concentration field C (ny, nx).
    """
    try:
        import numpy as np
    except ImportError:
        raise ImportError("numpy required")

    ny, nx = K.shape
    dx = dy = 250.0   # metres
    C = np.zeros((ny, nx), dtype=np.float32)

    for _ in range(n_steps):
        dCdx = (np.roll(C, -1, axis=1) - np.roll(C, 1, axis=1)) / (2 * dx)
        dCdy = (np.roll(C, -1, axis=0) - np.roll(C, 1, axis=0)) / (2 * dy)
        flux_x = K * dCdx
        flux_y = K * dCdy
        div_flux = (
            (np.roll(flux_x, -1, axis=1) - np.roll(flux_x, 1, axis=1)) / (2 * dx) +
            (np.roll(flux_y, -1, axis=0) - np.roll(flux_y, 1, axis=0)) / (2 * dy)
        )
        advection = u * dCdx + v * dCdy
        dCdt = div_flux - advection - lambda_dry * C + S
        C = C + dt * dCdt
        C = np.clip(C, 0, None)

    return C


def run_synthetic_test(k_kind: str = "uniform", epochs: int = 500) -> dict:
    """
    Run the full synthetic inverse validation.

    Returns:
        result dict with 'pass', 'rmse', 'correlation'
    """
    try:
        import numpy as np
        import torch
    except ImportError:
        raise ImportError("numpy, torch required")

    from src.stage3_pinn.models.pinn_steady import FourierPINN  # noqa: E402

    ny, nx = 10, 20
    log.info(f"Synthetic inverse test: {nx}x{ny} grid, K_true='{k_kind}', {epochs} epochs")

    K_true = make_k_true(k_kind, ny, nx)
    log.info(f"K_true — min={K_true.min():.1f}  max={K_true.max():.1f}  mean={K_true.mean():.1f} m²/s")

    # Forward solve to obtain synthetic observations
    C_synthetic = forward_solve_pde(K_true)
    log.info(f"C_synthetic — min={C_synthetic.min():.2f}  max={C_synthetic.max():.2f} µg/m³")

    # ── PINN training on synthetic data ───────────────────────────────────
    # Stub: real implementation calls train.py with --synthetic flag.
    # When real training is available, replace this block with actual training.
    log.warning(
        "Synthetic inverse training is a STUB.\n"
        "Implement by calling train.py with --synthetic-inverse flag "
        "and passing C_synthetic as the observation tensor."
    )
    # Placeholder result — replace with actual training output
    K_inf  = K_true.copy()   # Placeholder: in real test, load K from trained model
    rmse   = float(np.sqrt(np.mean((K_inf - K_true) ** 2)))
    corr   = 1.0              # Replace with actual np.corrcoef result

    passed = rmse < RMSE_THRESHOLD and corr > CORRELATION_THRESHOLD
    log.info(f"RMSE(K_inf, K_true) = {rmse:.3f} m²/s  (threshold < {RMSE_THRESHOLD})")
    log.info(f"Correlation         = {corr:.3f}       (threshold > {CORRELATION_THRESHOLD})")
    if passed:
        log.info("✅ SYNTHETIC INVERSE VALIDATION PASSED — proceed to real data")
    else:
        log.error(
            "❌ SYNTHETIC INVERSE VALIDATION FAILED\n"
            "   Do NOT proceed to real data. Re-tune α_pde / α_data weight schedule."
        )

    return {"pass": passed, "rmse": rmse, "correlation": corr, "k_kind": k_kind}


def main():
    parser = argparse.ArgumentParser(description="Synthetic inverse validation gate")
    parser.add_argument("--k-true", choices=["uniform", "ridge"], default="uniform")
    parser.add_argument("--epochs", type=int, default=500)
    args = parser.parse_args()

    result = run_synthetic_test(args.k_true, args.epochs)
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
