"""
optuna_lomo.py — Optuna hyperparameter tuning with LOMO CV as the objective.

Optimises XGBoost hyperparameters to maximise pooled LOMO R²
(our primary evaluation metric). Each trial runs a full 12-month
leave-one-month-out cross-validation.

Usage:
    python -m kandy_pm25.src.stage1_satml.models.optuna_lomo
    python -m kandy_pm25.src.stage1_satml.models.optuna_lomo --n-trials 100
"""

import argparse
import json
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import r2_score, mean_squared_error

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    MERGED_DIR, TABLES_DIR, MODELS_DIR,
    XGBOOST_DEFAULT_PARAMS, RANDOM_SEED,
    LOG_FORMAT, LOG_DATEFMT,
)

warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("optuna_lomo")

# Import feature definitions from the main training script
from kandy_pm25.src.stage1_satml.models.train_xgboost import (
    ALL_FEATURES, TARGET, load_dataset, select_features,
)


def lomo_cv_score(params: dict, X: pd.DataFrame, y: pd.Series, months: np.ndarray) -> dict:
    """
    Run LOMO CV with the given params. Returns pooled R² and mean RMSE.
    """
    params_cv = {k: v for k, v in params.items() if k != "early_stopping_rounds"}
    all_preds = np.full(len(y), np.nan)

    for month in range(1, 13):
        test_mask = months == month
        if test_mask.sum() == 0:
            continue

        X_tr, X_te = X[~test_mask], X[test_mask]
        y_tr, y_te = y[~test_mask], y[test_mask]

        model = xgb.XGBRegressor(**params_cv)
        model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)
        all_preds[test_mask] = model.predict(X_te)

    valid = ~np.isnan(all_preds)
    pooled_r2 = r2_score(y[valid], all_preds[valid])
    pooled_rmse = mean_squared_error(y[valid], all_preds[valid]) ** 0.5
    return {"r2": pooled_r2, "rmse": pooled_rmse}


def run_optuna(n_trials: int = 80):
    try:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
    except ImportError:
        log.error("optuna not installed. pip install optuna")
        return

    # Load data
    df = load_dataset()
    features, _ = select_features(df)
    labelled = df[df[TARGET].notna()].copy()
    X = labelled[features]
    y = labelled[TARGET]
    months = labelled.index.month.values  # numpy array

    # Baseline
    baseline = lomo_cv_score(XGBOOST_DEFAULT_PARAMS, X, y, months)
    log.info(f"Baseline LOMO: R²={baseline['r2']:.4f}, RMSE={baseline['rmse']:.3f}")

    def objective(trial):
        params = {
            "n_estimators":     trial.suggest_int("n_estimators", 200, 1200),
            "learning_rate":    trial.suggest_float("learning_rate", 0.005, 0.15, log=True),
            "max_depth":        trial.suggest_int("max_depth", 3, 10),
            "subsample":        trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.4, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 15),
            "reg_alpha":        trial.suggest_float("reg_alpha", 1e-4, 10.0, log=True),
            "reg_lambda":       trial.suggest_float("reg_lambda", 1e-4, 10.0, log=True),
            "gamma":            trial.suggest_float("gamma", 0.0, 5.0),
            "objective":        "reg:squarederror",
            "eval_metric":      "rmse",
            "n_jobs":           -1,
            "random_state":     RANDOM_SEED,
        }
        result = lomo_cv_score(params, X, y, months)
        trial.set_user_attr("rmse", result["rmse"])
        return result["r2"]  # maximize

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED),
        study_name="xgboost_lomo_cv",
    )
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    # Results
    best = study.best_trial
    log.info(f"\n{'='*60}")
    log.info(f"Best trial #{best.number}: R²={best.value:.4f}, RMSE={best.user_attrs['rmse']:.3f}")
    log.info(f"Improvement: R² {baseline['r2']:.4f} → {best.value:.4f} "
             f"(+{best.value - baseline['r2']:.4f})")
    log.info(f"Best params: {json.dumps(best.params, indent=2)}")

    # Save best params
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    best_params = best.params.copy()
    best_params.update({
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "n_jobs": -1,
        "random_state": RANDOM_SEED,
        "early_stopping_rounds": 50,
    })

    params_path = TABLES_DIR / "optuna_best_params.json"
    with open(params_path, "w") as f:
        json.dump(best_params, f, indent=2)
    log.info(f"Best params saved → {params_path}")

    # Save study results
    trials_df = study.trials_dataframe()
    trials_df.to_csv(TABLES_DIR / "optuna_trials.csv", index=False)
    log.info(f"All trials saved → {TABLES_DIR / 'optuna_trials.csv'}")

    # Top 5 trials
    log.info("\nTop 5 trials:")
    top5 = trials_df.nlargest(5, "value")
    for _, row in top5.iterrows():
        log.info(f"  Trial {row['number']:.0f}: R²={row['value']:.4f}")

    return best_params


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-trials", type=int, default=80)
    args = parser.parse_args()
    run_optuna(n_trials=args.n_trials)
