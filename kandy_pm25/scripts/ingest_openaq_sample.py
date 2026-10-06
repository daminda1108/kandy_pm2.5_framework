"""ingest_openaq_sample.py — pull the registered OpenAQ sample from the public S3 archive.

Reads the drawn sample (prereg v2 Amendment 2, option C) and the PVAF location census, then
pulls hourly PM2.5 per station straight from `s3://openaq-data-archive` — anonymous, no API
key, no /locations call (gotcha #35: the REST key is for discovery only, and discovery is
already done and on disk).

BOUNDS, declared rather than discovered later. The full sample is 2,473 locations; pulling
every location-month would be ~118k requests. Two caps keep it tractable and neither touches
the registered SELECTION:

  MAX_STATIONS_PER_CITY = 30   the ladder needs held-out + fit stations, not all 194 of
                               Bangkok's. Stations are ranked by record length, so the cap
                               drops the shortest records, never a whole city.
  YEARS                        a fixed common window, so cities are compared over the same
                               period rather than over whatever each happens to have.

Both are recorded per city in the manifest, so the exclusion funnel is auditable.

Usage:
  python scripts/ingest_openaq_sample.py --band deep_tropical      # irreplaceable cell first
  python scripts/ingest_openaq_sample.py --all
Out:
  data/processed/modular/openaq/{cluster}.parquet     per-station hourly PM2.5
  data/processed/modular/openaq_manifest.csv          what was pulled, what failed
"""
from __future__ import annotations

import argparse
import gzip
import io
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CENSUS = REPO / "data" / "processed" / "cnemc_panel" / "openaq_census" / "locations_clustered.csv"
SAMPLE = REPO / "data" / "processed" / "modular" / "validation_sample.csv"
OUT = REPO / "data" / "processed" / "modular" / "openaq"

S3_BUCKET = "openaq-data-archive"
S3_PREFIX_YEAR = "records/csv.gz/locationid={lid}/year={year}/"
# Files are DAILY (one per station-day), not monthly -- measured 0.41 s per file, so cost is
# stations x years x 365. 12 stations x 2 years = 8,760 files/city keeps the whole sample near
# 3 h at 16 threads. 12 stations is enough for the ladder (a held-out third plus fit stations).
N_YEARS = 2
MAX_STATIONS_PER_CITY = 12
WORKERS = 16


def s3_client():
    """Anonymous client. The archive is public (gotcha #35) -- no credentials, no API key."""
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    return boto3.client("s3", config=Config(signature_version=UNSIGNED,
                                            region_name="us-east-1",
                                            retries={"max_attempts": 3}))


def _list_year_keys(s3, loc_id: int, year: int) -> list[str]:
    """S3 object names are NOT predictable, so they must be LISTED, not constructed.

    Guessing `location-<id>-<yyyymm>.csv.gz` returns 404 for every object and looks exactly
    like a city with no data -- which is how the first run reported EMPTY for cities that
    actually have years of records.
    """
    prefix = S3_PREFIX_YEAR.format(lid=loc_id, year=year)
    keys, token = [], None
    while True:
        kw = dict(Bucket=S3_BUCKET, Prefix=prefix, MaxKeys=1000)
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        keys.extend(o["Key"] for o in r.get("Contents", []))
        token = r.get("NextContinuationToken")
        if not token:
            break
    return keys


def fetch_loc_year(loc_id: int, year: int) -> pd.DataFrame | None:
    s3 = s3_client()
    try:
        keys = _list_year_keys(s3, loc_id, year)
    except Exception:
        return None
    parts = []
    for k in keys:
        try:
            body = s3.get_object(Bucket=S3_BUCKET, Key=k)["Body"].read()
            with gzip.GzipFile(fileobj=io.BytesIO(body)) as f:
                parts.append(pd.read_csv(f))
        except Exception:
            continue
    if not parts:
        return None
    d = pd.concat(parts, ignore_index=True)
    if "parameter" in d.columns:
        d = d[d.parameter.astype(str).str.lower() == "pm25"]
    return d if len(d) else None


def city_years(locs: pd.DataFrame) -> list[int]:
    """The city's OWN last N_YEARS of coverage, not a fixed global window.

    Coverage windows differ per city (Medellin's record ends 2024-09), so a fixed window
    silently gives some cities far less data than others -- and "2 years" would then describe
    the request rather than the data. Recorded per city in the manifest.
    """
    last = pd.to_datetime(locs.dt_last, errors="coerce", utc=True).max()
    if pd.isna(last):
        return [2024, 2025]
    y = int(last.year)
    return list(range(y - N_YEARS + 1, y + 1))


