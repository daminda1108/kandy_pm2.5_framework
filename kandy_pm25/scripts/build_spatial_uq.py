"""Lever 3 — per-pixel SPATIAL uncertainty for the decomposition product.

The current PI (pm25_q05/q95) is the T(t) temporal-conformal interval scaled
multiplicatively by S·M (corr(q50, PI width)=0.999) — it carries NO independent
SPATIAL uncertainty. But the spatial layers are the least-anchored part of the model:
  - M-confinement amplitude κ is empirically UNIDENTIFIABLE from the valley networks
    (calibrate_m_confinement.py: b_c≈0, source/confinement collinear).
  - S_emit (VanD) has only weak ±10% contrast and documents over-prediction at
    elevated pixels (FECT Hantana obs 10.5 vs pred 19.9).
  - GHAP (U7) corroborates LEVEL/SEASON but the fine intra-valley pattern only weakly
    (r=0.13) — neither product strongly resolves 1 km structure.

So the honest move (Lever 3) is: inflate the PI MOST where the spatial structure is most
aggressive and least anchored, keep it tight on the well-anchored valley floor.

  d(x,y)   = pixel_annual_mean_q50 / basin_mean − 1          (spatial deviation)
  u(x,y)   = α0 + α1·(|d| / max|d|)                          (per-pixel uncertain fraction)
  σ_t      = (q95 − q05) / (2·1.645)                         (existing temporal σ)
  σ_sp     = u(x,y) · |q50(x,y,t) − basin_mean_q50(t)|       (spatial σ, hourly)
  σ_tot    = sqrt(σ_t² + σ_sp²)
  q05_sp   = max(q50 − 1.645·σ_tot, 0);  q95_sp = q50 + 1.645·σ_tot

α0=0.4 (40% of every pixel's spatial deviation is treated as uncertain — weak VanD +
unconstrained κ), α1=0.6 (rising to 100% at the most-deviating elevated/edge pixels).
These are documented priors, not fitted — the point is honest width, not a calibrated σ.

Output: data/processed/decomp/kandy_decomp_predictions_{year}_spuq.parquet
        (adds pm25_q05_sp, pm25_q95_sp, sigma_spatial) + printed width report.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
YEARS = range(2019, 2025)
Z90 = 1.6448536  # 90% two-sided
ALPHA0, ALPHA1 = 0.40, 0.60
CEN = (7.2906, 80.6337)


def process(year, report=False):
    f = DEC / f"kandy_decomp_predictions_{year}.parquet"
    if not f.exists():
        return None
    d = pd.read_parquet(f)
    # per-pixel spatial deviation from basin annual mean
    px = d.groupby(["lat", "lon"])["pm25_q50"].mean()
    basin = px.mean()
    dev = (px / basin - 1.0)
    u = ALPHA0 + ALPHA1 * (dev.abs() / dev.abs().max())     # per-pixel uncertain fraction
    u_map = u.to_dict()
    d["_u"] = list(map(u_map.get, zip(d.lat, d.lon)))
    # hourly basin mean q50
    bm = d.groupby("time")["pm25_q50"].transform("mean")
    sigma_t = (d.pm25_q95 - d.pm25_q05) / (2 * Z90)
    sigma_sp = d._u * (d.pm25_q50 - bm).abs()
    sigma_tot = np.sqrt(sigma_t**2 + sigma_sp**2)
    d["sigma_spatial"] = sigma_sp.astype(np.float32)
    d["pm25_q05_sp"] = np.clip(d.pm25_q50 - Z90 * sigma_tot, 0, None).astype(np.float32)
    d["pm25_q95_sp"] = (d.pm25_q50 + Z90 * sigma_tot).astype(np.float32)
    d = d.drop(columns=["_u"])
    out = DEC / f"kandy_decomp_predictions_{year}_spuq.parquet"
    d.to_parquet(out, index=False)

    if report:
        piw_old = (d.pm25_q95 - d.pm25_q05)
        piw_new = (d.pm25_q95_sp - d.pm25_q05_sp)
        # valley-floor vs elevated (by spatial deviation: floor = high q50, elevated = low)
        pxm = d.groupby(["lat", "lon"]).agg(
            q50=("pm25_q50", "mean"), old=("pm25_q95", "mean"),
            old0=("pm25_q05", "mean"), neww=("pm25_q95_sp", "mean"),
            new0=("pm25_q05_sp", "mean")).reset_index()
        pxm["piw_old"] = pxm.old - pxm.old0
        pxm["piw_new"] = pxm.neww - pxm.new0
        floor = pxm.q50 >= pxm.q50.quantile(0.75)
        elev = pxm.q50 <= pxm.q50.quantile(0.25)
        print(f"── {year} ──")
        print(f"  PI width  mean: {piw_old.mean():.1f} → {piw_new.mean():.1f} µg/m³  "
              f"(+{piw_new.mean()-piw_old.mean():.1f})")
        print(f"  valley-floor PI:  {pxm.loc[floor,'piw_old'].mean():.1f} → "
              f"{pxm.loc[floor,'piw_new'].mean():.1f}")
        print(f"  elevated-pixel PI: {pxm.loc[elev,'piw_old'].mean():.1f} → "
              f"{pxm.loc[elev,'piw_new'].mean():.1f}   "
              f"(elevated/floor width ratio {pxm.loc[elev,'piw_new'].mean()/pxm.loc[floor,'piw_new'].mean():.2f}×, "
              f"was {pxm.loc[elev,'piw_old'].mean()/pxm.loc[floor,'piw_old'].mean():.2f}×)")
    return out


def main():
    print("Building per-pixel spatial UQ (Lever 3)…")
    for yr in YEARS:
        o = process(yr, report=(yr in (2019, 2024)))
        if o:
            print(f"  wrote {o.name}")
    print("Done. New cols: pm25_q05_sp, pm25_q95_sp, sigma_spatial.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
