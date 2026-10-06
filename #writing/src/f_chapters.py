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

from thesisviz import C, FIGURES, ne_geoms, natural_earth, save_fig, style

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

    import cartopy.crs as ccrs
    pc = ccrs.PlateCarree()
    fig = plt.figure(figsize=(9.6, 3.9))
    # 2026-09-19: at the 6 in column the map's latitude labels ran into the histogram's axis
    # label; the histogram moves right and narrows.
    a1 = fig.add_axes([0.0, 0.13, 0.60, 0.78], projection=ccrs.Robinson())
    a2 = fig.add_axes([0.79, 0.17, 0.20, 0.70])

    _robinson_base(a1)
    a1.scatter(d.lon, d.lat, s=1.2, c=C["muted"], alpha=0.35, lw=0, transform=pc, zorder=3,
               label="all PM2.5 locations")
    a1.scatter(ref.lon, ref.lat, s=1.5, c=C["local"], alpha=0.6, lw=0, transform=pc, zorder=4,
               label="reference grade")
    a1.plot(80.63, 7.29, marker="*", ms=13, color=C["ink"], transform=pc, zorder=6)
    import matplotlib.patheffects as pe
    a1.text(89, 4.0, "Kandy", fontsize=9.5, va="center", transform=pc, zorder=6,
            path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])
    fig.legend(*a1.get_legend_handles_labels(), loc="lower center",
               bbox_to_anchor=(0.32, 0.0), ncol=2, frameon=False, fontsize=8.5, markerscale=6)
    a1.set_title(f"{len(d):,} openly published PM2.5 locations worldwide", fontsize=10)

    # Sri Lanka at country scale: a star at world scale says nothing about the target.
    ins = fig.add_axes([0.035, 0.15, 0.10, 0.30], projection=pc)
    ins.set_extent([79.3, 82.3, 5.7, 10.1], crs=pc)
    ins.add_geometries(ne_geoms("50m", "physical", "land"), pc, facecolor=C["fill"],
                       edgecolor=C["line"], lw=0.3)
    ins.add_geometries([_country("Sri Lanka")], pc, facecolor=C["fill2"], edgecolor=C["line"],
                       lw=0.5)
    ins.plot(80.63, 7.29, marker="*", ms=8, color=C["ink"], transform=pc)
    ins.set_title("Sri Lanka", fontsize=7, pad=2)
    ins.spines["geo"].set_edgecolor(C["line"]); ins.spines["geo"].set_linewidth(0.5)

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
    return fig, "F1_1_observing_density"


def _robinson_base(ax) -> None:
    """Land, coastline, borders and a graticule, from the cached Natural Earth layers only.

    Robinson rather than an equal-area projection: both world maps argue about latitude, and
    Robinson keeps latitude bands readable where an equal-area map compresses the high ones.
    """
    import cartopy.crs as ccrs
    pc = ccrs.PlateCarree()
    ax.set_global()
    ax.add_geometries(ne_geoms("110m", "physical", "land"), pc, facecolor=C["fill"],
                      edgecolor="none", zorder=0)
    ax.add_geometries(ne_geoms("110m", "physical", "coastline"), pc, facecolor="none",
                      edgecolor=C["line"], lw=0.4, zorder=1)
    ax.add_geometries(ne_geoms("110m", "cultural", "admin_0_boundary_lines_land"), pc,
                      facecolor="none", edgecolor="#c4c4c4", lw=0.25, zorder=1)
    gl = ax.gridlines(crs=pc, xlocs=range(-180, 181, 30), ylocs=range(-60, 61, 30),
                      lw=0.3, color=C["muted"], alpha=0.45, draw_labels=True)
    # Latitude labels on the right only: on the left the Sri Lanka inset covered "60°S".
    gl.top_labels = gl.left_labels = gl.bottom_labels = False
    gl.right_labels = True
    gl.ylabel_style = dict(size=8, color=C["muted"])
    x = np.linspace(-180, 180, 361)
    for y in (-23.5, 23.5):
        ax.plot(x, np.full_like(x, y), transform=pc, color=C["local"], lw=0.6, ls=":",
                zorder=2)
    ax.text(-172, 27, "tropics", fontsize=7.5, color=C["local"], transform=pc, zorder=2)
    ax.spines["geo"].set_edgecolor(C["line"]); ax.spines["geo"].set_linewidth(0.6)


