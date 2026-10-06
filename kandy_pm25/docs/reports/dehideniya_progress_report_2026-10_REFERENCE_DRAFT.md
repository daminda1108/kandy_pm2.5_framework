# [AI REFERENCE DRAFT — rewrite every sentence in your own words before sending]

# Progress report for supervision and review: PM2.5 estimation for Kandy, and what an air-quality observation is worth
**To:** Dr. Mahasen Dehideniya (data-science co-supervisor) · **From:** Daminda Alahakoon · **Date:** October 2026
**Suggested attachments:** Fig. A `fig3b_like_for_like.png`, Fig. B `figS1_station_count.png`, Fig. C
`fig7b_spatial_noise.png` (in `papers/paper1_information_budget/figures/`).

---

## How to read this report
It has been a long time since we met, so this report is deliberately complete. It covers what I tried, what failed and
why, the design choices I made and how I justified them, the errors I found in my own work, where the project stands,
and the decisions I would like your judgement on.

**If you have little time**, please read Section 1 (the arc), Section 6 (a flaw I found in my main result and the
corrected analysis), and Sections 9–10 (decisions and questions for you).

The thesis is due next month. There are two papers:
- **Paper 1** is a methods paper on the value of information, and is the more mature.
- **Paper 2** is the Kandy application, which waits for CEA monitoring data.

My main supervisor and I agreed to settle the method first.

**Contents**
1. The problem, and how the project got here
2. Data
3. Part A — the Kandy model
4. Methods I tried and abandoned
5. Part B — the information-budget study
6. A flaw I found in my own design, and the corrected analysis
7. Errors I found in my own work along the way
8. What I think is solid, and what is not
9. Decisions where I need your judgement
10. Questions for you, by area
11. Timeline and next steps
Appendix: registrations

---

## 1. The problem, and how the project got here
**The original aim** was an hourly, 1 km map of PM2.5 over the Kandy basin, with honest uncertainty. One difficulty
shaped everything since: Kandy has **no public monitor**. The only local data are two low-cost PurpleAir sensors (FECT,
2018 onward) and one year of a research monitor (KOALA, 2019).

**Phase 1 — machine learning and physics-informed networks (March–May 2026).**
- **Satellite-ML model for the daily level.** The first version calibrated CAMS labels with KOALA and then validated
  against KOALA, which is circular. Moving to the FECT sensors as labels gave leave-one-month-out R² 0.69 (daily). An
  hourly version reached 0.58, just short of its 0.60 target.
- **Physics-informed models for the map.** A spatial PINN lost the ordering of stations, and all six parameters of a
  terrain-flow model hit their bounds.
- **A cross-city neural process** (ConvCNP), trained on three valley cities and applied zero-shot to Kandy, gave an
  over-smoothed map. Fine-tuning it on the two FECT sensors made it memorise their locations.
- **Lesson:** the binding constraint was data, not architecture.

**Phase 2 — a physically structured model, checked elsewhere (June–July).**
- I rebuilt the product as an additive decomposition: a regional background plus a local increment, spread by an
  emission pattern, terrain confinement and diagnostic winds, and anchored to a satellite PM2.5 product.
- Kandy cannot check it, so I ran the identical pipeline at ten cities with dense networks, restricted to Kandy's
  two-sensor budget.
- A public web explorer, a release repository and a preprint followed.

**Phase 3 — the question changes (August).**
- The first independent Kandy checks arrived. The NBRO station agrees with the model within 3 %, but three low-cost
  records sit below it, so the level is an open question.
- Since a Kandy map cannot be validated without local data, the useful scientific question became **what each
  observation is worth to a city without monitors**, and so what Kandy should measure first. That became the
  "information-budget ladder".

**Phase 4 — testing it properly (September).**
- Repeating the analysis over many random station splits showed that some striking early results were single random
  draws, so I rebuilt the method (ladder v2).
- I registered a confirmation on 72 fresh cities, three robustness tests and a within-city "spatial learning curve",
  and ran each once.
