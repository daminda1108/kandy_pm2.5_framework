# Chapter 7. Making sure it works

A model that cannot be checked where it is used is not obviously worth more than a plausible
guess. This chapter sets out the procedure that makes checking possible, reports what it
measured, describes the confounds it caught before they reached print, and gives the external
tests the model has at the demonstration city. It ends with the ones that carry no weight, and
why they are reported anyway.

## 7.1 Borrowed ground truth

Kandy has two low-cost sensors and no reference monitor, so no local dataset exists against which
the field can be scored. The procedure adopted here borrows the ground truth from elsewhere. A
city with a dense monitoring network is deliberately reduced to the information Kandy actually
has, and the model is then scored against the monitors that were taken away from it.

{{dia:protocol}}

The reduction is what makes the test informative. Scoring a model that has seen thirty monitors
measures a capability the target city will never possess, and reporting that number as though it
described the target is the most common way this class of model is oversold. The panel comprises
{{claim:frame.cities}} cities across {{claim:frame.countries}} countries and
{{claim:frame.city_days}} city days, with a median of {{claim:frame.med_held_stations}} withheld
stations and {{claim:frame.med_days_per_city}} scored days per city.

{{fig:panel}}

Kandy contributes nothing to this panel. It supplies no training data at any tier, which is what
allows the measurement to be applied to it.

{{tbl:T4_3}}

## 7.2 What each increment of information is worth

The measurement is possible because the tiers are nested. A lower tier is not a different model,
it is the same model with a stream removed, so the difference between two tiers is information
loss and nothing else.

{{tbl:T7_1}}

{{fig:ladder}}

Reported as the median across cities of the per-city percentage reduction in daily root mean
square error, never as a ratio of medians and never averaged across metrics. Four features of
that table matter more than its ordering.

**Free data is not negligible.** Static geography, which is terrain, roads, land cover, night
lights and population, and which is available for every city on Earth at no cost, buys
{{claim:step.geography}} per cent. That is comparable to what the first local instrument buys.

**Geography beats the satellite level.** The annual satellite level buys
{{claim:step.satellite}} per cent, less than the geography. The reason is straightforward once
seen: an annual level cannot touch day-to-day variance, and daily error is what daily variance is
made of.

**The second monitor through the eighth buys nothing.** {{claim:step.bud1_bud2}} per cent is not
a small effect but an absent one, and Section 7.4 shows it is the most estimator-robust result in
the study. A city with two sensors and a city with eight are, for this model, the same city.

**The regional background is the largest single gain measured.** At {{claim:step.bud2_bud3}} per
cent it exceeds every other rung, and it is the instrument air quality programmes are least
likely to fund, because a rural monitor serves no constituency.

One caveat belongs with that last row rather than in a footnote. The regional background used
here is an outer-ring proxy drawn from the same network in every city, so its gain partly
measures more of the same network rather than genuinely regional air. Only a true regional
network settles it, and that is what a station of the kind Chapter 9 recommends would provide.

## 7.3 The recommendation inverts in the tropics

The pooled table is misleading if read as advice, and {{tbl:T7_2}} is the finding.

{{tbl:T7_2}}

Stratified by latitude band, the ordering reverses in the band Kandy belongs to: local sensors
buy {{claim:band.deep_tropical.step_bud0c_bud1}} per cent there against
{{claim:band.deep_tropical.step_bud2_bud3}} per cent for the regional background, which is the
opposite of the pooled result. A programme following the pooled recommendation in Colombo or
Kampala would buy the wrong instrument first.

That inversion strengthened when the satellite stream was replaced with one of clean provenance,
which Section 7.5 describes. On the corrected stream the two local sensors buy
{{claim:maiac.deep_tropical_first2}} per cent in Kandy's band against
{{claim:maiac.deep_tropical_background}} for the background, a local advantage of
{{claim:maiac.deep_tropical_local_advantage}} times.

The reversal is not a curiosity. It means the recommendation this thesis is most likely to be
quoted for is the wrong recommendation for the city it was built for, and a reader who takes the
pooled row without the band row will act on it.

