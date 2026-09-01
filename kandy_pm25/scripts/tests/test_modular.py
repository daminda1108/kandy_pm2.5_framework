"""Invariant tests for the modular grey-box formulation (docs/MODEL_SPECIFICATION.md).

These sit alongside the existing 18 evidence-pipeline tests. They assert the CONTRACT: budget
nesting, admissibility refusal, the four hard constraints, and that the observation model
reproduces the known point-vs-area behaviour rather than hiding it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.modular import budgets as bd            # noqa: E402
from src.modular import constraints as ct        # noqa: E402
from src.modular import observation as obs       # noqa: E402


# ── budgets ───────────────────────────────────────────────────────────────────────────────

def test_registry_nesting_is_strict():
    """Ladder RUNGS must strictly contain their parent. Siblings (nested=False) trade a
    stream rather than adding one, and are exempt by declaration -- not by a hardcoded id."""
    for b in bd.REGISTRY.values():
        if b.parent and b.nested:
            assert bd.get(b.parent).admits < b.admits, f"{b.id} does not strictly contain parent"


def test_degradation_chain_reaches_root():
    assert bd.chain("Bud4") == ["Bud4", "Bud3", "Bud2", "Bud1", "Bud0"]
    assert bd.chain("Bud0") == ["Bud0"]


def test_admissibility_refuses_richer_stream():
    """The whole point: a tier cannot touch a stream it is not entitled to."""
    with pytest.raises(bd.AdmissibilityError):
        bd.BUD0.require(bd.SENSOR_PAIR)
    with pytest.raises(bd.AdmissibilityError):
        bd.BUD1.require(bd.REFERENCE_MONITOR)
    with pytest.raises(bd.AdmissibilityError):
        bd.BUD3.require(bd.SPATIAL_NETWORK)
    bd.BUD4.require(bd.SPATIAL_NETWORK, bd.REGIONAL_NETWORK, bd.REFERENCE_MONITOR)


def test_no_component_both_estimated_and_imposed():
    for b in bd.REGISTRY.values():
        assert not (b.estimates & b.imposes), b.id


def test_pattern_is_imposed_below_bud4():
    """Five independent tests found no learnable spatial signal below a local network."""
    for bid in ("Bud0", "Bud1", "Bud2", "Bud3"):
        assert bd.P in bd.get(bid).imposes
    assert bd.P in bd.BUD4.estimates


def test_background_only_estimated_from_bud3():
    for bid in ("Bud0", "Bud1", "Bud2"):
        assert bd.B in bd.get(bid).imposes
    assert bd.B in bd.BUD3.estimates


def test_sensor_bias_only_identifiable_with_a_reference_monitor():
    assert bd.BIAS not in bd.BUD1.estimates
    assert bd.BIAS in bd.BUD2.estimates


# ── constraints ───────────────────────────────────────────────────────────────────────────

def _synthetic(nh=48, npx=100, seed=0):
    rng = np.random.default_rng(seed)
    T = rng.uniform(8, 30, nh)
    B = T * rng.uniform(0.35, 0.7, nh)
    P = rng.uniform(0.5, 2.0, (nh, npx)); P /= P.mean(axis=1, keepdims=True)
    inc = T - B
    field = B[:, None] + np.clip(inc, 0, None)[:, None] * P + np.clip(inc, None, 0)[:, None]
    return field, T, B, P


def test_conservation_holds_on_the_split_form():
    field, T, B, P = _synthetic()
    assert ct.check_conservation(field, T) < ct.TOL_T_LOCK


def test_conservation_catches_a_broken_field():
    field, T, B, P = _synthetic()
    field = field + 1.0                       # a uniform level error breaks the T-lock
    with pytest.raises(ct.ConstraintViolation):
        ct.check_conservation(field, T)


def test_unit_mean_enforced_and_detected():
    field, T, B, P = _synthetic()
    assert ct.check_unit_mean(P) < 1e-9
    with pytest.raises(ct.ConstraintViolation):
        ct.check_unit_mean(P * 1.05)


def test_coherence_cap_detects_violation():
    T = np.array([10.0, 12.0, 20.0, 9.0])
    day = np.zeros(4, dtype=int)
    ct.check_coherence(np.full(4, 8.0), T, day)          # 8 <= 0.98*9, fine
    with pytest.raises(ct.ConstraintViolation):
        ct.check_coherence(np.full(4, 9.5), T, day)      # above the daily minimum


# ── observation model ─────────────────────────────────────────────────────────────────────

def _field_grid():
    lats = np.linspace(7.20, 7.35, 16)
    lons = np.linspace(80.55, 80.70, 16)
    yy, xx = np.meshgrid(lats, lons, indexing="ij")
    core = np.exp(-(((yy - 7.29) / 0.03) ** 2 + ((xx - 80.63) / 0.03) ** 2))
    return 15.0 + 20.0 * core, lats, lons


def test_point_operator_beats_areal_mean_at_a_core_site():
    """The registered expectation: an areal field read at a core point sits ABOVE the area mean.

    This is the +5.85 ug/m3 one-sided offset that made empirical coverage read 72.4%. With an
    observation operator it is a PREDICTED quantity, not an anomaly.
    """
    field, lats, lons = _field_grid()
    inst = obs.Instrument.reference("core", 7.29, 80.63)
    r = obs.compare(inst, observed=30.0, field=field, lats=lats, lons=lons)
    assert r["point_minus_areal"] > 0
    assert r["expected"] > r["areal_mean"]


def test_representativeness_sigma_vanishes_on_a_flat_field():
    lats = np.linspace(0, 1, 8); lons = np.linspace(0, 1, 8)
    flat = np.full((8, 8), 12.0)
    assert obs.representativeness_sigma(flat, lats, lons, 0.5, 0.5) == pytest.approx(0.0)


def test_representativeness_sigma_grows_with_structure():
    field, lats, lons = _field_grid()
    edge = obs.representativeness_sigma(field, lats, lons, 7.21, 80.56)
    slope = obs.representativeness_sigma(field, lats, lons, 7.275, 80.615)
    assert slope > edge


def test_lcs_carries_more_uncertainty_than_a_reference_monitor():
    field, lats, lons = _field_grid()
    ref = obs.Instrument.reference("ref", 7.29, 80.63)
    lcs = obs.Instrument.low_cost("lcs", 7.29, 80.63)
    assert lcs.predict(field, lats, lons)[1] > ref.predict(field, lats, lons)[1]


def test_time_integrated_operator_averages_the_window():
    field, lats, lons = _field_grid()
    op = obs.TimeIntegratedOperator(7.29, 80.63)
    one = op.apply([field], lats, lons)
    two = op.apply([field, field * 2.0], lats, lons)
    assert two == pytest.approx(1.5 * one, rel=1e-9)
