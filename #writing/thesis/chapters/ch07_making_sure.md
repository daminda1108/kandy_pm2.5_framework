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

### Why a panel measurement should apply to Kandy at all

Independence is necessary for the transfer and it is not sufficient. A panel that Kandy is absent
from is also a panel Kandy may not resemble, and the question of what licenses carrying a number
from one to the other has to be answered rather than assumed.

**The panel is not a sample of the world's cities.** It is the set of cities that publish enough
concurrent monitoring to be scored, which selects for institutional capacity, income and
monitoring history. Chapter 2 gives the reason this cannot be fixed by sampling harder: the
regime with the least reference monitoring is the regime that most needs a sensorless method, so
the cities that could best represent Kandy are the cities least able to appear. Where a claim
depends on the panel being representative, it is not made.

**What transfers is an ordering, not a magnitude.** The quantity carried to Kandy is which
observation is worth more than which, and orderings survive shifts in level that would invalidate
a transferred number. No statement in Chapter 9 depends on Kandy's own error falling by any
particular percentage.

**The transfer is made within a stratum, not from the pool.** Kandy is matched to the panel on
the variables that plausibly govern the ordering rather than to the panel as a whole. It is read
against the deep-tropical band, which Section 7.3 shows reverses the pooled result, and against
the low-cost-sensor stratum, since Kandy's instruments are low-cost and Section 7.6 shows the
class changes what added sensors are worth. A pooled number would be the wrong number twice over.

**The panel matches Kandy on the one structural variable it was selected for and on no others by
design.** Every panel city is a valley or basin, which is the feature the construction depends
on, and this is a selection criterion rather than a finding. The panel contains no coastal city,
so nothing here supports a coastal application.

**What would break the transfer is stated so that it can be checked.** If Kandy's ordering is
governed by something the band does not capture, the recommendation is wrong. Section 7.3 names
the candidate, the amplitude of the regional seasonal cycle, and Chapter 9 gives the analysis that
would test whether the band is standing in for it. Until that is run, the transfer rests on Kandy
resembling its band, which is an assumption with evidence behind it and not a demonstration.

## 7.2 What each increment of information is worth

The measurement is possible because the tiers are nested. A lower tier is not a different model,
it is the same model with a stream removed, so the difference between two tiers is information
loss and nothing else.

**What is measured, stated precisely.** The phrase *value of information* has a formal meaning in
decision theory, where it is the reduction in expected loss under a stated decision problem
[@Howard1966]. No decision problem is specified here, and predictive error stands in for loss.
The quantity reported throughout this chapter is therefore the **marginal predictive value of an
observation stream, using the reduction in out-of-sample daily root mean square error as the loss
surrogate, at a fixed position in a fixed ordering of streams**. The shorter phrase is used
informally in the rest of the thesis, and it means this. Work that defines an explicit decision
loss, weighting misclassified air quality categories by population and vulnerability, is
measuring something related and not identical [@Choi2026].

Two consequences follow from the surrogate and both bound what the chapter can conclude. A stream
that would change a decision without much changing average error is under-valued here, which is
plausible for episode warning, where the loss is concentrated in a few days a year. And because
the estimator shrinks a tier back toward the tier below when the new stream does not help,
**the ladder cannot find that a stream is harmful**, only that it is not usable. That is the
right behaviour for measuring what a rational user could obtain from optional information, and it
means a rung of approximately zero should be read as no attainable improvement rather than as no
information present.

{{tbl:T7_1}}

{{fig:ladder}}

Reported as the median across cities of the per-city percentage reduction in daily root mean
square error, never as a ratio of medians and never averaged across metrics.

**The unit of uncertainty here is the city, not the city-day.** The panel holds
{{claim:frame.city_days}} city-days, and quoting that as a sample size would be wrong by a wide
margin, because days within a city are strongly correlated and a long record would then count as
independent evidence many thousands of times over. Taking the median of per-city values already
stops long records dominating the point estimate. Intervals are obtained by resampling **cities**
with replacement:

| step | median | interval over cities |
|---|---:|---:|
| the first two sensors | {{claim:step.bud0c_bud1}} per cent | {{claim:boot.ghap.pooled.first2.lo}} to {{claim:boot.ghap.pooled.first2.hi}} |
| monitors three to six | {{claim:step.bud1_bud2}} per cent | {{claim:boot.ghap.pooled.stn3to8.lo}} to {{claim:boot.ghap.pooled.stn3to8.hi}} |
| a background series | {{claim:step.bud2_bud3}} per cent | {{claim:boot.ghap.pooled.bg.lo}} to {{claim:boot.ghap.pooled.bg.hi}} |

