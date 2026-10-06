# Amendment 2 to OSF `rqn4y` — an exploratory terrain moderator, two implementation corrections, and a disclosure of everything done before scoring

**Lodged before any real PM2.5 value was scored by any estimator.** Project: Kandy PM2.5 (Daminda
Alahakoon, University of Peradeniya). Drafted 2026-09-11. Parent registration: OSF
[`rqn4y`](https://osf.io/rqn4y/). Amendment 1: OSF [`26hp8`](https://osf.io/26hp8/) (deep-learning
arms). Plan: `kandy_pm25/docs/spatial_learning_curve_plan_2026-09-11.md` §13.

**OSF [`4whsc`](https://osf.io/4whsc/), project [`qxam3`](https://osf.io/qxam3/)**, registered
2026-09-11 13:36:44 UTC by `scripts/osf_lodge.py` and verified as an artefact after the request.
Submitted pending OSF approval; the timestamp is fixed at submission.

This amendment **adds one exploratory analysis** and **records two corrections to how registered
steps are implemented**. It changes no estimand, no estimator, no prediction, no pass criterion,
no stop rule and no detection limit in `rqn4y` or `26hp8`.

---

## 1. What had been done when this was lodged, disclosed in full

- **Frame frozen by the registered rule (D3).** Registered frame (75 per cent day coverage):
  18 primary cities, 745 sites, 7 countries (13 temperate, 4 subtropical, 1 tropical); 15
  secondary; band arm 6 cities. Stop rule passed (18 ≥ 10). Declared sensitivity S-1 (70 per cent)
  also frozen. **No estimator had been fitted to any of it.**
- **Predictors built (D4)** for 1,141 sites in 41 cities, no missing values.
- **Positive controls for the deep arms (amendment 1):**
  - **E11 (TNP-D) FAILED its registered control** on Kaggle (T4, 40,000 steps): median held-out
    Spearman −0.027 / −0.104 / −0.006 over three seeds against oracle kriging 0.635. Under
    `26hp8` its real-data results are **not interpreted**. Before accepting this, the implementation
    was checked for a defect (`scripts/spatial_curve_dl_e11_mask_probe.py`,
    `scripts/spatial_curve_dl_e11_diagnosis.py`): the attention mask, target isolation and context
    path are correct, and the same code learns a random plane (Spearman 1.000 vs oracle 0.979) and a
    smooth 8–15 km field (0.974 vs 0.989). The failure is the model on the registered rough
    short-range field, not the code. **No change to E11 is made; the registered verdict stands.**
  - E10 (ConvGNP): control running at lodging; not yet known.
- **The registered leakage self-test was run** (it is a gate on the machinery, not an estimand) and
  first **failed**; see D-7.

## 2. D-6 — OSM road covariates from Geofabrik extracts, not live Overpass

`road_major_300` and `dist_major_km` were being computed from live Overpass queries at about
20 minutes per city, almost all of it queueing for a public slot (13–16 hours for the frame).
They are instead read from one set of Geofabrik extracts (37 files, 9.05 GB, downloaded
2026-09-11, every file MD5-verified), chosen as the minimum-size set whose polygons cover every
city's padded box (largest uncovered sliver 0.2 per cent of a box).
**Definitions unchanged:** the same highway values and classes, the same segment-midpoint rule,
the same haversine. **One mechanical difference:** a segment enters a city when its midpoint lies
in one of the city's tiles, where Overpass returned whole ways touching a tile. Tiles reach 4.2 km
past every site and the widest buffer is 1 km, so every `road_*` value is unchanged by construction;
only `dist_major_km` beyond the pad can differ, and it was already an upper bound there (7 of 1,141
sites exceed 4 km).
**Cross-check** on the two cities Overpass had finished (London 81 sites, Seoul 115): both
registered covariates identical, Spearman 1.000, median and 95th-percentile absolute difference
0.000. Every city is computed from the extracts, so the frame rests on one snapshot.

## 3. D-7 — the leakage self-test's implementation corrected; its criterion unchanged

**Registered criterion (unchanged):** with merging disabled, a held-out site whose co-located twin
is in the fitting set must be predicted by E3 with standardised error below 0.1.
**First implementation, and why it failed at 2.03:** it took each member instrument's mean over
**its own** days and read the raw hourly files **without the freeze's QC**. Of 47 merged pairs, 22
share fewer than 30 days and 5 share none: they are replaced instruments (one record ends, the next
begins), not concurrent twins. The test therefore measured the seasonal difference between two
records, not co-location.
**Diagnosis before the correction** (`leakage_diagnosis.csv`): on the days both report, twins agree
to a median 0.01 SD, and E3 reproduces the twin's value to 0.011 SD. The leak the guard exists for
is real and large.
**Correction:** the freeze's own `qc_hourly` on each member; both members compared on the days both
report (at least 30); non-concurrent pairs skipped and counted.
**Result: PASSED**, median error 0.080 with the twin against 0.699 without it, on 24 pairs in 9
cities (22 skipped as not concurrent). ⚠ The margin under 0.1 is modest.

## 4. Exploratory analysis X-T — does terrain moderate the curve?

**Exploratory. Never reported as confirmatory.**

**Why.** The frame is chosen by network density; none of its cities is a valley city of the kind
the learning curve is meant to inform. What is meant to transfer is the relation between sensor
density and skill, and basin terrain plausibly changes spatial structure (cold pools, inversions,
drainage flows). Published evidence: in western Montana a terrain-derived accumulation layer
explained 59.5 per cent of the spatial variance of winter mean PM2.5 during inversions, while in
the summer smoke season sensor density alone was often sufficient (Swanson et al. 2026,
doi:10.1016/j.scitotenv.2026.181915).

**Descriptors** (SRTM GL1; `scripts/spatial_curve_terrain.py`, computed before any scoring):
T1 relief, p95 − p5 of elevation over the sites' box padded 5 km; T2 p95 − p5 of elevation at the
sites; T3 mean slope over the padded box; T4 enclosure, the number of 8 compass rays from the median
site that rise at least 200 m above the median site elevation within 15 km.
In the primary frame: relief 37–552 m (median 230), slope 1.7–12.9°, 4 cities with enclosure ≥ 4
and 8 with enclosure 0. ⚠ **Three of the four enclosed cities are Korean**, so terrain and network
are partly aliased.

**Outcomes** per primary city, read from the registered analysis's own outputs
(`scripts/spatial_curve_moderators.py`): O1 reach (E3); O2 crossover k× (E3 over E1); O3 E3 held-out
Spearman at k = 12; O4 paired E3 − E1 at k = 12. Reach and crossover never reached within the tested
range are right-censored and ranked above every finite value.

**Statistic.** Spearman over primary cities; 95 per cent interval by a two-level bootstrap
(countries, then cities within country; 5,000 draws); permutation p (10,000). A test needs at least
8 cities with a defined outcome. **Sixteen tests, uncorrected**: about one will cross p < 0.05 by
chance. With about 18 cities only |ρ| above roughly 0.5 is detectable, so **a null is not evidence
that terrain does not matter**. The same analysis is run on sensitivity frame S-1 beside it.

**How it will be read.** Any apparent moderation is a lead for a registered follow-up with more
basin cities, reported with its interval, its test count and the Korea aliasing beside it.

## 5. Deviations recorded in code before this amendment, restated

D-1 cLHS drawn independently per k (not nested) · D-2 Q2 at a reduced, shared budget · D-3 E6 and
the blocked held-out on random ordering only · D-4 Q3 reach defined on E3, E4 beside it · D-5 E7
scored on held-out sites inside the grey-box grid only, every estimator re-scored on that subset ·
S-1 declared sensitivity frame at 70 per cent coverage, reported beside the registered result. All
are in `scripts/spatial_curve_analysis.py` (`DEVIATIONS`) and are written to every run's summary.

---
**Correction note added 2026-09-25 (local copy only; the lodged OSF text is unchanged).** Recounted
from `leakage_diagnosis.csv` and `analysis/leakage_test.csv`: of **47** merged pairs, **23** share
fewer than 30 days (5 share none), and **24** concurrent pairs in 9 cities are scored. Section 3
above says "22" twice; the correct count is 23, and 24 + 23 = 47. The result is unchanged (median
error 0.080 with the twin, 0.699 without). The deviation text in `spatial_curve_analysis.py`
already carries 23 of 47.
