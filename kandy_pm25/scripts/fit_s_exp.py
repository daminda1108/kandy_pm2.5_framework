"""fit_s_exp.py -- estimate the emission-surface exponent, the one parameter the data can constrain.

BACKGROUND
    P4 (F.75) found that of the model's five free parameters, `s_exp` -- the exponent on the
    emission surface, P_local ∝ norm(S_emit^s_exp · M · (1+amp)) -- is the ONLY one identifiable
    at every budget including Kandy's own. It has never been estimated: `diff_decomp.py`
    documents it as "implicitly 1.0, never tested", and production carries 1.0 by default.

    It matters because it is the dominant knob on spatial CONTRAST AMPLITUDE, and F.76 measured
    the model at 1.23x against an observed annual network contrast of 1.26-1.50x.

WHY IT CANNOT BE FITTED AT KANDY
    Akurana (7.366 N) lies OUTSIDE the 15x15 km domain (gotcha #49). Only Hantana is in-domain,
    so Kandy has effectively ONE usable sensor and a spatial-contrast parameter is unfittable
    there by construction. It must be fitted on the panel and transferred -- exactly the
    situation as eps0 (W7/F.30), and the transferability question is therefore the real one.

METHOD
    For each panel city with a dense network: take the real emission surface and real terrain,
    evaluate the model's relative spatial pattern at the stations' own pixels for a grid of
    s_exp, and find the value whose predicted across-station contrast (p90/p10 of the pattern)
    matches the OBSERVED across-station contrast of period-mean PM2.5.

    Contrast is compared at MATCHED SUPPORT -- period means on both sides -- which is the
    correction F.76 established.

⚠ INTERPRETATION LIMIT, STATED UP FRONT
    Observed station contrast contains SITING contrast (kerbside vs background placement) that a
    1 km areal model cannot and should not reproduce. Matching it exactly would be fitting siting.
    So the fitted value is an UPPER bound on the defensible s_exp, not a target to adopt blindly.

Usage:  python scripts/fit_s_exp.py
Out:    data/processed/modular/s_exp_fit.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "processed" / "modular" / "s_exp_fit.csv"

CITIES = ["medellin", "kathmandu", "chiangmai"]
GRID = np.round(np.arange(0.25, 3.01, 0.05), 2)
KAPPA = 0.15          # shipped prior; unidentifiable at low budget (F.75), so held


def load(city: str):
    st = np.load(REPO / f"data/processed/decomp/S_traffic_{city}.npz")
    tr = np.load(REPO / f"data/processed/pinn_inputs/{city}_terrain_core.npz")
    S = st["S_traffic"].astype(float)
    lats, lons = st["lats"].astype(float), st["lons"].astype(float)

    dz = tr["delta_z"].astype(float)
    yi = np.clip(np.linspace(0, dz.shape[0] - 1, S.shape[0]).round().astype(int), 0, dz.shape[0] - 1)
    xi = np.clip(np.linspace(0, dz.shape[1] - 1, S.shape[1]).round().astype(int), 0, dz.shape[1] - 1)
    dzr = dz[np.ix_(yi, xi)]
    c = -(dzr - dzr.mean()) / (dzr.std() + 1e-9)

    d = pd.read_parquet(REPO / f"data/processed/stage2/{city}_perstation_v13.parquet",
                        columns=["datetime_utc", "station_id", "pm25", "lat", "lon"])
    d = d.dropna(subset=["pm25", "lat", "lon"])
    d = d[d.pm25 > 0]
    g = d.groupby("station_id").agg(obs=("pm25", "mean"), n=("pm25", "size"),
                                    lat=("lat", "first"), lon=("lon", "first"))
    g = g[g.n >= 2000]                       # a period mean needs a real record behind it

    rows = []
    for sid, r in g.iterrows():
        iy = int(np.abs(lats - r.lat).argmin()); ix = int(np.abs(lons - r.lon).argmin())
        if abs(lats[iy] - r.lat) > abs(lats[1] - lats[0]) * 2: continue
        if abs(lons[ix] - r.lon) > abs(lons[1] - lons[0]) * 2: continue
        rows.append(dict(station_id=sid, obs=r.obs, iy=iy, ix=ix))
    return S / S.mean(), c, pd.DataFrame(rows)


def main() -> None:
    out = []
    for city in CITIES:
        try:
            S, c, stn = load(city)
        except Exception as e:
            print(f"{city}: FAILED {str(e)[:70]}"); continue
        if len(stn) < 8:
            print(f"{city}: only {len(stn)} in-domain stations, skipped"); continue

        obs = stn.obs.to_numpy()
        obs_contrast = float(np.percentile(obs, 90) / np.percentile(obs, 10))
        print(f"\n=== {city}: {len(stn)} in-domain stations")
        print(f"    observed station-mean contrast (p90/p10) = {obs_contrast:.3f}")

        # M is time-averaged: the diurnal weight averages to ~0.5 over a long period
        M = 1.0 + KAPPA * 0.5 * c
        best, rows = None, []
        for s in GRID:
            P = (S ** s) * M
            P = P / P.mean()
            p = P[stn.iy.to_numpy(), stn.ix.to_numpy()]
            pc = float(np.percentile(p, 90) / np.percentile(p, 10))
            rows.append((s, pc))
            if best is None or abs(pc - obs_contrast) < abs(best[1] - obs_contrast):
                best = (s, pc)
        s_hat, pc_hat = best
        at1 = [pc for s, pc in rows if abs(s - 1.0) < 1e-9][0]
        print(f"    model contrast at s_exp = 1.0 (shipped) = {at1:.3f}")
        print(f"    best-matching s_exp = {s_hat:.2f}  -> contrast {pc_hat:.3f}")
        out.append(dict(city=city, n_stations=len(stn), obs_contrast=round(obs_contrast, 3),
                        contrast_at_s1=round(at1, 3), s_exp_hat=float(s_hat),
                        contrast_at_hat=round(pc_hat, 3),
                        saturated=bool(s_hat <= GRID[0] + 1e-9 or s_hat >= GRID[-1] - 1e-9)))

    df = pd.DataFrame(out)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print("\n=== SUMMARY ===")
    print(df.to_string(index=False))
    if len(df) >= 2:
        v = df.s_exp_hat
        print(f"\nfitted s_exp across cities: {list(v)}")
        print(f"  spread {v.min():.2f} - {v.max():.2f}   ratio {v.max()/max(v.min(),1e-9):.2f}x")
        print("  TRANSFERABLE" if v.max() / max(v.min(), 1e-9) < 1.5 else
              "  DOES NOT TRANSFER -- between-city spread too large (cf. eps0, W7/F.30)")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
