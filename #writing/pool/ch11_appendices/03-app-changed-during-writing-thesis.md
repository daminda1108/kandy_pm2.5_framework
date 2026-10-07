# What changed during the writing of this thesis {#app-changed-during-writing-thesis}

Preparing this document required regenerating quantities that had been recorded earlier in the
project. Several of them moved. They are listed here rather than silently corrected, because the
pattern in them is the subject of {{ref:ch-eight-approaches-did-work}} and the machinery in {{ref:ch-reproducibility-machinery-catches-errors}} exists because of
them.

<!-- lint:off the recorded column lists values this project has RETIRED; they are the subject of the table -->

| quantity | recorded | regenerated | why it moved |
|---|---|---|---|
| countries in the panel | 32 | {{claim:frame.countries}} | never re-derived after the panel was corrected from 47 to {{claim:frame.cities}} cities |
| relief across the domain | 800 m | {{claim:kandy.relief_m}} m | a prose estimate; now taken from the elevation model |
| interval coverage after re-centring | 91.5 per cent | {{claim:kandy.cov90_recentred}} per cent | recomputed against the rebuilt field |
| donor benchmark correlation | 0.923 | {{claim:donor.benchmark_median}} | the recorded value was the single nearest pair, quoted as though it were a median |
| separation to the donor city | 93 km | {{claim:donor.colombo_km}} km | measured city centre to city centre, the convention every other pair uses |
| hours where the background exceeded the total | stated three ways | {{claim:field.precap_excess_mean}} per cent | one quantity had been reported as 38.5, as 38.2 of midday hours, and as 29.9 |
| parameters saturating their bounds | six of six | two of six | the project ledger carried the overstatement; the regenerated figure reports two |
| reference-dense cities, tropics against temperate | 5 and 32 | {{claim:census.deep_tropical}} and {{claim:census.temperate}} | pulled fresh from the global archive rather than recalled |
| population-weighted exposure uplift | 7 per cent | {{claim:exposure.uplift_pct}} per cent | the exposure file predated the field rebuild |
| attributable deaths per year | 427 | {{claim:burden.deaths}} | the same stale input |
| share of the background gain an independent network recovers | 79 per cent, then 73 | {{claim:donor.gain_reproduced_pct}} per cent | re-run on the corrected bottom rung, which leaves less headroom for any background to recover, and then computed per city and paired rather than as a ratio of medians |

<!-- lint:on -->

A second set of corrections came in October, from a verification pass over the information ladder
and from an external review of the whole analysis. They are listed separately because they changed
conclusions rather than values.

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
| diurnal swing of the sensor record | constant-humidity correction | peak to trough {{claim:v2.rh.constant_rh80.peak_to_trough}} becomes {{claim:v2.rh.barkjohn_hourly_rh.peak_to_trough}} with hourly humidity | the correction had used a fixed relative humidity; the shipped field is not yet rebuilt |
| age range of the attributable burden | not stated | stated as all ages, illustrative only | the response function is defined for adults of 25 and older and was applied to all ages; a corrected figure awaits age-specific mortality data |

<!-- lint:on -->

Two features of the first table are worth stating.

**None of these was found by reading.** Every one was found by recomputing a quantity and
comparing, which is why the machinery of {{ref:ch-reproducibility-machinery-catches-errors}} exists and why it runs on every build rather
than at the end.

Four of them made an argument weaker and were kept anyway. The donor benchmark, the bound
saturation, the countries count and the independent-background recovery all made the surrounding
claim less impressive once corrected. The last of those was regenerated specifically because an
external reader identified the background rung as the thesis's most vulnerable claim, so it is
the clearest case of the pattern: the check was run in the place where the result was most wanted
to hold, and it came back smaller. A number that strengthens an argument is the least likely
number to be checked, and that is the argument for checking all of them mechanically rather than
selectively.
