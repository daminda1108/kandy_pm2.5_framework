# Pre-registration — confirmation of the information-budget ladder on fresh cities

**Status:** approved by the author and lodged on OSF, 2026-09-28, before any confirmation PM2.5 was
downloaded (see section 3 for the one disclosed exception).

**OSF:** registration [`ueyfr`](https://osf.io/ueyfr/), project [`dm9zf`](https://osf.io/dm9zf/); registered
2026-09-28 04:24:22 UTC (pending OSF approval at lodging). The text below is the lodged text unchanged.

## 1. Why this registration exists

Every result on the 47-city discovery panel is exploratory: the panel was analysed many times, and a code
audit (ledger F.115) and a redesign of the estimator (ladder v2, `docs/redesign_ladder_v2_plan_2026-09-25.md`)
were both done on it. This registration fixes the estimator, the endpoints and the decision rules
**before any PM2.5 value of the confirmation cities is downloaded**, and tests them once.

## 2. Confirmation panel (frozen)

- File: `data/processed/modular/confirmation/confirmation_panel.csv`, SHA-256
  `80c4ae34aeb65907149f5c1483020b395a184602a1819a1f619fc08dafe8eecc`.
- Rule (`scripts/confirmation_panel.py`, seed 20260926), applied to metadata only: OpenAQ clusters
  (single-linkage 25 km) whose locations were active ≥ 365 days in 2024-09-01 → 2026-08-31 and that lie more
  than 30 km from every city ever drawn, with ≥ 10 locations; CNEMC cities not in discovery with ≥ 10
  stations; at most 4 OpenAQ clusters per country and 12 CNEMC cities (as in discovery); every tropical
  candidate taken.
- **76 cities in 30 countries**: temperate 54, subtropical 18, tropical 2, deep tropical 2; 63 of 76
  reference-dominated. The panel therefore confirms for a mainly temperate and subtropical, mainly regulatory
  population; this is stated in advance.
- Exclusions, applied by the discovery rules and reported, never replaced: fewer than 10 stations with data
  after QC; fewer than 120 scored days; missing a predictor stream.

## 3. Data (identical definitions to discovery)

- PM2.5: OpenAQ S3 archive by the discovery ingest function unchanged (`ingest_openaq_sample.ingest_city`:
  at most 12 member locations per city, ranked by record span, over the city's last two calendar years of
  coverage; members from `confirmation_members.csv`, SHA-256
  `7d3e77a0d5752b7d6e60431d659a720fa8eac5bf0844fcc10a93cc856efa70b7`) and CNEMC (all stations); the scored
  window is the intersection with the driver window 2024-09-01 → 2026-08-31; hourly values in (0, 1000) µg m⁻³;
  **a station-day is valid with ≥ 18 of 24 hours** (US EPA 40 CFR Part 50 App. N); daily city and rung
  values are equal-weight means over valid stations.
- Drivers: ERA5-Land daily t2m, u10, v10, wind, ERA5 BLH at 00/06/12/18 UTC, day of year, by
  `pull_openaq_drivers.pull_city` for every city, discovery and confirmation, after the 2026-09-27 fix to its
  chunking (the head and tail of every window were not requested before; all cities re-pulled).
- Cities kept by the discovery rules: ≥ 10 stations with data, ≥ 200 driver-matched days, ≥ 120 scored days.
- Code path tested before lodging by `ladder_v2_confirm.py --dry-run` (discovery cities relabelled; no
  confirmation data). `--ingest` and `--score` refuse to run until `confirmation/REGISTERED.json` exists.
- Satellite: MAIAC AOD (MCD19A2), best quality, 5 km mean, missing days left missing
  (`build_bud0_maiac.pull_city_year`).
- Static geography: the same 60 predictors on 40 random points in the city's urban centre (GHSL
  GHS_SMOD_V2-0 class 30, fallback 23 then 21), `build_static_geo_grid.py`.
  Road features were read from OpenStreetMap through the public Overpass API; for the cities where that
  server was too slow (seven cities: oaq_AT_17, oaq_AU_45, oaq_BE_6, oaq_GB_4, oaq_GB_34, oaq_IE_31,
  oaq_IT_44) they were read from Geofabrik extracts of the same OSM data by `geofabrik_grid_roads.py`, with
  the same feature function. The two routes were
  verified identical on two cities computed both ways (Spearman 1.0000, maximum difference 0.0000;
  also D-6 of the spatial learning curve).
- **Predictors frozen by hash:** every confirmation predictor file (drivers, AOD, urban-centre geography, the
  panel and member lists; 383 files, 76 cities) is listed in `docs/confirmation_data_manifest.json`,
  combined SHA-256 `6754d841e18e3f375b25615cf722df4246926e0154ab1e832fe7984338b0830f`.
- Predictors for all 76 cities were pulled before this registration. No OpenAQ PM2.5 for the 64 OpenAQ
  confirmation cities has been downloaded. **Disclosure:** hourly CNEMC data for the 12 CNEMC confirmation
  cities are already on disk, downloaded in 2026 as part of a 199-city archive census that recorded each
  city's mean and 90th-percentile PM2.5 and its station count (`panel_census.csv`). No ladder, station-split
  or rung analysis has ever been run on them, and none will be before lodging. The census summaries carry no
  information about any registered endpoint, which are all within-city comparisons between rungs.

