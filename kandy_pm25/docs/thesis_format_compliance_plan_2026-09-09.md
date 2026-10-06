# Plan: bringing the thesis onto the Peradeniya format

**Written 2026-09-09.** The ruling for this plan is the user's: *we will follow these rules for
now*. "These rules" are the Postgraduate Institute of Science, University of Peradeniya,
**Format of Project Report/Thesis, M.Sc., M.Phil. and Ph.D. Degrees, 2018** — the nearest
authoritative published Peradeniya house style, since the Faculty of Science undergraduate
handbook carries no thesis format section and leaves it to the department.

**Everything below was checked against the built document, not assumed.** Where a claim rests on
an inspection, the inspection is named.

## 0. Rulings taken, 2026-09-09

The three open decisions in this plan were put to the user and settled. They are recorded here so
the rest of the document can be read as settled rather than as options.

| | ruling | consequence |
|---|---|---|
| **G8** caption and table font size | **Follow the guide: 10 pt.** The 12 pt floor was a summary instruction extended to the thesis by analogy; it is withdrawn for captions and table text. Body stays 12 pt. | one change in `make_reference_docx.py` |
| **G9** chapter structure | **Do not restructure.** Keep the thematic monograph and make the mapping to the guide's roles explicit in §1.5. | a paragraph in `ch01`; ⚠ **supervisor agreement is still the user's action** |
| **G12** equations | **Set the displayed equations as real mathematics and number them. Leave the running prose in backticks alone.** | `ch06`, plus numbering in `assemble.py` |

⚠ **One standing caveat.** The PGIS guide is a *postgraduate* document. The department's own
undergraduate sheet, if one exists, overrides it on every point. Nothing in this plan is worth
executing twice, so **ask the department before the binding and copies decisions**, which are the
only irreversible ones.

---

## 1. What the rules require

Extracted from the guide, sections 1.1 to 1.6, 2.5 and 3.1.

### Page and type

| | required | currently | |
|---|---|---|---|
| paper | A4, ≥80 gsm, **one side only** | A4 | 🟢 |
| body font | Times New Roman 12 | Times New Roman 12 | 🟢 |
| body spacing | 1.5 | 1.5, justified | 🟢 |
| **single-spaced** | declaration, abstract, acknowledgements, contents, list of tables, list of figures, list of abbreviations, table titles, figure captions, references | captions single; **declaration, abstract, acknowledgements and references inherit 1.5** | 🔴 |
| **left margin** | **40 mm** | 35 mm | 🔴 |
| **right margin** | **15 mm** | 25 mm | 🔴 |
| top / bottom margin | 25 mm | 25 mm | 🟢 |
| **page numbers** | roman, top-centre, 10 mm from top edge, for prefatory pages; **arabic from 1**, bottom-centre, 10 mm from bottom edge, from Chapter 1 | **none at all — one section, no PAGE field in any footer** | 🔴 |

### Prefatory pages, in this order

Title → **Declaration** → **Abstract** → Acknowledgements → **Table of Contents** →
**List of Tables** → **List of Figures** → List of Abbreviations → **List of Appendices**.

### Main body

- Each chapter opens **CHAPTER n** in uppercase bold Times New Roman **size 14, centred**, then
  the chapter title in **uppercase bold 14**, then the text after a two-line space.
- Sub-headings numbered `1.1`, `1.1.1`. Bold for sub-titles, italics for emphasis.
- **Figure captions go below the figure, size 10**, single-spaced if more than one line.
- **Table titles go above the table, size 10.**
- **Any table of three to four pages or more moves to an appendix.**
- **Maps must carry coordinates, a linear scale, a directive arrow and an index map** showing the
  locality of the area.
- Abstract **≤ 350 words**, single-spaced, **on one page**, one paragraph preferred, **no
  keywords**.
- References: author-year **or** numeric, one system throughout, one list at the end when the
  chapters describe a coherent study — which they do here.
- SI units, negative exponents rather than solidus, no space between a number and `%`,
  no digits beyond the precision of the instrument.

---

## 2. What the built document already satisfies

Verified by walking `build/thesis.docx` element by element with `python-docx`.

- 🟢 **Figure captions are below the image.** The paragraph order at Figure 1.1 is prose, image,
  caption.
