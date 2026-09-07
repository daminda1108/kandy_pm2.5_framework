# Chapter 4. What there was to work with

Chapter 3 established that Kandy has no continuous measurement record. This chapter sets out what
it does have, what was obtained from elsewhere, and what was requested and never arrived. The
constraint that shapes everything after it is stated first, because it was a choice rather than
an accident.

## 4.1 A deliberate constraint on the inputs

**Nothing used in this work was collected for it.**

Every stream is either openly published or was obtained on request from an existing archive. No
instrument was deployed, no campaign was run, and no dataset was commissioned. That is a
limitation in the ordinary sense, and it was also the point. A method that requires bespoke
measurement cannot be applied to the cities that most need it, because those are precisely the
cities where bespoke measurement is unaffordable. A method built only from what is already
available can be applied anywhere, and the cost of that decision is visible in Chapter 8.

{{tbl:T4_1}}

The column that earns that table is the last one. A data inventory listing resolution and
coverage without stating what each stream cannot do is a catalogue, not an argument.

## 4.2 The streams, and what each one is actually good for

**Satellite aerosol retrieval** supplies a daily signal that correlates with column loading. It
is the only stream that observes the atmosphere over Kandy directly at useful frequency. Its
weaknesses are that it is absent under cloud, which in a monsoon climate is a substantial
fraction of days, and that it carries no diurnal information whatever, because the satellite
passes at a fixed local time.

A satellite-derived annual concentration surface supplies the level. It is a fusion product
and it is used here only as an annual anchor. Section 7.5 describes what happened when it was
used as though it were an independent observation, which it is not.

Reanalysis meteorology supplies wind, boundary-layer height, temperature and humidity at
hourly resolution [@Hersbach2020]. This is the workhorse of the temporal model and it is the
reason a sensorless tier is possible at all. Its limitation is one of scale: a valley
boundary layer fifteen kilometres across is not resolved by a driver whose grid is twice that.
What the driver supplies is the regional state, and the model's task is to map from that state
to a local response.

A global composition reanalysis supplies a chemical prior [@Keller2021]. It enters as a
feature rather than as a target, and Section 7.10 uses its speciation for an independent check.
It is itself a model at roughly twenty-five kilometres, so it can corroborate or contradict but
cannot validate.

Precipitation required a decision that is worth recording. The obvious choice, land-surface
reanalysis precipitation, was tested against a representative gauge and rejected: it delivers
approximately twice the gauge total at this site. Satellite precipitation radar lands within a
few per cent of the same gauge and is used instead. Where it is absent the field reports nothing
rather than falling back to the rejected product.

Static geography supplies terrain, roads, land cover, vegetation, night lights and
population. Individually each is a weak predictor. Collectively they are worth
{{claim:step.geography}} per cent on the ladder of Chapter 7, which is comparable to the first
local instrument, and they are free everywhere on Earth. Chapter 9 reports that land cover
measured over a coarse buffer is the strongest single spatial predictor in the entire set, which
was not expected.

The two local sensors are low-cost units at different elevations, one at roughly 460 metres
about six kilometres north of the city and one at roughly 738 metres on the southern slope. Both
sit on or near the valley floor, not on the ridge, and a metadata audit early in the
project found that both had been recorded at incorrect elevations for some months, which had
propagated into a description of them as highland sites. They are not.

## 4.3 The borrowed panel

The validation of Chapter 7 requires cities with dense monitoring, and Sri Lanka has none that
qualify. The panel is therefore assembled from two open archives covering
{{claim:frame.cities}} cities in {{claim:frame.countries}} countries.

{{fig:panel}}

Three properties of that panel constrain what Chapter 7 can conclude, and all three are stated
there as well as here.

It is not a random sample of cities. Cities enter it by having published dense monitoring, which
is correlated with income, with latitude and with the kind of institution that operates a
network.

Every city in it is a valley or a basin, selected for similarity to the target. That makes the
transfer more credible and it means the results are not established for coastal regimes.

And the association between instrument class and latitude band cannot be removed by sampling
more carefully, for the reason Chapter 2 gave: the population of candidate cities does not
contain a balanced draw.

## 4.4 What was requested and did not arrive

This section exists because the alternative is to present the constraint as though it were a
design decision throughout.

**The regulatory authority's Kandy record.** An hourly record covering particulate, gases and
full meteorology including a rain gauge, extending from 2019, with a known gap of about fifteen
months when the station could not be operated. Access was granted in principle for academic use.
It requires a formal request on institutional letterhead followed by a signed agreement, and the
agreement carries a condition that any manipulation of the data be notified and authorised in
advance. That condition needs clarifying with the issuing office, because bias correction, gap
handling and aggregation are ordinary analysis rather than manipulation, and a model that cannot
perform them cannot be built. The record was not obtained within the period of this work.

The reference monitor at Torrington Park. This instrument anchored the calibration of
published low-cost sensor records in the region and would have settled the level discrepancy of
Section 7.8 directly. It is no longer operating, so it is a provenance for other people's
records rather than a data route.

A national research organisation's regional stations. These supply the external check used in
Section 7.8, obtained through a published paper rather than directly. A direct request would
provide the regional background that Chapter 7 measures as the largest single gain on the
ladder, and Chapter 9 ranks it accordingly.

The university's own islandwide sensor network. Identified late and not pursued within this
work. It is the cheapest route of the four and it is internal.

## 4.5 Computational resources

The work runs on a single workstation with a consumer graphics processor, supplemented by a free
hosted notebook service for the neural network training described in Chapter 5. Total compute is
modest by the standards of the machine learning literature, and the reason is worth stating: the
binding constraint on this problem is the information content of the available observations, not
the capacity to fit a model to them. Chapter 5 describes several attempts that consumed
substantial computation and produced no usable result, and none of them would have been rescued
by more.

The satellite and geographic data were extracted through a cloud-hosted earth observation
platform, which matters practically. A decade ago the terrain, land cover, night lights and
population extraction described here would itself have been a project. It is now a few hours of
scripting, and that shift is a large part of why a thesis of this kind is feasible at an
undergraduate scale at all.

## 4.6 The construction that follows

{{dia:pipeline}}

The remainder of Part II describes how these streams are combined. The temporal anchor takes the
drivers and the satellite level and produces a basin-mean concentration for every hour. The
background term takes the same drivers and produces a regional contribution. The spatial pattern
takes the static geography and produces a unit-mean surface. Chapter 6 sets out the formulation
and Chapter 7 measures what each stream contributes.

The order in which those three are described is not the order in which they were built, and
Chapter 5 gives the actual sequence, which involved abandoning two complete architectures before
arriving at this one.