## 4. Estimator (ladder v2, frozen code: commit `e6b744ba8f8848cc8d2881531cae533181082767`, per-file SHA-256 in `docs/ladder_v2_freeze_manifest.json`)

`scripts/ladder_v2_confirm.py --ingest` then `--score` (21 splits, 5 learner seeds, cross-fitted weights,
18 h completeness, urban-centre geography, drivers v2, MAIAC), which runs the frozen `ladder_v2.run` over the
union of discovery and confirmation cities and summarises the confirmation cities only.
- Held-out set per city: ⌊n/3⌋ (min 3) stations drawn by seed; observation rungs: stations 1–2 (Bud1),
  1–6 (Bud2), a same-network background series = daily 10th percentile of the remaining stations (Bud3).
- Sensorless rung Bud0c: histogram gradient boosting (learning rate 0.06, ≤ 300 iterations, scikit-learn
  1.8 defaults), leave-one-city-out over the union of discovery and confirmation cities (123), prediction =
  median over 5 learner seeds.
- Rungs combine by shrinkage with a weight **cross-fitted from the other cities** (median of their
  within-city optima), never chosen against the scored city's held-out stations.
- Per-city effect = median over 21 station splits. Effects are summarised over the **76 confirmation
  cities only**.
- Intervals: two-level cluster bootstrap (clusters = country for OpenAQ, the CNEMC network as one), 4,000
  draws, percentile 95 %; the city bootstrap is reported beside it.

## 5. Endpoints and decision rules (reconstruction arm, RMSE)

| id | hypothesis | estimate | supported if | discovery value (exploratory) |
|---|---|---|---|---|
| **H1** | the first one or two local stations reduce daily city-mean RMSE | median % gain Bud0c → Bud1 | cluster lower bound > 0 | +21.8 [10.5, 52.9] |
| **H2** | stations three to six add less than one point | median % gain Bud1 → Bud2 | cluster interval inside [−1, +1] (equivalence bound fixed here) | +0.54 [0.21, 0.80] |
| **H3** | a same-network background series reduces RMSE given six stations | median % gain Bud2 → Bud3 | cluster lower bound > 0 | +34.4 [15.4, 62.2] |
| **H4** | ordering of background vs first two (two-sided; no direction predicted) | median of within-city (Bud3 gain − Bud1 gain) | reported; an ordering is claimed only if the cluster interval excludes 0 | +4.8 [−23.6, +52.1] |
| **M1** | local stations gain relative to a background toward the equator | slope on \|latitude\| in the median regression of (H4 effect) on \|latitude\| and reference fraction | cluster lower bound of the slope > 0 | +1.09 /° [−0.69, +3.35] |
| **H5** (approved by the author 2026-09-27) | for guideline exceedances a background series is worth more than the first two stations | median of within-city (Bud3 gain − Bud1 gain) under the exceedance loss (balanced error at 15 µg m⁻³) | cluster lower bound > 0 | +34.5 [11.0, 65.9] (prospective +43.2 [7.8, 70.9]) |

H5 was added after the final discovery run, because the discovery secondary losses showed it more
clearly than any other ordering (tail loss +27.5 [2.7, 55.0]); it is registered as a directional
prediction derived from discovery, which is what the confirmation is for. With H5 there are five
confirmatory tests on the confirmation panel; no multiplicity correction is applied, and each is
reported against its own rule.

⚠ Power stated in advance: M1 has four confirmation cities below 23.5° and is expected to be weak; a null
on M1 is reported as undetectable, not as absence.

**Secondary (not counted toward confirmation):** H1–H5 under the tail loss (RMSE on days with observation ≥
the city's 90th percentile) and H1–H3 under the exceedance loss; the prospective arm (coefficients and weights
on the earlier half of each record, scored on the later half); the order test and station-count sweep
(`ladder_v2_secondary.py`). The MAIAC→GHAP contrast is not repeated (GHAP is excluded from confirmation).

Discovery values: 47 cities, MAIAC, the frozen estimator, reconstruction arm, median [two-level cluster
95 %]; exploratory (`ladder_v2/maiac_s21_b5_crossfit_c18_grid_dv2_summary.json`). Deep-tropical H4 on
discovery −27.4 [−47.8, +11.8] (n 12), reported for context only.

## 6. What would change the conclusions (written before the data)

- H1 or H3 fails → the corresponding discovery claim does not generalise beyond the discovery panel.
- H2 fails with an interval above +1 → denser local networks do add information in this population.
- H4 excludes zero → an ordering exists in this population; its direction is reported as found.
- M1 supported → the discovery hint of a tropical inversion generalises as a latitude gradient; M1
  undetectable → the deep-tropical inversion remains exploratory, as the discovery evidence already implies.
- H5 supported → for guideline exceedances a background series outranks the first local stations in this
  population; H5 fails → the discovery ordering under that loss does not generalise, and no recommendation
  about exceedance monitoring is made from it.

## 7. Deviations

Any deviation is logged with its date and reason before scoring and reported beside the registered result.
