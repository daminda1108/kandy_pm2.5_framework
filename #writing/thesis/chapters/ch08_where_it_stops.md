# Chapter 8. Where the model stops

A model of this kind is usually reported with its skill and a list of caveats. This chapter
reports something more specific: the resolution at which the model stops working, the reason,
and the quantity that survives. The distinction matters because "the data was inadequate" and
"the question was mis-specified" call for entirely different responses, and only one of them is
true here.

## 8.1 The observation that sets the problem

Kandy's within-city gradient is not small. The roadside survey of Chapter 3 recorded
concentrations falling from 110 to 4 micrograms per cubic metre over three hundred metres inside
a single botanical garden [@Elangasinghe2008], and across the whole survey the observed spread is
{{claim:spatial.obs_spread}} times. The delivered field spans {{claim:spatial.model_spread}}
times.

Two orders of magnitude separate them. The natural reading is that the model has failed, and
showing why that reading is wrong is the substance of this chapter.

## 8.2 A test that holds support fixed

The survey contains one pair of sites that isolates the question. The garden entrance and a point
three hundred metres inside it were sampled with the same instrument, over the same three-hour
window, on the same protocol. **They fall inside a single {{claim:subgrid.coarse_res_m}} metre
model cell.** Support is held fixed; only location varies.

| | observed | model as delivered |
|---|---:|---:|
| ratio between the two sites | {{claim:spatial.paired_obs_ratio}} times | {{claim:spatial.paired_model_ratio}} times |

{{fig:paired}}

The model returns exactly unity, for the unavoidable reason that it is being asked about one
pixel twice. The cleanest statement of the limit is that **the model's entire dynamic range
across Kandy is smaller than the difference between two points three hundred metres apart inside
one garden.**

Three limitations belong with that statement rather than after it. The observed values are coarse
particulate and the model is fine particulate, so only ratios are meaningful. Of the survey's
{{claim:spatial.transect_sites}} mapped sites, {{claim:spatial.transect_censored}} are censored
at a common upper value and several more are binned, leaving only
{{claim:spatial.transect_distinct_obs}} distinct observations, so the rank correlation across all
sites is a weak test and this chapter does not lean on it. And a second apparent pair in the
survey, a school junction and its grounds, proves on inspection to carry a single coordinate for
both sites, so the model's unit ratio there is an artefact of the question, not a result.
That pair is withdrawn. The garden pair is the evidence.

## 8.3 Is it resolution? A registered test says no

The obvious diagnosis is that one kilometre is too coarse. That diagnosis was pre-registered as
a hypothesis and tested.

The model's own emission surface is computed at {{claim:subgrid.fine_res_m}} metres and
aggregated to {{claim:subgrid.coarse_res_m}} metres before anything is rendered, so a finer field
already exists inside the build. At the paired microsites the fine surface gives a ratio of
{{claim:subgrid.paired_efine_ratio}} times in the correct direction, where the delivered product
gives unity. That is a real signal, and the registered hypothesis was that dispersing it at
{{claim:subgrid.fine_res_m}} metres would recover a material fraction of the observed contrast.

**It does not.** Running the calibrated terrain solver at {{claim:subgrid.fine_res_m}} metres,
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

## 8.4 What is actually lost, and where

The refutation also disposes of the premise that motivated it. Contrast is not destroyed by
coarsening. It is **relocated**. Tracking the spread through the build:

| stage | ratio of the ninetieth to the tenth percentile |
|---|---:|
| raw emission surface at {{claim:subgrid.fine_res_m}} m | {{claim:s1.contrast.raw_E_fine_94_m}} |
| after tempering | {{claim:s1.contrast.log1p_tempering}} |
| after dispersion at {{claim:subgrid.fine_res_m}} m | {{claim:s1.contrast.dispersion_94_m}} |
| after solving at {{claim:subgrid.production_res_m}} m | {{claim:s1.contrast.solve_at_238_m_production}} |
| reported at {{claim:subgrid.coarse_res_m}} m | {{claim:s1.contrast.report_at_998_m}} |