def _country(admin: str):
    from cartopy.io import shapereader
    for rec in shapereader.Reader(str(natural_earth("10m", "cultural",
                                                    "admin_0_countries"))).records():
        if rec.attributes.get("ADMIN") == admin:
            return rec.geometry
    raise KeyError(admin)


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
    ax.annotate("Kandy's band", xy=(counts[0] + max(counts) * 0.06, 0.12),
                xytext=(max(counts) * 0.42, 0.55),
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
    # The flag is attached to the frame BEFORE sorting. It was computed as a separate series and
    # then indexed by position after the sort, which drew the open markers on the four lowest
    # sites instead of the four recorded as ">150" (found 2026-09-19).
    d = d.assign(o_rel=d.obs / d.obs.median(), m_rel=d.model / d.model.median(),
                 is_cens=d.cens.astype(str).str.lower().isin(["true", "1"]))
    d = d.sort_values("o_rel", kind="stable").reset_index(drop=True)
    cens = d.is_cens
    x = np.arange(len(d))

    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    ax.plot(x, d.o_rel, marker="o", ms=7, lw=1.2, color=C["local"],
            label=f"observed PM10, the {len(d)} survey sites inside the domain")
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
    ax.scatter([], [], s=70, facecolor="white", edgecolor=C["local"], lw=1.4,
               label="recorded as \"above 150\", a lower bound")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.text(0.98, 0.02, f"observed spread {cv('spatial.obs_spread'):.0f} times, "
                        f"model spread {cv('spatial.model_spread'):.2f} times",
            transform=ax.transAxes, fontsize=9.5, color=C["muted"], ha="right")
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

    import cartopy.crs as ccrs
    from adjustText import adjust_text
    pc, rob = ccrs.PlateCarree(), ccrs.Robinson()
    L["country"] = L.city.map(m.country)
    if len(L) != int(cv("frame.cities")):
        raise ValueError(f"panel map has {len(L)} cities, claim frame.cities says "
                         f"{cv('frame.cities')}")

    # Same projection, basemap and panel geometry as Figure 1.1, so the two read as a pair.
    fig = plt.figure(figsize=(9.6, 3.9))
    a1 = fig.add_axes([0.0, 0.16, 0.58, 0.75], projection=rob)
    a2 = fig.add_axes([0.80, 0.22, 0.18, 0.65])
    _robinson_base(a1)
    d = pd.read_csv(LOCS).dropna(subset=["lat", "lon"])
    a1.scatter(d.lon, d.lat, s=0.6, c="#bdbdbd", lw=0, transform=pc, zorder=3)
    sizes = 12 + 2.6 * L.n_held.fillna(0)
    a1.scatter(L.lon, L.lat, s=sizes, c=C["local"], alpha=0.75, edgecolor="white", lw=0.6,
               transform=pc, zorder=4, label="panel city, sized by withheld monitors")
    a1.plot(80.63, 7.29, marker="*", ms=13, color=C["ink"], transform=pc, zorder=6)
    fig.legend(*a1.get_legend_handles_labels(), loc="lower center",
               bbox_to_anchor=(0.30, 0.055), frameon=False, fontsize=8.5)
    a1.set_title(f"{int(cv('frame.cities'))} cities, {int(cv('frame.countries'))} countries",
                 fontsize=10)

    # Label only the deep-tropical members, grouped by country: they are the ones the Kandy
    # argument turns on, and individually they are indistinguishable dots.
    dt = L[L.band == "deep_tropical"].groupby("country").agg(
        lat=("lat", "mean"), lon=("lon", "mean"), n=("city", "size")).reset_index()
    if int(dt.n.sum()) != int(cv("stn.dt_n")):
        raise ValueError("deep-tropical member count disagrees with claim stn.dt_n")
    # Listed under the map, not placed on it (2026-09-19): at print size the West African
    # members' labels sat on top of one another however adjustText moved them.
    import matplotlib.patheffects as pe
    kx, ky = rob.transform_points(pc, np.array([80.63]), np.array([7.29]))[0, :2]
    a1.text(kx + 6.0e5, ky - 1.2e6, "Kandy", fontsize=9, fontweight="bold", zorder=7,
            path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])
    members = ", ".join(f"{c} ({n})" if n > 1 else c for c, n in zip(dt.country, dt.n))
    import textwrap
    fig.text(0.30, 0.0, "deep-tropical members: " + "\n".join(textwrap.wrap(members, 90)),
             ha="center", va="bottom", fontsize=8, color=C["ink"])

    order = ["deep_tropical", "tropical", "subtropical", "temperate"]
    lab = ["deep tropical", "tropical", "subtropical", "temperate"]
    n = [int((L.band == b).sum()) for b in order]
    # Horizontal (2026-09-19): four band names under narrow vertical bars ran together.
    yb = np.arange(len(lab))[::-1]
    a2.barh(yb, n, color=[C["local"], C["local"], C["regional"], C["free"]], alpha=0.85)
    for yi, k in zip(yb, n):
        a2.text(k + 0.4, yi, str(k), va="center", fontsize=10)
    a2.set_yticks(yb); a2.set_yticklabels(lab)
    a2.set_xlabel("cities"); a2.set_xlim(0, max(n) * 1.3)
    a2.set_title("by latitude band", fontsize=10)
    for s in ("top", "right"):
        a2.spines[s].set_visible(False)
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
        ax.set_xticklabels(["source\nsurface", "after\ndispersion"])
        ax.set_xlim(-0.25, 1.25)
        if ax is a1:
            ax.set_ylabel(r"rank correlation $\rho$ at held-out stations")
        worse = int((after < before).sum())
        ax.set_title(f"{title}\nworse in {worse} of {len(before)}", fontsize=10)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    fig.suptitle("The step meant to place the increment removes rank on both frames",
                 fontsize=11, y=1.01)
    fig.tight_layout(w_pad=2.5)
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
    ax.set_ylim(0, max(max(pooled), max(band)) * 1.45)
    ax.legend(frameon=False, fontsize=9.5, loc="upper center", ncol=2)
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
    names = ["ridge", "MLP", "random\nforest", "best\nsingle\npredictor"]
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
    a2.set_title(f"city by city: learned is better\nin {better} of {len(dd)}", fontsize=10)
    for s in ("top", "right"):
        a2.spines[s].set_visible(False)

    fig.tight_layout(w_pad=2.5)
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


