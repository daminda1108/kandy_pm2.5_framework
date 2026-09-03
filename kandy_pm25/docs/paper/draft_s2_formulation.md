# 2. Formulation: an information-tiered decomposition

*Rewrite of `draft_s4_formulation.md` per `rewrite_plan_2026-08-22.md` §2. Numbers are
claim tokens resolved at build time from `data/processed/modular/claims.json`; the build fails
if any of them disagrees with a fresh recomputation, or if any token reaches the output
unresolved.*

---

Section 1 argued that most cities needing a PM2.5 field cannot check one. This section
describes a model built to that condition rather than in spite of it. Its organising idea is
not the physics, which is deliberately modest, nor the machine learning, which is
off-the-shelf. It is that **the model declares which observations it is entitled to use, and
degrades exactly when they are withheld.** That property is what converts an ablation into a
measurement, and Sections 3 and 4 depend on it entirely.

## 2.1 The decomposition and its gauge

Let `T(t)` be the basin-mean concentration at hour `t`, `B(t)` the regional and transboundary
background — taken horizontally uniform across the 15 × 15 km domain — and `P(x, y, t)` a
dimensionless local pattern normalised to unit spatial mean. Writing the local increment as
`inc(t) = T(t) − B(t)`, concentration on the 1 km grid is

```
PM(x, y, t) = B(t) + max( max(inc, 0), ε ) · P(x, y, t)
                   + min(inc, 0) − max( 0, ε − max(inc, 0) )
```

The elementary form is the first line with `ε = 0`: a uniform background plus a local increment
redistributed by a unit-mean pattern. The additional terms are corrections, derived in §2.5.

Because `P` integrates to unity, **the spatial average of the field returns `T(t)` exactly**.
The pattern redistributes material within the basin without altering the total. This gauge
condition does three things at once. It prevents an imposed spatial pattern from displacing the
level, which is the quantity the observations *do* constrain. It renders level and pattern
separately identifiable, so each can be validated independently — which is what Section 4
exploits. And it makes the consequence of `P` being wrong bounded and legible: an error in `P`
is an error in *where* the material sits, never in *how much* of it there is.

One qualification, stated rather than buried. The satellite anchor is exact — the annual mean of
`T` equals the Van Donkelaar basin mean to four decimal places every year — but the delivered
field sits **0.39 to 0.56 per cent above** it, consistently and in the same direction. The cause
is a chain effect, not a defect in the gauge: each build step preserves the mean, but the
unit-mean pattern is recovered from an upstream field rather than from the anchor directly, and
a small positive offset accumulates. The gauge holds by construction and to within 0.6 per cent
in practice, and we state it that way rather than as an exact identity.

## 2.2 The observation model

A field is areal; a monitor is a point. Comparing them by co-location is a change-of-support
error, and it is the single most common way a model of this kind is scored wrongly. For each
instrument `k` we write

```
y_k(t) = H_k[C](t) + b_k + e_k ,     e_k ~ N(0, σ²_meas,k + σ²_rep,k)
```

with `H_k` the observation operator, `b_k` a systematic offset, and `σ_rep` a representativeness
error from sub-grid variability the model cannot resolve. The operators differ by instrument
class: a reference monitor and a low-cost sensor are near-delta in space, a satellite product is
already an areal average, a passive sampler integrates in *time*, and a mobile campaign
integrates along a path.

Two quantities are distinct and are routinely conflated. `b_k` is a **systematic** offset —
siting bias plus device calibration; a kerbside monitor inside a 1 km cell reads systematically
above the cell mean, and this is where a low-cost sensor's calibration lives. `σ_rep` is a
**random** error from unresolved sub-grid structure, and it is estimated from the local spatial
variability of the field itself, so it grows in structured hours and shrinks when the field is
well mixed.

This level is not decoration. The shipped 90 per cent interval covers 72.4 per cent of
observations at the two Kandy sensors — but observations fall *below* the lower bound in 25.7
per cent of hours and above the upper in only 1.9 per cent. That is a one-sided offset, not a
width failure: removing each sensor's own median offset restores coverage to 91.5 per cent. The
interval was correctly scaled and incorrectly centred, and only an explicit `b_k` makes that
diagnosis available rather than leaving it as an apparent calibration failure.

⚠ We state a limitation here rather than let it be inferred. The operators are implemented and
tested, and `b_k` and `σ_rep` are estimated at panel cities that have reference monitors. At
Kandy they are **not estimated**, because estimating them requires a reference monitor and Kandy
has none. The observation model therefore disciplines the *comparison* at the demonstration
city without correcting it — which is a `Bud1` limitation by construction, and is precisely the
kind of thing the budget below is designed to make visible.

## 2.3 The information budget

