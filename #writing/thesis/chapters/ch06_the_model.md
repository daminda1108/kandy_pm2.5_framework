# Chapter 6. The model

The construction described here is deliberately modest in its physics and entirely conventional
in its machine learning. Neither is the contribution. What the model does that is unusual is
declare which observations it is entitled to use, and degrade exactly when one of them is
withheld. That property is what makes Chapter 7 a measurement rather than a set of ablations,
and everything else in this chapter exists to support it.

{{dia:pipeline}}

## 6.1 The decomposition and what it conserves

Write `T(t)` for the concentration averaged over the basin at hour `t`, `B(t)` for the regional
and transboundary background, taken uniform across the fifteen kilometre domain, and `P(x, y, t)`
for a dimensionless local pattern normalised so that its spatial mean is one. With the local
increment written as `inc(t) = T(t) - B(t)`, concentration on the kilometre grid is

```
PM(x, y, t) = B(t) + max(inc, 0) * P(x, y, t) + min(inc, 0) + e(t) * (P - 1)
```

The elementary form is the first two terms with the corrections set to zero: a uniform
background plus a local increment redistributed by a unit-mean pattern. This is the additive
urban increment decomposition familiar from monitoring network analysis [@Lenschow2001], and the
scale separation it rests on has long precedent in air quality time series work [@Rao1994;
@Eskridge1997]. The additional terms are corrections and are derived in Section 6.5.

{{dia:decomposition}}

Because `P` integrates to unity, **the spatial average of the field returns `T(t)` exactly**.
The pattern moves material around the basin without altering how much of it there is. That
condition does three things at once, and they are the reason the decomposition was chosen over
a multiplicative alternative.

It prevents an imposed spatial pattern from displacing the level, which is the quantity the
observations actually constrain. It makes level and pattern separately identifiable, so each can
be validated independently, which is what Chapter 7 exploits. And it bounds the consequence of
being wrong: an error in `P` is an error in **where** material sits, never in **how much** of it
there is.

One qualification belongs here rather than in a limitations list. The satellite anchor is exact,
in that the annual mean of `T` matches the reference product to four decimal places every year.
The delivered field nonetheless sits {{claim:gauge.drift_lo_pct}} to {{claim:gauge.drift_hi_pct}}
per cent above it, consistently and in the same direction. The cause is an accumulation across
build steps rather than a defect in the gauge: each step preserves the mean, but the unit-mean
pattern is recovered from an upstream field rather than from the anchor directly, and a small
positive offset accrues. The condition holds by construction and to within about half a per cent
in practice, and this thesis states it that way rather than as an exact identity.

## 6.2 Comparing an areal model to a point instrument

A field is areal. A monitor is a point. Comparing them by co-location is a change-of-support
error and it is the most common way a model of this kind is scored wrongly.

{{dia:obsoperator}}

For each instrument `k`,

```
y_k(t) = H_k[C](t) + b_k + e_k,      e_k ~ N(0, s_meas,k^2 + s_rep,k^2)
```

with `H_k` an observation operator, `b_k` a systematic offset and `s_rep` a representativeness
error arising from sub-grid variability the model cannot resolve. The operators differ by
instrument class. A reference monitor and a low-cost sensor are near-delta in space. A satellite
product is already an areal average. A passive sampler integrates in time rather than space, and
a mobile campaign integrates along a path.

Two quantities here are distinct and are routinely conflated. `b_k` is **systematic**: siting
bias plus device calibration. A kerbside monitor inside a kilometre cell reads systematically
above the cell mean, and this is also where a low-cost sensor's calibration error lives
[@Barkjohn2021; @Morawska2018]. `s_rep` is **random**, arising from unresolved structure, and it
is estimated from the local spatial variability of the field itself, so it grows in structured
hours and shrinks when the basin is well mixed.

