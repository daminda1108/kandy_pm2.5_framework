"""
calibration.py — Reliability diagram and calibration assessment for Stage 1 UQ.

Per §1.6 of RESEARCH_PROJECT_DESIGN.md, the 90% prediction intervals from
quantile regression must be empirically calibrated:
  - Reliability diagram: for each nominal coverage α, the empirical coverage
    (fraction of observations inside the interval) should match α within ±0.05.

Victory condition: empirical coverage within ±0.05 of diagonal for all α.

Usage:
    from calibration import assess_calibration, plot_reliability_diagram
    results = assess_calibration(y_obs, q_preds)
    plot_reliability_diagram(results, save_path="results/figures/calibration.png")
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import LOG_FORMAT, LOG_DATEFMT, QUANTILE_ALPHAS, FIGURES_DIR, MERGED_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("calibration")


# ─────────────────────────────────────────────────────────────────────────────
# CORE CALIBRATION ASSESSMENT
# ─────────────────────────────────────────────────────────────────────────────

def assess_calibration(
    y_obs: np.ndarray,
    quantile_predictions: Dict[float, np.ndarray],
    alphas: Optional[List[float]] = None,
    tolerance: float = 0.05,
) -> pd.DataFrame:
    """
    Compute empirical coverage for each nominal quantile level.

    For a well-calibrated quantile model:
        P(Y ≤ q̂_α) ≈ α   for all α

    For a 90% interval (q05, q95), the interval should contain ~90% of observations.

    Args:
        y_obs                : Observed PM2.5 values (n,)
        quantile_predictions : Dict mapping quantile level → predicted values
                               e.g. {0.05: q05_preds, 0.50: median_preds, 0.95: q95_preds}
        alphas               : Quantile levels to evaluate (defaults to QUANTILE_ALPHAS from config)
        tolerance            : Acceptable deviation from diagonal (default ±0.05)

    Returns:
        DataFrame with columns: alpha, empirical_coverage, deviation, within_tolerance
    """
    if alphas is None:
        alphas = QUANTILE_ALPHAS

    y = np.asarray(y_obs).ravel()
    mask = ~np.isnan(y)
    y = y[mask]

    records = []
    for alpha in alphas:
        if alpha not in quantile_predictions:
            log.warning(f"Quantile α={alpha} not in predictions — skipping")
            continue
        q_pred = np.asarray(quantile_predictions[alpha]).ravel()[mask]
        empirical_coverage = float((y <= q_pred).mean())
        deviation = abs(empirical_coverage - alpha)
        records.append({
            "alpha": alpha,
            "empirical_coverage": round(empirical_coverage, 4),
            "nominal_coverage":   round(alpha, 4),
            "deviation":          round(deviation, 4),
            "within_tolerance":   deviation <= tolerance,
        })

    results = pd.DataFrame(records)
    if not results.empty:
        pass_rate = results["within_tolerance"].mean()
        log.info(f"Calibration: {pass_rate*100:.0f}% of quantile levels within ±{tolerance} tolerance")
        if pass_rate < 1.0:
            log.warning("Some quantile levels are outside tolerance — consider recalibration")
    return results


def compute_prediction_interval_coverage(
    y_obs: np.ndarray,
    q_low: np.ndarray,
    q_high: np.ndarray,
    nominal_coverage: float = 0.90,
) -> Dict:
    """
    Check empirical coverage of a single prediction interval [q_low, q_high].

    Args:
        y_obs            : Observed PM2.5 (n,)
        q_low            : Lower bound predictions (n,) — e.g. q05
        q_high           : Upper bound predictions (n,) — e.g. q95
        nominal_coverage : Expected fraction inside the interval (e.g. 0.90)

    Returns:
        Dict with empirical_coverage, deviation, passed, interval_width_mean
    """
    y = np.asarray(y_obs).ravel()
    ql = np.asarray(q_low).ravel()
    qh = np.asarray(q_high).ravel()

    mask = ~(np.isnan(y) | np.isnan(ql) | np.isnan(qh))
    y, ql, qh = y[mask], ql[mask], qh[mask]

    inside = ((y >= ql) & (y <= qh)).mean()
    deviation = abs(float(inside) - nominal_coverage)
    result = {
        "empirical_coverage":  round(float(inside), 4),
        "nominal_coverage":    nominal_coverage,
        "deviation":           round(deviation, 4),
        "passed":              deviation <= 0.05,
        "interval_width_mean": round(float((qh - ql).mean()), 4),
        "n":                   int(mask.sum()),
    }
    log.info(
        f"PI coverage: {result['empirical_coverage']:.1%} (nominal={nominal_coverage:.1%}, "
        f"Δ={deviation:.3f}, {'✅ PASS' if result['passed'] else '❌ FAIL'})"
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# UNCERTAINTY STATISTICS
# ─────────────────────────────────────────────────────────────────────────────

def uncertainty_to_weight(
    q05: np.ndarray,
    q95: np.ndarray,
) -> np.ndarray:
    """
    Convert Stage 1 prediction intervals to inverse-variance weights for Stage 3.

    σ²_Stage1 = ((q95 - q05) / 3.29)²    [90% PI → σ₁.₆₄₅ on each tail]
    w(x,y,day) = 1 / (1 + σ²_Stage1)

    These weights down-weight uncertain Stage 1 pixels in the Stage 3 L_data loss.
    SW Monsoon cloud-gap days will have the widest intervals → lowest weights.

    Returns:
        weights: array same shape as q05, values in (0, 1]
    """
    sigma2 = ((np.asarray(q95) - np.asarray(q05)) / 3.29) ** 2
    weights = 1.0 / (1.0 + sigma2)
    log.info(f"Stage 1 → Stage 3 weights: mean={weights.mean():.3f}, min={weights.min():.3f}")
    return weights.astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# VISUALISATION
# ─────────────────────────────────────────────────────────────────────────────

def plot_reliability_diagram(
    calibration_df: pd.DataFrame,
    save_path: Optional[str] = None,
    show: bool = False,
) -> None:
    """
    Plot reliability (calibration) diagram.

    Perfect calibration: empirical_coverage = nominal_coverage (diagonal line).
    Shaded ±0.05 band marks the acceptable tolerance zone per §1.6.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not available — skipping reliability diagram")
        return

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration", linewidth=1.5)
    ax.fill_between([0, 1], [-0.05, 0.95], [0.05, 1.05], alpha=0.10,
                     color="green", label="±0.05 tolerance")

    ax.plot(
        calibration_df["nominal_coverage"],
        calibration_df["empirical_coverage"],
        "o-", color="#e63946", linewidth=2, markersize=7, label="Model",
    )

    ax.set_xlabel("Nominal coverage (α)", fontsize=13)
    ax.set_ylabel("Empirical coverage", fontsize=13)
    ax.set_title("Stage 1 Quantile Regression — Reliability Diagram", fontsize=13)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.legend(fontsize=11); ax.grid(alpha=0.3)

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        log.info(f"Reliability diagram saved → {save_path}")
    if show:
        plt.show()
    plt.close()


