# Kandy PM2.5 — Multi-Target PM2.5 Estimation for Unmonitored Tropical Highland Cities

Undergraduate thesis project — Daminda Alahakoon, Department of Environmental Sciences, University of Peradeniya.

---

## Overview

Kandy, Sri Lanka has no continuous PM2.5 monitoring stations. This repository develops a multi-stage framework for spatiotemporally resolved PM2.5 estimation in Kandy and two other unmonitored Sri Lankan highland cities (Nuwara Eliya and Badulla), at the intrinsic resolution of the available driving data — 1 km, hourly — with calibrated per-pixel uncertainty.

The framework cascades a satellite-machine-learning temporal anchor through a cross-continental physics-informed transfer experiment to a Convolutional Neural Process residual learner trained on three station-rich source cities and applied zero-shot to the Sri Lankan highland targets. Each stage is independently testable and is reported with its own held-out skill, uncertainty calibration, and structural-consistency diagnostics.

What the framework does *not* do: it does not replace physical monitoring; it does not provide point-level accuracy at sub-1 km; it does not chemically apportion sources; it does not forecast. Outputs at the unmonitored targets are hourly 1 km PM2.5 fields with per-pixel σ, anchored to the only published Kandy in-situ campaign (Senarathna et al. 2024). Strict validation requires field deployment, which is identified as a future work item.

---

## Pipeline

```
                 ┌─────────────────────────────────────────────┐
                 │ KOALA 2019 anchor 24.5 µg/m³ (Senarathna     │
                 │ et al. 2024, CJS 53(2):197–206; 12 monthly   │
                 │ aggregates)                                  │
                 └────────────────────┬────────────────────────┘
                                      │
        ┌──────────────────┬──────────┴──────────┬──────────────────┐
        v                  v                     v                  v
   Stage A           Stage B               Stage C            Stage D
   Temporal anchor   Reanalysis baseline   Cross-city         Zero-shot
   (XGBoost +        (GEOS-CF × per-city   residual learner   inference at
   LGBM+CatBoost     scaling, Kandy ratio  (ConvCNP,          Kandy + Nuwara
   blend)            0.536 = 24.5 / 45.7)  deepsensor)        Eliya + Badulla
                                           N = 3 highland-    (1 km hourly +
   v1 daily LOMO                           valley source      per-pixel σ;
   R² = 0.631;                             cities; predicts   3 consistency
   v3 hourly                               pm25 − c_prior     anchors per
   pooled R² = 0.581                       residual           target)
                                                    │
                                                    v
                                        Stage 2 — Physics transfer
                                        (FourierPINNV3 TD-PDE,
                                        Medellín → Chiang Mai)
                                        Medellín R² = 0.932,
                                        Chiang Mai R² = 0.765
```

Native resolution is 1 km hourly. An optional terrain-guided 1 km → 100 m kernel disaggregation (Stage E) is available as a labelled presentation step; it adds no new physical information.

---

## Methodological Evolution

The current architecture is the result of several explicit pivots, each driven by a measured failure of the prior approach. They are summarised here so the design choices are legible; the full record lives in `docs/REDESIGN_2026-05-08.md`, `docs/AUDIT_2026-05-08.md`, and the session log at `memory/SESLOG.md`.

