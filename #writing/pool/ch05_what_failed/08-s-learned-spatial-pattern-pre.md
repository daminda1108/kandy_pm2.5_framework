## A learned spatial pattern, pre-registered and refuted {#s-learned-spatial-pattern-pre}

**What was expected.** This is the only one of the eight where the expectation was recorded in
full before anything was run.

The registration [OSF 2jyfg] stated the benchmark, the detection limit and the bar. The benchmark
was the strongest single globally available predictor tested here, built-up land-cover fraction measured within
2.4 kilometres, which reaches a median per-city rank correlation of {{claim:phase1.best_rho}}
across {{claim:phase1.cities}} cities and {{claim:phase1.stations}} stations. The smallest
improvement the frame could detect at eighty per cent power was {{claim:phase1.min_detectable}}.
The bar was set at their sum, {{claim:phase2.bar}}, and the registration recorded the prediction
that it would not be cleared.

**What happened.** A pattern was learned subject to a conservation constraint, so that its
spatial mean is exactly one and it can therefore move material without creating it. Three
estimators were fitted, with leave-one-city-out throughout. The best reached
{{claim:phase2.rho_learned}}. The median paired difference against the benchmark was
{{claim:phase2.delta}}, better in {{claim:phase2.better_in}} of {{claim:phase1.cities}} cities,
at a p-value of {{claim:phase2.p_value}}.

{{fig:learnedbar}}

What it cost. About a week, because the preceding phases had already established the frame,
the benchmark and the detection limit.

What it established. A bounded claim, which none of the five nulls in {{ref:s-five-attempts-find-spatial}} produced:

> On {{claim:phase1.cities}} cities and {{claim:phase1.stations}} stations, a learned within-city
> pattern does not beat the best single globally available predictor by more than
> {{claim:phase1.min_detectable}} in rank correlation.

That is a different kind of statement from "no spatial signal was found". It says what was
excluded and, by implication, what was not. An effect smaller than the detection limit remains
entirely possible, and a campaign that sited monitors deliberately across land-use contrast
would be a different experiment; {{ref:s-six-negative-results-their}} runs the nearest version of it the panel allows.

Two further results came out of the same work and both are used later. The conservation
constraint holds to {{claim:phase2.gauge_drift}} across degenerate cases including a saturated
pattern and an overflow-range input, so a learned pattern can misplace material but cannot create
it. And no engineered emission surface beat a single freely available raster: a sector-weighted
composite reached {{claim:phase0.rho_sector}} against the production surface's
{{claim:phase0.rho_traffic}}, and adding industrial land use from open mapping data did not
change that conclusion.
