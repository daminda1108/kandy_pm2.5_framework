"""
eda_stage1.py — Stage 1 EDA: 11 publication-quality plots for the Kandy PM2.5 thesis.

Plots:
  4a. Label distribution (histogram + KDE + Q-Q + log-normal fit)
  4b. Missingness heatmap (years × features)
  4c. Seasonal PM2.5 boxplots with KOALA reference
  4d. Annual PM2.5 trend with COVID/La Niña markers
  4e. AOD–PM2.5 scatter by season (4-panel)
  4f. Feature correlation heatmap (|r| > 0.15)
  4g. ACF of PM2.5 (lags 0–30)
  4h. BLH vs PM2.5 (two-panel scatter)
  4i. CAMS raw vs MERRA-2 vs KOALA (2019 only)
  4j. AOD missingness by season
  4k. SHAP summary bar chart (top 20 features, colour by group)

Usage:
  python src/stage1_satml/visualization/eda_stage1.py
"""

import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import linkage, leaves_list
from statsmodels.graphics.tsaplots import plot_acf

warnings.filterwarnings("ignore")

# ── Path setup ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(ROOT))

from src.utils.plot_style import apply_style, PM25_CMAP, save_figure

apply_style("ieee")

# ── Paths ────────────────────────────────────────────────────────────────────
MERGED_DIR  = ROOT / "data" / "processed" / "merged"
TABLES_DIR  = ROOT / "results" / "tables"
MODELS_DIR  = ROOT / "results" / "models"
MERRA2_PATH = ROOT / "data" / "raw" / "merra2" / "merra2_pm25_daily.csv"
OUT_DIR     = ROOT / "results" / "eda" / "stage1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── WHO / Sri Lanka standards ────────────────────────────────────────────────
WHO_ANNUAL   = 15.0   # µg/m³
WHO_24H      = 25.0
SL_ANNUAL    = 25.0
SL_24H       = 50.0

# ── KOALA reference — Senarathna et al. 2024, CJS 53(2):197-206 ─────────────
# DOI: 10.4038/cjs.v53i2.8403. Instrument: KOALA (Plantower PMS1003) vs BAM, NIFS Kandy.
# Previous anchor (Priyankara 2021): 34.48 µg/m³ — identified as ≈ March peak, not annual.
KOALA_ANNUAL = 24.5225   # µg/m³ — true 2019 annual mean (average of 12 monthly means)
KOALA_MARCH  = 34.87     # µg/m³ — March (first inter-monsoon peak; highest month)
# Monthly means used for correction (12 independent ratios, no single KOALA_RATIO):
KOALA_MONTHLY = {
    1: 26.13,  2: 26.92,  3: 34.87,  4: 33.50,
    5: 28.04,  6: 19.64,  7: 22.57,  8: 20.07,
    9: 20.89, 10: 21.01, 11: 22.87, 12: 17.76,
}  # µg/m³

# ── Season helper ────────────────────────────────────────────────────────────
SEASON_MAP = {12: "DJF", 1: "DJF", 2: "DJF",
              3:  "MAM", 4: "MAM", 5: "MAM",
              6:  "JJA", 7: "JJA", 8: "JJA",
              9:  "SON", 10: "SON", 11: "SON"}
SEASON_COLOURS = {"DJF": "#2166AC", "MAM": "#4DAC26", "JJA": "#D73027", "SON": "#F1A340"}


# ─────────────────────────────────────────────────────────────────────────────
# Load dataset
# ─────────────────────────────────────────────────────────────────────────────
print("Loading dataset …")
df = pd.read_parquet(MERGED_DIR / "dataset_daily.parquet")
df.index = pd.to_datetime(df.index)
pm = df["pm25_observed"].dropna()
print(f"  Dataset: {df.shape}  |  labelled days: {len(pm)}")
print(f"  pm25_observed mean={pm.mean():.1f}, median={pm.median():.1f}, "
      f"std={pm.std():.1f}, skew={pm.skew():.2f}")
print(f"  2019 mean: {df.loc[df.index.year==2019,'pm25_observed'].mean():.2f} µg/m³")


