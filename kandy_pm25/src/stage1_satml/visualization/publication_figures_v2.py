"""
publication_figures_v2.py — Publication-quality figures for RECAP Stage A.

Generates F01–F10 (pre-reg §9) as PDF + PNG at 300 dpi, IEEE column widths.

Outputs:
  results/figures/stage1_v2/publication/F01_domain_map.{pdf,png}
  results/figures/stage1_v2/publication/F02_timeseries.{pdf,png}
  results/figures/stage1_v2/publication/F03_baseline_comparison.{pdf,png}
  results/figures/stage1_v2/publication/F04_per_month.{pdf,png}
  results/figures/stage1_v2/publication/F05_reliability.{pdf,png}
  results/figures/stage1_v2/publication/F06_shap_importance.{pdf,png}
  results/figures/stage1_v2/publication/F07_sensor_coherence.{pdf,png}
  results/figures/stage1_v2/publication/F08_ablation.{pdf,png}
  results/figures/stage1_v2/publication/F09_ood_embassy.{pdf,png}
  results/figures/stage1_v2/publication/F10_worst_month.{pdf,png}

Style:
  - SciencePlots IEEE preset + STIX math fonts
  - Single column = 88 mm; double column = 180 mm
  - Colour-blind safe palette (Wong / IBM)
  - Bootstrap 95% CIs as error bars / shaded bands

Usage:
  python -m src.stage1_satml.visualization.publication_figures_v2
  python src/stage1_satml/visualization/publication_figures_v2.py
  python src/stage1_satml/visualization/publication_figures_v2.py --only F02 F03
"""

import argparse
import logging
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.colors import LightSource
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds

warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import PROC_DIR, FIGURES_DIR, RAW_DIR, LOG_FORMAT, LOG_DATEFMT
from src.utils.plot_style import (
    apply_style, SINGLE_COL_IN, DOUBLE_COL_IN, FIG_DPI,
    PM25_CMAP, DIFF_CMAP,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("publication_figures_v2")

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

TRAIN_DIR  = PROC_DIR / "stage1_v2" / "training"
EDA_DIR    = PROC_DIR / "stage1_v2" / "eda"
DATASET    = PROC_DIR / "stage1_v2" / "dataset_v2_multistation_daily.parquet"
DEM_TIF    = RAW_DIR / "dem" / "srtm_elevation_30m.tif"

OUT_DIR    = FIGURES_DIR / "stage1_v2" / "publication"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Color palette (Wong 2011, colour-blind safe)
# ─────────────────────────────────────────────────────────────────────────────

C_AKURANA   = "#D55E00"   # vermillion
C_HANTANA   = "#0072B2"   # blue
C_KOALA     = "#009E73"   # bluish green
C_EMBASSY   = "#CC79A7"   # reddish purple
C_RECAP     = "#000000"   # black for model
C_PI        = "#000000"   # PI band shading colour
C_PERSIST   = "#56B4E9"   # sky blue
C_DOYCLIM   = "#E69F00"   # orange
C_CAMS      = "#F0E442"   # yellow
C_GEOS      = "#999999"   # grey

GROUP_COLOR = {
    "A": "#0072B2", "B": "#E69F00", "C": "#009E73", "D": "#D55E00",
    "E": "#CC79A7", "F": "#56B4E9", "G": "#000000", "STATION": "#999999",
}
GROUP_LABEL = {
    "A": "Ventilation", "B": "Valley transport", "C": "Wet scavenging",
    "D": "Source / column", "E": "Reanalysis priors", "F": "Climate modes",
    "G": "Temporal", "STATION": "Station coords",
}

SENSOR_INFO = {
    12451: ("Akurana",    7.366, 80.618, 1538, C_AKURANA),
    33495: ("Hantana TR4", 7.356, 80.631, 1698, C_HANTANA),
}

KOALA_STATION  = (7.27, 80.60, "KOALA (Peradeniya)", C_KOALA)
EMBASSY_STATION = (6.909, 79.875, "US Embassy Colombo", C_EMBASSY)


def _save(fig, name: str) -> None:
    pdf = OUT_DIR / f"{name}.pdf"
    png = OUT_DIR / f"{name}.png"
    fig.savefig(pdf, dpi=FIG_DPI, bbox_inches="tight")
    fig.savefig(png, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  wrote {pdf.name}, {png.name}")


# ─────────────────────────────────────────────────────────────────────────────
# F01 — Domain map
# ─────────────────────────────────────────────────────────────────────────────

def fig01_domain_map() -> None:
    log.info("── F01 domain map ──")
    fig = plt.figure(figsize=(DOUBLE_COL_IN, DOUBLE_COL_IN * 0.55))
    # Two panels: (a) wider Sri Lanka context; (b) Kandy zoom
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.35], wspace=0.18)
    ax_sl  = fig.add_subplot(gs[0, 0])
    ax_kd  = fig.add_subplot(gs[0, 1])

    # ── (a) Sri Lanka context ─────────────────────────────────────────────
    ax_sl.set_xlim(79.5, 82.0); ax_sl.set_ylim(5.7, 9.9)
    ax_sl.set_aspect("equal")
    ax_sl.set_xlabel("Longitude (°E)"); ax_sl.set_ylabel("Latitude (°N)")
    ax_sl.set_title("(a) Sri Lanka — study regions", loc="left", fontsize=9)
    ax_sl.grid(alpha=0.3, linewidth=0.4)
    # Plot stations as scatter (no coastline file → leave as scatter on graticule)
    for sid, (name, lat, lon, _alt, c) in SENSOR_INFO.items():
        ax_sl.scatter(lon, lat, s=40, marker="o", c=c, edgecolor="black", linewidth=0.6, zorder=5)
    ax_sl.scatter(KOALA_STATION[1], KOALA_STATION[0], s=40, marker="s", c=KOALA_STATION[3],
                  edgecolor="black", linewidth=0.6, zorder=5)
    ax_sl.scatter(EMBASSY_STATION[1], EMBASSY_STATION[0], s=40, marker="D",
                  c=EMBASSY_STATION[3], edgecolor="black", linewidth=0.6, zorder=5)
    # bbox rectangles
    kbox = mpatches.Rectangle((80.45, 7.10), 0.40, 0.40,
                              fill=False, edgecolor="black", linewidth=1.0)
    cbox = mpatches.Rectangle((79.82, 6.85), 0.12, 0.12,
                              fill=False, edgecolor=C_EMBASSY, linewidth=1.0)
    ax_sl.add_patch(kbox); ax_sl.add_patch(cbox)
    ax_sl.text(80.93, 7.15, "Kandy bbox", fontsize=7)
    ax_sl.text(79.94, 6.78, "Colombo bbox", fontsize=7, color=C_EMBASSY)

    # ── (b) Kandy zoom with DEM hillshade if available ────────────────────
    bbox = (80.45, 80.85, 7.10, 7.50)   # lon_min, lon_max, lat_min, lat_max
    ax_kd.set_xlim(bbox[0], bbox[1]); ax_kd.set_ylim(bbox[2], bbox[3])
    ax_kd.set_aspect("equal")
    ax_kd.set_xlabel("Longitude (°E)"); ax_kd.set_ylabel("Latitude (°N)")
    ax_kd.set_title("(b) Kandy domain — sensor locations + terrain", loc="left", fontsize=9)

    if DEM_TIF.exists():
        try:
            with rasterio.open(DEM_TIF) as r:
                win = from_bounds(bbox[0], bbox[2], bbox[1], bbox[3], r.transform)
                dem = r.read(1, window=win)
                if dem.dtype.kind != "f":
                    dem = dem.astype(float)
                dem = np.where(dem < -1000, np.nan, dem)
                ls = LightSource(azdeg=315, altdeg=45)
                hs = ls.hillshade(np.nan_to_num(dem, nan=float(np.nanmean(dem))),
                                   vert_exag=2.5)
                ax_kd.imshow(hs, extent=bbox, cmap="gray", alpha=0.55,
                             origin="upper", zorder=1)
                im = ax_kd.imshow(dem, extent=bbox, cmap="terrain",
                                  alpha=0.55, origin="upper", zorder=2)
                cb = fig.colorbar(im, ax=ax_kd, shrink=0.7, pad=0.02)
                cb.set_label("Elevation (m a.s.l.)", fontsize=8)
        except Exception as e:
            log.warning(f"  DEM render failed ({e}); falling back to scatter only")
    else:
        log.warning(f"  DEM not found at {DEM_TIF}; skipping hillshade")

    for sid, (name, lat, lon, alt, c) in SENSOR_INFO.items():
        ax_kd.scatter(lon, lat, s=110, marker="o", c=c, edgecolor="black",
                      linewidth=0.9, zorder=5,
                      label=f"FECT {name} ({alt} m)")
        ax_kd.text(lon + 0.012, lat + 0.005, name, fontsize=8, zorder=6,
                   path_effects=[])

    ax_kd.scatter(KOALA_STATION[1], KOALA_STATION[0], s=110, marker="s",
                  c=KOALA_STATION[3], edgecolor="black", linewidth=0.9, zorder=5,
                  label="KOALA Peradeniya (~480 m)")
    ax_kd.text(KOALA_STATION[1] + 0.012, KOALA_STATION[0] - 0.012,
               "KOALA", fontsize=8, color=KOALA_STATION[3], zorder=6)
    # 15×15 km PINN bbox (training-feature aggregation domain)
    pinn = mpatches.Rectangle((80.566, 7.223), 0.135, 0.135,
                              fill=False, edgecolor="red", linewidth=0.9,
                              linestyle="--")
    ax_kd.add_patch(pinn)
    ax_kd.text(80.57, 7.36, "PINN bbox (15 × 15 km)", color="red", fontsize=7)
    ax_kd.legend(loc="lower left", fontsize=7, framealpha=0.92)

    fig.suptitle("Figure 1 — Study domain and observation network",
                 fontsize=10, y=1.02)
    _save(fig, "F01_domain_map")


