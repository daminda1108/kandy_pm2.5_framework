# Pre-registration v2 — stratified validation of the modular decomposition (widened frame)

**Date:** 2026-08-18 · **Supersedes** `prereg_modular_validation_2026-08-18.md` (v1, CNEMC-only).
Registered **before** any city in the widened frame was scored.

**Why v2 exists.** v1 declared a CNEMC-only frame. Inspection of the PVAF OpenAQ census then
showed a materially better frame already indexed on disk. Registering a design already known to
be second-best would be the wrong kind of rigour, so v1 is superseded rather than amended.
The CNEMC-arm run launched under v1 is treated as a **pilot**, reported separately and labelled
as such — not folded into the v2 result.

---

## 0. The frame, counted

Two sources, both already on disk as an index:

| source | what exists | ladder-eligible (>= 10 stations) |
|---|---|---|
| CNEMC panel | 199 cities, per-station hourly **ingested** | **39** |
| OpenAQ census | 19,589 locations, **715 city clusters** indexed; time series **not yet pulled** | **191** (>= 10 concurrent) |

**Ladder-eligible frame: N = 230 cities, 61 countries.**

Latitude structure — the reason for widening:

| band | CNEMC | OpenAQ |
|---|---:|---:|
| deep tropics, \|lat\| < 15 (**Kandy = 7.3 N**) | **0** | **17** (14 countries) |
| \|lat\| < 20 | **0** | 25 (16 countries) |
| southern hemisphere | **0** | 20 (8 countries) |
| tropical band \|lat\| < 23.5 | 18 | 33 |

**Every city at Kandy's latitude in this project comes from OpenAQ.** CNEMC spans 20.0-47.7 N
and structurally cannot supply one. This is the quantified form of the standing "the panel does
not bracket Kandy" limitation, and the widened frame is the first thing that addresses it.

## 1. Selection strata — declared, and only on what is known BEFORE ingest

This is the load-bearing design decision. For OpenAQ clusters, pollution level and station
relief are **not known** until the time series is pulled. Stratifying on them would mean
selecting after measuring, which is the F.24 error. Therefore:

**A-priori strata (selection):**
- `band`: deep-tropical (<15) / tropical (15-23.5) / subtropical (23.5-35) / temperate (>35)
- `stations`: 10-15 / 16-30 / >30
- `source`: OpenAQ / CNEMC (proxy for regulatory network and instrument protocol)

**Measured covariates (reported, never used to select):** pollution level, station relief,
coastal proximity, source mix. These are reported per city in the results table and used for
*post-hoc description*, explicitly labelled as such.

**Sampling rule.** The deep-tropical cell is **fully enumerated** (all 17 — it is the scarce,
Kandy-relevant stratum and must not be sub-sampled). Other cells are sampled to a target of
**up to 12 cities each**, drawn by a fixed seed from the eligible list, with no substitution
after a city fails ingest — failures are reported in an **exclusion funnel**, not replaced.

**Country cap:** no more than **4 cities per country**, applied before sampling. Without it the
sample re-inherits the volume bias it exists to avoid (US 50, Germany 12, Spain 10 at the >= 10
cut; China 39).

## 2. The ladder (unchanged from v1)

| rung | information | estimator |
|---|---|---|
| `Bud0` | drivers + static covariates, **no observation of this city** | leave-one-city-out gradient boosting |
| `Bud1` | + 2 local stations | affine correction |
| `Bud2` | + 6 local stations | affine correction |
| `Bud3` | + outer-ring stations as background proxy | linear in (prior, background) |

Every rung fitted only on its own admissible stations; all rungs scored on stations no rung
sees. Richer rungs enter via cross-validated shrinkage, folds grouped by day.

## 3. Registered gates

- **V1 — P2 monotonicity.** Held-out RMSE must not increase along the ladder in **>= 90%** of
  cities. Violations named individually.
- **V2 — `Bud0` genuinely sensorless.** LOCO fold excludes every station of the target city;
  asserted in code.
- **V3 — per-stratum reporting.** Nothing reported pooled without also being reported per cell.
  Cells with < 3 cities are **not estimable**, never pooled away.
- **V4 — diminishing returns.** Registered expectation from F.48: the `Bud0 -> Bud1` step
  exceeds the `Bud1 -> Bud2` step in a majority of cities.
- **V5 (new) — the tropical claim.** Any statement that the model transfers to Kandy's regime
  must rest on the **deep-tropical cell alone**, reported with its own N. Pooling it with
  temperate cities to claim "transfers across regimes" is prohibited by this registration.
- **V6 (new) — LCS honesty.** OpenAQ cities are low-cost-sensor-heavy. Sensor class is recorded
  per city and reported; results are given **split by class**, since instrument bias `b_k` is
  unidentified at every budget below `Bud2`.

