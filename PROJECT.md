# Kandy PM2.5 — Project State

**Researcher:** Daminda Alahakoon, BSc (Hons) Environmental Sciences, University of Peradeniya
**Supervisors:** Dr. U. Ranatunga (main), Dr. M. Dehideniya (co)
**Last updated:** 2026-08-10

This is the current-state map of the project. Architecture and code organisation live in
`PROJECT_ARCHITECTURE.md`; session history in `memory/SESLOG.md`; operating rules and the
live task list in `CLAUDE.md` (single source of truth for current state). Numbers are not
restated across files — where a figure matters, this doc points to where it is produced.

---

## 0. Research question

Can a city with **no public, retrievable PM2.5 monitor** be given a credible, uncertainty-
quantified, fine-resolution (1 km hourly) PM2.5 field — and can that field be *verified*
despite the absence of local ground truth? Target: **Kandy, Sri Lanka** (enclosed
central-highland valley, ~0.4 M people, no public monitor).

## 1. What the project is now

The deliverable is an **additive background-and-increment decomposition model** for Kandy,
plus a **transfer-validation** method that establishes its credibility on the held-out
networks of monitored analogue cities ("borrowed ground truth"). The flagship output is a
preprint. Everything else (Stage A/B, PINN, ConvCNP, PVAF) is now supporting or historical
context that led here.

- **Production model:** `PM(x,y,t) = B(t) + max(T(t)−B(t),0)·P_local(x,y,t) + min(T(t)−B(t),0)`
  — regional background plus a locally structured, unit-mean increment. The local pattern
  structures only the accumulation above background; ventilation below background (deep midday
  mixing) is applied uniformly so the field goes flat, never inverting the core-vs-periphery
  ordering (2026-07-10 increment-split fix). Basin mean ≡ T(t) (the T-lock invariant) holds
  exactly. Component detail in `PROJECT_ARCHITECTURE.md §2`.
- **Validation:** the identical model is run for monitored analogue cities under a two-sensor
  information budget that emulates Kandy's data poverty, then scored against each city's
  held-out network. **N=10 cities, 5 countries, 2 continents** (Asia + South America).
- **Deliverable:** `kandy_pm25/docs/reports/preprint_kandy.{md,pdf}` (**30 pp**) — see §4.

## 2. Headline results (where produced)

