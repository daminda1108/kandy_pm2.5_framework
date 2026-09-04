# 1. The problem: modelling where you cannot check

Most of the world's population breathes air that nobody measures. Ground monitoring is
concentrated where it was historically affordable [@Shaddick2020; @Martin2019], and the deficit
is not uniform: it is worst in exactly the places where concentrations are highest and where the
health burden per microgram falls on the largest populations. Fine particulate matter remains
among the largest environmental contributors to mortality worldwide [@Burnett2018;
@GBD2021Risk], and the estimates that establish that are themselves built on modelled surfaces
in most of the regions that dominate the total — so the quality of an unverifiable model is not
an academic matter but an input to a number that drives policy.

The response has been a generation of models that supply a field where instruments do not:
satellite–reanalysis fusions [@vanDonkelaar2021; @Hammer2020], land-use regressions [@Hoek2008],
chemical transport and dispersion models [@Denby2020; @Cimorelli2005], global aerosol
reanalyses [@Buchard2017; @Provencal2017], and increasingly machine-learned combinations of all
three [@Di2019; @Reid2015; @Wei2023]. Between them they now cover the globe at kilometre scale
and daily resolution, and they are genuinely good.

The difficulty is not that they are inaccurate. It is that **in the places they are built for,
there is no way to find out.** A model trained where monitors are dense and applied where they
are absent is validated on one population and used on another. The literature knows this and
reports out-of-sample statistics diligently, but the out-of-sample test is almost always
conducted where monitors exist, which is the wrong regime by construction. The transfer that
matters — from dense to sparse — is the one that cannot be scored.

## 1.1 Complex terrain is where this bites hardest

Valleys and basins concentrate the problem rather than merely instantiating it. Nocturnal
inversions, cold-air pooling and the diurnal reversal of slope flows can hold a shallow polluted
layer over a city for days, so concentrations depend on stability and drainage geometry as much
as on emissions [@Whiteman2000; @Chemel2016]. Three consequences follow for anyone modelling
such a place. Concentrations vary sharply over distances well below the resolution of any global
product. The relationship between emission and concentration is mediated by a boundary layer
that a coarse driver represents only in the aggregate. And the monitors that do exist are sited
on valley floors, for the same reasons that people live there, so a network in a basin samples
one horizon of a strongly stratified field and cannot constrain the rest of it.

This is also the regime with the least monitoring. That conjunction — the hardest physics and
the thinnest observation — is what motivates the approach taken here, and it is the reason the
demonstration city is a valley city rather than a convenient one.

## 1.2 The question that is not usually asked

Faced with an unmonitored city, a ministry has a decision to make, and it is not "which model is
most accurate". It is: **what would I have to buy to trust an answer here, and in what order?**
A reference monitor costs tens of thousands of dollars and years of maintenance. A pair of
low-cost sensors costs a few hundred, at the price of a calibration problem of its own
[@Morawska2018]. A rural background station serves no constituency and is politically the
hardest thing to fund. These are not interchangeable, and the literature offers remarkably
little that would let a ministry rank them.

The reason is structural rather than an oversight. Answering the question requires knowing what
a model would produce *without* a given observation, and for most model families that is not a
well-posed question: removing an input and refitting produces a different model, so the
difference between the two confounds information loss with model change. Hybrid
physics–machine-learning approaches [@Raissi2019] tighten the physical constraints but do not
change this, because the constraint is not about physics — it is about whether the same object
exists at two levels of information. The quantity a ministry needs is simply not recoverable
from the models the field currently builds.

## 1.3 What this paper does

We formulate a model in which the question **is** well-posed, and then answer it.

The formulation (§2) is an additive separation of a spatially uniform regional background from a
locally generated increment — a scale separation with long precedent in air-quality time-series
analysis [@Rao1994; @Eskridge1997] — placed inside an explicit observation operator and an
explicit information budget. The budget declares, per tier, which observation streams the model
is entitled to use, and guarantees that a lower tier is recoverable **bit-exactly** from a higher
one when a stream is withheld. Withholding information becomes a controlled operation rather
than a refit. That property — not the physics, which is modest, nor the machine learning, which
is standard — is the contribution, because it is what turns an ablation into a measurement.

We then run the measurement (§3, §4) across {{claim:frame.cities}} cities in 32 countries and
{{claim:frame.city_days}} city-days, with gates registered before scoring. The results are not
what the field's intuition would suggest. Freely available static geography is worth
{{claim:step.geography}}%, comparable to what the first local instrument buys. The second
through eighth monitors are worth {{claim:step.bud1_bud2}}% — indistinguishable from nothing. A
regional background station is worth {{claim:step.bud2_bud3}}%, the largest single gain we
measure, and it is the rung most programmes never build. And the recommendation **inverts by
latitude band**, so the pooled answer is the wrong answer for the tropics — including for the
city this paper demonstrates on.

§5 reports where the model stops. This is not a caveats section: the limit is located, measured,
and shown to be a limit of *definition* rather than of data, since most within-city variation is
sub-grid and a 1 km field therefore cannot place it however finely the physics is run. §6 runs
the whole apparatus at a city with two low-cost sensors and no reference monitor, and checks it
against records that played no part in building it. §7 states what the evidence forbids.

## 1.4 The demonstration city

Sri Lanka has no dense regulatory network, a documented epidemiological signal [@Nandasena2010],
and a research literature on Kandy that is real but thin — morphological and mineralogical
characterisation of the city's particulate [@Samaradiwakara2021], deposition chemistry
[@Dharmapriya2024], a single published year of speciated measurement [@Senarathna2024;
@Ileperuma2020], and recent machine-learning work on Sri Lankan air quality that is trained
where the monitors are [@Mampitiya2023]. The city is a steep valley of about 400,000 people with
two low-cost sensors and no operating reference monitor.

It is, in other words, exactly the configuration this paper is about, and we treat it as a
demonstration rather than a validation throughout — a distinction we maintain even where it
weakens a claim we would prefer to make.

## 1.5 What we do not claim

Stated here rather than left for a referee to extract.

We do not claim a validated neighbourhood-scale map. We do not claim the model captures
atmospheric chemistry — it has none. We do not claim the spatial nulls in the literature,
including our own, isolate an information limit; §5.5 shows they share a defect and §5.5 also
shows what they had the power to detect. We do not claim the framework is validated for coastal
regimes, since every city in the panel is a valley or basin. We do not present the transport
layer as an accuracy gain, because §5.4 shows it is not one. And we do not claim the two local
sensors validate anything, because the model is calibrated to them.

What we do claim is narrow: **a formulation whose information budget is declared and whose
degradation between tiers is exact, and a measurement, made on that formulation, of what each
increment of observation is worth.**

---

## Drafting notes, to remove before submission

- "32 countries" still needs a claim token; it is currently hardcoded.
- Citation weight is now front-loaded here as intended: the introduction carries the model-family
  survey, the complex-terrain case, and the Sri Lankan literature.
- Check §1.3's forward references against final section numbering before build.