# ── the six figures from the 2026-09-09 plan ─────────────────────────────────────────────
# Each covers a finding that previously existed only as prose or a table. Every value is read
# from the scored file the corresponding claims are generated from, and where the figure
# recomputes a summary from rows it asserts the result against the stored summary, so a figure
# cannot quietly draw something the text does not say.

BAND_STYLE = {"deep_tropical": ("deep tropical", C["local"]),
              "tropical": ("tropical", C["regional"]),
              "subtropical": ("subtropical", C["muted"]),
              "temperate": ("temperate", C["free"])}


def _bands() -> pd.Series:
    L = pd.read_csv(MOD / "ladder_revalidated.csv", dtype={"city": str})
    return L[L.bottom == "Bud0c"].set_index("city").band


def _spines(*axes) -> None:
    for a in axes:
        for s in ("top", "right"):
            a.spines[s].set_visible(False)


def f7_station_count():
    """Section 7.2. Saturation at one station, which previously had no figure at all."""
    style()
    J = json.load(open(MOD / "station_count_curve.json", encoding="utf-8"))
    s = pd.read_csv(MOD / "station_count_curve.csv", dtype={"city": str})
    base = s[s.k == 0].set_index("city").rmse
    s = s[s.k > 0].assign(base=lambda x: x.city.map(base))
    s["gain"] = 100.0 * (s.base - s.rmse) / s.base
    s["band"] = s.city.map(_bands())
    pooled = s.groupby("k").gain.median()
    for k, v in J["gain_by_k"].items():
        if abs(pooled[int(k)] - v) > 0.05:
            raise ValueError(f"k={k}: recomputed {pooled[int(k)]:.3f} vs stored {v}")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.7),
                                 gridspec_kw=dict(width_ratios=[1.25, 1]))
    ks = np.arange(1, 9)
    for b, (lab, col) in BAND_STYLE.items():
        g = s[s.band == b].groupby("k").gain.median().reindex(ks)
        n = s[(s.band == b) & (s.k == 1)].city.nunique()
        a1.plot(ks, g.values, color=col, lw=0.9, alpha=0.8, label=f"{lab} ({n})")
    a1.plot(ks, pooled.reindex(ks).values, color=C["ink"], lw=2.0, marker="o", ms=4.5,
            label=f"pooled ({J['k1_cities']})", zorder=5)
    a1.errorbar([1], [J["k1_gain"]], yerr=[[J["k1_gain"] - J["k1_lo"]],
                                           [J["k1_hi"] - J["k1_gain"]]],
                fmt="none", ecolor=C["ink"], elinewidth=1.4, capsize=4, zorder=6)
    a1.annotate(f"one station: {cv('stn.one_gain')} per cent",
                xy=(1, J["k1_gain"]), xytext=(1.6, 3.0), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=C["ink"], lw=0.9))
    a1.set_xticks(ks)
    a1.set_xlabel("local stations admitted")
    a1.set_ylabel("median reduction in daily error (%)")
    a1.set_ylim(0, max(40, float(s.groupby(["band", "k"]).gain.median().max()) + 5))
    a1.legend(frameon=False, fontsize=8, loc="upper left", ncol=2, bbox_to_anchor=(0, 1.0))
    a1.set_ylim(0, a1.get_ylim()[1] + 14)
    a1.set_title("the curve is flat from the first station", fontsize=10)

    pv = J["paired_vs_one"]
    kk = sorted(int(k) for k in pv)
    med = np.array([pv[str(k)]["median"] for k in kk])
    lo = np.array([pv[str(k)]["lo"] for k in kk])
    hi = np.array([pv[str(k)]["hi"] for k in kk])
    a2.axhline(0, color=C["muted"], lw=0.8)
    a2.errorbar(kk, med, yerr=[med - lo, hi - med], fmt="o", color=C["ink"], ms=4.5,
                ecolor=C["line"], elinewidth=1.1, capsize=3)
    a2.set_xticks(kk)
    a2.set_xlabel("local stations admitted")
    a2.set_ylabel("gain over one station\n(percentage points)")
    a2.set_ylim(-0.25, float(hi.max()) + 0.25)
    a2.set_title("paired within city,\nagainst one station", fontsize=10)
    _spines(a1, a2)
    fig.tight_layout(w_pad=2.0)
    return fig, "F7_station_count"


