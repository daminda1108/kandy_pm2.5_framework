## Discussion {#a-discussion}

The results sort the field into three kinds of statement, and the sorting is the main thing this
study establishes about Kandy. A fourth part of the discussion concerns what Kandy should measure
next, and a fifth records a design flaw found late in the work and what it changed.

**Supported: the timing.** The seasonal and daily behaviour of the field is supported from three
directions. The construction that produces it transfers between monitored valley and basin cities
when their own observations are withheld ({{ref:s-model-across-ten-cities}}). Its temporal anchor,
placed on the ladder, follows the withheld daily city mean at a correlation of
{{claim:v2.km.reco.unio.K2_r.median}} where its anchor stations observed the period, though only
{{claim:v2.km.pros.unio.K2_r.median}} where they did not, so the day-to-day sequence at Kandy is
best supported on the days its sensors reported ({{ref:s-kandy-model-rung}}). At Kandy itself the
daily record of the national research organisation, recovered for 2021 and 2022, supports the
seasonal shape (correlation {{claim:nbrod.climatology_r}} across the twelve calendar months) but
not the day-to-day sequence (correlation {{claim:nbrod.anomaly_daily_r}} within months), and the
field misses the year 2022 almost entirely ({{ref:s-kandy-daily-record}}). The timing evidence is
therefore strongest for the seasonal cycle, weaker for the daily cycle, and weakest for individual
days. The interval around the field
under-covers: nominal ninety per cent intervals cover {{claim:kandy.cov90}} per cent of the two
sensors' hours. Removing each sensor's own offset, with the width unchanged, raises that to
{{claim:kandy.cov90_recentred}} per cent ({{ref:s-interval-calibration}}), which diagnoses a possible
calibration bias at those sensors; it does not establish that the width is right for the basin
field, and across the ladder's cities the interval under-covers as well. One qualification applies to the amplitude of the daily cycle rather than its
timing. The sensor record to which the temporal anchor is sharpened was converted with a constant
relative humidity, and repeating the conversion with hourly humidity reduces the ratio of the morning peak to the midday level in that record from {{claim:v2.rh.constant_rh80.peak_to_trough}} to
{{claim:v2.rh.barkjohn_hourly_rh.peak_to_trough}}. Carried through the delivered series, the alternative leaves the
level, the timing of the peaks and of the midday dip, the day-to-day sequence and the local fraction
essentially unchanged, but it reduces the depth of the cycle and reverses the ordering of night and
midday ({{ref:s-rh-scenario}}). The regulatory station's hourly record
({{ref:s-cea-reference}}) supports the timing and the depth of the morning peak but places the
daily minimum in the deep night, lower than either conversion gives, so the field's nights are too
high. Which part of that is the humidity conversion and which the low-cost sensors' siting cannot
be separated without co-locating them with the reference.

