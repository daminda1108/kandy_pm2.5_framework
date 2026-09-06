---
title: "Measuring what an air quality observation is worth, in cities that cannot check a model"
author: "Daminda Alahakoon, University of Peradeniya, Sri Lanka"
date: "2026"
geometry: margin=1.9cm
fontsize: 10pt
mainfont: "Times New Roman"
colorlinks: false
---

**Undergraduate thesis, 2026. Two-page summary.** Full thesis: 35,000 words, 35 figures, 10
chapters. Six pre-registrations lodged on OSF before the corresponding analyses ran.

## The problem

Most of the world's population breathes air that nobody measures, and the deficit is worst where
concentrations are highest. Models supply a field where instruments do not, and they are good. But
they are validated where monitors are dense and used where monitors are absent, so **the transfer
that matters is the one transfer that cannot be scored**, and the usual response to doubt needs
exactly the observations whose absence created it.

This thesis changes the question. Rather than asking how accurate a model is where accuracy
cannot be measured, it asks what a model is entitled to claim given the observations it has, and
measures the marginal predictive value of each further observation stream: the reduction in
out-of-sample daily error at a fixed position in a fixed ordering, which stands in for loss rather
than being decision-theoretic value of information.

## The construction

Concentration is separated into a spatially uniform regional background and a locally generated
increment redistributed by a pattern normalised to unit spatial mean. Two properties make the
measurement possible.

**Conservation.** The spatial mean of the field returns the temporal anchor exactly, so an error
in the pattern misplaces material without creating it.

**Exact degradation.** The model declares which observation streams each tier may use, and
withholding one reproduces the lower tier bit-for-bit rather than approximately. Specification and
fitting are held constant, so the difference between two tiers isolates the predictive consequence
of admitting that stream rather than confounding it with a change of model.

## Three results

Measured across **{{claim:frame.cities}} cities in {{claim:frame.countries}} countries and
{{claim:frame.city_days}} city-days**, scoring each city against monitors withheld from it. Every
panel city is a valley or basin and publishes enough monitoring to be scored, so what follows is
bounded by that panel.

**1. Freely available geography is worth about as much as the first monitor a city buys.** Terrain,
roads, land cover, night lights and population together buy {{claim:step.geography}} per cent in
daily error. Monitors three to six buy {{claim:step.bud1_bud2}} per cent, an absent effect rather
than a small one, and the most estimator-robust result in the study. Sweeping from one station to
eight puts the saturation one rung lower than the tier structure could express: the first station
buys {{claim:stn.one_gain}} per cent and the second adds {{claim:stn.second_adds}} points.
A background series from outside the urban core buys {{claim:step.bud2_bud3}} per cent, the
largest single gain measured, and the instrument that would supply it is the one programmes are
least likely to fund. That series is a proxy built from each city's own outer ring rather than a
rural monitor, so it was rebuilt from a donor city the target never sees: an independent network
recovers {{claim:donor.gain_reproduced_pct}} per cent of the gain, falling to
{{claim:donor.reproduced_deep_tropical}} per cent in Kandy's own stratum. That establishes
transferable information in a background-like observation, not that a rural station would deliver
this figure at Kandy. Every figure is a marginal value at a position in one ordering. Cities are
not independent either, since {{claim:clust.largest_n}} share a national network; resampling
clusters widens every interval by about half again and overturns none, and the tightest result
stays the null.

**2. The recommendation inverts between strata.** In the deep tropics, local sensors buy
{{claim:maiac.deep_tropical_first2}} per cent against {{claim:maiac.deep_tropical_background}}
per cent for the background proxy, reversing the pooled ordering. Paired within city and
bootstrapped over cities the advantage is {{claim:inv.maiac.median}} points
[{{claim:inv.maiac.lo}}, {{claim:inv.maiac.hi}}], favouring sensors in
{{claim:inv.maiac.frac_cities}} per cent of the band, and a programme following pooled advice
would buy the wrong instrument first. The defensible form is narrow: the panel supports a
deep-tropical ordering in which local observations outperform the background proxy, and how far
that reflects an atmospheric regime rather than a measurement regime is unresolved. The stratum
holds thirteen cities, instrument class is strongly associated
with latitude, and the paired test was not pre-registered.

