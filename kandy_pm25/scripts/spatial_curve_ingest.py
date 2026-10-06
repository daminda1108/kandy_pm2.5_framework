"""spatial_curve_ingest.py -- D1 and D2 of the spatial learning curve (OSF registration, 2026-09-11).

WHAT IT DOES. For every candidate cluster fixed by the registration, pull hourly PM2.5 for every
reference-grade location from the public OpenAQ archive, over the metadata-optimal one-year window
plus 60 days of margin on each side, convert to UTC, average multiple sensors per location-hour,
and cache one parquet per location. Nothing is merged, filtered for coverage or scored here; that
is D3, run separately after this finishes, so the frame is frozen by the registered rule and never
by inspecting what arrived.

WHY ONLY THE WINDOW. Bytes are trivial (0.08 MB per station-year) and requests are not: every
location stores one object per day. Listing a location returns every key it has ever written, and
the object name carries its date, so keys are filtered to the window BEFORE any GET.

RESUMABLE. A location whose parquet exists is skipped. A location that returns no objects in the
window is recorded as empty, not retried forever. A run can be killed and restarted.

⚠ TIMESTAMPS arrive in local time (Bangkok rows read +07:00). Parsed with utc=True. Mixing offsets
would silently misalign days across time zones.

Usage: .venv/Scripts/python.exe scripts/spatial_curve_ingest.py [--workers 64] [--limit-clusters N]
Out:   data/processed/modular/spatial_curve/raw/{location_id}.parquet
       data/processed/modular/spatial_curve/candidates.csv    (locations x cluster x window)
       data/processed/modular/spatial_curve/ingest_log.csv     (one row per location)
"""
from __future__ import annotations

import argparse
import gzip
import io
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(__file__).resolve().parents[1]
FEAS = REPO / "scripts" / "spatial_curve_feasibility"
sys.path.insert(0, str(FEAS))
DISCOVERY = REPO / "data" / "external" / "openaq" / "discovery" / "global_locations.csv"
OUT = REPO / "data" / "processed" / "modular" / "spatial_curve"
RAW = OUT / "raw"
RAW.mkdir(parents=True, exist_ok=True)

BUCKET = "openaq-data-archive"
PREFIX = "records/csv.gz/locationid={loc}/"
MARGIN_DAYS = 60                 # registered: 60 days either side of the metadata window
WINDOW_DAYS = 365
MIN_CONC_ALL = 15                # registered: every cluster with >= 15 concurrent
MIN_CONC_TROPICS = 12            # registered: tropical and deep tropical with >= 12
DATE_IN_KEY = re.compile(r"-(\d{8})\.csv\.gz$")
MAX_ERROR_STREAK = 25            # consecutive failed locations that mean the network is down
LOC_WORKERS = 6                  # locations in flight at once; each fans out over the GET pool


def band(lat: float) -> str:
    a = abs(lat)
    return ("deep_tropical" if a < 15 else "tropical" if a < 23.5
            else "subtropical" if a < 35 else "temperate")


def candidates() -> pd.DataFrame:
    """Locations to pull, each with its cluster and download window.

    Clustering and the metadata-optimal window are recomputed with the feasibility module's own
    functions, so the candidate set is exactly the one the registration's projection described.
    """
    import concurrent_density as cd                                        # noqa: E402

    d = pd.read_csv(DISCOVERY).rename(columns={"first": "t_first", "last": "t_last"})
    d["t_first"] = pd.to_datetime(d.t_first, errors="coerce", utc=True).dt.tz_localize(None)
    d["t_last"] = pd.to_datetime(d.t_last, errors="coerce", utc=True).dt.tz_localize(None)
    ref = d[d.is_monitor & d.t_first.notna() & d.t_last.notna()].dropna(subset=["lat", "lon"])
    ref = ref.reset_index(drop=True)
    ref["cluster"] = cd.cluster(ref)

    rows = []
    for cl, g in ref.groupby("cluster"):
        if len(g) < MIN_CONC_TROPICS:
            continue
        lat0 = float(g.lat.mean())
        k, s = cd.max_concurrent(g.t_first.values, g.t_last.values, WINDOW_DAYS)
        b = band(lat0)
        need = MIN_CONC_TROPICS if b in ("tropical", "deep_tropical") else MIN_CONC_ALL
        if k < need or s is None:
            continue
        w0 = pd.Timestamp(np.datetime64(int(s), "D")) - pd.Timedelta(days=MARGIN_DAYS)
        w1 = w0 + pd.Timedelta(days=WINDOW_DAYS + 2 * MARGIN_DAYS)
        # only locations whose metadata span touches the download window can contribute
        touch = g[(g.t_last >= w0) & (g.t_first <= w1)]
        for r in touch.itertuples():
            rows.append(dict(location_id=int(r.id), name=r.name, cluster=int(cl), band=b,
                             country=r.country, lat=r.lat, lon=r.lon, conc_365=int(k),
                             win_start=w0.date().isoformat(), win_end=w1.date().isoformat()))
    return pd.DataFrame(rows)


