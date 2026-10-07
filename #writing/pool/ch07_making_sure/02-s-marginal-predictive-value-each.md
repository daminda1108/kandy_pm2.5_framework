## The marginal predictive value of each information stream {#s-marginal-predictive-value-each}

The measurement is possible because the tiers are nested. A lower tier is not a different model,
it is the same model with a stream removed, so the specification and the fitting machinery are
held constant and the difference between two tiers isolates the predictive consequence of
admitting that stream. That is a weaker sentence than saying the difference is information loss
and nothing else, and it is the accurate one. Admitting a stream also changes what the estimator
can fit, how much weight it places on the new tier rather than falling back to the one below, and
how the covariates interact. All of those are consequences of the added information rather than
separate effects, but none of them is nothing.
What the nesting rules out is the confound that matters most: a difference produced by changing the
model, not by changing what it was allowed to see. The registered results below show that nesting
alone does not rule out a second confound, a difference in how two rungs **use** what they see, and
{{ref:s-like-for-like}} measures it.

**What is measured, stated precisely.** The phrase *value of information* has a formal meaning in
decision theory, where it is the reduction in expected loss under a stated decision problem
[@Howard1966]. No decision problem is specified here, and predictive error stands in for loss.
The quantity reported throughout {{this:a-app-panel}} is therefore the **marginal predictive value
of an observation stream, using the reduction in out-of-sample daily root mean square error of the
city-mean concentration as the loss surrogate, at a fixed position in a fixed ordering of streams,
and for a stated use of the stream**. The shorter phrase is used informally in the rest of the
thesis, and it means this. Work that defines an explicit decision loss, weighting misclassified air
quality categories by population and vulnerability, is measuring something related and not
identical [@Choi2026]. Because a stream that would change a decision without much changing average
error is under-valued by this surrogate, every result is also scored on a second loss, the balanced
error of classifying days above the World Health Organization twenty-four-hour guideline of fifteen
micrograms per cubic metre.

### The rungs, and how each uses its stations {#s-rungs-how-each-uses}

Each city's stations are shuffled. The first few form a held-out set, whose daily mean is the
target being scored, and the rest form a pool in shuffled order from which the rungs draw.

The **sensorless rung** uses only what any city could assemble without a monitor: reanalysis
drivers, static geography computed at random points in the city's urban centre, and a daily raw
satellite aerosol retrieval. It is fitted leave-one-city-out, so a city contributes no PM2.5
observation to its own prediction, and its prediction is the median over five learner seeds.

The **first two stations** of the pool enter as a recalibration. Their daily mean is regressed on
the sensorless prediction, and the fitted intercept and slope correct the level and scale of that
prediction. A station's reading on a given day does not enter that day's prediction. **Stations
three to six** enter the same way, as the recalibration recomputed from six stations.

The **background series** is the daily tenth percentile of the city's remaining pool stations,
entered through a second regression alongside the sensorless prediction, so its reading on the day
being predicted does enter that day's prediction. It is drawn from the same network as the local
stations, with no distance criterion, and it is not a rural or regional monitor.
{{ref:s-test-using-independent-donor}} measures how much of it a genuinely separate network
recovers.

These differences of use were stated in the registered design, but their consequence was not
understood until after the confirmation had been scored, and {{ref:s-like-for-like}} reports it.

Each rung is scored in two uses. In the **reconstruction** arm the coefficients are fitted over the
period that is scored, which is the position of a city estimating its past concentrations with
sensors that ran over the same period. In the **prospective** arm coefficients and weights come from
the earlier half of each record and the later half is scored, which is the position of a city that
calibrates and then relies on the model.

### Shrinkage chosen without the scoring stations {#s-shrinkage-cross-fitted}

Each rung is combined with the rung below it through a shrinkage weight between zero and one. A
city's own best weight could only be chosen against its held-out stations, which are the scoring
target and which a city without a dense network does not have. The weight applied to a city is
therefore cross-fitted: the median of the weights that minimise error in every other city. A rung
can then score worse than its parent out of sample. A gain near zero means no usable improvement, a
negative gain is possible, and both are reported. The first version of the ladder chose each
city's weight against its own held-out stations, which guaranteed that no rung could lose skill and
which, as {{ref:s-redundancy-begins}} explains, set the value of a second station to almost exactly
zero.

