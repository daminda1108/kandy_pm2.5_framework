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
# CANONICAL CONSTANTS — single source of truth (added 2026-05-08 per audit §6.2)
# These values are referenced by paper drafts, kernel scripts, and validation
# routines. If a downstream file disagrees with the value here, the downstream
# file is wrong. Update this block, never restate the values elsewhere.
# ─────────────────────────────────────────────

# KOALA PM2.5 anchor (Senarathna et al. 2024, CJS 53(2):197–206)
# 12-month low-cost-sensor campaign, n=12 monthly aggregates, multi-sensor.
# Reported annual mean ± 17.5% bound → [20.2, 28.8] µg/m³.
# NOTE (2026-06-04 area-vs-floor correction): this is a valley-FLOOR / near-core
# level — the KOALA/NIFS monitor (7.2839 N, 80.6322 E) sits ~27 m above the local
# valley floor, ~0.7 km S of Kandy lake. It is NOT the basin AREA mean (that is the
# VanD basin reading ~19.7, corroborated by GHAP ~17). The decomposition level
# anchor uses VanD's area mean directly (β≡1); KOALA is reproduced at the NIFS pixel
# by the confinement field, not forced. See features/vandonkelaar.py + gotcha #51.
KOALA_ANCHOR_UG_M3 = 24.5225

# CAMS EAC4 over Kandy, 2019 annual mean, raw (uncorrected)
CAMS_KANDY_2019_MEAN_UG_M3 = 40.98

# Stage A flat-annual bias correction factor (KOALA / CAMS_2019)
CAMS_BIAS_FACTOR_FLAT = round(KOALA_ANCHOR_UG_M3 / CAMS_KANDY_2019_MEAN_UG_M3, 4)
# = 0.5984 (used as `apply_koala_monthly_correction()` flat-annual ratio)

# GEOS-CF PM25_RH35_GCC over Kandy, annual mean over the available window
# (Jan 2018 – Apr 2026). Used as denominator for Kandy zero-shot c_prior scaling.
GEOS_CF_KANDY_MEAN_UG_M3 = 45.7

# Per-city station means and GEOS-CF means (used for Stage C residual learning).
# station_mean / geos_mean = city_ratio; c_prior_scaled = c_prior × city_ratio.
# All values verified against the Kaggle convcnp_loocv_v1 kernel and SESLOG.
STATION_CITY_MEANS_UG_M3 = {
    "medellin"     : 21.7,
    "chiangmai"    : 12.2,
    "kathmandu"    : 61.2,
    "bogota"       : 16.5,
    "mexico_city"  : 21.2,
    "kandy"        : KOALA_ANCHOR_UG_M3,   # KOALA anchor stands in for station mean
}

GEOS_CITY_MEANS_UG_M3 = {
    "medellin"     : 26.5,
    "chiangmai"    : 23.0,
    "kathmandu"    : 77.4,
    "bogota"       : 20.4,
    "mexico_city"  : 97.4,
    "kandy"        : GEOS_CF_KANDY_MEAN_UG_M3,
}

CITY_RATIOS = {
    city: round(STATION_CITY_MEANS_UG_M3[city] / GEOS_CITY_MEANS_UG_M3[city], 4)
    for city in GEOS_CITY_MEANS_UG_M3
}
# CITY_RATIOS["kandy"] == 0.5360 (locked; the Kandy zero-shot c_prior scalar)

# Convenience aliases for the most-cited values
KANDY_GEOS_CF_RATIO = CITY_RATIOS["kandy"]   # = 0.5360 (used in paper §3.2.5)

# Native data resolution at which results are reported.
# (Optional 100m presentation downscaling is labelled as such; not a model output.)
NATIVE_RESOLUTION_KM = 1.0
NATIVE_RESOLUTION_TIMESTEP = "hourly"

# Validation framing (use these labels; do not write "validation" at zero-shot targets)
ZERO_SHOT_VALIDATION_LABEL = "structural-consistency check pending field validation"

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

MEDELLIN_DATA_DIR      = EXTERNAL_DIR / "medellin"
MEDELLIN_PM25_DIR      = MEDELLIN_DATA_DIR / "pm25"
MEDELLIN_ERA5_DIR      = MEDELLIN_DATA_DIR / "era5"
MEDELLIN_DEM_DIR       = MEDELLIN_DATA_DIR / "dem"
MEDELLIN_SATELLITE_DIR = MEDELLIN_DATA_DIR / "satellite"
MEDELLIN_MODIS_DIR     = MEDELLIN_SATELLITE_DIR / "modis"
MEDELLIN_TROPOMI_DIR   = MEDELLIN_SATELLITE_DIR / "tropomi"
MEDELLIN_CAMS_DIR      = MEDELLIN_DATA_DIR / "cams"

