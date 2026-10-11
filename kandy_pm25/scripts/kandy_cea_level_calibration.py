"""kandy_cea_level_calibration.py -- the level factor beta fitted to the CEA Kandy station, 2019-01 .. 2021-06 only
(2026-10-11, ledger F.132). Split re-anchoring: the years 2022-10 .. 2026 are NOT used and remain a held-out check.

beta multiplies the van Donkelaar basin level that sets the annual level of T(t) and of the background
(features/vandonkelaar.py, L_corrected = beta * basin_mean). The field is linear in that level apart from two small
fixed terms (the marine background floor and the ventilated-hour floor eps0), so beta is estimated as the ratio of
the station's mean to the field-at-the-station-cell mean over the calibration days, using the field built with
beta = 1. A month-block bootstrap gives its interval. After the rebuild the residual calibration-period bias is
re-measured and reported (kandy_cea_reference_check.py), not iterated away.

  (default) fit beta from the beta=1 field (run BEFORE switching the anchor) -> stage1_v3/cea_level_beta.json
  --score  after the rebuild: held-out bias and RMSE change with intervals -> decomp/kandy_cea_split_score.json
Out: data/processed/stage1_v3/cea_level_beta.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
OUT = REPO / "data" / "processed" / "stage1_v3" / "cea_level_beta.json"
CAL0, CAL1 = pd.Timestamp("2019-01-01"), pd.Timestamp("2021-06-30")   # the first upload set (set1)
NBOOT, SEED = 4000, 20261011


def main():
    J = pd.read_csv(DEC / "kandy_cea_reference_check_daily.csv", index_col=0, parse_dates=True)
    C = J[(J.index >= CAL0) & (J.index <= CAL1)][["obs", "delivered"]].dropna()
    beta = float(C.obs.mean() / C.delivered.mean())
    rng = np.random.default_rng(SEED)
    months = C.index.to_period("M")
    groups = [C[months == m] for m in months.unique()]
    bs = []
    for _ in range(NBOOT):
        pick = [groups[i] for i in rng.integers(0, len(groups), len(groups))]
        D = pd.concat(pick)
        bs.append(D.obs.mean() / D.delivered.mean())
    lo, hi = np.percentile(bs, [2.5, 97.5])
    out = {"beta": beta, "ci95": [float(lo), float(hi)], "days": int(len(C)), "months": int(len(groups)),
           "window": [str(CAL0.date()), str(CAL1.date())], "obs_mean": float(C.obs.mean()),
           "model_mean_beta1": float(C.delivered.mean()),
           "held_out": "2022-10 .. 2026 (CEA upload sets 2-4 and the live feed)",
           "method": "ratio of means, station vs field at the station cell built with beta = 1; month-block bootstrap"}
    tmp = OUT.with_suffix(".tmp.json"); tmp.write_text(json.dumps(out, indent=2), encoding="utf-8"); os.replace(tmp, OUT)
    print(json.dumps(out, indent=1))


def score():
    """Held-out check after the rebuild: 2022-10 .. 2023 against the station, re-anchored vs satellite level; and the
    2024-2026 extension. Month-block bootstrap intervals on the bias and on the paired RMSE change."""
    J = pd.read_csv(DEC / "kandy_cea_reference_check_daily.csv", index_col=0, parse_dates=True)
    H = J[J.index > CAL1][["obs", "delivered", "satellite_level"]].dropna()
    rng = np.random.default_rng(SEED)
    months = H.index.to_period("M"); groups = [H[months == m] for m in months.unique()]

    def m(D):
        b_re = 100 * (D.delivered.mean() / D.obs.mean() - 1); b_sat = 100 * (D.satellite_level.mean() / D.obs.mean() - 1)
        r_re = np.sqrt(((D.delivered - D.obs) ** 2).mean()); r_sat = np.sqrt(((D.satellite_level - D.obs) ** 2).mean())
        return b_re, b_sat, 100 * (r_re / r_sat - 1)
    pt = m(H)
    bs = np.array([m(pd.concat([groups[i] for i in rng.integers(0, len(groups), len(groups))])) for _ in range(NBOOT)])
    ci = np.percentile(bs, [2.5, 97.5], axis=0)
    out = {"held_out_days": int(len(H)), "held_out_months": int(len(groups)),
           "bias_reanchored": [pt[0], *ci[:, 0]], "bias_satellite": [pt[1], *ci[:, 1]],
           "rmse_change_pct": [pt[2], *ci[:, 2]]}
    # Level range of the delivered annual basin means implied by beta's interval (the level now rests on beta).
    B = json.load(open(OUT, encoding="utf-8"))
    ann = {y: float(pd.read_parquet(REPO / "data" / "processed" / "stage1_v3" / "T_anchor" / f"T_kandy_hourly_{y}.parquet",
                                     columns=["T_q50"]).T_q50.mean()) for y in range(2019, 2024)}
    lo_f, hi_f = B["ci95"][0] / B["beta"], B["ci95"][1] / B["beta"]
    out["annual_means"] = ann
    out["level_range"] = {"min_lo": min(ann.values()) * lo_f, "max_hi": max(ann.values()) * hi_f,
                          "who_multiple_lo": min(ann.values()) * lo_f / 5.0}
    E = json.load(open(DEC / "kandy_cea_reference_check_ext.json", encoding="utf-8"))["delivered"]["all"]
    out["extension_2024_2026"] = {"days": E["n"], "bias_pct": E["bias_pct"], "r": E["r"]}
    p = DEC / "kandy_cea_split_score.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(out, indent=2), encoding="utf-8"); os.replace(tmp, p)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    import sys
    score() if "--score" in sys.argv else main()
