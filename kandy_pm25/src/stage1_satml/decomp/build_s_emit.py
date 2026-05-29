"""
build_s_emit.py — spatial multiplier S_emit(x, y) for the decomposition
PM(x, y, t) = T(t) · S_emit(x, y) · M(x, y, t)   (plan 2026-05-29 §3.2).

S_emit is the OBSERVED Van Donkelaar PM2.5 spatial pattern (multi-year mean,
2019-2023, time-stable), resampled to the canonical 16×16 ~1 km Kandy grid and
normalised to mean 1. No foreign-city LUR transfer — VanD already solved "what is
the observed PM2.5 surface over Kandy" with a global model.

Output: data/processed/decomp/S_emit_kandy.npz  (S_emit, lats, lons, years)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

from src.stage1_satml.features.vandonkelaar import spatial_multiplier_grid, POINTS

OUT_DIR = HERE / "data" / "processed" / "decomp"
OUT_DIR.mkdir(parents=True, exist_ok=True)
# Canonical grid = the existing zero-shot/heatmap grid (for side-by-side maps)
ZERO_SHOT = HERE / "data" / "processed" / "kandy_zero_shot" / \
    "kandy_predictions_20240101_0000_n8784.parquet"
YEARS = range(2019, 2024)


def canonical_grid() -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_parquet(ZERO_SHOT, columns=["lat", "lon"])
    lats = np.sort(df["lat"].unique())
    lons = np.sort(df["lon"].unique())
    return lats, lons


def main():
    lats, lons = canonical_grid()
    S = spatial_multiplier_grid(lats, lons, years=YEARS)   # (n_lat, n_lon), mean 1
    np.savez(OUT_DIR / "S_emit_kandy.npz",
             S_emit=S, lats=lats, lons=lons, years=np.array(list(YEARS)))

    # ── sanity diagnostics (U6 construction checks: VanD pattern signs) ──
    def at(la, lo):
        i = int(np.argmin(np.abs(lats - la)))
        j = int(np.argmin(np.abs(lons - lo)))
        return float(S[i, j])
    print(f"S_emit grid {S.shape}  mean={np.nanmean(S):.3f} (→1.000)  "
          f"range {np.nanmin(S):.3f}–{np.nanmax(S):.3f}")
    print(f"  Kandy city  S={at(*POINTS['city'][::1]):.3f}  (expect >1, urban core)")
    print(f"  NIFS        S={at(*POINTS['nifs']):.3f}")
    print(f"  Akurana     S={at(*POINTS['akurana_fect']):.3f}")
    print(f"  Hantana     S={at(*POINTS['hantana_fect']):.3f}")
    # contrast: top-decile vs bottom-decile pixels
    flat = S.flatten()
    hi = float(np.nanmean(flat[flat >= np.nanquantile(flat, 0.9)]))
    lo = float(np.nanmean(flat[flat <= np.nanquantile(flat, 0.1)]))
    print(f"  hot decile mean {hi:.3f} vs clean decile {lo:.3f}  "
          f"(spatial contrast {hi/lo:.2f}×)")
    print(f"\nWrote {OUT_DIR / 'S_emit_kandy.npz'}")


if __name__ == "__main__":
    main()
