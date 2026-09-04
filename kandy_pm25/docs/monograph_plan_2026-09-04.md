# The Kandy air quality monograph: plan

**Purpose.** The thesis draft. A single document covering everything the project has done,
written as a continuous story rather than as a paper. Output is .docx, Times New Roman, 12 pt
minimum, plain formatting.

**Decisions taken 2026-09-04.**

| question | answer | consequence |
|---|---|---|
| length | ~30,000 words, ~100 pages | Chapter 5 becomes the spine of Part II at ~5,000 words |
| destination | **this IS the thesis draft** | third person, full citation apparatus, **no unlicensed images anywhere** |
| reader | intelligent reader outside the field | Chapter 1 explains why weather forecasting works before contrasting it |
| the learned pattern null | Chapter 5, as a completed failure | Chapter 9 carries only what it implies for the next step |

🔴 **The destination answer removes the web image option entirely.** Every figure must be built
from open data the project already holds, or be the author's own photograph. This turns out to
cost nothing, because all twelve new figures were already specified as builds from CSV or NPZ on
disk. The single exception was a valley photograph for Chapter 2, which now needs either an
own photograph or an open licensed satellite view with the licence recorded. See section 7.

**Status.** Plan only, 2026-09-04. Nothing written yet. Figure inventory below was verified
against disk on the same day, including file dates against the field rebuild of 2026-08-18 and
the coherence cap of 2026-08-10.

---

## 1. What already exists that this can be built from

Checked on disk, not recalled.

| asset | size | state |
|---|---|---|
| `docs/model_reference/` (21 parts) + `MODEL_REFERENCE_COMBINED.md` | 45,118 words | technical reference, thesis grade, current |
| `F_epistemic_ledger.md` | 98 entries | every finding with its date and its refutation status |
| `docs/paper/` manuscript | 13,799 words, 18 figures, 62 refs | the methods paper, gated, current |
| `claims.json` | 224 claims, 183 used | every number generated from a scored file |
| `memory/SESLOG.md` | 4,754 lines | the narrative record, dated |
| figure archives | ~120 png across 12 directories | mixed currency, audited below |

The monograph is therefore mostly an act of **selection, sequencing and rewriting**, not of new
analysis. The one genuinely new writing task is Chapters 1, 2 and 5, which have no existing text.

---

## 2. Chapter structure, mapped to the six scope points

Target lengths are proposals. Total around 30,000 words, roughly 90 to 110 pages at 12 pt with
figures. See the open questions in section 6.

### Part I. The problem

**Chapter 1. Why we know the weather and not the air.** (scope 1) ~2,500 words
The asymmetry stated concretely. Weather forecasting works because the observing network is
dense and global, the governing physics is closed and well posed, and sixty years of data
assimilation has been poured into it. Air quality fails all three conditions at once: the
observation network is sparse and unevenly distributed, emissions are a boundary condition
nobody measures directly, and the chemistry is neither closed nor cheap. The chapter ends on the
consequence, which is that an air quality field for most of the world is a model output nobody
can check.

**Chapter 2. Why not Kandy, and what is at stake.** (scope 2) ~3,000 words
The monitoring deficit is worst exactly where concentrations are highest. Kandy is a specific
instance: a steep valley with 850 m of relief across 15 km, closed to the south by the Hantana
range, venting north west along the Mahaweli corridor, with two low cost sensors and no
operating reference monitor. The valley physics section explains why terrain makes this harder
rather than merely different. The stakes section covers the health burden and, more usefully,
the decision problem: a ministry does not need to know which model is most accurate, it needs to
know what to buy first.

