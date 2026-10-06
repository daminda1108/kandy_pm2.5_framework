"""cnemc_drivers_pullcity.py -- the discovery CNEMC cities' daily drivers by pull_city, the function
every OpenAQ city (and every confirmation city) uses.

Why (2026-09-26): discovery CNEMC drivers came from `met_raw/cnemc_era5_*.csv`, a different pull. On
city044 (2024-01..06) the two agree closely but not exactly (r 0.96-0.998; BLH max |d| 272 m). Ladder
v2 trains on discovery and applies to confirmation, so every city must carry drivers from ONE
function. v1 is left untouched (ladder_frames.build_bud0_frame(cnemc_drivers="met_raw") reproduces it).

Out: data/processed/modular/drivers_cnemc_pullcity/{slug}.csv
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "data" / "processed" / "modular" / "drivers_cnemc_pullcity"


def main() -> int:
    import ee
    ee.Initialize(project="kandypinn")
    from pull_openaq_drivers import pull_city
    from modular_validation_all import drivers_cnemc
    from src.modular.city_meta import city_meta
    m = city_meta()
    cn = m[m.src == "CNEMC"]
    old = drivers_cnemc()
    OUT.mkdir(parents=True, exist_ok=True)
    fails = 0
    for r in cn.itertuples():
        f = OUT / f"{r.city}.csv"
        if f.exists():
            continue
        w = old[old.slug == r.city].date
        s0 = (w.min() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        s1 = (w.max() + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
        try:
            d = pull_city(r.lat, r.lon, years=(s0, s1))
            d.insert(0, "slug", r.city)
            tmp = f.with_suffix(".csv.tmp"); d.to_csv(tmp, index=False); os.replace(tmp, f)
            print(f"  {r.city}: {len(d)} days {s0}..{s1}", flush=True)
        except Exception as e:                                             # noqa: BLE001
            fails += 1
            print(f"  {r.city}: FAILED {type(e).__name__}: {str(e)[:100]}", flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
