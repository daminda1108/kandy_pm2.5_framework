[STATUS: DRAFT — working document, not for submission. Every claim the paper makes, its number,
interval, n, evidence status and source. Update this file first when a number changes; the prose
follows it. Built 2026-09-28; F.118–F.123 added 2026-10-05.]

# Evidence map

Status key: **CONF** registered and confirmed on fresh cities · **REG** registered, run on
discovery · **EXPL** exploratory (post hoc or discovery-only) · **RETIRED** do not quote.

Intervals are two-level cluster 95 % unless marked (city) = city bootstrap.

## Ladder (daily city-mean RMSE unless stated)

| claim | number | interval | n | status | source |
|---|---|---|---|---|---|
| first two stations reduce error | +8.53 % | [3.07, 25.12] | 72 | CONF (H1) | `ladder_v2/confirm_REGISTERED_summary.json`; F.117 |
| stations 3–6 add < 1 point | +0.22 | [0.12, 0.50] | 72 | CONF (H2) | same |
| background given six stations | +41.10 % | [26.77, 62.84] | 68 | CONF (H3) | same |
| background > first two, ordinary day | +24.58 | [4.07, 47.80] | 68 | CONF (H4, two-sided) | same |
| background > first two, exceedance | +59.33 | [33.93, 67.73] | 67 | CONF (H5) | same |
| latitude dependence | +0.53 /° | [−1.79, +1.49] | 68 | CONF: undetectable (M1) | same |
| prospective arm reproduces all verdicts | H1 +6.46, H3 +44.25, H4 +27.31 | see 3.1.3 | 72/68 | CONF (secondary) | same |
| first two stations on high days | −2.66 | [−10.31, +3.74] | 72 | CONF (secondary) | same |
| H4 without CNEMC | +11.46 | [1.35, 33.33] | 56 | EXPL | `confirm_REGISTERED_by_network_EXPLORATORY.json` |
| first two, discovery | +21.8 % | [10.5, 52.9] | 46 | EXPL | `maiac_s21_b5_crossfit_c18_grid_dv2_summary.json` |
| first two, deep tropics, discovery | +52.9 % | [27.5, 64.4] | 13 | EXPL | same |
| background − first two, deep tropics | −27.4 | [−47.8, +11.8] | 12 | EXPL | same |
| same, deep tropics, exceedance | +7.71 | [0.07, 34.30] | 11 | EXPL | same |
| one station | +14.5 % | [8.4, 51.8] | 46 | EXPL | `secondary_maiac_s21_b5.json`; F.116 addendum |
| second station over first | +0.93 | [0.37, 1.50] | 46 | EXPL | same |
| order-robust: background after 2 vs after 6 | 31.8 vs 34.4 | endpoint gap −0.01 [−0.07, 0.04] | 44 | EXPL | same |
| first-station gain across learners | 22–41 % | — | 46 | EXPL | F.116 |
| GHAP tilts ordering toward background | MAIAC − GHAP −5.53 | [−16.84, −1.45] | 45 | EXPL | F.117 addendum |
| external network recovers the background rung | 71 % | [44, 82] | — | EXPL | F.116 |
| richer bottom rung improves Bud0 | +13.1 % | [9.2, 16.2] | 72 | REG b379r (R1) | `rich_baseline_results_2026-09-28.md`; F.118 |
| first-two gain does not shrink with richer rung | −0.7 | [−7.1, +1.7] | 72 | REG b379r: R3 refuted | same |
| H4 / H5 under richer rung | +21.7 / +45.4 | [3.8, 40.7] / [27.9, 58.3] | 68/67 | REG b379r | same |
| TabPFN bottom rung vs HGB | −11.1 % | [−50.9, −1.1] | 72 | REG jea58 | `learner_robustness_results_2026-09-29.md`; F.120 |
| GRU / HGB+physics vs HGB | +1.8 / +2.0 | [−4.3, +8.9] / [−0.3, +4.6] | 72 | REG jea58 | same |
| H4 under TabPFN | +8.3 | [−5.4, +40.6] | 68 | REG jea58 (two-sided, unresolved) | same |
| full networks: H1 / H2 / H3 | +7.68 / +0.46 / +46.02 | [3.24, 19.95] / [0.26, 0.73] / [34.26, 63.16] | 75/75/72 | REG mhgna, held | `full_network_ladder_results_2026-10-05.md`; F.122 |
| full networks: H4 / H5 | +32.01 / +63.38 | [11.59, 50.45] / [33.54, 71.83] | 72/71 | REG mhgna | same |
| full − registered, H4 (paired) | +2.39 | [0.57, 8.91] | 68 | REG mhgna N6 (two-sided) | same |
| full − re-applied cap, H4 (paired) | +3.18 | [−0.40, +9.54] | 68 | REG mhgna N6 secondary | same |
| full networks: cities with a background rung | 72 of 75 | — | — | REG mhgna secondary | same |

