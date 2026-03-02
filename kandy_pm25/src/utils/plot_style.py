"""
plot_style.py — Shared publication-quality matplotlib style for Kandy PM2.5.

Provides:
  apply_style()     — apply SciencePlots + custom rcParams globally
  style_context()   — context manager variant (reverts on exit)
  save_figure()     — save at 300 dpi as PDF + PNG
  PM25_CMAP         — cmocean.matter  (white → yellow → brown → dark red)
  DIFF_CMAP         — cmocean.balance (blue – white – red, anomalies)
  WIND_CMAP         — cmocean.speed   (white → dark green)
  DIFF_K_CMAP       — cmocean.tempo   (white → dark teal, diffusivity)
  SINGLE_COL_IN     — 88 mm in inches (journal single column)
  DOUBLE_COL_IN     — 180 mm in inches (journal double column)
  FIG_DPI           — 300

Usage:
    from src.utils.plot_style import apply_style, style_context, PM25_CMAP, save_figure

    # Apply globally (persists for rest of session):
    apply_style("ieee")

    # Or use as context manager (reverts afterwards):
    with style_context("ieee"):
        fig, ax = plt.subplots(figsize=(SINGLE_COL_IN, SINGLE_COL_IN * 0.8))
        sc = ax.scatter(lon, lat, c=pm25, cmap=PM25_CMAP)
        save_figure(fig, "fig3_scatter")
"""

from contextlib import contextmanager
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path

# ── Journal dimensions (mm → inches) ────────────────────────────────────────
SINGLE_COL_IN = 88  / 25.4   # 3.46 in
DOUBLE_COL_IN = 180 / 25.4   # 7.09 in
FIG_DPI = 300

# ── Colormaps — loaded at import time, graceful fallback ────────────────────
try:
    import cmocean
    PM25_CMAP   = cmocean.cm.matter    # white→yellow→orange→brown→dark red
    DIFF_CMAP   = cmocean.cm.balance   # diverging blue–white–red
    WIND_CMAP   = cmocean.cm.speed     # white → dark teal/green
    DIFF_K_CMAP = cmocean.cm.tempo     # white → dark teal (diffusivity)
except ImportError:
    PM25_CMAP   = plt.cm.YlOrRd
    DIFF_CMAP   = plt.cm.RdBu_r
    WIND_CMAP   = plt.cm.BuGn
    DIFF_K_CMAP = plt.cm.YlGnBu


def _load_cmaps():
    """No-op kept for backwards compatibility."""
    pass


# ── SciencePlots preset aliases ──────────────────────────────────────────────
_STYLE_MAP = {
    "ieee":     ["science", "ieee"],
    "nature":   ["science", "nature"],
    "science":  ["science"],
    "notebook": ["science", "notebook"],
}

# ── rcParams overlay applied on top of any SciencePlots base ─────────────────
_RCPARAMS = {
    "font.size":          9,
    "axes.titlesize":     10,
    "axes.labelsize":     9,
    "xtick.labelsize":    8,
    "ytick.labelsize":    8,
    "legend.fontsize":    8,
    "figure.dpi":         FIG_DPI,
    "savefig.dpi":        FIG_DPI,
    "savefig.bbox":       "tight",
    "axes.linewidth":     0.8,
    "lines.linewidth":    1.2,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
}


def _apply_rcparams():
    matplotlib.rcParams.update(_RCPARAMS)


def apply_style(preset: str = "ieee") -> None:
    """
    Apply SciencePlots style + project rcParams globally.

    Args:
        preset: "ieee" | "nature" | "science" | "notebook"

    Falls back gracefully if SciencePlots is not installed.
    """
    _load_cmaps()
    styles = _STYLE_MAP.get(preset, ["science"])
    try:
        import scienceplots  # noqa: F401 — registers styles on import
        plt.style.use(styles)
    except ImportError:
        fallback = (
            "seaborn-v0_8-paper"
            if "seaborn-v0_8-paper" in plt.style.available
            else "default"
        )
        plt.style.use(fallback)
    _apply_rcparams()


@contextmanager
def style_context(preset: str = "ieee"):
    """
    Context manager: applies style on entry, restores previous state on exit.

    Example:
        with style_context("ieee"):
            fig, ax = plt.subplots(...)
    """
    _load_cmaps()
    styles = _STYLE_MAP.get(preset, ["science"])
    try:
        import scienceplots  # noqa: F401
        with plt.style.context(styles):
            _apply_rcparams()
            yield
    except ImportError:
        fallback = (
            "seaborn-v0_8-paper"
            if "seaborn-v0_8-paper" in plt.style.available
            else "default"
        )
        with plt.style.context(fallback):
            _apply_rcparams()
            yield


def save_figure(
    fig,
    name: str,
    out_dir=None,
    dpi: int = FIG_DPI,
    formats: tuple = ("pdf", "png"),
) -> Path:
    """
    Save a figure as PDF and/or PNG.

    Args:
        fig:     matplotlib Figure
        name:    filename stem (no extension)
        out_dir: output directory; defaults to results/figures/publication/
        dpi:     raster resolution for PNG
        formats: tuple of format strings, e.g. ("pdf", "png")

    Returns:
        Path to the primary output file (first format).
    """
    if out_dir is None:
        try:
            out_dir = Path(__file__).parents[2] / "results" / "figures" / "publication"
        except Exception:
            out_dir = Path("results/figures/publication")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    primary = None
    for fmt in formats:
        path = out_dir / f"{name}.{fmt}"
        kwargs = {"dpi": dpi} if fmt != "pdf" else {}
        fig.savefig(path, **kwargs)
        if primary is None:
            primary = path
    return primary
