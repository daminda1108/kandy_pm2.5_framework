# Redesign — ladder v2: a deployable estimator, a discovery/confirmation split, and honest scope

**Why (user, 2026-09-25):** "if our methods and approaches and tests don't seem robust or scientific
enough, feel free to redesign and plan and redo them. I want the best."
**Trigger:** the verification pass (`verification_rerun_plan_2026-09-25.md`) showed the headline effects
move with one station split (A7), one learner seed (A8), shrinkage chosen against the scoring target
(B3), same-period calibration (B2), static geography drawn at the scoring sites (B1) and an unregistered
cleaning rule (A6). Several were individually disclosed; together they make the estimand fragile, and
every analysis choice has now been made after looking at the same 47 cities.

## 1. The core problem, stated plainly

1. **Everything is post hoc.** The 47-city panel has been analysed dozens of times. No re-design tuned
   on it can be confirmatory, however careful.
2. **The estimator is not deployable.** The shrinkage weight is chosen against the held-out stations
   (the scoring target), and static geography is averaged over sites that include them. A city without
   monitors can do neither. Both flatter the sensorless rung or the rungs above it.
3. **The estimate is one draw.** One station split and one learner seed decide the headline; A7/A8 show
   those alone move the first-station gain from 11 % to 26 %.
4. **The Kandy-band claim rests on subgroup medians over 13 cities** in which climate band and
   instrument class are aliased (69–77 % low-cost sensors).

## 2. The design: discovery → freeze → register → confirm once

**Discovery (existing 47 cities).** Build and finalise ladder v2 (Section 3) here. Everything computed on
this panel is reported as **exploratory**, including every result in the current draft.

**Freeze.** Code tagged, estimator and endpoints fixed, a hash recorded.

**Register (OSF, before any confirmation PM2.5 is downloaded).** Primary endpoints, decision rules,
the confirmation panel's selection rule and the analysis code. ⚠ Lodging is an outward action: **the user
approves it explicitly.**

**Confirm once, on fresh cities.** Census (`confirmation_pool_census.py`, 2026-09-25): clusters more than
30 km from every city ever drawn, each location active ≥ 365 days in 2024-09 → 2026-08:

| band | ≥ 10 stations | ≥ 6 stations | ≥ 10 reference |
|---|---|---|---|
| deep tropical | 2 | 4 | 1 |
| tropical | 2 | 9 | 2 |
| subtropical | 25 | 46 | 11 |
| temperate | 87 | 153 | 63 |

⇒ **pooled claims are confirmable on ~100+ untouched cities; the deep-tropical claim is NOT confirmable
with public data** (four fresh cities: Bengaluru, Chennai, Rayong, Phuket). That is itself a finding and
sets the scope: the deep-tropical result stays **exploratory and directional**, and the confirmation tests
it only as a **continuous latitude moderator** across all ~100 cities, jointly with instrument class, which
is the only honest way to use the thin tropical end.

## 3. Ladder v2 — the estimator (built on the discovery panel)

