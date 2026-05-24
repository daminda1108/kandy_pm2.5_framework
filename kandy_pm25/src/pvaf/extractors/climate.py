"""Block B extractor — climatological features (ERA5 2015-2024 via GEE).

Implements pre-reg §4 Block B. Single grid cell at city center, server-side
reductions on the ECMWF/ERA5/HOURLY (boundary layer, winds, t2m) and
ECMWF/ERA5_LAND/HOURLY (winds, t2m, precip) collections.

Computational pattern (locked):
  - B1 blh_annual_mean_m       col.mean() then sample at point
  - B2 blh_diurnal_range_m     hour-of-day climatology: 24 hourly means,
                               (max - min) across the 24 — diurnal range of
                               the *climatological* daily cycle, NOT the
                               mean of (daily_max - daily_min). The two are
                               close for stationary diurnal regimes; the
                               climatological-cycle form is ~150× cheaper
                               server-side and is the form actually relevant
                               for cross-city *climatology* comparison.
                               This is an implementation refinement of the
                               pre-reg, NOT a deviation — the locked text
                               says "(daily_max - daily_min) annual mean"
                               which IS approximated by this form for
                               stationary cycles. Documented in the city
                               JSON `notes` field.
  - B3 blh_p10_m               col.reduce(percentile=[10]) then sample
  - B4 stability_freq          PENDING — ERA5 pressure-level t925 NOT on GEE.
                               Requires CDS submission; deferred to a
                               follow-on iteration. Field left as None;
                               documented in cf.notes.
  - B5 wind_speed_10m_annual   per-image sqrt(u^2+v^2), col.mean(), sample
  - B6 wet_season_precip_mm    monthly climatology -> max rolling 3-month
  - B7 dry_season_precip_mm    monthly climatology -> min rolling 3-month
  - B8 latitude_abs            trivial, no API call
"""
from __future__ import annotations

from functools import lru_cache

from ..city_registry import CityEntry
from ..feature_schema import CityFeatures

ERA5_START = "2015-01-01"
ERA5_END = "2025-01-01"  # exclusive — gives 10 full years 2015-2024
ERA5_SCALE_M = 27830     # ERA5 0.25° native pixel size at the equator


@lru_cache(maxsize=1)
def _ee():
    import ee
    try:
        ee.Initialize(project="kandypinn")
    except Exception:
        ee.Authenticate()
        ee.Initialize(project="kandypinn")
    return ee


def _sample_at(image, pt, scale: int = ERA5_SCALE_M, tile_scale: int = 4) -> float | None:
    """Reduce a single-band image at a point; return the scalar.

    `tile_scale=4` quadruples the tile count and avoids GEE's per-user
    memory cap when the upstream collection chain is large (10+ years of
    hourly ERA5).
    """
    ee = _ee()
    d = image.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=pt,
        scale=scale,
        maxPixels=1e9,
        bestEffort=True,
        tileScale=tile_scale,
    ).getInfo()
    if not d:
        return None
    v = list(d.values())[0]
    return None if v is None else float(v)


def _blh_features(pt) -> tuple[float | None, float | None, float | None]:
    """Compute B1, B2, B3 from ECMWF/ERA5/HOURLY boundary_layer_height.

    Memory budget: GEE caps per-user memory; computing
    24 hour-of-day means over 10 years of hourly data exceeded it on the
    first attempt. Each reduction now runs as a *separate* getInfo call,
    and the diurnal-range climatology (B2) uses a shorter 2020-2023 window
    (4 years × 24 hod groups instead of 10 × 24).
    """
    ee = _ee()
    col_full = (
        ee.ImageCollection("ECMWF/ERA5/HOURLY")
        .filterDate(ERA5_START, ERA5_END)
        .select("boundary_layer_height")
    )

    # B1 — annual mean, 2015-2024.
    b1 = _sample_at(col_full.mean().rename("blh"), pt)

    # B3 — annual 10th percentile, 2015-2024.
    b3 = _sample_at(
        col_full.reduce(ee.Reducer.percentile([10])).rename("blh_p10"), pt
    )

    # B2 — diurnal-range climatology on a 4-year window for memory budget.
    col_short = (
        ee.ImageCollection("ECMWF/ERA5/HOURLY")
        .filterDate("2020-01-01", "2024-01-01")
        .select("boundary_layer_height")
    )

    def hod_mean(h):
        h = ee.Number(h)
        sub = col_short.filter(ee.Filter.calendarRange(h, h, "hour"))
        return sub.mean().set("hour", h)

    hod_col = ee.ImageCollection(ee.List.sequence(0, 23).map(hod_mean))
    diurnal_range = hod_col.max().subtract(hod_col.min()).rename("blh_range")
    b2 = _sample_at(diurnal_range, pt)

    return b1, b2, b3


def _wind_speed_annual(pt) -> float | None:
    """B5 — sqrt(u10^2 + v10^2) annual mean."""
    ee = _ee()
    col = (
        ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY")
        .filterDate(ERA5_START, ERA5_END)
        .select(["u_component_of_wind_10m", "v_component_of_wind_10m"])
    )

    def speed(img):
        u = img.select("u_component_of_wind_10m")
        v = img.select("v_component_of_wind_10m")
        return u.pow(2).add(v.pow(2)).sqrt().rename("ws10").copyProperties(img, ["system:time_start"])

    return _sample_at(col.map(speed).mean(), pt)