This level of description is not decoration, and the clearest demonstration is a diagnosis it
makes available. The delivered ninety per cent interval covers {{claim:kandy.cov90}} per cent of
observations at the two Kandy sensors. Read alone, that suggests the interval is too narrow. It
is not. Observations fall below the lower bound in {{claim:kandy.miss_below}} per cent of hours
and above the upper bound in {{claim:kandy.miss_above}} per cent, which is a one-sided failure
rather than a width failure. Removing each sensor's own median offset restores coverage to
{{claim:kandy.cov90_recentred}} per cent. The interval was correctly scaled and incorrectly
centred, and only an explicit `b_k` makes that diagnosis available at all.

A limitation follows immediately and is stated rather than left to be inferred. The operators
are implemented and tested, and `b_k` and `s_rep` are estimated at panel cities that have
reference monitors. At Kandy they are **not estimated**, because estimating them requires a
reference monitor and Kandy has none. The observation model therefore disciplines the comparison
at the demonstration city without correcting it.

## 6.3 The information budget

An information budget declares which observation streams a tier of the model may use. Builders
assert against it, so a stream a tier is not entitled to is unreachable by construction rather
than by discipline.

{{dia:tiers}}

The tiers are nested, and the nesting is asserted at import time so that a malformed budget
cannot be registered. Each tier declares, in one machine-readable object, what it admits, what it
estimates, what it imposes, and which tier it degrades to.

Admissibility is checked in three directions, and each check exists because the corresponding
failure occurred in this project.

The first stops a tier reaching for information it was not granted. This is the obvious
direction and it was implemented first.

The second stops a tier **quietly failing to use what it has**. This is the direction that was
missing, and Section 5.7 describes what its absence cost: the sensorless tier used one of the
three streams its budget admits, so every gain measured above it was measured against an
artificially weak baseline.

The third stops a tier being scored on units that lack one of its streams. A single city missing
a stream is invisible in a pooled median and shifts it.

The sensorless tier as finally specified carries {{claim:bud0c.n_features}} predictors, of which
{{claim:bud0c.n_geo_features}} are static geography. Chapter 7 shows that this width is not
incidental to the results.

## 6.4 What the construction guarantees, and what it does not

Four properties are claimed, and they are not of equal standing. Stating them as though they
were would be the easiest way to oversell this work, so the differences are set out explicitly.

**Conservation is a guarantee.** The spatial mean of the field returns the temporal anchor,
analytically and under test, to the tolerance given in Section 6.1. This holds by construction.

**Exact degradation is a guarantee.** Withholding a stream reproduces the lower tier
bit-for-bit, not approximately. This is what allows the difference between two tiers to be
attributed to information rather than to model change, and Chapter 7 depends on it entirely.

**Monotone skill under added information is an enforced mechanism, not a theorem.** The
construction shrinks towards the lower tier when the added observation does not help, so skill
cannot decrease. That is a property of the estimator that was built in deliberately, and a
different estimator would not have it.

**Declared identifiability is a discharged obligation rather than a property.** The model states
which parameters the data can constrain and which are imposed. Under a refined test, of
{{claim:p4.rows}} parameter combinations examined, {{claim:p4.identified}} were identified and
{{claim:p4.unidentified}} were not, with {{claim:p4.saturated}} saturating a bound. The one
parameter the specification says the data should constrain has profile intervals containing
unity in {{claim:p4.s_exp_intervals_containing_1}} of nine cases, so it is left at unity rather
than fitted.

The distinction matters because the phrase "four guaranteed properties" would be false, and it
is the kind of statement that survives review precisely because it is convenient.

## 6.5 The two correction terms

The elementary form fails in two specific and diagnosable ways. Each additional term repairs
exactly one of them.

**The increment split.** When the hourly total falls below the background, `inc` is negative, and
multiplying a core-high pattern by a negative number renders the city centre **cleaner** than the
countryside. The defect is obvious once seen and invisible in every aggregate statistic, because
it preserves the mean exactly. Against the unconstrained background it occurs in
{{claim:field.precap_excess_mean}} per cent of Kandy hours and, because ventilation peaks when
the boundary layer is deepest, in {{claim:field.precap_excess_midday}} per cent of midday hours.
The defect therefore concentrates in exactly the hours a daytime user would look at. The repair
is to structure only the accumulation above background and let ventilation below it apply
uniformly, which is the `max(inc, 0) * P` and `min(inc, 0)` pair. The basin mean is preserved
exactly and the midday inversion falls to {{claim:field.postcap_inversion_midday}} per cent.