**Anchored to one station: the level.** Taken from the satellite surface, the field read
{{claim:cea.sat.all.bias_pct}} per cent above the one regulatory record at Kandy, a station in the city
centre ({{ref:s-cea-reference}}); a calibrated low-cost record also sat below it, and only the national
research organisation's record, of undocumented instrument, sat above it. The delivered field is
re-anchored to the station with a factor fitted on its first two and a half years. The temporal anchor is itself calibrated to the city's two low-cost sensors, so
the level is not independent of Kandy observations in the way the pattern is. Two readings remain
possible. The offset may be a change of support, an area mean compared with points, or it may be
an upward bias of the field at the sensor locations, for which the constant-humidity conversion
is one candidate mechanism. The regulatory record makes the first harder to sustain, because its station lies in the
city centre where the cell is among the highest in the basin, but one station cannot separate a
level bias from a siting effect. The station does locate the step at which the excess enters. The corrected Akurana record follows the station closely
and sits {{claim:ceaatt.pct.akurana}} per cent from it on the days both reported, whereas the anchor
after re-anchoring to the satellite level sits {{claim:ceaatt.pct.T_basin}} per cent above it. The
low-cost calibration, long the suspected source, is the part that agrees; the satellite level is the
part that does not, which is why the correction was made at that step and nowhere else. On the
station's later record, not used for the fit, the re-anchored field is within
{{claim:ceasplit.bias_re}} per cent of the station where the satellite level was
{{claim:ceasplit.bias_sat}} per cent out, but over only {{claim:ceasplit.months}} months, and the
correction does not hold beyond 2023. What can be said is bounded: across the interval of the level factor the annual basin means lie
between {{claim:ceabeta.level_lo}} and {{claim:ceabeta.level_hi}} micrograms per cubic metre, at least
{{claim:ceabeta.who_lo}} times the guideline ({{ref:s-kandy-field-level}}). The
consequence runs through every number in {{ref:s-kandy-field}}: the cycles and the partition are
statements about shape and proportion that survive a shift in level, while the annual means, the
exposure figures and the comparison with the guideline do not. For that reason, among others,
no attributable burden is reported ({{ref:app-attributable-burden-projection}}).

**Not supported: the neighbourhood pattern.** The spatial pattern is a construction and should be
read as one. Measured on cities with dense networks, the spread inside a single cell is
{{claim:s2.within_pixel_p90p10}} against {{claim:s2.between_pixel_p90p10}} between cells
({{ref:s-reason-change-support}}), so most of the variation a resident would experience lies below
the resolution of the field. The step built to place the local increment through terrain-steered
flow lowers the ranking of neighbourhoods from the {{claim:r2.rho_emission_surface}} of the raw
emission surface to {{claim:r2.rho_with_atransport}}, and no model family built on freely
available covariates beat a single land-cover layer by more than the detection limit of
{{claim:phase1.min_detectable}} in rank correlation. Adding a few stations does not change this.
On the full records of the monitored cities, interpolation from three to eight stations clearly
overtook the free land-cover layer in only {{claim:v2.curve.full.holm_crossing}} of twenty-three
cities once multiple testing was accounted for, and neither interpolation nor a satellite PM2.5
surface, which reached a within-city rank correlation of {{claim:v2.curve.full.ghap.median}},
ranked neighbourhoods usefully ({{ref:s-spatial-results-support}}). The population-weighted
exposure of {{ref:s-exposure-weighting}} depends on where the pattern puts the concentration
relative to where people live, and inherits that limitation.

**The partition sits between the two.** The decomposition assigns {{claim:partition.f}} of the
concentration to the local increment. That value is set by a non-negativity constraint on the
increment, which caps how large the background can be, and it is therefore a bound rather than an
identification: it moves from {{claim:partition.f_lo}} to {{claim:partition.f_hi}} across the
anchored years, from {{claim:v2.f.cap_min}} to {{claim:v2.f.cap_max}} across the choice of day
boundary and of the statistic used for the daily minimum, and reaches
{{claim:field.f_form_roll48}} under a 48-hour background window
({{ref:s-partition-constraint-rather-than}}). Under every one of these choices the local fraction
is close to half. Two measurement routes at the regulatory station bracket it from below and above: the urban excess
over the cleanest regional town gives {{claim:lfs.e1min.f}}, a lower bound because every regional sensor is in a town,
and a combustion-tracer intercept gives {{claim:lfs.e2.co_p5.f}} ({{ref:s-local-fraction-measured}}). The model, at
{{claim:lfs.model.e2_cell}} for that cell, sits at the upper end; the rule fixed before the comparison classes it as
high against the first route, whose bias runs in the direction that would explain the gap. That is not comparable with the quarter taken earlier from source apportionment,
which classifies mass by emitting source rather than by spatial structure, and it does not establish
how much of the increment is emitted locally rather than formed in the air, which is the question a composition measurement would answer
({{ref:s-measurement-would-settle-most}}).

