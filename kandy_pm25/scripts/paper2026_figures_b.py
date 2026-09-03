"""Figures 3-6 for the 2026 rewrite. Companion to paper2026_figures.py.

Kept separate so the two files can be edited independently; the style constants and the claims
accessor are imported rather than duplicated, so a colour or a number changed in one place
changes in both.

  F3 streams      sections 4.4 and 4.5 -- the same monitors priced by four models, and what
                  swapping a fused covariate for a raw one moves (and does not move).
  F4 confounds    section 4.6 -- the instrument-class confound that cannot be sampled away.
  F5 withinpixel  section 5.6 -- the spread inside a cell against the spread across the map,
                  and why the validation of it is uninformative.
  F6 chemistry    section 6.4 -- secondary fraction by air-mass origin, including the
                  registered prediction that failed.

Usage:  .venv/Scripts/python.exe scripts/paper2026_figures_b.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from paper2026_figures import C, v, save, MOD, INK, MUTE, OBS, MODEL, FINE, GRID  # noqa: E402


def fig_streams():
    """4.4 and 4.5. Two results that are easy to state and hard to believe from text: a linear
    model prices the same monitor at four times the value, and swapping a fused covariate for a
    raw one leaves the satellite rung alone while doubling the rung above it."""
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={"wspace": 0.36})

    a = ax[0]
    L = [("ridge (linear)", v("learner.ridge_linear.step_bud0c_bud1"), OBS),
         ("gradient boosting", v("learner.histgbm_shipped.step_bud0c_bud1"), MODEL),
         ("gradient boosting,\nshallow", v("learner.histgbm_shallow.step_bud0c_bud1"), MODEL),
         ("random forest", v("learner.randomforest.step_bud0c_bud1"), MODEL)]
    yy = np.arange(len(L))[::-1]
    a.barh(yy, [x[1] for x in L], color=[x[2] for x in L], height=.58, zorder=2)
    for y, (lab, val, _) in zip(yy, L):
        a.text(val + 1.2, y, f"{val:.1f}%", va="center", fontsize=7.5, weight="bold")
    a.set_yticks(yy); a.set_yticklabels([x[0] for x in L], fontsize=6.8)
    a.set_xlim(0, 62)
    a.set_xlabel("measured value of the first two monitors (%)", fontsize=7.5)
    a.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    a.set_title("(a)  the same monitors, four models", fontsize=7.5, loc="left", pad=6)
    a.plot([17.5, 17.5], [0.35, 2.65], color=MUTE, lw=0.8)
    a.text(19, 1.5, f"non-linear:\nspread {v('learner.nonlinear_spread_bud0c_bud1')} pp",
           fontsize=6.4, color=MUTE, va="center")

    b = ax[1]
    # Short labels: the full phrase ran the two monitor categories into each other.
    groups = ["satellite\nrung", "monitors 1–2\npooled", "monitors 1–2\ndeep tropics"]
    fused = [v("c1.step_fused_ghap"), v("step.bud0c_bud1"),
             v("band.deep_tropical.step_bud0c_bud1")]
    raw = [v("c1.step_raw_aod"), v("maiac.step_bud0c_bud1"), v("maiac.deep_tropical_first2")]
    w, xs = 0.36, np.arange(3)
    b.bar(xs - w / 2, fused, w, label="fused product", color="#B8A0C9", zorder=2)
    b.bar(xs + w / 2, raw, w, label="raw satellite AOD", color="#4D9221", zorder=2)
    for i, (f_, r_) in enumerate(zip(fused, raw)):
        b.text(i - w / 2, f_ + 1.0, f"{f_:.1f}", ha="center", fontsize=6.8)
        b.text(i + w / 2, r_ + 1.0, f"{r_:.1f}", ha="center", fontsize=6.8, weight="bold")
    b.set_xticks(xs); b.set_xticklabels(groups, fontsize=6.5)
    b.set_ylim(0, 56); b.set_ylabel("median RMSE reduction (%)", fontsize=7.5)
    b.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    b.legend(fontsize=6.5, frameon=False, loc="upper left", handlelength=1.1)
    b.set_title("(b)  the contamination is not where we looked for it",
                fontsize=7.5, loc="left", pad=6)
    b.text(0, 11, "unchanged", ha="center", fontsize=6.4, color=MUTE, style="italic")
    b.annotate("", xy=(2 + w / 2, raw[2] - 2), xytext=(2 - w / 2, fused[2] + 2),
               arrowprops=dict(arrowstyle="->", color=OBS, lw=1.2))
    b.text(2.42, 34, "doubles", fontsize=6.6, color=OBS, weight="bold",
           rotation=90, va="center", ha="center")
    save(fig, "F3_streams")


def fig_confounds():
    """4.6. The confound that cannot be sampled away. A bar of it is more honest than a
    sentence claiming it."""
    lad = pd.read_csv(MOD / "ladder_revalidated.csv")
    x = lad[(lad.bottom == "Bud0c") & lad.band.notna()]
    ct = pd.crosstab(x.band, x.cls)
    for c_ in ("LCS", "reference"):
        if c_ not in ct:
            ct[c_] = 0
    order = [b for b in ["deep_tropical", "tropical", "subtropical", "temperate"] if b in ct.index]
    ct = ct.reindex(order)
    share = 100 * ct.LCS / (ct.LCS + ct.reference)

    fig, ax = plt.subplots(figsize=(4.4, 2.7))
    yy = np.arange(len(ct))[::-1]
    ax.barh(yy, share.values, color=MODEL, height=.6, zorder=2, label="low-cost")
    ax.barh(yy, 100 - share.values, left=share.values, color="#BDBDBD", height=.6, zorder=2,
            label="reference")
    for y, bd in zip(yy, ct.index):
        ax.text(3, y, f"{share[bd]:.0f}% low-cost", va="center", fontsize=6.8, color="white",
                weight="bold")
        ax.text(101.5, y, f"n={int(ct.loc[bd].sum())}", va="center", fontsize=6.4, color=MUTE)
    ax.set_yticks(yy)
    ax.set_yticklabels([b.replace("_", "\n") for b in ct.index], fontsize=7)
    ax.set_xlim(0, 114); ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("share of each band's cities, by instrument class", fontsize=7.5)
    ax.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    ax.legend(fontsize=6.4, frameon=False, loc="lower right", handlelength=1.1)
    ax.set_title("instrument class is confounded with latitude,\nand cannot be sampled away",
                 fontsize=7.5, loc="left", pad=6)
    save(fig, "F4_confounds")


def fig_withinpixel():
    """5.6. The most counter-intuitive number in the paper, and the honest statement that the
    check on it does not discriminate."""
    d = pd.read_csv(MOD / "s2_within_pixel.csv")
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.7),
                           gridspec_kw={"width_ratios": [1, 1.2], "wspace": 0.34})

    a = ax[0]
    vals = [v("s2.between_pixel_p90p10"), v("s2.within_pixel_p90p10")]
    a.bar([0, 1], vals, color=[MUTE, MODEL], width=.55, zorder=2)
    for i, val in enumerate(vals):
        a.text(i, val + 0.008, f"{val:.3f}×", ha="center", fontsize=8, weight="bold")
    a.set_xticks([0, 1])
    a.set_xticklabels(["between cells\n(across the map)", "within a cell\n(typical)"], fontsize=7)
    a.set_ylim(1.0, 1.28); a.set_ylabel("spread (p90/p10)", fontsize=7.5)
    a.axhline(1.0, color=INK, lw=0.7)
    a.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    a.set_title("(a)  most variation is inside a cell", fontsize=7.5, loc="left", pad=6)

    b = ax[1]
    q = d[d.kind == "site_quantile"].copy()
    if len(q):
        q["obs"] = [float(str(n).split("=")[-1]) for n in q.note.fillna("obs=nan")]
        b.scatter(q.obs, q.value, s=30, color=OBS, zorder=3, edgecolor="white", linewidth=.7)
        b.set_xscale("log")
        b.set_xlabel("observed at the site (µg m$^{-3}$, PM$_{10}$)", fontsize=7.5)
        b.set_ylabel("quantile within its own cell", fontsize=7.5)
        b.set_ylim(-0.12, 1.16); b.set_yticks([0, .25, .5, .75, 1])
        b.axhline(1.0, color=MUTE, lw=0.6, ls=":")
        b.axhline(0.0, color=MUTE, lw=0.6, ls=":")
        b.grid(color=GRID, lw=0.5, zorder=0)
        b.text(0.5, 0.52, "every site saturates at 0 or 1:\nthe test re-detects the amplitude "
                          "gap\nrather than testing ordering", transform=b.transAxes,
               ha="center", fontsize=6.3, color=MUTE, style="italic")
    b.set_title("(b)  and the check on it is uninformative", fontsize=7.5, loc="left", pad=6)
    save(fig, "F5_withinpixel")


def fig_chemistry():
    """6.4. The decomposition's first chemical corroboration, with the prediction that failed
    marked inside it rather than relegated to the caption."""
    d = pd.read_csv(MOD / "chemistry_origin_test.csv")
    s = d[d.kind == "sector"].copy().sort_values("sec_frac").reset_index(drop=True)
    nice = {"SW_marine": "Indian Ocean\n(south-west)", "other": "other",
            "local_recirc": "local\nrecirculation", "BoB_marine": "Bay of Bengal",
            "Penin_India": "peninsular\nIndia", "IGP_E_India": "Indo-Gangetic\nPlain"}
    col = {"SW_marine": "#2166AC", "BoB_marine": "#67A9CF", "other": "#BDBDBD",
           "local_recirc": "#4D9221", "Penin_India": "#D6604D", "IGP_E_India": "#B2182B"}

    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    yy = np.arange(len(s))[::-1]
    ax.barh(yy, s.sec_frac, color=[col.get(x, MUTE) for x in s.label], height=.6, zorder=2)
    ax.errorbar(s.sec_frac, yy, xerr=[s.sec_frac - s.lo95, s.hi95 - s.sec_frac],
                fmt="none", ecolor=INK, elinewidth=0.9, capsize=2, zorder=4)
    for y, r in zip(yy, s.itertuples()):
        ax.text(r.hi95 + 0.005, y, f"n={int(r.n)}", va="center", fontsize=6.2, color=MUTE)
    ax.set_yticks(yy); ax.set_yticklabels([nice.get(x, x) for x in s.label], fontsize=6.8)
    ax.set_xlim(0.28, 0.58)
    ax.set_xlabel("secondary fraction  (aged-aerosol signature)", fontsize=7.5)
    ax.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    ax.set_title("continental air is more aged than marine air —\nbut recirculated local air is "
                 "not the freshest", fontsize=7.5, loc="left", pad=6)
    if "local_recirc" in list(s.label):
        i = list(s.label).index("local_recirc")
        ax.annotate("registered prediction\nfailed here", xy=(s.sec_frac[i], yy[i]),
                    xytext=(0.50, yy[i] + 1.5), fontsize=6.3, color=OBS, ha="center",
                    arrowprops=dict(arrowstyle="->", color=OBS, lw=0.9))
    save(fig, "F6_chemistry")


def fig_protocol():
    """3.1. The withholding design. The 2026-08 version of this figure showed the ELEVEN-city
    panel and is stale by 37 cities; panel (a)'s logic survives, panel (b) is rebuilt from the
    scored file so it cannot drift again."""
    lad = pd.read_csv(MOD / "ladder_revalidated.csv")
    x = lad[lad.bottom == "Bud0c"].copy()

    fig = plt.figure(figsize=(7.2, 3.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 2.0], width_ratios=[1, 1], hspace=0.62,
                          wspace=0.3)

    # (a) the protocol, as a chain
    a = fig.add_subplot(gs[0, :]); a.axis("off")
    steps = [("a city with a dense\nnetwork of N monitors", "#EFEFEF", INK),
             ("keep two,\nwithhold the rest", "#FBE9E7", OBS),
             ("run the identical\npipeline, no tuning", "#EFEFEF", INK),
             ("score against the\nN−2 withheld", "#E8F0F8", MODEL),
             ("apply unchanged\nat the target city", "white", INK)]
    for i, (txt, fc, ec) in enumerate(steps):
        xx = i / len(steps) + 0.008
        a.add_patch(plt.Rectangle((xx, 0.28), 1 / len(steps) - 0.028, 0.5, transform=a.transAxes,
                                  facecolor=fc, edgecolor=ec, lw=1.0, zorder=2,
                                  clip_on=False))
        a.text(xx + (1 / len(steps) - 0.028) / 2, 0.53, txt, transform=a.transAxes,
               ha="center", va="center", fontsize=6.3, color=ec, zorder=3)
        if i < len(steps) - 1:
            a.annotate("", xy=(xx + 1 / len(steps) - 0.026, 0.53),
                       xytext=(xx + 1 / len(steps) - 0.030, 0.53), transform=a.transAxes,
                       arrowprops=dict(arrowstyle="->", color=MUTE, lw=0.9))
    a.text(0.5, 0.02, "The budget match is what makes the test informative: a model that has "
                      "seen thirty monitors\nmeasures a capability the target city will never "
                      "have.", transform=a.transAxes, ha="center", va="top", fontsize=6.4,
           color=MUTE)
    a.set_title("(a)  the protocol", fontsize=7.5, loc="left", pad=2)

    # (b) how many monitors each city actually had withheld
    b = fig.add_subplot(gs[1, 0])
    held = x.n_held.dropna().astype(int)
    b.hist(held, bins=range(int(held.min()), int(held.max()) + 2), color=MODEL,
           edgecolor="white", linewidth=.6, zorder=2)
    b.axvline(held.median(), color=OBS, lw=1.2, ls="--", zorder=3)
    b.text(held.median() + 0.12, b.get_ylim()[1] * 0.86, f"median {held.median():.0f}",
           fontsize=6.5, color=OBS)
    b.set_xlabel("withheld monitors scored against, per city", fontsize=7.2)
    b.set_ylabel("cities", fontsize=7.2)
    b.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    b.set_title(f"(b)  {len(x)} cities, not the 11 of the pilot", fontsize=7.5, loc="left", pad=5)

    # (c) and over how long
    c = fig.add_subplot(gs[1, 1])
    days = x.n_days.dropna()
    c.hist(days, bins=12, color="#4D9221", edgecolor="white", linewidth=.6, zorder=2)
    c.axvline(days.median(), color=OBS, lw=1.2, ls="--", zorder=3)
    c.text(days.median() * 1.04, c.get_ylim()[1] * 0.86, f"median {days.median():.0f} d",
           fontsize=6.5, color=OBS)
    c.set_xlabel("scored city-days", fontsize=7.2)
    c.set_ylabel("cities", fontsize=7.2)
    c.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    c.set_title(f"(c)  {int(x.n_days.sum()):,} city-days in total", fontsize=7.5, loc="left",
                pad=5)
    save(fig, "F7_protocol")


if __name__ == "__main__":
    fig_streams()
    fig_confounds()
    fig_withinpixel()
    fig_chemistry()
    fig_protocol()
