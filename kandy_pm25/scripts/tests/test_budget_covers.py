"""The dual admissibility check (F.84).

`require()` stops a tier reaching for information it was not granted. Nothing stopped a tier
quietly failing to use what it HAD -- and that asymmetry inflated the headline result, because
every gain on the ladder is measured against the rung below it.

The decisive test here is `test_the_actual_F84_defect_is_caught`: it replays the real feature
set of the scored `Bud0` and asserts the new check rejects it.
"""
import pytest

from src.modular.budgets import (
    AdmissibilityError, DRIVERS_REANALYSIS, SATELLITE_LEVEL, STATIC_GEO, SENSOR_PAIR, get,
)


def test_full_coverage_passes():
    get("Bud0").require_covers(SATELLITE_LEVEL, DRIVERS_REANALYSIS, STATIC_GEO)


def test_the_actual_F84_defect_is_caught():
    """The scored Bud0 used drivers ONLY. The check must reject exactly that."""
    with pytest.raises(AdmissibilityError) as e:
        get("Bud0").require_covers(DRIVERS_REANALYSIS)
    msg = str(e.value)
    assert "satellite_level" in msg and "static_geo" in msg
    assert "F.84" in msg


def test_partial_coverage_is_caught():
    with pytest.raises(AdmissibilityError):
        get("Bud0").require_covers(DRIVERS_REANALYSIS, STATIC_GEO)   # no satellite level


def test_declared_omission_is_allowed_but_must_be_explicit():
    """An omission is permitted only when it is written down at the call site."""
    get("Bud0").require_covers(DRIVERS_REANALYSIS,
                               allow=[SATELLITE_LEVEL, STATIC_GEO])


def test_the_two_checks_are_independent():
    """require() and require_covers() catch opposite failures and neither implies the other."""
    b = get("Bud0")
    b.require(DRIVERS_REANALYSIS)                       # under-powered: require() is happy
    with pytest.raises(AdmissibilityError):
        b.require_covers(DRIVERS_REANALYSIS)            # ... and require_covers() is not
    with pytest.raises(AdmissibilityError):
        b.require(SENSOR_PAIR)                          # over-reaching: require() catches it


def test_every_rung_can_satisfy_its_own_budget():
    for bid in ("Bud0", "Bud1", "Bud2", "Bud3", "Bud4"):
        b = get(bid)
        b.require_covers(*sorted(b.admits))
