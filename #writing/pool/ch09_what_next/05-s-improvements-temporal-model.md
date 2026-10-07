## Improvements to the temporal model {#s-improvements-temporal-model}

Five items, in decreasing order of what the evidence supports.

**An hourly humidity correction in the label.** The low-cost record the temporal anchor is
sharpened to was corrected with a constant relative humidity. With the hourly humidity the same
correction expects, the peak-to-trough ratio of the observed diurnal cycle falls from
{{claim:v2.rh.constant_rh80.peak_to_trough}} to {{claim:v2.rh.barkjohn_hourly_rh.peak_to_trough}},
so part of the delivered daily swing is a humidity artefact of the label. The correction is
straightforward to apply, but which diurnal shape is right can only be settled against a
co-located reference record, so the rebuild is deferred until the Central Environmental
Authority's Kandy record is available, and the two should be done together.

**The coherence cap on local days.** The constraint that sets the local fraction compares the
background with the daily minimum of the total, and production evaluates it on days defined in
universal time rather than in local time, using the minimum of twenty-four noisy hourly values,
which is biased low. Across reasonable choices of the day and the statistic the local fraction
moves between {{claim:v2.f.cap_min}} and {{claim:v2.f.cap_max}}. The partition should be quoted as
a bound under the cap with that range, and the cap should be rebuilt on local days in the same
pass as the humidity correction.

**Precipitation in the forecast drivers.** The current driver set for the forecast tier contains
no precipitation at all, which is a structural gap, not a measured deficiency. Wet removal
is one of the principal loss processes for particulate matter and the model is currently blind to
it in that mode. The ladder's driver set is a different case: it already held a daily rainfall
total that was never used, and {{ref:s-marginal-predictive-value-each}} reports the registered test of adding it, which found
nothing.

A per-lead skill curve. The forecast tier is presented as a demonstration rather than as a
validated product, and it will remain so until skill is reported separately at each lead time.
The current single widening factor applied across all leads is a placeholder.

A second driver source. Everything the model knows about the atmospheric state comes from one
reanalysis family. A second source would allow the driver contribution to be separated from the
particular reanalysis it came from, which no result in this thesis currently does.
