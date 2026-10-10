"""spatial_curve_terrain.py -- terrain descriptors per frame city, for EXPLORATORY analysis X-T.

Declared 2026-09-11, before any learning-curve result existed (plan §13). NOT part of the OSF
registration rqn4y or its amendment 26hp8, and never reported as confirmatory.

WHY. Every city in the frame is a dense urban network, and none is a valley city of Kandy's type.
If basin terrain changes how PM2.5 is structured in space (cold pools, drainage flows, trapping),
the density-to-skill relation measured here may not carry to Kandy. This asks whether the curve's
summary quantities vary with terrain INSIDE the frame. With about 18 primary cities it can find
only a large moderation, and a null is not evidence of none.

DESCRIPTORS (SRTM GL1, fixed here before any outcome was seen):
  T1 relief_m      p95 - p5 of elevation over the sites' bounding box padded 5 km (90 m scale)
  T2 site_range_m  p95 - p5 of elevation at the sites themselves (30 m scale)
  T3 slope_deg     mean slope over the same padded box (90 m scale)
  T4 enclosure     of 8 compass rays from the median site, how many rise >= 200 m above the
                   median site elevation within 15 km (0 = open plain, 8 = closed basin)

Usage: .venv/Scripts/python.exe scripts/spatial_curve_terrain.py
Out:   data/processed/modular/spatial_curve/frame_terrain.csv
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import spatial_curve_predictors as P                                        # noqa: E402

SC = REPO / "data" / "processed" / "modular" / "spatial_curve"
PAD_KM = 5.0
RAY_KM = 15.0
RAY_STEP_KM = 0.5
RISE_M = 200.0
DIRS = 8


def main() -> int:
    import ee
    ee.Initialize(project="kandypinn")
    dem = ee.Image("USGS/SRTMGL1_003").select("elevation")
    both = dem.addBands(ee.Terrain.slope(dem).rename("slope"))
    red = ee.Reducer.percentile([5, 95]).combine(ee.Reducer.mean(), sharedInputs=True)

    U = P.frame_union()
    out_f = SC / "frame_terrain.csv"
    done = set(pd.read_csv(out_f).cluster) if out_f.exists() else set()
    rows = pd.read_csv(out_f).to_dict("records") if out_f.exists() else []
    for cl, g in U.groupby("cluster"):
        if cl in done:
            continue
        t = time.time()
        lat0, lon0 = float(g.lat.median()), float(g.lon.median())
        kx = 111.32 * np.cos(np.radians(lat0))
        dla, dlo = PAD_KM / 110.57, PAD_KM / kx
        box = ee.Geometry.Rectangle([g.lon.min() - dlo, g.lat.min() - dla,
                                     g.lon.max() + dlo, g.lat.max() + dla])
        st = both.reduceRegion(reducer=red, geometry=box, scale=90, maxPixels=1e10,
                               bestEffort=True).getInfo()

        feats = [ee.Feature(ee.Geometry.Point([r.lon, r.lat]), {"kind": "site", "i": i, "d": -1, "r": 0.0})
                 for i, r in enumerate(g.itertuples())]
        steps = np.arange(RAY_STEP_KM, RAY_KM + 1e-9, RAY_STEP_KM)
        for d in range(DIRS):
            th = 2 * np.pi * d / DIRS
            for j, rk in enumerate(steps):
                feats.append(ee.Feature(ee.Geometry.Point([lon0 + rk * np.sin(th) / kx,
                                                            lat0 + rk * np.cos(th) / 110.57]),
                                        {"kind": "ray", "i": j, "d": d, "r": float(rk)}))
        got = dem.reduceRegions(collection=ee.FeatureCollection(feats), reducer=ee.Reducer.first(),
                                scale=30).getInfo()["features"]
        pr = pd.DataFrame([f["properties"] for f in got])
        site_z = pr[pr.kind == "site"]["first"].astype(float).dropna()
        z0 = float(site_z.median())
        ray = pr[pr.kind == "ray"].dropna(subset=["first"])
        rise = ray.groupby("d")["first"].max() - z0
        rows.append(dict(
            cluster=int(cl), sites=len(g), lat=round(lat0, 4), lon=round(lon0, 4),
            relief_m=float(st["elevation_p95"] - st["elevation_p5"]),
            site_range_m=float(site_z.quantile(.95) - site_z.quantile(.05)),
            slope_deg=float(st["slope_mean"]),
            enclosure=int((rise >= RISE_M).sum()),
            site_elev_median_m=z0, sites_with_elev=int(len(site_z))))
        tmp = out_f.with_suffix(".tmp")
        pd.DataFrame(rows).to_csv(tmp, index=False)
        tmp.replace(out_f)
        r = rows[-1]
        print(f"  cluster {cl}: relief {r['relief_m']:.0f} m, site range {r['site_range_m']:.0f} m, "
              f"slope {r['slope_deg']:.1f} deg, enclosure {r['enclosure']}/8  ({time.time() - t:.0f} s)",
              flush=True)
    print(f"wrote {out_f.name}: {len(rows)} cities")
    return 0


if __name__ == "__main__":
    sys.exit(main())
