# Pre-registration — is the spatial signal being measured at the wrong resolution?

**Written 2026-08-06, BEFORE any result was computed.** Two tests, gates fixed here.
Nothing below may be revised after the numbers are seen; a failure is reported as a
failure. This document exists because the same session criticised the manuscript for
constructing a screening rule after seeing which city failed (Yichang), and the criticism
applies to us.

---

## Motivation

Every spatial number the project reports is a **Spearman rank correlation over per-station
annual means**. Two properties of that choice are suspicious, and both were adopted by
inheritance rather than by argument.

1. **It is an annual mean.** The confinement physics predicts that within-city contrast
   exists *only under stagnation* — that is what the term encodes, and it is why a
   ventilated-hour floor had to be invented at all (`additive_v3`). Averaging stagnant and
   ventilated hours together mixes a real signal with a structural zero.
2. **It is per-station.** That is the finest possible target, finer than the product is
   used for and finer than the 1 km field claims to resolve. Policy questions are asked at
   the level of *zones* (core, floor, slope), not of individual monitors.

F.29 established exactly this failure mode on the time axis: the evening emission signal
was real, and annual-mean fitting had averaged it into invisibility. The question here is
whether the same thing is happening on the space axis.

**This is a re-measurement, not a re-model.** No model quantity changes in either test.

---

## Test A — regime-conditional spatial rank

**Question.** Is the spatial rank stronger when the basin is stagnant than when it is
ventilated?

**Stratification.** Ventilation index `VI = BLH x wind speed`, computed from the model's
meteorological drivers — **independent of any observation**, so the strata cannot be drawn
around the answer. Hours are split into quintiles of VI within each city. Q1 = most
stagnant, Q5 = most ventilated.

**Statistic.** Per city and per quintile, Spearman ρ between modelled and observed
station means computed on that quintile's hours only, over the same held-out stations and
the same domain filter as the headline scorecard. Station-resampled bootstrap for
intervals, permutation test for p, as in F.26.

**Pre-registered predictions.**

- **A1** ρ(Q1, stagnant) > ρ(Q5, ventilated) in **at least 7 of the 9 estimable cities**.
- **A2** Pooled ρ(Q1) ≥ **0.40**, the project's existing pre-registered spatial gate, which
  the annual-mean statistic clears at only 4 of 9 cities.
- **A3** The gap ρ(Q1) − ρ(Q5) is **positive at Kandy's analogue cities specifically**
  (Chiang Mai, Kathmandu), not only at the high-relief Chinese valleys.

**Falsifier.** If ρ(Q1) ≈ ρ(Q5) — a difference under 0.05 pooled — then annual averaging
is *not* diluting a regime-dependent signal, the current statistic is the right one, and
this line is abandoned. That outcome is reported.

**What a pass would mean.** That the spatial pattern is recoverable *when it matters* —
stagnation hours are episode hours — and absent when it does not matter. The honest
headline becomes conditional rather than bounded, and the claim tier for the spatial
pattern rises from *partial, regime-bounded* to *validated under the conditions the
mechanism specifies*. It would **not** license claiming per-pixel accuracy at all hours.

---

## Test B — zone contrast instead of station rank

**Question.** Does the model resolve *zone-level* contrast even where it fails to rank
individual stations?

**Zone definition — fixed here, from model inputs only.** Terciles of the **traffic
emission surface** `S_emit` at each station's pixel: Z1 = lowest third (periphery),
Z2 = middle, Z3 = top third (core). This uses no concentration data of any kind, observed
or modelled, so zones cannot be drawn around the outcome. Cities with fewer than 3 ranked
stations, or with no station in some tercile, are not estimable and are reported as such.

**Statistic.** For each city, the zone contrast
`Δ = mean(top tercile) − mean(bottom tercile)`, computed separately for observations and
for the model. Then across cities, regress `Δ_obs` on `Δ_mod`.

**Pre-registered predictions.**

- **B1** The cross-city slope of `Δ_obs` on `Δ_mod` is **positive with a 90% bootstrap
  interval excluding zero**.
- **B2** Per-city **sign agreement** (both Δ positive, or both negative) in **at least 7 of
  the 9 estimable cities**, against 4.5 expected by chance.
- **B3** Zone contrast is recovered at **at least 2 cities whose station-level ρ is not
  distinguishable from zero** (from F.26: Yichang, Bazhong, Xichang, Chiang Mai). This is
  the specific claim that aggregation recovers signal that station rank misses, and it is
  the one that would justify changing what the product reports.

**Falsifier.** If B1 fails, or if B3 recovers nothing at the four null cities, then the
signal is genuinely absent rather than mis-measured, the information-ceiling conclusion
stands unchanged and unqualified, and the paper keeps its current statistic.

**Known limitation, stated in advance.** Δ is a difference of means over few stations; it
is a *coarser* statistic with correspondingly wider intervals, and a positive result must
not be presented as though it were per-station skill. The gain, if any, is that a coarse
claim can be validated where a fine one cannot.

---

## Multiplicity and reporting

Six pre-registered predictions across two tests. We report **all six outcomes**, pass or
fail, and we do not convert a partial pass into a headline. Neither test may be re-run with
a different stratification, a different zone count, or a different city set after the
result is seen; if either looks worth varying, the variation is a new pre-registration.

If Test A passes and Test B fails, the reported claim is regime-conditional and
station-level. If both fail, the manuscript is unchanged and this document is published as
a negative result — it is a useful one, because "the spatial ceiling is not an artefact of
the evaluation statistic" is a stronger version of the current claim than "we did not
check".

**Artifacts:** `scripts/spatial_resolution_tests.py` →
`results/figures/multicity/spatial_resolution_tests.{csv,json}`.
