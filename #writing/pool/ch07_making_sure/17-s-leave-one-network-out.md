## Leave one network out {#s-leave-one-network-out}

The sensorless rung is fitted leave-one-city-out, so a city never contributes an observation to its
own prediction. Its neighbours in the same national network do contribute, on the same dates, and
they share its instruments, its calibration practice and much of its regional air. A sensorless
rung trained with them could be better than a genuinely monitorless city could achieve, and every
gain measured above it would then be too small.

The rung was therefore refitted leaving out the whole network, using the same clusters as the
bootstrap, so that no station of the target's own network enters its training [ledger F.124]. Under
the registered construction the first-station gain on the confirmation panel rises from
{{claim:v2.conf.reco.first2_rmse.median}} to {{claim:v2.review.lono.conf.first2_rmse.median}}
per cent, and the background verdicts barely move. Leave-one-city-out therefore flattered the
sensorless rung modestly, and the registered first-station gain is conservative by a few points.

The like-for-like conclusion does not depend on it. With the network left out, two stations read on
the day reduce daily error by {{claim:v2.review.registered_lono.reco.gL2s_rmse.median}} per cent
[{{claim:v2.review.registered_lono.reco.gL2s_rmse.lo}},
{{claim:v2.review.registered_lono.reco.gL2s_rmse.hi}}], and the background minus the first two is
{{claim:v2.review.registered_lono.reco.BGallmL2s_rmse.median}} points
[{{claim:v2.review.registered_lono.reco.BGallmL2s_rmse.lo}},
{{claim:v2.review.registered_lono.reco.BGallmL2s_rmse.hi}}] on daily error and
{{claim:v2.review.registered_lono.reco.BGallmL2s_exceed.median}} on exceedances. Kandy has no
national network whose stations could stand in for its own, so this is the more relevant version of
the sensorless rung for it, and it leaves the measurement priorities unchanged. Like {{ref:s-like-for-like}}, the check is exploratory.
