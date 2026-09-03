"""The formulation schematic (F8) and the visual abstract (F0).

Both are diagrams rather than plots, so nothing here reads a scored file except through
claims.json -- and where a number appears it comes from there, so the diagram cannot drift from
the analysis any more than the prose can.

  F8 schematic   section 2 -- the decomposition, the gauge, the tier ladder and the observation
                 operator, which a reader currently has to hold in their head from prose alone.
  F0 abstract    the whole argument on one page: the question, the mechanism that makes it
                 answerable, and the three answers.

Usage:  .venv/Scripts/python.exe scripts/paper2026_figures_c.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from paper2026_figures import v, save, INK, MUTE, OBS, MODEL, FINE, GRID  # noqa: E402

BG = "#4D9221"        # background / regional
INC = "#762A83"       # local increment
FREE = "#4D9221"      # freely available streams
RNG = np.random.default_rng(7)


def _box(ax, x, y, w, h, txt, fc, ec, fs=6.3, weight="normal", tc=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012",
                                facecolor=fc, edgecolor=ec, lw=0.9, transform=ax.transAxes,
                                zorder=2, clip_on=False))
    ax.text(x + w / 2, y + h / 2, txt, transform=ax.transAxes, ha="center", va="center",
            fontsize=fs, color=tc or ec, weight=weight, zorder=3)


def fig_schematic():
    fig = plt.figure(figsize=(7.2, 4.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.80, 1.0], width_ratios=[1.25, 1.0],
                          hspace=0.28, wspace=0.26)

    # ── (a) the decomposition and its gauge ───────────────────────────────────────────────
    a = fig.add_subplot(gs[0, :]); a.axis("off")
    a.set_title("(a)  the decomposition, and the gauge that makes it measurable",
                fontsize=7.6, loc="left", pad=4)
    a.text(0.012, 0.80, "PM(x, y, t)", transform=a.transAxes, fontsize=9, color=INK,
           va="center", family="serif")
    a.text(0.135, 0.80, "=", transform=a.transAxes, fontsize=9, color=INK, va="center")
    a.text(0.175, 0.80, "B(t)", transform=a.transAxes, fontsize=9, color=BG, va="center",
           weight="bold", family="serif")
    a.text(0.245, 0.80, "+", transform=a.transAxes, fontsize=9, color=INK, va="center")
    a.text(0.285, 0.80, "[ T(t) − B(t) ]", transform=a.transAxes, fontsize=9, color=INC,
           va="center", weight="bold", family="serif")
    a.text(0.455, 0.80, "·", transform=a.transAxes, fontsize=9, color=INK, va="center")
    a.text(0.485, 0.80, "P(x, y, t)", transform=a.transAxes, fontsize=9, color=MODEL,
           va="center", weight="bold", family="serif")

    # Labels are CENTRED under their term. Left-aligning them ran "regional background" into
    # "local increment" -- the terms sit closer together than the words describing them do.
    a.text(0.205, 0.55, "regional\nbackground\nuniform in space", transform=a.transAxes,
           fontsize=6.0, color=BG, va="top", ha="center", linespacing=1.35)
    a.text(0.365, 0.55, "local increment\nwhat the city adds", transform=a.transAxes,
           fontsize=6.0, color=INC, va="top", ha="center", linespacing=1.35)
    a.text(0.545, 0.55, "unit-mean pattern\nimposed, not fitted", transform=a.transAxes,
           fontsize=6.0, color=MODEL, va="top", ha="center", linespacing=1.35)

    # the gauge, stated as the consequence
    a.add_patch(Rectangle((0.655, 0.30), 0.335, 0.60, transform=a.transAxes, facecolor="#F5F7FA",
                          edgecolor=MUTE, lw=0.8, zorder=1, clip_on=False))
    a.text(0.822, 0.80, "the gauge condition", transform=a.transAxes, ha="center",
           fontsize=6.6, color=INK, weight="bold")
    a.text(0.822, 0.635, r"mean$_{x,y}$  P  =  1     $\Rightarrow$     mean$_{x,y}$  PM  =  T(t)",
           transform=a.transAxes, ha="center", fontsize=6.4, color=INK, family="serif")
    a.text(0.822, 0.40, "an error in P is an error in WHERE\nthe material sits, never in HOW MUCH",
           transform=a.transAxes, ha="center", fontsize=6.1, color=MUTE, style="italic")

    a.text(0.012, 0.06, "The pattern redistributes concentration inside the basin without altering "
                        "the total, so level and pattern are separately identifiable —\nand an "
                        "imposed pattern cannot displace the one quantity the observations do "
                        "constrain.", transform=a.transAxes, fontsize=6.2, color=MUTE, va="bottom")

    # ── (b) the tier ladder ───────────────────────────────────────────────────────────────
    b = fig.add_subplot(gs[1, 0]); b.axis("off")
    b.set_title("(b)  the information budget: what each tier may use,\n"
                "      and the first thing it can constrain", fontsize=7.6, loc="left", pad=4)
    tiers = [("Bud0", "satellite AOD · reanalysis\ndrivers · static geography", "level", FREE),
             ("Bud1", "+ 2 local sensors", "diurnal and seasonal shape", MODEL),
             ("Bud2", "+ a reference monitor", "instrument bias  b$_k$", MODEL),
             ("Bud3", "+ a regional network", "the background  B(t)", INC),
             ("Bud4", "+ a spatial network", "the pattern  P  — UNVALIDATED", OBS)]
    for i, (name, admits, first, col) in enumerate(tiers):
        y = 0.80 - i * 0.175
        _box(b, 0.005, y, 0.115, 0.125, name, "white", col, fs=6.6, weight="bold")
        b.text(0.135, y + 0.062, admits, transform=b.transAxes, fontsize=5.7, color=INK,
               va="center")
        b.text(0.545, y + 0.062, "→", transform=b.transAxes, fontsize=7, color=MUTE, va="center")
        b.text(0.585, y + 0.062, first, transform=b.transAxes, fontsize=5.9, color=col,
               va="center", style="italic")
    b.text(0.005, -0.03, "Nested, and a lower tier is recoverable BIT-EXACTLY from a higher one\n"
                         "when a stream is withheld — which is what turns an ablation into a "
                         "measurement.", transform=b.transAxes, fontsize=6.0, color=MUTE,
           va="top")

    # ── (c) the observation operator ──────────────────────────────────────────────────────
    c = fig.add_subplot(gs[1, 1])
    c.set_title("(c)  a field is areal; a monitor is a point", fontsize=7.6, loc="left", pad=4)
    # a cell, with sub-grid structure and one monitor in it
    fine = RNG.lognormal(0, 0.55, size=(10, 10))
    c.imshow(fine, cmap="YlOrBr", extent=(0, 1, 0, 1), origin="lower", alpha=.85, zorder=1,
             aspect="auto")
    c.add_patch(Rectangle((0, 0), 1, 1, facecolor="none", edgecolor=INK, lw=1.4, zorder=3))
    c.plot([0.72], [0.28], marker="v", ms=9, color=OBS, mec="white", mew=1.0, zorder=5)
    c.text(0.72, 0.16, "monitor", ha="center", fontsize=6.2, color=OBS, weight="bold", zorder=5)
    c.text(0.05, 0.90, "one 1 km cell", fontsize=6.4, color=INK, weight="bold", zorder=5)
    c.text(0.05, 0.80, "model reports its MEAN", fontsize=6.0, color=INK, zorder=5)
    c.set_xticks([]); c.set_yticks([])
    for sp in c.spines.values():
        sp.set_visible(False)
    c.text(0.5, -0.30, r"$y_k = H_k[C] + b_k + e_k$", transform=c.transAxes, ha="center",
           fontsize=7.6, color=INK, family="serif")
    c.text(0.5, -0.52, "b$_k$  siting and calibration offset (systematic)\n"
                       "e$_k$  measurement + representativeness (random)",
           transform=c.transAxes, ha="center", fontsize=6.0, color=MUTE)
    c.text(0.5, -0.80, "Without this, a kerbside point is compared to an areal mean\n"
                       "by co-location — and a centring error reads as a width failure.",
           transform=c.transAxes, ha="center", fontsize=6.0, color=OBS, style="italic")
    save(fig, "F8_schematic")


def fig_visual_abstract():
    """The whole argument on one page. Drawn on a single full-figure axes with explicit column
    bands: the first version used axis("off") subplots, whose text does not clip, and the
    columns overran each other."""
    fig = plt.figure(figsize=(7.5, 4.2))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    L, M, R = 0.035, 0.375, 0.66          # column left edges
    WL, WR = 0.30, 0.315                  # column text widths

    ax.text(0.5, 0.965, "What is a monitor worth?", ha="center", fontsize=12, color=INK,
            weight="bold")
    ax.text(0.5, 0.925, "exact model degradation as a measurement instrument for urban "
                        "PM$_{2.5}$", ha="center", fontsize=7.6, color=MUTE)
    ax.plot([L, 1 - L], [0.905, 0.905], color=GRID, lw=1.0)

    # ── column 1: the question and the mechanism ──────────────────────────────────────────
    ax.text(L, 0.855, "THE QUESTION", fontsize=7.0, color=MUTE, weight="bold")
    ax.text(L, 0.815, "Most cities that need a PM$_{2.5}$ field have\nno monitors to check one "
                      "with. So what\nshould be bought first, and in what order?",
            fontsize=7.4, color=INK, va="top", linespacing=1.5)
    ax.text(L, 0.665, "Usually unanswerable: remove an input\nand refit, and you have a "
                      "DIFFERENT\nmodel \u2014 the difference confounds\ninformation loss with "
                      "model change.",
            fontsize=6.7, color=MUTE, va="top", linespacing=1.5)

    ax.add_patch(FancyBboxPatch((L, 0.40), WL, 0.135,
                                boxstyle="round,pad=0.008,rounding_size=0.014",
                                facecolor="#F0F5EC", edgecolor=BG, lw=1.0, zorder=2))
    ax.text(L + WL / 2, 0.492, "THE MECHANISM", ha="center", fontsize=6.4, color=BG,
            weight="bold", zorder=3)
    ax.text(L + WL / 2, 0.443, "a lower tier is recoverable BIT-EXACTLY\nfrom a higher one",
            ha="center", fontsize=6.8, color=BG, weight="bold", zorder=3, linespacing=1.4)
    ax.text(L + WL / 2, 0.365, "an ablation becomes a measurement", ha="center", fontsize=6.6,
            color=BG, style="italic")

    ax.text(L, 0.28, f"{v('frame.cities')} cities  \u00b7  {v('frame.city_days'):,} city-days  "
                     f"\u00b7  32 countries", fontsize=7.0, color=INK, weight="bold")
    ax.text(L, 0.245, "every gate registered before scoring;\nthe majority of our own "
                      "predictions were refuted", fontsize=6.5, color=MUTE, va="top",
            linespacing=1.45)

    # ── column 2: the ladder, drawn as a self-contained inset ─────────────────────────────
    bx = fig.add_axes([M, 0.36, 0.245, 0.46])
    steps = [("free geography", v("step.geography"), FREE),
             ("free satellite", v("step.satellite"), FREE),
             ("first 2 monitors", v("maiac.step_bud0c_bud1"), MODEL),
             ("monitors 3\u20138", v("step.bud1_bud2"), MODEL),
             ("regional station", v("step.bud2_bud3"), INC)]
    yy = np.arange(len(steps))[::-1]
    bx.barh(yy, [s[1] for s in steps], color=[s[2] for s in steps], height=.62, zorder=2)
    for y, (lab, val, col) in zip(yy, steps):
        bx.text(1.2, y + 0.40, lab, fontsize=6.4, color=INK, va="center")
        bx.text(val + 1.2, y, f"{val:.1f}%", va="center", fontsize=7.2, weight="bold", color=col)
    bx.set_yticks([]); bx.set_ylim(-0.7, len(steps) - 0.15)
    bx.set_xlim(0, 52)
    bx.set_xlabel("median RMSE reduction", fontsize=6.6)
    bx.tick_params(axis="x", labelsize=6.2)
    bx.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    for sp in ("top", "right", "left"):
        bx.spines[sp].set_visible(False)
    ax.text(M, 0.855, "WHAT EACH INCREMENT BUYS", fontsize=7.0, color=MUTE, weight="bold")

    # ── column 3: the three answers ───────────────────────────────────────────────────────
    ax.text(R, 0.855, "THREE ANSWERS", fontsize=7.0, color=MUTE, weight="bold")
    items = [
        (0.815, "Free data is undervalued.",
         f"Static geography buys {v('step.geography')}% \u2014 about what\nthe first instrument "
         "buys, at every city,\nfor nothing."),
        (0.655, "Density saturates immediately.",
         f"Monitors 3\u20138 buy {v('step.bud1_bud2')}%. The most\nestimator-robust result in "
         "the study."),
        (0.515, "A fused covariate under-prices\nthe monitors it was trained on.",
         f"Swapping it for raw satellite retrievals\nleaves the satellite rung alone but "
         f"roughly\nDOUBLES a local monitor's measured value\n"
         f"({v('band.deep_tropical.step_bud0c_bud1')}% \u2192 "
         f"{v('maiac.deep_tropical_first2')}% in the tropics)."),
    ]
    for y, head, body in items:
        ax.text(R, y, head, fontsize=7.3, color=INK, weight="bold", va="top", linespacing=1.35)
        ax.text(R, y - 0.042 * (head.count(chr(10)) + 1), body, fontsize=6.5, color=MUTE,
                va="top", linespacing=1.5)

    # Dropped from 0.245: the box was landing on the third answer's closing line.
    ax.add_patch(FancyBboxPatch((R, 0.205), WR, 0.10,
                                boxstyle="round,pad=0.008,rounding_size=0.014",
                                facecolor="#FBE9E7", edgecolor=OBS, lw=1.0, zorder=2))
    ax.text(R + WR / 2, 0.255, "and the ordering INVERTS in the tropics:\nlocal stations worth "
                               f"{v('maiac.deep_tropical_local_advantage')}\u00d7 a regional one",
            ha="center", va="center", fontsize=6.8, color=OBS, weight="bold", zorder=3,
            linespacing=1.4)

    ax.plot([L, 1 - L], [0.185, 0.185], color=GRID, lw=1.0)
    ax.text(0.5, 0.145, "Where the model stops is measured, not caveated: two sites 300\u202fm "
                        f"apart inside one cell differ by {v('spatial.paired_obs_ratio')}\u00d7 "
                        f"in observation and {v('spatial.paired_model_ratio')}\u00d7 in the "
                        "model,", ha="center", fontsize=6.8, color=INK)
    ax.text(0.5, 0.105, f"and re-running the physics at {v('subgrid.fine_res_m')}\u202fm does "
                        "not change it. The spread WITHIN a typical cell "
                        f"({v('s2.within_pixel_p90p10'):.2f}\u00d7) exceeds the spread BETWEEN "
                        f"cells ({v('s2.between_pixel_p90p10'):.2f}\u00d7).",
            ha="center", fontsize=6.8, color=INK)
    ax.text(0.5, 0.055, "The model cannot say which street is worse. It can say what range a "
                        "cell spans \u2014 and no field of this kind currently reports it.",
            ha="center", fontsize=6.8, color=OBS, style="italic")

    save(fig, "F0_visual_abstract")



if __name__ == "__main__":
    fig_schematic()
    fig_visual_abstract()