**Chapter 3. What is already known about Kandy's air.** (scope 3) ~3,500 words
A chronological account of the measurement record, with what each study could and could not
establish. Roughly: Abeyratne and Ileperuma 2006 on gases by monsoon, Elangasinghe and
Shanthini 2008 on the roadside transect, Premasiri 2010 on fixed sites, Wickramasinghe 2011 on
area representative sampling, Seneviratne 2017 on source apportionment, Senarathna 2024 on the
single speciated year, Priyankara 2021 on respiratory outcomes, Dhammapala 2022 on the BAM
anchored record, Attanayake 2025 and Nirmani 2025 on recent machine learning and NBRO data. Then
the gap, stated as a list of things none of them could do. Then what modern computing actually
offers, distinguishing honestly between what machine learning adds and what it does not.

### Part II. The work

**Chapter 4. What there was to work with.** (scope 4a) ~3,000 words
Data inventory with provenance and limits: satellite products, reanalysis drivers, static
geography, the two FECT sensors, the borrowed multi city panel, and what was requested and never
arrived. This chapter carries the acquisition history honestly, including the CEA correspondence
and the defunct Torrington Park monitor.

**Chapter 5. What was tried and did not work.** (scope 4b) ~5,000 words
The longest chapter and the most valuable one in the thesis. The project has
an unusually complete record of documented failure and it should be the spine of the middle of
the book rather than an appendix. Sections:

1. The cross continental physics informed neural network, and why transfer of a fitted physics
   is not transfer of physics.
2. The rigid terrain ansatz, and what parameter bound saturation actually tells you.
3. The cross city ConvCNP: it produced fields, they were defensible, and they were spatially
   smoothed out.
4. Sim2Real: fine tuning on two sensors gave r = 0.9999 at those sensors and inflated the grid
   annual mean from 22.1 to 37.0. The model had learned coordinates as identity keys.
5. The five spatial nulls, and the later discovery that none of them had a stated detection
   limit.
6. The background rebuilds: five attempts, all rejected, and the over determination argument
   that ended them.
7. The defects found by audit rather than by review, and the checks now in code because of them.
8. **The learned spatial pattern, pre-registered and refuted.** Placed last because it is the
   only one of the eight that was done properly: a benchmark, a detection limit and a registered
   bar, all fixed before the model was written. It reached 0.286 against a bar of 0.44 and is
   reported as undetectable at that power rather than as a modest success.

Each section follows the same shape: what was expected, what happened, what it cost, what it
established. The chapter closes on the contrast the ordering is designed to make. Seven of these
failures were informative in proportion to how clearly the expectation had been stated in
advance, and the five spatial nulls in section 5 were the least informative of all because none
of them stated one. The eighth was registered, and it is the only one that produced a bounded
claim rather than an absence.

**Chapter 6. The model.** (scope 5a) ~4,000 words
Formulation, gauge, observation operator, information budget, the correction terms, and the
partition. Drawn from the manuscript's section 2 and the model reference parts 4 and 5, rewritten
for continuous reading rather than for a referee.

**Chapter 7. Making sure it works.** (scope 5b) ~4,000 words
Budget matched validation across 48 cities, the value of information ladder, the confounds the
registered gates caught, the external checks at Kandy, and the interval calibration. This is
where pre-registration gets explained as a working practice rather than as a formality.

**Chapter 8. Where the model stops.** (scope 5c) ~3,000 words
The paired site test, the change of support argument, the sub grid result, and the six spatial
nulls including the pre-registered one. The chapter argues that a stated limit is a product
feature and not an apology.

### Part III. Forward

**Chapter 9. What to build next.** (scope 6) ~2,500 words
Ranked by measured value rather than by appeal: the acquisition ordering that inverts for Kandy,
the forecast tier, the sector and industry work, the learned pattern result and what would make
it worth revisiting, and the two questions that a single local instrument would settle.

### Thesis apparatus, required because this is the submitted draft

Front matter: title page, declaration of originality, abstract (300 words), acknowledgements,
table of contents, list of figures, list of tables, list of abbreviations and symbols.
Back matter: references in a single consistent style, then the appendices.

**Format: standard practice, fixed now so nothing is blocked.** If the department later issues a
template, only the reference.docx changes and no text has to move.

