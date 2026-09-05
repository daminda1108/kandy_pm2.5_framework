# Chapter 9. What to build next

The measurement of Chapter 7 was undertaken to answer a practical question, and this chapter
gives the answer. Everything here is ranked by what the evidence says an action is worth rather
than by how appealing it is, and the two orderings differ.

## 9.1 The acquisition ordering, and why it inverts

{{dia:decisiontree}}

**Take the free data first.** Terrain, roads, land cover, vegetation, night lights, population,
reanalysis meteorology and satellite retrievals cost nothing and are available for every city.
Together they buy {{claim:step.geography}} per cent on the ladder, comparable to the first
instrument a city could purchase. A programme that has not exhausted them has not yet earned the
right to complain about lacking monitors.

**Then buy according to latitude band, not according to the global average.**

{{fig:acquisition}}

Pooled across the panel, a regional background station is the largest single gain at
{{claim:step.bud2_bud3}} per cent and two local sensors buy {{claim:step.bud0c_bud1}} per cent.
Within the deep tropical band, which is the band Kandy belongs to, the ordering reverses: local
sensors buy {{claim:maiac.deep_tropical_first2}} per cent against
{{claim:maiac.deep_tropical_background}} per cent for the background, a local advantage of
{{claim:maiac.deep_tropical_local_advantage}} times.

For Kandy specifically, therefore, **the first purchase is a local reference monitor**, and it
would settle two open questions at once: the level discrepancy of Section 7.8, where three of
four independent records sit below the model, and the source-mix question that Chapter 5 records
as having been asserted wrongly for most of this project's life.

**Do not buy the third through eighth monitors.** At {{claim:step.bud1_bud2}} per cent the gain
is indistinguishable from zero, and it is the most estimator-robust result in the study. This is
the acquisition most often proposed and the one the measurement does not support.

{{tbl:T9_1}}

## 9.2 The measurement that would settle the most

Beyond the ranking, three specific observations would each close a question this thesis leaves
open.

**A composition measurement at Kandy.** Section 7.10 established that continental air is more
secondary-rich than marine air, which is the ordering the decomposition requires, using a
composition product that is itself a model. A speciated measurement at the city would convert
that corroboration into a test. It would also settle whether the local increment can be treated
as fresh primary aerosol, which Section 7.10 showed is too simple because stagnation ages local
precursors in place.

**A campaign that sites monitors deliberately across land-use contrast.** Chapter 8 established
that the spatial limit is a change of support rather than a data deficiency, and that a learned
pattern does not beat the best single predictor by more than {{claim:phase1.min_detectable}} on
the frame available. That frame is a convenience sample: regulatory and low-cost networks are
sited for compliance and access. A campaign designed for the question would be a different
experiment, and the registered null explicitly does not exclude it finding something.

**A regional background station.** Even though it ranks second for Kandy, the background rung's
measured gain is partly an artefact of the proxy used for it, as Section 7.2 stated. A genuine
regional station is the only way to establish how much of that gain is regional information and
how much is more of the same network.

## 9.3 The construction step most worth revisiting

One finding in this thesis points at a specific line of code rather than at an instrument.

{{fig:dispersion}}

The dispersion solver was built to place the local increment by redistributing an emission
surface through terrain-steered flow. Scored against held-out stations it **removes** rank
correlation, taking the raw emission surface from {{claim:r2.rho_emission_surface}} down to
{{claim:r2.rho_with_atransport}} and improving only {{claim:r2.cities_improved}} of ten cities.
That result now holds on two independently selected sets of cities.

The implication is narrow and actionable. The benchmark for any replacement is not the delivered
field's {{claim:r2.rho_with_atransport}} but the undispersed surface's
{{claim:r2.rho_emission_surface}}, and a construction that simply declined to redistribute would
already be better than the one shipped. Chapter 8 argues that the placement problem is
information-limited; this result says that the current construction is not even reaching the
limit that the information allows.

## 9.4 What the radius result implies for resolution

{{fig:radius}}

Predictor skill rises with the radius of the buffer over which a predictor is measured, and peaks
at 2.4 kilometres, which is coarser than the kilometre cell the model reports on. Read with
Chapter 8's finding that within-cell spread exceeds between-cell spread, the band of usable
spatial information is bounded from both sides.

The consequence for anyone building a product of this kind is uncomfortable and worth stating
plainly. **Increasing resolution is not the improvement it appears to be.** A finer grid does not
recover the sub-grid variation, because that variation is not encoded in any available covariate,
and it moves the reporting scale further from the scale at which the predictors carry
information. The registered refinement test of Section 8.3 measured exactly this and found a
tenfold refinement in area worth {{claim:s1.paired_delta_on_refinement}} on the paired-site
ratio.

A more useful direction is the opposite one: report the within-cell distribution rather than a
cell value, which Chapter 8 shows is both well-posed and the larger of the two quantities.

## 9.5 What would make the temporal model better

Three items, in decreasing order of what the evidence supports.

**Precipitation in the forecast drivers.** The current driver set for the forecast tier contains
no precipitation at all, which is a structural gap rather than a measured deficiency. Wet removal
is one of the principal loss processes for particulate matter and the model is currently blind to
it in that mode.

**A per-lead skill curve.** The forecast tier is presented as a demonstration rather than as a
validated product, and it will remain so until skill is reported separately at each lead time.
The current single widening factor applied across all leads is a placeholder.

**A second driver source.** Everything the model knows about the atmospheric state comes from one
reanalysis family. A second source would allow the driver contribution to be separated from the
particular reanalysis it came from, which no result in this thesis currently does.

## 9.6 What this thesis suggests about method, beyond this problem

Two of the findings here are not about air quality.

**A value-of-information analysis must not price observations against a covariate trained on
those observations.** Section 7.5 showed that such contamination deflates the rung above it
rather than inflating its own, so a test that looks for excess skill in the contaminated stream
finds nothing and reports the leakage as immaterial. Fused products are now the default covariate
in this field, and this thesis is not aware of prior work that reports the effect.

**A null result without a stated detection limit converts a limitation of the experiment into a
claim about the world.** Chapter 5 records five nulls that did this and one that did not, and the
difference between them is the difference between a belief and a bounded claim. The cost of
stating a detection limit in advance is a power calculation. The cost of not stating one, in this
project, was four months.

## 9.7 What would not help

Stated because these are the proposals most likely to be made.

**A larger model.** Chapter 5 records several architectures of increasing capacity, none of
which recovered information that was not in the inputs.

**A finer grid**, for the reason given in Section 9.4.

**More monitors in the same city**, for the reason given in Section 9.1.

**More cities in the panel**, unless they are chosen to break the class-band association, which
Chapter 2 established cannot be done with the cities that currently publish data.
