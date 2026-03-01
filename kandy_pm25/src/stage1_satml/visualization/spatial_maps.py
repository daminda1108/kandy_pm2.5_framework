"""
spatial_maps.py — Publication-quality spatial maps for Stage 1 PM2.5 output.

Generates:
  1. Annual mean PM2.5 map (1 km grid)
  2. Seasonal PM2.5 maps (NE Monsoon, SW Monsoon, Inter-Monsoon)
  3. Prediction uncertainty map (width of 90% PI)
  4. Trend map (slope of PM2.5 vs year, 2019–2025)
  5. Physical feature maps (VVC, TII, KFP overlaid)

All maps use Kandy-specific colorscales (WHO guideline thresholds annotated).
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    KANDY_BBOX, LOG_FORMAT, LOG_DATEFMT,
    FIGURES_DIR, WHO_PM25_24H_GUIDELINE, WHO_PM25_ANNUAL_GUIDELINE
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("spatial_maps")

SEASON_MONTHS = {
    "NE Monsoon (Dec\u2013Mar)":    [12, 1, 2, 3],
    "SW Monsoon (May\u2013Sep)":    [5, 6, 7, 8, 9],
    "Inter-Monsoon (Apr+Oct-Nov)": [4, 10, 11],
}


def _get_plt():
    try:
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
        return plt, mcolors
    except ImportError:
        raise ImportError("matplotlib is required for spatial maps. Run: pip install matplotlib")


def plot_annual_mean_map(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    pm25_col: str = "pm25_pred",
    date_col: str = "date",
    save_path: Optional[str] = None,
) -> None:
    """
    Plot annual mean PM2.5 concentration map across the Kandy domain.
    Annotates WHO 24h guideline (15 µg/m³) and annual guideline (5 µg/m³).
    """
    plt, mcolors = _get_plt()
    annual = df.groupby([lat_col, lon_col])[pm25_col].mean().reset_index()

    fig, ax = plt.subplots(figsize=(8, 7))
    sc = ax.scatter(
        annual[lon_col], annual[lat_col], c=annual[pm25_col],
        cmap="YlOrRd", s=12, vmin=0, vmax=60, alpha=0.85,
    )
    cbar = plt.colorbar(sc, ax=ax, label="PM2.5 (µg/m³)")
    cbar.ax.axhline(y=WHO_PM25_ANNUAL_GUIDELINE, color="green", lw=1.5, label=f"WHO annual ({WHO_PM25_ANNUAL_GUIDELINE})")
    cbar.ax.axhline(y=WHO_PM25_24H_GUIDELINE, color="orange", lw=1.5)

    ax.set_title("Annual Mean PM2.5 — Kandy Valley (Stage 1 Sat-ML)", fontsize=13)
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    ax.grid(alpha=0.3)
    _save_or_show(fig, save_path or str(FIGURES_DIR / "annual_mean_pm25.png"))


def plot_seasonal_maps(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    pm25_col: str = "pm25_pred",
    date_col: str = "date",
    save_path: Optional[str] = None,
) -> None:
    """Plot 3-panel seasonal PM2.5 maps (NE Monsoon, SW Monsoon, Inter-Monsoon)."""
    plt, _ = _get_plt()
    df_plot = df.copy()
    df_plot["_month"] = pd.to_datetime(df_plot[date_col]).dt.month

    fig, axes = plt.subplots(1, 3, figsize=(18, 5), constrained_layout=True)
    fig.suptitle("Seasonal PM2.5 Maps — Kandy Valley", fontsize=14)

    vmax = df_plot[pm25_col].quantile(0.98)
    for ax, (season, months) in zip(axes, SEASON_MONTHS.items()):
        mask = df_plot["_month"].isin(months)
        seasonal = df_plot[mask].groupby([lat_col, lon_col])[pm25_col].mean().reset_index()
        sc = ax.scatter(
            seasonal[lon_col], seasonal[lat_col], c=seasonal[pm25_col],
            cmap="YlOrRd", s=8, vmin=0, vmax=vmax, alpha=0.85,
        )
        plt.colorbar(sc, ax=ax, label="PM2.5 (µg/m³)")
        ax.set_title(season, fontsize=11)
        ax.set_xlabel("Lon"); ax.set_ylabel("Lat")
        ax.grid(alpha=0.3)

    _save_or_show(fig, save_path or str(FIGURES_DIR / "seasonal_pm25_maps.png"))


def plot_uncertainty_map(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    q05_col: str = "pm25_q05",
    q95_col: str = "pm25_q95",
    save_path: Optional[str] = None,
) -> None:
    """
    Plot map of mean PI width — where Stage 1 is most uncertain.
    Highest uncertainty expected during SW Monsoon (cloud gaps).
    """
    plt, _ = _get_plt()
    df_unc = df.copy()
    df_unc["pi_width"] = df_unc[q95_col] - df_unc[q05_col]
    spatial = df_unc.groupby([lat_col, lon_col])["pi_width"].mean().reset_index()

    fig, ax = plt.subplots(figsize=(7, 6))
    sc = ax.scatter(
        spatial[lon_col], spatial[lat_col], c=spatial["pi_width"],
        cmap="plasma", s=12, alpha=0.85,
    )
    plt.colorbar(sc, ax=ax, label="90% PI width (µg/m³)")
    ax.set_title("Stage 1 Prediction Uncertainty\n(mean 90% PI width)", fontsize=13)
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    ax.grid(alpha=0.3)
    _save_or_show(fig, save_path or str(FIGURES_DIR / "uncertainty_map.png"))


def _save_or_show(fig, path: str, show: bool = False) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    log.info(f"Figure saved → {path}")
    if not show:
        import matplotlib.pyplot as plt
        plt.close(fig)
