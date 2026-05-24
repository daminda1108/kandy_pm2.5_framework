# Kandy PM2.5 — Multi-Target PM2.5 Estimation for Unmonitored Tropical Highland Cities

**Undergraduate thesis** — Daminda Alahakoon, Department of Environmental Sciences, University of Peradeniya
**Working spatial model:** end of June 2026 | **arXiv preprint:** 31 August 2026 | **JAMES/GMD submission:** 31 October 2026 | **Thesis:** October 2026

---

## Overview

Kandy, Sri Lanka has no continuous PM2.5 monitoring stations. This project develops a multi-stage framework for spatiotemporally resolved PM2.5 estimation in Kandy and other unmonitored tropical highland cities (Nuwara Eliya, Badulla), at the **intrinsic resolution of the available data — 1 km, hourly** — with calibrated per-pixel uncertainty. The framework cascades a satellite-ML temporal anchor through a cross-continental physics-informed transfer experiment to a Convolutional Neural Process residual learner trained on five station-rich source cities and applied zero-shot to Sri Lankan highland targets.

The project produces three independent contributions:
1. A 22-year KOALA-anchored PM2.5 chronology for Kandy from CAMS reanalysis (XGBoost, Stage A).
2. A documented cross-continental PINN transfer rule for time-dependent advection–diffusion physics (Stage 2: Medellín → Chiang Mai).
3. A diagnosed identifiability failure of fixed-form Whiteman terrain ansätze in tropical valleys, motivating the data-driven spatial architecture (paper §4 negative result).

The fourth, currently in progress: a Convolutional Neural Process residual learner that improves spatially upon a reanalysis prior, demonstrated zero-shot at three unmonitored Sri Lankan highland targets (Stage C+D).

> **What this framework does and does not do.** It does not replace physical monitoring; it does not provide point-level accuracy at sub-1 km; it does not chemically apportion sources; it does not forecast. It produces hourly 1 km PM2.5 fields anchored to the only published Kandy in-situ campaign (Senarathna et al. 2024), with uncertainty quantification and three structural-consistency anchors at the unmonitored target. Validation in the strict sense awaits future field deployment.

---

## Pipeline

```
                                    ┌────────────────────────────┐
                                    │ KOALA 2019 anchor 24.5 µg/m³│
                                    │ (Senarathna et al. 2024,   │
                                    │  CJS 53(2):197–206;        │
                                    │  12 monthly aggregates)    │
                                    └─────────────┬──────────────┘
                                                  │
              ┌──────────────────────┬────────────┴────────────┬──────────────────────┐
              │                      │                         │                      │
              v                      v                         v                      v
   STAGE A — Temporal anchor      STAGE B — Reanalysis      STAGE C — Cross-city    STAGE D — Zero-shot
   (XGBoost, daily, 2003–2025)    baseline (GEOS-CF         residual learner        inference
                                  hourly × per-city scale)  (ConvCNP, deepsensor)   (Kandy + Nuwara
   CAMS×0.5984 → bias-corrected    Kandy ratio = 0.536       N=5 source cities       Eliya + Badulla)
   labels                          (= 24.5 / 45.7)           predicts log(pm25/      1 km hourly +
                                                             c_prior_scaled)         per-pixel σ
   LOMO R²=0.631; KOALA r=0.515,                             3-seed LOOCV with       3 consistency anchors
   bias=+0.09 µg/m³                                           bootstrap CIs
                                                                       │
                                                                       v
                                                          STAGE 2 — Physics transfer
                                                          (paper §3.3 counterpoint)
                                                          FourierPINNV3 TD-PDE,
                                                          Medellín → Chiang Mai
                                                          Med R²=0.932, r_kblh=0.998
                                                          ChiMai R²=0.765, r_kblh=0.981

   PAPER §4 (parallel)
   SharedTerrainAnsatz negative result
   6 Whiteman parameters → bound saturation across 3 cities
   Conceptual contribution: rigid terrain ansatz fails identifiably in tropical valleys
```

Native data resolution is 1 km hourly. An optional terrain-guided 1 km → 100 m kernel disaggregation (Stage E) is available as a labelled presentation step; it introduces no new physical information.

---

## Stage A — Satellite-ML Temporal Anchor (COMPLETE)

