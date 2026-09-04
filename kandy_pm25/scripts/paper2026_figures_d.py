"""Kandy field figures for the 2026 rewrite. Companion to paper2026_figures{,_b,_c}.py.

These are the figures that show the model's actual output -- the thing the whole apparatus is
built to produce -- rather than a property of it.

  F_field           the shipped field and its decomposition: total, local increment, and the
                    regional/local partition per year.
  F_spatiotemporal  the showcase. Seasonal and diurnal composites of the shipped hourly field
                    on shared scales, so the two axes the model is actually good at are visible
                    side by side.

WHY THIS FILE EXISTS RATHER THAN A REUSE OF THE JULY SUITE
    `src/stage1_satml/decomp/paper_figures.py` renders the same quantities, but two of its
    defaults are now wrong for a paper:
      * it reads `B_background_hourly_{y}.parquet`, which predates the coherence cap of
        2026-08-10, so its partition panel reports the RETIRED ~25 per cent local share
        instead of the post-cap 0.48. Same failure family as gotchas #70 and #80: the
        correction lives in a new file and an old consumer still reads the old one.
      * `paperfig.ADD` resolves to `_additive_v2` while production ships `_additive_v3`.
        Immaterial for an annual mean, material for any single hour.
    Everything here reads the shipped `_additive_v3` fields and the post-cap `_v2` background.

Usage:  .venv/Scripts/python.exe scripts/paper2026_figures_d.py
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
from matplotlib.colors import PowerNorm

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from paper2026_figures import C, v, save, INK, MUTE, OBS, MODEL, GRID  # noqa: E402
from figdata import emit  # noqa: E402

DEC = REPO / "data" / "processed" / "decomp"
PIN = REPO / "data" / "processed" / "pinn_inputs"

YEAR = 2023
YEARS = [2019, 2020, 2021, 2022, 2023]
LT = 5.5                       # Sri Lanka standard time, hours ahead of UTC
PM_CMAP = "YlOrRd"             # sequential, CVD-safe; `turbo` is not used anywhere in this set
INC_CMAP = "YlGnBu"


def _load(year: int) -> pd.DataFrame:
    """Shipped hourly field, with local time attached."""
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}_additive_v3.parquet",
                        columns=["time", "lat", "lon", "pm25_q50"])
    d["lt"] = d["time"] + pd.Timedelta(hours=LT)
    return d


def _grid(d: pd.DataFrame, col: str = "pm25_q50"):
    """Mean over whatever rows are passed, returned as a (lat, lon) array."""
    g = d.groupby(["lat", "lon"])[col].mean().unstack()
    return g.values, g.index.values, g.columns.values


def _terrain():
    """Elevation at its own 100 m resolution with its own extent, for contours. The grid runs
    south-to-north in row 0 (checked, not assumed -- gotcha #56 is about a different loader),
    so `origin="lower"` is correct and no row flip is applied."""
    f = PIN / "kandy_elev_grid_100m.npz"
    if not f.exists():
        return None
    z = np.load(f)
    ext = [float(z["bbox_lon_min"]), float(z["bbox_lon_max"]),
           float(z["bbox_lat_min"]), float(z["bbox_lat_max"])]
    return z["elev"], ext


def _map(ax, Z, lats, lons, *, cmap, norm=None, vmin=None, vmax=None, terrain=None):
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    im = ax.imshow(Z, origin="lower", extent=ext, cmap=cmap, norm=norm, vmin=vmin, vmax=vmax,
                   aspect="equal", interpolation="bilinear")
    if terrain is not None:
        te, text = terrain
        ax.contour(te, extent=text, origin="lower", levels=[600, 800, 1000, 1200],
                   colors="#00000040", linewidths=0.35)
        ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True); s.set_linewidth(0.6); s.set_color(INK)
    return im


# ── F_field ───────────────────────────────────────────────────────────────────────────────
def fig_field():
    """The shipped field, its local increment, and the partition -- the last read from the
    post-cap artefact rather than recomputed from a pre-cap background."""
    d = _load(YEAR)
    B = pd.read_parquet(DEC / f"B_background_hourly_{YEAR}_v2.parquet")
    Bann = float(B["B"].mean())
    tot, lats, lons = _grid(d)
    inc = tot - Bann
    terr = _terrain()

    fig = plt.figure(figsize=(7.2, 2.95), constrained_layout=True)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 1.3])
    axa, axb, axc = (fig.add_subplot(gs[i]) for i in range(3))

    im = _map(axa, tot, lats, lons, cmap=PM_CMAP, norm=PowerNorm(1.3, 10, 40), terrain=terr)
    axa.set_title(f"(a)  annual mean, {YEAR}", fontsize=7.5, loc="left", pad=4)
    cb = fig.colorbar(im, ax=axa, shrink=0.80, pad=0.02)
    cb.set_label("µg m$^{-3}$", fontsize=6.3); cb.ax.tick_params(labelsize=5.8)

    imb = _map(axb, inc, lats, lons, cmap=INC_CMAP, vmin=0, vmax=float(np.percentile(inc, 99)),
               terrain=terr)
    axb.set_title("(b)  local increment", fontsize=7.5, loc="left", pad=4)
    cb = fig.colorbar(imb, ax=axb, shrink=0.80, pad=0.02)
    cb.set_label("µg m$^{-3}$ above $B$", fontsize=6.3); cb.ax.tick_params(labelsize=5.8)

    # (c) the partition, read from the post-cap artefact
    P = json.load(open(DEC / "kandy_partition_v2.json"))
    per = {r["year"]: r for r in P["per_year"]}
    xs = np.arange(len(YEARS))
    Bv = [per[y]["B"] for y in YEARS]
    Iv = [per[y]["I"] for y in YEARS]
    axc.bar(xs, Bv, color="#6BAED6", width=0.66, label="regional background $B$", zorder=2)
    axc.bar(xs, Iv, bottom=Bv, color=OBS, width=0.66, label="local increment", zorder=2)
    for x, y in zip(xs, YEARS):
        tot_y = per[y]["B"] + per[y]["I"]
        axc.text(x, tot_y + 0.5, f"{per[y]['local_frac']*100:.0f}%", ha="center",
                 fontsize=6.8, weight="bold", color=INK)
    axc.set_xticks(xs); axc.set_xticklabels([str(y) for y in YEARS], fontsize=6.8)
    axc.set_ylabel("annual PM$_{2.5}$ (µg m$^{-3}$)", fontsize=7)
    axc.set_ylim(0, max(b + i for b, i in zip(Bv, Iv)) * 1.34)
    axc.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    axc.tick_params(labelsize=6.8)
    axc.legend(fontsize=6.2, loc="upper left", frameon=False, ncol=1,
               handlelength=1.1, borderaxespad=0.15)
    axc.set_title(f"(c)  partition, $f$ = {v('partition.f'):.2f}", fontsize=7.5, loc="left", pad=5)

    save(fig, "F_field")
    print(f"    B {Bann:.2f}  basin {tot.mean():.2f}  contrast {tot.max()/tot.min():.3f}x")
    emit("F_field", background_annual=round(Bann, 2), basin_mean=round(float(tot.mean()), 2),
         annual_contrast_maxmin=round(float(tot.max() / tot.min()), 3), year=YEAR)
    return tot, lats, lons


# ── F_spatiotemporal ──────────────────────────────────────────────────────────────────────
SEASONS = [("DJF", [12, 1, 2]), ("MAM", [3, 4, 5]), ("JJA", [6, 7, 8]), ("SON", [9, 10, 11])]
PHASES = [("night\n00–05 LT", range(0, 6)), ("morning rush\n06–09 LT", range(6, 10)),
          ("midday\n12–15 LT", range(12, 16)), ("evening\n18–21 LT", range(18, 22))]


def fig_spatiotemporal():
    """The showcase: the two axes the model is actually good at, side by side. Seasonal on the
    top row, diurnal on the bottom, each row on one shared scale so panels are comparable
    within a row and the row means are legible against each other."""
    d = _load(YEAR)
    d["mon"] = d["lt"].dt.month
    d["hr"] = d["lt"].dt.hour
    _, lats, lons = _grid(d)
    terr = _terrain()

    srows = [_grid(d[d.mon.isin(m)])[0] for _, m in SEASONS]
    prows = [_grid(d[d.hr.isin(list(h))])[0] for _, h in PHASES]

    fig = plt.figure(figsize=(7.2, 4.35))
    gs = fig.add_gridspec(2, 5, width_ratios=[1, 1, 1, 1, 0.062], hspace=0.10, wspace=0.06)

    for row, (arrs, labs) in enumerate([(srows, [s for s, _ in SEASONS]),
                                        (prows, [p for p, _ in PHASES])]):
        lo = min(float(np.nanmin(a)) for a in arrs)
        hi = max(float(np.nanmax(a)) for a in arrs)
        for j, (A, lab) in enumerate(zip(arrs, labs)):
            ax = fig.add_subplot(gs[row, j])
            im = _map(ax, A, lats, lons, cmap=PM_CMAP, vmin=lo, vmax=hi, terrain=terr)
            ax.set_title(lab, fontsize=6.8, pad=3, color=INK)
            ax.text(0.035, 0.045, f"{A.mean():.1f}", transform=ax.transAxes, fontsize=6.2,
                    color=INK, weight="bold",
                    bbox=dict(fc="white", ec="none", alpha=.72, pad=1.2))
        cax = fig.add_subplot(gs[row, 4])
        cb = fig.colorbar(im, cax=cax)
        cb.set_label("PM$_{2.5}$ (µg m$^{-3}$)", fontsize=6.2)
        cb.ax.tick_params(labelsize=5.8)

    fig.text(0.008, 0.735, "seasonal", rotation=90, va="center", fontsize=8, weight="bold",
             color=INK)
    fig.text(0.008, 0.285, "diurnal", rotation=90, va="center", fontsize=8, weight="bold",
             color=INK)
    save(fig, "F_spatiotemporal")

    out = {}
    for lab, arrs, names in (("season", srows, [s for s, _ in SEASONS]),
                             ("phase", prows, ["night", "morning", "midday", "evening"])):
        means = [float(a.mean()) for a in arrs]
        print(f"    {lab:7s} means {['%.1f' % m for m in means]}  "
              f"swing {max(means)/min(means):.2f}x")
        out[f"{lab}_swing"] = round(max(means) / min(means), 2)
        for nm, m in zip(names, means):
            out[f"{lab}_{nm.lower()}"] = round(m, 1)
    # the recorded diurnal structure: deep night sits ABOVE the midday trough (gotcha #54)
    out["night_over_midday"] = round(out["phase_night"] / out["phase_midday"], 3)
    emit("F_spatiotemporal", **out)


if __name__ == "__main__":
    print("Kandy field figures, from the shipped _additive_v3 field and the post-cap background")
    fig_field()
    fig_spatiotemporal()
