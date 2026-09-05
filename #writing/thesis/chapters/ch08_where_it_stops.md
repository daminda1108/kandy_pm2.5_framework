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
both sites, so the model's unit ratio there is an artefact of the question rather than a result.
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
the dispersion step rather than the source surface as the place to intervene.

## 8.5 Six nulls, and why only the last one says anything

Section 5.5 described five searches for learnable spatial structure, none of which stated in
advance what it could detect. {{fig:nullpower}} gives the retrospective answer: at their sample
sizes they could only have found residual correlations between
{{claim:null.min_detectable_lo}} and {{claim:null.min_detectable_hi}}.

The sixth was done differently. Before any model was written, the benchmark, the detection limit
and the bar were registered [OSF 2jyfg]. The benchmark is the best single globally available
predictor, built-up land-cover fraction within 2.4 kilometres, at {{claim:phase1.best_rho}}
across {{claim:phase1.cities}} cities. The detection limit on that frame is
{{claim:phase1.min_detectable}}. The bar was their sum, {{claim:phase2.bar}}.

The learned pattern reached {{claim:phase2.rho_learned}}, a median paired difference of
{{claim:phase2.delta}}, better in {{claim:phase2.better_in}} of {{claim:phase1.cities}} cities at
a p-value of {{claim:phase2.p_value}}.

The resulting statement is bounded, and none of the previous five produced anything comparable:

> On {{claim:phase1.cities}} cities and {{claim:phase1.stations}} stations, a learned within-city
> pattern does not beat the best single globally available predictor by more than
> {{claim:phase1.min_detectable}} in rank correlation.

That is a claim which can be disputed, and which a better experiment can supersede. "No spatial
signal was found" is not.

## 8.6 The reason, which is a change of support

The deeper explanation is not about method at all.

{{fig:withinpixel}}

The spread within a typical model cell is {{claim:s2.within_pixel_p90p10}}, and the spread
between cells across the whole map is {{claim:s2.between_pixel_p90p10}}. **Most of the within-city
variation is inside a cell, not between cells.** The cell mean is conserved through the
comparison to {{claim:s2.cell_mean_drift}}, so this is a statement about the field's structure
and not about a numerical artefact.

A second line points the same way from the opposite end. Chapter 9 reports that predictor skill
rises with the radius of the buffer the predictor is measured over, and peaks at 2.4 kilometres,
which is coarser than the cell the model reports on. Taken together the two results bracket the
usable band from both sides: finer than a cell is unrecoverable, and what remains informative is
coarser than a cell.

That is a change-of-support statement rather than a data-quality statement, and it has a
consequence the field does not generally acknowledge. A one kilometre product cannot answer
"which part of this cell is worst" for any city with this structure, however the product is
built and however much data is used to build it.

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

**Can a user be told the range their cell spans?** Yes. The within-cell distribution is both
well-posed and the larger of the two quantities, and Section 8.6 supplies it.

The second question is the more useful one for exposure assessment, and this thesis is not aware
of a gridded product that currently reports it. The number is retained; what it is said to
measure changes.

The spatial rung of the information budget therefore remains a **declared design assumption**
rather than a validated one. The difference from where this project began is that the assumption
has now been tested, under a registration that could have overturned it, and the test reported
what it was able to see.
