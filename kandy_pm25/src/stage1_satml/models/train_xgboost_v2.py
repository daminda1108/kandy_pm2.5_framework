"""
train_xgboost_v2.py — Stage 1 v2 nested LOMO quantile XGBoost + baselines.

OSF pre-registration: docs/osf_prereg_stage1_v2.md §5 (locked 2026-05-17).
Project rules: .claude/rules/stage1-data.md (v2 section).

────────────────────────────────────────────────────────────────────────
Protocol (pre-reg §5.3)
────────────────────────────────────────────────────────────────────────
Outer: Leave-One-Month-Out — 84 folds, one per (year, month) ∈ 2019–2025.
       Each fold's test set is all FECT sensor-days for that specific
       (year, month). Sensor identity is NOT a split dimension.

       NOTE on inner CV: pre-reg §5.3 specifies inner blocked-temporal
       5-fold for hyperparameter search. v2.0 uses fixed hyperparameters
       loaded from results/models/xgboost_best_params.json (v1 optima) as
       the starting point. Bayesian hyperparameter optimisation is a
       v2.1 follow-up (pre-reg §5.2 explicitly allows starting from v1
       optima and reserves the search for a one-time inner-fold pass).

Model:  XGBoost quantile regression with τ ∈ {0.05, 0.50, 0.95}
        (XGBoost 3.x multi-quantile objective="reg:quantileerror").

Baselines (pre-reg §5.4):
  1. persistence   : y_hat(t) = y_obs(t-1)         [via pm25_lag_1d]
  2. doy_clim      : DOY mean computed on train, applied to test
  3. cams_scaled   : cams_pm25_raw × CAMS_BIAS_FACTOR_FLAT (= v1's pm25_observed)
  4. geos_scaled   : geos_cf_pm25_raw × KANDY_GEOS_CF_RATIO (NaN until GEOS-CF lands)

Metrics (pre-reg §5.5):
  Primary:   RMSE, MAE, bias, R², CRPS (pinball-loss-based 3-quantile),
             90% PI coverage, 90% PI width
  Secondary: per-fold, per-month, per-baseline tables

────────────────────────────────────────────────────────────────────────
Outputs (under data/processed/stage1_v2/training/)
────────────────────────────────────────────────────────────────────────
  predictions_lomo_v2.parquet         — per-row: date, sensor_id, y_true,
                                         q05/q50/q95, baselines, fold_id
  metrics_per_fold_v2.csv             — per fold per model: RMSE/R²/CRPS/cov90/...
  metrics_per_month_v2.csv            — per calendar month aggregate
  summary_v2.csv                      — aggregate across all folds per model

Usage:
  python -m src.stage1_satml.models.train_xgboost_v2
  python src/stage1_satml/models/train_xgboost_v2.py
  python src/stage1_satml/models/train_xgboost_v2.py --force
  python src/stage1_satml/models/train_xgboost_v2.py --smoke    # 3 folds only

Reference: pre-reg §5; build_dataset_v2.py; calibrate_fect.py.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    PROC_DIR, MODELS_DIR,
    CAMS_BIAS_FACTOR_FLAT, KANDY_GEOS_CF_RATIO,
    LOG_FORMAT, LOG_DATEFMT,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("train_xgboost_v2")

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

V2_DATASET     = PROC_DIR / "stage1_v2" / "dataset_v2_multistation_daily.parquet"
V1_BEST_PARAMS = MODELS_DIR / "xgboost_best_params.json"

OUT_DIR = PROC_DIR / "stage1_v2" / "training"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _suffixed(base: Path, suffix: str = "") -> Path:
    """Insert a suffix before the extension: foo.csv + _abl_drop_E → foo_abl_drop_E.csv"""
    if not suffix:
        return base
    return base.with_name(base.stem + suffix + base.suffix)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

TRAIN_YEARS = list(range(2019, 2026))     # pre-reg §3.4
QUANTILES   = (0.05, 0.50, 0.95)
RANDOM_SEED = 42

# Features = 28 mechanistic features (pre-reg §4) + per-station physics features.
# Per-station (lat, lon, elevation_m): allowed because LOMO does not split on
# sensor (pre-reg §5.3 amendment 2026-05-17); model needs them to discriminate
# Akurana (1538 m) from Hantana TR4 (1698 m).
META_COLS  = ["date", "sensor_id", "sensor_name", "region"]
LABEL_COL  = "pm25_observed"
PERSIST_COL = "pm25_lag_1d"    # used both as a feature AND for the persistence baseline

STATION_COLS = ["lat", "lon", "elevation_m"]

FEATURE_GROUPS: dict[str, list[str]] = {
    "A": ["wind_speed_10m", "blh_era5", "ventilation_coefficient",
          "lapse_rate_t925_t2m", "nocturnal_blh_ratio"],
    "B": ["wind_along_corridor", "wind_cross_corridor",
          "wind_into_blocked_sector", "valley_drainage_index"],
    "C": ["precip_24h", "precip_7d", "dry_spell_days"],
    "D": ["aod_maiac", "aod_blh_ratio", "no2_column", "fire_count_5d"],
    "E": ["cams_pm25_raw", "geos_cf_pm25_raw", "prior_disagreement"],
    "F": ["mei_sin", "mei_cos", "iod_dmi", "mjo_amplitude"],
    "G": ["pm25_lag_1d", "pm25_lag_7d_mean", "pm25_lag_30d_mean",
          "doy_sin", "doy_cos"],
    "STATION": STATION_COLS,
}

FEATURE_COLS = [c for g in FEATURE_GROUPS.values() for c in g]


def select_features(drop_groups: list[str] | None = None,
                    drop_features: list[str] | None = None,
                    keep_only: list[str] | None = None) -> list[str]:
    """Return the feature column list with the requested ablations applied.

    drop_groups:  group letters from FEATURE_GROUPS to drop entirely
    drop_features: individual column names to drop
    keep_only:    if set, restrict to ONLY these feature columns (overrides drops)
    """
    if keep_only is not None:
        return list(keep_only)
    drop_groups = drop_groups or []
    drop_features = set(drop_features or [])
    out = []
    for g, cols in FEATURE_GROUPS.items():
        if g in drop_groups:
            continue
        for c in cols:
            if c in drop_features:
                continue
            out.append(c)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Data load
# ─────────────────────────────────────────────────────────────────────────────

def load_dataset(label_scale: float = 1.0) -> pd.DataFrame:
    """Load v2 dataset. If label_scale != 1.0, multiply pm25_observed AND the
    lag features pm25_lag_{1d,7d_mean,30d_mean} by that factor (pre-reg §6.1
    anchor sweep). All other features unchanged."""
    if not V2_DATASET.exists():
        raise FileNotFoundError(f"v2 dataset missing — run build_dataset_v2.py first: {V2_DATASET}")
    df = pd.read_parquet(V2_DATASET)
    df["date"] = pd.to_datetime(df["date"])
    df["year"]  = df["date"].dt.year
    df["month"] = df["date"].dt.month
    n0 = len(df)
    df = df[df["year"].isin(TRAIN_YEARS)].reset_index(drop=True)
    log.info(f"  loaded {n0:,} rows; kept {len(df):,} in training window {TRAIN_YEARS[0]}–{TRAIN_YEARS[-1]}")

    # Drop rows where label is missing (shouldn't happen for FECT calibrated but guard)
    n_pre = len(df)
    df = df.dropna(subset=[LABEL_COL]).reset_index(drop=True)
    if len(df) < n_pre:
        log.warning(f"  dropped {n_pre - len(df)} rows with missing label")

    # Pre-reg §6.1 anchor sensitivity: rescale label + lag features by a
    # constant. Linear transform; preserves R², scales RMSE/bias proportionally.
    if abs(label_scale - 1.0) > 1e-9:
        label_like = [LABEL_COL, "pm25_lag_1d", "pm25_lag_7d_mean", "pm25_lag_30d_mean"]
        label_like = [c for c in label_like if c in df.columns]
        for c in label_like:
            df[c] = df[c] * label_scale
        log.info(f"  §6.1 anchor sweep: label_scale={label_scale:.4f}  "
                 f"new pm25_observed mean={df[LABEL_COL].mean():.3f} µg/m³")

    # Feature column coverage
    present_feats = [c for c in FEATURE_COLS if c in df.columns]
    missing_feats = [c for c in FEATURE_COLS if c not in df.columns]
    if missing_feats:
        log.warning(f"  feature columns absent from dataset: {missing_feats}")
    log.info(f"  using {len(present_feats)}/{len(FEATURE_COLS)} feature columns")

    # NaN report per feature
    nan_pct = df[present_feats].isna().mean().sort_values(ascending=False)
    high_nan = nan_pct[nan_pct > 0.5]
    if len(high_nan):
        log.info("  features with >50% NaN (XGBoost handles, but flagged):")
        for c, p in high_nan.items():
            log.info(f"    {c:<28}  {100*p:5.1f}%")

    return df


# ─────────────────────────────────────────────────────────────────────────────
# Hyperparameters
# ─────────────────────────────────────────────────────────────────────────────

def load_hyperparameters() -> dict:
    """v1 Optuna optima as starting point (pre-reg §5.2)."""
    if not V1_BEST_PARAMS.exists():
        log.warning(f"v1 best params not found at {V1_BEST_PARAMS}; using defaults")
        base = {}
    else:
        with open(V1_BEST_PARAMS) as f:
            base = json.load(f)

    # Adapt for quantile objective: drop incompatible keys, override objective.
    drop_keys = {"objective", "eval_metric", "early_stopping_rounds"}
    params = {k: v for k, v in base.items() if k not in drop_keys}

    params.update({
        "objective": "reg:quantileerror",
        "quantile_alpha": list(QUANTILES),
        "tree_method": "hist",
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
    })
    log.info(f"  hyperparameters: n_estimators={params.get('n_estimators')}  "
             f"lr={params.get('learning_rate'):.4f}  max_depth={params.get('max_depth')}  "
             f"objective=reg:quantileerror α={list(QUANTILES)}")
    return params


# ─────────────────────────────────────────────────────────────────────────────
# Metrics
# ─────────────────────────────────────────────────────────────────────────────

def rmse(y, yhat) -> float:
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def mae(y, yhat) -> float:
    return float(np.mean(np.abs(y - yhat)))


def bias(y, yhat) -> float:
    return float(np.mean(yhat - y))


def r2(y, yhat) -> float:
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")


def crps_quantile(y: np.ndarray, q_preds: np.ndarray, taus=QUANTILES) -> float:
    """Pinball-loss-based CRPS estimator with discrete quantile predictions.

    For each (y, q_τ): pinball_τ = (y - q_τ) · (τ - 𝟙(q_τ > y)).
    CRPS_approx = 2 · mean(pinball) — Laio & Tamea 2007 estimator.
    With 3 quantiles, biased but interpretable. Lower is better."""
    y = np.asarray(y).reshape(-1, 1)
    q = np.asarray(q_preds)
    taus_arr = np.array(taus).reshape(1, -1)
    indicator = (q > y).astype(float)
    pinball = (y - q) * (taus_arr - indicator)
    return float(2.0 * pinball.mean())


def cov90(y: np.ndarray, q05: np.ndarray, q95: np.ndarray) -> float:
    return float(np.mean((y >= q05) & (y <= q95)))


def pi_width(q05: np.ndarray, q95: np.ndarray) -> float:
    return float(np.mean(q95 - q05))


def compute_metrics(y: np.ndarray, q05: np.ndarray, q50: np.ndarray,
                    q95: np.ndarray) -> dict:
    return {
        "n":         int(len(y)),
        "rmse":      rmse(y, q50),
        "mae":       mae(y, q50),
        "bias":      bias(y, q50),
        "r2":        r2(y, q50),
        "crps":      crps_quantile(y, np.column_stack([q05, q50, q95])),
        "cov90":     cov90(y, q05, q95),
        "pi_width":  pi_width(q05, q95),
    }


def compute_point_metrics(y: np.ndarray, yhat: np.ndarray) -> dict:
    """For baselines that produce only a point estimate (no quantiles)."""
    return {
        "n":         int(len(y)),
        "rmse":      rmse(y, yhat),
        "mae":       mae(y, yhat),
        "bias":      bias(y, yhat),
        "r2":        r2(y, yhat),
        "crps":      float("nan"),
        "cov90":     float("nan"),
        "pi_width":  float("nan"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Baselines
# ─────────────────────────────────────────────────────────────────────────────

def baseline_persistence(df_test: pd.DataFrame) -> np.ndarray:
    return df_test[PERSIST_COL].to_numpy()


def baseline_doy_climatology(df_train: pd.DataFrame, df_test: pd.DataFrame) -> np.ndarray:
    """DOY mean computed on train, applied by day-of-year to test."""
    doy_mean = (df_train.assign(doy=df_train["date"].dt.dayofyear)
                        .groupby("doy")[LABEL_COL].mean())
    test_doy = df_test["date"].dt.dayofyear
    out = test_doy.map(doy_mean).to_numpy()
    # Fallback to global train mean for any DOY missing in train
    fallback = float(df_train[LABEL_COL].mean())
    return np.where(np.isnan(out), fallback, out)


def baseline_cams_scaled(df_test: pd.DataFrame) -> np.ndarray:
    """v1's KOALA-corrected CAMS: cams_pm25_raw × CAMS_BIAS_FACTOR_FLAT."""
    return (df_test["cams_pm25_raw"] * CAMS_BIAS_FACTOR_FLAT).to_numpy()


