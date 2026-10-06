"""confirmation_members.py -- the member OpenAQ location ids of each frozen confirmation cluster.

The frozen panel (confirmation_panel.csv, SHA-256 80c4ae34...) stores each OpenAQ cluster's median
lat/lon and counts, not its members. This re-runs the IDENTICAL clustering of
confirmation_pool_census.py (same census file, same activity filter, same single-linkage 25 km per
country) and matches every cluster to the frozen panel on (country, median lat, median lon, n).
It REFUSES unless all 64 OpenAQ panel clusters match exactly one regenerated cluster. Metadata only:
no PM2.5 is read.

Out: data/processed/modular/confirmation/confirmation_members.csv (cid, location_id, lat, lon, is_monitor)
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "data" / "processed" / "modular"
PANEL_SHA = "80c4ae34aeb65907149f5c1483020b395a184602a1819a1f619fc08dafe8eecc"
W0, W1 = pd.Timestamp("2024-09-01", tz="UTC"), pd.Timestamp("2026-08-31", tz="UTC")


def main() -> int:
    pf = MOD / "confirmation" / "confirmation_panel.csv"
    sha = hashlib.sha256(pf.read_bytes()).hexdigest()
    assert sha == PANEL_SHA, f"frozen panel changed: {sha}"
    P = pd.read_csv(pf)
    P = P[P.src == "OpenAQ"].copy()

    g = pd.read_csv(REPO / "data/external/openaq/discovery/global_locations.csv", low_memory=False)
    for c in ("first", "last"):
        g[c] = pd.to_datetime(g[c], errors="coerce", utc=True)
    g = g.dropna(subset=["lat", "lon", "first", "last"])
    ov = (g["last"].clip(upper=W1) - g["first"].clip(lower=W0)).dt.days
    g = g[ov >= 365].copy()

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
            rows.append(dict(country=ctry, lat=s.lat.median(), lon=s.lon.median(), n=len(s),
                             ids=s.id.tolist(), lats=s.lat.tolist(), lons=s.lon.tolist(),
                             mon=s.is_monitor.astype(bool).tolist()))
    C = pd.DataFrame(rows)

    out, unmatched = [], []
    for r in P.itertuples():
        m = C[(C.country == r.country) & (C.n == r.n)
              & np.isclose(C.lat, r.lat, atol=1e-9) & np.isclose(C.lon, r.lon, atol=1e-9)]
        if len(m) != 1:
            unmatched.append((r.cid, len(m)))
            continue
        m = m.iloc[0]
        for i, la, lo, mo in zip(m.ids, m.lats, m.lons, m.mon):
            out.append(dict(cid=r.cid, location_id=int(i), lat=la, lon=lo, is_monitor=bool(mo)))
    if unmatched:
        raise SystemExit(f"{len(unmatched)} panel clusters did not match exactly one cluster: "
                         f"{unmatched[:10]}")
    D = pd.DataFrame(out)
    f = MOD / "confirmation" / "confirmation_members.csv"
    tmp = f.with_suffix(".csv.tmp"); D.to_csv(tmp, index=False); os.replace(tmp, f)
    print(f"{P.cid.nunique()} OpenAQ clusters matched; {len(D)} member locations -> {f.name}")
    print(f"SHA-256 {hashlib.sha256(f.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
