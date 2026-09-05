# Chapter 5. What was tried and did not work

This chapter is longer than the one describing the model that did work, and it is placed before
it rather than in an appendix. The reason is that the pattern across these eight attempts turned
out to be more useful than any of them individually, and the model in Chapter 6 is largely a
consequence of that pattern rather than of a design decision taken at the start.

Each section states what was expected, what happened, what it cost, and what it established.
The last of those is the column that matters, and it varies enormously between the eight.

{{dia:timeline}}

The eight are not of equal weight and the chapter does not present them as though they were. Four
changed the design of the model that followed. Four established something narrower, either
closing a question or exposing a defect in how the work was being checked. A reader who wants the
argument rather than the record can take the first group and Section 5.9.

**The four that changed the design.** Section 5.1 established that physics transfers between
cities while a fitted parameterisation does not, which is why the final construction imposes its
physics and learns only the temporal behaviour. Section 5.3 established that a learned spatial
field trained across cities does not recover within-city structure. Section 5.4 established that
a model given coordinates will memorise them, which produced the admissibility rule governing
every tier in Chapter 6. Section 5.8 supplied the bounded spatial null that Chapter 8 is devoted
to explaining.

**The four that established something narrower, or nothing.** Section 5.2 is an identifiability
diagnostic that closed a modelling direction. Section 5.6 records five reconstructions of the
background, all rejected, which is the origin of the constraint in Section 6.6. Section 5.7
records defects found by audit rather than by review, and is the reason Chapter 10 exists. None
of the three produced a better model and each prevented a wrong claim.

Section 5.5 belongs in this second group for a different reason, and it is the one section whose
placement is itself an argument. It consumed the most time of any entry here and established the
least, and Section 5.9 explains why. A reader short of patience should still read it, because the
contrast with Section 5.8 is the chapter's conclusion.

## 5.1 A physics-informed network transferred between continents

**What was expected.** A neural network constrained to obey an advection-diffusion-deposition
equation should learn a representation of transport that is a property of the physics rather
than of the city it was fitted in. If so, a network trained where data is plentiful could be
transferred to a city where it is not, and the physical constraint would carry the transfer.

**What happened.** A time-dependent formulation was fitted at Medellin, reaching a coefficient
of determination of 0.932, and transferred to Chiang Mai, where it reached 0.765 with a bias of
-0.59 [ledger stage 2, 76,261 parameters]. By the standards of the transfer literature that is a
good result. It was nonetheless abandoned.

**What it cost.** Several months, and the larger part of the project's computational budget.

**What it established.** The transferred quantity was not what the design assumed. What survives
transfer is the **form** of the physics, which was imposed rather than learned and would have
been imposed identically without any network. What does not survive is the fitted parameterisation,
because those parameters encode the emission field and the boundary-layer climatology of the
city they were fitted in, and those are exactly the things that differ between cities. The
constraint made the model physically plausible without making it transferable, and plausibility
was not the problem.

This is the first appearance of a distinction the rest of the thesis depends on. **Imposing
physics and learning physics are different operations, and only the first transfers.** Chapter 6
imposes.

## 5.2 A rigid physical form fitted across cities

**What was expected.** If a single parameterised form for valley confinement, taken from the
mountain meteorology literature, could be fitted jointly across several cities, the fitted
parameters would characterise valley behaviour in general and could be applied to a new valley.

**What happened.** Two of the form's six parameters, a trapping depth and a valley shape
exponent, were driven onto their bound constraints by the fit. Cross-validated skill was uneven:
correlation of 0.863 at one city and 0.323 at another [ledger stage 3 LOOCV].

{{fig:bound}}

**What it cost.** Less than the previous attempt, because the failure was legible early.

**What it established.** Parameters that saturate their bounds are not estimates. The data does
not contain the information needed to identify them, and a fit that reports them anyway is
reporting the boundary of the search space rather than a property of the atmosphere. This is
identifiability failure, and the useful response is not a better optimiser but a declaration:
those parameters are imposed, not estimated, and the model should say so. That declaration
became the fourth of the properties set out in Chapter 6.

An unexpected consequence, and it belongs here rather than in a footnote. For most of this
project's history the outcome was recorded as **all six** parameters saturating rather than two.
The correction came from regenerating the figure during preparation of this thesis, not from
anyone questioning the claim, and the project's own epistemic ledger still carried the
overstatement until that point. A number that makes an argument stronger is the least likely
number to be checked. Section 5.7 is about errors of that kind, and this one is an instance of
the class it describes.

## 5.3 A conditional neural process trained across cities

**What was expected.** A neural process trained on several cities with dense monitoring should
learn to map from covariates to a spatial field, and could then be applied to a city it had
never seen. This is the most direct machine-learning attack on the problem and it is what most
readers would try first.

**What happened.** The model was built, trained across three source cities, and applied to Kandy
producing a full year of hourly fields. Cross-city correlation reached 0.599 on average
[ledger v14]. Calibrated intervals were obtained by conformal post-processing and covered close
to their nominal rate at all three source cities.

