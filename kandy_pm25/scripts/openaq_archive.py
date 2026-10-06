"""openaq_archive.py -- one resumable cache of OpenAQ archive objects, shared by tests A and B.

Registered tests (2026-10-04): A, the full-network ladder (docs/prereg_full_network_ladder_2026-10-04.md);
B, the spatial learning curve on full records (docs/prereg_spatial_curve_full_record_2026-10-04.md).

UNIT = one (location, calendar year): every daily object under `locationid=<id>/year=<y>/` of
`s3://openaq-data-archive`, parsed, PM2.5 rows only, stored with the columns both registered pipelines
read (`datetime` as written, `value` coerced to numeric, `units`, `sensors_id`). Nothing is filtered,
floored or averaged here: A's and B's own registered transformations are applied downstream to exactly
these rows, so neither test's processing changes.

    data/processed/modular/openaq_archive/units/{loc}/{year}.parquet     the unit (exists = complete)
    data/processed/modular/openaq_archive/units/{loc}/{year}.json        listed, parsed, unparsable, time

RULES
  * A unit is written only if EVERY listed object was fetched. A transport failure is retried 5 times;
    if it still fails, the unit is not written and is redone on the next run. So no object can be lost
    silently (the failure mode `confirm_ingest_audit.py` had to estimate after the fact).
  * An object that downloads but cannot be parsed is skipped and COUNTED (`unparsable`), as the
    registered pipelines skipped it; it is not retried forever.
  * Writes are atomic (temp file + os.replace), so a stop loses at most the units in flight.
  * `night_guard.check()` runs before each unit is started: under night_window.sh the run stops
    cleanly before the deadline and exits 75 to resume the next night.

Usage:
  python scripts/openaq_archive.py --plan a|b|ab           # write the unit plan, print its size
  python scripts/openaq_archive.py --fetch a|b|ab [--workers 64] [--limit N]
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import sys
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import night_guard                                                       # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
ARCH = MOD / "openaq_archive"
UNITS = ARCH / "units"
BUCKET = "openaq-data-archive"
LOC_PREFIX = "records/csv.gz/locationid={loc}/"
YEAR_PREFIX = "records/csv.gz/locationid={loc}/year={year}/"
KEEP = ("datetime", "parameter", "units", "value", "sensors_id")
GUARD_MARGIN_S = 900                 # stop starting units 15 min before the deadline

# test A, as registered: up to 40 locations per city by record span
A_MAX = 40
A_CAP = 12                           # the old cap, re-applied for the reproduction check


# ── plans ─────────────────────────────────────────────────────────────────────────────────────
def _rank(locs: pd.DataFrame) -> pd.DataFrame:
    """Exactly ingest_openaq_sample.ingest_city's ranking: record span, longest first."""
    locs = locs.copy()
    locs["span"] = (pd.to_datetime(locs.dt_last, errors="coerce", utc=True)
                    - pd.to_datetime(locs.dt_first, errors="coerce", utc=True)).dt.days
    return locs.sort_values("span", ascending=False).drop_duplicates("loc_id")


def a_cities() -> list[dict]:
    """Every OpenAQ city of test A with its ranked locations, full window and capped years."""
    import ingest_openaq_sample as ios
    out = []
    # discovery: the OpenAQ cities that enter the ladder frame (station file AND driver file present)
    s = pd.read_csv(MOD / "validation_sample.csv")
    s = s[s.src == "OpenAQ"]
    cl = pd.read_csv(REPO / "data/processed/cnemc_panel/openaq_census/locations_clustered.csv")
    for r in s.itertuples():
        c = int(r.cluster)
        if not ((MOD / "openaq" / f"{c}.parquet").exists() and (MOD / "drivers" / f"{c}.csv").exists()):
            continue
        locs = _rank(cl[cl.cluster == c])
        dd = pd.to_datetime(pd.read_csv(MOD / "drivers" / f"{c}.csv", usecols=["date"]).date, errors="coerce")
        out.append(dict(panel="discovery", city=str(c), locs=locs,
                        w0=dd.min().normalize(), w1=dd.max().normalize(),
                        capped_years=ios.city_years(locs.head(A_CAP))))
    # confirmation: the registered member lists, metadata from the global census (as ueyfr)
    CD = MOD / "confirmation"
    M = pd.read_csv(CD / "confirmation_members.csv")
    g = pd.read_csv(REPO / "data/external/openaq/discovery/global_locations.csv", low_memory=False)
    g = g.rename(columns={"id": "location_id"})
    for cid, m in M.groupby("cid"):
        if not (CD / "drivers" / f"{cid}.csv").exists():
            continue
        x = m.merge(g[["location_id", "first", "last"]], on="location_id", how="left")
        locs = _rank(pd.DataFrame({"loc_id": x.location_id, "dt_first": x["first"], "dt_last": x["last"],
                                   "lat": x.lat, "lon": x.lon, "provider": np.nan,
                                   "is_monitor": x.is_monitor}))
        dd = pd.to_datetime(pd.read_csv(CD / "drivers" / f"{cid}.csv", usecols=["date"]).date)
        out.append(dict(panel="confirmation", city=str(cid), locs=locs,
                        w0=dd.min().normalize(), w1=dd.max().normalize(),
                        capped_years=ios.city_years(locs.head(A_CAP))))
    return out


