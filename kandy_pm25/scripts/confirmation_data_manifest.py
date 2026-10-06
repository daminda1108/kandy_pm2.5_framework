"""confirmation_data_manifest.py -- freeze the confirmation PREDICTORS by hash before registration.

Hashes every file the confirmation scorer will read other than PM2.5: the panel and members files,
every city's drivers and AOD file, and the urban-centre geography (per-city point/raster/road files
and the merged static_geo_grid.csv). REFUSES unless all 76 panel cities have every file and the merged
geography holds all 76. The combined SHA-256 (over the sorted per-file hashes) goes into the
registration.

Out: kandy_pm25/docs/confirmation_data_manifest.json
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CD = REPO / "data" / "processed" / "modular" / "confirmation"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    P = pd.read_csv(CD / "confirmation_panel.csv")
    cids = [str(c) for c in P.cid]
    files = [CD / "confirmation_panel.csv", CD / "confirmation_members.csv", CD / "static_geo_grid.csv"]
    missing = []
    for c in cids:
        for f in (CD / "drivers" / f"{c}.csv", CD / "aod" / f"{c}.csv",
                  *(CD / "geo_grid" / f"{c}_{s}.csv" for s in ("pts", "gee", "osm"))):
            (files.append(f) if f.exists() else missing.append(str(f.relative_to(CD))))
    if missing:
        print(f"REFUSED: {len(missing)} files missing, e.g. {missing[:6]}")
        return 1
    G = pd.read_csv(CD / "static_geo_grid.csv")
    absent = sorted(set(cids) - set(G.city.astype(str)))
    if absent:
        print(f"REFUSED: merged geography lacks {len(absent)} cities: {absent[:8]} (re-run the merge)")
        return 1
    per = {str(f.relative_to(REPO)).replace("\\", "/"): sha(f) for f in files}
    combined = hashlib.sha256("".join(f"{k}:{v}\n" for k, v in sorted(per.items())).encode()).hexdigest()
    out = {"what": "confirmation predictors frozen before registration (no PM2.5)",
           "frozen_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "cities": len(cids), "files": len(per), "combined_sha256": combined, "sha256": per}
    jp = REPO / "docs" / "confirmation_data_manifest.json"; tmp = jp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, indent=1), encoding="utf-8"); os.replace(tmp, jp)
    print(f"{len(per)} files, {len(cids)} cities; combined SHA-256 {combined}\n-> {jp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
