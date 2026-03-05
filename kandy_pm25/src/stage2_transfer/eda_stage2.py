"""
eda_stage2.py — Stage 2 EDA: 5 publication-quality plots comparing Kandy,
                Medellín, and Chiang Mai for transfer learning domain assessment.

Plots:
  6a. PM2.5 distribution comparison (three-panel histogram + KDE)
  6b. Seasonal pattern comparison (monthly mean per city)
  6c. BLH and wind speed distributions (2×3 layout)
  6d. Domain suitability CSV table
  6e. Medellín spatial gradient diagnostic

Usage:
    python src/stage2_transfer/eda_stage2.py
"""

import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

# ── Path setup ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from src.utils.plot_style import apply_style, PM25_CMAP, save_figure
apply_style("ieee")

# ── Paths ─────────────────────────────────────────────────────────────────────
STAGE2_DIR = ROOT / "data" / "processed" / "stage2"
MERGED_DIR = ROOT / "data" / "processed" / "merged"
OUT_DIR    = ROOT / "results" / "eda" / "stage2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CITY_COLOURS = {
    "Kandy":     "#2166ac",
    "Medellín":  "#d6604d",
    "Chiang Mai":"#4dac26",
}

# ─────────────────────────────────────────────────────────────────────────────
# Load datasets
# ─────────────────────────────────────────────────────────────────────────────
print("Loading datasets …")

# Kandy — daily domain dataset
df_k = pd.read_parquet(MERGED_DIR / "dataset_daily.parquet")
df_k.index = pd.to_datetime(df_k.index)
kandy_pm = df_k["pm25_observed"].dropna()

# Medellín — per-station (89,946 rows × multiple stations)
# datetime_utc is a column (not the index) in this parquet — set it as index
df_m = pd.read_parquet(STAGE2_DIR / "medellin_stage2_perstation.parquet")
if "datetime_utc" in df_m.columns:
    df_m.index = pd.to_datetime(df_m["datetime_utc"])
else:
    df_m.index = pd.to_datetime(df_m.index)

# Chiang Mai — non-burning period (5,564 rows)
df_c = pd.read_parquet(STAGE2_DIR / "chiangmai_stage2_nonburning.parquet")
df_c.index = pd.to_datetime(df_c.index)

# Map PM2.5 column names (adapt to whatever column name exists)
def get_pm_col(df):
    for c in ["pm25", "pm25_mean", "pm2_5", "PM2_5", "pm25_obs"]:
        if c in df.columns:
            return c
    # Fallback: first numeric column with 'pm' in name
    cands = [c for c in df.columns if "pm" in c.lower()]
    return cands[0] if cands else None

med_pm_col = get_pm_col(df_m)
cm_pm_col  = get_pm_col(df_c)
print(f"  Medellín PM col: {med_pm_col}  | Chiang Mai PM col: {cm_pm_col}")

med_pm = df_m[med_pm_col].dropna() if med_pm_col else pd.Series(dtype=float)
cm_pm  = df_c[cm_pm_col].dropna()   if cm_pm_col  else pd.Series(dtype=float)

print(f"  Kandy:     n={len(kandy_pm)}, mean={kandy_pm.mean():.1f}, std={kandy_pm.std():.1f}")
print(f"  Medellín:  n={len(med_pm)}, mean={med_pm.mean():.1f}, std={med_pm.std():.1f}")
print(f"  Chiang Mai:n={len(cm_pm)}, mean={cm_pm.mean():.1f}, std={cm_pm.std():.1f}")


# ─────────────────────────────────────────────────────────────────────────────
# 6a — PM2.5 distribution comparison
# ─────────────────────────────────────────────────────────────────────────────
print("\n[6a] PM2.5 distribution comparison …")
datasets = [("Kandy", kandy_pm), ("Medellín", med_pm), ("Chiang Mai", cm_pm)]

x_max = max(d.quantile(0.99) for _, d in datasets if len(d) > 0)
x_min = 0

