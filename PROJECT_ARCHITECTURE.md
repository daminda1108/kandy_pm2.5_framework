# Kandy PM2.5 — Architecture

**Last updated:** 2026-07-02. Companion to `PROJECT.md` (state) and `CLAUDE.md` (rules/tasks).
This document is how the model and the evidence pipeline are built: the component maths, the
module map, the execution/data flow, and the testing/reproducibility setup. All paths are
relative to `d:/ProjectCD/kandy_pm25/` unless noted.

---

## 1. The model in one equation

Hourly PM2.5 on a 1 km grid is an additive background-and-increment field (Lenschow 2001):

```
PM(x,y,t) = B(t) + [ T(t) − B(t) ] · P_local(x,y,t)
```

- `T(t)` — basin-mean concentration (the temporal anchor; carries the level and its evolution).
- `B(t)` — regional/transboundary background (spatially near-uniform).
- `P_local(x,y,t)` — dimensionless local pattern, **normalised to unit spatial mean**.

**T-lock invariant.** Because `P_local` has unit mean, the basin average of the field returns
`T(t)` exactly. The spatial pattern redistributes concentration within the valley without
changing the total the anchor specifies. This is what lets the level and the pattern be
reasoned about — and validated — separately, and it is the basis of the sensitivity result
(area mean invariant to the local fraction f).

**Additive, not multiplicative.** `T·P` would modulate the regional background by the local
pattern (unphysical) and inflate the level at floor/core-clustered monitors (ablation: +26%).
The additive form adds `B` uniformly and structures only the increment.

## 2. Components (maths · inputs · code)

Detailed forms are in the preprint Appendix A; source-of-truth code below.

**Temporal anchor `T(t)`** = bias-corrected satellite annual level `L(year)` × a mean-preserving
learned anomaly `g(drivers)` × amplitude-preserving diurnal/seasonal shape corrections.
Gradient-boosted, lag-free (usable without recent observations). Anchored per year to
van Donkelaar; for the analogue cities anchored to 2 elevation-gradient sensors; for Kandy
either FECT/KOALA-anchored (deployed) or **sensorless** (GeoAQ-Zero Track T-a).
Code: `src/stage1_satml/models/predict_T_anchor_v3.py` + `scripts/sharpen_T_diurnal.py` (Kandy);
`src/transfer_validation/t_anchor.py` (multi-city).

**Regional background `B(t)`** = `(1−f)·L(year)` × daily GEOS-CF shape × origin-conditioned
re-levelling `κ_origin` (air-mass trajectory class). Local fraction `f≈0.25` for Kandy
(source apportionment; SBI posterior 0.18 [0.10,0.27]). Code: `src/stage1_satml/decomp/
build_additive_background.py`, `scripts/build_additive_field_v2.py`; multi-city
`src/transfer_validation/assembly.py` (`b_hourly`).

**Local pattern** `P_local = norm( S_emit · M · A_transport · e(t) )`:
- `S_emit` — bottom-up **traffic-centrality** surface (OSM road graph; betweenness = through-
  traffic, closeness = trip generation; congestion EF). A **proxy for the local spatial
  pattern, not a source inventory** — the level is carried by `T(t)` (all sources). Code:
  `scripts/build_xichang_traffic_emission.py` (multi-city), `src/stage1_satml/decomp/
  build_traffic_emission.py` (Kandy).
- `M` — terrain confinement `1 + κ·w(BLH)·c(x,y)` (relief-based confinement index c, BLH-
  modulated). κ bounded prior (unidentified). Code: `build_m_confinement.py`,
  `build_xichang_core_terrain.py`.
- `A_transport` — advection/dispersion along **WindNinja** mass-consistent diagnostic winds
  (channelling, blocking, day/night up-valley/drainage reversal). Enters the 4factor scenario;
  the scored additive headline uses `S_emit·M` only (so it is wind-independent — analogue
  cities can run `NO_WINDNINJA=1`). Code: `src/stage1_satml/decomp/terrain_transport.py`,
  `scripts/build_xichang_windninja.py`.
- `e(t)` — bimodal emission-timing profile from the per-city source mix (`emix`). Code:
  `src/stage1_satml/decomp/emission_profile.py`.

**Uncertainty.** Pattern interval = conformal calibration of the anchor quantiles propagated
through the increment; background contributes a bracket over rural-floor/origin assumptions.
90% intervals throughout; empirical coverage reported where ground truth exists.

## 3. Execution flow

**Per analogue city** (`slug` ∈ xichang, chiangmai, bazhou, chandigarh, kathmandu, taian,
baoji, yichang, medellin):

```
data/external/{slug}/dem/*.tif
      │  build_xichang_core_terrain.py --city slug      → {slug}_terrain_core.npz  (delta_z, svf; N–S flip, gotcha #56)
      │  build_xichang_traffic_emission.py --city slug  → S_traffic_{slug}.npz     (centrality × EF)
      │  build_xichang_windninja.py --city slug         → {slug}_windninja_library.npz  (optional; NO_WINDNINJA skips)
      ▼
NO_WINDNINJA=1 xichang_prod.py --city slug   (stages: static → T(t) → B(t) → field)
      │   drivers via src/transfer_validation/drivers.py (per-city GEE CSVs, else station-mean PROXY)
      │   2-sensor elevation-gradient anchors; VanD tile (Asia or SA); f from city_config
      ▼
data/processed/decomp_{slug}/{slug}_decomp_predictions_{year}_{4factor,additive_v2}.parquet
      ▼
city_validation_scorecard.py --cities ...   → results/figures/multicity/validation_scorecard.{png,csv}
xichang_paper_figures.py --city slug         → results/figures/{slug}_paper_figures_v2/  (F1–F13)
```

