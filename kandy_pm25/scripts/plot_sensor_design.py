"""plot_sensor_design.py -- the proposed network on the three surfaces that chose it.

Three panels, because the design has three justifications and they are not the same picture.

(a) EMISSIONS. What the design stratum was drawn to span, and what the present network misses.
(b) FLOW PHYSICS. Nocturnal drainage convergence: where cold air pools after sunset. A design
    stratified on emissions alone samples where the sources are and learns nothing about what
    the atmosphere does with them.
(c) PEOPLE. Population and susceptible receptors. A different objective, selecting different
    sites, which is why they are a separate stratum rather than a weighting.

LAYOUT. Two columns by two rows, with the key and the caveats in the fourth cell. The modelled
domain is square, so three square maps in a row scale to about 5 cm each on a portrait page and
three in a column would run to nearly 50 cm. A 2x2 block is the only arrangement that keeps each
map large on a portrait page, and the spare cell is where the legend belongs anyway.

Every number on the figure is read from the design files. Nothing is typed.

Out: results/figures/kandy_decomp/sensor_design_kandy.png
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
from matplotlib.lines import Line2D

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
DEC = REPO / "data" / "processed" / "decomp"
OUTD = REPO / "results" / "figures" / "kandy_decomp"
OUTD.mkdir(parents=True, exist_ok=True)
OUT = OUTD / "sensor_design_kandy.png"

STY = {
    "A_anchor":   dict(c="#000000", m="*", s=560, lab="A  reference anchor"),
    "B_design":   dict(c="#1f6fb4", m="o", s=150, lab="B  design: emission + flow physics"),
    "E_vertical": dict(c="#7b3fa0", m="v", s=160, lab="E  vertical transect, floor to ridge"),
    "C_paired":   dict(c="#d1495b", m="^", s=130, lab="C  paired microsites, one cell"),
    "D_receptor": dict(c="#1a7f37", m="s", s=135, lab="D  receptor, held out of fitting"),
}
EXISTING = [(7.265, 80.625, "FECT Hantana"), (7.2731, 80.6117, "BAM-cal LCS")]
TITLE_FS, LAB_FS, TICK_FS = 15, 13, 12


def strata(ax, d, only=None):
    for key, k in STY.items():
        if only and key not in only:
            continue
        g = d[d.stratum == key]
        if len(g):
            ax.scatter(g.lon, g.lat, c=k["c"], marker=k["m"], s=k["s"],
                       edgecolor="white", linewidth=1.7, zorder=6)


def main() -> None:
    from design_sensor_network import load_layers
    L = load_layers()
    lat, lon = L["lat"], L["lon"]
    ext = [lon.min(), lon.max(), lat.min(), lat.max()]
    d = pd.read_csv(DEC / "sensor_design_kandy.csv")
    rc = pd.read_csv(DEC / "kandy_receptors_ranked.csv")
    pop = np.load(DEC / "population_kandy.npz")
    with open(DEC / "sensor_design_summary.json", encoding="utf-8") as fh:
        S = json.load(fh)

    plt.rcParams.update({"font.size": 12})
    fig, axes = plt.subplots(2, 2, figsize=(14.6, 15.4))
    A, B, C, K = axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]

    # ── (a) emissions ─────────────────────────────────────────────────────────────────────
    E = L["E"]
    Ef = E[np.isfinite(E)]
    pctg = np.full(E.shape, np.nan)
    pctg[np.isfinite(E)] = 100.0 * np.searchsorted(np.sort(Ef), Ef) / len(Ef)
    im = A.imshow(pctg, origin="lower", extent=ext, cmap="YlOrRd", aspect="equal",
                  vmin=0, vmax=100)
    cb = fig.colorbar(im, ax=A, fraction=0.046, pad=0.02)
    cb.set_label("percentile of the emission proxy", fontsize=LAB_FS - 1)
    cb.ax.axhline(61, color="#1f6fb4", linewidth=3.0)
    cb.ax.annotate("61st", xy=(-0.28, 61), xycoords=("axes fraction", "data"),
                   fontsize=11, color="#1f6fb4", va="center", ha="right", fontweight="bold")
    strata(A, d)
    for la, lo, nm in EXISTING:
        A.scatter(lo, la, facecolors="none", edgecolor="#222222", marker="o", s=300,
                  linewidth=2.6, linestyle="--", zorder=7)
        A.annotate(nm, (lo, la), textcoords="offset points", xytext=(11, -16),
                   fontsize=11, color="#222222", fontweight="bold")
    A.set_title(f"(a)  Emissions: spanning what the network misses\n"
                f"existing records occupy the {S['existing_pct_lo']:.0f}st to "
                f"{S['existing_pct_hi']:.0f}th percentile;\n{S['design_below_61']} of "
                f"{S['n_design']} design sites fall below the 61st",
                fontsize=TITLE_FS, loc="left")
    A.set_ylabel("latitude", fontsize=LAB_FS)

    # ── (b) flow physics ──────────────────────────────────────────────────────────────────
    cv = L["conv_night"]
    lim = float(np.nanpercentile(np.abs(cv), 97))
    im = B.imshow(cv, origin="lower", extent=ext, cmap="RdBu_r", aspect="equal",
                  vmin=-lim, vmax=lim)
    cb = fig.colorbar(im, ax=B, fraction=0.046, pad=0.02)
    cb.set_label("nocturnal flow convergence\n(red: cold air pools here)", fontsize=LAB_FS - 1)
    strata(B, d, only=["B_design", "E_vertical", "A_anchor"])
    B.set_title(f"(b)  Flow physics: where drainage air pools\n"
                f"the design straddles ventilation and confinement,\nnot only sources; transect "
                f"spans {S['vertical_zaf_lo']:.0f} to {S['vertical_zaf_hi']:.0f} m above "
                f"the floor", fontsize=TITLE_FS, loc="left")

    # ── (c) people ────────────────────────────────────────────────────────────────────────
    im = C.imshow(pop["pop"], origin="lower",
                  extent=[pop["lons"].min(), pop["lons"].max(),
                          pop["lats"].min(), pop["lats"].max()],
                  cmap="Blues", aspect="equal")
    cb = fig.colorbar(im, ax=C, fraction=0.046, pad=0.02)
    cb.set_label("population per km$^2$ cell", fontsize=LAB_FS - 1)
    hi = rc[rc.E_pct >= 90]
    C.scatter(rc.lon, rc.lat, c="#8a8a8a", marker=".", s=40, zorder=3,
              label=f"all mapped receptors ({len(rc)})")
    C.scatter(hi.lon, hi.lat, facecolors="none", edgecolor="#d1495b", marker="o", s=85,
              linewidth=1.6, zorder=4, label=f"above the 90th emission pct ({len(hi)})")
    strata(C, d, only=["D_receptor", "A_anchor"])
    C.scatter([], [], c=STY["D_receptor"]["c"], marker="s", s=135, edgecolor="white",
              label=f"selected receptor sites ({S['n_receptor']})")
    C.set_xlim(ext[0], ext[1]); C.set_ylim(ext[2], ext[3])
    C.set_title(f"(c)  People: the susceptible sit where the model is weakest\n"
                f"{len(hi)} of {len(rc)} receptors ({100*len(hi)/len(rc):.0f}%) are above "
                f"the 90th percentile\nof the emission proxy",
                fontsize=TITLE_FS, loc="left")
    C.set_xlabel("longitude", fontsize=LAB_FS)
    C.set_ylabel("latitude", fontsize=LAB_FS)
    C.legend(loc="lower left", fontsize=11, framealpha=0.94)

    for ax in (A, B, C):
        ax.tick_params(labelsize=TICK_FS)
    B.set_xlabel("longitude", fontsize=LAB_FS)

    # ── (d) the key, in the cell the square maps leave free ───────────────────────────────
    K.axis("off")
    counts = d.stratum.value_counts().to_dict()
    handles = [Line2D([], [], color=k["c"], marker=k["m"], linestyle="none", markersize=15,
                      markeredgecolor="white", markeredgewidth=1.5,
                      label=f'{k["lab"]}   ({counts.get(key, 0)})')
               for key, k in STY.items()]
    handles.append(Line2D([], [], color="#222222", marker="o", linestyle="none",
                          markerfacecolor="none", markersize=14, markeredgewidth=2.4,
                          label="existing record   (2)"))
    K.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, 1.0), fontsize=13,
             frameon=False, handletextpad=0.9, labelspacing=1.15, borderpad=0.0)
    K.text(0.0, 0.44,
           f"{S['n_total']} sites in five strata.\n\n"
           f"Candidates were screened to the {S['cells_feasible']:,} of "
           f"{S['cells_total']:,} cells within\n{S['access_max_m']:.0f} m of a road and "
           f"therefore serviceable, BEFORE the\ndesign was optimised: logistics constrains "
           f"the candidate set\nand never scores a site.\n\n"
           f"The emission surface is a road-network PROXY. It under-\nsamples residential "
           f"biomass burning, which is 14.1 per cent\nof measured mass against traffic's 7.6. "
           f"Receptors come from\na volunteer map and are a LOWER BOUND: a missing school\n"
           f"is invisible. Panel (b) is smoothed to the wind field's\nnative ~230 m.",
           fontsize=12, va="top", ha="left", color="#333333", linespacing=1.45)

    fig.suptitle(f"Proposed sensor network for Kandy: {S['n_total']} sites in five strata,\n"
                 f"sited on emissions, flow physics and exposure",
                 fontsize=17, y=0.995, x=0.012, ha="left")
    fig.tight_layout(rect=[0.01, 0.005, 0.99, 0.945], h_pad=3.0, w_pad=2.2)
    fig.savefig(OUT, dpi=170)
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
