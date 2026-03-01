"""
discover_sources.py — Post-training analysis of the learned emission source field S(x,y,t).

After Stage 3 training, extract and validate the discovered source strength S:

1. CORRELATION WITH OSM ROAD DENSITY: S should correlate strongly with road network
   density (r > 0.5) because traffic is the dominant PM2.5 source in Kandy city.

2. CORRELATION WITH TROPOMI NO₂: TROPOMI NO₂ column is a proxy for traffic exhaust.
   S should correlate with NO₂ at the km scale.

3. TEMPORAL PATTERN: S should peak during rush-hour windows (07:00–09:00 and 17:00–19:00
   local time) — combustion engines → PM2.5 → S elevated.

4. SEASONAL PATTERN: S should be higher in NE Monsoon (drier, more biomass burning)
   than SW Monsoon (wet season). If S is uniform in time, the K-S identification
   may have collapsed (degenerate solution).

Victory condition (§3.2): S-OSM correlation r > 0.5 AND
S not spatially uniform (spatial CV > 0.2).
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
log = logging.getLogger("discover_sources")

# Victory condition thresholds
S_OSM_CORR_THRESHOLD  = 0.5   # Minimum Pearson r(S, road_density)
S_SPATIAL_CV_MIN      = 0.2   # Minimum spatial coefficient of variation


def extract_source_field(
    model,
    domain,
    t_norm: float = 0.5,
    device=None,
) -> pd.DataFrame:
    """
    Extract the learned source field S(x,y,t) over the full Kandy grid.

    Args:
        model   : Trained FourierPINN
        domain  : KandyDomain object
        t_norm  : Normalised time (0=start, 1=end of study period)
        device  : torch.device

    Returns:
        DataFrame with columns: lat, lon, S
    """
    try:
        import torch
    except ImportError:
        raise ImportError("PyTorch required")

    dev = device or torch.device("cpu")
    model.eval()

    with torch.no_grad():
        inputs = torch.tensor(domain.flat_inputs(t_norm), dtype=torch.float32, device=dev)
        _, (_, _, S) = model(inputs)
        S_np = S.squeeze().cpu().numpy()

    df = pd.DataFrame({"lat": domain.lat_grid.ravel(), "lon": domain.lon_grid.ravel(), "S": S_np})
    log.info(f"S field extracted: mean={S_np.mean():.4f}, std={S_np.std():.4f}, CV={S_np.std()/(S_np.mean()+1e-9):.3f}")
    return df


def correlate_with_osm(s_df: pd.DataFrame, domain) -> dict:
    """
    Compute Pearson correlation between discovered S and OSM road density.

    Args:
        s_df   : Source field DataFrame (lat, lon, S)
        domain : KandyDomain with .road_density attribute

    Returns:
        Dict with r, p-value, and passed flag.
    """
    if domain.road_density is None:
        log.warning("OSM road density not loaded — skipping S-OSM correlation")
        return {"passed": None, "reason": "road_density not loaded"}

    from scipy.stats import pearsonr
    road_flat = domain.road_density.ravel()
    s_flat    = s_df["S"].values

    # Align lengths
    n = min(len(road_flat), len(s_flat))
    r, p = pearsonr(road_flat[:n], s_flat[:n])
    passed = r > S_OSM_CORR_THRESHOLD

    result = {
        "S_OSM_corr_r": round(float(r), 4),
        "S_OSM_p_value": round(float(p), 6),
        "passed": passed,
    }
    status = "✅ PASS" if passed else "❌ FAIL"
    log.info(f"S-OSM correlation: r={r:.3f}, p={p:.4f} — {status}")
    return result


def correlate_with_tropomi(s_df: pd.DataFrame, tropomi_no2_df: pd.DataFrame) -> dict:
    """
    Compute correlation between discovered S and TROPOMI NO₂ column density.

    TROPOMI NO₂ is provided at 3.5×5.5 km; bilinear interpolation to PINN grid needed.
    Both S and NO₂ log-transformed before correlation (both are right-skewed).

    Args:
        s_df          : Source field DataFrame
        tropomi_no2_df: DataFrame with lat, lon, no2_column (molecules/cm²)

    Returns:
        Dict with Pearson r and passed flag.
    """
    from scipy.stats import pearsonr

    if tropomi_no2_df.empty:
        log.warning("TROPOMI NO₂ not provided — skipping")
        return {"passed": None}

    # Merge on nearest grid point (simplified)
    merged = pd.merge_asof(
        s_df.sort_values("lat"), tropomi_no2_df.sort_values("lat"),
        on="lat", direction="nearest",
    )
    if merged.empty or "no2_column" not in merged.columns:
        return {"passed": None, "reason": "merge failed"}

    log_s   = np.log1p(merged["S"].clip(lower=0))
    log_no2 = np.log1p(merged["no2_column"].clip(lower=0))
    r, p = pearsonr(log_s, log_no2)
    passed = r > 0.3  # Weaker threshold — different physical footprint

    result = {"S_NO2_corr_r": round(float(r), 4), "S_NO2_p_value": round(float(p), 6), "passed": passed}
    status = "✅" if passed else "❌"
    log.info(f"S-TROPOMI-NO₂ correlation: r={r:.3f} — {status}")
    return result


def check_spatial_heterogeneity(s_df: pd.DataFrame) -> dict:
    """
    Check that S is spatially heterogeneous (not degenerate uniform field).

    If CV < S_SPATIAL_CV_MIN, the K-S inverse problem may have collapsed
    to a degenerate solution (K absorbed all spatial structure from S).
    """
    cv = float(s_df["S"].std() / (s_df["S"].mean() + 1e-9))
    passed = cv >= S_SPATIAL_CV_MIN
    result = {"S_spatial_CV": round(cv, 4), "passed": passed}
    status = "✅ Spatially heterogeneous" if passed else "❌ S is nearly uniform — check K-S degeneracy"
    log.info(f"S spatial CV: {cv:.3f} — {status}")
    return result


def plot_source_map(s_df: pd.DataFrame, save_path: Optional[str] = None) -> None:
    """Plot spatial map of the discovered source field S."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not available"); return

    fig, ax = plt.subplots(figsize=(8, 6))
    sc = ax.scatter(s_df["lon"], s_df["lat"], c=s_df["S"], cmap="hot_r", s=6, alpha=0.85)
    plt.colorbar(sc, ax=ax, label="S (µg/m³/s)")
    ax.set_title("Discovered Emission Source S(x,y) — Stage 3 PINN", fontsize=12)
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    ax.grid(alpha=0.3)

    out = save_path or str(FIGURES_DIR / "source_field_map.png")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close()
    log.info(f"Source field map saved → {out}")


def run_source_analysis(
    model, domain,
    tropomi_df: Optional[pd.DataFrame] = None,
    save: bool = True,
) -> dict:
    """Master runner: extract S field, correlate with OSM and TROPOMI, check heterogeneity."""
    s_df    = extract_source_field(model, domain)
    osm_r   = correlate_with_osm(s_df, domain)
    no2_r   = correlate_with_tropomi(s_df, tropomi_df if tropomi_df is not None else pd.DataFrame())
    hetero  = check_spatial_heterogeneity(s_df)

    if save:
        plot_source_map(s_df)
        s_df.to_csv(MODELS_DIR / "stage3_pinn" / "source_field.csv", index=False)
    return {"osm_corr": osm_r, "no2_corr": no2_r, "heterogeneity": hetero, "s_df": s_df}
