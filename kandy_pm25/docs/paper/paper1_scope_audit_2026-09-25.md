# Paper 1 scope audit — what we have, what is left, and why (2026-09-25)

**Purpose.** Establish the scope of Paper 1 (the information-budget methods paper) from the
evidence as it stands today, not as earlier documents describe it. Method: three independent
read-only investigations (the Paper 1 draft; the evidence ledger F.50–F.113 with the OSF
registry; the history of papers and reviews), every consequential claim re-checked against the
files, and four comparisons that had never been paired computed paired (ledger **F.114**).

---

## 1. Bottom line

1. **The programme has a real, publishable methods result, but not the one the current draft
   leads with.** The draft's abstract says a single ground sensor "buys the largest gain in
   spatial skill available to any city, rich or poor". Two things are wrong with that: the ladder
   measures **daily city-mean error**, not spatial skill, and on the satellite stream the project
   actually uses the sensor-versus-background comparison is a **tie** when each city is compared
   with itself.
2. **What survives every paired test is a cleaner and more useful claim:** *what an observation
   is worth depends on the loss first and the climate band second.* On average days, across the
   panel, a background series and two local sensors are indistinguishable; on episode days the
   background wins in about three cities of four (paired, interval excluding zero); in the deep
   tropics local sensors win on average days and lose on exceedance. Beyond the first local
   station, more stations buy essentially nothing under every test.
3. **The strongest methodological contribution is the one the project kept rediscovering:**
   pooled medians across a city panel mislead, and did so at least **six** times in this project
   (F.102, F.103, F.111, F.112 P4, F.113, F.114). A paper that makes paired within-city
   comparison the required estimator, and shows the reversals, is citable and general.
4. **Before Results can be written**, the headline comparisons must be tokenised as claims,
   cluster-bootstrapped, and the draft corrected in eleven places (§5). No new data are needed.
5. **One scope decision is yours** (§7): whether Paper 1 waits for the registered spatial
   learning curve, which is the only pre-registered test that directly asks how much *spatial*
   skill each sensor buys.

---

## 2. What the programme has done, and why (the arc in one page)

| period | what was built | why it moved on |
|---|---|---|
| May–June 2026 | Kandy field: satellite-ML temporal anchor, then the additive decomposition `PM = B + [T−B]·P`; 10-city transfer validation; preprint (June 30) | The spatial arm could not be validated: monitors in valley cities are floor-sited and a city with no monitors cannot check its own map. |
| July–Aug 14 | 28-page manuscript for ACP: "the information in public observations bounds the admissible model class" | The claims audit (Aug 22) found the spatial arm confounded with change of support, and the panel grew to 47–48 cities. |
| Aug 18–23 | **The information-budget ladder**: declared tiers `Bud0`→`Bud3`, exact nesting, admissibility checked both ways (`require_covers`, after the F.84 defect inflated every gain) | This became the portable contribution: it needs no Sri Lankan data. |
| Sept 1–15 | Registered tests (C1, S1/S2, R2, chemistry, learned pattern, embeddings, precipitation), four outside review rounds answered largely by computation (F.97–F.112) | Reviews showed the Kandy recommendation depends on satellite stream, loss and driver set. |
| Sept 19 | Thesis split into A (Kandy field) and B (what an observation is worth) for the 75-page limit | — |
| Sept 23 | **Two papers**: Paper 1 = methods (48-city ladder + spatial nulls), Paper 2 = Kandy application (waits for CEA data) | Same day: C7 re-scoring and the pairing test changed the headline (F.113). |
| Sept 25 | This audit; F.114 pairs the last unpaired headline comparisons | — |

**Why each strand exists:** the ladder answers *which observation should a monitorless city buy
first*; the spatial nulls answer *can a better model substitute for observation of fine-scale
pattern*; the Kandy field answers *what is the best field we can build for one monitorless city*.
Paper 1 is the first two; Paper 2 is the third.

---

## 3. The evidence, graded for Paper 1

