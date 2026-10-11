# Local fraction at Kandy from measurements — results (2026-10-11, ledger F.134)

Specification: `docs/local_fraction_study_spec_2026-10-11.md`, committed (`f6a8e3d`) before any estimator ran.
Scripts: `pull_cea_airshare_network.py`, `local_fraction_e1.py`, `local_fraction_e2.py`, `local_fraction_e3.py`.
Outputs: `data/processed/decomp/local_fraction_e{1,2,3}.json`. Exploratory.

## Data found for this study

CEA AirShare (`aq.cea.lk`) lists 31 locations. Its public routes `/public/sensor-locations` and
`/public/sensors/location/{id}` give each site's equipment: 1 = regulatory AAQMS (Battaramulla, Kandy), 3 = NBRO sensor
(26 sites; **no history served**), 4 = IQAir (11 sites, daily history from late 2024/2025). At Battaramulla an IQAir unit
is co-located with the reference AAQMS: 471 days, r **0.954**, `AAQMS = 4.53 + 0.779 × IQAir`.

## Results

| route | what it measures | value | 95 % interval |
|---|---|---|---|
| **model, station cell** (same definition) | 1 − ⟨B⟩/⟨PM_cell⟩ | **0.49–0.52** (delivered field over E1's months 0.495; extension tier on E1's days 0.521; on E2's hours 0.505) | — |
| model, basin | 1 − ⟨B⟩/⟨T⟩ | 0.479 (production); 0.489 on E2's hours | 0.428–0.489 across cap specifications |
| **E1 primary** — Kandy minus the median of 5 calibrated regional IQAir sites ≤ 150 km (Ella 65 km, Rathnapura 72, Chilaw 97, Anuradhapura 119, Akkaraipattu 135) | urban increment over regional towns | **0.20** | [0.05, 0.32] |
| E1 sensitivity — daily minimum of those sites | urban increment over the cleanest regional town | **0.36** | [0.25, 0.46] |
| E1 sensitivity — all-island median | | 0.22 | [0.07, 0.36] |
| E1 sensitivity — uncalibrated | | 0.21 | [0.01, 0.38] |
| **E2** — CO tracer intercept, 5th percentile (primary) | share above the PM level at background CO | **0.53** | [0.48, 0.59] (exploratory bootstrap) |
| E2 — CO 10th pct / NO2 5th / NO2 10th | | 0.47 / 0.52 / 0.47 | |
| E3 — 2020 curfew, weather-adjusted | f·a + (1−f)·r | 0.40 (raw 0.52) | [0.29, 0.50] |
| E4 — Seneviratne 2017 PMF | identified local primary sources | ≈ 0.29 (soil 3.8, sea salt 3.2, traffic 7.6, biomass 14.1 %, + metallurgy) | — |

E1 uses 230 matched days (15 months, 2024-10 → 2026-10); E2 15,912 hours (29 months, 2019–2023); E3 34 curfew days
against 54 reference days (2019, 2021).

## Verdict under the rule fixed in the specification

The model's station-cell value (0.49–0.52) lies **above the E1 daily-minimum point value (0.36)**, so by the
pre-specified rule the model's `f` is classed **too high** relative to E1. E2, the second route, **agrees with the
model** (0.47–0.53 against 0.505 on the same hours).

## Interpretation

The two routes bracket the answer from opposite sides, and the direction of each bias is known:
- **E1 is a lower bound by construction.** Every regional reference is a town or city sensor (Rathnapura, Anuradhapura
  and Chilaw are district centres), so each carries its own local increment, which E1 counts as regional. Even the
  daily minimum across five towns is a town. A rural reference would give a higher value.
- **E2 can err in both directions.** Local dust and locally formed secondary aerosol do not follow CO and fall into
  the background (biasing it low); regional plumes carrying CO steepen the slope (direction mixed).
- E3 cannot bound `f` because the regional level also fell in spring 2020 (concurrent South Asian lockdowns). If the
  regional change were zero it would imply `f ≥ 0.40`.
- E4: the identified local primary sources (~0.29) are a floor on the local share of mass; the model's increment also
  contains locally formed secondary material, which PMF on elements does not resolve.

**Defensible statement:** measurements place the local share at the city-centre station between about **0.36** (urban
increment over the cleanest regional town, a lower bound) and **0.53** (combustion-tracer intercept). The model's
0.49–0.52 at that cell, and 0.48 for the basin, lie in the upper part of that range; the pre-specified urban-increment
test classes the model as high, and that test's known bias runs in the direction that would explain the gap. An exact
value is not identifiable from the available records: it would need a rural regional reference monitor (a clean site
upwind of Kandy), which no public network provides.

## Cautions

- E1 covers 2024–2026; the delivered field's `f` is for 2019–2023. Both model comparisons are reported.
- Kandy's AAQMS daily values were used as served; for the live feed the platform's daily aggregation is assumed to use
  local days.
- IQAir calibration from one co-located site (Colombo), applied island-wide.
