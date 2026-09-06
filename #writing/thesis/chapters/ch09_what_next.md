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

**Do not expand the local network as a way of improving this model, and the redundancy starts
earlier than the ladder's rungs suggest.** Section 7.2 sweeps the station count from one to
eight: a single station buys {{claim:stn.one_gain}} per cent, the second adds
{{claim:stn.second_adds}} percentage points paired within city, and no count between two and
eight beats one station by more than {{claim:stn.max_extra}}. **One local observation captures
essentially everything a city-mean model can extract from local observation**, which makes this
the most estimator-robust result in the study and also the cheapest recommendation in it.

Two qualifications travel with it. This concerns monitors as networks actually place them, and a
campaign designed across land-use contrast is a different proposition, recommended below for a
different reason. And a pair buys something the ladder does not score: a second sensor is what
makes a between-sensor comparison possible, which is how the calibration checks of Chapter 7 were
obtained at all. The advice is that a second station does not improve the model, not that it is
worthless.

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
experiment, and the registered null explicitly does not exclude it finding something. Section 9.7
sets that campaign out in full, because it is the recommendation this thesis is most likely to be
acted on and the one that most needs to be defensible.

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
at {{claim:phase1.best_radius_km}} kilometres, which is coarser than the kilometre cell the model
reports on. Read with
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

## 9.7 A network for Kandy, and why these sites rather than the obvious ones

Everything above says what to buy. This says where to put it, because the two questions have
different answers and the second is where a recommendation usually becomes unfalsifiable.

### What the campaign is for, and what it is deliberately not for

**It is not for making the map finer.** Chapter 8 measured that a tenfold refinement of the grid
moves the paired-site ratio by {{claim:s1.paired_delta_on_refinement}}, and Section 8.5 bounds
what a learned pattern adds over a single free raster. A campaign sold as increased resolution
would be spending against results this thesis already has.

It is for four things: anchoring the level, where three of four independent records sit below the
model and one matches; measuring the within-cell distribution, which Chapter 8 argues is the
well-posed quantity and the larger one; testing the flow physics the model imposes and has never
validated, meaning the nocturnal drainage sink and the confinement term; and establishing what
susceptible people actually breathe, which is a different question answered at different places.

⚠ The campaign was conceived with a fifth purpose, testing whether the spatial ceiling is a
sampling artefact, and that purpose does not survive its own power calculation. The subsection
below the figures explains why, because the finding is more useful than the campaign would have
been.

### The measurement that determines the design

The fine emission surface spans a factor of sixty-five from its tenth to its ninetieth percentile
across the domain. **The existing fixed records sit between the
{{claim:net.existing_pct_lo}}st and hundredth percentile of that range.** The entire lower
{{claim:net.existing_pct_lo}} per cent is unsampled, and one of the two low-cost sensors lies
outside the modelled domain altogether. A network cannot recover a gradient it never straddles,
and this is the most likely reason six searches for spatial structure found none.

### Sampling the physics, not only the sources

A design stratified on emissions samples where the sources are and learns nothing about what the
atmosphere does with them. The sites are therefore selected to span flow as well as emission.

{{fig:network}}

**Nocturnal drainage.** Cold air runs downslope after sunset and pools. The diagnostic wind field
varies threefold in nocturnal speed across this domain, and its convergence marks where that air
accumulates. The model predicts a sink down-valley of the core and no instrument has ever tested
that prediction.

**Confinement and inversion.** The depth of a cell below its surroundings is what traps a
nocturnal inversion, and the model's confinement term is built from it and has never been
validated. Sky view factor would be the natural second covariate for the radiative cooling that
forms an inversion; measured on this domain it is very nearly constant, so it is dropped rather
than carried as a covariate that would dilute the others.

**The vertical gradient, which is the axis nobody samples.** Section 5.5 records that the
dynamic-transport null was diagnosed as a data problem rather than a physics problem: monitored
stations worldwide sit on the valley floor and never straddle the floor-to-ridge gradient, and
the one panel city with several hundred metres of station relief showed the expected signs. Kandy
has {{claim:kandy.relief_m}} metres of relief inside the domain. A deliberate transect from
{{claim:net.vertical_lo}} to {{claim:net.vertical_hi}} metres above the local valley floor is the
single most valuable physical addition available here, and it is a stratum of its own rather than
something left to chance.

**Logistics enters as a constraint and never as an objective.** Only
{{claim:net.cells_feasible}} of the domain's {{claim:net.cells_total}} cells,
{{claim:net.feasible_pct}} per cent, are close enough to a road to be serviced, and candidates
outside that set are removed before the design is optimised. Making access an objective rather
than a constraint is precisely how convenience sampling happens, and it is what this design
exists to avoid.