Status key: **REG** = registered on OSF with a verdict; **POST HOC** = exploratory, computed
after seeing data; **DESC** = descriptive. "Paired" = median of within-city differences,
bootstrapped over cities.

### A. Headline-grade (paired, robust across every check that has been run)

| # | result | number | status | robust to |
|---|---|---|---|---|
| A1 | **Redundancy:** stations 3–6 add essentially nothing | 0.1 % [0.0, 0.9]; ≤1.37 under cluster bootstrap; 0 under all four losses | values REG (`g6hqb`); intervals POST HOC | every learner (F.88), every loss (F.109), both orders, both streams, clustering |
| A2 | **Saturation at one station:** the second adds +0.01 pp | first station 17.0 % [5.0, 21.8]; no k = 2–8 beats one by >0.15 pp | POST HOC, paired | pooled; deep-tropical underpowered, not null |
| A3 | **The ordering depends on the loss (panel-wide)** | background − first two: RMSE +2.3 [−9.2, +21.4], MAE +4.3 [−8.7, +26.8], **tail +32.2 [+14.3, +43.8], exceedance +28.2 [+15.0, +53.2]** | POST HOC (F.113/F.114) | paired; not yet cluster-bootstrapped |
| A4 | **A monitor-trained covariate deflates the rung above it** | deep-tropical inversion GHAP +3.6 [−14.3, +36.3] vs MAIAC +33.3 [+7.0, +50.1] | C1 stream switch REG (`bkpyr`); inversion POST HOC | same cities, same procedure, only the stream differs |
| A5 | **Pooled medians reverse under pairing** (methodological) | six recorded instances, several with opposite signs | DESC (instances) | this is the finding |
| A6 | **Instrument class is aliased with climate band, structurally** | deep tropics 69–77 % low-cost; 6 deep-tropical vs 65 temperate reference clusters worldwide | DESC (global census) | cannot be sampled away |
| A7 | **Two-way admissibility catches real defects** | F.84 (25.6 → 17.9 %), C7 (58 claims), an unused variable inside an admitted stream (F.112) | DESC | the machinery's own track record |

### B. Supporting (sound, but with a stated limitation)

| # | result | limitation |
|---|---|---|
| B1 | Deep-tropical: local sensors beat background on RMSE, **+33.3 [7.0, 50.1]**, 10/13 cities; reverses on exceedance **−15.9 [−38.1, −1.5]** | post hoc; n = 13; magnitude moves with stream, loss and driver set (with precipitation the interval spans zero) |
| B2 | Learned pattern does not beat the best free raster (0.286 vs 0.309) | **REG `2jyfg`**, 5/5 held; bounded at a detection limit of 0.130 |
| B3 | EO foundation embeddings do not beat it (−0.028 paired) | **REG `6udm3`**, 3/3; E3 partial ρ +0.191 [−0.007, +0.355] is marginal, not zero |
| B4 | Seven model families, none beats the benchmark by >0.130; kriging, GWR, IDW with the city's own stations do worse | POST HOC (F.105) |
| B5 | Deliberate siting does not beat convenience siting, paired −0.044 [−0.095, +0.118] | POST HOC; **undetectable, not refuted** |
| B6 | Estimator dependence: Ridge collapses (50 % first rung) while tree learners agree (12–14 %) | DESC (F.88); the claim is "robust across non-linear learners" |
| B7 | Ordering effects are real and small: +1.1 pp for stations 3–8, +0.65 pp for the background | POST HOC (F.114) |

### C. Must NOT be a headline (fragile, unpaired, or withdrawn)

