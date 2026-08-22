# Pre-registration — hourly background structure and a learnable decomposition

**Date:** 2026-08-18 · **Author:** Claude (session), for D. Alahakoon
**Status:** registered BEFORE any of the four workstreams was run.
**Ledger slots reserved:** F.44 (trajectory sub-daily), F.45 (entrainment signature),
F.46 (distributional anchor), F.47 (differentiable decomposition).

---

## 0. Why this exists, and what it is not

The shipped background `B(t)` is **daily-flat**. The physical objection is correct: the regional
background does vary within the day. Five reformulations (F.13, F.15 ×2, F.17, F.18) were built
and rejected, and F.41 declared the hourly split "probably unidentifiable"; CLAUDE.md carries a
standing rule against a sixth reformulation. F.43 superseded that rule once, on the grounds that
*imposing a constraint the construction violated* is a different act from *re-deriving a level*.

This registration does not propose a sixth reformulation of the background **level**. It
separates the problem into two components with different identifiability status, and acts only
where identification exists or can be tested:

| component of hourly `B` variation | driver | collinear with the local increment? | status |
|---|---|---|---|
| **advective** — the upwind air mass changes | trajectory / origin | **no** (850 hPa, above the BL) | identifiable; data already held, discarded at build time → **W1** |
| **dilutive** — the boundary layer deepens and collapses | BLH | **yes** — the same variable dilutes both terms | not identifiable from a total-only series; one possible escape → **W2** |

The algebraic statement of the second row is why model class cannot help:
`T(t) ≈ [A + E(t)] / BLH(t)`. Two terms, one driver, one observable. No architecture separates
them. Everything below respects that.

**Invariants that bind all four workstreams.** T-lock (basin mean ≡ `T(t)`, Δ<0.05); the F.43
coherence cap `B ≤ (1−F_MIN)·min_hour(T)`; the increment-split form; `EPS_FLOOR=0` recovering
v2 byte-identically; the 18-test pytest suite; webapp QA gate < 0.25 µg/m³. Any workstream that
moves a locked-tier number by more than the QA tolerance stops and reports rather than ships.

---

## W1 — Use the trajectory data at its native 6-hourly resolution

### The defect
`scripts/build_additive_field_v2.py::daily_class()` reads `d1_trajectories_850.parquet`
(11,676 rows, arrivals at 00/06/12/18 UTC, 2,919 days) and collapses it to one class per day
with `.mode()`. Measured before registering:

- the trajectory **sector** changes within the day on **24.8%** of days;
- the binary **marine flag that actually sets `B`'s level** flips within the day on **11.3%**;
- the marine rate is flat across arrival hours (0.292 / 0.293 / 0.292 / 0.287).

So on roughly one day in nine the background genuinely steps mid-day and the model holds it
flat by construction — while the discarded signal carries **no diurnal cycle**, only episodic
transitions. That bounds the claim: W1 makes `B` step when the air mass steps. It does not make
`B` breathe with the boundary layer, and it is not advertised as doing so.

### The change
Map the class to the T-anchor clock by 6-hourly arrival instead of by date. No new free
parameter; `B_MARINE`, the continental level solve, the annual-mean lock and the F.43 cap are
untouched in form.

### Registered gates (all must hold)
- **W1-G1** T-lock exact on every rebuilt year (Δ < 0.05 µg/m³).
- **W1-G2** the 18 invariant tests pass; webapp QA < 0.25.
- **W1-G3** annual `f` moves by **< 0.02** from the F.43 value (~0.48). W1 redistributes `B`
  within days under an unchanged annual mean; a large `f` move means it did something else.
- **W1-G4** coherence-cap activation does not increase. A sub-daily `B` that trips the cap
  *more often* is worse-conditioned than the daily one and is rejected.
- **W1-G5 (falsifier)** if locked-tier annual means move by more than the QA tolerance,
  W1 is confined to the extension/shipped tier and the locked tier is left alone.

### Prior, published in advance
Effect on any reported quantity: **small**. Expected: annual means unchanged (T-lock), `f`
within 0.01, changed hours concentrated on the 11.3% of flip days. Value is correctness and a
better-conditioned background, not a headline number.

---

## W2 — The entrainment-signature test (does the dilutive half have a way out?)

### Hypothesis
Local emissions accumulate **at the surface**, so deepening the boundary layer dilutes them:
the increment falls as BLH rises. A regional layer advected **aloft** is entrained downward as
the boundary layer deepens: the surface background *rises* as BLH rises. If Kandy's
transboundary load arrives lofted, the two components carry **opposite-signed** BLH responses —
a second identifying dimension, and the only route by which the dilutive half stops being
ill-posed without new instruments.

