"""
multicollinearity_v2.py — VIF + per-group dependence audit (2026-05-18).

Pre-reg locks 28 features by mechanism, but the audit identified
suspected multicollinearity:
  - Group E: cams_pm25_raw + geos_cf_pm25_raw + |cams-geos| (by construction)
  - Group G: pm25_lag_1d, _7d_mean, _30d_mean (autocorrelated obs)
  - Group A: wind_speed_10m * blh_era5 = ventilation_coefficient (exact identity)
  - Group F: mei_sin and mei_cos modulated by same MEI value

Variance Inflation Factor (VIF) flags features whose variation is well
explained by linear combinations of others. VIF > 5 = concerning, > 10 = severe.
This is descriptive (not a reason to drop — pre-reg locks the feature set),
but it's a reviewer concern to surface in the paper.

Outputs:
  data/processed/stage1_v2/eda/vif_v2.csv
  data/processed/stage1_v2/eda/per_group_correlation_v2.csv
  results/figures/stage1_v2/eda/F_vif_bar.png

Usage:
  python -m src.stage1_satml.evaluation.multicollinearity_v2
  python src/stage1_satml/evaluation/multicollinearity_v2.py
"""

import logging
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

warnings.filterwarnings("ignore", category=RuntimeWarning)

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import PROC_DIR, FIGURES_DIR, LOG_FORMAT, LOG_DATEFMT
from src.stage1_satml.models.train_xgboost_v2 import (
    LABEL_COL, FEATURE_GROUPS, FEATURE_COLS, TRAIN_YEARS,
)
from src.stage1_satml.visualization.eda_v2 import (
    feature_group, GROUP_COLOR, GROUP_LABEL,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("multicollinearity_v2")

V2_DATASET = PROC_DIR / "stage1_v2" / "dataset_v2_multistation_daily.parquet"
OUT_TABLES = PROC_DIR / "stage1_v2" / "eda"
OUT_FIGS   = FIGURES_DIR / "stage1_v2" / "eda"
OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_FIGS.mkdir(parents=True, exist_ok=True)


def vif_one(X: pd.DataFrame, col: str) -> float:
    """VIF for one feature: 1 / (1 - R²) of regressing col on all others."""
    other = X.drop(columns=[col]).dropna()
    if len(other) < 30:
        return float("nan")
    aligned = X.loc[other.index, col].dropna()
    common = other.index.intersection(aligned.index)
    if len(common) < 30:
        return float("nan")
    y = X.loc[common, col].to_numpy(dtype=np.float64)
    Xo = X.loc[common, [c for c in X.columns if c != col]].to_numpy(dtype=np.float64)
    if np.any(np.isnan(Xo)) or np.any(np.isnan(y)):
        return float("nan")
    mdl = LinearRegression().fit(Xo, y)
    r2 = mdl.score(Xo, y)
    return float("inf") if r2 >= 1.0 else 1.0 / (1.0 - r2)


def main():
    df = pd.read_parquet(V2_DATASET)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df = df[df["year"].isin(TRAIN_YEARS)].dropna(subset=[LABEL_COL]).reset_index(drop=True)

    feats = [c for c in FEATURE_COLS if c in df.columns]
    log.info(f"  {len(df):,} rows × {len(feats)} feats")

    # Drop all-NaN features for VIF (linear regression can't handle them)
    keep = [c for c in feats if df[c].notna().sum() > 100]
    dropped = [c for c in feats if c not in keep]
    if dropped:
        log.info(f"  excluded from VIF (sparse / all-NaN): {dropped}")

    X = df[keep].copy()
    # Median-impute remaining NaN so VIF computation is stable
    X = X.fillna(X.median(numeric_only=True))

    log.info("── VIF (variance inflation factor) ──")
    rows = []
    for c in keep:
        v = vif_one(X, c)
        rows.append({"feature": c, "group": feature_group(c), "vif": v})
        flag = ""
        if np.isfinite(v):
            if v > 10:   flag = " ← SEVERE (>10)"
            elif v > 5:  flag = " ← concerning (>5)"
        log.info(f"  {c:<28} [{feature_group(c)}]  VIF = {v:7.2f}{flag}")
    vif_df = pd.DataFrame(rows).sort_values("vif", ascending=False)
    vif_df.to_csv(OUT_TABLES / "vif_v2.csv", index=False)

    # ── per-group correlation summary ──
    log.info("── per-group max |Pearson r| ──")
    group_rows = []
    for g, cols in FEATURE_GROUPS.items():
        cols = [c for c in cols if c in keep]
        if len(cols) < 2:
            continue
        c = X[cols].corr().abs()
        np.fill_diagonal(c.values, np.nan)
        max_r = float(c.max().max())
        mean_r = float(c.values[~np.isnan(c.values)].mean())
        # Which pair?
        pair = None
        if not np.isnan(max_r):
            idx = np.unravel_index(np.nanargmax(c.values), c.shape)
            pair = (cols[idx[0]], cols[idx[1]])
        group_rows.append({
            "group":     g,
            "label":     GROUP_LABEL.get(g, g),
            "n_feats":   len(cols),
            "max_abs_r": max_r,
            "max_pair":  f"{pair[0]} ↔ {pair[1]}" if pair else "",
            "mean_abs_r": mean_r,
        })
        log.info(f"  [{g}] {GROUP_LABEL.get(g, g):<22}  "
                 f"max|r|={max_r:.3f}  pair=({pair[0]}, {pair[1]})  "
                 f"mean|r|={mean_r:.3f}")
    pd.DataFrame(group_rows).to_csv(OUT_TABLES / "per_group_correlation_v2.csv", index=False)

    # ── VIF bar chart ──
    plot_df = vif_df.copy()
    plot_df["vif_plot"] = plot_df["vif"].clip(upper=50)   # cap inf for plotting
    fig, ax = plt.subplots(figsize=(7, max(5, 0.18 * len(plot_df))))
    colors = [GROUP_COLOR.get(g, "#888888") for g in plot_df["group"]]
    bars = ax.barh(plot_df["feature"][::-1], plot_df["vif_plot"][::-1], color=colors[::-1])
    ax.axvline(5, color="orange", linestyle="--", linewidth=0.7, label="VIF=5 concerning")
    ax.axvline(10, color="red", linestyle="--", linewidth=0.7, label="VIF=10 severe")
    ax.set_xlabel("VIF (capped at 50 for plot)")
    ax.set_title("Variance Inflation Factor by feature (capped axis)")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_FIGS / "F_vif_bar.png", dpi=130)
    plt.close(fig)
    log.info(f"  wrote {OUT_FIGS / 'F_vif_bar.png'}")


if __name__ == "__main__":
    main()
