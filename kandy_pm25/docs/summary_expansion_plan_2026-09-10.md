# Plan: the summary expanded to three pages, covering the whole work

**Written 2026-09-10.** The brief: the summary should cover everything — the PM2.5 model itself,
why the failed approaches failed, the validation machinery, and what the work means for
measurement and policy — while staying compact and understandable.

**Nothing here is written yet.** Every measurement below was taken from the current files.

---

## 0. Decisions taken

| | ruling |
|---|---|
| **length** | **One document, three pages.** The two-page constraint is retired for this document. |
| **audience** | **Researchers and PhD supervisors.** Leads with the method and what is new; keeps detection limits and the refutation record prominent; tolerates technical density. |
| **model detail** | **Components named, one equation.** State the decomposition once as real mathematics, then say what each term is and where it comes from. |
| **policy scope** | **The measurement-priority ordering** and **exposure weighting**. ⚠ **Not** the campaign costing. ⚠ **Not** the attributable-burden projection, which the F.110 review deliberately demoted to Appendix E. |

---

## 1. The budget, measured rather than guessed

The current summary is **1,460 words on exactly two pages**, so the page holds about **730 words**
at the present settings: 12 pt Times New Roman, 1.25 cm margins, `linespread 0.95`.

**Three pages is therefore a ceiling of about 2,190 words.** The plan below budgets **2,010**,
leaving roughly 180 words of slack. That slack is not padding to be spent. Three pages has a hard
edge exactly as two did, and the project has twice cut body text before noticing that the overflow
came from the title block or from a paragraph splitting across a break. **Measure where the space
went before cutting anything.**

Current distribution, for reference:

| section | words |
|---|---:|
| Three results | 555 |
| Where the model stops | 298 |
| Demonstration | 187 |
| The problem | 160 |
| How the model is built | 139 |
| How the work is done | 63 |
| header line | 22 |

Two observations from that table. **`How the model is built` is 139 words and contains no model** —
it describes two design properties, conservation and exact removal, and never says how a
concentration field is computed. And **the failures, the validation machinery and the policy
implications together occupy 63 words**, at the very bottom, after the reader has decided.

---

## 2. The structure proposed

Ten sections, 2,010 words. Sections marked **NEW** do not exist today.

| | section | words | change |
|---|---|---:|---|
| 1 | header line | 30 | corrected, see §5 |
| 2 | The problem | 150 | trimmed from 160 |
| 3 | **What is new** | 70 | **NEW** |
| 4 | **The model** | 190 | rebuilt from the 139-word section |
| 5 | What each observation is worth | 380 | compressed from ~400 |
| 6 | A measurement that changed the method | 150 | compressed from ~200 |
| 7 | **Eight approaches that did not work** | 200 | **NEW** |
| 8 | Where the model stops | 280 | from 298, gains the dispersion result |
| 9 | **How the work was checked** | 200 | **NEW**, absorbs the 63-word coda |
| 10 | Kandy, and what it implies for measurement | 300 | from 187 |
| | contact | 15 | |

### §3. What is new — 70 words

Currently absent, and a researcher asks it within thirty seconds. **State it with the concession,
because conceding is what makes the rest credible.** The thesis §3.4 already splits it four ways
and the summary should carry the same split: the **idea is not new** — withholding an observation
to price it is standard observing-system practice — what is new is the **exact nesting**, which
turns an ablation into a measurement, the **budget-matched transfer** to a city with no monitors,
and **two empirical results**.

### §4. The model — 190 words

The decomposition set once as a real equation, with the four terms named and sourced. Under the
Peradeniya rules the thesis will number its display equations; the summary has no chapter
structure, so it carries the equation unnumbered.

🟢 **No build change is needed.** Checked: `pandoc --list-extensions=markdown` reports
`+tex_math_dollars` **on by default**, and `build_summary.py` passes plain `markdown`, so `$...$`
already renders through the xelatex path.