| element | setting |
|---|---|
| page | A4, 2.5 cm margins, 3.5 cm left for binding |
| body | Times New Roman 12 pt, 1.5 line spacing, justified |
| headings | Times New Roman bold; 14 pt chapter, 13 pt section, 12 pt subsection |
| captions | Times New Roman 12 pt, above tables and below figures, per convention |
| numbering | by chapter: Figure 3.2, Table 5.1 |
| pagination | roman numerals for front matter, arabic from Chapter 1 |
| references | author-year, single consistent style, generated from `references.bib` |
| declaration | standard originality wording, signed page |

**Appendices.** ~1,500 words plus tables
A: symbols and constants. B: the epistemic ledger, abridged to the entries the text cites.
C: reproduction instructions. D: the pre-registrations, listed with their outcomes.

---

## 3. Figure plan

Numbering is per chapter. Status audited against disk on 2026-09-04.

⚠ **The staleness rule for this document.** The field was rebuilt on 2026-08-18 and the coherence
cap was imposed on 2026-08-10. Any figure drawing the Kandy field and dated before 2026-08-18 is
stale and must be regenerated. Figures documenting **abandoned** approaches are exempt, because
they are historical records of what that approach produced and not claims about the current
field. That exemption is stated in each caption.

### Chapter 1

| fig | content | source | status |
|---|---|---|---|
| 1.1 | Global observing density, weather against air quality | **NEW.** Build from `global_locations.csv` (20,179 PM2.5 sites, already pulled) against a WMO synoptic station count | to build |
| 1.2 | Why the three conditions differ: a comparison panel, not a data figure | **NEW**, schematic | to build |

### Chapter 2

| fig | content | source | status |
|---|---|---|---|
| 2.1 | Kandy study area, terrain, drainage, settlement | `paper2026/F1_study_area.png` | 🟢 current (contains no model output, cannot go stale) |
| 2.2 | Reference monitoring by latitude band | **NEW** from `global_reference_census.csv` (6 deep tropical against 65 temperate) | to build |
| 2.3 | Valley cross section, floor to ridge | **NEW** from the DEM | to build |
| 2.4 | Exposure and attributable burden | `paper2026/F_burden.png` | 🟢 regenerated 2026-09-04 |

### Chapter 3

| fig | content | source | status |
|---|---|---|---|
| 3.1 | Timeline of Kandy air quality measurement, what each study resolved | **NEW**, from the literature already read | to build |
| 3.2 | The roadside transect, 110 to 4 µg/m³ over 300 m | **NEW** from `elangasinghe_spatial_test.csv` | to build |
| 3.3 | Four independent point records against the model | **NEW** from `nbro_pixel_check.csv` plus the literature table | to build |

### Chapter 4

| fig | content | source | status |
|---|---|---|---|
| 4.1 | Data streams: resolution, coverage, provenance | **NEW**, schematic with real coverage numbers | to build |
| 4.2 | The information budget and its tiers | `paper2026/F8_schematic.png` panel b | 🟢 current |
| 4.3 | The 48 city panel, where it is and what it is made of | **NEW** from `ladder_revalidated.csv` plus `validation_frame.csv` | to build |

### Chapter 5

| fig | content | source | status |
|---|---|---|---|
| 5.1 | ConvCNP zero shot Kandy field, as produced in May | `kandy_zero_shot/annual_mean.png`, `diurnal_cycle.png` | 🟡 dated 2026-05-23, **exempt**, historical record |
| 5.2 | Sim2Real memorisation: r = 0.9999 at the sensors, grid mean 22.1 to 37.0 | `kandy_sim2real/annual_mean.png` plus `summary.csv` | 🟡 exempt, historical |
| 5.3 | Parameter bound saturation and the identifiability limit | `paper2026/F3_information_bound.png` | 🟢 regenerated 2026-09-03 |
| 5.4 | The five spatial nulls and what each could have detected | **NEW**, combines `F12_null_power` with the four earlier nulls | to build |
| 5.5 | The dispersion step costs rank | **NEW** from `r2_atransport.csv` and `phase0_sector_surface.csv` | to build |
| 5.6 | Five background rebuilds, and the constraint that ended them | **NEW** from `kandy_field_diagnostics.csv` | to build |

