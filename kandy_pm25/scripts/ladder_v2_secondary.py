"""ladder_v2_secondary.py -- the order test and the station-count sweep, re-run on ladder v2.
(user, 2026-09-27: "re-run order and station count on v2")

Everything is the frozen v2 machinery from ladder_v2.py (load: 18 h rule, grid geography, drivers v2;
bagged_bud0: 5 learner seeds; 21 station splits; weights cross-fitted from the OTHER cities; per-city
effect = median over splits; two-level cluster bootstrap). Only the rungs chained differ:

  ORDER    A (production)  Bud0c -> s2 -> s6 -> s6bg      B (bg early)  Bud0c -> s2 -> s2bg -> s6bg
           where s2 = stations 1-2, s6 = stations 1-6, "bg" = the same-network background regressor.
  COUNT    k = 1..8 stations, each shrunk toward the SENSORLESS rung (as in v1's sweep), gain vs Bud0c.

Out: data/processed/modular/ladder_v2/secondary_{order,count}_{tag}.csv / .json
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

from ladder_frames import SEED                                          # noqa: E402
from ladder_v2 import OUTD, bagged_bud0, boot_city, boot_cluster, load  # noqa: E402
from modular_validation_all import _affine                               # noqa: E402
from src.modular import shrinkage as sh                                  # noqa: E402
from src.modular.city_meta import city_meta                              # noqa: E402

ORDER_A = ["s2", "s6", "s6bg"]
ORDER_B = ["s2", "s2bg", "s6bg"]
KMAX = 8


def split(st, seed):
    rng = np.random.default_rng(seed)
    ids = np.array(sorted(st.station_id.unique()))
    rng.shuffle(ids)
    n_hold = max(3, len(ids) // 3)
    return ids[:n_hold], ids[n_hold:]


def raw_preds(city, st, b0, seed):
    """Raw predictions of every rung spec used here, on one split. None if not scoreable."""
    held, pool = split(st, seed)
    daily = lambda k: st[st.station_id.isin(k)].groupby("date").pm25.mean()
    p0 = b0[b0.city == city].set_index("date").bud0
    fr = pd.concat([p0, daily(held).rename("obs")], axis=1).dropna().sort_index()
    if len(fr) < 120:
        return None
    x0 = fr.bud0.to_numpy()
    P = {"Bud0": x0}
    for k in range(1, min(KMAX, len(pool)) + 1):                 # station count, affine
        # no minimum-overlap skip here: _affine itself falls back to the identity (a=0, b=1) below 30
        # overlap days, exactly as ladder_v2.rungs uses it (parity fix 2026-09-27)
        j = pd.concat([p0, daily(pool[:k]).rename("fit")], axis=1).dropna()
        a, b = _affine(j.fit.to_numpy(), j.bud0.to_numpy())
        P[f"k{k}"] = a + b * x0
    P["s2"], P["s6"] = P.get("k2"), P.get(f"k{min(6, len(pool))}")
    reg = pool[min(6, len(pool)):]
    if len(reg):
        bg = st[st.station_id.isin(reg)].groupby("date").pm25.quantile(0.10).rename("bg")
        for name, stations in (("s2bg", pool[:2]), ("s6bg", pool[:min(6, len(pool))])):
            j = pd.concat([p0, bg, daily(stations).rename("fit")], axis=1).dropna()
            if len(j) > 60:
                A = np.vstack([np.ones(len(j)), j.bud0.to_numpy(), j.bg.to_numpy()]).T
                c, *_ = np.linalg.lstsq(A, j.fit.to_numpy(), rcond=None)
                kk = pd.concat([p0, bg], axis=1).reindex(fr.index)
                P[name] = c[0] + c[1] * kk.bud0.to_numpy() + c[2] * kk.bg.fillna(kk.bg.mean()).to_numpy()
    return fr, {k: v for k, v in P.items() if v is not None}


def rmse(x, o):
    return float(np.sqrt(np.mean((x - o) ** 2)))


def own_weights(fr, P, seed):
    """This city's own optimal weights for every chain step -- used ONLY to cross-fit OTHER cities."""
    obs, days = fr.obs.to_numpy(), fr.index.astype(str).to_numpy()
    w = {}
    for name, order in (("A", ORDER_A), ("B", ORDER_B)):
        # chain as far as this city's rungs exist, exactly as ladder_v2.chain does (a city with no
        # outer ring still contributes its early-step weights); parity fix 2026-09-27
        cur = P["Bud0"]
        for r in order:
            if r not in P:
                break
            ww = sh.optimal_weight(cur, P[r], obs, groups=days, seed=seed).w
            w[f"{name}:{r}"] = ww
            cur = sh.combine(cur, P[r], ww)
    for k in range(1, KMAX + 1):
        if f"k{k}" in P:
            w[f"k{k}"] = sh.optimal_weight(P["Bud0"], P[f"k{k}"], obs, groups=days, seed=seed).w
    return w


def score(fr, P, wg):
    obs = fr.obs.to_numpy()
    out = {"Bud0": rmse(P["Bud0"], obs)}
    for name, order in (("A", ORDER_A), ("B", ORDER_B)):
        cur = P["Bud0"]
        for r in order:
            if r not in P or f"{name}:{r}" not in wg or pd.isna(wg[f"{name}:{r}"]):
                break
            cur = sh.combine(cur, P[r], float(wg[f"{name}:{r}"]))
            out[f"{name}_{r}"] = rmse(cur, obs)
    for k in range(1, KMAX + 1):
        if f"k{k}" in P and f"k{k}" in wg:
            out[f"k{k}"] = rmse(sh.combine(P["Bud0"], P[f"k{k}"], float(wg[f"k{k}"])), obs)
    return out