⚠ This is reasoning from transport physics, not from a measurement. It fails if the regional
plume arrives already well-mixed through the boundary layer, which is plausible.

### Design
Observed FECT PM2.5 (`dataset_v3_hourly.parquet`, `pm25_observed`, n=19,686, 2 sensors,
2018-07 → 2026-05) against ERA5 `blh_m`. **Within (sensor × month × hour-of-day) cells**, so
day-to-day BLH variation is compared at a fixed clock time and the emission clock `e(t)` is
held constant by construction. Cell-demeaned `log PM` regressed on cell-demeaned `log BLH`;
the slope is the elasticity. Stratified by the 6-hourly trajectory class (marine vs
continental) at the matching arrival.

Controls: rain-hours excluded (`tp` > 0, scavenging confound); cells with < 8 observations
dropped; morning boundary-layer growth window (07–13 LT) reported as primary with the full day
as a secondary. Uncertainty by bootstrap over **days**, not hours (hours within a day are not
independent).

### Registered gates
- **W2-G1 (directional — the gate is the SIGN, not the magnitude)**
  `slope_continental − slope_marine > 0`, with a 90% bootstrap CI **excluding zero**.
  Following F.35's recorded gate error, a directional hypothesis is tested by direction; a
  magnitude comparison does not satisfy this gate.
- **W2-G2 (placebo)** the same contrast computed on a **shuffled** trajectory label must not
  pass W2-G1. If it does, the design is picking up seasonality, not origin.
- **W2-G3 (seasonal honesty)** report the contrast within DJF and JJA separately. A result
  present only in the season where marine and continental days barely co-occur is confounded
  with season and is reported as such, not as a mechanism.

### Prior, published in advance
**~55–60% that the sign is as predicted, and the effect is small.** Recorded explicitly so a
confirming result cannot be reported as a strong prediction and a null cannot be quietly
reframed. Kandy's own record makes the null plausible: the inter-monsoon transboundary peak
coincides with deep, well-mixed conditions.

### What each outcome licenses
- **PASS** — a second identifying dimension exists. W4's latent model gains a real constraint
  and the "probably unidentifiable" clause in F.41 is narrowed rather than repeated.
- **FAIL** — the dilutive half is closed **by measurement rather than by argument**, which is
  a stronger statement than the current one and is publishable in the same register as the
  five spatial nulls. F.41 stands, with a mechanism attached.

---

## W3 — One distributional learner in place of the patch stack (option A)

