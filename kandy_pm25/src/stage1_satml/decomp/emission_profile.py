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

VEHICULAR_SHARE = 0.90        # Kandy ~90% vehicular
# ── STATUS (2026-08-06, W10): the vehicular share is a prior with LOCAL OBSERVATIONAL
# SUPPORT, and the evening lobe below is a LOCAL CORRECTION, not literature.
# `scripts/kandy_holiday_experiment.py` uses Sri Lankan public holidays as a natural
# experiment: they remove local activity and leave transboundary transport untouched, so
# the holiday-minus-working-day difference at hour h estimates the local emission clock.
# It confirmed the ~90% vehicular assumption (the effect is 3.67x stronger at rush hours,
# and zero at midnight -- the vehicle signature) and rejected one feature of the profile.
# `scripts/kandy_emission_clock_fit.py` quantifies it on 971 treated sensor-hours:
#
#     quantity                 EDGAR prior     measured (bootstrap 90% CI)
#     morning peak hour        08:00           08:00              <- prior CONFIRMED
#     evening peak hour        17:00           19:00 [17, 21]
#     evening/morning ratio    0.97            2.14 [1.17, 4.35]  <- prior REJECTED
#
# The CI on the ratio excludes the prior value, so the prior is not merely uncertain
# there. The correction below shifts the evening lobe +1 h and raises it by x1.479,
# SHRUNK toward the prior in proportion to the width of the bootstrap interval (w=0.40)
# because ~40 treated hours per bin is thin. Morning lobe, night floor and overall shape
# remain the EDGAR prior -- the instrument identifies the evening lobe and nothing more.
# Agreement with the measured clock rises from r=0.49 to r=0.79.
# Set EVENING_FIT = False to recover the pre-2026-08-06 literature-only profile exactly.
EVENING_FIT = True
_EVE = np.arange(14, 24)      # hours the correction touches
_EVE_SHIFT = 1                # hours later, from the measured peak
_EVE_GAIN = 1.479             # amplitude above the night floor, shrunk toward the prior


def _correct_evening(prof: np.ndarray) -> np.ndarray:
    """Shift and scale the evening lobe above the night floor. Mean-preserving."""
    p = np.asarray(prof, float).copy()
    floor = p[[2, 3]].mean()
    lobe = np.clip(p[_EVE] - floor, 0.0, None) * _EVE_GAIN
    # shift LATER with edge clamping. np.roll would wrap the tail of the lobe back onto
    # the first hour of the window and punch a hole at 14:00 -- the shift is in time,
    # not a rotation.
    idx = np.clip(np.arange(len(lobe)) - _EVE_SHIFT, 0, len(lobe) - 1)
    p[_EVE] = floor + lobe[idx]
    return p


def emission_profile(vehicular_share: float = VEHICULAR_SHARE,
                     evening_fit: bool = None) -> np.ndarray:
    """Normalised (mean 1) diurnal emission weight, length 24 (local hour)."""
    if evening_fit is None:
        evening_fit = EVENING_FIT
    traffic = _correct_evening(E_TRAFFIC) if evening_fit else E_TRAFFIC
    e = vehicular_share * traffic + (1.0 - vehicular_share) * E_DOMESTIC
    return e / e.mean()


E_NORM = emission_profile()


def e_at(hour_local) -> np.ndarray:
    """e(t) evaluated at an array (or scalar) of local hours 0..23."""
    return E_NORM[np.asarray(hour_local).astype(int) % 24]
