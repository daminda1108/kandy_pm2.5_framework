# [AI REFERENCE DRAFT — rewrite every sentence in your own words before sending]

# Progress report: how much does each kind of air-quality information buy?
**To:** Dr. Mahasen Dehideniya (data-science co-supervisor) · **From:** Daminda Alahakoon · **Date:** October 2026

---

## What I would like from you
I am asking for a critical review of the **method**, before the method paper is finalised. My main supervisor and I
agreed to settle the method part first. I would value your view on five questions (Section 6), especially whether the
statistical design is sound and whether there is a better modelling approach for the sensorless baseline or the
spatial part. I am open to substantial changes.

## 1. The problem
Kandy has no public PM2.5 monitor. To estimate air quality there, we need to know **how much each kind of information
improves an estimate of a city's daily PM2.5**:
- no local sensors (only weather reanalysis, satellite aerosol and geography);
- the first one or two local stations;
- a few more stations;
- a regional background (a low percentile of nearby stations).

This is a **value-of-information** question. The answer tells a city with no monitors what to install first. I
answer it on cities that do have dense monitoring networks, then apply the result to Kandy.

## 2. Data
- **Cities:** about 120 cities with at least 10 monitoring stations. They come from OpenAQ (worldwide) and the
  Chinese national network (CNEMC). They are split into a **discovery panel** (47 cities, used to develop the
  method) and a **confirmation panel** (72 fresh cities, scored once).
- **Target:** daily mean PM2.5. A station-day counts only with at least 18 valid hours.
- **Predictors for the sensorless rung:**
  - ERA5 weather: temperature, wind, boundary-layer height;
  - MAIAC satellite aerosol optical depth;
  - 60 static geography features, computed on a grid over the urban centre rather than at monitor sites, to avoid
    leakage;
  - season.

## 3. Method: the "information-budget ladder"
Each city's stations are split at random into **held-out stations**, used only for scoring, and **available
stations**. Four estimators ("rungs") are compared, each allowed more information than the one before:

| rung | information | model |
|---|---|---|
| Bud0 | no local sensors | gradient-boosted trees (HistGradientBoosting), **leave-one-city-out**: the city being predicted is never in training |
| Bud1 | + first two stations | Bud0 recalibrated (affine) to the two stations |
| Bud2 | + stations 3–6 | same, on six stations |
| Bud3 | + background | regression on Bud0 and the daily 10th percentile of the remaining stations |

**Score:** the percentage reduction in RMSE at the held-out stations from one rung to the next, per city.
- **Repeats:** 21 random station splits × 5 learner seeds per city, averaged before any inference. A single split
  turned out to be one noisy draw.
- **Inference:** the median over cities, with a **two-level cluster bootstrap** (cities nested in networks or
  countries), 4,000 draws.
- **Arms:** a "reconstruction" arm, and a "prospective" arm where calibration uses only earlier days.

**Safeguards:**
- every test is **pre-registered on OSF** before its data are retrieved or scored;
- the code is **frozen by hash**;
- a synthetic-target **dry run** comes first;
- every re-run must pass a **parity gate**: it must reproduce the earlier registered result exactly before anything
  new is scored.

About a quarter of my registered predictions have been refuted (22 of 92 by late September). I report these rather
than drop them.

## 4. Results so far

**Confirmation on 72 fresh cities (OSF `ueyfr`):**
| question | result (median % RMSE gain [95 % cluster CI]) |
|---|---|
| first two stations over no sensors (used only to recalibrate) | **+8.5 [3.1, 25.1]** |
| stations 3–6 | +0.2 (negligible) |
| background, given six stations | **+41.1 [26.8, 62.8]** |
| background minus first two | **+24.6 [4.1, 47.8]** as constructed (see below) |
| same, for exceedance days | **+59.3** |
| does the ordering change with latitude? | not detectable (only 4 low-latitude cities) |

**A flaw I found afterwards, by reviewing my own code (2026-10-06):** the two rungs do not use their
stations the same way. The first two stations only correct the level and scale of the sensorless estimate (an
intercept and slope), so their daily readings never enter a day's prediction; the background is read on the day.
When I re-scored every stream the same way (post hoc, reproducing the registered numbers exactly):
| arm, read on the day (100 cities) | % RMSE gain |
|---|---|
| first two stations | **+58.8 [44.9, 69.0]** |
| background (as registered) | +57.7 [46.4, 67.4] |
| background from only two stations | +57.2 |
| background minus first two | **−0.22 [−0.60, +0.04]** |

So the registered "background is worth more" is a property of how I built the rungs. What actually matters is
whether a station's reading is used on the day (~58 %) or only as a calibration (~9–14 %); the kind of station
does not. The registered results stand as registered, but I now interpret them this way.

