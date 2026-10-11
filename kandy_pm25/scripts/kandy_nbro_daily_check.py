"""kandy_nbro_daily_check.py -- the delivered field against the NBRO Kandy daily PM2.5 record, 2021-2022
(2026-10-11, ledger F.128). EXPLORATORY; the first day-to-day test at Kandy against a record the model never saw.

Observed: daily PM2.5 at the NBRO Kandy station, digitised from Nirmani et al. (2025) Figure 3
(scripts/digitize_nirmani_kandy.py; digitised annual means within +4 / -2 per cent of the published ones).
Model: the shipped additive_v3 field at the cell nearest the station (7.2939 N, 80.6414 E), averaged over each local
(Asia/Colombo) day; also the basin-mean anchor T(t) as a second arm.
Split: days on which the low-cost sensors that train and sharpen T(t) reported (>= 18 hours from either sensor)
against days they did not -- the reconstruction / prospective distinction of the ladder rung, at Kandy.
Metrics: Pearson r, RMSE, bias (per cent of the observed mean), and a persistence-free benchmark: the observed
climatological monthly mean (in-sample for the observations, so it flatters the benchmark, not the model).
Digitisation error is a floor on the achievable agreement and is stated with the results.

Out: data/processed/decomp/kandy_nbro_daily_check.csv (per day), kandy_nbro_daily_check.json (summary)
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
OBS = REPO / "data" / "external" / "nbro" / "nirmani2025_kandy_daily_digitised.csv"
SLAT, SLON = 7.293864, 80.64136                     # NBRO Kandy (network feed coordinates)
TZ = "Asia/Colombo"


def model_daily(year):
    f = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}_additive_v3.parquet",
                        columns=["time", "lat", "lon", "pm25_q50"])
    lats, lons = np.sort(f.lat.unique()), np.sort(f.lon.unique())
    plat, plon = lats[np.abs(lats - SLAT).argmin()], lons[np.abs(lons - SLON).argmin()]
    t = pd.to_datetime(f.time, utc=True).dt.tz_convert(TZ).dt.tz_localize(None).dt.floor("D")
    cell = f[(f.lat == plat) & (f.lon == plon)].assign(day=t)
    basin = f.assign(day=t).groupby("day").pm25_q50.mean()
    return cell.groupby("day").pm25_q50.mean().rename("model_cell"), basin.rename("model_basin"), (plat, plon)


def sensor_days():
    d = pd.read_parquet(REPO / "data" / "processed" / "stage1_v3" / "dataset_v3_hourly.parquet",
                        columns=["datetime_utc", "sensor_id", "pm25_observed"]).dropna()
    t = pd.to_datetime(d.datetime_utc, utc=True).dt.tz_convert(TZ).dt.tz_localize(None).dt.floor("D")
    n = d.assign(day=t).groupby(["day", "sensor_id"]).size().unstack(fill_value=0)
    return set(n.index[(n >= 18).any(axis=1)])


def stats(o, m):
    e = m - o
    return dict(n=int(len(o)), r=float(np.corrcoef(o, m)[0, 1]), rmse=float(np.sqrt(np.mean(e ** 2))),
                bias_pct=float(100 * e.mean() / o.mean()), obs_mean=float(o.mean()), model_mean=float(m.mean()))


def main():
    obs = pd.read_csv(OBS, parse_dates=["date"]).groupby("date").pm25_digitised.mean()
    parts = []
    for y in (2021, 2022):
        c, b, cellpos = model_daily(y)
        parts.append(pd.concat([c, b], axis=1))
    M = pd.concat(parts)
    J = M.join(obs.rename("obs"), how="inner").dropna()
    sd = sensor_days()
    J["sensors_reported"] = J.index.isin(sd)
    J = J[~J.index.duplicated()]
    clim = J.groupby(J.index.month).obs.transform("mean")
    out = {"cell": [float(cellpos[0]), float(cellpos[1])], "days": int(len(J))}
    for scope, sub in (("all", J), ("sensors_reported", J[J.sensors_reported]),
                       ("sensors_absent", J[~J.sensors_reported])):
        if len(sub) < 20:
            continue
        out[scope] = {"model_cell": stats(sub.obs.values, sub.model_cell.values),
                      "model_basin": stats(sub.obs.values, sub.model_basin.values),
                      "monthly_climatology_benchmark": stats(sub.obs.values, clim.loc[sub.index].values)}
    mo = J.resample("MS").mean(numeric_only=True).dropna()
    out["monthly"] = stats(mo.obs.values, mo.model_cell.values)
    cl = mo.groupby(mo.index.month)[["obs", "model_cell"]].mean()
    out["climatology_r"] = float(cl.obs.corr(cl.model_cell))                  # 12 calendar months
    for y in (2021, 2022):
        s = mo[mo.index.year == y]
        out[f"monthly_r_{y}"] = float(s.obs.corr(s.model_cell))
    an = J.groupby(J.index.to_period("M"))[["obs", "model_cell"]].transform(lambda x: x - x.mean())
    out["anomaly_daily_r"] = float(an.obs.corr(an.model_cell))                 # day-to-day within month
    DEC.mkdir(parents=True, exist_ok=True)
    tmp = DEC / "kandy_nbro_daily_check.tmp.csv"; J.to_csv(tmp); os.replace(tmp, DEC / "kandy_nbro_daily_check.csv")
    p = DEC / "kandy_nbro_daily_check.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