## 7.4 Is this a property of the information or of the model?

A value-of-information result is worthless if it is really a statement about one estimator. The
first rung was therefore re-run across four [@Ke2017; @Chen2016; @Prokhorenkova2018].

{{fig:streams}}

Across the three non-linear learners the spread is
{{claim:learner.nonlinear_spread_bud0c_bud1}} percentage points. Ridge regression collapses,
reporting {{claim:learner.ridge_linear.step_bud0c_bud1}} per cent against the shipped estimator's
{{claim:learner.histgbm_shipped.step_bud0c_bud1}}, because on a sensorless tier of
{{claim:bud0c.n_features}} predictors a linear model cannot exploit the free data and the monitor
therefore appears to rescue it.

That is a result rather than a nuisance, and it is the useful reading. **The measured value of a
monitor depends on how well the free data is already being used.** A programme modelling badly
will conclude that monitors are worth several times what a programme modelling well would
conclude. This thesis therefore claims the ladder is robust across non-linear estimators, and
explicitly not that even a linear model reproduces it, which an earlier version of this work did
claim.

One result survives every learner including ridge: the second-through-eighth monitor rung stays
at approximately zero, with a spread of {{claim:learner.all_spread_bud1_bud2}} percentage points.
The redundancy of those monitors is the most robust finding in the study.

## 7.5 What a fused product does to a measurement of this kind

The satellite stream was initially a published fused concentration product [@Wei2023]. Products
of that kind are trained on ground monitors, in this case on networks that supply this study's
own panel, and predicted from a feature set that substantially overlaps the tier's other streams.
The stream was therefore not an independent observation and its measured value was a mixture.

The ladder was re-run on raw satellite aerosol optical depth [@Lyapustin2018; @Levy2013], a
radiometric retrieval trained on nothing.

| | fused product | raw retrieval |
|---|---:|---:|
| the satellite rung itself | {{claim:c1.step_fused_ghap}} per cent | {{claim:c1.step_raw_aod}} per cent |
| the rung above it, pooled | {{claim:step.bud0c_bud1}} per cent | {{claim:maiac.step_bud0c_bud1}} per cent |

**The satellite rung barely moves**, by {{claim:c1.fused_excess_pp}} percentage points. The
fused product's apparent value was satellite information that a raw retrieval supplies equally
well, not recycled information inflating its own score. The pre-registered prediction was the
opposite.

**The rung above it moves a great deal.** The mechanism is clear once seen: a product trained on
a city's monitors already encodes part of what those monitors would tell you, so adding the
monitor appears to buy less. **Contamination does not inflate the contaminated rung, it deflates
the rung above it.** The pre-registered test looked for excess skill in the satellite's own rung,
found none, and would have reported the leakage as immaterial had the ladder not been re-run.

This generalises past this thesis. Any analysis that prices observations against a covariate
trained on those observations will under-price them, and fused products are now the default
covariate in this field.

## 7.6 Three confounds the pooled numbers hid

Each was caught by a gate declared before the run rather than by review, and each would otherwise
have reached print.

**Country crossed with latitude.** A minimum-cost sampling design drew the entire mid-latitude
arm from a single national network, aliasing band with network so completely that no
band-stratified result could have been interpreted. It was corrected by a registered amendment
before any scoring took place, which is the only reason it appears here as a methodological note
rather than as a retraction.

**Driver completeness crossed with band.** Boundary-layer height coverage is uneven across bands,
so the ladder was re-run without it. The first rung moves from
{{claim:confound.blh.with_blh_step1}} to {{claim:confound.blh.without_blh_step1}} per cent, a
shift of {{claim:confound.blh.delta}} percentage points, which bounds what the uneven coverage
can be doing. The band ordering is unchanged.

**Instrument class crossed with band.** The deep-tropical cell is
{{claim:confound.deep_tropical_lcs_pct}} per cent low-cost sensors against
{{claim:confound.other_bands_lcs_pct}} per cent in the other bands, and this one cannot be
sampled away for the reason Chapter 2 gave.