- 🟢 **Table titles are above the table.** At Table 3.1 the caption paragraph precedes the `tbl`
  element.
- 🟢 **Times New Roman throughout**, set on `w:ascii`, `w:hAnsi`, `w:cs` and `w:eastAsia`, so
  Word cannot silently substitute a second face for complex scripts.
- 🟢 **One reference list at the end**, which is what the guide recommends for a coherent study.
- 🟢 **Section numbering to depth three**, matching the specimen.
- 🟢 **A signed declaration exists** and is worded as a declaration of originality.
- 🟢 **A table of contents is generated** by `pandoc --toc --toc-depth 3`.
- 🟢 **No percentage is written with a space before the sign** — zero occurrences.

---

## 3. The gaps, ranked

### 🔴 G1. The abstract is 1,199 words against a 350-word cap

The single largest formal gap, and the only one that cannot be fixed mechanically. It is
**3.4 times the limit** and will not fit on one page at 12 pt single-spaced.

This is a rewrite, not a trim, and the standing constraint that *length is not a concern* does
not apply: the cap is an external rule the user has chosen to follow, and the abstract is the one
place in the document where a hard limit exists. It is the same class of constraint as the
two-page summary.

**Where the displaced material goes:** Chapter 1 already carries §1.4 *Aim and approach*, §1.5
*Structure of the thesis* and §1.6 *Scope of the claims*. A monograph normally carries the long
synopsis there. Nothing needs to be lost.

**The shape to write to**, from the abstract literature and consistent with the guide's
single-paragraph preference: *why the work was done · the gap · the aim · the method · the
findings · the conclusion*. Past tense for what was done and found, present tense for established
facts and for the contribution, third person. **No keywords** — the guide forbids them, which
overrides the general advice to include five to eight.

⚠ **The abstract currently carries 23 claim tokens.** A 350-word abstract cannot hold 23 numbers
and still read as prose. Deciding **which numbers survive into the abstract is a scientific
decision, not a formatting one**, and it should be made deliberately rather than by whichever
sentences happen to survive the cut. The F.110 review already moved two things into the abstract
on purpose — the dispersion failure and the loss reversal — and both must survive.

### 🔴 G2. There are no page numbers anywhere

`build/thesis.docx` has **one section and no `PAGE` field in any footer**. The guide requires two
numbering schemes in two positions, which needs the document split into at least two Word
sections with a restart.

Pandoc cannot do this from markdown. The fix belongs in `make_reference_docx.py` for the footer
styles and in a **new post-pandoc step** for the section break and restart, because the break has
to fall at a place only the assembled document knows.

⚠ **Gotcha #70 applies exactly here.** A page-numbering fix applied by hand to `thesis.docx`
would be destroyed by the next `build_docx.py`. It has to live in the chain.

### 🔴 G3. Prefatory page order is wrong and one list is missing

Three separate defects:

1. **The table of contents lands before the Declaration.** Pandoc inserts `--toc` immediately
   after the title block. Required position is after the Acknowledgements.
2. **List of Figures precedes List of Tables.** The guide has tables first.
3. **There is no List of Appendices**, though Appendices A to E exist.

The first needs a pandoc-level change or a post-pass; the second is a two-block swap in
`ch00_front.md`; the third needs a new `{{listofappendices}}` token in `assemble.py`, built the
same way as the existing two.

### 🔴 G4. Margins are wrong on two edges

Left 35 mm against a required 40, right 25 mm against a required 15. One-line change in
`make_reference_docx.py`, then re-run it. The right margin change **widens the text block by
10 mm and will reflow the whole document**, so it must happen *before* any figure sizing work,
not after.

### 🔴 G5. Four blocks are 1.5-spaced that must be single

Declaration, abstract, acknowledgements and the reference list all inherit `Normal`. Captions and
table text are already single. The fix is a `Bibliography` style override in
`make_reference_docx.py` plus a pandoc div or a post-pass for the three front blocks.

### 🟡 G6. The reference style does not match either specimen

Current output, from `--citeproc` with no CSL, is pandoc's default **Chicago author-date**:

> Abeyratne, Vilani D. K., and Oliver A. Ileperuma. 2006. "Air Pollution Monitoring in the City of Kandy…" *Journal of the National Science Foundation of Sri Lanka* 34 (3): …