| Claim | Result | Produced by |
|---|---|---|
| Temporal transfer (seasonal) | $r$ 0.94–1.00 across **10** cities | `scripts/city_validation_scorecard.py` |
| Temporal transfer (diurnal) | $r$ 0.60–0.98 (**9 of 10**) | ″ |
| Level transfer (2-sensor anchored) | $-4\%$ to $+30\%$ | ″ |
| Fine within-city spatial rank is significant above each city's own permutation null in 6 of 9 estimable cities (0.43-0.83), on a corrected estimator that cannot launder temporal skill (F.32-F.34).py` |
| Kathmandu full-machinery showcase | 0.97 / 0.97 / −0.1% / ρ 0.39 (39 held-out) | `data/processed/decomp_kathmandu/` |
| Robustness — sensitivity | deaths 421–425 invariant to f∈[0.15,0.35] & ±20% background | `scripts/sensitivity_analysis.py` (S1) |
| Robustness — ablation | temporal anchor-driven; additive vs multiplicative +26% level | `scripts/ablation_scorecard.py` (S2) |
| Independent corroboration | airport visibility r=−0.46 (n=364); literature seasonal cycle | `scripts/independent_visibility.py` (S3) |
| Sensorless temporal anchor (**DAILY only**) | LOCO 97% beat baseline, seasonal r 0.95 | GeoAQ-Zero Track T-a |
| Ventilated-hour floor (additive_v3) | **Medellín-VALIDATED**: holdout-6 flat-hour RMSE 8.53→8.00 | `scripts/score_additive_v3.py` |
| Spatial ceiling — 5th independent null | EO foundation embeddings add **no** signal beyond physics (3 cities, partial ρ≈0) | `scripts/alphaearth_spatial_test.py` |
| **Spatial ceiling — MEASURED, 47 cities** | **ρ ≈ 0.2–0.28**, unmoved by four surfaces AND by a full LUR predictor set incl. roads (+0.273→+0.275) | `scripts/{spatial_proxy_scan,lur_fit}.py` (F.56/F.58/F.59/F.61) |
| **Budget ladder — level axis, RE-VALIDATED 2026-08-23** | 47 cities, 4 bands, 32 countries. ⚠ The 2026-08-19 gains are **retired**: the scored `Bud0` used one of three admitted streams (F.84). Bottom rung now decomposed — **static geo 10.8%, satellite level 7.6%**; then **+2 stn 17.9%, +6 stn 0.1%, +background 40.6%** | `scripts/{revalidate_ladder,build_bud0_streams}.py` (F.84–F.85) |
| **Ladder robustness** | Robust across **non-linear** estimators (spread 2.5 pp); a linear baseline **collapses** on the 68-feature `Bud0c` — F.81 refuted. `Bud1→Bud2`≈0 holds under every learner | `scripts/learner_sensitivity_bud0c.py` (F.88) |
| **Spatial amplitude — at matched support** | Model annual p90/p10 **1.232** vs observed **1.26–1.47**; the apparent 85× vs 1.23× gap was a change-of-support artefact. Paired microsites 300 m apart in one pixel: **27.5× observed vs 1.000× modelled** | `scripts/{elangasinghe_spatial_test,support_collapse_test,fit_s_exp}.py` (F.69/F.76/F.77) |
| **P4 identifiability — RUN** | `kappa`, `eps0`, `w_evening` unidentifiable at Kandy's budget; **`s_exp` is the only identifiable parameter and had never been fitted** (fitted → non-transferable, held at 1.0) | `scripts/{p4_identifiability,fit_s_exp}.py` (F.75/F.77) |
| **Background gain is REAL** | independent network at a median 89 km recovers **73%** of it on the corrected `Bud0c` rung (was 75%/79% pre-F.84). ⚠ **Bounds the same-network artefact from above, does not measure it**: 84% at 62 km vs 57% at 152 km. ⚠ Kandy's own band recovers only **37%** at 221 km, n=4 | `scripts/independent_background_revalidated.py` (F.54 re-run 2026-09-05) |
| **The ladder is PATH-DEPENDENT** | a "background first" rung is **impossible by construction** (its coefficient is fitted against local stations). Permuted: background 40.6→38.0% (robust), monitors 3–6 **0.13→2.81%** (21×, still small). Same information set, **different skill** (0.106 µg/m³) | `scripts/ladder_order_and_bootstrap.py` (F.97) |
| **Uncertainty over CITIES** | first two **17.9% [4.6, 23.5]** · monitors 3–6 **0.1% [0.0, 0.9]** · background **40.6% [26.7, 45.2]**. 🟢 **The tightest result is the null** | same (F.97) |
| 🔴 **The first rung's SIZE was Kandy's budget, not a measured optimum** | `SENSOR_PAIR` = *"<= 2 local low-cost sensors (the Kandy budget)"*. **One station buys 17.02% [4.57, 21.83]; the second adds 0.01 pp** paired, and no count 2–8 beats one by more than 0.15 pp. **Saturation is at ONE.** Deep tropical agrees (+0.22 pp [0.00, +2.90], 6/13) ⚠ but both bands are underpowered rather than null. 🔴 The second rung is `pool[:6]`, i.e. stations **3–6**, written "three to eight" in nine places with **opposite signs** (+0.75 vs −0.49 pp) | `scripts/station_count_curve.py` (F.102) |
| 🔴 **Deliberate siting does NOT beat convenience siting** | 43 dense-network cities, 601 stations, each made into both designs from its own stations: **paired −0.044 [−0.095, +0.118]**, winning 19/43. ⚠ The difference of medians (+0.114) points the OTHER way. ⚠ The fixed-holdout re-check is uninformative on this panel (median held-out = 4, Spearman quantised to 0.1) | `scripts/siting_experiment.py` (F.103) |
| 🔴 **The tropical inversion depends on the satellite stream** | paired over cities, n=13: raw MAIAC **+33.3 pp [+7.0, +50.1]**, 77% of cities; fused GHAP **+3.6 pp [−14.3, +36.3]**, 54% — **a coin flip**. **F.92 alone did not support the recommendation; quote F.96/MAIAC** | same (F.97) |
| **Diurnal transfer** | works in the **deep tropics** (+25.8% vs flat, r 0.63, ~1 h phase); pooled 5.5% **worse** than flat | `scripts/diurnal_transfer_test.py` (F.55) |
| **Kandy product** | basin **21.0** µg/m³, pop-weighted **23.0** (uplift **+9%**); local share **0.483** (⚠ a constrained decomposition, **not** source apportionment; honest range 0.482–0.547); **431 deaths/yr**, response-function-conditional interval **[237–632]**, 300 avoidable. ⚠ The interval carries ONLY the CRF uncertainty | additive_v3 field + `health_burden.py`, regenerated 2026-09-04 |

⚠ **The 25/75 split is a PRIOR and is now REFUTED by five independent lines (2026-08-06, ledger
F.17–F.22).** A within-day-flat background cannot exceed the day's minimum total, which puts a hard
floor of **f ≥ 0.410** under the local share using only the shipped T(t); the shipped 0.244 sits
below that floor in **9 of 12 months**, so B > T in 28.5% of hours and the field renders spatially
uniform there. Five lines now converge on **f ≈ 0.35–0.45**:

| line | value | independent of the others? |
|---|---|---|
| coherence floor (shipped anchor alone) | 0.410 | yes |
| NBRO island network, wet season | 0.446 | yes, an instrument |
| hierarchical SBI de-attenuation (Kandy held out of the fit) | 0.392 [0.258, 0.525] | yes |
| **holiday natural experiments** (Poya / fixed holidays) | 0.24–0.52 | **yes — measures local activity directly** |
| literature bracket | [0.15, 0.50] | soft |

The SBI inference is **attenuated by ρ = 0.426 ± 0.066**, estimated from three cities, which is why
it looked low wherever it could be checked — the project's informal bias argument, now quantified.

**f has NOT been changed in the shipped model.** Five background reformulations were built and all
rejected: an independent background, pointwise coherence, an f inside the literature bracket and the
W2 seasonal shape are **four constraints on three degrees of freedom**. The limitation is surfaced
in the app instead. **T-locked quantities — basin means, exposure, burden — are unaffected**, because
the basin mean equals T(t) whatever B is. Resolution needs one in-basin or upwind monitor.

**Weak-point register (opened 2026-08-06).** Six items closed by measurement, three open. Closed:
the shipped interval's coverage (width correct at 91.5% once the area-vs-point centring offset is
removed; raw 72.4%); the anchor-choice concern (the extremal pair *penalises* level and RMSE, and
flatters seasonal r by ~+0.01); the never-verified data survey; the KOALA anchor's significant
figures; the ~90% vehicular assumption (**corroborated** — the holiday effect is 3.67x stronger at
rush hours); and the f prior (**refuted**, five converging lines). Open: the FECT calibration itself
is unvalidated; the eps-floor is transferred from a single city; and e(t)'s evening lobe is
misplaced (observed peak 20:00, e(t) says 18:00) -- the only open item that would change a shipped
number. Detail in `CLAUDE.md` section 2b and ledger F.20-F.25.

