"""
blend_v3.py — Linear blender of v3 LGBM + CatBoost + XGB + CV+ conformal wrap.

Reads the three model prediction parquets, fits a non-negative sum-to-one
linear blender on q50 across all LOMO predictions, then applies a Mondrian
CV+ conformal wrap (calibration set = all OOF predictions from other folds).

Output:
  data/processed/stage1_v3/training/predictions_blend_v3.parquet
  data/processed/stage1_v3/training/summary_blend_v3.csv
  data/processed/stage1_v3/training/blender_weights_v3.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

DATA = HERE / "data" / "processed" / "stage1_v3" / "training"

ALPHA = 0.10  # 90% PI target
HOD_BINS = [(0, 5), (6, 9), (10, 14), (15, 18), (19, 23)]


def _hod_bin(h):
    for i, (lo, hi) in enumerate(HOD_BINS):
        if lo <= h <= hi: return i
    return -1


def main():
    paths = {
        "lgbm": DATA / "predictions_lomo_v3_lgbm.parquet",
        "catboost": DATA / "predictions_lomo_v3_catboost.parquet",
        "xgb": DATA / "predictions_lomo_v3_xgb.parquet",
    }
    for name, p in paths.items():
        if not p.exists():
            print(f"MISSING: {name} -> {p}")
            return

    dfs = {}
    for name, p in paths.items():
        d = pd.read_parquet(p)
        d["datetime_utc"] = pd.to_datetime(d["datetime_utc"], utc=True)
        d = d[["datetime_utc", "sensor_id", "fold", "pm25_observed",
               "c_prior_anchored",
               "pm25_pred_q05", "pm25_pred_q50", "pm25_pred_q95"]]
        d = d.rename(columns={
            "pm25_pred_q05": f"q05_{name}",
            "pm25_pred_q50": f"q50_{name}",
            "pm25_pred_q95": f"q95_{name}",
        })
        dfs[name] = d
        print(f"  {name}: {len(d):,} rows")

    merge = dfs["lgbm"].merge(dfs["catboost"], on=["datetime_utc","sensor_id","fold",
                                                   "pm25_observed","c_prior_anchored"])
    merge = merge.merge(dfs["xgb"], on=["datetime_utc","sensor_id","fold",
                                        "pm25_observed","c_prior_anchored"])
    print(f"\nMerged: {len(merge):,} rows")

    # ── Blender weights via inner-fold least-squares (non-neg, sum-to-1) ──
    Q = np.stack([merge["q50_lgbm"], merge["q50_catboost"], merge["q50_xgb"]], axis=1)
    y = merge["pm25_observed"].values
    def _loss(w):
        return float(np.mean(((Q @ w) - y) ** 2))
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    bnds = [(0, 1)] * 3
    res = minimize(_loss, x0=np.array([1/3]*3), bounds=bnds, constraints=cons)
    w_lgbm, w_cat, w_xgb = res.x
    print(f"\nBlender weights:")
    print(f"  LightGBM: {w_lgbm:.3f}")
    print(f"  CatBoost: {w_cat:.3f}")
    print(f"  XGBoost:  {w_xgb:.3f}")

    merge["q50_blend"] = (w_lgbm * merge["q50_lgbm"]
                          + w_cat * merge["q50_catboost"]
                          + w_xgb * merge["q50_xgb"])
    # Blend q05/q95 with same weights (preserve order)
    merge["q05_blend"] = (w_lgbm * merge["q05_lgbm"]
                          + w_cat * merge["q05_catboost"]
                          + w_xgb * merge["q05_xgb"])
    merge["q95_blend"] = (w_lgbm * merge["q95_lgbm"]
                          + w_cat * merge["q95_catboost"]
                          + w_xgb * merge["q95_xgb"])

    # ── CV+ conformal wrap — Mondrian (calendar_month × hod_bin) ──
    merge["month"] = merge["datetime_utc"].dt.month
    merge["hod_bin"] = merge["datetime_utc"].dt.hour.apply(_hod_bin)

    out_rows = []
    for fold_id in merge["fold"].unique():
        cal = merge[merge["fold"] != fold_id].copy()
        test = merge[merge["fold"] == fold_id].copy()
        cal["score_lo"] = cal["q05_blend"] - cal["pm25_observed"]
        cal["score_hi"] = cal["pm25_observed"] - cal["q95_blend"]
        # global fallbacks
        c_lo_g = float(np.quantile(cal["score_lo"], 1 - ALPHA/2))
        c_hi_g = float(np.quantile(cal["score_hi"], 1 - ALPHA/2))
        # Mondrian lookup
        lookup = {}
        for (mo, hb), grp in cal.groupby(["month", "hod_bin"]):
            if len(grp) >= 50:
                lookup[(mo, hb)] = (
                    float(np.quantile(grp["score_lo"], 1 - ALPHA/2)),
                    float(np.quantile(grp["score_hi"], 1 - ALPHA/2)),
                )
        def _adjust(row):
            c_lo, c_hi = lookup.get((row["month"], row["hod_bin"]), (c_lo_g, c_hi_g))
            return pd.Series({
                "q05_conf": row["q05_blend"] - c_lo,
                "q95_conf": row["q95_blend"] + c_hi,
            })
        test = test.join(test.apply(_adjust, axis=1))
        out_rows.append(test)
    out = pd.concat(out_rows, ignore_index=True)

    # ── Pooled metrics ──
    def _pooled(t, q05c, q50c, q95c, label):
        err = t[q50c] - t["pm25_observed"]
        rmse = float(np.sqrt((err ** 2).mean()))
        cov = ((t["pm25_observed"] >= t[q05c]) &
               (t["pm25_observed"] <= t[q95c])).mean()
        width = (t[q95c] - t[q05c]).mean()
        r2 = 1 - (err ** 2).sum() / ((t["pm25_observed"] - t["pm25_observed"].mean()) ** 2).sum()
        return dict(model=label, n=len(t), rmse=rmse, r2=float(r2),
                    cov90=float(cov), pi_width=float(width))

    rows = [
        _pooled(merge, "q05_lgbm", "q50_lgbm", "q95_lgbm", "v3.0 LightGBM"),
        _pooled(merge, "q05_catboost", "q50_catboost", "q95_catboost", "v3.0 CatBoost"),
        _pooled(merge, "q05_xgb", "q50_xgb", "q95_xgb", "v3.0 XGBoost"),
        _pooled(merge, "q05_blend", "q50_blend", "q95_blend", "v3.0 Blender (pre-conformal)"),
        _pooled(out, "q05_conf", "q50_blend", "q95_conf", "v3.0 Blender + CV+ Mondrian"),
    ]
    summary = pd.DataFrame(rows)
    print("\n── MODEL COMPARISON (pooled across all LOMO predictions) ──")
    print(summary.to_string(index=False))

    out.to_parquet(DATA / "predictions_blend_v3.parquet", index=False)
    summary.to_csv(DATA / "summary_blend_v3.csv", index=False)
    with open(DATA / "blender_weights_v3.json", "w") as f:
        json.dump({"w_lgbm": float(w_lgbm),
                   "w_catboost": float(w_cat),
                   "w_xgb": float(w_xgb),
                   "loss_rmse": float(np.sqrt(res.fun))}, f, indent=2)
    print(f"\nSaved blender weights, predictions, summary to {DATA}")


if __name__ == "__main__":
    main()
