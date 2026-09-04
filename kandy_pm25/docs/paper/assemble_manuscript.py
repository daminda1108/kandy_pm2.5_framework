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
# The rewrite has no Table 1 anchor yet; assembly of the table is deferred until section 3
# settles. Set to None so the assembler does not assert on a sentence that no longer exists.
TABLE1_ANCHOR = None

# 2026-09 rewrite order (rewrite_plan_2026-08-22.md). The previous eight files are retained
# on disk as the superseded draft; they are NOT built. Editing them has no effect.
ORDER = [
    "draft_s1_problem.md",
    "draft_s2_formulation.md",
    "draft_s3_design.md",
    "draft_s4_value_of_information.md",
    "draft_s5_where_it_stops.md",
    "draft_s6_kandy.md",
    "draft_s7_forbids.md",
    "draft_s8_discussion.md",
]

# figure key -> (number, caption). Only figures that exist as files are inserted; the rest
# are left as text callouts so the manuscript builds before the suite is complete.
# tag -> (file stem, caption). NUMBERS ARE NOT SET HERE. The drafts refer to figures by
# {{fig:tag}} and the assembler numbers them by order of first appearance, so inserting or
# dropping a figure never leaves a stale "Figure 9" in the prose. This is the durable fix for
# a trap this project has hit before.
FIGURES = {
    "protocol": ("F7_protocol",
                 "Budget-matched validation. (a) The protocol: a city with a dense network is "
                 "given only what the target city budget allows, and scored against the "
                 "monitors withheld. The budget match is what makes the test informative -- a "
                 "model that has seen thirty monitors measures a capability the target will "
                 "never have. (b) Withheld monitors per city and (c) scored city-days across "
                 "the full panel, both drawn from the scored file rather than recorded by hand, "
                 "so they cannot drift from the analysis."),
    "studyarea": ("F1_study_area",
                  "The demonstration city. Kandy sits on the floor of a steep valley in the "
                  "central highlands of Sri Lanka, closed to the south by the Hantana range and "
                  "open to the north-west along the Mahaweli valley, which is its principal "
                  "ventilation corridor. Terrain, drainage and settlement only: no model output "
                  "appears in this panel, which is why it is the one figure in this paper that "
                  "cannot go out of date."),
    "schematic": ("F8_schematic",
                  "The formulation. (a) The decomposition and its gauge: a spatially uniform "
                  "regional background plus a local increment redistributed by a unit-mean "
                  "pattern. Because the pattern integrates to unity, the spatial average of the "
                  "field returns the temporal anchor exactly, so an error in the pattern is an "
                  "error in where material sits and never in how much there is. (b) The "
                  "information budget: what each tier may use and the first quantity it can "
                  "constrain. Tiers are nested, and a lower one is recoverable bit-exactly from "
                  "a higher one when a stream is withheld -- the property that turns an "
                  "ablation into a measurement. Bud4 is a declared design assumption, not a "
                  "validated rung. (c) The observation operator: the model reports a cell mean "
                  "while a monitor samples a point inside it, so a systematic offset and a "
                  "representativeness error must be carried explicitly. Without them a "
                  "centring error is read as a failure of interval width."),
    "ladder": ("F2_ladder",
               "What each increment of information buys, as the median across cities of the "
               "per-city reduction in daily RMSE. (a) The pooled ladder, coloured by whether a "
               "stream is freely available everywhere, a local instrument, or regional. Free "
               "static geography is worth about as much as the first local instrument, and "
               "monitors three through eight are indistinguishable from zero. (b) The same two "
               "rungs stratified by latitude band, with the number of cities in each cell on "
               "the axis. The ordering inverts in the deep tropics, so the pooled "
               "recommendation is the wrong recommendation there."),
    "streams": ("F3_streams",
                "Two results about what is being measured. (a) The same two monitors priced by "
                "four estimators. The three non-linear learners agree to within a few "
                "percentage points; ridge regression, unable to exploit sixty-eight sensorless "
                "predictors, reports the monitor as worth four times more. The measured value "
                "of an observation is not a property of the observation alone. (b) Replacing a "
                "fused PM2.5 product with raw satellite retrievals. The satellite rung itself "
                "barely moves, so the fused product was not inflating its own score; the rung "
                "above it roughly doubles, because a product trained on a city's monitors "
                "already encodes part of what those monitors would say."),
    "confounds": ("F4_confounds",
                  "The confound that cannot be sampled away. Instrument class is strongly "
                  "associated with latitude band: the deep-tropical cell is dominated by "
                  "low-cost sensors while the higher-latitude bands are reference-dominated. "
                  "Worldwide there are too few densely reference-monitored tropical cities to "
                  "break the association by sampling, so results are reported stratified by "
                  "class throughout. The regime that most needs a sensorless method is the "
                  "regime where reference monitoring is scarcest."),
    "paired": ("F1_paired",
               "The spatial limit, measured rather than asserted. (a) Two sites 300 m apart "
               "inside a single model cell, sampled by the same instrument over the same "
               "three-hour window: observed against the field as shipped and after re-running "
               "the physics ten times finer in area. (b) The same ratio against model "
               "resolution, coarse to fine; refinement does not close the gap, and a "
               "pre-registered prediction that it would is refuted. (c) Where the contrast "
               "goes, through each stage of the build. It is relocated, not destroyed -- the "
               "dispersed field still spans an order of magnitude at the shipped resolution, in "
               "different places from where the survey measured it."),
    "withinpixel": ("F5_withinpixel",
                    "What survives the limit. (a) The spread inside a typical cell exceeds the "
                    "spread between cells across the whole map, so most within-city variation "
                    "is sub-grid by the model's own structure. This is simultaneously the "
                    "explanation for the paired-site result and the reason a pointwise product "
                    "is not available. (b) The check on it, reported as uninformative: because "
                    "the predicted within-cell spread is far smaller than the observed range, "
                    "every high site saturates at the top quantile and every low one at the "
                    "bottom, so the test re-detects the amplitude gap rather than testing "
                    "ordering. The single non-saturated site runs the other way."),
    "field": ("F_field",
              "The delivered field and what it is made of. (a) The annual-mean surface for the "
              "demonstration year, with terrain contours at 200 m intervals; the enclosed floor "
              "and the ventilated ridge are visible as a smooth gradient rather than as sharp "
              "structure, which is the honest appearance of a 1 km product in this terrain. (b) "
              "The local increment alone -- what is left after the spatially uniform regional "
              "background is removed. It is this component, not the total, that a local "
              "intervention can act on. (c) The regional-local partition per year. The share is "
              "read from the post-cap artefact: an earlier background that allowed the regional "
              "term to exceed the total on some hours put this near 25 per cent, and imposing "
              "the physical constraint that local sources cannot emit negatively moves it to "
              "about half."),
    "spatiotemporal": ("F_spatiotemporal",
                       "The delivered field across its two well-supported axes, both rows drawn "
                       "from the same hourly product. Top: seasonal composites, spanning a "
                       "factor of {{claim:kandy.season_swing}} from the stagnant north-east "
                       "monsoon to the ventilated south-west. Bottom: diurnal composites, "
                       "spanning a factor of {{claim:kandy.phase_swing}}, with both traffic "
                       "peaks resolved and a midday minimum. Each row carries one shared colour "
                       "scale, so panels are comparable within a row; the near-uniform "
                       "appearance of the ventilated panels is a property of the model and not "
                       "of the rendering, because when the total falls to the background the "
                       "increment that carries all spatial structure goes to zero with it. Note "
                       "that deep night sits ABOVE the midday trough, by a factor of "
                       "{{claim:kandy.night_over_midday}}: the minimum is at midday, not at "
                       "night."),
    "cycles": ("F_cycles",
               "Seasonal and diurnal cycles against the two ground sensors. The agreement is "
               "close and it is NOT evidence of skill: the temporal anchor is fitted to these "
               "same sensors and then amplitude-sharpened to their observed swing, so this "
               "figure measures the calibration and is in sample by construction. It is "
               "included because a reader is entitled to see that the calibration took, and "
               "because the out-of-sample version of the same comparison, at a city the model "
               "was never fitted to, appears later in this section."),
    "episode": ("F_episode",
                "A stagnation episode, December 2022. (a) The field at the peak hour. (b) The "
                "basin-mean trace across 48 hours, against the WHO 24-hour interim target. The "
                "episode is reproduced without any local observation of it, because the "
                "conditions that produce it -- a shallow boundary layer, weak flow and an "
                "advected regional load -- are present in the reanalysis drivers. This is the "
                "regime the model is most useful in and the one where its interval is widest."),
    "scorecard": ("F7_scorecard",
                  "The full validation panel: ten cities, each scored against monitors withheld "
                  "from the fit, on four axes. The level and the seasonal cycle transfer "
                  "everywhere. The diurnal cycle transfers in the deep tropics and fails "
                  "outside it, which is a regime statement rather than an average one and is "
                  "why no pooled diurnal number appears anywhere in this paper. The fine "
                  "spatial rank is estimable in nine of the ten cities and is weak in most of "
                  "them; the tenth is left blank because it could not be computed, which is not "
                  "the same as a measured zero."),
    "kathmandu": ("F8_kathmandu",
                  "The same construction at a city it was not built for, and the out-of-sample "
                  "counterpart to the in-sample cycles figure. The model is given two stations "
                  "and scored against the {{claim:ktm.scored_stations}} withheld. (a) Seasonal "
                  "and (b) diurnal cycles reproduce with a level bias of "
                  "{{claim:ktm.level_bias_pct}} per cent; (c) the station-by-station spatial "
                  "anomaly, the axis where agreement is weakest. This city is the panel's most "
                  "favourable case and is shown as such, not as typical."),
    "uncertainty": ("F11_uncertainty",
                    "Why a coverage failure must be decomposed before it is diagnosed. (a) The "
                    "nominal 90 per cent interval covers {{claim:kandy.cov90}} per cent of "
                    "sensor hours, which reads as intervals that are too narrow. It is not: the "
                    "misses are one-sided, {{claim:kandy.miss_below}} per cent below against "
                    "{{claim:kandy.miss_above}} per cent above. (b) Removing each sensor's own "
                    "median offset, and changing nothing about the width, restores coverage to "
                    "{{claim:kandy.cov90_recentred}} per cent. The width was right and the "
                    "centring was wrong, because the model reports an areal mean and the sensor "
                    "samples a point inside it -- the term the observation operator carries "
                    "explicitly."),
    "bound": ("F3_information_bound",
              "Three independent signatures of the same limit. (a) A rigid physical ansatz "
              "fitted across cities drives two of its six parameters onto their bounds: the "
              "data do not contain enough information to identify them, so they are declared "
              "rather than estimated. (b) A flexible neural spatial model improves as more "
              "structure is added and then stops, short of the ceiling, in the same place. (c) "
              "The memorisation signature: error near a training sensor against error far from "
              "one. A model fine-tuned on two sensors reproduces them almost exactly and "
              "degrades with distance, which is what learning sensor identity looks like rather "
              "than learning the basin."),
    "nullpower": ("F12_null_power",
                  "What the spatial nulls could have detected. For each city the measured "
                  "partial correlation is shown against the smallest effect the test could have "
                  "found at 80 per cent power given its sample size. The detectable range runs "
                  "from {{claim:null.min_detectable_lo}} to "
                  "{{claim:null.min_detectable_hi}}, so these nulls exclude large residual "
                  "structure and say nothing about moderate structure. A null result is a "
                  "statement about power before it is a statement about nature, and reporting "
                  "one without its detection limit is how a null becomes a false confirmation."),
    "chemistry": ("F6_chemistry",
                  "A chemical check on the decomposition's load-bearing assumption, using "
                  "back-trajectory sector -- independent of the composition product -- to "
                  "classify air-mass origin. Continental-Indian air is measurably more "
                  "secondary-rich, and therefore more aged, than marine air: the ordering the "
                  "decomposition requires, and its first chemical support. The registered "
                  "prediction that recirculated local air would be the freshest is refuted, "
                  "because stagnation gives local precursors time to age in place, so treating "
                  "the local increment as fresh primary aerosol is too simple. Bars show "
                  "medians with bootstrap intervals; n is the number of days per sector."),
}

