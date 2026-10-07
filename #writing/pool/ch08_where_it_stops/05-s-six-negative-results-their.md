## Six negative results and their detection limits {#s-six-negative-results-their}

{{ref:s-five-attempts-find-spatial}} described five searches for learnable spatial structure, none of which stated in
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

### The strongest available covariate, tested where the power is {#s-strongest-available-covariate-tested}

The tournament above varies the model and holds the information fixed. The complement is to hold
the model fixed and vary the information, and the strongest candidate available is an Earth
observation foundation model. This project had already tested one, and the test was not good
enough: it ran on three cities and thirty-three stations between them, and {{ref:app-changed-during-writing-thesis}} records its
minimum detectable partial correlation as {{claim:emb.f27_mde_lo}} to
{{claim:emb.f27_mde_hi}}. It could exclude only a large effect. On the frame {{this:ch-model-stops}} uses the
detectable difference is {{claim:emb.detection_limit}}, and the embeddings had never been scored
there.

That test was registered [OSF 6udm3] before it was written, with the benchmark, the detection limit
and the bar carried over unchanged from the tournament. Sixty-four dimensional annual embeddings
were sampled in a hundred-metre buffer at every station, returning values at all
{{claim:emb.stations}} of them across {{claim:emb.cities}} cities, and scored leave-one-city-out
exactly as above.

| model | median rank correlation |
|---|---:|
| the benchmark raster | {{claim:emb.rho_bench}} |
| embeddings alone | {{claim:emb.rho_alone}} |
| the sixty existing predictors | {{claim:emb.rho_existing}} |
| existing predictors and embeddings together | {{claim:emb.rho_combined}} |

**That table is the trap this thesis has now fallen into three times, and it is shown because
hiding it would be worse.** Read down the column, the embeddings post the highest median of
anything tested. They appear to beat the best free raster and to beat the entire sixty-predictor
set at once. Paired within city, which is the only comparison that answers the question, embeddings
against the benchmark is {{claim:emb.e1.paired}}
[{{claim:emb.e1.lo}}, {{claim:emb.e1.hi}}], and adding them to the existing predictors is
{{claim:emb.e2.paired}} [{{claim:emb.e2.lo}}, {{claim:emb.e2.hi}}]. Both fail the registered bar,
and both point the opposite way to the medians.

The claim this licenses is the one the registration specified: on {{claim:emb.cities}} cities and
{{claim:emb.stations}} stations, {{claim:emb.dims}}-dimensional Earth observation foundation-model
embeddings do not beat the best single globally available raster by more than
{{claim:emb.detection_limit}} in rank correlation. That is the seventh null on this question and
the second with a detection limit fixed in advance, and it replaces an underpowered null with a
bounded one.

One number in it should not be rounded to zero. The partial correlation with the benchmark
regressed out is {{claim:emb.e3.paired}}, with a lower bound of {{claim:emb.e3.lo}}: it fails to
exclude zero by seven thousandths, and it is about three times the estimate the earlier
underpowered test produced. The registered verdict is undetectable and that stands. But *embeddings
carry no independent signal* would be a stronger statement than this measurement supports, and if
any part of this question deserves a further experiment it is that one.

### Seven further model families, tested {#s-seven-further-model-families}

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
coefficients of determination quoted in {{ref:s-gap-stated-list}} [@Hoek2008], buys {{claim:tour.lur.paired}}. A
linear mixed model with a city random intercept is indistinguishable from ridge regression.

The oracle families are the more interesting result. With the target city's own stations visible,
inverse distance weighting reaches {{claim:tour.oracle_idw}}, geographically weighted regression
{{claim:tour.oracle_gwr}} and kriging {{claim:tour.oracle_krige}}. All three sit below the
benchmark's {{claim:tour.benchmark}}, which is obtained with no local observation at all. On this
frame a city that has a network, using the methods designed for exactly that case, ranks its own
stations no better than a single free raster ranks a city it has never seen.
{{ref:s-five-attempts-find-spatial}} reported the same thing for inverse distance weighting alone.

The oracle arm is a leave-one-out ranking of every station in a city, which is not the design of
the registered spatial learning curve of {{ref:s-what-stations-buy-map}}. There a fixed set of
held-out sites is scored from a controlled number of fitting stations, and under the registered
first-pass rule kriging or regression kriging overtook the raster at some density in most cities.
The two analyses are closer than that contrast suggests. At three fitting stations the curve puts
kriging and the raster at a similar low skill, and once the per-city comparisons are corrected for
multiple testing only {{claim:v2.curve.full.holm_crossing}} of twenty-three cities show
interpolation clearly ahead. Both analyses therefore say that a few stations do not rank a city's
neighbourhoods better than a free layer, and the curve adds that only the few networks with
several dozen stations reach a moderate ranking.

A claim that nothing beat one free raster is only as good as a reader's ability to check it, so
{{fig:tournament}} puts every family on one axis. The left panel is the paired comparison, with the
foundation-model embeddings of the registered test included, and the registered detection limit
drawn as the line an improvement would have had to cross. No interval reaches it. The right panel
gives the unpaired medians, which is the only form in which the oracle families can be shown, and
places them below a separator because they answer a question a city without monitors cannot ask.

{{fig:tournament}}

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
