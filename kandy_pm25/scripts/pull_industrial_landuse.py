"""Industrial land-use surfaces from OpenStreetMap — the sector the model has never had.

WHY. `src/modular/emission.py` defines an `industry` proxy that deliberately RAISES: industry is
the one sector that does not co-locate with roads or population, so there is no admissible
fallback. Consequently no city in the panel declares an industry sector, every declared mix sums
to 1.00 over vehic/heat/burn, and whatever industrial mass exists is implicitly placed on roads.
Yichang is the measured consequence -- the production traffic surface scores rho = -0.091 there,
anti-correlated with the stations.

WHAT IS PULLED. OSM polygons for industrial land use and the point/area sources that behave like
it. Free, global, and the only openly available industrial geometry at this scale:

    landuse=industrial   general industrial zoning
    landuse=quarry       extraction, a strong local dust source
    man_made=works       factories tagged individually
    power=plant          generation, which is neither roads nor population

WHAT IS BUILT. Fractional area coverage per grid cell -- the share of each cell occupied by
industrial polygons. Area-weighted rather than counted, because one large works matters more
than three small yards, and a count would say the opposite.

⚠ OSM completeness varies by country and is not uniform across this panel. A city with no
industrial polygons may have no industry OR no mapper; the two are indistinguishable here and
the count is reported per city so the difference is visible rather than averaged away.

Usage: .venv/Scripts/python.exe scripts/pull_industrial_landuse.py [--city SLUG]
Out:   data/processed/decomp/industry_{slug}.npz   (keys: industry, lats, lons, source)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import requests
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from calibrate_terrain_solver import SLUG, load_city  # noqa: E402

DEC = REPO / "data" / "processed" / "decomp"
OVERPASS = "https://overpass-api.de/api/interpreter"

# Overpass returns 406 without a User-Agent (gotcha #41). Contact string per OSM etiquette.
HEADERS = {"User-Agent": "kandy-pm25-research/1.0 (academic; contact: 11daminda08@gmail.com)"}

TAGS = [("landuse", "industrial"), ("landuse", "quarry"),
        ("man_made", "works"), ("power", "plant")]
NGRID = 32                      # the industry raster's own grid; interpolated later


def query(bbox) -> list:
    """Every industrial polygon in the box, as lists of (lat, lon) rings."""
    lat_min, lat_max, lon_min, lon_max = bbox
    parts = "".join(
        f'way["{k}"="{v}"]({lat_min},{lon_min},{lat_max},{lon_max});'
        f'relation["{k}"="{v}"]({lat_min},{lon_min},{lat_max},{lon_max});'
        for k, v in TAGS)
    q = f"[out:json][timeout:180];({parts});out geom;"
    for attempt in range(4):
        r = requests.post(OVERPASS, data={"data": q}, headers=HEADERS, timeout=240)
        if r.status_code in (429, 504):
            time.sleep(20 * (attempt + 1))
            continue
        r.raise_for_status()
        return r.json().get("elements", [])
    raise RuntimeError("Overpass kept refusing")


def polygons(elements) -> list:
    out = []
    for e in elements:
        if e.get("type") == "way" and e.get("geometry"):
            ring = [(p["lon"], p["lat"]) for p in e["geometry"]]
            if len(ring) >= 4:
                out.append(ring)
        elif e.get("type") == "relation":
            for m in e.get("members", []):
                if m.get("geometry") and m.get("role") in ("outer", ""):
                    ring = [(p["lon"], p["lat"]) for p in m["geometry"]]
                    if len(ring) >= 4:
                        out.append(ring)
    geoms = []
    for ring in out:
        try:
            g = Polygon(ring)
            if not g.is_valid:
                g = g.buffer(0)
            if g.is_valid and g.area > 0:
                geoms.append(g)
        except Exception:                                                   # noqa: BLE001
            continue
    return geoms


def rasterise(geoms, bbox, n=NGRID):
    """Fraction of each cell covered by industrial polygons."""
    lat_min, lat_max, lon_min, lon_max = bbox
    lats = np.linspace(lat_min, lat_max, n)
    lons = np.linspace(lon_min, lon_max, n)
    grid = np.zeros((n, n))
    if not geoms:
        return grid, lats, lons
    merged = unary_union(geoms)                 # dissolve overlaps: area, not double-counted area
    dlat = (lat_max - lat_min) / (n - 1)
    dlon = (lon_max - lon_min) / (n - 1)
    for i, la in enumerate(lats):
        for j, lo in enumerate(lons):
            cell = box(lo - dlon / 2, la - dlat / 2, lo + dlon / 2, la + dlat / 2)
            if merged.intersects(cell):
                grid[i, j] = merged.intersection(cell).area / cell.area
    return grid, lats, lons


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default=None, help="one slug, else every panel city")
    a = ap.parse_args()

    names = ["Xichang", "Bazhou", "Baoji", "Taian", "Yichang", "Chandigarh",
             "Kathmandu", "Medellin", "ChiangMai"]
    if a.city:
        names = [k for k, v in SLUG.items() if v == a.city]

    print("industrial land use from OpenStreetMap\n")
    print(f"  {'city':<11}{'polys':>7}{'cells>0':>9}{'max frac':>10}{'mean frac':>11}")
    print("  " + "-" * 48)
    for name in names:
        slug = SLUG[name]
        try:
            lats0, lons0, _, _, _, bbox = load_city(slug)
        except Exception as e:                                              # noqa: BLE001
            print(f"  {name:<11}  no grid: {str(e)[:40]}")
            continue
        try:
            els = query(bbox)
        except Exception as e:                                              # noqa: BLE001
            print(f"  {name:<11}  Overpass failed: {str(e)[:40]}")
            continue
        geoms = polygons(els)
        grid, lats, lons = rasterise(geoms, bbox)
        nz = int((grid > 0).sum())
        print(f"  {name:<11}{len(geoms):>7}{nz:>9}{grid.max():>10.3f}{grid.mean():>11.4f}")
        np.savez_compressed(DEC / f"industry_{slug}.npz", industry=grid, lats=lats, lons=lons,
                            source=f"OSM {'/'.join(k + '=' + v for k, v in TAGS)}; "
                                   f"{len(geoms)} polygons; fractional cell area")
        time.sleep(3)                            # Overpass etiquette
    print(f"\n  wrote industry_*.npz to {DEC.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
