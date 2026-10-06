"""spatial_curve_predictors.py -- D4 of the spatial learning curve (OSF rqn4y, 2026-09-10).

Attaches the seven registered covariates to every site of the frozen frame:
  lc_built_2400 (the benchmark E1), lc_built_300, ntl_1000, pop_1000, ndvi_1000,
  road_major_300, dist_major_km.

GEE SURFACES are computed by build_lur_predictors.gee_city unchanged, so every raster, radius and
reduction scale is identical to the frame the project's earlier spatial tests used.

OSM ROADS are NOT computed by build_lur_predictors.osm_city, for two reasons found by reading it:
  * it sends ONE Overpass query per city bounding box for every road class. The dense networks in
    this frame are 25 km clusters around London, Seoul and Tokyo, and a single query for every
    residential and service way in that box is the timeout the plan registered a fallback for.
    Here the box is TILED, only tiles within reach of a site are queried, and ways are
    de-duplicated by their OSM id across tiles.
  * its site-by-segment loop is pure Python. On a megacity network that is hours. Here it is
    vectorised with numpy on segment midpoints, preserving osm_city's definitions exactly:
    a segment counts toward a buffer when its MIDPOINT lies within the radius, and its full
    length is added.
⚠ dist_major_km is the distance to the nearest major-road midpoint among the tiles fetched. A
site whose nearest major road lies beyond the fetched tiles gets an upper bound, the same limit
osm_city's padded box had. Tiles extend DIST_PAD_KM beyond every site to keep this rare.

RESUMABLE: one cached file per cluster and stage.

Usage: .venv/Scripts/python.exe scripts/spatial_curve_predictors.py [--stage gee|osm|merge|all]
Out:   data/processed/modular/spatial_curve/predictors/{cluster}_{gee,osm}.csv
       data/processed/modular/spatial_curve/frame_predictors.csv
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import build_lur_predictors as blp                                          # noqa: E402

SC = REPO / "data" / "processed" / "modular" / "spatial_curve"
PRED = SC / "predictors"
PRED.mkdir(parents=True, exist_ok=True)

COVARS = ["lc_built_2400", "lc_built_300", "ntl_1000", "pop_1000", "ndvi_1000",
          "road_major_300", "dist_major_km"]
TILE_DEG = 0.08                  # ~9 km tiles; small enough for Overpass in a dense city
REACH_KM = 1.2                   # widest road buffer is 1 km; osm_city's own cut-off
DIST_PAD_KM = 3.0                # extra reach for the nearest-major-road distance
OVERPASS = "https://overpass-api.de/api/interpreter"


# ── GEE ───────────────────────────────────────────────────────────────────────────────────────
def gee_stage(sites: pd.DataFrame) -> None:
    import ee
    ee.Initialize(project="kandypinn")
    for cl, g in sites.groupby("cluster"):
        f = PRED / f"{cl}_gee.csv"
        if cache_complete(f, g):
            continue
        t = time.time()
        g2 = g[["site", "lat", "lon"]].rename(columns={"site": "station_id"})
        out = blp.gee_city(g2)
        tmp = f.with_suffix(".tmp")
        out.rename(columns={"station_id": "site"}).to_csv(tmp, index=False)
        tmp.replace(f)
        print(f"  gee  cluster {cl}: {len(g)} sites in {time.time() - t:.0f} s", flush=True)


# ── OSM ───────────────────────────────────────────────────────────────────────────────────────
STATUS = "https://overpass-api.de/api/status"


def _wait_for_slot(max_wait=600):
    """Block until Overpass reports a free slot for this client, using its own announced times."""
    import re as _re
    from datetime import datetime, timezone
    t0 = time.time()
    while time.time() - t0 < max_wait:
        try:
            req = urllib.request.Request(STATUS, headers=blp.UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                txt = r.read().decode("utf-8", "replace")
        except Exception:                                                  # noqa: BLE001
            time.sleep(10)
            continue
        if "slots available now" in txt:
            return
        waits = []
        for m in _re.finditer(r"Slot available after: (\S+Z)", txt):
            try:
                at = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                waits.append((at - datetime.now(timezone.utc)).total_seconds())
            except ValueError:
                pass
        time.sleep(max(2.0, min(waits) + 1.0) if waits else 5.0)


def _query(s, w, n, e, tries=4):
    q = (f"[out:json][timeout:180];way[highway~\"^(motorway|trunk|primary|secondary|"
         f"tertiary|residential|unclassified|living_street|service)"
         f"(_link)?$\"]({s},{w},{n},{e});out geom;")
    for t in range(tries):
        try:
            _wait_for_slot()
            req = urllib.request.Request(OVERPASS, data=q.encode(), headers=blp.UA)
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except Exception as ex:                                            # noqa: BLE001
            if t == tries - 1:
                raise RuntimeError(f"Overpass failed for tile {s:.3f},{w:.3f}: {ex}") from ex
            time.sleep(30 * (t + 1))


def _tiles(g: pd.DataFrame):
    """Tiles of TILE_DEG covering every site's reach; only tiles a site can actually use."""
    lat0 = float(g.lat.mean())
    dlat = (REACH_KM + DIST_PAD_KM) / 110.57
    dlon = (REACH_KM + DIST_PAD_KM) / (111.32 * np.cos(np.radians(lat0)))
    need = set()
    for r in g.itertuples():
        for la in np.arange(r.lat - dlat, r.lat + dlat + 1e-9, TILE_DEG / 2):
            for lo in np.arange(r.lon - dlon, r.lon + dlon + 1e-9, TILE_DEG / 2):
                need.add((int(np.floor(la / TILE_DEG)), int(np.floor(lo / TILE_DEG))))
    return sorted(need)


