"""xichang_paper_figures.py — the F1–F13 publication suite for XICHANG, the
city-parameterised fork of src/stage1_satml/decomp/paper_figures.py (Kandy v2).

Reads the Xichang production products (scripts/xichang_prod.py → data/processed/
decomp_xichang/) — the SAME additive v2 model, Xichang terrain/met/satellite/traffic.
The Kandy figure code is untouched. Key change vs Kandy: F10 validates against the
held-out CNEMC ground network (real validation), since Xichang HAS ground truth.

Run:  python scripts/xichang_paper_figures.py --figs all   (or f3,f6,f10 …)
Out:  results/figures/xichang_paper_figures_v2/
"""
from __future__ import annotations
import argparse
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.ndimage import zoom, gaussian_filter

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
from src.stage1_satml.decomp import pubfig            # noqa: F401 (style)
from src.stage1_satml.decomp import paperfig as pf    # pm_norm, cmaps, square_heatmaps
from src.transfer_validation.citypack import get
from src.transfer_validation.anchors import station_stats
from src.transfer_validation.assembly import _terrain, _interp2
import xichang_prod as xp
from city_config import cfg

CITY = "xichang"
PIN = REPO / "data" / "processed" / "pinn_inputs"
DEC = REPO / "data" / "processed" / "decomp_xichang"
OUT = REPO / "results" / "figures" / "xichang_paper_figures_v2"
TZ = "Asia/Shanghai"
YEAR = 2023
CEN = (27.894, 102.264)
CFG = cfg("xichang")
PM = pf.PM_CMAP; INF = pf.INFERNO
ADD = "_additive_v2"


def _setup(city):
    global CITY, DEC, OUT, TZ, YEAR, CEN, CFG
    xp._setup(city)
    c = cfg(city); CITY = city; CFG = c; TZ = c["tz"]; CEN = c["cen"]
    YEAR = xp.HEADLINE
    DEC = REPO / "data" / "processed" / f"decomp_{city}"
    OUT = REPO / "results" / "figures" / f"{city}_paper_figures_v2"
    global _ELEV; _ELEV = None
    OUT.mkdir(parents=True, exist_ok=True)


def _anchor_pair():
    return xp.anchors()


def cp_xichang():
    return xp.cp_xichang()


OUT.mkdir(parents=True, exist_ok=True)


def _save(fig, name, pdf=False, square=True):
    if square:
        pf.square_heatmaps(fig)
    fig.savefig(OUT / f"{name}.png", dpi=350, bbox_inches="tight")
    if pdf:
        fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig); print(f"  wrote {name}.png")


