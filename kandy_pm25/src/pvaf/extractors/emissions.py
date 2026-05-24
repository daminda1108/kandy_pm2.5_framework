"""Block C extractor — emission-regime features via GEE + local EDGAR.

Implements pre-reg §4 Block C. Buffers: 25 km for C1-C4, 50 km for C5.

Status:
  C1 ntl_log_mean            VIIRS NOAA/VIIRS/DNB/MONTHLY_V1, GEE       ✓
  C2 pop_density_log         WorldPop/GP/100m/pop, GEE                  ✓
  C3 edgar_pm25_kg_m2_yr     EDGAR v8.1 NetCDF — local path STUB        ⏳
  C4 edgar_residential_frac  EDGAR v8.1 NetCDF — local path STUB        ⏳
  C5 fire_count_50km_yr      FIRMS, GEE                                 ✓

C3/C4 require the EDGAR v8.1 PM2.5 sectoral NetCDF set
(~5 GB total) under data/external/edgar_v8/. Download is a one-time job
out of scope for the extractor itself; the function detects the missing
file and leaves the field None with a clear note.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

from ..city_registry import CityEntry
from ..feature_schema import CityFeatures

EDGAR_DIR = Path("d:/ProjectCD/kandy_pm25/data/external/edgar_v8")
EMISSION_BUFFER_M = 25_000   # locked: 25 km for C1-C4
FIRE_BUFFER_M = 50_000       # locked: 50 km for C5
VIIRS_START = "2020-01-01"
VIIRS_END = "2024-01-01"     # exclusive — 4 years
FIRMS_START = "2020-01-01"
FIRMS_END = "2024-01-01"


@lru_cache(maxsize=1)
def _ee():
    import ee
    try:
        ee.Initialize(project="kandypinn")
    except Exception:
        ee.Authenticate()
        ee.Initialize(project="kandypinn")
    return ee


def _ntl_log_mean(geom) -> float | None:
    """C1 — log(mean(VIIRS NTL 2020-2023) + 1) over 25 km buffer."""
    ee = _ee()
    # VCMSLCFG = stray-light-corrected, cloud-free monthly composite.
    col = (
        ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
        .filterDate(VIIRS_START, VIIRS_END)
        .select("avg_rad")
    )
    mean_img = col.mean()
    stats = mean_img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=500,
        maxPixels=1e9,
        bestEffort=True,
    ).getInfo()
    if not stats:
        return None
    v = list(stats.values())[0]
    if v is None or v < 0:
        # NTL can be slightly negative due to noise — clip to 0 before log.
        v = max(0.0, v or 0.0)
    return math.log(float(v) + 1.0)


def _pop_density_log(geom) -> float | None:
    """C2 — log(mean WorldPop 2020 1 km) over 25 km buffer."""
    ee = _ee()
    # WorldPop GP global-mosaic — 2020 unconstrained.
    col = (
        ee.ImageCollection("WorldPop/GP/100m/pop")
        .filter(ee.Filter.eq("year", 2020))
    )
    pop = col.mosaic()
    stats = pop.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=100,
        maxPixels=1e9,
        bestEffort=True,
    ).getInfo()
    if not stats:
        return None
    v = list(stats.values())[0]
    if v is None:
        return None
    # log(mean+1) to keep finite at sparsely-populated cells.
    return math.log(float(v) + 1.0)


def _fire_count_annual(geom) -> float | None:
    """C5 — FIRMS confirmed-fire detections / year over 50 km buffer."""
    ee = _ee()
    col = (
        ee.ImageCollection("FIRMS")
        .filterDate(FIRMS_START, FIRMS_END)
        .filterBounds(geom)
        .select("T21")
    )
    # FIRMS images are per-day binary detections at 1 km. Count non-null
    # pixels across the collection within the buffer. Each image's
    # reduceRegion(count) returns pixel count; sum over the collection.
    def per_img(img):
        c = img.reduceRegion(
            reducer=ee.Reducer.count(),
            geometry=geom,
            scale=1000,
            maxPixels=1e9,
            bestEffort=True,
        )
        return ee.Feature(None, {"n": c.get("T21")})

    fc = col.map(per_img)
    total = fc.aggregate_sum("n").getInfo()
    if total is None:
        return None
    n_years = 4.0  # 2020-2023 inclusive
    return float(total) / n_years


def _edgar_emissions(city: CityEntry, cf: CityFeatures) -> tuple[float | None, float | None]:
    """C3/C4 — EDGAR v8.1 total + residential-fraction within 25 km.

    Returns (C3, C4) or (None, None) with a note if the NetCDFs are absent.
    """
    if not EDGAR_DIR.exists():
        cf.notes.append(
            f"EDGAR: {EDGAR_DIR} missing -> C3/C4 None (download pending)"
        )
        return None, None

    total_files = list(EDGAR_DIR.glob("*PM25*TOTALS*.nc")) + list(EDGAR_DIR.glob("*PM25*total*.nc"))
    if not total_files:
        cf.notes.append(
            "EDGAR: no *PM25*TOTALS*.nc found in edgar_v8/ -> C3/C4 None"
        )
        return None, None

    try:
        import xarray as xr
    except ImportError:
        cf.notes.append("EDGAR: xarray not installed -> C3/C4 None")
        return None, None

    # EDGAR is 0.1° resolution. 25 km ≈ 0.225° latitude — sum the cells
    # intersecting a 25 km circular buffer (approximate as a bbox here).
    dlat = 25_000 / 111_000.0
    dlon = 25_000 / (111_000.0 * max(math.cos(math.radians(city.lat)), 0.01))
    lat_min, lat_max = city.lat - dlat, city.lat + dlat
    lon_min, lon_max = city.lon - dlon, city.lon + dlon

    try:
        ds = xr.open_dataset(total_files[0])
        lat_name = "lat" if "lat" in ds.coords else "latitude"
        lon_name = "lon" if "lon" in ds.coords else "longitude"
        # Pick the PM2.5 emission variable — EDGAR uses 'emi_pm2p5' or similar.
        var = next(
            (v for v in ds.data_vars if "pm" in v.lower() and "2" in v.lower()),
            list(ds.data_vars)[0],
        )
        clip = ds[var].sel({
            lat_name: slice(lat_min, lat_max),
            lon_name: slice(lon_min, lon_max),
        })
        # Sum over the bbox; convert kg/m^2/s -> kg/m^2/yr by ×86400×365.25
        # IF the unit string says s^-1. Otherwise pass through.
        unit_attr = clip.attrs.get("units", "").lower()
        scale = 86400.0 * 365.25 if "s-1" in unit_attr or "s^-1" in unit_attr else 1.0
        c3 = float(clip.sum().item()) * scale
    except Exception as e:
        cf.notes.append(f"EDGAR total read failed: {e}")
        return None, None

    # Residential sector
    res_files = list(EDGAR_DIR.glob("*PM25*RES*.nc")) + list(EDGAR_DIR.glob("*PM25*residential*.nc"))
    if not res_files:
        cf.notes.append("EDGAR residential: file missing -> C4 None")
        return c3, None

    try:
        ds_r = xr.open_dataset(res_files[0])
        var_r = next(
            (v for v in ds_r.data_vars if "pm" in v.lower() and "2" in v.lower()),
            list(ds_r.data_vars)[0],
        )
        clip_r = ds_r[var_r].sel({
            lat_name: slice(lat_min, lat_max),
            lon_name: slice(lon_min, lon_max),
        })
        res_total = float(clip_r.sum().item()) * scale
        c4 = res_total / c3 if c3 > 0 else None
    except Exception as e:
        cf.notes.append(f"EDGAR residential read failed: {e}")
        return c3, None

    return c3, c4


def extract(city: CityEntry, cf: CityFeatures) -> None:
    """Populate Block C fields from VIIRS + WorldPop + EDGAR + FIRMS."""
    try:
        ee = _ee()
    except Exception as e:
        cf.notes.append(f"emissions GEE init failed: {e}")
        return

    pt = ee.Geometry.Point([city.lon, city.lat])
    buf25 = pt.buffer(EMISSION_BUFFER_M)
    buf50 = pt.buffer(FIRE_BUFFER_M)

    try:
        cf.ntl_log_mean = _ntl_log_mean(buf25)
    except Exception as e:
        cf.notes.append(f"NTL failed: {e}")

    try:
        cf.pop_density_log = _pop_density_log(buf25)
    except Exception as e:
        cf.notes.append(f"WorldPop failed: {e}")

    try:
        cf.fire_count_50km_yr = _fire_count_annual(buf50)
    except Exception as e:
        cf.notes.append(f"FIRMS failed: {e}")

    try:
        c3, c4 = _edgar_emissions(city, cf)
        cf.edgar_pm25_kg_m2_yr = c3
        cf.edgar_residential_frac = c4
    except Exception as e:
        cf.notes.append(f"EDGAR failed: {e}")
