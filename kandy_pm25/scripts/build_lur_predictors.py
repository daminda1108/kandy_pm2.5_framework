"""build_lur_predictors.py — R1 of the 2026-08-19 remediation plan.

Builds a proper land-use-regression predictor set at every station in the 47-city frame.

WHY. Our spatial tests reached rho ~ 0.2 with four proxies at two radii and NO ROADS, while
published LUR explains 43-83% of within-city PM2.5 variance. The global NO2 LUR names "major
roads within 100 m" as its strongest predictor, and NDVI / tree cover / water as the strongest
negative ones. The three surfaces we tested all shared the same missing predictor set, so their
agreement was not independent confirmation. This fixes the instrumentation before any further
conclusion is drawn.

TWO STAGES, both resumable per city:
  gee   NDVI, tree cover, water occurrence, ESA land-cover fractions, GHS built volume
        (total and non-residential), population, night lights -- each at 100/300/1000/2400 m.
  osm   road length by class in 50/100/300/500/1000 m buffers, and distance to the nearest
        major road. One Overpass query per city bbox; buffers computed locally.

Radii follow the LUR literature (300/600/900/1200/2400/4800 m is typical; the small 50-100 m
road buffers matter most and are the ones we lacked entirely).

Usage:
  python scripts/build_lur_predictors.py --stage gee
  python scripts/build_lur_predictors.py --stage osm
Out:
  data/processed/modular/lur/{gee,osm}/{city}.csv  and  lur_predictors.csv (merged)
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "lur"

GEE_RADII = [100, 300, 1000, 2400]
ROAD_RADII = [50, 100, 300, 500, 1000]

# OSM highway classes, grouped as LUR conventionally does
ROAD_CLASSES = {
    "major": ("motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link"),
    "medium": ("secondary", "secondary_link", "tertiary", "tertiary_link"),
    "minor": ("residential", "unclassified", "living_street", "service"),
}
UA = {"User-Agent": "kandy-pm25-research/1.0 (academic; contact: 11daminda08@gmail.com)"}


def stations() -> pd.DataFrame:
    s = pd.read_csv(MOD / "spatial_proxy_stations.csv")
    return s[["city", "band", "src", "station_id", "lat", "lon", "pm"]].dropna(
        subset=["lat", "lon"])


# ── stage: GEE ────────────────────────────────────────────────────────────────────────────

def gee_city(g: pd.DataFrame) -> pd.DataFrame:
    import ee
    feats = [ee.Feature(ee.Geometry.Point([float(r.lon), float(r.lat)]), {"k": int(i)})
             for i, r in enumerate(g.itertuples())]
    fc = ee.FeatureCollection(feats)

    ndvi = (ee.ImageCollection("MODIS/061/MOD13A2").filterDate("2023-01-01", "2025-01-01")
            .select("NDVI").mean().multiply(0.0001).rename("ndvi"))
    tree = ee.Image("UMD/hansen/global_forest_change_2023_v1_11").select("treecover2000") \
        .rename("tree")
    water = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").unmask(0) \
        .rename("water")
    pop = ee.Image("JRC/GHSL/P2023A/GHS_POP/2020").select("population_count").rename("pop")
    bv = ee.Image("JRC/GHSL/P2023A/GHS_BUILT_V/2020")
    built = bv.select("built_volume_total").rename("built")
    nres = bv.select("built_volume_nres").rename("nres")
    ntl = (ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
           .filterDate("2023-01-01", "2025-01-01").select("avg_rad").mean().rename("ntl"))
    lc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map")
    # land-cover fractions that LUR uses: built-up (50), tree (10), grass/crop (30/40), water (80)
    lcb = (lc.eq(50).rename("lc_built")
           .addBands(lc.eq(10).rename("lc_tree"))
           .addBands(lc.eq(30).Or(lc.eq(40)).rename("lc_veg"))
           .addBands(lc.eq(80).rename("lc_water")))

    img = (ndvi.addBands(tree).addBands(water).addBands(pop).addBands(built)
           .addBands(nres).addBands(ntl).addBands(lcb).toFloat())

    out = g.reset_index(drop=True).copy()
    for rad in GEE_RADII:
        buf = fc.map(lambda f, r=rad: f.buffer(r))
        res = img.reduceRegions(collection=buf, reducer=ee.Reducer.mean(),
                                scale=max(30, rad // 10)).getInfo()
        vals = {}
        for f in res["features"]:
            p = f["properties"]
            vals[int(p["k"])] = p
        for b in ("ndvi", "tree", "water", "pop", "built", "nres", "ntl",
                  "lc_built", "lc_tree", "lc_veg", "lc_water"):
            out[f"{b}_{rad}"] = [vals.get(i, {}).get(b, np.nan) for i in range(len(out))]
    return out


# ── stage: OSM roads ──────────────────────────────────────────────────────────────────────

def _overpass(bbox, tries: int = 3):
    """Roads in a bbox. Overpass rejects requests without a User-Agent (gotcha #41)."""
    import urllib.request
    s, w, n, e = bbox
    q = (f"[out:json][timeout:180];way[highway~\"^(motorway|trunk|primary|secondary|"
         f"tertiary|residential|unclassified|living_street|service)"
         f"(_link)?$\"]({s},{w},{n},{e});out geom;")
    for t in range(tries):
        try:
            req = urllib.request.Request("https://overpass-api.de/api/interpreter",
                                         data=q.encode(), headers=UA)
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except Exception as e:
            if t == tries - 1:
                raise
            time.sleep(20 * (t + 1))
    return None


def _seg_len_km(a, b):
    r = 6371.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = p2 - p1
    dl = math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def osm_city(g: pd.DataFrame) -> pd.DataFrame:
    pad = 0.02
    bbox = (g.lat.min() - pad, g.lon.min() - pad, g.lat.max() + pad, g.lon.max() + pad)
    data = _overpass(bbox)
    ways = []
    for el in data.get("elements", []):
        tag = (el.get("tags") or {}).get("highway", "")
        cls = next((k for k, v in ROAD_CLASSES.items() if tag in v), None)
        if cls and el.get("geometry"):
            pts = [(p["lat"], p["lon"]) for p in el["geometry"]]
            ways.append((cls, pts))

    out = g.reset_index(drop=True).copy()
    for cls in ROAD_CLASSES:
        for rad in ROAD_RADII:
            out[f"road_{cls}_{rad}"] = 0.0
    out["dist_major_km"] = np.nan

    for i, st in enumerate(out.itertuples()):
        best = np.inf
        for cls, pts in ways:
            for a, b in zip(pts[:-1], pts[1:]):
                mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                d = _seg_len_km((st.lat, st.lon), mid)
                if cls == "major":
                    best = min(best, d)
                if d > 1.2:                      # outside the widest buffer
                    continue
                L = _seg_len_km(a, b)
                for rad in ROAD_RADII:
                    if d <= rad / 1000.0:
                        out.at[i, f"road_{cls}_{rad}"] += L
        out.at[i, "dist_major_km"] = best if np.isfinite(best) else np.nan
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["gee", "osm", "merge"], required=True)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    st = stations()
    cities = sorted(st.city.unique())
    if a.limit:
        cities = cities[:a.limit]
    d = OUT / a.stage if a.stage != "merge" else OUT
    d.mkdir(parents=True, exist_ok=True)

    if a.stage == "merge":
        frames = []
        for c in cities:
            fg, fo = OUT / "gee" / f"{c}.csv", OUT / "osm" / f"{c}.csv"
            if not fg.exists():
                continue
            g = pd.read_csv(fg)
            if fo.exists():
                o = pd.read_csv(fo)
                cols = [x for x in o.columns if x.startswith("road_") or x == "dist_major_km"]
                g = g.merge(o[["station_id"] + cols], on="station_id", how="left")
            frames.append(g)
        m = pd.concat(frames, ignore_index=True)
        m.to_csv(MOD / "lur_predictors.csv", index=False)
        nroad = sum(1 for c in cities if (OUT / "osm" / f"{c}.csv").exists())
        print(f"merged {len(m)} stations, {m.city.nunique()} cities "
              f"({nroad} with roads), {m.shape[1]} columns -> lur_predictors.csv")
        return

    if a.stage == "gee":
        import ee
        ee.Initialize(project="kandypinn")

    print(f"stage={a.stage}, {len(cities)} cities")
    for i, c in enumerate(cities, 1):
        f = d / f"{c}.csv"
        if f.exists():
            print(f"  [{i}/{len(cities)}] {c} exists")
            continue
        g = st[st.city == c]
        try:
            r = gee_city(g) if a.stage == "gee" else osm_city(g)
            r.to_csv(f, index=False)
            extra = ""
            if a.stage == "osm":
                extra = (f" major@300m median "
                         f"{r['road_major_300'].median():.2f} km")
            print(f"  [{i}/{len(cities)}] {c:<10} n={len(g):>3} OK{extra}")
        except Exception as e:
            print(f"  [{i}/{len(cities)}] {c:<10} FAILED {str(e)[:70]}")


if __name__ == "__main__":
    main()
