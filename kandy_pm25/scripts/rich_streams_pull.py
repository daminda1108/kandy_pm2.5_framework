"""rich_streams_pull.py -- predictors for the RICH sensorless rung (Bud0R), discovery + confirmation.

Registered test (draft 2026-09-28, `docs/prereg_rich_baseline_2026-09-28_DRAFT.md`): does the confirmed
ladder ranking survive a sensorless baseline that also knows terrain, a chemical-transport model's
PM2.5, fires, NO2 and precipitation? This script pulls PREDICTORS ONLY. It never reads PM2.5.

Every stream is global, free and computable for a city with no monitors, at the city centroid (the
same point the ladder's drivers use) or, for terrain, around it. Nothing is sampled at monitor sites
(gotcha #99).

  cams     ECMWF/CAMS/NRT, particulate_matter_d_less_than_25_um_surface, the 00 UTC run's forecast
           hours 0-21 averaged per UTC day, 0.4 deg pixel at the centroid, kg m-3 x 1e9 = ug m-3.
           CAMS assimilates satellite AOD, O3, CO, NO2, SO2; its documentation lists no surface PM2.5
           monitors in any cycle through 50r1 (checked 2026-09-28).
  no2      COPERNICUS/S5P/OFFL/L3_NO2 tropospheric_NO2_column_number_density, daily mean of all
           overpasses, 5 km (pyramid mean) at the centroid; missing days stay missing (as MAIAC).
  imerg    NASA/GPM_L3/IMERG_V07 precipitation (mm/h, 30 min), daily total = mean rate x 24, 0.1 deg.
  firms    FIRMS fire pixels (T21 present), daily count within 100 km and 300 km of the centroid, 1 km.
  terrain  COPERNICUS/DEM/GLO30 (global, incl. > 60 N), static per city, around the centroid:
           elev_m (centroid), relief_10/30 (p95 - p5 within 10 / 30 km), slope_10 (mean slope within
           10 km, deg), floor_rel_30 (centroid minus p5 within 30 km), enclosure (of 8 rays, how many
           rise >= 200 m above the centroid within 15 km).

Output: data/processed/modular/rich_streams/{stream}/{city}_{year}.csv (resumable), terrain.csv.
Usage: python scripts/rich_streams_pull.py [--streams cams,no2,imerg,firms,terrain] [--test CITY]
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "rich_streams"


def cities() -> pd.DataFrame:
    from src.modular.city_meta import city_meta
    rows = []
    disc = [Path(f).stem for f in glob.glob(str(MOD / "drivers_v2" / "*.csv"))]
    m = city_meta(disc).set_index("city")
    for c in disc:
        d = pd.read_csv(MOD / "drivers_v2" / f"{c}.csv", usecols=["date"])
        rows.append(dict(city=c, lat=float(m.loc[c, "lat"]), lon=float(m.loc[c, "lon"]),
                         d0=d.date.min(), d1=d.date.max()))
    P = pd.read_csv(MOD / "confirmation" / "confirmation_panel.csv")
    for r in P.itertuples():
        d = pd.read_csv(MOD / "confirmation" / "drivers" / f"{r.cid}.csv", usecols=["date"])
        rows.append(dict(city=r.cid, lat=r.lat, lon=r.lon, d0=d.date.min(), d1=d.date.max()))
    return pd.DataFrame(rows)


def _init():
    import ee
    ee.Initialize(project="kandypinn")
    return ee


def _chunks(d0, d1):
    """Calendar-year chunks with the true window ends (gotcha #98)."""
    s, e = pd.Timestamp(d0), pd.Timestamp(d1) + pd.Timedelta(days=1)
    edges = [s] + [pd.Timestamp(f"{y}-01-01") for y in range(s.year + 1, e.year + 1)
                   if pd.Timestamp(f"{y}-01-01") < e] + [e]
    return [(a, b) for a, b in zip(edges[:-1], edges[1:]) if a < b]


def _region(ee, col, pt, scale, band):
    r = col.select(band).getRegion(pt, scale).getInfo()
    d = pd.DataFrame(r[1:], columns=r[0])
    d["t"] = pd.to_datetime(d.time, unit="ms")
    return d


def pull(ee, stream, c, a, b):
    pt = ee.Geometry.Point(c.lon, c.lat)
    A, B = a.strftime("%Y-%m-%d"), b.strftime("%Y-%m-%d")
    if stream == "cams":
        col = (ee.ImageCollection("ECMWF/CAMS/NRT").filterDate(A, B)
               .filter(ee.Filter.eq("model_initialization_hour", 0))
               .filter(ee.Filter.lte("model_forecast_hour", 21)))
        d = _region(ee, col, pt, 44528, "particulate_matter_d_less_than_25_um_surface")
        d["v"] = pd.to_numeric(d.iloc[:, 4], errors="coerce") * 1e9
        out = d.groupby(d.t.dt.floor("D")).v.agg(["mean", "count"]).rename(
            columns={"mean": "cams_pm25", "count": "cams_n"})
    elif stream == "no2":
        col = ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_NO2").filterDate(A, B).filterBounds(pt)
        d = _region(ee, col, pt, 5000, "tropospheric_NO2_column_number_density")
        d["v"] = pd.to_numeric(d.iloc[:, 4], errors="coerce")
        out = d.groupby(d.t.dt.floor("D")).v.mean().rename("no2_trop").to_frame()
    elif stream == "imerg":
        col = ee.ImageCollection("NASA/GPM_L3/IMERG_V07").filterDate(A, B)
        d = _region(ee, col, pt, 11132, "precipitation")
        d["v"] = pd.to_numeric(d.iloc[:, 4], errors="coerce")
        g = d.groupby(d.t.dt.floor("D")).v.agg(["mean", "count"])
        out = pd.DataFrame({"precip_mm": g["mean"] * 24, "imerg_n": g["count"]})
    elif stream == "firms":
        b100, b300 = pt.buffer(100_000), pt.buffer(300_000)
        col = ee.ImageCollection("FIRMS").filterDate(A, B).select("T21")

        # One aggregation per buffer over the stacked daily images (toBands), instead of one per
        # image: identical counts, and it stays under Earth Engine's concurrent-aggregation limit.
        # Verified equal to the per-image method on already-pulled chunks (fire_method_check).
        ids = col.aggregate_array("system:index").getInfo()
        ts = col.aggregate_array("system:time_start").getInfo()
        if not ids:
            d = pd.DataFrame(columns=["t", "n100", "n300"])
        else:
            stack = col.toBands()
            r1 = stack.reduceRegion(ee.Reducer.count(), b100, 1000, maxPixels=1e12, tileScale=8).getInfo()
            r3 = stack.reduceRegion(ee.Reducer.count(), b300, 1000, maxPixels=1e12, tileScale=8).getInfo()
            d = pd.DataFrame({"t": ts, "n100": [r1.get(f"{i}_T21", 0) for i in ids],
                              "n300": [r3.get(f"{i}_T21", 0) for i in ids]})
        if d.empty:
            return pd.DataFrame(columns=["date", "fire_n100", "fire_n300"])
        d["date"] = pd.to_datetime(d.t, unit="ms").dt.floor("D")
        out = d.groupby("date")[["n100", "n300"]].sum().rename(
            columns={"n100": "fire_n100", "n300": "fire_n300"})
        # a day with no FIRMS image is a day with no detected fire record, not a missing value:
        full = pd.date_range(a, b - pd.Timedelta(days=1), freq="D")
        out = out.reindex(full).fillna(0.0)
    out.index.name = "date"
    return out.reset_index()


def terrain(ee, c, source="GLO30") -> dict:
    """GLO-30 first; SRTM GL1 only where GLO-30 has no data (its Armenia and Azerbaijan tiles are
    not released). The source is recorded per city."""
    pt = ee.Geometry.Point(c.lon, c.lat)
    # Ocean pixels are EXCLUDED: stored as 0 m, they make a coastal city's relief describe the sea
    # (Jersey: relief within 30 km = 0 m, below its 10 km relief of 99.5 m). GLO-30 carries its own
    # water-body mask (WBM == 1 is ocean); lakes and rivers stay in.
    if source == "GLO30":
        col = ee.ImageCollection("COPERNICUS/DEM/GLO30")
        wbm = col.select("WBM").mosaic()
        dem = col.select("DEM").mosaic().updateMask(wbm.neq(1)).setDefaultProjection(
            "EPSG:4326", None, 30)
    else:
        s = ee.Image("USGS/SRTMGL1_003").select("elevation")
        dem = s.updateMask(s.gt(0)).rename("DEM")     # SRTM stores the sea as 0 (fallback cities are inland)
    slope = ee.Terrain.slope(dem)
    pct = ee.Reducer.percentile([5, 95])
    r10 = dem.reduceRegion(pct, pt.buffer(10_000), 90, maxPixels=1e10).getInfo()
    r30 = dem.reduceRegion(pct, pt.buffer(30_000), 90, maxPixels=1e10).getInfo()
    s10 = slope.reduceRegion(ee.Reducer.mean(), pt.buffer(10_000), 90, maxPixels=1e10).getInfo()
    e0 = None
    for rad in (500, 2000, 5000):          # centroid elevation from land only; widen if the centroid is at sea
        e0 = dem.reduceRegion(ee.Reducer.median(), pt.buffer(rad), 30).getInfo()["DEM"]
        if e0 is not None:
            break
    enc = 0
    for k in range(8):
        az = np.deg2rad(45 * k)
        pts = [[c.lon + (km / 111.32) * np.sin(az) / np.cos(np.deg2rad(c.lat)),
                c.lat + (km / 110.57) * np.cos(az)] for km in np.arange(0.5, 15.01, 0.5)]
        mx = dem.reduceRegion(ee.Reducer.max(), ee.Geometry.MultiPoint(pts), 30).getInfo()["DEM"]
        enc += int(mx is not None and e0 is not None and mx - e0 >= 200)
    if None in (e0, r10.get("DEM_p5"), r30.get("DEM_p5"), s10.get("slope")):
        if source == "GLO30":
            return terrain(ee, c, "SRTMGL1")
        raise RuntimeError("no DEM data in GLO-30 or SRTM GL1")
    return dict(city=c.city, dem=source, elev_m=e0, relief_10=r10["DEM_p95"] - r10["DEM_p5"],
                relief_30=r30["DEM_p95"] - r30["DEM_p5"], slope_10=s10["slope"],
                floor_rel_30=e0 - r30["DEM_p5"], enclosure=enc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--streams", default="cams,no2,imerg,firms,terrain")
    ap.add_argument("--test", default="")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    ee = _init()
    C = cities()
    if a.test:
        C = C[C.city == a.test]
    streams = a.streams.split(",")
    fails = 0
    if "terrain" in streams:
        tf = OUT / "terrain.csv"
        old = pd.read_csv(tf, dtype={"city": str}) if tf.exists() else pd.DataFrame(columns=["city"])
        todo = [c for c in C.itertuples() if c.city not in set(old.city)]
        rows = []
        with ThreadPoolExecutor(a.workers) as ex:
            futs = {ex.submit(terrain, ee, c): c.city for c in todo}
            for f in as_completed(futs):
                try:
                    rows.append(f.result())
                except Exception as e:                                     # noqa: BLE001
                    fails += 1
                    print(f"  FAILED terrain {futs[f]}: {str(e)[:120]}", flush=True)
        if rows:
            OUT.mkdir(parents=True, exist_ok=True)
            new = pd.concat([old, pd.DataFrame(rows)], ignore_index=True)
            tmp = tf.with_suffix(".tmp"); new.to_csv(tmp, index=False); os.replace(tmp, tf)
        print(f"  terrain: {len(rows)} new, {fails} failed", flush=True)
    jobs = []
    for s in [s for s in streams if s != "terrain"]:
        (OUT / s).mkdir(parents=True, exist_ok=True)
        for c in C.itertuples():
            for x, y in _chunks(c.d0, c.d1):
                f = OUT / s / f"{c.city}_{x.year}.csv"
                if not f.exists():
                    jobs.append((s, c, x, y, f))
    print(f"  {len(jobs)} stream chunks to pull", flush=True)
    t0 = time.time()

    def one(job):
        s, c, x, y, f = job
        d = pull(ee, s, c, x, y)
        tmp = f.with_suffix(".tmp"); d.to_csv(tmp, index=False); os.replace(tmp, f)
        return s, c.city, x.year, len(d)

    done = 0
    with ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for f in as_completed(futs):
            try:
                s, c, y, n = f.result(); done += 1
                if done % 25 == 0 or a.test:
                    print(f"  [{done}/{len(jobs)}] {s} {c} {y}: {n} days ({time.time() - t0:.0f} s)",
                          flush=True)
            except Exception as e:                                         # noqa: BLE001
                fails += 1
                j = futs[f]
                print(f"  FAILED {j[0]} {j[1].city} {j[2].year}: {type(e).__name__}: {str(e)[:120]}",
                      flush=True)
    print(f"  done {done}, failed {fails}", flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
