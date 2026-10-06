# Spatial learning curve — registered results (OSF `rqn4y`, `26hp8`, `4whsc`, `4qs9c`), 2026-09-28

Scored once by `scripts/spatial_curve_run_summary.py` (preflight passed: 37 + 41 cached city results,
consolidated CPU-only E8/E9 from 7 kernels with every value finite, 15 E10 prediction files, controls
E10 3/3 passed and E11 3/3 failed). Positive control and leakage self-test re-passed inside the run.
Outputs `data/processed/modular/spatial_curve/{analysis,analysis_s70}/summary.json`; log
`spatial_curve/summary_run_2026-09-28.log`. **Primary frame: 18 cities, 7 countries; detection limit at
7 countries = 0.28 in ρ** (large: the test resolves only big effects).

## Verdicts (primary frame; S-1 70 % frame beside)

| id | prediction | result | verdict | S-1 |
|---|---|---|---|---|
| X1 | E3 (kriging) and E4 (IDW) rise with k | E3 rises; E4 does not rise monotonically | **refuted** | holds |
| X2 | E3 or E5 cross over the free raster by k ≤ 35 in ≥ half the cities | 61 % of cities (11/18) | **held** | holds (53 %) |
| X3 | ridge LUR (E2) saturates by k ≤ 12, within δ of the raster | k* = 3; E2 − E1 = −0.059 | **held** | holds |
| X4 | no curve exceeds the within-cell ceiling by more than δ | 2 cities with a ceiling, none exceeded | **held** | refuted |
| X5 | cLHS siting does not beat random ordering by more than δ | 0.00 [0.00, 0.00], 18 cities | **held** (see note) | holds |
| X6 | every per-day (Q2) curve lies below the static (Q1) curve | not below for E3, E4, E9 | **refuted** | refuted |
| X7 | median reach below 5 km | 1.0 km | **held** | holds (1.0) |
| X8 | band-arm cities inside the primary envelope (exploratory) | 3 of 4 scorable inside | exploratory | |
| X9 | no deep estimator beats regression kriging (E5) by more than δ | max advantage E10 +0.065, E8 +0.030, E9 +0.002 | **held** (E11 not interpreted) | holds |
| X10 | TabPFN with coordinates (E9) beats plain TabPFN (E8) for all k ≥ 12 | E9 worse: −0.052 [−0.103, −0.018] at k = 12 | **refuted** | refuted |
| X11 | deep prior's advantage over kriging is larger at k = 3–5 than at large k | E10: +0.037 (16 cities) | **held for E10**; E11 not interpreted | holds |
| X12 | E10 and E11 agree within δ | E11 not interpretable (failed control) | **not tested** | |
| X13 | deep arms on the band arm (exploratory) | E10 inside at 3 of 4 | exploratory | |

**X5 note.** As coded, X5 pools every estimator and takes medians of a statistic that has few distinct
values (Spearman on ~10 held-out sites). Estimators that never use the fitting stations (E0, E1, E7)
differ by exactly 0, which pins the median at 0.00. An exploratory check restricted to the
station-using estimators and averaged over the 100 replicates gives cLHS − random of at most
±0.012 in every case (E3 at k ≤ 12: +0.003, cLHS ahead in 11 of 18 cities). The verdict is unchanged:
siting strategy does not matter at a resolvable size, consistent with F.103.

## The curve (pooled median ρ by k, primary frame; cities per k shown)

| k (cities) | 3 (18) | 5 (18) | 8 (18) | 12 (16) | 18 (9) | 25 (7) | 35 (3) | 50 (3) | 70 (2) |
|---|---|---|---|---|---|---|---|---|---|
| free raster E1 | 0.18 | 0.18 | 0.18 | 0.18 | 0.22 | 0.23 | 0.18 | 0.18 | 0.20 |
| ridge LUR E2 | 0.11 | 0.12 | 0.18 | 0.22 | 0.33 | 0.33 | 0.34 | 0.37 | 0.39 |
| kriging E3 | 0.11 | 0.15 | 0.18 | 0.20 | 0.20 | 0.16 | 0.36 | 0.40 | 0.50 |
| regression kriging E5 | 0.10 | 0.17 | 0.21 | 0.29 | 0.30 | 0.31 | 0.40 | 0.42 | 0.45 |
| ConvGNP E10 | 0.18 | 0.21 | 0.20 | 0.21 | 0.19 | 0.21 | 0.21 | 0.20 | 0.24 |

⚠ Pooled medians at different k cover different cities (dense cities only at large k), so this table
describes; the verdicts use per-city paired quantities. Above k = 25 only 2–3 cities remain.

## Reading

Cities split. In 11 of 18, kriging or regression kriging beats the free built-up raster at some tested
k (5 of them already at 3 stations; median crossover 5 among those 11); in the other 7 no interpolator
beats the raster within the densities that exist. Pooled, skill rises from about 0.1 at 3 stations to
0.3 at 12–18 and 0.4–0.5 in the two or three densest networks. The ConvGNP deep prior stays flat near
the raster level. One station informs about 1 km. Choosing sites by design rather than at random buys
nothing measurable. The detection limit is large (0.28 at 7 countries), so only big effects are
resolvable. What this does **not** give: a station count for a Kandy map. Kandy is not represented in
this frame (1 tropical city), and whether it would be a crossing or a non-crossing city is unknown.
