"""The new thesis figures. Every one is built from a file already on disk.

Numbered by chapter, matching monograph_plan_2026-09-04.md. Figures that already exist and are
current (the paper's suite, regenerated 2026-09-03 or later) are not rebuilt here; this module
covers only what the plan lists as new.

⚠ NOTHING HERE IS ILLUSTRATIVE. Where a figure shows a quantity, that quantity is read from a
scored file. Where a figure is a schematic, it is drawn as one and says so in its caption.

Usage: python f_chapters.py [--only F1_1]
Out:   thesis/figures/*.png and .pdf
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from thesisviz import C, FIGURES, save_fig, style

REPO = Path(r"D:\ProjectCD\kandy_pm25")
MOD = REPO / "data" / "processed" / "modular"
DEC = REPO / "data" / "processed" / "decomp"
LOCS = REPO / "data" / "external" / "openaq" / "discovery" / "global_locations.csv"
CLAIMS = json.load(open(MOD / "claims.json", encoding="utf-8"))["claims"]
FIGDATA = REPO / "data" / "processed" / "paper_figures"


def fd(name: str) -> dict:
    """Values emitted by a test script. Read, never retyped."""
    return json.load(open(FIGDATA / f"{name}.json", encoding="utf-8"))


def cv(tag: str) -> float:
    return CLAIMS[tag]["value"]


def band_of(lat: float) -> str:
    a = abs(lat)
    return ("deep tropical" if a < 15 else "tropical" if a < 23.5
            else "subtropical" if a < 35 else "temperate")


# ── 1.1 the observing asymmetry ───────────────────────────────────────────────────────────

def f1_1_observing_density():
    """Chapter 1. Where the world measures particulate matter, and where it does not.

    The point of Chapter 1 is that weather has a dense global observing network and air quality
    does not. This is the air quality half, drawn from every location OpenAQ publishes. The
    weather comparison is a cited count rather than a second map, because the synoptic network
    is not ours to plot and a licensed figure was ruled out.
    """
    style()
    d = pd.read_csv(LOCS).dropna(subset=["lat", "lon"])
    ref = d[d.is_monitor.astype(str).str.lower().isin(["true", "1"])]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6),
                                 gridspec_kw=dict(width_ratios=[1.85, 1]))

    a1.scatter(d.lon, d.lat, s=1.4, c=C["muted"], alpha=0.30, lw=0, label="all PM2.5 locations")
    a1.scatter(ref.lon, ref.lat, s=1.6, c=C["local"], alpha=0.55, lw=0,
               label="reference grade")
    a1.plot(80.63, 7.29, marker="*", ms=15, color=C["ink"], zorder=5)
    a1.text(80.63 + 6, 7.29, "Kandy", fontsize=10, va="center")
    for y in (-23.5, 23.5):
        a1.axhline(y, color=C["line"], lw=0.6, ls=":")
    a1.text(-178, 24.6, "tropics", fontsize=8.5, color=C["muted"])
    a1.set_xlim(-180, 180); a1.set_ylim(-60, 80)
    a1.set_xlabel("longitude"); a1.set_ylabel("latitude")
    a1.legend(loc="lower left", frameon=True, framealpha=0.92, fontsize=8.5, markerscale=6)
    a1.set_title(f"{len(d):,} openly published PM2.5 locations worldwide", fontsize=10)

    # by absolute latitude, which is where the deficit actually shows
    bins = np.arange(0, 75, 5)
    allc, _ = np.histogram(np.abs(d.lat), bins=bins)
    refc, _ = np.histogram(np.abs(ref.lat), bins=bins)
    ctr = bins[:-1] + 2.5
    a2.barh(ctr, allc, height=4.2, color=C["muted"], alpha=0.35, label="all")
    a2.barh(ctr, refc, height=4.2, color=C["local"], alpha=0.75, label="reference")
    a2.axhline(7.29, color=C["ink"], lw=1.2, ls="--")
    a2.text(allc.max() * 0.97, 9.5, "Kandy", ha="right", fontsize=9.5)
    a2.set_ylabel("absolute latitude"); a2.set_xlabel("locations")
    a2.legend(frameon=False, fontsize=9)
    a2.set_title("the deficit is a latitude deficit", fontsize=10)

    fig.tight_layout()
    return fig, "F1_1_observing_density"


# ── 2.2 who could be scored at all ────────────────────────────────────────────────────────

def f2_2_reference_by_band():
    """Chapter 2. How many cities in each band could support a dense validation at all.

    This is the constraint that no amount of care in sampling can remove, and it is the reason
    Chapter 7 reports everything stratified.
    """
    style()
    d = pd.read_csv(MOD / "global_reference_census.csv")
    order = ["deep_tropical", "tropical", "subtropical", "temperate"]
    nice = {"deep_tropical": "deep tropical", "tropical": "tropical",
            "subtropical": "subtropical", "temperate": "temperate"}
    counts = [int((d.band == b).sum()) for b in order]

    fig, ax = plt.subplots(figsize=(6.6, 3.3))
    cols = [C["local"], C["local"], C["regional"], C["free"]]
    bars = ax.barh([nice[b] for b in order], counts, color=cols, alpha=0.85, height=0.62)
    for b, n in zip(bars, counts):
        ax.text(n + max(counts) * 0.015, b.get_y() + b.get_height() / 2, str(n),
                va="center", fontsize=11)
    ax.set_xlabel("cities with ten or more concurrent reference monitors")
    ax.set_xlim(0, max(counts) * 1.14)
    ax.annotate("Kandy's band", xy=(counts[0], 0), xytext=(max(counts) * 0.42, 0.55),
                fontsize=10, color=C["local"],
                arrowprops=dict(arrowstyle="->", color=C["local"], lw=1.1))
    ax.set_title(f"{int(cv('census.temperate_over_deep_tropical'))}"
                 f" times as many in the temperate band as in the deep tropics",
                 fontsize=10.5, pad=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    return fig, "F2_2_reference_by_band"


# ── 3.2 the roadside transect ─────────────────────────────────────────────────────────────

def f3_2_transect():
    """Chapter 3. The measurement that sets the whole spatial problem.

    A 25 site roadside survey across Kandy found concentrations falling from 110 to 4 over
    300 m inside one botanical garden. That is the observation Chapter 8 has to explain.
    """
    style()
    d = pd.read_csv(DEC / "elangasinghe_spatial_test.csv")
    d = d.dropna(subset=["obs", "model"])

    # 🔴 NOT a 1:1 scatter. The survey measured PM10 at the roadside over three hours and the
    # model reports PM2.5 as a cell mean, so the two have no common scale and a 1:1 line would
    # assert a comparison that does not exist. What IS comparable is the SPREAD, which is the
    # claim the figure exists to support, so each series is shown relative to its own median.
    cens = d.cens.astype(str).str.lower().isin(["true", "1"])
    d = d.assign(o_rel=d.obs / d.obs.median(), m_rel=d.model / d.model.median())
    d = d.sort_values("o_rel").reset_index(drop=True)
    x = np.arange(len(d))

    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    ax.plot(x, d.o_rel, marker="o", ms=7, lw=1.2, color=C["local"],
            label=f"observed, roadside PM10 ({len(d)} sites)")
    # Censored sites report a common upper value, which means "at least this". Drawn as open
    # markers so they are not read as measurements.
    ax.scatter(x[cens.values], d.o_rel[cens.values], s=70, facecolor="white",
               edgecolor=C["local"], lw=1.4, zorder=4)
    ax.plot(x, d.m_rel, marker="s", ms=6, lw=1.2, color=C["free"],
            label="model PM2.5 at the same locations")
    ax.axhline(1.0, color=C["muted"], lw=0.8, ls=":")

    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([str(i + 1) for i in x], fontsize=8.5)
    ax.set_xlabel("survey site, ordered by observed concentration")
    ax.set_ylabel("value relative to that series' own median")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.scatter([], [], s=70, facecolor="white", edgecolor=C["local"], lw=1.4,
               label="censored")
    ax.text(0.02, 0.02, f"observed spread {cv('spatial.obs_spread'):.0f} times, "
                        f"model spread {cv('spatial.model_spread'):.2f} times",
            transform=ax.transAxes, fontsize=9.5, color=C["muted"])
    ax.set_title("The survey and the model are different quantities, so only spread is "
                 "comparable", fontsize=10.5, pad=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    return fig, "F3_2_transect"


# ── 4.3 the panel ─────────────────────────────────────────────────────────────────────────

def f4_3_panel():
    """Chapter 4. The cities the validation borrows its ground truth from."""
    style()
    L = pd.read_csv(MOD / "ladder_revalidated.csv", dtype={"city": str})
    L = L[L.bottom == "Bud0c"]
    v = pd.read_csv(MOD / "validation_frame.csv", dtype={"slug": str})
    m = v.drop_duplicates("slug").set_index("slug")
    L["lat"] = L.city.map(m.lat)
    L["lon"] = L.city.map(m.lon)
    L = L.dropna(subset=["lat", "lon"])

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.5),
                                 gridspec_kw=dict(width_ratios=[1.9, 1]))
    d = pd.read_csv(LOCS).dropna(subset=["lat", "lon"])
    a1.scatter(d.lon, d.lat, s=0.7, c="#d9d9d9", lw=0)
    sizes = 14 + 3.0 * L.n_held.fillna(0)
    a1.scatter(L.lon, L.lat, s=sizes, c=C["local"], alpha=0.75, edgecolor="white", lw=0.8,
               label="panel city, sized by withheld monitors")
    a1.plot(80.63, 7.29, marker="*", ms=16, color=C["ink"], zorder=5)
    a1.text(80.63 + 6, 7.29, "Kandy, the target", fontsize=10, va="center")
    a1.set_xlim(-180, 180); a1.set_ylim(-60, 80)
    a1.set_xlabel("longitude"); a1.set_ylabel("latitude")
    a1.legend(loc="lower left", frameon=True, framealpha=0.92, fontsize=8.5)
    a1.set_title(f"{int(cv('frame.cities'))} cities, {int(cv('frame.countries'))} countries",
                 fontsize=10)

    order = ["deep_tropical", "tropical", "subtropical", "temperate"]
    lab = ["deep trop.", "tropical", "subtrop.", "temperate"]
    n = [int((L.band == b).sum()) for b in order]
    a2.bar(lab, n, color=[C["local"], C["local"], C["regional"], C["free"]], alpha=0.85)
    for i, k in enumerate(n):
        a2.text(i, k + 0.4, str(k), ha="center", fontsize=10.5)
    a2.set_ylabel("cities"); a2.set_ylim(0, max(n) * 1.2)
    a2.tick_params(axis="x", rotation=20)
    a2.set_title("by latitude band", fontsize=10)
    for s in ("top", "right"):
        a2.spines[s].set_visible(False)
    fig.tight_layout()
    return fig, "F4_3_panel"


# ── 5.5 the dispersion step ───────────────────────────────────────────────────────────────

def f5_5_dispersion_costs():
    """Chapter 5. The step that was supposed to place the increment, and takes skill away.

    Two independent frames agree, which is why this is the strongest argument in the thesis
    for revisiting the spatial construction rather than abandoning it.
    """
    style()
    r2 = pd.read_csv(MOD / "r2_atransport.csv")
    r2 = r2[r2.city != "MEDIAN"].dropna(subset=["rho_S", "rho_C"])
    p0 = pd.read_csv(MOD / "phase0_sector_surface.csv").dropna(subset=["ntl", "ntl_disp"])

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.9))

    for ax, before, after, names, title in (
        (a1, r2.rho_S.values, r2.rho_C.values, r2.city.values,
         "frame one: ten valley cities"),
        (a2, p0.ntl.values, p0.ntl_disp.values, p0.city.values,
         "frame two: eight cities, different selection"),
    ):
        for b, a_, nm in zip(before, after, names):
            col = C["good"] if a_ > b else C["bad"]
            ax.plot([0, 1], [b, a_], color=col, lw=1.3, alpha=0.75, marker="o", ms=5)
        ax.axhline(0, color=C["muted"], lw=0.8, ls=":")
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["source\nsurface", "after the\ndispersion solver"])
        ax.set_xlim(-0.25, 1.25)
        ax.set_ylabel(r"rank correlation $\rho$ at held-out stations")
        worse = int((after < before).sum())
        ax.set_title(f"{title}\nworse in {worse} of {len(before)}", fontsize=10)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    fig.suptitle("The step meant to place the increment removes rank on both frames",
                 fontsize=11, y=1.01)
    fig.tight_layout()
    return fig, "F5_5_dispersion_costs"


# ── 9.1 what to buy, pooled against Kandy's band ──────────────────────────────────────────

def f9_1_acquisition():
    """Chapter 9. The recommendation, and the fact that it inverts for the target city."""
    style()
    pooled = [cv("step.bud0c_bud1"), cv("step.bud2_bud3")]
    band = [cv("maiac.deep_tropical_first2"), cv("maiac.deep_tropical_background")]

    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    x = np.arange(2)
    w = 0.36
    ax.bar(x - w / 2, pooled, w, color=C["muted"], alpha=0.55,
           label="pooled across all 48 cities")
    ax.bar(x + w / 2, band, w, color=C["local"], alpha=0.85,
           label="Kandy's own latitude band")
    for xi, (p, b) in enumerate(zip(pooled, band)):
        ax.text(xi - w / 2, p + 0.9, f"{p:.1f}", ha="center", fontsize=10, color=C["muted"])
        ax.text(xi + w / 2, b + 0.9, f"{b:.1f}", ha="center", fontsize=10.5, color=C["local"])
    ax.set_xticks(x)
    ax.set_xticklabels(["two local sensors", "a regional background station"])
    ax.set_ylabel("median reduction in daily RMSE (per cent)")
    ax.set_ylim(0, max(max(pooled), max(band)) * 1.22)
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    ax.set_title("The pooled ordering reverses in the band the target city belongs to",
                 fontsize=10.5, pad=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    return fig, "F9_1_acquisition"


# ── 9.2 the learned pattern against its bar ───────────────────────────────────────────────

def f9_2_learned_bar():
    """Chapter 9, cross referenced from Chapter 5. The registered test and its outcome."""
    style()
    d = pd.read_csv(MOD / "phase2_learned_pattern.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.7),
                                 gridspec_kw=dict(width_ratios=[1, 1.25]))

    L = fd("phase2_learned")
    names = ["ridge", "MLP", "random\nforest", "best single\npredictor"]
    vals = [L["rho_ridge"], L["rho_mlp"], L["rho_rf"], L["rho_baseline"]]
    cols = [C["muted"], C["muted"], C["local"], C["free"]]
    a1.bar(names, vals, color=cols, alpha=0.85)
    a1.axhline(L["bar"], color=C["bad"], lw=1.6, ls="--")
    a1.text(3.4, L["bar"] + 0.007, f"the registered bar, {L['bar']}", ha="right",
            fontsize=9.5, color=C["bad"])
    for i, v in enumerate(vals):
        a1.text(i, v + 0.012, f"{v:.3f}", ha="center", fontsize=9.5)
    a1.set_ylabel(r"median per-city $\rho$")
    a1.set_ylim(0, L["bar"] * 1.16)
    a1.set_title("nothing learned reaches the bar", fontsize=10)
    for s in ("top", "right"):
        a1.spines[s].set_visible(False)

    dd = d.dropna(subset=["learned", "baseline"])
    a2.scatter(dd.baseline, dd.learned, s=55, color=C["local"], alpha=0.7,
               edgecolor="white", lw=0.9)
    lim = [-1.02, 1.02]
    a2.plot(lim, lim, ls="--", lw=1.0, color=C["muted"])
    a2.axhline(0, color=C["muted"], lw=0.6, ls=":")
    a2.axvline(0, color=C["muted"], lw=0.6, ls=":")
    a2.set_xlim(lim); a2.set_ylim(lim)
    a2.set_xlabel(r"best single predictor, per city $\rho$")
    a2.set_ylabel(r"learned pattern, per city $\rho$")
    better = int((dd.learned > dd.baseline).sum())
    a2.set_title(f"city by city: learned is better in {better} of {len(dd)}", fontsize=10)
    for s in ("top", "right"):
        a2.spines[s].set_visible(False)

    fig.tight_layout()
    return fig, "F9_2_learned_bar"


# ── 9.3 skill against buffer radius ───────────────────────────────────────────────────────

def f9_3_radius():
    """Chapter 9, and it is the most surprising figure in the thesis.

    The information that ranks stations lives at scales LARGER than the cell the model reports
    on. Read with the within-cell result of Chapter 8, the usable band is squeezed from both
    sides.
    """
    style()
    R = pd.read_csv(MOD / "phase1_predictor_ranking.csv")
    fams = {"lc_built": "built-up land cover", "pop": "population",
            "ntl": "night lights", "nres": "non-residential built",
            "road_major": "major roads"}
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    cols = [C["local"], C["free"], C["regional"], C["muted"], C["good"]]
    for (pre, lab), col in zip(fams.items(), cols):
        sub = R[R.predictor.str.match(rf"^{pre}_\d+$")].copy()
        if sub.empty:
            continue
        sub["r"] = sub.predictor.str.extract(r"_(\d+)$").astype(int)
        sub = sub.sort_values("r")
        ax.plot(sub.r, sub.median_rho, marker="o", ms=5.5, lw=1.5, color=col, label=lab)
    ax.axvline(1000, color=C["ink"], lw=1.1, ls="--")
    ax.text(1040, 0.028, "the model reports\nat 1 km", fontsize=9.5, color=C["ink"])
    ax.set_xscale("log")
    ax.set_xlabel("buffer radius around the station (m)")
    ax.set_ylabel(r"median per-city rank correlation $\rho$")
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    ax.set_title("Skill rises with radius and peaks coarser than the reporting cell",
                 fontsize=10.5, pad=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    return fig, "F9_3_radius"


BUILDERS = {
    "F1_1": f1_1_observing_density,
    "F2_2": f2_2_reference_by_band,
    "F3_2": f3_2_transect,
    "F4_3": f4_3_panel,
    "F5_5": f5_5_dispersion_costs,
    "F9_1": f9_1_acquisition,
    "F9_2": f9_2_learned_bar,
    "F9_3": f9_3_radius,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    todo = [a.only] if a.only else list(BUILDERS)

    from PIL import Image
    for key in todo:
        try:
            fig, name = BUILDERS[key]()
        except Exception as e:                                              # noqa: BLE001
            print(f"  {key:<6} FAILED  {type(e).__name__}: {str(e)[:70]}")
            continue
        if fig is None:
            continue
        p = save_fig(fig, name, FIGURES)
        w, h = Image.open(p).size
        flag = "" if 0.8 <= w / h <= 3.0 else "   <-- aspect"
        print(f"  {key:<6} {name:<30} {w}x{h}  {w/h:.2f}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