Then the output was examined. The fields were smooth. They were consistent with the annual mean,
they reproduced the seasonal cycle, and the diurnal cycle had roughly the right shape. They
contained almost no spatial structure. The model had learned to produce a plausible city-mean
concentration and to vary it gently in space in a way that was not wrong so much as
uninformative.

**What it cost.** The largest single block of work in the project, and it produced deliverable
output that was held back rather than published.

**What it established.** Three things, and the third is the one that mattered.

A model can be right on every aggregate diagnostic and still fail at the task it was built for.
Annual mean, seasonal cycle, diurnal cycle and interval coverage were all acceptable, and none of
them is sensitive to whether the spatial field carries information.

A learned field is not automatically an informative field. Smoothness is what a flexible model
produces when the covariates do not constrain the output, and it is difficult to distinguish
from appropriate regularisation by inspection.

And the assessment problem of Chapter 1 applies to the assessment itself. There was no
measurement at Kandy against which the fields could be scored, so the decision to hold them back
was a judgement, not a test. Chapter 8 finally converted that judgement into a measurement, four
months later.

## 5.4 Fine-tuning on the two sensors that exist

**What was expected.** If a model transferred from other cities is smooth, fine-tuning it on
Kandy's own two sensors should sharpen it. The sensors are the only local information available
and using them is the obvious next step.

**What happened.** After fine-tuning, agreement at the exact sensor coordinates went from a
correlation of 0.43 to 0.9999, and the error at those points fell to 0.12 micrograms per cubic
metre [ledger sim2real]. On the grid, the annual mean rose from 22.1 to 37.0 micrograms per
cubic metre, which is a physically impossible response to fitting two points more closely.

**What it cost.** Little in time. A great deal in what it revealed.

**What it established.** The model had been given latitude and longitude as inputs. With two
sensors and coordinates available, the cheapest way to fit the training data is to memorise the
two coordinate pairs as identity keys and predict the sensor value at those keys. Everywhere
else the network is unconstrained, and the field it produces there is arbitrary.

This is the origin of the admissibility rule that Chapter 6 states formally: **a model may not
receive an input that identifies the location it is predicting**. Latitude and longitude are the
obvious case. The subtler cases took longer to find, and one of them is in Section 5.7.

It also established the diagnostic. A metric evaluated at the training points cannot detect
memorisation, because memorisation is what makes that metric good. Only a quantity evaluated
away from the training points can, and here the grid mean was that quantity.

## 5.5 Five attempts to find spatial structure, and what none of them reported

**What was expected.** Kandy has a large within-city gradient. The roadside survey of Chapter 3
measured concentrations varying by a factor of {{claim:spatial.obs_spread}} across the city.
Some covariate should encode it.

**What happened.** Five separate searches, over about four months.

The first tested whether the emission proxy correlated with observed concentration across
monitored cities, and found that it did, weakly. The second tested whether a learned spatial
pattern could beat the imposed one, and found a rank correlation near 0.14 [ledger track S]. The
third tested whether transport dynamics could be learned from the monitored panel, and found
that they could not, for the reason that the monitors are all sited on valley floors and
therefore never sample the vertical gradient. The fourth applied a general-purpose
earth-observation embedding, and found nothing. The fifth built a full land-use regression
predictor set, {{claim:lur.predictors}} predictors at {{claim:lur.total_stations}} stations
across {{claim:lur.cities}} cities, and moved the pooled rank correlation from 0.273 to 0.275
[ledger F.61].

**What it cost.** Four months, and a settled belief that the spatial problem was
information-limited.

**What it established.** Very little, and that is the finding. Not one of the five stated, before
it ran, what size of effect it would have been able to detect. A power analysis conducted much
later established that at their sample sizes they could only have detected residual correlations
between {{claim:null.min_detectable_lo}} and {{claim:null.min_detectable_hi}}. They therefore
excluded a very large learnable signal and said nothing whatever about a moderate one.

For four months the project held a belief that its own evidence did not support. The belief
happened to be approximately correct, as Section 5.8 shows, but it was held for the wrong
reason, and a null result reported without a detection limit converts a limitation of the
experiment into a claim about the atmosphere.

{{dia:taxonomy}}

## 5.6 Five reconstructions of the regional background

**What was expected.** The separation of local from regional concentration in Chapter 6 depends
on a background term. The first construction of that term produced a partition that disagreed
with source-apportionment literature, so the term was rebuilt.

**What happened.** It was rebuilt five times. A cap, a re-levelling, and three successive
reformulations. Each was scored against the same criteria and each was rejected.

**What it cost.** Roughly six weeks, spread over two months.

**What it established.** After the fifth rejection the reason became clear, and it was not that
the constructions were poor. The background is required to satisfy four conditions
simultaneously: to reproduce an independently measured regional concentration, to remain below
the total at every hour, to yield a local fraction inside a bracket taken from source
apportionment, and to reproduce a documented seasonal pattern. Those are four constraints on a
term with three degrees of freedom [ledger F.17]. The system is over-determined, and no
construction satisfies all four because none can.

