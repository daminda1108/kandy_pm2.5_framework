"""spatial_significance_test.py — per-city significance for the anomaly rank, and an
estimator that survives sparse networks (2026-08-07).

PRE-REGISTERED: `docs/prereg_spatial_significance_2026-08-07.md`. Gates D1-D5 and the
decision rule were fixed before any number here was computed.

WHAT THE PREVIOUS ROUND LEFT OPEN
---------------------------------
E1 (per-hour network-mean removal) gave pooled +0.621 vs +0.372 published. Its pooled
permutation control passed. But the validity gate C1 was UNEVALUABLE -- the common-hours
estimator needed 80% of stations reporting at once and only 3 of 9 cities ever manage it
-- and per-city significance was never registered. The pooled null p95 is +0.520, so at
4-17 stations per city a rank of 0.5 is easily chance. "8 of 9 above 0.40" was arithmetic.

THIS ROUND
----------
E3 pairwise co-observed concordance -- for each station PAIR, compare the mean observed
   difference with the mean modelled difference over the hours both report. Never needs a
   global quorum, so it is estimable on the coverage this panel actually has. That was the
   design error that killed C1 and it is not repeated.
D1 per-city permutation p-values, 5000 draws.
D4 counts only cities that are BOTH significant and above 0.40.

Run:  .venv/Scripts/python.exe scripts/spatial_significance_test.py
Out:  results/figures/multicity/spatial_significance_test.{csv,json}
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import xichang_paper_figures as xf                       # noqa: E402

OUT = REPO / "results" / "figures" / "multicity"
CITIES = ["xichang", "chiangmai", "bazhou", "chandigarh", "kathmandu",
          "baoji", "taian", "yichang", "medellin", "bogota"]
MIN_ST = 4
MIN_NET = 3
MIN_PAIR_H = 50         # pair overlap floor        [pre-registered]
NPERM = 5000            # per-city permutations     [pre-registered]
ALPHA = 0.05            # significance threshold    [pre-registered]
SEED = 20260807


def merged(city: str) -> pd.DataFrame:
    xf._setup(city)
    st, anc = xf._stations_split()
    vault = [s for s in st.index if int(s) not in anc]
    P, O = [], []
    for y in xf.xp.YEARS:
        try:
            P.append(xf._pred_at_stations(y)); O.append(xf._obs(y))
        except Exception:
            continue
    P = pd.concat(P).dropna(subset=["pred"]); O = pd.concat(O)
    P = P[P.station_id.isin(vault)]; O = O[O.station_id.isin(vault)]
    return P.merge(O[["loct", "station_id", "pm25"]], on=["loct", "station_id"],
                   how="inner")


def anomalies(J: pd.DataFrame):
    """E1: per-hour network-mean removed station means."""
    J = J.assign(n_t=J.groupby("loct").pm25.transform("size"))
    J = J[J.n_t >= MIN_NET]
    if J.empty:
        return None, None
    J = J.assign(a_obs=J.pm25 - J.groupby("loct").pm25.transform("mean"),
                 a_mod=J.pred - J.groupby("loct").pred.transform("mean"))
    ao = J.groupby("station_id").a_obs.mean()
    am = J.groupby("station_id").a_mod.mean()
    c = ao.index.intersection(am.index)
    return (am[c], ao[c]) if len(c) >= MIN_ST else (None, None)


def pairwise_concordance(J: pd.DataFrame):
    """E3: sign agreement of observed vs modelled differences on co-observed hours."""
    piv_o = J.pivot_table(index="loct", columns="station_id", values="pm25")
    piv_m = J.pivot_table(index="loct", columns="station_id", values="pred")
    ids = [c for c in piv_o.columns if c in piv_m.columns]
    agree = tot = 0
    for i, j in combinations(ids, 2):
        both = piv_o[[i, j]].notna().all(axis=1) & piv_m[[i, j]].notna().all(axis=1)
        if int(both.sum()) < MIN_PAIR_H:
            continue
        do = float((piv_o.loc[both, i] - piv_o.loc[both, j]).mean())
        dm = float((piv_m.loc[both, i] - piv_m.loc[both, j]).mean())
        if do == 0 or dm == 0:
            continue
        tot += 1
        agree += int(np.sign(do) == np.sign(dm))
    if tot < 3:
        return np.nan, 0
    return 2.0 * agree / tot - 1.0, tot


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from scipy.stats import spearmanr, kendalltau
    print("=== PRE-REGISTERED per-city significance + sparse-network estimator ===")
    print("    gates: docs/prereg_spatial_significance_2026-08-07.md")
    print("    prior: middle branch expected; Chiang Mai expected to FAIL significance\n")
    rng = np.random.default_rng(SEED)
    rows = []
    print("  city            E1 rho    p      null p95   E1 tau   E3 tau   pairs   n")
    for city in CITIES:
        try:
            J = merged(city)
            am, ao = anomalies(J)
        except Exception as e:                                        # noqa: BLE001
            print(f"  {city:<15} SKIP ({type(e).__name__}: {e})")
            continue
        name = xf.CFG["name"].split(" (")[0].strip()
        if am is None:
            print(f"  {name:<15} not estimable (<{MIN_ST} ranked stations)")
            rows.append(dict(city=name, e1=np.nan, p=np.nan, null95=np.nan,
                             e1_tau=np.nan, e3=np.nan, pairs=0, n=0))
            continue
        x, y = am.to_numpy(float), ao.to_numpy(float)
        e1 = float(spearmanr(x, y)[0])
        e1_tau = float(kendalltau(x, y)[0])
        null = np.array([spearmanr(rng.permutation(x), y)[0] for _ in range(NPERM)])
        null = null[np.isfinite(null)]
        p = float((np.abs(null) >= abs(e1)).mean())
        null95 = float(np.percentile(null, 95))
        e3, npairs = pairwise_concordance(J)
        rows.append(dict(city=name, e1=e1, p=p, null95=null95, e1_tau=e1_tau,
                         e3=e3, pairs=npairs, n=len(x)))
        star = "*" if p < ALPHA else " "
        print(f"  {name:<15}{e1:+6.2f}{star} {p:6.3f}   {null95:+7.2f}   "
              f"{e1_tau:+6.2f}   {'   —' if not np.isfinite(e3) else f'{e3:+6.2f}'}"
              f"{npairs:>8}{len(x):>4}")

    R = pd.DataFrame(rows)
    R.to_csv(OUT / "spatial_significance_test.csv", index=False)
    est = R.dropna(subset=["e1"])

    print("\n" + "=" * 74 + "\n  PRE-REGISTERED GATES\n" + "=" * 74)
    nsig = int((est.p < ALPHA).sum())
    print(f"  D1  cities significant at p<{ALPHA}          : {nsig} of {len(est)}"
          f"   [{', '.join(est[est.p < ALPHA].city)}]")

    b = est.dropna(subset=["e3"])
    d = float(np.abs(b.e3.mean() - b.e1_tau.mean())) if len(b) else np.nan
    sgn = int((np.sign(b.e3) == np.sign(b.e1_tau)).sum()) if len(b) else 0
    d2 = bool(np.isfinite(d) and d <= 0.15 and sgn >= 7)
    print(f"  D2  E3 vs E1_tau agree (|d|<=0.15, >=7/9)  : |d| {d:.3f}, sign {sgn}/{len(b)}"
          f"   -> {'PASS' if d2 else 'FAIL'}")

    rn = (float(np.corrcoef(est.e1, est.n)[0, 1]) if len(est) >= 4 else np.nan)
    d3 = bool(np.isfinite(rn) and abs(rn) < 0.5)
    print(f"  D3  small-n inflation |r(E1, n)| < 0.5     : r {rn:+.3f}"
          f"   -> {'PASS' if d3 else 'FAIL — skill is confounded with network size'}")

    qual = est[(est.p < ALPHA) & (est.e1 >= 0.40)]
    nq = len(qual)
    branch = ("REVISE UPWARD: fine spatial rank transfers; E1 replaces the spatial column"
              if nq >= 7 else
              "STANDS, restated: partial and regime-bounded on a corrected estimator"
              if nq >= 4 else
              "STRENGTHENED: information ceiling holds; the pooled upward signal was "
              "small-sample noise")
    print(f"  D4  significant AND >= 0.40                : {nq} of {len(est)}"
          f"   [{', '.join(qual.city)}]\n      -> {branch}")

    an = {r.city: {"E1": round(float(r.e1), 3), "p": round(float(r.p), 4)}
          for r in est.itertuples() if r.city.split()[0] in ("Chiang", "Kathmandu")}
    print(f"  D5  Kandy's analogues                      : {an}")

    res = {"gates": {"D2_validity": d2, "D3_small_n": d3},
           "D1_n_significant": nsig, "D4": {"n_qualifying": nq, "cities": list(qual.city),
                                            "branch": branch},
           "D5_analogues": an,
           "pooled": {"E1_rho": round(float(est.e1.mean()), 4),
                      "E1_tau": round(float(est.e1_tau.mean()), 4),
                      "E3_tau": None if b.empty else round(float(b.e3.mean()), 4)},
           "r_E1_vs_nstations": None if not np.isfinite(rn) else round(rn, 4),
           "per_city": {r.city: {"E1": None if not np.isfinite(r.e1) else round(float(r.e1), 3),
                                 "p": None if not np.isfinite(r.p) else round(float(r.p), 4),
                                 "null_p95": None if not np.isfinite(r.null95) else round(float(r.null95), 3),
                                 "E3": None if not np.isfinite(r.e3) else round(float(r.e3), 3),
                                 "n": int(r.n)} for r in R.itertuples()},
           "prior": ("middle branch expected; Chiang Mai expected to FAIL significance. "
                     "The previous round's prior was WRONG and is recorded as such.")}
    res["verdict"] = (("VALID (D2 passes). " if d2 else
                       "INVALID -- D2 failed; neither estimator adopted, published column "
                       "stands with the instability documented. ")
                      + f"{nq} of {len(est)} cities are both significant and above 0.40. "
                      + branch + ".")
    print(f"\n  VERDICT: {res['verdict']}")
    (OUT / "spatial_significance_test.json").write_text(
        json.dumps(res, indent=1, default=float), encoding="utf-8")
    print("\nwrote spatial_significance_test.{csv,json}")


if __name__ == "__main__":
    main()
