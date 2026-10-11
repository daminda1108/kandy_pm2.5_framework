### The regulatory station in Kandy city {#s-cea-reference}

The national regulatory authority operates an automated monitoring station in the centre of Kandy,
one of two such stations in the country. Its record was requested formally during this work and
access was granted in principle, subject to an agreement that had not been concluded by the time
of writing ({{ref:s-data-requested-but-obtained}}). The authority's public platform, however, serves
the station's daily and hourly means for the whole period, and the comparison below uses those
public values [@CEA2026AirShare]; any underlying record released under the formal agreement may
differ from them. The station's record from January 2019 to June 2021 is used to set the field's
level, below; only its later record is independent of the model. It is the only record at Kandy from
a regulatory instrument, although the platform does not state the measurement method. The station reported PM2.5 on {{claim:cea.days}} days between 2019 and 2023. It did not
operate from mid-2021 to late 2022, so 2021 and 2022 are represented by a few months each. The
analysis is exploratory and was added after the rest of the model had been fixed.

{{tbl:T3_cea}}

**The level, as first built.** Before this record was used, the field took its annual level directly
from the satellite surface. Over all reporting days the station's mean is {{claim:cea.sat.all.obs_mean}}
and that field at the station's cell {{claim:cea.sat.all.model_mean}}, so it read
{{claim:cea.sat.all.bias_pct}} per cent above the station. The excess held in every year except
2022, whose {{claim:cea.sat.2022.n}} reporting days fall in the high season at the end of the year:
{{claim:cea.sat.2019.bias_pct}} and {{claim:cea.sat.2020.bias_pct}} per cent in the two full years
and {{claim:cea.sat.2023.bias_pct}} per cent in 2023. The field with the dispersion step, before it
was removed, read {{claim:cea.disp.all.bias_pct}} per cent above the station.

**The timing.** The level does not affect the timing, which is the same in every version of the
field. The daily correlation is {{claim:cea.del.all.r}}, against
{{claim:cea.bench.r}} for the station's own calendar-month climatology. Once each month's mean is
removed from both series, the daily correlation is {{claim:cea.del.anomaly_daily_r}}, so the field
follows the station's day-to-day sequence within the month, more closely than at the
research organisation's station ({{ref:s-kandy-daily-record}}). Across the twelve calendar months the
correlation is {{claim:cea.del.climatology_r}}. On the {{claim:cea.del.sensors_absent.n}} days when the
city's two low-cost sensors were not reporting, the daily correlation is
{{claim:cea.del.sensors_absent.r}}; on the {{claim:cea.del.sensors_reported.n}} days when they were, it
is {{claim:cea.del.sensors_reported.r}}. Agreement with this record therefore does not depend on the
anchor sensors being present.

**Where the excess enters.** On the {{claim:ceaatt.days}} days on which both the station and the
Akurana low-cost sensor reported, the station's mean is {{claim:ceaatt.mean.obs}}. The corrected
sensor record, which the temporal anchor is trained on, reads {{claim:ceaatt.mean.akurana}}
({{claim:ceaatt.pct.akurana}} per cent relative to the station) and follows the station closely, at a daily correlation of
{{claim:ceaatt.r.akurana}}. The basin anchor after its yearly re-anchoring to the satellite level
reads {{claim:ceaatt.mean.T_basin}} ({{claim:ceaatt.pct.T_basin}} per cent above), and the field at the
station's cell {{claim:ceaatt.mean.delivered}} ({{claim:ceaatt.pct.delivered}} per cent above). The
satellite level at the city's cell exceeds the station's annual mean by
{{claim:ceaatt.vand.2019.pct}}, {{claim:ceaatt.vand.2020.pct}} and {{claim:ceaatt.vand.2023.pct}} per
cent in the three years the station covers well. The excess therefore enters at the step that sets
the anchor's annual level from the satellite surface, not in the low-cost sensor record and not in
the spatial pattern. It also corroborates the sensors' calibration: the corrected Akurana record
sits within a few per cent of a regulatory instrument. The ratio of the station to the ridge sensor
at Hantana is {{claim:ceaatt.ratio.hantana.2019_2023}} before 2024 and
{{claim:ceaatt.ratio.hantana.2024_2026}} after it, on only {{claim:ceaatt.ratio.hantana.2024_2026.n}}
days, so there is no sign that the station's record shifted between the uploaded sets in which the
platform holds it, although the later check is thin.

