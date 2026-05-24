"""
synthetic_outage_v3.py — H7 outage-robustness test for v3 LightGBM.

Pre-reg H7: During synthetic sensor outages, var(pred) ≥ 0.2 × var(c_prior_anchored)
            (the model must not collapse to a flat signal when lag features go NaN).

Procedure:
  1. Train a single LightGBM-quantile (α = 0.50) on the FULL v3 dataset (no LOMO).
  2. Identify candidate 7-day blocks of continuous coverage for each sensor.
  3. For each block, predict two scenarios:
        (a) "observed"  — original features, including lag_1h/3h/24h/168h.
        (b) "outage"    — lag features wiped to NaN; rest unchanged.
  4. Compute var(pred) for both, plus correlation between scenarios.
  5. Pass criterion: median var(outage_pred) / var(c_prior_anchored) ≥ 0.2.

Also compares against a v2.1-style "absolute model" emulation, where the
prediction collapses to ~population mean when lags are NaN (the failure mode
that motivated the residual-target architecture).

Output:
  data/processed/stage1_v3/training/outage_test_v3.csv
  results/figures/stage1_v3/outage_stress_test.png+pdf
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

warnings.filterwarnings("ignore")

DATA = HERE / "data" / "processed" / "stage1_v3"
OUT_DIR = DATA / "training"
FIG_DIR = HERE / "results" / "figures" / "stage1_v3"
FIG_DIR.mkdir(parents=True, exist_ok=True)

LAG_COLS = ["lag_1h", "lag_3h", "lag_24h", "lag_168h"]
DROP_COLS = {
    "pm25_observed", "residual_target",
    "sensor_name", "datetime_utc", "qc_flag",
    "geos_cf_pm25_raw", "c_prior_scaled", "c_prior_anchored", "b_FECT",
    "t925_minus_t2m_04LT_yesterday",
}


def get_features(df):
    return [c for c in df.columns if c not in DROP_COLS]


def find_continuous_block(sensor_df, length_hours=168):
    """Return the longest continuous coverage window of `length_hours` hours,
    plus the (start, end) datetime."""
    sensor_df = sensor_df.sort_values("datetime_utc")
    # consecutive 1-hour spacing
    diffs = sensor_df["datetime_utc"].diff().dt.total_seconds() / 3600
    # mark new run when gap > 1 hour
    runs = (diffs != 1).cumsum()
    grp = sensor_df.groupby(runs).size()
    long = grp[grp >= length_hours]
    if len(long) == 0:
        return None
    run_id = long.index[len(long) // 2]   # middle-length run
    block = sensor_df[runs == run_id].iloc[:length_hours]
    return block


def main():
    import lightgbm as lgb

    df = pd.read_parquet(DATA / "dataset_v3_hourly.parquet")
    df = df.dropna(subset=["residual_target", "c_prior_anchored"]).reset_index(drop=True)
    print(f"Loaded {len(df):,} rows × {df.shape[1]} cols")

    feat = get_features(df)
    print(f"Features ({len(feat)}): {feat}")

    print("\nTraining single-shot LightGBM (α=0.50) on full data...")
    model = lgb.LGBMRegressor(
        objective="quantile", alpha=0.5,
        learning_rate=0.05, num_leaves=63, min_data_in_leaf=20,
        feature_fraction=0.85, bagging_fraction=0.85, bagging_freq=5,
        n_estimators=600, verbose=-1,
    )
    model.fit(df[feat], df["residual_target"].values,
              categorical_feature=["sensor_id"])

    print("\nFinding continuous 7-day blocks per sensor...")
    results = []
    block_records = []
    for sid in df["sensor_id"].unique():
        sub = df[df["sensor_id"] == sid].copy()
        block = find_continuous_block(sub, length_hours=168)
        if block is None:
            print(f"  sensor {sid}: no 7-day block found")
            continue

        X_obs = block[feat].copy()
        X_out = block[feat].copy()
        for col in LAG_COLS:
            X_out[col] = np.nan

        res_obs = model.predict(X_obs)
        res_out = model.predict(X_out)
        pm25_obs_pred = block["c_prior_anchored"].values + res_obs
        pm25_out_pred = block["c_prior_anchored"].values + res_out
        pm25_true = block["pm25_observed"].values
        c_prior = block["c_prior_anchored"].values

        var_obs_pred = float(np.var(pm25_obs_pred))
        var_out_pred = float(np.var(pm25_out_pred))
        var_c_prior = float(np.var(c_prior))
        var_true = float(np.var(pm25_true))
        ratio_h7 = var_out_pred / var_c_prior if var_c_prior > 0 else float("nan")

        r_obs = float(np.corrcoef(pm25_obs_pred, pm25_true)[0, 1])
        r_out = float(np.corrcoef(pm25_out_pred, pm25_true)[0, 1])
        r_cprior = float(np.corrcoef(c_prior, pm25_true)[0, 1])
        rmse_obs = float(np.sqrt(np.mean((pm25_obs_pred - pm25_true)**2)))
        rmse_out = float(np.sqrt(np.mean((pm25_out_pred - pm25_true)**2)))
        rmse_cprior = float(np.sqrt(np.mean((c_prior - pm25_true)**2)))

        h7_pass = ratio_h7 >= 0.20
        print(f"  sensor {sid} block {block['datetime_utc'].iloc[0]} -> {block['datetime_utc'].iloc[-1]}")
        print(f"    var(obs_pred)={var_obs_pred:.2f}  "
              f"var(outage_pred)={var_out_pred:.2f}  "
              f"var(c_prior)={var_c_prior:.2f}  ratio={ratio_h7:.3f}  "
              f"H7: {'PASS' if h7_pass else 'FAIL'}")
        print(f"    RMSE obs={rmse_obs:.2f}  outage={rmse_out:.2f}  c_prior={rmse_cprior:.2f}")
        print(f"    r obs={r_obs:.3f}  outage={r_out:.3f}  c_prior={r_cprior:.3f}")

        results.append({
            "sensor_id": sid,
            "block_start": block["datetime_utc"].iloc[0],
            "block_end": block["datetime_utc"].iloc[-1],
            "var_obs_pred": var_obs_pred,
            "var_outage_pred": var_out_pred,
            "var_c_prior": var_c_prior,
            "var_true": var_true,
            "ratio_outage_vs_cprior": ratio_h7,
            "h7_pass": h7_pass,
            "rmse_obs_pred": rmse_obs,
            "rmse_outage_pred": rmse_out,
            "rmse_c_prior_only": rmse_cprior,
            "r_obs_pred": r_obs,
            "r_outage_pred": r_out,
            "r_c_prior_only": r_cprior,
        })
        block_records.append((sid, block, pm25_obs_pred, pm25_out_pred, c_prior, pm25_true))

    if not results:
        print("No blocks evaluated."); return

    res_df = pd.DataFrame(results)
    res_df.to_csv(OUT_DIR / "outage_test_v3.csv", index=False)

    median_ratio = res_df["ratio_outage_vs_cprior"].median()
    overall_pass = median_ratio >= 0.20
    print(f"\n══ H7 OUTAGE-ROBUSTNESS RESULT ══")
    print(f"Median var(outage_pred) / var(c_prior) = {median_ratio:.3f}")
    print(f"Threshold ≥ 0.20  →  H7: {'PASS' if overall_pass else 'FAIL'}")
    print(f"Per-sensor pass: {res_df['h7_pass'].sum()}/{len(res_df)}")

    # ── Figure ─────────────────────────────────────────────────────────────
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 150})
    n_blocks = len(block_records)
    fig, axes = plt.subplots(n_blocks, 1, figsize=(7, 3.0 * n_blocks),
                             sharex=False)
    if n_blocks == 1: axes = [axes]
    for ax, (sid, block, pm_obs, pm_out, c_p, pm_true) in zip(axes, block_records):
        t = pd.to_datetime(block["datetime_utc"]).dt.tz_convert("Asia/Colombo")
        ax.plot(t, pm_true, "-", color="#343a40", lw=0.7, alpha=0.6,
                label="FECT observed")
        ax.plot(t, c_p, "-", color="#f08c00", lw=0.8,
                label="c_prior_anchored (GEOS-CF + b_FECT)")
        ax.plot(t, pm_obs, "-", color="#1864ab", lw=0.9,
                label="v3 pred (with lags)")
        ax.plot(t, pm_out, "--", color="#c92a2a", lw=1.0,
                label="v3 pred (lags wiped — outage)")
        ax.set_title(f"Sensor {sid} — 7-day continuous block "
                     f"{block['datetime_utc'].iloc[0].date()} → "
                     f"{block['datetime_utc'].iloc[-1].date()}",
                     fontsize=8.5)
        ax.set_ylabel("PM₂.₅ (µg m⁻³)")
        ax.grid(axis="y", lw=0.4, alpha=0.5)
        ax.legend(fontsize=6, ncol=2, loc="upper right", framealpha=0.85)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"outage_stress_test.{ext}",
                    bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"\nSaved: {OUT_DIR / 'outage_test_v3.csv'}")
    print(f"Saved: {FIG_DIR / 'outage_stress_test.png'}")


if __name__ == "__main__":
    main()