### Chapters 6 to 8

Mostly the manuscript's existing suite, all regenerated 2026-09-03 or later.

| fig | content | source | status |
|---|---|---|---|
| 6.1 | The formulation: decomposition, budget, observation operator | `F8_schematic.png` | 🟢 |
| 6.2 | The delivered field and its components | `F_field.png` | 🟢 2026-09-04 |
| 6.3 | Emission surface construction | `paper_figures_v2/F5_emission.png` | 🟢 regenerated 2026-09-03 |
| 6.4 | Mechanism: confinement and ventilation | `paper_figures_v2/F4_mechanism.png` | 🔴 **STALE**, 2026-07-16, regenerate |
| 7.1 | Budget matched validation protocol | `F7_protocol.png` | 🟢 |
| 7.2 | The value of information ladder | `F2_ladder.png` | 🟢 |
| 7.3 | Estimator dependence and stream provenance | `F3_streams.png` | 🟢 |
| 7.4 | The confound that cannot be sampled away | `F4_confounds.png` | 🟢 |
| 7.5 | Ten city scorecard | `F7_scorecard.png` | 🟢 |
| 7.6 | Kathmandu, the showcase transfer | `F8_kathmandu.png` | 🟢 2026-09-04 |
| 7.7 | Seasonal and diurnal cycles against the sensors | `F_cycles.png` | 🟢 2026-09-04 |
| 7.8 | Interval calibration: width right, centring wrong | `F11_uncertainty.png` | 🟢 |
| 7.9 | Chemical check on the decomposition premise | `F6_chemistry.png` | 🟢 |
| 8.1 | The paired site test | `F1_paired.png` | 🟢 |
| 8.2 | Within pixel against between pixel spread | `F5_withinpixel.png` | 🟢 |
| 8.3 | Contrast against averaging support | `paper_figures_v2/F9_scales.png` | 🟢 regenerated 2026-09-03 |
| 8.4 | Detection limits of the spatial nulls | `F12_null_power.png` | 🟢 |
| 8.5 | The field across seasons and hours | `F_spatiotemporal.png` | 🟢 2026-09-04 |
| 8.6 | A stagnation episode | `F_episode.png` | 🟢 2026-09-04 |

### Chapter 9

| fig | content | source | status |
|---|---|---|---|
| 9.1 | Acquisition ordering, pooled against Kandy's own band | **NEW** from `claims.json` (F.92, F.96) | to build |
| 9.2 | The learned pattern result against its registered bar | **NEW** from `phase1_predictor_ranking.csv`, `phase2_learned_pattern.csv` | to build |
| 9.3 | Predictor skill against buffer radius | **NEW** from `phase1_predictor_ranking.csv` | to build |

### Tables

Under-planned in the first draft of this plan. A thesis of this kind carries its evidence in
tables as much as in figures, and most of these already exist as data.

