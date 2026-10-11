"""pull_cea_kandy_aqms.py -- the CEA Kandy regulatory station (AAQMS) from the public AirShare platform
(https://aq.cea.lk, Central Environmental Authority). 2026-10-11, ledger F.130.

The platform's own charts read `/public/sensor-data/history` without authentication; this script uses the same
endpoint at a polite rate (one request per second, resumable cache). Kandy is `locationId=4`; the reference station is
equipment `1` ("AAQMS - Ambient Air Quality Monitoring System"). A one-day window returns hourly records; a month
returns daily records.

  --daily   one request per month, 2019-01 .. today  -> data/external/cea/kandy_aqms_daily.csv
  --hourly  one request per day, --start .. --end    -> data/external/cea/kandy_aqms_hourly.csv
Raw JSON per request is cached under data/external/cea/raw/ so a rerun only fetches what is missing.
Data are CEA's; cite the Central Environmental Authority and observe its conditions for academic use.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import pandas as pd
import requests

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "external" / "cea"
RAW = OUT / "raw"
URL = "https://aq.cea.lk/public/sensor-data/history"
LOC, EQ = 4, 1
FIELDS = ["pm2_5", "pm10", "o3", "co", "no2", "so2", "pm2_5_status", "pm10_status", "created_at"]


def session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (academic research; University of Peradeniya PM2.5 thesis)",
                      "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"})
    s.get("https://aq.cea.lk/", timeout=60)
    return s


def fetch(s, start, end, tag):
    p = RAW / f"{tag}_{start}_{end}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    for attempt in range(4):
        try:
            r = s.get(URL, params={"locationId": LOC, "equipmentId": EQ, "startTime": start, "endTime": end}, timeout=90)
            r.raise_for_status()
            j = r.json()
            tmp = p.with_suffix(".tmp"); tmp.write_text(json.dumps(j), encoding="utf-8"); os.replace(tmp, p)
            time.sleep(1.0)
            return j
        except Exception as e:                                       # noqa: BLE001
            print(f"  retry {attempt + 1} {start}: {str(e)[:80]}", flush=True); time.sleep(5 * (attempt + 1))
    raise SystemExit(f"failed {start}..{end}")


def rows(j):
    out = []
    for x in j.get("result", []):
        if "pm2_5" not in x and "pm10" not in x:
            continue                                                 # an empty slot (created_at only)
        out.append({k: x.get(k) for k in FIELDS})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--daily", action="store_true")
    ap.add_argument("--hourly", action="store_true")
    ap.add_argument("--start", default="2019-01-01")
    ap.add_argument("--end", default="2023-12-31")
    a = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    s = session()
    if a.daily:
        R = []
        for m in pd.period_range("2019-01", pd.Timestamp.today().strftime("%Y-%m"), freq="M"):
            j = fetch(s, m.start_time.strftime("%Y-%m-%d"), m.end_time.strftime("%Y-%m-%d"), "daily")
            assert j.get("type") == "daily", (m, j.get("type"))
            R += rows(j)
        d = pd.DataFrame(R).drop_duplicates("created_at")
        tmp = OUT / "kandy_aqms_daily.tmp.csv"; d.to_csv(tmp, index=False); os.replace(tmp, OUT / "kandy_aqms_daily.csv")
        print(f"daily: {len(d)} days with values; PM2.5 non-null {d.pm2_5.notna().sum()}")
    if a.hourly:
        R = []
        days = pd.date_range(a.start, a.end, freq="D")
        for i, day in enumerate(days):
            k = day.strftime("%Y-%m-%d")
            j = fetch(s, k, k, "hourly")
            if j.get("type") != "hourly":
                print(f"  {k}: type {j.get('type')}", flush=True)
            R += rows(j)
            if i % 100 == 0:
                print(f"  {i + 1}/{len(days)} {k}", flush=True)
        h = pd.DataFrame(R).drop_duplicates("created_at")
        tmp = OUT / "kandy_aqms_hourly.tmp.csv"; h.to_csv(tmp, index=False); os.replace(tmp, OUT / "kandy_aqms_hourly.csv")
        print(f"hourly: {len(h)} hours with values; PM2.5 non-null {h.pm2_5.notna().sum()}")


if __name__ == "__main__":
    main()