The guide's author-year specimen wants initials, the year in parentheses, no quotation marks on
the title, `and` rather than `&`, and a bold volume number:

> Abeyratne, V.D.K. and Ileperuma, O.A. (2006). Air pollution monitoring in the city of Kandy… *Journal of the National Science Foundation of Sri Lanka* **34**(3), …

This is one consistent system applied consistently, so it satisfies the *letter* of §3.1 — the
guide permits author-year and does not mandate one house variant. It does not match the specimen.
**Closest available CSL is `harvard-cite-them-right`**, which gives initials and a parenthesised
year and differs from the specimen only in punctuation. Recommend downloading that CSL and
passing `--csl`; do not hand-roll one.

### 🟡 G7. Chapter headings are not in the specimen form

Required: `CHAPTER 3` centred, uppercase, bold, 14 pt, then the title on its own line in the same
form, then two blank lines. Current: a single left-aligned `Heading 1` reading
`Chapter 3. What is already known about Kandy's air`.

⚠ This interacts with the figure plan's chapter titles. **Do the titles first and the heading
form second**, or the same lines get edited twice.

### 🟡 G8. Caption and table font size — A CONFLICT NEEDING A RULING

The guide says figure captions and table titles are **size 10**. The project's standing
instruction, recorded in `make_reference_docx.py`, is a **12 pt minimum applied to captions and
table text as well**, deliberately and knowing it lengthens the document.

**These cannot both hold.** The two rules were set by different authorities for different
documents — the 12 pt floor was a user instruction for the summary, extended to the thesis by
analogy.

🟢 **RULED 2026-09-09: follow the guide.** Captions and table text drop to **10 pt**; the body
stays at 12. The 12 pt floor remains in force for the two-page summary, which is a different
document under a different constraint. ⚠ **`make_reference_docx.py`'s docstring says the 12 pt
minimum "is what was asked for" — that comment must be corrected in the same edit**, or the next
reader will restore the old value believing it was an instruction still standing.

### 🟡 G9. The chapter structure matches neither template

Guide §1.6 offers exactly two patterns: **chapter per subproject**, each carrying its own
Introduction, Methodology, Results and Discussion and Conclusions; or the **classic IMRaD spine**
of Introduction, Methodology, Results and Discussion, Conclusions.

The thesis is a **thematic monograph**: failures, model, validation, limits, recommendations.
This is a legitimate and common third pattern and it is a better fit for this work than either
template — the thesis's contribution is a measurement framework, and an IMRaD spine would split
the framework across a methodology chapter and a results chapter and destroy it.

🟢 **RULED 2026-09-09: do not restructure.** Instead, make the mapping explicit and defensible:

- §1.5 *Structure of the thesis* should say plainly which chapter discharges which of the
  guide's roles: **Chapters 1–4 are the introduction and literature**, **Chapter 6 is the
  methodology**, **Chapters 7 and 8 are results and discussion**, **Chapter 9 is conclusions and
  recommendations**, **Chapter 5 is a negative-results chapter with no template equivalent**.
- ⚠ **This is the one item on the list that requires the supervisor's agreement rather than a
  decision here.** A deviation cleared in advance is a design choice; the same deviation
  discovered at submission is a defect.

### 🟡 G12. Equations are set as code, not as equations, and none is numbered

The guide's §2.1.1 requires that formulae be printed with space around them, that subscripts and
superscripts be clear, that **the meaning of every symbol be given immediately after its first
use**, and that **equations be numbered serially at the right-hand side in parentheses**.

Measured against that:

- **There is no mathematics in the thesis at all in the typographic sense** — zero `$…$` spans
  across all twelve chapter files. The central decomposition in §6.1 is a **fenced code block**,
  rendered in Consolas 10 pt, and every symbol in the prose is inline code: `` `T(t)` ``,
  `` `B(t)` ``, `` `P(x, y, t)` ``.
- **No equation carries a number**, so no equation can be referred to by one.
- 🟢 The symbols *are* defined at first use, in the sentence immediately before the block, and
  again in the front matter's Symbols table. That half of the rule is already satisfied.

**No library is needed to fix this**, which was checked rather than assumed:
`build_docx.py` already passes `--from markdown+…+tex_math_dollars`, and a test conversion
through the project's own `reference.docx` produced **four native `m:oMath` elements** — Word
treats them as real equations, editable in its equation editor. The change is to the source
markdown, not to the toolchain.

