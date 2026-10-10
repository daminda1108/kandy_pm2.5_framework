### Sensitivity to the humidity correction {#s-rh-scenario}

The sensor record that sets the amplitude of the temporal anchor was corrected for the
over-reading of optical sensors with a constant relative humidity of eighty per cent
({{ref:s-data-streams-their-uses}}). Which correction is right cannot be settled without a
co-located reference instrument, so both were carried through the delivered series as alternative
scenarios rather than waiting for one. The production scenario is the delivered field unchanged.
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
{{claim:rh2.hourly_rh.daily_r}}. And the timing of the morning and evening peaks and of the midday
trough does not move.

Three findings do not survive it. The ratio of the morning peak to the midday trough falls from
{{claim:rh2.production.peak_trough}} to {{claim:rh2.hourly_rh.peak_trough}}. The night, which in
the delivered field runs {{claim:rh2.production.night_midday}} times the midday level, falls to
{{claim:rh2.hourly_rh.night_midday}} of it, so whether the night or the midday is the daily
minimum depends on the correction. And the seasonal contrast widens from
{{claim:rh2.production.season_swing}} to {{claim:rh2.hourly_rh.season_swing}} between the highest
and lowest months. The interval's coverage of the corrected sensor record is
{{claim:rh2.production.cov90}} and {{claim:rh2.hourly_rh.cov90}}, one-sided in both.

The production scenario remains the delivered field because it is the one the model was built and
validated on, not because it is known to be right. Statements in this thesis about the depth of the
daily cycle, and about whether night exceeds midday, are therefore conditional on the humidity
correction; statements about the level, the timing of the cycle, the day-to-day sequence and the
local fraction are not.
