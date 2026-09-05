Table: Data streams, their provenance, and the limit that matters

| stream | product | resolution | the limit that matters here |
|---|---|---|---|
| Satellite aerosol | MODIS multi-angle retrieval [@Lyapustin2018] | 1 km, daily | cloud gaps; carries no diurnal information at all |
| Satellite concentration | annual reanalysis-fusion surface [@vanDonkelaar2021] | 1 km, annual | an annual level cannot constrain day-to-day variance |
| Reanalysis drivers | wind, boundary layer, temperature, humidity [@Hersbach2020] | 9 to 31 km, hourly | a valley boundary layer is not resolved at this scale |
| Chemical prior | global composition reanalysis [@Keller2021] | 25 km, hourly | itself a model; corroborates but cannot validate |
| Precipitation | satellite precipitation radar | 10 km, half-hourly | reanalysis land precipitation was rejected: twice the gauge at this site |
| Terrain | digital elevation model [@Farr2007] | 30 m | static; carries no information about emission |
| Roads | open street mapping | vector | completeness varies by country and is not measurable from the data |
| Land cover and vegetation | satellite land cover and greenness | 10 to 500 m | the strongest single spatial predictor, and still only a proxy |
| Night lights | satellite radiance [@Elvidge2017] | 500 m | conflates commercial activity with residential density |
| Population | modelled settlement layer [@Tatem2017] | 100 m | a model, not a census, at this resolution |
| Local sensors | two low-cost units at Kandy | hourly, 2018 to 2026 | both on the valley floor; carry their own calibration problem |
| Borrowed panel | two open monitoring networks | {{claim:frame.cities}} cities | no Sri Lankan city qualifies for it |

Nothing in this table was collected for this project. Every stream is either openly published or was obtained on request, which is a deliberate constraint: a method that requires bespoke measurement cannot be applied to the cities that most need it.
