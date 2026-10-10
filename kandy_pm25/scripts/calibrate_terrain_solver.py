"""Calibrate the deterministic terrain transport solver on PVAF v2 valley analogues.

The terrain solver (src/stage1_satml/decomp/terrain_transport.py) has ~5 hand-set
dimensionless params (K0, DRAIN, BLOCK, SLOPE_K, BLH_REF). Kandy has no spatial
ground truth to fit them. The PVAF v2 valley-grade core — Xichang, Bazhou,
Kathmandu, Medellin, Chiang Mai — are DENSELY MONITORED valleys in Kandy's regime;
their station networks are the ground truth Kandy lacks.

Method (physics fixed, params only — user choice 2026-06-01):
  per city: build delta_z (confinement) + VIIRS-NTL (source) grid -> run solver
  under a representative STABLE-CALM condition -> sample predicted C at each
  station -> SPATIAL correlation vs observed per-station mean PM2.5.
Objective = mean spatial Spearman r across cities (rank-based: robust to the
solver's relative-scale output). Phase 1 = default params (does the physics have
cross-city skill at all?). Phase 2 = optimise the shared params.

Run: python scripts/calibrate_terrain_solver.py [--optimize]
Output: data/processed/decomp/terrain_calibration.json + console report.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator
from scipy.stats import pearsonr, spearmanr

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src.stage1_satml.decomp.terrain_transport import solve_terrain, DEFAULT_PARAMS

PINN = REPO / "data" / "processed" / "pinn_inputs"
ST = REPO / "data" / "processed" / "stage2"
OUT = REPO / "data" / "processed" / "decomp"

NGRID = 48                      # solver grid (n x n); sparse solve is fast
STABLE_BLH = 250.0              # representative stable BLH (terrain imprints pattern)
STABLE_WIND = 0.5              # near-calm: pattern = source + drainage + confinement

# Selection by TERRAIN SKILL: a city is learnable only if the deterministic terrain
# physics actually explains its observed spatial gradient (Pearson r >= SKILL_MIN).
# Cities where terrain is irrelevant (Medellin: gotcha #23 gradient ANTI-correlated,
# suburban high stations cleaner; ChiangMai: regional biomass smoke) are USELESS for
# learning terrain physics and get dropped — not the model's fault, just not its job.
SKILL_MIN = 0.20

# All candidate cities with terrain_stations.npz + VIIRS-NTL + station PM on disk.
# slug -> (perstation parquet, pm column, station-id column)
CITIES = {
    "Xichang":    ("xichang_combined_perstation.parquet",   "pm25_raw", "station_name"),
    "Bazhou":     ("bazhou_combined_perstation.parquet",    "pm25_raw", "station_name"),
    "Baoji":      ("baoji_combined_perstation.parquet",     "pm25_raw", "station_name"),
    "Jincheng":   ("jincheng_combined_perstation.parquet",  "pm25_raw", "station_name"),
    "Taian":      ("taian_combined_perstation.parquet",     "pm25_raw", "station_name"),
    "Yichang":    ("yichang_combined_perstation.parquet",   "pm25_raw", "station_name"),
    "Chandigarh": ("chandigarh_combined_perstation.parquet","pm25_raw", "station_name"),
    "Kathmandu":  ("kathmandu_perstation_v13.parquet",      "pm25",     "station_id"),
    "Medellin":   ("medellin_perstation_v13.parquet",       "pm25",     "station_id"),
    "ChiangMai":  ("chiangmai_perstation_v13.parquet",      "pm25",     "station_id"),
    # 4 new valley cities (Expansion-E ingestion 2026-06-01; pass PVAF v2 regime)
    "Shiyan":     ("shiyan_valley_perstation.parquet",      "pm25_raw", "station_name"),
    "Panzhihua":  ("panzhihua_valley_perstation.parquet",   "pm25_raw", "station_name"),
    "Guiyang":    ("guiyang_valley_perstation.parquet",     "pm25_raw", "station_name"),
    "Zunyi":      ("zunyi_valley_perstation.parquet",       "pm25_raw", "station_name"),
}
SLUG = {"Xichang": "xichang", "Bazhou": "bazhou", "Baoji": "baoji",
        "Jincheng": "jincheng", "Taian": "taian", "Yichang": "yichang",
        "Chandigarh": "chandigarh", "Kathmandu": "kathmandu",
        "Medellin": "medellin", "ChiangMai": "chiangmai",
        "Shiyan": "shiyan", "Panzhihua": "panzhihua", "Guiyang": "guiyang",
        "Zunyi": "zunyi"}

# Final learnable set: 6 terrain-learnable v15 valleys + 4 new v2-passing valleys.
FINAL_TEN = ["Baoji", "Bazhou", "Chandigarh", "Xichang", "Taian", "Kathmandu",
             "Shiyan", "Panzhihua", "Guiyang", "Zunyi"]


def _axis_ascending(grid2d_lat, grid2d_lon, field):
    """Return 1D ascending lat/lon axes and field oriented to match."""
    lat = grid2d_lat[:, 0].astype(float)
    lon = grid2d_lon[0, :].astype(float)
    if lat[0] > lat[-1]:
        lat, field = lat[::-1], field[::-1, :]
    if lon[0] > lon[-1]:
        lon, field = lon[:, ::-1], field[:, ::-1]
    return lat, lon, field


def load_city(slug):
    """Build (lats, lons, delta_z, S, dx) on an NGRID x NGRID grid over the terrain
    footprint, plus the observed (lat, lon, pm) station vectors."""
    t = np.load(PINN / f"{slug}_terrain_stations.npz")
    tlat, tlon, dz = _axis_ascending(t["lat_grid"], t["lon_grid"], t["delta_z"].astype(float))
    dz = np.nan_to_num(dz, nan=0.0)          # no-data DEM patches -> neutral (flat)
    nt = np.load(PINN / f"{slug}_viirs_ntl_stations.npz")
    nlat, nlon, NL = _axis_ascending(nt["lat_grid"], nt["lon_grid"], nt["NTL"].astype(float))
    NL = np.nan_to_num(NL, nan=0.0)

    lat_min, lat_max = float(tlat.min()), float(tlat.max())
    lon_min, lon_max = float(tlon.min()), float(tlon.max())
    lats = np.linspace(lat_min, lat_max, NGRID)
    lons = np.linspace(lon_min, lon_max, NGRID)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    pts = np.stack([LA.ravel(), LO.ravel()], 1)

    dz_g = RegularGridInterpolator((tlat, tlon), dz, bounds_error=False,
                                   fill_value=None)(pts).reshape(NGRID, NGRID)
    S_g = RegularGridInterpolator((nlat, nlon), NL, bounds_error=False,
                                  fill_value=0.0)(pts).reshape(NGRID, NGRID)
    S_g = np.clip(S_g, 0, None); S_g /= (S_g.max() + 1e-9)
    dx = (lat_max - lat_min) * 111000.0 / (NGRID - 1)
    return lats, lons, dz_g, S_g, dx, (lat_min, lat_max, lon_min, lon_max)


def load_stations(parquet, pm_col, id_col):
    df = pd.read_parquet(ST / parquet, columns=[id_col, "lat", "lon", pm_col])
    df = df.dropna(subset=["lat", "lon", pm_col])
    g = df.groupby(id_col).agg(lat=("lat", "median"), lon=("lon", "median"),
                               pm=(pm_col, "mean")).reset_index()
    return g


def city_skill(grids, stns, P):
    """Spatial Pearson + Spearman between solver C and observed PM at stations."""
    lats, lons, dz, S, dx, bbox = grids
    _, _, _, _, C = solve_terrain(STABLE_WIND, 0.0, STABLE_BLH, lats, lons, dz, S, dx, P=P)
    rgi = RegularGridInterpolator((lats, lons), C, bounds_error=False, fill_value=None)
    la = np.clip(stns["lat"].values, bbox[0], bbox[1])
    lo = np.clip(stns["lon"].values, bbox[2], bbox[3])
    cpred = rgi(np.stack([la, lo], 1))
    obs = stns["pm"].values
    ok = np.isfinite(cpred) & np.isfinite(obs)
    if ok.sum() < 4 or np.std(cpred[ok]) < 1e-9:
        return None, None, int(ok.sum())
    return (float(pearsonr(cpred[ok], obs[ok])[0]),
            float(spearmanr(cpred[ok], obs[ok])[0]), int(ok.sum()))


def evaluate(cache, P, verbose=False, subset=None):
    rows, rs = [], []
    for name, (grids, stns) in cache.items():
        pr, sr, n = city_skill(grids, stns, P)
        rows.append((name, pr, sr, n))
        if sr is not None and (subset is None or name in subset):
            rs.append(sr)
        if verbose:
            ps = f"{pr:+.3f}" if pr is not None else "  n/a"
            ss = f"{sr:+.3f}" if sr is not None else "  n/a"
            ctl = "" if (subset is None or name in subset) else "  (control)"
            print(f"  {name:<11} n_stn={n:<3} pearson={ps}  spearman={ss}{ctl}")
    mean_sr = float(np.mean(rs)) if rs else -1.0
    return mean_sr, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--optimize", action="store_true")
    args = ap.parse_args()

    print("Loading candidate city grids + station networks ...")
    cache = {}
    for name, (pq, pmc, idc) in CITIES.items():
        grids = load_city(SLUG[name])
        stns = load_stations(pq, pmc, idc)
        cache[name] = (grids, stns)
        print(f"  {name:<11} grid {NGRID}x{NGRID}  dx={grids[4]:.0f}m  "
              f"delta_z[{grids[2].min():.0f},{grids[2].max():.0f}]  n_stn={len(stns)}")

    print(f"\n=== PHASE 1: terrain-skill screen (default params, stable-calm "
          f"BLH {STABLE_BLH}, wind {STABLE_WIND}) ===")
    _, base_rows = evaluate(cache, DEFAULT_PARAMS, verbose=True)

    # Auto-screen (transparency) + the locked FINAL_TEN calibration set
    ranked = sorted(base_rows, key=lambda r: -(r[1] if r[1] is not None else -9))
    auto = [r[0] for r in ranked if r[1] is not None and r[1] >= SKILL_MIN]
    learnable = [c for c in FINAL_TEN if c in cache]
    print(f"\n  AUTO-SCREEN (Pearson >= {SKILL_MIN}): {auto}")
    print(f"  FINAL TEN (6 v15 + 4 new v2-passing valleys): {learnable}")

    result = {"skill_screen": {r[0]: {"pearson": r[1], "spearman": r[2], "n": r[3]}
                               for r in base_rows},
              "auto_screen": auto, "final_ten": learnable, "skill_min": SKILL_MIN}

    if args.optimize and learnable:
        print(f"\n=== PHASE 2: optimise K0, DRAIN, SLOPE_K on the {len(learnable)} "
              f"learnable cities ===")
        from scipy.optimize import minimize
        keys = ["K0", "DRAIN", "SLOPE_K"]   # BLOCK (calm) + BLH_REF (degenerate) fixed
        x0 = np.log([DEFAULT_PARAMS[k] for k in keys])

        def neg(x):
            P = {**DEFAULT_PARAMS, **{k: float(np.exp(v)) for k, v in zip(keys, x)}}
            sr, _ = evaluate(cache, P, subset=learnable)
            return -sr

        base_sr, _ = evaluate(cache, DEFAULT_PARAMS, subset=learnable)
        res = minimize(neg, x0, method="Nelder-Mead",
                       options={"maxiter": 120, "xatol": 0.05, "fatol": 0.005})
        Pbest = {**DEFAULT_PARAMS, **{k: float(np.exp(v)) for k, v in zip(keys, res.x)}}
        best_sr, best_rows = evaluate(cache, Pbest, verbose=True, subset=learnable)
        print(f"  MEAN spatial Spearman r over FINAL_TEN (calibrated) = {best_sr:+.3f}"
              f"  (default {base_sr:+.3f})")
        lp = [r[1] for r in best_rows if r[0] in learnable and r[1] is not None]
        print(f"  cross-city Pearson: mean {np.mean(lp):+.3f} +/- {np.std(lp):.3f} "
              f"(n={len(lp)} valleys; spread = transfer UQ)")
        print(f"  CALIBRATED PARAMS: " +
              ", ".join(f"{k}={Pbest[k]:.3f}" for k in keys))
        result["phase2_calibrated"] = {
            "mean_spearman": best_sr, "mean_spearman_default": base_sr,
            "per_city": {r[0]: {"pearson": r[1], "spearman": r[2], "n": r[3]} for r in best_rows},
            "params": {k: Pbest[k] for k in DEFAULT_PARAMS}}

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "terrain_calibration.json").write_text(json.dumps(result, indent=2))
    print(f"\nWrote {OUT / 'terrain_calibration.json'}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
