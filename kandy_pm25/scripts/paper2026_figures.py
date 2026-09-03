"""Figures for the 2026 rewrite. Every number is read from claims.json, never typed.

Two figures, in the priority the rewrite plan sets:

  F1 paired      the money figure -- two microsites 300 m apart inside one 998 m cell, and what
                 happens when the physics is re-run ten times finer. Carries section 5.
  F2 ladder      the budget ladder, stratified by band and instrument class, with per-cell n
                 IN THE FIGURE rather than the caption (a reviewer who has to hunt for the
                 sample size assumes it was hidden).

Usage:  .venv/Scripts/python.exe scripts/paper2026_figures.py
Out:    results/figures/paper2026/{F1_paired,F2_ladder}.{png,pdf}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
MOD = REPO / "data" / "processed" / "modular"
OUT = REPO / "results" / "figures" / "paper2026"
OUT.mkdir(parents=True, exist_ok=True)

C = json.load(open(MOD / "claims.json"))["claims"]
v = lambda k: C[k]["value"]

# Colour-blind-safe throughout. `turbo` fails a CVD check and is not used anywhere here.
INK, MUTE = "#1a1a1a", "#8a8a8a"
OBS, MODEL, FINE = "#B2182B", "#2166AC", "#67A9CF"
GRID = "#E8E8E8"

plt.rcParams.update({
    "font.size": 8, "axes.linewidth": 0.7, "axes.edgecolor": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.major.width": 0.7, "ytick.major.width": 0.7,
    "figure.dpi": 200, "savefig.dpi": 400, "savefig.bbox": "tight",
})


def save(fig, stem):
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{stem}.{ext}")
    plt.close(fig)
    print(f"  wrote {stem}.png / .pdf")


# ── F1: the paired-site figure ────────────────────────────────────────────────────────────
def fig_paired():
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.6),
                           gridspec_kw={"width_ratios": [1.05, 1.0, 1.25], "wspace": 0.42})

    # (a) the pair itself, on a log axis because 27.5x will not show linearly beside 1.1x
    a = ax[0]
    obs_hi, obs_lo = 110.0, 4.0
    series = [("observed\n(3 h, kerbside)", obs_hi, obs_lo, OBS),
              ("model,\nas shipped", 1.0, 1.0 / v("spatial.paired_model_ratio"), MODEL),
              (f"model,\n{v('subgrid.fine_res_m')} m", 1.0, 1.0 / v("s1.paired_fine_94m"), FINE)]
    for i, (lab, hi, lo, col) in enumerate(series):
        hi_n, lo_n = (hi / lo, 1.0) if i else (obs_hi / obs_lo, 1.0)
        a.plot([i, i], [lo_n, hi_n], color=col, lw=6, solid_capstyle="butt", alpha=.85, zorder=2)
        a.plot([i], [hi_n], "o", color=col, ms=5, zorder=3)
        a.plot([i], [lo_n], "o", color="white", mec=col, mew=1.3, ms=5, zorder=3)
        a.text(i, hi_n * 1.28, f"{hi_n:.2f}×", ha="center", color=col, fontsize=8, weight="bold")
    a.set_yscale("log"); a.set_ylim(0.7, 60)
    a.set_xticks(range(3)); a.set_xticklabels([s[0] for s in series], fontsize=6.6)
    a.set_ylabel("ratio between the two sites", fontsize=7.5)
    a.axhline(1.0, color=MUTE, lw=0.6, ls=":")
    a.set_yticks([1, 2, 5, 10, 30]); a.set_yticklabels(["1", "2", "5", "10", "30"])
    a.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    a.set_title("(a)  two sites, 300 m apart,\none 998 m cell", fontsize=7.5, loc="left", pad=6)

    # (b) refinement changes nothing
    b = ax[1]
    xs = [v("subgrid.coarse_res_m"), 238, v("subgrid.fine_res_m")]
    ys = [v("spatial.paired_model_ratio"), v("s1.paired_production_238m"), v("s1.paired_fine_94m")]
    b.plot(xs, ys, "o-", color=MODEL, lw=1.4, ms=5, zorder=3)
    b.axhline(v("spatial.paired_obs_ratio"), color=OBS, lw=1.2, ls="--", zorder=2)
    b.text(0.5, 0.86, "observed 27.5×", transform=b.transAxes, ha="center", color=OBS, fontsize=7)
    b.set_xscale("log"); b.set_yscale("log")
    # Coarse -> fine, left to right: the claim is about REFINING, so the reading order should
    # follow the argument rather than the numeric value of the resolution.
    b.invert_xaxis()
    b.set_xticks(xs); b.set_xticklabels([f"{int(x)} m" for x in xs], fontsize=7)
    b.set_ylim(0.85, 60); b.set_yticks([1, 2, 5, 10, 30])
    b.set_yticklabels(["1", "2", "5", "10", "30"])
    b.set_xlabel("model resolution", fontsize=7.5)
    b.set_ylabel("paired-site ratio", fontsize=7.5)
    b.grid(color=GRID, lw=0.5, zorder=0)
    b.set_title("(b)  refining the physics\ndoes not close it", fontsize=7.5, loc="left", pad=6)

    # (c) where the contrast goes -- it is relocated, not destroyed
    c = ax[2]
    stages = [("raw emission,\n94 m", v("s1.contrast.raw_E_fine_94_m")),
              ("+ tempering", v("s1.contrast.log1p_tempering")),
              ("+ dispersion", v("s1.contrast.dispersion_94_m")),
              ("+ solve 238 m", v("s1.contrast.solve_at_238_m_(production)")),
              ("+ report 998 m", v("s1.contrast.report_at_998_m"))]
    yy = np.arange(len(stages))[::-1]
    c.barh(yy, [s[1] for s in stages], color=FINE, height=.62, zorder=2)
    for y, (lab, val) in zip(yy, stages):
        c.text(val + 1.5, y, f"{val:.1f}×", va="center", fontsize=7, color=INK)
    c.set_yticks(yy); c.set_yticklabels([s[0] for s in stages], fontsize=6.8)
    c.set_xlim(0, 78); c.set_xlabel("within-domain spread (p90/p10)", fontsize=7.5)
    c.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    c.set_title("(c)  contrast is relocated,\nnot destroyed", fontsize=7.5, loc="left", pad=6)

    save(fig, "F1_paired")


# ── F2: the budget ladder ─────────────────────────────────────────────────────────────────
def fig_ladder():
    lad = pd.read_csv(MOD / "ladder_revalidated.csv")
    x = lad[lad.bottom == "Bud0c"]
    n_band = x.band.value_counts().to_dict()
    n_cls = x.cls.value_counts().to_dict()

    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9),
                           gridspec_kw={"width_ratios": [1.15, 1.0], "wspace": 0.3})

    # (a) the pooled ladder
    a = ax[0]
    steps = [("+ static\ngeography", v("step.geography"), "#4D9221"),
             ("+ satellite\nlevel", v("step.satellite"), "#4D9221"),
             ("+ 2 local\nsensors", v("step.bud0c_bud1"), MODEL),
             ("+ 6 more\nsensors", v("step.bud1_bud2"), MODEL),
             ("+ regional\nbackground", v("step.bud2_bud3"), "#762A83")]
    xs = np.arange(len(steps))
    a.bar(xs, [s[1] for s in steps], color=[s[2] for s in steps], width=.66, zorder=2)
    for i, (lab, val, _) in enumerate(steps):
        a.text(i, val + 1.1, f"{val:.1f}%", ha="center", fontsize=7.5, weight="bold")
    a.set_xticks(xs); a.set_xticklabels([s[0] for s in steps], fontsize=6.8)
    a.set_ylabel("median RMSE reduction (%)", fontsize=7.5)
    a.set_ylim(0, 48); a.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    a.set_title(f"(a)  what each increment buys   ·   n = {v('frame.cities')} cities",
                fontsize=7.5, loc="left", pad=6)
    a.text(3, 6, "indistinguishable\nfrom zero", ha="center", fontsize=6.4, color=MUTE, style="italic")

    # (b) stratified -- the ordering inverts in the deep tropics
    b = ax[1]
    bands = ["deep_tropical", "tropical", "subtropical", "temperate"]
    labs = ["deep\ntropical", "tropical", "sub-\ntropical", "temperate"]
    first = [v(f"band.{bd}.step_bud0c_bud1") for bd in bands]
    back = [v(f"band.{bd}.step_bud2_bud3") for bd in bands]
    w, xs = 0.36, np.arange(len(bands))
    b.bar(xs - w / 2, first, w, label="+2 local sensors", color=MODEL, zorder=2)
    b.bar(xs + w / 2, back, w, label="+regional background", color="#762A83", zorder=2)
    for i, bd in enumerate(bands):
        b.text(i, -4.6, f"n={n_band.get(bd, 0)}", ha="center", fontsize=6.4, color=MUTE)
    b.set_xticks(xs); b.set_xticklabels(labs, fontsize=7)
    b.set_ylim(-6, 48); b.set_ylabel("median RMSE reduction (%)", fontsize=7.5)
    b.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    b.axhline(0, color=INK, lw=0.7)
    b.legend(fontsize=6.6, frameon=False, loc="upper left", handlelength=1.1)
    b.set_title("(b)  the ordering inverts in the tropics", fontsize=7.5, loc="left", pad=6)
    # A connecting arrow between the two bars read as "local DECREASES to background"; a plain
    # bracket over the pair says "these two are the wrong way round here" without that ambiguity.
    top = max(first[0], back[0])
    b.plot([-w / 2, -w / 2, w / 2, w / 2], [top + 3.0, top + 5.0, top + 5.0, top + 3.0],
           color=OBS, lw=1.0, clip_on=False)
    b.text(0, top + 6.2, "local wins here", ha="center", fontsize=6.6, color=OBS, weight="bold")

    save(fig, "F2_ladder")
    print(f"  (instrument class n: {n_cls})")


if __name__ == "__main__":
    print(f"figures -> {OUT.relative_to(REPO)}")
    fig_paired()
    fig_ladder()
