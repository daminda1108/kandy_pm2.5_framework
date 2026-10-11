"""figure_provenance.py -- rebuild every thesis figure under a read/write trace and audit what each one drew from
(2026-10-11, after a review found Figure 3.1 drawn from an artefact older than the field it described).

For each figure builder: run it in a child process with I/O hooks that log every data file read (pandas, numpy,
xarray, rasterio, geopandas, json/open) and every figure written (matplotlib savefig). Then:
  * flag any read of a SUPERSEDED artefact (pattern list below; each entry says why it is retired);
  * flag any read of a Kandy field product older than the current delivered field;
  * compare each embedded figure's checksum before and after the rebuild (a change = it was stale);
  * check every figure embedded in the assembled thesis is written by some builder (no orphans).

  python build/figure_provenance.py            # trace + rebuild all builders, write the report
Out: #writing/build/figure_provenance.json, FIGURE_PROVENANCE.md (repository root)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WR = HERE.parent                                   # #writing
ROOT = WR.parent                                   # D:/ProjectCD
KP = ROOT / "kandy_pm25"
PY = KP / ".venv" / "Scripts" / "python.exe"
LOGDIR = HERE / "_provenance_logs"

BUILDERS = [(KP, f"scripts/{s}") for s in (
    "paper2026_figures.py", "paper2026_figures_b.py", "paper2026_figures_c.py", "paper2026_figures_d.py",
    "paper2026_fig_cycles_episode_burden.py", "paper2026_fig11_uncertainty.py", "paper2026_fig12_null_power.py",
    "paper2026_fig7_scorecard.py", "paper2026_fig8_kathmandu.py")] + [
    (WR, f"src/{s}") for s in ("f_chapters.py", "f_paper1.py", "d_schematics.py", "d_flowcharts.py",
                                "d05_validation_protocol.py")]

# Retired artefacts, each with the reason. A read of one of these by a thesis figure is a finding.
SUPERSEDED = [
    (r"backup_(dispersed|satellite_level)_", "a backup of a retired field version"),
    (r"kandy_decomp_predictions_\d{4}_additive\.parquet$", "v1 additive field (pre coherence cap)"),
    (r"B_background_hourly_\d{4}\.parquet$", "v1 background (pre coherence cap; F.43)"),
    (r"additive_partition\.csv$", "v1 partition (~0.25 local share; superseded by kandy_partition_v2.json)"),
    (r"decomp_summary_\d{4}\.csv$", "June 2026 summary file, predates additive_v3"),
    (r"_prerebuild_", "pre-rebuild archive"),
]
FIELD_PRODUCT = re.compile(r"(kandy_decomp_predictions_\d{4}_.*\.parquet|B_background_hourly_\d{4}_v2\.parquet|"
                           r"T_kandy_hourly_\d{4}\.parquet|kandy_partition_v2\.json)$")

HOOK = r'''
import builtins, io, json, os, sys, runpy
LOG = open(os.environ["PROV_LOG"], "a", encoding="utf-8")
def _log(kind, p):
    try:
        LOG.write(json.dumps({"k": kind, "p": os.path.abspath(str(p))}) + "\n"); LOG.flush()
    except Exception:
        pass
_open = builtins.open
def _hopen(f, mode="r", *a, **k):
    if isinstance(f, (str, os.PathLike)) and ("r" in mode or mode == "") and "+" not in mode:
        _log("read", f)
    return _open(f, mode, *a, **k)
builtins.open = _hopen
io.open = _hopen
def _wrap(mod, name, kind="read"):
    try:
        m = __import__(mod, fromlist=[name]); f = getattr(m, name)
        def g(p, *a, **k):
            if isinstance(p, (str, os.PathLike)): _log(kind, p)
            return f(p, *a, **k)
        setattr(m, name, g)
    except Exception:
        pass
for mod, name in [("pandas", "read_parquet"), ("pandas", "read_csv"), ("pandas", "read_json"), ("numpy", "load"),
                  ("xarray", "open_dataset"), ("rasterio", "open"), ("geopandas", "read_file"), ("PIL.Image", "open")]:
    _wrap(mod, name)
try:
    import matplotlib.figure as mf
    _sf = mf.Figure.savefig
    def _hs(self, fname, *a, **k):
        if isinstance(fname, (str, os.PathLike)): _log("write", fname)
        return _sf(self, fname, *a, **k)
    mf.Figure.savefig = _hs
except Exception:
    pass
import shutil, subprocess
for _n in ("copyfile", "copy", "copy2"):
    _f = getattr(shutil, _n)
    def _c(src, dst, *a, _f=_f, **k):
        _log("read", src); _log("write", dst)
        return _f(src, dst, *a, **k)
    setattr(shutil, _n, _c)
_run = subprocess.run
def _r(cmd, *a, **k):
    # a builder that launches another Python builder: trace the child too
    if isinstance(cmd, (list, tuple)) and len(cmd) > 1 and str(cmd[0]).lower().endswith("python.exe")             and str(cmd[1]).endswith(".py"):
        cmd = [cmd[0], os.environ["PROV_HOOK"], *cmd[1:]]
        env = dict(k.get("env") or os.environ); env.setdefault("PROV_LOG", os.environ["PROV_LOG"])
        env["PROV_LOG"] = os.environ["PROV_LOG"]; env["PROV_HOOK"] = os.environ["PROV_HOOK"]; k["env"] = env
    return _run(cmd, *a, **k)
subprocess.run = _r
script = sys.argv[1]; sys.argv = sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
runpy.run_path(script, run_name="__main__")
'''


def sha(p: Path) -> str:
    return hashlib.sha1(p.read_bytes()).hexdigest() if p.exists() else "missing"


def embedded_figures() -> list[Path]:
    t = (HERE / "a" / "thesis.md").read_text(encoding="utf-8")
    return sorted({Path(m) for m in re.findall(r"\]\((D:/[^)]+?\.png)\)", t)})


def main() -> int:
    LOGDIR.mkdir(exist_ok=True)
    hook = LOGDIR / "_hook.py"; hook.write_text(HOOK, encoding="utf-8")
    figs = embedded_figures()
    before = {str(f): sha(f) for f in figs}
    # optional baseline: checksums recorded at an earlier release ("<sha1>  <path>" lines), so a figure already
    # rebuilt by an interrupted run is still compared against the released state
    if len(sys.argv) > 2 and sys.argv[1] == "--baseline":
        for line in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines():
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            h, f = parts[0], parts[1].lstrip("*").strip()
            if f in before:
                before[f] = h
    t_field = max(p.stat().st_mtime for p in (KP / "data/processed/decomp").glob("kandy_decomp_predictions_20??_additive_v3.parquet"))
    runs = []
    t_start = time.time()
    for cwd, script in BUILDERS:
        log = LOGDIR / (Path(script).stem + ".jsonl")
        if log.exists():
            log.unlink()
        env = dict(os.environ, PROV_LOG=str(log), PROV_HOOK=str(hook), PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                   MPLBACKEND="Agg")
        t0 = time.time()
        r = subprocess.run([str(PY), str(hook), str(cwd / script)], cwd=cwd, env=env, capture_output=True, text=True)
        ev = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
        reads = sorted({e["p"] for e in ev if e["k"] == "read" and not e["p"].endswith((".py", ".pyc", ".mplstyle", ".ttf", ".otf", ".afm"))
                        and "site-packages" not in e["p"] and "\\Lib\\" not in e["p"]})
        writes = sorted({e["p"] for e in ev if e["k"] == "write"})
        flags = []
        for p in reads:
            for pat, why in SUPERSEDED:
                if re.search(pat, p.replace("\\", "/")):
                    flags.append({"file": p, "why": why})
            if FIELD_PRODUCT.search(p.replace("\\", "/")) and os.path.exists(p) and os.path.getmtime(p) < t_field - 3600 \
                    and "_drv" not in p and not re.search(r"_(4factor|additive_v2)\.parquet$|kandy_decomp_predictions_\d{4}\.parquet$", p):
                flags.append({"file": p, "why": "Kandy field product older than the current delivered field"})
        runs.append(dict(builder=script, exit=r.returncode, seconds=round(time.time() - t0, 1), reads=reads,
                         writes=writes, flags=flags, stderr_tail=r.stderr[-600:] if r.returncode else ""))
        print(f"{script}: exit {r.returncode}, {len(reads)} inputs, {len(writes)} figures written, {len(flags)} flags", flush=True)
    after = {str(f): sha(f) for f in figs}
    written = {os.path.normcase(os.path.abspath(w)) for r in runs for w in r["writes"]}
    rows = []
    for f in figs:
        fn = os.path.normcase(os.path.abspath(f))
        by = [r["builder"] for r in runs if fn in {os.path.normcase(os.path.abspath(w)) for w in r["writes"]}]
        # a renderer the hooks cannot see (graphviz) still counts if the file was rewritten during this run
        if not by and f.stat().st_mtime >= t_start:
            by = ["(rewritten during the run by an untraced renderer: graphviz builders d_flowcharts/d05)"]
        rows.append(dict(figure=str(f), builder=by[0] if by else None, rebuilt=bool(by),
                         changed=before[str(f)] != after[str(f)], mtime=time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime))))
    out = dict(built=time.strftime("%Y-%m-%dT%H:%M:%S"), field_mtime=time.strftime("%Y-%m-%d %H:%M", time.localtime(t_field)),
               figures=rows, builders=runs)
    (HERE / "figure_provenance.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    md = ["# Figure provenance, thesis A", "",
          f"- Built {out['built']}; delivered field written {out['field_mtime']}.",
          f"- Figures embedded: {len(rows)}; rebuilt by a builder this run: {sum(r['rebuilt'] for r in rows)}; "
          f"changed by the rebuild (were stale): {sum(r['changed'] for r in rows)}; orphans (no builder): "
          f"{sum(not r['rebuilt'] for r in rows)}.",
          f"- Builders failing: {sum(r['exit'] != 0 for r in runs)}; superseded-input flags: {sum(len(r['flags']) for r in runs)}.",
          "", "| figure | builder | changed by rebuild |", "|---|---|---|"]
    md += [f"| `{Path(r['figure']).name}` | `{r['builder']}` | {'**yes**' if r['changed'] else 'no'} |" for r in rows]
    md += ["", "## Flags (reads of superseded or out-of-date artefacts)", ""]
    fl = [(r["builder"], f) for r in runs for f in r["flags"]]
    md += [f"- `{b}` read `{Path(f['file']).name}` — {f['why']}" for b, f in fl] or ["- none"]
    (ROOT / "FIGURE_PROVENANCE.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n{len(rows)} figures; rebuilt {sum(r['rebuilt'] for r in rows)}; changed {sum(r['changed'] for r in rows)}; "
          f"orphans {sum(not r['rebuilt'] for r in rows)}; flags {len(fl)}; failing builders {sum(r['exit'] != 0 for r in runs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
