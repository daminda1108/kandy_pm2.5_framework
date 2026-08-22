# Pre-registration — making the local/background partition an estimated, time-varying quantity

**Written 2026-08-07, BEFORE any number was computed.** Registers the method, the gates, the
falsifiers and the author's prior. Nothing here may be revised after results are seen; a
variation is a new pre-registration.

---

## The problem

The field is `PM = B(t) + [T(t) − B(t)]·P_local(x,y,t)`. The background is closed by
`B_annual = (1−f)·L(year)` with **f a per-year constant taken from literature**. One
observable, two unknowns per hour, closed by assertion.

Consequences already on record: the constant is refuted from below by a coherence floor
computed from the shipped anchor alone (f ≥ 0.41 against a shipped 0.244, ledger F.17);
`B > T` in 28.5% of hours; five reconstructions were built and each broke one of four
mutually unsatisfiable constraints (F.13/F.15/F.17/F.18); and the fuel-crisis justification
for the year-to-year variation was withdrawn after the shock test returned the opposite sign
(F.35). Every one of those five attempts varied the **functional form** of B while leaving
the **identification** untouched. This registers a change to the identification.

The physical premise, which the current constant denies: the split is **not constant**. It
varies with Indo-Gangetic outflow (B up, f down), with the south-west monsoon (B down, f up),
with day of week and holiday, and hour to hour with ventilation.

## The estimator

```
T(t) = B(t) + κ · A(t) · e(t) / V(t)
```

- `e(t)` — the diurnal emission clock, **measured** from the holiday instrument (F.29), not assumed
- `V(t)` — ventilation, BLH × wind speed, from reanalysis drivers only
- `A(t)` — activity state: working day / Saturday / Sunday / Poya / fixed holiday / lockdown
- `B(t)` — latent background, constrained smooth at synoptic scale and above
- `κ` — local emission-to-concentration scaling

Fitted as a state-space model with **four observation streams**, each identifying a different
part:

1. **the basin anchor `T(t)`** — the sum;
2. **the between-sensor difference** — differencing two sites cancels a spatially uniform `B`
   exactly, giving a background-free observation of the local term;
3. **holiday contrasts** as moment conditions — they shift `A(t)` exogenously and pin `κ`;
4. **MERRA-2 hourly speciation** (BC, OC, sulfate, dust, sea salt) as a prior on `B`'s level
   *by air-mass regime* — used for **shape and regime only, never for level**, because the
   published Indian validation shows sulfate biased −31% to −0.4%.

Smoothness of `B` is imposed by a Kolmogorov–Zurbenko-style band separation: `B` may carry
synoptic (2–10 day) and seasonal variance, and may not carry a diurnal harmonic locked to the
activity cycle. **`f(t) = L(t)/T(t)` is then an output**, varying hourly, not an input.

## STEP 1 (this registration's immediate scope) — a reference split at the panel cities

Before any estimator is fitted, we need something to score it against. The panel cities have
dense networks; Kandy does not. Step 1 builds a **reference partition** at each panel city
using information Kandy will never have, so that later steps can be scored on whether they
recover it from Kandy's two-sensor budget.

**Method.** Stations are assigned to *core* and *peripheral* groups by their percentile on the
**traffic emission surface** — a model input using no concentration data, the same
leakage-free rule used for the zone test (F.36). The reference background for each hour is
the **10th percentile across peripheral stations** reporting that hour (Lenschow lower
envelope, applied across space rather than time). The reference local increment is the
network mean minus that background, and `f_ref = L_ref / T_ref`.

**Step-1 gates, fixed here.**

- **P1 — the periphery is genuinely peripheral.** In each city, the peripheral group's median
  emission-surface percentile must be below the core group's by at least 0.25 (on a 0–1
  scale). Cities failing this have no usable periphery and are reported **not estimable**,
  not forced.
- **P2 — the reference is physically ordered.** `B_ref < T_ref` in at least 95% of hours, and
  `f_ref ∈ (0, 1)` in at least 95% of hours. A reference that violates its own physics cannot
  score anything.
- **P3 — the reference is not an artefact of network geometry.** `f_ref` must not correlate
  with the number of reporting stations at |r| > 0.5 across hours.
- **P4 — enough cities survive.** At least **5** of the ten cities must pass P1–P3, otherwise
  the transfer-validation design for the partition is not viable and **the whole plan stops
  here** and is reported as infeasible.

**Descriptive outputs (no gates, reported because they are the point):** `f_ref` by month, by
hour of day, and by air-mass regime, per city — the first direct measurement anywhere in this
project of how much the partition actually moves.

## Later steps (registered now so they cannot be redesigned around a result)

- **Step 2** — pull MERRA-2 `M2T1NXAER` hourly speciation for Kandy and the panel.
- **Step 3** — fit the estimator at panel cities under the **two-sensor budget**, choosing the
  two sensors by the same elevation-gradient rule the panel already uses.
- **Step 4 — transfer validation.** Gates: **T1** pooled correlation between estimated and
  reference `f(t)` at monthly resolution ≥ 0.5; **T2** pooled bias in annual mean `f` within
  ±0.10; **T3** the estimator beats the incumbent constant-`f` baseline on monthly RMSE at
  **≥ 7 of the surviving cities**; **T4** `κ` stable across cities — between-city τ no more
  than 3× the median within-city standard error (the test the ε-floor failed, F.30).
- **Step 5** — apply at Kandy with intervals, **only if T1–T3 pass**. If T4 fails, `κ` is
  reported as a non-transferable quantity and Kandy's value carries the pooled predictive
  interval rather than a point estimate.

## Falsifiers

- Step 1 stops the plan if fewer than 5 cities pass (P4).
- If **T1 fails**, the estimator does not track the partition's variation, and the correct
  conclusion is that the constant-`f` closure is not improvable with two sensors — which
  would be a **stronger** statement of the information limit than the current one, and is
  reported as such.
- If the estimator recovers `f_ref` only where networks are dense, that is a density
  dependence and must be reported as bounding applicability at Kandy.

## Author's prior, published in advance

I expect **P1–P4 to pass** (the panel was selected partly for network density) and the
descriptive result to show `f_ref` varying substantially — plausibly a factor of two between
monsoon and outflow regimes — which would confirm the physical premise and condemn the
constant.

I am **least confident in T4**: `κ` couples emissions to concentrations through local
dispersion, and the ε-floor result (F.30) showed a structurally similar constant failing to
transfer with between-city variance 14–18× the within-city uncertainty. I expect T4 to
**fail**, and in that case the honest outcome is a Kandy `f(t)` with a wide interval rather
than a sharp new number.

I do **not** expect this to overturn the coherence floor: any credible `f(t)` should average
to something at or above ~0.4, consistent with F.17/F.21/F.22.

**Artifacts:** `scripts/panel_reference_partition.py` →
`results/figures/multicity/panel_reference_partition.{csv,json}`.