# ─────────────────────────────────────────────────────────────────────────────
# SELF-CONTAINED RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_reliability_diagram(
    save_path: Optional[str] = None,
    show: bool = False,
) -> pd.DataFrame:
    """
    Load predictions from the merged parquet and produce the reliability diagram.

    What we have
    ────────────
    Three trained quantile models: q05, q50, q95.
    The predictions parquet stores their outputs in columns pm25_q05, pm25_q50,
    pm25_q95 alongside pm25_observed.

    Reliability diagram produced
    ────────────────────────────
    assess_calibration() checks individual-quantile calibration:
      P(Y ≤ q̂_α) ≈ α   for α ∈ {0.05, 0.50, 0.95}
    This gives three points on the reliability diagram (the standard check for
    quantile regression output).

    The 90% prediction-interval empirical coverage is also logged separately via
    compute_prediction_interval_coverage().

    What is NOT available without retraining
    ─────────────────────────────────────────
    A five-level PI reliability diagram (nominal = 0.50, 0.70, 0.80, 0.90, 0.95)
    requires quantile pairs [q0.025/q0.975, q0.10/q0.90, q0.15/q0.85,
    q0.25/q0.75] in addition to [q0.05/q0.95].  Train those models first and
    pass their predictions to assess_calibration() / plot_reliability_diagram().

    Returns
    ───────
    calibration_df : DataFrame from assess_calibration()
    """
    preds_path = MERGED_DIR / "pm25_predictions_daily.parquet"
    if not preds_path.exists():
        raise FileNotFoundError(
            f"Predictions parquet not found: {preds_path}\n"
            "Run train_xgboost.py first to generate quantile predictions."
        )

    df = pd.read_parquet(preds_path)
    df = df.dropna(subset=["pm25_observed"])

    if df.empty:
        raise ValueError("No rows with non-NaN pm25_observed in predictions parquet.")

    log.info(f"Loaded {len(df):,} observed days for calibration assessment.")

    y_obs = df["pm25_observed"].values
    q_preds = {
        0.05: df["pm25_q05"].values,
        0.50: df["pm25_q50"].values,
        0.95: df["pm25_q95"].values,
    }

    # Individual-quantile calibration (3 points on the diagram)
    calibration_df = assess_calibration(y_obs, q_preds, alphas=QUANTILE_ALPHAS)

    # 90% PI coverage (logged separately)
    compute_prediction_interval_coverage(
        y_obs,
        q_low=df["pm25_q05"].values,
        q_high=df["pm25_q95"].values,
        nominal_coverage=0.90,
    )

    if save_path is None:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        save_path = str(FIGURES_DIR / "reliability_diagram.png")

    plot_reliability_diagram(calibration_df, save_path=save_path, show=show)
    return calibration_df


if __name__ == "__main__":
    run_reliability_diagram()