def f7_losses():
    """Section 7.2.1. The most consequential qualification in the thesis, previously a table."""
    style()
    J = json.load(open(MOD / "loss_sensitivity.json", encoding="utf-8"))
    losses = [("rmse", "daily error"), ("mae", "absolute error"), ("tail", "episode days"),
              ("exceedance", "exceedance")]
    steps = [("first two sensors", "first two\nsensors"),
             ("stations three to six", "monitors\nthree to six"),
             ("a background series", "a background\nseries")]
    cols = [C["free"], "#92c5de", C["local"], C["bad"]]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.9),
                                 gridspec_kw=dict(width_ratios=[1.3, 1]))
    w = 0.19
    for i, (lk, lname) in enumerate(losses):
        vals = [J["steps"][f"{sk}|{lk}"] for sk, _ in steps]
        x = np.arange(len(steps)) + (i - 1.5) * w
        med = np.array([v["median"] for v in vals])
        a1.bar(x, med, width=w * 0.92, color=cols[i], alpha=0.85, label=lname)
        a1.errorbar(x, med, yerr=[med - [v["lo"] for v in vals], [v["hi"] for v in vals] - med],
                    fmt="none", ecolor=C["ink"], elinewidth=0.8, capsize=2)
    a1.axhline(0, color=C["muted"], lw=0.8)
    a1.set_xticks(np.arange(len(steps)))
    a1.set_xticklabels([s for _, s in steps], fontsize=9)
    a1.set_ylabel("median reduction in loss (%)")
    a1.legend(frameon=False, fontsize=8.5, loc="upper center", ncol=2)
    a1.set_ylim(a1.get_ylim()[0], a1.get_ylim()[1] + 12)
    a1.set_title(f"three steps, four losses, {J['cities']} cities", fontsize=10)

    inv = J["inversion"]
    y = np.arange(len(losses))[::-1]
    for yi, (lk, lname), col in zip(y, losses, cols):
        v = inv[lk]
        excl = v["lo"] > 0 or v["hi"] < 0
        a2.errorbar([v["median"]], [yi], xerr=[[v["median"] - v["lo"]], [v["hi"] - v["median"]]],
                    fmt="o", color=col, ms=6, ecolor=col, elinewidth=1.6, capsize=3,
                    mfc=col if excl else "white")
    a2.axvline(0, color=C["ink"], lw=0.9)
    a2.set_yticks(y)
    a2.set_yticklabels([f"{n}\n({inv[k]['n']} cities)" for k, n in losses], fontsize=8.5)
    lim = max(abs(inv[k][q]) for k, _ in losses for q in ("lo", "hi")) * 1.08
    a2.set_xlim(-lim, lim)
    a2.set_ylim(-0.8, len(losses) - 0.4)
    a2.set_ylim(-1.5, len(losses) - 0.4)
    a2.text(0.98, 0.08, "favours local\nsensors →", transform=a2.transAxes, ha="right",
            fontsize=8, color=C["muted"])
    a2.text(0.02, 0.08, "← favours the\nbackground", transform=a2.transAxes, ha="left",
            fontsize=8, color=C["muted"])
    a2.set_xlabel("paired advantage, deep-tropical\nband (percentage points)")
    a2.set_title("the ordering changes sign\n(filled: interval excludes zero)", fontsize=10)
    _spines(a1, a2)
    fig.tight_layout(w_pad=2.0)
    return fig, "F7_losses"


