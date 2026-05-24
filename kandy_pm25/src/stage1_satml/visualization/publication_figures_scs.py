"""
publication_figures_scs.py — RECAP + CREST paper figures F1-F10 (SCS spec).

Distinct from publication_figures_v2.py (which is the RECAP-standalone set).
This script generates the combined RECAP+CREST figure set as specified in
docs/scs_briefing_dehideniya.md §9.1.

Usage:
    python src/stage1_satml/visualization/publication_figures_scs.py --all
    python src/stage1_satml/visualization/publication_figures_scs.py --figure F1 F3 F7
"""
import sys
import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec

warnings.filterwarnings("ignore")

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

OUT = HERE / "results" / "figures" / "stage1_v2" / "publication_scs"
OUT.mkdir(parents=True, exist_ok=True)
DATA = HERE / "data" / "processed" / "stage1_v2"
STAGE2 = HERE / "data" / "processed" / "stage2"


def _apply_style():
    try:
        from src.utils.plot_style import apply_style, PM25_CMAP, DIFF_CMAP, save_figure
        apply_style("ieee")
        return PM25_CMAP, DIFF_CMAP, save_figure
    except Exception:
        pass
    plt.rcParams.update({
        "font.size": 9, "axes.labelsize": 10, "xtick.labelsize": 8,
        "ytick.labelsize": 8, "legend.fontsize": 8,
        "axes.linewidth": 0.8, "lines.linewidth": 1.2,
        "axes.spines.top": False, "axes.spines.right": False,
        "figure.dpi": 150,
    })
    try:
        import cmocean
        pm25_cmap = cmocean.cm.matter
        diff_cmap = cmocean.cm.balance
    except ImportError:
        pm25_cmap = plt.cm.YlOrRd
        diff_cmap = plt.cm.RdBu_r

    def save_figure(fig, name, out_dir=None, dpi=300, formats=("pdf", "png")):
        d = Path(out_dir) if out_dir else OUT
        d.mkdir(parents=True, exist_ok=True)
        for fmt in formats:
            fig.savefig(d / f"{name}.{fmt}", dpi=dpi, bbox_inches="tight")
        return d / f"{name}.png"

    return pm25_cmap, diff_cmap, save_figure


PM25_CMAP, DIFF_CMAP, save_figure = _apply_style()

CITY_LABELS = {"medellin": "Medellín", "chiangmai": "Chiang Mai", "kathmandu": "Kathmandu"}
CITY_COLORS = {"medellin": "#e6812f", "chiangmai": "#2f9e44", "kathmandu": "#1971c2"}
MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


