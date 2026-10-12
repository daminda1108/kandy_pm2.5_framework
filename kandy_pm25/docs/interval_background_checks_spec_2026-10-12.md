# Interval and background checks against CEA records — spec (2026-10-12)

Written and committed before either check was scored. Exploratory, not registered. Ledger entry on completion.

## A. The shipped 90 % interval at the CEA regulatory station

**Why.** The only coverage figure for the delivered field (77.3 %, 88.6 % after removing each sensor's median offset;
`kandy_interval_coverage.py`) is measured at the two FECT sensors, which the temporal anchor was trained and sharpened
on, so it is in-sample (gotcha #68). The CEA station is the first instrument the field was not fitted to, except for the
level factor β, which used 2019-01 → 2021-06.

**Object.** `[pm25_q05, pm25_q95]` of `kandy_decomp_predictions_{y}_additive_v3.parquet` at the 1 km cell nearest the
station (7.2906 N, 80.6337 E), clipped at 0 as displayed (same convention as `kandy_interval_coverage.py`). Station
hourly PM2.5 on `t_local` (gotcha #106), duplicates averaged; field time converted UTC → Asia/Colombo.

**Periods.** calibration 2019-01-01 → 2021-06-30 (β fitted here); held-out 2021-07-01 → 2023-12-31 (in practice from
2022-10, after the station gap); extension 2024 → 2026 (`_additive_v3_drv`), reported separately.

**Metrics.** coverage; fraction below / above; mean width; median offset (model q50 − observed); coverage of the same
width after removing the period's median offset (centring against width, gotcha #75); coverage by local-hour band
(night 00–05, morning 06–09, midday 11–15, evening 17–20) and by season. Daily (secondary): station daily mean against
the daily mean of q05/q95 — an approximation that overstates coverage when hourly errors are not fully correlated
within the day; reported with that caveat.

**Reading, fixed now.** On the held-out period: coverage ≥ 85 % → consistent with nominal. Below 85 % → one-sided
(one tail ≥ 3× the other) and re-centred coverage ≥ 85 % → a centring error, width adequate; otherwise → the interval is
too narrow, and the ratio of the width needed for 90 % to the shipped width is reported. Calibration-period coverage is
reported but not read as independent, because β was fitted on it.

## B. The background's day-to-day signal against the regional network

**Why.** B(t) has had one external check (NBRO regional stations, daily r 0.37). The AirShare regional IQAir units
give a second, independent record of the regional air Kandy sits in.

**Scope limit.** The regional units report from 2024-06 only, so the delivered 2019–2023 background cannot be scored.
What can be scored is the background **construction** applied to 2024–2025, where GEOS-CF and the trajectory archive
exist, and the extension tier's shipped background.

**Regional record R(d).** As E1 (`local_fraction_e1.py`): IQAir daily means calibrated against the Battaramulla AAQMS,
sites within 150 km of Kandy outside the Colombo area, median over ≥ 2 reporting sites. Sensitivity: all-island median
(excluding Colombo and Kandy).

**Arms.**
1. `B_method`: the delivered construction (`build_additive_field_v2.build_B_v2` logic: air-mass class level × within-class
   GEOS-CF daily modulation), before the coherence cap, built for 2024–2025. Scale-free; only correlations are read.
2. `B_ext`: the shipped extension background `B_background_hourly_{y}_v2_drv`, daily mean.
3. `GEOS-CF`: the raw daily prior alone.
4. Comparators: `T_ext` (extension temporal anchor, basin mean) and `K` (CEA Kandy station).

**Metrics.** daily Pearson r with R, month-block bootstrap 95 % CI (4000); within-month anomaly r (each series minus its
calendar-month mean), which removes the shared seasonal cycle. Level ratio B_ext / R reported but secondary (the
extension tier's level is known to read ~40 % low at the station).

**Reading, fixed now.** Descriptive. The background is meant to be the regional part, so the informative comparison is
B against R relative to K against R: B_method anomaly r at or above K's anomaly r = the construction captures the
regional day-to-day signal as well as Kandy's own station shares it; anomaly r with a CI including 0 = the background's
day-to-day variation is not supported. If `B_ext` scores like `T_ext`, say so: it is built as a monthly multiple of T.

## Outputs
`data/processed/decomp/kandy_cea_interval_check.json`, `data/processed/decomp/background_regional_check.json`.
Scripts `scripts/kandy_cea_interval_check.py`, `scripts/background_regional_check.py`.
