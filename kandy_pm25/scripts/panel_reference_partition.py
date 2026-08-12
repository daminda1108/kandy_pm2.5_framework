"""panel_reference_partition.py — STEP 1: a reference local/background split at the panel
cities, to score a Kandy estimator against (2026-08-07).

PRE-REGISTERED: `docs/prereg_partition_identification_2026-08-07.md`. Gates P1-P4, the later
steps and the author's prior were fixed before any number here was computed.

WHY
---
Kandy's partition is closed by a per-year CONSTANT f, which is refuted from below by the
model's own coherence floor and which five reformulations failed to repair. Every one of
those attempts changed the FORM of the background while leaving the IDENTIFICATION untouched.
Before building an estimator that identifies the split from data, we need something to score
it against -- and the panel cities have the dense networks Kandy lacks.

METHOD
------
Stations are split into CORE and PERIPHERAL by percentile on the traffic emission surface --
a model input, using no concentration data of any kind, so the groups cannot be drawn around
the answer (same leakage-free rule as the zone test, F.36). For each hour the reference
background is the 10th percentile across reporting peripheral stations (a Lenschow lower
envelope taken across space instead of time), the reference local increment is the network
mean minus it, and f_ref = L_ref / T_ref.

This is a REFERENCE, not truth: it inherits Lenschow's assumption that the cleanest
peripheral station approximates the regional air. The gates below exist to reject cities
where even that is untenable.

Run:  .venv/Scripts/python.exe scripts/panel_reference_partition.py
Out:  results/figures/multicity/panel_reference_partition.{csv,json}
"""
from __future__ import annotations

import argparse
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
CORE_Q, PERI_Q = 2 / 3, 1 / 3      # emission-surface percentiles defining the groups
BG_PCTL = 10                        # Lenschow lower envelope across peripheral stations
MIN_PERI, MIN_HOURS = 2, 500        # minimum peripheral stations / usable hours
MIN_DAYS, MIN_H_PER_DAY = 60, 12    # --daily: usable days, hours needed for a daily mean
SEP_MIN = 0.25                      # P1: core-minus-peripheral percentile separation


def emission_pctl(city: str, st, ids):
    """Station percentile on the traffic emission surface (a MODEL INPUT)."""
    from scipy.interpolate import RegularGridInterpolator
    t = np.load(REPO / "data" / "processed" / "decomp" / f"S_traffic_{city}.npz")
    S, la, lo = t["S_traffic"], t["lats"], t["lons"]
    f = RegularGridInterpolator(
        (np.linspace(la[0], la[-1], S.shape[0]), np.linspace(lo[0], lo[-1], S.shape[1])),
        S, bounds_error=False, fill_value=np.nan)
    sub = st.loc[[i for i in ids if i in st.index]]
    v = pd.Series(f(np.column_stack([sub.lat.to_numpy(), sub.lon.to_numpy()])),
                  index=sub.index).dropna()
    return v.rank(pct=True) if len(v) >= 3 else None


