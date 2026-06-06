"""
figure_suite.py — the FINAL-MODEL monograph figure suite (2026-06-04, cividis).

One driver for the full publication suite, area-anchored (β≡1) headline = the
SMOOTH three-factor field; the four-factor transport overlay appears only as the
labelled scenario in Fig 4.2. Perceptually-uniform CIVIDIS for concentration,
RdBu for the signed confinement z-score, terrain for relief. WHO Interim-Target
ticks on every concentration bar. All output → results/figures/monograph/.

Figures:
  fig21_studyarea   2.1  shaded relief + sensors/ridge/corridor + regional inset
  fig22_availability 2.2 data-availability Gantt (2018-2026) + processing flow
  fig32_factors     3.2  S_emit | c(x,y) signed | M nocturnal | assembled PM (+BLH inset)
  fig41_versions    4.1  ConvCNP v15 / v16a / decomposition (shared scale)
  fig42_scenario    4.2  smooth headline vs four-factor scenario + e(t) inset
  fig43_valleyscreen 4.3 world map of 300+ screened valleys by station relief + relief ECDF
  fig51_annual_seasonal 5.1 annual + 4 seasonal (two rows: shared + per-season scale)
  fig52_diurnal     5.2  diurnal cycle (+PI band) + day vs night maps
  fig53_interannual 5.3  basin AREA mean 2019-2023 +PI vs VanD, KOALA-floor, Hantana-ridge
  fig54_ghap        5.4  GHAP cross-check (seasonal r / area-level / per-pixel)
  fig55_uq          5.5  per-pixel 90% PI-width map
External (run separately): figure_architecture (3.1), figure_area_anchor (X1), exposure_weighting (X2).
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
from src.stage1_satml.decomp.figures_pub import (_draw, _scale_bar, _north_arrow,
                                                 _elev, LANDMARKS)
from src.stage1_satml.decomp.emission_profile import e_at

DEC = REPO / "data" / "processed" / "decomp"
STG = REPO / "data" / "processed" / "stage1_v3"
PIN = REPO / "data" / "processed" / "pinn_inputs"
PVAF = REPO / "data" / "processed" / "pvaf"
ZS = REPO / "data" / "processed" / "kandy_zero_shot"
from src.stage1_satml.decomp.pubfig import PUB_OUT as OUT  # publication style + folder
OUT.mkdir(parents=True, exist_ok=True)

CMAP = "cividis"
# Area-anchored field lives ~17-24 (core to ~30); scale 12-30 uses the cividis range
# while staying WHO-threshold-anchored (IT-3 15, IT-2 25). All of Kandy >> AQG 5.
VMN, VMX = 12, 30
WHO_T = [15, 20, 25, 30]
WHO_L = ["15 IT-3", "20", "25 IT-2", "30"]
CEN = (7.2906, 80.6337)
KOALA_FLOOR, HANTANA_RIDGE = 24.52, 10.5
KOALA_YEAR = 2019                      # KOALA 24.5 = Jan-Dec 2019 NIFS annual mean ONLY
# HEADLINE spatial field (2026-06-05): the additive Lenschow field
#   PM = B(t) + [T(t)-B(t)]*P_local   (GHAP-calibrated increment, basin mean preserved).
# The smooth T*S*M and the four-factor T*S*M*A are now ablation / scenario respectively.
HL = "_additive"


def _who_cbar(fig, im, ax, shrink=0.8):
    cb = fig.colorbar(im, ax=ax, label="PM₂.₅ (µg m⁻³)", extend="both", ticks=WHO_T, shrink=shrink)
    cb.ax.set_yticklabels(WHO_L, fontsize=7)
    return cb


def _annual_field(year, suffix=HL):
    """annual-mean q50 grid for a given field suffix ('' smooth, '_4factor', '_additive')."""
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}{suffix}.parquet",
                        columns=["lat", "lon", "pm25_q50"])
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    Z = d.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(
        index=lats, columns=lons).values
    return Z, lats, lons


def _headline_annual(year):
    return _annual_field(year, HL)


def _smooth_annual(year):
    return _annual_field(year, "")


# ─────────────────────────── 2.1 study area ────────────────────────────────
def fig21_studyarea():
    elev, ela, elo = _elev()
    fig, ax = plt.subplots(figsize=(7.2, 6.2), constrained_layout=True)
    im = ax.imshow(elev, origin="lower", extent=[elo.min(), elo.max(), ela.min(), ela.max()],
                   cmap="terrain", aspect="auto")
    cs = ax.contour(elo, ela, elev, levels=range(500, 1400, 150), colors="k",
                    linewidths=0.4, alpha=0.4)
    ax.clabel(cs, fontsize=6, fmt="%d")
    marks = {"Kandy city centre": (7.2906, 80.6337, "o", "yellow"),
             "NIFS / KOALA (floor)": (7.2839, 80.6322, "^", "cyan"),
             "FECT-Hantana (ridge)": (7.265, 80.625, "s", "magenta"),
             "FECT-Akurana (N, out-of-bbox)": (7.357, 80.618, "D", "white")}
    for nm, (la, lo, mk, c) in marks.items():
        ax.plot(lo, la, mk, mfc=c, mec="k", mew=0.9, ms=9, zorder=5,
                label=f"{nm}")
    ax.annotate("Hantana ridge", (80.628, 7.255), color="k", fontsize=8, fontweight="bold", rotation=-20)
    ax.annotate("Mahaweli corridor\n(WNW–NW vent)", (80.595, 7.31), color="navy", fontsize=7.5)
    _scale_bar(ax, ela[:, 0] if ela.ndim > 1 else ela, elo[0, :] if elo.ndim > 1 else elo)
    _north_arrow(ax, ela.ravel(), elo.ravel())
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    ax.set_title("Kandy basin — shaded relief, enclosing terrain, and ground sensors\n"
                 "(intermontane valley; KOALA on the floor, FECT-Hantana on the ridge)", fontsize=10)
    ax.legend(loc="lower right", fontsize=6.8, framealpha=0.9)
    cb = fig.colorbar(im, ax=ax, label="elevation (m a.s.l.)", shrink=0.8)
    fig.savefig(OUT / "fig21_studyarea.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote fig21_studyarea.png")


# ─────────────────────────── 2.2 data availability ─────────────────────────
def fig22_availability():
    # (start, end, name, role-colour)  — v3 window context
    OBS, FEAT, ANCH = "#2C7FB5", "#E08214", "#41AB5D"
    rows = [
        ("FECT PurpleAir (labels)", 2018.8, 2026.4, OBS),
        ("KOALA / Senarathna (floor anchor)", 2019.0, 2020.0, ANCH),
        ("Van Donkelaar V6 (level+source)", 1998.0, 2023.99, ANCH),
        ("GHAP (independent cross-check)", 2017.0, 2022.99, ANCH),
        ("GEOS-CF prior (feature)", 2019.0, 2026.0, FEAT),
        ("CAMS EAC4 (feature)", 2018.0, 2026.0, FEAT),
        ("ERA5 BLH/wind/T (feature)", 2018.0, 2026.0, FEAT),
        ("TROPOMI NO₂ (feature)", 2018.0, 2026.0, FEAT),
        ("MAIAC AOD (feature, 84% gap)", 2018.0, 2026.0, FEAT),
        ("VIIRS night-lights (source/pop)", 2018.0, 2024.0, OBS),
    ]
    fig, ax = plt.subplots(figsize=(9.5, 5.0), constrained_layout=True)
    for i, (nm, a, b, c) in enumerate(rows):
        ax.barh(i, b - a, left=a, color=c, alpha=0.85, height=0.6)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=8)
    ax.invert_yaxis(); ax.set_xlim(1998, 2026.6); ax.set_xlabel("year")
    ax.axvspan(2018.8, 2026.0, color="grey", alpha=0.08)
    ax.text(2022.4, len(rows) - 0.3, "Stage-A v3 hourly window", fontsize=7.5, color="grey", ha="center")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=OBS, label="observed"), Patch(color=FEAT, label="feature"),
                       Patch(color=ANCH, label="anchor / reference")], fontsize=8, loc="lower left")
    ax.set_title("Data availability and evidential role (Kandy reconstruction inputs)", fontsize=10)
    ax.grid(axis="x", alpha=0.25)
    fig.savefig(OUT / "fig22_availability.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote fig22_availability.png")


# ─────────────────────────── 3.2 the factors ───────────────────────────────
def fig32_factors():
    S = np.load(DEC / "S_emit_kandy.npz"); Semit = S["S_emit"]; lats = S["lats"]; lons = S["lons"]
    Mz = np.load(DEC / "M_confinement_kandy.npz"); c = Mz["c"]; kappa = float(Mz["kappa"]); Hr = float(Mz["H_ridge_m"])
    # nocturnal M: low BLH → high w
    g = pd.read_parquet(STG / "inference_grid_2023_s12451.parquet", columns=["datetime_utc", "blh_m"])
    t = pd.to_datetime(g.datetime_utc, utc=True).dt.tz_convert("Asia/Colombo")
    blh_night = g.blh_m[(t.dt.hour <= 5) | (t.dt.hour >= 22)].median()
    w = np.clip((Hr - blh_night) / Hr, 0, 1)
    Mnoc = 1 + kappa * w * c
    Zpm, _, _ = _headline_annual(2023)
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]

    fig, ax = plt.subplots(1, 4, figsize=(18, 4.8), constrained_layout=True)
    from scipy.ndimage import zoom
    # (a) S_emit
    im0 = ax[0].imshow(zoom(Semit, 8, order=3), origin="lower", extent=ext, cmap=CMAP,
                       aspect="auto", interpolation="bilinear")
    ax[0].set_title("(a) $S_{emit}(x,y)$ — satellite source\n(normalised, mean 1)", fontsize=9)
    fig.colorbar(im0, ax=ax[0], shrink=0.7)
    # (b) signed confinement c
    vlim = np.abs(c).max()
    im1 = ax[1].imshow(zoom(c, 8, order=3), origin="lower", extent=ext, cmap="RdBu_r",
                       vmin=-vlim, vmax=vlim, aspect="auto", interpolation="bilinear")
    ax[1].set_title("(b) $c(x,y)$ confinement z-score\n(+red trapped floor / −blue ridge)", fontsize=9)
    fig.colorbar(im1, ax=ax[1], shrink=0.7)
    # (c) nocturnal M
    im2 = ax[2].imshow(zoom(Mnoc, 8, order=3), origin="lower", extent=ext, cmap=CMAP,
                       aspect="auto", interpolation="bilinear")
    ax[2].set_title(f"(c) $M(x,y,t)$ nocturnal\n(BLH≈{blh_night:.0f} m, floor pooling)", fontsize=9)
    fig.colorbar(im2, ax=ax[2], shrink=0.7)
    # (d) assembled PM — additive Lenschow headline
    im3 = _draw(ax[3], Zpm, lats, lons, CMAP, vmin=VMN, vmax=VMX)
    ax[3].set_title("(d) assembled $\\widehat{PM}_{2.5}$\n(annual 2023, additive headline)", fontsize=9)
    _who_cbar(fig, im3, ax[3], shrink=0.7)
    for a in ax:
        a.plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.8, ms=5)
        a.set_xticks([]); a.set_yticks([])
    fig.suptitle("The decomposition factors over Kandy  —  additive headline "
                 "$PM=B(t)+[T(t)-B(t)]\\,P_{local}$, $P_{local}\\propto S_{emit}\\cdot M$ "
                 "(local increment only; background $B$ added uniformly)", fontsize=11.5)
    fig.savefig(OUT / "fig32_factors.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote fig32_factors.png")


# ─────────────────────────── 5.1 annual + seasonal ─────────────────────────
def fig51_annual_seasonal(year=2023):
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}{HL}.parquet",
                        columns=["time", "lat", "lon", "pm25_q50"])
    d["loct"] = pd.to_datetime(d.time, utc=True).dt.tz_convert("Asia/Colombo")
    d["seas"] = d.loct.dt.month % 12 // 3
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    names = {0: "DJF", 1: "MAM", 2: "JJA", 3: "SON"}

    def grid(sub):
        return sub.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(
            index=lats, columns=lons).values
    Zann = grid(d); Zs = [grid(d[d.seas == s]) for s in range(4)]

    fig, axes = plt.subplots(2, 5, figsize=(19, 8.0), constrained_layout=True)
    im = _draw(axes[0, 0], Zann, lats, lons, CMAP, vmin=VMN, vmax=VMX)
    axes[0, 0].set_title(f"ANNUAL  {np.nanmean(Zann):.1f}", fontsize=10)
    for s in range(4):
        _draw(axes[0, s + 1], Zs[s], lats, lons, CMAP, show_marks=False, vmin=VMN, vmax=VMX)
        axes[0, s + 1].set_title(f"{names[s]}  {np.nanmean(Zs[s]):.1f}", fontsize=10)
    # row 2: per-panel scale
    for col, (Z, ttl) in enumerate([(Zann, "ANNUAL")] + [(Zs[s], names[s]) for s in range(4)]):
        vmn, vmx = np.nanpercentile(Z, 4), np.nanpercentile(Z, 98)
        iml = _draw(axes[1, col], Z, lats, lons, CMAP, show_marks=False, vmin=vmn, vmax=vmx)
        axes[1, col].set_title(f"{ttl} (own {vmn:.0f}–{vmx:.0f})", fontsize=8.5)
        fig.colorbar(iml, ax=axes[1, col], shrink=0.7)
    for a in axes.ravel():
        a.plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.7, ms=4)
        a.set_xticks([]); a.set_yticks([])
    _who_cbar(fig, im, list(axes[0, :]), shrink=0.6)
    axes[0, 0].set_ylabel("shared WHO scale", fontsize=9)
    axes[1, 0].set_ylabel("per-panel scale", fontsize=9)
    fig.suptitle(f"Kandy reconstructed PM₂.₅ {year} — annual + seasonal (additive headline; area mean ~21; "
                 "MAM/DJF high, JJA monsoon low)", fontsize=12)
    fig.savefig(OUT / "fig51_annual_seasonal.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote fig51_annual_seasonal.png")


# ─────────────────────────── 5.2 diurnal + day/night ───────────────────────
def fig52_diurnal(year=2023):
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}{HL}.parquet",
                        columns=["time", "lat", "lon", "pm25_q50", "pm25_q05", "pm25_q95"])
    d["loct"] = pd.to_datetime(d.time, utc=True).dt.tz_convert("Asia/Colombo"); d["h"] = d.loct.dt.hour
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    diur = d.groupby("h")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean()

    fig = plt.figure(figsize=(15, 5.2), constrained_layout=True)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1, 1])
    axc = fig.add_subplot(gs[0, 0])
    axc.fill_between(diur.index, diur.pm25_q05, diur.pm25_q95, color="#FDE0A0", alpha=0.7, label="90% PI")
    axc.plot(diur.index, diur.pm25_q50, "o-", color="#B35806", lw=2, label="median")
    axc.axvline(7, color="grey", ls=":"); axc.axvline(14, color="grey", ls=":")
    axc.annotate("07 LT peak", (7, diur.pm25_q50.max()), fontsize=8)
    axc.annotate("14 LT trough", (14, diur.pm25_q50.min()), fontsize=8)
    axc.set_xlabel("local hour"); axc.set_ylabel("PM₂.₅ (µg m⁻³)"); axc.set_xticks(range(0, 24, 3))
    axc.set_title("(a) basin-mean diurnal cycle"); axc.legend(fontsize=8); axc.grid(alpha=0.25)

    def grid(sub):
        return sub.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(
            index=lats, columns=lons).values
    day = grid(d[(d.h >= 11) & (d.h <= 16)]); night = grid(d[(d.h <= 5) | (d.h >= 21)])
    for k, (Z, tag) in enumerate([(day, "(b) day 11–16 LT (well-mixed)"), (night, "(c) night 21–05 LT (trapped)")]):
        ax = fig.add_subplot(gs[0, k + 1])
        LA, LO = np.meshgrid(lats, lons, indexing="ij"); dd = np.hypot(LA - CEN[0], LO - CEN[1])
        ce = Z[dd <= np.percentile(dd, 20)].mean() / Z[dd >= np.percentile(dd, 80)].mean()
        im = _draw(ax, Z, lats, lons, CMAP, show_marks=False, vmin=VMN, vmax=VMX)
        ax.plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.8, ms=5)
        ax.set_title(f"{tag}\ncore/edge {ce:.2f}×", fontsize=9); ax.set_xticks([]); ax.set_yticks([])
        if k == 1:
            _who_cbar(fig, im, ax, shrink=0.8)
    fig.suptitle("Kandy diurnal cycle and day–night spatial contrast (additive headline, 2023)", fontsize=11)
    fig.savefig(OUT / "fig52_diurnal_daynight.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote fig52_diurnal_daynight.png")


# ─────────────────────────── 5.5 UQ PI width ───────────────────────────────
def fig55_uq(year=2023):
    # additive headline PI width = (q95-q05) [propagated T conformal] + background bracket
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}{HL}.parquet",
                        columns=["lat", "lon", "pm25_q05", "pm25_q95", "pm25_blo", "pm25_bhi"])
    d["piw"] = (d.pm25_q95 - d.pm25_q05) + (d.pm25_bhi - d.pm25_blo)
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    W = d.groupby(["lat", "lon"]).piw.mean().unstack("lon").reindex(index=lats, columns=lons).values
    fig, ax = plt.subplots(figsize=(6.8, 5.8), constrained_layout=True)
    from scipy.ndimage import zoom
    ext = [lons.min(), lons.max(), lats.min(), lats.max()]
    im = ax.imshow(zoom(W, 8, order=3), origin="lower", extent=ext, cmap="magma",
                   aspect="auto", interpolation="bilinear")
    elev, ela, elo = _elev()
    ax.contour(elo, ela, elev, levels=range(500, 1300, 150), colors="w", linewidths=0.3, alpha=0.3)
    for nm, (la, lo, mk) in LANDMARKS.items():
        ax.plot(lo, la, mk, mfc="white", mec="k", mew=0.8, ms=5)
    _scale_bar(ax, lats, lons); _north_arrow(ax, lats, lons)
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    ax.set_title(f"Per-pixel 90% PI width (additive headline + background bracket), {year}\n"
                 "(conformal T-interval scaled by the local increment + the [ridge…rural] background band)", fontsize=9.3)
    fig.colorbar(im, ax=ax, label="90% PI width (µg m⁻³)", shrink=0.85)
    fig.savefig(OUT / "fig55_uq.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote fig55_uq.png")


# ─────────────────────────── 5.3 inter-annual ──────────────────────────────
def fig53_interannual():
    rows = []
    for y in range(2019, 2024):
        d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}{HL}.parquet",
                            columns=["pm25_q50", "pm25_q05", "pm25_q95"])
        rows.append((y, d.pm25_q50.mean(), d.pm25_q05.mean(), d.pm25_q95.mean()))
    df = pd.DataFrame(rows, columns=["year", "q50", "q05", "q95"])
    vand = pd.read_csv(STG / "vandonkelaar_kandy_annual.csv")
    gh = pd.read_parquet(DEC / "ghap_kandy_monthly_2019_2022.parquet").groupby("year").ghap_pm25.mean()
    fig, ax = plt.subplots(figsize=(8.2, 5.0), constrained_layout=True)
    ax.fill_between(df.year, df.q05, df.q95, color="#C6DBEF", alpha=0.6, label="90% PI")
    ax.plot(df.year, df.q50, "o-", color="#08519C", lw=2.2, label="reconstruction (area mean)")
    vd = vand[vand.year.between(2019, 2023)]
    ax.plot(vd.year, vd.basin_mean, "s--", color="#41AB5D", label="Van Donkelaar (area)")
    ax.plot(gh.index, gh.values, "^--", color="#CB181D", label="GHAP (independent area)")
    # KOALA = single 2019 floor anchor (not re-measured each year) → marker at 2019 only
    ax.scatter([KOALA_YEAR], [KOALA_FLOOR], marker="*", s=170, color="k", zorder=6,
               label="KOALA 2019 floor (Senarathna 2024)")
    ax.axhline(HANTANA_RIDGE, color="tab:brown", ls=":", lw=1.2,
               label="FECT-Hantana ridge (2018–23 mean) 10.5")
    ax.annotate("2021 COVID low", (2021, df.loc[df.year == 2021, "q50"].iloc[0] - 1.5),
                fontsize=8, ha="center", color="#08519C")
    ax.set_xticks(range(2019, 2024)); ax.set_xlabel("year"); ax.set_ylabel("annual PM₂.₅ (µg m⁻³)")
    ax.set_title("Inter-annual basin AREA mean — two independent area products agree;\n"
                 "KOALA floor / Hantana ridge bracket the area mean (trend low-confidence)", fontsize=9.5)
    ax.legend(fontsize=7.5, ncol=2); ax.grid(alpha=0.25)
    fig.savefig(OUT / "fig53_interannual.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote fig53_interannual.png")


# ─────────────────────────── 5.4 GHAP cross-check ──────────────────────────
def fig54_ghap():
    from scipy.spatial import cKDTree
    from scipy.stats import pearsonr
    ghap = pd.read_parquet(DEC / "ghap_kandy_monthly_2019_2022.parquet")
    dec = []
    for y in range(2019, 2023):
        d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}.parquet",
                            columns=["time", "lat", "lon", "pm25_q50"])
        d["month"] = pd.to_datetime(d.time).dt.month; dec.append(d)
    dec = pd.concat(dec, ignore_index=True)
    dc = dec.groupby("month").pm25_q50.mean(); gc = ghap.groupby("month").ghap_pm25.mean()
    r_se = pearsonr(dc.values, gc.values)[0]
    dpx = dec.groupby(["lat", "lon"]).pm25_q50.mean().reset_index()
    gpx = ghap.groupby(["lat", "lon"]).ghap_pm25.mean().reset_index()
    _, idx = cKDTree(gpx[["lat", "lon"]].values).query(dpx[["lat", "lon"]].values)
    dpx["ghap"] = gpx.ghap_pm25.values[idx]; r_sp = pearsonr(dpx.pm25_q50, dpx.ghap)[0]
    lv = dec.groupby(dec.time.map(lambda t: pd.to_datetime(t).year)).pm25_q50.mean()
    gl = ghap.groupby("year").ghap_pm25.mean()

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4), constrained_layout=True)
    ax[0].plot(range(1, 13), dc.values, "o-", label="reconstruction"); ax[0].plot(range(1, 13), gc.values, "s-", label="GHAP")
    ax[0].set_title(f"(a) seasonal climatology  r={r_se:.2f}"); ax[0].set_xlabel("month")
    ax[0].set_ylabel("PM₂.₅ (µg m⁻³)"); ax[0].legend(fontsize=8); ax[0].grid(alpha=0.25)
    yrs = list(lv.index)
    ax[1].plot(yrs, lv.values, "o-", color="#08519C", label="reconstruction (area)")
    ax[1].plot(list(gl.index), gl.values, "^-", color="#CB181D", label="GHAP (area)")
    ax[1].scatter([KOALA_YEAR], [KOALA_FLOOR], marker="*", s=150, color="k", zorder=6,
                  label="KOALA 2019 floor")
    ax[1].set_title("(b) area level — two products agree, below floor"); ax[1].set_xlabel("year")
    ax[1].set_ylabel("µg/m³"); ax[1].set_xticks(yrs); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.25)
    ax[2].scatter(dpx.ghap, dpx.pm25_q50, s=10, alpha=0.5, color="#6A51A3")
    ax[2].set_title(f"(c) per-pixel pattern  r={r_sp:.2f} (both near-smooth)")
    ax[2].set_xlabel("GHAP (µg/m³)"); ax[2].set_ylabel("reconstruction (µg/m³)"); ax[2].grid(alpha=0.25)
    fig.suptitle("Independent cross-check against GHAP (2019–2022; computed on the magnitude-independent "
                 "field): seasonal phase corroborated, area level corroborated, fine pattern sign-only\n"
                 "(the additive headline shares this phase + placement; its fine magnitude is GHAP-calibrated)",
                 fontsize=9.8)
    fig.savefig(OUT / "fig54_ghap.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote fig54_ghap.png")


# ─────────────────────────── 4.2 headline vs scenario ──────────────────────
def fig42_scenario(year=2023):
    hl, lats, lons = _headline_annual(year)          # additive Lenschow headline
    f4 = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}_4factor.parquet",
                         columns=["lat", "lon", "pm25_q50"])
    Z4 = f4.groupby(["lat", "lon"]).pm25_q50.mean().unstack("lon").reindex(index=lats, columns=lons).values
    LA, LO = np.meshgrid(lats, lons, indexing="ij"); dd = np.hypot(LA - CEN[0], LO - CEN[1])
    def ce(Z): return Z[dd <= np.percentile(dd, 20)].mean() / Z[dd >= np.percentile(dd, 80)].mean()

    fig, ax = plt.subplots(1, 3, figsize=(16.5, 5.2), constrained_layout=True,
                           gridspec_kw=dict(width_ratios=[1, 1, 0.85]))
    im = _draw(ax[0], hl, lats, lons, CMAP, vmin=VMN, vmax=VMX)
    ax[0].set_title(f"(a) HEADLINE: additive $B+[T-B]\\,P_{{local}}$\nbasin {hl.mean():.1f}, "
                    f"core/edge {ce(hl):.2f}× (GHAP-calibrated)", fontsize=9)
    _draw(ax[1], Z4, lats, lons, CMAP, vmin=VMN, vmax=VMX)
    ax[1].set_title(f"(b) SCENARIO: multiplicative + $A_{{transport}}$\nbasin {Z4.mean():.1f}, core/edge {ce(Z4):.2f}×", fontsize=9)
    for a in ax[:2]:
        a.plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.8, ms=5); a.set_xticks([]); a.set_yticks([])
    _who_cbar(fig, im, list(ax[:2]), shrink=0.7)
    # (c) e(t) emission timing inset
    hrs = np.arange(24); ev = np.array([e_at(h) for h in hrs])
    ax[2].plot(hrs, ev, "o-", color="#B35806", lw=2)
    ax[2].axvspan(6, 9, color="grey", alpha=0.12); ax[2].axvspan(17, 19, color="grey", alpha=0.12)
    ax[2].annotate("07 rush", (7, ev[7]), fontsize=8); ax[2].annotate("18 rush", (18, ev[18]), fontsize=8)
    ax[2].set_xlabel("local hour"); ax[2].set_ylabel("emission weight $e(t)$ (norm)")
    ax[2].set_title("(c) $e(t)$ — bimodal road-traffic\n(~90% vehicular; EDGAR profile)", fontsize=9)
    ax[2].set_xticks(range(0, 24, 6)); ax[2].grid(alpha=0.25)
    fig.suptitle("Additive headline vs multiplicative transport scenario: both lift the urban core, the "
                 "additive increment is GHAP-calibrated; amplitude a prior (basin mean preserved)", fontsize=10.5)
    fig.savefig(OUT / "fig42_headline_scenario.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote fig42_headline_scenario.png")


# ─────────────────────────── 4.1 version progression ───────────────────────
def fig41_versions():
    def zs_annual(tag):
        d = pd.read_parquet(ZS / f"kandy_predictions_20240101_0000_n8784_{tag}mondrian.parquet",
                            columns=["lat", "lon", "pm25_pred"])
        lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
        Z = d.groupby(["lat", "lon"]).pm25_pred.mean().unstack("lon").reindex(index=lats, columns=lons).values
        return np.clip(Z, 0, None), lats, lons
    panels = []
    for tag, ttl in [("v15", "(a) ConvCNP v15 (N=10)\nspatial inversion"),
                     ("v16a", "(b) ConvCNP v16a (N=3)\ncore recovered, inflated")]:
        try:
            panels.append((*zs_annual(tag), ttl))
        except Exception:
            pass
    dec, dlats, dlons = _headline_annual(2023)
    panels.append((dec, dlats, dlons, f"(c) decomposition (production, additive)\narea mean {dec.mean():.1f}"))
    fig, ax = plt.subplots(1, len(panels), figsize=(5.4 * len(panels), 5.2), constrained_layout=True)
    im = None
    for a, (Z, la, lo, ttl) in zip(np.atleast_1d(ax), panels):
        im = _draw(a, Z, la, lo, CMAP, show_marks=False, vmin=VMN, vmax=VMX)
        a.plot(CEN[1], CEN[0], "o", mfc="white", mec="k", mew=0.8, ms=5)
        a.set_title(ttl, fontsize=9); a.set_xticks([]); a.set_yticks([])
    _who_cbar(fig, im, list(np.atleast_1d(ax)), shrink=0.7)
    fig.suptitle("Why decomposition: cross-city ConvCNP transfer inverts/inflates Kandy's pattern; "
                 "the physics decomposition is stable and area-anchored", fontsize=11)
    fig.savefig(OUT / "fig41_versions.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote fig41_versions.png")


# ─────────────────────────── 4.3 valley screen (cartopy) ───────────────────
def fig43_valleyscreen():
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    cn = pd.read_csv(PVAF / "cnemc_relief_screen_v3.csv")
    oa = pd.read_csv(PVAF / "openaq_relief_screen_v3.csv")
    cn_relief = cn["elev_p10_90"].clip(0, 400)
    oa_relief = oa["dz_p10_90"].clip(0, 400)
    fig = plt.figure(figsize=(15, 5.6), constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.9, 1])
    ax = fig.add_subplot(gs[0, 0], projection=ccrs.Robinson())
    ax.add_feature(cfeature.LAND, facecolor="#EFEFE7"); ax.add_feature(cfeature.OCEAN, facecolor="#DCE9F2")
    ax.add_feature(cfeature.COASTLINE, lw=0.3); ax.set_global()
    sc = ax.scatter(cn.lon, cn.lat, c=cn_relief, s=14, cmap="viridis", vmin=0, vmax=300,
                    transform=ccrs.PlateCarree(), edgecolor="k", lw=0.2, label="CNEMC (249)")
    ax.scatter(oa.lon, oa.lat, c=oa_relief, s=26, cmap="viridis", vmin=0, vmax=300, marker="^",
               transform=ccrs.PlateCarree(), edgecolor="k", lw=0.3, label="OpenAQ (45)")
    ax.scatter([80.63], [7.29], c="red", s=120, marker="*", transform=ccrs.PlateCarree(),
               edgecolor="k", zorder=6, label="Kandy (target)")
    fig.colorbar(sc, ax=ax, label="station relief, δz p10–p90 (m)", shrink=0.6)
    ax.set_title("(a) 300+ screened monitored valleys — coloured by station relief\n"
                 "(monitors sited on the floor everywhere; little vertical sampling)", fontsize=9.5)
    ax.legend(loc="lower left", fontsize=7)
    # (b) ECDF of station relief — floor-clustering
    axb = fig.add_subplot(gs[0, 1])
    allr = np.sort(np.concatenate([cn_relief.values, oa_relief.values]))
    axb.plot(allr, np.linspace(0, 1, len(allr)), "-", color="#6A51A3", lw=2)
    axb.axvline(100, color="grey", ls=":");
    frac = (allr < 100).mean()
    axb.annotate(f"{frac*100:.0f}% of valleys\n< 100 m station relief", (110, 0.4), fontsize=8.5)
    axb.set_xlabel("station relief δz p10–p90 (m)"); axb.set_ylabel("cumulative fraction of valleys")
    axb.set_title("(b) floor-clustering: the gradient is\nnot sampled by public networks", fontsize=9.5)
    axb.grid(alpha=0.25); axb.set_xlim(0, 400)
    fig.suptitle("Why valley confinement cannot be validated from public data — an exhaustive 300+ valley screen", fontsize=11)
    fig.savefig(OUT / "fig43_valleyscreen.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("wrote fig43_valleyscreen.png")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for fn in (fig21_studyarea, fig22_availability, fig32_factors, fig41_versions,
               fig42_scenario, fig43_valleyscreen, fig51_annual_seasonal, fig52_diurnal,
               fig53_interannual, fig54_ghap, fig55_uq):
        try:
            fn()
        except Exception as e:
            import traceback; print(f"FAIL {fn.__name__}: {e}"); traceback.print_exc()
    print(f"\nSuite → {OUT}")


if __name__ == "__main__":
    main()
