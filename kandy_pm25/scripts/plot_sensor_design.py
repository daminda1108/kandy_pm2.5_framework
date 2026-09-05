"""plot_sensor_design.py -- the proposed network on the surface that chose it.

Two panels, because the design has two justifications and they are not the same picture.
Left: the emission proxy that the design stratum was drawn to span. Right: where susceptible
people are, which is a different objective and selects different sites.

Out: results/figures/kandy_decomp/sensor_design_kandy.png
"""
from __future__ import annotations

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
DEC = REPO / "data" / "processed" / "decomp"
OUTD = REPO / "results" / "figures" / "kandy_decomp"
OUTD.mkdir(parents=True, exist_ok=True)
OUT = OUTD / "sensor_design_kandy.png"

STY = {
    "A_anchor":   dict(c="#111111", m="*", s=420, lab="A  reference anchor (1)"),
    "B_design":   dict(c="#1f6fb4", m="o", s=110, lab="B  design, covariate-spanning (12)"),
    "C_paired":   dict(c="#d1495b", m="^", s=95,  lab="C  paired microsites (9)"),
    "D_receptor": dict(c="#2a9d3f", m="s", s=95,  lab="D  receptor, held out (8)"),
}
EXISTING = [(7.265, 80.625, "FECT Hantana"), (7.2731, 80.6117, "BAM-cal LCS")]


def main() -> None:
    t = np.load(DEC / "S_traffic_kandy.npz")
    E, lat, lon = t["E_fine"], t["fine_lat"], t["fine_lon"]
    d = pd.read_csv(DEC / "sensor_design_kandy.csv")
    rc = pd.read_csv(DEC / "kandy_receptors_ranked.csv")
    pop = np.load(DEC / "population_kandy.npz")
    ext = [lon.min(), lon.max(), lat.min(), lat.max()]

    fig, axes = plt.subplots(1, 2, figsize=(15.5, 7.4))

    # ── left: the emission proxy, log-scaled because it spans 65x ─────────────────────────
    ax = axes[0]
    # Colour by PERCENTILE, not by value. The claim being made is about percentile coverage
    # ("8 of 12 design sites fall below the 61st"), so the reader should be able to check it
    # off the colourbar. A log-value scale renders most of the domain one shade of red and
    # hides exactly the structure the panel exists to show.
    Ef = E[np.isfinite(E)]
    pct = np.full(E.shape, np.nan)
    pct[np.isfinite(E)] = 100.0 * (np.searchsorted(np.sort(Ef), Ef) / len(Ef))
    im = ax.imshow(pct, origin="lower", extent=ext, cmap="YlOrRd", aspect="auto",
                   vmin=0, vmax=100)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    cb.set_label("percentile of the emission proxy within the domain")
    # Mark the floor of the existing network ON the colourbar, with the label placed to the
    # LEFT so it does not collide with the colourbar's own axis label.
    cb.ax.axhline(61, color="#1f6fb4", linewidth=2.4)
    cb.ax.annotate("61st\nfloor of the\nexisting network", xy=(-0.35, 61),
                   xycoords=("axes fraction", "data"), fontsize=7.5, color="#1f6fb4",
                   va="center", ha="right", fontweight="bold")
    for s, g in d.groupby("stratum"):
        k = STY[s]
        ax.scatter(g.lon, g.lat, c=k["c"], marker=k["m"], s=k["s"],
                   edgecolor="white", linewidth=1.1, zorder=5)
    for la, lo, nm in EXISTING:
        ax.scatter(lo, la, facecolors="none", edgecolor="#444444", marker="o", s=190,
                   linewidth=2.0, linestyle="--", zorder=6)
        ax.annotate(nm, (lo, la), textcoords="offset points", xytext=(8, -12),
                    fontsize=8, color="#333333")
    ax.set_title("The design spans the gradient the present network does not\n"
                 "existing records sit in the 61st to 100th percentile; 8 of 12 design "
                 "sites fall below the 61st", fontsize=10.5, loc="left")
    ax.set_xlabel("longitude"); ax.set_ylabel("latitude")

    # ── right: population and the receptors ──────────────────────────────────────────────
    ax = axes[1]
    im = ax.imshow(pop["pop"], origin="lower",
                   extent=[pop["lons"].min(), pop["lons"].max(),
                           pop["lats"].min(), pop["lats"].max()],
                   cmap="Blues", aspect="auto")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    cb.set_label("population per km$^2$ cell")
    ax.scatter(rc.lon, rc.lat, c="#999999", marker=".", s=22, zorder=3,
               label=f"all mapped receptors ({len(rc)})")
    hi = rc[rc.E_pct >= 90]
    ax.scatter(hi.lon, hi.lat, facecolors="none", edgecolor="#d1495b", marker="o", s=52,
               linewidth=1.0, zorder=4, label=f"above the 90th emission pct ({len(hi)})")
    g = d[d.stratum == "D_receptor"]
    ax.scatter(g.lon, g.lat, c=STY["D_receptor"]["c"], marker="s", s=110,
               edgecolor="white", linewidth=1.1, zorder=6, label="selected receptor sites (8)")
    ax.scatter(d[d.stratum == "A_anchor"].lon, d[d.stratum == "A_anchor"].lat,
               c="#111111", marker="*", s=420, edgecolor="white", linewidth=1.1, zorder=7)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_title(f"Susceptible groups sit where the model is least validated\n"
                 f"{len(hi)} of {len(rc)} receptors ({100*len(hi)/len(rc):.0f}%) are above the "
                 f"90th percentile of the emission proxy", fontsize=10.5, loc="left")
    ax.set_xlabel("longitude")
    ax.legend(loc="lower left", fontsize=8.5, framealpha=0.92)

    handles = [Line2D([], [], color=k["c"], marker=k["m"], linestyle="none",
                      markersize=10, markeredgecolor="white", label=k["lab"])
               for k in STY.values()]
    handles.append(Line2D([], [], color="#444444", marker="o", linestyle="none",
                          markerfacecolor="none", markersize=11, label="existing record"))
    axes[0].legend(handles=handles, loc="lower left", fontsize=8.5, framealpha=0.92)

    fig.suptitle("Proposed sensor network for Kandy: 30 sites in four strata",
                 fontsize=13, y=0.99, x=0.008, ha="left")
    fig.text(0.008, 0.005,
             "The emission surface is a road-network PROXY, not a measured inventory, and it "
             "under-samples residential biomass burning (14.1% of measured mass against "
             "traffic's 7.6%). Receptor layer is OpenStreetMap and is a lower bound.",
             fontsize=8, color="#555555")
    fig.tight_layout(rect=[0, 0.022, 1, 0.955])
    fig.savefig(OUT, dpi=190)
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