Those intervals are wide, and they should be. **The one that is not wide is the one the thesis
leans on hardest**: monitors three to six are bounded above by
{{claim:boot.ghap.pooled.stn3to8.hi}} per cent across resamples of the panel, so the absence of
that effect is established far more tightly than the presence of either other effect. The first
two sensors and the background are both real and neither is pinned down to better than roughly a
factor of two.

### Cities are not independent of each other either

Resampling cities is an improvement on resampling city-days, but it still assumes that one city
tells you nothing about another, and that assumption is false here. Cities share national
monitoring programmes, instrument procurement, siting conventions, calibration practice, operators
and processing chains. {{claim:clust.largest_n}} of the panel's cities belong to a single national
network. A resample that happens to draw many of them is not the diverse sample its size suggests.

The panel's {{claim:frame.cities}} cities fall into {{claim:clust.n_clusters}} clusters when a
cluster is defined as a network within a country. Resampling clusters with replacement, and then
cities within each drawn cluster, propagates both levels of variation instead of only the lower
one.

| step | median | over cities | over clusters | wider by |
|---|---:|---:|---:|---:|
| the first two sensors | {{claim:clust.first2.median}} per cent | {{claim:boot.ghap.pooled.first2.lo}} to {{claim:boot.ghap.pooled.first2.hi}} | {{claim:clust.first2.lo}} to {{claim:clust.first2.hi}} | {{claim:clust.first2.widening}} |
| monitors three to six | {{claim:clust.stn3to6.median}} per cent | {{claim:boot.ghap.pooled.stn3to8.lo}} to {{claim:boot.ghap.pooled.stn3to8.hi}} | {{claim:clust.stn3to6.lo}} to {{claim:clust.stn3to6.hi}} | {{claim:clust.stn3to6.widening}} |
| a background series | {{claim:clust.bg.median}} per cent | {{claim:boot.ghap.pooled.bg.lo}} to {{claim:boot.ghap.pooled.bg.hi}} | {{claim:clust.bg.lo}} to {{claim:clust.bg.hi}} | {{claim:clust.bg.widening}} |

Every interval widens, by about half again. The city count therefore overstates the effective
sample size, and an interval quoted over cities is optimistic. That correction is owed to the
reader whichever way it points.

It does not move any conclusion, and it strengthens one. The background remains the largest gain
with a lower bound of {{claim:clust.bg.lo}} per cent. The first two sensors keep a lower bound of
{{claim:clust.first2.lo}} per cent. Monitors three to six remain bounded above by
{{claim:clust.stn3to6.hi}} per cent, and a null that survives a wider interval is strictly stronger
than one that does not, so the redundancy result is improved by the objection rather than damaged
by it.

The clustering also has an asymmetry worth naming, because it falls in a useful place. The
deep-tropical cities of Section 7.3 occupy {{claim:clust.inv.maiac.n_clusters}} clusters between
{{claim:clust.inv.maiac.n_cities}} cities, so that band is almost entirely singletons and there is nothing to
correct: its paired interval is
{{claim:clust.inv.maiac.lo}} to {{claim:clust.inv.maiac.hi}} points under clustering, unchanged to
four decimal places. **The dependence problem belongs to the pooled numbers, which one national
network dominates, and not to the band-stratified result that the recommendation for Kandy rests
on.**

One statistic had to be withdrawn from this analysis after it was computed. An intra-class
correlation over all cities returned values between 0.82 and 0.99 [ledger F.104], which reads as
overwhelming network dependence and is an artefact of the grouping: {{claim:clust.singletons}} of the
{{claim:clust.n_clusters}} clusters hold one city, a single-city cluster has no internal variance
by construction, and its whole deviation is therefore booked as between-cluster variance. Computed
only over cities that have a cluster sibling the figure is {{claim:clust.bg.icc}} for the
background rung and {{claim:clust.stn3to6.icc}} for the redundancy rung. Those are substantial and
they are meaningful. The width ratio in the table above is the diagnostic that carries no such
artefact, and it is the one to read.

