"""House style for every diagram and figure in the thesis.

WHY THIS EXISTS. A thesis that mixes matplotlib data figures with diagrams drawn in some other
tool reads as a report with clip art in it. Everything here renders through one style: Times New
Roman to match the body text, one palette, one line weight, one arrow head. A reader should not
be able to tell which library drew which picture.

TWO BACKENDS, chosen by what the picture is.

  schemdraw   hand placed flowcharts, where the layout carries meaning and must not move:
              the pipeline, the validation protocol, the decision tree. Renders through
              matplotlib, so the fonts match the data figures exactly.

  graphviz    dependency graphs where automatic layout is genuinely better than hand placement
              and the exact node positions do not matter: the regeneration chain, tier nesting.
              Font is set to Times New Roman so the output still matches.

Usage:
    from thesisviz import style, save, C, gv_digraph
    style()
    with schemdraw.Drawing() as d:
        ...
    save(d, "D5_validation_protocol")
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# Graphviz installs here on Windows and is not added to PATH by the installer.
_GV = r"C:\Program Files\Graphviz\bin"
if os.path.isdir(_GV) and _GV not in os.environ.get("PATH", ""):
    os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + _GV

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = ROOT / "thesis" / "diagrams"
FIGURES = ROOT / "thesis" / "figures"
for _d in (DIAGRAMS, FIGURES):
    _d.mkdir(parents=True, exist_ok=True)

# ── palette ───────────────────────────────────────────────────────────────────────────────
# Deliberately small and colour-vision safe. The thesis is printed as often as it is read on
# screen, so every pair here is also separable in greyscale by lightness.
C = {
    "ink":      "#1a1a1a",   # text and rules
    "muted":    "#6b6b6b",   # secondary text, annotations
    "line":     "#4d4d4d",   # arrows and boxes
    "free":     "#4393c3",   # information that is free everywhere (blue)
    "local":    "#d6604d",   # information that must be bought locally (red)
    "regional": "#f4a582",   # regional information (light red)
    "good":     "#4d9221",   # held, passed, kept
    "bad":      "#c51b7d",   # refuted, failed, dropped
    "fill":     "#f2f2f2",   # box fill
    "fill2":    "#e3eef6",   # emphasised box fill
}

FONT = "Times New Roman"
# Graphviz renders through Pango, which parses a trailing "Roman" as a STYLE keyword and
# silently drops it, giving Sans. A trailing comma stops the strip. Verified: this name loads
# without a Pango warning, "Times New Roman" alone does not.
GV_FONT = "Times New Roman,"
BASE_PT = 11          # diagram text; body is 12 pt, and a diagram reads correctly one step down


def style(font_pt: int = BASE_PT) -> None:
    """Apply the thesis look to matplotlib, which schemdraw draws through."""
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": [FONT, "Times", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": font_pt,
        "axes.titlesize": font_pt + 1,
        "axes.labelsize": font_pt,
        "xtick.labelsize": font_pt - 1,
        "ytick.labelsize": font_pt - 1,
        "legend.fontsize": font_pt - 1,
        "axes.edgecolor": C["line"],
        "axes.labelcolor": C["ink"],
        "text.color": C["ink"],
        "xtick.color": C["line"],
        "ytick.color": C["line"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.bbox": "tight",
        "savefig.dpi": 400,
        "lines.linewidth": 1.2,
    })


def save(drawing, name: str, folder: Path = DIAGRAMS) -> Path:
    """Write a schemdraw drawing as png at 400 dpi, and as pdf for the record."""
    png = folder / f"{name}.png"
    drawing.save(str(png), dpi=400)
    try:
        drawing.save(str(folder / f"{name}.pdf"))
    except Exception:                                                   # noqa: BLE001
        pass
    return png


def save_fig(fig, name: str, folder: Path = FIGURES) -> Path:
    png = folder / f"{name}.png"
    fig.savefig(png, dpi=400)
    fig.savefig(folder / f"{name}.pdf")
    plt.close(fig)
    return png


def gv_digraph(name: str, rankdir: str = "TB"):
    """A graphviz Digraph already carrying the thesis fonts and colours."""
    import graphviz
    g = graphviz.Digraph(name, format="png")
    g.attr(rankdir=rankdir, bgcolor="white", splines="ortho", nodesep="0.35",
           ranksep="0.5", fontname=GV_FONT)
    g.attr("node", shape="box", style="rounded,filled", fillcolor=C["fill"],
           color=C["line"], fontname=GV_FONT, fontsize=str(BASE_PT), fontcolor=C["ink"],
           margin="0.14,0.09")
    g.attr("edge", color=C["line"], fontname=GV_FONT, fontsize=str(BASE_PT - 2),
           fontcolor=C["muted"], arrowsize="0.7")
    return g


def gv_note(g, text: str) -> None:
    """Attach the diagram's one-line point as a graph label.

    Not as a node. A caption node needs an invisible edge to position it, which adds a whole
    rank and stretches the drawing down a page it does not need.
    """
    g.attr(label=text.replace(chr(10), chr(92) + "n"), labelloc="b", labeljust="c",
           fontname=GV_FONT, fontsize=str(BASE_PT - 1.5), fontcolor=C["muted"])


def gv_save(g, name: str, folder: Path = DIAGRAMS) -> Path:
    """Render a graphviz graph at print resolution. Returns the png path."""
    g.attr(dpi="400")
    out = folder / name
    g.render(str(out), format="png", cleanup=True)
    g.render(str(out), format="pdf", cleanup=True)
    return folder / f"{name}.png"
