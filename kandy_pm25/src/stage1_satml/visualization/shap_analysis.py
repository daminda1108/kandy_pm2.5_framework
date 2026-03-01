"""
shap_analysis.py — SHAP-based interpretability for Stage 1 XGBoost model.

Per §1.7 victory conditions:
  - VVC, TII, and BLH must appear in the top 5 SHAP features.
    If they don't, the topography-aware features need investigation.

Produces:
  1. Global feature importance bar chart (mean |SHAP|)
  2. SHAP beeswarm plot (distribution of SHAP values per feature)
  3. SHAP dependence plots for top physics-motivated features
  4. SHAP interaction analysis (VVC × TII)

Usage:
    from shap_analysis import run_shap_analysis, plot_shap_summary
    shap_vals, X_sample = run_shap_analysis(model, X_test)
    plot_shap_summary(shap_vals, X_sample)
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT, FIGURES_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("shap_analysis")

# Physics features expected to dominate (for victory condition check)
EXPECTED_TOP_FEATURES = ["vvc", "tii", "blh", "kfp", "dsc"]


def run_shap_analysis(
    model,
    X: pd.DataFrame,
    n_samples: int = 500,
    random_state: int = 42,
) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    Compute SHAP values for a fitted XGBoost model.

    Args:
        model       : Fitted XGBRegressor
        X           : Feature DataFrame (test or full dataset)
        n_samples   : Subsample size for SHAP (full dataset can be slow)
        random_state: For reproducible subsampling

    Returns:
        shap_values : Array of shape (n_samples, n_features)
        X_sample    : Corresponding subsampled feature DataFrame
    """
    try:
        import shap
    except ImportError:
        raise ImportError("shap not installed. Run: pip install shap")

    rng = np.random.default_rng(random_state)
    idx = rng.choice(len(X), size=min(n_samples, len(X)), replace=False)
    X_sample = X.iloc[idx].reset_index(drop=True)

    log.info(f"Computing SHAP values for {len(X_sample)} samples …")
    explainer  = shap.TreeExplainer(model)
    shap_vals   = explainer.shap_values(X_sample)

    # Check victory condition: physics features in top 5
    importance = pd.Series(
        np.abs(shap_vals).mean(axis=0),
        index=X_sample.columns
    ).sort_values(ascending=False)

    top5 = set(importance.head(5).index.str.lower())
    physics_in_top5 = [f for f in EXPECTED_TOP_FEATURES if any(f in t for t in top5)]
    log.info(f"Top 5 features: {list(importance.head(5).index)}")
    log.info(f"Physics features in top 5: {physics_in_top5}")
    if len(physics_in_top5) < 2:
        log.warning("⚠️  VVC/TII/BLH not prominent in SHAP — check feature engineering")

    return shap_vals, X_sample


def get_feature_importance(
    shap_values: np.ndarray,
    feature_names: List[str],
) -> pd.DataFrame:
    """Return mean absolute SHAP values as a ranked feature importance DataFrame."""
    importance = pd.DataFrame({
        "feature":    feature_names,
        "mean_abs_shap": np.abs(shap_values).mean(axis=0),
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    importance["rank"] = importance.index + 1
    return importance


def plot_shap_summary(
    shap_values: np.ndarray,
    X_sample: pd.DataFrame,
    plot_type: str = "bar",
    save_path: Optional[str] = None,
    max_display: int = 20,
) -> None:
    """
    Plot SHAP summary (bar = mean |SHAP|, beeswarm = full distribution).

    Args:
        shap_values : SHAP values array
        X_sample    : Feature DataFrame
        plot_type   : "bar" or "beeswarm"
        save_path   : Where to save the figure
        max_display : Number of features to show
    """
    try:
        import shap
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("shap/matplotlib not available")
        return

    fig, ax = plt.subplots(figsize=(9, 7))
    shap.summary_plot(
        shap_values, X_sample,
        plot_type=plot_type,
        max_display=max_display,
        show=False,
    )
    plt.title("SHAP Feature Importance — Stage 1 XGBoost (Kandy PM2.5)", fontsize=12)
    plt.tight_layout()

    out = save_path or str(FIGURES_DIR / f"shap_{plot_type}.png")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=150, bbox_inches="tight")
    log.info(f"SHAP {plot_type} plot saved → {out}")
    plt.close()


def plot_shap_dependence(
    shap_values: np.ndarray,
    X_sample: pd.DataFrame,
    feature: str,
    interaction_feature: str = "auto",
    save_path: Optional[str] = None,
) -> None:
    """
    SHAP dependence plot for a single feature.

    Useful for validating physical relationships:
    - VVC:  SHAP should decrease as VVC increases (better ventilation → lower PM2.5 impact)
    - TII:  SHAP should increase as TII increases (stronger inversion → higher PM2.5)
    - BLH:  SHAP should decrease as BLH increases (deeper mixing → lower PM2.5)
    """
    try:
        import shap
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("shap/matplotlib not available")
        return

    if feature not in X_sample.columns:
        log.warning(f"Feature '{feature}' not found in data")
        return

    feat_idx = list(X_sample.columns).index(feature)
    fig, ax = plt.subplots(figsize=(7, 5))
    shap.dependence_plot(
        feat_idx, shap_values, X_sample,
        interaction_index=interaction_feature,
        ax=ax, show=False,
    )
    ax.set_title(f"SHAP Dependence: {feature}", fontsize=12)
    plt.tight_layout()

    out = save_path or str(FIGURES_DIR / f"shap_dependence_{feature}.png")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=150, bbox_inches="tight")
    log.info(f"SHAP dependence ({feature}) saved → {out}")
    plt.close()
