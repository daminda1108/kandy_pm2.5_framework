## Interval calibration {#s-interval-calibration}

An interval that is honest about its own uncertainty has to be checked against observations, not
merely constructed. The check available at Kandy is narrow, because the city has only two low-cost
sensors, but it is the check that exists. The figure below compares the delivered interval against
what those sensors recorded, hour by hour. What to look for is not simply whether the observations
fall inside the band, but where they fall when they land outside it. An interval that is too narrow
misses on both sides in roughly equal numbers. An interval that is correctly sized but wrongly
positioned misses almost entirely on one side, and that distinction decides whether the problem is
the width or the centring. The figure shows the second pattern.

{{fig:uncertainty}}

The interval is nominal at ninety per cent rather than guaranteed at it: conformal calibration
earns its coverage under exchangeability [@Vovk2005; @Angelopoulos2023], which strongly
dependent environmental series do not satisfy, so what follows is an empirical check and not a confirmation of a theoretical
property. It covers {{claim:kandy.cov90}} per cent of observations at
the two sensors, which read alone suggests the intervals are too narrow. {{ref:s-comparing-areal-model-point}} gave the
diagnosis: the misses are one-sided, {{claim:kandy.miss_below}} per cent below against
{{claim:kandy.miss_above}} per cent above, with a median offset of
{{claim:kandy.median_offset}} micrograms per cubic metre. Removing each sensor's own offset
restores coverage to {{claim:kandy.cov90_recentred}} per cent.

The width was right and the centring was wrong, and the cause is the change of support of
{{ref:ch-model-stops}} rather than a failure of the calibration procedure.

### External identification of the representativeness error {#s-external-identification-representativeness-error}

That answer is complete for the delivered interval and incomplete for the observation model that
{{ref:s-comparing-areal-model-point}} specifies. The specification writes a point measurement as the areal field plus an
instrument offset plus an error with two parts, a measurement term and a representativeness term
covering sub-grid variability the model cannot resolve. The implementation estimates the second
from the local variability of the field itself. That is elegant, and it is circular: the model is
being asked how wrong its own unresolved spatial structure is, and a model that understates
sub-grid variability would understate this term in the same proportion.

The quantity can be identified without the model. Wherever two or more instruments fall inside a
single model cell, the spread between them measures the point-versus-area error directly, with no
field consulted and no pattern assumed. The panel contains {{claim:srep.panel_cells}} such cells
holding {{claim:srep.panel_stations}} instruments across {{claim:srep.panel_cities}} cities, and
the Kandy transect of {{ref:ch-model-stops}} contributes {{claim:srep.kandy_cells}} more.

| source | within-cell coefficient of variation | times the model |
|---|---:|---:|
| panel instruments sharing a cell | {{claim:srep.panel_cv}} | {{claim:srep.ratio_panel}} |
| Kandy transect sites sharing a cell | {{claim:srep.kandy_cv}} | {{claim:srep.ratio_kandy}} |
| the model estimator at the same places | {{claim:srep.model_cv}} | 1.0 |

The estimator is too small by a factor of {{claim:srep.ratio_panel}} on the panel and by at least
{{claim:srep.ratio_kandy}} at Kandy. The Kandy figure is a lower bound, because three of its seven
sites were censored at an upper sampling limit and censoring can only shrink an observed spread,
so the bias runs toward the model and cannot have produced the result.

Two things follow, and they are different. The delivered interval is unaffected, because its width
comes from the temporal anchor's conformal quantiles, not from this term, and the coverage
figures above already show that width to be right for an areal quantity. What is affected is the
observation model, which the specification requires to exist before any regulatory record is
ingested. Had this term been used as written, the first point-level interval built against a real
Kandy measurement would have been too narrow by a factor of three or more, and the resulting
apparent over-confidence would have looked like an error in the field rather than an error in the
comparison. The term must be taken from co-located instruments. The delivered interval is
calibrated for an areal quantity, and it understates point-level uncertainty.
