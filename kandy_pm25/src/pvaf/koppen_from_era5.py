"""Derive Köppen-Geiger climate class from ERA5 monthly climatology.

Replaces a Köppen-Geiger raster lookup with a server-side ERA5-Land
monthly aggregate query. Self-contained (no asset path dependency,
no local raster file).

Reference for the classification rules:
  Beck, H.E. et al. (2018), Sci. Data 5, 180214.
  Peel, M.C. et al. (2007), HESS 11, 1633-1644.

Inputs per point:
  monthly_t_C  : list of 12 mean monthly 2m temperatures, °C
  monthly_p_mm : list of 12 monthly total precipitation values, mm
  lat          : latitude in degrees (sign matters: hemisphere → summer)

Returns one of the standard 30-class strings or None on indeterminate.

Disk cache: keyed on (lat, lon) rounded to 0.1° (~11 km — finer than the
ERA5-Land grid). First lookup queries ERA5; subsequent lookups for the
same cell are instant. Cache file: data/cache/pvaf_koppen_cache.json
"""
from __future__ import annotations

import json
import threading
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _ee():
    import ee
    try:
        ee.Initialize(project="kandypinn")
    except Exception:
        ee.Authenticate()
        ee.Initialize(project="kandypinn")
    return ee


ERA5_SCALE_M = 11132  # ERA5-Land 0.1° at the equator


def _classify(monthly_t_C: list[float], monthly_p_mm: list[float], lat: float) -> str | None:
    """Apply Köppen-Geiger rules. Returns a 2-3 letter class or None."""
    if len(monthly_t_C) != 12 or len(monthly_p_mm) != 12:
        return None
    if any(t is None for t in monthly_t_C) or any(p is None for p in monthly_p_mm):
        return None

    t = monthly_t_C
    p = monthly_p_mm
    Tann = sum(t) / 12.0
    Pann = sum(p)
    Tmin = min(t)
    Tmax = max(t)
    n_above_10 = sum(1 for x in t if x >= 10.0)

    # Northern vs southern hemisphere — defines "summer"/"winter" months
    if lat >= 0:
        summer_months = [3, 4, 5, 6, 7, 8]   # Apr-Sep (idx 3-8 → months 4-9 incl)
        winter_months = [9, 10, 11, 0, 1, 2]  # Oct-Mar
    else:
        summer_months = [9, 10, 11, 0, 1, 2]
        winter_months = [3, 4, 5, 6, 7, 8]

    Psummer = sum(p[m] for m in summer_months)
    Pwinter = sum(p[m] for m in winter_months)
    Tsummer = max(t[m] for m in summer_months)
    Pdry = min(p)

    # Step 1: aridity threshold (B group). Pthreshold depends on seasonal
    # precip distribution.
    if Pwinter >= 0.7 * Pann:
        Pthresh = 2 * Tann
    elif Psummer >= 0.7 * Pann:
        Pthresh = 2 * Tann + 28
    else:
        Pthresh = 2 * Tann + 14

    if Pann < 10 * Pthresh:
        # Arid: BW (desert) or BS (steppe)
        if Pann < 5 * Pthresh:
            kind = "BW"
        else:
            kind = "BS"
        return kind + ("h" if Tann >= 18 else "k")

    # Step 2: A group — tropical (all months >= 18°C)
    if Tmin >= 18:
        if Pdry >= 60:
            return "Af"
        if Pdry >= 100 - Pann / 25:
            return "Am"
        return "Aw"  # AS / AW collapses into Aw at this scale

    # Helper — Peel et al. (2007) seasonality classification for C/D groups.
    def _seasonality(p, summer_months, winter_months) -> str:
        p_summer_wet_max = max(p[m] for m in summer_months)
        p_winter_wet_max = max(p[m] for m in winter_months)
        p_summer_dry_min = min(p[m] for m in summer_months)
        p_winter_dry_min = min(p[m] for m in winter_months)
        # "w" = dry winter: driest winter month < 1/10 of wettest summer month
        if p_winter_dry_min < p_summer_wet_max / 10:
            return "w"
        # "s" = dry summer (Mediterranean): driest summer < 40 mm AND
        #       < 1/3 of wettest winter
        if p_summer_dry_min < 40 and p_summer_dry_min < p_winter_wet_max / 3:
            return "s"
        return "f"

    # Step 3: C group — temperate
    if Tmin > -3 and Tmin < 18 and Tmax > 10:
        seasonality = _seasonality(p, summer_months, winter_months)
        if Tmax >= 22:
            tsuf = "a"
        elif n_above_10 >= 4:
            tsuf = "b"
        else:
            tsuf = "c"
        return "C" + seasonality + tsuf

    # Step 4: D group — cold (Tmin <= -3, Tmax > 10)
    if Tmin <= -3 and Tmax > 10:
        seasonality = _seasonality(p, summer_months, winter_months)
        if Tmax >= 22:
            tsuf = "a"
        elif n_above_10 >= 4:
            tsuf = "b"
        elif Tmin < -38:
            tsuf = "d"
        else:
            tsuf = "c"
        return "D" + seasonality + tsuf

    # Step 5: E group — polar
    if Tmax <= 10:
        return "ET" if Tmax > 0 else "EF"

    return None


