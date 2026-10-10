## The measurement-priority ordering {#s-measurement-priority-ordering}

The practical question behind this thesis is what a city with almost no monitoring should obtain
first. The answer depends less on which instrument is bought than on how its readings are used,
and it depends on the purpose the estimate serves: a daily city level, a check on that level, or
a map of where in the city pollution is highest. The ordering below is stated for those purposes
in turn. It rests on the panel measurements of {{ref:s-marginal-predictive-value-each}}, read with
the post hoc re-analysis that put every observation on the same footing [ledger F.124], and on the
spatial results of {{ref:ch-model-stops}}.

This section ranks measurements by marginal predictive value, and that is not the same thing as a
procurement optimum. No cost enters the ladder, and neither does maintenance, calibration burden,
instrument reliability, compliance value, coverage, nor the consequence of a decision made on the
output. What follows therefore **informs** procurement rather than optimising it: it says which
measurement this model can use most, not which purchase a programme should make once its own
costs and obligations are counted. Two further limits of scope travel with every statement here.
The confirmation cities were mostly temperate and mostly served by regulatory reference networks,
so low-cost tropical networks lie outside the population the ladder was confirmed on, and Kandy
lies outside it too. And the value of a reference-grade instrument as such was never a rung,
which is why it is argued separately below.

**Take the free data first.** Terrain, roads, land cover, vegetation, night lights, population,
reanalysis meteorology and satellite retrievals cost nothing and are available for every city.
Every gain reported below is measured on top of them, so a programme that skips this step will
see larger gains from its first instruments without being better off. The free streams are also
not exhausted by the set the ladder used: a richer registered baseline, adding atmospheric
composition reanalysis, fires, satellite nitrogen dioxide, rainfall and terrain, improved the
sensorless estimate by a further {{claim:v2.rich.bud0_gain.median}} per cent
[{{claim:v2.rich.bud0_gain.lo}}, {{claim:v2.rich.bud0_gain.hi}}], and every registered verdict
survived the change.

**Then obtain continuous stations whose readings reach the estimate every day.** This is the
recommendation of this thesis, and it is the one most robust to how the evidence is read. When a
station's reading is used on the day it is taken, two stations reduce daily error in the
reconstructed city mean by {{claim:v2.review.registered_loco.reco.gL2s_rmse.median}} per cent
[{{claim:v2.review.registered_loco.reco.gL2s_rmse.lo}}, {{claim:v2.review.registered_loco.reco.gL2s_rmse.hi}}].
Used only to recalibrate the sensorless estimate, as the registered first rung used them, the
same two stations gave {{claim:v2.conf.reco.first2_rmse.median}} per cent
[{{claim:v2.conf.reco.first2_rmse.lo}}, {{claim:v2.conf.reco.first2_rmse.hi}}] on the fresh
confirmation cities, and nothing detectable on high-pollution days. On cities with full station
networks the same contrast holds at every station count:

{{fig:stationdaily}}

One station read daily reduced error by {{claim:v2.review.k.day1.median}} per cent
[{{claim:v2.review.k.day1.lo}}, {{claim:v2.review.k.day1.hi}}], two by
{{claim:v2.review.k.day2.median}} per cent [{{claim:v2.review.k.day2.lo}}, {{claim:v2.review.k.day2.hi}}]
and five by {{claim:v2.review.k.day5.median}} per cent [{{claim:v2.review.k.day5.lo}}, {{claim:v2.review.k.day5.hi}}],
while the same stations used as a calibration only gave about {{claim:v2.review.k.cal2.median}}
per cent whatever their number. Most of the value arrives with the first two or three stations,
and almost all of it lies in the daily reading rather than in the calibration. A short campaign
that co-locates instruments for a few weeks and then leaves recovers a small fraction of what a
station reporting continuously is worth.