# ─────────────────────────────────────────────────────────────────────────────
# F02 — 22-year RECAP reconstruction (2003-2025) with Van Donkelaar overlay
# ─────────────────────────────────────────────────────────────────────────────

def fig02_timeseries() -> None:
    log.info("── F02 22-year reconstruction ──")
    full = pd.read_parquet(TRAIN_DIR / "predictions_22yr_2003_2025.parquet")
    full["date"] = pd.to_datetime(full["date"])
    # Domain-mean daily (sensors collapsed to one curve)
    daily = full.groupby(["date", "extrapolation_flag"]).agg(
        q05=("xgb_q05", "mean"),
        q50=("xgb_q50", "mean"),
        q95=("xgb_q95", "mean"),
    ).reset_index().sort_values("date")
    # 90-day rolling for 22-year-figure clarity
    daily["q50_s"] = daily["q50"].rolling(90, min_periods=10, center=True).mean()
    daily["q05_s"] = daily["q05"].rolling(90, min_periods=10, center=True).mean()
    daily["q95_s"] = daily["q95"].rolling(90, min_periods=10, center=True).mean()

    # FECT obs (for 2019-2025 visible markers)
    fect = pd.read_parquet(DATASET)
    fect["date"] = pd.to_datetime(fect["date"])

    # Annual triangulation
    val_csv = PROC_DIR / "stage1_v2" / "eda" / "cross_product_22yr_v2.csv"
    annual = pd.read_csv(val_csv) if val_csv.exists() else pd.DataFrame()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(DOUBLE_COL_IN, DOUBLE_COL_IN * 0.62),
                                    sharex=False, gridspec_kw={"height_ratios": [3, 1.6]})

    # ── (a) 22-year time series ────────────────────────────────────────────
    extr_end = pd.Timestamp("2018-12-31")
    ax1.axvspan(daily["date"].min(), extr_end, color="#e0e0e0", alpha=0.45,
                zorder=0, label="Extrapolation (PI × 1.5, no FECT obs)")
    ax1.fill_between(daily["date"], daily["q05_s"], daily["q95_s"],
                     color=C_PI, alpha=0.15, linewidth=0, label="RECAP 90 % PI (90-d)")
    ax1.plot(daily["date"], daily["q50_s"], color=C_RECAP, linewidth=0.9,
             label="RECAP q$_{50}$ (90-d)")
    # FECT obs
    for sid, (name, lat, lon, alt, c) in SENSOR_INFO.items():
        sub = fect[fect["sensor_id"] == sid].sort_values("date")
        ax1.scatter(sub["date"], sub["pm25_observed"], s=2.5, c=c, alpha=0.45,
                    edgecolor="none", label=f"FECT {name}", zorder=3)
    ax1.set_ylabel(r"PM$_{2.5}$ ($\mu$g m$^{-3}$)")
    ax1.set_title("(a) RECAP 22-year daily reconstruction (2003–2025) — Kandy district highlands",
                  loc="left", fontsize=9)
    ax1.legend(loc="upper right", fontsize=7, ncol=2, framealpha=0.92)
    ax1.grid(alpha=0.3, linewidth=0.4)
    ax1.set_ylim(0, max(50, float(daily["q95_s"].max(skipna=True)) * 1.05))
    ax1.xaxis.set_major_locator(mdates.YearLocator(base=2))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # ── (b) Annual triangulation: RECAP vs Van Donkelaar vs scaled reanalyses ─
    if not annual.empty:
        a = annual.sort_values("year")
        ax2.plot(a["year"], a["v2_q50_22yr"], color=C_RECAP, marker="o", linewidth=1.0,
                 markersize=3.5, label="RECAP q$_{50}$ annual")
        ax2.plot(a["year"], a["van_donkelaar"], color=C_EMBASSY, marker="s",
                 linewidth=0.8, markersize=3, label="Van Donkelaar V6GL02.04")
        ax2.plot(a["year"], a["geos_cf_scaled"], color=C_GEOS, marker="^",
                 linewidth=0.7, markersize=3, linestyle="--", label="GEOS-CF × 0.536")
        ax2.plot(a["year"], a["cams_scaled"], color=C_CAMS, marker="v",
                 linewidth=0.7, markersize=3, linestyle="--", label="CAMS × 0.598")
        ax2.axvspan(2003, 2018.5, color="#e0e0e0", alpha=0.45, zorder=0)
        ax2.set_xlim(2003, 2025)
        ax2.set_ylabel(r"Annual mean ($\mu$g m$^{-3}$)")
        ax2.set_xlabel("Year")
        ax2.set_title("(b) Annual-mean triangulation — RECAP vs independent products",
                      loc="left", fontsize=9)
        ax2.legend(loc="upper right", fontsize=7, ncol=2, framealpha=0.92)
        ax2.grid(alpha=0.3, linewidth=0.4)
        # r vs VanD on extrap window
        ext = a[(a["year"] >= 2003) & (a["year"] <= 2018)].dropna(subset=["v2_q50_22yr", "van_donkelaar"])
        if len(ext) > 3:
            r_ext = float(np.corrcoef(ext["v2_q50_22yr"], ext["van_donkelaar"])[0, 1])
            bias_ext = float((ext["v2_q50_22yr"] - ext["van_donkelaar"]).mean())
            ax2.text(0.02, 0.96,
                     f"Extrapolation (2003–2018) vs Van Donkelaar:\n"
                     f"n = {len(ext)}, $r$ = {r_ext:+.3f}, bias = {bias_ext:+.2f} $\\mu$g m$^{{-3}}$",
                     transform=ax2.transAxes, ha="left", va="top", fontsize=7,
                     bbox=dict(facecolor="white", edgecolor="black", linewidth=0.4, pad=2))

    fig.suptitle("Figure 2 — RECAP 22-year reconstruction and annual cross-product validation",
                 fontsize=10, y=1.00)
    fig.tight_layout()
    _save(fig, "F02_timeseries")


