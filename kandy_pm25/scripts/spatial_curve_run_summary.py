"""The spatial learning curve SUMMARY run: every arm merged, both frames, exactly once.

Written 2026-09-23 after a rehearsal found that the default inputs would have been wrong:
  * merge_deep's default directory (dl_out/) holds a GPU-era pred_tabpfn_fold4.parquet (D-8)
    and every E10 prediction twice (fold*/ and e10_fold*/, byte-identical);
  * a city missing from the cache would have been silently re-scored, not reported.
This runner names every input explicitly and checks it BEFORE anything is summarised.

Inputs:
  city cache   spatial_curve/city_cache_salvage/  (37 registered + 41 S-1 per-city results)
  E10          spatial_curve/dl_out/e10_fold{0..4}/pred_convgnp_*  (one folder set only)
  E8/E9        spatial_curve/tabpfn_consolidated/pred_tabpfn_consolidated_{frame}.parquet
               written by spatial_curve_tabpfn_consolidate.py from the CPU kernels (D-8)

Usage:
  python scripts/spatial_curve_run_summary.py --preflight   # checks only; computes no result
  python scripts/spatial_curve_run_summary.py               # the summary run itself
"""
import argparse, os, subprocess, sys
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SC = REPO / "data/processed/modular/spatial_curve"
CACHE = SC / "city_cache_salvage"
E10 = [SC / "dl_out" / f"e10_fold{i}" for i in range(5)]
TABPFN = SC / "tabpfn_consolidated"
# The REGISTERED positive controls, which gate E10/E11 interpretation. They are NOT in dl_out/:
# that folder holds only 20- and 100-step SMOKE controls marked primary, all failed, which would
# have labelled E10 "failed its control" when its registered control (3 seeds, 1,209 steps) passed.
CONTROLS = [SC / "kaggle/control_kernel_convgnp/out_v1/dl_out",      # E10: 3/3 passed
            SC / "kaggle/control_kernel/out_v2/dl_out"]              # E11: 3/3 failed (amendment 2)
EXPECT_CONTROLS = {"E10 ConvGNP": (3, True), "E11 TNP-D": (3, False)}
FRAMES = {"registered": ("", "frame_cities.csv"), "s70": ("s70", "frame_cities_s70.csv")}


def preflight() -> list[str]:
    errs = []
    for frame, (tag, fc) in FRAMES.items():
        C = pd.read_csv(SC / fc)
        use = C[C.primary.astype(bool) | C.secondary.astype(bool) | C.band_arm.astype(bool)]
        want = {int(c) for c in use.cluster}
        have = {int(p.stem.split("_")[-1]) for p in CACHE.glob(f"city_{frame}_*.pkl")}
        if want - have:
            errs.append(f"{frame}: cache lacks {sorted(want - have)}")
        f = TABPFN / f"pred_tabpfn_consolidated_{frame}.parquet"
        if not f.exists():
            errs.append(f"{frame}: {f.name} not written yet (run the consolidator)")
        else:
            T = pd.read_parquet(f, columns=["cluster", "est", "device"])
            if not (T.device == "cpu").all():
                errs.append(f"{frame}: consolidated E8/E9 not all device=cpu (D-8)")
            if set(T.est) != {"E8", "E9"}:
                errs.append(f"{frame}: consolidated file holds {sorted(set(T.est))}, want E8 and E9")
            scored = {int(c) for c in T.cluster}
            # only cities with splits can carry E8/E9 (registered 107, 115 have none)
            ad = SC / ("analysis" + ("_s70" if frame == "s70" else ""))
            sp = set()
            for q in ("q1_primary", "q2"):
                if (ad / f"splits_{q}.parquet").exists():
                    sp |= set(pd.read_parquet(ad / f"splits_{q}.parquet", columns=["cluster"]).cluster.astype(int))
            if (want & sp) - scored:
                errs.append(f"{frame}: E8/E9 lack cities {sorted((want & sp) - scored)}")
        print(f"{frame}: {len(want)} cities needed | cache {len(want & have)} | "
              f"E8/E9 file {'present' if f.exists() else 'ABSENT'}", flush=True)
    n10 = sum(len(list(d.rglob("pred_convgnp_*.parquet"))) for d in E10)   # nested: e10_foldN/dl_out/
    print(f"E10: {n10} prediction files in e10_fold0..4 (expected 15: 5 folds x 3 seeds)", flush=True)
    if n10 != 15:
        errs.append(f"E10: {n10} prediction files, expected 15")
    import json
    ctl = {}
    for d in CONTROLS:
        for f in d.rglob("control_*.json"):
            j = json.loads(f.read_text())
            if j.get("primary_control"):
                ctl.setdefault(j["arm"], []).append(bool(j["passed"]))
    for arm, (n, passed) in EXPECT_CONTROLS.items():
        got = ctl.get(arm, [])
        print(f"control {arm}: {len(got)} runs, passed_all={all(got) if got else None}", flush=True)
        if len(got) != n or all(got) != passed:
            errs.append(f"control {arm}: read {got}, recorded as {n} runs passed={passed}")
    stray = [p for d in E10 + [TABPFN] + CONTROLS for p in d.rglob("pred_*.parquet")
             if "tabpfn" in p.name and not p.name.startswith("pred_tabpfn_consolidated_")]
    if stray:
        errs.append(f"non-consolidated TabPFN files inside the merge dirs: {[p.name for p in stray]}")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight", action="store_true", help="checks only; no summary computed")
    a = ap.parse_args()
    errs = preflight()
    for e in errs:
        print("  PREFLIGHT FAIL:", e, flush=True)
    if a.preflight or errs:
        print("preflight", "FAILED" if errs else "passed", "-- nothing summarised", flush=True)
        return 1 if errs else 0
    env = dict(os.environ, SPATIAL_DL_PRED_DIRS=os.pathsep.join(str(d) for d in E10 + [TABPFN] + CONTROLS))
    for frame, (tag, _) in FRAMES.items():
        cmd = [sys.executable, "-u", str(REPO / "scripts/spatial_curve_analysis.py"),
               "--city-cache", str(CACHE), "--require-cache", "--defer-dl-arms", "--frame-tag", tag]
        print(f"\n=== summary: {frame} ===", flush=True)
        r = subprocess.run(cmd, env=env)
        if r.returncode:
            print(f"{frame}: summary exited {r.returncode}; stopping", flush=True)
            return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
