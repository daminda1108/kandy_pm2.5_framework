"""Build one thesis: python build_docx.py --thesis a   (or b)

Runs the whole chain rather than trusting that the previous stage was run:

    t_tables.py      regenerate the table fragments the build consumes (gotcha #90)
    lint.py          style rules on EXACTLY the files this thesis includes; a violation blocks
    assemble.py      composition, numbering, {{ref:}} and {{claim:}} gates
    pandoc           markdown to .docx against build/reference.docx, APS numeric citations
    postprocess.py   sections, roman then Arabic page numbers, contents fields, and the
                     compliance measurement in Word

⚠ pandoc warns about unresolved citations and still exits 0, so its stderr is surfaced rather
than swallowed.

Out: build/<id>/thesis_<id>.docx, build/<id>/thesis_<id>.pdf, build/<id>/compliance.json
Exit 2 means the document built but does not meet the page or proportion rules.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REF = HERE / "reference.docx"
CSL = HERE / "csl" / "american-physics-society.csl"
BIB = Path("D:/ProjectCD/kandy_pm25/docs/paper/references.bib")
PY = sys.executable
sys.path.insert(0, str(HERE))


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
    ap.add_argument("--thesis", required=True, choices=["a", "b"])
    ap.add_argument("--skip-lint", action="store_true",
                    help="build anyway. For inspecting a draft, never for a version shared.")
    ap.add_argument("--no-word", action="store_true",
                    help="skip the Word stage (no page measurement, no PDF)")
    a = ap.parse_args()
    out = HERE / a.thesis
    out.mkdir(exist_ok=True)

    if shutil.which("pandoc") is None:
        print("pandoc not on PATH")
        return 1
    for need in (REF, CSL, BIB):
        if not need.exists():
            print(f"missing: {need}")
            return 1

    if not run([PY, str(ROOT / "src" / "t_tables.py")], "tables"):
        return 1

    if not a.skip_lint:
        from assemble import sources_of
        files = [str(p) for p in sources_of(a.thesis)]
        if not run([PY, str(HERE / "lint.py"), *files], "lint"):
            return 1
    else:
        print("lint SKIPPED. Do not share this build.")

    if not run([PY, str(HERE / "assemble.py"), "--thesis", a.thesis], "assemble"):
        return 1

    cmd = ["pandoc", str(out / "thesis.md"),
           "--from", "markdown+pipe_tables+implicit_figures+tex_math_dollars+raw_attribute",
           "--to", "docx",
           "--reference-doc", str(REF),
           # NOT --toc: the contents is a Word field placed after the acknowledgement, as the
           # guidelines order it. NOT --number-sections: assemble.py numbers every heading.
           "--resource-path", f"{ROOT / 'thesis'}",
           "--citeproc", "--bibliography", str(BIB), "--csl", str(CSL),
           # A printed thesis: reference titles as plain black text, not blue hyperlinks.
           "--metadata", "link-bibliography=false",
           "-o", str(out / "pandoc.docx")]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    warn = (r.stderr or "").strip()
    if warn:
        print()
        print("pandoc said:")
        print(warn)
    if r.returncode != 0:
        print("pandoc failed")
        return 1
    if "citation" in warn.lower():
        print("⚠ pandoc reported a citation problem above. It still exited 0. Check it.")

    post = [PY, str(HERE / "postprocess.py"), "--thesis", a.thesis]
    if a.no_word:
        post.append("--no-word")
    rc = subprocess.run(post, cwd=str(HERE)).returncode
    return rc


if __name__ == "__main__":
    sys.exit(main())