Four features of the table matter more than its ordering.

**Free data is not negligible.** Static geography, which is terrain, roads, land cover, night
lights and population, and which is available for every city on Earth at no cost, buys
{{claim:step.geography}} per cent. That is comparable to what the first local instrument buys.

**Geography beats the satellite level.** The annual satellite level buys
{{claim:step.satellite}} per cent, less than the geography. The reason is straightforward once
seen: an annual level cannot touch day-to-day variance, and daily error is what daily variance is
made of.

**Additional monitors add almost nothing this model can use.** At
{{claim:step.bud1_bud2}} per cent the effect is not small but absent, and Section 7.4 shows it is
the most estimator-robust result in the study.

### Where the redundancy actually begins, which is earlier than the ladder suggests

The rung above adds two stations, and that number was not chosen by measurement. The budget
specification defines the stream as at most two local low-cost sensors and annotates it as **the
deployed Kandy budget**, so the ladder's first ground rung was sized to match the demonstration
city. That is a defensible design choice, because the point is to price the tier Kandy actually
occupies. It also means the two-station figure had never been checked against the alternatives.

Sweeping the count from one to eight on the same frame, the same sensorless rung and the same
seed, so that only the number of stations varies:

**A single station buys {{claim:stn.one_gain}} per cent**, against
{{claim:step.bud0c_bud1}} for two. Paired within city, **the second station adds
{{claim:stn.second_adds}} percentage points**, and no count between two and eight beats one
station by more than {{claim:stn.max_extra}} percentage points.

**The saturation is at one, not at two.** The headline belonged to the first station all along,
and "the first two sensors" overstates what the pair contributes. The redundancy this chapter
reports therefore begins at the **second** monitor rather than the third, which makes the finding
stronger than the ladder's own rungs can express: one local observation captures essentially
everything a city-mean model can extract from local observation.

**The band Kandy belongs to gives the same answer.** In the deep tropics a single station buys
{{claim:stn.dt_one_gain}} per cent and a second adds {{claim:stn.dt_second_adds}} percentage
points paired within city, improving {{claim:stn.dt_improving}} of {{claim:stn.dt_n}} cities. No
band shows a measurable second-station gain, so the recommendation does not depend on reading the
pooled result across a band boundary.

⚠ **One number in that analysis is a trap, and it is worth showing rather than hiding.** In the
temperate band the *median gain* rises by {{claim:stn.temp_diff_of_medians}} percentage points
when a second station is added, which looks like a large effect and is not one. Paired within
city the median is {{claim:stn.temp_second_adds}}, and only {{claim:stn.temp_improving}} of
{{claim:stn.temp_n}} cities improve at all. The apparent jump is produced by one city moving from
no gain to a third of its error while another loses almost as much, so the city sitting at the
median changes. **A difference of medians is not the median difference**, and this project's
standing rule of taking the median of per-city ratios rather than a ratio of medians exists
precisely to stop that number being reported as an effect.

⚠ Three further limits. The temperate interval runs to {{claim:stn.temp_hi}} on
{{claim:stn.temp_n}} cities, so that band is **underpowered rather than null**, and the same is
true of the deep-tropical upper bound at {{claim:stn.dt_hi}}. The sweep prices stations for a
**daily city-mean**, and a second station is what makes a between-sensor comparison possible at
all, which is how the calibration of Section 7.9 and the sensor reliability figure were obtained.
**A pair buys quality assurance that the model does not score**, and the finding is that a second
station does not improve the model, not that it is worthless.

Two further qualifications belong with the row, because it is the one most likely to be quoted as
procurement advice. It concerns **attainable predictive improvement in a daily city-mean**, so it
says those monitors add little that this model can exploit for that quantity, and not that they
carry no information. A monitor also serves compliance, public reporting and calibration, none of
which this measurement addresses. And the monitors in question were **not sited for this
purpose**: they are the networks each panel city happens to operate, so what is measured is the
marginal value of additional monitors *as actually placed*. Where a sensor is placed is itself
part of the information problem and a developed research question in its own right
[@Verghese2022; @Choi2026]. Nothing here shows that monitors placed deliberately across a city's
land-use contrast would be worth as little, and Chapter 9 recommends exactly such a campaign for
a different purpose.

