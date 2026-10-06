"""drivers_v2_pull.py -- re-pull every city's daily drivers with the chunk-boundary fix (2026-09-27).

`pull_openaq_drivers.pull_city` split its window at calendar quarter starts INSIDE the window and
so never requested the head (window start -> first quarter start) or the tail (last quarter
start -> window end) of the ERA5 BLH series (nor of the coastal ERA5 fallback). Those days carried
NaN BLH and were dropped from every ladder frame. Fixed in `_bounded_quarters`.

  --panel discovery     -> data/processed/modular/drivers_v2/{city}.csv  (OpenAQ AND CNEMC cities,
                           each over the same window as its v1 file; v1 files are left untouched so
                           the v1 ladder still reproduces)
  --panel confirmation  -> data/processed/modular/confirmation/drivers/{cid}.csv (overwritten:
                           nothing has been computed from them)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
MOD = REPO / "data" / "processed" / "modular"


def _write(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".csv.tmp"); df.to_csv(tmp, index=False); os.replace(tmp, path)


def targets(panel):
    if panel == "confirmation":
        P = pd.read_csv(MOD / "confirmation" / "confirmation_panel.csv")
        return [(r.cid, r.lat, r.lon, "2024-09-01", "2026-09-01",
                 MOD / "confirmation" / "drivers" / f"{r.cid}.csv") for r in P.itertuples()]
    from src.modular.city_meta import city_meta
    out = []
    for r in city_meta().itertuples():
        old = (MOD / "drivers" / f"{r.city}.csv" if r.src == "OpenAQ"
               else MOD / "drivers_cnemc_pullcity" / f"{r.city}.csv")
        if not old.exists():
            continue                                  # a city never ingested (failed draw)
        d = pd.to_datetime(pd.read_csv(old, usecols=["date"]).date)
        s0 = d.min().strftime("%Y-%m-%d")
        s1 = (d.max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        out.append((r.city, r.lat, r.lon, s0, s1, MOD / "drivers_v2" / f"{r.city}.csv"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", choices=("discovery", "confirmation"), required=True)
    ap.add_argument("--force", action="store_true", help="re-pull even if the v2 file exists")
    a = ap.parse_args()
    import ee
    ee.Initialize(project="kandypinn")
    from pull_openaq_drivers import pull_city
    T = targets(a.panel)
    fails = 0
    for i, (city, lat, lon, s0, s1, f) in enumerate(T, 1):
        if f.exists() and not a.force and _is_fixed(f, s0):
            continue
        try:
            m = pull_city(lat, lon, years=(s0, s1))
            m.insert(0, "city", city)
            _write(m, f)
            print(f"  [{i}/{len(T)}] {city:<16} {s0}..{s1}  days {len(m)}  "
                  f"BLH NaN {int(m.boundary_layer_height.isna().sum())}", flush=True)
        except Exception as e:                                             # noqa: BLE001
            fails += 1
            print(f"  [{i}/{len(T)}] {city:<16} FAILED {type(e).__name__}: {str(e)[:100]}", flush=True)
    print(f"{len(T) - fails} of {len(T)} ok")
    return 1 if fails else 0


def _is_fixed(f: Path, s0: str) -> bool:
    """A file pulled after the fix has BLH on its first day."""
    d = pd.read_csv(f, usecols=["date", "boundary_layer_height"])
    first = d[d.date == d.date.min()].boundary_layer_height
    return bool(first.notna().any())


if __name__ == "__main__":
    raise SystemExit(main())