- A Kandy sensor-network design was also drafted. It is excluded from the thesis until the method is settled.

**Phase 5 — auditing it (October).**
- A design audit found that a 12-station cap and a one-year record window had shaped two results, so both were re-run
  under new registrations.
- A self-review of my code, done as an outside referee would, found a flaw in my main result (Section 6) and narrowed
  several other claims.

## 2. Data
- **Kandy:**
  - FECT PurpleAir sensors at Akurana (~460 m) and Hantana (~738 m), hourly, 2018–2026;
  - KOALA research monitor, 2019;
  - independent point records published by NBRO and in two 2025 papers;
  - CEA regulatory monitor (hourly, 2019–2026), granted in principle but awaiting a formal agreement.
- **Panel cities:** about 120 cities with at least 10 stations, from OpenAQ (worldwide) and CNEMC (China). A
  station-day needs at least 18 valid hours.
- **Free predictors:**
  - ERA5 weather (temperature, wind, boundary-layer height);
  - MAIAC satellite aerosol;
  - 60 static geography features on a grid over the urban centre;
  - CAMS and GEOS-CF chemical-transport fields;
  - van Donkelaar and GHAP satellite PM2.5 products;
  - IMERG rainfall;
  - OpenStreetMap roads;
  - a 90 m terrain model.

---

## 3. Part A — the Kandy model (Paper 2; supervision needed on identifiability and uncertainty)

### 3.1 Formulation
PM(x, y, t) = B(t) + max(T − B, 0) · P(x, y, t) + min(T − B, 0) + ε(t)(P − 1)

- **T(t), basin level.** Gradient-boosted trees on free drivers. It is wrapped in a conformal interval, re-anchored
  each year to a satellite area mean, and its diurnal and seasonal amplitude is sharpened to the FECT sensors.
- **B(t), regional background.** A rural satellite floor times a daily regional shape.
- **P(x, y), local pattern, mean 1.** The product of a road-network emission surface, terrain confinement and
  diagnostic winds. Because it averages to 1, the field's basin mean equals T exactly; I call this the T-lock, and it
  holds to within 0.6 % in practice.
- **The two correction terms.** Each fixes a measured defect:
  - *Increment split.* When T dips below B (38 % of hours), a plain product renders the city core cleaner than the
    countryside. The split applies the pattern only to the excess above background.
  - *Ventilated-hour floor (ε).* The split alone left well-mixed hours perfectly flat, which Medellín's stations
    contradict. A small mean-zero floor restores some pattern on those hours.

### 3.2 Justifications I would like checked
- **Additive rather than multiplicative.** A multiplicative form modulates the transboundary background by local
  emissions, which is physically wrong. The additive form keeps the background uniform and structures only the local
  part.
- **Level anchored to a basin area mean, not to KOALA.** KOALA is a valley-floor point, and two independent satellite
  products put the area mean 25–30 % lower. Forcing the basin mean to the floor point double-counted the floor
  enhancement.
- **Local fraction f ≈ 0.48 (the share of PM2.5 attributed to the local increment).**
  - Local sources emit every hour, so the background should never exceed the total. I imposed this as a daily cap,
    B ≤ (1 − 0.02) × the day's minimum T.
  - ⚠ The review showed that **f is then set by T's daily amplitude, not identified by data**. It moves between
    **0.43 and 0.49** with reasonable choices: UTC versus local day, and the minimum versus a less noise-sensitive
    statistic.
  - I now describe it as "a bound under the cap", not as "fixed by physics".
- **The pattern is imposed physics, not learned.** Six independent tests showed the fine within-city pattern cannot be
  learned from free covariates (Section 5.6).

### 3.3 Validation
- **Ten analogue cities.** The identical pipeline, at Kandy's two-sensor budget, scored against held-out stations:
  - seasonal r 0.94–1.00;
  - diurnal r 0.60–0.98 in 9 of 10 cities;
  - level −4 % to +30 % (median +7.6 %);
  - spatial rank significant in 6 of 9 cities.
