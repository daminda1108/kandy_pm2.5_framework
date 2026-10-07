# An attributable-burden projection {#app-attributable-burden-projection}

This projection sits in an appendix because two independent readers made the same point
about it, and both were right. A figure of the form "N deaths per year" is quotable in a
way its caveats are not. The arithmetic below is illustrative: it shows the order of magnitude
the delivered field implies, it applies the response function outside the population for which
that function is defined, and its interval omits most of the uncertainty a complete estimate would
carry.

It is included because {{ref:ch-kandy-setting-record-stakes}} names health as one of the two stakes, and a thesis that
raises a stake and then declines to quantify it has evaded its own framing. It is placed
here because the arithmetic is a projection of this field through somebody else's
epidemiology, not a measurement this work performed.

{{fig:burden}}

**The projection.** The population-weighted exposure of {{ref:s-exposure-weighting}} is passed
through the Global Exposure Mortality Model for non-communicable disease and lower respiratory
infection [@Burnett2018], against a national mortality baseline. That gives
{{claim:burden.deaths}} attributable deaths per year, an attributable fraction of
{{claim:burden.fraction_pct}} per cent, of which {{claim:burden.avoidable}} would be avoidable if
concentrations met the World Health Organization guideline [@WHO2021]. The accompanying interval,
{{claim:burden.ci_low}} to {{claim:burden.ci_high}}, is obtained by passing the lower and upper
bounds of the field's ninety per cent interval through the same central response function.

**The response function was applied to all ages.** The model is defined for adults of
twenty-five and older, with baseline mortality taken by age group. The projection here instead
applied it to the whole population of the modelled domain, using the national crude death rate for
all ages scaled by the share of deaths from the included causes. The domain is the fifteen
kilometre square of the field, which holds more people than the municipality of Kandy, so the
count refers to the domain and not to the city. Because children and young adults have low
mortality from these causes, applying the function to all ages with an all-age crude rate does not
reproduce the age-structured calculation, and the direction and size of the difference have not
been established. A corrected estimate requires age-specific baseline mortality for Sri Lanka by
cause, from the Global Burden of Disease study, which had not been obtained when this thesis was
written. Until it is, the figures above are an illustration of scale and not an estimate.

**What the interval contains.** It propagates the uncertainty of the concentration field's
anchor, as carried by the delivered interval, through the central response function. It carries no
uncertainty from the response function itself, whose published parameters are uncertain, none from
the mortality baseline, none from the population weighting, and none from the omissions of the
delivered interval set out in {{ref:s-interval-calibration}}. Nor does it carry the open level
question of {{ref:s-checks-kandy-carry-weight}}: if the three low point records are right and the
model reads high, the burden is over-stated. A full interval would be wider than this one by an
amount this thesis has not estimated. **It should not be read as a total uncertainty interval on
the burden.**

**Three further qualifications.** The response function and the mortality baseline are both
taken from published work and neither was estimated here, so this is a projection of the delivered
field through somebody else's epidemiology rather than an epidemiological result. The share of
deaths from the included causes is a national figure applied to a city. And the exposure is a
modelled area quantity weighted by a modelled distribution of where people spend their time, so
every error in the field and in the weighting enters the projection without being represented in
its interval.

The figures in this section were regenerated for this thesis, and doing so moved them. The
exposure and burden files predated the field rebuild, so the previously reported uplift of seven
per cent and burden of 427 were computed on a superseded field. This is recorded because it is
the same failure mode {{ref:ch-reproducibility-machinery-catches-errors}} describes and it was found the same way.