def osm_city_tiled(g: pd.DataFrame) -> pd.DataFrame:
    ways = {}
    tiles = _tiles(g)
    t_city = time.time()
    for ti, (i, j) in enumerate(tiles, 1):
        s, w = i * TILE_DEG, j * TILE_DEG
        t_tile = time.time()
        data = _query(s, w, s + TILE_DEG, w + TILE_DEG)
        print(f"      tile {ti}/{len(tiles)}: {len(data.get('elements', [])):,} ways in "
              f"{time.time() - t_tile:.0f} s (city {(time.time() - t_city) / 60:.1f} min)", flush=True)
        for el in data.get("elements", []):
            if el.get("id") in ways or not el.get("geometry"):
                continue
            tag = (el.get("tags") or {}).get("highway", "")
            cls = next((k for k, v in blp.ROAD_CLASSES.items() if tag in v), None)
            if cls:
                ways[el["id"]] = (cls, [(p["lat"], p["lon"]) for p in el["geometry"]])

    mids, lens, cls_of = [], [], []
    for cls, pts in ways.values():
        m, l_ = _segments(pts)
        if len(m):
            mids.append(m); lens.append(l_); cls_of += [cls] * len(m)
    if not mids:
        return _road_features(g, np.empty((0, 2)), np.empty(0), np.empty(0, dtype=object))
    return _road_features(g, np.vstack(mids), np.concatenate(lens), np.asarray(cls_of))


def _segments(pts):
    """Midpoints and haversine lengths (km) of a polyline's segments, as osm_city defines them."""
    p = np.asarray(pts, float)
    a, b = p[:-1], p[1:]
    if not len(a):
        return np.empty((0, 2)), np.empty(0)
    la1, lo1, la2, lo2 = map(np.radians, (a[:, 0], a[:, 1], b[:, 0], b[:, 1]))
    h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return (a + b) / 2, 2 * 6371.0 * np.arcsin(np.sqrt(h))