| tbl | content | source | status |
|---|---|---|---|
| 1.1 | Weather against air quality on the three conditions: observation, closure, assimilation | prose, structured | to write |
| 2.1 | Kandy at a glance: population, elevation, relief, monitoring, climate regime | `claims.json` + census | to build |
| 2.2 | What each acquisition route would cost and what it would settle | `claims.json` (F.92, F.96) | to build |
| 3.1 | Every Kandy air quality study: year, method, sites, duration, finding, limit | literature, already read | **to write, the most valuable table in Part I** |
| 3.2 | The four independent Kandy point records against the model | `nbro_pixel_check.csv` + literature | to build |
| 4.1 | Data inventory: stream, product, resolution, coverage, provenance, admissible tier | disk audit | to build |
| 4.2 | The information budget: what each tier admits and the first quantity it constrains | `src/modular/budgets.py` | exists in manuscript |
| 4.3 | The 48 city panel: city, country, band, stations, days, instrument class | `ladder_revalidated.csv` | to build |
| 5.1 | **Every method tried: expectation, outcome, cost, what it established** | ledger F.1 to F.98 | **to build, the spine table of Chapter 5** |
| 5.2 | The five spatial nulls and the detection limit each actually had | `F12_null_power` + ledger | to build |
| 5.3 | Five background rebuilds and why each was rejected | ledger F.13 to F.19 | to build |
| 6.1 | Symbols, units and constants used in the formulation | `model_reference/A_symbols.md`, `B_constants.md` | exists |
| 7.1 | The value of information ladder, pooled | `claims.json` | exists in manuscript |
| 7.2 | The ladder stratified by latitude band, with n | `claims.json` | exists |
| 7.3 | Estimator sensitivity: four learners on the same rung | `learner_sensitivity_bud0c.csv` | exists |
| 7.4 | Ten city validation scorecard | `validation_scorecard.csv` | exists |
| 7.5 | Registered predictions across all five pre-registrations, and their outcomes | the prereg documents | **to build, and it is the thesis's strongest single table** |
| 8.1 | Contrast against averaging support and against siting design | `support_collapse.csv` | exists |
| 8.2 | What the model may and may not be asked | prose, structured | to write |
| 9.1 | Next steps ranked by measured value, not by appeal | `claims.json` | to build |
| A.1 | Abbreviations and acronyms | to compile | to build |

**21 tables.** 6 exist, 15 to build or write, all from material on disk.

### Diagrams and flowcharts

Also under-planned. These carry the process argument, which is a large part of what this thesis
is actually about. **Drawn with dedicated diagramming libraries**, not hand placed in matplotlib. Tooling is
installed and proven, see section 4b.

| dia | content | why it earns its place |
|---|---|---|
| D1 | The full pipeline: drivers and satellite in, anchor and background and pattern, field out | Ch 4. The reader cannot follow Chapters 6 to 8 without it |
| D2 | The decomposition as a picture: uniform background plus redistributed increment | Ch 6. One diagram replaces two pages of equations |
| D3 | Budget tier nesting and exact degradation between tiers | Ch 6. The paper's central mechanism |
| D4 | The observation operator: areal field against point sensor | Ch 6. Change of support, the single most common scoring error |
| D5 | Budget matched validation: what is withheld, what is scored | Ch 7. The protocol that makes the ladder mean anything |
| D6 | The pre-registration workflow, from prediction to refutation | Ch 7. This is a method, and it should be drawn as one |
| D7 | The claims gate: from scored file to number in the text, and where it fails the build | Ch 10 or Ch 7 |
| D8 | Failure taxonomy: the eight failures classified by what made them informative | **Ch 5, and it is the chapter's argument in one image** |
| D9 | Acquisition decision tree: what to buy first, with the tropical branch inverting | Ch 9. The practical output of the whole thesis |
| D10 | Regeneration chain: which script owns which artefact | Ch 10 or appendix. Prevents the stale artefact class of error |
| D11 | Kandy valley schematic: terrain, ventilation corridor, sensor positions, drainage | Ch 2. Orientation before any result |
| D12 | Timeline: what was tried when, and what each attempt closed | Ch 5 opener |

**12 diagrams, all new.**

### Totals

**34 figures.** 19 exist and are current, 1 is stale and needs regenerating (6.4), 2 are exempt
historical records, and **12 are new**. Every new figure draws on a CSV or NPZ already on disk,
so none requires new modelling.

**Whole document: 34 figures, 21 tables, 12 diagrams = 67 visual elements** across roughly 100
pages, or one every 1.5 pages. That is dense, and appropriate: this is a thesis whose argument
is carried by measured quantities and by process, and both are better shown than described.

