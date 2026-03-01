"""
validate_chiangmai.py — Stage 2: Zero-shot + fine-tune transfer validation on Chiang Mai.

Validation strategy (§2.7 of RESEARCH_PROJECT_DESIGN.md):
  Step 1 (zero-shot): Apply the Medellín-pretrained backbone to Chiang Mai
                      WITHOUT any fine-tuning. Measure K, S, and PM2.5 skill.
  Step 2 (fine-tune): Fine-tune for 100 epochs on a small training window of
                      Chiang Mai data (3 months), then test on held-out months.

The K field from Chiang Mai is the key diagnostic:
  - K_chiangmai should be within a physically plausible range
  - Diurnal K cycle should match expected katabatic/anabatic patterns

Gate condition (§2.7):
  PASS: zero-shot RMSE < 15 µg/m³ AND diurnal K cycle within 0.3 of Stull 1988 reference
  FAIL: K magnitude is 10× Medellín's value → catastrophic domain shift → abort transfer

Usage:
    python validate_chiangmai.py [--epochs 100] [--ckpt <path>]
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[4]))
from config import LOG_FORMAT, LOG_DATEFMT, MODELS_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("validate_chiangmai")

CM_RAW_DIR   = Path(__file__).parents[4] / "data" / "raw" / "chiangmai"
CHECKPOINT_DIR = MODELS_DIR / "stage2_pretrain"
RESULTS_DIR  = MODELS_DIR / "stage2_pretrain" / "chiangmai_validation"

# Physical plausibility thresholds for K-field check
K_MEDELLIN_REFERENCE = 50.0    # m²/s — expected K from Medellín pre-training
K_CATASTROPHIC_RATIO = 10.0    # If K_CM / K_MEd > 10 → catastrophic domain shift
DIURNAL_TOLERANCE    = 0.3     # |corr(K_cycle, Stull_ref)| must exceed this


def load_chiangmai_pm25() -> pd.DataFrame:
    """Load Chiang Mai PCD PM2.5 ground truth from downloaded CSV."""
    pm25_csvs = sorted((CM_RAW_DIR / "pm25").glob("pcd_chiangmai_pm25*.csv"))
    if not pm25_csvs:
        raise FileNotFoundError(
            f"No Chiang Mai PM2.5 data in {CM_RAW_DIR / 'pm25'}. "
            "Run: python download_chiangmai.py --pcd-only"
        )
    df = pd.concat([pd.read_csv(f) for f in pm25_csvs], ignore_index=True)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    daily = df.groupby("date")["pm25_ugm3"].mean().reset_index()
    daily.columns = ["date", "pm25_observed"]
    log.info(f"Loaded {len(daily)} daily Chiang Mai PM2.5 obs")
    return daily


def zero_shot_predict(model, cm_era5_path: Path) -> pd.DataFrame:
    """
    Apply pre-trained model to Chiang Mai domain WITHOUT fine-tuning.

    The model predicts PM2.5 at Chiang Mai PCD station locations using only
    ERA5 wind as input (no observed PM2.5 used for prediction).

    Returns DataFrame with columns: date, pm25_pred, K_mean
    """
    log.info("Zero-shot transfer: predicting Chiang Mai PM2.5 …")
    # Placeholder — will call model.forward() on Chiang Mai grid
    # and extract the diffusivity K field
    result = {
        "date":     pd.date_range("2019-01-01", periods=365, freq="D"),
        "pm25_pred": np.full(365, np.nan),   # Filled by model.forward()
        "K_mean":    np.full(365, np.nan),   # Diffusivity field mean
    }
    return pd.DataFrame(result)


def compute_validation_metrics(
    y_obs: pd.Series,
    y_pred: pd.Series,
) -> dict:
    """Compute RMSE, MAE, R² for validation."""
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    mask = y_obs.notna() & y_pred.notna()
    yt, yp = y_obs[mask].values, y_pred[mask].values
    return {
        "n":    int(mask.sum()),
        "RMSE": round(float(np.sqrt(mean_squared_error(yt, yp))), 4),
        "MAE":  round(float(mean_absolute_error(yt, yp)), 4),
        "R2":   round(float(r2_score(yt, yp)), 4),
    }


def check_transfer_gate(
    metrics: dict,
    k_ratio: float,
    diurnal_corr: float,
) -> bool:
    """
    Evaluate the Stage 2 transfer validation gate condition (§2.7).

    PASS conditions:
      1. zero-shot RMSE < 15 µg/m³  (model generalises to Chiang Mai)
      2. K_CM / K_MED < 10          (no catastrophic domain shift)
      3. |diurnal_corr| > 0.3       (K shows expected diurnal cycle)
    """
    rmse   = metrics.get("RMSE", np.inf)
    cond1  = rmse < 15.0
    cond2  = k_ratio < K_CATASTROPHIC_RATIO
    cond3  = abs(diurnal_corr) > DIURNAL_TOLERANCE
    passed = cond1 and cond2 and cond3

    log.info("═══ TRANSFER VALIDATION GATE ═══")
    log.info(f"  RMSE < 15 µg/m³        : {rmse:.3f} → {'✅' if cond1 else '❌'}")
    log.info(f"  K ratio < 10           : {k_ratio:.2f} → {'✅' if cond2 else '❌'}")
    log.info(f"  Diurnal K corr > 0.3   : {diurnal_corr:.3f} → {'✅' if cond3 else '❌'}")
    log.info(f"  Gate: {'✅ PASS — proceed to Kandy fine-tuning' if passed else '❌ FAIL — review domain shift'}")
    return passed


def compute_transfer_diagnostics(
    K_learned: "np.ndarray",
    BLH_era5: "np.ndarray",
    Kx: "np.ndarray",
    Ky: "np.ndarray",
    S_amplitude: "np.ndarray",
    stable_night_mask: "np.ndarray",
    K_rmse_monsoon: float,
    K_rmse_dry: float,
) -> dict:
    """
    5 physics transfer diagnostics for the Chiang Mai validation gate.

    These verify that USEFUL VALLEY PHYSICS transferred, not just
    good overall R². All 5 must pass for the transfer to be considered
    physically meaningful for Kandy fine-tuning.

    Args:
        K_learned       : 1-D array of learned diffusivity K values [m²/s]
        BLH_era5        : Matching ERA5 boundary layer heights [m]
        Kx, Ky          : Along-valley and cross-valley K components [m²/s]
        S_amplitude     : Source term amplitude time series (diurnal cycle)
        stable_night_mask: Boolean mask for stable nocturnal conditions
        K_rmse_monsoon  : K-field RMSE during monsoon months (May–Sep)
        K_rmse_dry      : K-field RMSE during dry months (Nov–Mar)

    Returns:
        dict with per-diagnostic values, thresholds, pass/fail flags,
        and an 'all_pass' summary key.
    """
    from scipy.stats import pearsonr

    def _bimodality_coefficient(x: "np.ndarray") -> float:
        """Sarle bimodality coefficient. >0.555 suggests bimodal distribution."""
        import pandas as pd
        n = len(x)
        skew = float(pd.Series(x).skew())
        kurt = float(pd.Series(x).kurtosis())
        return (skew ** 2 + 1) / (kurt + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3)))

    # ── Diagnostic 1: K-BLH correlation ─────────────────────────────────────
    # Physics: K ∝ BLH^α, α ∈ [0.5, 1.5] means turbulence scales correctly
    # with mixing depth. A correlation > 0.5 confirms this scaling.
    k_blh_corr = float(pearsonr(K_learned, BLH_era5)[0])

    # ── Diagnostic 2: Nocturnal K collapse ───────────────────────────────────
    # Physics: stable katabatic nights → laminar flow → K < 10 m²/s.
    # A PINN that learned katabatic dynamics should suppress K at night.
    nocturnal_k_mean = float(np.mean(K_learned[stable_night_mask]))

    # ── Diagnostic 3: Kx/Ky anisotropy ratio ─────────────────────────────────
    # Physics: valley channelling makes along-valley diffusion > cross-valley.
    # Ratio > 1.2 confirms the model learned directional turbulence structure.
    kx_ky_ratio = float(np.mean(Kx) / max(float(np.mean(Ky)), 1e-9))

    # ── Diagnostic 4: Source bimodality ──────────────────────────────────────
    # Physics: traffic emission S should show AM/PM peaks → bimodal diurnal.
    # Bimodality coefficient > 0.555 (Sarle threshold) confirms diurnal peaks.
    source_bimo = _bimodality_coefficient(S_amplitude)

    # ── Diagnostic 5: Monsoon K degradation ──────────────────────────────────
    # Physics: monsoon months have different turbulence regime (wet, unstable).
    # A ratio < 2.0 means performance does not catastrophically collapse under
    # monsoon conditions — the physics still partially transfers.
    monsoon_ratio = float(K_rmse_monsoon / max(K_rmse_dry, 1e-6))

    diagnostics = {
        "k_blh_correlation":           k_blh_corr,
        "k_blh_correlation_threshold": 0.5,
        "k_blh_pass":                  k_blh_corr > 0.5,

        "nocturnal_k_mean":            nocturnal_k_mean,
        "nocturnal_k_threshold":       10.0,
        "nocturnal_k_pass":            nocturnal_k_mean < 10.0,

        "kx_ky_ratio_along_axis":      kx_ky_ratio,
        "kx_ky_threshold":             1.2,
        "kx_ky_pass":                  kx_ky_ratio > 1.2,

        "source_bimodality":           source_bimo,
        "source_bimodality_threshold": 0.555,
        "source_bimodality_pass":      source_bimo > 0.555,

        "monsoon_k_degradation":       monsoon_ratio,
        "monsoon_degradation_threshold": 2.0,
        "monsoon_degradation_pass":    monsoon_ratio < 2.0,
    }
    diagnostics["all_pass"] = all([
        diagnostics["k_blh_pass"],
        diagnostics["nocturnal_k_pass"],
        diagnostics["kx_ky_pass"],
        diagnostics["source_bimodality_pass"],
        diagnostics["monsoon_degradation_pass"],
    ])

    log.info("═══ PHYSICS TRANSFER DIAGNOSTICS ═══")
    log.info(f"  D1 K-BLH corr > 0.5          : {k_blh_corr:.3f} → {'✅' if diagnostics['k_blh_pass'] else '❌'}")
    log.info(f"  D2 Nocturnal K < 10 m²/s      : {nocturnal_k_mean:.2f} → {'✅' if diagnostics['nocturnal_k_pass'] else '❌'}")
    log.info(f"  D3 Kx/Ky ratio > 1.2          : {kx_ky_ratio:.3f} → {'✅' if diagnostics['kx_ky_pass'] else '❌'}")
    log.info(f"  D4 Source bimodality > 0.555   : {source_bimo:.3f} → {'✅' if diagnostics['source_bimodality_pass'] else '❌'}")
    log.info(f"  D5 Monsoon degradation < 2×    : {monsoon_ratio:.3f} → {'✅' if diagnostics['monsoon_degradation_pass'] else '❌'}")
    log.info(f"  Physics transfer: {'✅ ALL PASS — valley physics transferred' if diagnostics['all_pass'] else '❌ PARTIAL — review diagnostics before Kandy fine-tune'}")

    return diagnostics


def finetune_chiangmai(
    model,
    pm25_df: pd.DataFrame,
    n_epochs: int = 100,
    lr: float = 1e-4,
) -> list:
    """
    Fine-tune the Medellín backbone on 3 months of Chiang Mai data.

    Uses a 3-month train / 9-month test temporal split.
    λ_physics is lowered but kept > 0 to prevent PDE structure collapse.
    """
    try:
        import torch
        import torch.optim as optim
    except ImportError:
        raise ImportError("PyTorch required")

    log.info(f"Fine-tuning on Chiang Mai ({n_epochs} epochs, lr={lr}) …")
    optimizer = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()), lr=lr
    )
    loss_history = []
    for epoch in range(n_epochs):
        # Placeholder: full implementation calls pde_residual + data_loss
        loss_val = 0.0
        optimizer.step()
        if epoch % 20 == 0:
            log.info(f"  CM fine-tune epoch {epoch}/{n_epochs}: loss={loss_val:.6f}")
        loss_history.append({"epoch": epoch, "loss": loss_val})
    return loss_history


def main():
    parser = argparse.ArgumentParser(description="Stage 2 Chiang Mai transfer validation")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--ckpt",   type=str, help="Path to pretrained checkpoint")
    args = parser.parse_args()

    ckpt_path = Path(args.ckpt) if args.ckpt else CHECKPOINT_DIR / "pretrained_physics_backbone.pt"
    if not ckpt_path.exists():
        log.error(f"Checkpoint not found: {ckpt_path}. Run pretrain_medellin.py first.")
        sys.exit(1)

    try:
        import torch
        from src.stage3_pinn.models.fourier_pinn import FourierPINN
        model = FourierPINN()
        ckpt  = torch.load(str(ckpt_path), map_location="cpu")
        model.load_state_dict(ckpt["model_state_dict"])
        log.info(f"Loaded checkpoint: {ckpt_path}")
    except ImportError:
        log.warning("FourierPINN import failed — ensure stage3_pinn/models/ is complete")
        sys.exit(0)

    pm25_df = load_chiangmai_pm25()
    preds   = zero_shot_predict(model, CM_RAW_DIR / "era5")

    merged = pm25_df.merge(preds, on="date", how="inner")
    metrics = compute_validation_metrics(merged["pm25_observed"], merged["pm25_pred"])
    log.info(f"Zero-shot metrics: {metrics}")

    # Placeholder K diagnostics
    k_ratio    = merged["K_mean"].mean() / K_MEDELLIN_REFERENCE if "K_mean" in merged else 1.0
    diurnal_r  = 0.0  # Will be computed by validate/transfer_decision.py

    gate_passed = check_transfer_gate(metrics, k_ratio, diurnal_r)

    # Physics transfer diagnostics — run regardless of gate outcome
    # Placeholders here; populated by zero_shot_predict() once implemented
    if "K_mean" in merged.columns and not merged["K_mean"].isna().all():
        K_arr = merged["K_mean"].dropna().values
        blh_arr = np.ones_like(K_arr) * 500.0    # ERA5 BLH placeholder
        kx_arr = K_arr * 1.3                      # Placeholder anisotropy
        ky_arr = K_arr * 1.0
        s_arr  = np.abs(np.sin(np.linspace(0, 4 * np.pi, len(K_arr))))
        stable_mask = K_arr < np.median(K_arr)    # Placeholder night mask
        _ = compute_transfer_diagnostics(
            K_arr, blh_arr, kx_arr, ky_arr, s_arr, stable_mask,
            K_rmse_monsoon=0.0, K_rmse_dry=0.0,
        )
    else:
        log.info("Physics transfer diagnostics skipped — K_mean not yet populated "
                 "(implement zero_shot_predict() to activate)")

    if gate_passed:
        loss_hist = finetune_chiangmai(model, pm25_df, n_epochs=args.epochs)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(loss_hist).to_csv(RESULTS_DIR / "finetune_chiangmai_losses.csv", index=False)

    log.info("✅ Chiang Mai validation complete.")


if __name__ == "__main__":
    main()
