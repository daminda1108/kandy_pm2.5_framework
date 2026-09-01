"""Tier contract tests: admissibility at execution, and P3 exact degradation across all pairs."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.modular import budgets as bd   # noqa: E402
from src.modular import tiers as tr     # noqa: E402


def _ctx(n=64, seed=0):
    rng = np.random.default_rng(seed)
    return {"prior": rng.uniform(8, 30, n), "pair": rng.uniform(8, 30, n),
            "ref": rng.uniform(8, 30, n), "reg": rng.uniform(3, 12, n),
            "spatial": rng.uniform(0.5, 2.0, n), "geo": np.ones(n)}


def _prov(component, requires, key, name):
    return tr.ComponentProvider(component=component, requires=frozenset(requires),
                                fn=lambda ctx, k=key: np.asarray(ctx[k], float), name=name)


def _tier(bid):
    """A minimal tier per budget, each estimating exactly what its budget claims."""
    b = bd.get(bid)
    p = {}
    p[bd.L] = _prov(bd.L, {bd.SATELLITE_LEVEL}, "prior", "L")
    if bid == "Bud0":
        p[bd.A] = _prov(bd.A, {bd.DRIVERS_REANALYSIS}, "prior", "A0")
    elif bid == "Bud1":
        p[bd.A] = _prov(bd.A, {bd.DRIVERS_REANALYSIS, bd.SENSOR_PAIR}, "pair", "A1")
    elif bid in ("Bud2", "Bud3", "Bud4"):
        p[bd.A] = _prov(bd.A, {bd.DRIVERS_REANALYSIS, bd.REFERENCE_MONITOR}, "ref", "A2")
    if bd.B in b.estimates:
        p[bd.B] = _prov(bd.B, {bd.REGIONAL_NETWORK}, "reg", "B3")
    if bd.P in b.estimates:
        p[bd.P] = _prov(bd.P, {bd.SPATIAL_NETWORK}, "spatial", "P4")
    return tr.Tier(budget=b, providers=p)


def test_every_registry_budget_builds_a_valid_tier():
    for bid in ("Bud0", "Bud1", "Bud2", "Bud3", "Bud4"):
        _tier(bid).validate()


def test_provider_needing_an_inadmissible_stream_is_refused_at_build():
    with pytest.raises(bd.AdmissibilityError):
        tr.Tier(budget=bd.BUD0,
                providers={bd.A: _prov(bd.A, {bd.REFERENCE_MONITOR}, "ref", "leak")})


def test_provider_with_unknown_stream_is_refused():
    with pytest.raises(bd.AdmissibilityError):
        _prov(bd.A, {"telepathy"}, "ref", "bogus")


def test_tier_claiming_to_estimate_without_a_provider_is_refused():
    with pytest.raises(bd.AdmissibilityError):
        tr.Tier(budget=bd.BUD4, providers={bd.L: _prov(bd.L, {bd.SATELLITE_LEVEL}, "prior", "L")})


def test_run_returns_every_component():
    out = _tier("Bud4").run(_ctx())
    for c in (bd.L, bd.A, bd.B, bd.P):
        assert c in out and np.all(np.isfinite(out[c]))


@pytest.mark.parametrize("child,parent", [("Bud1", "Bud0"), ("Bud2", "Bud1"),
                                          ("Bud3", "Bud2"), ("Bud4", "Bud3")])
def test_p3_degradation_is_bit_exact(child, parent):
    """Withholding the extra stream must reproduce the parent EXACTLY, not approximately."""
    ctx = _ctx(seed=7)
    got = _tier(child).degrade_to(_tier(parent)).run(ctx)
    ref = _tier(parent).run(ctx)
    assert set(got) == set(ref)
    for c in ref:
        assert np.array_equal(got[c], ref[c]), f"{child}->{parent} not bit-exact on {c}"


def test_degrade_to_wrong_parent_is_refused():
    with pytest.raises(bd.AdmissibilityError):
        _tier("Bud3").degrade_to(_tier("Bud0"))


def test_streams_used_never_exceeds_budget():
    for bid in ("Bud0", "Bud1", "Bud2", "Bud3", "Bud4"):
        t = _tier(bid)
        assert t.streams_used() <= t.budget.admits


# ── production bindings ───────────────────────────────────────────────────────────────────

def test_every_production_builder_declares_a_known_budget():
    from src.modular import production as pr
    for builder in pr.BINDINGS:
        assert pr.declare(builder).id in bd.REGISTRY


def test_undeclared_builder_is_refused():
    from src.modular import production as pr
    with pytest.raises(pr.BindingError):
        pr.declare("a_builder_that_does_not_exist")


def test_locked_kandy_chain_runs_at_the_two_sensor_budget():
    """T(t) is trained AND sharpened on FECT, so the whole locked chain is Bud1, not Bud0."""
    from src.modular import production as pr
    for builder in ("predict_T_anchor_v3", "sharpen_T_diurnal",
                    "build_additive_field_v2", "build_additive_field_v3", "webapp_export"):
        assert pr.declare(builder).id == "Bud1"


def test_extension_tier_is_a_sibling_not_a_rung():
    """BudExt DROPS the satellite level anchor, so P2/P3 do not apply between it and Bud1."""
    from src.modular import production as pr
    ext = pr.declare("kandy_driver_tier_build")
    assert ext.id == "BudExt"
    assert ext.nested is False
    assert bd.SATELLITE_LEVEL in bd.BUD1.admits
    assert bd.SATELLITE_LEVEL not in ext.admits


def test_forecast_tier_is_a_sibling_not_a_rung():
    from src.modular import production as pr
    f = pr.declare("kandy_live_forecast")
    assert f.nested is False and bd.FORWARD_DRIVERS in f.admits


def test_production_builder_cannot_claim_an_inadmissible_stream():
    from src.modular import production as pr
    with pytest.raises(bd.AdmissibilityError):
        pr.require("build_additive_field_v2", bd.REFERENCE_MONITOR)
    pr.require("build_additive_field_v2", bd.SATELLITE_LEVEL, bd.SENSOR_PAIR)


def test_non_nested_budgets_are_exempt_from_strict_nesting_only():
    for b in bd.REGISTRY.values():
        if b.parent and b.nested:
            assert bd.get(b.parent).admits < b.admits