**Build load: 12 figures, 15 tables, 12 diagrams = 39 new artefacts.** None requires new
modelling. The diagrams are the largest single block of work because they have no data source to
generate from, only a design.

### On web images: ruled out

The document is the thesis draft, so an image whose licence cannot be demonstrated is a liability
rather than a convenience. Every figure in the list above is built from data the project holds.
The three candidates that would have been web images are replaced:

| wanted | replaced by |
|---|---|
| synoptic station density map | figure 1.1, built from the OpenAQ census plus a published WMO station count, cited |
| WHO or IHME burden graphic | figure 2.4, the project's own exposure and burden calculation |
| satellite view of the Kandy valley | figure 2.3, a DEM derived cross section and hillshade, which is more informative anyway |

⚠ If a photograph of the valley is wanted for Chapter 2, the options are the author's own
photograph, or an image with a recorded CC licence. Nothing else.

---

## 4b. Diagram toolchain, installed and proven 2026-09-04

Everything lives in `D:\ProjectCD\#writing`.

```
#writing/src/thesisviz.py       house style: palette, fonts, save helpers, both backends
#writing/src/d*.py              one script per diagram
#writing/thesis/diagrams/       output, gitignored, regenerated from src
#writing/thesis/figures/        output
#writing/thesis/chapters/       ch01..ch10.md
#writing/build/                 reference.docx, assemble.py, build_docx.py, lint.py
```

**Two libraries, chosen by what the picture is.**

| library | version | used for |
|---|---|---|
| **graphviz** (+ Graphviz 16.0.0 binary) | 0.21 | anything that branches or rejoins. Automatic layout solves collisions that hand placement cannot: the pipeline, the validation protocol, tier nesting, the decision tree, the regeneration chain |
| **schemdraw** | 0.23 | linear or spatially meaningful diagrams where node position itself carries information |

Both were installed and a full diagram (D5, the validation protocol) was built end to end to
prove the chain before committing to twelve. **Three things that proof established:**

🔴 **Graphviz silently loses Times New Roman.** It renders through Pango, which parses a trailing
"Roman" as a *style* keyword and drops it, falling back to Sans without failing. `"Times-Roman"`
and `"Times New Roman,"` (trailing comma) both load correctly; the obvious spelling does not.
Fixed in `thesisviz.GV_FONT` with the reason recorded, because the failure is silent and would
otherwise reappear in whichever diagram was written next.

🔴 **A diagram of more than about six ranks will not sit on a page.** D5's first draft had nine
boxes for a four step procedure. Top to bottom it came out at aspect 0.46, a full page tall and
half a page wide; left to right at 7.76, a strip. **The fix was not a layout parameter, it was
deleting five boxes.** The rule for the remaining eleven: if it does not fit, remove content
before touching `ranksep`. The final D5 is aspect 1.30 with four ranks.

⚠ **Captions belong in the graph label, not in a node.** A caption node needs an invisible edge
to position it, which adds a rank and stretches the drawing. `thesisviz.gv_note()` handles it.

**Palette**, in `thesisviz.C`: blue for information that is free everywhere, red for information
that must be bought locally, light red for regional, green for held, magenta for refuted. Every
pair is separable in greyscale by lightness, because a thesis is printed as often as it is read.

## 4. Production pipeline

```
scripts/build_claims.py                 regenerate every number
scripts/monograph_figures*.py           the 12 new figures  (to write)
docs/monograph/ch01..ch09.md            one file per chapter, edited by hand
docs/monograph/assemble.py              concatenate, resolve {{claim:}} and {{fig:}}
docs/monograph/build_docx.py            pandoc with a reference.docx
```

**Typography.** Pandoc's default .docx is Calibri 11 pt. Times New Roman 12 pt requires a
`reference.docx` with the Normal, Heading and Caption styles set. Two routes:

1. `pandoc --print-default-data-file reference.docx > reference.docx`, then patch
   `word/styles.xml` to set `w:ascii="Times New Roman"` and `w:sz="24"` (half points).
