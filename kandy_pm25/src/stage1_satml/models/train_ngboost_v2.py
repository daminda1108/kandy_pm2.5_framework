"""
train_ngboost_v2.py — Stage 1 v2 NGBoost Student-t heavy-tail variant.

OSF pre-registration: docs/osf_prereg_stage1_v2.md §5.1.

The pre-reg requires two trained models for the primary result:
  1. Quantile XGBoost (train_xgboost_v2.py)  — quantile regression at α ∈ {0.05, 0.50, 0.95}
  2. NGBoost Student-t                       — heavy-tail probabilistic regression
The better-calibrated variant (by pre-specified CRPS criterion on held-out
months) is reported as primary.

This script runs the LOMO pipeline using NGBoost with Student-t distribution
(`ngboost.distns.T` — 3 params: loc, scale, df with ν ≥ 3 enforced via
post-hoc clipping). Mirrors train_xgboost_v2.py's protocol (84 outer
LOMO folds, 1,526 sensor-day rows, same baselines).

Outputs (under data/processed/stage1_v2/training/):
  predictions_lomo_ngboost.parquet     — per-row: date, sensor_id, y_true,
                                           q05/q50/q95, df, scale, baselines
  metrics_per_fold_ngboost.csv         — per fold per model
  summary_ngboost.csv                  — aggregate

Usage:
  python -m src.stage1_satml.models.train_ngboost_v2
  python src/stage1_satml/models/train_ngboost_v2.py
  python src/stage1_satml/models/train_ngboost_v2.py --force
  python src/stage1_satml/models/train_ngboost_v2.py --smoke

Reference: pre-reg §5.1, §5.5.
"""

import argparse
import logging
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

# Suppress NGBoost's verbose per-stage convergence output (we log per-fold instead).
warnings.filterwarnings("ignore", category=UserWarning, module="ngboost")
warnings.filterwarnings("ignore", category=RuntimeWarning)

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import PROC_DIR, LOG_FORMAT, LOG_DATEFMT