def f7_cluster_bootstrap():
    """Section 7.2. Every interval widens under network clustering and no conclusion moves."""
    style()
    d = pd.read_csv(MOD / "cluster_bootstrap.csv")
    d = d[(d.ladder == "ghap") & (d.stratum == "pooled")].set_index("step")
    rows = [("first two sensors", "the first two sensors", "clust.first2"),
            ("sensors three to six", "monitors three to six", "clust.stn3to6"),
            ("a background series", "a background series", "clust.bg")]
    fig, axes = plt.subplots(3, 1, figsize=(7.4, 4.4))
    for ax, (key, lab, tag) in zip(axes, rows):
        r = d.loc[key]
        for q in ("lo", "hi"):
            if abs(r[f"clust_{q}"] - cv(f"{tag}.{q}")) > 0.01 * max(1, abs(cv(f"{tag}.{q}"))):
                raise ValueError(f"{tag}.{q}: file {r[f'clust_{q}']} vs claim {cv(f'{tag}.{q}')}")
        ax.plot([r.city_lo, r.city_hi], [0.32, 0.32], color=C["free"], lw=3.2,
                solid_capstyle="butt", label="resampling cities")
        ax.plot([r.clust_lo, r.clust_hi], [-0.32, -0.32], color=C["local"], lw=3.2,
                solid_capstyle="butt", label="resampling networks, then cities")
        ax.plot([r["median"]] * 2, [-0.6, 0.6], color=C["ink"], lw=1.2)
        span = r.clust_hi - min(0.0, r.clust_lo)
        ax.set_xlim(min(0.0, r.clust_lo) - 0.06 * span, r.clust_hi + 0.30 * span)
        ax.set_ylim(-0.9, 0.9)
        ax.set_yticks([])
        ax.text(r.clust_hi + 0.03 * span, -0.32, f"{r.width_ratio:.2f} times as wide",
                va="center", fontsize=8.5, color=C["local"])
        ax.set_title(f"{lab}, {r.n_cities} cities in {r.n_clusters} networks", fontsize=9.5,
                     loc="left", pad=2)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
    axes[0].legend(frameon=False, fontsize=8.5, loc="upper right", bbox_to_anchor=(1.0, 1.55),
                   ncol=2)
    axes[-1].set_xlabel("median reduction in daily error (%), with 95% interval; "
                        "each row on its own scale")
    fig.tight_layout(h_pad=0.6)
    return fig, "F7_cluster_bootstrap"


