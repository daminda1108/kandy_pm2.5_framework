"""Block D extractor — monitoring practicality from OpenAQ /v3.

Implements pre-reg §4 Block D + §6 monitoring-tier rules.

OpenAQ /v3 API:
  - GET /locations?coordinates=lat,lon&radius=25000   (radius cap 25 km)
  - GET /locations/{id}/sensors                       (sensor types)
  - GET /locations/{id}/measurements                  (NOT used here — for
                                                       date-range probing we
                                                       use the locations
                                                       metadata firstDate/
                                                       lastDate fields)

Authentication: optional API key in header `X-API-Key`. Key lives in
d:/ProjectCD/API.txt under "OpenAQ API: ...". With key we get higher rate
limits; without, the public endpoints still work.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import requests

from ..city_registry import CityEntry
from ..feature_schema import CityFeatures, assign_monitoring_tier

OPENAQ_BASE = "https://api.openaq.org/v3"
API_KEY_FILE = Path("d:/ProjectCD/API.txt")

# Sensor-type strings OpenAQ uses to flag reference monitors. AirNow / SIATA /
# Air4Thai measurements come back tagged as "reference"; AirGradient and
# PurpleAir come back as "low-cost" / "lcs". Verify-by-network rather than
# trusting a single string match.
REFERENCE_NETWORK_HINTS = (
    "airnow", "siata", "air4thai", "epa", "cetesb", "reference",
    "embassy", "doe", "ema", "cea",
)
LCS_NETWORK_HINTS = ("airgradient", "purpleair", "clarity", "atmotube")


def _get_api_key() -> str | None:
    if not API_KEY_FILE.exists():
        return None
    for line in API_KEY_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"\s*OpenAQ API\s*[:=]\s*(\S+)", line, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _request(path: str, params: dict[str, Any] | None = None) -> dict:
    """GET with API key, basic retry, JSON parse."""
    headers = {}
    key = _get_api_key()
    if key:
        headers["X-API-Key"] = key

    url = f"{OPENAQ_BASE}{path}"
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=30)
            if r.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            last_exc = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"OpenAQ /v3 GET {path} failed after 3 attempts: {last_exc}")


def _classify_sensor(location: dict) -> tuple[bool, bool]:
    """Return (is_reference, has_calibration_metadata).

    `is_reference` = location's provider or instrument suggests a regulatory
    monitor.
    `has_calibration_metadata` = location is LCS but the network has
    documented calibration coefficients (AirGradient yes; PurpleAir
    sometimes; Clarity rarely).
    """
    provider = (location.get("provider") or {}).get("name", "").lower()
    instruments = location.get("instruments") or []
    instr_names = " ".join(
        (i.get("name") or "").lower() for i in instruments
    )
    haystack = f"{provider} {instr_names}"

    is_ref = any(h in haystack for h in REFERENCE_NETWORK_HINTS)
    is_lcs = any(h in haystack for h in LCS_NETWORK_HINTS)

    # AirGradient has published per-LCS calibration in this project already
    has_calib = "airgradient" in haystack

    return is_ref or (not is_lcs), has_calib


def _years_coverage(location: dict) -> float:
    """Continuous-year span from datetimeFirst/datetimeLast."""
    df = (location.get("datetimeFirst") or {}).get("utc")
    dl = (location.get("datetimeLast") or {}).get("utc")
    if not df or not dl:
        return 0.0
    from datetime import datetime
    try:
        first = datetime.fromisoformat(df.replace("Z", "+00:00"))
        last = datetime.fromisoformat(dl.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    return max(0.0, (last - first).days / 365.25)


def _has_param(location: dict, code: str) -> bool:
    sensors = location.get("sensors") or []
    for s in sensors:
        p = (s.get("parameter") or {})
        if (p.get("name") or "").lower() == code:
            return True
    return False


def extract(city: CityEntry, cf: CityFeatures, radius_m: int = 25_000) -> None:
    """Populate Block D fields on `cf` from OpenAQ /v3."""
    try:
        # Hourly PM2.5 is what we need; other pollutants noted as tiebreaker.
        params = {
            "coordinates": f"{city.lat},{city.lon}",
            "radius": radius_m,  # capped at 25_000 per API
            "limit": 1000,
            "parameters_id": "2",   # PM2.5 in OpenAQ /v3
        }
        data = _request("/locations", params=params)
    except Exception as e:
        cf.notes.append(f"OpenAQ /locations failed: {e}")
        cf.monitoring_tier = "M3"
        return

    results = data.get("results") or []
    if not results:
        cf.notes.append("OpenAQ: 0 PM2.5 locations within 25 km")
        cf.n_stations_25km = 0
        cf.monitoring_tier = "M3"
        return

    cf.n_stations_25km = len(results)
    cf.n_years_coverage = max(_years_coverage(loc) for loc in results)

    ref_flags = [_classify_sensor(loc) for loc in results]
    cf.has_reference_monitor = any(is_ref for is_ref, _ in ref_flags)
    cf.has_calibration_data = any(has_calib for _, has_calib in ref_flags)

    # Multi-pollutant tiebreaker — any location reports NO2 OR O3 OR PM10
    try:
        multi_params = {
            "coordinates": f"{city.lat},{city.lon}",
            "radius": radius_m,
            "limit": 200,
        }
        all_locs = _request("/locations", params=multi_params).get("results") or []
        has_no2 = any(_has_param(l, "no2") for l in all_locs)
        has_o3 = any(_has_param(l, "o3") for l in all_locs)
        has_pm10 = any(_has_param(l, "pm10") for l in all_locs)
        cf.multi_pollutant_available = has_no2 or has_o3 or has_pm10
        if cf.multi_pollutant_available:
            cf.notes.append(
                f"multi-pollutant: PM10={has_pm10} NO2={has_no2} O3={has_o3}"
            )
    except Exception as e:
        cf.notes.append(f"multi-pollutant probe failed (non-fatal): {e}")

    cf.monitoring_tier = assign_monitoring_tier(cf)
    cf.notes.append(
        f"OpenAQ: n_stations={cf.n_stations_25km} years={cf.n_years_coverage:.1f} "
        f"ref={cf.has_reference_monitor} calib={cf.has_calibration_data} "
        f"=> {cf.monitoring_tier}"
    )
