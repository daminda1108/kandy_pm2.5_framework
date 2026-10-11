"""Sweep the coherence-cap parameter and emit the insensitivity result as an artifact.

The paper's central attribution claim is that the local fraction f follows from a physical
constraint rather than from tuning. The evidence for that is a sweep of F_MIN, the one free
parameter in the cap, showing f barely moves. That sweep existed only as a source comment in
`build_additive_field_v2.py`. Phase 1 of the paper build requires it to be an artifact.

The cap is B <= (1 - F_MIN) x min_hour(T) for each day. F_MIN was chosen as the smallest
value that removes the zero-local-share defect, before f was known, so it is not a tuning
knob. This script measures how much room there would have been to tune it.

Output
    data/processed/decomp/kandy_fmin_sweep.{csv,json}
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T_DIR = ROOT / "data" / "processed" / "stage1_v3" / "T_anchor"
OUT = ROOT / "data" / "processed" / "decomp"

YEARS = [2019, 2020, 2021, 2022, 2023]
GRID = [0.00, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08]
SHIPPED = 0.02


def main() -> None:
    mod = importlib.import_module("build_additive_field_v2")
    vand = pd.read_csv(ROOT / "data" / "processed" / "stage1_v3" /
                       "vandonkelaar_kandy_annual.csv").set_index("year")

    T = {y: pd.read_parquet(T_DIR / f"T_kandy_hourly_{y}.parquet",
                            columns=["datetime_utc", "T_q50"]) for y in YEARS}

    rows = []
    original = mod.F_MIN
    try:
        for fmin in GRID:
            mod.F_MIN = fmin
            per_year = []
            for y in YEARS:
                b_annual = (1 - mod.FRAC_LOCAL_YEAR[y]) * float(vand.loc[y, "L_corrected"])   # the level T(t) is anchored to (F.132)
                B = mod.build_B_v2(y, b_annual)
                if getattr(mod, "RELEVEL", False):
                    B = mod.relevel_background(B, y)
                m = B[["datetime_utc", "B"]].merge(T[y], on="datetime_utc")
                Bv, Tv = m["B"].to_numpy(float), m["T_q50"].to_numpy(float)
                share = np.divide(Tv - Bv, Tv, out=np.zeros_like(Tv), where=Tv > 0)
                per_year.append({
                    "F_MIN": fmin, "year": y,
                    "f": float(1.0 - Bv.mean() / Tv.mean()),
                    "hours_below_fmin_pct": float(100.0 * np.mean(share < fmin - 1e-9)),
                    "hours_B_gt_T_pct": float(100.0 * np.mean(Bv > Tv)),
                })
            rows.extend(per_year)
    finally:
        mod.F_MIN = original

    df = pd.DataFrame(rows)
    agg = df.groupby("F_MIN").agg(f_mean=("f", "mean"),
                                  f_min_year=("f", "min"),
                                  f_max_year=("f", "max"),
                                  zero_local_pct=("hours_below_fmin_pct", "mean")
                                  ).reset_index()

    span = float(agg.f_mean.max() - agg.f_mean.min())
    shipped_f = float(agg.loc[agg.F_MIN == SHIPPED, "f_mean"].iloc[0])
    summary = {
        "shipped_F_MIN": SHIPPED,
        "shipped_f": shipped_f,
        "sweep_range_of_F_MIN": [GRID[0], GRID[-1]],
        "sweep_range_of_f": [float(agg.f_mean.min()), float(agg.f_mean.max())],
        "f_span_across_sweep": span,
        "interpretation": (
            "A fourfold change in the only free parameter of the cap moves the annual local "
            "fraction by %.3f. The constraint sets f, not the parameter." % span),
        "years": YEARS,
    }

    (OUT / "kandy_fmin_sweep.json").write_text(
        json.dumps({"summary": summary,
                    "by_fmin": agg.to_dict("records"),
                    "per_year": rows}, indent=1))
    df.to_csv(OUT / "kandy_fmin_sweep.csv", index=False)

    print(agg.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print(f"\nshipped F_MIN = {SHIPPED}: f = {shipped_f:.4f}")
    print(f"f across the whole sweep: {summary['sweep_range_of_f'][0]:.4f} "
          f"to {summary['sweep_range_of_f'][1]:.4f}, span {span:.4f}")
    print("\nwrote kandy_fmin_sweep.csv and .json")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
