> ⚠ **SUPERSEDED 2026-08-18 by `prereg_modular_validation_v2_2026-08-18.md`.** The frame here is CNEMC-only; the PVAF OpenAQ census supplies 191 further ladder-eligible clusters including the **17 deep-tropical cities this frame has none of**. The run launched under this document is retained as a **pilot** and must not be reported as the registered result.

# Pre-registration — stratified validation of the modular decomposition

**Date:** 2026-08-18 · Registered **before** any city was scored.
Frame: `data/processed/modular/panel_census.csv` (199 CNEMC cities, built before this doc).

---

## 0. Two corrections to the premise, established by inspection

**The OpenAQ archive on disk is THREE cities**, not a vast one: Chiang Mai, Kathmandu, Medellin
(`data/external/openaq/{raw,processed,discovery}`). The *access* is real and cheap — the S3
archive is public and unsigned (gotcha #35) — but a stratified global ingest is an unstarted
multi-day task (download, QC, per-device calibration per gotcha #37), not something already in
hand. Any claim of "validated across global regimes" is currently unsupported.

**The CNEMC panel cannot bracket Kandy, and now this is quantified.** Of 199 cities:

| | |
|---|---|
| latitude range | **20.0 to 47.7 N** — **zero** cities south of 20 N (Kandy: 7.3 N) |
| PM2.5 mean | 8.5 to 60.7, median 32 (Kandy: ~19-21, i.e. the **low** stratum) |
| cities with >= 10 stations | **39** |
| cities with >= 12 stations | 20 |

Cross-tabulated at >= 10 stations (relief x pollution level):

| relief \ level | low | mid | high |
|---|---:|---:|---:|
| flat (<20 m) | **0** | 4 | 3 |
| moderate (20-75 m) | 3 | 10 | 7 |
| confined (>75 m) | 2 | 5 | 5 |

**The flat/low cell is empty and the whole low column holds 5 cities.** A fully-crossed 3x3
design is therefore not supportable, and the Kandy-relevant stratum is the thinnest one in the
frame. This is the standing "the panel does not bracket Kandy" critique, measured.

---

## 1. What is therefore being claimed

**Scope, stated before results:** transfer of the modular decomposition across **terrain and
pollution regimes within a mid-latitude, mid-to-high-pollution, single-country regulatory
network**, plus three tropical/Southern-Hemisphere cities from OpenAQ. It is **not** a global
validation and **not** a demonstration that the model brackets Kandy.

## 2. Design

**Frame.** All panel cities with `n_stations >= 10` (N = 39), plus Chiang Mai, Kathmandu and
Medellin from OpenAQ (N = 3). **Total N = 42.**

**Strata** (declared now, not after): `relief` = elev_p10_90 in {<20, 20-75, >75} m;
`level` = pm25_mean in {<25, 25-40, >40} ug/m3. Reported per cell; cells with < 3 cities are
reported as **not estimable**, never pooled away.

**The ladder**, per city, with every rung fitted only on its own admissible stations and all
rungs scored on stations no rung ever saw:

| rung | information | estimator |
|---|---|---|
| `Bud0` | ERA5 drivers + static covariates, **no local observation of this city** | **leave-one-city-out gradient boosting** — a genuine sensorless ML level |
| `Bud1` | + 2 local stations | affine correction |
| `Bud2` | + 6 local stations | affine correction |
| `Bud3` | + outer-ring stations as a background proxy | linear in (prior, background) |

Richer rungs enter via cross-validated shrinkage, folds grouped by day.

## 3. Registered gates

- **V1 — P2 monotonicity.** Held-out RMSE must not increase along the ladder in
  **>= 90%** of cities. Reported per city; violations named, not averaged away.
- **V2 — Bud0 is genuinely sensorless.** The LOCO fold must exclude every station of the target
  city. Asserted in code, not by inspection.
- **V3 — per-stratum reporting.** No result is reported pooled without also being reported per
  cell. (Following the F.24 error: never average a skill measure across strata.)
- **V4 — diminishing returns.** Pre-registered expectation from F.48: the `Bud1 -> Bud2` step
  buys less than the `Bud0 -> Bud1` step in a majority of cities. Stated in advance so a
  confirmation cannot be presented as a discovery.

## 4. Published priors

- P2 will hold in nearly all cities **by construction** (shrinkage includes w = 0); the
  informative quantity is the WEIGHT, not whether P2 passes.
- `Bud0 -> Bud1` will be the largest step in most cities.
- The background rung will be large where the outer ring is genuinely cleaner and near-zero in
  flat cities.
- **Expect worse absolute skill in the high-pollution stratum** (Kathmandu's smoke regime
  gained little at every rung in F.48).

## 5. Stopping rule

Failed gates are reported as failures. The design is not re-cut after seeing results; if the
strata prove unusable that is the finding.
