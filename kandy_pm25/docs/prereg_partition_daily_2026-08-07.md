# Pre-registration — daily-resolution reference partition (second attempt)

**Written 2026-08-07, BEFORE any number was computed.**

## This is a second attempt, and the first one failed

`docs/prereg_partition_identification_2026-08-07.md` registered an **hourly** reference
partition at the panel cities. It **failed its own gate P4**: only 3 of 10 cities passed,
against a required 5. The binding failure was P2 — in 13–25% of hours at five cities, the
peripheral 10th percentile *exceeded* the network mean, i.e. the periphery was not cleaner
than the core. That is recorded as ledger **F.40** and is not being quietly set aside.

Two candidate explanations were identified there and could not be separated: genuine physics
(hourly background/increment decomposition may be ill-posed a fifth of the time), or sampling
noise (the failing cities have ~4 peripheral stations, where a 10th percentile is unstable,
while the three passing cities have 13, 6 and 5). **This registration tests that distinction
directly** and, if the noise explanation holds, recovers a usable reference at a coarser
resolution.

**What is being changed, and the cost of changing it.** The reference moves from hourly to
**daily** resolution. Averaging suppresses the sampling noise but forfeits the diurnal
component of the partition — the 0.17 diurnal swing measured in F.40 would become
un-modelled and must be disclosed as such. What survives is the day-to-day and seasonal
variation, which is the larger part of the physical premise (F.40 measured a **1.66×**
seasonal swing) and the part that responds to Indo-Gangetic outflow and the monsoon.

Nothing else changes: the same cities, the same leakage-free core/periphery split by
traffic-emission percentile, the same 10th-percentile lower envelope, the same gate
thresholds. **Only the temporal resolution of the reference differs.** Gate thresholds are
deliberately *not* relaxed — relaxing them after seeing that exactly three cities passed is
the post-hoc screening this project criticised in its own referee review.

## Method

Station daily means → core/periphery groups by traffic-emission percentile (a model input,
no concentration data) → `B_ref(day)` = 10th percentile across peripheral stations' daily
means → `L_ref = T_ref − B_ref`, `f_ref = L_ref / T_ref`. A day is usable only if at least
two peripheral stations and at least 12 hours report.

## Gates (thresholds unchanged from the hourly registration)

- **Q1** peripheral group's median emission percentile below the core group's by ≥ 0.25.
- **Q2** `B_ref < T_ref` and `f_ref ∈ (0,1)` on ≥ 95% of usable **days**.
- **Q3** `|r(f_ref, n_reporting_stations)| ≤ 0.5` across days.
- **Q4** at least **5** cities pass Q1–Q3, else this route is abandoned and the partition
  stays a disclosed constant. **There will be no third attempt at a different resolution.**

## The diagnostic this registration exists to produce

- **D1 — noise or physics?** For every city, report the ordering rate at hourly and at daily
  resolution side by side, against the number of peripheral stations. If the improvement is
  concentrated at the cities with few peripheral stations, the hourly failure was **sampling
  noise**; if ordering stays poor at daily resolution even where networks are dense, it is
  **physics**, and the `B > T` incoherence at Kandy (28.5% of hours, F.17) is intrinsic to
  the decomposition rather than a defect of our construction. Either answer is worth having
  and both are reported.

## Predictions, published in advance

- **Q2 improves substantially** — I expect daily ordering rates of 92–99% where hourly was
  75–87%.
- **Q4 passes with 5 to 7 cities.** I am genuinely unsure; 4 peripheral stations remains thin
  even daily, so this could fail again.
- **D1 comes out mostly "noise"** — I expect the improvement to be largest at Yichang and
  Chiang Mai (hourly 75%, 78%, four peripheral stations each).
- **`f_ref` stays near 0.4** at the passing cities and retains a seasonal swing above 1.4×.
  If the daily mean `f_ref` moves far from the 0.398 measured hourly, the reference is
  resolution-dependent and **neither version should be trusted**.

## If Q4 passes

Proceed to steps 2–5 of the parent registration (MERRA-2 speciation → estimator under the
two-sensor budget → transfer validation gates T1–T4 → Kandy) with `f` estimated at **daily**
resolution, and the diurnal component explicitly declared un-modelled.

**Artifacts:** `scripts/panel_reference_partition.py --daily` →
`results/figures/multicity/panel_reference_partition_daily.{csv,json}`.
