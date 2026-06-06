"""
pubfig.py — publication-grade matplotlib style + output folder for the final-model
figure suite (2026-06-05). Importing this module applies the style globally.

Style: SciencePlots 'science' base (thin axes, inward minor ticks, tight) WITHOUT
the LaTeX engine (robust to the suite's unicode labels µg m⁻³, PM₂.₅, °N), with
STIX (Times-like) text+math fonts for a journal-standard serif look. 400 dpi.

All figures render to results/figures/publication/ (a fresh, dedicated folder).
"""
from __future__ import annotations
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[3]
PUB_OUT = REPO / "results" / "figures" / "publication"
PUB_OUT.mkdir(parents=True, exist_ok=True)


def apply() -> None:
    try:
        import scienceplots  # noqa: F401  (registers the styles)
        plt.style.use(["science", "no-latex"])
    except Exception:
        pass
    mpl.rcParams.update({
        # journal-standard serif (STIX ≈ Times), consistent text + math
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "axes.unicode_minus": False,
        # resolution / saving
        "savefig.dpi": 400, "figure.dpi": 120,
        "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        # type sizes (publication)
        "font.size": 8.5, "axes.titlesize": 9.0, "axes.labelsize": 8.5,
        "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.0,
        "figure.titlesize": 10.5,
        # lines / axes / ticks
        "axes.linewidth": 0.6, "lines.linewidth": 1.4,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
        "xtick.direction": "out", "ytick.direction": "out",
        # CANONICAL 2026-06-06: legends always visible (opaque box, never washed into the map)
        "legend.frameon": True, "legend.framealpha": 0.92, "legend.edgecolor": "0.6",
        "legend.facecolor": "white", "legend.fancybox": True, "legend.handlelength": 1.5,
        "legend.borderpad": 0.4, "legend.labelspacing": 0.3,
        "grid.linewidth": 0.4, "grid.alpha": 0.25,
    })


apply()
