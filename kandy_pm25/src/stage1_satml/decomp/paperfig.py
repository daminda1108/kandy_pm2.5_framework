"""
paperfig.py — shared helpers for the publication paper-figure suite (2026-06-05).
Plan: docs/paper_figures_plan_2026-06-05.md.

Provides: the universal turbo PM scale + WHO colourbar; WindNinja wind-field
sampling (regime-mean flow) for speed-scaled quiver overlays; accumulation
diagnostics (ventilation index, flux convergence); a realistic 3D terrain inset;
and a png(400dpi)+pdf saver. Importing applies the `pubfig` publication style.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from src.stage1_satml.decomp import pubfig  # applies publication style on import
from src.stage1_satml.decomp import terrain_transport as tt
from config import KANDY_PINN_BBOX as BB

DEC = REPO / "data" / "processed" / "decomp"
STG = REPO / "data" / "processed" / "stage1_v3"
PIN = REPO / "data" / "processed" / "pinn_inputs"

# ── model variant ───────────────────────────────────────────────────────────
# v2 = wide-domain (Knuckles/central-highlands) WindNinja winds + origin-conditioned
# B(t) — ADOPTED AS THE OFFICIAL MODEL 2026-06-15 (W1 swap gates + BV1 + G-c all pass;
# docs/v2_consolidated_implementation_2026-06-15.md). DEFAULT is now v2 →
# `_additive_v2` fields → results/figures/paper_figures_v2/.
# Set PAPERFIG_VARIANT=v1 to regenerate the ARCHIVED v1 set (narrow winds, flat B)
# → `_additive` fields → results/figures/paper_figures/.
# ADD is the additive-field suffix every figure read must use (hardcoded + field()).
VARIANT = os.environ.get("PAPERFIG_VARIANT", "v2").strip().lower()
ADD = "_additive" if VARIANT == "v1" else "_additive_v2"
PAPER_OUT = REPO / "results" / "figures" / ("paper_figures" if VARIANT == "v1"
                                            else "paper_figures_v2")
PAPER_OUT.mkdir(parents=True, exist_ok=True)

# ── universal PM scale — YlOrRd, raised vmax + nonlinear (PowerNorm) ─────────
# Locked 2026-06-06 (user): warm "emission-hotspot" map; one SHARED scale but the
# top is extended to the episodic core spike and a PowerNorm(γ>1) is applied so the
# enclosed-core/episodic maxima stand out as deep red WITHOUT saturating, while the
# flatter validated-headline basin still shows its yellow→orange gradient.
PM_CMAP = "YlOrRd"
PM_VMIN, PM_VMAX, PM_GAMMA = 10.0, 40.0, 1.30
TURBO = PM_CMAP   # back-compat: every PM heatmap reference now resolves to YlOrRd
# A4 publication sizing: full text width ~178 mm = 7.0 in; figures kept <= ~8.7 in
# tall so each fits on one A4 page with its caption.
A4_W = 7.0
A4_W_WIDE = 7.2
A4_H_MAX = 8.7
WHO_TICKS = [15, 25, 35]
WHO_LABELS = ["15·IT-3", "25·IT-2", "35·IT-1"]
CEN = (7.2906, 80.6337)
INFERNO = "inferno"          # reserved for pure EMISSION-source maps (distinct from concentration)


def pm_norm(vmin=None, vmax=None, gamma=None):
    """shared nonlinear PM norm — PowerNorm(γ) so the elevated core/episode pops."""
    return mcolors.PowerNorm(gamma=gamma or PM_GAMMA,
                             vmin=PM_VMIN if vmin is None else vmin,
                             vmax=PM_VMAX if vmax is None else vmax)


def pm_cbar(fig, im, ax, shrink=0.8, label="PM$_{2.5}$ (µg m$^{-3}$)", ticks=None):
    tk = ticks or WHO_TICKS
    cb = fig.colorbar(im, ax=ax, extend="both", ticks=tk, shrink=shrink, label=label)
    if tk is WHO_TICKS or tk == WHO_TICKS:
        cb.ax.set_yticklabels(WHO_LABELS, fontsize=7)
    return cb


def square_heatmaps(fig):
    """CANONICAL 2026-06-06: force every imshow heatmap axis to a square box. Colorbars
    (label '<colorbar>', 0 images) and line/bar plots (0 images) are left untouched."""
    for ax in fig.axes:
        if len(ax.images) >= 1:
            ax.set_box_aspect(1)


def save(fig, name, pdf=False, square=True):
    if square:
        square_heatmaps(fig)
    fig.savefig(PAPER_OUT / f"{name}.png", dpi=400, bbox_inches="tight")
    if pdf:
        fig.savefig(PAPER_OUT / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}.png" + (" + .pdf" if pdf else ""))


# ── field loaders ───────────────────────────────────────────────────────────
def field(year, kind="additive", col="pm25_q50", hours=None):
    """annual (or hour-subset) mean grid for a prediction field.
    kind: 'additive' (headline turbo), '4factor' (scenario), '' (smooth)."""
    suf = {"additive": ADD, "additive_v2": "_additive_v2",
           "4factor": "_4factor", "smooth": ""}[kind]
    cols = ["time", "lat", "lon", col]
    d = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}{suf}.parquet", columns=cols)
    if hours is not None:
        loct = pd.to_datetime(d.time, utc=True).dt.tz_convert("Asia/Colombo")
        d = d[loct.dt.hour.isin(hours)]
    lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())
    Z = d.groupby(["lat", "lon"])[col].mean().unstack("lon").reindex(index=lats, columns=lons).values
    return Z, lats, lons


# ── WindNinja wind sampling (for quiver) ────────────────────────────────────
def _met(year):
    return pd.read_parquet(STG / f"inference_grid_{year}_s12451.parquet",
                           columns=["datetime_utc", "u10", "v10", "blh_m"])


def wn_regime_mean(year=2023, hours=None, sample=400):
    """frequency-weighted MEAN WindNinja terrain wind (u,v on the 64x64 grid) over
    the hours subset (e.g. night 21–05, day 11–16). Returns U, V, lats, lons."""
    m = _met(year).dropna()
    loct = pd.to_datetime(m.datetime_utc, utc=True).dt.tz_convert("Asia/Colombo")
    if hours is not None:
        m = m[loct.dt.hour.isin(hours)]
    if len(m) > sample:
        m = m.sample(sample, random_state=0)
    L = np.load(PIN / "windninja_library.npz", allow_pickle=True)
    lats, lons = L["lats"], L["lons"]
    Us, Vs = [], []
    for _, r in m.iterrows():
        w = tt.windninja_wind(r.u10, r.v10, r.blh_m)
        if w is not None:
            Us.append(w[0]); Vs.append(w[1])
    if not Us:
        return None, None, lats, lons
    return np.mean(Us, axis=0), np.mean(Vs, axis=0), lats, lons


_SEAS_ORDER = ["DJF", "MAM", "JJA", "SON"]


def load_seasonal_episodic():
    """per-season WindNinja wind + A-patterns + the episodic worst-case field
    (built by scripts/build_seasonal_episodic_fields.py)."""
    return np.load(DEC / "seasonal_episodic_fields.npz", allow_pickle=True)


def seas_wind(d, season):
    """per-season WindNinja regime-mean (U,V,lats,lons) — the monsoon reversal."""
    i = _SEAS_ORDER.index(season)
    return d["seas_U"][i], d["seas_V"][i], d["wn_lats"], d["wn_lons"]


def emission_contours(ax, levels_pct=(86, 94, 98), color="#39FF14", lw=0.7):
    """overlay congestion-emission intensity contours (S_traffic) on a PM map, marking
    the high-emission arterials/core that signal where concentration can spike."""
    from scipy.ndimage import gaussian_filter
    d = np.load(DEC / "S_traffic_kandy.npz")
    E = gaussian_filter(d["E_fine"], 3); flat, flon = d["fine_lat"], d["fine_lon"]
    LO, LA = np.meshgrid(flon, flat)
    lv = np.percentile(E, list(levels_pct))
    ax.contour(LO, LA, E, levels=lv, colors=color, linewidths=lw, alpha=0.85, linestyles="-")


def quiver(ax, U, V, lats, lons, step=6, color="white", scale=None, lw=0.6, solid=None):
    """quiver over a map (lats ascending S→N, lons W→E). Default = speed-shaded (Greys);
    pass solid="#222" for a single high-contrast colour (clearer for direction on pale maps)."""
    LO, LA = np.meshgrid(np.linspace(lons.min(), lons.max(), U.shape[1]),
                         np.linspace(lats.min(), lats.max(), U.shape[0]))
    sl = (slice(None, None, step), slice(None, None, step))
    if solid is not None:
        return ax.quiver(LO[sl], LA[sl], U[sl], V[sl], color=solid, scale=scale or 26,
                         width=0.006, headwidth=3.5, pivot="mid", alpha=0.9)
    spd = np.hypot(U, V)
    return ax.quiver(LO[sl], LA[sl], U[sl], V[sl], spd[sl], cmap="Greys",
                     scale=scale or 28, width=0.005, headwidth=3.2, edgecolor=color,
                     linewidth=lw, pivot="mid", alpha=0.95)


# ── accumulation / deposition diagnostics ───────────────────────────────────
def ventilation_index(year=2023, hours=None):
    """basin ventilation index VI = BLH·|U10| time-mean (m²/s). Low = stagnant."""
    m = _met(year).dropna()
    loct = pd.to_datetime(m.datetime_utc, utc=True).dt.tz_convert("Asia/Colombo")
    if hours is not None:
        m = m[loct.dt.hour.isin(hours)]
    return float((m.blh_m * np.hypot(m.u10, m.v10)).mean())


def flux_convergence(C, U, V, dx):
    """−∇·(C u): positive where pollution accumulates (mass converges), µg m⁻³ s⁻¹·m⁻¹·…
    sign-only diagnostic — normalise for display."""
    Fy, Fx = np.gradient(C * V, dx), None
    _, Fx = np.gradient(C * U, dx)
    Cy = np.gradient(C * V, dx)[0]
    conv = -(Fx + Cy)
    return conv


def solver_state(u_syn, v_syn, blh):
    """run the WindNinja-driven solver for a condition → C field + (U,V) wind + grids."""
    lats, lons, z, S, dx = tt.load_grids()
    _, _, _, _, C = tt.solve_terrain(u_syn, v_syn, blh, lats, lons, z, S, dx)
    w = tt.windninja_wind(u_syn, v_syn, blh)
    U, V = (w if w is not None else (np.zeros_like(z), np.zeros_like(z)))
    return C, U, V, lats, lons, z, dx