**Standing prediction, registered before the data exists (F.25).** Any future point measurement at
Kandy -- the CEA archive, NBRO "Kandy 1", a mobile campaign -- will show the model **about 40% high**
on a naive comparison. That is the expected area-versus-point offset of **+5 to +6 ug/m3** and must
be removed before any bias or coverage statement; an offset far outside that range would indicate a
genuine level error.

**Applicability-map ordering (spatial ρ, N=10) — RESTATED 2026-08-07 on a corrected
estimator (F.32–F.34).** The previous ordering was computed on per-station annual means
averaged over *different* hour sets for model and observations, a convention that shifts the
answer by up to 0.88 in either direction. The column now removes each hour's network mean
from both series before any station mean is taken, so the temporal anchor's skill cannot
enter a spatial number, and each city is tested against its **own** permutation null:

Baoji **0.83** > Bogotá **0.80** > Xichang **0.78** > Tai'an **0.72** > Medellín **0.66**
(all *p* < 0.05) > Yichang 0.60 (*p* 0.08) > Bazhong 0.54 (*p* 0.31) > Kathmandu **0.43**
(*p* 0.007) > Chiang Mai 0.22 (*p* 0.51) > Chandigarh NOT ESTIMABLE (n_ρ = 2).

**6 of 9 estimable cities are significant**, against 4 clearing the old 0.40 gate. Validated
against an independent pairwise-concordance estimator (agreement 0.002, sign 9/9) and
uncorrelated with network size (r = −0.18). The qualitative claim is **unchanged: partial and
regime-bounded** — but it now rests on a statistic that survives its own validity checks, and
**Kandy's two closest analogues are the panel's weakest** (Chiang Mai not significant,
Kathmandu lowest of the six), which is the line the transfer argument depends on.
Spatial skill remains information-limited — now **eight** independent lines, and the ceiling is
**measured rather than inferred**: ρ ≈ 0.2–0.28 survived a full land-use-regression predictor set
(roads at 50–1000 m, NDVI, tree cover, water, land cover, built volume; 636 stations, 47 cities).
⚠ **`Bud4` is unsupported**: a local spatial network does not make the pattern estimable —
interpolation between a city's own stations is worse than assuming uniformity (F.60–F.62).

Bogotá is the decisive case: a **flat** city (Δz 11 m at the
core) reaching ρ 0.67 on a 30× traffic gradient locates the spatial signal in the **emission
pattern, not relief**, where a valley confounds the two. Temporal and level are the validated
claims; the partition is identified annually only (see above).

## 2b. The spatial rung, tested under pre-registration (2026-09-04, OSF `2jyfg`)

§5 of the manuscript declares the spatial rung a **design assumption** rather than a validated
one. That assumption was tested. It held.

| | value |
|---|---:|
| best single globally available predictor (built-up land cover, 2.4 km) | **ρ = 0.309** |
| minimum detectable paired improvement, 80 % power, 46 cities / 630 stations | **0.130** |
| registered bar | **ρ ≥ 0.44** |
| learned pattern achieved (random forest; MLP 0.236, ridge 0.221) | **0.286** |
| median paired delta against the benchmark | **+0.022** (25/46, *p* = 0.94) |

**L1 held — the bar is not cleared**, and per the registration this is reported as *undetectable
at this power*, not as a modest success. L2 (beats the dispersed field, 0.274), L3 (conservation
to 3.3e-16) and L4 (lower outside temperate) held; L5 held by the letter only and is reported as
uninformative.

**This is the sixth null on within-city spatial pattern and the first with a detection limit
stated in advance.** The previous five could only have detected effects of 0.65–0.96. The claim
it licenses is bounded: *on 46 cities and 630 stations, a learned within-city pattern does not
beat the best single globally available predictor by more than 0.13 in rank correlation.*

**Two results survive the null.**

🟢 **Conservation is exact and survives abuse.** `P = N·softmax` over cells holds to 3.3e-16
across saturated, overflow-range and dead-constant logit fields; the field's spatial mean returns
the anchor to 7e-15 and a ventilated hour renders exactly flat. A learned pattern can misplace
material; it cannot create it. We argue in the note that this — not the learning — is what a
model of this kind should be judged on.

🟢 **Skill rises with buffer radius and peaks at 2.4 km**, coarser than the 1 km reporting cell.
Read with the sub-grid result (within-cell 1.218 > between-cell 1.049), the usable band is
bracketed from both sides.

⚠ **Withdrawn:** "night lights is the best spatial proxy at ρ ≈ 0.34" was an eight-city figure;
on 46 cities night lights reaches 0.197. ⚠ **Not established:** the band difference is real
(temperate +0.457 vs +0.225, *p* = 0.006) but its mechanism is not, and the de-confounding test
was not pre-registered. ⚠ **No engineered emission surface beats a single free raster** — not
congestion-weighted road centrality, not a sector-weighted composite, not one carrying OSM
industrial land use (which is a real predictor, and rescues Yichang where the traffic surface
scores −0.091, but does not win overall).

## 2c. The Kandy campaign, and what it can no longer claim (2026-09-06, OSF `ad3py`)

A 35-site network was designed for Kandy, justified against the physics of the basin and against
United States siting law, costed, and pre-registered before deployment. Two of its purposes were
then removed by its own analysis, and both removals happened before any money was committed.

