## Conclusions {#a-conclusions-list}

The conclusions are given against the objectives set out in {{ref:a-aims}}. What this study
delivers is a constrained reconstruction of PM2.5 over Kandy and an account of how far each part of
it can be trusted. It does not deliver a validated hourly, kilometre-scale map, and the conclusions
are worded so that they cannot be read as one. {{tbl:T4_ledger}} states, for each part of the
reconstruction, what the evidence supports and what it may be used for.

{{tbl:T4_ledger}}

1. **A decomposition that conserves the city-wide mean can be built for Kandy from data available
   everywhere.** The field separates a regional background from a local increment whose spatial
   average is fixed by construction, so an error in the pattern moves material without creating
   it; in the delivered field the city mean departs from the anchor by at most
   {{claim:gauge.drift_hi_pct}} per cent. Each component declares which observations it may use,
   and removing an observation stream reproduces the simpler tier exactly, which is what allows
   the value of each stream to be measured.
2. **The reconstructed annual basin means exceed the World Health Organization annual guideline in
   every satellite-anchored year**, at {{claim:kandy.mean_min}} to {{claim:kandy.mean_max}}
   micrograms per cubic metre, with a north-east monsoon maximum, a south-west monsoon minimum, and
   morning and evening peaks either side of a midday dip. Because the absolute level is
   set by one regulatory station (conclusion 3), these values characterise the modelled field. The exceedance itself is
   robust: across the interval of the level factor the annual basin means lie between
   {{claim:ceabeta.level_lo}} and {{claim:ceabeta.level_hi}} micrograms per cubic metre, at least
   {{claim:ceabeta.who_lo}} times the guideline. Under the baseline
   decomposition the local increment accounts for {{claim:partition.f}} of the modelled
   concentration; the fraction ranges from {{claim:v2.f.cap_min}} to {{claim:v2.f.cap_max}} under
   the tested choices of day boundary and daily-floor statistic, reaches
   {{claim:field.f_form_roll48}} with a 48-hour background window, and is
   {{claim:rh2.hourly_rh.f}} under the hourly-humidity label. These describe the decomposition's
   sensitivity to its specification, not a confidence interval and not a source apportionment: they
   do not say that half of Kandy's PM2.5 is emitted in Kandy. At the regulatory station, the
   urban excess over the cleanest regional town gives a lower-bound estimate of {{claim:lfs.e1min.f}}
   and a combustion-tracer intercept a separate estimate of {{claim:lfs.e2.co_p5.f}}, which has
   biases in both directions and is not an upper bound. The model's {{claim:lfs.model.e2_cell}} at
   that cell is broadly consistent with the tracer estimate; the urban-increment comparison
   indicates that it may be high. Weighting by population raises exposure
   {{claim:exposure.uplift_pct}} per cent above the area mean, a figure that inherits the uncertainty
   of the level and of the unvalidated spatial pattern. No attributable burden is reported: it needs
   age-specific mortality, a settled level and a propagated uncertainty that this study does not yet
   have ({{ref:app-attributable-burden-projection}}).
