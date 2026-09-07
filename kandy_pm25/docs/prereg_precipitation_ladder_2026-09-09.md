# Pre-registration — does wet removal belong in the ladder's bottom rung?

**Lodged before the analysis was run.** Project: Kandy PM2.5 (Daminda Alahakoon, University of
Peradeniya). Date drafted: 2026-09-09.

---

## 1. The defect this tests, which is not a data gap

The ladder's sensorless rung `Bud0a` is specified as *reanalysis drivers*. The feature list it
actually fits on is:

```
FEATS = [temperature_2m, u_component_of_wind_10m, v_component_of_wind_10m,
         wind, boundary_layer_height, doy_sin, doy_cos]
```

**There is no precipitation and no humidity in it, so wet removal is absent from the model's
meteorology entirely.** Table 9.1 already carries that as `NO MEASUREMENT: a known structural gap`.

What makes this worth registering rather than simply fixing is what was found on inspection:
**`total_precipitation_sum` is already present in the scored frame.** It was pulled, merged and
then never referenced, because it is not in `FEATS`. So `Bud0a` has a driver its budget admits,
sitting in its own input frame, and does not use it.

**That is the F.84 defect class.** F.84 found the scored `Bud0` using one of the three streams its
budget admitted, which inflated every gain measured above it and moved the headline from 25.6% to
17.9%. `Budget.require_covers()` was written to stop a recurrence, but it asserts coverage at the
level of *streams* — `DRIVERS`, `STATIC_GEO`, `SATELLITE_LEVEL` — and cannot see that a variable
inside an admitted stream is unused. **This registration therefore tests a live hypothesis about a
possible repeat of the most serious defect this project has found.**

## 2. The hazard that decides the design, declared before running

Precipitation is **62.8% complete** across the frame. **11 of 48 cities fall below 90% coverage and
at least one is at 0%.**

This is the exact shape of the C1/MAIAC defect recorded as gotcha #85: a stream that looks present,
is silently absent for many units, and is accepted without warning by a gradient-boosting learner
that tolerates missing values — there it produced a clean, plausible, entirely meaningless −0.41%.

Two design consequences, fixed here:

1. **Coverage is asserted before fitting**, not inspected afterwards. Cities below **90%**
   precipitation coverage are excluded from the comparison.
2. **The comparison is run on one fixed city set.** Both the with-precipitation and the
   without-precipitation ladder are scored on **the same cities**, so the contrast is the covariate
   and not a change of frame. Comparing a 48-city ladder against a 37-city ladder would confound
   the two and is specifically not what will be done.

## 3. Predictions, fixed here

The estimand is unchanged from the production ladder: median across cities of the per-city
percentage reduction in daily RMSE, paired within city, bootstrapped over cities.

**P1 — the bottom rung improves.** Adding precipitation lowers `Bud0a` RMSE.
*Registered expectation: HOLDS, modestly.* Wet deposition is a real removal mechanism and daily
rainfall is one of the few driver variables with a direct physical path to daily PM2.5.

**P2 — the gains measured above it shrink.** A better sensorless rung leaves less headroom, so
`Bud0c → Bud1` falls.
*Registered expectation: HOLDS.* This is the F.84 mechanism, and it is the reason this test matters
beyond one number: if P1 holds and P2 holds, several published gains are overstated.

**P3 — the redundancy null survives.** Stations three to six remain bounded near zero.
*Registered expectation: HOLDS.* It has survived four losses, a cluster bootstrap and seven
estimators; a driver variable should not disturb it.

**P4 — the background rung remains the largest single gain.**
*Registered expectation: HOLDS.*

**P5 — the deep-tropical ordering does not reverse.** Local observations continue to outrank the
background proxy in Kandy's own band on daily RMSE.
*Registered expectation: HOLDS in direction.* ⚠ This is the prediction most likely to fail, because
that band is thirteen cities and F.109 already showed its interval is fragile to resampling detail.
A reversal here would be a material result and would be reported as one.

## 4. What each outcome means, written before it is known

**If P1 and P2 both hold.** The ladder has been under-using an admitted driver, exactly as in F.84,
and every gain above `Bud0a` in the current thesis is overstated by the amount P2 measures. The
affected numbers would be re-derived and the thesis corrected. The finding would also show that
`require_covers()` is insufficient as written, because stream-level coverage cannot detect an
unused variable inside an admitted stream.

**If P1 holds and P2 does not.** Precipitation adds skill at the bottom without displacing anything
above, meaning the streams are complementary rather than substitutable. The ladder's conclusions
stand and the driver set improves.

**If P1 fails.** Daily rainfall carries no usable signal for daily city-mean PM2.5 on this panel at
this resolution. That is a reportable null and it closes a gap Table 9.1 currently lists as
unmeasured — but it must not be read as *wet removal does not matter*, only that an 11 km reanalysis
daily total does not improve this prediction.

**If the coverage assertion fails**, the result is reported as a **failure to test**, not as a null.

## 5. Analysis specification

- Estimator, seed, tier construction, shrinkage and holdout are **unchanged** from
  `modular_validation_all` and `ladder_order_and_bootstrap`. The only difference between arms is the
  presence of `total_precipitation_sum` in the feature list.
- Both arms use the identical city set, identical station roles and identical random seed, so the
  pairing is exact.
- Precipitation enters as the daily total already present in the frame. ⚠ `ECMWF/ERA5_LAND/DAILY_AGGR`
  supplies `total_precipitation_sum` as a daily sum, so gotcha #60's de-accumulation does **not**
  apply; this is asserted by checking the value range is physical rather than assumed.
- Bootstrap over cities, 4000 resamples, paired within city. A difference of medians is not an
  effect and will not be quoted as one.

## 6. Deviations

Any deviation will be recorded with its reason. If the analysis cannot be run as specified, that is
a failure to test rather than a null.
