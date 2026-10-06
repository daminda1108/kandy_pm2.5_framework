## The marginal predictive value of each information stream {#s-marginal-predictive-value-each}

The measurement is possible because the tiers are nested. A lower tier is not a different model,
it is the same model with a stream removed, so the specification and the fitting machinery are
held constant and the difference between two tiers isolates the predictive consequence of
admitting that stream. That is a weaker sentence than saying the difference is information loss
and nothing else, and it is the accurate one. Admitting a stream also changes what the estimator
can fit, how much weight it places on the new tier rather than falling back to the one below, and
how the covariates interact. All of those are consequences of the added information rather than
separate effects, but none of them is nothing.
What the nesting rules out is the confound that matters: a difference produced by changing the
model, not by changing what it was allowed to see.

**What is measured, stated precisely.** The phrase *value of information* has a formal meaning in
decision theory, where it is the reduction in expected loss under a stated decision problem
[@Howard1966]. No decision problem is specified here, and predictive error stands in for loss.
The quantity reported throughout {{this:ch-validation-without-local-ground}} is therefore the **marginal predictive value of an
observation stream, using the reduction in out-of-sample daily root mean square error as the loss
surrogate, at a fixed position in a fixed ordering of streams**. The shorter phrase is used
informally in the rest of the thesis, and it means this. Work that defines an explicit decision
loss, weighting misclassified air quality categories by population and vulnerability, is
measuring something related and not identical [@Choi2026].

Two consequences follow from the surrogate and both bound what the chapter can conclude. A stream
that would change a decision without much changing average error is under-valued here, which is
plausible for episode warning, where the loss is concentrated in a few days a year. That is a
statement the chapter can test rather than merely make, and {{ref:s-ordering-under-four-loss}} tests it. And because
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

### Dependence between cities {#s-dependence-between-cities}

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

A table of interval bounds makes the widening easy to state and hard to see. {{fig:clusterboot}}
draws the two intervals for each step one above the other. Each row has its own scale, because the
redundancy step is two orders of magnitude smaller than the other two, and what the eye should
take from it is that the red bar is always longer than the blue one and never crosses a
conclusion.

{{fig:clusterboot}}

It does not move any conclusion, and it strengthens one. The background remains the largest gain
with a lower bound of {{claim:clust.bg.lo}} per cent. The first two sensors keep a lower bound of
{{claim:clust.first2.lo}} per cent. Monitors three to six remain bounded above by
{{claim:clust.stn3to6.hi}} per cent, and a null that survives a wider interval is strictly stronger
than one that does not, so the redundancy result is improved by the objection rather than damaged
by it.

The clustering also has an asymmetry worth naming, because it falls in a useful place. The
deep-tropical cities of {{ref:s-recommendation-inverts-tropics}} occupy {{claim:clust.inv.maiac.n_clusters}} clusters between
{{claim:clust.inv.maiac.n_cities}} cities, so that band is almost entirely singletons and there is nothing to
correct: its paired interval is
{{claim:clust.inv.maiac.lo}} to {{claim:clust.inv.maiac.hi}} points under clustering, unchanged to
four decimal places. **The dependence problem belongs to the pooled numbers, which one national
network dominates, and not to the band-stratified result that the recommendation for Kandy rests
on.**

One statistic had to be withdrawn from this analysis after it was computed. An intra-class
correlation computed over all cities returned values between 0.82 and 0.99 [ledger F.104]. That
reads as overwhelming dependence between cities in the same network, and it is an artefact of how
the groups were formed. {{claim:clust.singletons}} of the {{claim:clust.n_clusters}} clusters hold a
single city. A cluster of one has no internal variation by construction, so its entire deviation
from the average is counted as variation between clusters rather than within them. Computed
only over cities that have a cluster sibling the figure is {{claim:clust.bg.icc}} for the
background rung and {{claim:clust.stn3to6.icc}} for the redundancy rung. Those are substantial and
they are meaningful. The width ratio in the table above is the diagnostic that carries no such
artefact, and it is the one to read.

