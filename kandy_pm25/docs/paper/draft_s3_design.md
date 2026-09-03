# 3. Design: budget-matched validation across 48 cities

*Rewrite and expansion of `draft_s5_validation.md` per `rewrite_plan_2026-08-22.md` §3. Includes
the claims-audit item on the spatial estimator's honest framing.*

---

The measurement in §4 requires a validation design in which information can be withheld
deliberately and the withholding is verifiable. This section describes that design and the three
confounds it caught.

## 3.1 Borrowed ground truth

Kandy cannot validate this model: it has two low-cost sensors and no reference monitor, which is
the condition the model exists for. So the model is validated **where the observations exist**
and demonstrated where they do not.

{{fig:protocol}}a states the design. For each panel city we withhold most of the network, give
the model only what a target city's budget would allow, and score against the stations withheld. A city with 30 monitors is treated
as a city with two, and the other 28 become the test set. The design measures what the model
would have produced had that city been as data-poor as the target — the counterfactual structure
of an optimal-design problem [@Ryan2016; @Dehideniya2018] — which is the counterfactual
a ministry actually faces.

Drivers are ERA5 meteorology [@Hersbach2020] with composition priors from GEOS-CF [@Keller2021]
and CAMS [@Inness2019].

{{fig:protocol}}b and c show how much was withheld and over how long.

**The panel:** {{claim:frame.cities}} cities, 32 countries, four latitude bands,
{{claim:frame.city_days}} city-days. A median of {{claim:frame.med_days_per_city}} days and
{{claim:frame.med_held_stations}} withheld stations per city. {{claim:frame.bands}} cities carry
a latitude-band label; the remainder are a single national network treated as one stratum.

⚠ The panel is a **convenience sample with coordinates**, not a designed one. Regulatory and
low-cost networks are sited for compliance and for where people volunteer to host devices — not
across land-use contrast, which is what a spatial validation design would require. §5 returns to
what that costs.

## 3.2 Withholding has to be enforced, not intended

The design's validity rests entirely on tiers actually receiving what they are declared to
receive. That turns out to be harder than it sounds, and we report the failures because they are
the reason the checks exist.

The scored sensorless tier used **one of the three streams its budget admits**. The
specification, the pre-registration and the implementation all disagreed with one another, and
nobody noticed for five days, because the defect is invisible in every pooled number: a rung that
under-uses its budget simply makes every gain above it look larger. Correcting it moved the
headline first rung from 25.6% to {{claim:step.bud0c_bud1}}%.

Three further checks were added after failures of the same family, each of which produced a
clean, plausible, wrong number:

- a **city** scored inside a rung whose streams it lacks — {{claim:coverage.bud0c_cities_missing_a_stream}} of
  {{claim:coverage.bud0c_cities_scored}}, which moves the first rung to
  {{claim:step.bud0c_bud1_stream_complete}}% when enforced;
- a stream that **merged cleanly and arrived empty**, keyed and typed correctly, fitted by a
  gradient-boosted learner without a warning;
- a covariate that was **not the independent observation it was labelled as** (§4.5).

The general lesson is worth more than the individual fixes: **a tolerant learner will absorb an
admissibility error that a strict one would raise.** Every one of these was found because
something refused to accept the data, and three of the four refusals had to be written first.

## 3.3 Pre-registration, and what it cost us

Every test reported in §4 and §5 was registered before it ran, with its priors and — the part
that matters — an explicit statement of what result would make us abandon the hypothesis.

Of the registered predictions in the most recent rounds, **the majority were refuted**, including
several of ours that were central to the narrative we expected to write. The registered
prediction that a finer grid would recover within-city contrast was refuted (§5.3). The
prediction that a fused satellite product would show measurable excess skill from leakage was
refuted (§4.5) — and its refutation redirected us to where the leakage actually was. The
prediction that a dispersion layer improves spatial rank was refuted (§5.4).

We report this proportion deliberately. A registered design that never refutes its authors is
not doing anything.

## 3.4 What the spatial estimator does and does not measure

An earlier version of this work reported a fine-spatial rank correlation as though it were a
straightforward skill statistic. It is not, and the honest framing is narrower.

The estimator compares, within each hour, the model's per-station anomaly after removing the
network mean against the observed anomaly. It therefore measures **the ordering of stations
relative to each other**, conditional on the level being right — which the gauge condition (§2.1)
guarantees. It does not measure whether the map is right at unmonitored locations, and it is
computed on a median of a handful of stations per city, which is a thin basis for a rank
statistic.

⚠ Where a city has too few usable station pairs the estimator returns **undefined**, not zero.
An earlier version of this work reported one such city's undefined value as a measured null. We
report "—" for those cities and count them separately.

## 3.5 Independence of the demonstration

The demonstration city contributes nothing to the panel, and the panel contributes nothing to the
demonstration city's parameters. This matters because the model's temporal anchor is calibrated
to the demonstration city's two sensors, so **any comparison against those sensors is in-sample
and is reported as such** — never as validation. The checks in §6 that carry weight are those
against records that played no part in construction.

---

## Drafting notes, to remove before submission

- Figures: the protocol figure is placed. A study-area map for the demonstration city is still
  wanted in §6.
- "32 countries", the 25.6% pre-correction figure, and the median-stations-per-city count need
  claim tokens.
- §3.3's "majority were refuted" should be replaced by an exact count once the registered-outcome
  table is assembled for §7.
