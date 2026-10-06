"""kandy_f_sensitivity.py -- review steps K-a and K-c (docs/review_remediation_plan_2026-10-06.md).
EXPLORATORY sensitivity of the local fraction f to how the coherence cap is computed. Production is not
changed; the production builder is imported and run with an override that disables the cap, and the cap is
then re-applied here in several forms.

The cap is B(h) <= (1 - F_MIN) * min over the day of T(h). Two choices the review questioned:
  K-a  the "day" is the UTC day (05:30 - 05:29 local), splitting the night;
  K-c  the minimum of 24 hourly model values is an extreme-value statistic, biased low by model noise.
Variants: day = UTC | local (Asia/Colombo); statistic = min | 2nd-lowest hour | 10th percentile |
min of a 3-hour running mean. f = 1 - mean(B_capped) / mean(T), per year 2019-2023.
Parity: the UTC/min variant must reproduce the stored production background (B_background_hourly_{y}_v2).
Out: data/processed/decomp/f_sensitivity.csv
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import build_additive_field_v2 as bv   # noqa: E402

OUT = REPO / "data" / "processed" / "decomp" / "f_sensitivity.csv"


def stat(name):
    return {"min": lambda s: s.min(),
            "second": lambda s: np.sort(s.to_numpy())[1] if len(s) > 1 else s.min(),
            "p10": lambda s: s.quantile(0.10),
            "min_roll3": None}[name]


def main():
    vand = pd.read_csv(REPO / "data" / "processed" / "stage1_v3" / "vandonkelaar_kandy_annual.csv").set_index("year")
    rows = []
    for y in range(2019, 2024):
        T = pd.read_parquet(bv.TANCHOR / f"T_kandy_hourly_{y}.parquet", columns=["datetime_utc", "T_q50"])
        b_annual = (1 - bv.FRAC_LOCAL_YEAR[y]) * float(vand.loc[y, "basin_mean"])
        big = T.copy(); big["T_q50"] = 1e9
        Bu = bv.build_B_v2(y, b_annual, T_override=big).B.to_numpy()          # cap disabled
        ts = pd.to_datetime(T.datetime_utc)
        ts = ts.dt.tz_localize("UTC") if ts.dt.tz is None else ts.dt.tz_convert("UTC")
        days = {"utc": ts.dt.tz_localize(None).dt.floor("D"),
                "local": ts.dt.tz_convert("Asia/Colombo").dt.tz_localize(None).dt.floor("D")}
        t = T.T_q50.reset_index(drop=True)
        tmean = float(t.mean())
        stored = pd.read_parquet(bv.DEC / f"B_background_hourly_{y}_v2.parquet").B.to_numpy()
        for dname, dd in days.items():
            dd = dd.reset_index(drop=True)
            for sname in ("min", "second", "p10", "min_roll3"):
                if sname == "min_roll3":
                    sm = t.rolling(3, center=True, min_periods=1).mean()
                    m = sm.groupby(dd).transform("min")
                else:
                    m = t.groupby(dd).transform(stat(sname))
                cap = (1 - bv.F_MIN) * m.to_numpy()
                B = np.minimum(Bu, cap)
                rec = dict(year=y, day=dname, stat=sname, f=1 - B.mean() / tmean,
                           capped_share=float((Bu > cap).mean()))
                if dname == "utc" and sname == "min":
                    rec["parity_max_abs_vs_stored_B"] = float(np.max(np.abs(B - stored)))
                rows.append(rec)
        print(f"  {y} done", flush=True)
    d = pd.DataFrame(rows)
    tmp = OUT.with_suffix(".tmp.csv"); d.to_csv(tmp, index=False); os.replace(tmp, OUT)
    print(d.pivot_table(index=["day", "stat"], columns="year", values="f").round(3).assign(
        mean=lambda x: x.mean(axis=1).round(3)).to_string())
    print("parity:", d.parity_max_abs_vs_stored_B.dropna().max())
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
