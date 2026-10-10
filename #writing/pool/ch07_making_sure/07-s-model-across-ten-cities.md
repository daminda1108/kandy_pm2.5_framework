## The model across ten cities {#s-model-across-ten-cities}

This section scores the complete model, field and all, across the ten valley and basin cities
where it was built with only two anchor stations and scored against the stations withheld from it
({{ref:s-borrowed-ground-truth}}). Three axes are
scored separately: how well the model reproduces the seasonal cycle, how well it reproduces the
daily cycle, and how far its annual level sits from the observed one. The figure below gives all
three for every city, with the axes kept apart rather than combined into a single score. Reading
across a row shows one city's profile; reading down a column shows how consistent the model is on
that axis. The spread down the diurnal column is the result that matters most, and {{ref:s-checks-kandy-carry-weight}}
returns to it.

{{fig:scorecard}}

Three axes are reported separately and never averaged, because averaging a skill percentile
across metrics produces a meaningless middle: an earlier version of this work did exactly that
and reported a model as representative on the strength of two opposite effects cancelling.

Seasonal correlation runs {{claim:scorecard.seasonal_r_lo}} to {{claim:scorecard.seasonal_r_hi}}
across the panel. Diurnal correlation runs {{claim:scorecard.diurnal_r_lo}} to
{{claim:scorecard.diurnal_r_hi}}, which is a much wider range and is regime-dependent rather than
random. Level bias has a median of {{claim:scorecard.level_bias_median}} per cent. The fine
spatial rank is estimable at {{claim:scorecard.spatial_estimable}} of the ten cities, with a
median of {{claim:scorecard.spatial_rho_median}}.

The best case, a city with a dense network scored at forty stations, is shown in
{{ref:s-ten-city-showcase}} and labelled as the best case rather than as typical.