def f6_partition():
    """Section 6.6. Three sensitivity axes drawn apart, so they cannot be conflated (F.108)."""
    style()
    P = json.load(open(DEC / "kandy_partition_v2.json", encoding="utf-8"))
    yrs = [r for r in P["per_year"] if r["tier"] == "anchored"]
    sw = pd.read_csv(DEC / "kandy_fmin_sweep.csv").groupby("F_MIN").f.mean()
    if abs(sw.loc[P["summary"]["f_min_parameter"]] - P["summary"]["f_anchored_mean"]) > 5e-4:
        raise ValueError("production sweep does not reproduce the production fraction")
    forms = [("calendar\nday", cv("field.f_form_calendar")),
             ("rolling\n24 h", cv("field.f_form_roll24")),
             ("rolling\n48 h", cv("field.f_form_roll48"))]
    allv = ([r["local_frac"] for r in yrs] + list(sw.values)
            + [cv("field.f_sweep_lo"), cv("field.f_sweep_hi")] + [v for _, v in forms])
    lo, hi = min(allv), max(allv)

    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(9.6, 3.5), sharey=True,
                                     gridspec_kw=dict(width_ratios=[1.1, 1.2, 0.9]))
    for a in (a1, a2, a3):
        a.axhspan(lo, hi, color=C["fill2"], zorder=0)
        a.axhline(cv("partition.f"), color=C["muted"], lw=0.8, ls="--", zorder=1)

    a1.plot([r["year"] for r in yrs], [r["local_frac"] for r in yrs], "o-", color=C["free"],
            ms=5)
    a1.set_xticks([r["year"] for r in yrs])
    a1.tick_params(axis="x", labelsize=8.5)
    a1.set_ylabel("local fraction of the basin mean")
    a1.set_title("(a) anchored years", fontsize=10)
    a1.text(yrs[-1]["year"], hi - 0.003, f"production {cv('partition.f')}\n(dashed)",
            fontsize=8, color=C["muted"], va="top", ha="right")

    a2.plot(sw.index, sw.values, "o-", color=C["free"], ms=5, label="production code path")
    a2.plot([0.0, cv("field.f_sweep_param_hi")], [cv("field.f_sweep_lo"), cv("field.f_sweep_hi")],
            "o", mfc="white", mec=C["local"], ms=6, mew=1.3, label="independent reimplementation")
    a2.axvline(cv("partition.f_min_parameter"), color=C["ink"], lw=0.8, ls=":")
    a2.text(cv("partition.f_min_parameter") + 0.002, lo + 0.003, "value used", fontsize=8)
    a2.set_xlabel(r"$F_{min}$")
    a2.set_title(r"(b) the $F_{min}$ sweep", fontsize=10)
    a2.legend(frameon=False, fontsize=7.5, loc="upper left")

    xs = np.arange(len(forms))
    a3.plot(xs, [v for _, v in forms], "o", mfc="white", mec=C["local"], ms=6, mew=1.3)
    a3.set_xticks(xs)
    a3.set_xticklabels([n for n, _ in forms], fontsize=8.5)
    a3.set_xlim(-0.5, len(forms) - 0.5)
    a3.set_title("(c) constraint window", fontsize=10)
    a3.text(len(forms) - 0.55, lo + 0.003, f"shaded: {lo:.3f} to {hi:.3f}", fontsize=8,
            ha="right", color=C["muted"])
    _spines(a1, a2, a3)
    fig.tight_layout()
    return fig, "F6_partition"