| Date | Pivot | Reason |
|---|---|---|
| 2026-03 | QSS spatial PINN → **TD-PDE temporal PINN** for Stage 2 | QSS lost spatial ordering of stations under physics pressure (λ_pde ≥ 0.38 collapsed the field). TD-PDE with the v7 curriculum (pure-data Phase 1 → ramped λ_pde to 0.15 max) recovered ordering and now anchors Stage 2. |
| 2026-05-04 | SharedTerrainAnsatz → **ConvCNP residual learner** for Stage C | All six Whiteman-ansatz parameters hit bound constraints across the source-city set; the rigid functional form could not represent valley physics in different regimes. ConvCNP residual learning was adopted; the ansatz failure is retained as a documented diagnostic. |
| 2026-05-17 | CAMS as label → **CAMS as feature** (Stage 1 v2 reframe) | v1 used KOALA both to calibrate CAMS labels (×0.598) and to validate the result (r = 0.515) — circular by construction. v2 promotes FECT-calibrated PurpleAir to labels and demotes CAMS / GEOS-CF to features; daily LOMO R² moved from 0.631 to 0.689. |
| 2026-05-20 | Daily v2 → **hourly v3** | Hourly residual target with per-sensor offsets enables diurnal-cycle reproduction (against Senarathna 2024, r = +0.865). After a 39-feature Tier-1 rebuild failed to lift pooled R² above 0.581, the R² ≥ 0.60 target was closed as an honest near-miss; sensor expansion was identified as the binding constraint, not architecture. |
| 2026-05 | N = 5 → **N = 3** source cities + **PVAF v1** | Bogotá and Mexico City were dropped from Stage C cross-validation as different atmospheric regimes (Mexico City GEOS-CF over-predicts by a factor of ~4.6). PVAF v1 was launched to select additional highland-valley analogues by physics-similarity scoring before Kandy production maps are regenerated. |
| 2026-05-22 | Gaussian NLL → **Student-t(df = 5) + split-conformal** for UQ | ConvCNP v13 satisfied point-skill targets but Gaussian likelihood let σ collapse (cov90 fell to 0.54–0.73). v14 switched to Student-t for robust point estimation; per-(city × hour-of-day) Mondrian conformal calibration restored cov90 ∈ [0.85, 0.95] across all source cities without retraining. |

---

## Stage A — Satellite-ML Temporal Anchor

Two parallel tracks are maintained: a daily anchor (v1) and an hourly RECAP residual learner (v3). The daily track stays in the repository as a 22-year chronology for Kandy; the hourly track is the operational track for Stage D inference.

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

---

## Stage 2 — Cross-Continental PINN Transfer

Time-dependent advection–diffusion PINN, FourierPINNV3 architecture:

```
∂C/∂t + u·∇C = ∇·(K∇C) − v_d·C + S − Λ·P·C
```

Trained from raw PyTorch autograd. Quasi-steady-state formulation was tested at Kandy (v8 / v9) and rejected on structural grounds (R² = −0.39 / −0.32 with r(K, BLH) = 0.998 / 0.999, indicating QSS cannot capture temporal dynamics through K(BLH) alone).

**Architecture (FourierPINNV3, 76,261 parameters):**

- SpatialEmbedding: dual-bank multi-scale Fourier features, m_lo = m_hi = 64, σ ∈ {1.0, 3.0}, out_dim = 256
- TrunkNetV3: Linear(261 → 128) → GELU → 1 × ResBlock(128) → Linear(128 → 64) → GELU
- DiffusionSubNetV3: factored K_base(BLH, t) × K_aniso(x, y, elev), 1,315 parameters
- AlphaNet: [sin h, cos h] → α; S(x, y, t) = α(t) × R(x, y), where R is a registered OSM road kernel buffer (breaks K–S identifiability structurally)

**Canonical curriculum (v7, used unchanged for both source cities):**

| Phase | Epochs | λ_pde | λ_data | λ_bc | λ_kblh |
|---|---|---|---|---|---|
| 1 — Pure data | 0–25 % | 0.00 | 0.75 | 0.20 | 0.05 |
| 2 — PDE ramp | 25–60 % | 0 → 0.15 | 0.75 → 0.55 | 0.20 → 0.15 | 0.05 → 0.15 |
| 3 — Steady | 60–100 % | 0.15 (max) | 0.55 | 0.15 | 0.15 |

Phase 1 must be pure data — the PDE residual is not informative until the network establishes spatial station ordering. λ_pde > 0.15 collapses spatial ordering.

**Transfer results.**

