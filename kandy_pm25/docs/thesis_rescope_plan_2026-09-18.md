# Thesis rescope and guideline compliance — plan, 2026-09-18

Two theses are built from one source of truth, both compliant with the ENS4998 Final Report
Format and the attached Physical Review style guide. **Thesis A is the degree submission and is
built first.**

Sources: `D:\Downloads\Guidlines Thesis (1).docx` (department) and `D:\Downloads\styleguide (1).pdf`
(APS, cited by the guidelines for referencing).

---

## 1. What the guidelines require

**Page layout.** A4. Margins left 1.25 in, right and top 1 in, bottom 1.25 in. Times New Roman.
Chapter title 14 pt bold UPPERCASE centred. Headings 11 pt bold. Body justified, line spacing 1.5.
Standard British English.

**Page numbering.** Lower centre, consecutive. Declaration to Acknowledgement in **roman**; Table
of Contents onwards in **Arabic**.

**Length. 40–75 pages, exclusive of appendices.** Introduction not more than 40 % of pages;
Results and Discussion not less than 30 %.

**Sequence.** Front page (their template) · Declaration · Abstract (single page, ≤ 350 words,
single spaced, justified) · Acknowledgement · Table of Contents · List of Figures · List of Tables ·
List of Abbreviations · Introduction · Methodology · Results and Discussion · Conclusions and
Future Work · References · Appendices (no page limit).

**Headings.** No numbered heading deeper than three levels (`1.1.1` acceptable, `1.1.1.1` not).
Anything deeper is included without a number.

**Figures.** Any figure taken from another source must be cited.

**Referencing.** A single style throughout, per the attached style guide: APS numeric, `[1]` in
text, entries of the form `J. M. Smith, Phys. Rev. B 26, 1 (1982)`.

**Title page template.** Title 14 pt bold; "An undergraduate research project report submitted by"
12 pt; name and registration number 14 pt; department, faculty, university, "In partial fulfilment
of" 12 pt; degree line, "University of Peradeniya, Sri Lanka" and the year 12 pt bold.

## 2. Where the document stood on 2026-09-18 (measured in Word, not estimated)

| | measured | required |
|---|---|---|
| pages | **136** (≈ 131 excluding present appendices) | 40–75 |
| words | 42,315 in the built file; 41,134 by the assembler | — |
| abstract | **1,194 words** | ≤ 350, one page |
| structure | 11 narrative chapters | four body chapters, fixed order |
| citations | author–date (Chicago) | APS numeric |
| cross-references | **253** typed "Chapter N" / "Section N.N" | must resolve per document |
| deepest numbered heading | 7.2.1 | compliant |
| British English | 5 instances of "organization" | compliant after fix |

Page budget that follows: **75 pages ≈ 18,000–20,000 words of text plus about 25 figures.** The
body of each thesis is therefore roughly half the present document; the remainder moves to
appendices, which are unlimited and excluded from the count.

## 3. Decisions taken (user, 2026-09-18)

1. **Rescope rather than compress.** Two separate theses are built, A and B.
2. **Thesis A is the ENS4998 submission** and is built first. B follows.
3. **Overflow goes to appendices in full** — nothing is summarised away, nothing is dropped.
4. **Citations switch to APS numeric.**
5. **Figure and table numbering stays chapter-based** (Figure 3.5, Table 3.2); the APS guide is
   followed for referencing, not for figure and table conventions.
6. **Titles** (revisable after the outlines are approved):
   - **A** — AN HOURLY KILOMETRE-SCALE FINE PARTICULATE MATTER RECONSTRUCTION FOR KANDY,
     SRI LANKA: CONSTRUCTION, VALIDATION WITHOUT LOCAL GROUND TRUTH, AND MEASUREMENT PRIORITIES
   - **B** — MEASURING WHAT AN AIR QUALITY OBSERVATION IS WORTH: AN INFORMATION-BUDGET APPROACH
     FOR CITIES WITHOUT MONITORS, DEMONSTRATED AT KANDY
7. **Registration number S/20/005, year 2026** (user, 2026-09-18). **Plan approved.**

## 4. Repository architecture

```
#writing/
  theses/a/chapters/...          thesis A, its own prose and order
  theses/b/chapters/...          thesis B
  theses/{a,b}/manifest.yaml     ordered section list + which are appendices
  shared/                        fragments included verbatim by both
  src/                           one set of figure and table builders (unchanged)
  build/build_docx.py --thesis a|b   → build/thesis_a.docx, build/thesis_b.docx
```

**`shared/` exists to stop two copies of one fact drifting apart** — the model definition, the
data inventory, the registrations table, the reproducibility appendix. Same reasoning as
gotcha #90: a fact has one generated source and every document points at it.