def _road_features(g, M, L, K):
    """Per site: road length by class within each radius (a segment counts when its MIDPOINT is
    inside the radius, with its full length) and distance to the nearest major-road midpoint."""
    out = g.reset_index(drop=True).copy()
    for c in blp.ROAD_CLASSES:
        for rad in blp.ROAD_RADII:
            out[f"road_{c}_{rad}"] = 0.0
    out["dist_major_km"] = np.nan
    if not len(M):
        return out
    mla, mlo = np.radians(M[:, 0]), np.radians(M[:, 1])
    for i, r in enumerate(out.itertuples()):
        p1, l1 = np.radians(r.lat), np.radians(r.lon)
        h = np.sin((mla - p1) / 2) ** 2 + np.cos(p1) * np.cos(mla) * np.sin((mlo - l1) / 2) ** 2
        d = 2 * 6371.0 * np.arcsin(np.sqrt(h))           # same haversine as osm_city
        maj = K == "major"
        if maj.any():
            out.at[i, "dist_major_km"] = float(d[maj].min())
        for c in blp.ROAD_CLASSES:
            m = K == c
            for rad in blp.ROAD_RADII:
                out.at[i, f"road_{c}_{rad}"] = float(L[m & (d <= rad / 1000.0)].sum())
    return out


def osm_stage(sites: pd.DataFrame) -> None:
    for cl, g in sites.groupby("cluster"):
        f = PRED / f"{cl}_osm.csv"
        if cache_complete(f, g):
            continue
        t = time.time()
        try:
            out = osm_city_tiled(g[["site", "lat", "lon"]])
        except Exception as ex:                                            # noqa: BLE001
            print(f"  osm  cluster {cl}: FAILED {ex}  (re-run to retry)", flush=True)
            continue
        tmp = f.with_suffix(".tmp")
        out.to_csv(tmp, index=False)
        tmp.replace(f)
        print(f"  osm  cluster {cl}: {len(g)} sites in {time.time() - t:.0f} s", flush=True)


# ── OSM from Geofabrik extracts (declared 2026-09-11) ─────────────────────────────────────────
# Overpass ran at ~20 min per city (13-16 h for the frame), almost all of it queueing for a public
# slot. The same OSM ways are read here from Geofabrik extracts. Definitions are unchanged: the
# same highway values and classes, the same segment midpoint rule, the same haversine. What
# differs: (a) the data are one Geofabrik snapshot rather than live Overpass; (b) a segment enters
# a city when its MIDPOINT lies in one of the city's tiles, where Overpass took whole ways touching
# a tile. Tiles reach 4.2 km beyond every site and the widest buffer is 1 km, so every road_*
# value is identical by construction; only dist_major_km beyond the pad can differ, and it was
# already an upper bound there. Every city is recomputed from the extracts, including those
# Overpass finished, so the frame rests on one snapshot; the Overpass files are kept as a check.
GEOFABRIK = REPO / "data" / "external" / "osm" / "geofabrik"
PBF_COVER = SC / "osm_pbf_cover.csv"         # cluster -> minimal set of extracts covering its tiles
SEGS = PRED / "pbf_segments"


def _region_file(region: str) -> Path:
    return GEOFABRIK / f"{region.split('/')[-1]}-latest.osm.pbf"


def scan_region(region: str, tiles: set) -> Path:
    """One pass over an extract: every classed highway segment whose midpoint falls in `tiles`.
    Cached as parquet per region, so a restart never re-reads a finished extract."""
    import osmium
    f = SEGS / f"{region.replace('/', '_')}.parquet"
    if f.exists():
        return f
    SEGS.mkdir(parents=True, exist_ok=True)
    cls_of = {v: k for k, vs in blp.ROAD_CLASSES.items() for v in vs}
    fp = (osmium.FileProcessor(str(_region_file(region)))
          .with_locations()
          .with_filter(osmium.filter.EntityFilter(osmium.osm.WAY))
          .with_filter(osmium.filter.TagFilter(*[("highway", v) for v in cls_of])))
    rows = {k: [] for k in ("way", "seg", "cls", "mlat", "mlon", "len_km")}
    t = time.time()
    for w in fp:
        pts = [(n.lat, n.lon) for n in w.nodes if n.location.valid()]
        if len(pts) < 2:
            continue
        m, l_ = _segments(pts)
        keep = [i for i in range(len(m))
                if (int(np.floor(m[i, 0] / TILE_DEG)), int(np.floor(m[i, 1] / TILE_DEG))) in tiles]
        if not keep:
            continue
        c = cls_of[w.tags["highway"]]
        for i in keep:
            rows["way"].append(w.id); rows["seg"].append(i); rows["cls"].append(c)
            rows["mlat"].append(m[i, 0]); rows["mlon"].append(m[i, 1]); rows["len_km"].append(l_[i])
    out = pd.DataFrame(rows)
    tmp = f.with_suffix(".tmp")
    out.to_parquet(tmp, index=False)
    tmp.replace(f)
    print(f"  pbf  {region}: {len(out):,} segments in {out.way.nunique():,} ways, "
          f"{time.time() - t:.0f} s", flush=True)
    return f


