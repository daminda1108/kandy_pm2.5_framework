"""Consolidate every E8/E9 (TabPFN) output into ONE predictions file per frame, for merge_deep.

WHY THIS STEP EXISTS (2026-09-15). E8/E9 were scored across sessions that were killed at Kaggle's
12 h wall and resumed, on two devices (GPU, then CPU). Three facts make a naive merge wrong:
  * merge_deep reads ONLY `pred_*.parquet`, and a killed session leaves only `partial_*` files --
    82,804 already-scored rows would silently never reach the summary;
  * a resumed session's final `pred_*` holds only THAT session's rows, not the resumed ones;
  * a city interrupted mid-way appears in an earlier partial (Q1 only) AND, complete, in a later
    file. merge_deep takes the median over duplicate keys, so an overlap would quietly average two
    scorings of one task.
Rule: a (frame, cluster) is taken from exactly ONE source file -- the one holding it complete (both
designs), preferring the file with the most rows for it -- and cities not complete anywhere are
reported and left out, never half-merged. Give the summary run ONLY the consolidated file.

Usage: python spatial_curve_tabpfn_consolidate.py <dir-with-tabpfn-parquets>... --out <dir> [--dry-run]
"""
import argparse, sys
from pathlib import Path
import pandas as pd

KEY = ["frame", "design", "cluster", "rep", "k", "day", "est"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cities", default="", help="cities.parquet: refuse unless every registered city is present")
    ap.add_argument("--allow-incomplete", action="store_true", help="rehearsal only")
    ap.add_argument("--splits-dir", default="", help="expect only cities that have splits here")
    a = ap.parse_args()
    found = sorted({f for d in a.dirs for f in Path(d).rglob("*tabpfn*.parquet")
                    if f.name.startswith(("partial_", "pred_"))
                    and not f.name.startswith("pred_tabpfn_consolidated_")})
    # D-8: CPU-scored sources only. The CPU kernels tag every output `_cpu_`; anything else is
    # GPU-era (archived, never merged) and is listed, not silently dropped.
    files = [f for f in found if "_cpu_" in f.name]
    for f in found:
        if "_cpu_" not in f.name:
            print(f"  D-8 EXCLUDED (not CPU-scored): {f}", flush=True)
    if not files:
        print("no CPU-scored tabpfn parquets found"); return 1
    parts = []
    for f in files:
        # Keyed by FULL PATH (2026-09-24): by name alone, two runs' same-named files in different
        # folders were merged as one "source" (141,610 duplicate keys, caught by the check below).
        P = pd.read_parquet(f); P["source"] = str(f.resolve()); parts.append(P)
        print(f"  {f.name}: {len(P):,} rows, {P.groupby(['frame','cluster']).ngroups} (frame, city)", flush=True)
    P = pd.concat(parts, ignore_index=True)

    # completeness per (source, frame, cluster): both designs present
    per = P.groupby(["source", "frame", "cluster"]).agg(designs=("design", "nunique"), rows=("rho", "size")).reset_index()
    complete = per[per.designs >= 2].sort_values(["frame", "cluster", "rows"], ascending=[True, True, False])
    chosen = complete.drop_duplicates(["frame", "cluster"])
    keep = P.merge(chosen[["source", "frame", "cluster"]], on=["source", "frame", "cluster"])
    dup = int(keep.duplicated(KEY).sum())
    if dup:
        print(f"REFUSING: {dup} duplicate task keys inside chosen sources"); return 2

    # 2026-09-24: five Kaggle kernels "completed" with 0 finite rows in 130,000+ (tabpfn 9.0.0 licence
    # error swallowed by predict_all's bare except). Rows are not results: refuse any chosen city
    # whose E8/E9 values are all NaN.
    fin = keep.groupby(["frame", "cluster", "est"]).rho.apply(lambda s: int(s.notna().sum()))
    dead = sorted({(f, int(c)) for (f, c, _), n in fin.items() if n == 0})
    if dead:
        print(f"REFUSING: {len(dead)} (frame, city) with NO finite E8/E9 value (TabPFN never "
              f"produced a prediction): {dead[:12]}{' ...' if len(dead) > 12 else ''}"); return 4
    allc = P.groupby(["frame", "cluster"]).size().index
    got = set(map(tuple, chosen[["frame", "cluster"]].to_numpy()))
    incomplete = sorted((f, int(c)) for f, c in allc if (f, c) not in got)
    for frame, g in keep.groupby("frame"):
        print(f"{frame}: {g.cluster.nunique()} complete cities, {len(g):,} rows, "
              f"finite {int(g.rho.notna().sum()):,}", flush=True)
    print(f"incomplete everywhere (left out, to be scored): {incomplete or 'none'}", flush=True)
    # Every city the frame registers must be present: a city that never appears in any file is
    # invisible to the check above (it has no rows to be incomplete in).
    missing = {}
    if a.cities:
        C = pd.read_parquet(a.cities)
        for frame in sorted(set(C.frame)):
            want = set(C[C.frame == frame].cluster.astype(int))
            if a.splits_dir:
                # Only cities that HAVE splits can be scored (2026-09-24: registered 107 and 115
                # have none, so they would read as "missing" forever).
                sub = {"registered": "analysis", "s70": "analysis_s70"}[frame]
                sp = set()
                for q in ("q1_primary", "q2"):
                    f = Path(a.splits_dir) / f"{sub}_splits_{q}.parquet"
                    if f.exists():
                        sp |= set(pd.read_parquet(f, columns=["cluster"]).cluster.astype(int))
                no_splits = sorted(want - sp)
                if no_splits:
                    print(f"{frame}: {len(no_splits)} cities have no splits, nothing to score: {no_splits}")
                want &= sp
            have = set(keep[keep.frame == frame].cluster.astype(int))
            if want - have:
                missing[frame] = sorted(want - have)
            print(f"{frame}: {len(have & want)}/{len(want)} registered cities consolidated", flush=True)
    if (incomplete or missing) and not a.allow_incomplete:
        print(f"REFUSING: incomplete {incomplete} / missing {missing}. Score them, or pass "
              "--allow-incomplete for a rehearsal (never for the summary run)."); return 3
    if a.dry_run:
        print("dry run: nothing written"); return 0
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for frame, g in keep.groupby("frame"):
        f = out / f"pred_tabpfn_consolidated_{frame}.parquet"
        g.drop(columns="source").assign(device="cpu").to_parquet(f, index=False)
        print("wrote", f.name, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
