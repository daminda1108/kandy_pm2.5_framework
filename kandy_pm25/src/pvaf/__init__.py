"""PVAF v1 — Physics-based Valley Analogue Finder.

Pre-registration: docs/osf_prereg_pvaf_v1.md (locked 2026-05-23, OSF guid ykdb9).
Plan: docs/pvaf_v1_plan.md.
"""

from .feature_schema import (
    CityFeatures,
    FEATURE_WEIGHTS,
    BLOCK_A_FEATURES,
    BLOCK_B_FEATURES,
    BLOCK_C_FEATURES,
    WEIGHTED_FEATURES,
    KOPPEN_ALLOWED,
    assign_monitoring_tier,
)

__all__ = [
    "CityFeatures",
    "FEATURE_WEIGHTS",
    "BLOCK_A_FEATURES",
    "BLOCK_B_FEATURES",
    "BLOCK_C_FEATURES",
    "WEIGHTED_FEATURES",
    "KOPPEN_ALLOWED",
    "assign_monitoring_tier",
]
