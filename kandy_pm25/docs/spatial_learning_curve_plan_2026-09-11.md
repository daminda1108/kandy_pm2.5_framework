# Plan: the spatial learning curve — what each additional sensor buys for the within-city field

**Written 2026-09-11. Nothing here has been run.** Every feasibility number below was measured
this session, and the scripts that produced them are kept under
`scripts/spatial_curve_feasibility/` so the plan can be audited. The test is to be **registered on
OSF before any analysis code is written**, as every registered test in this project has been.

---

## 0. Why this exists

### The discovery that prompted it

The budget ladder, which carries the thesis's headline results, scores **one quantity**: the daily
city-mean. Read out of the code, not the prose:

```
target       = daily(held)                # mean over held-out stations -> one series per city
pred["Bud1"] = a  + b  * bud0             # (a, b) fitted on the mean of 2 pool stations
pred["Bud2"] = a' + b' * bud0             # (a', b') fitted on the mean of 6 pool stations
```

**Every rung's prediction is spatially constant.** Adding stations three to six changes two
coefficients of an affine rescaling of the same city-level series, which is the mechanical reason
their gain is about 0.1 per cent. The ladder therefore says nothing about spatial performance, and
cannot.

### The gap it leaves

The project's goal is a **spatiotemporal** field. The approaches Chapter 5 records as failures —
the physics-informed network, the rigid terrain form, the conditional neural process, the learned
pattern — were all attempts on the spatial axis. The spatial evidence the thesis holds is a set of
**nulls against a benchmark at convenience density**, and one relevant quantity has never been
measured at all:

> **how within-city spatial skill changes as stations are added, one increment at a time.**

`siting_experiment.py` varies *which* stations are fitted, never *how many*: its fitting-set size
is `k = max(4, n // 2)`, fixed per city, and it varies within **zero of 43** cities.

### Why the Kandy campaign needs it

F.100 and F.103 removed the campaign's spatial justification, and the open decision recorded in
the plan is *what the campaign claims*. A measured curve of skill against sensor count, with its
saturation point and ceiling, is the missing input. It would also replace the D-efficiency argument
the project has already found ranks the wrong designs first.

⚠ **The campaign cannot supply this for itself.** Its design holds out 8 receptor sites. Measured
below, a Spearman correlation on 8 held-out points has a per-split standard deviation of **0.34**,
so one campaign in one city cannot resolve its own spatial skill. The curve has to come from
cities that already have the density.

### Naming

This is **not** "the ladder for space" and must not be called that. The ladder's defining
property is exact nesting on a scalar series scored by RMSE. Here, withholding a station changes
both the fit and the thing the fit is judged against. The design below nests the **data** — each
fitting set contains the previous one — which gives paired increments, but it is not the ladder's
exact-degradation guarantee and will not be described as one.

---

## 1. What was measured to design it

### 1.1 The census overstated density

`global_reference_census.py` reports `n_ref = len(g)`, every reference station that **ever**
existed in a cluster; its overlap window only requires the tenth-ranked station. Recomputed as the
largest number of reference stations whose records jointly cover a common window
(`concurrent_density.py`, upper bound because gaps inside a record are invisible to metadata):

| concurrent reference stations | clusters, 1-year window | clusters, 2-year window | bands, 1-year |
|---|---:|---:|---|
| ≥ 15 | 56 | 50 | 35 temperate, 16 subtropical, 3 deep tropical, 2 tropical |
| ≥ 20 | 28 | 24 | 19 temperate, 6 subtropical, 2 tropical, 1 deep tropical |
| ≥ 30 | 14 | 11 | 10 temperate, 2 subtropical, 1 tropical, 1 deep tropical |
| ≥ 40 | 9 | 8 | 6 temperate, 2 subtropical, 1 deep tropical |

The densest networks: Korea 125, Japan 124, Britain 99, **Bangkok 86 — concurrent over a full two
years**, the only dense deep-tropical network in the world's openly published record.

### 1.2 Gaps inside records are modest

