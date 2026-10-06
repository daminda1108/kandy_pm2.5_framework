"""ladder_v2_fullnet.py -- registered test A: does the confirmed ladder depend on the station cap?

Registration: docs/prereg_full_network_ladder_2026-10-04.md (OSF id in modular/fullnet/REGISTERED.json).
The estimator is the frozen ladder v2 (`ladder_v2.run`, `ladder_v2_confirm.union`), UNCHANGED. Only the
OpenAQ station files differ. They are read from MIRROR directories that hold byte-identical
(SHA-256-verified) copies of every other input, so the frozen code runs with nothing but its two path
constants re-pointed (`modular_validation_all.MOD` for discovery stations, `ladder_v2_confirm.CD` for
confirmation stations). Three arms:

  original  mirror of the ORIGINAL capped station files. PARITY GATE: must reproduce the registered
            confirmation (OSF ueyfr) per-city effects exactly, proving the re-pointing is inert.
  capped    the old cap (12 locations by record span, the last two calendar years of those 12) re-applied
            to the newly retrieved records. REPRODUCTION CHECK: reported, not a gate.
  full      every cluster member ranked by record span, up to 40, over the city's full driver window.

Station files are built from the shared unit cache (`openaq_archive.py`) with the transformation of
`ingest_openaq_sample.ingest_city`, line for line: parse `datetime` as UTC and drop the zone, `value` to
numeric, drop missing, keep (0, 1000), floor to the hour, mean per (location, hour).

Endpoints (confirmation panel, reconstruction arm, two-level cluster bootstrap, 95 %):
  N1 first2_rmse lower > 0 | N2 s36_rmse inside [-1, +1] | N3 bg_rmse lower > 0
  N4 bgm2_rmse two-sided, ordering only if 0 excluded | N5 bgm2_exceed lower > 0
  N6 per-city paired change, full minus the REGISTERED ueyfr value, in bg_rmse, bgm2_rmse and bgm2_exceed:
     median over cities, two-level cluster bootstrap, two-sided. (Secondary: the same against the capped arm.)

Usage:
  python scripts/ladder_v2_fullnet.py --build full|capped          # station files from the unit cache
  python scripts/ladder_v2_fullnet.py --mirror original|capped|full
  python scripts/ladder_v2_fullnet.py --score original|capped|full [--dry-run]
  python scripts/ladder_v2_fullnet.py --endpoints                    # N1-N6 after the three scores
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import openaq_archive as oa                                               # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
CD = MOD / "confirmation"
FN = MOD / "fullnet"
OUTD = MOD / "ladder_v2"
ARMS = ("original", "capped", "full")
SEED_BOOT = 20261004


def _require_registered() -> dict:
    f = FN / "REGISTERED.json"
    if not f.exists() or not json.loads(f.read_text(encoding="utf-8")).get("osf"):
        raise SystemExit("REFUSED: test A runs on new records only after its registration is lodged "
                         "(modular/fullnet/REGISTERED.json with an OSF id)")
    return json.loads(f.read_text(encoding="utf-8"))


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _atomic_parquet(d: pd.DataFrame, f: Path) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    d.to_parquet(tmp, index=False)
    os.replace(tmp, f)


# ── station files from the unit cache ─────────────────────────────────────────────────────────
def hourly(used: pd.DataFrame, years: list[int]) -> pd.DataFrame | None:
    """ingest_city's transformation applied to the cached units of `used` x `years`."""
    frames = []
    for r in used.itertuples():
        for y in years:
            f = oa.unit_path(int(r.loc_id), int(y))
            if not f.exists():
                raise FileNotFoundError(f"unit {int(r.loc_id)}/{y} not retrieved")
            d = pd.read_parquet(f)
            if len(d):
                d["loc_id"] = int(r.loc_id)
                frames.append(d)
    if not frames:
        return None
    x = pd.concat(frames, ignore_index=True)
    tcol = "datetime" if "datetime" in x.columns else x.columns[0]
    x["datetime_utc"] = pd.to_datetime(x[tcol], errors="coerce", utc=True).dt.tz_localize(None)
    x["pm25"] = pd.to_numeric(x.get("value"), errors="coerce")
    x = x.dropna(subset=["datetime_utc", "pm25"])
    x = x[(x.pm25 > 0) & (x.pm25 < 1000)]
    x["datetime_utc"] = x.datetime_utc.dt.floor("h")
    g = (x.groupby(["loc_id", "datetime_utc"]).pm25.mean().reset_index()
         .merge(used[["loc_id", "lat", "lon", "provider", "is_monitor"]], on="loc_id", how="left"))
    return g.rename(columns={"loc_id": "station_id"})


