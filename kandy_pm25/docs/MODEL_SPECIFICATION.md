# Model specification — an information-tiered grey-box decomposition for urban PM2.5

**Version:** 0.1 (specification; supersedes nothing until implemented)
**Date:** 2026-08-18
**Status:** this is the **target** formulation. `PROJECT_ARCHITECTURE.md` documents what is
built today. Where the two disagree, the architecture file is the truth about the code and this
file is the truth about the intent.

Rationale and evidence: [`model_formulation_2026-08-18.md`](model_formulation_2026-08-18.md).
ML placement: [`model_formulation_ml_map_2026-08-18.md`](model_formulation_ml_map_2026-08-18.md).

---

## 1. What the model is, in one paragraph

A hourly, 1 km field of surface PM2.5 over a target city, produced as a **mass-conserving
additive decomposition** into a regional background and a locally structured increment. The
physics is imposed and explicit; machine learning enters only where an identifiable label
exists; and the whole estimator is defined at a **declared information budget**, so the same
model — unchanged in form — serves a city with no monitor and a city with a dense network,
degrading exactly between the two.

It is **not** a chemical transport model. See §8.

---

## 2. Notation

| symbol | meaning | support |
|---|---|---|
| `C(s,t)` | true surface PM2.5 | point, hourly |
| `B(s,t)` | regional / advected background | coarse spatial, hourly |
| `A(t)` | local increment amplitude, `>= 0` | basin, hourly |
| `P(s,t)` | local pattern, unit spatial mean | 1 km, hourly |
| `T(t)` | basin-mean anchor | basin, hourly |
| `L(y)` | annual level anchor | basin, annual |
| `theta` | physics constants, calibrated | — |
| `H_k` | observation operator for instrument `k` | — |
| `b_k` | instrument bias | — |
| `sigma_rep` | representativeness error | — |
| `Bud_i` | information budget `i` | — |

---

## 3. Level 1 — latent process

    C(s,t) = B(s,t) + A(t) * P(s,t)

**Hard constraints.** Never fitted, never violated, asserted at every budget:

| id | constraint | test |
|---|---|---|
| C1 | `mean_s C(.,t) = T(t)` (conservation / T-lock) | `T1` basin-mean drift < 0.05 |
| C2 | `B(t) <= (1 - f_min) * min_h T` (coherence) | `T2` cap-violation count = 0 |
| C3 | `A(t) >= 0` and `C(s,t) >= 0` at render | `T3` |
| C4 | `mean_s P(.,t) = 1` (unit mean) | `T4` |

C1 is what makes level and pattern separately reasonable-about, and separately validatable. It
must remain **structural** — imposed inside the computational graph by normalisation, not
restored afterwards by a correction.

**Component forms (current, calibratable):**

    P(s,t) = norm( S(s)^s_exp * M(s,t; kappa) * A_trans(s,t; a_cap) * e(t; w_evening) )
    A(t)   = max(T(t) - B(t), 0)                      [increment split]
    theta  = (kappa, a_cap, eps0, w_evening, s_exp)

The shipped field adds a bounded mean-zero pattern floor `eps0` on ventilated hours; it is
mean-zero precisely so C1 survives, and `eps0 = 0` recovers the un-floored form bit-exactly.

---

## 4. Level 2 — observation model

For each instrument `k`:

    y_k(t) = H_k[C](t) + b_k + e_k ,     e_k ~ N(0, sigma_meas,k^2 + sigma_rep,k^2)

| instrument class | `H_k` | notes |
|---|---|---|
| reference continuous monitor | near-delta in space, hourly | `b_k` small, known |
| low-cost sensor (LCS) | near-delta + device response | `b_k` is the calibration slope/offset |
| satellite product | area average over cell | already an areal quantity |
| passive sampler | point, **time-integrated** | the operator must integrate in time |
| mobile campaign | path-integrated, intermittent | |

**This level is mandatory before any local observation is ingested.** Without it, a point
monitor is compared to an areal field by naive co-location, which is exactly how the shipped
90% interval came to read 72.4% coverage — a one-sided area-vs-point offset, not a width error.

---

## 5. Level 3 — information budgets

| budget | adds | first thing it can constrain |
|---|---|---|
| `Bud0` sensorless | satellite level, reanalysis drivers, static geography | level; **no diurnal cycle** |
| `Bud1` two-sensor | 2 elevation-gradient sensors | diurnal + seasonal shape |
| `Bud2` reference | a continuous reference monitor | `b_k`; removes in-sample circularity in `A(t)` |
| `Bud3` regional | rural / regional network | **`B(t)`** |
| `Bud4` spatial | passive network or campaign | **`P(s,t)`** |
| `Budf` forecast | forward drivers only | level only; `P` from climatology |

