"""Build the FINAL four-factor model output: apply the emission-timed transport overlay
A_transport(x,y,t) to the smooth T·S·M predictions, producing the shipped product.

  PM_4factor(x,y,t) = PM_smooth(x,y,t) · A_transport(x,y,t)
  A_transport = normalise(1 + a(t)·(shape_bin(x,y) − 1)),  spatial mean 1 each hour
  a(t) = clip( e_norm(local_hour) · 18 / (wind·BLH), 0, 0.5 )     [emission × stability]

Efficient: the terrain advection–dispersion SHAPE is solved once per (wind-sector × BLH
bin) and cached (~50 solves); the hourly application is then vectorised. q05/q50/q95 are
all scaled by the same A (the overlay redistributes the level, preserving the basin mean).

Output: data/processed/decomp/kandy_decomp_predictions_{year}_4factor.parquet
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src.stage1_satml.decomp.terrain_transport import solve_terrain, load_grids
from src.stage1_satml.decomp.emission_profile import e_at

DEC = REPO / "data" / "processed" / "decomp"
YEARS = range(2019, 2024)
BLH_EDGES = np.array([0, 100, 175, 275, 400, 600, 1000, 5000.0])

# NOTE (2026-07-10): an emission-timing spatial sharpening term (rush-hour core boost
# tied to S_traffic) was TESTED here and REJECTED on evidence — it pushed the core
# diurnal amplitude further ABOVE the observed FECT floor (1.30 vs obs 0.72), moved the
# core/ridge amplitude ratio away from observed (0.41 vs 0.67), barely changed the phase
# correlation, and reintroduced core<periphery inversions off-peak. Kandy's gentle relief
# already shows an attenuated-same-phase ridge (obs floor/ridge amp 0.72/0.48), which the
# unmodified model reproduces (core/ridge 0.92/0.57). Left unmodified. See webapp_v2 plan.
_LATS, _LONS, _Z, _S, _DX = load_grids()
_SHAPE_CACHE: dict = {}


def _shape16(u, v, blh, lats16, lons16):
    _, _, _, _, C = solve_terrain(u, v, blh, _LATS, _LONS, _Z, _S, _DX)
    sh = np.clip(C / (C.mean() + 1e-9), 0.4, 4.0)
    rgi = RegularGridInterpolator((_LATS, _LONS), sh)
    LA, LO = np.meshgrid(np.clip(lats16, _LATS.min(), _LATS.max()),
                         np.clip(lons16, _LONS.min(), _LONS.max()), indexing="ij")
    return rgi(np.stack([LA.ravel(), LO.ravel()], 1)).reshape(16, 16)


def _met_table(year):
    g = pd.read_parquet(REPO / f"data/processed/stage1_v3/inference_grid_{year}_s12451.parquet",
                        columns=["datetime_utc", "u10", "v10", "blh_m", "wind_speed_10m"])
    t = pd.to_datetime(g.datetime_utc, utc=True)
    g["time"] = t
    g["lh"] = t.dt.tz_convert("Asia/Colombo").dt.hour
    g["sector"] = (np.round(np.degrees(np.arctan2(g.u10, g.v10)) / 45.0).astype(int) % 8)
    g["bbin"] = np.clip(np.digitize(g.blh_m, BLH_EDGES) - 1, 0, len(BLH_EDGES) - 2)
    return g.set_index("time")


def _shape_for(sector, bbin, umean, vmean, blhmean, lats16, lons16):
    key = (int(sector), int(bbin))
    if key not in _SHAPE_CACHE:
        _SHAPE_CACHE[key] = _shape16(umean, vmean, blhmean, lats16, lons16)
    return _SHAPE_CACHE[key]


def build_year(year, lats16, lons16, bin_means):
    pred = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}.parquet")
    pred = pred.sort_values(["time", "lat", "lon"]).reset_index(drop=True)
    pred["time"] = pd.to_datetime(pred["time"], utc=True)
    times = pred["time"].drop_duplicates().to_numpy()
    nt = len(times)
    assert len(pred) == nt * 256, f"{year}: {len(pred)} != {nt}*256"
    met = _met_table(year).reindex(times)

    A_cube = np.empty((nt, 16, 16), float)
    for i, t in enumerate(times):
        r = met.iloc[i]
        bm = bin_means[(int(r.sector), int(r.bbin))]
        shape = _shape_for(r.sector, r.bbin, bm[0], bm[1], bm[2], lats16, lons16)
        amp = np.clip(e_at(r.lh) * 18.0 / (max(r.wind_speed_10m, 0.3) * max(r.blh_m, 1)), 0, 0.5)
        A = np.clip(1.0 + amp * (shape - 1.0), 0.5, 2.8)
        A_cube[i] = A / A.mean()
    Aflat = A_cube.reshape(nt * 256)
    for col in ("pm25_q05", "pm25_q50", "pm25_q95"):
        pred[col] = (pred[col].to_numpy() * Aflat).astype(np.float32)
    out = DEC / f"kandy_decomp_predictions_{year}_4factor.parquet"
    pred.to_parquet(out, index=False)
    cc = pred.groupby(["lat", "lon"])["pm25_q50"].mean()
    LA, LO = np.meshgrid(np.sort(pred.lat.unique()), np.sort(pred.lon.unique()), indexing="ij")
    Z = cc.unstack("lon").values
    d = np.hypot(LA - 7.2906, LO - 80.6337)
    ce = Z[d <= np.percentile(d, 20)].mean() / Z[d >= np.percentile(d, 80)].mean()
    print(f"  {year}: basin {pred.pm25_q50.mean()*0+Z.mean():.1f}  annual core/edge {ce:.2f}×  -> {out.name}")


def main():
    # one shape lookup, built from per-bin mean met pooled over all years
    pool = pd.concat([_met_table(y).reset_index() for y in YEARS], ignore_index=True)
    lats16 = np.sort(pd.read_parquet(DEC / "kandy_decomp_predictions_2023.parquet",
                                     columns=["lat"]).lat.unique())
    lons16 = np.sort(pd.read_parquet(DEC / "kandy_decomp_predictions_2023.parquet",
                                     columns=["lon"]).lon.unique())
    bin_means = {}
    for (s, b), g in pool.groupby(["sector", "bbin"]):
        bin_means[(int(s), int(b))] = (g.u10.mean(), g.v10.mean(), g.blh_m.mean())

    print(f"Building 4-factor predictions; {len(bin_means)} (sector×BLH) shape bins.")
    for y in YEARS:
        build_year(y, lats16, lons16, bin_means)
    print(f"Cached {len(_SHAPE_CACHE)} terrain solves total.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
