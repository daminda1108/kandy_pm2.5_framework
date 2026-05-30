"""
compare_versions.py — Bowatte deliverable: side-by-side annual-mean Kandy PM2.5
maps across the modelling progression (v13 → v15 → v16a → decomposition).

Tells the honest story:
  v13 (ConvCNP N=3)   — spatially smoothed-out (KTM-dominated)
  v15 (ConvCNP N=10)  — spatial INVERSION (road r=-0.41, urban core too clean)
  v16a (ConvCNP N=3*) — signs correct but magnitude inflated (32.3 vs KOALA 24.5)
  decomposition       — magnitude-correct (26.1), correct signs, conformal UQ

Output: results/figures/kandy_decomp/version_comparison.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
try:
    from src.utils.plot_style import apply_style, PM25_CMAP
    apply_style("ieee")
    CMAP = PM25_CMAP
except Exception:
    CMAP = "YlOrBr"

DATA = HERE / "data" / "processed"
OUT = HERE / "results" / "figures" / "kandy_decomp"
OUT.mkdir(parents=True, exist_ok=True)

PANELS = [
    ("v13 ConvCNP (N=3)", DATA / "kandy_zero_shot/kandy_predictions_20240101_0000_n8784.parquet",
     "pm25_pred", "smoothed-out\n(KTM-dominated)"),
    ("v15 ConvCNP (N=10)", DATA / "kandy_zero_shot/kandy_predictions_20240101_0000_n8784_v15mondrian.parquet",
     "pm25_pred", "spatial inversion\n(urban core too clean)"),
    ("v16a ConvCNP (N=3 ablation)", DATA / "kandy_zero_shot/kandy_predictions_20240101_0000_n8784_v16amondrian.parquet",
     "pm25_pred", "signs correct,\nmagnitude inflated 32.3"),
    ("Decomposition T·S·M (v1)", DATA / "decomp/kandy_decomp_predictions_2024.parquet",
     "pm25_q50", "magnitude-correct 26.1,\ncorrect signs, conformal UQ"),
]


def annual_grid(path, col):
    d = pd.read_parquet(path, columns=["lat", "lon", col])
    g = d.groupby(["lat", "lon"])[col].mean().reset_index()
    Z = g.pivot(index="lat", columns="lon", values=col)
    return Z.values, Z.index.values, Z.columns.values


def main():
    grids = [(t, *annual_grid(p, c), note) for t, p, c, note in PANELS]
    vmin = min(np.nanmin(Z) for _, Z, *_ in grids)
    vmax = max(np.nanmax(Z) for _, Z, *_ in grids)
    # clip extreme tails for a readable shared scale
    vmin, vmax = max(0, vmin), min(vmax, 40)

    fig, ax = plt.subplots(1, 4, figsize=(17, 4.6), constrained_layout=True)
    for a, (title, Z, lats, lons, note) in zip(ax, grids):
        im = a.pcolormesh(lons, lats, Z, cmap=CMAP, vmin=vmin, vmax=vmax, shading="auto")
        a.set_title(title, fontsize=10)
        a.text(0.5, -0.16, note, transform=a.transAxes, ha="center", va="top",
               fontsize=8, color="#444")
        a.text(0.04, 0.96, f"mean {np.nanmean(Z):.1f}", transform=a.transAxes,
               ha="left", va="top", fontsize=9, fontweight="bold",
               bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.7))
        a.set_xlabel("lon"); a.set_xticks([])
        a.set_yticks([])
    ax[0].set_ylabel("lat")
    fig.colorbar(im, ax=ax, label="annual-mean PM₂.₅ (µg m⁻³)", shrink=0.8)
    fig.suptitle("Kandy 2024 annual-mean PM₂.₅ — modelling progression "
                 "(KOALA anchor 24.5)", fontsize=12)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"version_comparison.{ext}", dpi=200, bbox_inches="tight")
    print(f"Wrote {OUT / 'version_comparison.png'}")
    for title, Z, *_ , note in grids:
        f = Z.ravel()
        print(f"  {title:<32} mean {np.nanmean(Z):5.1f}  "
              f"contrast(p90/p10) {np.nanquantile(f,0.9)/np.nanquantile(f,0.1):.2f}×")


if __name__ == "__main__":
    main()
