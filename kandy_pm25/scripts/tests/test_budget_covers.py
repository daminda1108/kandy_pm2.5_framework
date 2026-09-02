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


# ── C7: per-unit coverage (plan 2026-09-01) ───────────────────────────────────────────────
# require_covers() closes F.84 at the TIER level. It cannot see that an individual scored city
# carries none of the data the tier is named for. One city was scored in Bud0c with no
# STATIC_GEO at all; HistGBM accepts NaN and trained around it, and enforcing coverage moves the
# headline first rung 17.8% -> 15.8%.

def test_require_covers_units_passes_when_every_unit_is_complete():
    b = get("Bud0")
    full = {s: sorted(b.admits) for s in ("cityA", "cityB", "cityC")}
    b.require_covers_units(full)  # must not raise


def test_require_covers_units_raises_on_a_single_short_unit():
    b = get("Bud0")
    cov = {"cityA": sorted(b.admits), "cityB": sorted(b.admits)}
    cov["3147"] = [s for s in b.admits if s != STATIC_GEO]
    with pytest.raises(AdmissibilityError) as e:
        b.require_covers_units(cov)
    msg = str(e.value)
    assert "3147" in msg and STATIC_GEO in msg
    assert "1 of 3" in msg


def test_require_covers_units_allow_declares_the_concession():
    b = get("Bud0")
    cov = {"c1": [DRIVERS_REANALYSIS, SATELLITE_LEVEL]}
    with pytest.raises(AdmissibilityError):
        b.require_covers_units(cov)
    b.require_covers_units(cov, allow=[STATIC_GEO])  # declared -> allowed


def test_require_covers_units_reports_all_offenders_not_just_the_first():
    b = get("Bud0")
    cov = {f"c{i}": [DRIVERS_REANALYSIS] for i in range(9)}
    with pytest.raises(AdmissibilityError) as e:
        b.require_covers_units(cov)
    assert "9 of 9" in str(e.value)
    assert "+4 more" in str(e.value)


def test_tier_level_check_passes_while_unit_level_fails():
    """The exact C7 shape: the design is right and the data is not."""
    b = get("Bud0")
    b.require_covers(DRIVERS_REANALYSIS, SATELLITE_LEVEL, STATIC_GEO)  # tier-level: PASS
    cov = {"good": sorted(b.admits), "3147": [DRIVERS_REANALYSIS, SATELLITE_LEVEL]}
    with pytest.raises(AdmissibilityError):
        b.require_covers_units(cov)  # unit-level: FAIL


# ── gotcha #85: a stream can merge cleanly and arrive empty ────────────────────────────────
# The MAIAC pull joined on (city, date) with matching keys and correct dtypes, and delivered a
# column that was NaN for a median of 100% of each city's rows, because it had been pulled for
# 2019-2022 against a frame spanning 2021-2026. HistGBM fitted it and returned a clean number.

import pandas as pd  # noqa: E402

from src.modular.budgets import require_stream_coverage  # noqa: E402


def _frame(cov_by_city):
    """cov_by_city: {city: fraction of 20 rows that are non-null}."""
    rows = []
    for c, frac in cov_by_city.items():
        n = 20
        vals = [1.0] * int(round(frac * n)) + [float("nan")] * (n - int(round(frac * n)))
        rows += [{"city": c, "aod": v} for v in vals]
    return pd.DataFrame(rows)


def test_coverage_passes_when_the_stream_is_really_there():
    require_stream_coverage(_frame({"a": 0.9, "b": 0.8, "c": 0.7}), "aod")


def test_coverage_tolerates_genuine_cloud_gaps():
    # 40% coverage is a real satellite stream, not a broken merge.
    require_stream_coverage(_frame({"a": 0.4, "b": 0.45, "c": 0.4}), "aod")


def test_the_actual_gotcha85_defect_is_caught():
    """The MAIAC shape: merged, typed, keyed correctly, and empty."""
    with pytest.raises(AdmissibilityError) as e:
        require_stream_coverage(_frame({"a": 0.0, "b": 0.0, "c": 0.0}), "aod")
    msg = str(e.value)
    assert "merged but EMPTY" in msg and "gotcha #85" in msg


def test_coverage_cannot_pass_on_its_mean():
    """A stream present for a few units and absent for the rest must not average its way through."""
    with pytest.raises(AdmissibilityError):
        require_stream_coverage(_frame({"a": 1.0, "b": 1.0, "c": 0.0, "d": 0.0, "e": 0.0}), "aod")


def test_missing_column_says_the_merge_did_not_happen():
    with pytest.raises(AdmissibilityError) as e:
        require_stream_coverage(_frame({"a": 1.0}), "sat_level")
    assert "did not happen" in str(e.value)
