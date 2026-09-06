"""Build the thesis .docx.

Runs the whole chain rather than trusting that the previous stage was run:

    lint.py          style rules; a violation blocks the build
    assemble.py      chapter concatenation, claims gate, figure numbering
    pandoc           markdown to .docx against build/reference.docx

⚠ pandoc warns about unresolved citations and still exits 0, so its stderr is surfaced rather
than swallowed. A .docx that silently contains a broken citation field is worse than a build
that fails, because a supervisor sees it before the author does.

Usage: python build_docx.py [--skip-lint]
Out:   build/thesis.docx
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MD = HERE / "thesis.md"
OUT = HERE / "thesis.docx"
REF = HERE / "reference.docx"
BIB = Path(r"D:\ProjectCD\kandy_pm25\docs\paper\references.bib")
PY = sys.executable


def run(cmd, label) -> bool:
    r = subprocess.run(cmd, cwd=str(HERE), capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    print(out.rstrip())
    if r.returncode != 0:
        print(f"\n{label} failed. Not building the docx.")
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-lint", action="store_true",
                    help="build anyway. For inspecting a draft, never for a version shared.")
    a = ap.parse_args()

    if shutil.which("pandoc") is None:
        print("pandoc not on PATH")
        return 1
    if not REF.exists():
        print("reference.docx missing. Run make_reference_docx.py first.")
        return 1

    # Tables are a DERIVED artefact and the build consumes them, so the build regenerates them.
    # Without this the chain reads whatever t_tables.py last wrote, which is the stale-artefact
    # failure Chapter 10 is about: a structural edit to a table silently does not reach the
    # document while every claim inside it still resolves and every gate stays green. Found
    # exactly that way, by editing a table note and watching the old note build.
    if not run([PY, str(ROOT / "src" / "t_tables.py")], "tables"):
        return 1

    if not a.skip_lint:
        if not run([PY, str(HERE / "lint.py")], "lint"):
            return 1
    else:
        print("lint SKIPPED. Do not share this build.")

    if not run([PY, str(HERE / "assemble.py")], "assemble"):
        return 1

    cmd = ["pandoc", str(MD),
           "--from", "markdown+pipe_tables+implicit_figures+tex_math_dollars",
           "--to", "docx",
           "--reference-doc", str(REF),
           "--toc", "--toc-depth", "3",
           # NOT --number-sections. Every heading already carries its own number, because
           # assemble.py reads the chapter number out of the heading text to number figures and
           # tables by chapter. Letting pandoc number them as well produced headings like
           # "8.3 7.3 The recommendation inverts in the tropics" -- pandoc's count, which treats
           # the front matter as chapter one and is therefore offset by one, followed by the real
           # section number. An external reviewer saw it in the built document.
           "--resource-path", f"{ROOT / 'thesis'}",
           "-o", str(OUT)]
    if BIB.exists():
        cmd += ["--citeproc", "--bibliography", str(BIB)]

    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    warn = (r.stderr or "").strip()
    if warn:
        print("\npandoc said:")
        print(warn)
    if r.returncode != 0:
        print("pandoc failed")
        return 1

    kb = OUT.stat().st_size / 1024
    print(f"\nwrote {OUT.relative_to(ROOT)}  ({kb:,.0f} KB)")
    if "citation" in warn.lower():
        print("⚠ pandoc reported a citation problem above. It still exited 0. Check it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
