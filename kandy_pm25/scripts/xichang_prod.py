"""xichang_prod.py — apply the locked Kandy v2 production decomposition to Xichang.

Parallel to the Kandy chain (predict_T_anchor → build_decomp_map → build_overlay_
predictions → build_additive_field_v2), city-parameterised for Xichang, writing the
SAME production-format products so a parameterised paper-figure fork can read them.
The locked Kandy scripts are NOT touched.

Design (user-locked 2026-06-27): 2-SENSOR Kandy-grade mirror (T(t) from the elevation-
gradient anchor pair only; the rest of the CNEMC network is held out for validation);
years 2020–2025, headline 2023; v1 transboundary background (rural-VanD × GEOS-CF
daily shape); full F1–F13 figure fork.

Grid: 64×64 over the city-centred core box (= WindNinja library box = core terrain).
Stages (run `--stage all` or a subset):
  static  S_emit, M(confinement static parts), VanD levels, traffic-on-solver-grid
  tt      T(t) hourly 2020–2025 from the 2 anchors  → T_xichang_hourly_{y}.parquet
  bt      B(t) v1 hourly                            → B_background_hourly_{y}_xichang.parquet
  field   smooth → 4factor (WindNinja A_transport + e(t)) → additive_v2  (per year)
  seasepi seasonal + episode precomputed fields     → seasonal_episodic_fields_xichang.npz
  valid   CNEMC held-out-network validation aggregates → xichang_validation_*.csv/parquet
Out: data/processed/decomp_xichang/*
"""
from __future__ import annotations
import argparse
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from src.transfer_validation.citypack import get
from src.transfer_validation.anchors import station_stats
from src.transfer_validation.assembly import (spatial_fields, b_hourly,
                                              KAPPA, _terrain, _interp2)
from src.transfer_validation import drivers
from src.transfer_validation.t_anchor import fit_and_build
from src.transfer_validation import vand as V
from xichang_twin_figures import _draw_list           # elevation-gradient anchor pair
from city_config import cfg, citypack, e_profile

# ── city config (set by _setup(city); defaults = Xichang) ───────────────────
CITY = "xichang"
TZ = "Asia/Shanghai"
YEARS = list(range(2020, 2026))
HEADLINE = 2023
NGRID = 64
PIN = REPO / "data" / "processed" / "pinn_inputs"
OUT = REPO / "data" / "processed" / "decomp_xichang"
OUT.mkdir(parents=True, exist_ok=True)
CORE_TERRAIN = PIN / "xichang_terrain_core.npz"
WN_LIB = PIN / "xichang_windninja_library.npz"
XKAPPA = 0.05
E_PROF = None


