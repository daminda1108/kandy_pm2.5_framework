Table: What a station is worth when it is read on the day (post hoc)

| comparison | median % reduction in daily RMSE, or paired points |
|---|---|
| first two stations, read on the day | {{claim:v2.review.registered_loco.reco.gL2s_rmse.median}} [{{claim:v2.review.registered_loco.reco.gL2s_rmse.lo}}, {{claim:v2.review.registered_loco.reco.gL2s_rmse.hi}}] |
| background as registered, read on the day | {{claim:v2.review.registered_loco.reco.gBGall_rmse.median}} [{{claim:v2.review.registered_loco.reco.gBGall_rmse.lo}}, {{claim:v2.review.registered_loco.reco.gBGall_rmse.hi}}] |
| background minus first two, both read on the day | {{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.median}} [{{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.lo}}, {{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.hi}}] |
| one station read daily | {{claim:v2.review.k.day1.median}} [{{claim:v2.review.k.day1.lo}}, {{claim:v2.review.k.day1.hi}}] |
| two stations read daily | {{claim:v2.review.k.day2.median}} [{{claim:v2.review.k.day2.lo}}, {{claim:v2.review.k.day2.hi}}] |
| five stations read daily | {{claim:v2.review.k.day5.median}} [{{claim:v2.review.k.day5.lo}}, {{claim:v2.review.k.day5.hi}}] |
| two stations used only as a recalibration | {{claim:v2.review.k.cal2.median}} [{{claim:v2.review.k.cal2.lo}}, {{claim:v2.review.k.cal2.hi}}] |

Exploratory re-analysis of the registered data (ledger F.124): every stream regressed with the free estimate against stations not otherwise used, same-day, with shrinkage weights cross-fitted from other cities. The registered numbers are reproduced exactly in the same run. Station-count rows: full networks, 86 cities.
