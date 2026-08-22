# Pre-registration — Colombo zero-shot out-of-regime test

**Written 2026-08-22, BEFORE the analysis is run.** No Colombo skill number has been computed
under this design. The reference distributions in §5 are panel statistics that already existed
(`ladder_all.csv`, 47 cities) and contain no Colombo result.

⚠ **Register this on OSF before running.** Every previous pre-registration in this project lives
as an untracked local file, so none carries verifiable timing (see §9). This is the one that can
still be done properly, and the paper should contain at least one registration a reader can check.

---

## 1. Why this test

The budget ladder was validated across 47 cities, 32 countries and four latitude bands. That
supports a claim of generality. It has never been tested against a city chosen specifically
because the model **should struggle there**.

Colombo is that city:

- **Coastal.** The production spatial machinery is valley physics — confinement is
  `M = 1 + κ·w(BLH)·c` with `c = z-score(−Δz)`, which is degenerate on flat coastal ground, and
  the dominant coastal mechanisms (sea breeze, marine boundary layer, sea-salt aerosol) have **no
  representation in the model at all**.
- **Reference-grade.** The US Embassy BAM gives 1,661 daily observations — the best ground truth
  in the country, and far better than anything at Kandy.
- **Genuinely held out.** Sri Lanka appears nowhere in the 47-city panel (verified against
  `openaq_manifest.csv`), so no Colombo data entered the `Bud0` learner.
- **Same country and monsoon as the target**, which isolates *regime* from *region*.

## 2. Hypothesis

**H:** The sensorless tier `Bud0` — a leave-one-city-out learner on globally available drivers
only — transfers to a coastal city outside the model's design regime with skill inside the
panel's own distribution.

**H is falsifiable and I expect it to fail on one axis** (§4).

## 3. Design

- **Model:** `fit_bud0` unchanged (`modular_validation_all.py`), `HistGradientBoostingRegressor`,
  `max_iter=300`, `learning_rate=0.06`. Trained on all 47 panel cities; Colombo held out entirely.
- **Features:** the frozen `FEATS` set only — `temperature_2m`, `u_component_of_wind_10m`,
  `v_component_of_wind_10m`, `wind`, `boundary_layer_height`, `doy_sin`, `doy_cos`. **No local
  observations, no lags, no satellite AOD, no reanalysis PM.**
- **Target:** daily mean PM2.5, US Embassy Colombo BAM,
  `data/processed/stage1_v2/dataset_v2_colombo_daily.parquet`, column `pm25_observed`.
- **Drivers:** built from `data/raw/era5_colombo/*.csv`, hourly → daily mean, **in the same units
  and with the same aggregation as the panel pipeline**. ⚠ This is the single largest technical
  risk in the test (§7).
- **Seeds:** 3 runs, seeds 0/1/2; report the median and the spread.

## 4. Registered priors — stated as numbers so they can be wrong

| | prior | reasoning |
|---|---|---|
| **seasonal** | monthly-mean r ≥ **0.6** | monsoon timing is regional and is carried by BLH, wind and day-of-year; the panel's deep-tropical arm already transfers seasonally |
| **level** | absolute bias **worse** than the panel median; I expect **15–40% low** | sea salt is a real PM2.5 component in Colombo that no driver represents, and sea-breeze ventilation is absent from the feature set |
| **daily** | RMSE inside the tropical p10–p90 band, **but in the upper half** | day-to-day variance at a coastal site is driven by sea-breeze onset, which the drivers do not resolve |
| **overall** | **H survives on seasonal and daily, fails on level** | — |

If instead the level comes out *better* than the panel median, the ladder is **more** general
than claimed and that must be reported as such.

## 5. Gates, with thresholds fixed now

Reference distribution: the 47-city panel's own `Bud0` RMSE. Deep-tropical median **17.43**;
tropical + deep-tropical p10–p90 **[13.43, 45.54]**.

| gate | criterion | meaning if failed |
|---|---|---|
| **C-G1** | daily RMSE within **[13.43, 45.54]** | Colombo is an outlier against the panel; generality claim narrows to non-coastal |
| **C-G2** | monthly-mean seasonal r ≥ **0.60** | the seasonal cycle does not transfer out of regime |
| **C-G3** | absolute level bias ≤ **40%** | the sensorless level is not usable in a coastal regime |
| **C-G4** | daily R² > **0** against a climatological (day-of-year mean) baseline | the model adds nothing over knowing the date |

**C-G4 is the real test.** A model can post a respectable RMSE purely by reproducing the seasonal
climatology. If it cannot beat day-of-year climatology it has learned nothing transferable, and
that outcome must be reported however the other three land.

## 6. Stopping rule

**One analysis, one report.** No re-specification of features, model, period, or metric after
seeing any result. If the driver build proves incompatible (§7), the test is declared
**inconclusive on technical grounds** and reported as such — it is not re-run with a modified
feature set to obtain a number.

## 7. Known technical risk, declared in advance

Colombo's ERA5 file is a different product path from the panel's driver pipeline. A units
mismatch (K vs °C), a different daily-aggregation convention, or a differing `wind` definition
would produce a **spuriously bad** result that looks like a regime failure. Mitigation, fixed now:
before scoring, verify that Colombo's driver distributions (mean, sd, range for each of the seven
features) fall inside the panel's per-feature range. **If they do not, the test is inconclusive
(§6), not failed.**

## 8. What this test does NOT establish

- Nothing about the **spatial** field at Colombo. One point monitor cannot test a spatial pattern,
  and the change-of-support limit (F.69/F.76/F.77) applies to this comparison exactly as it does
  everywhere else.
- Nothing about `Bud1`–`Bud3`. Sri Lanka has too few OpenAQ stations to populate the higher rungs;
  this tests the **sensorless tier only**.
- It is **one city**. A single out-of-regime success does not license "works coastal"; a single
  failure does not refute the panel. It bounds the claim, it does not replace the panel.

## 9. Registration status — stated honestly

This project has nine pre-registration documents with gates, priors, stopping rules and
amendments, and they demonstrably did work: two registered priors were refuted, three confounds
were caught before scoring, and one published claim was withdrawn when its own falsifier fired.

**But none of them is git-tracked or third-party registered**, so none carries timing a reader can
verify. The paper must say so, and must rest their credibility on the fact that **they fired
against us** rather than on unverifiable dating.

**This document is the exception and must remain so:** commit it, push it, and register it on OSF
**before** `scripts/colombo_zeroshot_test.py` is run for the first time.
