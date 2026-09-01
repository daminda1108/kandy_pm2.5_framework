"""Speciated PM2.5 for the whole validation panel -- so composition can meet the budget ladder.

WHY THE PANEL AND NOT JUST KANDY. Kandy's composition alone is an anecdote. Across the panel it
becomes a variable, and it lets the programme ask a question it has never been able to ask:

    does the VALUE OF INFORMATION depend on what the aerosol is made of?

The ladder says the first two monitors buy 17.9% and a regional background rung buys 40.6%.
Those numbers are currently reported as though a city is a city. But a **secondary-dominated**
city -- one whose PM2.5 is mostly sulphate, nitrate and secondary organics formed over hours to
days -- is chemically a REGIONAL problem, so a regional background station should be worth more
there and a local monitor less. A **primary-dominated** city, whose PM is fresh local
combustion, should be the reverse.

If that holds, composition predicts which cities need which instrument, and the ladder stops
being a single global recommendation and becomes a targeted one. If it does not hold, the
ladder's generality is *strengthened*, because it would mean the value of a monitor is
insensitive to the chemistry.

Either way it is a question no value-of-information study in this area has asked, and the data
costs an annual-mean pull.

⚠ Annual means, not daily. A composition SHARE is a slow-varying quantity and the ladder is
scored on city-days pooled over years, so a per-city annual share is the matched resolution.
This is a deliberate choice, not a shortcut: daily speciation for 57 cities buys nothing the
share does not already carry, and gotcha #82's lesson is that a stream should be used at the
strength its question needs -- no weaker, and no stronger for show.

⚠ GEOS-CF is a MODEL at ~25 km. For a large city that is roughly the urban footprint; for a
small one it is the surrounding region. Composition is regional in character so this is
tolerable, but it is a real limit and the per-city values must never be presented as measured.

Usage:  .venv/Scripts/python.exe scripts/pull_panel_speciation.py [--years 2019 2022]
Out:    data/processed/modular/panel_speciation.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from build_bud0_maiac import targets   # noqa: E402  -- same 57-city target list

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "panel_speciation.csv"
COLL = "NASA/GEOS-CF/v1/rpl/tavg1hr"
SPECIES = {
    "PM25su_RH35_GCC": "sulphate",
    "PM25ni_RH35_GCC": "nitrate",
    "PM25oc_RH35_GCC": "organic_carbon",
    "PM25bc_RH35_GCC": "black_carbon",
    "PM25soa_RH35_GCC": "secondary_organic",
    "PM25du_RH35_GCC": "dust",
    "PM25ss_RH35_GCC": "sea_salt",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs=2, default=[2019, 2022])
    a = ap.parse_args()
    y0, y1 = a.years

    import ee
    ee.Initialize(project="kandypinn")

    tgt = targets()
    bands = list(SPECIES)
    # One multi-year mean image, sampled once per city: the cheapest form of the question.
    # Sample four synoptic hours (00/06/12/18 UTC) rather than all 24. Meaning four years of
    # HOURLY GEOS-CF is ~35,000 images and does not finish; this is 6x cheaper and a composition
    # SHARE is slow-varying. Four hours rather than one because nitrate partitions to the
    # particle phase in the cool hours, so a single-hour sample would bias the share.
    mean_img = (ee.ImageCollection(COLL)
                .filterDate(f"{y0}-01-01", f"{y1 + 1}-01-01")
                .filter(ee.Filter.Or(*[ee.Filter.calendarRange(h, h, "hour")
                                       for h in (0, 6, 12, 18)]))
                .select(bands).mean())
    print(f"panel speciation: {len(tgt)} cities, {y0}-{y1} mean, {len(bands)} species\n")

    # One reduceRegions over ALL points. Sampling city-by-city made the server recompute the
    # multi-year mean for every request -- two cities in ten minutes. This is one composite.
    feats = [ee.Feature(ee.Geometry.Point([float(r.lon), float(r.lat)]).buffer(10000),
                        {"city": str(r.city)}) for r in tgt.itertuples()]
    fc = ee.FeatureCollection(feats)
    res = mean_img.reduceRegions(collection=fc, reducer=ee.Reducer.mean(),
                                 scale=27750).getInfo()
    rows = []
    for ft in res["features"]:
        p_ = ft["properties"]
        row = {"city": p_.get("city")}
        row.update({SPECIES[b_]: p_.get(b_) for b_ in bands})
        rows.append(row)
    rows = pd.DataFrame(rows).merge(
        tgt.assign(city=tgt.city.astype(str))[["city", "lat", "lon"]], on="city", how="left"
    ).to_dict("records")
    print(f"  reduced {len(rows)} cities in one call")

    d = pd.DataFrame(rows)
    sp = list(SPECIES.values())
    d = d.dropna(subset=sp, how="all")
    d["total"] = d[sp].sum(axis=1)
    d["secondary"] = d[["sulphate", "nitrate", "secondary_organic"]].sum(axis=1)
    d["primary_carb"] = d[["black_carbon", "organic_carbon"]].sum(axis=1)
    d["sec_frac"] = d.secondary / (d.secondary + d.primary_carb)
    d["oc_bc"] = d.organic_carbon / d.black_carbon.replace(0, np.nan)
    d.to_csv(OUT, index=False)

    print(f"\nwrote {OUT.relative_to(REPO)}   ({len(d)} cities)")
    print(f"\nsecondary fraction across the panel:")
    print(f"  median {d.sec_frac.median():.3f}  p10 {d.sec_frac.quantile(.1):.3f}  "
          f"p90 {d.sec_frac.quantile(.9):.3f}  range {d.sec_frac.min():.3f}-{d.sec_frac.max():.3f}")
    print(f"  OC/BC  median {d.oc_bc.median():.1f}  range {d.oc_bc.min():.1f}-{d.oc_bc.max():.1f}")
    lo = d.nsmallest(3, "sec_frac")[["city", "sec_frac", "oc_bc"]]
    hi = d.nlargest(3, "sec_frac")[["city", "sec_frac", "oc_bc"]]
    print("\n  most PRIMARY-dominated:"); print(lo.to_string(index=False))
    print("\n  most SECONDARY-dominated:"); print(hi.to_string(index=False))
    print("\n[!] GEOS-CF is a model at ~25 km. Shares, never measured per-city masses.")


if __name__ == "__main__":
    main()