**The design.** Five strata over an emission surface spanning 65× between its tenth and ninetieth
percentiles, of which the two existing records occupy only the 61st to 100th: one anchor, twelve
design sites chosen by conditioned Latin hypercube over seven covariates (including nocturnal
ventilation, drainage convergence and the day-to-night ventilation ratio), nine paired sites at
100 and 300 m, five vertical sites spanning 8 to 291 m above the local valley floor, and eight
receptor sites near vulnerable-group facilities, held out of fitting. Serviceability was a
constraint rather than an afterthought: 19,467 of 25,600 cells lie within 400 m of a road, and the
screen ran before the optimisation rather than after it.

**What it cannot do.** Beating the 0.309 benchmark with eighteen fitting sites would require a
gain of +0.30 to +0.47 in rank correlation, while the 46-city panel resolves 0.130; matching the
benchmark in a single city needs between 96 and 304 sites. The headline spatial hypothesis was
demoted to exploratory before funding. It was then removed altogether: on 43 cities with dense
networks and 601 stations, each city made into both a deliberately sited and a convenience-sited
design by choosing which of its own stations to fit on, deliberate siting does not measurably beat
convenience siting (paired median −0.044, interval −0.095 to +0.118, winning in 19 of 43). The
result is undetectable rather than refuted, but it removes the last available explanation for the
gap between published land-use regression (R² 0.43 to 0.83) and this project's convenience frames
(ρ near 0.3). That gap is information, not sampling.

**What it can do, and is well powered for.** The anchor settles the level on its own. The
within-cell ratio resolves to 1.044 within seven days, against competing predictions of 1.58 and
27.5. The drainage sign test takes the night as its unit and reaches 63.1 per cent over ninety
nights.

**Cost.** Instruments come to 9,900 US dollars for 38 units and 6 spares at a published unit
price of 225; a reference anchor is 10,000 to 40,000. Mounting, power, import duty, labour and
servicing carry empty unit prices, because none is published for Sri Lanka, and import duty is the
largest single unknown. The reference anchor may instead be a letter: the Central Environmental
Authority has granted access in principle. Trimming the design stratum from twelve sites to ten
saves 450 dollars, under three per cent of the instrument budget, so the remaining decision is
about what the campaign claims rather than what it costs.

**A limitation of the criterion, stated.** D-efficiency ranks the road-sited network at 0.70 and
the existing two-sensor network at 0.88 against 0.35 for the proposal. It therefore prefers the
two designs already known to produce spatial nulls, while road-siting samples a single percentile
of the emission gradient. The criterion is reported with the design and is not used to choose it.

---

## 2d. Chemistry: one bound, one registered null, one invalid test (2026-09-06)

Chemistry was deepened on reviewer request without adding a chemical transport model, by
species-resolved testing against reanalysis already held on disk.

The usable result is a pair of Fréchet bounds placing the locally emitted primary share of Kandy's
PM2.5 between 9.1 and 48.3 per cent. This is what replaces the withdrawn statement that removing
every local source would remove half the problem, and it shows that the withdrawn statement sat at
the top of the admissible range rather than in the middle of it.

The registered test asked whether composition explains what latitude band only labels. All three
confirmatory hypotheses were undetectable, the largest partial correlation reaching 0.135 against
a minimum detectable effect of 0.431. The deviation is the finding: controlling for band drops the
eleven CNEMC cities, and the exploratory signal that motivated the study, a pooled correlation of
+0.388 across 46 cities, survives in neither resulting group (banded 35 cities +0.093, CNEMC
eleven +0.036). The apparent chemical relationship is a network effect wearing a chemical
variable's name.

The species-resolved partition is invalid and is reported as untested rather than as either held
or refuted. It ranks dust at 0.806 and sea salt at 0.645 above black carbon at 0.387. An inland
valley has no local sea-salt source, so the estimator is measuring episodic variability rather
than origin, and reporting the reversal would report an instrument failure as a finding.

Chemistry remains a supporting discipline with one measured bound. It is not a fourth pillar, and
the thesis says so.

---

## 2e. What an external review changed, and what it did not (2026-09-07, F.104-F.108)

A full external methodological review was answered over two rounds. Its three computational
objections were settled by running the experiments rather than by rewording, and all three found
something. The reviewer's closing assessment of the design is the frame this section is written
in: the core experimental architecture works, and the remaining work is narrower interpretation of
individual estimands rather than repair.

**Cities are not independent inferential units, and the intervals were too narrow.** The 48 panel
cities fall into 29 clusters when a cluster is a network within a country, and 11 of them belong to
one national network. A two-level bootstrap that resamples clusters and then cities inside each
drawn cluster widens every interval by between 1.34 and 1.97 times. No conclusion moves. The
background rung keeps a lower bound of 22.3 per cent, the first two sensors keep 4.5 per cent, and
stations three to six remain bounded above by 1.37 per cent, so the redundancy null is improved
rather than damaged by the objection. The deep-tropical inversion is unchanged to four decimal
places, because those 13 cities occupy 12 clusters: the dependence problem belongs to the pooled
numbers, which one national network dominates, and not to the band-stratified result the
recommendation for Kandy rests on. An intra-class correlation of 0.82 to 0.99 was computed and then
withdrawn, because 23 singleton clusters have no within-cluster variance and inflate it by
construction; over cities with a sibling it runs 0.23 to 0.65.

