"""support_collapse_test.py -- does within-city contrast really collapse with averaging support?

WHY THIS TEST EXISTS
--------------------
F.68-F.71 assembled a four-rung "support ladder" for Kandy: within-city PM contrast measured at
85x (3-hour kerbside, 25 sites), 4.0x (8-hour land-use strata, 20 sites), 3.0x (24-hour fixed,
5 sites) and 1.23x (this model, 1 km annual). The monotone collapse is the paper's headline
explanation for why the spatial axis has a ceiling.

The obvious objection is that those four numbers come from four different studies with different
instruments, different pollutants (PM10 vs PM2.5), different siting and eras spanning 2004-2022 --
so the "collapse" could be an artefact of comparing incompatible measurements rather than a
property of averaging.

This test answers that with data we own. At three cities with dense networks -- same instrument
class within a city, same era, same pollutant -- we measure the across-station contrast as a
function of the averaging window. If contrast collapses monotonically here too, the mechanism is
real and the Kandy ladder is an instance of it rather than a coincidence of heterogeneous sources.

WHAT IS COMPUTED
    For each averaging window w, resample every station to w, then AT EACH TIME STEP compute the
    across-station contrast (p90/p10, and max/min). Report the median over time steps. This
    mirrors how the literature measurements were actually made: a snapshot at some averaging
    support, and the spread across sites within it.

    Only time steps with at least MIN_STN concurrent reporting stations are used, so the contrast
    is not driven by a shrinking sample.

NOTE This isolates the TEMPORAL half of the support effect. The spatial half -- what happens when
     point measurements are averaged over a 1 km cell -- cannot be measured from point networks
     at all, and that is precisely why the Kandy literature (which samples at 300 m separations)
     is needed for it.

Usage:  python scripts/support_collapse_test.py
Out:    data/processed/modular/support_collapse.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "processed" / "modular" / "support_collapse.csv"

CITIES = ["medellin", "kathmandu", "chiangmai"]
WINDOWS = [("1h", "1h"), ("3h", "3h"), ("8h", "8h"), ("24h", "1D"),
           ("weekly", "7D"), ("monthly", "30D"), ("annual", "365D")]
MIN_STN = 5          # minimum concurrent stations for a time step to count
MIN_STEPS = 5        # minimum qualifying time steps for a window to be reported


def contrast(city: str) -> list[dict]:
    f = REPO / f"data/processed/stage2/{city}_perstation_v13.parquet"
    d = pd.read_parquet(f, columns=["datetime_utc", "station_id", "pm25"])
    d = d.dropna(subset=["pm25"])
    d = d[d.pm25 > 0]                       # zeros/negatives break a ratio
    d["t"] = pd.to_datetime(d.datetime_utc)
    piv = d.pivot_table(index="t", columns="station_id", values="pm25", aggfunc="mean")
    print(f"\n=== {city}: {piv.shape[1]} stations, {piv.shape[0]} hourly steps, "
          f"{piv.index.min().date()} to {piv.index.max().date()}")

    rows = []
    for label, rule in WINDOWS:
        r = piv if rule == "1h" else piv.resample(rule).mean()
        n = r.notna().sum(axis=1)
        r = r[n >= MIN_STN]
        if len(r) < MIN_STEPS:
            print(f"  {label:<8} too few qualifying steps ({len(r)})")
            continue
        p90 = r.quantile(0.90, axis=1)
        p10 = r.quantile(0.10, axis=1)
        mx, mn = r.max(axis=1), r.min(axis=1)
        ok = (p10 > 0) & (mn > 0)
        rat_r = (p90[ok] / p10[ok]).median()
        rat_x = (mx[ok] / mn[ok]).median()
        rows.append(dict(city=city, window=label, n_steps=int(ok.sum()),
                         med_stations=float(n[n >= MIN_STN].median()),
                         p90_p10=round(float(rat_r), 3), max_min=round(float(rat_x), 3)))
        print(f"  {label:<8} steps={int(ok.sum()):>6}  stations={n[n>=MIN_STN].median():4.0f}   "
              f"p90/p10 = {rat_r:5.2f}x    max/min = {rat_x:6.2f}x")
    return rows


def main() -> None:
    rows = []
    for c in CITIES:
        try:
            rows += contrast(c)
        except Exception as e:
            print(f"  {c}: FAILED {str(e)[:80]}")
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    if df.empty:
        print("\nno results")
        return

    print("\n=== ACROSS-STATION CONTRAST vs AVERAGING WINDOW (p90/p10) ===")
    piv = df.pivot_table(index="window", columns="city", values="p90_p10")
    piv = piv.reindex([w for w, _ in WINDOWS if w in piv.index])
    print(piv.round(2).to_string())

    print("\n=== is the collapse monotone in each city? ===")
    for c in df.city.unique():
        s = df[df.city == c].set_index("window").p90_p10
        s = s.reindex([w for w, _ in WINDOWS if w in s.index]).dropna()
        mono = bool((np.diff(s.values) <= 1e-9).all())
        print(f"  {c:<11} {' -> '.join(f'{v:.2f}' for v in s.values)}   "
              f"{'MONOTONE' if mono else 'NOT monotone'}"
              f"   total collapse {s.iloc[0]/s.iloc[-1]:.2f}x")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
