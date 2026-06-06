"""
figure_area_anchor.py — the 2026-06-04 area-vs-floor level correction, visualised.

Three annual-mean panels with the three independent ground points overlaid
(KOALA-NIFS floor 24.5, FECT-Hantana ridge 10.5, FECT-Akurana peri-urban 16.7):

  (a) BEFORE — floor-anchored (basin mean forced = KOALA 24.5; old beta=1.2472).
      Reconstructed as the area-anchored field × 1.2472 (exact: the only change
      was the scalar level). Over-states the ventilated ridge ~2×.
  (b) AFTER  — area-anchored (basin = VanD area mean ~21; KOALA is the floor the
      confinement field reproduces at NIFS, not the basin mean). Production.
  (c) SCENARIO B — area-anchored + the ground-calibrated steep confinement
      (M_confinement_calibrated_local, floor:ridge 2.33× from the NIFS/Hantana
      pair). Reproduces all three ground points, but rests on N=2 LCS sensors
      (one a flagged PurpleAir) → shipped as a labelled scenario, NOT the headline.

Prints the predicted-vs-observed at each ground site for all three panels.
"""
from __future__ import annotations
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from src.stage1_satml.decomp.figures_pub import _draw, _scale_bar, _north_arrow

DEC = REPO / "data" / "processed" / "decomp"
from src.stage1_satml.decomp.pubfig import PUB_OUT as OUT  # publication style + folder
OUT.mkdir(parents=True, exist_ok=True)
OLD_BETA = 1.2472  # floor-anchor scalar (old design) — reconstructs the BEFORE field

# (lat, lon, observed µg/m³, role)
GROUND = {
    "KOALA-NIFS\n(floor 27m)": (7.2839, 80.6322, 24.5, "o"),
    "FECT-Hantana\n(ridge 196m)": (7.265, 80.625, 10.5, "^"),
    "FECT-Akurana\n(peri-urban)": (7.366, 80.618, 16.7, "s"),
}
REF_YEAR = 2023


def _annual(year):
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}.parquet",
                        columns=["lat", "lon", "pm25_q50"])
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    Z = d.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(
        index=lats, columns=lons).values
    return Z, lats, lons


def _scenario_b(Zarea, lats, lons):
    """area level × (steep ground-calibrated confinement / current confinement).

    Zarea already = L·S·M_current. Multiply by M_steep/M_current (both mean-1) to
    swap the weak production confinement for the NIFS/Hantana-calibrated steep one,
    holding L and S fixed.
    """
    Mc = np.load(DEC / "M_confinement_kandy.npz")
    c = Mc["c"]; kappa = float(Mc["kappa"])
    # production annual-effective confinement (time-mean w≈w_bar from local calib)
    Lz = np.load(DEC / "M_confinement_calibrated_local.npz")
    wbar = float(Lz["w_bar"]); Msteep = Lz["Mbar_calibrated"]
    Mcur = 1.0 + kappa * wbar * c
    Mcur /= Mcur.mean(); Msteep = Msteep / Msteep.mean()
    return Zarea * (Msteep / Mcur)


def _at(Z, lats, lons, la, lo):
    return float(Z[np.argmin(np.abs(lats - la)), np.argmin(np.abs(lons - lo))])


def main():
    Zarea, lats, lons = _annual(REF_YEAR)
    Zbefore = Zarea * OLD_BETA
    Zb = _scenario_b(Zarea, lats, lons)
    panels = [(Zbefore, f"(a) BEFORE — floor-anchored\nbasin {Zbefore.mean():.1f} (forced = KOALA)"),
              (Zarea,  f"(b) AFTER — area-anchored (production)\nbasin {Zarea.mean():.1f} (VanD area mean)"),
              (Zb,     f"(c) SCENARIO B — area + steep confinement\nbasin {Zb.mean():.1f} (ground-calibrated, N=2)")]

    print(f"Ground-point predicted vs observed ({REF_YEAR} annual):")
    print(f"  {'site':14s} {'obs':>5s} {'(a)before':>9s} {'(b)area':>8s} {'(c)scenB':>8s}")
    for nm, (la, lo, obs, mk) in GROUND.items():
        tag = nm.split('\n')[0]
        print(f"  {tag:14s} {obs:5.1f} {_at(Zbefore,lats,lons,la,lo):9.1f} "
              f"{_at(Zarea,lats,lons,la,lo):8.1f} {_at(Zb,lats,lons,la,lo):8.1f}")

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.4), constrained_layout=True)
    im = None
    for ax, (Z, ttl) in zip(axes, panels):
        im = _draw(ax, Z, lats, lons, "cividis", show_marks=False, vmin=8, vmax=30)
        for nm, (la, lo, obs, mk) in GROUND.items():
            ax.plot(lo, la, mk, mfc="cyan", mec="k", mew=1.0, ms=9)
            ax.annotate(f"{nm}\nobs {obs:.1f}", (lo, la), xytext=(5, 5),
                        textcoords="offset points", fontsize=6.5,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", alpha=0.7, lw=0))
        _scale_bar(ax, lats, lons); ax.set_title(ttl, fontsize=9.5)
        ax.set_xticks([]); ax.set_yticks([])
    _north_arrow(axes[2], lats, lons)
    cb = fig.colorbar(im, ax=axes, label="annual PM₂.₅ (µg m⁻³)", extend="both", shrink=0.7)
    fig.suptitle("Area-vs-floor level correction (2026-06-04): KOALA anchors the valley FLOOR, "
                 "not the basin area mean — cyan markers are independent ground sensors", fontsize=11)
    fig.savefig(OUT / "figX1_area_vs_floor.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"\nWrote {OUT / 'figX1_area_vs_floor.png'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