**Kandy production** (the deployed model): `predict_T_anchor_v3 → sharpen_T_diurnal →
build_decomp_map → build_overlay_predictions (4factor) → build_spatial_uq →
build_additive_field(_v2) → exposure_weighting + health_burden → paper_figures.py`
(regen order = gotcha #53). Products in `data/processed/decomp/`.

**Evidence artefacts:** `sensitivity_analysis.py` (S1), `ablation_scorecard.py` (S2; ABLATE
hook in `xichang_prod.build_field`, non-destructive suffixed output), `independent_visibility.py`
(S3), `spatial_skill_law.py` (S4), `w2_transboundary_figure.py`. One-command per-city rebuild:
`regenerate_city.py`.

## 4. Code organisation

```
kandy_pm25/
├── src/                     (git-tracked)
│   ├── stage1_satml/        Stage A temporal anchor + the Kandy decomp modules
│   │   ├── models/          predict_T_anchor_v3, GBM boosters
│   │   ├── features/        vandonkelaar.py (level anchor), dataset builders
│   │   └── decomp/          build_additive_*, build_m_confinement, build_traffic_emission,
│   │                        emission_profile, terrain_transport, exposure_weighting,
│   │                        health_burden, paper_figures, paperfig, pubfig
│   ├── transfer_validation/ (git-tracked) the validation harness:
│   │                        citypack, drivers, t_anchor, assembly, anchors, vand, score
│   ├── stage2_transfer/     supporting cross-continental PINN (historical)
│   └── stage3_pinn/         ConvCNP + city_config (Stage B, historical)
├── scripts/                 (mostly gitignored; EVIDENCE CHAIN tracked as of 2026-07-02)
│   ├── city_config.py       CITIES dict (per-city bbox/utm/dem/f/emix) + citypack()/cfg()/e_profile()
│   ├── xichang_prod.py      multi-city static→T→B→field (the engine)
│   ├── xichang_twin_figures / xichang_paper_figures / city_validation_scorecard
│   ├── build_xichang_{core_terrain,traffic_emission,windninja}, build_station_terrain
│   ├── sensitivity_analysis / ablation_scorecard / independent_visibility / spatial_skill_law
│   ├── w2_transboundary_figure / regenerate_city
│   └── tests/               pytest invariant suite (conftest + test_evidence_pipeline)
├── config.py                (git-tracked) constants
├── data/  results/  docs/   (gitignored)
└── kandy_pm25_release/      separate public repo (kandymodel/ package) — parent-gitignored
```

**Two registries (note):** `src/transfer_validation/citypack.py` has a frozen `REGISTRY`
(prereg cities); the multi-city production/scorecard path uses `scripts/city_config.py`'s
`citypack(slug)` built from the `CITIES` dict. Adding a city = a `CITIES` entry + a
`{slug}_perstation_*` parquet (variant in `_PARQUET_VARIANTS`) + a DEM + drivers (GEE CSVs or
proxy) + the build chain in §3.

## 5. Testing & reproducibility

- **Tests:** `scripts/tests/` (pytest, 10 passing) assert the invariants the paper rests on —
  T-lock basin mean; additive-vs-multiplicative level; unit-mean normalisation; f-invariance +
  exposure linearity; split-conformal coverage; GEMM monotonicity/bounds; emission-timing
  shape; `city_config` integrity. Run: `python -m pytest scripts/tests -q`.
- **Reproducibility:** model inputs are public; `regenerate_city.py` rebuilds any configured
  city terrain→traffic→(winds)→prod→figures→score. Kandy figures reproduce from the release
  repo's `regenerate_all.py`. Repro guide: `docs/REPRODUCE.md`.
- **Preprint build:** `docs/reports/build_report.js --src preprint_kandy.md --style
  _preprint_style.tex` (pandoc→XeLaTeX). Figure callouts are hardcoded numbers — pandoc `\ref`
  does not resolve here (gotcha #58) — re-map on any figure add/remove.

## 6. Key invariants & gotchas (architecture-critical)

- **T-lock** (basin mean ≡ T) — verify Δ<0.05 after any regen.
- **N–S DEM flip** (gotcha #56): `build_station_terrain.resample_dem` returns north-up; the
  pipeline assumes south-up → `[::-1]` at each call site.
- **Additive negative under extreme contrast** (gotcha #57): clip field at 0; disclosed.
- **Emission surface = spatial proxy, not inventory** (gotcha #59): level from T(t) anchor.
- **Scored headline is wind-independent** — analogue cities use `NO_WINDNINJA=1`.
- **Bounded interpolation** for station sampling (`fill_value=nan`+dropna) — extrapolation
  poisons out-of-box stations.