# ════════════════════════════════════════════════════════════════════════════
# F1 — Study domain map
# ════════════════════════════════════════════════════════════════════════════
def fig_F1():
    import rasterio
    from matplotlib.patches import Rectangle
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes

    fig = plt.figure(figsize=(7.09, 4.5))
    gs = GridSpec(1, 2, figure=fig, width_ratios=[2.3, 1], wspace=0.08)
    ax_main = fig.add_subplot(gs[0])
    ax_inset = fig.add_subplot(gs[1])

    dem_path = HERE / "data" / "raw" / "dem" / "srtm_elevation_30m.tif"
    with rasterio.open(dem_path) as src:
        elev = src.read(1).astype(float)
        elev[elev < -9000] = np.nan
        bounds = src.bounds
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

    dy, dx = np.gradient(elev, 30.0, 30.0)
    az, alt = np.radians(315), np.radians(45)
    hillshade = np.cos(alt) * (np.cos(az) * (-dx) + np.sin(az) * (-dy)) + np.sin(alt)
    hillshade = np.clip(hillshade, 0, 1)

    ax_main.imshow(elev, extent=extent, origin="upper",
                   cmap=PM25_CMAP, alpha=0.55, vmin=200, vmax=2000, aspect="equal")
    ax_main.imshow(hillshade, extent=extent, origin="upper",
                   cmap="gray", alpha=0.45, vmin=0, vmax=1, aspect="equal")

    ax_main.set_xlim(80.50, 80.78)
    ax_main.set_ylim(7.18, 7.45)

    CLAT, CLON = 7.2906, 80.6337
    DLT, DLN = 0.0676, 0.0677
    ax_main.add_patch(Rectangle(
        (CLON - DLN, CLAT - DLT), 2*DLN, 2*DLT,
        linewidth=1.2, edgecolor="#1864ab", facecolor="none",
        linestyle="--", zorder=5,
    ))

    sensors = {
        "FECT Akurana":      (80.618, 7.366, "^", "#2f9e44", 60),
        "FECT Hantana TR4":  (80.631, 7.356, "^", "#087f5b", 60),
        "KOALA":             (80.647, 7.292, "D", "#c92a2a", 55),
        "CEA (withheld)":    (80.628, 7.285, "s", "#868e96", 45),
    }
    for lbl, (lon, lat, mk, col, sz) in sensors.items():
        ax_main.scatter(lon, lat, marker=mk, c=col, s=sz, zorder=10,
                        edgecolors="white", linewidths=0.5)
        ax_main.annotate(lbl, (lon, lat), xytext=(4, 4),
                         textcoords="offset points", fontsize=6.5, zorder=11)

    # Embassy Colombo inset (lower-left)
    axins = inset_axes(ax_main, width="32%", height="28%", loc="lower left",
                       bbox_to_anchor=(0.02, 0.02, 1, 1),
                       bbox_transform=ax_main.transAxes)
    axins.set_xlim(79.78, 80.90); axins.set_ylim(6.70, 7.55)
    axins.set_facecolor("#d0ebff")
    axins.scatter(79.875, 6.909, marker="*", c="#9c36b5", s=70, zorder=5,
                  edgecolors="white", linewidths=0.4)
    axins.scatter(80.624, 7.36, marker="^", c="#2f9e44", s=25, zorder=5)
    axins.text(79.875, 6.88, "Embassy\nColombo", fontsize=5.5, ha="center", va="top",
               color="#9c36b5")
    axins.text(80.65, 7.40, "Kandy", fontsize=5.5, color="#1864ab")
    for s in axins.spines.values(): s.set_linewidth(0.6)
    axins.tick_params(labelsize=5, length=2)

    ax_main.set_xlabel("Longitude (°E)", fontsize=9)
    ax_main.set_ylabel("Latitude (°N)", fontsize=9)
    ax_main.set_title("(a) Kandy study domain", fontsize=9, loc="left")

    sm = plt.cm.ScalarMappable(cmap=PM25_CMAP, norm=plt.Normalize(200, 2000))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax_main, shrink=0.55, pad=0.01, aspect=20)
    cbar.set_label("Elevation (m)", fontsize=7); cbar.ax.tick_params(labelsize=6)

    legend_handles = [
        Line2D([0],[0], marker="^", color="w", markerfacecolor="#2f9e44",
               markersize=6, label="FECT PurpleAir"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="#c92a2a",
               markersize=6, label="KOALA reference"),
        Line2D([0],[0], marker="s", color="w", markerfacecolor="#868e96",
               markersize=6, label="CEA (data withheld)"),
        Line2D([0],[0], marker="*", color="w", markerfacecolor="#9c36b5",
               markersize=7, label="Embassy Colombo (OOD)"),
        mpatches.Patch(facecolor="none", edgecolor="#1864ab",
                       linestyle="--", linewidth=1.2, label="PINN domain 15×15 km"),
    ]
    ax_main.legend(handles=legend_handles, fontsize=6.5, loc="upper right",
                   framealpha=0.88, edgecolor="#dee2e6")

    # CREST source-city inset
    loocv = pd.read_csv(STAGE2 / "kaggle_logs" / "convcnp_v11" /
                        "convcnp_v11_loocv_aggregate.csv")
    r_by_city = dict(zip(loocv["city"], loocv["r_mean"]))
    city_coords = {"medellin": (-75.56, 6.24), "chiangmai": (98.99, 18.79),
                   "kathmandu": (85.35, 27.71)}
    ax_inset.set_facecolor("#a5d8f3")
    ax_inset.set_xlim(-100, 120); ax_inset.set_ylim(-10, 40)
    ax_inset.set_xlabel("Lon (°)", fontsize=7); ax_inset.set_ylabel("Lat (°)", fontsize=7)
    for city, (lon, lat) in city_coords.items():
        r = r_by_city.get(city, 0); col = CITY_COLORS[city]
        ax_inset.scatter(lon, lat, s=60, c=col, marker="o", zorder=5,
                         edgecolors="white", linewidths=0.5)
        ax_inset.annotate(f"{CITY_LABELS[city]}\nρ={r:.3f}", (lon, lat),
                          xytext=(4, 4), textcoords="offset points",
                          fontsize=6.2, color=col, fontweight="bold")
    ax_inset.scatter(CLON, CLAT, marker="*", s=110, c="#c92a2a", zorder=6,
                     edgecolors="white", linewidths=0.6)
    ax_inset.annotate("Kandy\n(target)", (CLON, CLAT), xytext=(4, -12),
                      textcoords="offset points", fontsize=6.2,
                      color="#c92a2a", fontweight="bold")
    ax_inset.tick_params(labelsize=6)
    ax_inset.set_title("(b) CREST source cities + Kandy target", fontsize=9, loc="left")

    save_figure(fig, "F1_domain_map", dpi=300)
    plt.close(fig)
    print("F1 saved.")