# ── data helpers ────────────────────────────────────────────────────────────
def field(year=YEAR, kind="additive_v2", col="pm25_q50", hours=None, season=None):
    d = pd.read_parquet(DEC / f"{CITY}_decomp_predictions_{year}_{kind.strip('_')}.parquet"
                        if kind != "additive_v2" else
                        DEC / f"{CITY}_decomp_predictions_{year}_additive_v2.parquet",
                        columns=["time", "lat", "lon", col])
    d["loct"] = pd.to_datetime(d.time, utc=True).dt.tz_convert(TZ)
    if hours is not None:
        d = d[d.loct.dt.hour.isin(hours)]
    if season is not None:
        d = d[d.loct.dt.month % 12 // 3 == season]
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    # Physical floor: clip negative concentrations to 0 (a no-op for the gentle-
    # contrast cities; in high-contrast regimes like KTM, structuring a small
    # clean-season increment by a sharp unit-mean pattern can push low-emission
    # ridge pixels slightly negative — clamp for display, see report caveat).
    d[col] = d[col].clip(lower=0)
    Z = d.groupby(["lat", "lon"])[col].mean().unstack("lon").reindex(index=lats, columns=lons).values
    return Z, lats, lons


def _elev_grid():
    z = np.load(PIN / f"{CITY}_terrain_core.npz")
    lat = np.asarray(z["lat_grid"])[:, 0].astype(float)
    lon = np.asarray(z["lon_grid"])[0, :].astype(float)
    from build_station_terrain import resample_dem
    SRTM = REPO / "data" / "external" / CITY / "dem" / CFG["dem"]
    LO, LA = np.meshgrid(np.linspace(lon.min(), lon.max(), 200),
                         np.linspace(lat.min(), lat.max(), 200))
    elev = resample_dem(SRTM, LA.astype("f4"), LO.astype("f4"))[::-1]   # N-S flip (gotcha)
    return elev, LA[:, 0], LO[0, :]


_ELEV = None
def _elev_cached():
    global _ELEV
    if _ELEV is None:
        _ELEV = _elev_grid()
    return _ELEV


def _draw(ax, Z, lats, lons, cmap, norm=None, vmin=None, vmax=None, terrain=True):
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    im = ax.imshow(Z, origin="lower", extent=ext, aspect="auto", cmap=cmap,
                   norm=norm, vmin=vmin, vmax=vmax, interpolation="bilinear")
    if terrain:                       # elevation context on every heatmap
        elev, ela, elo = _elev_cached()
        ax.contour(elo, ela, elev, levels=range(1550, 2400, 200), colors="k",
                   linewidths=0.25, alpha=0.35)
        ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_xticks([]); ax.set_yticks([])
    return im


def _xnorm(Z):
    """Xichang PM scale — data-centred (the city runs hotter than Kandy's 13–30)."""
    v = Z[np.isfinite(Z)]
    return mcolors.Normalize(vmin=float(np.percentile(v, 3)), vmax=float(np.percentile(v, 99)))


def _wn_season_wind(season):
    """Season-mean WindNinja terrain wind on the library grid (for quivers)."""
    L = np.load(PIN / f"{CITY}_windninja_library.npz", allow_pickle=True)
    U, V, dirs, speeds = L["u"], L["v"], L["dirs"], L["speeds"]
    m = _met()
    m = m[m.loct.dt.month % 12 // 3 == season]
    frm = (np.degrees(np.arctan2(m.u10.mean(), m.v10.mean())) + 180) % 360
    di = int(np.argmin(np.abs((dirs - frm + 180) % 360 - 180)))
    ri = 0
    return U[di, 0, ri], V[di, 0, ri], L["lats"], L["lons"]


def _met(year=YEAR):
    from src.transfer_validation import drivers
    cp = replace(xp.cp_xichang(), score_years=(year,))
    w = drivers.era5_winds(cp); b = drivers.blh(cp)
    m = w.merge(b, on="datetime")
    m["loct"] = pd.to_datetime(m.datetime, utc=True).dt.tz_convert(TZ)
    return m[m.loct.dt.year == year]


def _quiver(ax, U, V, wla, wlo, step=4, color="white"):
    LO, LA = np.meshgrid(np.linspace(wlo[0], wlo[-1], U.shape[1]),
                         np.linspace(wla[0], wla[-1], U.shape[0]))
    ax.quiver(LO[::step, ::step], LA[::step, ::step], U[::step, ::step], V[::step, ::step],
              color=color, scale=45, width=0.004, alpha=0.9)


def _traffic_contours(ax):
    z = np.load(DEC / f"S_emit_{CITY}.npz")  # fallback extent
    t = np.load(REPO / "data" / "processed" / "decomp" / f"S_traffic_{CITY}.npz")
    S = t["S_traffic"]; la = t["lats"]; lo = t["lons"]
    ax.contour(np.linspace(lo[0], lo[-1], S.shape[1]), np.linspace(la[0], la[-1], S.shape[0]),
               S, levels=np.nanpercentile(S, [88, 95, 99]), colors="#39FF14",
               linewidths=0.6, alpha=0.9)


# ── stations / validation ───────────────────────────────────────────────────
def _stations_split():
    cp = cp_xichang(); a = set(int(x) for x in _anchor_pair())
    st = cp.stations().set_index("station_id")
    return st, a


def _pred_at_stations(year, kind="additive_v2"):
    """Predicted field interpolated to station coords (per month + per hour)."""
    d = pd.read_parquet(DEC / f"{CITY}_decomp_predictions_{year}_additive_v2.parquet",
                        columns=["time", "lat", "lon", "pm25_q50", "pm25_q05", "pm25_q95"])
    d["loct"] = pd.to_datetime(d.time, utc=True).dt.tz_convert(TZ)
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    st, _ = _stations_split()
    from scipy.interpolate import RegularGridInterpolator
    out = []
    for (t, loct), g in d.groupby(["time", "loct"]):
        Z = g.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(index=lats, columns=lons).values
        # bounded interpolation: stations outside the field box → NaN (dropped
        # downstream), NOT linearly extrapolated. Extrapolation on a far outlier
        # produces astronomical values that poison the network means (KTM SW
        # outlier hit −1.5e4). In-box stations are unaffected.
        f = RegularGridInterpolator((lats, lons), Z, bounds_error=False, fill_value=np.nan)
        v = f(np.column_stack([st.lat.to_numpy(), st.lon.to_numpy()]))
        out.append(pd.DataFrame({"loct": loct, "station_id": st.index, "pred": v}))
    return pd.concat(out, ignore_index=True)


def _obs(year):
    cp = cp_xichang()
    df = pd.read_parquet(cp.station_parquet(), columns=["datetime_utc", "station_id", "pm25"]).dropna(subset=["pm25"])
    df["loct"] = pd.to_datetime(df.datetime_utc, utc=True).dt.tz_convert(TZ)
    return df[df.loct.dt.year == year]


# ════════════════════════════════ FIGURES ══════════════════════════════════
def f1_studyarea():
    import matplotlib.patheffects as mpe
    from matplotlib.colors import LightSource
    elev, ela, elo = _elev_grid()
    ext = [elo.min(), elo.max(), ela.min(), ela.max()]
    ls = LightSource(azdeg=315, altdeg=45)
    fig, ax = plt.subplots(figsize=(7.0, 6.6))
    rgb = ls.shade(elev, cmap=plt.cm.terrain, blend_mode="soft", vert_exag=1.4, dx=90, dy=90)
    ax.imshow(rgb, origin="lower", extent=ext, aspect="auto", interpolation="bilinear")
    cs = ax.contour(elo, ela, elev, levels=range(1500, 2400, 150), colors="0.3", linewidths=0.3, alpha=0.5)
    ax.clabel(cs, fontsize=5, fmt="%d m")
    st, anc = _stations_split()
    for sid, r in st.iterrows():
        used = int(sid) in anc
        ax.plot(r.lon, r.lat, "^" if used else "o", ms=9 if used else 6,
                mfc="#D7263D" if used else "#1A9850", mec="k", mew=0.7, zorder=6,
                label=("anchor station" if used else "held-out station"))
    ax.plot(*CEN[::-1], marker="*", mfc="#FFD700", mec="k", mew=0.8, ms=16, zorder=7)
    ax.annotate(CFG["name"].split(" (")[0], CEN[::-1], (5, -10), textcoords="offset points", fontsize=9,
                fontweight="bold", color="#7a0010", path_effects=[mpe.withStroke(linewidth=1.6, foreground="white")])
    for txt, la, lo, typ in CFG["labels"]:
        col = "#08306b" if typ == "lake" else "0.1"
        ax.annotate(txt, (lo, la), fontsize=7.0, color=col, ha="center",
                    style="italic" if typ == "lake" else "normal",
                    fontweight="bold" if typ == "mtn" else "normal",
                    path_effects=[mpe.withStroke(linewidth=1.2, foreground="white")])
    h, l = ax.get_legend_handles_labels()
    seen = dict(zip(l, h)); ax.legend(seen.values(), seen.keys(), loc="lower right", fontsize=7, framealpha=0.92)
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    ax.set_title(f"{CFG['name']}: study domain, terrain and monitoring network", fontsize=9.5)
    try:
        import cartopy.crs as ccrs, cartopy.feature as cfeature
        from matplotlib.patches import Rectangle
        ix0, ix1, iy0, iy1, region = CFG["inset"]
        axi = fig.add_axes([0.13, 0.63, 0.2, 0.2], projection=ccrs.PlateCarree())
        axi.set_extent([ix0, ix1, iy0, iy1], ccrs.PlateCarree())
        axi.add_feature(cfeature.LAND, facecolor="#EAE6DA"); axi.add_feature(cfeature.COASTLINE, lw=0.4)
        axi.add_patch(Rectangle((CEN[1] - 0.25, CEN[0] - 0.25), 0.5, 0.5, ec="#D7263D",
                                fc="none", lw=1.3, transform=ccrs.PlateCarree()))
        axi.text(ix0 + (ix1 - ix0) * 0.1, iy1 - (iy1 - iy0) * 0.18, region, fontsize=6,
                 fontweight="bold", color="0.25", transform=ccrs.PlateCarree())
    except Exception as e:
        print(f"  (inset skipped: {e})")
    _save(fig, "F1_study_area", pdf=True, square=False)


def f3_decomposition():
    add, lats, lons = field(YEAR)
    B = pd.read_parquet(DEC / f"B_background_hourly_{YEAR}_{CITY}.parquet")["B"].mean()
    incr = add - B
    part = []
    for y in xp.YEARS:
        a = pd.read_parquet(DEC / f"{CITY}_decomp_predictions_{y}_additive_v2.parquet", columns=["pm25_q50"])
        bb = pd.read_parquet(DEC / f"B_background_hourly_{y}_{CITY}.parquet")["B"].mean()
        basin = float(a.pm25_q50.mean()); part.append((y, float(bb), basin - float(bb), basin))
    pdf = pd.DataFrame(part, columns=["year", "B", "I", "basin"]); pdf["loc%"] = pdf.I / pdf.basin * 100
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    fig, AX = plt.subplots(2, 2, figsize=(7.2, 6.9), constrained_layout=True)
    n = _xnorm(add)
    im = AX[0, 0].imshow(np.full_like(add, B), origin="lower", extent=ext, cmap=PM, norm=n, aspect="equal")
    AX[0, 0].set_title(f"(a) regional background $B$ ({B:.1f} µg m$^{{-3}}$)", fontsize=9); AX[0,0].set_xticks([]); AX[0,0].set_yticks([])
    fig.colorbar(im, ax=AX[0, 0], shrink=0.85, label="µg m$^{-3}$")
    imb = AX[0, 1].imshow(zoom(incr, 6, order=1), origin="lower", extent=ext, cmap=INF, aspect="equal",
                          vmin=0, vmax=np.percentile(incr, 99), interpolation="bilinear")
    AX[0, 1].set_title("(b) local increment $[T-B]\\,P_{local}$", fontsize=9); AX[0,1].set_xticks([]); AX[0,1].set_yticks([])
    fig.colorbar(imb, ax=AX[0, 1], shrink=0.85, label="µg m$^{-3}$")
    imc = _draw(AX[1, 0], add, lats, lons, PM, norm=n); AX[1,0].set_aspect("equal")
    AX[1, 0].set_title(f"(c) total $\\widehat{{PM}}_{{2.5}}$ ({add.mean():.1f} µg m$^{{-3}}$)", fontsize=9)
    fig.colorbar(imc, ax=AX[1, 0], shrink=0.85, label="µg m$^{-3}$")
    x = pdf.year.astype(str)
    AX[1, 1].bar(x, pdf.B, color="#6BAED6", label="regional / transboundary $B$")
    AX[1, 1].bar(x, pdf.I, bottom=pdf.B, color="#E6550D", label="local increment (actionable)")
    for i, r in pdf.iterrows():
        AX[1, 1].text(i, r.basin + 0.4, f"{r['loc%']:.0f}%", ha="center", fontsize=8, fontweight="bold")
    AX[1, 1].set_ylabel("annual PM$_{2.5}$ (µg m$^{-3}$)"); AX[1, 1].set_ylim(0, pdf.basin.max() * 1.25)
    AX[1, 1].set_title("(d) regional and local fractions by year", fontsize=8.6)
    AX[1, 1].legend(fontsize=7, loc="lower center")
    fig.suptitle(f"Additive decomposition, {CFG['name']}: regional background and local increment", fontsize=10.5)
    _save(fig, "F3_decomposition")


def f6_seasonal():
    names = {0: "DJF", 1: "MAM", 2: "JJA", 3: "SON"}
    Zann, lats, lons = field(YEAR)
    Zs = [field(YEAR, season=k)[0] for k in range(4)]
    n = _xnorm(np.concatenate([Zann.ravel()] + [z.ravel() for z in Zs]))
    fig, axes = plt.subplots(2, 5, figsize=(7.4, 3.6), constrained_layout=True)
    panels = [("ANNUAL", Zann)] + [(names[k], Zs[k]) for k in range(4)]
    for c, (ttl, Z) in enumerate(panels):
        im = _draw(axes[0, c], Z, lats, lons, PM, norm=n)
        sea = None if c == 0 else c - 1
        if sea is not None:
            U, V, wla, wlo = _wn_season_wind(sea); _quiver(axes[0, c], U, V, wla, wlo, step=5, color="#1A1A1A")
        axes[0, c].set_title(f"{ttl}  {np.nanmean(Z):.1f}", fontsize=9)
        an = Z - np.nanmean(Zann); vl = np.nanpercentile(np.abs([z - np.nanmean(Zann) for z in [Zann] + Zs]), 98)
        axes[1, c].imshow(zoom(an, 6, order=1), origin="lower", extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                          cmap="RdBu_r", vmin=-vl, vmax=vl, aspect="auto", interpolation="bilinear")
        axes[1, c].set_title(f"{ttl} − annual", fontsize=8.4); axes[1, c].set_xticks([]); axes[1, c].set_yticks([])
    fig.colorbar(im, ax=list(axes[0, :]), shrink=0.6, label="PM$_{2.5}$ (µg m$^{-3}$)")
    fig.suptitle(f"Annual and seasonal mean PM$_{{2.5}}$ with terrain-resolved wind field, {CFG['name']}", fontsize=9.8)
    _save(fig, "F6_seasonal")


def f7_diurnal():
    HRS = [3, 8, 11, 15, 20, 23]
    d = pd.read_parquet(DEC / f"{CITY}_decomp_predictions_{YEAR}_additive_v2.parquet", columns=["time", "lat", "lon", "pm25_q50"])
    d["h"] = pd.to_datetime(d.time, utc=True).dt.tz_convert(TZ).dt.hour
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    def grid(x): return x.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(index=lats, columns=lons).values
    diur = d.groupby("h").pm25_q50.mean(); n = _xnorm(grid(d))
    fig = plt.figure(figsize=(7.2, 6.6)); gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 0.8], hspace=0.2, wspace=0.06)
    im = None
    for k, h in enumerate(HRS):
        a = fig.add_subplot(gs[k // 3, k % 3]); im = _draw(a, grid(d[d.h == h]), lats, lons, PM, norm=n)
        a.set_title(f"{h:02d} LT  ({np.nanmean(grid(d[d.h==h])):.0f})", fontsize=8.4)
    fig.colorbar(im, ax=[fig.axes[i] for i in range(6)], shrink=0.85, label="PM$_{2.5}$ (µg m$^{-3}$)")
    axc = fig.add_subplot(gs[2, :]); axc.plot(diur.index, diur.values, "o-", color="#B35806", lw=2)
    axc.set_xlabel("local hour"); axc.set_ylabel("basin PM$_{2.5}$"); axc.set_xticks(range(0, 24, 2)); axc.grid(alpha=0.25)
    fig.suptitle(f"Diurnal evolution of PM$_{{2.5}}$, {CFG['name']}", fontsize=10)
    _save(fig, "F7_diurnal")


def f10_validation():
    """THE proof: predicted field vs HELD-OUT ground network (real ground truth)."""
    from scipy.stats import pearsonr, spearmanr
    st, anc = _stations_split()
    vault = [s for s in st.index if int(s) not in anc]
    pred_all, obs_all = [], []
    for y in xp.YEARS:
        p = _pred_at_stations(y); o = _obs(y)
        p["ym"] = p.loct.dt.to_period("M"); o["ym"] = o.loct.dt.to_period("M")
        pred_all.append(p.assign(year=y)); obs_all.append(o.assign(year=y))
    P = pd.concat(pred_all).dropna(subset=["pred"]); O = pd.concat(obs_all)
    P = P[P.station_id.isin(vault)]; O = O[O.station_id.isin(vault)]
    # (a) seasonal climatology (monthly city-mean)
    pm = P.assign(m=P.loct.dt.month).groupby("m").pred.mean()
    om = O.assign(m=O.loct.dt.month).groupby("m").pm25.mean()
    r_se = pearsonr(pm.reindex(om.index).values, om.values)[0]
    # (b) per-station spatial means
    ps = P.groupby("station_id").pred.mean(); os_ = O.groupby("station_id").pm25.mean()
    common = ps.index.intersection(os_.index)
    rho = spearmanr(ps[common], os_[common])[0]
    # (c) diurnal
    ph = P.assign(h=P.loct.dt.hour).groupby("h").pred.mean(); oh = O.assign(h=O.loct.dt.hour).groupby("h").pm25.mean()
    r_di = pearsonr(ph.reindex(oh.index).values, oh.values)[0]
    # level comparison: VanD-anchored vs sensor-anchored vs CNEMC obs
    vand = float(pd.read_csv(DEC / f"vandonkelaar_{CITY}_annual.csv").basin_mean.mean())
    model_lvl = float(P.pred.mean()); obs_lvl = float(O.pm25.mean())
    fig, ax = plt.subplots(1, 4, figsize=(8.4, 2.7), constrained_layout=True)
    ax[0].plot(om.index, om.values, "s-", color="#1f6f8b", label="network obs"); ax[0].plot(pm.index, pm.values, "o-", color="#B35806", label="model")
    ax[0].set_title(f"(a) seasonal (r={r_se:.2f})", fontsize=8.4); ax[0].set_xlabel("month"); ax[0].set_ylabel("PM$_{2.5}$"); ax[0].legend(fontsize=6.5); ax[0].grid(alpha=.25)
    lo = min(os_[common].min(), ps[common].min()) - 2; hi = max(os_[common].max(), ps[common].max()) + 2
    ax[1].plot([lo, hi], [lo, hi], "--", color="grey", lw=1); ax[1].scatter(os_[common], ps[common], s=55, c="#B35806", edgecolor="k")
    ax[1].set_xlim(lo, hi); ax[1].set_ylim(lo, hi); ax[1].set_title(f"(b) per-station (ρ={rho:.2f})", fontsize=8.4)
    ax[1].set_xlabel("network obs"); ax[1].set_ylabel("model"); ax[1].grid(alpha=.25)
    ax[2].plot(oh.index, oh.values, "s-", color="#1f6f8b", label="network"); ax[2].plot(ph.index, ph.values, "o-", color="#B35806", label="model")
    ax[2].set_title(f"(c) diurnal (r={r_di:.2f})", fontsize=8.4); ax[2].set_xlabel("local hour"); ax[2].set_xticks(range(0, 24, 6)); ax[2].grid(alpha=.25)
    ax[3].bar(["VanD\n(satellite)", "model\n(sensor-anch.)", "network\nobs"], [vand, model_lvl, obs_lvl],
              color=["#9E9AC8", "#B35806", "#1f6f8b"])
    for i, v in enumerate([vand, model_lvl, obs_lvl]):
        ax[3].text(i, v + 0.3, f"{v:.1f}", ha="center", fontsize=8, fontweight="bold")
    ax[3].set_ylabel("annual mean PM$_{2.5}$"); ax[3].set_title("(d) annual mean level", fontsize=8.4); ax[3].grid(axis="y", alpha=.25)
    fig.suptitle(f"Validation against the held-out monitoring network, {CFG['name']} ({len(vault)} stations)", fontsize=9.2)
    _save(fig, "F10_validation")


def f13_episode():
    add, lats, lons = field(YEAR)
    # the city's own peak recorded hour in the most recent year (held-out)
    eyr = max(xp.YEARS)
    d = pd.read_parquet(DEC / f"{CITY}_decomp_predictions_{eyr}_additive_v2.parquet", columns=["time", "lat", "lon", "pm25_q50"])
    peak_t = d.groupby("time").pm25_q50.mean().idxmax()
    ep = d[d.time == peak_t]
    ep_lab = pd.to_datetime(peak_t, utc=True).tz_convert(TZ).strftime("%Y-%m-%d %H:%M")
    elat = np.sort(ep.lat.unique()); elon = np.sort(ep.lon.unique())
    E = ep.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(index=elat, columns=elon).values
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.9), constrained_layout=True)
    im0 = _draw(ax[0], add, lats, lons, PM, norm=_xnorm(add)); ax[0].set_title(f"(a) annual mean\nbasin {np.nanmean(add):.0f} µg m$^{{-3}}$", fontsize=8.4)
    fig.colorbar(im0, ax=ax[0], shrink=0.75, label="µg m$^{-3}$")
    en = pf.pm_norm(vmin=15, vmax=max(90, float(np.nanmax(E))), gamma=1.4)
    im1 = ax[1].imshow(E, origin="lower", extent=[elon.min(), elon.max(), elat.min(), elat.max()], aspect="auto", cmap="turbo", norm=en, interpolation="bilinear")
    _traffic_contours(ax[1]); ax[1].set_xticks([]); ax[1].set_yticks([])
    ax[1].set_title(f"(b) peak episode, {ep_lab}\ncore {np.nanmax(E):.0f}, basin {np.nanmean(E):.0f}", fontsize=8.4)
    fig.colorbar(im1, ax=ax[1], extend="max", ticks=[25, 50, 75, 90], shrink=0.75, label="µg m$^{-3}$")
    t = np.load(REPO / "data" / "processed" / "decomp" / f"S_traffic_{CITY}.npz"); S = gaussian_filter(t["S_traffic"], 1)
    im2 = ax[2].imshow(S, origin="lower", extent=[t["lons"][0], t["lons"][-1], t["lats"][0], t["lats"][-1]],
                       cmap=INF, aspect="auto", norm=mcolors.PowerNorm(0.5), interpolation="bilinear")
    ax[2].set_xticks([]); ax[2].set_yticks([]); ax[2].set_title("(c) traffic-emission intensity", fontsize=8.4)
    fig.colorbar(im2, ax=ax[2], shrink=0.75, label="rel.")
    fig.suptitle(f"Annual mean, peak episode and emission source, {CFG['name']}", fontsize=9.2)
    _save(fig, "F13_episode")


