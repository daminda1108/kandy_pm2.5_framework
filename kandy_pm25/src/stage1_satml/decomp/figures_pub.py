"""
figures_pub.py — publication-grade Kandy PM2.5 maps following satellite-AQ
literature conventions (van Donkelaar/ACAG, China multi-decade PM2.5 studies):

  - smooth continuous rendering (1 km field, not blocky pixels)
  - ONE shared colour scale across year panels (cross-year comparable)
  - WHO-referenced colourbar (AQG 5; Interim Targets 10/15/25/35 µg/m³ ticks)
  - geographic context: terrain contour lines, labelled landmarks, scale bar,
    north arrow, lat/lon graticule

Outputs (results/figures/kandy_decomp/pub/):
  annual_{year}_{cmap}.png        single polished annual map
  multiyear_{cmap}.png            2×3 grid 2019–2024, shared WHO scale
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrow
from scipy.ndimage import zoom

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
try:
    from src.utils.plot_style import apply_style
    apply_style("ieee")
except Exception:
    pass

DECOMP = HERE / "data" / "processed" / "decomp"
ELEV_NPZ = HERE / "data" / "processed" / "pinn_inputs" / "kandy_elev_grid_100m.npz"
OUT = HERE / "results" / "figures" / "kandy_decomp" / "pub"
OUT.mkdir(parents=True, exist_ok=True)

VMIN, VMAX = 12, 40                    # shared scale spanning WHO IT-3..>IT-1
WHO_TICKS = [15, 25, 35]               # IT-3, IT-2, IT-1 (AQG=5 noted separately)
LANDMARKS = {                          # (lat, lon, label, marker)
    "Kandy city": (7.2906, 80.6337, "o"),
    "NIFS/KOALA": (7.2675, 80.5985, "^"),
    "Hantana FECT": (7.265, 80.625, "s"),
}
YEARS = list(range(2019, 2025))


def _annual_pm(year):
    d = pd.read_parquet(DECOMP / f"kandy_decomp_predictions_{year}.parquet",
                        columns=["lat", "lon", "pm25_q50"])
    g = d.groupby(["lat", "lon"])["pm25_q50"].mean().reset_index()
    Z = g.pivot(index="lat", columns="lon", values="pm25_q50")
    return Z.values, Z.index.values, Z.columns.values


def _elev():
    z = np.load(ELEV_NPZ)
    return z["elev"], z["lat_grid"], z["lon_grid"]


def _scale_bar(ax, lats, lons, km=5):
    lat0 = float(np.mean(lats))
    deg = km / (111.0 * np.cos(np.radians(lat0)))
    x0 = lons.min() + 0.12 * (lons.max() - lons.min())
    y0 = lats.min() + 0.07 * (lats.max() - lats.min())
    ax.plot([x0, x0 + deg], [y0, y0], "k-", lw=2.2, solid_capstyle="butt")
    ax.text(x0 + deg / 2, y0 + 0.012 * (lats.max() - lats.min()), f"{km} km",
            ha="center", va="bottom", fontsize=7)


def _north_arrow(ax, lats, lons):
    rx, ry = lons.max() - lons.min(), lats.max() - lats.min()
    x = lons.max() - 0.08 * rx
    ytip = lats.max() - 0.07 * ry
    ax.annotate("N", xy=(x, ytip), xytext=(x, ytip - 0.11 * ry),
                ha="center", va="center", fontsize=8, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="k", lw=1.1))


def _draw(ax, Z, lats, lons, cmap, show_terrain=True, show_marks=True,
          smooth=8):
    Zs = zoom(Z, smooth, order=3)      # cubic upsample → smooth 1 km field
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    im = ax.imshow(Zs, origin="lower", extent=ext, cmap=cmap, vmin=VMIN,
                   vmax=VMAX, aspect="auto", interpolation="bilinear")
    if show_terrain:
        elev, ela, elo = _elev()
        ax.contour(elo, ela, elev, levels=range(500, 1300, 150),
                   colors="k", linewidths=0.35, alpha=0.30)
    if show_marks:
        for name, (la, lo, mk) in LANDMARKS.items():
            ax.plot(lo, la, mk, mfc="white", mec="k", mew=0.8, ms=5, zorder=5)
    ax.set_xlim(lons.min(), lons.max()); ax.set_ylim(lats.min(), lats.max())
    return im


def annual_map(year=2024, cmap="YlOrRd"):
    Z, lats, lons = _annual_pm(year)
    fig, ax = plt.subplots(figsize=(6.4, 5.6), constrained_layout=True)
    im = _draw(ax, Z, lats, lons, cmap)
    for name, (la, lo, mk) in LANDMARKS.items():
        ax.annotate(name, (lo, la), xytext=(4, 4), textcoords="offset points",
                    fontsize=7, color="k",
                    path_effects=[])
    _scale_bar(ax, lats, lons); _north_arrow(ax, lats, lons)
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    ax.set_title(f"Kandy annual-mean PM₂.₅, {year}  "
                 f"(basin mean {np.nanmean(Z):.1f} µg m⁻³)", fontsize=10)
    cb = fig.colorbar(im, ax=ax, label="PM₂.₅ (µg m⁻³)", extend="both",
                      ticks=[VMIN, 15, 25, 35, VMAX], shrink=0.85)
    cb.ax.set_yticklabels(["12", "15  WHO IT-3", "25  IT-2", "35  IT-1", "40"],
                          fontsize=7)
    fig.savefig(OUT / f"annual_{year}_{cmap}.png", dpi=240, bbox_inches="tight")
    plt.close(fig)


def multiyear_grid(cmap="YlOrRd"):
    fig, axes = plt.subplots(2, 3, figsize=(13, 8.4), constrained_layout=True)
    im = None
    for ax, year in zip(axes.ravel(), YEARS):
        Z, lats, lons = _annual_pm(year)
        im = _draw(ax, Z, lats, lons, cmap, show_marks=False)
        ax.plot(80.6337, 7.2906, "o", mfc="white", mec="k", mew=0.8, ms=4)
        ttl = f"{year}   {np.nanmean(Z):.1f} µg m⁻³"
        if year == 2024:
            ttl += " *"
            ax.text(0.5, 0.02, "* level: 2023 VanD proxy", transform=ax.transAxes,
                    ha="center", va="bottom", fontsize=6.5, color="white")
        ax.set_title(ttl, fontsize=10)
        ax.set_xticks([]); ax.set_yticks([])
    _scale_bar(axes[1, 0], *_annual_pm(2019)[1:]); _north_arrow(axes[0, 2], *_annual_pm(2019)[1:])
    cb = fig.colorbar(im, ax=axes, label="PM₂.₅ (µg m⁻³)", extend="both",
                      ticks=[VMIN, 15, 25, 35, VMAX], shrink=0.6)
    cb.ax.set_yticklabels(["12", "15  WHO IT-3", "25  IT-2", "35  IT-1", "40"],
                          fontsize=8)
    fig.suptitle("Kandy annual-mean PM₂.₅ 2019–2024 — decomposition "
                 "(all of Kandy exceeds WHO AQG of 5 µg m⁻³)", fontsize=12)
    fig.savefig(OUT / f"multiyear_{cmap}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUT / f'multiyear_{cmap}.png'} + annual maps")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmap", default="turbo")
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()
    annual_map(args.year, args.cmap)
    multiyear_grid(args.cmap)