fig, axes = plt.subplots(1, 3, figsize=(7.09, 2.8), sharey=False, sharex=True)
for ax, (name, data) in zip(axes, datasets):
    if len(data) == 0:
        ax.set_title(f"{name}\n(no data)")
        continue
    col = CITY_COLOURS[name]
    ax.hist(data, bins=40, density=True, alpha=0.5, color=col, edgecolor="none")
    x = np.linspace(max(0, data.min()), min(x_max, data.max()), 300)
    kde = stats.gaussian_kde(data.clip(0.1))
    ax.plot(x, kde(x), color=col, lw=1.5)
    skew = stats.skew(data)
    ann = (f"mean={data.mean():.1f}\n"
           f"std={data.std():.1f}\n"
           f"skew={skew:.2f}")
    ax.text(0.96, 0.95, ann, transform=ax.transAxes, va="top", ha="right",
            fontsize=7, bbox=dict(boxstyle="round,pad=0.25", fc="white", alpha=0.8))
    ax.set_title(f"{name}")
    ax.set_xlabel("PM$_{2.5}$ (µg m$^{-3}$)")
    ax.set_xlim(x_min, x_max)
axes[0].set_ylabel("Density")
fig.suptitle("PM$_{2.5}$ distribution comparison — transfer learning domains",
             fontsize=8, y=1.01)
fig.tight_layout()
save_figure(fig, "pm25_distribution_comparison", out_dir=OUT_DIR)
plt.close(fig)
print("  → pm25_distribution_comparison saved")


# ─────────────────────────────────────────────────────────────────────────────
# 6b — Seasonal pattern comparison
# ─────────────────────────────────────────────────────────────────────────────
print("[6b] Seasonal pattern comparison …")
month_labels = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]

def monthly_means(data):
    m = data.groupby(data.index.month).mean()
    return m.reindex(range(1, 13))

fig, ax = plt.subplots(figsize=(5.5, 3.0))
for name, data in datasets:
    if len(data) == 0:
        continue
    mm = monthly_means(data)
    ax.plot(range(1, 13), mm.values, marker="o", markersize=4,
            lw=1.4, color=CITY_COLOURS[name], label=name)

ax.set_xticks(range(1, 13))
ax.set_xticklabels(month_labels)
ax.set_xlabel("Month")
ax.set_ylabel("Mean PM$_{2.5}$ (µg m$^{-3}$)")
ax.set_title("Seasonal PM$_{2.5}$ pattern by city")
ax.legend(fontsize=8)
ax.text(0.01, 0.01,
        "Kandy: NE monsoon dry Jan–Mar | Medellín: bimodal dry seasons | "
        "Chiang Mai: non-burning May–Dec subset",
        transform=ax.transAxes, fontsize=5.5, style="italic", va="bottom")
fig.tight_layout()
save_figure(fig, "seasonal_pattern_comparison", out_dir=OUT_DIR)
plt.close(fig)
print("  → seasonal_pattern_comparison saved")


# ─────────────────────────────────────────────────────────────────────────────
# 6c — BLH and wind distributions
# ─────────────────────────────────────────────────────────────────────────────
print("[6c] BLH and wind distributions …")
# Map BLH/wind columns for each dataset
city_data = {
    "Kandy":     df_k,
    "Medellín":  df_m,
    "Chiang Mai":df_c,
}

def get_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

blh_cands  = ["blh_min", "blh_max", "blh", "blh_mean", "boundary_layer_height"]
wind_cands = ["wind_speed", "u10", "wind", "ws"]