2. Build the reference document with `python-docx` and set the styles programmatically.

Route 1 is fewer moving parts and is the recommendation. ⚠ Minimum 12 pt means captions and
table text must also be 12 pt, which is larger than typographic convention and will lengthen the
document. Worth confirming, see question 4.

**Claim tokens.** Strong recommendation to reuse the manuscript's `{{claim:tag}}` mechanism, so
the monograph cannot drift from the data the way the manuscript did before the gate existed. The
alternative is to hardcode, which for a 30,000 word document guarantees the same class of error
the project has already found nine times.

**Style rules, enforced by a lint script:**
- No em dashes anywhere. Use a comma, a colon, or a full stop.
- No "delve", "leverage" as a verb, "it is worth noting", "in the realm of", "tapestry",
  "testament to", "navigate the complexities".
- No sentence beginning "Importantly," or "Notably,".
- No three item lists used decoratively.
- **Third person throughout.** No "I" or "we found". The thesis convention, and it also removes
  the temptation to narrate the process rather than report the result. ⚠ Chapter 5 is the hard
  case: describing a failure in the third person can read as evasive. The rule there is to name
  the decision and its consequence plainly, without a grammatical subject to hide behind.
- Contractions avoided, but formality not forced.
- Numbers in prose come from claim tokens, never typed.

---

## 5. Sequencing

Ordered so that nothing is written into a format that later has to change, and so the largest
uncertainty is retired first.

| stage | work | output | why here |
|---|---|---|---|
| A | reference.docx, assemble/build chain, style lint | a chain that demonstrably emits 12 pt Times with no em dashes | writing 30,000 words before this exists is the expensive mistake |
| B | **the 12 diagrams** | `results/figures/monograph/D*.png` | largest unknown, no data source, pure design. Doing them first means Chapters 4 to 9 can be written against a picture that already exists |
| C | the 12 new figures | `results/figures/monograph/F*.png` | all from CSV or NPZ on disk |
| D | the 15 new tables | generated into markdown by script, not typed | same claims gate as the prose |
| E | regenerate figure 6.4 | current mechanism panel | one script run |
| F | Chapters 4, 6, 7, 8 by adaptation | ~14,000 words | selection and rewriting, not composition |
| G | Chapters 1, 2, 3, 5, 9 written fresh | ~16,000 words | the real writing. Chapter 5 is the largest single piece |
| H | front and back matter, full read, lint, claim gate, build | the .docx | |

Stages B, C and D are mechanical and can be done in long uninterrupted runs. Stage G is the work.

⚠ **One sequencing risk worth naming.** Chapter 5 depends on the ledger being accurate about
what was expected before each attempt, and the earliest entries predate the pre-registration
habit. Where an expectation was not recorded in advance, the chapter must say so rather than
reconstruct one. That is the difference between a chapter about learning and a chapter about
looking clever in hindsight.

## 6. Open questions

1. **Is a photograph of the valley wanted for Chapter 2?** If so it must be the author's own or
   carry a recorded licence. Figure 2.3, the DEM cross section, covers the scientific need
   without one.
2. **Should there be a Chapter 10 on software and reproducibility?** The material exists
   (`model_reference` parts 7b and 10) and examiners often expect it. Around 2,000 words, or it
   can stay an extended appendix. Recommendation: make it Chapter 10, because the claims gate
   and the pre-registration machinery are among the more defensible things the project built.

---

## 7. What is settled

- Length ~30,000 words, ~100 pages.
- This is the thesis draft: third person, full citation apparatus, no unlicensed images.
- Written for an intelligent reader outside the field.
- The learned pattern null sits in Chapter 5 section 8, not in Chapter 9.
- 34 figures: 19 current, 1 to regenerate, 2 exempt historical, 12 to build from data on disk.
- Every number comes from a claim token, gated the way the manuscript is.
- No em dashes, and a lint script that enforces it along with the other style rules.
