"""The matplotlib diagrams: D2, D4, D8, D11, D12.

These are not flowcharts. Each one is a picture of a quantity, a geometry or a classification,
so an automatic graph layout has nothing to offer and the drawing is done directly. They share
the house style with the graphviz diagrams through thesisviz.style().

D11 and D12 use real data: the Kandy digital elevation model and the project's own record of
when each attempt was made. Neither is illustrative.

Usage: python d_schematics.py [--only D8]
Out:   thesis/diagrams/D*.png and .pdf
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

from thesisviz import C, DIAGRAMS, save_fig, style

REPO = Path(r"D:\ProjectCD\kandy_pm25")
DEM = REPO / "data" / "processed" / "pinn_inputs" / "kandy_elev_grid_100m.npz"
DEM_UTM = REPO / "data" / "processed" / "pinn_inputs" / "kandy_dem_utm44n_90m_wide.tif"
OSM = REPO / "data" / "processed" / "decomp" / "osm_kandy"


# ── D2: the decomposition ─────────────────────────────────────────────────────────────────

def d2_decomposition():
    """Chapter 6. The decomposition as a cross section, which is clearer than three maps.

    A map of each component looks like three maps. A cross section shows the one thing that
    matters: the background is flat, the increment carries all of the structure, and the total
    is their sum. The gauge is then visible rather than asserted, because the shaded area under
    the increment is the same whatever shape it takes.
    """
    style()
    x = np.linspace(0, 15, 400)
    core = np.exp(-((x - 6.2) ** 2) / 5.0) + 0.55 * np.exp(-((x - 10.5) ** 2) / 2.2)
    P = 1.0 + 1.5 * (core - core.mean()) / core.std() * 0.35
    B, inc = 11.0, 9.5
    total = B + inc * P

    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    ax.fill_between(x, 0, B, color=C["free"], alpha=0.30, lw=0,
                    label="B(t)  regional background, spatially uniform")
    ax.fill_between(x, B, total, color=C["local"], alpha=0.32, lw=0,
                    label="[T(t) - B(t)] P(x)  local increment, all the structure")
    ax.plot(x, total, color=C["ink"], lw=1.6, label="PM(x, t)  the delivered field")
    ax.axhline(B + inc, color=C["muted"], ls="--", lw=1.0)
    ax.text(14.8, B + inc + 0.35, "T(t), the basin mean", ha="right", va="bottom",
            fontsize=9.5, color=C["muted"])

    ax.annotate("", xy=(1.1, B), xytext=(1.1, B + inc),
                arrowprops=dict(arrowstyle="<->", color=C["muted"], lw=1.0))
    # Above the arrow, clear of the curve: beside it, the text ran into the rising flank.
    ax.text(0.3, B + inc + 1.0, "the part a local\nintervention can change",
            fontsize=9, color=C["muted"], va="bottom")

    ax.set_xlabel("distance across the basin (km)")
    ax.set_ylabel(r"PM$_{2.5}$  ($\mu$g m$^{-3}$)")
    ax.set_xlim(0, 15); ax.set_ylim(0, 37)
    ax.legend(loc="upper right", frameon=True, framealpha=0.94, fontsize=9)
    ax.set_title("The spatial mean of P is one, so the area under the red band is fixed",
                 fontsize=10, color=C["muted"], pad=8)
    return fig, "D2_decomposition"


# ── D4: the observation operator ──────────────────────────────────────────────────────────

def d4_observation_operator():
    """Chapter 6. Why comparing an areal model to a point sensor needs two extra terms.

    This is the single most common way a model of this kind is scored wrongly, and it is hard
    to convey in words because the error is geometric.
    """
    style()
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    rng = np.random.default_rng(3)

    ax.add_patch(Rectangle((0, 0), 10, 10, facecolor=C["fill2"], edgecolor=C["line"], lw=1.4))
    ax.text(0.35, 9.3, "one model cell, 1 km", fontsize=10, color=C["ink"])

    # sub-grid structure the cell cannot resolve
    xs, ys = rng.uniform(0.6, 9.4, 220), rng.uniform(0.6, 9.4, 220)
    w = np.exp(-((xs - 7.2) ** 2 + (ys - 3.0) ** 2) / 6.0)
    ax.scatter(xs, ys, s=90 * w + 4, c=C["local"], alpha=0.30, lw=0)
    ax.text(5.0, -0.5, "real sub-grid structure", fontsize=9.5, color=C["muted"], ha="center",
            va="top")

    ax.plot(7.4, 3.4, marker="v", ms=12, color=C["ink"], zorder=5)
    import matplotlib.patheffects as pe
    ax.text(7.9, 3.4, "the monitor\nsits here", fontsize=9.5, va="center", color=C["ink"],
            path_effects=[pe.withStroke(linewidth=2.5, foreground=C["fill2"])], zorder=6)
    ax.axhline(0, color="none")

    ax.annotate("", xy=(11.6, 5.0), xytext=(10.3, 5.0),
                arrowprops=dict(arrowstyle="->", color=C["line"], lw=1.4))
    ax.text(12.0, 8.4, "the model reports", fontsize=10, color=C["ink"])
    ax.text(12.0, 7.4, r"$H_k[C]$   the cell MEAN", fontsize=10, color=C["free"])
    ax.text(12.0, 5.9, "the monitor reports", fontsize=10, color=C["ink"])
    ax.text(12.0, 4.9, "a POINT inside it", fontsize=10, color=C["local"])
    ax.text(12.0, 3.2, r"$y_k = H_k[C] + b_k + e_k$", fontsize=11, color=C["ink"])
    ax.text(12.0, 2.1, r"$b_k$  systematic: siting and calibration", fontsize=9,
            color=C["muted"])
    ax.text(12.0, 1.2, r"$\sigma_{rep}$  random: unresolved structure", fontsize=9,
            color=C["muted"])

    ax.set_xlim(-0.4, 23); ax.set_ylim(-1.6, 10.4)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Without these two terms a centring error is read as a failure of interval "
                 "width", fontsize=10, color=C["muted"], pad=6)
    return fig, "D4_observation_operator"


# ── D8: the failure taxonomy ──────────────────────────────────────────────────────────────

def d8_failure_taxonomy():
    """Chapter 5, and it is that chapter's argument in one picture.

    Eight attempts, placed by whether an expectation was stated before the run and whether the
    outcome was a bounded claim. The diagonal is the whole point: the attempts that stated what
    they expected are the ones that produced something usable when they failed.
    """
    style()
    fig, ax = plt.subplots(figsize=(7.6, 5.6))

    # x: was an expectation stated in advance?   y: did it yield a bounded claim?
    items = [
        ("Cross-continental PINN", 0.18, 0.30),
        ("Rigid terrain ansatz", 0.30, 0.62),
        ("Cross-city ConvCNP", 0.22, 0.20),
        ("Sim2Real fine-tuning", 0.12, 0.55),
        ("Five spatial nulls", 0.20, 0.10),
        ("Five background rebuilds", 0.55, 0.58),
        ("Audit defects", 0.72, 0.70),
        ("Learned pattern, registered", 0.92, 0.90),
    ]
    # Label offsets chosen so no label crosses a marker, another label or the diagonal note.
    off = {"Cross-city ConvCNP": (12, 0, "left", "center"),
           "Five spatial nulls": (12, 0, "left", "center"),
           "Five background rebuilds": (-6, -12, "right", "top")}
    for label, x, y in items:
        strong = x > 0.5
        ax.scatter(x, y, s=190, color=C["good"] if strong else C["bad"],
                   alpha=0.85, zorder=3, edgecolor="white", lw=1.2)
        dx, dy, ha, va = off.get(label, (0, 13, "center", "baseline"))
        ax.annotate(label, (x, y), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va=va, fontsize=9.5,
                    color=C["ink"] if strong else C["muted"])

    ax.plot([0.02, 0.98], [0.02, 0.98], ls="--", lw=1.0, color=C["muted"], alpha=0.6, zorder=1)
    ax.text(0.80, 0.63, "an attempt yields as much\nas it declared in advance",
            fontsize=9.5, color=C["muted"], rotation=38, ha="center", va="center", alpha=0.9)

    ax.set_xlabel("was an expectation stated BEFORE the run?", labelpad=8)
    ax.set_ylabel("did failing produce a bounded claim?", labelpad=8)
    ax.set_xlim(0, 1.05); ax.set_ylim(0, 1.05)
    ax.set_xticks([0.05, 0.95]); ax.set_xticklabels(["no", "yes"])
    ax.set_yticks([0.05, 0.95]); ax.set_yticklabels(["no", "yes"])
    ax.set_title("Eight attempts that did not work, and what each one still established",
                 fontsize=10.5, pad=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return fig, "D8_failure_taxonomy"


# ── D11: the valley ───────────────────────────────────────────────────────────────────────

def d11_valley():
    """Chapter 2. The setting, from the digital elevation model rather than from a photograph.

    A licensed satellite image would show the same valley less informatively. The cross section
    is what the confinement term of Chapter 6 actually acts on.
    """
    style()
    if not DEM.exists():
        print("  D11 skipped: DEM not found")
        return None, None
    import geopandas as gpd
    import importlib.util
    import json
    import rasterio
    from matplotlib.ticker import FuncFormatter
    from matplotlib_scalebar.scalebar import ScaleBar
    from pyproj import Transformer
    from thesisviz import natural_earth

    spec = importlib.util.spec_from_file_location("kcfg", REPO / "config.py")
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)
    BB = cfg.KANDY_PINN_BBOX
    claims = json.load(open(REPO / "data" / "processed" / "modular" / "claims.json",
                            encoding="utf-8"))["claims"]

    # The PROFILE and the relief figures come from the 100 m grid, because that is the source of
    # the gated claim kandy.relief_m; a different DEM would put a second relief in the thesis.
    z = np.load(DEM)
    elev = z["elev"].astype(float)
    lat = z["lat_grid"][:, 0].astype(float)
    lon = z["lon_grid"][0, :].astype(float)
    if lat[0] > lat[-1]:
        lat, elev = lat[::-1], elev[::-1, :]

    # The MAP is drawn in UTM 44N so that distance on the page is true and a scale bar means
    # something. The wide raster is cropped to the modelled domain plus a margin, so the domain
    # boundary is visible as a boundary rather than coinciding with the frame.
    to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
    cx = [BB["lon_min"], BB["lon_max"], BB["lon_max"], BB["lon_min"], BB["lon_min"]]
    cy = [BB["lat_min"], BB["lat_min"], BB["lat_max"], BB["lat_max"], BB["lat_min"]]
    bx, by = to_utm.transform(cx, cy)
    pad = 3000.0
    x0, x1, y0, y1 = min(bx) - pad, max(bx) + pad, min(by) - pad, max(by) + pad
    with rasterio.open(DEM_UTM) as r:
        if r.crs.to_epsg() != 32644:
            raise ValueError(f"{DEM_UTM.name} is {r.crs}, expected UTM 44N")
        T = r.transform
        c0, r0 = ~T * (x0, y1)
        c1, r1 = ~T * (x1, y0)
        c0, r0 = max(int(np.floor(c0)), 0), max(int(np.floor(r0)), 0)
        c1, r1 = min(int(np.ceil(c1)), r.width), min(int(np.ceil(r1)), r.height)
        zu = r.read(1)[r0:r1, c0:c1].astype(float)
        if r.nodata is not None:
            zu[zu == r.nodata] = np.nan
    left, top = T.c + c0 * T.a, T.f + r0 * T.e
    right, bottom = left + zu.shape[1] * T.a, top + zu.shape[0] * T.e
    ext = [left, right, bottom, top]

    fig = plt.figure(figsize=(9.8, 4.7))
    a1 = fig.add_axes([0.05, 0.11, 0.47, 0.80])
    a2 = fig.add_axes([0.71, 0.17, 0.28, 0.66])

    # Hillshade under a translucent elevation ramp. `terrain` puts blue at its low end, which
    # makes a valley floor read as water; `gist_earth` does not. Row 0 is north here, so the
    # northward gradient is the negative of the row gradient.
    dzdx = np.gradient(zu, axis=1) / abs(T.a)
    dzdy = -np.gradient(zu, axis=0) / abs(T.e)
    slope = np.arctan(np.hypot(dzdx, dzdy))
    aspect = np.arctan2(-dzdx, dzdy)
    az, alt = np.radians(315.0), np.radians(45.0)
    shade = (np.sin(alt) * np.cos(slope)
             + np.cos(alt) * np.sin(slope) * np.cos(az - aspect))
    a1.imshow(shade, cmap="gray", extent=ext, origin="upper")
    im = a1.imshow(zu, cmap="gist_earth", extent=ext, origin="upper", alpha=0.62)
    xc = left + (np.arange(zu.shape[1]) + 0.5) * T.a
    yc = top + (np.arange(zu.shape[0]) + 0.5) * T.e
    lv = np.arange(np.floor(np.nanmin(zu) / 100) * 100, np.nanmax(zu) + 100, 100)
    a1.contour(xc, yc, zu, levels=lv, colors=C["line"], linewidths=0.3, alpha=0.5)
    major = a1.contour(xc, yc, zu, levels=[v for v in lv if v % 500 == 0], colors=C["ink"],
                       linewidths=0.6, alpha=0.7)
    a1.clabel(major, fmt="%d m", fontsize=6.5, inline=True)

    a1.plot(bx, by, color=C["ink"], lw=1.1)
    import matplotlib.patheffects as pe
    a1.text(bx[3] + 250, by[3] - 250, "modelled domain", fontsize=8, va="top",
            path_effects=[pe.withStroke(linewidth=2.2, foreground="white", alpha=0.85)])

    riv = gpd.read_file(OSM / "rivers.geojson")
    riv = riv[riv.name == "Mahaweli Ganga"].to_crs(32644)
    if riv.empty:
        raise ValueError("Mahaweli Ganga not found in the cached OSM rivers layer")
    riv.plot(ax=a1, color=C["free"], lw=1.4, zorder=3)

    # NORTH-SOUTH through the city, not west-east. The domain's high ground is the Hantana
    # range on the southern edge, and a west-east cut at the city latitude misses it entirely:
    # it reports 267 m of relief where the domain has 846, which would have put a figure in
    # the thesis contradicting a gated claim.
    cut_lon = 80.6337
    sx, sy = to_utm.transform([cut_lon, cut_lon], [BB["lat_min"], BB["lat_max"]])
    a1.plot(sx, sy, color=C["local"], lw=1.4, ls="--", zorder=4)

    import matplotlib.patheffects as pe
    halo = [pe.withStroke(linewidth=2.2, foreground="white", alpha=0.85)]

    def lab(lo_, la_, text, **kw):
        ux, uy = to_utm.transform(lo_, la_)
        a1.text(ux, uy, text, zorder=6, path_effects=halo, **kw)
        return ux, uy

    ux, uy = to_utm.transform(80.6350, 7.2931)
    a1.plot(ux, uy, "o", ms=5, color=C["ink"], zorder=6)
    lab(80.6400, 7.2931, "Kandy", fontsize=9, fontweight="bold", va="center")
    lab(80.6300, 7.3221, "Katugastota", fontsize=7.5, color=C["ink"], va="center")
    lab(80.5870, 7.2600, "Peradeniya", fontsize=7.5, color=C["ink"], ha="right", va="center")
    lab(80.6120, 7.2450, "Hantana range", fontsize=8.5, style="italic", ha="center")
    lab(80.6930, 7.2560, "Mahaweli Ganga", fontsize=8, style="italic", color=C["free"],
        ha="center", va="top")
    for name, la_, lo_ in (("Hantana sensor", 7.265, 80.625), ("Akurana sensor", 7.366, 80.618)):
        ux, uy = to_utm.transform(lo_, la_)
        a1.plot(ux, uy, "^", ms=6.5, color=C["local"], mec="white", mew=0.7, zorder=7)
        # To the right of the marker: on the left, "Hantana sensor" ran into "Peradeniya".
        a1.text(ux + 300, uy, name, fontsize=7.5, color=C["local"], ha="left", va="center",
                zorder=7, path_effects=halo, fontweight="bold")

    a1.set_xlim(x0, x1); a1.set_ylim(y0, y1)
    a1.set_aspect("equal")
    km = FuncFormatter(lambda v, _: f"{v / 1000:.0f}")
    a1.xaxis.set_major_formatter(km); a1.yaxis.set_major_formatter(km)
    a1.tick_params(labelsize=8)
    a1.set_xlabel("easting (km, UTM zone 44N)"); a1.set_ylabel("northing (km)")
    a1.add_artist(ScaleBar(1.0, units="m", location="lower right", length_fraction=0.22,
                           box_alpha=0.85, font_properties={"size": 8}))
    a1.annotate("", xy=(0.06, 0.17), xytext=(0.06, 0.06), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color=C["ink"], lw=1.3))
    a1.text(0.06, 0.185, "N", transform=a1.transAxes, ha="center", va="bottom", fontsize=10,
            fontweight="bold", path_effects=halo)
    fig.colorbar(im, ax=a1, shrink=0.8, pad=0.02, label="elevation (m)")

    # Locator: where in Sri Lanka this is, from the cached Natural Earth countries only.
    ins = a1.inset_axes([0.80, 0.64, 0.2, 0.36])
    world = gpd.read_file(natural_earth("10m", "cultural", "admin_0_countries"))
    world[world.ADMIN == "Sri Lanka"].plot(ax=ins, color=C["fill2"], edgecolor=C["line"], lw=0.5)
    ins.plot(80.635, 7.293, "*", ms=8, color=C["local"])
    ins.set_xlim(79.4, 82.1); ins.set_ylim(5.8, 10.0)
    ins.set_xticks([]); ins.set_yticks([])
    ins.set_facecolor("white")
    for s in ins.spines.values():
        s.set_visible(True); s.set_color(C["line"]); s.set_linewidth(0.5)

    j = int(np.abs(lon - cut_lon).argmin())
    prof = elev[:, j]
    km = (lat - lat.min()) * 111.0
    a2.fill_between(km, prof.min() - 40, prof, color=C["fill"], lw=0)
    a2.plot(km, prof, color=C["ink"], lw=1.4)
    floor = float(prof.min())
    a2.axhline(floor, color=C["muted"], ls=":", lw=1.0)
    a2.text(km.max(), floor - 14, f"valley floor, {floor:.0f} m", ha="right", va="top",
            fontsize=9, color=C["muted"])
    # The profile runs SOUTH to NORTH: x = 0 is the southern edge, which is the high ground.
    # Labelling x = 0 as the Mahaweli corridor put the ridge and the vent the wrong way round.
    xa = km[int(len(km) * 0.42)]
    a2.annotate("", xy=(xa, floor), xytext=(xa, float(prof.max())),
                arrowprops=dict(arrowstyle="<->", color=C["local"], lw=1.2))
    a2.text(xa + 0.35, (floor + prof.max()) / 2,
            f"{prof.max() - floor:.0f} m along this line\n"
            f"{claims['kandy.relief_m']['value']:.0f} m across the domain",
            fontsize=9.5, color=C["local"], va="center", ha="left")
    a2.text(km[int(len(km) * 0.12)], prof.max() * 0.99, "Hantana\nrange",
            fontsize=9, color=C["muted"], va="top")
    a2.text(km.max() * 0.99, floor + 190, "Mahaweli\ncorridor", fontsize=9,
            color=C["muted"], va="bottom", ha="right")
    a2.set_xlabel("distance south to north (km)")
    a2.set_ylabel("elevation (m)")
    a2.set_xlim(0, km.max())

    fig.suptitle("Kandy: the geometry the confinement term acts on", fontsize=11, y=0.99)
    return fig, "D11_valley"


# ── D12: the timeline ─────────────────────────────────────────────────────────────────────

def d12_timeline():
    """Chapter 5 opener. What was attempted, when, and how it ended.

    Dates are from the project's own dated record, not reconstructed.
    """
    style()
    rows = [
        ("2026-03", "Daily boosted-tree anchor", "kept as a 22-year chronology", "part"),
        ("2026-03", "Cross-continental PINN", "methodology study, not a feeder", "fail"),
        ("2026-05", "Hourly residual anchor v3", "kept, it is the production anchor", "keep"),
        ("2026-05", "Cross-city ConvCNP", "fields defensible, spatially smoothed out", "fail"),
        ("2026-05", "Sim2Real fine-tuning", "memorised the sensors, grid mean 22 to 37", "fail"),
        ("2026-06", "Additive decomposition", "kept, it is the production model", "keep"),
        ("2026-06", "Dynamic transport learning", "null, monitors are floor-sited", "fail"),
        ("2026-07", "Five background rebuilds", "all rejected, over-determined", "fail"),
        ("2026-08", "Coherence cap on B", "kept, the partition moved to 0.48", "keep"),
        ("2026-08", "Budget ladder re-validation", "kept, the defect was ours", "keep"),
        ("2026-09", "Learned spatial pattern", "refuted against a registered bar", "fail"),
    ]
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    colmap = {"keep": C["good"], "fail": C["bad"], "part": C["muted"]}
    for i, (date, what, outcome, kind) in enumerate(rows):
        y = len(rows) - i
        ax.plot([0, 1], [y, y], color=C["fill"], lw=8, solid_capstyle="butt", zorder=1)
        ax.scatter(0, y, s=90, color=colmap[kind], zorder=3, edgecolor="white", lw=1.2)
        ax.text(-0.035, y, date, ha="right", va="center", fontsize=9.5, color=C["muted"])
        ax.text(0.03, y + 0.20, what, ha="left", va="center", fontsize=10.5, color=C["ink"])
        ax.text(0.03, y - 0.24, outcome, ha="left", va="center", fontsize=9.5,
                color=C["muted"])

    ax.set_xlim(-0.22, 1.02); ax.set_ylim(0.3, len(rows) + 0.9)
    ax.axis("off")
    ax.scatter([], [], s=90, color=C["good"], label="kept in the production model")
    ax.scatter([], [], s=90, color=C["bad"], label="did not work")
    ax.scatter([], [], s=90, color=C["muted"], label="retained for a narrower purpose")
    ax.legend(loc="lower right", frameon=False, fontsize=9.5, ncol=1)
    ax.set_title("What was attempted, and how each attempt ended", fontsize=11, pad=12)
    return fig, "D12_timeline"


BUILDERS = {
    "D2": d2_decomposition, "D4": d4_observation_operator, "D8": d8_failure_taxonomy,
    "D11": d11_valley, "D12": d12_timeline,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    todo = [a.only] if a.only else list(BUILDERS)

    from PIL import Image
    for key in todo:
        fig, name = BUILDERS[key]()
        if fig is None:
            continue
        p = save_fig(fig, name, DIAGRAMS)
        w, h = Image.open(p).size
        flag = "" if 0.8 <= w / h <= 2.6 else "   <-- check aspect"
        print(f"  {key:<4} {name:<28} {w}x{h}  aspect {w/h:.2f}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