**What Kandy should measure next.** Each limit above points to the same need, local observation,
and the cross-city measurement of {{ref:a-app-panel}} says what form it should take. A station's
value to a daily city-mean estimate lies in its reading entering the estimate each day. Read daily,
one station reduces daily error by {{claim:v2.review.k.day1.median}} per cent, two by
{{claim:v2.review.k.day2.median}} per cent and five by {{claim:v2.review.k.day5.median}} per cent;
used only to calibrate the sensorless estimate, the same stations reduce it by about
{{claim:v2.review.k.cal2.median}} per cent whatever their number. The kind of station matters
little: two stations read on the day are worth about the same whether they are the first local
stations or two of the outer stations from which the background series is built. The difference
between them is {{claim:v2.review.registered_loco.reco.BG2mL2s_rmse.median}} points (95 per
cent interval {{claim:v2.review.registered_loco.reco.BG2mL2s_rmse.lo}} to
{{claim:v2.review.registered_loco.reco.BG2mL2s_rmse.hi}}), and a background series read on the
day differs from the first two stations read on the day by
{{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.median}} points
({{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.lo}} to
{{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.hi}}). Beyond the first few stations the
returns are small for a city mean, and a neighbourhood map is not within reach of a handful of
stations at all. For Kandy this means continuously reporting stations whose readings enter the
estimate daily. The national environmental authority's hourly record from 2019 is the nearest
such source, and could enter the reconstruction day by day for the years it covers rather than
serve once as a calibration; a regional background series from the National Building Research
Organisation network is complementary to it, not ranked against it. A reference-grade instrument among the
stations would add what no low-cost sensor can, by settling the level that the independent
records leave open. The panel on which these values were measured is mostly temperate and mostly
regulatory, whereas Kandy is tropical and low-cost; nothing in the panel suggests that the value
of a daily reading depends on climate, but the panel has too few tropical cities to test it.

**A design flaw found by review, and what it changes.** After the registered tests had been run,
an adversarial review of the project's own code and design found that the registered comparison
of rungs on the information ladder did not compare like with like. The first local stations
entered only as a recalibration of the sensorless estimate, an intercept and a slope fitted once,
whereas the background series entered with its reading on each day. As constructed, the
registered test found the background ahead of the first two stations by
{{claim:v2.conf.reco.bgm2_rmse.median}} points (95 per cent interval
{{claim:v2.conf.reco.bgm2_rmse.lo}} to {{claim:v2.conf.reco.bgm2_rmse.hi}}), and that verdict
stands as a statement about the rungs as built. Once both were used the same way, the difference
was close to zero. The registration had fixed how the test was run, and the test was run exactly
as written behind a parity gate; registration does not check whether a comparison compares like
with like, and a design that treats its arms differently should be expected to find an ordering.
For Kandy the change is material. Earlier drafts of this work recommended a background series
ahead of local stations on the strength of the registered ordering, and before that recommended
local stations ahead of a background on the strength of an apparent reversal in the deep tropics
that did not survive averaging over station splits. Neither recommendation stands. What replaces
them is the recommendation above, which does not rank kinds of station and rests on how a
station's readings are used. That recommendation is better founded than either predecessor but not
equally confirmed: the like-for-like comparison is a post hoc re-analysis of the registered
data, and the near-equivalence of station types it reports awaits a fresh pre-specified test.

Read together, the field is a well-founded account of when Kandy's air is worse and by roughly
how much relative to the rest of the year, on a level anchored to one regulatory station, with nights that run too
high relative to midday, and with a spatial pattern that is
imposed rather than measured. That is less than a validated map, and the map should not be read
as one: its differences between cells are a hypothesis to be tested, not a ranking of
neighbourhoods. It is also more than Kandy has
had, and each of its limits points to a specific measurement, set out in {{ref:ch-measure-next}}
and carried into the further work of {{ref:a-conclusions}}.
