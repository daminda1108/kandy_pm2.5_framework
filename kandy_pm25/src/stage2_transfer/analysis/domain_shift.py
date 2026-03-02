"""
domain_shift.py — Quantify domain shift between source (Medellín) and target (Kandy/Chiang Mai).

Domain shift analysis helps explain WHY transfer works or fails.
Two types of shift are assessed:

1. FEATURE SHIFT — Does the distribution of ERA5 wind, BLH, precip differ
   significantly between Medellín and Kandy?
   Method: Maximum Mean Discrepancy (MMD) or Jensen-Shannon divergence.

2. K-MAGNITUDE SHIFT — Does the discovered diffusivity K in the source domain
   predict a plausible K in the target domain?
   Method: Compare K histogram between source and target application.

See §2.7 of RESEARCH_PROJECT_DESIGN.md for the K ratio thresholds.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT, MODELS_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("domain_shift")

ANALYSIS_DIR = MODELS_DIR / "stage2_pretrain" / "domain_shift"


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE SHIFT
# ─────────────────────────────────────────────────────────────────────────────

def jensen_shannon_divergence(p: np.ndarray, q: np.ndarray, n_bins: int = 50) -> float:
    """
    Compute Jensen-Shannon divergence between two empirical distributions.
    JSD = 0 → identical, JSD = 1 → maximally different.
    """
    p_hist, edges = np.histogram(p, bins=n_bins, density=True)
    q_hist, _     = np.histogram(q, bins=edges, density=True)

    eps = 1e-10
    p_norm = p_hist + eps
    q_norm = q_hist + eps
    m = 0.5 * (p_norm + q_norm)

    jsd = 0.5 * np.sum(p_norm * np.log(p_norm / m)) + 0.5 * np.sum(q_norm * np.log(q_norm / m))
    return float(np.clip(jsd / np.log(2), 0, 1))  # Normalise to [0,1]


def compute_feature_shift(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    features: List[str],
) -> pd.DataFrame:
    """
    Compute Jensen-Shannon divergence for each meteorological feature between
    source (Medellín) and target (Kandy or Chiang Mai) domains.

    JSD > 0.5 on wind or BLH → significant domain shift → advection pattern differs.

    Args:
        source_df : ERA5 feature DataFrame for source domain
        target_df : ERA5 feature DataFrame for target domain
        features  : List of feature column names to compare

    Returns:
        DataFrame with columns: feature, jsd, shift_level
    """
    results = []
    for feat in features:
        if feat not in source_df.columns or feat not in target_df.columns:
            log.warning(f"Feature '{feat}' missing in one or both domains — skipping")
            continue
        src = source_df[feat].dropna().values
        tgt = target_df[feat].dropna().values
        jsd = jensen_shannon_divergence(src, tgt)
        shift_level = "low" if jsd < 0.2 else ("moderate" if jsd < 0.5 else "high")
        results.append({"feature": feat, "jsd": round(jsd, 4), "shift_level": shift_level})
        log.info(f"  {feat}: JSD={jsd:.3f} ({shift_level} shift)")

    df = pd.DataFrame(results).sort_values("jsd", ascending=False)
    n_high = (df["shift_level"] == "high").sum()
    if n_high > 0:
        log.warning(f"{n_high} features with HIGH domain shift — transfer may be harder")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# K-MAGNITUDE SHIFT
# ─────────────────────────────────────────────────────────────────────────────

def compute_k_shift(
    k_source: np.ndarray,
    k_target: np.ndarray,
) -> Dict:
    """
    Compare diffusivity K magnitude between source and target domains.

    Key diagnostic for the transfer gate:
      ratio = median(K_target) / median(K_source)
      ratio < 2   → minimal K shift → transfer good
      ratio 2–10  → moderate shift → partial unfreeze
      ratio > 10  → catastrophic shift → cold start

    Returns dict with ratio, JSD, and interpretation.
    """
    ks = k_source[~np.isnan(k_source)]
    kt = k_target[~np.isnan(k_target)]

    ratio = float(np.median(kt) / (np.median(ks) + 1e-9))
    jsd   = jensen_shannon_divergence(ks, kt, n_bins=30)

    if ratio < 2:
        interpretation = "minimal_shift"
    elif ratio < 10:
        interpretation = "moderate_shift"
    else:
        interpretation = "catastrophic_shift"

    result = {
        "K_source_median": round(float(np.median(ks)), 4),
        "K_target_median": round(float(np.median(kt)), 4),
        "K_ratio":         round(ratio, 3),
        "K_jsd":           round(jsd, 4),
        "interpretation":  interpretation,
    }
    icon = {"minimal_shift": "✅", "moderate_shift": "⚠️", "catastrophic_shift": "❌"}[interpretation]
    log.info(f"K-magnitude shift: ratio={ratio:.2f}, JSD={jsd:.3f} → {icon} {interpretation}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MASTER RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_domain_shift_analysis(
    source_era5: pd.DataFrame,
    target_era5: pd.DataFrame,
    k_source:    np.ndarray,
    k_target:    np.ndarray,
    met_features: List[str] = None,
    save: bool = True,
) -> Dict:
    """
    Full domain shift analysis: feature shift + K-magnitude shift.

    Args:
        source_era5  : ERA5 DataFrame for source domain (Medellín)
        target_era5  : ERA5 DataFrame for target domain (Kandy or Chiang Mai)
        k_source     : Discovered K values from source domain training
        k_target     : K values from target domain (zero-shot or fine-tuned)
        met_features : ERA5 variable names to compare (default: wind/BLH/precip)
        save         : Save results to CSV

    Returns:
        Dict with feature_shift DataFrame and k_shift Dict
    """
    if met_features is None:
        met_features = ["u10", "v10", "blh", "tp", "t2m"]

    log.info("═══ DOMAIN SHIFT ANALYSIS ═══")
    feature_shift = compute_feature_shift(source_era5, target_era5, met_features)
    k_shift = compute_k_shift(k_source, k_target)

    if save:
        ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
        feature_shift.to_csv(ANALYSIS_DIR / "feature_shift_jsd.csv", index=False)
        pd.DataFrame([k_shift]).to_csv(ANALYSIS_DIR / "k_magnitude_shift.csv", index=False)
        log.info(f"Domain shift results saved → {ANALYSIS_DIR}")

    return {"feature_shift": feature_shift, "k_shift": k_shift}
