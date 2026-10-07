## What additional stations buy for a map {#s-what-stations-buy-map}

The tests above ask what can be placed in a city without any local observation. A city that
acquires monitors asks a different question: how well can it rank its own neighbourhoods from
cleanest to dirtiest once it has some stations, and how does that skill grow as stations are
added? That question was registered before it was scored [OSF rqn4y], with three dated
amendments [OSF 26hp8; OSF 4whsc; OSF 4qs9c], and it is the only spatial test in this thesis that
prices observations rather than covariates.

**Design.** The test uses the densest monitoring networks in the public archives. In each city a
fixed set of held-out sites, at least ten or a third of the network, whichever is larger, is set
aside, and a growing number of fitting stations, from three upwards, is drawn from the remainder.
Each estimator predicts the long-term mean at the held-out sites, and its skill is the within-city
rank correlation between predicted and observed means. The estimators are the built-up land-cover
raster that served as the benchmark in {{ref:s-six-negative-results-their}}, which uses no
stations at all; land-use regression; inverse distance weighting; kriging; regression kriging; and
four learned arms, two neural processes trained across cities and a tabular foundation model
with and without coordinates. Every verdict rests on paired within-city differences, never
on the pooled medians. The primary frame held eighteen cities in seven countries, only one of them
tropical. The same registered code was later run on each site's full record [OSF fu59b], which
raised the frame to twenty-three cities in nine countries and added a deep-tropical city, Bangkok,
with a dense network.

**The registered result.** Of the eleven confirmatory predictions, seven held in the primary
frame, three were refuted and one could not be tested because one of its estimators failed the
registered positive control. With three fitting stations no interpolator ranked a city's sites better than
the free raster; land-use regression saturated early, within the detection limit of the raster;
the learned arms stayed close to the raster at every density; and only the few networks with
several dozen stations ranked their sites well. One station informed roughly the kilometre around
it. That kilometre is the width of the first distance bin of the analysis, so it is an upper bound
on the resolution of the statement and not a measured length. On full records one further
prediction was refuted: in two cities, stations sharing a model cell predicted one another worse
than chance, so the within-cell ceiling the registration assumed does not bound skill where
neighbouring sites disagree. Under the registered crossing rule, kriging or regression kriging
overtook the raster at some tested density in eleven of eighteen cities, and in fifteen of
twenty-three on full records.

{{fig:spatialcurve}}

**What a re-analysis changed.** That crossing rule was a first-pass reading of per-city rank
correlations computed on ten to a few dozen held-out sites, and a post hoc re-analysis
[ledger F.124] asked how much of it is sampling noise. Four results narrow the registered
reading, and none of them reverses a verdict.

- *Cities do not clearly split.* The spread of kriging-minus-raster differences between cities
  is not significantly larger than the sampling noise of a rank correlation over a city's sites,
  at any tested density, and only two cities are individually distinguishable from zero. With a
  Holm correction over the densities tested, {{claim:v2.curve.full.holm_crossing}} of twenty-three
  cities cross the raster on full records and {{claim:v2.curve.reg.holm_crossing}} of eighteen in
  the registered frame.
- *Siting by design gains nothing, now with a meaningful interval.* The registered siting
  statistic was exactly zero with a zero-width interval, an artefact of pooling estimators that
  never use the fitting stations. For kriging alone, sites chosen to span the covariates minus
  sites chosen at random is {{claim:v2.curve.full.x5_e3_k3.median}}
  [{{claim:v2.curve.full.x5_e3_k3.lo}}, {{claim:v2.curve.full.x5_e3_k3.hi}}] at three stations on
  full records and {{claim:v2.curve.full.x5_e3_k5.median}}
  [{{claim:v2.curve.full.x5_e3_k5.lo}}, {{claim:v2.curve.full.x5_e3_k5.hi}}] at five. The
  verdict stands.
- *Tropical cities cannot be distinguished from the others.* Kriging's advantage over the raster
  at three stations is lower in the tropical cities by {{claim:v2.curve.full.trop_minus_other_k3.median}}
  on the Fisher-z scale [{{claim:v2.curve.full.trop_minus_other_k3.lo}},
  {{claim:v2.curve.full.trop_minus_other_k3.hi}}]. No difference is resolved, but the point
  estimate favours the raster in the tropics, so the registered description of the tropical
  cities as lying inside the temperate envelope overstated the agreement.
- *The detection limits are larger than registered.* Computed with the observed spread of
  per-city differences rather than the spread assumed at registration, the smallest resolvable
  difference in rank correlation is {{claim:v2.curve.full.mde_empirical}} on full records and
  {{claim:v2.curve.reg.mde_empirical}} in the registered frame. Only large effects are visible.

A fifth check added a benchmark the registration did not have. A satellite-derived one-kilometre
PM2.5 surface [@Wei2023] ranks held-out sites at {{claim:v2.curve.full.ghap.median}}
[{{claim:v2.curve.full.ghap.lo}}, {{claim:v2.curve.full.ghap.hi}}], close to the built-up raster:
paired, the satellite surface minus the raster is {{claim:v2.curve.full.ghap_minus_e1.median}}
[{{claim:v2.curve.full.ghap_minus_e1.lo}}, {{claim:v2.curve.full.ghap_minus_e1.hi}}], and kriging
from three stations minus the satellite surface is {{claim:v2.curve.full.e3k3_minus_ghap.median}}
[{{claim:v2.curve.full.e3k3_minus_ghap.lo}}, {{claim:v2.curve.full.e3k3_minus_ghap.hi}}]. The
satellite product may have been trained on some of these monitors, so its score is an upper bound
for a free surface. At the densities a city without monitors could afford, neither a free product
nor interpolation from its own stations ranks neighbourhoods usefully.

{{fig:spatialnoise}}

**What this means for Kandy.** The curve gives no station count for a Kandy map. At three to
eight stations no method tested ranked neighbourhoods usefully in the typical city, the cities
where interpolation clearly overtook a free layer were few, and the tropical cities, which are the
nearest analogues to Kandy the archives hold, could not be told apart from the temperate ones at
the resolution the data allow. **A handful of stations in Kandy should be expected to give the
city's level and its day-to-day variation, not a map of its neighbourhoods.** That is consistent
with every other result in {{this:ch-model-stops}}: the structure that matters lies inside a
kilometre cell, and a few points spread across the basin do not resolve it.