**A background series is the largest single gain measured.** At {{claim:step.bud2_bud3}} per
cent it exceeds every other rung, and the instrument that would supply it is the one air quality
programmes are least likely to fund, because a rural monitor serves no constituency.

That last row needs a qualification stated in its own right rather than in a footnote, because
the row is the most quotable number in this thesis and the qualification changes what it means.

**What was actually supplied to the model was not a rural station.** It was the tenth percentile
of the target city's own outer-ring monitors, five to fifteen kilometres from the centre. Those
monitors share the city's instruments, calibration, siting conventions and operator. The measured
gain is therefore the gain from *a background series constructed this way*, and part of it could
be more of the same network rather than regional air. Read without this paragraph, the row says
that a rural monitor is worth {{claim:step.bud2_bud3}} per cent, and the experiment does not
establish that.

### Testing it with a network the city never sees

The question is answerable without new instruments. The background can be rebuilt from **a
different city entirely**, thirty to three hundred kilometres away, whose monitors the target
never sees, and passed through an identical chain so that only the background differs. Below
thirty kilometres a donor is really the same urban area; beyond three hundred it is a different
air mass and should stop helping.

| background supplied | median gain over the previous rung |
|---|---:|
| the city's own outer ring | {{claim:step.bud2_bud3}} per cent |
| a donor city at a median of {{claim:donor.median_km}} km | {{claim:donor.gain_reproduced_pct}} per cent of it recovered |

**A network the city has never seen recovers about three quarters of the effect.** The rung is
carrying genuine regional information and is not mostly a same-network artefact.

Three limits on that reassurance, and the first is the one that matters.

**It bounds the artefact from above; it does not measure it.** Recovery falls with donor
distance, from {{claim:donor.reproduced_near}} per cent at {{claim:donor.km_near}} kilometres to
{{claim:donor.reproduced_far}} per cent at {{claim:donor.km_far}}. The donors sit far outside the
city while the own-network ring sits just outside it, so the residual gap conflates *same
network* with *much closer*. The honest statement is that the same-network component is **at
most** the residual quarter, most likely less, and this test cannot divide it further.

**The recovery fraction itself moved when the ladder was corrected**, from a recorded 79 per cent
to {{claim:donor.gain_reproduced_pct}} on the rebuilt bottom rung [ledger F.54]. A stronger
sensorless rung leaves less headroom for any background to recover, and the independent one loses
more of that headroom than the city's own. The direction survives; the margin is smaller than the
project previously recorded.

**Coverage is partial and biased.** Only {{claim:donor.pairs}} of the panel's cities have a donor
in range at all; {{claim:donor.no_donor}} have none. The cities that do are concentrated where
urban monitoring is dense, and the deep-tropical cell is the thinnest. In that cell, which is
Kandy's own, recovery falls to {{claim:donor.reproduced_deep_tropical}} per cent at a median
donor distance of {{claim:donor.km_deep_tropical}} kilometres. **The independent evidence for
this rung is weakest exactly where the demonstration city sits**, which is a reason to prefer the
band-stratified recommendation of Section 7.3 over the pooled one, and not only for the reason
Section 7.3 gives.

A genuine rural background station remains the only thing that settles it, which is why
Chapter 9 lists one even though it ranks second for Kandy.

## 7.3 The recommendation inverts in the tropics

The pooled table is misleading if read as advice, and {{tbl:T7_2}} is the finding.

One feature of that table has to be read before its numbers, because it looks like an error and
is not. **Its city column sums to {{claim:frame.bands}} and the panel has
{{claim:frame.cities}}.** The difference is {{claim:frame.unbanded}} cities drawn from a single
national network, which are scored in every pooled result in this chapter and carry no latitude
band, so they cannot appear in a band-stratified row. Excluding them from the stratification is
deliberate. Assigning them a band would place a large block of cities from one country and one
network into one cell, which is the confound a registered amendment was written to remove, and
Section 7.6 gives that history.

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

### Does the inversion survive an interval?

A median of thirteen cities is a thin basis for a procurement recommendation, and the difference
between two medians hides whether the same cities drive both. The comparison was therefore made
**paired within each city** and bootstrapped over cities, since days within a city are not
independent and the panel's true unit here is the city.

