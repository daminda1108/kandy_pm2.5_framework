## Every station used the same way: a post hoc re-analysis {#s-like-for-like}

**Why it was needed.** An external review of the code after the registered tests had been scored
found that the registered rungs do not compare like with like [ledger F.124]. The first two
stations, and stations three to six, enter only as a recalibration of the sensorless estimate, so a
station's reading never reaches the prediction for the day it was taken. The background rung reads
its stations on the day being predicted, and it summarises every remaining station in the pool
rather than two. A comparison between those rungs therefore mixes three things: the kind of station,
the way its reading is used, and the number of stations it summarises. The registration fixed how
each comparison would be run and the run followed it exactly, and every gate passed, because none of
them asks whether the arms of a comparison differ only in the factor under test. A small probe on
ten discovery cities suggested that the use, not the kind, was doing the work, and the re-analysis
below was run to measure it.

**Design.** The registered data were re-scored with four arms that differ only in which stations
supply a same-day predictor. With the registered shuffle, the first two pool stations form the
*local* set, stations three to six form the fitting target, and the remaining stations form the
*outer* set. Each arm regresses the daily mean of stations three to six on the sensorless estimate
and its same-day predictor, predicts the held-out mean with the fitted coefficients, and is shrunk
toward the sensorless estimate with a weight taken from the other cities. The four predictors are the
first two stations' daily mean; the daily tenth percentile of the whole outer set, which is the
registered background; the same percentile of only two outer stations, which matches the count of
the local arm; and the mean of those two outer stations, which matches its kind of summary. Every arm
needs at least eight pool stations, which one hundred cities of the discovery and confirmation panels
together provide. Both uses are scored, the reconstruction and a prospective arm in which every
stream keeps reporting after a calibration on the earlier half of the record. The registered chain is
recomputed in the same run and reproduces the registered per-city effects to the precision of
floating-point arithmetic.

{{tbl:T7_2_like_for_like_v2}}

{{fig:likeforlike}}

**Result.** Read on the day, two stations reduce daily error by close to three fifths, whichever
stations they are. The first two stations give {{claim:v2.review.registered_loco.reco.gL2s_rmse.median}}
per cent [{{claim:v2.review.registered_loco.reco.gL2s_rmse.lo}},
{{claim:v2.review.registered_loco.reco.gL2s_rmse.hi}}]. The registered background gives
{{claim:v2.review.registered_loco.reco.gBGall_rmse.median}} per cent, the background from two outer
stations {{claim:v2.review.registered_loco.reco.gBG2_rmse.median}} per cent, and the mean of two
outer stations {{claim:v2.review.registered_loco.reco.gM2_rmse.median}} per cent. Paired within city,
the background minus the first two is {{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.median}}
points [{{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.lo}},
{{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.hi}}] on daily error and
{{claim:v2.review.registered_loco.reco.BGallmL2s_exceed.median}} points on the exceedance loss.
Prospectively it is {{claim:v2.review.registered_loco.pros.BGallmL2s_rmse.median}} points
[{{claim:v2.review.registered_loco.pros.BGallmL2s_rmse.lo}},
{{claim:v2.review.registered_loco.pros.BGallmL2s_rmse.hi}}]. The count-matched and kind-matched
comparisons are no larger: {{claim:v2.review.registered_loco.reco.BG2mL2s_rmse.median}} and
{{claim:v2.review.registered_loco.reco.M2mL2s_rmse.median}} points. On the same cities the registered
construction reproduces the registered ordering, so the ordering is produced by the difference of
use and by nothing that the stations measure.

**Count, separated from kind.** On the full-network frame of {{ref:s-robustness-full-networks}}, where
the outer set holds about ten stations, the same comparison separates the number of stations from
their kind. Two outer stations, as a percentile or as a mean, match the first two stations
({{claim:v2.review.full_loco.reco.BG2mL2s_rmse.median}} points
[{{claim:v2.review.full_loco.reco.BG2mL2s_rmse.lo}}, {{claim:v2.review.full_loco.reco.BG2mL2s_rmse.hi}}]
and {{claim:v2.review.full_loco.reco.M2mL2s_rmse.median}}
[{{claim:v2.review.full_loco.reco.M2mL2s_rmse.lo}}, {{claim:v2.review.full_loco.reco.M2mL2s_rmse.hi}}]).
A background that summarises all outer stations leads them by
{{claim:v2.review.full_loco.reco.BGallmL2s_rmse.median}} points
[{{claim:v2.review.full_loco.reco.BGallmL2s_rmse.lo}}, {{claim:v2.review.full_loco.reco.BGallmL2s_rmse.hi}}],
{{claim:v2.review.full_loco.reco.BGallmL2s_exceed.median}} points on exceedances and
{{claim:v2.review.full_loco.pros.BGallmL2s_rmse.median}} prospectively. More stations read on the day
add a little, and the kind of station adds nothing resolvable. Nearly all of the registered ordering
comes from the use of the reading.

**What it means.** The registered rungs measured two different uses of observations, and the
difference between those uses is the finding. A station whose reading reaches the estimate each day
reduces daily error by more than half; the same station used only to correct the level and scale of
a free estimate reduces it by about a tenth ({{ref:s-redundancy-begins}}). For a city deciding what to
measure, the operative question is therefore whether a station's readings will be available to the
estimate day by day, and the kind of station, local or background, matters far less than that. This
is the evidence behind the measurement priorities for Kandy in the main text.

**Status.** The re-analysis was designed after the registered results were known, so it is
exploratory. A registered test of the symmetric design would need a fresh set of dense networks that
none of the analyses has seen, and the public archives no longer hold enough of them; it has not been
run. The registered verdicts stand as registered and are quoted as constructed.
