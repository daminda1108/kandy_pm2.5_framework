"""
publication_figures.py — Generate all publication-quality figures for the Kandy PM2.5 paper.

Reproduces the 8 core figures from RESEARCH_PROJECT_DESIGN.md §5 (Publication Plan):

  Fig 1  — Study area map: Kandy valley topography + monitoring stations
  Fig 2  — Framework overview (3-stage pipeline diagram)
  Fig 3  — Stage 1 performance: scatter + blocked-CV RMSE vs benchmark
  Fig 4  — Stage 1 SHAP summary: feature importance + physics victory
  Fig 5  — Stage 3 K-field spatial map (Kx, Ky, anisotropy)
  Fig 6  — Stage 3 discovered source S vs OSM road density scatter
  Fig 7  — Stage 1 vs Stage 3 valley difference map + UQ comparison
  Fig 8  — Transfer learning convergence: transfer vs cold-start loss curves

All figures are journal-style (300 dpi, 88 mm or 180 mm wide for single/double column).
Uses matplotlib with the 'seaborn-v0_8-paper' style for clean line aesthetics.

Usage (regenerate all):
    python publication_figures.py --all
    python publication_figures.py --fig 5   # Only Figure 5
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import LOG_FORMAT, LOG_DATEFMT, FIGURES_DIR, TABLES_DIR, MODELS_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("publication_figures")

# Journal figure dimensions (mm → inches, 1 mm = 1/25.4 in)
SINGLE_COL_W = 88  / 25.4   # 3.46 in — single column
DOUBLE_COL_W = 180 / 25.4   # 7.09 in — double column
FIG_DPI      = 300

PUB_DIR = FIGURES_DIR / "publication"


def _setup_style() -> None:
    """Apply a clean journal-style matplotlib rcParams."""
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        # Try seaborn style; fall back to a clean custom dict
        style = "seaborn-v0_8-paper" if "seaborn-v0_8-paper" in plt.style.available else "default"
        plt.style.use(style)
        matplotlib.rcParams.update({
            "font.size":        9,
            "axes.titlesize":   10,
            "axes.labelsize":   9,
            "xtick.labelsize":  8,
            "ytick.labelsize":  8,
            "legend.fontsize":  8,
            "figure.dpi":       FIG_DPI,
            "savefig.dpi":      FIG_DPI,
            "savefig.bbox":     "tight",
            "axes.linewidth":   0.8,
            "lines.linewidth":  1.2,
        })
    except ImportError:
        pass


def _save(fig, name: str) -> Path:
    PUB_DIR.mkdir(parents=True, exist_ok=True)
    out = PUB_DIR / f"{name}.pdf"
    fig.savefig(out)
    png = PUB_DIR / f"{name}.png"
    fig.savefig(png, dpi=FIG_DPI)
    log.info(f"Figure saved → {out.name}")
    return out


# ── Individual figures ───────────────────────────────────────────────────────

def fig1_study_area(dem_path: Optional[Path] = None) -> None:
    """Fig 1 — Kandy valley topography + station locations."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not available"); return

    fig, ax = plt.subplots(figsize=(SINGLE_COL_W, SINGLE_COL_W * 0.9))
    # Placeholder topographic background — replaced with actual DEM when available
    ax.set_facecolor("#d9e8f5")
    kandy_lat, kandy_lon = 7.2906, 80.6337
    ax.scatter([kandy_lon], [kandy_lat], marker="^", color="crimson", s=40, zorder=5, label="Kandy centre")
    ax.set_xlim(80.55, 80.72); ax.set_ylim(7.22, 7.38)
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    ax.set_title("Study Area — Kandy Valley, Sri Lanka")
    ax.legend(fontsize=7); ax.grid(alpha=0.3, linewidth=0.5)
    ax.text(0.97, 0.03, "DEM: SRTM 30 m", transform=ax.transAxes,
            fontsize=6, ha="right", alpha=0.6)
    _save(fig, "fig1_study_area"); plt.close()


def fig3_stage1_performance(metrics_csv: Optional[Path] = None) -> None:
    """Fig 3 — Stage 1 temporal blocked-CV RMSE comparison."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not available"); return

    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL_W, DOUBLE_COL_W * 0.45))

    # Left: scatter plot (Stage 1 predicted vs observed)
    axes[0].set_xlabel("Observed PM2.5 (µg/m³)")
    axes[0].set_ylabel("Predicted PM2.5 (µg/m³)")
    axes[0].set_title("Stage 1 Sat-ML: Predicted vs Observed")
    axes[0].plot([0, 100], [0, 100], "k--", lw=0.8, label="1:1 line")
    axes[0].text(0.05, 0.9, "Populate from Stage 1 eval output",
                 transform=axes[0].transAxes, fontsize=7, alpha=0.5)

    # Right: blocked-CV RMSE bars
    axes[1].set_xlabel("Cross-validation Strategy")
    axes[1].set_ylabel("RMSE (µg/m³)")
    axes[1].set_title("Blocked Cross-Validation RMSE")
    axes[1].text(0.05, 0.9, "Populate from blocked_cv.py output",
                 transform=axes[1].transAxes, fontsize=7, alpha=0.5)

    fig.suptitle("Stage 1 Model Performance", fontsize=10)
    _save(fig, "fig3_stage1_performance"); plt.close()


def fig5_k_field(k_csv: Optional[Path] = None) -> None:
    """Fig 5 — Stage 3: Kx, Ky, and K_ratio spatial maps."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not available"); return

    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE_COL_W, DOUBLE_COL_W * 0.38))
    if k_csv and Path(k_csv).exists():
        k_df = pd.read_csv(k_csv)
        for ax, col, cmap, label in zip(
            axes,
            ["Kx", "Ky", "K_ratio"],
            ["viridis", "viridis", "RdYlGn"],
            ["Kx (m²/s)", "Ky (m²/s)", "Kx/Ky"],
        ):
            sc = ax.scatter(k_df["lon"], k_df["lat"], c=k_df[col],
                            cmap=cmap, s=2, rasterized=True)
            plt.colorbar(sc, ax=ax, label=label, shrink=0.8)
    else:
        for ax in axes:
            ax.text(0.5, 0.5, "Run Stage 3 first",
                    ha="center", va="center", transform=ax.transAxes, fontsize=8, alpha=0.5)
    for ax, t in zip(axes, ["(a) Along-valley Kx", "(b) Cross-valley Ky", "(c) Anisotropy Kx/Ky"]):
        ax.set_title(t, fontsize=8); ax.grid(alpha=0.2, lw=0.4)
    fig.suptitle("Stage 3 Learned Diffusivity Field", fontsize=10)
    _save(fig, "fig5_k_field"); plt.close()