An information budget declares which observation streams a tier may use. Builders assert against
it, so a stream a tier is not entitled to is unreachable by construction rather than by
discipline.

| budget | adds | first thing it can constrain |
|---|---|---|
| `Bud0` sensorless | satellite AOD, reanalysis drivers, static geography | level; **no diurnal cycle** |
| `Bud1` two-sensor | 2 local low-cost sensors | diurnal and seasonal shape |
| `Bud2` reference | a continuous reference monitor | `b_k`; removes in-sample circularity |
| `Bud3` regional | a rural or regional network | **`B(t)`** |
| `Bud4` spatial | a passive network or campaign | **`P(x, y, t)`** |

The budgets are nested, `Bud0 ⊂ Bud1 ⊂ … ⊂ Bud4`, and the nesting is asserted at import time so
a malformed budget cannot be registered. Each tier declares in one machine-readable object what
it admits, what it estimates, what it imposes, and which tier it degrades to.

**Admissibility is checked in three directions, and each check exists because the corresponding
failure occurred.** `require()` stops a tier reaching for information it was not granted — the
obvious direction. `require_covers()` stops a tier *quietly failing to use what it has*, which
is not obvious at all: a rung that under-uses its budget inflates every gain measured above it,
and that is exactly what happened here. The scored sensorless tier used one of the three streams
its budget admits, and the error was invisible in every pooled number until it was looked for
directly. `require_covers_units()` then stops an individual *city* being scored in a rung whose
streams it lacks, and `require_stream_coverage()` asserts a merged stream's **values** rather
than the fact that a join ran — a stream can key correctly, type correctly, and arrive entirely
empty, and a gradient-boosted learner will fit it without a word.

We report that history rather than presenting the checks as foresight. Three of the four were
written after the failure they now prevent.

🔴 **`Bud4` is a declared design assumption, not a validated rung**, and we label it as such
wherever it appears. A spatial network does not make `P` estimable at the resolutions available:
inverse-distance interpolation between a city's own stations is worse than assuming the city is
uniform, and a transferred land-use regression barely beats a population raster. Every other rung
is validated in Section 4; this one is a statement of intent.

## 2.4 What the formulation guarantees, and what it does not

⚠ We claim **two guarantees, one enforced mechanism, and one property that has been discharged
by measurement** — not four guaranteed properties, which is how an earlier version of this work
described it and which the evidence does not support.

**P1, conservation.** The gauge condition holds at every budget and every parameter value,
analytically and under test, to the 0.6 per cent stated in §2.1. This is a guarantee.

**P3, exact nesting.** `Bud_i` reduces **bit-exactly** to `Bud_{i−1}` when the extra stream is
withheld, asserted by byte comparison for all four adjacent tier pairs. This is a guarantee, and
it is the load-bearing one. Without it, "remove the stations and refit" produces a *different
model*, and the difference measures information loss tangled with model change. With it, the
difference is information loss alone. **This is what makes Section 4 a measurement rather than a
comparison of two models**, and it is the property we would ask a reader to take from this
section.

**P2, monotone skill under added information, is enforced rather than guaranteed.** It is not
automatic — a naive assimilation at two sensors previously made this model worse — so each tier
is shrunk toward its parent with a weight set by measured information gain. It holds on every
rung that exists across the validation panel.

**P4, declared identifiability, is discharged.** Every element of the parameter vector carries a
profile-likelihood interval per budget, on a {{claim:p4.grid}}-point grid with interpolated
threshold crossings. Of {{claim:p4.rows}} parameter-budget combinations, {{claim:p4.identified}}
are identified and {{claim:p4.unidentified}} are **unidentified**, bound-saturated across their
whole admissible range. We lead with the second number. The one parameter the panel does
constrain is the emission-surface exponent, whose {{claim:p4.s_exp_intervals_containing_1}}
profile intervals all contain 1.0 at a median width of {{claim:p4.s_exp_median_box_fraction}} of
its box — so leaving it at unity is supported by an interval rather than by an assumption.

⚠ An earlier version of this analysis reported {{claim:p4.zero_width_identified}} additional
parameters as identified on a coarser grid, where a single grid point below the threshold
produced a zero-width interval. A zero-width profile interval means the grid cannot resolve the
interval, not that the parameter is sharply determined. The refinement removed those and moved
six combinations out of `identified`. The model is less identifiable than the coarse grid
suggested, and P4 is the one property that could not survive being wrong in this particular way.

## 2.5 The two correction terms

The elementary form fails in two specific, diagnosable ways, and each additional term repairs
exactly one.