| satellite stream | advantage of two sensors over a background | cities favouring sensors |
|---|---:|---:|
| the fused product | {{claim:inv.ghap.median}} points, from {{claim:inv.ghap.lo}} to {{claim:inv.ghap.hi}} | {{claim:inv.ghap.frac_cities}} per cent |
| the raw retrieval | {{claim:inv.maiac.median}} points, from {{claim:inv.maiac.lo}} to {{claim:inv.maiac.hi}} | {{claim:inv.maiac.frac_cities}} per cent |

**On the fused product the inversion does not survive.** The interval spans zero and the sensors
win in barely half the cities, which is a coin flip. Read alone, that version of the result would
not support a recommendation, and an earlier version of this work stated it as though it did.

**On the raw retrieval it does.** The interval excludes zero and the sensors win in
{{claim:inv.maiac.frac_cities}} per cent of the band. This is the version the recommendation
rests on.

The two rows are the same thirteen cities and the same procedure, differing only in the satellite
stream, which makes this the sharpest consequence of Section 7.5 anywhere in the thesis. **The
contaminated covariate did not merely shift the numbers; it destroyed the significance of the
finding that matters most for the demonstration city.** A monitor-trained product understates
what a monitor is worth, and in the deep tropics it understated it enough to hide the inversion
entirely.

Two limits stay attached. The band holds thirteen cities and the interval is correspondingly
wide, running to {{claim:inv.maiac.hi}} points at the upper end. And the pairing test was not
pre-registered, so it is reported as an analysis performed after the result was known.

The reversal is not a curiosity. It means the recommendation this thesis is most likely to be
quoted for is the wrong recommendation for the city it was built for, and a reader who takes the
pooled row without the band row will act on it.

**Latitude is a label here, not a mechanism, and the distinction is not pedantic.** What the
measurement establishes is that cities sorted into these bands differ in the ordering, which is a
latitude-stratified empirical difference. It does not establish that latitude causes the
difference, and nothing in this design could. Band travels with at least six other things:
instrument class, which Section 7.6 shows differs by a factor of
{{claim:confound.deep_tropical_lcs_pct}} against
{{claim:confound.other_bands_lcs_pct}} per cent low-cost units; network density and design;
driver completeness; the seasonal structure of the meteorology; the source mix; and the
institutional history that determines which cities publish at all.

A mechanism can be proposed, and the honest status of the proposal is that it is consistent with
the data rather than tested by it. In the deep tropics the seasonal cycle of the regional
background is weak, so a background series carries less information that a sensorless model has
not already extracted from reanalysis and geography; in the temperate bands a strong winter
accumulation regime makes the background series carry a great deal. If that is right, the
operative variable is the amplitude of the regional seasonal cycle and latitude is standing in
for it. Testing it would require sorting cities by that amplitude directly and checking whether
the ordering follows the amplitude or the latitude, which is one of the analyses Chapter 9 lists
and this thesis did not run.

The practical consequence survives the uncertainty about mechanism, which is why the
recommendation is stated as it is. A programme in Kandy should read the row for the band Kandy
falls in, because that row is the closest available match to Kandy on every one of the correlated
variables at once, whichever of them is doing the work. That is a weaker justification than a
causal one and it is sufficient for the decision.

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

One result survives every learner including ridge: the third-through-sixth monitor rung stays
at approximately zero, with a spread of {{claim:learner.all_spread_bud1_bud2}} percentage points.
The redundancy of those monitors is the most robust finding in the study.

### And is it a property of the information, or of the order it was added in?

Every number in {{tbl:T7_1}} is a marginal gain at a position in a fixed sequence. What the table
reports is therefore the value of a stream **given the streams below it and before the streams
above it**, which is not the same as an intrinsic property of that stream. Information interacts:
a stream that looks redundant when added late may have carried a great deal when added early.
The estimand is a path-dependent marginal, and this thesis names it that way.

One reordering cannot be run, and saying why is more informative than the reordering would have
been. The background enters as a second regressor whose coefficient is fitted against local
station data, so a rung that added a background before any local station has nothing to fit
against and cannot be constructed. **A background series is only ever priceable given some local
observation.** That is a property of the decomposition rather than a limitation of the
implementation, and it means the ladder's order is partly forced rather than chosen.

What can be permuted is where the background sits relative to the later monitors. Running the
chain both ways across {{claim:order.cities}} cities, so that both routes end at the same
information set and only the interior order differs:

