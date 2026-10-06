Table: Registered confirmation on 72 fresh cities, as constructed

| endpoint | what the rung does | median (two-level cluster 95 % interval) |
|---|---|---|
| H1 first two stations | recalibrate the free estimate (intercept and slope) | {{claim:v2.conf.reco.first2_rmse.median}} [{{claim:v2.conf.reco.first2_rmse.lo}}, {{claim:v2.conf.reco.first2_rmse.hi}}] per cent |
| H2 stations three to six | the same recalibration from six stations | {{claim:v2.conf.reco.s36_rmse.median}} [{{claim:v2.conf.reco.s36_rmse.lo}}, {{claim:v2.conf.reco.s36_rmse.hi}}] points |
| H3 background series | the daily 10th percentile of the other stations, read on the day | {{claim:v2.conf.reco.bg_rmse.median}} [{{claim:v2.conf.reco.bg_rmse.lo}}, {{claim:v2.conf.reco.bg_rmse.hi}}] per cent |
| H4 background minus first two | a comparison of the two rungs as built | {{claim:v2.conf.reco.bgm2_rmse.median}} [{{claim:v2.conf.reco.bgm2_rmse.lo}}, {{claim:v2.conf.reco.bgm2_rmse.hi}}] points |
| H5 the same, exceedance days | as H4, balanced error at 15 µg m⁻³ | {{claim:v2.conf.reco.bgm2_exceed.median}} [{{claim:v2.conf.reco.bgm2_exceed.lo}}, {{claim:v2.conf.reco.bgm2_exceed.hi}}] points |

Verdicts stand as registered (OSF ueyfr). The rungs use their stations differently: the local stations never enter a day's prediction, the background does. H4 and H5 therefore compare uses, not observations (Table 7.2).