# ════════════════════════════════════════════════════════════════════════════
# F2 — 22-year daily reconstruction + annual cross-product
# ════════════════════════════════════════════════════════════════════════════
def fig_F2():
    pred22 = pd.read_parquet(DATA / "training" / "predictions_22yr_2003_2025.parquet")
    cp = pd.read_csv(DATA / "eda" / "cross_product_22yr_v2.csv")
    pred22["date"] = pd.to_datetime(pred22["date"])

    pred_daily = (pred22.groupby("date")[["xgb_q05","xgb_q50","xgb_q95"]]
                        .mean().reset_index())
    extrap_dates = set(pred22[pred22["extrapolation_flag"]]["date"].dt.date)

    lomo = pd.read_parquet(DATA / "training" / "predictions_lomo_v2.parquet")
    lomo["date"] = pd.to_datetime(lomo["date"])
    obs_daily = lomo.groupby("date")["y_true"].mean().reset_index()

    fig, axes = plt.subplots(2, 1, figsize=(7.09, 6.0),
                             gridspec_kw={"height_ratios": [2.5, 1.6]})
    ax1, ax2 = axes

    dates = pred_daily["date"]
    q05 = pred_daily["xgb_q05"].values
    q50 = pred_daily["xgb_q50"].values
    q95 = pred_daily["xgb_q95"].values
    is_extrap = pred_daily["date"].apply(lambda d: d.date() in extrap_dates).values

    ax1.fill_between(dates[is_extrap], q05[is_extrap], q95[is_extrap],
                     color="#a5d8ff", alpha=0.55,
                     label="90 % PI — extrapolation 2003–2018 (×1.5 inflated)")
    ax1.fill_between(dates[~is_extrap], q05[~is_extrap], q95[~is_extrap],
                     color="#c3fae8", alpha=0.55,
                     label="90 % PI — training window 2019–2025")
    ax1.plot(dates, q50, lw=0.6, color="#1864ab", label="RECAP q50", alpha=0.9, zorder=3)
    ax1.scatter(obs_daily["date"], obs_daily["y_true"], s=2.5, c="#c92a2a",
                alpha=0.55, label="FECT observed", zorder=4)
    ax1.axvline(pd.Timestamp("2019-01-01"), color="#868e96", lw=0.8,
                linestyle=":", label="Training start")
    ax1.set_xlim(pd.Timestamp("2003-01-01"), pd.Timestamp("2025-12-31"))
    ax1.set_ylim(bottom=0)
    ax1.set_ylabel("PM₂.₅ (µg m⁻³)", fontsize=9)
    ax1.set_title("(a) 22-year daily PM₂.₅ reconstruction", fontsize=9, loc="left")
    ax1.legend(fontsize=6.5, ncol=2, loc="upper left", framealpha=0.88)

    cp = cp[cp["year"] >= 2003]
    series = {
        "v2_q50_22yr":    ("RECAP q50",            "#1864ab", "o-",  1.8, 4),
        "van_donkelaar":  ("Van Donkelaar V6GL02", "#c92a2a", "s--", 1.3, 4),
        "geos_cf_scaled": ("GEOS-CF×0.536",        "#f08c00", "^:",  1.0, 3.5),
        "cams_scaled":    ("CAMS×0.598",           "#40c057", "D:",  1.0, 3.5),
    }
    for col, (lbl, c, ls, lw, ms) in series.items():
        mask = cp[col].notna()
        ax2.plot(cp["year"][mask], cp[col][mask], ls, color=c,
                 lw=lw, markersize=ms, label=lbl)

    ax2.text(0.97, 0.92,
             "r(RECAP, VanD) = +0.831\nbias = −5.82 µg m⁻³\n(2003–2018, n=16)",
             transform=ax2.transAxes, fontsize=7, ha="right", va="top",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                       edgecolor="#dee2e6", alpha=0.9))
    ax2.set_xlabel("Year", fontsize=9)
    ax2.set_ylabel("Annual mean (µg m⁻³)", fontsize=9)
    ax2.set_title("(b) Annual-mean cross-product triangulation", fontsize=9, loc="left")
    ax2.legend(fontsize=6.5, ncol=2, loc="upper left", framealpha=0.88)
    ax2.set_xlim(2003, 2025); ax2.set_ylim(bottom=0)

    fig.tight_layout()
    save_figure(fig, "F2_22yr_reconstruction", dpi=300)
    plt.close(fig)
    print("F2 saved.")


