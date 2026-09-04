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
    ax.text(1.35, B + inc / 2, "the part a local\nintervention can change",
            fontsize=9, color=C["muted"], va="center")

    ax.set_xlabel("distance across the basin (km)")
    ax.set_ylabel(r"PM$_{2.5}$  ($\mu$g m$^{-3}$)")
    ax.set_xlim(0, 15); ax.set_ylim(0, 26)
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
    ax.text(6.4, 1.0, "real sub-grid structure", fontsize=9.5, color=C["muted"])

    ax.plot(7.4, 3.4, marker="v", ms=12, color=C["ink"], zorder=5)
    ax.text(7.9, 3.4, "the monitor\nsits here", fontsize=9.5, va="center", color=C["ink"])
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

    ax.set_xlim(-0.4, 23); ax.set_ylim(-0.4, 10.4)
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
    for label, x, y in items:
        strong = x > 0.5
        ax.scatter(x, y, s=190, color=C["good"] if strong else C["bad"],
                   alpha=0.85, zorder=3, edgecolor="white", lw=1.2)
        ax.annotate(label, (x, y), xytext=(0, 13), textcoords="offset points",
                    ha="center", fontsize=9.5,
                    color=C["ink"] if strong else C["muted"])

    ax.plot([0.02, 0.98], [0.02, 0.98], ls="--", lw=1.0, color=C["muted"], alpha=0.6, zorder=1)
    ax.text(0.60, 0.50, "an attempt yields as much\nas it declared in advance",
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
    z = np.load(DEM)
    elev = z["elev"].astype(float)
    lat = z["lat_grid"][:, 0].astype(float)
    lon = z["lon_grid"][0, :].astype(float)
    if lat[0] > lat[-1]:
        lat, elev = lat[::-1], elev[::-1, :]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.9),
                                 gridspec_kw=dict(width_ratios=[1.05, 1]))

    # Hillshade under a translucent elevation ramp. `terrain` puts blue at its low end, which
    # makes a valley floor read as water; `gist_earth` does not.
    gy, gx = np.gradient(elev, 100.0)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = np.radians(315.0), np.radians(45.0)
    shade = (np.sin(alt) * np.cos(slope)
             + np.cos(alt) * np.sin(slope) * np.cos(az - aspect))
    ext = [lon.min(), lon.max(), lat.min(), lat.max()]
    a1.imshow(shade, cmap="gray", extent=ext, origin="lower")
    im = a1.imshow(elev, cmap="gist_earth", extent=ext, origin="lower", alpha=0.62)

    # NORTH-SOUTH through the city, not west-east. The domain's high ground is the Hantana
    # range on the southern edge, and a west-east cut at the city latitude misses it entirely:
    # it reports 267 m of relief where the domain has 846, which would have put a figure in
    # the thesis contradicting a gated claim.
    cut_lon = 80.6337
    a1.axvline(cut_lon, color=C["local"], lw=1.5, ls="--")
    a1.text(cut_lon + 0.003, lat.max() - 0.004, "cross section", color=C["local"], fontsize=9,
            rotation=90, va="top")
    a1.plot(cut_lon, 7.2906, marker="o", ms=6, color=C["ink"])
    a1.text(cut_lon + 0.005, 7.2906, "city centre", fontsize=9, color=C["ink"], va="center")
    a1.set_xlabel("longitude (E)"); a1.set_ylabel("latitude (N)")
    fig.colorbar(im, ax=a1, shrink=0.82, label="elevation (m)")

    j = int(np.abs(lon - cut_lon).argmin())
    prof = elev[:, j]
    km = (lat - lat.min()) * 111.0
    a2.fill_between(km, prof.min() - 40, prof, color=C["fill"], lw=0)
    a2.plot(km, prof, color=C["ink"], lw=1.4)
    floor = float(prof.min())
    a2.axhline(floor, color=C["muted"], ls=":", lw=1.0)
    a2.text(km.max(), floor + 14, f"valley floor, {floor:.0f} m", ha="right", fontsize=9,
            color=C["muted"])
    # The profile runs SOUTH to NORTH: x = 0 is the southern edge, which is the high ground.
    # Labelling x = 0 as the Mahaweli corridor put the ridge and the vent the wrong way round.
    xa = km[int(len(km) * 0.42)]
    a2.annotate("", xy=(xa, floor), xytext=(xa, float(prof.max())),
                arrowprops=dict(arrowstyle="<->", color=C["local"], lw=1.2))
    a2.text(xa + 0.35, (floor + prof.max()) / 2,
            f"{prof.max() - floor:.0f} m along this line\n"
            f"{elev.max() - elev.min():.0f} m across the domain",
            fontsize=9.5, color=C["local"], va="center", ha="left")
    a2.text(km[int(len(km) * 0.03)], prof.max() * 0.99, "Hantana range\n(closes the basin)",
            fontsize=9, color=C["muted"], va="top")
    a2.text(km.max() * 0.99, floor + 120, "Mahaweli corridor\n(ventilation)", fontsize=9,
            color=C["muted"], va="bottom", ha="right")
    a2.set_xlabel("distance south to north (km)")
    a2.set_ylabel("elevation (m)")
    a2.set_xlim(0, km.max())

    fig.suptitle("Kandy: the geometry the confinement term acts on", fontsize=11, y=1.00)
    fig.tight_layout()
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