def f8_tournament():
    """Section 8.5. 'Nothing beat one free raster' as an image a reader can check."""
    style()
    T = json.load(open(MOD / "spatial_tournament.json", encoding="utf-8"))
    E = json.load(open(MOD / "embedding_spatial_test.json", encoding="utf-8"))
    lim = T["detection_limit"]
    if abs(lim - cv("phase1.min_detectable")) > 1e-9 or abs(E["detection_limit"] - lim) > 1e-9:
        raise ValueError("detection limit disagrees between the tournament, the embedding "
                         "test and claim phase1.min_detectable")
    F = T["families"]
    nice = {"gp_covariates": "Gaussian process on covariates",
            "lur_stepwise": "stepwise land-use regression", "ridge": "ridge regression",
            "mixed_effects": "mixed model, city intercept", "elasticnet": "elastic net",
            "random_forest": "random forest", "gradient_boost": "gradient boosting"}
    adm = sorted([k for k in nice if k in F], key=lambda k: F[k]["paired"])
    if len(adm) != int(cv("tour.families")):
        raise ValueError("admissible family count disagrees with claim tour.families")
    rows = [(nice[k], F[k]["paired"], F[k]["lo"], F[k]["hi"], C["free"]) for k in adm]
    e1 = E["tests"]["E1"]
    rows.insert(0, ("foundation-model embeddings", e1["median"], e1["lo"], e1["hi"], C["ink"]))

    # Stacked, not side by side (2026-09-19): side by side at the 6 in column the two sets of
    # long family names ran into each other and into the detection-limit label.
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.0, 4.9),
                                 gridspec_kw=dict(height_ratios=[1, 1.15]))
    y = np.arange(len(rows))
    for yi, (lab, m_, l_, h_, col) in zip(y, rows):
        a1.errorbar([m_], [yi], xerr=[[m_ - l_], [h_ - m_]], fmt="o", color=col, ms=5,
                    ecolor=col, elinewidth=1.3, capsize=3)
    a1.set_yticks(y)
    a1.set_yticklabels([r[0] for r in rows], fontsize=8.5)
    a1.axvline(0, color=C["muted"], lw=0.8)
    a1.axvline(lim, color=C["bad"], lw=1.2, ls="--")
    a1.text(lim + 0.006, len(rows) - 1.0, "registered\ndetection\nlimit", color=C["bad"],
            fontsize=8.5, va="center", ha="left")
    a1.set_xlim(min(r[2] for r in rows) - 0.03, lim + 0.11)
    a1.set_xlabel("paired improvement in rank correlation\nover the benchmark raster")
    a1.set_title("admissible families, paired within city", fontsize=10)

    bars = ([("benchmark raster", F["benchmark"]["median_rho"], C["ink"], "")]
            + [(nice[k], F[k]["median_rho"], C["free"], "") for k in adm[::-1]]
            + [(n, F[k]["median_rho"], "white", "////") for k, n in
               (("idw", "inverse distance"), ("gwr_oracle", "geographically weighted"),
                ("kriging", "kriging"))])
    yb = np.arange(len(bars))[::-1].astype(float)
    yb[-3:] -= 0.6
    for yi, (lab, v, col, hatch) in zip(yb, bars):
        a2.barh(yi, v, height=0.7, color=col, edgecolor=C["bad"] if hatch else col,
                hatch=hatch, lw=0.8)
    a2.axvline(F["benchmark"]["median_rho"], color=C["ink"], lw=0.8, ls=":")
    a2.axhline(yb[-3] + 0.8, color=C["muted"], lw=0.6)
    a2.text(0.005, yb[-1] - 0.75, "hatched: oracles, which see the city's own stations\n"
            "and are inadmissible where there are none", fontsize=8.5, color=C["bad"], va="top")
    a2.set_yticks(yb)
    a2.set_yticklabels([b[0] for b in bars], fontsize=8)
    a2.set_ylim(yb[-1] - 2.9, yb[0] + 0.6)
    a2.set_xlabel("median held-out rank correlation")
    a2.set_title("every oracle ranks below the free raster", fontsize=10)
    _spines(a1, a2)
    fig.tight_layout()
    return fig, "F8_tournament"


def f8_contrast_window():
    """Between-cell contrast against the averaging window, with the published range.

    Replaces the image previously printed under this caption, which was a different figure that
    happened to share the file name F9_scales (temporal variation and the ventilation index).

    The observed curves are this project's own measurement (ledger F.76,
    scripts/support_collapse_test.py): across-station p90/p10 in three panel cities with dense,
    same-instrument networks, the same statistic as the model's across-cell p90/p10. An earlier
    version of the prose cited the monthly range to Wickramasinghe 2011, a single-city PAH study
    that contains no such measurement; that citation was wrong and is removed.
    """
    style()
    w = pd.read_csv(DEC / "kandy_contrast_by_window.csv").set_index("window")
    obs = pd.read_csv(MOD / "support_collapse.csv")
    order = ["1h", "24h", "weekly", "monthly", "annual"]
    w = w.loc[order]
    for win, tag in (("1h", "field.contrast_hourly"), ("monthly", "field.contrast_monthly")):
        if abs(round(w.loc[win, "p90_p10"], 2) - cv(tag)) > 0.011:
            raise ValueError(f"{win} contrast disagrees with claim {tag}")
    monthly = obs[obs.window == "monthly"].p90_p10
    if (round(monthly.min(), 2), round(monthly.max(), 2)) != (1.26, 1.51):
        raise ValueError("observed monthly range no longer 1.26 to 1.51; update the prose")

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    xs = np.arange(len(order))
    names = {"medellin": "Medellín", "kathmandu": "Kathmandu", "chiangmai": "Chiang Mai"}
    for (city, g), mk in zip(obs.groupby("city", sort=False), ("s", "^", "D")):
        g = g.set_index("window").reindex(order).p90_p10
        ax.plot(xs, g.values, mk + "--", color=C["muted"], ms=5, lw=1,
                label=f"{names[city]}, across stations")
    ax.plot(xs, w.p90_p10.values, "o-", color=C["free"], ms=7, lw=2,
            label="Kandy model, across cells")
    ax.set_xticks(xs)
    ax.set_xticklabels(["hourly", "daily", "weekly", "monthly", "annual"])
    ax.set_xlabel("averaging window")
    ax.set_ylabel("contrast, 90th / 10th percentile")
    ax.set_xlim(-0.4, len(order) - 0.6)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    _spines(ax)
    fig.tight_layout()
    return fig, "F8_contrast_window"


