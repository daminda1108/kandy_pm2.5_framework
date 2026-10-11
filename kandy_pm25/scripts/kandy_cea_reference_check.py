"""kandy_cea_reference_check.py -- the delivered field against the CEA Kandy regulatory station (AAQMS), 2019-2023
(2026-10-11, ledger F.130). EXPLORATORY; the first comparison with a reference-grade record at Kandy.

Observed: CEA AAQMS (Department of Education, Bogambara; 7.2906 N, 80.6337 E), daily and hourly PM2.5 from the public
AirShare platform (scripts/pull_cea_kandy_aqms.py). Model: the delivered additive_v3 field at the station's cell, and
the dispersed variant shipped until 2026-10-11 (decomp/backup_dispersed_2026-10-11) as a comparison arm.

Daily: per-year level bias, r, RMSE; seasonal (calendar-month) climatology r; within-month anomaly r; the split by
whether the two low-cost sensors reported. Hourly (if present): the mean diurnal shape of the station against the
delivered anchor under the two humidity corrections of the sensor record (constant RH, delivered; hourly RH,
scripts/kandy_rh_scenario.py), via the same ratio-of-climatologies transform; morning-peak/midday and night/midday ratios.

Out: data/processed/decomp/kandy_cea_reference_check.json (+ _daily.csv, _hourly_diurnal.csv)

  --extension   score 2024-2026 against the driver-anchored extension tier (`..._additive_v3_drv`), which is
                built without a satellite level for those years: a prospective check. Writes `..._ext.*`; the
                hourly-RH scenario arm is not available for this tier, so only the delivered shape is scored.
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
DEC = REPO / "data" / "processed" / "decomp"
CEA = REPO / "data" / "external" / "cea"
SLAT, SLON = 7.2906, 80.6337
TZ = "Asia/Colombo"
YEARS = range(2019, 2024)
EXT = "--extension" in sys.argv
if EXT:
    YEARS = range(2024, 2027)


def cell_series(path_tpl):
    parts = []
    for y in YEARS:
        p = Path(str(path_tpl).format(y=y))
        if not p.exists():
            return None
        f = pd.read_parquet(p, columns=["time", "lat", "lon", "pm25_q50"])
        lats, lons = np.sort(f.lat.unique()), np.sort(f.lon.unique())
        plat, plon = lats[np.abs(lats - SLAT).argmin()], lons[np.abs(lons - SLON).argmin()]
        c = f[(f.lat == plat) & (f.lon == plon)].copy()
        c["time"] = pd.to_datetime(c.time, utc=True).dt.tz_convert(TZ).dt.tz_localize(None)
        parts.append(c.set_index("time").pm25_q50)
    return pd.concat(parts)


def stats(o, m):
    o, m = np.asarray(o, float), np.asarray(m, float)
    if len(o) < 3:
        return None
    return dict(n=int(len(o)), r=float(np.corrcoef(o, m)[0, 1]), rmse=float(np.sqrt(np.mean((m - o) ** 2))),
                bias_pct=float(100 * (m.mean() - o.mean()) / o.mean()), obs_mean=float(o.mean()), model_mean=float(m.mean()))


def sensor_days():
    d = pd.read_parquet(REPO / "data" / "processed" / "stage1_v3" / "dataset_v3_hourly.parquet",
                        columns=["datetime_utc", "sensor_id", "pm25_observed"]).dropna()
    t = pd.to_datetime(d.datetime_utc, utc=True).dt.tz_convert(TZ).dt.tz_localize(None).dt.floor("D")
    n = d.assign(day=t).groupby(["day", "sensor_id"]).size().unstack(fill_value=0)
    return set(n.index[(n >= 18).any(axis=1)])


def main():
    obs = pd.read_csv(CEA / "kandy_aqms_daily.csv", parse_dates=["created_at"])
    obs["day"] = obs.created_at.dt.floor("D")
    obs = obs.groupby("day").pm2_5.mean().dropna()
    obs = obs[(obs.index.year >= min(YEARS)) & (obs.index.year <= max(YEARS))]
    if EXT:
        arms = {"delivered": cell_series(DEC / "kandy_decomp_predictions_{y}_additive_v3_drv.parquet")}
    else:
        arms = {"delivered": cell_series(DEC / "kandy_decomp_predictions_{y}_additive_v3.parquet"),
                "dispersed_previous": cell_series(DEC / "backup_dispersed_2026-10-11" / "kandy_decomp_predictions_{y}_additive_v3.parquet")}
    sfx = "_ext" if EXT else ""
    out = {"station": [SLAT, SLON]}
    J = pd.DataFrame({"obs": obs})
    for k, s in arms.items():
        if s is not None:
            J[k] = s.groupby(s.index.floor("D")).mean()
    J = J.dropna()
    sd = sensor_days()
    J["sensors_reported"] = J.index.isin(sd)
    out["days"] = int(len(J))
    for k in [c for c in arms if c in J]:
        o = {"all": stats(J.obs, J[k]),
             "sensors_reported": stats(J[J.sensors_reported].obs, J[J.sensors_reported][k]),
             "sensors_absent": stats(J[~J.sensors_reported].obs, J[~J.sensors_reported][k])}
        o["by_year"] = {int(y): stats(g.obs, g[k]) for y, g in J.groupby(J.index.year) if len(g) >= 20}
        mo = J.resample("MS").mean(numeric_only=True).dropna()
        cl = mo.groupby(mo.index.month)[["obs", k]].mean()
        o["climatology_r"] = float(cl.obs.corr(cl[k]))
        o["monthly_r"] = float(mo.obs.corr(mo[k]))
        an = J.groupby(J.index.to_period("M"))[["obs", k]].transform(lambda x: x - x.mean())
        o["anomaly_daily_r"] = float(an.obs.corr(an[k]))
        out[k] = o
    clim = J.groupby(J.index.month).obs.transform("mean")
    out["monthly_climatology_benchmark"] = stats(J.obs, clim)
    J.to_csv(DEC / f"kandy_cea_reference_check{sfx}_daily.csv")

    hp = CEA / "kandy_aqms_hourly.csv"
    if hp.exists():
        h = pd.read_csv(hp, parse_dates=["created_at", "t_local"]).dropna(subset=["pm2_5"])
        h = h[(h.t_local.dt.year >= min(YEARS)) & (h.t_local.dt.year <= max(YEARS))]
    if hp.exists() and len(h) > 1000:
        # The platform stamps hourly records hh:30 in UTC, not local time: ozone, which peaks in the early afternoon,
        # peaks at stamps 04-08 (= 09:30-13:30 LT). Shift to Sri Lanka time (+05:30) before taking the local hour.
        # t_local is written by pull_cea_kandy_aqms.py with the per-source shift (manual sets UTC, live feed local).
        h["hour"] = h.t_local.dt.hour
        oh = h.groupby("hour").pm2_5.mean(); oh = oh / oh.mean()
        o3 = h.dropna(subset=["o3"]).groupby("hour").o3.mean()
        o3r = pd.concat([o3.iloc[-1:], o3, o3.iloc[:1]]).rolling(3, center=True).mean().iloc[1:-1]   # circular 3-h
        out["hourly_o3_peak_hour_local"] = int(o3r.idxmax())
        from kandy_rh_scenario import labels, clim as lclim, rescale   # the scenario transform, unchanged
        L = labels()
        cl = {lab: (lclim(L[lab], L.ts, "h"), lclim(L[lab], L.ts, "m")) for lab in ("production", "hourly_rh")}
        tan = REPO / "data" / "processed" / "stage1_v3" / "T_anchor"
        rows = {}
        if EXT:
            fld = arms["delivered"]
            fld = fld[fld.index.floor("h").isin(h.t_local.dt.floor("h"))]
            mh = fld.groupby(fld.index.hour).mean(); rows["production"] = mh / mh.mean()
        for lab in (() if EXT else ("production", "hourly_rh")):
            parts = []
            for y in YEARS:
                T0 = pd.read_parquet(tan / f"T_kandy_hourly_{y}.parquet", columns=["datetime_utc", "T_q05", "T_q50", "T_q95"])
                parts.append(rescale(T0, cl["production"], cl[lab]))
            T = pd.concat(parts)
            t = pd.to_datetime(T.datetime_utc, utc=True).dt.tz_convert(TZ).dt.tz_localize(None)
            T = T.assign(t=t).set_index("t")
            T = T[T.index.floor("h").isin(h.t_local.dt.floor("h"))]      # same hours as the station
            mh = T.groupby(T.index.hour).T_q50.mean(); rows[lab] = mh / mh.mean()
        D = pd.DataFrame({"station": oh, **rows})
        D.to_csv(DEC / f"kandy_cea_reference_check{sfx}_hourly_diurnal.csv")
        ratio = lambda s: dict(peak07_over_midday=float(s[7] / s[14]), night_over_midday=float(s[[0, 1, 2, 3, 4]].mean() / s[14]),
                               min_hour=int(s.idxmin()), max_hour=int(s.idxmax()))
        out["hourly"] = {"hours": int(len(h)), "station": ratio(D.station),
                         **{lab: {**ratio(D[lab]), "shape_r": float(D.station.corr(D[lab])),
                                  "shape_rmse": float(np.sqrt(((D.station - D[lab]) ** 2).mean()))} for lab in rows}}
    p = DEC / f"kandy_cea_reference_check{sfx}.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(out, indent=2), encoding="utf-8"); os.replace(tmp, p)
    print(json.dumps({k: (v if k in ("days", "station", "monthly_climatology_benchmark", "hourly", "hourly_o3_peak_hour_local") else
                          {kk: v[kk] for kk in ("all", "sensors_reported", "sensors_absent", "climatology_r", "monthly_r", "anomaly_daily_r")})
                      for k, v in out.items()}, indent=1)[:5000])


if __name__ == "__main__":
    main()