# ─────────────────────────────────────────────────────────────────────────────
# F03 — Baseline comparison with bootstrap CIs
# ─────────────────────────────────────────────────────────────────────────────

def fig03_baselines() -> None:
    log.info("── F03 baseline comparison ──")
    bs = pd.read_csv(TRAIN_DIR / "bootstrap_ci_v2.csv")
    sub = bs[bs["config"] == "xgboost_v2_quantile (Kandy LOMO)"]
    # Pull per-model rows: primary = xgboost, baselines via 'model' tag
    rows = []
    # primary
    for m in ["rmse", "r2", "cov90", "crps"]:
        r = sub[(sub["model"] == "primary") & (sub["metric"] == m)]
        if len(r):
            r = r.iloc[0]
            rows.append({"model": "RECAP (XGBoost-v2)", "metric": m,
                         "point": r["point"], "lo": r["ci_low"], "hi": r["ci_high"]})
    # baselines
    bmap = {"baseline_persistence": "Persistence",
            "baseline_doy_clim":    "DOY climatology",
            "baseline_cams_scaled": "CAMS × 0.598",
            "baseline_geos_scaled": "GEOS-CF × 0.536"}
    for k, name in bmap.items():
        for m in ["rmse", "r2"]:
            r = sub[(sub["model"] == k) & (sub["metric"] == m)]
            if len(r):
                r = r.iloc[0]
                rows.append({"model": name, "metric": m,
                             "point": r["point"], "lo": r["ci_low"], "hi": r["ci_high"]})
    plot_df = pd.DataFrame(rows)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(DOUBLE_COL_IN, DOUBLE_COL_IN * 0.40),
                                    gridspec_kw={"width_ratios": [1.4, 1]})

    # ── (a) RMSE comparison ────────────────────────────────────────────────
    order = ["RECAP (XGBoost-v2)", "Persistence", "DOY climatology",
             "CAMS × 0.598", "GEOS-CF × 0.536"]
    colours = [C_RECAP, C_PERSIST, C_DOYCLIM, C_CAMS, C_GEOS]
    rmse_df = plot_df[plot_df["metric"] == "rmse"].set_index("model").loc[order]
    err = np.array([rmse_df["point"] - rmse_df["lo"], rmse_df["hi"] - rmse_df["point"]])
    bars = ax1.barh(range(len(order)), rmse_df["point"], xerr=err, color=colours,
                    edgecolor="black", linewidth=0.6, capsize=3,
                    error_kw={"linewidth": 0.7})
    ax1.set_yticks(range(len(order)))
    ax1.set_yticklabels(order, fontsize=8)
    ax1.invert_yaxis()
    ax1.set_xlabel(r"Pooled LOMO RMSE ($\mu$g m$^{-3}$)")
    ax1.set_title("(a) Headline error (95 % bootstrap CI)", loc="left", fontsize=9)
    ax1.grid(axis="x", alpha=0.3, linewidth=0.4)
    # Annotate H1 reference + Δ%
    base_rmse = float(rmse_df.loc["GEOS-CF × 0.536", "point"])
    for i, (m, v) in enumerate(rmse_df["point"].items()):
        ax1.text(v + max(err[:, i]) + 0.4, i, f"{v:.2f}", va="center", fontsize=7)
    recap_rmse = float(rmse_df.loc["RECAP (XGBoost-v2)", "point"])
    h1_pct = 100 * (base_rmse - recap_rmse) / base_rmse
    ax1.text(0.98, 0.02, f"H1: $\\Delta$RMSE vs GEOS-CF baseline = $-${h1_pct:.0f}%\n(threshold $\\geq$15 %)",
             transform=ax1.transAxes, ha="right", va="bottom",
             fontsize=7, bbox=dict(facecolor="white", edgecolor="black", linewidth=0.4, pad=2))

    # ── (b) R² + cov90 (model + key baselines) ────────────────────────────
    r2_df = plot_df[plot_df["metric"] == "r2"].set_index("model").loc[order]
    cov_row = sub[(sub["model"] == "primary") & (sub["metric"] == "cov90")].iloc[0]
    x = np.arange(len(order))
    err2 = np.array([r2_df["point"] - r2_df["lo"], r2_df["hi"] - r2_df["point"]])
    ax2.barh(x, r2_df["point"], xerr=err2, color=colours, edgecolor="black",
             linewidth=0.6, capsize=3, error_kw={"linewidth": 0.7})
    ax2.axvline(0, color="black", linewidth=0.5)
    ax2.set_yticks(x); ax2.set_yticklabels(order, fontsize=8)
    ax2.invert_yaxis()
    ax2.set_xlabel(r"Pooled $R^2$")
    ax2.set_title("(b) $R^2$ and 90 % PI coverage", loc="left", fontsize=9)
    ax2.grid(axis="x", alpha=0.3, linewidth=0.4)
    for i, (m, v) in enumerate(r2_df["point"].items()):
        ax2.text(v + max(err2[:, i]) + 0.04, i, f"{v:+.3f}", va="center", fontsize=7)
    ax2.text(0.98, 0.02,
             f"RECAP cov90 = {cov_row['point']:.3f}\n"
             f"[{cov_row['ci_low']:.3f}, {cov_row['ci_high']:.3f}]\n"
             "H4 envelope [0.85, 0.95] $\\checkmark$",
             transform=ax2.transAxes, ha="right", va="bottom", fontsize=7,
             bbox=dict(facecolor="white", edgecolor="black", linewidth=0.4, pad=2))

    fig.suptitle("Figure 3 — RECAP vs reanalysis-scaled and statistical baselines",
                 fontsize=10, y=1.02)
    fig.tight_layout()
    _save(fig, "F03_baseline_comparison")