No ordering of station types is established for this purpose. In a post hoc re-analysis that used every
stream on the same footing, two local stations,
a background summarising the rest of the network and any two other stations were indistinguishable:
the background minus the first two is {{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.median}}
points [{{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.lo}}, {{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.hi}}]
for ordinary days and {{claim:v2.review.registered_loco.reco.BGallmL2s_exceed.median}} points
[{{claim:v2.review.registered_loco.reco.BGallmL2s_exceed.lo}}, {{claim:v2.review.registered_loco.reco.BGallmL2s_exceed.hi}}]
for exceedances of the guideline, and the prospective arm, in which every stream keeps reporting
and coefficients come only from the earlier half of the record, gives
{{claim:v2.review.registered_loco.pros.BGallmL2s_rmse.median}} points
[{{claim:v2.review.registered_loco.pros.BGallmL2s_rmse.lo}}, {{claim:v2.review.registered_loco.pros.BGallmL2s_rmse.hi}}].
The registered ladder reported a background series ahead of the first local stations by
{{claim:v2.conf.reco.bgm2_rmse.median}} points, but that comparison set a reading used on the day
against a reading used only for calibration, so it is quoted as constructed and **does not rank
a background above local stations**. For Kandy the consequence is direct. The stations of the
Central Environmental Authority in the city, the regional stations of the National Building
Research Organisation and the university's own sensor network should all be brought into the
estimate as continuous daily inputs, whichever of them can be obtained, and they are
complementary rather than ranked.

**Make at least one of them reference grade, for a reason the ladder does not price.** The case
for a reference instrument is a measurement-design argument and stands on its own. It would
settle the level discrepancy of {{ref:s-checks-kandy-carry-weight}}, where three of four
independent records sit below the model and the one that matches carries an undocumented
instrument. It would anchor the calibration of the low-cost sensors already in the basin, against
which their performance can be assessed on a published protocol [@Duvall2021]. And it would settle
the shape of the diurnal cycle, which at present depends on a humidity correction: with a constant
relative humidity the corrected low-cost record has a peak-to-trough ratio of
{{claim:v2.rh.constant_rh80.peak_to_trough}}, and with hourly humidity
{{claim:v2.rh.barkjohn_hourly_rh.peak_to_trough}}. Only a co-located reference record can say
which is right. None of the station-count figures above is evidence for this case, and it does
not need them.

**Do not expand the network to improve the daily mean.** Beyond two or three stations read daily,
further stations add little to a daily city-level estimate. On full networks a background
summarising about ten outer stations added
{{claim:v2.review.full_loco.reco.BGallmL2s_rmse.median}} points
[{{claim:v2.review.full_loco.reco.BGallmL2s_rmse.lo}}, {{claim:v2.review.full_loco.reco.BGallmL2s_rmse.hi}}]
over two stations read on the day, an effect of count rather than of kind, and stations three to
six used as a recalibration added {{claim:v2.conf.reco.s36_rmse.median}} points
[{{claim:v2.conf.reco.s36_rmse.lo}}, {{claim:v2.conf.reco.s36_rmse.hi}}]. That last value is close
to guaranteed by design, because a recalibration with an intercept and a slope is already fixed by
two stations, so it says that further stations used that way add nothing, not that they carry no
information. A pair still buys something the ladder does not score: a second sensor makes a
between-sensor comparison possible, which is how the calibration checks of
{{ref:s-checks-kandy-carry-weight}} were obtained at all.

**Buy a network for a map only if the map is the purpose, and expect little from a small one.**
A city that needs more stations needs them for a spatial purpose, such as locating hotspots,
siting interventions or exposure mapping, and should judge them against that purpose. For that
purpose the evidence is weak. {{ref:s-what-stations-buy-map}} finds that at three to eight
stations neither interpolation nor a free product ranked neighbourhoods usefully, that
interpolation clearly overtook a free land-cover layer in only
{{claim:v2.curve.full.holm_crossing}} of twenty-three cities after correction for multiple
testing, and that siting by design gained nothing. A Kandy network of a handful of stations should
be expected to give the city's level and its days, not its neighbourhoods.

The tropics cannot be given advice of their own. The confirmation held only four low-latitude
cities with dense networks, its test of a latitude dependence was undetectable, and the public
record holds too few dense tropical networks to settle the question. Nothing in this study
suggests that the value of a same-day reading differs by climate band, and no ordering specific
to Kandy's band is claimed.

{{tbl:T9_1_next_v2}}