def f2_schematic():
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    G = {"observed": "#2C7FB5", "learned": "#41AB5D", "physics": "#E08214"}
    fig, ax = plt.subplots(figsize=(7.0, 3.9)); ax.set_xlim(0, 100); ax.set_ylim(0, 56); ax.axis("off")
    def box(x, y, w, h, t, fc, fs=8):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4", fc=fc, ec="k", lw=0.8, alpha=0.9))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs)
    def arr(x0, y0, x1, y1):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=12, lw=0.9, color="0.3"))
    for t, y in [("Satellite\n(VanD V6)", 46), ("Reanalysis\n(ERA5 BLH/wind)", 34), ("CTM prior\n(GEOS-CF)", 22), ("DEM (SRTM)\n+ WindNinja", 10)]:
        box(2, y, 16, 9, t, "#EAF2F8", 6.6)
    for t, y, c in [("$T(t)$ temporal\n2 CNEMC sensors", 46, G["learned"]), ("$B(t)$ background\nrural VanD × CTM", 34, G["observed"]),
                    ("$S_{emit}$ + congestion\n(OSM centrality)", 22, G["observed"]), ("$M$ confinement /\n$A$ WindNinja", 10, G["physics"])]:
        box(26, y, 20, 9, t, c, 6.8)
    for _, y in [(0, 46), (0, 34), (0, 22), (0, 10)]:
        arr(18, y + 4.5, 26, y + 4.5)
    box(52, 26, 18, 14, "Additive\n$B+[T-B]P_{local}$", "#FCF3CF", 7.5)
    for y in (50.5, 38.5, 26.5, 14.5):
        arr(46, y, 52, 33)
    box(74, 30, 12, 9, "Conformal\nUQ", "#F5EEF8", 7.5); arr(70, 33, 74, 34.5)
    box(90, 24, 9, 16, "1 km ×\nhourly", "#E8F8F5", 7); arr(86, 34.5, 90, 32)
    ax.set_title(f"Model architecture with city-specific inputs, {CFG['name']}", fontsize=10.5)
    _save(fig, "F2_schematic", pdf=True, square=False)