def plan_a() -> pd.DataFrame:
    rows = []
    for c in a_cities():
        top = c["locs"].head(A_MAX)
        win_years = list(range(c["w0"].year, c["w1"].year + 1))
        for rank, r in enumerate(top.itertuples()):
            ys = set(win_years) | (set(c["capped_years"]) if rank < A_CAP else set())
            for y in sorted(ys):
                rows.append(dict(test="A", panel=c["panel"], city=c["city"], loc=int(r.loc_id),
                                 rank=rank, year=int(y)))
    return pd.DataFrame(rows)


def plan_b() -> pd.DataFrame:
    """Every candidate location of the registered curve, every year of its archive record (the
    year folders are listed, not guessed from metadata)."""
    C = pd.read_csv(MOD / "spatial_curve" / "candidates.csv")
    locs = sorted(C.location_id.astype(int).unique())
    s3 = client(16)
    with ThreadPoolExecutor(16) as ex:
        yrs = list(ex.map(lambda l: list_years(s3, l), locs))
    rows = [dict(test="B", panel="curve", city=str(int(C[C.location_id == l].cluster.iloc[0])), loc=l,
                 rank=-1, year=y) for l, ys in zip(locs, yrs) for y in ys]
    return pd.DataFrame(rows)


# ── S3 ────────────────────────────────────────────────────────────────────────────────────────
def client(pool: int):
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    return boto3.client("s3", config=Config(signature_version=UNSIGNED, region_name="us-east-1",
                                            max_pool_connections=pool + 16,
                                            retries={"max_attempts": 6, "mode": "standard"}))


def _retry(fn, tries=6):
    for k in range(tries):
        try:
            return fn()
        except Exception:                                                   # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(min(30, 2 ** k))


def list_years(s3, loc: int) -> list[int]:
    out, tok = [], None
    while True:
        kw = dict(Bucket=BUCKET, Prefix=LOC_PREFIX.format(loc=loc), Delimiter="/", MaxKeys=1000)
        if tok:
            kw["ContinuationToken"] = tok
        r = _retry(lambda: s3.list_objects_v2(**kw))
        for p in r.get("CommonPrefixes", []):
            v = p["Prefix"].rstrip("/").split("year=")[-1]
            if v.isdigit():
                out.append(int(v))
        tok = r.get("NextContinuationToken")
        if not tok:
            return sorted(out)


def list_keys(s3, loc: int, year: int) -> list[str]:
    keys, tok = [], None
    while True:
        kw = dict(Bucket=BUCKET, Prefix=YEAR_PREFIX.format(loc=loc, year=year), MaxKeys=1000)
        if tok:
            kw["ContinuationToken"] = tok
        r = _retry(lambda: s3.list_objects_v2(**kw))
        keys.extend(o["Key"] for o in r.get("Contents", []))
        tok = r.get("NextContinuationToken")
        if not tok:
            return keys


class Unparsable(Exception):
    pass


def get_object(s3, key: str) -> pd.DataFrame:
    body = _retry(lambda: s3.get_object(Bucket=BUCKET, Key=key)["Body"].read(), tries=5)
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(body)) as f:
            d = pd.read_csv(f)
    except Exception as e:                                                  # noqa: BLE001
        raise Unparsable(str(e)[:80]) from e
    if "parameter" in d.columns:
        d = d[d.parameter.astype(str).str.lower() == "pm25"]
    d = d[[c for c in KEEP if c in d.columns]].copy()
    if "value" in d:
        d["value"] = pd.to_numeric(d.value, errors="coerce")
    for c in ("datetime", "units"):
        if c in d:
            d[c] = d[c].astype(str)
    return d


def unit_path(loc: int, year: int) -> Path:
    return UNITS / str(loc) / f"{year}.parquet"