def build(arm: str) -> int:
    _require_registered()
    import ingest_openaq_sample as ios
    rows, missing = [], 0
    for c in oa.a_cities():
        if arm == "full":
            used = c["locs"].head(oa.A_MAX)
            years = list(range(c["w0"].year, c["w1"].year + 1))
        else:
            used = c["locs"].head(oa.A_CAP)
            years = ios.city_years(used)
        try:
            g = hourly(used, years)
        except FileNotFoundError as e:
            missing += 1
            print(f"  {c['city']:<16} NOT BUILT: {e}")
            continue
        f = FN / arm / c["panel"] / f"{c['city']}.parquet"
        r = dict(panel=c["panel"], city=c["city"], locs_available=len(c["locs"]), locs_used=len(used),
                 years=f"{years[0]}-{years[-1]}", stations=0 if g is None else int(g.station_id.nunique()),
                 rows=0 if g is None else len(g))
        if g is not None:
            _atomic_parquet(g, f)
        rows.append(r)
    M = pd.DataFrame(rows)
    M.to_csv(FN / f"build_manifest_{arm}.csv", index=False)
    print(M.groupby("panel")[["locs_used", "stations"]].median().to_string())
    print(f"{arm}: {len(M)} cities built, {missing} not built (units missing)")
    return 0 if missing == 0 else 3


# ── mirrors: byte-identical copies of every non-station input ─────────────────────────────────
def mirror(arm: str) -> Path:
    """MOD-like and CD-like directories for one arm. Station files come from the arm; every other file
    is copied and its SHA-256 checked against the original."""
    root = FN / f"mirror_{arm}"
    if root.exists():
        shutil.rmtree(root)
    disc, conf = root / "disc", root / "conf"
    checks = []

    def cp(src: Path, dst: Path):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        assert _sha(src) == _sha(dst), f"copy differs: {src}"
        checks.append((str(src.relative_to(REPO)), _sha(dst)))

    for f in sorted((MOD / "drivers").glob("*.csv")):
        cp(f, disc / "drivers" / f.name)
    for name in ("confirmation_panel.csv", "static_geo_grid.csv"):
        cp(CD / name, conf / name)
    for sub in ("drivers", "aod"):
        for f in sorted((CD / sub).glob("*.csv")):
            cp(f, conf / sub / f.name)
    # the arm's station files
    if arm == "original":
        for f in sorted((MOD / "openaq").glob("*.parquet")):
            cp(f, disc / "openaq" / f.name)
        for f in sorted((CD / "openaq").glob("*.parquet")):
            cp(f, conf / "openaq" / f.name)
        cp(CD / "REGISTERED.json", conf / "REGISTERED.json")
    else:
        (disc / "openaq").mkdir(parents=True, exist_ok=True)
        for f in sorted((FN / arm / "discovery").glob("*.parquet")):
            shutil.copy2(f, disc / "openaq" / f.name)
        (conf / "openaq").mkdir(parents=True, exist_ok=True)
        for f in sorted((FN / arm / "confirmation").glob("*.parquet")):
            shutil.copy2(f, conf / "openaq" / f.name)
        shutil.copy2(FN / "REGISTERED.json", conf / "REGISTERED.json")
    (root / "mirror_checks.json").write_text(json.dumps(checks, indent=1), encoding="utf-8")
    print(f"mirror {arm}: {len(checks)} files copied and verified by SHA-256")
    return root


def _point(root: Path) -> None:
    """Re-point the frozen modules' two path constants. Nothing else changes."""
    import ladder_v2_confirm as lvc
    import modular_validation_all as mva
    mva.MOD = root / "disc"
    lvc.CD = root / "conf"


# ── scoring ───────────────────────────────────────────────────────────────────────────────────
def score(arm: str, dry_run: bool, splits: int, bag: int, boot: int) -> int:
    if arm != "original":
        _require_registered()
    root = FN / f"mirror_{arm}"
    if not root.exists():
        raise SystemExit(f"{root} missing: run --mirror {arm}")
    _point(root)
    import ladder_v2_confirm as lvc
    from ladder_v2 import run
    frame, meta, score_cities, dropped = lvc.union("maiac")
    if dry_run:
        from ladder_v2_rich import synthetic
        st, p, met, geo_f, sat = frame
        st, p = synthetic(st, p)
        frame = (st, p, met, geo_f, sat)
    print(f"[{arm}{' DRY-RUN' if dry_run else ''}] union {len(frame[0])} cities; scoring "
          f"{len(score_cities)}; dropped {dropped}", flush=True)
    S, percity, res = run("maiac", splits, bag, "crossfit", True, "grid", boot, True,
                          frame=frame, meta=meta, score_cities=score_cities)
    res["dropped"] = dropped
    tag = f"fullnet_{'dryrun_' if dry_run else ''}{arm}"
    OUTD.mkdir(parents=True, exist_ok=True)
    S.to_csv(OUTD / f"{tag}_splits.csv", index=False)
    for k, C in percity.items():
        C.to_csv(OUTD / f"{tag}_percity_{k}.csv")
    if arm == "original" and not dry_run:                     # the parity gate
        R = pd.read_csv(OUTD / "confirm_REGISTERED_percity_reconstruction.csv", index_col=0)
        B = percity["reconstruction"]
        cols = [c for c in R.columns if c.split("_")[0] in ("first2", "s36", "bg", "bgm2")]
        common = [c for c in R.index if c in B.index]
        diff = float((B.loc[common, cols] - R.loc[common, cols]).abs().max().max())
        res["parity_max_abs_diff"] = diff
        res["parity_cities"] = [len(common), len(R)]
        print(f"PARITY: {len(common)}/{len(R)} cities, max |diff| {diff:.3g}")
        assert len(common) == len(R), "parity: confirmation cities lost"
        assert diff < 1e-9, f"parity FAILED: the re-pointed run does not reproduce ueyfr ({diff})"
    jp = OUTD / f"{tag}_summary.json"
    tmp = jp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(res, indent=2), encoding="utf-8"); os.replace(tmp, jp)
    print(f"-> {jp}")
    return 0


