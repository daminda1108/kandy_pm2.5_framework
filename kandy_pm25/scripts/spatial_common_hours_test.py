"""spatial_common_hours_test.py — a spatial rank statistic that cannot launder temporal
skill into a spatial number (2026-08-07).

PRE-REGISTERED: `docs/prereg_common_hours_spatial_2026-08-07.md`. Gates C1-C5 and the
decision rule were fixed before any number here was computed, together with the author's
stated prior (that this will make the spatial claim WEAKER, not stronger).

THE CONFOUND
------------
The published spatial rank averages model and observations over DIFFERENT hour sets, so a
station's observed mean partly encodes when it reported. Hour-matching fixes that but
introduces a worse problem: it gives every station the temporal weighting of its own
observations, so a model with strong temporal skill and ZERO spatial skill still produces
correlated station means. Seasonal r here is 0.94-1.00, so that channel is wide open.

THE FIX
-------
E1 network anomaly -- remove each hour's network mean from BOTH series within that hour,
   so every hour-level signal (season, diurnal, episodes, the whole temporal anchor) is
   differenced away before any station mean is taken. What survives is the persistent
   station-to-station offset, which is the spatial claim and nothing else.
E2 common hours   -- restrict to hours when >=80% of ranked stations report together, so
   all stations share one hour set by construction. Independent route, same target.

C3 permutation control is load-bearing: shuffling which station gets which modelled
anomaly must destroy the rank. If it does not, E1 can manufacture correlation and is void.

Run:  .venv/Scripts/python.exe scripts/spatial_common_hours_test.py
Out:  results/figures/multicity/spatial_common_hours_test.{csv,json}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import xichang_paper_figures as xf                       # noqa: E402

OUT = REPO / "results" / "figures" / "multicity"
CITIES = ["xichang", "chiangmai", "bazhou", "chandigarh", "kathmandu",
          "baoji", "taian", "yichang", "medellin", "bogota"]
MIN_ST = 4              # stations needed for an estimable rank (as everywhere else)
MIN_NET = 3             # |S_t| floor for an anomaly hour        [pre-registered]
QUORUM = 0.80           # E2 station quorum                      [pre-registered]
MIN_COMMON_H = 200      # E2 minimum shared hours                [pre-registered]
NPERM = 2000
SEED = 20260807


def merged(city: str):
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


def spear(x, y):
    from scipy.stats import spearmanr
    if len(x) < MIN_ST:
        return np.nan
    v = spearmanr(np.asarray(x, float), np.asarray(y, float))[0]
    return float(v) if np.isfinite(v) else np.nan


def e1_anomaly(J: pd.DataFrame):
    """Per-hour network-mean-removed anomalies, then rank station mean anomalies."""
    g = J.groupby("loct")
    J = J.assign(n_t=g.pm25.transform("size"))
    J = J[J.n_t >= MIN_NET]
    if J.empty:
        return np.nan, 0, 0, None
    J = J.assign(a_obs=J.pm25 - J.groupby("loct").pm25.transform("mean"),
                 a_mod=J.pred - J.groupby("loct").pred.transform("mean"))
    ao = J.groupby("station_id").a_obs.mean()
    am = J.groupby("station_id").a_mod.mean()
    c = ao.index.intersection(am.index)
    return spear(am[c], ao[c]), len(c), int(J.loct.nunique()), (am[c], ao[c])


def e2_common(J: pd.DataFrame):
    """Means over hours where >=QUORUM of the ranked stations report together."""
    ids = J.station_id.unique()
    need = max(MIN_ST, int(np.ceil(QUORUM * len(ids))))
    cnt = J.groupby("loct").station_id.nunique()
    hrs = cnt[cnt >= need].index
    if len(hrs) < MIN_COMMON_H:
        return np.nan, 0, int(len(hrs))
    K = J[J.loct.isin(hrs)]
    pm = K.groupby("station_id").pred.mean(); om = K.groupby("station_id").pm25.mean()
    c = pm.index.intersection(om.index)
    return spear(pm[c], om[c]), len(c), int(len(hrs))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== PRE-REGISTERED common-hours / anomaly spatial test ===")
    print("    gates: docs/prereg_common_hours_spatial_2026-08-07.md")
    print("    author's stated prior: this will make the spatial claim WEAKER\n")
    sc = pd.read_csv(OUT / "validation_scorecard.csv")
    sc["key"] = sc.city.map(lambda s: s.split(" (")[0].strip())
    pub = dict(zip(sc.key, sc.spatial))
    rng = np.random.default_rng(SEED)

    rows, perm_all = [], []
    print("  city           published   paired      E1 anom    E2 common   nH(E1)  nH(E2)")
    for city in CITIES:
        try:
            J = merged(city)
        except Exception as e:                                       # noqa: BLE001
            print(f"  {city:<14} SKIP ({type(e).__name__}: {e})")
            continue
        name = xf.CFG["name"].split(" (")[0].strip()
        pm = J.groupby("station_id").pred.mean(); om = J.groupby("station_id").pm25.mean()
        c = pm.index.intersection(om.index)
        r_paired = spear(pm[c], om[c])
        r1, n1, h1, vecs = e1_anomaly(J)
        r2, n2, h2 = e2_common(J)

        # C3 permutation control on E1
        p95 = np.nan
        if vecs is not None and np.isfinite(r1) and len(vecs[0]) >= MIN_ST:
            am, ao = vecs
            null = [spear(rng.permutation(am.to_numpy()), ao.to_numpy())
                    for _ in range(NPERM)]
            null = [v for v in null if np.isfinite(v)]
            if null:
                perm_all += null
                p95 = float(np.percentile(null, 95))
        rows.append(dict(city=name, published=pub.get(name), paired=r_paired,
                         E1_anomaly=r1, E2_common=r2, n_stations=n1,
                         hours_E1=h1, hours_E2=h2, perm_p95=p95))
        f = lambda v: "     —" if v is None or not np.isfinite(v) else f"{v:+6.2f}"   # noqa: E731
        print(f"  {name:<14}{f(pub.get(name, np.nan))}    {f(r_paired)}    {f(r1)}     "
              f"{f(r2)}   {h1:>7} {h2:>7}")

    R = pd.DataFrame(rows)
    R.to_csv(OUT / "spatial_common_hours_test.csv", index=False)
    est = R.dropna(subset=["E1_anomaly"])

    print("\n" + "=" * 72 + "\n  PRE-REGISTERED GATES\n" + "=" * 72)
    both = est.dropna(subset=["E2_common"])
    d12 = float(np.abs(both.E1_anomaly.mean() - both.E2_common.mean())) if len(both) else np.nan
    sign12 = int((np.sign(both.E1_anomaly) == np.sign(both.E2_common)).sum())
    c1 = bool(np.isfinite(d12) and d12 <= 0.15 and sign12 >= 7)
    print(f"  C1  E1 vs E2 agree (|d|<=0.15, sign>=7/9)  : |d| {d12:.3f}, "
          f"sign {sign12}/{len(both)}   -> {'PASS' if c1 else 'FAIL'}")

    pooled_e1 = float(est.E1_anomaly.mean())
    pooled_pair = float(est.paired.mean())
    c2 = bool(pooled_e1 < pooled_pair - 0.10)
    print(f"  C2  pooled E1 < pooled paired - 0.10      : E1 {pooled_e1:+.3f} vs "
          f"paired {pooled_pair:+.3f}   -> {'PASS' if c2 else 'FAIL'}")

    null_c = float(np.mean(perm_all)) if perm_all else np.nan
    null95 = float(np.percentile(perm_all, 95)) if perm_all else np.nan
    c3 = bool(np.isfinite(null_c) and abs(null_c) <= 0.10 and pooled_e1 > null95)
    print(f"  C3  permutation null ~0 and E1 > null p95 : null {null_c:+.3f}, "
          f"p95 {null95:+.3f}, E1 {pooled_e1:+.3f}   -> {'PASS' if c3 else 'FAIL'}")

    n40 = int((est.E1_anomaly >= 0.40).sum())
    branch = ("REVISE UPWARD: fine spatial rank DOES transfer once the confound is removed"
              if n40 >= 7 else
              "STANDS, restated: partial and regime-bounded, on a corrected estimator"
              if n40 >= 4 else
              "STRENGTHENED: the information-ceiling conclusion holds and the previously "
              "published values were optimistic")
    print(f"  C4  cities with E1 >= 0.40                : {n40} of {len(est)}"
          f"   -> {branch}")

    an = {r.city: None if not np.isfinite(r.E1_anomaly) else round(float(r.E1_anomaly), 3)
          for r in est.itertuples() if r.city.split()[0] in ("Chiang", "Kathmandu")}
    print(f"  C5  Kandy's analogues (reported, no gate) : {an}")

    res = {"gates": {"C1": c1, "C2": c2, "C3": c3},
           "pooled": {"published": round(float(est.published.mean(skipna=True)), 4),
                      "paired": round(pooled_pair, 4), "E1_anomaly": round(pooled_e1, 4),
                      "E2_common": None if both.empty else round(float(both.E2_common.mean()), 4)},
           "permutation_null": {"centre": None if not np.isfinite(null_c) else round(null_c, 4),
                                "p95": None if not np.isfinite(null95) else round(null95, 4)},
           "C4": {"n_ge_040": n40, "n_estimable": int(len(est)), "branch": branch},
           "C5_analogues": an,
           "per_city": {r.city: {"published": None if r.published is None or not np.isfinite(r.published) else round(float(r.published), 3),
                                 "paired": None if not np.isfinite(r.paired) else round(float(r.paired), 3),
                                 "E1": None if not np.isfinite(r.E1_anomaly) else round(float(r.E1_anomaly), 3),
                                 "E2": None if not np.isfinite(r.E2_common) else round(float(r.E2_common), 3)}
                        for r in R.itertuples()},
           "prior_stated_in_prereg": ("author expected E1 to fall well below paired and "
                                      "near or below published -- i.e. a WEAKER claim"),
           "validity": ("C1 and C3 are the validity gates. If either fails, neither E1 nor "
                        "E2 may be used and the spatial column is left as published, with "
                        "the instability documented as a limitation.")}
    res["verdict"] = (
        ("VALID estimator (C1+C3 pass). " if (c1 and c3) else
         "INVALID -- validity gate failed; do NOT adopt these numbers. ")
        + (f"Pooled spatial rank is {pooled_e1:+.3f} once every hour-level signal is "
           f"differenced away, against {pooled_pair:+.3f} hour-matched and "
           f"{est.published.mean(skipna=True):+.3f} as published. ")
        + branch + ".")
    print(f"\n  VERDICT: {res['verdict']}")
    (OUT / "spatial_common_hours_test.json").write_text(
        json.dumps(res, indent=1, default=float), encoding="utf-8")
    print("\nwrote spatial_common_hours_test.{csv,json}")


if __name__ == "__main__":
    main()
