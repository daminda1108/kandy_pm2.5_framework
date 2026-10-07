## The data streams and their uses {#s-data-streams-their-uses}

**Satellite aerosol retrieval** supplies a daily signal that correlates with column loading
[@Lyapustin2018; @Levy2013]. It is the only stream that observes the atmosphere over Kandy
directly at useful frequency. Its
weaknesses are that it is absent under cloud, which in a monsoon climate is a substantial
fraction of days, and that it carries no diurnal information whatever, because the satellite
passes at a fixed local time.

A satellite-derived annual concentration surface supplies the level [@Wei2023]. It is a fusion
product and it is used here only as an annual anchor. {{ref:s-effect-monitor-trained-covariate}} describes what happened when it was
used as though it were an independent observation, which it is not.

Reanalysis meteorology supplies wind, boundary-layer height, temperature and humidity at
hourly resolution [@Hersbach2020]. This is the workhorse of the temporal model and it is the
reason a sensorless tier is possible at all. Its limitation is one of scale: a valley
boundary layer fifteen kilometres across is not resolved by a driver whose grid is twice that.
What the driver supplies is the regional state, and the model's task is to map from that state
to a local response.

A global composition reanalysis supplies a chemical prior [@Keller2021]. It enters as a
feature rather than as a target, and {{ref:s-independent-chemical-check}} uses its speciation for an independent check.
It is itself a model at roughly twenty-five kilometres, so it can corroborate or contradict but
cannot validate.

Precipitation required a decision that is worth recording. The obvious choice, land-surface
reanalysis precipitation, was tested against a representative gauge and rejected: it delivers
approximately twice the gauge total at this site. Satellite precipitation radar [@Huffman2020] lands
within a few per cent of the same gauge and is used instead. Where it is absent the field reports nothing
rather than falling back to the rejected product.

Static geography supplies terrain, roads, land cover, vegetation, night lights and
population [@Farr2007; @OpenStreetMap; @Zanaga2022; @Didan2021; @Hansen2013; @Pekel2016; @Elvidge2017; @Schiavina2023; @Pesaresi2023]. Individually each is a weak predictor. Collectively they make up most of the predictors of the
sensorless tier on the ladder of {{ref:s-marginal-predictive-value-each}}, and they are free
everywhere on Earth. In the redesigned ladder they are computed at random points in each city's
urban centre rather than at its monitoring sites, so that a city without monitors can compute them
too. {{ref:s-implications-radius-result}} reports that land cover
measured over a coarse buffer is the strongest single spatial predictor in the entire set, which
was not expected.

The two local sensors are low-cost units, their records obtained through PurpleAir [@PurpleAir],
at different elevations, one at roughly 460 metres
about six kilometres north of the city and one at roughly 738 metres on the southern slope. Both
sit on or near the valley floor, not on the ridge, and a metadata audit early in the
project found that both had been recorded at incorrect elevations for some months, which had
propagated into a description of them as highland sites. They are not.

Both records are corrected for the known over-reading of optical sensors with the Barkjohn
equation [@Barkjohn2021]. Its humidity term was evaluated at a constant relative humidity of
eighty per cent rather than at the hourly value. Because the humidity at Kandy follows a strong
daily cycle, this leaves part of that cycle in the corrected record: recomputed with hourly
reanalysis humidity, the ratio of the normalised morning peak to the afternoon trough falls from
{{claim:v2.rh.constant_rh80.peak_to_trough}} to {{claim:v2.rh.barkjohn_hourly_rh.peak_to_trough}}.
{{ref:s-excluded-processes-known-limits}} sets out what this means for the model.