{{fig:confounds}}

The gain from additional sensors depends on what they are, and the class matters. Median
shrinkage weight placed on sensors three through eight is {{claim:class.LCS.w_bud2}} for low-cost
units against {{claim:class.reference.w_bud2}} for reference monitors, a contrast of
{{claim:class.w_bud2_contrast}} times. Low-cost units gain more from replication because
per-device error averages down.

An earlier version of this work reported that contrast as infinite and concluded that reference
networks gain nothing at all from added stations. That was computed on a superseded run. The
direction survives, the magnitude does not, and any argument resting on the strong form has to be
re-made rather than inherited.

## 7.7 The model across ten cities

{{fig:scorecard}}

Three axes are reported separately and never averaged, because averaging a skill percentile
across metrics produces a meaningless middle: an earlier version of this work did exactly that
and reported a model as representative on the strength of two opposite effects cancelling.

Seasonal correlation runs {{claim:scorecard.seasonal_r_lo}} to {{claim:scorecard.seasonal_r_hi}}
across the panel. Diurnal correlation runs {{claim:scorecard.diurnal_r_lo}} to
{{claim:scorecard.diurnal_r_hi}}, which is a much wider range and is regime-dependent rather than
random. Level bias has a median of {{claim:scorecard.level_bias_median}} per cent. The fine
spatial rank is estimable at {{claim:scorecard.spatial_estimable}} of the ten cities, with a
median of {{claim:scorecard.spatial_rho_median}}.

{{fig:kathmandu}}

The showcase city is shown because it is the best case and is labelled as such. It reaches a
seasonal correlation of {{claim:ktm.seasonal_r}} and a diurnal correlation of
{{claim:ktm.diurnal_r}} at {{claim:ktm.stations}} stations, with a level bias of
{{claim:ktm.level_bias_pct}} per cent. Its spatial rank, taken from the panel scorecard rather
than from the figure so that one city does not carry two numbers, is
{{claim:scorecard.kathmandu_spatial_rho}}.

## 7.8 The checks at Kandy that carry weight, and the ones that do not

**The two local sensors cannot validate this model**, and the reason is structural rather than a
matter of degree. The temporal anchor is trained on their residual and then amplitude-sharpened
to their observed swing, so agreement with them measures the calibration and not skill.

{{fig:cycles}}

The comparison is shown for completeness, at a seasonal correlation of
{{claim:kandy.cycles_seasonal_r}} and a diurnal correlation of
{{claim:kandy.cycles_diurnal_r}}, and those numbers should be read as confirming that the
calibration was applied rather than as evidence that the model works.

**Two records do carry weight**, because the model played no part in producing them and they
played no part in producing the model.

{{tbl:T3_2}}

The published record from the national research organisation gives annual means at a site that is
neither of the two sensors. The model at that cell reads {{claim:nbro.model_pixel_2021}} against
an observed {{claim:nbro.diff_pct_2021}} per cent difference in the first year, and
{{claim:nbro.model_pixel_2022}} at {{claim:nbro.diff_pct_2022}} per cent in the second.

The reason that comparison is genuinely external deserves stating rather than asserting. The
anchor is calibrated to the two low-cost sensors, so the model's basin **mean** is not
independent of Kandy observations. The spatial pattern is independent, because it is an emission
proxy multiplied by a confinement term, both imposed and neither fitted to anything measured in
this city. What the comparison therefore tests is the **lift**, meaning how far the field rises
from the basin mean to that particular cell, and the lift is {{claim:nbro.lift_pct_2021}} per
cent in the first year and {{claim:nbro.lift_pct_2022}} per cent in the second. Had the lift been
near zero the comparison would have collapsed into a check on the anchor and carried no spatial
information at all. The station sits {{claim:nbro.station_offset_km}} kilometres from the centre
of the cell it falls in, so the pairing is not marginal.

**A discrepancy remains open and is not resolved here.** Of four independent point records at
Kandy, three sit below the model and one matches it. The three low ones are all low-cost sensors
carrying a downward calibration correction; the one that matches has an undocumented instrument.
This is a level discrepancy on the axis this thesis calls well supported, and it is stated as an
open question rather than settled by choosing the record that agrees.

