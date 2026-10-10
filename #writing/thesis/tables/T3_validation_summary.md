Table: Validation results by evaluation condition

| condition | evidence | result | caveat |
|---|---|---|---|
| Seasonal aggregation | ten analogue cities, withheld stations | seasonal correlation {{claim:scorecard.seasonal_r_lo}} to {{claim:scorecard.seasonal_r_hi}}; level bias median {{claim:scorecard.level_bias_median}} per cent | climatological; level there set by two stations, not the satellite |
| Shape of the daily cycle | ten analogue cities | diurnal correlation {{claim:scorecard.diurnal_r_lo}} to {{claim:scorecard.diurnal_r_hi}} | regime-dependent; depth also calibration-dependent at Kandy |
| Daily, anchor stations reporting | ladder, {{claim:v2.km.cities_scored}} cities | error {{claim:v2.km.reco.unio.gK2_rmse.median}} per cent below the sensorless estimate; correlation {{claim:v2.km.reco.unio.K2_r.median}}; bias {{claim:v2.km.reco.unio.K2_bias.median}} per cent | includes training on the anchor stations' own record |
| Daily, anchor stations not reporting | ladder, prospective | error {{claim:v2.km.pros.unio.gK2_rmse.median}} per cent below [{{claim:v2.km.pros.unio.gK2_rmse.lo}}, {{claim:v2.km.pros.unio.gK2_rmse.hi}}]; correlation {{claim:v2.km.pros.unio.K2_r.median}}; bias {{claim:v2.km.pros.unio.K2_bias.median}} per cent | no resolvable gain over the sensorless estimate |
| Hourly, at Kandy | one month of one sensor withheld at a time | coefficient of determination {{claim:v2.tanchor.lagfree.r2}}; RMSE {{claim:v2.tanchor.lagfree.rmse}} | the same sensors calibrate the anchor's amplitude |
| Interval coverage | Kandy sensors; ladder cities | {{claim:kandy.cov90}} per cent; a fraction {{claim:v2.km.reco.unio.K2_cov90.median}} | nominal 90; misses one-sided at Kandy |
| Independent Kandy records | national organisation, two years; three low-cost records | {{claim:nbro.diff_pct_2021}} and {{claim:nbro.diff_pct_2022}} per cent; low-cost records below the field | point against cell; instruments differ |

A high seasonal correlation does not imply accurate daily or hourly values; each condition is reported separately for that reason.