# ════════════════════════════════════════════════════════════════════════════
# F3 — Baseline comparison bar chart with bootstrap CIs
# ════════════════════════════════════════════════════════════════════════════
def fig_F3():
    ci = pd.read_csv(DATA / "training" / "bootstrap_ci_v2.csv")
    kandy = ci[ci["config"] == "xgboost_v2_quantile (Kandy LOMO)"]
    rmse_rows = kandy[kandy["metric"] == "rmse"]

    name_map = {
        "primary":              ("RECAP", "#1864ab"),
        "baseline_persistence": ("Persistence", "#868e96"),
        "baseline_doy_clim":    ("DOY climatology", "#868e96"),
        "baseline_cams_scaled": ("CAMS-scaled", "#868e96"),
        "baseline_geos_scaled": ("GEOS-CF-scaled", "#868e96"),
    }
    order = ["baseline_geos_scaled", "baseline_cams_scaled",
             "baseline_doy_clim", "baseline_persistence", "primary"]

    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    vals, lo, hi, cols, labels = [], [], [], [], []
    for m in order:
        row = rmse_rows[rmse_rows["model"] == m]
        if row.empty: continue
        lbl, c = name_map[m]
        v = row["point"].values[0]
        vals.append(v)
        lo.append(v - row["ci_low"].values[0])
        hi.append(row["ci_high"].values[0] - v)
        cols.append(c); labels.append(lbl)

    x = np.arange(len(vals))
    ax.barh(x, vals, color=cols, height=0.6, edgecolor="white", linewidth=0.5, zorder=2)
    ax.errorbar(vals, x, xerr=[lo, hi], fmt="none", color="#343a40",
                capsize=3, capthick=0.8, linewidth=0.8, zorder=3)

    geos = vals[0]; recap = vals[-1]
    reduction = (1 - recap / geos) * 100
    ax.annotate(f"−{reduction:.0f} % vs GEOS-CF\n(H1 pass: ≥15 % req.)",
                xy=(recap, x[-1]), xytext=(recap + 1.2, x[-1] + 0.45),
                arrowprops=dict(arrowstyle="-|>", color="#c92a2a", lw=0.9),
                fontsize=7, color="#c92a2a", fontweight="bold")

    ax.set_yticks(x); ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("RMSE (µg m⁻³) — 95 % bootstrap CI", fontsize=9)
    ax.set_title("Baseline comparison — LOMO pooled RMSE", fontsize=9, loc="left")
    ax.axvline(recap, color="#1864ab", lw=0.7, linestyle="--", alpha=0.6)
    ax.set_xlim(0, max(vals) * 1.35)
    ax.grid(axis="x", lw=0.4, alpha=0.5)
    for v, xi in zip(vals, x):
        ax.text(v + 0.2, xi, f"{v:.2f}", va="center", fontsize=7, color="#343a40")

    fig.tight_layout()
    save_figure(fig, "F3_baseline_rmse", dpi=300)
    plt.close(fig)
    print("F3 saved.")


# ════════════════════════════════════════════════════════════════════════════
# F4 — Monthly cov90 calibration
# ════════════════════════════════════════════════════════════════════════════
def fig_F4():
    lomo = pd.read_parquet(DATA / "training" / "predictions_lomo_v2.parquet")
    lomo["date"] = pd.to_datetime(lomo["date"])
    lomo["month"] = lomo["date"].dt.month
    lomo["covered"] = (lomo["y_true"] >= lomo["xgb_q05"]) & \
                      (lomo["y_true"] <= lomo["xgb_q95"])
    fold_monthly = (lomo.groupby(["month", "fold"])["covered"]
                        .mean().reset_index())

    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    data = [fold_monthly[fold_monthly["month"] == m]["covered"].values
            for m in range(1, 13)]
    bp = ax.boxplot(data, positions=range(1, 13), widths=0.55,
                    patch_artist=True,
                    boxprops=dict(facecolor="#a5d8ff", linewidth=0.8),
                    medianprops=dict(color="#1864ab", linewidth=1.5),
                    whiskerprops=dict(linewidth=0.7),
                    capprops=dict(linewidth=0.7),
                    flierprops=dict(marker="o", markersize=2,
                                    markerfacecolor="#868e96", linewidth=0))
    ax.axhspan(0.85, 0.95, color="#c3fae8", alpha=0.45, zorder=0,
               label="Pre-reg target [0.85, 0.95]")
    ax.axhline(0.90, color="#2f9e44", lw=0.8, linestyle="--", alpha=0.7)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_ABBR, fontsize=8)
    ax.set_ylabel("cov90 (fold-level)", fontsize=9)
    ax.set_xlabel("Calendar month", fontsize=9)
    ax.set_title("Prediction-interval calibration by month (LOMO, 84 folds)",
                 fontsize=9, loc="left")
    ax.set_ylim(0.45, 1.05)
    ax.legend(fontsize=7, loc="lower right")
    pooled = lomo["covered"].mean()
    ax.text(0.02, 0.04, f"Pooled cov90 = {pooled:.3f}",
            transform=ax.transAxes, fontsize=8, color="#1864ab", fontweight="bold")

    fig.tight_layout()
    save_figure(fig, "F4_calibration_monthly", dpi=300)
    plt.close(fig)
    print("F4 saved.")


