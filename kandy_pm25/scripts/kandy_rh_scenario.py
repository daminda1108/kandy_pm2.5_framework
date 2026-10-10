"""kandy_rh_scenario.py -- the hourly-humidity label as a full alternative scenario for T(t) (2026-10-10, F.126).
EXPLORATORY; non-destructive (no production file is written).

The production label is Barkjohn (2021) at a constant RH of 80 %. The alternative evaluates the same formula
with hourly ERA5 RH (kandy_rh_sensitivity.py). Production T(t) is sharpened to the label's hour-of-day and
month climatologies (sharpen_T_diurnal.py). The alternative scales it by the ratio of the alternative label's
normalised climatologies to the production label's, then restores the annual mean (the van Donkelaar level),
so the delivered cycle moves exactly as far as the label's does. The production scenario is the identity. The learned residual is not
retrained: the lag-free GBM damps the cycle and the sharpening step sets its amplitude, so the label enters
the delivered series through the sharpening (stated as a limitation).

For each scenario: diurnal and seasonal statistics of T, the coherence-capped background and local fraction
(production builder with T_override; parity with the stored background in the production scenario), and
T's hourly interval coverage and daily skill against the sensor record expressed in the SAME label.

Out: data/processed/decomp/rh_scenario.csv (per year x scenario), rh_scenario_summary.csv
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import build_additive_field_v2 as bv                                        # noqa: E402
from kandy_rh_sensitivity import rh_from                                     # noqa: E402
from src.stage1_satml.data.calibrate_fect import CLIM_RH_KANDY, barkjohn     # noqa: E402

STG = REPO / "data" / "processed" / "stage1_v3"
OUT = REPO / "data" / "processed" / "decomp" / "rh_scenario.csv"
YEARS = range(2019, 2024)


def labels() -> pd.DataFrame:
    d = pd.read_parquet(STG / "dataset_v3_hourly.parquet")
    d = d.dropna(subset=["pm25_observed", "t2m", "d2m"]).copy()
    t2m, d2m = d.t2m.astype(float), d.d2m.astype(float)
    if t2m.median() < 100:
        t2m, d2m = t2m + 273.15, d2m + 273.15
    rh = rh_from(t2m, d2m)
    cf1 = (d.pm25_observed - barkjohn(0.0, CLIM_RH_KANDY)) / (barkjohn(1.0, CLIM_RH_KANDY) - barkjohn(0.0, CLIM_RH_KANDY))
    d["production"] = d.pm25_observed
    d["hourly_rh"] = barkjohn(cf1, rh)
    d["ts"] = pd.to_datetime(d.datetime_utc, utc=True)
    sid = "sensor_id" if "sensor_id" in d.columns else "station_id"
    return d[["ts", sid, "production", "hourly_rh"]].rename(columns={sid: "sensor"})


def clim(s: pd.Series, ts: pd.Series, by: str) -> pd.Series:
    t = ts.dt.tz_convert("Asia/Colombo")
    key = t.dt.hour if by == "h" else t.dt.month
    c = s.groupby(key.values).mean()
    return c / c.mean()


def rescale(T: pd.DataFrame, cl_from: tuple, cl_to: tuple) -> pd.DataFrame:
    """Move T's hour-of-day and month climatology from one label's to another's by the RATIO of the two
    labels' normalised climatologies, then restore the annual mean (the van Donkelaar level). With
    cl_from == cl_to this is the identity, so the production scenario is the stored T exactly."""
    T = T.copy()
    tl = pd.to_datetime(T["datetime_utc"], utc=True).dt.tz_convert("Asia/Colombo")
    rh = (cl_to[0] / cl_from[0]).to_dict(); rm = (cl_to[1] / cl_from[1]).to_dict()
    kv = tl.dt.hour.map(rh).fillna(1.0).values * tl.dt.month.map(rm).fillna(1.0).values
    orig = float(T["T_q50"].mean())
    for c in ("T_q05", "T_q50", "T_q95"):
        T[c] = T[c].values * kv
    scale = orig / float(T["T_q50"].mean())
    for c in ("T_q05", "T_q50", "T_q95"):
        T[c] = T[c] * scale
    return T


def stats_T(T: pd.DataFrame) -> dict:
    tl = pd.to_datetime(T["datetime_utc"], utc=True).dt.tz_convert("Asia/Colombo")
    h = T.groupby(tl.dt.hour.values).T_q50.mean(); h = h / h.mean()
    m = T.groupby(tl.dt.month.values).T_q50.mean(); m = m / m.mean()
    return dict(T_mean=float(T.T_q50.mean()), T_h07=h[7], T_h14=h[14], T_peak_trough=h[7] / h[14],
                T_night_midday=h[[0, 1, 2, 3, 4]].mean() / h[14], T_season_swing=m.max() / m.min())


def skill(T: pd.DataFrame, L: pd.DataFrame, lab: str) -> dict:
    t = T.assign(ts=pd.to_datetime(T.datetime_utc, utc=True))[["ts", "T_q05", "T_q50", "T_q95"]]
    j = L.merge(t, on="ts", how="inner").dropna(subset=[lab])
    if j.empty:
        return {}
    y = j[lab]
    inside = (y >= j.T_q05) & (y <= j.T_q95)
    off = j.groupby("sensor").apply(lambda g: (g[lab] - g.T_q50).median())
    yc = y - j.sensor.map(off)
    inside_c = (yc >= j.T_q05) & (yc <= j.T_q95)
    dd = j.assign(day=j.ts.dt.tz_convert("Asia/Colombo").dt.floor("D")).groupby("day")[[lab, "T_q50"]].mean()
    return dict(n_hours=len(j), cov90=float(inside.mean()), miss_below=float((y < j.T_q05).mean()),
                miss_above=float((y > j.T_q95).mean()), cov90_recentred=float(inside_c.mean()),
                daily_r=float(dd[lab].corr(dd.T_q50)),
                daily_rmse=float(np.sqrt(((dd[lab] - dd.T_q50) ** 2).mean())),
                label_mean=float(y.mean()))


def main():
    L = labels()
    vand = pd.read_csv(STG / "vandonkelaar_kandy_annual.csv").set_index("year")
    cl = {lab: (clim(L[lab], L.ts, "h"), clim(L[lab], L.ts, "m")) for lab in ("production", "hourly_rh")}
    rows = []
    for y in YEARS:
        T0 = pd.read_parquet(bv.TANCHOR / f"T_kandy_hourly_{y}.parquet",
                             columns=["datetime_utc", "T_q05", "T_q50", "T_q95"])
        b_annual = (1 - bv.FRAC_LOCAL_YEAR[y]) * float(vand.loc[y, "basin_mean"])
        stored = pd.read_parquet(bv.DEC / f"B_background_hourly_{y}_v2.parquet").B.to_numpy()
        for lab in ("production", "hourly_rh"):
            T = rescale(T0, cl["production"], cl[lab])
            B = bv.build_B_v2(y, b_annual, T_override=T[["datetime_utc", "T_q50"]]).B.to_numpy()
            rec = dict(year=y, scenario=lab, f=1 - B.mean() / T.T_q50.mean(), **stats_T(T), **skill(T, L, lab))
            if lab == "production":
                rec["T_parity_max_abs"] = float(np.max(np.abs(T.T_q50.to_numpy() - T0.T_q50.to_numpy())))
                rec["B_parity_max_abs"] = float(np.max(np.abs(B - stored)))
            rows.append(rec)
        print(f"  {y} done", flush=True)
    d = pd.DataFrame(rows)
    tmp = OUT.with_suffix(".tmp.csv"); d.to_csv(tmp, index=False); os.replace(tmp, OUT)
    s = d.drop(columns=["year"]).groupby("scenario").mean(numeric_only=True).T
    s["change"] = s["hourly_rh"] - s["production"]
    sp = OUT.with_name("rh_scenario_summary.csv"); tmp = sp.with_suffix(".tmp.csv")
    s.to_csv(tmp); os.replace(tmp, sp)
    print(s.round(4).to_string())
    print("parity T/B (production):", d.T_parity_max_abs.max(), d.B_parity_max_abs.max())


if __name__ == "__main__":
    main()
