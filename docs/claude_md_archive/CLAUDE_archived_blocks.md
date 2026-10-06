# CLAUDE.md archive — append-only

Blocks moved out of `CLAUDE.md` when their conclusions were absorbed into
`CONTEXT.md`, the gotchas, `PROJECT.md` or the ledger. Never edit; only append.


# Archived from CLAUDE.md on 2026-09-21
Source: CLAUDE.md sha256 dd18103b8077 (full copy: CLAUDE_2026-09-21_pre-trim.md). Verbatim; line numbers are those of that copy.

<!-- CLAUDE.md lines 201-236 -->
## Current State (updated 2026-09-14, 🗺️ **THE FIGURE PLAN EXECUTED · THE REGISTRATIONS TABLE READS THE REGISTRY**)

Thesis-only session while the spatial learning curve runs. **No computation, no new result.**
Commit `8ac0b56` (local, not pushed). Narrative: SESLOG 2026-09-14.

- 🔴 **T7_5 was wrong twice.** Its note said *"fourteen of thirty refuted"* where its own rows
  gave **11 of 30**, and it stopped at **6** registrations when `registrations.json` holds **11**.
  `t7_5_registrations()` now builds rows AND note from the registry and refuses on an unverified
  list, held+refuted≠predictions, or a `_totals` block that disagrees. **Quote: eleven
  registrations; 13 of 38 refuted over the seven that have run.** Spatial-curve rows (`rqn4y`,
  `26hp8`, `4whsc`) print **"not yet scored"**. Hand-typed counts in ch10 ("eight") and
  Appendix B ("six") removed — the generated note is the only place a count appears.