## Bounded spatial tests (within-city Spearman, paired vs built-up benchmark 0.301)

| claim | number | interval | n | status | source |
|---|---|---|---|---|---|
| learned pattern | +0.022 | [−0.062, +0.050] (city) | 46 | REG 2jyfg, fails | learned-pattern note; F.115 |
| embeddings E1 / E2 | −0.028 / −0.002 | [−0.170, +0.084] / [−0.064, +0.049] (city) | 47 | REG 6udm3, fail | F.111 |
| embeddings E3 partial ρ | +0.191 | [−0.007, +0.355] | 47 | REG 6udm3, undetectable | F.111 |
| six model families | −0.081 to +0.018 | all include 0 | 47 | EXPL | F.105 |
| oracle kriging / GWR / IDW | 0.048 / 0.073 / 0.190 | — | 47 | EXPL | F.105 |
| deliberate vs convenience siting | −0.044 | [−0.095, +0.118] (city) | 43 | EXPL | F.103 |
| detection limits | 0.130; 0.180 / 0.080; 0.09–0.16 | — | — | — | `mde_recompute.py`; F.115 |

## Spatial learning curve (within-city Spearman)

| claim | number | interval | n | status | source |
|---|---|---|---|---|---|
| cities cross the raster (one-year records) | 11 of 18; 5 at k = 3 | — | 18 | REG rqn4y X2 held | `spatial_curve_results_2026-09-28.md`; F.119 |
| reach of one station | 1.0 km | — | 18 | REG rqn4y X7 held | same |
| TabPFN with coordinates worse | −0.052 | [−0.103, −0.018] | — | REG 26hp8 X10 refuted | same |
| full-record frame | 23 primary, 960 sites, 9 countries; Bangkok deep tropical | — | — | REG fu59b F1 | `spatial_curve_full_record_results_2026-10-05.md`; F.123 |
| cities cross the raster (full records) | 15 of 23; 8 at k = 3 | — | 23 | REG fu59b X2 held | same |
| within-cell ceiling exceeded | London −0.28, Bangkok −0.57 ceilings | — | 3 with ceiling | REG fu59b X4 refuted | same |
| terrain moderates the curve (X-T) | 0 of 32 intervals exclude 0; min p 0.09 | — | 18 / 23 | EXPL (amendment 2) | `analysis{,_full}/moderators_terrain.csv` |
| tropical arm vs temperate envelope | none above; 3 of 8 partly below | MDE 0.28 | 8 | EXPL fu59b F3 | `F3_tropical_arm.json` |

## Panel and data

| claim | number | source |
|---|---|---|
| discovery frame | 47 cities, 28 countries, 642 stations, 30,327 city-days; 46 scored | `ladder_v2.load`; §2.1 |
| confirmation panel | 76 registered, 30 countries; 72 scored; 4 excluded by rule | `confirmation_results_2026-09-28.md` |
| confirmation composition | 50 temperate, 18 subtropical, 2 tropical, 2 deep tropical (scored); 63/76 reference | same |
| retrieval completeness | 0.00 % estimated loss, 64 cities | `confirmation/ingest_audit.csv` |
| deep-tropical dense networks | 6 vs 65 temperate clusters (≥ 10 reference) | F.53; `global_reference_census.py` |
| registrations | 17 in the register; 14 run; 105 predictions: 66 held, 23 refuted, 6 not tested, 10 two-sided or exploratory | `#writing/registrations.json` (2026-10-05) |

## RETIRED — never quote

| claim | why | replacement |
|---|---|---|
| local stations 4.2× the background in the deep tropics; +33.3 [7.0, 50.1] | one split, one seed (F.115) | −27.4 [−47.8, +11.8], EXPL |
| GHAP halves the value of a local station | v2 paired +2.3 [−0.6, +16.9] (F.117 addendum) | GHAP tilts the ordering, EXPL |
| first two stations ≈ 22 % as a headline | discovery, band-balanced | 8.5 % CONF |
| saturation at ONE station | in-sample shrinkage (F.116 addendum) | second station +0.93 |
| "no pooled ordering" | superseded by confirmation | H4 +24.6 |
| TabPFN "reproducible on any machine" | 1/80 across machines | deterministic within one environment (4qs9c §5) |