| quantity | in the production order | with the background moved one step earlier |
|---|---:|---:|
| what a background series buys | {{claim:order.bg_after_8stn}} per cent | {{claim:order.bg_after_2stn}} per cent |
| what monitors three to six buy | {{claim:order.stn3to8_no_bg}} per cent | {{claim:order.stn3to8_with_bg}} per cent |

**The background result is order-robust.** It is the largest step in either position, and moving
it changes it by about two percentage points.

**The redundancy result is order-robust in its conclusion and not in its magnitude.** Monitors
three to six buy {{claim:order.stn3to8_with_bg}} per cent once a background is present, which
is more than twenty times the production figure and still small. Part of that difference is not
extra local information at all: with more stations the fitted background coefficient is estimated
more sharply, so some of the apparent gain is a better-estimated background rather than a
better-observed city. The defensible statement is that the rung is small under both orders, and
not that it is a fixed quantity.

**And the two orders do not reach the same skill despite reaching the same information.** Median
final error differs by {{claim:order.endpoint_gap}} micrograms per cubic metre between the
routes. The shrinkage estimator accumulates differently along different paths, so path dependence
is a property of this measurement and not only of the presentation. It is reported here rather
than left for a reader to discover.

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

The claim needs its boundary stated, and Section 3.4 states it. That such products leak is
known, and evaluation practice already guards against it [@Just2020]. The addition here concerns
the **signature** of the leak rather than its existence: when the quantity being estimated is the
marginal value of an observation, the contamination surfaces in the neighbouring term, so the
diagnostic that a careful analyst would reach for is the one that cannot see it. The
pre-registered test in this study was that diagnostic, and it returned a clean result on
contaminated data.

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

This is the confound that most limits the band result, and it deserves more than a note. Low-cost
sensor response depends on humidity, aerosol composition, sensor age and the duration and design
of the calibration, and there is no universal calibration procedure that removes this
[@Zhang2025]. A band that is mostly low-cost is therefore not only a different climate regime, it
is a different measurement regime, with a different error structure in both the fitting data and
the held-out target. Some part of what the band contrast measures is instrument behaviour rather
than atmosphere, and no analysis in this thesis can separate the two.

The consequence is carried into the recommendation rather than left here. Kandy's own instruments
are low-cost, so the low-cost stratum is the right analogue for it, and reading Kandy against a
band that happens to share its instrument class is a better match than reading it against the
pool. That is a defence of the recommendation and not of the mechanism: it makes the advice
appropriate for Kandy while leaving open what the band contrast is actually made of.

There is now a named route by which the confound could operate, which is more than this thesis
could offer when the confound was first recorded. [@Senarathna2026] calibrated low-cost sensors
against reference monitors in two Sri Lankan climatic zones and found that a calibration fitted in
the wet season, applied to dry-season data, produces a mean absolute percentage error of 26.57 per
cent. Seasonal calibration drift of that size in a stratum that is
{{claim:confound.deep_tropical_lcs_pct}} per cent low-cost, against
{{claim:confound.other_bands_lcs_pct}} per cent elsewhere, is a concrete mechanism by which part of a
band difference could be instrument behaviour rather than atmospheric behaviour. It does not
overturn the inversion, and it is not evidence that the inversion is spurious. It converts the
confound from something this thesis could only label into something a future study can measure,
which is the more useful state for it to be in.

{{fig:confounds}}

The gain from additional sensors depends on what they are, and the class matters. Median
shrinkage weight placed on sensors three through six is {{claim:class.LCS.w_bud2}} for low-cost
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

### What identifies the representativeness error, other than the model itself

That answer is complete for the delivered interval and incomplete for the observation model that
Section 6.2 specifies. The specification writes a point measurement as the areal field plus an
instrument offset plus an error with two parts, a measurement term and a representativeness term
covering sub-grid variability the model cannot resolve. The implementation estimates the second
from the local variability of the field itself. That is elegant, and it is circular: the model is
being asked how wrong its own unresolved spatial structure is, and a model that understates
sub-grid variability would understate this term in the same proportion.

The quantity can be identified without the model. Wherever two or more instruments fall inside a
single model cell, the spread between them measures the point-versus-area error directly, with no
field consulted and no pattern assumed. The panel contains {{claim:srep.panel_cells}} such cells
holding {{claim:srep.panel_stations}} instruments across {{claim:srep.panel_cities}} cities, and
the Kandy transect of Chapter 8 contributes {{claim:srep.kandy_cells}} more.

