# The deployed Kandy model as a rung of the ladder: specification (2026-10-10)

**Status: EXPLORATORY, specified before any scoring.** This file is committed to git before
`scripts/ladder_v2_kandy_model.py` produces a single number, so the commit time is the record that
the arms, the data, the losses and the summary were fixed blind. It is not an OSF registration
(lodging one is the author's decision). No registered result is altered by it.

## Why

The thesis validates the Kandy reconstruction "without local ground truth" by reducing monitored
cities to Kandy's information budget and scoring against monitors withheld from them. The ladder
does that, but its sensorless rung is a gradient-boosted model of the daily city mean, not the
model deployed at Kandy. The thesis therefore could not say how the **deployed** model performs
at Kandy's budget. This test puts the deployed model's temporal anchor on the ladder.

Only the temporal anchor T(t) is needed. The delivered field is
B + max(T − B, 0)·P + min(T − B, 0) + ε(P − 1) with P of unit spatial mean, so its city mean is T(t)
exactly (to the documented 0.4–0.6 % build drift). The background B and the pattern P cannot change
a daily city-mean score.

## Data

- Cities, stations, held-out sets, splits: the ladder union (`ladder_v2_confirm.union("maiac")`), the
  same 21 seeds and the same station shuffle as `ladder_v2.rungs` / `ladder_v2_review.sym`
  (held = first max(3, n/3) shuffled stations; pool = the rest). Same daily target: the mean of the
  held-out stations.
- GEOS-CF PM25_RH35_GCC, daily mean of hourly values, area mean over the bounding box of each city's
  urban-centre sample points (`pull_kandy_model_priors.py`). GEE coverage ends 2026-01-02, so only
  days up to 2025-12-31 are scored, for **every** arm.
- van Donkelaar V6.GL.02 annual mean over the same box, 2019–2022. Years after 2022 use the 2022
  value, as the Kandy chain uses its last tile as a proxy (Amendment 2).
- Meteorological drivers: the ladder frame's daily ERA5 drivers for that city (no new pull).

## Arms (all scored on the identical set of days per city × split)

| arm | what it is | local stations it uses |
|---|---|---|
| `Bud0` | the ladder's sensorless rung (cached LOCO bag-of-5, `review_bud0_registered_loco_b5`) | none |
| `Bud0cal2` | `Bud0` with an intercept and slope fitted to the first two pool stations (the registered first-two rung before shrinkage) | pool[0:2], calibration only |
| `K0` | Kandy chain with no stations: GEOS-CF daily series, additively shifted per calendar year so its annual mean equals the van Donkelaar level | none |
| `K2` | **Kandy chain as deployed**, with pool[0:2] as the anchor pair: ratio = row-mean(anchor)/row-mean(prior); residual target anchor − prior·ratio; LightGBM quantile heads (0.05/0.50/0.95, `t_anchor.LGBM_PARAMS`) on day-of-year harmonics, day of week, BLH, u10, v10, wind speed, t2m and the scaled prior; CV+ Mondrian conformal by month on 5 sequential folds; monthly amplitude sharpening to the anchor climatology (clip 0.5–2); per-year additive re-anchor to van Donkelaar | pool[0:2], training and calibration only, never read on the day |
| `L2same` | first two pool stations read on the day, exactly as the review's symmetric `L2s` arm without shrinkage: the daily mean of pool[2:6] (never the held-out set) regressed on (1, Bud0, mean of pool[0:2]); Bud0 affine fallback on days the pair is missing; needs pool ≥ 6 | pool[0:2] read on the day; pool[2:6] fit only |

(Amended before scoring, same day: the first draft fitted `L2same` on the held-out mean, which would
score it in sample.)

Daily resolution is a declared deviation from the hourly Kandy chain: the hour-of-day features and the
hour-of-day sharpening are dropped because the scored quantity is a daily mean. Everything else is
`src/transfer_validation/t_anchor.py` unchanged.

Two uses, as in the ladder: **reconstruction** (K2 and the calibrations fitted over the scored
period, the position of Kandy's 2019–2023 reconstruction) and **prospective** (fitted on days before
the midpoint of the scored record, later half scored).

## Losses and summary

Per city × split: RMSE, the loss in the top decile of days (`tail`), the WHO 24-h exceedance balanced
error (`ladder_v2.losses`), Pearson r, bias as a per cent of the observed mean, and for K2 the
empirical coverage of its nominal 90 % interval. Gains are 100·(loss_Bud0 − loss_arm)/loss_Bud0.
Per city: median over splits. Across cities: median, with the two-level cluster bootstrap over
networks (`ladder_v2.boot_cluster`, 4000 draws, seed 20260927). Reported for the confirmation cities
and the union.

## Questions, fixed in advance (no directional predictions are registered)

Q1. Where does K2 sit relative to Bud0, Bud0cal2 and L2same on RMSE?
Q2. Does K0 (Kandy chain, no stations) beat Bud0 (the ladder's sensorless learner)?
Q3. What coverage does K2's nominal 90 % interval achieve against the held-out city mean?
Q4. Does the answer to Q1 change between the reconstruction and prospective uses?

Eligibility: a city × split is scored if the anchor pair has ≥ 120 days with a prior and the
held-out frame has ≥ 120 scored days. Excluded city × splits are counted and reported.