| claim | why |
|---|---|
| "A background series is the largest single gain" (40.6 %) | holds paired only on the retired GHAP stream; MAIAC is a tie on average days (F.113) |
| "Geography beats the satellite level" | paired +3.5 [−2.1, +15.2]; withdrawn (F.114) |
| "Satellite helps coastal cities 1.8× (4×)" | between-group ratio, no interval, 9 of 13 deep-tropical cities are coastal |
| "13× more from stations 3–8 with a background" | a ratio of medians; paired it is about 1 pp |
| "Background largest under every loss" | unpaired; paired it is a tie on RMSE and MAE |
| F.109 "fragility" | withdrawn: the gap was the C7 defect |
| F.112 P4 "background stays largest" | not supported paired, before and after the fix |
| Any `Bud3` magnitude stated as what a *rural* monitor buys | the background is an outer-ring proxy from the same network, and its gain tracks network size (F.73, F.54: 73 % recovered by an independent network) |
| "Four guaranteed properties" | two guarantees (P1, P3), one enforced mechanism (P2), one discharged obligation (P4) |

### D. Kandy-specific → Paper 2, not Paper 1

The additive decomposition and `f ≈ 0.48`; the Kandy checks (NBRO, FECT, transect); W11;
exposure and burden; the dispersion step; the procurement advice (CEA before NBRO); the
measurement campaign (`ad3py`); `s_rep` (F.106); chemistry bounds (F.98).

### E. Not yet available

The **spatial learning curve** (`rqn4y` / `26hp8` / `4whsc`, amendment 3 lodged for D-8): E0–E7
and E10 scored, E8/E9 64 of 78 city-frames complete, wave 2 postponed. **No number exists and
none may be quoted.**

---

## 4. The Paper 1 draft today

Location `papers/paper1_information_budget/`. Title and abstract and the introduction are drafted;
methods, results and discussion are outlines; results is marked BLOCKED; no figures are built
(`dabest`, `ptitprince` not installed); target ERL, secondary npj Climate and Atmospheric Science;
Paper 2 is an empty folder.

**Defects found (all verified against the files):**

1. Abstract 00:24–25: "a single co-located ground sensor buys the largest gain **in spatial skill**
   available to any city, rich or poor." The ladder measures daily city-mean error, not spatial
   skill; and on MAIAC the paired comparison with the background is a tie (A3).
2. Abstract 00:32–33 and 01:95: "a **single** local sensor beats a regional background monitor
   outright." The band comparison is the **first two** stations.
3. Results 03:20 calls the deep-tropical result "registered". It is post hoc (F.97c, F.113).
4. "**Eight pre-registered** tests" (00:36; 01:110, 118). The registry holds two panel-level spatial
   registrations with verdicts (`2jyfg`, `6udm3`); `bkpyr`'s spatial items are Kandy-field tests.
   F.105, F.103 and F.61 are post hoc.
5. Old ordering numbers (0.13 → 2.81 %, "21×") in `publication_strategy_2026-09-23.md`.
6. Headline figures from the retired GHAP stream (40.6 vs 17.9) in `FIGURE_PLAN.md`, marked
   "unchanged".
7. F.109 still marked "blocked"; none of the corrected values used.
8. Pairing reversals counted as "two other" or "a third time"; the record now has six.
9. 01:124 "a denser spatial network is unlikely to help" pre-empts the unscored spatial curve.
10. Panel counts: "13 temperate" appears to come from the spatial-curve frame, not the ladder
    panel; "48 cities" is used where the analyses have 46–47 (and 35 in F.112).
11. Section numbering in the introduction does not match the files.

---

## 5. Proposed scope for Paper 1

**Working title (for discussion):** *What an observation is worth depends on the question:
declared information budgets across 48 cities, and why pooled comparisons mislead.*

**The question.** For a city with no monitors, which observation stream is worth acquiring first,
and does the answer survive the comparison each city makes with itself?

**Claims (in order of strength):**
1. **Method.** A declared-budget ladder with exact nesting and two-way admissibility, and the
   defects it caught (A7).
2. **Redundancy and saturation.** Past the first local station, additional stations add
   essentially nothing, under every learner, loss, order and clustering (A1, A2).
3. **The ordering is loss-dependent.** Average days: background and local sensors tie across the
   panel. Episode days: the background wins. Deep tropics: local sensors win on average days and
   lose on exceedance (A3, B1). Every recommendation must name its loss.