def f4_mechanism():
    # Xichang is EVENING-peaked (residential heating, no morning commuter rush):
    # trapped = evening (18–21 LT, emissions + shallow BLH); ventilated = midday.
    EVE = [18, 19, 20, 21]; DAY = [11, 12, 13, 14, 15]
    Zm, lats, lons = field(YEAR, "4factor", hours=EVE); Zd, _, _ = field(YEAR, "4factor", hours=DAY)
    n = _xnorm(np.concatenate([Zm.ravel(), Zd.ravel()]))
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 3.3), constrained_layout=True)
    for a, (Z, sea, ttl) in zip(ax, [(Zm, 0, "(a) evening (18–21 LT)"),
                                     (Zd, 2, "(b) midday (11–15 LT)")]):
        im = _draw(a, Z, lats, lons, PM, norm=n); _traffic_contours(a)
        U, V, wla, wlo = _wn_season_wind(sea); _quiver(a, U, V, wla, wlo, step=5)
        a.set_title(ttl, fontsize=7.8); fig.colorbar(im, ax=a, shrink=0.8, label="µg m$^{-3}$")
    fig.suptitle(f"Evening accumulation and midday ventilation, {CFG['name']}", fontsize=9.0)
    _save(fig, "F4_mechanism")


def f5_emission():
    t = np.load(REPO / "data" / "processed" / "decomp" / f"S_traffic_{CITY}.npz")
    la, lo = t["lats"], t["lons"]; ext = [lo[0], lo[-1], la[0], la[-1]]
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.7), constrained_layout=True)
    for a, (Z, ttl) in zip(ax, [(t["betweenness"], "(a) betweenness\n(pass-by flow)"),
                                (t["closeness"], "(b) closeness\n(trip-ends)"),
                                (t["S_traffic"], "(c) congestion emission $S$\n(× COPERT EF)")]):
        im = a.imshow(zoom(Z, 2, order=1), origin="lower", extent=ext, cmap=INF, aspect="auto", interpolation="bilinear")
        a.set_title(ttl, fontsize=8.4); a.set_xticks([]); a.set_yticks([]); fig.colorbar(im, ax=a, shrink=0.75)
    fig.suptitle(f"Traffic emission surface (network-centrality AADT), {CFG['name']}", fontsize=9.6)
    _save(fig, "F5_emission")


