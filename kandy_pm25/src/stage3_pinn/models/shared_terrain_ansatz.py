"""
shared_terrain_ansatz.py — SharedTerrainAnsatz: 6-scalar terrain-met ansatz.

Core hypothesis: PM2.5 concentration C can be decomposed as
    C(x,y,t) = C_prior(t) × F_eff(x,y,t) × [1 + α_corr · σ(NN(x,y,t))]

where
    F_eff(x,y,t) = 1 + F_valley(x,y) × F_met(x,y,t)

    F_valley(x,y) = α_valley · exp(−Δz(x,y) / H_trap)
        Δz   = elevation above local valley floor [m]  (from TPI/SVF npz)
        H_trap  ∈ [80, 500] m  — learnable e-folding height
        α_valley ∈ [0.5, 4.0] — learnable concentration enhancement

    F_met(x,y,t) = σ(−w_stab · BLH/BLH_ref) · σ(−w_wind · |wind|/u_ref)
        Terrain trapping strong when: BLH is LOW (stable) AND wind is CALM
        w_stab, w_wind ∈ [0, ∞) — learnable sensitivities
        BLH_ref ∈ [200, 3000] m — learnable reference BLH
        u_ref   ∈ [0.5, 15] m/s — learnable reference wind speed

These 6 scalars (H_trap, α_valley, w_stab, w_wind, BLH_ref, u_ref) are SHARED
across all source cities. They encode the physical terrain-PM2.5 relationship.
At Kandy, these scalars are FROZEN; only the NN backbone is fine-tuned.

Literature: Whiteman 2014 (H_trap 150-300m), Chemel 2015 (α_valley 1.5-3),
            Toro 2023 (F_met BLH+wind coupling).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SharedTerrainAnsatz(nn.Module):
    """
    6 learnable scalars encoding terrain-driven PM2.5 spatial structure.

    Designed to be trained jointly across Medellín, Chiang Mai, Kathmandu,
    then frozen for zero-shot Kandy prediction.

    Args:
        freeze: if True, all parameters are frozen (for Kandy fine-tuning stage)
    """

    def __init__(self, freeze: bool = False):
        super().__init__()
        # Unconstrained parameters; physical ranges enforced via properties
        self._log_H_trap   = nn.Parameter(torch.tensor(0.0))   # → H_trap  [80, 500] m
        self._log_alpha_v  = nn.Parameter(torch.tensor(0.0))   # → α_valley [0.5, 4.0]
        self._w_stab       = nn.Parameter(torch.tensor(1.0))   # BLH sensitivity ≥ 0
        self._w_wind       = nn.Parameter(torch.tensor(1.0))   # wind sensitivity ≥ 0
        self._log_BLH_ref  = nn.Parameter(torch.tensor(3.0))   # → BLH_ref [200, 3000] m
        self._log_u_ref    = nn.Parameter(torch.tensor(3.0))   # → u_ref   [0.5, 15] m/s

        if freeze:
            for p in self.parameters():
                p.requires_grad = False

    # ── Physical properties (bounded) ─────────────────────────────────────────

    @property
    def H_trap(self) -> torch.Tensor:
        """e-folding trapping height [80, 500] m."""
        return 80.0 + 420.0 * torch.sigmoid(self._log_H_trap)

    @property
    def alpha_valley(self) -> torch.Tensor:
        """Valley concentration enhancement [0.5, 4.0]."""
        return 0.5 + 3.5 * torch.sigmoid(self._log_alpha_v)

    @property
    def BLH_ref(self) -> torch.Tensor:
        """Reference BLH for stability sigmoid [200, 3000] m."""
        return 200.0 + 2800.0 * torch.sigmoid(self._log_BLH_ref)

    @property
    def u_ref(self) -> torch.Tensor:
        """Reference wind speed [0.5, 15.0] m/s."""
        return 0.5 + 14.5 * torch.sigmoid(self._log_u_ref)

    @property
    def w_stab(self) -> torch.Tensor:
        """BLH sensitivity (softplus to ensure non-negative)."""
        return F.softplus(self._w_stab)

    @property
    def w_wind(self) -> torch.Tensor:
        """Wind sensitivity (softplus to ensure non-negative)."""
        return F.softplus(self._w_wind)

    # ── Forward pass ──────────────────────────────────────────────────────────

    def forward(
        self,
        delta_z:    torch.Tensor,   # (N,) elevation above valley floor [m]
        wind_speed: torch.Tensor,   # (N,) |u10, v10| [m/s]
        blh:        torch.Tensor,   # (N,) boundary layer height [m]
    ) -> torch.Tensor:
        """
        Returns F_eff(x,y,t) = 1 + F_valley(x,y) × F_met(x,y,t)

        Inputs:
            delta_z    : (N,) — per-sample elevation above valley floor [m]
            wind_speed : (N,) — |wind| [m/s]
            blh        : (N,) — boundary layer height [m]

        Output:
            F_eff : (N,) — multiplicative concentration enhancement ≥ 1

        Convention:
            F_eff = 1   → no terrain effect (open plain, high BLH, strong wind)
            F_eff > 1   → terrain trapping active (valley floor, stable, calm)
        """
        # Tier 1: static spatial structure (elevation-driven)
        F_valley = self.alpha_valley * torch.exp(-delta_z / self.H_trap)

        # Tier 2: temporal modulation — trapping active when stable + calm
        # Both sigmoid arguments negative → high activation when BLH/wind is LOW
        stability   = torch.sigmoid(-self.w_stab * blh        / self.BLH_ref)
        ventilation = torch.sigmoid(-self.w_wind * wind_speed / self.u_ref)
        F_met = stability * ventilation

        return 1.0 + F_valley * F_met

    def diagnostics(self) -> dict:
        """Return current scalar values for logging."""
        return {
            "H_trap_m":    self.H_trap.item(),
            "alpha_valley": self.alpha_valley.item(),
            "w_stab":      self.w_stab.item(),
            "w_wind":      self.w_wind.item(),
            "BLH_ref_m":   self.BLH_ref.item(),
            "u_ref_ms":    self.u_ref.item(),
        }
