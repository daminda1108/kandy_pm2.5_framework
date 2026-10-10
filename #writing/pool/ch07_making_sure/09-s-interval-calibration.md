## Interval calibration {#s-interval-calibration}

An interval that is honest about its own uncertainty has to be checked against observations, not
merely constructed. The check available at Kandy is narrow, because the city has only two low-cost
sensors, but it is the check that exists. The figure below compares the delivered interval against
what those sensors recorded, hour by hour. What to look for is not simply whether the observations
fall inside the band, but where they fall when they land outside it. An interval that is too narrow
misses on both sides in roughly equal numbers. An interval that is correctly sized but wrongly
positioned misses almost entirely on one side, and that distinction decides whether the problem is
the width or the centring. The figure shows the second pattern.

{{fig:uncertainty}}

The interval is nominal at ninety per cent rather than guaranteed at it: conformal calibration
earns its coverage under exchangeability [@Vovk2005; @Angelopoulos2023], which strongly
dependent environmental series do not satisfy, so what follows is an empirical check and not a confirmation of a theoretical
property. It covers {{claim:kandy.cov90}} per cent of observations at
the two sensors, which read alone suggests the intervals are too narrow. {{ref:s-comparing-areal-model-point}} gave the
diagnosis: the misses are one-sided, {{claim:kandy.miss_below}} per cent below against
{{claim:kandy.miss_above}} per cent above, with a median offset of
{{claim:kandy.median_offset}} micrograms per cubic metre. Removing each sensor's own offset
restores coverage to {{claim:kandy.cov90_recentred}} per cent.

The width is about right and the centring is not. The cause of the offset is not settled. It may
be the change of support of {{ref:ch-model-stops}}, in which case the interval is correct for the
areal quantity it describes. It may instead be an upward level bias of the model at these points,
for which the constant-humidity correction of the sensor record is one candidate mechanism, and
{{ref:s-checks-kandy-carry-weight}} sets out the evidence on each side. The check cannot
distinguish the two, because the sensors that score the interval are the same sensors that
calibrated the anchor; a co-located reference monitor would.

The interval is also incomplete. Its width comes from the anchor's conformal quantiles and the
spread of the local pattern, and the background enters through a fixed band. It omits the
uncertainty of the confinement strength, of the local fraction, of the emission proxy and of the
sensor calibration slope ({{ref:s-comparing-areal-model-point}}), so a coverage near nominal for
the anchor would still understate the uncertainty of the field.

The observation model's representativeness term, the error of comparing a point with a cell, is
estimated in the implementation from the field's own local variability, which is circular.
{{ref:s-external-identification-representativeness-error}} identifies it independently, from
instruments that share a model cell, and finds the model's estimate several times too small.