Recognising that changed the response from building a sixth version to stating a limitation. It
also produced the constraint that eventually resolved the partition, described in Chapter 6:
local sources emit continuously, so the background can never exceed the total, and a background
that does is over-estimated rather than describing an unusual hour. Imposing that single physical
condition moved the local fraction to {{claim:partition.f}} and it is not sensitive to the one
free parameter it introduces.

The five rejected versions were not wasted, but they were not efficient either. The
over-determination argument could have been made before the first rebuild rather than after the
fifth.

## 5.7 Defects found by audit rather than by review

**What was expected.** That the model's own numbers were what the documentation said they were.

**What happened.** They were not, repeatedly, and the discrepancies were found by recomputing
rather than by anyone noticing.

The most serious concerned the sensorless tier. Its specification admits three information
streams, and its registration said the same. The implementation used one of them. Because every
gain on the ladder of Chapter 7 is measured against the tier below it, every reported gain above
that tier had been measured against an artificially weakened baseline. The headline first rung
fell from a superseded value to {{claim:step.bud0c_bud1}} per cent when this was corrected.

Others followed once the numbers were being recomputed systematically. A gain measured across two
information streams had been reported under the name of one of them. A statistic describing
instrument classes had never been recomputed after the run it described was replaced. The panel
size and the number of city-days were both stale. One city had been scored in a tier whose data
it did not have. A published fused product had been used as an independent satellite observation
when it is trained on the very monitors the study prices.

**What it cost.** A full development cycle, and the retraction of several statements that had
been made confidently.

**What it established.** Two things that changed how the work is done.

The first is that admissibility must be checked in both directions. A check that a tier does not
use information it is not entitled to is half a check. The other half is that a tier does use
everything it is entitled to, because a tier that quietly under-uses its budget inflates every
measurement taken above it. Both assertions now exist in code.

The second is the machinery this thesis is written with. Every number in this document is
generated from a scored file at build time, and the build refuses to complete if the prose and
the data disagree. Chapter 10 describes it. It was written because nine numbers in an earlier
draft had gone stale against their own sources, including one quantity that was stated three
different ways in a single document without anyone noticing.

## 5.8 A learned spatial pattern, pre-registered and refuted

**What was expected.** This is the only one of the eight where the expectation was recorded in
full before anything was run.

The registration [OSF 2jyfg] stated the benchmark, the detection limit and the bar. The benchmark
was the best single globally available predictor, built-up land-cover fraction measured within
2.4 kilometres, which reaches a median per-city rank correlation of {{claim:phase1.best_rho}}
across {{claim:phase1.cities}} cities and {{claim:phase1.stations}} stations. The smallest
improvement the frame could detect at eighty per cent power was {{claim:phase1.min_detectable}}.
The bar was set at their sum, {{claim:phase2.bar}}, and the registration recorded the prediction
that it would not be cleared.

**What happened.** A pattern was learned subject to a conservation constraint, so that its
spatial mean is exactly one and it can therefore move material without creating it. Three
estimators were fitted, with leave-one-city-out throughout. The best reached
{{claim:phase2.rho_learned}}. The median paired difference against the benchmark was
{{claim:phase2.delta}}, better in {{claim:phase2.better_in}} of {{claim:phase1.cities}} cities,
at a p-value of {{claim:phase2.p_value}}.

{{fig:learnedbar}}

**What it cost.** About a week, because the preceding phases had already established the frame,
the benchmark and the detection limit.

**What it established.** A bounded claim, which none of the five nulls in Section 5.5 produced:

> On {{claim:phase1.cities}} cities and {{claim:phase1.stations}} stations, a learned within-city
> pattern does not beat the best single globally available predictor by more than
> {{claim:phase1.min_detectable}} in rank correlation.

That is a different kind of statement from "no spatial signal was found". It says what was
excluded and, by implication, what was not. An effect smaller than the detection limit remains
entirely possible, and a campaign that sited monitors deliberately across land-use contrast
would be a different experiment with a different answer.

Two further results came out of the same work and both are used later. The conservation
constraint holds to {{claim:phase2.gauge_drift}} across degenerate cases including a saturated
pattern and an overflow-range input, so a learned pattern can misplace material but cannot create
it. And no engineered emission surface beat a single freely available raster: a sector-weighted
composite reached {{claim:phase0.rho_sector}} against the production surface's
{{claim:phase0.rho_traffic}}, and adding industrial land use from open mapping data did not
change that conclusion.

## 5.9 The pattern across the eight

Reading {{dia:taxonomy}} again with the eight accounts in hand, the attempts lie close to a
diagonal. An approach yielded about as much when it failed as it had declared before it started.

The five spatial nulls of Section 5.5 declared nothing and yielded nothing, despite consuming
four months and producing a belief the project acted on. The registered test of Section 5.8
declared a benchmark, a detection limit and a bar, consumed a week, and produced a statement that
can be quoted, disputed and superseded by a better experiment. The two are the same finding. They
differ only in whether anyone wrote down beforehand what would count as evidence.

That is not a claim that pre-registration is a general remedy. It is an observation about eight
specific attempts in one project, and the sample is neither large nor independent. But the
ordering is consistent enough to have changed how the remaining work was done, and the practice
described in Chapter 7 is the direct consequence.

{{tbl:T5_1}}
