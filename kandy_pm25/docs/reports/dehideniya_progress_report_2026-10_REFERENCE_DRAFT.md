# [AI REFERENCE DRAFT — rewrite every sentence in your own words before sending]

# Progress report: what is an air-quality observation worth to a city without monitors?
**To:** Dr. Mahasen Dehideniya (data-science co-supervisor) · **From:** Daminda Alahakoon · **Date:** October 2026
**Attachments (suggested):** Fig. A `fig3b_like_for_like.png`, Fig. B `figS1_station_count.png`,
Fig. C `fig7b_spatial_noise.png` (all in `papers/paper1_information_budget/figures/`).

---

## What I would like from you
A critical review of the **method**, before I finalise the method paper and the thesis (submission next month). My
main supervisor and I agreed to settle the method first. A self-review of my code last week overturned one of my
headline results, and I would value your view on whether the corrected analysis is now sound and on the five questions
in Section 7. I am open to substantial changes.

## 1. The problem
Kandy has no public PM2.5 monitor. Before anyone buys instruments, it helps to know **how much each kind of
observation improves an estimate of a city's daily PM2.5**, starting from free global data only (weather reanalysis,
satellite aerosol, a map of the city's surface). This is a **value-of-information** question. I answer it on cities
that do have dense monitoring networks, by withholding most of their stations and measuring what each added
observation buys, then ask what transfers to Kandy.

## 2. Data
- **Cities:** about 120 cities with at least 10 monitoring stations, from OpenAQ (worldwide) and the Chinese national
  network (CNEMC): a **discovery panel** (47 cities, used to develop the method) and a **confirmation panel**
  (76 fresh cities registered before their data were retrieved, 72 scored).
- **Target:** daily mean PM2.5 over a city's held-out stations; a station-day needs at least 18 valid hours.
- **Free predictors:** ERA5 weather (temperature, wind, boundary-layer height), MAIAC satellite aerosol, 60 static
  geography features computed on a grid over the urban centre (not at monitor sites, to avoid leakage), season.

## 3. Method
Each city's stations are split at random into **held-out stations** (scoring only) and **available stations**.
Estimators ("rungs") are compared, each allowed more information than the last:

| rung | information | model |
|---|---|---|
| Bud0 | free data only | gradient-boosted trees, **leave-one-city-out** (the city being predicted is never in training) |
| Bud1 | + first two stations | Bud0 recalibrated (intercept and slope) to the two stations |
| Bud2 | + stations 3–6 | the same recalibration on six stations |
| Bud3 | + background | regression on Bud0 and the daily 10th percentile of the remaining stations |

- **Score:** percentage reduction in RMSE at the held-out stations, per city.
- **Repeats:** 21 random station splits × 5 learner seeds per city, averaged before inference (a single split proved to
  be one noisy draw).
- **Inference:** median over cities with a **two-level cluster bootstrap** (cities nested in networks or countries).
- **Safeguards:** every test **pre-registered on OSF** before its data were retrieved; code **frozen by hash**; a
  synthetic dry run first; a **parity gate** (a re-run must reproduce the previous registered result exactly).
  Across 17 registrations, 105 predictions have been scored: 66 held, **23 were refuted**, and I report the refutations.

## 4. Registered results
**Confirmation on 72 fresh cities (OSF `ueyfr`)**, with the rungs as built:

| endpoint | result (median % RMSE gain [95 % cluster CI]) |
|---|---|
| first two stations, used to recalibrate Bud0 | +8.5 [3.1, 25.1] |
| stations 3–6, the same recalibration | +0.2 |
| background series, read on the day | +41.1 [26.8, 62.8] |
| background minus first two | +24.6 [4.1, 47.8] |
| the same on WHO-guideline exceedance days | +59.3 [33.9, 67.7] |
| dependence on latitude | not detectable (only 4 low-latitude cities) |

**Robustness, each registered separately:** a richer free baseline (adding CAMS PM2.5, fires, NO₂, rainfall, terrain;
Bud0 improved 13 %); three other learners (TabPFN, a 14-day GRU, trees with physics features — none beat gradient
boosting); and full station networks (up to 40 stations per city). The confirmation verdicts held each time; one
prediction of the richer-baseline test (that the first-station gain would shrink) was refuted.

## 5. A flaw I found in my own design, and what the corrected analysis shows
Reviewing my code as an outside referee would, I found that **the rungs do not use their stations the same way**.
The first stations only correct the level and scale of the free estimate, so their daily readings never reach a day's
prediction; the background is read on the day. The registered ordering "background beats the first local stations"
therefore compares two *uses*, not two kinds of observation. Registration and parity gates could not catch this: they
check that a test is run as written, not that it compares like with like.

I re-scored every stream the same way (post hoc; the same run reproduces the registered numbers to 3 × 10⁻¹⁴):