### One estimate per city: averaging over the random design {#s-averaging-random-design}

Which stations a city happens to hold out and receive is a random draw, and so is the fit of a
gradient-boosted learner, which holds out a random fraction of its training rows to decide when to
stop. Each per-city effect is therefore the **median over twenty-one station splits** of that
city's gain, each computed with the five-seed sensorless rung, before any comparison across cities
is made. The design was adopted because the first version of the ladder, run on one split and one
seed, had produced its most quoted result from a single draw: repeated over twenty alternative
splits, the interval behind the deep-tropical comparison of {{ref:s-recommendation-inverts-tropics}}
excluded zero in only three [ledger F.115]. A learner seed alone moved the first-station gain by more
than the size of several of the effects being measured.

### Pairing within city {#s-pairing-within-city}

Cities differ several-fold in how well the sensorless rung predicts them. When two streams are
compared by the difference between the median gain of each, the comparison is dominated by which
cities happen to score well on each stream rather than by which stream is better within a city,
and the two can point in opposite directions. Every comparison between two streams, rungs or
designs is therefore the median over cities of the **within-city** difference, reported with its
interval and the number of cities in which it is positive. A difference of medians may be shown to
describe the data and is never reported as an effect. The project learned this rule at its own
expense. In the siting experiment of {{ref:a-app-spatial}} the difference of medians between
deliberate and convenience siting was {{claim:site.diff_of_medians}} in favour of deliberate siting,
while the paired median was {{claim:site.paired_median}}, pointing the other way.

### Dependence between cities {#s-dependence-between-cities}

**The unit of uncertainty is the city, not the city-day.** Days within a city are strongly
correlated, so counting city-days as independent would treat a long record as thousands of
separate pieces of evidence. Resampling cities is an improvement on resampling city-days, but it
still assumes that one city tells nothing about another, and that assumption is false here.
Cities share national monitoring programmes, instrument procurement, siting conventions,
calibration practice and processing chains. In the discovery panel, {{claim:clust.largest_n}}
cities belong to a single national network, and the {{claim:frame.cities}} cities fall into
{{claim:clust.n_clusters}} clusters when a cluster is defined as a network within a country, of
which {{claim:clust.singletons}} hold a single city.

Every interval in {{this:a-app-panel}} is therefore a **two-level cluster bootstrap**: clusters
are resampled with replacement, then cities within each drawn cluster, which propagates both levels
of variation. On the discovery ladder, against a bootstrap over cities alone, this widened the
interval for the first two stations by a factor of {{claim:clust.first2.widening}}, for stations
three to six by {{claim:clust.stn3to6.widening}} and for the background by
{{claim:clust.bg.widening}}. A city count overstates the effective sample size, and an interval
quoted over cities alone is optimistic. That correction is owed to the reader whichever way it
points.

### Discovery, registration and gates {#s-discovery-registration-gates}

Everything run on the discovery panel shaped the design and is exploratory. The design was then
frozen, the analysis code was committed, and the hypotheses, the decision rules and the
confirmation cities were registered [OSF ueyfr] before any PM2.5 for those cities was retrieved.
The confirmation was scored once. Four gates stood between the frozen code and a reported number.

1. **Budgets in both directions.** Each rung asserts in code that it uses no stream outside its
   budget, and that it uses every stream inside it; any deliberate omission must be declared where
   the rung is built ({{ref:s-information-budget}}). A third check refuses to score a city that
   lacks one of a rung's streams.
2. **Parity.** The redesigned code reproduces the first version to numerical precision when run
   with the first version's settings, so every difference between the versions is attributable to a declared
   design change rather than to an accident of reimplementation.
3. **Completeness of retrieval.** Every station-year listed in the archive was re-listed and a
   sample of listed but absent daily files was tested, to show that the retrieval had not silently
   lost data before scoring.
4. **Structure of the frame.** Each frame is checked for unique city-day keys, for static
   predictors that are constant within a city, and for stream coverage over the frame's own date
   span, so that a predictor that looks present and is empty refuses rather than scores.

Later analyses on the same data, including the re-analysis of {{ref:s-like-for-like}}, recompute
the registered result in the same run and report how closely it is reproduced, so that a
re-analysis can be checked against the record before it is read.