- 🔴 **Four visuals were printed twice under one number**: T7_5 (ch10 + App. B), `panel`,
  `pipeline`, `dispersion`. Later copies are now inline references, and **`assemble.py` refuses a
  duplicate placement** (gotcha #94).
- 🟢 **All six plan figures built** (`f_chapters.py`), each asserting its recomputed summary
  against the stored JSON/claim: N4 `F6_partition` (§6.6) · N6 `F7_cluster_bootstrap` · N3
  `F7_losses` (§7.2.1) · N1 `F7_station_count` · N2 `F8_tournament` (§8.5) · N5 `F9_paired_trap`
  (§9.7). Each has a lead-in.
- 🟢 **The maps are maps.** M1/M2 Robinson + Natural Earth (M2 labels deep-tropical members by
  country); M3 `D11_valley` in UTM 44N with 100 m contours, scale bar, north arrow, Mahaweli,
  sensors, locator. `thesisviz.natural_earth()` **raises instead of downloading**. Profile and relief
  label still read the 100 m grid behind the gated `kandy.relief_m`.
- **Chapter titles 3, 4, 5, 7, 9, 10 changed** (user approved). Ch1 kept: *"weather is forecast and
  air quality is not"* is false — air quality is forecast. ⚠ Ch5 is now *"Eight approaches that did
  not work"*; **Table 5.1 has eight rows and the title must change if a row is added.**
- ⚠ **ch06 said the production F_min sweep "left no artefact".** `decomp/kandy_fmin_sweep.csv`
  exists and reproduces 0.483; the quoted reimplementation reads ~0.006 higher (0.482–0.509 vs
  0.477–0.502). Sentence corrected; N4 plots both.
- ⚠ **`loss_sensitivity.json` `excludes_zero` is wrong-sided**: false for exceedance at
  [−32.1, −2.68]. Prose is right; the script's flag is not. Exceedance inversion is **n = 10**, not 13.
- ⚠ **The summary will print "eleven" and "thirteen of thirty-eight" on its next rebuild** — it reads
  the same JSON. Not rebuilt or touched this session.

**Thesis: 43,713 words · 41 figures · 10 tables · 566 claims · 0 lint errors.**


<!-- CLAUDE.md lines 295-1204 -->
## Current State (updated 2026-09-09d, ✍️ **THE THESIS AND SUMMARY REWRITTEN FOR A READER — AND THE VISUALS AUDITED**)

No computation this session. What changed is who the document is written for, and a plan exists
for the part of it that was never done properly: the figures. Narrative: SESLOG 2026-09-09d.

### ✍️ The prose was written for the person who built it, and now is not
The user's instruction was *"phrasing and wording to be humanized and understandable... much of it
sounds cryptic"*, applied first to the summary, then to the thesis. The pass was structural, not
cosmetic:
- 🔴 **"The ladder" is used 33 times and was never introduced.** The thesis's central metaphor had
  no definition anywhere. Same defect for `rung`, `tier`, `the panel`. All now glossed at first use.
- 🔴 **"Stratum" named two different objects in ch09** — a latitude band and a design group. Split.
- **49 section headings replaced.** 31 of 124 opened with What/Where/Why/How and 16 used the
  *"X, and what it does not"* construction — a quarter of all headings following one formula, which
  reads as a house style before it reads as description. ⚠ **Distinctive chapter titles were
  deliberately kept**; flattening every heading into a bureaucratic noun phrase is a different
  failure. Section *numbers* untouched, so every cross-reference still resolves.
- **11 figures gained lead-in paragraphs.** Six sat directly under a heading with no prose at all,
  so a reader met the image before being told what question it answers.
- ⚠ **The summary tension resolved in favour of comprehension** (user: *"I don't mind if the summary
  is recompressed but it should be comprehensible"*). Space came from layout and content, never from
  re-compressing the language.
- 🔴 **Process note, twice over:** I cut summary body text before noticing the extra page came from
  the **title block**, then again before noticing it came from the **final paragraph splitting
  across the break**. **Measure where the space went before cutting content.**

### 📋 A FIGURE AND MAP PLAN, written after checking rather than assuming
Plan: [`kandy_pm25/docs/figure_and_map_plan_2026-09-09.md`](kandy_pm25/docs/figure_and_map_plan_2026-09-09.md).
**Awaiting user approval before execution** — in particular the seven proposed chapter titles.
- 🔴 **The maps are not maps.** `obsdensity` (ch1) and `panel` (ch4) are `scatter(lon, lat)` on bare
  axes labelled "longitude" and "latitude" — **no coastline, no landmass, no projection, no
  graticule**. For the figure that opens the thesis and carries its motivating claim, that is the
  weakest visual decision in the document. `valley` (ch2) has a reasoned hand-computed hillshade but
  no scale bar, north arrow, contours or locator inset.
- 🟢 **The libraries are already installed** — geopandas 1.1.2, cartopy 0.25.0, contextily, rasterio,
  shapely, pyproj, osmnx, matplotlib-scalebar. 🟢 **Cartopy's Natural Earth cache is populated**
  (65 shapefiles); all five needed features were **tested loading from disk**, so the maps build
  offline with no tile service and no licensing question. **Missing: `mapclassify`, `adjustText`** —
  install rather than hand-roll.
- 🟢 **All six proposed new figures have their data on disk.** N1 station-count curve · N2
  model-family tournament · N3 loss sensitivity and the sign flip · N4 partition sensitivity across
  **three** axes (the F.108 error, made impossible to repeat) · N5 paired vs unpaired (gotcha #91,
  which has now caught this project four times) · N6 cluster-bootstrap forest plot.
  **This is a plotting job, not an analysis job.**
- 🟢 **Both stated risks were tested, not just listed:** no prose anywhere names a figure by number,
  so inserting six figures and renumbering is safe; and every cartopy feature loads from cache, so a
  build cannot silently attempt a download.
- **Deliberately NOT proposed:** figures for the precipitation null, the campaign costing or the
  chemistry bounds — all three are table-shaped and a figure would be decoration.

### 📄 A CV rebuilt from a veteran's skeleton
`D:\Downloads\Daminda_Alahakoon_CV_2026-09.{md,docx}`, for the user to finish by hand. Assessed the
**Makoto Kelp / University of Utah** PhD opening against the user's profile; advised emailing with
CV + summary attached rather than waiting on a partial transcript that costs money and days.
⚠ **Per [[phd-application-strategy]] the standing decision is Fall 2028**, so this is one posting
evaluated on its merits, not a reopening of the cycle.

**Thesis: 42,637 words · 35 figures · 10 tables · 566 claims · 0 lint errors, builds clean.**
Summary 2 pages.

## Current State (updated 2026-09-09c, 🟢 **NO F.84 REPEAT — THE UNUSED DRIVER WAS UNUSED HARMLESSLY**)

Two registered tests in one session, both nulls, both useful. Narrative: SESLOG 2026-09-09.
Ledger **F.111** (embeddings) and **F.112** (precipitation). Registrations **OSF
[`6udm3`](https://osf.io/6udm3/)** and **[`z89kt`](https://osf.io/z89kt/)**, both lodged before
their scripts were written. **Seven → nine OSF registrations.**

### 🟢 F.112 — the defect that was NOT there
`total_precipitation_sum` was **already in the scored frame** — pulled, merged, never referenced,
because it is absent from `FEATS`. So `Bud0a` held a driver its budget admits, in its own inputs,
unused. **That is the F.84 defect class**, which moved a headline from 25.6% to 17.9%.
⚠ `require_covers()` cannot catch it: it asserts coverage at **stream** level and cannot see an
unused variable **inside** an admitted stream.

Both arms on **one fixed city set**, identical seed and machinery, one feature apart:

| registered | result | verdict |
|---|---|---|
| **P1** bottom rung improves | **−0.129%** [−4.561, +5.780] | **REFUTED** |
| **P2** gains above shrink | paired **+0.000** [−4.88, +1.61] | **REFUTED** |
| **P3** redundancy null survives | 0.37 → 0.69, paired **+0.000** | HOLDS |
| **P4** background stays largest | 28.53 → 32.12 | HOLDS |
| **P5** deep-tropical does not reverse | +19.84 → **+9.20** pp, both exclude 0 | HOLDS in direction |

**No published number is overstated.** The variable was unused harmlessly. 🟢 **Table 9.1's
`NO MEASUREMENT` row for precipitation is now a REGISTERED NULL** — the gap is measured, not
unexamined. ⚠ **Not** evidence that wet removal does not matter: an 11 km reanalysis daily total
does not help *this* prediction at *this* resolution.
⚠ **P5's magnitude roughly HALVES** (+19.84 → +9.20). The deep-tropical margin has now proved
sensitive to the **satellite stream** (F.97), the **loss** (F.109) and the **driver set** (F.112) —
three demonstrations that it is the least robust quantity the Kandy recommendation rests on.

### 🔴 GOTCHA #91 A FOURTH TIME — and the most instructive instance yet
Unpaired, the first-rung gain reads **35.05% without precipitation against 27.42% with**, a
7.6-point drop that is exactly the shrinkage **P2 predicted**. Paired: **+0.000**. **The unpaired
comparison would have CONFIRMED a registered prediction that the paired one refutes.** Every prior
instance produced a *flattering* number; this produced a *confirming* one, which is harder to
resist. Registration is what made it visible.

### ⚠ Two caveats that must travel with F.112's numbers
The coverage gate keeps **37 of 48 cities** (35 scored), so the first rung reads **35.05%** here
against the published **17.9%** on 48 cities. **That gap is the city subset, not precipitation.**
The arms are comparable to each other and to nothing else.
⚠ **A hypothesis tested and refuted:** ERA5-Land has no data over water, so the excluded cities
were expected to be coastal. They are the opposite — **18% coastal against 51%**, median coast
distance **187 km against 46 km**. The gap is inland and its cause is unidentified.

**Thesis: 40,868 words · 35 figures · 10 tables · 566 claims · 0 lint errors.** Summary 2 pages.

## Current State (updated 2026-09-09b, 🔬 **A SEVENTH NULL, REGISTERED — EO FOUNDATION EMBEDDINGS DO NOT BREAK THE CEILING**)

The user asked whether the newest GEE geospatial model could help. It could, the question was
well posed, and it was registered and run. Narrative: SESLOG 2026-09-09. Ledger **F.111**.
Registration **OSF [`6udm3`](https://osf.io/6udm3/)**, project `ng2tc`, lodged **before** the
script was written. Prereg `docs/prereg_embedding_spatial_2026-09-09.md`.

### Why it was worth re-running something already tested
AlphaEarth was already one of the six spatial nulls (**F.27**, partial ρ +0.066, p = 0.80) — but
**F.28 had already retracted its force**: minimum detectable partial ρ **0.65 / 0.82 / 0.96** on
**17 / 10 / 6 stations**. It excluded only a large effect. **F.105**'s frame resolves **0.130** on
**47 cities / 636 stations**, and the embeddings had never been scored there. An external reviewer
named the same gap independently: the benchmark is *"the best predictor among the predictors you
happened to assemble, not a mathematical maximum."*

### 🟢 The result — all three confirmatory tests fail, as registered
64 dims, 10 m, 2023 mosaic, 100 m buffer, **100% coverage of 636 stations**, leave-one-CITY-out.

| test | paired | 95% over cities | wins |
|---|---:|---|---:|
| **E1** embeddings vs benchmark | **−0.028** | [−0.170, +0.084] | 21/47 |
| **E2** +embeddings vs 60 existing | **−0.002** | [−0.064, +0.049] | 23/47 |
| **E3** partial ρ, benchmark removed | **+0.191** | **[−0.007, +0.355]** | undetectable |

**The claim:** *on 47 cities and 636 stations, 64-dim EO foundation-model embeddings do not beat
the best single free raster by more than 0.130 in rank correlation.* **The previous embedding null
resolved 0.65; this one resolves 0.130** — a five-fold tightening. **Seventh null, second with a
detection limit fixed in advance.**

### 🔴 GOTCHA #91 FOR THE THIRD TIME — and it would have been the headline
Unpaired, embeddings post **the highest median of anything tested: 0.327 vs the benchmark's
0.301**, appearing to beat both the best free raster and the whole 60-predictor set. **Paired
within city: −0.028, winning 21/47.** Opposite signs. Reporting the medians would have produced
*"foundation-model embeddings break the spatial ceiling."* Third instance after F.102 (+12.91 vs
+0.14) and F.103 (+0.114 vs −0.044). **The misleading table is kept in §8.5 beside the paired
numbers, deliberately.**

### ⚠ E3 is marginal, not zero
**+0.191 with a lower bound of −0.007** — it misses excluding zero by seven thousandths, and is
**~3× F.27's +0.066** measured with far more power. Registered verdict *undetectable* stands, but
*"embeddings carry no independent signal"* overstates it. **This is where a follow-up goes**, and
the design is **more cities, not more bands**.
🟢 **The leakage audit was not required:** the registration made a PASS provisional on checking
AlphaEarth's training corpus for ground-monitor ingestion (the C1/F.95 lesson). Contamination could
only have *inflated* a score, so a failure needs no such check.

### 🟡 TWO GAPS THIS SURFACED, both admissible at `Bud0` and neither yet tested
- 🔴 **The driver set contains NO precipitation and NO humidity.** `FEATS` is temperature, u/v wind,
  wind speed, BLH and two day-of-year terms. **Wet removal is entirely absent**, and Table 9.1
  already lists it as `NO MEASUREMENT: a known structural gap`. ERA5-Land precipitation is global,
  free and already used at Kandy (⚠ de-accumulate, gotcha #60). This targets the **temporal** axis,
  where the model is strong and where the ladder's bottom rung sits.
- 🔴 **Every one of the 60 LUR predictors is a LAND-SURFACE proxy** — NDVI, tree, water, population,
  built-up, night lights, land cover, roads, distance-to-road. **There is no chemical tracer.** A
  satellite NO₂ column is a direct observation of co-emitted combustion rather than a land proxy,
  and the Quito study found NO₂ *far* more predictable from these same embeddings (R² ≈ 0.71) than
  PM2.5. ⚠ Resolution is the open question: TROPOMI is ~3.5×5.5 km against a 1 km target, so this
  may be coarser than the structure it would have to place.

**Thesis: 40,472 words · 35 figures · 10 tables · 548 claims · 0 lint errors.** Summary 2 pages.

## Current State (updated 2026-09-09, 🔬 **TWO MORE REVIEWERS · A STYLE CLAIM MEASURED · FIVE CLAIMS PROMOTED OR DEMOTED**)

Two further external assessments of the finished thesis, both **91–93/100**, both agreeing the
methodology is sound and the remaining work is claim calibration. **No computation overturned
anything.** What changed is what the document emphasises. Narrative: SESLOG 2026-09-09.
Ledger **F.110**.

### 🔴 A STYLE CLAIM THAT WAS CHECKABLE — and the specific charge was wrong
Reviewer 2 said *"X is not Y. It is Z"* recurred **"dozens of times almost verbatim"** and might
read as machine-written. **Counted: 8 times in 33,694 words.** But the *diagnosis* was right and
two other tics were genuinely uniform, at a near-constant rate in **every** chapter:

| tic | before | after |
|---|---:|---:|
| `rather than` | 189 (5.6 / 1000 words) | **147** |
| paragraph-opening **bold** | 178 of 535 paragraphs (**33%**) | **78 (15%)** |

Thinned with rotating alternatives so removing one tic did not install another. ⚠ **Three rewrites
broke the sense and were repaired by hand** — one inverted a comparative. **A mechanical style pass
needs a human read of every diff**: the guards stopped syntax errors, not meaning errors.

### 🟢 PROMOTED — the dispersion failure is a headline, not a caveat
Both reviewers, independently. The raw emission surface ranks neighbourhoods at **0.371**; the
terrain-steered dispersion solver **lowers** it to **0.274**, improving **3 of 10** cities. It was
honestly reported in §8.4 and §6.1 and mentioned in **neither the abstract nor Chapter 1**.
**The measurement framework works better than the spatial model it was built to evaluate.** Now in
both. 🟢 **The F.109 loss reversal also reaches the abstract** — a skimmer could previously have
missed that the Kandy recommendation inverts on episode and exceedance losses.

### 🔴 DEMOTED — the attributable-burden projection moved to **Appendix E**
Both reviewers. Labelling it *illustrative* was not enough: *"N deaths per year"* detaches from its
caveats on first quotation, and its interval carries only response-function uncertainty. §7.11
keeps the **exposure weighting** (a measurement on this project's own raster); the mortality
arithmetic is an appendix stating why it is not a result.

### Four narrowings
- **`partition.f` prints 0.483, not 0.4828.** The fourth digit is unsupported — the value moves
  0.035 across anchored years and 0.058 across window forms. Four decimals read as **overclaiming
  by formatting**.
- **"Any analysis ... will under-price them"** → the measured statement only: *in this nested
  construction, contamination showed up as an understatement of the rung above*. Generality untested.
- **What is validated is named**: a budget-matched procedure on **monitored valley/basin cities**,
  applied to a monitorless one **by analogy**. The target is by construction the kind of city the
  validation set excludes — resemblance, not a transportability theorem.
- **Reproducibility** is **auditable, and reproducible conditional on obtaining the source
  datasets**. Third-party licences make that the honest ceiling.

🟢 **RESOLVED — THE THESIS IS RETITLED** (user chose option C, 2026-09-09):
> *Measuring what an air quality observation is worth: an information-budget approach, demonstrated at Kandy, Sri Lanka*

The old title, *"An information-tiered model for urban fine particulate matter in a city that
cannot check it"*, promised a **PM2.5 product**; §9.9 says the absolute scale at Kandy is not
independently validated. The colon form puts the **contribution** before the colon and the **case
study** after, and *"demonstrated at"* cannot be read as *"validated for"* — the same distinction
§9.9 draws. Kandy stays visible, which matters at Peradeniya and in the CEA correspondence.
⚠ **The summary now carries the SAME title**; the two previously disagreed.
⚠ **Declined on standing instruction:** both asked for a 15–25% length cut.

### 🟢 RETITLED, and the summary format fixed (2026-09-09)
The thesis is now titled *“An information-tiered decomposition for hourly kilometre-scale urban
PM2.5: what it reconstructs, and what each further observation is worth, demonstrated at Kandy”* —
a merge of two candidates, naming **what the model is, what it does, its second job, and where it
is demonstrated**. **“Reconstructs” is the load-bearing verb**: it says what the code produces
without asserting the product has been checked, where *mapping* or *predicting* would reopen the
overclaim the review rounds closed. An earlier draft ended *“…at Kandy, a city that cannot check
either”*; the user trimmed that tail, so **the epistemic caveat now lives only in the abstract and
§9.9**, which is where it belongs — but it is no longer signalled by the title, and anyone quoting
the title alone will not meet it.
**Summary format, user-set:** Times New Roman throughout, **body 12pt and nothing smaller**, title
one step above body, both contact addresses (`11daminda08@gmail.com`, `s20005@sci.pdn.ac.lk`).
⚠ **Two pages is now TIGHT.** 12pt cost a third page; recovered with margins **1.25cm**,
`linespread 0.95`, `titlesec` spacing and ~75 words of genuine redundancy. **Any further addition
to the summary pushes it to three pages** — trim something else, or accept the third page.
⚠ **Two LaTeX traps in the summary preamble, both cost a build:** a `%` comment is escaped by
pandoc into `\%` and breaks LaTeX, and `\selectfont` cannot run before `\begin{document}`.
⚠ **And a shell trap:** backticks inside a double-quoted `python -c` string are command-substituted
by bash. Use a heredoc or the Write tool for any text containing backticks.

**Thesis: 40,024 words · 35 figures · 10 tables · 528 claims · 0 lint errors.** Summary 2 pages.

## Current State (updated 2026-09-08, 🔴 **THE TWO SUBMISSION BLOCKERS FIXED — AND THE KANDY RECOMMENDATION SCOPED TO ONE LOSS**)

Third external review round, scoring **91–93/100** and naming **two things to fix before calling it
submission-ready**. Both fixed. A third point was answered by computation and **produced the most
consequential qualification in the chapter**. Narrative: SESLOG 2026-09-08. Ledger **F.109**.

### 🔴 BLOCKER 1 — an identifiability claim that was mathematically false (§6.4)
The thesis said the unit-mean gauge *"makes level and pattern separately identifiable"*. **It does
not identify `B`.** For any admissible alternative background `B'`, setting
`P' = (C − B')/(T − B')` gives a pattern that also has unit spatial mean and reproduces the same
field — so the gauge is satisfied for **every** candidate background. It identifies the **anchor**
and pins the pattern's normalisation; the split into background and increment is identified by
§6.6's constraints and §6.3's construction, not by the gauge. Corrected, with the counterexample
stated in the text.

### 🔴 BLOCKER 2 — Table 9.1's evidence column cited the wrong result
Row one recommended **a reference monitor** on the evidence *"local sensors are worth 43.7% in this
band"* — while the thesis says elsewhere that **the ladder measured LOW-COST sensors and 43.7% is
not evidence for reference grade**. Rebuilt: the evidence column now names the **kind** of argument
(`LADDER` / `MEASUREMENT DESIGN` / `REGISTERED NULL` / `NO MEASUREMENT`) as well as its content, and
the reference-grade row carries the measurement-design case alone.

### 🔴 F.109 — THE RECOMMENDATION HOLDS FOR AVERAGE DAYS AND REVERSES ON EPISODES
The reviewer's largest surviving point was that everything is scored on daily RMSE. The ladder was
**re-scored under four losses** on the honest MAIAC stream: `rmse` · `mae` · **`tail`** (top decile
of observed days) · **`exceedance`** (balanced accuracy at the WHO 15 µg/m³ guideline).

| step | rmse | mae | tail | exceedance |
|---|---:|---:|---:|---:|
| first two sensors | 22.88 | 23.13 | **5.22** | **0.00** |
| **stations three to six** | **0.13** | **0.00** | **0.00** | **0.00** |
| **a background series** | 33.13 | 34.08 | **39.47** | **33.42** |

🟢 **The redundancy null survives all four** — and this is the result most exposed to the
objection, since the natural reply is that extra stations earn their keep on episodes. They do not.
🟢 **The background is largest under every loss and LARGEST OF ALL ON THE TAIL**, coherent with W2:
Kandy's worst days are substantially regional, and a background series is what sees them coming.
🔴 **But the deep-tropical inversion FLIPS SIGN.** Paired, n=13: rmse **+33.67**, mae **+42.21**
(local wins) — tail **−16.38**, exceedance **−7.57 [−32.10, −2.68], EXCLUDES ZERO** (background
wins). **"Buy a local sensor first" is a statement about daily city-mean accuracy.** For exceedance
detection or health alerting — a stake Chapter 2 names — the measurement says the opposite.
⚠ **A fragility recorded about the headline:** this reimplementation reproduces the RMSE inversion
median (**+33.67** vs recorded **+33.34**) but its interval **includes zero** where the recorded one
excludes it. Resampling detail on **n=13**. **An exclusion that survives one bootstrap and not
another is not robust**, and the inversion is now quoted with that attached.

### Eight further wordings narrowed (none touched a model, a fit or a number)
**Procurement → measurement priority**: §9.1 retitled, and it now says it **informs** procurement
rather than optimising it, since no cost, maintenance, reliability or compliance value enters the
ladder. *"The cheapest recommendation in it"* is gone. · **The positivity constraint** is now a
**non-negative local-contribution constraint**, a modelling choice rather than a physical theorem
— continuous emission is about sources, `T−B` is about a constructed decomposition. · **"Difference
= information loss and nothing else"** → specification and fitting held constant, isolating the
predictive consequence. · **The benchmark is "strongest tested"**, not a mathematical upper bound.
· **"Physics transfers between cities"** → one comparison, reported as motivating a design decision.
· **"One observation captures essentially everything"** now carries its qualifiers inside the
sentence. · **The interval is "nominal and empirically checked"** — conformal coverage needs
exchangeability, which a monsoon series does not satisfy. · **New §9.9** puts *the absolute
concentration scale at Kandy is not independently validated* in the closing position.

**Thesis: 39,476 words · 35 figures · 10 tables · 528 claims · 0 lint errors.** Summary 2 pages.

## Current State (updated 2026-09-07, 🔬 **AN OUTSIDE REVIEW ANSWERED BY COMPUTATION — THREE OBJECTIONS, THREE MEASUREMENTS**)

A full external review (~8.5–9/10 as an undergraduate thesis; weakest on statistical inference and
Kandy-specific validation). **Its three computational objections were answered by running the
experiments rather than by rewording.** All three found something. Narrative: SESLOG 2026-09-07.
Ledger **F.104–F.107**.

### 🟢 F.104 — cities are NOT independent, intervals were too narrow, nothing flips
48 cities fall into **29 clusters** (network × country); **11 are one national network**. A
two-level bootstrap (clusters, then cities within clusters) **widens every interval by 1.34–1.97×**.
The reviewer is right about the width. **Every conclusion survives:** background 40.55% with a
lower bound of **22.3%**; first two sensors lower bound **4.5%**; **stations 3–6 bounded above by
1.37%** — and a null surviving a WIDER interval is strictly stronger, so the redundancy result is
*improved* by the objection.
🟢 **The deep-tropical inversion is unchanged to four decimals** — 13 cities in **12 clusters**,
so Kandy's own band is almost all singletons. **The dependence problem belongs to the POOLED
numbers, not to the band-stratified recommendation Kandy rests on.**
🔴 **A statistic withdrawn from its own output:** naive ICC read 0.82–0.99, an artefact of 23
singleton clusters having zero within-cluster variance. Over cities with a sibling it is
**0.23–0.65**. **Quote the width ratio, never the ICC.**

### 🟢 F.105 — the spatial null is a property of the DATA, not of one model family
Seven admissible families on 47 cities / 636 stations / 60 predictors, leave-one-CITY-out:
**none beats the benchmark (0.301) by more than the registered 0.130 limit.** Best is a GP on
covariates at **+0.018**. **Conventional stepwise LUR — the class the reviewer named, and the one
reaching R² 0.43–0.83 in published campaigns — buys +0.010.** A mixed model with a city random
intercept is indistinguishable from ridge.
🔴 **Kriging and GWR are INADMISSIBLE** — both estimate a surface *from observations at the
target*, which a city with no monitors does not have. Run anyway as an **oracle** with the city's
own stations visible: IDW **0.190**, GWR **0.073**, kriging **0.048** — **all BELOW the admissible
benchmark**. Extends F.60 from IDW to the geostatistical and locally weighted families.
⚠ **The first oracle run reported kriging at −0.833** — an artefact: within-city standardisation
makes Σz=0, so the leave-one-out training mean is exactly −zᵢ/(n−1) and correlates with the
held-out value at **exactly −1.000 in all 46 cities**. Fixed by fitting the normalisation on
training points only.

### 🔴 F.106 — `s_rep` IS externally identifiable, and it is 2.6 to 17× too small
The reviewer's sharpest point: the representativeness error is estimated from the field's own
neighbourhood gradient, so the model prices its own unresolved structure. **It can be identified
without the model**: instruments sharing one cell measure it directly. Panel **14 cells / 36
instruments / 12 cities** → within-cell CV **0.140**; Kandy transect **0.911** (a LOWER bound,
3 of 7 sites censored); model proxy **0.054**.
⚠ **What it does NOT affect:** `representativeness_sigma` lives only in `src/modular/observation.py`
and is **not wired into production**; the shipped interval's width comes from the conformal
`T05–T95` propagation, so gotcha #75 stands (width right for an AREAL quantity, 92.2% after
de-biasing). **What it does:** catches the defect *before* CEA/NBRO data arrives — exactly when the
spec says the observation model must exist. Take `s_rep` from **co-located instruments**.

### 🟢 F.107 — a 2026 Sri Lankan calibration paper the sweep missed
**Senarathna, Attanayake, Bergin, Bhave, Vithanage, Harischandra & Bowatte (2026)**, *Env. Monit.
Assess.* **198**(7):786 — **three authors already load-bearing here, including the supervisor**.
🟢 **Independently corroborates F.63**: Colombo-fitted calibrations lose effectiveness at Kandy,
across climatic zones. *Two unrelated quantities, one conclusion — Colombo stays refuted as a donor.*
🔴 **Names a mechanism for the instrument-class confound**: wet-season calibration applied to dry
season gives **26.57% MAPE**, in a band that is 77% low-cost against 25% elsewhere.
⚠ **Its Kandy reference is the Torrington Park BAM-1020**, recorded here as defunct. **Worth
resolving** — F.101 prices a reference anchor at 10–40k USD.

### Wording the review forced, and it stays
Abstract now says a background **proxy** built from each city's outer ring, not a rural monitor;
states the partition's **0.482–0.547** sensitivity and that the increment is *the spatially
structured component in the domain, not material emitted in Kandy*; and says the Kandy checks test
**the lift above an already anchored mean**. §9.1 bounds the recommendation to *"within this panel,
the deep-tropical stratum is the closest available analogue to Kandy"* — **never "tropical cities
should buy local monitors first"**. §7.11 is retitled **an illustrative projection**.
🔴 **A real defect fixed:** `--number-sections` was double-numbering headings (*"8.3 7.3 The
recommendation inverts"*) because pandoc counted the front matter as chapter one. Removed. The
linter also crashed on any line holding a non-cp1252 glyph; the reporter is now best-effort.

### 🔴 F.108 — A CORRECTION THAT INTRODUCED A DEFECT (2026-09-07, second review round)
The abstract read *"sensitive to the definition of the background window across 0.466 to 0.501"*.
**Those are the min/max over ANCHORED YEARS, not window definitions.** The partition has **three**
sensitivity axes: anchored years **0.466–0.501** · `F_min` sweep **0.482–0.509** · **window form
0.489–0.547**. The abstract attached the right numbers to the wrong descriptor and so understated
the window sensitivity by dropping its largest member. **Introduced while tightening the abstract
for the SAME reviewer's earlier round.** ⚠ **The claims gate cannot catch this** — every token
resolved; the English clause naming what they measured was wrong. Third instance of that limit
after gotchas #86 and #90.

### The rest was claim calibration, not repair (reviewer's own framing)
- **Deep-tropical ordering** now carries its bounding sentence in abstract and §7.3: *the panel
  supports a deep-tropical ordering in which local observations outperform the background proxy;
  how far that reflects an atmospheric rather than a measurement regime is unresolved.*
- **Background conditionality reaches the abstract**, including donor recovery falling to **37%**
  in Kandy's own stratum — transferable information, **not** a figure a rural station delivers.
- **The partition's FIRST appearance (§2.3)** now carries the assumptions and the
  not-a-source-apportionment qualifier, which had lived only in §6.6.
- **"Marginal predictive value" is dominant in results** (§7.2 heading, Table 7.1 caption, the
  abstract's estimand); *value of information* is reserved for Chapter 3's conceptual frame.
  Table 7.1's `Bud1→Bud2` row said "six further sensors" against `pool[:6]` → **stations three to
  six** (gotcha #92, tenth site).

**Thesis: 37,550 words · 35 figures · 10 tables · 477 claims · 0 lint errors.** Summary 2 pages.

## Current State (updated 2026-09-06, 🔬 **A CAMPAIGN DESIGNED, COSTED, REGISTERED — AND ITS OWN PREMISE REFUTED**)

An optimal sensor network for Kandy was designed, justified against physics and siting law,
costed, and pre-registered. **Two of its purposes were then killed by its own analysis, both
before any money was committed.** Narrative: SESLOG 2026-09-06. Ledger **F.98–F.103**.
Plan [`kandy_pm25/docs/sensor_placement_plan_2026-09-05.md`](kandy_pm25/docs/sensor_placement_plan_2026-09-05.md);
registration `docs/prereg_kandy_campaign_2026-09-05.md` (**OSF [`ad3py`](https://osf.io/ad3py/)**).

### 🔴 TWO SENSORS WAS KANDY'S BUDGET, NOT A MEASURED OPTIMUM (F.102) — and the truth is stronger
The user asked whether the ladder's `Bud1` = 2 stations was a finding or a constraint. **It was a
constraint, and the spec says so outright:** `SENSOR_PAIR = "<= 2 local low-cost sensors (the
Kandy budget)"`. Sweeping k = 1..8:

| k | median RMSE reduction vs `Bud0c` | paired gain over k−1 |
|---:|---:|---:|
| **1** | **17.02% [4.57, 21.83]** | — |
| 2 | 17.03% | **+0.01 pp** |
| 3–8 | 17.0–17.2% | ≤ +0.15 pp |

**Saturation is at ONE station, not two.** The redundancy the thesis reported as beginning at the
third monitor actually begins at the **second**. Band-stratified agrees (deep tropical: one
station **20.01%**, second **+0.22 pp [0.00, +2.90]**, 6/13 cities improving) ⚠ **but both bands
are underpowered rather than null.** 🔴 **A prose error found with it:** the code is
`b2 = pool[:6]`, so the second rung is stations **3–6**, described as "three to eight" in **nine
places** — and the two ranges have **opposite signs** (+0.75 vs −0.49). All corrected; the
`stn3to8` claim keys are kept as historical with notes.

### 🔴 DELIBERATE SITING DOES NOT BEAT CONVENIENCE SITING (F.103) — 43 cities, 601 stations
The user's question: *we have cities with robust monitoring networks; can't we test this on
them?* Yes — each dense city can be made into **both** designs by choosing which of its own
stations to fit on. Four fitting strategies, same RidgeCV, scored on held-out stations.

| | median ρ | best in |
|---|---:|---:|
| cLHS (the proposed design) | 0.257 | 16 |
| **convenience (what networks do)** | **0.143** | 12 |

**That table is wrong. Paired within city: −0.044 [−0.095, +0.118], winning 19/43.**
🔴 **Difference of medians +0.114 against a paired median of −0.044 — the SECOND time in one
session** (F.102's temperate band: +12.91 vs +0.14). ⚠ **Undetectable, not refuted** — the
interval does not exclude a +0.118 advantage. ⚠ The promised fixed-holdout re-check **returned
nothing usable**: median city 12 stations → held-out 4 → Spearman quantised to steps of 0.1.
A limit of the panel, **not** a confirmation.

🔴 **CONSEQUENCE — the campaign's spatial ambition is dead twice over.** F.100 says a campaign
this size cannot *detect* a siting effect (needs 96–304 sites); F.103 says there is probably
none *to* detect. **The gap between published LUR (R² 0.43–0.83) and this project's convenience
frames (ρ ≈ 0.3) is NOT siting — it is information.** The campaign must **no longer be described
as testing the spatial ceiling in any form.**

### 🟢 The network that survives (F.99, F.100, F.101)
**35 sites, 5 strata**, over a fine emission surface spanning **65×** p10→p90 of which the
existing records occupy only the **61st–100th percentile**: anchor 1 · design 12 (cLHS over 7
covariates incl. **nocturnal ventilation, drainage convergence, day/night ventilation ratio**) ·
paired 9 · vertical 5 (**8–291 m above the local floor** — the axis no network samples) ·
receptor 8 (held out). **Logistics is a hard constraint, screened BEFORE optimisation**: 19,467
of 25,600 cells serviceable within 400 m of a road.
- 🔴 **D-efficiency ranks the wrong designs first** — road-sited 0.70, existing 0.88, proposal
  0.35 — i.e. it endorses the two designs already known to produce nulls, while road-siting
  samples **one percentile** of the gradient. Reported as a limitation of the criterion.
- **What IS well powered:** within-cell ratio resolves to **1.044 in 7 days** against competing
  predictions of 1.58 and 27.5; drainage is a sign test on **nights** (63.1% over 90); the anchor
  settles the level alone. **H1 (beat ρ 0.309) demoted to exploratory BEFORE funding.**
- **Cost: instruments 9,900 USD** (38 units + 6 spares at a published 225) **+ reference anchor
  10,000–40,000** = **19,900–49,900**. Mounting, power, duty, labour, servicing carry **empty
  unit prices** — none published for Sri Lanka. 🔴 **The re-scope is not worth doing:** trimming
  the design stratum 12→10 saves **450 USD**, under 3%. 🔴 **The largest line may be a letter.**
- ⚠ SVF measured and dropped (CV 0.023) — reproduces gotcha #21.

### 🔬 Chemistry deepened on reviewer request (F.98) — one bound, one null, one invalid
- 🟢 **USABLE:** **Fréchet bounds** put the locally emitted primary share at Kandy between
  **9.1% and 48.3%** — this replaces the withdrawn "removing local sources removes half the
  problem", and shows that claim sat at the **top** of the admissible range.
- 🔴 **REGISTERED NULL:** does composition explain what latitude band only labels? All three
  confirmatory hypotheses **undetectable** (largest partial ρ **0.135** vs MDE **0.431**). The
  deviation is the finding: the exploratory signal that motivated it (pooled 46 cities +0.388,
  p = 0.008) **survives in neither group** — banded 35 cities **+0.093**, CNEMC 11 **+0.036**.
  **A network effect wearing a chemical variable's name.**
- ⚠ **INVALID, neither held nor refuted:** the species-resolved partition ranks **dust 0.806 and
  sea salt 0.645 above black carbon 0.387**. An inland valley has no local sea-salt source, so
  the estimator measures episodic variability, not origin. **Reporting the reversal would report
  an instrument failure as a finding.**

**Thesis state: 34,949 words · 35 figures · 10 tables · 417 claims · 0 lint errors.**
Figures 9.4/9.5 rebuilt portrait with **hillshade and elevation contours** (three maps had none).
Six OSF registrations. All pushed.

## Current State (updated 2026-09-05, 🔬 **TWO REVIEW ROUNDS ANSWERED · A HIDDEN FINDING RECOVERED**)

Two rounds of outside methodological review of the thesis, answered **by computation where
possible rather than by rewording**. Narrative: SESLOG 2026-09-05. Ledger **F.97** + an F.54
re-run block.

### 🔴 THE ONE THAT CHANGED A CONCLUSION (F.97c)
The deep-tropical inversion, **paired within city** and bootstrapped over cities, n=13:

| stream | paired advantage of 2 sensors over background | favours sensors | excludes 0 |
|---|---:|---:|---|
| **GHAP (fused)** | **+3.6 pp [−14.3, +36.3]** | 54% | **NO** |
| **MAIAC (raw)** | **+33.3 pp [+7.0, +50.1]** | 77% | **YES** |

**F.92's inversion, measured on GHAP, was a coin flip.** Same 13 cities, same procedure, only the
satellite stream differs. **The contaminated covariate did not merely shift the numbers — it
destroyed the significance of the finding that matters most for Kandy.** Sharpest consequence of
C1/F.95 in the programme. ⚠ Post-hoc, not registered. **Quote F.96/MAIAC, never F.92/GHAP alone.**

### 🟢 The background rung was TESTED, not just caveated (F.54 re-run)
`independent_background_revalidated.py`. An independent donor network 30–300 km out recovers
**73%** of the `Bud3` gain on the corrected `Bud0c` rung, so the rung carries genuine regional
information. 🔴 The published statistic **moved 79 → 73**. ⚠ It **bounds the artefact from above
and does not measure it**: recovery is 84% at 62 km against 57% at 152 km, so independence is
confounded with proximity. ⚠ **Kandy's own band is the weakest cell** — 37% at 221 km, n=4.

### 🔬 Path dependence + city-level uncertainty (F.97a, F.97b)
- **One reordering is impossible by construction and that IS the finding:** the background is a
  regressor fitted against LOCAL station data, so **it is only ever priceable given some local
  observation.** The ladder's order is partly forced, not chosen.
- Permuting it against monitors 3–8 over 46 cities: background **40.56 vs 38.03%** (order-robust);
  monitors 3–8 **0.13 vs 2.81%** — order-robust in conclusion, **21× in magnitude**. **Never
  quote 0.1% as a fixed quantity.**
- 🔴 The two orders reach the **same information set and NOT the same skill** (0.106 µg/m³ apart).
- ⚠ Because the estimator shrinks back, **the ladder cannot discover a stream is HARMFUL**, only
  that it is unusable. A ~0 rung means *no attainable improvement*, not *no information*.
- **Bootstrap over CITIES** (28,930 city-days is not n=28,930): first two **17.9% [4.6, 23.5]**,
  monitors 3–8 **0.1% [0.0, 0.9]**, background **40.6% [26.7, 45.2]**. 🟢 **The tightest result
  is the null.**

### 🟢 The "48 vs 37" table is NOT an error — and now says so on its face
37 cities carry a band; **11 are CNEMC and carry none**. The country column reaches 32 because
**4 countries span bands** and are counted once in each, while China appears in no band row.
**A per-band distinct count is not additive.** New claims `frame.unbanded` ·
`frame.band_country_sum` · `frame.countries_multiband`.

### 🔴 Claims that were WEAKENED and must stay weakened
- **"Removing every local source removes half the problem" is WITHDRAWN** (Ch2, Ch6, summary).
  The partition is a **constrained decomposition, not observed source apportionment**, and
  **local increment ≠ locally emitted primary material** because there is no chemistry.
  Honest range including the 48-h constraint form: **0.482 to 0.547**.
- **The ladder measured two LOW-COST sensors**, so it does **not** measure reference-monitor
  value. The case for reference grade is a separate measurement-design argument (Ch9.1).
- The estimand is **marginal predictive value using out-of-sample RMSE as the loss surrogate at
  a fixed position**, not decision-theoretic VoI.
- Monitors 3–8 are priced **as networks actually place them**; placement is its own problem.
- The burden interval is **response-function-conditional**, not a total uncertainty interval.

### 🟢 Literature positioning now exists (Ch3.4)
Against Howard 1966 (VoI) · Chaloner 1995 (optimal design) · **Samrat 2025 (observing-system
experiments)** · Verghese 2022 + **Choi & Hummel 2026** (the nearest neighbour: VoI on low-cost
PM2.5 networks, but optimising *placement* in a monitored region). **The IDEA is conceded as not
new** — measuring an observation by withholding it is standard OSE practice. Novelty split four
ways: idea (not new) · application (close to new) · implementation (exact nesting) · two
empirical results. **7 bib entries added, all Crossref-verified.**

🟢 **Attanayake2025 CHECK discharged** — the recorded **title was wrong** (a paraphrase). Correct:
*An RF-CNN pipeline for predicting PM2.5 concentration in Sri Lanka*, JHMA 19:100782.

**Thesis state: 30,052 words · 33 figures · 9 tables · 302 claims · 0 lint errors.** Summary
2 pages. Commits `7564d90`, `12ef445`, pushed.

## Current State (updated 2026-09-04, 🔬 **EVERY NUMBER GENERATED · A SIXTH NULL, REGISTERED**)

Two strands. The manuscript's numbers are now **all generated by scripts and gate-checked** —
`TOKENISATION_BACKLOG.md` group 3 is empty. And the spatial question the paper declares as an
assumption was **tested under pre-registration and the assumption held**.

### 🔴 Numbers that MOVED on 2026-09-04 — quote these
| was | is | why |
|---|---|---|
| panel spans **32 countries** | **29** | never re-derived after the 47→48 frame correction; C4's third sibling |
| Kandy relief **800 m** | **850 m** | prose guess; now from the DEM |
| interval re-centres to **91.5%** | **92.2%** | recomputed against the current field |
| donor benchmark **0.923** | **0.846** pooled / **0.822** matched | 0.923 was the single NEAREST pair (0.928), quoted as a median |
| Kandy–Colombo **93 km** | **93.9 km** | city-centre, the convention every panel pair uses |
| "weakest of 20 donor pairs" | **weakest at comparable separation** | one pair at 285 km scores lower |
| B > T pre-cap: **38.5% / 38.2% / 24.8–36.1 (mean 29.9)** | **38.8% of hours, 53.9% of midday** | 🔴 **one quantity was stated three different ways in one document** |
| §5.7 "1.26–1.47 at matched support" | **model 1.175 monthly vs 1.26–1.51** | the comparison was window-MISMATCHED — an annual model figure against mixed-window observations |
| **5** deep-tropical vs **32** temperate reference clusters | **6 vs 65** | pulled fresh from OpenAQ (20,179 locations); the disparity is **larger**, 10.8× |
| NBRO pixel lift **15.6%** | **15.6% (2021), 17.9% (2022)** | one year's value was quoted as the property |

🟢 **224 claims, 183 resolved, gates 6/6.** New generators: `colombo_donor_test.py` ·
`nbro_pixel_check.py` · `kandy_field_diagnostics.py` · `global_reference_census.py`.

### 🔬 Paper 2 — the learned spatial pattern (OSF [`2jyfg`](https://osf.io/2jyfg/))
Plan `docs/learned_pattern_plan_2026-09-04.md`; note `docs/paper/note_spatial_pattern_2026-09-04.md`.

- **Phase 0** — the sector-weighted emission surface **does not help** (+0.098 vs traffic +0.319).
  Adding **OSM industrial land use** (newly pulled) gives a genuine predictor — best single proxy
  at Tai'an and Medellín, and it rescues Yichang where traffic scores **−0.091** — but no
  engineered surface beats a single free raster. ⚠ Caught mid-run: the traffic surface was being
  scored partly on **zero padding** (21 of 33 Chiang Mai stations outside its footprint).
- **Phase 1** — on **46 cities / 630 stations** the best single predictor is **built-up land
  cover at 2.4 km, ρ = 0.309**. 🔴 The earlier "night lights at 0.34" was an 8-city figure and is
  **withdrawn** (night lights is 0.197). Skill **rises with buffer radius**, peaking at 2.4 km —
  *coarser than the 1 km cell*, which brackets the usable band against the sub-grid finding.
- **Phase 2** — learned pattern **0.286** against benchmark 0.309; median paired delta **+0.022**,
  25/46, p = 0.94, against a registered detection limit of 0.130. **L1 held: the bar (0.44) is
  not cleared.** L2/L3/L4 held; L5 held by the letter only. Gauge exact to **3.3e-16**.
- 🟡 Band difference is real (temperate +0.457 vs +0.225, p = 0.006; survives within-network
  de-confounding, p = 0.002) but the **mechanism is NOT established** — the second network runs
  the other way at n=3–4. The within-network test was **not pre-registered**; label it exploratory.
- **This is the sixth null on within-city spatial pattern and the FIRST with a detection limit
  stated in advance.** `Bud4` stays a declared design assumption — now tested.

## Current State (updated 2026-09-01, 🔬 **AUDIT + FIVE REGISTERED TESTS**)

A full development cycle. Every headline claim was re-derived from the scored files; **three did
not reproduce**. Five registered tests ran, **three refuted**. The model has composition data for
the first time. Narrative: SESLOG 2026-09-01. Plan:
[`kandy_pm25/docs/improvement_plan_2026-09-01.md`](kandy_pm25/docs/improvement_plan_2026-09-01.md).

### 🔴 Numbers that MOVED today — quote these, not the August ones
| was | is | why |
|---|---|---|
| 47 cities / 32,396 city-days | **48 / 28,930** | superseded pre-F.84 frame (C4) |
| satellite helps coastal **4x** | **1.8x** (satellite alone) | the 4x was geography+satellite, reported under the satellite's name (C2) |
| `w_Bud2` ref **0.000** / LCS **0.900** | **0.350 / 0.575** | stratified stats were never re-derived after the re-validation (C3) |
| `Bud0c→Bud1` **17.8%** | **15.8%** stream-complete | one city was scored in `Bud0c` with no STATIC_GEO (C7) |
| P4: 19 `identified` | **13**, 11 zero-width artefacts removed | grid too coarse (C5) |

🟢 **`s_exp` survived the P4 refinement** — all 9 profile intervals contain 1.0, so F.77's
decision rests on an interval rather than an artefact.

### 🔬 Registered results (OSF `bkpyr`, `kx23c`) — ledger F.89–F.93
- **S1 REFUTED** — at 94 m the paired microsites read **1.135×** against 27.5× observed. The
  spatial question is **closed**. 🟢 But its premise died too: the dispersed field spans **18.7×**
  at 998 m, so contrast is **misplaced, not lost to resolution**.
- **R2 REFUTED** — `A_transport` scored at last and it **costs** rank (+0.371 → +0.274, 3/10
  cities). **The abstract must state the headline field excludes it.**
- **S2 delivered** — within-pixel spread **1.218×** exceeds between-pixel **1.049×**, gauge-exact
  to 7e-15. Most midday spatial variation is **sub-grid**.
- **R1 — 🔴 THE ACQUISITION ADVICE INVERTS FOR KANDY (F.92).** Pooled says background (40.6%);
  Kandy's own band says **local stations 21.9% vs background 8.5%**. **CEA now outranks NBRO.**
  🟢 **CONFIRMED AND DOUBLED on the honest stream (F.96): 43.7% vs 10.3%, local wins 4.2×.**
- **Chemistry (F.93)** — **C-H1 HELD**, continental air is more secondary-rich than marine
  (0.410 vs 0.365, p=3.1e-09): **the decomposition's first chemical corroboration**. **C-H2
  REFUTED usefully** — stagnation ages air in place, so *"local increment = fresh primary"* is too
  simple. **OC/BC 13.8** is a third independent refutation of "~90% vehicular".

### 🟢 C1 — RESOLVED 2026-09-01 (F.95): the honest stream costs nothing
GHAP trains on ~9,500 stations **including OpenAQ and CNEMC, this panel's own sources**, and its
predictors substantially overlap our other two streams. `Bud0c` was not drivers + geography + an independent
observation. **RESOLVED:** raw MAIAC AOD scores **+5.97%** against the fused GHAP's **+5.37%** —
the fused product shows **no excess**, so its apparent value was satellite information, not
recycled information. **Switch `SATELLITE_LEVEL` to MAIAC**: admissible, no leakage, no shared
drivers, and at least as good. 🟢 **P5 held — geography (10.8%) still beats the satellite level**
on an honest stream. ⚠ 11 of 47 cities carry AOD on <30% of days (cloud). Research note:
`kandy_pm25/docs/c1_satellite_stream_research_2026-09-01.md`.

### 🟢 Machinery that now prevents the recurrence
`scripts/build_claims.py` regenerates **99 claims** from source with statistic, n and provenance;
`assemble_manuscript.py` **refuses to build** if prose and data disagree (it blocked on first use);
`scripts/submission_gate.py` runs six checks. `Budget.require_covers_units()` closes C7 in code.

### 🟢 THE PAPER IS DRAFTED END TO END (2026-09-03)
9,754 words, 8 sections, **9 figures**, 50 citations, 135 claims. **Edit `draft_s*.md`, never
`manuscript_kandy.md`.** Build: `scripts/build_claims.py` → `docs/paper/assemble_manuscript.py`
→ `docs/paper/build_docx.py`. The build **refuses** if prose and data disagree.
- Sections: `draft_s1_problem` · `s2_formulation` · `s3_design` · `s4_value_of_information` ·
  `s5_where_it_stops` · `s6_kandy` · `s7_forbids` · `s8_discussion`. The 2026-08 drafts
  (`draft_s1_s2_intro` etc.) are **superseded and not built**.
- Figures: `scripts/paper2026_figures{,_b,_c}.py`. Every value reads `claims.json`.
- ⚠ **Never write "four guaranteed properties"** — two guarantees (P1, P3), one enforced
  mechanism (P2), one discharged (P4).
- ⚠ `F_cycles` predates the current field build by a day: **regenerate before reuse.**

### Pending
1. **Circulate the paper** to the four readers — user action, and the critical path.
2. **MAIAC gap-fill** complete; C1 and F.92 both resolved (F.95/F.96).
2. **R3** (competitor benchmark) untried. 3. **Phase 6** propagation to the release repo.
4. Approve the two OSF registrations (48-h window). 5. **Send the CEA letter** — now the
   highest-value acquisition by measurement, not just the only route.

## Current State (updated 2026-08-14, 📄 **NEW PAPER BUILT END TO END, 28 pp**)

The preprint is superseded. A new manuscript was defined, evidence-frozen, drafted, figured,
adversarially reviewed and built. It lives in `kandy_pm25/docs/paper/`, targets **ACP via
EGUsphere**, and stands at **28 pp, 11,753 words, 11 figures, 61 references, 3 CHECK flags**.

- **How it is built** → `PROJECT_ARCHITECTURE.md` § "Manuscript build".
  **Edit `draft_s*.md`, never `manuscript_kandy.md`** — the latter is a build product.
- **What the checking produced** (14 numerical corrections, 12 review findings) → `PROJECT.md`
  § "2026 manuscript". Narrative → SESLOG 2026-08-13/14.
- Phases 0 to 8 complete. **Phase 9, circulation to the four readers, is the user's step.**

### 🔴 Three corrections that change how things must be SAID
1. **f = 0.4828**, from `kandy_partition_v2.json`. `additive_partition.csv` is stale at 25.3%
   and renamed `_v1_superseded`. Never quote it.
2. **The gauge is not exact.** The field runs **+0.39 to +0.56%** above the anchor every year.
   Say "to within 0.6 per cent". The old G1 check compared two fields sharing the drift.
3. **eps0 for Kandy is 3.69**, not 2.573; it scales with mean accumulation, which the cap moved.

### 🟢 NBRO is a live data route
Nirmani et al. (2025) obtained **daily Kandy PM2.5 for 2021–2022 from NBRO on official
request**. Letter drafted (`docs/EMAILS_TO_SEND.md` #4), alongside a Met Department letter (#5)
for station meteorology. NBRO is cheaper than CEA: no R&D agreement, no manipulation clause.
**Their Table 1 has now been read directly — see the 2026-08-22 block below.**

## 🆕 Literature-recovered Kandy ground truth (2026-08-22, ledger F.64–F.67)

Three papers supplied by the user were read. They produced **the first independent checks on the
Kandy field in the project's history**, one corroboration, one contradiction, and one live
acquisition lead.

| finding | ledger |
|---|---|
| 🟢 **W5 CORROBORATED** — FECT Akurana full-record mean **17.8** against a BAM-anchored published study's **~18–19** | F.64 |
| 🟢 **NBRO Kandy (KAN), 24-h, N=360/yr**: obs **19.6** (2021) / **22.7** (2022) vs model at that pixel **19.74 / 22.11** — **+0.7% / −2.6%** | F.65 |
| ⚠ **A BAM-calibrated LCS at Kandy** (7.2731, 80.6117) reads **19.49** where the model says **25.01** — **+28% high** | F.65 |
| ⚫ **A reference-grade BAM-1020 stood at Torrington Park, KANDY** — **but it is DEFUNCT (user, 2026-08-22)**. Provenance for the published records; **not** a data route. **CEA is the only route to a Kandy reference monitor.** | F.65 |
| 🔴 **W6 REOPENED** — Kandy PMF: **traffic 7.6%**, **biomass burning 14.1%** of PM2.5 mass | F.66 |
| ⚠ Nirmani's meteorology is **Open-Meteo/ERA5 reanalysis**, not station data — their Kandy CBPF source attribution is weak evidence | F.67 |
| 🟢 **A 25-site Kandy PM10 transect measures the spatial ceiling's CAUSE** — **110 → 4 µg/m³ over 300 m**, R² **0.82** vs traffic. The signal is huge but **sub-grid**: decay length tens–hundreds of metres against a 1 km cell | F.68 |
| 🔴 **Scored: observed spread across Kandy 85×, model spread 1.23×.** Paired microsites 300 m apart: **27.5× observed vs 1.000× modelled** (same pixel). Rank ρ +0.44, n.s. **First within-Kandy spatial test ever run** | F.69 |

### 🔴 The level discrepancy this opens
Of four independent Kandy point records, **three sit below the model** and **one matches it**.
The three low ones are all low-cost sensors carrying a downward calibration correction; the one
that matches has an **undocumented instrument**. This is not resolvable from the literature and
it is a **level** question — the axis the programme calls strong. **State it as an open
discrepancy; do not resolve it by picking the record that agrees.**

### 🔴 What must no longer be said
**"Kandy ~90% vehicular" is refuted as a mass share.** The defensible statement is: *traffic
dominates the local increment's sub-daily **timing** (measured, F.23); it is a **minority of
local PM2.5 mass** (measured, F.66).* This is the strongest case yet for wiring the
sector-weighted `S_emit` — but as a **correctness fix, not an expected skill gain** (the spatial
ceiling F.56/F.61 means it will not move ρ), and Kandy's burning sector has **no admissible
FIRMS proxy** (incense, oil lamps and domestic burning are invisible to FIRMS, exactly as
Kathmandu's kilns are).

## Model formulation (target architecture, 2026-08-18)

The model is being restated as an **information-tiered grey-box decomposition**: a hierarchical
latent-process model with an explicit **observation operator**, **declared information budgets**
(`Bud0` sensorless → `Bud4` spatial network), and four guaranteed properties — **P1**
conservation, **P2** monotone skill under added data, **P3** exact degradation between tiers,
**P4** declared identifiability. Spec: [`kandy_pm25/docs/MODEL_SPECIFICATION.md`](kandy_pm25/docs/MODEL_SPECIFICATION.md);
reasoning `model_formulation_2026-08-18.md`; ML placement `model_formulation_ml_map_2026-08-18.md`.

- **The largest gap is that there is NO observation model.** Point sensors are compared to an
  areal field by naive co-location — the origin of gotcha #75. `H_k`, `b_k`, `sigma_rep` must
  exist **before** any CEA/NBRO/Met data is ingested, or the first comparison repeats it by hand.
- **Second gap: no tier registry.** Tiers live in filename suffixes and scattered flags, so
  admissibility is enforced by discipline, not construction (gotchas #68 and #73 were both
  caught by audit after the fact).
- ⚠ **Three claims NOT to make:** "every layer is ML" (B's dilutive part and P's shape are
  *measured* unlearnable) · "fully captures atmospheric physics" (no chemistry, no secondary
  aerosol, no deposition, no vertical structure; `A_transport` unscored) · "works coastal"
  (the panel is 10 cities, **all valley/basin, zero coastal**). "Forecasting" in a title
  requires a per-lead skill curve first.
- Defensible framing: *an information-tiered grey-box decomposition for urban PM2.5 in
  data-scarce cities, with exact degradation between tiers and monotone skill under added
  observation.* The contribution is the **declared budget with guaranteed nesting**, not the
  physics and not the ML.

## Budget-ladder validation — RE-VALIDATED 2026-08-23 (ledger F.50–F.53, **corrected by F.84–F.87**)

**Modular decomposition built** (`src/modular/`: budgets · observation model · constraints ·
shrinkage · tier harness · production bindings · sector emission surface; **68 tests**).
Spec [`kandy_pm25/docs/MODEL_SPECIFICATION.md`](kandy_pm25/docs/MODEL_SPECIFICATION.md);
registration `docs/prereg_modular_validation_v2_2026-08-18.md` (option C + 2 amendments).

**Frame: 47 cities scored, 4 latitude bands, 32 countries, 32,396 city-days.** OpenAQ ingest
46/46 attempted → 37 retained (9 excluded, named, never replaced) + 11 CNEMC. All six gates run.

🔴 **THE 2026-08-19 STEP GAINS ARE RETIRED (F.84).** The scored `Bud0` used **one of the
three streams its budget admits** — drivers only, no satellite level, no static geography — so
every gain above it was measured against an artificially weak baseline. Fixed in code by
`Budget.require_covers()`; re-registered at **https://osf.io/g6hqb/** and re-run.

**THE BOTTOM RUNG IS NOW DECOMPOSED**, so each globally available stream is measured on the same
footing as a monitor (median RMSE across cities):

| rung | median RMSE | step |
|---|---:|---:|
| `Bud0a` reanalysis drivers only | 21.94 | — |
| `Bud0b` + static geography | 20.31 | **10.8%** |
| **`Bud0c`** + satellite level — *the spec-compliant `Bud0`* | 19.99 | **7.6%** |

🟢 **Static geography (10.8%) beats the satellite level (7.6%)** — an annual satellite level
cannot touch day-to-day variance, which is what daily RMSE is made of.

**Step gains from `Bud0c` (median % RMSE reduction) — QUOTE THESE:**

| step | pooled | deep-trop | tropical | subtrop | temperate |
|---|---:|---:|---:|---:|---:|
| `Bud0c→Bud1` (+2 stn) | **17.9** | 21.9 | 6.7 | 29.7 | 33.5 |
| `Bud1→Bud2` (+6 stn) | **0.1** | 0.9 | 0.1 | 0.3 | 1.1 |
| `Bud2→Bud3` (+background) | **40.6** | 8.5 | 39.8 | 36.0 | 31.6 |

⚠ The **band ordering flipped**: the first two stations now buy most in the **temperate** band
(33.5) and least in the **tropical** (6.7), where previously the deep tropics led at 38.5. And in
the deep tropics the background rung **collapses from 28.1 to 8.5** once a satellite level is
present — the satellite substitutes for the background there. ⚠ Subtropical and temperate cells
are **n=7**; small.

🔴 **THREE CONFOUNDS CAUGHT BY REGISTERED GATES, not by review** — each invisible in the pooled
numbers and each would have reached a paper:
1. **country × latitude** (Amendment 2) — the min-GEE design made the mid-latitude arm 33
   cities all Chinese, aliasing band with network.
2. **driver completeness × band** (F.51) — BLH coverage differs 5.1 pp; re-ran without BLH,
   only the top-two ordering flips (a 0.013 gap), the temperate deficit survives.
3. **instrument class × band** (F.52) — the deep-tropical cell is 69% LCS, the rest
   reference-dominated.

🔴 **"More in-city stations buy nothing" is a REFERENCE-NETWORK result.** Median `w_Bud2`:
reference **0.000**, LCS **0.900**. LCS carry per-device error, so averaging more of them cuts
noise. **Never state V4 unconditionally.** The pilot's 2.9% (F.50) must not be quoted — its
`Bud0` had lat/lon and could identify the city.

🔴 **Two registered priors REFUTED**: `Bud0→Bud1` does NOT dominate (background does); and
`Bud0` is worst in the **temperate** band (normalised 1.194), not the deep tropics (0.792).

🔴 **And five of eight re-validation priors refuted (F.85)** — including my headline one: I
registered the satellite level as the largest step below the ground rungs at 25–45%; it is
**7.6%**. 🟢 **The coastal test held strongly:** a satellite level helps coastal cities **four
times** as much as inland (24.4% vs 6.2%, n=21 vs 27; **not** confounded with instrument class,
Fisher p=0.38).

🔴 **F.53 — the class/band confound CANNOT be sampled away.** Worldwide only **5** deep-tropical
clusters have ≥10 concurrent reference stations, against 32 temperate. *The regime that most
needs a sensorless method is where reference monitoring is scarcest* — a finding in its own
right. Decision: report class-stratified throughout; treat the **LCS stratum as the Kandy
analogue** (Kandy's sensors are low-cost); do not chase a de-aliased draw.

⚠ **Unchanged caveat:** `Bud3`'s background is an outer-ring proxy from the SAME network in
every city, so its large gains partly measure "more of the same network". Only a true regional
network settles it — **which is exactly what NBRO would be at Kandy.**

**Sector-weighted `S_emit`** (`src/modular/emission.py`): `S = norm(Σ w_k · norm(proxy_k))`
using the `emix` already declared per city — which previously fed only `e(t)`, so Kathmandu
asserted 50% burning in TIME and 100% roads in SPACE. Population + FIRMS surfaces pulled for all
11 panel cities. `vehic=1.0` reproduces the traffic surface bit-exactly. **Built and tested, NOT
wired into production.** ⚠ Kathmandu returns **zero FIRMS detections** (kilns are continuous
combustion, not open flame) → its burn sector falls back to a flagged placeholder; industry has
no proxy and no admissible fallback. **⚠ F.66 shows Kandy has the same problem.**

**GEE cost assumption was WRONG** and is corrected: daily/static pulls are **minutes, not days**
(ERA5-Land daily 5.3 s/city via `getRegion`; GHS-POP 5 s; FIRMS 26 s). The multi-day rule
applies to hourly Drive exports only. Two real traps: gotcha #44 memory limit on 2-yr hourly
BLH (fixed by quarterly chunking) and **ERA5-Land has NO DATA OVER WATER** — 4 coastal/island
cities failed until falling back to global ERA5.

## The three axes — measured evidence state (2026-08-19, ledger F.55–F.62)

The model reconstructs an hourly 1 km field, but its **evidence is anisotropic**. All three axes
have now been tested on the widened frame, and two have measured ceilings.

| axis | evidence | status |
|---|---|---|
| **level, daily** | 47 cities, 4 bands, 32 countries; monotone under added data; background gain 75% reproduced by an INDEPENDENT network 89 km away (F.54) | **strong** |
| **sub-daily shape** | transfers in the **deep tropics** (+25.8% vs flat, r 0.63, ~1 h phase error) and **nowhere else**; pooled it is 5.5% WORSE than assuming no cycle (F.55) | **regime-limited** |
| **spatial pattern** | **rho ~ 0.2–0.28 ceiling**, unmoved by four successive attempts (F.56/F.58/F.59/F.61) | **ceiling measured** |

🟢 **2026-08-22 — the ceiling's CAUSE is now measured in Kandy itself (F.68).** A 25-site
PM10 transect with per-site traffic counts (Elangasinghe & Shanthini 2008, 2004–06) records
**110 → 4 µg/m³ over 300 m** inside one botanical garden, and **R² = 0.82** against traffic
intensity. Kandy's within-city signal is *enormous*; its **decay length is tens to hundreds of
metres**, and a 1 km cell integrates over exactly that decay. **The pattern is sub-grid by
construction, not missing from the data.** This upgrades the ceiling from "our networks are
inadequate" to a **change-of-support** statement, and retrospectively justifies `Bud4`'s
demotion. ⚠ It does NOT resolve W6 — roadside PM10 *spatial variance explained* and ambient
PM2.5 *mass share* are different quantities.

🔴 **The spatial ceiling survived proper instrumentation.** A full LUR predictor set — road
length by class at 50/100/300/500/1000 m, distance-to-road, NDVI, tree cover, water, land-cover
fractions, built volume, population, night lights at 4 radii, 636 stations, 47 cities — moved
pooled rho from **+0.273 to +0.275**. The literature's strongest predictor ("major roads within
100 m") buys nothing here. Published LUR reaches R² 0.43–0.83 because those campaigns **site
monitors deliberately across land-use contrast**; regulatory and LCS networks are sited for
compliance, so ours is a convenience sample with coordinates, not a LUR design.

🔴 **`Bud4` is UNSUPPORTED as specified.** A spatial network does NOT make `P` estimable:
inverse-distance interpolation between a city's own stations is **worse than assuming the city
is uniform** (F.60), and a transferred LUR barely beats a population raster (F.61). Every other
rung of the ladder is validated; this one is a declared design assumption and must be labelled
as such.

🔴 **The diurnal dilution term is ~zero.** Fitted exponent **0.054** against 1.0 for pure
inverse-BLH dilution — a ~40× diurnal swing in boundary-layer height produces almost no swing in
city-mean PM2.5, because in `PM = B + local` only the local increment dilutes while `B` is
already well mixed. So there is no physical component to peel off and transfer (F.62). The
civil-vs-solar-time sub-hypothesis is **refuted by construction**: true offsets are median
+0.29 h, max +1.87 h, against a 7.5–8 h phase error.

**⚠ ACQUISITION CONSEQUENCE — this changes the CEA/NBRO priority.** Do **not** request the CEA
passive NO₂ network as a fix for `P_local`; its value is the `f` partition and local activity
tracing (F.45). ⚠ **SUPERSEDED 2026-09-01 by F.92 — see below. For KANDY, local stations outrank the background station.** The claim below is the POOLED result: the background rung
is the largest measured gain in the programme and 75% of it survives an independent network.
**⚫ 2026-08-22 correction: the Torrington Park BAM is DEFUNCT** (user). It anchored the
published RF-CNN calibration and Dhammapala's correction, but it is not a data route. **CEA is
the only route to a Kandy reference monitor**, and it alone would settle the level discrepancy
(W11) and the W6 source-mix question.

🔴 **AND THERE IS NO FREE SUBSTITUTE (F.63).** Sri Lanka has three OpenAQ locations, all inside
the admissible 30–300 km donor window — Colombo at **93 km, reference-grade, already on disk**.
Tested: Kandy–Colombo daily **r = 0.604** (≈0.70 attenuation-corrected) against a benchmark
median of **0.923** at that distance — **the weakest of all 20 donor pairs**. The central
highlands decouple coastal Colombo from inland Kandy, especially in the SW monsoon.
**Do not re-propose Colombo as a background donor.**

Docs: [`docs/spatial_diurnal_remediation_plan_2026-08-19.md`](kandy_pm25/docs/spatial_diurnal_remediation_plan_2026-08-19.md)
(plan + outcomes) · `MODEL_SPECIFICATION.md` §10.3 · ledger F.55–F.62.


<!-- CLAUDE.md lines 1283-1287 -->
### Stage A v1 — Daily XGBoost temporal anchor — SUPERSEDED by v3 (retained as 22-yr chronology)
- XGBoost, 44 features, 8,279 days (2003–2025). **LOMO R²=0.631**, RMSE=4.82, 90% PI=89.4%.
- Methodological weakness: KOALA used both to calibrate labels (×0.598) AND to validate (r=0.515) → circular.
- Models on disk: `results/models/xgboost_kandy_pm25.ubj`, `xgboost_q05/q50/q95.ubj`. Pixel model ORPHANED.


<!-- CLAUDE.md lines 1302-1314 -->
### Stage A v2.1 — Daily RECAP (SUPERSEDED by v3; retained as baseline)
- **Reframe:** CAMS + GEOS-CF as FEATURES (residual learning); FECT-calibrated PurpleAir as LABELS. Pre-reg `docs/osf_prereg_stage1_v2.md`, 6 amendments locked 2026-05-17.
- **Data:** 1,550 sensor-day rows (Akurana **~460m**, ~6km N of Kandy/out-of-bbox + Hantana TR4 **~738m**, 7.265N/80.625E), 2018-10 → 2026-05. Both **valley/suburban, NOT highland** (see `docs/audit_2026-05-29.md` E1–E3). 28 mechanistic features.
- **v2.1 LOMO:** pooled **RMSE 5.73, R² +0.689, cov90 0.88** (62 non-empty folds).
- **Baselines:** persistence 6.39, doy_clim 10.13, cams_scaled 12.67, geos_scaled 14.24.
- **🎯 Pre-reg H1 SATISFIED: 60% RMSE reduction vs GEOS-CF×0.536** (threshold ≥15%).
- **Surprising finding:** AOD + GEOS-CF added only +1.4% over v2.0. Meteorology + CAMS_raw carry most signal.
- **§6.4 + §6.5 ablations DONE:** ΔRMSE ranking: **G temporal +13.1%** > E reanalysis +8.0% > C wet scavenging +5.6% > E cams-only +3.1% > E geos-only +1.4% > STATION +0.7%. Vector valley TBI (B) and AOD (D) add essentially zero.
- **NGBoost Student-t variant:** `train_ngboost_v2.py`. Switched to `TFixedDf(df=5)` due to gradient instability (documented pre-reg deviation). XGBoost-quantile is primary (CRPS 2.65 < NGBoost 3.86).
- **Embassy Colombo OOD (§6.6): H4 SATISFIED.** `results/models/xgboost_v2_full_kandy.ubj`. 1,661 Embassy daily rows: **cov90 0.861, RMSE 9.51, bias −4.92, R² +0.452, CRPS 3.76.** Honest finding: **point estimates degrade OOD but calibrated UQ transfers.**
- **§6.1 anchor sensitivity:** R² invariant +0.689 across KOALA ∈ {20,22,24.5225,27,29}. **§6.2 OOY holdout:** asymmetric — beats persistence forward, loses backward. **§6.3 cross-product triangulation:** v2 ~14 vs VanD ~19 vs GEOS/CAMS ~24. Paper hook: "calibrated to station ≠ calibrated to area".
- **Models on disk:** `data/processed/stage1_v2/dataset_v2_multistation_daily.parquet`, `training/{predictions_lomo_v2.parquet, summary_v2.csv}`.


<!-- CLAUDE.md lines 1320-1351 -->
### Stage B — Cross-city ConvCNP residual learner ✅ CAPABILITY LOCKED (v14 + conformal); Kandy production maps HELD (2026-05-23)
- **Target: `pm25 − c_prior_scaled`.** deepsensor 0.4.2 ConvNP, UNet (32,64,128), 625,989 params, heteroscedastic Gaussian likelihood.
- **N=3 source cities (LOOCV):** Mel, ChiMai, KTM. Bogotá + MexCity DROPPED. Title is **"supervised cross-city ConvCNP"**.
- **Training data:** 100 stations × 1.24 M hourly rows (OpenAQ S3 + AirNow Embassy, per-LCS calibrated).
- **Cascade (locked 2026-05-21):** v12 OSM road density → v13 + VIIRS NTL + wider terrain → **v14 UQ restoration (Student-t / σ-floor)** → v15 + EDGAR sector.
- **v13 COMPLETE**: KTM r **0.590**, ChiMai **0.820**, Mel **0.280**. **Mean r 0.563** (+0.120 vs v12). **KTM bias +6.48**. **G1/G6 PASS for first time**. **G4 FAIL across all cities** (cov90 collapsed). Kernel `damindaalahakoon/kandy-convcnp-loocv-v13`.
- **v14 COMPLETE (Student-t df=5)**: KTM r **0.682**, ChiMai 0.795, Mel **0.321**, **mean r 0.599** (best ever). **KTM bias +0.14** (G6 PASS by an order of magnitude). Cov90 KTM 0.754, ChiMai 0.508, Mel 0.518 — **G4 still FAILS.**
- **v14 interpretation (physics correction):** Student-t encourages *tighter* σ, not wider. Best-ever median estimator, worse interval estimator — opposite of what the v14 plan predicted.
- **v14-conformal COMPLETE**: q̂ Mel 6.33±2.82, ChiMai 5.95±1.28, KTM **3.13±0.11**. **Calibrated cov90: Mel 93.0%, ChiMai 89.5%, KTM 91.5% — G4 fully satisfied.** Script `scripts/conformal_calibrate_v14.py`.
- **Final UQ pipeline (locked)**: Student-t(df=5) NLL during training + split-conformal scaling at inference. Paper framing: "robust point estimation + calibrated intervals via post-hoc conformal" (Vovk 2005, Romano 2019).
- **Kandy zero-shot inference RUN (2026-05-23, full year 2024, 2.25M predictions)** — pipeline + outputs work; consistency anchors pass; **maps technically defensible but spatially smoothed-out**. Checkpoint `convcnp_v13_holdout_medellin_seed3.pt`. σ scaled by KTM analogue q̂ = 3.13 or per-hour Mondrian q̂ ∈ [2.13, 3.54]. **Result HELD as preliminary, NOT for publication.**
- **Three consistency anchors PASS** (NOT called validation): annual mean 22.1 vs KOALA 24.5 ✅; seasonal DJF 27.7 / MAM 26.3 / JJA 11.5 / SON 23.0 ✅; diurnal nocturnal plateau ~37, midday trough ~7 ✅
- **Known limitations:** diurnal morning peak phase off by ~4 hr; negative-value floor (−12 in tail extremes, clipped at 0 for plotting only); PI widths ~20 annual mean up to 60 nocturnal. **Stage B transfer claim remains "exploratory cross-city" not "validated".**
- **Sim2Real Phase 2 (N=2 FECT) NEGATIVE RESULT**: fine-tuned on Kandy 2018-2023; held-out eval at the *exact* FECT (lat,lon): r 0.43 → **0.9999**, RMSE 15.39 → **0.12**. But on the 1 km grid annual mean inflates 22.1 → 37.0. The model memorised the *exact* sensor (lat,lon) as identity keys, not Kandy basin physics. **Documented as the §6 ablation motivating the ≥5-sensor data-acquisition agenda.**
- **Mondrian (per-hour) conformal COMPLETE**: test cov90 ChiMai 91.4%, KTM 87.0%, Mel 89.6%. Kandy mean PI width 20.5 → 18.9 (8% tighter). Script `scripts/conformal_per_grid_v15.py`.
- **🎯 PVAF v2 "Expansion-E" — source-set RE-SELECTED 2026-06-01.** Fixes the documented v15 failure (magnitude-blindness selected 3–4×-dirtier industrial basins). Added **magnitude (E1, w0.24)** + **pattern (E2, w0.12)**; Kandy ref = **bias-corrected AREA mean 24.5** (NOT FECT 13.6). **Selected source set (N=9):** Xichang, Bazhou, **Kathmandu, Medellín, Chiang Mai**, Puebla, León, Sandton, Hyderabad. **Valley-grade core: Xichang, Bazhou, Kathmandu, Medellín, Chiang Mai.** Caveat: Sandton anti-phased (pattern 0.45) — recommend drop. Output `data/processed/pvaf/expansion_e_ranked.csv`.
- **PVAF v15 source-set LOCKED 2026-05-24 (N=10) — SUPERSEDED.** Magnitude-blind.
- **Room for improvement (deferred):** more source cities via PVAF; Sim2Real with ≥5 spatially-diverse sensors; per-pixel σ inflation from terrain uncertainty.
- **Kaggle dataset**: `damindaalahakoon/kaggle-dataset-kandy-stage3`.
- **Source tree:** `src/stage3_pinn/models/convcnp_terrain.py`, `data/convcnp_loader.py`, `training/train_convcnp.py`, `training/loocv_convcnp.py`.
- **Data invariants:** `scripts/validate_perstation_parquets.py --version v13 --strict` (13 checks/city). v13 PASS 39/39.
- **Data dictionary:** `docs/stage_c_data_dictionary.md` (v11 — refresh pending).

### Supporting experiment 1 — Cross-continental PINN transfer (Mel → ChiMai) ✅ COMPLETE
- TD-PDE: Medellín (R²=0.932, ep1400) → ChiangMai (R²=0.765, bias=−0.59, ep2200).
- Canonical ckpts: `results/models/stage2_medellin_pinn/td_pinn_v1/checkpoints/epoch_01400.pt`, `stage2_chiangmai_pinn/td_pinn_v1/checkpoints/epoch_02200.pt`.
- FourierPINNV3, **76,261 params**. v7 curriculum: Phase 1 λ_pde=0; Phase 2 ramp 0→0.15; Phase 3 0.15.
- Status: standalone methodology study. NOT a feeder for Stage B.

### Supporting experiment 2 — SharedTerrainAnsatz identifiability diagnostic
- All 6 rigid-Whiteman parameters hit bound constraints across Mel + ChiMai + KTM. LOOCV: ChiMai r=0.323, KTM r=0.863. Status: documented diagnostic motivating the move to ConvCNP. No further iteration planned.


<!-- CLAUDE.md lines 1487-1497 -->
**Supporting cross-continental PINN data & models**
- Parquets: `data/processed/stage2/`
- Medellín TD-PDE v1: `results/models/stage2_medellin_pinn/td_pinn_v1/checkpoints/epoch_01400.pt`
- ChiangMai TD-PDE v1: `results/models/stage2_chiangmai_pinn/td_pinn_v1/checkpoints/epoch_02200.pt`
- ChiangMai PINN v5 (QSS reference): `results/models/stage2_chiangmai_pinn/v5/checkpoints/epoch_04000.pt`

**Stage B Tier C+ data & kernels**
- Tier C merged: `data/processed/tier_c/kandy_tier_c_merged.parquet` (70,128 rows, 21 cols)
- PINN inputs: `data/processed/pinn_inputs/kandy_elev_grid_100m.npz`, `kandy_terrain_wind_100m.npz`, `kandy_road_kernel_100m.npz`, `kandy_stage1_pixel_preds.npz`, `kandy_terrain_tpi_svf_100m.npz`
- Kaggle kernels: `data/processed/stage2/kaggle_kernel_kandy_td_pinn_v*/`; logs `kaggle_logs/kandy_td_v*/`; dataset dir `kaggle_dataset_kandy_stage3/`


<!-- CLAUDE.md lines 1510-1515 -->
**PVAF v1 (Physics Valley Analogue Finder)**
- Pre-reg: `docs/osf_prereg_pvaf_v1.md` (OSF guid `ykdb9`, locked 2026-05-23)
- Plan: `docs/pvaf_v1_plan.md`; source `src/pvaf/`; CLI `scripts/pvaf/`
- Features `data/processed/pvaf/{city}_features.json`; pool `candidate_pool.csv`; rankings `tier1_rankings.csv`
- Reports: `reports/pvaf_tier1_summary.md`, `reports/pvaf_tier1_sanity_n4.md`


<!-- CLAUDE.md lines 1770-1857 -->
### 0v. Superseded IMMEDIATE list (2026-09-09d)
0. **THE THESIS NEEDS A HUMAN READ END TO END.** 42,637 words, 566 claims, gates green, four
   rounds of outside review answered, and a full humanisation pass. Every mechanical check runs on
   every build; **none of them checks that a number is meaningful, only that it is current** — and
   F.108 proved the claims gate cannot catch an English clause that names the wrong thing.
   ⚠ **The style pass raises the stakes:** three mechanical rewrites broke the sense this session
   and were repaired by hand, so a human read is now checking meaning the guards never touched.
   User action, and the critical path for the thesis.
0a. **APPROVE OR AMEND THE FIGURE AND MAP PLAN**, then execute it.
   `kandy_pm25/docs/figure_and_map_plan_2026-09-09.md`. **Nothing in it is started.** Order:
   install `mapclassify` + `adjustText` → **seven chapter titles** → N1/N4/N6 → N2/N3/N5 →
   M3 `valley` (UTM 44N, contours, scale bar, north arrow) → M1/M2 as a pair (Robinson + Natural
   Earth) → lead-ins for the six new figures. The two proposed titles that carry the most:
   **"Eight approaches that did not work"** (a number is a claim; "What was tried and did not work"
   is a mood) and **"Validation without local ground truth"** (states the hardest problem on the
   contents page, where "Making sure it works" states nothing).
0b. **Decide what the campaign CLAIMS, now that F.103 removed its spatial justification.** The
   design stratum's founding argument — that deliberate siting recovers pattern a convenience
   network cannot — **does not survive 43 dense-network cities**. Two thin justifications remain:
   making the exposure field checkable beyond the three paired locations, and making Kandy the
   only deliberately sited city in a 48-city convenience panel (itself weakened by F.103).
   ⚠ Per F.101 the cost either way is **under 3% of the instrument budget**, so this is a
   question about **what the campaign claims, not what it costs.**
0c. **Send the CEA letter** — now both the first scientific step (F.96: local stations worth
   **4.2×** the background in Kandy's band) **and the largest cost decision** (F.101: a reference
   anchor is 10,000–40,000 USD to buy, or a letter to borrow).
0d. **Get a local quote in rupees.** Every non-instrument line in the costing carries an empty
   unit price — mounting, power, import duty, labour, servicing — because none is published for
   Sri Lanka. **Import duty is the single largest unknown.**
0e. **Circulate the paper** to the four readers — user action, unchanged.
0f. ⚠ **CLAUDE.md is 1,614 lines against its own ~900-line target.** Ten months of `## Current
   State` blocks have stacked up and several are fully absorbed into the gotchas, the ledger and
   `PROJECT.md`. **Archive them to the index table** (one row + a SESLOG date) at the next
   convenient boundary. Not urgent; it is context cost, not correctness.

### 0w. Superseded IMMEDIATE list (2026-09-06)
0. **THE THESIS NEEDS A HUMAN READ END TO END.** 34,949 words, 417 claims, gates green, two
   rounds of outside methodological review answered. Every mechanical check runs on every build;
   **none of them checks that a number is meaningful, only that it is current.** User action,
   and the critical path for the thesis.
0a. **Decide what the campaign CLAIMS, now that F.103 removed its spatial justification.** The
   design stratum's founding argument — that deliberate siting recovers pattern a convenience
   network cannot — **does not survive 43 dense-network cities**. Two thin justifications remain:
   making the exposure field checkable beyond the three paired locations, and making Kandy the
   only deliberately sited city in a 48-city convenience panel (itself weakened by F.103).
   ⚠ Per F.101 the cost either way is **under 3% of the instrument budget**, so this is a
   question about **what the campaign claims, not what it costs.**
0b. **Send the CEA letter** — now both the first scientific step (F.96: local stations worth
   **4.2×** the background in Kandy's band) **and the largest cost decision** (F.101: a reference
   anchor is 10,000–40,000 USD to buy, or a letter to borrow).
0c. **Get a local quote in rupees.** Every non-instrument line in the costing carries an empty
   unit price — mounting, power, import duty, labour, servicing — because none is published for
   Sri Lanka. **Import duty is the single largest unknown.**
0d. **Circulate the paper** to the four readers — user action, unchanged.


### 0x. Superseded IMMEDIATE list (2026-09-05)
0. **THE THESIS NEEDS A HUMAN READ END TO END.** ~~30,052 words, 302 claims.~~
0a. **Decide on the chemistry question.** ✅ **DONE 2026-09-06 (F.98)** — deepened without a CTM,
   exactly by the route named here (species-resolved testing against reanalysis already on disk).
   Outcome: one usable Fréchet bound, one registered null, one invalid test. **Chemistry is a
   supporting discipline with a measured bound, not a fourth pillar, and the thesis says so.**

### 0y. Superseded IMMEDIATE list (2026-09-04)
0. **CIRCULATE THE PAPER.** It is built, gated and numerically complete: 13,799 words, 18
   figures, 62 references, 224 claims of which 183 resolve, gates 6/6, DOCX verified. **Every
   number it contains is now generated by a script** — `docs/paper/TOKENISATION_BACKLOG.md`
   group 3 is empty. The remaining work on it is a human reading it end to end. **User action,
   and the critical path.**
0a. **Send the CEA letter.** F.96 gives the number: two local stations are worth **4.2×** a
   regional background station in Kandy's band — the reverse of the pooled advice.
0b. **Decide the venue for the paper-2 note** (`docs/paper/note_spatial_pattern_2026-09-04.md`).
   Too small for a full paper, too specific for a letter; a methods note or registered-report
   short communication fits. Three figure candidates identified.

### Retired from IMMEDIATE (done 2026-09-03/04)
~~Write the paper~~ **DONE.** ~~Figure-numbering hygiene~~ **DONE** (gapless, verified in the
DOCX). ~~Swap `turbo` off the episode scale~~ **DONE** (G5 gate). ~~OSF `nxqgb` decision~~ — it
stands, cited as run/reported/superseded. ~~Re-export the webapp payload~~ **DONE.**

### 0z. Superseded IMMEDIATE list (2026-08-23)
0. **WRITE THE PAPER.** Testing is finished. Plan `docs/paper/rewrite_plan_2026-08-22.md` (methods-primary, Kandy as demonstration), claims audit + drafted replacement passages `docs/paper/claims_audit_2026-08-22.md`, positioning `docs/paper/literature_positioning_2026-08-23.md`. **Start with §2, the formulation.** ⚠ **Do not run more tests** — the remaining candidates are low-value and each risks delay without changing a conclusion.
0b. **Decide on OSF `nxqgb`** (the first, superseded Colombo registration) — recommendation: **let it stand**, cite it as run/reported/superseded, because *why* it was superseded is itself the finding. User's call.
0c. **Two submission blockers:** figure-numbering hygiene (editors desk-reject on it, gotcha #58) and swapping **`turbo` off the episode scale** (F.83 — it is the only palette that fails the colour-vision check, and it is used on the most consequential maps).
1. **Re-export the webapp payload and commit** — already QA-passed at 0.0014 µg/m³ (tolerance 0.25), wind parity 0.0005 m/s, **not yet deployed**. `kandy_webapp/` is a separate repo. ⚠ Bump the `?v=<ts>` cache-bust; ⚠ verify the push with `git -C <path> rev-list --count origin/main..HEAD` (gotcha #77).
2. **Send the CEA letter** — with the Torrington Park BAM defunct, CEA is the **only** route to a Kandy reference monitor, and it is the one acquisition that settles both W11 and W6. University letterhead → Director General, copy DDG (Environmental Protection), then the R&D agreement.
3. **Decide what to do about `emix`** — `vehic = 0.85` is now known to misstate the mass split (F.66). Either wire `src/modular/emission.py` with a burning sector, or declare the weight as a *timing* prior in the docs. **Do not claim a skill gain from it.**



# Archived from CLAUDE.md on 2026-09-27
Source: CLAUDE.md sha256 aea0c31d1955 (full copy: CLAUDE_2026-09-27_pre-trim.md). Verbatim; line numbers are those of that copy.

<!-- CLAUDE.md lines 126-157 -->
## Current State (updated 2026-09-19b, ✍️ **THESIS A: INTRODUCTION FACT-CHECKED AND REWRITTEN · EVERY FIGURE PRINT-FITTED · SUMMARY FOR A**)

No computation. Both theses rebuilt and **compliant at 75 Arabic pages each — zero margin**; any
added body text or taller figure breaks the limit. Summary rewritten for Thesis A in the same
formal register and cut to **2 pages, 1,432 words** (linespread 0.90, parskip 0.06em; 12 pt body
unchanged), with an **Ongoing work and verification** section: spatial curve running with no
verdict, four data requests open, the campaign design under development. Commits `04685e1`, `8803346`, `3f8a42f` (local, not pushed). Narrative: SESLOG 2026-09-19.

- 🔴 **Kandy population was wrong in the thesis.** Quote **98,828 residents** in the Kandy MC
  (2012 census, `DCS2012Census`) and **nearly 389,000 weekday commuters, more than twice the
  residents** (World Bank PID PIDA28437, 2020, `WorldBank2020KMTT`). The old ">150,000 + 100,000 a
  day" came from Wickramasinghe 2011 (a PM10-PAH paper, no census basis); the abstract's "about four
  hundred thousand" had no source. ⚠ **422,314** in the burden figure is the **WorldPop count of the
  15 km domain**, not the city, and is now labelled so.
- 🟢 **Introduction fact-checked statement by statement** (88; 2 wrong, ~17 overstated) and then
  **rewritten in a formal register** (user: the weather framing read as unscientific). NWP kept as a
  cited point of reference; anecdote and rhetorical headings removed. Fragments are shared, so
  **Thesis B's Introduction changed too.** Key corrections: the Elangasinghe survey is PM10, the
  110→4 drop is garden entrance → 300 m inside, R² 0.82 is over **20** roadside sites, sites sampled
  on different days; Seneviratne "contradicts at one suburban site", not "refutes"; the mean is
  preserved **to within 0.6 %**, not exactly; Hantana 1,200–1,300 m (1,297 in the DEM).
  ⚠ **Open:** "Torrington Park BAM no longer in operation" has no citable source (user knowledge).
- 🟢 **Every figure prints at ≥ 8 pt, measured exactly** from its text objects, not by OCR
  (`printfit.fit_print` now also narrows the canvas until the SAVED tight width fits 6.02 in).
  Label collisions fixed in ~20 figures after a visual pass of all 42.
- 🔴 **Content errors the figure pass found** (no gate could): F3_2 transect drew the ">150"
  censored markers on the **four lowest** sites (flag indexed after a sort); D9 and F2 said
  "three to eight" / "+6 more" for the stations-3-to-6 rung; D9 now states the exceedance
  reversal; F7 scorecard band drawn at ±10 % against a ±15 % pass rule; F1 "kerbside"; F8
  Kathmandu cited a paper-only "Table 1".
- `postprocess.py` writes `thesis_X_new.pdf` when the PDF is open in a viewer (it used to fail).


<!-- CLAUDE.md lines 221-253 -->
## Current State (updated 2026-09-17, 🧭 **THE SENSOR-PLACEMENT PROPOSAL LEAVES THE THESIS · SPATIAL CURVE: E0–E7 SCORED, E8/E9 WAITING**)

### 🔴 USER DECISION 2026-09-17 — the Kandy measurement campaign is NOT in the final thesis
The sensor-placement / measurement-campaign proposal (**F.99–F.101**, OSF **`ad3py`**, plan
`kandy_pm25/docs/sensor_placement_plan_2026-09-05.md`) is **excluded from the final thesis because
it is still under development.** The design, costing, power analysis, registration and scripts
all **stay in the project** as ongoing work; only the thesis stops presenting it.
🟢 **REMOVED FROM THE THESIS 2026-09-17** (verified in the built `.docx`: no "network for Kandy",
no `sensor_design`, the only `ad3py` is the neutral T7_5 row).
- **§9.7 deleted** (design, site groups, power, costs, limits, Figs `network`/`networkwhy`, Table
  `T9_2` + its builder). **§9.8→9.7 "Approaches that would not help", §9.9→9.8 "The sentence to
  carry away".**
- **Relocated, not deleted:** F.103 siting experiment + `pairedtrap` → **new last subsection of
  §8.5, "Deliberate siting, tested on the dense networks"**, reframed as a panel test of whether the
  spatial null is a siting artefact (undetectable, not refuted: interval reaches +0.118). F.112
  precipitation null → **new closing subsection of §7.2, "A driver that was admitted and never
  used"**; §9.5 points to it.
- **User decisions:** `ad3py` stays in T7_5 as **"Kandy measurement design"**, cells *not reported
  in this thesis*, note says still under development (counts unchanged, eleven). §9.2's campaign
  item and T9_1's row are rewritten as a **tested result, not ranked as an acquisition**. The summary
  keeps **one sentence** of F.103. Cross-refs fixed in ch05, ch07, ch08, ch09, ch10.
- **Build:** 43,713 → **41,134 words** · 41 → **39 figures** · 10 → **9 tables** · 0 lint errors.
  Summary still **3 pages** (2,323 → 2,220 words).
- ⚠ **48 claim keys are now unused by the thesis** — every `net.*` and `cost.*` and `camp.*`
  (incl. `camp.n_heldout`). Generators in `kandy_pm25/scripts/build_claims.py` **left in place**
  (the design is ongoing work); user's call whether to retire them.

### 🔬 Spatial learning curve (details: the 2026-09-12 block's "Progress 2026-09-15")
**Still nothing to quote; no verdict computed.** E0–E7 **78/78**; E10 done; E11 not interpreted;
E8/E9 **CPU-only (D-8)**. As of 2026-09-17 the five `kandy-e89-cpu2-{r-a,r-b,s-a,s-b,s-c}` kernels
are **still ERROR at the secret read — never run from the UI**. Watcher restarted
(`spatial_curve_kaggle_watch2.py --require-live`). Gotchas **#93**, **#95**.


<!-- CLAUDE.md lines 912-944 -->
0g2. ✅ **SUPERSEDED 2026-09-25/27 by F.115/F.116** (every ladder script re-run through one frame builder; registry rewritten; the band result demoted). Kept for its history:
   🔴 **C7 NEVER REACHED THREE LATER LADDER SCRIPTS (found 2026-09-21 by the pandera guard).**
   City **3147** (South Africa, subtropical, 518 city-days) is in the pool but absent from
   `bud0_static_geo.csv`, so a left merge gave it **NaN for all 60 geography features**, and
   gradient boosting fitted it silently. Affected: `ladder_order_and_bootstrap.py` (**F.97**),
   `loss_sensitivity.py` (**F.109**), `precip_ladder_test.py` (**F.112**). `ladder_maiac.py`
   (**F.96**) filters to geo cities and is clean. `require_covers_units` was only ever wired
   into `c1_satellite_stream_ladder.py`. 3147 is not deep-tropical, so band results can only
   move through training contamination. **2026-09-23: FIXED AND RE-SCORED**
   (`restrict_to_stream_complete`, `ccef683`). Old outputs are in `modular/_backup_pre_c7fix_2026-09-23/`.
   **58 claims drift, and `claims.json` is NOT yet regenerated**, so the thesis build will refuse
   until the prose below is fixed with it. 3147 was never scored itself; it contaminated as
   TRAINING data for every other city, and that effect was not small:
   - **F.109:** RMSE inversion now **+33.3 [7.0, 50.1]**, which reproduces F.96/F.97. The thesis's
     "fragility" paragraph (the interval includes zero because of resampling detail) is **FALSE**:
     the gap was this defect. Exceedance −7.57 → **−15.9 [−38.1, −1.54]**, still excludes zero.
   - **F.97 ordering:** stations 3–6 0.13/2.81 → **0.23/2.97**. "More than twenty times" is
     **FALSE** (about 13×). The background result stays order-robust.
   - **F.112:** P1 −1.04 %, P2 paired −0.30, P3 holds, P5 16.4 → 8.6 (still halves). 🔴 **P4
     was never supported paired, even before the fix:** background minus first two, paired
     within city, **old −0.99 [−9.2, +13.8], new +0.02 [−8.6, +7.2]**. "P4 HOLDS" was a
     difference of medians (gotcha #91, fifth instance). The unpaired "35.05 vs 27.42
     would have confirmed P2" illustration disappears on corrected data (31.7 vs 31.9).
   🔴 **AND THE POOLED HEADLINE FAILS PAIRING ON THE HONEST STREAM (computed 2026-09-23).**
   Background minus first two, paired within city, `Bud0c` bottom rung:
   **GHAP +14.6 [+3.1, +27.2]** (32/46, holds) · **MAIAC +2.3 [−10.9, +21.4]** (24/46,
   **does NOT survive**; the medians 37.1 vs 23.6 are a composition effect, gotcha #91) ·
   **MAIAC deep tropics −33.3 [−50.1, −7.0]** (3/13, = F.96, robust). So *"a background series is
   the largest single gain"* holds only on the retired fused stream. What survives is the band
   result. **Not yet in the ledger or CONTEXT.md.**
   ✅ `claims.json` regenerated (566 reproduce). **User 2026-09-23: the old thesis is NOT being
   corrected; a new one will be written.** Remaining: the P4 verdict in `registrations.json`,
   the ledger, CONTEXT.md. The Paper 1 session (`D:\ProjectCD\papers\`) has been told all of this.


# Archived from CLAUDE.md on 2026-09-28
Source: CLAUDE.md sha256 e3ebb8319132 (full copy: CLAUDE_2026-09-28_pre-trim.md). Verbatim; line numbers are those of that copy.

<!-- CLAUDE.md lines 111-140 -->
## Current State (updated 2026-09-27, 🔬 **VERIFICATION PASS + LADDER v2 REDESIGN · DISCOVERY DONE · CONFIRMATION REGISTRATION AWAITS THE USER**)

User directives: re-run everything so every claim is right (2026-09-25), then *"redesign and redo
whatever is not robust or scientific enough — I want the best"*; the old thesis is frozen, a new
one will be written. Logs: `kandy_pm25/docs/verification_rerun_plan_2026-09-25.md` (defects, all
re-runs) and `kandy_pm25/docs/redesign_ladder_v2_plan_2026-09-25.md` (redesign). Ledger **F.115**
(verification) and **F.116** (redesign). `CONTEXT.md`'s ladder section and retired table rewritten.

- 🔴 **Verification (F.115):** CNEMC cities were unbanded and classed LCS in every ladder output
  (`src/modular/city_meta.py`); city 3147 still in two analyses and 2168 dropped in two others
  (ONE frame builder now, `scripts/ladder_frames.py`); silent `except: continue` everywhere
  (`src/modular/runlog.py`); four unpaired verdicts; the registry undercounted
  (**48 predictions, 26 held, 17 refuted, 5 not tested**; was 38/25/13); D-7 is 23 of 47;
  detection limits are per test (0.08–0.18, not a shared 0.130); cluster widening 1.15–2.21×.
- 🔴 **The deep-tropical inversion was one station split and one learner seed.** Over 20 splits its
  interval excludes zero in 3/20; under ladder v2 it is **−27.4 [−47.8, +11.8]** and reverses
  prospectively. **Exploratory only; "4.2×" and "robust" retired.** Cannot be confirmed with public
  data (4 fresh tropical cities).
- 🟢 **Ladder v2** (commit **`ba0da66`**, manifest `docs/ladder_v2_freeze_manifest.json`): 21 splits,
  5 learner seeds, cross-fitted shrinkage, urban-centre static geography
  (`build_static_geo_grid.py`), 18 h completeness, one driver function with the chunk fix. Parity
  with v1 to 1e-9. **Discovery (MAIAC, cluster 95 %):** first two stations **+21.8 [10.5, 52.9]**,
  stations 3–6 **+0.54 [0.21, 0.80]**, background **+34.4 [15.4, 62.2]**, no pooled ordering, no
  latitude effect.
- ⏭ **Confirmation:** 76 fresh cities, 30 countries, cap 4 (user, 2026-09-26), frozen by hash;
  predictors pulled (drivers 76/76, AOD 76/76); urban-centre geography building. Draft
  registration `kandy_pm25/docs/prereg_ladder_v2_confirmation_DRAFT_2026-09-26.md` → **USER approves
  the text → lodge on OSF → write `confirmation/REGISTERED.json` → `ladder_v2_confirm.py --ingest`,
  then `--score`**. The scorer refuses to touch confirmation PM2.5 before that file exists.


<!-- CLAUDE.md lines 141-203 -->
## Current State (updated 2026-09-19, 📚 **TWO THESES FROM ONE POOL · THESIS A BUILT AND GUIDELINE-COMPLIANT · B NEXT**)

Department guidelines (ENS4998 Final Report Format + the APS style guide it cites) arrived
2026-09-18. The old thesis measured **136 pages against a 40–75 limit**. User decisions: **rescope
into two theses** — **A, the Kandy field (the ENS4998 submission)** and **B, what an observation is
worth** — overflow to appendices **in full**, **APS numeric citations**, chapter-based figure and
table numbering. Reg. no **S/20/005**, year 2026. Plan (approved):
`kandy_pm25/docs/thesis_rescope_plan_2026-09-18.md`.

### 🟢 The machinery (build once, serves both)
- **`#writing/pool/`**: the old chapters split into **93 labelled section fragments**
  (`migrate_to_pool.py`, old number → label in `pool/labels.json`). **Edit fragments, never a thesis
  build.** `thesis/chapters/` is now LEGACY (not built); retire it after B.
- **`theses/{a,b}/thesis.md`** = composition file: headings + own prose + `{{include:pool/... shift=N}}`.
  **`assemble.py --thesis a` numbers every heading** (chapters 1–4, appendices A, B…; ≤3 numbered
  levels by construction) and resolves **`{{ref:label}}`** ("Chapter 3"/"Section 3.2"/"Appendix B")
  and **`{{this:label}}`** ("this chapter/section/appendix") per thesis. **Lint ERRORs on any typed
  "Chapter N"/"Section N.N"/"this chapter"; assemble does the same for captions.**
- **`postprocess.py`**: roman front matter → Arabic from the contents, bottom-centre numbers,
  Word TOC / List of Figures / List of Tables fields; then **Word COM** updates fields, exports PDF,
  and **measures compliance** (body 40–75 Arabic pages before Appendix A, Intro ≤40 %, Results ≥30 %,
  abstract one page). `build_docx.py --thesis a` exits 2 if non-compliant. pywin32 installed.
- `reference.docx`: guideline margins, TNR (**theme fonts overridden** — pandoc headings were sans),
  14 pt bold centred uppercase chapter titles, 11 pt headings. Symbols are italic maths and the two
  core equations display maths (`typeset_symbols.py`); ⚠ glyphs removed.

### 🟢 Thesis A — COMPLIANT (build 2026-09-19)
**72 Arabic pages before appendices** (limit 75), Intro 19 %, Results 33 %, abstract 334 words on one
page. 4 chapters + 11 appendices; 71 references. New A prose in `theses/a/`: abstract, aims and
objectives, scope, **"The reconstructed field"** (the Kandy field had NO results section before),
discussion, conclusions.

### 🔴 Defects found and fixed on the way (the gates could not see them)
- **~80 chapter-level refs** landed on only part of a split chapter → read in context and repointed
  (`repoint_refs.py`); one promised a revisit that **never existed** (Abeyratne2006) → reworded.
- **`F_episode` labelled a 55 µg/m³ line "WHO 24-h IT-1"** — WHO 2021 IT-1 is **75** (IT-2 50). Fixed.
- **Figure `scales` printed the WRONG image** (a same-named `F9_scales` of temporal variation). Built
  the intended `F8_contrast_window` in `f_chapters.py`.
- **Four typed refs in captions** bypassed the lint. **Data sources uncited**: panel archives,
  land cover, vegetation, water, GHSL; the geography sentence cited **WorldPop for a GHSL layer**.
  11 data citations added to `references.bib` (DOI-sourced where a DOI exists); `CREDITS` table
  in `visuals.py`.
- "The admissibility rule that Chapter 6 states formally" was false even in the old thesis (the rule
  is stated in the fine-tuning section and enforced in code) → reworded and repointed.

### 🟢 Thesis B — COMPLIANT (build 2026-09-19)
**73 Arabic pages before appendices**, Intro 14 %, Results 41 %, abstract 315 words on one page.
Title *MEASURING WHAT AN AIR QUALITY OBSERVATION IS WORTH: AN INFORMATION-BUDGET APPROACH FOR
CITIES WITHOUT MONITORS, DEMONSTRATED AT KANDY*. Body = panel ladder + checks + spatial nulls +
Kandy priorities; appendices = Kandy setting, Kandy field construction and checks, further checks
(estimator, confounds, siting, ten-city transfer), failed approaches, chemistry, software.
- Title page name (user, 2026-09-19): **A. M. D. W. B. Alahakoon**, both theses.
- Shared moves: A's field section → **`pool/kandy/field.md`** (label `s-kandy-field`); the siting
  subsection split out as **`pool/ch08.../05b-s-deliberate-siting-tested-dense.md`**.
- Verified both: no dangling printed refs, no raw citation keys; only framing fragments excluded
  (old aim/structure, superseded abstract; A omits the old closing statement its Discussion replaces).

### ⏭ Next
1. **Human read of both**, especially the section seams (e.g. B's "B.1 The construction that
   follows" reads oddly out of its original place).
2. ~~The summary still carries the OLD title~~ **DONE 2026-09-19b** — rewritten for Thesis A.
3. Retire `#writing/thesis/chapters/` (legacy, no longer built) — user's call.


<!-- CLAUDE.md lines 357-363 -->
### ⚠ Research audit (2026-05-29) — `docs/audit_2026-05-29.md`
Full Tier 1–3 sweep. **5 errors found, none corrupted the model** (bbox-shared features + b_FECT offset-absorption firewalled it): E1 FECT elevations (1538/1698→460/738), E2 Hantana coord (→7.265/80.625), E3 Akurana out-of-bbox, E4 "highland" narrative false, E5 Senarathna monthly coeffs May–Nov mis-transcribed (fixed → monthly r 0.73→0.83). **Verified sound:** T(t) core, b_FECT, GEOS ratio, β, KOALA 24.5, hourly+weekly coeffs, all 10 source-city coords. See gotcha #49.

📦 **Retired-stage reference archived 2026-09-21** (Stage A v1 daily XGBoost, Stage A v2.1 daily
RECAP, Stage B ConvCNP + PVAF, both supporting PINN experiments) is kept verbatim in
`docs/claude_md_archive/CLAUDE_archived_blocks.md`. Headline numbers are in `PROJECT.md`.


<!-- CLAUDE.md lines 378-382 -->
### Reanalysis prior (preprocessing inside Stage B, not a standalone stage)
- GEOS-CF PM25_RH35_GCC × per-city row-mean scaling. **Kandy ratio = 0.536** (= 24.5 / 45.7). Locked in `config.py` as `KANDY_GEOS_CF_RATIO`.
- v11 row-mean per-city ratios: Mel 0.8070, ChiMai 0.5933, KTM 0.5601, Kandy 0.536. Bogotá 0.807, MexCity 0.217 retained for reproducibility only.
- Used inside Stage B as `c_prior_scaled = c_prior × city_ratio` to form the residual target `pm25 − c_prior_scaled`.


<!-- CLAUDE.md lines 520-531 -->
**Stage B multi-city per-station data (N=5 historical, N=3 active)**
- Medellín: `data/processed/stage2/medellin_stage2_perstation.parquet` (59,138 rows, 11 stations)
- ChiangMai: `chiangmai_stage3_perstation.parquet` (87,791 rows, 8 stations)
- Kathmandu: `kathmandu_stage3_perstation.parquet` (122,046 rows, 45 stations)
- Bogotá: `bogota_stage3_perstation.parquet` (145,586 rows, 19 stations)
- Mexico City: `mexico_city_stage3_perstation.parquet` (354,651 rows, 32 stations)
- Terrain NPZs: `data/processed/pinn_inputs/{medellin,chiangmai,kathmandu,kandy,bogota,mexico_city}_terrain_tpi_svf_100m.npz`
- **v13 per-station parquets (canonical)**: `data/processed/stage2/{kathmandu,chiangmai,medellin}_perstation_v13.parquet` + `v13_city_constants.json`
- Wide-footprint road kernels: `{city}_road_kernel_stations_100m.npz`; wide terrain `{city}_terrain_stations.npz`; VIIRS NTL `{city}_viirs_ntl_stations.npz`
- **Kandy zero-shot pipeline (2026-05-23)**: `scripts/kandy_zero_shot_inference.py` · `conformal_calibrate_v14.py` · `kandy_heatmaps.py`; predictions `data/processed/kandy_zero_shot/kandy_predictions_20240101_0000_n8784.parquet`; figures `results/figures/kandy_zero_shot/`
- Builders: `rebuild_perstation_extended.py --version v11` · `build_road_kernel_for_city.py --city` (needs User-Agent, gotcha #41) · `build_station_road_kernels.py` · `add_road_density_to_perstation.py --version v12` · `gee_export_source_cities.py` · `gee_export_source_city_terrain.py` · `merge_source_city_gee_met.py` · `download_gee_drive_outputs.py`


<!-- CLAUDE.md lines 580-580 -->
13. **Kaggle PINN inference**: ALWAYS on Kaggle. NEVER run FourierPINNV3 inference locally.

<!-- CLAUDE.md lines 581-581 -->
14. **blh_norm = BLH_m / 2000.0** everywhere. `t_norm = h/24` (hour-of-day, NOT training fraction).

<!-- CLAUDE.md lines 582-582 -->
15. **grid_sampler_2d_backward**: not differentiable for 2nd-order autograd. All `_interp_grid` outputs must be `.detach()`-ed before PDE residual calls.

<!-- CLAUDE.md lines 584-584 -->
17. **MERRA-2 as label rejected**: r(CAMS,MERRA-2)=0.177 over Kandy. Use ONLY as validation diagnostic.

<!-- CLAUDE.md lines 585-585 -->
18. **FourierPINN v2 backbone incompatible with FourierPINNV3**: 0 keys transfer. Do not attempt to load.

<!-- CLAUDE.md lines 588-588 -->
21. **SVF is near-uniform across all cities** (~0.977–0.984): ridges are 5-10 km away, beyond the 2 km scan radius. **Drop SVF from SharedTerrainAnsatz** — use delta_z alone for F_valley. Do not re-add SVF.

<!-- CLAUDE.md lines 589-589 -->
22. **CityConfig _REPO path**: `_REPO = Path(__file__).parents[3]` → resolves to `kandy_pm25/`. NOT parents[4]. File is at `src/stage3_pinn/data/city_config.py`.

<!-- CLAUDE.md lines 591-591 -->
24. **Kathmandu GD Labs network**: dense 52-station network went live Oct 2025 only. Training window = Oct 2025–May 2026 (8 months). Covers post-monsoon + winter + pre-monsoon — sufficient for trapping-season physics.

<!-- CLAUDE.md lines 594-594 -->
27. **Medellin GEOS-CF gap**: station data Aug 2018–Aug 2019, but GEOS-CF only from Jan 2019. Filter Medellin to Jan 2019 onwards in any kernel using c_prior. Loses 34% of rows.

<!-- CLAUDE.md lines 595-595 -->
28. **CorrectionNet inputs = physics features, NO (lat, lon)**: (sin_h, cos_h, sin_doy, cos_doy, blh_norm, delta_z_norm). lat/lon enable station memorisation → LOOCV collapses. blh_norm+delta_z_norm are OK because they're physics features, not location identifiers.

<!-- CLAUDE.md lines 596-596 -->
29. **c_prior (GEOS-CF) systematically overestimates all cities**: Mel ×0.82, ChiMai ×0.53, KTM ×0.79. Formula `F_eff = 1 + positive` can only scale UP — degenerates when c_prior > city_mean. **Always scale c_prior before ansatz**: `c_prior_scaled = c_prior × (station_mean / c_prior_mean)`.

<!-- CLAUDE.md lines 600-600 -->
33. **Bogotá GEOS-CF city_ratio = 0.807** (16.5/20.4). **Mexico City ratio = 0.217** (21.2/97.4). Hardcoded in `GEOS_CITY_MEANS`/`STATION_CITY_MEANS`. MexCity 0.217 is real.

<!-- CLAUDE.md lines 606-606 -->
39. **c_prior ratio MUST be row-mean, not timestamp-mean**: timestamp-mean weights every hour equally regardless of station count; for cities with growing station counts (KTM 9× growth) this drifts the ratio ~12% and inflates c_prior_scaled ~5 µg/m³. Use row-mean. v11: Mel 0.8070, ChiMai 0.5933, KTM **0.5601**.

<!-- CLAUDE.md lines 607-607 -->
40. **deepsensor 0.4.2 has NO Student-t likelihood** as a config knob. Keep `het` likelihood but replace the Gaussian NLL with `-StudentT(df=5, loc=μ, scale=σ).log_prob(y).mean()`.

<!-- CLAUDE.md lines 609-609 -->
42. **ConvCNP terrain bbox does NOT constrain station inclusion**: stations outside the terrain raster still train via per-station context. Wider rasters improve encoder coverage but are NOT required.

<!-- CLAUDE.md lines 610-610 -->
43. **Road density must be sampled from a station-footprint kernel**, not the 15×15 km PINN grid — most stations fall outside it → road_density=0 by default. Use `{city}_road_kernel_stations_100m.npz`.


# Archived from CLAUDE.md on 2026-09-29
Pending item 0a (spatial learning curve), superseded by its scoring (F.119). Verbatim.

0a. **CONTINUE AND FINISH THE SPATIAL LEARNING CURVE** — everything is built and gated; what
   remains is scoring and writing. In order:
   1. ~~licence, weights, E0–E7 scoring, E10 kernels~~ **DONE 2026-09-13/15** (78/78 cities; E10 952,068 preds);
   2. **USER: start the five `kandy-e89-cpu2-*` kernels** — tick `TABPFN_TOKEN` in each editor,
      accelerator None, Save & Run All (D-8: E8/E9 are CPU-only). ✅ **2026-09-23: the 14-second
      crash is fixed and version 3 is pushed to all five** (gotcha #93f). Their current ERROR is the
      expected missing secret after the push. 🔴 **2026-09-24: THAT RUN PRODUCED NOTHING**
      (gotcha #93g: tabpfn 9.0.0, 0 finite rows). **Version 5 is pushed to all five** with 8.5.0
      pinned, the canary and the all-NaN refusal. **USER: tick TABPFN_TOKEN, accelerator None,
      Save & Run All, again.** ⚠ r-b's shards g4 and g7 hit the **12 h wall** last time. Outputs
      survive a timeout, so cities left unfinished need a second, targeted wave. Real 8.5.0 speed
      on Kaggle is not yet measured (3.5 s per task locally).
      🟢 **2026-09-25: VERSION 5 WORKS, BUT WAVE 1 IS PARTIAL.** Canary OK and every row finite.
      Six shards hit the 12 h wall (Kaggle speed is about **6 s per task**, not 3.5). Outputs are in
      `shard_out/kandy-e89-cpu2-*`; the all-NaN run is in `shard_out/_archive_v3_allnan_tabpfn900_2026-09-23/`.
      **Complete: registered 28/37, S-1 36/41.** Remaining **14 cities, about 12,600 tasks**:
      registered 24, 10, 32, 47, 66, 140, 156 (107 and 115 have NO splits, so nothing to score);
      S-1 13, 24, 37, 48, 156.
      **WAVE 2 STARTED 2026-09-28 (was postponed 2026-09-25).** Steps as run:
      (1) `kaggle datasets create -p <abs>/spatial_curve/kaggle/tabpfn_cpu_wave1_dataset` (34 flat
      `_cpu_` files, 981 KB, metadata present). The first attempt uploaded every file but **never
      created the dataset**, so check the published listing afterwards; (2) push
      `kaggle/tabpfn_cpu_w2-reg` and `tabpfn_cpu_w2-s70` (new slugs `kandy-e89-cpu3-{reg,s70}`,
      generated with `make_tabpfn_cpu_kernels.py --wave 2`, resume dataset attached, outputs tagged
      `_cpu_w2_`); (3) USER ticks the secret, sets accelerator None, runs. The heaviest shard is
      about 4,200 tasks (~7 h). Resume was verified locally on the real files: each shard skips its
      64 complete city-frames. Then consolidate all 7 kernel folders with
      `--cities .../data_dataset/cities.parquet --splits-dir .../data_dataset`, and run
      `spatial_curve_run_summary.py --preflight`.
      🔴 **2026-09-25: CPU scoring is NOT reproducible ACROSS MACHINES.** 80 wave-1 tasks re-scored
      on the laptop (same code, data, tabpfn 8.5.0 and seed) matched Kaggle's values in **1/80**,
      median |Δρ| 0.012, max 0.29. D-8's "48/48 identical" was within ONE machine. Amendment 3's
      justification "reproducibility on any machine" is therefore **overstated**: disclose it in
      Paper 1's methods and the ledger. The cause (PyTorch build or CPU instruction set) is not
      isolated. **Decision: wave 2 runs on Kaggle, the same environment as wave 1, so no city mixes
      machines.**
      🟢 **Amendment 3 (D-8) REGISTERED 2026-09-28 as OSF `4qs9c`** (project `79qkw`). The 09-23 POST
      never created a registration (the draft stayed a draft). It was re-submitted from the same draft
      with a dated §5 disclosing wave 1, the tabpfn-9.0.0 void run and the cross-machine 1/80 result,
      and correcting "reproducible on any machine". Pending approval: **verify it is listed after
      48 h** (a pending registration vanished once).
      🟢 **WAVE 2 RUNNING on Kaggle (user, 2026-09-28).**
   3. download E8/E9 outputs → `scripts/spatial_curve_tabpfn_consolidate.py` (one source per city);
   4. summary run on Kaggle CPU: all 78 city pickles (`kandy-spatial-city-cache`) + E10 preds +
      ONLY the consolidated E8/E9 file (`merge_deep` reads `pred_*` only);
   5. decide whether to lodge **D-8** on OSF as an amendment (user's call);
   6. run **X-T**, the exploratory terrain moderator (`spatial_curve_moderators.py`);
   7. **write it up**: new Chapter 8 section, §7.2 scope statement, §9.7, abstract, summary,
      Appendix B. ✅ The registrations table already reads `registrations.json` (2026-09-14):
      scoring the curve means setting `held`/`refuted` on `rqn4y`/`26hp8` there and nothing else.
   8. **fix the `excludes_zero` flag in the loss-sensitivity script** (wrong-sided for negative
      intervals) before any loss figure or claim reads it again.
   ⚠ **E11 is not interpreted** whatever its real-data numbers look like (control failed; the
   failure is the model on the registered task, not the code).


# Archived from CLAUDE.md on 2026-10-05
Source: CLAUDE.md sha256 d00725e4d809 (full copy: CLAUDE_2026-10-05_pre-trim.md). Verbatim; line numbers are those of that copy.

<!-- CLAUDE.md lines 130-188 -->
## Current State (updated 2026-09-12, 🔬 **THE SPATIAL LEARNING CURVE IS UNDERWAY — DATA BUILT, GATES PASSED, NOTHING SCORED**)

The test the user asked for after questioning what the ladder measures: **how much spatial skill
each additional sensor inside a city buys.** Registered **OSF [`rqn4y`](https://osf.io/rqn4y/)**
+ amendment 1 **[`26hp8`](https://osf.io/26hp8/)** (deep arms) + amendment 2
**[`4whsc`](https://osf.io/4whsc/)** (terrain moderator, D-6, D-7; lodged 2026-09-11 13:36 UTC,
before any real scoring). Plan `kandy_pm25/docs/spatial_learning_curve_plan_2026-09-11.md`.

🟢 **SCORED ONCE 2026-09-28 (F.119, `docs/spatial_curve_results_2026-09-28.md`):** 7 held, 3 refuted (X1, X6, X10),
1 not testable (X12, E11). Cities split (11/18 cross the raster; 7 never); reach ~1 km; siting irrelevant.
The block below is the pre-scoring history.

### What exists
- **Frame frozen by the registered rule (D3).** 18 primary cities, 745 sites, 7 countries
  (13 temperate, 4 subtropical, 1 tropical); 15 secondary; band arm 6. Stop rule passed (18 ≥ 10).
  Sensitivity frame S-1 (70 % coverage) frozen beside it.
- **Ingest complete**: 1,974 reference locations, 0 failed objects. **Predictors complete (D4)**:
  1,141 sites, no missing values; 41 benchmark grids, 69,595 cells, no NaN.
- **Terrain descriptors** for all 41 cities (`spatial_curve_terrain.py`): primary-frame relief
  37–552 m, slope 1.7–12.9°, 4 cities enclosed on ≥ 4 of 8 rays, 8 on none.
  ⚠ **3 of the 4 enclosed cities are Korean** — terrain is partly aliased with network.
- **Gates green**: synthetic positive control PASS (E3 0.540 vs oracle 0.554 at k=35); leakage
  self-test PASS after D-7.

### 🔴 Two corrections and one failure, all declared before scoring
- **D-6 — roads now from Geofabrik extracts, not live Overpass.** Overpass queued ~20 min/city
  (13–16 h for the frame). 37 extracts, 9.05 GB, every file MD5-verified; minimum-cover set chosen
  by polygon containment. **Cross-check on the two cities Overpass had finished: identical,
  Spearman 1.000, zero difference.**
- **D-7 — the leakage self-test was wrong, not the guard.** It failed at 2.03 because it compared
  each instrument's mean over **its own** days and skipped the freeze's QC; 23 of 47 merged pairs (recounted 2026-09-25; the lodged text says 22)
  are **replaced instruments, not concurrent twins**. Corrected → **PASS at 0.080** (0.699 without
  the twin). ⚠ Margin under the 0.1 threshold is modest.
- **🔴 E11 (TNP-D) FAILED its registered positive control** — three seeds at −0.027 / −0.104 /
  −0.006 against oracle 0.635, training NLL pinned at the no-information value for 40k steps.
  **Checked for a code defect first**: attention mask, target isolation and context path all
  correct, and the same code learns a random plane (1.000) and a smooth field (0.974).
  **The registered verdict stands: E11's real-data results are not interpreted.**
- 🟢 **E10 (ConvGNP) PASSED all three primary seeds** — 0.610 / 0.599 / 0.604 vs oracle 0.635,
  7.44 s/step on T4, step budget set by the registered timing rule.

### 🔄 Progress 2026-09-15 — E0–E7 SCORED, E8/E9 RE-SCORING ON CPU, NO VERDICT COMPUTED
🔴 **Still nothing to quote.** Scoring is complete for part of the design; no summary or verdict
exists, and none may be written before every arm is merged.
- **E0–E7: 78/78 city results** (37 registered + 41 S-1), every pickle parsed, in
  `spatial_curve/city_cache_salvage/` and Kaggle dataset `kandy-spatial-city-cache`.
- **E10** done (952,068 predictions). **E11** control failed → not interpreted.
- **E8/E9 → D-8 (declared 2026-09-15): CPU ONLY.** TabPFN's default `inference_precision="auto"`
  uses autocast on CUDA, float32 on CPU: 48 GPU values re-scored on CPU matched **8/48**, median
  |Δρ| **0.073**, max 0.376; CPU vs itself **48/48 identical**. The 27 GPU-scored cities are
  archived, NOT merged. Five CPU kernels `kandy-e89-cpu2-{r-a,r-b,s-a,s-b,s-c}` await
  **TABPFN_TOKEN ticked in each editor + Save & Run All (accelerator None)**.
- **Before the summary:** run `spatial_curve_tabpfn_consolidate.py` on the CPU outputs (merge_deep
  reads only `pred_*`; resumed sessions leave `partial_*`) and give the summary run ONLY the
  consolidated file. Then X-T, then write-up.
- Fixes that made this possible: gotchas **#93** and **#95** (Kaggle secrets/subdirs/accelerator;
  mgwr loky segfault → `n_jobs=1`, bit-identical; pinned dataset versions; `--only-clusters`).
- Is D-8 to be lodged on OSF as an amendment? **User's call — not done.**



# Archived from CLAUDE.md on 2026-10-06
Source: CLAUDE.md sha256 59472372d54f (full copy: CLAUDE_2026-10-06_pre-trim.md). Verbatim; line numbers are those of that copy.

<!-- CLAUDE.md lines 125-158 -->
## Current State (updated 2026-10-05, 🟢 **CONFIRMED; ROBUST TO BASELINE, LEARNER AND STATION CAP; SPATIAL CURVE RE-RUN ON FULL RECORDS**)

Four registered tests scored ONCE each, 2026-09-28/29, every one behind a parity or preflight gate.
Records in `kandy_pm25/docs/`: `confirmation_results_2026-09-28.md`, `rich_baseline_results_2026-09-28.md`,
`spatial_curve_results_2026-09-28.md`, `learner_robustness_results_2026-09-29.md`. Ledger **F.117–F.120**.

- 🟢 **Confirmation (OSF `ueyfr`, F.117)**: 72 fresh cities. H1 first two **+8.5 % [3.1, 25.1]** (discovery
  +21.8 retired) · H2 stations 3–6 **+0.22** · H3 background **+41.1** · H4 **+24.6 [4.1, 47.8]** background >
  first two · H5 exceedances **+59.3** · M1 latitude **undetectable**. Deviation E-1 (parallel ingest) only.
- 🟢 **Richer baseline (OSF `b379r`, F.118)**: + CAMS NRT PM2.5, terrain (ocean-masked), FIRMS, TROPOMI NO2,
  IMERG, day of week → Bud0 **+13.1 %**; 6/7 as registered; **R3 refuted** (first-station gain did not shrink).
- 🟢 **Learners (OSF `jea58`, F.120)**: TabPFN / 14-day GRU / HGB+physics → **all 12 directional verdicts
  held**; none beats HGB (TabPFN −11 %); H4 ordering unresolved under TabPFN's weaker baseline.
- 🔬 **Spatial learning curve (`rqn4y`+`26hp8`, F.119)**: 7 held, 3 refuted (X1, X6, X10), 1 not testable
  (X12). Cities split (11/18 cross the raster, 7 never); reach ~1 km; siting irrelevant; **no Kandy station
  count follows**.
- Registry: **17 entries (incl. amendments); 105 predictions over 14 run: 66 held, 23 refuted, 6 not tested, 10 two-sided/exploratory**
  (A: 4 held + 2 two-sided; B: 6 held, X4 refuted). `ueyfr`, `4qs9c`, `b379r`, `jea58`, `mhgna`, `fu59b` pending OSF approval (gotcha #100).
- 🔴 **Design audit (F.121, 2026-10-04)**: the OpenAQ 12-station/2-year cap and the spatial curve's one-year window shaped
  results. **User approved redoing both** as registered tests **A** (full-network ladder) and **B** (spatial curve on full
  records). 🟢 **LODGED 2026-10-04: A = OSF `mhgna` (project `87znu`), B = OSF `fu59b` (project `4xvpw`)**, freeze `1e5f712`
  (`docs/{fullnet,curve_fullrecord}_freeze_manifest.json`). Dry runs before lodging: A parity 72/72 vs ueyfr (2.8e-14);
  B freeze byte-identical, leakage 0.0798; retrieval engine exact on in-cap data. Scripts `openaq_archive.py` (shared
  unit cache, `--fetch ab`), `ladder_v2_fullnet.py` (`--build/--mirror/--score/--endpoints`), `spatial_curve_fullrecord.py`
  (`--assemble/--freeze/--frame/--cover/--extracts/--predictors/--analysis`). Retrieval started 2026-10-05 00:05
  — complete (3.26 M objects, 0 errors). 🟢 **Both scored 2026-10-05:** A (F.122) all verdicts hold on
  full networks (background − first two +32.0 [11.6, 50.5]); B (F.123) 23 primary cities incl. Bangkok, X4 refuted, tropical arm inside
  the temperate envelope. Records `docs/{full_network_ladder,spatial_curve_full_record}_results_2026-10-05.md`.
  Large retrievals run in a scheduled window via `scripts/night_window.sh`; operating details are kept local (memory
  `reference-slt-fibre-network`). **Manuscripts and registrations state design choices and their consequences, never
  infrastructure** (user rule).
- 🧭 **Supervisor (2026-10-04)**: method part first; he handles Kandy institutional data; sensor proposal waits; meet
  Dr. Mahasen Dehideniya; review paper (topic open).
- ⏭ Paper 1 draft updated (§2.12, §3.1.5–3.1.6, §3.6; commit `760abad`); evidence map still to update.
