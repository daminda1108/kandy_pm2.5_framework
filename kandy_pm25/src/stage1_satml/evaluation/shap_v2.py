"""
shap_v2.py — SHAP analysis for Stage 1 v2 (audit addition 2026-05-18).

Loads the trained-on-all-Kandy quantile XGBoost model
(`results/models/xgboost_v2_full_kandy.ubj`) and computes SHAP attributions
on the training pool (1,526 sensor-day rows). XGBoost's quantile objective
emits a multi-output tree (3 quantile heads), so SHAP returns a list of
arrays, one per head; we focus on the median (q50) head as the primary
explanation channel.

Outputs:
  data/processed/stage1_v2/eda/shap_global_v2.csv         per-feature mean |SHAP|
  data/processed/stage1_v2/eda/shap_grouped_v2.csv        per-mechanistic-group total
  results/figures/stage1_v2/eda/F_shap_global_bar.png     top features bar chart
  results/figures/stage1_v2/eda/F_shap_grouped_bar.png    per-group bar chart
  results/figures/stage1_v2/eda/F_shap_beeswarm.png       beeswarm (top 15)

Usage:
  python -m src.stage1_satml.evaluation.shap_v2
  python src/stage1_satml/evaluation/shap_v2.py
"""

import argparse
import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import PROC_DIR, FIGURES_DIR, MODELS_DIR, LOG_FORMAT, LOG_DATEFMT
from src.stage1_satml.models.train_xgboost_v2 import (
    LABEL_COL, FEATURE_GROUPS, FEATURE_COLS, TRAIN_YEARS,
)
from src.stage1_satml.visualization.eda_v2 import (
    feature_group, GROUP_COLOR, GROUP_LABEL,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("shap_v2")

V2_DATASET = PROC_DIR / "stage1_v2" / "dataset_v2_multistation_daily.parquet"
MODEL_PATH = MODELS_DIR / "xgboost_v2_full_kandy.ubj"

OUT_TABLES = PROC_DIR / "stage1_v2" / "eda"
OUT_FIGS   = FIGURES_DIR / "stage1_v2" / "eda"
OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_FIGS.mkdir(parents=True, exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-sample", type=int, default=1000,
                    help="SHAP background sample size (CLAUDE.md says 1000)")
    args = ap.parse_args()

    log.info("── load dataset + model ──")
    df = pd.read_parquet(V2_DATASET)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df = df[df["year"].isin(TRAIN_YEARS)].dropna(subset=[LABEL_COL]).reset_index(drop=True)
    log.info(f"  dataset: {len(df):,} rows")

    model = xgb.XGBRegressor()
    model.load_model(MODEL_PATH)
    feats = model.get_booster().feature_names or [c for c in FEATURE_COLS if c in df.columns]
    log.info(f"  model: {len(feats)} features  (path={MODEL_PATH})")

    rng = np.random.default_rng(42)
    if len(df) > args.n_sample:
        idx = rng.choice(len(df), args.n_sample, replace=False)
        sample = df.iloc[idx]
    else:
        sample = df
    X = sample[feats].astype(np.float32).reset_index(drop=True)

    log.info("── compute SHAP (TreeExplainer) ──")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # XGBoost quantile-regression emits multi-output: shap_values may be (n, m, 3).
    arr = np.asarray(shap_values)
    if arr.ndim == 3:
        log.info(f"  multi-output SHAP shape={arr.shape} — using q50 (axis=2 idx=1)")
        shap_q50 = arr[:, :, 1]   # median quantile (q50)
    else:
        shap_q50 = arr
    log.info(f"  shap_q50 shape={shap_q50.shape}")

    # ── Global importance: mean |SHAP| per feature ──
    mean_abs = np.abs(shap_q50).mean(axis=0)
    global_df = pd.DataFrame({
        "feature":   feats,
        "group":     [feature_group(f) for f in feats],
        "mean_abs_shap": mean_abs,
        "frac_total":    mean_abs / mean_abs.sum(),
    }).sort_values("mean_abs_shap", ascending=False)
    global_df.to_csv(OUT_TABLES / "shap_global_v2.csv", index=False)

    log.info("  top 15 features by mean |SHAP|:")
    for _, r in global_df.head(15).iterrows():
        log.info(f"    {r['feature']:<28} [{r['group']}]  "
                 f"{r['mean_abs_shap']:7.4f}  ({r['frac_total']*100:4.1f}%)")

    # ── Grouped importance ──
    grouped = global_df.groupby("group", as_index=False).agg(
        mean_abs_shap=("mean_abs_shap", "sum"),
        n_features=("feature", "count"),
        frac_total=("frac_total", "sum"),
    ).sort_values("mean_abs_shap", ascending=False)
    grouped["group_label"] = [GROUP_LABEL.get(g, g) for g in grouped["group"]]
    grouped.to_csv(OUT_TABLES / "shap_grouped_v2.csv", index=False)

    log.info("  mechanistic-group breakdown:")
    for _, r in grouped.iterrows():
        log.info(f"    [{r['group']}] {r['group_label']:<22}  "
                 f"{r['mean_abs_shap']:7.4f}  ({r['frac_total']*100:5.1f}%, "
                 f"n_feat={int(r['n_features'])})")

    # ── Plot 1: top-feature bar chart ──
    top = global_df.head(15)
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = [GROUP_COLOR.get(g, "#888888") for g in top["group"]]
    ax.barh(top["feature"][::-1], top["mean_abs_shap"][::-1], color=colors[::-1])
    ax.set_xlabel("mean |SHAP value| (µg/m³)")
    ax.set_title("Top 15 features by mean |SHAP| (Stage 1 v2, q50 head, n_bg=1000)")
    ax.grid(axis="x", alpha=0.3)
    # mechanism legend
    used = list(top["group"].unique())
    handles = [plt.Rectangle((0, 0), 1, 1, color=GROUP_COLOR.get(g, "#888")) for g in used]
    labels  = [f"{g} — {GROUP_LABEL.get(g, g)}" for g in used]
    ax.legend(handles, labels, loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_FIGS / "F_shap_global_bar.png", dpi=130)
    plt.close(fig)
    log.info(f"  wrote {OUT_FIGS / 'F_shap_global_bar.png'}")

    # ── Plot 2: grouped bar chart ──
    fig, ax = plt.subplots(figsize=(7, 4))
    glab = [f"{r['group']}\n{r['group_label']}" for _, r in grouped.iterrows()]
    gcol = [GROUP_COLOR.get(g, "#888888") for g in grouped["group"]]
    ax.bar(glab, grouped["mean_abs_shap"], color=gcol, edgecolor="black", linewidth=0.5)
    ax.set_ylabel("Σ mean |SHAP| (µg/m³)")
    ax.set_title("SHAP importance by mechanistic group")
    ax.grid(axis="y", alpha=0.3)
    # annotate
    for i, (_, r) in enumerate(grouped.iterrows()):
        ax.text(i, r["mean_abs_shap"], f"{r['frac_total']*100:.1f}%",
                ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_FIGS / "F_shap_grouped_bar.png", dpi=130)
    plt.close(fig)
    log.info(f"  wrote {OUT_FIGS / 'F_shap_grouped_bar.png'}")

    # ── Plot 3: beeswarm of top 15 features ──
    top_feats = top["feature"].tolist()
    top_idx   = [feats.index(f) for f in top_feats]
    fig = plt.figure(figsize=(8, 6))
    shap.summary_plot(
        shap_q50[:, top_idx], X[top_feats],
        feature_names=top_feats, show=False, max_display=15, plot_size=None,
    )
    fig.suptitle("SHAP beeswarm — top 15 features (q50 head)", fontsize=10, y=1.02)
    fig.savefig(OUT_FIGS / "F_shap_beeswarm.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  wrote {OUT_FIGS / 'F_shap_beeswarm.png'}")


if __name__ == "__main__":
    main()