CHIANGMAI_DATA_DIR      = EXTERNAL_DIR / "chiangmai"
CHIANGMAI_PM25_DIR      = CHIANGMAI_DATA_DIR / "pm25"
CHIANGMAI_ERA5_DIR      = CHIANGMAI_DATA_DIR / "era5"
CHIANGMAI_DEM_DIR       = CHIANGMAI_DATA_DIR / "dem"
CHIANGMAI_SATELLITE_DIR = CHIANGMAI_DATA_DIR / "satellite"
CHIANGMAI_MODIS_DIR     = CHIANGMAI_SATELLITE_DIR / "modis"
CHIANGMAI_TROPOMI_DIR   = CHIANGMAI_SATELLITE_DIR / "tropomi"

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
    # Tuned via 100-trial Optuna LOMO-CV objective (2026-03-07)
    # Best mean LOMO RMSE: 4.818 µg/m³ vs 4.925 default (saved: results/models/xgboost_best_params.json)
    # Key findings: strong L1 (reg_alpha=12.4), non-zero gamma (1.98), shallow trees (depth=5)
    "n_estimators":      1184,
    "learning_rate":     0.008216557622222474,
    "max_depth":         5,
    "subsample":         0.7671508181415934,
    "colsample_bytree":  0.9104394470417163,
    "colsample_bylevel": 0.9744748155917816,
    "min_child_weight":  3,
    "gamma":             1.980599561405435,
    "reg_alpha":         12.447006316112198,
    "reg_lambda":        2.7135425208026795e-05,
    "objective":         "reg:squarederror",
    "eval_metric":       "rmse",
    "n_jobs":            -1,
    "random_state":      42,
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

# Bounding boxes for external cities (broad, for ERA5 download)
MEDELLIN_BBOX  = (-75.65, 6.17, -75.52, 6.31)    # lon_min, lat_min, lon_max, lat_max (tuple)
# Dict version for compatibility with spatial_mean_over_bbox (same format as KANDY_BBOX)
MEDELLIN_BROAD_BBOX = {
    "lat_min": 6.17, "lat_max": 6.31,
    "lon_min": -75.65, "lon_max": -75.52,
}
# Medellín valley physics (Aburrá valley, N-S oriented)
MEDELLIN_VALLEY_DEPTH_M   = 800.0   # Valley floor to surrounding ridge (~1500m vs ~700m floor)
MEDELLIN_VALLEY_AXIS_DEG  = 0.0     # Valley runs N-S (0° = North), vs 45° for Kandy
MEDELLIN_CENTRE_LAT       = 6.2441
MEDELLIN_CENTRE_LON       = -75.5812
CHIANGMAI_BBOX = (98.93,  18.70, 99.07,  18.87)
CHIANGMAI_BROAD_BBOX = {                             # dict form for spatial_mean_over_bbox
    "lon_min": 98.93, "lat_min": 18.70,
    "lon_max": 99.07, "lat_max": 18.87,
}
CHIANGMAI_VALLEY_DEPTH_M  = 800.0   # Ping River valley: floor ~300m, ridges ~1000-1100m
CHIANGMAI_VALLEY_AXIS_DEG = 0.0     # N-S oriented (Ping River axis)
CHIANGMAI_CENTRE_LAT      = 18.7846
CHIANGMAI_CENTRE_LON      = 98.9868

# Bogotá (RMCAB / OpenAQ source city #4) — high-altitude Andean basin
BOGOTA_BBOX = (-74.25, 4.45, -73.95, 4.85)
BOGOTA_BROAD_BBOX = {
    "lat_min": 4.45, "lat_max": 4.85,
    "lon_min": -74.25, "lon_max": -73.95,
}
BOGOTA_VALLEY_DEPTH_M  = 600.0    # Sabana ~2550m, eastern hills ~3150m
BOGOTA_VALLEY_AXIS_DEG = 0.0      # Open Sabana, eastern wall N-S
BOGOTA_CENTRE_LAT      = 4.6486
BOGOTA_CENTRE_LON      = -74.0833

# Mexico City (SIMAT / OpenAQ source city #5) — high-altitude continental basin
MEXICO_CITY_BBOX = (-99.32, 19.20, -98.85, 19.60)
MEXICO_CITY_BROAD_BBOX = {
    "lat_min": 19.20, "lat_max": 19.60,
    "lon_min": -99.32, "lon_max": -98.85,
}
MEXICO_CITY_VALLEY_DEPTH_M  = 1000.0  # Valley floor ~2240m, surrounding ridges 3000-3500m
MEXICO_CITY_VALLEY_AXIS_DEG = 0.0     # Roughly N-S basin
MEXICO_CITY_CENTRE_LAT      = 19.4326
MEXICO_CITY_CENTRE_LON      = -99.1332

# Pre-training sub-domains — 15×15km centred on monitoring network centroids
# Matches Kandy PINN domain scale (KANDY_PINN_BBOX = 15×15km).
# Scale matching is critical: Fourier features tuned for 15km spatial features.
# Medellín: 11/21 stations inside (urban core of Aburrá valley)
# Chiang Mai: 3/3 stations inside
MEDELLIN_PINN_BBOX = {
    "lat_min": 6.1635,
    "lat_max": 6.2986,
    "lon_min": -75.6426,
    "lon_max": -75.5066,
}
CHIANGMAI_PINN_BBOX = {
    "lat_min": 18.7446,
    "lat_max": 18.8797,
    "lon_min": 98.8808,
    "lon_max": 99.0236,
}

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
FOURIER_N     = 256   # Number of Fourier basis functions
FOURIER_SIGMA = 1.0   # Frequency scale for normalised [-1,1] inputs (σ=1.0 — matches Medellín backbone)

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
PINN_TIMESTEPS_PER_DAY = 48   # 30-min intervals → 48 per day (was PINN_HOURS=24)

