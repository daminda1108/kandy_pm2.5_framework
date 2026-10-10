## Future work {#a-future}

The limits identified in {{ref:a-results}} each point to a specific piece of further work.

### Measurements that would settle the most {#s-measurement-would-settle-most}

**Continuously reporting stations at Kandy, read daily, with a reference-grade instrument among
them.** This is the ranking of {{ref:s-measurement-priority-ordering}}. A reference instrument
co-located with the low-cost sensors would also settle the level, which three low-cost records and
one national record leave open, and the depth of the daily cycle, which depends on the humidity
correction. The national regulatory authority's Kandy record, granted in principle
({{ref:s-data-requested-but-obtained}}), is the first such record to obtain, and it would allow the
deployed model to be scored at Kandy on the same footing as the ladder scores it elsewhere.

**A composition measurement.** The locally emitted primary share lies between
{{claim:chem.intervention_lo}} and {{claim:chem.intervention_hi}} per cent, and the width of that
range is set entirely by not knowing how much of the local increment is secondary. Speciated
measurement at Kandy would narrow it and make the species-resolved test of
{{ref:s-independent-chemical-check}} possible.

**A regional background station.** It would supply the regional series the background term is
currently built without, and separate regional information from more of the same network in a way
no re-analysis of the panel can. The nearest reference city, Colombo, was tested as a donor and
refused: its daily correlation with Kandy is {{claim:donor.colombo_r}} against a benchmark of
{{claim:donor.benchmark_median_matched}} at comparable separation, consistent with the finding of
[@Senarathna2026] that sensor calibrations do not transfer between the two climatic zones.

### The construction step most worth revisiting {#s-construction-step-most-worth}

Scored against held-out stations, the dispersion step lowers the pattern's rank correlation from
{{claim:r2.rho_emission_surface}} to {{claim:r2.rho_with_atransport}}
({{ref:s-spatial-contrast-lost}}). A construction that declined to redistribute would already be
better than the one delivered, so the undispersed surface, not the delivered field, is the
benchmark for any replacement.

### Improvements to the temporal model {#s-improvements-temporal-model}

The sensor record that sharpens the anchor should be corrected with hourly rather than constant
humidity, which lowers the observed peak-to-trough ratio from
{{claim:v2.rh.constant_rh80.peak_to_trough}} to {{claim:v2.rh.barkjohn_hourly_rh.peak_to_trough}};
which shape is right can only be settled against a co-located reference, so the rebuild waits for
the regulatory record. In the same pass the coherence cap should be evaluated on local days with a
robust daily floor. The panel version of the anchor scored on the ladder
({{ref:s-kandy-model-rung}}) used only the composition prior and meteorology; scoring the full
predictor set across the panel would test whether the satellite and composition predictors add
day-to-day skill. A second reanalysis family as driver, and precipitation in the forecast drivers,
would remove two structural dependencies.

### Approaches that would not help {#s-approaches-would-help}

A larger model, because a model can only redistribute the information in its inputs and no model
family tested recovered structure the inputs did not encode ({{ref:s-six-negative-results-their}}).
A finer grid, because the variation lives inside the cell ({{ref:s-implications-radius-result}}).
More stations for a neighbourhood map at the counts a city like Kandy could afford, or stations
sited deliberately across land-use contrast, because neither produced a resolvable gain
({{ref:s-what-stations-buy-map}}, {{ref:s-deliberate-siting-tested-dense}}). And more cities of the
kind the panels already hold: what would help is dense tropical networks.
