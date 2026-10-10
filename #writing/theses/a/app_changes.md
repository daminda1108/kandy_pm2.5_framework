# What changed during the writing of this thesis {#app-changed-during-writing-thesis}

Preparing this document required regenerating quantities recorded earlier in the project, and
some of them moved. Eleven values changed when they were recomputed from their source files, among
them the number of countries in the panel and the population-weighted exposure uplift; each
now carries its regenerated value in the text. The corrections below
changed conclusions rather than values. They came from a verification pass over the information
ladder and from an external review of the whole analysis in October 2026, and they are listed so
that a reader of earlier drafts or presentations can see what replaced what.

<!-- lint:off the recorded column lists values this project has RETIRED; they are the subject of the table -->

| quantity | recorded | now | why it moved |
|---|---|---|---|
| gain from the first two local stations | 17.8 per cent | {{claim:v2.conf.reco.first2_rmse.median}} per cent on the registered confirmation, as constructed | the earlier value came from one station split and one learner seed on the discovery panel |
| first two local stations against a background, used the same way | background ranked above local stations | difference {{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.median}} points | the registered rungs used the stations as a recalibration and the background on the day; used the same way they are worth about the same |
| two stations read on the day against two used as calibration | not measured | {{claim:v2.review.k.day2.median}} against {{claim:v2.review.k.cal2.median}} per cent | the review's station-count curve |
| deep-tropical reversal of the ladder | 33.3 points, interval excluding zero, 4.2 times | not distinguishable from zero; exploratory | one split and one seed; averaged over splits the interval excludes zero in three of twenty |
| clusters in the discovery panel | 29 | twenty-eight | a city counted in two clusters; the cluster widening of the intervals was recomputed |
| reference against low-cost cities in the discovery panel | 20 and 27 | thirty-one and sixteen | the Chinese national network had been classed as low-cost |
| precipitation registration | 3 held and 2 refuted | 1 held, 3 refuted, 1 not adjudicable | the verdicts were recomputed as paired comparisons |
| local fraction | fixed by physics | {{claim:v2.f.cap_min}} to {{claim:v2.f.cap_max}}, a bound under the constraint | the constraint ran on UTC days and on the single lowest hour, both choices the fraction depends on |
| siting interval of the spatial learning curve | 0.00 to 0.00 | {{claim:v2.curve.reg.x5_e3_k3.lo}} to {{claim:v2.curve.reg.x5_e3_k3.hi}} at three stations | the summary pooled estimators that cannot differ at a site; the verdict is unchanged |
| cities where kriging beats the built-up layer | 15 of 23 | {{claim:v2.curve.full.holm_crossing}} of 23 | a correction for multiple comparisons, which the first reading omitted |
| detection limit of the spatial learning curve | 0.24 | {{claim:v2.curve.full.mde_empirical}} | the registered value assumed a spread smaller than the one observed |
| diurnal swing of the sensor record | constant-humidity correction | morning peak to midday {{claim:v2.rh.constant_rh80.peak_to_trough}} becomes {{claim:v2.rh.barkjohn_hourly_rh.peak_to_trough}} with hourly humidity | the correction had used a fixed relative humidity; the shipped field is not yet rebuilt |
| attributable burden | a number of deaths per year with an interval | withdrawn; the method is given without a number | the response function is defined for adults of 25 and older and was applied to all ages, the interval omitted most of the uncertainty and the level is unresolved; an estimate awaits age-specific mortality data |

<!-- lint:on -->
