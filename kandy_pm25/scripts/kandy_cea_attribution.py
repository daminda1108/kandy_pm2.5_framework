"""kandy_cea_attribution.py -- where the level excess at the CEA Kandy station enters the chain (2026-10-11, F.131).

On days when the CEA regulatory station (AAQMS, city centre) and the FECT Akurana low-cost sensor both reported, compare:
  the station; the corrected Akurana record the temporal anchor is trained on; the basin anchor T(t) after its per-year
  re-anchoring to the van Donkelaar satellite level; and the delivered field at the station's cell.
Also the CEA/FECT ratio before and after 2024 (a check that the station's record did not shift between upload sets),
and the van Donkelaar annual level at the city pixel against the station's annual means. EXPLORATORY.

In: data/processed/decomp/kandy_cea_reference_check_daily.csv (from kandy_cea_reference_check.py),
    data/external/cea/kandy_aqms_daily.csv, stage1_v3/dataset_v3_hourly.parquet, T_anchor, vandonkelaar_kandy_annual.csv
Out: data/processed/decomp/kandy_cea_attribution.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
V3 = REPO / "data" / "processed" / "stage1_v3"
TZ = "Asia/Colombo"
AKU, HAN = 12451, 33495


def local_day(s):
    return pd.to_datetime(s, utc=True).dt.tz_convert(TZ).dt.tz_localize(None).dt.floor("D")


def main():
    J = pd.read_csv(DEC / "kandy_cea_reference_check_daily.csv", index_col=0, parse_dates=True)
    d = pd.read_parquet(V3 / "dataset_v3_hourly.parquet", columns=["datetime_utc", "sensor_id", "pm25_observed"]).dropna()
    d["day"] = local_day(d.datetime_utc)
    n = d.groupby(["day", "sensor_id"]).pm25_observed.agg(["mean", "size"])
    n = n[n["size"] >= 18]["mean"].unstack()
    T = pd.concat([pd.read_parquet(V3 / "T_anchor" / f"T_kandy_hourly_{y}.parquet", columns=["datetime_utc", "T_q50"])
                   for y in range(2019, 2024)])
    T["day"] = local_day(T.datetime_utc)
    K = J.join(n[AKU].rename("akurana")).join(T.groupby("day").T_q50.mean().rename("T_basin")).dropna(subset=["akurana"])
    out = {"shared_days": int(len(K)), "means": {c: float(K[c].mean()) for c in ("obs", "akurana", "T_basin", "delivered")}}
    out["pct_vs_station"] = {c: float(100 * (K[c].mean() / K.obs.mean() - 1)) for c in ("akurana", "T_basin", "delivered")}
    out["r_vs_station"] = {c: float(K.obs.corr(K[c])) for c in ("akurana", "T_basin", "delivered")}

    c = pd.read_csv(REPO / "data" / "external" / "cea" / "kandy_aqms_daily.csv", parse_dates=["created_at"]).dropna(subset=["pm2_5"])
    c = c.groupby(c.created_at.dt.floor("D")).pm2_5.mean()
    S = n.join(c.rename("cea"), how="inner")
    S["late"] = S.index >= "2024-01-01"
    out["cea_over_fect"] = {}
    for sid, tag in ((AKU, "akurana"), (HAN, "hantana")):
        for late, per in ((False, "2019_2023"), (True, "2024_2026")):
            g = S[(S.late == late)].dropna(subset=[sid])
            if len(g):
                out["cea_over_fect"][f"{tag}.{per}"] = {"n": int(len(g)), "median_ratio": float((g.cea / g[sid]).median()),
                                                        "r": float(g.cea.corr(g[sid])) if len(g) > 2 else None}
    va = pd.read_csv(V3 / "vandonkelaar_kandy_annual.csv").set_index("year")
    yr = J.groupby(J.index.year).obs.mean()
    out["vand_city_vs_station"] = {int(y): {"vand_city": float(va.loc[y, "city"]), "station": float(yr[y]),
                                            "pct": float(100 * (va.loc[y, "city"] / yr[y] - 1))}
                                   for y in yr.index if y in va.index and (J.index.year == y).sum() >= 150}
    p = DEC / "kandy_cea_attribution.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(out, indent=2), encoding="utf-8"); os.replace(tmp, p)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