**Cross-references become tokens.** A shared fragment cannot say "Section 7.2": that section
carries a different number in each thesis and is an appendix in one of them. Every internal
reference becomes `{{sec:label}}`, resolved by `assemble.py` against the manifest of the thesis
being built, and `lint.py` **refuses a typed "Chapter N" or "Section N.N" anywhere**. Without
this, restructuring two documents from one pool is 253 chances to point at the wrong section, and
no existing gate can see it (family of gotchas #90, #94).

## 5. Phases

### Phase 0 — shared infrastructure, built once
- `make_reference_docx.py` rewritten to the guideline typography: margins (3.18 / 2.54 / 2.54 /
  3.18 cm), 14 pt bold uppercase centred chapter titles, 11 pt bold headings, justified 1.5 body,
  a single-spaced abstract style.
- Post-processing pass for what pandoc cannot express: the departmental title page, a section
  break so front matter numbers in roman and the body restarts at Arabic 1, bottom-centre page
  number fields, and real Word TOC / List of Figures / List of Tables fields.
- Word COM is available on this machine (`WINWORD.EXE` present), so the build **updates those
  fields and reads back the page count itself** rather than estimating.
- `{{sec:label}}` resolution in `assemble.py`; lint rule banning typed section references.
- APS numeric CSL (`american-physical-society.csl`, downloaded) wired into the pandoc call.
- **Compliance gate** in the build: body pages within 40–75 excluding appendices, Introduction
  ≤ 40 %, Results and Discussion ≥ 30 %, abstract ≤ 350 words and one page, no numbered heading
  deeper than three levels. A failure blocks the build, as the claims gate does.

### Phase 1 — Thesis A (the submission)
Outline approved first, then prose is moved, then the abstract is rewritten to 350 words, then
build and iterate against the page gate.

### Phase 2 — Thesis B
The same, with the Kandy field construction moving to appendices instead of the panel.

### Phase 3 — verification on both
British English pass; List of Abbreviations; source credit in the caption of every figure built
on third-party data (Natural Earth, OpenStreetMap, the DEM, satellite products); every citation
checked as rendered; PDF exports.

## 6. Thesis A — proposed outline and page budget

Front matter (roman): title page · declaration · abstract (≤ 350 words) · acknowledgement ·
contents · list of figures · list of tables · list of abbreviations.

| chapter | content, from the present document | ~pages |
|---|---|---|
| **1. INTRODUCTION** | air quality as an environmental health problem and why monitoring is scarce (ch01) · Kandy, its valley and its airshed (ch02) · what is already known for Kandy and Sri Lanka (ch03) · the gap · **aims and objectives** (new, explicit) · scope of claims | ~16 |
| **2. METHODOLOGY** | data and their provenance (ch04) · the background-and-increment decomposition, the gauge, the anchor (ch06) · construction of the Kandy field, uncertainty and the ventilated-hour floor · how a field is validated with no local ground truth, including the budget-matched panel in brief (ch07.1) · reproducibility and the claims machinery in brief (ch10) | ~22 |
| **3. RESULTS AND DISCUSSION** | the reconstructed field: level, seasonal and diurnal behaviour · the checks that carry weight and the open level discrepancy (7.8) · interval calibration (7.9) · the partition and what it does not mean (6.6, with the chemistry bound) · exposure weighting (7.11) · where the field stops: change of support and within-cell spread (ch08, condensed) · what the panel measurement implies for Kandy's band (7.2, 7.3, condensed) · what the results support (8.8) | ~28 |
| **4. CONCLUSIONS AND FUTURE WORK** | conclusions · measurement priorities for Kandy (9.1 with Table 9.1) · future work (9.2–9.5) · the closing statement (9.8) | ~7 |
| **References** | APS numeric | ~4 |

Body ≈ 73 pages; Introduction ≈ 22 % (limit 40 %); Results and Discussion ≈ 38 % (floor 30 %).

Appendices, unlimited: **A** the 48-city panel and the budget ladder in full · **B** the spatial
ceiling, the model-family tournament and the registered nulls · **C** approaches that did not work
(ch05) · **D** software, the claims machinery and the registrations table (ch10) · **E** retired
numbers and the illustrative burden projection (ch11) · **F** chemistry.

## 7. Thesis B — outline sketch (after A)

Body: the sensorless problem and value-of-information positioning · the panel, the information
budgets and the exact nesting that turns an ablation into a measurement · the ladder, the
inversion in the tropics and the four losses · the measured ceilings and the registered nulls ·
Kandy as the demonstration and its measurement priorities. Appendices carry the Kandy field
construction, the Kandy-specific checks, the failed approaches, chemistry and the software.

## 8. Risks, and what each is guarded by

| risk | guard |
|---|---|
| 253 cross-references silently wrong after restructuring | `{{sec:label}}` tokens + lint ban; build fails on a dangling label |
| a fact corrected in one thesis and not the other | `shared/` fragments; claims tokens; one generated source per fact |
| page count guessed instead of measured | Word COM reads it back; the gate blocks the build |
| the spatial learning curve leaking into prose as a result | it has none; both theses say registered and underway, nothing more |
| APS style applied where the guidelines do not ask for it | referencing only; figure and table numbering stays chapter-based |
| prose moved between chapters losing the framing it was written for | outlines approved before prose moves; a human read after each phase |
