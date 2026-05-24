"""
convcnp_terrain.py — ConvCNP residual learner (Stage C).

Thin wrapper around `deepsensor.model.ConvNP` (Vaughan et al. GMD 2022;
Andersson et al. EDS 2023). The model takes a per-city task containing:

    Context (set 0): static terrain delta_z (xarray DataArray, lat × lon)
    Context (set 1): sparse station observations (pd.DataFrame indexed by
                     (time, lat, lon)) with columns
                       pm25            — additive residual (pm25_obs − c_prior_scaled)
                       blh_norm        — boundary-layer height / 2000 m
                       c_prior_norm    — c_prior_scaled / 100
                       sin_h, cos_h    — diurnal harmonics
                       sin_doy, cos_doy — annual harmonics
    Target:          subset of stations (pm25 column only)

and outputs a per-target-station predictive (μ, σ) over the residual. The
final PM2.5 prediction is `μ + c_prior_scaled` (added back at evaluation).

The canonical training/eval pipeline lives in
`src/stage3_pinn/training/loocv_convcnp.py`. The reported numerical results
(v11, 2026-05-16) were produced by the frozen Kaggle kernel
`data/processed/stage2/kaggle_kernel_convcnp_v11/convcnp_loocv_v11.py`,
which implements the same algorithm in a self-contained script.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from scipy.stats import norm

# deepsensor is a Kaggle/runtime dependency (not in requirements.txt because
# the canonical run environment is Kaggle T4×2 + uni-server T4×2). Importing
# at function call time so the module can be inspected without the dep.


# Architecture constants used in v10 / v11 (locked 2026-05-10)
UNET_CHANNELS    = (32, 64, 128)
LIKELIHOOD       = "gnp"                # = "lowrank" — heteroscedastic Gaussian
INTERNAL_DENSITY = 50                   # ConvNP grid density (points per 1×1 deg)


def build_convcnp_model(dp_ref, tl_ref,
                        unet_channels: Tuple[int, ...] = UNET_CHANNELS,
                        likelihood: str = LIKELIHOOD,
                        internal_density: int = INTERNAL_DENSITY):
    """
    Construct a ConvNP with the architecture used for Stage C v10/v11.

    Parameters
    ----------
    dp_ref : deepsensor.data.DataProcessor
        Reference DataProcessor (used to infer input/output schema).
    tl_ref : deepsensor.data.TaskLoader
        Reference TaskLoader (used to infer context/target structure).
    unet_channels : tuple[int, ...]
        UNet downsampling-path channel widths. Default (32, 64, 128).
    likelihood : str
        deepsensor likelihood key. Default "gnp" (= LowRankGaussianLikelihood,
        equivalent to "lowrank"). Other v10/v11-compatible options: "het"/"cnp".
        See gotcha #40 (CLAUDE.md) for Student-t workaround — not a config knob.
    internal_density : int
        Density of the internal ConvNP grid (points per 1×1 input-space unit).

    Returns
    -------
    deepsensor.model.ConvNP
        Constructed model. Total params: 625,989 for the v10/v11 defaults.
    """
    from deepsensor.model import ConvNP
    return ConvNP(
        dp_ref, tl_ref,
        unet_channels=unet_channels,
        likelihood=likelihood,
        internal_density=internal_density,
    )


def coverage_90(y_true: np.ndarray,
                y_mean: np.ndarray,
                y_std:  np.ndarray) -> float:
    """
    Fraction of observations falling inside the central 90% predictive
    interval given Gaussian predictive (μ, σ).

    The z-score is `norm.ppf(0.95) ≈ 1.6449` so the interval is symmetric
    around y_mean. Heteroscedastic σ means coverage is computed per-point.

    Used as the G4 gate metric (target [0.85, 0.95]) in v10/v11 LOOCV.
    """
    z  = norm.ppf(0.95)
    lo = y_mean - z * y_std
    hi = y_mean + z * y_std
    return float(((y_true >= lo) & (y_true <= hi)).mean())
