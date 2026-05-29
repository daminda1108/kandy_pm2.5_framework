"""
build_decomp_map.py — assemble the production decomposition map (plan 2026-05-29):

    PM(x, y, t) = T(t) · S_emit(x, y) · M(x, y, t)
    M(x, y, t)  = 1 + kappa · w(BLH_t) · c(x, y)

Inputs (all on disk):
  T(t)        data/processed/stage1_v3/T_anchor/T_kandy_hourly_{year}.parquet
  S_emit      data/processed/decomp/S_emit_kandy.npz
  c(x,y)      data/processed/decomp/M_confinement_kandy.npz
  BLH(t)      data/processed/stage1_v3/inference_grid_{year}_s12451.parquet (blh_m)

Output:
  data/processed/decomp/kandy_decomp_predictions_{year}.parquet  (n_hours×256 rows)
  data/processed/decomp/decomp_summary_{year}.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

DATA = HERE / "data" / "processed"
DECOMP = DATA / "decomp"


def build(year: int = 2024, sensor_id: int = 12451):
    T = pd.read_parquet(DATA / "stage1_v3" / "T_anchor" / f"T_kandy_hourly_{year}.parquet")
    T["datetime_utc"] = pd.to_datetime(T["datetime_utc"], utc=True)
    grid = pd.read_parquet(DATA / "stage1_v3" / f"inference_grid_{year}_s{sensor_id}.parquet",
                           columns=["datetime_utc", "blh_m"])
    grid["datetime_utc"] = pd.to_datetime(grid["datetime_utc"], utc=True)
    T = T.merge(grid, on="datetime_utc", how="left").sort_values("datetime_utc").reset_index(drop=True)

    Sz = np.load(DECOMP / "S_emit_kandy.npz")
    Mz = np.load(DECOMP / "M_confinement_kandy.npz")
    S = Sz["S_emit"].astype(np.float32)            # (16,16)
    c = Mz["c"].astype(np.float32)                 # (16,16)
    lats, lons = Sz["lats"], Sz["lons"]
    kappa = float(Mz["kappa"]); H_ridge = float(Mz["H_ridge_m"])

    # time-weight w(t): nocturnal trapping when BLH below ridge height
    blh = T["blh_m"].to_numpy(dtype=np.float32)
    blh = np.where(np.isnan(blh), np.nanmedian(blh), blh)
    w = np.clip((H_ridge - blh) / H_ridge, 0.0, 1.0)        # (n_t,)

    n_t = len(T)
    Sf = S.ravel()[None, :]                                 # (1,256)
    cf = c.ravel()[None, :]                                 # (1,256)
    M = 1.0 + kappa * w[:, None] * cf                       # (n_t,256)
    SM = (Sf * M).astype(np.float32)                        # (n_t,256)

    out = {}
    for q in ("T_q05", "T_q50", "T_q95"):
        out[q.replace("T_", "pm25_")] = (T[q].to_numpy(np.float32)[:, None] * SM).ravel()
    out["pm25_q05"] = np.clip(out["pm25_q05"], 0.0, None)   # physical floor on PI lower

    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    times = np.repeat(T["datetime_utc"].to_numpy(), 256)
    df = pd.DataFrame({
        "time": times,
        "lat": np.tile(LA.ravel(), n_t),
        "lon": np.tile(LO.ravel(), n_t),
        "pm25_q50": out["pm25_q50"], "pm25_q05": out["pm25_q05"], "pm25_q95": out["pm25_q95"],
    })
    out_path = DECOMP / f"kandy_decomp_predictions_{year}.parquet"
    df.to_parquet(out_path, index=False)

    # ── summary: annual map + spatial contrast (day vs night) ──
    pm = out["pm25_q50"].reshape(n_t, 256)
    ann = pm.mean(0).reshape(16, 16)                        # annual-mean map
    lt_hour = T["datetime_utc"].dt.tz_convert("Asia/Colombo").dt.hour.to_numpy()
    night = np.isin(lt_hour, [0, 1, 2, 3, 4, 5, 22, 23])
    day = np.isin(lt_hour, [10, 11, 12, 13, 14, 15])
    night_map = pm[night].mean(0).reshape(16, 16)
    day_map = pm[day].mean(0).reshape(16, 16)

    def contrast(m):
        f = m.ravel()
        return float(np.quantile(f, 0.9) / np.quantile(f, 0.1))
    summ = dict(
        year=year, n_rows=len(df), annual_spatial_mean=float(ann.mean()),
        annual_contrast_p90_p10=contrast(ann),
        night_contrast=contrast(night_map), day_contrast=contrast(day_map),
        annual_min=float(ann.min()), annual_max=float(ann.max()),
        night_max=float(night_map.max()), day_max=float(day_map.max()),
        pi_width_mean=float((out["pm25_q95"] - out["pm25_q05"]).mean()),
    )
    pd.DataFrame([summ]).to_csv(DECOMP / f"decomp_summary_{year}.csv", index=False)
    print(f"── decomp map {year} ──")
    for k, v in summ.items():
        print(f"  {k:<24}{v}")
    print(f"\nWrote {out_path} ({len(df):,} rows)")
    return df


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()
    build(year=args.year)