| City | Role | Best checkpoint | R² | r(K, BLH) | Bias |
|---|---|---|---|---|---|
| Medellín (SIATA, 11 stations) | Pre-training | TD-PDE v1 ep1400 | 0.932 | 0.998 | — |
| Chiang Mai (Air4Thai + PA, 8 stations) | Held-out validation | TD-PDE v1 ep2200 | 0.765 | 0.981 | −0.59 µg/m³ |

The pre-training ↔ transfer warm-start was validated through controlled experiments showing pure-data Phase-1 weights transfer, while Phase-3 physics-tuned weights overfit to source-domain physics.

---

## Stage C — ConvCNP Residual Learner

Spatial estimation of `pm25 − c_prior_scaled` (additive residual against a GEOS-CF reanalysis prior, anchored per city). Framed as exploratory cross-city transfer; the spatial product inherits structure from priors and from cross-city training as much as from the source-city data themselves.

**Source cities (N = 3, locked):** Medellín (11 stations, lowland control), Chiang Mai (8, tropical analogue), Kathmandu (45, dense valley). Bogotá and Mexico City were dropped as different atmospheric regimes. The roster is intended to expand to N ≥ 6 via PVAF v1 (highland-valley analogue finder; currently selecting candidates from Dhaka, Lahore, Jakarta, Kabul, La Paz, Quito).

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

---

## Stage D — Zero-Shot Inference at Three Sri Lankan Highland Targets

Kandy (~500 m ASL, valley), Nuwara Eliya (~1,900 m ASL, highland), Badulla (~680 m ASL, valley). Output: 1 km hourly PM2.5 + per-pixel σ over a one-year period.

**Kandy 2024 inference (preliminary, retained but not yet promoted to a primary product).** 2.25 M predictions on a 1 km × hourly grid using checkpoint `convcnp_v13_holdout_medellin_seed3.pt` with conformal scale q̂ = 3.13 (KTM highland-valley analogue).

| Anchor | Value | Reference | Result |
|---|---|---|---|
| Annual mean | 22.1 µg/m³ | KOALA 24.5 ± 5 µg/m³ | within envelope |
| Seasonal contrast | DJF 27.7 / MAM 26.3 / JJA 11.5 / SON 23.0 | Senarathna 2024 + monsoon scavenging | qualitative match |
| Diurnal shape | nocturnal plateau ~37; sharp 06 → 10 LT collapse; midday trough 12–15 LT ~7; evening 17–23 LT rebuild | Senarathna 2024 | shape match; morning peak phase off by ~4 h |

Three known limitations are explicitly disclosed: the morning-peak phase error (model 03 LT vs Senarathna 07 LT, attributable to absence of Sri Lankan emission-timing data in training); a negative-value tail (−12 µg/m³ at the extreme, clipped at zero for plotting); and an N = 3 source set with only Kathmandu as a true highland-valley analogue. The Kandy spatial product is therefore held as preliminary, pending the PVAF source-city expansion.

A Sim2Real fine-tune on the two available FECT sensors (Akurana, Hantana) was attempted and produced a negative result: r → 0.9999 at the exact sensor pixels but city-wide annual mean inflated to 37 µg/m³ via wild extrapolation. The model memorised the exact sensor coordinates as identity keys rather than basin physics. This is retained as a documented ablation supporting the case for ≥ 5 spatially diverse sensors.

Anchors are framed as **structural-consistency checks pending field validation**, not as validation in the strict sense. KOALA, Senarathna, and MAIAC each play dual roles as upstream calibration anchors and downstream consistency checks; the framework cannot validate against an anchor it was calibrated to.

---

## Repository Structure

