"""
build_m_confinement.py — spatial confinement field c(x, y) for the meteorological
modulation M(x, y, t) in the decomposition (plan 2026-05-29 §3.3).

    M(x, y, t) = 1 + kappa · w(BLH_t) · c(x, y)        (spatial-mean(M)=1 per hour)

This restores the time-dependent spatial structure that a separable T(t)·S_emit
throws away: under a shallow nocturnal boundary layer, valley-floor pixels pool
pollution relative to ridges; by midday the contrast collapses. M factorises into
a time-invariant confinement field c(x,y) (built here) and an hour-varying
trapping weight w(BLH_t) (computed at assembly from the inference grid's blh_m).

  c(x, y) = z-score(-delta_z) over the grid  → +ve in enclosed valley floor,
            -ve on ridges; mean 0 so spatial-mean(M)=1 holds exactly.
  w(t)    = clip((H_ridge - BLH_t) / H_ridge, 0, 1)  → 1 at full nocturnal
            trapping (BLH ≪ ridge), 0 when well-mixed (BLH ≥ ridge).

kappa and H_ridge are PHYSICAL PRIORS, not fitted — there is no within-Kandy
hourly multi-point ground truth to calibrate them yet. They are the knobs to
calibrate once KOALA/NBRO hourly data arrives (plan U8). Documented as such.

Output: data/processed/decomp/M_confinement_kandy.npz (c, lats, lons, kappa, H_ridge)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

TERRAIN_NPZ = HERE / "data" / "processed" / "pinn_inputs" / "kandy_terrain_tpi_svf_100m.npz"
ZERO_SHOT = HERE / "data" / "processed" / "kandy_zero_shot" / \
    "kandy_predictions_20240101_0000_n8784.parquet"
OUT_DIR = HERE / "data" / "processed" / "decomp"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Physical priors (uncalibrated — to be tuned with KOALA/NBRO hourly data, U8)
KAPPA = 0.15        # max fractional amplitude per 1σ confinement at full trapping
H_RIDGE_M = 300.0   # effective ridge/trapping height above valley floor (NPZ: H_trap=200, max delta_z=414)
CLIP_SIGMA = 2.5    # clip confinement z-score tails


def canonical_grid() -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_parquet(ZERO_SHOT, columns=["lat", "lon"])
    return np.sort(df["lat"].unique()), np.sort(df["lon"].unique())


def main():
    from scipy.interpolate import RegularGridInterpolator

    z = np.load(TERRAIN_NPZ)
    dz = z["delta_z"].astype(float)                 # (150,150) height above valley floor
    lat2d, lon2d = z["lat_grid"], z["lon_grid"]
    lat1d, lon1d = lat2d[:, 0], lon2d[0, :]
    # ensure ascending for the interpolator
    if lat1d[0] > lat1d[-1]:
        lat1d, dz = lat1d[::-1], dz[::-1, :]
    if lon1d[0] > lon1d[-1]:
        lon1d, dz = lon1d[::-1], dz[:, ::-1]

    lats, lons = canonical_grid()
    rgi = RegularGridInterpolator((lat1d, lon1d), dz, bounds_error=False,
                                  fill_value=None)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    dz_grid = rgi(np.stack([LA.ravel(), LO.ravel()], axis=1)).reshape(LA.shape)

    # confinement: enclosed valley floor (low delta_z) → positive, mean 0
    c = -(dz_grid - dz_grid.mean()) / dz_grid.std()
    c = np.clip(c, -CLIP_SIGMA, CLIP_SIGMA)
    c = c - c.mean()    # re-centre after clip so spatial-mean(M)=1 holds

    np.savez(OUT_DIR / "M_confinement_kandy.npz",
             c=c, lats=lats, lons=lons,
             kappa=KAPPA, H_ridge_m=H_RIDGE_M, dz_grid=dz_grid)

    # diagnostics
    def at(la, lo):
        i = int(np.argmin(np.abs(lats - la)))
        j = int(np.argmin(np.abs(lons - lo)))
        return float(c[i, j]), float(dz_grid[i, j])
    print(f"confinement c(x,y) grid {c.shape}  mean={c.mean():+.3f}  "
          f"range {c.min():+.2f}..{c.max():+.2f}")
    for name, (la, lo) in {"Kandy_city": (7.2906, 80.6337),
                           "Akurana": (7.366, 80.618),
                           "Hantana": (7.265, 80.625)}.items():
        cc, dd = at(la, lo)
        print(f"  {name:<11} c={cc:+.2f}  delta_z={dd:.0f} m")
    # implied nocturnal contrast at full trapping (w=1)
    m_hi = 1 + KAPPA * 1.0 * c.max()
    m_lo = 1 + KAPPA * 1.0 * c.min()
    print(f"  → nocturnal M range {m_lo:.2f}..{m_hi:.2f}  "
          f"(valley/ridge contrast {m_hi/m_lo:.2f}× at full trapping, kappa={KAPPA})")
    print(f"\nWrote {OUT_DIR / 'M_confinement_kandy.npz'}")


if __name__ == "__main__":
    main()