🟢 **RULED 2026-09-09: set the displayed equations properly and number them; leave the running
prose in backticks alone.** Display mathematics is where the guide's rule actually bites, and the
humanisation pass deliberately moved this document away from notation in running text —
converting every `` `T(t)` `` to `$T(t)$` would partly undo it.

Candidates for numbered display equations, from a first pass: the decomposition in §6.1, the
identifiability counterexample `P' = (C − B') / (T − B')` in the same section, the observation
operator in §6.2, and the two correction terms in §6.5.

**Libraries installed for this work** (2026-09-09), none of them required by the document build:

| | version | for |
|---|---|---|
| `sympy` | 1.14.0, already present | deriving and checking algebra, emitting LaTeX from expressions |
| `pylatexenc` | 2.11, **installed** | LaTeX to unicode, so the linter can read a math span without the cp1252 crash that has bitten it before |
| `latex2mathml` | **installed** | LaTeX to MathML, if any equation ever has to reach HTML |
| MiKTeX | already on PATH | already used by the summary PDF build |
| matplotlib mathtext | built in, `fontset: stix` | math inside figures already matches Times |

### ⚪ G10. Units are written out in words

The guide's §2.2 assumes symbol form and prefers negative exponents: `µg m⁻³`, not `µg/m³`. The
thesis writes **"micrograms per cubic metre"** in prose and carries **no symbol form at all** —
eight occurrences, all spelled out.

Prose spelling is not a violation of a rule about symbols, and it was almost certainly a
deliberate choice in the humanisation pass. **No action proposed.** Recorded so that a reader of
this plan does not later mistake it for an oversight.

### ⚪ G11. Details to confirm with the department, not to guess at

- **Whether the title page carries a visible roman numeral.** The guide numbers prefatory pages
  from the title page and does not exempt it; conventional practice suppresses the number on the
  title page itself. Both readings are defensible.
- **Number of copies and binding colour.** The guide's table is postgraduate-specific
  (maroon for M.Sc.) and cannot be extrapolated to a B.Sc.
- **Whether a page or word limit applies.** None is published anywhere found. At 42,637 words
  the thesis is master's-scale, which is worth raising *before* rather than after.

---

## 4. What the figure plan already fixes

The guide's §2.5.2 requires that **maps carry coordinates, a linear scale, a directive arrow and
an index map**. Measured against that rule:

| figure | state | after the figure plan |
|---|---|---|
| `obsdensity`, Ch 1 | bare `scatter(lon, lat)` — no scale, no arrow, no index map | M1 adds projection, graticule, coastline and a Sri Lanka locator inset |
| `panel`, Ch 4 | same | M2, as a pair with M1 |
| `valley`, Ch 2 | hillshade, no scale bar, no north arrow, no inset | M3 adds all three plus contours |

🟢 **This means the figure and map plan is not only a quality improvement — it is the compliance
fix for §2.5.2.** As they stand, all three would fail the rule. That raises its priority.

⚠ **The two plans interact at three points**, and the order matters:
1. **G4 margins before any figure work** — a 10 mm wider text block changes every figure's
   rendered width.
2. **Figure-plan chapter titles before G7 heading form** — otherwise the same lines are edited
   twice.
3. **Figure-plan renumbering before G3's List of Appendices** — the list machinery is the same
   code path.

---

## 5. Where each fix lives

The project's own rule is that a correction belongs inside the script that owns the artefact.
Applying it:

| gap | owner | why |
|---|---|---|
| G1 abstract | `thesis/chapters/ch00_front.md` and `ch01_*.md` | content, hand-written |
| G2 page numbers | `build/make_reference_docx.py` (footer styles) **+ a new post-pandoc step** | the section break falls at a position only the assembled document knows |
| G3 order and lists | `ch00_front.md` (swap) + `build/assemble.py` (`{{listofappendices}}`) + post-pass (TOC position) | |
| G4 margins | `build/make_reference_docx.py`, then re-run it | |
| G5 spacing | `build/make_reference_docx.py` (`Bibliography` style) + a div or post-pass for the three front blocks | |
| G6 CSL | download `harvard-cite-them-right.csl`, pass `--csl` in `build/build_docx.py` | |
| G7 heading form | `build/assemble.py` (emit two lines) + `make_reference_docx.py` (centre, uppercase) | |
| G8 caption size | `build/make_reference_docx.py` — **after the ruling** | |
| G9 structure | `ch01_weather_and_air.md` §1.5 only — **after the supervisor agrees** | |
| G12 equations | `thesis/chapters/ch06_the_model.md` + `build/assemble.py` for numbering | the number, like a figure's, must be assigned at assembly so it cannot go stale |

