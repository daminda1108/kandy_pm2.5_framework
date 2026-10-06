[STATUS: DRAFT. Abstract numbers depend on the same provisional result flagged in
01_introduction.md; do not finalize before that resolves. Style pass applied 2026-09-23 (em
dashes removed, cadence reworked; see papers/WORKFLOW.md "De-AI-ifying the prose").]

# Working title

*Declared information budgets for urban PM2.5: what 48 cities say about the value of an
observation, and why the naive way of asking overstates it*

(Candidates considered and rejected: a title naming "global south" or "ML-infused" was rejected
on 2026-08-22 as factually wrong. The panel spans high-income and low-income cities, and machine
learning plays a minor role in the ladder itself. The title should name what is actually being
claimed: a measurement of information value, and a warning about how that measurement is
usually made.)

# Abstract (draft, target ~250 words for ERL)

A city without an air-quality monitoring network faces a real, unanswered question. Which
observation is worth acquiring next: a satellite retrieval, a single low-cost sensor, a regional
background monitor, a dense spatial network? We answer it with a declared information budget, a
framework that nests observation tiers, states in advance exactly which data streams each tier
may draw on, and checks computationally that a tier neither over- nor under-uses what it was
assigned. Across a 48-city panel spanning temperate, subtropical, tropical, and deep-tropical
climates, a single co-located ground sensor buys the largest gain in spatial skill available to
any city, rich or poor, and that gain saturates almost entirely after the first sensor. A
regional background monitor looks like the next biggest lever when cities are compared by their
panel median. It stops looking that way once each city is compared against itself. On our
least-contaminated satellite stream, the paired within-city difference between a background
monitor and a two-sensor budget cannot be distinguished from zero. The apparent advantage
survives only on a fused satellite product that already encodes some of the very ground stations
whose value it is meant to measure. What holds up under the stricter test is narrower and more
useful: in the deep-tropical climate band, Kandy's own regime, a single local sensor beats a
regional background monitor outright. We find the same pattern, an unpaired panel comparison
reversing under a paired one, in two other results in this study, and argue it is a risk for any
multi-city value-of-information analysis reported as a simple median. A companion program of
eight pre-registered tests then asks whether the fine-scale spatial pattern of urban PM2.5, as
opposed to its level and its daily shape, can be learned at all. None of seven model families, a
comprehensive land-use predictor set, or a recent satellite foundation-model embedding beats a
static land-cover benchmark by more than the pre-registered detection limit. Together these
results give a city with a limited budget a concrete basis for its next investment, and give the
field a cautionary result about how that investment should be evaluated.

# Keywords (draft)

air quality monitoring network design; value of information; PM2.5; low-cost sensors;
multi-city panel study; paired comparison; spatial interpolation limits