The dispersed field still spans {{claim:s1.contrast.report_at_998_m}} times at the delivered
resolution. There is no shortage of contrast. **It is in different places from where the survey
measured it**, which is a failure of placement rather than of dynamic range or of support.

An independent line agrees from the opposite direction, and it is the most actionable finding in
this chapter. Scored across ten monitored cities, the raw emission surface ranks neighbourhoods
at {{claim:r2.rho_emission_surface}}. Passing it through the dispersion solver **lowers** that to
{{claim:r2.rho_with_atransport}}, improving only {{claim:r2.cities_improved}} of ten. The step
that redistributes contrast is the step that misplaces it.

{{fig:dispersion}}

That result now holds on two independently selected sets of cities, which is why Chapter 9 treats
the dispersion step and not the source surface as the place to intervene.

## 8.5 Six nulls, and why only the last one says anything

Section 5.5 described five searches for learnable spatial structure, none of which stated in
advance what it could detect. {{fig:nullpower}} gives the retrospective answer: at their sample
sizes they could only have found residual correlations between
{{claim:null.min_detectable_lo}} and {{claim:null.min_detectable_hi}}.

{{fig:nullpower}}

The sixth was done differently. Before any model was written, the benchmark, the detection limit
and the bar were registered [OSF 2jyfg]. The benchmark is the strongest single globally available
predictor, built-up land-cover fraction within {{claim:phase1.best_radius_km}} kilometres, at
{{claim:phase1.best_rho}}
across {{claim:phase1.cities}} cities. The detection limit on that frame is
{{claim:phase1.min_detectable}}. The bar was their sum, {{claim:phase2.bar}}.

The learned pattern reached {{claim:phase2.rho_learned}}, a median paired difference of
{{claim:phase2.delta}}, better in {{claim:phase2.better_in}} of {{claim:phase1.cities}} cities at
a p-value of {{claim:phase2.p_value}}.

The resulting statement is bounded, and none of the previous five produced anything comparable:

> On {{claim:phase1.cities}} cities and {{claim:phase1.stations}} stations, a learned within-city
> pattern does not beat the best single globally available predictor by more than
> {{claim:phase1.min_detectable}} in rank correlation.

The benchmark in that sentence is the strongest predictor **tested here**, chosen by ranking the
free rasters this project had assembled. It is not a mathematical upper bound on what free data
could supply, and a covariate nobody in this study thought to pull could beat it. What the
tournament below establishes is that no model family beats it on the covariates that were
assembled, which is a different and weaker statement than no predictor existing.

That is a claim which can be disputed, and which a better experiment can supersede. "No spatial
signal was found" is not.

### Was it the data, or was it one model family?

The registered test compared one learned family against one raster, and a reader is entitled to
ask whether the conventional spatial toolkit would have done better. Land-use regression,
geostatistics, geographically weighted regression and mixed-effects models are the standard tools
for this problem, and none of them was in the comparison. So all of them were run, on
{{claim:tour.cities}} cities and {{claim:tour.stations}} stations with
{{claim:lur.predictors}} predictors, each fitted with the target city entirely withheld and scored
on the ranking of that city's stations.

Two of those families cannot be run in the setting this thesis is about, and the reason is not a
technicality. Kriging interpolates between measured points, and geographically weighted regression
fits a local regression around each location from nearby measured points. A city with no monitors
has no nearby measured points. They estimate a surface from observations at the target, which is
the spatial tier this section exists to question, applied to a problem defined by its absence.
Rather than exclude them by argument they were run anyway, with the target city's own stations
made visible, and reported separately as an upper bound on what a city with a network could
obtain.

