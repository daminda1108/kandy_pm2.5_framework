# 4. The value of information

*New section per `rewrite_plan_2026-08-22.md` §4.*

---

Section 3 described a design in which information can be withheld exactly. This section reports
what each increment of it is worth. The measurement is possible because of P3: a lower rung is
not a different model, it is the same model with a stream removed, so the difference between
rungs is information loss and nothing else.

All figures are the median across cities of the per-city percentage reduction in daily RMSE —
never a ratio of medians, and never averaged across metrics.

## 4.1 The ladder

{{claim:frame.cities}} cities, {{claim:frame.city_days}} city-days, a median of
{{claim:frame.med_days_per_city}} days and {{claim:frame.med_held_stations}} withheld stations
per city.

| step | median RMSE reduction |
|---|---:|
| `Bud0a → Bud0b` add static geography | **{{claim:step.geography}}%** |
| `Bud0b → Bud0c` add a satellite level | {{claim:step.satellite}}% |
| `Bud0c → Bud1` add 2 local sensors | **{{claim:step.bud0c_bud1}}%** |
| `Bud1 → Bud2` add 6 more sensors | **{{claim:step.bud1_bud2}}%** |
| `Bud2 → Bud3` add a regional background | **{{claim:step.bud2_bud3}}%** |

That table is the paper's central measurement and it repays being looked at rather than read,
because the interesting structure is in the sizes and not in the ranking. {{fig:ladder}}a plots
the same rungs, coloured by what kind of thing each stream is — freely available everywhere, a
local instrument, or a regional one — and the colouring is the point: the free streams and the
purchased streams interleave rather than separating, which is not how a procurement decision is
usually imagined. Panel (b) then breaks the two decisive rungs out by latitude band with the
number of cities printed on the axis rather than hidden in a caption, because a reader who has
to hunt for a sample size is entitled to assume it was hidden. Four features of the pooled
ladder are worth more than its ordering.

**Free data is not negligible.** Static geography — terrain, roads, land cover, night lights,
population, all globally available — buys {{claim:step.geography}}%, which is comparable to what
the first local instrument buys, and it buys it at every city on Earth for nothing.

**The second monitor through the eighth buys nothing.** {{claim:step.bud1_bud2}}% is not a small
effect; it is indistinguishable from zero, and it is the most estimator-robust result in the
study (§4.4). A city with two sensors and a city with eight are, for this model, the same city.

**The regional background is the largest single gain in the programme**
({{claim:step.bud2_bud3}}%), and it is the rung most air-quality programmes never build, because
a rural station serves no constituency.

⚠ **And a caveat that applies to the background rung specifically.** `Bud3`'s background is an
outer-ring proxy drawn from the *same* network in every city, so its gain partly measures "more
of the same network" rather than a genuinely regional signal. Only a true regional network
settles it. We report the number with that qualification attached rather than in a footnote.

## 4.2 Stratification is not optional

The pooled table above is misleading if read as a recommendation, and the stratified table is
the finding.

| band | n | `Bud0c → Bud1` | `Bud2 → Bud3` |
|---|---:|---:|---:|
| deep tropical | 13 | {{claim:band.deep_tropical.step_bud0c_bud1}}% | **{{claim:band.deep_tropical.step_bud2_bud3}}%** |
| tropical | 10 | {{claim:band.tropical.step_bud0c_bud1}}% | {{claim:band.tropical.step_bud2_bud3}}% |
| subtropical | 7 | {{claim:band.subtropical.step_bud0c_bud1}}% | {{claim:band.subtropical.step_bud2_bud3}}% |
| temperate | 7 | {{claim:band.temperate.step_bud0c_bud1}}% | {{claim:band.temperate.step_bud2_bud3}}% |

{{fig:ladder}}b stratifies it. **In the deep tropics the ordering inverts.** Local sensors buy
{{claim:band.deep_tropical.step_bud0c_bud1}}% and the regional background only
{{claim:band.deep_tropical.step_bud2_bud3}}% — the reverse of the pooled result, which is
computed largely from bands the deep tropics is not in. A programme in Colombo or Kampala
following the pooled recommendation would buy the wrong instrument.

