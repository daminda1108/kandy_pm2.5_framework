"""
sharpen_T_diurnal.py — diurnal-amplitude bias-correction for the temporal anchor T(t)
(2026-06-05).

The lag-free GBM that produces T(t) reproduces the diurnal SHAPE well (corr 0.95 vs the
observed FECT climatology) but REGRESSES TO THE MEAN — it damps the bimodal swing to
~85% of observed: deep-night (00–05) is ~0.94 of the daily mean where the data say 0.87,
and the 07 LT rush peak is ~1.31 where the data say 1.40. Kandy's PM2.5 is traffic-
dominated and the city is quiet overnight (confirmed: observed FECT deep-night ≈ daily
minimum; Senarathna/CJS 2024 — "highest early morning & evening, lowest afternoon"), so
the damped night is unphysical.

Fix: a per-local-hour multiplicative correction k(h) = obs_norm(h) / Tmodel_norm(h) that
maps T(t)'s diurnal climatology onto the observed FECT one, applied to every quantile,
then re-anchored so the annual mean (the van Donkelaar area level) is preserved exactly.
This is a climatology bias-correction to a calibration input (FECT), so it is consistency,
not new validation. Overwrites the T_anchor parquets in place.

Run after predict_T_anchor_v3.py, before build_decomp_map.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
STG = REPO / "data" / "processed" / "stage1_v3"
TANCHOR = STG / "T_anchor"
YEARS = range(2019, 2025)
QCOLS = ["T_q05", "T_q50", "T_q95", "T_q05_preanchor", "T_q50_preanchor", "T_q95_preanchor"]


def _obs_norm(by):
    d = pd.read_parquet(STG / "dataset_v3_hourly.parquet",
                        columns=["datetime_utc", "pm25_observed"]).dropna()
    t = pd.to_datetime(d.datetime_utc, utc=True).dt.tz_convert("Asia/Colombo")
    key = t.dt.hour if by == "h" else t.dt.month
    di = d.groupby(key)["pm25_observed"].mean()
    return di / di.mean()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    obs_h, obs_m = _obs_norm("h"), _obs_norm("m")   # observed DIURNAL + SEASONAL climatologies
    print("=== sharpening T(t) -> observed FECT swing (diurnal + seasonal) ===")
    print(f"  obs deep-night {obs_h[[0,1,2,3,4,5]].mean():.2f} peak07 {obs_h[7]:.2f} | "
          f"obs Mar {obs_m[3]:.2f} Aug {obs_m[8]:.2f} (swing {obs_m.max()/obs_m.min():.2f}x)")
    for y in YEARS:
        p = TANCHOR / f"T_kandy_hourly_{y}.parquet"
        if not p.exists():
            continue
        T = pd.read_parquet(p)
        tl = pd.to_datetime(T["datetime_utc"], utc=True).dt.tz_convert("Asia/Colombo")
        T["_h"] = tl.dt.hour; T["_m"] = tl.dt.month
        cols = [c for c in QCOLS if c in T.columns]
        orig = float(T["T_q50"].mean())
        # diurnal correction (≈1 if already sharpened) × seasonal correction
        mh = T.groupby("_h")["T_q50"].mean(); mh /= mh.mean()
        kh = (obs_h / mh); kh /= (kh * mh).sum() / mh.sum()
        mm = T.groupby("_m")["T_q50"].mean(); mm /= mm.mean()
        km = (obs_m / mm); km /= (km * mm).sum() / mm.sum()
        kv = T["_h"].map(kh.to_dict()).values * T["_m"].map(km.to_dict()).values
        for c in cols:
            T[c] = T[c].values * kv
        scale = orig / float(T["T_q50"].mean())                       # re-anchor annual level
        for c in cols:
            T[c] = T[c] * scale
        sm = T.groupby("_m")["T_q50"].mean() / T["T_q50"].mean()
        T = T.drop(columns=["_h", "_m"]); T.to_parquet(p, index=False)
        print(f"  {y}: Mar {sm[3]:.2f} Aug {sm[8]:.2f} (swing {sm.max()/sm.min():.2f}x)  "
              f"annual mean {orig:.2f}->{T['T_q50'].mean():.2f}")
    print("\nT_anchor sharpened (diurnal+seasonal). Re-run: build_decomp_map -> build_overlay_predictions"
          " -> build_spatial_uq -> build_additive_field -> exposure/burden -> figures.")


if __name__ == "__main__":
    main()