_CACHE_PATH = Path("d:/ProjectCD/kandy_pm25/data/cache/pvaf_koppen_cache.json")
_CACHE_LOCK = threading.Lock()
_CACHE_RESOLUTION_DEG = 0.1  # ~11 km bin — finer than ERA5-Land native grid


def _cache_key(lat: float, lon: float) -> str:
    rlat = round(lat / _CACHE_RESOLUTION_DEG) * _CACHE_RESOLUTION_DEG
    rlon = round(lon / _CACHE_RESOLUTION_DEG) * _CACHE_RESOLUTION_DEG
    return f"{rlat:+.1f},{rlon:+.1f}"


def _load_cache() -> dict:
    if not _CACHE_PATH.exists():
        return {}
    try:
        return json.loads(_CACHE_PATH.read_text())
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, indent=0, separators=(",", ":")))
    tmp.replace(_CACHE_PATH)


def koppen_from_era5(lat: float, lon: float, use_cache: bool = True) -> tuple[str | None, dict]:
    """Compute Köppen class for one point from ERA5-Land monthly climatology.

    Returns (koppen_class, debug_dict). Disk-cached at 0.1° resolution.
    """
    if use_cache:
        with _CACHE_LOCK:
            cache = _load_cache()
            key = _cache_key(lat, lon)
            if key in cache:
                hit = cache[key]
                return hit.get("kg"), {"cached": True, **hit.get("dbg", {})}

    ee = _ee()
    pt = ee.Geometry.Point([lon, lat])

    # Monthly climatology 2015-2024 from ERA5-Land MONTHLY_AGGR (cheap).
    col = (
        ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
        .filterDate("2015-01-01", "2025-01-01")
        .select(["temperature_2m", "total_precipitation_sum"])
    )

    def month_clim(m):
        m = ee.Number(m)
        sub = col.filter(ee.Filter.calendarRange(m, m, "month"))
        return sub.mean().set("month", m)

    clim = ee.ImageCollection(ee.List.sequence(1, 12).map(month_clim))
    bands = clim.toBands()
    d = bands.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=pt,
        scale=ERA5_SCALE_M,
        tileScale=4,
        maxPixels=1e9,
        bestEffort=True,
    ).getInfo()
    if not d:
        return None, {"err": "empty reduceRegion"}

    # Band names: "0_temperature_2m", "0_total_precipitation_sum", "1_...", ...
    monthly_t = []
    monthly_p = []
    for m in range(12):
        t = d.get(f"{m}_temperature_2m")
        p = d.get(f"{m}_total_precipitation_sum")
        monthly_t.append(None if t is None else (t - 273.15))  # K -> C
        monthly_p.append(None if p is None else (p * 1000.0))  # m -> mm

    cls = _classify(monthly_t, monthly_p, lat)
    dbg = {
        "monthly_t_C": [round(x, 1) if x is not None else None for x in monthly_t],
        "monthly_p_mm": [round(x, 1) if x is not None else None for x in monthly_p],
    }

    if use_cache:
        with _CACHE_LOCK:
            cache = _load_cache()
            cache[_cache_key(lat, lon)] = {"kg": cls, "dbg": dbg}
            _save_cache(cache)
    return cls, dbg


if __name__ == "__main__":
    # Quick sanity test on Kandy + 3 sources
    for name, lat, lon in [
        ("Kandy", 7.2906, 80.6337),
        ("Medellin", 6.2476, -75.5658),
        ("ChiangMai", 18.7883, 98.9853),
        ("Kathmandu", 27.7172, 85.3240),
    ]:
        kg, dbg = koppen_from_era5(lat, lon)
        print(f"{name:12s} -> {kg}")
