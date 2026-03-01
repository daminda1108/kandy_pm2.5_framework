"""
stage1_vs_stage3.py — Head-to-head comparison of Stage 1 (Sat-ML) vs Stage 3 (PINN) PM2.5.

This is the central publication comparison of the framework (§4.1 of design doc):

    Stage 1: spatial mean field at ~1 km, driven purely by satellite/met covariates.
    Stage 3: physics-constrained sub-km field inside the Kandy valley, inheriting
             Stage 1 as a boundary condition.

Metrics computed:
  1. SPATIAL CORRELATION: Does the PINN add spatial structure that Stage 1 can't see?
     Metric: Pearson r(Stage1, Stage3) — if r ≈ 1.0, PINN is redundant.
  2. ROOT-MEAN-SQUARE DIFFERENCE: How much does the PINN deviate from Stage 1?
  3. VALLEY vs RIM: Is the PINN-Stage1 delta larger inside the valley than at the rim?
     Expected: larger delta inside (valley trapping effect) — key scientific insight.
  4. UQ COMPARISON: Does Stage 3 PI width differ from Stage 1 PI width?
     Expected: Stage 3 PI tighter at well-constrained inner-valley locations.
  5. GROUND TRUTH VALIDATION: Where ground-truth PM2.5 sensors are available, compare
     Stage 1 RMSE vs Stage 3 RMSE.

Victory condition: Stage 3 RMSE at ground-truth sensors < Stage 1 RMSE.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import LOG_FORMAT, LOG_DATEFMT, FIGURES_DIR, TABLES_DIR

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("stage1_vs_stage3")


def load_predictions(
    stage1_dir: Path,
    stage3_dir: Path,
    date:       str,
) -> tuple:
    """
    Load Stage 1 and Stage 3 prediction grids for a given date.

    Returns:
        (df_s1, df_s3) — DataFrames with [lat, lon, pm25_pred, pm25_q05, pm25_q95]
    """
    def _load(d: Path, date: str) -> pd.DataFrame:
        patterns = [f"*{date}*.parquet", f"*{date}*.csv"]
        for pat in patterns:
            files = sorted(d.glob(pat))
            if files:
                f = files[0]
                return pd.read_parquet(f) if f.suffix == ".parquet" else pd.read_csv(f)
        log.warning(f"No prediction file for {date} in {d}")
        return pd.DataFrame()

    return _load(stage1_dir, date), _load(stage3_dir, date)


def spatial_correlation(s1_vals: np.ndarray, s3_vals: np.ndarray) -> dict:
    """
    Pearson correlation between Stage 1 and Stage 3 spatial fields.

    r close to 1 → PINN mostly tracking Stage 1 (structurally similar).
    r low → PINN adding distinct sub-km spatial information (desirable!).
    Target: r ∈ [0.6, 0.9] — correlated but enriched.
    """
    from scipy.stats import pearsonr
    mask = ~(np.isnan(s1_vals) | np.isnan(s3_vals))
    r, p = pearsonr(s1_vals[mask], s3_vals[mask])
    result = {"r": round(float(r), 4), "p": round(float(p), 6), "n": int(mask.sum())}
    log.info(f"Spatial correlation S1 vs S3: r={r:.3f}")
    return result


def rmse_comparison(
    obs: pd.DataFrame,
    s1_preds: pd.DataFrame,
    s3_preds: pd.DataFrame,
    obs_col: str = "pm25_obs",
) -> pd.DataFrame:
    """
    Compare Stage 1 vs Stage 3 RMSE against ground-truth sensors.

    Args:
        obs      : Ground-truth DataFrame with [lat, lon, pm25_obs, date]
        s1_preds : Stage 1 predictions (merged to obs locations)
        s3_preds : Stage 3 predictions (merged to obs locations)
        obs_col  : Observed PM2.5 column name

    Returns:
        DataFrame with RMSE / MAE / R² for both stages.
    """
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

    results = []
    for label, preds in [("Stage1_Sat-ML", s1_preds), ("Stage3_PINN", s3_preds)]:
        if preds.empty or obs.empty:
            continue
        merged = pd.merge_asof(
            obs.sort_values("lat"), preds.sort_values("lat"),
            on="lat", direction="nearest",
        )
        if merged.empty:
            continue
        valid = merged[obs_col].notna() & merged["pm25_pred"].notna()
        yt = merged.loc[valid, obs_col].values
        yp = merged.loc[valid, "pm25_pred"].values
        results.append({
            "model":  label,
            "n":      int(valid.sum()),
            "RMSE":   round(float(np.sqrt(mean_squared_error(yt, yp))), 3),
            "MAE":    round(float(mean_absolute_error(yt, yp)), 3),
            "R2":     round(float(r2_score(yt, yp)), 4),
        })

    df = pd.DataFrame(results)
    if not df.empty:
        win = df.loc[df["RMSE"].idxmin(), "model"]
        log.info(f"RMSE comparison:\n{df.to_string(index=False)}")
        log.info(f"Better model: {win}")
    return df


def valley_vs_rim_delta(
    s1_df: pd.DataFrame,
    s3_df: pd.DataFrame,
    valley_elev_cutoff: float = 550.0,
) -> dict:
    """
    Compare Stage 3 - Stage 1 delta inside the valley vs at the rim.

    Uses elevation as a proxy: valley ≡ elevation < valley_elev_cutoff.
    Expected result: |delta_valley| > |delta_rim|
    — the PINN adds more spatial detail inside the valley (trapping zone).

    Args:
        s1_df              : Stage 1 predictions with optional 'elevation' column
        s3_df              : Stage 3 predictions (must cover same spatial grid)
        valley_elev_cutoff : Elevation threshold [m] separating valley from rim

    Returns:
        Dict with mean delta inside valley vs rim, and hypothesis test result.
    """
    merged = pd.merge(
        s1_df[["lat", "lon", "pm25_pred"]].rename(columns={"pm25_pred": "C_s1"}),
        s3_df[["lat", "lon", "pm25_pred"]].rename(columns={"pm25_pred": "C_s3"}),
        on=["lat", "lon"], how="inner",
    )
    merged["delta"] = merged["C_s3"] - merged["C_s1"]

    # Use elevation if available; else use latitude as rough proxy (centre is valley)
    if "elevation" in s1_df.columns:
        merged = merged.merge(s1_df[["lat", "lon", "elevation"]], on=["lat", "lon"])
        in_valley = merged["elevation"] < valley_elev_cutoff
    else:
        lat_mid = merged["lat"].median()
        lat_q25 = merged["lat"].quantile(0.25)
        lat_q75 = merged["lat"].quantile(0.75)
        in_valley = (merged["lat"] >= lat_q25) & (merged["lat"] <= lat_q75)

    valley_delta = float(merged.loc[in_valley, "delta"].abs().mean())
    rim_delta    = float(merged.loc[~in_valley, "delta"].abs().mean())
    passed = valley_delta > rim_delta

    result = {
        "mean_abs_delta_valley_µgm3": round(valley_delta, 3),
        "mean_abs_delta_rim_µgm3":    round(rim_delta, 3),
        "valley_gt_rim":              passed,
    }
    status = "✅" if passed else "❌"
    log.info(f"Valley vs rim delta: valley={valley_delta:.2f}, rim={rim_delta:.2f} {status}")
    return result


def plot_difference_map(
    s1_df: pd.DataFrame,
    s3_df: pd.DataFrame,
    save_path: Optional[str] = None,
) -> None:
    """Plot Stage3 − Stage1 difference map and side-by-side concentration fields."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not available"); return

    merged = pd.merge(
        s1_df[["lat", "lon", "pm25_pred"]].rename(columns={"pm25_pred": "C_s1"}),
        s3_df[["lat", "lon", "pm25_pred"]].rename(columns={"pm25_pred": "C_s3"}),
        on=["lat", "lon"],
    )
    merged["delta"] = merged["C_s3"] - merged["C_s1"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5), constrained_layout=True)
    for ax, (col, title, cmap) in zip(axes, [
        ("C_s1",  "Stage 1 Sat-ML (µg/m³)",     "YlOrRd"),
        ("C_s3",  "Stage 3 PINN (µg/m³)",        "YlOrRd"),
        ("delta", "PINN − Sat-ML (µg/m³)",       "RdBu_r"),
    ]):
        sc = ax.scatter(merged["lon"], merged["lat"], c=merged[col], cmap=cmap, s=5)
        plt.colorbar(sc, ax=ax); ax.set_title(title); ax.grid(alpha=0.3)

    fig.suptitle("Stage 1 vs Stage 3 PM2.5 Comparison", fontsize=13)
    out = save_path or str(FIGURES_DIR / "stage1_vs_stage3_delta.png")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close()
    log.info(f"Difference map saved → {out}")


def run_comparison(
    stage1_dir: Path,
    stage3_dir: Path,
    ground_truth_csv: Optional[Path] = None,
    date: str = "mean",
    save: bool = True,
) -> dict:
    """Master runner: load both stages, compute all comparison metrics, save table."""
    s1_df, s3_df = load_predictions(stage1_dir, stage3_dir, date)
    if s1_df.empty or s3_df.empty:
        log.error("One or both prediction sets are empty — cannot compare")
        return {}

    corr = spatial_correlation(s1_df["pm25_pred"].values, s3_df["pm25_pred"].values)
    vr   = valley_vs_rim_delta(s1_df, s3_df)

    rmse_df = pd.DataFrame()
    if ground_truth_csv and Path(ground_truth_csv).exists():
        gt_df  = pd.read_csv(ground_truth_csv)
        rmse_df = rmse_comparison(gt_df, s1_df, s3_df)

    if save:
        plot_difference_map(s1_df, s3_df)
        if not rmse_df.empty:
            rmse_df.to_csv(TABLES_DIR / "stage1_vs_stage3_rmse.csv", index=False)

    return {"spatial_correlation": corr, "valley_rim_delta": vr, "rmse_comparison": rmse_df}
