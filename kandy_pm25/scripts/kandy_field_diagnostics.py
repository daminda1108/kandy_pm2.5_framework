"""Diagnostics §2 and §5 quote and nothing computed  (re-run 2026-09-04)

Four quantities were literals in the manuscript. Each is cheap and each is now derived from the
shipped anchor, the shipped backgrounds and the shipped field.

  ventilated hours   how often the hourly total falls BELOW the daily background. This is the
                     fraction of hours the increment-split correction of §2.5 acts on, and the
                     fraction of hours that would render with the core CLEANER than the rural
                     edge under the uncorrected form (gotcha #57).
  pre-cap excess     how often the background exceeded the total before the coherence
                     constraint of §2.6. Read against the v1 background, which is kept on disk
                     precisely so this comparison stays possible.
  constraint sweep   whether the local fraction depends on the free parameter or on the form of
                     the constraint. The whole argument of §2.6 is that it does not.
  contrast by window the model's own p90/p10 at each averaging window, so §5.7 can compare like
                     with like. It was comparing an ANNUAL model contrast against observed
                     values taken at mixed windows.

⚠ One mismatch this script cannot remove. The observed contrasts in `support_collapse.csv` are
spreads across a city's STATIONS; the model contrast is a spread across its CELLS. Matching the
window removes the larger half of the discrepancy and the remainder is stated, not hidden.

Usage: .venv/Scripts/python.exe scripts/kandy_field_diagnostics.py
Out:   data/processed/decomp/kandy_field_diagnostics.csv
       data/processed/paper_figures/kandy_diagnostics.json
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from figdata import emit  # noqa: E402

DEC = REPO / "data" / "processed" / "decomp"
TDIR = REPO / "data" / "processed" / "stage1_v3" / "T_anchor"
YEARS = [2019, 2020, 2021, 2022, 2023]
MIDDAY = range(9, 16)          # local hours the §2.5 inversion diagnostic uses
LT = 5.5


# NB: the anchor column is renamed `tot` everywhere below. A DataFrame column named
# "T" is unreachable as `df.T` -- that is the transpose -- and the comparison then
# silently returns a transposed frame instead of a boolean mask.
def _anchor(year: int) -> pd.Series:
    t = pd.read_parquet(TDIR / f"T_kandy_hourly_{year}.parquet",
                        columns=["datetime_utc", "T_q50"])
    return t.set_index("datetime_utc").T_q50


def _bg(year: int, capped: bool) -> pd.Series:
    suffix = "_v2" if capped else ""
    b = pd.read_parquet(DEC / f"B_background_hourly_{year}{suffix}.parquet",
                        columns=["datetime_utc", "B"])
    return b.set_index("datetime_utc").B


def ventilated_and_precap() -> pd.DataFrame:
    rows = []
    for y in YEARS:
        T = _anchor(y)
        post, pre = _bg(y, True), _bg(y, False)
        j = pd.concat([T.rename("tot"), post.rename("Bpost"), pre.rename("Bpre")],
                      axis=1).dropna()
        lt_hour = (j.index + pd.Timedelta(hours=LT)).hour
        vent = j.tot < j.Bpost
        mid = np.isin(lt_hour, list(MIDDAY))
        rows.append(dict(
            year=y,
            vent_pct=100.0 * float(vent.mean()),
            vent_midday_pct=100.0 * float(vent[mid].mean()),
            precap_excess_pct=100.0 * float((j.Bpre > j.tot).mean()),
            precap_excess_midday_pct=100.0 * float((j.Bpre > j.tot)[mid].mean()),
            postcap_excess_pct=100.0 * float((j.Bpost > j.tot).mean()),
        ))
    return pd.DataFrame(rows)


def cap_fraction(f_min: float, form: str) -> float:
    """Local fraction under a given constraint form. Mirrors §2.6.

    The background may not exceed the total, and local sources emit continuously so a floor
    f_min on the local share is imposed. `form` selects how the daily reference minimum is
    taken -- the point of the sweep is that the answer barely moves between them.
    """
    fr = []
    for y in YEARS:
        T = _anchor(y)
        B = _bg(y, False)                       # start from the UNCAPPED background
        j = pd.concat([T.rename("tot"), B.rename("B")], axis=1).dropna()
        if form == "calendar":
            ref = j.tot.groupby(j.index.floor("D")).transform("min")
        elif form == "roll24":
            ref = j.tot.rolling(24, center=True, min_periods=6).min()
        elif form == "roll48":
            ref = j.tot.rolling(48, center=True, min_periods=12).min()
        else:
            raise ValueError(form)
        cap = (1.0 - f_min) * ref               # B may not exceed this
        Bc = np.minimum(j.B, cap).clip(lower=0)
        fr.append(1.0 - float(Bc.mean()) / float(j.tot.mean()))
    return float(np.mean(fr))


def contrast_by_window() -> pd.DataFrame:
    """Model p90/p10 across cells, at each averaging window support_collapse.csv uses."""
    f = pd.concat([pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}_additive_v3.parquet",
                                   columns=["time", "lat", "lon", "pm25_q50"])
                   for y in YEARS], ignore_index=True)
    f["cell"] = f.lat.astype(str) + "_" + f.lon.astype(str)
    out = []
    for name, rule in [("1h", None), ("24h", "D"), ("weekly", "W"), ("monthly", "M"),
                       ("annual", "Y")]:
        g = f if rule is None else f.assign(
            time=f.time.dt.floor("D") if rule == "D"
            else f.time.dt.to_period(rule).dt.start_time)
        cell = g.groupby(["time", "cell"]).pm25_q50.mean().unstack()
        r = cell.apply(lambda s: np.nanpercentile(s, 90) / np.nanpercentile(s, 10), axis=1)
        out.append(dict(window=name, n_steps=int(len(r)), p90_p10=float(r.median())))
    return pd.DataFrame(out)


def main() -> int:
    print("Kandy field diagnostics\n")

    v = ventilated_and_precap()
    print(v.round(2).to_string(index=False))
    vent = float(v.vent_pct.mean())
    vent_mid = float(v.vent_midday_pct.mean())
    print(f"\n  ventilated hours, all      {vent:.1f}%   (mean over {len(YEARS)} years)")
    print(f"  ventilated hours, midday   {vent_mid:.1f}%   <- the pre-fix inversion rate")
    print(f"  pre-cap B > T              {v.precap_excess_pct.min():.1f} to "
          f"{v.precap_excess_pct.max():.1f}%, mean {v.precap_excess_pct.mean():.1f}%")
    print(f"  post-cap B > T             {v.postcap_excess_pct.max():.2f}% at worst\n")

    print("  constraint sweep")
    base = cap_fraction(0.02, "calendar")
    sweep = {fm: cap_fraction(fm, "calendar") for fm in (0.0, 0.02, 0.04, 0.08)}
    for fm, val in sweep.items():
        print(f"    f_min {fm:.2f}   f = {val:.3f}")
    forms = {k: cap_fraction(0.02, k) for k in ("calendar", "roll24", "roll48")}
    for k, val in forms.items():
        print(f"    form {k:<9} f = {val:.3f}")

    w = contrast_by_window()
    print("\n  model contrast by window")
    print(w.round(3).to_string(index=False))

    v.to_csv(DEC / "kandy_field_diagnostics.csv", index=False)
    w.to_csv(DEC / "kandy_contrast_by_window.csv", index=False)

    emit("kandy_diagnostics",
         ventilated_pct=round(vent, 1),
         ventilated_midday_pct=round(vent_mid, 1),
         precap_excess_lo=round(float(v.precap_excess_pct.min()), 1),
         precap_excess_hi=round(float(v.precap_excess_pct.max()), 1),
         precap_excess_mean=round(float(v.precap_excess_pct.mean()), 1),
         precap_excess_midday=round(float(v.precap_excess_midday_pct.mean()), 1),
         postcap_excess_max=round(float(v.postcap_excess_pct.max()), 2),
         f_sweep_lo=round(min(sweep.values()), 3),
         f_sweep_hi=round(max(sweep.values()), 3),
         f_sweep_param_hi=max(sweep),
         f_form_calendar=round(forms["calendar"], 3),
         f_form_roll24=round(forms["roll24"], 3),
         f_form_roll48=round(forms["roll48"], 3),
         contrast_monthly=round(float(w[w.window == "monthly"].p90_p10.iloc[0]), 3),
         contrast_annual=round(float(w[w.window == "annual"].p90_p10.iloc[0]), 3),
         contrast_hourly=round(float(w[w.window == "1h"].p90_p10.iloc[0]), 3))
    _ = base
    return 0


if __name__ == "__main__":
    sys.exit(main())
