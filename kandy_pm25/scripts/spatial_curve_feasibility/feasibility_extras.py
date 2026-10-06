"""Two feasibility measurements for the spatial learning curve, kept so the plan can be audited.

1. Change-of-support exposure: per dense city, the median nearest-neighbour distance between
   reference stations and the share of stations with another within 1 km (one model cell).
2. Co-located instruments: how many distinct SITES remain when stations closer than 50, 100 and
   250 m are merged, and the frame projected after merging and 85 per cent coverage survival.

Reads concurrent_density.csv, written by concurrent_density.py in the same directory.
Out: support_floor.csv, colocation.csv beside this file.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).parent
REPO = Path(r"D:\ProjectCD\kandy_pm25")

C = pd.read_csv(HERE / "concurrent_density.csv")
C = C[C.conc_365 >= 15]
g = pd.read_csv(REPO / "data/external/openaq/discovery/global_locations.csv")
g = g[g.is_monitor].dropna(subset=["lat", "lon"])


def km_matrix(la, lo, lat0):
    return 111 * np.hypot(la[:, None] - la[None], (lo[:, None] - lo[None]) * np.cos(np.radians(lat0)))


def sites(la, lo, lat0, r_km):
    """Greedy merge of stations closer than r_km into one site; returns the site count."""
    n = len(la); sid = -np.ones(n, int); c = 0
    for i in range(n):
        if sid[i] >= 0:
            continue
        d = 111 * np.hypot(la - la[i], (lo - lo[i]) * np.cos(np.radians(lat0)))
        sid[(d <= r_km) & (sid < 0)] = c
        c += 1
    return c


floor, colo = [], []
for r in C.itertuples():
    km = 111 * np.hypot(g.lat - r.lat, (g.lon - r.lon) * np.cos(np.radians(r.lat)))
    s = g[km < 25]
    la, lo = s.lat.to_numpy(), s.lon.to_numpy()
    D = km_matrix(la, lo, r.lat)
    np.fill_diagonal(D, np.inf)
    nn = D.min(1)
    floor.append(dict(cluster=r.cluster, band=r.band, country=r.country, n=len(s),
                      nn_median_km=round(float(np.median(nn)), 2),
                      share_with_neighbour_lt_1km=round(float((nn < 1).mean()), 3)))
    colo.append(dict(cluster=r.cluster, band=r.band, country=r.country, stations=len(s),
                     sites_50m=sites(la, lo, r.lat, 0.05), sites_100m=sites(la, lo, r.lat, 0.10),
                     sites_250m=sites(la, lo, r.lat, 0.25), conc_365=r.conc_365))

F = pd.DataFrame(floor)
F.to_csv(HERE / "support_floor.csv", index=False)
print(f"change of support: median nearest neighbour {F.nn_median_km.median():.2f} km, "
      f"median share within 1 km {F.share_with_neighbour_lt_1km.median():.3f}")

R = pd.DataFrame(colo)
R["keep_frac_100m"] = (R.sites_100m / R.stations).round(3)
R.to_csv(HERE / "colocation.csv", index=False)
print(f"co-location: {R.stations.sum()} stations -> {R.sites_100m.sum()} sites at 100 m "
      f"({R.sites_100m.sum() / R.stations.sum():.1%})")
adj = (R.conc_365 * R.keep_frac_100m * 0.85).round()
for thr in (15, 20, 30):
    print(f"  projected cities with >= {thr} sites: {int((adj >= thr).sum())}  "
          f"bands {dict(R[adj >= thr].band.value_counts())}")