**Re-anchoring the level, with a held-out check.** Because the excess enters at one identifiable step,
it can be corrected there without touching the rest of the chain. The annual satellite level is
multiplied by a single factor, fitted as the ratio of the station's mean to the field's over the
station's first {{claim:ceabeta.days}} reporting days, January 2019 to June 2021. The factor is
{{claim:ceabeta.beta}} (95 per cent interval {{claim:ceabeta.lo}} to {{claim:ceabeta.hi}}, from a
bootstrap over its {{claim:ceabeta.months}} months). It scales the temporal anchor and the background
together, so the spatial pattern is unchanged and the local fraction moves only through the
background's fixed marine floor, and it is applied as a
multiplication because a fixed downward shift of that size drove the cleanest hours below zero. The
station's later record, October 2022 to 2023, was not used and serves as the check. On those
{{claim:ceasplit.days}} held-out days the re-anchored field differs from the station by
{{claim:ceasplit.bias_re}} per cent ({{claim:ceasplit.bias_re.lo}} to {{claim:ceasplit.bias_re.hi}}),
against {{claim:ceasplit.bias_sat}} per cent ({{claim:ceasplit.bias_sat.lo}} to
{{claim:ceasplit.bias_sat.hi}}) for the field at the satellite level, and its daily error is
{{claim:ceasplit.rmse_change}} per cent different ({{claim:ceasplit.rmse_change.lo}} to
{{claim:ceasplit.rmse_change.hi}}). The pooled figure hides errors of opposite
sign: the re-anchored field reads {{claim:cea.del.2022.bias_pct}} per cent in the short 2022 window
and {{claim:cea.del.2023.bias_pct}} per cent in 2023, so it is not shown to be accurate year by year,
and the interval on the change in daily error includes no improvement. The held-out record covers
only {{claim:ceasplit.months}} months, so the check points in the right direction without excluding
the satellite level. The factor is also fitted at one point, the station's cell, and applied to the
whole basin, so it carries the assumption that the modelled relation between that cell and the basin
mean is right; the spatial pattern that sets that relation is not validated
({{ref:s-spatial-contrast-lost}}). The result is therefore a provisional basin-level correction
anchored to one regulatory station, conditional on the modelled site-to-cell relation, and a
held-out temporal check; it is not an independent measurement of the basin mean. The delivered field is the
re-anchored one ({{tbl:T3_cea}} shows both).

**After 2023.** The software extends the field to 2024 to 2026 without a satellite surface for
those years ({{ref:a-scope}}); the station allows that extension its only check. On the {{claim:ceaext.days}} days the station reported, mostly in
the high season, the extension, which inherits the re-anchored level, differs from the station's mean by
{{claim:ceaext.all.bias_pct}} per cent, reading low,
with a daily correlation of {{claim:ceaext.all.r}} and {{claim:ceaext.monthly_r}} for monthly means;
within the month the correlation is {{claim:ceaext.anomaly_daily_r}}. The station's own calendar
climatology reaches {{claim:ceaext.bench.r}} over the same days, so the extension's day-to-day skill
there is no better than the season. The station's hourly cycle over these years has the same shape
as before, with a morning peak {{claim:ceaext.hourly.station.peak07_over_midday}} times midday and
nights at {{claim:ceaext.hourly.station.night_over_midday}} of it; the extension exaggerates the
morning peak ({{claim:ceaext.hourly.production.peak07_over_midday}}) and keeps its nights high
({{claim:ceaext.hourly.production.night_over_midday}}). The station reads much higher in these years than before 2023, while the
model's level does not rise, and the re-anchoring makes the gap larger. Whether the rise is real or
a change in the station's record cannot be settled from the platform: the ratio to the Hantana
sensor is stable, but on only {{claim:ceaatt.ratio.hantana.2024_2026.n}} days. The extension is not
otherwise used in this thesis, and the re-anchoring is not supported beyond 2023.

**The daily cycle.** The station's hourly record, {{claim:cea.hourly.hours}} hours, is the first
reference against which the shape of the daily cycle can be checked. The platform's timestamps
follow two conventions: the records uploaded in batches for 2019 to mid-2025 are stamped in universal
time, and the live feed from September 2025 in local time. This was established from the gases. Ozone,
which peaks in the early afternoon, peaks at {{claim:cea.hourly.o3_peak_hour}} local time once the
batch records are shifted by five and a half hours, and the carbon monoxide cycle of the live feed
matches that of the batches only without the shift. Every hourly comparison uses the corrected
times. The
station's cycle has the timing of the delivered anchor: its highest hour is
{{claim:cea.hourly.station.max_hour}} in the morning, with a second peak in the evening and a dip
around midday. The morning peak is {{claim:cea.hourly.station.peak07_over_midday}} times the
midday level, against {{claim:cea.hourly.production.peak07_over_midday}} in the delivered anchor and
{{claim:cea.hourly.hourly_rh.peak07_over_midday}} under the hourly-humidity correction
({{ref:s-rh-scenario}}). The night is different. At the station the deep night is the daily
minimum, at {{claim:cea.hourly.station.night_over_midday}} of the midday level, whereas the delivered
anchor, on the same hours as the station, runs {{claim:cea.hourly.production.night_over_midday}} times midday at night and the
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
field and the level was reported as open. The regulatory record showed the satellite level about a
quarter too high at the city centre, located the excess in the satellite surface rather than in the
low-cost calibration, and allowed it to be corrected with a check on years not used for the fit. The
delivered level is therefore set by one regulatory station through a single factor, and its
uncertainty is that factor's interval, roughly a tenth either way, together with whatever the
station's undocumented method and siting contribute. The cost is independence: the station is now an
input for 2019 to mid-2021, and only its later record remains a check. The authority's conditions for
academic use of its data are acknowledged in {{ref:s-data-requested-but-obtained}}.
