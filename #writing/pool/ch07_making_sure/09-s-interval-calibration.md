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

The pattern points to a centring problem at these sensors rather than a width problem, but it is a
diagnostic, not a calibration of the interval: the re-centred coverage is measured on the two
sensors that also calibrated the anchor, so it cannot show that the width is right for the basin
field, and the interval omits uncertainties listed below. The cause of the offset is not settled. It may
be the change of support of {{ref:ch-model-stops}}, in which case the interval may be adequate for
the areal quantity it describes. It may instead be an upward level bias of the model at these points,
for which the constant-humidity correction of the sensor record is one candidate mechanism, and
{{ref:s-checks-kandy-carry-weight}} sets out the evidence on each side. The check at the
sensors cannot distinguish the two, because the sensors that score the interval are the same
sensors that calibrated the anchor.

The regulatory station ({{ref:s-cea-reference}}) does not settle the cause of the sensors' offset,
since it is not co-located with them, but it does test the interval against an instrument the
anchor was not fitted to. Only the level factor was estimated on the station, from its days before
mid-2021, so the later days are the independent test. On those held-out hours the interval covers
{{claim:ceaiv.held.coverage}} per cent, and the misses fall on both sides, {{claim:ceaiv.held.below}}
per cent below and {{claim:ceaiv.held.above}} per cent above, around a median offset of only
{{claim:ceaiv.held.offset}} micrograms per cubic metre; removing that offset leaves coverage at
{{claim:ceaiv.held.recentred}} per cent. Against a reference instrument the hourly interval is
therefore too narrow rather than misplaced: its half-widths would have to grow by a factor of
{{claim:ceaiv.held.k90}} to contain ninety per cent of the hours. The misses follow the field's
errors in the daily cycle. The station falls below the interval in {{claim:ceaiv.held.night.below}}
per cent of night hours, where the field's nights run too high, and rises above it in
{{claim:ceaiv.held.morning.above}} per cent of morning-peak hours and {{claim:ceaiv.held.midday.above}}
per cent of midday hours; coverage is lowest in the south-west monsoon months
({{claim:ceaiv.held.JJA.coverage}} per cent). Averaging both series over three hours, which damps the
instrument's own hour-to-hour noise, raises coverage only to {{claim:ceaiv.held.h3.coverage}} per cent,
so the shortfall is not measurement noise. Part of it is the difference between a point and a
kilometre cell, which the interval does not carry and which
{{ref:s-external-identification-representativeness-error}} finds the model underestimates; this check
cannot separate that part from error in the cycle itself. For daily means the interval does better,
containing {{claim:ceaiv.held.daily.coverage}} per cent of held-out days, although that figure averages
hourly quantiles and so overstates what a properly constructed daily interval would earn. Over the
calibration years the hourly coverage is {{claim:ceaiv.cal.coverage}} per cent, and in the extension
years, whose level reads far below the station, it falls to {{claim:ceaiv.ext.coverage}} per cent with
almost every miss above the interval. The one-sided pattern at the low-cost sensors is therefore a
property of those sensors, not of the interval: at a reference instrument the hourly interval is too
narrow, and close to nominal only for daily means. This check was made after the other validation
results, with its reading rules written down before it was scored.

The interval is also incomplete. Its width comes from the anchor's conformal quantiles and the
spread of the local pattern, and the background enters through a fixed band. It omits the
uncertainty of the confinement strength, of the local fraction, of the emission proxy and of the
sensor calibration slope ({{ref:s-comparing-areal-model-point}}), so a coverage near nominal for
the anchor would still understate the uncertainty of the field.

The observation model's representativeness term, the error of comparing a point with a cell, is
estimated in the implementation from the field's own local variability, which is circular.
{{ref:s-external-identification-representativeness-error}} identifies it independently, from
instruments that share a model cell, and finds the model's estimate several times too small.
