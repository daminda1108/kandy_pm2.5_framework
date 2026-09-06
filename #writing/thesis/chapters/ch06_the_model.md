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
observations actually constrain. It separates the temporal anchor from the spatial redistribution,
so the two can be evaluated independently, which is what Chapter 7 exploits. And it bounds the
consequence of being wrong: an error in `P` is an error in **where** material sits, never in
**how much** of it there is.

**What the unit-mean condition does not do is identify `B`.** It is worth being exact, because the
stronger statement is easy to make and is false. Taking the spatial mean of the field gives
`T` whatever the background happens to be: for any admissible alternative `B'`, setting
`P' = (C − B') / (T − B')` yields a pattern that also has unit spatial mean, and reproduces the
same field. The gauge therefore identifies the anchor and pins the normalisation of the pattern;
it says nothing about how the anchor divides into a background and an increment. That division is
identified by the constraints of Section 6.6 and by the construction of `B` in Section 6.3, not by
the gauge, and the sensitivity of the resulting fraction to those choices is reported there rather
than assumed away.

One qualification belongs here rather than in a limitations list. The satellite anchor is exact,
in that the annual mean of `T` matches the reference product to four decimal places every year.
The delivered field nonetheless sits {{claim:gauge.drift_lo_pct}} to {{claim:gauge.drift_hi_pct}}
per cent above it, consistently and in the same direction. The cause is an accumulation across
build steps rather than a defect in the gauge: each step preserves the mean, but the unit-mean
pattern is recovered from an upstream field rather than from the anchor directly, and a small
positive offset accrues. The condition holds by construction and to within about half a per cent
in practice, and this thesis states it that way rather than as an exact identity.

### Why the background is allowed to be uniform

Taking `B(t)` uniform over the domain looks like a strong physical assumption and is mostly a
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

Section 7.10 supplies composition evidence from an independent direction: air classified by
arrival sector as continental is more secondary-rich, and therefore more aged, than air arriving
from the ocean. A background composed of aged air is what the construction requires.

The assumption is nonetheless the one a denser network would test first, and Section 7.2 is
explicit that the proxy standing in for `B` is the weakest link in the chain.

### Why an imposed pattern is not simply an arbitrary prior

If `P` were chosen freely it would carry no information and the conservation property would
merely make it harmless. Three things stop it being arbitrary, and the third matters most.

It is constructed from measured quantities rather than fitted parameters. The surface combines
an emission proxy built from the road network with a confinement term built from the digital
elevation model, and neither is tuned to concentration data in the city where it is applied.

It is falsifiable and has been scored. Across the ten cities of Section 7.7 the pattern's rank
against held-out monitors is reported rather than assumed, with a median of
{{claim:scorecard.spatial_rho_median}}.

**And it has been partly refuted, which an arbitrary prior cannot be.** Section 8.4 reports that
the dispersion step, which is the part of the construction that redistributes the emission
surface through terrain-steered flow, **lowers** rank from {{claim:r2.rho_emission_surface}} to
{{claim:r2.rho_with_atransport}}. A prior that cannot fail would not have produced that result,
and the appropriate response is Chapter 9's rather than a defence of the construction.

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
makes available. The interval is nominal at ninety per cent by construction and empirically
checked here, which is the distinction that matters: conformal calibration earns its coverage
under exchangeability, and hourly air quality in a monsoon climate is not exchangeable, so the
nominal level is a design target and the measured coverage is the evidence. It covers
{{claim:kandy.cov90}} per cent of
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

The argument that replaced it is short. Local sources emit continuously, and rain changes removal
rather than emission, so at an emitting location some locally generated material is present at
every hour. The decomposition's increment is then required to be non-negative, the background can
never reach the total, and **a background at or above the total is not an unusual hour but an
over-estimated background**. Since `B` is flat within a day, the constraint has a closed form: cap
each day at `(1 - F_min)` times that day's minimum hourly total.

**This is a non-negative local-contribution constraint, and it should be called that rather than a
physical theorem.** Continuous emission is a statement about sources; `T - B` is a statement about
a constructed decomposition, and the two are not the same object. Transport, mixing, deposition,
secondary formation and a background that is itself built rather than measured all sit between
them, so continuous emission does not by itself prove that this particular residual must be
positive in every hour. What it does is make a negative residual far more readily explained by an
over-estimated background than by a real state of the atmosphere, which is enough to justify the
constraint as a modelling choice. It is imposed on those grounds, and Section 6.6 reports how much
the resulting fraction moves when the choice is varied.

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

The forty-eight hour form is the one that moves, from {{claim:field.f_form_calendar}} to
{{claim:field.f_form_roll48}}, and it is reported rather than excluded as an outlier. That is a
change of about a tenth in relative terms and it is the honest upper end of the sensitivity. The
reason it drifts is structural: a window longer than a day takes minima across days on which `B`
itself differs, so it constrains a quantity the decomposition does not define. A reader who
rejects that reasoning should read the partition as spanning roughly
{{claim:field.f_sweep_lo}} to {{claim:field.f_form_roll48}} rather than as a point value.

### What the partition is, and what it is not

This replaces an earlier estimate of about a quarter taken from source apportionment, and the
constraint refutes that value rather than refining it. Three statements about the new number have
to be kept apart, because the strongest reading is not supported.

**It is a constrained decomposition, not an observed apportionment.** The constraint rules out
decompositions that are physically incoherent, given that local sources emit continuously. It
does not measure how much material comes from where. Filter-based source apportionment at Kandy
resolves soil, aged sea salt, vehicular, biomass-burning and industrial factors
[@Seneviratne2017], and none of those maps onto a two-way split. The defensible form of the claim
is that **under the stated background and minimum-increment assumptions, the constrained
decomposition assigns {{claim:partition.f}} of modelled concentration to the local increment.**

**Local increment is not the same as locally emitted primary material.** The model has no
chemistry, as Section 6.7 states. Precursors emitted inside the basin can form particulate mass
inside it, and material formed outside can arrive already aged. The increment is defined by
spatial structure and timing rather than by origin, so it contains locally formed secondary
aerosol and excludes regionally formed aerosol regardless of where the precursors came from.
Section 7.10 supplies the one chemical check the thesis has, and it also refuted the simplest
reading, that the local increment can be treated as fresh primary aerosol.

**The intervention statement therefore has to be weaker than the arithmetic suggests.** It is not
established that removing every local source would remove half the concentration, because a
share of the increment is secondary material whose precursors are not all local and whose
formation would not stop with the emissions this decomposition can see.

Withdrawing the claim leaves a reader with nothing, so Section 7.10 replaces it with a bound. The
locally emitted primary share is constrained from both directions by the local share and the
secondary share together, with no further assumption, and at Kandy it lies between
**{{claim:chem.intervention_lo}} and {{claim:chem.intervention_hi}} per cent** of concentration.
The lower figure responds immediately to local emission control. The upper figure equals the
whole local increment and requires every locally formed secondary particle to vanish with it,
which is why the withdrawn claim sat at the top of a range rather than in the middle of one.

That is the honest form of the statement, and it is more useful than either the withdrawn
version or silence: local action is worth substantially more than the retired quarter implied,
and its immediate effect is bounded well below half. A speciated measurement in the city is the
experiment that would narrow the range, and Chapter 9 lists it.

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