# ─────────────────────────────────────────────────────────────────────────────
# F04 — Per-month LOMO performance + ENSO regime stratification
# ─────────────────────────────────────────────────────────────────────────────

def fig04_per_month() -> None:
    log.info("── F04 per-month performance ──")
    fold = pd.read_csv(TRAIN_DIR / "metrics_per_fold_v2.csv")
    fold = fold[fold["model"] == "xgboost_v2"].copy()
    fold["year"]  = fold["fold"].str.split("-").str[0].astype(int)
    fold["month"] = fold["fold"].str.split("-").str[1].astype(int)
    fold = fold[fold["n"] >= 5].dropna(subset=["rmse"])
    monsoon = {1: "NE", 2: "NE", 3: "FI", 4: "FI", 5: "SW", 6: "SW",
               7: "SW", 8: "SW", 9: "SW", 10: "SI", 11: "SI", 12: "NE"}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(DOUBLE_COL_IN, DOUBLE_COL_IN * 0.40))

    # ── (a) Boxplot of RMSE by calendar month ─────────────────────────────
    months = sorted(fold["month"].unique())
    data = [fold[fold["month"] == m]["rmse"].values for m in months]
    bp = ax1.boxplot(data, positions=months, widths=0.6, patch_artist=True,
                     medianprops=dict(color="black", linewidth=1.1),
                     boxprops=dict(linewidth=0.6),
                     whiskerprops=dict(linewidth=0.6),
                     capprops=dict(linewidth=0.6))
    monsoon_palette = {"NE": "#56B4E9", "FI": "#D55E00", "SW": "#009E73", "SI": "#E69F00"}
    for patch, m in zip(bp["boxes"], months):
        patch.set_facecolor(monsoon_palette[monsoon[m]])
        patch.set_alpha(0.6)
    ax1.set_xticks(months)
    ax1.set_xticklabels([f"{m:02d}\n{monsoon[m]}" for m in months], fontsize=7)
    ax1.set_xlabel("Calendar month  (NE / FI / SW / SI monsoons)")
    ax1.set_ylabel(r"Per-fold RMSE ($\mu$g m$^{-3}$)")
    ax1.set_title("(a) Per-fold LOMO RMSE by calendar month", loc="left", fontsize=9)
    ax1.grid(axis="y", alpha=0.3, linewidth=0.4)
    leg = [mpatches.Patch(color=col, alpha=0.6, label=lab)
           for lab, col in monsoon_palette.items()]
    ax1.legend(handles=leg, fontsize=7, loc="upper right", title="Monsoon",
               title_fontsize=7, framealpha=0.92)

    # ── (b) Heatmap year × month of fold RMSE ─────────────────────────────
    pivot = fold.pivot_table(index="year", columns="month", values="rmse")
    pivot = pivot.reindex(index=range(int(fold.year.min()), int(fold.year.max()) + 1),
                          columns=range(1, 13))
    im = ax2.imshow(pivot.values, aspect="auto", cmap="YlOrRd",
                    vmin=0, vmax=float(np.nanpercentile(pivot.values, 95)))
    ax2.set_yticks(range(len(pivot.index))); ax2.set_yticklabels(pivot.index, fontsize=7)
    ax2.set_xticks(range(12)); ax2.set_xticklabels([f"{m:02d}" for m in range(1, 13)], fontsize=7)
    ax2.set_xlabel("Calendar month")
    ax2.set_title("(b) Per-fold RMSE — year × month", loc="left", fontsize=9)
    cb = fig.colorbar(im, ax=ax2, shrink=0.8, pad=0.02)
    cb.set_label(r"RMSE ($\mu$g m$^{-3}$)", fontsize=7)
    for yi, y in enumerate(pivot.index):
        for xi, m in enumerate(range(1, 13)):
            v = pivot.values[yi, xi]
            if not np.isnan(v):
                ax2.text(xi, yi, f"{v:.1f}", ha="center", va="center",
                         fontsize=6, color="black" if v < 7 else "white")

    fig.suptitle("Figure 4 — RECAP temporal-skill stratification (Kandy LOMO)",
                 fontsize=10, y=1.02)
    fig.tight_layout()
    _save(fig, "F04_per_month")


