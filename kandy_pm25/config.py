"""
config.py — Central configuration for the Kandy PM2.5 sequential framework.
All paths, coordinates, constants, and parameters are defined here.
Import this module in every other script.
"""

from pathlib import Path

# ─────────────────────────────────────────────
# GOOGLE EARTH ENGINE
# ─────────────────────────────────────────────

GEE_PROJECT = "kandypinn"

# ─────────────────────────────────────────────
# STUDY AREA
# ─────────────────────────────────────────────

# Broad bounding box for satellite data downloads (ERA5, MODIS, TROPOMI)
KANDY_BBOX = {
    "lat_min": 7.10,
    "lat_max": 7.50,
    "lon_min": 80.45,
    "lon_max": 80.85,
}

# PINN domain: 15×15 km centred on Kandy city centre
# Justified by ERA5 grid scale (~28km) — captures all sub-grid terrain
# including Hantana (SW, 7km) and Knuckles massif (NE, 18-28km)
KANDY_CENTRE_LAT = 7.2906
KANDY_CENTRE_LON = 80.6337

_HALF_DEG_LAT = 0.0676   # 7.5 km / 111.0 km per degree
_HALF_DEG_LON = 0.0677   # 7.5 km / (111.0 × cos(7.29°))

KANDY_PINN_BBOX = {
    "lat_min": round(KANDY_CENTRE_LAT - _HALF_DEG_LAT, 6),  # 7.2230°N
    "lat_max": round(KANDY_CENTRE_LAT + _HALF_DEG_LAT, 6),  # 7.3582°N
    "lon_min": round(KANDY_CENTRE_LON - _HALF_DEG_LON, 6),  # 80.5660°E
    "lon_max": round(KANDY_CENTRE_LON + _HALF_DEG_LON, 6),  # 80.7014°E
}

# Central coordinates
KANDY_CENTER = {"lat": 7.2906, "lon": 80.6337}

# ─────────────────────────────────────────────
# TIME RANGE
# ─────────────────────────────────────────────

DATA_START_YEAR  = 2000
DATA_END_YEAR    = 2025   # inclusive; 25 years of data
DATA_START_MONTH = 1
DATA_END_MONTH   = 12

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────

ROOT_DIR = Path(__file__).parent          # kandy_pm25/
DATA_DIR = ROOT_DIR / "data"

# Raw downloads
RAW_DIR         = DATA_DIR / "raw"
MODIS_RAW_DIR   = RAW_DIR / "modis_aod"
TROPOMI_RAW_DIR = RAW_DIR / "tropomi"
ERA5_RAW_DIR    = RAW_DIR / "era5"
CAMS_RAW_DIR    = RAW_DIR / "cams"          # CAMS EAC4 PM2.5 — gap-fill + co-variate
DEM_RAW_DIR     = RAW_DIR / "dem"
LC_RAW_DIR      = RAW_DIR / "land_cover"
NDVI_RAW_DIR    = RAW_DIR / "ndvi"
GT_RAW_DIR      = RAW_DIR / "ground_truth"
MERRA2_RAW_DIR  = RAW_DIR / "merra2"          # MERRA-2 aerosol PM2.5
VAN_DONKELAAR_DIR = RAW_DIR / "van_donkelaar"  # Van Donkelaar V5.GL.04 annual PM2.5


# Processed
PROC_DIR        = DATA_DIR / "processed"
FEATURES_DIR    = PROC_DIR / "features"
MERGED_DIR      = PROC_DIR / "merged"
PINN_INPUT_DIR  = PROC_DIR / "pinn_inputs"

# External reference products (Stage 2 cities)
EXTERNAL_DIR        = DATA_DIR / "external"

MEDELLIN_DATA_DIR   = EXTERNAL_DIR / "medellin"
MEDELLIN_PM25_DIR   = MEDELLIN_DATA_DIR / "pm25"
MEDELLIN_ERA5_DIR   = MEDELLIN_DATA_DIR / "era5"
MEDELLIN_DEM_DIR    = MEDELLIN_DATA_DIR / "dem"