What the section must convey, in order: concentration as a **uniform regional background plus a
local increment redistributed by a unit-mean pattern**; the **temporal anchor** as a boosted model
on free drivers, conformally wrapped and re-anchored annually to a satellite product; the
**background** as a rural floor carrying a seasonal shape; the **pattern** as emissions times
terrain confinement; and the **two correction terms** in a clause each. Then the two design
properties that are already written well and should survive nearly verbatim: **conservation** and
**exact removal**.

⚠ **The honest note belongs here, not in a caveat later:** the pattern is the weakest component,
and §8 will say by how much.

### §5. What each observation is worth — 380 words

Merges the present results 1 and 2. Keeps the ladder, the saturation-at-one-station finding, the
background rung and the donor-recovery caveat, the tropical reversal, and the clustering caveat.

🔴 **It must gain the loss reversal, which the summary does not currently contain anywhere.** The
present text ends *"a programme following the pooled advice would buy the wrong instrument first"*,
and the thesis abstract narrows exactly that sentence: it holds for **daily city-mean accuracy**
and reverses on **exceedance detection**, where the background wins and the interval excludes zero.
As it stands **the summary asserts something the thesis has withdrawn**. One clause fixes it.

### §7. Eight approaches that did not work — 200 words, NEW

Eight failures in 200 words is 25 words each, which is a list and not an argument.
**Group them into three kinds and give each kind its lesson**, then name the individual attempts
in a single trailing sentence:

- **Transfer failures** — a physics-informed network moved between continents, a rigid physical
  form fitted across cities, a conditional neural process trained across cities. The lesson is
  that what transfers is physics, not fitted parameters.
- **Identifiability failures** — fine-tuning on the two sensors that exist, which memorised their
  coordinates; five reconstructions of the regional background. The lesson is that a quantity can
  be unrecoverable from the data no matter which model is asked.
- **Information failures** — five attempts to find spatial structure, and a pre-registered learned
  pattern. The lesson is §8's, and this is where the two sections join.

⚠ **This section is what distinguishes the work, and it should read as a result rather than as an
apology.** The thesis's own framing is that an attempt yields about as much when it fails as it
declared before it started, and that sentence, or one like it, belongs here.

### §8. Where the model stops — 280 words

Keeps the paired-site test, the refuted resolution hypothesis, the within-cell versus between-cell
spread, the registered learned-pattern null with its detection limit, and the seven-family
tournament.

🔴 **It must gain the dispersion result.** The terrain-steered solver, the component built to place
the local increment, **lowers** neighbourhood ranking from 0.371 to 0.274 and improves 3 of 10
cities. Both external reviewers said independently that this belongs at the front. It is the
clearest evidence in the project that the framework is honest about its own machinery, and the
summary does not currently mention it.

### §9. How the work was checked — 200 words, NEW

The validation engine, which currently exists as a 63-word coda. Four things, and they are
different in kind, so the section should not blur them:

1. **The protocol.** A city with a dense network is reduced to the target's information budget and
   scored against the monitors withheld from it. Budget matching is what makes the test
   informative.
2. **The claims gate.** Every number regenerates from its source file at build time and the build
   refuses to produce a document if prose and data disagree.
3. **Pre-registration.** Predictions and abandonment conditions lodged before the analysis ran.
4. **The refutation record**, which is the evidence that 1 to 3 are real rather than decorative.

⚠ **Every number in item 4 is currently wrong or unverifiable. See §5 below before writing it.**

### §10. Kandy, and what it implies for measurement — 300 words

The present 187-word Demonstration, plus the policy content the brief asks for.

Keeps: the partition and its sensitivity, the explicit statement that it is a decomposition and
not source apportionment, the two independent record checks and what they do and do not cover,
and the sentence that the neighbourhood map is not validated.

Gains, per the ruling: **the measurement-priority ordering** — what a city with no monitors should
buy first, why the tropical answer differs from the pooled one, and the episode caveat that
qualifies it — and **exposure weighting**, that population-weighted exposure runs about 9 per cent
above the area mean, so an area average understates what people breathe.