| Metric | Value |
|---|---|
| Held-out LOMO R² | **0.631** |
| Train-fit R² | 0.760 |
| Temporal CV R² | 0.554 |
| RMSE | 4.82 µg/m³ |
| 90% PI coverage | 89.4% (target > 85%) |
| 90% PI width | 17.6 µg/m³ |
| KOALA 2019 monthly r | 0.515 (n=12 monthly aggregates) |
| KOALA 2019 bias | +0.09 µg/m³ |
| Training window | 2003–2025 (8,279 days) |
| Features | 44 (5 satellite, 18 meteorological, 12 topographic, 9 temporal) |
| Hyperparameter search | 100-trial Optuna over LOMO objective |

**Bias correction.** A flat annual scalar ratio ×0.5984 was selected after monthly correction was tested and rejected (LOMO R² 0.631 → 0.507–0.519) and MERRA-2 blending was tested and rejected (r(CAMS, MERRA-2) = 0.177 over Kandy; LOMO degraded to 0.498). The Priyankara (2021) anchor of 34.48 µg/m³ was identified as a March peak rather than an annual mean and replaced with the Senarathna (2024) annual KOALA value of 24.5225 µg/m³ (within the published ±17.5% bound).

**Top SHAP drivers.** wind_speed (3.594), pm25_prev_month_mean (0.809), rwp (0.641), vvc (0.577), aod_blh_ratio (0.555).

**Monthly LOMO R²** (low values are structural — SW monsoon variance collapse, CoV–Skill r=0.823 p=0.001):
Jan 0.535 · Feb 0.341 · Mar 0.335 · Apr 0.193 · May 0.409 · Jun 0.137 · Jul 0.279 · Aug 0.319 · Sep 0.399 · Oct 0.588 · Nov 0.617 · Dec 0.663

---

## Stage 2 — Cross-Continental PINN Transfer (COMPLETE)

Time-dependent advection–diffusion PINN, FourierPINNV3 architecture:

```
∂C/∂t + u·∇C = ∇·(K∇C) − v_d·C + S − Λ·P·C
```

Trained from raw PyTorch autograd. Quasi-steady-state formulation was tested (Kandy v8/v9) and rejected on structural grounds (R² = −0.39 / −0.32 with r_kblh = 0.998/0.999, indicating QSS cannot capture temporal dynamics through K(BLH) alone).

**Architecture (FourierPINNV3, 76,261 parameters):**
- SpatialEmbedding: dual-bank multi-scale Fourier features, m_lo = m_hi = 64, σ ∈ {1.0, 3.0}, out_dim = 256
- TrunkNetV3: Linear(261 → 128) → GELU → 1 × ResBlock(128) → Linear(128 → 64) → GELU
- DiffusionSubNetV3: factored K_base(BLH, t) × K_aniso(x, y, elev), 1,315 parameters
- AlphaNet: [sin h, cos h] → α; S(x, y, t) = α(t) × R(x, y), 65 parameters; R(x, y) is a registered OSM road kernel buffer (breaks the K–S identifiability degeneracy structurally)

**Canonical curriculum (the v7 schedule used for both source cities):**
| Phase | Epochs | λ_pde | λ_data | λ_bc | λ_kblh |
|---|---|---|---|---|---|
| 1 — Pure data | 0–25% | **0.00** | 0.75 | 0.20 | 0.05 |
| 2 — PDE ramp | 25–60% | 0 → 0.15 | 0.75 → 0.55 | 0.20 → 0.15 | 0.05 → 0.15 |
| 3 — Steady | 60–100% | 0.15 (max) | 0.55 | 0.15 | 0.15 |

Phase 1 must be pure data (λ_pde = 0); the PDE residual cannot be informative until the network establishes spatial station ordering. λ_pde > 0.15 collapses spatial ordering (FourierPINNV3 v5 lesson).

**Transfer results.**
| City | Role | Best ckpt | R² | r(K, BLH) | Bias |
|---|---|---|---|---|---|
| Medellín (SIATA, 11 stations) | Pre-training | TD-PDE v1 ep1400 | **0.932** | **0.998** | — |
| Chiang Mai (Air4Thai+PA, 8 stations) | Held-out validation | TD-PDE v1 ep2200 | **0.765** | **0.981** | −0.59 µg/m³ |