CHIANGMAI_DATA_DIR  = EXTERNAL_DIR / "chiangmai"
CHIANGMAI_PM25_DIR  = CHIANGMAI_DATA_DIR / "pm25"
CHIANGMAI_ERA5_DIR  = CHIANGMAI_DATA_DIR / "era5"
CHIANGMAI_DEM_DIR   = CHIANGMAI_DATA_DIR / "dem"

# ⚠ STAGE 2 WIRING NOTE (2026-02-28):
# config.py paths above are CORRECT (data/external/{medellin,chiangmai}).
# However, the Stage 2 scripts hardcode their own stale paths to data/raw/:
#   pretrain_medellin.py: MEDELLIN_RAW_DIR = data/raw/medellin  ← WRONG
#   validate_chiangmai.py: CM_RAW_DIR       = data/raw/chiangmai ← WRONG
# Fix these in the Stage 2 data-wiring session by replacing hardcoded paths
# with MEDELLIN_DATA_DIR / CHIANGMAI_DATA_DIR imported from config.
# Also: pretrain_medellin.py globs "siata_pm25_*.csv" but file is
# "medellin_pm25_raw.csv"; validate_chiangmai.py globs "pcd_chiangmai_pm25*.csv"
# but file is "chiangmai_pm25_raw_2022.csv". Column "pm25_ugm3" → "pm25".

# Results
RESULTS_DIR     = ROOT_DIR / "results"
FIGURES_DIR     = RESULTS_DIR / "figures"
TABLES_DIR      = RESULTS_DIR / "tables"
MODELS_DIR      = RESULTS_DIR / "models"
VALIDATION_DIR  = RESULTS_DIR / "validation"

# ─────────────────────────────────────────────
# ERA5 CONFIGURATION
# ─────────────────────────────────────────────

ERA5_SINGLE_LEVEL_VARIABLES = [
    "10m_u_component_of_wind",      # u
    "10m_v_component_of_wind",      # v
    "2m_temperature",               # T2m
    "2m_dewpoint_temperature",      # Td2m → RH
    "surface_pressure",             # SP
    "total_precipitation",          # TP
    "boundary_layer_height",        # BLH  ← most critical
    "surface_solar_radiation_downwards",  # SSRD
    "total_column_water_vapour",    # TCWV
]

ERA5_PRESSURE_LEVEL_VARIABLES = [
    "temperature",                  # For 925 hPa inversion detection
    "geopotential",
]

ERA5_PRESSURE_LEVELS = ["925", "850", "700"]

# ERA5-Land at ~9 km — for better skin temperature
ERA5_LAND_VARIABLES = [
    "2m_temperature",
    "skin_temperature",
    "2m_dewpoint_temperature",
]

# ERA5 grid resolution (degrees)
ERA5_RESOLUTION = 0.25       # Single levels
ERA5_LAND_RESOLUTION = 0.1   # ERA5-Land

# ─────────────────────────────────────────────
# MODIS MAIAC AOD CONFIGURATION
# ─────────────────────────────────────────────

MODIS_PRODUCT   = "MCD19A2.061"   # MAIAC Land AOD, Collection 6.1
MODIS_AOD_BAND  = "AOD_55"        # 550 nm AOD channel
MODIS_QA_BAND   = "AOD_QA"        # Quality assurance flags
MODIS_AOD_SCALE = 0.001           # Scale factor to apply
MODIS_AOD_MIN   = 0.0             # Valid AOD range
MODIS_AOD_MAX   = 5.0

# ─────────────────────────────────────────────
# TROPOMI CONFIGURATION
# ─────────────────────────────────────────────

TROPOMI_COLLECTIONS = {
    "NO2":  "S5P_OFFL_L2__NO2____",
    "CO":   "S5P_OFFL_L2__CO_____",
    "AER_AI": "S5P_OFFL_L2__AER_AI_",
    "AER_LH": "S5P_OFFL_L2__AER_LH_",
}
TROPOMI_QA_THRESHOLD = 0.5   # Minimum QA value (0–1)