⚠ **Framed for a research reader, not as a ministry brief.** The ordering is presented as what the
measurement implies, with its bounds attached, not as a recommendation the thesis is entitled to
make on its own authority.

---

## 3. What comes out to make room

Compression, not deletion, and no language is compressed — the space comes from content, per the
standing rule.

- **Result 3, the contamination finding, loses about 50 words.** It is the most inward-facing
  block in the document: a reader who has not yet accepted the framework cannot follow a story
  about which rung a contamination deflates. Reduce it to its transferable lesson — *a
  monitor-trained covariate does not inflate its own step, it deflates the step above, so the
  obvious test finds nothing* — and keep the numbers that make it checkable.
- **`The problem` loses 10 words.** It is already tight and this is trimming, not restructuring.
- **The old coda disappears entirely**, its content rebuilt as §9.

---

## 4. Ordering of the work

1. **Resolve the registration count** (§5). Blocking: three sections quote it.
2. **§4 The model** and **§3 What is new** — the two that change what the document is.
3. **§7 Failures** and **§9 How the work was checked** — the two genuinely new sections.
4. **§5** gains the loss clause; **§8** gains the dispersion result. Both are corrections of
   existing claims and are the highest-value edits per word in the plan.
5. **§10 Kandy** expands.
6. **Compression pass** on result 3 and the problem statement.
7. **Build, then count pages.** ⚠ `build_summary.py` prints a word count and **does not check the
   page count**. Read it out of the PDF.

---

## 5. 🔴 The self-description numbers are stale, and one cannot currently be verified

The header line and the closing coda are **plain prose, not `{{claim:}}` tokens**, so the gate that
protects every other number in the document does not see them. Checked against the sources:

| the summary says | the actual state |
|---|---|
| 40,000 words | **42,637** |
| 35 figures, 10 chapters | correct |
| **eight OSF pre-registrations** | **three sources give three answers.** Thesis Appendix B says **six**. CLAUDE.md's newest block says **nine**. Enumerating identifiers across CONTEXT.md, CLAUDE.md and the ledger yields **eight**, one of which (`r7a3w`) is a project rather than a registration. |
| sixth negative result on the spatial question | **seventh.** F.111, the embedding test registered at `6udm3`, is on the same question and resolves 0.130. |
| fourteen of thirty predictions refuted | counts **five** registrations. The two newest, `6udm3` and `z89kt`, are not included. |

🔴 **Root cause, and it is upstream of the summary.** `T7_5_registrations` is **hand-maintained in
`t_tables.py`**, hardcoded rather than generated from a scored file, so it never learned about the
embedding and precipitation registrations. The thesis body discusses both — the embedding test
appears eight times in Chapter 8 and precipitation has its own subsection in Chapter 9 and a row in
Table 9.1 — while the registrations table and Appendix B's count still describe six. **This is
gotcha #90's family: the gate checks the values in the cells, not whether the table is current.**

🔴 **And the count cannot be settled from the repository.** Of eighteen `prereg_*.md` files, only
**five** contain a recoverable OSF identifier, and one of those disagrees with the project record:
`prereg_chemistry_2026-09-01.md` carries `bkpyr` where CLAUDE.md records the chemistry registration
as `kx23c`. **The authoritative source is the OSF account itself.**

**Action, before any of the three affected sections is written:** open the OSF account, list the
registrations, fix `t_tables.py` and Appendix B, and only then write the header line. ⚠ **Until
that is done the registration count is unquotable**, and writing around it with a vague phrase
would be worse than leaving it out.

---

## 6. Open questions