- **Independent Kandy checks.**
  - NBRO: +0.7 % and −2.6 % at its pixel (2021, 2022).
  - A satellite-calibrated low-cost record (RF-CNN, a 2025 study): the model reads +28 %.
  - Two FECT records: the model reads higher than both.
  - So three of four records sit **below** the model. I report this as an open level question (W11), but it may be an
    upward bias.
- **Off-the-shelf baseline.** At NBRO the GHAP satellite product alone reads −10 % and −17 %, so the chain does add
  value there. That is one site, with an undocumented instrument.

### 3.4 Uncertainty
- The 90 % interval covers only **72.4 %** at the FECT pixels, and the misses are almost all on one side: 25.7 % of
  observations fall below the interval and 1.9 % above.
- Removing each sensor's median offset restores 91.5 %. So the width is right and the centring is not. The field is a
  1 km area mean and the sensors are points.
- The interval does not propagate structural uncertainty: confinement strength, f, the emission proxy and the sensor
  calibration slope.

### 3.5 Weaknesses found in the October review
- **Humidity.** The sensors' humidity correction (the US EPA formula) used a constant 80 % humidity. With hourly ERA5
  humidity the modelled day-night swing shrinks by about 11 % (peak/trough 1.82 → 1.62). A full hygroscopic-growth
  correction over-corrects. Only co-location with a reference instrument can settle the diurnal shape.
- **Circularity.** The FECT sensors train T, set its interval width and sharpen its amplitude, so every FECT agreement
  is in-sample. The genuinely independent checks are NBRO, the RF-CNN record and KOALA 2019.
- **Health burden.** 431 deaths per year [237–632] for 2023. The model (GEMM) was applied to all ages instead of ages
  25 and over, and the interval carries only the response-function uncertainty. I treat it as an illustrative
  appendix.