# ─────────────────────────────────────────────
# HIMAWARI-8 AHI — NOT USABLE FOR SRI LANKA
# ─────────────────────────────────────────────
# Geostationary at 140.7°E. Full disk covers ~80°E to ~160°W.
# Sri Lanka is at 80.6°E — extreme western edge, high viewing zenith angle.
# AOD retrievals unreliable at limb geometry. DO NOT USE for Kandy.
# Kept for reference only.

HIMAWARI_RAW_DIR       = RAW_DIR / "himawari"

# ─────────────────────────────────────────────
# TOPOGRAPHY FEATURE CONSTANTS
# ─────────────────────────────────────────────

# Valley depth reference — approximate depth of Kandy bowl (m)
KANDY_VALLEY_DEPTH_M = 400.0

# TPI (Topographic Position Index) search radius
TPI_RADIUS_M = 2000.0  # 2 km neighbourhood

# Katabatic Flow Proxy — slope temperature gradient threshold (°C/m)
KATABATIC_TEMP_LAPSE = 0.0065   # Dry adiabatic lapse rate (K/m)

# Thermal Inversion Index pressure level (hPa)
INVERSION_PRESSURE_LEVEL = 925  # Compare T925 vs surface

# ─────────────────────────────────────────────
# MODEL CONFIGURATION (Stage 1)
# ─────────────────────────────────────────────

XGBOOST_DEFAULT_PARAMS = {
    "n_estimators":     500,
    "learning_rate":    0.05,
    "max_depth":        6,
    "subsample":        0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 3,
    "reg_alpha":        0.1,
    "reg_lambda":       1.0,
    "objective":        "reg:squarederror",
    "eval_metric":      "rmse",
    "n_jobs":           -1,
    "random_state":     42,
    "early_stopping_rounds": 50,
}

LIGHTGBM_DEFAULT_PARAMS = {
    "n_estimators":     500,
    "learning_rate":    0.05,
    "num_leaves":       63,
    "max_depth":        -1,
    "subsample":        0.8,
    "colsample_bytree": 0.8,
    "min_child_samples": 20,
    "reg_alpha":        0.1,
    "reg_lambda":       1.0,
    "objective":        "regression",
    "metric":           "rmse",
    "n_jobs":           -1,
    "random_state":     42,
    "verbose":          -1,
}

RANDOM_FOREST_DEFAULT_PARAMS = {
    "n_estimators": 300,
    "max_depth":    None,
    "max_features": "sqrt",
    "min_samples_split": 5,
    "min_samples_leaf":  2,
    "n_jobs":       -1,
    "random_state": 42,
}

# Cross-validation strategy (§1.5 of design doc)
CV_FOLDS        = 5
CV_STRATEGIES   = ["temporal", "blocked_spatial", "leave_season_out"]
CV_DEFAULT      = "temporal"  # Primary; all three required for paper
TRAIN_TEST_RATIO = 0.8

# Uncertainty quantification — quantile regression (§1.6)
QUANTILE_ALPHAS = [0.05, 0.50, 0.95]  # 90% prediction intervals

# ─────────────────────────────────────────────
# TRANSFER PRE-TRAINING CONFIGURATION (Stage 2)
# ─────────────────────────────────────────────

# Cities used for transfer learning
TRANSFER_PRETRAIN_CITY   = "medellin"    # Pre-training source city
TRANSFER_VALIDATE_CITY   = "chiangmai"   # Held-out validation city (never seen during pre-training)

# Bounding boxes for external cities
MEDELLIN_BBOX  = (-75.65, 6.17, -75.52, 6.31)    # lon_min, lat_min, lon_max, lat_max
CHIANGMAI_BBOX = (98.93,  18.70, 99.07,  18.87)