The cached station files hold only 11–12 stations per city, because the original ingest capped
them, so they cannot measure concurrency directly and the raw ratio against metadata (0.25) is an
artefact of the cap. What they do measure is **survival**: of the stations cached, the share
present on at least 75 per cent of days across the best one-year window. Bangkok 9 of 11, Mumbai
10 of 12, Japan 11 of 12, Medellín, Chile and Australia 12 of 12, Sweden 5 of 9. **Typical survival
is about 85 per cent**, and the plan uses that figure to project the frame.

### 1.3 The existing spatial frame has no common time window

`spatial_proxy_scan.station_means()` averages each station over its **whole** record, subject only
to 500 observations. A station that ran only through a polluted year is compared directly with one
that ran through a clean year, so part of the "spatial" contrast is temporal. Measured on the
36 OpenAQ cities of the current frame (`window_mismatch.py`):

- **17 of 36 cities have no common window of even 90 days** across their stations, so the
  confound cannot be assessed there at all.
- Where a common window exists (19 cities), whole-record and common-window means agree on rank at a
  median of **0.965** (minimum 0.691), with a median shift of **3.8 per cent** — but one city shifts
  by **52 per cent** at rank 0.69 and another by **26 per cent**.

That target feeds F.103, F.105, F.111 and the learned-pattern test. **The existing spatial nulls are
probably robust; the frame cannot demonstrate that for half its cities.** The new test enforces a
common window by construction, and Section 10 schedules an audit of the existing results.

### 1.4 Co-located instruments would leak

The median dense city has **32 per cent of stations within 1 km** of another, and some networks
have nearest neighbours 0–30 m away — several instruments at one site. Merging stations closer than
100 m into one site (`feasibility_extras.py`):

| | stations | sites at 50 m | sites at 100 m | sites at 250 m |
|---|---:|---:|---:|---:|
| all 56 dense cities | 2,215 | — | **1,986 (89.7%)** | — |
| worst: a US cluster | 54 | 20 | 18 | 17 |
| Sweden | 33 | 19 | 19 | 15 |
| Korea (largest) | 63 | 48 | 48 | 48 |
| **Bangkok** | **96** | **96** | **96** | **96** |

🔴 **Without merging, the test would flatter exactly the estimators it exists to measure.** A
held-out station whose twin sits in the fitting set is recovered almost perfectly by kriging or
inverse-distance weighting. That is the spatial form of the memorisation the project already met,
when fine-tuning drove agreement at two sensor coordinates to near unity while inflating the map.

### 1.5 Held-out sets need at least ten sites

Per-split noise of a Spearman correlation on held-out points, true rho 0.4, 3,000 draws:

| held-out sites | per-split sd | distinct attainable values |
|---:|---:|---:|
| 4 | 0.531 | 11 |
| 6 | 0.400 | 36 |
| 8 | 0.342 | 75 |
| 10 | 0.306 | 133 |
| 15 | 0.240 | 333 |
| 20 | 0.203 | 602 |

Four held-out points is the wall F.103's fixed-holdout re-check hit, now quantified. **Ten is the
floor; twenty is comfortable.** Per-split noise is then averaged away over replicates, and the
inference is across cities.

### 1.6 Detection limits

The project's own method (`phase1_frame_and_power.mde`): the smallest paired across-city effect a
one-sided Wilcoxon signed-rank test detects at 80 per cent power.

| cities | sd 0.10 | sd 0.15 | sd 0.20 | sd 0.25 |
|---:|---:|---:|---:|---:|
| 9 | 0.120 | 0.170 | 0.240 | 0.290 |
| 14 | 0.090 | 0.140 | 0.170 | 0.200 |
| 28 | 0.060 | 0.090 | 0.120 | 0.150 |
| 56 | 0.040 | 0.060 | 0.080 | 0.100 |

sd 0.20 is the siting experiment's observed between-city spread and is the planning value.

⚠ **The honest detection limit is set by networks, not cities.** At ≥20 concurrent stations the
28 cities come from **13 countries**, and Japan and Korea supply 16 of them. A cluster bootstrap
over networks (F.104) is mandatory, and the effective sample sits nearer the country count.

### 1.7 The projected frame

Applying 100 m merging and 85 per cent coverage survival to the metadata counts:

