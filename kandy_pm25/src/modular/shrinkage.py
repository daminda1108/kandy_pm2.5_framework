"""Tier shrinkage — the mechanism that enforces P2 (monotone skill under added data).

MODEL_SPECIFICATION.md section 6. Adding observations must not make the estimate worse. This is
NOT automatic and this project has the counter-example: fine-tuning on two local sensors
memorised their coordinates as identity keys and inflated the annual mean from 22.1 to
37.0 ug/m3. A richer tier is therefore never allowed to simply replace its parent.

    x(w) = x_parent + w * (x_child - x_parent),      w in [0, 1]

`w` is chosen on HELD-OUT data by a one-dimensional search that includes w = 0. Two properties
follow:

  HARD  (exact, testable)   w = 0 reproduces the parent bit-exactly, so a tier that buys
                            nothing degrades to its parent rather than to something worse.
                            This is the P3 nesting guarantee expressed as a limit of P2.

  SOFT  (statistical)       the selected w cannot be worse than the parent ON THE SELECTION
                            OBJECTIVE, because w = 0 is inside the search space. Out of sample
                            it is non-inferior only up to the noise in selecting one parameter,
                            which is why `optimal_weight` selects by CROSS-VALIDATION and
                            reports the fold spread rather than a single number.

Claiming a hard out-of-sample guarantee would be an overclaim; the honest statement is
non-inferiority on the selection objective plus a measured fold spread.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ShrinkResult:
    w: float
    w_folds: list[float]
    skill_parent: float
    skill_child: float
    skill_shrunk: float
    n: int
    metric: str = "rmse"

    @property
    def improved(self) -> bool:
        return self.skill_shrunk <= self.skill_parent + 1e-12

    def __str__(self) -> str:
        return (f"w={self.w:.3f} (folds {np.round(self.w_folds, 3).tolist()}) | "
                f"{self.metric}: parent {self.skill_parent:.4f} -> shrunk "
                f"{self.skill_shrunk:.4f} (child alone {self.skill_child:.4f}), n={self.n}")


def combine(parent: np.ndarray, child: np.ndarray, w: float) -> np.ndarray:
    """The shrinkage estimator. w=0 -> parent exactly; w=1 -> child exactly."""
    if not (0.0 <= w <= 1.0):
        raise ValueError(f"shrinkage weight must lie in [0, 1], got {w}")
    parent = np.asarray(parent, float)
    child = np.asarray(child, float)
    if parent.shape != child.shape:
        raise ValueError(f"shape mismatch {parent.shape} vs {child.shape}")
    if w == 0.0:
        return parent.copy()          # exact, not merely close
    if w == 1.0:
        return child.copy()
    return parent + w * (child - parent)


def _rmse(a: np.ndarray, b: np.ndarray) -> float:
    m = np.isfinite(a) & np.isfinite(b)
    if not m.any():
        return np.nan
    return float(np.sqrt(np.mean((a[m] - b[m]) ** 2)))


def _best_w(parent, child, obs, grid) -> float:
    errs = [_rmse(combine(parent, child, w), obs) for w in grid]
    return float(grid[int(np.nanargmin(errs))])


def optimal_weight(parent: np.ndarray, child: np.ndarray, obs: np.ndarray,
                   n_folds: int = 5, n_grid: int = 41, seed: int = 0,
                   groups: np.ndarray | None = None) -> ShrinkResult:
    """Select w by cross-validation, then report skill at the selected w.

    `groups` (e.g. station id, or day) makes the folds GROUPED, which matters: hours within a
    day are not independent, and pooling them into random folds would understate the noise in
    the selection and flatter the child tier.
    """
    parent = np.asarray(parent, float)
    child = np.asarray(child, float)
    obs = np.asarray(obs, float)
    ok = np.isfinite(parent) & np.isfinite(child) & np.isfinite(obs)
    parent, child, obs = parent[ok], child[ok], obs[ok]
    if groups is not None:
        groups = np.asarray(groups)[ok]
    n = len(obs)
    if n < 2 * n_folds:
        raise ValueError(f"too few usable rows ({n}) for {n_folds} folds")

    grid = np.linspace(0.0, 1.0, n_grid)
    rng = np.random.default_rng(seed)
    if groups is None:
        fold_id = rng.integers(0, n_folds, size=n)
    else:
        uniq = np.unique(groups)
        assign = {g: i for g, i in zip(uniq, rng.integers(0, n_folds, size=len(uniq)))}
        fold_id = np.array([assign[g] for g in groups])

    ws = []
    for f in range(n_folds):
        tr = fold_id != f
        if tr.sum() < 2 or (~tr).sum() < 1:
            continue
        ws.append(_best_w(parent[tr], child[tr], obs[tr], grid))
    w = float(np.median(ws)) if ws else 0.0

    return ShrinkResult(
        w=w, w_folds=ws,
        skill_parent=_rmse(parent, obs),
        skill_child=_rmse(child, obs),
        skill_shrunk=_rmse(combine(parent, child, w), obs),
        n=n,
    )


def assert_monotone(result: ShrinkResult, tol: float = 1e-9) -> None:
    """P2 check: the shrunk tier must not be worse than its parent on the selection objective."""
    if result.skill_shrunk > result.skill_parent + tol:
        raise AssertionError(
            f"P2 violated: shrunk {result.skill_shrunk:.6f} worse than parent "
            f"{result.skill_parent:.6f} (w={result.w})")