⚠ The subtropical and temperate cells are n = 7. We report them and do not build on them.

## 4.3 What kind of instrument, not just how many

The gain from additional sensors depends on what they are. Median shrinkage weight placed on
sensors three through eight: low-cost {{claim:class.LCS.w_bud2}}, reference
{{claim:class.reference.w_bud2}} — a contrast of {{claim:class.w_bud2_contrast}}×. Low-cost
units gain more from replication because per-device error averages down; a reference monitor's
third unit is close to redundant.

⚠ An earlier version of this work reported that contrast as *infinite* (0.000 against 0.900) and
concluded that reference networks gain nothing at all from added stations. That was computed on
a superseded run. The direction survives, the magnitude does not, and any argument resting on
the strong form — including our own use of the low-cost stratum as the Kandy analogue — has to
be re-made rather than inherited.

## 4.4 Is this a property of the information or of the model?

A value-of-information result is worthless if it is really a statement about one estimator.
Re-running the first rung across four learners [@Ke2017; @Chen2016; @Prokhorenkova2018]:

| learner | `Bud0c → Bud1` |
|---|---:|
| gradient boosting (shipped) | {{claim:learner.histgbm_shipped.step_bud0c_bud1}}% |
| gradient boosting, shallow | {{claim:learner.histgbm_shallow.step_bud0c_bud1}}% |
| random forest | {{claim:learner.randomforest.step_bud0c_bud1}}% |
| ridge regression | **{{claim:learner.ridge_linear.step_bud0c_bud1}}%** |

Two results in this section are easy to state and hard to believe from prose alone, and they sit
together in one figure for that reason. {{fig:streams}}a prices the same two monitors under four
different estimators; {{fig:streams}}b swaps the satellite stream from a fused product to a raw
retrieval and shows which rung moves. Read together they make the same point from opposite
directions — that a value-of-information number is a joint property of the information, the
estimator, and the provenance of everything else in the tier — and neither panel is
interpretable without the other beside it.

Panel (a) first. Across the three non-linear learners the spread is
{{claim:learner.nonlinear_spread_bud0c_bud1}} percentage points. **Ridge collapses**, reporting
{{claim:learner.ridge_linear.step_bud0c_bud1}}% — because on a 68-feature sensorless tier a
linear model cannot exploit the free data, so the monitor appears to rescue it.

That is the useful reading, and it is a result rather than a nuisance. **The measured value of a
monitor depends on how well you exploit the data you already have.** A programme modelling badly
will conclude that monitors are worth four times what a programme modelling well would conclude.
We therefore claim the ladder is robust across **non-linear** estimators, and explicitly not
that "even a linear model reproduces it" — which an earlier version of this work did claim.

🟢 One result survives every learner including Ridge: `Bud1 → Bud2` ≈ 0, spread
{{claim:learner.all_spread_bud1_bud2}} percentage points. The redundancy of the third-to-eighth
monitor is the most robust finding in the study.

## 4.5 What a fused product does to a value-of-information study

The satellite stream in `Bud0c` was initially a published fused PM2.5 product [@Wei2023]. Such
products are trained on ground monitors — in this case ~9,500 stations including the two networks
that supply this study's entire panel — and predicted from a feature set that substantially overlaps the
tier's other streams. The stream was therefore not an independent observation, and its measured
value was a mixture.

We re-ran the ladder on raw satellite aerosol optical depth [@Lyapustin2018; @Levy2013], a
radiometric retrieval trained on nothing:

| | fused product | **raw AOD** |
|---|---:|---:|
| step from `Bud0b` | {{claim:c1.step_fused_ghap}}% | {{claim:c1.step_raw_aod}}% |
| `Bud0c → Bud1` pooled | {{claim:step.bud0c_bud1}}% | **{{claim:maiac.step_bud0c_bud1}}%** |
| `Bud0c → Bud1` deep tropics | {{claim:band.deep_tropical.step_bud0c_bud1}}% | **{{claim:maiac.deep_tropical_first2}}%** |