4. **Pooled medians mislead; pair within city.** Six instances, with the estimator stated as a
   requirement (A5), and the contaminated-covariate effect as the sharpest case (A4).
5. **Bounded spatial nulls.** Two registered (`2jyfg`, `6udm3`) and two post hoc (F.105, F.103),
   stated as detection limits, not as "spatial pattern does not matter".
6. **A structural limit.** Instrument class and climate band are aliased worldwide (A6), which is
   why band results are stated as regimes, not mechanisms.

**In:** everything in §3 A and B. **Out:** everything in §3 C (except as corrections) and D.
**Deferred:** the spatial learning curve, unless you decide otherwise (§7).

**Figures (from the existing plan, re-based on MAIAC and paired):** the ladder schematic; the
paired estimation plot of background minus first two under each loss (the key figure); the
station-count saturation curve; the GHAP-vs-MAIAC inversion; the six pooled-versus-paired
reversals; the spatial-null forest plot with detection limits; the instrument-class census.

---

## 6. What is left to do for Paper 1, and why

| # | task | why | who |
|---|---|---|---|
| 1 | Tokenise F.113 and F.114 as claims in `build_claims.py` | the paper must quote generated numbers, never typed ones (gotchas #90, #94) | me |
| 2 | Cluster-bootstrap A3 and B7 (network × country clusters) | F.104 showed pooled intervals widen 1.45–1.97×; the loss result must survive it | me |
| 3 | Pair the remaining between-group claims (coastal, temperate `Bud0`, LCS vs reference weights) or drop them | same failure class as A5 | me |
| 4 | Update `registrations.json`: `z89kt` P4 not supported | the registry feeds every tally; it must match the ledger | **your call**, then me |
| 5 | Correct the draft's eleven defects (§4) and re-base every number on MAIAC | the draft currently asserts things the evidence does not support | me or the Paper 1 session |
| 6 | Fix the rung definitions to the panel as built (stations 3–6; same-network outer-ring background) | the spec and the panel differ (inventory flag) | me |
| 7 | Install `dabest`, `ptitprince`; build the figures | hard rule: install the right tool | me |
| 8 | Verify ERL's word, figure and reference limits against the journal's current guide | hard rule: verify, never guess | me |
| 9 | Cite and position against Choi & Hummel 2026, Verghese 2022, Samrat 2025, EGU26-9786 | the novelty case rests on the distinction | me |
| 10 | Supervisor sign-off, authorship, ORCID; circulation to the four readers | the paper's first external read has never happened | **you** |

## 7. Decisions needed from you

1. **Does Paper 1 wait for the spatial learning curve?** It is registered, directly asks how much
   *spatial* skill each sensor buys, and is the natural completion of claim 5. Waiting costs wave 2
   (~7 h of Kaggle, plus the upload you postponed) and the summary run. Not waiting keeps Paper 1
   to the ladder and the four bounded nulls, with the curve as a follow-up note. **My
   recommendation: do not wait; submit the ladder paper and give the curve its own short
   registered-report paper,** because it has its own registration trail and its result may take
   either direction.
2. **Adopt the loss-first headline (§5) in place of the current draft's?**
3. **Record `z89kt` P4 as not supported?**
4. **Target:** ERL (short letter format) or a longer methods journal? The claims in §5 are six;
   ERL's letter format may force claims 5 and 6 into the supplement.

## 8. The wider list, for completeness (not Paper 1)

- **Data (the critical path for Paper 2 and W11):** CEA letter; Peradeniya's own sensor network;
  follow-ups to FECT and MOSDAC (due 2026-09-02).
- **Thesis:** you are writing a new one; the old A/B builds are not being corrected.
- **Spatial learning curve:** wave 2 postponed; then consolidate, summary, verdicts, X-T.
- **Housekeeping:** push local commits; `CONTEXT.md` over its limit; CLAUDE.md creeping above 900
  lines; Snakemake pilot and Vale rules (Tier 1 tooling) not started.
- **Deferred by choice:** forecasting (Paper 2 of the forecast line), webapp UI, Zenodo badge, W6.