| source | within-cell coefficient of variation | times the model |
|---|---:|---:|
| panel instruments sharing a cell | {{claim:srep.panel_cv}} | {{claim:srep.ratio_panel}} |
| Kandy transect sites sharing a cell | {{claim:srep.kandy_cv}} | {{claim:srep.ratio_kandy}} |
| the model estimator at the same places | {{claim:srep.model_cv}} | 1.0 |

The estimator is too small by a factor of {{claim:srep.ratio_panel}} on the panel and by at least
{{claim:srep.ratio_kandy}} at Kandy. The Kandy figure is a lower bound, because three of its seven
sites were censored at an upper sampling limit and censoring can only shrink an observed spread,
so the bias runs toward the model and cannot have produced the result.

Two things follow, and they are different. The delivered interval is unaffected, because its width
comes from the temporal anchor's conformal quantiles rather than from this term, and the coverage
figures above already show that width to be right for an areal quantity. What is affected is the
observation model, which the specification requires to exist before any regulatory record is
ingested. Had this term been used as written, the first point-level interval built against a real
Kandy measurement would have been too narrow by a factor of three or more, and the resulting
apparent over-confidence would have looked like an error in the field rather than an error in the
comparison. The term must be taken from co-located instruments. The delivered interval is
calibrated for an areal quantity, and it understates point-level uncertainty.

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

### Three attempts to make chemistry carry more weight, and what each returned

Composition is the one axis on which this model makes a claim it does not model. That invites a
deeper test, and three were run. **Two returned nothing usable, and the reasons differ in a way
worth recording.**

**Does composition explain what latitude band only labels?** Section 7.3 states that band is a
stratifying label and names a candidate mechanism it does not test. A chemical mechanism is
available: a city whose particulate is mostly secondary is chemically a regional problem, so a
background observation should be worth more there and a local monitor less. That direction was
fixed in a script committed four days before any correlation was computed, which is why it could
be tested one-sided. It was pre-registered with its detection limit before the analysis ran.

**The result is undetectable at this power.** All {{claim:chem.mech.undetectable}} confirmatory
hypotheses return correlations far below what the design could see: the largest is
{{claim:chem.mech.largest_rho}} against a detection limit of {{claim:chem.mech.mde}}. That is not
a near miss, it is an order of magnitude short.

The reason is worth more than the result. The registration expected
{{claim:chem.mech.registered_n}} cities and the analysis scored {{claim:chem.mech.n}}, because
**controlling for band removes the cities that carry no band**, which are exactly the single
national network described in Section 7.3. That deviation is what makes the following table
possible, and the table is the finding:

| group | cities | correlation of composition with the acquisition advantage |
|---|---:|---:|
| pooled | {{claim:chem.cluster.pooled.n}} | {{claim:chem.cluster.pooled.rho}} |
| excluding the single network | {{claim:chem.cluster.banded.n}} | {{claim:chem.cluster.banded.rho}} |
| that network alone | {{claim:chem.cluster.single_network.n}} | {{claim:chem.cluster.single_network.rho}} |

**A correlation of {{claim:chem.cluster.pooled.rho}} survives in neither group on its own.** It
is produced entirely by the gap between two clusters that differ in network, instrument class and
country as well as in chemistry. This is the confound of Section 7.6 reappearing wearing a
chemical variable's name, and the only reason it was caught is that the registered design
controlled for band rather than pooling.

**Is the split chemically coherent species by species?** The decomposition asserts that the
background is aged and the increment fresher. Chemistry orders the species without ambiguity:
black carbon is emitted directly and has no secondary source, so it is the purest available
tracer of fresh local material, while sulphate forms over hours to days and is the purest tracer
of aged regional material. Applying one common estimator to each species predicts that the local
fraction of black carbon should exceed that of sulphate.

It does not: {{claim:chem.species.f_black_carbon}} against {{claim:chem.species.f_sulphate}}.
**That reversal is not reported as a refutation, because the test does not work.** Dust and sea
salt act as negative controls, since an inland valley has no local source of either and their
true local fraction is near zero. The estimator returns {{claim:chem.species.f_dust}} for dust
and {{claim:chem.species.f_sea_salt}} for sea salt, the two highest values of any species. An
estimator that ranks material with no local source above the purest local tracer is measuring
something other than local origin, and what it is measuring is episodic temporal variability:
dust and sea salt arrive in transport events and are the most episodic species present.

