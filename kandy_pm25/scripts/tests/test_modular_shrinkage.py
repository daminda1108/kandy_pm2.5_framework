"""P2 (monotone skill) and P3 (exact nesting) tests for the tier shrinkage mechanism."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.modular import shrinkage as sh  # noqa: E402


def test_p3_zero_weight_reproduces_parent_exactly():
    rng = np.random.default_rng(0)
    parent, child = rng.normal(20, 5, 500), rng.normal(20, 5, 500)
    out = sh.combine(parent, child, 0.0)
    assert np.array_equal(out, parent)          # bit-exact, not approximate


def test_unit_weight_reproduces_child_exactly():
    rng = np.random.default_rng(1)
    parent, child = rng.normal(20, 5, 200), rng.normal(20, 5, 200)
    assert np.array_equal(sh.combine(parent, child, 1.0), child)


def test_weight_outside_unit_interval_is_refused():
    a = np.zeros(5)
    for bad in (-0.01, 1.01):
        with pytest.raises(ValueError):
            sh.combine(a, a, bad)


def test_p2_useless_child_collapses_toward_parent():
    """A child carrying pure noise must not be allowed to degrade the estimate."""
    rng = np.random.default_rng(2)
    truth = rng.normal(20, 6, 4000)
    parent = truth + rng.normal(0, 2, 4000)
    child = rng.normal(20, 6, 4000)              # uninformative
    r = sh.optimal_weight(parent, child, truth)
    sh.assert_monotone(r)
    assert r.w < 0.25, f"useless child got weight {r.w}"


def test_p2_informative_child_earns_weight():
    rng = np.random.default_rng(3)
    truth = rng.normal(20, 6, 4000)
    parent = truth + rng.normal(0, 5, 4000)
    child = truth + rng.normal(0, 1, 4000)       # genuinely better
    r = sh.optimal_weight(parent, child, truth)
    sh.assert_monotone(r)
    assert r.w > 0.7, f"informative child only got weight {r.w}"
    assert r.skill_shrunk < r.skill_parent


def test_p2_holds_across_random_problems():
    """The property that matters: never worse than the parent, whatever the child is."""
    rng = np.random.default_rng(4)
    for _ in range(25):
        n = 1500
        truth = rng.normal(20, 6, n)
        parent = truth + rng.normal(0, rng.uniform(1, 6), n)
        child = (truth * rng.uniform(0.5, 1.5) + rng.normal(0, rng.uniform(1, 9), n))
        sh.assert_monotone(sh.optimal_weight(parent, child, truth))


def test_grouped_folds_are_used_when_supplied():
    rng = np.random.default_rng(5)
    n = 2000
    truth = rng.normal(20, 6, n)
    parent = truth + rng.normal(0, 4, n)
    child = truth + rng.normal(0, 2, n)
    groups = rng.integers(0, 20, n)              # e.g. station id
    r = sh.optimal_weight(parent, child, truth, groups=groups)
    sh.assert_monotone(r)
    assert len(r.w_folds) >= 2