def baseline_geos_scaled(df_test: pd.DataFrame) -> np.ndarray:
    """GEOS-CF scaled — NaN until GEOS-CF column lands."""
    if "geos_cf_pm25_raw" not in df_test.columns or df_test["geos_cf_pm25_raw"].isna().all():
        return np.full(len(df_test), np.nan)
    return (df_test["geos_cf_pm25_raw"] * KANDY_GEOS_CF_RATIO).to_numpy()


BASELINES = {
    "persistence":  baseline_persistence,
    "doy_clim":     None,                      # special — needs train and test
    "cams_scaled":  baseline_cams_scaled,
    "geos_scaled":  baseline_geos_scaled,
}


# ─────────────────────────────────────────────────────────────────────────────
# Folds
# ─────────────────────────────────────────────────────────────────────────────

def lomo_folds(df: pd.DataFrame) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Return list of (fold_id, train_idx, test_idx). One fold per (year, month).
    Train = all rows NOT in that month. Test = rows in that month."""
    folds = []
    for (y, m), grp in df.groupby(["year", "month"], sort=True):
        fold_id = f"{y}-{m:02d}"
        test_idx = grp.index.to_numpy()
        train_idx = df.index.difference(grp.index).to_numpy()
        if len(test_idx) == 0 or len(train_idx) == 0:
            continue
        folds.append((fold_id, train_idx, test_idx))
    return folds


# ─────────────────────────────────────────────────────────────────────────────
# Train + predict one fold
# ─────────────────────────────────────────────────────────────────────────────

def train_one_fold(df: pd.DataFrame, train_idx: np.ndarray, test_idx: np.ndarray,
                   feature_cols: list[str], params: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Train q05/q50/q95 multi-quantile XGBoost; return (q05, q50, q95) for test rows."""
    X_train = df.loc[train_idx, feature_cols].to_numpy(dtype=np.float32)
    y_train = df.loc[train_idx, LABEL_COL].to_numpy(dtype=np.float32)
    X_test  = df.loc[test_idx,  feature_cols].to_numpy(dtype=np.float32)

    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train, verbose=False)
    pred = model.predict(X_test)
    # multi-quantile output shape: (n_test, len(QUANTILES))
    if pred.ndim == 1:
        # Single quantile fallback (shouldn't happen with multi-α list, but safe)
        return pred, pred, pred
    return pred[:, 0], pred[:, 1], pred[:, 2]


