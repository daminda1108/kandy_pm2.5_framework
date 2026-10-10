## Registered robustness tests {#s-registered-robustness}

A confirmed verdict could still be a property of one choice the design happened to make: the
sensorless rung it was measured against, the learner that built that rung, or the cap on the number
of stations taken from each city. Each of these was tested by a separate registration, each lodged
before its own test was run, with the confirmation's code and cities held fixed and
one choice changed. {{fig:robustness}} gathers the results. Every directional verdict survives every
test, with one exception under one learner that {{ref:s-dependence-estimator}} reports. All of these
tests share the construction of {{ref:s-rungs-how-each-uses}}, so they show that the registered
verdicts are robust, not that the ordering they describe is a property of the observations.

{{fig:robustness}}

### A richer sensorless rung {#s-robustness-richer-baseline}

The first test asks whether the first stations are worth something only because the sensorless
rung is weak [OSF b379r]. Adding a reanalysis PM2.5 forecast, satellite nitrogen dioxide, active
fires, satellite precipitation, terrain and day of week to the sensorless rung reduces its error by
{{claim:v2.rich.bud0_gain.median}} per cent [{{claim:v2.rich.bud0_gain.lo}},
{{claim:v2.rich.bud0_gain.hi}}]. Every confirmed verdict holds on top of it. The registered prediction
that the first-station gain would shrink was refuted: paired within city, it did not measurably
change. The new streams improve the free estimate in ways the first recalibration does not duplicate.

### Full station networks {#s-robustness-full-networks}

The second test removes the cap of twelve stations per city, which had left one or two stations for
the background rung in many cities [OSF mhgna]. With every station each network holds, the
confirmation is scored on seventy-five cities with a median of seventeen stations. The first two
stations reduce error by {{claim:v2.fullnet.N1.median}} per cent [{{claim:v2.fullnet.N1.lo}},
{{claim:v2.fullnet.N1.hi}}]. Stations three to six add {{claim:v2.fullnet.N2.median}} points
[{{claim:v2.fullnet.N2.lo}}, {{claim:v2.fullnet.N2.hi}}], inside the registered bound. The background
adds {{claim:v2.fullnet.N3.median}} per cent [{{claim:v2.fullnet.N3.lo}}, {{claim:v2.fullnet.N3.hi}}],
and as constructed its lead over the first two stations is {{claim:v2.fullnet.N4.median}} points
[{{claim:v2.fullnet.N4.lo}}, {{claim:v2.fullnet.N4.hi}}] on daily error and
{{claim:v2.fullnet.N5.median}} [{{claim:v2.fullnet.N5.lo}}, {{claim:v2.fullnet.N5.hi}}] on exceedances.
The background verdicts were therefore not an artefact of a background built from one or two
stations.

One complication belongs with this test. The cap, re-applied to records retrieved later, did not
reproduce the registered run exactly, because the public archive had since added hourly values
inside the scored windows of seven cities. The sensorless rung is fitted across all cities, so those
values moved every city's effects slightly. Measured against the re-applied cap rather than the
registered run, the change in the ordering is not distinguishable from zero. A reproduction on data
retrieved again is therefore reported but never used as a gate; the parity gate runs on the stored
files.

### Precipitation, a driver admitted and never used {#s-driver-admitted-never-used}

The driver set carries temperature, wind, boundary-layer height and two day-of-year terms, so wet
removal appeared to be absent from its meteorology. On inspection a reanalysis daily precipitation
total was already in the scored frame, pulled and merged and never referenced, because it was not in
the feature list. That is the shape of the defect described in {{ref:s-information-budget}}:
a rung holding a driver its budget admits, unused.

It was registered and tested on the discovery ladder [OSF z89kt], with both arms fitted on one fixed
set of {{claim:precip.cities_scored}} cities, identical seed and machinery, differing in one feature.
Adding precipitation changes the sensorless rung by {{claim:precip.p1}} per cent
[{{claim:precip.p1_lo}}, {{claim:precip.p1_hi}}], which is nothing, and the first-station gain moves by
{{claim:precip.first2.paired}} points paired within city. The unused driver was unused harmlessly. Of
the five registered predictions, recomputed paired within city, one held, three were refuted and one
could not be adjudicated; the prediction that the background would remain the largest single gain is
among those refuted, because the support it had came from a difference of medians. The test
establishes only that an eleven-kilometre reanalysis daily rainfall total does not improve daily
city-mean prediction on this panel. It is not evidence that wet removal does not matter, and a gauge
network or a higher-resolution product remains untested. The registered rich-baseline test above
includes satellite precipitation among the streams it adds.
