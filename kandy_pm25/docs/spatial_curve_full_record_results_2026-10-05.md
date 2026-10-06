# Test B results — the spatial learning curve on full station records (OSF `fu59b`), scored once 2026-10-05

Registration `docs/prereg_spatial_curve_full_record_2026-10-04.md` (lodged 2026-10-04 18:23 UTC, project `4xvpw`),
extending `rqn4y` (+ `26hp8`, `4whsc`, `4qs9c`). Code frozen at `1e5f712` (`docs/curve_fullrecord_freeze_manifest.json`).
Outputs `modular/spatial_curve_full/` (frames, `analysis/`, `analysis_s70/`, `F1_frame.json`, `F3_tropical_arm.json`).
Deviations `modular/spatial_curve_full/DEVIATIONS.md` (B-1 and one implementation note, both logged before the summary).
Ledger F.123.

## Data and checks
- Records: all 1,974 candidate locations, full archive record (2.20 M daily objects), 0 unparsable; 1,972 with PM2.5.
- Freeze rule unchanged (75 %, S-1 at 70 %). Dry run on the registered one-year records reproduced the registered
  frames byte for byte.
- Registered gates on the new frame: leakage self-test **passed** (0.029 with the twin, 0.43 without; threshold
  0.1); positive control **passed** (E3 0.540 vs oracle 0.554 at k = 35).
- Predictors for every frame site by the registered functions (GEE, Geofabrik roads, benchmark grid); no missing
  covariate. Nine new extracts (current Geofabrik release, MD5-verified) for clusters new to the frame.
- Scored E0–E7 on Kaggle CPU (5 kernels, 20 shards, every shard exit 0): 48 registered-frame and 50 S-1 cities.
  E8–E11 not re-run, as registered; the summary merged no deep-arm predictions.
- **Deviation B-1:** Medellín's best window differs between the two frames on full records, so E7 (grey-box) is
  computed per frame over that frame's own window.

## F1 — the frame (reported first)
| | full records | registered one-year |
|---|---|---|
| primary cities | **23** (960 sites, 9 countries) | 18 (745 sites, 7 countries) |
| primary by band | 16 temperate, 5 subtropical, **1 deep tropical (Bangkok, 65 sites)**, 1 tropical (India) | 13, 4, 0, 1 |
| secondary | 21 | 15 |
| band arm (\|lat\| < 23.5, ≥ 12 sites) | **8** | 6 |
S-1 (70 %): 23 primary (982 sites), 22 secondary, band arm 9.
**The record window was a binding constraint:** five more primary cities, and the first deep-tropical one.

## F2 — X1–X7 on the full-record frame (registered rules)
| | expectation stated | full records | S-1 (70 %) | registered `rqn4y` |
|---|---|---|---|---|
| X1 IDW/E4 rise monotonically | refuted | **refuted** | refuted | refuted |
| X2 crossover k× ≤ 35 in ≥ half of cities | held | **held**: 15/23 (65 %) | not held (48 %) | held (61 %) |
| X3 ridge LUR saturates by k ≤ 12, within δ of raster | held | **held** (k* = 3, −0.04) | held | held |
| X4 no curve above the within-cell ceiling | held | **REFUTED** (see below) | refuted | held |
| X5 cLHS ≈ random | held | **held** (0.00, tie as before) | held | held |
| X6 per-day curves below static, for every estimator | refuted | **refuted** | refuted | refuted |
| X7 reach < 5 km | held | **held** (median 1.0 km) | held (0.5 km) | held |
Detection limit at 9 primary countries: 0.24 (registered 0.28 at 7).

**X4, the one change.** Three primary cities now have a computable within-cell ceiling (≥ 8 sites sharing 1 km
cells). In two of them the ceiling is **negative**: London (−0.28; an estimator reaches +0.02) and Bangkok
(−0.57; E2 reaches +0.40 at k = 35). Sites sharing a 1 km cell there predict each other worse than chance while the
estimators still recover the city-scale ranking. By the registered rule X4 is refuted; the reading is that the
within-cell ceiling is not a ceiling where cell-mates disagree, not that the estimators found sub-kilometre
structure. The third city (Korea, cluster 1, ceiling 0.22) is not exceeded beyond the detection limit.

**Crossovers (per city, frozen rule):** 15 of 23 primary cities cross the raster by k = 35, **8 of them at 3
stations**, 3 at 5, 1 at 8, 3 at 25–35; 8 never cross (registered: 11/18, 5 at 3, 7 never). Bangkok crosses at
3 stations (E5); the Indian tropical city at 5 (E3).

## F3 — tropical arm (exploratory, declared)
Eight band-arm cities in 7 countries; own detection limit **0.28**; compared with the envelope of E3 curves over the
21 non-tropical primary cities (`scripts/spatial_curve_fullrecord_f3.py`).
- No tropical city lies **above** the temperate envelope at any k.
- Inside at every scored k: India-23, Brazil, Hong Kong, Taiwan. Bangkok inside at 5 of 7 k (below at 2), Medellín
  at 1 of 2, India-107 below at its one k; Guangdong not scorable at any k.
- Median gap to the envelope's median: −0.29 to +0.37, around zero.
- Station-based estimators (E3 or E5) beat the raster at k = 3 in 7 of the 7 scorable cities (on the median curve).
- S-1: same picture (Bangkok inside at all 7 k).

## What it means (Section 5 of the registration)
- **Tropical cities now qualify**, so the curve speaks to cities like Kandy for the first time. Within a detection
  limit of 0.28, their curves are indistinguishable from the temperate ones: no evidence that tropical cities need
  more or fewer stations, and in most a few stations beat the satellite raster.
- **Every registered verdict repeats except X4.** Cities still split (15 cross, 8 never); reach stays about 1 km;
  siting method still makes no detectable difference.
- **"No station count follows" is revisited:** for a Kandy map, three to five reference stations reach the
  crossover in most cities, tropical ones included. But three of the eight tropical-arm cities sit partly or wholly below the envelope, and
  the arm has 8 cities with a 0.28 detection limit. That supports "a handful of stations is the right order of
  magnitude", not a specific number.
