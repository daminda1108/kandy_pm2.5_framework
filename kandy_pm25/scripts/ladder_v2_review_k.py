"""ladder_v2_review_k.py -- review follow-up (docs/review_remediation_plan_2026-10-06.md). EXPLORATORY.

The station-count curve of F.116 (`ladder_v2_secondary.py`, gain_k1..k8) uses the first k stations only to fit an
intercept and slope to Bud0 -- the calibration construction that F.124 showed drives the registered ordering. This
computes, on the same cities and splits, the curve a city actually faces when its k stations report every day,
beside the calibration curve on the same fitting target:

  pool (registered shuffle) = [s1 .. sN];  k stations = pool[:k];  fitting target = pool[-2:] (last two, disjoint
  for k <= N-2);  requires N >= 10 so k runs 1..8 on every city.
  cal_k   : target ~ a + b*Bud0                    (calibration only, as the registered rungs)
  day_k   : target ~ a + b*Bud0 + c*mean_k(t)      (same-day mean of the k stations; affine fallback on missing days)
Each is shrunk toward Bud0 with a weight cross-fitted from the other cities and scored on the held-out stations.
Bud0 is read from the review cache (`review_bud0_{frame}_loco_b5.parquet`), so this needs ladder_v2_review.py first.

Usage: python scripts/ladder_v2_review_k.py [--frame full|registered] [--splits 21] [--boot 4000]
Out:   data/processed/modular/ladder_v2/review_k_{frame}_{percity.csv,summary.json}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
warnings.filterwarnings("ignore")

import ladder_v2 as L                                        # noqa: E402
from ladder_frames import SEED                               # noqa: E402
from modular_validation_all import _affine                   # noqa: E402
from src.modular import shrinkage as sh                      # noqa: E402

KMAX = 8
ARMS = [f"{m}{k}" for m in ("cal", "day") for k in range(1, KMAX + 1)]


def preds(city, st, b0, seed):
    rng = np.random.default_rng(seed)
    ids = np.array(sorted(st.station_id.unique())); rng.shuffle(ids)
    n_hold = max(3, len(ids) // 3)
    held, pool = ids[:n_hold], ids[n_hold:]
    if len(pool) < KMAX + 2:
        return None
    daily = lambda k: st[st.station_id.isin(k)].groupby("date").pm25.mean()
    p0 = b0[b0.city == city].set_index("date").bud0
    fr = pd.concat([p0, daily(held).rename("obs")], axis=1).dropna().sort_index()
    if len(fr) < 120:
        return None
    y = daily(pool[-2:]).rename("y")
    j0 = pd.concat([p0, y], axis=1).dropna()
    a0, a1 = _affine(j0.y.to_numpy(), j0.bud0.to_numpy())
    aff = a0 + a1 * fr.bud0.to_numpy()
    P = {"Bud0": fr.bud0.to_numpy()}
    for k in range(1, KMAX + 1):
        x = daily(pool[:k]).rename("x")
        j = pd.concat([p0, x, y], axis=1).dropna()
        a, b = _affine(j.y.to_numpy(), j.bud0.to_numpy()) if len(j) >= 30 else (a0, a1)
        P[f"cal{k}"] = a + b * fr.bud0.to_numpy()
        if len(j) > 60:
            A = np.vstack([np.ones(len(j)), j.bud0.to_numpy(), j.x.to_numpy()]).T
            c, *_ = np.linalg.lstsq(A, j.y.to_numpy(), rcond=None)
            xs = x.reindex(fr.index).to_numpy()
            P[f"day{k}"] = np.where(np.isfinite(xs), c[0] + c[1] * fr.bud0.to_numpy() + c[2] * np.nan_to_num(xs), aff)
    return fr, P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", choices=["full", "registered"], default="full")
    ap.add_argument("--splits", type=int, default=21)
    ap.add_argument("--boot", type=int, default=4000)
    a = ap.parse_args()
    if a.frame == "full":
        import ladder_v2_fullnet as lf
        lf._point(REPO / "data" / "processed" / "modular" / "fullnet" / "mirror_full")
    import ladder_v2_confirm as lvc
    frame, meta, conf, _ = lvc.union("maiac")
    st = frame[0]
    cache = L.OUTD / f"review_bud0_{a.frame}_loco_b5.parquet"
    if not cache.exists():
        raise SystemExit(f"{cache} missing: run ladder_v2_review.py --frame {a.frame} first")
    b0 = pd.read_parquet(cache); b0["date"] = pd.to_datetime(b0.date)
    seeds = [SEED] + [SEED + 1000 * (k + 1) for k in range(a.splits - 1)]
    cache_p, own = {}, []
    for c in st:
        if c not in set(b0.city):
            continue
        for sd in seeds:
            r = preds(c, st[c], b0, sd)
            if r is None:
                continue
            fr, P = r
            cache_p[(c, sd)] = r
            obs, days = fr.obs.to_numpy(), fr.index.astype(str).to_numpy()
            own.append({"city": c, **{k: sh.optimal_weight(P["Bud0"], P[k], obs, groups=days, seed=sd).w
                                       for k in ARMS if k in P}})
    W = pd.DataFrame(own).set_index("city")
    rows = []
    for (c, sd), (fr, P) in cache_p.items():
        wg = W.drop(index=c, errors="ignore").median()
        obs = fr.obs.to_numpy()
        r0 = L.losses(P["Bud0"], obs)
        row = {"city": c, "seed": sd}
        for k in ARMS:
            if k in P and np.isfinite(wg.get(k, np.nan)):
                x = sh.combine(P["Bud0"], P[k], float(wg[k]))
                for Ls, v in L.losses(x, obs).items():
                    row[f"{k}_{Ls}"] = 100 * (r0[Ls] - v) / r0[Ls] if r0[Ls] else np.nan
        rows.append(row)
    S = pd.DataFrame(rows).replace([np.inf, -np.inf], np.nan)
    cols = [c for c in S.columns if c not in ("city", "seed")]
    C = S.groupby("city")[cols].median().join(meta[["band", "cluster"]])
    for k in range(2, KMAX + 1):
        C[f"dayextra{k}_rmse"] = C[f"day{k}_rmse"] - C["day1_rmse"]
    C.to_csv(L.OUTD / f"review_k_{a.frame}_percity.csv")
    rng = np.random.default_rng(SEED)
    res = {"config": vars(a), "cities": int(len(C))}
    keep = [f"{m}{k}_{Ls}" for m in ("cal", "day") for k in range(1, KMAX + 1) for Ls in ("rmse", "exceed")] + \
           [f"dayextra{k}_rmse" for k in range(2, KMAX + 1)]
    for col in keep:
        s = C[[col, "cluster"]].dropna()
        if len(s) < 4:
            continue
        v, g = s[col].to_numpy(), s.cluster.astype(str).to_numpy()
        bk = L.boot_cluster(v, g, rng, a.boot)
        res[col] = dict(n=int(len(v)), median=float(np.median(v)),
                        cluster=[float(np.percentile(bk, 2.5)), float(np.percentile(bk, 97.5))])
    p = L.OUTD / f"review_k_{a.frame}_summary.json"
    tmp = p.with_suffix(".json.tmp"); tmp.write_text(json.dumps(res, indent=2), encoding="utf-8"); os.replace(tmp, p)
    print(f"cities {len(C)}")
    for k in range(1, KMAX + 1):
        c_, d_ = res.get(f"cal{k}_rmse"), res.get(f"day{k}_rmse")
        e_ = res.get(f"dayextra{k}_rmse")
        print(f"  k={k}  calibration {c_['median']:+6.1f} [{c_['cluster'][0]:+.1f}, {c_['cluster'][1]:+.1f}]   "
              f"same-day {d_['median']:+6.1f} [{d_['cluster'][0]:+.1f}, {d_['cluster'][1]:+.1f}]"
              + (f"   extra over k=1 {e_['median']:+.2f} [{e_['cluster'][0]:+.2f}, {e_['cluster'][1]:+.2f}]" if e_ else ""))
    print(f"-> {p}")


if __name__ == "__main__":
    main()
