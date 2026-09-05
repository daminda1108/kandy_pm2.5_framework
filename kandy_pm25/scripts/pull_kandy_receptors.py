"""pull_kandy_receptors.py -- where the people who matter most actually are.

WHY THIS EXISTS. A sensor network designed only to inform a model is placed where the model is
most uncertain. A network designed to protect people is placed where susceptible people spend
time. Those are different objectives and they select different sites, so the campaign design
keeps them in separate strata rather than pretending one optimisation serves both.

This pulls the receptor layer: schools, hospitals, clinics, and care facilities inside the 15x15
km modelled domain, from OpenStreetMap.

WHY THESE GROUPS. Children breathe more air per unit body mass than adults and their lungs are
still developing; people already in hospital are by definition less able to tolerate an
additional insult. Both spend long, predictable hours at fixed, mappable locations, which is what
makes them addressable by a fixed-site network at all. Outdoor workers are equally exposed and
are NOT in this layer, because they have no fixed location: reaching them needs mobile or
personal sampling, and the plan says so rather than quietly dropping them.

⚠ OSM completeness varies and is not measurable from the data itself. A missing school is
invisible here. Counts are a lower bound and the plan treats them as one.

Usage: python scripts/pull_kandy_receptors.py
Out:   data/processed/decomp/kandy_receptors.csv
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import requests

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from config import KANDY_PINN_BBOX as BB  # noqa: E402

OUT = REPO / "data" / "processed" / "decomp" / "kandy_receptors.csv"
URL = "https://overpass-api.de/api/interpreter"
# Overpass returns 406 without a User-Agent (gotcha #41).
HEADERS = {"User-Agent": "kandy-pm25-research/1.0 (academic; contact: 11daminda08@gmail.com)"}

GROUPS = {
    "school": ['["amenity"="school"]', '["amenity"="kindergarten"]', '["amenity"="college"]'],
    "health": ['["amenity"="hospital"]', '["amenity"="clinic"]', '["amenity"="doctors"]'],
    "care": ['["amenity"="social_facility"]', '["amenity"="nursing_home"]'],
    "university": ['["amenity"="university"]'],
}


def query(sel: str) -> list[dict]:
    box = f'{BB["lat_min"]},{BB["lon_min"]},{BB["lat_max"]},{BB["lon_max"]}'
    q = (f'[out:json][timeout:90];('
         f'node{sel}({box});way{sel}({box});relation{sel}({box}););out center tags;')
    for attempt in range(4):
        try:
            r = requests.post(URL, data={"data": q}, headers=HEADERS, timeout=120)
            if r.status_code == 200:
                return r.json().get("elements", [])
            print(f"    HTTP {r.status_code}, retrying")
        except Exception as e:
            print(f"    {type(e).__name__}, retrying")
        time.sleep(6 * (attempt + 1))
    return []


def main() -> None:
    print("=== receptor layer for the Kandy campaign design ===")
    print(f"    domain {BB['lat_min']:.4f}-{BB['lat_max']:.4f}N, "
          f"{BB['lon_min']:.4f}-{BB['lon_max']:.4f}E\n")
    rows = []
    for group, sels in GROUPS.items():
        n0 = len(rows)
        for sel in sels:
            for el in query(sel):
                lat = el.get("lat") or (el.get("center") or {}).get("lat")
                lon = el.get("lon") or (el.get("center") or {}).get("lon")
                if lat is None or lon is None:
                    continue
                tags = el.get("tags", {})
                rows.append(dict(group=group, kind=tags.get("amenity", ""),
                                 name=tags.get("name", ""), lat=float(lat), lon=float(lon),
                                 osm_id=el.get("id")))
            time.sleep(2)
        print(f"    {group:11} {len(rows)-n0:>4}")

    d = pd.DataFrame(rows).drop_duplicates(subset=["osm_id"])
    # a node and its way sometimes both appear; collapse anything within ~30 m
    d["k"] = list(zip(d.lat.round(4), d.lon.round(4)))
    d = d.drop_duplicates(subset="k").drop(columns="k").reset_index(drop=True)
    d.to_csv(OUT, index=False)
    print(f"\n    {len(d)} distinct receptors -> {OUT.name}")
    print(d.group.value_counts().to_string())
    print(f"\n    named: {(d.name.fillna('') != '').sum()} of {len(d)}")
    print("\n[!] OSM completeness is not measurable from the data. These counts are a LOWER "
          "BOUND and the design treats them as one.")


if __name__ == "__main__":
    main()