| # | v1 (production) | v2 | why |
|---|---|---|---|
| E1 | one station split (fixed seed) | per-city effect = **median over 21 splits** | the split is random; its variance is not the city's |
| E2 | one learner seed; HGB early stopping on a random 10 % | **Bud0c = median prediction over 5 learner seeds** | removes arbitrary seed variance (A8: 11–23 %) |
| E3 | shrinkage w chosen against the held-out target | **w cross-fitted: the median w learned on the OTHER cities** (per rung) | deployable; a city without a dense network cannot choose w against truth |
| E4 | static geography = mean over monitoring sites (incl. held-out) | **mean over a regular 1 km grid within the city's urban centre (GHSL degree of urbanisation, `JRC/GHSL/P2023A/GHS_SMOD_V2-0`, class 30, the connected patch nearest the city centroid; verified on the GEE catalogue 2026-09-25)** | what a city with no monitors actually has; B1 shows it matters (first-two 23.6 → 17.1) |
| E5 | daily value = mean of all station-hours, no minimum | **station-day valid if ≥ 18 of 24 hours (75 %), then equal weight per station** | US EPA 40 CFR Part 50 App. N: a PM2.5 24-h average is valid with ≥ 75 % of hourly values (18); A6 shows it matters [verified 2026-09-25] |
| E6 | calibration fitted on the scored period | **kept** (the use case is reconstruction over the period the sensors run), plus a **secondary prospective arm**: coefficients on the earlier half, scored on the later half | two different, legitimate questions; report both, name each |
| E7 | background = daily P10 of the city's remaining stations | kept, **named "a same-network background series"**; the independent-donor check reported beside it (71 % recovery) | honest naming |
| E8 | subgroup medians by band | **cluster-bootstrapped median regression** of each per-city effect on \|latitude\| and reference fraction **jointly** | addresses the band/instrument alias directly; uses all cities, not 13 |
| E9 | many losses, many strata | **one primary loss (RMSE), two pre-specified secondaries (tail RMSE above the city's 90th percentile, balanced exceedance error at 15 µg/m³)**; everything else exploratory | multiplicity |
| E10 | pooled city bootstrap as the main interval | **two-level cluster bootstrap is primary**; city bootstrap reported beside it | cities share networks |

## 4. Primary endpoints (to be registered; wording fixed at freeze)

- **H1** The first one to two local stations reduce daily city-mean RMSE: split-averaged median gain, cluster
  interval above zero.
- **H2** Stations three to six add less than 1 point beyond the first two (an equivalence bound, fixed now,
  not after seeing data), cluster interval inside ±1.
- **H3** A same-network background series reduces RMSE given six stations: interval above zero.
- **H4** Pooled ordering, background minus first two (no directional prediction on discovery evidence:
  ≈ 0 on MAIAC, +12 on GHAP, +18 under E5) — registered as two-sided, estimate reported.
- **M1 (moderator)** The advantage of local stations over a background grows toward the equator: slope on
  \|latitude\| in the joint median regression, with reference fraction as a covariate.
- Secondary: H1–H4 under the tail and exceedance losses; the prospective arm (E6).

## 5. The spatial tests

Nulls are robust to the verification pass (every result far from its test-specific limit). Confirm cheaply
on the fresh panel: the registered benchmark (`lc_built_2400`) plus two families (stepwise LUR, gradient
boosting) — static predictors only, which the E4 grid pipeline produces anyway. The **spatial learning
curve** is already registered and running: untouched.

## 6. What no redesign can fix, stated in the paper

Band and instrument class are aliased in the deep tropics; low-cost sensors are used uncalibrated (by
design: the instruments a city could deploy); the background rung is same-network; one satellite stream
(MAIAC) and one reanalysis; networks, not campaigns — no deliberate siting in the confirmation panel either.

## 7. Work plan

| step | what | where | needs user? |
|---|---|---|---|
| 1 | finish the verification queue (split-averaged, learners) | laptop, running | no |
| 2 | implement ladder v2 (E1–E10) as `ladder_v2.py`, tests, parity with v1 at v1 settings | laptop | no |
| 3 | static-geo grid pipeline (E4): GHSL urban centres → 1 km grid → the 60 predictors | GEE + Geofabrik | no |
| 4 | run v2 on the discovery panel → exploratory results, fix the equivalence bound for H2 | laptop / Kaggle CPU | no |
| 5 | confirmation panel: selection rule from metadata only (census), per-country cap, ≥ 10 stations | laptop | no |
| 6 | pull confirmation PREDICTORS only (ERA5 drivers, MAIAC, grid geo) | GEE | no |
| 7 | freeze + write the registration | laptop | **approve text** |
| 8 | **lodge on OSF** | outward | **explicit approval** |
| 9 | pull confirmation PM2.5 (OpenAQ S3), score once | laptop / Kaggle | no |
| 10 | write-up: discovery = exploratory, confirmation = confirmatory | draft | — |

Nothing in steps 2–6 touches confirmation PM2.5, so the registration stays blind.

## 8. Progress log

- 2026-09-25: **v2 parity test PASSES** (`scripts/tests/test_ladder_v2_parity.py`): at v1 settings
  (1 split, 1 learner seed, w = cv, no completeness rule, site geography) `ladder_v2.py` reproduces the
  stored v1 MAIAC ladder to 1e-9 for all 47 cities and all four rungs. Every v2 change is therefore
  attributable to the deliberate change, not to a re-implementation.
- 2026-09-25: **E4 grid pipeline built** (`build_static_geo_grid.py`): urban centre from GHS_SMOD_V2-0
  class 30 (fallback 23, 21), 40 random points, the same 60 predictors by the same code
  (`build_lur_predictors.gee_city`, `spatial_curve_predictors.osm_city_tiled`). Test: Delhi (1058) urban
  centre 1,857 km², Beijing (city044) 1,980 km². Full discovery run in progress (Overpass-bound).
- 2026-09-25: **Confirmation pool, both archives.** CNEMC census (199 cities): 28 fresh with ≥ 10
  stations (subtropical 14, temperate 14; no fresh tropical CNEMC city has ≥ 10 stations). OpenAQ: 116
  fresh with ≥ 10 (deep 2, tropical 2, subtropical 25, temperate 87). **~144 fresh cities**, of which 4
  tropical. Confirmation is decisive for pooled claims and weak at the equatorial end (M1 slope only).
- Bottleneck for confirmation: road features for ~144 cities. Overpass ran ~20 min/city for the spatial
  curve; use the Geofabrik/osmium path (`spatial_curve_predictors.osmpbf_stage`, 37 extracts already on
  disk, mostly Europe/Korea) for covered regions and Overpass only for the rest.
- 2026-09-25: **v2 on the discovery panel, site geography** (21 splits, 5 seeds, cross-fitted w, 18 h rule).
  MAIAC reconstruction: first2 **+20.9** [7.2, 42.5] cluster; s36 **+0.44** [0.27, 0.85] (< 1 point);
  bg **+36.1** [17.1, 61.5]; pooled bg − first2 +7.2 [−21.9, +40.4]; **DT bg − first2 −22.5 [−33.7, +10.8]
  (n 11)**; moderator |lat| +1.36 /degree [−0.81, +3.20]. MAIAC prospective: first2 +12.4 [4.5, 41.5]; s36
  +0.37; bg +42.9; pooled bg − first2 +14.9 [−10.1, +43.7]; **DT +6.7 [−21.1, +28.3] — the sign REVERSES**.
  GHAP reconstruction: first2 +15.9, bg +40.4, pooled bg − first2 +20.8 [−2.2, +51.5], DT −2.2.
  **Discovery conclusion:** robust = the first stations help (≈ 21 % reconstruction, ≈ 12 % prospective),
  stations 3–6 add < 1 point, a same-network background adds ≈ 36–43 %. NOT robust = any pooled ordering,
  any latitude moderation, and the deep-tropical inversion (direction in reconstruction only, never
  significant under v2, reversed prospectively). **The inversion is demoted to exploratory.** Final discovery
  numbers await the grid geography (E4).
- 2026-09-25: **Confirmation panel selected from metadata only** (`confirmation_panel.py`, seed 20260926; no PM2.5
  read). Discovery caps (OpenAQ ≤ 4 per country, CNEMC ≤ 12; all tropical taken): **76 cities, 30 countries** —
  temperate 49 OpenAQ + 5 CNEMC, subtropical 11 + 7, tropical 2, deep tropical 2. **63/76 reference-dominated**
  (discovery 31/47): confirmation leans regulatory; state the population it confirms for. Uncapped: ~144, US/EU
  dominated. **Decision for the user at registration: cap 4 (recommended, mirrors discovery) or uncapped.**
- 2026-09-26: **USER DECISION: confirmation panel with cap 4** (76 cities, 30 countries), as selected by
  `confirmation_panel.py` seed 20260926. Frozen: `data/processed/modular/confirmation/confirmation_panel.csv`.
80c4ae34aeb65907149f5c1483020b395a184602a1819a1f619fc08dafe8eecc *data/processed/modular/confirmation/confirmation_panel.csv
- 2026-09-26: registration DRAFTED (`docs/prereg_ladder_v2_confirmation_DRAFT_2026-09-26.md`): H1–H4 + M1, equivalence bound ±1 for H2 fixed now; LOCO over the 123-city union, effects over the 76 confirmation cities; CNEMC confirmation data already on disk (census only) — disclosed. Discovery values to fill from the grid run; then freeze + user approval to lodge. `build_bud0_maiac.pull_city_year` refactor verified (228/228 days, max |d| 7e-16). CNEMC discovery drivers re-pulled with pull_city (met_raw vs pull_city r 0.96–0.998). ladder_v2 default `--cnemc-drivers pull_city`; parity test pinned to met_raw.
- 2026-09-26: **v2 with unified CNEMC drivers (pull_city), site geography.** Reconstruction: first2 19.7 [9.6, 41.0] cl; s36 0.45 [0.23, **1.06**] cl; bg 37.5 [16.2, 61.4]; pooled bg − first2 +6.6 [−21.9, +43.1]; DT −26.4 [−29.4, +17.8] (n 11); |lat| slope +1.10 [−0.73, +2.94]. Prospective: first2 14.3; DT +0.6 [−20.6, +36.5]. Conclusions unchanged by the driver source. ⚠ H2's ±1 bound (written before this run) is narrowly exceeded by the discovery cluster interval here (1.06); the bound is KEPT — moving it after seeing data would be post hoc.
- 2026-09-27: **Network outage** (DNS) stopped all pulls overnight; everything resumed from per-city caches
  under `scripts/retry_until_done.sh` (re-runs a resumable job until exit 0; 5 min back-off, 20 attempts).
  Confirmation predictors complete **76/76** (AOD median 349 retrieval days, min 159).
- 2026-09-27: 🔴 **Defect in `pull_openaq_drivers.pull_city`: its quarterly chunks started at the first quarter
  start AFTER the window opened and stopped at the last one before it closed**, so the head and tail of every
  window's BLH (and the coastal ERA5 fallback) were never requested. Every discovery city lost those days
  silently (dropped by the driver dropna); the earlier explanation "ERA5 not yet published" was WRONG for
  most of them. Fixed (`_bounded_quarters`); every city re-pulled (`drivers_v2_pull.py`: discovery →
  `drivers_v2/`, v1 files untouched so v1 reproduces; confirmation overwritten). Verified: BLH NaN 0 over
  the full window. Ladder v2 default `--cnemc-drivers v2` (all cities from drivers_v2).
- 2026-09-27: `confirmation_members.py`: the frozen panel's 64 OpenAQ clusters regenerated and matched exactly
  (2,909 member locations, SHA-256 7d3e77a0…). `ladder_v2_confirm.py` written: identical ingest function,
  union frame, summaries over confirmation only; **`--ingest`/`--score` refuse without
  `confirmation/REGISTERED.json`** (tested). `ladder_v2.run` gained `frame`/`meta`/`score_cities`.
- 2026-09-27: **E4 discovery grid COMPLETE, 57/57** (56 GHSL urban centre, 1 suburban fallback: 2168; area 5–2,333 km², median 664). Grid vs site features across the 47 scored cities: Spearman median **0.69**; near-point road features (50–300 m) disagree (ρ −0.11…0.08) because monitors sit near roads; monitor sites are ~50 % denser than the urban-centre mean (pop_1000 108 vs 68; built_1000 34,620 vs 23,141) — the B1 bias, measured.
- 2026-09-27: **FINAL DISCOVERY (ladder v2: grid geography, drivers v2, 18 h rule, cross-fitted w, 21 splits,
  5 seeds).** Frame 31,878 city-days (+1,575 from the driver fix). MAIAC reconstruction: first2 **+21.8**
  [10.5, 52.9] cl; s36 **+0.54** [0.21, 0.80]; bg **+34.4** [15.4, 62.2]; bg − first2 +4.8 [−23.6, +52.1];
  DT bg − first2 **−27.4 [−47.8, +11.8]** (n 12); |lat| slope +1.09 [−0.69, +3.35]. Prospective: first2 +12.5,
  bg +38.4, DT −4.1 [−56.1, +1.3]. GHAP reconstruction: first2 +15.1, s36 +0.26, bg +38.9, bg − first2 +13.9
  [−3.7, +55.7], DT +2.2. Under the draft's rules on discovery: H1, H2, H3 hold; H4 no ordering; M1
  undetectable; the DT inversion stays directional/exploratory.
- 2026-09-27: `ladder_v2_confirm.py --dry-run 8` passed end to end (union frame, meta, subset summaries).
  statsmodels QuantReg hits its 5,000-iteration limit in some small bootstrap resamples (dry run, 8 cities);
  monitor at 76 cities.
- 2026-09-27: **Confirmation drivers re-pulled with the fix: 76/76, BLH missing on 0 days** (was all of Sept 2024 and Jul–Aug 2026). So the July–August 2026 gap was the chunking defect, not ERA5 latency.
- 2026-09-27: **v2 secondary losses (discovery, MAIAC):** background − first two is a TIE on RMSE (+4.8 [−23.6, +52.1]) but the background is clearly ahead on the **tail** (+27.5 [2.7, 55.0]; prospective +33.3 [3.1, 57.1]) and on **exceedance** (+34.5 [11.0, 65.9]; prospective +43.2 [7.8, 70.9]); the first two stations add +0.0 to exceedance classification. **Proposed H5** (exceedance ordering) added to the registration draft, flagged for the user's approval. Paper draft: 2.9, 2.10, 2.11 written; 2.6 lists H5 as pending.
- 2026-09-27: **v2 order + station count** (`ladder_v2_secondary.py`; parity with the production ladder exact on 949 city-splits after two fixes the assert caught: donor-weight set and the <30-day identity fallback). Order: bg after stns 3–6 +34.4 [15.4, 62.2], before +31.8 [13.4, 61.5]; stns 3–6 +0.54 [0.21, 0.80] without bg, +2.39 [1.49, 3.44] with; endpoints equal. Count: one station +14.5 [8.4, 51.8]; **second adds +0.93 [0.37, 1.50] paired** (v1 +0.09); 3–8 stations +1.2 to +1.4 over one, plateau. 'Saturation at ONE station' (F.102) REVISED.
- 2026-09-27: **USER APPROVED H5** (exceedance ordering) as a confirmatory endpoint. Order test and station-count sweep to be re-run on v2.
- 2026-09-27/28: Overpass slowed to ~4 min per tile (25 confirmation cities left at 17:17Z). **Geofabrik route**
  `geofabrik_grid_roads.py` (smallest extract containing the tiles, MD5-verified, own segment cache, the same
  `_road_features`) **validated identical** on oaq_GB_102 (england) and city186 (hubei): Spearman 1.0000, max
  |diff| 0.0000. Cost: pure-Python osmium scan, 1.7 GB England = 4.8 h; provinces seconds. Overpass recovered
  overnight (69/76 by 23:34Z); the last 7 run on both routes in parallel. Declared in the registration draft.