fig, axes = plt.subplots(2, 3, figsize=(7.09, 4.5))
for col_idx, (name, d) in enumerate(city_data.items()):
    col_city = CITY_COLOURS[name]

    # BLH
    blh_col = get_col(d, blh_cands)
    ax_blh = axes[0, col_idx]
    if blh_col and d[blh_col].notna().sum() > 10:
        blh_data = d[blh_col].dropna()
        ax_blh.hist(blh_data, bins=40, density=True, alpha=0.6,
                    color=col_city, edgecolor="none")
        ax_blh.set_title(f"{name}\n({blh_col})")
        ax_blh.text(0.97, 0.97,
                    f"mean={blh_data.mean():.0f} m\nstd={blh_data.std():.0f} m",
                    transform=ax_blh.transAxes, va="top", ha="right", fontsize=7)
    else:
        ax_blh.text(0.5, 0.5, "BLH\nnot available", transform=ax_blh.transAxes,
                    ha="center", va="center", fontsize=8, color="gray")
        ax_blh.set_title(f"{name}")
    if col_idx == 0:
        ax_blh.set_ylabel("BLH\nDensity", fontsize=7)

    # Wind speed
    ws_col = get_col(d, wind_cands)
    ax_ws = axes[1, col_idx]
    if ws_col and d[ws_col].notna().sum() > 10:
        ws_data = d[ws_col].dropna()
        ax_ws.hist(ws_data, bins=40, density=True, alpha=0.6,
                   color=col_city, edgecolor="none")
        ax_ws.set_xlabel("Wind speed (m s$^{-1}$)")
        ax_ws.text(0.97, 0.97,
                   f"mean={ws_data.mean():.1f}\nstd={ws_data.std():.1f}",
                   transform=ax_ws.transAxes, va="top", ha="right", fontsize=7)
    else:
        ax_ws.text(0.5, 0.5, "Wind\nnot available", transform=ax_ws.transAxes,
                   ha="center", va="center", fontsize=8, color="gray")
    if col_idx == 0:
        ax_ws.set_ylabel("Wind\nDensity", fontsize=7)

fig.suptitle("BLH and wind speed distributions by city", fontsize=8)
fig.tight_layout()
save_figure(fig, "met_distribution_comparison", out_dir=OUT_DIR)
plt.close(fig)
print("  → met_distribution_comparison saved")


# ─────────────────────────────────────────────────────────────────────────────
# 6d — Domain suitability table (CSV)
# ─────────────────────────────────────────────────────────────────────────────
print("[6d] Domain suitability table …")

def safe_miss(df, col):
    if col not in df.columns:
        return np.nan
    return df[col].isna().mean() * 100

def safe_mean(df, col):
    if col not in df.columns:
        return np.nan
    return df[col].mean()

# Station count for Medellín
n_stations_med = df_m["station_id"].nunique() if "station_id" in df_m.columns else 11

table = pd.DataFrame([
    {
        "City": "Kandy",
        "PM2.5 mean (µg/m³)": round(kandy_pm.mean(), 2),
        "PM2.5 std": round(kandy_pm.std(), 2),
        "N days": len(kandy_pm),
        "Missing %": round(safe_miss(df_k, "pm25_observed"), 1),
        "BLH mean (m)": round(safe_mean(df_k, "blh_min"), 1),
        "N stations": 1,
        "Elevation (m)": 488,
        "Notes": "KOALA low-cost sensor; 1 ground station",
    },
    {
        "City": "Medellín",
        "PM2.5 mean (µg/m³)": round(med_pm.mean(), 2) if len(med_pm) > 0 else np.nan,
        "PM2.5 std": round(med_pm.std(), 2) if len(med_pm) > 0 else np.nan,
        "N days": int(med_pm.notna().sum()) if len(med_pm) > 0 else 0,
        "Missing %": round(safe_miss(df_m, med_pm_col) if med_pm_col else 0, 1),
        "BLH mean (m)": round(safe_mean(df_m, get_col(df_m, blh_cands) or ""), 1),
        "N stations": n_stations_med,
        "Elevation (m)": 1495,
        "Notes": "SIATA network; per-station; inter-station std=7.00 µg/m³ (34% of mean)",
    },
    {
        "City": "Chiang Mai",
        "PM2.5 mean (µg/m³)": round(cm_pm.mean(), 2) if len(cm_pm) > 0 else np.nan,
        "PM2.5 std": round(cm_pm.std(), 2) if len(cm_pm) > 0 else np.nan,
        "N days": int(cm_pm.notna().sum()) if len(cm_pm) > 0 else 0,
        "Missing %": round(safe_miss(df_c, cm_pm_col) if cm_pm_col else 0, 1),
        "BLH mean (m)": round(safe_mean(df_c, get_col(df_c, blh_cands) or ""), 1),
        "N stations": 1,
        "Elevation (m)": 316,
        "Notes": "City-averaged; non-burning period only (May–Dec 2022)",
    },
])

