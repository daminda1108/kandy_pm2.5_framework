"""confirmation_panel.py -- select the ladder-v2 CONFIRMATION panel from METADATA ONLY.
(redesign plan §2 and §7 step 5; no PM2.5 value is read here, so the registration stays blind)

Rule, mirroring the discovery draw (draw_validation_sample.py) as far as the fresh supply allows:
  * OpenAQ clusters from confirmation_pool.csv (single-linkage 25 km, locations active >= 365 d in
    2024-09-01 .. 2026-08-31, more than 30 km from EVERY city ever drawn) with >= 10 locations;
  * CNEMC cities from panel_census.csv not in the discovery sample, with >= 10 stations;
  * caps as in discovery: OpenAQ at most 4 clusters per country, CNEMC at most 12 cities, chosen at
    random with a fixed seed; every deep-tropical and tropical candidate is taken (the fresh supply
    there is 4 in total, so no cap binds).
Cities that later fail the ingest QC (< 10 stations with data, < 120 scored days) are excluded by
the same rules as discovery and reported, never replaced.

Out: data/processed/modular/confirmation/confirmation_panel.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "data" / "processed" / "modular"
SEED = 20260926


def band(lat):
    a = abs(lat)
    return ("deep_tropical" if a < 15 else "tropical" if a < 23.5
            else "subtropical" if a < 35 else "temperate")


def main():
    rng = np.random.default_rng(SEED)
    oa = pd.read_csv(MOD / "verify_2026-09-25" / "confirmation_pool.csv")
    oa = oa[oa.n >= 10].copy()
    oa["src"] = "OpenAQ"
    oa["cid"] = [f"oaq_{c}_{i}" for i, c in enumerate(oa.country)]
    keep = []
    for ctry, g in oa.groupby("country"):
        g = g.sample(frac=1, random_state=int(rng.integers(1e9)))
        trop = g[g.band.isin(["deep_tropical", "tropical"])]
        rest = g[~g.band.isin(["deep_tropical", "tropical"])]
        keep.append(pd.concat([trop, rest]).head(max(4, len(trop))))
    oa = pd.concat(keep)

    cen = pd.read_csv(MOD / "panel_census.csv")
    smp = pd.read_csv(MOD / "validation_sample.csv")
    used = set(smp[smp.src == "CNEMC"].slug.astype(str))
    cn = cen[~cen.slug.astype(str).isin(used) & (cen.n_stations >= 10)].copy()
    cn = cn.sample(frac=1, random_state=int(rng.integers(1e9))).head(12)
    cn = pd.DataFrame({"cid": cn.slug.astype(str), "src": "CNEMC", "country": "CN",
                       "lat": cn.lat, "lon": cn.lon, "n": cn.n_stations, "n_ref": cn.n_stations})
    cn["band"] = cn.lat.map(band)

    P = pd.concat([oa[["cid", "src", "country", "lat", "lon", "n", "n_ref", "band"]], cn],
                  ignore_index=True)
    out = MOD / "confirmation"; out.mkdir(parents=True, exist_ok=True)
    P.to_csv(out / "confirmation_panel.csv", index=False)
    print(f"confirmation panel: {len(P)} cities, {P.country.nunique()} countries")
    print(P.groupby(["band", "src"]).size().to_string())
    print(f"reference-dominated (n_ref/n >= 0.5): {(P.n_ref / P.n >= 0.5).sum()} of {len(P)}")


if __name__ == "__main__":
    main()
