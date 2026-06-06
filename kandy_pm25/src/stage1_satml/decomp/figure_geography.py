"""
figure_geography.py — Kandy emission x confinement geography (3D + panels).

Shows that the spatial PM2.5 structure is CONFINEMENT-dominated, not source-
dominated: emissions sit broadly on the low valley floor, but the enclosed floor
(Hantana ridge to the S, low ranges elsewhere, one open Mahaweli corridor to the
N toward Akurana) is where trapping amplifies them. The off-core FECT sensors
read low because they are ventilated (Hantana ridge) or on the open corridor
(Akurana) — not because they lack emissions.

Out: results/figures/kandy_decomp/geography/{terrain3d,emission_confinement}.png
"""
from __future__ import annotations
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
DEC = HERE / "data" / "processed" / "decomp"
PIN = HERE / "data" / "processed" / "pinn_inputs"
OUT = HERE / "results" / "figures" / "kandy_decomp" / "geography"
OUT.mkdir(parents=True, exist_ok=True)

# observed annual means (assume FECT calibration real, per user 2026-06-03)
OBS = {"NIFS/KOALA core": (7.2675, 80.5985, 24.5, "^"),
       "Kandy city": (7.2906, 80.6337, None, "o"),
       "Hantana ridge": (7.265, 80.625, 10.5, "s")}


def load():
    sat = np.load(DEC / "S_emit_kandy.npz"); lats, lons = sat["lats"], sat["lons"]
    M = np.load(DEC / "M_confinement_kandy.npz"); c, dz = M["c"], M["dz_grid"]
    ntl = np.load(PIN / "kandy_viirs_ntl_stations.npz")
    road = np.load(PIN / "kandy_road_kernel_100m.npz")
    dem = np.load(PIN / "kandy_elev_grid_100m.npz")

    def rg(sla, slo, v):
        LON, LAT = np.meshgrid(lons, lats); pts = np.column_stack([sla.ravel(), slo.ravel()])
        o = griddata(pts, v.ravel(), (LAT, LON), "linear")
        nn = griddata(pts, v.ravel(), (LAT, LON), "nearest"); o[np.isnan(o)] = nn[np.isnan(o)]
        return o
    z = lambda a: (a - a.mean()) / (a.std() + 1e-9)
    E = gaussian_filter(0.5 * z(rg(ntl["lat_grid"], ntl["lon_grid"], ntl["NTL_log"])) +
                        0.5 * z(rg(road["lat_grid"], road["lon_grid"], road["R"])), 1.0)
    ELEV = rg(dem["lat_grid"], dem["lon_grid"], dem["elev"])
    return lats, lons, c, dz, E, ELEV, dem


def terrain3d(dem, lats, lons):
    elev = dem["elev"]; la = dem["lat_grid"]; lo = dem["lon_grid"]
    s = 2
    elev, la, lo = elev[::s, ::s], la[::s, ::s], lo[::s, ::s]
    fig = plt.figure(figsize=(10, 7.5))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(lo, la, elev, cmap="terrain", linewidth=0, antialiased=True,
                    alpha=0.95, rcount=80, ccount=80)
    for name, (plat, plon, val, mk) in OBS.items():
        i = int(np.argmin(np.abs(dem["lat_grid"][:, 0] - plat)))
        j = int(np.argmin(np.abs(dem["lon_grid"][0, :] - plon)))
        e = dem["elev"][i, j]
        ax.scatter([plon], [plat], [e + 60], c="red", s=55, marker=mk,
                   edgecolor="k", depthshade=False)
        lab = name + (f"\n{val} µg/m³" if val else "")
        ax.text(plon, plat, e + 180, lab, fontsize=7, fontweight="bold", color="darkred")
    # corridor arrow (north, toward Akurana / Mahaweli)
    ax.text(lons.mean(), lats.max(), 480, "→ open Mahaweli\ncorridor (N)\nAkurana 16.7",
            fontsize=7, color="navy", fontweight="bold")
    ax.set_xlabel("Lon (°E)"); ax.set_ylabel("Lat (°N)"); ax.set_zlabel("Elevation (m)")
    ax.set_title("Kandy basin: enclosed valley floor (core) vs Hantana ridge (S) — "
                 "the trap that amplifies floor emissions", fontsize=10)
    ax.view_init(elev=32, azim=-118)
    fig.savefig(OUT / "terrain3d.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def panels(lats, lons, c, dz, E, ELEV):
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    from scipy.ndimage import zoom
    fig, ax = plt.subplots(1, 4, figsize=(18, 4.6), constrained_layout=True)
    sets = [(ELEV, "terrain", "(a) Elevation (m)", None),
            (E, "YlOrRd", "(b) Emission index (road+NTL)", None),
            (c, "RdBu_r", "(c) Confinement c(x,y)  (+ traps, − ventilates)", (-2.0, 2.0)),
            (E * (c > 0), "magma", "(d) Emission × in-trap  (the hotspot)", None)]
    for a, (Z, cm, t, lim) in zip(ax, sets):
        vmin, vmax = (lim if lim else (None, None))
        im = a.imshow(zoom(Z, 8, order=3), origin="lower", extent=ext, cmap=cm,
                      vmin=vmin, vmax=vmax, aspect="auto", interpolation="bilinear")
        a.contour(np.linspace(*ext[:2], ELEV.shape[1]), np.linspace(*ext[2:], ELEV.shape[0]),
                  ELEV, levels=range(500, 1300, 150), colors="k", linewidths=0.3, alpha=0.3)
        for name, (plat, plon, val, mk) in OBS.items():
            a.plot(plon, plat, mk, mfc="cyan", mec="k", mew=0.9, ms=7, zorder=5)
            if val:
                a.annotate(f"{val}", (plon, plat), xytext=(5, 4),
                           textcoords="offset points", fontsize=8, fontweight="bold")
        a.set_title(t, fontsize=9); a.set_xlabel("Lon (°E)")
        fig.colorbar(im, ax=a, shrink=0.7)
    ax[0].set_ylabel("Lat (°N)")
    fig.suptitle("Kandy: emissions concentrate on the low floor where confinement is "
                 "strongest → core hotspot; Hantana (ridge) emits but ventilates (10.5) "
                 "— confinement, not source, drives the contrast", fontsize=11)
    fig.savefig(OUT / "emission_confinement.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    lats, lons, c, dz, E, ELEV, dem = load()
    terrain3d(dem, lats, lons)
    panels(lats, lons, c, dz, E, ELEV)
    print(f"Wrote {OUT/'terrain3d.png'}")
    print(f"Wrote {OUT/'emission_confinement.png'}")


if __name__ == "__main__":
    main()