def osmpbf_stage(sites: pd.DataFrame) -> None:
    cover = pd.read_csv(PBF_COVER).set_index("cluster").regions.str.split("|")
    need = {}
    for cl, g in sites.groupby("cluster"):
        for r in cover.loc[cl]:
            need.setdefault(r, set()).update(_tiles(g))
    missing = [r for r in need if not _region_file(r).exists()]
    if missing:
        print(f"extracts not yet downloaded: {missing}; their cities are skipped this run")
    for r in sorted(need, key=lambda r: _region_file(r).stat().st_size if _region_file(r).exists() else 0):
        if r not in missing:
            scan_region(r, need[r])
    for cl, g in sites.groupby("cluster"):
        f = PRED / f"{cl}_osmpbf.csv"
        regs = cover.loc[cl]
        if cache_complete(f, g) or any(r in missing for r in regs):
            continue
        tiles = _tiles(g)
        S = pd.concat([pd.read_parquet(SEGS / f"{r.replace('/', '_')}.parquet") for r in regs],
                      ignore_index=True).drop_duplicates(["way", "seg"])  # overlapping extracts
        key = list(zip(np.floor(S.mlat / TILE_DEG).astype(int), np.floor(S.mlon / TILE_DEG).astype(int)))
        S = S[[k in tiles for k in key]]
        out = _road_features(g[["site", "lat", "lon"]], S[["mlat", "mlon"]].to_numpy(),
                             S.len_km.to_numpy(), S.cls.to_numpy())
        tmp = f.with_suffix(".tmp")
        out.to_csv(tmp, index=False)
        tmp.replace(f)
        print(f"  osmpbf cluster {cl}: {len(g)} sites from {'+'.join(regs)}", flush=True)


def merge_stage(sites: pd.DataFrame) -> int:
    parts, missing = [], []
    for cl, g in sites.groupby("cluster"):
        fg, fo = PRED / f"{cl}_gee.csv", PRED / f"{cl}_osmpbf.csv"      # one snapshot for all
        if not (fg.exists() and fo.exists()):
            missing.append(int(cl))
            continue
        a = pd.read_csv(fg)
        b = pd.read_csv(fo)
        rc = [c for c in b.columns if c.startswith("road_") or c == "dist_major_km"]
        parts.append(a.merge(b[["site"] + rc], on="site", how="left"))
    if missing:
        print(f"clusters without both stages: {missing}. Not merging; re-run the missing stage.")
        return 1
    P = pd.concat(parts, ignore_index=True)
    bad = P[COVARS].isna().sum()
    print("missing values per registered covariate:", bad[bad > 0].to_dict() or "none")
    tmp = SC / "frame_predictors.tmp"
    P.to_csv(tmp, index=False)
    tmp.replace(SC / "frame_predictors.csv")
    print(f"wrote frame_predictors.csv: {len(P)} sites, {P.cluster.nunique() if 'cluster' in P else '?'} clusters")
    return 0



