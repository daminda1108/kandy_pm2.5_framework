"""
curriculum.py — Curriculum learning schedule for Stage 3 PINN training.

λ weight schedule (§2.11 of RESEARCH_PROJECT_DESIGN.md):

Phase 1 (epochs 0–199, WARM-UP):
    λ_pde = 1.0, λ_data = 0.0, λ_bc = 1.0, λ_phys = 0.5
    Learn PDE structure before introducing data; prevents data from
    short-circuiting physics learning in the early epochs.

Phase 2 (epochs 200–499, MAIN TRAINING):
    λ_pde: cosine annealing from 1.0 → 0.5
    λ_data: linear ramp from 0.0 → 0.5
    λ_bc = 1.0 (held constant)
    λ_phys = 0.5 (held constant)

Phase 3 (epochs 500+, CONVERGENCE REFINEMENT):
    λ_pde = 0.5, λ_data = 1.0, λ_bc = 1.0, λ_phys = 0.2
    Data fidelity takes equal weight with physics; physics acts as regulariser.

Rationale: Starting with physics-only prevents the PINN from learning a
trivial mapping from inputs to Stage 1 values without discovering K and S.
"""

import logging
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import PINN_WARMUP_EPOCHS

log = logging.getLogger("curriculum")

# Phase boundaries
WARMUP_END        = PINN_WARMUP_EPOCHS
MAIN_TRAINING_END = 500

# Lambda targets
WARMUP_WEIGHTS    = {"pde": 1.0, "data": 0.0, "bc": 1.0, "phys": 0.5}
FINAL_WEIGHTS     = {"pde": 0.5, "data": 1.0, "bc": 1.0, "phys": 0.2}


@dataclass
class LambdaWeights:
    pde:  float = 1.0
    data: float = 0.0
    bc:   float = 1.0
    phys: float = 0.5

    def as_dict(self) -> Dict[str, float]:
        return {"pde": self.pde, "data": self.data, "bc": self.bc, "phys": self.phys}


class CurriculumScheduler:
    """
    Curriculum scheduler that returns PINN λ weights for a given epoch.

    Usage:
        scheduler = CurriculumScheduler(total_epochs=1000)
        for epoch in range(1000):
            lambdas = scheduler.step(epoch)
            L_total = total_loss(..., **lambdas.as_dict())
    """

    def __init__(self, total_epochs: int = 1000, warmup_end: int = WARMUP_END,
                 main_end: int = MAIN_TRAINING_END):
        self.total   = total_epochs
        self.warmup  = warmup_end
        self.main    = main_end

    def _cosine_anneal(self, start: float, end: float, epoch: int, t0: int, t1: int) -> float:
        """Cosine annealing from start → end over [t0, t1]."""
        if epoch <= t0:
            return start
        if epoch >= t1:
            return end
        progress = (epoch - t0) / (t1 - t0)
        return end + 0.5 * (start - end) * (1 + math.cos(math.pi * progress))

    def _linear_ramp(self, start: float, end: float, epoch: int, t0: int, t1: int) -> float:
        """Linear ramp from start → end over [t0, t1]."""
        if epoch <= t0:
            return start
        if epoch >= t1:
            return end
        return start + (end - start) * (epoch - t0) / (t1 - t0)

    def step(self, epoch: int) -> LambdaWeights:
        """Return λ weights for current epoch."""
        if epoch < self.warmup:
            return LambdaWeights(**{k: v for k, v in WARMUP_WEIGHTS.items()
                                    if k in LambdaWeights.__dataclass_fields__})

        elif epoch < self.main:
            return LambdaWeights(
                pde  = self._cosine_anneal(1.0, 0.5, epoch, self.warmup, self.main),
                data = self._linear_ramp(0.0, 0.5, epoch, self.warmup, self.main),
                bc   = 1.0,
                phys = 0.5,
            )

        else:
            return LambdaWeights(pde=0.5, data=1.0, bc=1.0, phys=0.2)

    def log_schedule(self, every: int = 100) -> None:
        """Print lambda schedule summary for key epochs."""
        log.info("═══ CURRICULUM SCHEDULE ═══")
        for epoch in range(0, self.total + 1, every):
            w = self.step(epoch)
            log.info(f"  epoch {epoch:4d}: λ_pde={w.pde:.2f}  λ_data={w.data:.2f}  "
                     f"λ_bc={w.bc:.2f}  λ_phys={w.phys:.2f}")
