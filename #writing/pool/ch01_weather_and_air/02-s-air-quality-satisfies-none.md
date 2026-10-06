## Limitations specific to particulate matter {#s-air-quality-satisfies-none}

*Observational coverage.* {{fig:obsdensity}} shows every location worldwide that publishes fine
particulate measurements openly. Measurement is concentrated in Europe, North America and eastern
Asia and becomes sparse towards the equator. The distribution is not random: coverage is lowest
in regions where concentrations are high and the population per instrument is large
[@Martin2019], so the regions with most to gain from additional measurement are the least likely
to have it.

{{fig:obsdensity}}

*Emissions.* Chemical transport models advect and remove particulate matter using the same
meteorology as weather prediction; the principal additional uncertainty lies in the emissions. An
urban air quality model requires the magnitude, location, timing and composition of emissions,
and little of this is observed directly, particularly for the diffuse sources that dominate urban
areas. Emissions are instead estimated from activity data, fuel statistics, traffic counts and
emission factors. Independent global inventories differ substantially for the same region and
sector [@Elguindi2020], and the uncertainty increases when an inventory is downscaled to a single
city. Secondary formation adds a further source of error: a large fraction of PM2.5 mass can be
formed in the atmosphere from gaseous precursors [@Huang2014], at rates that depend on
temperature, humidity, solar radiation and the concentrations of other species.

*Data assimilation.* Operational air quality systems assimilate observations, mainly satellite
aerosol optical depth and trace-gas columns, and this improves their analyses
[@Inness2019; @Bocquet2015]. Assimilation, however, corrects the model state, and where the
dominant error lies in the emissions rather than in the state, the correction decays as the model
is integrated forward. For this reason the joint estimation of emissions and state has developed
as a research field of its own [@Elbern2007; @Bocquet2015]. The methods that underpin weather
prediction therefore transfer only in part, because the error they correct is not the dominant
one.
