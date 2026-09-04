# Chapter 3. What is already known about Kandy's air

Kandy is not unmeasured. It is measured in a particular way, and the shape of that measurement
record determines what a model can and cannot be checked against. This chapter sets out what
each study established, then states what none of them could, then asks what recent developments
in computing actually offer against that gap.

## 3.1 Two decades of measurement

{{tbl:T3_1}}

Read as a body of work, the record has a clear structure. Every study is either a **point**, a
**campaign**, or a **national surface trained elsewhere**, and each of those three forms answers
a different question from the one a city needs answered.

The earliest of the studies is also the most useful for the argument of this thesis. Abeyratne
and Ileperuma measured sulphur dioxide, nitrogen dioxide and ozone at fixed sites and binned
them by monsoon [@Abeyratne2006]. They found the maximum in the north-east monsoon rather than
in the south-west. That matters because Sri Lanka's own industrial and urban sources lie to the
south-west of Kandy, so a domestic-source explanation predicts the opposite ordering. The result
is a spatial falsification test pointing at long-range transport, conducted in a different decade
from any evidence gathered in this thesis and on different pollutants, and Chapter 7 returns to
it as external corroboration for the decomposition.

The roadside survey of Elangasinghe and Shanthini is the measurement that sets the spatial
problem. Twenty-five sites across the city, three hours at each, with traffic
counts recorded alongside. Inside a single botanical garden the concentration fell from 110 to 4
micrograms per cubic metre over three hundred metres, and across the survey the correlation with
traffic intensity reached an R-squared of 0.82 [@Elangasinghe2008]. The observed spread across the whole survey is
{{claim:spatial.obs_spread}} times.

{{fig:transect}}

Chapter 8 is largely an attempt to explain that figure, and the explanation turns out not to be
the obvious one.

The source apportionment of Seneviratne and colleagues is the study that most changed this
project's own claims. Applying positive matrix factorisation to speciated
samples at Katugastota, they attribute 7.6 per cent of fine particulate mass to traffic and 14.1
per cent to biomass burning [@Seneviratne2017]. For most of this project's history the emission surface was
justified by a statement that Kandy's particulate is approximately ninety per cent vehicular,
which the apportionment refutes as a statement about mass. Section 5.7 describes how that error
persisted and what it cost.

More recent work has supplied the first independent checks. Nirmani and colleagues published
daily concentrations obtained from the National Building Research Organisation for 2021 and 2022,
at 360 days in each year [@Nirmani2025]. Dhammapala published a reference-anchored record that
allows a low-cost sensor calibration to be checked [@Dhammapala2022]. Attanayake and colleagues
built a machine-learned surface for Sri Lanka [@Attanayake2025]. Chapter 7 sets the model against
the first two of these, and they are the only genuinely external tests it has.

## 3.2 The gap, stated as a list

None of the studies above delivers a continuous field over the city. More precisely, taken
together they cannot supply the following.

**A concentration at an arbitrary location.** Every measurement is at a site somebody chose,
and the sites were chosen either for contrast, as in the roadside survey, or for institutional
convenience, as with the fixed stations. Neither sampling design supports interpolation to a
location nobody sampled.

**A continuous record.** The campaigns lasted hours. The longest published record is two years
of daily means at one location. Nothing supports a statement about a particular hour on a
particular day, which is the resolution at which exposure actually varies and at which an
episode would need to be recognised.

**A separation of local from regional.** The single most decision-relevant quantity is the split
between what Kandy generates and what arrives from outside it, and no measurement at one point
can separate the two. The monsoon result of Abeyratne and Ileperuma is suggestive, but it
concerns gases rather than particulate mass and it establishes a seasonal pattern rather than a
partition.

**Anything at all after the instrument stopped.** The reference monitor that anchored the
published calibrations is no longer operating. A record that ends is not a record a decision can
be based on today.

## 3.3 What computation offers, and what it does not

The response of the last decade to gaps of this kind has been machine learning applied to
satellite and reanalysis data, and the results have been substantial. Global surfaces at
kilometre scale and daily resolution now exist [@vanDonkelaar2021; @Hammer2020; @Wei2023], they
perform well where they can be tested, and they were not achievable by any earlier method.

Three things about that development are worth stating precisely, because this thesis relies on
one of them and declines the other two.

**What learning genuinely adds is the ability to exploit weak, numerous and mutually redundant
predictors.** Satellite aerosol retrievals, reanalysis meteorology, terrain, road networks,
population and night lights each carry a small amount of information about concentration, and
none of them individually supports a useful prediction. Combining sixty such predictors is a
task that regression handles badly and that modern non-linear estimators handle well. Chapter 7
measures this directly and finds that the choice of estimator matters more than expected: on the
sensorless tier a linear model collapses, and reports the value of a monitor as roughly four
times what a well-specified non-linear model reports.

**What learning does not add is the ability to see what the predictors do not encode.** This is
the constraint that Chapter 8 turns into a measurement. A model can only redistribute the
information present in its inputs, and if the spatial structure of a city is not encoded in any
globally available covariate, no architecture recovers it. Chapter 5 records five separate
attempts to find such structure and Chapter 8 records a sixth, pre-registered with a detection
limit stated in advance.

**And what learning cannot do at all is validate itself in a city with no monitors.** This is
Chapter 1's argument restated at the level of method. A more capable model does not relieve the
problem that its capability cannot be assessed where it is used. If anything it worsens it,
because a more capable model produces more plausible output, and plausibility is precisely what
cannot be relied upon in the absence of a check.

The approach taken in this thesis therefore uses machine learning for the part of the problem it
is good at, which is the temporal behaviour of a city-mean concentration from many weak
predictors, and it declines to use learning for the part where no check is available. The
spatial pattern is imposed from physical reasoning and declared as an assumption rather than
fitted, and Chapter 8 reports what happened when that decision was finally tested.
