"""kandy_interval_widen_fit.py -- fit the interval widening factor k at the CEA station on 2019-01 -> 2021-06, check it on
later days (2026-10-12; spec docs/diurnal_and_interval_widening_spec_2026-10-12.md, committed before this ran; F.137).

The field builders widen the spread of T's quantiles about its median before assembly,
    T05' = T50 - k (T50 - T05),  T95' = T50 + k (T95 - T50),
so each field quantile's basin mean still equals its (widened) anchor and the webapp reconstruction stays exact.
k = the smallest value (step 0.01) giving >= 90 % hourly coverage at the station cell on calibration hours. The fit reads
the UNWIDENED anchor quantiles from the T_anchor files and the cell pattern P recovered from the stored field (P does
not depend on k), so re-running it after a rebuild gives the same k.
Out: data/processed/decomp/interval_widening.json (read by build_additive_field_v2 and kandy_extension_fields)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import kandy_diurnal_cea_scenario as sc     # noqa: E402

DEC = REPO / "data" / "processed" / "decomp"
CAL_END = sc.CAL_END


def widened_cell(D, k):
    t05 = D.T_q50 - k * (D.T_q50 - D.T_q05)
    t95 = D.T_q50 + k * (D.T_q95 - D.T_q50)
    return pd.DataFrame({"q05": np.asarray(sc.split_floor(t05, D.B, D.P)),
                         "q50": np.asarray(sc.split_floor(D.T_q50, D.B, D.P)),
                         "q95": np.asarray(sc.split_floor(t95, D.B, D.P))}, index=pd.DatetimeIndex(D.tloc.to_numpy()))


def cov(j):
    lo, hi = j.q05.clip(lower=0), j.q95.clip(lower=0)
    d = j.groupby(j.index.floor("D")).agg(o=("obs", "mean"), lo=("q05", "mean"), hi=("q95", "mean"), n=("obs", "size"))
    d = d[d.n >= 18]
    return dict(n=int(len(j)), coverage=float(((j.obs >= lo) & (j.obs <= hi)).mean()),
                below=float((j.obs < lo).mean()), above=float((j.obs > hi).mean()),
                mean_width=float((hi - lo).mean()),
                daily_coverage=float(((d.o >= d.lo.clip(lower=0)) & (d.o <= d.hi.clip(lower=0))).mean()),
                days=int(len(d)))


def main():
    if "--provisional" in sys.argv:
        # k = 1 for the first rebuild only: the fit needs the rebuilt background and pattern; refit right after
        p = DEC / "interval_widening.json"
        p.write_text(json.dumps({"k": 1.0, "provisional": True}, indent=1), encoding="utf-8")
        print("wrote provisional k = 1"); return
    h = pd.read_csv(sc.CEA / "kandy_aqms_hourly.csv", parse_dates=["t_local"]).dropna(subset=["pm2_5"])
    h = h[(h.pm2_5 > 0) & (h.pm2_5 < 500)]
    obs = h.groupby(h.t_local.dt.floor("h")).pm2_5.mean().rename("obs")
    D = pd.concat([sc.load_year(y)[0] for y in sc.YEARS])
    grid = np.round(np.arange(1.0, 4.001, 0.01), 2)
    k_fit, curve = None, []
    for k in grid:
        j = widened_cell(D, k).join(obs, how="inner").dropna()
        c = cov(j[j.index < CAL_END])["coverage"]
        curve.append((float(k), c))
        if c >= 0.90:
            k_fit = float(k)
            break
    if k_fit is None:
        raise SystemExit("no k in [1, 4] reaches 90 % on calibration hours")
    out = {"spec": "docs/diurnal_and_interval_widening_spec_2026-10-12.md", "k": k_fit,
           "rule": "smallest k (step 0.01) with >= 90 % hourly coverage at the CEA station cell, calibration hours "
                   "2019-01 -> 2021-06; applied to the spread of T's quantiles about T50 before assembly"}
    for lab, k in (("unwidened", 1.0), ("widened", k_fit)):
        j = widened_cell(D, k).join(obs, how="inner").dropna()
        out[lab] = {"calibration": cov(j[j.index < CAL_END]), "held_out": cov(j[j.index >= CAL_END])}
    p = DEC / "interval_widening.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(out, indent=1), encoding="utf-8"); os.replace(tmp, p)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
