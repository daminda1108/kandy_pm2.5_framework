"""kandy_loso_test.py -- leave-one-sensor-out test of the temporal anchor at Kandy (2026-10-11, ledger F.128).
EXPLORATORY.

The deployed lag-free LightGBM residual model (train_lgbm_v3 settings) is trained on ONE of the two Kandy sensors
and scored on the OTHER, which it never saw. Sensor-identity predictors (sensor id, latitude, longitude, elevation)
are removed so the model cannot know which site it predicts. The target is the residual over the anchored prior
c_prior_anchored = rho * GEOS-CF + b_sensor; for the held-out sensor the TRAINING sensor's offset is used, so the
held-out sensor's own level does not enter the prediction. The two sites are ~12 km apart and ~280 m apart in
elevation, so this tests transfer between two points of the basin, not a basin-mean skill.

Metrics on the held-out sensor, hourly and daily (Asia/Colombo days with >= 18 hours): Pearson r, RMSE, bias, and
r after removing each series' mean (shape only); the same for the composition prior alone (the model without its
learned correction) as the benchmark; and the correlation of the mean diurnal cycles.

Out: data/processed/stage1_v3/training/kandy_loso_test.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src.stage1_satml.models.train_lgbm_v3 import DATASET_PATH, get_feature_cols   # noqa: E402

OUT = REPO / "data" / "processed" / "stage1_v3" / "training" / "kandy_loso_test.json"
IDENT = {"sensor_id", "lat", "lon", "elevation_m"}
PARAMS = dict(objective="quantile", learning_rate=0.05, num_leaves=63, min_data_in_leaf=20, feature_fraction=0.85,
              bagging_fraction=0.85, bagging_freq=5, max_depth=-1, n_estimators=600, verbose=-1, random_state=20260927)


def metrics(o, m):
    o, m = np.asarray(o, float), np.asarray(m, float)
    return dict(n=int(len(o)), r=float(np.corrcoef(o, m)[0, 1]), rmse=float(np.sqrt(np.mean((m - o) ** 2))),
                bias=float(np.mean(m - o)), obs_mean=float(o.mean()))


def main():
    import lightgbm as lgb
    df = pd.read_parquet(DATASET_PATH).dropna(subset=["residual_target"]).reset_index(drop=True)
    feats = [c for c in get_feature_cols(df, lag_free=True) if c not in IDENT and not c.startswith("fold")]
    sensors = sorted(df.sensor_id.unique())
    b = df.groupby("sensor_id").apply(lambda g: float((g.c_prior_anchored - g.c_prior_scaled).median())
                                      if "c_prior_scaled" in g else 0.0)
    res = {"features": feats, "sensors": [str(s) for s in sensors]}
    for test in sensors:
        train_id = [s for s in sensors if s != test][0]
        tr, te = df[df.sensor_id == train_id], df[df.sensor_id == test].copy()
        model = lgb.LGBMRegressor(alpha=0.5, **PARAMS).fit(tr[feats], tr.residual_target)
        prior_te = te.c_prior_anchored - b[test] + b[train_id]          # training sensor's offset
        te["pred"] = prior_te + model.predict(te[feats])
        te["prior_only"] = prior_te
        t = pd.to_datetime(te.datetime_utc, utc=True).dt.tz_convert("Asia/Colombo")
        te["day"], te["hour"] = t.dt.tz_localize(None).dt.floor("D"), t.dt.hour
        g = te.groupby("day")
        D = g[["pm25_observed", "pred", "prior_only"]].mean()[g.size() >= 18]
        rec = {"train_sensor": str(train_id), "test_hours": int(len(te)), "test_days": int(len(D))}
        for lvl, X in (("hourly", te), ("daily", D)):
            for arm in ("pred", "prior_only"):
                k = metrics(X.pm25_observed, X[arm])
                k["r_shape"] = float(np.corrcoef(X.pm25_observed - X.pm25_observed.mean(), X[arm] - X[arm].mean())[0, 1])
                rec[f"{lvl}.{arm}"] = k
        dh = te.groupby("hour")[["pm25_observed", "pred", "prior_only"]].mean()
        rec["diurnal_r.pred"] = float(dh.pm25_observed.corr(dh.pred))
        rec["diurnal_r.prior_only"] = float(dh.pm25_observed.corr(dh.prior_only))
        res[f"test_{test}"] = rec
        print(f"train {train_id} -> test {test}: hourly r {rec['hourly.pred']['r']:.3f} (prior {rec['hourly.prior_only']['r']:.3f}); "
              f"daily r {rec['daily.pred']['r']:.3f} (prior {rec['daily.prior_only']['r']:.3f}); diurnal r {rec['diurnal_r.pred']:.3f}")
    tmp = OUT.with_suffix(".tmp.json"); tmp.write_text(json.dumps(res, indent=2), encoding="utf-8"); os.replace(tmp, OUT)
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
