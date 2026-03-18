# Physics-Informed Neural Networks with Transfer Learning for Spatiotemporal PM2.5 Estimation in Kandy, Sri Lanka

**Undergraduate thesis** — Daminda Alahakoon, Department of Environmental Sciences,
University of Peradeniya | Target completion: October 2026 | Working model: May 2026

---

## Overview

Kandy, Sri Lanka has no operational PM2.5 monitoring network. This project develops a
three-stage cascaded framework to estimate PM2.5 at 100 m / 30 min resolution using
satellite observations, reanalysis meteorology, and physics-constrained deep learning —
with no ground sensors required during training.

### Three-Stage Framework

```
Stage 1 — Satellite-ML (XGBoost)
  Inputs : MODIS AOD, TROPOMI NO₂/CO/AER_AI, ERA5 meteorology, topographic features
  Output : Daily domain-mean PM2.5 + pixel-level spatial disaggregation (1 km)
  Status : COMPLETE — LOMO R²=0.631, RMSE=4.82 µg/m³

         |
         | Stage 1b pixel predictions as pseudo-label boundary conditions
         v

Stage 2 — Transfer Learning (Medellín → Chiang Mai)
  Pre-train FourierPINN physics backbone on Medellín (11 SIATA stations)
  Fine-tune on Chiang Mai pseudo-labels; validate vs 3 held-out Air4Thai stations
  Status : COMPLETE — ChiangMai v5 ep4000: R²=0.715, r_kblh=0.974 (no PDE explosion)

         |
         | Pretrained physics backbone (Medellín v8 ep1000, pure-data Phase 1)
         v

Stage 3 — PINN (Physics-Informed Neural Network)
  Domain  : 15 × 15 km, 150 × 150 grid at 100 m resolution
  Physics : Anisotropic advection-diffusion with dry deposition + BLH-dependent K
  Output  : PM2.5(x, y, t) at 100 m / 30 min over Kandy valley
  Status  : All gaps closed — ready for Kaggle training run
```

---

## Stage 1 Results (FINAL)

| Metric | Value |
|---|---|
| LOMO Overall R² | **0.631** |
| Temporal CV R² | 0.537 |
| Train-fit R² | 0.760 |
| RMSE | 4.82 µg/m³ |
| 90% PI coverage | 89.4% (target > 85%) |
| PI width | 17.6 µg/m³ |
| KOALA 2019 validation r | 0.515 (bias +0.09 µg/m³) |
| Training period | 2003–2025 (8,279 days) |
| Features | 44 |

**Top SHAP drivers:** wind_speed (3.594), pm25_prev_month_mean (0.809), rwp (0.641),
vvc (0.577), aod_blh_ratio (0.555)

**Monthly LOMO R²:** Jan 0.535 · Feb 0.341 · Mar 0.335 · Apr 0.193 · May 0.409 ·
Jun 0.137 · Jul 0.279 · Aug 0.319 · Sep 0.399 · Oct 0.588 · Nov 0.617 · Dec 0.663

Low R² in Jun–Aug is structural (SW monsoon suppresses PM2.5 variance, CoV < 0.15),
not a modelling failure.

---

## Stage 2 Results (COMPLETE — 2026-03-18)

### Medellín PINN v9 (pre-training domain)

| Metric | Value |
|---|---|
| Best checkpoint | ep3800 (Phase 3) |
| Spatial R² | 0.971 (ep2400 peak) |
| r(K, BLH) | 0.995 (Phase 3) |
| PDE explosion? | No — EMA normalisation + inoculation fix applied |

### Chiang Mai PINN v5 (transfer validation domain)

Warm-started from Medellín v8 ep1000 (pure-data Phase 1, λ_pde=0 throughout).
Trains through all 3 phases without PDE explosion for the first time.