Four features of the table matter more than its ordering.

**Free data is not negligible.** Static geography, which is terrain, roads, land cover, night
lights and population, and which is available for every city on Earth at no cost, buys
{{claim:step.geography}} per cent. That is comparable to what the first local instrument buys.

Geography beats the satellite level. The annual satellite level buys
{{claim:step.satellite}} per cent, less than the geography. The reason is straightforward once
seen: an annual level cannot touch day-to-day variance, and daily error is what daily variance is
made of.

Additional monitors add almost nothing this model can use. At
{{claim:step.bud1_bud2}} per cent the effect is not small but absent, and {{ref:s-dependence-estimator}} shows it is
the most estimator-robust result in the study.

### The ordering under four loss functions {#s-ordering-under-four-loss}

Everything above is measured as a reduction in daily root mean square error, which was chosen
because it is what the estimator already optimises. Nothing in the construction requires it: the
tiers are nested and the shrinkage is fitted identically whatever the scoring rule, so the ladder
can simply be re-scored. Four scoring rules were used, all on the raw
satellite stream of {{ref:s-effect-monitor-trained-covariate}}. The first two are root mean square error and mean absolute error.
The third is the same squared loss computed **only on days in the city's observed top decile**,
which asks the episode question as directly as this frame allows. The fourth is one minus balanced
accuracy at the World Health Organization twenty-four-hour guideline of
{{claim:loss.who_threshold}} micrograms per cubic metre, which makes the loss a question of
classification rather than of magnitude.

| step | daily error | absolute error | episode days | exceedance |
|---|---:|---:|---:|---:|
| the first two sensors | {{claim:loss.first2.rmse}} | {{claim:loss.first2.mae}} | {{claim:loss.first2.tail}} | {{claim:loss.first2.exceedance}} |
| monitors three to six | {{claim:loss.stn3to6.rmse}} | {{claim:loss.stn3to6.mae}} | {{claim:loss.stn3to6.tail}} | {{claim:loss.stn3to6.exceedance}} |
| a background series | {{claim:loss.bg.rmse}} | {{claim:loss.bg.mae}} | {{claim:loss.bg.tail}} | {{claim:loss.bg.exceedance}} |

**Two results survive every scoring rule, and the more exposed of the two is strengthened.**
Monitors three to six buy nothing under any of the four. That is the result most vulnerable to the
objection this test was built to answer, because the natural reply to a redundancy finding is that
extra stations earn their keep on episodes rather than on ordinary days. The episode and exceedance
columns are exactly where that would show, and it does not show there. They show zero in both. **A background series is the largest
gain under every loss, and its largest value of all is on episode days**, at
{{claim:loss.bg.tail}} per cent. That is coherent rather than surprising: if a substantial part of
a valley city's worst days is regional in origin, a series drawn from outside the urban core is
what sees them arriving.

The result that does not survive is the one the demonstration city depends on. Paired within
city across the deep-tropical band, the advantage of two local sensors over the background proxy is
{{claim:loss.inv.rmse}} points on daily error and {{claim:loss.inv.mae}} on absolute error, both
favouring local observation. On episode days it is {{claim:loss.inv.tail}} points and on
exceedance {{claim:loss.inv.exceedance}} points
[{{claim:loss.inv.exceedance.lo}}, {{claim:loss.inv.exceedance.hi}}], both favouring the
background, and the exceedance interval excludes zero.

Both halves of that result are in {{fig:losses}}. The left panel is the table above drawn as bars,
and shows the background as the tallest group under every loss and the redundancy step as nothing
under any of them. The right panel is the deep-tropical comparison, one interval per loss, against
a zero line that separates favouring local sensors from favouring the background. The change of
sign is the visible fact. The number of cities beside each loss is smaller for exceedance, where
not every city could be scored.

{{fig:losses}}

