"""make_learner_kernels.py -- build the Kaggle dataset and kernels for L1 (TabPFN) and L2 (GRU).

Dataset (flat root, gotcha #93b): bud0_learners_kaggle.py + frame_{tag}.parquet + columns json.
Kernels: one per learner and tag, GPU (the accelerator MUST be set to "GPU T4 x2" in the UI after the
push, gotcha #93e; the L1 kernel also needs the TABPFN_TOKEN secret ticked in the editor, #93a).
A new kernel slug per tag, because a kernel stays attached to the dataset version current at its
creation (gotcha #95a).

Usage: python scripts/make_learner_kernels.py --tag synthetic|real
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LD = REPO / "data" / "processed" / "modular" / "learners"
OWNER = "damindaalahakoon"

KERNEL = r'''import os, sys, subprocess, glob, json
LEARNER, TAG = "{learner}", "{tag}"
if LEARNER == "L1":
    from kaggle_secrets import UserSecretsClient
    try:
        tok = UserSecretsClient().get_secret("TABPFN_TOKEN").strip()
    except Exception as ex:
        raise SystemExit(f"could not read TABPFN_TOKEN ({{type(ex).__name__}}): tick it under Add-ons -> Secrets "
                         "in the editor, then run from the UI (a CLI push removes it)")
    os.environ["TABPFN_TOKEN"] = tok
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "tabpfn==8.5.0"], check=True)
import torch
assert torch.cuda.is_available(), "no GPU: set Accelerator -> GPU T4 x2 in the editor"
print("GPU:", torch.cuda.get_device_name(0), "capability", torch.cuda.get_device_capability(0), flush=True)
assert torch.cuda.get_device_capability(0) >= (7, 0), "P100 (sm_60) is not supported (gotcha #25)"
hits = glob.glob("/kaggle/input/**/bud0_learners_kaggle.py", recursive=True)
assert len(hits) == 1, hits
data = os.path.dirname(hits[0])
print("data dir:", data, sorted(os.listdir(data)), flush=True)
args = [sys.executable, hits[0], "--learner", LEARNER, "--tag", TAG, "--data", data,
        "--out", "/kaggle/working", "--repeat-check"]
{extra}
r = subprocess.run(args)
if r.returncode:
    raise SystemExit(r.returncode)
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", choices=("synthetic", "real"), required=True)
    ap.add_argument("--smoke", type=int, default=0, help="synthetic only: score 1 of N city shards")
    a = ap.parse_args()
    ds = LD / "kaggle" / f"dataset_{a.tag}"
    if ds.exists():
        shutil.rmtree(ds)
    ds.mkdir(parents=True)
    shutil.copy(REPO / "scripts" / "bud0_learners_kaggle.py", ds)
    for f in (f"frame_{a.tag}.parquet", f"frame_{a.tag}_columns.json"):
        shutil.copy(LD / f, ds)
    slug = f"kandy-learners-{a.tag}"
    json.dump({"title": slug, "id": f"{OWNER}/{slug}", "licenses": [{"name": "CC0-1.0"}]},
              open(ds / "dataset-metadata.json", "w"), indent=1)
    # real run: L1 (TabPFN, ~3.3 min per city on a T4) in 2 disjoint city shards, L2 (~0.6 min) in 1
    plan = [("L1", k, 2) for k in range(2)] + [("L2", 0, 1)] if a.tag == "real" else            [("L1", 0, 0), ("L2", 0, 0)]
    for L, k, n in plan:
        suffix = f"-s{k}" if n > 1 else ""
        kd = LD / "kaggle" / f"kernel_{L}_{a.tag}{suffix}"
        if kd.exists():
            shutil.rmtree(kd)
        kd.mkdir(parents=True)
        if a.smoke:
            extra = f'args += ["--shard", "0", "--n-shards", "{a.smoke}"]'
        elif n > 1:
            extra = f'args += ["--shard", "{k}", "--n-shards", "{n}"]'
        else:
            extra = ""
        (kd / "kernel.py").write_text(KERNEL.format(learner=L, tag=a.tag, extra=extra), encoding="utf-8")
        ks = f"kandy-bud0-{L.lower()}-{a.tag}{suffix}"
        json.dump({"id": f"{OWNER}/{ks}", "title": ks, "code_file": "kernel.py", "language": "python",
                   "kernel_type": "script", "is_private": True, "enable_gpu": True,
                   "enable_internet": True, "dataset_sources": [f"{OWNER}/{slug}"],
                   "competition_sources": [], "kernel_sources": []},
                  open(kd / "kernel-metadata.json", "w"), indent=2)
    print("built", ds, "and kernels for L1, L2")


if __name__ == "__main__":
    main()
