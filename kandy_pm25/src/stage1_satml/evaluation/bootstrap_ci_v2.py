"""
bootstrap_ci_v2.py — Bootstrap confidence intervals for v2 headline metrics.

CLAUDE.md HARD RULE (pre-redesign 2026-05-08):
  "3-seed runs with bootstrap CIs on every reported r. Single-run point
   estimates are uninterpretable."

This script computes percentile bootstrap CIs (B=1000 resamples) on the
pooled predictions parquets produced by train_xgboost_v2 / train_ngboost_v2
/ predict_colombo_v2. Resamples (date, sensor) pairs with replacement —
NOT independent days, because lag features induce per-station temporal
dependence. We use a block-bootstrap option for the time-correlated case;
default falls back to row-level resampling, which is conservative for the
pooled-LOMO aggregate but underestimates dependence within a fold.

Metrics returned with [2.5, 97.5] percentile CI:
  rmse, mae, bias, r2          (point estimators)
  cov90, pi_width, crps        (UQ — for the quantile model only)

Outputs (under data/processed/stage1_v2/training/):
  bootstrap_ci_v2.csv          (one row per (config, metric) with mean + CI)
  bootstrap_ci_v2_summary.txt  (pretty-printed paper-ready table)

Usage:
  python -m src.stage1_satml.evaluation.bootstrap_ci_v2
  python src/stage1_satml/evaluation/bootstrap_ci_v2.py
  python src/stage1_satml/evaluation/bootstrap_ci_v2.py --B 1000
  python src/stage1_satml/evaluation/bootstrap_ci_v2.py --block-size 30

Reference: CLAUDE.md HARD RULES; pre-reg §5.5 metrics.
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import PROC_DIR, LOG_FORMAT, LOG_DATEFMT

from src.stage1_satml.models.train_xgboost_v2 import (
    rmse, mae, bias, r2, crps_quantile,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("bootstrap_ci_v2")

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

TRAIN_DIR = PROC_DIR / "stage1_v2" / "training"

INPUTS: list[dict] = [
    {"config":  "xgboost_v2_quantile (Kandy LOMO)",
     "parquet": TRAIN_DIR / "predictions_lomo_v2.parquet",
     "y_col":   "y_true",  "q05": "xgb_q05", "q50": "xgb_q50", "q95": "xgb_q95",
     "baselines": {
         "persistence":  "baseline_persistence",
         "doy_clim":     "baseline_doy_clim",
         "cams_scaled":  "baseline_cams_scaled",
         "geos_scaled":  "baseline_geos_scaled",
     }},
    {"config":  "xgboost_v2_optuna_tuned (Kandy LOMO)",
     "parquet": TRAIN_DIR / "predictions_lomo_v2_tuned.parquet",
     "y_col":   "y_true",  "q05": "xgb_q05", "q50": "xgb_q50", "q95": "xgb_q95",
     "baselines": {}},
    {"config":  "ngboost_v2_tfixedf5 (Kandy LOMO)",
     "parquet": TRAIN_DIR / "predictions_lomo_ngboost.parquet",
     "y_col":   "y_true", "q05": "ngb_q05", "q50": "ngb_q50", "q95": "ngb_q95",
     "baselines": {}},
    {"config":  "xgboost_v2 (Colombo OOD)",
     "parquet": TRAIN_DIR / "predictions_colombo_v2.parquet",
     "y_col":   "pm25_observed", "q05": "q05", "q50": "q50", "q95": "q95",
     "baselines": {
         "persistence":  "baseline_persistence",
         "doy_clim":     "baseline_doy_clim",
         "cams_scaled":  "baseline_cams_scaled",
         "geos_scaled":  "baseline_geos_scaled",
     }},
]


# ─────────────────────────────────────────────────────────────────────────────
# Bootstrap resampling
# ─────────────────────────────────────────────────────────────────────────────

def block_bootstrap_indices(n: int, block_size: int, rng: np.random.Generator,
                            ordered_idx: np.ndarray | None = None) -> np.ndarray:
    """Moving-block bootstrap (Politis & Romano 1994). Sample n/block_size
    starting indices uniformly with replacement, concatenate block_size
    consecutive rows from each. Works on a pre-sorted (date, sensor) index.
    block_size=1 collapses to standard iid bootstrap."""
    if block_size <= 1:
        return rng.integers(0, n, size=n)
    n_blocks = (n + block_size - 1) // block_size
    starts = rng.integers(0, max(1, n - block_size + 1), size=n_blocks)
    idx = np.concatenate([np.arange(s, s + block_size) for s in starts])[:n]
    if ordered_idx is not None:
        return ordered_idx[idx]
    return idx


def bootstrap_metrics(y: np.ndarray, q05: np.ndarray | None,
                      q50: np.ndarray, q95: np.ndarray | None,
                      B: int, block_size: int,
                      seed: int = 42) -> dict[str, tuple[float, float, float]]:
    """Return {metric: (point, ci_low, ci_high)} where point is the in-sample
    estimate and CI is the 2.5–97.5 percentile bootstrap interval."""
    rng = np.random.default_rng(seed)
    n = len(y)
    ordered = np.arange(n)

    boots: dict[str, list[float]] = {
        "rmse": [], "mae": [], "bias": [], "r2": [],
    }
    if q05 is not None and q95 is not None:
        boots.update({"cov90": [], "pi_width": [], "crps": []})

    for _ in range(B):
        idx = block_bootstrap_indices(n, block_size, rng, ordered)
        ys = y[idx]
        ps = q50[idx]
        boots["rmse"].append(rmse(ys, ps))
        boots["mae"].append(mae(ys, ps))
        boots["bias"].append(bias(ys, ps))
        boots["r2"].append(r2(ys, ps))
        if q05 is not None and q95 is not None:
            qs05 = q05[idx]; qs95 = q95[idx]
            boots["cov90"].append(float(((qs05 <= ys) & (ys <= qs95)).mean()))
            boots["pi_width"].append(float((qs95 - qs05).mean()))
            qps = np.stack([qs05, ps, qs95], axis=1)
            boots["crps"].append(crps_quantile(ys, qps))

    out: dict[str, tuple[float, float, float]] = {}
    point = {
        "rmse": rmse(y, q50), "mae": mae(y, q50), "bias": bias(y, q50),
        "r2": r2(y, q50),
    }
    if q05 is not None and q95 is not None:
        point["cov90"]    = float(((q05 <= y) & (y <= q95)).mean())
        point["pi_width"] = float((q95 - q05).mean())
        point["crps"]     = crps_quantile(y, np.stack([q05, q50, q95], axis=1))

    for m, vals in boots.items():
        arr = np.array(vals)
        low  = float(np.percentile(arr, 2.5))
        high = float(np.percentile(arr, 97.5))
        out[m] = (point[m], low, high)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=1000, help="bootstrap iterations")
    ap.add_argument("--block-size", type=int, default=30,
                    help="moving-block size (1 = iid). 30 days is the canonical "
                         "monthly-block for daily PM2.5 (atmospheric autocorr decays "
                         "within ~14d but seasonal blocks > 30d).")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rows = []
    for cfg in INPUTS:
        path = cfg["parquet"]
        if not path.exists():
            log.warning(f"  missing parquet: {path}; skipping")
            continue
        df = pd.read_parquet(path)
        df = df.sort_values("date").reset_index(drop=True) if "date" in df.columns else df

        # Primary model (quantile)
        y_all = df[cfg["y_col"]].to_numpy(dtype=np.float64)
        mask = (~np.isnan(y_all)) & (~np.isnan(df[cfg["q50"]].to_numpy(dtype=np.float64)))
        y = y_all[mask]
        q05 = df[cfg["q05"]].to_numpy(dtype=np.float64)[mask]
        q50 = df[cfg["q50"]].to_numpy(dtype=np.float64)[mask]
        q95 = df[cfg["q95"]].to_numpy(dtype=np.float64)[mask]

        log.info(f"── {cfg['config']}  n={len(y):,}  B={args.B}  block={args.block_size} ──")
        res = bootstrap_metrics(y, q05, q50, q95, B=args.B,
                                block_size=args.block_size, seed=args.seed)
        for metric, (point, lo, hi) in res.items():
            rows.append({"config": cfg["config"], "model": "primary",
                         "metric": metric, "point": point, "ci_low": lo, "ci_high": hi})
            log.info(f"  {metric:<10}  {point:>+8.3f}  [{lo:>+7.3f}, {hi:>+7.3f}]")

        # Baselines (point-estimator only — no UQ)
        for b_name, b_col in cfg.get("baselines", {}).items():
            if b_col not in df.columns:
                continue
            yh = df[b_col].to_numpy(dtype=np.float64)
            m_b = (~np.isnan(y_all)) & (~np.isnan(yh))
            if m_b.sum() < 30:
                continue
            y_b = y_all[m_b]
            yh = yh[m_b]
            log.info(f"  baseline: {b_name}  n={len(y_b):,}")
            res_b = bootstrap_metrics(y_b, None, yh, None, B=args.B,
                                      block_size=args.block_size, seed=args.seed)
            for metric, (point, lo, hi) in res_b.items():
                rows.append({"config": cfg["config"], "model": f"baseline_{b_name}",
                             "metric": metric, "point": point, "ci_low": lo, "ci_high": hi})

    out_csv = TRAIN_DIR / "bootstrap_ci_v2.csv"
    out_txt = TRAIN_DIR / "bootstrap_ci_v2_summary.txt"
    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_csv, index=False)
    log.info(f"\nwrote {out_csv}  ({len(df_out)} rows)")

    # ── pretty summary ──
    lines = ["# Stage 1 v2 — bootstrap CIs (B={}, block={}d)".format(args.B, args.block_size), ""]
    for cfg_name in df_out["config"].unique():
        sub = df_out[df_out["config"] == cfg_name]
        lines.append(f"## {cfg_name}\n")
        lines.append("| model | metric | point | 95% CI low | 95% CI high |")
        lines.append("|---|---|---:|---:|---:|")
        for _, r in sub.iterrows():
            lines.append(f"| {r['model']} | {r['metric']} | {r['point']:+.3f} | "
                         f"{r['ci_low']:+.3f} | {r['ci_high']:+.3f} |")
        lines.append("")
    out_txt.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"wrote {out_txt}")


if __name__ == "__main__":
    main()
