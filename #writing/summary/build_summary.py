"""Build the two-page summary as PDF and .docx.

WHY IT GOES THROUGH THE SAME MACHINERY. This is the document most likely to be read by someone
who has never seen the work, and it is the one where a stale number does the most damage. It
carries {{claim:}} tokens resolved against the same generated file as the thesis, and the build
fails on drift exactly as the thesis build does.

PDF is the primary output: it is what a cold email should carry, because it renders identically
everywhere and cannot be edited by accident in transit. The .docx is produced alongside for
editing.

Usage: python build_summary.py
Out:   summary/summary.pdf, summary/summary.docx
"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "summary.md"
RESOLVED = HERE / "_summary_resolved.md"
REPO = Path("D:/ProjectCD/kandy_pm25")
CLAIMS = REPO / "data" / "processed" / "modular" / "claims.json"
BUILD_CLAIMS = REPO / "scripts" / "build_claims.py"
VENV_PY = REPO / ".venv" / "Scripts" / "python.exe"
REF = HERE.parent / "build" / "reference.docx"

TOKEN = re.compile(r"\{\{claim:([A-Za-z0-9_.]+)\}\}")


def main() -> int:
    # same gate as the thesis: recompute and refuse on drift
    r = subprocess.run([str(VENV_PY), str(BUILD_CLAIMS), "--check"],
                       cwd=str(REPO), capture_output=True, text=True)
    if r.returncode != 0:
        print("CLAIMS GATE FAILED, not building:")
        print((r.stdout + r.stderr)[-800:])
        return 1
    claims = json.load(io.open(CLAIMS, encoding="utf-8"))["claims"]
    print(f"claims.json fresh, {len(claims)} claims")

    text = io.open(SRC, encoding="utf-8").read()
    missing = []

    def sub(m):
        tag = m.group(1)
        if tag not in claims:
            missing.append(tag)
            return m.group(0)
        return str(claims[tag]["value"])

    text = TOKEN.sub(sub, text)
    if missing:
        print("UNRESOLVED CLAIMS, not building:")
        for t in sorted(set(missing)):
            print(f"  {t}")
        return 1

    # em dashes are banned in this project's writing; check the summary too
    if re.search(r"[\u2014\u2013]", text):
        print("em or en dash found in the summary. Not building.")
        return 1

    RESOLVED.write_text(text, encoding="utf-8")
    body = re.sub(r"^---.*?---", "", text, count=1, flags=re.S)
    words = len(re.sub(r"[^\w\s]", " ", body).split())
    print(f"words {words}")

    ok = True
    for fmt, out, extra in (
        ("pdf", HERE / "summary.pdf", ["--pdf-engine", "xelatex", "-V", "linkcolor=black"]),
        ("docx", HERE / "summary.docx", ["--reference-doc", str(REF)] if REF.exists() else []),
    ):
        cmd = ["pandoc", str(RESOLVED), "--from", "markdown+yaml_metadata_block",
               "--to", fmt, "-o", str(out)] + extra
        p = subprocess.run(cmd, cwd=str(HERE), capture_output=True, text=True)
        if p.returncode != 0:
            print(f"{fmt} failed:\n{(p.stdout + p.stderr)[-700:]}")
            ok = False
            continue
        print(f"  wrote {out.name}  ({out.stat().st_size / 1024:,.0f} KB)")
    RESOLVED.unlink(missing_ok=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
