"""confirm_ingest_parallel.py -- run the registered confirmation ingest in disjoint city shards.

Execution-only change (2026-09-28, logged as E-1 in confirmation/DEVIATIONS.md before scoring):
`ladder_v2_confirm.ingest()` fetches the 64 OpenAQ cities one after another (~10 min each, ~10 h).
This wrapper runs the SAME loop body -- the frozen `ingest_openaq_sample.ingest_city`, the same
member list, the same output directory and the same skip-if-present rule -- on the cities whose
position in the sorted member list is k mod n. Shards are disjoint, so no two processes write one
city. Each shard writes its own manifest; `--merge` combines them.

Usage:
  python scripts/confirm_ingest_parallel.py --shard 0 --n 3
  python scripts/confirm_ingest_parallel.py --merge
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import ladder_v2_confirm as lvc                                         # noqa: E402


def shard(k: int, n: int) -> None:
    lvc._require_registered()
    import ingest_openaq_sample as ios
    ios.OUT = lvc.CD / "openaq"
    M = pd.read_csv(lvc.CD / "confirmation_members.csv")
    g = pd.read_csv(REPO / "data/external/openaq/discovery/global_locations.csv", low_memory=False)
    g = g.rename(columns={"id": "location_id"})
    rows = []
    for i, (cid, m) in enumerate(M.groupby("cid")):          # same order as ingest()
        if i % n != k:
            continue
        f = ios.OUT / f"{cid}.parquet"
        if f.exists():
            continue
        locs = m.merge(g[["location_id", "first", "last"]], on="location_id", how="left")
        locs = pd.DataFrame({"loc_id": locs.location_id, "dt_first": locs["first"],
                             "dt_last": locs["last"], "lat": locs.lat, "lon": locs.lon,
                             "provider": np.nan, "is_monitor": locs.is_monitor})
        r = ios.ingest_city(cid, locs)
        rows.append(r)
        print(f"  {cid:<16} {r['status']} stations={r['stations']} rows={r['rows']}", flush=True)
        man = lvc.CD / f"ingest_manifest_shard{k}.csv"            # after every city: survives a kill
        old = pd.read_csv(man) if man.exists() else pd.DataFrame()
        pd.concat([old, pd.DataFrame([r])], ignore_index=True).to_csv(man, index=False)


def merge() -> None:
    parts = sorted(lvc.CD.glob("ingest_manifest_shard*.csv"))
    d = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
    d.to_csv(lvc.CD / "ingest_manifest.csv", index=False)
    print(d.status.value_counts().to_string(), f"\n{len(d)} cities in manifest")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int); ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--merge", action="store_true")
    a = ap.parse_args()
    merge() if a.merge else shard(a.shard, a.n)
