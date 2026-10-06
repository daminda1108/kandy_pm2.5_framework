## Resolution tested and refuted {#s-resolution-tested-refuted}

The obvious diagnosis is that one kilometre is too coarse. That diagnosis was pre-registered as
a hypothesis and tested.

The model's own emission surface is computed at {{claim:subgrid.fine_res_m}} metres and
aggregated to {{claim:subgrid.coarse_res_m}} metres before anything is rendered, so a finer field
already exists inside the build. At the paired microsites the fine surface gives a ratio of
{{claim:subgrid.paired_efine_ratio}} times in the correct direction, where the delivered product
gives unity. That is a real signal, and the registered hypothesis was that dispersing it at
{{claim:subgrid.fine_res_m}} metres would recover a material fraction of the observed contrast.

**It does not.** Running the calibrated terrain solver [@Forthofer2014] at
{{claim:subgrid.fine_res_m}} metres,
forced with the survey's own midday climatology and with nothing fitted:

| | production, {{claim:subgrid.production_res_m}} m | fine, {{claim:subgrid.fine_res_m}} m |
|---|---:|---:|
| paired-site ratio | {{claim:s1.paired_production_238m}} | {{claim:s1.paired_fine_94m}} |
| rank across the survey | {{claim:s1.rank_production_238m}} | {{claim:s1.rank_fine_94m}} |

A tenfold refinement in area moves the paired ratio by
{{claim:s1.paired_delta_on_refinement}} and the rank correlation by
{{claim:s1.rank_delta_on_refinement}}. Registered predictions
{{claim:s1.predictions_refuted}} are refuted. Resolution is not the binding constraint, and per
the registration the question is treated as closed rather than re-scoped.