| family | median rank correlation | paired against the benchmark | interval over cities |
|---|---:|---:|---:|
| the benchmark raster | {{claim:tour.benchmark}} | reference | reference |
| Gaussian process on covariates | {{claim:tour.gp.rho}} | {{claim:tour.gp.paired}} | {{claim:tour.gp.lo}} to {{claim:tour.gp.hi}} |
| random forest | {{claim:tour.rf.rho}} | {{claim:tour.rf.paired}} | {{claim:tour.rf.lo}} to {{claim:tour.rf.hi}} |
| stepwise land-use regression | {{claim:tour.lur.rho}} | {{claim:tour.lur.paired}} | {{claim:tour.lur.lo}} to {{claim:tour.lur.hi}} |
| linear mixed model, city random intercept | {{claim:tour.mixed.rho}} | {{claim:tour.mixed.paired}} | {{claim:tour.mixed.lo}} to {{claim:tour.mixed.hi}} |

Not one of the {{claim:tour.families}} admissible families beats the benchmark by more than the
registered detection limit of {{claim:phase1.min_detectable}}. The best of them improves on a
single free raster by {{claim:tour.gp.paired}} in rank correlation. Conventional stepwise land-use
regression, built the way the literature builds it and the class that reaches the published
coefficients of determination quoted in Section 3.2 [@Hoek2008], buys {{claim:tour.lur.paired}}. A
linear mixed model with a city random intercept is indistinguishable from ridge regression.

The oracle families are the more interesting result. With the target city's own stations visible,
inverse distance weighting reaches {{claim:tour.oracle_idw}}, geographically weighted regression
{{claim:tour.oracle_gwr}} and kriging {{claim:tour.oracle_krige}}. All three sit below the
benchmark's {{claim:tour.benchmark}}, which is obtained with no local observation at all. A city
that has a network, using the methods designed for exactly that case, ranks its own stations worse
than a single free raster ranks a city it has never seen. Section 5.5 reported the same thing for
inverse distance weighting alone; it holds for the geostatistical and locally weighted families
too.

The null is therefore a property of the information available on this frame, and not of the one
model family the registered test happened to use. That is a stronger statement than the
registration was able to make, and it is the one this thesis defends.

The first run of the oracle arm reported kriging at −0.833 [ledger F.105], which is not a poor
score but a near-perfect inversion, and near-perfect inversions are almost always artefacts. It was one. The
target had been standardised using every station in the city, so it summed to zero; holding one
station out then makes the mean of the remainder a strictly decreasing function of the held-out
value, and any model reverting toward its training mean is dragged toward a rank correlation of
minus one whatever its skill. Measured directly, the leave-one-out training mean correlates with
the held-out value at exactly minus one in every city of the panel. The fix was the standard rule that
had been broken, which is to fit the normalisation on the training points only. The values above
are the corrected ones. The admissible arm never had the problem, because there the whole city is
withheld and no such constraint exists.

## 8.6 The reason, which is a change of support

The deeper explanation is not about method at all.

{{fig:withinpixel}}

The spread within a typical model cell is {{claim:s2.within_pixel_p90p10}}, and the spread
between cells across the whole map is {{claim:s2.between_pixel_p90p10}}. **Most of the within-city
variation is inside a cell, not between cells.** The cell mean is conserved through the
comparison to {{claim:s2.cell_mean_drift}}, so this is a statement about the field's structure
and not about a numerical artefact.

A second line points the same way from the opposite end. Chapter 9 reports that predictor skill
rises with the radius of the buffer the predictor is measured over, and peaks at
{{claim:phase1.best_radius_km}} kilometres,
which is coarser than the cell the model reports on. Taken together the two results bracket the
usable band from both sides: finer than a cell is unrecoverable, and what remains informative is
coarser than a cell.

That is a change-of-support statement rather than a data-quality statement, and it has a
consequence the field does not generally acknowledge. A one kilometre product cannot answer
"which part of this cell is worst" for any city with this structure, however the product is
built and however much data is used to build it.

### Three things called resolution, and which of them this chapter measures

The statement above is easy to over-read, and separating the concepts it touches shows what the
evidence does and does not reach.

**The scale at which the atmosphere actually varies.** This is a property of the city. Chapter 3
establishes that it is fine and the variation is large, because a single instrument on a single
protocol recorded a factor of {{claim:spatial.paired_obs_ratio}} over three hundred metres
[@Elangasinghe2008]. Nothing in this chapter contradicts that, and nothing in it should be read
as claiming that Kandy's air is uniform below a kilometre. The opposite is measured.

