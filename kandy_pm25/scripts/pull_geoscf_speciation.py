"""Pull speciated PM2.5 for Kandy from GEOS-CF -- the chemistry the model has never had.

WHY THIS MATTERS MORE THAN IT LOOKS. The production model is an additive decomposition:

    PM = B(t)  +  local increment

where `B` is asserted to be the REGIONAL / TRANSBOUNDARY background and the increment is
asserted to be LOCAL. That assertion is the load-bearing physical claim of the whole
formulation, and it has only ever been supported statistically -- by a rural-satellite floor, a
coherence cap and a source-apportionment prior. It has never been checked against composition.

Chemistry can check it, because aged transported aerosol and fresh local combustion have
different fingerprints:

  SECONDARY  sulphate, nitrate, ammonium, secondary organic aerosol -- formed in the atmosphere
             over hours to days, so they are the signature of an AGED, TRANSPORTED air mass.
  PRIMARY    black carbon and primary organic carbon -- emitted directly, short-lived near
             source, so they are the signature of LOCAL, FRESH combustion.

If the decomposition is physically right, `B` should be secondary-dominated and the increment
primary-dominated. If it is wrong, they will look alike. Either answer is worth having, and
neither has ever been available.

⚠ GEOS-CF is a MODEL, not an observation. It cannot validate the decomposition; it can
corroborate or contradict it, and a contradiction would be the more informative outcome. The
bands are `RH35` -- dry reference at 35% relative humidity -- so these are composition SHARES,
not ambient masses, and must not be compared to a wet observation as levels.

Species (GEOS-CF v1 replay, tavg1hr, ug/m3 at RH35):
    PM25su  sulphate    PM25ni  nitrate      PM25oc  organic carbon
    PM25bc  black carbon PM25soa secondary organic  PM25du  dust   PM25ss  sea salt

Usage:  .venv/Scripts/python.exe scripts/pull_geoscf_speciation.py [--years 2019 2023]
Out:    data/processed/decomp/kandy_geoscf_speciation_daily.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from config import KANDY_PINN_BBOX as BB   # noqa: E402

OUT = REPO / "data" / "processed" / "decomp" / "kandy_geoscf_speciation_daily.csv"
COLL = "NASA/GEOS-CF/v1/rpl/tavg1hr"
SPECIES = {
    "PM25su_RH35_GCC": "sulphate",
    "PM25ni_RH35_GCC": "nitrate",
    "PM25oc_RH35_GCC": "organic_carbon",
    "PM25bc_RH35_GCC": "black_carbon",
    "PM25soa_RH35_GCC": "secondary_organic",
    "PM25du_RH35_GCC": "dust",
    "PM25ss_RH35_GCC": "sea_salt",
    "PM25_RH35_GCC": "total",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs=2, default=[2019, 2023])
    a = ap.parse_args()
    y0, y1 = a.years

    import ee
    ee.Initialize(project="kandypinn")

    lat = (BB["lat_min"] + BB["lat_max"]) / 2
    lon = (BB["lon_min"] + BB["lon_max"]) / 2
    pt = ee.Geometry.Point([lon, lat]).buffer(10000)
    bands = list(SPECIES)
    print(f"GEOS-CF speciation for Kandy ({lat:.4f}, {lon:.4f}), {y0}-{y1}")
    print(f"  {len(bands)} bands, daily means from hourly\n")

    frames = []
    for yr in range(y0, y1 + 1):
        for q in range(4):
            m0, m1 = q * 3 + 1, q * 3 + 4
            start = f"{yr}-{m0:02d}-01"
            end = f"{yr + 1}-01-01" if m1 > 12 else f"{yr}-{m1:02d}-01"
            try:
                col = (ee.ImageCollection(COLL).filterDate(start, end).select(bands))

                def to_feat(img):
                    v = img.reduceRegion(ee.Reducer.mean(), pt, scale=27750, maxPixels=1e9)
                    return ee.Feature(None, v.set("t", img.date().millis()))

                fc = ee.FeatureCollection(col.map(to_feat))
                cols = ["t"] + bands
                arr = fc.reduceColumns(ee.Reducer.toList(len(cols)), cols).get("list").getInfo()
                if not arr:
                    print(f"  {start} .. {end}   empty"); continue
                df = pd.DataFrame(arr, columns=cols).dropna()
                df["date"] = pd.to_datetime(df.t, unit="ms").dt.date
                daily = df.groupby("date")[bands].mean().reset_index()
                frames.append(daily)
                print(f"  {start} .. {end}   {len(daily):>4} days", flush=True)
            except Exception as e:
                print(f"  {start} .. {end}   FAILED {str(e)[:70]}")

    if not frames:
        print("nothing pulled"); sys.exit(1)
    d = pd.concat(frames, ignore_index=True).rename(columns=SPECIES)
    d = d.drop_duplicates("date").sort_values("date").reset_index(drop=True)
    d.to_csv(OUT, index=False)

    sp = [v for v in SPECIES.values() if v != "total"]
    share = d[sp].mean() / d[sp].mean().sum() * 100
    secondary = ["sulphate", "nitrate", "secondary_organic"]
    primary = ["black_carbon", "organic_carbon"]
    print(f"\nwrote {OUT.relative_to(REPO)}   ({len(d)} days)")
    print(f"\n=== mean composition, GEOS-CF at Kandy ({y0}-{y1}) ===")
    for k, v in share.sort_values(ascending=False).items():
        print(f"  {k:<20} {v:5.1f}%   {d[k].mean():7.3f} ug/m3")
    print(f"\n  secondary (SO4+NO3+SOA) {share[secondary].sum():5.1f}%")
    print(f"  primary carbonaceous    {share[primary].sum():5.1f}%")
    print(f"  natural (dust+sea salt) {share[['dust','sea_salt']].sum():5.1f}%")
    oc_bc = d.organic_carbon.mean() / max(d.black_carbon.mean(), 1e-9)
    print(f"\n  OC/BC ratio             {oc_bc:5.1f}")
    print("    traffic-dominated aerosol runs ~1-2; biomass burning runs high.")
    print("\n[!] GEOS-CF is a model at ~25 km. Shares, not ambient masses (RH35 dry reference).")


if __name__ == "__main__":
    main()