The pre-training ↔ transfer warm-start was validated through controlled experiments showing pure-data Phase-1 weights transfer (success), Phase-3 physics-tuned weights overfit to source-domain physics (failure), and inoculated progressive warm-starts partially transfer (partial failure).

---

## Stage C — ConvCNP Residual Learner (ACTIVE)

Spatial estimation of the deviation `log(pm25) − log(c_prior_scaled)` from a Convolutional Neural Process trained on five station-rich source cities. Anchored by the GEOS-CF reanalysis prior (`c_prior_scaled = c_prior × city_ratio`), so the model's contribution is the structured *correction* of the prior, not the prior itself.

**Source cities (N = 5):** Medellín (11 stations, control), Chiang Mai (8, tropical analog), Kathmandu (45, dense valley), Bogotá (~20, Andean control), Mexico City (~30, plateau control). Framed as **few-shot transfer**, not "meta-learning" (N = 5 is too small to support that claim).

**Architecture.** deepsensor 0.4.2 ConvNP. UNet (32, 64, 128). Heteroscedastic Gaussian likelihood with per-station σ_obs (Senarathna ±17.5%, KTM GD Labs ±30%, ChiMai PA ±20%). Cosine LR 5×10⁻⁵ → 1×10⁻⁶, gradient clip 1.0.

**Inputs.**
- Sparse station context per task: (lat, lon, pm25), per-station BLH, c_prior, diurnal harmonics, DOY harmonics
- Gridded auxiliaries: GEOS-CF c_prior, ERA5(-Land) BLH/u10/v10/T2m/dewpoint/precip, SRTM DEM, delta_z, OSM road kernel

**Per-city scaling factors** (locked in `kandy_pm25/config.py`):

| City | Station mean (µg/m³) | GEOS-CF mean (µg/m³) | Ratio |
|---|---|---|---|
| Medellín | 21.7 | 26.5 | 0.819 |
| Chiang Mai | 12.2 | 23.0 | 0.530 |
| Kathmandu | 61.2 | 77.4 | 0.791 |
| Bogotá | 16.5 | 20.4 | 0.807 |
| Mexico City | 21.2 | 97.4 | 0.217 |
| **Kandy** | **24.5 (KOALA)** | **45.7** | **0.536** |

**LOOCV history** (canonical: `docs/kaggle_kernel_log.md`).

| Run | Architecture change | Mel r | ChiMai r | KTM r | Mean | Gates |
|---|---|---|---|---|---|---|
| v4 | direct target, GNP | 0.153 | 0.648 | 0.459 | 0.420 | 2/3 |
| v7 | log-ratio target | 0.256 | 0.621 | 0.394 | 0.424 | 2/3 |
| v8 | N=5 (adds Bogotá + Mexico City) | RUNNING | — | — | — | — |

All single-run point estimates pending 3-seed re-runs with bootstrap confidence intervals (Week 2 of redesign schedule).

---

## Stage D — Zero-Shot at Three Unmonitored Sri Lankan Highland Targets

Best Stage C checkpoint applied to Kandy (~500 m ASL valley), Nuwara Eliya (~1,900 m ASL highland), and Badulla (~680 m ASL valley). Output: 1 km hourly PM2.5 + per-pixel σ.

**Three structural-consistency anchors per target** — explicitly framed as consistency checks pending field validation, not validation in the strict sense:

1. Annual spatial mean within ±5 µg/m³ of nearest published anchor
2. Diurnal cycle r > 0.7 against published diurnal pattern (Senarathna 2024 for Kandy)
3. MAIAC AOD spatial gradient r > 0.4 (with the retrieval-rate caveat: MAIAC has 27.1% annual coverage at Kandy, dropping below 20% in the southwest monsoon)

The KOALA anchor used for Kandy bias correction is also listed among the consistency anchors. This dual role is acknowledged: an anchor cannot independently validate a model calibrated against it. The three anchors are necessary but insufficient for validation; we additionally report spatial standard deviation, terrain–PM correlation, and predictive-interval calibration as physical-realism diagnostics.

---

## Repository Structure

