"""kandy_diurnal_cea_scenario.py -- the daily cycle of T(t) reshaped to the CEA regulatory station's, fitted on
2019-01 -> 2021-06 and scored on later days (2026-10-12; spec docs/diurnal_and_interval_widening_spec_2026-10-12.md,
committed before this ran). EXPLORATORY and non-destructive: no production file is written.

T'(t) = T(t) * r(h) [or r(season, h)], each year's mean restored (the level beta*VanD is unchanged). B is rebuilt with
the production builder because the coherence cap reads each day's lowest T. The station cell is reassembled with the
delivered pattern P at that cell, recovered from the stored additive_v3 field, and the stored epsilon floor.
Out: data/processed/decomp/diurnal_cea_scenario.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import build_additive_field_v2 as bv          # noqa: E402

DEC = REPO / "data" / "processed" / "decomp"
STG = REPO / "data" / "processed" / "stage1_v3"
CEA = REPO / "data" / "external" / "cea"
SLAT, SLON = 7.2906, 80.6337
TZ = "Asia/Colombo"
YEARS = range(2019, 2024)
CAL_END = pd.Timestamp("2021-07-01")
EPS0 = json.loads((DEC / "backup_fect_diurnal_2026-10-12" / "additive_v3_eps.json").read_text(encoding="utf-8"))["eps0"]
NITER = 3
# The scenario's "production" arm is the field BEFORE this step was adopted (F.137), kept in this backup, so the test
# stays reproducible after the delivered field changed. Re-running it reproduces diurnal_cea_scenario.json.
SRC = DEC / "backup_fect_diurnal_2026-10-12"
SWM = {5, 6, 7, 8, 9}


def split_floor(Tq, B, P, eps0=EPS0):
    i = Tq - B
    a = np.clip(i, 0, None); u = np.minimum(i, 0.0); e = np.clip(eps0 - a, 0, None)
    return B + np.maximum(a, eps0) * P + u - e


def load_year(y):
    """per-hour frame: T anchor quantiles, stored B, stored cell q05/q50/q95, recovered cell P."""
    f = pd.read_parquet(SRC / f"kandy_decomp_predictions_{y}_additive_v3.parquet",
                        columns=["time", "lat", "lon", "pm25_q05", "pm25_q50", "pm25_q95"])
    f["time"] = pd.to_datetime(f.time, utc=True)
    lats, lons = np.sort(f.lat.unique()), np.sort(f.lon.unique())
    plat, plon = lats[np.abs(lats - SLAT).argmin()], lons[np.abs(lons - SLON).argmin()]
    basin = f.groupby("time")[["pm25_q05", "pm25_q50", "pm25_q95"]].mean().add_prefix("bm_")
    c = f[(f.lat == plat) & (f.lon == plon)].set_index("time")[["pm25_q05", "pm25_q50", "pm25_q95"]]
    T = pd.read_parquet(SRC / "T_anchor" / f"T_kandy_hourly_{y}.parquet", columns=["datetime_utc", "T_q05", "T_q50", "T_q95"])
    T["time"] = pd.to_datetime(T.datetime_utc, utc=True)
    T = T.set_index("time")
    b = pd.read_parquet(SRC / f"B_background_hourly_{y}_v2.parquet")
    b["time"] = pd.to_datetime(b.datetime_utc, utc=True)
    d = T.join(b.set_index("time")[["B"]]).join(c).join(basin)
    a = np.clip(d.bm_pm25_q50 - d.B, 0, None)
    u = np.minimum(d.bm_pm25_q50 - d.B, 0.0); e = np.clip(EPS0 - a, 0, None)
    d["P"] = (d.pm25_q50 - d.B - u + e) / np.maximum(a, EPS0)
    # parity: the stored cell rebuilt from its own basin quantiles and the recovered P
    par = max(float(np.abs(split_floor(d[f"bm_pm25_{q}"], d.B, d.P) - d[f"pm25_{q}"]).max()) for q in ("q05", "q50", "q95"))
    d["tloc"] = d.index.tz_convert(TZ).tz_localize(None).floor("h")
    d["year"] = y
    return d, par


def apply_r(D, key, r):
    """T' = T * r[key], each year's mean of T_q50 restored."""
    k = D[key].map(r).to_numpy()
    out = D.copy()
    for q in ("T_q05", "T_q50", "T_q95"):
        out[q] = D[q].to_numpy() * k
    s = D.groupby("year").T_q50.transform("mean") / out.groupby("year").T_q50.transform("mean")
    for q in ("T_q05", "T_q50", "T_q95"):
        out[q] = out[q] * s
    return out


def rebuild_B(D, years):
    vand = pd.read_csv(STG / "vandonkelaar_kandy_annual.csv").set_index("year")
    out = D.copy()
    for y in years:
        m = out.year == y
        Ty = pd.DataFrame({"datetime_utc": out.index[m], "T_q50": out.T_q50[m].to_numpy()})
        b_annual = (1 - bv.FRAC_LOCAL_YEAR[y]) * float(vand.loc[y, "L_corrected"])
        out.loc[m, "B"] = bv.build_B_v2(y, b_annual, T_override=Ty).B.to_numpy()
    return out


def cell(D):
    return pd.DataFrame({q: np.asarray(split_floor(D[f"T_{q}"], D.B, D.P)) for q in ("q05", "q50", "q95")},
                        index=pd.DatetimeIndex(D.tloc.to_numpy()))


def clim(s, key):
    c = s.groupby(key).mean()
    return c / c.mean()


def metrics(j, fect_clim=None):
    o, m = j.obs, j.q50
    oh, mh = clim(o, j.index.hour), clim(m, j.index.hour)
    night = lambda c: c[[0, 1, 2, 3, 4, 5]].mean() / c[[11, 12, 13, 14, 15]].mean()
    morn = lambda c: c[[6, 7, 8, 9]].mean() / c[[11, 12, 13, 14, 15]].mean()
    d = j.groupby(j.index.floor("D")).agg(o=("obs", "mean"), m=("q50", "mean"), n=("obs", "size"))
    d = d[d.n >= 18]
    lo, hi = j.q05.clip(lower=0), j.q95.clip(lower=0)
    return dict(n=int(len(j)), diurnal_clim_r=float(np.corrcoef(oh, mh)[0, 1]),
                night_midday_obs=float(night(oh)), night_midday_model=float(night(mh)),
                morning_midday_obs=float(morn(oh)), morning_midday_model=float(morn(mh)),
                hourly_r=float(o.corr(m)), hourly_rmse=float(np.sqrt(((m - o) ** 2).mean())),
                daily_r=float(d.o.corr(d.m)), daily_bias_pct=float(100 * (d.m.mean() - d.o.mean()) / d.o.mean()),
                days=int(len(d)), cov90=float(((o >= lo) & (o <= hi)).mean()),
                below=float((o < lo).mean()), above=float((o > hi).mean()))


def f_partition(D):
    g = D.groupby("year")
    fy = 1 - g.B.mean() / g.T_q50.mean()
    return float(fy.mean()), {int(k): float(v) for k, v in fy.items()}


def fect_shape(D):
    """the field's T diurnal shape against the FECT climatology it is currently sharpened to (in-sample)."""
    d = pd.read_parquet(STG / "dataset_v3_hourly.parquet", columns=["datetime_utc", "pm25_observed"]).dropna()
    t = pd.to_datetime(d.datetime_utc, utc=True).dt.tz_convert(TZ)
    oh = d.groupby(t.dt.hour.values).pm25_observed.mean(); oh /= oh.mean()
    th = D.groupby(D.tloc.dt.hour).T_q50.mean(); th /= th.mean()
    return dict(r=float(np.corrcoef(oh, th)[0, 1]),
                night_midday_fect=float(oh[[0, 1, 2, 3, 4, 5]].mean() / oh[[11, 12, 13, 14, 15]].mean()),
                night_midday_T=float(th[[0, 1, 2, 3, 4, 5]].mean() / th[[11, 12, 13, 14, 15]].mean()))


