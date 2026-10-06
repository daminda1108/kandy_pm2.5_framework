"""True concurrent density per cluster, from OpenAQ discovery metadata.

global_reference_census.py reports n_ref = every reference station that ever existed in a
cluster. For a within-city spatial test what matters is how many report TOGETHER over a common
window. For each cluster and window length W, slide a window across time and count the
reference stations whose [t_first, t_last] fully covers it; report the maximum.

UPPER BOUND ONLY: t_first/t_last are the first and last report, so gaps in between are invisible.
The real count needs the station time series.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(r"D:\ProjectCD\kandy_pm25")
CACHE = REPO / "data/external/openaq/discovery/global_locations.csv"
CLUSTER_KM = 25.0


def band(lat):
    a = abs(lat)
    return ("deep_tropical" if a < 15 else "tropical" if a < 23.5
            else "subtropical" if a < 35 else "temperate")


def cluster(d):
    """Greedy fixed-radius clustering, densest seed first. Same rule as the census."""
    lat = np.radians(d.lat.to_numpy()); lon = np.radians(d.lon.to_numpy())
    n = len(d); cid = np.full(n, -1)
    # density = neighbours within radius, computed once
    order = np.arange(n)
    dens = np.zeros(n, int)
    for i in range(n):
        h = (np.sin((lat - lat[i]) / 2) ** 2
             + np.cos(lat[i]) * np.cos(lat) * np.sin((lon - lon[i]) / 2) ** 2)
        dens[i] = int((2 * 6371 * np.arcsin(np.sqrt(np.clip(h, 0, 1))) <= CLUSTER_KM).sum())
    order = np.argsort(-dens, kind="stable")
    c = 0
    for i in order:
        if cid[i] >= 0:
            continue
        h = (np.sin((lat - lat[i]) / 2) ** 2
             + np.cos(lat[i]) * np.cos(lat) * np.sin((lon - lon[i]) / 2) ** 2)
        near = (2 * 6371 * np.arcsin(np.sqrt(np.clip(h, 0, 1))) <= CLUSTER_KM) & (cid < 0)
        cid[near] = c; c += 1
    return cid


def max_concurrent(t0, t1, W):
    """Largest count of intervals fully covering some window of length W days."""
    t0 = t0.astype("datetime64[D]").astype(np.int64)
    t1 = t1.astype("datetime64[D]").astype(np.int64)
    best, best_start = 0, None
    # candidate window starts: every station start (the optimum starts at one of them)
    for s in np.unique(t0):
        e = s + W
        k = int(((t0 <= s) & (t1 >= e)).sum())
        if k > best:
            best, best_start = k, s
    return best, best_start

def main() -> None:
    """Run the census. Guarded, so importing cluster() and max_concurrent() from
    spatial_curve_ingest.py does not re-run and rewrite concurrent_density.csv."""
    d = pd.read_csv(CACHE).rename(columns={"first": "t_first", "last": "t_last"})
    d["t_first"] = pd.to_datetime(d.t_first, errors="coerce", utc=True).dt.tz_localize(None)
    d["t_last"] = pd.to_datetime(d.t_last, errors="coerce", utc=True).dt.tz_localize(None)
    ref = d[d.is_monitor & d.t_first.notna() & d.t_last.notna()].dropna(subset=["lat", "lon"]).copy()
    ref = ref.reset_index(drop=True)
    print(f"reference stations with dates: {len(ref):,}")
    ref["cluster"] = cluster(ref)

    rows = []
    for cl, g in ref.groupby("cluster"):
        if len(g) < 10:
            continue
        r = dict(cluster=int(cl), band=band(g.lat.mean()), country=g.country.mode().iloc[0],
                 lat=round(g.lat.mean(), 3), lon=round(g.lon.mean(), 3), ever=len(g))
        for W in (365, 730):
            k, s = max_concurrent(g.t_first.values, g.t_last.values, W)
            r[f"conc_{W}"] = k
            r[f"win_{W}"] = str(np.datetime64(int(s), "D")) if s is not None else ""
        rows.append(r)

    C = pd.DataFrame(rows).sort_values("conc_365", ascending=False)
    out = Path(__file__).with_name("concurrent_density.csv")
    C.to_csv(out, index=False)

    print(f"\nclusters with >=10 reference stations ever: {len(C)}")
    print("\nEVER-EXISTED vs CONCURRENT over one year:")
    for thr in (10, 15, 20, 30, 40, 60):
        e = C[C.ever >= thr]; c1 = C[C.conc_365 >= thr]; c2 = C[C.conc_730 >= thr]
        bd = dict(c1.band.value_counts())
        print(f"  >= {thr:3d}: ever {len(e):3d} | concurrent 1y {len(c1):3d} | concurrent 2y "
              f"{len(c2):3d} | 1y bands {bd}")
    print("\ntop 15 by concurrent one-year count:")
    print(C.head(15)[["cluster", "band", "country", "ever", "conc_365", "win_365",
                      "conc_730"]].to_string(index=False))
    print("\ndeep_tropical and tropical, by concurrent one-year count:")
    print(C[C.band.isin(["deep_tropical", "tropical"])].head(12)[
        ["cluster", "band", "country", "lat", "lon", "ever", "conc_365", "conc_730"]].to_string(index=False))


if __name__ == "__main__":
    main()