csv_path = OUT_DIR / "domain_suitability.csv"
table.to_csv(csv_path, index=False)
print(f"  → domain_suitability.csv saved ({csv_path})")
print(table.to_string(index=False))


# ─────────────────────────────────────────────────────────────────────────────
# 6e — Medellín spatial gradient diagnostic
# ─────────────────────────────────────────────────────────────────────────────
print("[6e] Medellín spatial gradient …")

lat_col = next((c for c in ["lat", "latitude", "station_lat"] if c in df_m.columns), None)
lon_col = next((c for c in ["lon", "longitude", "station_lon"] if c in df_m.columns), None)

if lat_col and lon_col and med_pm_col:
    # Find most data-rich month
    df_m["_month"] = df_m.index.month
    best_month = (df_m.groupby("_month")[med_pm_col].count().idxmax())
    month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                   7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    sub = df_m[df_m["_month"] == best_month].copy()
    sub_agg = sub.groupby([lat_col, lon_col])[med_pm_col].mean().reset_index()
    inter_std = sub[med_pm_col].std()
    inter_mean = sub[med_pm_col].mean()

    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.9), sharey=True)
    ax = axes[0]
    ax.scatter(sub_agg[lat_col], sub_agg[med_pm_col],
               s=50, color="#d6604d", edgecolors="k", lw=0.4)
    ax.set_xlabel("Station latitude (°N)")
    ax.set_ylabel(f"Mean PM$_{{2.5}}$ (µg m$^{{-3}}$) — {month_names[best_month]}")
    ax.set_title("(a) PM$_{2.5}$ vs latitude")
    r_lat = sub_agg[lat_col].corr(sub_agg[med_pm_col])
    ax.text(0.04, 0.94, f"r = {r_lat:.2f}", transform=ax.transAxes, fontsize=7)

    ax = axes[1]
    ax.scatter(sub_agg[lon_col], sub_agg[med_pm_col],
               s=50, color="#d6604d", edgecolors="k", lw=0.4)
    ax.set_xlabel("Station longitude (°E)")
    ax.set_title("(b) PM$_{2.5}$ vs longitude")
    r_lon = sub_agg[lon_col].corr(sub_agg[med_pm_col])
    ax.text(0.04, 0.94, f"r = {r_lon:.2f}", transform=ax.transAxes, fontsize=7)

    fig.text(0.5, -0.04,
             f"Inter-station std = {inter_std:.2f} µg m$^{{-3}}$ ({inter_std/inter_mean*100:.0f}% of mean). "
             f"Spatial gradient the Stage 2 PINN found trivially constant. Known limitation.",
             ha="center", fontsize=6, style="italic")
    df_m.drop(columns=["_month"], inplace=True)
    fig.tight_layout()
    save_figure(fig, "medellin_spatial_gradient", out_dir=OUT_DIR)
    plt.close(fig)
    print("  → medellin_spatial_gradient saved")
else:
    print(f"  [SKIP] lat/lon columns not found in Medellín parquet "
          f"(found: {[c for c in df_m.columns if 'lat' in c.lower() or 'lon' in c.lower()]})")


print(f"\n✅ Stage 2 EDA complete. All outputs → {OUT_DIR}")