# ─────────────────────────────────────────────────────────────────────────────
# 4a — Label Distribution
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4a] Label distribution …")
fig, axes = plt.subplots(1, 2, figsize=(7.09, 3.2))

ax = axes[0]
pm_vals = pm.values
mu, sigma = np.mean(np.log(pm_vals)), np.std(np.log(pm_vals))

ax.hist(pm_vals, bins=40, density=True, alpha=0.5, color="steelblue",
        edgecolor="none", label="Observed")

x = np.linspace(pm_vals.min(), pm_vals.max(), 300)
kde = stats.gaussian_kde(pm_vals)
ax.plot(x, kde(x), color="steelblue", lw=1.5, label="KDE")

lognorm_pdf = stats.lognorm.pdf(x, s=sigma, scale=np.exp(mu))
ax.plot(x, lognorm_pdf, color="darkorange", lw=1.5, ls="--", label="Log-normal fit")

for (val, col, ls, lbl) in [
    (WHO_ANNUAL, "#1a9850", "--", f"WHO annual {WHO_ANNUAL:.0f}"),
    (WHO_24H,    "#91cf60", ":",  f"WHO 24h {WHO_24H:.0f}"),
    (SL_ANNUAL,  "#d73027", "--", f"SL annual {SL_ANNUAL:.0f}"),
    (SL_24H,     "#fc8d59", ":",  f"SL 24h {SL_24H:.0f}"),
]:
    ax.axvline(val, color=col, ls=ls, lw=0.9, alpha=0.85, label=lbl)

ax.axvline(pm_vals.mean(),   color="k", ls="-",  lw=0.9, alpha=0.7)
ax.axvline(np.median(pm_vals), color="k", ls="--", lw=0.9, alpha=0.7)
ax.text(pm_vals.mean()+0.5,  ax.get_ylim()[1]*0.6,  "mean",   fontsize=7)
ax.text(np.median(pm_vals)+0.5, ax.get_ylim()[1]*0.5, "median", fontsize=7)

ax.set_xlabel("PM$_{2.5}$ (µg m$^{-3}$)")
ax.set_ylabel("Density")
ax.set_title("(a) PM$_{2.5}$ distribution")
ax.legend(fontsize=6, ncol=1)

ann_txt = (f"mean = {pm_vals.mean():.1f} µg m$^{{-3}}$\n"
           f"median = {np.median(pm_vals):.1f}\n"
           f"std = {pm_vals.std():.1f}\n"
           f"skew = {stats.skew(pm_vals):.2f}")
ax.text(0.96, 0.96, ann_txt, transform=ax.transAxes,
        va="top", ha="right", fontsize=7,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.75))

ax2 = axes[1]
(osm, osr), (slope, intercept, r) = stats.probplot(np.log(pm_vals), dist="norm", plot=None)
ax2.scatter(osm, osr, s=4, alpha=0.4, color="steelblue", rasterized=True)
x_line = np.array([osm.min(), osm.max()])
ax2.plot(x_line, slope*x_line + intercept, color="darkorange", lw=1.2)
ax2.set_xlabel("Theoretical quantiles (log-normal)")
ax2.set_ylabel("Sample quantiles (log PM$_{2.5}$)")
ax2.set_title("(b) Q‒Q plot vs log-normal")
ax2.text(0.04, 0.94, f"r = {r:.3f}", transform=ax2.transAxes, fontsize=7)

fig.text(0.5, -0.01, "Data: CAMS EAC4 + NRT, monthly KOALA correction. Senarathna et al. 2024, CJS 53(2):197-206.",
         ha="center", fontsize=6, style="italic")
fig.tight_layout()
save_figure(fig, "label_distribution", out_dir=OUT_DIR)
plt.close(fig)
print("  → label_distribution saved")


# ─────────────────────────────────────────────────────────────────────────────
# 4b — Missingness heatmap
# ─────────────────────────────────────────────────────────────────────────────
print("[4b] Missingness heatmap …")
years = sorted(df.index.year.unique())
feat_cols = [c for c in df.columns]
miss_pct = {}
for yr in years:
    sub = df[df.index.year == yr]
    miss_pct[yr] = (sub[feat_cols].isna().mean() * 100).rename(yr)

