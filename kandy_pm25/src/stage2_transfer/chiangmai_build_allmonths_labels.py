"""
chiangmai_build_allmonths_labels.py — Build all-months (2021-2025) pseudo-labels for
the station-informed PINN training kernel.

PURPOSE
-------
The non-burning-only XGBoost + pseudo-labels (chiangmai_stage1_pixel_preds.npz) cover
only 2022 May–Dec (236 days). The station-informed PINN needs ALL months including the
burning season (Feb–May) because:
  1. Burning-season peaks (20–40 µg/m³) provide dynamic range for K-BLH coupling.
  2. Multi-year data (2021–2025) enables robust LOSO validation.

This script:
  1. Loads ERA5 (annual .nc, 2021–2025) → daily features.
  2. Loads city-mean PM2.5 from chiangmai_all_stations_2021_2025.parquet.
  3. Trains XGBoost (LOMO-year CV) on all months.
  4. Generates 150×150 pixel pseudo-labels with elevation weighting.
  5. Saves:
       data/processed/stage2/chiangmai_pseudolabels_allmonths.npz   (pixel preds)
       results/models/chiangmai_stage1_allmonths_xgboost.ubj
       data/processed/stage2/chiangmai_stage1_allmonths_dataset.parquet

Usage:
    cd kandy_pm25/
    python src/stage2_transfer/chiangmai_build_allmonths_labels.py
    python src/stage2_transfer/chiangmai_build_allmonths_labels.py --no-shap
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import xgboost as xgb
from sklearn.metrics import mean_squared_error, r2_score

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import (
    CHIANGMAI_ERA5_DIR,
    CHIANGMAI_PM25_DIR,
    CHIANGMAI_VALLEY_DEPTH_M,
    CHIANGMAI_VALLEY_AXIS_DEG,
    PROC_DIR,
    MODELS_DIR,
    FIGURES_DIR,
    PINN_INPUT_DIR,
    LOG_FORMAT, LOG_DATEFMT,
)

sys.path.insert(0, str(Path(__file__).parents[1]))
from stage1_satml.features.topo_features import (
    compute_vvc,
    compute_rwp,
    compute_valley_wind_decomposition,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("cm_allmonths_labels")

# ── Paths ──────────────────────────────────────────────────────────────────────
STAGE2_PROC_DIR    = PROC_DIR / "stage2"
ALL_STATIONS_PARQ  = STAGE2_PROC_DIR / "chiangmai_all_stations_2021_2025.parquet"
ELEV_GRID_NPZ      = PINN_INPUT_DIR / "chiangmai_elev_grid_100m.npz"
PIXEL_PREDS_OUT    = STAGE2_PROC_DIR / "chiangmai_pseudolabels_allmonths.npz"
DATASET_OUT        = STAGE2_PROC_DIR / "chiangmai_stage1_allmonths_dataset.parquet"
MODEL_OUT          = MODELS_DIR / "chiangmai_stage1_allmonths_xgboost.ubj"
SHAP_FIGURE_OUT    = FIGURES_DIR / "publication" / "chiangmai_stage1_allmonths_shap.png"

ERA5_YEARS         = [2021, 2022, 2023, 2024, 2025]
TARGET             = "pm25_observed"
RANDOM_SEED        = 42
MIN_STATIONS_PER_DAY = 2   # require ≥ 2 stations reporting

# Elevation weighting for pixel pseudo-labels
ELEV_WEIGHT_LAMBDA = 0.20  # 18% reduction per 1000m elevation gain

# IDW blending parameters (E1 enhancement)
IDW_W_STA      = 0.70   # station IDW weight vs elevation-only (0.70 = 70% IDW, 30% elevation)
IDW_ELEV_SCALE = 0.50   # elevation scale factor in km (500 m → elevation counts as much as 500m horiz)

# XGBoost default params (starting point from non-burning stage1)
DEFAULT_PARAMS = {
    "n_estimators":      312,
    "learning_rate":     0.05,
    "max_depth":         5,
    "subsample":         0.8,
    "colsample_bytree":  0.8,
    "colsample_bylevel": 0.8,
    "min_child_weight":  3,
    "gamma":             0.5,
    "reg_alpha":         0.267,
    "reg_lambda":        1.0,
    "objective":         "reg:squarederror",
    "n_jobs":            -1,
    "random_state":      RANDOM_SEED,
}


# ── ERA5 loading ───────────────────────────────────────────────────────────────

def _aggregate_era5_daily(df: pd.DataFrame) -> pd.DataFrame:
    """ERA5 hourly DataFrame → daily aggregates + derived variables."""
    agg = {k: v for k, v in {
        "u10": "mean", "v10": "mean",
        "t2m": "mean", "d2m": "mean",
        "blh": ["min", "max"],
        "sp":  "mean",
        "tp":  "sum",
    }.items() if k in df.columns}

    df["date"] = df.index.normalize()
    daily = df.groupby("date").agg(agg)

    # Flatten multi-index columns
    daily.columns = [
        f"{c[0]}_{c[1]}" if isinstance(c, tuple) and c[1] else
        (c[0] if isinstance(c, tuple) else c)
        for c in daily.columns
    ]
    for raw, final in [
        ("u10_mean", "u10"), ("v10_mean", "v10"),
        ("t2m_mean", "t2m"), ("d2m_mean", "d2m"),
        ("sp_mean",  "sp"),  ("tp_sum",   "tp"),
    ]:
        if raw in daily.columns:
            daily = daily.rename(columns={raw: final})

    # Derived variables
    daily["wind_speed"] = np.sqrt(daily["u10"] ** 2 + daily["v10"] ** 2)
    daily["wind_dir"]   = (270 - np.degrees(np.arctan2(daily["v10"], daily["u10"]))) % 360

    if "t2m" in daily.columns and "d2m" in daily.columns:
        tc  = daily["t2m"] - 273.15
        tdc = daily["d2m"] - 273.15
        daily["rh"] = (
            100 * np.exp((17.625 * tdc) / (243.04 + tdc)) /
                  np.exp((17.625 * tc)  / (243.04 + tc))
        ).clip(0, 100)

    if "sp" in daily.columns:
        daily["sp"] = daily["sp"] / 100.0  # Pa → hPa

    # Temporal encodings
    daily["month"]     = daily.index.month
    daily["month_sin"] = np.sin(2 * np.pi * daily.index.month / 12)
    daily["month_cos"] = np.cos(2 * np.pi * daily.index.month / 12)
    daily["doy"]       = daily.index.dayofyear
    daily["doy_sin"]   = np.sin(2 * np.pi * daily.index.dayofyear / 365)
    daily["doy_cos"]   = np.cos(2 * np.pi * daily.index.dayofyear / 365)
    daily["dow_sin"]   = np.sin(2 * np.pi * daily.index.dayofweek / 7)
    daily["dow_cos"]   = np.cos(2 * np.pi * daily.index.dayofweek / 7)
    return daily


def load_era5_all_years(years: list[int]) -> pd.DataFrame:
    """Load ERA5 annual .nc files for multiple years → concatenated daily DataFrame."""
    frames = []
    for yr in years:
        nc_path = CHIANGMAI_ERA5_DIR / f"chiangmai_era5_{yr}.nc"
        if not nc_path.exists():
            log.warning(f"ERA5 not found for {yr}: {nc_path} — skipping")
            continue
        log.info(f"  Loading ERA5 {yr}: {nc_path.name}")
        try:
            ds = xr.open_dataset(str(nc_path))
            time_dim = next((d for d in ds.dims if d in ("time", "valid_time")), None)
            if time_dim is None:
                log.warning(f"  No time dimension in {nc_path.name}")
                ds.close()
                continue
            spatial_dims = [d for d in ds.dims if d != time_dim]
            ds_mean = ds.mean(dim=spatial_dims)
            df = ds_mean.to_dataframe()
            idx = pd.DatetimeIndex(df.index)
            if idx.tz is not None:
                idx = idx.tz_localize(None)
            df.index = idx
            rename = {"u10": "u10", "v10": "v10", "t2m": "t2m", "d2m": "d2m",
                      "blh": "blh", "sp": "sp", "tp": "tp"}
            df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
            frames.append(df)
            ds.close()
        except Exception as e:
            log.warning(f"  Error loading {nc_path.name}: {e}")

    if not frames:
        raise RuntimeError("No ERA5 files loaded. Check CHIANGMAI_ERA5_DIR.")

    era5 = pd.concat(frames).sort_index()
    era5 = era5[~era5.index.duplicated(keep="first")]
    log.info(f"ERA5 combined: {len(era5)} hourly rows, "
             f"{era5.index.min().date()} to {era5.index.max().date()}")

    daily = _aggregate_era5_daily(era5)
    log.info(f"ERA5 daily: {len(daily)} rows")
    return daily


# ── Station labels ─────────────────────────────────────────────────────────────

def load_city_mean_labels() -> pd.Series:
    """
    Load all-stations parquet → city-mean daily PM2.5.
    Requires ≥ MIN_STATIONS_PER_DAY stations reporting each day.
    """
    df = pd.read_parquet(ALL_STATIONS_PARQ)
    df["dt"] = pd.to_datetime(df["datetime_utc"]).dt.tz_localize(None)
    df["date"] = df["dt"].dt.normalize()
    df = df[(df["pm25"] >= 0) & (df["pm25"] <= 500)].copy()

    # Per-station daily mean → city daily mean
    station_daily = (
        df.groupby(["date", "location_id"])["pm25"]
        .mean()
    )
    n_sta_per_day = station_daily.groupby("date").count()
    valid_days = n_sta_per_day[n_sta_per_day >= MIN_STATIONS_PER_DAY].index

    city_mean = (
        station_daily
        .groupby("date")
        .mean()
        .rename(TARGET)
    )
    city_mean.index = pd.DatetimeIndex(city_mean.index)
    city_mean = city_mean[city_mean.index.isin(valid_days)]

    log.info(f"City-mean labels: {len(city_mean)} days, "
             f"mean={city_mean.mean():.1f}±{city_mean.std():.1f} µg/m³")
    log.info(f"  Date range: {city_mean.index.min().date()} to {city_mean.index.max().date()}")
    log.info(f"  Months: {sorted(city_mean.index.month.unique().tolist())}")
    log.info(f"  Years:  {sorted(city_mean.index.year.unique().tolist())}")
    return city_mean


# ── Topo features ──────────────────────────────────────────────────────────────

def compute_topo_features(era5: pd.DataFrame) -> pd.DataFrame:
    feats = pd.DataFrame(index=era5.index)
    blh_col = "blh_min" if "blh_min" in era5.columns else "blh"

    if blh_col in era5.columns and "wind_speed" in era5.columns:
        feats["vvc"] = compute_vvc(
            era5["wind_speed"], era5[blh_col],
            valley_depth_m=CHIANGMAI_VALLEY_DEPTH_M,
        )
        feats["blh_ratio"] = era5[blh_col] / 1000.0

    if "tp" in era5.columns and "wind_speed" in era5.columns:
        feats["rwp"] = compute_rwp(era5["tp"], era5["wind_speed"])

    if "u10" in era5.columns and "v10" in era5.columns:
        vw = compute_valley_wind_decomposition(
            era5["u10"], era5["v10"],
            blh_m=era5.get(blh_col),
            valley_axis_deg=CHIANGMAI_VALLEY_AXIS_DEG,
        )
        feats = pd.concat([feats, vw], axis=1)

    log.info(f"Topo features: {feats.shape[1]} columns → {list(feats.columns)}")
    return feats


# ── Dataset merge ──────────────────────────────────────────────────────────────

def build_dataset(era5_daily: pd.DataFrame, labels: pd.Series) -> tuple[pd.DataFrame, list[str]]:
    topo = compute_topo_features(era5_daily)
    merged = era5_daily.join(topo, how="left")
    merged = merged.join(labels, how="inner")  # only days with both ERA5 + labels

    NON_FEATURE = {TARGET, "month", "doy"}
    features = [c for c in merged.columns if c not in NON_FEATURE and merged[c].notna().any()]

    log.info(f"Dataset: {len(merged)} days × {len(features)} features + target")
    log.info(f"  Year distribution: {merged.groupby(merged.index.year).size().to_dict()}")
    log.info(f"  Month distribution: {merged.groupby(merged.index.month).size().to_dict()}")
    return merged, features


# ── Cross-validation ───────────────────────────────────────────────────────────

def run_lomo_year_cv(df: pd.DataFrame, features: list[str], params: dict) -> pd.Series:
    """
    Leave-One-Year-Out CV. With 5 years of data, each fold uses 4 years to train,
    1 year to validate. More robust than LOMO (month) for multi-year data.
    """
    labelled = df[df[TARGET].notna()].copy()
    X, y = labelled[features], labelled[TARGET]
    years = labelled.index.year

    all_preds = pd.Series(dtype=float, index=labelled.index, name="pm25_pred_loyo")
    fold_results = []

    for yr in sorted(years.unique()):
        test_mask = years == yr
        X_tr, X_te = X[~test_mask], X[test_mask]
        y_tr, y_te = y[~test_mask], y[test_mask]
        if len(y_te) == 0 or len(y_tr) < 50:
            continue

        p = {k: v for k, v in params.items() if k != "early_stopping_rounds"}
        model = xgb.XGBRegressor(**p)
        model.fit(X_tr, y_tr, verbose=False)
        pred = model.predict(X_te)
        all_preds[X_te.index] = pred

        r2   = r2_score(y_te, pred)
        rmse = mean_squared_error(y_te, pred) ** 0.5
        bias = float((pred - y_te.values).mean())
        log.info(f"LOYO {yr}: R²={r2:.3f}  RMSE={rmse:.2f}  bias={bias:+.2f}  n={len(y_te)}")
        fold_results.append({"year": yr, "r2": r2, "rmse": rmse, "bias": bias})

    folds = pd.DataFrame(fold_results)
    log.info(f"\nLOYO overall: R²={folds['r2'].mean():.3f}±{folds['r2'].std():.3f}  "
             f"RMSE={folds['rmse'].mean():.2f}±{folds['rmse'].std():.2f} µg/m³")
    return all_preds


# ── Pixel predictions ──────────────────────────────────────────────────────────

def _load_station_daily_for_idw() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load per-station daily PM2.5 and station locations for IDW blending.
    Returns: (station_pivot: Date×StationID DataFrame, sta_locs: DataFrame[lat,lon])
    """
    df = pd.read_parquet(ALL_STATIONS_PARQ)
    df["dt"]   = pd.to_datetime(df["datetime_utc"]).dt.tz_localize(None)
    df["date"] = df["dt"].dt.normalize()
    df = df[(df["pm25"] >= 0) & (df["pm25"] <= 500)].copy()

    sta_locs = (
        df.groupby("location_id")[["lat", "lon"]]
        .first()
        .astype(np.float64)
    )

    station_pivot = (
        df.groupby(["date", "location_id"])["pm25"]
        .mean()
        .unstack(level="location_id")
    )
    station_pivot.index = pd.DatetimeIndex(station_pivot.index)

    n_sta  = len(sta_locs)
    n_days = len(station_pivot)
    log.info(f"IDW: {n_sta} stations, {n_days} days of station data "
             f"({station_pivot.index.min().date()} – {station_pivot.index.max().date()})")
    return station_pivot, sta_locs