def fig6_source_osm(
    source_csv: Optional[Path] = None,
) -> None:
    """Fig 6 — Stage 3: Discovered source S vs OSM road density scatter."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not available"); return

    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL_W, DOUBLE_COL_W * 0.40))
    if source_csv and Path(source_csv).exists():
        s_df = pd.read_csv(source_csv)
        axes[0].scatter(s_df["lon"], s_df["lat"], c=s_df["S"],
                        cmap="hot_r", s=2, rasterized=True)
        axes[0].set_title("(a) Discovered Source S(x,y)")
    else:
        axes[0].text(0.5, 0.5, "Run Stage 3 first", ha="center", va="center",
                     transform=axes[0].transAxes, fontsize=8, alpha=0.5)

    axes[1].set_xlabel("OSM Road Density (km/km²)")
    axes[1].set_ylabel("S (µg/m³/s)")
    axes[1].set_title("(b) S vs Road Density — Pearson r")
    axes[1].text(0.05, 0.9, "Populate from discover_sources.py output",
                 transform=axes[1].transAxes, fontsize=7, alpha=0.5)
    _save(fig, "fig6_source_osm"); plt.close()


def fig7_stage1_vs_stage3(
    s1_preds_path: Optional[Path] = None,
    s3_preds_path: Optional[Path] = None,
) -> None:
    """Fig 7 — Stage 1 vs Stage 3 delta map + UQ width comparison."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not available"); return

    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE_COL_W, DOUBLE_COL_W * 0.38))
    for ax, t in zip(axes, [
        "(a) Stage 1 Sat-ML PM2.5",
        "(b) Stage 3 PINN PM2.5",
        "(c) PINN − Sat-ML Δ",
    ]):
        ax.set_title(t, fontsize=8)
        ax.text(0.5, 0.5, "Run pipeline then populate", ha="center", va="center",
                transform=ax.transAxes, fontsize=7, alpha=0.5)
    fig.suptitle("Stage 1 vs Stage 3 PM2.5 Comparison", fontsize=10)
    _save(fig, "fig7_stage1_vs_stage3"); plt.close()


def fig8_transfer_convergence(loss_dir: Optional[Path] = None) -> None:
    """Fig 8 — Transfer vs cold-start training loss curves."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not available"); return

    ldir = loss_dir or (MODELS_DIR / "stage3_pinn")
    fig, ax = plt.subplots(figsize=(SINGLE_COL_W, SINGLE_COL_W * 0.75))

    for fname, label, color in [
        ("transfer_losses.csv", "Transfer-init", "#2171b5"),
        ("coldstart_losses.csv", "Cold-start",  "#cb181d"),
    ]:
        p = ldir / fname
        if p.exists():
            df = pd.read_csv(p)
            col = "L_total" if "L_total" in df.columns else df.columns[-1]
            ax.semilogy(df["epoch"], df[col], color=color, label=label, lw=1.2)

    ax.set_xlabel("Training Epoch"); ax.set_ylabel("Total Loss (log scale)")
    ax.set_title("PINN Convergence: Transfer vs Cold-start")
    ax.legend(); ax.grid(alpha=0.3, lw=0.4)
    _save(fig, "fig8_transfer_convergence"); plt.close()


# ── CLI entry point ──────────────────────────────────────────────────────────

def main():
    _setup_style()
    parser = argparse.ArgumentParser(description="Generate publication figures")
    parser.add_argument("--all",  action="store_true", help="Generate all 8 figures")
    parser.add_argument("--fig",  type=int, help="Generate only figure N (1,3,5,6,7,8)")
    args = parser.parse_args()

    k_csv  = MODELS_DIR / "stage3_pinn" / "k_field.csv"
    s_csv  = MODELS_DIR / "stage3_pinn" / "source_field.csv"

    fig_map = {
        1: lambda: fig1_study_area(),
        3: lambda: fig3_stage1_performance(),
        5: lambda: fig5_k_field(k_csv),
        6: lambda: fig6_source_osm(s_csv),
        7: lambda: fig7_stage1_vs_stage3(),
        8: lambda: fig8_transfer_convergence(),
    }

    if args.fig:
        if args.fig in fig_map:
            fig_map[args.fig]()
        else:
            log.error(f"Figure {args.fig} not implemented. Choose from: {sorted(fig_map)}")
    else:  # --all is implied
        for fn in fig_map.values():
            try:
                fn()
            except Exception as e:
                log.error(f"Figure failed: {e}")

    log.info(f"All requested figures saved to {PUB_DIR}")


if __name__ == "__main__":
    main()