## 7.9 Are the intervals right?

{{fig:uncertainty}}

The delivered ninety per cent interval covers {{claim:kandy.cov90}} per cent of observations at
the two sensors, which read alone suggests the intervals are too narrow. Section 6.2 gave the
diagnosis: the misses are one-sided, {{claim:kandy.miss_below}} per cent below against
{{claim:kandy.miss_above}} per cent above, with a median offset of
{{claim:kandy.median_offset}} micrograms per cubic metre. Removing each sensor's own offset
restores coverage to {{claim:kandy.cov90_recentred}} per cent.

The width was right and the centring was wrong, and the cause is the change of support of
Chapter 8 rather than a failure of the calibration procedure.

## 7.10 An independent chemical check

The decomposition assumes that the regional background is aged air arriving from outside the
basin and the local increment is fresher material generated inside it. That assumption is
load-bearing and had never been tested against composition.

{{fig:chemistry}}

Classifying air-mass origin by back-trajectory sector, which is independent of the composition
product used to measure it, continental air is measurably more secondary-rich and therefore more
aged than marine air: {{claim:chem.sec_frac.IGP_E_India}} against
{{claim:chem.sec_frac.SW_marine}}. That is the ordering the decomposition requires and it is the
first chemical support the construction has.

A second registered prediction was refuted usefully. Recirculated local air was expected to be
the freshest, and it is not, because stagnation gives local precursors time to age in place. The
consequence is that treating the local increment as fresh primary aerosol is too simple, and
Chapter 9 lists the composition measurement that would settle it.

## 7.11 Exposure and attributable burden

Chapter 2 gave health as one of the two stakes, and the delivered field supports an estimate.

{{fig:burden}}

**The area mean under-states exposure.** People are not distributed uniformly over the basin;
they concentrate in the higher-concentration core. For {{claim:exposure.year}} the unweighted
basin mean is {{claim:exposure.area}} micrograms per cubic metre, the residential-weighted mean
is {{claim:exposure.residential}}, and the population-weighted mean is
{{claim:exposure.dynamic}}. That is an uplift of {{claim:exposure.uplift_pct}} per cent over the
area mean, and any health statement should use the weighted figure.

**The attributable burden.** Projecting the population-weighted exposure through a published
concentration-response function [@Burnett2018] against the national mortality baseline gives
{{claim:burden.deaths}} attributable deaths per year, with an interval of
{{claim:burden.ci_low}} to {{claim:burden.ci_high}}. That is an attributable fraction of
{{claim:burden.fraction_pct}} per cent, of which {{claim:burden.avoidable}} would be avoidable
if concentrations met the World Health Organization guideline [@WHO2021].

⚠ **Three qualifications, and they are not small.** The response function and the mortality
baseline are both taken from published work and neither was estimated here, so this is a
projection of the delivered field through somebody else's epidemiology rather than an
epidemiological result. The interval reflects only the published uncertainty in the response
function and not uncertainty in the field, which would widen it. And the estimate inherits the
level discrepancy of Section 7.8: if the three low point records are right and the model reads
high, the burden is over-stated proportionally.

The figures in this section were regenerated for this thesis, and doing so moved them. The
exposure and burden files predated the field rebuild, so the previously reported uplift of seven
per cent and burden of 427 were computed on a superseded field. This is recorded because it is
the same failure mode Chapter 10 describes and it was found the same way.

## 7.12 What this chapter does and does not establish

It establishes that the level and the seasonal cycle transfer, across
{{claim:frame.cities}} cities and four latitude bands, and that the value of each observation
stream can be measured rather than argued.

It establishes that the ordering of that value is not uniform, and that the pooled recommendation
is wrong for the tropics.

It does not establish that the model is accurate at Kandy, because that cannot be established
with the observations Kandy has. What it establishes is what the model is entitled to claim
there, which is a weaker statement and the only honest one available.