1. 🔴 **The title.** The document's title still leads with *an information-tiered decomposition
   for PM2.5*, a product, while the body argues a measurement method — and the expansion planned
   here moves the body further in that direction. ⚠ **The project record contradicts itself**:
   CLAUDE.md's 2026-09-09 block says *"RESOLVED — user chose option C"*, naming *"Measuring what an
   air quality observation is worth: an information-budget approach, demonstrated at Kandy, Sri
   Lanka"*, and a later subsection of the same block records the merged title now on disk. **The
   disk is authoritative; the decision is not recorded consistently.** Worth settling once, for the
   thesis and the summary together.
2. **Whether the eight failures are named individually.** The plan groups them into three kinds
   and names them in one trailing sentence, because eight entries in 200 words is a list. If any
   single failure is worth its own sentence, it is the **fine-tuning attempt**, which memorised
   two sensor coordinates and reached a correlation of 0.9999 at the exact sensor location while
   inflating the map: it is the most vivid single illustration of the identifiability problem in
   the project.
3. **Whether three pages is a ceiling or a target.** The plan treats it as a ceiling and budgets
   180 words under it. If it is a target, that slack can go to §7 or §10.

---

## 7. Decisions taken 2026-09-10

| | ruling |
|---|---|
| **title** | 🟢 **SETTLED 2026-09-10, candidate 1:** *The marginal value of an air quality observation, measured on an information-tiered grey-box decomposition: 48 cities, demonstrated at Kandy.* Contribution in the stressed opening position, the model as the instrument that made the measurement possible, 20 words. Applies to the thesis and the summary together. |
| **OSF count** | **Write around it for now.** Draft proceeds; the number is supplied later. |
| **style** | A measured contract, see below. The summary never received the F.110 style pass and carries its pre-pass signature. |

### The self-description numbers become claim tokens

"Write around it" is implemented as **tokens, not placeholders.** The word count, figure count and
registration count are currently plain prose, so the gate that protects every other number in the
document cannot see them, which is precisely why all three went stale. A literal placeholder
inherits that defect: the document still builds and can still be sent with a wrong number.

Written as `{{claim:}}` tokens instead, `build_summary.py` **refuses to build** until each
resolves. Word count and figure count are generated by the build. The registration count reads one
small source-of-truth file, filled once from the OSF account and thereafter the only place the
number lives.

🟢 This also closes the defect behind Section 5: `T7_5_registrations` stops being hand-maintained
in `t_tables.py` and reads the same file.

### Style contract, measured rather than asserted

The summary was never given the F.110 pass and carries its pre-pass signature:

| tic | summary now | thesis after F.110 | cap for the rewrite |
|---|---:|---:|---:|
| `rather than` | 8 in 1,460 words = **5.5 / 1,000** | 4.4 / 1,000 | **4 / 1,000** (about 8 uses in 2,010 words) |
| paragraphs opening bold | **7 of 23 = 30%** | 15% | **15%** |
| em or en dash | 0 | 0 | 0, enforced by the build |

Also barred: negation followed by assertion, of which the summary carries one
(*"which is not a small effect but an absent one"*); three-item lists used for rhythm; and section
headings carrying colons or questions. ⚠ **Every mechanical substitution is read by hand.** Three
inverted the sense during the thesis pass and needed repair, and the guards catch syntax, not
meaning.

## 8. Title candidates, 2026-09-10

The ruling is to keep the marginal-value framing and to carry the model's identity as well.
**"Grey-box" earns its place**: it is established vocabulary for a physics-and-learning hybrid, so
a modelling reader places the work from the title alone. "Information-tiered" is this project's own
coinage but is self-explanatory in context.

Constraints every candidate satisfies: no promise of a validated neighbourhood map, per Section
9.9; Kandy visible, which matters at Peradeniya and in the CEA correspondence; and one wording
used for the thesis and the summary together.

1. **Contribution first, mechanism second.**
   *The marginal value of an air quality observation, measured on an information-tiered grey-box
   decomposition: 48 cities, demonstrated at Kandy.*
2. **Model first, payload second.**
   *An information-tiered grey-box decomposition for urban PM2.5: the marginal value of each
   observation, measured by withholding across 48 cities and demonstrated at Kandy.*
