# Pre-registration — does aerosol composition explain the value of information?

**Registered:** 2026-09-05, before the confirmatory analysis was run.
**Project:** Kandy PM2.5, information-tiered grey-box decomposition.
**Analysis script (to be written after this document is lodged):**
`scripts/chemistry_mechanism.py` → `data/processed/modular/chemistry_mechanism.csv`.

---

## 0. Full disclosure of what has already been seen

This registration is **weaker than a true pre-registration and says so on its face.** A
disclosure section comes first because the alternative is to let a reader discover it.

**What was pre-specified, and when.** The directional prediction below was written into the
docstring of `scripts/pull_panel_speciation.py` and committed on **2026-09-01** as commit
`b9fd181`, four days before this document. It is git-tracked and its timestamp is verifiable.
The text reads:

> a **secondary-dominated** city [...] is chemically a REGIONAL problem, so a regional
> background station should be worth more there and a local monitor less. A
> **primary-dominated** city, whose PM is fresh local combustion, should be the reverse.

That is why the confirmatory tests below are **one-sided**. The direction was fixed before any
composition variable was ever correlated against any ladder outcome.

**What has already been run, and its result.** On 2026-09-05, before writing this document, an
exploratory probe correlated two composition variables against three ladder outcomes on the
MAIAC ladder, pooled, with no control for band and no multiplicity correction. Its full output:

| variable | outcome | Spearman rho | p (two-sided) |
|---|---|---:|---:|
| `sec_frac` | first-two-sensor gain | −0.031 | 0.840 |
| `sec_frac` | background gain | +0.261 | 0.080 |
| `sec_frac` | local-over-background advantage | −0.203 | 0.177 |
| `oc_bc` | first-two-sensor gain | +0.332 | 0.024 |
| `oc_bc` | background gain | −0.227 | 0.129 |
| `oc_bc` | local-over-background advantage | +0.388 | 0.008 |

**Nothing in this registration may be treated as blind to those six numbers.** Their
consequences are carried explicitly:

1. The `sec_frac` family is **confirmatory** (direction pre-specified 2026-09-01) but its
   effect sizes are now known to be small, so the registration states in advance that the
   expected outcome is a bounded null.
2. The `oc_bc` family is **exploratory promoted to confirmatory after seeing the data**. Its
   direction was *not* pre-specified. It is therefore tested **two-sided**, reported
   **separately**, excluded from the confirmatory multiplicity family, and **may not be
   described as pre-registered** under any outcome.
3. The band-controlled (partial) analyses, the GHAP-versus-MAIAC contrast, the bootstrap and
   the multiplicity correction have **not** been run in any form.

---

## 1. The question

The budget ladder reports what each observation stream is worth, and treats a city as a city.
Chapter 7 of the thesis reports that the ordering differs between latitude bands and states
explicitly that **latitude is a stratifying label and not a mechanism**. It names a candidate
mechanism and leaves it untested.

This registration tests a chemical mechanism instead. If a city's PM2.5 is dominated by
secondary material formed over hours to days, it is chemically a regional problem and a regional
background observation should be worth more there while a local monitor is worth less. If it is
dominated by fresh primary combustion, the reverse should hold.

**If it holds**, composition explains what latitude only labels, and the acquisition
recommendation becomes targetable by a quantity that can be obtained for any city without a
monitor. **If it fails**, the ladder's generality is strengthened rather than damaged: the value
of an observation would be shown insensitive to what the aerosol is made of.

---

## 2. Data, fixed before analysis

- **Composition:** `data/processed/modular/panel_speciation.csv`, 57 cities, GEOS-CF annual
  means. Variables used: `sec_frac` (secondary share of PM2.5) and `oc_bc` (organic to black
  carbon ratio). ⚠ GEOS-CF is a **model at ~25 km**, not a measurement, and per-city values are
  never to be presented as measured.
- **Ladder outcomes:** `ladder_maiac.csv` (primary, the honest satellite stream) and
  `ladder_revalidated.csv` (secondary, the fused stream), both at `bottom == Bud0c`.
- **Overlap:** all ladder cities carry composition. Scored n is expected to be **46** after
  dropping cities with no background rung.
- **Outcomes, defined now:**
  - `g_first2` = per-city per cent RMSE reduction, `Bud0` → `Bud1`
  - `g_bg` = per-city per cent RMSE reduction, `Bud2` → `Bud3`
  - `adv` = `g_first2 − g_bg`, the local-over-background advantage

---

## 3. Hypotheses

### Confirmatory family (one-sided; direction pre-specified 2026-09-01). Holm-corrected across the three.

