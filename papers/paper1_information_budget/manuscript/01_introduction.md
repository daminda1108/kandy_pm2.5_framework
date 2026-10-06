[STATUS: DRAFT. Headline finding in §1.3 is PROVISIONAL, awaiting an F-code and ledger entry
from the ongoing paired-vs-pooled reanalysis (see WRITING_LOG.md, 2026-09-23 entries). Do not
submit or circulate this section until that resolves.

REGISTRATION STATUS, checked 2026-09-23: both pairing results in §1.3 (the panel-wide MAIAC
comparison and the deep-tropical band comparison) are exploratory. Neither is pre-registered.
The deep-tropical result is ledger entry F.97c, whose own text says the pairing test was not
pre-registered and should be reported as post hoc; an earlier CLAUDE.md summary implying
otherwise was wrong. OSF registration `bkpyr` covers C1/S3, S1, S2, R2, and R3 only, no
band-inversion test. The registrations that did test ladder predictions are `g6hqb`
(re-validation) and `z89kt`, precipitation; see `D:\ProjectCD\#writing\registrations.json` for
their verdicts. §1.4's "pre-registered" language applies only to the eight spatial-limit tests.

STYLE, 2026-09-23: full rewrite pass to remove AI-typical cadence (em dashes, connective-tissue
filler, repeated rhetorical shapes). See `papers/WORKFLOW.md`, "De-AI-ifying the prose."]

# 1. Introduction

## 1.1 The gap: monitoring networks are designed without a rigorous account of what each sensor buys

More than half the world's urban population lives in a city with no regulatory-grade air
quality monitor [CITE: PNAS 2423259122]. The gap is not evenly spread. It falls hardest on
low- and middle-income countries, where a single reference-grade station can cost 15,000 to
40,000 US dollars to install and a comparable amount every year to keep running [CITE:
value-of-information sensor placement lit], against public budgets with far more urgent claims
on them. The question a city planner or a research group actually faces is rarely "should we
monitor." It is "where does the next dollar of monitoring capacity buy the most information,"
and right now there is no rigorous, generalizable answer to that question. Sensor-placement
studies typically optimize a single city at a time [CITE: Choi & Hummel, ERL 2026], reporting
one aggregate value-of-information number for the municipality studied. None decomposes that
value by the type of information involved. A satellite retrieval, one low-cost sensor, a
regional background monitor, and a dense spatial network are not interchangeable sources of
skill, and no existing study asks whether an answer for one city's information tiers holds for
another city in a different climate with a different monitoring history.

This paper asks that question directly. Given a declared, auditable budget of observation types,
how much predictive skill does each additional type of information actually buy, and does the
answer hold across cities that span temperate, subtropical, tropical, and deep-tropical
climates? We answer it with what we call a declared information budget: a nested set of
observation tiers, each scoped in advance to the data streams it is permitted to use, applied to
a panel of 48 cities with monitoring networks dense enough to serve as ground truth. We validate
the framework with a battery of pre-registered negative-result tests built to find out exactly
where the value of additional information runs out.

## 1.2 Why a declared budget, and why a panel

Separating a regional background signal from a local increment is not a new idea in urban air
pollution. It descends from the three-monitor mass-balance protocol of Lenschow et al. [CITE:
Lenschow2001], and reduced-form and hybrid physical-statistical models have used variants of it
for two decades [CITE: relevant hybrid model lit]. Our contribution is not the decomposition
itself. It is a way to reconstruct that decomposition, and to measure honestly what it costs to
reconstruct, without Lenschow's original three-station requirement. Most of the cities that
would benefit most from a model like this do not have three stations and are unlikely to have
three stations soon. Every tier in our budget states in advance exactly which observation
streams it may draw on: a satellite aerosol product, one co-located ground sensor, a regional
background series, a dense spatial network. We enforce this computationally rather than by
convention, checking that a tier's measured skill can only be attributed to the streams it was
assigned. This closes a failure mode we hit directly in our own early results. A tier that
quietly used more information than it declared, or just as damagingly failed to use information
it was entitled to, distorted every comparison built on top of it in one direction or the other.
Section 2.X describes the coverage-checking mechanism that catches both failures, and treats it
as a contribution of this paper in its own right rather than an implementation detail.

