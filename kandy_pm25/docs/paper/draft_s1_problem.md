# 1. The problem: modelling where you cannot check

*Rewrite per `rewrite_plan_2026-08-22.md` §1. The gap statement changes from "no field exists for
a Sri Lankan city" to "no model declares its information budget".*

---

Most of the world's population breathes air that nobody measures. Ground monitoring is
concentrated where it was historically affordable, and the deficit is not uniform — it is worst
in exactly the places where concentrations are highest and where the health burden per
microgram falls on the largest populations. The response has been a generation of models that
supply a field where instruments do not: satellite–reanalysis fusions, land-use regressions,
chemical transport models, and increasingly machine-learned combinations of all three.

These models work. The difficulty is not that they are inaccurate; it is that **in the places
they are built for, there is no way to find out.** A model trained where monitors are dense and
applied where they are absent is validated on one population and used on another. The literature
knows this and reports out-of-sample statistics diligently, but the out-of-sample test is almost
always conducted where monitors exist, which is the wrong regime by construction.

## 1.1 The question that is not usually asked

Faced with an unmonitored city, a ministry has a decision to make, and it is not "which model is
most accurate". It is: **what would I have to buy to trust an answer here, and in what order?**
A reference monitor costs tens of thousands of dollars and years of maintenance. A pair of
low-cost sensors costs a few hundred. A rural background station serves no constituency and is
politically the hardest to fund. These are not interchangeable, and the literature offers
remarkably little to distinguish them.

The reason is structural rather than an oversight. Answering it requires knowing what a model
would produce *without* a given observation, and for most models that is not a well-posed
question: removing an input and refitting produces a different model, so the difference between
them confounds information loss with model change. The quantity a ministry needs is not
recoverable from the models the field builds.

## 1.2 What this paper does

We formulate a model in which the question **is** well-posed, and then answer it.

The formulation (§2) declares, per tier, which observation streams it is entitled to use, and
guarantees that a lower tier is recoverable **bit-exactly** from a higher one when a stream is
withheld. Withholding information becomes a controlled operation rather than a refit. That
property — not the physics, which is modest, nor the machine learning, which is standard — is
the contribution, because it is what turns an ablation into a measurement.

We then run the measurement (§3, §4) across {{claim:frame.cities}} cities in 32 countries and
{{claim:frame.city_days}} city-days, with gates registered before scoring. The results are not
what the field's intuition would suggest. Freely available static geography is worth
{{claim:step.geography}}%, comparable to a local instrument. The second through eighth monitors
are worth {{claim:step.bud1_bud2}}% — indistinguishable from nothing. A regional background
station is worth {{claim:step.bud2_bud3}}%, the largest single gain we measure, and is the rung
most programmes never build. And the recommendation **inverts by latitude band**, so the pooled
answer is the wrong answer for the tropics.

§5 reports where the model stops. This is not a caveats section: the limit is located, measured,
and shown to be a limit of *definition* rather than of data — most within-city variation is
sub-grid, so a 1 km field cannot place it however finely the physics is run. §6 demonstrates the
whole apparatus at a city with two low-cost sensors and no reference monitor, checked against
records that played no part in building it. §7 states what the evidence forbids.

## 1.3 What we do not claim

Stated here rather than left for a referee.

We do not claim a validated neighbourhood-scale map. We do not claim the model captures
atmospheric chemistry — it has none. We do not claim the spatial nulls in the literature,
including our own, isolate an information limit; §5.5 shows they share a defect. We do not claim
the framework is validated for coastal regimes at the demonstration city, and we do not present
the transport layer as an accuracy gain, because §5.4 shows it is not one.

What we do claim is narrow: **a formulation whose information budget is declared and whose
degradation is exact, and a measurement of what each increment of observation is worth, made on
that formulation.**

---

## Drafting notes, to remove before submission

- Opening paragraph needs 3–4 citations for the monitoring deficit and the model families named.
- "32 countries" needs a claim token; it is currently hardcoded.
- Check §1.2's forward references against final section numbering before build.
