"""Assemble the section drafts into a single manuscript for the PDF build.

Concatenates docs/paper/draft_s*.md in section order, strips the drafting-notes block from
each, prepends the front matter, and stages the figures. Deliberately mechanical: all authoring
happens in the section files, so the manuscript is a build product and is never edited by hand.

Output
    docs/paper/manuscript_kandy.md      (build source)
    docs/paper/fig/                     (staged figures)
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
FIGSRC = DIR.parents[1] / "results" / "figures" / "paper2026"
FIGDIR = DIR / "fig"
OUT = DIR / "manuscript_kandy.md"
newline_ = chr(10)
# The sentence Table 1 is spliced after. Kept as a constant so a reworded
# sentence fails loudly at the assertion rather than silently dropping the table.
TABLE1_ANCHOR = "Table 1 and {{fig:scorecard}} give the full scorecard."

ORDER = [
    "draft_s1_s2_intro.md",
    "draft_s3_information_bound.md",
    "draft_s4_formulation.md",
    "draft_s5_validation.md",
    "draft_s6_results.md",
    "draft_s7_forbids.md",
    "draft_s8_s9_discussion.md",
]

# figure key -> (number, caption). Only figures that exist as files are inserted; the rest
# are left as text callouts so the manuscript builds before the suite is complete.
# tag -> (file stem, caption). NUMBERS ARE NOT SET HERE. The drafts refer to figures by
# {{fig:tag}} and the assembler numbers them by order of first appearance, so inserting or
# dropping a figure never leaves a stale "Figure 9" in the prose. This is the durable fix for
# a trap this project has hit before.
FIGURES = {
    "studyarea": ("F1_study_area",
                  "The Kandy basin, 15 by 15 km. Terrain, towns, the Mahaweli river and its "
                  "ventilation corridor to the north-west, and the Hantana range closing the "
                  "basin to the south. Marked are the city centre, the valley-floor research "
                  "site whose single published year of observation is used here, and the "
                  "ridge-top low-cost sensor. The second low-cost sensor, at Akurana, lies "
                  "about 1 km beyond the northern edge of the domain. Pure geography: no "
                  "model output appears in this panel."),
    "schematic": ("F2_schematic",
                  "The decomposition and its gauge condition. (a) Inputs and terms, coloured "
                  "by whether the observations can constrain them. (b) The unit-mean gauge: "
                  "the area average of the field returns the anchor exactly. (c) The two "
                  "correction terms and the defect each repairs."),
    "bound": ("F3_information_bound",
              "The information bound. (a) Where each bounded parameter of the rigid ansatz "
              "came to rest within its admissible range; two sit exactly on their lower "
              "bounds. (b) Per-city change from a Gaussian to a Student-t likelihood: mean "
              "correlation rises while mean coverage falls. (c) Annual mean against distance "
              "from the nearest tuning sensor, for the zero-shot and two-sensor fine-tuned "
              "fields."),
    "protocol": ("F6_protocol",
                 "Validation by borrowed ground truth. (a) The protocol. (b) What each city "
                 "was given and what it was scored against; 174 monitors were withheld across "
                 "the ten cities, and Kandy has none to withhold."),
    "scorecard": ("F7_scorecard",
                  "The ten-city scorecard. Seasonal and diurnal correlation, level bias and "
                  "fine spatial rank, scored against withheld monitors. Spatial rank is shown "
                  "against each city's own permutation null at the 95th percentile. "
                  "Chandigarh has no usable station pairs."),
    "ktm": ("F8_kathmandu",
            "Kathmandu, the deepest single test in the panel. The model was given two "
            "stations and is compared against the rest. (a) Seasonal cycle. (b) Diurnal "
            "cycle. (c) Fine spatial rank, per-station anomaly after the network mean is "
            "removed within each hour. The panels carry no scores of their own: the scored "
            "values, which apply the completeness screens and exclude the two anchor "
            "stations, are in Table 1."),
    "cycles": ("F_cycles",
               "Kandy seasonal and diurnal shape against the two local sensors. Unlike the "
               "Kathmandu comparison this one is in sample, because the temporal anchor is "
               "calibrated to these sensors, so agreement measures the calibration rather "
               "than skill. It is shown for the shape it carries, in particular the "
               "afternoon minimum, which is counter-intuitive and verified."),
    "episode": ("F_episode",
                "The December 2022 episode. (a) The field at the peak hour, on a scale "
                "adapted to that hour so the within-basin structure is visible. (b) Basin "
                "mean through the 48 hours, against the WHO 24 hour interim target."),
    "burden": ("F_burden",
               "Exposure and burden. (a) Four exposure tiers by year; the area mean "
               "understates exposure because population concentrates in the "
               "higher-concentration core. (b) Attributable and avoidable deaths for 2023, "
               "with the interval reflecting field uncertainty only."),
    "uncertainty": ("F11_uncertainty",
                    "The shipped interval is correctly scaled and incorrectly centred. "
                    "(a) Where observations fall relative to the interval, as shipped and "
                    "after removing each sensor's own median offset. (b) Coverage by season."),
    "nullpower": ("F12_null_power",
                  "What the earth-observation embedding null could have detected at 80 per "
                  "cent power. The measured partial correlations lie far inside the range the "
                  "test was blind to, so the null excludes only large effects."),
}

# Figures planned but not yet regenerated against the post-cap fields. Callouts to these are
# removed from the prose at assembly rather than left dangling. Empty as of
# 2026-08-14: ktm, cycles, episode and burden were rebuilt against the current fields.
DEFERRED: set[str] = set()

FRONT = """---
title: "Estimating urban PM~2.5~ where no monitor exists: an information-bounded decomposition, validated by transfer across ten cities"
author: "Daminda Alahakoon"
date: ""
---

