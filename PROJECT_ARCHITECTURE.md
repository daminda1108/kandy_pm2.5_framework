# Kandy PM2.5 — Architecture

**Last updated:** 2026-08-10. Companion to `PROJECT.md` (state) and `CLAUDE.md` (rules/tasks).
This document is how the model and the evidence pipeline are built: the component maths, the
module map, the execution/data flow, and the testing/reproducibility setup. All paths are
relative to `d:/ProjectCD/kandy_pm25/` unless noted.

**Scope boundary.** This file owns *how it is built* (maths, modules, flow, tests, invariants).
`PROJECT.md` owns *what came out* (stage results, metrics, data inventory, epistemic status).
Where a number appears in both, `PROJECT.md` is authoritative.

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

**The shipped equation is the increment-*split* form, not the one above.** When the hourly
total dips below the daily-resolution background the increment goes negative, and multiplying
a core-high pattern by a negative number renders the core *cleaner* than the rural edge. The
production form structures only accumulation above background and keeps ventilation below it
spatially uniform:

```
PM = B + max(T−B, 0)·P_local + min(T−B, 0)                          (additive_v2, locked)
```

`additive_v3` adds a bounded, mean-zero **pattern floor** `ε(t) = max(0, ε₀ − max(T−B,0))`, so
well-mixed hours retain realistic structure instead of rendering perfectly flat:

```
PM = B + max(max(T−B,0), ε₀)·P_local + min(T−B,0) − max(0, ε₀ − max(T−B,0))
```

Mean-zero ⇒ **T-lock still exact**; `ε₀ ≥ 0` with an accumulation-side `P` ⇒ cannot re-open the
core inversion; `ε₀ = 0` recovers v2 byte-identically. `ε₀` is fitted at Medellín (5.65) and
transferred to Kandy by the relative form (2.573) — a disclosed method transfer, the same
status as the wind prior. **v2 is the locked paper/scorecard tier; v3 is what the app serves.**

**Three field tiers, not interchangeable:** `additive_v2` (locked, 2019–2023, scored) ·
`additive_v3` (ε-floor, shipped) · a **driver-anchored extension tier** for 2024–2026 where the
satellite level anchor no longer reaches, plus a labelled forecast tier in the live payload.

## 2. Components (maths · inputs · code)

Detailed forms are in the preprint Appendix A; source-of-truth code below.

**Temporal anchor `T(t)`** = bias-corrected satellite annual level `L(year)` × a mean-preserving
learned anomaly `g(drivers)` × amplitude-preserving diurnal/seasonal shape corrections.
Gradient-boosted, lag-free (usable without recent observations). Anchored per year to
van Donkelaar; for the analogue cities anchored to 2 elevation-gradient sensors; for Kandy
either FECT/KOALA-anchored (deployed) or **sensorless** (GeoAQ-Zero Track T-a).
Code: `src/stage1_satml/models/predict_T_anchor_v3.py` + `scripts/sharpen_T_diurnal.py` (Kandy);
`src/transfer_validation/t_anchor.py` (multi-city).

**Regional background `B(t)`** carries a **COHERENCE CAP** (2026-08-10, ledger F.43): each
day's `B` is capped at `(1 − F_MIN) × min_hour(T)`, `F_MIN = 0.02`. Local sources emit
continuously, so `B ≤ T` must hold at every hour; a background at or above the total means
`B` is over-estimated, not that emissions stopped. Without it ~25% of hours rendered flat
with a zero local share at the traffic core. **Both tiers need it independently** — the
locked chain (`build_additive_field_v2.build_B_v2`) and the extension tier
(`kandy_driver_tier_build`) construct `B` by different routes, and capping one leaves the
other at 18–28%. The resulting `f ≈ 0.48` is insensitive to `F_MIN` (0.477 → 0.502 across a
fourfold sweep), so the constraint sets it, not the parameter.