def summarise(C, cols, rng, nboot):
    res = {}
    for stratum, sub in (("pooled", C), ("deep_tropical", C[C.band == "deep_tropical"])):
        for col in cols:
            s = sub[[col, "cluster"]].dropna()
            if len(s) < 4:
                continue
            v, g = s[col].to_numpy(), s.cluster.to_numpy()
            bc, bk = boot_city(v, rng, nboot), boot_cluster(v, g, rng, nboot)
            res[f"{stratum}.{col}"] = dict(
                n=int(len(v)), median=float(np.median(v)),
                city=[float(np.percentile(bc, 2.5)), float(np.percentile(bc, 97.5))],
                cluster=[float(np.percentile(bk, 2.5)), float(np.percentile(bk, 97.5))])
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stream", choices=("maiac", "ghap"), default="maiac")
    ap.add_argument("--splits", type=int, default=21)
    ap.add_argument("--bag", type=int, default=5)
    ap.add_argument("--boot", type=int, default=4000)
    a = ap.parse_args()
    st, p, met, geo_f, sat = load(a.stream, True, "grid", "v2")
    b0 = bagged_bud0(p, met + geo_f + sat, a.bag)
    meta = city_meta(list(st)).set_index("city")
    seeds = [SEED] + [SEED + 1000 * (k + 1) for k in range(a.splits - 1)]
    cities = [c for c in st if c in set(b0.city)]

    cache, W = {}, []
    for c in cities:
        for sd in seeds:
            rp = raw_preds(c, st[c], b0, sd)
            if rp is None:
                continue
            cache[(c, sd)] = rp
            W.append({"city": c, **own_weights(*rp, sd)})
    W = pd.DataFrame(W).set_index("city")

    rows = []
    for (c, sd), (fr, P) in cache.items():
        wg = W.drop(index=c).median()                                   # other cities only
        rows.append({"city": c, "seed": sd, **score(fr, P, wg)})
    R = pd.DataFrame(rows)
    # PARITY: order A IS the production ladder, so it must reproduce ladder_v2's rung RMSEs exactly
    prod = OUTD / f"{a.stream}_s{a.splits}_b{a.bag}_crossfit_c18_grid_dv2_splits.csv"
    if prod.exists():
        pr = pd.read_csv(prod, dtype={"city": str})
        pr = pr[pr.arm == "reconstruction"]
        j = R.merge(pr, on=["city", "seed"])
        for x, y in (("Bud0", "Bud0_rmse"), ("A_s2", "Bud1_rmse"), ("A_s6", "Bud2_rmse"),
                     ("A_s6bg", "Bud3_rmse")):
            d = (j[x] - j[y]).abs().max()
            assert not (d > 1e-9), f"parity with production failed at {x}: {d}"
        print(f"    parity with production ladder_v2: exact on {len(j)} city-splits", flush=True)
    g = lambda x, y: 100 * (R[x] - R[y]) / R[x]
    R["bg_after_6stn"] = g("A_s6", "A_s6bg")
    R["bg_after_2stn"] = g("B_s2", "B_s2bg")
    R["stn3to6_no_bg"] = g("A_s2", "A_s6")
    R["stn3to6_with_bg"] = g("B_s2bg", "B_s6bg")
    R["endpoint_gap"] = R.A_s6bg - R.B_s6bg
    for k in range(1, KMAX + 1):
        if f"k{k}" in R:
            R[f"gain_k{k}"] = g("Bud0", f"k{k}")
    for k in range(2, KMAX + 1):
        if f"gain_k{k}" in R:
            R[f"extra_k{k}_over_k1"] = R[f"gain_k{k}"] - R["gain_k1"]
    R = R.replace([np.inf, -np.inf], np.nan)

    eff = [c for c in R.columns if c.startswith(("bg_after", "stn3to6", "endpoint_gap", "gain_k", "extra_k"))]
    C = R.groupby("city")[eff].median().join(meta[["band", "cluster"]])
    rng = np.random.default_rng(SEED)
    res = {"config": dict(stream=a.stream, splits=a.splits, bag=a.bag, cities=int(len(C))),
           **summarise(C, eff, rng, a.boot)}
    tag = f"{a.stream}_s{a.splits}_b{a.bag}"
    OUTD.mkdir(parents=True, exist_ok=True)
    R.to_csv(OUTD / f"secondary_splits_{tag}.csv", index=False)
    C.to_csv(OUTD / f"secondary_percity_{tag}.csv")
    jp = OUTD / f"secondary_{tag}.json"; tmp = jp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(res, indent=2), encoding="utf-8"); os.replace(tmp, jp)

    print(f"\n=== ladder v2 secondary, {tag}, {len(C)} cities (median [cluster 95%]) ===")
    for k in ("bg_after_6stn", "bg_after_2stn", "stn3to6_no_bg", "stn3to6_with_bg", "endpoint_gap",
              *[f"gain_k{k}" for k in range(1, KMAX + 1)], *[f"extra_k{k}_over_k1" for k in range(2, KMAX + 1)]):
        for stratum in ("pooled", "deep_tropical"):
            v = res.get(f"{stratum}.{k}")
            if v:
                print(f"  {stratum:<14}{k:<20} n={v['n']:>2} {v['median']:+8.2f}   "
                      f"[{v['cluster'][0]:+7.2f}, {v['cluster'][1]:+7.2f}]")
    print(f"-> {jp}")


if __name__ == "__main__":
    main()