### The five strata

{{tbl:T9_2}}

They are separate because they answer different questions, and because **a site used to fit a
model cannot honestly validate it.** The receptor stratum in particular is chosen for who is
present rather than for what it would teach a model, and is held out of all fitting.

### Why these sites and not the ones a programme would otherwise choose

Proposing a design and asserting it is good is not an argument. Five designs were built on the
same candidate grid with the same covariates and scored on the same measures, including the two
a programme would most plausibly choose instead.

{{fig:networkwhy}}

**The textbook criterion endorses the convenience sample.** D-efficiency, the standard measure of
how precisely a design estimates a regression's coefficients, rates the conventionally road-sited
network at {{claim:net.deff.road}} and the existing Kandy network at {{claim:net.deff.existing}},
against {{claim:net.deff.proposed}} for the proposed design. **It ranks the two networks already
known to produce nulls above the one built to break them.** The road-sited design earns that
score while sampling {{claim:net.cover.road}} percentile of the emission gradient, because
D-efficiency rewards spread on the remaining covariates and is indifferent to collapse on the one
that matters.

The proposed design wins the measures that match the campaign's purpose. It spans
{{claim:net.cover.proposed}} percentiles of the gradient against {{claim:net.cover.existing}} for
the existing network, and its covariate distribution sits {{claim:net.ks.proposed}} from the
domain's against {{claim:net.ks.random}} for a random draw and {{claim:net.ks.road}} for the
conventional one.

**The cost is real and is stated rather than buried.** The design gives up
{{claim:net.deff_cost_pct}} per cent of D-efficiency against a D-optimal alternative, which puts
it below a random draw on that measure alone. The justification is not that the criterion is
wrong in general. It is that D-efficiency is defined relative to an assumed model, this thesis is
a record of that assumption failing six times, and the campaign exists to find out whether the
assumption can be rescued by better sampling. Buying coefficient precision for a model that does
not work would be buying the wrong thing.

**The number of sites is set by where the design stops paying**, not by a budget, and the
saturation point is a range rather than a value. Between {{claim:net.saturation_lo}} and
{{claim:net.saturation_hi}} sites the representativeness measure moves by less than its own
seed-to-seed standard deviation of {{claim:net.saturation_seed_sd}}, so specifying one of those
counts rather than the other is not supported by the curve. Below that range the loss is real:
cutting to eight costs {{claim:cost.ks_loss_pct_8}} per cent and cutting to six costs
{{claim:cost.ks_loss_pct_6}} per cent. Averaging over five random restarts is what makes this
readable, because a single restart produces a curve with a knee that is not there.

### The campaign cannot answer the question it was designed around

The design began from an assumption worth testing: that deliberate siting could break a ceiling
convenience siting could not. Registering the analysis [OSF ad3py] meant computing, in advance,
what the campaign could actually see. **The answer disqualifies its own headline question.**

Beating the benchmark rank correlation of {{claim:phase1.best_rho}} that a single free raster
already achieves would require, with {{claim:camp.n_fit}} sites available to fit a spatial
pattern, a gain of between {{claim:camp.h1_gain_lo}} and {{claim:camp.h1_gain_hi}} depending on
how far the campaign pattern departs from the benchmark predictor. The panel study this campaign
was meant to follow up resolved a gain of {{claim:camp.panel_limit}}. **Matching that in one city
would need on the order of a hundred to three hundred fitting sites**, against the
{{claim:camp.n_fit}} proposed.

That is not a shortfall to note in a limitations paragraph. It means a campaign of this size
**cannot settle whether the spatial ceiling is a sampling artefact**, and proposing it on that
basis would repeat, with instruments and public money, the error Chapter 5 documents: an
experiment that cannot see the effect it seeks, reporting its silence as evidence.

**The spatial test is therefore demoted to exploratory before deployment**, reported with its
bound attached, and the campaign is not to be described as resolving the spatial question under
any outcome.

**What the campaign is well powered for is the physics and the level**, and those become what it
is for. The paired triplets resolve a within-cell ratio to a factor of
{{claim:camp.h2_ratio_7d}} after a single week, against competing predictions of
{{claim:net.pair_contrast_hi}} from the model and {{claim:spatial.paired_obs_ratio}} from the one
existing observation, so that test is decisive almost immediately and
its power comes from hours averaged rather than from sites installed. The drainage prediction is
a sign test whose unit is the night rather than the site, needing the down-valley sink to exceed
the core on {{claim:camp.h4_nights90}} per cent of ninety nights. And one reference instrument
settles the level discrepancy on its own.

