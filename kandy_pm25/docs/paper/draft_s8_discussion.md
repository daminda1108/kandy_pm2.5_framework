# 8. Discussion and conclusions

*Rewrite per `rewrite_plan_2026-08-22.md` §8.*

---

## 8.1 What the exactness buys

The single design decision this work rests on is that a lower tier is recoverable bit-exactly
from a higher one. It sounds like an engineering nicety and it is not: it is the precondition for
every number in §4.

The usual way to price an observation is to remove it and refit. But the refitted model is a
*different* model, so the difference measures information loss confounded with model change, and
the two are not separable after the fact. With exact nesting the comparison is between one model
and itself, minus a stream. That is why we describe §4 as a measurement rather than an ablation
study, and it is the property we would ask a reader to carry away if they carry away one thing.

The cost is real and worth stating: the model must be built so that every tier's inputs are
declared and enforced, which constrains the architecture and rules out several convenient
designs. Whether that trade is worth making depends on whether the value-of-information question
is one you need answered.

## 8.2 What the measurement says

Three results seem to us to generalise past this model.

**Free data is undervalued.** Static geography — terrain, roads, land cover, night lights,
population — buys {{claim:step.geography}}%, comparable to a local instrument, at every city on
Earth for nothing. A programme that models badly will underuse it and conclude that monitors are
worth four times what a programme that models well would conclude (§4.4). **The measured value of
an observation is not a property of the observation alone.**

**Density saturates almost immediately.** Monitors three through eight buy
{{claim:step.bud1_bud2}}% — the most estimator-robust result in the study, surviving every
learner tested. For the class of question this model answers, a network's *first* instrument is
worth almost everything and its next several are worth almost nothing. Whether that holds for
questions this model does not answer, such as compliance or exposure at street scale, we cannot
say and do not claim.

**A fused covariate under-prices the observations it was trained on.** This is the result we did
not expect and did not register (§4.5). Fused products [@Wei2023; @vanDonkelaar2021; @Hammer2020]
are now the default covariate in this field. A product trained on a city's monitors encodes part of
what those monitors would say, so adding one appears to buy less — pooled,
{{claim:step.bud0c_bud1}}% against {{claim:maiac.step_bud0c_bud1}}% on a clean stream, and
roughly double that gap in the tropics. The contamination does not inflate the rung that carries
it; **it deflates the rung above.** Any value-of-information analysis built on one will systematically under-price observation.

## 8.3 Where the model stops

§5 locates the limit rather than caveating it. Most within-city variation is sub-grid: the spread
*inside* a typical 1 km cell ({{claim:s2.within_pixel_p90p10}}×) exceeds the spread *across the
map* ({{claim:s2.between_pixel_p90p10}}×). No refinement of the physics changes that, and a
registered test at {{claim:subgrid.fine_res_m}} m confirms it.

The consequence is a change in what the model may be asked, not a reduction in what it is
worth. It cannot identify which part of a cell is most polluted. It can report the range that
cell spans, which is both well-posed and the larger of the two quantities. We are not aware
of a gridded PM2.5 product that currently reports it.

## 8.4 Limitations we consider material

The demonstration city's level carries an unresolved discrepancy across four external records
(§6.2), on the axis this work otherwise calls strong. The panel is a convenience sample sited for
compliance, not for spatial contrast, and no designed alternative exists at this scale. The
background rung — the largest gain we measure — is estimated from a proxy drawn from the same
network in each city, so it partly measures more of the same network. `Bud4` is unvalidated by
construction. And the instrument-class confound cannot be sampled away, because the regime that
most needs a sensorless method is the regime where reference monitoring is scarcest (§4.6).

## 8.5 Conclusion

We set out to build a PM2.5 field for a city that cannot check one, and found that the more
tractable question was the adjacent one: **what would it take to trust such a field, and in what
order should it be bought?**

Answering it required a model that degrades exactly, which is a formulation problem rather than a
physics or a learning problem. Given that formulation, the answer at
{{claim:frame.cities}} cities is that free global data is worth more than the field assumes,
that the second monitor onward is worth close to nothing, that a regional background station is
worth more than either and is almost never funded, and that the ordering inverts in the tropics —
so the pooled recommendation is the wrong recommendation for much of the population it concerns.

For the demonstration city the recommendation is specific: two local stations are worth
{{claim:maiac.deep_tropical_local_advantage}}× a regional background station, which reverses what
the pooled result would have advised.

The measurement is only as reliable as the provenance of the streams it prices. Two of the
streams used here turned out not to be what they were labelled, and both instances are
reported alongside the corrected numbers rather than in place of them.

---

## Drafting notes, to remove before submission

- §8.2's third result is the strongest candidate for a standalone note; decide before submission.
- Tone pass done on §8.3–§8.5. Every number in this section is a token established in §2–§7;
  the section introduces none of its own.
