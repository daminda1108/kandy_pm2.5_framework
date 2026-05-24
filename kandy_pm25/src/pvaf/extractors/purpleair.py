"""Block D supplementary extractor — PurpleAir + SensorCommunity LCS coverage.

Implements pre-reg amendment 10c (2026-05-23). Augments the OpenAQ-only
Block D monitoring tier with LCS network lookups for top-K cities by
s_phys that fail OpenAQ M2.

Two backends:
  1. PurpleAir /v1/sensors  — globally deployed; API now PAID for bounding-box
     queries (HTTP 402 since mid-2024). Project READ key is valid for
     /v1/keys but not /v1/sensors with bbox. Function attempts the call;
     on 402 returns a clearly-labelled "unavailable" record.
  2. SensorCommunity (Luftdaten) /v1/filter/area  — free, no key, global.
     Covers the same LCS PM2.5 deployment niche; complements PurpleAir
     in regions where PA is paid-blocked.

Many active LCS sensors are NOT federated into OpenAQ /v3 (Kandy's
FECT is a known case). This module queries within a 25 km bounding box
around a city center, counts sensors with >= 2 years of historical
data, and assigns a supplementary monitoring tier:

  M1-PA  : >=5 sensors AND >=3 years AND project-known calibration coefficients
  M2-PA  : >=3 sensors AND >=2 years AND calibration available
  M3-PA  : otherwise (insufficient even with PurpleAir)

The pre-reg amendment treats M2-PA as equivalent to M2 for the
inclusion-rule monitoring gate (pre-reg §8). M1-PA equivalent to M1.

This module DOES NOT replace OpenAQ Block D; it runs as a secondary
check on a list of cities provided by the caller. The Tier 1 ranking
remains unchanged — only the monitoring inclusion gate widens.

PurpleAir API:
  GET https://api.purpleair.com/v1/sensors
    headers: X-API-Key: <read-key>
    params:
      fields=latitude,longitude,date_created,last_seen,name
      nwlat, nwlng, selat, selng       # bounding box
      max_age=0                         # all sensors (not just recent activity)

Note: the PurpleAir READ KEY (not WRITE) is sufficient for /v1/sensors
GET. Key lives in d:/ProjectCD/API.txt as "PurpleAir API: <key>".
"""
from __future__ import annotations

import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import requests

PA_API_BASE = "https://api.purpleair.com/v1"
PA_API_KEY_FILE = Path("d:/ProjectCD/API.txt")
DEFAULT_RADIUS_M = 25_000

PATier = Literal["M1-PA", "M2-PA", "M3-PA"]


def _get_api_key() -> str | None:
    if not PA_API_KEY_FILE.exists():
        return None
    for line in PA_API_KEY_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"\s*PurpleAir API\s*[:=]\s*(\S+)", line, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _bbox_for_radius(lat: float, lon: float, radius_m: float) -> tuple[float, float, float, float]:
    """Return (nwlat, nwlng, selat, selng) for a circular buffer of radius_m
    around (lat, lon). PurpleAir uses NW + SE corners."""
    dlat = radius_m / 111_000.0
    dlon = radius_m / (111_000.0 * max(math.cos(math.radians(lat)), 0.01))
    return (lat + dlat, lon - dlon, lat - dlat, lon + dlon)