🔴 **Nothing is fixed by editing `build/thesis.docx`.** Every such edit is destroyed by the next
build, silently, with no error. This is the project's gotcha #70 and it has already cost the
project a session once.

---

## 6. Order of execution

1. **Get the two rulings** — G8 caption size, and G9 from the supervisor. Neither blocks the rest.
2. **G4 margins.** One line, re-run `make_reference_docx.py`, rebuild. Do this first because it
   reflows everything.
3. **G5 spacing** and **G8 caption size** — same file, same re-run, so do them together with G4
   if the ruling has arrived.
4. **G6 CSL.** Download, pass the flag, rebuild, read ten references.
5. **G3 prefatory order and the List of Appendices.**
6. **G2 page numbers.** The largest engineering task and the one most likely to need a new script.
7. **G7 chapter heading form** — after the figure plan's chapter titles, not before.
8. **G12 display equations**, if the ruling is to set them. Content work, independent of
   everything above, and safe to do at any point.
9. **G1 the abstract.** Last, because it is a writing task and because the numbers it quotes may
   still move.

**The figure and map plan runs in parallel and is not blocked by any of this** except for G4,
which should land before its first figure is regenerated.

---

## 7. What the evidence says about how theses are judged

Format compliance is necessary and it is not sufficient. This section is drawn from the empirical
literature on **what examiners actually do**, rather than from generic writing advice, and it is
included because four of its findings change the priorities above.

### The findings that matter

**Examiners want to pass the thesis.** Across disciplines they are broadly consistent in
practice, expect to pass, and are unwilling to recommend a fail. The realistic risk is not
rejection; it is major revisions, and the revisions that count as major are *"a new study,
experimentation, or significant additional research or reformulation"*.

🔴 **But presentation quality is a pass/fail lever, not a cosmetic one.** McGill's guidelines put
it explicitly: stylistic and editorial changes are not normally major revisions, *but if the
quality of the presentation is so poor that extensive rewriting is required, the thesis should
not be passed*. Examiners report being easily irritated by typos and careless textual mistakes,
which they read as **lack of attention to detail** — and then generalise that judgement to the
research itself.

🔴 **The impression is formed by the end of the second or third chapter, usually at the end of
the literature review.** Mullins and Kiley's interviews with experienced examiners found that a
good literature review makes the examiner *"read the rest with much more of a sympathetic view"*,
and a poor one makes them read the rest critically; their stated reasoning is that *"it is
unusual that if someone does a poor job of the literature review that they will suddenly
improve"*. **The first three chapters are not preamble. They are where the verdict is set.**

**The common failure modes are alignment, criticality, methodological justification and
referencing.** Objectives that do not match the questions; a literature chapter that summarises
without evaluating, making the work read as a report rather than research; methods choices that
are made but not justified; and inconsistent or inaccurate references.

**Abstracts follow a fixed shape** — why the work was done, the gap, the aim, the method, the
findings, the conclusion — written in past tense for what was done and found, present tense for
established facts and for the contribution, third person, **and written last**.

### Four things this changes in the plan above

🔴 **1. The first three chapters deserve the human read first, not the last.** They are the
thinnest part of the document — Chapters 1 to 3 hold **5,010 words and 8 claim tokens** against
Chapter 7's 9,155 words and 212 — and they are precisely where the examiner's impression forms.
🟢 Checked rather than assumed: **§3.2 is genuinely critical, not descriptive.** It states the
gap as four things the existing record cannot supply and says why in each case, which is the
character examiners look for. The risk is not that Chapter 3 is uncritical; it is that at
**2,082 words it is the shortest substantive chapter in the thesis** and carries a
disproportionate share of the verdict.

🔴 **2. The abstract rewrite (G1) is a first-order task, not a formatting chore.** It is the
first thing read, it must carry the fixed six-part shape, and at 1,199 words it currently has no
shape at all. Its position in the execution order stays last only because the numbers must settle
first — **not** because it matters least.

