"""
transfer_diagnostics.py — Compare Stage 3 (transfer-init) vs cold-start PINN on Kandy.

After Stage 3 training with two initialisation strategies:
  - Transfer-initialised: backbone from Medellín pre-training
  - Cold-start: randomly initialised (Xavier uniform)

This module loads both models' predictions and computes:
  1. Held-out RMSE / MAE / R² comparison
  2. Convergence speed (epochs to target RMSE)
  3. K-field stability (variance of K over training epochs)
  4. Source field S plausibility (correlation with OSM road density)

Key expected result: transfer-init converges 2–5× faster and achieves
lower RMSE on SW Monsoon cloud-gap days (the hardest generalisation case).
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[4]))
from config import LOG_FORMAT, LOG_DATEFMT, MODELS_DIR, TABLES_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("transfer_diagnostics")

RESULTS_DIR = MODELS_DIR / "stage3_pinn" / "diagnostics"


def load_training_curves(transfer_csv: Path, coldstart_csv: Path) -> tuple:
    """
    Load training loss curves for transfer-init and cold-start runs.

    Returns:
        (transfer_df, coldstart_df) with columns: epoch, loss_total, loss_pde, loss_data
    """
    def _load(p: Path) -> pd.DataFrame:
        if not p.exists():
            log.warning(f"Loss curve not found: {p}")
            return pd.DataFrame()
        return pd.read_csv(p)

    t_df = _load(transfer_csv)
    c_df = _load(coldstart_csv)
    return t_df, c_df


def compute_convergence_speed(
    loss_df: pd.DataFrame,
    target_rmse: float = 5.0,
    loss_col: str = "loss_data",
) -> Optional[int]:
    """
    Find the epoch at which the model first reaches target_rmse.

    Returns None if target was never reached.
    """
    if loss_df.empty or loss_col not in loss_df.columns:
        return None
    below = loss_df[loss_df[loss_col] <= target_rmse]
    return int(below["epoch"].iloc[0]) if not below.empty else None


def compare_convergence(
    transfer_df: pd.DataFrame,
    coldstart_df: pd.DataFrame,
    target_rmse: float = 5.0,
) -> dict:
    """
    Compare convergence speed between transfer-init and cold-start training.

    Expected result: transfer-init reaches target_rmse 2–5× faster.
    """
    t_epoch = compute_convergence_speed(transfer_df, target_rmse)
    c_epoch = compute_convergence_speed(coldstart_df, target_rmse)

    speedup = None
    if t_epoch and c_epoch:
        speedup = round(c_epoch / t_epoch, 2)

    result = {
        "transfer_epoch_to_target":   t_epoch,
        "coldstart_epoch_to_target":  c_epoch,
        "speedup_factor":             speedup,
        "target_rmse":                target_rmse,
        "transfer_wins":              (t_epoch is not None and (c_epoch is None or t_epoch < c_epoch)),
    }
    status = "✅ Transfer faster" if result["transfer_wins"] else "❌ Transfer slower/tied"
    log.info(f"Convergence: transfer={t_epoch} epochs, cold-start={c_epoch} epochs, speedup={speedup}× — {status}")
    return result


def compare_held_out_metrics(
    transfer_preds: pd.DataFrame,
    coldstart_preds: pd.DataFrame,
    y_obs: pd.Series,
) -> pd.DataFrame:
    """
    Compare held-out PM2.5 prediction metrics for both models.

    Args:
        transfer_preds  : DataFrame with 'pm25_pred' from transfer-init model
        coldstart_preds : DataFrame with 'pm25_pred' from cold-start model
        y_obs           : Observed PM2.5 Series (same index)

    Returns:
        DataFrame comparing R², RMSE, MAE for both models.
    """
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

    rows = []
    for label, preds in [("transfer_init", transfer_preds), ("cold_start", coldstart_preds)]:
        if preds.empty:
            continue
        mask = y_obs.notna() & preds["pm25_pred"].notna()
        yt = y_obs[mask].values
        yp = preds["pm25_pred"][mask].values
        rows.append({
            "model":  label,
            "n":      int(mask.sum()),
            "R2":     round(float(r2_score(yt, yp)), 4),
            "RMSE":   round(float(np.sqrt(mean_squared_error(yt, yp))), 4),
            "MAE":    round(float(mean_absolute_error(yt, yp)), 4),
        })
    df = pd.DataFrame(rows)
    log.info("Held-out comparison:\n" + df.to_string(index=False))
    return df


def check_k_field_stability(k_series: pd.Series, label: str = "") -> dict:
    """
    Assess K-field stability: coefficient of variation (CV = std/mean).

    Low CV → K is stable across training → physics is well-identified.
    High CV → K is oscillating → underdetermined inverse problem.

    Acceptable CV < 0.3 for Kx and Ky separately.
    """
    cv = float(k_series.std() / (k_series.mean() + 1e-9))
    result = {"label": label, "K_mean": round(float(k_series.mean()), 4),
              "K_std": round(float(k_series.std()), 4), "K_cv": round(cv, 4),
              "stable": cv < 0.3}
    status = "✅ Stable" if result["stable"] else "❌ Unstable"
    log.info(f"K stability ({label}): mean={result['K_mean']:.2f}, CV={cv:.3f} — {status}")
    return result


def run_all_diagnostics(
    transfer_loss_csv:   Optional[Path] = None,
    coldstart_loss_csv:  Optional[Path] = None,
    save_report: bool = True,
) -> dict:
    """Master runner: load curves, compare convergence and metrics, save report."""
    t_loss = transfer_loss_csv  or (MODELS_DIR / "stage3_pinn" / "transfer_losses.csv")
    c_loss = coldstart_loss_csv or (MODELS_DIR / "stage3_pinn" / "coldstart_losses.csv")

    t_df, c_df = load_training_curves(Path(t_loss), Path(c_loss))
    convergence = compare_convergence(t_df, c_df)

    report = {"convergence": convergence}
    if save_report:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([convergence]).to_csv(RESULTS_DIR / "convergence_comparison.csv", index=False)
        log.info(f"Diagnostics report saved → {RESULTS_DIR}")

    return report
