"""geofabrik_grid_roads.py -- urban-centre ROAD features from Geofabrik OSM extracts (2026-09-27).

Why: the public Overpass server slowed to ~4 min per tile, leaving 25 confirmation cities (10 CNEMC)
at a day or more. The road features are computed from the SAME OpenStreetMap data read from Geofabrik
extracts; deviation D-6 of the spatial learning curve showed the two routes identical (Spearman 1.000,
zero difference). This is declared in the confirmation registration BEFORE lodging, and validated here
again on cities already done through Overpass (--validate).

Method, identical to build_static_geo_grid's Overpass path except for the data source:
  * points: the city's existing geo_grid/{city}_pts.csv (40 random urban-centre points)
  * tiles:  spatial_curve_predictors._tiles (each point's 1.2 km reach + 3 km pad)
  * extract: the SMALLEST Geofabrik extract whose polygon contains every needed tile (index-v1.json);
             downloaded and MD5-verified; refuses if none contains them
  * segments: one osmium pass per extract over the union of all needed tiles, cached in THIS script's
             own directory (the spatial curve's segment cache is clipped to other cities' tiles and must
             never be read here)
  * features: spatial_curve_predictors._road_features (the function the Overpass path uses)

Usage:
  python scripts/geofabrik_grid_roads.py --panel confirmation --remaining
  python scripts/geofabrik_grid_roads.py --panel confirmation --validate CID[,CID]   # vs Overpass files
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import build_lur_predictors as blp                                      # noqa: E402
import spatial_curve_predictors as scp                                  # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
GF = REPO / "data" / "external" / "osm" / "geofabrik"
INDEX_URL = "https://download.geofabrik.de/index-v1.json"
SEGS = MOD / "confirmation" / "geofabrik_segments"


def index():
    f = GF / "index-v1.json"
    if not f.exists():
        req = urllib.request.Request(INDEX_URL, headers=blp.UA)
        with urllib.request.urlopen(req, timeout=300) as r:
            f.write_bytes(r.read())
    return json.loads(f.read_text(encoding="utf-8"))["features"]


def tile_boxes(tiles):
    from shapely.geometry import box
    T = scp.TILE_DEG
    return [box(j * T, i * T, (j + 1) * T, (i + 1) * T) for i, j in tiles]


def smallest_extract(tiles, feats):
    from shapely.geometry import shape
    from shapely.ops import unary_union
    need = unary_union(tile_boxes(tiles))
    best = None
    for f in feats:
        url = f["properties"].get("urls", {}).get("pbf")
        if not url or f.get("geometry") is None:
            continue
        g = shape(f["geometry"])
        if g.contains(need):
            if best is None or g.area < best[1]:
                best = (f["properties"]["id"], g.area, url)
    if best is None:
        raise RuntimeError("no single Geofabrik extract contains all needed tiles")
    return best[0], best[2]


def download(url):
    dest = GF / url.rsplit("/", 1)[1]
    md5_url = url + ".md5"
    req = urllib.request.Request(md5_url, headers=blp.UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        want = r.read().decode().split()[0]
    if dest.exists() and hashlib.md5(dest.read_bytes()).hexdigest() == want:
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    t = time.time()
    req = urllib.request.Request(url, headers=blp.UA)
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as fh:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            fh.write(b)
    got = hashlib.md5(tmp.read_bytes()).hexdigest()
    if got != want:
        tmp.unlink()
        raise RuntimeError(f"MD5 mismatch for {dest.name}")
    os.replace(tmp, dest)
    print(f"    downloaded {dest.name} {dest.stat().st_size / 1e6:.0f} MB in {time.time() - t:.0f} s",
          flush=True)
    return dest


def scan(pbf: Path, tiles: set, tag: str) -> pd.DataFrame:
    """Classed highway segments whose midpoint lies in `tiles`, from one extract (own cache)."""
    import osmium
    SEGS.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(("|".join(f"{i},{j}" for i, j in sorted(tiles)) + pbf.name).encode()).hexdigest()[:12]
    f = SEGS / f"{tag}_{key}.parquet"
    if f.exists():
        return pd.read_parquet(f)
    cls_of = {v: k for k, vs in blp.ROAD_CLASSES.items() for v in vs}
    fp = (osmium.FileProcessor(str(pbf)).with_locations()
          .with_filter(osmium.filter.EntityFilter(osmium.osm.WAY))
          .with_filter(osmium.filter.TagFilter(*[("highway", v) for v in cls_of])))
    rows = {k: [] for k in ("way", "seg", "cls", "mlat", "mlon", "len_km")}
    t, T = time.time(), scp.TILE_DEG
    for w in fp:
        pts = [(n.lat, n.lon) for n in w.nodes if n.location.valid()]
        if len(pts) < 2:
            continue
        m, l_ = scp._segments(pts)
        keep = [i for i in range(len(m)) if (int(np.floor(m[i, 0] / T)), int(np.floor(m[i, 1] / T))) in tiles]
        if not keep:
            continue
        c = cls_of[w.tags["highway"]]
        for i in keep:
            rows["way"].append(w.id); rows["seg"].append(i); rows["cls"].append(c)
            rows["mlat"].append(m[i, 0]); rows["mlon"].append(m[i, 1]); rows["len_km"].append(l_[i])
    out = pd.DataFrame(rows)
    tmp = f.with_suffix(".tmp"); out.to_parquet(tmp, index=False); os.replace(tmp, f)
    print(f"    scanned {pbf.name}: {len(out):,} segments in {time.time() - t:.0f} s", flush=True)
    return out


def features(pts: pd.DataFrame, S: pd.DataFrame, tiles: set) -> pd.DataFrame:
    T = scp.TILE_DEG
    key = list(zip(np.floor(S.mlat / T).astype(int), np.floor(S.mlon / T).astype(int)))
    S = S[[k in tiles for k in key]]
    return scp._road_features(pts, S[["mlat", "mlon"]].to_numpy(), S.len_km.to_numpy(), S.cls.to_numpy())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", choices=("confirmation",), default="confirmation")
    ap.add_argument("--remaining", action="store_true", help="every city without an _osm.csv")
    ap.add_argument("--validate", default="", help="cities already done by Overpass, to compare")
    a = ap.parse_args()
    GD = MOD / "confirmation" / "geo_grid"
    P = pd.read_csv(MOD / "confirmation" / "confirmation_panel.csv")
    if a.validate:
        cities = a.validate.split(",")
    else:
        cities = [c for c in P.cid if not (GD / f"{c}_osm.csv").exists()]
    feats = index()
    plan = {}
    for c in cities:
        pts = pd.read_csv(GD / f"{c}_pts.csv")
        tiles = set(scp._tiles(pts))
        rid, url = smallest_extract(tiles, feats)
        plan.setdefault((rid, url), []).append((c, pts, tiles))
        print(f"  {c:<16} -> {rid}", flush=True)
    fails = 0
    for (rid, url), members in sorted(plan.items(), key=lambda kv: kv[0][0]):
        try:
            pbf = download(url)
            union = set().union(*[m[2] for m in members])
            S = scan(pbf, union, rid.replace("/", "_"))
            for c, pts, tiles in members:
                out = features(pts, S, tiles)
                if a.validate:
                    ov = pd.read_csv(GD / f"{c}_osm.csv")
                    cols = [k for k in out.columns if k.startswith("road_") or k == "dist_major_km"]
                    d = (out[cols].to_numpy(float) - ov[cols].to_numpy(float))
                    rel = np.nanmax(np.abs(d)) / max(1e-9, np.nanmax(np.abs(ov[cols].to_numpy(float))))
                    cm = pd.concat([out[cols].mean(), ov[cols].mean()], axis=1).corr(method="spearman").iloc[0, 1]
                    print(f"  VALIDATE {c}: city-mean Spearman {cm:.4f}; max |diff| / max value {rel:.4f}",
                          flush=True)
                else:
                    f = GD / f"{c}_osm.csv"
                    tmp = f.with_suffix(".csv.tmp"); out.to_csv(tmp, index=False); os.replace(tmp, f)
                    print(f"  {c:<16} roads from {rid}", flush=True)
        except Exception as e:                                             # noqa: BLE001
            fails += 1
            print(f"  FAILED {rid}: {type(e).__name__}: {str(e)[:120]}", flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
