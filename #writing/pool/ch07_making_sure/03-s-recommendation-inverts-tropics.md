## The recommendation inverts in the tropics {#s-recommendation-inverts-tropics}

The pooled table is misleading if read as advice, and {{tbl:T7_2}} is the finding.

One feature of that table has to be read before its numbers, because it looks like an error and
is not. **Its city column sums to {{claim:frame.bands}} and the panel has
{{claim:frame.cities}}.** The difference is {{claim:frame.unbanded}} cities drawn from a single
national network, which are scored in every pooled result in {{this:ch-validation-without-local-ground}} and carry no latitude
band, so they cannot appear in a band-stratified row. Excluding them from the stratification is
deliberate. Assigning them a band would place a large block of cities from one country and one
network into one cell, which is the confound a registered amendment was written to remove, and
{{ref:s-three-confounds-pooled-numbers}} gives that history.

{{tbl:T7_2}}

Stratified by latitude band, the ordering reverses in the band Kandy belongs to: local sensors
buy {{claim:band.deep_tropical.step_bud0c_bud1}} per cent there against
{{claim:band.deep_tropical.step_bud2_bud3}} per cent for the regional background, which is the
opposite of the pooled result. A programme following the pooled recommendation in Colombo or
Kampala would buy the wrong instrument first.

That inversion strengthened when the satellite stream was replaced with one of clean provenance,
which {{ref:s-effect-monitor-trained-covariate}} describes. On the corrected stream the two local sensors buy
{{claim:maiac.deep_tropical_first2}} per cent in Kandy's band against
{{claim:maiac.deep_tropical_background}} for the background, a local advantage of
{{claim:maiac.deep_tropical_local_advantage}} times.

### The inversion under a paired interval {#s-inversion-under-paired-interval}

A median of thirteen cities is a thin basis for a procurement recommendation, and the difference
between two medians hides whether the same cities drive both. The comparison was therefore made
**paired within each city** and bootstrapped over cities, since days within a city are not
independent and the panel's true unit here is the city.

| satellite stream | advantage of two sensors over a background | cities favouring sensors |
|---|---:|---:|
| the fused product | {{claim:inv.ghap.median}} points, from {{claim:inv.ghap.lo}} to {{claim:inv.ghap.hi}} | {{claim:inv.ghap.frac_cities}} per cent |
| the raw retrieval | {{claim:inv.maiac.median}} points, from {{claim:inv.maiac.lo}} to {{claim:inv.maiac.hi}} | {{claim:inv.maiac.frac_cities}} per cent |

**On the fused product the inversion does not survive.** The interval spans zero and the sensors
win in barely half the cities, which is a coin flip. Read alone, that version of the result would
not support a recommendation, and an earlier version of this work stated it as though it did.

On the raw retrieval it does. The interval excludes zero and the sensors win in
{{claim:inv.maiac.frac_cities}} per cent of the band. This is the version the recommendation
rests on.

The two rows are the same thirteen cities and the same procedure, differing only in the satellite
stream, which makes this the sharpest consequence of {{ref:s-effect-monitor-trained-covariate}} anywhere in the thesis. **The
contaminated covariate did not merely shift the numbers; it destroyed the significance of the
finding that matters most for the demonstration city.** A monitor-trained product understates
what a monitor is worth, and in the deep tropics it understated it enough to hide the inversion
entirely.

Two limits stay attached. The band holds thirteen cities and the interval is correspondingly
wide, running to {{claim:inv.maiac.hi}} points at the upper end. And the pairing test was not
pre-registered, so it is reported as an analysis performed after the result was known.

The reversal is not a curiosity. It means the recommendation this thesis is most likely to be
quoted for is the wrong recommendation for the city it was built for, and a reader who takes the
pooled row without the band row will act on it.

**Latitude is a label here, not a mechanism, and the distinction is not pedantic.** The statement
the evidence supports is this one: *the available panel supports a deep-tropical ordering in which
local observations outperform the background proxy, and how far that difference reflects the
atmosphere rather than the instruments used there remains unresolved.* What the measurement
establishes is that cities sorted into these bands differ in the ordering. That is an empirical
difference between groups defined by latitude, and nothing more. It does not establish that
latitude causes the difference, and nothing in this design could.

Band travels with at least six other things. The first is instrument class, which {{ref:s-three-confounds-pooled-numbers}}
shows differs by a factor of {{claim:confound.deep_tropical_lcs_pct}} against
{{claim:confound.other_bands_lcs_pct}} per cent low-cost units. The others are network density and
design, driver completeness, the seasonal structure of the meteorology, the source mix, and the
institutional history that decides which cities publish data at all.

A mechanism can be proposed, and the honest status of the proposal is that it is consistent with
the data rather than tested by it. In the deep tropics the seasonal cycle of the regional
background is weak, so a background series adds little that a model without sensors has not already
taken from reanalysis and geography. In the temperate bands a strong winter accumulation regime
makes the same series carry a great deal. If that is right, the
operative variable is the amplitude of the regional seasonal cycle and latitude is standing in
for it. Testing it would require sorting cities by that amplitude directly and checking whether
the ordering follows the amplitude or the latitude, which is one of the analyses {{ref:s-measurement-would-settle-most}} lists
and this thesis did not run.

The practical consequence survives the uncertainty about mechanism, which is why the
recommendation is stated as it is. A programme in Kandy should read the row for the band Kandy
falls in, because that row is the closest available match to Kandy on every one of the correlated
variables at once, whichever of them is doing the work. That is a weaker justification than a
causal one and it is sufficient for the decision.
