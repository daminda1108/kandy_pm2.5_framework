"""Diurnal emission-timing profile e(t) for the transport modulation (§3.4b).

Kandy's emissions are ~90% vehicular (vs ~55-60% in Colombo); the diurnal cycle is
therefore dominated by the road-traffic profile, reinforced by a smaller domestic-
combustion (cooking) term on the same morning/evening hours. The traffic shape follows
the EDGAR road-transport hour-of-day temporal profile (Crippa et al. 2020, Sci. Data);
domestic follows cooking studies (morning + heavier-evening peaks). Bimodal, mean 1.

This supplies the emission *clock* the spatial modulations otherwise lack: without it
the transport hotspot is gated by boundary-layer height alone and peaks through the dead
of night (low BLH) when emissions are minimal. With e(t) the hotspot follows the morning
and evening rush, when emissions and a shallow layer coincide.
"""
from __future__ import annotations
import numpy as np

# hour 0..23 local time
E_TRAFFIC = np.array([0.40, 0.30, 0.25, 0.25, 0.35, 0.60, 1.00, 1.65, 1.75, 1.45,
                      1.25, 1.20, 1.20, 1.20, 1.25, 1.35, 1.50, 1.70, 1.60, 1.35,
                      1.00, 0.75, 0.55, 0.45])
E_DOMESTIC = np.array([0.10, 0.10, 0.10, 0.10, 0.10, 0.30, 0.80, 1.80, 1.40, 0.70,
                       0.40, 0.40, 0.50, 0.40, 0.40, 0.50, 0.80, 1.40, 2.00, 1.80,
                       1.20, 0.60, 0.30, 0.20])

VEHICULAR_SHARE = 0.90        # Kandy ~90% vehicular (tunable prior)


def emission_profile(vehicular_share: float = VEHICULAR_SHARE) -> np.ndarray:
    """Normalised (mean 1) diurnal emission weight, length 24 (local hour)."""
    e = vehicular_share * E_TRAFFIC + (1.0 - vehicular_share) * E_DOMESTIC
    return e / e.mean()


E_NORM = emission_profile()


def e_at(hour_local) -> np.ndarray:
    """e(t) evaluated at an array (or scalar) of local hours 0..23."""
    return E_NORM[np.asarray(hour_local).astype(int) % 24]