miss_df = pd.DataFrame(miss_pct).T   # rows=years, cols=features
# Sort columns by overall missing rate
col_order = miss_df.mean().sort_values(ascending=True).index.tolist()
miss_df = miss_df[col_order]

fig, ax = plt.subplots(figsize=(12, 5))
im = ax.imshow(miss_df.values, aspect="auto", cmap="RdYlBu_r",
               vmin=0, vmax=100, interpolation="nearest")
plt.colorbar(im, ax=ax, label="Missing (%)", fraction=0.015, pad=0.01)
ax.set_xticks(range(len(col_order)))
ax.set_xticklabels(col_order, rotation=90, fontsize=5.5)
ax.set_yticks(range(len(years)))
ax.set_yticklabels(years, fontsize=6)
ax.set_title("Missingness heatmap — years × features (sorted by missing rate)")
ax.set_xlabel("Feature")
ax.set_ylabel("Year")

# Annotate cells with rate if > 20%
for i, yr in enumerate(years):
    for j, col in enumerate(col_order):
        v = miss_df.loc[yr, col]
        if v > 20:
            ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                    fontsize=4, color="black")

fig.tight_layout()
save_figure(fig, "missingness_heatmap", out_dir=OUT_DIR)
plt.close(fig)
print("  → missingness_heatmap saved")


# ─────────────────────────────────────────────────────────────────────────────
# 4c — Seasonal PM2.5 boxplots
# ─────────────────────────────────────────────────────────────────────────────
print("[4c] Seasonal boxplots …")
month_labels = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]
pm_df = pm.to_frame()
pm_df["month"] = pm_df.index.month

groups = [pm_df[pm_df["month"] == m]["pm25_observed"].values for m in range(1, 13)]

fig, ax = plt.subplots(figsize=(7.09, 3.2))
bp = ax.boxplot(groups, positions=range(1, 13), widths=0.6,
                patch_artist=True, notch=False,
                medianprops=dict(color="k", lw=1.2),
                boxprops=dict(facecolor="steelblue", alpha=0.6),
                flierprops=dict(marker=".", markersize=2, alpha=0.3),
                whiskerprops=dict(lw=0.8), capprops=dict(lw=0.8))

ax.scatter([3], [KOALA_MARCH], marker="*", s=80, color="crimson", zorder=5,
           label=f"KOALA 2019 Mar={KOALA_MARCH:.1f} µg m$^{{-3}}$")
ax.axhline(KOALA_ANNUAL, color="crimson", ls="--", lw=1.0,
           label=f"KOALA 2019 annual={KOALA_ANNUAL:.1f}")

for val, col, ls, lbl in [
    (WHO_ANNUAL, "#1a9850", "--", f"WHO annual {WHO_ANNUAL:.0f}"),
    (WHO_24H,    "#91cf60", ":",  f"WHO 24h {WHO_24H:.0f}"),
    (SL_ANNUAL,  "#d73027", "--", f"SL annual {SL_ANNUAL:.0f}"),
    (SL_24H,     "#fc8d59", ":",  f"SL 24h {SL_24H:.0f}"),
]:
    ax.axhline(val, color=col, ls=ls, lw=0.85, alpha=0.85, label=lbl)

ax.set_xticks(range(1, 13))
ax.set_xticklabels(month_labels)
ax.set_xlabel("Month")
ax.set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)")
ax.set_title("Seasonal PM$_{2.5}$ distribution (2003–2025)")
ax.legend(fontsize=6, ncol=2, loc="upper right")
fig.tight_layout()
save_figure(fig, "seasonal_pm25_boxplots", out_dir=OUT_DIR)
plt.close(fig)
print("  → seasonal_pm25_boxplots saved")


# ─────────────────────────────────────────────────────────────────────────────
# 4d — Annual trend
# ─────────────────────────────────────────────────────────────────────────────
print("[4d] Annual trend …")
ann = pm.groupby(pm.index.year).agg(["mean", "std"]).reset_index()
ann.columns = ["year", "mean", "std"]

