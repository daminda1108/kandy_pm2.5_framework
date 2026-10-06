# Pre-registration — what does each additional monitor buy for the within-city PM2.5 field?

**Lodged before the analysis was run.** Project: Kandy PM2.5 (Daminda Alahakoon, University of
Peradeniya). Date drafted: 2026-09-11. Full design rationale:
`kandy_pm25/docs/spatial_learning_curve_plan_2026-09-11.md`.

**OSF [`rqn4y`](https://osf.io/rqn4y/), project [`smznp`](https://osf.io/smznp/)**, registered
2026-09-10 19:14:37 UTC, lodged by `scripts/osf_lodge.py` and verified as an artefact after the
request. Submitted in a state pending OSF approval; the timestamp is fixed at submission. No
ingest had been run when it was lodged.

---

## 1. Why this test exists

This project's budget ladder prices data sources by the fall in out-of-sample error of the
**daily city-mean**. Each rung predicts one number per city per day, so adding monitors changes
only an affine calibration of that series, and the ladder cannot measure spatial performance.
The within-city spatial evidence the project holds consists of nulls against a free-raster
benchmark at the density of existing networks. **How spatial skill changes as monitors are added
has never been measured**: the siting experiment fixed the fitting-set size at half of each city's
stations.

This test measures it, within city, on the densest openly published reference networks, for a
static pattern and for the day-to-day field.

## 2. What was examined before lodging, disclosed

Feasibility was established from **station metadata** (locations, first and last report dates),
public-archive request timings, and simulation. Two results on **existing** data were also seen
and are disclosed here:

1. In the earlier siting experiment, where fitting-set size varied **between** cities, median
   held-out rank correlation rose from 0.03 at 5–7 fitting stations to 0.49 at 14–24. That
   association is confounded with city size and with held-out-set size, and it is **not** evidence
   for any hypothesis below. It motivated the within-city design.
2. In the existing spatial frame, station means are taken over each station's whole record; in 17
   of 36 cities the stations share no common 90-day window, and where one exists, whole-record and
   common-window means agree on rank at a median of 0.965.

No PM2.5 value from any city in the frame defined below has been used in any fit or score for this
test.

## 3. Frame, fixed here and applied after ingest

**Source.** OpenAQ public archive, hourly PM2.5.

**Eligibility, all required:**

1. Reference grade by OpenAQ's `isMonitor` flag. Low-cost sensors excluded.
2. Stations clustered greedily at 25 km, densest seed first.
3. Stations within **100 m** of each other merged into one **site**, whose hourly value is the mean
   of its members. Applied before any split.
4. Timestamps converted to UTC before daily aggregation.
5. QC: values in [0, 1000) µg/m³; runs of more than 24 identical consecutive hourly values removed;
   annual site mean in [5, 150] µg/m³.
6. **Download window:** the 365-day window that maximises metadata concurrency, with 60 days of
   margin on each side. **Analysis window:** the 365 consecutive days inside the download window
   that maximise the number of sites present on at least 75 per cent of days. A site enters only
   if it meets that coverage in that window. A day counts as present with at least 18 hourly
   values.
7. Clusters downloaded: every cluster with at least 15 metadata-concurrent reference stations over
   one year, plus every tropical and deep-tropical cluster (absolute latitude below 23.5°) with at
   least 12.

**Frames:**

- **Primary**: at least **20** sites after rules 1–6.
- **Secondary**: 15–19 sites.
- **Band arm**: tropical and deep-tropical cities with at least **12** sites, regardless of frame.

**Stop rule.** If fewer than **10** cities reach the primary frame, the analysis stops and that is
reported, because the detection limits of Section 6 no longer hold.

## 4. Design

**Units.** A site's static value is its mean over the analysis window. Its daily value is its mean
over a UTC day with at least 18 hourly values.

**Replicates.** 100 per city. In each:

- A **fixed held-out set** of `H = max(10, floor(n/3))` sites, drawn at random, unchanged as the
  fitting set grows.
- From the remaining sites, **three orderings**: random (primary), conditioned Latin hypercube
  over the covariates, and convenience (descending major-road length within 300 m).
- **Nested fitting sets**: the fitting set at size *k* is the first *k* sites of an ordering, for
  `k ∈ {3, 5, 8, 12, 18, 25, 35, 50, 70}`, truncated at `n − H`.

**Robustness variant.** A spatially blocked held-out set: the H sites nearest a random point.
Reported beside the random held-out result, never in place of it.

**Estimators.**

| | estimator | uses the *k* sites |
|---|---|---|
| E0 | uniform city | no |
| E1 | benchmark: built-up land cover within 2.4 km | no |
| E2 | ridge regression on seven covariates: built-up at 2.4 km and 300 m, night lights at 1 km, population at 1 km, NDVI at 1 km, major-road length within 300 m, distance to major road | fits |
| E3 | ordinary kriging (PyKrige), variogram fitted on the *k* sites | interpolates |
| E4 | inverse-distance weighting, power 2 | interpolates |
| E5 | regression kriging: E2 plus ordinary kriging of E2's residuals | both |
| E6 | geographically weighted regression (mgwr), for *k* ≥ 25 | fits locally |
| E7 | this project's grey-box spatial pattern, where its inputs exist (Medellín, Bogotá) | no |

**Leakage guards.** Standardisation, variogram and every fitted parameter use fitting sites only.
No covariate is derived from any site's PM2.5. Co-location merging precedes splitting.

**Leakage self-test**, run before scoring: with merging disabled, a held-out site whose co-located
twin is in the fitting set must be predicted by E3 with standardised error below 0.1. If it is not,
the guard is not demonstrably working and scoring does not proceed until it is.

## 5. Estimands and scoring

- **Q1, static.** Per city, *k*, ordering and estimator: median over replicates of the Spearman
  correlation between predicted and observed static values at held-out sites.
- **Q2, spatiotemporal.** Per day with at least H held-out sites present: fit on that day's values
  at the fitting sites that report, score Spearman across held-out sites. City value: median across
  days. E2 and E5 refit their coefficients per day; E1 and E7 contribute their fixed spatial
  ranking.
- **Q3, reach.** Absolute standardised error of every held-out prediction, binned by distance to
  the nearest fitting site (bins 0–0.5, 0.5–1, 1–2, 2–3, 3–5, 5–8, 8–12, over 12 km). The **reach**
  is the smallest distance bin whose median error is not lower than E0's by more than its
  bootstrap interval.
- **Q4, design.** The Q1 curves under cLHS and convenience ordering, paired with random ordering
  on the same held-out sets.
- **Q5, band.** The band-arm curves against the envelope of primary-frame curves.

**Inference.** Every comparison is a within-city paired difference. Effect: the median of per-city
differences. Interval: 95 per cent, two-level cluster bootstrap, resampling countries and then
cities within countries, 5,000 draws. A difference of medians is never reported as an effect.

**Saturation point** *k\**: the smallest *k* after which the paired increment to the next registered
size has an interval containing zero and a median below 0.02.

**Crossover point** *k×*: the smallest *k* at which an estimator's paired advantage over E1 has an
interval excluding zero.

**Within-cell ceiling**, estimated per city before scoring: the rank correlation attainable if every
site were predicted by the mean of other sites in its own 1 km cell, in cities with enough such
pairs.

## 6. Detection limits, fixed here

Smallest paired across-city effect detectable at 80 per cent power, one-sided Wilcoxon, α = 0.05,
at a between-city spread of 0.20: **0.17** at 14 cities, **0.12** at 28. Because cities cluster
within national networks, the limit that applies is the one for the number of **countries** in the
frame, and it will be reported with every result.

## 7. Predictions

**X1.** E3 and E4 increase in median with *k* across the registered sizes, in the primary frame.

**X2.** E3 or E5 reaches a crossover *k×* ≤ 35 in at least half of primary-frame cities.

**X3.** E2 saturates at *k\** ≤ 12, at a level whose paired difference from E1 lies within the
detection limit.

**X4.** No estimator's median curve exceeds the city's within-cell ceiling by more than the
detection limit.

**X5.** At matched *k*, cLHS ordering does not beat random ordering by more than the detection
limit.

**X6.** For every estimator, the Q2 curve lies below the Q1 curve, and the ranking of estimators at
the largest common *k* is the same in both.

**X7.** The reach in the median primary-frame city is below 5 km.

**X8, exploratory.** In the band arm, every city's E3 curve lies inside the primary-frame envelope
at every *k*.

## 8. What each outcome means, written before the outcome is known

- **X2 holds.** The project's spatial nulls are a density result: at the density of existing
  networks no estimator beats a free raster, and with enough monitors interpolation does. The
  crossover density is reported, and the proposed Kandy network is judged against it.
- **X2 fails.** The nulls hold across the full density range available in the world's openly
  published reference networks. The spatial purpose of a Kandy monitoring campaign is closed.
- **X4 binds early.** The limit is change of support, not monitor count.
- **X7** converts a monitor count into a coverage statement: how much of a city one monitor informs.

**None of these outcomes validates the Kandy field.** The band arm holds at most three cities.

## 9. Deviations

Any departure from this document is reported beside the result it affects, with its reason. If a
specified step cannot be run, that is reported as a failure to test, not replaced by an alternative
chosen after the data are seen.