def s3_client(workers: int):
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    # STANDARD, not adaptive. Adaptive mode rate-limits the whole client after any throttle
    # response and recovers slowly; the first full run crawled at 30-180 s per location while a
    # fresh process did the same location in 8-15 s (2026-09-11). Standard still retries.
    return boto3.client("s3", config=Config(signature_version=UNSIGNED,
                                            max_pool_connections=workers + 4 * LOC_WORKERS,
                                            retries={"max_attempts": 6, "mode": "standard"}))


def keys_in_window(s3, loc: int, w0: str, w1: str) -> list[str]:
    lo, hi = w0.replace("-", ""), w1.replace("-", "")
    keys, tok = [], None
    while True:
        kw = {"Bucket": BUCKET, "Prefix": PREFIX.format(loc=loc), "MaxKeys": 1000}
        if tok:
            kw["ContinuationToken"] = tok
        # listing had no retry, and one DNS failure on it ended the first full run (2026-09-10)
        for attempt in range(6):
            try:
                r = s3.list_objects_v2(**kw)
                break
            except Exception:                                              # noqa: BLE001
                if attempt == 5:
                    raise
                time.sleep(2 ** attempt)
        for o in r.get("Contents", []):
            m = DATE_IN_KEY.search(o["Key"])
            if m and lo <= m.group(1) <= hi:
                keys.append(o["Key"])
        if not r.get("IsTruncated"):
            break
        tok = r["NextContinuationToken"]
    return keys


def fetch(s3, key: str) -> pd.DataFrame | None:
    for attempt in range(4):
        try:
            body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
            d = pd.read_csv(io.BytesIO(gzip.decompress(body)),
                            usecols=lambda c: c in ("datetime", "parameter", "units", "value",
                                                    "sensors_id"))
            return d[d.parameter.astype(str).str.lower() == "pm25"]
        except Exception:                                                  # noqa: BLE001
            time.sleep(0.5 * (attempt + 1))
    return None


