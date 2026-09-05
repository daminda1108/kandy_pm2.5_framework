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

For Kandy specifically, therefore, **the first purchase is a local observation rather than a
regional one**. Section 7.3 shows that conclusion survives a paired interval over cities on the
clean satellite stream, favouring local sensors in {{claim:inv.maiac.frac_cities}} per cent of
the band, and that it does **not** survive on the contaminated stream.

**Two separate arguments then point at a reference-grade instrument, and they should not be
merged.** The ladder measured two low-cost sensors, so it establishes that a local observation
outranks a regional one in this band. It does not establish the value of a reference monitor,
which was never a rung. The case for making that local observation reference-grade is a
measurement-design argument standing on its own: a reference instrument would settle the level
discrepancy of Section 7.8, where three of four independent records sit below the model and the
one that matches carries an undocumented instrument, and it would anchor the calibration of any
low-cost sensors deployed afterwards. That case is strong, and the
{{claim:maiac.deep_tropical_first2}} per cent figure is not evidence for it.

**Do not expand to a third through eighth monitor as a way of improving this model.** At
{{claim:step.bud1_bud2}} per cent the gain is indistinguishable from zero, with an upper bound of
{{claim:boot.ghap.pooled.stn3to8.hi}} per cent across resamples of the panel, and it is the most
estimator-robust result in the study. The qualification of Section 7.2 travels with it: this
concerns monitors as networks actually place them, and a campaign designed across land-use
contrast is a different proposition, recommended below for a different reason.

{{tbl:T9_1}}

## 9.2 The measurement that would settle the most

Beyond the ranking, three specific observations would each close a question this thesis leaves
open.

**A composition measurement at Kandy, and this is now the best-argued item on the list.**
Section 7.10 established that continental air is more secondary-rich than marine air, which is
the ordering the decomposition requires, using a composition product that is itself a model. A
speciated measurement would convert that corroboration into a test. Three further things now
depend on it specifically.

It would narrow the intervention bound. The locally emitted primary share currently lies between
{{claim:chem.intervention_lo}} and {{claim:chem.intervention_hi}} per cent, and the width of that
range is set entirely by not knowing how much of the local increment is secondary. This is the
single number a city authority would most want and the one the model cannot supply.

It would make the species-resolved test possible. Section 7.10 reports that test as untested
rather than refuted, because a floor-based estimator on daily modelled composition measures
episodic variability rather than origin, demonstrated by its own negative controls. Measured
speciation at sub-daily resolution would let the same question be asked with an estimator that
can answer it, since the model's background is defined as flat within a day and that is the
structure a floor-based estimator needs in order to mean anything.

And it would settle whether the local increment can be treated as fresh primary aerosol, which
Section 7.10 showed is too simple because stagnation ages local precursors in place.

**A campaign that sites monitors deliberately across land-use contrast.** Chapter 8 established
that the spatial limit is a change of support rather than a data deficiency, and that a learned
pattern does not beat the best single predictor by more than {{claim:phase1.min_detectable}} on
the frame available. That frame is a convenience sample: regulatory and low-cost networks are
sited for compliance and access. A campaign designed for the question would be a different
experiment, and the registered null explicitly does not exclude it finding something.

**A regional background station.** It ranks second for Kandy rather than first, and the reason to
want one anyway is that it would close a question the panel can only bound. Section 7.2 rebuilt
the background from a donor city the target never sees and recovered
{{claim:donor.gain_reproduced_pct}} per cent of the gain, which establishes that the rung carries
regional information rather than more of the same network. It does not divide the residual
quarter, because donor distance is confounded with independence, and in Kandy's own band recovery
falls to {{claim:donor.reproduced_deep_tropical}} per cent on
{{claim:donor.km_deep_tropical}}-kilometre donors. A real station five to fifty kilometres out
would separate the two in a way no re-analysis of the existing panel can.

One further item belongs here even though it is an analysis rather than an observation, because
it needs no new data and it would sharpen the thesis's most policy-relevant result. Section 7.3
reports that the acquisition ordering differs between latitude bands and states that latitude is
a label rather than a mechanism. The candidate mechanism is the amplitude of the regional
seasonal cycle, which is high in the temperate bands and weak in the deep tropics, and which is
computable for every city already on disk. Sorting the panel by that amplitude directly, and
asking whether the ordering follows the amplitude or the latitude, would convert a stratified
association into a tested explanation. It should be registered before it is run, for the reason
Section 9.6 gives.

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
in this field. That such products leak is established and guarded against in evaluation practice
[@Just2020]; what Section 3.4 argues is unreported is the displaced signature, which is what
makes the obvious diagnostic the wrong one.

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
