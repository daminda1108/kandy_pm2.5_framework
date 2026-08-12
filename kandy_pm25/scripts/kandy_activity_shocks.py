"""kandy_activity_shocks.py — do the 2020 lockdown and the 2021-22 fuel crisis constrain
the local share? (2026-08-07)

PRE-REGISTERED: `docs/prereg_activity_shocks_2026-08-07.md`. Predictions S1-S5, falsifiers
and the author's prior were fixed before any number here was computed.

THE IDEA
--------
The holiday instrument (F.22/F.23/F.29) works because a public holiday removes local
activity while leaving transboundary transport untouched. Holidays are one-day shocks. Two
much larger, longer shocks sit unexploited in the same record: the 2020 COVID lockdown and
the 2021-22 fuel crisis. The shipped model already ASSUMES these matter -- FRAC_LOCAL_YEAR
is hand-lowered for 2020-2022 on exactly this reasoning, described in the manuscript as
"reasoned rather than fitted". This asks whether the data support the reasoning.

ESTIMATOR
---------
Identical to F.22: difference each hour against its own (month x hour x ventilation
quintile) cell mean, so meteorology and season are controlled non-parametrically.
Ventilation comes from model drivers only. Controls are the SAME CALENDAR WEEKS in non-shock
years, so the comparison is within season by construction. Ordinary working days only:
holidays and Sundays are excluded from both sides so the instruments cannot contaminate
each other.

REGISTERED CAVEAT
-----------------
2020 lockdowns across India suppressed TRANSBOUNDARY transport too, so unlike a Poya day the
lockdown does not cleanly isolate local activity. Its implied f is reported as an UPPER
BOUND regardless of the value.

Run:  .venv/Scripts/python.exe scripts/kandy_activity_shocks.py
Out:  data/processed/decomp/kandy_activity_shocks.{csv,json}
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
STG = REPO / "data" / "processed" / "stage1_v3"
DEC = REPO / "data" / "processed" / "decomp"
TZ_H = 5.5
NBOOT, SEED = 4000, 20260807

SHOCKS = {
    "COVID lockdown": (dt.date(2020, 3, 20), dt.date(2020, 5, 11), (0.60, 0.80)),
    "fuel crisis (peak)": (dt.date(2022, 3, 1), dt.date(2022, 9, 30), (0.25, 0.50)),
    "fuel crisis (full)": (dt.date(2021, 11, 1), dt.date(2022, 9, 30), (0.20, 0.40)),
}
CONTROL_YEARS = [2019, 2023]
FIXED_HOL = [(1, 15), (2, 4), (4, 13), (4, 14), (5, 1), (12, 25)]


def poya_dates(y0: int, y1: int) -> set:
    import ephem
    out, d = set(), ephem.Date(f"{y0}/1/1")
    end = ephem.Date(f"{y1 + 1}/1/1")
    while d < end:
        d = ephem.next_full_moon(d)
        out.add((pd.Timestamp(ephem.Date(d).datetime(), tz="UTC")
                 + pd.Timedelta(hours=TZ_H)).date())
    return out


def load() -> pd.DataFrame:
    cols = ["datetime_utc", "pm25_observed", "blh_m"]
    d0 = pd.read_parquet(STG / "dataset_v3_hourly.parquet")
    if "ws_ms" in d0.columns:
        cols.append("ws_ms")
    d = d0[cols].copy()
    d["t"] = pd.to_datetime(d.datetime_utc, utc=True)
    lt = d.t + pd.Timedelta(hours=TZ_H)
    d["hr"], d["mon"], d["date"] = lt.dt.hour, lt.dt.month, lt.dt.date
    d["doy"], d["dow"], d["year"] = lt.dt.dayofyear, lt.dt.dayofweek, lt.dt.year
    d = d.dropna(subset=["pm25_observed", "blh_m"])
    vent = d.blh_m * (d.ws_ms if "ws_ms" in d.columns else 1.0)
    d["vq"] = pd.qcut(vent, 5, labels=False, duplicates="drop")
    return d


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== PRE-REGISTERED activity-shock experiments ===")
    print("    gates: docs/prereg_activity_shocks_2026-08-07.md")
    print("    prior: S1-S3 hold; S4 least confident (lockdown f likely too HIGH)\n")
    d = load()
    y0, y1 = int(d.year.min()), int(d.year.max())
    poya = poya_dates(y0, y1)
    fixed = {dt.date(y, m, dd) for y in range(y0, y1 + 1) for m, dd in FIXED_HOL}
    d = d[~d.date.isin(poya | fixed) & (d.dow < 6)].copy()   # ordinary working days only

    cell = d.groupby(["mon", "hr", "vq"]).pm25_observed.transform("mean")
    n_cell = d.groupby(["mon", "hr", "vq"]).pm25_observed.transform("size")
    d = d[n_cell >= 10].copy()
    d["resid"] = d.pm25_observed - cell[d.index]
    lvl = float(d.pm25_observed.mean())
    print(f"  {len(d):,} working-day sensor-hours {y0}-{y1}; mean {lvl:.2f} ug/m3\n")

    rng = np.random.default_rng(SEED)
    rows = []
    for label, (a, b, drop) in SHOCKS.items():
        doy_a, doy_b = a.timetuple().tm_yday, b.timetuple().tm_yday
        span_years = sorted({a.year, b.year})
        tr = d[(d.date >= a) & (d.date <= b)]
        # control: SAME calendar window in non-shock years
        if doy_a <= doy_b:
            win = (d.doy >= doy_a) & (d.doy <= doy_b)
        else:
            win = (d.doy >= doy_a) | (d.doy <= doy_b)
        ct = d[win & d.year.isin(CONTROL_YEARS)]
        if len(tr) < 50 or len(ct) < 50:
            print(f"  {label:<22} insufficient data (treat {len(tr)}, ctrl {len(ct)})")
            continue
        eff = float(tr.resid.mean() - ct.resid.mean())
        pct = 100.0 * eff / lvl
        bs = np.array([rng.choice(tr.resid.to_numpy(), len(tr)).mean()
                       - rng.choice(ct.resid.to_numpy(), len(ct)).mean()
                       for _ in range(NBOOT)])
        lo, hi = np.percentile(bs, [5, 95])
        p = float(2 * min((bs >= 0).mean(), (bs <= 0).mean()))
        f_rng = [round(abs(eff) / lvl / drop[1], 3), round(abs(eff) / lvl / drop[0], 3)]
        rows.append(dict(shock=label, years=str(span_years), n_treat=len(tr),
                         n_ctrl=len(ct), effect_ug=round(eff, 3), effect_pct=round(pct, 2),
                         ci90_ug=[round(float(lo), 3), round(float(hi), 3)], p=round(p, 5),
                         assumed_activity_drop=list(drop), implied_f=f_rng))
        print(f"  {label:<22} n={len(tr):>5}  effect {eff:+6.3f} ug/m3 ({pct:+6.2f}%)  "
              f"90% CI [{lo:+.2f}, {hi:+.2f}]  p={p:.4f}  implied f {f_rng}")

    R = pd.DataFrame(rows)
    R.to_csv(DEC / "kandy_activity_shocks.csv", index=False)

    print("\n" + "=" * 66 + "\n  PRE-REGISTERED PREDICTIONS\n" + "=" * 66)
    g = {r["shock"]: r for r in rows}
    lock = g.get("COVID lockdown"); fuel = g.get("fuel crisis (peak)")
    HOL_FIXED, SUNDAY = -15.63, -7.77
    s1 = bool(lock and lock["effect_pct"] < 0 and abs(lock["effect_pct"]) > abs(HOL_FIXED))
    print(f"  S1  lockdown negative and > |{HOL_FIXED}%| : "
          f"{lock['effect_pct'] if lock else 'n/a'}%   -> {'PASS' if s1 else 'FAIL'}")
    s2 = bool(fuel and fuel["effect_pct"] < 0
              and abs(SUNDAY) < abs(fuel["effect_pct"]) < abs(lock["effect_pct"] if lock else 1e9))
    print(f"  S2  fuel crisis intermediate            : "
          f"{fuel['effect_pct'] if fuel else 'n/a'}%   -> {'PASS' if s2 else 'FAIL'}")
    s3 = bool(lock and fuel and abs(SUNDAY) < abs(fuel["effect_pct"]) < abs(lock["effect_pct"]))
    print(f"  S3  ordering Sunday < fuel < lockdown   -> {'PASS' if s3 else 'FAIL'}")
    band = (0.258, 0.525)
    s4 = bool(lock and not (lock["implied_f"][1] < band[0] or lock["implied_f"][0] > band[1]))
    print(f"  S4  implied f overlaps [0.26, 0.53]     : "
          f"{lock['implied_f'] if lock else 'n/a'}   -> {'PASS' if s4 else 'FAIL'}")
    print(f"  S5  supports hand-lowering f in 2020-22 : reported, no threshold")

    npass = sum([s1, s2, s3, s4])
    res = {"level_ugm3": round(lvl, 3), "shocks": rows,
           "predictions": {"S1": s1, "S2": s2, "S3": s3, "S4": s4},
           "reference_effects": {"sunday_pct": SUNDAY, "fixed_holiday_pct": HOL_FIXED},
           "registered_caveat": (
               "2020 lockdowns across India suppressed TRANSBOUNDARY transport as well, so "
               "the lockdown does not cleanly isolate local activity the way a Poya day "
               "does. Its implied f is an UPPER BOUND."),
           "prior": "S1-S3 expected to hold; S4 least confident, lockdown f expected too high"}
    res["verdict"] = (
        (f"{npass}/4 met. The shock instruments corroborate the holiday result and the "
         f"hand-lowered f for 2020-2022 has observational support."
         if npass >= 3 else
         f"{npass}/4 met. The shocks do NOT reproduce the holiday instrument's structure; "
         f"the holiday-based line of evidence for f must be reported as weaker, not "
         f"defended.")
        + " Lockdown-implied f is an upper bound by the registered caveat.")
    print(f"\n  VERDICT: {res['verdict']}")
    (DEC / "kandy_activity_shocks.json").write_text(json.dumps(res, indent=1, default=float),
                                                    encoding="utf-8")
    print("\nwrote kandy_activity_shocks.{csv,json}")


if __name__ == "__main__":
    main()
