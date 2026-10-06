[STATUS: DRAFT — AI reference text; the author rewrites. Written last, from `90_evidence_map.md`.
About 330 words; trim to the journal limit.]

# Declared information budgets: what an air-quality observation is worth to a city without monitors

## Abstract

Many cities must decide what to measure before they can estimate their daily PM2.5, and have little
evidence to decide with. We measured what each type of observation adds to a daily city estimate
that starts from free global data: reanalysis weather, a map of the city's surface and a satellite
aerosol retrieval. Each estimate was built under a declared information budget, a list of admitted
data streams that the code checks in both directions. Local stations and a background series were
then added one rung at a time. In each city, held-out stations scored every rung, and every
comparison was paired within city and averaged over 21 random station splits. We developed the
method on 47 cities and then tested it once on 76 fresh cities, registered before their data were
retrieved (72 scored). The first one or two local stations reduced daily error by 8.5 % [3.1, 25.1],
less than half the discovery estimate. Four further stations added 0.2 points. A background series
from the same network reduced error by 41 % [27, 63] and outranked the first local stations: by 24.6
points [4.1, 47.8] on ordinary days and by 59.3 [33.9, 67.7] for exceedances of the WHO 24-hour
guideline, where the first stations added nothing detectable. The findings held under a richer starting estimate (adding chemical-transport PM2.5, fires, NO2, rain and
terrain), under three other learners, including a deep sequence model, none of which beat gradient
boosting, and with every city's full station network. For a within-city map, cities split: in about two
thirds, interpolation from a few to a few dozen stations overtook a free land-cover layer, in the rest it
never did, and choosing sites by design rather than at random gained nothing. Re-run on full station
records, which brought in the first deep-tropical network, tropical cities fell within the range of
temperate ones. Whether local stations gain value relative to a background in the
tropics could not be tested: public archives hold four fresh dense tropical networks. Two striking
exploratory results did not survive split-averaging and pairing. We report both as a caution for
studies that rest on one random split.

**Keywords:** PM2.5; value of information; monitoring network design; pre-registration; low-cost
sensors; satellite aerosol; paired inference
