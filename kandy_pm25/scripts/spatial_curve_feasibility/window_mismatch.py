"""How badly do station records disagree on time window inside the current spatial frame?

spatial_proxy_scan.station_means() averages each station over its WHOLE record. If stations in
one city cover different periods, part of the between-station contrast is temporal. Measure it:
per city, the overlap of all station records, and how much a station's whole-record mean moves
when recomputed over the city's common window.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO = Path(r"D:\ProjectCD\kandy_pm25")
MOD = REPO / "data/processed/modular"

lur = pd.read_csv(MOD / "lur_predictors.csv")
lur["city"] = lur.city.astype(str)
cities = set(lur[lur.src == "OpenAQ"].city)

f0 = next(iter(sorted((MOD / "openaq").glob("*.parquet"))))
cols = pd.read_parquet(f0).columns.tolist()
tcol = next(c for c in cols if "date" in c.lower() or "time" in c.lower())
print(f"parquet columns: {cols} | time column used: {tcol}")

rows = []
for c in sorted(cities):
    f = MOD / "openaq" / f"{c}.parquet"
    if not f.exists():
        continue
    d = pd.read_parquet(f, columns=["station_id", tcol, "pm25"]).dropna()
    d[tcol] = pd.to_datetime(d[tcol], utc=True)
    keep = set(lur[lur.city == c].station_id.astype(str))
    d["station_id"] = d.station_id.astype(str)
    d = d[d.station_id.isin(keep)]
    if d.station_id.nunique() < 6:
        continue
    span = d.groupby("station_id")[tcol].agg(["min", "max"])
    lo, hi = span["min"].max(), span["max"].min()          # common window of ALL stations
    common_days = max(0, (hi - lo).days)
    whole = d.groupby("station_id").pm25.mean()
    if common_days >= 90:
        w = d[(d[tcol] >= lo) & (d[tcol] <= hi)].groupby("station_id").pm25.mean()
        j = pd.concat([whole.rename("whole"), w.rename("common")], axis=1).dropna()
        rho = spearmanr(j.whole, j.common).statistic if len(j) >= 4 else np.nan
        shift = float(np.median(np.abs(j.common / j.whole - 1)) * 100)
    else:
        rho, shift = np.nan, np.nan
    start_spread = (span["min"].max() - span["min"].min()).days
    rows.append(dict(city=c, stations=len(span), start_spread_days=start_spread,
                     common_days=common_days, rank_rho_whole_vs_common=rho,
                     median_abs_shift_pct=shift))

R = pd.DataFrame(rows)
R.to_csv(Path(__file__).with_name("window_mismatch.csv"), index=False)
print(f"\nOpenAQ cities scored: {len(R)}")
print(f"station start dates spread within a city, median: {R.start_spread_days.median():.0f} days")
print(f"cities whose stations share NO common window of >= 90 days: "
      f"{int((R.common_days < 90).sum())} of {len(R)}")
ok = R.dropna(subset=["rank_rho_whole_vs_common"])
print(f"where a common window exists ({len(ok)} cities):")
print(f"  median rank agreement, whole-record vs common-window means: "
      f"{ok.rank_rho_whole_vs_common.median():.3f} "
      f"(min {ok.rank_rho_whole_vs_common.min():.3f})")
print(f"  median absolute shift in a station's mean: {ok.median_abs_shift_pct.median():.1f} %")
print("\nworst ten by rank agreement:")
print(ok.nsmallest(10, "rank_rho_whole_vs_common").to_string(index=False))