def f8_regimes():
    d = pd.read_parquet(DEC / f"{CITY}_decomp_predictions_{YEAR}_additive_v2.parquet", columns=["time", "lat", "lon", "pm25_q50"])
    d["loct"] = pd.to_datetime(d.time, utc=True).dt.tz_convert(TZ); d["h"] = d.loct.dt.hour; d["s"] = d.loct.dt.month % 12 // 3
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    def grid(x): return x.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(index=lats, columns=lons).values
    regs = [("morning rush\n(trapped)", d[d.h.isin([6, 7, 8, 9])], 0), ("midday\n(ventilated)", d[d.h.isin([11, 12, 13, 14, 15])], 2),
            ("DJF winter\n(accumulation)", d[d.s == 0], 0), ("JJA summer\n(washout)", d[d.s == 2], 2)]
    n = _xnorm(grid(d))
    fig, ax = plt.subplots(1, 4, figsize=(7.4, 2.4), constrained_layout=True); im = None
    for a, (ttl, sub, sea) in zip(ax, regs):
        Z = grid(sub); im = _draw(a, Z, lats, lons, PM, norm=n); _traffic_contours(a)
        U, V, wla, wlo = _wn_season_wind(sea); _quiver(a, U, V, wla, wlo, step=6)
        a.set_title(f"{ttl}\nbasin {np.nanmean(Z):.1f}", fontsize=8.4)
    fig.colorbar(im, ax=list(ax), shrink=0.75, label="µg m$^{-3}$")
    fig.suptitle(f"Spatiotemporal response to meteorological conditions, {CFG['name']}", fontsize=9.6)
    _save(fig, "F8_circumstances")


