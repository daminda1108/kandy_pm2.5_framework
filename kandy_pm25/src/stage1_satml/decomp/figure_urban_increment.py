"""
figure_urban_increment.py — Akurana-anchored urban-increment SCENARIO figures.

Visualises the core-vs-area finding (assumption: Akurana 16.7 µg/m³ is a real
peri-urban level):
  (a) current decomposition source field  = S_emit_sat · L      (~uniform ~24)
  (b) Akurana-anchored urban-increment field (core 24.5 / peri 16.7 / highland)
  (c) the 3-tier classification from road + night-lights
Same YlOrRd / WHO scale on (a,b) so the redistribution is legible: the current
product paints the whole basin at core levels; anchoring to Akurana shows only
the core / Peradeniya-Rd zone is ~24 and the off-core basin drops to ~13-17.

Out: results/figures/kandy_decomp/urban_increment/{source_comparison,multiplier}.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap, TwoSlopeNorm

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
from src.stage1_satml.decomp.figures_pub import (  # noqa: E402
    _draw, _scale_bar, _north_arrow, LANDMARKS)

DEC = HERE / "data" / "processed" / "decomp"
OUT = HERE / "results" / "figures" / "kandy_decomp" / "urban_increment"
OUT.mkdir(parents=True, exist_ok=True)


def _akurana_note(ax, lats, lons):
    rx = lons.max() - lons.min()
    x = lons.min() + 0.5 * rx
    ax.annotate("↑ Akurana 16.7 (6 km N)", xy=(x, lats.max()),
                xytext=(x, lats.max() - 0.04 * (lats.max() - lats.min())),
                ha="center", va="top", fontsize=6.5, color="navy", fontweight="bold")


def main():
    sat = np.load(DEC / "S_emit_kandy.npz")
    ui = np.load(DEC / "S_emit_urban_increment.npz")
    lats, lons = sat["lats"], sat["lons"]
    L = float(ui["L_decomp"]); area_mean = float(ui["area_mean_implied"])
    C_core, C_peri, C_high = float(ui["C_core"]), float(ui["C_peri"]), float(ui["C_high"])
    tier = ui["tier"]

    field_cur = sat["S_emit"] * L                     # current source field µg/m³
    field_ui = np.where(tier == 2, C_core, np.where(tier == 0, C_high, C_peri)).astype(float)

    # ── Figure 1: absolute source fields + tier map ──
    vmin, vmax = 12, 26
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), constrained_layout=True)

    im = _draw(axes[0], field_cur, lats, lons, "YlOrRd", vmin=vmin, vmax=vmax)
    axes[0].set_title(f"(a) Current source field  $S_{{emit}}\\cdot L$\n"
                      f"basin {field_cur.mean():.1f} µg m⁻³  ·  contrast "
                      f"{field_cur.max()/field_cur.min():.2f}×", fontsize=9)

    _draw(axes[1], field_ui, lats, lons, "YlOrRd", vmin=vmin, vmax=vmax)
    axes[1].set_title(f"(b) Akurana-anchored urban increment\n"
                      f"core {C_core:.1f} / peri {C_peri:.1f} / highland {C_high:.1f}  ·  "
                      f"area-mean {area_mean:.1f}  ·  contrast {C_core/C_high:.2f}×",
                      fontsize=9)
    _akurana_note(axes[1], lats, lons)

    # tier map (categorical)
    tcmap = ListedColormap(["#2c7fb8", "#fed98e", "#d7301f"])  # highland/peri/core
    from scipy.ndimage import zoom
    Ts = zoom(tier, 8, order=0)
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    axes[2].imshow(Ts, origin="lower", extent=ext, cmap=tcmap,
                   norm=BoundaryNorm([-.5, .5, 1.5, 2.5], tcmap.N), aspect="auto")
    for name, (la, lo, mk) in LANDMARKS.items():
        axes[2].plot(lo, la, mk, mfc="white", mec="k", mew=0.8, ms=5, zorder=5)
        axes[2].annotate(name, (lo, la), xytext=(4, 4), textcoords="offset points",
                         fontsize=6.5)
    axes[2].set_title("(c) Tiers from road + night-lights\n"
                      "(blue highland · tan peri-urban · red core)", fontsize=9)
    axes[2].set_xlim(lons.min(), lons.max()); axes[2].set_ylim(lats.min(), lats.max())

    for ax in axes:
        _scale_bar(ax, lats, lons); ax.set_xlabel("Longitude (°E)")
    axes[0].set_ylabel("Latitude (°N)")
    _north_arrow(axes[0], lats, lons)
    cb = fig.colorbar(im, ax=axes[:2], label="PM₂.₅ (µg m⁻³)", extend="both",
                      ticks=[12, 15, 25], shrink=0.7)
    cb.ax.set_yticklabels(["12", "15 WHO IT-3", "25 IT-2"], fontsize=7)
    fig.suptitle("Akurana-anchored urban-increment SCENARIO (assumes FECT 16.7 real) — "
                 "the current product paints the whole basin at core levels; the "
                 "increment localises ~24 to the core/Peradeniya-Rd zone and drops the "
                 "off-core basin to ~13–17 µg m⁻³", fontsize=10.5)
    fig.savefig(OUT / "source_comparison.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    # ── Figure 2: multiplier surfaces (divergent about 1.0) ──
    fig2, ax2 = plt.subplots(1, 2, figsize=(10.6, 5.2), constrained_layout=True)
    norm = TwoSlopeNorm(vmin=0.75, vcenter=1.0, vmax=1.55)
    from scipy.ndimage import zoom as _z
    for ax, M, ttl in [(ax2[0], sat["S_emit"], f"(a) Satellite $S_{{emit}}$  "
                        f"({sat['S_emit'].max()/sat['S_emit'].min():.2f}×)"),
                       (ax2[1], ui["S_emit_UI"], f"(b) Urban-increment $S_{{emit}}$  "
                        f"({C_core/C_high:.2f}×)")]:
        Ms = _z(M, 8, order=3)
        im2 = ax.imshow(Ms, origin="lower", extent=ext, cmap="RdBu_r", norm=norm,
                        aspect="auto", interpolation="bilinear")
        for name, (la, lo, mk) in LANDMARKS.items():
            ax.plot(lo, la, mk, mfc="white", mec="k", mew=0.8, ms=5, zorder=5)
        ax.set_title(ttl, fontsize=9); ax.set_xlabel("Longitude (°E)")
        ax.set_xlim(lons.min(), lons.max()); ax.set_ylim(lats.min(), lats.max())
    ax2[0].set_ylabel("Latitude (°N)")
    fig2.colorbar(im2, ax=ax2, label="source multiplier (basin mean = 1)",
                  extend="both", shrink=0.8)
    fig2.suptitle("Source-surface contrast: satellite (near-smooth) vs "
                  "Akurana-anchored urban increment", fontsize=10.5)
    fig2.savefig(OUT / "multiplier.png", dpi=220, bbox_inches="tight")
    plt.close(fig2)
    print(f"Wrote {OUT/'source_comparison.png'}")
    print(f"Wrote {OUT/'multiplier.png'}")


if __name__ == "__main__":
    main()
