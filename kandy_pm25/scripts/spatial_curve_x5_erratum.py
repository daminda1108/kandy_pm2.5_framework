"""spatial_curve_x5_erratum.py -- review step S-a (docs/review_remediation_plan_2026-10-06.md).

The registered X5 summary (spatial_curve_analysis.py:805-810) takes, per city, the median of cLHS - random
differences pooled over EVERY estimator. E0 (city mean) and E1 (built-up raster) do not depend on which
stations are fitted, so their differences are exactly 0 (and the `|e7sub` copies add more zeros); the
per-city median collapses to 0.00 and the interval to [0.00, 0.00]. The verdict was also one-sided.

This recomputes X5 from the stored q1.parquet per estimator that DOES depend on the fitted sites, with the
registered two-level country bootstrap, two-sided, at the registered k grid, and also per k. Both frames.
Output: data/processed/modular/{spatial_curve,spatial_curve_full}/analysis/x5_erratum.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from spatial_curve_analysis import cluster_boot   # noqa: E402  (registered bootstrap, unchanged)

MOD = REPO / "data" / "processed" / "modular"
SITE_DEPENDENT = ["E2", "E3", "E4", "E5", "E6"]


def run(frame: str) -> dict:
    d = MOD / frame
    q = pd.read_parquet(d / "analysis" / "q1.parquet")
    C = pd.read_csv(d / "frame_cities.csv").set_index("cluster")
    prim = C.index[C.primary.astype(bool)]
    ctry = C.country
    mde = json.load(open(d / "analysis" / "summary.json"))["detection_limit_at_countries"]
    q = q[(q.holdout == "random") & q.ordering.isin(["clhs", "random"])]
    w = q.pivot_table(index=["cluster", "rep", "k", "est"], columns="ordering", values="rho").dropna()
    w["diff"] = w.clhs - w.random
    w = w.reset_index()
    out = {"frame": frame, "detection_limit": mde,
           "zero_share_registered_pool": float((w["diff"] == 0).mean())}
    est_present = [e for e in SITE_DEPENDENT if e in set(w.est)]
    out["estimators"] = est_present
    for e in est_present + ["all_site_dependent"]:
        sub = w[w.est.isin(est_present)] if e == "all_site_dependent" else w[w.est == e]
        per_city = sub.groupby("cluster")["diff"].median()
        med, lo, hi, n = cluster_boot(per_city[per_city.index.isin(prim)], ctry)
        rec = dict(median=med, lo=lo, hi=hi, cities=n,
                   holds_two_sided=(bool(abs(med) < mde) if np.isfinite(med) else None),
                   interval_inside_band=(bool(lo > -mde and hi < mde) if np.isfinite(lo) else None))
        byk = {}
        for k, g in sub.groupby("k"):
            pc = g.groupby("cluster")["diff"].median()
            m2, l2, h2, n2 = cluster_boot(pc[pc.index.isin(prim)], ctry)
            byk[int(k)] = dict(median=m2, lo=l2, hi=h2, cities=n2)
        rec["by_k"] = byk
        out[e] = rec
    return out


def main():
    for frame in ("spatial_curve", "spatial_curve_full"):
        r = run(frame)
        p = MOD / frame / "analysis" / "x5_erratum.json"
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(r, indent=2), encoding="utf-8"); os.replace(tmp, p)
        print(f"{frame}: zero share in registered pool {r['zero_share_registered_pool']:.2f}; limit {r['detection_limit']}")
        for e in r["estimators"] + ["all_site_dependent"]:
            v = r[e]
            print(f"  {e:<20} {v['median']:+.3f} [{v['lo']:+.3f}, {v['hi']:+.3f}] n={v['cities']}  "
                  f"inside +-limit: {v['interval_inside_band']}")
        print(f"-> {p}")


if __name__ == "__main__":
    main()