### The defect
`T(t)` is produced by a GBM, then `sharpen_T_diurnal.py` restores the damped diurnal and
seasonal amplitude, then `extension_tail_correction.py` restores the damped tail. Three layers,
two of them corrections for one cause: a conditional-mean-ish learner regresses to the mean and
cannot extrapolate past its training targets (gotcha #76). The patches fix *climatological
moments*, which is why the tail correction explicitly fixes episode **frequency** and not
episode **timing**.

### The change
A learner that predicts the **conditional distribution** natively — distributional GBM or a
quantile-regression / implicit-quantile head — replacing GBM + sharpen + tail-correct, with the
existing CV+ Mondrian conformal wrap retained on top.

### Registered gates (scored on the LOCKED years, leave-one-year-out)
- **W3-G1** pooled hourly R² ≥ 0.583 (the v3.0 production value). No re-thresholding.
- **W3-G2** cov90 ∈ [0.85, 0.95].
- **W3-G3 (the point of the exercise)** with **no** sharpening and **no** tail correction
  applied: diurnal swing ratio ≥ 0.95 of observed, and hours > 55 µg/m³ within ±25% of the
  observed count, held-out. This is the tail diagnostic gotcha #76 requires of any new tier.
- **W3-G4** hourly r not worse than the current stack (0.836–0.890 band).
- **W3-G5 (falsifier)** if W3-G3 fails, the patch stack is *not* reinstated on top to rescue
  it — the result is reported as a negative and the current stack stays. Patching a new
  learner with the old corrections would reproduce the defect and hide it.

### Prior, published in advance
**Likely to pass W3-G1/G2 and genuinely uncertain on W3-G3.** Label noise from the FECT
calibration (slopes 1.34–1.40, W5 open) is a ceiling on achievable R² that no model class
lifts. The expected win is *architectural* — three layers to one, and a tail that is modelled
rather than reinstated — not a large metric jump. If the honest outcome is "same numbers,
fewer patches", that is the result and it is reported as such.

---

## W4 — Differentiable decomposition (option B)

### The change
Re-express the field equation in an autodiff framework so its internal constants become
**estimated parameters with intervals** rather than hand-set values: `κ` (confinement), the
transport amplitude cap (currently a hard-coded `0.5` that saturates ~4% of hours,
concentrated at 06:00 and 19:00), `ε₀` (transferred from Medellín), the `e(t)` evening-lobe
weight, and the `S_emit` exponent. Trained end-to-end against the labels that already exist:
the N=10 analogue cities' held-out networks, through the existing scorecard harness.

This is the differentiable-modelling paradigm (Shen et al., *Nat Rev Earth Environ* 2023;
UDE hydrology, GMD 2026). It calibrates the structure already argued for; it does not learn new
structure.

### Registered gates
- **W4-G1 (invariant)** T-lock exact by construction — unit-mean normalisation is
  differentiable and must remain in the graph. A formulation that breaks T-lock is rejected
  regardless of fit.
- **W4-G2 (generalisation, not fit)** fitted parameters must improve **held-out** spatial ρ or
  diurnal r on cities **excluded from the fit** (leave-one-city-out). An in-sample improvement
  is not a result — see gotcha #68.
- **W4-G3 (identifiability, reported either way)** profile likelihood / Hessian per parameter.
  Parameters that hit bounds or show flat profiles are **reported as unidentified**, exactly as
  κ (2026-06-01) and the six SharedTerrainAnsatz parameters were. Bound-saturation is a
  publishable finding, not a failure to hide.
- **W4-G4 (descriptor admissibility, gotcha #73)** no quantity derived from a target city's own
  outcome may enter the fit, even under leave-one-out.
- **W4-G5 (adoption)** fitted values replace hand-set constants **only** where W4-G2 and W4-G3
  both pass. Otherwise the hand-set prior stands and the interval is reported alongside it.

### Prior, published in advance
**Expect partial identifiability.** κ was already found empirically unidentifiable at N=1 and
all six SharedTerrainAnsatz parameters bound-saturated. Pooling 10 cities is more constraint
than either had, but the honest expectation is that **some** parameters identify (the transport
cap and the `S_emit` exponent are the best candidates, since they act where held-out stations
exist) and **some** do not. A result of "two of five identify, three do not" is a successful
outcome of this workstream.

---

## 5. Order of execution, and the stopping rule

1. **W2** first — cheapest, decisive, and its outcome changes what W4's latent extension is
   allowed to claim.
2. **W1** — contained, uses data already collected, no new free parameter.
3. **W3** — self-contained on the temporal anchor.
4. **W4** — largest, and best informed by the other three.

**Stopping rule.** Any workstream that fails its registered gates is written up as a negative
result in the ledger and **not** iterated into a pass. Re-running a failed design with a
loosened gate is the failure mode this document exists to prevent.

---

## 6. Outcomes (appended after running; the registered content above is unaltered)

| workstream | status | outcome | ledger |
|---|---|---|---|
| **W2** entrainment signature | run 2026-08-18 | **NULL.** W2-G1 passed (+0.473) but the composition-matched placebo recovers +0.430 of it; JJA, the only block where both air masses genuinely co-occur, gives +0.10 [−0.54, +0.92]. The dilutive half is closed **by measurement**. Not iterated. | **F.45** |
| **W1** sub-daily origin | dry run 2026-08-18 | W1-G3 **PASS** (max Δf 0.0016). **W1-G4 FAILS as registered** — cap activation rises 0.5–0.9 pp in every year. Escalated, not reinterpreted. Structural finding: the F.43 cap fires on **49–75%** of hours, so `B` is cap-dominated and the origin construction is largely inoperative. | **F.44** |
| **W3** distributional anchor | not started | — | F.46 reserved |
| **W4** differentiable decomposition | not started | — | F.47 reserved |

**One design fault of my own, recorded.** The first W2 run filtered rain as `tp <= 0`. ERA5
`tp` is in metres, so that kept only the 12.6% of hours that are exactly zero — and because
marine air at Kandy *is* monsoon air, it deleted the marine stratum preferentially, which would
have manufactured the very contrast the test was looking for. Corrected to a 0.1 mm/h threshold
before any result was read. Same family as gotcha #74: a filter that correlates with the
stratification is not a neutral filter.
