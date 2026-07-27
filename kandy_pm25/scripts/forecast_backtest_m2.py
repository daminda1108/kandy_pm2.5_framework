"""forecast_backtest_m2.py — F-M2: end-to-end forecast-driver backtest (2026-07-10).

The decisive test: does the 2-anchor T(t) survive being driven by ARCHIVED GEOS-CF
FORECAST drivers instead of the analysis/reanalysis drivers it trained on?

Procedure (Medellín, 2023; ground truth = 22 held-out stations):
  1. Pick a 2-station gradient anchor (clean + dirty, well-sampled); hold out the rest.
  2. ratio = anchor row-mean pm25 / c_prior (scales the prior; gotcha #39).
  3. Train the lag-free LGBM quantile heads on ANALYSIS drivers + anchor obs
     (residual target = anchor_pm - c_prior_scaled), exactly as validated.
  4. Predict T(t) two ways on the same 2023 valid hours:
       ANALYSIS-driven  (reference: ERA5 met + GEOS-CF analysis prior)
       FORECAST-driven  (operational: archived GEOS-CF forecast drivers, ~24 h lead)
  5. Score both vs the held-out-station area-mean, + baselines (24 h persistence,
     raw scaled GEOS-CF forecast). Report RMSE / r / seasonal r / diurnal r /
     skill-vs-persistence — the FG2 gate.

Run:  .venv/Scripts/python.exe scripts/forecast_backtest_m2.py --city medellin
Out:  data/processed/stage1_v3/training/forecast_backtest_m2_{city}.csv + printed table
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

REPO = Path(__file__).resolve().parents[1]
STG = REPO / "data" / "processed" / "stage2"
FCST = REPO / "data" / "external" / "geoscf_forecast"
OUT = REPO / "data" / "processed" / "stage1_v3" / "training"

FEATURES = ["sin_h", "cos_h", "sin_doy", "cos_doy", "dow",
            "blh", "u10", "v10", "wspd", "t2m", "c_prior_scaled"]
LGBM = dict(objective="quantile", learning_rate=0.05, num_leaves=63,
            n_estimators=600, min_child_samples=20, subsample=0.8,
            colsample_bytree=0.8, verbose=-1, n_jobs=-1)
STATION_PARQUET = {"medellin": "medellin_perstation_v13.parquet"}


def _calendar(df, tcol="valid"):
    dt = df[tcol]
    df["sin_h"] = np.sin(2 * np.pi * dt.dt.hour / 24)
    df["cos_h"] = np.cos(2 * np.pi * dt.dt.hour / 24)
    doy = dt.dt.dayofyear
    df["sin_doy"] = np.sin(2 * np.pi * doy / 365.25)
    df["cos_doy"] = np.cos(2 * np.pi * doy / 365.25)
    df["dow"] = dt.dt.dayofweek
    return df


def _shape_r(a, b, by):
    """correlation of the `by`-grouped means (diurnal / seasonal shape)."""
    g = pd.DataFrame({"a": a, "b": b, "by": by}).groupby("by").mean()
    return float(np.corrcoef(g.a, g.b)[0, 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="medellin", choices=list(STATION_PARQUET))
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--train-end", type=int, default=None,
                    help="last year (inclusive) allowed in TRAINING. Default = year-1, "
                         "i.e. a clean temporal split. Pass the eval year to reproduce "
                         "the original leaky run.")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    d = pd.read_parquet(STG / STATION_PARQUET[a.city])
    d["valid"] = pd.to_datetime(d["datetime_utc"], utc=True)

    # --- 2-station gradient anchor: highest & lowest mean PM among well-sampled ---
    cov = (d[d.valid.dt.year == a.year].groupby("station_id")
           .agg(n=("pm25", "size"), pm=("pm25", "mean")))
    well = cov[cov.n > 3000].sort_values("pm")
    anchors = [well.index[-1], well.index[0]]      # dirtiest + cleanest
    held = [s for s in cov.index if s not in anchors]
    print(f"{a.city} {a.year}: anchors {anchors} (pm {well.pm.iloc[-1]:.1f}/{well.pm.iloc[0]:.1f}) "
          f"| {len(held)} held-out stations")

    # --- ratio + anchor obs (residual target on the analysis prior) ---
    an = d[d.station_id.isin(anchors)].dropna(subset=["pm25", "c_prior"])
    ratio = float(an.pm25.mean() / an.c_prior.mean())
    anchor_obs = an.groupby("valid")["pm25"].mean().rename("anchor_pm")

    # --- ANALYSIS driver table (area-mean per valid hour) ---
    drv = (d.groupby("valid")
             .agg(c_prior=("c_prior", "mean"), blh=("blh", "mean"),
                  u10=("u10", "mean"), v10=("v10", "mean"), t2m=("t2m", "mean"))
             .reset_index())
    drv["c_prior_scaled"] = drv["c_prior"] * ratio
    drv["wspd"] = np.hypot(drv.u10, drv.v10)
    drv = _calendar(drv)

    # --- train on analysis drivers + anchor obs ---
    # CLEAN TEMPORAL SPLIT: a forecast model must not have trained on the period it is
    # scored on. The original run trained on ALL anchor-hours including the evaluation
    # year, which inflates skill against persistence (persistence gets no such look-ahead).
    tr = drv.merge(anchor_obs, on="valid").dropna(subset=FEATURES + ["anchor_pm"])
    train_end = a.train_end if a.train_end is not None else a.year - 1
    n_all = len(tr)
    tr = tr[tr.valid.dt.year <= train_end]
    print(f"  temporal split: train <= {train_end}, eval {a.year}  "
          f"({n_all:,} -> {len(tr):,} anchor-hours)")
    if tr.empty:
        raise SystemExit(f"no training hours at or before {train_end}")
    tr["resid"] = tr["anchor_pm"] - tr["c_prior_scaled"]
    heads = {q: LGBMRegressor(alpha=q, **LGBM).fit(tr[FEATURES], tr["resid"])
             for q in (0.05, 0.50, 0.95)}
    print(f"  trained on {len(tr):,} anchor-hours; ratio {ratio:.3f}")

    # --- FORECAST driver table (archived GEOS-CF forecast, nearest-24h lead) ---
    f = pd.read_csv(FCST / f"geoscf_fcst_{a.city}_{a.year}.csv")
    f["valid"] = pd.to_datetime(f.valid_ms, unit="ms", utc=True)
    f["dl"] = (f.lead_h - 24).abs()
    f = f.sort_values("dl").drop_duplicates("valid_ms")
    fdrv = f.rename(columns={"PM25_RH35_GCC": "c_prior", "ZPBL": "blh",
                             "U10M": "u10", "V10M": "v10", "T2M": "t2m"})
    fdrv["c_prior_scaled"] = fdrv["c_prior"] * ratio
    fdrv["wspd"] = np.hypot(fdrv.u10, fdrv.v10)
    fdrv = _calendar(fdrv)

    # --- held-out ground truth: area-mean of held-out stations per valid hour ---
    ho = (d[d.station_id.isin(held) & (d.valid.dt.year == a.year)]
          .groupby("valid")["pm25"].mean().rename("obs"))

    def predict(table):
        t = table.dropna(subset=FEATURES).copy()
        t["Tt"] = t["c_prior_scaled"] + heads[0.50].predict(t[FEATURES])
        return t.set_index("valid")["Tt"].clip(lower=0)

    T_anal = predict(drv)
    T_fcst = predict(fdrv)
    raw_fcst = fdrv.set_index("valid")["c_prior_scaled"].clip(lower=0)   # baseline

    # align everything on held-out valid hours (2023)
    ev = pd.concat([ho, T_anal.rename("T_anal"), T_fcst.rename("T_fcst"),
                    raw_fcst.rename("raw_fcst")], axis=1).dropna(subset=["obs"])
    ev = ev[ev.index.year == a.year]
    persist = ev["obs"].shift(24)                     # 24-h persistence baseline

    def score(pred, name):
        m = ev.assign(p=pred).dropna(subset=["p", "obs"])
        rmse = float(np.sqrt(((m.p - m.obs) ** 2).mean()))
        r = float(np.corrcoef(m.p, m.obs)[0, 1])
        sr = _shape_r(m.p.values, m.obs.values, m.index.month)
        dr = _shape_r(m.p.values, m.obs.values, m.index.hour)
        return dict(pred=name, n=len(m), rmse=round(rmse, 2), r=round(r, 3),
                    seasonal_r=round(sr, 3), diurnal_r=round(dr, 3))

    # showcase artifact: the full held-out evaluation series (Act 2 packaging)
    ev.assign(persist=persist).to_csv(OUT / f"forecast_series_{a.city}_{a.year}_train{a.train_end if a.train_end is not None else a.year-1}.csv")

    rows = [score(ev["T_anal"], "anchor / ANALYSIS (ref)"),
            score(ev["T_fcst"], "anchor / FORECAST"),
            score(ev["raw_fcst"], "raw scaled GEOS-CF fcst"),
            score(persist, "24h persistence")]
    res = pd.DataFrame(rows)
    rmse_p = res.loc[res.pred == "24h persistence", "rmse"].iloc[0]
    res["skill_vs_persist"] = (1 - res["rmse"] / rmse_p).round(3)
    OUT.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT / f"forecast_backtest_m2_{a.city}_train{a.train_end if a.train_end is not None else a.year-1}.csv", index=False)

    print(f"\n=== F-M2 held-out backtest ({a.city} {a.year}, {len(ev)} hours, "
          f"{len(held)} stations) ===")
    print(res.to_string(index=False))
    rf = res.loc[res.pred == "anchor / FORECAST"].iloc[0]
    ra = res.loc[res.pred == "anchor / ANALYSIS (ref)"].iloc[0]
    print(f"\nFG2 gates:")
    print(f"  forecast beats 24h persistence:      "
          f"{'PASS' if rf.skill_vs_persist > 0 else 'FAIL'} (skill {rf.skill_vs_persist:+.3f})")
    print(f"  forecast beats raw GEOS-CF forecast: "
          f"{'PASS' if rf.rmse < res.loc[res.pred=='raw scaled GEOS-CF fcst','rmse'].iloc[0] else 'FAIL'}")
    print(f"  forecast retains anchor skill: seasonal {rf.seasonal_r/ra.seasonal_r*100:.0f}% "
          f"diurnal {rf.diurnal_r/max(ra.diurnal_r,0.01)*100:.0f}% of analysis-driven")
    print(f"\nWrote {OUT / f'forecast_backtest_m2_{a.city}.csv'}")


if __name__ == "__main__":
    main()