**3. A monitor-trained covariate under-prices monitors, and not in the way one would look for.**
Replacing a published fused concentration product with a raw satellite retrieval left the
satellite's own contribution essentially unchanged, at {{claim:c1.step_fused_ghap}} per cent
against {{claim:c1.step_raw_aod}}, and roughly doubled the contribution of the rung above it.
**Contamination does not inflate the contaminated term; it deflates the term above.** A
pre-registered test looking for excess skill in the contaminated stream found none and would have
reported the leakage as immaterial; the displaced signature is what makes the obvious diagnostic
the wrong one. It is not cosmetic: on the fused product the inversion above is
{{claim:inv.ghap.median}} points with an interval spanning zero, so the contamination did not
shift that result, it removed it.

## Where the model stops, and why that is a result

Two survey sites three hundred metres apart fall inside a single model cell and differ by a factor
of {{claim:spatial.paired_obs_ratio}} observationally; the model returns unity, because it is
being asked about one pixel twice. A pre-registered test of the obvious diagnosis, that the grid
is too coarse, was **refuted**: a tenfold refinement in area moves the paired ratio by
{{claim:s1.paired_delta_on_refinement}}. The reason is a change of support rather than a data
deficiency, since spread *within* a typical cell exceeds spread *between* cells across the whole
map, {{claim:s2.within_pixel_p90p10}} against {{claim:s2.between_pixel_p90p10}}. A
kilometre-scale product cannot answer which part of a cell is worst, however it is built. What it
can report is the range the cell spans, which is well-posed, larger, and reported by no gridded
product now in use.

## A pre-registered null with a stated detection limit

A learned spatial pattern was tested with the benchmark, the detection limit and the bar all
fixed before the model was written. Benchmark {{claim:phase1.best_rho}}, detection limit
{{claim:phase1.min_detectable}}, bar {{claim:phase2.bar}}. The learned pattern reached
{{claim:phase2.rho_learned}}.

This is the sixth null on this question and the first with a detection limit fixed in advance, so
it yields a bounded claim where the previous five, which could only have detected effects between
{{claim:null.min_detectable_lo}} and {{claim:null.min_detectable_hi}}, yielded none.
{{claim:tour.families}} further families were then run on the same frame, including stepwise
land-use regression, a Gaussian process and a mixed model: none beats the benchmark by more than
the detection limit, and kriging and geographically weighted regression, which need observations
at the target, fall below it even when given the city's own stations. The null is a property of
the information, not of one model family.

## Demonstration

Kandy, Sri Lanka: a valley city of 400,000 with two low-cost sensors and no reference monitor.
Under the stated background and minimum-increment assumptions the constrained
decomposition assigns **{{claim:partition.f}}** of modelled concentration to a locally generated
increment, derived from a physical constraint rather than assumed, against a retired prior of
about a quarter; it ranges {{claim:partition.f_lo}} to {{claim:partition.f_hi}} across anchored
years and {{claim:field.f_form_calendar}} to {{claim:field.f_form_roll48}} across background-window
definitions. That is a model-imposed split rather than a
measured source apportionment: the increment is the spatially structured component inside the
model domain, which is not the same quantity as material emitted in Kandy, and the model carries
no chemistry with which to separate them. Against two published records that played no part in
building the model, the field agrees to {{claim:nbro.diff_pct_2021}} and
{{claim:nbro.diff_pct_2022}} per cent in two independent years. Those checks cover the city-mean
level, and because the temporal anchor is calibrated to Kandy's own sensors they test the modelled
lift above an anchored mean rather than the whole field. **The neighbourhood-scale map is not validated and is not
claimed to be**, for the reason the previous section gives.

## How the work is done

Every numeric claim is regenerated from its source at build time and the build refuses to complete
if prose and data disagree. Writing the thesis moved eleven previously recorded quantities, none
found by reading; four made the surrounding argument weaker and were kept. Chapter 5 is an account
of eight approaches that did not work.

## Status

Manuscript drafted (13,800 words, 18 figures, 62 references) and targeted at a methods venue.
Thesis complete. Six OSF pre-registrations, fourteen of thirty predictions refuted across the five
that have run. Code, claim generators and pre-registrations are version-controlled.

**Contact:** 11daminda08@gmail.com
