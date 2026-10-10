## The temporal anchor {#s-temporal-anchor}

The temporal anchor *T*(*t*) is the concentration averaged over the basin at each hour. It carries
the level of the field and all of its variation in time, and because the pattern has unit mean it
is also the field's city mean, to within the build tolerance of {{ref:s-decomposition-conserves}}. It is built in five steps.

**A prior from a composition model.** The hourly PM2.5 of the global composition forecast system
GEOS-CF [@Keller2021], averaged over the basin, is scaled to the local sensors by a single ratio
and a per-sensor offset. The scaled prior supplies the large-scale variation that a model trained
on two sensors could not learn alone, including regional episodes.

**A learned correction.** Gradient-boosted regression trees (LightGBM [@Ke2017]) learn the residual between
the two Kandy sensors and the scaled prior. The predictors are exogenous only: reanalysis
meteorology (boundary-layer height, ten-metre wind, temperature, dew point, precipitation, surface
solar radiation, and the temperature at 925 hPa with an indicator of the overnight inversion
[@Hersbach2020]), the reanalysis particulate concentration of the Copernicus service [@Inness2019], satellite
aerosol optical depth and tropospheric nitrogen dioxide with the time since each overpass
[@Lyapustin2018; @Veefkind2012], the tendencies of the composition prior, calendar and solar geometry, and the
identity, position and elevation of the sensor. No measured concentration from an earlier hour is
used. A model with such lags scores better on the hours a sensor observed, but it cannot predict
the hours no sensor observed, and those are most of the record. Three heads are fitted, for the
fifth, fiftieth and ninety-fifth percentiles, on every hourly sensor observation from 2018 onwards.

**An interval.** The two outer heads are widened by conformal calibration, computed separately
for each month and each six-hour block of the day from predictions made with one month of one
sensor withheld at a time [@Romano2019]. The nominal interval is ninety per cent.

**A level from a satellite surface.** Each year the whole series is shifted by a constant so that
its annual mean equals the annual mean of the van Donkelaar satellite-derived surface over the
basin [@vanDonkelaar2021]. The shift moves the level and leaves the shape and the interval width
unchanged. The target is the **area** mean of the surface, not the reading of a valley-floor
monitor. An earlier version forced the basin mean to a published valley-floor value, which
over-predicted the ventilated ridge by about a factor of two; {{ref:s-comparing-areal-model-point}}
explains why a point on the valley floor is not an estimate of the area mean. Years after the last
published surface use the last surface as their level, and are labelled as an extension.

**Amplitude correction.** A model of this kind regresses towards the mean, and the learned
series reproduces the shape of the observed daily and seasonal cycles while damping their
amplitude. Multiplicative factors for each hour of the day and each month map the model's
climatology onto the climatology of the sensor record, and the annual mean is then restored.

Three properties of this construction matter for everything that follows. The anchor is
**calibrated to the two Kandy sensors** three times over (the residual, the interval and the
amplitude), so agreement with those sensors cannot be used as validation, and
{{ref:s-checks-kandy-carry-weight}} does not use it. Its **level** comes from the satellite
surface rather than from the sensors. And its **skill is modest at the hourly scale**: the figures
are given in {{ref:s-excluded-processes-known-limits}}, and most of the anchor's skill lies in the
daily and seasonal variation that {{ref:ch-validation-without-local-ground}} tests elsewhere.