PINN_NETWORK = {
    "hidden_layers": 6,
    "neurons_per_layer": 128,  # ablation winner C_medium 2026-03-01 — see results/ablation/WINNER.txt
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
PINN_FOURIER_FEATURES = FOURIER_N       # 256 random Fourier basis functions  # ablation winner C_medium 2026-03-01
PINN_FOURIER_SIGMA    = FOURIER_SIGMA   # Frequency scale σ = 1.0
PINN_HIDDEN_LAYERS    = PINN_NETWORK["hidden_layers"]      # 6
PINN_HIDDEN_UNITS     = PINN_NETWORK["neurons_per_layer"]  # 128  # ablation winner C_medium 2026-03-01

# Pre-trained Stage 2 backbone for Stage 3 initialisation.
# Set to None to cold-start. Path is relative to project root via MODELS_DIR.
# Canonical warm-start: Medellín v8 Phase-1 ep1000 (R²=0.882, r_kblh=0.879, pure-data — DO NOT use v9 ep1000 which is inoculated).
PINN_PRETRAINED_BACKBONE = MODELS_DIR / "stage2_medellin_pinn" / "v8" / "checkpoints" / "epoch_01000.pt"

# Training hyper-parameters (flat aliases)
PINN_EPOCHS = PINN_TRAINING["epochs_physics"]   # 12 000
PINN_LR     = PINN_TRAINING["lr_physics"]       # 1e-4

# Collocation point counts (flat aliases)
N_COLLOCATION_INTERIOR = PINN_N_COLLOCATION_INTERIOR   # 8 000
N_COLLOCATION_BOUNDARY = PINN_N_COLLOCATION_BOUNDARY   # 1 500

# Physically plausible K bounds (flat aliases from transfer validation gate)
K_MIN_MS2 = TRANSFER_K_MIN_M2S   # 1.0  m²/s
K_MAX_MS2 = TRANSFER_K_MAX_M2S   # 100.0 m²/s

# ── V2 DiffusionSubNet (Upgrade 1) ──────────────────────────────────────────
# Separate 3-layer MLP for Kx, Ky taking [x, y, t, blh_norm, elev_norm] inputs.
PINN_DIFFUSION_HIDDEN = 32      # neurons in DiffusionSubNet hidden layers (5→32→32→2)
PINN_BLH_NORM_SCALE   = 2000.0  # m — BLH normalisation denominator (clips to [0,1])

# ── V2 SourceSubNet (Upgrade 2) ──────────────────────────────────────────────
# Dedicated 4-layer MLP for S with cyclic hour-of-day + day-of-week encoding.
PINN_SOURCE_HIDDEN      = 48    # neurons in SourceSubNet hidden layers (6→48→48→48→1)
PINN_SOURCE_CYCLIC_TIME = True  # enable cyclic (sin/cos) time encoding for S head

# ── V2 Reinit flags for Stage 3 Kandy fine-tuning (Upgrade 3) ───────────────
# Source subnet: Medellín traffic emission spatial patterns are city-specific — always reinit
PINN_REINIT_SOURCE_AT_KANDY    = True
# Diffusion subnet: Kandy amphitheatre bowl ≠ Medellín linear valley — reinit K network
PINN_REINIT_DIFFUSION_AT_KANDY = True

# ── Loss weight schedules per training phase (Upgrade 3) ────────────────────
# Reference: RESEARCH_PROJECT_DESIGN.md §2.6
LOSS_SCHEDULE = {
    "medellin_pretrain": {
        "lambda_physics": 0.7,   # reduced from 0.9 — prevents trivial physics collapse
        "lambda_data":    0.2,   # increased from 0.1 — data constrains spatial field
        "lambda_bc":      0.1,
        "lambda_k_bound": 0.05,  # DiffusionSubNet soft bound penalty weight
    },
    "chiangmai_pretrain": {
        "lambda_physics": 0.6,
        "lambda_data":    0.3,
        "lambda_bc":      0.1,
        "lambda_k_bound": 0.05,
    },
    "kandy_finetune": {
        "lambda_physics": 0.4,   # physics already embedded in backbone
        "lambda_data":    0.5,   # Stage 1 observations are precious
        "lambda_bc":      0.1,
        "lambda_k_bound": 0.05,
        "stage1_weight":  True,  # weight by 1/σ² from Stage 1 quantile regression
    },
}

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

# Stage 3 TD-PINN v4 architecture constants
KOALA_PM25_ANCHOR = 24.5225   # Senarathna et al. 2024 annual mean (Kandy KOALA station)
PINN_DELTA_MAX    = 15.0      # max deviation from prior: C = C_prior + tanh(head)*DELTA_MAX

# ─────────────────────────────────────────────
# RANDOM SEED
# ─────────────────────────────────────────────

RANDOM_SEED = 42

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
