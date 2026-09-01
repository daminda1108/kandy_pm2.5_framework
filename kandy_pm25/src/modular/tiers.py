"""Tier execution — binds an information budget to concrete component estimators.

MODEL_SPECIFICATION.md section 5.1. A `Tier` is a `Budget` plus one `ComponentProvider` per
component (L, B, A, P). Each provider declares the streams it consumes, and `Tier.run()`
asserts those against the budget BEFORE calling anything. A provider that reaches for a stream
its budget does not admit raises rather than silently producing a leaked estimate.

`Tier.degrade_to(parent)` drops every provider that needs a stream above the parent budget and
substitutes the parent's provider. The P3 guarantee is then a testable statement:

    tier.degrade_to(parent).run(ctx) == parent_tier.run(ctx)      bit-exactly

which `test_modular_tiers.py` asserts for every adjacent pair in the registry.

This module carries NO science. It is the harness that makes the tier contract enforceable; the
component estimators are supplied by the caller.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, FrozenSet, Mapping

import numpy as np

from . import budgets as bd


@dataclass(frozen=True)
class ComponentProvider:
    """One way of estimating one component, with its information requirements declared."""

    component: str
    requires: FrozenSet[str]
    fn: Callable[[Mapping], np.ndarray]
    name: str = ""

    def __post_init__(self):
        unknown = self.requires - bd.ALL_STREAMS
        if unknown:
            raise bd.AdmissibilityError(
                f"provider {self.name or self.component} declares unknown streams {sorted(unknown)}")

    def __call__(self, ctx: Mapping) -> np.ndarray:
        return self.fn(ctx)


@dataclass
class Tier:
    """A budget bound to a set of component providers."""

    budget: bd.Budget
    providers: dict[str, ComponentProvider] = field(default_factory=dict)

    def __post_init__(self):
        self.validate()

    # ── contract ──────────────────────────────────────────────────────────────────────────
    def validate(self) -> None:
        """Every provider must be admissible, and estimated components must have providers."""
        for comp, prov in self.providers.items():
            if comp != prov.component:
                raise bd.AdmissibilityError(
                    f"provider registered under {comp!r} declares component {prov.component!r}")
            bad = prov.requires - self.budget.admits
            if bad:
                raise bd.AdmissibilityError(
                    f"{self.budget.id}: provider for {comp} requires {sorted(bad)}, "
                    f"which this budget does not admit")
        missing = [c for c in self.budget.estimates
                   if c in (bd.L, bd.B, bd.A, bd.P) and c not in self.providers]
        if missing:
            raise bd.AdmissibilityError(
                f"{self.budget.id} claims to estimate {missing} but has no provider for them")

    def run(self, ctx: Mapping) -> dict[str, np.ndarray]:
        """Execute every provider. Admissibility is re-asserted at call time, not just at build."""
        self.validate()
        out = {}
        for comp, prov in self.providers.items():
            self.budget.require(*sorted(prov.requires))
            out[comp] = prov(ctx)
        return out

    # ── degradation ───────────────────────────────────────────────────────────────────────
    def degrade_to(self, parent: "Tier") -> "Tier":
        """Drop providers that need streams above the parent budget; take the parent's instead.

        This is what P3 means operationally: withholding a stream must reproduce the parent
        tier, not merely something close to it.
        """
        if parent.budget.id != (self.budget.parent or ""):
            raise bd.AdmissibilityError(
                f"{parent.budget.id} is not the declared parent of {self.budget.id} "
                f"(parent={self.budget.parent})")
        kept = {}
        for comp, prov in self.providers.items():
            if prov.requires <= parent.budget.admits:
                kept[comp] = prov
        for comp, prov in parent.providers.items():
            kept.setdefault(comp, prov)
            if comp in self.providers and not (self.providers[comp].requires
                                               <= parent.budget.admits):
                kept[comp] = prov          # parent's provider replaces the inadmissible one
        return Tier(budget=parent.budget, providers=kept)

    def streams_used(self) -> FrozenSet[str]:
        s: set[str] = set()
        for prov in self.providers.values():
            s |= set(prov.requires)
        return frozenset(s)


def imposed(component: str, value_key: str, name: str = "") -> ComponentProvider:
    """A component taken from a prior/construction — consumes no observational stream."""
    return ComponentProvider(
        component=component, requires=frozenset({bd.STATIC_GEO}),
        fn=lambda ctx, k=value_key: np.asarray(ctx[k], dtype=float),
        name=name or f"imposed:{component}",
    )
