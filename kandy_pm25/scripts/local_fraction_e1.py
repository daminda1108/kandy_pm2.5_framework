"""local_fraction_e1.py -- E1 of the local-fraction study: Kandy's urban increment against the AirShare regional network
(spec docs/local_fraction_study_spec_2026-10-11.md, committed before this script ran; ledger F.134).

f_E1 = 1 - <R>/<K>; K = CEA Kandy AAQMS daily PM2.5; R = daily regional background from IQAir units within 150 km of
Kandy and outside the Colombo urban area, calibrated against the reference AAQMS co-located at Battaramulla.
R primary = median of the calibrated regional sites (>= 2 reporting); sensitivities: daily minimum; all-island median
(excluding Colombo-area sites and Kandy). Month-block bootstrap (4000). Model: extension tier on the same days, and the
2019-2023 delivered field over the same calendar months.
Out: data/processed/decomp/local_fraction_e1.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
CEA = REPO / "data" / "external" / "cea"
KLAT, KLON = 7.2906, 80.6337
COLOMBO = {"Battaramulla", "Colombo 05", "Colombo 07", "Colombo"}
RADIUS_KM = 150
NB, SEED = 4000, 20261011


def km(lat, lon):
    p = np.radians
    a = np.sin((p(lat) - p(KLAT)) / 2) ** 2 + np.cos(p(KLAT)) * np.cos(p(lat)) * np.sin((p(lon) - p(KLON)) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def cell_daily(tpl, years):
    parts, Bs = [], []
    for y in years:
        p = Path(str(tpl[0]).format(y=y))
        if not p.exists():
            continue
        f = pd.read_parquet(p, columns=["time", "lat", "lon", "pm25_q50"])
        lats, lons = np.sort(f.lat.unique()), np.sort(f.lon.unique())
        plat, plon = lats[np.abs(lats - KLAT).argmin()], lons[np.abs(lons - KLON).argmin()]
        c = f[(f.lat == plat) & (f.lon == plon)]
        t = pd.to_datetime(c.time, utc=True).dt.tz_convert("Asia/Colombo").dt.tz_localize(None).dt.floor("D")
        parts.append(pd.Series(c.pm25_q50.to_numpy(), index=t).groupby(level=0).mean())
        b = pd.read_parquet(Path(str(tpl[1]).format(y=y)), columns=["datetime_utc", "B"])
        tb = pd.to_datetime(b.datetime_utc, utc=True).dt.tz_convert("Asia/Colombo").dt.tz_localize(None).dt.floor("D")
        Bs.append(pd.Series(b.B.to_numpy(), index=tb).groupby(level=0).mean())
    return pd.concat(parts).groupby(level=0).mean(), pd.concat(Bs).groupby(level=0).mean()   # a local day spans two UTC files at new year


def fboot(K, R, rng):
    df = pd.DataFrame({"K": K, "R": R}).dropna()
    m = df.index.to_period("M"); groups = [df[m == u] for u in m.unique()]
    pt = 1 - df.R.mean() / df.K.mean()
    bs = []
    for _ in range(NB):
        d = pd.concat([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        bs.append(1 - d.R.mean() / d.K.mean())
    return dict(f=float(pt), ci95=[float(x) for x in np.percentile(bs, [2.5, 97.5])], days=int(len(df)),
                months=int(len(groups)), K_mean=float(df.K.mean()), R_mean=float(df.R.mean()))


def main():
    rng = np.random.default_rng(SEED)
    net = pd.read_csv(CEA / "network_daily.csv", parse_dates=["day"])
    net["dist_km"] = km(net.lat, net.lon)
    # calibration at Battaramulla: AAQMS (1) vs IQAir (4)
    bat = net[net.name == "Battaramulla"].pivot_table(index="day", columns="equipment_id", values="pm2_5").dropna()
    bat = bat.rename(columns={1: "ref", 4: "iq"})
    b, a = np.polyfit(bat.iq, bat.ref, 1)
    cal = dict(days=int(len(bat)), slope=float(b), intercept=float(a), r=float(bat.ref.corr(bat.iq)),
               ref_mean=float(bat.ref.mean()), iq_mean=float(bat.iq.mean()))
    calibrated = cal["r"] >= 0.7 and cal["days"] >= 60
    iq = net[(net.equipment_id == 4) & (~net.name.isin(COLOMBO)) & (net.name != "Kandy")].copy()
    iq["pm_cal"] = a + b * iq.pm2_5
    # Kandy reference: AAQMS daily from the full daily pull (covers 2019 -> today)
    kd = pd.read_csv(CEA / "kandy_aqms_daily.csv", parse_dates=["created_at"]).dropna(subset=["pm2_5"])
    K = kd.groupby(kd.created_at.dt.floor("D")).pm2_5.mean()
    out = {"spec": "docs/local_fraction_study_spec_2026-10-11.md", "calibration_battaramulla": cal,
           "calibration_applied": calibrated, "sites": {}}
    near = iq[iq.dist_km <= RADIUS_KM]
    for nm, g in iq.groupby("name"):
        out["sites"][nm] = dict(dist_km=round(float(g.dist_km.iloc[0]), 1), days=int(len(g)), near=bool(g.dist_km.iloc[0] <= RADIUS_KM))
    col = "pm_cal" if calibrated else "pm2_5"
    wide_near = near.pivot_table(index="day", columns="name", values=col)
    wide_all = iq.pivot_table(index="day", columns="name", values=col)
    ok = wide_near.notna().sum(axis=1) >= 2
    R_med, R_min = wide_near[ok].median(axis=1), wide_near[ok].min(axis=1)
    R_isl = wide_all[wide_all.notna().sum(axis=1) >= 2].median(axis=1)
    out["primary_median_near"] = fboot(K, R_med, rng)
    out["sens_min_near"] = fboot(K, R_min, rng)
    out["sens_island_median"] = fboot(K, R_isl, rng)
    if calibrated:
        wide_raw = near.pivot_table(index="day", columns="name", values="pm2_5")
        okr = wide_raw.notna().sum(axis=1) >= 2
        out["sens_uncalibrated_median_near"] = fboot(K, wide_raw[okr].median(axis=1), rng)
    days = pd.DataFrame({"K": K, "R": R_med}).dropna().index
    # model: extension tier on the same days
    ext_cell, ext_B = cell_daily((DEC / "kandy_decomp_predictions_{y}_additive_v3_drv.parquet",
                                  DEC / "B_background_hourly_{y}_v2_drv.parquet"), (2024, 2025, 2026))
    E = pd.DataFrame({"cell": ext_cell, "B": ext_B}).reindex(days).dropna()
    out["model_extension_same_days"] = dict(days=int(len(E)), f_model_cell=float(1 - E.B.mean() / E.cell.mean()))
    # model: delivered 2019-2023 over the same calendar months (weights = matched days per month)
    cell, Bd = cell_daily((DEC / "kandy_decomp_predictions_{y}_additive_v3.parquet",
                           DEC / "B_background_hourly_{y}_v2.parquet"), range(2019, 2024))
    D = pd.DataFrame({"cell": cell, "B": Bd}).dropna()
    w = pd.Series(days.month).value_counts()
    mc = D.groupby(D.index.month).mean()
    cellw = float((mc.cell.reindex(w.index) * w).sum() / w.sum()); Bw = float((mc.B.reindex(w.index) * w).sum() / w.sum())
    out["model_delivered_same_months"] = dict(f_model_cell=1 - Bw / cellw)
    p = DEC / "local_fraction_e1.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(out, indent=1), encoding="utf-8"); os.replace(tmp, p)
    print(json.dumps({k: v for k, v in out.items() if k != "sites"}, indent=1))
    print("sites:", out["sites"])


if __name__ == "__main__":
    main()