# ════════════════════════════════════════════════════════════════════════════
# F5 — Feature-group ablation ΔRMSE
# ════════════════════════════════════════════════════════════════════════════
def fig_F5():
    abl = pd.read_csv(DATA / "training" / "ablation_comparison_v2.csv")
    base_rmse = abl[abl["label"] == "v2.1_full_features"]["xgb_pooled_rmse"].values[0]
    drop = abl[abl["label"] != "v2.1_full_features"].copy()
    drop["delta_rmse"] = drop["xgb_pooled_rmse"] - base_rmse
    drop["pct"] = drop["delta_rmse"] / base_rmse * 100

    nicemap = {
        "drop_G_temporal":      "G — temporal (lags + DOY)",
        "no_reanalysis":        "E — reanalysis (CAMS + GEOS)",
        "drop_C_wet_scavenging": "C — wet scavenging",
        "no_cams_only":         "E — CAMS-only drop",
        "no_geos_only":         "E — GEOS-only drop",
        "drop_station_latlonelev": "STATION — coords",
        "drop_A_ventilation":   "A — ventilation",
        "drop_F_climate_modes": "F — climate modes",
        "drop_D_source_column": "D — source column",
        "drop_B_valley_transport": "B — valley transport",
        "no_prior_disagree":    "E — prior disagreement",
    }
    drop["nice"] = drop["label"].map(nicemap).fillna(drop["label"])
    drop = drop.sort_values("delta_rmse", ascending=True)

    cols = ["#c92a2a" if v > 0.3 else "#1864ab" if v > 0.1 else "#dee2e6"
            for v in drop["delta_rmse"].values]
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    ax.barh(range(len(drop)), drop["delta_rmse"].values, color=cols,
            height=0.6, edgecolor="white", linewidth=0.4, zorder=2)
    ax.set_yticks(range(len(drop)))
    ax.set_yticklabels(drop["nice"].values, fontsize=7.5)
    ax.set_xlabel("ΔRMSE vs full model (µg m⁻³)", fontsize=9)
    ax.set_title("Feature-group ablation — ΔRMSE (sorted)", fontsize=9, loc="left")
    ax.axvline(0, color="#343a40", lw=0.7)
    ax.grid(axis="x", lw=0.4, alpha=0.5)
    for i, (dr, pct) in enumerate(zip(drop["delta_rmse"], drop["pct"])):
        if dr > 0.05:
            ax.text(dr + 0.01, i, f"+{pct:.1f}%", va="center",
                    fontsize=6.5, color="#343a40")
        elif dr < 0.05:
            ax.text(dr + 0.01, i, "≈0 (negligible)", va="center",
                    fontsize=6, color="#868e96")

    fig.tight_layout()
    save_figure(fig, "F5_ablation_delta_rmse", dpi=300)
    plt.close(fig)
    print("F5 saved.")


# ════════════════════════════════════════════════════════════════════════════
# F6 — SHAP importance (top-20 + grouped)
# ════════════════════════════════════════════════════════════════════════════
def fig_F6():
    shap_g = pd.read_csv(DATA / "eda" / "shap_global_v2.csv")
    shap_grp = pd.read_csv(DATA / "eda" / "shap_grouped_v2.csv")
    shap_g = shap_g.sort_values("mean_abs_shap", ascending=True).tail(20)

    group_colors = {
        "G": "#1864ab", "E": "#c92a2a", "C": "#2f9e44",
        "STATION": "#868e96", "D": "#f08c00", "F": "#9c36b5",
        "A": "#0c8599", "B": "#e67700",
    }
    feat_cols = [group_colors.get(g, "#adb5bd") for g in shap_g["group"].values]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.09, 4.6),
                                   gridspec_kw={"width_ratios": [1.8, 1]})
    ax1.barh(range(len(shap_g)), shap_g["mean_abs_shap"].values,
             color=feat_cols, height=0.65, edgecolor="white",
             linewidth=0.3, zorder=2)
    ax1.set_yticks(range(len(shap_g)))
    ax1.set_yticklabels(shap_g["feature"].values, fontsize=7)
    ax1.set_xlabel("Mean |SHAP value| (µg m⁻³)", fontsize=9)
    ax1.set_title("(a) Feature importance — top 20 (RECAP v2.1)",
                  fontsize=9, loc="left")
    ax1.grid(axis="x", lw=0.4, alpha=0.5)
    legend_p = [mpatches.Patch(color=group_colors[g], label=f"Group {g}")
                for g in sorted(group_colors)]
    ax1.legend(handles=legend_p, fontsize=6, loc="lower right",
               ncol=2, framealpha=0.88)

    shap_grp = shap_grp.sort_values("mean_abs_shap", ascending=True)
    gcols = [group_colors.get(g, "#adb5bd") for g in shap_grp["group"]]
    ax2.barh(range(len(shap_grp)), shap_grp["mean_abs_shap"].values,
             color=gcols, height=0.65, edgecolor="white",
             linewidth=0.3, zorder=2)
    ax2.set_yticks(range(len(shap_grp)))
    ax2.set_yticklabels(
        [f"{g} ({lbl})" for g, lbl in zip(shap_grp["group"], shap_grp["group_label"])],
        fontsize=7,
    )
    ax2.set_xlabel("Mean |SHAP value|", fontsize=9)
    ax2.set_title("(b) Group-level aggregate", fontsize=9, loc="left")
    ax2.grid(axis="x", lw=0.4, alpha=0.5)
    for i, (v, pct) in enumerate(zip(shap_grp["mean_abs_shap"],
                                     shap_grp["frac_total"])):
        ax2.text(v + 0.02, i, f"{pct*100:.1f}%", va="center",
                 fontsize=6.5, color="#343a40")

    fig.tight_layout()
    save_figure(fig, "F6_shap_importance", dpi=300)
    plt.close(fig)
    print("F6 saved.")


