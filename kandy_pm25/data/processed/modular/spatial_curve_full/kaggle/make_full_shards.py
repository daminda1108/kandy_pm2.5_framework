"""Test B (OSF fu59b): Kaggle CPU kernels that score E0-E7 on the full-record frames.

Same kernel design as spatial_curve/kaggle/make_analysis_cpu_shards.py (single-worker processes over a
global shard partition, per-city cache, fail loudly), with three changes:
  * inputs are two NEW datasets built here: the frozen code (byte-identical, SHA-256 recorded) and the
    full-record frame files;
  * deviation B-1: each frame runs in its own project directory whose frame_greybox.csv holds THAT frame's
    E7 values (frame_greybox.csv for the registered frame, frame_greybox_s70.csv for S-1);
  * fresh kernel slugs (gotcha #95a).
Usage: python make_full_shards.py      (writes datasets/ and kernels/; pushing is done separately)
"""
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
NEW = HERE.parent
REPO = NEW.parents[3]
OWNER = "damindaalahakoon"
N_KERNELS, PROCS = 5, 4
CODE = ["spatial_curve_analysis.py", "spatial_curve_freeze.py", "design_sensor_network.py"]
FRAME = ["frame_cities.csv", "frame_cities_s70.csv", "frame_sites.csv", "frame_sites_s70.csv",
         "frame_predictors.csv", "frame_greybox.csv", "frame_greybox_s70.csv", "frame_daily.parquet",
         "frame_daily_s70.parquet"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def datasets():
    out = {}
    for slug, files, src in (("kandy-spatial-full-code", CODE, REPO / "scripts"),
                             ("kandy-spatial-full-data", FRAME, NEW)):
        d = HERE / "datasets" / slug
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        for f in files:
            shutil.copy2(src / f, d / f)
            assert sha(src / f) == sha(d / f)
        (d / "dataset-metadata.json").write_text(json.dumps(
            {"title": slug, "id": f"{OWNER}/{slug}", "licenses": [{"name": "CC0-1.0"}]}, indent=2))
        out[slug] = {f: sha(d / f) for f in files}
    (HERE / "dataset_hashes.json").write_text(json.dumps(out, indent=2))


KERNEL = '''"""Test B (OSF fu59b), E0-E7 on full-record frames, CPU shard {k} of {nk}: global shards {lo}..{hi} of {tot}."""
import json, os, shutil, subprocess, sys, time
from pathlib import Path

K, PROCS, TOT = {k}, {procs}, {tot}
print("CPUs:", os.cpu_count(), "| kernel shard", K, flush=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pykrige", "mgwr", "gstools"], check=True)
found = {{}}
for root, _, files in os.walk("/kaggle/input"):
    for f in files:
        found.setdefault(f, Path(root) / f)
code = {code}
frame = {frame}
missing = [f for f in code + frame if f not in found]
if missing:
    raise SystemExit(f"inputs incomplete, missing {{missing}}")

def project(tag):
    proj = Path(f"/kaggle/working/proj_{{tag or 'registered'}}")
    if proj.exists():
        shutil.rmtree(proj)
    (proj / "scripts").mkdir(parents=True)
    for f in code:
        shutil.copy2(found[f], proj / "scripts" / f)
    SC = proj / "data" / "processed" / "modular" / "spatial_curve"
    SC.mkdir(parents=True)
    for f in frame:
        if f.startswith("frame_greybox"):
            continue
        shutil.copy2(found[f], SC / f)
    # deviation B-1: this frame's own E7 values
    shutil.copy2(found["frame_greybox_s70.csv" if tag else "frame_greybox.csv"], SC / "frame_greybox.csv")
    return proj

cache = Path("/kaggle/working/city_cache"); cache.mkdir(exist_ok=True)
env = dict(os.environ, SPATIAL_DL_PRED_DIRS="", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
           OPENBLAS_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
t0 = time.time()
report = {{"kernel_shard": K, "frames": {{}}}}
procs = []
for tag in ("", "s70"):                       # both frames concurrently (gotcha #95d)
    script = str(project(tag) / "scripts" / "spatial_curve_analysis.py")
    name = tag or "registered"
    for j in range(PROCS // 2 if PROCS > 1 else 1):
        g = K * (PROCS // 2) + j
        cmd = [sys.executable, "-u", script, "--defer-dl-arms", "--workers", "1", "--city-cache", str(cache),
               "--shard", str(g), "--n-shards", str(TOT), "--score-only"] + (["--frame-tag", tag] if tag else [])
        log = open(f"/kaggle/working/{{name}}_g{{g}}.log", "w")
        procs.append((name, g, subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT), log))
        print(f"  {{name}}: global shard {{g}}/{{TOT}} started", flush=True)
for name, g, p, log in procs:
    rc = p.wait(); log.close()
    report["frames"].setdefault(name, {{}})[g] = rc
    tail = Path(f"/kaggle/working/{{name}}_g{{g}}.log").read_text(errors="replace").splitlines()
    print(f"  {{name}} shard {{g}}: exit {{rc}} | {{(time.time()-t0)/60:.1f}} min", flush=True)
    for ln in tail[-4:]:
        print("   " + ln, flush=True)
cached = sorted(f.name for f in cache.glob("city_*.pkl"))
report["cached"] = len(cached); report["minutes"] = round((time.time() - t0) / 60, 1)
Path("/kaggle/working/shard_summary.json").write_text(json.dumps(report, indent=2, default=str))
print(json.dumps(report, indent=2, default=str), flush=True)
bad = {{f"{{fr}}:{{g}}": rc for fr, ex in report["frames"].items() for g, rc in ex.items() if rc}}
if bad:
    raise SystemExit(f"shards failed: {{bad}}")
if not cached:
    raise SystemExit("no city was cached")
'''


def kernels():
    tot = N_KERNELS * (PROCS // 2)               # each kernel runs PROCS//2 shards per frame
    for k in range(N_KERNELS):
        d = HERE / "kernels" / f"full_s{k}"
        d.mkdir(parents=True, exist_ok=True)
        lo = k * (PROCS // 2)
        src = KERNEL.format(k=k, nk=N_KERNELS, procs=PROCS, tot=tot, lo=lo, hi=lo + PROCS // 2 - 1,
                            code=repr(CODE), frame=repr(FRAME))
        compile(src, "kernel.py", "exec")
        (d / "kernel.py").write_text(src, encoding="utf-8")
        meta = {"id": f"{OWNER}/kandy-spatial-full-s{k}", "title": f"kandy-spatial-full-s{k}",
                "code_file": "kernel.py", "language": "python", "kernel_type": "script", "is_private": True,
                "enable_gpu": False, "enable_internet": True,
                "dataset_sources": [f"{OWNER}/kandy-spatial-full-code", f"{OWNER}/kandy-spatial-full-data"],
                "competition_sources": [], "kernel_sources": []}
        (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"{N_KERNELS} kernels, {tot} global shards per frame")


if __name__ == "__main__":
    datasets(); kernels()
