# Local fraction at Kandy from measurements — specification (2026-10-11)

Written and committed **before any estimator below was computed**. Exploratory: it is not lodged with OSF, but the
git commit that adds this file precedes every result file it names. Ledger entry on completion: F.134.

## The quantity under test

The thesis's local fraction is a model quantity: `f = 1 − ⟨B⟩/⟨T⟩` per year, averaged over 2019–2023, where `B` is a
background uniform over the basin within each day and `T` the basin mean (production 0.479, 0.428–0.489 across cap
specifications; F.133). No measurement observes `f` directly. Each estimator below measures something related, and
**each is compared with the model computed the same way, at the same place, on the same days** — never with 0.479
directly. A measured value at the station's cell is expected to exceed the basin value, because the city centre carries
more local increment than the basin mean.

Model comparison quantities (from the delivered field and its background):
- `f_model_cell = 1 − ⟨B⟩/⟨PM_cell⟩` at the cell containing the CEA Kandy station (7.2906 N, 80.6337 E), on the
  estimator's matched days.
- `f_model_basin = 1 − ⟨B⟩/⟨T⟩` on the same days.

## E1 — urban increment against a regional network (primary)

Lenschow et al. (2001) urban increment: `f_E1 = 1 − ⟨R⟩/⟨K⟩`, `K` = CEA Kandy AAQMS daily PM2.5, `R` = daily regional
background.
- Regional sensors: the IQAir units on CEA AirShare (equipment 4) at sites **within 150 km of Kandy and outside the
  Colombo urban area**, daily means, from their start (late 2024/2025) to 2026-10-10.
- Calibration: IQAir units are low-cost. At Battaramulla an IQAir unit is co-located with a reference AAQMS. Fit
  `AAQMS = a + b·IQAir` on matched days by ordinary least squares and apply it to every IQAir site. Report the fit and
  its r. If the co-located r < 0.7 or fewer than 60 matched days exist, report E1 uncalibrated as well, and flag it.
- `R` primary: the median of the calibrated regional sites each day (at least two reporting). Sensitivities: the daily
  minimum (closest to a clean background; biases `f` up) and the all-island median excluding Colombo and Kandy.
- Matched days: `K` and `R` both present. Bootstrap by calendar month (4000 resamples) for 95 % intervals.
- Model comparison: the 2024–2026 extension tier (`_v3_drv`, `B_*_v2_drv`) on the same days; and, because that tier's
  level is known to read low against CEA (F.131/F.132), also the 2019–2023 delivered field over the same calendar
  months (climatological comparison).
- Known bias: regional sites are towns with their own local increment, so `R` is high and `f_E1` is a **lower bound**
  on the urban increment at the station, except under the daily-minimum sensitivity.

## E2 — combustion-tracer intercept (independent, covers 2019–2023)

At the CEA Kandy AAQMS, hourly, local time corrected per source (gotcha #106). For each calendar month of each year with
at least 300 hours of PM2.5 and CO: regress PM2.5 on CO by Theil–Sen; take `CO_bg` = the month's 5th percentile of
CO; the background is `PM_bg = intercept + slope·CO_bg`, floored at 0; `f_E2 = 1 − Σ PM_bg·n / Σ PM` over months.
Sensitivities: NO2 instead of CO; 10th percentile for the tracer background.
- Biases: local non-combustion PM (resuspended dust) and locally formed secondary aerosol do not track CO, so they
  fall into the background (`f_E2` low); regional plumes that carry CO raise the slope (direction mixed). Reported as
  an independent route, not a better one.
- Model comparison: `f_model_cell` and `f_model_basin` on the same hours (2019–2023).

## E3 — the 2020 curfew (context, not a bound unless the regional change is known)

Ratio `ρ = K / T_cf`, `T_cf` = the model's temporal anchor (its predictors include the GEOS-CF composition forecast, run
with business-as-usual emissions). Effect `D = 1 − ⟨ρ⟩_curfew / ⟨ρ⟩_reference`, curfew 2020-03-20 → 2020-05-10,
reference = the same calendar window in 2019 and 2021 where available. With local emissions cut by a fraction `a ≤ 1`
and regional by `r ≥ 0`, `D = f·a + (1−f)·r`; `D` is a lower bound on `f` only if `r = 0`, which the concurrent South
Asian lockdowns make unlikely. Reported with the literature values; not used to bound `f`.

## E4 — literature

Map each published Kandy or Sri Lanka figure (lockdown reductions, PMF source shares, transboundary studies) to the
quantity it measures, and state whether it bears on `f`.

## Decision rule (fixed now)

The model's `f` is called **consistent with measurement** if `f_model_cell` lies inside the E1 primary 95 % interval or
between the E1 primary and E1 daily-minimum point values; **too high** if it lies above the E1 daily-minimum value;
**too low** if it lies below the E1 primary lower bound. E2 is reported beside it, with the same comparison, as a
second route. No estimator replaces the model's `f` in the thesis without the user's decision.

## Outputs

`scripts/pull_cea_airshare_network.py`, `scripts/local_fraction_e1.py`, `local_fraction_e2.py`, `local_fraction_e3.py`
→ `data/processed/decomp/local_fraction_study.json`; results note `docs/local_fraction_study_results_2026-10-11.md`.
