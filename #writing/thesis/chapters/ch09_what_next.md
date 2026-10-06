# Chapter 9. What to measure next

The measurement of Chapter 7 was undertaken to answer a practical question, and this chapter
gives the answer. Everything here is ranked by what the evidence says an action is worth rather
than by how appealing it is, and the two orderings differ.

## 9.1 The measurement-priority ordering

The practical question behind this thesis is what a city with almost no monitoring should obtain
first. The answer is not a single instrument, because it depends on what the city already has and
on which group of cities it resembles. The figure below sets that out as the decision it actually
is: start from what is already available at no cost, then branch on whether the city has any local
observation at all, and then branch again on the group it belongs to, because Section 7.3 shows the
ordering reverses between those groups. Each endpoint names the measurement to obtain and the
section that prices it. The diagram encodes ordering only. It does not encode cost, and the
distinction is the subject of the paragraph that follows.

{{dia:decisiontree}}

This section ranks measurements by the marginal predictive value defined in Section 7.2, and that
is not the same thing as a procurement optimum. No cost enters the ladder, and neither does
maintenance, calibration burden, instrument reliability, compliance value, temporal or spatial
coverage, nor the consequence of a decision made on the output. What follows therefore **informs**
procurement rather than optimising it: it says which measurement this model can use most, not
which purchase a programme should make once its own costs and obligations are counted. The
distinction matters most where the two could diverge, and a reference-grade instrument is the
clearest case: no rung of the ladder priced one, the measurement-design argument below favours it,
and Chapter 2 notes that it costs tens of thousands of dollars to install.

**Take the free data first.** Terrain, roads, land cover, vegetation, night lights, population,
reanalysis meteorology and satellite retrievals cost nothing and are available for every city.
Together they buy {{claim:step.geography}} per cent on the ladder, comparable to the first
instrument a city could purchase. A programme that has not exhausted them is leaving the cheapest
available improvement unused.

Then buy according to the group of cities the target belongs to, not according to the global
average.

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

The scope of that recommendation should be stated exactly, because it is the sentence most likely
to be lifted out of this thesis. What is established is that **within this panel, the
deep-tropical group is the closest available analogue to Kandy, and within that group a local
observation outranks the background stand-in.** It is not established that tropical cities in
general should buy local monitors first. The group contains thirteen cities, band travels with
instrument class and five other things, and Section 7.3 sets out why a latitude label is not a
mechanism. A city that resembles Kandy in the ways this panel can measure should read the band
row; a city that does not has been given a method for pricing its own options, which is the more
transferable product of the two.

**And the ordering holds for one loss, not for all of them.** Section 7.2.1 re-scores the ladder
under four scoring rules. Under daily and absolute error the local advantage is
{{claim:loss.inv.rmse}} and {{claim:loss.inv.mae}} points. On days in the observed top decile it
is {{claim:loss.inv.tail}} points and on exceedance at the World Health Organization guideline
{{claim:loss.inv.exceedance}} points
[{{claim:loss.inv.exceedance.lo}}, {{claim:loss.inv.exceedance.hi}}], both favouring the
background proxy, with the exceedance interval excluding zero. **A programme whose purpose is a
daily city-mean field should buy the local observation first. A programme whose purpose is
exceedance detection or health alerting should not**, and the background series is worth
{{claim:loss.bg.tail}} per cent on episode days, its largest value under any loss. Chapter 2 names
both purposes, so the ordering has to be stated with its loss attached and not as a single
recommendation.

Two separate arguments then point at a reference-grade instrument, and they should not be
merged. The ladder measured two low-cost sensors, so it establishes that a local observation
outranks a regional one in this band. It does not establish the value of a reference monitor,
which was never a rung. The case for making that local observation reference-grade stands on its own as a
measurement-design argument. A reference instrument would settle the level discrepancy of
Section 7.8, where three of four independent records sit below the model and the one that matches
carries an undocumented instrument. It would also anchor the calibration of any low-cost sensors
deployed afterwards, against which their performance can be assessed on a published protocol
[@Duvall2021]. That case is strong, and the
{{claim:maiac.deep_tropical_first2}} per cent figure is not evidence for it.

