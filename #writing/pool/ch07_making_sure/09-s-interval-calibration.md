## Interval calibration {#s-interval-calibration}

An interval that is honest about its own uncertainty has to be checked against observations, not
merely constructed. The check available at Kandy is narrow, because the city has only two low-cost
sensors, but it is the check that exists. The figure below compares the delivered interval against
what those sensors recorded, hour by hour. What to look for is not simply whether the observations
fall inside the band, but where they fall when they land outside it. An interval that is too narrow
misses on both sides in roughly equal numbers. An interval that is correctly sized but wrongly
positioned misses almost entirely on one side, and that distinction decides whether the problem is
the width or the centring. The figure shows the delivered interval at the sensors.

{{fig:uncertainty}}

The interval is nominal at ninety per cent rather than guaranteed at it: conformal calibration
earns its coverage under exchangeability [@Vovk2005; @Angelopoulos2023], which strongly
dependent environmental series do not satisfy, so what follows is an empirical check and not a confirmation of a theoretical
property. The two corrections described below were fitted at the regulatory station, and the
sensors are scored after them. The delivered interval covers {{claim:kandy.cov90}} per cent of the
sensors' hours, close to nominal, but the misses lean to one side, {{claim:kandy.miss_below}} per
cent below against {{claim:kandy.miss_above}} per cent above, with a median offset of
{{claim:kandy.median_offset}} micrograms per cubic metre; removing each sensor's own offset raises
coverage to {{claim:kandy.cov90_recentred}} per cent ({{ref:s-comparing-areal-model-point}}). The
asymmetry points to a centring problem at these sensors. Its cause is not settled: it may be the
change of support of {{ref:ch-model-stops}}, or an upward level bias of the model at these points,
and {{ref:s-checks-kandy-carry-weight}} sets out the evidence on each side. The sensors cannot
distinguish the two, because they also calibrated the anchor.

The regulatory station ({{ref:s-cea-reference}}) does not settle the cause of the sensors' offset,
since it is not co-located with them, but it tests the interval against an instrument the anchor was
not fitted to beyond the station's own first thirty months. As first delivered, before the two
corrections, the interval contained {{claim:ceaiv0.held.coverage}} per cent of the station's
held-out hours, from July 2021 onwards. The misses fell on both sides, {{claim:ceaiv0.held.below}}
per cent below and {{claim:ceaiv0.held.above}} per cent above, around a median offset of only
{{claim:ceaiv0.held.offset}} micrograms per cubic metre, and removing that offset left coverage at
{{claim:ceaiv0.held.recentred}} per cent. Against a reference instrument the hourly interval was
therefore too narrow rather than misplaced: its half-widths would have had to grow by a factor of
{{claim:ceaiv0.held.k90}}. The misses followed the errors in the daily cycle: the station fell below
the interval in {{claim:ceaiv0.held.night.below}} per cent of night hours, where the first delivered
field's nights ran too high, and rose above it in {{claim:ceaiv0.held.morning.above}} per cent of
morning-peak hours and {{claim:ceaiv0.held.midday.above}} per cent of midday hours. Averaging over
three hours, which damps the instrument's own hour-to-hour noise, raised coverage only to
{{claim:ceaiv0.held.h3.coverage}} per cent, so the shortfall was not measurement noise. The one-sided
pattern at the low-cost sensors is therefore a property of those sensors, not of the interval.

Two corrections followed, both fitted on the station's hours from January 2019 to June 2021 and
checked on the later hours under rules written down before the check. The daily cycle was refitted
to the station's ({{ref:s-cea-reference}}), which on its own raised held-out coverage to
{{claim:iw.unwidened.held.coverage}} per cent. The interval was then widened by a factor of
{{claim:iw.k}} on the spread of the temporal anchor ({{ref:s-temporal-anchor}}). On the held-out hours
the delivered interval contains {{claim:ceaiv.held.coverage}} per cent, missing
{{claim:ceaiv.held.below}} per cent below and {{claim:ceaiv.held.above}} per cent above, and it
contains {{claim:ceaiv.held.daily.coverage}} per cent of daily means, a figure that averages hourly
quantiles and so overstates what a properly constructed daily interval would earn. The price is
width: the mean width of the hourly interval at the station grows from {{claim:ceaiv0.held.width}}
to {{claim:ceaiv.held.width}} micrograms per cubic metre. Part of what the factor absorbs is the
difference between a point and a kilometre cell, which
{{ref:s-external-identification-representativeness-error}} finds the model underestimates, so the
interval is now sized for a point like the station and is conservative for the mean of a cell. In
the extension years, whose level reads far below the station, coverage is
{{claim:ceaiv.ext.coverage}} per cent, with most misses above the interval: a width factor does not
repair a level error. The factor rests on one station in the city centre, and it is reported as such.

The interval is also incomplete. Its width comes from the anchor's conformal quantiles and the
spread of the local pattern, and the background enters through a fixed band. It omits the
uncertainty of the confinement strength, of the local fraction, of the emission proxy and of the
sensor calibration slope ({{ref:s-comparing-areal-model-point}}), so a coverage near nominal for
the anchor would still understate the uncertainty of the field.

The observation model's representativeness term, the error of comparing a point with a cell, is
estimated in the implementation from the field's own local variability, which is circular.
{{ref:s-external-identification-representativeness-error}} identifies it independently, from
instruments that share a model cell, and finds the model's estimate several times too small.