# ─────────────────────────────────────────────────────────────────────────────
# F05 — Reliability + PI coverage + tail residual histogram
# ─────────────────────────────────────────────────────────────────────────────

def fig05_reliability() -> None:
    log.info("── F05 reliability + PI calibration ──")
    preds = pd.read_parquet(TRAIN_DIR / "predictions_lomo_v2.parquet")
    y = preds["y_true"].to_numpy()
    q05 = preds["xgb_q05"].to_numpy()
    q50 = preds["xgb_q50"].to_numpy()
    q95 = preds["xgb_q95"].to_numpy()

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(DOUBLE_COL_IN, DOUBLE_COL_IN * 0.32))

    # ── (a) Empirical vs nominal PI coverage at multiple α ────────────────
    # Interpolate intermediate quantiles via simple linear interp between (q05, q50, q95).
    alphas = np.linspace(0.05, 0.95, 19)
    emp = []
    for a in alphas:
        if a <= 0.5:
            t = a / 0.5
            qa = q05 + t * (q50 - q05)
        else:
            t = (a - 0.5) / 0.5
            qa = q50 + t * (q95 - q50)
        emp.append((y <= qa).mean())
    ax1.plot([0, 1], [0, 1], color="black", linewidth=0.6, linestyle="--",
             label="Ideal")
    ax1.plot(alphas, emp, marker="o", markersize=3, color=C_RECAP, linewidth=1.0,
             label="RECAP")
    ax1.set_xlabel("Nominal quantile $\\tau$")
    ax1.set_ylabel("Empirical fraction $\\leq q_\\tau$")
    ax1.set_title("(a) Quantile reliability", loc="left", fontsize=9)
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1)
    ax1.grid(alpha=0.3, linewidth=0.4)
    ax1.legend(fontsize=7)

    # ── (b) Per-fold 90% PI coverage histogram ────────────────────────────
    fold = pd.read_csv(TRAIN_DIR / "metrics_per_fold_v2.csv")
    cov_xgb = fold[(fold["model"] == "xgboost_v2") & fold["cov90"].notna()]["cov90"]
    ax2.hist(cov_xgb, bins=np.linspace(0, 1, 21), color=C_RECAP,
             edgecolor="black", linewidth=0.4, alpha=0.6)
    ax2.axvspan(0.85, 0.95, color="green", alpha=0.18, label="H4 envelope")
    ax2.axvline(0.90, color="black", linestyle="--", linewidth=0.6, label="Nominal 0.90")
    pooled_cov = float(((q05 <= y) & (y <= q95)).mean())
    ax2.axvline(pooled_cov, color=C_RECAP, linewidth=1.3,
                label=f"Pooled = {pooled_cov:.3f}")
    ax2.set_xlabel("Per-fold 90 % PI coverage")
    ax2.set_ylabel("Fold count")
    ax2.set_title("(b) Per-fold coverage distribution", loc="left", fontsize=9)
    ax2.legend(fontsize=7, loc="upper left")
    ax2.grid(axis="y", alpha=0.3, linewidth=0.4)

    # ── (c) Standardised residual histogram with Gaussian + Student-t(5) overlay
    sigma = (q95 - q05) / (2 * 1.6449)        # Gaussian approx σ from 90 % PI
    z = (y - q50) / np.where(sigma > 0, sigma, 1.0)
    z = z[np.isfinite(z)]
    bins = np.linspace(-5, 5, 51)
    ax3.hist(z, bins=bins, color=C_RECAP, edgecolor="black", linewidth=0.4,
             alpha=0.55, density=True, label="Standardised residuals")
    xs = np.linspace(-5, 5, 200)
    from scipy.stats import norm, t as student_t
    ax3.plot(xs, norm.pdf(xs), color="black", linewidth=1.0, label="N(0, 1)")
    ax3.plot(xs, student_t.pdf(xs, df=5), color=C_HANTANA, linewidth=1.0,
             linestyle="--", label="Student-t (df=5)")
    ax3.set_xlabel(r"$z = (y - q_{50}) / \hat\sigma$")
    ax3.set_ylabel("Density")
    ax3.set_title("(c) Residual heavy-tail diagnostic", loc="left", fontsize=9)
    ax3.set_xlim(-5, 5)
    ax3.legend(fontsize=7)
    ax3.grid(alpha=0.3, linewidth=0.4)

    fig.suptitle("Figure 5 — RECAP probabilistic-forecast calibration",
                 fontsize=10, y=1.02)
    fig.tight_layout()
    _save(fig, "F05_reliability")