**Regional background `B(t)`, construction:** = `(1−f)·L(year)` × daily GEOS-CF shape × origin-conditioned
re-levelling `κ_origin` (air-mass trajectory class). **Daily resolution against an hourly `T`** —
this is the structural seam, see §6. The per-year `f` values (0.20–0.28) are now the **pre-cap
record only** — the effective fraction is set by the coherence cap above at ~0.48, and the
four-constraints-on-three-degrees-of-freedom deadlock was broken by imposing physics rather
than re-deriving a level. Rejected earlier rebuilds retained as the analysis trail: `scripts/kandy_background_{cap,
relevel,v3,v4,v5}.py`; `build_additive_field_v2.py` carries `RELEVEL = False`.
Code: `src/stage1_satml/decomp/build_additive_background.py`,
`scripts/build_additive_field_v2.py`; multi-city `src/transfer_validation/assembly.py`
(`b_hourly`). Extension years: `scripts/kandy_driver_tier_build.py` — the extension `B` must
**inherit the locked monthly `B/T` ratio** (gotcha #61), never a flat annual fraction.

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
90% intervals throughout; empirical coverage reported where ground truth exists. The forecast
tier applies an **OOD widening `k = 1.35`**, derived (not chosen) from the sensorless anchor's
measured 70.7% coverage — direct search and split-conformal agree to 0.000, rounded up so the
shipped interval is never narrower than the measured one (`scripts/kandy_forecast_ood_widening.py`).
**Coverage decomposes into centring and width** — see §6.

**Forecast tier.** Registered as a synthetic year in the client store, so reconstruction runs
through the *identical* field equation rather than a parallel code path. Only the level is
forecast; the field uses the most recent reconstructed year's `(month, local-hour)` `P_local`
climatology, and the background inherits the locked monthly `B/T` ratio. Runner:
`kandy_webapp/live/kandy_live.py` (hourly Action, NASA CFAPI). It logs the rolling analysis
window each hour as a **nowcast**, which is what permanently closes the record→forecast seam:
the CFAPI serves analysis for a 25 h window only and the replay archive ends 2026-01-02, so
nothing can fill that band retrospectively.

## 3. Execution flow

**Per analogue city** (`slug` ∈ xichang, chiangmai, bazhou, chandigarh, kathmandu, taian,
baoji, yichang, medellin, bogota — **N = 10**):

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
build_additive_field_v2 → build_additive_field_v3 → exposure_weighting + health_burden →
paper_figures.py → webapp_export.py (+ QA gate)` (regen order = gotcha #53).
⚠ **v2 and v3 must be rebuilt together** — the exporter reads v3 but derives its anchors from
whichever field it is given, so a partial rebuild desyncs them and fails the QA gate
(gotcha #65/#70). Products in `data/processed/decomp/`.

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

- **Tests:** `scripts/tests/` (pytest, **18 passing**) assert the invariants the paper rests on —
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

- **T-lock** (basin mean ≡ T) — verify Δ<0.05 after any regen. Holds for v2, the split form and
  the v3 ε-floor alike; it is the invariant everything else is reasoned against.
- **N–S DEM flip** (gotcha #56): `build_station_terrain.resample_dem` returns north-up; the
  pipeline assumes south-up → `[::-1]` at each call site.
- **Additive negative under extreme contrast** (gotcha #57): clip **at render**, never in the
  parquet — the exporter derives its anchors from the stored field, so clipping on disk breaks
  `mean(field) == anchor` and fails QA (gotcha #65).
- **Emission surface = spatial proxy, not inventory** (gotcha #59): level from T(t) anchor.
- **Scored headline is wind-independent** — analogue cities use `NO_WINDNINJA=1`.
- **Bounded interpolation** for station sampling (`fill_value=nan`+dropna) — extrapolation
  poisons out-of-box stations.
- **The daily-`B` seam is structural, not a bug to patch.** `B` is daily while `T` is hourly, so
  `B > T` in 28.5% of shipped hours and those hours cannot carry a coherent split. Five
  reformulations were built and rejected; the limitation is surfaced in the interface instead.
  Do not attempt a sixth — the gap is a measurement (one in-basin or upwind monitor).
- **A fix to a derived artefact must live in the code that derives it** (gotcha #70): a
  post-processing correction to `B` was silently regenerated away by the field builder.
- **A build flag must not change the physics** (gotcha #72): a `--years` selector once left too
  few driver rows and silently tripped a fallback that flattened the background shape.
  `_prior_reference()` now loads reference years independently and raises rather than degrade.
- **Descriptor admissibility** (gotcha #73): a city-similarity descriptor may be used only if it
  exists for a target with **no local observations**. Anything derived from the target's own
  outcome leaks, even under leave-one-out.
- **Test the TAIL, not only the mean** (gotcha #76): the extension tier passed annual,
  monthly, seasonal and diurnal checks while producing 0.5 episode-hours a year against ~85.
  Any new tier needs a tail diagnostic before it ships. The correction
  (`scripts/extension_tail_correction.py`) inverts the estimator's own damping, measured by
  leave-one-year-out and applied **by quantile** so hour-ranking survives; it fixes episode
  *frequency*, never episode *timing*.
- **The two uncalibrated constants that shape every hourly map** are the ε-floor (`EPS_FLOOR`)
  and the transport amplitude cap (`0.5` in `build_overlay_predictions.py`). The cap saturates
  on ~4% of hours — concentrated at 06:00 and 19:00 — and on those hours the spatial amplitude
  is set by the constant rather than by meteorology. The defensible published figure is the
  **annual** core/edge contrast (~1.2×), not an hourly maximum.
- **Coverage decomposes** (gotcha #75): before concluding an interval is too narrow, separate
  centring from width. The shipped 72.4% is a one-sided +5.85 µg/m³ area-vs-point offset;
  removing each sensor's own median restores 91.5%.


---

## Manuscript build (2026-08-14)

The paper in `kandy_pm25/docs/paper/` is assembled from parts, never edited as a whole.

```
python scripts/paper2026_table1.py                 # Table 1 from artifacts
python docs/paper/assemble_manuscript.py           # sections -> manuscript_kandy.md
node docs/paper/build_report.js --src manuscript_kandy.md --style _preprint_style.tex
```

**`manuscript_kandy.md` is a build product. Edit `draft_s*.md`, `abstract.md` and
`references.bib`.** The assembler strips drafting notes, prepends the front matter and abstract,
splices Table 1, resolves citations and figures, and appends the bibliography div.

Three invariants it enforces, each closing a trap this project has hit:

- **Figures are numbered by order of first appearance** from `{{fig:tag}}` tokens, so inserting
  or dropping a figure can never leave a stale "Figure 9" in the prose. This retires gotcha #58.
- **Citations are checked in both directions** every run: keys found, bibliography size, unknown
  keys, uncited entries. Drift fails loudly.
- **Unicode is substituted for TeX** at assembly. Latin Modern has no superscript-minus glyph,
  so `µg m⁻³` builds silently as `g m` with the exponent dropped; the drafts stay readable and
  the substitution happens in the build.

Every figure and Table 1 regenerate from artifacts listed in `docs/paper/NUMBERS_LEDGER.md`, so
no number in the paper is typed by hand.

Two build gotchas worth keeping: `plt.colorbar(ax=ax)` reflows the host axes and silently breaks
hardcoded coordinates on a schematic; and pandoc renders markdown tables as `longtable`, which
has no float placement and splits across a page break, so Table 1 is emitted as a LaTeX float.
