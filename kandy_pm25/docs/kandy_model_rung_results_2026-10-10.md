# The deployed Kandy model as a rung of the ladder: results (2026-10-10, ledger F.125)

**EXPLORATORY.** Spec fixed and committed before scoring: `docs/kandy_model_rung_spec_2026-10-10.md`
(git a45cf0c; amendment before scoring in the following commit). Script `scripts/ladder_v2_kandy_model.py`;
inputs `scripts/pull_kandy_model_priors.py` (GEOS-CF daily area means 2021–2025 and van Donkelaar V6.GL.02
annual 2019–2022 for 133 ladder cities, urban-centre boxes). Outputs `data/processed/modular/ladder_v2/kandy_model_*`.
Claims `v2.km.*` (build_claims.py `kandy_model_rung`). Thesis A §3.2.3 + Table 3.3.

**Coverage.** 118 cities with inputs (1 without Bud0), 104 scored; city × split cells: 1,827 scored, 497 anchor pair
< 120 days, 133 scored days < 120, 21 pool < 2. Scored window ends 2025-12-31 (GEOS-CF on GEE ends 2026-01-02).

## Union (n = 104 cities, 49 networks): median over cities, cluster-bootstrap 95 % interval

| | reconstruction | prospective |
|---|---|---|
| Bud0 daily RMSE (µg/m³) | 12.97 [8.18, 17.35] | 12.24 [8.00, 16.13] |
| K2 (deployed chain, 2 anchors) RMSE | 8.35 [5.73, 10.60] | 10.70 [7.31, 14.47] |
| gain K0 (chain, no stations) vs Bud0, % | −51.5 [−153.5, −18.5] | −48.7 [−171.4, −17.0] |
| gain Bud0cal2 (2 stations, calibration) % | +12.6 [5.1, 29.4] | +12.0 [5.0, 26.1] |
| **gain K2 (deployed chain) %** | **+32.7 [25.9, 41.9]** | **+4.8 [−2.8, 25.8]** |
| gain L2same (2 stations read on the day) % | +60.8 [47.2, 69.3] | +59.5 [45.8, 65.9] |
| K2 − Bud0cal2 (points) | +17.0 [6.7, 21.4] | −6.4 [−12.7, +3.0] |
| L2same − K2 (points) | +22.2 [12.1, 32.6] | +44.0 [26.1, 67.3] |
| r: Bud0 / K0 / K2 / L2same | 0.58 / 0.65 / 0.86 / 0.94 | 0.61 / 0.66 / 0.67 / 0.91 |
| bias %: Bud0 / K0 / K2 | +16.9 / +7.6 / +7.9 | +19.0 / −0.5 / +17.7 |
| K2 nominal-90 % interval coverage | 0.696 [0.628, 0.766] | 0.797 [0.701, 0.855] |

Confirmation cities only (n = 64): K2 gain +32.7 [23.3, 42.0], K2 − Bud0cal2 +18.9 [6.9, 26.5] (reconstruction).

## Reading

- Q1: where the anchor pair observed the scored period, the deployed chain sits between calibration-only (+12.6)
  and reading the stations on the day (+60.8). Part of its gain is in-period training on the anchor record, i.e. the
  position of Kandy's reconstruction on sensor-observed days.
- Q4: prospectively the gain is not resolvable and the chain is no better than recalibration (−6.4 [−12.7, +3.0]);
  r falls 0.86 → 0.67. This is Kandy's position on unobserved days.
- Q2: the chain without stations tracks the daily sequence better than Bud0 (r 0.65 vs 0.58) but overstates its
  amplitude (GEOS-CF swings), so RMSE is ~50 % worse. The two stations scale the prior.
- Q3: interval under-covers (0.70 reconstruction, 0.80 prospective) — matches Kandy's 72.4 % at the sensors.
- Level from van Donkelaar sits +8 % (reco) / +18 % (pros) above the withheld mean: same sign as the Kandy W11
  discrepancy (field above three of four records).

Declared differences from the deployed Kandy anchor: daily resolution; predictors = GEOS-CF prior + ERA5 daily
meteorology + calendar (no CAMS, MAIAC, TROPOMI, t925, sensor metadata); conformal strata by month only.