| comparison, every stream read on the day (Fig. A) | result |
|---|---|
| first two stations | **+58.8 % [44.9, 69.0]** (100 cities) |
| background, as registered | +57.7 % [46.4, 67.4] |
| background minus first two | **−0.22 [−0.60, +0.04]** points |
| the same, exceedance days | −0.11 [−2.49, 0.00] |
| full networks: background of ~10 stations minus first two | +2.5 [1.1, 3.7] (an effect of count, not kind) |

And the question a city actually asks, how many stations, read daily (Fig. B, 86 cities):

| stations | 1 | 2 | 3 | 5 | 8 |
|---|---|---|---|---|---|
| read every day | −42 % | −53 % | −56 % | −58 % | −61 % |
| used only to calibrate | about −11 % at every count |

Two further checks: refitting the free baseline leaving out each city's **whole network** (not just the city) makes the
registered gains slightly larger (first two 8.5 → 13.3 %), so leave-one-city-out flattered the baseline a little; and
the corrected comparison does not change. Because almost no fresh dense networks remain, I cannot register a fresh test
of the corrected design; I report it as a post-hoc re-analysis beside the registered result.

**Corrected conclusion:** what a monitor-less city gains is the **daily reading**: one station read every day removes
about 42 % of the error, two about 53 %, and the kind of station hardly matters. A short calibration campaign recovers
only about a fifth of that.

## 6. The within-city map, and the Kandy model
**Spatial learning curve** (registered `rqn4y`, re-run on full records `fu59b`; 23 cities in 9 countries, including
Bangkok): how well do 3, 5, 8 … stations rank a city's neighbourhoods? A post-hoc re-analysis narrowed the registered
reading (Fig. C):
- under the registered rule 15 of 23 cities "crossed" a free land-cover layer, but each city is scored on as few as 10
  held-out sites; the spread between cities is not larger than sampling noise, and **3 of 23** cross after a Holm
  correction;
- at 3–8 stations neither interpolation, the land-cover layer nor a satellite PM2.5 product ranks neighbourhoods
  usefully (rank correlation about 0.1); careful siting (cLHS) gains nothing — the registered summary of this test had a
  pooling bug that printed [0.00, 0.00], which I corrected (real interval about ±0.05);
- tropical cities cannot be distinguished from temperate ones; the honest detection limit is 0.35, not the 0.24 I
  registered.

**Kandy model** (a satellite-anchored hourly 1 km field built from two low-cost sensors): the local share of PM2.5,
which I had reported as 0.48 "fixed by physics", is a bound that moves between 0.43 and 0.49 with reasonable choices of
how the bound is computed; the sensors' humidity correction used a constant 80 % humidity, and hourly humidity shrinks
the modelled day-night swing by about 11 %. I am leaving the shipped model unchanged until the CEA monitoring data allow
a proper check against a reference instrument.

**For Kandy:** a few continuously reporting stations (CEA, NBRO, the university network) should give the city's level and
its day-to-day changes; they will not give a reliable neighbourhood map.

## 7. Questions for you
1. **The correction.** Is re-scoring every stream with same-day use the right way to repair the design, or would you
   frame it as data-denial (observing-system) experiments from data assimilation? Is it acceptable to report it
   post hoc beside the registered result, given that a fresh registered test is not possible?
2. **Inference.** Is the median of per-city gains with a two-level cluster bootstrap the right summary, or would a
   hierarchical (mixed-effects or Bayesian) model of the gains be better?
3. **Free baseline.** Pooled trees beat TabPFN and a GRU. For a target city unlike most training cities (Kandy), is
   there a domain-adaptation or importance-weighting approach I should try?
4. **Transfer to the tropics.** With so few low-latitude cities, how would you quantify how far the results can be
   trusted for Kandy (e.g. a covariate-shift diagnostic, or conformal intervals under shift)?
5. **Spatial mapping.** With 5–50 irregular sites per city and noisy per-city scores, is a hierarchical model of rank
   correlation against station count (city random effects) the right analysis, and is there a better mapping method
   than regression kriging?

## 8. Next steps
- Rewrite the thesis and Paper 1 around the corrected finding (daily reading vs calibration) and the narrowed spatial
  results; thesis submission next month.
- My main supervisor is arranging the CEA Kandy monitoring data, which will let me check the Kandy model against a
  reference instrument.
- The sensor-placement proposal waits until the method is settled; a review paper in atmospheric science (topic to agree).

## Appendix: where to look
OSF registrations: `ueyfr` (confirmation), `b379r` (baseline), `jea58` (learners), `mhgna` (full networks),
`rqn4y` and `fu59b` (spatial curve). The review and every re-analysis are logged in
`kandy_pm25/docs/review_remediation_plan_2026-10-06.md`; code and figures are in the project repository, which I can share.
