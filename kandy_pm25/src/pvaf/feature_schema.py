"""Typed feature schema for PVAF v1.

Locked by OSF pre-registration ykdb9 (2026-05-23).

This file is the single source of truth for:
  - Feature names, units, and weights (Blocks A, B, C)
  - Köppen-Geiger hard-filter allowed classes
  - Monitoring tier (M1 / M2 / M3) assignment logic
  - JSON (de)serialisation of per-city feature vectors

NOTHING in this file may be tuned against PVAF rankings or v15 LOOCV
outcomes. Any change here is a pre-reg deviation and must be logged as
amendment 10a / 10b / ... in docs/osf_prereg_pvaf_v1.md before being
applied.

Extraction is OUT OF SCOPE for this module — see
scripts/pvaf/extract_city_features.py (Phase 2).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal, Optional

# ----------------------------------------------------------------------------
# Feature catalogue — Section 4 of the OSF pre-reg
# ----------------------------------------------------------------------------

# Block A — Topographic / geometric (sum = 0.30, 15 km buffer)
BLOCK_A_FEATURES: dict[str, float] = {
    "valley_depth_m":            0.08,
    "valley_width_km":           0.05,
    "aspect_ratio":              0.04,
    "drainage_area_km2":         0.04,
    "elev_p10":                  0.02,
    "elev_p50":                  0.02,
    "elev_p90":                  0.01,
    "valley_orientation_deg":    0.02,
    "terrain_ruggedness_index":  0.02,
}

# Block B — Climatological (sum = 0.40, 2015-2024 ERA5)
BLOCK_B_FEATURES: dict[str, float] = {
    "blh_annual_mean_m":         0.08,
    "blh_diurnal_range_m":       0.08,
    "blh_p10_m":                 0.05,
    "stability_freq":            0.06,
    "wind_speed_10m_annual":     0.04,
    "wet_season_precip_mm":      0.03,
    "dry_season_precip_mm":      0.03,
    "latitude_abs":              0.03,
}

# Block C — Emission regime (sum = 0.25, 25 km buffer; 50 km for fires)
BLOCK_C_FEATURES: dict[str, float] = {
    "ntl_log_mean":              0.07,
    "pop_density_log":           0.06,
    "edgar_pm25_kg_m2_yr":       0.05,
    "edgar_residential_frac":    0.04,
    "fire_count_50km_yr":        0.03,
}

# Combined weight table — used by score_tier1.py
WEIGHTED_FEATURES: dict[str, float] = {
    **BLOCK_A_FEATURES,
    **BLOCK_B_FEATURES,
    **BLOCK_C_FEATURES,
}
FEATURE_WEIGHTS = WEIGHTED_FEATURES  # alias

# Lock check — weights must sum to 0.95 (intentional: 0.30 + 0.40 + 0.25)
_BLOCK_A_SUM = round(sum(BLOCK_A_FEATURES.values()), 6)
_BLOCK_B_SUM = round(sum(BLOCK_B_FEATURES.values()), 6)
_BLOCK_C_SUM = round(sum(BLOCK_C_FEATURES.values()), 6)
assert _BLOCK_A_SUM == 0.30, f"Block A weights sum to {_BLOCK_A_SUM}, expected 0.30"
assert _BLOCK_B_SUM == 0.40, f"Block B weights sum to {_BLOCK_B_SUM}, expected 0.40"
assert _BLOCK_C_SUM == 0.25, f"Block C weights sum to {_BLOCK_C_SUM}, expected 0.25"

BLOCK_OF: dict[str, str] = (
    {name: "A" for name in BLOCK_A_FEATURES}
    | {name: "B" for name in BLOCK_B_FEATURES}
    | {name: "C" for name in BLOCK_C_FEATURES}
)

# Köppen-Geiger hard filter — Section 5 of the OSF pre-reg
KOPPEN_ALLOWED: frozenset[str] = frozenset({"Cfb", "Cwa", "Cwb", "Aw", "Am", "Cfa"})

# ----------------------------------------------------------------------------
# Per-city feature vector
# ----------------------------------------------------------------------------

MonitoringTier = Literal["M1", "M2", "M3"]


@dataclass
class CityFeatures:
    """One city's PVAF feature vector. Mirrors Section 4 of the pre-reg.

    `None` for any weighted field means extraction failed or data is
    unavailable — these cities should NOT enter Tier 1 scoring without
    imputation, which is itself a deviation.
    """

    # Identity / metadata
    city: str
    country: str
    lat: float
    lon: float
    koppen: str
    elev_center_m: float
    extraction_date: str  # ISO date, set by extractor
    schema_version: str = "pvaf_v1"

    # Block A — Topography (15 km buffer)
    valley_depth_m: Optional[float] = None
    valley_width_km: Optional[float] = None
    aspect_ratio: Optional[float] = None
    drainage_area_km2: Optional[float] = None
    elev_p10: Optional[float] = None
    elev_p50: Optional[float] = None
    elev_p90: Optional[float] = None
    valley_orientation_deg: Optional[float] = None
    terrain_ruggedness_index: Optional[float] = None

    # Block B — Climate (ERA5 2015-2024, city-center cell)
    blh_annual_mean_m: Optional[float] = None
    blh_diurnal_range_m: Optional[float] = None
    blh_p10_m: Optional[float] = None
    stability_freq: Optional[float] = None
    wind_speed_10m_annual: Optional[float] = None
    wet_season_precip_mm: Optional[float] = None
    dry_season_precip_mm: Optional[float] = None
    latitude_abs: Optional[float] = None

    # Block C — Emissions (25 km buffer; 50 km for fires)
    ntl_log_mean: Optional[float] = None
    pop_density_log: Optional[float] = None
    edgar_pm25_kg_m2_yr: Optional[float] = None
    edgar_residential_frac: Optional[float] = None
    fire_count_50km_yr: Optional[float] = None

    # Block D — Monitoring practicality (FILTER, not weighted)
    n_stations_25km: int = 0
    n_years_coverage: float = 0.0
    has_reference_monitor: bool = False
    has_calibration_data: bool = False
    multi_pollutant_available: bool = False  # tiebreaker only (Section 8)

    # Derived: monitoring tier, populated by assign_monitoring_tier()
    monitoring_tier: Optional[MonitoringTier] = None

    # Provenance — free-form notes from extraction (gaps, fallbacks, etc.)
    notes: list[str] = field(default_factory=list)

    # -- helpers -------------------------------------------------------------

    def feature_vector(self) -> dict[str, float]:
        """Return the dict of weighted features in canonical order.

        Raises ValueError if any weighted feature is None — that city
        cannot enter Tier 1 scoring without explicit imputation.
        """
        missing = [
            name for name in WEIGHTED_FEATURES
            if getattr(self, name) is None
        ]
        if missing:
            raise ValueError(
                f"{self.city}: missing weighted features {missing}; "
                "cannot enter Tier 1 scoring without imputation."
            )
        return {name: float(getattr(self, name)) for name in WEIGHTED_FEATURES}

    def passes_koppen_filter(self) -> bool:
        """True iff the city's Köppen class is in KOPPEN_ALLOWED."""
        return self.koppen in KOPPEN_ALLOWED

    def to_json(self, path: Path | str) -> None:
        Path(path).write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def from_json(cls, path: Path | str) -> CityFeatures:
        data = json.loads(Path(path).read_text())
        # Backwards-compat — drop fields not in the current dataclass.
        valid = {k: data[k] for k in cls.__dataclass_fields__ if k in data}
        return cls(**valid)