fig, ax = plt.subplots(figsize=(7.09, 3.0))
ax.fill_between(ann["year"], ann["mean"]-ann["std"], ann["mean"]+ann["std"],
                alpha=0.25, color="steelblue")
ax.plot(ann["year"], ann["mean"], color="steelblue", lw=1.5, marker="o",
        markersize=3, label="Annual mean ± 1SD")
ax.axvline(2020, color="gray", ls="--", lw=1.0)
ax.text(2020.1, ann["mean"].max()*0.97, "COVID\nlockdown", fontsize=6.5, color="gray")
ax.axvspan(2021, 2023.99, alpha=0.08, color="crimson")
ax.text(2022, ann["mean"].min()*1.02, "La Niña\n2021–23", fontsize=6.5,
        color="crimson", ha="center")
ax.axhline(KOALA_ANNUAL, color="crimson", ls="--", lw=0.9,
           label=f"KOALA 2019={KOALA_ANNUAL:.1f} µg m$^{{-3}}$")
ax.axhline(WHO_ANNUAL, color="#1a9850", ls="--", lw=0.9,
           label=f"WHO annual={WHO_ANNUAL:.0f}")
ax.set_xlabel("Year")
ax.set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)")
ax.set_title("Annual mean PM$_{2.5}$ — Kandy (2003–2025)")
ax.legend(fontsize=7)
fig.tight_layout()
save_figure(fig, "annual_pm25_trend", out_dir=OUT_DIR)
plt.close(fig)
print("  → annual_pm25_trend saved")


# ─────────────────────────────────────────────────────────────────────────────
# 4e — AOD–PM2.5 scatter by season
# ─────────────────────────────────────────────────────────────────────────────
print("[4e] AOD–PM2.5 scatter …")
if "aod_modis" in df.columns:
    sub = df[df["pm25_observed"].notna() & df["aod_modis"].notna()].copy()
    sub["season"] = sub.index.month.map(SEASON_MAP)
    seasons = ["DJF", "MAM", "JJA", "SON"]
    fig, axes = plt.subplots(2, 2, figsize=(7.09, 5.5), sharey=True)
    axes = axes.flatten()
    for i, s in enumerate(seasons):
        ax = axes[i]
        g = sub[sub["season"] == s]
        sc = ax.scatter(g["aod_modis"], g["pm25_observed"],
                        c=g.index.year, cmap=PM25_CMAP,
                        s=6, alpha=0.55, rasterized=True)
        r = g["aod_modis"].corr(g["pm25_observed"])
        ax.text(0.04, 0.93, f"r = {r:.2f}  n={len(g)}", transform=ax.transAxes,
                fontsize=7, va="top")
        ax.set_title(f"({chr(97+i)}) {s}")
        ax.set_xlabel("MODIS AOD")
        if i % 2 == 0:
            ax.set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)")
    fig.colorbar(sc, ax=axes, label="Year", fraction=0.02, pad=0.01)
    fig.suptitle("AOD–PM$_{2.5}$ scatter by season", y=1.01)
    fig.tight_layout()
    save_figure(fig, "aod_pm25_scatter_seasonal", out_dir=OUT_DIR)
    plt.close(fig)
    print("  → aod_pm25_scatter_seasonal saved")
else:
    print("  [SKIP] aod_modis not in dataset")