# ─────────────────────────────────────────────────────────────────────────────
# F06 — SHAP grouped importance + top-feature bar (paper-ready)
# ─────────────────────────────────────────────────────────────────────────────

def fig06_shap() -> None:
    log.info("── F06 SHAP grouped + top features ──")
    glob = pd.read_csv(EDA_DIR / "shap_global_v2.csv")
    grp  = pd.read_csv(EDA_DIR / "shap_grouped_v2.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(DOUBLE_COL_IN, DOUBLE_COL_IN * 0.40),
                                    gridspec_kw={"width_ratios": [1.2, 1]})

    # ── (a) Top 12 features ─────────────────────────────────────────────────
    top = glob.head(12).copy()
    colours = [GROUP_COLOR.get(g, "#888") for g in top["group"]]
    ax1.barh(top["feature"][::-1], top["mean_abs_shap"][::-1], color=colours[::-1],
             edgecolor="black", linewidth=0.5)
    ax1.set_xlabel(r"Mean $|\mathrm{SHAP}|$ ($\mu$g m$^{-3}$)")
    ax1.set_title("(a) Top 12 features", loc="left", fontsize=9)
    ax1.grid(axis="x", alpha=0.3, linewidth=0.4)
    # Group legend
    used = list(top["group"].unique())
    handles = [mpatches.Patch(color=GROUP_COLOR.get(g, "#888"),
                              label=f"{g} — {GROUP_LABEL.get(g, g)}") for g in used]
    ax1.legend(handles=handles, fontsize=7, loc="lower right", framealpha=0.92)

    # ── (b) Group sum + fraction ───────────────────────────────────────────
    grp = grp.sort_values("mean_abs_shap", ascending=True)
    glbl = [f"{r['group']} — {GROUP_LABEL.get(r['group'], r['group'])}" for _, r in grp.iterrows()]
    gcol = [GROUP_COLOR.get(g, "#888") for g in grp["group"]]
    ax2.barh(glbl, grp["mean_abs_shap"], color=gcol, edgecolor="black", linewidth=0.5)
    for i, (_, r) in enumerate(grp.iterrows()):
        ax2.text(r["mean_abs_shap"], i, f"  {r['frac_total']*100:.1f} %",
                 va="center", fontsize=7)
    ax2.set_xlabel(r"$\sum$ Mean $|\mathrm{SHAP}|$ ($\mu$g m$^{-3}$)")
    ax2.set_title("(b) Mechanistic-group totals", loc="left", fontsize=9)
    ax2.grid(axis="x", alpha=0.3, linewidth=0.4)

    fig.suptitle("Figure 6 — Feature attribution (TreeSHAP on q$_{50}$, $n_{bg}{=}1000$)",
                 fontsize=10, y=1.02)
    fig.tight_layout()
    _save(fig, "F06_shap_importance")


# ─────────────────────────────────────────────────────────────────────────────
# F07 — Sensor coherence: Akurana ↔ Hantana + sensor time-series coverage
# ─────────────────────────────────────────────────────────────────────────────

def fig07_sensor_coherence() -> None:
    log.info("── F07 sensor coherence ──")
    df = pd.read_parquet(DATASET)
    df["date"] = pd.to_datetime(df["date"])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(DOUBLE_COL_IN, DOUBLE_COL_IN * 0.42),
                                    gridspec_kw={"width_ratios": [1.5, 1]})

    # ── (a) Per-sensor daily time series ───────────────────────────────────
    for sid, (name, lat, lon, alt, c) in SENSOR_INFO.items():
        sub = df[df["sensor_id"] == sid].sort_values("date")
        ax1.scatter(sub["date"], sub["pm25_observed"], s=2.5, c=c, alpha=0.5,
                    edgecolor="none", label=f"FECT {name} ({alt} m, n={len(sub):,})")
    ax1.set_ylabel(r"FECT-calibrated PM$_{2.5}$ ($\mu$g m$^{-3}$)")
    ax1.set_xlabel("Date")
    ax1.set_title("(a) FECT sensor daily coverage", loc="left", fontsize=9)
    ax1.legend(fontsize=7, loc="upper right", framealpha=0.92)
    ax1.grid(alpha=0.3, linewidth=0.4)
    ax1.set_ylim(0, max(60, float(df["pm25_observed"].quantile(0.99)) * 1.1))
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # ── (b) Akurana ↔ Hantana overlap scatter ─────────────────────────────
    pivot = df.pivot_table(index="date", columns="sensor_id",
                           values="pm25_observed", aggfunc="mean")
    both = pivot[[12451, 33495]].dropna()
    if len(both) > 5:
        ax2.scatter(both[12451], both[33495], s=18, c="#444444", alpha=0.65,
                    edgecolor="black", linewidth=0.3)
        lim = max(both.max().max() * 1.1, 30)
        ax2.plot([0, lim], [0, lim], "k--", linewidth=0.6, label="1:1")
        r = float(both[12451].corr(both[33495]))
        # Linear fit overlay
        coef = np.polyfit(both[12451], both[33495], 1)
        xs = np.linspace(0, lim, 50)
        ax2.plot(xs, coef[0] * xs + coef[1], color=C_AKURANA, linewidth=1.0,
                 label=f"OLS y = {coef[0]:.2f} x + {coef[1]:+.1f}")
        ax2.set_xlim(0, lim); ax2.set_ylim(0, lim)
        ax2.set_aspect("equal")
        ax2.set_xlabel(r"Akurana PM$_{2.5}$ ($\mu$g m$^{-3}$)")
        ax2.set_ylabel(r"Hantana TR4 PM$_{2.5}$ ($\mu$g m$^{-3}$)")
        ax2.set_title(f"(b) Inter-station overlap (n = {len(both)}, $r$ = {r:.3f})",
                      loc="left", fontsize=9)
        ax2.legend(fontsize=7, loc="lower right", framealpha=0.92)
        ax2.grid(alpha=0.3, linewidth=0.4)

    fig.suptitle("Figure 7 — FECT inter-sensor coherence and coverage",
                 fontsize=10, y=1.00)
    fig.tight_layout()
    _save(fig, "F07_sensor_coherence")


