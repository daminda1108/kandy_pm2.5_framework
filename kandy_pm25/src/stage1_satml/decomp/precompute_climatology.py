"""
precompute_climatology.py — cache temporal + spatial climatology from the
2019-2023 decomposition maps (each year on its own real VanD level), so the
publication figures/tables are fast and mutually consistent.

Output: data/processed/decomp/climatology.npz with
  temporal (basin spatial-mean): diurnal[yr,24], weekly[yr,7], monthly[yr,12],
                                 annual[yr]  (LT = Asia/Colombo)
  spatial  (multi-year mean maps): seasonal[4,16,16] (DJF,MAM,JJA,SON),
                                   hourly[24,16,16], annual_map[16,16]
  + lats, lons, years
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
DECOMP = HERE / "data" / "processed" / "decomp"
YEARS = list(range(2019, 2024))
SEASONS = {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}


def main():
    lats = lons = None
    diur = {}; week = {}; mon = {}; ann = {}
    seas_sum = np.zeros((4, 16, 16)); seas_n = np.zeros(4)
    hour_sum = np.zeros((24, 16, 16)); hour_n = np.zeros(24)
    amap_sum = np.zeros((16, 16)); amap_n = 0

    for y in YEARS:
        d = pd.read_parquet(DECOMP / f"kandy_decomp_predictions_{y}.parquet",
                            columns=["time", "lat", "lon", "pm25_q50"])
        d["time"] = pd.to_datetime(d["time"], utc=True)
        lt = d["time"].dt.tz_convert("Asia/Colombo")
        d["hour"] = lt.dt.hour; d["dow"] = lt.dt.dayofweek
        d["month"] = lt.dt.month; d["seas"] = d["month"].map(SEASONS)
        if lats is None:
            lats = np.sort(d.lat.unique()); lons = np.sort(d.lon.unique())

        basin = d.groupby("time")["pm25_q50"].mean()
        bt = basin.index.tz_convert("Asia/Colombo")
        bdf = pd.DataFrame({"v": basin.values, "hour": bt.hour, "dow": bt.dayofweek,
                            "month": bt.month})
        diur[y] = bdf.groupby("hour")["v"].mean().reindex(range(24)).values
        week[y] = bdf.groupby("dow")["v"].mean().reindex(range(7)).values
        mon[y] = bdf.groupby("month")["v"].mean().reindex(range(1, 13)).values
        ann[y] = float(bdf["v"].mean())

        def _maps(key, n_bins):
            g = d.groupby([key, "lat", "lon"])["pm25_q50"].mean()
            out = np.full((n_bins, 16, 16), np.nan)
            for b in range(n_bins):
                if b in g.index.get_level_values(0):
                    sub = g.loc[b].reset_index()
                    out[b] = sub.pivot(index="lat", columns="lon", values="pm25_q50").values
            return out
        sm = _maps("seas", 4); hm = _maps("hour", 24)
        seas_sum += np.nan_to_num(sm); seas_n += (~np.isnan(sm[:, 0, 0])).astype(float)
        hour_sum += np.nan_to_num(hm); hour_n += (~np.isnan(hm[:, 0, 0])).astype(float)
        amap_sum += d.groupby(["lat", "lon"])["pm25_q50"].mean().unstack().values
        amap_n += 1
        print(f"  {y}: annual {ann[y]:.1f}  ({len(d):,} rows)")

    np.savez(DECOMP / "climatology.npz",
             years=np.array(YEARS), lats=lats, lons=lons,
             diurnal=np.array([diur[y] for y in YEARS]),
             weekly=np.array([week[y] for y in YEARS]),
             monthly=np.array([mon[y] for y in YEARS]),
             annual=np.array([ann[y] for y in YEARS]),
             seasonal=seas_sum / seas_n[:, None, None],
             hourly=hour_sum / hour_n[:, None, None],
             annual_map=amap_sum / amap_n)
    print(f"Wrote {DECOMP / 'climatology.npz'}")


if __name__ == "__main__":
    main()
