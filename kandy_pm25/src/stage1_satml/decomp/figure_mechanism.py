"""
figure_mechanism.py — the emission → terrain/wind → core-hotspot mechanism (2026-06-04).

Visualises the A_transport scenario physics: traffic-congestion EMISSION hotspots
(figX3) are CONTAINED by the basin under calm/shallow-boundary-layer nights and
VENTILATED under windy/deep-mixing days, and the time-average is the urban-core
hotspot. Placement is NO2-corroborated; magnitude is a prior (scenario).

Panels:
  (a) emission source (congestion) + enclosing terrain contours
  (b) calm night (light wind, shallow BLH): solver → emissions TRAPPED on the floor/core
  (c) windy day (strong wind, deep BLH):    solver → emissions DISPERSED / ventilated
  (d) net annual four-factor PM2.5: emission × terrain containment → core hotspot

Out: results/figures/final_model_suite/figX7_emission_terrain_mechanism.png
"""
from __future__ import annotations
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import zoom

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from config import KANDY_PINN_BBOX as BB
from src.stage1_satml.decomp.terrain_transport import solve_terrain, load_grids, DEFAULT_PARAMS
from src.stage1_satml.decomp.figures_pub import _draw, _scale_bar, _north_arrow

DEC = REPO / "data" / "processed" / "decomp"
from src.stage1_satml.decomp.pubfig import PUB_OUT as OUT  # publication style + folder
CEN = (7.2906, 80.6337)


def _solver_field(u, v, blh, lats, lons, z, S, dx):
    out = solve_terrain(u, v, blh, lats, lons, z, S, dx)
    C = out[-1] if isinstance(out, tuple) else out          # solver returns (...,C)
    return C / (C.mean() + 1e-9)


def _channeled_wind(u_syn, v_syn, blh, z, dx, p=DEFAULT_PARAMS):
    """The terrain wind the solver actually uses: synoptic flow with the up-slope
    component removed (blocked by hillsides) + stability-gated katabatic drainage."""
    dzdy, dzdx = np.gradient(z, dx)
    slope = np.hypot(dzdx, dzdy) + 1e-9
    nx, ny = dzdx / slope, dzdy / slope
    block = p["BLOCK"] * np.clip(slope / p["SLOPE_REF"], 0, 1)
    into = u_syn * nx + v_syn * ny
    u_ch = u_syn - block * into * nx; v_ch = v_syn - block * into * ny
    stab = np.clip((600.0 - blh) / 600.0, 0, 1)
    return u_ch - p["DRAIN"] * stab * dzdx, v_ch - p["DRAIN"] * stab * dzdy


def _overlay(ax, z, lats, lons, U, V, syn=None):
    LO = np.linspace(lons.min(), lons.max(), z.shape[1])
    LA = np.linspace(lats.min(), lats.max(), z.shape[0])
    ax.contour(LO, LA, z, levels=8, colors="cyan", linewidths=0.4, alpha=0.55)
    s = max(1, z.shape[0] // 11)
    GLO, GLA = np.meshgrid(LO[::s], LA[::s])
    ax.quiver(GLO, GLA, U[::s, ::s], V[::s, ::s], color="white", scale=28,
              width=0.004, alpha=0.9)
    if syn is not None:
        ax.annotate("", xy=(0.86, 0.9), xytext=(0.74, 0.82), xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="-|>", color="lime", lw=2))
        ax.text(0.74, 0.74, "synoptic\nwind", transform=ax.transAxes, color="lime",
                fontsize=7, fontweight="bold")


