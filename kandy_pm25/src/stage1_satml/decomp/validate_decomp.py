"""
validate_decomp.py — validation battery for the decomposition map (plan §4, gates):

  U5  independent spatial check: annual map vs VIIRS NTL (NOT used to build the
      map) + vs elevation/delta_z (physical: higher → cleaner).
  U6  spatial sign battery: urban core > basin, highland < basin (construction
      check on S_emit — labelled non-independent).
  FECT pointwise (sanity): decomp at the Akurana/Hantana FECT pixels vs the
      calibrated FECT observations. NOTE: FECT are HIGHLAND sites; the map is
      basin-anchored, so a positive bias here diagnoses VanD's too-weak
      highland↔valley contrast, not a temporal error.

Writes results/figures/kandy_decomp/validation_report.csv (+ prints).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

DATA = HERE / "data" / "processed"
DECOMP = DATA / "decomp"
OUT = HERE / "results" / "figures" / "kandy_decomp"
OUT.mkdir(parents=True, exist_ok=True)
FECT = {12451: (7.366, 80.618), 33495: (7.356, 80.631)}


def _annual_grid(year):
    df = pd.read_parquet(DECOMP / f"kandy_decomp_predictions_{year}.parquet")
    lats = np.sort(df.lat.unique()); lons = np.sort(df.lon.unique())
    ann = df.groupby(["lat", "lon"])["pm25_q50"].mean().reset_index()
    Z = ann.pivot(index="lat", columns="lon", values="pm25_q50").values
    return Z, lats, lons


def u5_independent(year=2024):
    from scipy.interpolate import RegularGridInterpolator
    from scipy.stats import pearsonr, spearmanr
    Z, lats, lons = _annual_grid(year)

    # VIIRS NTL (31×31) → resample to map grid
    ntl = np.load(DATA / "pinn_inputs" / "kandy_viirs_ntl_stations.npz")
    nlat, nlon = ntl["lat_grid"][:, 0], ntl["lon_grid"][0, :]
    NL = ntl["NTL_log"].astype(float)
    if nlat[0] > nlat[-1]:
        nlat, NL = nlat[::-1], NL[::-1, :]
    if nlon[0] > nlon[-1]:
        nlon, NL = nlon[::-1], NL[:, ::-1]
    rgi = RegularGridInterpolator((nlat, nlon), NL, bounds_error=False, fill_value=None)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    ntl_g = rgi(np.stack([LA.ravel(), LO.ravel()], 1)).reshape(Z.shape)

    # elevation/delta_z (from M confinement npz dz_grid, already on map grid)
    dz = np.load(DECOMP / "M_confinement_kandy.npz")["dz_grid"]

    z = Z.ravel()
    out = {}
    for name, field in [("VIIRS_NTL_log", ntl_g.ravel()), ("delta_z", dz.ravel())]:
        r, p = pearsonr(z, field); rho, _ = spearmanr(z, field)
        out[name] = (r, rho, p)
    return out


def u6_signs(year=2024):
    Z, lats, lons = _annual_grid(year)
    basin = float(Z.mean())

    def at(la, lo):
        return float(Z[np.argmin(np.abs(lats - la)), np.argmin(np.abs(lons - lo))])
    city = at(7.2906, 80.6337)
    checks = {
        "urban_core>basin": (city, basin, city > basin),
        "akurana_highland<basin": (at(*FECT[12451]), basin, at(*FECT[12451]) < basin),
        "hantana_highland<basin": (at(*FECT[33495]), basin, at(*FECT[33495]) < basin),
    }
    return checks, basin


def fect_pointwise(year):
    pred = pd.read_parquet(DECOMP / f"kandy_decomp_predictions_{year}.parquet")
    pred["time"] = pd.to_datetime(pred["time"], utc=True)
    lats = np.sort(pred.lat.unique()); lons = np.sort(pred.lon.unique())
    obs = pd.read_parquet(DATA / "stage1_v3" / "dataset_v3_hourly.parquet",
                          columns=["sensor_id", "datetime_utc", "pm25_observed"])
    obs["datetime_utc"] = pd.to_datetime(obs["datetime_utc"], utc=True)
    obs = obs[obs["datetime_utc"].dt.year == year].dropna(subset=["pm25_observed"])

    rows = []
    for sid, (la, lo) in FECT.items():
        o = obs[obs.sensor_id == sid]
        if len(o) < 50:
            continue
        gla = lats[np.argmin(np.abs(lats - la))]; glo = lons[np.argmin(np.abs(lons - lo))]
        px = pred[(pred.lat == gla) & (pred.lon == glo)][
            ["time", "pm25_q05", "pm25_q50", "pm25_q95"]]
        m = o.merge(px, left_on="datetime_utc", right_on="time", how="inner")
        if len(m) < 50:
            continue
        err = m.pm25_q50 - m.pm25_observed
        rows.append(dict(
            sensor=sid, year=year, n=len(m),
            obs_mean=float(m.pm25_observed.mean()), pred_mean=float(m.pm25_q50.mean()),
            rmse=float(np.sqrt((err**2).mean())), bias=float(err.mean()),
            cov90=float(((m.pm25_observed >= m.pm25_q05) &
                         (m.pm25_observed <= m.pm25_q95)).mean())))
    return rows


def main():
    print("══ U5 — independent spatial correlation (annual 2024 map) ══")
    for name, (r, rho, p) in u5_independent(2024).items():
        exp = "+" if name == "VIIRS_NTL_log" else "−"
        print(f"  vs {name:<14} Pearson r={r:+.3f}  Spearman ρ={rho:+.3f}  (expect {exp})")

    print("\n══ U6 — spatial sign battery (construction check) ══")
    checks, basin = u6_signs(2024)
    print(f"  basin mean S·T annual = {basin:.2f}")
    for k, (v, b, ok) in checks.items():
        print(f"  {k:<26} {v:.2f} vs {b:.2f}  {'PASS' if ok else 'FAIL'}")

    print("\n══ FECT pointwise (highland sanity — bias diagnoses VanD flatness) ══")
    allrows = []
    for yr in (2019, 2024):
        for row in fect_pointwise(yr):
            allrows.append(row)
            print(f"  s{row['sensor']} {yr}: n={row['n']:<5} obs={row['obs_mean']:.1f} "
                  f"pred={row['pred_mean']:.1f} rmse={row['rmse']:.1f} "
                  f"bias={row['bias']:+.1f} cov90={row['cov90']:.2f}")
    pd.DataFrame(allrows).to_csv(OUT / "validation_fect_pointwise.csv", index=False)
    print(f"\nWrote {OUT / 'validation_fect_pointwise.csv'}")


if __name__ == "__main__":
    main()
