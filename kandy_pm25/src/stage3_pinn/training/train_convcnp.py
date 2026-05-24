"""
train_convcnp.py — Training loop for one Stage C LOOCV fold.

Implements the canonical v10/v11 training schedule:

  - LR        = 5e-5
  - warmup    = LinearLR (start 0.1 → 1.0) for first 50 epochs
  - main      = CosineAnnealingLR (T_max = N_EPOCHS − 50, eta_min = 1e-6)
  - grad clip = 1.0
  - tasks/epoch = `batch_per_city × len(train_cities)` per epoch
  - best-checkpoint selection on epoch-mean training NLL

Each LOOCV fold trains on `train_cities` (all source cities except held_out),
samples context/target station splits per city per epoch via the seeded RNG,
and saves the best-loss state_dict.
"""

from __future__ import annotations

import time
from typing import Dict, List, Sequence, Tuple

import numpy as np


# Canonical hyperparameters from v10/v11 (locked 2026-05-10)
LR              = 5e-5
GRAD_CLIP       = 1.0
BATCH_PER_CITY  = 12
WARMUP_EPOCHS   = 50
MAX_POOL        = 6000           # per-city timestamp cap (memory / wall-time)


def build_city_dp_tl(dz_da, ctx_df, tgt_df):
    """
    Build deepsensor (DataProcessor, TaskLoader) for one city's
    (terrain, context-stations, target-stations) triple.

    Returns
    -------
    (dp, tl, dz_n, ctx_n, tgt_n, shared) : tuple
        dp     — DataProcessor fit on this city's data
        tl     — TaskLoader (context = [terrain, context-station-df],
                              target = target-station-df)
        dz_n   — normalised terrain DataArray
        ctx_n  — normalised context DataFrame
        tgt_n  — normalised target DataFrame
        shared — sorted list of timestamps present in BOTH ctx_n and tgt_n
    """
    from deepsensor.data import DataProcessor, TaskLoader

    dp                = DataProcessor(x1_name="lat", x2_name="lon")
    dz_n, ctx_n, tgt_n = dp([dz_da, ctx_df, tgt_df])
    tl                = TaskLoader(context=[dz_n, ctx_n], target=tgt_n)
    ctx_times = set(ctx_n.index.get_level_values("time"))
    tgt_times = set(tgt_n.index.get_level_values("time"))
    shared    = sorted(ctx_times & tgt_times)
    return dp, tl, dz_n, ctx_n, tgt_n, shared


def train_one_fold(model,
                   train_info: Dict[str, dict],
                   n_epochs: int,
                   rng: np.random.Generator,
                   lr: float = LR,
                   grad_clip: float = GRAD_CLIP,
                   batch_per_city: int = BATCH_PER_CITY,
                   warmup_epochs: int = WARMUP_EPOCHS,
                   max_pool: int = MAX_POOL,
                   log_every: int = 50,
                   ) -> Tuple[float, Dict, int]:
    """
    Train one LOOCV fold. Modifies `model.model` in place; on return the
    model weights are restored to the best-loss checkpoint.

    Parameters
    ----------
    model : deepsensor.model.ConvNP
        Constructed by `convcnp_terrain.build_convcnp_model`.
    train_info : dict[city_name -> {dp, tl, dz_n, ctx_n, tgt_n, shared}]
        Output of `build_city_dp_tl` for each training city.
        `shared` is the list of timestamps available for sampling.
    n_epochs : int
        Total training epochs. 400 for Kaggle (12-hr ceiling); 1000+ on uni.
    rng : np.random.Generator
        Seeded RNG for reproducible per-epoch timestamp sampling.
    lr : float
    grad_clip : float
    batch_per_city : int
        Number of timestamps sampled per city per epoch.
    warmup_epochs : int
        Linear warmup duration.
    max_pool : int
        Maximum per-city timestamps to consider. Caps memory + wall-time.
    log_every : int
        Print progress every N epochs.

    Returns
    -------
    (best_loss, best_state, nan_steps) : (float, dict, int)
        best_loss  — minimum epoch-mean training loss seen
        best_state — corresponding state_dict (CPU tensors)
        nan_steps  — count of optimisation steps with non-finite loss (skipped)
    """
    import torch

    train_cities = list(train_info.keys())

    optimizer = torch.optim.Adam(model.model.parameters(), lr=lr)
    warmup    = torch.optim.lr_scheduler.LinearLR(
        optimizer, start_factor=0.1, total_iters=warmup_epochs)
    cosine    = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=n_epochs - warmup_epochs, eta_min=1e-6)

    # Cap each city's pool of available timestamps
    for city in train_cities:
        pool = train_info[city]["shared"]
        if len(pool) > max_pool:
            train_info[city]["shared"] = rng.choice(pool, max_pool, replace=False).tolist()

    t0           = time.time()
    best_loss    = float("inf")
    best_state   = None
    nan_steps    = 0

    for epoch in range(1, n_epochs + 1):
        model.model.train()

        # Sample one batch of tasks (batch_per_city timestamps per training city)
        tasks = []
        for city in train_cities:
            info     = train_info[city]
            batch_ts = rng.choice(
                info["shared"],
                size=min(batch_per_city, len(info["shared"])),
                replace=False,
            )
            for ts in batch_ts:
                task = info["tl"](ts, context_sampling=["all", "all"],
                                  target_sampling="all")
                tasks.append(task)

        epoch_losses = []
        for task in tasks:
            loss = model.loss_fn(task, normalise=True)
            if not torch.isfinite(loss):
                nan_steps += 1
                continue
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.model.parameters(), grad_clip)
            optimizer.step()
            epoch_losses.append(loss.item())

        if epoch <= warmup_epochs:
            warmup.step()
        else:
            cosine.step()

        if epoch_losses:
            mean_loss = float(np.mean(epoch_losses))
            if mean_loss < best_loss:
                best_loss  = mean_loss
                best_state = {k: v.cpu().clone() for k, v in model.model.state_dict().items()}

        if epoch % log_every == 0:
            mean_loss = float(np.mean(epoch_losses)) if epoch_losses else float("nan")
            lr_now    = optimizer.param_groups[0]["lr"]
            elapsed   = time.time() - t0
            print(f"    Epoch {epoch:3d}/{n_epochs}  loss={mean_loss:.4f}  "
                  f"best={best_loss:.4f}  lr={lr_now:.2e}  nan={nan_steps}  "
                  f"elapsed={elapsed/60:.1f}min")

    if best_state is not None:
        model.model.load_state_dict(best_state)
        print(f"  Restored best checkpoint (loss={best_loss:.4f})")

    return best_loss, best_state, nan_steps
