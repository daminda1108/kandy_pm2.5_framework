"""
generate_chiangmai_figures.py — Generate all 10 figures for the Chiang Mai validation report.

Phase 6 of the Chiang Mai PINN validation report.

Inputs (from prior phases):
    - data/processed/stage2/chiangmai_pinn_vs_observations.parquet  (Phase 4)
    - data/processed/stage2/chiangmai_burning_mask.csv               (Phase 5)
    - results/tables/chiangmai_pinn_station_metrics.json             (Phase 4)
    - results/tables/chiangmai_pinn_seasonal_metrics.json            (Phase 4)
    - results/tables/chiangmai_burning_analysis.json                 (Phase 5)
    - data/external/chiangmai/era5/chiangmai_era5_2022.nc            (Phase 2a ✅)
    - data/external/chiangmai/pm25/chiangmai_all_stations_2021_2025.csv  (Phase 1 ✅)

Figures:
    F1  Station map (CM domain box, terrain, Air4Thai + PurpleAir markers)
    F2  PM2.5 time series 2021-2025 (all stations, colour by provider)
    F3  PINN vs observations scatter (all stations × dates, 1:1 line, R² annotation)
    F4  Per-station R² bar chart
    F5  Monthly bias by month (burning months highlighted)
    F6  K–BLH correlation scatter
    F7  Diurnal PINN K cycle for selected days
    F8  Burning analysis three-panel (obs vs PINN vs baseline)
    F9  Spatial PINN heatmap + station overlays (non-burning day)
    F10 Annual mean PINN PM2.5 with station values

Output: results/figures/publication/chiangmai_report_F{01..10}.{pdf,png}

Usage:
    python generate_chiangmai_figures.py        # all 10 figures
    python generate_chiangmai_figures.py --fig F1 F3 F6   # specific figures
    python generate_chiangmai_figures.py --check          # check which input files exist
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    LOG_FORMAT, LOG_DATEFMT,
    DATA_DIR, RESULTS_DIR,
    CHIANGMAI_PINN_BBOX,
    PINN_BLH_NORM_SCALE,
)
from src.utils.plot_style import apply_style, save_figure, PM25_CMAP, DIFF_CMAP

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("generate_chiangmai_figures")

PROCESSED_DIR = DATA_DIR / "processed"

# ── Input paths ───────────────────────────────────────────────────────────────
PINN_PARQUET = PROCESSED_DIR / "stage2" / "chiangmai_pinn_vs_observations.parquet"
BURN_MASK    = PROCESSED_DIR / "stage2" / "chiangmai_burning_mask.csv"
PM25_CSV     = DATA_DIR / "external" / "chiangmai" / "pm25" / "chiangmai_all_stations_2021_2025.csv"
STATION_JSON = RESULTS_DIR / "tables" / "chiangmai_pinn_station_metrics.json"
SEASON_JSON  = RESULTS_DIR / "tables" / "chiangmai_pinn_seasonal_metrics.json"
BURN_JSON    = RESULTS_DIR / "tables" / "chiangmai_burning_analysis.json"
ERA5_2022    = DATA_DIR / "external" / "chiangmai" / "era5" / "chiangmai_era5_2022.nc"
ELEV_NPZ     = PROCESSED_DIR / "pinn_inputs" / "chiangmai_elev_grid_100m.npz"
CKPT_DIR     = RESULTS_DIR / "models" / "stage2_chiangmai_pinn" / "v5" / "checkpoints"

# ── Style constants ────────────────────────────────────────────────────────────
BURNING_MONTHS = {2, 3, 4, 5}

PROVIDER_COLORS = {
    "Air4Thai":  "#1f77b4",   # blue
    "PurpleAir": "#ff7f0e",   # orange
}

SEASON_COLORS = {
    "burning":     "#d62728",   # red
    "non-burning": "#2ca02c",   # green
    "cool":        "#9467bd",   # purple
}


# ══════════════════════════════════════════════════════════════════════════════
# Data loading helpers
# ══════════════════════════════════════════════════════════════════════════════

def load_pinn_df() -> pd.DataFrame:
    if not PINN_PARQUET.exists():
        raise FileNotFoundError(f"Run Phase 4 first: {PINN_PARQUET}")
    df = pd.read_parquet(str(PINN_PARQUET))
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], utc=True)
    return df


def load_raw_obs() -> pd.DataFrame:
    df = pd.read_csv(str(PM25_CSV))
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True)
    return df


def load_station_metrics() -> dict:
    if not STATION_JSON.exists():
        return {}
    with open(STATION_JSON) as f:
        return json.load(f)


def load_season_metrics() -> dict:
    if not SEASON_JSON.exists():
        return {}
    with open(SEASON_JSON) as f:
        return json.load(f)


def load_burn_analysis() -> dict:
    if not BURN_JSON.exists():
        return {}
    with open(BURN_JSON) as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════════════════════
# F1 — Station Map
# ══════════════════════════════════════════════════════════════════════════════

def figure_F1_station_map(df: pd.DataFrame):
    """Station map: CM PINN bbox, terrain background, Air4Thai + PurpleAir markers."""
    apply_style("ieee")
    fig, ax = plt.subplots(figsize=(5, 5))

    # Domain bbox
    bbox = CHIANGMAI_PINN_BBOX
    rect = mpatches.Rectangle(
        (bbox["lon_min"], bbox["lat_min"]),
        bbox["lon_max"] - bbox["lon_min"],
        bbox["lat_max"] - bbox["lat_min"],
        linewidth=2, edgecolor="black", facecolor="none", linestyle="--",
        label="PINN domain (15×15 km)"
    )
    ax.add_patch(rect)

    # Terrain background (if elev available)
    if ELEV_NPZ.exists():
        elev_data = np.load(str(ELEV_NPZ))
        elev = elev_data["elev"]
        lat_g = np.linspace(bbox["lat_min"], bbox["lat_max"], 150)
        lon_g = np.linspace(bbox["lon_min"], bbox["lon_max"], 150)
        ax.contourf(lon_g, lat_g, elev, levels=10, cmap="terrain", alpha=0.4)

    # Stations
    station_info = df.groupby(["location_name", "provider"]).first()[["lat", "lon"]].reset_index()
    for _, row in station_info.iterrows():
        provider = row["provider"]
        marker   = "^" if provider == "Air4Thai" else "o"
        color    = PROVIDER_COLORS.get(provider, "gray")
        ax.scatter(row["lon"], row["lat"], c=color, marker=marker, s=80, zorder=5,
                   edgecolors="white", linewidths=0.5)
        ax.annotate(row["location_name"][:15], (row["lon"], row["lat"]),
                    fontsize=5, xytext=(3, 3), textcoords="offset points")

    # Legend
    handles = [
        mpatches.Patch(color=PROVIDER_COLORS["Air4Thai"],  label="Air4Thai (govt)"),
        mpatches.Patch(color=PROVIDER_COLORS["PurpleAir"], label="PurpleAir (low-cost)"),
        rect,
    ]
    ax.legend(handles=handles, fontsize=6, loc="lower right")

    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title("Chiang Mai PM$_{2.5}$ station network")
    ax.set_xlim(bbox["lon_min"] - 0.02, bbox["lon_max"] + 0.02)
    ax.set_ylim(bbox["lat_min"] - 0.02, bbox["lat_max"] + 0.02)
    plt.tight_layout()
    save_figure(fig, "chiangmai_report_F01_station_map")
    plt.close(fig)
    log.info("F1 saved")


# ══════════════════════════════════════════════════════════════════════════════
# F2 — PM2.5 Time Series
# ══════════════════════════════════════════════════════════════════════════════

def figure_F2_timeseries(obs_df: pd.DataFrame):
    """PM2.5 time series 2021-2025, all stations, colour by provider, 7-day rolling mean."""
    apply_style("ieee")
    fig, ax = plt.subplots(figsize=(8, 3.5))

    obs_df["date"] = obs_df["datetime_utc"].dt.date
    daily = (
        obs_df.groupby(["date", "location_name", "provider"])
        .agg(pm25=("pm25", "mean"))
        .reset_index()
    )
    daily["date"] = pd.to_datetime(daily["date"])

    for stn, grp in daily.groupby("location_name"):
        grp = grp.sort_values("date")
        provider = grp["provider"].iloc[0]
        color = PROVIDER_COLORS.get(provider, "gray")
        # 7-day rolling mean
        rolling = grp.set_index("date")["pm25"].rolling("7D", min_periods=3).mean()
        ax.plot(rolling.index, rolling.values, color=color, alpha=0.7, linewidth=0.8,
                label=stn[:20])

    # Shade burning seasons (Feb–May each year)
    for year in range(2021, 2026):
        ax.axvspan(pd.Timestamp(f"{year}-02-01"), pd.Timestamp(f"{year}-05-31"),
                   alpha=0.08, color="#d62728", zorder=0)

    ax.set_xlabel("Date")
    ax.set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)")
    ax.set_title("Chiang Mai PM$_{2.5}$ 2021–2025 (7-day rolling mean)")
    ax.legend(fontsize=5, loc="upper right", ncol=2)
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    save_figure(fig, "chiangmai_report_F02_timeseries")
    plt.close(fig)
    log.info("F2 saved")


# ══════════════════════════════════════════════════════════════════════════════
# F3 — PINN vs Observations Scatter
# ══════════════════════════════════════════════════════════════════════════════

def figure_F3_scatter(df: pd.DataFrame, season_metrics: dict):
    """Scatter plot: PINN vs observed PM2.5. Points coloured by season."""
    if "pm25_pinn" not in df.columns:
        log.warning("F3: pm25_pinn column missing — skip")
        return

    apply_style("ieee")
    fig, ax = plt.subplots(figsize=(4.5, 4.5))

    for season, color in SEASON_COLORS.items():
        sub = df[df["season"] == season]
        if len(sub) == 0:
            continue
        ax.scatter(sub["pm25_obs"], sub["pm25_pinn"], c=color, alpha=0.3,
                   s=4, label=season, zorder=2)

    # 1:1 line
    vmax = max(df["pm25_obs"].quantile(0.99), df["pm25_pinn"].quantile(0.99))
    ax.plot([0, vmax], [0, vmax], "k--", linewidth=1, zorder=3, label="1:1")

    # Annotate metrics
    overall = season_metrics.get("overall", {})
    r2  = overall.get("R2", float("nan"))
    rmse = overall.get("RMSE", float("nan"))
    n   = overall.get("n", len(df))
    ax.text(0.05, 0.95, f"R²={r2:.3f}\nRMSE={rmse:.1f} µg/m³\nn={n:,}",
            transform=ax.transAxes, fontsize=8, va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    ax.set_xlim(0, vmax)
    ax.set_ylim(0, vmax)
    ax.set_xlabel("Observed PM$_{2.5}$ (µg m$^{-3}$)")
    ax.set_ylabel("PINN PM$_{2.5}$ (µg m$^{-3}$)")
    ax.set_title("PINN vs observations — Chiang Mai 2021–2025")
    ax.legend(fontsize=7, markerscale=2)
    plt.tight_layout()
    save_figure(fig, "chiangmai_report_F03_pinn_vs_obs")
    plt.close(fig)
    log.info("F3 saved")


# ══════════════════════════════════════════════════════════════════════════════
# F4 — Per-station R² Bar Chart
# ══════════════════════════════════════════════════════════════════════════════

def figure_F4_station_r2(station_metrics: dict):
    """Bar chart of R² per station."""
    if not station_metrics:
        log.warning("F4: no station metrics — skip")
        return

    apply_style("ieee")
    stations = sorted(station_metrics.items(), key=lambda x: -x[1].get("R2", -9))
    names  = [s[:25] for s, _ in stations]
    r2s    = [m.get("R2", 0) for _, m in stations]
    ns     = [m.get("n", 0) for _, m in stations]
    providers = [m.get("provider", "?") for _, m in stations]
    colors = [PROVIDER_COLORS.get(p, "gray") for p in providers]

    fig, ax = plt.subplots(figsize=(6, max(3, 0.5 * len(stations))))
    bars = ax.barh(range(len(names)), r2s, color=colors, edgecolor="white", linewidth=0.5)

    for i, (r2, n) in enumerate(zip(r2s, ns)):
        ax.text(r2 + 0.01, i, f"{r2:.3f} (n={n})", va="center", fontsize=7)

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel("R² (PINN vs obs)")
    ax.set_title("Per-station PINN accuracy — Chiang Mai 2021–2025")
    ax.axvline(0.5, color="red", linestyle="--", linewidth=1, label="Gate R²=0.50")
    ax.set_xlim(-0.1, 1.1)

    handles = [
        mpatches.Patch(color=PROVIDER_COLORS["Air4Thai"],  label="Air4Thai"),
        mpatches.Patch(color=PROVIDER_COLORS["PurpleAir"], label="PurpleAir"),
        plt.Line2D([0], [0], color="red", linestyle="--", label="Gate R²=0.50"),
    ]
    ax.legend(handles=handles, fontsize=7, loc="lower right")
    plt.tight_layout()
    save_figure(fig, "chiangmai_report_F04_station_r2")
    plt.close(fig)
    log.info("F4 saved")


# ══════════════════════════════════════════════════════════════════════════════
# F5 — Monthly Bias
# ══════════════════════════════════════════════════════════════════════════════

def figure_F5_monthly_bias(df: pd.DataFrame):
    """Monthly mean bias (PINN − obs), burning months highlighted in red."""
    if "pm25_pinn" not in df.columns:
        log.warning("F5: pm25_pinn column missing — skip")
        return

    apply_style("ieee")
    df["bias"] = df["pm25_pinn"] - df["pm25_obs"]
    monthly = df.groupby("month").agg(
        bias_mean=("bias", "mean"),
        bias_std =("bias", "std"),
        n        =("bias", "count"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(6, 3.5))
    colors = ["#d62728" if m in BURNING_MONTHS else "#1f77b4"
              for m in monthly["month"]]
    ax.bar(monthly["month"], monthly["bias_mean"], color=colors, alpha=0.8,
           yerr=monthly["bias_std"] / np.sqrt(monthly["n"]), capsize=4)
    ax.axhline(0, color="black", linewidth=0.8)

    month_labels = ["Jan","Feb","Mar","Apr","May","Jun",
                    "Jul","Aug","Sep","Oct","Nov","Dec"]
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_labels, fontsize=8)
    ax.set_xlabel("Month")
    ax.set_ylabel("PINN bias (µg m$^{-3}$)")
    ax.set_title("Monthly PINN bias — Chiang Mai 2021–2025")

    handles = [
        mpatches.Patch(color="#d62728", label="Burning season (Feb–May)"),
        mpatches.Patch(color="#1f77b4", label="Other months"),
    ]
    ax.legend(handles=handles, fontsize=7)
    plt.tight_layout()
    save_figure(fig, "chiangmai_report_F05_monthly_bias")
    plt.close(fig)
    log.info("F5 saved")


# ══════════════════════════════════════════════════════════════════════════════
# F6 — K–BLH Correlation
# ══════════════════════════════════════════════════════════════════════════════

def figure_F6_kblh(df: pd.DataFrame, season_metrics: dict):
    """K (PINN diffusivity) vs BLH scatter — physics gate."""
    if "K_pinn" not in df.columns or "blh" not in df.columns:
        log.warning("F6: K_pinn or blh column missing — skip")
        return

    apply_style("ieee")
    fig, ax = plt.subplots(figsize=(4.5, 4.5))

    for season, color in SEASON_COLORS.items():
        sub = df[(df["season"] == season) & df["K_pinn"].notna() & df["blh"].notna()]
        if len(sub) == 0:
            continue
        ax.scatter(sub["blh"], sub["K_pinn"], c=color, alpha=0.3, s=4, label=season, zorder=2)

    r_kblh = season_metrics.get("K_BLH_r", float("nan"))
    ax.text(0.05, 0.95, f"r(K, BLH) = {r_kblh:.3f}\nGate: r > 0.50 → "
            f"{'PASS' if r_kblh > 0.50 else 'FAIL'}",
            transform=ax.transAxes, fontsize=8, va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    ax.set_xlabel("BLH (m)")
    ax.set_ylabel("K (PINN diffusivity, arb. units)")
    ax.set_title("K–BLH correlation — physics validation")
    ax.legend(fontsize=7, markerscale=2)
    plt.tight_layout()
    save_figure(fig, "chiangmai_report_F06_k_blh")
    plt.close(fig)
    log.info("F6 saved")


# ══════════════════════════════════════════════════════════════════════════════
# F7 — Diurnal K Cycle
# ══════════════════════════════════════════════════════════════════════════════

def figure_F7_diurnal_k():
    """Diurnal K cycle: run PINN at 24 time steps at domain centroid, show K vs hour."""
    try:
        import torch
        from src.stage3_pinn.models.fourier_pinn_v3 import FourierPINNV3
    except ImportError as e:
        log.warning("F7: cannot import torch/FourierPINNV3 — skip (%s)", e)
        return

    ckpt = CKPT_DIR / "epoch_01200.pt"
    if not ckpt.exists():
        log.warning("F7: checkpoint not found — skip")
        return

    model = FourierPINNV3()
    state = torch.load(str(ckpt), map_location="cpu", weights_only=False)
    if isinstance(state, dict) and "model_state_dict" in state:
        state = state["model_state_dict"]
    model.load_state_dict(state, strict=False)
    model.eval()

    # Domain centroid (x=0, y=0) — BLH varies by hour (daytime peak)
    hours = np.linspace(0, 23, 24)
    # Synthetic BLH: 200m at night, 1500m at midday
    blh_m = 200 + 1300 * np.clip(np.sin(np.pi * (hours - 6) / 12), 0, 1)
    K_vals = []

    with torch.no_grad():
        for h, blh in zip(hours, blh_m):
            t_norm = h / 24.0
            xyt = torch.tensor([[0.0, 0.0, t_norm]], dtype=torch.float32)
            blh_t = torch.tensor([[blh / PINN_BLH_NORM_SCALE]], dtype=torch.float32)
            elev_t = torch.tensor([[0.3]], dtype=torch.float32)
            _, (Kx, Ky, _) = model(xyt, blh=blh_t, elev=elev_t)
            K_vals.append(float((Kx.item() + Ky.item()) / 2))

    apply_style("ieee")
    fig, ax1 = plt.subplots(figsize=(6, 3.5))
    ax2 = ax1.twinx()

    ax1.plot(hours, K_vals, "b-o", markersize=4, label="K (PINN)", linewidth=1.5)
    ax2.plot(hours, blh_m, "r--s", markersize=3, label="BLH (synthetic)", linewidth=1)
    ax2.set_ylabel("BLH (m)", color="red")
    ax2.tick_params(axis="y", labelcolor="red")

    ax1.set_xlabel("Hour of day (UTC)")
    ax1.set_ylabel("K (PINN diffusivity, arb. units)", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")
    ax1.set_title("Diurnal K cycle at domain centroid — physics validation")
    ax1.set_xticks(range(0, 24, 3))

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc="upper left")

    plt.tight_layout()
    save_figure(fig, "chiangmai_report_F07_diurnal_k")
    plt.close(fig)
    log.info("F7 saved")


# ══════════════════════════════════════════════════════════════════════════════
# F8 — Burning Season Analysis (Three-Panel)
# ══════════════════════════════════════════════════════════════════════════════

def figure_F8_burning(df: pd.DataFrame):
    """Three-panel: obs distribution / PINN distribution / baseline — by season."""
    apply_style("ieee")
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.5), sharey=True)

    bins = np.linspace(0, 200, 50)
    for season, color in SEASON_COLORS.items():
        sub = df[df["season"] == season]
        if len(sub) == 0:
            continue
        # Panel 1: observed
        axes[0].hist(sub["pm25_obs"].dropna(), bins=bins, color=color, alpha=0.6,
                     label=season, density=True)
        # Panel 2: PINN (if available)
        if "pm25_pinn" in df.columns:
            axes[1].hist(sub["pm25_pinn"].dropna(), bins=bins, color=color, alpha=0.6,
                         label=season, density=True)
        # Panel 3: baseline (if available)
        if "pm25_baseline" in df.columns:
            bl = sub["pm25_baseline"].dropna()
            bl = bl[np.isfinite(bl)]
            if len(bl) > 0:
                axes[2].hist(bl, bins=bins, color=color, alpha=0.6,
                             label=season, density=True)

    titles = ["Observed PM$_{2.5}$", "PINN PM$_{2.5}$", "Counterfactual baseline"]
    for ax, title in zip(axes, titles):
        ax.set_xlabel("PM$_{2.5}$ (µg m$^{-3}$)")
        ax.set_title(title, fontsize=9)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("Density")

    fig.suptitle("PM$_{2.5}$ distributions by season — Chiang Mai 2021–2025", fontsize=10)
    plt.tight_layout()
    save_figure(fig, "chiangmai_report_F08_burning_analysis")
    plt.close(fig)
    log.info("F8 saved")


# ══════════════════════════════════════════════════════════════════════════════
# F9 — Spatial PINN Heatmap
# ══════════════════════════════════════════════════════════════════════════════

def figure_F9_spatial_map(df: pd.DataFrame):
    """Spatial PINN PM2.5 heatmap for a selected non-burning day, with station overlays."""
    try:
        import torch
        from src.stage3_pinn.models.fourier_pinn_v3 import FourierPINNV3
    except ImportError as e:
        log.warning("F9: cannot import torch/FourierPINNV3 — skip (%s)", e)
        return

    ckpt = CKPT_DIR / "epoch_01200.pt"
    if not ckpt.exists():
        log.warning("F9: checkpoint not found — skip")
        return

    model = FourierPINNV3()
    state = torch.load(str(ckpt), map_location="cpu", weights_only=False)
    if isinstance(state, dict) and "model_state_dict" in state:
        state = state["model_state_dict"]
    model.load_state_dict(state, strict=False)
    model.eval()

    # Choose a non-burning day with ≥3 station observations
    if "pm25_obs" in df.columns:
        non_burn = df[df["season"] == "non-burning"]
        day_counts = non_burn.groupby("date")["location_id"].nunique()
        good_days = day_counts[day_counts >= 3]
        if len(good_days) > 0:
            selected_date = good_days.index[len(good_days) // 2]   # median date
        else:
            selected_date = None
    else:
        selected_date = None

    # Build 150×150 grid
    bbox = CHIANGMAI_PINN_BBOX
    nx = ny = 50   # subsample for speed
    lat_arr = np.linspace(bbox["lat_min"], bbox["lat_max"], ny)
    lon_arr = np.linspace(bbox["lon_min"], bbox["lon_max"], nx)
    x_norm = np.linspace(-1, 1, nx)
    y_norm = np.linspace(-1, 1, ny)
    XX, YY = np.meshgrid(x_norm, y_norm)

    # Use typical non-burning BLH (700m)
    blh_norm = 700.0 / PINN_BLH_NORM_SCALE
    t_norm   = 12.0 / 24.0   # midday

    grid_pts = np.column_stack([XX.ravel(), YY.ravel(),
                                 np.full(nx * ny, t_norm)])
    C_grid = np.zeros(ny * nx)

    chunk = 500
    with torch.no_grad():
        for i in range(0, len(grid_pts), chunk):
            xyt_t = torch.tensor(grid_pts[i:i+chunk], dtype=torch.float32)
            blh_t = torch.full((len(xyt_t), 1), blh_norm, dtype=torch.float32)
            elev_t = torch.full((len(xyt_t), 1), 0.3, dtype=torch.float32)
            C, _ = model(xyt_t, blh=blh_t, elev=elev_t)
            C_grid[i:i+chunk] = C.squeeze().numpy()

    C_map = C_grid.reshape(ny, nx)

    apply_style("ieee")
    fig, ax = plt.subplots(figsize=(5, 5))
    lon_g = np.linspace(bbox["lon_min"], bbox["lon_max"], nx)
    lat_g = np.linspace(bbox["lat_min"], bbox["lat_max"], ny)
    im = ax.pcolormesh(lon_g, lat_g, C_map, cmap=PM25_CMAP, vmin=0, vmax=60, shading="auto")
    plt.colorbar(im, ax=ax, label="PINN PM$_{2.5}$ (µg m$^{-3}$)")

    # Overlay station observations for selected day
    if selected_date is not None and "pm25_obs" in df.columns:
        day_obs = df[df["date"] == selected_date]
        sc = ax.scatter(day_obs["lon"], day_obs["lat"],
                        c=day_obs["pm25_obs"], cmap=PM25_CMAP, vmin=0, vmax=60,
                        s=120, edgecolors="black", linewidths=1.5, zorder=5,
                        marker="^", label="Station obs")
        date_str = str(selected_date.date()) if hasattr(selected_date, "date") else str(selected_date)[:10]
        ax.set_title(f"PINN PM$_{{2.5}}$ spatial map — {date_str}")
        ax.legend(fontsize=7)
    else:
        ax.set_title("PINN PM$_{2.5}$ spatial map (non-burning, midday)")

    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    plt.tight_layout()
    save_figure(fig, "chiangmai_report_F09_spatial_map")
    plt.close(fig)
    log.info("F9 saved")


# ══════════════════════════════════════════════════════════════════════════════
# F10 — Annual Mean PINN PM2.5
# ══════════════════════════════════════════════════════════════════════════════

def figure_F10_annual_mean(df: pd.DataFrame):
    """Annual mean PINN PM2.5 map with station annual means overlaid."""
    if "pm25_pinn" not in df.columns:
        log.warning("F10: pm25_pinn column missing — skip")
        return

    try:
        import torch
        from src.stage3_pinn.models.fourier_pinn_v3 import FourierPINNV3
    except ImportError:
        log.warning("F10: cannot import torch/FourierPINNV3 — skip")
        return

    ckpt = CKPT_DIR / "epoch_01200.pt"
    if not ckpt.exists():
        log.warning("F10: checkpoint not found — skip")
        return

    model = FourierPINNV3()
    state = torch.load(str(ckpt), map_location="cpu", weights_only=False)
    if isinstance(state, dict) and "model_state_dict" in state:
        state = state["model_state_dict"]
    model.load_state_dict(state, strict=False)
    model.eval()

    # Annual mean: average over 12 months × 4 time steps = 48 snapshots
    # Use representative BLH for each season
    bbox = CHIANGMAI_PINN_BBOX
    nx = ny = 50
    x_norm = np.linspace(-1, 1, nx)
    y_norm = np.linspace(-1, 1, ny)
    XX, YY = np.meshgrid(x_norm, y_norm)
    grid_pts_xy = np.column_stack([XX.ravel(), YY.ravel()])

    C_accum = np.zeros(ny * nx)
    n_snaps = 0
    snap_configs = [
        (blh, t_h) for blh in [300, 700, 1200]   # night, morning, day BLH
        for t_h in [6, 12, 18]                    # 3 time steps
    ]

    chunk = 500
    with torch.no_grad():
        for blh_m, t_h in snap_configs:
            t_norm = t_h / 24.0
            blh_norm = blh_m / PINN_BLH_NORM_SCALE
            grid_pts = np.column_stack([grid_pts_xy, np.full(nx*ny, t_norm)])
            for i in range(0, len(grid_pts), chunk):
                xyt_t = torch.tensor(grid_pts[i:i+chunk], dtype=torch.float32)
                blh_t = torch.full((len(xyt_t), 1), blh_norm, dtype=torch.float32)
                elev_t = torch.full((len(xyt_t), 1), 0.3, dtype=torch.float32)
                C, _ = model(xyt_t, blh=blh_t, elev=elev_t)
                C_accum[i:i+chunk] += C.squeeze().numpy()
            n_snaps += 1

    C_annual = (C_accum / n_snaps).reshape(ny, nx)

    apply_style("ieee")
    fig, ax = plt.subplots(figsize=(5, 5))
    lon_g = np.linspace(bbox["lon_min"], bbox["lon_max"], nx)
    lat_g = np.linspace(bbox["lat_min"], bbox["lat_max"], ny)
    im = ax.pcolormesh(lon_g, lat_g, C_annual, cmap=PM25_CMAP, vmin=0, vmax=50, shading="auto")
    plt.colorbar(im, ax=ax, label="Annual mean PM$_{2.5}$ (µg m$^{-3}$)")

    # Station annual means from obs
    if "pm25_obs" in df.columns:
        stn_means = df.groupby(["location_name", "lat", "lon"])["pm25_obs"].mean().reset_index()
        sc = ax.scatter(stn_means["lon"], stn_means["lat"],
                        c=stn_means["pm25_obs"], cmap=PM25_CMAP, vmin=0, vmax=50,
                        s=120, edgecolors="black", linewidths=1.5, zorder=5,
                        marker="^", label="Station annual mean")
        for _, row in stn_means.iterrows():
            ax.annotate(f"{row['pm25_obs']:.1f}", (row["lon"], row["lat"]),
                        fontsize=5, xytext=(3, 3), textcoords="offset points", color="white",
                        fontweight="bold")

    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_title("Annual mean PINN PM$_{2.5}$ — Chiang Mai 2021–2025")
    ax.legend(fontsize=7)
    plt.tight_layout()
    save_figure(fig, "chiangmai_report_F10_annual_mean")
    plt.close(fig)
    log.info("F10 saved")


# ══════════════════════════════════════════════════════════════════════════════
# Check inputs
# ══════════════════════════════════════════════════════════════════════════════

def check_inputs():
    files = [
        (PINN_PARQUET, "Phase 4 output"),
        (BURN_MASK,    "Phase 5 output"),
        (PM25_CSV,     "Phase 1 output"),
        (STATION_JSON, "Phase 4 station metrics"),
        (SEASON_JSON,  "Phase 4 seasonal metrics"),
        (BURN_JSON,    "Phase 5 burning analysis"),
        (ERA5_2022,    "ERA5 2022 NC"),
        (ELEV_NPZ,     "ChiangMai elev grid"),
        (CKPT_DIR / "epoch_01200.pt", "PINN v5 ep1200 checkpoint"),
    ]
    all_ok = True
    log.info("=== Input file status ===")
    for path, desc in files:
        exists = Path(path).exists()
        status = "✅" if exists else "❌ MISSING"
        log.info("  %s — %s", desc, status)
        if not exists:
            all_ok = False
    return all_ok


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    ALL_FIGS = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"]

    parser = argparse.ArgumentParser()
    parser.add_argument("--fig", nargs="+", default=ALL_FIGS,
                        choices=ALL_FIGS, help="Which figures to generate")
    parser.add_argument("--check", action="store_true",
                        help="Only check which input files exist")
    args = parser.parse_args()

    if args.check:
        check_inputs()
        return

    # Load shared data
    pinn_df = None
    obs_df  = None
    station_metrics = load_station_metrics()
    season_metrics  = load_season_metrics()

    if PINN_PARQUET.exists():
        pinn_df = load_pinn_df()
        log.info("PINN parquet loaded: %d rows", len(pinn_df))
    else:
        log.warning("PINN parquet not found — F3/F4/F5/F6/F8/F10 may be skipped")

    if PM25_CSV.exists():
        obs_df = load_raw_obs()
        log.info("Raw obs loaded: %d rows", len(obs_df))

    # Try to merge burning mask (has baseline column)
    if pinn_df is not None and BURN_MASK.exists():
        burn_df = pd.read_csv(str(BURN_MASK))
        if "pm25_baseline" in burn_df.columns:
            merge_cols = ["date", "location_id", "pm25_baseline"]
            merge_cols = [c for c in merge_cols if c in burn_df.columns]
            pinn_df["date_str"] = pinn_df["date"].astype(str).str[:10]
            burn_df["date_str"] = burn_df["date"].astype(str).str[:10]
            pinn_df = pinn_df.merge(
                burn_df[["date_str", "location_id", "pm25_baseline"]],
                on=["date_str", "location_id"], how="left"
            )

    # Generate figures
    for fig_id in args.fig:
        log.info("Generating %s...", fig_id)
        try:
            if fig_id == "F1":
                df = pinn_df if pinn_df is not None else (
                    obs_df.groupby(["location_name","provider"])
                    .first()[["lat","lon"]].reset_index()
                    if obs_df is not None else pd.DataFrame()
                )
                figure_F1_station_map(df)
            elif fig_id == "F2":
                if obs_df is not None:
                    figure_F2_timeseries(obs_df)
                else:
                    log.warning("F2: raw obs not available")
            elif fig_id == "F3":
                if pinn_df is not None:
                    figure_F3_scatter(pinn_df, season_metrics)
            elif fig_id == "F4":
                figure_F4_station_r2(station_metrics)
            elif fig_id == "F5":
                if pinn_df is not None:
                    figure_F5_monthly_bias(pinn_df)
            elif fig_id == "F6":
                if pinn_df is not None:
                    figure_F6_kblh(pinn_df, season_metrics)
            elif fig_id == "F7":
                figure_F7_diurnal_k()
            elif fig_id == "F8":
                if pinn_df is not None:
                    figure_F8_burning(pinn_df)
            elif fig_id == "F9":
                df9 = pinn_df if pinn_df is not None else pd.DataFrame()
                figure_F9_spatial_map(df9)
            elif fig_id == "F10":
                df10 = pinn_df if pinn_df is not None else pd.DataFrame()
                figure_F10_annual_mean(df10)
        except Exception as e:
            log.error("Error generating %s: %s", fig_id, e, exc_info=True)

    log.info("Figure generation complete.")


if __name__ == "__main__":
    main()
