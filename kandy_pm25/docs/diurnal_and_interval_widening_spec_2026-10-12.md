# Daily-cycle correction from the CEA station, and interval widening — spec (2026-10-12)

Written and committed before either step was scored. Exploratory, not registered. Follows F.136.

The split is the one already used for the level factor β (F.132): **calibration** 2019-01-01 → 2021-06-30 (the
station's earlier days), **held-out** 2021-07-01 → 2023-12-31 (in practice 2022-10 onward). Nothing below is fitted on
held-out days.

## Step 1 — the daily-cycle test (scenario first)

**Why.** The field's nights run too high at the station (night/midday 1.17 against 0.71) and the hourly interval misses
follow that cycle error (F.136). T(t) is sharpened to the hour-of-day climatology of the two FECT low-cost sensors
(`sharpen_T_diurnal.py`), whose record was humidity-corrected with a constant RH. The reference station is the better
target for the cycle's shape, if it holds on days it was not fitted to.

**Scenario.** T′(t) = T(t) × r(h), h = local hour, with r(h) the ratio of the station's normalised hour-of-day
climatology to the field's at the station cell, both on calibration-period hours where the station reports. Because the
field is B + max(T−B,0)·P + …, a ratio applied to T does not move the cell by the same ratio, so r is found by a fixed
point (3 iterations: apply, rebuild the cell, re-take the ratio), on calibration hours only. Each year's mean of T is then
restored (the level is β·VanD and unchanged). B is rebuilt with the production builder (`build_B_v2(..., T_override)`),
because the coherence cap depends on each day's lowest T. The cell field is reassembled with the delivered pattern P at
that cell (recovered from the stored field) and the stored ε-floor (2.907). Sensitivity: r by hour × two seasons
(south-west monsoon May–Sep; rest).

**Scores, held-out hours, production against scenario:** correlation of the 24-hour climatology with the station's;
night (00–05) / midday (11–15) and morning (06–09) / midday ratios; hourly r and RMSE; daily r and level bias; hourly
90 % coverage (unwidened). Also reported: the local fraction f under the scenario, and the fit to the FECT sensors
(in-sample; it is expected to worsen).

**Adoption rule, fixed now.** Adopt the scenario as the delivered field only if, on held-out hours, ALL of:
(a) hourly RMSE is lower; (b) the absolute error of the night/midday ratio is at most half the production error;
(c) daily r falls by no more than 0.02. Otherwise it is reported as a scenario and the field is unchanged. The change in
f is reported, not gated; if f leaves the measured range 0.36–0.53 (F.134), that is stated as a consequence.

## Step 2 — the interval widening (on whichever field step 1 leaves)

**Rule.** One symmetric factor k scales the spread of T's quantiles about the median before assembly:
T05′ = T50 − k(T50 − T05), T95′ = T50 + k(T95 − T50). It is applied inside the field builders
(`build_additive_field_v2.assemble_v2`, `kandy_extension_fields.py`), read from `interval_widening.json` written by the
fitting script, and the builders refuse to run without it (as for β). T(t)'s own files are not changed. Because the
widening is applied to the anchor quantiles before the split, the basin mean of each field quantile still equals its
anchor exactly and the webapp reconstruction stays exact.

**Fit.** k is the smallest value (grid 0.01) giving ≥ 90 % hourly coverage at the station cell on **calibration**
hours, computed with the same cell assembly as step 1. **Check:** held-out hourly coverage, misses below/above, daily
coverage (averaged quantiles), and coverage at the FECT sensors. Reported as is; no second fit.
The extension tier receives the same k; its coverage is reported but its level error (~−40 %) is not addressed by a
width factor.

## Outputs
`data/processed/decomp/diurnal_cea_scenario.json`, `data/processed/decomp/interval_widening.json`;
scripts `scripts/kandy_diurnal_cea_scenario.py`, `scripts/kandy_interval_widen_fit.py`.
