### The regulatory station in Kandy city {#s-cea-reference}

The national regulatory authority operates an automated monitoring station in the centre of Kandy,
one of two such stations in the country. Its record was requested formally during this work and
access was granted in principle, subject to an agreement that had not been concluded by the time
of writing ({{ref:s-data-requested-but-obtained}}). The authority's public platform, however, serves
the station's daily and hourly means for the whole period, and the comparison below uses those
public values [@CEA2026AirShare]. The record played no part in building the field. It is the only
record at Kandy from a regulatory instrument, although the platform does not state the measurement
method. The station reported PM2.5 on {{claim:cea.days}} days between 2019 and 2023. It did not
operate from mid-2021 to late 2022, so 2021 and 2022 are represented by a few months each. The
comparison is exploratory and was made after the field was fixed.

{{tbl:T3_cea}}

**The level.** Over all reporting days the station's mean is {{claim:cea.del.all.obs_mean}} and the
field at the station's cell is {{claim:cea.del.all.model_mean}}, so the field reads
{{claim:cea.del.all.bias_pct}} per cent above the station. The excess holds in every year except
2022, whose {{claim:cea.del.2022.n}} reporting days fall in the high season at the end of the year:
{{claim:cea.del.2019.bias_pct}} and {{claim:cea.del.2020.bias_pct}} per cent in the two full years
and {{claim:cea.del.2023.bias_pct}} per cent in 2023. The field as delivered before the dispersion
step was removed read {{claim:cea.disp.all.bias_pct}} per cent above the station, so the removal
moved the level towards this record.

**The timing.** The daily correlation is {{claim:cea.del.all.r}}, against
{{claim:cea.bench.r}} for the station's own calendar-month climatology. Once each month's mean is
removed from both series, the daily correlation is {{claim:cea.del.anomaly_daily_r}}, so the field
follows the station's day-to-day sequence within the month, more closely than at the
research organisation's station ({{ref:s-kandy-daily-record}}). Across the twelve calendar months the
correlation is {{claim:cea.del.climatology_r}}. On the {{claim:cea.del.sensors_absent.n}} days when the
city's two low-cost sensors were not reporting, the daily correlation is
{{claim:cea.del.sensors_absent.r}}; on the {{claim:cea.del.sensors_reported.n}} days when they were, it
is {{claim:cea.del.sensors_reported.r}}. Agreement with this record therefore does not depend on the
anchor sensors being present.

**The daily cycle.** The station's hourly record, {{claim:cea.hourly.hours}} hours, is the first
reference against which the shape of the daily cycle can be checked. The platform stamps hourly
records in universal time rather than local time; this was established from the station's ozone,
which peaks in the early afternoon, at {{claim:cea.hourly.o3_peak_hour}} local time once the stamps
are shifted by five and a half hours, and every hourly comparison uses the shifted times. The
station's cycle has the timing of the delivered anchor: its highest hour is
{{claim:cea.hourly.station.max_hour}} in the morning, with a second peak in the evening and a dip
around midday. The morning peak is {{claim:cea.hourly.station.peak07_over_midday}} times the
midday level, against {{claim:cea.hourly.production.peak07_over_midday}} in the delivered anchor and
{{claim:cea.hourly.hourly_rh.peak07_over_midday}} under the hourly-humidity correction
({{ref:s-rh-scenario}}). The night is different. At the station the deep night is the daily
minimum, at {{claim:cea.hourly.station.night_over_midday}} of the midday level, whereas the delivered
anchor runs {{claim:cea.hourly.production.night_over_midday}} times midday at night and the
hourly-humidity scenario {{claim:cea.hourly.hourly_rh.night_over_midday}}. The correlation of the
mean daily cycles is {{claim:cea.hourly.production.shape_r}} for the delivered anchor and
{{claim:cea.hourly.hourly_rh.shape_r}} for the hourly-humidity scenario. The reference therefore
settles the question left open in {{ref:s-rh-scenario}} in one direction: the timing of the cycle
and the depth of the morning peak are supported, and the nights of the delivered field are too
high relative to midday, by more than either humidity correction accounts for. The anchor's daily
shape is inherited from the two low-cost sensors through the amplitude sharpening
({{ref:s-temporal-anchor}}), so this is a property of the calibration record rather than of the
model's predictors.

**What it changes.** Before this record was available, the external records at Kandy bracketed the
field, one above and three below, and the level was reported as open. A regulatory instrument now
sits below the field by about a quarter in most years, in the same direction as the calibrated
low-cost records and the one-sided interval misses at the two anchor sensors
({{ref:s-interval-calibration}}). The research organisation's record, of undocumented instrument, is
the only one above it. The weight of evidence is now that the delivered level is too high at the
city centre. The size of the excess is uncertain, because the station's method and siting are not
documented and because a point and a one-kilometre cell need not agree. The field has not been
recalibrated to this record: doing so would make the record an input, and it is the only regulatory
check available. The authority's conditions for academic use of its data are acknowledged in
{{ref:s-data-requested-but-obtained}}.