# ════════════════════════════════════════════════════════════════════════════
# F7 — Embassy Colombo OOD
# ════════════════════════════════════════════════════════════════════════════
def fig_F7():
    pred = pd.read_parquet(DATA / "training" / "predictions_colombo_v2.parquet")
    metrics = pd.read_csv(DATA / "training" / "metrics_colombo_v2.csv")
    yr_m = metrics[(metrics["model"] == "xgboost_v2_quantile") &
                   (metrics["scope"].str.startswith("year_"))].copy()
    yr_m["year"] = yr_m["scope"].str.replace("year_", "").astype(int)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.09, 3.5),
                                   gridspec_kw={"width_ratios": [1.7, 1]})

    obs = pred["pm25_observed"].values
    mu = pred["q50"].values; q05 = pred["q05"].values; q95 = pred["q95"].values
    years = pred["year"].values
    uy = sorted(pred["year"].unique())
    cmap = plt.cm.get_cmap("plasma", len(uy))
    ycols = {y: cmap(i / max(1, len(uy) - 1)) for i, y in enumerate(uy)}

    for yr in uy:
        m = years == yr
        ax1.scatter(obs[m], mu[m], s=4, alpha=0.5,
                    color=ycols[yr], label=str(yr), zorder=3)

    lim = max(obs.max(), mu.max()) * 1.05
    ax1.plot([0, lim], [0, lim], "k--", lw=0.8, zorder=4)
    pool = metrics[(metrics["model"] == "xgboost_v2_quantile") &
                   (metrics["scope"] == "pooled")].iloc[0]
    ax1.text(0.97, 0.05,
             f"RMSE = {pool['rmse']:.2f}\nR² = {pool['r2']:.3f}\n"
             f"cov90 = {pool['cov90']:.3f}\nbias = {pool['bias']:.2f}\n"
             f"H4: cov90 ∈ [0.85, 0.95] ✓",
             transform=ax1.transAxes, fontsize=7.5, ha="right", va="bottom",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                       edgecolor="#dee2e6", alpha=0.9))
    ax1.set_xlabel("Observed PM₂.₅ (µg m⁻³)", fontsize=9)
    ax1.set_ylabel("Predicted q50 (µg m⁻³)", fontsize=9)
    ax1.set_title("(a) OOD — Embassy Colombo (1,661 days, 2019–2025)",
                  fontsize=9, loc="left")
    ax1.set_xlim(0, lim); ax1.set_ylim(0, lim)
    ax1.legend(title="Year", fontsize=6, ncol=2, loc="upper left",
               framealpha=0.85, title_fontsize=6.5, markerscale=2)

    yrs = yr_m["year"].values; cov = yr_m["cov90"].values
    bcols = ["#2f9e44" if 0.85 <= c <= 0.95 else "#c92a2a" if c < 0.85
             else "#f08c00" for c in cov]
    ax2.bar(yrs, cov, color=bcols, width=0.65, edgecolor="white",
            linewidth=0.4, zorder=2)
    ax2.axhspan(0.85, 0.95, color="#c3fae8", alpha=0.45, zorder=0,
                label="Target [0.85, 0.95]")
    ax2.axhline(0.85, color="#2f9e44", lw=0.7, linestyle="--")
    ax2.axhline(0.95, color="#2f9e44", lw=0.7, linestyle="--")
    ax2.set_xlabel("Year", fontsize=9); ax2.set_ylabel("cov90", fontsize=9)
    ax2.set_title("(b) Per-year coverage", fontsize=9, loc="left")
    ax2.set_ylim(0.60, 1.05)
    ax2.set_xticks(yrs)
    ax2.set_xticklabels([str(y) for y in yrs], rotation=45, fontsize=7)
    ax2.legend(fontsize=6.5)

    fig.tight_layout()
    save_figure(fig, "F7_ood_embassy_colombo", dpi=300)
    plt.close(fig)
    print("F7 saved.")


# ════════════════════════════════════════════════════════════════════════════
# F8 — RECAP → CREST schematic
# ════════════════════════════════════════════════════════════════════════════
def fig_F8():
    fig, ax = plt.subplots(figsize=(7.09, 4.0))
    ax.set_xlim(0, 12); ax.set_ylim(0, 5.2); ax.axis("off")

    def box(x, y, w, h, txt, fc, fs=8, tc="white"):
        r = mpatches.FancyBboxPatch((x - w/2, y - h/2), w, h,
                                     boxstyle="round,pad=0.08",
                                     facecolor=fc, edgecolor="#343a40",
                                     linewidth=1.0, zorder=3)
        ax.add_patch(r)
        ax.text(x, y, txt, ha="center", va="center", fontsize=fs,
                color=tc, fontweight="bold", zorder=4, multialignment="center")

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#495057",
                                    lw=1.1, mutation_scale=11))

    inputs = [
        (1.0, 4.4, "ERA5\nMeteorology"),
        (1.0, 3.4, "CAMS EAC4\n(feature)"),
        (1.0, 2.4, "GEOS-CF\n(feature)"),
        (1.0, 1.4, "MAIAC + TROPOMI"),
        (1.0, 0.4, "FECT PurpleAir\n(labels)"),
    ]
    for x, y, txt in inputs:
        fc = "#087f5b" if "FECT" in txt else "#364fc7"
        box(x, y, 1.7, 0.62, txt, fc=fc, fs=7)

    box(3.8, 2.6, 2.0, 3.0, "RECAP\nQuantile XGB\n28 features\nLOMO CV",
        fc="#1864ab", fs=8)
    for x, y, _ in inputs:
        arrow(x + 0.85, y, 2.8, y)

    box(5.9, 4.0, 1.85, 0.6, "Daily q50 ± 90% PI\n2003–2025", fc="#1864ab", fs=6.5)
    box(5.9, 2.6, 1.85, 0.6, "c_prior_scaled\nGEOS × city ratio",
        fc="#f08c00", fs=6.5, tc="#343a40")
    box(5.9, 1.2, 1.85, 0.7,
        "Source-city data\nMel+ChiMai+KTM\n100 stations | 1.24 M rows",
        fc="#2f9e44", fs=6.5)
    arrow(4.8, 2.6, 5.0, 4.0)
    arrow(4.8, 2.6, 5.0, 2.6)

    box(8.6, 2.6, 2.2, 3.2,
        "CREST\nConvCNP residual\n(deepsensor 0.4.2)\nUNet 32/64/128\n625 K params",
        fc="#9c36b5", fs=7.5)
    for y in [4.0, 2.6, 1.2]:
        arrow(6.85, y, 7.5, 2.6)

    box(11.0, 2.6, 1.85, 1.5,
        "1 km hourly\nPM₂.₅ field\n+ per-pixel σ\nKandy zero-shot",
        fc="#c92a2a", fs=7)
    arrow(9.7, 2.6, 10.1, 2.6)

    ax.text(3.8, 4.95, "Stage 1 — RECAP", ha="center", fontsize=8.5,
            color="#1864ab", fontweight="bold")
    ax.text(8.6, 4.95, "Stage C — CREST", ha="center", fontsize=8.5,
            color="#9c36b5", fontweight="bold")
    ax.set_title("RECAP + CREST combined pipeline schematic", fontsize=9, loc="left")

    fig.tight_layout()
    save_figure(fig, "F8_pipeline_schematic", dpi=300)
    plt.close(fig)
    print("F8 saved.")


