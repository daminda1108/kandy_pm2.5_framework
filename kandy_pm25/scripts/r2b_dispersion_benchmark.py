"""r2b_dispersion_benchmark.py -- the dispersion step against its simpler alternatives on IDENTICAL sites
(2026-10-10, second external review, item 9; ledger F.126). EXPLORATORY.

Extends R2 (r2_score_atransport.py, registered OSF bkpyr): the same ten analogue cities, the same stations,
the same solver call. Three arms are scored on exactly the same station set per city:
  S      the raw road-traffic emission surface (undispersed)
  C      the delivered surface: S carried through the terrain advection-dispersion solver (A_transport)
  BU     the best single free spatial predictor of the panel tests: ESA WorldCover 2021 built-up fraction
         within 1 km of each station (Earth Engine), which needs no model at all
For each arm: Spearman rank correlation with station means, and the predicted contrast (P90/P10 of the
arm's values at the stations) against the observed contrast (P90/P10 of station means). BU's contrast is
not in concentration units and is not reported.

Out: data/processed/modular/r2b_dispersion_benchmark.csv
"""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
from calibrate_terrain_solver import CITIES, SLUG, FINAL_TEN, STABLE_WIND, STABLE_BLH, load_city, load_stations  # noqa: E402
from r2_score_atransport import rank_at_stations  # noqa: E402
from scipy.interpolate import RegularGridInterpolator  # noqa: E402
from src.stage1_satml.decomp.terrain_transport import solve_terrain  # noqa: E402

OUT = REPO / "data" / "processed" / "modular" / "r2b_dispersion_benchmark.csv"
BUFFER_M = 1000


def builtup(ee, stns: pd.DataFrame) -> np.ndarray:
    wc = ee.ImageCollection("ESA/WorldCover/v200").first().eq(50).rename("bu")
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([float(r.lon), float(r.lat)]).buffer(BUFFER_M),
                                          {"i": int(i)}) for i, r in enumerate(stns.itertuples())])
    res = wc.reduceRegions(fc, ee.Reducer.mean(), scale=10).getInfo()["features"]
    v = np.full(len(stns), np.nan)
    for f in res:
        v[f["properties"]["i"]] = f["properties"].get("mean", np.nan)
    return v


def values_at(lats, lons, F, stns, bbox):
    rgi = RegularGridInterpolator((lats, lons), F, bounds_error=False, fill_value=None)
    la = np.clip(stns["lat"].values, bbox[0], bbox[1]); lo = np.clip(stns["lon"].values, bbox[2], bbox[3])
    return rgi(np.stack([la, lo], 1))


def p90p10(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    lo = np.percentile(x, 10)
    return float(np.percentile(x, 90) / lo) if lo > 0 else np.nan


def main():
    import ee
    ee.Initialize(project="kandypinn")
    rows = []
    for name in FINAL_TEN:
        try:
            fn, pm_col, id_col = CITIES[name]
            lats, lons, dz, S, dx, bbox = load_city(SLUG[name])
            stns = load_stations(REPO / "data" / "processed" / "stage2" / fn, pm_col, id_col).reset_index(drop=True)
        except Exception as e:
            print(f"  {name}: skipped ({str(e)[:50]})"); continue
        _, _, _, _, C = solve_terrain(STABLE_WIND, 0.0, STABLE_BLH, lats, lons, dz, S, dx)
        vS, vC = values_at(lats, lons, S, stns, bbox), values_at(lats, lons, C, stns, bbox)
        vB = builtup(ee, stns)
        obs = stns["pm"].values
        ok = np.isfinite(vS) & np.isfinite(vC) & np.isfinite(vB) & np.isfinite(obs)
        if ok.sum() < 4:
            print(f"  {name}: < 4 common sites"); continue
        r = lambda v: float(spearmanr(v[ok], obs[ok])[0]) if np.std(v[ok]) > 1e-12 else np.nan
        rS0, _ = rank_at_stations(lats, lons, S, stns, bbox)
        rows.append(dict(city=name, n=int(ok.sum()), rho_S=r(vS), rho_C=r(vC), rho_BU=r(vB),
                         contrast_obs=p90p10(obs[ok]), contrast_S=p90p10(vS[ok]), contrast_C=p90p10(vC[ok]),
                         parity_rho_S_vs_R2=float(r(vS) - rS0) if np.isfinite(rS0) else np.nan))
        print(f"  {name:<11} n={ok.sum():>3}  S {rows[-1]['rho_S']:+.3f}  C {rows[-1]['rho_C']:+.3f}  "
              f"BU {rows[-1]['rho_BU']:+.3f}  contrast obs {rows[-1]['contrast_obs']:.2f} "
              f"S {rows[-1]['contrast_S']:.2f} C {rows[-1]['contrast_C']:.2f}", flush=True)
    d = pd.DataFrame(rows)
    med = d.drop(columns=["city"]).median(numeric_only=True)
    paired = {"C_minus_S": (d.rho_C - d.rho_S), "BU_minus_S": (d.rho_BU - d.rho_S), "BU_minus_C": (d.rho_BU - d.rho_C)}
    extra = {}
    for k, v in paired.items():
        v = v.dropna()
        extra[f"{k}_median"] = float(v.median()); extra[f"{k}_wins"] = int((v > 0).sum()); extra[f"{k}_n"] = len(v)
    d = pd.concat([d, pd.DataFrame([{"city": "MEDIAN", **med.to_dict(), **extra}])], ignore_index=True)
    tmp = OUT.with_suffix(".tmp.csv"); d.to_csv(tmp, index=False); os.replace(tmp, OUT)
    print(d.tail(1).T.to_string())


if __name__ == "__main__":
    main()
