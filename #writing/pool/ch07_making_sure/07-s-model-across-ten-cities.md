## The model across ten cities {#s-model-across-ten-cities}

The ladder measures what an observation is worth. It does not say how well the model performs, and
those are different questions. This section answers the second one across the ten cities where the
full model was built, rather than the many more cities of the discovery, confirmation and
full-network panels where only the ladder was run. Three axes are
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

{{fig:kathmandu}}

The showcase city is shown because it is the best case and is labelled as such. It reaches a
seasonal correlation of {{claim:ktm.seasonal_r}} and a diurnal correlation of
{{claim:ktm.diurnal_r}} at {{claim:ktm.stations}} stations, with a level bias of
{{claim:ktm.level_bias_pct}} per cent. Its spatial rank, taken from the panel scorecard rather
than from the figure so that one city does not carry two numbers, is
{{claim:scorecard.kathmandu_spatial_rho}}.