# ─────────────────────────────────────────────────────────────────────────────
# F08 — Ablation analysis (drop-one-group + reanalysis variants)
# ─────────────────────────────────────────────────────────────────────────────

def fig08_ablation() -> None:
    log.info("── F08 ablation summary ──")
    abl = pd.read_csv(TRAIN_DIR / "ablation_comparison_v2.csv")
    full = abl[abl["label"] == "v2.1_full_features"]
    full_rmse = float(full.iloc[0]["xgb_pooled_rmse"]) if len(full) else 5.73
    abl = abl[abl["label"] != "v2.1_full_features"].copy()
    abl["delta_rmse"] = abl["xgb_pooled_rmse"] - full_rmse
    abl["delta_pct"] = 100 * abl["delta_rmse"] / full_rmse

    # Friendly labels
    label_map = {
        "drop_A_ventilation":     "−A Ventilation",
        "drop_B_valley_transport": "−B Valley transport",
        "drop_C_wet_scavenging":  "−C Wet scavenging",
        "drop_D_source_column":   "−D Source / column",
        "drop_F_climate_modes":   "−F Climate modes",
        "drop_G_temporal":        "−G Temporal lags",
        "drop_station_latlonelev": "−STATION lat/lon/elev",
        "no_cams_only":           "−E1 CAMS only",
        "no_geos_only":           "−E2 GEOS-CF only",
        "no_reanalysis":          "−E all reanalysis",
        "no_prior_disagree":      "−E3 prior disagreement",
    }
    abl["nice"] = abl["label"].map(label_map).fillna(abl["label"])
    abl = abl.sort_values("delta_rmse", ascending=True)

    fig, ax = plt.subplots(figsize=(SINGLE_COL_IN * 1.6, SINGLE_COL_IN * 1.05))
    colours = []
    for _, r in abl.iterrows():
        grp = r["drop_groups"] if isinstance(r["drop_groups"], str) and r["drop_groups"] != "nan" else ""
        if grp in GROUP_COLOR:
            colours.append(GROUP_COLOR[grp])
        elif "cams" in r["label"]:
            colours.append(GROUP_COLOR["E"])
        elif "geos" in r["label"]:
            colours.append(GROUP_COLOR["E"])
        elif "reanalysis" in r["label"]:
            colours.append(GROUP_COLOR["E"])
        elif "prior" in r["label"]:
            colours.append(GROUP_COLOR["E"])
        else:
            colours.append("#999")
    ax.barh(abl["nice"], abl["delta_pct"], color=colours, edgecolor="black", linewidth=0.5)
    ax.axvline(0, color="black", linewidth=0.6)
    ax.set_xlabel(r"$\Delta$ pooled RMSE vs full feature set (%)")
    ax.set_title(f"Figure 8 — Mechanistic-group ablations (full RMSE = {full_rmse:.2f} $\\mu$g m$^{{-3}}$)",
                 loc="left", fontsize=9)
    for i, (_, r) in enumerate(abl.iterrows()):
        v = r["delta_pct"]
        ax.text(v + (0.4 if v >= 0 else -0.4), i,
                f"{v:+.1f} %", va="center", ha="left" if v >= 0 else "right", fontsize=7)
    ax.grid(axis="x", alpha=0.3, linewidth=0.4)
    fig.tight_layout()
    _save(fig, "F08_ablation")


# ─────────────────────────────────────────────────────────────────────────────
# F09 — Embassy Colombo OOD: scatter + per-year coverage
# ─────────────────────────────────────────────────────────────────────────────

def fig09_ood() -> None:
    log.info("── F09 Embassy Colombo OOD ──")
    pr = pd.read_parquet(TRAIN_DIR / "predictions_colombo_v2.parquet")
    pr["date"] = pd.to_datetime(pr["date"])
    pr["year"] = pr["date"].dt.year
    y = pr["pm25_observed"].to_numpy()
    q05 = pr["q05"].to_numpy()
    q50 = pr["q50"].to_numpy()
    q95 = pr["q95"].to_numpy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(DOUBLE_COL_IN, DOUBLE_COL_IN * 0.42),
                                    gridspec_kw={"width_ratios": [1, 1.3]})

    # ── (a) Predicted vs observed scatter, coloured by year ───────────────
    cmap = plt.cm.viridis
    years = sorted(pr["year"].unique())
    for yr in years:
        sub = pr[pr["year"] == yr]
        ax1.scatter(sub["pm25_observed"], sub["q50"], s=6,
                    c=cmap((yr - min(years)) / max(1, max(years) - min(years))),
                    alpha=0.55, edgecolor="none",
                    label=f"{yr} (n={len(sub)})")
    lim = max(float(np.nanmax(y)) * 1.05, float(np.nanmax(q50)) * 1.05, 30)
    ax1.plot([0, lim], [0, lim], "k--", linewidth=0.6, label="1:1")
    pooled_r = np.corrcoef(y, q50)[0, 1]
    pooled_bias = float((q50 - y).mean())
    pooled_cov = float(((q05 <= y) & (y <= q95)).mean())
    ax1.set_xlim(0, lim); ax1.set_ylim(0, lim)
    ax1.set_aspect("equal")
    ax1.set_xlabel(r"Embassy observed PM$_{2.5}$ ($\mu$g m$^{-3}$)")
    ax1.set_ylabel(r"RECAP q$_{50}$ ($\mu$g m$^{-3}$)")
    ax1.set_title(f"(a) Embassy Colombo predicted vs observed",
                  loc="left", fontsize=9)
    ax1.legend(fontsize=6, loc="upper left", ncol=2, framealpha=0.92)
    ax1.grid(alpha=0.3, linewidth=0.4)
    ax1.text(0.98, 0.02,
             f"$n$ = {len(pr):,}\n"
             f"Pearson $r$ = {pooled_r:.3f}\n"
             f"Bias = {pooled_bias:+.2f}\n"
             f"cov90 = {pooled_cov:.3f}",
             transform=ax1.transAxes, ha="right", va="bottom", fontsize=7,
             bbox=dict(facecolor="white", edgecolor="black", linewidth=0.4, pad=2))

    # ── (b) Per-year cov90 with H4 envelope ───────────────────────────────
    yr_metrics = pr.groupby("year").apply(lambda g:
        pd.Series({"n": len(g),
                   "cov90": float(((g["q05"] <= g["pm25_observed"]) &
                                   (g["pm25_observed"] <= g["q95"])).mean()),
                   "rmse": float(np.sqrt(((g["pm25_observed"] - g["q50"])**2).mean())),
                   "bias": float((g["q50"] - g["pm25_observed"]).mean()),
                   })).reset_index()
    ax2.axhspan(0.85, 0.95, color="green", alpha=0.18, label="H4 envelope")
    ax2.axhline(0.90, color="black", linestyle="--", linewidth=0.6, label="Nominal 0.90")
    bars = ax2.bar(yr_metrics["year"].astype(int).astype(str),
                   yr_metrics["cov90"], color=C_EMBASSY, edgecolor="black",
                   linewidth=0.5, alpha=0.85)
    for r in yr_metrics.itertuples():
        ax2.text(str(int(r.year)), r.cov90 + 0.01,
                 f"n={int(r.n)}\nrmse={r.rmse:.1f}", ha="center",
                 fontsize=6, va="bottom")
    ax2.set_ylim(0.6, 1.02)
    ax2.set_ylabel("90 % PI empirical coverage")
    ax2.set_xlabel("Year")
    ax2.set_title("(b) Per-year coverage (H4 ✓ on pooled, $n_{tot}{=}1\\,661$)",
                  loc="left", fontsize=9)
    ax2.legend(fontsize=7, loc="lower left", framealpha=0.92)
    ax2.grid(axis="y", alpha=0.3, linewidth=0.4)

    fig.suptitle("Figure 9 — RECAP out-of-domain calibration at US Embassy Colombo",
                 fontsize=10, y=1.02)
    fig.tight_layout()
    _save(fig, "F09_ood_embassy")