The ordering therefore flips sign between average-day and episode losses. {{ref:s-measurement-priority-ordering}}'s
recommendation is a statement about daily city-mean accuracy, which is the product this thesis
delivers, and it may not be stated without naming that loss. For exceedance detection or health
alerting, which {{ref:ch-kandy-setting-record-stakes}} gives as one of the two stakes, the measurement points the other way.
This does not overturn the recommendation. It scopes it, and the scope was previously assumed
rather than measured.

One fragility belongs with this table rather than after it. The reimplementation used here
reproduces the recorded daily-error inversion closely, at {{claim:loss.inv.rmse}} points against
the {{claim:inv.maiac.median}} recorded in {{ref:s-recommendation-inverts-tropics}}, but its interval **includes zero** where
the recorded one excludes it. The difference is resampling detail on thirteen cities rather than a
disagreement about the estimate. An interval on thirteen cities that excludes zero under one
bootstrap and not under another is not a robust exclusion, and the inversion is quoted throughout
this thesis with that fragility attached.

### Where the redundancy begins {#s-redundancy-begins}

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

The saturation is at one, not at two. The headline belonged to the first station all along,
and "the first two sensors" overstates what the pair contributes. The redundancy {{this:ch-validation-without-local-ground}}
reports therefore begins at the **second** monitor, not the third, which makes the finding
stronger than the ladder's own rungs can express: one local observation captures essentially
everything a city-mean model can extract from local observation.

The band Kandy belongs to gives the same answer. In the deep tropics a single station buys
{{claim:stn.dt_one_gain}} per cent and a second adds {{claim:stn.dt_second_adds}} percentage
points paired within city, improving {{claim:stn.dt_improving}} of {{claim:stn.dt_n}} cities. No
band shows a measurable second-station gain, so the recommendation does not depend on reading the
pooled result across a band boundary.

{{fig:stationcount}} shows the sweep. Read the left panel for shape rather than level: the bands
sit at very different heights, which is the band ordering of {{ref:s-recommendation-inverts-tropics}}, but every line is close
to flat from the first station onward. The right panel is the comparison that decides the
question, each count paired against a single station within city, and every interval sits on or
against zero.

{{fig:stationcount}}

One number in that analysis is a trap, and it is worth showing rather than hiding. In the
temperate band the *median gain* rises by {{claim:stn.temp_diff_of_medians}} percentage points
when a second station is added, which looks like a large effect and is not one. Paired within
city the median is {{claim:stn.temp_second_adds}}, and only {{claim:stn.temp_improving}} of
{{claim:stn.temp_n}} cities improve at all. The apparent jump is produced by one city moving from
no gain to a third of its error while another loses almost as much, so the city sitting at the
median changes. **A difference of medians is not the median difference**, and this project's
standing rule of taking the median of per-city ratios rather than a ratio of medians exists
precisely to stop that number being reported as an effect.

Three further limits. The temperate interval runs to {{claim:stn.temp_hi}} on
{{claim:stn.temp_n}} cities, so that band is **underpowered rather than null**, and the same is
true of the deep-tropical upper bound at {{claim:stn.dt_hi}}. The sweep prices stations for a
**daily city-mean**, and a second station is what makes a between-sensor comparison possible at
all, which is how the calibration of {{ref:s-interval-calibration}} and the sensor reliability figure were obtained.
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
[@Verghese2022; @Choi2026]. Nothing here shows what monitors placed deliberately across a city's
land-use contrast would be worth for a daily city mean. {{ref:s-six-negative-results-their}} asks the related spatial
question on the panel's own dense networks, and there deliberate siting does not beat convenience
siting.

**A background series is the largest single gain measured.** At {{claim:step.bud2_bud3}} per
cent it exceeds every other rung, and the instrument that would supply it is the one air quality
programmes are least likely to fund, because a rural monitor serves no constituency.

That last row needs a qualification stated in its own right, not in a footnote, because
the row is the most quotable number in this thesis and the qualification changes what it means.

