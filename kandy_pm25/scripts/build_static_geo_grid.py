"""build_static_geo_grid.py -- STATIC_GEO as a city WITHOUT monitors would have it (ladder v2, E4).

v1's STATIC_GEO is the mean of the 60 LUR predictors over each city's monitoring sites, a third of
which are the held-out stations that score the city (verification B1). A city with no monitors has
no sites. v2 describes the city by a random sample of points inside its URBAN CENTRE:

  urban centre = the connected patch of GHSL degree-of-urbanisation class 30 ("urban centre",
                 JRC/GHSL/P2023A/GHS_SMOD_V2-0, epoch 2020, 1 km) that contains the city centroid,
                 else the nearest such patch within 30 km; if none, class >= 23 (dense urban
                 cluster), then >= 21 (suburban). The level used is recorded per city.
  points       = N random points inside that patch (fixed seed).
  features     = the SAME 60 predictors, by the SAME code: build_lur_predictors.gee_city (rasters
                 at 100/300/1000/2400 m) and spatial_curve_predictors.osm_city_tiled (OSM roads by
                 class within 50-1000 m, distance to the nearest major road).
  city value   = mean over the points.

Usage: python scripts/build_static_geo_grid.py [--n 40] [--cities a,b,...] [--stage pts|gee|osm|merge|all]
Out:   data/processed/modular/geo_grid/{city}_{pts,gee,osm}.csv, static_geo_grid.csv
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
MOD = REPO / "data" / "processed" / "modular"
GD = MOD / "geo_grid"
SMOD = "JRC/GHSL/P2023A/GHS_SMOD_V2-0"
LEVELS = (30, 23, 21)           # urban centre, dense urban cluster, suburban


def centroids(panel: str = "discovery") -> pd.DataFrame:
    if panel == "confirmation":
        P = pd.read_csv(MOD / "confirmation" / "confirmation_panel.csv")
        return P.rename(columns={"cid": "city"})[["city", "lat", "lon", "band", "src"]]
    from src.modular.city_meta import city_meta
    return city_meta()[["city", "lat", "lon", "band", "src"]]


def points_for(city, lat, lon, n, seed=20260925):
    import ee
    img = ee.ImageCollection(SMOD).filterDate("2020-01-01", "2021-01-01").first().select(0)
    pt = ee.Geometry.Point([float(lon), float(lat)])
    region = pt.buffer(30000)
    for lvl in LEVELS:
        mask = img.gte(lvl).selfMask() if lvl < 30 else img.eq(30).selfMask()
        vec = mask.reduceToVectors(geometry=region, scale=1000, geometryType="polygon",
                                   eightConnected=True, maxPixels=1e9, bestEffort=True)
        n_poly = vec.size().getInfo()
        if n_poly == 0:
            continue
        inside = vec.filterBounds(pt)
        poly = (inside.first() if inside.size().getInfo() > 0 else
                vec.map(lambda f: f.set("d", f.geometry().distance(pt, 10)))
                   .sort("d").first())
        geom = ee.Feature(poly).geometry()
        area = geom.area(10).divide(1e6).getInfo()
        rp = ee.FeatureCollection.randomPoints(region=geom, points=n, seed=seed, maxError=10)
        coords = [f["geometry"]["coordinates"] for f in rp.getInfo()["features"]]
        d = pd.DataFrame(coords, columns=["lon", "lat"])
        d["city"], d["level"], d["area_km2"] = city, lvl, area
        return d
    raise RuntimeError(f"{city}: no urban patch at any level within 30 km")


def _write(df, path):
    tmp = path.with_suffix(".csv.tmp"); df.to_csv(tmp, index=False); os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--cities", default="")
    ap.add_argument("--stage", choices=("pts", "gee", "osm", "merge", "all"), default="all")
    ap.add_argument("--panel", choices=("discovery", "confirmation"), default="discovery")
    a = ap.parse_args()
    global GD
    if a.panel == "confirmation":
        GD = MOD / "confirmation" / "geo_grid"
    GD.mkdir(parents=True, exist_ok=True)
    C = centroids(a.panel)
    if a.cities:
        C = C[C.city.isin(a.cities.split(","))]
    stages = ("pts", "gee", "osm", "merge") if a.stage == "all" else (a.stage,)

    if {"pts", "gee"} & set(stages):
        import ee
        ee.Initialize(project="kandypinn")
    fails = []
    for r in C.itertuples():
        fp, fg, fo = (GD / f"{r.city}_{s}.csv" for s in ("pts", "gee", "osm"))
        try:
            if "pts" in stages and not fp.exists():
                _write(points_for(r.city, r.lat, r.lon, a.n), fp)
                print(f"  {r.city:<9} points ok", flush=True)
            if "gee" in stages and fp.exists() and not fg.exists():
                import build_lur_predictors as blp
                _write(blp.gee_city(pd.read_csv(fp)), fg)
                print(f"  {r.city:<9} gee ok", flush=True)
            if "osm" in stages and fp.exists() and not fo.exists():
                import spatial_curve_predictors as scp
                t0 = time.time()
                _write(scp.osm_city_tiled(pd.read_csv(fp)), fo)
                print(f"  {r.city:<9} osm ok ({(time.time() - t0) / 60:.1f} min)", flush=True)
        except Exception as e:                                             # noqa: BLE001
            fails.append((r.city, f"{type(e).__name__}: {e}"))
            print(f"  {r.city:<9} FAILED {type(e).__name__}: {str(e)[:120]}", flush=True)

    if "merge" in stages:
        geo_cols = [c for c in pd.read_csv(MOD / "bud0_static_geo.csv").columns
                    if c not in ("city", "geo_n_stations")]
        rows = []
        for r in centroids(a.panel).itertuples():
            fp, fg, fo = (GD / f"{r.city}_{s}.csv" for s in ("pts", "gee", "osm"))
            if not (fp.exists() and fg.exists() and fo.exists()):
                continue
            g, o, pts = pd.read_csv(fg), pd.read_csv(fo), pd.read_csv(fp)
            m = pd.concat([g, o.drop(columns=[c for c in o.columns if c in g.columns])], axis=1)
            row = {"city": r.city, **m[geo_cols].mean().to_dict(),
                   "grid_points": len(m), "grid_level": int(pts.level.iloc[0]),
                   "grid_area_km2": float(pts.area_km2.iloc[0])}
            rows.append(row)
        G = pd.DataFrame(rows)
        _write(G, MOD / ("static_geo_grid.csv" if a.panel == "discovery"
                         else "confirmation/static_geo_grid.csv"))
        print(f"\nmerged {len(G)} cities -> static_geo_grid.csv; levels "
              f"{G.grid_level.value_counts().to_dict()}")
    if fails:
        print(f"\n{len(fails)} failures: {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