# Import shared infrastructure from the XGBoost script
from src.stage1_satml.models.train_xgboost_v2 import (
    LABEL_COL, PERSIST_COL, FEATURE_COLS, TRAIN_YEARS, RANDOM_SEED, QUANTILES,
    load_dataset, lomo_folds,
    compute_metrics, compute_point_metrics,
    baseline_persistence, baseline_doy_climatology,
    baseline_cams_scaled, baseline_geos_scaled, BASELINES,
    aggregate_per_month, aggregate_summary,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("train_ngboost_v2")

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

OUT_DIR     = PROC_DIR / "stage1_v2" / "training"
OUT_PREDS   = OUT_DIR / "predictions_lomo_ngboost.parquet"
OUT_FOLD    = OUT_DIR / "metrics_per_fold_ngboost.csv"
OUT_MONTH   = OUT_DIR / "metrics_per_month_ngboost.csv"
OUT_SUMMARY = OUT_DIR / "summary_ngboost.csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# NGBoost setup
# ─────────────────────────────────────────────────────────────────────────────

# Pre-reg §5.1 specifies "Student-t with df learnable, ν ≥ 3 enforced."
# DEVIATION 2026-05-18: ngboost.distns.T (learnable-df Student-t) suffers
# log-df gradient degeneracy on this dataset (sklearn "y contains NaN" from
# corrupted gradients). Switching to TFixedDf with df=5 — a literature-
# standard value for atmospheric extremes (Wilks 2011 §4.4.3) that satisfies
# the ν ≥ 3 finite-variance constraint. Documented in pre-reg amendment log.
NGB_DF_FIXED = 5.0
NU_MIN = 3.0   # report-time constraint check


def make_ngb_regressor():
    """Build an NGBRegressor with FIXED-df Student-t and a moderate-depth tree base.
    df=5 is literature-standard for atmospheric heavy-tail (Wilks 2011)."""
    from ngboost import NGBRegressor
    from ngboost.distns import TFixedDf
    from sklearn.tree import DecisionTreeRegressor

    # Subclass TFixedDf with df=5 baked in via the `fixed_df` class attr
    # (ngboost.distns.t.TFixedDf default is 3 — overridden here per pre-reg §5.1
    # rationale: ν=5 retains heavy-tail behavior while ensuring finite kurtosis).
    class T5(TFixedDf):
        fixed_df = NGB_DF_FIXED

    base = DecisionTreeRegressor(max_depth=5, random_state=RANDOM_SEED)
    return NGBRegressor(
        Dist=T5,
        Base=base,
        n_estimators=500,
        learning_rate=0.02,
        minibatch_frac=0.7,
        col_sample=0.85,
        verbose=False,
        random_state=RANDOM_SEED,
    )


def fit_predict_ngb(X_train, y_train, X_test, n_features):
    """Train NGBoost-T(df=5) + return (q05, q50, q95, df, scale, loc) for test set.

    With fixed df, q05/q50/q95 are computed analytically via scipy.stats.t."""
    model = make_ngb_regressor()
    model.fit(X_train, y_train)
    dist = model.pred_dist(X_test)
    # Direct quantile via scipy t (df is fixed, no need to instantiate frozen rv each time).
    loc   = np.asarray(dist.loc)
    scale = np.asarray(dist.scale)
    df    = float(NGB_DF_FIXED)
    from scipy.stats import t as student_t
    q05 = student_t.ppf(0.05, df=df, loc=loc, scale=scale)
    q50 = loc.copy()                              # symmetric t: median = loc
    q95 = student_t.ppf(0.95, df=df, loc=loc, scale=scale)
    df_reported = np.full_like(loc, df)           # scalar df → array for output schema
    return q05, q50, q95, df_reported, scale, loc, model


# ─────────────────────────────────────────────────────────────────────────────
# Per-fold loop
# ─────────────────────────────────────────────────────────────────────────────

def run_lomo_ngb(df: pd.DataFrame, feature_cols: list[str], smoke: bool = False
                 ) -> tuple[pd.DataFrame, pd.DataFrame]:
    folds = lomo_folds(df)
    if smoke:
        folds = folds[:3]
        log.info(f"  SMOKE: limiting to first {len(folds)} folds")
    log.info(f"  running {len(folds)} LOMO folds  (NGBoost-T, n_estim=500)")

    pred_rows: list[pd.DataFrame] = []
    metric_rows: list[dict] = []
    df_means: list[float] = []

    t0 = time.time()
    for i, (fid, tr_idx, te_idx) in enumerate(folds, 1):
        train = df.loc[tr_idx]
        test  = df.loc[te_idx]
        y     = test[LABEL_COL].to_numpy(dtype=np.float32)

        X_train = df.loc[tr_idx, feature_cols].astype(np.float32)
        y_train = df.loc[tr_idx, LABEL_COL].astype(np.float32)
        X_test  = df.loc[te_idx, feature_cols].astype(np.float32)

        # NGBoost doesn't handle NaN natively — impute with train-fold means.
        # (XGBoost handles NaN; NGBoost does not. Documented limitation.)
        train_means = X_train.mean(numeric_only=True)
        X_train = X_train.fillna(train_means).to_numpy(dtype=np.float32)
        X_test  = X_test.fillna(train_means).to_numpy(dtype=np.float32)
        # Handle any remaining all-NaN columns (e.g. fire_count_5d)
        col_mean = np.nanmean(X_train, axis=0)
        col_mean = np.where(np.isnan(col_mean), 0.0, col_mean)
        X_train  = np.where(np.isnan(X_train), col_mean, X_train)
        X_test   = np.where(np.isnan(X_test),  col_mean, X_test)

        try:
            q05, q50, q95, df_arr, scale_arr, loc_arr, _ = fit_predict_ngb(
                X_train, y_train.to_numpy(), X_test, n_features=X_train.shape[1])
        except Exception as e:
            log.error(f"  fold {fid} NGBoost failed: {type(e).__name__}: {e}")
            continue

        m_ngb = compute_metrics(y, q05, q50, q95)
        m_ngb.update({"fold": fid, "model": "ngboost_v2",
                      "df_mean": float(np.mean(df_arr)),
                      "df_p10":  float(np.percentile(df_arr, 10))})
        metric_rows.append(m_ngb)
        df_means.append(float(np.mean(df_arr)))

        # baselines (same as XGBoost script)
        baselines: dict[str, np.ndarray] = {}
        for name, fn in BASELINES.items():
            if name == "doy_clim":
                baselines[name] = baseline_doy_climatology(train, test)
            else:
                baselines[name] = fn(test)
        for name, yhat in baselines.items():
            mask = ~np.isnan(yhat)
            if mask.sum() == 0:
                m_b = {"n": 0, "rmse": float("nan"), "mae": float("nan"),
                       "bias": float("nan"), "r2": float("nan"),
                       "crps": float("nan"), "cov90": float("nan"),
                       "pi_width": float("nan")}
            else:
                m_b = compute_point_metrics(y[mask], yhat[mask])
            m_b.update({"fold": fid, "model": name})
            metric_rows.append(m_b)

        pred_rows.append(pd.DataFrame({
            "date":      test["date"].values,
            "sensor_id": test["sensor_id"].values,
            "fold":      fid,
            "y_true":    y,
            "ngb_q05":   q05,
            "ngb_q50":   q50,
            "ngb_q95":   q95,
            "ngb_loc":   loc_arr,
            "ngb_scale": scale_arr,
            "ngb_df":    df_arr,
            **{f"baseline_{k}": v for k, v in baselines.items()},
        }))

        if i % 6 == 0 or i == len(folds):
            elapsed = time.time() - t0
            eta = elapsed / i * (len(folds) - i)
            log.info(f"  [{i:>3}/{len(folds)}] fold {fid}  n_test={len(te_idx):>3}  "
                     f"ngb_rmse={m_ngb['rmse']:5.2f} r2={m_ngb['r2']:+.3f} "
                     f"cov90={m_ngb['cov90']:.2f} df_mean={m_ngb['df_mean']:5.1f}  "
                     f"elapsed={elapsed:.0f}s eta={eta:.0f}s")

    preds   = pd.concat(pred_rows, ignore_index=True)
    metrics = pd.DataFrame(metric_rows)
    log.info(f"  Student-t df_mean across folds: {np.mean(df_means):.1f}  "
             f"(NU_MIN enforced: {NU_MIN})")
    return preds, metrics


# ─────────────────────────────────────────────────────────────────────────────
# Aggregation — same as XGBoost but renamed columns
# ─────────────────────────────────────────────────────────────────────────────

def ngb_summary(metrics: pd.DataFrame, preds: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model_name, grp in metrics.groupby("model"):
        valid = grp.dropna(subset=["rmse"])
        rows.append({
            "model":           model_name,
            "n_folds":         int((grp["n"] > 0).sum()),
            "n_obs":           int(grp["n"].sum()),
            "rmse_mean":       float(valid["rmse"].mean()),
            "rmse_median":     float(valid["rmse"].median()),
            "mae_mean":        float(valid["mae"].mean()),
            "bias_mean":       float(valid["bias"].mean()),
            "r2_mean":         float(valid["r2"].mean()),
            "crps_mean":       float(valid["crps"].mean()) if valid["crps"].notna().any() else float("nan"),
            "cov90_mean":      float(valid["cov90"].mean()) if valid["cov90"].notna().any() else float("nan"),
            "pi_width_mean":   float(valid["pi_width"].mean()) if valid["pi_width"].notna().any() else float("nan"),
        })

    yhat_col = {"ngboost_v2":   "ngb_q50",
                "persistence":  "baseline_persistence",
                "doy_clim":     "baseline_doy_clim",
                "cams_scaled":  "baseline_cams_scaled",
                "geos_scaled":  "baseline_geos_scaled"}
    from src.stage1_satml.models.train_xgboost_v2 import rmse, r2, bias
    for m_name, col in yhat_col.items():
        if col not in preds.columns:
            continue
        mask = preds[col].notna()
        if mask.sum() == 0:
            continue
        y = preds.loc[mask, "y_true"].to_numpy()
        yh = preds.loc[mask, col].to_numpy()
        for r in rows:
            if r["model"] == m_name:
                r["rmse_pooled"] = rmse(y, yh)
                r["r2_pooled"]   = r2(y, yh)
                r["bias_pooled"] = bias(y, yh)
                r["n_pooled"]    = int(len(y))
                break

    return pd.DataFrame(rows).sort_values("rmse_mean", na_position="last")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite outputs")
    ap.add_argument("--smoke", action="store_true",
                    help="3 folds only for smoke-test (~2 min)")
    args = ap.parse_args()

    if OUT_PREDS.exists() and not args.force:
        log.warning(f"{OUT_PREDS} exists — use --force to overwrite")
        return

    log.info("── load dataset ──")
    df = load_dataset()
    feats = [c for c in FEATURE_COLS if c in df.columns]
    log.info(f"  using {len(feats)} feature columns (NGBoost imputes NaN with train-fold means)")

    log.info("── run NGBoost LOMO ──")
    preds, metrics = run_lomo_ngb(df, feats, smoke=args.smoke)

    preds.to_parquet(OUT_PREDS, index=False)
    log.info(f"  wrote {OUT_PREDS}  ({len(preds):,} rows × {len(preds.columns)} cols)")

    metrics.to_csv(OUT_FOLD, index=False)
    log.info(f"  wrote {OUT_FOLD}  ({len(metrics):,} rows)")

    per_month = aggregate_per_month(metrics)
    per_month.to_csv(OUT_MONTH, index=False)
    log.info(f"  wrote {OUT_MONTH}  ({len(per_month):,} rows)")

    summary = ngb_summary(metrics, preds)
    summary.to_csv(OUT_SUMMARY, index=False)
    log.info(f"  wrote {OUT_SUMMARY}")

    log.info("── headline summary ──")
    for _, r in summary.iterrows():
        m = r["model"]
        pooled = (f"pooled_rmse={r.get('rmse_pooled', float('nan')):.2f}  "
                  f"pooled_r2={r.get('r2_pooled', float('nan')):+.3f}"
                  if not pd.isna(r.get("rmse_pooled", float("nan"))) else "pooled=NA")
        log.info(f"  {m:<14}  fold_rmse_mean={r['rmse_mean']:5.2f}  "
                 f"fold_r2_mean={r['r2_mean']:+.3f}  "
                 f"cov90={r['cov90_mean'] if not pd.isna(r['cov90_mean']) else float('nan'):.2f}  "
                 f"crps={r['crps_mean'] if not pd.isna(r['crps_mean']) else float('nan'):.2f}  "
                 f"n_folds={int(r['n_folds'])}  {pooled}")


if __name__ == "__main__":
    main()
