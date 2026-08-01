"""kandy_era5land_refresh.py — top up the extension tier's ERA5-Land drivers
in place, without a Drive export round trip (2026-07-27).

WHY
---
The explorer's extension years (2024-2026) are driven by
`data/external/kandy/extended_gee/drive/kandy_era5land_{y}.csv`. Those CSVs were
written by a Drive export in July 2026, so the 2026 file stops at 2026-07-13 23:00
and the shipped payload stops with it — which is what opened the visible gap
between the end of the record and the start of the live forecast window.

ERA5-Land's own latency is about five days, so the record CAN always be carried to
roughly now-5d. The only reason it was not is that nothing re-ran the pull.

APPROACH
--------
For a few hundred hourly images over a 15x15 km box, a Drive export is overkill:
`reduceRegion` per image, batched through one `getInfo()` per chunk, returns the
same area means in a couple of minutes. Rows are APPENDED and de-duplicated on
`datetime`, so re-running is safe and never rewrites history.

Columns match the existing CSV exactly (u/v 10 m, t2m, d2m in kelvin, total
precipitation in metres) because the downstream chain parses them positionally by
name — this script must not invent a schema.

NOTE on tp: ERA5-Land total_precipitation ACCUMULATES from 00 UTC (gotcha #60).
The stored column keeps the raw accumulated value, exactly as the Drive export
did; de-accumulation happens downstream. Do not "fix" it here.

Run:  .venv/Scripts/python.exe scripts/kandy_era5land_refresh.py [--year 2026]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
import config as C  # noqa: E402

DRV = REPO / "data/external/kandy/extended_gee/drive"
BANDS = ["u_component_of_wind_10m", "v_component_of_wind_10m",
         "temperature_2m", "dewpoint_temperature_2m", "total_precipitation"]
CHUNK_H = 168          # one week of hourly images per getInfo() call


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    args = ap.parse_args()

    import ee
    ee.Initialize(project="kandypinn")

    b = C.KANDY_PINN_BBOX
    box = ee.Geometry.Rectangle([b["lon_min"], b["lat_min"], b["lon_max"], b["lat_max"]])

    path = DRV / f"kandy_era5land_{args.year}.csv"
    old = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["datetime"] + BANDS)
    have = set(old.datetime.astype(str))
    start = (pd.Timestamp(old.datetime.max()) + pd.Timedelta(hours=1)
             if len(old) else pd.Timestamp(f"{args.year}-01-01"))

    col = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").select(BANDS)
    latest = pd.Timestamp(ee.Date(col.aggregate_max("system:time_start"))
                          .format("YYYY-MM-dd HH:mm").getInfo())
    print(f"{path.name}: have to {old.datetime.max() if len(old) else '-'}; "
          f"ERA5-Land published to {latest:%Y-%m-%d %H:%M} UTC")
    if start > latest:
        print("nothing new to fetch")
        return

    rows = []
    cur = start
    while cur <= latest:
        stop = min(cur + pd.Timedelta(hours=CHUNK_H), latest + pd.Timedelta(hours=1))
        sub = col.filterDate(cur.strftime("%Y-%m-%dT%H:%M"), stop.strftime("%Y-%m-%dT%H:%M"))

        def one(img):
            v = img.reduceRegion(ee.Reducer.mean(), box, scale=11132, tileScale=4)
            return ee.Feature(None, v.set("datetime",
                                          img.date().format("YYYY-MM-dd HH:mm")))

        got = sub.map(one).getInfo()["features"]
        for f in got:
            p = f["properties"]
            if p.get("temperature_2m") is None:
                continue
            rows.append({"datetime": p["datetime"], **{k: p.get(k) for k in BANDS}})
        print(f"  {cur:%Y-%m-%d %H:%M} -> {stop:%Y-%m-%d %H:%M}: {len(got)} images")
        cur = stop

    new = pd.DataFrame(rows)
    new = new[~new.datetime.astype(str).isin(have)]
    if new.empty:
        print("no new rows")
        return
    out = pd.concat([old, new], ignore_index=True)
    out["_k"] = pd.to_datetime(out.datetime)
    out = out.sort_values("_k").drop_duplicates("datetime", keep="last").drop(columns="_k")
    out.to_csv(path, index=False)
    print(f"appended {len(new)} rows -> {len(out)} total, now ending "
          f"{out.datetime.iloc[-1]}")


if __name__ == "__main__":
    main()
