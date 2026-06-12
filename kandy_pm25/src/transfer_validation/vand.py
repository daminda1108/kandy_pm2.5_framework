"""vand.py — Van Donkelaar V6 level anchor, rural background, and S_emit per CityPack.

Mirrors the locked Kandy recipe exactly (src/stage1_satml/features/vandonkelaar.py +
decomp/build_additive_background.py), generalised to any CityPack on the held Asia
tile (lon 65-145E, lat -10-60N):

  1. annual_levels(cp)       — per-year basin AREA mean over the city's derived bbox
                               (the level anchor L(year); beta ≡ 1, area-not-floor,
                               gotcha #51).
  2. rural_background(cp)    — per-year rural floor of the ±0.45° regional box
                               around the city centre: central = P10, bracket
                               [P05 .. P25]. (Kandy used ridge-obs 10.5 as the hard
                               lower anchor; panel cities have no ridge sensor, so
                               the bracket lower bound is P05 — documented deviation,
                               same spirit.) Also reports the satellite-implied local
                               increment fraction f_sat = 1 − B/L, the diagnostic
                               compared against the pre-registered f bracket (V6).
  3. s_emit_pattern(cp, ...) — multi-year mean VanD surface on a target grid,
                               normalised to mean 1 (the unit-mean spatial backbone).

Pure read of data/raw/van_donkelaar/*.nc — no network, no model step.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

WIDE_HALF = 0.45      # ±0.45° ≈ ±50 km regional box (same as Kandy background)
RURAL_PCTL = 10       # central rural-background estimator (P10 floor)


def _open_pm25(cp, year: int):
    """Open the VanD tile for year and return the PM25 DataArray (lazy)."""
    import xarray as xr
    tile = cp.vand_tile(year)
    if tile is None:
        raise FileNotFoundError(
            f"VanD tile not held for {cp.slug} year {year} (NA tile — Phase 4)")
    return xr.open_dataset(tile)["PM25"]


def _sel_box(da, lat0, lat1, lon0, lon1):
    """bbox select robust to ascending/descending latitude axis (Kandy guard)."""
    sub = da.sel(lat=slice(lat0, lat1), lon=slice(lon0, lon1))
    if sub.sizes.get("lat", 0) == 0:
        sub = da.sel(lat=slice(lat1, lat0), lon=slice(lon0, lon1))
    return sub


def _tile_years(years) -> list[int]:
    """Map requested years onto held tiles (2024/25 → 2023 proxy), deduped."""
    return sorted({min(int(y), 2023) for y in years})


def annual_levels(cp, years=None):
    """Per-year VanD basin AREA mean over the city's derived bbox → DataFrame."""
    import pandas as pd
    years = _tile_years(years or cp.score_years)
    b = cp.bbox()
    rows = []
    for y in years:
        da = _open_pm25(cp, y)
        sub = _sel_box(da, b["lat_min"], b["lat_max"], b["lon_min"], b["lon_max"])
        v = sub.values
        rows.append({"year": y,
                     "basin_mean": float(np.nanmean(v)),
                     "basin_p90": float(np.nanpercentile(v, 90)),
                     "basin_p10": float(np.nanpercentile(v, 10)),
                     "n_px": int(np.isfinite(v).sum())})
    return pd.DataFrame(rows)


def rural_background(cp, years=None):
    """Per-year rural VanD floor of the ±0.45° regional box → DataFrame.

    Columns: rural_p05/p10/p25/p50, region_mean, B_central (=P10),
    B_lo (=P05), B_hi (=P25), vand_basin, increment, f_sat (=increment/basin).
    f_sat is the SATELLITE-implied local fraction — the V6 diagnostic.
    """
    import pandas as pd
    years = _tile_years(years or cp.score_years)
    la0, lo0 = cp.centre()
    lev = annual_levels(cp, years).set_index("year")["basin_mean"]
    rows = []
    for y in years:
        da = _open_pm25(cp, y)
        sub = _sel_box(da, la0 - WIDE_HALF, la0 + WIDE_HALF,
                       lo0 - WIDE_HALF, lo0 + WIDE_HALF)
        v = sub.values
        v = v[np.isfinite(v)]
        basin = float(lev.loc[y])
        b_central = float(np.percentile(v, RURAL_PCTL))
        rows.append({
            "year": y,
            "rural_p05": float(np.percentile(v, 5)),
            "rural_p10": b_central,
            "rural_p25": float(np.percentile(v, 25)),
            "rural_p50": float(np.percentile(v, 50)),
            "region_mean": float(v.mean()),
            "B_central": b_central,
            "B_lo": float(np.percentile(v, 5)),
            "B_hi": float(np.percentile(v, 25)),
            "vand_basin": basin,
            "increment": basin - b_central,
            "f_sat": (basin - b_central) / basin,
        })
    return pd.DataFrame(rows)


def level_for_year(cp, year: int) -> tuple[float, int]:
    """Basin AREA level L(year) with the 2023-proxy convention (Amendment 2).

    VanD V6 ends 2023; for 2024/2025 the 2023 tile is the documented proxy —
    the same convention Kandy production uses for its 2024 maps.
    Returns (level, tile_year_used).
    """
    tile_year = min(year, 2023)
    lev = annual_levels(cp, [tile_year])
    return float(lev.basin_mean.iloc[0]), tile_year


def s_emit_pattern(cp, lats: np.ndarray, lons: np.ndarray, years=None) -> np.ndarray:
    """Multi-year mean VanD surface on (lats, lons), normalised to mean 1."""
    import xarray as xr
    years = _tile_years(years or cp.score_years)
    b = cp.bbox()
    pad = 0.05  # small halo so edge interpolation has support
    stack = []
    for y in years:
        da = _open_pm25(cp, y)
        sub = _sel_box(da, b["lat_min"] - pad, b["lat_max"] + pad,
                       b["lon_min"] - pad, b["lon_max"] + pad)
        if float(sub.lat[0]) > float(sub.lat[-1]):
            sub = sub.sortby("lat")
        stack.append(sub.assign_coords(year=y))
    mean_surf = xr.concat(stack, dim="year").mean("year")
    arr = mean_surf.interp(lat=xr.DataArray(lats, dims="lat"),
                           lon=xr.DataArray(lons, dims="lon")).values
    return arr / np.nanmean(arr)


def _selftest() -> int:
    from .citypack import get
    ok = True
    for slug in ("xichang", "chandigarh", "kathmandu", "medellin"):
        cp = get(slug)
        try:
            bg = rural_background(cp)
            lat = np.linspace(cp.bbox()["lat_min"], cp.bbox()["lat_max"], 32)
            lon = np.linspace(cp.bbox()["lon_min"], cp.bbox()["lon_max"], 32)
            S = s_emit_pattern(cp, lat, lon)
            print(f"\n=== {slug} ===")
            print(bg[["year", "vand_basin", "B_central", "B_lo", "B_hi", "f_sat"]]
                  .round(2).to_string(index=False))
            print(f"S_emit: shape={S.shape} mean={np.nanmean(S):.4f} "
                  f"range=[{np.nanmin(S):.3f},{np.nanmax(S):.3f}]  "
                  f"f_sat mean={bg.f_sat.mean():.2f} vs prereg bracket {cp.f_bracket}")
        except FileNotFoundError as e:
            print(f"\n=== {slug} === SKIP ({e})")
            if slug != "medellin":   # only the NA-tile gap is expected
                ok = False
        except Exception as e:  # noqa: BLE001
            print(f"\n=== {slug} === ERR {type(e).__name__}: {e}")
            ok = False
    print("\nVAND SELFTEST", "PASS" if ok else "ERRORS")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())
