## Three confounds the pooled numbers hid {#s-three-confounds-pooled-numbers}

Each of the first two was caught by a gate declared before the run and not by review, and each
would otherwise have reached print. The third cannot be removed by any design available to this
thesis.

**Country crossed with latitude.** A minimum-cost sampling design drew the entire mid-latitude
arm of the discovery panel from a single national network, aliasing band with network so completely
that no band-stratified result could have been interpreted. It was corrected by a registered
amendment before any scoring took place, which is the only reason it appears here as a
methodological note rather than as a retraction. The confirmation panel caps the number of cities
per country for the same reason.

**Driver completeness crossed with band.** Boundary-layer height coverage is uneven across bands,
so the first version of the ladder was re-run without it. The first rung moved from
{{claim:confound.blh.with_blh_step1}} to {{claim:confound.blh.without_blh_step1}} per cent, a shift of
{{claim:confound.blh.delta}} percentage points, which bounds what the uneven coverage can be doing.
The redesigned ladder checks the coverage of every stream over each frame's own date span before
fitting, so a driver that is present in name and missing in fact now refuses rather than scores.

**Instrument class crossed with band.** Most of the deep-tropical cities in the panel are monitored
by low-cost sensors, while most cities in the other bands are monitored by regulatory reference
networks. In the discovery panel as a whole, thirty-one cities are dominated by reference monitors
and sixteen by low-cost sensors; an earlier count, which classed the Chinese national network as
low-cost, had reported the split the other way round. The confirmation panel is more regulatory
still, with sixty-three of its seventy-six cities dominated by reference monitors. This confound
cannot be sampled away, for the reason {{ref:ch-kandy-setting-record-stakes}} gave.

It limits any band result, and it deserves more than a note. Low-cost sensor response depends on
humidity, aerosol composition, sensor age and the duration and design of the calibration, and there
is no universal calibration procedure that removes this [@Zhang2025]. A band that is mostly low-cost
is therefore not only a different climate regime, it is a different measurement regime, with a
different error structure in both the fitting data and the held-out target, and low-cost values
enter the ladder as reported, without a city-specific calibration. There is a named route by which
the confound could operate. [@Senarathna2026] calibrated low-cost sensors against reference monitors
in two Sri Lankan climatic zones and found that a calibration fitted in the wet season, applied to
dry-season data, produces a mean absolute percentage error of 26.57 per cent. Seasonal calibration
drift of that size, in a group of cities dominated by low-cost sensors, is a concrete mechanism by
which part of a band difference could be instrument behaviour rather than atmosphere.

With the deep-tropical comparison retracted ({{ref:s-recommendation-inverts-tropics}}), the confound
no longer has a band result to qualify, and its remaining consequence is for transfer. Kandy is
monitored only by low-cost sensors and the confirmed population is mostly reference networks. The
like-for-like re-analysis finds that the kind of station makes no resolvable difference once
readings are used alike ({{ref:s-like-for-like}}), but low-cost and reference stations were not
separated in that comparison, so whether a low-cost reading used daily is worth as much as a
reference reading used daily is not measured here. It is one reason the main text treats making one
Kandy station reference grade as a question of measurement design, settled by co-location, rather
than as a rung of the ladder.