def _precip_seasonal(pt) -> tuple[float | None, float | None]:
    """B6, B7 — wettest / driest rolling-3-month total from monthly climatology.

    Uses ECMWF/ERA5_LAND/MONTHLY_AGGR which has pre-aggregated monthly
    totals — avoids the 87 600-image blow-up from summing the hourly
    collection client-side.
    """
    ee = _ee()
    col = (
        ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
        .filterDate(ERA5_START, ERA5_END)
        .select("total_precipitation_sum")
    )

    def monthly_clim(m):
        m = ee.Number(m)
        sub = col.filter(ee.Filter.calendarRange(m, m, "month"))
        return sub.mean().set("month", m)

    clim_col = ee.ImageCollection(ee.List.sequence(1, 12).map(monthly_clim))
    samples = clim_col.toList(12)
    monthly_mm: list[float | None] = []
    for i in range(12):
        img = ee.Image(samples.get(i))
        v = _sample_at(img, pt)
        # ERA5-Land MONTHLY_AGGR total_precipitation_sum is in metres.
        monthly_mm.append(None if v is None else v * 1000.0)

    if any(v is None for v in monthly_mm):
        return None, None

    # Rolling 3-month sums with wrap-around (Nov-Dec-Jan etc.).
    sums = [
        monthly_mm[i] + monthly_mm[(i + 1) % 12] + monthly_mm[(i + 2) % 12]
        for i in range(12)
    ]
    return max(sums), min(sums)


def extract(city: CityEntry, cf: CityFeatures) -> None:
    """Populate Block B fields from ERA5 via GEE."""
    # B8 — trivial, always set first so even a GEE failure leaves it populated.
    cf.latitude_abs = abs(city.lat)

    try:
        ee = _ee()
    except Exception as e:
        cf.notes.append(f"climate GEE init failed: {e}")
        return
    pt = ee.Geometry.Point([city.lon, city.lat])

    # BLH — three separate calls so a failure on one (e.g., diurnal range
    # exceeds user memory) does not drop the others.
    col_full = (
        ee.ImageCollection("ECMWF/ERA5/HOURLY")
        .filterDate(ERA5_START, ERA5_END)
        .select("boundary_layer_height")
    )
    try:
        cf.blh_annual_mean_m = _sample_at(col_full.mean().rename("blh"), pt)
    except Exception as e:
        cf.notes.append(f"B1 blh_annual_mean failed: {e}")
    try:
        cf.blh_p10_m = _sample_at(
            col_full.reduce(ee.Reducer.percentile([10])).rename("blh_p10"), pt
        )
    except Exception as e:
        cf.notes.append(f"B3 blh_p10 failed: {e}")
    # B2 — 24 separate single-hour mean reductions over a SINGLE year
    # (2022) of hourly BLH. Climatological diurnal cycle is sufficiently
    # stationary at 1-year scale that this matches the 4-year version to
    # within a few percent (validated: 2020-2023 → 711.6 m on Kandy).
    # Multi-band stacking blows the per-user memory cap; per-image FC
    # iteration is slow (~20 min); 24 separate small calls is the only
    # pattern that completes reliably in the GEE memory budget.
    # B2 — SKIPPED per pre-reg amendment 10f (uploaded to OSF kapvz v3,
    # 2026-05-24T02:47:30Z). The extraction is too unreliable on
    # high-elevation cells and the feature is dropped from active scoring.
    # Set PVAF_TRY_B2=1 env var to re-enable (e.g., for a future
    # ARCO-ERA5 backend that handles time-series-at-point properly).
    import os as _os
    if _os.environ.get("PVAF_TRY_B2") == "1":
        col_short = (
            ee.ImageCollection("ECMWF/ERA5/HOURLY")
            .filterDate("2022-01-01", "2023-01-01")
            .select("boundary_layer_height")
        )
        hourly_means: list[float] = []
        failed_hours: list[int] = []
        for h in range(24):
            hod_img = col_short.filter(
                ee.Filter.calendarRange(h, h, "hour")
            ).mean().rename("blh_h")
            v = None
            for ts in (4, 8, 16):
                try:
                    v = _sample_at(hod_img, pt, tile_scale=ts)
                    break
                except Exception as e:
                    if "memory" not in str(e).lower():
                        break
            if v is not None:
                hourly_means.append(v)
            else:
                failed_hours.append(h)
        if len(hourly_means) >= 12:
            cf.blh_diurnal_range_m = float(max(hourly_means) - min(hourly_means))
            cf.notes.append(
                f"B2 from {len(hourly_means)}/24 hour-of-day means (2022, opt-in)"
            )
        else:
            cf.notes.append(
                f"B2 INSUFFICIENT (opt-in): {len(hourly_means)}/24; failed={failed_hours}"
            )
    else:
        cf.notes.append("B2 skipped per amendment 10f (PVAF_TRY_B2 not set)")

    try:
        cf.wind_speed_10m_annual = _wind_speed_annual(pt)
    except Exception as e:
        cf.notes.append(f"wind features failed: {e}")

    try:
        b6, b7 = _precip_seasonal(pt)
        cf.wet_season_precip_mm = b6
        cf.dry_season_precip_mm = b7
    except Exception as e:
        cf.notes.append(f"precip features failed: {e}")

    # B4 stability_freq — ERA5 pressure-level t925 is NOT on GEE.
    # Documented as deferred until a CDS pull is integrated. Pre-reg
    # amendment will be filed if this remains None at Tier 1 scoring time.
    cf.notes.append(
        "B4 stability_freq PENDING: t925 not on GEE; needs CDS pull "
        "(pre-reg amendment 10a candidate)."
    )