Nested: `Bud0` ⊂ `Bud1` ⊂ `Bud2` ⊂ `Bud3` ⊂ `Bud4`.

### 5.1 The tier contract

Every tier declares, in one machine-readable object:

```
tier:
  id:            Bud2
  parent:        Bud1
  admits:        [satellite_level, drivers, static_geo, sensor_pair, reference_monitor]
  estimates:     [L, A, b_k]
  imposes:       [B, P]
  degrades_to:   Bud1        # exactly, when reference_monitor is withheld
  shrink_toward: Bud1
```

Builders **assert** against `admits`. Any stream not listed is unreachable by construction. This
is what converts "we were careful about leakage" into "the code could not have leaked", and it
is the direct structural answer to the two leakage defects found by audit (in-sample
calibration; descriptor derived from the target's own outcome).

---

## 6. Guaranteed properties

| id | property | statement | how tested |
|---|---|---|---|
| **P1** | conservation | C1 holds at every budget and every parameter value | analytic + `T1` across the parameter box |
| **P2** | monotonicity | skill does not decrease as budget increases | ablation across the validation panel; shrinkage enforces it |
| **P3** | exact nesting | `Bud_i` reduces **bit-exactly** to `Bud_{i-1}` when the extra stream is withheld | byte-comparison test per tier pair |
| **P4** | declared identifiability | every element of `theta` carries a profile-likelihood interval **per budget**; bound-saturation is reported, not hidden | profile likelihood |

P2 and P3 are the methods contribution. P2 is not automatic — a naive assimilation at N=2
previously made this model worse — so it is enforced by shrinking each tier toward its parent
with weight set by measured information gain.

---

## 7. Epistemic status matrix

The model reports, for every component at every budget, one of:
**imposed** · **transferred** · **calibrated** · **identified** · **measured**,
together with its validation route (in-sample · borrowed ground truth · local held-out ·
pre-registered prediction).

This matrix is the primary object of the paper. A claim without a cell in it is not a claim.

---

## 8. What this model is NOT

Stated explicitly, because overclaiming here is the most attackable thing available to a
referee:

- **Not a chemical transport model.** No gas-phase or aqueous chemistry, no secondary aerosol
  formation, no explicit deposition or scavenging, no vertical structure, no hygroscopic growth.
- **Not a source apportionment.** The emission surface is a spatial *proxy*; the level is
  carried by the anchor and reflects all sources.
- **Not validated for coastal regimes.** The validation panel is terrain-confined basins.
- **Not a forecast system** until the forecast tier carries a per-lead skill curve and a scored
  background component. Until then it ships as a labelled demonstration tier.
- **Not able to resolve the hourly local/background split from a total-only series.** Measured,
  not assumed: the dilutive components of background and increment share their only driver.

---

## 9. Implementation status against this specification

| element | status |
|---|---|
| C1–C4 constraints | implemented; C1 structural under autodiff |
| differentiable forward model | implemented, reproduces both shipped tiers bit-exactly |
| `theta` calibration | **partially fitted (F.77)** — `s_exp` fitted on the panel: it does NOT transfer (0.25–0.45, ratio 1.8×) and stays at 1.0. The rest remain priors. |
| tier execution harness | **implemented** (`src/modular/tiers.py`) — admissibility asserted at build AND at call |
| shrinkage (P2 mechanism) | **implemented** (`src/modular/shrinkage.py`), CV-selected weight, day-grouped folds |
| observation model (`H_k`, `b_k`, `sigma_rep`) | **implemented** (`src/modular/observation.py`); see finding below |
| tier contract / registry | **implemented** (`src/modular/budgets.py`), 16 tests |
| P1 | holds |
| P2 | **demonstrated** on 3 real networks (F.48), then on **48 cities** (F.51/F.85). ⚠ 1 of the 48 is scored in `Bud0c` while missing the STATIC_GEO stream entirely (C7) |
| P3 | **generalised** — bit-exact degradation asserted for all 4 adjacent tier pairs |
| P4 | **run 2026-08-22 (F.75), refined 2026-09-01 (C5).** Profiles now use a 25-point grid with interpolated chi2 crossings; **zero-width intervals mislabelled `identified` went 11 → 0**, and six rows lost `identified` status, so the model is less identifiable than the coarse-grid table suggested (13 identified, 17 weak, 13 UNIDENTIFIED, 2 grid-limited). 🟢 **`s_exp` survives and is now properly evidenced: all 9 profile intervals contain 1.0** (median width 16% of box, the narrowest parameter), so F.77's decision to keep it at 1.0 rests on an interval rather than an artefact. Lead with the UNIDENTIFIED rows — Kathmandu's `kappa`, `eps0`, `w_evening` at `Bud1`, all bound-saturated. |


---

## 10. Implementation findings

### 10.1 The observation operator does NOT explain the coverage result (2026-08-18)

Tested on the real 2022 field over 220 sampled hours, the resolved point-vs-area offset is:

| site | median | mean | IQR |
|---|---:|---:|---:|
| FECT-Hantana | **+0.02** | -1.03 | [-0.96, +0.10] |
| NIFS-KOALA | **+0.85** | +2.49 | [+0.30, +2.29] |

against a recorded one-sided offset of about **+5.85 µg/m³**. So a faithful change-of-support
operator recovers at most a fifth of it, and essentially none at Hantana.

**Conclusion: the offset is predominantly SUB-GRID, not resolved-scale.** The 1 km pattern is
too smooth (annual core/edge contrast ~1.2x) to produce an offset of that size. It therefore
belongs in `b_k`, and `b_k` cannot be a free constant if it is to transfer — Hantana sits about
196 m above its own grid cell's mean elevation, and confinement is elevation-dependent, so the
defensible form is a **sub-grid siting term with an elevation covariate**:

    b_k = beta_0 + beta_z * (z_sensor - z_cell_mean)

`beta_z` is identifiable at `Bud2` (a reference monitor at known elevation), and it is exactly
the quantity the CEA station will pin down. Until then it stays a declared prior.

This is a **negative result for the strongest claim made for the observation model** — it was
expected to absorb the coverage discrepancy and it does not. It still earns its place: it makes
the residual attributable (resolved vs sub-grid) instead of unexplained, and it says precisely
which parameter the incoming data will identify.


### 10.2 Test inventory (2026-08-18)

`python -m pytest scripts/tests -q` -> **52 passed**: 18 pre-existing evidence-pipeline tests,
16 budget/observation/constraint tests, 7 shrinkage (P2/P3) tests, 11 tier-contract tests.
The P3 test is parameterised over every adjacent tier pair and asserts **bit-exact** equality
(`np.array_equal`), not approximate agreement.


### 10.3 The spatial and sub-daily axes have MEASURED ceilings (2026-08-19)

Recorded here because the specification's `Bud4` rung rests on an assumption that has now been
tested and failed.

**Spatial.** Four independent attempts, each on a larger or better-instrumented frame:

| attempt | frame | median rho |
|---|---|---:|
| traffic-centrality surface | 9 valley cities | +0.32 |
| sector-weighted surface (`emix`) | 9 cities | +0.30 (no better, F.56) |
| four global proxies, 2 radii | 47 cities | +0.21 (F.58) |
| fitted regime weights | 45 cities | +0.20 (F.59) |
| **full LUR set incl. roads, 4-5 radii** | **47 cities** | **+0.275 (F.61)** |

**Ceiling: rho ~ 0.2-0.28.** It survived the addition of road length in 50-1000 m buffers,
NDVI, tree cover, water, land-cover fractions and built volume. Within-city PM2.5 contrast is
genuinely small (between-station CV 0.125), and our stations are a convenience sample rather
than a LUR design.

**Sub-daily.** Whole-shape transfer is 5.5% worse than flat pooled; a physically motivated
decomposition using each city's own boundary-layer climatology is 5.6% worse (F.62). The fitted
dilution exponent is **0.054** — a ~40x diurnal swing in boundary-layer height produces almost
no diurnal swing in city-mean PM2.5, because in `PM = B + local` only the local increment
dilutes and `B` is already well mixed.

**🔴 `Bud4` is UNSUPPORTED as specified.** Section 5 asserts that a spatial network makes `P`
estimable. Tested two ways and it does not: inverse-distance interpolation between a city's own
stations is **worse than assuming the city is uniform** (F.60), and a transferred LUR barely
beats a population raster (F.61). `Bud4` remains in the registry as a declared design
assumption and must be labelled as such until a test passes. Every other rung is validated.

**Consequence for data acquisition.** The CEA passive NO2 network should NOT be requested as a
fix for `P_local`. Its value is in the `f` partition and as a local activity tracer (F.45). The
regional/background rung remains the largest measured gain in the whole programme, and 75% of it
survives an independent network (F.54) — so **NBRO is the acquisition that pays**.