def _setup(city):
    """Point all module globals at `city` (from city_config)."""
    global CITY, TZ, YEARS, HEADLINE, OUT, CORE_TERRAIN, WN_LIB, XKAPPA, E_PROF
    c = cfg(city)
    CITY = city; TZ = c["tz"]; YEARS = list(c["years"]); XKAPPA = c["kappa"]
    HEADLINE = c["years"][len(c["years"]) // 2] if 2023 not in c["years"] else 2023
    OUT = REPO / "data" / "processed" / f"decomp_{city}"; OUT.mkdir(parents=True, exist_ok=True)
    CORE_TERRAIN = PIN / f"{city}_terrain_core.npz"
    WN_LIB = PIN / f"{city}_windninja_library.npz"
    E_PROF = e_profile(city)


def cp_xichang():
    return replace(citypack(CITY), terrain_npz_name=CORE_TERRAIN.name,
                   score_years=tuple(YEARS))


def anchors():
    cp = cp_xichang()
    ty = max(y for y in YEARS if y < max(YEARS)) if len(YEARS) > 1 else YEARS[0]
    return _draw_list(cp, tuple(y for y in YEARS if y < max(YEARS)), max(YEARS))[0].anchors


# ─────────────────────────── static spatial products ───────────────────────
def build_static():
    cp = cp_xichang()
    fields = spatial_fields(cp)                        # S (S_emit, mean1), c, h_ridge
    glat, glon = fields["glat"], fields["glon"]
    # S_emit
    np.savez(OUT / f"S_emit_{CITY}.npz", S_emit=fields["S"], lats=glat, lons=glon)
    # confinement static field c(x,y) + h_ridge (M assembled per-hour with BLH later)
    np.savez(OUT / f"M_confinement_{CITY}.npz", c=fields["c_grid_on_S"],
             lats=glat, lons=glon, h_ridge=fields["h_ridge"], kappa=KAPPA)
    # VanD annual levels over the core box
    lev = V.annual_levels(cp, YEARS)
    lev.to_csv(OUT / f"vandonkelaar_{CITY}_annual.csv", index=False)
    # rural background floor (v1 B level)
    bg = V.rural_background(cp, YEARS)
    bg.to_csv(OUT / f"background_b_annual_{CITY}.csv", index=False)
    print(f"  static: grid {len(glat)}×{len(glon)}  S_emit[{fields['S'].min():.2f},"
          f"{fields['S'].max():.2f}]  h_ridge {fields['h_ridge']:.0f} m")
    print(f"  VanD basin levels: {dict(zip(lev.year, lev.basin_mean.round(1)))}")
    print(f"  rural floor (P10): {dict(zip(bg.year, bg.rural_p10.round(1)))}")
    return fields


# ─────────────────────────── T(t) — 2-sensor anchor ────────────────────────
def _anchor_annual_obs(cp, a):
    """Observed annual mean PM2.5 of the 2 anchor sensors per year (the model's
    allowed ground truth — varies year-to-year, unlike the 2023-frozen VanD tile)."""
    df = pd.read_parquet(cp.station_parquet(), columns=["datetime_utc", "station_id", "pm25"])
    df = df[df.station_id.isin(list(a))].dropna(subset=["pm25"])
    df["year"] = pd.to_datetime(df.datetime_utc, utc=True).dt.year
    return df.groupby("year").pm25.mean()


def build_T():
    cp = cp_xichang()
    a = anchors()
    elev = _elev_at_station(cp, a)
    print(f"  T(t) anchors = {a}  Δz {elev}  (2-sensor Kandy-grade)")
    T, info = fit_and_build(cp, a)                     # VanD-anchored (per-year)
    T["year"] = pd.to_datetime(T.datetime).dt.year
    sens = _anchor_annual_obs(cp, a)                   # observed sensor annual mean
    # SENSOR-ANCHORED headline: shift each year so annual mean = the 2 sensors'
    # observed mean (removes VanD's documented over-estimate of low-PM cities +
    # restores inter-annual variation; VanD freezes at the 2023 tile). VanD-anchored
    # kept as the *_vand comparison (shows the inherited satellite bias).
    for y in YEARS:
        m = T.year == y
        vand_mean = float(T.loc[m, "T_q50"].mean())
        s = float(sens.get(y, sens.get(min(y, int(sens.index.max())), vand_mean)))
        shift = s - vand_mean
        sub_v = T[m][["datetime", "T_q05", "T_q50", "T_q95"]].rename(columns={"datetime": "datetime_utc"})
        sub_v.to_parquet(OUT / f"T_{CITY}_hourly_{y}_vand.parquet", index=False)
        sub_s = sub_v.copy()
        for c in ("T_q05", "T_q50", "T_q95"):
            sub_s[c] = sub_s[c] + shift
        sub_s.to_parquet(OUT / f"T_{CITY}_hourly_{y}.parquet", index=False)
    annv = T.groupby("year").T_q50.mean().round(1).to_dict()
    print(f"  VanD-anchored annual: {annv}")
    print(f"  sensor-anchored (headline): {sens.round(1).to_dict()}")


def _elev_at_station(cp, ids):
    lat1, lon1, dz = _terrain(cp)
    st = cp.stations().set_index("station_id")
    out = {}
    for i in ids:
        if i in st.index:
            out[i] = float(_interp2(lat1, lon1, dz,
                                    np.array([st.loc[i, "lat"]]),
                                    np.array([st.loc[i, "lon"]]))[0])
    return {k: round(v) for k, v in out.items()}


# ─────────────────────────── B(t) v1 background ────────────────────────────
def build_B():
    """B(t) v1 (transboundary background), GROUND-ANCHORED for monitored cities:
    B_annual(year) = (1 − f) · L_obs(year), where L_obs is the 2 anchor sensors'
    OBSERVED annual mean (real ground data), and f is the city local fraction
    (source apportionment). A city with a real network does NOT need the satellite:
    the observed level is inter-annually live and is not frozen at the 2023 VanD
    tile (the freeze that limits the sensorless Kandy product). × GEOS-CF daily
    seasonal shape (diurnally flat). Kandy itself, lacking sensors, keeps the
    VanD-anchored background in src/.../decomp/build_additive_background.py — VanD
    is needed there precisely because there is no ground level to anchor to.
    NOTE: changing B does not move the headline basin mean (≡ T(t), B cancels) nor
    the held-out seasonal/diurnal/level/spatial scores (P_local rank is invariant);
    it only grounds the background partition and the within-city increment amplitude."""
    cp = cp_xichang()
    f = float(cp.f_local)
    a = anchors()
    sens = _anchor_annual_obs(cp, a)                    # observed sensor annual mean (ground)
    g = drivers.geos_cf_prior(cp)
    g["date"] = g.datetime.dt.floor("D")
    daily_all = g.groupby("date").pm25_prior.mean()
    b_ann = {}
    for y in YEARS:
        obs = float(sens.get(y, sens.get(min(y, int(sens.index.max())), np.nan)))
        if not np.isfinite(obs):
            obs = float(sens.mean())
        b_annual = (1.0 - f) * obs
        b_ann[y] = round(b_annual, 1)
        T = pd.read_parquet(OUT / f"T_{CITY}_hourly_{y}.parquet", columns=["datetime_utc"])
        d = pd.to_datetime(T.datetime_utc).dt.floor("D")
        shape = daily_all[daily_all.index.year == y]
        if len(shape):
            s = d.map(shape / shape.mean()).fillna(1.0); s = s / s.mean()
        else:
            s = pd.Series(1.0, index=T.index)
        B = b_annual * s.to_numpy()
        pd.DataFrame({"datetime_utc": T.datetime_utc, "B": B,
                      "B_lo": 0.70 * B, "B_hi": 1.25 * B}).to_parquet(
            OUT / f"B_background_hourly_{y}_{CITY}.parquet", index=False)
    print(f"  f_local={f} → B_annual=(1-f)·L_obs(ground): {b_ann}  (ground-anchored, no VanD)")


# ─────────────────────────── field assembly (4factor + additive_v2) ────────
STORE = 24                                  # storage grid (figures zoom-interpolate)
BLH_EDGES = np.array([0, 100, 175, 275, 400, 600, 1000, 5000.0])

# emission-timing e(t) and κ are city-specific (set by _setup → E_PROF / XKAPPA
# from city_config: source-mix-based, zero-GT). κ small where the urban core sits
# above the valley floor (Phase-0 κ→0); city-specific source mix shapes e(t).


def _solver_grids():
    """64×64 elevation + traffic source over the core box (matches WN library box)."""
    import rasterio
    from build_station_terrain import resample_dem
    z = np.load(CORE_TERRAIN)
    lat = np.asarray(z["lat_grid"])[:, 0].astype(float)
    lon = np.asarray(z["lon_grid"])[0, :].astype(float)
    lats = np.linspace(lat.min(), lat.max(), NGRID)
    lons = np.linspace(lon.min(), lon.max(), NGRID)
    LO, LA = np.meshgrid(lons, lats)
    SRTM = REPO / "data" / "external" / "xichang" / "dem" / "xichang_srtm_dem.tif"
    elev = resample_dem(SRTM, LA.astype("f4"), LO.astype("f4"))[::-1]   # N-S flip (gotcha)
    tr = np.load(OUT / f"S_emit_{CITY}.npz")  # placeholder; traffic loaded below
    trf = np.load(REPO / "data" / "processed" / "decomp" / f"S_traffic_{CITY}.npz")
    from scipy.interpolate import RegularGridInterpolator
    S = RegularGridInterpolator((trf["lats"], trf["lons"]), trf["S_traffic"],
                                bounds_error=False, fill_value=0.0)(
        np.stack([LA.ravel(), LO.ravel()], 1)).reshape(NGRID, NGRID)
    S = S / (S.max() + 1e-9)
    dx = (lat.max() - lat.min()) * 111000.0 / (NGRID - 1)
    return lats, lons, elev, S, dx


def _downsample(F, lats, lons, tlat, tlon):
    from scipy.interpolate import RegularGridInterpolator
    g = RegularGridInterpolator((lats, lons), F, bounds_error=False, fill_value=None)
    LO, LA = np.meshgrid(tlon, tlat)
    return g(np.stack([LA.ravel(), LO.ravel()], 1)).reshape(len(tlat), len(tlon))


def _emission_backbone(tlat, tlon):
    """Local-increment spatial backbone = EMISSION proxy (VIIRS NTL + congestion
    traffic), NOT the smooth VanD PM surface. Validated to rank held-out stations
    far better (NTL ρ=0.80, traffic 0.70 vs VanD 0.40); principled — the regional
    VanD PM level lives in B(t), the local pattern follows urban emission activity."""
    from scipy.interpolate import RegularGridInterpolator
    LO, LA = np.meshgrid(tlon, tlat)
    def samp(path, key, lk="lats", ok="lons"):
        z = np.load(path); A = np.asarray(z[key], float); la = np.asarray(z[lk]); lo = np.asarray(z[ok])
        if la.ndim == 2:
            la = la[:, 0]; lo = lo[0, :]
        if la[0] > la[-1]:
            la = la[::-1]; A = A[::-1]
        return RegularGridInterpolator((la, lo), A, bounds_error=False, fill_value=None)(
            np.column_stack([LA.ravel(), LO.ravel()])).reshape(len(tlat), len(tlon))
    nz = np.load(PIN / f"{CITY}_viirs_ntl_stations.npz")
    nkey = [k for k in nz.files if "ntl" in k.lower() or "rad" in k.lower() or "avg" in k.lower()][0]
    ntl = samp(PIN / f"{CITY}_viirs_ntl_stations.npz", nkey, "lat_grid", "lon_grid")
    trf = samp(REPO / "data" / "processed" / "decomp" / f"S_traffic_{CITY}.npz", "S_traffic")
    # log-temper each proxy's heavy urban tail (NTL spans ~8× core/edge; raw use
    # explodes the increment), then blend NTL-weighted and cap the contrast so the
    # field keeps the RANK skill without the amplitude blow-up (obs is only ~1.6×).
    ntl = np.log1p(2.0 * np.clip(ntl, 0, None) / (np.nanmean(np.clip(ntl, 0, None)) + 1e-9))
    trf = np.log1p(2.0 * np.clip(trf, 1e-6, None) / (np.nanmean(np.clip(trf, 1e-6, None)) + 1e-9))
    ntl /= np.nanmean(ntl); trf /= np.nanmean(trf)
    S = 0.6 * ntl + 0.4 * trf
    S = S / np.nanmean(S)
    # balance RANK (emission ordering) vs AMPLITUDE (real within-city gradient is
    # small): keep the ordering but cap contrast near the observed ~1.6× max/min.
    S = np.clip(S, 0.80, 1.45)
    return S / np.nanmean(S)


def build_field():
    import os
    from src.stage1_satml.decomp import terrain_transport as tt
    # ── ablation hook (evidence-hardening Phase 3) ────────────────────────────
    # ABLATE ∈ {no_terrain, no_emission, no_pattern, no_timing, no_winds}. When set,
    # writes to a *_abl_{name} suffix (never clobbers the real product). The additive
    # headline uses S_emit·M only, so no_terrain/no_emission/no_pattern need no wind
    # solve (fast); no_timing/no_winds affect only the 4factor scenario.
    ABL = os.environ.get("ABLATE", "").strip().lower()
    SUF = f"_abl_{ABL}" if ABL else ""
    ABL_ADD_ONLY = ABL in ("no_terrain", "no_emission", "no_pattern")
    e_at = lambda h: E_PROF[np.asarray(h).astype(int) % 24]   # city-specific e(t)
    if ABL == "no_timing":
        e_at = lambda h: np.full_like(np.asarray(h, float), float(np.mean(E_PROF)))
    # point the production terrain solver at the city WindNinja library + grids.
    # NO_WINDNINJA=1 uses the analytical wind fallback instead — valid when only the
    # additive_v2 HEADLINE is needed (it uses S_emit·M, wind-independent; winds enter
    # only the unscored 4factor scenario), avoiding a slow 64-solve library build.
    tt._WN_LIB_PATH = WN_LIB; tt._WN_LIB = None
    tt.USE_WINDNINJA = (os.environ.get("NO_WINDNINJA", "") == "")
    lats, lons, z, S, dx = _solver_grids()
    fields = spatial_fields(cp_xichang())
    Semit = _downsample(fields["S"], fields["glat"], fields["glon"], lats, lons)
    cgrid = _downsample(fields["c_grid_on_S"], fields["glat"], fields["glon"], lats, lons)
    h_ridge = fields["h_ridge"]
    tlat = np.linspace(lats[0], lats[-1], STORE); tlon = np.linspace(lons[0], lons[-1], STORE)
    LO, LA = np.meshgrid(tlon, tlat)

    cp = cp_xichang()
    wnd = drivers.era5_winds(cp).rename(columns={"datetime": "tn"})[["tn", "u10", "v10"]]
    blhd = drivers.blh(cp).rename(columns={"datetime": "tn"})[["tn", "blh_m"]]
    shape_cache: dict = {}

    def shape_for(sec, bb, u, v, b):
        key = (sec, bb)
        if key not in shape_cache:
            _, _, _, _, C = tt.solve_terrain(u, v, max(b, 30.0), lats, lons, z, S, dx)
            sh = np.clip(C / (C.mean() + 1e-9), 0.4, 4.0)
            shape_cache[key] = _downsample(sh, lats, lons, tlat, tlon)
        return shape_cache[key]

    # HEADLINE backbone = smooth VanD surface. (Tested an NTL+traffic emission
    # backbone: it ranks held-out stations better on the RAW surface (ρ 0.40→0.80)
    # but embedding it inflates the level monotonically with contrast — the vault
    # stations cluster in the high-emission core, yet real PM there is NOT elevated
    # (obs ≈ city mean). Emission ≠ concentration: the steep emission gradient
    # disperses to a ~1.1× PM gradient, so the smooth field is the faithful product.
    # `_emission_backbone` retained as the documented scenario.)
    Se = _downsample(fields["S"], fields["glat"], fields["glon"], tlat, tlon)
    cg = _downsample(fields["c_grid_on_S"], fields["glat"], fields["glon"], tlat, tlon)
    px = STORE * STORE

    for y in YEARS:
        T = pd.read_parquet(OUT / f"T_{CITY}_hourly_{y}.parquet")
        B = pd.read_parquet(OUT / f"B_background_hourly_{y}_{CITY}.parquet")[["datetime_utc", "B"]]
        T["tn"] = pd.to_datetime(T.datetime_utc).dt.tz_localize(None)
        B["tn"] = pd.to_datetime(B.datetime_utc).dt.tz_localize(None)
        T = T.sort_values("tn")
        T = pd.merge_asof(T, wnd.sort_values("tn"), on="tn", direction="nearest")
        T = pd.merge_asof(T, blhd.sort_values("tn"), on="tn", direction="nearest")
        T = pd.merge_asof(T, B.sort_values("tn")[["tn", "B"]], on="tn", direction="nearest")
        # precompute per-hour scalars (vectorised)
        T["spd"] = np.maximum(np.hypot(T.u10, T.v10), 0.3)
        T["lh"] = (pd.to_datetime(T.datetime_utc, utc=True).dt.tz_convert(TZ)).dt.hour
        T["e"] = e_at(T.lh.values)
        T["a"] = np.clip(T.e * 18.0 / (T.spd * np.maximum(T.blh_m, 50.0)) * 50.0, 0, 0.5)
        T["sec"] = (((np.degrees(np.arctan2(T.u10, T.v10)) + 180) % 360) // 22.5).astype(int)
        T["bb"] = np.digitize(T.blh_m, BLH_EDGES)
        T["w"] = np.clip((h_ridge - T.blh_m) / h_ridge, 0, 1)
        f4 = np.empty((len(T) * px, 3), "f4"); ad = np.empty((len(T) * px, 5), "f4")
        times = np.empty(len(T) * px, dtype="datetime64[ns]")
        tvals = pd.to_datetime(T.datetime_utc).dt.tz_localize(None).values
        Se_p = np.ones_like(Se) if ABL == "no_emission" else Se
        for i, r in enumerate(T.itertuples(index=False)):
            if ABL_ADD_ONLY:
                A = 1.0                                            # no wind solve needed
            else:
                sh = shape_for(r.sec, r.bb, r.u10, r.v10, r.blh_m)
                A = 1.0 + r.a * (sh - 1.0); A = A / A.mean()
                if ABL == "no_winds":
                    A = 1.0
            M = 1.0 if ABL == "no_terrain" else (1.0 + XKAPPA * r.w * cg)
            Psm = (Se_p * M)
            Psm = np.ones(px) if ABL == "no_pattern" else (Psm / Psm.mean()).ravel()
            P4 = (Se_p * M * A)
            P4 = np.ones(px) if ABL == "no_pattern" else (P4 / P4.mean()).ravel()
            Bv = r.B; sl = slice(i * px, (i + 1) * px)
            f4[sl, 0] = r.T_q05 * P4; f4[sl, 1] = r.T_q50 * P4; f4[sl, 2] = r.T_q95 * P4
            ad[sl, 0] = np.clip(Bv + (r.T_q05 - Bv) * Psm, 0, None)
            ad[sl, 1] = Bv + (r.T_q50 - Bv) * Psm; ad[sl, 2] = Bv + (r.T_q95 - Bv) * Psm
            ad[sl, 3] = Bv * 1.25 + (r.T_q50 - Bv * 1.25) * Psm
            ad[sl, 4] = Bv * 0.70 + (r.T_q50 - Bv * 0.70) * Psm
            times[sl] = tvals[i]
        latcol = np.tile(LA.ravel(), len(T)); loncol = np.tile(LO.ravel(), len(T))
        if not ABL_ADD_ONLY:      # 4factor only meaningful when winds/timing are live
            pd.DataFrame({"time": times, "lat": latcol, "lon": loncol,
                          "pm25_q05": f4[:, 0], "pm25_q50": f4[:, 1], "pm25_q95": f4[:, 2]}
                         ).to_parquet(OUT / f"{CITY}_decomp_predictions_{y}_4factor{SUF}.parquet", index=False)
        pd.DataFrame({"time": times, "lat": latcol, "lon": loncol,
                      "pm25_q05": ad[:, 0], "pm25_q50": ad[:, 1], "pm25_q95": ad[:, 2],
                      "pm25_blo": ad[:, 3], "pm25_bhi": ad[:, 4]}
                     ).to_parquet(OUT / f"{CITY}_decomp_predictions_{y}_additive_v2{SUF}.parquet", index=False)
        print(f"  {y}: additive_v2 basin {ad[:,1].mean():.2f}  ({len(T):,} hr × {STORE}² px, "
              f"{len(shape_cache)} cached solves)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all")
    ap.add_argument("--city", default="xichang")
    a = ap.parse_args()
    _setup(a.city)
    stages = (["static", "tt", "bt", "field"] if a.stage == "all" else a.stage.split(","))
    if "static" in stages:
        print("=== STATIC ==="); build_static()
    if "tt" in stages:
        print("=== T(t) ==="); build_T()
    if "bt" in stages:
        print("=== B(t) ==="); build_B()
    if "field" in stages:
        print("=== FIELD (smooth → 4factor → additive_v2) ==="); build_field()
    print(f"\n→ {OUT}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
