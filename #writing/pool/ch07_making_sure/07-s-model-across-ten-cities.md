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
across the panel. That number means little on its own, because the composition prior carries a seasonal cycle and the
two anchor stations carry their city's, so both were scored in the same way, on the same withheld stations, years and
calendar months. The prior alone reaches a median of {{claim:sb.prior.median}} ({{claim:sb.prior.min}} to
{{claim:sb.prior.max}}), and the model improves on it in {{claim:sb.above_prior}} of the ten cities. The anchor
stations' own monthly climatology reaches {{claim:sb.anchors.median}}, the model {{claim:sb.model.median}}, and the
model is the better of the two in only {{claim:sb.above_anchors}} cities, with a median difference of
{{claim:sb.model_minus_anchors}}. The seasonal agreement is therefore inherited from the anchor stations: the
construction carries it across the city without degrading it and improves on the free prior, but it does not add
seasonal skill beyond what two stations already hold.

Diurnal correlation runs {{claim:scorecard.diurnal_r_lo}} to {{claim:scorecard.diurnal_r_hi}}, a much wider range that
is regime-dependent rather than random, and the same baselines tell the same story. The prior alone carries almost no
daily cycle (median {{claim:sbd.prior.median}}), and the model improves on it in {{claim:sbd.above_prior}} cities by a
median of {{claim:sbd.model_minus_prior}}. The anchor stations' own daily cycle reaches {{claim:sbd.anchors.median}},
against the model's {{claim:sbd.model.median}}, with the model the better in {{claim:sbd.above_anchors}} cities; where
the model fails, as in the city at the bottom of the range, the anchors' own cycle fails with it. Both cycles are
therefore carried across the city from the anchor stations, which is what the construction is designed to do, and both
baselines were added after an external review asked for them. Level bias has a median of {{claim:scorecard.level_bias_median}} per cent. The fine
spatial rank is estimable at {{claim:scorecard.spatial_estimable}} of the ten cities, with a
median of {{claim:scorecard.spatial_rho_median}}.

The best case, a city with a dense network scored at forty stations, is shown in
{{ref:s-ten-city-showcase}} and labelled as the best case rather than as typical.