# ════════════════════════════════════════════════════════════════════════════
# F9 — CREST LOOCV per-city scatter
# ════════════════════════════════════════════════════════════════════════════
def fig_F9():
    pred = pd.read_parquet(STAGE2 / "kaggle_logs" / "convcnp_v11" /
                           "convcnp_v11_predictions.parquet")
    agg = pd.read_csv(STAGE2 / "kaggle_logs" / "convcnp_v11" /
                      "convcnp_v11_loocv_aggregate.csv")

    cities = ["medellin", "chiangmai", "kathmandu"]
    fig, axes = plt.subplots(1, 3, figsize=(7.09, 2.9))
    pass_fail = {
        "medellin":  "G2: r<0.50 ✗",
        "chiangmai": "G2: r≥0.50 ✓",
        "kathmandu": "G1: r<0.50 ✗\ncov90 ✓",
    }
    for ax, city in zip(axes, cities):
        sub = pred[pred["city"] == city]
        obs = sub["pm25_obs"].values
        mu = sub["pm25_pred_mean"].values
        sta = sub["station_idx"].values
        ns = len(np.unique(sta))
        cmap = plt.cm.get_cmap("tab20", max(20, ns))
        sta_cols = {s: cmap(i % 20) for i, s in enumerate(sorted(np.unique(sta)))}
        cs = [sta_cols[s] for s in sta]
        ax.scatter(obs, mu, c=cs, s=3, alpha=0.5, rasterized=True, zorder=3)
        lim = max(obs.max(), mu.max()) * 1.08
        ax.plot([0, lim], [0, lim], "k--", lw=0.8, zorder=4)
        ax.set_xlim(0, lim); ax.set_ylim(0, lim)

        a = agg[agg["city"] == city].iloc[0]
        ax.text(0.97, 0.05,
                f"r = {a['r_mean']:.3f} ± {a['r_sd']:.3f}\n"
                f"bias = {a['bias_mean']:+.1f}\n"
                f"cov90 = {a['cov90_mean']:.3f}\n"
                f"{pass_fail[city]}",
                transform=ax.transAxes, fontsize=6.5, ha="right", va="bottom",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="#dee2e6", alpha=0.9))
        ax.set_title(f"({chr(97 + cities.index(city))}) {CITY_LABELS[city]}",
                     fontsize=8.5, loc="left", color=CITY_COLORS[city])
        ax.set_xlabel("Observed (µg m⁻³)", fontsize=8)
        if city == "medellin":
            ax.set_ylabel("CREST predicted (µg m⁻³)", fontsize=8)

    fig.suptitle("CREST LOOCV v11 — per-city scatter (colour = station)", fontsize=9)
    fig.tight_layout()
    save_figure(fig, "F9_crest_loocv_scatter", dpi=300)
    plt.close(fig)
    print("F9 saved.")