def f9_scales():
    frames = []
    for y in xp.YEARS:
        a = pd.read_parquet(DEC / f"{CITY}_decomp_predictions_{y}_additive_v2.parquet", columns=["time", "pm25_q05", "pm25_q50", "pm25_q95"])
        frames.append(a.groupby("time")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean())
    bm = pd.concat(frames); bm.index = pd.to_datetime(bm.index, utc=True).tz_convert(TZ)
    bm["y"] = bm.index.year; bm["m"] = bm.index.month; bm["dow"] = bm.index.dayofweek; bm["h"] = bm.index.hour
    BAND = "#FCE3B4"; LN = "#B35806"
    fig, AX = plt.subplots(2, 2, figsize=(7.2, 5.0), constrained_layout=True)
    ya = bm.groupby("y")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean()
    AX[0, 0].fill_between(ya.index, ya.pm25_q05, ya.pm25_q95, color="#C6DBEF", alpha=.6); AX[0, 0].plot(ya.index, ya.pm25_q50, "o-", color="#08519C", lw=2)
    AX[0, 0].set_title("(a) inter-annual", fontsize=9.5); AX[0, 0].set_xticks(xp.YEARS)
    mo = bm.groupby("m")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean()
    AX[0, 1].fill_between(mo.index, mo.pm25_q05, mo.pm25_q95, color=BAND, alpha=.8); AX[0, 1].plot(mo.index, mo.pm25_q50, "o-", color=LN, lw=2)
    AX[0, 1].set_title("(b) seasonal", fontsize=9.5); AX[0, 1].set_xlabel("month")
    wk = bm.groupby("dow").pm25_q50; AX[1, 0].bar(range(7), wk.mean(), color=["#6BAED6"] * 5 + ["#FD8D3C", "#FD8D3C"])
    AX[1, 0].set_xticks(range(7)); AX[1, 0].set_xticklabels(["M", "T", "W", "T", "F", "S", "S"]); AX[1, 0].set_title("(c) weekly", fontsize=9.5)
    lo, hi = wk.mean().min(), wk.mean().max(); AX[1, 0].set_ylim(lo - (hi - lo) * 1.5 - .3, hi + (hi - lo) * 1.5 + .3)
    hr = bm.groupby("h")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean()
    AX[1, 1].fill_between(hr.index, hr.pm25_q05, hr.pm25_q95, color=BAND, alpha=.8); AX[1, 1].plot(hr.index, hr.pm25_q50, "o-", color=LN, lw=2)
    AX[1, 1].set_title("(d) diurnal", fontsize=9.5); AX[1, 1].set_xlabel("local hour"); AX[1, 1].set_xticks(range(0, 24, 6))
    for a in AX.ravel():
        a.set_ylabel("PM$_{2.5}$", fontsize=8); a.grid(alpha=.25); a.tick_params(labelsize=7.5)
    fig.suptitle(f"PM$_{{2.5}}$ variation across temporal scales, {CFG['name']}", fontsize=10.5)
    _save(fig, "F9_scales")