```
ProjectCD/
├── README.md                    This file
├── CLAUDE.md                    Active session instructions (single source of truth for current state)
├── PROJECT.md                   Detailed stage results, architecture, data inventory
├── memory/SESLOG.md             Session log (history of decisions and runs)
├── docs/
│   ├── AUDIT_2026-05-08.md      Hostile peer-review audit + fix log
│   ├── REDESIGN_2026-05-08.md   From-scratch redesign with 16-week schedule
│   ├── kaggle_kernel_log.md     Kaggle kernel run history
│   ├── paper/                   Manuscript sections in progress
│   │   ├── 00_paper_plan.md
│   │   ├── 01_introduction.md
│   │   ├── 02_study_area_data.md
│   │   ├── 03_methods.md
│   │   └── 04_negative_result.md
│   └── archive/                 Superseded plans and reports (banner-marked)
├── kandy_pm25/
│   ├── config.py                All paths, constants, city ratios — single source of truth
│   ├── requirements.txt
│   └── src/
│       ├── stage1_satml/        Stage A: XGBoost satellite-ML
│       ├── stage2_transfer/     Stage 2: FourierPINNV3 cross-continental transfer
│       ├── stage3_pinn/
│       │   ├── data/            CityConfig + multicity loader
│       │   ├── domain/          Kandy domain definitions
│       │   ├── models/
│       │   │   ├── fourier_pinn_v3.py        Active — FourierPINNV3 (76,261 params)
│       │   │   ├── shared_terrain_ansatz.py  Paper §4 negative-result reference
│       │   │   ├── convcnp_terrain.py        ConvCNP residual learner (Stage C)
│       │   │   └── _archive/                 Pre-pivot v1/v2 PINN models, do not import
│       │   ├── physics/         pde_residual_v3.py + source_kernel.py (active);
│       │   │                    advection_diffusion.py et al. → _archive/
│       │   └── training/        train.py (Stage 2); train_convcnp.py (Stage C)
│       └── utils/               plot_style.py
└── scripts/                     Standalone data-acquisition and validation scripts
```

---

## Setup

```bash
cd kandy_pm25
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt

# Authenticate APIs (one-time)
cdsapi-config                   # ERA5/CAMS via Copernicus ADS
earthengine authenticate        # Google Earth Engine
```

See `kandy_pm25/SETUP_GUIDE.md` for detailed setup, including Kaggle access-token configuration for kernel pushes.

---

## Key Commands

```bash
# All commands run from kandy_pm25/

# Build merged Stage A dataset (ERA5 + MODIS + TROPOMI + CAMS labels + topographic features)
python src/stage1_satml/features/build_dataset.py

# Train Stage A XGBoost + quantile models
python src/stage1_satml/models/train_xgboost.py --no-shap

# Stage 2 cross-continental PINN training is run on Kaggle (T4×2 GPU).
# Kernel directories live under data/processed/stage2/kaggle_kernel_*/
# Push pattern:
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 .venv/Scripts/kaggle.exe \
    kernels push -p data/processed/stage2/kaggle_kernel_kandy_td_pinn_v7/

# Stage C ConvCNP LOOCV is also run on Kaggle:
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 .venv/Scripts/kaggle.exe \
    kernels push -p data/processed/stage2/kaggle_kernel_convcnp_v1/
```

---

## Data Sources

| Dataset | Resolution | Period | Role |
|---|---|---|---|
| CAMS EAC4 reanalysis | 0.75°/daily | 2003–2025 | Stage A training labels (×0.5984 KOALA-corrected) |
| GEOS-CF PM25_RH35_GCC | 0.25°/hourly | 2018–2026 | Stage B reanalysis prior; Stage C c_prior |
| ERA5 single-level | 0.25°/hourly | 2001–2026 | Wind, BLH, T2m, precipitation |
| ERA5-Land | 0.1°/hourly | 2001–2026 | High-resolution wind, T2m, dewpoint |
| MODIS MAIAC AOD (MCD19A2) | 1 km/daily | 2001–2025 | Stage A feature; Stage D consistency anchor |
| TROPOMI NO2 / CO | ~7 km/daily | 2018–2026 | Stage A satellite features |
| MERRA-2 aerosol | 0.625°/hourly | 2001–2026 | Diagnostic only — rejected as label (r(CAMS,MERRA-2)=0.177) |
| Van Donkelaar V6GL02.04 | 1 km/annual | 1998–2023 | Independent satellite PM2.5 product (Stage A triangulation) |
| SRTM 30 m DEM | 30 m static | — | Terrain elevation, slope, aspect |
| OpenStreetMap | Vector | 2025 | Road network → emission source kernel |
| KOALA Kandy 2019 (Senarathna et al. 2024) | Annual + 12 monthly + diurnal | 2019 | Bias correction anchor and Stage D consistency anchor |
| SIATA Medellín | Point/hourly | 2018–2025 | Stage 2 pre-training (11 stations); Stage C source city |
| Air4Thai + PurpleAir Chiang Mai | Point/hourly | 2021–2025 | Stage 2 transfer validation (8 stations); Stage C source city |
| GD Labs + Embassy Kathmandu | Point/hourly | Oct 2025 – May 2026 | Stage C source city (45 stations dense window) |
| RMCAB Bogotá | Point/hourly | 2018–2025 | Stage C source city (~20 stations) |
| SIMAT Mexico City | Point/hourly | 2018–2025 | Stage C source city (~30 stations) |