# Figures planned but not yet regenerated against the post-cap fields. Callouts to these are
# removed from the prose at assembly rather than left dangling. Empty as of
# 2026-08-14: ktm, cycles, episode and burden were rebuilt against the current fields.
DEFERRED: set[str] = set()

FRONT = """---
title: "What is a monitor worth? Exact model degradation as a measurement instrument for urban PM~2.5~ in data-scarce cities"
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

    text = re.sub(r"\{\{claim:([^}|]+)(?:\|([,a-z]+))?\}\}", token, text)
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
    if TABLE1_ANCHOR is not None:
        table1 = (DIR / "table1.md").read_text(encoding="utf-8").strip()
        if TABLE1_ANCHOR not in body:
            raise RuntimeError("Table 1 anchor sentence not found; it was reworded")
        body = body.replace(TABLE1_ANCHOR, TABLE1_ANCHOR + 2 * newline_ + table1)
    body, n_fig, deferred = resolve_figures(body)
    abstract, _, _ = resolve_claims(abstract)
    body, claims_used, claims_unused = resolve_claims(body)
    body = tex_safe(body)
    # citeproc places the bibliography at this div; without it the list is appended
    # unlabelled, which is what happened on the first build.
    body += (2 * newline_ + "---" + 2 * newline_ + "# References" + 2 * newline_
             + "::: {#refs}" + newline_ + ":::" + newline_)
    doc = FRONT + abstract + 2 * newline_ + "---" + 2 * newline_ + body
    # Nothing token-shaped may reach the PDF. A tag the resolver's regex cannot match used to
    # survive as literal text without raising -- silent pass-through, the same failure class as
    # a merged-but-empty data stream.
    leftover = re.findall(r"\{\{[^}]{0,80}\}\}", doc)
    if leftover:
        raise RuntimeError("unresolved tokens reached the manuscript: "
                           + ", ".join(sorted(set(leftover))[:6]))
    OUT.write_text(doc, encoding="utf-8")

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
