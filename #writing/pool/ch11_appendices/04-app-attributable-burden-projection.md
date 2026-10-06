# An attributable-burden projection {#app-attributable-burden-projection}

This projection sits in an appendix because two independent readers made the same point
about it, and both were right. A figure of the form "N deaths per year" is quotable in a
way its caveats are not, and the interval attached to it propagates the published
uncertainty in the concentration-response function and nothing else. It carries no
uncertainty from the concentration field, none from the population weighting, and none
from the unresolved level discrepancy of {{ref:s-checks-kandy-carry-weight}}. A complete interval would be wider
by an amount this thesis has not estimated.

It is included because {{ref:ch-kandy-setting-record-stakes}} names health as one of the two stakes, and a thesis that
raises a stake and then declines to quantify it has evaded its own framing. It is placed
here because the arithmetic is a projection of this field through somebody else's
epidemiology, not a measurement this work performed.

{{fig:burden}}

The attributable burden. Projecting the population-weighted exposure through a published
concentration-response function [@Burnett2018] against the national mortality baseline gives
{{claim:burden.deaths}} attributable deaths per year, with a **response-function-conditional
interval** of {{claim:burden.ci_low}} to {{claim:burden.ci_high}}. That is an attributable
fraction of {{claim:burden.fraction_pct}} per cent, of which {{claim:burden.avoidable}} would be
avoidable if concentrations met the World Health Organization guideline [@WHO2021].

The interval is named that way because of what it does not contain. It propagates the published
uncertainty in the response function and nothing else. It carries no uncertainty from the
concentration field, from the population weighting, or from the level discrepancy of {{ref:s-checks-kandy-carry-weight}},
and a full interval would be wider than this one by an amount this thesis has not estimated.
**It should not be read as a total uncertainty interval on the burden.**

**Three qualifications, and they are not small.** The response function and the mortality
baseline are both taken from published work and neither was estimated here, so this is a
projection of the delivered field through somebody else's epidemiology rather than an
epidemiological result. The interval reflects only the published uncertainty in the response
function and not uncertainty in the field, which would widen it. And the estimate inherits the
level discrepancy of {{ref:s-checks-kandy-carry-weight}}: if the three low point records are right and the model reads
high, the burden is over-stated proportionally.

The figures in this section were regenerated for this thesis, and doing so moved them. The
exposure and burden files predated the field rebuild, so the previously reported uplift of seven
per cent and burden of 427 were computed on a superseded field. This is recorded because it is
the same failure mode {{ref:ch-reproducibility-machinery-catches-errors}} describes and it was found the same way.
