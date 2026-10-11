"""kandy_attanayake_pixel.py -- the delivered field at the Attanayake et al. (2025) Kandy low-cost site (2026-10-11).

Replaces a hand-typed model value (25.01, ledger F.65) that predates the 2026-10-11 field changes (dispersion removed,
mean conservation fixed). The published record is 164 clear-sky daily means, 2022-11-02 -> 2024-02-29, mean 19.49; the
dates of the 164 days are not published, so the model is averaged over the calendar window. Only the anchored portion
(-> 2023-12-31) is scored: 2024 is outside the delivered 2019-2023 field.

Out: data/processed/decomp/kandy_attanayake_pixel.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
SLAT, SLON = 7.2731, 80.6117
OBS = 19.49
T0, T1 = pd.Timestamp("2022-11-02"), pd.Timestamp("2023-12-31 23:59")


def main():
    cell, area = [], []
    for y in (2022, 2023):
        f = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}_additive_v3.parquet", columns=["time", "lat", "lon", "pm25_q50"])
        f["time"] = pd.to_datetime(f.time, utc=True).dt.tz_convert("Asia/Colombo").dt.tz_localize(None)
        f = f[(f.time >= T0) & (f.time <= T1)]
        lats, lons = np.sort(f.lat.unique()), np.sort(f.lon.unique())
        plat, plon = lats[np.abs(lats - SLAT).argmin()], lons[np.abs(lons - SLON).argmin()]
        cell.append(f[(f.lat == plat) & (f.lon == plon)].pm25_q50)
        area.append(f.groupby("time").pm25_q50.mean())
    c, a = pd.concat(cell), pd.concat(area)
    out = dict(site=[SLAT, SLON], window=[str(T0.date()), str(T1.date())], obs_published=OBS,
               model_pixel=float(c.mean()), model_area=float(a.mean()),
               diff_pct=float(100 * (c.mean() - OBS) / OBS), hours=int(len(c)))
    p = DEC / "kandy_attanayake_pixel.json"
    tmp = p.with_suffix(".tmp.json"); tmp.write_text(json.dumps(out, indent=2), encoding="utf-8"); os.replace(tmp, p)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
