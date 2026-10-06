"""confirmation_predictors.py -- PREDICTORS for the ladder-v2 confirmation panel. No PM2.5 is read.
(redesign plan §7 step 6; the registration stays blind because nothing here touches the target)

For each city in confirmation/confirmation_panel.csv (76 cities, cap 4, frozen 2026-09-26):
  drivers  daily ERA5-Land t2m/u10/v10/wind + ERA5 BLH at 00/06/12/18 UTC, by the SAME function the
           discovery OpenAQ arm used (pull_openaq_drivers.pull_city)
  aod      daily best-quality MAIAC AOD in a 5 km buffer, by the SAME function the discovery pull used
           (build_bud0_maiac.pull_city_year)
Window: 2024-09-01 .. 2026-08-31, the census window the panel was selected on.
Static geography (urban-centre grid) is built by build_static_geo_grid.py --panel confirmation.

Out: data/processed/modular/confirmation/{drivers,aod}/{cid}.csv
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
MOD = REPO / "data" / "processed" / "modular"
CD = MOD / "confirmation"
W0, W1 = "2024-09-01", "2026-09-01"          # end exclusive


def _write(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".csv.tmp"); df.to_csv(tmp, index=False); os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("drivers", "aod", "all"), default="all")
    a = ap.parse_args()
    import ee
    ee.Initialize(project="kandypinn")
    from pull_openaq_drivers import pull_city
    from build_bud0_maiac import pull_city_year

    P = pd.read_csv(CD / "confirmation_panel.csv")
    fails = []
    for i, r in enumerate(P.itertuples(), 1):
        try:
            fd = CD / "drivers" / f"{r.cid}.csv"
            if a.stage in ("drivers", "all") and not fd.exists():
                m = pull_city(r.lat, r.lon, years=(W0, W1))
                m.insert(0, "city", r.cid)
                _write(m, fd)
            fa = CD / "aod" / f"{r.cid}.csv"
            if a.stage in ("aod", "all") and not fa.exists():
                parts = []
                for yr in (2024, 2025, 2026):
                    d0 = max(W0, f"{yr}-01-01"); d1 = min(W1, f"{yr + 1}-01-01")
                    got = pull_city_year(r.lat, r.lon, yr, d0, d1)
                    if got is None:
                        raise RuntimeError(f"MAIAC {yr} failed after retries")
                    parts.append(got)
                d = pd.concat(parts, ignore_index=True)
                d.insert(0, "city", r.cid)
                _write(d, fa)
            print(f"  [{i}/{len(P)}] {r.cid:<16} ok", flush=True)
        except Exception as e:                                             # noqa: BLE001
            fails.append((r.cid, f"{type(e).__name__}: {str(e)[:100]}"))
            print(f"  [{i}/{len(P)}] {r.cid:<16} FAILED {fails[-1][1]}", flush=True)
    print(f"\n{len(P) - len(fails)} of {len(P)} complete; {len(fails)} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