**The ventilated-hour floor.** The split renders ventilated hours perfectly flat, and ground
truth from a city with a dense network shows they are not. A bounded, mean-zero term
`e(t)(P - 1)` restores a small amount of structure on those hours. Being mean-zero, it leaves
conservation exact; being bounded below by zero and acting only on the accumulation side, it
cannot re-invert the core; and setting its scale to zero recovers the previous form exactly,
which is verified rather than asserted.

## 6.6 The partition, which is a constraint rather than a choice

The decomposition is only useful to a decision if the split between local and regional is
credible, and for most of this project's history it was not. The value was taken from source
apportionment literature and sat near a quarter.

The argument that replaced it is short. Local sources emit continuously. Rain changes removal,
not emission. Therefore at an emitting location the local increment is strictly positive at every
hour, the background can never reach the total, and **a background at or above the total is not
an unusual hour but an over-estimated background**. Since `B` is flat within a day, the
constraint has a closed form: cap each day at `(1 - F_min)` times that day's minimum hourly
total.

Before the constraint, the background exceeded the total in
{{claim:field.precap_excess_lo}} to {{claim:field.precap_excess_hi}} per cent of hours, averaging
{{claim:field.precap_excess_mean}}. In each such hour the field rendered flat and reported a zero
local share at the traffic core. After the constraint the residual is at worst
{{claim:field.postcap_excess_max}} per cent in any year, and every remaining case is an hour
where the anchor itself returned a negative total, which no constraint on the background can
repair.

Across the anchored years the local fraction is **{{claim:partition.f}}**, ranging
{{claim:partition.f_lo}} to {{claim:partition.f_hi}}.

**The result does not depend on the free parameter.** Sweeping `F_min` from zero to
{{claim:field.f_sweep_param_hi}}, a fourfold change, moves the fraction from
{{claim:field.f_sweep_lo}} to {{claim:field.f_sweep_hi}}. The value used was chosen as the
smallest that removes the defect, before the resulting fraction was known. Nor does it depend
much on the form of the constraint, which is the more searching test. The production form uses a
calendar-day minimum and gives {{claim:field.f_form_calendar}}. Replacing it with a centred
rolling twenty-four hour minimum gives {{claim:field.f_form_roll24}}, and doubling that window to
forty-eight hours gives {{claim:field.f_form_roll48}}. The answer is stable across constraint
forms that respect the daily structure of `B`, and drifts only when the window exceeds the
timescale on which `B` is defined.

The sweep and the constraint-form figures come from an independent reimplementation of the
constraint rather than from the production code path, because the original sweep left no
artefact. It reproduces the originally reported values closely enough that the conclusion is
unchanged, and the text above quotes the reimplementation because it is the version that can be
re-run.

This replaces an earlier estimate of about a quarter taken from source apportionment. The
constraint refutes that value rather than refining it, and the practical consequence for Kandy is
substantial: approximately half of the concentration over the basin is generated inside it, so an
intervention removing every local source would remove about half of the problem rather than a
quarter of it.

## 6.7 What this model is not

It contains no chemistry. There is no gas-phase mechanism, no aerosol thermodynamics, no
secondary formation and no deposition scheme beyond a bulk loss term in a layer that is not part
of the delivered field. Secondary aerosol enters only through the background and the anchor.

It does not resolve vertical structure. The field is a single layer.

Its spatial pattern is imposed rather than learned, and Chapter 8 reports what happened when that
decision was finally subjected to a pre-registered test.

And its emission proxy is a proxy. The surface sets only the shape of the local increment; the
level is carried by `T(t)`, which is pinned to total observed concentration from all sources.
A source that is spatially decoupled from the road network is therefore misplaced rather than
omitted, and Chapter 8 gives the measured consequence at a city where that happens.
