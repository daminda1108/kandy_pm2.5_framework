"""
loocv_convcnp.py — Leave-one-city-out cross-validation orchestrator for Stage C.

Runs the canonical v11 protocol:

  - LOOCV_CITIES = ["medellin", "chiangmai", "kathmandu"]   (N=3)
  - For each held-out city × each seed in {1, 2, 3}:
        * Build per-city (DataProcessor, TaskLoader) on train_cities
        * Train one fold via train_one_fold (v10/v11 schedule)
        * Evaluate on held-out city: r, RMSE, RMSE-bias-corrected, bias, cov90
        * Save per-fold checkpoint and per-prediction records

This module produces the numerical results in paper §5. Reported gates:
  G1 KTM r > 0.50
  G2 ChiMai r > 0.30
  G3 mean r > 0.40
  G4 cov90 KTM ∈ [0.85, 0.95]
  G5 max per-fold seed SD < 0.10
  G6 |KTM bias| < 8 µg/m³   (added v11)

The frozen Kaggle kernel
`data/processed/stage2/kaggle_kernel_convcnp_v11/convcnp_loocv_v11.py`
implements this same algorithm as a self-contained script and is the
artifact that produced the reported v11 numbers (2026-05-16).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

from ..models.convcnp_terrain import (
    build_convcnp_model,
    coverage_90,
    UNET_CHANNELS,
    LIKELIHOOD,
    INTERNAL_DENSITY,
)
from .train_convcnp import (
    build_city_dp_tl,
    train_one_fold,
    LR,
    GRAD_CLIP,
    BATCH_PER_CITY,
    WARMUP_EPOCHS,
    MAX_POOL,
)


# v11 canonical city constants (row-mean ratio; data/processed/stage2/v11_city_constants.json)
STATION_CITY_MEANS = {"medellin": 19.11, "chiangmai": 23.81, "kathmandu": 40.83}
GEOS_CITY_MEANS    = {"medellin": 23.68, "chiangmai": 40.13, "kathmandu": 72.90}
CITY_RATIOS        = {"medellin": 0.8070, "chiangmai": 0.5933, "kathmandu": 0.5601}
CITY_SIGMA_RESID   = {"medellin": 15.98,  "chiangmai": 20.33,  "kathmandu": 39.59}


@dataclass
class LoocvConfig:
    cities:        List[str]     = field(default_factory=lambda: ["medellin", "chiangmai", "kathmandu"])
    seeds:         List[int]     = field(default_factory=lambda: [1, 2, 3])
    n_epochs:      int           = 400
    ctx_fraction:  float         = 0.30          # held-out city: fraction of stations used as context at inference
    n_eval_times:  int           = 500
    lr:            float         = LR
    grad_clip:     float         = GRAD_CLIP
    batch_per_city: int          = BATCH_PER_CITY
    warmup_epochs: int           = WARMUP_EPOCHS
    max_pool:      int           = MAX_POOL
    unet_channels: Tuple[int, ...] = UNET_CHANNELS
    likelihood:    str           = LIKELIHOOD
    internal_density: int        = INTERNAL_DENSITY


def _evaluate_holdout(model, tl, raw_df, tgt_norm, shared_times,
                      pm25_std, pm25_mean_, c_prior_default,
                      n_eval: int, rng) -> Tuple[List[dict], dict]:
    """
    Evaluate model on a held-out city's target stations.

    Returns
    -------
    (per_pred_records, summary) :
        per_pred_records — list of dicts, one row per (station, timestamp)
        summary          — dict with r, rmse, rmse_bc, bias, coverage_90, n
    """
    import torch
    from scipy.stats import pearsonr

    ho_tgt_times = set(tgt_norm.index.get_level_values("time"))
    n_eval_use   = min(n_eval, len(shared_times))
    eval_sample  = rng.choice(shared_times, n_eval_use, replace=False).tolist()

    pred_lin_all, std_lin_all, obs_lin_all = [], [], []
    per_pred_records: List[dict] = []

    model.model.eval()
    for ts in eval_sample:
        if ts not in ho_tgt_times:
            continue
        try:
            X_t  = tgt_norm.xs(ts, level="time")
            task = tl(ts, context_sampling=["all", "all"], target_sampling="all")
            with torch.no_grad():
                result = model.predict(task, X_t=X_t,
                                       X_t_is_normalised=True, unnormalise=False)

            preds_norm = np.array(result["pm25"]["mean"].values.flatten(), dtype=np.float64)
            std_norm   = np.array(result["pm25"]["std"].values.flatten(),  dtype=np.float64)
            obs_norm   = np.array(task["Y_t"][0].flatten(),                 dtype=np.float64)

            preds_resid = preds_norm * pm25_std + pm25_mean_
            std_resid   = std_norm   * pm25_std
            obs_resid   = obs_norm   * pm25_std + pm25_mean_

            try:
                raw_at_t = raw_df.xs(ts, level="time")
                c_prior_per_station = raw_at_t["c_prior_scaled_raw"].values.astype(np.float64)
                if len(c_prior_per_station) != len(preds_resid):
                    c_prior_per_station = np.full(len(preds_resid), c_prior_default)
            except KeyError:
                c_prior_per_station = np.full(len(preds_resid), c_prior_default)

            preds_lin = preds_resid + c_prior_per_station
            obs_lin   = obs_resid   + c_prior_per_station

            for i, (p, s, o, cp) in enumerate(
                    zip(preds_lin, std_resid, obs_lin, c_prior_per_station)):
                if (np.isfinite(p) and np.isfinite(o) and o > 0
                        and np.isfinite(s) and s > 0):
                    pred_lin_all.append(float(p))
                    std_lin_all.append(float(s))
                    obs_lin_all.append(float(o))
                    per_pred_records.append({
                        "time": str(ts), "station_idx": int(i),
                        "pm25_obs": float(o), "pm25_pred_mean": float(p),
                        "pm25_pred_std": float(s), "c_prior_scaled": float(cp),
                    })
        except Exception as e:
            print(f"      [eval skip] {e}")
            continue

    if len(pred_lin_all) >= 20:
        pred_arr = np.array(pred_lin_all)
        std_arr  = np.array(std_lin_all)
        obs_arr  = np.array(obs_lin_all)
        r_lin, _ = pearsonr(obs_arr, pred_arr)
        rmse_raw = float(np.sqrt(np.mean((pred_arr - obs_arr) ** 2)))
        bias_raw = float(np.mean(pred_arr - obs_arr))
        bias_shift = float(np.mean(obs_arr) - np.mean(pred_arr))
        rmse_bc  = float(np.sqrt(np.mean((pred_arr + bias_shift - obs_arr) ** 2)))
        cov_90   = coverage_90(obs_arr, pred_arr, std_arr)
        summary  = dict(r=r_lin, rmse=rmse_raw, rmse_bc=rmse_bc,
                        bias=bias_raw, coverage_90=cov_90, n=len(pred_lin_all))
    else:
        summary  = dict(r=np.nan, rmse=np.nan, rmse_bc=np.nan,
                        bias=np.nan, coverage_90=np.nan, n=len(pred_lin_all))

    return per_pred_records, summary


def run_loocv(city_data: Dict[str, pd.DataFrame],
              city_raw:  Dict[str, pd.DataFrame],
              city_terrain: Dict[str, "xr.DataArray"],
              cfg: LoocvConfig,
              out_dir: Path,
              ) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run the full LOOCV grid. For each (held_out_city, seed):

      1. Build per-city DP/TL on `train_cities = cities - {held_out}`.
      2. Construct a fresh ConvCNP and train via `train_one_fold`.
      3. Evaluate on held-out city's target stations.
      4. Append per-seed row to `all_results`; per-prediction rows to `all_predictions`.
      5. Save fold checkpoint to `out_dir`.

    Parameters
    ----------
    city_data : dict[city -> feature_df]   from convcnp_loader.load_city
    city_raw  : dict[city -> raw_df]       from convcnp_loader.load_city
    city_terrain : dict[city -> xr.DataArray]  from convcnp_loader.load_terrain_da
    cfg : LoocvConfig
    out_dir : Path
        Where to write per-fold checkpoints. Created if missing.

    Returns
    -------
    (perseed_df, predictions_df) : (pd.DataFrame, pd.DataFrame)
        perseed_df       — one row per (city, seed): r, rmse, rmse_bc, bias, cov90, n.
        predictions_df   — one row per (city, seed, time, station_idx) prediction.
    """
    import torch

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_results:     List[dict] = []
    all_predictions: List[dict] = []
    t_start = time.time()

    for held_out in cfg.cities:
        for seed in cfg.seeds:
            torch.manual_seed(seed)
            np.random.seed(seed)
            rng = np.random.default_rng(seed)

            print("\n" + "=" * 60)
            print(f"LOOCV fold = {held_out.upper()}  |  seed = {seed}")
            print(f"  total elapsed: {(time.time()-t_start)/60:.1f} min")

            train_cities = [c for c in cfg.cities if c != held_out]
            print(f"  Train cities: {train_cities}")

            # Per-city DP/TL for training
            train_info: Dict[str, dict] = {}
            for city in train_cities:
                df  = city_data[city]
                dz  = city_terrain[city]
                all_lats = df.index.get_level_values("lat").unique().tolist()
                n_ctx    = max(1, int(len(all_lats) * 0.5))
                ctx_lats = set(rng.choice(all_lats, n_ctx, replace=False).tolist())
                tgt_lats = [l for l in all_lats if l not in ctx_lats] or all_lats
                ctx_df = df[df.index.get_level_values("lat").isin(ctx_lats)]
                tgt_df = df[df.index.get_level_values("lat").isin(tgt_lats)][["pm25"]]
                dp, tl, dz_n, ctx_n, tgt_n, shared = build_city_dp_tl(dz, ctx_df, tgt_df)
                train_info[city] = dict(dp=dp, tl=tl, dz_n=dz_n,
                                        ctx_n=ctx_n, tgt_n=tgt_n, shared=shared)
                print(f"    {city}: {len(shared):,} timestamps | "
                      f"{n_ctx} ctx / {len(tgt_lats)} tgt stns | terrain {dz.shape}")

            # Build model (using one training city's DP/TL as reference schema)
            ref_city = train_cities[0]
            model = build_convcnp_model(
                train_info[ref_city]["dp"], train_info[ref_city]["tl"],
                unet_channels=cfg.unet_channels,
                likelihood=cfg.likelihood,
                internal_density=cfg.internal_density,
            )
            n_params = sum(p.numel() for p in model.model.parameters())
            print(f"  ConvNP params: {n_params:,}")

            # Train
            train_one_fold(
                model, train_info, n_epochs=cfg.n_epochs, rng=rng,
                lr=cfg.lr, grad_clip=cfg.grad_clip,
                batch_per_city=cfg.batch_per_city,
                warmup_epochs=cfg.warmup_epochs,
                max_pool=cfg.max_pool,
            )

            # Held-out city DP/TL for inference
            print(f"\n  Evaluating on {held_out.upper()} (seed {seed})...")
            ho_df    = city_data[held_out]
            ho_raw   = city_raw[held_out]
            ho_dz    = city_terrain[held_out]
            ho_stns  = ho_df.index.get_level_values("lat").unique()
            n_ctx    = max(1, int(len(ho_stns) * cfg.ctx_fraction))
            ctx_mask = np.zeros(len(ho_stns), dtype=bool)
            ctx_mask[rng.choice(len(ho_stns), n_ctx, replace=False)] = True

            ctx_lats = ho_stns[ctx_mask]
            tgt_lats = ho_stns[~ctx_mask]
            ho_ctx_df  = ho_df[ho_df.index.get_level_values("lat").isin(ctx_lats)]
            ho_tgt_df  = ho_df[ho_df.index.get_level_values("lat").isin(tgt_lats)][["pm25"]]
            ho_raw_tgt = ho_raw[ho_raw.index.get_level_values("lat").isin(tgt_lats)]

            ho_dp, ho_tl, ho_dz_n, ho_ctx_n, ho_tgt_n, ho_shared = build_city_dp_tl(
                ho_dz, ho_ctx_df, ho_tgt_df)
            print(f"    Context stations: {n_ctx}, Target stations: {len(tgt_lats)}, "
                  f"Timestamps: {len(ho_shared):,}")

            pm25_std   = ho_dp.config["pm25"]["params"]["std"]
            pm25_mean_ = ho_dp.config["pm25"]["params"]["mean"]

            per_pred_records, summary = _evaluate_holdout(
                model, ho_tl, ho_raw_tgt, ho_tgt_n, ho_shared,
                pm25_std=pm25_std, pm25_mean_=pm25_mean_,
                c_prior_default=STATION_CITY_MEANS[held_out],
                n_eval=cfg.n_eval_times, rng=rng,
            )

            row = dict(city=held_out, seed=seed, **summary)
            print(f"    r={summary['r']:.3f}  RMSE={summary['rmse']:.2f}  "
                  f"RMSE_bc={summary['rmse_bc']:.2f}  bias={summary['bias']:+.2f}  "
                  f"cov90={summary['coverage_90']:.2%}  N={summary['n']}")

            all_results.append(row)
            for r in per_pred_records:
                r["city"] = held_out
                r["seed"] = seed
                all_predictions.append(r)

            ckpt_path = out_dir / f"convcnp_holdout_{held_out}_seed{seed}.pt"
            torch.save(model.model.state_dict(), ckpt_path)
            print(f"    Checkpoint: {ckpt_path}")

    perseed_df     = pd.DataFrame(all_results)
    predictions_df = pd.DataFrame(all_predictions)
    return perseed_df, predictions_df
