## The effect of a monitor-trained covariate {#s-effect-monitor-trained-covariate}

The satellite stream was initially a published fused concentration product [@Wei2023]. Products
of that kind are trained on ground monitors, in this case on networks that supply this study's
own panel, and predicted from a feature set that substantially overlaps the tier's other streams.
The stream was therefore not an independent observation and its measured value was a mixture.

The ladder was re-run on raw satellite aerosol optical depth [@Lyapustin2018; @Levy2013], a
radiometric retrieval trained on nothing.

| | fused product | raw retrieval |
|---|---:|---:|
| the satellite rung itself | {{claim:c1.step_fused_ghap}} per cent | {{claim:c1.step_raw_aod}} per cent |
| the rung above it, pooled | {{claim:step.bud0c_bud1}} per cent | {{claim:maiac.step_bud0c_bud1}} per cent |

**The satellite rung barely moves**, by {{claim:c1.fused_excess_pp}} percentage points. The
fused product's apparent value was satellite information that a raw retrieval supplies equally
well, not recycled information inflating its own score. The pre-registered prediction was the
opposite.

The rung above it moves a great deal. The mechanism is clear once seen: a product trained on
a city's monitors already encodes part of what those monitors would tell you, so adding the
monitor appears to buy less. **Contamination does not inflate the contaminated rung, it deflates
the rung above it.** The pre-registered test looked for excess skill in the satellite's own rung,
found none, and would have reported the leakage as immaterial had the ladder not been re-run.

The mechanism plausibly reaches past this thesis, and the claim should be stated at the width the
experiment supports. What was measured is that in this nested construction, contamination by a
covariate trained on the candidate observation showed up as an understatement of the marginal
value of the rung above it, not as an inflation of the contaminated rung itself. Whether that
signature is general to observation-pricing designs is untested here. It is worth stating because
fused products are now the default covariate in this field, and because the diagnostic a careful
analyst would reach for first looks in the wrong place.

The claim needs its boundary stated, and {{ref:s-position-literature-claims-novelty}} states it. That such products leak is
known, and evaluation practice already guards against it [@Just2020]. The addition here concerns
the **signature** of the leak rather than its existence: when the quantity being estimated is the
marginal value of an observation, the contamination surfaces in the neighbouring term, so the
diagnostic that a careful analyst would reach for is the one that cannot see it. The
pre-registered test in this study was that diagnostic, and it returned a clean result on
contaminated data.
