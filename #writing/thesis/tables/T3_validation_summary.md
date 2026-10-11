Table: Validation results by evaluation condition

| condition | evidence | result | caveat |
|---|---|---|---|
| Seasonal aggregation | ten analogue cities, withheld stations | seasonal correlation {{claim:scorecard.seasonal_r_lo}} to {{claim:scorecard.seasonal_r_hi}}; level bias median {{claim:scorecard.level_bias_median}} per cent | climatological; level there set by two stations, not the satellite |
| Shape of the daily cycle | ten analogue cities | diurnal correlation {{claim:scorecard.diurnal_r_lo}} to {{claim:scorecard.diurnal_r_hi}} | regime-dependent; depth also calibration-dependent at Kandy |
| Daily, anchor stations reporting | ladder, {{claim:v2.km.cities_scored}} cities | error {{claim:v2.km.reco.unio.gK2_rmse.median}} per cent below the sensorless estimate; correlation {{claim:v2.km.reco.unio.K2_r.median}}; bias {{claim:v2.km.reco.unio.K2_bias.median}} per cent | includes training on the anchor stations' own record |
| Daily, anchor stations not reporting | ladder, prospective | error {{claim:v2.km.pros.unio.gK2_rmse.median}} per cent below [{{claim:v2.km.pros.unio.gK2_rmse.lo}}, {{claim:v2.km.pros.unio.gK2_rmse.hi}}]; correlation {{claim:v2.km.pros.unio.K2_r.median}}; bias {{claim:v2.km.pros.unio.K2_bias.median}} per cent | no resolvable gain over the sensorless estimate |
| Hourly, at Kandy | one month of one sensor withheld at a time | coefficient of determination {{claim:v2.tanchor.lagfree.r2}}; RMSE {{claim:v2.tanchor.lagfree.rmse}} | the same sensors calibrate the anchor's amplitude |
| Interval coverage | Kandy sensors; ladder cities | {{claim:kandy.cov90}} per cent; a fraction {{claim:v2.km.reco.unio.K2_cov90.median}} | nominal 90; misses one-sided at Kandy |
| Daily, at Kandy | national organisation's daily record, 2021 and 2022 | daily correlation {{claim:nbrod.all.model_cell.r}}; across calendar months {{claim:nbrod.climatology_r}}; within months {{claim:nbrod.anomaly_daily_r}} | digitised from a published figure; misses 2022 |
| Held-out sensor at Kandy | train on one sensor, score the other | daily correlation {{claim:loso.akurana.daily.pred.r}} and {{claim:loso.hantana.daily.pred.r}}; prior alone {{claim:loso.akurana.daily.prior_only.r}} and {{claim:loso.hantana.daily.prior_only.r}} | two low-cost sensors sharing a calibration |
| Independent Kandy records | national organisation, two years; three low-cost records | national record {{claim:nbro.diff_pct_2021}} and {{claim:nbro.diff_pct_2022}} per cent; low-cost records below the field | point against cell; instruments differ |

A high seasonal correlation does not imply accurate daily or hourly values; each condition is reported separately for that reason.
