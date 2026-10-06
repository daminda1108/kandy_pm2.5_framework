"""How much does discovery METADATA overstate concurrency? Check against cached real data.

concurrent_density.py counts stations whose first-to-last report covers a window. Gaps inside
that span are invisible there. For every dense candidate that already has a cached station
parquet, count the stations with at least 75% of days present across the best 365-day window,
and compare with the metadata figure.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).parent
REPO = Path(r"D:\ProjectCD\kandy_pm25")
MOD = REPO / "data/processed/modular"

C = pd.read_csv(HERE / "concurrent_density.csv")
C = C[C.conc_365 >= 15].copy()
man = pd.read_csv(MOD / "openaq_manifest.csv")
man = man[man.status == "OK"]

rows = []
for r in C.itertuples():
    km = 111 * np.hypot(man.lat - r.lat, (man.lon - r.lon) * np.cos(np.radians(r.lat)))
    hit = man[km < 25]
    if hit.empty:
        rows.append(dict(cluster=r.cluster, band=r.band, country=r.country, meta_1y=r.conc_365,
                         cached=False))
        continue
    cl = int(hit.iloc[0].cluster)
    f = MOD / "openaq" / f"{cl}.parquet"
    if not f.exists():
        rows.append(dict(cluster=r.cluster, band=r.band, country=r.country, meta_1y=r.conc_365,
                         cached=False))
        continue
    d = pd.read_parquet(f, columns=["station_id", "datetime_utc", "pm25", "is_monitor"])
    d = d[d.is_monitor.astype(bool)].dropna(subset=["pm25"])
    d["day"] = pd.to_datetime(d.datetime_utc, utc=True).dt.floor("D")
    pres = (d.groupby(["station_id", "day"]).size().unstack(0).notna())
    pres = pres.reindex(pd.date_range(pres.index.min(), pres.index.max(), freq="D", tz="UTC"),
                        fill_value=False)
    roll = pres.rolling(365, min_periods=365).mean()          # fraction of days present
    best = int((roll >= 0.75).sum(axis=1).max()) if len(roll) >= 365 else 0
    span_days = (pres.index.max() - pres.index.min()).days
    rows.append(dict(cluster=r.cluster, band=r.band, country=r.country, meta_1y=r.conc_365,
                     cached=True, manifest_cluster=cl, stations_in_cache=pres.shape[1],
                     cache_span_days=span_days, real_1y_75pct=best))

R = pd.DataFrame(rows)
R.to_csv(HERE / "cached_concurrency.csv", index=False)
k = R[R.cached]
print(f"dense candidates (meta >= 15): {len(R)} | already cached locally: {len(k)}")
if len(k):
    k = k.assign(ratio=k.real_1y_75pct / k.meta_1y)
    print(k[["cluster", "band", "country", "meta_1y", "stations_in_cache", "cache_span_days",
             "real_1y_75pct", "ratio"]].to_string(index=False))
    print(f"\nmedian real/metadata ratio: {k.ratio.median():.2f}")
print("\nnot cached (need ingest):", len(R) - len(k), "cities;",
      dict(R[~R.cached].band.value_counts()))
