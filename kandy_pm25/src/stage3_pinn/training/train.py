"""
train.py — Master training loop for Stage 3 Kandy PINN.

Orchestrates all components: domain, collocation, loss functions, curriculum.
Loads Stage 1 predictions as boundary conditions and data supervision.

Three initialisation paths (from transfer_decision.json):
  A. use_pretrained_frozen  — load backbone, freeze, fine-tune head
  B. use_pretrained_unfrozen — load backbone, full fine-tune
  C. random_init            — cold start training

Best practice: run with --profile first (20 epochs) to confirm GPU memory.

Usage:
    python train.py --init A --epochs 1000 --lr 5e-4
    python train.py --init C --epochs 1000  # Cold start fallback
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    LOG_FORMAT, LOG_DATEFMT, MODELS_DIR, MERGED_DIR, PINN_GRID_RESOLUTION_M,
    N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY, PINN_EPOCHS, PINN_LR,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("train_pinn")

CHECKPOINT_DIR   = MODELS_DIR / "stage3_pinn"
TRANSFER_DECISION_JSON = MODELS_DIR / "stage2_pretrain" / "chiangmai_validation" / "transfer_decision.json"


def _get_device():
    try:
        import torch
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    except ImportError:
        raise ImportError("PyTorch required. Run: pip install torch")


def load_init_decision() -> dict:
    """Read transfer_decision.json to determine initialisation path."""
    if not TRANSFER_DECISION_JSON.exists():
        log.warning("transfer_decision.json not found — defaulting to cold start (C)")
        return {"decision": "C_cold_start", "stage3_init": "random_init"}
    with open(TRANSFER_DECISION_JSON) as f:
        return json.load(f)


def build_model(init_mode: str, device):
    """Build FourierPINN with appropriate initialisation."""
    from src.stage3_pinn.models.fourier_pinn import build_fourier_pinn

    model = build_fourier_pinn()
    model = model.to(device)

    if init_mode in ("use_pretrained_frozen", "use_pretrained_unfrozen"):
        ckpt_path = MODELS_DIR / "stage2_pretrain" / "pretrained_physics_backbone.pt"
        if not ckpt_path.exists():
            log.warning(f"Pretrained checkpoint not found: {ckpt_path} — falling back to random init")
            return model, "random_init"

        import torch
        ckpt = torch.load(str(ckpt_path), map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
        log.info(f"Loaded pretrained backbone from {ckpt_path}")

        if init_mode == "use_pretrained_frozen":
            from src.stage2_transfer.pretrain.layer_freezing import freeze_backbone
            model = freeze_backbone(model, n_frozen_layers=4)

    else:
        log.info("Cold-start: using random Xavier initialisation")

    return model, init_mode


def load_stage1_data() -> "pd.DataFrame":
    """Load Stage 1b pixel-level predictions for boundary condition supervision.

    Source: pm25_pixel_predictions.parquet produced by train_pixel_xgboost.py.
    Columns required by DirichletBC: date, lat, lon, pm25_pred.
    Optional columns for uncertainty weighting: pm25_q05, pm25_q95.
    """
    import pandas as pd
    pred_path = MERGED_DIR / "pm25_pixel_predictions.parquet"
    if not pred_path.exists():
        raise FileNotFoundError(
            f"Stage 1b pixel predictions not found: {pred_path}\n"
            "Run: python src/stage1_satml/models/train_pixel_xgboost.py"
        )
    df = pd.read_parquet(pred_path)
    # Rename pixel prediction column to the name DirichletBC expects
    if "pm25_pixel_pred" in df.columns and "pm25_pred" not in df.columns:
        df = df.rename(columns={"pm25_pixel_pred": "pm25_pred"})
    # Ensure date is a plain column (not index) for date-string filtering
    if df.index.name == "date":
        df = df.reset_index()
    log.info(f"Loaded {len(df):,} Stage 1b pixel prediction rows "
             f"({df['date'].nunique()} dates, {df['pixel_id'].nunique()} pixels)")
    return df


def train_pinn(
    model,
    stage1_df:  "pd.DataFrame",
    n_epochs:   int,
    lr:         float,
    device,
    use_rar:    bool = True,
    rar_start:  int  = 200,
    save_every: int  = 100,
) -> list:
    """
    Main PINN training loop.

    Each iteration:
      1. Sample collocation points (uniform or RAR)
      2. Evaluate PDE residual at interior points
      3. Evaluate BC loss at boundary points using Stage 1 preds
      4. Evaluate data loss at Stage 1 pixel locations
      5. Compute physical constraint losses
      6. Apply curriculum-weighted total loss, backprop, step optimizer

    Args:
        model      : FourierPINN model
        stage1_df  : Stage 1 PM2.5 predictions DataFrame
        n_epochs   : Total training epochs
        lr         : Initial learning rate (Adam)
        device     : torch.device
        use_rar    : Enable RAR after rar_start epoch
        rar_start  : Epoch to switch from uniform to RAR collocation
        save_every : Checkpoint save frequency

    Returns:
        loss_history : List of dicts with per-epoch loss breakdown
    """
    import torch
    import torch.optim as optim

    from src.stage3_pinn.training.curriculum    import CurriculumScheduler
    from src.stage3_pinn.training.loss_functions import (
        data_fidelity_loss, total_loss, LossTracker,
    )
    from src.stage3_pinn.training.collocation   import sample_uniform, sample_rar, to_tensors
    from src.stage3_pinn.physics.advection_diffusion import pde_loss
    from src.stage3_pinn.physics.constraints    import compute_all_constraints
    from src.stage3_pinn.domain.boundary_conditions import DirichletBC, NeumannBC
    from config import KANDY_PINN_BBOX

    optimizer   = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=lr)
    scheduler_opt = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_epochs, eta_min=1e-6)
    curriculum  = CurriculumScheduler(total_epochs=n_epochs)
    bc_handler  = DirichletBC(stage1_df)
    tracker     = LossTracker()

    dates  = sorted(stage1_df["date"].unique())
    n_dates = len(dates)
    log.info(f"Starting PINN training: {n_epochs} epochs, {n_dates} training dates, device={device}")
    curriculum.log_schedule(every=200)

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    xy_int, t_int, xy_bnd, t_bnd = sample_uniform(
        N_COLLOCATION_INTERIOR, N_COLLOCATION_BOUNDARY, KANDY_PINN_BBOX
    )

    for epoch in range(n_epochs):
        model.train()
        lambdas   = curriculum.step(epoch)
        current_lr = scheduler_opt.get_last_lr()[0] if epoch > 0 else lr

        # --- Sample one random date for data/BC loss ---
        date_today = dates[epoch % n_dates]
        df_today   = stage1_df[stage1_df["date"].astype(str) == str(date_today)]

        # Daily mean and uncertainty-weighted mean wind
        c1_mean  = float(df_today["pm25_pred"].mean()) if "pm25_pred" in df_today else 0.0
        wind_u_d = float(df_today["u10"].mean()) if "u10" in df_today.columns else 0.5
        wind_v_d = float(df_today["v10"].mean()) if "v10" in df_today.columns else 0.5

        # --- RAR update ---
        if use_rar and epoch >= rar_start and epoch % 50 == 0:
            try:
                xy_int, t_int = sample_rar(
                    model, n_coarse=5000, n_add=200, n_keep=N_COLLOCATION_INTERIOR - 200,
                    xy_current=xy_int, t_current=t_int,
                    wind_u=wind_u_d, wind_v=wind_v_d, device=device,
                )
            except Exception as e:
                log.debug(f"RAR update failed at epoch {epoch}: {e}")

        # --- Collocation tensors ---
        xyt_int, wu_int, wv_int = to_tensors(xy_int, t_int, wind_u_d, wind_v_d, device)
        xyt_int = xyt_int.requires_grad_(True)

        optimizer.zero_grad()

        # PDE residual
        L_pde = pde_loss(model, xyt_int, wu_int, wv_int) if lambdas.pde > 0 else torch.zeros(1, device=device)

        # Data fidelity vs Stage 1
        L_data = torch.zeros(1, device=device)
        if lambdas.data > 0 and len(df_today) > 0:
            try:
                x_s1 = torch.tensor(df_today["x_norm"].values[:, None], dtype=torch.float32, device=device)
                y_s1 = torch.tensor(df_today["y_norm"].values[:, None], dtype=torch.float32, device=device)
                t_s1 = torch.zeros_like(x_s1)
                xyt_s1 = torch.cat([x_s1, y_s1, t_s1], dim=1)
                C_pred_s1, _ = model(xyt_s1)
                C_target = torch.tensor(df_today["pm25_pred"].values, dtype=torch.float32, device=device)
                w_s1 = torch.tensor(df_today.get("weight", np.ones(len(df_today))).values,
                                     dtype=torch.float32, device=device) if "weight" in df_today else None
                L_data = data_fidelity_loss(C_pred_s1.squeeze(), C_target, w_s1)
            except Exception as e:
                log.debug(f"Data loss computation failed: {e}")

        # BC loss
        L_bc = bc_handler.compute_bc_loss(model, str(date_today), device) if lambdas.bc > 0 else torch.zeros(1, device=device)

        # Physics constraints
        L_phys = torch.zeros(1, device=device)
        if lambdas.phys > 0:
            try:
                _, (Kx, Ky, S) = model(xyt_int.detach())
                C_int, _ = model(xyt_int.detach())
                c_losses = compute_all_constraints(C_int, Kx, Ky, S, c1_mean)
                L_phys = c_losses["total"]
            except Exception as e:
                log.debug(f"Physics constraint failed: {e}")

        L_total  = total_loss(L_pde, L_data, L_bc, L_phys,
                              lambdas.pde, lambdas.data, lambdas.bc, lambdas.phys)
        L_total.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler_opt.step()

        tracker.record(
            epoch,
            float(L_pde), float(L_data), float(L_bc), float(L_phys), float(L_total), current_lr
        )
        tracker.log_epoch(epoch, every=50)

        # Checkpoint
        if epoch % save_every == 0 or epoch == n_epochs - 1:
            ckpt = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "loss": float(L_total),
            }
            torch.save(ckpt, CHECKPOINT_DIR / f"kandy_pinn_epoch{epoch:04d}.pt")
            log.info(f"Checkpoint saved (epoch {epoch})")

    log.info("═══ PINN TRAINING COMPLETE ═══")
    return tracker.history


def main():
    parser = argparse.ArgumentParser(description="Stage 3 Kandy PINN training")
    parser.add_argument("--init",    choices=["A", "B", "C"], default=None,
                        help="Init strategy: A=frozen, B=unfrozen, C=cold. Auto from transfer_decision.json if omitted")
    parser.add_argument("--epochs",  type=int, default=PINN_EPOCHS)
    parser.add_argument("--lr",      type=float, default=PINN_LR)
    parser.add_argument("--no-rar",  action="store_true", help="Disable RAR collocation")
    parser.add_argument("--profile", action="store_true", help="Quick 20-epoch smoke-test")
    args = parser.parse_args()

    device = _get_device()
    log.info(f"Device: {device}")

    # Determine initialisation
    if args.init:
        init_map = {"A": "use_pretrained_frozen", "B": "use_pretrained_unfrozen", "C": "random_init"}
        init_mode = init_map[args.init]
    else:
        decision   = load_init_decision()
        init_mode  = decision.get("stage3_init", "random_init")
    log.info(f"Initialisation mode: {init_mode}")

    model, init_mode = build_model(init_mode, device)

    stage1_df = load_stage1_data()

    n_epochs = 20 if args.profile else args.epochs
    history  = train_pinn(
        model, stage1_df, n_epochs, args.lr, device,
        use_rar=not args.no_rar,
    )

    import pandas as pd
    hist_df = pd.DataFrame(history)
    hist_df.to_csv(CHECKPOINT_DIR / "training_losses.csv", index=False)
    log.info(f"Loss history saved → {CHECKPOINT_DIR / 'training_losses.csv'}")
    log.info("✅ Stage 3 PINN training complete.")


if __name__ == "__main__":
    main()