**The increment split.** When the hourly total dips below the daily background — which happens
in 38.5 per cent of Kandy hours — `inc` is negative, and multiplying a core-high pattern by a
negative number renders the *core cleaner than the countryside*. The repair is to structure only
the accumulation above background and let ventilation below it apply uniformly: the `max(inc,0)·P`
and `min(inc,0)` terms. The basin mean is preserved exactly, and the inversion falls from 38.2
per cent of midday hours to zero.

**The ventilated-hour floor.** The split renders ventilated hours perfectly flat, and ground
truth at a monitored analogue shows they are not. A bounded, mean-zero floor `ε(t)` restores
structure without touching the gauge: mean-zero implies the T-lock is exact, and `ε = 0`
recovers the split bit-exactly, which is asserted rather than assumed. Its magnitude is fitted
at one city and transferred; we report that it does **not** transfer well, and that Kandy's value
sits inside a pooled bracket rather than being determined by it.

## 2.6 The partition, and why it is a constraint rather than a choice

The decomposition makes available an attribution a single-term model cannot: how much of the
annual mean is generated inside the basin. Across the anchored years the local fraction is
**{{claim:partition.f}}**, ranging {{claim:partition.f_lo}} to {{claim:partition.f_hi}}.

That follows from a physical constraint, not a parameter choice, and the argument is short.
Local sources emit continuously; rain changes removal, not emission. Therefore at an emitting
location the local increment is strictly positive at every hour, the background can never reach
the total, and **a background at or above the total is not a physical state but an over-estimated
background**. Since `B` is flat within a day, the constraint has a closed form: cap each day at
`(1 − F_min)` times that day's minimum hourly total.

Before the constraint, the background exceeded the total in 24.8 to 36.1 per cent of hours,
averaging 29.9 per cent. In each such hour the field rendered exactly flat and reported a zero
local share at the traffic core. After it, the residual is under {{claim:partition.residual_b_gt_t_pct}} per cent per year, and every
remaining case is an hour where the anchor itself returned a negative total, which no constraint
on the background can repair.

**The result does not depend on the free parameter.** Sweeping `F_min` from 0 to 0.08 — a
fourfold change — moves the local fraction from 0.477 to 0.502. The value used ({{claim:partition.f_min_parameter}}) was chosen as the
smallest that removes the defect, *before* the resulting fraction was known. Nor does it depend
much on the form of the constraint, which is the more searching test: replacing the calendar-day
minimum with a centred rolling 24-hour minimum moves the fraction from 0.481 to 0.487. Doubling
the window to 48 hours moves it to 0.540 — so the answer is stable across constraint forms that
respect the daily structure of `B`, and drifts only when the window exceeds the timescale on
which `B` is defined.

We note that this replaces an earlier estimate of about 0.25 taken from source-apportionment
literature. The constraint refutes that value rather than refining it.

## 2.7 What this model is not

Stated explicitly, because overclaiming here is the most attackable thing available to a referee.

- **Not a chemical transport model.** No gas-phase or aqueous chemistry, no secondary aerosol
  formation, no explicit deposition or scavenging, no vertical structure, no hygroscopic growth.
- **Not a source apportionment.** The emission surface is a spatial *proxy*; the level is carried
  by the anchor and reflects all sources.
- **Not able to resolve the hourly local/background split from a total-only series.** Measured,
  not assumed: the dilutive components of background and increment share their only driver.
- 🔴 **Not dependent on its transport layer, which has now been scored and does not help.**
  Across ten monitored cities, ranking neighbourhoods on the raw emission surface achieves
  {{claim:r2.rho_emission_surface}} against {{claim:r2.rho_with_atransport}} after the
  terrain-aware dispersion solver has run — it improves rank in {{claim:r2.cities_improved}} of
  ten cities. The solver is a topographically-steered redistribution filter, **not forward fluid
  dynamics**: it is steady-state per hour, so it cannot represent recirculating valley eddies or
  multi-hour stagnation. It is retained because it supplies hour-to-hour behaviour the headline
  field otherwise lacks, but **the headline field does not depend on it**, and we say so here
  rather than waiting to be told.

---

## Drafting notes, to remove before submission

- Claim tokens resolve from `claims.json`; run `scripts/build_claims.py --check` before any
  build. The partition figures are now tokenised.
- STILL HARDCODED, each needing a generating script in `build_claims.py`: the 0.39–0.56 per cent
  gauge drift, the 72.4/25.7/1.9/91.5 interval-coverage set, the 38.5/38.2 inversion pair, and
  the constraint-form sweep (0.477–0.502, 0.481/0.487/0.540). All four are computable from the
  shipped parquets plus the anchor; none is a literature value.
- §2.3 should cite the four admissibility checks by their ledger entries once the reference list
  is rebuilt.
- Decide with the supervisor whether §2.6's partition stays here or moves to the Kandy
  demonstration; it is formulation *and* result, and currently sits in both.
