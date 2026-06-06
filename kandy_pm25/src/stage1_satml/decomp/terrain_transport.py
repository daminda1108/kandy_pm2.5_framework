"""
terrain_transport.py — TERRAIN-AWARE advection–dispersion for the Kandy valley.
Replaces the flat-ground solver (which was physically wrong for a basin city).

Pollution dispersion in a valley is governed by atmospheric–terrain interaction:
  • channeled wind  — the up-slope component of the synoptic wind is blocked by
    hillsides, so flow follows the valley (along-contour).
  • nocturnal drainage (katabatic) — a downslope flow ∝ −∇z, strong under a
    shallow/stable boundary layer, pools pollution on the valley FLOOR.
  • ridge-confined mixing — horizontal diffusivity is suppressed across steep
    terrain; ridges are barriers and the basin traps.

Solves steady-state  u_terrain·∇C − ∇·(K(x,y)∇C) + λC = S  (upwind, Dirichlet
C=0 at the domain edge), source S from VIIRS NTL (urban emissions). Deterministic,
NOT a PINN. Terrain z from SRTM.

API: solve_terrain(u_syn, v_syn, blh) -> C (NxN), and grids via load_grids().
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.interpolate import RegularGridInterpolator

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
from config import KANDY_PINN_BBOX as BB

PINN = HERE / "data" / "processed" / "pinn_inputs"
N = 64
# K0/DRAIN/SLOPE_K cross-city CALIBRATED on 10 monitored valleys (2026-06-01,
# scripts/calibrate_terrain_solver.py; cross-city Pearson +0.49+/-0.17). The
# calibration barely moved the original hand-set priors (120 / 8.0 / 0.060) -> the
# physical priors were sound and now have empirical backing. BLOCK/BLH_REF held
# (unidentifiable under the stable-calm calibration regime).
K0 = 124.88                # base horizontal diffusivity (m²/s) at reference BLH (was 120)
BLH_REF = 300.0            # reference BLH; mixing scales with BLH/BLH_REF
LAM = 0.003 / 1000.0       # deposition loss (1/s)
BLOCK = 1.0                # up-slope blocking strength (channeling)
DRAIN = 8.14               # katabatic gain (m/s per unit slope; was 8.0)
SLOPE_K = 0.062            # slope scale for diffusivity suppression (was 0.06)
SLOPE_REF = 0.05           # slope scale for channeling saturation
# Vertical decoupling (2026-06-03): pixels whose height above the valley floor
# (delta_z) exceeds the inversion/BLH top decouple to the free troposphere and
# ventilate — the cold-air-pool physics that makes elevated sites (Hantana ridge)
# read low while the enclosed floor (core) accumulates (Chemel & Burns 2015;
# Largeron & Staquet 2016). Implemented as a smooth sigmoid loss inside the PDE so
# the floor-ridge contrast stays continuous. Amplitude bracketed; magnitude awaits
# across-elevation sensor calibration (the FECT NIFS/Hantana pair suggests strong).
VENT_FT = 0.018            # free-troposphere ventilation rate above the inversion (1/s)
VENT_H = 110.0             # sigmoid transition width for decoupling (m)
FLOOR_PCTL = 5.0           # valley-floor reference = this percentile of elevation


def _grid_fields():
    """Elevation z, slopes, and NTL source on the N×N solver grid (lat,lon ascending)."""
    ze = np.load(PINN / "kandy_elev_grid_100m.npz")
    elat, elon = ze["lat_grid"][:, 0], ze["lon_grid"][0, :]
    Z = ze["elev"].astype(float)
    if elat[0] > elat[-1]:
        elat, Z = elat[::-1], Z[::-1, :]
    if elon[0] > elon[-1]:
        elon, Z = elon[::-1], Z[:, ::-1]
    # SOURCE (2026-06-04): congestion-weighted traffic EMISSION surface — a bottom-up
    # road allocation, centrality-AADT (betweenness pass-by + closeness O-D; Lowry
    # 2014, Kazerani & Winter 2009) × COPERT/HBEFA speed/congestion emission factor
    # (Borge 2017), built by build_traffic_emission.py. Replaces the hand-placed
    # congestion Gaussians + raw road kernel with the literature-backed flow
    # allocation: the hotspot now follows real through-traffic + trip-end congestion
    # (lake round, clock tower, Katugastota/Peradeniya arterials, bus stands).
    # Magnitude is a literature-bounded prior (no Kandy traffic counts; TomTom flow
    # verified UNAVAILABLE for Sri Lanka) — carried in the model UQ.
    tr = np.load(HERE / "data" / "processed" / "decomp" / "S_traffic_kandy.npz")
    Ef = tr["E_fine"].astype(float)                 # fine 160×160 emission field
    flat, flon = tr["fine_lat"], tr["fine_lon"]

    lats = np.linspace(BB["lat_min"], BB["lat_max"], N)
    lons = np.linspace(BB["lon_min"], BB["lon_max"], N)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    pts = np.stack([LA.ravel(), LO.ravel()], 1)
    z = RegularGridInterpolator((elat, elon), Z, bounds_error=False, fill_value=None)(pts).reshape(N, N)
    S = RegularGridInterpolator((flat, flon), Ef, bounds_error=False, fill_value=0.0)(pts).reshape(N, N)
    S = np.log1p(4.0 * np.clip(S, 0, None))         # same tempering as the saved surface
    S = S / (S.max() + 1e-9)
    dx = (BB["lat_max"] - BB["lat_min"]) * 111000.0 / (N - 1)
    return lats, lons, z, S, dx


def load_grids():
    lats, lons, z, S, dx = _grid_fields()
    return lats, lons, z, S, dx


# Tunable parameters (defaults = the hand-set Kandy values). Calibrated across
# monitored valley analogues by scripts/calibrate_terrain_solver.py.
DEFAULT_PARAMS = dict(K0=K0, BLH_REF=BLH_REF, LAM=LAM, BLOCK=BLOCK,
                      DRAIN=DRAIN, SLOPE_K=SLOPE_K, SLOPE_REF=SLOPE_REF,
                      VENT_FT=VENT_FT, VENT_H=VENT_H, FLOOR_PCTL=FLOOR_PCTL)

# ── WindNinja diagnostic-wind library (2026-06-05) ──────────────────────────
# Replaces the hand-rolled channelling+drainage (the analytical block below) with
# physically-derived mass-consistent terrain winds precomputed by WindNinja
# (scripts/build_windninja_library.py). Falls back to the analytical wind when the
# library is absent or the grid size differs.
USE_WINDNINJA = True
_WN_LIB_PATH = PINN / "windninja_library.npz"
_WN_LIB = None


def _load_wn_lib():
    global _WN_LIB
    if _WN_LIB is None and _WN_LIB_PATH.exists():
        d = np.load(_WN_LIB_PATH, allow_pickle=True)
        _WN_LIB = dict(u=d["u"], v=d["v"], dirs=d["dirs"], speeds=d["speeds"])
    return _WN_LIB


def windninja_wind(u_syn, v_syn, blh):
    """Terrain wind (U, V on the library grid) from the WindNinja library, blended
    by direction (circular), speed (2 anchors, linear) and stability (night drainage
    ↔ day mixing via BLH). Returns None if the library is unavailable."""
    lib = _load_wn_lib()
    if lib is None:
        return None
    dirs, speeds, u4, v4 = lib["dirs"], lib["speeds"], lib["u"], lib["v"]
    spd = float(np.clip(np.hypot(u_syn, v_syn), 0.2, 8.0))
    dfrom = float(np.degrees(np.arctan2(-u_syn, -v_syn)) % 360.0)
    nd = len(dirs); step = 360.0 / nd
    i0 = int(np.floor(dfrom / step)) % nd; i1 = (i0 + 1) % nd
    wd1 = ((dfrom - dirs[i0]) % 360.0) / step; wd0 = 1.0 - wd1
    s0, s1 = float(speeds[0]), float(speeds[1])
    cs1 = (spd - s0) / (s1 - s0); cs0 = 1.0 - cs1            # linear over the 2 anchors
    wn = float(np.clip((600.0 - blh) / 600.0, 0, 1)); wday = 1.0 - wn
    def pick(arr):
        return sum(wdv * csv * (wn * arr[di, si, 0] + wday * arr[di, si, 1])
                   for di, wdv in ((i0, wd0), (i1, wd1))
                   for si, csv in ((0, cs0), (1, cs1)))
    return pick(u4), pick(v4)


def solve_terrain(u_syn, v_syn, blh, lats=None, lons=None, z=None, S=None, dx=None, P=None):
    """Steady-state terrain advection-dispersion. P overrides DEFAULT_PARAMS; grid
    size n is taken from z.shape (square), so any resolution works (not just N=64)."""
    if z is None:
        lats, lons, z, S, dx = _grid_fields()
    p = {**DEFAULT_PARAMS, **(P or {})}
    n = z.shape[0]
    # gradients (x=lon=j eastward, y=lat=i northward)
    dzdy, dzdx = np.gradient(z, dx)            # rise per metre
    slope = np.hypot(dzdx, dzdy) + 1e-9
    nx, ny = dzdx / slope, dzdy / slope        # unit up-slope
    # TERRAIN WIND. Preferred: WindNinja mass-consistent diagnostic field (channelling,
    # blocking, day anabatic / night katabatic drainage — all physically derived).
    wn = windninja_wind(u_syn, v_syn, blh) if USE_WINDNINJA else None
    if wn is not None and wn[0].shape == z.shape:
        U, V = wn
    else:
        # analytical fallback (hand-rolled channelling + drainage)
        block = p["BLOCK"] * np.clip(slope / p["SLOPE_REF"], 0, 1)
        into = u_syn * nx + v_syn * ny             # synoptic component into the slope
        u_ch = u_syn - block * into * nx
        v_ch = v_syn - block * into * ny
        stab = np.clip((600.0 - blh) / 600.0, 0, 1)   # 1 shallow/stable → 0 deep/mixed
        U = u_ch - p["DRAIN"] * stab * dzdx
        V = v_ch - p["DRAIN"] * stab * dzdy
    # 3) diffusivity scales with BLH (deep convective BLH → strong turbulent mixing
    #    → smooth field; shallow stable BLH → weak mixing → concentrated), and is
    #    suppressed across steep terrain (ridges are mixing barriers)
    Kf = p["K0"] * np.clip(blh / p["BLH_REF"], 0.3, 6.0) * np.exp(-slope / p["SLOPE_K"])
    # vertical decoupling: height above the valley floor vs the inversion (BLH).
    # Pixels above the pool top (delta_z > blh) ventilate to the free troposphere
    # via a smooth sigmoid loss → ridges suppressed, enclosed floor accumulates.
    dz_floor = z - np.percentile(z, p["FLOOR_PCTL"])
    vent = p["VENT_FT"] / (1.0 + np.exp(-(dz_floor - blh) / p["VENT_H"]))
    lam_field = p["LAM"] + vent

    A = sp.lil_matrix((n * n, n * n))
    b = S.flatten().astype(float).copy()
    for i in range(n):
        for j in range(n):
            k = i * n + j
            if i in (0, n - 1) or j in (0, n - 1):
                A[k, k] = 1.0; b[k] = 0.0; continue
            ux, uy = U[i, j], V[i, j]
            kE = 0.5 * (Kf[i, j] + Kf[i, j + 1]) / dx ** 2
            kW = 0.5 * (Kf[i, j] + Kf[i, j - 1]) / dx ** 2
            kN = 0.5 * (Kf[i, j] + Kf[i + 1, j]) / dx ** 2
            kS = 0.5 * (Kf[i, j] + Kf[i - 1, j]) / dx ** 2
            diag = kE + kW + kN + kS + lam_field[i, j]
            A[k, k + 1] += -kE; A[k, k - 1] += -kW
            A[k, k + n] += -kN; A[k, k - n] += -kS
            # advection upwind
            if ux >= 0: diag += ux / dx; A[k, k - 1] += -ux / dx
            else:       diag += -ux / dx; A[k, k + 1] += ux / dx
            if uy >= 0: diag += uy / dx; A[k, k - n] += -uy / dx
            else:       diag += -uy / dx; A[k, k + n] += uy / dx
            A[k, k] += diag
    C = spla.spsolve(A.tocsr(), b).reshape(n, n)
    return lats, lons, z, S, C


if __name__ == "__main__":
    # sanity: stagnant shallow-BLH case — pollution should pool on the valley FLOOR
    lats, lons, z, S, C = solve_terrain(0.4, 0.0, 100.0)   # weak easterly, shallow BLH
    fi, fj = np.unravel_index(np.argmin(z), z.shape)        # valley floor (lowest)
    ci, cj = np.unravel_index(np.argmax(C), C.shape)        # concentration peak
    print(f"valley floor (min z={z.min():.0f}m) at lat {lats[fi]:.4f} lon {lons[fj]:.4f}")
    print(f"concentration peak at      lat {lats[ci]:.4f} lon {lons[cj]:.4f}  (z={z[ci,cj]:.0f}m)")
    print(f"Kandy core ~7.2906/80.6337; NTL source peak at "
          f"lat {lats[np.unravel_index(S.argmax(),S.shape)[0]]:.4f} "
          f"lon {lons[np.unravel_index(S.argmax(),S.shape)[1]]:.4f}")
    print(f"C peak/mean = {C.max()/C.mean():.2f}×  (elevated pixels mean C "
          f"{C[z>z.mean()].mean():.3f} vs floor pixels {C[z<np.quantile(z,0.2)].mean():.3f})")
