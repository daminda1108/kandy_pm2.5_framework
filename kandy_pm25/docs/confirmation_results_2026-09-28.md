# Confirmation of ladder v2 on fresh cities — registered results (OSF `ueyfr`, 2026-09-28)

Registration: `docs/prereg_ladder_v2_confirmation_2026-09-28.md` (OSF `ueyfr`, project `dm9zf`,
registered 2026-09-28 04:24:22 UTC, pending OSF approval at lodging). Scored once, 2026-09-28
~08:00 UTC, by `scripts/ladder_v2_confirm.py --score` on the frozen code (all 27 files in
`docs/ladder_v2_freeze_manifest.json` re-hashed identical immediately before the run).
Outputs: `data/processed/modular/ladder_v2/confirm_REGISTERED_{summary.json,splits.csv,percity_*.csv}`.
Deviations (execution only, logged before scoring): `data/processed/modular/confirmation/DEVIATIONS.md` (E-1).

## Panel as scored

- 76 registered → **72 scored** (4 excluded by the registered rules, never replaced): oaq_BG_97 (7
  stations < 10); oaq_CZ_109, oaq_IT_115, oaq_IT_44 (183 / 140 / 143 driver-matched days < 200).
- 50 temperate, 18 subtropical, 2 tropical, 2 deep tropical; 63 reference-dominated; 30 clusters
  (29 countries + CNEMC). Splits per city 6–21 (cities with few valid split draws keep fewer).
- Background rung (Bud3) exists for 68: four cities (oaq_ES_42, oaq_IT_114, oaq_ZA_105, oaq_ZA_106)
  have too few non-held, non-rung stations for it under the frozen rule.
- Ingest audit (`confirm_ingest_audit.py`): estimated silent loss of daily files **0.00 % in all 64
  OpenAQ cities** (listed-but-absent files sampled, none held valid PM2.5).

## Registered endpoints (reconstruction arm, RMSE, median [two-level cluster 95 %])

| id | estimate | confirmation | rule | verdict | discovery (exploratory) |
|---|---|---|---|---|---|
| H1 | first two stations | **+8.53 [+3.07, +25.12]**, n 72 | lower > 0 | **SUPPORTED** | +21.8 [10.5, 52.9] |
| H2 | stations 3–6 | **+0.22 [+0.12, +0.50]**, n 72 | inside [−1, +1] | **SUPPORTED** | +0.54 [0.21, 0.80] |
| H3 | background given six | **+41.10 [+26.77, +62.84]**, n 68 | lower > 0 | **SUPPORTED** | +34.4 [15.4, 62.2] |
| H4 | background − first two (two-sided) | **+24.58 [+4.07, +47.80]**, n 68 | ordering claimed only if 0 excluded | **ORDERING FOUND: background > first two** | +4.8 [−23.6, +52.1] |
| M1 | slope of H4 effect on \|lat\| | **+0.53 [−1.79, +1.49]** /°, n 68 | lower > 0 | **NOT SUPPORTED — undetectable** (4 cities below 23.5°, as stated in advance); 1 of 1,000 bootstrap fits did not converge | +1.09 [−0.69, +3.35] |
| H5 | background − first two, exceedance loss | **+59.33 [+33.93, +67.73]**, n 67 | lower > 0 | **SUPPORTED** | +34.5 [11.0, 65.9] |

City-bootstrap intervals agree in sign on every endpoint (H1 [3.47, 18.58]; H3 [33.7, 52.6];
H4 [10.3, 37.5]; H5 [43.1, 67.0]).

**What changed from discovery.** H1 holds but is **less than half the discovery size** (8.5 vs 21.8);
H4, undetermined on discovery, now resolves: in this mainly temperate and subtropical, mainly
regulatory population, a same-network background series is worth more than the first two local
stations even for ordinary-day RMSE. The deep-tropical inversion stays exploratory: M1 cannot see
it (2 + 2 low-latitude cities; their H4 medians −9.6 and −7.7 are descriptive only).

## Secondary (registered as not counted toward confirmation)

| effect | reconstruction | prospective |
|---|---|---|
| first two, tail | −2.66 [−10.31, +3.74] | −0.72 [−9.51, +9.07] |
| background − first two, tail | +54.15 [+31.04, +66.66] | +52.21 [+28.13, +63.64] |
| first two, exceedance | −0.51 [−7.61, 0.00] | 0.00 [−5.64, +0.80] |
| stations 3–6, exceedance | 0.00 [0.00, 0.00] (74 % of cities exactly 0: no day reclassified) | 0.00 |
| background, exceedance | +52.54 [+32.75, +67.28] | +50.53 [+34.78, +67.18] |
| H1 / H2 / H3 / H4, RMSE | — | +6.46 [2.54, 23.51] / +0.42 [0.18, 0.78] / +44.25 [26.78, 61.55] / +27.31 [5.09, 47.96] |
| M1 slope | — | +0.71 [−1.89, +1.62] |

The prospective arm reproduces every registered verdict. The first local stations do nothing
detectable for high days or for guideline exceedances; their gain is on ordinary days.

## Exploratory, not registered (added after scoring)

Split by network (`confirm_REGISTERED_by_network_EXPLORATORY.json`), because CNEMC is one cluster
holding 12 of 72 cities:

| | OpenAQ only (n 60 / 56) | CNEMC only (n 12) |
|---|---|---|
| first two | +12.32 [+2.88, +27.48] | +4.32 [+2.42, +8.83] |
| background | +37.39 [+24.37, +44.65] | +68.81 [+65.06, +72.99] |
| background − first two | **+11.46 [+1.35, +33.33]** | +63.87 [+60.38, +67.66] |
| background − first two, exceedance | +56.73 [+29.67, +67.59] | +67.08 [+54.31, +83.79] |

H4's ordering survives without the CNEMC network, at about half the pooled size. CNEMC cities
(regulatory, 10+ co-located stations per city) make a background series nearly the same as the
city signal, which is why the effect there is so large.

## Reading

Confirmed for this population: one or two local stations help (smaller than discovery suggested),
four more add almost nothing, and a same-network background adds most, **more than the first two
stations** for ordinary days, for high days and for exceedances. ⚠ The background rung is a
**same-network** series (daily 10th percentile of the city's other stations), not a regional station
outside the city; what it confirms is the value of a background level measured by the network, and
it transfers to an external regional station only as far as that station tracks the city floor.
Not confirmable here: any latitude
dependence, and therefore anything specific to the deep tropics (Kandy's band). Scope: 50 of 72
scored cities are temperate and 63 of 76 reference-dominated; the population is stated in the
registration and results do not extend to low-cost-sensor tropical networks by construction.