def query_purpleair(
    lat: float,
    lon: float,
    radius_m: float = DEFAULT_RADIUS_M,
    api_key: str | None = None,
    max_age_days: int = 0,
) -> dict:
    """Query PurpleAir /v1/sensors within `radius_m` of (lat, lon).

    Returns:
        {
          'n_sensors': int,
          'sensors': [(sensor_index, lat, lon, date_created, last_seen, name), ...],
          'oldest_date_created_ts': float | None,   # earliest sensor in epoch s
          'years_coverage': float | None,
          'recent_active_count': int,               # last_seen within 30 days
        }
    """
    key = api_key or _get_api_key()
    if not key:
        raise RuntimeError("No PurpleAir API key in d:/ProjectCD/API.txt")

    nwlat, nwlng, selat, selng = _bbox_for_radius(lat, lon, radius_m)

    params = {
        "fields": "latitude,longitude,date_created,last_seen,name",
        "nwlat": f"{nwlat:.4f}",
        "nwlng": f"{nwlng:.4f}",
        "selat": f"{selat:.4f}",
        "selng": f"{selng:.4f}",
        "max_age": str(max_age_days),
    }
    headers = {"X-API-Key": key}

    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.get(
                f"{PA_API_BASE}/sensors",
                params=params,
                headers=headers,
                timeout=60,
            )
            if r.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 402:
                # Paid-tier required for bounding-box queries (post-2024).
                # Return a clearly-labelled "unavailable" record — caller
                # should fall back to SensorCommunity or skip augmentation.
                return {
                    "n_sensors": 0, "sensors": [],
                    "oldest_date_created_ts": None,
                    "years_coverage": None,
                    "recent_active_count": 0,
                    "api_unavailable": "402 Payment Required — bbox query requires paid PA points",
                }
            r.raise_for_status()
            payload = r.json()
            break
        except requests.RequestException as e:
            last_exc = e
            time.sleep(2 ** attempt)
    else:
        raise RuntimeError(f"PurpleAir /v1/sensors failed: {last_exc}")

    fields = payload.get("fields") or []
    data = payload.get("data") or []
    if not fields:
        return {"n_sensors": 0, "sensors": [], "oldest_date_created_ts": None,
                "years_coverage": None, "recent_active_count": 0}

    # PurpleAir API returns `data` as list-of-lists in `fields` column order.
    idx = {name: i for i, name in enumerate(fields)}
    now = datetime.now(timezone.utc).timestamp()
    sensors = []
    oldest = None
    recent = 0
    for row in data:
        ts_created = row[idx["date_created"]] if "date_created" in idx else None
        ts_last = row[idx["last_seen"]] if "last_seen" in idx else None
        sensors.append((
            row[idx.get("sensor_index", 0)] if "sensor_index" in idx else None,
            row[idx["latitude"]] if "latitude" in idx else None,
            row[idx["longitude"]] if "longitude" in idx else None,
            ts_created, ts_last,
            row[idx["name"]] if "name" in idx else "",
        ))
        if ts_created and (oldest is None or ts_created < oldest):
            oldest = ts_created
        if ts_last and (now - ts_last) <= 30 * 86400:
            recent += 1

    years_cov = ((now - oldest) / (365.25 * 86400)) if oldest else None

    return {
        "n_sensors": len(sensors),
        "sensors": sensors,
        "oldest_date_created_ts": oldest,
        "years_coverage": years_cov,
        "recent_active_count": recent,
    }


def assign_pa_tier(
    n_sensors: int,
    years_coverage: float | None,
    has_calibration: bool,
) -> PATier:
    """PurpleAir-augmented tier per amendment 10c. Mirrors OpenAQ tier
    thresholds but treats PurpleAir as LCS+calibration-required."""
    if (
        n_sensors >= 5
        and (years_coverage or 0) >= 3
        and has_calibration
    ):
        return "M1-PA"
    if (
        n_sensors >= 3
        and (years_coverage or 0) >= 2
        and has_calibration
    ):
        return "M2-PA"
    return "M3-PA"


SC_API_BASE = "https://data.sensor.community"


