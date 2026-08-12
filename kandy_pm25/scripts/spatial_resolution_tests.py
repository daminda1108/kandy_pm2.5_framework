"""spatial_resolution_tests.py — is the spatial signal being measured at the wrong
resolution? (2026-08-06)

PRE-REGISTERED. Gates and predictions are fixed in
`docs/prereg_spatial_resolution_2026-08-06.md`, written before any number here was
computed. Nothing in this script may be tuned after seeing a result; a failure is
reported as a failure.

TEST A -- regime-conditional rank. Stratify hours by ventilation index VI = BLH x wind
speed, taken from the model's own MET DRIVERS so the strata are independent of any
observation, and recompute the station rank within each quintile. Prediction: rank is
stronger under stagnation (Q1) than under ventilation (Q5), because that is what the
confinement mechanism claims.

TEST B -- zone contrast. Assign stations to terciles of the TRAFFIC EMISSION SURFACE
(a model input, using no concentration data of any kind), and compare the observed
top-minus-bottom contrast with the modelled one across cities. Prediction: aggregation
recovers signal that per-station ranking misses.

Neither test changes any model quantity. Both are re-measurements.

Run:  .venv/Scripts/python.exe scripts/spatial_resolution_tests.py
Out:  results/figures/multicity/spatial_resolution_tests.{csv,json}
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
NBOOT = 4000
SEED = 20260806
MIN_STATIONS = 4          # same threshold the scorecard uses for an estimable rank


def city_frames(city: str):
    """Merged per-station hourly (pred, obs) + the met drivers for stratification."""
    xf._setup(city)
    st, anc = xf._stations_split()
    vault = [s for s in st.index if int(s) not in anc]
    P, O, M = [], [], []
    for y in xf.xp.YEARS:
        try:
            P.append(xf._pred_at_stations(y)); O.append(xf._obs(y))
            M.append(xf._met(y))
        except Exception:
            continue
    if not P:
        raise RuntimeError("no years available")
    P = pd.concat(P).dropna(subset=["pred"]); O = pd.concat(O); M = pd.concat(M)
    P = P[P.station_id.isin(vault)]; O = O[O.station_id.isin(vault)]
    J = P.merge(O[["loct", "station_id", "pm25"]], on=["loct", "station_id"], how="inner")
    # ventilation index from the MET DRIVERS ONLY -- no observation enters the strata
    wcol = "wspd" if "wspd" in M.columns else None
    if wcol is None:
        for a, b in (("u10", "v10"), ("u", "v")):
            if a in M.columns and b in M.columns:
                M["wspd"] = np.hypot(M[a], M[b]); wcol = "wspd"; break
    bcol = next((c for c in M.columns if c.lower() in ("blh", "blh_m", "zpbl")), None)
    if wcol is None or bcol is None:
        raise RuntimeError(f"no met columns for VI (have {list(M.columns)})")
    M = M[["loct", wcol, bcol]].dropna().drop_duplicates("loct")
    M["VI"] = M[bcol] * M[wcol]
    J = J.merge(M[["loct", "VI"]], on="loct", how="inner")
    return J, st, vault


def rho_boot(x, y, seed=SEED, nboot=NBOOT):
    from scipy.stats import spearmanr
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    if n < MIN_STATIONS:
        return np.nan, np.nan, np.nan, n
    r = spearmanr(x, y)[0]
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(nboot):
        k = rng.integers(0, n, n)
        if len(np.unique(k)) < 3:
            continue
        v = spearmanr(x[k], y[k])[0]
        if np.isfinite(v):
            bs.append(v)
    lo, hi = (np.percentile(bs, [5, 95]) if bs else (np.nan, np.nan))
    return float(r), float(lo), float(hi), n


def emission_tercile(city: str, st, ids):
    """Station terciles of the traffic emission surface -- a MODEL INPUT.

    Uses no concentration data, observed or modelled, so the zones cannot be drawn
    around the outcome.
    """
    from scipy.interpolate import RegularGridInterpolator
    t = np.load(REPO / "data" / "processed" / "decomp" / f"S_traffic_{city}.npz")
    S, la, lo = t["S_traffic"], t["lats"], t["lons"]
    f = RegularGridInterpolator(
        (np.linspace(la[0], la[-1], S.shape[0]), np.linspace(lo[0], lo[-1], S.shape[1])),
        S, bounds_error=False, fill_value=np.nan)
    sub = st.loc[[i for i in ids if i in st.index]]
    v = f(np.column_stack([sub.lat.to_numpy(), sub.lon.to_numpy()]))
    s = pd.Series(v, index=sub.index).dropna()
    if len(s) < 3 or s.nunique() < 3:
        return None
    q = s.rank(pct=True)
    return pd.Series(np.where(q <= 1 / 3, "Z1", np.where(q >= 2 / 3, "Z3", "Z2")),
                     index=s.index)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== PRE-REGISTERED spatial-resolution tests ===")
    print("    gates: docs/prereg_spatial_resolution_2026-08-06.md\n")
    A, B, rows = {}, {}, []
    for city in CITIES:
        try:
            J, st, vault = city_frames(city)
        except Exception as e:                                     # noqa: BLE001
            print(f"  {city:<12} SKIP ({type(e).__name__}: {e})")
            continue
        name = xf.CFG["name"].split(" (")[0]

        # ── Test A: rank within ventilation quintiles ────────────────────────
        J["q"] = pd.qcut(J.VI, 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"], duplicates="drop")
        per_q = {}
        for qq in ["Q1", "Q5"]:
            g = J[J.q == qq]
            if g.empty:
                continue
            ps = g.groupby("station_id").pred.mean()
            os_ = g.groupby("station_id").pm25.mean()
            c = ps.index.intersection(os_.index)
            r, lo, hi, n = rho_boot(ps[c].to_numpy(), os_[c].to_numpy())
            per_q[qq] = {"rho": r, "ci": [lo, hi], "n": n, "hours": int(len(g))}
        # annual reference on the same stations
        ps = J.groupby("station_id").pred.mean(); os_ = J.groupby("station_id").pm25.mean()
        c = ps.index.intersection(os_.index)
        r_all, lo_all, hi_all, n_all = rho_boot(ps[c].to_numpy(), os_[c].to_numpy())
        A[name] = {"annual": {"rho": r_all, "ci": [lo_all, hi_all], "n": n_all}, **per_q}
        q1 = per_q.get("Q1", {}).get("rho", np.nan)
        q5 = per_q.get("Q5", {}).get("rho", np.nan)
        print(f"  {name:<12} A: annual {r_all:+.2f} | stagnant Q1 {q1:+.2f} | "
              f"ventilated Q5 {q5:+.2f} | gap {q1 - q5:+.2f}  (n={n_all})")

        # ── Test B: zone contrast on emission terciles ───────────────────────
        zon = emission_tercile(city, st, list(c))
        if zon is None or zon.nunique() < 3:
            B[name] = {"estimable": False}
            print(f"  {' ':<12} B: not estimable (needs stations in 3 emission terciles)")
        else:
            om = os_.reindex(zon.index); pm = ps.reindex(zon.index)
            d_obs = float(om[zon == "Z3"].mean() - om[zon == "Z1"].mean())
            d_mod = float(pm[zon == "Z3"].mean() - pm[zon == "Z1"].mean())
            B[name] = {"estimable": True, "d_obs": d_obs, "d_mod": d_mod,
                       "n_z1": int((zon == "Z1").sum()), "n_z3": int((zon == "Z3").sum()),
                       "sign_agree": bool(np.sign(d_obs) == np.sign(d_mod))}
            print(f"  {' ':<12} B: zone contrast obs {d_obs:+6.2f} | mod {d_mod:+6.2f} | "
                  f"{'AGREE' if B[name]['sign_agree'] else 'disagree'}")
        rows.append({"city": name, "rho_annual": r_all, "rho_Q1": q1, "rho_Q5": q5,
                     **{f"B_{k}": v for k, v in B[name].items()}})

    # ── gates ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 66 + "\n  PRE-REGISTERED GATES\n" + "=" * 66)
    res = {"testA": A, "testB": B, "gates": {}}

    gaps = {c: v["Q1"]["rho"] - v["Q5"]["rho"] for c, v in A.items()
            if "Q1" in v and "Q5" in v and np.isfinite(v["Q1"]["rho"])
            and np.isfinite(v["Q5"]["rho"])}
    n_better = sum(1 for g in gaps.values() if g > 0)
    a1 = n_better >= 7
    q1s = [v["Q1"]["rho"] for v in A.values() if "Q1" in v and np.isfinite(v["Q1"]["rho"])]
    pooled_q1 = float(np.mean(q1s)) if q1s else np.nan
    a2 = np.isfinite(pooled_q1) and pooled_q1 >= 0.40
    analogues = [c for c in gaps if c.split()[0] in ("Chiang", "Kathmandu")]
    a3 = bool(analogues) and all(gaps[c] > 0 for c in analogues)
    pooled_gap = float(np.mean(list(gaps.values()))) if gaps else np.nan
    print(f"  A1  stagnant > ventilated in >=7 of 9 : {n_better} of {len(gaps)}"
          f"   -> {'PASS' if a1 else 'FAIL'}")
    print(f"  A2  pooled rho(Q1) >= 0.40           : {pooled_q1:+.3f}"
          f"   -> {'PASS' if a2 else 'FAIL'}")
    print(f"  A3  gap > 0 at Kandy's analogues     : "
          f"{ {c: round(gaps[c], 2) for c in analogues} }   -> {'PASS' if a3 else 'FAIL'}")
    print(f"      (pooled gap Q1-Q5 = {pooled_gap:+.3f}; falsifier is |gap| < 0.05)")

    est = {c: v for c, v in B.items() if v.get("estimable")}
    n_sign = sum(1 for v in est.values() if v["sign_agree"])
    b2 = n_sign >= 7
    dm = np.array([v["d_mod"] for v in est.values()], float)
    do = np.array([v["d_obs"] for v in est.values()], float)
    if len(dm) >= 4:
        rng = np.random.default_rng(SEED)
        sl = float(np.polyfit(dm, do, 1)[0])
        bs = []
        for _ in range(NBOOT):
            k = rng.integers(0, len(dm), len(dm))
            if len(np.unique(k)) < 3:
                continue
            try:
                bs.append(float(np.polyfit(dm[k], do[k], 1)[0]))
            except Exception:                                       # noqa: BLE001
                continue
        blo, bhi = np.percentile(bs, [5, 95])
        b1 = bool(blo > 0)
    else:
        sl = blo = bhi = np.nan; b1 = False
    nulls = {"Yichang", "Bazhong", "Xichang", "Chiang"}
    rec = [c for c, v in est.items()
           if c.split()[0] in nulls and v["sign_agree"] and abs(v["d_obs"]) > 0.5]
    b3 = len(rec) >= 2
    print(f"\n  B1  cross-city slope > 0 (CI excl 0) : slope {sl:+.3f} "
          f"[{blo:+.3f}, {bhi:+.3f}]   -> {'PASS' if b1 else 'FAIL'}")
    print(f"  B2  sign agreement in >=7 of 9       : {n_sign} of {len(est)}"
          f"   -> {'PASS' if b2 else 'FAIL'}")
    print(f"  B3  recovers >=2 station-null cities : {rec}   -> {'PASS' if b3 else 'FAIL'}")

    res["gates"] = {"A1": bool(a1), "A2": bool(a2), "A3": bool(a3),
                    "B1": bool(b1), "B2": bool(b2), "B3": bool(b3),
                    "pooled_rho_Q1": None if not np.isfinite(pooled_q1) else round(pooled_q1, 4),
                    "pooled_gap_Q1_Q5": None if not np.isfinite(pooled_gap) else round(pooled_gap, 4),
                    "n_stagnant_better": n_better, "n_sign_agree": n_sign,
                    "zone_slope": None if not np.isfinite(sl) else round(sl, 4),
                    "zone_slope_ci90": [None if not np.isfinite(blo) else round(blo, 4),
                                        None if not np.isfinite(bhi) else round(bhi, 4)]}
    npass = sum(res["gates"][k] for k in ("A1", "A2", "A3", "B1", "B2", "B3"))
    res["verdict"] = (
        f"{npass} of 6 pre-registered predictions met. "
        + ("Test A supports a regime-conditional reading of the spatial claim. "
           if (a1 and abs(pooled_gap) >= 0.05) else
           "Test A does NOT support regime-conditioning; annual averaging is not "
           "diluting a stagnation signal, and the current statistic is the right one. ")
        + ("Test B supports reporting zone contrast in place of station rank."
           if (b1 and b2) else
           "Test B does NOT support a zone-level claim; the signal is absent rather "
           "than mis-measured, and the information-ceiling conclusion stands unqualified."))
    print(f"\n  VERDICT: {res['verdict']}")
    pd.DataFrame(rows).to_csv(OUT / "spatial_resolution_tests.csv", index=False)
    (OUT / "spatial_resolution_tests.json").write_text(
        json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote spatial_resolution_tests.{{csv,json}}")


if __name__ == "__main__":
    main()
