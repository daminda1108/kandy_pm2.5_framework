"""How many cities in each latitude band could be scored at all?  (ledger F.53, 2026-09-04)

THE CLAIM THIS SETTLES. §4.6 states that the association between instrument class and latitude
band cannot be broken by sampling a better panel, because the population of candidate cities
does not contain a balanced draw. That is a statement about the world's monitoring network and
not about our panel, and it was a pair of literals -- "only five deep-tropical clusters have ten
or more concurrent reference stations, against 32 temperate" -- with nothing behind it on disk.

WHAT IS COUNTED. Every OpenAQ location reporting PM2.5, clustered greedily at CLUSTER_KM, and a
cluster is counted when at least MIN_STATIONS of its REFERENCE-GRADE stations were reporting
over a common window. Reference class is OpenAQ's own `isMonitor` flag, so the classification is
the provider's rather than ours.

⚠ WHAT THIS IS NOT. OpenAQ is not the world's monitoring network; it is the part of it that is
openly published. Networks that do not federate -- and several large national ones do not --
are invisible here, so these counts are a lower bound on what exists and an accurate count of
what an outside researcher could actually assemble. That second reading is the one §4.6 needs,
and it is the one stated.

Usage: .venv/Scripts/python.exe scripts/global_reference_census.py [--refresh]
Out:   data/processed/modular/global_reference_census.csv    (one row per cluster)
       data/processed/paper_figures/global_census.json
       data/external/openaq/discovery/global_locations.csv   (raw pull, cached)
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from figdata import emit  # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
CACHE = REPO / "data" / "external" / "openaq" / "discovery" / "global_locations.csv"
KEYFILE = REPO.parent / "API.txt"

API = "https://api.openaq.org/v3/locations"
PM25_PARAM = 2                 # OpenAQ parameter id for PM2.5
PAGE = 1000
CLUSTER_KM = 25.0              # the radius the project's own OpenAQ discovery used
MIN_STATIONS = 10              # "ten or more concurrent reference stations"
MIN_OVERLAP_DAYS = 365         # what "concurrent" means, stated rather than implied


def band(lat: float) -> str:
    a = abs(lat)
    return ("deep_tropical" if a < 15 else "tropical" if a < 23.5
            else "subtropical" if a < 35 else "temperate")


def api_key() -> str:
    txt = io.open(KEYFILE, encoding="utf-8", errors="replace").read()
    m = re.search(r"OpenAQ API\s*:\s*([0-9a-fA-F]{32,})", txt)
    if not m:
        raise SystemExit("no OpenAQ key found in API.txt")
    return m.group(1)


def pull() -> pd.DataFrame:
    """Every PM2.5 location OpenAQ publishes, one page at a time."""
    key, rows, page = api_key(), [], 1
    while True:
        r = requests.get(API, headers={"X-API-Key": key},
                         params={"parameters_id": PM25_PARAM, "limit": PAGE, "page": page},
                         timeout=60)
        if r.status_code == 429:
            time.sleep(8)
            continue
        r.raise_for_status()
        got = r.json().get("results", [])
        if not got:
            break
        for L in got:
            co = L.get("coordinates") or {}
            if co.get("latitude") is None:
                continue
            rows.append(dict(
                id=L.get("id"), name=L.get("name"),
                lat=co["latitude"], lon=co["longitude"],
                is_monitor=bool(L.get("isMonitor")),
                country=(L.get("country") or {}).get("code"),
                first=(L.get("datetimeFirst") or {}).get("utc"),
                last=(L.get("datetimeLast") or {}).get("utc")))
        print(f"    page {page:>3}  {len(rows):>6} locations", end="\r")
        if len(got) < PAGE:
            break
        page += 1
        time.sleep(0.25)
    print()
    return pd.DataFrame(rows)


def cluster(d: pd.DataFrame) -> pd.DataFrame:
    """Greedy fixed-radius clustering, densest seed first. Deterministic."""
    lat = np.radians(d.lat.values)
    lon = np.radians(d.lon.values)
    n = len(d)
    cid = np.full(n, -1)
    order = np.argsort(-d.lat.values)          # deterministic, arbitrary, order-independent
    nxt = 0
    for i in order:
        if cid[i] >= 0:
            continue
        dl = lon - lon[i]
        h = (np.sin((lat - lat[i]) / 2) ** 2
             + np.cos(lat) * np.cos(lat[i]) * np.sin(dl / 2) ** 2)
        km = 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(h, 0, 1)))
        near = (km <= CLUSTER_KM) & (cid < 0)
        cid[near] = nxt
        nxt += 1
    out = d.copy()
    out["cluster"] = cid
    return out


def main() -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--refresh", action="store_true", help="re-pull instead of using the cache")
    args = a.parse_args()

    if CACHE.exists() and not args.refresh:
        d = pd.read_csv(CACHE)
        print(f"cached pull: {len(d):,} PM2.5 locations  ({CACHE.name})")
    else:
        print("pulling every PM2.5 location OpenAQ publishes")
        d = pull()
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        d.to_csv(CACHE, index=False)
        print(f"  wrote {CACHE.relative_to(REPO)}  --  {len(d):,} locations")

    d = d.dropna(subset=["lat", "lon"])
    # `first` and `last` are DataFrame METHODS, so d.first is a bound method and never the
    # column. Renamed rather than accessed by bracket, so the trap cannot come back.
    d = d.rename(columns={"first": "t_first", "last": "t_last"})
    d["t_first"] = pd.to_datetime(d["t_first"], errors="coerce", utc=True)
    d["t_last"] = pd.to_datetime(d["t_last"], errors="coerce", utc=True)
    ref = d[d.is_monitor & d.t_first.notna() & d.t_last.notna()].copy()
    print(f"  reference-grade with dates: {len(ref):,} of {len(d):,}")

    ref = cluster(ref)
    ref["band"] = ref.lat.map(band)

    rows = []
    for cl, g in ref.groupby("cluster"):
        if len(g) < MIN_STATIONS:
            continue
        # concurrency: the widest window in which MIN_STATIONS were simultaneously reporting.
        # Taking the MIN_STATIONS-th latest start against the MIN_STATIONS-th earliest end is
        # the exact test -- a count of stations that merely EXISTED is not concurrency.
        start = np.sort(g.t_first.values)[MIN_STATIONS - 1]
        end = np.sort(g.t_last.values)[::-1][MIN_STATIONS - 1]
        overlap = (pd.Timestamp(end) - pd.Timestamp(start)).days
        if overlap < MIN_OVERLAP_DAYS:
            continue
        rows.append(dict(cluster=int(cl), band=g.band.mode().iloc[0], n_ref=len(g),
                         lat=float(g.lat.mean()), lon=float(g.lon.mean()),
                         overlap_days=int(overlap),
                         country=g.country.mode().iloc[0] if g.country.notna().any() else ""))
    C = pd.DataFrame(rows)
    if C.empty:
        print("  no clusters met the threshold -- check the pull")
        return 1

    counts = C.band.value_counts().to_dict()
    print(f"\n  clusters with >= {MIN_STATIONS} concurrent reference stations "
          f"(>= {MIN_OVERLAP_DAYS} days overlap):")
    for b in ("deep_tropical", "tropical", "subtropical", "temperate"):
        print(f"    {b:<15} {counts.get(b, 0):>4}")
    C.sort_values(["band", "n_ref"], ascending=[True, False]).to_csv(
        MOD / "global_reference_census.csv", index=False)
    print(f"\n  wrote {(MOD / 'global_reference_census.csv').relative_to(REPO)}")

    emit("global_census",
         deep_tropical=int(counts.get("deep_tropical", 0)),
         tropical=int(counts.get("tropical", 0)),
         subtropical=int(counts.get("subtropical", 0)),
         temperate=int(counts.get("temperate", 0)),
         min_stations=MIN_STATIONS,
         min_overlap_days=MIN_OVERLAP_DAYS,
         cluster_km=CLUSTER_KM,
         reference_locations=int(len(ref)),
         total_locations=int(len(d)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