The vertical transect is demoted for the same reason as the spatial test: at five sites only a
correlation of {{claim:camp.h3_vertical_mde}} or larger is visible, which is close to a perfect
monotone relationship, so it is registered as exploratory and adding transect sites is the
cheapest way to make it confirmatory later.

This is what a pre-registration is for, and it is the second time in this thesis that computing a
detection limit in advance changed what was worth doing rather than merely how it would be
reported. The first time, in Chapter 8, it converted five uninformative nulls into one bounded
claim. This time it stopped a campaign being sold for something it could not deliver, and it did
so while the cost of changing course was still a paragraph.

### What it costs, and where the cost actually sits

A recommendation without a price is not a recommendation, and the price here has a shape worth
knowing.

The low-cost network is **{{claim:cost.n_lcs}} units plus {{claim:cost.spares}} spares**, at a
published vendor price of {{claim:cost.lcs_unit_usd}} US dollars each, so
**{{claim:cost.lcs_total_usd}} dollars** in total. The reference anchor is the other line, and
public statements put a regulatory-grade instrument at {{claim:cost.ref_lo_usd}} to
{{claim:cost.ref_hi_usd}} dollars, which is a range from a published position rather than a
quote. The instrument subtotal is therefore **{{claim:cost.total_lo_usd}} to
{{claim:cost.total_hi_usd}} dollars**, and everything else, meaning mounting, power,
connectivity, import duty, labour and a year of servicing, is left as a line item with no unit
price, because none is published for Sri Lanka and a number typed there would be a guess.

Two consequences follow, and the second is the useful one.

**The anchor dominates, and it may not be a purchase.** It costs between one and four times the
entire low-cost network. The national environmental authority has granted this project access in
principle to a Kandy regulatory station carrying hourly concentration and full meteorology,
subject to a formal agreement. If that completes, the largest line in the budget becomes a letter.

**And the obvious economy is not worth making.** The design stratum lost most of its
justification when the spatial hypothesis was demoted, which invites cutting it. Cutting it from
twelve sites to ten saves {{claim:cost.design_saving_usd}} dollars, under three per cent of the
low-end subtotal. At this unit price no plausible re-scoping of a low-cost network changes the
shape of the budget. The effort belongs on the agreement, not on trimming sensors.

### What survives of the design stratum's justification

Its main purpose is gone and two smaller ones remain, one of which was not the original
intention and is stated as such rather than presented as foresight.

It still serves the exploratory spatial test, reported with its bound.

**And it would make Kandy the only deliberately sited city in a panel of
{{claim:frame.cities}} convenience samples.** Every city in the frame that produced this
thesis's spatial nulls was sited for compliance and access. One city sited for contrast is a
different kind of observation, and it is worth more to the multi-city frame than to Kandy itself.
That justification was arrived at after the original one failed, which is the honest way to
describe it.

### What this design cannot do

It cannot narrow the intervention bound of Section 7.10, which runs from
{{claim:chem.intervention_lo}} to {{claim:chem.intervention_hi}} per cent and needs filter
sampling and chemical analysis rather than optical particle counters.

It under-samples residential biomass burning. The design stratifies on a surface built from road
network centrality, and the source apportionment of Chapter 3 attributes 14.1 per cent of mass to
biomass burning against 7.6 per cent to traffic [@Seneviratne2017]. A source that is spatially
decoupled from roads is under-represented by construction, and the honest response is to add
residential sites on that ground rather than to pretend the proxy covers them.

The receptor layer is drawn from a volunteer map whose completeness cannot be measured from
itself, so {{claim:net.receptors_mapped}} is a lower bound and a missing school is invisible.

And outdoor workers, who are among the most exposed people in the city, are not in the design at
all, because they have no fixed location. Reaching them needs personal or mobile sampling, which
is a different instrument and a different protocol. Their absence is a gap in this plan rather
than a judgement that they matter less.

## 9.8 What would not help

Stated because these are the proposals most likely to be made.

**A larger model.** Chapter 5 records several architectures of increasing capacity, none of
which recovered information that was not in the inputs.

**A finer grid**, for the reason given in Section 9.4.

**More monitors in the same city, sited as networks conventionally site them**, for the reason
given in Section 9.1. ⚠ This is not an argument against the campaign of Section 9.7. That
campaign is a different proposition precisely because its sites are chosen for contrast rather
than for compliance and access, and the measured redundancy of additional monitors says
nothing about it.

**More cities in the panel**, unless they are chosen to break the class-band association, which
Chapter 2 established cannot be done with the cities that currently publish data.
