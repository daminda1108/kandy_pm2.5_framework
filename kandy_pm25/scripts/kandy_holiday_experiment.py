"""kandy_holiday_experiment.py — measure the locally generated share of Kandy's
PM2.5 from public-holiday natural experiments (2026-08-06).

WHY THIS EXISTS
---------------
The local/regional split is the weakest number in the model. It is currently an
assumption, and four indirect lines (SBI corrected for attenuation 0.392, the coherence
floor 0.410, the NBRO regional floor 0.446, the literature bracket) converge near 0.40,
while a meteorology-controlled SUNDAY test implies only 0.14-0.23. That conflict needs a
cleaner instrument than the weekend.

Sri Lanka provides one. **Poya days** are monthly full-moon public holidays: business and
much traffic stop, and — crucially — they fall on a DIFFERENT DAY OF THE WEEK each month,
because they track the lunar cycle rather than the calendar week. That breaks the
confound that limits the weekend test: a holiday effect can be identified while day of
week is held fixed. Transboundary transport is indifferent to Sri Lankan holidays, so any
PM drop is local by construction.

The **Sinhala/Tamil New Year** (13-14 April) is a second, much stronger instrument: a
multi-day national shutdown with large-scale movement out of cities.

DESIGN
------
Outcome: FECT hourly PM2.5. Control for meteorology and season non-parametrically by
differencing each observation against the mean of its (month x hour x ventilation
quintile) cell, where ventilation = BLH x wind speed. Day of week enters as a covariate,
so the holiday effect is identified WITHIN day-of-week rather than across it.

    resid = PM - mean(PM | month, hour, ventilation quintile)
    resid ~ holiday + day_of_week

Reported as a percentage of the mean level, and converted to an implied local share
under a stated assumption about how much activity a holiday removes. That assumption is
the weakest link and is reported as a range, never as a point.

WHAT IT CAN AND CANNOT SHOW
---------------------------
CAN: a lower bound on the share of PM2.5 that is locally generated AND responds to human
activity on a 1-day timescale.

CANNOT: the total local share. Sources with no holiday cycle — domestic cooking, waste
burning, road-dust resuspension, and any local source that runs at the weekend — are
invisible to this design and fall on the regional side of the estimate by default. A
result well below the four converging lines is therefore evidence that the local burden
is NOT predominantly traffic, not necessarily that the lines are wrong.

Poya dates are computed from the astronomical full moon in Sri Lanka local time via
`ephem`. The gazetted holiday is the full-moon calendar day; where the gazette differs by
a day the effect is diluted, not biased, so this is conservative.

Run:  .venv/Scripts/python.exe scripts/kandy_holiday_experiment.py
Out:  data/processed/decomp/kandy_holiday_experiment.{csv,json}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import ephem
import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
STG = REPO / "data" / "processed" / "stage1_v3"
DEC = REPO / "data" / "processed" / "decomp"
OUT_CSV = DEC / "kandy_holiday_experiment.csv"
OUT_JSON = DEC / "kandy_holiday_experiment.json"

TZ_H = 5.5                    # Asia/Colombo
N_VENT = 5                    # ventilation quintiles
ACTIVITY_DROP = (0.30, 0.50)  # assumed reduction in local activity on a holiday


def poya_days(y0: int, y1: int) -> set:
    """Full-moon calendar days in Sri Lanka local time = Poya public holidays."""
    out, d = set(), ephem.Date(f"{y0}/01/01")
    end = ephem.Date(f"{y1}/12/31")
    while d < end:
        d = ephem.next_full_moon(d)
        utc = d.datetime()
        out.add((utc + pd.Timedelta(hours=TZ_H)).date())
    return out


def fixed_holidays(y0: int, y1: int) -> dict:
    """Fixed-date Sri Lankan public holidays, by category."""
    ny, other = set(), set()
    for y in range(y0, y1 + 1):
        ny.add(pd.Timestamp(f"{y}-04-13").date())
        ny.add(pd.Timestamp(f"{y}-04-14").date())
        for md in ("02-04", "05-01", "12-25"):
            other.add(pd.Timestamp(f"{y}-{md}").date())
    return {"newyear": ny, "other_fixed": other}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== Kandy holiday natural experiment ===")
    d = pd.read_parquet(STG / "dataset_v3_hourly.parquet")
    d["t"] = pd.to_datetime(d.datetime_utc, utc=True)
    lt = d.t + pd.Timedelta(hours=TZ_H)
    d["date"] = lt.dt.date
    d["dow"] = lt.dt.dayofweek
    d["hr"] = lt.dt.hour
    d["mo"] = lt.dt.month
    d["yr"] = lt.dt.year
    d = d.dropna(subset=["pm25_observed", "blh_m", "wind_speed_10m"])
    y0, y1 = int(d.yr.min()), int(d.yr.max())
    print(f"  {len(d):,} sensor-hours, {y0}-{y1}, mean {d.pm25_observed.mean():.2f} ug/m3")

    poya = poya_days(y0, y1)
    fixed = fixed_holidays(y0, y1)
    d["poya"] = d.date.isin(poya)
    d["newyear"] = d.date.isin(fixed["newyear"])
    d["other_hol"] = d.date.isin(fixed["other_fixed"])
    d["sunday"] = d.dow == 6
    print(f"  Poya days in range: {len(poya)}; observed on {d.poya.sum():,} sensor-hours "
          f"({d[d.poya].date.nunique()} distinct days)")
    dowmix = d[d.poya].groupby(d[d.poya].dow).date.nunique()
    print(f"  Poya day-of-week spread: {dict(dowmix)}  <- the point: not one weekday")

    # ── meteorology + season control ─────────────────────────────────────────
    d["vent"] = pd.qcut(d.blh_m * d.wind_speed_10m.clip(lower=0.05),
                        N_VENT, labels=False, duplicates="drop")
    d["cell"] = d.mo.astype(str) + "_" + d.hr.astype(str) + "_" + d.vent.astype(str)
    cell_mean = d.groupby("cell").pm25_observed.transform("mean")
    cell_n = d.groupby("cell").pm25_observed.transform("size")
    d = d[cell_n >= 10].copy()
    d["resid"] = d.pm25_observed - cell_mean[d.index]
    lvl = float(d.pm25_observed.mean())
    print(f"  after control cells (month x hour x ventilation, n>=10): {len(d):,} hours")

    def effect(mask, label, ctrl=None):
        a = d.loc[mask, "resid"].dropna()
        b = d.loc[~mask if ctrl is None else ctrl, "resid"].dropna()
        if len(a) < 30 or len(b) < 30:
            return None
        t, p = stats.ttest_ind(a, b, equal_var=False)
        diff = float(a.mean() - b.mean())
        return {"label": label, "n_treat": int(len(a)), "n_ctrl": int(len(b)),
                "effect_ug": round(diff, 3), "effect_pct": round(100 * diff / lvl, 2),
                "p": float(p)}

    rows = []
    workday = ~(d.poya | d.newyear | d.other_hol | d.sunday)
    for mask, label in [(d.poya, "Poya (lunar public holiday)"),
                        (d.newyear, "Sinhala/Tamil New Year (13-14 Apr)"),
                        (d.other_hol, "other fixed public holidays"),
                        (d.sunday, "Sunday")]:
        r = effect(mask, label, ctrl=workday)
        if r:
            rows.append(r)

    # Poya identified WITHIN day-of-week: compare each Poya hour against ordinary
    # days sharing its weekday. This is what the weekend test cannot do.
    parts = []
    for dow in range(7):
        m = (d.dow == dow)
        a = d.loc[m & d.poya, "resid"].dropna()
        b = d.loc[m & workday, "resid"].dropna()
        if len(a) >= 30 and len(b) >= 30:
            parts.append((len(a), a.mean() - b.mean()))
    if parts:
        w = np.array([p[0] for p in parts], float)
        v = np.array([p[1] for p in parts], float)
        within = float((w * v).sum() / w.sum())
        rows.append({"label": "Poya, WITHIN day-of-week (weighted)",
                     "n_treat": int(w.sum()), "n_ctrl": -1,
                     "effect_ug": round(within, 3),
                     "effect_pct": round(100 * within / lvl, 2), "p": np.nan})

    print("\n  effect on PM2.5 vs ordinary working days (meteorology-controlled)")
    print("    " + f"{'instrument':<38}{'n':>7}{'ug/m3':>9}{'%':>8}{'p':>10}")
    for r in rows:
        pp = "  n/a" if not np.isfinite(r["p"]) else f"{r['p']:.2e}"
        print(f"    {r['label']:<38}{r['n_treat']:>7}{r['effect_ug']:>9.3f}"
              f"{r['effect_pct']:>8.2f}{pp:>10}")

    # ── implied local share ──────────────────────────────────────────────────
    print(f"\n  IMPLIED locally generated, activity-responsive share")
    print(f"    (holiday removes {ACTIVITY_DROP[0]:.0%}-{ACTIVITY_DROP[1]:.0%} of local activity)")
    implied = {}
    for r in rows:
        if r["effect_ug"] >= 0:
            continue
        rng = [abs(r["effect_pct"]) / 100 / ACTIVITY_DROP[1],
               abs(r["effect_pct"]) / 100 / ACTIVITY_DROP[0]]
        implied[r["label"]] = [round(rng[0], 3), round(rng[1], 3)]
        print(f"    {r['label']:<38} f = {rng[0]:.3f} to {rng[1]:.3f}")

    print("\n  CONTEXT — the other lines on f")
    for k, v in [("hierarchical, SBI attenuation-corrected", 0.392),
                 ("coherence floor (shipped anchor alone)", 0.410),
                 ("NBRO island network, wet season", 0.446),
                 ("shipped prior FRAC_LOCAL_YEAR", 0.244)]:
        print(f"    {k:<42} {v:.3f}")

    res = {"level_ugm3": round(lvl, 3), "n_hours": int(len(d)),
           "n_poya_days": int(d[d.poya].date.nunique()),
           "poya_dow_spread": {int(k): int(v) for k, v in dowmix.items()},
           "effects": rows, "implied_f": implied,
           "activity_drop_assumed": list(ACTIVITY_DROP),
           "interpretation": (
               "This bounds the share that is locally generated AND responds to human "
               "activity within a day. Sources with no holiday cycle -- domestic cooking, "
               "waste burning, road dust -- are invisible here and are absorbed into the "
               "regional side. A result well below the converging lines near 0.40 is "
               "therefore evidence that the local burden is not predominantly traffic, "
               "which would contradict the ~90% vehicular assumption used for e(t) and "
               "the traffic-centrality emission surface."),
           "caveats": [
               "FECT point sensors (Akurana ~460 m, Hantana ridge ~738 m), not the basin mean.",
               "The activity-drop assumption is unverified for Kandy and dominates the "
               "conversion; the effect size itself is assumption-free.",
               "Poya dates are astronomical full moons in local time; a gazette mismatch "
               "of one day dilutes the effect rather than biasing it.",
               "Control cells are month x hour x ventilation quintile, not a full "
               "meteorological model."]}
    OUT_JSON.write_text(json.dumps(res, indent=1), encoding="utf-8")
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)
    print(f"\nwrote {OUT_JSON.name} + {OUT_CSV.name}")


if __name__ == "__main__":
    main()