**The spatial null belongs to the data rather than to one model family.** Seven admissible model
families were fitted on 47 cities and 636 stations with 60 predictors, each with the target city
withheld entirely. None beats the benchmark of 0.301 by more than the registered detection limit
of 0.130; the best is a Gaussian process on covariates at plus 0.018, and conventional stepwise
land-use regression, the class that reaches published coefficients of determination between 0.43
and 0.83, buys plus 0.010. Kriging and geographically weighted regression are inadmissible in this
setting, because both estimate a surface from observations at the target and a city without
monitors has none. Run anyway as an oracle with the city's own stations visible, they score 0.048
and 0.073 against a benchmark of 0.301 obtained with no local observation at all, which extends the
earlier interpolation result from inverse distance weighting to the geostatistical and locally
weighted families.

**The representativeness error is externally identifiable and it was too small.** The observation
model estimated it from the local variability of the field, which asks the model to price its own
unresolved structure. Instruments sharing a single model cell measure the quantity directly: 14
such cells across 12 panel cities give a within-cell coefficient of variation of 0.140, the Kandy
transect gives 0.911 as a censored lower bound, and the model estimator gives 0.054. The estimator
is therefore too small by a factor of 2.6 on the panel and at least 17 at Kandy. It is not wired
into production and the delivered interval takes its width from the conformal quantiles instead, so
the shipped product is unaffected; what the result does is catch the defect at the point the
specification requires the observation model to exist, which is before any regulatory record is
ingested.

**A 2026 Sri Lankan calibration study was missing from the bibliography and is load-bearing three
ways.** It corroborates the refusal of Colombo as a background donor from an entirely different
quantity, since calibration models fitted in Colombo lose effectiveness at Kandy across climatic
zones. It gives the instrument-class confound a named mechanism, since a wet-season calibration
applied to dry-season data costs 26.57 per cent in mean absolute percentage error and the
deep-tropical stratum is 77 per cent low-cost against 25 per cent elsewhere. And its Kandy
reference is the Torrington Park BAM-1020, recorded in this project as defunct, which is worth
resolving because a reference anchor is the campaign's largest budget line.

**One defect was introduced by a correction.** After the first round, the abstract was tightened to
report the local fraction's sensitivity and gave the range 0.466 to 0.501 as sensitivity to the
definition of the background window. Those numbers are the minimum and maximum over anchored years.
The partition has three separate sensitivity axes, all reported correctly in the body: anchored
years 0.466 to 0.501, the parameter sweep 0.482 to 0.509, and background-window form 0.489 to
0.547. The abstract attached the right numbers to the wrong descriptor and so omitted the largest
member of the axis it named. The claims gate could not have caught it, because every token resolved
and the error was in the clause describing what the tokens measured.

**Four statements were narrowed and none of them was a model change.** The deep-tropical ordering
is now stated as supported by the available panel, with the question of whether it reflects an
atmospheric or a measurement regime left explicitly unresolved. The background rung's
conditionality reaches the abstract, including donor recovery falling to 37 per cent in Kandy's own
stratum. The partition's first appearance, in Section 2.3 rather than Chapter 6, now carries the
assumptions and the statement that a constrained decomposition is not a source apportionment.
And marginal predictive value is now the dominant term in the results, with value of information
reserved for the conceptual frame.

---

---

## 3. Epistemic status (what each claim can bear)

- **Validated by transfer:** seasonal & diurnal structure (held-out networks, 10 cities).
- **Anchored / corroborated:** absolute level (2-sensor transfer; sensorless for Kandy;
  2 satellite products; visibility; literature).
- **Identified ANNUALLY ONLY, and revised:** the regional–local partition. The shipped 25/75
  prior is refuted by five converging lines placing **f ≈ 0.35–0.45**; the raw SBI f=0.18 is
  **attenuated** (ρ = 0.426 ± 0.066, estimated from 3 cities). The split is **not separable at
  hourly resolution** — four requirements on it are mutually unsatisfiable with the available
  data (F.17–F.22). Burden and level are unaffected: the field is T-locked.
- **Imposed (scenario):** fine spatial amplitude and transport magnitude; confinement κ.
- Falsifiers per element: preprint Appendix D (epistemic ledger).

## 4. Deliverables

- **Flagship preprint:** `kandy_pm25/docs/reports/preprint_kandy.{md,pdf}` (**30 pp**, style
  `_preprint_style.tex`, built via `docs/reports/build_report.js`). Target venues: ERL /
  EGUsphere / AIES. Pre-submission plan: `docs/paper/pre_submission_fixes_and_spatial_roadmap_2026-07.md`.
- **Standalone release model:** local `d:/ProjectCD/kandy_pm25_release/` → repo
  `daminda1108/kandy_pm25_model` (public, MIT, v1.0.0; package `kandymodel/`). The runnable
  Kandy production model; code-only, data via `scripts/regenerate_all.py`. Gitignored by parent.
- **Research framework repo:** `daminda1108/kandy_pm2.5_framework` (from `kandy_pm25/src/`).
- **Technical reference ("model bible"):** `kandy_pm25/docs/model_reference/` (20 parts) +
  `docs/MODEL_REFERENCE_COMBINED.md`.
- **Supervisor reports + China-arc doc:** `kandy_pm25/docs/reports/`.
- **Public web explorer, Kandy (2019–2026):** `daminda1108/kandy-pm25-explorer` (GitHub Pages) —
  static client-side reconstruction of the additive_v2 model; local `d:/ProjectCD/kandy_webapp/`.
  Two tiers, labelled on-site: **2019–2023 satellite-anchored (locked)** and **2024–2026 a
  driver-anchored extension** (VanD ends 2023). Wind uses the B2 thermal valley-circulation
  input as a *disclosed method transfer* (form validated at Medellín + Kathmandu; Kandy
  parameters are physical priors — no local wind record).
