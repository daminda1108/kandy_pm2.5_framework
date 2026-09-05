---
title: "Measuring what an air quality observation is worth, in cities that cannot check a model"
author: "Daminda Alahakoon, University of Peradeniya, Sri Lanka"
date: "2026"
geometry: margin=1.9cm
fontsize: 10pt
mainfont: "Times New Roman"
colorlinks: false
---

**Undergraduate thesis, 2026. Two-page summary.** Full thesis: 23,000 words, 33 figures, 10
chapters. Five pre-registrations lodged on OSF before the corresponding analyses ran.

## The problem

Most of the world's population breathes air that nobody measures, and the deficit is worst where
concentrations are highest. Models supply a field where instruments do not, and they are good.
But they are validated where monitors are dense and used where monitors are absent, so **the
transfer that matters is the one transfer that cannot be scored**. The usual response to doubt,
testing more thoroughly, needs exactly the observations whose absence created the doubt.

This thesis changes the question. Rather than asking how accurate a model is where accuracy
cannot be measured, it asks what a model is entitled to claim given the observations it has, and
then measures what each further observation would be worth.

## The construction

Concentration is separated into a spatially uniform regional background and a locally generated
increment redistributed by a pattern normalised to unit spatial mean. Two properties make the
measurement possible.

**Conservation.** The spatial mean of the field returns the temporal anchor exactly, so an error
in the pattern misplaces material without creating it. The consequence of being wrong is bounded
and legible.

**Exact degradation.** The model declares which observation streams each tier may use, and
withholding one reproduces the lower tier bit-for-bit rather than approximately. That is what
converts an ablation into a measurement of information: the difference between two tiers is
information loss and nothing else, because it is the same model rather than a refitted one.

## Three results

Measured across **{{claim:frame.cities}} cities in {{claim:frame.countries}} countries and
{{claim:frame.city_days}} city-days**, scoring each city against monitors deliberately withheld
from it.

**1. Freely available geography is worth about as much as the first monitor a city buys.** Terrain,
roads, land cover, night lights and population together buy {{claim:step.geography}} per cent in
daily error. The second monitor through the eighth buy {{claim:step.bud1_bud2}} per cent, which
is not a small effect but an absent one, and it is the most estimator-robust result in the study.
A regional background station buys {{claim:step.bud2_bud3}} per cent, the largest single gain
measured, and it is the instrument programmes are least likely to fund because a rural monitor
serves no constituency.

**2. The recommendation inverts by latitude band.** In the deep tropics, local sensors buy
{{claim:maiac.deep_tropical_first2}} per cent against {{claim:maiac.deep_tropical_background}}
per cent for the regional background, reversing the pooled ordering. A programme in Colombo or
Kampala following advice derived from the global average would buy the wrong instrument first.

**3. A monitor-trained covariate under-prices monitors, and not in the way one would look for.**
Replacing a published fused concentration product with a raw satellite retrieval left the
satellite's own contribution essentially unchanged, at {{claim:c1.step_fused_ghap}} per cent
against {{claim:c1.step_raw_aod}}. It roughly doubled the contribution of the rung above it. **Contamination does not inflate the contaminated
term; it deflates the term above.** A pre-registered test that looked for excess skill in the
contaminated stream found none and would have reported the leakage as immaterial. Fused products
are now the default covariate in this field, and I am not aware of prior work reporting this.

## Where the model stops, and why that is a result

Two survey sites three hundred metres apart fall inside a single model cell. They differ by a
factor of {{claim:spatial.paired_obs_ratio}} observationally; the model returns unity, because it
is being asked about one pixel twice. A pre-registered test of the obvious diagnosis, that the
grid is too coarse, was **refuted**: a tenfold refinement in area moves the paired ratio by
{{claim:s1.paired_delta_on_refinement}}.

The reason is a change of support rather than a data deficiency. Spread *within* a typical cell exceeds spread
*between* cells across the whole map, by {{claim:s2.within_pixel_p90p10}} against
{{claim:s2.between_pixel_p90p10}} on the same measure. A kilometre-scale product cannot answer which part of a cell
is worst, for any city with this structure, however it is built. What it can report is the range
the cell spans, which is both well-posed and the larger quantity, and which no gridded product
currently reports.

## A pre-registered null with a stated detection limit

A learned spatial pattern was tested with the benchmark, the detection limit and the bar all
fixed before the model was written. Benchmark {{claim:phase1.best_rho}}, detection limit
{{claim:phase1.min_detectable}}, bar {{claim:phase2.bar}}. The learned pattern reached
{{claim:phase2.rho_learned}}.

This is the sixth null on this question in the project and the first with a detection limit
stated in advance. It yields a bounded claim, which the previous five did not: *on
{{claim:phase1.cities}} cities and {{claim:phase1.stations}} stations, a learned pattern does not
beat the best single globally available predictor by more than {{claim:phase1.min_detectable}} in
rank correlation.* A retrospective power analysis showed the earlier five could only have
detected effects between {{claim:null.min_detectable_lo}} and {{claim:null.min_detectable_hi}},
which is why they said nothing.

## Demonstration

Kandy, Sri Lanka: a valley city of 400,000 with two low-cost sensors and no operating reference
monitor. The local share of concentration is **{{claim:partition.f}}**, derived from a physical
constraint rather than assumed, so roughly half the burden is actionable locally. Against two
published records that played no part in building the model, the field agrees to
{{claim:nbro.diff_pct_2021}} and {{claim:nbro.diff_pct_2022}} per cent in two independent years.

## How the work is done

Every numeric claim in the thesis is regenerated from its source file at build time and the build
refuses to complete if prose and data disagree. Writing the thesis moved ten previously recorded
quantities, none of which was found by reading; three of them made the surrounding argument
weaker and were kept. Chapter 5 is a five-thousand-word account of eight approaches that did not
work, ordered so that the contrast is visible: an approach yielded about as much when it failed
as it had declared before it started.

## Status

Manuscript drafted (13,800 words, 18 figures, 62 references) and targeted at a methods venue.
Thesis complete. Five OSF pre-registrations, fourteen of thirty predictions refuted. Code, claim
generators and pre-registrations are version-controlled and available.

**Contact:** 11daminda08@gmail.com