# ─────────────────────────────────────────────────────────────────────────────
# 4f — Feature correlation heatmap
# ─────────────────────────────────────────────────────────────────────────────
print("[4f] Feature correlation heatmap …")
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
corr_all = df[num_cols].corr()
# Keep only features correlated |r|>0.15 with pm25_observed
if "pm25_observed" in corr_all.columns:
    strong = corr_all["pm25_observed"].abs()
    keep = strong[strong > 0.15].index.tolist()
    if "pm25_observed" not in keep:
        keep.append("pm25_observed")
    corr_sub = df[keep].corr()
    # Hierarchical clustering
    Z = linkage(corr_sub.values, method="ward")
    order = leaves_list(Z)
    corr_reord = corr_sub.iloc[order, :].iloc[:, order]

    fig, ax = plt.subplots(figsize=(max(6, len(keep)*0.4), max(5, len(keep)*0.38)))
    im = ax.imshow(corr_reord.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02, label="Pearson r")
    cols_ord = corr_reord.columns.tolist()
    ax.set_xticks(range(len(cols_ord))); ax.set_xticklabels(cols_ord, rotation=90, fontsize=6)
    ax.set_yticks(range(len(cols_ord))); ax.set_yticklabels(cols_ord, fontsize=6)
    for i in range(len(cols_ord)):
        for j in range(len(cols_ord)):
            v = corr_reord.iloc[i, j]
            if abs(v) >= 0.3:
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=4.5, color="white" if abs(v) > 0.6 else "black")
    ax.set_title("Feature correlation (|r| > 0.15 with PM$_{2.5}$, hierarchical order)")
    fig.tight_layout()
    save_figure(fig, "feature_correlation_heatmap", out_dir=OUT_DIR)
    plt.close(fig)
    print("  → feature_correlation_heatmap saved")


# ─────────────────────────────────────────────────────────────────────────────
# 4g — ACF of PM2.5
# ─────────────────────────────────────────────────────────────────────────────
print("[4g] ACF …")
pm_reindex = pm.asfreq("D")  # will have NaNs for missing days — statsmodels handles this
fig, ax = plt.subplots(figsize=(5.5, 2.8))
plot_acf(pm_reindex.fillna(pm_reindex.mean()), lags=30, ax=ax,
         alpha=0.05, color="steelblue", vlines_kwargs={"color": "steelblue"})
ax.set_xlabel("Lag (days)")
ax.set_ylabel("ACF")
ax.set_title("Autocorrelation of daily PM$_{2.5}$ — justifies LOMO CV")
ax.axhline(0, color="black", lw=0.5)
fig.tight_layout()
save_figure(fig, "pm25_acf", out_dir=OUT_DIR)
plt.close(fig)
print("  → pm25_acf saved")


# ─────────────────────────────────────────────────────────────────────────────
# 4h — BLH vs PM2.5 (two-panel scatter)
# ─────────────────────────────────────────────────────────────────────────────
print("[4h] BLH vs PM2.5 …")
if "blh_min" in df.columns and "blh_max" in df.columns:
    sub = df[df["pm25_observed"].notna()].copy()
    sub["season"] = sub.index.month.map(SEASON_MAP)
    fig, axes = plt.subplots(1, 2, figsize=(7.09, 3.1))
    for ax, blh_col, label, letter in zip(axes,
                                           ["blh_min", "blh_max"],
                                           ["BLH$_{min}$ nocturnal (m)",
                                            "BLH$_{max}$ daytime (m)"],
                                           ["a", "b"]):
        for s, col in SEASON_COLOURS.items():
            g = sub[sub["season"] == s]
            ax.scatter(g[blh_col], g["pm25_observed"],
                       s=5, alpha=0.4, color=col, rasterized=True, label=s)
        r = sub[blh_col].corr(sub["pm25_observed"])
        ax.text(0.96, 0.96, f"r = {r:.2f}", transform=ax.transAxes,
                va="top", ha="right", fontsize=7)
        ax.set_xlabel(label)
        ax.set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)")
        ax.set_title(f"({letter}) {blh_col}")
    handles = [mpatches.Patch(color=c, label=s) for s, c in SEASON_COLOURS.items()]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=7,
               bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("BLH vs PM$_{2.5}$ — low BLH → high PM$_{2.5}$ (valley trapping)")
    fig.tight_layout()
    save_figure(fig, "blh_pm25_scatter", out_dir=OUT_DIR)
    plt.close(fig)
    print("  → blh_pm25_scatter saved")
else:
    print("  [SKIP] blh_min/blh_max not in dataset")


