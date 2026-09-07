# Pre-registration — do EO foundation-model embeddings break the within-city spatial ceiling?

**Lodged before the analysis was run.** Project: Kandy PM2.5 (Daminda Alahakoon, University of
Peradeniya). Date drafted: 2026-09-09.

---

## 1. Why this test exists, and why now

This project has recorded six independent nulls on within-city spatial pattern for PM2.5. One of
them used AlphaEarth satellite embeddings (`scripts/alphaearth_spatial_test.py`, ledger F.27) and
returned a partial correlation of **+0.066** with the physics pattern regressed out, p = 0.80, at
Medellín.

**That null is underpowered and this project has already said so in writing.** Ledger **F.28**
records the minimum detectable partial correlation at 80% power as **0.65** at Medellín (n = 17),
**0.82** at Chiang Mai (n = 10) and **0.96** at Kathmandu (n = 6), and states that the test
"excludes only a LARGE independent embedding signal". It was run on three cities and 33 stations
between them.

Since then this project built a much better-powered frame for exactly this question. Ledger
**F.105** scored seven spatial model families on **47 cities and 636 stations** with a
**detection limit of 0.130**, against a benchmark of **0.301** (built-up land-cover fraction within
2.4 km). That frame is five to seven times more sensitive than the frame the embedding null was run
on, and the embeddings have never been tested on it.

An external reviewer independently identified the gap this closes: the benchmark is *"the best
predictor among the predictors you happened to assemble, not a mathematical maximum over all
possible covariates."* Embeddings are a genuinely different information source rather than another
model family, so they test the information limit rather than re-testing the model limit that F.105
already settled.

## 2. Data and admissibility

**Predictor.** `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` (AlphaEarth Foundations), 64 bands, 10 m,
annual, 2017–2025. Verified reachable on 2026-09-09; a 40-station probe over the scoring frame
returned embeddings at 40 of 40 locations.

**Admissibility at `Bud0`, which is the condition that matters.** The embeddings are global, free,
annual, and require no observation at the target city. A city with no monitors can obtain them.
This is the same admissibility class as the benchmark raster and is the reason the test is
meaningful for Kandy at all.

⚠ **One admissibility risk is declared in advance.** AlphaEarth assimilates Sentinel-1, Sentinel-2,
Landsat, ERA5-Land, GRACE, GEDI and descriptive text. It is not known to ingest ground PM2.5
monitor data, but this project has already been caught once by a fused product that silently
contained the observations being priced (ledger C1/F.95, where GHAP trains on ~9,500 stations
including this panel's own sources). **If the embeddings pass the bar below, the result will not be
reported until the training-corpus question has been resolved**, and the pass will be labelled
provisional until then. A failure needs no such check, because contamination could only inflate a
score.

**Frame.** `data/processed/modular/lur_predictors.csv` — 636 stations, 47 cities, the same frame
F.105 used. Both predictors and target are standardised within city, so no model can score by
rediscovering that some cities are dirtier than others. The quantity is purely the within-city
ranking of stations.

**Scoring.** Leave-one-CITY-out. The target city contributes no observation to any fit. Spearman
rank correlation of predicted against observed station means, per city.

## 3. Hypotheses and gates, fixed here

The benchmark, the detection limit and the bar are taken from F.105 and are not renegotiable after
seeing the result.

| quantity | value |
|---|---|
| benchmark (best single free raster, `lc_built_2400`) | **ρ = 0.301** |
| minimum detectable paired improvement on this frame | **0.130** |
| **the bar** | **paired median improvement over the benchmark > 0.130, with a bootstrap interval over cities excluding 0.130** |

**E1 (confirmatory).** Embeddings alone, fitted leave-one-city-out, beat the benchmark by more than
the detection limit.
*Registered expectation: E1 FAILS.* Three reasons, stated now so that a failure cannot be presented
as a prediction and a success cannot be presented as expected. First, the published prior art
closest to this test ([Quito, *Remote Sensing* 17:3472, 2025](https://www.mdpi.com/2072-4292/17/20/3472))
reports R² ≈ 0.71 for NO₂ and SO₂ but only *moderate* accuracy for PM2.5, and PM2.5 is the
pollutant here. Second, six prior nulls. Third, and most important, ledger F.68/F.69 establish that
Kandy's within-city signal decays over tens to hundreds of metres, so the pattern is **sub-grid by
construction** and no annual surface covariate can place it.

**E2 (confirmatory).** Embeddings *added to* the existing 60-predictor set beat that set by more
than the detection limit. This separates "embeddings carry signal" from "embeddings carry signal
the assembled covariates do not already carry".
*Registered expectation: E2 FAILS.*

**E3 (confirmatory).** Embeddings carry signal independent of the benchmark: partial Spearman
correlation with `lc_built_2400` regressed out, tested against zero, pooled over cities.
*Registered expectation: E3 is undetectable.* This is the same quantity the underpowered F.27 test
estimated at +0.066; the value of running it here is the power, not the novelty.

**E4 (exploratory, labelled as such and not counted as a confirmatory outcome).** Whether any skill
that does appear is concentrated in a small subset of the 64 bands, as the Quito study reports.

## 4. What each outcome means, written before the outcome is known

**If E1 or E2 passes.** The within-city spatial ceiling is not an information limit in the form this
project has claimed. Chapter 8's central negative result would require substantial revision, the
sixth null would be superseded, and the campaign design of §9.7 would need rethinking because a free
global covariate would have done what the campaign was partly meant to test. The leakage check in §2
becomes mandatory before any of that is written down.

**If all three fail.** The strongest available foundation-model covariate does not beat a single
free raster on 47 cities, at a detection limit of 0.130 rather than the 0.65 the previous embedding
test could resolve. That converts an **underpowered** null into a **bounded** one, which is exactly
the upgrade F.105 and the Phase 2 registration made for their own questions. The claim it licenses:
*on 47 cities and 636 stations, 64-dimensional EO foundation-model embeddings do not beat the best
single globally available raster by more than 0.130 in rank correlation.*

**A null here does not establish that sub-kilometre PM2.5 is unpredictable.** It bounds what this
information and these model classes recovered on this frame. That distinction is load-bearing
throughout Chapter 8 and applies to this test unchanged.

## 5. Analysis specification

- Estimator: RidgeCV over the 64 embedding dimensions (E1); RidgeCV over 60 existing predictors
  with and without the 64 embedding dimensions (E2). Ridge because the F.105 tournament used it and
  because 64 dimensions on a median city of 12 stations would otherwise fit noise.
- Embedding value per station: mean over a **100 m** buffer, mosaicked over **2023**, the midpoint
  of the panel's span. A sensitivity over 2021–2024 is exploratory.
- **Paired within city, bootstrapped over cities, 4000 resamples.** A difference of medians is not
  an effect, and on this panel it has pointed the wrong way twice (gotcha #91).
- Cities with fewer than 6 stations are excluded, as in F.105.

## 6. Deviations

Any deviation from this document will be recorded in the results with its reason. The bar in §3 is
fixed. If the analysis cannot be run as specified, that will be reported as a failure to test rather
than as a null.
