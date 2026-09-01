"""Sector-weighted emission surface: degradation, unit mean, and honest failure."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.modular import emission as em   # noqa: E402


def _grids(seed=0, n=16):
    rng = np.random.default_rng(seed)
    return {"traffic": rng.uniform(0.2, 3.0, (n, n)),
            "population": rng.uniform(0.1, 5.0, (n, n)),
            "ntl": rng.uniform(0.0, 2.0, (n, n))}


def test_vehic_only_reproduces_traffic_surface_exactly():
    """Graceful degradation: adopting this must not move a traffic-only city."""
    g = _grids()
    s = em.compose(g, {"vehic": 1.0})
    assert np.allclose(s.S, em.unit_mean(g["traffic"]), rtol=0, atol=0)


def test_surface_is_always_unit_mean():
    g = _grids()
    for mix in ({"vehic": 1.0}, {"vehic": .4, "heat": .1, "burn": .5},
                {"vehic": .35, "heat": .65}):
        assert em.compose(g, mix).S.mean() == pytest.approx(1.0, rel=1e-12)


def test_weights_are_emission_shares_not_proxy_units():
    """Each proxy is unit-meaned BEFORE weighting, so a proxy in different units cannot
    hijack the mix."""
    g = _grids()
    a = em.compose(g, {"vehic": .5, "heat": .5}).S
    g2 = dict(g, population=g["population"] * 1000.0)
    b = em.compose(g2, {"vehic": .5, "heat": .5}).S
    assert np.allclose(a, b, rtol=1e-12)


def test_mixed_surface_differs_from_traffic_only():
    g = _grids()
    mixed = em.compose(g, {"vehic": .4, "heat": .1, "burn": .5}).S
    assert not np.allclose(mixed, em.unit_mean(g["traffic"]), atol=1e-6)


def test_missing_sector_is_recorded_not_silently_dropped():
    """Silently dropping a sector turns a mixed-source city back into a traffic-only one."""
    g = {"traffic": _grids()["traffic"]}
    s = em.compose(g, {"vehic": .4, "heat": .1, "burn": .5})
    assert "heat" in s.dropped and "burn" in s.dropped
    assert s.weights_used == {"vehic": 1.0}
    assert any("redistributed" in p for p in s.provenance)


def test_strict_mode_refuses_a_missing_sector():
    g = {"traffic": _grids()["traffic"]}
    with pytest.raises(em.ProxyError):
        em.compose(g, {"vehic": .5, "burn": .5}, strict=True)


def test_industry_has_no_fallback():
    """Industry is precisely the sector that does not track roads or population."""
    g = _grids()
    s = em.compose(g, {"vehic": .5, "industry": .5})
    assert "industry" in s.dropped


def test_placeholder_burn_proxy_is_flagged():
    g = _grids()
    s = em.compose(g, {"vehic": .5, "burn": .5})
    assert s.is_placeholder_dependent
    s2 = em.compose(dict(g, fire=np.abs(_grids(1)["population"])), {"vehic": .5, "burn": .5})
    assert not s2.is_placeholder_dependent


def test_t_lock_survives_the_sector_surface():
    """The field equation's basin mean must still return T for any mix."""
    g = _grids()
    P = em.compose(g, {"vehic": .4, "heat": .1, "burn": .5}).S.ravel()
    T, B = 22.0, 11.0
    field = B + max(T - B, 0) * P + min(T - B, 0)
    assert field.mean() == pytest.approx(T, rel=1e-12)
