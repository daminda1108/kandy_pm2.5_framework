## External identification of the representativeness error {#s-external-identification-representativeness-error}

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

On the panel the estimator is too small by a factor of {{claim:srep.ratio_panel}}. That figure
compares the long-term means of stations that share a cell, so it assumes those means are
comparable: stations whose records cover different periods, or that differ in siting or instrument,
contribute spread that is not within-cell variation. It is therefore evidence that the implemented
term is too small, not a precise measurement of how much.

The Kandy figure, a factor of {{claim:srep.ratio_kandy}}, is weaker evidence and is not a lower
bound. Three of its seven sites were censored at an upper sampling limit, which shrinks the observed
spread, but the sites were sampled on different days and measured PM10, and day-to-day variation
widens the spread ({{ref:s-test-holds-support-fixed}}). The two biases run in opposite directions
and the net direction is not known, so the Kandy figure is a strongly confounded diagnostic of
possible within-cell heterogeneity, not an estimate of the point-to-cell error.

Two things follow, and they are different. The delivered interval is unaffected, because its width
comes from the temporal anchor's conformal quantiles, not from this term. What is affected is the
observation model, which the specification requires to exist before any regulatory record is
ingested. Had this term been used as written, the first point-level interval built against a real
Kandy measurement would have been too narrow, by a factor of about two to three on the panel's
evidence, and the resulting
apparent over-confidence would have looked like an error in the field rather than an error in the
comparison. The term must be taken from co-located, time-aligned instruments. The delivered
interval describes an areal quantity, and it understates point-level uncertainty.