| Metric | ep1100 (best combined) | ep4000 (best Phase 3) | Target |
|---|---|---|---|
| Spatial R² vs Air4Thai | **0.823** | **0.715** | > 0.70 |
| r(K, BLH) | 0.614 | **0.974** | > 0.50 |
| Mean bias | −0.112 µg/m³ | −0.383 µg/m³ | < 5 µg/m³ |
| PDE explosion? | No | No | ✅ |

**Transfer rule validated:** Warm-starting from a pure-data Phase-1 checkpoint
(λ_pde=0 throughout Phase 1) is mandatory for cross-domain transfer. Inoculated
Phase-1 checkpoints and Phase-3 checkpoints both failed (v3, v4).

---

## Stage 3 Architecture

**Model:** FourierPINNV3 — 76,261 parameters (Kaggle kernel variant)

- SpatialEmbedding: dual-scale Fourier features (σ=1.0, σ=3.0; 64+64 frequencies)
- TrunkNet: ResNet blocks with BLH and elevation conditioning
- AlphaNet: diurnal source modulation via sin/cos hour encoding
- Road kernel: wired via `F.grid_sample` on OSM-derived proximity field

**PDE:** Steady-state advection-diffusion `u·∇C = ∇·(K∇C) − v_d·C + S`
with BLH-dependent isotropic diffusivity K.

**Training fixes applied (I1–I4, S1–S4):**
- I1: EMA normalisation of L_pde (prevents Phase 2 explosion)
- I2: PDE inoculation (λ_pde=0.001 from epoch 0 — no cold PDE shock)
- I3: Coordinates standardised to [−1, 1]; alpha_x = 2/lx_m
- I4: Data-dominant curriculum (λ_data > λ_pde at all epochs)
- S1: SpatialEmbedding B-matrices registered as nn.Module buffers
- S2: Gradient clipping max_norm=5.0
- S4: Real DEM elevation (kandy_elev_grid_100m.npz, 431–1277 m) wired to PDE

---

## Repository Structure

```
ProjectCD/
├── .gitignore               Policy: only kandy_pm25/src/** and config.py tracked
├── README.md
└── kandy_pm25/
    ├── config.py             Central configuration — all paths, constants, parameters
    ├── requirements.txt      Python package dependencies
    ├── run_pipeline.py       Master pipeline runner
    ├── SETUP_GUIDE.md        Installation and environment setup
    └── src/
        ├── stage1_satml/     Stage 1: Satellite-ML (XGBoost)
        │   ├── features/     build_dataset.py, spatial_disaggregate.py, topo_features.py
        │   ├── models/       train_xgboost.py, train_pixel_xgboost.py, quantile models
        │   ├── evaluation/   blocked_cv.py, calibration.py
        │   └── visualization/ shap_analysis.py, spatial_maps.py
        ├── stage2_transfer/  Stage 2: Transfer learning (Medellín → Chiang Mai)
        │   ├── pretrain/     train_medellin_pinn.py
        │   ├── validate/     validate_chiangmai.py
        │   ├── chiangmai_build_dataset.py
        │   ├── chiangmai_terrain.py
        │   ├── chiangmai_train_stage1.py
        │   ├── download_gee_chiangmai.py
        │   └── train_chiangmai_pinn.py
        ├── stage3_pinn/      Stage 3: Physics-Informed Neural Network (Kandy)
        │   ├── models/       fourier_pinn_v3.py
        │   ├── physics/      pde_residual_v3.py
        │   └── training/     train.py
        ├── utils/            plot_style.py (IEEE figures, PM25_CMAP, save_figure)
        └── comparison/       Cross-stage comparison and publication figures
```

---

## Setup

```bash
# 1. Create virtual environment
cd kandy_pm25
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Authenticate APIs (one-time)
cdsapi-config                   # ERA5/CAMS via Copernicus ADS
earthengine authenticate        # Google Earth Engine
```

See [kandy_pm25/SETUP_GUIDE.md](kandy_pm25/SETUP_GUIDE.md) for detailed setup.

---

## Key Commands

