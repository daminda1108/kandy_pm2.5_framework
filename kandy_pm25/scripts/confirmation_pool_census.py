"""confirmation_pool_census.py -- is there a FRESH panel of cities, never used, to confirm on?
(redesign planning, 2026-09-25)

Groups OpenAQ locations into city clusters (single-linkage within 25 km), keeps locations active
for at least 365 days inside the window 2024-09-01 .. 2026-08-31, excludes every cluster whose
centre lies within 30 km of ANY city in the discovery sample (validation_sample.csv, 57 cities incl.
failed draws), and counts what remains by absolute-latitude band and station count.

Out: data/processed/modular/verify_2026-09-25/confirmation_pool.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "data" / "processed" / "modular"
W0, W1 = pd.Timestamp("2024-09-01", tz="UTC"), pd.Timestamp("2026-08-31", tz="UTC")


def km(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = (np.sin((lat2 - lat1) * p / 2) ** 2
         + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * np.arcsin(np.sqrt(a))


def band(lat):
    a = abs(lat)
    return ("deep_tropical" if a < 15 else "tropical" if a < 23.5
            else "subtropical" if a < 35 else "temperate")


def main():
    g = pd.read_csv(REPO / "data/external/openaq/discovery/global_locations.csv", low_memory=False)
    for c in ("first", "last"):
        g[c] = pd.to_datetime(g[c], errors="coerce", utc=True)
    g = g.dropna(subset=["lat", "lon", "first", "last"])
    ov = (g["last"].clip(upper=W1) - g["first"].clip(lower=W0)).dt.days
    g = g[ov >= 365].copy()
    print(f"locations active >= 365 d in window: {len(g)}")

    rows = []
    for ctry, sub in g.groupby("country"):
        if len(sub) == 1:
            lab = np.array([1])
        else:
            xyz = np.c_[np.cos(np.radians(sub.lat)) * np.cos(np.radians(sub.lon)),
                        np.cos(np.radians(sub.lat)) * np.sin(np.radians(sub.lon)),
                        np.sin(np.radians(sub.lat))] * 6371.0
            lab = fcluster(linkage(xyz, "single"), t=25.0, criterion="distance")
        for k in np.unique(lab):
            s = sub[lab == k]
            rows.append(dict(country=ctry, lat=s.lat.median(), lon=s.lon.median(),
                             n=len(s), n_ref=int(s.is_monitor.astype(bool).sum())))
    C = pd.DataFrame(rows)
    smp = pd.read_csv(MOD / "validation_sample.csv")
    near = np.zeros(len(C), bool)
    for r in smp.itertuples():
        near |= km(C.lat.to_numpy(), C.lon.to_numpy(), r.lat, r.lon) < 30
    C["in_discovery"] = near
    C["band"] = C.lat.map(band)
    fresh = C[~C.in_discovery]
    out = MOD / "verify_2026-09-25" / "confirmation_pool.csv"
    fresh.sort_values("n", ascending=False).to_csv(out, index=False)

    print("\nFRESH clusters (not within 30 km of any discovery city), by band")
    for thr in (10, 6):
        t = fresh[fresh.n >= thr]
        tr = fresh[fresh.n_ref >= thr]
        print(f"  >= {thr} stations (any type): " + ", ".join(
            f"{b} {int((t.band == b).sum())}" for b in ("deep_tropical", "tropical", "subtropical", "temperate"))
            + f"   | >= {thr} REFERENCE: " + ", ".join(
            f"{b} {int((tr.band == b).sum())}" for b in ("deep_tropical", "tropical", "subtropical", "temperate")))
    dt = fresh[(fresh.band == "deep_tropical") & (fresh.n >= 6)].sort_values("n", ascending=False)
    print("\n  deep-tropical fresh clusters with >= 6 stations:")
    print(dt.head(25).to_string(index=False))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