## 4. Published priors

- P2 holds nearly everywhere **by construction** (w = 0 is in the search space); the informative
  quantity is the WEIGHT, not the pass.
- `Bud0 -> Bud1` is the largest step in most cities.
- The background rung is large where the outer ring is genuinely cleaner, near-zero in flat
  cities.
- **`Bud0` will be materially worse in the deep tropics than in the temperate band**, because
  the LOCO training pool is dominated by mid-latitude cities. If this does not occur it is a
  finding, not a relief.
- Absolute skill will be worst in high-pollution, smoke-driven regimes.

## 5. Ingest dependency, stated honestly

The OpenAQ arm **cannot run until the time series are pulled**. The S3 archive is public and
unsigned and `scripts/ingest_openaq_s3.py` exists, but ingest plus QC plus per-device
calibration (gotcha #37) is a multi-day task. Until then:

- the **CNEMC arm** can be reported as a pilot, labelled as such, with its frame limits stated;
- **no cross-regime or Kandy-relevance claim may be made from the CNEMC arm alone** (V5).

## 6. Stopping rule

Failed gates are reported as failures. Strata are not re-cut after seeing results. If a cell
proves unusable, that is the finding.

---

**OSF status:** not registered. Publishing to a public, irreversible registry under the
researcher's identity is the researcher's action, not the assistant's. This document is
timestamped only by the repository until then.


---

## Amendment 1 (2026-08-18) — sampling rule corrected, and the design sized

Made **after inspecting the frame and its cost, before any city was scored.** Recorded rather
than silently applied.

**The defect.** The registered country cap (4 per country) was applied to both arms. CNEMC is a
**single-country stratum**, not 39 independent countries, so the cap discarded 35 of the 39
CNEMC cities — the ones whose ERA5 drivers are **already on disk**. It therefore *maximised* GEE
cost instead of minimising it, producing N = 88 with **84** driver pulls.

**The correction.** The cap applies to the **OpenAQ arm only**, where it does the job it was
written for (US 50, Germany 12, Spain 10 at the >= 10-station cut). CNEMC passes through
uncapped and is reported as **one single-country stratum whose N buys within-regime replication,
not country diversity** — a distinction that must survive into the paper.

**Minimum-GEE rule (`--min-gee`).** No OpenAQ city is drawn in the subtropical or temperate
bands, because CNEMC supplies those at zero driver cost. **Every GEE pull therefore buys
latitude coverage that is otherwise unobtainable.**

### The sized design

| band | CNEMC (free) | OpenAQ (GEE) | total |
|---|---:|---:|---:|
| deep-tropical (\|lat\| < 15) | 0 | **15** | 15 |
| tropical (15-23.5) | 3 | 11 | 14 |
| subtropical (23.5-35) | 17 | 0 | 17 |
| temperate (> 35) | 16 | 0 | 16 |
| **total** | **36** | **26** | **N = 62** |

**20 countries. GEE driver pulls: 26 — down from 84, a 69% reduction — with the
Kandy-relevant cell fully enumerated and untouched.**

### What this N can and cannot support, stated before results

- **Per-band medians with bootstrap CIs**: supported at n = 14-17 per band.
- **Deep-tropical vs mid-latitude contrast**: n = 15 vs 33 gives 80% power at roughly
  **d ~ 0.9**. It can detect a **large** regime difference and **cannot** detect a subtle one.
  This is a registered limitation, not a result to be discovered later.
- **P2 proportion**: N = 62 gives a binomial CI of about **+/- 7 pp** on a 90% gate.
- **Not supported**: any fully-crossed band x relief x level design; any claim resting on a
  cell with fewer than 3 cities (V3); any Kandy-relevance claim from outside the
  deep-tropical cell (V5).

For scale: the currently submission-ready panel is **N = 10, all terrain-confined basins, all
mid-latitude**. This design is N = 62 across **four latitude bands and 20 countries**, with 15
cities at Kandy's own latitude — the first time the project has had any.

**Further trim, if GEE is tighter still:** dropping the 11 tropical OpenAQ cities leaves
**N = 51 with 15 pulls**, but reduces the latitude axis to a two-point contrast with a gap
either side of it. Not recommended; recorded so the choice is explicit.


---

## Amendment 2 (2026-08-18) — the minimum-GEE design was CONFOUNDED; corrected before any scoring

Raised by the researcher, verified, and acted on. Recorded in full because Amendment 1 caused it.

**The defect.** Amendment 1's minimum-GEE rule drew no OpenAQ city in the subtropical or
temperate bands, so the mid-latitude comparison arm was **33 cities, all Chinese**, against 15
deep-tropical cities that are all non-Chinese. Latitude band was therefore **perfectly aliased
with country and monitoring network**: a deep-tropics-vs-mid-latitude difference could equally
be a non-China-vs-China difference, and no analysis of that sample could separate them.

**This is not a presentational weakness — it makes the V5 contrast uninterpretable**, which is
the one claim the whole widened frame exists to support. Amendment 1 optimised an operational
cost (GEE pulls) and silently destroyed the design's inferential content. The ordering was
wrong: cost should be minimised *subject to* identifiability, never ahead of it.

**A second, quieter problem with the same cause.** 36 CNEMC cities are not 36 independent
samples for a *transfer* claim. They share one regulatory network, one instrument protocol, one
calibration regime, one continent. Effective sample size is far below nominal, so a large CNEMC
count inflates apparent power without adding proportional evidence.

**The correction (option C).**

- The country cap applies to **both** arms. China becomes one country among many.
- CNEMC is additionally capped at **12 cities total** — enough to represent a well-observed
  single-network stratum, capped so it cannot exceed roughly a quarter of the sample.
- OpenAQ cities **are** drawn in the subtropical and temperate bands, so the mid-latitude arm
  contains multiple countries and networks and the band contrast is identifiable.
- The deep-tropical cell remains **fully enumerated** and untouched by all of the above.

**Cost.** GEE driver pulls rise from 26 to roughly 40. That increase is the price of an
interpretable headline contrast, and it is the correct trade.

**What is now reportable that was not:** whether a deep-tropics penalty survives adjustment for
network and country. Under Amendment 1 that question was unanswerable by construction.


---

## Outcomes (appended after running; registered content above unaltered)

| arm | status | outcome |
|---|---|---|
| **CNEMC pilot** (v1 frame) | run 2026-08-18, **39 cities** | V1 **PASS 97%** (violation named: city038) · V4 **confirmed sharply** · **the background rung is the only large step: +2.9% / 0.0% / 43.6%**. My registered prior that `Bud0->Bud1` would dominate was **wrong**. Ledger **F.50**. |
| **OpenAQ arm** (v2 frame) | **COMPLETE 2026-08-19, 47 cities scored** | V1 **PASS 98%** (violation named: 3147) · V2/V3 honoured · **V4 confirmed but CONDITIONED on instrument class** · **V5 confounded and disclosed** · **V6 fired** — class aliased with band. Two registered priors refuted. Ledger **F.51–F.53**. |

**The pilot cannot support any v2 claim** (gate V5): it is one country, one network,
20-47.7 N. It is reported as a pilot wherever it appears.


---

## Registered experiment S1 (2026-08-19) — can regime-specific emission weights be FITTED?

Registered before running. Follows F.58, which found the best spatial proxy differs by latitude
band (population in the deep tropics, built surface subtropical, night lights temperate, fire
tropical) and that no fixed surface can be right in all four.

**Question.** Does a per-regime weighting of source proxies, FITTED on other cities, rank
held-out cities' stations better than the best single proxy?

**Design.** Frame = the 47 cities / 636 stations of F.58. Features = 4 proxies x 2 scales
(point, 2 km). Weights fitted per latitude band, **leave-one-city-out within band**, scored on
the held-out city's stations by Spearman rank. Weights constrained non-negative and summing to
one, so they remain interpretable as emission shares.

**Baselines, all scored identically:** best single proxy (population 2 km), equal weights over
all proxies, and per-band best single proxy.

**Gates.**
- **S1-G1** the fitted weighting must beat `population_2km` on **median held-out rho**, pooled.
- **S1-G2** it must not be worse in any band (no band may lose more than 0.05 rho).
- **S1-G3** fitted weights must be reported in full, including any that collapse onto a single
  proxy -- a "fit" that just rediscovers population is a null and is reported as one.
- **S1-G4** fire is included as a candidate but its estimability (18 of 47 cities) is reported
  alongside any weight it receives.

**Published priors.**
- **Modest or no gain is the expected outcome.** Fitting 4-8 weights on 10-13 cities per band is
  high-variance, and the pooled spatial ceiling is rho ~ 0.2 -- there is little signal to
  apportion. A null here would be consistent with the five prior spatial nulls, not a surprise.
- If anything gains, the **temperate band** is the most likely (its best single proxy, night
  lights at +0.441, is already the strongest band-level signal).
- Fire will likely receive weight in the tropical band and be unstable there because it is
  estimable in so few cities.

**Stopping rule.** If S1-G1 fails, the fitted weighting is not adopted and the hand-declared
`emix` stays as-is with F.56's verdict standing. No re-cutting of bands after seeing results.