**The species prediction is therefore untested rather than refuted.** Reporting the reversal as a
chemical result would be reporting an instrument failure as a finding, which is the error
Chapter 5 exists to document. ⚠ The controls were read after the run rather than declared before
it, which is a weakness in the design and not a defence of it.

**What an intervention could remove.** The third attempt is the one that works, and it repairs a
claim Section 6.6 withdraws. With the local share and the secondary share both known, the
locally emitted primary share is bounded from both directions without further assumption. At
Kandy it lies between **{{claim:chem.intervention_lo}} and {{claim:chem.intervention_hi}} per
cent** of concentration. The lower figure is material that is both local and primary, and
responds immediately to local emission control. The upper figure is the whole local increment,
and requires every locally formed secondary particle to disappear as well. The gap between them
is precisely what cannot be resolved without speciated measurement in the city.

## 7.11 Exposure and attributable burden, as an illustrative projection

Chapter 2 gave health as one of the two stakes, and the delivered field supports an estimate.

This section is deliberately the least load-bearing in the chapter, and it is placed last for
that reason. Everything before it measures something and reports what the measurement can carry.
What follows takes the delivered field, which has unresolved level uncertainty, unresolved spatial
uncertainty and an open discrepancy against three of its four independent point records, and
projects it through a published concentration-response function that was estimated elsewhere. The
arithmetic then returns a single confident-looking number of deaths. That mismatch between the
discipline of the measurement and the apparent precision of the output is a property of burden
estimation rather than of this field, and the honest label for the result is an **illustrative
projection**, not a finding. It is included because a thesis that names health as a stake and then
declines to quantify it has ducked its own framing, and excluded from every summary of what the
work establishes.

{{fig:burden}}

**The area mean under-states exposure.** People are not distributed uniformly over the basin;
they concentrate in the higher-concentration core. For {{claim:exposure.year}} the unweighted
basin mean is {{claim:exposure.area}} micrograms per cubic metre, the residential-weighted mean
is {{claim:exposure.residential}}, and the population-weighted mean is
{{claim:exposure.dynamic}}. That is an uplift of {{claim:exposure.uplift_pct}} per cent over the
area mean, and any health statement should use the weighted figure.

**The attributable burden.** Projecting the population-weighted exposure through a published
concentration-response function [@Burnett2018] against the national mortality baseline gives
{{claim:burden.deaths}} attributable deaths per year, with a **response-function-conditional
interval** of {{claim:burden.ci_low}} to {{claim:burden.ci_high}}. That is an attributable
fraction of {{claim:burden.fraction_pct}} per cent, of which {{claim:burden.avoidable}} would be
avoidable if concentrations met the World Health Organization guideline [@WHO2021].

The interval is named that way because of what it does not contain. It propagates the published
uncertainty in the response function and nothing else. It carries no uncertainty from the
concentration field, from the population weighting, or from the level discrepancy of Section 7.8,
and a full interval would be wider than this one by an amount this thesis has not estimated.
**It should not be read as a total uncertainty interval on the burden.**

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

It establishes that the level and the seasonal cycle transfer across the panel of
{{claim:frame.cities}} cities and four latitude bands, and that the value of each observation
stream can be measured rather than argued.

It establishes that the ordering of that value differs between bands, and that the pooled
recommendation is the wrong one in the band the demonstration city belongs to.

**The scope of both statements is the panel, and the panel is not the world.** Every city in it
is a valley or basin, so nothing here supports a coastal application. Every city in it publishes
enough concurrent monitoring to be scored, which selects for exactly the institutional capacity
that the cities this method exists for do not have. Two of the four bands rest on cells of seven
cities. Where a result is quoted outside this thesis, the qualifier that belongs with it is
across the monitored valley and basin cities that could be assembled, and not globally.

It does not establish that the model is accurate at Kandy, because that cannot be established
with the observations Kandy has. In particular it does not establish that the neighbourhood-scale
field is correct, and Chapter 8 gives the measurement showing that it is not, together with the
reason no product built from the available covariates would be. What this chapter establishes is
what the model is entitled to claim, which is a weaker statement and the only honest one
available.
