"""pull_kandy_model_priors.py -- the two sensor-free inputs of the Kandy T(t) chain, for every ladder city.

EXPLORATORY (2026-10-10). Feeds scripts/ladder_v2_kandy_model.py, which scores the deployed Kandy model's
temporal anchor as a rung of the ladder (spec: docs/kandy_model_rung_spec_2026-10-10.md).

For each ladder city the area is the bounding box of its urban-centre sample points (the points the
sensorless rung's static geography uses; geo_grid/*_pts.csv), so no input is placed at a monitoring site.

  1. GEOS-CF PM25_RH35_GCC (NASA/GEOS-CF/v1/rpl/tavg1hr), daily mean of the hourly images, area mean.
     One Export.table.toDrive per year to Drive folder KANDYMODEL_LADDER (2021..2026; GEE ends 2026-01-02).
  2. van Donkelaar V6.GL.02 annual PM2.5 (sat-io GLOBAL-SATELLITE-PM25/ANNUAL), area mean, 2019..2022,
     computed directly (small) -> data/processed/modular/kandy_model_rung/vand_annual.csv

Usage: python scripts/pull_kandy_model_priors.py --submit | --vand | --status | --download
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "kandy_model_rung"
FOLDER = "KANDYMODEL_LADDER"
YEARS = range(2021, 2027)
GEOS = "NASA/GEOS-CF/v1/rpl/tavg1hr"
VAND = "projects/sat-io/open-datasets/GLOBAL-SATELLITE-PM25/ANNUAL"


def city_boxes() -> pd.DataFrame:
    rows = []
    for f in sorted(glob.glob(str(MOD / "geo_grid" / "*_pts.csv"))) + \
             sorted(glob.glob(str(MOD / "confirmation" / "geo_grid" / "*_pts.csv"))):
        d = pd.read_csv(f)
        if d.empty:
            continue
        rows.append(dict(city=str(d.city.iloc[0]), lon0=d.lon.min(), lon1=d.lon.max(),
                         lat0=d.lat.min(), lat1=d.lat.max(), n_pts=len(d)))
    b = pd.DataFrame(rows).drop_duplicates("city")
    assert b.city.is_unique and len(b) > 100, f"unexpected city count {len(b)}"
    return b


def _fc(ee, b):
    feats = []
    for r in b.itertuples():
        g = ee.Geometry.Rectangle([r.lon0, r.lat0, r.lon1, r.lat1], None, False)
        feats.append(ee.Feature(g, {"city": r.city}))
    return ee.FeatureCollection(feats)


def submit(ee, b):
    fc = _fc(ee, b)
    col = ee.ImageCollection(GEOS).select("PM25_RH35_GCC")
    for y in YEARS:
        start = ee.Date.fromYMD(y, 1, 1)
        n = ee.Date.fromYMD(y + 1, 1, 1).difference(start, "day")

        def make_day(start):                     # closure: ee.List.map introspects every parameter
            def day(k):
                d0 = start.advance(k, "day")
                ims = col.filterDate(d0, d0.advance(1, "day"))
                img = ims.mean()
                return img.reduceRegions(fc, ee.Reducer.mean(), scale=27750).map(
                    lambda f: f.set({"date": d0.format("YYYY-MM-dd"), "n_hours": ims.size()}))
            return day

        days = ee.List.sequence(0, n.subtract(1))
        out = ee.FeatureCollection(days.map(make_day(start))).flatten().filter(ee.Filter.gt("n_hours", 0))
        t = ee.batch.Export.table.toDrive(collection=out, description=f"kmr_geoscf_{y}", folder=FOLDER,
                                          fileNamePrefix=f"kmr_geoscf_{y}", fileFormat="CSV",
                                          selectors=["city", "date", "mean", "n_hours"])
        t.start()
        print(f"  submitted kmr_geoscf_{y}: {t.id}")


def vand(ee, b):
    fc = _fc(ee, b)
    col = ee.ImageCollection(VAND)
    rows = []
    for y in range(2019, 2023):
        img = col.filter(ee.Filter.stringContains("system:index", f"_{y}01-{y}12")).first()
        res = img.reduceRegions(fc, ee.Reducer.mean(), scale=1000).getInfo()["features"]
        for f in res:
            pr = f["properties"]
            v = pr.get("mean", pr.get("b1"))
            rows.append(dict(city=pr["city"], year=y, vand=v))
        print(f"  VanD {y}: {sum(r['year'] == y and r['vand'] is not None for r in rows)} cities")
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "vand_annual.tmp.csv"
    pd.DataFrame(rows).to_csv(tmp, index=False)
    os.replace(tmp, OUT / "vand_annual.csv")


def status(ee):
    for t in ee.batch.Task.list()[:30]:
        if t.config.get("description", "").startswith("kmr_"):
            s = t.status()
            print(f"  {s['description']:<20} {s['state']:<10} {s.get('error_message', '')}")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    for k in ("submit", "vand", "status", "download"):
        g.add_argument(f"--{k}", action="store_true")
    a = ap.parse_args()
    if a.download:
        sys.argv = [sys.argv[0], "--folder", FOLDER]
        sys.path.insert(0, str(REPO / "scripts"))
        import download_gee_drive_outputs as dl
        return dl.main()
    import ee
    ee.Initialize(project="kandypinn")
    b = city_boxes()
    OUT.mkdir(parents=True, exist_ok=True)
    b.to_csv(OUT / "city_boxes.csv", index=False)
    print(f"{len(b)} cities; median box {((b.lon1 - b.lon0)).median():.2f} x {((b.lat1 - b.lat0)).median():.2f} deg")
    if a.submit:
        submit(ee, b)
    elif a.vand:
        vand(ee, b)
    else:
        status(ee)


if __name__ == "__main__":
    main()