# ----------------------------------------------------------------------------
# Monitoring-tier assignment — Section 6 of the OSF pre-reg
# ----------------------------------------------------------------------------

def assign_monitoring_tier(cf: CityFeatures) -> MonitoringTier:
    """Assign exactly one of M1 / M2 / M3 per the locked thresholds.

    M1: reference monitor AND >=5 stations AND >=3 years
    M2: (reference AND >=3 stations AND >=2 years)
        OR (all-LCS AND calibration AND >=5 stations AND >=3 years)
    M3: otherwise
    """
    ref = cf.has_reference_monitor
    n = cf.n_stations_25km
    yrs = cf.n_years_coverage

    if ref and n >= 5 and yrs >= 3:
        return "M1"

    m2_reference = ref and n >= 3 and yrs >= 2
    m2_lcs = (not ref) and cf.has_calibration_data and n >= 5 and yrs >= 3
    if m2_reference or m2_lcs:
        return "M2"

    return "M3"


# ----------------------------------------------------------------------------
# Self-check — runnable as a module-level sanity test
# ----------------------------------------------------------------------------

def _self_check() -> None:
    """Verify the locked invariants. Called when run as a script."""
    assert len(WEIGHTED_FEATURES) == 22, len(WEIGHTED_FEATURES)
    assert round(sum(WEIGHTED_FEATURES.values()), 6) == 0.95
    assert KOPPEN_ALLOWED == frozenset({"Cfb", "Cwa", "Cwb", "Aw", "Am", "Cfa"})

    dummy = CityFeatures(
        city="Test", country="XX", lat=0.0, lon=0.0,
        koppen="Cfb", elev_center_m=500.0, extraction_date="2026-05-23",
        n_stations_25km=5, n_years_coverage=3.5,
        has_reference_monitor=True, has_calibration_data=False,
    )
    assert dummy.passes_koppen_filter()
    assert assign_monitoring_tier(dummy) == "M1"

    dummy.n_stations_25km = 3
    dummy.n_years_coverage = 2.0
    assert assign_monitoring_tier(dummy) == "M2"

    dummy.has_reference_monitor = False
    dummy.has_calibration_data = True
    dummy.n_stations_25km = 5
    dummy.n_years_coverage = 3.0
    assert assign_monitoring_tier(dummy) == "M2"

    dummy.has_calibration_data = False
    assert assign_monitoring_tier(dummy) == "M3"

    print("feature_schema.py self-check PASS")
    print(f"  {len(WEIGHTED_FEATURES)} weighted features, sum = {sum(WEIGHTED_FEATURES.values()):.4f}")
    print(f"  Blocks: A={_BLOCK_A_SUM}, B={_BLOCK_B_SUM}, C={_BLOCK_C_SUM}")
    print(f"  Köppen allowed: {sorted(KOPPEN_ALLOWED)}")


if __name__ == "__main__":
    _self_check()