| sites after both | cities | bands |
|---|---:|---|
| ≥ 15 | **33** | 20 temperate, 9 subtropical, 2 deep tropical, 2 tropical |
| ≥ 20 | **15** | 11 temperate, 2 subtropical, 1 deep tropical, 1 tropical |
| ≥ 30 | 10 | 7 temperate, 2 subtropical, 1 deep tropical |

This is a projection. **The frame is fixed by the registered eligibility rule after ingest, never
by a list chosen beforehand.**

### 1.8 Retrieval cost

One Bangkok reference station (`s3_probe.py`): 1,491 daily objects over six years, 0.08 MB per
station-year. Bytes are trivial; the cost is request count. Measured throughput against the public
bucket:

| workers | GET/s |
|---:|---:|
| 8 | 18.2 |
| 32 | 56.0 |
| 64 | **82.5** |

A one-year window over all 1,986 candidate sites is at most about **725,000 objects, about
2.5 hours** at 64 workers. Feasible in one session, no API spend (gotcha #35).

⚠ **Timestamps arrive in local time** (Bangkok rows read `+07:00`). Every series is converted to UTC
before a daily mean is formed, or days misalign across time zones.

### 1.9 Libraries

Installed 2026-09-11: **pykrige 1.7.3, mgwr 2.2.1, libpysal 4.14.1, gstools 1.7.0.**
`spatial_tournament.py` hand-rolled its kriging, IDW and GWR because none was present. Kriging is
the estimator whose skill should depend most on density, so under the project's rule the proper
implementation is used here, and Section 10 schedules a cross-check of the hand-rolled version.

### 1.10 Where the project's own model can be scored

The grey-box pattern needs an emission surface and a terrain core, which exist for ten panel
cities. Of the dense candidates, **Medellín (19 concurrent) and Bogotá (16)** have both — two
deep-tropical cities, Kandy's band. Mexico City does not.

---

## 2. The questions, as estimands

| | question | estimand |
|---|---|---|
| **Q1** | What does each additional station buy for the **static** within-city pattern? | held-out rank correlation of common-window site means, against fitting-set size *k*, per estimator |
| **Q2** | What does it buy for the **spatiotemporal** field — the project's actual target? | per-day rank correlation across held-out sites, summarised over days, against *k* |
| **Q3** | How far does one sensor's information **reach**? | held-out error against distance to the nearest fitting site |
| **Q4** | Does **deliberate siting** matter once density makes it testable? | the Q1 curve under cLHS, random and convenience ordering at matched *k* |
| **Q5** | Does the curve **transfer** to Kandy's band, and where does the grey-box pattern sit on it? | the deep-tropical arm against the temperate envelope; the grey-box pattern as a horizontal line |

**Q2 is the question the project exists to answer and is co-primary with Q1.** A static pattern
of long-term means is what land-use regression measures; a model delivering an hourly field has to
be judged on a field that changes by day.

---

## 3. Frame and eligibility, fixed before ingest

A city enters when **all** of the following hold, evaluated on ingested data:

1. **Reference-grade only**, by OpenAQ's own `isMonitor` flag, so the classification is the
   provider's. Low-cost sensors are excluded from this test; their per-device error would be
   confounded with the density effect.
2. **Clustering** at 25 km, the rule the census and the project's discovery already use.
3. **Co-location merge**: stations within **100 m** become one site, whose value is the mean of its
   members. Applied **before** any split.
4. **Common window**: the 365-day window maximising the number of sites present on at least
   **75 per cent** of days. Only those sites, and only that window.
5. **UTC** before daily aggregation.
6. **QC**: the project's registered E4/E5 criteria — annual mean in 5–150 µg/m³, no run of more than
   24 identical hourly values, no value above 1,000.
7. **Size**: **≥ 20 sites → primary frame. 15–19 → secondary frame.** Deep-tropical and tropical
   cities with **≥ 12 sites** form the **band arm** regardless, because that is the only way to put
   any Kandy-band cities in the test.

Target frame by projection: **about 15 primary, about 33 in primary plus secondary.**

---

## 4. Design

### 4.1 Held-out set

Per replicate, a **fixed held-out set** of `H = max(10, floor(n / 3))` sites, drawn at random. It
does not change as *k* grows within the replicate. **This is the control the descriptive check
lacked:** there, held-out size grew with *k*, so estimator precision improved along the same axis
being measured.

**Robustness variant, registered now:** a **spatially blocked** held-out set — the sites of a
randomly placed contiguous block — which removes the advantage a held-out site gains from a
fitting site a few hundred metres away. Reported beside the random held-out result, never instead
of it.

### 4.2 Nested fitting sets

From the remaining `n − H` sites, one **ordering** is drawn per replicate. The fitting set at size
*k* is the first *k* sites of that ordering, so every larger set **contains** every smaller one.
Each increment is therefore a **paired marginal within replicate** — what adding those stations
buys, with the held-out set and every earlier station unchanged.

Sizes: `k ∈ {3, 5, 8, 12, 18, 25, 35, 50, 70}`, truncated at `n − H`. **18 is included because it is
the campaign's number of fitting sites.**

Orderings (Q4): **random** (primary), **cLHS** over the covariates, **convenience** (descending major
road length within 300 m, what compliance networks do). Each replicate draws all three on the same
held-out set.

**Replicates:** 100 per city.

### 4.3 Estimators

| | estimator | uses the *k* stations? | role |
|---|---|---|---|
| E0 | uniform city | no | floor; any predictor must beat it |
| E1 | free-raster benchmark (built-up at 2.4 km) | no | the project's registered benchmark, horizontal in *k* |
| E2 | ridge land-use regression on the 7 covariates of F.103 | fits on them | the covariate family |
| E3 | ordinary kriging, PyKrige, variogram fitted on the *k* sites only | interpolates them | the density family |
| E4 | inverse-distance weighting | interpolates them | the density family, parameter-free |
| E5 | regression kriging: E2 plus kriged E2 residuals | both | the hybrid a practitioner would use |
| E6 | geographically weighted regression, mgwr | fits locally | where `k ≥ 25` only |
| E7 | the grey-box pattern | no | Medellín and Bogotá only, horizontal in *k* |

### 4.4 Leakage guards, every one of which has already bitten this project

- **Standardisation and variogram fitted on fitting sites only.** Standardising within city over all
  sites is what drove the F.105 kriging oracle to correlate at exactly −1.000 in all 46 cities.
- **Co-location merge before splitting** (Section 3, item 3).
- **No descriptor of the target's outcome** among the covariates (gotcha #73). The seven covariates
  of F.103 are all land-surface rasters.
- **Common window for fitting and held-out alike.**

---

## 5. Scoring

**Q1, static.** For each city, *k*, ordering and estimator, the **median over replicates** of the
held-out Spearman correlation.

**Q2, spatiotemporal.** For each day in the common window with at least H held-out sites reporting,
fit on that day's values at the *k* fitting sites and score the Spearman correlation across that
day's held-out sites. The city value is the median across days. E2 and E5 use covariates fitted to
the day; E3 and E4 interpolate the day. This is the estimand closest to the model the thesis builds.

**Q3, reach.** Every held-out prediction is tagged with its distance to the nearest fitting site.
Absolute standardised error is binned by that distance, pooled within city, and the city curves are
summarised. The registered quantity is the **distance at which error reaches the uniform-city
error**: past that range a station carries no local information.

### 5.1 Effects and inference — paired, always

Every comparison is a **within-city paired difference**, summarised as the **median of the per-city
differences**, with a **95 per cent interval from a two-level cluster bootstrap**: networks
(country), then cities within networks (F.104). A difference of medians may be shown for
description and is never quoted as an effect (gotcha #91, which has caught this project four times).

**Saturation point** *k\**, defined now: the smallest *k* after which the paired increment to the
next size has a 95 per cent interval containing zero **and** a median below **0.02**.

**Crossover point** *k×*, defined now: the smallest *k* at which an estimator's paired advantage
over the benchmark E1 has a 95 per cent interval excluding zero.

---

## 6. Registered expectations, stated before any result

Written so that a failure cannot later be presented as a prediction, nor a success as expected.

- **X1 — density families improve with *k*.** E3 and E4 rise monotonically in median across the
  registered sizes. *Expected to hold.*
- **X2 — interpolation overtakes the benchmark, late.** E3 or E5 reaches a crossover *k×* ≤ 35 in at
  least half the primary cities. F.60 found interpolation worse than a uniform city at convenience
  density; this predicts that the finding is a **density** effect and reverses with enough stations.
  *Expected to hold, and the most informative outcome if it does not.*
- **X3 — covariate regression saturates early.** E2's saturation *k\** ≤ 12, at a level within the
  detection limit of the benchmark, consistent with F.105. *Expected to hold.*
- **X4 — a ceiling below unity.** Every curve plateaus below the within-cell ceiling, estimated in
  advance for each city from the variance among sites sharing a 1 km cell. *Expected to hold*; the
  change-of-support result puts within-cell spread (1.218) above between-cell spread (1.049).
- **X5 — siting still does not matter.** At matched *k*, cLHS does not beat random ordering by more
  than the detection limit. F.103's null, now tested at a held-out size where it can be resolved.
  *Expected to hold.*
- **X6 — the spatiotemporal curve sits below the static curve, estimators in the same order.**
  *Expected to hold.*
- **X7 — a finite reach.** Q3's error-equals-uniform distance is finite and below **5 km** in the
  median primary city. *Expected to hold.*
- **X8 — the deep-tropical arm.** Bangkok's curve lies inside the temperate envelope at every *k*.
  **Exploratory**, because the arm holds at most three cities.

---

## 7. What each outcome means, written before the outcome is known

**If X2 holds.** The spatial nulls in Chapter 8 are a **density** result: at convenience density no
estimator beats a free raster, and with enough stations interpolation does. The thesis states the
density at which the crossover arrives, and the campaign is judged against it: a 35-site network
with 18 fitting sites is either past the crossover or short of it, and the curve says which.

**If X2 fails.** The nulls are an **information** result at any density the world's networks
provide. Chapter 8's conclusion strengthens from *undetectable at this power* to *absent across the
density range observed*, and the campaign's spatial purpose is closed permanently.

**If X4's ceiling is reached early.** The limit is change of support, not station count, which
confirms Chapter 8's mechanism with a direct measurement and bounds what any kilometre-scale
product can deliver.

**Q3's reach becomes the single most useful number for Kandy.** It converts a station count into
a coverage statement: how much of the city a sensor actually informs.

**What no outcome licenses.** None of this validates the Kandy field. The deep-tropical arm is one
to three cities; transfer to Kandy stays an analogy, and the thesis says so in the same terms it
uses for the ladder.

---

## 8. Data retrieval

| step | what | cost |
|---|---|---|
| D1 | re-run discovery for the candidate clusters; record location IDs with coordinates | minutes |
| D2 | ingest hourly PM2.5 from the public archive for every candidate site, best one-year window only | ≤ 725,000 objects, about 2.5 h at 64 workers |
| D3 | apply the eligibility rule of Section 3; freeze the frame and write it to disk | minutes |
| D4 | predictors for frozen sites: GEE surfaces, reusing `build_lur_predictors.py` | minutes per city |
| D5 | OSM roads for frozen sites | one Overpass query per city bbox |
| D6 | within-cell ceiling per city, from co-located site pairs | minutes |

⚠ **D5 is the likeliest failure.** Megacity bboxes such as Seoul, Tokyo and London may exceed
Overpass limits. The fallback is to **tile the bbox** and deduplicate ways by ID, decided now so it
is not improvised later.

⚠ **Bangkok needs a full re-ingest**: 11 of its 96 sites are cached.

---

## 9. What the thesis gains

| where | change |
|---|---|
| **Chapter 8** | a new section: the spatial learning curve, its saturation, crossover, ceiling and reach |
| **§7.2** | the ladder's scope stated at the top of the section: it prices stations for a **daily city-mean** |
| **§9.7** | the campaign judged against the measured curve instead of D-efficiency |
| **Chapter 5** | the failed spatial approaches read against the density at which they were attempted |
| **abstract and summary** | the scope correction, and the curve's headline |
| **Appendix B and `registrations.json`** | the new registration, counted from the verified registry |

The summary already needs the scope correction whether or not the test runs; that edit is
independent of this plan.

---

## 10. Audits this plan schedules on existing results

Both follow from what was measured in Section 1, and both are reported however they come out.

1. **The window confound (1.3).** Re-derive the headline numbers of F.103, F.105 and F.111 on
   common-window targets in the cities where a common window exists, and report whether any
   conclusion moves.
2. **The hand-rolled geostatistics (1.9).** Score `spatial_tournament.py`'s kriging and GWR against
   PyKrige and mgwr on identical splits. If the published F.105 figures move, the change is reported
   as a correction.

---

## 11. Order of work

1. **Register** on OSF: frame rule, design, estimators, scoring, X1–X8 and their consequences.
2. **D1–D3**: ingest and freeze the frame. **Stop and report** if fewer than 10 cities reach the
   primary frame, because the design's detection limit then no longer holds.
3. **D4–D6**: predictors and ceilings.
4. **Leakage self-test** before scoring: with the co-location merge disabled, E3 on a held-out
   site with a twin in the fitting set must score near 1. If it does not, the guard is not working.
5. **Q1 and Q2**, then **Q3**, then **Q4**, then **Q5**.
6. **Audits** (Section 10).
7. **Write**: Chapter 8 section, §7.2 scope, §9.7, abstract, summary, Appendix B.

---

## 12. What this test does not claim

- It does not validate the Kandy field at any resolution.
- It does not measure low-cost sensor networks, whose per-device error would be confounded with
  density.
- It does not say where in a city stations should go. Q4 tests whether siting strategy matters at
  density; it does not optimise placement.
- It does not transfer the ladder's exact-nesting guarantee to space. The nesting here is of data.

## 13. Exploratory analysis X-T: does terrain moderate the curve? (added 2026-09-11)

**Declared before any learning-curve result existed** (the frame was frozen and the predictors
were still being built; no estimator had been scored on real data). **Not part of OSF `rqn4y` or
amendment `26hp8`**, and never reported as confirmatory. User request, after asking why this
test uses dense cities rather than topographic analogues.

**Why.** The frame is chosen by network density, and no city in it is a valley city of Kandy's
type (primary frame: 13 temperate, 4 subtropical, 1 tropical). The quantity meant to transfer to
Kandy is the relation between sensor spacing and skill, which depends on how PM2.5 is structured
in space. Basin terrain plausibly changes that structure: cold pools and inversions trap pollution
along elevation contours, and in western Montana a terrain-derived accumulation layer explained
59.5% of the spatial variance of winter mean PM2.5 (Swanson et al., 2026). If terrain moderates the
curve *inside* the frame, the dense-city answer is less safe to carry to Kandy.

**Descriptors**, fixed in `scripts/spatial_curve_terrain.py` (SRTM GL1): T1 relief over the sites'
box padded 5 km (p95 − p5); T2 elevation spread across the sites themselves; T3 mean slope; T4
enclosure, the number of 8 compass rays from the median site that rise ≥ 200 m within 15 km.

**Outcomes**, read from the registered analysis's own per-city outputs, in
`scripts/spatial_curve_moderators.py`: O1 reach (E3), O2 crossover k× (E3 over E1), O3 E3 skill at
k = 12, O4 paired E3 − E1 at k = 12. Censored reach and crossover (never reached within the tested
range) are ranked above every finite value.

**Statistic.** Spearman over primary cities, two-level country-then-city bootstrap, permutation p.
**Sixteen uncorrected tests**: about one will look significant by chance. With ~18 cities only
|ρ| above roughly 0.5 is detectable, so **a null here is not evidence that terrain does not
matter**. Anything that looks like a moderation is a lead for a registered follow-up with more
basin cities, and the natural source of those is the band arm and the deep-tropical networks F.53
found to be scarce.

**Not lodged on OSF.** Lodging it as a timestamped note before the first real scoring run would
make the "declared before results" claim checkable by a reader, not just asserted here. User's call.