# ─────────────────────────────────────────────────────────────────────────────
# 4i — CAMS raw vs MERRA-2 vs KOALA (2019)
# ─────────────────────────────────────────────────────────────────────────────
print("[4i] CAMS corrected vs MERRA-2 vs KOALA (2019) …")
df_2019 = df[df.index.year == 2019].copy()
# Monthly-corrected CAMS: corrected[d] = raw[d] × ratio_m, so raw[d] = corrected[d] / ratio_m.
# ratio_m = KOALA_MONTHLY[m] / CAMS_2019_monthly_mean[m]. We recover per-month:
cams_monthly_mean_corrected = df_2019.groupby(df_2019.index.month)["pm25_observed"].transform("mean")
koala_monthly_series = df_2019.index.month.map(KOALA_MONTHLY)
# cams_raw per day = corrected / ratio_m = corrected × (CAMS_monthly_mean_corrected / KOALA_monthly[m])
cams_raw_2019 = df_2019["pm25_observed"] * (cams_monthly_mean_corrected / koala_monthly_series)

fig, ax = plt.subplots(figsize=(7.09, 3.2))
ax.plot(df_2019.index, cams_raw_2019.values, color="#2166ac", lw=1.0, alpha=0.85,
        label="CAMS raw (approx. recovered, monthly ratio)")

if MERRA2_PATH.exists():
    m2 = pd.read_csv(MERRA2_PATH)
    m2["date"] = pd.to_datetime(m2["date"])
    m2 = m2[m2["date"].dt.year == 2019].set_index("date")["merra2_pm25"]
    ax.plot(m2.index, m2.values, color="#d6604d", lw=1.0, alpha=0.85,
            label=f"MERRA-2 (r=0.177, Δ=−23.6 µg m$^{{-3}}$)")
else:
    print("  [INFO] MERRA-2 daily CSV not found — skipping MERRA-2 line")

ax.axhline(KOALA_ANNUAL, color="crimson", ls="--", lw=1.2,
           label=f"KOALA annual mean = {KOALA_ANNUAL:.2f} µg m$^{{-3}}$")
ax.axhline(KOALA_MARCH,  color="crimson", ls=":",  lw=1.0,
           label=f"KOALA March mean  = {KOALA_MARCH:.2f} µg m$^{{-3}}$")

ax.set_xlabel("Date (2019)")
ax.set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)")
ax.set_title("CAMS (monthly-corrected) vs MERRA-2 vs KOALA reference — 2019")
ax.legend(fontsize=7)
ax.text(0.01, 0.02,
        "Note: MERRA-2 r=0.177 vs CAMS — structurally incompatible for valley basin.\n"
        "MERRA-2 used as validation diagnostic only.",
        transform=ax.transAxes, fontsize=6, style="italic", va="bottom")
fig.tight_layout()
save_figure(fig, "cams_merra2_koala_comparison_2019", out_dir=OUT_DIR)
plt.close(fig)
print("  → cams_merra2_koala_comparison_2019 saved")


# ─────────────────────────────────────────────────────────────────────────────
# 4j — AOD missingness by season
# ─────────────────────────────────────────────────────────────────────────────
print("[4j] AOD missingness by season …")
if "aod_modis" in df.columns:
    df["_month"] = df.index.month
    miss_by_month = df.groupby("_month")["aod_modis"].apply(lambda x: x.isna().mean() * 100)
    pm_by_month   = df.groupby("_month")["pm25_observed"].mean()

    fig, ax = plt.subplots(figsize=(5.5, 3.0))
    ax2 = ax.twinx()
    bars = ax.bar(range(1, 13), miss_by_month, color="steelblue", alpha=0.7,
                  label="AOD missing %")
    ax2.plot(range(1, 13), pm_by_month, color="darkorange", lw=1.5,
             marker="o", markersize=4, label="Mean PM$_{2.5}$")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["Jan","Feb","Mar","Apr","May","Jun",
                        "Jul","Aug","Sep","Oct","Nov","Dec"])
    ax.set_xlabel("Month")
    ax.set_ylabel("MODIS AOD missing rate (%)", color="steelblue")
    ax2.set_ylabel("Mean PM$_{2.5}$ (µg m$^{-3}$)", color="darkorange")
    ax.tick_params(axis="y", labelcolor="steelblue")
    ax2.tick_params(axis="y", labelcolor="darkorange")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1+h2, l1+l2, fontsize=7, loc="upper left")
    ax.set_title("MODIS AOD missing rate vs mean PM$_{2.5}$ by month\n"
                 "(JJA cloud gap: missing-not-at-random)")
    df.drop(columns=["_month"], inplace=True)
    fig.tight_layout()
    save_figure(fig, "aod_missingness_seasonal", out_dir=OUT_DIR)
    plt.close(fig)
    print("  → aod_missingness_seasonal saved")


