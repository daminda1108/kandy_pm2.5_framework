## Guarantees, enforced mechanisms and discharged obligations {#s-guarantees-enforced-mechanisms-discharged}

Four properties are claimed, and they are not of equal standing. Stating them as though they
were would be the easiest way to oversell this work, so the differences are set out explicitly.

**Conservation is a guarantee.** The spatial mean of the field returns the temporal anchor,
analytically and under test, to the tolerance given in {{ref:s-decomposition-conserves}}. This holds by construction.

**Exact removal is a guarantee.** Taking a stream away reproduces the simpler tier exactly, to the
last decimal place, rather than approximately. This is what allows the difference between two tiers
to be attributed to the data and not to a change in the model, and {{ref:s-marginal-predictive-value-each}} depends on it
entirely.

**Skill never falling when data is added is an enforced mechanism, not a theorem, and it holds only
where the mechanism is fitted on the data being scored.** When an added observation does not help,
the model falls back towards the simpler tier through a shrinkage weight. In the first version of
the ladder that weight was chosen on the data being scored, so the score could not get worse. A city without a dense network cannot choose a weight that way, because the only
data that could choose it are the stations held back for scoring. The redesigned ladder of
{{ref:s-marginal-predictive-value-each}} therefore takes each city's weight from the other cities.
Out of sample, a rung can then score worse than the rung below it, and such losses are reported
rather than prevented. The property belongs to the estimator and to how its weight is chosen, not to
the data.

**Declared identifiability is an obligation that has been discharged, rather than a property of
the model.** The model states which of its parameters the data can actually pin down and which are
imposed by hand. Under a refined test, of
{{claim:p4.rows}} parameter combinations examined, {{claim:p4.identified}} were identified and
{{claim:p4.unidentified}} were not, with {{claim:p4.saturated}} saturating a bound. The one
parameter the specification says the data should constrain has profile intervals containing
unity in {{claim:p4.s_exp_intervals_containing_1}} of nine cases, so it is left at unity rather
than fitted.

The distinction matters because the phrase "four guaranteed properties" would be false, and it
is the kind of statement that survives review precisely because it is convenient.
