"""Modular grey-box decomposition: information budgets, observation model, constraints.

Implements docs/MODEL_SPECIFICATION.md. See that file for the formulation; this package is the
machinery the specification calls for and the current pipeline lacks.
"""
from . import budgets, constraints, observation, production, shrinkage, tiers  # noqa: F401

__all__ = ["budgets", "observation", "constraints", "shrinkage", "tiers", "production"]
