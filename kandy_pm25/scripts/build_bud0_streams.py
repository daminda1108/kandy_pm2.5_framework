"""build_bud0_streams.py -- STATIC_GEO and SATELLITE_LEVEL at city level, for the re-validated Bud0.

Pre-registration: docs/prereg_revalidation_2026-08-23.md  |  OSF: https://osf.io/g6hqb/
Trigger: F.84 -- the scored Bud0 used one of the three streams its budget admits.

STATIC_GEO      city-level means of the existing 636-station LUR predictor set, aggregated over
                each city's own stations. Declared in the registration as a convenience sample of
                the city's geography rather than the city's geography.
SATELLITE_LEVEL GHAP annual PM2.5 (1 km) at the city centroid. Band `b1` is ALREADY ug/m3 --
                do NOT apply a 0.1 scale (gotcha #50).

Usage:  python scripts/build_bud0_streams.py [--geo] [--sat]
Out:    data/processed/modular/bud0_static_geo.csv
        data/processed/modular/bud0_satellite_level.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "data" / "processed" / "modular"
GHAP = "projects/sat-io/open-datasets/GHAP/GHAP_Y1K_PM25"


def build_geo() -> pd.DataFrame:
    d = pd.read_csv(MOD / "lur_predictors.csv")
    drop = {"city", "band", "src", "station_id", "lat", "lon", "pm"}
    feats = [c for c in d.columns if c not in drop]
    g = d.groupby("city")[feats].mean()
    g["geo_n_stations"] = d.groupby("city").size()
    # terrain relief is not in the LUR set; add the station-spread of elevation proxies we do have
    g = g.reset_index()
    g["city"] = g.city.astype(str)
    out = MOD / "bud0_static_geo.csv"
    g.to_csv(out, index=False)
    print(f"STATIC_GEO: {len(g)} cities x {len(feats)} predictors -> {out.name}")
    print(f"  e.g. {feats[:6]} ...")
    return g


def build_sat(years=(2019, 2020, 2021, 2022)) -> pd.DataFrame:
    import ee
    ee.Initialize(project="kandypinn")

    man = pd.read_csv(MOD / "openaq_manifest.csv")
    man = man[man.status == "OK"][["cluster", "lat", "lon"]]
    man["city"] = man.cluster.astype(str)
    smp = pd.read_csv(MOD / "validation_sample.csv")
    cn = smp[smp.src == "CNEMC"][["slug", "lat", "lon"]].rename(columns={"slug": "city"})
    cn["city"] = cn.city.astype(str)
    tgt = pd.concat([man[["city", "lat", "lon"]], cn], ignore_index=True).drop_duplicates("city")

    col = ee.ImageCollection(GHAP).filterDate(f"{min(years)}-01-01", f"{max(years)+1}-01-01")
    rows = []
    for i, r in enumerate(tgt.itertuples(), 1):
        try:
            pt = ee.Geometry.Point([float(r.lon), float(r.lat)]).buffer(5000)
            # b1 is ALREADY ug/m3 (gotcha #50): no scaling
            v = col.mean().select("b1").reduceRegion(
                ee.Reducer.mean(), pt, scale=1000, maxPixels=1e9).getInfo()
            lev = v.get("b1")
            rows.append(dict(city=r.city, sat_level=float(lev) if lev is not None else np.nan))
            print(f"  [{i:>2}/{len(tgt)}] {r.city:<10} sat_level={lev}")
        except Exception as e:
            rows.append(dict(city=r.city, sat_level=np.nan))
            print(f"  [{i:>2}/{len(tgt)}] {r.city:<10} FAILED {str(e)[:70]}")
    s = pd.DataFrame(rows)
    out = MOD / "bud0_satellite_level.csv"
    s.to_csv(out, index=False)
    ok = s.sat_level.notna().sum()
    print(f"\nSATELLITE_LEVEL: {ok}/{len(s)} cities -> {out.name}")
    print(f"  R-G5 gate (>=45 cities): {'PASS' if ok >= 45 else 'FAIL -- name the shortfall'}")
    if ok < len(s):
        print("  missing:", list(s[s.sat_level.isna()].city))
    return s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", action="store_true")
    ap.add_argument("--sat", action="store_true")
    a = ap.parse_args()
    if not (a.geo or a.sat):
        a.geo = a.sat = True
    if a.geo:
        build_geo()
    if a.sat:
        build_sat()
