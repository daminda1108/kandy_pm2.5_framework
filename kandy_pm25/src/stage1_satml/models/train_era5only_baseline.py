"""
train_era5only_baseline.py — ERA5-only baseline XGBoost for RQ4 ablation.

RQ4: Do topography-aware features (VVC, KFP, TII, TPI, DSC, RWP, CGI) improve
     PM2.5 prediction beyond standard meteorological inputs?

This script trains an identical XGBoost quantile regression setup on ERA5-only
features, without any topographic features. The R² difference under blocked CV
versus the full-feature model (train_xgboost.py) answers RQ4.

ERA5-only feature set (7 variables):
    T2m           : 2 m air temperature [K]
    u10, v10      : 10 m wind components [m/s]
    BLH           : Boundary layer height [m]
    TP            : Total precipitation [mm/h]
    RH            : 2 m relative humidity [%]
    SSRD          : Surface solar radiation downwards [W/m²]

Full model adds 7 topo-aware features (VVC, KFP, TII, TPI, DSC, RWP, CGI).
The difference in blocked-CV R² is the evidence for RQ4.

Usage:
    python train_era5only_baseline.py --data data/processed/stage1_features.parquet
    python train_era5only_baseline.py --data ... --out outputs/stage1/era5only_baseline.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[4]))
from config import LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("train_era5only_baseline")

# ERA5-only feature columns (no topographic features — RQ4 ablation)
ERA5_FEATURES = ["T2m", "u10", "v10", "BLH", "TP", "RH", "SSRD"]

TARGET_COL = "pm25_ugm3"
OUT_DIR    = Path("outputs/stage1")


def train_era5only(data_path: Path, out_path: Path) -> dict:
    """
    Train XGBoost quantile regression on ERA5-only features with blocked CV.

    Returns:
        metrics dict with q50_r2, q05_coverage, q95_coverage (blocked CV mean)
    """
    try:
        import pandas as pd
        import xgboost as xgb
        import numpy as np
    except ImportError:
        raise ImportError("pandas, xgboost, numpy required")

    log.info(f"Loading feature data: {data_path}")
    df = pd.read_parquet(data_path) if str(data_path).endswith(".parquet") else pd.read_csv(data_path)

    missing = [c for c in ERA5_FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing ERA5 feature columns: {missing}. "
                         f"Run download_era5.py and meteo_features.py first.")

    X = df[ERA5_FEATURES].values
    y = df[TARGET_COL].values
    log.info(f"ERA5-only features: {ERA5_FEATURES}")
    log.info(f"Training on {len(df)} samples")

    # Blocked spatial CV: 5 folds by latitude band
    df["_lat_fold"] = pd.cut(df["lat"], bins=5, labels=False) if "lat" in df else 0
    folds = df["_lat_fold"].unique()

    metrics_per_fold = []
    for fold in folds:
        train_mask = df["_lat_fold"] != fold
        test_mask  = ~train_mask
        X_tr, y_tr = X[train_mask], y[train_mask]
        X_te, y_te = X[test_mask],  y[test_mask]

        model_q50 = xgb.XGBRegressor(
            objective="reg:quantileerror", quantile_alpha=0.50,
            n_estimators=500, learning_rate=0.05, max_depth=6,
            subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=0,
        )
        model_q50.fit(X_tr, y_tr)
        preds = model_q50.predict(X_te)

        ss_res = np.sum((y_te - preds) ** 2)
        ss_tot = np.sum((y_te - y_te.mean()) ** 2)
        r2 = 1.0 - ss_res / (ss_tot + 1e-12)
        metrics_per_fold.append({"fold": int(fold), "r2": float(r2), "n_test": int(test_mask.sum())})
        log.info(f"Fold {fold}: R² = {r2:.3f}")

    import numpy as np
    mean_r2 = float(np.mean([m["r2"] for m in metrics_per_fold]))
    metrics = {
        "model":       "ERA5-only baseline (RQ4 ablation)",
        "features":    ERA5_FEATURES,
        "mean_cv_r2":  mean_r2,
        "folds":       metrics_per_fold,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metrics, indent=2))
    log.info(f"Baseline metrics saved → {out_path}")
    log.info(f"ERA5-only mean blocked-CV R² = {mean_r2:.3f}")
    log.info("Compare to full-feature model R² to answer RQ4.")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="ERA5-only XGBoost baseline for RQ4 ablation")
    parser.add_argument("--data", type=Path, required=True,
                        help="Path to feature Parquet/CSV with ERA5 + topo + PM2.5 columns")
    parser.add_argument("--out", type=Path,
                        default=OUT_DIR / "era5only_baseline.json",
                        help="JSON output path for CV metrics")
    args = parser.parse_args()
    train_era5only(args.data, args.out)


if __name__ == "__main__":
    main()
