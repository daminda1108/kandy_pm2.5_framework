# Kandy PM2.5 — Satellite-ML and Cross-City Spatial Estimation

Undergraduate thesis project — Daminda Alahakoon, Department of Environmental Sciences, University of Peradeniya.

**Last updated: 2026-08-10.** Canonical state is [`CLAUDE.md`](CLAUDE.md); this README mirrors it. Build detail is in [`PROJECT_ARCHITECTURE.md`](PROJECT_ARCHITECTURE.md).

---

## Overview

Kandy, Sri Lanka has no continuous PM2.5 monitoring stations. This repository develops a two-stage framework for spatiotemporally resolved PM2.5 estimation over Kandy at the intrinsic resolution of the available driving data — 1 km, hourly — with calibrated per-pixel uncertainty.

Stage A produces a temporal anchor for Kandy from satellite reanalysis and machine learning, calibrated against the only published Kandy in-situ campaign (Senarathna et al. 2024). The **deployable spatial product** is a physically-structured *additive background-plus-increment decomposition* that places the Stage A temporal anchor into a 1 km hourly field using measured satellite emission patterns, terrain confinement, and diagnostic terrain winds, separating a regional and transboundary background from the locally-generated, locally-actionable increment. An earlier exploratory route — a Convolutional Neural Process trained zero-shot across three source cities (Stage B) — is retained as the cross-city experiment that motivated the decomposition.

The **local fraction `f`** governing that separation is now set by a physical constraint rather than a literature prior. Local sources emit continuously, so the local increment at an emitting location is strictly positive at every hour — rain changes removal, not emission — and therefore the background can never equal or exceed the total. Imposing that (capping each day's background at the day's minimum total) gives **`f ≈ 0.48`**: roughly half the annual mean is locally generated. The value is set by the constraint, not by a tuning parameter — sweeping the one free parameter across a fourfold range moves `f` only from 0.477 to 0.502 — and it agrees with three independent lines of evidence (a coherence floor of ≥0.41 from the anchor alone, a hierarchical fit with Kandy held out at 0.392, and a national-network instrument at 0.446). The conventional source-apportionment prior of ~0.25, used in earlier versions of this work, sat below its own coherence floor in nine months of twelve and is retired. The field is *T-locked*, so the level, exposure and health burden are arithmetically unchanged by this; what changes is the attribution.

What the framework does *not* do, in its current form: it does not replace physical monitoring; it does not provide point-level accuracy at sub-1 km; and it does not chemically apportion sources. Outputs are hourly 1 km PM2.5 fields with calibrated uncertainty and a population-exposure / health-burden layer, plus a separately-labelled forecast tier shipped as a **demonstration**. Strict spatial validation requires field deployment at Kandy with elevation-spanning hourly sensors, identified as the binding next step.

---

## Pipeline

```
   Satellite reanalysis + ML        Van Donkelaar 1 km        ERA5 winds / BLH, SRTM
   (GEOS-CF, CAMS, ERA5, MAIAC)      annual PM2.5 surface      terrain, OSM road network
              │                             │                          │
              v                             v                          v
   ┌──────────────────────┐     ┌──────────────────────┐   ┌───────────────────────────┐
   │ Stage A anchor  T(t) │     │ B(t)  regional /     │   │ P_local(x,y,t)  unit-mean │
   │ lag-free GBM +       │     │ transboundary        │   │ S_emit · M · A_transport  │
   │ conformal UQ +       │     │ background (rural    │   │ (traffic source, terrain  │
   │ diurnal sharpening   │     │ floor × seasonal)    │   │ confinement, WindNinja)   │
   └──────────┬───────────┘     └──────────┬───────────┘   └─────────────┬─────────────┘
              └─────────────────┬──────────┴─────────────────────────────┘
                                v
              ┌──────────────────────────────────────────────────────┐
              │  Additive decomposition  (PRODUCTION spatial product) │
              │  PM(x,y,t) = B(t) + [ T(t) − B(t) ] · P_local(x,y,t)  │
              │  → Kandy 1 km hourly PM2.5 field + 90% PI + per-pixel │
              │    σ  →  population-weighted exposure + health burden │
              └──────────────────────────────────────────────────────┘

   Exploratory predecessor (Stage B): a cross-city ConvCNP residual learner trained on
   N = 3 source cities and applied zero-shot at Kandy. Technically defensible but
   spatially over-smoothed; retained as the experiment that motivated the decomposition.
```

Native resolution is 1 km hourly. The 0.25° driving reanalyses (GEOS-CF, ERA5) have no spatial structure below ~25 km; resolving below 1 km from these inputs is unsupported. The level is anchored to the per-year Van Donkelaar **area** mean (β ≡ 1); the KOALA 24.5 µg/m³ figure is a 2019 valley-floor / populated-core point, not the basin-area mean, and no longer scales the level.

---

## Methodological Evolution

The current architecture is the result of several explicit pivots, each driven by a measured failure of the prior approach. They are summarised here so the design choices are legible; the full record lives in `docs/REDESIGN_2026-05-08.md`, `docs/AUDIT_2026-05-08.md`, and the session log at `memory/SESLOG.md`.

