## Dependence on the estimator {#s-dependence-estimator}

A measurement of this kind is worthless if it is really a statement about one estimator. The
first rung was therefore re-run across four [@Ke2017; @Chen2016; @Prokhorenkova2018].

The question the figure below answers is whether the value assigned to an observation is a property
of that observation or of the algorithm that was given it. If the four learners agree, the value is
a property of the information. If they disagree, then what has been measured is partly the
competence of the model, and the number cannot be quoted without naming the estimator alongside it.
The figure gives the first rung under each learner. The three non-linear learners should be read
together and the linear one separately, because the gap between them is the finding rather than
noise, and {{ref:s-dependence-estimator}} explains why a linear baseline behaves so differently on a predictor set of
this width.

{{fig:streams}}

Across the three non-linear learners the spread is
{{claim:learner.nonlinear_spread_bud0c_bud1}} percentage points. Ridge regression collapses,
reporting {{claim:learner.ridge_linear.step_bud0c_bud1}} per cent against the shipped estimator's
{{claim:learner.histgbm_shipped.step_bud0c_bud1}}, because on a sensorless tier of
{{claim:bud0c.n_features}} predictors a linear model cannot exploit the free data and the monitor
therefore appears to rescue it.

That is a result and not a nuisance, and it is the useful reading. **The measured value of a
monitor depends on how well the free data is already being used.** A programme modelling badly
will conclude that monitors are worth several times what a programme modelling well would
conclude. This thesis therefore claims the ladder is robust across non-linear estimators, and
explicitly not that even a linear model reproduces it, which an earlier version of this work did
claim.

One result survives every learner including ridge: the third-through-sixth monitor rung stays
at approximately zero, with a spread of {{claim:learner.all_spread_bud1_bud2}} percentage points.
The redundancy of those monitors is the most robust finding in the study.

### Dependence on the ordering {#s-dependence-ordering}

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

The redundancy result is order-robust in its conclusion and not in its magnitude. Monitors
three to six buy {{claim:order.stn3to8_with_bg}} per cent once a background is present, which
is more than twenty times the production figure and still small. Part of that difference is not
extra local information at all: with more stations the fitted background coefficient is estimated
more sharply, so some of the apparent gain is a better-estimated background rather than a
better-observed city. The defensible statement is that the rung is small under both orders, and
not that it is a fixed quantity.

And the two orders do not reach the same skill despite reaching the same information. Median
final error differs by {{claim:order.endpoint_gap}} micrograms per cubic metre between the
routes. The shrinkage estimator accumulates differently along different paths, so path dependence
is a property of this measurement and not only of the presentation. It is reported here rather
than left for a reader to discover.
