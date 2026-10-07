## Dependence on the estimator {#s-dependence-estimator}

A measurement of this kind is worthless if it is really a statement about one estimator. The
question is whether the value assigned to an observation is a property of that observation or of
the algorithm that was given it. If different learners agree, the value is a property of the
information. If they disagree, then what has been measured is partly the competence of the model,
and the number cannot be quoted without naming the estimator alongside it.

The confirmation was therefore re-scored with the sensorless rung built by three other learners
[OSF jea58]: a pre-trained tabular foundation model [@Hollmann2025], a recurrent network reading
fourteen days of history, and the shipped gradient-boosting learner given ventilation features
derived from the atmospheric physics. The rungs above it were left unchanged. None of the
alternatives improved on gradient boosting. The foundation model's sensorless rung was worse, by
{{claim:v2.learn.L1_vs_hgb.median}} per cent [{{claim:v2.learn.L1_vs_hgb.lo}},
{{claim:v2.learn.L1_vs_hgb.hi}}], and the recurrent network
({{claim:v2.learn.L2_vs_hgb.median}} [{{claim:v2.learn.L2_vs_hgb.lo}}, {{claim:v2.learn.L2_vs_hgb.hi}}])
and the physics features ({{claim:v2.learn.L3_vs_hgb.median}} [{{claim:v2.learn.L3_vs_hgb.lo}},
{{claim:v2.learn.L3_vs_hgb.hi}}]) were indistinguishable from it. At this sample size, a deep model
reading two weeks of history adds nothing a tree model does not already extract from the day's
weather.

All twelve directional verdicts held under the three alternatives ({{fig:robustness}}). One result
moved, and it moved in the direction the design predicts. Under the foundation model's weaker
sensorless rung the first two stations were worth more, and the ordinary-day lead of the background
over them was no longer resolvable, while the exceedance ordering held under every learner.

That is a result and not a nuisance. **The measured value of a station depends on how well the
free data is already being used.** A programme modelling badly will conclude that stations are
worth more than a programme modelling well would conclude. The same dependence appeared on the
discovery panel, where the first-station gain varied widely between learners and was largest where
the sensorless estimate was weakest. The defensible claim is that the registered verdicts are robust
across the non-linear estimators tested, and explicitly not that any estimator reproduces them; on a
sensorless rung of {{claim:bud0c.n_features}} predictors a linear baseline collapses, and the first
station then appears to rescue it. The result that holds under every learner is the small value of
stations three to six, which follows from the construction of the recalibration rather than from the
learner ({{ref:s-registered-confirmation}}).

### Dependence on the ordering {#s-dependence-ordering}

Every registered number is a marginal gain at a position in a fixed sequence. What the ladder
reports is therefore the value of a stream **given the streams below it and before the streams above
it**, which is not an intrinsic property of that stream. Information interacts: a stream that looks
redundant when added late may carry a great deal when added early. The estimand is a path-dependent
marginal, and this thesis names it that way.

One reordering cannot be run under the registered construction. The background enters through a
regression whose coefficient is fitted against local station data, so a background added before any
local station has nothing to fit against. That is a property of how the rung was built, not a
statement that a background is only useful alongside local stations, and the same-day arms of
{{ref:s-like-for-like}} are built differently.

What can be permuted is where the background sits relative to stations three to six. On the
discovery panel, moving the background from after six stations to after two changed its gain by a
few points, and the two routes reached the same final skill. Stations three to six were worth a
little more once a background was present, partly because more stations estimate the background's
coefficient more sharply rather than because they observe the city better. Both conclusions are small
under either order, and neither is a fixed quantity; the first version of the ladder had quoted the
second as a twenty-fold change, a figure that does not survive averaging over station splits.