def main():
    lats, lons, z, S, dx = load_grids()
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    # two regimes (BLH chosen so terrain blocking stays VISIBLE — deep-BLH 1150 is
    # the most-ventilated case where the structure washes out; 700 m disperses but
    # the ridges still confine the flow, ridge/floor C ≈ 0.12 vs 0.08 at night)
    NIGHT = (0.5, 0.2, 120.0); DAY = (1.5, 0.8, 700.0)
    Cnight = _solver_field(*NIGHT, lats, lons, z, S, dx)             # calm, shallow → trapped
    Cday = _solver_field(*DAY, lats, lons, z, S, dx)                 # breezy → channelled + dispersed
    Un, Vn = _channeled_wind(*NIGHT, z, dx); Ud, Vd = _channeled_wind(*DAY, z, dx)
    # annual 4-factor PM
    d = pd.read_parquet(DEC / "kandy_decomp_predictions_2023_4factor.parquet",
                        columns=["lat", "lon", "pm25_q50"])
    plat = np.sort(d.lat.unique()); plon = np.sort(d.lon.unique())
    PM = d.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(index=plat, columns=plon).values

    fig, ax = plt.subplots(1, 4, figsize=(20, 5.2), constrained_layout=True)
    # (a) emission + terrain
    im0 = ax[0].imshow(zoom(S, 4, order=1), origin="lower", extent=ext, cmap="inferno", aspect="auto")
    ax[0].contour(np.linspace(lons.min(), lons.max(), z.shape[1]),
                  np.linspace(lats.min(), lats.max(), z.shape[0]), z,
                  levels=8, colors="cyan", linewidths=0.4, alpha=0.5)
    ax[0].set_title("(a) emission hotspots (traffic congestion)\n+ enclosing terrain", fontsize=9)
    fig.colorbar(im0, ax=ax[0], shrink=0.7, label="rel. emission")
    # (b) trapped, (c) channelled+dispersed — terrain contours + channelled-wind vectors
    # make the BLOCKING visible: the green synoptic wind is bent to follow the valley.
    vmx = max(np.percentile(Cnight, 98), np.percentile(Cday, 98))
    for a, (C, U, V, ttl) in zip(ax[1:3], [
            (Cnight, Un, Vn, "(b) calm night (BLH≈120 m): drainage + weak mixing\nTRAPPED → core/floor accumulates (ridge/floor 0.08)"),
            (Cday, Ud, Vd, "(c) breezy day (BLH≈700 m): wind CHANNELLED by the valley,\nridges block cross-flow → dispersed but still confined (ridge/floor 0.12)")]):
        im = a.imshow(zoom(C, 4, order=1), origin="lower", extent=ext, cmap="inferno",
                      vmin=0, vmax=vmx, aspect="auto")
        _overlay(a, z, lats, lons, U, V, syn=True)
        a.set_title(ttl, fontsize=8.5); fig.colorbar(im, ax=a, shrink=0.7, label="rel. concentration")
    # (d) net annual PM
    im3 = _draw(ax[3], PM, plat, plon, "cividis", vmin=12, vmax=30)
    ax[3].set_title("(d) net annual PM₂.₅ (four-factor)\nemission × terrain containment → core hotspot", fontsize=9)
    cb = fig.colorbar(im3, ax=ax[3], shrink=0.7, label="PM₂.₅ (µg m⁻³)", extend="both", ticks=[15, 20, 25, 30])
    cb.ax.set_yticklabels(["15 IT-3", "20", "25 IT-2", "30"], fontsize=7)
    for a in ax:
        a.plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.8, ms=5)
        a.set_xticks([]); a.set_yticks([])
    _scale_bar(ax[0], lats, lons); _north_arrow(ax[3], plat, plon)
    fig.suptitle("Mechanism: traffic-congestion emissions, contained by terrain under calm nights and "
                 "ventilated under windy days, accumulate into the urban-core hotspot\n"
                 "(A_transport scenario; placement NO₂-corroborated, magnitude a physical prior)", fontsize=11)
    fig.savefig(OUT / "figX7_emission_terrain_mechanism.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    cc = lambda A, la, lo: A[np.argmin(abs((plat if A.shape[0]==len(plat) else lats)-la))]
    print(f"  night core/edge {Cnight[np.argmin(abs(lats-CEN[0])),np.argmin(abs(lons-CEN[1]))]/np.percentile(Cnight,15):.1f}× "
          f"vs day {Cday[np.argmin(abs(lats-CEN[0])),np.argmin(abs(lons-CEN[1]))]/np.percentile(Cday,15):.1f}×")
    print(f"Wrote {OUT/'figX7_emission_terrain_mechanism.png'}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