```
ProjectCD/
├── README.md                    This file
├── CLAUDE.md                    Active session instructions (single source of truth for current state)
├── PROJECT.md                   Detailed stage results, architecture, data inventory
├── memory/SESLOG.md             Session log (history of decisions and runs)
├── docs/
│   ├── AUDIT_2026-05-08.md      Hostile peer-review audit and fix log
│   ├── REDESIGN_2026-05-08.md   From-scratch redesign with 16-week schedule
│   ├── kaggle_kernel_log.md     Kaggle kernel run history
│   ├── osf_prereg_*.md          Pre-registrations and amendments
│   ├── pvaf_v1_plan.md          Physics-based Valley Analogue Finder plan
│   └── archive/                 Superseded plans and reports (banner-marked)
├── kandy_pm25/
│   ├── config.py                All paths, constants, city ratios — single source of truth
│   ├── requirements.txt
│   └── src/
│       ├── stage1_satml/        Stage A: XGBoost / LightGBM / CatBoost satellite-ML
│       ├── stage2_transfer/     Stage 2: FourierPINNV3 cross-continental transfer
│       ├── stage3_pinn/
│       │   ├── data/            CityConfig + multi-city loader
│       │   ├── models/
│       │   │   ├── fourier_pinn_v3.py        Active — FourierPINNV3 (76,261 params)
│       │   │   ├── shared_terrain_ansatz.py  Diagnostic reference (rigid Whiteman ansatz)
│       │   │   ├── convcnp_terrain.py        ConvCNP residual learner (Stage C)
│       │   │   └── _archive/                 Pre-pivot v1/v2 PINN models, do not import
│       │   ├── physics/         pde_residual_v3.py + source_kernel.py (active)
│       │   └── training/        train.py (Stage 2); train_convcnp.py (Stage C)
│       └── pvaf/                Physics-based Valley Analogue Finder v1
└── scripts/                     Standalone data-acquisition and validation scripts
```

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

# Build merged Stage A daily dataset
python src/stage1_satml/features/build_dataset.py

# Train Stage A v1 XGBoost + quantile models
python src/stage1_satml/models/train_xgboost.py --no-shap

# Build Stage A v3 hourly residual dataset
python src/stage1_satml/features/build_dataset_v3_hourly.py

# Train v3 base learners and blend
python src/stage1_satml/models/train_lgbm_v3.py
python src/stage1_satml/models/train_catboost_v3.py
python src/stage1_satml/models/train_xgb_v3.py
python src/stage1_satml/models/blend_v3.py
python src/stage1_satml/models/conformal_v3.py

# Stage 2 cross-continental PINN training is run on Kaggle (T4 x2 GPU).
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 .venv/Scripts/kaggle.exe \
    kernels push -p data/processed/stage2/kaggle_kernel_kandy_td_pinn_v7/

# Stage C ConvCNP LOOCV is also run on Kaggle:
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 .venv/Scripts/kaggle.exe \
    kernels push -p data/processed/stage2/kaggle_kernel_convcnp_v14/