def city_obs(city: str):
    xf._setup(city)
    st, _ = xf._stations_split()
    O = []
    for y in xf.xp.YEARS:
        try:
            O.append(xf._obs(y))
        except Exception:
            continue
    if not O:
        return None, None
    return pd.concat(O), st


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--daily", action="store_true",
                    help="daily-resolution reference (prereg_partition_daily_2026-08-07.md)")
    args, _ = ap.parse_known_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if args.daily:
        print("=== STEP 1b: DAILY-resolution reference partition (SECOND attempt) ===")
        print("    prereg: docs/prereg_partition_daily_2026-08-07.md")
        print("    the HOURLY attempt FAILED P4 (3 of 10); thresholds UNCHANGED")
        print("    prior: Q2 92-99%, Q4 passes with 5-7 cities, D1 mostly 'noise'\n")
    else:
        print("=== STEP 1: reference local/background split at the panel cities ===")
        print("    prereg: docs/prereg_partition_identification_2026-08-07.md")
        print("    prior: P1-P4 expected to pass; f_ref expected to vary ~2x by regime\n")
    # hourly ordering rates from the first attempt (F.40), for the D1 diagnostic
    HOURLY_ORDER = {"Chiang Mai": 0.78, "Bazhong": 0.87, "Kathmandu Valley": 0.98,
                    "Baoji": 0.95, "Tai'an": 0.86, "Yichang": 0.75,
                    "Medellín": 0.97, "Bogotá": 0.99}
    rows, detail = [], {}
    for city in CITIES:
        try:
            O, st = city_obs(city)
        except Exception as e:                                       # noqa: BLE001
            print(f"  {city:<12} SKIP ({type(e).__name__}: {e})"); continue
        if O is None:
            print(f"  {city:<12} no observations"); continue
        name = xf.CFG["name"].split(" (")[0].strip()
        ids = list(O.station_id.unique())
        pc = emission_pctl(city, st, ids)
        if pc is None:
            print(f"  {name:<12} not estimable (<3 stations on the emission surface)")
            rows.append(dict(city=name, estimable=False, reason="no emission percentile"))
            continue
        peri = pc[pc <= PERI_Q].index
        core = pc[pc >= CORE_Q].index
        sep = float(pc[core].median() - pc[peri].median()) if len(peri) and len(core) else np.nan
        if len(peri) < MIN_PERI or not np.isfinite(sep):
            print(f"  {name:<12} not estimable (peripheral n={len(peri)})")
            rows.append(dict(city=name, estimable=False, n_peri=int(len(peri)),
                             reason="too few peripheral stations"))
            continue

        if args.daily:
            # station daily means first, then the envelope across peripheral stations
            O = O.assign(d=O.loct.dt.floor("D"))
            sd = O.groupby(["d", "station_id"]).pm25.agg(["mean", "size"])
            sd = sd[sd["size"] >= MIN_H_PER_DAY]["mean"].rename("pm25").reset_index()
            P = sd[sd.station_id.isin(peri)]
            bg = P.groupby("d").pm25.apply(
                lambda s: np.percentile(s, BG_PCTL) if len(s) >= MIN_PERI else np.nan)
            net = sd.groupby("d").pm25.mean()
            nrep = sd.groupby("d").station_id.nunique()
            need = MIN_DAYS
        else:
            P = O[O.station_id.isin(peri)]
            g = P.groupby("loct").pm25
            bg = g.apply(lambda s: np.percentile(s, BG_PCTL) if len(s) >= MIN_PERI else np.nan)
            net = O.groupby("loct").pm25.mean()
            nrep = O.groupby("loct").station_id.nunique()
            need = MIN_HOURS
        df = pd.DataFrame({"B": bg, "T": net, "n": nrep}).dropna()
        if len(df) < need:
            print(f"  {name:<12} not estimable ({len(df)} usable hours)")
            rows.append(dict(city=name, estimable=False, hours=int(len(df)),
                             reason="too few hours")); continue
        df["f"] = 1.0 - df.B / df["T"].replace(0, np.nan)
        ok_order = float(((df.B < df["T"]) & df.f.between(0, 1)).mean())
        r_n = float(np.corrcoef(df.f.fillna(0), df.n)[0, 1]) if df.n.nunique() > 1 else 0.0

        p1, p2, p3 = sep >= SEP_MIN, ok_order >= 0.95, abs(r_n) <= 0.5
        mo = df.f.groupby(df.index.month).mean()
        hr = (df.f.groupby(df.index.hour).mean() if not args.daily
              else pd.Series({0: np.nan}))
        rows.append(dict(city=name, estimable=True, n_peri=int(len(peri)),
                         n_core=int(len(core)), separation=round(sep, 3),
                         hours=int(len(df)), f_mean=round(float(df.f.mean()), 3),
                         f_p10=round(float(df.f.quantile(.10)), 3),
                         f_p90=round(float(df.f.quantile(.90)), 3),
                         month_min=round(float(mo.min()), 3),
                         month_max=round(float(mo.max()), 3),
                         hour_min=round(float(hr.min()), 3),
                         hour_max=round(float(hr.max()), 3),
                         hourly_ordered=HOURLY_ORDER.get(name),
                         pct_ordered=round(ok_order, 3), r_f_nstations=round(r_n, 3),
                         P1=bool(p1), P2=bool(p2), P3=bool(p3)))
        detail[name] = {"f_by_month": {int(k): round(float(v), 3) for k, v in mo.items()},
                        "f_by_hour": {int(k): round(float(v), 3) for k, v in hr.items()}}
        print(f"  {name:<12} peri {len(peri):>2}/core {len(core):>2} sep {sep:+.2f} | "
              f"f {df.f.mean():.2f} [{df.f.quantile(.1):.2f}, {df.f.quantile(.9):.2f}] | "
              f"month {mo.min():.2f}-{mo.max():.2f} | ordered {100*ok_order:.0f}% | "
              f"{'PASS' if (p1 and p2 and p3) else 'fail'}")

    R = pd.DataFrame(rows)
    tag = "_daily" if args.daily else ""
    R.to_csv(OUT / f"panel_reference_partition{tag}.csv", index=False)
    est = R[R.get("estimable", False) == True]                       # noqa: E712
    passing = est[est.P1 & est.P2 & est.P3] if len(est) else est

    print("\n" + "=" * 74 + "\n  PRE-REGISTERED GATES\n" + "=" * 74)
    for g, lbl in [("P1", "periphery genuinely peripheral (sep >= 0.25)"),
                   ("P2", "reference physically ordered (>=95%)"),
                   ("P3", "not a network-geometry artefact (|r| <= 0.5)")]:
        n = int(est[g].sum()) if len(est) else 0
        print(f"  {g}  {lbl:<48} {n} of {len(est)}")
    p4 = len(passing) >= 5
    print(f"  P4  at least 5 cities pass P1-P3                    "
          f"{len(passing)} of {len(R)}   -> {'PASS' if p4 else 'FAIL — PLAN STOPS'}")

    if len(passing):
        spread = float((passing.month_max - passing.month_min).mean())
        ratio = float((passing.month_max / passing.month_min.clip(lower=0.01)).median())
        print(f"\n  DESCRIPTIVE (the point of step 1):")
        print(f"    mean f across passing cities      {passing.f_mean.mean():.3f}")
        print(f"    mean seasonal swing in f          {spread:.3f} "
              f"(median month_max/month_min = {ratio:.2f}x)")
        print(f"    mean diurnal swing in f           "
              f"{float((passing.hour_max - passing.hour_min).mean()):.3f}")
        print(f"    -> the partition {'DOES' if spread > 0.10 else 'does NOT'} move "
              f"materially within a year, so a per-year constant is "
              f"{'inadequate' if spread > 0.10 else 'defensible'}")

    if args.daily and len(est):
        print("\n  D1 — was the hourly failure NOISE or PHYSICS?")
        print("    city            n_peri   hourly    daily    change")
        for r in est.itertuples():
            h = getattr(r, "hourly_ordered", None)
            if h is None or not np.isfinite(h):
                continue
            print(f"    {r.city:<16}{r.n_peri:>5}   {100*h:6.0f}%  {100*r.pct_ordered:6.0f}%"
                  f"   {100*(r.pct_ordered-h):+6.0f}")
        sm = est[est.n_peri <= 4]; lg = est[est.n_peri > 4]
        d_sm = float((sm.pct_ordered - sm.hourly_ordered).mean()) if len(sm) else np.nan
        d_lg = float((lg.pct_ordered - lg.hourly_ordered).mean()) if len(lg) else np.nan
        print(f"    mean improvement: sparse (<=4 peri) {100*d_sm:+.0f} pts | "
              f"dense (>4) {100*d_lg:+.0f} pts")
        print(f"    -> {'NOISE dominated the hourly failure' if d_sm > d_lg + 0.02 else 'improvement is NOT concentrated in sparse networks — physics contributes'}")
        res_d1 = {"improvement_sparse": None if not np.isfinite(d_sm) else round(d_sm, 4),
                  "improvement_dense": None if not np.isfinite(d_lg) else round(d_lg, 4)}
    else:
        res_d1 = None

    res = {"gates": {"P1": int(est.P1.sum()) if len(est) else 0,
                     "P2": int(est.P2.sum()) if len(est) else 0,
                     "P3": int(est.P3.sum()) if len(est) else 0,
                     "P4_pass": bool(p4), "n_passing": int(len(passing)),
                     "n_estimable": int(len(est))},
           "per_city": R.to_dict("records"), "profiles": detail, "D1": res_d1,
           "resolution": "daily" if args.daily else "hourly",
           "verdict": ("Step 1 viable: a reference partition exists at enough cities to score "
                       "an estimator against. Proceed to step 2." if p4 else
                       "Step 1 FAILS P4: fewer than 5 cities admit a defensible reference "
                       "partition. The transfer-validation design for the partition is not "
                       "viable and the plan stops here, as registered.")}

    (OUT / f"panel_reference_partition{tag}.json").write_text(
        json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\n  VERDICT: {res['verdict']}")
    print(f"wrote panel_reference_partition{tag}.{{csv,json}}")


if __name__ == "__main__":
    main()