3. **Method named in the field's own terms.**
   *Pricing observations by withholding them: an information-tiered grey-box decomposition of
   urban PM2.5 across 48 cities, demonstrated at Kandy.*

## 9. The pending data, and what each source would and would not validate

**On the user's instruction, 2026-09-10:** the summary should say that institutional data has not
yet been obtained and that the model becomes checkable when it arrives. **Four sources, not one.**

Placed in Section 10 immediately after the sentence declaring the neighbourhood map unvalidated,
because that is where the reader is already asking what would settle it.

### Status, read out of `EMAILS_TO_SEND.md` rather than assumed

⚠ **The four are at four different stages, and the summary should not flatten them into one
"awaiting reply".** Two are further along than that phrasing implies and one is behind it.

| source | recorded state | what it would test |
|---|---|---|
| **Department of Meteorology** | 🟢 **Replied 2026-08-16.** Hourly rainfall, temperature and humidity available; hourly wind **not** available, three-hourly is; a university letter earns a fee discount. **Blocked on a quotation, not on permission.** | station **humidity** inside the basin, the only route to checking the low-cost sensor correction slopes (**W5**); three-hourly **wind**, which tests whether reanalysis represents valley ventilation on the timescale the field varies |
| **CEA** | 🟢 **Replied 2026-08-25** requiring a Director General letter, a data request form and a signed agreement; the reply pack was prepared 2026-08-26. Hourly regulatory record **2019 to 2026-05**, gap 2021-07 to 2022-10. **Granted in principle; paperwork in progress.** | the **level and its hourly variation against a regulatory instrument**, which is the open half of **W11** |
| **FECT** | Sent 2026-08-12, **no reply logged**, follow-up due 2026-09-02. The file's own note is that a visit is likelier to work than a second email. | the **calibration records** behind the two sensors the temporal anchor is fitted to |
| **NBRO** | ⚠ **Drafted as Email 4 and not logged as sent.** The status table records only emails 1 to 3. | a **regional background series**, which the ladder prices as the largest single gain, and a Kandy record running to thirteen years |

⚠ **Two corrections to that file, which predates later findings.** It says CEA's passive NO2
network *"would give the first spatial validation at Kandy"* — **superseded**: the network was
demoted once the spatial ceiling was measured as information-limited, and its value is the
partition and local activity tracing. It also says FECT's records would *close* W5 — **W5 was
corroborated in 2026-08 by F.64**, so the records would settle rather than open it. Neither
superseded claim should reach the summary.

### 🔴 The scoping that must travel with the statement

*"Awaiting validation"* is honest only if it says **which axis becomes checkable**. Written
loosely it promises that the pending data would validate the model, and the project's own results
say it would not.

**What the four together would settle:** the **level and its hourly variation** against a
regulatory instrument, the **sensor calibration** the anchor depends on, and whether **reanalysis
represents ventilation** inside the basin. Three of the largest declared weak points.

**What none of them would settle:** the **neighbourhood-scale map**. Fixed stations cannot check a
within-city pattern, and the shortfall is measured: **F.100**, one city needs **96 to 304 sites**
to beat the spatial benchmark by a detectable margin; **F.103**, on 43 dense-network cities
deliberate siting does not measurably beat convenience siting, so the gap is information and not
design.

⚠ **The phrasing is therefore a scoped statement, not a promise.** Something with the shape of:
*four institutional records have been requested and none is yet in hand; the meteorological office
and the environmental authority have both replied and access is in progress. Together they would
make the level, the sensor calibration and the represented ventilation checkable for the first
time, and would settle a level discrepancy this work reports as open. They would not make the
neighbourhood map checkable, which needs a campaign of the size Chapter 9 designs.*

🟢 **This strengthens the document rather than hedging it.** For a research reader it converts
"unvalidated" into a stated, costed and already-initiated next step, without claiming anything the
evidence does not carry. **Budget: about 75 words**, from the 180 words of slack, leaving 105.
