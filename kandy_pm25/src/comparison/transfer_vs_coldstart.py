"""
transfer_vs_coldstart.py — Compare transfer-initialised vs cold-start PINN on Kandy.

Science question: Does pre-training on Medellín physically transfer to the
Kandy domain, or is the geography too different?

Metrics (§4.2 of RESEARCH_PROJECT_DESIGN.md):
  1. CONVERGENCE SPEED: Epochs to reach RMSE < 5 µg/m³ — speedup factor expected 2–5×.
  2. FINAL RMSE: At n_epochs, which model has lower RMSE at ground truth sensors?
  3. K-FIELD QUALITY: Is K_transfer within [1, 100] m²/s more reliably than K_coldstart?
  4. LOSS LANDSCAPE: Transfer should show smoother loss curves (fewer oscillations).
  5. DATA EFFICIENCY: Compare performance with N=30 vs N=100 ground-truth observations.

Expected result: Transfer ≥ cold-start in at least 3/5 metrics.
If cold-start wins overall → add a "failure analysis" section to the paper.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import LOG_FORMAT, LOG_DATEFMT, MODELS_DIR, FIGURES_DIR, TABLES_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("transfer_vs_coldstart")


def load_loss_curves(loss_dir: Path) -> tuple:
    """
    Load training loss CSV files for both transfer-init and cold-start runs.

    Expected files:
      - {loss_dir}/transfer_losses.csv
      - {loss_dir}/coldstart_losses.csv

    Returns:
        (transfer_df, coldstart_df) with columns: epoch, L_pde, L_data, L_total
    """
    def _safe_load(path: Path) -> pd.DataFrame:
        if path.exists():
            return pd.read_csv(path)
        log.warning(f"Loss file not found: {path}")
        return pd.DataFrame()

    t_df = _safe_load(loss_dir / "transfer_losses.csv")
    c_df = _safe_load(loss_dir / "coldstart_losses.csv")
    return t_df, c_df


def convergence_analysis(
    transfer_df: pd.DataFrame,
    coldstart_df: pd.DataFrame,
    target_loss: float = 5.0,
    loss_col: str = "L_data",
) -> dict:
    """
    Compare epochs-to-convergence for both models.

    Args:
        target_loss : Loss threshold that defines "converged"
        loss_col    : Which loss column to monitor

    Returns:
        Dict with epochs, speedup factor, and winner.
    """
    def _epoch_to_target(df: pd.DataFrame) -> Optional[int]:
        if df.empty or loss_col not in df.columns:
            return None
        hits = df[df[loss_col] <= target_loss]
        return int(hits["epoch"].iloc[0]) if not hits.empty else None

    t_epoch = _epoch_to_target(transfer_df)
    c_epoch = _epoch_to_target(coldstart_df)
    speedup = round(c_epoch / t_epoch, 2) if t_epoch and c_epoch else None
    winner  = "transfer" if (t_epoch and (not c_epoch or t_epoch < c_epoch)) else "coldstart"

    result = {
        "transfer_epochs_to_target":  t_epoch,
        "coldstart_epochs_to_target": c_epoch,
        "speedup_factor":  speedup,
        "target_loss":     target_loss,
        "winner":          winner,
    }
    icon = "✅" if winner == "transfer" else "⚠️"
    log.info(f"Convergence: transfer={t_epoch}ep, cold-start={c_epoch}ep, speedup={speedup}× {icon}")
    return result


def final_rmse_comparison(
    transfer_ckpt: Path,
    coldstart_ckpt: Path,
    ground_truth_df: pd.DataFrame,
    domain,
    device=None,
) -> pd.DataFrame:
    """
    Load both checkpoints, run inference, compare RMSE at ground-truth sensors.

    Returns DataFrame with RMSE / MAE / R² for both models.
    """
    try:
        import torch
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        from src.stage3_pinn.models.fourier_pinn import build_fourier_pinn
    except ImportError as e:
        log.warning(f"Cannot run final RMSE comparison: {e}"); return pd.DataFrame()

    dev = device or torch.device("cpu")
    results = []

    for label, ckpt_path in [("transfer_init", transfer_ckpt), ("cold_start", coldstart_ckpt)]:
        if not ckpt_path.exists():
            log.warning(f"Checkpoint not found: {ckpt_path}"); continue

        model = build_fourier_pinn().to(dev)
        ckpt  = torch.load(str(ckpt_path), map_location=dev)
        model.load_state_dict(ckpt["model_state_dict"])
        model.eval()

        # Evaluate at ground-truth sensor locations
        lats  = torch.tensor(ground_truth_df["lat"].values, dtype=torch.float32, device=dev)
        lons  = torch.tensor(ground_truth_df["lon"].values, dtype=torch.float32, device=dev)
        x, y  = domain.to_normalised(lons.cpu().numpy(), lats.cpu().numpy())
        xyt   = torch.tensor(
            np.column_stack([x, y, np.full(len(x), 0.5)]),
            dtype=torch.float32, device=dev,
        )
        with torch.no_grad():
            C_pred, _ = model(xyt)
        preds = C_pred.squeeze().cpu().numpy()
        obs   = ground_truth_df["pm25_obs"].values
        valid = ~np.isnan(obs) & ~np.isnan(preds)

        results.append({
            "model":  label,
            "n":      int(valid.sum()),
            "RMSE":   round(float(np.sqrt(mean_squared_error(obs[valid], preds[valid]))), 3),
            "MAE":    round(float(mean_absolute_error(obs[valid], preds[valid])), 3),
            "R2":     round(float(r2_score(obs[valid], preds[valid])), 4),
        })

    df = pd.DataFrame(results)
    log.info(f"Final RMSE comparison:\n{df.to_string(index=False)}")
    return df


def k_quality_check(
    transfer_k: np.ndarray,
    coldstart_k: np.ndarray,
    k_min: float = 1.0,
    k_max: float = 100.0,
) -> dict:
    """
    Check what fraction of K values fall within [k_min, k_max] for both models.

    Higher fraction → K is more physically plausible.
    """
    def _fraction_valid(k: np.ndarray) -> float:
        return float(np.mean((k >= k_min) & (k <= k_max)))

    t_frac = _fraction_valid(transfer_k)
    c_frac = _fraction_valid(coldstart_k)
    result = {
        "transfer_K_valid_fraction":  round(t_frac, 4),
        "coldstart_K_valid_fraction": round(c_frac, 4),
        "winner": "transfer" if t_frac >= c_frac else "coldstart",
    }
    log.info(f"K quality: transfer={t_frac:.1%} valid, cold={c_frac:.1%} valid → {result['winner']} wins")
    return result


def plot_loss_curves(
    transfer_df: pd.DataFrame,
    coldstart_df: pd.DataFrame,
    save_path: Optional[str] = None,
) -> None:
    """Plot training loss curves side by side for qualitative comparison."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not available"); return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    col  = "L_total" if "L_total" in (transfer_df.columns if not transfer_df.empty else []) else "L_pde"
    for df, label, color in [(transfer_df, "Transfer-init", "steelblue"), (coldstart_df, "Cold-start", "coral")]:
        if not df.empty and col in df.columns:
            axes[0].semilogy(df["epoch"], df[col], color=color, label=label, lw=1.5)
    axes[0].set_xlabel("Epoch"); axes[0].set_ylabel("Loss (log scale)")
    axes[0].set_title("Training Loss Curves"); axes[0].legend(); axes[0].grid(alpha=0.3)

    # Bar chart of final RMSE (fill from external call or placeholder)
    axes[1].set_title("Final RMSE at Ground-Truth Sensors")
    axes[1].set_xticks([]); axes[1].set_yticks([])
    axes[1].text(0.5, 0.5, "Run final_rmse_comparison() to populate",
                 ha="center", va="center", transform=axes[1].transAxes, fontsize=10, alpha=0.5)

    fig.suptitle("Transfer-init vs Cold-start PINN", fontsize=13)
    out = save_path or str(FIGURES_DIR / "transfer_vs_coldstart_losses.png")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close()
    log.info(f"Loss curves saved → {out}")


def run_comparison(
    loss_dir: Optional[Path] = None,
    save: bool = True,
) -> dict:
    """Master runner: load curves, convergence analysis, K quality check, plots."""
    ldir = loss_dir or (MODELS_DIR / "stage3_pinn")
    transfer_df, coldstart_df = load_loss_curves(ldir)
    convergence = convergence_analysis(transfer_df, coldstart_df)

    if save:
        plot_loss_curves(transfer_df, coldstart_df)
        pd.DataFrame([convergence]).to_csv(TABLES_DIR / "transfer_vs_coldstart_convergence.csv", index=False)

    return {"convergence": convergence}