- **Medellín deliverable app (2018–2024 + live forecast):** `daminda1108/medellin-pm25`
  (local `d:/ProjectCD/medellin_webapp/`) — the "what Kandy gets with the right data" demo and
  the improvement testbed. Public-first UI, shared engine via `js/cities.js`; hourly live
  forecast to **+120 h** with per-lead F-MQO skill scored against WAQI/SIATA observations.
- **Forecast extension (ground-truth-validated; live at Medellín, DEMONSTRATION tier at Kandy
  since 2026-08-02):** the lag-free temporal anchor is satellite-independent (retrain Δ −0.004 R²)
  and, driven by archived GEOS-CF *forecast* data, beats 24 h persistence by **+0.120 skill**
  (RMSE 5.71 vs 6.49) against 15 held-out Medellín stations while retaining ~100% of the
  seasonal/diurnal shape. ⚠ **The earlier +0.223 was inflated by temporal leakage** — that run
  trained on hours inside its own evaluation year; the clean split (train ≤2022) roughly halves it
  and all pre-registered gates still pass. **Never quote +0.22 or the 12–36 h lead sweep.**
  Kandy ships it as a labelled demonstration with borrowed evidence and OOD-widened intervals
  (k = 1.35, from the sensorless anchor's measured 70.7% coverage) — there is still no local
  self-check, by design. Docs `docs/forecast_*_2026-07-10.md`; ledger F.12.
- **Medellín proving-ground showcase:** a ground-data ladder — Act 0 zero-local-data (VanD level
  + physics; ρ 0.779 = ties the 2-sensor tier) → data-value curve (skill vs N monitors).
  Headline value-of-monitoring result: **one unrepresentative sensor is worse than none,
  placement beats count at small N**, assimilation helps at N≥2 and saturates ~N=12. Plan
  `docs/medellin_showcase_plan_2026-07-11.md`; artifacts `results/figures/medellin_showcase/`.
  The **improvement loop it powered closed 2026-07-21**: B2 wind ported to Kandy (gated at two
  valleys), amplitude "fix" A2 and the ConvCNP assimilator both **rejected on their own
  pre-registered gates**, and the held-out re-score (now N=10) confirmed no regression.

## 5. Data inventory (current model)

All model inputs are public and available for any city.

| Quantity | Source | Notes |
|---|---|---|
| Terrain (DEM) | SRTM 30 m | per-city `data/external/{city}/dem/` |
| Meteorology | ERA5 (winds, BLH, T, RH, precip) | hourly |
| Regional chemistry shape | GEOS-CF | daily; per-city ratio |
| Satellite PM2.5 level | van Donkelaar V6 (Asia + SA tiles), GHAP V1 | 1 km; level anchor + independent cross-check |
| Trace-gas / aerosol columns | TROPOMI NO2, MODIS/MAIAC AOD | features for T(t) |
| Night-lights | VIIRS | population/activity proxy |
| Roads | OpenStreetMap | emission-surface centrality |
| Analogue ground truth | CNEMC, OpenAQ, national networks | held-out validation, 9 cities |
| Kandy reference (consistency only) | KOALA/Senarathna 2024 (1 yr, 1 pt); FECT (non-public) | not a public network |

Multi-city products: `data/processed/decomp_{kathmandu,xichang,bazhou,chandigarh,taian,baoji,yichang,medellin}/`.
Kandy production: `data/processed/decomp/kandy_decomp_predictions_{year}_additive_v2.parquet`.

## 6. Locked methodological commitments

- Single target: **Kandy**. Native resolution **1 km hourly**.
- Model is **additive** (not multiplicative) — keeps the level unbiased at floor-sited
  networks (+26% inflation avoided; ablation-confirmed).
- **T-lock:** basin mean ≡ T(t); the spatial pattern redistributes without changing the total.
- Spatial pattern is **physics-imposed, not learned** (learned-pattern model fails; ρ≈0.14).
- Kandy framing: "consistency anchors + transfer validation," never "direct validation."
- Emission surface = **proxy for the local spatial pattern, not a source inventory**; level
  carried by the total-PM anchor (gotcha #59).
- Evidence pipeline is **version-controlled + tested** (`scripts/` evidence chain +
  `scripts/tests/`, 10 invariant tests; committed 2026-07-02).

## 7. Supporting / historical work (led here; not the deliverable)

- **Stage A** — satellite-ML temporal anchor (daily XGBoost 2003–2025 LOMO R²=0.63; hourly v3
  LGBM/CatBoost/XGB blend R²=0.58 + CV+ Mondrian conformal). Lineage of the T(t) anchor.
- **Stage B** — cross-city ConvCNP residual learner (deepsensor, LOOCV mean r≈0.44–0.60);
  reframed as the exploratory spatial-transfer result that motivated the physics decomposition.
- **Supporting PINN** (Medellín→Chiang Mai TD-PDE, FourierPINNV3) and **SharedTerrainAnsatz** —
  methodology studies, not feeders.
- **PVAF** — physics valley-analogue finder; now the objective analogue-selection procedure
  (preprint Appendix E) + an OOD/descriptor tool.
- **GeoAQ-Zero / SERENDIB** — zero-ground-truth framework (Tracks T-a/U/I/S) + planned all-island
  Atlas. Track T-a (sensorless anchor) folded into the preprint; Track S null (spatial
  unlearnable from public covariates).

Full history: `memory/SESLOG.md`; canonical doc index: `docs/README.md`; foundational design:
`RESEARCH_PROJECT_DESIGN.md`, `docs/REDESIGN_2026-05-08.md`.

## 8. Next (pre-submission)

1. **DONE (2026-07-02):** version + test the evidence pipeline (18 invariant tests).
2. **DONE (2026-07-25/26):** anchor provenance audited; A4 disclosure, A3 shelf-life caveat and
   the references applied; preprint rebuilt at 28 pp, N=10.
   - The audit's finding, stated plainly: the shown Kandy **level** is genuinely sensorless
     (T annual mean ≡ VanD basin *area* mean, exactly), but the **diurnal/seasonal amplitude**
     is calibrated against the two local research low-cost sensors. Now disclosed in §2, with
     the §8 "reproduces the calibrated reference" claim relabelled a *two-instrument
     consistency check*. `docs/paper/a4_anchor_provenance_audit_2026-07-25.md`.
3. **Open decision:** whether to go beyond that minimal disclosure — Option 2 (show the
   Section-7 *sensorless* field as the product) or Option 3 (reframe as a two-sensor product).
   Option 2 is the strongest for the thesis and costs figure polish (sensorless seasonal
   r 0.62 vs the calibrated 0.75+).
4. Supervisor + one external atmospheric-science reader → enable GitHub↔Zenodo → DOI → submit
   (ERL / EGUsphere / AIES).
5. Optional: one genuine tropical **South/SE-Asian** analogue (the Chinese share is 5/10 after
   Bogotá, which added regime rather than geography).
6. Optional follow-up: mobile-monitoring campaign — after five independent nulls, the only
   remaining lever for measured fine-spatial skill → a "measured fine field" paper.

## 8b. The post-2023 extension tier — a defect found by a user, and fixed

The 2024–2026 years are **not** anchored to the satellite level product (it ends in 2023);
they are a separate driver-anchored tier. In August 2026 a user reported implausible
estimates there. The report was correct and the audit is worth recording, because of *how*
the defect hid.

**Every aggregate diagnostic passed.** Annual mean, monthly means (within 12% of the anchored
climatology), seasonal shape, diurnal swing (ratio 0.99), diurnal phase, background ratio,
accumulation fraction. **The tail was destroyed**: hours above 55 µg/m³ fell from ~85/yr in
the anchored years to **0.5/yr**, with a hard ceiling at 56.5 µg/m³ — the 99.2nd percentile of
the anchored distribution — and three consecutive years capping within 1.7 µg/m³ of each
other. The suite contained no tail diagnostic, so nothing caught it for a year.

**Cause.** A quantile GBM predicts leaf averages and cannot extrapolate beyond its training
targets; the tier is lag-free so multi-day episodes cannot build; and the existing amplitude
correction operates only on the hour-of-day and month climatologies.

**Fix, validated.** The estimator's own damping is measured by leave-one-year-out over the
anchored years and inverted *indexed by quantile*, so hour ranking and genuine interannual
differences survive. Holding each anchored year out: p99 44.6 → 54.9 against a truth of 54.9;
hours>55 1.8 → 88.2 against 84.8; level unchanged. Intervals widened in the same pass, so the
less certain tier is now the wider one (41–49 vs 28–30 µg/m³).

**What it does not fix, and this must be quoted with it:** the correction restores *how often*
episodes of a given size occur, **not that they occur on the right hours**. Hourly correlation
with truth is unchanged by construction. A specific hour in 2024–2026 is indicative of
conditions, not a reading.

**A second, separate limitation surfaced in the same investigation.** The *hourly* spatial
sharpness is bounded by a hand-set constant that has never been calibrated. On ~4% of hours —
12.7% of 06:00, 15.6% of 19:00, none at midday — that bound is reached, producing core pixels
of 100–200 µg/m³ on a 20–30 µg/m³ basin and core/edge ratios near 4×, where the figure this
project defends is the **annual** contrast of about 1.2×. Now disclosed in the public method
page. The annual figure stands; a single dramatic hour does not.

## 8b-bis. RESOLVED — the coherence cap (2026-08-10)

An external reviewer supplied the argument eight internal attempts had missed: **local
sources emit continuously, so the local increment at an emitting location is strictly
positive at every hour.** Rain changes removal, not emission. A background at or above the
total is therefore not a physical state; it is an over-estimated background. Uncapped, this
was violated on ~25% of hours, rendering the field exactly flat and reporting a **zero local
share at the traffic core**, which is impossible.

Because the background is daily-flat, the constraint has a closed form — cap each day at
`(1 − F_MIN) × min_hour(T)`, which is the coherence bound of F.17 *imposed* rather than
merely computed. Result across all eight years: **zero-local hours fall from ~25% to 0.13%**,
and the annual local fraction becomes **f ≈ 0.48**.

**The answer is not tunable.** Sweeping `F_MIN` from 0 to 0.08 moves `f` only from 0.477 to
0.502 — the physical constraint sets it, not the parameter. `F_MIN = 0.02` was chosen as the
smallest value that removes the defect, before the resulting `f` was known.

**f = 0.48 agrees with every independent line**: above the coherence floor (≥0.41), inside
the hierarchical interval (0.392 [0.258, 0.525]), near the network instrument (0.446). The
0.244 prior is retired. **Basin means, exposure and burden are unchanged** — the field is
T-locked; only the attribution moves, from ~25/75 to **~48/52**.

**The cost, disclosed:** the wet/dry background ratio moves to 0.39 against an observed 0.53,
the gate on which an earlier rebuild was rejected. Accepted because the physical constraint
is absolute while that reference is inferred from sensor totals partitioned by origin — an
inference that itself presupposes a local share, so it cannot adjudicate against revising it.
Reclassified from gate to diagnostic.

*(§8c below records the three identification routes that failed before this; they are kept
because the negative results stand and the hourly-resolution finding is transferable.)*

## 8c. The partition: what is claimable, after three failed identification routes

Attempts to make the local fraction an estimated, time-varying quantity were pre-registered
and **all stopped at their own gates** (ledger F.40, F.41): an hourly reference partition at
the panel cities (3 of 10 cities passed, 5 required), a daily one (4 of 10), and the
coarse-CTM urban-increment route standard in Europe (GEOS-CF as background puts `B > T` in 60%
of hours). Combined with the five earlier background reconstructions, **eight distinct routes
have now failed on criteria set in advance.** A standing rule follows: no further
reformulation without new measurement.

**What can be claimed.** The annual local fraction to roughly ±0.1, from three independent and
convergent lines — a coherence floor of ≥0.41 computed from the shipped anchor alone, a
hierarchical fit with Kandy held out (0.392 [0.258, 0.525]), and a national-network instrument
(0.446). The shipped prior of 0.244 is refuted. Separately, the partition's **seasonal shape**
is measurable: it swings by about **1.66×** within a year at panel cities, stable across
temporal resolution, confirming that a per-year constant is physically inadequate even though
its level cannot be pinned this way.

**What cannot.** A validated time-varying fraction — not for lack of an estimator, but for
lack of anything credible to score one against.

**What is probably not identifiable at all, and is worth reporting as a finding.** The hourly
split. `B > T` in 28.5% of Kandy hours was long assumed to be an artefact of our background
construction. It is not: observation-based references built from real, dense monitoring
networks incur the same pathology in **13–25% of hours and 7–25% of days**. Hourly
background/increment decomposition appears close to ill-posed regardless of how the background
is constructed — a transferable result, and a stronger statement than the caveat it replaces.

## 9. Known scope limits worth stating

- **Sensorless is DAILY-only.** Track T-a gives a genuinely sensor-free daily/seasonal anchor;
  the **hourly/diurnal shape has never been produced sensorlessly** anywhere in the project
  (Kandy's comes from a FECT-trained GBM + amplitude sharpening; the analogue cities' from a
  residual GBM trained on their two anchor sensors). The tier labelled "0 sensors" removes only
  the sensor *level-anchoring* — corrected in both apps to "satellite level only".
  `docs/sensorless_product_scope_2026-07-25.md`.
- **Panel↔validation overlap.** 5 of the 9 original scorecard cities sit inside the 199-city
  CNEMC panel. No published result is affected (the scorecard model never trains on the panel;
  Track T-a is LOCO), but a *future* panel-trained model can be validated only on the four
  non-Chinese cities.
- **Bogotá is a 2-year city** (2021–2022 dense network), so its level/inter-annual claims are
  weaker than its diurnal and spatial ones.


---

## 2026 manuscript: what the checking produced

The paper build ran nine phases (`docs/paper/PAPER_DEFINITION.md`). Its most useful output was
not the prose but what verification found. **Fourteen numerical corrections and twelve review
findings, none of which came from writing more.**

### Corrections to reported quantities

| was | is | note |
|---|---|---|
| local fraction 25.3% (`additive_partition.csv`) | **0.4828** | file was stale by 2×; the value existed only in prose. Now `kandy_partition_v2.json`, file renamed `_v1_superseded` |
| gauge "preserved exactly" | **+0.39 to +0.56% above anchor**, every year | P is recovered from an upstream field; the old check compared two fields sharing the drift |
| ansatz "6 of 6 parameters at bounds" | **2 of 6**, both at the low extreme | read from the surviving log |
| fine-tuned field "flat near sensors, 33 far away" | **44.3 within 2 km, 1.65 beyond 10 km** | signature runs opposite to the record |
| interval coverage after re-centring 91.5% | **92.2%**, offset +5.859 | artifact regenerated since |
| evening emission peak 19 LT, ratio 2.14 | **18 LT, 2.32** | intervals unchanged, conclusion unaffected |
| zero-local hours 0.13% | **0.00 to 0.47% per year** | cause is negative anchor hours, not cap failure |
| eps0 Kandy 2.573 | **3.69** | scales with mean accumulation, which the cap moved |
| core-to-edge contrast (undefined) | **1.31**, top-to-bottom decile | three values were circulating because no definition was stated |

### New results the checking produced

- **f is insensitive to the cap's FORM, not only its parameter**: calendar-day 0.481,
  rolling-24 h 0.487, rolling-48 h 0.540, uncapped 0.242. Converts a caveat into evidence.
- **The PDE network supplies a controlled experiment**: same architecture, Chiang Mai with 8
  stations fits a spatial field; Kandy with 2 gives spatial SD **2.7% of mean** while
  reproducing its own temporal input at r 0.9996.
- **Anchor returns a negative total in up to 0.47% of hours**, minimum −3.49. A deficiency of
  the model class; a log or gamma link is the remedy.

### Corrections from outside the project

- **Nirmani et al. 2025** publish daily Kandy PM2.5 for 2021–2022, obtained **from NBRO on
  official request**. The claim "no continuous public record" was too strong; the defensible
  claim is no publicly *retrievable* continuous *hourly* series.
- **Elangasinghe & Shanthini 2008** (25 sites, PM10 vs traffic, r² 0.82) and **Wickramasinghe
  et al. 2011** (20 sites, urban/suburban/rural) give **45 Kandy locations, two groups, two
  methods**, all showing particulate tracking the road network. Strongest support the emission
  surface has.
- **A reference was credited to the wrong authors.** `Rao1997` is in fact **Eskridge et al.
  1997**; the DOI was right and the author list was not.
