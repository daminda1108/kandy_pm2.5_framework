## Conclusions {#a-conclusions-list}

The conclusions are given against the objectives set out in {{ref:a-aims}}. What this study
delivers is a constrained reconstruction of PM2.5 over Kandy and an account of how far each part of
it can be trusted. It does not deliver a validated hourly, kilometre-scale map, and the conclusions
are worded so that they cannot be read as one.

1. **A decomposition that conserves the city-wide mean can be built for Kandy from data available
   everywhere.** The field separates a regional background from a local increment whose spatial
   average is fixed by construction, so an error in the pattern moves material without creating
   it; in the delivered field the city mean departs from the anchor by at most
   {{claim:gauge.drift_hi_pct}} per cent. Each component declares which observations it may use,
   and removing an observation stream reproduces the simpler tier exactly, which is what allows
   the value of each stream to be measured.
2. **The reconstructed field is above the World Health Organization annual guideline in every
   year of the study period**, at {{claim:kandy.mean_min}} to {{claim:kandy.mean_max}} micrograms
   per cubic metre, with a north-east monsoon maximum, a south-west monsoon minimum and a midday
   trough below the night. That PM2.5 is a substantial concern in Kandy is better supported than
   the exact values, whose level is open (conclusion 3). The decomposition assigns about half of
   the concentration to the local increment, {{claim:partition.f}} in production and
   {{claim:v2.f.cap_min}} to {{claim:v2.f.cap_max}} across reasonable forms of the constraint that
   sets it. This is a bound on a constructed partition, not a source apportionment: it does not
   say that half of Kandy's PM2.5 is emitted in Kandy. Weighting by population raises exposure
   {{claim:exposure.uplift_pct}} per cent above the area mean, and both that figure and the
   illustrative burden of {{ref:app-attributable-burden-projection}} inherit the uncertainty of the
   level and of the unvalidated spatial pattern.
3. **The evidence for the field is graded, and its parts stand at different strengths.**
   - *The seasonal cycle is the best-supported property.* The construction reproduces it in every
     analogue city when their own observations are withheld (seasonal correlation
     {{claim:scorecard.seasonal_r_lo}} to {{claim:scorecard.seasonal_r_hi}}).
   - *The day-to-day sequence is supported where the sensors reported.* Placed on the ladder in
     {{claim:v2.km.cities_scored}} cities, the deployed temporal model reduces daily error by
     {{claim:v2.km.reco.unio.gK2_rmse.median}} per cent against a generic sensorless estimate where
     its two anchor stations observed the period, and by no resolvable amount where they did not.
     At Kandy that means the daily sequence is credible on days the sensors reported and much less
     so on the many days they did not.
   - *The daily cycle's timing is supported and its depth is not.* The daily cycle transfers to some
     analogue cities and not to others (diurnal correlation {{claim:scorecard.diurnal_r_lo}} to
     {{claim:scorecard.diurnal_r_hi}}), hourly skill at Kandy is modest (a coefficient of
     determination of {{claim:v2.tanchor.lagfree.r2}} out of sample), and the depth of the cycle
     depends on a humidity correction that only a co-located reference instrument can check.
   - *The absolute level is open.* An independent national record agrees with the field in two
     years, three low-cost records sit below it, and the satellite level used to anchor it sits
     above the withheld city mean across the ladder's cities. The interval's nominal ninety per
     cent coverage is not achieved, at Kandy or in those cities.
4. **The field is not supported below the kilometre scale, and its spatial pattern is a hypothesis,
   not a measurement.** More of the variation within a city lies inside a single cell than between
   cells, no model built from freely available covariates recovers it, the dispersion step meant to
   place the local increment lowers its agreement with withheld stations, and a handful of
   interpolated stations does not recover it either; the limit is one of support and of the
   information available, not of the model chosen. The map may illustrate the construction and
   guide where to measure. It must not be used to rank neighbourhoods or to place interventions as
   though its differences between cells had been validated.
5. **The measurement worth most to Kandy is a set of continuously reporting stations whose
   readings enter the estimate each day.** A station read daily is worth several times what the
   same station is worth as a one-off calibration, and a handful of stations fixes the level and
   the daily sequence of a city mean but not a neighbourhood map. A reference-grade instrument among
   them would also settle the level and the depth of the daily cycle. This conclusion replaces an
   earlier ordering of a background series above local stations, which a review traced to a
   registered comparison of rungs that used their stations differently. The comparison that
   replaced it, with every station used the same way, finds the kind of station makes no resolvable
   difference, but it is a post hoc re-analysis of the registered data, not a registered
   confirmation, and a fresh pre-specified test is required before the near-equivalence of station
   types is treated as established ({{ref:a-future}}).
