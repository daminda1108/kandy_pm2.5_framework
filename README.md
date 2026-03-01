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
  Status : COMPLETE — LOMO R²=0.607, RMSE=4.33 µg/m³

         |
         | Stage 1b pixel predictions as boundary conditions
         v

Stage 2 — Transfer Learning (Medellín → Chiang Mai → Kandy)
  Pre-train PINN physics backbone on Medellín (data-rich valley city)
  Validate transfer on Chiang Mai before applying to Kandy
  Status : Data downloaded; pre-training pipeline coded

         |
         | Pretrained physics backbone
         v

Stage 3 — PINN (Physics-Informed Neural Network)
  Domain  : 15 × 15 km, 150 × 150 grid at 100 m resolution
  Physics : Anisotropic advection-diffusion with dry/wet deposition
  Output  : PM2.5(x, y, t) at 100 m / 30 min over Kandy valley
  Status  : Architecture complete; awaits Stage 2 backbone
```

---

## Stage 1 Results (FINAL)

| Metric | Value |
|---|---|
| LOMO Overall R² | 0.607 |
| Temporal CV R² | 0.537 |
| Train-fit R² | 0.790 |
| RMSE | 4.33 µg/m³ |
| 90% PI coverage | 88.5% (target >85%) |
| PI width | 12.3 µg/m³ |
| Training period | 2003–2025 (8,401 days) |
| Features | 44 |

**Top SHAP drivers:** wind_speed (3.21), rwp (0.58), aod_blh_ratio (0.55),
aod_modis (0.48), vvc (0.40)

**Monthly LOMO R²:** Jan 0.543 · Feb 0.200 · Mar 0.351 · Apr 0.134 · May 0.366 ·
Jun 0.147 · Jul 0.156 · Aug 0.267 · Sep 0.322 · Oct 0.544 · Nov 0.597 · Dec 0.649

Low R² in Jun–Aug is structural (SW monsoon suppresses PM2.5 variance, CoV < 0.15),
not a modelling failure.

---

## Repository Structure

```
ProjectCD/
├── .gitignore
├── README.md
└── kandy_pm25/
    ├── config.py              Central configuration — all paths, constants, parameters
    ├── requirements.txt       Python package dependencies
    ├── run_pipeline.py        Master pipeline runner (single entry point)
    ├── SETUP_GUIDE.md         Installation and environment setup
    └── src/
        ├── stage1_satml/      Stage 1: Satellite-ML (XGBoost)
        │   ├── features/      build_dataset.py, topo_features.py, meteo_features.py
        │   ├── models/        train_xgboost.py, train_pixel_xgboost.py, quantile models
        │   ├── evaluation/    blocked_cv.py, calibration.py, validate_van_donkelaar.py
        │   └── visualization/ shap_analysis.py, spatial_maps.py
        ├── stage2_transfer/   Stage 2: Transfer learning
        │   ├── pretrain/      pretrain_medellin.py, layer_freezing.py
        │   ├── validate/      validate_chiangmai.py
        │   └── analysis/      domain_shift.py, transfer_diagnostics.py
        ├── stage3_pinn/       Stage 3: Physics-Informed Neural Network
        │   ├── domain/        boundary_conditions.py, kandy_domain.py
        │   ├── models/        fourier_pinn.py, pinn_steady.py, pinn_transient.py
        │   ├── physics/       advection_diffusion.py, constraints.py, source_term.py
        │   ├── training/      train.py, curriculum.py, collocation.py, loss_functions.py
        │   └── analysis/      discover_diffusivity.py, uncertainty_maps.py
        └── comparison/        Cross-stage comparison and publication figures
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
cdsapi-config                   # ERA5 via Copernicus ADS
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

# SHAP feature importance
python -c "from kandy_pm25.src.stage1_satml.visualization.shap_analysis import run_shap_analysis; run_shap_analysis()"

# Stage 2 pre-training (Medellín)
python src/stage2_transfer/pretrain/pretrain_medellin.py --epochs 500

# Stage 2 Chiang Mai transfer validation
python src/stage2_transfer/validate/validate_chiangmai.py

# Stage 3 PINN training
python src/stage3_pinn/training/train.py --init A --epochs 1000
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
| MERRA-2 ensemble labels | 2003–2025 | Downloaded, pending integration |
| Medellín SIATA PM2.5 (Stage 2) | 2018–2019 | Downloaded |
| Chiang Mai PCD + PurpleAir (Stage 2) | 2022 | Downloaded |

---

## Key Design Decisions

- **No ground sensors required during training:** PM2.5 labels are derived from satellite
  reanalysis products and cross-validated against an independent multi-year satellite
  climatology (Van Donkelaar et al. 2021, V6GL02.04).
- **Uncertainty quantification:** Quantile regression (q05/q50/q95) on Stage 1 outputs
  propagates prediction uncertainty as inverse-variance boundary condition weights into Stage 3.
- **Stage 3 domain:** 15 × 15 km centred on Kandy city
  (7.2230–7.3582°N, 80.5660–80.7014°E), 150 × 150 grid at 100 m.
  Terrain blocking index computed from SRTM 30 m DEM.
- **Physics-first Stage 3:** Raw PyTorch autograd throughout — no third-party PINN frameworks.
  Anisotropic advection-diffusion with dry and wet deposition terms parameterised from
  published aerosol physics literature.
- **Multi-fidelity cascaded framework:** Stage 1 uncertainty enters Stage 3 as scalar
  inverse-variance weights on boundary conditions, following Peherstorfer et al. (2018).

---

## Pending Work

1. MERRA-2 ensemble label integration — run `process_merra2.py`, rebuild dataset, retrain
2. Stage 2 data wiring — fix loader paths in `pretrain_medellin.py` / `validate_chiangmai.py`
3. Stage 2 Medellín pre-training — once data wiring is complete
4. Stage 3 PINN training — after Stage 2 backbone is available
5. Diagnose 2021–2025 performance trend

---

## Citation

If you use this code or methodology, please cite:

> Alahakoon, D. (2026). *Physics-Informed Neural Networks with Transfer Learning for
> Spatiotemporal PM2.5 Dispersion Modeling in Kandy, Sri Lanka.* Undergraduate thesis,
> Department of Environmental Sciences, University of Peradeniya.