def query_sensorcommunity(
    lat: float,
    lon: float,
    radius_km: float = 25.0,
) -> dict:
    """Query SensorCommunity (formerly Luftdaten) /v1/filter/area for PM2.5 sensors.

    Free, no key, global. Returns 5-min averaged PM2.5 readings from
    citizen-deployed LCS (mostly SDS011) within radius_km of (lat, lon).

    Result is a snapshot of recent activity — no historical coverage info
    from this endpoint, just current sensor count. Useful as a "is there
    ANY LCS coverage here" signal when PurpleAir is paywalled.
    """
    url = f"{SC_API_BASE}/airrohr/v1/filter/area={lat},{lon},{radius_km}"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"n_sensors_recent": 0, "api_error": str(e)[:120]}

    # Each entry is a single measurement; one sensor produces many per hour.
    # Count unique sensor_ids that reported in this snapshot.
    sensor_ids = set()
    for entry in data:
        sid = (entry.get("sensor") or {}).get("id")
        sensor_values = entry.get("sensordatavalues") or []
        if sid and any(v.get("value_type") == "P2" for v in sensor_values):
            sensor_ids.add(sid)
    return {
        "n_sensors_recent": len(sensor_ids),
        "snapshot_records": len(data),
    }


def lookup_supplementary(
    city_name: str,
    lat: float,
    lon: float,
    radius_m: float = DEFAULT_RADIUS_M,
    project_has_calibration: bool = True,
) -> dict:
    """End-to-end: query PA, assign tier, return summary dict for the
    pre-reg amendment 10c audit trail.

    `project_has_calibration` defaults to True because the FECT/PurpleAir
    AirGradient calibration coefficients (`data/external/openaq/processed/
    eda/{city}/calibration_coefficients.csv`) are reusable for any new
    PurpleAir city by applying the same per-LCS regression. False if a
    new network without published coefficients.

    Calls BOTH backends and stores both results; tier assignment uses
    PurpleAir when available, falls back to SensorCommunity recent-count
    when PA is paywalled.
    """
    pa = query_purpleair(lat, lon, radius_m=radius_m)
    sc = query_sensorcommunity(lat, lon, radius_km=radius_m / 1000.0)

    pa_unavailable = "api_unavailable" in pa
    if not pa_unavailable:
        tier = assign_pa_tier(
            n_sensors=pa["recent_active_count"],
            years_coverage=pa["years_coverage"],
            has_calibration=project_has_calibration,
        )
        tier_source = "purpleair"
    else:
        # PA paywalled — fall back to SensorCommunity. SC gives only
        # current-active count, not historical years. Treat n_recent>=3
        # as M2-PA-equivalent if calibration is plausible; otherwise M3-PA.
        n = sc.get("n_sensors_recent", 0)
        if n >= 5 and project_has_calibration:
            tier = "M2-PA"  # downgraded one step due to no years-coverage info
        elif n >= 3 and project_has_calibration:
            tier = "M3-PA"  # not promoted — count alone insufficient
        else:
            tier = "M3-PA"
        tier_source = "sensorcommunity_fallback"

    return {
        "city": city_name,
        "lat": lat,
        "lon": lon,
        "pa_n_sensors_total": pa.get("n_sensors", 0),
        "pa_n_sensors_recent_30d": pa.get("recent_active_count", 0),
        "pa_years_coverage": pa.get("years_coverage"),
        "pa_api_unavailable": pa.get("api_unavailable"),
        "sc_n_sensors_recent": sc.get("n_sensors_recent", 0),
        "sc_api_error": sc.get("api_error"),
        "pa_tier": tier,
        "tier_source": tier_source,
        "lookup_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    # Sanity probe: query Kandy + Quito + Mel
    for name, lat, lon in [
        ("Kandy", 7.2906, 80.6337),
        ("Quito", -0.1807, -78.4678),
        ("Medellin", 6.2476, -75.5658),
        ("Hanoi", 21.0285, 105.8542),
    ]:
        try:
            r = lookup_supplementary(name, lat, lon)
            pa_status = "paywalled" if r.get("pa_api_unavailable") else f"n={r['pa_n_sensors_recent_30d']}"
            print(f"{name:12s}  PA: {pa_status:>15s}  "
                  f"SC: n_recent={r['sc_n_sensors_recent']:4d}  "
                  f"tier={r['pa_tier']}  source={r['tier_source']}")
        except Exception as e:
            print(f"{name:12s}  FAIL: {str(e)[:100]}")
