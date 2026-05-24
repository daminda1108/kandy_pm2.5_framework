"""City registry for PVAF v1 — Kandy (target) + source cities + a-priori candidates.

The lat/lon for each city is the OpenAQ-station-cluster centroid where one exists,
otherwise the official city-hall coordinates (cf. pre-reg §4 buffer-anchor rule).

Köppen-Geiger class is the Beck et al. (2018) present-day classification, looked
up at the city-center coordinate. Recorded here for traceability; the extractor
re-verifies against the Beck raster at runtime.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class CityEntry:
    name: str
    country: str
    lat: float
    lon: float
    elev_m_approx: float
    koppen_expected: str
    role: str  # "target" | "current_source" | "candidate" | "negative_control"
    notes: str = ""


# Target — what we are trying to predict at zero-shot
TARGET = [
    CityEntry("Kandy", "LK", 7.2906, 80.6337, 500, "Am", "target",
              "Sri Lankan hill-country; KOALA + FECT + Embassy Colombo OOD"),
]

# Current Stage C source set (Mel, ChiMai, KTM)
CURRENT_SOURCES = [
    CityEntry("Medellin", "CO", 6.2476, -75.5658, 1495, "Cfb", "current_source",
              "SIATA network; predicted to score below ChiMai/KTM"),
    CityEntry("ChiangMai", "TH", 18.7883, 98.9853, 310, "Aw", "current_source",
              "Air4Thai + AirGradient; burning-season impacted"),
    CityEntry("Kathmandu", "NP", 27.7172, 85.3240, 1400, "Cwa", "current_source",
              "GD Labs + reference; severe Himalayan trapping"),
]

# A-priori candidate cities — predictions locked in pre-reg §9
CANDIDATES = [
    CityEntry("Quito", "EC", -0.1807, -78.4678, 2850, "Cfb", "candidate",
              "Predicted top-10; M2 likely"),
    CityEntry("AddisAbaba", "ET", 9.0300, 38.7400, 2355, "Cwb", "candidate",
              "Predicted top-15 physics; M3 likely (monitoring gap)"),
    CityEntry("LaPaz", "BO", -16.5000, -68.1500, 3640, "Cwb", "candidate",
              "Extreme valley physics; M3 likely"),
    CityEntry("Tehran", "IR", 35.6892, 51.3890, 1200, "Cwa", "candidate",
              "Severe trapping basin; M3 likely"),
    CityEntry("Antananarivo", "MG", -18.8792, 47.5079, 1280, "Cwb", "candidate",
              "Highland; M3 likely"),
    CityEntry("Bogota", "CO", 4.7110, -74.0721, 2640, "Cfb", "candidate",
              "Plateau not valley; predicted top-20 — re-evaluate post-PVAF"),
    CityEntry("MexicoCity", "MX", 19.4326, -99.1332, 2240, "Cwb", "candidate",
              "Too large/latitudinal — predicted top-30; re-evaluate"),
]

# Explicit negative control — pre-reg §9.2 predicts Hanoi falls OUTSIDE top 30.
# If it doesn't, the metric is broken.
NEGATIVE_CONTROLS = [
    CityEntry("Hanoi", "VN", 21.0285, 105.8542, 20, "Cwa", "negative_control",
              "NOT a valley; pre-reg falsification probe — must rank LOW"),
]

# Secondary-pool cities (excluded by Köppen filter; reported as robustness check)
SECONDARY_POOL = [
    CityEntry("SaltLakeCity", "US", 40.7608, -111.8910, 1290, "BSk", "candidate",
              "Excluded by Köppen; mid-lat CAP analogue for Kandy winter"),
    CityEntry("Sarajevo", "BA", 43.8563, 18.4131, 550, "Dfb", "candidate",
              "Excluded by Köppen; well-monitored highland valley"),
]


ALL_PRIMARY = TARGET + CURRENT_SOURCES + CANDIDATES + NEGATIVE_CONTROLS
ALL_CITIES = ALL_PRIMARY + SECONDARY_POOL

CITY_BY_NAME: dict[str, CityEntry] = {c.name: c for c in ALL_CITIES}


def get_city(name: str) -> CityEntry:
    """Lookup by canonical name (case-insensitive)."""
    key = name.strip()
    for canonical in CITY_BY_NAME:
        if canonical.lower() == key.lower():
            return CITY_BY_NAME[canonical]
    raise KeyError(f"Unknown city: {name!r}. Known: {sorted(CITY_BY_NAME)}")
