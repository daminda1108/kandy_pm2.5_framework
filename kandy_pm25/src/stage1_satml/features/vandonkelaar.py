"""
vandonkelaar.py — Van Donkelaar ACAG V6.GL02.04 annual PM2.5 surface utilities.

Two roles in the production decomposition (plan 2026-05-29):
  1. LEVEL anchor for T(t): per-year, bias-corrected basin annual mean
     L(year) = beta · VanD_basin(year), where beta pins VanD to the one
     valley-floor ground truth we have (KOALA 2019 = 24.5225 µg/m³ at NIFS Kandy,
     Senarathna 2024). VanD reads ~25% low over Kandy, so the raw surface is NOT
     used unbias-corrected. This replaces the old "force annual mean = KOALA"
     re-anchor — the level is now per-year and observation-grounded.
  2. (Phase 1) spatial backbone for S_emit(x, y): the normalised VanD surface.

Data: data/raw/van_donkelaar/V6GL02.04.CNNPM25.AS.{YYYY}01-{YYYY}12.nc
      0.01° (~1.1 km), variable 'PM25' (µg/m³), Asia tile. Coverage 1998–2023.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

from config import KANDY_PINN_BBOX, KOALA_ANCHOR_UG_M3

VAND_DIR = HERE / "data" / "raw" / "van_donkelaar"
OUT_CSV = HERE / "data" / "processed" / "stage1_v3" / "vandonkelaar_kandy_annual.csv"
OUT_JSON = HERE / "data" / "processed" / "stage1_v3" / "vandonkelaar_level_meta.json"

# Diagnostic point locations (lat, lon)
POINTS = {
    "nifs": (7.2675, 80.5985),       # NIFS Kandy (KOALA / Senarathna station)
    "city": (7.2906, 80.6337),       # Kandy city centre
    "akurana_fect": (7.366, 80.618),
    "hantana_fect": (7.265, 80.625),
}


def _year_of(path: str) -> int:
    # filename: V6GL02.04.CNNPM25.AS.201901-201912.nc  → token[4] = '201901-201912'
    return int(os.path.basename(path).split(".")[4][:4])


def annual_kandy_levels(min_year: int = 2015) -> pd.DataFrame:
    """Per-year VanD annual mean over the Kandy PINN bbox + diagnostic points."""
    import xarray as xr

    bb = KANDY_PINN_BBOX
    files = sorted(glob.glob(str(VAND_DIR / "V6GL02*.nc")))
    files = [f for f in files if _year_of(f) >= min_year]
    rows = []
    for f in files:
        ds = xr.open_dataset(f)
        da = ds["PM25"]
        sub = da.sel(lat=slice(bb["lat_min"], bb["lat_max"]),
                     lon=slice(bb["lon_min"], bb["lon_max"]))
        if sub.size == 0:  # latitude stored descending
            sub = da.sel(lat=slice(bb["lat_max"], bb["lat_min"]),
                         lon=slice(bb["lon_min"], bb["lon_max"]))
        row = {"year": _year_of(f), "basin_mean": float(sub.mean())}
        for name, (la, lo) in POINTS.items():
            row[name] = float(da.sel(lat=la, lon=lo, method="nearest"))
        rows.append(row)
        ds.close()
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def spatial_multiplier_grid(lats: np.ndarray, lons: np.ndarray,
                            years=range(2019, 2024)) -> np.ndarray:
    """VanD spatial pattern S_emit on a target grid, normalised to mean 1.

    Uses a multi-year mean (default 2019-2023) so the *pattern* is time-stable
    (the per-year *level* lives in T(t), not here). Bilinear-interpolated from the
    0.01° VanD surface to the (lats × lons) grid. Returns a (n_lat, n_lon) array
    with mean(S_emit) = 1 by construction — the dimensionless spatial multiplier
    in PM(x,y,t) = T(t)·S_emit(x,y)·M(x,y,t).
    """
    import xarray as xr

    files = {y: f for f in glob.glob(str(VAND_DIR / "V6GL02*.nc"))
             for y in [_year_of(f)]}
    use = [files[y] for y in years if y in files]
    if not use:
        raise ValueError(f"No VanD files for years {list(years)}")
    pad = 0.05  # subset a little beyond grid for clean bilinear edges
    la0, la1 = float(np.min(lats)) - pad, float(np.max(lats)) + pad
    lo0, lo1 = float(np.min(lons)) - pad, float(np.max(lons)) + pad
    stack = []
    for f in use:
        ds = xr.open_dataset(f)
        sub = ds["PM25"].sel(lat=slice(la0, la1), lon=slice(lo0, lo1))
        if sub.size == 0:
            sub = ds["PM25"].sel(lat=slice(la1, la0), lon=slice(lo0, lo1))
        stack.append(sub)
        ds.close()
    mean_surf = xr.concat(stack, dim="year").mean("year")
    target = xr.DataArray(lats, dims="y"), xr.DataArray(lons, dims="x")
    interp = mean_surf.interp(lat=target[0], lon=target[1])
    arr = interp.values  # (n_lat, n_lon)
    return arr / np.nanmean(arr)


def bias_factor(levels: pd.DataFrame, ref_year: int = 2019,
                koala: float = KOALA_ANCHOR_UG_M3) -> float:
    """Multiplicative bias correction pinning VanD basin-mean to KOALA at ref_year.

    KOALA (NIFS valley floor, Senarathna 2024) is the only valley-floor ground
    truth; we assume it represents the basin annual level and that VanD's
    low-bias over Kandy is uniform-multiplicative.
    """
    v = levels.loc[levels["year"] == ref_year, "basin_mean"]
    if v.empty:
        raise ValueError(f"No VanD basin_mean for ref_year {ref_year}")
    return float(koala / v.iloc[0])


def build_levels_table() -> pd.DataFrame:
    """Compute, persist, and return the per-year bias-corrected level table."""
    levels = annual_kandy_levels()
    beta = bias_factor(levels)
    levels["beta"] = beta
    levels["L_corrected"] = beta * levels["basin_mean"]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    levels.to_csv(OUT_CSV, index=False)
    latest = int(levels["year"].max())
    json.dump({
        "beta": beta,
        "ref_year": 2019,
        "koala_anchor": KOALA_ANCHOR_UG_M3,
        "vand_basin_2019": float(levels.loc[levels.year == 2019, "basin_mean"].iloc[0]),
        "latest_year_available": latest,
        "method": "L(year) = beta * VanD_basin(year); beta = KOALA_2019 / VanD_basin_2019",
        "source": "ACAG V6.GL02.04 CNN PM2.5 annual, 0.01deg, Asia tile",
    }, open(OUT_JSON, "w"), indent=2)
    return levels


def level_for_year(year: int) -> tuple[float, dict]:
    """Bias-corrected basin annual level for `year`.

    If `year` is beyond VanD coverage (currently >2023), fall back to the latest
    available year as a proxy and flag it in the returned info dict.
    """
    if OUT_CSV.exists():
        levels = pd.read_csv(OUT_CSV)
    else:
        levels = build_levels_table()
    avail = sorted(levels["year"].tolist())
    proxy_year, proxied = year, False
    if year not in avail:
        proxy_year, proxied = max(avail), True
    L = float(levels.loc[levels["year"] == proxy_year, "L_corrected"].iloc[0])
    info = {"target_year": year, "proxy_year": proxy_year, "proxied": proxied,
            "L": L, "beta": float(levels["beta"].iloc[0])}
    return L, info


if __name__ == "__main__":
    tab = build_levels_table()
    beta = float(tab["beta"].iloc[0])
    print(f"beta (KOALA_2019 / VanD_basin_2019) = {beta:.4f}")
    print(tab[["year", "basin_mean", "nifs", "city", "L_corrected"]].to_string(index=False))
    print(f"\nWrote {OUT_CSV}")
    print(f"Wrote {OUT_JSON}")
    L24, info = level_for_year(2024)
    print(f"\nL(2024) = {L24:.2f} µg/m³  (proxy_year={info['proxy_year']}, proxied={info['proxied']})")