def ingest_location(s3, pool: ThreadPoolExecutor, row) -> dict:
    loc = int(row.location_id)
    f = RAW / f"{loc}.parquet"
    if f.exists():
        return dict(location_id=loc, status="cached")
    keys = keys_in_window(s3, loc, row.win_start, row.win_end)
    if not keys:
        pd.DataFrame(columns=["datetime_utc", "pm25"]).to_parquet(f, index=False)
        return dict(location_id=loc, status="empty", keys=0)
    parts = list(pool.map(lambda k: fetch(s3, k), keys))
    failed = sum(p is None for p in parts)
    d = pd.concat([p for p in parts if p is not None and len(p)], ignore_index=True) \
        if any(p is not None and len(p) for p in parts) else pd.DataFrame()
    if d.empty:
        pd.DataFrame(columns=["datetime_utc", "pm25"]).to_parquet(f, index=False)
        return dict(location_id=loc, status="no_pm25", keys=len(keys), failed=failed)
    units = sorted(set(d.units.astype(str)))
    d["datetime_utc"] = pd.to_datetime(d.datetime, utc=True, errors="coerce").dt.floor("h")
    d["value"] = pd.to_numeric(d.value, errors="coerce")
    d = d.dropna(subset=["datetime_utc", "value"])
    # several PM2.5 sensors at one location: one value per location-hour
    h = d.groupby("datetime_utc", as_index=False).value.mean().rename(columns={"value": "pm25"})
    # write to a temp name then replace, so a killed run never leaves a truncated parquet that
    # the resume logic would then treat as complete
    tmp = f.with_suffix(".tmp")
    h.to_parquet(tmp, index=False)
    tmp.replace(f)
    return dict(location_id=loc, status="ok", keys=len(keys), failed=failed, hours=len(h),
                units="|".join(units))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=64)
    ap.add_argument("--limit-clusters", type=int, default=0, help="smoke test on N clusters")
    a = ap.parse_args()

    C = candidates()
    if a.limit_clusters:
        keep = C.drop_duplicates("cluster").nlargest(a.limit_clusters, "conc_365").cluster
        C = C[C.cluster.isin(keep)]
    C.to_csv(OUT / ("candidates_smoke.csv" if a.limit_clusters else "candidates.csv"), index=False)
    nclu = C.cluster.nunique()
    print(f"candidates: {len(C):,} locations in {nclu} clusters | bands "
          f"{dict(C.drop_duplicates('cluster').band.value_counts())}", flush=True)

    s3 = s3_client(a.workers)
    log, t0, streak, aborted = [], time.time(), 0, False
    rows = list(C.itertuples())
    # Several locations in flight at once. One location at a time left the GET pool idle while
    # each location listed its keys and wrote its file, and at 8-15 s per location that is
    # 6-7 hours for this candidate set. With LOC_WORKERS in flight the pool stays busy.
    with ThreadPoolExecutor(a.workers) as pool, ThreadPoolExecutor(LOC_WORKERS) as outer:
        futs = {outer.submit(ingest_location, s3, pool, row): row for row in rows}
        for i, fut in enumerate(as_completed(futs), 1):
            row = futs[fut]
            try:
                r = fut.result()
                streak = 0
            except Exception as e:                                          # noqa: BLE001
                # A transient failure must not end a three-hour run. No parquet is written for
                # this location, so a re-run retries it. A LONG run of failures means the
                # network itself is down, and continuing would only mark every remaining
                # location as failed in seconds, so that stops the run instead.
                r = dict(location_id=int(row.location_id), status="error",
                         error=f"{type(e).__name__}: {str(e)[:160]}")
                streak += 1
            r.update(cluster=int(row.cluster), band=row.band, country=row.country)
            log.append(r)
            if streak >= MAX_ERROR_STREAK:
                for f in futs:
                    f.cancel()                   # pending only; running ones finish cleanly
                aborted = True
                pd.DataFrame(log).to_csv(OUT / "ingest_log.csv", index=False)
                print(f"\nABORT: {streak} consecutive failures, last: {r['error']}. "
                      f"Network down? Re-run to resume; completed locations are kept.",
                      flush=True)
                break
            if i % 25 == 0 or i == len(rows):
                el = time.time() - t0
                done = sum(1 for x in log if x["status"] in ("ok", "cached"))
                rate = i / el if el else 0
                eta = (len(rows) - i) / rate / 60 if rate else float("nan")
                print(f"  {i:5d}/{len(rows)} locations | usable {done} | {el / 60:5.1f} min "
                      f"| eta {eta:5.1f} min", flush=True)
                pd.DataFrame(log).to_csv(OUT / "ingest_log.csv", index=False)
    if aborted:
        return 4

    L = pd.DataFrame(log)
    L.to_csv(OUT / "ingest_log.csv", index=False)
    print("\nstatus:", dict(L.status.value_counts()))
    if "failed" in L:
        print(f"objects that failed after retries: {int(L.failed.fillna(0).sum())}")
    if "units" in L:
        print("units seen:", sorted(set("|".join(L.units.dropna()).split("|")) - {""}))
    print(f"total {(time.time() - t0) / 60:.1f} min")
    n_err = int((L.status == "error").sum())
    if n_err:
        print(f"{n_err} locations ended in error and have no parquet. Re-run to retry them.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