def main():
    h = pd.read_csv(CEA / "kandy_aqms_hourly.csv", parse_dates=["t_local"]).dropna(subset=["pm2_5"])
    h = h[(h.pm2_5 > 0) & (h.pm2_5 < 500)]
    obs = h.groupby(h.t_local.dt.floor("h")).pm2_5.mean().rename("obs")
    parts, pars = [], {}
    for y in YEARS:
        d, par = load_year(y); parts.append(d); pars[y] = par
        print(f"  {y}: loaded, cell parity {par:.2e}", flush=True)
    D = pd.concat(parts)
    D["h"] = D.tloc.dt.hour
    D["sh"] = np.where(D.tloc.dt.month.isin(SWM), 100, 0) + D.h
    res = {"spec": "docs/diurnal_and_interval_widening_spec_2026-10-12.md", "eps0": EPS0,
           "cell_parity_max_abs": pars}
    base = cell(D).join(obs, how="inner").dropna()
    res["production"] = {"calibration": metrics(base[base.index < CAL_END]),
                         "held_out": metrics(base[base.index >= CAL_END]), "f": f_partition(D), "fect": fect_shape(D)}
    cal_years = [2019, 2020, 2021]
    for name, key in (("hour", "h"), ("season_hour", "sh")):
        r = pd.Series(1.0, index=sorted(D[key].unique()))
        for it in range(NITER):
            Dc = rebuild_B(apply_r(D[D.year.isin(cal_years)], key, r), cal_years)
            jc = cell(Dc).join(obs, how="inner").dropna()
            jc = jc[jc.index < CAL_END]
            kc = Dc.set_index("tloc")[key].reindex(jc.index)
            so = jc.obs.groupby(kc.values).mean(); sm = jc.q50.groupby(kc.values).mean()
            r = r * ((so / so.mean()) / (sm / sm.mean())).reindex(r.index).fillna(1.0)
            print(f"  {name} iter {it + 1}: night/midday model "
                  f"{metrics(jc)['night_midday_model']:.3f} vs obs {metrics(jc)['night_midday_obs']:.3f}", flush=True)
        S = rebuild_B(apply_r(D, key, r), list(YEARS))
        j = cell(S).join(obs, how="inner").dropna()
        res[name] = {"r": {str(k): float(v) for k, v in r.items()},
                     "calibration": metrics(j[j.index < CAL_END]), "held_out": metrics(j[j.index >= CAL_END]),
                     "f": f_partition(S), "fect": fect_shape(S)}
        P0, P1 = res["production"]["held_out"], res[name]["held_out"]
        a = P1["hourly_rmse"] < P0["hourly_rmse"]
        b = abs(P1["night_midday_model"] - P1["night_midday_obs"]) <= 0.5 * abs(P0["night_midday_model"] - P0["night_midday_obs"])
        c = P1["daily_r"] >= P0["daily_r"] - 0.02
        res[name]["adoption"] = dict(a_rmse_lower=bool(a), b_night_error_halved=bool(b), c_daily_r_ok=bool(c),
                                     adopt=bool(a and b and c))
    p = DEC / "diurnal_cea_scenario.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(res, indent=1), encoding="utf-8"); os.replace(tmp, p)
    for k in ("production", "hour", "season_hour"):
        for per in ("calibration", "held_out"):
            m = res[k][per]
            print(f"{k:12s} {per:11s} clim r {m['diurnal_clim_r']:.3f} night {m['night_midday_model']:.2f}/{m['night_midday_obs']:.2f} "
                  f"morn {m['morning_midday_model']:.2f}/{m['morning_midday_obs']:.2f} hr r {m['hourly_r']:.3f} rmse {m['hourly_rmse']:.2f} "
                  f"daily r {m['daily_r']:.3f} bias {m['daily_bias_pct']:+.1f} cov {m['cov90']:.3f}")
        print(f"   f {res[k]['f'][0]:.3f}  fect {res[k]['fect']}  adoption {res[k].get('adoption')}")


def write_r():
    """--write-r: the adopted arm's hour-of-day factors, for sharpen_T_diurnal.py (F.137). Only if the rule said adopt."""
    S = json.loads((DEC / "diurnal_cea_scenario.json").read_text(encoding="utf-8"))
    arm = S["hour"]
    if not arm["adoption"]["adopt"]:
        raise SystemExit("the pre-specified adoption rule did not pass; nothing written")
    out = {"r_by_local_hour": arm["r"], "arm": "hour", "fitted_on": "CEA AAQMS hourly, 2019-01-01 -> 2021-06-30",
           "applied_after": "the FECT hour/month sharpening, then each year's mean of T restored",
           "spec": S["spec"], "held_out": arm["held_out"], "adoption": arm["adoption"]}
    p = DEC / "diurnal_cea_r.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(out, indent=1), encoding="utf-8"); os.replace(tmp, p)
    print("wrote", p, {k: round(v, 3) for k, v in arm["r"].items()})


if __name__ == "__main__":
    write_r() if "--write-r" in sys.argv else main()
