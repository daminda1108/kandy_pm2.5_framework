## Abstract

Most cities that need a PM2.5 field have no monitors to build or check one with. Models are
built for them anyway, and almost none state what information they would require to be trusted,
or what the next instrument would be worth. That question is not usually well-posed: removing an
input and refitting produces a *different* model, so the difference confounds information loss
with model change.

We formulate an information-tiered decomposition in which the budget is declared per tier and a
lower tier is recoverable **bit-exactly** from a higher one when a stream is withheld. Withholding
becomes a controlled operation, and an ablation becomes a measurement. We then run that
measurement across {{claim:frame.cities}} cities in {{claim:frame.countries}} countries and
{{claim:frame.city_days|,}} city-days, with gates registered before scoring.

Freely available static geography reduces daily RMSE by {{claim:step.geography}} per cent —
comparable to the first local instrument, at every city on Earth for nothing. The first two
local sensors buy {{claim:maiac.step_bud0c_bud1}} per cent; **sensors three through eight buy
{{claim:step.bud1_bud2}} per cent**, a result robust across every estimator tested. A regional
background station buys {{claim:step.bud2_bud3}} per cent, the largest single gain we measure and
the rung most programmes never build. The ordering **inverts by latitude band**: in the deep
tropics local sensors are worth {{claim:maiac.deep_tropical_local_advantage}} times a regional
station, so the pooled recommendation is the wrong recommendation for much of the affected
population.

Two results generalise beyond this model. The measured value of an observation depends on how
well the free data is already exploited — a linear baseline reports the first rung at
{{claim:learner.ridge_linear.step_bud0c_bud1}} per cent against
{{claim:learner.histgbm_shipped.step_bud0c_bud1}} per cent for a non-linear one. And a covariate
trained on ground monitors **under-prices the observations it was trained on**: replacing a
published fused product with raw satellite retrievals leaves the satellite rung unchanged
({{claim:c1.fused_excess_pp}} percentage points) while roughly doubling the measured value of a
local monitor. Fused products are now the default covariate in this field.

We also locate where the model stops. Two sites 300 m apart inside one grid cell differ by
{{claim:spatial.paired_obs_ratio}}-fold in observation and
{{claim:spatial.paired_model_ratio}}-fold in the model, and a pre-registered test shows that
re-running the physics at {{claim:subgrid.fine_res_m}} m does not change that. The limit is one of
definition rather than data: the spread *within* a typical cell
({{claim:s2.within_pixel_p90p10}}) exceeds the spread *between* cells
({{claim:s2.between_pixel_p90p10}}). The model cannot say which street is worse; it can say what
range a cell spans, and we suggest fields of this kind should report it.

The apparatus is demonstrated at Kandy, Sri Lanka — two low-cost sensors, no reference monitor —
and checked against records that played no part in building it.