- **Decision (mine and my main supervisor's):** the shipped model stays unchanged until the CEA data arrive. Then I
  rebuild with hourly humidity and a local-day cap, and check against the reference monitor.

---

## 4. Methods I tried and abandoned
| method | what happened | why I stopped |
|---|---|---|
| CAMS-label XGBoost, KOALA-calibrated (Stage A v1) | daily R² 0.63 | circular: KOALA used both to calibrate the labels and to validate them |
| Spatial PINN (quasi-steady-state) | lost the ordering of stations under physics weight | moved to a time-dependent PINN, then cut spatial PINN work entirely |
| Rigid terrain-flow ansatz (Whiteman) | all six parameters hit their bounds in every city | the functional form cannot represent different valley regimes |
| ConvCNP cross-city transfer (3 source cities) | sound point skill; Gaussian likelihood collapsed the variance (coverage 0.54–0.73), fixed with Student-t + per-city×hour conformal | zero-shot map over-smoothed; fine-tuning on two sensors memorised their coordinates |
| Temporal Fusion Transformer (hourly) | R² 0.45 against the tree blend's 0.58 | no gain |
| Five rebuilds of the background B(t) | each moved one diagnostic and broke another | the hourly local/regional split is not identifiable from these data; I stopped at five |
| Learned spatial pattern, foundation-model embeddings, land-use regression, six model families | none beat a single built-up covariate beyond its detection limit | information-limited at 1 km (Section 5.6) |
| GEMS geostationary satellite | 55° viewing angle at Kandy (1 pixel over the domain); misses afternoon and night | geometry, decided before requesting access |
| ERA5-Land rainfall | 2× the gauge total | replaced by GPM IMERG |
| Single-split ladder (v1) | a headline "4.2× local over background in the deep tropics" | excluded zero in only 3 of 20 alternative splits; retracted |

---

## 5. Part B — the information-budget study (Paper 1)

### 5.1 Design
Each city's stations are split at random into **held-out stations** (scoring only) and **available stations**.
Estimators ("rungs") are compared, each allowed more information than the one before:

| rung | information | model |
|---|---|---|
| Bud0 | free data only | gradient-boosted trees, **leave-one-city-out** |
| Bud1 | + first two stations | Bud0 recalibrated (intercept, slope) to the two stations |
| Bud2 | + stations 3–6 | the same recalibration on six stations |
| Bud3 | + background | regression on Bud0 and the daily 10th percentile of the remaining stations |

Each rung declares the data streams it may use, and the code asserts this in **both directions**: a rung may not use a
stream it is not entitled to, and may not silently under-use one it is. The second check exists because of an error
(Section 7).

### 5.2 Statistical design choices and their justification
| choice | justification | what I would like checked |
|---|---|---|
| Percentage RMSE reduction per city, then the **median over cities** | cities differ hugely in baseline skill; the median of ratios, never a ratio of medians | is a per-city percentage the right effect measure? |
| **Paired within city** | an unpaired difference of medians pointed the wrong way twice in this project | — |
| **21 station splits × 5 learner seeds**, averaged before inference | one split moved a headline from significant to null; one seed moved a gain from 11 % to 23 % | is averaging the right way to handle design randomness, or should it enter the model? |
| **Two-level cluster bootstrap** (networks/countries, then cities) | cities in one national network are not independent; intervals widen 1.15–2.21× | would a hierarchical model be better? |
| Shrinkage weights **cross-fitted** from the other cities | the first version chose each city's weight against its own held-out stations | — |
| Static geography on a **grid over the urban centre**, not at monitors | monitor-site features describe the scoring sites (~50 % denser), a leak | — |
| **Pre-registration** on OSF, frozen code, synthetic dry run, **parity gate** | discovery results moved on confirmation; the gate forces exact reproduction before anything new is scored | do these safeguards answer reviewers, given Section 6? |

### 5.3 Registered confirmation (OSF `ueyfr`, 72 fresh cities), with the rungs as built
| endpoint | median % RMSE gain [95 % cluster CI] |
|---|---|
| first two stations, as a recalibration | +8.5 [3.1, 25.1] |
| stations 3–6, as a recalibration | +0.2 |
| background, read on the day | +41.1 [26.8, 62.8] |
| background minus first two | +24.6 [4.1, 47.8] |
| the same on WHO-guideline exceedance days | +59.3 [33.9, 67.7] |
| dependence on latitude | not detectable (4 low-latitude cities) |

### 5.4 Registered robustness tests
- **Richer free baseline** (`b379r`): adding CAMS PM2.5, fires, NO₂, rainfall and terrain improved Bud0 by 13 %.
  Six of seven predictions held; the one that failed predicted that the first-station gain would shrink.
- **Other learners** (`jea58`): TabPFN, a 14-day GRU, and trees with physics features. None beat gradient boosting
  (TabPFN −11 %), and all 12 directional verdicts held.
- **Full station networks** (`mhgna`): up to 40 stations per city instead of 12. Every verdict held.

### 5.5 Registered null: precipitation
Adding rainfall moved the free baseline by −1.0 % [−5.5, +4.3]. That gap is now measured, not assumed.

### 5.6 Within-city maps
**Bounded nulls.** Six independent tests found that nothing free beats a single built-up covariate (within-city rank
correlation about 0.3):
- a learned pattern (+0.022, detection limit 0.13);
- Earth-observation foundation-model embeddings;
- six model families (best +0.018);
- a full land-use-regression predictor set (pooled rank correlation 0.273 → 0.275);
- deliberate versus convenience siting (paired −0.044 [−0.095, +0.118]).

**Spatial learning curve** (registered `rqn4y`, re-run on full records `fu59b`; 23 cities in 9 countries, including
Bangkok): how well do 3, 5, 8 … stations rank a city's neighbourhoods? Post-hoc re-analysis (Fig. C):
- Under the registered rule, 15 of 23 cities "crossed" a free land-cover layer. But each city is scored on as few as 10
  held-out sites, the spread between cities is not larger than sampling noise, and only **3 of 23** cross after a Holm
  correction.
- At 3–8 stations, neither interpolation, the land-cover layer nor a satellite PM2.5 product ranks neighbourhoods
  usefully (rank correlation about 0.1). Beyond about 1 km, kriging simply returns the city mean.
- Siting by design gains nothing (about ±0.05; Section 7 explains the registered bug in this test).
- Tropical cities cannot be distinguished from temperate ones (−0.22 [−0.45, +0.02]). The honest detection limit is
  0.35, not the 0.24 I registered.

---

## 6. A flaw I found in my own design, and the corrected analysis
Reviewing my code as an outside referee would, I found that **the rungs do not use their stations the same way**.
- The first stations only correct the level and scale of the free estimate, so their daily readings never reach a
  day's prediction. That rung was meant to mimic a short calibration campaign.
- The background is read on the day it describes.

The registered ordering "background beats the first local stations" therefore compares two *uses*, not two kinds of
observation. Registration and parity gates could not catch this: they check that a test is run as written, not that
it compares like with like.

I re-scored every stream the same way, post hoc. The same run reproduces the registered numbers to 3 × 10⁻¹⁴.

| every stream read on the day (Fig. A) | result |
|---|---|
| first two stations | **+58.8 % [44.9, 69.0]** (100 cities) |
| background, as registered | +57.7 % [46.4, 67.4] |
| background minus first two | **−0.22 [−0.60, +0.04]** points |
| the same, exceedance days | −0.11 [−2.49, 0.00] |
| full networks: a ~10-station background minus first two | +2.5 [1.1, 3.7] (an effect of count, not kind) |

How many stations, read daily (Fig. B, 86 cities):

| stations | 1 | 2 | 3 | 5 | 8 |
|---|---|---|---|---|---|
| read every day | −42 % | −53 % | −56 % | −58 % | −61 % |
| used only to calibrate | about −11 % at every count |

**Two further checks:**
- Refitting the free baseline leaving out each city's **whole network**, not just the city, makes the registered gains
  slightly larger (first two 8.5 → 13.3 %). So leave-one-city-out flattered the baseline a little. The corrected
  comparison is unchanged.
- I cannot register a fresh test of the corrected design, because almost no fresh dense networks remain (20 CNEMC
  cities, 2 of them tropical). I report it as a post-hoc re-analysis beside the registered result.

**Corrected conclusion:** a monitor-less city gains from the **daily reading**. One station read every day removes
about 42 % of the error, two about 53 %, and the kind of station hardly matters. A short calibration campaign recovers
about a fifth of that.

---

## 7. Errors I found in my own work along the way
I list these because they shaped the design, and because you may see others like them.
1. **A rung that under-used its data** (August). The free baseline used only one of the three free streams it was
   entitled to, which inflated the first-station gain (25.6 % instead of 17.9 %). This led to the two-way admissibility
   check.
2. **One split, one seed** (September). The headline deep-tropical result was a single random draw, which led to
   split-averaging.
3. **Difference of medians.** A siting comparison read as a doubling unpaired (0.257 vs 0.143); paired within city it
   was −0.044. Since then, every comparison is paired.
4. **A leaking feature.** Geography averaged over monitoring sites described the scoring sites. It is now computed on
   an urban-centre grid.
5. **Silent data gaps.** A date-chunking error dropped about 5 % of city-days, and an unpinned library update turned
   every prediction into missing values over a 27-hour run. Now every run checks coverage and counts finite values.
6. **The October design audit.** A 12-station cap and one-year records shaped two results. Both were re-run under new
   registrations.
7. **The October code review:**
   - the rung asymmetry (Section 6);
   - a pooling bug that printed the siting interval as [0.00, 0.00];
   - a first-pass crossing rule on 10-site correlations;
   - an assumed spread that understated the spatial detection limit;
   - the local fraction "fixed by physics";
   - the constant-humidity sensor correction.
8. **The thesis build.** It had silently failed for two weeks after a renaming of result keys; that is now repaired.

---

## 8. What I think is solid, and what is not
**Solid:**
- the leave-one-out free baseline, split-averaging, pairing and cluster bootstrap;
- the registered results themselves, which reproduce exactly;
- robustness across baselines, learners and network size;
- the corrected finding that a station's value lies in its daily reading, with a clear curve of diminishing returns;
- the bounded spatial nulls;
- seasonal and level transfer of the Kandy model to analogue cities.

**Weak or open:**
- The corrected comparison is post hoc.
- The panel is mostly temperate and regulatory-grade, while Kandy is tropical with low-cost sensors.
- The "background" rung comes from the same network. An independent network 30–300 km away recovers about 71 % of it.
- The spatial curve's per-city scores are noisy.
- In the Kandy model: f is a bound, not an estimate; the level question (W11) is open; the diurnal shape depends on the
  humidity correction; the intervals omit structural uncertainty; and the pattern is imposed, not validated at Kandy.

---

## 9. Decisions where I need your judgement
1. **How to present the corrected finding.** Should the corrected analysis lead Paper 1 and the thesis, with the
   registered result reported "as constructed"? Or should the registered result lead, with the correction as a major
   caveat?
2. **The local fraction f.** Keep the coherence-cap bound (0.43–0.49, clearly labelled), or replace it with a standard
   approach? For example, a Lenschow increment against a rural reference station (NBRO regional sites), or a Bayesian
   decomposition with priors that gives f a posterior.
3. **Uncertainty in the Kandy model.** Is it worth building structural uncertainty (f, confinement, emission proxy,
   calibration slope) into the intervals before the CEA data, or only after?
4. **Thesis scope.** Lead with the method study, with the Kandy model as the application? Or the reverse?
5. **Target journal for Paper 1, and the review-paper topic.**

## 10. Questions for you, by area
**Statistics**
1. Is the median of per-city percentage gains, with a two-level cluster bootstrap, the right summary? Or would a
   hierarchical model of the gains (cities in networks in countries) be more defensible?
2. Is it acceptable to report the like-for-like re-analysis post hoc, beside the registered result, when a fresh
   registered test is impossible? Should it instead be framed as data-denial experiments, as in data assimilation?

**Machine learning**

3. Pooled gradient boosting beat TabPFN and a GRU. For a target city unlike most training cities (Kandy), would you
   try domain adaptation or importance weighting?
4. How should I quantify how far the results transfer to the tropics with so few low-latitude cities? For example, a
   covariate-shift diagnostic or conformal intervals under shift.

**Spatial statistics**

5. With 5–50 irregular sites per city and noisy per-city scores, is a hierarchical model of rank correlation against
   station count (with city random effects) the right analysis? Is there a better mapping method than regression
   kriging?

**Kandy model**

6. Is the additive decomposition, with an imposed pattern and a capped background, a defensible structure? Or would
   you expect a data-fusion model (universal kriging with a satellite trend, or a Bayesian downscaler) to be required
   by reviewers?
7. For the low-cost sensors: is an ERA5-humidity EPA correction enough, or should I wait for co-location with the CEA
   monitor before any diurnal claim?

## 11. Timeline and next steps
- **This month:** rewrite the thesis around the corrected findings, then submit next month. Rewrite Paper 1 from its
  revised draft (all figures are built).
- **CEA data** (my main supervisor is arranging the agreement): check the Kandy model against a reference instrument,
  rebuild with hourly humidity, and settle the level question. Then Paper 2.
- **Later:** the sensor-placement proposal, once the method is settled, and a review paper (topic to agree).

## Appendix: registrations
17 registrations on OSF:
- 14 have run, scoring 105 predictions: 66 held, 23 refuted, 6 not tested, 10 two-sided or descriptive.
- Main ones: `ueyfr` (confirmation), `b379r` (richer baseline), `jea58` (learners), `mhgna` (full networks), `rqn4y`
  and `fu59b` (spatial curve), `2jyfg` (learned pattern), `6udm3` (embeddings), `z89kt` (precipitation).
- The review and every re-analysis are logged in `kandy_pm25/docs/review_remediation_plan_2026-10-06.md`. I can share
  the code repository, the draft paper and the thesis.
