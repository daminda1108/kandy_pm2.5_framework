"""spatial_curve_fullrecord.py -- registered test B: the spatial learning curve on full station records.

Registration: docs/prereg_spatial_curve_full_record_2026-10-04.md (OSF id in
modular/spatial_curve_full/REGISTERED.json); an extension of OSF rqn4y (+ 26hp8, 4whsc, 4qs9c).

Everything is the registered pipeline, UNCHANGED, run in a separate directory `modular/spatial_curve_full/`
(the registered `spatial_curve/` is never written). Each frozen module is imported and only its
path constants are re-pointed. The one change is the record each candidate location contributes: its
full archive record instead of the registered one-year download window.

  --assemble    per candidate location: every cached unit (openaq_archive.py) -> the registered ingest
                transformation of spatial_curve_ingest.ingest_location, line for line (PM2.5 rows, UTC,
                hour floor, mean over the location's sensors) -> raw/{loc}.parquet
  --freeze      spatial_curve_freeze (D3, registered rule; --present-frac 0.70 --tag s70 for S-1)
  --frame       F1: the frame, reported first (primary, secondary, band arm, tropical counts)
  --cover       road-extract cover (D-6 rule: minimum-size set of Geofabrik extracts covering each
                city's padded tile box); clusters already covered keep the registered cover
  --extracts    retrieve missing extracts, MD5-verified (heavy: run under night_window.sh)
  --predictors  spatial_curve_predictors (D4: GEE, OSM extracts, benchmark grid, merge)
  --terrain / --greybox     spatial_curve_terrain, spatial_curve_greybox
  --analysis    spatial_curve_analysis with --defer-dl-arms (E0-E7; E8-E11 not re-run, as registered)
                any further arguments are passed through (e.g. --city-cache, --only-clusters, --frame-tag)

Usage: python scripts/spatial_curve_fullrecord.py --assemble | --freeze [args] | --frame | --cover |
       --extracts | --predictors [--stage ...] | --terrain | --greybox | --analysis [args]
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import night_guard                                                       # noqa: E402
import openaq_archive as oa                                              # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
OLD = MOD / "spatial_curve"
NEW = MOD / "spatial_curve_full"
RAW = NEW / "raw"
GEOFABRIK = REPO / "data" / "external" / "osm" / "geofabrik"
COVER_SHARE = 0.998                  # D-6: largest uncovered sliver 0.2 per cent of a box
UA = {"User-Agent": "kandy-pm25-research/1.0 (academic)"}


def _require_registered() -> None:
    f = NEW / "REGISTERED.json"
    if not f.exists() or not json.loads(f.read_text(encoding="utf-8")).get("osf"):
        raise SystemExit("REFUSED: test B runs on new records only after its registration is lodged "
                         "(modular/spatial_curve_full/REGISTERED.json with an OSF id)")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _setup() -> None:
    """The registered candidate list, byte-identical, in the new directory."""
    NEW.mkdir(parents=True, exist_ok=True)
    src, dst = OLD / "candidates.csv", NEW / "candidates.csv"
    if not dst.exists() or _sha(src) != _sha(dst):
        shutil.copy2(src, dst)
    assert _sha(src) == _sha(dst)


# ── assemble ──────────────────────────────────────────────────────────────────────────────────
def location_hourly(units: list[Path]) -> pd.DataFrame:
    """spatial_curve_ingest.ingest_location's processing, applied to the location's full record."""
    parts = [pd.read_parquet(f) for f in units]
    parts = [p for p in parts if len(p)]
    if not parts:
        return pd.DataFrame(columns=["datetime_utc", "pm25"])
    d = pd.concat(parts, ignore_index=True)
    d["datetime_utc"] = pd.to_datetime(d.datetime, utc=True, errors="coerce").dt.floor("h")
    d["value"] = pd.to_numeric(d.value, errors="coerce")
    d = d.dropna(subset=["datetime_utc", "value"])
    return d.groupby("datetime_utc", as_index=False).value.mean().rename(columns={"value": "pm25"})


def assemble() -> int:
    _require_registered()
    _setup()
    plan = pd.read_csv(oa.ARCH / "plan_b.csv")
    C = pd.read_csv(NEW / "candidates.csv")
    RAW.mkdir(parents=True, exist_ok=True)
    rows, missing = [], 0
    for loc in sorted(C.location_id.astype(int).unique()):
        ys = sorted(plan[plan["loc"] == loc].year.astype(int))
        units = [oa.unit_path(loc, y) for y in ys]
        if not all(u.exists() for u in units):
            missing += 1
            continue
        h = location_hourly(units)
        f = RAW / f"{loc}.parquet"
        tmp = f.with_suffix(".tmp")
        h.to_parquet(tmp, index=False); os.replace(tmp, f)
        meta = [json.loads(u.with_suffix(".json").read_text(encoding="utf-8")) for u in units]
        rows.append(dict(location_id=loc, years=len(ys), first_year=ys[0] if ys else None,
                         last_year=ys[-1] if ys else None, hours=len(h),
                         listed=sum(m["listed"] for m in meta), unparsable=sum(m["unparsable"] for m in meta)))
    L = pd.DataFrame(rows)
    L.to_csv(NEW / "assemble_log.csv", index=False)
    print(f"assembled {len(L)} locations ({int((L.hours > 0).sum())} with PM2.5), {missing} not assembled "
          f"(units missing); objects listed {int(L.listed.sum()):,}, unparsable {int(L.unparsable.sum())}")
    return 0 if missing == 0 else 3


# ── re-pointed frozen modules ─────────────────────────────────────────────────────────────────
def _freeze_mod():
    import spatial_curve_freeze as m
    m.SC, m.RAW = NEW, RAW
    return m


def _pred_mod():
    import spatial_curve_predictors as m
    m.SC, m.PRED = NEW, NEW / "predictors"
    m.PRED.mkdir(parents=True, exist_ok=True)
    m.PBF_COVER, m.SEGS = NEW / "osm_pbf_cover.csv", m.PRED / "pbf_segments"
    return m


def _run_main(mod, argv: list[str]) -> int:
    sys.argv = [mod.__file__, *argv]
    return int(mod.main() or 0)


def freeze(argv) -> int:
    _require_registered(); _setup()
    return _run_main(_freeze_mod(), argv)


def frame_report() -> int:
    """F1, reported before any curve."""
    out = {}
    for tag in ("", "_s70"):
        f = NEW / f"frame_cities{tag}.csv"
        if not f.exists():
            continue
        Cn = pd.read_csv(f)
        Co = pd.read_csv(OLD / f"frame_cities{tag}.csv")
        def counts(C):
            p = C[C.primary.astype(bool)]
            return dict(primary=int(len(p)), primary_sites=int(p.sites.sum()),
                        primary_countries=int(p.country.nunique()),
                        primary_by_band=p.band.value_counts().to_dict(),
                        secondary=int(C.secondary.astype(bool).sum()),
                        band_arm=int(C.band_arm.astype(bool).sum()),
                        tropical_or_deep_in_frame=int(C[(C.primary.astype(bool) | C.secondary.astype(bool)
                                                         | C.band_arm.astype(bool))
                                                        & C.band.isin(["tropical", "deep_tropical"])].shape[0]))
        out[tag or "registered"] = dict(full_record=counts(Cn), registered_one_year=counts(Co))
    (NEW / "F1_frame.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


# ── road-extract cover (D-6 rule) ─────────────────────────────────────────────────────────────
def _frame_sites() -> pd.DataFrame:
    P = _pred_mod()
    return P.frame_union()


def _sizes(ids: list[str], idx: dict) -> dict:
    cache_f = GEOFABRIK / "sizes.json"
    cache = json.loads(cache_f.read_text(encoding="utf-8")) if cache_f.exists() else {}
    for i in ids:
        if i in cache:
            continue
        req = urllib.request.Request(idx[i]["urls"]["pbf"], method="HEAD", headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            cache[i] = int(r.headers["Content-Length"])
    cache_f.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    return cache


def _min_size_cover(cand, part, size, area) -> list[str]:
    """D-6 rule: the set of extracts with the SMALLEST TOTAL SIZE whose polygons cover at least
    COVER_SHARE of the box. Exact branch-and-bound over candidates ordered by size."""
    from shapely.ops import unary_union
    need = COVER_SHARE * area.area
    order = sorted((i for i in cand if part[i].area > 0), key=lambda i: size[i])
    best = [None, float("inf")]

    def dfs(k, chosen, got, total):
        if total >= best[1]:
            return
        if got.area >= need:
            best[0], best[1] = list(chosen), total
            return
        for j in range(k, len(order)):
            i = order[j]
            if total + size[i] >= best[1]:
                break                                  # sorted by size: nothing later is cheaper
            new = unary_union([got, part[i]])
            if new.area - got.area <= 1e-12 * area.area:
                continue                               # adds nothing
            dfs(j + 1, chosen + [i], new, total + size[i])
    dfs(0, [], area.difference(area), 0)
    if best[0] is None:                                # nothing reaches the share: take everything useful
        return order
    return best[0]


def cover() -> int:
    from shapely.geometry import box, shape
    from shapely.ops import unary_union
    P = _pred_mod()
    sites = _frame_sites()
    old = pd.read_csv(OLD / "osm_pbf_cover.csv")
    j = json.loads((GEOFABRIK / "index-v1.json").read_text(encoding="utf-8"))
    idx = {f["properties"]["id"]: dict(f["properties"], geom=shape(f["geometry"]))
           for f in j["features"] if f.get("geometry") and f["properties"]["urls"].get("pbf")}
    rows = []
    for cl, g in sites.groupby("cluster"):
        if cl in set(old.cluster):
            rows.append(old[old.cluster == cl].iloc[0].to_dict())
            continue
        tiles = P._tiles(g)
        td = P.TILE_DEG
        area = unary_union([box(lo * td, la * td, (lo + 1) * td, (la + 1) * td) for la, lo in tiles])
        cand = [i for i, v in idx.items() if v["geom"].intersects(area)]
        size = _sizes(cand, idx)
        chosen = _min_size_cover(cand, {i: idx[i]["geom"].intersection(area) for i in cand}, size, area)
        cov = unary_union([idx[i]["geom"] for i in chosen]).intersection(area).area / area.area
        regs = [idx[i]["urls"]["pbf"].split("download.geofabrik.de/")[1].rsplit("-latest", 1)[0]
                for i in chosen]
        regs = [r.split("/")[-1] if not r.startswith("north-america/us/") else "us/" + r.split("/")[-1]
                for r in regs]
        rows.append(dict(cluster=int(cl), country=None, sites=len(g), regions="|".join(regs),
                         uncovered_pct=round(100 * (1 - cov), 3)))
        rows[-1]["_urls"] = "|".join(idx[i]["urls"]["pbf"] for i in chosen)
    D = pd.DataFrame(rows)
    D.drop(columns=["_urls"], errors="ignore").to_csv(NEW / "osm_pbf_cover.csv", index=False)
    need = sorted({u for us in D.get("_urls", pd.Series(dtype=str)).dropna() for u in us.split("|")})
    need = [u for u in need if not (GEOFABRIK / u.rsplit("/", 1)[1]).exists()]
    (NEW / "extracts_needed.txt").write_text("\n".join(need), encoding="utf-8")
    sz = _sizes([], idx)
    print(f"cover: {len(D)} clusters ({int(D.cluster.isin(old.cluster).sum())} kept from the registered "
          f"cover); extracts to retrieve: {len(need)}")
    for u in need:
        print("   ", u)
    return 0


def extracts() -> int:
    """Retrieve the extracts listed by --cover, each MD5-verified, atomically. Night window only."""
    need = [u for u in (NEW / "extracts_needed.txt").read_text(encoding="utf-8").split() if u]
    left = 0
    for u in need:
        dst = GEOFABRIK / u.rsplit("/", 1)[1]
        if dst.exists():
            continue
        night_guard.check(margin_s=1800)
        md5 = urllib.request.urlopen(urllib.request.Request(u + ".md5", headers=UA), timeout=60).read() \
            .decode().split()[0]
        part = dst.with_suffix(".part")
        h = hashlib.md5()
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120) as r, open(part, "wb") as f:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b); h.update(b)
                if night_guard.remaining() < 300:
                    break
        if h.hexdigest() != md5:
            part.unlink(missing_ok=True); left += 1
            print(f"  {dst.name}: incomplete or MD5 mismatch, will retry")
            continue
        (dst.parent / (dst.name + ".md5")).write_text(f"{md5}  {dst.name}\n", encoding="utf-8")
        os.replace(part, dst)
        print(f"  {dst.name}: {dst.stat().st_size / 1e6:.0f} MB, MD5 ok", flush=True)
    if left and night_guard.remaining() < 1800:
        return night_guard.COME_BACK_TOMORROW
    return 0 if left == 0 else 3


def predictors(argv) -> int:
    _require_registered()
    return _run_main(_pred_mod(), argv)


def terrain(argv) -> int:
    _require_registered()
    _pred_mod()                                    # terrain reads frame_union through the predictors module
    import spatial_curve_terrain as m
    m.SC = NEW
    return _run_main(m, argv)


def greybox(argv) -> int:
    """E7 per frame (deviation B-1, declared 2026-10-05 before scoring): on full records Medellín's best
    365-day window differs between the registered frame and S-1, and the frozen script requires one
    window shared by both frames. Each frame's E7 values are therefore computed over that frame's OWN
    window, by the frozen script run on a view holding only that frame."""
    _require_registered()
    import spatial_curve_greybox as m
    for tag in ("", "_s70"):
        view = NEW / f"_greybox_view{tag or '_registered'}"
        if view.exists():
            shutil.rmtree(view)
        view.mkdir()
        for n in (f"frame_cities{tag}.csv", f"frame_sites{tag}.csv"):
            shutil.copy2(NEW / n, view / n)
        m.SC = view
        rc = _run_main(m, argv)
        if rc:
            return rc
        shutil.copy2(view / "frame_greybox.csv", NEW / f"frame_greybox{tag}.csv")
    return 0


def analysis(argv) -> int:
    _require_registered()
    import spatial_curve_analysis as m
    m.SC, m.RAW = NEW, RAW
    # DEEP_DIRS is fixed at import from the ORIGINAL SC (spatial_curve/dl_out, the registered curve's
    # E10/E11 predictions). Test B does not re-run the deep arms, so nothing may be merged from there.
    m.DEEP_DIRS = [NEW / "dl_out"]
    assert not m.DEEP_DIRS[0].exists(), "test B has no deep-arm predictions"
    base_load = m.load_frame

    def load_frame():                                   # deviation B-1: each frame's own E7 values
        cities, sites, daily = base_load()
        if m.FRAME_TAG:
            gb = pd.read_csv(NEW / f"frame_greybox_{m.FRAME_TAG}.csv")[["site", "greybox"]]
            sites = sites.drop(columns=["greybox"], errors="ignore").merge(gb, on="site", how="left")
        return cities, sites, daily
    m.load_frame = load_frame
    if "--defer-dl-arms" not in argv and "--synthetic" not in argv and "--leakage-test" not in argv:
        argv = [*argv, "--defer-dl-arms"]            # E8-E11 are not re-run (registration Section 3)
    if "--with-tabpfn" in argv:
        raise SystemExit("REFUSED: the deep arms are not part of test B")
    return _run_main(m, argv)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__); return 1
    cmd, rest = sys.argv[1], sys.argv[2:]
    t = time.time()
    fn = {"--assemble": lambda: assemble(), "--freeze": lambda: freeze(rest), "--frame": frame_report,
          "--cover": cover, "--extracts": extracts, "--predictors": lambda: predictors(rest),
          "--terrain": lambda: terrain(rest), "--greybox": lambda: greybox(rest),
          "--analysis": lambda: analysis(rest)}.get(cmd)
    if fn is None:
        print(__doc__); return 1
    rc = fn()
    print(f"[{cmd}] exit {rc} in {(time.time() - t) / 60:.1f} min")
    return rc


if __name__ == "__main__":
    sys.exit(main())
