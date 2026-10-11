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
divides into a background and an increment. That division is bounded by the constraint in
{{ref:s-partition-constraint-rather-than}} and by the way *B* is built in {{ref:s-regional-background}}, and how much the resulting fraction moves
when those choices are varied is reported there rather than assumed away.

#### Three quantities kept distinct {#s-three-quantities}

Three quantities are easily conflated, and this thesis keeps them apart throughout.

The **regional-background estimate** *B*(*t*) is a constructed quantity: a level and a daily series
built from a satellite surface, a composition model and an air-mass classification
({{ref:s-regional-background}}). It is not a measured inflow.

The **local increment** *T*(*t*) − *B*(*t*) is the residual of the total above that estimate under
the specified decomposition. Its share of the total is the **local fraction** *f*. Because *B* is
constructed and capped by a constraint, *f* is a property of the decomposition and moves when the
decomposition is specified differently ({{ref:s-partition-constraint-rather-than}}).

The **locally emitted primary contribution** is the mass emitted directly by sources inside the
basin. It is a different physical quantity, the one an emission-control decision acts on, and this
model does not observe it: the local increment includes secondary aerosol formed inside the basin
from precursors of any origin, and excludes aerosol formed regionally. Where this thesis bounds it,
it does so separately ({{ref:s-partition-detail}}).

One qualification belongs here rather than in a limitations list. The condition holds only if every
spatial factor that multiplies the anchor has unit spatial mean at every hour, and an earlier build
broke it in two places. The confinement term was multiplied with the level surface without being
renormalised, and the two covary on the valley floor; and the dispersion factor was renormalised on
its own rather than against the field it multiplied, so where it reinforced the core-high pattern the
product's mean exceeded the anchor. The second effect dominated: the delivered field sat about half a
per cent above the anchor, most on still rush-hour evenings when the dispersion factor was strongest.
Both factors are now renormalised against the field they multiply, the anchor is read directly from
*T*(*t*) rather than from a derived field, and a test asserts that the delivered field's annual mean
equals *T*(*t*). The largest annual departure is now {{claim:gauge.drift_hi_pct}} per cent at one
decimal place; individual hours can still depart slightly where the floor at zero applies on the
cleanest hours.

Two assumptions carry the construction: that the background can be treated as uniform across the
domain, and that the imposed pattern is more than an arbitrary prior. Both are examined in
{{ref:s-decomposition-assumptions}}.
