## The reconstructed field {#s-kandy-field}

The construction of {{ref:ch-model}} produces a concentration for every one-kilometre cell of the
Kandy domain for every hour from 2019 to 2023. This section describes what that field says. The
sections after it ask how far it can be believed, and the distinction matters: everything below
is a property of the reconstruction, and {{ref:s-checks-kandy-carry-weight}} and {{ref:ch-model-stops}} establish which
parts of it are supported by evidence.

### Level and partition {#s-kandy-field-level}

The annual basin mean runs from {{claim:kandy.mean_min}} to {{claim:kandy.mean_max}} micrograms
per cubic metre across the five anchored years. The reconstructed annual basin means exceed the
World Health Organization annual guideline of 5 micrograms per cubic metre [@WHO2021] in every
anchored year, by a factor of {{claim:kandy.who_min}} to {{claim:kandy.who_max}}. The level is the satellite surface's,
re-anchored to the regulatory station in the city centre by a single factor of
{{claim:ceabeta.beta}} fitted on 2019 to mid-2021 ({{ref:s-cea-reference}}); it is therefore as good
as that one station, and its check on later years covers only {{claim:ceasplit.months}} months. The
conclusion that the guideline is exceeded is robust to it: at either end of the factor's interval the
annual basin means lie between {{claim:ceabeta.level_lo}} and {{claim:ceabeta.level_hi}} micrograms
per cubic metre, at least {{claim:ceabeta.who_lo}} times the guideline. In
{{claim:exposure.year}} the regional background averages {{claim:partition.B_2023}} against a basin mean of
{{claim:partition.T_2023}}, so roughly half of the basin mean is carried by air that is the same everywhere in the
city: the local fraction that year is {{claim:partition.f_2023}}. Over the anchored years the annual fractions run
from {{claim:partition.f_lo}} to {{claim:partition.f_hi}}, and their mean, {{claim:partition.f}}, is the local
fraction quoted elsewhere. {{ref:s-partition-constraint-rather-than}} shows
that it is a property of the decomposition, set by a non-negativity constraint on the increment:
{{claim:v2.f.cap_min}} to {{claim:v2.f.cap_max}} across the tested day-boundary and daily-floor
choices and {{claim:field.f_form_roll48}} with a 48-hour background window, rather than a value the
data identify. The
lowest year is 2021, when activity was restricted for part of the year.

{{fig:field}}

All of the spatial structure lies in the local increment, the part of the concentration above the
background (panel b). It is highest on the built-up valley floor and lowest over the higher ground
to the south, which is the pattern the emission surface and the confinement term impose. Both are
imposed rather than fitted to anything measured in Kandy, which is why the pattern is independent
of the two local sensors and also why it has to be tested separately. Across the domain the
annual mean of the full field, background included, varies by a factor of
{{claim:kandy.annual_contrast}} between the tenth and ninetieth percentile cells and {{claim:kandy.contrast_maxmin}} between the lowest cell and the highest.
Averaged over a month the corresponding between-cell ratio is {{claim:field.contrast_monthly}},
and within a single hour it is {{claim:field.contrast_hourly}}. The hourly figure is the smaller
because on well-ventilated hours the local increment, which carries the pattern, is small or
absent, so the field over the city is close to uniform. These are contrasts of the full concentration
field at one-kilometre cells. The pattern *P* itself, which multiplies only the increment above the
background, has a larger contrast; the uniform background dilutes it in the full field, so the two
are different quantities and not inconsistent results.

### Seasonal and daily cycles {#s-kandy-field-cycles}

{{fig:spatiotemporal}}

In {{claim:exposure.year}} the basin mean is {{claim:kandy.season_djf}} micrograms per cubic metre
from December to February, {{claim:kandy.season_mam}} from March to May,
{{claim:kandy.season_jja}} from June to August and {{claim:kandy.season_son}} from September to
November, a ratio of {{claim:kandy.season_swing}} between the highest season and the lowest. The
highest concentrations fall in the north-east monsoon months and the lowest in the south-west
monsoon, when marine air and frequent rain keep concentrations down.

Within the day the field has two peaks and a trough. Averaged over the same year it is
{{claim:kandy.phase_morning}} in the morning traffic window, {{claim:kandy.phase_midday}} at
midday, {{claim:kandy.phase_evening}} in the evening and {{claim:kandy.phase_night}} at night, a
ratio of {{claim:kandy.phase_swing}} between the highest window and the lowest. In the delivered
field the midday trough and not the night is the daily minimum: the night runs
{{claim:kandy.night_over_midday}} times the midday level (basin mean of the delivered field in 2023, night and midday
windows as above; the temporal anchor over all hours of 2019 to 2023 gives {{claim:rh2.production.night_midday}}
and on the regulatory station's reporting hours {{claim:cea.hourly.production.night_over_midday}}, all well above the
station's own {{claim:cea.hourly.station.night_over_midday}}), consistent with the boundary layer that
dilutes emissions during the day collapsing after sunset. The same ordering is in the two Kandy
sensors' record as currently corrected, but it is not robust to the humidity correction (below). That agreement is expected rather
than earned, because the temporal anchor is calibrated to those sensors, and
{{ref:s-checks-kandy-carry-weight}} explains why it cannot be counted as validation.

The depth of the daily cycle carries a further qualification. The sensor record to which the
temporal anchor is sharpened was converted from the sensors' raw readings with a constant
relative humidity. Repeating the conversion with the hourly humidity reduces the ratio of the morning peak to the midday level in that record from {{claim:v2.rh.constant_rh80.peak_to_trough}} to
{{claim:v2.rh.barkjohn_hourly_rh.peak_to_trough}} while leaving the timing of the morning and
evening peaks and of the midday dip unchanged. Carried through the delivered series
({{ref:s-rh-scenario}}), it also reverses the ordering of night and midday: the night falls to
{{claim:rh2.hourly_rh.night_midday}} of the midday level. The shipped field uses the
constant-humidity conversion. The regulatory station's hourly record ({{ref:s-cea-reference}})
supports the timing of the cycle and the depth of the morning peak, but at the station the deep
night is the daily minimum, at {{claim:cea.hourly.station.night_over_midday}} of the midday level,
so the field's nights are too high relative to midday and the statement that night exceeds midday
should not be relied on.

### An episode {#s-kandy-field-episode}

Averages hide the days that matter most for health. In December 2022 the field shows a
high-concentration episode across the whole basin, and those two days show what the construction
does with one.

{{fig:episode}}

Over the 48 hours of the episode the basin mean averaged {{claim:kandy.episode_mean}} micrograms
per cubic metre, reaching {{claim:kandy.episode_peak}} in the evening of the first day. At the peak
hour the whole domain was raised together: the difference between the cleanest and the most
polluted cell was small beside the level itself (panel a). In this model a uniform rise is what an
elevated background produces by construction, because the background is uniform across the domain
and all spatial structure belongs to the local increment; the uniformity is therefore consistent
with regional transport but is not independent evidence of it. It is a model-inferred regional
episode. The episode falls in the north-east monsoon, the season in which published back-trajectory
analysis of the national network traces high particulate concentrations to air arriving from eastern
India and the Bay of Bengal [@Nirmani2025], but that analysis is seasonal and does not establish the
origin of this particular event. If it was regional, an episode of this kind is, for a local
authority, a warning to issue rather than an emission to control, and
recognising it on the day requires an observation that reaches the estimate on the day, whether
from a station inside the basin or from a background station outside it.
