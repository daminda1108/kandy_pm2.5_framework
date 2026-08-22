# Pre-registration — a spatial rank statistic that cannot launder temporal skill

**Written 2026-08-07, BEFORE any number was computed.** I hold a strong prior about the
outcome (stated below), which is exactly why the gates are fixed first.

---

## The problem this exists to solve

The project reports fine within-city spatial skill as a Spearman rank correlation over
per-station means. There are two ways to compute those means and they disagree by a lot.

| city | published (unpaired) | hour-matched (paired) | shift |
|---|---:|---:|---:|
| Chiang Mai | −0.06 | +0.82 | +0.88 |
| Yichang | +0.13 | +0.95 | +0.82 |
| Xichang | +0.07 | +0.75 | +0.68 |
| Kathmandu | +0.39 | +0.93 | +0.54 |
| Bazhong | +0.10 | −0.22 | **−0.32** |
| Medellín | +0.78 | +0.78 | −0.00 |
| Bogotá | +0.67 | +0.63 | −0.04 |

Mean |shift| = 0.404. `spatial_pairing_diagnostic.py` established that the difference is
**isolated to hour-matching alone** (the unpaired route reproduces the published scorecard
to 0.000, on the same stations, years and domain filter) and that **no join defect** is
involved (the merge is strictly one-to-one).

**Both statistics are flawed, in opposite ways.**

- **Unpaired** averages modelled values over all modelled hours and observed values over
  all observed hours. If stations report over different periods, each station's observed
  mean partly encodes *when* it reported rather than *where* it is.
- **Paired** forces both means onto the same hours, which fixes that — but thereby gives
  every station the same temporal weighting as its own observations. A model with strong
  temporal skill and **zero spatial skill** would then still produce correlated station
  means, purely by getting the seasonal and diurnal cycles right. This model's seasonal
  *r* is 0.94–1.00, so the contamination channel is wide open.

The diagnostic supports this reading: the two cities with the most *even* station coverage
(Medellín CV 0.30, Bogotá CV 0.34) shift by −0.003 and −0.039, while the most uneven
(Kathmandu CV 1.15, Bazhong CV 1.01) shift by +0.54 and −0.32.

**Neither number should be published.** This registers the estimator that should be.

---

## The estimators

Both remove the shared temporal weighting by construction. They are computed on the same
held-out stations, years and domain filter as every previous spatial number.

**E1 — network anomaly.** For each hour *t*, over the set `S_t` of held-out stations
reporting at *t* (require `|S_t| ≥ 3`), subtract that hour's network mean from both
observed and modelled values:

```
a_obs(i,t) = obs(i,t) − mean_{j∈S_t} obs(j,t)
a_mod(i,t) = mod(i,t) − mean_{j∈S_t} mod(j,t)
```

Average each station's anomaly over time, then Spearman across stations. Any hour-level
signal common to the whole network — season, diurnal cycle, episodes, the entire temporal
skill of the anchor — is removed *within each hour* and cannot enter the rank. What
survives is the persistent station-to-station offset, which is the spatial claim.

**E2 — common hours.** Restrict to hours in which at least 80% of the ranked stations
report simultaneously; require at least 200 such hours, else the city is not estimable.
Compute plain means over that shared hour set. Every station is then averaged over an
identical set of hours, so no temporal-weighting difference exists to launder.

E1 uses all data and is the primary estimator. E2 is the independent check: they attack
the same confound by different routes and should agree.

---

## Pre-registered predictions

**C1 — the two estimators agree.** Pooled |ρ(E1) − ρ(E2)| ≤ 0.15, and per-city sign
agreement in at least 7 of the 9 estimable cities. *Failure means one estimator is broken
and neither result may be used.* This is the validity gate and is checked first.

**C2 — the anomaly rank is below the paired rank.** Pooled ρ(E1) < pooled ρ(paired), by
more than 0.10. This is the direct test of the contamination hypothesis. *If C2 fails, the
contamination argument is wrong and the paired numbers deserve reconsideration.*

**C3 — permutation control.** Randomly permuting which station receives which modelled
anomaly must destroy the correlation: the permutation null must be centred within ±0.10 of
zero, and the observed pooled ρ(E1) must exceed the 95th percentile of that null for the
result to count as signal at all. *This is the check that the estimator cannot manufacture
rank from nothing.* Failure invalidates E1 outright.

**C4 — the decision rule, fixed in advance.** Whatever ρ(E1) turns out to be, the
manuscript will carry it, and the consequence is determined now rather than after:

- if ρ(E1) ≥ 0.40 at **7 or more** of 9 estimable cities → the published claim that fine
  spatial rank does not transfer is **wrong and must be revised upward**;
- if ρ(E1) ≥ 0.40 at **4 to 6** cities → the current "regime-bounded, partial" claim
  stands, with the estimator corrected and the numbers restated;
- if ρ(E1) ≥ 0.40 at **3 or fewer** cities → the information-ceiling conclusion is
  **strengthened**, and the previously published values were optimistic.

**C5 — Kandy's analogues.** Report ρ(E1) separately for Chiang Mai and Kathmandu. No
threshold is attached; this is reported because Kandy's transfer argument leans on them and
the reader is entitled to see them singly rather than pooled.

---

## My prior, stated so it can be held against me

I expect ρ(E1) to fall **well below** the paired values and **near or below** the published
unpaired ones — that is, I expect the middle or third branch of C4, and I expect this
exercise to end by making the project's spatial claim *weaker*, not stronger. I am running
it because the current number rests on an undocumented convention, and an unstable
pessimistic number is no more publishable than an unstable optimistic one.

If the first branch of C4 occurs — genuine transfer at 7+ cities after the confound is
removed — that is a major upward revision to the paper and I will report it as such, with
the permutation control (C3) as the load-bearing evidence, because a favourable surprise
here needs more support than an unfavourable one.

---

## Reporting rules

All five outcomes reported, pass or fail. The estimator is not to be varied after the
result is seen: no changing the 80% quorum, the `|S_t| ≥ 3` floor, the 200-hour minimum,
or the city set. Any variation is a new pre-registration. The prior above is published with
the result so that a confirmation is visibly distinguishable from a surprise.

**Artifacts:** `scripts/spatial_common_hours_test.py` →
`results/figures/multicity/spatial_common_hours_test.{csv,json}`.
Supersedes the spatial column of `validation_scorecard.csv` if C1 and C3 pass.