| Date | Pivot | Reason |
|---|---|---|
| 2026-03 | QSS spatial PINN → **TD-PDE temporal PINN** | QSS lost spatial ordering of stations under physics pressure (λ_pde ≥ 0.38 collapsed the field). TD-PDE with the v7 curriculum (pure-data Phase 1 → ramped λ_pde to 0.15 max) recovered ordering. The TD-PDE result was later moved to a supporting experiment, since spatial PINN work was cut entirely and the temporal anchor was solved more reliably by gradient-boosted trees. |
| 2026-05-04 | SharedTerrainAnsatz → **ConvCNP residual learner** for spatial | All six Whiteman-ansatz parameters hit bound constraints across the source-city set; the rigid functional form could not represent valley physics in different regimes. ConvCNP residual learning was adopted; the ansatz failure is retained as a documented diagnostic. |
| 2026-05-17 | CAMS as label → **CAMS as feature** (Stage A v2 reframe) | v1 used KOALA both to calibrate CAMS labels (×0.598) and to validate the result (r = 0.515) — circular by construction. v2 promotes FECT-calibrated PurpleAir to labels and demotes CAMS / GEOS-CF to features; daily LOMO R² moved from 0.631 to 0.689. |
| 2026-05-20 | Daily v2 → **hourly v3** | Hourly residual target with per-sensor offsets enables diurnal-cycle reproduction (against Senarathna 2024, r = +0.865). After a 39-feature Tier-1 rebuild failed to lift pooled R² above 0.581, the R² ≥ 0.60 target was closed as an honest near-miss; sensor expansion was identified as the binding constraint, not architecture. |
| 2026-05 | N = 5 → **N = 3** source cities + **PVAF v1** | Bogotá and Mexico City were dropped from Stage B cross-validation as different atmospheric regimes (Mexico City GEOS-CF over-predicts by a factor of ~4.6). PVAF v1 was launched to select additional highland-valley analogues by physics-similarity scoring before Kandy production maps are regenerated. |
| 2026-05-22 | Gaussian NLL → **Student-t(df = 5) + split-conformal** for UQ | ConvCNP v13 satisfied point-skill targets but Gaussian likelihood let σ collapse (cov90 fell to 0.54–0.73). v14 switched to Student-t for robust point estimation; per-(city × hour-of-day) Mondrian conformal calibration restored cov90 ∈ [0.85, 0.95] across all source cities without retraining. |
| 2026-05–06 | ConvCNP zero-shot map → **additive decomposition production model** | The N = 3 zero-shot spatial map was technically defensible but spatially over-smoothed (only Kathmandu is a true highland-valley analogue), and a Sim2Real fine-tune on the two FECT sensors memorised sensor coordinates rather than basin physics. The deployable spatial product was rebuilt as a physically-structured additive decomposition (Van Donkelaar-anchored emission pattern + congestion-weighted traffic source + terrain confinement + WindNinja diagnostic winds); the ConvCNP work is retained as the exploratory predecessor. |

---

## Stage A — Satellite-ML Temporal Anchor

Two parallel tracks are maintained: a daily anchor (v1) and an hourly RECAP residual learner (v3). The daily track stays in the repository as a 22-year chronology for Kandy; the hourly track is the operational temporal product.

**v1 — daily, 2003–2025 (8,279 days, 44 features).**

| Metric | Value |
|---|---|
| Held-out LOMO R² | 0.631 |
| RMSE | 4.82 µg/m³ |
| 90 % PI coverage | 89.4 % |
| KOALA 2019 monthly r | 0.515 (n = 12) |
| KOALA 2019 bias | +0.09 µg/m³ |

Bias correction is a flat annual scalar ×0.5984 = 24.5225 / 40.98 (KOALA annual / CAMS 2019 raw). Monthly correction was tested and rejected (R² dropped to 0.507–0.519); MERRA-2 blending was tested and rejected (r(CAMS, MERRA-2) = 0.177 over Kandy).

Top SHAP drivers: wind_speed (3.594), pm25_prev_month_mean (0.809), rwp (0.641), vvc (0.577), aod_blh_ratio (0.555).

**v3 — hourly residual target (`pm25 − c_prior_anchored`), 2018–2026 (19,686 sensor-hours, 33–39 features).**

| Metric | v3.0 (33 feat) | v3-extended (39 feat) |
|---|---|---|
| Pooled hourly LOMO RMSE | 7.76 µg/m³ | 7.78 µg/m³ |
| Pooled hourly LOMO R² | 0.583 | 0.581 |
| 90 % PI coverage | 0.865 | 0.867 |
| 90 % PI width | 22.3 µg/m³ | — |
| CRPS | 2.9 | — |

Production model is a linear blend of LightGBM + CatBoost + XGBoost-quantile wrapped in CV+ Mondrian conformal calibration. Per-sensor offsets `b_FECT` (Akurana −9.105, Hantana −13.749 µg/m³) anchor the residual target to zero mean by construction.