def _boot(v, grp, rng, n):
    from ladder_v2 import boot_city, boot_cluster
    v, grp = np.asarray(v, float), np.asarray(grp)
    k = ~np.isnan(v); v, grp = v[k], grp[k]
    bc, bk = boot_city(v, rng, n), boot_cluster(v, grp, rng, n)
    return dict(n=int(len(v)), n_clusters=int(len(np.unique(grp))), median=float(np.median(v)),
                city=[float(np.percentile(bc, 2.5)), float(np.percentile(bc, 97.5))],
                cluster=[float(np.percentile(bk, 2.5)), float(np.percentile(bk, 97.5))])


def endpoints(boot: int) -> int:
    _require_registered()
    full = json.loads((OUTD / "fullnet_full_summary.json").read_text(encoding="utf-8"))["reconstruction"]
    out = {}
    rule = {"N1": ("first2_rmse", "lower>0"), "N2": ("s36_rmse", "inside[-1,1]"),
            "N3": ("bg_rmse", "lower>0"), "N4": ("bgm2_rmse", "two-sided"),
            "N5": ("bgm2_exceed", "lower>0")}
    for n, (k, r) in rule.items():
        e = full[f"pooled.{k}"]; lo, hi = e["cluster"]
        verdict = {"lower>0": "SUPPORTED" if lo > 0 else "NOT SUPPORTED",
                   "inside[-1,1]": "SUPPORTED" if (lo >= -1 and hi <= 1) else "NOT SUPPORTED",
                   "two-sided": ("ORDERING: background > first two" if lo > 0 else
                                 "ORDERING: first two > background" if hi < 0 else "NO ORDERING")}[r]
        out[n] = dict(key=k, rule=r, **e, verdict=verdict)
    F = pd.read_csv(OUTD / "fullnet_full_percity_reconstruction.csv", index_col=0)
    refs = {"registered_ueyfr": OUTD / "confirm_REGISTERED_percity_reconstruction.csv",
            "capped_arm": OUTD / "fullnet_capped_percity_reconstruction.csv"}
    rng = np.random.default_rng(SEED_BOOT)
    for name, p in refs.items():
        if not p.exists():
            continue
        R = pd.read_csv(p, index_col=0)
        common = [c for c in R.index if c in F.index]
        for k in ("bg_rmse", "bgm2_rmse", "bgm2_exceed"):
            d = F.loc[common, k] - R.loc[common, k]
            e = _boot(d.to_numpy(), F.loc[common, "cluster"].to_numpy(), rng, boot)
            lo, hi = e["cluster"]
            out[f"N6.{name}.{k}"] = dict(**e, verdict="excludes 0" if (lo > 0 or hi < 0) else "includes 0",
                                        primary=(name == "registered_ueyfr"))
    jp = OUTD / "fullnet_endpoints.json"
    jp.write_text(json.dumps(out, indent=2), encoding="utf-8")
    for k, v in out.items():
        print(f"  {k:<34} n={v['n']:>3} {v['median']:+8.2f} [{v['cluster'][0]:+.2f}, {v['cluster'][1]:+.2f}]"
              f"  {v['verdict']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--build", choices=["full", "capped"])
    g.add_argument("--mirror", choices=ARMS)
    g.add_argument("--score", choices=ARMS)
    g.add_argument("--endpoints", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--splits", type=int, default=21)
    ap.add_argument("--bag", type=int, default=5)
    ap.add_argument("--boot", type=int, default=4000)
    a = ap.parse_args()
    if a.build:
        return build(a.build)
    if a.mirror:
        mirror(a.mirror); return 0
    if a.score:
        return score(a.score, a.dry_run, a.splits, a.bag, a.boot)
    return endpoints(a.boot)


if __name__ == "__main__":
    sys.exit(main())