Do not expand the local network as a way of improving this model, and the redundancy starts
earlier than the ladder's rungs suggest. Section 7.2 sweeps the station count from one to
eight: a single station buys {{claim:stn.one_gain}} per cent, the second adds
{{claim:stn.second_adds}} percentage points paired within city, and no count between two and
eight beats one station by more than {{claim:stn.max_extra}}. **For a daily city mean under this
model, on networks sited as these are, one local observation captures essentially everything a
further local observation could add**, which makes this the most estimator-robust result in the
study. The qualifiers are load-bearing and belong inside the sentence rather than after it: the
quantity is a daily city mean and not an episode or an exceedance, the model is this one, and the
stations sit where each city's programme happened to put them. Section 7.2.1 shows the finding
surviving three further losses, including the two that ask about episodes. Declining to buy something is also the only
recommendation here whose cost consequence is unambiguous, since no cost model is needed to
price an instrument that is not purchased.

Two qualifications travel with it. This concerns monitors as networks actually place them, and
whether placing them deliberately across land-use contrast changes the spatial picture is a
separate question, which Section 8.5 tests on the panel's own dense networks. And a pair buys something the ladder does not score: a second sensor is what
makes a between-sensor comparison possible, which is how the calibration checks of Chapter 7 were
obtained at all. The advice is that a second station does not improve the model, not that it is
worthless.

{{tbl:T9_1}}

## 9.2 The measurement that would settle the most

Beyond the ranking, two specific observations would each close a question this thesis leaves
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

A regional background station. It ranks second for Kandy rather than first, and the reason to
want one anyway is that it would close a question the panel can only bound. Section 7.2 rebuilt
the background from a donor city the target never sees and recovered
{{claim:donor.gain_reproduced_pct}} per cent of the gain, which establishes that the rung carries
regional information rather than more of the same network. It does not divide the residual
quarter, because donor distance is confounded with independence, and in Kandy's own band recovery
falls to {{claim:donor.reproduced_deep_tropical}} per cent on
{{claim:donor.km_deep_tropical}}-kilometre donors. A real station five to fifty kilometres out
would separate the two in a way no re-analysis of the existing panel can.

The nearest candidate donor was tested and refused. Colombo lies {{claim:donor.colombo_km}}
kilometres away, is reference grade, and its record was already held; daily correlation with Kandy
is {{claim:donor.colombo_r}} against a benchmark of {{claim:donor.benchmark_median_matched}} at comparable
separation, which is the weakest pairing available. The central highlands decouple the coastal
plain from the interior. That conclusion has since been reached independently, from a different
quantity, by [@Senarathna2026]: sensor calibration models fitted in Colombo lose effectiveness when
applied at Kandy, and the authors attribute it to the two cities lying in different climatic
zones. Two unrelated measurements, one conclusion, and Colombo does not become a Kandy donor by
being close.

**A network sited deliberately across land-use contrast is not on this list, and the reason is a
measurement.** Chapter 8 established that the spatial limit is a change of support rather than a
data deficiency, and that a learned pattern does not beat the best single predictor by more than
{{claim:phase1.min_detectable}} on the frame available. That frame is a convenience sample, since
regulatory and low-cost networks are sited for compliance and access, so the natural proposal is
to site monitors on purpose. Section 8.5 tested that proposal on the panel's own dense networks:
paired within city, deliberate siting scores {{claim:site.paired_median}} against convenience
siting [{{claim:site.paired_lo}}, {{claim:site.paired_hi}}]. The interval does not exclude a
modest advantage, so this is a bound and not a refutation, but it leaves no measured case for
ranking deliberate siting as an observation this model would use.

One further item belongs here even though it is an analysis and not an observation, because
it needs no new data and it would sharpen the thesis's most policy-relevant result. Section 7.3
reports that the measurement-priority ordering differs between bands and states that latitude is
a label rather than a mechanism. The candidate mechanism is the amplitude of the regional
seasonal cycle, which is high in the temperate bands and weak in the deep tropics, and which is
computable for every city already on disk. Sorting the panel by that amplitude directly, and
asking whether the ordering follows the amplitude or the latitude, would convert a stratified
association into a tested explanation. It should be registered before it is run, for the reason
Section 9.6 gives.

## 9.3 The construction step most worth revisiting

One finding in this thesis points at a specific line of code rather than at an instrument. It is
the result drawn in {{fig:dispersion}}, in Chapter 8.

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

## 9.4 Implications of the radius result

