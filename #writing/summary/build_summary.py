"""Build the three-page summary as PDF and .docx.

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
# Thesis A is the ENS4998 submission the summary describes (2026-09-19). The old single-thesis
# build/thesis.md is legacy and no longer built, so counting it would describe the wrong document.
THESIS_MD = HERE.parent / "build" / "a" / "thesis.md"
REGISTRY = HERE.parent / "registrations.json"

TOKEN = re.compile(r"\{\{claim:([A-Za-z0-9_.]+)\}\}")

# The summary is the only document that describes ITSELF: how long the thesis is, how many
# figures it carries, how many registrations stand behind it. Those numbers were plain prose,
# so the gate that protects every other figure in the document could not see them, and all
# three drifted. They are claims now, resolved here, from the same artefacts a reader would
# check.
# Two words, so that if the marker lands at a line end LaTeX breaks it at the space. As one
# word it hyphenated to "[UN-VERIFIED]", which is legible but looks like a typesetting
# fault instead of a deliberate flag.
UNVERIFIED = "[NOT VERIFIED]"


def _spell(n: int) -> str:
    """Small integers as words. A summary that says '8 pre-registrations' mid-sentence reads
    as a spreadsheet; the surrounding prose spells its numbers out."""
    words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
             "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
             "seventeen", "eighteen", "nineteen"]
    if n < 20:
        return words[n]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    if n < 100:
        return tens[n // 10] + ("" if n % 10 == 0 else f"-{words[n % 10]}")
    return str(n)


def meta_claims() -> dict:
    """Numbers the summary states about the thesis and about the project's own practice.

    Anything that cannot be established is returned as UNVERIFIED rather than omitted or
    guessed. It then renders that way on the page, which is deliberate: a number nobody has
    checked must be impossible to send out by accident, and a build that merely warns on the
    console gets ignored the third time it warns.
    """
    m: dict[str, object] = {}

    if THESIS_MD.exists():
        t = THESIS_MD.read_text(encoding="utf-8")
        # the same expression assemble.py uses, so the two counts cannot disagree
        n_words = len(re.sub(r"[^\w\s]", " ", t).split())
        m["meta.words"] = f"{n_words:,}"
        # appendix visuals are lettered (Figure A.1), so the label is [0-9A-Z]+ before the dot
        m["meta.figures"] = len(set(re.findall(r"^!\[(Figure [0-9A-Z]+\.\d+)\.", t, re.M)))
        m["meta.tables"] = len(set(re.findall(r"^Table: (Table [0-9A-Z]+\.\d+)\.", t, re.M)))
    else:
        m["meta.words"] = m["meta.figures"] = m["meta.tables"] = UNVERIFIED

    if not REGISTRY.exists():
        m["meta.registrations"] = m["meta.refuted"] = UNVERIFIED
        return m

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = reg.get("registrations", [])
    if not reg.get("verified_against_osf"):
        # The list exists but nobody has checked it against the account it claims to describe.
        m["meta.registrations"] = m["meta.refuted"] = UNVERIFIED
        return m

    m["meta.registrations"] = _spell(len(rows))
    scored = [r for r in rows if r.get("refuted") is not None]
    if len(scored) == len(rows) or all(
            r.get("refuted") is not None or r.get("status", "").startswith("prospective")
            or r.get("kind") in ("campaign", "spatial_curve")     # carry no outcome of their own (T7_5 rule)
            for r in rows):
        ref = sum(r["refuted"] for r in scored)
        tot = sum(r["predictions"] for r in scored)
        m["meta.refuted"] = f"{_spell(ref)} of {_spell(tot)}"
    else:
        m["meta.refuted"] = UNVERIFIED
    return m


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

    meta = meta_claims()
    for tag, val in meta.items():
        claims[tag] = {"value": val}
    unver = [t for t, v in meta.items() if v == UNVERIFIED]
    if unver:
        print(f"  {len(unver)} self-description claim(s) UNVERIFIED and will print that way "
              f"on the page: {', '.join(unver)}")
        print("  fix: check registrations.json against the OSF account, set "
              "verified_against_osf true")

    text = io.open(SRC, encoding="utf-8").read()
    missing = []

    def sub(m):
        tag = m.group(1)
        if tag not in claims:
            missing.append(tag)
            return m.group(0)
        v = claims[tag]["value"]
        # Counts in the tens of thousands are unreadable without a separator, and the summary
        # is prose. The threshold sits above any four-digit value so that a year is never
        # punctuated into something that looks like a count.
        if isinstance(v, int) and not isinstance(v, bool) and abs(v) >= 10000:
            return f"{v:,}"
        return str(v)

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
