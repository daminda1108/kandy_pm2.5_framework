# Pre-registration — per-city significance, and an estimator that works on sparse networks

**Written 2026-08-07, BEFORE any number was computed.** Follow-up to
`prereg_common_hours_spatial_2026-08-07.md`, whose C1 could not be evaluated and whose C4
branch is therefore unsupported.

---

## What the previous round left open

The anomaly estimator E1 (per-hour network-mean removal) gave a pooled rank of **+0.621**,
against **+0.696** hour-matched and **+0.372** as published. Its permutation control passed
at the pooled level (null centred +0.001; E1 above the null p95 of +0.520). But two things
block adoption:

1. **C1 was unevaluable.** The common-hours check E2 required 80% of ranked stations
   reporting simultaneously, which only 3 of 9 cities ever achieve. Where computable, E1
   and E2 agreed to 0.011 — but three cities cannot validate an estimator.
2. **Per-city significance was never registered.** The pooled permutation null has a p95 of
   **+0.520**. With 4 to 17 stations per city, a rank correlation of 0.5 arises by chance
   easily. "8 of 9 cities exceed 0.40" is therefore arithmetic, not evidence, and the
   upward revision it implies is not supported at the city level.

This round fixes both. **The author's prior from the previous round was wrong** — E1 came
out well above the published values, not below — and that is recorded here rather than
quietly dropped.

---

## The new estimator

**E3 — pairwise co-observed concordance.** For every unordered station pair (i, j) with at
least 50 hours in which **both** report, compute the mean observed difference and the mean
modelled difference over exactly those shared hours:

```
d_obs(i,j) = mean_{t : both report} [ obs(i,t) − obs(j,t) ]
d_mod(i,j) = mean_{t : both report} [ mod(i,t) − mod(j,t) ]
```

The statistic is the concordance `tau_pair = 2C − 1`, where `C` is the fraction of pairs
whose two differences share a sign.

Why this is the right instrument for sparse networks: it never requires all stations to
report at once, only pairs. Every pair contributes on its own overlap, so a network that
never achieves a global quorum still yields an estimate. It removes the temporal confound
by the same logic as E1 — each comparison is made within shared hours — while degrading
gracefully as coverage thins.

**Scale comparability.** `tau_pair` is a Kendall-family statistic and is not on the same
scale as Spearman's rho. E1 is therefore **also** recomputed as Kendall's tau (`E1_tau`)
for the comparison, so the agreement test is like-for-like. Both are reported.

---

## Pre-registered gates

**D1 — per-city permutation significance of E1.** For each city, 5000 permutations of which
station receives which modelled anomaly; report the two-sided p and the null p95. Count the
cities with p < 0.05. *No threshold attached to the count itself; it feeds D4.*

**D2 — validity, and the one that must pass.** E3 and E1_tau agree: pooled
|tau_pair − E1_tau| ≤ 0.15, and per-city sign agreement in **at least 7 of the 9 estimable
cities**. E3 is estimable wherever pairs overlap, so unlike C1 this gate is reachable.
*If D2 fails, neither estimator is adopted and the published spatial column stands with the
instability documented as a limitation.*

**D3 — small-n inflation check.** Report the correlation between per-city E1 and the number
of ranked stations. If |r| ≥ 0.5, the apparent skill is confounded with network size and
must be reported as such rather than as spatial skill.

**D4 — the decision rule, fixed now.** Counting only cities where E1 is significant at
p < 0.05 **and** ρ ≥ 0.40:

- **7 or more of 9** → the published "fine spatial rank does not transfer" claim is wrong;
  the manuscript is revised upward and E1 replaces the spatial column.
- **4 to 6** → the current partial, regime-bounded claim stands, restated on the corrected
  estimator, with per-city significance reported.
- **3 or fewer** → the information-ceiling conclusion is **strengthened**; the previously
  published values were, if anything, optimistic, and the upward signal in the pooled
  number was small-sample noise.

**D5 — Kandy's analogues, reported singly.** Chiang Mai and Kathmandu, with their per-city
p values. No threshold. The previous round found them the two weakest in the panel
(+0.22, +0.43) and the reader is entitled to see whether that survives significance testing.

---

## Prior, stated again so it can be scored again

Having been wrong last round, I hold this one loosely. My expectation is the **middle
branch** of D4: a handful of well-monitored, high-relief cities show significant rank and
the sparse ones do not, leaving the claim partial and regime-bounded but on a defensible
estimator. I specifically expect **Chiang Mai to fail significance**, which would matter,
because it is Kandy's closest climatic analogue.

---

## Reporting rules

All five outcomes reported. No parameter may be varied after the result is seen — not the
50-hour pair minimum, not the 5000 permutations, not the p < 0.05 threshold, not the city
set. The previous round's failure to reach C1 is a lesson already applied here: **D2 was
designed to be evaluable on the coverage this panel actually has**, which is the mistake
that invalidated the last attempt.

**Artifacts:** `scripts/spatial_significance_test.py` →
`results/figures/multicity/spatial_significance_test.{csv,json}`.