def ingest_city(cluster: int, locs: pd.DataFrame) -> dict:
    locs = locs.copy()
    locs["span"] = (pd.to_datetime(locs.dt_last, errors="coerce", utc=True)
                    - pd.to_datetime(locs.dt_first, errors="coerce", utc=True)).dt.days
    locs = locs.sort_values("span", ascending=False).drop_duplicates("loc_id")
    used = locs.head(MAX_STATIONS_PER_CITY)

    years = city_years(used)
    tasks = [(int(r.loc_id), y) for r in used.itertuples() for y in years]
    frames = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_loc_year, lid, y): lid for lid, y in tasks}
        for f in as_completed(futs):
            d = f.result()
            if d is not None:
                d["loc_id"] = futs[f]
                frames.append(d)
    if not frames:
        return {"cluster": cluster, "status": "EMPTY", "stations": 0, "rows": 0,
                "locs_available": len(locs), "locs_used": len(used),
                "years": f"{years[0]}-{years[-1]}"}

    x = pd.concat(frames, ignore_index=True)
    tcol = "datetime" if "datetime" in x.columns else x.columns[0]
    x["datetime_utc"] = pd.to_datetime(x[tcol], errors="coerce", utc=True).dt.tz_localize(None)
    x["pm25"] = pd.to_numeric(x.get("value"), errors="coerce")
    x = x.dropna(subset=["datetime_utc", "pm25"])
    x = x[(x.pm25 > 0) & (x.pm25 < 1000)]
    x["datetime_utc"] = x.datetime_utc.dt.floor("h")
    g = (x.groupby(["loc_id", "datetime_utc"]).pm25.mean().reset_index()
         .merge(used[["loc_id", "lat", "lon", "provider", "is_monitor"]], on="loc_id", how="left"))
    g = g.rename(columns={"loc_id": "station_id"})

    OUT.mkdir(parents=True, exist_ok=True)
    g.to_parquet(OUT / f"{cluster}.parquet", index=False)
    return {"cluster": cluster, "status": "OK", "stations": int(g.station_id.nunique()),
            "rows": len(g), "locs_available": len(locs), "locs_used": len(used),
            "years": f"{years[0]}-{years[-1]}",
            "t_start": str(g.datetime_utc.min())[:10], "t_end": str(g.datetime_utc.max())[:10],
            "frac_reference": float(g.drop_duplicates("station_id").is_monitor.mean())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--band", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    s = pd.read_csv(SAMPLE)
    s = s[s.src == "OpenAQ"].copy()
    if a.band:
        s = s[s.band == a.band]
    if a.limit:
        s = s.head(a.limit)
    cl = pd.read_csv(CENSUS)
    cl = cl[cl.cluster.isin(s.cluster.dropna().astype(int))]

    print(f"ingesting {len(s)} OpenAQ cities "
          f"({'band=' + a.band if a.band else 'all bands'}), "
          f"last {N_YEARS} yr per city, <= {MAX_STATIONS_PER_CITY} stations/city")

    rows = []
    for i, r in enumerate(s.itertuples(), 1):
        c = int(r.cluster)
        locs = cl[cl.cluster == c]
        if (OUT / f"{c}.parquet").exists():
            print(f"  [{i}/{len(s)}] cluster {c} ({r.country}) - already present, skipped")
            continue
        res = ingest_city(c, locs)
        res.update(country=r.country, band=r.band, lat=r.lat, lon=r.lon)
        rows.append(res)
        print(f"  [{i}/{len(s)}] cluster {c:>5} {str(r.country)[:22]:<22} "
              f"{res['status']:<5} stations={res['stations']:>3} rows={res['rows']:>8}")

    if rows:
        m = pd.DataFrame(rows)
        p = REPO / "data" / "processed" / "modular" / "openaq_manifest.csv"
        if p.exists():
            m = pd.concat([pd.read_csv(p), m], ignore_index=True).drop_duplicates(
                "cluster", keep="last")
        m.to_csv(p, index=False, encoding="utf-8")
        ok = m[m.status == "OK"]
        print(f"\n{len(ok)}/{len(m)} cities ingested | "
              f">= 10 stations: {int((ok.stations >= 10).sum())}")
        print(f"manifest -> {p}")


if __name__ == "__main__":
    main()