*Department of Environmental Sciences, University of Peradeniya, Sri Lanka.*

*Supervisors: Dr. U. Ranatunga, Dr. M. Dehideniya.*

**DRAFT. Not for circulation beyond named reviewers.**
Assembled from the section drafts by `assemble_manuscript.py`; edit the sections, not this file.

---

"""


# The section drafts use Unicode for readability. Latin Modern has no glyph for superscript
# minus, superscript digits, or Greek in the monospace face, so xelatex drops them silently and
# the PDF loses its units. Substituted here rather than in the drafts, which stay readable.
TEX_SUBS = [
    ("µg m⁻³", r"$\mu$g m$^{-3}$"),
    ("μg m⁻³", r"$\mu$g m$^{-3}$"),
    ("s⁻¹", r"s$^{-1}$"),
    ("10⁻⁶", r"$10^{-6}$"),
    ("PM~2.5~", "PM~2.5~"),          # pandoc subscript, leave alone
]
# Greek inside fenced code blocks has no glyph in the mono face; spell it out there only.
CODE_SUBS = [("λ", "lambda"), ("ε", "eps"), ("∇", "grad"), ("·", "."), ("−", "-")]


def tex_safe(text: str) -> str:
    for a, b in TEX_SUBS:
        text = text.replace(a, b)

    def fix_block(m):
        body = m.group(0)
        for a, b in CODE_SUBS:
            body = body.replace(a, b)
        return body

    text = re.sub(r"```.*?```", fix_block, text, flags=re.S)
    # inline code spans have the same font problem
    text = re.sub(r"`[^`\n]*`",
                  lambda m: m.group(0).replace("ε", "eps").replace("λ", "lambda"), text)
    return text


def _bib_keys() -> set:
    """Every key defined in references.bib."""
    txt = (DIR / "references.bib").read_text(encoding="utf-8")
    return set(re.findall(r"^@[a-zA-Z]+\{([^,]+)", txt, flags=re.M))


def citations(text: str, keys: set) -> tuple:
    """Convert [Key] and [K1, K2] to pandoc citeproc syntax, and report unknown keys.

    The drafts use a plain bracket form because it reads better while writing. Anything
    inside brackets that is not a known key is left untouched, so ordinary bracketed
    prose and markdown links survive.
    """
    unknown = set()

    def sub(m):
        inner = m.group(1)
        parts = [p.strip() for p in inner.split(",")]
        if not parts or not all(re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", p) for p in parts):
            return m.group(0)
        if not any(p in keys for p in parts):
            return m.group(0)
        for p in parts:
            if p not in keys:
                unknown.add(p)
        return "[" + "; ".join("@" + p for p in parts) + "]"

    # not preceded by ! (image) and not followed by ( (markdown link)
    pattern = r"(?<!\!)\[([^\[\]\n]{3,80})\](?!\()"
    out = re.sub(pattern, sub, text)
    return out, unknown


def unnumber_headings(text: str) -> str:
    """Strip our own section numbers; LaTeX numbers the headings itself.

    Without this every heading renders twice-numbered, as "1 1. Introduction".
    """
    return re.sub(r"^(#+)\s+\d+(?:\.\d+)?\.?\s+", lambda m: m.group(1) + " ", text, flags=re.M)


def strip_notes(text: str) -> str:
    """Remove the drafting-notes block and the leading draft banner."""
    text = re.split(r"\n##+ Drafting notes", text)[0]
    text = re.sub(r"\*Draft, Phase 5.*?\*\n", "", text, flags=re.S)
    text = re.sub(r"\n---\n\s*\Z", "\n", text)
    return unnumber_headings(text.strip()) + "\n"


def resolve_figures(text: str) -> tuple:
    """Number figures by order of first appearance and splice each one in.

    Returns (text, n_placed, deferred_seen). Tokens are {{fig:tag}} with an optional trailing
    panel letter, e.g. {{fig:bounda}} renders as "Figure 3a".
    """
    FIGDIR.mkdir(exist_ok=True)
    order, seen_deferred = [], set()

    # Match against the known tags, longest first. A bare [a-z]+ is greedy and swallows the
    # panel letter, so {{fig:bounda}} parses as the tag "bounda" and the figure is never found.
    known = sorted(set(FIGURES) | DEFERRED, key=len, reverse=True)
    TOKEN = r"\{\{fig:(" + "|".join(known) + r")([a-c])?\}\}"

    for m in re.finditer(TOKEN, text):
        tag = m.group(1)
        if tag in DEFERRED:
            seen_deferred.add(tag)
        elif tag in FIGURES and tag not in order:
            order.append(tag)

    number = {t: i + 1 for i, t in enumerate(order)}

    def token(m):
        tag, panel = m.group(1), m.group(2) or ""
        if tag in number:
            return f"Figure {number[tag]}{panel}"
        return ""                      # deferred: drop the callout, keep the sentence

    text = re.sub(r"\s*\(" + TOKEN + r"\)",
                  lambda m: "" if m.group(1) in DEFERRED else " (" + token(m) + ")", text)
    text = re.sub(TOKEN, token, text)

    for tag in order:
        stem, cap = FIGURES[tag]
        src = FIGSRC / f"{stem}.png"
        if not src.exists():
            continue
        shutil.copy2(src, FIGDIR / f"{stem}.png")
        block = f"{newline_}{newline_}![**Figure {number[tag]}.** {cap}](fig/{stem}.png)"                 f"{newline_}{newline_}"
        m = re.search(rf"Figure {number[tag]}[a-c]?", text)
        if not m:
            continue
        end = text.find(newline_ * 2, m.end())
        end = len(text) if end == -1 else end
        text = text[:end] + block + text[end:]

    return text, len(order), seen_deferred


CLAIMS = DIR.parents[1] / "data" / "processed" / "modular" / "claims.json"


def _claims_are_fresh() -> None:
    """Refuse to build on a stale claims file (Phase 2, plan 2026-09-01).

    The manuscript quotes numbers; the numbers live in CSVs; nothing connected them. That gap
    produced three wrong headline claims (C2, C3, C4) which survived a full re-validation
    because the re-validation updated the pooled ladder and left the stratified and frame
    statistics untouched. Regenerating on every build is the only thing that closes it.
    """
    import subprocess
    r = subprocess.run([sys.executable, str(DIR.parents[1] / "scripts" / "build_claims.py"),
                        "--check"], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            "claims.json disagrees with a fresh recomputation -- an input changed under the "
            "manuscript. Re-run scripts/build_claims.py and re-check every affected sentence.\n"
            + r.stdout + r.stderr)


def resolve_claims(text: str) -> tuple:
    """Substitute {{claim:tag}} tokens from the generated claims file.

    `{{claim:step.bud2_bud3}}`        -> 40.6
    `{{claim:frame.city_days|,}}`     -> 28,930      thousands separator
    `{{claim:step.geography|pct}}`    -> 10.8%

    An unknown tag RAISES rather than rendering empty: a silently dropped number reads as a
    finished sentence and is exactly how a wrong figure survives proofreading.
    """
    if not CLAIMS.exists():
        raise RuntimeError(f"{CLAIMS} missing -- run scripts/build_claims.py first")
    _claims_are_fresh()
    rows = json.loads(CLAIMS.read_text(encoding="utf-8"))["claims"]

    used, unknown = set(), set()

    def token(m):
        tag, fmt = m.group(1), m.group(2)
        if tag not in rows:
            unknown.add(tag)
            return m.group(0)
        used.add(tag)
        v = rows[tag]["value"]
        if fmt == ",":
            return f"{v:,}"
        if fmt == "pct":
            return f"{v}%"
        return str(v)

    text = re.sub(r"\{\{claim:([A-Za-z0-9_.]+)(?:\|([,a-z]+))?\}\}", token, text)
    if unknown:
        raise RuntimeError(
            "unknown claim tag(s): " + ", ".join(sorted(unknown))
            + "\nEvery number in the manuscript must resolve to a generated claim. Add it to "
              "scripts/build_claims.py with its statistic, n, source and ledger reference.")
    return text, used, set(rows) - used


def main() -> None:
    abstract = (DIR / "abstract.md").read_text(encoding="utf-8").strip()
    body = "\n\n---\n\n".join(strip_notes((DIR / f).read_text(encoding="utf-8"))
                              for f in ORDER)
    keys = _bib_keys()
    body, unknown = citations(body, keys)
    table1 = (DIR / "table1.md").read_text(encoding="utf-8").strip()
    if TABLE1_ANCHOR not in body:
        raise RuntimeError("Table 1 anchor sentence not found; it was reworded")
    body = body.replace(TABLE1_ANCHOR, TABLE1_ANCHOR + 2 * newline_ + table1)
    body, n_fig, deferred = resolve_figures(body)
    body, claims_used, claims_unused = resolve_claims(body)
    body = tex_safe(body)
    # citeproc places the bibliography at this div; without it the list is appended
    # unlabelled, which is what happened on the first build.
    body += (2 * newline_ + "---" + 2 * newline_ + "# References" + 2 * newline_
             + "::: {#refs}" + newline_ + ":::" + newline_)
    OUT.write_text(FRONT + abstract + 2 * newline_ + "---" + 2 * newline_ + body,
                   encoding="utf-8")

    words = len(re.sub(r"!\[.*?\]\(.*?\)", "", body).split())
    print(f"wrote {OUT.name}")
    print(f"  sections {len(ORDER)}   figures numbered and placed {n_fig}")
    print(f"  claims resolved {len(claims_used)}, generated but unused {len(claims_unused)}")
    print(f"  body words {words:,}")
    used = set(re.findall(r"@([A-Za-z][A-Za-z0-9]*)", body))
    print(f"  citations {len(used)} distinct, bibliography has {len(keys)}")
    if unknown:
        print(f"  UNKNOWN KEYS: {', '.join(sorted(unknown))}")
    uncited = sorted(keys - used)
    if uncited:
        print(f"  in bib but never cited ({len(uncited)}): {', '.join(uncited)}")
    if deferred:
        print(f"  deferred figures, callouts removed: {', '.join(sorted(deferred))}")


if __name__ == "__main__":
    main()