| | hypothesis | direction | refuted if |
|---|---|---|---|
| **M1** | `g_bg` rises with `sec_frac` | positive | rho ≤ 0 or below the detection limit |
| **M2** | `g_first2` falls with `sec_frac` | negative | rho ≥ 0 or below the detection limit |
| **M3** | `adv` falls with `sec_frac` | negative | rho ≥ 0 or below the detection limit |

**The decisive form of each is the partial correlation controlling for latitude band**, because
the whole point is to ask whether composition explains what band labels. The pooled form is
reported alongside and is not decisive.

### Exploratory, promoted after seeing the data (two-sided, NOT pre-registered, reported separately)

| | hypothesis |
|---|---|
| **M4** | `adv` rises with `oc_bc`, partial on band |

**M4 may not be called a pre-registered result under any outcome.** It is reported because
concealing the largest correlation in the probe would be worse than reporting it with its
provenance attached.

---

## 4. Detection limits, computed before the analysis

Fisher-z, 80% power. These depend only on n and alpha and were computed without reference to any
outcome.

| test | n | alpha | detection limit |
|---|---:|---:|---:|
| M1–M3 pooled, one-sided, nominal | 46 | 0.05 | **0.362** |
| M1–M3 partial on band, one-sided, nominal | 46 | 0.05 | **0.374** |
| M1–M3 partial, one-sided, Holm worst case | 46 | 0.0167 | **0.438** |
| M4 partial, two-sided | 46 | 0.05 | **0.416** |
| any single band alone | 7–13 | 0.05 | **0.709 to 0.886** |

🔴 **Two consequences are registered in advance rather than discovered afterwards.**

**The probe's largest effect sits below the confirmatory detection limit.** The pooled `oc_bc`
correlation of +0.388 is under the 0.416 needed for M4 and under the 0.438 Holm worst case for
the confirmatory family. **The most probable outcome of this study is a bounded null**, and that
is stated here so it cannot later be presented as a disappointment or reframed as a success.

**Within-band testing is not attempted.** At 7 to 13 cities a band could only reveal
correlations above 0.71, which is larger than anything plausible here. Reporting per-band
correlations would be the exact error Chapter 5 of the thesis documents: an experiment that
cannot detect the effect it is looking for, reporting its silence as evidence. **Band enters
only as a control variable.**

---

## 5. Analysis, fixed now

1. Merge composition onto each ladder at `bottom == Bud0c`; drop cities with no `rmse_Bud3`.
2. Spearman rank correlations for M1 to M4, pooled.
3. **Partial** rank correlations controlling for band, by residualising the ranks of both
   variables on band indicators and correlating the residuals. Band is a 4-level factor, so
   3 degrees of freedom are spent.
4. Holm correction across the three confirmatory tests. M4 is corrected separately and never
   pooled into that family.
5. Bootstrap over **cities** (2000 resamples) for every reported correlation, because the unit
   is the city and days within a city are not independent.
6. Repeat on the GHAP ladder. **The MAIAC ladder is primary**; GHAP is reported as a
   sensitivity, since F.97 established that a monitor-trained covariate deflates the rung above
   it and can remove a real effect.

**No other analysis will be reported as confirmatory.** Anything further is exploratory and
labelled.

---

## 6. Decision rules

- **M1–M3 held** if the partial correlation has the registered sign, exceeds the detection
  limit, and survives Holm. Composition then explains part of what band labels, and Chapter 7's
  mechanism paragraph is rewritten from "candidate, untested" to a measured result.
- **M1–M3 undetectable** if the sign is right but the magnitude is below the detection limit.
  Reported as *undetectable at this power*, with the bound stated, exactly as the spatial null
  in Chapter 8 is reported. **This is the expected outcome.**
- **M1–M3 refuted** if the sign is wrong at a detectable magnitude. The ladder's generality is
  then strengthened and the thesis says so.
- **In every case**, Chapter 7 keeps the sentence that latitude is a label rather than a
  mechanism. A null here does not license attributing the band effect to latitude.

---

## 7. What this study cannot do

Stated in advance so no reader has to infer it.

It cannot establish causation. Composition, band, instrument class and network design all travel
together, and controlling for band does not control for the rest.

It cannot speak for cities outside the panel, which is valley and basin cities that publish
enough monitoring to be scored.

It uses **modelled** composition at ~25 km, not measured speciation. A city's `sec_frac` here is
a regional characterisation, and for a small city the grid cell is mostly its surroundings.

And it cannot rescue the sample size. **The panel is too small to establish a chemical mechanism
at the effect size that appears to be present**, which is itself the most useful thing this
registration can record in advance.
