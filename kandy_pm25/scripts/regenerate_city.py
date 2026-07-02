"""regenerate_city.py — one-command reproduction of the city-generalised model.

Runs the full transfer-validation chain for any configured city, from public inputs
(SRTM DEM, ERA5, GEOS-CF, van Donkelaar / GHAP, OpenStreetMap, VIIRS, the public ground
network) to the held-out validation scorecard and the F1–F13 figure suite. This is the
reproducibility entry point for the paper's cross-city results: given the inputs staged
under data/, `python scripts/regenerate_city.py --city kathmandu` regenerates Kathmandu
end to end; likewise chiangmai, xichang, bazhou, chandigarh, baoji, taian, yichang.

Stages (skip any with --skip):
  terrain   build_xichang_core_terrain      DEM → core terrain npz
  traffic   build_xichang_traffic_emission  OSM road graph → emission surface
  winds     build_xichang_windninja         DEM → mass-consistent wind library (64 solves)
  prod      xichang_prod                     S_emit·M·T·B·4factor·additive_v2 fields
  figures   xichang_paper_figures            F1–F13 suite
  score     city_validation_scorecard        held-out-network scorecard (single city)

Inputs required on disk (per city), all public:
  data/external/{city}/dem/{dem}.tif                     SRTM (via GEE export)
  data/processed/stage2/{city}_perstation_v1x.parquet    public ground network (CNEMC/OpenAQ)
  ERA5 + GEOS-CF caches resolved by src/transfer_validation/drivers.py
  van Donkelaar / GHAP tiles resolved by citypack.vand_tile
The Kandy target itself needs no ground network (sensorless anchor); the analogue cities
use two elevation-gradient anchors, auto-selected.

Note: the model source lives under kandy_pm25/scripts + kandy_pm25/src/transfer_validation
and src/stage1_satml/decomp. For a public release, ship those two trees + this driver +
the data-fetch manifest (docs/REPRODUCE.md); data/ and results/ regenerate from here.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable

STAGES = [
    ("terrain", ["scripts/build_xichang_core_terrain.py", "--city", "{c}"]),
    ("traffic", ["scripts/build_xichang_traffic_emission.py", "--city", "{c}"]),
    ("winds",   ["scripts/build_xichang_windninja.py", "--city", "{c}"]),
    ("prod",    ["scripts/xichang_prod.py", "--city", "{c}"]),
    ("figures", ["scripts/xichang_paper_figures.py", "--city", "{c}", "--figs", "all"]),
    ("score",   ["scripts/city_validation_scorecard.py", "--cities", "{c}"]),
]


def run(city, skip):
    import os
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for name, cmd in STAGES:
        if name in skip:
            print(f"  [skip] {name}"); continue
        argv = [PY] + [a.format(c=city) for a in cmd]
        print(f"\n===== {name} :: {' '.join(argv[1:])} =====", flush=True)
        t0 = time.time()
        r = subprocess.run(argv, cwd=REPO, env=env)
        if r.returncode != 0:
            print(f"  ✗ stage '{name}' failed (exit {r.returncode}) — stopping."); sys.exit(r.returncode)
        print(f"  ✓ {name} in {time.time()-t0:.0f}s")
    print(f"\n✓ {city} regenerated. Products → data/processed/decomp_{city}/; "
          f"figures → results/figures/{city}_paper_figures_v2/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True)
    ap.add_argument("--skip", default="", help="comma list: terrain,traffic,winds,prod,figures,score")
    a = ap.parse_args()
    run(a.city, set(s.strip() for s in a.skip.split(",") if s.strip()))


if __name__ == "__main__":
    main()
