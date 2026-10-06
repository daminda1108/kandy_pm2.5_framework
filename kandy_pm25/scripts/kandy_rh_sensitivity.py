"""kandy_rh_sensitivity.py -- review step K-b (docs/review_remediation_plan_2026-10-06.md). EXPLORATORY.

The production label is Barkjohn (2021) with a CONSTANT RH = 80 % (calibrate_fect.CLIM_RH_KANDY), so the
RH term is a fixed offset and cannot remove humidity-driven over-reading that follows the diurnal RH cycle.
Here the same formula is evaluated with HOURLY ERA5 RH (from t2m, d2m in dataset_v3_hourly, Magnus formula),
and, as a non-linear alternative, with a kappa-Koehler hygroscopic growth correction
    PM_dry = PM_wet / (1 + kappa * aw / (1 - aw)),  aw = min(RH, 95 %) / 100,  kappa = 0.4 (range 0.2-0.6)
applied to the constant-RH Barkjohn value (relative correction normalised to its RH=80 % value, so the
annual level is unchanged and only the SHAPE moves). Reports the normalised diurnal profile and the
amplitude statistics the model is sharpened to (07 peak, 14 trough, 18-19 peak, 00-04 night), and the
coherence-floor f-proxy  1 - mean(daily min)/mean  on the sensor series itself.
Out: data/processed/decomp/rh_sensitivity.csv
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src.stage1_satml.data.calibrate_fect import CLIM_RH_KANDY, barkjohn   # noqa: E402

OUT = REPO / "data" / "processed" / "decomp" / "rh_sensitivity.csv"


def rh_from(t2m_k, d2m_k):
    t, d = t2m_k - 273.15, d2m_k - 273.15
    es = lambda x: np.exp(17.625 * x / (243.04 + x))
    return np.clip(100 * es(d) / es(t), 0, 100)


def main():
    d = pd.read_parquet(REPO / "data" / "processed" / "stage1_v3" / "dataset_v3_hourly.parquet")
    d = d.dropna(subset=["pm25_observed", "t2m", "d2m"]).copy()
    t2m, d2m = d.t2m.astype(float), d.d2m.astype(float)
    if t2m.median() < 100:                                     # already Celsius
        t2m, d2m = t2m + 273.15, d2m + 273.15
    d["rh"] = rh_from(t2m, d2m)
    # invert the constant-RH Barkjohn to recover cf_1, then re-apply with hourly RH
    cf1 = (d.pm25_observed - barkjohn(0.0, CLIM_RH_KANDY)) / (barkjohn(1.0, CLIM_RH_KANDY) - barkjohn(0.0, CLIM_RH_KANDY))
    variants = {"constant_rh80": d.pm25_observed,
                "barkjohn_hourly_rh": barkjohn(cf1, d.rh)}
    for kappa in (0.2, 0.4, 0.6):
        aw = np.minimum(d.rh, 95) / 100
        g = 1 + kappa * aw / (1 - aw)
        g80 = 1 + kappa * 0.8 / 0.2
        variants[f"koehler_k{kappa}"] = d.pm25_observed * g80 / g
    loc = pd.to_datetime(d.datetime_utc)
    loc = (loc.dt.tz_localize("UTC") if loc.dt.tz is None else loc).dt.tz_convert("Asia/Colombo")
    d["hour"], d["day"] = loc.dt.hour.to_numpy(), loc.dt.tz_localize(None).dt.floor("D").to_numpy()
    rows = []
    rh_h = d.groupby("hour").rh.mean()
    print("ERA5 RH by local hour: 07 %.0f  14 %.0f  19 %.0f  02 %.0f" % (rh_h[7], rh_h[14], rh_h[19], rh_h[2]))
    for name, v in variants.items():
        x = d.assign(v=v)
        x = x[x.v > 0]
        prof = x.groupby(["sensor_id", "hour"]).v.mean().groupby("hour").mean()
        prof = prof / prof.mean()
        night = prof.loc[[0, 1, 2, 3, 4]].mean()
        dd = x.groupby(["sensor_id", "day"]).v.agg(["min", "mean", "size"])
        dd = dd[dd["size"] >= 20]
        fproxy = float(1 - dd["min"].sum() / dd["mean"].sum())
        rows.append(dict(variant=name, h07=prof[7], h14=prof[14], h18_19=prof.loc[[18, 19]].mean(), night=night,
                         peak_to_trough=prof.max() / prof.min(), f_proxy_sensor=fproxy, mean=float(x.v.mean())))
    r = pd.DataFrame(rows)
    tmp = OUT.with_suffix(".tmp.csv"); r.to_csv(tmp, index=False); os.replace(tmp, OUT)
    print(r.round(3).to_string(index=False))
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