A predictor of within-city pattern has to be measured over some area around each point, and the
size of that area is a free choice that is usually made without comment. Testing it directly
produces the most surprising result in this thesis. The figure below scores the best single freely
available predictor at a range of buffer radii, from a few hundred metres up to several kilometres,
against held-out monitors. If sub-kilometre structure were the thing being recovered, skill would
be highest at the smallest radius and fall away as the buffer widened. It does the opposite. Skill
rises with radius and peaks at {{claim:phase1.best_radius_km}} kilometres, which is coarser than
the cell the model reports on, and Section 9.4 draws the consequence for resolution.

{{fig:radius}}

Predictor skill rises with the radius of the buffer over which a predictor is measured, and peaks
at {{claim:phase1.best_radius_km}} kilometres, which is coarser than the kilometre cell the model
reports on. Read with
Chapter 8's finding that within-cell spread exceeds between-cell spread, the band of usable
spatial information is bounded from both sides.

The consequence for anyone building a product of this kind is uncomfortable and worth stating
plainly. Increasing resolution is not the improvement it appears to be. A finer grid does not
recover the sub-grid variation, because that variation is not encoded in any available covariate,
and it moves the reporting scale further from the scale at which the predictors carry
information. The registered refinement test of Section 8.3 measured exactly this and found a
tenfold refinement in area worth {{claim:s1.paired_delta_on_refinement}} on the paired-site
ratio.

A more useful direction is the opposite one: report the within-cell distribution rather than a
cell value, which Chapter 8 shows is both well-posed and the larger of the two quantities.

## 9.5 Improvements to the temporal model

Three items, in decreasing order of what the evidence supports.

**Precipitation in the forecast drivers.** The current driver set for the forecast tier contains
no precipitation at all, which is a structural gap, not a measured deficiency. Wet removal
is one of the principal loss processes for particulate matter and the model is currently blind to
it in that mode. The ladder's driver set is a different case: it already held a daily rainfall
total that was never used, and Section 7.2 reports the registered test of adding it, which found
nothing.

A per-lead skill curve. The forecast tier is presented as a demonstration rather than as a
validated product, and it will remain so until skill is reported separately at each lead time.
The current single widening factor applied across all leads is a placeholder.

A second driver source. Everything the model knows about the atmospheric state comes from one
reanalysis family. A second source would allow the driver contribution to be separated from the
particular reanalysis it came from, which no result in this thesis currently does.

## 9.6 Methodological lessons beyond this problem

Two of the findings here are not about air quality.

**A value-of-information analysis must not price observations against a covariate that was trained
on those same observations.** Section 7.5 showed that this kind of contamination deflates the rung
above it rather than inflating its own. A test that looks for excess skill inside the contaminated
stream therefore finds nothing, and reports the leakage as immaterial. Fused products are now the default covariate
in this field. That such products leak is established and guarded against in evaluation practice
[@Just2020]; what Section 3.4 argues is unreported is the displaced signature, which is what
makes the obvious diagnostic the wrong one.

A null result without a stated detection limit converts a limitation of the experiment into a
claim about the world. Chapter 5 records five nulls that did this and one that did not, and the
difference between them is the difference between a belief and a bounded claim. The cost of
stating a detection limit in advance is a power calculation. The cost of not stating one, in this
project, was four months.

## 9.7 Approaches that would not help

Stated because these are the proposals most likely to be made.

**A larger model.** Chapter 5 records several architectures of increasing capacity, none of
which recovered information that was not in the inputs.

A finer grid, for the reason given in Section 9.4.

More monitors in the same city, sited as networks conventionally site them, for the reason
given in Section 9.1. Siting them deliberately across land-use contrast instead is a different
proposition, and the measured redundancy of additional monitors says nothing about it; what does
bear on it is Section 8.5, which finds no paired advantage for deliberate siting on the panel's
dense networks.

More cities in the panel, unless they are chosen to break the class-band association, which
Chapter 2 established cannot be done with the cities that currently publish data.

## 9.8 The sentence to carry away

Two statements should survive any summary of this work, and they pull in opposite directions.

**The method is transferable and the ordering it produces is measured.** A city with no monitors
can be told what its next observation is worth, in units of predictive error, on evidence from
forty-eight cities with the target withheld from every fit.

The absolute concentration scale at Kandy is not independently validated. The temporal anchor
is calibrated against the city's own two low-cost sensors, so the external records of Section 7.8
test the modelled lift above an already anchored mean, not the level itself; three of the
four independent point records sit below the model and the one that agrees carries an undocumented
instrument. Nothing in this thesis resolves that, and a reference-grade measurement at Kandy is
the only thing that would. Until one exists, the field should be read as a well-founded relative
and spatial construction on a level that remains open.