def f12_uq():
    d = pd.read_parquet(DEC / f"{CITY}_decomp_predictions_{YEAR}_additive_v2.parquet",
                        columns=["lat", "lon", "pm25_q05", "pm25_q95", "pm25_blo", "pm25_bhi"])
    d["piw"] = (d.pm25_q95 - d.pm25_q05) + (d.pm25_bhi - d.pm25_blo).abs()
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    W = d.groupby(["lat", "lon"]).piw.mean().unstack("lon").reindex(index=lats, columns=lons).values
    conf = float((d.pm25_q95 - d.pm25_q05).mean()); bg = float((d.pm25_bhi - d.pm25_blo).abs().mean())
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 3.2), width_ratios=[1.3, 1], constrained_layout=True)
    im = ax[0].imshow(zoom(W, 6, order=1), origin="lower", extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                      cmap="magma", aspect="auto", interpolation="bilinear")
    ax[0].set_xticks([]); ax[0].set_yticks([]); ax[0].set_title("(a) per-pixel 90% PI width", fontsize=8.8)
    fig.colorbar(im, ax=ax[0], shrink=.82, label="µg m$^{-3}$")
    ax[1].bar(["temporal\nconformal", "background\nbracket"], [conf, bg], color=["#3690C0", "#E6550D"])
    ax[1].set_ylabel("mean width (µg m$^{-3}$)"); ax[1].set_title("(b) interval components"); ax[1].grid(axis="y", alpha=.25)
    fig.suptitle(f"Uncertainty, {CFG['name']}: conformal interval and background bracket", fontsize=10.2)
    _save(fig, "F12_uncertainty")


