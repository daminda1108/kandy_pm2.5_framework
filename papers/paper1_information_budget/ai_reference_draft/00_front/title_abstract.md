[STATUS: DRAFT — AI reference text; the author rewrites. Written last, from `90_evidence_map.md`.
Revised 2026-10-06 after the external review (ledger F.124): the registered background-versus-local ordering is a
property of how the rungs were built, so the headline is now same-day observation versus calibration. About 330
words; trim to the journal limit.]

# Declared information budgets: what an air-quality observation is worth to a city without monitors

## Abstract

Many cities must decide what to measure before they can estimate their daily PM2.5, and have little
evidence to decide with. We measured what observations add to a daily city estimate that starts from
free global data: reanalysis weather, a map of the city's surface and a satellite aerosol retrieval.
Each estimate was built under a declared information budget, checked in code in both directions, and
observations were added one rung at a time. Held-out stations scored every rung, and every comparison
was paired within city and averaged over 21 random station splits. We developed the method on 47 cities
and tested it once on 76 fresh cities, registered before their data were retrieved (72 scored). Used
only to recalibrate the free estimate, the first two local stations reduced daily error by 8.5 %
[3.1, 25.1] and four more added 0.2 points; a same-network background series, used day by day, reduced
it by 41 % [27, 63]. These registered results held under a richer starting estimate, three other
learners and full station networks. A post-hoc re-analysis that used every stream the same way showed
that the apparent advantage of the background came from that difference in use: two stations read on
the same day reduced error by 59 % [45, 69], whether they were the first local stations, a background
quantile or any two others, and with the number of stations matched the paired differences stayed within
one point. With full networks, a background summarising ten or more stations added a further 2.5 points
[1.1, 3.7]: a small effect of count, not of kind. What a monitor-less city gains is the daily reading,
not a particular kind of station. For a within-city map, neither free
products (a built-up layer or a satellite PM2.5 surface) nor interpolation from three to eight stations
ranked neighbourhoods usefully (rank correlation about 0.1); after correcting for multiple testing only
3 of 23 cities showed interpolation overtaking the free layer, and choosing sites by design gained
nothing. Tropical cities could not be distinguished from temperate ones. Two striking exploratory
results, and the registered ordering itself, did not survive closer comparison. We report all three as
a caution: registration fixes how a comparison is run, not whether it compares like with like.

**Keywords:** PM2.5; value of information; monitoring network design; pre-registration; low-cost
sensors; satellite aerosol; paired inference
