# Constants and configuration {#app-constants-configuration}

Values that are configuration rather than measurement. They are wrong only if the model changes,
in which case the code changes with them.

| quantity | value | what it is |
|---|---|---|
| modelled domain | 15 by 15 km | the extent over which the field is delivered |
| reporting resolution | 1 km, hourly | the grid the field is published on |
| solve resolution | {{claim:subgrid.production_res_m}} m | the grid the transport solver runs on |
| fine emission grid | {{claim:subgrid.fine_res_m}} m | the grid the emission surface is computed on |
| coverage | 2019 to 2026 | satellite-anchored to 2023, extension tier thereafter |
| interval level | 90 per cent | nominal coverage of the delivered interval |
| sensorless predictors | {{claim:bud0c.n_features}} | of which {{claim:bud0c.n_geo_features}} are static geography |
| local share floor | {{claim:partition.f_min_parameter}} | the one free parameter in the coherence constraint |
