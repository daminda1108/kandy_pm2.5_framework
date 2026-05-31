"""
figures_spatial.py — publication spatial-variation maps from the cached
climatology (2019-2023 multi-year), turbo, terrain context, shared scales:

  seasonal_maps()  — DJF/MAM/JJA/SON mean maps (shared scale; magnitude + pattern)
  diurnal_maps()   — 6 hours across the day showing the basin "breathe"
                     (nocturnal valley-pooling → midday mixing — the M physics)

Outputs: results/figures/kandy_decomp/pub/{seasonal_turbo,diurnal_turbo}.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
from src.stage1_satml.decomp.figures_pub import (
    _draw, _scale_bar, _north_arrow, OUT, DECOMP)
try:
    from src.utils.plot_style import apply_style
    apply_style("ieee")
except Exception:
    pass

CMAP = "turbo"


def _cb(fig, im, axes, vmin, vmax, who=True):
    ticks = sorted(set([vmin] + [t for t in (15, 25, 35) if vmin < t < vmax] + [vmax]))
    cb = fig.colorbar(im, ax=axes, label="PM₂.₅ (µg m⁻³)", extend="both",
                      ticks=ticks, shrink=0.7)
    if who:
        labs = {15: "15  WHO IT-3", 25: "25  IT-2", 35: "35  IT-1"}
        cb.ax.set_yticklabels([labs.get(int(t), f"{int(t)}") for t in ticks], fontsize=7)


def seasonal_maps():
    z = np.load(DECOMP / "climatology.npz")
    lats, lons, seas = z["lats"], z["lons"], z["seasonal"]
    names = ["DJF", "MAM", "JJA", "SON"]
    vmin, vmax = 12, 40
    fig, ax = plt.subplots(1, 4, figsize=(15, 4.4), constrained_layout=True)
    im = None
    for a, m, nm in zip(ax, seas, names):
        im = _draw(a, m, lats, lons, CMAP, show_marks=False, vmin=vmin, vmax=vmax)
        a.plot(80.6337, 7.2906, "o", mfc="white", mec="k", mew=0.8, ms=4)
        a.set_title(f"{nm}   {np.nanmean(m):.1f} µg m⁻³", fontsize=10)
        a.set_xticks([]); a.set_yticks([])
    _scale_bar(ax[0], lats, lons); _north_arrow(ax[3], lats, lons)
    _cb(fig, im, ax, vmin, vmax)
    fig.suptitle("Kandy seasonal-mean PM₂.₅ (2019–2023) — wet JJA monsoon minimum, "
                 "dry-season + inter-monsoon peaks", fontsize=12)
    fig.savefig(OUT / "seasonal_turbo.png", dpi=220, bbox_inches="tight")
    plt.close(fig); print("Wrote", OUT / "seasonal_turbo.png")


def diurnal_maps(hours=(3, 7, 11, 15, 19, 23)):
    z = np.load(DECOMP / "climatology.npz")
    lats, lons, hourly = z["lats"], z["lons"], z["hourly"]
    sel = [hourly[h] for h in hours]
    vmin = float(np.floor(min(np.nanmin(m) for m in sel)))
    vmax = float(np.ceil(max(np.nanmax(m) for m in sel)))
    fig, ax = plt.subplots(2, 3, figsize=(13, 8.4), constrained_layout=True)
    im = None
    for a, h in zip(ax.ravel(), hours):
        im = _draw(a, hourly[h], lats, lons, CMAP, show_marks=False, vmin=vmin, vmax=vmax)
        a.plot(80.6337, 7.2906, "o", mfc="white", mec="k", mew=0.8, ms=4)
        a.set_title(f"{h:02d}:00 LT   {np.nanmean(hourly[h]):.1f} µg m⁻³", fontsize=10)
        a.set_xticks([]); a.set_yticks([])
    _scale_bar(ax[1, 0], lats, lons); _north_arrow(ax[0, 2], lats, lons)
    _cb(fig, im, ax, vmin, vmax, who=False)
    fig.suptitle("Kandy diurnal PM₂.₅ spatial cycle (2019–2023) — nocturnal "
                 "valley-pooling (high, confined) → midday mixing (low, uniform)",
                 fontsize=12)
    fig.savefig(OUT / "diurnal_turbo.png", dpi=220, bbox_inches="tight")
    plt.close(fig); print("Wrote", OUT / "diurnal_turbo.png")


if __name__ == "__main__":
    seasonal_maps()
    diurnal_maps()
