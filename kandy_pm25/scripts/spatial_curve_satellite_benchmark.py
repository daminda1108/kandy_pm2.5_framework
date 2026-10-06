"""spatial_curve_satellite_benchmark.py -- review step S-e (docs/review_remediation_plan_2026-10-06.md).
EXPLORATORY. Adds the benchmark a referee will ask for: a 1 km satellite PM2.5 product at the sites.

GHAP annual 1 km (Wei et al.; GEE `projects/sat-io/open-datasets/GHAP/GHAP_Y1K_PM25`, band b1 already in
ug/m3, gotcha #50), 2017-2022. Each city takes the GHAP year containing the middle of its frozen 365-day
window, or the nearest available year (2022 for later windows; within-city spatial ranks of an annual
product are assumed stable across a few years -- declared). Sampled at each site's coordinate.

Scoring mirrors E1 exactly: for every stored (city, replicate) held-out set
(`{frame}/analysis_splits_q1.parquet`), Spearman between GHAP and the site means on the held-out sites;
per city the median over replicates. Compared, paired within city, with E1 (built-up raster) and with
E3 (kriging) at k = 3, 5, 8, using the registered two-level country bootstrap.
Out: {frame}/analysis/satellite_benchmark.json, {frame}/ghap_sites.csv
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from spatial_curve_analysis import cluster_boot   # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
ASSET = "projects/sat-io/open-datasets/GHAP/GHAP_Y1K_PM25"
YEARS = range(2017, 2023)


def pull(frame: str) -> pd.DataFrame:
    out = MOD / frame / "ghap_sites.csv"
    if out.exists():
        return pd.read_csv(out)
    import ee
    ee.Initialize(project="kandypinn")
    S = pd.read_csv(MOD / frame / "frame_sites.csv")
    C = pd.read_csv(MOD / frame / "frame_cities.csv").set_index("cluster")
    mid = (pd.to_datetime(C.window_start) + (pd.to_datetime(C.window_end) - pd.to_datetime(C.window_start)) / 2).dt.year
    C["ghap_year"] = mid.clip(min(YEARS), max(YEARS))
    S["ghap_year"] = S.cluster.map(C.ghap_year)
    rows = []
    for yr, g in S.groupby("ghap_year"):
        img = ee.Image(f"{ASSET}/GHAP_PM25_Y1K_{int(yr)}_V1").select("b1")
        for i in range(0, len(g), 400):
            part = g.iloc[i:i + 400]
            fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([float(r.lon), float(r.lat)]), {"site": str(r.site)})
                                       for r in part.itertuples()])
            res = img.reduceRegions(collection=fc, reducer=ee.Reducer.first(), scale=1000).getInfo()
            rows += [{"site": f["properties"]["site"], "ghap": f["properties"].get("first"), "ghap_year": int(yr)}
                     for f in res["features"]]
        print(f"  GHAP {yr}: {len(g)} sites", flush=True)
    d = S[["cluster", "site", "lat", "lon", "static_mean"]].astype({"site": str}).merge(pd.DataFrame(rows), on="site")
    tmp = out.with_suffix(".tmp.csv"); d.to_csv(tmp, index=False); os.replace(tmp, out)
    return d


def score(frame: str) -> dict:
    G = pull(frame)
    gmap = dict(zip(G.site.astype(str), G.ghap)); ymap = dict(zip(G.site.astype(str), G.static_mean))
    sp = pd.read_parquet(MOD / frame / "analysis_splits_q1.parquet")
    sp = sp.drop_duplicates(["cluster", "rep"])                    # held set does not depend on k
    rows = []
    for r in sp.itertuples():
        held = [h for h in str(r.held).split("|") if h in gmap and gmap[h] is not None and np.isfinite(gmap[h])]
        if len(held) < 5:
            continue
        x = np.array([gmap[h] for h in held]); y = np.array([ymap[h] for h in held])
        rho = spearmanr(x, y).statistic if np.ptp(x) > 0 else 0.0
        rows.append(dict(cluster=r.cluster, rep=r.rep, rho_ghap=float(rho)))
    R = pd.DataFrame(rows)
    q = pd.read_parquet(MOD / frame / "analysis" / "q1.parquet")
    q = q[(q.holdout == "random") & (q.ordering == "random")]
    C = pd.read_csv(MOD / frame / "frame_cities.csv").set_index("cluster")
    prim = C.index[C.primary.astype(bool)]
    ctry = C.country
    per = R.groupby("cluster").rho_ghap.median().rename("GHAP").to_frame()
    e1 = q[q.est == "E1"].groupby(["cluster", "rep"]).rho.median().rename("E1").reset_index()
    J = R.merge(e1, on=["cluster", "rep"])
    per["GHAP_minus_E1"] = (J.rho_ghap - J.E1).groupby(J.cluster).median()
    for k in (3, 5, 8):
        e3 = q[(q.est == "E3") & (q.k == k)][["cluster", "rep", "rho"]]
        J3 = R.merge(e3, on=["cluster", "rep"])
        per[f"E3k{k}_minus_GHAP"] = (J3.rho - J3.rho_ghap).groupby(J3.cluster).median()
    per["E1"] = J.groupby("cluster").E1.median()
    out = {"frame": frame, "cities": int(per.index.isin(prim).sum()),
           "ghap_years": G.ghap_year.value_counts().to_dict(), "missing_sites": int(G.ghap.isna().sum())}
    for col in per.columns:
        m, lo, hi, n = cluster_boot(per.loc[per.index.isin(prim), col], ctry)
        out[col] = dict(median=m, lo=lo, hi=hi, cities=n)
    per.to_csv(MOD / frame / "analysis" / "satellite_benchmark_city.csv")
    return out


def main():
    for frame in ("spatial_curve", "spatial_curve_full"):
        r = score(frame)
        p = MOD / frame / "analysis" / "satellite_benchmark.json"
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(r, indent=2, default=str), encoding="utf-8"); os.replace(tmp, p)
        print(f"== {frame}  cities {r['cities']}  years {r['ghap_years']}  missing {r['missing_sites']}")
        for c in ("GHAP", "E1", "GHAP_minus_E1", "E3k3_minus_GHAP", "E3k5_minus_GHAP", "E3k8_minus_GHAP"):
            v = r[c]
            print(f"  {c:<18} {v['median']:+.3f} [{v['lo']:+.3f}, {v['hi']:+.3f}] n={v['cities']}")


if __name__ == "__main__":
    main()