def fetch_unit(s3, pool: ThreadPoolExecutor, loc: int, year: int) -> dict:
    f = unit_path(loc, year)
    if f.exists():
        return dict(loc=loc, year=year, status="cached")
    t = time.time()
    keys = list_keys(s3, loc, year)
    bad = []

    def one(k):
        try:
            return get_object(s3, k)
        except Unparsable:
            bad.append(k)
            return None
    parts = list(pool.map(one, keys))           # a transport failure raises here: unit not written
    d = [p for p in parts if p is not None and len(p)]
    d = pd.concat(d, ignore_index=True) if d else pd.DataFrame(columns=list(KEEP[:1]) + ["value"])
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    d.to_parquet(tmp, index=False)
    meta = dict(loc=loc, year=year, listed=len(keys), parsed=len(keys) - len(bad), unparsable=len(bad),
                unparsable_keys=bad[:20], rows=len(d), fetched_utc=pd.Timestamp.utcnow().isoformat(),
                seconds=round(time.time() - t, 1))
    jt = f.with_suffix(".json.tmp")
    jt.write_text(json.dumps(meta), encoding="utf-8")
    os.replace(jt, f.with_suffix(".json"))     # metadata first, then the unit: the parquet marks completion
    os.replace(tmp, f)
    return dict(meta, status="ok")


# ── run ───────────────────────────────────────────────────────────────────────────────────────
def load_plan(which: str) -> pd.DataFrame:
    parts = []
    for t in which.lower():
        f = ARCH / f"plan_{t}.csv"
        if not f.exists():
            raise SystemExit(f"{f} missing: run --plan {t} first")
        parts.append(pd.read_csv(f))
    return pd.concat(parts, ignore_index=True)


def fetch(which: str, workers: int, limit: int) -> int:
    P = load_plan(which)
    U = P.drop_duplicates(["loc", "year"])[["loc", "year"]]
    todo = [(int(r.loc), int(r.year)) for r in U.itertuples() if not unit_path(r.loc, r.year).exists()]
    if limit:
        todo = todo[:limit]
    print(f"plan {which}: {len(U):,} units, {len(U) - len(todo) if not limit else '?'} cached, "
          f"{len(todo):,} to fetch", flush=True)
    s3 = client(workers)
    log, errors, t0 = [], 0, time.time()
    lock = threading.Lock()
    outer_n = max(4, workers // 8)
    with ThreadPoolExecutor(workers) as pool, ThreadPoolExecutor(outer_n) as outer:
        it, live, stopped = iter(todo), {}, False
        while True:
            while not stopped and len(live) < outer_n:
                nxt = next(it, None)
                if nxt is None:
                    break
                if night_guard.remaining() <= GUARD_MARGIN_S:
                    stopped = True
                    break
                live[outer.submit(fetch_unit, s3, pool, *nxt)] = nxt
            if not live:
                break
            done, _ = wait(live, return_when=FIRST_COMPLETED)
            for fu in done:
                loc, year = live.pop(fu)
                try:
                    r = fu.result()
                except Exception as e:                                      # noqa: BLE001
                    r = dict(loc=loc, year=year, status="error", error=f"{type(e).__name__}: {str(e)[:120]}")
                    errors += 1
                with lock:
                    log.append(r)
                n = len(log)
                if n % 50 == 0:
                    el = time.time() - t0
                    objs = sum(x.get("listed", 0) for x in log)
                    print(f"  {n:,}/{len(todo):,} units | {objs:,} objects | {objs / max(el, 1):.0f}/s | "
                          f"errors {errors} | {el / 60:.1f} min", flush=True)
    L = pd.DataFrame(log)
    if len(L):
        lf = ARCH / "fetch_log.csv"
        L.drop(columns=[c for c in ("unparsable_keys",) if c in L], errors="ignore").to_csv(
            lf, mode="a", header=not lf.exists(), index=False)
    left = sum(not unit_path(r.loc, r.year).exists() for r in U.itertuples())
    print(f"run: {len(L)} units, {errors} errors, {left:,} units still missing, "
          f"{(time.time() - t0) / 60:.1f} min", flush=True)
    if stopped and left:
        print("deadline reached with work left: resume next night", flush=True)
        return night_guard.COME_BACK_TOMORROW
    return 0 if left == 0 else 3


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", choices=["a", "b", "ab"])
    g.add_argument("--fetch", choices=["a", "b", "ab"])
    ap.add_argument("--workers", type=int, default=64)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    ARCH.mkdir(parents=True, exist_ok=True)
    if a.plan:
        for t in a.plan:
            P = plan_a() if t == "a" else plan_b()
            tmp = ARCH / f"plan_{t}.tmp"
            P.to_csv(tmp, index=False); os.replace(tmp, ARCH / f"plan_{t}.csv")
            u = P.drop_duplicates(["loc", "year"])
            print(f"plan {t.upper()}: {P.city.nunique()} cities, {P['loc'].nunique():,} locations, "
                  f"{len(u):,} location-years (~{365 * len(u) / 1e6:.2f} M daily objects at most)")
        return 0
    return fetch(a.fetch, a.workers, a.limit)


if __name__ == "__main__":
    sys.exit(main())
