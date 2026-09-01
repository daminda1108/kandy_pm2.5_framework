"""Mechanical pre-submission gate — the checks that must never be done by eye.

PHASE 2 of docs/improvement_plan_2026-09-01.md.

Every check here exists because the corresponding failure actually happened, and each one is
invisible to a careful read of the prose:

  G1  claims freshness      C2/C3/C4 -- three headline numbers survived a full re-validation
                            because the pooled ladder was updated and the stratified and frame
                            statistics were not. Nothing connected the prose to the CSVs.
  G2  unresolved tokens     a {{claim:...}} or {{fig:...}} that reaches the PDF is a number the
                            reader never sees and the author believes is there.
  G3  figure numbering      pandoc-crossref is NOT installed (gotcha #58), so every figure
                            number is hardcoded and shifts when a figure moves. Editors desk-
                            reject on "Figure 1. Figure 3." and on stray `??`.
  G4  build markers         raw assembler scaffolding reaching the manuscript.
  G5  colour vision         F.83 -- `turbo` is the one palette that fails a CVD check, and it
                            was used on the most consequential maps.
  G6  retired claims        every number the project has retired, grepped for by value, so a
                            resurrected figure fails the build rather than the review.

Exit 0 only if every gate passes. Run before any submission or circulation.

Usage:  .venv/Scripts/python.exe scripts/submission_gate.py [--manuscript PATH]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAPER = REPO / "docs" / "paper"
DEFAULT_MS = PAPER / "manuscript_kandy.md"

# Retired numbers, keyed by the claim they belonged to. Matched as whole tokens so "0.48" does
# not fire on "10.4828". Sources: CONTEXT.md section 3, and the 2026-09-01 audit.
RETIRED = {
    r"\b0\.244\b": "local fraction f -- superseded by the coherence cap (F.43); use 0.48",
    r"\b25\.3\s*%": "f as a percentage from additive_partition.csv -- stale, renamed _v1_superseded",
    r"\b2\.573\b": "eps0 pre-cap -- use 3.69 (F.57)",
    r"\b0\.911\b": "spatial CV R2 -- a label-construction artefact, never a spatial result",
    r"90\s*(?:%|per cent)\s+vehic": "refuted as a mass share (F.66); traffic is 7.6% of PM2.5 mass",
    r"\b32,396\b": "city-days from the superseded pre-F.84 run -- the frame is 28,930 (C4)",
    r"\b47\s+cities\b": "the superseded frame -- 48 cities scored (C4)",
    r"four guaranteed properties": "two guarantees, one measured mechanism, one discharged (F.74)",
    r"\b25\.6\s*%": "the pre-F.84 first rung -- inflated by an under-powered Bud0 (F.84/F.85)",
}


def _run(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  -- {detail}" if detail and not ok else ""))
    return ok


def g1_claims_fresh() -> bool:
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "build_claims.py"), "--check"],
                       capture_output=True, text=True)
    return _run("G1 claims reproduce from the scored files", r.returncode == 0,
                r.stdout.strip().replace("\n", " | "))


def g2_tokens(text: str) -> bool:
    left = re.findall(r"\{\{[^}]{0,60}\}\}", text)
    return _run("G2 no unresolved {{...}} tokens", not left, ", ".join(sorted(set(left))[:6]))


def g3_figures(text: str) -> bool:
    bad = []
    bad += ["`??` in text"] * len(re.findall(r"\?\?", text))
    bad += ["raw \\ref{fig"] * len(re.findall(r"ef\{fig", text))
    bad += ["`Fig.~` (unresolved crossref)"] * len(re.findall(r"Fig\.~", text))
    # "Figure 1. Figure 3." -- two numbers colliding in one caption
    bad += ["adjacent figure numbers"] * len(re.findall(r"Figure \d+\.\s*Figure \d+", text))
    # every figure number must appear, in order, with none skipped
    nums = sorted({int(n) for n in re.findall(r"Figure (\d+)", text)})
    if nums and nums != list(range(1, max(nums) + 1)):
        missing = sorted(set(range(1, max(nums) + 1)) - set(nums))
        bad.append(f"gap in figure numbering: {missing} never referenced")
    return _run("G3 figure numbering clean and gapless", not bad, "; ".join(sorted(set(bad))))


DRAFT_BANNER = "DRAFT. Not for circulation"


def g4_markers(text: str) -> bool:
    """Build markers in the BODY. The front matter is exempt while the draft banner stands.

    The assembler deliberately stamps "Assembled from the section drafts by
    `assemble_manuscript.py`; edit the sections, not this file" into the front matter -- that is
    a working instruction, not stray scaffolding, and it goes when the banner goes. Failing on
    it every run would train us to ignore G4, which is worse than not having G4.
    """
    # The one sanctioned occurrence, verbatim. Anything else is scaffolding that leaked.
    SANCTIONED = ("Assembled from the section drafts by `assemble_manuscript.py`; "
                  "edit the sections, not this file.")
    scope = text.replace(SANCTIONED, "", 1) if DRAFT_BANNER in text else text
    bad = [m for m in ("assemble_manuscript", "TODO", "FIXME", "XXX", "LOREM") if m in scope]
    if DRAFT_BANNER in text:
        print("         note: draft banner present -- remove it, and the front-matter build "
              "note, before submission")
    return _run("G4 no build markers or placeholders in the body", not bad, ", ".join(bad))


def g5_palette() -> bool:
    p = REPO / "scripts" / "palette_cvd_check.py"
    if not p.exists():
        return _run("G5 colour-vision check available", False, f"{p.name} not found")
    r = subprocess.run([sys.executable, str(p)], capture_output=True, text=True)
    out = (r.stdout + r.stderr).lower()
    # F.83: turbo is the one palette that fails. The gate is that it is not reported as in use.
    fails = r.returncode != 0 or ("turbo" in out and "fail" in out)
    return _run("G5 no CVD-failing palette in use", not fails, "turbo still reported in use (F.83)")


# A paper MUST be able to discuss what it retired -- "a published estimate of 0.244, used in
# earlier versions of this work, lies below ..." is correct scholarship, not a resurrection.
# A retired value inside a sentence that also retires it is reported and not failed.
RETIRING_LANGUAGE = re.compile(
    r"supersed|retire|earlier version|previously|no longer|formerly|revised|refut|"
    r"we now|stale|withdraw|corrected",
    flags=re.IGNORECASE)


def g6_retired(text: str) -> bool:
    """Fail on a retired number ASSERTED; report one that is discussed as retired."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    asserted, discussed = [], []
    for pat, why in RETIRED.items():
        for s in sentences:
            if re.search(pat, s, flags=re.IGNORECASE):
                (discussed if RETIRING_LANGUAGE.search(s) else asserted).append((pat, why, s))
                break
    for pat, why, s in discussed:
        print(f"         note: {pat} appears in a retiring context -- allowed. "
              f"\"{s.strip()[:88]}...\"")
    return _run("G6 no retired number asserted as current", not asserted,
                "; ".join(f"{p} ({w})" for p, w, _ in asserted))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", default=str(DEFAULT_MS))
    a = ap.parse_args()
    ms = Path(a.manuscript)

    print(f"submission gate  --  {ms.name}\n")
    results = [g1_claims_fresh(), g5_palette()]

    if not ms.exists():
        print(f"  [SKIP] G2-G4, G6: {ms.name} not built yet")
    else:
        text = ms.read_text(encoding="utf-8", errors="surrogateescape")
        results += [g2_tokens(text), g3_figures(text), g4_markers(text), g6_retired(text)]

    n_ok = sum(results)
    print(f"\n{n_ok}/{len(results)} gates pass")
    if n_ok < len(results):
        print("BLOCKED -- do not circulate or submit until every gate is green.")
        return 1
    print("clear to build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