**Robustness checks, each registered separately:**
- **Richer sensorless baseline** (`b379r`): adding CAMS forecast PM2.5, terrain, fires, TROPOMI NO₂ and rainfall
  improved Bud0 by 13 %. Six of the seven verdicts held.
- **Different learners** (`jea58`):
  - TabPFN (a tabular foundation model) did **worse** (−11 %), and a 14-day GRU did no better. Physics features did
    no better either.
  - All directional verdicts held.
- **Full station networks** (`mhgna`, October): the first runs used at most 12 stations per city. With up to 40
  (median 17), every verdict held, and the background's advantage grew (+32.0 [11.6, 50.5]).

**Within-city "spatial learning curve" (`rqn4y`):**
- This asks how many stations it takes to **map** a city, rather than to estimate its average.
- Estimators: IDW, kriging, regression kriging, ridge land-use regression, GWR, TabPFN, ConvGNP (a neural process)
  and TNP-D.
- **Findings:**
  - Cities split: 11 of 18 beat a satellite raster with enough stations; 7 never do.
  - Station information reaches only about 1 km.
  - Choosing sites carefully (cLHS) gave no detectable gain over random siting.
- A re-run on each station's full record (`fu59b`, October) grew the frame to 23 cities in 9 countries, including
  Bangkok, the first deep-tropical city:
  - Under the registered rule 15 of 23 cities beat the raster. A re-analysis I did afterwards shows most of that
    is sampling noise (each city is scored on as few as 10 held-out sites): only **3 of 23** cross after a Holm
    correction, and the differences between cities are not significant.
  - Tropical vs other cities: −0.22 [−0.45, +0.02] (Fisher z); not distinguishable, but if anything worse.
  - A summary bug: the registered siting comparison (cLHS vs random) reported [0.00, 0.00] because it pooled
    estimators that cannot differ. Corrected per estimator, it is about ±0.05: still no gain from careful siting.
  - A satellite PM2.5 product (GHAP) ranks neighbourhoods no better than the land-cover layer (ρ ≈ 0.1).
  - One registered prediction failed: the "within-cell ceiling". In London and Bangkok, stations sharing a 1 km cell
    disagree with each other more than chance.
- **What this means for Kandy:** with a handful of stations, expect to get the city's level and its day-to-day
  changes, not a reliable neighbourhood map.

## 5. What I think is solid, and what is not
**Solid:**
- leave-one-city-out sensorless baseline;
- randomisation and repeats;
- registration and parity gates;
- results stable across baselines, learners and network size;
- the main finding after the correction: a station's value lies in its daily reading.

**Weak or open:**
- The panel is mostly temperate and regulatory-grade. Kandy is tropical, so the transfer to Kandy is an
  extrapolation.
- The "background" rung is built from the same network, so it is a proxy for a true regional background. An
  independent network 30–300 km away recovers about 71 % of it.
- The rung models are deliberately simple: affine and linear, and (my main error) the registered rungs were not
  built alike; the corrected comparison is post hoc, not registered.
- The spatial curve's per-city scores are noisy (10 held-out sites in most cities).
- Uncertainty comes from bootstrapping over cities, not from a probabilistic model.

## 6. Questions for you
1. **Inference design.** Is the median of per-city percentage gains, with a two-level cluster bootstrap, the right
   summary? Would a hierarchical (mixed-effects or Bayesian) model of the gains be better, given cities nested in
   networks and countries?
2. **Sensorless baseline.** Pooled trees under leave-one-city-out beat TabPFN and a GRU. Is there a
   transfer-learning or domain-adaptation approach I should try for a target city (Kandy) unlike most training
   cities? For example: importance weighting, or hierarchical models with city-level covariates.
3. **Rung models.** Should the station rungs use partial pooling across cities (a hierarchical calibration) instead
   of a separate affine fit per city? And is the like-for-like re-analysis (same-day use for every stream) the
   right correction, or would you frame the comparison differently, e.g. as data-denial experiments from data
   assimilation?
4. **Extrapolating to the tropics.** With few low-latitude cities, how would you quantify how far the result can be
   trusted for Kandy? For example, a covariate-shift diagnostic, or conformal intervals under shift.
5. **Spatial mapping.** For small, irregular station sets (5–50 sites per city), is there a better approach than
   regression kriging, which wins most often? One neural process passed its positive control and one failed.

## 7. Next steps
- Rewrite Paper 1 around the corrected finding (same-day reading vs calibration) and the narrowed spatial results.
- My main supervisor is arranging institutional Kandy data (CEA monitoring) for validation.
- The sensor-placement proposal waits until the method is concluded.
- A review paper in atmospheric science (topic to agree).

## Appendix: where to look
OSF registrations: `ueyfr` (confirmation), `b379r` (baseline), `jea58` (learners), `mhgna` (full networks),
`rqn4y` and `fu59b` (spatial curve). I can share the code repository and a one-page method diagram.
