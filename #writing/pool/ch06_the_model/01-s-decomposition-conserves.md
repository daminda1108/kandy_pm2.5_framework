## The decomposition and what it conserves {#s-decomposition-conserves}

Write *T*(*t*) for the concentration averaged over the basin at hour *t*, *B*(*t*) for the regional
and transboundary background, taken uniform across the fifteen kilometre domain, and *P*(*x*, *y*, *t*)
for a dimensionless local pattern normalised so that its spatial mean is one. With the local
increment written as inc(*t*) = *T*(*t*) − *B*(*t*), concentration on the kilometre grid is

$$\mathrm{PM}(x,y,t) = B(t) + \max(\mathrm{inc},0)\,P(x,y,t) + \min(\mathrm{inc},0) + e(t)\,\bigl(P-1\bigr)$$

The elementary form is the first two terms with the corrections set to zero: a uniform
background plus a local increment redistributed by a unit-mean pattern. This is the additive
urban increment decomposition familiar from monitoring network analysis [@Lenschow2001], and the
scale separation it rests on has long precedent in air quality time series work [@Rao1994;
@Eskridge1997]. The additional terms are corrections and are derived in {{ref:s-two-correction-terms}}.

{{dia:decomposition}}

The pattern *P* is normalised so that it averages to one across the city. Because of that,
**the spatial average of the field returns *T*(*t*) exactly**: the pattern moves material around the
basin without changing how much of it there is. That single condition does three things, and
together they are why this form was chosen over a multiplicative one.

It prevents an imposed spatial pattern from displacing the level, which is the quantity the
observations actually constrain. It separates the temporal anchor from the spatial redistribution,
so the two can be evaluated independently, which is what {{ref:ch-validation-without-local-ground}} exploits. And it bounds the
consequence of being wrong: an error in *P* is an error in **where** material sits, never in
**how much** of it there is.

**What that condition does not do is pin down *B*.** Being exact here matters, because the
stronger statement is easy to make and is false. Taking the spatial mean of the field returns *T*
whatever the background happens to be. For any other background *B*′ that is physically allowed,
setting *P*′ = (*C* − *B*′) / (*T* − *B*′) gives a pattern that also averages to one and reproduces exactly
the same field, so the condition is satisfied by every candidate background rather than by one.
What it fixes is the anchor and the scale of the pattern. It says nothing about how the anchor
divides into a background and an increment. That division is settled by the constraint in
{{ref:s-partition-constraint-rather-than}} and by the way *B* is built in {{ref:s-information-budget}}, and how much the resulting fraction moves
when those choices are varied is reported there rather than assumed away.

One qualification belongs here rather than in a limitations list. The satellite anchor is exact,
in that the annual mean of *T* matches the reference product to four decimal places every year.
The delivered field nonetheless sits {{claim:gauge.drift_lo_pct}} to {{claim:gauge.drift_hi_pct}}
per cent above it, consistently and in the same direction. The cause is a small error accumulating across build steps rather than a fault in the
normalisation itself: each step preserves the mean, but the pattern is recovered from the output of
the previous step rather than from the anchor directly, so a small positive offset builds up. The condition holds by construction and to within about half a per cent
in practice, and this thesis states it that way, not as an exact identity.

### The uniform background assumption {#s-uniform-background-assumption}

Taking *B*(*t*) uniform over the domain looks like a strong physical assumption and is mostly a
definition. The decomposition splits concentration into a part with no horizontal structure at
this scale and a part with all of it, so anything varying across fifteen kilometres is assigned
to the increment by construction. The assumption is not that regional air is truly uniform. It is
that the split is useful, which requires the uniform part to be large and the residual structure
in it to be small beside the increment's.

Three lines support that, and one of them is a measurement made for this thesis.

Regional air arriving over the basin has travelled hundreds of kilometres and is well mixed
through the depth of the boundary layer, so its horizontal gradient across fifteen kilometres is
small compared with a local increment whose sources sit inside the domain.

If the background were behaving as a locally accumulating quantity it would dilute as the
boundary layer grows through the day. Fitting the exponent that would express that gives
{{claim:dilution.exponent}} against a value of one for pure inverse-height dilution, so the
component is close to inert to the diurnal cycle. That is the behaviour of air already mixed
rather than air accumulating in place.

{{ref:s-independent-chemical-check}} supplies composition evidence from an independent direction: air classified by
arrival sector as continental is more secondary-rich, and therefore more aged, than air arriving
from the ocean. A background composed of aged air is what the decomposition requires.

The assumption is nonetheless the one a denser network would test first, and {{ref:s-marginal-predictive-value-each}} is
explicit that the proxy standing in for *B* is the weakest link in the chain.

### The imposed pattern is not an arbitrary prior {#s-imposed-pattern-arbitrary-prior}

If *P* were chosen freely it would carry no information and the conservation property would
merely make it harmless. Three things stop it being arbitrary, and the third matters most.

It is constructed from measured quantities rather than fitted parameters. The surface combines
an emission proxy built from the road network [@Ntziachristos2000] with a confinement term
built from the digital elevation model, and neither is tuned to concentration data in the city where it is applied.

It is falsifiable and has been scored. Across the ten cities of {{ref:s-model-across-ten-cities}} the pattern's rank
against held-out monitors is reported rather than assumed, with a median of
{{claim:scorecard.spatial_rho_median}}.

**And it has been partly refuted, which an arbitrary prior cannot be.** {{ref:s-spatial-contrast-lost}} reports that
the dispersion step, which is the part of the model that redistributes the emission
surface through terrain-steered flow, **lowers** rank from {{claim:r2.rho_emission_surface}} to
{{claim:r2.rho_with_atransport}}. A prior that cannot fail would not have produced that result,
and the appropriate response is {{ref:s-construction-step-most-worth}}'s rather than a defence of the model.
