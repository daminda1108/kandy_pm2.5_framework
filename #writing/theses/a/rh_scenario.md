### Sensitivity to the humidity correction {#s-rh-scenario}

The sensor record that sets the amplitude of the temporal anchor was corrected for the
over-reading of optical sensors with a constant relative humidity of eighty per cent
({{ref:s-data-streams-their-uses}}). Which correction is right cannot be settled without a
co-located reference instrument, so both were carried through the temporal anchor as it was sharpened to
the sensors, as alternative scenarios rather than waiting for one. The production scenario is that anchor
unchanged, which was the delivered field until its daily cycle was refitted to the regulatory station.
The alternative applies the same correction with the hourly reanalysis humidity, moves the anchor's
hour-of-day and month climatology by the ratio of the two corrected records' climatologies, and
restores each year's mean to the satellite level; the background and its cap are then rebuilt with
the production code. The learned correction inside the anchor is not retrained, because the
amplitude of the delivered series is set by the climatology step and not by the learner. The
analysis is exploratory.

{{tbl:T3_rh_scenario}}

Four findings survive the choice. The annual level is the same by construction. The local fraction
moves from {{claim:rh2.production.f}} to {{claim:rh2.hourly_rh.f}}, well inside the range set by
the specification of the cap. The day-to-day sequence is unchanged: the correlation of the anchor's
daily means with the sensors' is {{claim:rh2.production.daily_r}} and
{{claim:rh2.hourly_rh.daily_r}}. And the timing of the morning and evening peaks and of the midday dip does not move.

Three findings do not survive it. The ratio of the morning peak to the midday level falls from
{{claim:rh2.production.peak_trough}} to {{claim:rh2.hourly_rh.peak_trough}}. The night, which in
the temporal anchor as sharpened to the sensors runs {{claim:rh2.production.night_midday}} times the midday level (every hour of
2019 to 2023, the hours to 04:00 against 14:00), falls to
{{claim:rh2.hourly_rh.night_midday}} of it, so whether the night or the midday is the daily
minimum depends on the correction. And the seasonal contrast widens from
{{claim:rh2.production.season_swing}} to {{claim:rh2.hourly_rh.season_swing}} between the highest
and lowest months. The interval's coverage of the corrected sensor record is
{{claim:rh2.production.cov90}} and {{claim:rh2.hourly_rh.cov90}}, one-sided in both.

Both scenarios are computed on the temporal anchor as it was before its daily cycle was refitted
to the regulatory station ({{ref:s-cea-reference}}), because they concern the correction of the
sensor record that shaped that anchor. The field was not rebuilt with the hourly correction, because
against the station neither correction fixes the defect: the hourly correction moves the nights
closer but leaves them too high and lowers the morning peak below what the station records, while
computing the cap on local rather than universal-time days moves the local fraction by about a
hundredth and leaves the nights unchanged. The daily cycle was instead refitted to the station
directly, and the collocation planned in {{ref:s-future-collocation}} is designed to find the cause
in the sensor record. Neither scenario is validated against a co-located reference instrument, and the two do not bound
the true cycle: they are alternatives that show which conclusions depend on the correction. The
regulatory station in the city centre, which is not co-located with the sensors, gives a partial
answer ({{ref:s-cea-reference}}): its morning peak matches the production scenario and its nights
are lower than either. Since that refit the delivered field's daily shape comes from the station rather than from either correction, so the scenarios bear on the sensor record and on the seasonal swing it still sets, not on the delivered daily cycle; statements about the level, the timing of the cycle, the day-to-day sequence and the local fraction do not depend on them.
