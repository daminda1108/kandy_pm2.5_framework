"""The four hard constraints (MODEL_SPECIFICATION.md section 3), as assertions.

These are never fitted and never violated. They are checked here so that any assembly path --
the current builders, the differentiable model, or a future tier -- can be held to the same
contract by calling one function.
"""
from __future__ import annotations

import numpy as np

TOL_T_LOCK = 0.05      # ug/m3, the G1 gate
TOL_UNIT_MEAN = 1e-6


class ConstraintViolation(AssertionError):
    """A hard constraint was violated. This is never acceptable."""


def check_conservation(field: np.ndarray, T: np.ndarray, tol: float = TOL_T_LOCK) -> float:
    """C1 -- the basin mean of the field must equal the anchor at every hour."""
    drift = np.abs(np.nanmean(field, axis=1) - np.asarray(T, dtype=float))
    worst = float(np.nanmax(drift))
    if worst > tol:
        raise ConstraintViolation(f"C1 conservation: max |basin mean - T| = {worst:.4g} > {tol}")
    return worst


def check_coherence(B: np.ndarray, T: np.ndarray, day_index: np.ndarray,
                    f_min: float = 0.02) -> int:
    """C2 -- B may not exceed (1 - f_min) x the day's minimum total."""
    B = np.asarray(B, float); T = np.asarray(T, float)
    n_bad = 0
    for d in np.unique(day_index):
        m = day_index == d
        cap = (1.0 - f_min) * np.nanmin(T[m])
        n_bad += int(np.sum(B[m] > cap + 1e-9))
    if n_bad:
        raise ConstraintViolation(f"C2 coherence: {n_bad} hours with B above the daily cap")
    return n_bad


def check_nonneg_amplitude(A: np.ndarray) -> None:
    """C3 -- the local increment amplitude is non-negative."""
    if np.nanmin(np.asarray(A, float)) < -1e-9:
        raise ConstraintViolation("C3: negative increment amplitude")


def check_unit_mean(P: np.ndarray, tol: float = TOL_UNIT_MEAN) -> float:
    """C4 -- the local pattern has unit spatial mean at every hour."""
    dev = np.abs(np.nanmean(np.asarray(P, float), axis=1) - 1.0)
    worst = float(np.nanmax(dev))
    if worst > tol:
        raise ConstraintViolation(f"C4 unit mean: max |mean(P) - 1| = {worst:.3g} > {tol}")
    return worst


def check_all(field, T, P, A=None, B=None, day_index=None, f_min: float = 0.02) -> dict:
    """Run every applicable constraint. Returns the measured margins."""
    out = {"C1_drift": check_conservation(field, T), "C4_unit_mean": check_unit_mean(P)}
    if A is not None:
        check_nonneg_amplitude(A); out["C3"] = "ok"
    if B is not None and day_index is not None:
        out["C2_violations"] = check_coherence(B, T, day_index, f_min)
    return out