The scale at which the reporting grid is defined. This is a choice, and Section 8.3 tested
changing it. A tenfold refinement in cell area moved the paired-site ratio by
{{claim:s1.paired_delta_on_refinement}}, so the choice is not what is binding.

The scale at which the available predictors carry information. This is the constraint, and it
is the only one of the three this chapter measures. Section 9.4 reports that predictor skill
rises with the radius over which a predictor is averaged and peaks above the cell size, and
Section 8.5 bounds what a learned pattern adds over the best single predictor. Both are
statements about a predictor set, not about the atmosphere.

Read together the three give a conditional claim, not a universal one, and the condition is
worth carrying: **given the globally available covariates that a city with no monitors can
obtain, sub-kilometre structure cannot be placed, even though it exists and is large.** A
campaign that measured the structure directly would not be bound by this, which is why Chapter 9
lists one. The claim is a limit on inference from a particular information set and not a
statement about the ultimate predictability of urban air.

## 8.7 At matched support, the model is close to right

The apparent catastrophe of Section 8.1 is a comparison between quantities defined at different
supports. At matched support and matched averaging window the picture changes.

At monthly averaging the model's between-cell ratio is {{claim:field.contrast_monthly}}, against
1.26 to 1.51 measured across the stations of three comparable cities at the same window
[@Wickramasinghe2011]. Annually the model gives {{claim:kandy.annual_contrast}}.

{{fig:scales}}

One mismatch remains and it is stated rather than allowed to flatter the agreement. The observed
figures are spreads across a city's **stations**; the model's is a spread across its **cells**.
Matching the averaging window removes the larger part of the discrepancy, and an earlier version
of this comparison set an annual model contrast against observed values taken at mixed windows,
which overstated the agreement. The residual is a support difference that cannot be closed
without a campaign designed for it.

## 8.8 What this licenses

The operational statement is narrow and, this thesis argues, honest.

**Can a user rank neighbourhoods against what a monitor would read there?** No. The fine spatial
rank of the delivered construction is {{claim:r2.rho_with_atransport}}, and Section 8.5 gives the
bound on what a learned alternative could add.

Can a user be told the range their cell spans? Yes. The within-cell distribution is both
well-posed and the larger of the two quantities, and Section 8.6 supplies it.

The second question is the more useful one for exposure assessment, and this thesis is not aware
of a gridded product that currently reports it. The number is retained; what it is said to
measure changes.

The spatial rung of the information budget therefore remains a **declared design assumption**
rather than a validated one. The difference from where this project began is that the assumption
has now been tested, under a registration that could have overturned it, and the test reported
what it was able to see.

### Three claims about the spatial limit, at three different strengths

The chapter's argument is easy to compress into something stronger than the evidence, so the
components are separated here and graded.

**Established.** The delivered construction is worse than one of its own intermediate products.
Passing the emission surface through the dispersion solver takes rank from
{{claim:r2.rho_emission_surface}} down to {{claim:r2.rho_with_atransport}}, on two independently
selected sets of cities. This is a defect in the present implementation and it is not a statement
about information.

Established. Within-cell spread exceeds between-cell spread, and a tenfold refinement of the
grid does not recover the paired contrast. Sub-kilometre structure cannot be placed from the
covariates available.

Not established. That the best possible use of the available information could not beat the
benchmark substantially. The registered test bounds what a learned pattern added over the best
single predictor at {{claim:phase1.min_detectable}} in rank correlation, which leaves real room
between the benchmark and any ceiling. **The evidence does not exclude a better construction; it
bounds how much better a learned one was able to be on this frame.**

The composite statement the thesis defends is therefore that the current construction is
demonstrably imperfect, and that the available information appears to give a more flexible
construction limited headroom. Those are different claims resting on different evidence, and
Chapter 9 acts on the first rather than the second, because the first is the one with a known
remedy.
