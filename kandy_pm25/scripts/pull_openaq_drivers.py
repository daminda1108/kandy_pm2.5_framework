"""pull_openaq_drivers.py — daily ERA5 drivers for the ingested OpenAQ sample.

Feeds `Bud0`, the sensorless rung: a leave-one-city-out model of daily mean PM2.5 from drivers
alone. Without drivers an OpenAQ city cannot enter the ladder at all.

COST, measured rather than assumed. The project's standing assumption was that per-city GEE
work is a multi-day Drive round trip. That is true for HOURLY time series; it is false here:

  ERA5-Land daily aggregates   `getRegion` -> 731 days in ONE call, 5.3 s/city
  ERA5 hourly BLH              13.3 s per 3 months, so ~107 s/city for 2 years

BLH is therefore sampled at the four synoptic hours (00/06/12/18 UTC) rather than all 24 --
a standard daily-mean approximation that costs ~4x less. Whole sample: ~20 min, not days.

The feature set is kept IDENTICAL to the CNEMC arm (t2m, u10, v10, wind, BLH, day-of-year), so
the pooled leave-one-city-out model sees the same predictors everywhere. A pooled model whose
features differ by arm would confound source with skill.

Usage: python scripts/pull_openaq_drivers.py [--limit N]
Out:   data/processed/modular/drivers/{cluster}.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "drivers"

LAND_DAILY = "ECMWF/ERA5_LAND/DAILY_AGGR"
ERA5_HOURLY = "ECMWF/ERA5/HOURLY"
YEARS = ("2023-01-01", "2025-01-01")
SYNOPTIC = [0, 6, 12, 18]


def _frame(rows) -> pd.DataFrame:
    d = pd.DataFrame(rows[1:], columns=rows[0])
    d["date"] = pd.to_datetime(d["time"], unit="ms", utc=True).dt.tz_localize(None).dt.floor("D")
    return d


def _bounded_quarters(start: str, end: str):
    """Chunk edges for [start, end): the window's own ends plus every quarter start inside it.

    FIX 2026-09-27: `pd.date_range(start, end, freq="QS")` begins at the first quarter start
    AFTER `start` and stops at the last one before `end`, so the head (start -> first quarter)
    and the tail (last quarter -> end) were never requested. Every city lost its first and last
    partial quarter of BLH (and of the coastal ERA5 fallback), and those days were then dropped
    by the driver dropna. Discovery files pulled before this date carry the defect; ladder v2
    uses re-pulled files (drivers_v2/).
    """
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    inner = [t for t in pd.date_range(s, e, freq="QS") if s < t < e]
    return [s, *inner, e]


def pull_city(lat: float, lon: float, years=None) -> pd.DataFrame:
    """years -- (start, end) ISO strings. MUST match the city's own ingest window.

    The ingest takes each city's LAST TWO YEARS of coverage, which for 34 of 37 cities is
    2025-2026. A hardcoded 2023-2025 driver window therefore overlapped the station data
    almost nowhere and silently dropped those cities from the ladder -- 48 cities in, 13 out,
    with the deep-tropical cell collapsing from 13 to 1. The window is now taken PER CITY from
    the ingest manifest, so drivers and observations cover the same days by construction.
    """
    import ee
    years = years or YEARS
    pt = ee.Geometry.Point([float(lon), float(lat)])

    land = (ee.ImageCollection(LAND_DAILY).filterDate(*years)
            .select(["temperature_2m", "u_component_of_wind_10m",
                     "v_component_of_wind_10m", "total_precipitation_sum"]))
    d = _frame(land.getRegion(pt, scale=11132).getInfo())
    for c_ in ("temperature_2m", "u_component_of_wind_10m",
               "v_component_of_wind_10m", "total_precipitation_sum"):
        d[c_] = pd.to_numeric(d[c_], errors="coerce")

    # ERA5-LAND HAS NO DATA OVER WATER. A coastal or island city samples ocean and every
    # variable returns None -- which is how Dakar, Malta and two others failed. This is not an
    # edge case to patch around: it is a systematic gap in the COASTAL stratum, exactly the
    # regime the project has never validated. Fall back to ERA5 (non-Land), which is global.
    if d["temperature_2m"].notna().sum() < 30:
        era = (ee.ImageCollection(ERA5_HOURLY).filterDate(*years)
               .filter(ee.Filter.Or(*[ee.Filter.calendarRange(h, h, "hour")
                                      for h in SYNOPTIC]))
               .select(["temperature_2m", "u_component_of_wind_10m",
                        "v_component_of_wind_10m", "total_precipitation"]))
        parts = []
        chunks_ = _bounded_quarters(years[0], years[1])
        for s_, e_ in zip(chunks_[:-1], chunks_[1:]):
            cc = era.filterDate(str(s_.date()), str(e_.date()))
            parts.append(_frame(cc.getRegion(pt, scale=27830).getInfo()))
        d = pd.concat(parts, ignore_index=True)
        d = d.rename(columns={"total_precipitation": "total_precipitation_sum"})
        for c_ in ("temperature_2m", "u_component_of_wind_10m",
                   "v_component_of_wind_10m", "total_precipitation_sum"):
            d[c_] = pd.to_numeric(d[c_], errors="coerce")

    d = d.groupby("date").agg({"temperature_2m": "mean",
                               "u_component_of_wind_10m": "mean",
                               "v_component_of_wind_10m": "mean",
                               "total_precipitation_sum": "sum"}).reset_index()

    # GEE "User memory limit exceeded" on a two-year hourly reduction -- gotcha #44, already
    # recorded for exactly this class of query. The documented remedy is a shorter window, so
    # BLH is pulled in QUARTERLY chunks and concatenated. Chunking changes nothing about the
    # result; it only keeps each request inside the per-user memory cap.
    chunks = _bounded_quarters(years[0], years[1])
    parts = []
    for s, e in zip(chunks[:-1], chunks[1:]):
        c = (ee.ImageCollection(ERA5_HOURLY)
             .filterDate(str(s.date()), str(e.date()))
             .filter(ee.Filter.Or(*[ee.Filter.calendarRange(h, h, "hour")
                                    for h in SYNOPTIC]))
             .select("boundary_layer_height"))
        parts.append(_frame(c.getRegion(pt, scale=27830).getInfo()))
    b = pd.concat(parts, ignore_index=True)
    b = b.groupby("date").boundary_layer_height.mean().reset_index()

    m = d.merge(b, on="date", how="left")
    m["wind"] = np.hypot(m.u_component_of_wind_10m.astype(float),
                         m.v_component_of_wind_10m.astype(float))
    return m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--skip-existing", action="store_true", default=True)
    a = ap.parse_args()

    import ee
    ee.Initialize(project="kandypinn")

    man = pd.read_csv(MOD / "openaq_manifest.csv")
    keep = man[(man.status == "OK") & (man.stations >= 10)].copy()
    if a.limit:
        keep = keep.head(a.limit)
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"{len(keep)} cities with >= 10 stations; window {YEARS[0]}..{YEARS[1]}")

    for i, r in enumerate(keep.itertuples(), 1):
        c = int(r.cluster)
        f = OUT / f"{c}.csv"
        if a.skip_existing and f.exists():
            print(f"  [{i}/{len(keep)}] {c} exists, skipped")
            continue
        try:
            # window from the manifest, padded a day either side
            s0 = (pd.Timestamp(r.t_start) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            s1 = (pd.Timestamp(r.t_end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            m = pull_city(r.lat, r.lon, years=(s0, s1))
            m.insert(0, "cluster", c)
            m.to_csv(f, index=False)
            print(f"  [{i}/{len(keep)}] {c:>5} {str(r.country)[:20]:<20} "
                  f"days={len(m):>4} blh_ok={int(m.boundary_layer_height.notna().sum()):>4} "
                  f"{s0}..{s1}")
        except Exception as e:
            print(f"  [{i}/{len(keep)}] {c:>5} FAILED {str(e)[:70]}")


if __name__ == "__main__":
    main()