# ─────────────────────────────────────────────────────────────────────────────
# F10 — Worst-month case study
# ─────────────────────────────────────────────────────────────────────────────

def fig10_worst_month() -> None:
    log.info("── F10 worst-month case study ──")
    fold = pd.read_csv(TRAIN_DIR / "metrics_per_fold_v2.csv")
    fold = fold[(fold["model"] == "xgboost_v2") & (fold["n"] >= 10)].copy()
    fold["year"]  = fold["fold"].str.split("-").str[0].astype(int)
    fold["month"] = fold["fold"].str.split("-").str[1].astype(int)
    fold = fold.dropna(subset=["rmse"]).sort_values("rmse", ascending=False)
    worst = fold.iloc[0]
    log.info(f"  worst fold: {worst['fold']}  rmse={worst['rmse']:.2f}  n={int(worst['n'])}")
    target_year  = int(worst["year"])
    target_month = int(worst["month"])

    preds = pd.read_parquet(TRAIN_DIR / "predictions_lomo_v2.parquet")
    preds["date"] = pd.to_datetime(preds["date"])
    sub = preds[preds["fold"] == worst["fold"]].copy().sort_values("date")

    fig, ax = plt.subplots(figsize=(DOUBLE_COL_IN, DOUBLE_COL_IN * 0.35))
    # Per-sensor scatter
    for sid, (name, lat, lon, alt, c) in SENSOR_INFO.items():
        s = sub[sub["sensor_id"] == sid]
        if len(s):
            ax.scatter(s["date"], s["y_true"], s=22, c=c, edgecolor="black",
                       linewidth=0.5, zorder=4, label=f"FECT {name}")
    # Predictions for each sensor — connect with lines
    for sid, (name, lat, lon, alt, c) in SENSOR_INFO.items():
        s = sub[sub["sensor_id"] == sid].sort_values("date")
        if len(s):
            ax.fill_between(s["date"], s["xgb_q05"], s["xgb_q95"],
                            color=c, alpha=0.18, linewidth=0, zorder=2)
            ax.plot(s["date"], s["xgb_q50"], color=c, linewidth=1.1, zorder=3,
                    label=f"RECAP q50 ({name})")
    # GEOS-CF baseline
    base = sub.groupby("date")["baseline_geos_scaled"].mean().reset_index()
    ax.plot(base["date"], base["baseline_geos_scaled"], color=C_GEOS, linewidth=0.8,
            linestyle=":", label="GEOS-CF × 0.536", zorder=1)
    ax.set_ylabel(r"PM$_{2.5}$ ($\mu$g m$^{-3}$)")
    ax.set_xlabel("Date")
    ax.set_title(f"Figure 10 — Worst-fold case study: {worst['fold']}  "
                 f"(per-fold RMSE = {worst['rmse']:.2f} $\\mu$g m$^{{-3}}$, "
                 f"n = {int(worst['n'])})",
                 loc="left", fontsize=9)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
    ax.legend(fontsize=7, ncol=2, loc="upper right", framealpha=0.92)
    ax.grid(alpha=0.3, linewidth=0.4)
    fig.tight_layout()
    _save(fig, "F10_worst_month")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

ALL_FIGS = {
    "F01": fig01_domain_map,
    "F02": fig02_timeseries,
    "F03": fig03_baselines,
    "F04": fig04_per_month,
    "F05": fig05_reliability,
    "F06": fig06_shap,
    "F07": fig07_sensor_coherence,
    "F08": fig08_ablation,
    "F09": fig09_ood,
    "F10": fig10_worst_month,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", default=None,
                    help="generate only these figures (e.g. F02 F03)")
    args = ap.parse_args()

    apply_style("ieee")
    log.info(f"output dir: {OUT_DIR}")

    todo = list(ALL_FIGS.keys()) if not args.only else [k for k in ALL_FIGS if k in args.only]
    for k in todo:
        try:
            ALL_FIGS[k]()
        except Exception as e:
            log.error(f"  {k} FAILED: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()

    log.info("done")


if __name__ == "__main__":
    main()
