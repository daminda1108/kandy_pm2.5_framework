## Excluded processes and known limits {#s-excluded-processes-known-limits}

It contains no chemistry. There is no gas-phase mechanism, no aerosol thermodynamics, no
secondary formation and no deposition scheme beyond a bulk loss term in a layer that is not part
of the delivered field. Secondary aerosol enters only through the background and the anchor.

It does not resolve vertical structure. The field is a single layer.

Its spatial pattern is imposed rather than learned, and {{ref:s-six-negative-results-their}} reports what happened when that
decision was finally subjected to a pre-registered test.

And its emission proxy is a proxy. The surface sets only the shape of the local increment; the
level is carried by *T*(*t*), which is pinned to total observed concentration from all sources.
A source that is spatially decoupled from the road network is therefore misplaced rather than
omitted, and {{ref:ch-model-stops}} gives the measured consequence at a city where that happens.

### Limits of the Kandy sensor record {#s-limits-kandy-sensor-record}

The skill of *T*(*t*) itself is modest at the hourly scale. The deployed anchor uses no measured
concentration as an input, because it must predict the hours that no sensor observed, and scored by
leaving out one month of one sensor at a time it reaches a coefficient of determination of
{{claim:v2.tanchor.lagfree.r2}} on hourly values, with a root mean square error of
{{claim:v2.tanchor.lagfree.rmse}} micrograms per cubic metre and a coverage of
{{claim:v2.tanchor.lagfree.cov90}} for its nominal ninety per cent interval before the conformal correction.
A variant that also uses the concentrations measured in earlier hours reaches
{{claim:v2.tanchor.lagged_blend.r2}}, but that variant is a short-range nowcaster rather than a
reconstruction, and simple persistence of the previous hour does better still, so its score is not
evidence for *T*(*t*). Most of the anchor's skill lies in the daily and seasonal variation that the
validation of the following chapter tests across cities.

Three further limits concern the low-cost sensor record that shapes *T*(*t*), and each was
identified by an external review of the chain.

**The humidity correction uses a constant relative humidity.** The sensors are corrected with the
Barkjohn equation [@Barkjohn2021], whose humidity term was evaluated at a fixed relative humidity
of eighty per cent rather than at the hourly value. Over-reading by an optical sensor follows the
humidity cycle, which at Kandy is high at night and in the early morning and lowest in the
afternoon, so a constant term leaves part of that cycle in the corrected record, and the
sharpening step then imposes it on *T*(*t*). Recomputing the correction with hourly reanalysis
humidity lowers the ratio of the morning peak to the midday level of the normalised diurnal
cycle from {{claim:v2.rh.constant_rh80.peak_to_trough}} to
{{claim:v2.rh.barkjohn_hourly_rh.peak_to_trough}}, about a tenth less swing. A full hygroscopic growth correction applied on top inverts the cycle, which appears physically
implausible for a valley whose diurnal cycle is set by the boundary layer. These are alternative
correction scenarios, and neither is validated against a co-located reference instrument; judging
one of them implausible does not make the other two a bound on the true shape. The shipped field
keeps the constant-humidity correction, and {{ref:s-rh-scenario}} carries the hourly correction
through the delivered series as an alternative to show which conclusions depend on the choice.
Because the local fraction is a function of the diurnal amplitude of *T*
({{ref:s-partition-constraint-rather-than}}), the choice reaches the partition as well, though only
slightly.

**The sensor record is used three times.** The same two sensors train the anchor, set the width of
its conformal interval and supply the diurnal and seasonal profile to which it is sharpened. The
van Donkelaar surface sets both the annual level and the background. Agreement between the model
and either source is therefore calibration, not validation, and {{ref:s-checks-kandy-carry-weight}}
separates these shared inputs from the records that are independent of them.

**The sharpening step makes two simplifying assumptions.** It treats the hour-of-day and
month-of-year factors as independent, so a diurnal cycle whose shape changes with the season is
represented by one shape scaled by month. And it pools a valley sensor with a ridge sensor at
different elevations into one profile, although the two need not share a diurnal shape.
