"""
figure_architecture.py — schematic of the spatial-temporal decomposition model
for the supervisor review. Inputs → three model layers → combination → output.

Output: results/figures/kandy_decomp/pub/architecture.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).parents[3]
import sys as _sys; _sys.path.insert(0, str(HERE))
from src.stage1_satml.decomp.pubfig import PUB_OUT as OUT  # publication style + folder
OUT.mkdir(parents=True, exist_ok=True)

TEAL = "#2A9D8F"; CORAL = "#E76F51"; GREEN = "#5B8C5A"
GREY = "#6B7280"; DARK = "#13403B"; LIGHT = "#EEF8F6"


def box(ax, x, y, w, h, title, sub, fc, ec):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.02",
                                fc=fc, ec=ec, lw=1.6, mutation_aspect=0.6))
    ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center",
            fontsize=9.5, fontweight="bold", color=DARK)
    ax.text(x + w / 2, y + h * 0.26, sub, ha="center", va="center",
            fontsize=7.2, color="#374151")


def arrow(ax, x0, y0, x1, y1, color=GREY):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                                 mutation_scale=12, lw=1.3, color=color,
                                 shrinkA=2, shrinkB=2))


def main():
    fig, ax = plt.subplots(figsize=(12, 6.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # column headers
    for x, t in [(0.13, "INPUT DATA"), (0.50, "MODEL LAYERS"), (0.85, "PRODUCT")]:
        ax.text(x, 0.97, t, ha="center", fontsize=10, fontweight="bold", color=DARK)

    # ── inputs ──
    box(ax, 0.02, 0.70, 0.22, 0.14, "Satellite + reanalysis",
        "GEOS-CF · ERA5 · CAMS · MAIAC", LIGHT, GREY)
    box(ax, 0.02, 0.43, 0.22, 0.14, "Ground sensors",
        "FECT PurpleAir · KOALA (2019)", LIGHT, GREY)
    box(ax, 0.02, 0.16, 0.22, 0.14, "Spatial layers",
        "Van Donkelaar · SRTM · VIIRS NTL", LIGHT, GREY)

    # ── model layers ──
    box(ax, 0.37, 0.70, 0.26, 0.15, "T(t)  temporal level",
        "lag-free LightGBM (residual vs\nGEOS-CF) + Mondrian conformal", "#E8F6F3", TEAL)
    box(ax, 0.37, 0.43, 0.26, 0.15, "S_emit(x, y)  spatial pattern",
        "Van Donkelaar PM2.5 surface\n(2019–23), normalised mean 1", "#FDECE7", CORAL)
    box(ax, 0.37, 0.16, 0.26, 0.15, "M(x, y, t)  confinement",
        "1 + κ·w(BLH)·c(terrain)\nnocturnal valley-pooling", "#EAF2E9", GREEN)

    # ── combine + output ──
    ax.text(0.715, 0.515, "⊗", ha="center", va="center", fontsize=26, color=DARK)
    box(ax, 0.74, 0.36, 0.24, 0.30,
        "PM(x, y, t) = T·S·M",
        "1 km × hourly field\n+ calibrated 90% PI\nper-year VanD AREA level\n(β≡1; KOALA=floor diag.)\n2019–2023", "#F4F7F6", DARK)

    # input → layer arrows
    arrow(ax, 0.24, 0.77, 0.37, 0.77, GREY)               # sat → T
    arrow(ax, 0.24, 0.50, 0.37, 0.74, GREY)               # ground → T
    arrow(ax, 0.24, 0.23, 0.37, 0.50, CORAL)              # spatial → S
    arrow(ax, 0.24, 0.20, 0.37, 0.23, GREEN)              # spatial(terrain) → M
    arrow(ax, 0.24, 0.72, 0.37, 0.25, GREEN)              # reanalysis(BLH) → M
    # layers → combine
    for y in (0.775, 0.505, 0.235):
        arrow(ax, 0.63, y, 0.715, 0.515, DARK)
    arrow(ax, 0.745, 0.515, 0.74, 0.515, DARK)

    ax.text(0.5, 0.045,
            "Separable decomposition: time-rich signal (T) and space-poor signal (S·M) "
            "use the right data at the right confidence — never contaminating each other.",
            ha="center", fontsize=8.2, style="italic", color="#374151")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig31_architecture.{ext}", dpi=300, bbox_inches="tight")
    print("Wrote", OUT / "fig31_architecture.png")


if __name__ == "__main__":
    main()