# ─────────────────────────────────────────────────────────────────────────────
# Per-fold collection
# ─────────────────────────────────────────────────────────────────────────────

def run_lomo(df: pd.DataFrame, feature_cols: list[str], params: dict,
             smoke: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Iterate LOMO folds, train+predict, collect per-row predictions and per-fold metrics."""
    folds = lomo_folds(df)
    if smoke:
        folds = folds[:3]
        log.info(f"  SMOKE: limiting to first {len(folds)} folds")
    log.info(f"  running {len(folds)} LOMO folds")

    pred_rows: list[pd.DataFrame] = []
    metric_rows: list[dict] = []

    t0 = time.time()
    for i, (fid, tr_idx, te_idx) in enumerate(folds, 1):
        train = df.loc[tr_idx]
        test  = df.loc[te_idx]
        y     = test[LABEL_COL].to_numpy(dtype=np.float32)

        # ── XGBoost quantile ──
        q05, q50, q95 = train_one_fold(df, tr_idx, te_idx, feature_cols, params)
        m_xgb = compute_metrics(y, q05, q50, q95)
        m_xgb.update({"fold": fid, "model": "xgboost_v2"})
        metric_rows.append(m_xgb)

        # ── baselines ──
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
                       "crps": float("nan"), "cov90": float("nan"), "pi_width": float("nan")}
            else:
                m_b = compute_point_metrics(y[mask], yhat[mask])
            m_b.update({"fold": fid, "model": name})
            metric_rows.append(m_b)

        # ── per-row preds ──
        pred_rows.append(pd.DataFrame({
            "date":         test["date"].values,
            "sensor_id":    test["sensor_id"].values,
            "fold":         fid,
            "y_true":       y,
            "xgb_q05":      q05,
            "xgb_q50":      q50,
            "xgb_q95":      q95,
            **{f"baseline_{k}": v for k, v in baselines.items()},
        }))

        if i % 12 == 0 or i == len(folds):
            elapsed = time.time() - t0
            eta = elapsed / i * (len(folds) - i)
            log.info(f"  [{i:>3}/{len(folds)}] fold {fid}  n_test={len(te_idx):>3}  "
                     f"xgb_rmse={m_xgb['rmse']:5.2f} r2={m_xgb['r2']:+.3f} cov90={m_xgb['cov90']:.2f}  "
                     f"elapsed={elapsed:.0f}s eta={eta:.0f}s")

    preds = pd.concat(pred_rows, ignore_index=True)
    metrics = pd.DataFrame(metric_rows)
    return preds, metrics


# ─────────────────────────────────────────────────────────────────────────────
# Aggregation
# ─────────────────────────────────────────────────────────────────────────────

def aggregate_per_month(metrics: pd.DataFrame) -> pd.DataFrame:
    """Group folds by calendar month (Jan..Dec across years). Useful for the
    per-month LOMO table (Figure 4 of pre-reg §9)."""
    m = metrics.copy()
    m["calendar_month"] = m["fold"].str.split("-").str[1].astype(int)
    grouped = (m.groupby(["calendar_month", "model"])
                .agg(n_folds=("n", "count"), n_obs=("n", "sum"),
                     rmse=("rmse", "mean"), mae=("mae", "mean"),
                     bias=("bias", "mean"), r2=("r2", "mean"),
                     crps=("crps", "mean"), cov90=("cov90", "mean"),
                     pi_width=("pi_width", "mean"))
                .reset_index()
                .sort_values(["model", "calendar_month"]))
    return grouped


def aggregate_summary(metrics: pd.DataFrame, preds: pd.DataFrame) -> pd.DataFrame:
    """Overall LOMO performance per model — both fold-averaged and pooled."""
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

    # Pooled (across all test rows) — what the paper reports as headline.
    yhat_col = {"xgboost_v2": "xgb_q50",
                "persistence": "baseline_persistence",
                "doy_clim": "baseline_doy_clim",
                "cams_scaled": "baseline_cams_scaled",
                "geos_scaled": "baseline_geos_scaled"}
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

def run_pipeline(feature_cols: list[str] | None = None,
                 suffix: str = "",
                 smoke: bool = False,
                 force: bool = True,
                 quiet: bool = False,
                 label_scale: float = 1.0) -> pd.DataFrame:
    """Programmatic entry point for ablation drivers.

    Parameters:
      feature_cols: feature list to use (default: all FEATURE_COLS present in df)
      suffix:       added before extension in all output files (e.g. '_abl_drop_E')
      smoke:        run only first 3 folds
      force:        overwrite existing outputs
      quiet:        suppress per-fold logs
      label_scale:  multiplier applied to pm25_observed + pm25_lag_* (pre-reg §6.1)

    Returns the summary DataFrame (one row per model).
    """
    out_preds   = _suffixed(OUT_DIR / "predictions_lomo_v2.parquet", suffix)
    out_fold    = _suffixed(OUT_DIR / "metrics_per_fold_v2.csv",     suffix)
    out_month   = _suffixed(OUT_DIR / "metrics_per_month_v2.csv",    suffix)
    out_summary = _suffixed(OUT_DIR / "summary_v2.csv",              suffix)

    if out_preds.exists() and not force:
        log.warning(f"{out_preds} exists — pass force=True to overwrite")
        return pd.read_csv(out_summary) if out_summary.exists() else pd.DataFrame()

    log_level_save = logging.getLogger("train_xgboost_v2").level
    if quiet:
        logging.getLogger("train_xgboost_v2").setLevel(logging.WARNING)

    log.info(f"── pipeline run  suffix='{suffix}'  label_scale={label_scale} ──")
    df = load_dataset(label_scale=label_scale)
    params = load_hyperparameters()
    if feature_cols is None:
        feats = [c for c in FEATURE_COLS if c in df.columns]
    else:
        feats = [c for c in feature_cols if c in df.columns]
    log.info(f"  using {len(feats)} feature columns")

    preds, metrics = run_lomo(df, feats, params, smoke=smoke)

    preds.to_parquet(out_preds, index=False)
    metrics.to_csv(out_fold, index=False)
    per_month = aggregate_per_month(metrics)
    per_month.to_csv(out_month, index=False)
    summary = aggregate_summary(metrics, preds)
    summary["suffix"] = suffix or "_full"
    summary["n_features"] = len(feats)
    summary.to_csv(out_summary, index=False)

    log.info(f"  wrote {out_preds.name}, {out_summary.name}")
    if quiet:
        logging.getLogger("train_xgboost_v2").setLevel(log_level_save)

    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite outputs")
    ap.add_argument("--smoke", action="store_true",
                    help="run only first 3 folds for smoke-test (~30s)")
    ap.add_argument("--drop-group", default=None,
                    help="comma-separated group letters to drop (e.g. 'E' or 'D,E')")
    ap.add_argument("--drop-features", default=None,
                    help="comma-separated feature names to drop")
    ap.add_argument("--suffix", default="",
                    help="suffix appended to output filenames (default '')")
    args = ap.parse_args()

    drop_groups = args.drop_group.split(",") if args.drop_group else None
    drop_features = args.drop_features.split(",") if args.drop_features else None
    feats = select_features(drop_groups=drop_groups, drop_features=drop_features)

    summary = run_pipeline(feature_cols=feats, suffix=args.suffix,
                           smoke=args.smoke, force=args.force)

    # ── print summary ──
    log.info("── headline summary ──")
    for _, r in summary.iterrows():
        m = r["model"]
        pooled = (f"pooled_rmse={r.get('rmse_pooled', float('nan')):.2f}  "
                  f"pooled_r2={r.get('r2_pooled', float('nan')):+.3f}"
                  if not pd.isna(r.get("rmse_pooled", float("nan"))) else "pooled=NA")
        log.info(f"  {m:<14}  fold_rmse_mean={r['rmse_mean']:5.2f}  "
                 f"fold_r2_mean={r['r2_mean']:+.3f}  "
                 f"cov90={r['cov90_mean'] if not pd.isna(r['cov90_mean']) else float('nan'):.2f}  "
                 f"n_folds={int(r['n_folds'])}  {pooled}")


if __name__ == "__main__":
    main()