# Pre-training loss weights (physics-dominant phase)
PRETRAIN_LAMBDA_PHYSICS = 1.0
PRETRAIN_LAMBDA_DATA    = 0.5

# Validation gate thresholds (Stull 1988 bounds)
TRANSFER_K_MIN_M2S  = 1.0     # Minimum physically valid K (m²/s)
TRANSFER_K_MAX_M2S  = 100.0   # Maximum physically valid K (m²/s)
TRANSFER_PDE_THRESH = 0.1     # Max normalised PDE residual to pass validation gate
TRANSFER_FINETUNE_EPOCHS = 100  # Minimal fine-tune epochs on Chiang Mai for gate check

# Layer-freezing strategy during Kandy fine-tuning (Stage 3)
# Layers 0-3: universal physics (freeze); Layers 4-5: city-specific (unfreeze)
FROZEN_LAYERS = [0, 1, 2, 3]

# ─────────────────────────────────────────────
# PINN CONFIGURATION (Stage 3 — Kandy PINN)
# ─────────────────────────────────────────────

# Fourier feature embedding (Tancik et al. 2020) — combats spectral bias at 100m
FOURIER_N     = 256   # Number of Fourier basis functions (doubled for 100m)
FOURIER_SIGMA = 20.0  # Frequency scale; increased for 100m-scale features

# Anisotropic diffusivity: PINN learns [Kx, Ky] separately
# Expected: Kx > Ky along Kandy's NE-SW valley axis
PINN_OUTPUTS  = ["C", "Kx", "Ky"]   # Three-output PINN

# PINN_DOMAIN dict removed 2026-02-28
# Superseded by KANDY_PINN_BBOX (15×15 km domain, 7.2230–7.3582°N, 80.5660–80.7014°E)
# See KANDY_PINN_BBOX defined above

# Grid resolution for PINN output — 100m target
# At lat 7.29°N: 1° lon ≈ 110.0 km, 1° lat ≈ 111.2 km
# 100m ≈ 0.0009° (0.0009 × 111,000 ≈ 99.9m)
PINN_OUTPUT_RESOLUTION_DEG = 0.0009  # ~100 m at Kandy latitude
PINN_HOURS   = 48    # 30-min time steps per day (was 24 hourly)

PINN_NETWORK = {
    "hidden_layers": 5,
    "neurons_per_layer": 64,
    "activation": "tanh",
    "dropout_p": 0.1,  # MC Dropout probability (§2.8)
}

PINN_TRAINING = {
    "n_boundary_points": 900,    # Boundary condition points (scaled for 100m grid)
    "n_data_points":     5000,   # Points where Stage 1 daily-mean constraint applies
    "epochs_warmup":     3000,   # Data-only pre-training (Phase 1 of §7.2)
    "epochs_physics":    12000,  # Physics-included training (Phase 2-3)
    "lr_warmup":         1e-3,
    "lr_physics":        1e-4,
    "lambda_data":       1.0,    # Data loss weight (scaled by inverse Stage 1 uncertainty)
    "lambda_pde":        0.01,   # PDE residual loss weight (start low, cosine schedule)
    "lambda_phys":       0.001,  # Physical constraint weight (K>0, C≥0)
}

# Collocation point sampling strategy for L_pde (§7.2)
PINN_COLLOCATION_STRATEGY = "random"  # "random" | "uniform" | "rar" (residual-adaptive)
PINN_N_COLLOCATION = 5000             # N points per training step (scaled for 100m grid)
PINN_RAR_TOP_FRAC  = 0.20             # Top-20% residual pixels get 50% of budget (for "rar")

# Collocation sampling — scaled for 15×15 km domain
# Interior: ~80% of grid points sampled per batch
# Boundary: proportional to larger perimeter (60km vs previous 33km)
PINN_N_COLLOCATION_INTERIOR = 8000   # was 5000
PINN_N_COLLOCATION_BOUNDARY = 1500   # was 900

# Curriculum warmup — extended for more heterogeneous 15×15 km terrain
PINN_WARMUP_EPOCHS = 200   # was 100 — Hantana + Knuckles terrain needs longer settle

