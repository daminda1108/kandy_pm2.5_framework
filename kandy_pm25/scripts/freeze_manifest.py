"""freeze_manifest.py -- SHA-256 freeze of code and predictor data before a registration is lodged.

Usage:
  python scripts/freeze_manifest.py --name rich --code a.py,b.py --data-dir data/processed/modular/rich_streams
  python scripts/freeze_manifest.py --name rich --verify     # re-hash and compare, exit 1 on any change
Output: docs/{name}_freeze_manifest.json (per-file hashes + a combined data hash).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--code", default="")
    ap.add_argument("--data-dir", default="")
    ap.add_argument("--exclude", default=".log,.tmp")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    mf = REPO / "docs" / f"{a.name}_freeze_manifest.json"
    if a.verify:
        m = json.loads(mf.read_text(encoding="utf-8"))
        bad = [f for f, h in {**m["code"], **m["data"]}.items() if sha(REPO / f) != h]
        print(f"{len(m['code'])} code + {len(m['data'])} data files; changed: {bad}")
        return 1 if bad else 0
    code = {f: sha(REPO / f) for f in a.code.split(",") if f}
    data = {}
    if a.data_dir:
        ex = tuple(a.exclude.split(","))
        for p in sorted((REPO / a.data_dir).rglob("*")):
            if p.is_file() and not p.name.endswith(ex) and "_v0_" not in p.name:
                data[p.relative_to(REPO).as_posix()] = sha(p)
    comb = hashlib.sha256("".join(f"{k}{v}" for k, v in sorted(data.items())).encode()).hexdigest()
    import subprocess
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True,
                            text=True).stdout.strip()
    m = {"name": a.name, "commit_at_freeze": commit, "code": code, "data": data,
         "data_files": len(data), "data_combined_sha256": comb}
    mf.write_text(json.dumps(m, indent=1), encoding="utf-8")
    print(f"{len(code)} code files, {len(data)} data files, combined data sha256 {comb}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
