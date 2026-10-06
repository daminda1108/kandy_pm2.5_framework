"""Make a matplotlib figure print at the size its fonts claim.

WHY. The thesis text column is 6.0 inches (A4 less the departmental 1.25 in and 1 in margins).
Figures were drawn 7 to 9.5 inches wide with 7 to 8 pt lettering, and pandoc shrinks anything
wider than the column to fit, so their lettering printed at 3 to 6 pt (measured by OCR on every
figure of Thesis A, 2026-09-19). Nothing in the build reported it.

fit_print(fig) is called immediately before savefig. It
  1. resizes a figure wider than the column to the column width, so a point in the code is a
     point on the page;
  2. raises any text still below MIN_PT to MIN_PT;
  3. re-runs the layout so the larger lettering is not clipped.
It never changes data, only geometry and type size.
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.text as mtext

TEXT_W_IN = 8.27 - 1.25 - 1.0     # A4 width less the ENS4998 margins
MIN_PT = 8.0

# Maths text is laid out when first drawn, so its face must be set before any figure is built:
# setting it only at save time left italic symbols (B, f) in the default sans serif.
mpl.rcParams.update({"mathtext.fontset": "stix",
                     "font.serif": ["Times New Roman", "Times", "STIXGeneral"]})


def fit_print(fig, width_in: float = TEXT_W_IN, min_pt: float = MIN_PT,
              height_boost: float = 1.12) -> None:
    w, h = fig.get_size_inches()
    if w > width_in:
        # The same lettering on a narrower canvas needs a little more height to breathe.
        fig.set_size_inches(width_in, h * width_in / w * height_boost)
    # Tick labels do not exist until the figure is drawn, so draw first. They are also
    # regenerated on every later draw from the axis's tick parameters, so the floor has to be set
    # through tick_params and not on the label objects alone (found 2026-09-19: tick and
    # colour-bar labels set at 6 pt survived the first version of this rule untouched).
    fig.canvas.draw()
    for ax in fig.axes:
        for name, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
            labs = [t for t in axis.get_ticklabels(which="both") if t.get_text().strip()]
            if labs and min(t.get_fontsize() for t in labs) < min_pt:
                ax.tick_params(axis=name, which="both", labelsize=min_pt)
    for t in fig.findobj(mtext.Text):
        if t.get_text().strip() and t.get_fontsize() < min_pt:
            t.set_fontsize(min_pt)
    # One face throughout, the thesis's own (ENS4998: Times New Roman). Several analysis figures
    # were set in the matplotlib default sans serif, beside Times in the text and in every other
    # figure. Mathematical text uses STIX, the Times-compatible maths face.
    mpl.rcParams.update({"font.family": "serif",
                         "font.serif": ["Times New Roman", "Times", "STIXGeneral"],
                         "mathtext.fontset": "stix"})
    for t in fig.findobj(mtext.Text):
        t.set_fontfamily("serif")
    _relayout(fig)
    # A legend or label drawn outside the axes makes the SAVED image (bbox_inches="tight", the
    # default in every thesis style) wider than the canvas, and pandoc then shrinks the whole
    # image, lettering included, back to the column. Found 2026-09-19 by measuring the saved
    # widths: several figures saved at 6.3 to 6.9 in after this function had set 6.0. Narrow the
    # canvas until the tight box fits.
    for _ in range(6):
        fig.canvas.draw()
        tight_w = fig.get_tightbbox(fig.canvas.get_renderer()).width
        if tight_w <= width_in * 1.002:
            break
        w, h = fig.get_size_inches()
        fig.set_size_inches(w - (tight_w - width_in) - 0.02, h)
        _relayout(fig)


def _relayout(fig) -> None:
    # Tried and rejected 2026-09-19: switching figures to constrained layout here collapsed the
    # multi-panel ones and did not help labels that collide inside their own axes. Those are
    # fixed in each figure's own script.
    engine = fig.get_layout_engine()
    if engine is not None:
        engine.execute(fig)
    else:
        try:
            fig.tight_layout()
        except Exception:                                                   # noqa: BLE001
            pass


def printed_min_pt(fig, width_in: float = TEXT_W_IN, tight: bool = True) -> tuple[float, float]:
    """(smallest visible lettering in printed points, saved width in inches), measured exactly
    from the figure's own text objects rather than from pixels."""
    fig.canvas.draw()
    w = (fig.get_tightbbox(fig.canvas.get_renderer()).width if tight
         else fig.get_size_inches()[0])
    sizes = [t.get_fontsize() for t in fig.findobj(mtext.Text)
             if t.get_visible() and t.get_text().strip()]
    return (min(sizes) * min(1.0, width_in / w) if sizes else float("nan")), w