def generate_pixel_preds(
    city_preds_series: pd.Series,
    use_idw: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate 150×150 pixel pseudo-labels.

    With use_idw=True (default, E1 enhancement):
        C_pixel = IDW_W_STA × IDW(x,y,t) + (1−IDW_W_STA) × C_city(t) × elev_weight(x,y)
        d_eff   = sqrt(d_horiz_km² + (IDW_ELEV_SCALE × Δelev_km)²)
        weight  = 1 / d_eff²

    With use_idw=False (legacy elevation-only):
        C_pixel = C_city(t) × exp(−λ × (elev − elev_mean) / 1000)

    Returns: (pixel_preds: float32 (n_days, 150, 150), dates: datetime64[D])
    """
    elev_data  = np.load(ELEV_GRID_NPZ)
    elev_grid  = elev_data["elev"].astype(np.float32)
    lat_grid   = elev_data["lat_grid"].astype(np.float64)
    lon_grid   = elev_data["lon_grid"].astype(np.float64)
    H, W = elev_grid.shape
    log.info(f"Elevation grid: {H}×{W}, "
             f"mean={elev_grid.mean():.0f}m, range=[{elev_grid.min():.0f}, {elev_grid.max():.0f}]m")

    elev_mean   = float(np.nanmean(elev_grid))
    elev_weight = np.exp(-ELEV_WEIGHT_LAMBDA * (elev_grid - elev_mean) / 1000.0)

    city_preds = city_preds_series.sort_index()
    n_days     = len(city_preds)
    pixel_preds = np.zeros((n_days, H, W), dtype=np.float32)

    if not use_idw:
        for i, c_city in enumerate(city_preds.values):
            pixel_preds[i] = (float(c_city) * elev_weight).astype(np.float32)
        dates = city_preds.index.to_numpy(dtype="datetime64[D]")
        log.info(f"Pixel preds (elev-only): shape={pixel_preds.shape}, "
                 f"spatial_std={pixel_preds.std(axis=(1,2)).mean():.3f} µg/m³")
        return pixel_preds, dates

    # ── IDW blending ───────────────────────────────────────────────────────────
    station_pivot, sta_locs = _load_station_daily_for_idw()
    sta_id_list = sta_locs.index.tolist()
    n_sta = len(sta_id_list)

    # km-per-degree factors at Chiang Mai latitude (~18.8°N)
    deg_to_km_lat = 111.0
    deg_to_km_lon = 111.0 * np.cos(np.radians(18.8))

    # Pre-compute static IDW weights: (H*W, n_sta)
    # Elevation at each station = nearest-pixel elevation
    sta_elev = np.zeros(n_sta, dtype=np.float64)
    for j, sid in enumerate(sta_id_list):
        slat, slon = sta_locs.loc[sid, "lat"], sta_locs.loc[sid, "lon"]
        dist = np.abs(lat_grid - slat) + np.abs(lon_grid - slon)
        iy, ix = np.unravel_index(np.argmin(dist), dist.shape)
        sta_elev[j] = float(elev_grid[iy, ix])

    weights_all = np.zeros((H * W, n_sta), dtype=np.float32)
    for j, sid in enumerate(sta_id_list):
        slat, slon = sta_locs.loc[sid, "lat"], sta_locs.loc[sid, "lon"]
        d_lat_km  = (lat_grid - slat) * deg_to_km_lat          # (H, W)
        d_lon_km  = (lon_grid - slon) * deg_to_km_lon          # (H, W)
        d_horiz   = np.sqrt(d_lat_km**2 + d_lon_km**2)         # km
        d_elev    = (elev_grid - sta_elev[j]) / 1000.0          # km
        d_eff     = np.sqrt(d_horiz**2 + (IDW_ELEV_SCALE * d_elev)**2 + 1e-6)
        weights_all[:, j] = (1.0 / d_eff**2).reshape(-1).astype(np.float32)

    log.info(f"IDW weight matrix: {weights_all.shape}, "
             f"max_weight={weights_all.max():.2f}")

    # Per-day IDW + blend
    dates = city_preds.index.to_numpy(dtype="datetime64[D]")
    for i, (date, c_city) in enumerate(city_preds.items()):
        elev_pred = (float(c_city) * elev_weight).astype(np.float32)  # (H, W)

        # Stations reporting this day
        if date in station_pivot.index:
            row = station_pivot.loc[date]
            reporting_j   = [j for j, sid in enumerate(sta_id_list)
                             if sid in row.index and not pd.isna(row.get(sid, np.nan))]
            reporting_pm25 = np.array([row[sta_id_list[j]] for j in reporting_j],
                                       dtype=np.float32)
        else:
            reporting_j, reporting_pm25 = [], np.array([], dtype=np.float32)

        if len(reporting_j) > 0:
            w_today  = weights_all[:, reporting_j]                  # (H*W, k)
            w_sum    = w_today.sum(axis=1, keepdims=True) + 1e-12  # (H*W, 1)
            idw_pred = (w_today @ reporting_pm25) / w_sum.squeeze()  # (H*W,)
            idw_pred = idw_pred.reshape(H, W).astype(np.float32)
            pixel_preds[i] = IDW_W_STA * idw_pred + (1 - IDW_W_STA) * elev_pred
        else:
            pixel_preds[i] = elev_pred  # fallback: elevation-only

    spatial_std = pixel_preds.std(axis=(1, 2)).mean()
    log.info(f"Pixel preds (IDW): shape={pixel_preds.shape}, "
             f"mean={pixel_preds.mean():.1f} µg/m³, "
             f"spatial_std={spatial_std:.3f} µg/m³  [target: >2.0]")
    return pixel_preds, dates


# ── SHAP ───────────────────────────────────────────────────────────────────────

def run_shap(model: xgb.XGBRegressor, X: pd.DataFrame) -> None:
    try:
        import shap
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("shap/matplotlib not installed — skipping SHAP")
        return
    log.info("Running SHAP …")
    X_sample  = X.sample(min(300, len(X)), random_state=RANDOM_SEED)
    explainer = shap.TreeExplainer(model)
    sv        = explainer.shap_values(X_sample)
    importance = pd.DataFrame({
        "feature": X.columns.tolist(),
        "mean_abs_shap": np.abs(sv).mean(axis=0),
    }).sort_values("mean_abs_shap", ascending=False)
    log.info("Top 10 features:\n" + importance.head(10).to_string(index=False))
    SHAP_FIGURE_OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 8))
    shap.summary_plot(sv, X_sample, show=False, max_display=20)
    plt.tight_layout()
    plt.savefig(SHAP_FIGURE_OUT, dpi=150, bbox_inches="tight")
    plt.close()
    log.info(f"SHAP → {SHAP_FIGURE_OUT}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build all-months ChiangMai pseudo-labels (2021–2025)"
    )
    parser.add_argument("--no-shap", action="store_true", help="Skip SHAP")
    parser.add_argument("--no-idw",  action="store_true",
                        help="Use elevation-only weighting (legacy). Default: IDW blending.")
    args = parser.parse_args()

    # 1. Load ERA5
    log.info("── 1. Loading ERA5 (2021–2025) ─────────────────────────────────")
    era5_daily = load_era5_all_years(ERA5_YEARS)

    # 2. Load labels
    log.info("── 2. Loading city-mean labels ──────────────────────────────────")
    labels = load_city_mean_labels()

    # 3. Build dataset
    log.info("── 3. Building dataset ───────────────────────────────────────────")
    df, features = build_dataset(era5_daily, labels)
    STAGE2_PROC_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(DATASET_OUT)
    log.info(f"Dataset → {DATASET_OUT}")

    # 4. Cross-validation
    log.info("── 4. LOYO Cross-Validation ──────────────────────────────────────")
    loyo_preds = run_lomo_year_cv(df, features, DEFAULT_PARAMS)

    # 5. Train final model on ALL data
    log.info("── 5. Training final model ───────────────────────────────────────")
    labelled = df[df[TARGET].notna()].copy()
    X_full, y_full = labelled[features], labelled[TARGET]
    p = {k: v for k, v in DEFAULT_PARAMS.items() if k != "early_stopping_rounds"}
    model = xgb.XGBRegressor(**p)
    model.fit(X_full, y_full, verbose=False)
    train_pred = model.predict(X_full)
    r2_train = r2_score(y_full, train_pred)
    bias_train = float((train_pred - y_full.values).mean())
    log.info(f"Train-fit: R²={r2_train:.3f}, bias={bias_train:+.2f} µg/m³")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(str(MODEL_OUT))
    log.info(f"Model → {MODEL_OUT}")

    # 6. Generate pixel predictions (for PINN pseudo-labels)
    use_idw = not args.no_idw
    log.info(f"── 6. Generating pixel pseudo-labels (150×150, IDW={'ON' if use_idw else 'OFF'}) ──")
    city_pred_series = pd.Series(train_pred, index=y_full.index, name="pm25_pred")
    pixel_preds, dates = generate_pixel_preds(city_pred_series, use_idw=use_idw)

    np.savez_compressed(
        str(PIXEL_PREDS_OUT),
        pixel_preds=pixel_preds,
        dates=dates,
    )
    size_mb = PIXEL_PREDS_OUT.stat().st_size / 1e6
    log.info(f"Pixel predictions → {PIXEL_PREDS_OUT}  ({size_mb:.1f} MB)")
    log.info(f"  n_days={len(dates)}, shape={pixel_preds.shape}")
    log.info(f"  Date range: {dates.min()} to {dates.max()}")

    # 7. SHAP
    if not args.no_shap:
        run_shap(model, X_full)

    log.info("── Done ─────────────────────────────────────────────────────────")
    log.info(f"All-months pseudo-labels ready: {PIXEL_PREDS_OUT}")
    log.info(f"  {len(dates)} days × 150 × 150 pixels")
    log.info(f"  Burning months included: {sorted(set(pd.DatetimeIndex(dates).month.tolist()))}")


if __name__ == "__main__":
    main()
