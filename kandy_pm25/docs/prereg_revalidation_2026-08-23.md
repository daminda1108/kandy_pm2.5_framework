# Pre-registration — re-validation of the budget ladder with a spec-compliant `Bud0`

**Written 2026-08-23, BEFORE any re-run.** No number under this design has been computed.

🟢 **REGISTERED: https://osf.io/g6hqb/ — 2026-08-23T04:21:32Z**, before the satellite pull, before the rebuild, and before any result existed. Materials at https://osf.io/akt7n/.

⚠ **Register on OSF before step 3 of `revalidation_plan_2026-08-23.md`.** The prior registration
(https://osf.io/nxqgb/) stands and is **not withdrawn**: that test was run exactly as registered,
its result is real, and the reason it is superseded (F.84) is itself the finding. This document
supersedes it in design, not in standing.

---

## 1. Why this re-validation exists

Ledger **F.84**. The scored `Bud0` used **one of the three streams its budget admits**:

| layer | `Bud0` |
|---|---|
| specification (`budgets.py`) | satellite level + reanalysis drivers + static geography |
| prior registration | "drivers **+ static covariates**" |
| **implementation** | **seven meteorological features, nothing else** |

Every gain on the ladder is measured against the rung below it, so an under-powered bottom rung
inflates **all** of them. The reported `Bud0→Bud1` (~24%) and `Bud2→Bud3` (~38–40%) are therefore
not interpretable, and the Colombo test (F.78) was scored against that weakened baseline.

A code-level fix is already in place: `Budget.require_covers()` asserts that a tier **uses** every
stream it admits, with omissions declarable only at the call site
(`scripts/tests/test_budget_covers.py`, 6 tests; the real `Bud0` feature set is asserted to fail).

## 2. Design — the bottom rung is DECOMPOSED, not replaced

Rebuilding `Bud0` with all three streams would answer the objection and discard information.
Instead each globally available stream becomes its own rung, so satellite and geography are
measured on the same footing as ground stations:

| rung | information | estimator |
|---|---|---|
| `Bud0a` | reanalysis drivers only | LOCO gradient boosting |
| `Bud0b` | + static geography (city-level) | LOCO gradient boosting |
| `Bud0c` | + satellite PM2.5 annual level — **the spec-compliant `Bud0`** | LOCO GBM, level re-anchored |
| `Bud1` | + 2 local stations | affine correction, CV-shrunk |
| `Bud2` | + 6 more local stations | affine correction, CV-shrunk |
| `Bud3` | + outer-ring stations as background | linear in (prior, background) |

**Locked choices** (fixed here so they cannot be tuned after seeing results):

- **Satellite product: GHAP** (1 km, on GEE; ⚠ band `b1` is already µg m⁻³ — no 0.1 scale,
  gotcha #50). Production uses van Donkelaar; the two agree at Kandy within 6% (U7) and the
  difference is declared, not hidden.
- **Static geography: city-level means of the existing LUR predictor set** (`lur_predictors.csv`,
  636 stations, 47 cities) — road length by class at five radii, NDVI, tree cover, water, land
  cover, built volume, population, night lights. **Aggregated over each city's own stations**,
  which matches the support at which scoring happens. ⚠ This is a convenience sample of the
  city's geography, not the city's geography; a city-polygon sensitivity check is run **only if**
  `Bud0a→Bud0b` proves load-bearing.
- **LOCO throughout**, target city excluded from training, asserted in code.

## 3. 🔴 A leakage path declared in advance, not engineered away

**Every global satellite PM2.5 product is calibrated against a global ground network**, plausibly
including monitors in this panel. So `Bud0c` is **locally sensorless but not
information-theoretically sensorless**.

This cannot be removed — it is a property of the product class. It is handled by **reporting
`Bud0a` alongside `Bud0c`**: the pair brackets the answer, `Bud0a` being the strictly sensorless
bound. Any statement about sensorless performance must quote both. Same family as gotcha #73.

## 4. Registered gates

| gate | criterion |
|---|---|
| **R-G1** P3 | `Bud0a` recoverable **bit-exactly** from `Bud0c` by withholding streams; likewise up the ladder |
| **R-G2** P2 | held-out RMSE does not increase along the ladder, on **every rung that exists** (⚠ a missing rung is *undefined*, not a failure — F.79) |
| **R-G3** coverage | `require_covers()` passes for every rung, or the omission is declared |
| **R-G4** stratification | nothing pooled without also being reported by band **and** by coastal/inland **and** by instrument class |
| **R-G5** satellite coverage | ≥ 45 of 47 cities, or the shortfall is named and never silently replaced |
| **R-G6** Colombo | as prior registration: RMSE in [13.43, 45.54]; seasonal r ≥ 0.60; \|bias\| ≤ 40%; **R² > 0 against day-of-year climatology** (decisive) |

## 5. 🔴 The coastal test — the confound Colombo alone cannot break

Colombo is our only out-of-panel city **and** it is coastal, so "coastal" and "external" are
perfectly confounded there. **The panel breaks the confound at no data cost: 22 of 46 cities lie
within 50 km of the coast, 24 do not** (Natural Earth 110 m coastline; threshold fixed here).

Registered analysis: report every rung stratified by coastal/inland.

## 6. Registered priors — numbers, so they can be wrong

**On the ladder:**

| step | prior |
|---|---|
| `Bud0a→Bud0b` (geography) | **5–15%**. Geography carries a level signal (population, lights) but the target is a city-mean scalar. |
| `Bud0b→Bud0c` (satellite) | 🔴 **25–45% — the largest single step below the ground rungs.** A satellite product measures the annual level directly. |
| `Bud0c→Bud1` (2 stations) | **5–15%, materially below the currently-reported ~24%**, because the satellite anchor supplies much of what those stations were supplying. |
| `Bud1→Bud2` | **~0%**, unchanged. |
| `Bud2→Bud3` (background) | **15–30%, below the current 38–40%**, because a satellite level already carries regional information. |

**Overall: I expect the ladder to flatten.** If it does not, local stations carry information no
global product does, which is a finding in its own right and must be reported as such.

**On the coastal hypothesis — this directly tests the F.78 diagnosis:**

> If the Colombo failure was caused by `Bud0` having *no information about the place beyond its
> weather*, then (a) `Bud0a` should be **worse at coastal cities than inland ones**, and (b) the
> `Bud0a→Bud0c` gain should be **larger at coastal cities**, because a satellite product directly
> observes the anomalous cleanliness that meteorology cannot infer.
>
> If instead coastal and inland cities behave alike at every rung, the Colombo failure was **not**
> about coastal regime, and my F.78 diagnosis is wrong.

**On Colombo re-run:** level bias falls from **+31.3%** to **under 15%**, and **R² against
climatology becomes positive** (C-G4 passes). If C-G4 still fails with a spec-compliant `Bud0`,
the sensorless tier genuinely does not transfer out of regime and F.78's conclusion survives its
own correction.

## 7. Stopping rule

**One rebuild, one report.** No re-specification of streams, estimator, aggregation or metric
after seeing any result. `Bud0c`'s feature set is fixed by §2 and may not be tuned. If the
satellite pull fails coverage (R-G5), the shortfall is named and the analysis proceeds on the
cities that have it — it is not backfilled with a substitute product.

## 8. What this cannot establish

- Nothing about the **spatial** field. The ladder scores a city-daily mean; the change-of-support
  limit (F.69/F.76/F.77) is untouched by this re-validation and is not re-litigated here.
- Nothing about `Bud4`, which remains a declared design assumption (F.60/F.61).
- Colombo remains **one** external city. The coastal stratification (§5) is what carries the
  regime claim; Colombo is corroboration, not the evidence.
