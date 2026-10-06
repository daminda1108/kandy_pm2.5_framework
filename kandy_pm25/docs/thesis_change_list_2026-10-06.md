# Thesis change list: bringing the chapters in line with the evidence (2026-10-06)

**What this is.** A claim-by-claim list of what each chapter of the thesis must change. It lists facts and
numbers only, and the author rewrites the prose himself. No thesis file was edited. Step D3 of
`review_remediation_plan_2026-10-06.md`.

**Basis.** Sources: `#writing/thesis/chapters/ch00..ch11*.md`, with every `{{claim:}}` token resolved from
`kandy_pm25/data/processed/modular/claims.json` (generated 2026-09-23). Line numbers refer to the source files.
They were checked against `CONTEXT.md`, the ledger (F.115–F.123), the six results records of 2026-09-28 → 10-05
and the external review (R1–R7, S1–S9, K1–K9).

**Three problems cut across every chapter. Fix these first.**
1. **The claims registry still points to the v1 ladder.** `step.*`, `stn.*`, `band.*`, `maiac.*` and
   `donor.*` are generated from `ladder_revalidated.csv`, `station_count_curve.json` and
   `independent_background_revalidated.csv` (F.85/F.102/F.54). All of these were superseded by F.115/F.116.
   Every ladder token in the thesis therefore prints a v1 or discovery number. `build_claims.py` needs new
   tokens read from `modular/ladder_v2/confirm_REGISTERED_*`, `rich_*`, `learners_*`, `fullnet_*` and
   `spatial_curve{,_full}/analysis/*`. Until that happens the claims gate will stay green on retired values
   (gotcha #90 family).
2. **The generated tables and figures carry the retired numbers too.** They must be rebuilt from new
   generators, not patched in prose.
   - Tables: `T7_1_ladder` (v1 Bud0a→Bud3 rungs), `T7_2_bands` (the band reversal, with "the ordering
     reverses in the deep tropics" in its note) and `T9_1_next` (first row: "A local observation, in
     preference to a regional one").
   - Figures: `fig:ladder`, `fig:clusterboot`, `fig:losses`, `fig:stationcount`, `fig:acquisition`,
     `fig:streams`, `fig:confounds`, `dia:decisiontree` (band branch), `fig:panel` (add the confirmation
     cities) and `fig:partition` (needs a fourth sensitivity axis).
   - `T7_5_registrations` regenerates from `registrations.json`, which is current (17 entries, 2026-10-05).
3. **Mark R1 as pending wherever the thesis says "background > local stations".** The rungs are not
   compared like for like. Bud1/Bud2 use stations only to fit an intercept and slope to Bud0; Bud3 uses the
   background stations' same-day reading (R1). Bud3 also uses more stations than Bud1 (R4), and the
   prospective arm assumes the background keeps reporting (R3).
   - The registered verdicts stand as registered.
   - Every sentence that ranks the background above local stations is marked **"PENDING L1 — rephrase as
     'as constructed'"** below.
   - Pilot (R1a, 10 discovery cities, exploratory): first two used as calibration **+4.1 %**, used same-day
     **+71.9 %**; background **+68.6 %**; background from two stations **+65.6 %**; background minus
     same-day first two **−1.8** (first two win in 60 % of cities).

Shorthand used below: **CONF** = confirmation (OSF `ueyfr`, F.117), **v2-D** = ladder v2 on the discovery panel
(F.116, exploratory), **FN** = full-network test A (`mhgna`, F.122), **SC** = spatial curve (`rqn4y` F.119;
full records `fu59b` F.123), **REV** = `review_remediation_plan_2026-10-06.md` log.

---

## Chapter 0: front matter and abstract (`ch00_front.md`)

| location | current text | problem | replacement content | source |
|---|---|---|---|---|
| ch00:53–54 | "across 48 cities in 29 countries and 28930 city days" | Discovery panel only. It is now exploratory, and the confirmation set is missing. | Discovery: 47–48 cities (exploratory). CONF: 76 registered, 72 scored, 30 countries (29 + CNEMC), 50 temperate, 18 subtropical, 2 tropical, 2 deep tropical; 63/76 reference-dominated. FN: 75 cities, median 17 stations. | F.116, F.117, F.122 |
| ch00:55–57 | "Freely available geography … is worth 10.8 per cent … comparable to the first local instrument" | v1 sub-rung (Bud0a→Bud0b), not re-measured under v2. The comparison to "first instrument" uses v1 numbers. | Drop the comparison, or label the figure as v1 discovery (exploratory). The v2 Bud0 includes geography sampled at 40 random GHSL urban-centre points. Richer sensorless streams add +13.1 % [9.2, 16.2] to Bud0. First two stations, CONF: +8.5 % [3.1, 25.1]. | F.116, F.118, F.117 |
| ch00:57–58 | "The third through sixth monitors are worth 0.1 per cent" | v1 number. The meaning also changes under R2. | CONF H2: +0.22 [0.12, 0.50] (inside the registered ±1). FN: +0.46 [0.26, 0.73]. R2: an affine calibration with 2 parameters is already fixed by two stations, so a near-zero value is close to guaranteed by design. Say "stations 3–6 used as a recalibration add nothing", not "carry no information". | F.117, F.122, R2 |
| ch00:58–60 | "the first station buys 17.0 per cent and the second adds 0.01 points" | **RETIRED** (v1, in-sample shrinkage zeroed the second station). | v2-D: one station +14.5 % [8.4, 51.8]; a second adds **+0.93 [0.37, 1.50]** paired; 3–8 stations add +1.2 to +1.4 over one, then flat. "Saturation at one" is retired. | F.116 addendum |
| ch00:62–63 | "The largest single gain comes from a background series … at 40.6 per cent" | v1 value. Ranks background above local (R1). | CONF H3 +41.1 % [26.8, 62.8]; FN +46.0 [34.3, 63.2]. **PENDING L1 — rephrase as "as constructed".** | F.117, F.122, R1 |
| ch00:63–64 | "a stand-in built from each city's own outermost monitors" | v1 definition. v2 is a different construction (R7). | v2/CONF: the daily 10th percentile of the same network's other stations. Never call it "regional" or "rural". Check the wording against `ladder_v2.py:110-118`. | F.117, R7 |
| ch00:65 | "An independent network recovers 73 per cent of the gain" | **RETIRED**: a ratio of medians. | 71 % [44, 82] per city, paired (n 19). | F.115 |
| ch00:66–67 | "recovery falls to 37 per cent in the group the demonstration city belongs to" | n = 3, a v1 ratio of medians that was never re-derived. | Delete. If kept: "n = 3, not interpretable". | F.115 |
| ch00:71–73 | "reordering … moving one of the magnitudes by a factor of twenty" | **RETIRED** ("more than twenty times"). | v2-D: stations 3–6 add +0.54 [0.21, 0.80] without a background and +2.39 [1.49, 3.44] with one (about 4×). Background +34.4 after vs +31.8 before. Both conclusions are order-robust. | F.115, F.116 addendum |
| ch00:74–79 | "Within the deep tropics the panel supports an ordering in which local observations outperform the background" | **RETRACTED.** | v2-D deep tropics −27.4 [−47.8, +11.8] (n 12); the interval crosses 0, and the prospective arm gives −4.1 [−56.1, +1.3]. Exploratory, direction only. CONF M1 latitude slope +0.53 [−1.79, +1.49]: undetectable, with only 4 cities below 23.5°. Nothing is confirmed for Kandy's band. | F.115–F.117 |
| ch00:77 | "That group holds thirteen cities" | Belongs to the retracted claim. | n 12 under v2. Delete along with the claim. | F.116 |
| ch00:81–85 | "Local observation wins on average daily error. The background stand-in wins on the dirtiest ten per cent" | The loss-dependent flip was a v1 deep-tropical result. Pooled CONF does not show it. | CONF: background > first two on RMSE (H4 +24.6 [4.1, 47.8]), on the tail (+54.2 [31.0, 66.7]) and on exceedance (H5 +59.3 [33.9, 67.7]). First two do nothing detectable on high days (tail −2.66 [−10.31, +3.74]). **PENDING L1.** | F.117, R1 |
| ch00:88–90 | "assigns 0.483 … a figure fixed by a physical consistency constraint rather than assumed" | Overstated (K3). Also built on UTC days (K2). | f is a **bound under a non-negativity cap**. Production 0.483 (UTC day, daily minimum). Local day 0.492; second-lowest hour 0.455; 3-hour running minimum 0.456; 10th percentile 0.433. So f ≈ 0.43–0.49 across these choices, and 0.489–0.547 across window forms. Quote "about 0.45–0.5, a bound under the cap". | REV K-a/K-c, F.108 |
| ch00:96–100 | "agreeing to 0.7 and −2.6 per cent in two independent years" | Keep, but add the baseline (K9/K-e). | GHAP at the same pixel: 17.6 / 18.8 against observed 19.6 / 22.7 (−10 % / −17 %). One site, two years, instrument undocumented. | REV K-e |
| ch00:after 117 | (missing) | The abstract has no spatial-curve result. | See New material §E: "a handful of reference stations is the right order of magnitude", now weakened by the reanalysis (Holm: 3/23 cities cross). | F.123, REV S-b |
| ch00:119–125 | "The neighbourhood-scale map is not validated" | Fine. | Keep. | — |

## Chapter 1 (`ch01_weather_and_air.md`)

| location | current text | problem | replacement content | source |
|---|---|---|---|---|
| ch01:97–98 | "Freely available geographic data is worth about as much as the first monitor a city buys" | v1 comparison. | As ch00:55. | F.116/F.117 |
| ch01:98–99 | "The second monitor onward is worth nothing that can be measured" | **RETIRED.** | Second station +0.93 [0.37, 1.50] (v2-D). Stations 3–6 +0.22 (CONF), which is close to zero by design (R2). | F.116, F.117, R2 |
| ch01:99–101 | "The largest single gain comes from a background series … a rural monitor serves no constituency" | R1/R7. | Same-network 10th percentile, +41.1 (CONF). **PENDING L1 — "as constructed"**. Not a rural monitor. | F.117, R1, R7 |
| ch01:101–103 | "the ordering … reverses between latitude bands, so the advice … is the wrong advice in the band" | **RETRACTED.** | Latitude dependence is undetectable (M1). The inversion is exploratory (−27.4 [−47.8, +11.8]). | F.116, F.117 |
| ch01:105–107 | "The ordering above reverses again when it is scored on episode days" | v1 deep-tropical result. | CONF pooled: the background ranks higher on every loss. First two help on ordinary days only. **PENDING L1.** | F.117 |
| ch01:113–116 | "the latitude ordering is a difference between bands" | No band difference is established. | "Latitude dependence is undetectable with 4 low-latitude confirmation cities." | F.117 |
| ch01:140–145 | "every city in the validation panel is a valley or a basin" | False for the ladder panels. The CONF panel was selected on metadata only (prereg §2), with no terrain rule. The valley/basin statement holds for the 10-city scorecard. | Separate the three panels: 10-city model scorecard (valley/basin), ladder discovery (check), CONF 76 (no terrain criterion; mainly temperate and regulatory). Scope sentence per R6: 4/72 tropical, median reference fraction 1.0, Kandy tropical and low-cost. | prereg_ladder_v2_confirmation §2, R6 |

## Chapter 2 (`ch02_why_not_kandy.md`)

| location | current text | problem | replacement content | source |
|---|---|---|---|---|
| ch02:46 | "a city of roughly four hundred thousand people" | **RETIRED** (no source). | 98,828 residents in the Kandy MC (2012 census); about 389,000 weekday commuters (World Bank 2020). 422,314 is the WorldPop count of the 15 km domain, not the city. | CONTEXT §2 |
| ch02:56–59 | "Chapter 7 reports every result stratified because of it" | The confirmation cannot stratify. | CONF has 4 low-latitude cities, so band results stay exploratory (M1 undetectable). | F.117 |
| ch02:71–72 | "Chapter 7 gives the exposure and burden estimates that follow … with their intervals" | The burden is not a result (F.110). K7. | Exposure: §7.11 (+9 %, 21.0 → 23.0). Burden: Appendix E only, as an illustrative projection. | F.110, K7 |
| ch02:84–88 | "assigns 0.483 … derived in Chapter 6 from a physical constraint rather than assumed" | K3. | "A bound under a non-negativity cap, about 0.45–0.5 (0.43–0.49 across day-boundary and daily-minimum choices; 0.489–0.547 across window forms)". | REV K-a/K-c |
| ch02:93–94 | "local action worth substantially more than the quarter this project previously assumed" | Fine in direction. | Keep. Attach the f range. | — |
| ch02:125 | "The answer for Kandy is not the answer that the global average would give." | Rests on the retracted inversion. | "For Kandy's band nothing is confirmed. A local station network (CEA) and a background series (NBRO) are complementary, not ranked." | F.116, F.117 |

## Chapter 3 (`ch03_what_is_known.md`)

| location | current text | problem | replacement content | source |
|---|---|---|---|---|
| ch03:91–94 | "a linear model collapses, and reports the value of a monitor as roughly four times" | v1 (F.88). | F.115: across HGB, shallow HGB, RF and Ridge, the background gain is 36.8–39.8 % and the 3–6 null holds, but the first-two gain varies 22.5–41.3 % with baseline weakness. F.120 (CONF): with TabPFN Bud0 is 11.1 % worse [−50.9, −1.1], and the first two then read +18.6 %. | F.115, F.120 |
| ch03:101–104 | "Chapter 5 records five … and Chapter 8 records a sixth" | Out of date. | Seven nulls on the spatial pattern (6udm3 is the seventh), plus the spatial curve (F.119/F.123). | F.111, F.119 |
| ch03:153–154 | "free terrain data and a rural monitor and a satellite retrieval are compared on one axis" | R7. | "a background series built from the same network". | R7 |
| ch03:182–186 | "That the ordering … differs between latitude bands, and that a monitor-trained covariate deflates … the rung above" | **Both RETIRED** as findings. | The latitude ordering is exploratory (F.116/F.117). GHAP "deflation": paired, the first two read +2.28 [−0.59, +16.85] and the claim is retired. What survives is that a monitor-trained covariate tilts the ordering toward the background: background − first two −5.53 [−16.84, −1.45]. New findings to name instead: the CONF verdicts (H1–H5) and their robustness (F.118/F.120/F.122). | F.117 addendum |
| ch03:188–195 | "the same contamination … displaces the effect onto a neighbouring term" | Overstated as found. | Restate as the F.117 addendum: the ordering is tilted, and the first-station difference is not resolved. | F.117 addendum |

## Chapter 4 (`ch04_what_there_was.md`)

| location | current text | problem | replacement content | source |
|---|---|---|---|---|
| ch04:55–58 | "Collectively they are worth 10.8 per cent … comparable to the first local instrument" | v1. | As ch00:55. | F.116 |
| ch04:71–72 | "covering 48 cities in 29 countries" | Discovery only. | Add CONF 72/76 (30 countries) and FN 75. | F.117, F.122 |
| ch04:76–77, 93–94 | "Every member is a valley or a basin, chosen so that the physical setting resembles the target" | Not true of CONF. Check whether it holds for discovery. | CONF chosen on metadata only (≥ 10 locations, ≥ 30 km from any drawn city, ≤ 4 clusters per country). No terrain rule. | prereg §2 |
| ch04:96–98 | "the association between instrument class and latitude band" | The v1 class split was wrong (CNEMC classed as LCS). | Corrected discovery class split 31 ref / 16 LCS (was 20 / 27). CONF 63/76 reference. Recompute the band × class contrast. | F.115 |
| ch04:119–122 | "the regional background that Chapter 7 measures as the largest single gain" | R1/R7. | NBRO = a genuine regional series, never measured by the ladder. The ladder's background is a same-network proxy, and an independent network recovers 71 % [44, 82] of it. **PENDING L1.** | F.115, R1, R7 |
| ch04:62–66 | (FECT sensors) | K1 missing. | The Barkjohn correction uses a constant RH = 80 % (`calibrate_fect.py:123,264`). With hourly ERA5 RH, the diurnal peak/trough falls from 1.82 to 1.62 (about 11 % less swing). | REV K-b |

## Chapter 5 (`ch05_what_failed.md`)

| location | current text | problem | replacement content | source |
|---|---|---|---|---|
| ch05:212–217 | "the constraint that eventually resolved the partition … not sensitive to the one free parameter" | K3/K2. | The cap binds in 49–75 % of hours. f ≈ 1 − mean(daily min T)/mean(T), so it is a function of T's amplitude. The minimum of 24 noisy values is biased low (−0.02 to −0.05). Production uses UTC days (+0.009 under local days). Range ~0.43–0.49. | REV K-a/K-c, K3 |
| ch05:233–234 | "The headline first rung fell from a superseded value to 17.8 per cent" | History stops before F.115. | Continue the history: F.115 put it at 14.95 % (GHAP); v2-D +21.8 [10.5, 52.9]; CONF **+8.5 [3.1, 25.1]**, less than half of discovery. | F.115–F.117 |
| ch05:236–241 | list of audit defects | Misses the largest audit. | Add the F.115/F.116 defects: CNEMC unbanded and classed as LCS; city 3147 still in two scripts; silent `except` loops; four unpaired verdicts; chunking that never requested window heads or tails (+1,575 city-days, +5 %); geography averaged over scoring sites (sites ~50 % denser); **the headline was one split and one seed** (the inversion's interval excludes 0 in 3/20 splits; the seed alone moved first-two 11–23 %). Add the review bugs: X5 pooled over site-independent estimators ([0.00, 0.00]); coherence cap on UTC days. | F.115, F.116, REV S-a, K2 |
| ch05:303–317 | "pattern across the eight" | Could carry the strongest instance. | Optional: discovery → registered confirmation as the strongest case of "declare first". | F.117 |

## Chapter 6 (`ch06_the_model.md`)

| location | current text | problem | replacement content | source |
|---|---|---|---|---|
| ch06:137–144 | "The interval was correctly scaled and incorrectly centred" | K5: the alternative reading is not stated. | The one-sided miss (25.7 % below, 1.9 % above), together with 3 of 4 independent records below the model, is evidence of an **upward level bias** at the FECT/LCS points. NBRO disagrees (+0.7 / −2.6). Also K6: intervals omit κ, f, the emission proxy and the calibration slope; the background band is hard-coded 0.70/1.25. | K5, K6 |
| ch06:185–187 | "The sensorless tier … carries 68 predictors, of which 60 are static geography" | v1 Bud0c. | v2 Bud0: geography from 40 random GHSL urban-centre points (not monitor sites), ≥ 18 h station-days, 5 learner seeds. Rich variant +13 features (CAMS NRT, terrain, FIRMS, TROPOMI NO2, IMERG, day of week). Read the v2 count from code. | F.116, F.118 |
| ch06:243 (heading) | "The partition, which is a constraint rather than a choice" | Contradicts ch06:261–263 ("a modelling choice") and K3. | Heading along the lines of "a bound under a non-negativity constraint". | K3 |
| ch06:253–254 | "cap each day at (1 − F_min) times that day's minimum hourly total" | K2: the day is UTC. | Days are UTC (05:30–05:29 local), which splits the night. Local-day f 0.492 vs 0.483. Fix due at the next rebuild (K-a). | REV K-a |
| ch06:274–286 | "Across the anchored years the local fraction is 0.483 … The result does not depend on the free parameter." | A fourth sensitivity is missing. | Add the daily-minimum estimator: UTC/local 2nd-lowest 0.455/0.469, 3-hour running minimum 0.456/0.468, 10th percentile 0.433/0.446. Hourly-RH calibration leaves a sensor-level f proxy unchanged (0.547 → 0.545). The cap binds in 49–75 % of hours. | REV K-a/K-b/K-c |
| ch06:282 | "The production form uses a calendar-day minimum and gives 0.489" | Inconsistent with the headline 0.483 (production path, `f_sensitivity.csv` reproduces B exactly). | Explain 0.489 (reimplementation) vs 0.483 (production), or quote one. | REV K-a, F.43 |
| ch06:303–308 | "The partition therefore has three separate sensitivities" | Now four. | Anchored years 0.466–0.501 · F_min 0.482–0.509 · window form 0.489–0.547 · day boundary and minimum estimator 0.433–0.492. `fig:partition` needs a fourth row. | F.108, REV K-c |
| ch06:342–349 | "between 9.1 and 48.3 per cent … bounded well below half" | The upper bound equals f, so it moves with f. | The upper end becomes ~43–49 % across the K-c choices. The direction of the statement holds. | REV K-c, F.98 |
| ch06:352–366 (6.7) | known limits | K1/K4/K8 missing. | Add: constant-RH humidity correction (K1). FECT trains T, sets its conformal width and sharpens it; van Donkelaar sets both level and B (K4). Sharpening assumes hour × month factors are independent and pools a valley sensor with a ridge sensor (K8). | K1, K4, K8 |
| ch06:277–278 | "Sweeping F_min from zero to 0.08, a fourfold change" | 0 → 0.08 is not fourfold; Appendix A gives 0.02. | Fix the arithmetic: 0.02 → 0.08 is fourfold. | App A |

## Chapter 7 (`ch07_making_sure.md`): the most affected chapter

| location | current text | problem | replacement content | source |
|---|---|---|---|---|
| ch07:20–23 | "48 cities … 29 countries … 28930 city days … median 4.0 withheld … 520 scored days" | v1 discovery frame. | v2-D (47 cities, +1,575 city-days after the chunking fix) as exploratory. CONF: 72 scored, 30 clusters, 6–21 splits per city, background rung in 68. FN: 75 (72 under the cap), median 17 stations. | F.116, F.117, F.122 |
| ch07:44–47 | "What transfers is an ordering, not a magnitude." | The ordering is confirmed only for a temperate, regulatory population. | CONF H4 +24.6 [4.1, 47.8], background > first two, **as constructed (PENDING L1)**. Scope: 50/72 temperate, 63/76 reference (R6). | F.117, R1, R6 |
| **ch07:49–53** | "read against the deep-tropical band, which Section 7.3 shows reverses the pooled result … A pooled number would be the wrong number twice over" | **RETRACTED** (task note T1). The low-cost-class argument relied on the v1 class split. | No band reversal is established (v2-D −27.4 [−47.8, +11.8], prospective −4.1; CONF M1 undetectable). Class split corrected to 31/16. Kandy reading: confirmed pooled verdicts plus "nothing confirmed for the deep tropics". | F.115–F.117 |
| ch07:55–58 | "Every panel city is a valley or basin … a selection criterion" | Not true of CONF. | As ch04:76. | prereg §2 |
| ch07:60–64 | "the transfer rests on Kandy resembling its band" | The band result is gone. | Transfer rests on the CONF population; Kandy lies outside its bulk (R6). | R6 |
| ch07:113–117 | table: first two 17.8 [4.6, 23.5]; 3–6 0.1 [0.0, 0.9]; background 40.6 [26.7, 45.2] | v1, city bootstrap. | CONF cluster: H1 +8.53 [3.07, 25.12]; H2 +0.22 [0.12, 0.50]; H3 +41.10 [26.77, 62.84]; H4 +24.58 [4.07, 47.80]; H5 +59.33 [33.93, 67.73]. City bootstrap: H1 [3.47, 18.58], H3 [33.7, 52.6], H4 [10.3, 37.5], H5 [43.1, 67.0]. v2-D: +21.8 [10.5, 52.9] / +0.54 [0.21, 0.80] / +34.4 [15.4, 62.2]. | F.116, F.117 |
| ch07:119–124 | "The one that is not wide is the one the thesis leans on hardest … absence … established far more tightly" | R2: close to guaranteed by design. | Two stations already determine an intercept and slope over hundreds of days. The small H2 says "more stations do not improve a recalibration", not "no information". | R2 |
| ch07:131–147 | "48 cities fall into 29 clusters … wider by 1.45 / 1.56 / 1.59" | **RETIRED.** | 47 cities in **28** clusters; widening **1.15–2.21×**. Cluster bootstrap is primary everywhere. CONF: 30 clusters. | F.115 |
| ch07:157–162 | "The background remains the largest gain with a lower bound of 22.3" | v1, R1. | CONF H3 lower bound 26.77. **PENDING L1.** | F.117 |
| ch07:164–171 | "deep-tropical … paired interval is 7.0 to 50.1 … the recommendation for Kandy rests on" | **RETRACTED.** | As ch07:49. | F.115, F.116 |
| ch07:173–182 | ICC 0.82–0.99; 23 of 29 singleton clusters; 0.564 / 0.285 | Computed on the old clustering. | Recompute on 28 clusters (v2), or drop. | F.115 |
| ch07:186–188 | "Static geography … buys 10.8 per cent … comparable to … the first local instrument" | v1. | As ch00:55. | F.116 |
| ch07:190–193 | "The annual satellite level buys 7.6 per cent" | v1 rung, not part of the v2 ladder. | Label it v1/exploratory, or drop it. | F.116 |
| ch07:195–197 | "Additional monitors add almost nothing … not small but absent … the most estimator-robust result" | v1 value plus R2. | +0.22 (CONF) / +0.46 (FN); interpret per R2. F.120: H2 holds under all three learners. | F.117, F.120, F.122 |
| ch07:212–216 | four-loss table (24.6/22.8/8.6/0.0; 0.12/0/0/0; 37.1/38.0/38.4/28.0) | v1 MAIAC. | CONF secondary (recon / prospective): first two, tail −2.66 [−10.31, +3.74]; first two, exceedance −0.51 [−7.61, 0.00]; 3–6, exceedance 0.00 (74 % of cities exactly 0); background, exceedance +52.54 [32.75, 67.28]; background − first two, tail +54.15 [31.04, 66.66]; H5 +59.33. There is no MAE column in v2. | F.117 |
| ch07:218–226 | "A background series is the largest gain under every loss, and its largest value of all is on episode days" | v1, R1. | The direction agrees with CONF. **PENDING L1 — "as constructed"**. | F.117, R1 |
| ch07:228–250 | deep-tropical paired 33.3 / 40.8 / −20.8 / −15.9 [−38.1, −1.54]; "the ordering therefore flips sign between average-day and episode losses" | **RETIRED** (one split, one seed). | The pooled CONF shows no flip: the background ranks higher on RMSE, tail and exceedance. Deep tropics exploratory only. | F.113, F.115–F.117 |
| ch07:252–258 | "⚠ One fragility … includes zero where the recorded one excludes it" | Superseded. | F.115: over 20 splits, 3/20 exclude 0; split-averaged −28.7 [−36.3, −7.7], −25.0 [−36.2, +8.3] under the 18 h rule; v2 −27.4 [−47.8, +11.8]. Demoted to exploratory. | F.115, F.116 |
| ch07:271–286 | "A single station buys 17.0 … the second station adds 0.01 … The saturation is at one, not at two … deep tropics … 20.0 … 0.22 … 6 of 13" | **RETIRED.** | v2-D: one station +14.5 [8.4, 51.8]; second +0.93 [0.37, 1.50] paired; 3–8 add +1.2 to +1.4 over one, then flat. Band rows not recomputed; drop them. | F.116 addendum |
| ch07:296–304 | temperate "12.9 … paired 0.14 … 3 of 7" | v1 numbers. The lesson stays. | Keep the lesson (difference of medians). Recompute the example on v2, or cite the F.103 siting case instead. | gotcha #91 |
| ch07:306–312 | "temperate interval runs to 6.52 … deep-tropical upper bound 2.9" | v1. | Drop, or replace with the v2 interval above. | F.116 |
| ch07:327–329 | "A background series is the largest single gain measured. At 40.6 per cent" | v1, R1. | CONF H3 +41.1; FN +46.0. **PENDING L1.** | F.117, F.122 |
| ch07:334–336 | "the tenth percentile of the target city's own outer-ring monitors, five to fifteen kilometres from the centre" | v1 construction. | v2: daily 10th percentile of the same network's other (non-held, non-rung) stations; check the radius in `ladder_v2.py`. R4: Bud3 uses all remaining stations against two for Bud1. FN: verdicts survive full networks (the background is larger with more stations). | R4, R7, F.122 |
| ch07:350–356 | "own outer ring 40.6 … donor 89 km … 73 per cent … about three quarters" | **RETIRED.** | 71 % [44, 82] per city paired (n 19); paired −13.8 pp [−20.6, −7.8]. | F.115 |
| ch07:360–362 | "from 84 per cent at 62 kilometres to 57 per cent at 152" | Recomputed. | 83 % at ~62 km, 45 % at ~152 km. | F.115 |
| ch07:367–371 | "from a recorded 79 per cent to 73" | Incomplete. | 79 → 73 (ratio of medians) → **71 paired**. | F.115 |
| ch07:373–380 | "deep-tropical cell … recovery falls to 37 per cent … reason to prefer the band-stratified recommendation" | n 3; the recommendation is retracted. | 20/47 cities have a donor, 4 of them deep-tropical. Drop the 37 % and the band preference. | F.115 |
| ch07:382–383 | "Chapter 9 lists one even though it ranks second for Kandy" | No ranking survives for Kandy. | "complementary, not ranked". | F.116 |
| ch07:399–400 | "The redundancy null survives and the background remains the largest single gain." | P4 refuted when paired. | z89kt verdicts recomputed: P1 refuted, P2 refuted, P3 not adjudicable, **P4 refuted (+0.02 [−12.63, +7.15])**, P5 held in direction → 1 held / 3 refuted / 1 not adjudicable. Keep −1.04 [−5.5, +4.3] and −0.30. | F.113, F.115 |
| ch07:411–415 | "deep-tropical margin … 16.4 to 8.61 … least robust quantity the band recommendation rests on" | Exploratory now. | Keep only as an illustration of instability (F.115/F.116 list 7 things that move it). | F.115 |
| **ch07:417–507 (§7.3 entire)** | "The recommendation inverts in the tropics" | **RETRACT the section as a finding.** 21.9 vs 8.5; 43.7 vs 10.3; 4.2×; paired 3.6 [−14.3, 36.3] 54 % and 33.3 [7.0, 50.1] 77 %; "contaminated covariate destroyed the significance" — all retired. "Sums to 37 … 11 from a single network carry no band" is also wrong after F.115, because CNEMC is now banded (`city_meta.attach_meta`). | Rewrite as exploratory: v2-D −27.4 [−47.8, +11.8] (n 12), prospective −4.1 [−56.1, +1.3], GHAP +2.2. CONF M1 +0.53 [−1.79, +1.49]; the 4 low-latitude CONF cities have H4 medians −9.6 and −7.7 (descriptive). Keep the "latitude is a label" paragraph and the seasonal-amplitude mechanism as untested ideas. | F.115–F.117 |
| ch07:487–489, 643–672 | "differs by a factor of 77.0 against 25.0 per cent low-cost units" | v1 class split (CNEMC misclassed). | Recompute the band × class split with `city_meta`. Discovery 31 ref / 16 LCS. "It does not overturn the inversion": there is no inversion to overturn. | F.115 |
| ch07:525–541 | "spread … 2.5 points. Ridge … 50.2 … against 11.7 … 3–6 spread 0.46" | v1 (F.88). | F.115 (v1 corrected): background 36.8–39.8 % and 3–6 null robust across HGB/shallow HGB/RF/Ridge; first-two 22.5–41.3 %. F.120 on CONF: all 12 directional verdicts hold under TabPFN 8.5.0, a 14-day GRU and HGB + physics. Bud0 vs HGB: TabPFN −11.1 [−50.9, −1.1], GRU +1.8 [−4.3, +8.9], physics +2.0 [−0.3, +4.6]. H4 holds under GRU +25.7 [9.3, 49.3] and physics +25.0 [3.1, 48.3], not under TabPFN +8.3 [−5.4, +40.6], where first two read +18.6. | F.115, F.120 |
| ch07:562–576 | "38.4 / 37.6 … 0.23 / 2.97 … more than twenty times" | **RETIRED.** | v2-D: background +34.4 [15.4, 62.2] after 3–6 vs +31.8 [13.4, 61.5] before; 3–6 +0.54 without vs +2.39 [1.49, 3.44] with. | F.116 addendum |
| ch07:551–556 | "background enters as a second regressor whose coefficient is fitted against local station data" | Must be reconciled with R1/R3. | State that Bud3 uses the background's same-day reading while Bud1/2 do not (R1), and that the prospective arm assumes the background keeps reporting (R3). L1 will add symmetric arms (L2s, BGall, BG2). | R1, R3 |
| ch07:594–616 (§7.5) | "fused 5.37 / raw 5.97; rung above 17.8 vs 23.6 … Contamination … deflates the rung above it" | **RETIRED** as a paired result. | v2-D paired MAIAC − GHAP: first two +2.28 [−0.59, +16.85] (MAIAC higher in 65 % of 46); background −1.52 [−3.84, −0.46]; background − first two −5.53 [−16.84, −1.45]. What survives: a monitor-trained covariate **tilts the ordering toward the background**. | F.117 addendum |
| ch07:637–641 | "first rung moves from 22.3 to 19.6 … band ordering is unchanged" | v1. "Band ordering" is no longer a result. | Label it v1, or drop it. | F.116 |
| ch07:676–685 | "shrinkage weight … 0.575 … 0.35 … 1.64 times" | v1 in-sample shrinkage; v2 cross-fits the weights. | Recompute the weights by class under v2, or drop. | F.116 |
| ch07:691 | "rather than the forty-eight where only the ladder was run" | Out of date. | 47 discovery + 72 CONF + 75 FN. | F.117, F.122 |
| ch07:724–732 | FECT 0.994 / 0.994 "confirming that the calibration was applied" | Fine. Add K4. | List the shared inputs: FECT → T, conformal width, sharpening; VanD → level and B. | K4 |
| ch07:739–753 | NBRO 19.7 / +0.7; 22.1 / −2.6 | Keep. Add the baseline. | GHAP at that pixel: 17.6 / 18.8 (−10 % / −17 %). The chain beats the off-the-shelf product at the one reference-like record (one site, two years). | REV K-e |
| ch07:755–759 | "A discrepancy remains open and is not resolved here." | K5. | Also report the review's reading: the one-sided coverage plus 3 of 4 records below point to an upward bias at LCS points. Add the K1 humidity mechanism, which lowers the diurnal swing by about 11 % (peak 1.337 → 1.287; trough 0.736 → 0.811). Not settled without CEA co-location. | K5, REV K-b |
| ch07:784–785 | "the cause is the change of support … rather than a failure of the calibration procedure" | Too confident (K5, K1). | Change of support **or** an upward level bias. Constant RH is a candidate mechanism. | K1, K5 |
| ch07:849–877 | "controlling for band removes the cities that carry no band … 46 / 35 / 11" | The description of CNEMC as bandless is out of date after F.115. | The registered result stands. Reword the explanation: CNEMC was unbanded in the frame used then. | F.115 |
| ch07:929–934 | "the ordering of that value differs between bands, and … the pooled recommendation is the wrong one" | **RETRACTED.** | Replace with: CONF H1–H5 (as constructed, PENDING L1); robust to baseline (F.118), learner (F.120) and station cap (F.122); latitude undetectable. | F.117–F.122 |
| ch07:936–941 | "Every city in it is a valley or basin … Two of the four bands rest on cells of seven cities" | Panel description wrong for CONF. | CONF scope per R6 (4/72 tropical). | R6 |

## Chapter 8 (`ch08_where_it_stops.md`)

| location | current text | problem | replacement content | source |
|---|---|---|---|---|
| ch08:219–226 | "IDW 0.19, GWR 0.0734, kriging 0.0483 … A city that has a network … ranks its own stations worse than a single free raster" | Must be reconciled with SC, where kriging or RK crossed the raster by the frozen rule in 11/18 and 15/23 cities. | The reanalysis (S-b/S-c) brings the two closer. At k = 3 skill is ≈ 0.10 for both raster and kriging. Holm-corrected crossovers 3/23 (full) and 3/18 (registered). Between-city heterogeneity is not significant on full records (Q p 0.06–0.26). State that the two analyses use different frames (LOCO ranking of all stations vs within-city held-out sites, H = max(10, n//3)). | F.119, F.123, REV S-b/S-c |
| ch08:262–270 | "deliberate siting scores −0.044 … 19 of 43" | F.103 is fine and is distinct from SC X5. Add the X5 erratum. | SC X5 per estimator, E3 cLHS − random: registered k = 3 +0.013 [−0.062, +0.061], k = 5 −0.019 [−0.042, +0.028], k = 8 −0.013 [−0.054, +0.002]; full k = 3 0.000 [−0.049, +0.046], k = 5 −0.024 [−0.042, +0.024]. Never quote the registered "0.00 [0.00, 0.00]" (a bug from pooling site-independent estimators). | REV S-a |
| ch08:286–291 | "The robustness check could not be run … a held-out third is 4" | SC ran a fixed held-out design. | SC: H = max(10, n//3), so 14/23 full-frame cities score on 10 sites (Spearman SE ≈ 0.33; S2). | F.123, S2 |
| ch08:356–361 | "given the globally available covariates … sub-kilometre structure cannot be placed" | Add the station-based side. | SC: reach ≈ 1 km. This is the resolution of the first distance bin, so do not quote it as a measured length (S5). X4 refuted on full records (London −0.28, Bangkok −0.57 within-cell ceilings). | F.119, F.123, S5 |
| ch08:387–389 | "Can a user rank neighbourhoods …? No. … 0.274" | Keep. Add the new benchmark. | GHAP 1 km at 1,506 SC sites: within-city rank +0.125 [−0.031, +0.297] vs built-up raster +0.097; paired GHAP − raster +0.018 [−0.143, +0.170]; kriging minus GHAP at k = 3/5/8: +0.012 / +0.002 / −0.017. Neither free products nor 3–8 stations rank neighbourhoods usefully (ρ ≈ 0.1–0.15). | REV S-e |
| ch08:398–401 | "The spatial rung … remains a declared design assumption" | Keep. Add the SC outcome. | See New material §E. | F.119, F.123 |
| new §8.x | (missing) | The spatial learning curve is absent. | See New material §E. | F.119, F.123 |

## Chapter 9 (`ch09_what_next.md`)

| location | current text | problem | replacement content | source |
|---|---|---|---|---|
| ch09:11–16, `dia:decisiontree` | "branch again on the group it belongs to, because Section 7.3 shows the ordering reverses" | Retracted. | Remove the band branch. Branch on the purpose (daily mean or exceedance) only as far as CONF supports, and **PENDING L1**. | F.117 |
| ch09:26–28 | "no rung of the ladder priced one [reference instrument]" | CONF is 63/76 reference-dominated. | The confirmed ladder mostly priced **reference** networks. Low-cost tropical networks are outside it by construction. | F.117 |
| ch09:30–34 | "Together they buy 10.8 per cent … comparable to the first instrument" | v1. | As ch00:55. | F.116 |
| ch09:41–46 | "a regional background … 40.6 … two local sensors 17.8 … deep tropical … 43.7 against 10.3 … 4.2 times" | **RETIRED** ("4.2×" must never be quoted). | CONF: first two +8.5, background +41.1, background − first two +24.6 (as constructed, **PENDING L1**). Deep tropics exploratory. | F.115–F.117 |
| ch09:48–51 | "For Kandy specifically, therefore, the first purchase is a local observation … 77 per cent" | **RETRACTED.** | "CEA local stations and an NBRO background are complementary, not ranked." The CEA case rests on the level discrepancy and calibration (measurement design). | F.116 |
| ch09:53–61 | scope paragraph ("within that group a local observation outranks the background stand-in") | Retracted. | Scope = the CONF population (mainly temperate and regulatory; R6). | R6 |
| ch09:63–74 | "the local advantage is 33.3 and 40.8 … −20.8 … −15.9 [−38.1, −1.54] … 38.4" | **RETIRED.** | CONF: the background ranks higher on RMSE, tail and exceedance. First two help on ordinary days only (tail −2.66 [−10.31, +3.74]). **PENDING L1.** | F.117 |
| ch09:76–85 | "The ladder measured two low-cost sensors, so it establishes that a local observation outranks a regional one in this band … 43.7" | Both premises are wrong now. | Keep the measurement-design argument for a reference monitor (level, calibration anchor). Delete the band sentence and the 43.7. | F.117 |
| ch09:87–99 | "a single station buys 17.0 … second adds 0.01 … one local observation captures essentially everything … most estimator-robust result" | **RETIRED.** | Second station +0.93 [0.37, 1.50]; 3–6 +0.22 by recalibration design (R2). For a **map**, SC on full records says "a handful (3–5) of reference stations is the right order of magnitude", which the review weakens (Holm: 3/23 cross). | F.116, F.123, R2, REV S-c |
| ch09:136–144 | "It ranks second for Kandy … recovered 73 … falls to 37 per cent on 221-kilometre donors" | Retired numbers and ranking. | Not ranked. 71 % [44, 82]. Drop the 37 / 221. | F.115, F.116 |
| ch09:156–165 | siting −0.044 [−0.0952, 0.118] | Fine (F.103). | Keep. Add the X5 erratum (see ch08:262). | REV S-a |
| ch09:167–175 | "it would sharpen the thesis's most policy-relevant result … ordering differs between bands" | There is no band result to sharpen. | Keep as an exploratory analysis idea, and say that CONF cannot see latitude (M1). | F.117 |
| ch09:248–254 | "this kind of contamination deflates the rung above it rather than inflating its own" | **RETIRED.** | "A monitor-trained covariate tilts the ordering toward the background (−5.53 [−16.84, −1.45]); the first-station effect is unresolved." | F.117 addendum |
| ch09:271–275 | "More monitors in the same city … for the reason given in Section 9.1" | The reason is retired. A map needs more than one station. | For a daily mean: 3–6 as recalibration add +0.22. For a map: SC (handful; reach ~1 km; GHAP ≈ kriging at k ≤ 8). | F.117, F.123, REV S-e |
| ch09:284–286 | "on evidence from forty-eight cities" | Out of date. | "registered on 72 fresh cities (ueyfr), robust to baseline, learner and station cap". | F.117–F.122 |
| ch09:288–294 | "The absolute concentration scale at Kandy is not independently validated" | Keep. Strengthen. | Add K5 (upward-bias evidence), K-e (GHAP −10/−17 % at NBRO), K1. | K1, K5, REV K-e |

## Chapter 10 (`ch10_software.md`)

| location | current text | problem | replacement content | source |
|---|---|---|---|---|
| ch10:98–100 | "a spatial learning curve that is registered and underway" | Out of date. | Scored 2026-09-28 (F.119; 7 held, 3 refuted, 1 not testable) and re-run on full records 2026-10-05 (F.123, X4 refuted). | F.119, F.123 |
| ch10:102 (`T7_5`) | (generated) | Must regenerate. | Registry: 17 entries (including amendments); 105 predictions over 14 run: 66 held, 23 refuted, 6 not tested, 10 two-sided or exploratory. `mhgna` and `fu59b` pending OSF approval. Add an erratum row for X5 (verdict stands, interval was a bug). | CLAUDE.md 2026-10-05, REV S-a |
| ch10:104–108 | "two dated amendments to the spatial learning curve" | Incomplete. | Amendments `4whsc`, `4qs9c` (D-8); deviations E-1 (CONF), B-1 (test B), D-6/D-7. | F.117, F.119, F.123 |
| ch10:159–163 | "It does not check that a number is meaningful" | Add the strongest examples. | The headline was one split and one seed (F.115). The X5 pooling bug passed every gate (S1). The cap ran on UTC days (K2). | F.115, S1, K2 |
| ch10 (new) | (missing) | The review is not described as a practice. | One paragraph: an external adversarial review (R1–R7, S1–S9, K1–K9) and what it changed. See New material §F. | REV |

## Appendices (`ch11_appendices.md`)

| location | current text | problem | replacement content | source |
|---|---|---|---|---|
| A:14 | "sensorless predictors 68, of which 60 are static geography" | v1. | v2 Bud0 count, read from code (urban-centre geography). | F.116 |
| B:19–21 | "registrations whose analyses have not run have predictions and no outcomes" | Nearly all have now run. | State which registrations still have no outcome by reading `registrations.json` (at least `ad3py`, the campaign, which is excluded from the thesis). Do not type the list by hand. | registrations.json |
| D table | 11 rows | Missing every change since 2026-09-19. | Add rows (recorded → regenerated): first two 17.8 → **+8.5** (CONF); first station 17.0 / second 0.01 → 14.5 / **+0.93**; deep-tropical inversion +33.3 [7.0, 50.1], "4.2×" → −27.4 [−47.8, +11.8], exploratory; "more than twenty times" → ~4×; donor recovery 73 → **71** paired; clusters 29 → **28**, widening 1.45–1.59 → **1.15–2.21**; GHAP "deflation" → retired; class split 20/27 → 31/16; z89kt 3 held/2 refuted → 1/3/1; registry 11 regs, 13/38 → current counts; f "fixed" → bound 0.43–0.49 (+0.489–0.547); X5 interval [0.00, 0.00] → per-estimator values; SC crossover 15/23 → 3/23 (Holm). | F.115–F.117, REV |
| D:76 | "79 per cent → 73 per cent" | Superseded again. | → 71 [44, 82] paired. | F.115 |
| E:112–117 | "431 attributable deaths … 237 to 632 … 18.2 per cent … 300 avoidable" | K7 is not stated. | GEMM is defined for ages 25+ with age-specific baselines. It was applied to the all-age crude death rate over the whole 422 k WorldPop domain (`health_burden.py:45-50,102`). A corrected estimate needs GBD 2021 Sri Lanka age-specific rates (blocked, user download). Keep "response-function-conditional" and the illustrative framing. Say that 422 k is the domain, not the city. | K7, REV K-d |

---

## (1) Claims that are fine and should be KEPT

- The decomposition, conservation, the increment split (38.8 % / 53.9 % → 0.0 %), the ε floor, and the gauge
  statement that unit mean does not pin `B` (ch06:40–48, F.108).
- The four-property wording (ch06:189–217) and the T-lock at 0.39–0.56 %.
- Dilution exponent 0.054. Kandy relief 850 m. 6 vs 65 reference-dense clusters (10.8×). WHO lines.
  Seneviratne 7.6 % / 14.1 % and the refutation of "~90 % vehicular".
- The FECT self-check framed as calibration (0.994). NBRO +0.7 / −2.6 %, with the K-e addition.
- `s_rep` too small by 2.61× on the panel and ≥ 16.9× at Kandy. Interval coverage 72.4 / 25.7 / 1.9 / 92.2,
  with the K5 caveat added.
- Chemistry: continental 0.447 vs marine 0.324; the species test is untested rather than refuted. The 9.1–48.3 %
  bound keeps its direction; the upper end moves with f.
- Exposure: 21.0 / 21.9 / 23.0, +9 %. The burden stays in Appendix E as a response-function-conditional
  projection.
- Chapter 8 core: paired garden sites 27.5× vs 1.0×; registered refinement null (S1a/S1c); dispersion lowers
  rank 0.371 → 0.274 (3/10); within-cell 1.22 > between-cell 1.05; radius peak 2.4 km.
  - 2jyfg: 0.286, +0.022, 25/46, δ 0.13.
  - 6udm3: paired −0.028, partial 0.191 [−0.007].
  - F.105 tournament and the −0.833 artefact account.
  - F.103 siting −0.044 [−0.095, +0.118], 19/43, which is a separate test from X5.
- Precipitation null: −1.04 [−5.5, +4.3] and −0.30 paired. Colombo donor 0.604 vs 0.822 at 93.9 km.
- Chapter 5 accounts 5.1–5.6 and 5.8; the 0.65–0.96 retrospective power. Chapters 1 and 3 framing on value of
  information, OSEs and Choi 2026 (with the R7 relabel). The ch09:288–294 statement that the level is not
  validated. The ch10 machinery description.

## (2) New material the thesis lacks entirely

**A. Ladder v2 and the verification pass (F.115/F.116).**
- Design: per-city effect = median over 21 station splits; Bud0 = median over 5 learner seeds; cross-fitted
  shrinkage; geography from 40 random GHSL urban-centre points; ≥ 18 h station-days; two-level cluster
  bootstrap; parity with v1 to 1e-9.
- Discovery (exploratory): +21.8 [10.5, 52.9] / +0.54 [0.21, 0.80] / +34.4 [15.4, 62.2]; background − first
  two +4.8 [−23.6, +52.1]; deep tropics −27.4 [−47.8, +11.8].
- Defects found: as listed under ch05:236.

**B. Registered confirmation (OSF `ueyfr`, F.117).**
- Panel: 76 fresh cities registered before any PM2.5 was retrieved; 72 scored; frozen `e6b744b`; ingest loss
  0.00 %.
- Endpoints: H1 +8.53 [3.07, 25.12]; H2 +0.22 [0.12, 0.50]; H3 +41.10 [26.77, 62.84]; H4 +24.58
  [4.07, 47.80] (background > first two); H5 +59.33 [33.93, 67.73]; M1 +0.53 [−1.79, +1.49], undetectable.
- The prospective arm reproduces every verdict.
- By network: OpenAQ only H4 +11.46 [1.35, 33.33]; CNEMC only +63.9.
- Scope: 50/72 temperate, 63/76 reference. **The H4/H5 ordering is "as constructed, PENDING L1" (R1).**

**C. Robustness, all registered.**
- Richer baseline (`b379r`, F.118): Bud0 +13.1 % [9.2, 16.2]. Under it: first two +8.9 [3.6, 15.3], 3–6
  +0.24, background +35.6, H4 +21.7 [3.8, 40.7], exceedance +45.4 [27.9, 58.3]. 6/7 as registered; R3
  refuted (paired −0.7 [−7.1, +1.7]).
- Learners (`jea58`, F.120): numbers under ch07:525.
- Full networks (`mhgna`, F.122; design audit F.121): N1 +7.68 [3.24, 19.95]; N2 +0.46 [0.26, 0.73]; N3
  +46.02 [34.26, 63.16]; N4 +32.01 [11.59, 50.45]; N5 +63.38 [33.54, 71.83]. N6: H4 change +2.39
  [0.57, 8.91], but +3.18 [−0.40, +9.54] against the re-applied cap. 1,313 back-filled rows in 7 cities.

**D. What the confirmation does not settle (R1–R7).**
- R1: the rungs use stations differently (calibration vs same-day). Pilot numbers in the preamble.
- R2: H2 is close to guaranteed by design.
- R3: the prospective arm assumes the background keeps reporting.
- R4: station count is confounded with stream type.
- R5: Bud0 is leave-one-city-out, so same-network neighbours stay in training.
- R6: Kandy lies outside the confirmed population.
- R7: the background is same-network.
- Pending: L1–L3 (exploratory); L4 (Test C, a symmetric registered design, which is the author's call).

**E. Spatial learning curve (`rqn4y`+`26hp8`+`4whsc`+`4qs9c`, F.119; full records `fu59b`, F.123).**
- Registered frame: 18 cities, 745 sites, 7 countries, δ 0.28.
  - Held: X2 (11/18 cross; 5 at k = 3; 7 never), X3, X4, X5, X7 (reach 1.0 km), X9 (E10 at most +0.065),
    X11.
  - Refuted: X1, X6, X10 (TabPFN with coordinates −0.052 [−0.103, −0.018]).
  - Not testable: X12 (E11 failed its control).
- Full records: 23 cities, 960 sites, 9 countries, including Bangkok (65 sites).
  - 15/23 cross, 8 of them at k = 3; 8 never cross.
  - X4 refuted (London −0.28, Bangkok −0.57). S-1: X2 not held (48 %).
  - Tropical arm: 8 cities, none above the temperate envelope.
  - X-T terrain moderator: 0/16 intervals exclude 0 in either frame.
- Review reanalysis (exploratory; replaces the "cities split" and "tropical inside envelope" readings):
  - Holm crossovers 3/23 and 3/18.
  - Heterogeneity not significant on full records (Q p 0.06–0.26, I² 0.23–0.42); only 2/23 cities
    individually distinguishable.
  - Tropical − other, kriging − raster at k = 3: −0.22 [−0.45, +0.02] (z scale).
  - Empirical detection limits 0.35 (full) / 0.51 (registered), not 0.24 / 0.28.
  - X5 erratum as under ch08:262.
  - GHAP benchmark ≈ raster ≈ kriging (ρ 0.1–0.15).
  - Quote at most "a handful of stations is the right order of magnitude; no Kandy number".

**F. The review's self-critique of the Kandy chain (K1–K9).**
- K1 constant RH: swing 1.82 → 1.62 with hourly RH; a full κ-Köhler correction over-corrects.
- K2/K3 f: production 0.483; range 0.433–0.492.
- K4 shared inputs.
- K5 upward-bias reading.
- K6 incomplete intervals.
- K7 burden age structure (blocked on GBD data).
- K8 sharpening assumptions.
- K9/K-e: GHAP −10 / −17 % at NBRO, while the chain is +0.7 / −2.6 %.
- None of these has been propagated into the shipped field yet (K-f is the author's decision).