def f11_burden():
    """Exposure screening (GEMM relative risk × dynamic exposure); WorldPop optional."""
    Z, lats, lons = field(YEAR)
    exp = float(np.nanmean(Z))
    def gemm_rr(pm, a=0.143, b=1.6, c=15.5, d=36.8):
        z = np.maximum(pm - 2.4, 0)
        return np.exp(a * np.log(1 + z / b) / (1 + np.exp(-(z - c) / d)))
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.9), constrained_layout=True)
    im = _draw(ax[0], gemm_rr(Z), lats, lons, INF); ax[0].set_title("(a) GEMM relative-risk field", fontsize=8.6)
    fig.colorbar(im, ax=ax[0], shrink=.8, label="RR")
    pm = np.linspace(0, 60, 200); ax[1].plot(pm, gemm_rr(pm), color="#B2182B", lw=2)
    ax[1].axvline(exp, color="#08519C", ls="--", label=f"Xichang exp. {exp:.0f}"); ax[1].axvline(5, color="green", ls=":", label="WHO AQG 5")
    ax[1].set_xlabel("PM$_{2.5}$ (µg m$^{-3}$)"); ax[1].set_ylabel("relative risk"); ax[1].set_title("(b) GEMM exposure–response"); ax[1].legend(fontsize=7.5); ax[1].grid(alpha=.25)
    fig.suptitle(f"Health exposure screening (GEMM relative risk), {CFG['name']}", fontsize=9.6)
    _save(fig, "F11_burden")


ALL = {"f1": f1_studyarea, "f2": f2_schematic, "f3": f3_decomposition, "f4": f4_mechanism,
       "f5": f5_emission, "f6": f6_seasonal, "f7": f7_diurnal, "f8": f8_regimes,
       "f9": f9_scales, "f10": f10_validation, "f11": f11_burden, "f12": f12_uq,
       "f13": f13_episode}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("--figs", default="all"); ap.add_argument("--city", default="xichang"); a = ap.parse_args()
    _setup(a.city)
    keys = list(ALL) if a.figs == "all" else a.figs.split(",")
    for k in keys:
        try:
            ALL[k.strip()]()
        except Exception as e:
            import traceback; print(f"FAIL {k}: {e}"); traceback.print_exc()
    print(f"\n→ {OUT}")


if __name__ == "__main__":
    main()
