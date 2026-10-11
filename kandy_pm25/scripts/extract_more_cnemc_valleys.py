"""Extract per-station MEAN PM2.5 for NEW Chinese valley cities from the CNEMC
HeQinWill archive, to expand the terrain-physics-learnable source set toward N=10.

Only per-station spatial means are needed (the terrain screen tests the SPATIAL
gradient), so we SAMPLE one hourly snapshot per Nth day across 2022-2026 rather
than parse all 1598 days — stable means, ~minutes not hours.

Output: data/processed/stage2/{slug}_valley_perstation.parquet (station_name, lat,
lon, pm25_raw=mean, n_obs) + prints bbox per city for the GEE terrain/NTL step.
"""
from __future__ import annotations
import glob
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
ARCH = REPO / "data" / "external" / "cnemc" / "heqinwill_clone" / "Archive"
OUT = REPO / "data" / "processed" / "stage2"

# new valley/basin candidates: slug -> CNEMC `area` string
NEW = {
    "lanzhou":   "兰州市",   "lhasa":     "拉萨市",   "chongqing": "重庆市",
    "panzhihua": "攀枝花市", "shiyan":    "十堰市",   "yibin":     "宜宾市",
    "zunyi":     "遵义市",   "leshan":    "乐山市",   "guiyang":   "贵阳市",
    "changzhi":  "长治市",
}
AREA2SLUG = {v: k for k, v in NEW.items()}
DAY_STRIDE = 8          # sample every 8th archive day


def main():
    days = sorted(d for d in ARCH.glob("20*-*-*") if d.is_dir())
    days = days[::DAY_STRIDE]
    print(f"Sampling {len(days)} days (stride {DAY_STRIDE}) for {len(NEW)} cities ...")
    # slug -> code -> [lat, lon, sum, cnt]
    acc = {s: defaultdict(lambda: [0.0, 0.0, 0.0, 0]) for s in NEW}
    for di, day in enumerate(days):
        files = sorted(day.glob("*.csv"))
        if not files:
            continue
        try:
            df = pd.read_csv(files[0], dtype={"stationcode": str},
                             usecols=["stationcode", "longitude", "latitude", "area", "pm2_5"])
        except Exception:
            continue
        df = df[df["area"].isin(AREA2SLUG)].dropna(subset=["pm2_5", "latitude", "longitude"])
        for r in df.itertuples(index=False):
            s = AREA2SLUG[r.area]
            e = acc[s][r.stationcode]
            e[0], e[1] = r.latitude, r.longitude
            e[2] += float(r.pm2_5); e[3] += 1
        if (di + 1) % 25 == 0:
            print(f"  {di+1}/{len(days)} days ...")

    rows, bboxes = [], {}
    for slug in NEW:
        st = [(c, v[0], v[1], v[2] / v[3], v[3]) for c, v in acc[slug].items() if v[3] >= 5]
        if len(st) < 5:
            print(f"  [skip] {slug}: only {len(st)} stations with data")
            continue
        df = pd.DataFrame(st, columns=["station_name", "lat", "lon", "pm25_raw", "n_obs"])
        df.to_parquet(OUT / f"{slug}_valley_perstation.parquet")
        la, lo = df.lat.values, df.lon.values
        bb = (float(la.min()-0.05), float(la.max()+0.05), float(lo.min()-0.05), float(lo.max()+0.05))
        bboxes[slug] = bb
        rows.append((slug, len(df), df.pm25_raw.mean(), bb))
        print(f"  {slug:<10} n_stn={len(df):<3} mean_pm={df.pm25_raw.mean():.0f}  "
              f"bbox=({bb[0]:.2f},{bb[1]:.2f},{bb[2]:.2f},{bb[3]:.2f})")

    # dump bbox table for the GEE step
    pd.DataFrame([{"slug": s, "lat_min": b[0], "lat_max": b[1], "lon_min": b[2],
                   "lon_max": b[3]} for s, b in bboxes.items()]).to_csv(
        OUT / "valley_bboxes.csv", index=False)
    print(f"\nWrote {len(rows)} city parquets + {OUT/'valley_bboxes.csv'}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
