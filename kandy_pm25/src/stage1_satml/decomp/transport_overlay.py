"""
transport_overlay.py — Tier-B physics enhancement: a DETERMINISTIC steady-state
advection–dispersion transport overlay for the decomposition (plan
docs/decomp_enhancement_analysis_2026-05-31.md §4).

Solves   u·∇C − ∇·(K∇C) + v_d·C = S   (upwind advection, central diffusion,
deposition sink) per ERA5 wind octant on a refined grid, with an emission-source
proxy S from VIIRS night-lights. The per-octant fields are weighted by the
observed wind-frequency distribution → a climatological transport modulation
Ã(x,y) (mean-normalised, so the VanD/KOALA basin anchor is preserved).

NOT a PINN (PINN spatial is cancelled). Mechanistic → defensible without local
fitting; within-basin gradients remain FIELD-UNVALIDATED (validate vs MAIAC/NTL).
Experimental v1.1 — does NOT replace the locked v1.

Output: data/processed/decomp/transport_overlay.npz (A 16×16, mean 1) + diagnostics.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.interpolate import RegularGridInterpolator

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))
from config import KANDY_PINN_BBOX as BB

PINN = HERE / "data" / "processed" / "pinn_inputs"
DECOMP = HERE / "data" / "processed" / "decomp"

N = 64                                   # solver grid
K_DIFF = 120.0                           # horizontal eddy diffusivity (m²/s)
SPEED = 2.0                              # representative wind speed (m/s, ERA5 ~2)
V_DEP, H_MIX = 0.003, 1000.0            # deposition velocity (m/s), mixing height (m)
LAM = V_DEP / H_MIX                       # first-order loss (1/s)
# observed wind-frequency by octant (N..NW) from FECT/ERA5 (Probe B counts)
WIND_FREQ = np.array([896, 2901, 3816, 1249, 1775, 6789, 1401, 699], float)
WIND_FREQ /= WIND_FREQ.sum()
OCTANTS = np.arange(8) * 45.0            # met direction FROM which wind blows


def _source_grid():
    """Emission proxy S(x,y) from VIIRS NTL, resampled to the N×N solver grid."""
    z = np.load(PINN / "kandy_viirs_ntl_stations.npz")
    nlat, nlon = z["lat_grid"][:, 0], z["lon_grid"][0, :]
    NL = z["NTL"].astype(float)
    if nlat[0] > nlat[-1]:
        nlat, NL = nlat[::-1], NL[::-1, :]
    if nlon[0] > nlon[-1]:
        nlon, NL = nlon[::-1], NL[:, ::-1]
    rgi = RegularGridInterpolator((nlat, nlon), NL, bounds_error=False, fill_value=0.0)
    lats = np.linspace(BB["lat_min"], BB["lat_max"], N)
    lons = np.linspace(BB["lon_min"], BB["lon_max"], N)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    S = rgi(np.stack([LA.ravel(), LO.ravel()], 1)).reshape(N, N)
    S = np.clip(S, 0, None)
    return S / (S.max() + 1e-9), lats, lons


def _solve(S, ux, uy, dx):
    """Steady-state u·∇C − K∇²C + λC = S (upwind), Dirichlet C=0 boundaries."""
    A = sp.lil_matrix((N * N, N * N))
    b = S.flatten().astype(float).copy()
    kd = K_DIFF / dx ** 2
    for i in range(N):
        for j in range(N):
            k = i * N + j
            if i in (0, N - 1) or j in (0, N - 1):
                A[k, k] = 1.0; b[k] = 0.0; continue
            diag = 4 * kd + LAM
            # diffusion neighbours
            A[k, k - N] += -kd; A[k, k + N] += -kd
            A[k, k - 1] += -kd; A[k, k + 1] += -kd
            # advection (upwind). x=lon=j (ux), y=lat=i (uy)
            if ux >= 0: diag += ux / dx; A[k, k - 1] += -ux / dx
            else:       diag += -ux / dx; A[k, k + 1] += ux / dx
            if uy >= 0: diag += uy / dx; A[k, k - N] += -uy / dx
            else:       diag += -uy / dx; A[k, k + N] += uy / dx
            A[k, k] += diag
    C = spla.spsolve(A.tocsr(), b)
    return C.reshape(N, N)


def main():
    S, lats, lons = _source_grid()
    dx = (BB["lat_max"] - BB["lat_min"]) * 111000.0 / (N - 1)   # ~238 m
    fields = []
    for d in OCTANTS:
        # met dir FROM d → wind vector points TO (d+180): u=-s·sin, v=-s·cos
        ux = -SPEED * np.sin(np.radians(d))
        uy = -SPEED * np.cos(np.radians(d))
        fields.append(_solve(S, ux, uy, dx))
    clim = np.tensordot(WIND_FREQ, np.array(fields), axes=(0, 0))   # (N,N)

    # mean-normalise (preserve basin anchor); resample to canonical 16×16 grid
    A64 = 1.0 + (clim - clim.mean()) / (clim.mean() + 1e-9)         # multiplicative, mean≈1
    A64 = np.clip(A64, 0.5, 2.5)
    rgi = RegularGridInterpolator((lats, lons), A64)
    g16_lat = np.linspace(BB["lat_min"], BB["lat_max"], 16)
    g16_lon = np.linspace(BB["lon_min"], BB["lon_max"], 16)
    # use the canonical zero-shot grid for exact alignment
    import pandas as pd
    zs = pd.read_parquet(HERE / "data/processed/kandy_zero_shot/"
                         "kandy_predictions_20240101_0000_n8784.parquet",
                         columns=["lat", "lon"])
    g16_lat = np.sort(zs.lat.unique()); g16_lon = np.sort(zs.lon.unique())
    LA, LO = np.meshgrid(np.clip(g16_lat, lats.min(), lats.max()),
                         np.clip(g16_lon, lons.min(), lons.max()), indexing="ij")
    A16 = rgi(np.stack([LA.ravel(), LO.ravel()], 1)).reshape(16, 16)
    A16 = A16 / A16.mean()

    np.savez(DECOMP / "transport_overlay.npz", A=A16, lats=g16_lat, lons=g16_lon,
             A64=A64, source=S, params=dict(K=K_DIFF, speed=SPEED, lam=LAM))
    print(f"Transport overlay Ã: mean {A16.mean():.3f}  range {A16.min():.2f}–{A16.max():.2f}  "
          f"contrast(p90/p10) {np.quantile(A16,0.9)/np.quantile(A16,0.1):.2f}×")
    print(f"Wrote {DECOMP / 'transport_overlay.npz'}")


if __name__ == "__main__":
    main()