# Daily-mean constraint batching mode (§7.2)
# "parallel"  = stack all 24 hours, single forward pass (recommended)
# "stochastic" = sample k=6 random hours (faster, noisier)
PINN_DAILY_MEAN_MODE = "parallel"
PINN_STOCHASTIC_K    = 6              # Hours per step if mode="stochastic"

# MC Dropout for Stage 2 UQ (§2.8)
MC_DROPOUT_N = 30   # Number of forward passes for uncertainty estimation

# Fixed deposition velocity — NOT learned (§2.11)
# Dry deposition for PM2.5 over urban surfaces: 0.001–0.01 m/s (Seinfeld & Pandis)
V_DEPOSITION = 0.003  # m/s — midpoint for urban PM2.5
V_DEPOSITION_SENSITIVITY = [0.001, 0.003, 0.01]  # For sensitivity tests

# ─────────────────────────────────────────────
# STAGE 3 PINN — FLAT ALIASES & DERIVED CONSTANTS
# (used by stage3_pinn modules; derived from dicts above)
# ─────────────────────────────────────────────

# FourierPINN architecture (flat aliases for import convenience)
PINN_FOURIER_FEATURES = FOURIER_N       # 256 random Fourier basis functions
PINN_FOURIER_SIGMA    = FOURIER_SIGMA   # Frequency scale σ = 20.0
PINN_HIDDEN_LAYERS    = PINN_NETWORK["hidden_layers"]      # 5
PINN_HIDDEN_UNITS     = PINN_NETWORK["neurons_per_layer"]  # 64

# Training hyper-parameters (flat aliases)
PINN_EPOCHS = PINN_TRAINING["epochs_physics"]   # 12 000
PINN_LR     = PINN_TRAINING["lr_physics"]       # 1e-4

# Collocation point counts (flat aliases)
N_COLLOCATION_INTERIOR = PINN_N_COLLOCATION_INTERIOR   # 8 000
N_COLLOCATION_BOUNDARY = PINN_N_COLLOCATION_BOUNDARY   # 1 500

# Physically plausible K bounds (flat aliases from transfer validation gate)
K_MIN_MS2 = TRANSFER_K_MIN_M2S   # 1.0  m²/s
K_MAX_MS2 = TRANSFER_K_MAX_M2S   # 100.0 m²/s

DOMAIN_LON_EXTENT_KM = 15.0   # was ~11.1
DOMAIN_LAT_EXTENT_KM = 15.0   # was ~5.55

# Grid resolution
# Development runs: 150m (100×100 = 10,000 pts, ~2h CPU per training run)
# Final publication: 100m (150×150 = 22,500 pts, ~5h CPU / ~40min GPU)
PINN_GRID_RESOLUTION_M = 100   # Final publication resolution (exact integer — no truncation)

# ─────────────────────────────────────────────
# PHYSICAL CONSTANTS
# ─────────────────────────────────────────────

G_MS2         = 9.81          # Gravitational acceleration (m/s²)
RD            = 287.05        # Specific gas constant for dry air (J/kg/K)
CP            = 1005.0        # Specific heat at constant pressure (J/kg/K)
KAPPA         = RD / CP       # Poisson constant
KARMAN        = 0.41          # Von Kármán constant
T0_K          = 273.15        # 0°C in Kelvin
P0_HPA        = 1013.25       # Standard sea-level pressure (hPa)

# PM2.5 reference value (µg/m³)
WHO_PM25_ANNUAL_GUIDELINE  = 5.0   # WHO 2021 guideline
WHO_PM25_24H_GUIDELINE     = 15.0  # WHO 2021 24h guideline
INDIA_NAAQS_PM25_ANNUAL    = 40.0  # NAAQS (relevant as regional comparison)

# ─────────────────────────────────────────────
# RANDOM SEED
# ─────────────────────────────────────────────

RANDOM_SEED = 42

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
