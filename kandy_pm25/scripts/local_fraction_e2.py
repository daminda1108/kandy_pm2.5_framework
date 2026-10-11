"""local_fraction_e2.py -- E2 of the local-fraction study: combustion-tracer intercept at the CEA Kandy AAQMS, 2019-2023
(spec docs/local_fraction_study_spec_2026-10-11.md, committed before this script ran; ledger F.134).

Per calendar month with >= 300 hours of PM2.5 and tracer: Theil-Sen PM2.5 ~ tracer; background
PM_bg = intercept + slope * tracer_bg (tracer_bg = the month's p-th percentile), floored at 0;
f_E2 = 1 - sum(PM_bg * n) / sum(PM). Tracer CO (primary) or NO2; p = 5 (primary) or 10.
Model on the same hours: f_model_cell = 1 - <B>/<PM_cell>, f_model_basin = 1 - <B>/<T>.
Out: data/processed/decomp/local_fraction_e2.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
TAN = REPO / "data" / "processed" / "stage1_v3" / "T_anchor"
CEA = REPO / "data" / "external" / "cea"
SLAT, SLON = 7.2906, 80.6337
TZ = "Asia/Colombo"
YEARS = range(2019, 2024)
MIN_H = 300


def model_hourly():
    cell, B, T = [], [], []
    for y in YEARS:
        f = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}_additive_v3.parquet", columns=["time", "lat", "lon", "pm25_q50"])
        lats, lons = np.sort(f.lat.unique()), np.sort(f.lon.unique())
        plat, plon = lats[np.abs(lats - SLAT).argmin()], lons[np.abs(lons - SLON).argmin()]
        c = f[(f.lat == plat) & (f.lon == plon)]
        cell.append(pd.Series(c.pm25_q50.to_numpy(), index=pd.to_datetime(c.time, utc=True)))
        b = pd.read_parquet(DEC / f"B_background_hourly_{y}_v2.parquet", columns=["datetime_utc", "B"])
        B.append(pd.Series(b.B.to_numpy(), index=pd.to_datetime(b.datetime_utc, utc=True)))
        t = pd.read_parquet(TAN / f"T_kandy_hourly_{y}.parquet", columns=["datetime_utc", "T_q50"])
        T.append(pd.Series(t.T_q50.to_numpy(), index=pd.to_datetime(t.datetime_utc, utc=True)))
    M = pd.DataFrame({"cell": pd.concat(cell), "B": pd.concat(B), "T": pd.concat(T)})
    M.index = M.index.tz_convert(TZ).tz_localize(None).floor("h")
    return M[~M.index.duplicated()]


def e2(h, tracer, pct):
    rows, bg_sum, pm_sum = [], 0.0, 0.0
    for per, g in h.dropna(subset=["pm2_5", tracer]).groupby(h.t_local.dt.to_period("M")):
        if len(g) < MIN_H:
            continue
        slope, icpt, _, _ = theilslopes(g.pm2_5.to_numpy(float), g[tracer].to_numpy(float))
        tb = float(np.percentile(g[tracer], pct))
        pmbg = max(0.0, icpt + slope * tb)
        rows.append(dict(month=str(per), n=len(g), slope=slope, intercept=icpt, tracer_bg=tb, pm_bg=pmbg,
                         pm_mean=float(g.pm2_5.mean()), f_month=1 - pmbg / float(g.pm2_5.mean())))
        bg_sum += pmbg * len(g); pm_sum += float(g.pm2_5.sum())
    return dict(tracer=tracer, pct=pct, months=len(rows), hours=int(sum(r["n"] for r in rows)),
                f=1 - bg_sum / pm_sum if pm_sum else None, per_month=rows)


def main():
    h = pd.read_csv(CEA / "kandy_aqms_hourly.csv", parse_dates=["t_local"])
    h = h[(h.t_local.dt.year >= 2019) & (h.t_local.dt.year <= 2023)].copy()
    out = {"spec": "docs/local_fraction_study_spec_2026-10-11.md"}
    for tracer in ("co", "no2"):
        for pct in (5, 10):
            out[f"{tracer}_p{pct}"] = e2(h, tracer, pct)
    # model on the hours used by the primary arm
    M = model_hourly()
    used = set(r["month"] for r in out["co_p5"]["per_month"])
    hh = h.dropna(subset=["pm2_5", "co"])
    hh = hh[hh.t_local.dt.to_period("M").astype(str).isin(used)]
    J = M.reindex(hh.t_local.dt.floor("h")).dropna()
    out["model_same_hours"] = dict(hours=int(len(J)), f_model_cell=float(1 - J.B.mean() / J.cell.mean()),
                                   f_model_basin=float(1 - J.B.mean() / J["T"].mean()),
                                   obs_mean=float(hh.pm2_5.mean()), model_cell_mean=float(J.cell.mean()))
    p = DEC / "local_fraction_e2.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(out, indent=1), encoding="utf-8"); os.replace(tmp, p)
    for k in ("co_p5", "co_p10", "no2_p5", "no2_p10"):
        print(k, out[k]["months"], "months", round(out[k]["f"], 3))
    print("model same hours:", {k: round(v, 3) for k, v in out["model_same_hours"].items()})


if __name__ == "__main__":
    main()
