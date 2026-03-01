"""
discover_diffusivity.py — Post-training analysis of the learned diffusivity K field.

After Stage 3 training, extract and analyse the learned Kx(x,y,t) and Ky(x,y,t) fields:

1. COMPARISON WITH STULL (1988): Plot K vs BLH and compare to parameterisations
   from Stull (1988) Mountain Meteorology Table 8-2. K should correlate with BLH.

2. ANISOTROPY MAPPING: Visualise Kx/Ky ratio across the Kandy domain.
   Expected: Kx > Ky along the main E-W valley axis.

3. DIURNAL CYCLE: Plot hourly-mean Kx and Ky — should show peaks at 14:00
   (daytime convective mixing) and troughs at 04:00 (nocturnal katabatic).

4. WIND COUPLING: Scatter K_eff = sqrt(Kx² + Ky²) vs wind speed — should show
   positive correlation (higher wind → more turbulent diffusion).

Victory condition (§3.2): K magnitude within physically plausible range [1, 500] m²/s
and Kx/Ky anisotropy ratio 1.5–10 — consistent with valley channelling theory.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT, MODELS_DIR, FIGURES_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("discover_diffusivity")

# Stull (1988) reference diffusivity vs BLH
# K ≈ 0.1 × u* × h_BLH  (simplified mixing-length formula)
STULL_K_PER_BLH = 0.05   # m²/s per metre of BLH (approximate from Table 8-2)


def extract_k_field(
    model,
    domain,
    t_norm: float = 0.5,
    device=None,
) -> pd.DataFrame:
    """
    Forward-pass the trained PINN over the full Kandy grid to extract K fields.

    Args:
        model   : Trained FourierPINN model
        domain  : KandyDomain object
        t_norm  : Normalised time at which to evaluate K (0.5 = mid-period)
        device  : torch.device

    Returns:
        DataFrame with columns: lat, lon, Kx, Ky, K_ratio, K_eff
    """
    try:
        import torch
    except ImportError:
        raise ImportError("PyTorch required")

    dev = device or torch.device("cpu")
    model.eval()

    with torch.no_grad():
        inputs = torch.tensor(domain.flat_inputs(t_norm), dtype=torch.float32, device=dev)
        _, (Kx, Ky, _) = model(inputs)
        Kx_np = Kx.squeeze().cpu().numpy()
        Ky_np = Ky.squeeze().cpu().numpy()

    df = pd.DataFrame({
        "lat":      domain.lat_grid.ravel(),
        "lon":      domain.lon_grid.ravel(),
        "Kx":       Kx_np,
        "Ky":       Ky_np,
        "K_ratio":  Kx_np / (Ky_np + 1e-9),
        "K_eff":    np.sqrt(Kx_np ** 2 + Ky_np ** 2),
    })
    log.info(f"K field extracted: Kx mean={Kx_np.mean():.2f}, Ky mean={Ky_np.mean():.2f}, "
             f"K_ratio mean={df['K_ratio'].mean():.2f}")
    return df


def compare_with_stull(k_df: pd.DataFrame, era5_blh: pd.Series) -> dict:
    """
    Compare discovered K with Stull (1988) mixing-length parameterisation.

    Expected: K ~ STULL_K_PER_BLH × BLH [m²/s].
    Correlation should be r > 0.3 (loose — BLH drives K but not exclusively).

    Args:
        k_df      : K field DataFrame (from extract_k_field)
        era5_blh  : Daily BLH values from ERA5 [m]

    Returns:
        Dict with correlation, Stull prediction, and ratio test.
    """
    if era5_blh.empty:
        log.warning("ERA5 BLH not provided — skipping Stull comparison")
        return {}

    k_mean  = float(k_df["K_eff"].mean())
    blh_mean = float(era5_blh.mean())
    stull_k  = STULL_K_PER_BLH * blh_mean
    ratio    = k_mean / (stull_k + 1e-9)

    result = {
        "K_eff_mean_ms2":   round(k_mean, 4),
        "BLH_mean_m":       round(blh_mean, 2),
        "Stull_K_est_ms2":  round(stull_k, 4),
        "K_Stull_ratio":    round(ratio, 3),
        "physically_plausible": 0.1 < ratio < 10.0,
    }
    status = "✅" if result["physically_plausible"] else "❌"
    log.info(f"Stull comparison: K_eff={k_mean:.2f}, Stull_ref={stull_k:.2f}, ratio={ratio:.2f} {status}")
    return result


def check_anisotropy(k_df: pd.DataFrame) -> dict:
    """
    Check that Kx/Ky anisotropy is within the physically expected range [1.5, 10].

    Kx = along-valley (E-W) diffusivity, Ky = cross-valley (N-S) diffusivity.
    Valley channelling should make Kx > Ky.
    """
    ratio_median = float(k_df["K_ratio"].median())
    ratio_iqr    = float(k_df["K_ratio"].quantile(0.75) - k_df["K_ratio"].quantile(0.25))
    passed = 1.5 <= ratio_median <= 10.0

    result = {
        "K_ratio_median":  round(ratio_median, 3),
        "K_ratio_IQR":     round(ratio_iqr, 3),
        "anisotropy_OK":   passed,
    }
    status = "✅ PASS" if passed else "❌ FAIL — K anisotropy outside physical range"
    log.info(f"Anisotropy: Kx/Ky median={ratio_median:.2f} {status}")
    return result


def plot_k_spatial(k_df: pd.DataFrame, save_path: Optional[str] = None) -> None:
    """Plot spatial maps of Kx, Ky, and K_ratio across the Kandy domain."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not available"); return

    fig, axes = plt.subplots(1, 3, figsize=(18, 5), constrained_layout=True)
    fields    = [("Kx", "along-valley (m²/s)"), ("Ky", "cross-valley (m²/s)"), ("K_ratio", "Kx/Ky")]
    cmaps     = ["viridis", "viridis", "RdYlGn"]

    for ax, (col, label), cmap in zip(axes, fields, cmaps):
        sc = ax.scatter(k_df["lon"], k_df["lat"], c=k_df[col], cmap=cmap, s=4, alpha=0.8)
        plt.colorbar(sc, ax=ax, label=label)
        ax.set_title(f"{col} — {label}", fontsize=11)
        ax.grid(alpha=0.3)

    fig.suptitle("Learned Diffusivity K Field — Kandy PINN Stage 3", fontsize=13)
    out = save_path or str(FIGURES_DIR / "k_spatial_map.png")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close()
    log.info(f"K spatial map saved → {out}")


def run_k_analysis(model, domain, era5_blh: pd.Series = None, save: bool = True) -> dict:
    """Master runner: extract K field, run all checks, produce plots."""
    k_df   = extract_k_field(model, domain)
    stull  = compare_with_stull(k_df, era5_blh if era5_blh is not None else pd.Series(dtype=float))
    aniso  = check_anisotropy(k_df)
    if save:
        plot_k_spatial(k_df)
        k_df.to_csv(MODELS_DIR / "stage3_pinn" / "k_field.csv", index=False)
        log.info("K field analysis complete.")
    return {"stull": stull, "anisotropy": aniso, "k_df": k_df}
