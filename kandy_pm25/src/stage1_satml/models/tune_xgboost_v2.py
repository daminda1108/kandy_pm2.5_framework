"""
tune_xgboost_v2.py — Pre-reg §5.2 inner-fold Bayesian hyperparameter search.

OSF pre-registration §5.2 (verbatim):
  "Fixed at v1 Optuna optima as starting point (loaded from
   results/models/xgboost_best_params.json). One round of nested Bayesian
   optimization (50 trials) allowed within the inner CV fold only — never
   on test fold metrics."

Protocol:
  1. Load Kandy v2 dataset (1,526 sensor-day rows 2019-2025).
  2. Optuna study with 50 trials over the hyperparameter bounds locked
     in pre-reg §5.2:
        n_estimators       [200, 2000]
        max_depth          [3, 10]
        learning_rate      log-uniform [0.005, 0.3]
        subsample          [0.5, 1.0]
        colsample_bytree   [0.5, 1.0]
        reg_alpha          log-uniform [1e-3, 10]
        reg_lambda         log-uniform [1e-3, 10]
  3. Each trial evaluated via inner 5-fold blocked TEMPORAL CV (no random
     shuffle; consecutive month-blocks). Objective = mean CRPS across folds
     (pre-reg §5.5 selection criterion — lower better).
  4. Best params saved + a final LOMO run with the tuned params writes a
     side-by-side comparison vs the v1-best_params headline.

Outputs:
  results/models/xgboost_v2_best_params.json           — tuned hyperparameters
  data/processed/stage1_v2/training/optuna_trials_v2.csv
  data/processed/stage1_v2/training/predictions_lomo_v2_tuned.parquet
  data/processed/stage1_v2/training/summary_v2_tuned.csv
  data/processed/stage1_v2/training/hpo_comparison_v2.csv

Usage:
  python -m src.stage1_satml.models.tune_xgboost_v2
  python src/stage1_satml/models/tune_xgboost_v2.py --trials 50
  python src/stage1_satml/models/tune_xgboost_v2.py --skip-lomo   # tuning only
  python src/stage1_satml/models/tune_xgboost_v2.py --smoke       # 5 trials

Reference: pre-reg §5.2, §5.3, §5.5.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
import xgboost as xgb

# Quiet down Optuna's per-trial info logging (we summarise at the end).
optuna.logging.set_verbosity(optuna.logging.WARNING)

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import PROC_DIR, MODELS_DIR, LOG_FORMAT, LOG_DATEFMT

from src.stage1_satml.models.train_xgboost_v2 import (
    LABEL_COL, FEATURE_COLS, TRAIN_YEARS, RANDOM_SEED, QUANTILES,
    load_dataset, crps_quantile, run_pipeline,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("tune_xgboost_v2")

# ─────────────────────────────────────────────────────────────────────────────
# Paths + constants
# ─────────────────────────────────────────────────────────────────────────────

OUT_DIR = PROC_DIR / "stage1_v2" / "training"
OUT_TRIALS  = OUT_DIR / "optuna_trials_v2.csv"
OUT_COMPARE = OUT_DIR / "hpo_comparison_v2.csv"
OUT_PARAMS  = MODELS_DIR / "xgboost_v2_best_params.json"
V1_PARAMS   = MODELS_DIR / "xgboost_best_params.json"

OUT_DIR.mkdir(parents=True, exist_ok=True)

INNER_N_FOLDS = 5
DEFAULT_TRIALS = 50

PARAM_BOUNDS = {
    "n_estimators":     (200, 2000),
    "max_depth":        (3, 10),
    "learning_rate":    (0.005, 0.3),     # log-uniform
    "subsample":        (0.5, 1.0),
    "colsample_bytree": (0.5, 1.0),
    "reg_alpha":        (1e-3, 10),        # log-uniform
    "reg_lambda":       (1e-3, 10),        # log-uniform
}


def suggest_params(trial: optuna.Trial) -> dict:
    """Sample one set of hyperparameters from the locked bounds."""
    return {
        "n_estimators":     trial.suggest_int("n_estimators",
                                              *PARAM_BOUNDS["n_estimators"]),
        "max_depth":        trial.suggest_int("max_depth",
                                              *PARAM_BOUNDS["max_depth"]),
        "learning_rate":    trial.suggest_float("learning_rate",
                                                *PARAM_BOUNDS["learning_rate"],
                                                log=True),
        "subsample":        trial.suggest_float("subsample",
                                                *PARAM_BOUNDS["subsample"]),
        "colsample_bytree": trial.suggest_float("colsample_bytree",
                                                *PARAM_BOUNDS["colsample_bytree"]),
        "reg_alpha":        trial.suggest_float("reg_alpha",
                                                *PARAM_BOUNDS["reg_alpha"], log=True),
        "reg_lambda":       trial.suggest_float("reg_lambda",
                                                *PARAM_BOUNDS["reg_lambda"], log=True),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Inner blocked-temporal CV
# ─────────────────────────────────────────────────────────────────────────────

def blocked_temporal_folds(df: pd.DataFrame, n_folds: int = INNER_N_FOLDS
                           ) -> list[tuple[np.ndarray, np.ndarray]]:
    """Consecutive (year, month) blocks. Sort by date, split blocks into k
    contiguous chunks, each chunk is one fold's validation set.

    Per pre-reg §5.3 'Blocked temporal 5-fold over remaining months for
    hyperparameter search. No random shuffle. Block size = 1 month minimum.'
    """
    df = df.sort_values("date").reset_index(drop=True)
    df["year_month"] = df["date"].dt.to_period("M")
    months = sorted(df["year_month"].unique())
    n_per = max(1, len(months) // n_folds)

    folds = []
    for i in range(n_folds):
        start = i * n_per
        end = (i + 1) * n_per if i < n_folds - 1 else len(months)
        val_months = set(months[start:end])
        val_mask = df["year_month"].isin(val_months).values
        train_idx = np.where(~val_mask)[0]
        val_idx   = np.where(val_mask)[0]
        folds.append((train_idx, val_idx))
    return folds


def build_xgb(params: dict) -> xgb.XGBRegressor:
    """Wrap suggested params with the locked quantile objective + seed."""
    return xgb.XGBRegressor(
        objective="reg:quantileerror",
        quantile_alpha=list(QUANTILES),
        tree_method="hist",
        random_state=RANDOM_SEED,
        n_jobs=-1,
        verbosity=0,
        **params,
    )


def objective_factory(df: pd.DataFrame, feats: list[str]) -> "callable":
    folds = blocked_temporal_folds(df)

    def objective(trial: optuna.Trial) -> float:
        params = suggest_params(trial)
        crps_per_fold = []
        for train_idx, val_idx in folds:
            X_train = df.loc[train_idx, feats].astype(np.float32)
            y_train = df.loc[train_idx, LABEL_COL].astype(np.float32)
            X_val   = df.loc[val_idx, feats].astype(np.float32)
            y_val   = df.loc[val_idx, LABEL_COL].astype(np.float32).to_numpy()

            model = build_xgb(params)
            model.fit(X_train, y_train)
            q = model.predict(X_val)
            crps_per_fold.append(crps_quantile(y_val, q))
        return float(np.mean(crps_per_fold))

    return objective


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=DEFAULT_TRIALS,
                    help=f"Optuna trials (default {DEFAULT_TRIALS} per pre-reg §5.2)")
    ap.add_argument("--smoke", action="store_true", help="5 trials for smoke")
    ap.add_argument("--skip-lomo", action="store_true",
                    help="run only the Optuna tuning, skip the final LOMO comparison")
    ap.add_argument("--force", action="store_true",
                    help="overwrite outputs")
    args = ap.parse_args()
    n_trials = 5 if args.smoke else args.trials

    log.info("── load v2 dataset ──")
    df = load_dataset()
    feats = [c for c in FEATURE_COLS if c in df.columns]
    log.info(f"  {len(df):,} rows × {len(feats)} feats; objective=CRPS (lower=better); "
             f"inner 5-fold blocked temporal CV per fold")

    # v1 seed
    if not V1_PARAMS.exists():
        log.warning(f"v1 best_params missing — running from default")
        seed_params = None
    else:
        with open(V1_PARAMS) as f:
            v1 = json.load(f)
        seed_params = {k: v for k, v in v1.items() if k in PARAM_BOUNDS}
        log.info(f"  seeding Optuna with v1 best_params: {seed_params}")

    sampler = optuna.samplers.TPESampler(seed=RANDOM_SEED, n_startup_trials=10)
    study = optuna.create_study(direction="minimize", sampler=sampler,
                                study_name="stage1_v2_xgboost_crps")
    if seed_params:
        study.enqueue_trial(seed_params)

    objective = objective_factory(df, feats)

    log.info(f"── Optuna: {n_trials} trials ──")
    t0 = time.time()
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    elapsed = time.time() - t0
    log.info(f"  done in {elapsed:.0f}s  best CRPS={study.best_value:.4f}")

    # Save best params
    best = study.best_params
    best.update({
        "objective":      "reg:quantileerror",
        "quantile_alpha": list(QUANTILES),
        "tree_method":    "hist",
        "random_state":   RANDOM_SEED,
        "n_jobs":         -1,
    })
    OUT_PARAMS.write_text(json.dumps(best, indent=2))
    log.info(f"  wrote {OUT_PARAMS}")

    # Save trial log
    trial_rows = []
    for t in study.trials:
        row = {"trial": t.number, "value_crps": t.value, "state": str(t.state)}
        row.update({f"p_{k}": v for k, v in t.params.items()})
        trial_rows.append(row)
    pd.DataFrame(trial_rows).to_csv(OUT_TRIALS, index=False)
    log.info(f"  wrote {OUT_TRIALS}")

    log.info("── top 5 trials ──")
    for t in sorted(study.trials, key=lambda x: x.value)[:5]:
        log.info(f"  trial {t.number:3d}  crps={t.value:.4f}  "
                 f"depth={t.params.get('max_depth')}  "
                 f"lr={t.params.get('learning_rate'):.4f}  "
                 f"n_est={t.params.get('n_estimators')}  "
                 f"sub={t.params.get('subsample'):.2f}  "
                 f"col={t.params.get('colsample_bytree'):.2f}")

    if args.skip_lomo:
        log.info("skipping final LOMO comparison (--skip-lomo)")
        return

    # ── final LOMO with tuned params (re-uses run_pipeline + override params) ──
    log.info("── final LOMO with tuned params ──")
    # Monkey-patch the cached hyperparameters via a small in-memory override.
    # train_xgboost_v2.load_hyperparameters reads a file; we want it to use ours.
    # Cleanest path: write tuned params back to a temporary file that
    # load_hyperparameters can read on the next call.
    from src.stage1_satml.models import train_xgboost_v2 as tx2
    orig_loader = tx2.load_hyperparameters
    tx2.load_hyperparameters = lambda: {**best}

    try:
        summary_tuned = run_pipeline(feature_cols=feats, suffix="_tuned",
                                     smoke=False, force=True, quiet=True)
    finally:
        tx2.load_hyperparameters = orig_loader

    # ── side-by-side comparison ──
    untuned_summary_path = OUT_DIR / "summary_v2.csv"
    if untuned_summary_path.exists():
        untuned = pd.read_csv(untuned_summary_path)
        untuned_xgb = untuned[untuned["model"] == "xgboost_v2"].iloc[0].to_dict()
        tuned_xgb   = summary_tuned[summary_tuned["model"] == "xgboost_v2"].iloc[0].to_dict()
        rows = []
        for tag, r in [("v1_best_params (headline)", untuned_xgb),
                       ("v2_optuna_50_trials",        tuned_xgb)]:
            rows.append({
                "config":       tag,
                "rmse_pooled":  r.get("rmse_pooled"),
                "r2_pooled":    r.get("r2_pooled"),
                "bias_pooled":  r.get("bias_pooled"),
                "rmse_mean":    r.get("rmse_mean"),
                "cov90_mean":   r.get("cov90_mean"),
                "crps_mean":    r.get("crps_mean"),
                "n_folds":      r.get("n_folds"),
            })
        cmp = pd.DataFrame(rows)
        cmp.to_csv(OUT_COMPARE, index=False)
        log.info(f"  wrote {OUT_COMPARE}")
        log.info("\n── HPO comparison ──")
        for _, r in cmp.iterrows():
            log.info(f"  {r['config']:<28}  rmse_pooled={r['rmse_pooled']:5.3f}  "
                     f"r2_pooled={r['r2_pooled']:+.3f}  cov90={r['cov90_mean']:.3f}  "
                     f"crps={r['crps_mean']:.3f}")
        d_rmse = float(tuned_xgb.get("rmse_pooled")) - float(untuned_xgb.get("rmse_pooled"))
        d_pct  = 100 * d_rmse / float(untuned_xgb.get("rmse_pooled"))
        log.info(f"\n  Δ pooled RMSE (tuned − v1): {d_rmse:+.3f}  ({d_pct:+.1f}%)")


if __name__ == "__main__":
    main()