def f9_paired_trap():
    """Section 8.5 (moved from 9.7 on 2026-09-17; the F9_ name is kept so the built file is
    unchanged). The difference-of-medians trap drawn once, on the siting experiment."""
    style()
    J = json.load(open(MOD / "siting_experiment.json", encoding="utf-8"))
    r = pd.read_csv(MOD / "siting_experiment.csv", dtype={"city": str})
    piv = r.groupby(["city", "method"]).rho.median().unstack()
    for mth in ("clhs", "convenience"):
        if abs(piv[mth].median() - J["median_rho"][mth]) > 1e-3:
            raise ValueError(f"{mth}: recomputed median {piv[mth].median()} vs stored")
    diff = (piv.clhs - piv.convenience).dropna()
    pj = J["paired_vs_convenience"]["clhs"]
    if abs(diff.median() - pj["median"]) > 1e-3:
        raise ValueError("paired median does not reproduce siting_experiment.json")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.0, 3.8),
                                 gridspec_kw=dict(width_ratios=[1, 1.15]))
    for _, row in piv[["convenience", "clhs"]].dropna().iterrows():
        up = row.clhs > row.convenience
        a1.plot([0, 1], [row.convenience, row.clhs], color=C["good"] if up else C["bad"],
                lw=0.6, alpha=0.45)
    for x, mth in ((0, "convenience"), (1, "clhs")):
        a1.plot([x - 0.18, x + 0.18], [piv[mth].median()] * 2, color=C["ink"], lw=2.6)
    a1.text(0.5, 1.07, f"medians {cv('site.rho_convenience')} and {cv('site.rho_deliberate')}",
            ha="center", fontsize=9, fontweight="bold")
    a1.set_ylim(-1.05, 1.15)
    a1.set_xticks([0, 1])
    a1.set_xticklabels(["convenience\nsubset", "deliberately\nspread subset"])
    a1.set_xlim(-0.4, 1.4)
    a1.set_ylabel("held-out rank correlation")
    a1.set_title("read as two medians: a near doubling", fontsize=10)

    bins = np.linspace(diff.min() - 0.02, diff.max() + 0.02, 22)
    a2.hist(diff, bins=bins, color=C["fill2"], edgecolor=C["line"], lw=0.6)
    a2.axvline(0, color=C["ink"], lw=0.9)
    top = a2.get_ylim()[1] * 1.3
    a2.set_ylim(0, top)
    a2.plot([pj["lo"], pj["hi"]], [top * 0.9] * 2, color=C["local"], lw=3,
            solid_capstyle="butt")
    a2.plot([pj["median"]], [top * 0.9], "o", color=C["local"], ms=6)
    a2.text(pj["hi"] + 0.04, top * 0.9,
            f"paired median {cv('site.paired_median')},\n"
            f"better in {cv('site.wins')} of {cv('site.cities')} cities",
            fontsize=8.5, va="center", color=C["local"])
    a2.set_xlabel("within-city difference,\nspread minus convenience")
    a2.set_ylabel("cities")
    a2.set_title("read within city: no advantage", fontsize=10)
    _spines(a1, a2)
    fig.tight_layout(w_pad=2.0)
    return fig, "F9_paired_trap"


BUILDERS = {
    "F6_partition": f6_partition,
    "F7_station_count": f7_station_count,
    "F7_losses": f7_losses,
    "F7_cluster": f7_cluster_bootstrap,
    "F8_tournament": f8_tournament,
    "F9_paired": f9_paired_trap,
    "F8_window": f8_contrast_window,
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