def frame_union() -> pd.DataFrame:
    """Sites of every frame city in the registered frame and in any sensitivity frame."""
    parts = []
    for sfx in ("", "_s70"):
        fs, fc = SC / f"frame_sites{sfx}.csv", SC / f"frame_cities{sfx}.csv"
        if not (fs.exists() and fc.exists()):
            continue
        c = pd.read_csv(fc)
        keep = c[c.primary.astype(bool) | c.secondary.astype(bool) | c.band_arm.astype(bool)].cluster
        s_ = pd.read_csv(fs)
        parts.append(s_[s_.cluster.isin(keep)][["cluster", "site", "lat", "lon"]])
        print(f"  frame{sfx or ' (registered)'}: {len(parts[-1])} sites in {parts[-1].cluster.nunique()} cities")
    U = pd.concat(parts, ignore_index=True).drop_duplicates("site")
    # one site id, one location: a mismatch would mean the id is not stable across frames
    return U


def cache_complete(f: Path, g: pd.DataFrame) -> bool:
    if not f.exists():
        return False
    have = set(pd.read_csv(f, usecols=["site"]).site.astype(str))
    return set(g.site.astype(str)) <= have


BENCH_RADIUS_M = 2400
BENCH_SCALE_M = 240              # gee_city reduces at max(30, rad // 10)
GRID_KM = 1.0
GRID_PAD_KM = 3.0


def raster_stage(sites: pd.DataFrame) -> None:
    """E10's gridded auxiliary: the benchmark covariate on a 1 km grid, computed as for a site."""
    import ee
    ee.Initialize(project="kandypinn")
    lc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map")
    built = lc.eq(50).rename("lc_built").toFloat()
    for cl, g in sites.groupby("cluster"):
        f = PRED / f"{cl}_bench_grid.csv"
        if f.exists():
            continue
        t = time.time()
        lat0 = float(g.lat.mean())
        dlat = GRID_KM / 110.57
        dlon = GRID_KM / (111.32 * np.cos(np.radians(lat0)))
        plat = GRID_PAD_KM / 110.57
        plon = GRID_PAD_KM / (111.32 * np.cos(np.radians(lat0)))
        lats = np.arange(g.lat.min() - plat, g.lat.max() + plat + 1e-9, dlat)
        lons = np.arange(g.lon.min() - plon, g.lon.max() + plon + 1e-9, dlon)
        pts = [(la, lo) for la in lats for lo in lons]
        vals = []
        for i in range(0, len(pts), 400):
            chunk = pts[i:i + 400]
            fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([lo, la]).buffer(BENCH_RADIUS_M),
                                                  {"k": j}) for j, (la, lo) in enumerate(chunk)])
            res = built.reduceRegions(collection=fc, reducer=ee.Reducer.mean(),
                                      scale=BENCH_SCALE_M).getInfo()
            got = {int(ft["properties"]["k"]): ft["properties"].get("mean") for ft in res["features"]}
            vals += [got.get(j, np.nan) for j in range(len(chunk))]
        out = pd.DataFrame(pts, columns=["lat", "lon"])
        out["lc_built_2400"] = vals
        tmp = f.with_suffix(".tmp")
        out.to_csv(tmp, index=False)
        tmp.replace(f)
        print(f"  raster cluster {cl}: {len(lats)} x {len(lons)} grid in {time.time() - t:.0f} s",
              flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["gee", "osm", "osmpbf", "raster", "merge", "all"],
                    default="all")
    a = ap.parse_args()
    sites = frame_union()
    print(f"{len(sites)} sites in {sites.cluster.nunique()} frame cities")
    if a.stage in ("gee", "all"):
        gee_stage(sites)
    if a.stage == "osm":                       # Overpass: kept as a cross-check, not in "all"
        osm_stage(sites)
    if a.stage in ("osmpbf", "all"):
        osmpbf_stage(sites)
    if a.stage in ("raster", "all"):
        raster_stage(sites)
    if a.stage in ("merge", "all"):
        return merge_stage(sites)
    return 0


if __name__ == "__main__":
    sys.exit(main())