🟡 **3. "Alignment" gives a concrete check the build cannot run.** The aim stated in §1.4 and the
scope in §1.6 must still match what Chapters 7 to 9 actually deliver, after four review rounds
moved several claims. **This is a paragraph-level read of §1.4 against §7.12 and §9.9**, and it
is exactly the kind of drift the claims gate cannot see, in the same class as F.108.

🟢 **4. The referencing gap (G6) is worth more than its severity mark suggests.** Inconsistent
referencing is named as a credibility failure in its own right. The fix is a one-line `--csl`
change, so it is the cheapest item on the list relative to what it protects.

⚠ **What this evidence does not license.** These findings come from PhD examination, mostly in
Australia, the UK and Canada. A Sri Lankan B.Sc. project is examined by a smaller panel against
a departmental standard, and the transfer is an inference. **The presentation and alignment
lessons transfer; the specific procedures do not.**

## 8. Risks

⚠ **The reference document is regenerated, not edited.** `make_reference_docx.py` says *run once,
re-run only if the typography changes*. The typography is about to change three times. Re-run it
once at the end of step 3, not once per change, and **confirm the file was rewritten** rather
than trusting the script's exit status.

⚠ **The claims gate protects values, not layout.** Every fix in this plan is invisible to the
six gates, the linter and the claims machinery. **The only check is opening the built document
and looking at it** — which is the same conclusion the project reached about the thesis's
numbers, restated for its formatting.

⚠ **Two Word sections will change how pandoc's table of contents renders**, because a TOC field
spanning a section break needs the field updated in Word. Expect to press F9, and expect the
first build after G2 to look wrong until it is refreshed.

⚠ **A departmental sheet, if it surfaces later, overrides this entire document.** The cost of
that is one re-run of steps 2 to 5 and a rewrite of the abstract to a different limit. That is
cheap, which is the argument for doing the work now rather than waiting for a sheet that may not
exist.

---

## 9. Sources

**The rules being followed:**
Postgraduate Institute of Science, University of Peradeniya, *Format of Project Report/Thesis:
M.Sc., M.Phil. and Ph.D. Degrees* (2018) — https://www.pgis.lk/downloads/staff/info_report_thesis_guide_2018.pdf
Faculty of Science, University of Peradeniya, *Student Handbook 2021/2022* (checked; carries no
thesis format section) — https://sci.pdn.ac.lk/docs/Student-Handbook-2021-2022_v1.1.pdf

**On how theses are judged (Section 7):**
Mullins, G. and Kiley, M. (2002). It's a PhD, not a Nobel Prize: how experienced examiners assess
research theses. *Studies in Higher Education* **27**(4), 369-386 —
https://documents.uow.edu.au/content/groups/public/@web/@raid/documents/doc/uow016364.pdf
Golding, C., Sharmini, S. and Lazarovitch, A. (2014). What examiners do: what thesis students
should know. *Assessment & Evaluation in Higher Education* — https://eric.ed.gov/?id=EJ1030245
Kiley, M. (2017). Advice for writing a thesis (based on what examiners do). *Open Review of
Educational Research* **4**(1) — https://www.tandfonline.com/doi/full/10.1080/23265507.2017.1300862
McGill University, *Thesis Guidelines* CGPS.12.02 — https://www.mcgill.ca/gps/files/gps/cgps.12.02.pdf

**On format choice and abstracts:**
Lund University AWELU, *PhD theses* — https://www.awelu.lu.se/genres/writing-in-academic-genres/phd-theses/
University of Freiburg, *Cumulative versus monographic dissertation* —
https://www.unr.uni-freiburg.de/dokumente/promotionen/Cumulative%20versus%20monographic%20Dissertation.pdf
Australian National University, *Writing an abstract* —
https://www.anu.edu.au/students/academic-skills/research-writing/journal-article-writing/writing-an-abstract
Monash University, *Methods thesis chapter* —
https://www.monash.edu/student-academic-success/excel-at-writing/how-to-write/thesis-chapter/methods-thesis-chapter

⚠ The Kiley (2017) article was cited from its abstract and search summary; **the full text
returned HTTP 403 and was not read**. Every claim attributed to it here is corroborated by one of
the other four sources.