```bash
# All commands run from kandy_pm25/

# Build merged dataset (ERA5 + MODIS + TROPOMI + topographic features)
python src/stage1_satml/features/build_dataset.py

# Train Stage 1a XGBoost + quantile models
python src/stage1_satml/models/train_xgboost.py --no-shap

# Train Stage 1b pixel-level spatial disaggregation model
python src/stage1_satml/features/spatial_disaggregate.py
python src/stage1_satml/models/train_pixel_xgboost.py --no-shap

# Stage 2 Medellín PINN training (Kaggle GPU — use kernel in data/processed/stage2/)
# See data/processed/stage2/kaggle_kernel_medellin_pinn/

# Stage 2 Chiang Mai PINN training (Kaggle GPU — use kernel in data/processed/stage2/)
# See data/processed/stage2/kaggle_kernel_chiangmai_pinn/

# Stage 3 Kandy PINN training (Kaggle GPU, warm-start from Medellín v8 ep1000)
python src/stage3_pinn/training/train.py --model v3 --epochs 5000 --wandb
```

---

## Data Sources

| Dataset | Coverage | Status |
|---|---|---|
| ERA5 reanalysis (surface + 925 hPa) | 2000–2025 | Complete |
| MODIS AOD (Terra MCD19A2) | 2000–2025 | Complete |
| TROPOMI NO₂ / CO / AER_AI | 2018–2025 | Complete |
| CAMS EAC4 PM2.5 reanalysis | 2003–2025 | Complete |
| Van Donkelaar V6GL02.04 satellite PM2.5 | 1998–2023 | Complete |
| SRTM 30 m DEM | Static | Complete |
| Medellín SIATA PM2.5 (Stage 2) | 2018–2019 | Complete |
| Chiang Mai Air4Thai + ERA5 (Stage 2) | 2022 | Complete |
| Kandy 100 m elevation grid | Static | Complete (431–1277 m) |
| Kandy OSM road kernel | Static | Complete (97.5% non-zero) |
| Kandy Stage 1 pseudo-labels (150×150) | 2003–2025 | Complete (8,401 days) |

---

## Key Design Decisions

- **No ground sensors required during training:** PM2.5 labels derived from satellite
  reanalysis (CAMS EAC4) corrected against KOALA multi-year monitoring data
  (Senarathna et al. 2024, CJS 53(2):197–206). Cross-validated against Van Donkelaar
  V6GL02.04 satellite PM2.5 climatology.
- **Transfer learning before Kandy:** FourierPINNV3 is pre-trained on Medellín (data-rich
  valley city with 11 monitoring stations), then validated on Chiang Mai (3 held-out stations
  never seen during training) before applying to Kandy. This is the only pre-Kandy
  opportunity to verify that the PINN learns real physics, not noise.
- **Pure-data Phase-1 warm-start rule:** Cross-domain transfer requires a warm-start
  checkpoint from a Phase 1 where λ_pde=0 throughout. Inoculated or Phase-3 checkpoints
  lock the K–BLH relationship to the source domain geography and fail to adapt.
- **Uncertainty quantification:** Quantile regression (q05/q50/q95) on Stage 1 outputs
  propagates prediction uncertainty as inverse-variance boundary condition weights into Stage 3.
- **Stage 3 domain:** 15 × 15 km centred on Kandy city
  (7.2230–7.3582°N, 80.5660–80.7014°E), 150 × 150 grid at 100 m.
- **Physics-first Stage 3:** Raw PyTorch autograd throughout — no third-party PINN frameworks.
- **Multi-fidelity cascaded framework** (Peherstorfer et al. 2018): Stage 1 uncertainty
  enters Stage 3 as scalar inverse-variance weights on boundary conditions.

---

## Citation

If you use this code or methodology, please cite:

> Alahakoon, D. (2026). *Physics-Informed Neural Networks with Transfer Learning for
> Spatiotemporal PM2.5 Dispersion Modeling in Kandy, Sri Lanka.* Undergraduate thesis,
> Department of Environmental Sciences, University of Peradeniya.