**What was actually supplied to the model was not a rural station.** It was the tenth percentile
of the target city's own outer-ring monitors, five to fifteen kilometres from the centre. Those
monitors share the city's instruments, calibration, siting conventions and operator. The measured
gain is therefore the gain from *a background series constructed this way*, and part of it could
be more of the same network rather than regional air. Read without this paragraph, the row says
that a rural monitor is worth {{claim:step.bud2_bud3}} per cent, and the experiment does not
establish that.

### A test using an independent donor network {#s-test-using-independent-donor}

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

The recovery fraction itself moved when the ladder was corrected, from a recorded 79 per cent
to {{claim:donor.gain_reproduced_pct}} on the rebuilt bottom rung [ledger F.54]. A stronger
sensorless rung leaves less headroom for any background to recover, and the independent one loses
more of that headroom than the city's own. The direction survives; the margin is smaller than the
project previously recorded.

Coverage is partial and biased. Only {{claim:donor.pairs}} of the panel's cities have a donor
in range at all; {{claim:donor.no_donor}} have none. The cities that do are concentrated where
urban monitoring is dense, and the deep-tropical cell is the thinnest. In that cell, which is
Kandy's own, recovery falls to {{claim:donor.reproduced_deep_tropical}} per cent at a median
donor distance of {{claim:donor.km_deep_tropical}} kilometres. **The independent evidence for
this rung is weakest exactly where the demonstration city sits**, which is a reason to prefer the
band-stratified recommendation of {{ref:s-recommendation-inverts-tropics}} over the pooled one, and not only for the reason
{{ref:s-recommendation-inverts-tropics}} gives.

A genuine rural background station remains the only thing that settles it, which is why
{{ref:s-measurement-would-settle-most}} lists one even though it ranks second for Kandy.

### A driver that was admitted and never used {#s-driver-admitted-never-used}

The ladder's driver set carries temperature, wind, boundary-layer height and two day-of-year
terms, so wet removal appeared to be absent from its meteorology, and precipitation had been
recorded as a structural gap with no measurement behind it. On inspection the variable was
not missing at all: `total_precipitation_sum` was already in the scored frame, pulled and merged
and never referenced, because it was not in the feature list. A rung holding a driver its budget
admits, in its own inputs, unused. That is the shape of the defect described in {{ref:s-three-confounds-pooled-numbers}},
which moved a headline by eight percentage points when it was found.

It was registered [OSF z89kt] and tested with both arms fitted on one fixed set of
{{claim:precip.cities_scored}} cities, identical seed and machinery, differing in one feature.
Adding precipitation changes the sensorless rung by {{claim:precip.p1}} per cent
[{{claim:precip.p1_lo}}, {{claim:precip.p1_hi}}], which is nothing, and the gains above it are
unmoved: the first two sensors shift by {{claim:precip.first2.paired}} points paired within city.
The redundancy null survives and the background remains the largest single gain.

So there is no repeat of the earlier defect. The unused driver was unused harmlessly, and no
published number in this thesis is overstated because of it. What the test establishes is narrow
and worth stating exactly: an eleven-kilometre reanalysis daily rainfall total does not improve
daily city-mean prediction on this panel. It is not evidence that wet removal does not matter, and
a gauge network or a higher-resolution product remains untested.

Two cautions travel with it. The coverage gate keeps {{claim:precip.cities_passing}} of the
panel's cities, so these figures sit on a subset and are not comparable to the ladder reported
earlier in this section; the two arms are comparable to each other and to nothing else. And the
deep-tropical margin, while it keeps its direction, roughly halves, from
{{claim:precip.p5_without}} to {{claim:precip.p5_with}} points. That margin has now proved
sensitive to the satellite stream, to the loss function and to the driver set, which is three
demonstrations that it is the least robust quantity the band recommendation of {{ref:s-recommendation-inverts-tropics}} rests
on.
