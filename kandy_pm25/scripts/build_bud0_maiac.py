"""C1 -- pull raw MAIAC AOD, the honest satellite stream.

Registered at https://osf.io/bkpyr/ (2026-09-01) as test C1/S3.

WHY. `SATELLITE_LEVEL` is currently GHAP, and GHAP is not a satellite observation. It is a fused
machine-learning product (Wei et al., Nat Commun 14:8349, 2023) trained on ~9,500 ground stations
INCLUDING OpenAQ and CNEMC -- the two networks that supply this study's entire panel -- and
predicted from a feature set that substantially overlaps the tier's other two streams: all seven
of our reanalysis drivers, plus NDVI, night lights, population and elevation from our static
geography, plus GEOS-CF, CAMS, humidity, pressure, precipitation and evaporation which we do not
even carry.

So `Bud0c` is not "drivers + geography + an independent satellite observation". It is drivers +
geography + a non-linear recombination of drivers and geography, plus AOD, plus extra drivers,
plus the panel's own monitors, precomputed by somebody else's Extra-Trees model. The 7.6%
attributed to "a satellite level" is a mixture, and the leakage is not escaped by using the
annual product -- averaging a contaminated quantity does not decontaminate it.

MAIAC (MCD19A2) `Optical_Depth_055` is an actual radiometric retrieval. It is not trained on
monitors, it does not contain our drivers, and it exists everywhere `Bud0` claims to operate.
That makes it the admissible stream for a genuinely sensorless tier.

⚠ AOD is a COLUMN quantity and PM2.5 is a surface one; they are related through boundary-layer
depth and hygroscopic growth, both of which the tier already carries as drivers. The learner is
free to use it or not. That is the point: we are measuring what an honest satellite stream is
worth, not asserting it is worth something.

QA. `AOD_QA` bit 8-11 is the retrieval quality; 0000 = best. Cloud-masked and low-quality
retrievals are dropped rather than gap-filled -- a missing day should read as missing, because
gap-filling with a model is how a satellite stream stops being a satellite stream.

Usage:  .venv/Scripts/python.exe scripts/build_bud0_maiac.py [--years 2019 2022]
Out:    data/processed/modular/bud0_maiac_aod.csv   (city, date, aod)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "bud0_maiac_aod.csv"
MAIAC = "MODIS/061/MCD19A2_GRANULES"
BUFFER_M = 5000          # same 5 km footprint the GHAP pull used, so the streams are comparable


def targets() -> pd.DataFrame:
    """The same 48-city target list build_bud0_streams.py uses -- OpenAQ clusters + CNEMC."""
    man = pd.read_csv(MOD / "openaq_manifest.csv")
    man = man[man.status == "OK"][["cluster", "lat", "lon"]]
    man["city"] = man.cluster.astype(str)
    smp = pd.read_csv(MOD / "validation_sample.csv")
    cn = smp[smp.src == "CNEMC"][["slug", "lat", "lon"]].rename(columns={"slug": "city"})
    cn["city"] = cn.city.astype(str)
    return (pd.concat([man[["city", "lat", "lon"]], cn], ignore_index=True)
            .drop_duplicates("city").reset_index(drop=True))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs=2, default=[2019, 2022])
    a = ap.parse_args()
    y0, y1 = a.years

    import ee
    ee.Initialize(project="kandypinn")

    tgt = targets()
    print(f"MAIAC AOD pull: {len(tgt)} cities, {y0}-{y1}, {BUFFER_M/1000:.0f} km footprint\n")

    def masked(img):
        # AOD_QA bits 8-11 = AOD QA level; 0 is best quality. Keep only that.
        qa = img.select("AOD_QA").rightShift(8).bitwiseAnd(15)
        return (img.select("Optical_Depth_055")
                .updateMask(qa.eq(0))
                .multiply(0.001)                       # MCD19A2 scale factor
                .copyProperties(img, ["system:time_start"]))

    # RESUME. The first run lost 131 of 228 city-years to computation timeouts and connection
    # drops while a second GEE job competed with it, leaving 26 of 57 cities. Re-pulling the
    # ~14k rows that already succeeded would just burn the same budget again, so completed
    # city-years are skipped and only the gaps are fetched.
    done = set()
    rows = []
    if OUT.exists():
        prev = pd.read_csv(OUT, parse_dates=["date"])
        prev["yr"] = prev.date.dt.year
        for (c, yr), g in prev.groupby(["city", "yr"]):
            done.add((str(c), int(yr)))
            rows.append(g[["city", "date", "aod"]])
        print(f"resuming: {len(done)} city-years already on disk, {len(prev):,} rows\n")

    failed = []
    for i, r in enumerate(tgt.itertuples(), 1):
        pt = ee.Geometry.Point([float(r.lon), float(r.lat)]).buffer(BUFFER_M)
        got = 0
        for yr in range(y0, y1 + 1):
            if (str(r.city), yr) in done:
                continue
            try:
                col = (ee.ImageCollection(MAIAC)
                       .filterDate(f"{yr}-01-01", f"{yr + 1}-01-01")
                       .filterBounds(pt)
                       .map(masked))

                # getRegion over a 5 km buffer at 1 km returns every pixel of every granule and
                # blows the element limit (gotcha #44). Reduce each granule to ONE buffer-mean
                # server-side, then pull a single flat array per city-year.
                def to_feat(img):
                    v = img.reduceRegion(ee.Reducer.mean(), pt, scale=1000, maxPixels=1e9) \
                           .get("Optical_Depth_055")
                    return ee.Feature(None, {"t": img.date().millis(), "aod": v})

                fc = ee.FeatureCollection(col.map(to_feat)).filter(ee.Filter.notNull(["aod"]))
                # Retry with backoff: the losses were transport drops and server-side
                # timeouts, not bad queries, so a single attempt throws away recoverable work.
                pairs = None
                for attempt in range(3):
                    try:
                        pairs = fc.reduceColumns(ee.Reducer.toList(2),
                                                 ["t", "aod"]).get("list").getInfo()
                        break
                    except Exception:
                        if attempt < 2:
                            time.sleep(15 * (attempt + 1))
                if not pairs:
                    failed.append((r.city, yr, "no data after retries"))
                    continue
                df = pd.DataFrame(pairs, columns=["t", "aod"]).dropna()
                if df.empty:
                    continue
                df["date"] = pd.to_datetime(df.t, unit="ms").dt.date
                daily = df.groupby("date").aod.mean().reset_index()
                daily["city"] = r.city
                rows.append(daily)
                got += len(daily)
            except Exception as e:
                failed.append((r.city, yr, str(e)[:60]))
        print(f"  [{i:>2}/{len(tgt)}] {r.city:<10} {got:>5} city-days", flush=True)
        # Incremental write. A four-hour pull that loses everything to one bad response is a
        # four-hour pull you run twice; partial output is also resumable.
        if rows:
            pd.concat(rows, ignore_index=True)[["city", "date", "aod"]].to_csv(OUT, index=False)

    if not rows:
        print("no data pulled"); sys.exit(1)
    out = pd.concat(rows, ignore_index=True)[["city", "date", "aod"]]
    out.to_csv(OUT, index=False)
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print(f"  {len(out):,} city-days, {out.city.nunique()} cities")
    cov = out.groupby("city").size()
    print(f"  coverage per city: median {cov.median():.0f}, min {cov.min()}, max {cov.max()}")
    print(f"  AOD: mean {out.aod.mean():.3f}, p10 {out.aod.quantile(.1):.3f}, "
          f"p90 {out.aod.quantile(.9):.3f}")
    if failed:
        print(f"  {len(failed)} city-year pulls failed; first: {failed[:3]}")


if __name__ == "__main__":
    main()