A single city cannot tell you whether a result generalizes or whether it is an accident of that
city's geography, monitoring history, or climate. That is the reason to run this across a panel
rather than validate the framework once and apply it. We assembled a 48-city panel spanning four
climate bands (temperate, subtropical, tropical, and deep-tropical), drawing on OpenAQ,
national monitoring networks including China's CNEMC, and city-level reference archives (Methods
§2.X). We track the deep-tropical band separately throughout this paper. It is the smallest band
in our panel, roughly thirteen cities, and it includes Kandy's own climate regime. It is also, as
we show in Section 4, the one band in which several of the panel-wide conclusions do not hold.

## 1.3 What we found: a real ladder, and a warning about how to measure it

[PROVISIONAL: numbers below await an F-code, see the status note at the top of this file]

Moving from a satellite-only budget to one that includes a single co-located ground sensor buys
the largest jump in spatial skill available to any city in the panel, rich or poor. A second
sensor at the same city buys almost nothing beyond the first. That correction came late: a
2026-09-05 fix to our own earlier draft found we had mislabeled which stations a middle rung of
the ladder actually used, and the corrected result shows the tier saturating after one station,
not two.

A regional background monitor looks like the next lever, and by most accounts the largest one,
when cities are compared as a pooled median across the panel. We caution against trusting that
comparison. When each city is instead compared against itself, pairing its own background-tier
score against its own two-sensor score, the "background is the largest lever" claim does not
survive on the satellite stream we treat as our primary, least-contaminated predictor: a
monitor-independent aerosol retrieval. It does survive on a fused, monitor-blended product, and
the reason is itself informative. That fused product partially encodes the very ground stations
whose marginal value we are trying to measure, so any comparison built on it is tilted toward
flattering the tier below it. Both of these paired comparisons are exploratory findings from this
study, not tests of a pre-registered hypothesis. What holds up on the honest stream, in both the
pooled and the paired analysis, is narrower and more useful: in the deep-tropical band, Kandy's
own climate regime, a single local sensor outperforms a regional background monitor, the reverse
of the panel-wide pooled ordering. We treat this as the paper's more defensible headline. It
survives the stricter test, and it speaks directly to the cities this framework is meant to serve.

We think the mechanism behind this matters beyond the specific result. An unpaired comparison of
panel medians can quietly reverse or erase an effect that the correctly paired, within-city
comparison reveals. This is not a one-off in our analysis. We document two further instances
elsewhere in this study where an unpaired comparison gave the opposite answer to the paired one
(Section 4.X), and we suspect this is a common, under-examined failure in any multi-city
value-of-information or sensor-network study that reports its result as a simple median or mean
across sites, including work already published in this literature that we cannot re-check
without access to the underlying, city-level data.

## 1.4 A second, independent contribution: the limits of learnable spatial structure

Alongside the information-budget ladder, we report a coordinated program of eight pre-registered
tests asking whether the fine-scale spatial pattern of urban air pollution, as distinct from its
city-wide level and its daily shape, can be learned from any predictor set or model family
currently proposed in the literature. These include a Gaussian-process spatial interpolator, a
land-use regression model built on a comprehensive multi-radius road-network predictor set, a
random forest trained on Google DeepMind's AlphaEarth satellite embeddings [CITE: AlphaEarth
2025 arXiv], and seven distinct estimator families scored head to head on identical, withheld
data. Each test carried a stated minimum detectable effect fixed in advance, so a null result
here means something. All eight return the same answer: none of these approaches distinguishes
itself from a simple, static land-cover benchmark by more than the pre-registered detection
threshold.

We do not present this as a discouraging coda. It tells a reader attempting the same kind of
analysis in their own city exactly which further investments are, and are not, likely to move
the needle: a denser spatial network is unlikely to help; a fundamentally different kind of
predictor might. It also speaks directly to a recent claim that AlphaEarth-style foundation
model embeddings capture fine-scale urban air-quality structure [CITE: Alvarez et al. 2025,
AlphaEarth Quito NO2/SO2]. Our results say that claim does not extend to the finer spatial
structure this paper is concerned with, at least not at the scale and resolution of our panel.

## 1.5 Structure of the paper

Section 2 describes the declared-budget framework, its coverage-checking machinery, and the
48-city panel. Section 3 reports the value-of-information ladder, including the pooled-versus-
paired result described above. Section 4 reports the eight spatial-limit tests. Section 5
discusses what this means for a city deciding how to spend its next unit of monitoring budget,
using Kandy, Sri Lanka, the subject of a companion paper applying this framework directly
[CITE: Paper 2, in prep], as the working example, and what the results here do not yet tell us.
