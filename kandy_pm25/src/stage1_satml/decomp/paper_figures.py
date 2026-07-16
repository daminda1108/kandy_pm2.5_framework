"""
paper_figures.py — the 12-figure publication suite (2026-06-05).
Plan + locked design: docs/paper_figures_plan_2026-06-05.md.

Narrative: I setting (F1) · II mechanism (F2 schematic, F3 decomposition, F4 wind-
terrain engine, F5 emission) · III spatiotemporal output (F6 seasonal, F7 diurnal,
F8 circumstances, F9 scales) · IV validation/burden (F10, F11, F12).

Universal turbo PM scale 13–30; inferno for emission/intensity; speed-scaled WindNinja
quiver on transport/output figures; accumulation diagnostics (ventilation index, flux
convergence). Style via paperfig→pubfig (SciencePlots+STIX). Out: results/figures/paper_figures/.

Run:  python paper_figures.py --figs all      (or  --figs f1,f4,f7 …)
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import zoom, gaussian_filter

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from src.stage1_satml.decomp import paperfig as pf
from src.stage1_satml.decomp.figures_pub import _draw, _elev, _scale_bar, _north_arrow, LANDMARKS
from config import KANDY_PINN_BBOX as BB

YEAR = 2023
NIGHT_H = [0, 1, 2, 3, 4, 5]        # genuine deep-night (city asleep — low emissions)
MORNING_H = [6, 7, 8, 9]            # morning rush peak (high traffic + still-shallow BLH = trapped)
DAY_H = [11, 12, 13, 14, 15, 16]    # well-mixed midday (deep BLH = ventilated)
DEC, STG, PIN = pf.DEC, pf.STG, pf.PIN
CEN = pf.CEN
GROUND = {"observed": "#2C7FB5", "learned": "#41AB5D", "physics": "#E08214"}


# ════════════════════════ F1 — study area & terrain ════════════════════════
def _osm_layers():
    """OSM water / rivers / roads / place-points within the Kandy bbox, cached to disk
    (GeoJSON) so the full-suite run stays fast and works offline after the first pull."""
    import geopandas as gpd
    from config import KANDY_PINN_BBOX as BB
    cdir = DEC / "osm_kandy"; cdir.mkdir(exist_ok=True)
    bbox = (BB["lon_min"], BB["lat_min"], BB["lon_max"], BB["lat_max"])
    layers = {"water": {"natural": "water", "water": True},
              "rivers": {"waterway": ["river", "stream", "canal"]},
              "roads": {"highway": ["motorway", "trunk", "primary", "secondary", "tertiary"]},
              "places": {"place": ["city", "town", "village", "suburb", "hamlet", "neighbourhood"]}}
    out = {}
    for nm, tags in layers.items():
        fp = cdir / f"{nm}.geojson"
        if fp.exists():
            out[nm] = gpd.read_file(fp)
        else:
            import osmnx as ox
            g = ox.features_from_bbox(bbox=bbox, tags=tags)
            g = g[g.geometry.notna()].reset_index()
            keep = [c for c in ("name", "place", "highway", "waterway", "natural", "geometry") if c in g.columns]
            g = g[keep]
            g.to_file(fp, driver="GeoJSON")
            out[nm] = g
    return out


def f1_studyarea():
    from matplotlib.colors import LightSource
    import matplotlib.patheffects as mpe
    from config import KANDY_PINN_BBOX as BB
    elev, ela, elo = _elev()
    ext = [elo.min(), elo.max(), ela.min(), ela.max()]
    ls = LightSource(azdeg=315, altdeg=45)
    fig = plt.figure(figsize=(7.0, 7.0))
    ax = fig.add_axes([0.10, 0.07, 0.80, 0.80])
    rgb = ls.shade(elev, cmap=plt.cm.terrain, blend_mode="soft", vert_exag=1.5,
                   dx=90, dy=90, vmin=250, vmax=1320)
    ax.imshow(rgb, origin="lower", extent=ext, aspect="auto", interpolation="bilinear", zorder=0)
    cs = ax.contour(elo, ela, elev, levels=range(450, 1350, 150), colors="0.3", linewidths=0.3, alpha=0.5, zorder=1)
    ax.clabel(cs, fontsize=5, fmt="%d m")
    # ── real geography from OSM (roads, river, lake, towns) ──────────────────
    try:
        L = _osm_layers()
        L["roads"].plot(ax=ax, color="0.45", linewidth=0.45, alpha=0.7, zorder=2)
        if len(L["rivers"]):
            L["rivers"].plot(ax=ax, color="#2171B5", linewidth=1.1, alpha=0.9, zorder=3)
        if len(L["water"]):
            L["water"].plot(ax=ax, facecolor="#4292C6", edgecolor="#08519C", linewidth=0.4, alpha=0.95, zorder=3)
        # curated, well-spread town labels (accurate OSM coords); city marker only for Kandy
        pls = L["places"]; pls = pls[pls["name"].notna()].copy()
        pls["lat"] = pls.geometry.centroid.y; pls["lon"] = pls.geometry.centroid.x
        want = ["Katugastota", "Peradeniya", "Kundasale", "Wattegama", "Madawala", "Talatuoya",
                "Ampitiya", "Gannoruwa", "Tennekumbura", "Halloluwa", "Pallekele", "Hindagala", "Nugawela"]
        for _, r in pls[pls["name"].isin(want)].drop_duplicates("name").iterrows():
            ax.plot(r.lon, r.lat, "o", ms=2.6, mfc="0.15", mec="white", mew=0.4, zorder=5)
            ax.annotate(r["name"], (r.lon, r.lat), (2.5, 2.5), textcoords="offset points",
                        fontsize=5.6, color="0.12", zorder=6,
                        path_effects=[mpe.withStroke(linewidth=1.4, foreground="white")])
    except Exception as e:
        print(f"  (OSM layers skipped: {e})")
    # city centre + the ground sensors (F1 is the reference map → pins belong here)
    ax.plot(80.6337, 7.2906, marker="*", mfc="#D7263D", mec="k", mew=0.8, ms=15, zorder=8, label="Kandy city centre")
    ax.annotate("Kandy", (80.6337, 7.2906), (5, -9), textcoords="offset points", fontsize=8, fontweight="bold",
                color="#7a0010", zorder=8, path_effects=[mpe.withStroke(linewidth=1.6, foreground="white")])
    for nm, la, lo, mk, c in [("NIFS / KOALA (valley floor)", 7.2839, 80.6322, "^", "#00E5FF"),
                              ("FECT–Hantana (ridge)", 7.265, 80.625, "s", "#FF2D95")]:
        ax.plot(lo, la, mk, mfc=c, mec="k", mew=0.9, ms=9, zorder=8, label=nm)
    ax.annotate("HANTANA RANGE", (80.622, 7.247), color="0.1", fontsize=8, fontweight="bold", rotation=-15, ha="center", zorder=7)
    ax.annotate("Udawattakele\nforest reserve", (80.652, 7.302), color="#0b3d0b", fontsize=6.2, ha="center", zorder=7,
                path_effects=[mpe.withStroke(linewidth=1.4, foreground="white")])
    ax.annotate("Mahaweli R. /\nventilation corridor", (80.598, 7.318), (80.578, 7.288), color="#08306b", fontsize=6.4,
                ha="center", zorder=7, arrowprops=dict(arrowstyle="-|>", color="#08306b", lw=1.2),
                path_effects=[mpe.withStroke(linewidth=1.4, foreground="white")])
    # graticule
    ax.set_xticks(np.arange(80.58, 80.70, 0.03)); ax.set_yticks(np.arange(7.24, 7.36, 0.03))
    ax.grid(True, color="0.5", lw=0.3, alpha=0.4); ax.tick_params(labelsize=7)
    ax.set_xlim(BB["lon_min"], BB["lon_max"]); ax.set_ylim(BB["lat_min"], BB["lat_max"])
    _scale_bar(ax, ela.ravel() if ela.ndim == 1 else ela[:, 0], elo.ravel() if elo.ndim == 1 else elo[0, :])
    _north_arrow(ax, ela.ravel(), elo.ravel())
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    ax.set_title("Kandy — intermontane valley (15 × 15 km study domain): terrain, towns, river & lake", fontsize=10)
    ax.legend(loc="lower right", fontsize=7, framealpha=0.92, edgecolor="0.6")
    try:
        import cartopy.crs as ccrs, cartopy.feature as cfeature
        from matplotlib.patches import Rectangle
        axi = fig.add_axes([0.125, 0.625, 0.205, 0.205], projection=ccrs.PlateCarree())
        axi.set_extent([79.4, 82.1, 5.7, 10.0], ccrs.PlateCarree())
        axi.add_feature(cfeature.LAND, facecolor="#EAE6DA"); axi.add_feature(cfeature.OCEAN, facecolor="#CFE2F3")
        axi.add_feature(cfeature.COASTLINE, lw=0.5)
        cx, cy, hw = 80.6337, 7.2906, 0.30          # study-domain box, enlarged for country-scale visibility
        axi.add_patch(Rectangle((cx - hw, cy - hw), 2 * hw, 2 * hw, ec="#D7263D", fc="none",
                                lw=1.4, transform=ccrs.PlateCarree(), zorder=6))
        axi.annotate("Kandy", (cx, cy + hw), (80.0, 8.9), fontsize=6, color="#7a0010", fontweight="bold",
                     transform=ccrs.PlateCarree(), arrowprops=dict(arrowstyle="-", color="#7a0010", lw=0.5))
        axi.text(79.55, 9.55, "SRI LANKA", fontsize=6, fontweight="bold", color="0.25", transform=ccrs.PlateCarree())
        for s in axi.spines.values():
            s.set(edgecolor="0.35", lw=0.9)
    except Exception as e:
        print(f"  (locator inset skipped: {e})")
    pf.save(fig, "F1_study_area", pdf=True, square=False)


# ════════════════════════ F2 — model schematic ═════════════════════════════
def f2_schematic():
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    fig, ax = plt.subplots(figsize=(7.0, 3.9)); ax.set_xlim(0, 100); ax.set_ylim(0, 56); ax.axis("off")
    def box(x, y, w, h, text, fc, ec="k", fs=8):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4", fc=fc, ec=ec, lw=0.8, alpha=0.9))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, zorder=5)
    def arrow(x0, y0, x1, y1):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=12, lw=0.9, color="0.3"))
    # lane 1 inputs
    inp = [("Satellite\n(VanD, GHAP,\nMAIAC, NO₂)", 46), ("Reanalysis\n(ERA5 BLH,\nwind, T)", 34),
           ("CTM prior\n(GEOS-CF,\nCAMS)", 22), ("DEM (SRTM)\n+ WindNinja", 10)]
    for t, y in inp:
        box(2, y, 16, 9, t, "#EAF2F8", fs=6.6)
    # lane 2 components
    comp = [("$T(t)$ temporal\nGBM + conformal", 46, GROUND["learned"]),
            ("$B(t)$ background\nrural VanD × CTM", 34, GROUND["observed"]),
            ("$S_{emit}$ source\n+ congestion", 22, GROUND["observed"]),
            ("$M$ confinement /\n$A$ WindNinja transport", 10, GROUND["physics"])]
    for t, y, c in comp:
        box(26, y, 20, 9, t, c, fs=6.8)
    for _, y in inp:
        arrow(18, y + 4.5, 26, y + 4.5)
    # lane 3 assembly
    box(52, 26, 18, 14, "Additive assembly\n$B+[T-B]\\,P_{local}$\n(basin mean preserved)", "#FCF3CF", fs=7.5)
    for y in (50.5, 38.5, 26.5, 14.5):
        arrow(46, y, 52, 33)
    box(74, 30, 12, 9, "Conformal\nUQ", "#F5EEF8", fs=7.5); arrow(70, 33, 74, 34.5)
    box(90, 24, 9, 16, "1 km ×\nhourly ×\n{q05,q50,q95}", "#E8F8F5", fs=7); arrow(86, 34.5, 90, 32)
    # grounding key
    for i, (k, c) in enumerate(GROUND.items()):
        ax.add_patch(FancyBboxPatch((2 + i * 18, 1.5), 3, 2.4, boxstyle="round,pad=0.1", fc=c, ec="k", lw=0.5))
        ax.text(6 + i * 18, 2.7, {"observed": "observed", "learned": "learned", "physics": "physics-imposed"}[k], fontsize=7, va="center")
    ax.set_title("Model architecture: observation-grounded additive decomposition", fontsize=10.5)
    pf.save(fig, "F2_schematic", pdf=True)


# ════════════════════════ F3 — additive decomposition ══════════════════════
def f3_decomposition():
    add, lats, lons = pf.field(YEAR, "additive")
    b = pd.read_parquet(DEC / f"B_background_hourly_{YEAR}.parquet")
    Bann = float(b["B"].mean())
    incr = add - Bann
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    # partition per year
    part = []
    for y in range(2019, 2024):
        a = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}{pf.ADD}.parquet", columns=["pm25_q50"])
        bb = pd.read_parquet(DEC / f"B_background_hourly_{y}.parquet")["B"].mean()
        basin = float(a.pm25_q50.mean()); part.append((y, float(bb), basin - float(bb), basin))
    pdf = pd.DataFrame(part, columns=["year", "B", "I", "basin"]); pdf["loc%"] = pdf.I / pdf.basin * 100

    fig, AX = plt.subplots(2, 2, figsize=(7.2, 6.9), constrained_layout=True)
    axa, axb, axc, axd = AX[0, 0], AX[0, 1], AX[1, 0], AX[1, 1]
    im = axa.imshow(np.full_like(add, Bann), origin="lower", extent=ext, cmap=pf.PM_CMAP, norm=pf.pm_norm(), aspect="equal")
    axa.set_title(f"(a) regional background $B$ (uniform {Bann:.1f} µg m$^{{-3}}$)", fontsize=9)
    pf.pm_cbar(fig, im, axa, 0.85)
    imb = axb.imshow(zoom(incr, 8, order=1), origin="lower", extent=ext, cmap=pf.INFERNO, aspect="equal", vmin=0, vmax=np.percentile(incr, 99), interpolation="bilinear")
    axb.set_title("(b) local increment $[T-B]\\,P_{local}$", fontsize=9)
    fig.colorbar(imb, ax=axb, shrink=0.85, label="µg m$^{-3}$")
    imc = _draw(axc, add, lats, lons, pf.PM_CMAP, norm=pf.pm_norm())
    axc.set_aspect("equal"); axc.set_title(f"(c) total $\\widehat{{PM}}_{{2.5}}$ ({add.mean():.1f} µg m$^{{-3}}$)", fontsize=9); pf.pm_cbar(fig, imc, axc, 0.85)
    for a in (axa, axb, axc):
        a.set_xticks([]); a.set_yticks([])
    x = pdf.year.astype(str)
    axd.bar(x, pdf.B, color="#6BAED6", label="regional / transboundary $B$")
    axd.bar(x, pdf.I, bottom=pdf.B, color="#E6550D", label="local increment (actionable)")
    for i, r in pdf.iterrows():
        axd.text(i, r.basin + 0.35, f"{r['loc%']:.0f}%", ha="center", fontsize=8, fontweight="bold")
    axd.set_ylabel("annual PM$_{2.5}$ (µg m$^{-3}$)"); axd.set_ylim(0, pdf.basin.max() * 1.2)
    axd.set_title("(d) regional-vs-local partition\nlocal share dips 2020–22 (lockdown + fuel crisis), recovers", fontsize=8.6)
    axd.legend(fontsize=7, loc="lower center")
    fig.suptitle("Additive decomposition: uniform regional background + local increment", fontsize=10.5)
    pf.save(fig, "F3_decomposition")


# ════════════════════════ F4 — wind–terrain mechanism ⭐ ════════════════════
def f4_mechanism():
    Zm, lats, lons = pf.field(YEAR, "4factor", hours=MORNING_H)
    Zd, _, _ = pf.field(YEAR, "4factor", hours=DAY_H)
    Um, Vm, wlat, wlon = pf.wn_regime_mean(YEAR, MORNING_H)
    Ud, Vd, _, _ = pf.wn_regime_mean(YEAR, DAY_H)
    Un, Vn, _, _ = pf.wn_regime_mean(YEAR, NIGHT_H)
    # spatial ventilation index VI(x,y) = mean BLH × |wind(x,y)| (deep night) — low = stagnant
    m = pf._met(YEAR); loct = pd.to_datetime(m.datetime_utc, utc=True).dt.tz_convert("Asia/Colombo")
    blh_n = m[loct.dt.hour.isin(NIGHT_H)].blh_m.mean()
    VI = blh_n * np.hypot(Un, Vn)
    # flux convergence (accumulation) for a representative calm, shallow-BLH morning
    C, U, V, slat, slon, z, dx = pf.solver_state(0.6, 0.2, 180.0)
    conv = gaussian_filter(pf.flux_convergence(C, U, V, dx), 1.0)

    fig, ax = plt.subplots(2, 2, figsize=(7.0, 6.4), constrained_layout=True)
    for a, (Z, Uq, Vq, ttl) in zip([ax[0, 0], ax[0, 1]], [
            (Zm, Um, Vm, "(a) morning rush (06–09 LT) — trapped"),
            (Zd, Ud, Vd, "(b) midday (11–16 LT) — ventilated")]):
        im = _draw(a, Z, lats, lons, pf.PM_CMAP, norm=pf.pm_norm())
        pf.emission_contours(a)               # green = high traffic emission (hotspot risk)
        pf.quiver(a, Uq, Vq, wlat, wlon, step=6, color="white")

        a.set_title(ttl, fontsize=8.6); a.set_xticks([]); a.set_yticks([])
        pf.pm_cbar(fig, im, a, 0.8)
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    a = ax[1, 0]
    imv = a.imshow(zoom(VI, 4, order=1), origin="lower", extent=ext, cmap="cividis_r", aspect="auto")
    pf.quiver(a, Un, Vn, wlat, wlon, step=6, color="white")

    a.set_title("(c) ventilation index $VI=\\mathrm{BLH}\\cdot|u|$ (night)\n— dark = stagnant, accumulation-prone", fontsize=8.6)
    a.set_xticks([]); a.set_yticks([]); fig.colorbar(imv, ax=a, shrink=0.8, label="VI (m$^2$ s$^{-1}$)")
    a = ax[1, 1]
    cl = np.percentile(np.abs(conv), 98)
    imc = a.imshow(zoom(conv, 4, order=1), origin="lower", extent=ext, cmap="RdBu_r", vmin=-cl, vmax=cl, aspect="auto")

    a.set_title("(d) flux convergence $-\\nabla\\!\\cdot(Cu)$ (calm morning)\n— red = pollution accumulates", fontsize=8.6)
    a.set_xticks([]); a.set_yticks([]); fig.colorbar(imc, ax=a, shrink=0.8, label="accumulation")
    fig.suptitle("The wind–terrain engine: WindNinja winds trap the morning-rush emissions, then ventilate by midday", fontsize=10.5)
    pf.save(fig, "F4_mechanism", pdf=False)


# ════════════════════════ F5 — emission source ═════════════════════════════
def f5_emission():
    d = np.load(DEC / "S_traffic_kandy.npz")
    flat, flon = d["fine_lat"], d["fine_lon"]; ext = [flon.min(), flon.max(), flat.min(), flat.max()]
    bt = d["betweenness_fine"] if "betweenness_fine" in d.files else d["E_fine"]
    od = d["closeness_fine"] if "closeness_fine" in d.files else d["E_fine"]
    E = d["E_fine"]
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.7), constrained_layout=True)
    for a, (Z, ttl) in zip(ax, [(bt, "(a) betweenness centrality\n(pass-by flow, r≈0.77 vs measured)"),
                                (od, "(b) closeness centrality\n(origin–destination trip-ends)"),
                                (E, "(c) congestion emission $S$\n(betweenness+closeness × COPERT EF)")]):
        im = a.imshow(zoom(Z, 2, order=1), origin="lower", extent=ext, cmap=pf.INFERNO, aspect="auto", interpolation="bilinear")

        a.set_title(ttl, fontsize=8.6); a.set_xticks([]); a.set_yticks([])
        fig.colorbar(im, ax=a, shrink=0.75, label="normalised")
    for nm, (la, lo) in {"lake round": (7.291, 80.638), "Katugastota": (7.322, 80.63), "Peradeniya": (7.255, 80.597)}.items():
        ax[2].annotate(nm, (lo, la), color="white", fontsize=6.5)
    fig.suptitle("Emission source: bottom-up centrality-AADT congestion surface (inferno)", fontsize=10.5)
    pf.save(fig, "F5_emission")


# ════════════════════════ F6 — annual + seasonal ═══════════════════════════
def f6_seasonal():
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{YEAR}{pf.ADD}.parquet", columns=["time", "lat", "lon", "pm25_q50"])
    d["loct"] = pd.to_datetime(d.time, utc=True).dt.tz_convert("Asia/Colombo"); d["s"] = d.loct.dt.month % 12 // 3
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique()); names = {0: "DJF", 1: "MAM", 2: "JJA", 3: "SON"}
    def grid(x): return x.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(index=lats, columns=lons).values
    Zann = grid(d); Zs = [grid(d[d.s == k]) for k in range(4)]
    se = pf.load_seasonal_episodic()
    Un, Vn, wlat, wlon = pf.wn_regime_mean(YEAR, NIGHT_H + DAY_H)
    fig, axes = plt.subplots(2, 5, figsize=(7.2, 3.5), constrained_layout=True)
    panels = [("ANNUAL", Zann)] + [(names[k], Zs[k]) for k in range(4)]
    # per-season ERA5→WindNinja wind: DJF blows toward SW, JJA toward NE (monsoon reversal)
    winds = [(Un, Vn, wlat, wlon)] + [pf.seas_wind(se, names[k]) for k in range(4)]
    for c, (ttl, Z) in enumerate(panels):
        im = _draw(axes[0, c], Z, lats, lons, pf.PM_CMAP, show_marks=False, norm=pf.pm_norm())
        U_, V_, la_, lo_ = winds[c]
        pf.quiver(axes[0, c], U_, V_, la_, lo_, step=8, solid="#1A1A1A")
        axes[0, c].set_title(f"{ttl}  {np.nanmean(Z):.1f}", fontsize=9)
        an = Z - np.nanmean(Zann)
        vl = np.nanpercentile(np.abs([z - np.nanmean(Zann) for z in [Zann] + Zs]), 98)
        ima = axes[1, c].imshow(zoom(an, 8, order=1), origin="lower", extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                                cmap="RdBu_r", vmin=-vl, vmax=vl, aspect="auto", interpolation="bilinear")
        axes[1, c].set_title(f"{ttl} − annual", fontsize=8.5)
        if c == 4:
            fig.colorbar(ima, ax=axes[1, :], shrink=0.6, label="anomaly (µg m$^{-3}$)")
    for a in axes.ravel():
        a.set_xticks([]); a.set_yticks([])
    pf.pm_cbar(fig, _draw(axes[0, 0], Zann, lats, lons, pf.PM_CMAP, show_marks=False, norm=pf.pm_norm()), list(axes[0, :]), 0.6)
    fig.suptitle("Annual + seasonal PM$_{2.5}$ with per-season WindNinja flow (NE-monsoon→SW vs "
                 "SW-monsoon→NE, ventilated JJA) — additive headline", fontsize=10)
    pf.save(fig, "F6_seasonal")


# ════════════════════════ F7 — diurnal evolution ⭐ ═════════════════════════
def f7_diurnal():
    HRS = [3, 7, 10, 14, 18, 22]                 # deep-night · morning peak · late-am · midday trough · evening peak · late-evening
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{YEAR}{pf.ADD}.parquet", columns=["time", "lat", "lon", "pm25_q50"])
    d["loct"] = pd.to_datetime(d.time, utc=True).dt.tz_convert("Asia/Colombo"); d["h"] = d.loct.dt.hour
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    def grid(x): return x.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(index=lats, columns=lons).values
    diur = d.groupby("h").pm25_q50.mean()
    fig = plt.figure(figsize=(7.2, 6.6)); gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 0.8], hspace=0.18, wspace=0.06)
    im = None
    for k, h in enumerate(HRS):
        a = fig.add_subplot(gs[k // 3, k % 3]); Z = grid(d[d.h == h])
        im = _draw(a, Z, lats, lons, pf.PM_CMAP, show_marks=False, norm=pf.pm_norm())
        rg = NIGHT_H if h <= 5 else MORNING_H if h <= 9 else DAY_H if h <= 16 else MORNING_H
        U, V, wlat, wlon = pf.wn_regime_mean(YEAR, rg, sample=150)
        pf.quiver(a, U, V, wlat, wlon, step=7, color="white", lw=0.5)

        lab = {3: "deep-night", 7: "morning peak", 10: "late morning", 14: "midday trough", 18: "evening peak", 22: "late evening"}[h]
        a.set_title(f"{h:02d} LT — {lab}  ({np.nanmean(Z):.0f})", fontsize=8.4); a.set_xticks([]); a.set_yticks([])
    pf.pm_cbar(fig, im, [fig.axes[i] for i in range(6)], 0.85)
    axc = fig.add_subplot(gs[2, :])
    axc.plot(diur.index, diur.values, "o-", color="#B35806", lw=2)
    axc.axvline(7, color="grey", ls=":"); axc.axvline(14, color="grey", ls=":"); axc.axvline(18, color="grey", ls=":")
    axc.annotate("07 morning peak", (7, diur.max()), fontsize=8, ha="center")
    axc.annotate("14 trough", (14, diur.min()), fontsize=8); axc.annotate("18 evening peak", (18.2, diur[18]), fontsize=8)
    for h in HRS:
        axc.axvline(h, color="0.85", lw=0.5, zorder=0)
    axc.set_xlabel("local hour"); axc.set_ylabel("basin PM$_{2.5}$ (µg m$^{-3}$)"); axc.set_xticks(range(0, 24, 2)); axc.grid(alpha=0.25)
    fig.suptitle("Diurnal evolution: low overnight → morning rush peak → midday ventilation → evening rush rebuild", fontsize=10.5)
    pf.save(fig, "F7_diurnal")


# ════════════════════════ F8 — different circumstances ⭐ ═══════════════════
def f8_regimes():
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{YEAR}{pf.ADD}.parquet", columns=["time", "lat", "lon", "pm25_q50"])
    d["loct"] = pd.to_datetime(d.time, utc=True).dt.tz_convert("Asia/Colombo")
    d["h"] = d.loct.dt.hour; d["s"] = d.loct.dt.month % 12 // 3
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    def grid(x): return x.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(index=lats, columns=lons).values
    regs = [("calm morning rush\n(trapped)", d[d.h.isin(MORNING_H)], MORNING_H),
            ("windy midday\n(ventilated)", d[d.h.isin(DAY_H)], DAY_H),
            ("MAM inter-monsoon\n(transboundary high)", d[d.s == 1], MORNING_H),
            ("JJA monsoon\n(washout)", d[d.s == 2], DAY_H)]
    fig, ax = plt.subplots(1, 4, figsize=(7.2, 2.4), constrained_layout=True); im = None
    for a, (ttl, sub, rg) in zip(ax, regs):
        Z = grid(sub); im = _draw(a, Z, lats, lons, pf.PM_CMAP, show_marks=False, norm=pf.pm_norm())
        pf.emission_contours(a, lw=0.5)
        U, V, wlat, wlon = pf.wn_regime_mean(YEAR, rg, sample=150)
        pf.quiver(a, U, V, wlat, wlon, step=8, color="white", lw=0.4)

        a.set_title(f"{ttl}\nbasin {np.nanmean(Z):.1f} µg m$^{{-3}}$", fontsize=8.6); a.set_xticks([]); a.set_yticks([])
    pf.pm_cbar(fig, im, list(ax), 0.75)
    fig.suptitle("Spatiotemporal response to circumstance: stagnation traps, wind ventilates, monsoon washes out", fontsize=10.5)
    pf.save(fig, "F8_circumstances")


# ════════════════════════ F9 — variation across scales ═════════════════════
def f9_scales():
    frames = []
    for y in range(2019, 2024):
        a = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}{pf.ADD}.parquet", columns=["time", "pm25_q05", "pm25_q50", "pm25_q95"])
        frames.append(a.groupby("time")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean())
    bm = pd.concat(frames); bm.index = pd.to_datetime(bm.index, utc=True).tz_convert("Asia/Colombo")
    bm["y"] = bm.index.year; bm["m"] = bm.index.month; bm["dow"] = bm.index.dayofweek; bm["h"] = bm.index.hour
    bm = bm[bm.y.between(2019, 2023)]
    BAND = "#FCE3B4"; LN = "#B35806"
    fig = plt.figure(figsize=(7.2, 5.0))
    gs = fig.add_gridspec(2, 3, hspace=0.55, wspace=0.45)
    axa, axb, axc = (fig.add_subplot(gs[0, i]) for i in range(3))
    axd = fig.add_subplot(gs[1, 0])
    ya = bm.groupby("y")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean()
    axa.fill_between(ya.index, ya.pm25_q05, ya.pm25_q95, color="#C6DBEF", alpha=.6); axa.plot(ya.index, ya.pm25_q50, "o-", color="#08519C", lw=2.2)
    axa.scatter([2019], [24.52], marker="*", s=160, color="k", zorder=6)
    axa.annotate("KOALA 2019", (2019, 24.52), (2019.18, 27.6), fontsize=6.3, ha="left",
                 arrowprops=dict(arrowstyle="-", color="0.5", lw=0.4))
    axa.annotate("2021 COVID/fuel", (2021, ya.pm25_q50.loc[2021]), (2021, ya.pm25_q50.loc[2021] - 3.6),
                 fontsize=6.5, ha="center", va="center", arrowprops=dict(arrowstyle="->", color="0.5", lw=0.4))
    axa.set_title("(a) inter-annual", fontsize=9.5); axa.set_xticks(range(2019, 2024)); axa.tick_params(axis="x", labelrotation=0)
    mo = bm.groupby("m")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean()
    axb.fill_between(mo.index, mo.pm25_q05, mo.pm25_q95, color=BAND, alpha=.8); axb.plot(mo.index, mo.pm25_q50, "o-", color=LN, lw=2.2)
    axb.axvspan(5.5, 8.5, color="#9ECAE1", alpha=.25); axb.annotate("SW monsoon\nwashout", (7, mo.pm25_q50.min()), fontsize=7, ha="center", va="bottom")
    axb.set_title("(b) seasonal", fontsize=9.5); axb.set_xlabel("month"); axb.set_xticks(range(1, 13, 2))
    wk = bm.groupby("dow").pm25_q50; axc.bar(range(7), wk.mean(), yerr=wk.sem(), color=["#6BAED6"] * 5 + ["#FDAE6B", "#FD8D3C"], capsize=2)
    axc.set_xticks(range(7)); axc.set_xticklabels(["M", "T", "W", "T", "F", "S", "S"]); axc.set_title("(c) weekly", fontsize=9.5)
    lo, hi = wk.mean().min(), wk.mean().max(); axc.set_ylim(lo - (hi - lo) * 1.6 - .3, hi + (hi - lo) * 1.6 + .3)
    hr = bm.groupby("h")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean()
    axd.fill_between(hr.index, hr.pm25_q05, hr.pm25_q95, color=BAND, alpha=.8); axd.plot(hr.index, hr.pm25_q50, "o-", color=LN, lw=2.2)
    axd.axvline(7, color="grey", ls=":"); axd.axvline(18, color="grey", ls=":")
    axd.set_title("(d) diurnal", fontsize=9.5); axd.set_xlabel("local hour"); axd.set_xticks(range(0, 24, 6))
    for a in (axa, axb, axc, axd):
        a.set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)", fontsize=8); a.grid(alpha=.25); a.tick_params(labelsize=7.5)
    # ventilation-index driver row (VI = BLH·|u|): seasonal + diurnal
    m = pf._met(YEAR); m["loct"] = pd.to_datetime(m.datetime_utc, utc=True).dt.tz_convert("Asia/Colombo")
    m["h"] = m.loct.dt.hour; m["mon"] = m.loct.dt.month
    by_h = m.groupby("h"); by_m = m.groupby("mon")
    axe = fig.add_subplot(gs[1, 1]); axf = fig.add_subplot(gs[1, 2])
    axe.plot(by_m.mon.first(), (by_m.blh_m.mean() * by_m.apply(lambda g: np.hypot(g.u10, g.v10).mean())), "s-", color="#2171B5", lw=2)
    axe.axvspan(5.5, 8.5, color="#9ECAE1", alpha=.25)
    axe.set_title("(e) VI seasonal (high JJA)", fontsize=9.5)
    axe.set_xlabel("month"); axe.set_xticks(range(1, 13, 2)); axe.grid(alpha=.25); axe.tick_params(labelsize=7.5); axe.set_ylabel("VI (m$^2$ s$^{-1}$)", fontsize=8)
    axf.plot(by_h.h.first(), (by_h.blh_m.mean() * by_h.apply(lambda g: np.hypot(g.u10, g.v10).mean())), "o-", color="#2171B5", lw=2)
    axf.axvline(7, color="grey", ls=":")
    axf.set_title("(f) VI diurnal (low at night)", fontsize=9.5)
    axf.set_xlabel("local hour"); axf.set_xticks(range(0, 24, 6)); axf.grid(alpha=.25); axf.tick_params(labelsize=7.5); axf.set_ylabel("VI (m$^2$ s$^{-1}$)", fontsize=8)
    fig.suptitle("PM$_{2.5}$ variation across every scale, driven by the ventilation index $VI=\\mathrm{BLH}\\cdot|u|$ (e,f)", fontsize=10.5)
    pf.save(fig, "F9_scales")


# ════════════════════════ F10 — validation ═════════════════════════════════
def f10_validation():
    from scipy.stats import pearsonr
    from scipy.spatial import cKDTree
    ghap = pd.read_parquet(DEC / "ghap_kandy_monthly_2019_2022.parquet")
    dec = []
    for y in range(2019, 2023):
        a = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}.parquet", columns=["time", "lat", "lon", "pm25_q50"])
        a["month"] = pd.to_datetime(a.time).dt.month; dec.append(a)
    dec = pd.concat(dec)
    dc = dec.groupby("month").pm25_q50.mean(); gc = ghap.groupby("month").ghap_pm25.mean()
    r_se = pearsonr(dc.values, gc.values)[0]
    lv = dec.groupby(dec.time.map(lambda t: pd.to_datetime(t).year)).pm25_q50.mean(); gl = ghap.groupby("year").ghap_pm25.mean()
    dpx = dec.groupby(["lat", "lon"]).pm25_q50.mean().reset_index(); gpx = ghap.groupby(["lat", "lon"]).ghap_pm25.mean().reset_index()
    _, idx = cKDTree(gpx[["lat", "lon"]].values).query(dpx[["lat", "lon"]].values); dpx["g"] = gpx.ghap_pm25.values[idx]
    r_sp = pearsonr(dpx.pm25_q50, dpx.g)[0]
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.9), constrained_layout=True)
    ax[0].plot(range(1, 13), dc.values, "o-", label="reconstruction"); ax[0].plot(range(1, 13), gc.values, "s-", label="GHAP")
    ax[0].set_title(f"(a) seasonal climatology (r={r_se:.2f})", fontsize=8.6); ax[0].set_xlabel("month"); ax[0].set_ylabel("PM$_{2.5}$ (µg m$^{-3}$)", fontsize=8); ax[0].legend(fontsize=7); ax[0].grid(alpha=.25)
    yrs = list(lv.index); ax[1].plot(yrs, lv.values, "o-", color="#08519C", label="reconstruction"); ax[1].plot(list(gl.index), gl.values, "^-", color="#CB181D", label="GHAP")
    ax[1].scatter([2019], [24.52], marker="*", s=140, color="k", label="KOALA 2019"); ax[1].set_title("(b) area level (below floor)", fontsize=8.6); ax[1].set_xticks(yrs); ax[1].legend(fontsize=7); ax[1].grid(alpha=.25)
    ax[2].scatter(dpx.g, dpx.pm25_q50, s=8, alpha=.5, color="#6A51A3"); ax[2].set_title(f"(c) per-pixel (r={r_sp:.2f})", fontsize=8.6); ax[2].set_xlabel("GHAP"); ax[2].set_ylabel("reconstruction"); ax[2].grid(alpha=.25)
    fig.suptitle("Independent GHAP corroboration: seasonal r=0.91; area level agrees, below KOALA floor; fine pattern sign-only", fontsize=9.2)
    pf.save(fig, "F10_validation")


# ════════════════════════ F11 — exposure & burden ══════════════════════════
def f11_burden():
    import importlib
    hb = importlib.import_module("src.stage1_satml.decomp.health_burden")
    Z, lats, lons = pf.field(YEAR, "additive")
    P = np.load(DEC / "population_kandy.npz"); pop = P["pop"].astype(float); pop *= (hb.BBOX_POP / pop.sum())
    base = pop * hb.CDR * hb.F_NCD_LRI; deaths = hb.af(Z) * base
    csv = pd.read_csv(DEC / "health_burden.csv").iloc[0]
    fig = plt.figure(figsize=(7.2, 2.8), constrained_layout=True); gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 1, .85])
    a0 = fig.add_subplot(gs[0, 0]); im = _draw(a0, deaths, lats, lons, pf.INFERNO, show_terrain=False, vmin=0, vmax=np.percentile(deaths, 99))
    a0.set_title(f"(a) attributable deaths/yr per pixel\ntotal {csv.attributable_deaths_per_yr:.0f} [{csv.ci_low:.0f}–{csv.ci_high:.0f}]", fontsize=8.6); a0.set_xticks([]); a0.set_yticks([])
    fig.colorbar(im, ax=a0, shrink=.8, label="deaths yr$^{-1}$")
    a1 = fig.add_subplot(gs[0, 1]); pm = np.linspace(0, 60, 200); a1.plot(pm, hb.gemm_rr(pm), color="#B2182B", lw=2)
    a1.axvline(csv.dynamic_exposure, color="#08519C", ls="--", label=f"Kandy exp. {csv.dynamic_exposure:.0f}"); a1.axvline(5, color="green", ls=":", label="WHO AQG 5")
    a1.set_xlabel("PM$_{2.5}$ (µg m$^{-3}$)"); a1.set_ylabel("relative risk"); a1.set_title("(b) GEMM exposure–response"); a1.legend(fontsize=7.5); a1.grid(alpha=.25)
    a2 = fig.add_subplot(gs[0, 2]); a2.axis("off")
    txt = (f"KANDY PM$_{{2.5}}$ BURDEN ({YEAR})\n\nattributable deaths/yr\n  {csv.attributable_deaths_per_yr:.0f} [{csv.ci_low:.0f}–{csv.ci_high:.0f}]\n"
           f"  = {csv.attributable_fraction_pct:.0f}% NCD+LRI\n\navoidable if WHO AQG met\n  {csv.avoidable_vs_WHO_AQG5:.0f}/yr\n\n"
           f"actionable share\n  ~25% local · ~75% regional")
    a2.text(0, .95, txt, va="top", fontsize=9, family="monospace", bbox=dict(boxstyle="round,pad=.5", fc="#FFF6EC", ec="#B2182B"))
    fig.suptitle("Health burden — GEMM NCD+LRI × population (screening estimate); only ~25% is locally actionable", fontsize=10.2)
    pf.save(fig, "F11_burden")


# ════════════════════════ F12 — uncertainty ════════════════════════════════
def f12_uq():
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{YEAR}{pf.ADD}.parquet",
                        columns=["lat", "lon", "pm25_q05", "pm25_q95", "pm25_blo", "pm25_bhi"])
    d["piw"] = (d.pm25_q95 - d.pm25_q05) + (d.pm25_bhi - d.pm25_blo)
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    W = d.groupby(["lat", "lon"]).piw.mean().unstack("lon").reindex(index=lats, columns=lons).values
    conf = float((d.pm25_q95 - d.pm25_q05).mean()); bg = float((d.pm25_bhi - d.pm25_blo).mean())
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 3.2), width_ratios=[1.3, 1], constrained_layout=True)
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    im = ax[0].imshow(zoom(W, 8, order=1), origin="lower", extent=ext, cmap="magma", aspect="auto", interpolation="bilinear")
    elev, ela, elo = _elev(); ax[0].contour(elo, ela, elev, levels=range(500, 1300, 150), colors="w", linewidths=.3, alpha=.3)
         # city centre only
    _scale_bar(ax[0], lats, lons); _north_arrow(ax[0], lats, lons)
    ax[0].set_title("(a) per-pixel 90% PI width\n(widest on unconstrained ridge/edge)", fontsize=8.8); ax[0].set_xticks([]); ax[0].set_yticks([])
    fig.colorbar(im, ax=ax[0], shrink=.82, label="90% PI width (µg m$^{-3}$)")
    ax[1].bar(["temporal\nconformal", "background\nbracket"], [conf, bg], color=["#3690C0", "#E6550D"])
    ax[1].set_ylabel("mean width (µg m$^{-3}$)"); ax[1].set_title("(b) interval components"); ax[1].grid(axis="y", alpha=.25)
    fig.suptitle("Uncertainty: calibrated temporal conformal interval + propagated background bracket", fontsize=10.2)
    pf.save(fig, "F12_uncertainty")


# ════════ F13 — average vs stagnation episode + emission intensity ⭐ ════════
def f13_episode():
    """The headline AVERAGE is moderate and fairly flat, but the SAME terrain + emissions,
    under a calm low-BLH inter-monsoon night with evening-rush emissions, concentrate
    pollution sharply in the Hantana-enclosed urban core — the episodic spike that
    time-averaging hides. Validated-flat headline and physical scenario shown side by side."""
    from matplotlib.colors import LightSource
    se = pf.load_seasonal_episodic()
    epi = se["episode"]; la16 = se["lats16"]; lo16 = se["lons16"]
    add, lats, lons = pf.field(YEAR, "additive")            # validated headline (basin ~21)
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    Uw, Vw, wla, wlo = pf.seas_wind(se, "MAM")             # inter-monsoon stagnation flow
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.9), constrained_layout=True)

    # (a) validated average headline
    im0 = _draw(ax[0], add, lats, lons, pf.PM_CMAP, show_marks=False, norm=pf.pm_norm())
    pf.quiver(ax[0], Uw, Vw, wla, wlo, step=9, color="white", lw=0.5)

    ax[0].set_title(f"(a) validated annual average\nbasin {np.nanmean(add):.0f} µg m$^{{-3}}$ (fairly flat)", fontsize=8.4)
    pf.pm_cbar(fig, im0, ax[0], 0.75)

    # (b) stagnation episode — own extended scale so the core spike is read, not clipped
    enorm = pf.pm_norm(vmin=15, vmax=100, gamma=1.5)
    im1 = _draw(ax[1], epi, la16, lo16, pf.PM_CMAP, show_marks=False, norm=enorm)
    pf.emission_contours(ax[1], lw=0.6)
    pf.quiver(ax[1], Uw, Vw, wla, wlo, step=9, color="white", lw=0.5)

    # open ≠ clean: the through-flow corridor ventilates; the down-valley low end is a drainage SINK
    # spread the labels (core→bottom, corridor→left, sink→right) so they don't collide with each other/title
    ax[1].annotate("traffic-hub core", (80.6337, 7.2906), (80.610, 7.246), fontsize=5.8,
                   color="k", ha="center", arrowprops=dict(arrowstyle="->", color="k", lw=0.55))
    ax[1].annotate("vented\ncorridor\n(40%)", (80.588, 7.322), (80.576, 7.285), fontsize=5.4,
                   color="#08306b", ha="center", va="center", arrowprops=dict(arrowstyle="->", color="#08306b", lw=0.55))
    ax[1].annotate("drainage\nsink (100%)", (80.632, 7.335), (80.667, 7.312), fontsize=5.4,
                   color="#7a0177", ha="center", va="center", arrowprops=dict(arrowstyle="->", color="#7a0177", lw=0.55))
    ax[1].set_title(f"(b) stagnation episode (scenario)\ncore {np.nanmax(epi):.0f} · basin {np.nanmean(epi):.0f} µg m$^{{-3}}$", fontsize=8.4)
    fig.colorbar(im1, ax=ax[1], extend="max", ticks=[25, 50, 75, 100], shrink=0.75, label="PM$_{2.5}$ (µg m$^{-3}$)")

    # (c) emission intensity (where spikes originate) — congestion-AADT × EF, inferno
    sd = np.load(DEC / "S_traffic_kandy.npz"); E = gaussian_filter(sd["E_fine"], 2)
    eext = [sd["fine_lon"].min(), sd["fine_lon"].max(), sd["fine_lat"].min(), sd["fine_lat"].max()]
    im2 = ax[2].imshow(E, origin="lower", extent=eext, cmap=pf.INFERNO, aspect="auto",
                       norm=__import__("matplotlib").colors.PowerNorm(0.5), interpolation="bilinear")
    elev, ela, elo = _elev(); ax[2].contour(elo, ela, elev, levels=range(500, 1300, 200), colors="w", linewidths=.3, alpha=.35)

    ax[2].set_xlim(lons.min(), lons.max()); ax[2].set_ylim(lats.min(), lats.max())
    ax[2].set_title("(c) traffic-emission intensity\n(core ≈ 15× corridor)", fontsize=8.4)
    fig.colorbar(im2, ax=ax[2], shrink=0.75, label="rel. emission")
    for a in ax:
        a.set_xticks([]); a.set_yticks([])
    fig.suptitle("Emission ≠ concentration: a 15× traffic-hub emission gradient → only ~1.45× core at rush, "
                 "~1.1× annually (dispersion + 75% regional background)", fontsize=8.8)
    pf.save(fig, "F13_episode")


ALL = {"f1": f1_studyarea, "f2": f2_schematic, "f3": f3_decomposition, "f4": f4_mechanism,
       "f5": f5_emission, "f6": f6_seasonal, "f7": f7_diurnal, "f8": f8_regimes,
       "f9": f9_scales, "f10": f10_validation, "f11": f11_burden, "f12": f12_uq,
       "f13": f13_episode}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("--figs", default="all"); a = ap.parse_args()
    keys = list(ALL) if a.figs == "all" else a.figs.split(",")
    for k in keys:
        try:
            ALL[k.strip()]()
        except Exception as e:
            import traceback; print(f"FAIL {k}: {e}"); traceback.print_exc()
    print(f"\n→ {pf.PAPER_OUT}")


if __name__ == "__main__":
    main()
