# Constants and configuration {#app-constants-configuration}

Values that are configuration rather than measurement. They are wrong only if the model changes,
in which case the code changes with them.

| quantity | value | what it is |
|---|---|---|
| modelled domain | 15 by 15 km | the extent over which the field is delivered |
| reporting resolution | 1 km, hourly | the grid the field is published on |
| solve resolution | {{claim:subgrid.production_res_m}} m | the grid the transport solver runs on |
| fine emission grid | {{claim:subgrid.fine_res_m}} m | the grid the emission surface is computed on |
| study period | 2019 to 2023 | the satellite-anchored years on which every result in this thesis rests |
| extension tier | 2024 to 2026 | delivered by the software with a driver-anchored level; not evaluated here and not part of the evidence |
| interval level | 90 per cent | nominal coverage of the delivered interval |
| sensorless predictors | {{claim:bud0c.n_features}} | of which {{claim:bud0c.n_geo_features}} are static geography |
| local share floor | {{claim:partition.f_min_parameter}} | the one free parameter in the coherence constraint |
| marine background floor | {{claim:config.b_marine}} micrograms per cubic metre | background on six-hourly arrivals classed as marine ({{ref:s-regional-background}}) |
| confinement amplitude κ | {{claim:config.kappa}} | fractional enhancement per standard deviation of confinement at full trapping; a prior, not fitted |
| effective ridge height | {{claim:config.h_ridge_m}} m | boundary-layer height above which confinement is switched off |
| conformal strata | month by six-hour block | the cells in which the anchor's interval is calibrated |
