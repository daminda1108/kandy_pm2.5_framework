"""Render the assembled manuscript to .docx for editing.

WHY DOCX AND NOT PDF. The PDF is the submission artefact; this is the working copy, so it is
built with tracked-changes-friendly styles and with citations RESOLVED to text rather than left
as pandoc-citeproc fields -- a field that a co-author's Word cannot resolve renders as a broken
reference, and a supervisor reading a draft should never see one.

The build refuses to run on a stale manuscript: it re-assembles first, which re-runs the claims
gate, so a .docx can never carry a number the data no longer supports.

Usage:  .venv/Scripts/python.exe docs/paper/build_docx.py
Out:    docs/paper/manuscript_kandy.docx
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
MS = DIR / "manuscript_kandy.md"
BIB = DIR / "references.bib"
OUT = DIR / "manuscript_kandy.docx"


def main() -> int:
    if shutil.which("pandoc") is None:
        print("pandoc not found on PATH"); return 1

    # Re-assemble first. This re-runs the claims freshness gate, so the .docx cannot be built
    # from a manuscript whose numbers have drifted from the scored files.
    r = subprocess.run([sys.executable, str(DIR / "assemble_manuscript.py")],
                       capture_output=True, text=True, cwd=DIR)
    if r.returncode != 0:
        print("assembly failed -- not building the docx:\n" + r.stdout + r.stderr)
        return 1
    print(r.stdout.strip())

    cmd = [
        "pandoc", str(MS),
        "-o", str(OUT),
        "--from", "markdown+pipe_tables+tex_math_dollars+raw_tex",
        "--to", "docx",
        "--citeproc",
        "--bibliography", str(BIB),
        "--resource-path", str(DIR),
        "--number-sections",
        "--toc", "--toc-depth=2",
        "--metadata", "link-citations=true",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=DIR)
    if r.returncode != 0:
        print("pandoc failed:\n" + r.stdout + r.stderr)
        return 1
    if r.stderr.strip():
        # Pandoc warns about unresolved citation keys on stderr and still exits 0. That is
        # exactly the failure this project has made before, so it is surfaced rather than eaten.
        print("pandoc warnings:\n  " + r.stderr.strip().replace("\n", "\n  "))
    size = OUT.stat().st_size / 1024
    print(f"\nwrote {OUT.name}  ({size:,.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