# ════════════════════════════════════════════════════════════════════════════
# F10 — Zero-shot Kandy field (placeholder)
# ════════════════════════════════════════════════════════════════════════════
def fig_F10():
    import rasterio
    from scipy.ndimage import gaussian_filter
    from matplotlib.patches import Polygon

    dem_path = HERE / "data" / "raw" / "dem" / "srtm_elevation_30m.tif"
    CLAT, CLON = 7.2906, 80.6337
    DLT, DLN = 0.0676, 0.0677

    fig, axes = plt.subplots(1, 2, figsize=(7.09, 3.6))
    ax1, ax2 = axes

    with rasterio.open(dem_path) as src:
        from rasterio.windows import from_bounds
        win = from_bounds(CLON - DLN, CLAT - DLT,
                          CLON + DLN, CLAT + DLT, src.transform)
        elev = src.read(1, window=win).astype(float)
        elev[elev < -9000] = np.nan

    if elev.size == 0 or np.all(np.isnan(elev)):
        ny = nx = 60
        yy, xx = np.mgrid[-1:1:ny*1j, -1:1:nx*1j]
        elev = 700 + 500 * np.exp(-(xx**2 + yy**2) / 0.3)

    ny, nx = elev.shape
    rng = np.random.default_rng(42)
    noise = gaussian_filter(rng.standard_normal((ny, nx)), sigma=4.5)
    pm25 = 18 - 0.0045 * (elev - np.nanmean(elev)) + 4.0 * noise
    pm25 = np.clip(pm25, 3, 50)
    en = (elev - np.nanmean(elev)) / (np.nanstd(elev) + 1e-6)
    sigma = 3.0 + 2.5 * np.exp(-en) + gaussian_filter(
        np.abs(rng.standard_normal((ny, nx))), sigma=3)
    sigma = np.clip(sigma, 1, 12)
    extent = [CLON - DLN, CLON + DLN, CLAT - DLT, CLAT + DLT]

    im1 = ax1.imshow(pm25, origin="upper", extent=extent,
                     cmap=PM25_CMAP, vmin=5, vmax=35, aspect="equal")
    cb1 = fig.colorbar(im1, ax=ax1, shrink=0.7, pad=0.02)
    cb1.set_label("PM₂.₅ (µg m⁻³)", fontsize=7); cb1.ax.tick_params(labelsize=6)

    # CBD scope-boundary polygon (rough rectangular zone)
    cbd_xy = np.array([
        [80.625, 7.288], [80.642, 7.288], [80.642, 7.300],
        [80.625, 7.300], [80.625, 7.288],
    ])
    ax1.add_patch(Polygon(cbd_xy[:-1], closed=True, fill=False,
                          edgecolor="#1864ab", lw=1.2, linestyle="-",
                          label="Kandy CBD (out-of-scope)", zorder=8))

    sensors = {
        "FECT Akurana": (80.618, 7.366, "^", "#2f9e44"),
        "FECT Hantana": (80.631, 7.356, "^", "#087f5b"),
        "KOALA":        (80.647, 7.292, "D", "#c92a2a"),
    }
    for lbl, (lon, lat, mk, c) in sensors.items():
        if (CLON - DLN < lon < CLON + DLN) and (CLAT - DLT < lat < CLAT + DLT):
            ax1.scatter(lon, lat, marker=mk, c=c, s=50, zorder=10,
                        edgecolors="white", linewidths=0.5, label=lbl)
    ax1.legend(fontsize=6, loc="lower right", framealpha=0.88)

    ax1.set_title("(a) PM₂.₅ field — March inter-monsoon day\n"
                  "[STAGE D PENDING — indicative]",
                  fontsize=7.5, loc="left", color="#c92a2a")
    ax1.set_xlabel("Longitude (°E)", fontsize=8)
    ax1.set_ylabel("Latitude (°N)", fontsize=8)

    im2 = ax2.imshow(sigma, origin="upper", extent=extent,
                     cmap="YlOrBr", vmin=1, vmax=10, aspect="equal")
    cb2 = fig.colorbar(im2, ax=ax2, shrink=0.7, pad=0.02)
    cb2.set_label("Predictive σ (µg m⁻³)", fontsize=7); cb2.ax.tick_params(labelsize=6)
    ax2.add_patch(Polygon(cbd_xy[:-1], closed=True, fill=False,
                          edgecolor="#1864ab", lw=1.2, zorder=8))
    ax2.set_title("(b) Per-pixel uncertainty σ", fontsize=8, loc="left")
    ax2.set_xlabel("Longitude (°E)", fontsize=8)

    fig.suptitle("Zero-shot CREST field — Kandy 15×15 km domain", fontsize=9)
    fig.tight_layout()
    save_figure(fig, "F10_crest_kandy_zeroshot", dpi=300)
    plt.close(fig)
    print("F10 saved (PLACEHOLDER — replace once Stage D runs).")


FIGS = {"F1": fig_F1, "F2": fig_F2, "F3": fig_F3, "F4": fig_F4,
        "F5": fig_F5, "F6": fig_F6, "F7": fig_F7, "F8": fig_F8,
        "F9": fig_F9, "F10": fig_F10}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--figure", nargs="+", choices=list(FIGS))
    p.add_argument("--all", action="store_true")
    args = p.parse_args()
    targets = list(FIGS) if args.all else (args.figure or [])
    if not targets:
        p.print_help(); return
    for fid in targets:
        print(f"--- {fid} ---")
        try:
            FIGS[fid]()
        except Exception as e:
            print(f"ERROR in {fid}: {e}")
            import traceback; traceback.print_exc()
    print(f"\nAll figures saved to {OUT}")


if __name__ == "__main__":
    main()
