"""Assemble the thesis from its chapter files, resolving every token.

Two token types, both resolved here so a number or a figure reference cannot drift from the
data that produced it:

    {{claim:tag}}     replaced from kandy_pm25/data/processed/modular/claims.json, and the
                      build FAILS if the tag is missing or if claims.json is older than the
                      scored files it derives from.
    {{fig:tag}}       replaced with "Figure 3.2" and the image inserted at first use, numbered
                      by chapter in order of first appearance.
    {{tbl:tag}}       the same for tables.

WHY THE TOKENS. The manuscript this project already wrote carried nine numbers that had gone
stale against their own source, including one stated three different ways in a single document.
Every one was caught by a gate like this and none by reading.

Usage: python assemble.py
Out:   build/thesis.md  (the input to build_docx.py; never edit it)
"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "thesis" / "chapters"
DIAGRAMS = ROOT / "thesis" / "diagrams"
TABLES = ROOT / "thesis" / "tables"
FIGURES = ROOT / "thesis" / "figures"
OUT = ROOT / "build" / "thesis.md"

REPO = Path(r"D:\ProjectCD\kandy_pm25")
CLAIMS = REPO / "data" / "processed" / "modular" / "claims.json"
BUILD_CLAIMS = REPO / "scripts" / "build_claims.py"
VENV_PY = REPO / ".venv" / "Scripts" / "python.exe"

CLAIM_TOKEN = re.compile(r"\{\{claim:([A-Za-z0-9_.]+)\}\}")
VIS_TOKEN = re.compile(r"\{\{(fig|tbl|dia):([A-Za-z0-9_]+)\}\}")
DRAFTING = re.compile(r"(?ms)^## Drafting notes.*?(?=^## |\Z)")

# tag -> (file stem, caption). The file is looked up in thesis/diagrams then thesis/figures.
#
# A token ALONE ON A LINE places the image with its caption. The same token inline becomes
# just the label, so "as {{dia:protocol}} shows" reads as "as Figure 7.1 shows". This is the
# convention the project's manuscript already uses and it removes the whole class of error
# where prose says Figure 4 and the image is Figure 5.
VISUALS: dict[str, tuple[str, str]] = {
    "protocol": (
        "D5_validation_protocol",
        "Budget matched validation. A city with a dense network is reduced to the target "
        "city's information budget and then scored against the monitors withheld from it. "
        "Blue marks what the model is permitted to see; red marks what is held back. The "
        "budget match is what makes the test informative, because a model that has seen "
        "thirty monitors measures a capability the target city will never have."),
}


def claims_fresh() -> bool:
    """Recompute the claims and refuse to build on drift. Same gate as the manuscript."""
    if not CLAIMS.exists():
        print("claims.json missing")
        return False
    r = subprocess.run([str(VENV_PY), str(BUILD_CLAIMS), "--check"],
                       cwd=str(REPO), capture_output=True, text=True)
    if r.returncode != 0:
        print("CLAIMS GATE FAILED. The stored claims disagree with a fresh recomputation:")
        print((r.stdout + r.stderr)[-1500:])
        return False
    return True


def load_claims() -> dict:
    return json.load(io.open(CLAIMS, encoding="utf-8"))["claims"]


def resolve_claims(text: str, claims: dict) -> tuple[str, list[str]]:
    missing: list[str] = []

    def sub(m):
        tag = m.group(1)
        if tag not in claims:
            missing.append(tag)
            return m.group(0)
        return str(claims[tag]["value"])

    return CLAIM_TOKEN.sub(sub, text), missing


def resolve_visuals(text: str) -> tuple[str, dict, list[str]]:
    """Number figures, tables and diagrams by chapter, in order of first appearance.

    Numbers are never written in the source. Inserting a figure at chapter three therefore
    cannot leave a stale "Figure 3.4" four chapters later, which is a defect this project has
    already shipped once.
    """
    counters: dict[tuple[str, int], int] = {}
    assigned: dict[str, str] = {}
    missing: list[str] = []
    chapter = 0

    # figures and diagrams share one sequence per chapter, because a reader does not
    # distinguish them; tables have their own.
    seq = {"fig": "fig", "dia": "fig", "tbl": "tbl"}

    def label_for(kind: str, tag: str) -> str:
        key = f"{seq[kind]}:{tag}"
        if key not in assigned:
            ck = (seq[kind], chapter)
            counters[ck] = counters.get(ck, 0) + 1
            word = "Table" if kind == "tbl" else "Figure"
            assigned[key] = f"{word} {chapter}.{counters[ck]}"
        return assigned[key]

    out_lines: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^#\s+Chapter\s+(\d+)", line)
        if m:
            chapter = int(m.group(1))

        placed = VIS_TOKEN.fullmatch(line.strip())

        # A table token alone on a line pulls in the generated fragment from thesis/tables/.
        # Same convention as figures, and for the same reason: the number in "Table 5.1" is
        # assigned here, so inserting a table cannot leave a stale reference elsewhere.
        if placed and placed.group(1) == "tbl":
            tag = placed.group(2)
            lab = label_for("tbl", tag)
            frag = TABLES / f"{tag}.md"
            if not frag.exists():
                cand = sorted(TABLES.glob(f"{tag}*.md"))
                frag = cand[0] if cand else frag
            if not frag.exists():
                missing.append(f"tbl:{tag}")
                out_lines.append(lab)
                continue
            body = io.open(frag, encoding="utf-8").read().strip().splitlines()
            # the generated fragment starts "Table: <title>"; pandoc wants the caption to
            # carry the number, and the number is only known here
            if body and body[0].startswith("Table:"):
                body[0] = f"Table: {lab}. {body[0][len('Table:'):].strip()}"
            out_lines.append("")
            out_lines.extend(body)
            out_lines.append("")
            continue

        if placed and placed.group(1) in ("fig", "dia"):
            kind, tag = placed.group(1), placed.group(2)
            lab = label_for(kind, tag)
            if tag not in VISUALS:
                missing.append(f"{kind}:{tag}")
                out_lines.append(lab)
                continue
            stem, caption = VISUALS[tag]
            path = None
            for folder in (DIAGRAMS, FIGURES):
                if (folder / f"{stem}.png").exists():
                    path = (folder / f"{stem}.png").as_posix()
                    break
            if path is None:
                missing.append(f"file for {kind}:{tag} ({stem}.png)")
                out_lines.append(lab)
                continue
            # pandoc's implicit_figures turns a lone image into a figure with its alt text
            # as the caption, which is where the reference.docx Caption style lands.
            out_lines.append(f"![{lab}. {caption}]({path})")
            out_lines.append("")
            continue

        out_lines.append(VIS_TOKEN.sub(lambda mm: label_for(mm.group(1), mm.group(2)), line))
    return "\n".join(out_lines), assigned, missing


def main() -> int:
    files = sorted(CHAPTERS.glob("*.md"))
    if not files:
        print(f"no chapters in {CHAPTERS}")
        return 1

    print("assembling the thesis")
    if not claims_fresh():
        return 1
    claims = load_claims()
    print(f"  claims.json fresh, {len(claims)} claims")

    parts, all_missing = [], []
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        t = DRAFTING.sub("", t)               # drafting notes never reach the output
        parts.append(t.rstrip() + "\n")
    text = "\n\n".join(parts)

    # ORDER MATTERS. Visuals first: a table fragment is pulled in whole and carries its own
    # {{claim:}} tokens, so resolving claims before insertion leaves those tokens untouched
    # and the build fails on them. Figure captions may carry tokens for the same reason.
    text, assigned, vis_missing = resolve_visuals(text)
    all_missing += vis_missing
    text, missing = resolve_claims(text, claims)
    all_missing += missing

    leftover = re.findall(r"\{\{[^}]+\}\}", text)
    if all_missing or leftover:
        print("\nUNRESOLVED TOKENS. Not writing output.")
        for t in sorted(set(all_missing)):
            print(f"  missing claim: {t}")
        for t in sorted(set(leftover))[:20]:
            print(f"  unresolved:    {t}")
        return 1

    OUT.write_text(text, encoding="utf-8")
    words = len(re.sub(r"[^\w\s]", " ", text).split())
    figs = sum(1 for k in assigned if k.startswith(("fig:", "dia:")))
    tbls = sum(1 for k in assigned if k.startswith("tbl:"))
    print(f"  chapters {len(files)}")
    print(f"  words    {words:,}")
    print(f"  figures  {figs}   tables {tbls}")
    print(f"  wrote    {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
