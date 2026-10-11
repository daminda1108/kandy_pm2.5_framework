"""pull_cea_airshare_network.py -- daily PM2.5 from the CEA AirShare network (https://aq.cea.lk), 2024-06 .. today
(2026-10-11, local-fraction study F.134, spec docs/local_fraction_study_spec_2026-10-11.md).

Locations and their equipment come from the platform's own public routes (`/public/sensor-locations`,
`/public/sensors/location/{id}`). Equipment 1 = the regulatory AAQMS, 3 = NBRO sensor (no history is served), 4 = IQAir.
One request per (location, equipment, month); a month window returns daily records. Polite rate (1 s), raw cache.

Out: data/external/cea/network_daily.csv  (location_id, name, lat, lon, equipment_id, equipment, day, pm2_5, pm10)
Data are CEA's; cite the Central Environmental Authority.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd
import requests

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "external" / "cea"
RAW = OUT / "raw_network"
BASE = "https://aq.cea.lk"


def session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (academic research; University of Peradeniya PM2.5 thesis)",
                      "Accept": "application/json"})
    s.get(BASE + "/", timeout=60)
    return s


def get_json(s, path, params=None, cache=None):
    if cache and cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    for attempt in range(4):
        try:
            r = s.get(BASE + path, params=params, timeout=90)
            r.raise_for_status()
            j = r.json()
            if cache:
                tmp = cache.with_suffix(".tmp"); tmp.write_text(json.dumps(j), encoding="utf-8"); os.replace(tmp, cache)
            time.sleep(1.0)
            return j
        except Exception as e:                                       # noqa: BLE001
            print(f"  retry {attempt + 1} {path} {params}: {str(e)[:80]}", flush=True); time.sleep(5 * (attempt + 1))
    raise SystemExit(f"failed {path} {params}")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    s = session()
    locs = get_json(s, "/public/sensor-locations")
    rows = []
    months = pd.period_range("2024-06", pd.Timestamp.today().strftime("%Y-%m"), freq="M")
    for L in locs:
        eqs = get_json(s, f"/public/sensors/location/{L['id']}", cache=RAW / f"eq_{L['id']}.json")
        for e in eqs:
            if e["id"] not in (1, 4):                                # NBRO (3) serves no history
                continue
            for m in months:
                a, b = m.start_time.strftime("%Y-%m-%d"), m.end_time.strftime("%Y-%m-%d")
                j = get_json(s, "/public/sensor-data/history",
                             {"locationId": L["id"], "equipmentId": e["id"], "startTime": a, "endTime": b},
                             cache=RAW / f"d_{L['id']}_{e['id']}_{m}.json")
                for x in j.get("result", []):
                    if x.get("pm2_5") is None:
                        continue
                    rows.append(dict(location_id=L["id"], name=L["name"], lat=float(L["latitude"]),
                                     lon=float(L["longitude"]), equipment_id=e["id"], equipment=e.get("name"),
                                     day=str(x["created_at"])[:10], pm2_5=x.get("pm2_5"), pm10=x.get("pm10")))
        print(f"  {L['name']}: {sum(1 for r in rows if r['location_id'] == L['id'])} station-days", flush=True)
    d = pd.DataFrame(rows).drop_duplicates(["location_id", "equipment_id", "day"])
    tmp = OUT / "network_daily.tmp.csv"; d.to_csv(tmp, index=False); os.replace(tmp, OUT / "network_daily.csv")
    print(f"network_daily.csv: {len(d)} station-days, {d.location_id.nunique()} locations")


if __name__ == "__main__":
    main()
