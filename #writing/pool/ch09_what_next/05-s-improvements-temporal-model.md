## Improvements to the temporal model {#s-improvements-temporal-model}

Three items, in decreasing order of what the evidence supports.

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