{{fig:streams}}b puts the two side by side. **The satellite rung barely moves** ({{claim:c1.fused_excess_pp}} pp): the fused product's
apparent value was satellite information that raw AOD supplies as well, not recycled information
inflating its own score. We had registered the opposite prediction.

🔴 **The rung above it moves a great deal.** On an honest stream the first two monitors buy
{{claim:maiac.step_bud0c_bud1}}% pooled rather than {{claim:step.bud0c_bud1}}%, and
{{claim:maiac.deep_tropical_first2}}% rather than
{{claim:band.deep_tropical.step_bud0c_bud1}}% in the deep tropics — **roughly double**.

The mechanism is straightforward once seen. A product trained on a city's monitors already
encodes part of what those monitors would tell you. Adding the monitor therefore appears to buy
less. **The contamination does not inflate the contaminated rung; it deflates the rung above
it.** Our own pre-registered test looked for the excess in the satellite's own skill, found none,
and would have reported the leakage as immaterial had the ladder not been re-run.

**This generalises beyond this study.** Any value-of-information analysis that prices
observations against a covariate trained on those observations will **under-price them** — and
fused products are now the default covariate in this field. We know of no prior work that
reports this, and it is invisible unless the analysis is repeated on a stream with clean
provenance.

## 4.6 Three confounds the pooled numbers hid

Each was caught by a gate declared before the run, not by review, and each would otherwise have
reached print.

**Country × latitude.** A minimum-cost design made the mid-latitude arm 33 cities from a single
country, aliasing latitude band with monitoring network. Corrected by an amendment before
scoring.

**Driver completeness × band.** Boundary-layer height coverage is uneven across bands, so the
ladder was re-run without it. The first rung moves from {{claim:confound.blh.with_blh_step1}}%
to {{claim:confound.blh.without_blh_step1}}% — a shift of {{claim:confound.blh.delta}}
percentage points, which bounds what the uneven coverage can be doing. The band ordering is
unchanged.

**Instrument class × band.** The third is different in kind from the first two, which is why it
gets a figure and they do not. Both of those were design faults with repairs: one was amended
before scoring, the other bounded by a re-run. This one has no repair available. The
deep-tropical cell of the panel is {{claim:confound.deep_tropical_lcs_pct}} per cent low-cost
sensors against {{claim:confound.other_bands_lcs_pct}} per cent in the other bands, so latitude
band and instrument class are entangled in the data and any band-stratified number carries a
class effect inside it. The obvious fix is to sample a better-balanced panel, and
{{fig:confounds}} exists to show why that fix is not available: worldwide, only five
deep-tropical clusters have ten or more concurrent reference stations, against 32 temperate. The
population of candidate cities does not contain a balanced draw.

That last constraint is a finding in itself: **the regime that most needs a sensorless method is
the regime where reference monitoring is scarcest.** We therefore report class-stratified results
throughout rather than chasing a de-aliased sample that does not exist.

---

## Drafting notes, to remove before submission

- Needs `{{fig:ladder}}` (step gain per rung, stratified by band, class and coastal/inland, with
  per-cell n **in the figure**, not the caption) and `{{fig:confounds}}`.
- The instrument-class confound is now tokenised (and the recomputation moved it from 69% to
  {{claim:confound.deep_tropical_lcs_pct}}%, which is why it is a token).
- The BLH ablation is now tokenised as an actual re-run rather than a coverage statistic.
- Still hardcoded: the 5-vs-32 reference-cluster counts, which are a property of the global
  network rather than of anything in this repository and may have to stay a cited figure.
- Decide whether §4.5 stays here or becomes a standalone methods note; it generalises past this
  paper and may be diluted by sitting inside it.