Against Senarathna 2024 diurnal pattern: r = +0.865 (morning peak 07 LT match, evening peak 18–19 LT with 1 h drift). Embassy Colombo out-of-domain coverage (2019–2025): cov90 = 0.861, RMSE = 9.51, R² = 0.452 — point skill degrades out-of-domain but the predictive interval transfers honestly.

For the production decomposition the Stage A anchor is regenerated as a **lag-free** gradient-boosted series (LightGBM-only) on exogenous drivers, re-anchored per year to the bias-corrected Van Donkelaar level and amplitude-sharpened to the observed FECT diurnal and seasonal swing. Lag-free is used because 2024 FECT coverage is too sparse for reliable autoregression.

---

## Production Spatial Model — Additive Background + Increment Decomposition

The deployable Kandy spatial product. It replaces the held ConvCNP zero-shot map and is the model carried into the supervisor-facing reporting and the health-burden layer. The concentration at position $(x,y)$ and hour $t$ is written as a regional background plus a locally shaped increment (Lenschow apportionment):

```
PM(x, y, t) = B(t) + [ T(t) − B(t) ] · P_local(x, y, t)
```

- **B(t)** — regional and transboundary background, horizontally uniform per hour. Built as a rural Van Donkelaar floor (10th percentile of a ±0.45° box) scaled by the GEOS-CF daily seasonal shape; **daily resolution, diurnally flat** — a known limitation, see below. It is levelled by a local fraction `f` set per year in the range 0.20–0.28, originally bracketed [15 %, < 50 %] from source-apportionment literature (World Bank 2022; Seneviratne 2017) and **not** satellite-tuned. That prior is now superseded as an estimate — see [Local/regional partition](#localregional-partition--an-open-quantity).
- **T(t)** — the Stage A v3 lag-free temporal anchor, conformal-wrapped and amplitude-sharpened (above).
- **P_local** — unit-mean local pattern, the normalised product of emission structure (Van Donkelaar surface + a bottom-up congestion-weighted traffic source: network betweenness/closeness × COPERT emission factors), boundary-layer-scaled terrain confinement $M = 1 + \kappa\,w(\mathrm{BLH})\,c(x,y)$, and a transport overlay $A_\text{transport}$ on **WindNinja** mass-consistent diagnostic winds (channelling + day-anabatic / night-katabatic drainage) with a bimodal diurnal emission-timing profile. Because $P_\text{local}$ has unit basin mean, the basin-average concentration is preserved exactly at $T(t)$ and only the spatial *arrangement* of the local quarter is structured. $A_\text{transport}$ is shipped as a physically-motivated **scenario**, not a validated layer.

**Level anchor (area-not-floor).** The basin level is set directly to the per-year Van Donkelaar area mean ($\beta \equiv 1$); KOALA 24.5 µg/m³ is a 2019 valley-**floor / populated-core** point, not the basin-area mean, and is no longer used to scale the level. Two independent satellite area products agree below it (VanD ≈ 19.7, GHAP ≈ 17.0 for 2019), and the confinement field reproduces KOALA at the NIFS pixel unforced.

**Results (2019–2023).** Basin annual mean ≈ 21 µg/m³ (per year 19.7 / 19.0 / 17.0 / 18.7 / 20.9; 2021 COVID/fuel-crisis low). Seasonal MAM > DJF > SON ≈ JJA (monsoon washout); diurnal bimodal with morning and evening traffic peaks and a genuine deep-night low. Senarathna 2019 diurnal r = 0.75, monthly r = 0.83 (preserved through the additive re-anchor). Every cell and hour carries a calibrated 90 % prediction interval plus a per-pixel spatial-uncertainty layer.

**Independent corroboration (not validation).** GHAP (Wei et al., 1 km, methodologically distinct from Van Donkelaar): seasonal r = +0.909; basin level within ≈ 6 %; fine-spatial r = +0.13 (both products smooth at that scale); inter-annual ≈ 0 (trend low-confidence). TROPOMI NO₂ corroborates emission placement (core > edge). The model independently reconstructs documented Kandy haze episodes (Nov 2019, Dec 2022) at the right level by the right mechanism.

**Exposure and health (2023, shipped tier).** Population clusters in the higher-loading core, so the area mean understates exposure: area 21.0 → residential 21.5 → **dynamic population-weighted 22.6** → populated-core 22.0. Health statements use the dynamic population-weighted figure. A GEMM concentration–response layer gives **427 attributable deaths/yr [235–625]**, attributable fraction 18.0 %, of which 295 are avoidable against the WHO guideline. All four exposure tiers sit *below* the 2019 KOALA point (24.5 µg/m³), which is a valley-floor measurement, not an area mean.

**Known limitations.** The fine-scale spatial *magnitude* of the core enhancement is imposed from physics and not independently measured — no public monitoring network anywhere samples the valley-floor-to-ridge gradient (a several-hundred-valley screen confirmed floor-clustering is universal), and **five independent tests** now establish that it cannot be learned from public covariates either (learned-pattern null; dynamic-transport null; two emission-proxy nulls; and an AlphaEarth Earth-representation-embedding null replicated in three valleys). The ceiling is information-limited, not model-limited. The confinement strength $\kappa$, the local fraction, the traffic emission scaling, and the transport amplitude are literature priors, not Kandy-calibrated. These are exactly the quantities that elevation-spanning local ground data would resolve.

**Interval centring.** The shipped 90 % interval covers 72.4 % of observed hours at the two sensor pixels. This is a *centring* offset, not a width error: the failure is one-sided (observations below the lower bound in 25.7 % of hours, above the upper in 1.9 %) with a median offset of +5.85 µg/m³ — the expected area-vs-point geometry, since the field is a 1 km area mean and the sensors are points. Removing each sensor's own median offset restores 91.5 % coverage. **Standing prediction:** a naive comparison against any future point measurement at Kandy will show the model ≈ 40 % high; that offset of +5 to +6 µg/m³ is expected and must be removed before any bias or coverage statement. An offset far outside that range indicates a genuine level error.

**Field tiers.** Three variants exist and are not interchangeable. `additive_v2` is the **locked** tier the paper and the multi-city scorecard are scored on (2019–2023). `additive_v3` adds a bounded, mean-zero *pattern floor* on ventilated hours — without it the increment split renders well-mixed hours perfectly flat, which held-out Medellín stations show the real atmosphere never is; it is T-lock-exact by construction, leaves structured hours byte-identical, and is what the web application serves. A separate **driver-anchored extension tier** covers 2024–2026, where the satellite level anchor no longer reaches, and is labelled as such everywhere it appears.

Code: `kandy_pm25/src/stage1_satml/decomp/` (build + figure suite) and `src/stage1_satml/models/predict_T_anchor_v3.py`. Canonical figure suite: `decomp/paper_figures.py` (F1–F13). Plans: `docs/additive_background_increment_plan_2026-06-04.md`, `docs/kandy_production_plan_2026-05-29.md`.

---

## Local/regional partition — an open quantity

The split between the regional background `B(t)` and the local increment is the least-settled number in the model, and the 2026-08 assessment is recorded here rather than in the shipped value.

**The shipped prior is refuted.** Five independent lines converge well above it:

| Line | Estimate of `f` | Independent of the model? |
|---|---|---|
| Hierarchical Bayesian pooling over 4 cities, Kandy held out | **0.392** [0.258, 0.525] | fitted on other cities only |
| Coherence floor (a within-day-flat `B` cannot exceed the day's minimum total) | **≥ 0.410** | uses the shipped anchor alone |
| NBRO island-network background instrument | **0.446** | yes — external measurement |
| Holiday natural experiments (Sunday / Poya / fixed holidays) | 0.24 – 0.52 | yes — external event structure |
| Source-apportionment literature bracket | [0.15, 0.50] | yes |
| **Shipped value** | **0.244** | — |

The hierarchical fit also recovers a **multiplicative attenuation `ρ = 0.426 ± 0.066`** in the project's own simulation-based inference: that inference systematically recovers only ~43 % of the true fraction, which explains why it read low at every locally-dominated city.

**Why the shipped value was not simply raised.** An independent background, pointwise coherence, `f` inside the literature bracket, and the observed wet/dry seasonal ratio are **four constraints on three degrees of freedom**. Five separate background reconstructions were built and gated; each satisfies three constraints and breaks the fourth, and which one breaks depends only on which was left unconstrained. The best candidate reached `f = 0.438` — matching the external instrument — and improved coherence from 28.5 % to 7.4 %, but drove the seasonal ratio to 0.349 against an observed 0.53, so it was rejected on the same gate that rejected the earlier attempts.

**What ships instead.** No model quantity was changed. Hours where the split cannot be made coherently now say *"Local contribution not resolvable this hour"* with the reason, rather than printing a spurious 0 % local share. The binding gap is specific and cheap to close: **1.8 % of hours put the total below the measured regional floor**, and that floor is an island-wide percentile pooling coastal stations while Kandy is inland and elevated. One in-basin or upwind monitor determines which side is wrong and collapses the over-determination. This is a measurement, not a reformulation.

---

## Transfer validation — the multi-city scorecard

Kandy has no held-out network, so the model is validated where analogous cities *do* have one: the production pipeline is run end-to-end at each city under **the same two-sensor information budget Kandy has**, and scored against that city's withheld monitors. This is the "borrowed ground truth" design.

**Panel: N = 10 cities, 5 countries, 2 continents** (Xichang, Chiang Mai, Bazhong, Chandigarh, Kathmandu, Baoji, Tai'an, Yichang, Medellín, Bogotá).

| Axis | Result | Gate tally |
|---|---|---|
| Seasonal correlation | 0.97 – 1.00 | 10/10 met |
| Diurnal correlation | 0.60 – 0.97 | 8/10 met |
| Level bias | −4 % to +30 % | 8/10 met |
| Fine within-city spatial rank | ρ 0.07 – 0.78 | **4 of 9 estimable** met |

The honest reading: **temporal structure and level transfer robustly across regimes; fine within-city spatial rank does not.** The spatial gate's failure pattern is itself the evidence for the information ceiling. Two results are worth stating because they were predicted wrongly beforehand — Medellín and Bogotá, the two cities where relief is weakest or absent, rank *highest* on fine spatial skill, which locates the spatial signal in the **emission surface rather than in terrain relief**. Chandigarh's spatial rank is **not estimable** (fewer than four co-located held-out stations) and is reported as such, never as a measured null.

---

## Deliverables

| Artefact | Status |
|---|---|
| **Kandy PM2.5 Explorer** — public web application, client-side field reconstruction | live, 2019–2026 + demonstration forecast tier |
| **Medellín showcase app** — the same engine where a city *does* have ground truth | live, 2018–2024 |
| **Preprint** (`kandy_pm25/docs/reports/preprint_kandy.pdf`) | 30 pp, claim-audited, submission-ready pending supervisor review |
| **Standalone model release** — `daminda1108/kandy_pm25_model`, MIT | v1.0.0 |
| **Technical reference** — 20-part model reference + epistemic ledger | current |

The forecast tier is labelled a **demonstration** in the interface and in every string: it is driven by an archived forecast-driver backtest at Medellín showing a skill improvement of **+0.120** over 24-hour persistence on a clean temporal split. An earlier figure of +0.223 was inflated by training-window leakage and must not be quoted.

---

## Stage B — Cross-City Spatial Residual Learner

**Superseded as the production spatial map by the additive decomposition above; retained as the exploratory cross-city experiment that motivated it.** Spatial estimation of `pm25 − c_prior_scaled` (additive residual against a GEOS-CF reanalysis prior, anchored per city). Framed as exploratory cross-city transfer; the spatial product inherits structure from priors and from cross-city training as much as from the source-city data themselves.

**Reanalysis prior (preprocessing step inside Stage B).** GEOS-CF PM25_RH35_GCC at 0.25° hourly is scaled per city by `c_prior_scaled = c_prior × city_ratio`, where `city_ratio = mean(pm25) / mean(c_prior)` is computed on per-row station–timestamp overlap. The Kandy ratio is 0.536 (= 24.5 / 45.7, KOALA / GEE GEOS-CF mean). This corrects the well-documented GEOS-CF over-prediction in tropical Asia and prevents prior-inflation in the residual.

**Source cities (N = 3, locked).** Medellín (11 stations, lowland control), Chiang Mai (8, tropical analogue), Kathmandu (45, dense valley). Bogotá and Mexico City were dropped as different atmospheric regimes. *(Historical: the roster was intended to expand via PVAF. That expansion happened, but into the **decomposition** transfer panel described above, not into ConvCNP training — the ConvCNP line was retired before the expanded source set could be used.)*

**Architecture.** deepsensor 0.4.2 ConvNP. UNet (32, 64, 128), 625,989 parameters. Student-t(df = 5) likelihood for robust point estimation; cosine LR 5 × 10⁻⁵ → 1 × 10⁻⁶, gradient clip 1.0. Inputs: station context (lat, lon, pm25) with per-station BLH, c_prior, diurnal and DOY harmonics; gridded auxiliaries c_prior, ERA5(-Land) BLH / u10 / v10 / T2m / dewpoint / precip, SRTM DEM, delta_z, OSM road density, VIIRS NTL.

**Per-city scaling factors** (locked in `kandy_pm25/config.py`, row-mean ratios):

| City | Station mean (µg/m³) | GEOS-CF mean (µg/m³) | Ratio |
|---|---|---|---|
| Medellín | 21.7 | 26.5 | 0.807 |
| Chiang Mai | 12.2 | 23.0 | 0.593 |
| Kathmandu | 61.2 | 77.4 | 0.560 |
| Kandy | 24.5 (KOALA) | 45.7 | 0.536 |

**Cascade history** (canonical: `docs/kaggle_kernel_log.md`). Each version adds a clean ablation.

| Version | Change | Mel r | ChiMai r | KTM r | Mean r | KTM bias (µg/m³) | cov90 |
|---|---|---|---|---|---|---|---|
| v11 | row-mean ratio fix | 0.170 | 0.682 | 0.427 | 0.426 | +11.59 | KTM 0.870 |
| v12 | + OSM road density | 0.174 | 0.698 | 0.456 | 0.443 | +9.09 | KTM 0.857 |
| v13 | + VIIRS NTL + wider terrain raster | 0.280 | 0.820 | 0.590 | 0.563 | +6.48 | collapsed 0.54–0.73 |
| v14 | Student-t(df = 5) likelihood | 0.321 | 0.795 | 0.682 | 0.599 | +0.14 | uncalibrated 0.51–0.75 |
| v14 + conformal | per-(city × hour-of-day) Mondrian conformal | — | — | — | — | — | 0.895–0.930 |

UQ pipeline (locked): Student-t(df = 5) NLL during training for a robust median, plus split-conformal scaling at inference for calibrated 90 % intervals (Vovk 2005; Romano et al. 2019). KTM analogue scale factor q̂ = 3.13 (scalar) or q̂ ∈ [2.13, 3.54] (per hour-of-day).

**Kandy zero-shot inference (preliminary, retained but not promoted to a primary product).** 2.25 M predictions on a 1 km × hourly grid for 2024 using checkpoint `convcnp_v13_holdout_medellin_seed3.pt` with conformal scale q̂ = 3.13 (KTM highland-valley analogue).

| Anchor | Value | Reference | Result |
|---|---|---|---|
| Annual mean | 22.1 µg/m³ | KOALA 24.5 ± 5 µg/m³ | within envelope |
| Seasonal contrast | DJF 27.7 / MAM 26.3 / JJA 11.5 / SON 23.0 | Senarathna 2024 + monsoon scavenging | qualitative match |
| Diurnal shape | nocturnal plateau ~37; sharp 06 → 10 LT collapse; midday trough 12–15 LT ~7; evening 17–23 LT rebuild | Senarathna 2024 | shape match; morning peak phase off by ~4 h |

Three known limitations are explicitly disclosed: the morning-peak phase error (model 03 LT vs Senarathna 07 LT, attributable to absence of Sri Lankan emission-timing data in training); a negative-value tail (−12 µg/m³ at the extreme, clipped at zero for plotting); and an N = 3 source set with only Kathmandu as a true highland-valley analogue. The Kandy spatial product is therefore held as preliminary, pending the PVAF source-city expansion.

A Sim2Real fine-tune on the two available FECT sensors (Akurana, Hantana) was attempted and produced a negative result: r → 0.9999 at the exact sensor pixels but city-wide annual mean inflated to 37 µg/m³ via wild extrapolation. The model memorised the exact sensor coordinates as identity keys rather than basin physics. This is retained as a documented ablation supporting the case for ≥ 5 spatially diverse sensors.

Anchors are framed as **structural-consistency checks pending field validation**, not as validation in the strict sense. KOALA, Senarathna, and MAIAC each play dual roles as upstream calibration anchors and downstream consistency checks; the framework cannot validate against an anchor it was calibrated to.

---

## Supporting Experiments

These workstreams are documented in the repository because they were carried out, produced artifacts, and informed the current design. None of them feeds the current Stage A or Stage B deployment pipeline; they are retained for transparency.

### Cross-continental PINN transfer experiment (Medellín → Chiang Mai)

A time-dependent advection–diffusion PINN (FourierPINNV3, 76,261 parameters) was pre-trained on Medellín and validated on Chiang Mai, to test whether a physics-informed network with the right curriculum could transfer cross-continent. The result is positive: Medellín R² = 0.932 (r(K, BLH) = 0.998) and Chiang Mai R² = 0.765 (r(K, BLH) = 0.981, bias = −0.59 µg/m³). The canonical curriculum is a three-phase schedule (pure-data Phase 1 → λ_pde ramp → λ_pde = 0.15 steady); λ_pde > 0.15 collapses spatial ordering.

The experiment establishes a transferable curriculum for cross-continental time-dependent PINN transfer in the absence of target-city ground truth. Spatial PINN work over Kandy was cut after the rigid Whiteman-ansatz identifiability failure (see next experiment), so this checkpoint is not used as a feeder for Stage B. Code: `kandy_pm25/src/stage2_transfer/`. Canonical checkpoints: `results/models/stage2_medellin_pinn/td_pinn_v1/checkpoints/epoch_01400.pt`, `results/models/stage2_chiangmai_pinn/td_pinn_v1/checkpoints/epoch_02200.pt`.

### SharedTerrainAnsatz identifiability diagnostic

A six-parameter rigid Whiteman terrain ansatz (`H_trap`, `α_v`, `w_stab`, `w_wind`, …) was fit jointly across Medellín, Chiang Mai, and Kathmandu. All six parameters hit bound constraints in each fit; LOOCV held-out skill on the held-out city collapsed to noise. The failure mode is identifiability: the ansatz functional form cannot simultaneously represent valley physics in regimes as different as Medellín (lowland), Chiang Mai (broad valley), and Kathmandu (dense bowl). This motivated the move to a data-driven ConvCNP residual learner for Stage B. Code: `kandy_pm25/src/stage3_pinn/models/shared_terrain_ansatz.py`.

### PVAF v1 — Physics-based Valley Analogue Finder

A supporting tool, not a deployed stage. PVAF scores candidate cities against Kandy across four feature families (terrain, climate, emissions, monitoring coverage) to select highland-valley analogues. Tier-1 sanity on the N = 4 set ranks Chiang Mai > Kathmandu > Medellín, matching the v14 LOOCV transfer-r rank order (Spearman ρ = 1.0). Its lasting role is as the city-similarity component that seeded the decomposition transfer panel; a v2 rescoring added pollution magnitude and seasonal pattern as first-class axes after v1's magnitude-blindness selected industrial basins 3–4× dirtier than Kandy. Code: `kandy_pm25/src/pvaf/`. Plan: `docs/pvaf_v1_plan.md`. Pre-registration: `osf.io/ykdb9` (locked 2026-05-23).

---

## Repository Structure

```
ProjectCD/
├── README.md                    This file — public overview
├── PROJECT_ARCHITECTURE.md      How the model is built (maths, module map, flow, tests)
├── CLAUDE.md                    Active session instructions (single source of truth for current state)
├── PROJECT.md                   Stage results, data inventory, epistemic status
├── memory/SESLOG.md             Session log (history of decisions and runs)
├── docs/
│   ├── AUDIT_2026-05-08.md      Hostile peer-review audit and fix log
│   ├── REDESIGN_2026-05-08.md   From-scratch redesign
│   ├── kaggle_kernel_log.md     Kaggle kernel run history
│   ├── osf_prereg_*.md          Pre-registrations and amendments
│   ├── pvaf_v1_plan.md          PVAF v1 plan and methodology
│   └── archive/                 Superseded plans and reports (banner-marked)
├── kandy_pm25/docs/             Current production working set + model reference + preprint
├── kandy_webapp/                Kandy PM2.5 Explorer (separate public repo)
├── medellin_webapp/             Medellín showcase app (separate public repo)
├── kandy_pm25_release/          Standalone model release (separate public repo, MIT)
├── kandy_pm25/
│   ├── config.py                All paths, constants, city ratios — single source of truth
│   ├── requirements.txt
│   └── src/
│       ├── stage1_satml/        Stage A satellite-ML + production decomposition
│       │   ├── decomp/          Additive decomposition: build_*, paper_figures.py (F1–F13),
│       │   │                    health_burden.py, exposure_weighting.py, terrain_transport.py
│       │   ├── features/        vandonkelaar.py (level anchor), dataset builders
│       │   └── models/          predict_T_anchor_v3.py (T(t)); XGBoost / LGBM / CatBoost
│       ├── stage2_transfer/     Cross-continental PINN experiment (supporting)
│       ├── stage3_pinn/
│       │   ├── data/            CityConfig + multi-city loader
│       │   ├── models/
│       │   │   ├── fourier_pinn_v3.py        FourierPINNV3 used by supporting PINN experiment
│       │   │   ├── shared_terrain_ansatz.py  Identifiability diagnostic (supporting)
│       │   │   ├── convcnp_terrain.py        Stage B ConvCNP residual learner
│       │   │   └── _archive/                 Pre-pivot v1/v2 PINN models, do not import
│       │   ├── physics/         pde_residual_v3.py + source_kernel.py (PINN experiment)
│       │   └── training/        train.py (PINN experiment); train_convcnp.py (Stage B)
│       └── pvaf/                PVAF v1 analogue finder (supporting tool)
└── scripts/                     Standalone data-acquisition and validation scripts
```

The narrative stages (A, B) and the directory workstream numbers (`stage1_satml/`, `stage2_transfer/`, `stage3_pinn/`) are distinct namespaces. Stage A code lives under `src/stage1_satml/`; Stage B code lives under `src/stage3_pinn/` (which also houses the supporting cross-continental PINN code that was historically called "stage 3" before the spatial PINN line was retired). Directory names are preserved to avoid breaking imports, Kaggle kernel paths, and the configuration constants.

---

## Setup

```bash
cd kandy_pm25
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt

# Authenticate APIs (one-time)
cdsapi-config                   # ERA5 and CAMS via Copernicus ADS
earthengine authenticate        # Google Earth Engine
```

See `kandy_pm25/SETUP_GUIDE.md` for detailed setup, including Kaggle access-token configuration for kernel pushes.

---

## Key Commands

```bash
# All commands run from kandy_pm25/

# --- Stage A ---

# Build merged daily dataset
python src/stage1_satml/features/build_dataset.py

# Train v1 XGBoost + quantile models
python src/stage1_satml/models/train_xgboost.py --no-shap

# Build v3 hourly residual dataset
python src/stage1_satml/features/build_dataset_v3_hourly.py

# Train v3 base learners and blend
python src/stage1_satml/models/train_lgbm_v3.py
python src/stage1_satml/models/train_catboost_v3.py
python src/stage1_satml/models/train_xgb_v3.py
python src/stage1_satml/models/blend_v3.py
python src/stage1_satml/models/conformal_v3.py

# --- Stage B ---

# ConvCNP cross-city LOOCV (Kaggle, T4 x2 GPU)
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 .venv/Scripts/kaggle.exe \
    kernels push -p data/processed/stage2/kaggle_kernel_convcnp_v14/

# --- Supporting cross-continental PINN experiment ---

PYTHONUTF8=1 PYTHONIOENCODING=utf-8 .venv/Scripts/kaggle.exe \
    kernels push -p data/processed/stage2/kaggle_kernel_kandy_td_pinn_v7/
```

---

## Data Sources

| Dataset | Resolution | Period | Role |
|---|---|---|---|
| CAMS EAC4 reanalysis | 0.75° / daily | 2003–2025 | Stage A v1 training labels (KOALA-corrected) |
| GEOS-CF PM25_RH35_GCC | 0.25° / hourly | 2018–2026 | Decomposition background seasonal shape; Stage A driver; Stage B per-city scaled prior |
| ERA5 single-level | 0.25° / hourly | 2001–2026 | Wind, BLH, T2m, precipitation |
| ERA5-Land | 0.1° / hourly | 2001–2026 | High-resolution wind, T2m, dewpoint |
| ERA5 pressure levels | 0.25° / hourly | 2018–2025 | T925 (subsidence inversion proxy) |
| MODIS MAIAC AOD (MCD19A2) | 1 km / daily | 2001–2025 | Stage A feature; Stage B consistency anchor |
| TROPOMI NO₂ / CO | ~7 km / daily | 2018–2026 | Stage A features; NO₂ emission-placement cross-check |
| VIIRS Nighttime Lights | 500 m / monthly | 2018–2023 | Emission pattern; population-weighted exposure; Stage B feature |
| MERRA-2 aerosol | 0.625° / hourly | 2001–2026 | Diagnostic only — rejected as label |
| Van Donkelaar V6.GL02.04 | 1 km / annual | 1998–2023 | **Production level anchor (area mean) + S_emit emission pattern** |
| GHAP / GlobalHighPM2.5 (Wei et al.) | 1 km / monthly | 2017–2022 | Independent corroboration (seasonal r = 0.91); not a model input |
| SRTM 30 m DEM | 30 m static | — | Terrain confinement; WindNinja diagnostic winds |
| OpenStreetMap road network | Vector | 2025 | Congestion-weighted traffic emission source; Stage B road density |
| WorldPop population | ~100 m | 2020 | Population-weighted exposure and health burden |
| KOALA Kandy (Senarathna et al. 2024) | Annual + 12 monthly + diurnal | 2019 | 2019 floor/core consistency anchor; diurnal/monthly reference |
| FECT PurpleAir Kandy (Akurana + Hantana) | Point / hourly | 2018–2026 | Stage A v3 labels (per-sensor calibrated) |
| US Embassy Colombo (AirNow) | Point / hourly | 2019–2026 | Out-of-domain coverage check |
| SIATA Medellín | Point / hourly | 2018–2025 | Stage B source city |
| Air4Thai + PurpleAir Chiang Mai | Point / hourly | 2021–2025 | Stage B source city |
| AirGradient + GD Labs Kathmandu | Point / hourly | Oct 2025 – May 2026 | Stage B source city |

---

## Key Methodological Notes

- **Physics-structured, not black-box, at the spatial step.** The production field imposes its spatial structure from independently defensible physics (measured Van Donkelaar emission pattern, congestion-weighted traffic source, terrain confinement, WindNinja diagnostic winds) and learns only the temporal level from data. This is what avoided the cross-city ConvCNP failure mode, where the spatial pattern was inherited from the training cities rather than from Kandy.
- **Basin mean is preserved exactly.** `P_local` is normalised to unit basin mean, so the basin-average concentration equals the temporal anchor `T(t)` and only the spatial *arrangement* of the local quarter is structured. The level itself is the per-year Van Donkelaar **area** mean (β ≡ 1).
- **Additive, not multiplicative.** `PM = B + [T − B]·P_local` adds the regional background uniformly and structures only the locally generated increment; the earlier multiplicative `T·S·M` incorrectly modulated the transboundary background by the local pattern. A held-out ablation quantifies the difference: multiplicative inflates the held-out level by +26 % where monitors cluster on the valley floor, additive by −0 %.
- **The local fraction is a disclosed prior under active revision.** It is set per year in the range 0.20–0.28 and was never fitted; five independent lines now place it at 0.35–0.45. Because the field is T-locked the level and burden are insensitive to this — the attribution claim is not. See [Local/regional partition](#localregional-partition--an-open-quantity).
- **Native resolution 1 km hourly.** GEOS-CF (0.25°) and ERA5 (0.25°) have no spatial structure below ~25 km; resolving below 1 km from these inputs is unsupported.
- **Uncertainty quantification.** CV+ Mondrian conformal on the Stage A anchor; calibrated 90 % prediction interval plus a per-pixel spatial-uncertainty layer on the production field. Coverage and calibration are reported alongside every r / RMSE.
- **Anchors are calibration anchors, not validators.** KOALA, Senarathna, GHAP, and the FECT sensors double as upstream calibration anchors and downstream consistency checks; they cannot independently validate. Agreement is reported as *corroboration*, never validation.
- **Fine-scale magnitude is the open item, and local ground data is the binding constraint.** The within-basin floor-to-ridge magnitude is imposed from physics and unmeasured — no public network anywhere samples that gradient (a several-hundred-valley screen confirmed floor-clustering is universal). Confinement strength, local fraction, traffic scaling, and transport amplitude are literature priors. Elevation-spanning local ground observation is the decisive next input; the transport overlay `A_transport` is shipped as a scenario, not a validated layer.
- **Reproducibility.** Regeneration chain and gotchas are documented in `CLAUDE.md`; Kaggle kernels and per-version metric tables in `docs/kaggle_kernel_log.md`; pre-registrations and amendments in `docs/osf_prereg_*.md`.

---

*This document mirrors the canonical state in [`CLAUDE.md`](CLAUDE.md) and [`PROJECT.md`](PROJECT.md). If you find a discrepancy between this README and the canonical state files, the canonical state files take precedence and this README is wrong.*