# ─────────────────────────────────────────────────────────────────────────────
# 4k — SHAP summary bar chart
# ─────────────────────────────────────────────────────────────────────────────
print("[4k] SHAP summary bar …")
shap_path = TABLES_DIR / "shap_importance.csv"
if not shap_path.exists():
    shap_path = TABLES_DIR / "shap_feature_importance.csv"

if shap_path.exists():
    shap_df = pd.read_csv(shap_path)
    # Normalise column names
    if "mean_abs_shap" not in shap_df.columns:
        for c in shap_df.columns:
            if "shap" in c.lower():
                shap_df = shap_df.rename(columns={c: "mean_abs_shap"})
                break
    if "feature" not in shap_df.columns:
        shap_df = shap_df.rename(columns={shap_df.columns[0]: "feature"})

    shap_df = shap_df.nlargest(20, "mean_abs_shap").reset_index(drop=True)

    # Feature-group colour map
    meteo_feats = {"wind_speed", "wind_dir", "blh_min", "blh_max", "t2m", "d2m",
                   "skt", "rh", "sp", "tp", "ssrd", "u10", "v10", "wdir_sin",
                   "wdir_cos", "t925", "blh_mean"}
    sat_feats   = {"aod_modis", "tropomi_no2", "tropomi_co", "tropomi_aer_ai",
                   "aod_blh_ratio", "aod_rh", "no2_blh_ratio", "co_blh_ratio"}
    topo_feats  = {"vvc", "vvc_revised", "kfp", "kfp_v2", "dsc", "rwp",
                   "terrain_blocking_idx", "wind_along", "wind_cross",
                   "valley_flow_ratio", "richardson_number", "ri_stable_flag"}
    clim_feats  = {"mei_month_sin", "mei_month_cos", "month_sin", "month_cos",
                   "dow_sin", "dow_cos", "month", "dow"}

    def get_colour(feat):
        if feat in meteo_feats:    return "#4393c3"  # steelblue
        if feat in sat_feats:      return "#d6604d"  # orange-red
        if feat in topo_feats:     return "#4dac26"  # green
        if feat in clim_feats:     return "#762a83"  # purple
        return "#aaaaaa"

    colours = [get_colour(f) for f in shap_df["feature"]]
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    bars = ax.barh(range(len(shap_df)), shap_df["mean_abs_shap"][::-1].values,
                   color=colours[::-1], edgecolor="none", height=0.7)
    ax.set_yticks(range(len(shap_df)))
    ax.set_yticklabels(shap_df["feature"][::-1].tolist(), fontsize=7)
    ax.set_xlabel("Mean |SHAP value| (µg m$^{-3}$)")
    ax.set_title("SHAP feature importance — top 20\n(monthly KOALA correction, Senarathna 2024)")

    legend_patches = [
        mpatches.Patch(color="#4393c3", label="Meteorological"),
        mpatches.Patch(color="#d6604d", label="Satellite"),
        mpatches.Patch(color="#4dac26", label="Topographic"),
        mpatches.Patch(color="#762a83", label="Temporal/Climate"),
    ]
    ax.legend(handles=legend_patches, fontsize=7, loc="lower right")
    fig.tight_layout()
    save_figure(fig, "shap_summary_bar", out_dir=OUT_DIR)
    plt.close(fig)
    print("  → shap_summary_bar saved")
else:
    print(f"  [SKIP] SHAP importance file not found at {shap_path}")


print(f"\n✅ Stage 1 EDA complete. All plots → {OUT_DIR}")