---

## Key Methodological Decisions

- **No ground sensors during training.** PM2.5 labels for Kandy are derived from satellite reanalysis (CAMS EAC4) bias-corrected against the KOALA campaign anchor (Senarathna et al. 2024, CJS 53(2):197–206). Cross-validated against Van Donkelaar V6GL02.04 satellite climatology.
- **Pre-Kandy physics transfer.** FourierPINNV3 is pre-trained on Medellín, then validated on Chiang Mai (held-out stations never seen during training) before any Kandy application — the only pre-Kandy physics-validation opportunity available.
- **Pure-data Phase-1 warm-start rule.** Cross-domain transfer requires initialising from a Phase-1 checkpoint (λ_pde = 0). Inoculated progressive warm-starts and Phase-3 checkpoints lock the K–BLH relationship to source-domain geography and fail to adapt.
- **Residual learning at the spatial step.** Stage C predicts `log(pm25) − log(c_prior_scaled)`, not pm25 directly. This makes the GEOS-CF prior contribution explicit rather than implicit and prevents accidentally claiming model skill that is in fact reanalysis interpolation.
- **Native resolution 1 km hourly.** The driving reanalyses (GEOS-CF 0.25°, ERA5 0.25°) have no spatial structure below ~25 km; resolving below 1 km from these inputs is fictional. An optional terrain-guided kernel disaggregation to 100 m is provided as a labelled presentation step.
- **Uncertainty quantification.** Quantile regression (q05/q50/q95) on Stage A; heteroscedastic Gaussian likelihood on Stage C; coverage and calibration reported alongside every r/RMSE.
- **Stage 3 domain.** 15 × 15 km centred on Kandy (KANDY_PINN_BBOX: 7.2230–7.3582 °N, 80.5660–80.7014 °E), 150 × 150 grid at 100 m for inputs; outputs reported at 1 km native.
- **Multi-target zero-shot.** The framework is applied at three Sri Lankan highland targets (Kandy, Nuwara Eliya, Badulla) to demonstrate that the cross-city training generalises to multiple unmonitored cities, not just the original target.
- **Quasi-steady-state PDE rejected.** Tested as v8/v9 in the spatial-attractor era; structural failure (negative R² with high r_kblh). Time-dependent advection–diffusion is the only PDE form used.
- **Fixed Whiteman terrain ansatz rejected.** SharedTerrainAnsatz combined_v2 demonstrated identifiability collapse across heterogeneous tropical valleys (six learnable parameters all converging to bound constraints). The failure motivates the data-driven Stage C architecture and constitutes paper §4 (negative result).

---

## Citation

If you use this code or methodology, please cite:

> Alahakoon, D. (2026). *Multi-Target PM2.5 Estimation for Unmonitored Tropical Highland Cities via Cross-City Convolutional Neural Processes Anchored by Reanalysis Priors.* Undergraduate thesis, Department of Environmental Sciences, University of Peradeniya. arXiv preprint forthcoming.

---

*This document mirrors the canonical state in [`CLAUDE.md`](CLAUDE.md) and [`PROJECT.md`](PROJECT.md). Last rewritten 2026-05-08 to resolve the issues documented in [`docs/AUDIT_2026-05-08.md`](docs/AUDIT_2026-05-08.md). All numbers in this README are cross-referenced against the canonical state files; if you find a discrepancy, the canonical state files take precedence and this README is wrong.*
