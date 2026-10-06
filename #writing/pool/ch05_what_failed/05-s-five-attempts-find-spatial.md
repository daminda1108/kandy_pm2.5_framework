## Five attempts to find spatial structure {#s-five-attempts-find-spatial}

**What was expected.** Kandy has a large within-city gradient. The roadside survey of {{ref:s-two-decades-measurement}}
measured concentrations varying by a factor of {{claim:spatial.obs_spread}} across the city.
Some covariate should encode it.

What happened. Five separate searches, over about four months.

The first tested whether the emission proxy correlated with observed concentration across
monitored cities, and found that it did, weakly. The second tested whether a learned spatial
pattern could beat the imposed one, and found a rank correlation near 0.14 [ledger track S]. The
third tested whether transport dynamics could be learned from the monitored panel, and found
that they could not, for the reason that the monitors are all sited on valley floors and
therefore never sample the vertical gradient. The fourth applied a general-purpose
earth-observation embedding, and found nothing. The fifth built a full land-use regression
predictor set [@Wang2012LUR], {{claim:lur.predictors}} predictors at
{{claim:lur.total_stations}} stations
across {{claim:lur.cities}} cities, and moved the pooled rank correlation from 0.273 to 0.275
[ledger F.61].

**What it cost.** Four months, and a settled belief that the spatial problem was
information-limited.

What it established. Very little, and that is the finding. Not one of the five stated, before
it ran, what size of effect it would have been able to detect. A power analysis conducted much
later established that at their sample sizes they could only have detected residual correlations
between {{claim:null.min_detectable_lo}} and {{claim:null.min_detectable_hi}}. They therefore
excluded a very large learnable signal and said nothing whatever about a moderate one.

For four months the project held a belief that its own evidence did not support. The belief
happened to be approximately correct, as {{ref:s-learned-spatial-pattern-pre}} shows, but it was held for the wrong
reason. A null result reported without a detection limit, meaning the smallest effect the
experiment could have found had one been there, converts a limitation of the experiment into a
claim about the atmosphere.

{{dia:taxonomy}}