```

---

## Data Sources

| Dataset | Resolution | Period | Role |
|---|---|---|---|
| CAMS EAC4 reanalysis | 0.75° / daily | 2003–2025 | Stage A v1 training labels (KOALA-corrected) |
| GEOS-CF PM25_RH35_GCC | 0.25° / hourly | 2018–2026 | Stage B reanalysis prior; Stage C c_prior |
| ERA5 single-level | 0.25° / hourly | 2001–2026 | Wind, BLH, T2m, precipitation |
| ERA5-Land | 0.1° / hourly | 2001–2026 | High-resolution wind, T2m, dewpoint |
| ERA5 pressure levels | 0.25° / hourly | 2018–2025 | T925 (subsidence inversion proxy) |
| MODIS MAIAC AOD (MCD19A2) | 1 km / daily | 2001–2025 | Stage A feature; Stage D consistency anchor |
| TROPOMI NO₂ / CO | ~7 km / daily | 2018–2026 | Stage A and Stage A v3 satellite features |
| VIIRS Nighttime Lights | 500 m / monthly | 2018–2023 | Stage C anthropogenic feature |
| MERRA-2 aerosol | 0.625° / hourly | 2001–2026 | Diagnostic only — rejected as label |
| Van Donkelaar V6GL02.04 | 1 km / annual | 1998–2023 | Stage A triangulation |
| SRTM 30 m DEM | 30 m static | — | Terrain elevation, slope, aspect |
| OpenStreetMap road network | Vector | 2025 | Stage 2 source kernel; Stage C road density |
| KOALA Kandy (Senarathna et al. 2024) | Annual + 12 monthly + diurnal | 2019 | Bias correction and Stage D consistency anchor |
| FECT PurpleAir Kandy (Akurana + Hantana) | Point / hourly | 2018–2026 | Stage A v3 labels (per-sensor calibrated) |
| US Embassy Colombo (AirNow) | Point / hourly | 2019–2026 | Out-of-domain coverage check |
| SIATA Medellín | Point / hourly | 2018–2025 | Stage 2 pre-training; Stage C source |
| Air4Thai + PurpleAir Chiang Mai | Point / hourly | 2021–2025 | Stage 2 transfer; Stage C source |
| AirGradient + GD Labs Kathmandu | Point / hourly | Oct 2025 – May 2026 | Stage C source |

---

## Key Methodological Notes

- **No Sri Lankan ground sensors during Stage C / D training.** The Stage C model is trained entirely on Medellín / Chiang Mai / Kathmandu and applied zero-shot to Sri Lankan targets. The two FECT sensors in Kandy are used in Stage A v3 (Akurana, Hantana) and held entirely out of Stage C training to preserve the zero-shot framing.
- **Pre-Kandy physics transfer.** FourierPINNV3 is pre-trained on Medellín, then validated on Chiang Mai (held-out stations never seen during training) before any Kandy application — the only pre-Kandy physics-validation opportunity available.
- **Pure-data Phase-1 warm-start rule.** Cross-domain TD-PDE transfer requires initialising from a Phase-1 checkpoint (λ_pde = 0). Inoculated progressive warm-starts and Phase-3 checkpoints lock the K–BLH relationship to source-domain geography and fail to adapt.
- **Residual learning at the spatial step.** Stage C predicts `pm25 − c_prior_scaled`, not pm25 directly. This makes the reanalysis prior's contribution explicit rather than implicit, and prevents claiming model skill that is in fact reanalysis interpolation.
- **Native resolution 1 km hourly.** GEOS-CF (0.25°) and ERA5 (0.25°) have no spatial structure below ~25 km; resolving below 1 km from these inputs is fictional. The optional 100 m kernel disaggregation is presentation-only.
- **Uncertainty quantification.** Quantile regression on Stage A v1; CV+ Mondrian conformal on Stage A v3; Student-t likelihood + per-(city × hour-of-day) Mondrian conformal on Stage C. Coverage and calibration are reported alongside every r / RMSE.
- **Stage 2 / 3 PINN domain.** 15 × 15 km centred on Kandy (KANDY_PINN_BBOX: 7.2230–7.3582 °N, 80.5660–80.7014 °E), 150 × 150 grid at 100 m for inputs; outputs reported at 1 km native.
- **Multi-target zero-shot.** The framework is applied at three Sri Lankan highland targets (Kandy, Nuwara Eliya, Badulla) to demonstrate that cross-city training generalises to multiple unmonitored cities, not just the original target.
- **Quasi-steady-state PDE rejected.** Tested as v8 / v9 in the spatial-attractor era; structural failure (negative R² with high r(K, BLH)). Time-dependent advection–diffusion is the only PDE form used.
- **Fixed Whiteman terrain ansatz rejected.** SharedTerrainAnsatz combined_v2 demonstrated identifiability collapse across heterogeneous tropical valleys (six learnable parameters all converging to bound constraints). This motivated the data-driven Stage C architecture and is retained as a diagnostic reference.
- **Reproducibility.** All Kaggle kernels, dataset versions, and per-version metric tables are logged in `docs/kaggle_kernel_log.md`. Pre-registrations and amendments live in `docs/osf_prereg_*.md`.

---

*This document mirrors the canonical state in [`CLAUDE.md`](CLAUDE.md) and [`PROJECT.md`](PROJECT.md). If you find a discrepancy between this README and the canonical state files, the canonical state files take precedence and this README is wrong.*
