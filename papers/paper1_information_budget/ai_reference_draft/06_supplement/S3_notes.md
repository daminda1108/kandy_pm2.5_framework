[STATUS: DRAFT — AI reference text; the author rewrites. Supplementary notes referred to from the main text.
Tables S1 and S2 are generated (`supplement/build_supplement_tables.py`); this file is written by hand and
carries no count that is not traced to the ledger.]

# Supplementary notes

## S3.1 Why X5's registered statistic is exactly zero

The registered statistic for X5 (site selection by conditioned Latin hypercube against random selection)
came out at 0.00 [0.00, 0.00] in the registered run and again on full records. As coded, the statistic
pools every estimator, including those that never use the fitting stations (the free raster E1 and the
uniform city E0), and takes medians of a rank statistic with few distinct values across replicates. Both
features pin the median at zero, so the reported interval is an artefact (erratum, F.124). Recomputed for
kriging alone with the registered two-level bootstrap, two-sided, per number of stations k: registered
frame +0.013 [−0.062, +0.061] (k = 3), −0.019 [−0.042, +0.028] (k = 5), −0.013 [−0.054, +0.002] (k = 8);
full records 0.000 [−0.049, +0.046], −0.024 [−0.042, +0.024], 0.000 [−0.018, +0.024]. The median over
estimators and densities stays within ±0.012, but the intervals are of the order of ±0.05. The verdict, that
site selection by design gains nothing resolvable, is unchanged [F.119, F.124; Sections 3.6.2, 3.6.5;
`spatial_curve_x5_erratum.py`].

## S3.2 Supporting exploratory analyses of within-city structure

Earlier, lower-powered checks on the same frame of cities point the same way as the registered tests of
Section 2.8 [F.58–F.61]:

- **Single global proxies.** The best single proxy for a station's long-term level was population within
  2 km (rank correlation 0.207).
- **Fitted regime weights.** Emission-proxy weights fitted separately for each climate band, leave one
  city out within band, scored 0.203 pooled against 0.207 for population within 2 km (45 cities); they
  helped in temperate and subtropical cities and hurt in tropical ones [F.59].
- **Inverse-distance interpolation from a city's own network.** Worse than assuming the city is uniform in
  23 of 30 cities.
- **A full land-use regression predictor set.** It moved the pooled correlation only from 0.273 to 0.275.

## S3.3 The station cap and the archive (test A)

Re-applying the confirmation's station cap (12 stations, last two calendar years) to records retrieved on
5 October 2026 matched the stored files wherever both held data. The new records also held extra hours:
most fell after each city's driver window and were removed by the driver merge, and 1,313 hourly values
in seven cities fell inside it. Because the sensorless rung is fitted across all cities, these values moved
every city's effects slightly (69 of 72 per-city vectors differ above 10⁻⁹) without changing any verdict.
This is why the paired change in Section 3.1.7 is reported against both the registered values and the
re-applied cap [F.122].

## S3.4 Corrections made during verification

Three defects were found and corrected before the confirmation was scored. Every result in the paper is the
corrected one; they are listed so that a reader comparing with earlier drafts or the registrations can see
what changed [F.115, F.116].

- **Climate-band labels.** A coding defect left the 11 CNEMC cities without a band label, so band results
  covered OpenAQ cities only. With the labels restored, the temperate, subtropical and tropical cells gained
  their CNEMC cities. No CNEMC city is deep-tropical, so deep-tropical results did not change.
- **Reference classification.** CNEMC cities had been classed as low-cost-sensor cities by default. They are
  regulatory networks and are now classed as reference-dominated (31 reference, 16 low-cost discovery cities).
- **Saturation after the first station.** An earlier estimator chose each city's shrinkage weight against the
  same stations that scored it. It could set a noisy second station's weight to zero, which made the ladder
  appear to saturate at one station (second station +0.09 points). With weights borrowed from other cities
  (cross-fitting, Section 2.3), the second station is worth about one point (+0.93 [0.37, 1.50]).
- **Cluster bootstrap widening.** Computed before these corrections, clustering widened the pooled intervals
  by a factor of 1.45 to 1.97; on the corrected ladders the factor is 1.15 to 2.21 (Section 2.5).

