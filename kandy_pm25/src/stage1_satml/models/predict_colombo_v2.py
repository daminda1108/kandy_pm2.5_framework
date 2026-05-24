"""
predict_colombo_v2.py — Pre-reg §6.6 Embassy Colombo OOD inference.

Protocol (per pre-reg §6.6, verbatim):
  "Single one-shot inference of trained model on Embassy hourly aggregated to
   daily. Report coverage, residual distribution. Do not retrain on Embassy."

Pipeline:
  1. Train a single quantile XGBoost on the FULL Kandy FECT dataset (no LOMO
     holdout) — this is the "trained model" that ships with the paper.
     Hyperparameters frozen at the same values used by train_xgboost_v2.py
     for the main LOMO results.
  2. Load Colombo v2 dataset (built by build_dataset_v2_colombo.py).
  3. Predict q05/q50/q95 on Colombo.
  4. Compute metrics: pooled RMSE, R², bias, MAE, 90% PI coverage, PI width,
     CRPS (pinball-based estimator).
  5. Save predictions + metrics + per-year breakdown.

Outputs (under data/processed/stage1_v2/training/):
  predictions_colombo_v2.parquet     (per-row q05/q50/q95 + baselines)
  metrics_colombo_v2.csv             (pooled + per-year)
  model_xgb_v2_full_kandy.json       (trained model — XGBoost JSON serialisation)

Usage:
  python -m src.stage1_satml.models.predict_colombo_v2
  python src/stage1_satml/models/predict_colombo_v2.py --force

Reference: pre-reg §6.6, §5.5 (uses XGBoost-quantile primary model).
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import PROC_DIR, MODELS_DIR, LOG_FORMAT, LOG_DATEFMT

from src.stage1_satml.models.train_xgboost_v2 import (
    LABEL_COL, FEATURE_COLS, TRAIN_YEARS, RANDOM_SEED, QUANTILES,
    load_hyperparameters,
    rmse, r2, bias, mae,
    crps_quantile,
    baseline_persistence, baseline_doy_climatology,
    baseline_cams_scaled, baseline_geos_scaled,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("predict_colombo_v2")

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

KANDY_DATASET   = PROC_DIR / "stage1_v2" / "dataset_v2_multistation_daily.parquet"
COLOMBO_DATASET = PROC_DIR / "stage1_v2" / "dataset_v2_colombo_daily.parquet"

OUT_DIR    = PROC_DIR / "stage1_v2" / "training"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PREDS  = OUT_DIR / "predictions_colombo_v2.parquet"
OUT_METRIC = OUT_DIR / "metrics_colombo_v2.csv"

# Model goes to results/models so it's discoverable alongside v1 artefacts.
OUT_MODEL  = MODELS_DIR / "xgboost_v2_full_kandy.ubj"


# ─────────────────────────────────────────────────────────────────────────────
# Training (single model on all FECT, no LOMO)
# ─────────────────────────────────────────────────────────────────────────────

def train_full_model(force_retrain: bool) -> tuple[xgb.XGBRegressor, list[str]]:
    if OUT_MODEL.exists() and not force_retrain:
        log.info(f"  loading existing full-Kandy model: {OUT_MODEL}")
        model = xgb.XGBRegressor()
        model.load_model(OUT_MODEL)
        # Read feature list from the model
        feats = model.get_booster().feature_names or []
        log.info(f"  loaded {len(feats)} feature columns from saved model")
        return model, feats

    log.info("  training quantile XGBoost on full Kandy FECT (no LOMO)")
    df = pd.read_parquet(KANDY_DATASET)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df = df[df["year"].isin(TRAIN_YEARS)].reset_index(drop=True)
    df = df.dropna(subset=[LABEL_COL]).reset_index(drop=True)
    feats = [c for c in FEATURE_COLS if c in df.columns]
    X = df[feats].astype(np.float32)
    y = df[LABEL_COL].astype(np.float32)
    log.info(f"  X={X.shape}  y={y.shape}  feats={len(feats)}")

    params = load_hyperparameters()
    # Strip non-quantile keys + force multi-quantile objective
    drop = {"objective", "eval_metric", "early_stopping_rounds"}
    params = {k: v for k, v in params.items() if k not in drop}
    params.update({
        "objective":      "reg:quantileerror",
        "quantile_alpha": list(QUANTILES),
        "tree_method":    "hist",
        "random_state":   RANDOM_SEED,
        "n_jobs":         -1,
    })
    model = xgb.XGBRegressor(**params)
    model.fit(X, y)
    model.save_model(OUT_MODEL)
    log.info(f"  saved {OUT_MODEL}")
    return model, feats


# ─────────────────────────────────────────────────────────────────────────────
# Predict Colombo
# ─────────────────────────────────────────────────────────────────────────────

def predict_colombo(model: xgb.XGBRegressor, feats: list[str]) -> pd.DataFrame:
    log.info("  loading Colombo dataset")
    c = pd.read_parquet(COLOMBO_DATASET)
    c["date"] = pd.to_datetime(c["date"])
    c["year"] = c["date"].dt.year
    c = c.dropna(subset=[LABEL_COL]).reset_index(drop=True)
    log.info(f"  Colombo: {len(c):,} rows  [{c['date'].min().date()} → {c['date'].max().date()}]")

    # Align feature columns to the model's expected names
    missing = [f for f in feats if f not in c.columns]
    if missing:
        log.warning(f"  features missing in Colombo dataset (will be NaN): {missing}")
        for m in missing:
            c[m] = np.nan
    X = c[feats].astype(np.float32)
    q = model.predict(X)               # shape (n, 3)
    c["q05"], c["q50"], c["q95"] = q[:, 0], q[:, 1], q[:, 2]

    # Baselines (baseline_* return ndarrays already)
    c["baseline_persistence"]  = baseline_persistence(c)
    c["baseline_doy_clim"]     = baseline_doy_climatology(c, c)    # in-sample clim on Colombo days
    c["baseline_cams_scaled"]  = baseline_cams_scaled(c)
    c["baseline_geos_scaled"]  = baseline_geos_scaled(c)
    return c


def colombo_metrics(c: pd.DataFrame) -> pd.DataFrame:
    """Pooled + per-year metrics for the model + each baseline."""
    rows = []
    models = {
        "xgboost_v2_quantile":  "q50",
        "persistence":          "baseline_persistence",
        "doy_clim":             "baseline_doy_clim",
        "cams_scaled":          "baseline_cams_scaled",
        "geos_scaled":          "baseline_geos_scaled",
    }
    for tag, col in models.items():
        if col not in c.columns:
            continue
        for scope, sub in (("pooled", c),
                           *((f"year_{y}", c[c["year"] == y]) for y in sorted(c["year"].unique()))):
            mask = sub[col].notna() & sub[LABEL_COL].notna()
            if mask.sum() < 5:
                continue
            y_true = sub.loc[mask, LABEL_COL].to_numpy(dtype=np.float64)
            y_hat  = sub.loc[mask, col].to_numpy(dtype=np.float64)
            r = {
                "model":   tag,
                "scope":   scope,
                "n":       int(mask.sum()),
                "rmse":    rmse(y_true, y_hat),
                "mae":     mae(y_true, y_hat),
                "bias":    bias(y_true, y_hat),
                "r2":      r2(y_true, y_hat),
            }
            if tag == "xgboost_v2_quantile":
                q05 = sub.loc[mask, "q05"].to_numpy(dtype=np.float64)
                q95 = sub.loc[mask, "q95"].to_numpy(dtype=np.float64)
                cov = float(((q05 <= y_true) & (y_true <= q95)).mean())
                width = float((q95 - q05).mean())
                q_preds = np.stack([q05, y_hat, q95], axis=1)   # (n, 3)
                crps = crps_quantile(y_true, q_preds)
                r.update({
                    "cov90":     cov,
                    "pi_width":  width,
                    "crps":      float(crps),
                })
            rows.append(r)
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="overwrite predictions + retrain model")
    args = ap.parse_args()

    log.info("── train full-Kandy quantile XGBoost (or load if cached) ──")
    model, feats = train_full_model(force_retrain=args.force)

    log.info("── one-shot inference on Colombo ──")
    c = predict_colombo(model, feats)

    log.info("── compute metrics ──")
    metrics = colombo_metrics(c)

    c.to_parquet(OUT_PREDS, index=False)
    log.info(f"  wrote {OUT_PREDS}  ({len(c):,} rows × {len(c.columns)} cols)")
    metrics.to_csv(OUT_METRIC, index=False)
    log.info(f"  wrote {OUT_METRIC}  ({len(metrics):,} rows)")

    # ── pooled summary ──
    log.info("\n── §6.6 OOD pooled results (Embassy Colombo, 2019-2025) ──")
    pooled = metrics[metrics["scope"] == "pooled"].sort_values("rmse")
    log.info(f"  {'model':<22}  {'n':>5}  {'rmse':>6}  {'mae':>5}  {'bias':>6}  {'r2':>6}  {'cov90':>5}  {'crps':>5}")
    for _, r in pooled.iterrows():
        cov = r["cov90"] if pd.notna(r.get("cov90")) else float("nan")
        crps = r["crps"] if pd.notna(r.get("crps")) else float("nan")
        log.info(f"  {r['model']:<22}  {r['n']:>5}  {r['rmse']:>6.2f}  {r['mae']:>5.2f}  "
                 f"{r['bias']:>+6.2f}  {r['r2']:>+6.3f}  "
                 f"{cov:>5.2f}  {crps:>5.2f}")

    # ── per-year coverage (decision rule §7 row 5: H4 within [0.85, 0.95]) ──
    log.info("\n── §6.6 per-year coverage trend ──")
    xgb_yr = metrics[(metrics["model"] == "xgboost_v2_quantile") &
                     (metrics["scope"].str.startswith("year_"))].sort_values("scope")
    for _, r in xgb_yr.iterrows():
        cov = r["cov90"] if pd.notna(r.get("cov90")) else float("nan")
        log.info(f"  {r['scope']:<10}  n={r['n']:>4}  rmse={r['rmse']:5.2f}  "
                 f"bias={r['bias']:+5.2f}  cov90={cov:.2f}")

    # ── H4 verdict ──
    pooled_xgb = pooled[pooled["model"] == "xgboost_v2_quantile"]
    if len(pooled_xgb) > 0:
        cov = float(pooled_xgb.iloc[0]["cov90"])
        ok = 0.85 <= cov <= 0.95
        verdict = "SATISFIED" if ok else "VIOLATED"
        log.info(f"\n  H4 (cov90 ∈ [0.85, 0.95] on Colombo OOD): {verdict}  (cov90={cov:.3f})")


if __name__ == "__main__":
    main()
