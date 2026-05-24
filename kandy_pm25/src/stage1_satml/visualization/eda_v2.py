"""
eda_v2.py — Systematic EDA for Stage 1 v2 standalone-paper dataset.

Audit-driven addition (2026-05-18) per data-science-discipline review.
Up until now, EDA was incident-driven (NaN diagnostics, RH saturation,
MODIS deprecation). This script does the up-front exploration a reviewer
will expect to see.

Generates:
  data/processed/stage1_v2/eda/feature_distributions.csv    — per-feature stats
  data/processed/stage1_v2/eda/feature_correlation_matrix.csv
  data/processed/stage1_v2/eda/feature_label_correlation.csv
  data/processed/stage1_v2/eda/sensor_coherence_summary.csv
  data/processed/stage1_v2/eda/label_temporal_summary.csv
  data/processed/stage1_v2/eda/outlier_summary.csv
  results/figures/stage1_v2/eda/             ← PNG figures
    F_distributions_grouped.png
    F_correlation_heatmap.png
    F_sensor_timeseries.png
    F_sensor_overlap_scatter.png
    F_label_by_year.png
    F_label_by_month.png

Usage:
  python -m src.stage1_satml.visualization.eda_v2
  python src/stage1_satml/visualization/eda_v2.py
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

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import PROC_DIR, FIGURES_DIR, LOG_FORMAT, LOG_DATEFMT
from src.stage1_satml.models.train_xgboost_v2 import (
    LABEL_COL, FEATURE_GROUPS, FEATURE_COLS, TRAIN_YEARS,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("eda_v2")

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

V2_DATASET = PROC_DIR / "stage1_v2" / "dataset_v2_multistation_daily.parquet"
OUT_TABLES = PROC_DIR / "stage1_v2" / "eda"
OUT_FIGS   = FIGURES_DIR / "stage1_v2" / "eda"
OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_FIGS.mkdir(parents=True, exist_ok=True)

# Color per mechanistic group (for plot grouping)
GROUP_COLOR = {
    "A": "#1f77b4",   # ventilation — blue
    "B": "#ff7f0e",   # valley transport — orange
    "C": "#2ca02c",   # wet scavenging — green
    "D": "#d62728",   # source / column — red
    "E": "#9467bd",   # multi-fidelity priors — purple
    "F": "#8c564b",   # climate modes — brown
    "G": "#e377c2",   # temporal — pink
    "STATION": "#7f7f7f",  # gray
}

GROUP_LABEL = {
    "A": "ventilation", "B": "valley_transport", "C": "wet_scavenging",
    "D": "source_column", "E": "reanalysis_priors", "F": "climate_modes",
    "G": "temporal", "STATION": "station_coords",
}


def feature_group(col: str) -> str:
    for g, cols in FEATURE_GROUPS.items():
        if col in cols:
            return g
    return "?"


# ─────────────────────────────────────────────────────────────────────────────
# Load
# ─────────────────────────────────────────────────────────────────────────────

def load_for_eda() -> pd.DataFrame:
    df = pd.read_parquet(V2_DATASET)
    df["date"] = pd.to_datetime(df["date"])
    df["year"]  = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df = df[df["year"].isin(TRAIN_YEARS)].reset_index(drop=True)
    log.info(f"  loaded {len(df):,} rows × {len(df.columns)} cols  "
             f"[{df['date'].min().date()} → {df['date'].max().date()}]")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Section 1 — Feature distributions
# ─────────────────────────────────────────────────────────────────────────────

def section_distributions(df: pd.DataFrame) -> pd.DataFrame:
    log.info("── feature distributions ──")
    rows = []
    for c in FEATURE_COLS + [LABEL_COL]:
        if c not in df.columns:
            continue
        s = df[c].dropna()
        rows.append({
            "feature":  c,
            "group":    feature_group(c) if c in FEATURE_COLS else "LABEL",
            "n_valid":  int(s.size),
            "n_nan":    int(df[c].isna().sum()),
            "frac_nan": float(df[c].isna().mean()),
            "mean":     float(s.mean()) if s.size else float("nan"),
            "std":      float(s.std()) if s.size else float("nan"),
            "min":      float(s.min()) if s.size else float("nan"),
            "p01":      float(s.quantile(0.01)) if s.size else float("nan"),
            "p25":      float(s.quantile(0.25)) if s.size else float("nan"),
            "p50":      float(s.median()) if s.size else float("nan"),
            "p75":      float(s.quantile(0.75)) if s.size else float("nan"),
            "p99":      float(s.quantile(0.99)) if s.size else float("nan"),
            "max":      float(s.max()) if s.size else float("nan"),
            "skew":     float(s.skew()) if s.size > 2 else float("nan"),
            "kurtosis": float(s.kurtosis()) if s.size > 2 else float("nan"),
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT_TABLES / "feature_distributions.csv", index=False)
    return out


def plot_distributions_grouped(df: pd.DataFrame) -> None:
    """Grid of feature histograms, colored by mechanistic group."""
    feats = [c for c in FEATURE_COLS if c in df.columns and df[c].notna().any()]
    n = len(feats)
    ncols = 5
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.2 * ncols, 2.2 * nrows))
    axes = axes.flatten()
    for i, c in enumerate(feats):
        ax = axes[i]
        g = feature_group(c)
        s = df[c].dropna()
        if s.size < 5:
            ax.text(0.5, 0.5, "(all NaN)", ha="center", va="center", transform=ax.transAxes)
        else:
            ax.hist(s, bins=40, color=GROUP_COLOR.get(g, "#888888"),
                    edgecolor="black", linewidth=0.3, alpha=0.85)
        ax.set_title(f"{c}\n[{g}]", fontsize=8)
        ax.tick_params(labelsize=6)
        ax.grid(alpha=0.3)
    for j in range(n, len(axes)):
        axes[j].axis("off")
    fig.suptitle("Feature distributions (Stage 1 v2, 2019-2025 training pool)",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(OUT_FIGS / "F_distributions_grouped.png", dpi=130)
    plt.close(fig)
    log.info(f"  wrote {OUT_FIGS / 'F_distributions_grouped.png'}")


# ─────────────────────────────────────────────────────────────────────────────
# Section 2 — Correlation analysis
# ─────────────────────────────────────────────────────────────────────────────

def section_correlations(df: pd.DataFrame) -> pd.DataFrame:
    log.info("── correlation matrix ──")
    feats = [c for c in FEATURE_COLS if c in df.columns and df[c].notna().any()]
    corr = df[feats + [LABEL_COL]].corr(method="spearman")  # robust to outliers
    corr.to_csv(OUT_TABLES / "feature_correlation_matrix.csv")

    # Label correlations sorted
    label_corr = corr[LABEL_COL].drop(LABEL_COL).sort_values(key=abs, ascending=False)
    label_corr_df = pd.DataFrame({
        "feature":      label_corr.index,
        "group":        [feature_group(c) for c in label_corr.index],
        "spearman_corr_with_label": label_corr.values,
    })
    label_corr_df.to_csv(OUT_TABLES / "feature_label_correlation.csv", index=False)
    return corr


def plot_correlation_heatmap(corr: pd.DataFrame) -> None:
    feats = [c for c in corr.columns if c != LABEL_COL]
    # Reorder rows/cols by mechanistic group so blocks are visible.
    groups = sorted(feats, key=lambda c: (feature_group(c), c))
    ordered = groups + [LABEL_COL]
    M = corr.loc[ordered, ordered].values
    fig, ax = plt.subplots(figsize=(0.28 * len(ordered) + 2, 0.28 * len(ordered) + 1))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(ordered)))
    ax.set_yticks(range(len(ordered)))
    ax.set_xticklabels(ordered, rotation=90, fontsize=6)
    ax.set_yticklabels(ordered, fontsize=6)
    fig.colorbar(im, ax=ax, shrink=0.5, label="Spearman ρ")
    ax.set_title("Feature × feature × label Spearman correlations (grouped)", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT_FIGS / "F_correlation_heatmap.png", dpi=130)
    plt.close(fig)
    log.info(f"  wrote {OUT_FIGS / 'F_correlation_heatmap.png'}")


# ─────────────────────────────────────────────────────────────────────────────
# Section 3 — Sensor coherence
# ─────────────────────────────────────────────────────────────────────────────

def section_sensor_coherence(df: pd.DataFrame) -> pd.DataFrame:
    log.info("── sensor coherence ──")
    pivot = df.pivot_table(index="date", columns="sensor_id", values=LABEL_COL)
    rows = []
    sensors = sorted(df["sensor_id"].unique())
    for s1 in sensors:
        for s2 in sensors:
            if s1 >= s2:
                continue
            both = pivot[[s1, s2]].dropna()
            if len(both) < 30:
                continue
            r = both[s1].corr(both[s2])
            rows.append({
                "sensor_a":     s1,
                "sensor_b":     s2,
                "n_overlap":    int(len(both)),
                "pearson_corr": float(r),
                "mean_a":       float(both[s1].mean()),
                "mean_b":       float(both[s2].mean()),
                "rmse_a_vs_b":  float(np.sqrt(((both[s1] - both[s2])**2).mean())),
                "bias_a_minus_b": float((both[s1] - both[s2]).mean()),
            })
    out = pd.DataFrame(rows)
    out.to_csv(OUT_TABLES / "sensor_coherence_summary.csv", index=False)
    return out


def plot_sensor_timeseries(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    sensors = sorted(df["sensor_id"].unique())
    for s in sensors:
        sub = df[df["sensor_id"] == s].sort_values("date")
        name = sub["sensor_name"].iloc[0]
        ax.plot(sub["date"], sub[LABEL_COL], label=f"{name} (n={len(sub)})",
                linewidth=0.7, alpha=0.85)
    ax.set_xlabel("date"); ax.set_ylabel("PM2.5 (µg/m³, FECT-calibrated)")
    ax.set_title("FECT sensor daily PM2.5 — coverage + co-evolution")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_FIGS / "F_sensor_timeseries.png", dpi=130)
    plt.close(fig)
    log.info(f"  wrote {OUT_FIGS / 'F_sensor_timeseries.png'}")


def plot_sensor_overlap_scatter(df: pd.DataFrame) -> None:
    sensors = sorted(df["sensor_id"].unique())
    if len(sensors) < 2:
        return
    pivot = df.pivot_table(index="date", columns="sensor_id", values=LABEL_COL)
    s1, s2 = sensors[0], sensors[1]
    both = pivot[[s1, s2]].dropna()
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(both[s1], both[s2], s=8, alpha=0.5, color="#1f77b4")
    lim = max(both.max().max() * 1.05, 50)
    ax.plot([0, lim], [0, lim], "k--", linewidth=0.7, label="1:1")
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_xlabel(f"Sensor {s1}"); ax.set_ylabel(f"Sensor {s2}")
    r = both[s1].corr(both[s2])
    ax.set_title(f"Daily PM2.5 overlap (n={len(both)}, Pearson r={r:.3f})")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_FIGS / "F_sensor_overlap_scatter.png", dpi=130)
    plt.close(fig)
    log.info(f"  wrote {OUT_FIGS / 'F_sensor_overlap_scatter.png'}")


# ─────────────────────────────────────────────────────────────────────────────
# Section 4 — Label temporal structure
# ─────────────────────────────────────────────────────────────────────────────

def section_label_temporal(df: pd.DataFrame) -> pd.DataFrame:
    log.info("── label temporal structure ──")
    rows = []
    for yr, sub in df.groupby("year"):
        s = sub[LABEL_COL].dropna()
        rows.append({"scope": f"year_{yr}", "n": len(s),
                     "mean": s.mean(), "p50": s.median(), "p95": s.quantile(0.95),
                     "max": s.max()})
    for mo, sub in df.groupby("month"):
        s = sub[LABEL_COL].dropna()
        rows.append({"scope": f"month_{mo:02d}", "n": len(s),
                     "mean": s.mean(), "p50": s.median(), "p95": s.quantile(0.95),
                     "max": s.max()})
    out = pd.DataFrame(rows)
    out.to_csv(OUT_TABLES / "label_temporal_summary.csv", index=False)
    return out


def plot_label_by_period(df: pd.DataFrame) -> None:
    # by year
    fig, ax = plt.subplots(figsize=(8, 4))
    years = sorted(df["year"].unique())
    data = [df[df["year"] == y][LABEL_COL].dropna().values for y in years]
    ax.boxplot(data, labels=[str(y) for y in years], showfliers=False)
    ax.set_xlabel("year"); ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_title("PM2.5 label distribution by year (FECT, Kandy)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_FIGS / "F_label_by_year.png", dpi=130)
    plt.close(fig)

    # by month (pooled)
    fig, ax = plt.subplots(figsize=(8, 4))
    months = sorted(df["month"].unique())
    data = [df[df["month"] == m][LABEL_COL].dropna().values for m in months]
    monsoon_label = {1: "NE", 2: "NE", 3: "FI", 4: "FI", 5: "SW", 6: "SW",
                     7: "SW", 8: "SW", 9: "SW", 10: "SI", 11: "SI", 12: "NE"}
    labels = [f"{m:02d}\n{monsoon_label.get(m,'')}" for m in months]
    ax.boxplot(data, labels=labels, showfliers=False)
    ax.set_xlabel("calendar month  (NE = NE monsoon, FI = 1st inter-mon, SW = SW monsoon, SI = 2nd inter-mon)")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_title("PM2.5 by month — Kandy monsoon seasonality")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_FIGS / "F_label_by_month.png", dpi=130)
    plt.close(fig)
    log.info(f"  wrote {OUT_FIGS / 'F_label_by_year.png'}, F_label_by_month.png")


# ─────────────────────────────────────────────────────────────────────────────
# Section 5 — Outlier analysis
# ─────────────────────────────────────────────────────────────────────────────

def section_outliers(df: pd.DataFrame) -> pd.DataFrame:
    log.info("── outlier scan ──")
    rows = []
    # Tukey IQR fences
    s = df[LABEL_COL].dropna()
    q25, q75 = s.quantile([0.25, 0.75])
    iqr = q75 - q25
    lo, hi = q25 - 1.5 * iqr, q75 + 1.5 * iqr
    n_outliers_iqr = int((s < lo).sum() + (s > hi).sum())
    rows.append({"scope": "label_overall_tukey_iqr",
                 "n_outliers": n_outliers_iqr,
                 "frac": n_outliers_iqr / len(s),
                 "lower_fence": float(lo), "upper_fence": float(hi)})

    # Per-feature top-5 extreme values
    for c in FEATURE_COLS + [LABEL_COL]:
        if c not in df.columns:
            continue
        s = df[c].dropna()
        if len(s) < 10:
            continue
        rows.append({"scope": f"feature_{c}",
                     "n_outliers": int(((s < s.quantile(0.01)) | (s > s.quantile(0.99))).sum()),
                     "frac": float(((s < s.quantile(0.01)) | (s > s.quantile(0.99))).mean()),
                     "p01": float(s.quantile(0.01)),
                     "p99": float(s.quantile(0.99)),
                     "max_abs_z": float(np.abs((s - s.mean()) / (s.std() + 1e-9)).max()),
                     })
    out = pd.DataFrame(rows)
    out.to_csv(OUT_TABLES / "outlier_summary.csv", index=False)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-figs", action="store_true", help="skip PNG generation")
    args = ap.parse_args()

    df = load_for_eda()
    dist = section_distributions(df)
    corr = section_correlations(df)
    sens = section_sensor_coherence(df)
    section_label_temporal(df)
    section_outliers(df)

    log.info(f"  rows × cols: {df.shape}; "
             f"high-NaN features (>50%): "
             f"{dist[dist.frac_nan>0.5].feature.tolist()}")

    # ── top label correlations ──
    label_corr = pd.read_csv(OUT_TABLES / "feature_label_correlation.csv").head(10)
    log.info("  top 10 features by |Spearman ρ with pm25_observed|:")
    for _, r in label_corr.iterrows():
        log.info(f"    {r['feature']:<28} [{r['group']}] {r['spearman_corr_with_label']:+.3f}")

    # ── sensor coherence summary ──
    log.info("  sensor inter-comparison:")
    for _, r in sens.iterrows():
        log.info(f"    {int(r['sensor_a'])}↔{int(r['sensor_b'])}: "
                 f"n={int(r['n_overlap']):>4}, r={r['pearson_corr']:+.3f}, "
                 f"means {r['mean_a']:.1f} vs {r['mean_b']:.1f} (Δ={r['bias_a_minus_b']:+.1f})")

    if not args.no_figs:
        plot_distributions_grouped(df)
        plot_correlation_heatmap(corr)
        plot_sensor_timeseries(df)
        plot_sensor_overlap_scatter(df)
        plot_label_by_period(df)


if __name__ == "__main__":
    main()