3. **The evidence for the field is graded, and its parts stand at different strengths.**
   - *The seasonal cycle is the best-supported property, and it comes from the anchor stations.* The
     construction reproduces it in every analogue city when their own observations are withheld
     (seasonal correlation {{claim:scorecard.seasonal_r_lo}} to {{claim:scorecard.seasonal_r_hi}}),
     better than the composition prior alone (median {{claim:sb.prior.median}}) but no better than the
     two anchor stations' own climatology (median {{claim:sb.anchors.median}}): it preserves what the
     stations hold rather than adding to it.
   - *At Kandy, the daily record of the national research organisation (2021 and 2022) supports the
     seasonal shape (correlation {{claim:nbrod.climatology_r}} across calendar months) but not the
     day-to-day sequence (within-month correlation {{claim:nbrod.anomaly_daily_r}}), and the field
     misses the crisis year 2022.* A sensor withheld from training is tracked at a daily correlation of
     {{claim:loso.akurana.daily.pred.r}} and {{claim:loso.hantana.daily.pred.r}}.
   - *The day-to-day sequence is supported where the sensors reported.* Placed on the ladder in
     {{claim:v2.km.cities_scored}} cities, the deployed temporal model reduces daily error by
     {{claim:v2.km.reco.unio.gK2_rmse.median}} per cent against a generic sensorless estimate where
     its two anchor stations observed the period, and by no resolvable amount where they did not.
     At Kandy that means the daily sequence is credible on days the sensors reported and much less
     so on the many days they did not.
   - *The daily cycle's timing and morning peak are supported; its nights are too high.* The daily cycle transfers to some
     analogue cities and not to others (diurnal correlation {{claim:scorecard.diurnal_r_lo}} to
     {{claim:scorecard.diurnal_r_hi}}), as well as the anchor stations' own cycle does (median
     {{claim:sbd.anchors.median}} against {{claim:sbd.model.median}}) and far better than the prior alone, and hourly skill at Kandy is modest (a coefficient of
     determination of {{claim:v2.tanchor.lagfree.r2}} out of sample). Under the alternative humidity
     correction the timing of the peaks and of the midday dip is unchanged, but the morning-peak-to-midday ratio falls
     from {{claim:rh2.production.peak_trough}} to {{claim:rh2.hourly_rh.peak_trough}} and the night
     falls below midday. The regulatory station's hourly record settles part of this: it has the same
     timing and a morning peak {{claim:cea.hourly.station.peak07_over_midday}} times midday, as in the
     delivered field, but its deep night is the daily minimum
     ({{claim:cea.hourly.station.night_over_midday}} of midday), lower than either correction gives.
   - *The absolute level is anchored to the regulatory station, with a held-out check that points
     the right way but is short.* Taken from the satellite surface, the level read
     {{claim:cea.sat.all.bias_pct}} per cent above the regulatory station over {{claim:cea.days}} days.
     The excess enters at the satellite level: the corrected low-cost record the anchor is trained on
     sits {{claim:ceaatt.pct.akurana}} per cent from the station on shared days, the satellite-anchored
     basin series {{claim:ceaatt.pct.T_basin}} per cent. Re-anchored with a factor of
     {{claim:ceabeta.beta}} ({{claim:ceabeta.lo}} to {{claim:ceabeta.hi}}) fitted on 2019 to mid-2021,
     the field differs from the station by {{claim:ceasplit.bias_re}} per cent on the
     {{claim:ceasplit.days}} held-out days of 2022 and 2023 ({{claim:ceasplit.bias_re.lo}} to
     {{claim:ceasplit.bias_re.hi}}), against {{claim:ceasplit.bias_sat}} per cent at the satellite level;
     the pooled figure combines {{claim:cea.del.2022.bias_pct}} per cent in 2022 with
     {{claim:cea.del.2023.bias_pct}} per cent in 2023, and the reduction in daily error is not
     established. It is a provisional correction anchored to one station and conditional on the
     modelled relation between that station's cell and the basin mean.
     The field follows the station's day-to-day sequence (daily correlation {{claim:cea.del.all.r}},
     {{claim:cea.del.anomaly_daily_r}} within the month). Beyond 2023 the re-anchored extension reads
     {{claim:ceasplit.ext_bias}} per cent against the station, so the correction is not supported
     there. Across the ladder's cities the satellite level likewise sits above the withheld city mean,
     by {{claim:v2.km.reco.unio.K2_bias.median}} per cent in reconstruction and
     {{claim:v2.km.pros.unio.K2_bias.median}} per cent prospectively. The interval's nominal ninety per
     cent coverage is not achieved, at Kandy or in those cities; at the regulatory station the hourly
     interval contains {{claim:ceaiv.held.coverage}} per cent of held-out hours, missing on both sides,
     so it is too narrow rather than misplaced.
4. **The field is not supported below the kilometre scale, and its spatial pattern is a hypothesis,
   not a measurement.** More of the variation within a city lies inside a single cell than between
   cells, no model built from freely available covariates recovers it, the dispersion step meant to
   place the local increment lowered its agreement with withheld stations and has been removed, and a
   handful of
   interpolated stations does not recover it either; the limit is one of support and of the
   information available, not of the model chosen. The map may illustrate the construction and
   guide where to measure. It must not be used to rank neighbourhoods or to place interventions as
   though its differences between cells had been validated.
5. **The measurement worth most to Kandy is a set of continuously reporting stations whose
   readings enter the estimate each day.** For the city-mean estimation procedure tested, on a mostly
   temperate panel, a station read daily is worth several times what the same station is worth as a
   one-off calibration, and a handful of stations fixes the level and
   the daily sequence of a city mean but not a neighbourhood map. A reference-grade instrument among
   them would also settle the level and the depth of the daily cycle. This conclusion replaces an
   earlier ordering of a background series above local stations, which a review traced to a
   registered comparison of rungs that used their stations differently. The comparison that
   replaced it, with every station used the same way, finds the kind of station makes no resolvable
   difference, but it is a post hoc re-analysis of the registered data, not a registered
   confirmation, and a fresh pre-specified test is required before the near-equivalence of station
   types is treated as established ({{ref:a-future}}).
6. **The next step is to test the reconstruction, not to enlarge it.** The work that follows treats the
   delivered field as a locked hypothesis and collects observations able to refute it: the regulatory
   record's provenance first, then low-cost sensors evaluated against the reference across two
   monsoons, then a distributed network whose level, within-cell, drainage and daily-cycle tests are
   powered to give an answer, and finally a rural background reference and composition measurement
   ({{ref:a-future}}). Whether the map survives, fails at one kilometre, or fails for temporal or
   background reasons, the outcome says which part of the construction to keep.
