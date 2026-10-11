"""f_diurnal_amplitude_sweep.py — what actually sets the shipped local fraction f?

F.43 established that f is insensitive to F_MIN (0.477 -> 0.502 across a fourfold sweep) and
concluded the coherence constraint, not the parameter, sets f ~ 0.48. That is true, and it is
not the whole sensitivity. The cap is (1 - F_MIN) x min_hour(T), so when it binds -- and F.44
measured it binding on 49-75% of hours -- f is a function of the ANCHOR'S DIURNAL RANGE,
mean(daily-min T) / mean(T). That range is set by sharpen_T_diurnal.py mapping T onto the
observed FECT swing, so f may inherit a dependency on W5 (the unvalidated FECT calibration).

This script sweeps the quantity F.43 did not: the diurnal amplitude of T.

TWO SWEEPS, and the contrast between them is the point:

  amplitude   T -> daily_mean + a * (T - daily_mean).  Preserves every daily mean, hence the
              annual level and the T-lock, and changes ONLY the within-day swing. This is the
              shape dependency.

  level       T -> s * T.  A uniform multiplicative rescale, i.e. what a pure FECT calibration
              SLOPE error would do. Reported to test, rather than assert, whether a slope error
              moves f. Note the anchor is re-anchored per year to van Donkelaar, so a FECT
              slope error should not survive into the shipped level at all -- but B's annual
              mean comes from van Donkelaar independently of T, so the ratio is not
              automatically invariant. Measure it.

Nothing is written to any product. Usage: python scripts/f_diurnal_amplitude_sweep.py
Output: data/processed/decomp/f_diurnal_amplitude_sweep.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_additive_field_v2 as bld  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
TANCHOR = REPO / "data" / "processed" / "stage1_v3" / "T_anchor"
OUT = REPO / "data" / "processed" / "decomp" / "f_diurnal_amplitude_sweep.csv"

AMPLITUDES = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
LEVELS = [0.8, 1.0, 1.25]


def anchor(year: int) -> pd.DataFrame:
    t = pd.read_parquet(TANCHOR / f"T_kandy_hourly_{year}.parquet",
                        columns=["datetime_utc", "T_q50"])
    t["date"] = pd.to_datetime(t.datetime_utc).dt.tz_localize(None).dt.floor("D")
    return t


def rescale(t: pd.DataFrame, amp: float = 1.0, lvl: float = 1.0) -> pd.DataFrame:
    """Amplitude scaling preserves each DAILY MEAN exactly; level scaling is uniform."""
    o = t.copy()
    dm = o.groupby("date").T_q50.transform("mean")
    o["T_q50"] = (dm + amp * (o.T_q50 - dm)) * lvl
    return o[["datetime_utc", "T_q50"]]


def b_annual_for(year: int) -> float:
    vand = pd.read_csv(REPO / "data" / "processed" / "stage1_v3" /
                       "vandonkelaar_kandy_annual.csv", index_col=0)
    return (1 - bld.FRAC_LOCAL_YEAR[year]) * float(vand.loc[year, "L_corrected"])   # the level T(t) is anchored to (F.132)


def evaluate(year: int, t: pd.DataFrame, amp: float, lvl: float) -> dict:
    Tm = rescale(t, amp, lvl)
    B = bld.build_B_v2(year, b_annual_for(year), T_override=Tm)
    m = B.merge(Tm, on="datetime_utc", how="inner")
    m["d"] = pd.to_datetime(m.datetime_utc).dt.floor("D")
    dmin = m.groupby("d").T_q50.min()
    # The cap is (1 - F_MIN) x DAILY-MIN T, not (1 - F_MIN) x T at that hour. An hour is
    # cap-set when B equals that daily bound -- comparing B against the hour's own T instead
    # would only ever fire at the daily minimum hour (~1/24) and understate it ~20-fold.
    cap = (1.0 - bld.F_MIN) * m.d.map(dmin).to_numpy(float)
    return {
        "year": year, "amplitude": amp, "level": lvl,
        "mean_T": m.T_q50.mean(), "mean_B": m.B.mean(),
        "f": 1 - m.B.mean() / m.T_q50.mean(),
        "dailymin_over_mean": dmin.mean() / m.T_q50.mean(),
        "cap_set_pct": 100 * float((np.abs(m.B.to_numpy(float) - cap) < 1e-9).mean()),
    }


def main() -> None:
    rows = []
    for y in bld.YEARS:
        t = anchor(y)
        for a in AMPLITUDES:
            rows.append(evaluate(y, t, a, 1.0))
        for s in LEVELS:
            if s != 1.0:
                rows.append(evaluate(y, t, 1.0, s))
    r = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    r.to_csv(OUT, index=False)

    pd.set_option("display.width", 200, "display.max_columns", 30)

    amp = r[r.level == 1.0].pivot_table(index="amplitude", columns="year", values="f")
    amp["pooled"] = r[r.level == 1.0].groupby("amplitude").f.mean()
    print("\n=== f vs DIURNAL AMPLITUDE of the anchor (daily means preserved) ===")
    print(amp.round(4).to_string())
    base = float(amp.loc[1.0, "pooled"])
    lo, hi = float(amp.loc[0.8, "pooled"]), float(amp.loc[1.2, "pooled"])
    print(f"\npooled f at amplitude 1.00 : {base:.4f}")
    print(f"pooled f at amplitude 0.80 : {lo:.4f}   (delta {lo - base:+.4f})")
    print(f"pooled f at amplitude 1.20 : {hi:.4f}   (delta {hi - base:+.4f})")
    print(f"RANGE OF f ACROSS +/-20% AMPLITUDE: {hi - lo:.4f}")
    print("   compare F.43's F_MIN sweep, which moved f by 0.025 across a fourfold change.")

    lev = r[r.amplitude == 1.0].pivot_table(index="level", columns="year", values="f")
    lev["pooled"] = r[r.amplitude == 1.0].groupby("level").f.mean()
    print("\n=== f vs uniform LEVEL rescale (a pure calibration-slope error) ===")
    print(lev.round(4).to_string())

    print("\n=== diagnostics at amplitude 1.00 ===")
    print(r[(r.amplitude == 1.0) & (r.level == 1.0)]
          [["year", "f", "dailymin_over_mean", "cap_set_pct"]]
          .round(4).to_string(index=False))


if __name__ == "__main__":
    main()
