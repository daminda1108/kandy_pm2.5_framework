"""
fourier_pinn_v3.py — FourierPINN v3 — redesigned for Kandy Stage 3.

Changes from v2:
  1. Separate 2D multi-scale SpatialEmbedding (σ_lo=1.0, σ_hi=3.0) + 1D TemporalEncoding.
     Joint xyt Fourier embedding removed: steady-state PDE has no physical x-t coupling.
  2. BLH and elevation enter the trunk directly (517-dim input) — C is directly modulated
     by BLH and the trunk must see it to predict C without relying on PDE coupling alone.
  3. Wider trunk first layer (256), standard 2-layer ResBlocks, 256→128 bottleneck.
  4. Factored DiffusionSubNetV3: K_base(BLH, t) × K_aniso(x, y, elev).
     K_base captures the dominant physical driver (BLH-modulated scale);
     K_aniso captures terrain-induced spatial modulation. Reduces K from ~22,500
     spatial DOF to ~100 identifiable parameters.
  5. K_MAX = 150 m²/s (tighter than v2; Pe=300 at u=3m/s over 15km keeps advection relevant).
  6. AlphaNet source term — 2-input diurnal only (day-of-week removed: Stage 3 target
     is daily-mean PM2.5 and the 7-day cycle averages out).
  7. Road kernel (B4): already wired in v2; preserved exactly in v3 with same grid_sample logic.

Transfer interface (v8 Stage 2 backbone → v3 Stage 3):
  - head_C (128→1): CAN transfer (same shape)
  - trunk layers: INCOMPATIBLE (512→128 in v2 vs 517→256 in v3) — reinitialise
  - KBaseNet: ATTEMPT mapping from v2 DiffSubNet fc1/fc2 (will likely fail shape check)
  - KAnisoNet: REINITIALISE (Kandy terrain ≠ Medellín)
  - AlphaNet: REINITIALISE (new source parameterisation)

Stage 3 usage:
    model = FourierPINNV3()
    C, (Kx, Ky, S) = model(xyt, blh=blh_norm, elev=elev_norm)
    # xyt: (N,3) [x_norm ∈ [-1,1], y_norm ∈ [-1,1], t_norm ∈ [0,1] (=h/24)]
    # blh_norm = BLH_m / 2000.0, elev_norm ∈ [0,1]

Upgrade history:
  v1 (2026-03-01): Shared trunk → 4 separate linear heads.
  v2 (2026-03-01): DiffusionSubNet + SourceSubNet + road kernel (B4 wired).
  v3 (2026-03-10): Separate embeddings, BLH in trunk, factored K, tighter K_MAX.
"""

import logging
import math
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    LOG_FORMAT, LOG_DATEFMT,
    PINN_INPUT_DIR,
    K_MIN_MS2,           # 1.0 m²/s  (floor for K_base)
    PINN_BLH_NORM_SCALE, # 2000.0 m  (blh_norm = BLH_m / 2000.0)
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("fourier_pinn_v3")

# ── v3-specific constants (not overriding config defaults) ────────────────────
K_MAX_V3       = 150.0   # m²/s — tighter than v2 (Pe=300 at u=3m/s, L=15km)
K_RATIO_MAX    = 5.0     # max gx or gy (anisotropy factor, dimensionless)
_SPATIAL_M_LO  = 128     # Fourier modes, large-scale (σ=1.0, ~km features)
_SPATIAL_M_HI  = 128     # Fourier modes, fine-scale  (σ=3.0, ~100m features)
_SPATIAL_SIGMA_LO = 1.0  # N(0, σ²) for B_lo — 1 cycle per normalised unit = ~km
_SPATIAL_SIGMA_HI = 3.0  # N(0, σ²) for B_hi — 3 cycles per norm unit = ~100m


# ═══════════════════════════════════════════════════════════════════════════════
# EMBEDDING — separate spatial (multi-scale 2D) + temporal (1D cyclic)
# ═══════════════════════════════════════════════════════════════════════════════

class SpatialEmbedding:
    """
    Multi-scale 2D Fourier embedding for (x, y) coordinates only.

    Two frequency banks:
      B_lo ~ N(0, σ_lo²): 128 modes, large-scale (~km) spatial features
      B_hi ~ N(0, σ_hi²): 128 modes, fine-scale  (~100m) spatial features

    Output: [sin(2π x·B_lo^T), cos(2π x·B_lo^T),
             sin(2π x·B_hi^T), cos(2π x·B_hi^T)] ∈ ℝ^512

    B matrices are fixed (non-trained) and deterministic from seed=42.
    Multi-scale σ provides adequate frequency coverage from valley-scale
    gradients (~km) down to road-corridor-scale variability (~100m).

    Physical motivation: separating x,y from t avoids spurious x-t frequency
    coupling that the steady-state PDE does not contain.
    """

    def __init__(self, m_lo: int = _SPATIAL_M_LO, m_hi: int = _SPATIAL_M_HI,
                 sigma_lo: float = _SPATIAL_SIGMA_LO, sigma_hi: float = _SPATIAL_SIGMA_HI,
                 seed: int = 42):
        rng = np.random.default_rng(seed)
        self.B_lo = rng.normal(0, sigma_lo, size=(m_lo, 2)).astype(np.float32)
        self.B_hi = rng.normal(0, sigma_hi, size=(m_hi, 2)).astype(np.float32)
        self.out_dim = 4 * m_lo  # = 4 × 128 = 512 (sin+cos for each bank)

    def embed(self, xy: "torch.Tensor") -> "torch.Tensor":
        """
        Args:
            xy : (N, 2) [x_norm, y_norm] tensor, both ∈ [-1, 1]
        Returns:
            (N, 512) multi-scale Fourier features
        """
        import torch
        B_lo = torch.tensor(self.B_lo, dtype=xy.dtype, device=xy.device)
        B_hi = torch.tensor(self.B_hi, dtype=xy.dtype, device=xy.device)
        pi2  = 2.0 * math.pi
        proj_lo = pi2 * (xy @ B_lo.T)   # (N, 128)
        proj_hi = pi2 * (xy @ B_hi.T)   # (N, 128)
        return torch.cat([
            torch.sin(proj_lo), torch.cos(proj_lo),
            torch.sin(proj_hi), torch.cos(proj_hi),
        ], dim=-1)                        # (N, 512)


class TemporalEncoding:
    """
    Lightweight 1D cyclic encoding for t_norm ∈ [0, 1].

    Output: [sin(2π·t), cos(2π·t), t] ∈ ℝ³

    No learned parameters. Captures periodicity (t represents h/24 in Stage 3)
    without introducing spurious x-t frequency coupling in the Fourier embedding.
    The raw t value is included to allow the network to distinguish phase within
    the cycle (e.g., pre-dawn vs post-midnight).
    """

    out_dim: int = 3

    @staticmethod
    def encode(t: "torch.Tensor") -> "torch.Tensor":
        """
        Args:
            t : (N, 1) normalised time ∈ [0, 1]
        Returns:
            (N, 3) cyclic encoding
        """
        import torch
        pi2 = 2.0 * math.pi
        return torch.cat([torch.sin(pi2 * t), torch.cos(pi2 * t), t], dim=-1)


# ═══════════════════════════════════════════════════════════════════════════════
# TRUNK NETWORK (v3)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_trunk_v3(in_dim: int = 517, hidden: int = 256, bottleneck: int = 128):
    """
    Build TrunkNetV3: wider first layer + standard 2-layer ResBlocks + bottleneck.

    Architecture:
        Linear(in_dim → hidden) → Tanh
        ResBlock(hidden) × 2
        Linear(hidden → bottleneck) → Tanh
    Output: bottleneck-dim feature vector

    ResBlock: Linear(h→h) → Tanh → Linear(h→h) + add_input → Tanh
    (Standard residual: skip connection at block boundary, Tanh after add)

    Motivation vs v2 asymmetric skip: standard pre-activation residual
    ensures unobstructed gradient flow through every layer. v2's skip
    at odd layers only left layers 0, 2, 4 without gradient shortcuts.
    """
    try:
        import torch.nn as nn
    except ImportError:
        raise ImportError("PyTorch required")

    class _ResBlock(nn.Module):
        def __init__(self, dim: int):
            super().__init__()
            self.fc1 = nn.Linear(dim, dim)
            self.fc2 = nn.Linear(dim, dim)
            self.act = nn.Tanh()
            nn.init.xavier_normal_(self.fc1.weight); nn.init.zeros_(self.fc1.bias)
            nn.init.xavier_normal_(self.fc2.weight); nn.init.zeros_(self.fc2.bias)

        def forward(self, x):
            return self.act(self.fc2(self.act(self.fc1(x))) + x)

    class TrunkNetV3(nn.Module):
        def __init__(self):
            super().__init__()
            self.proj       = nn.Linear(in_dim, hidden)
            self.blocks     = nn.ModuleList([_ResBlock(hidden), _ResBlock(hidden)])
            self.bottleneck = nn.Linear(hidden, bottleneck)
            self.act        = nn.Tanh()
            nn.init.xavier_normal_(self.proj.weight);       nn.init.zeros_(self.proj.bias)
            nn.init.xavier_normal_(self.bottleneck.weight); nn.init.zeros_(self.bottleneck.bias)

        def forward(self, x):
            h = self.act(self.proj(x))
            for block in self.blocks:
                h = block(h)
            return self.act(self.bottleneck(h))

    return TrunkNetV3()


# ═══════════════════════════════════════════════════════════════════════════════
# DIFFUSION SUBNET v3 — factored K = K_base × K_aniso
# ═══════════════════════════════════════════════════════════════════════════════

def _build_k_base_net():
    """
    BLH-driven diffusivity scale. Universal physics — transferable Stage 2→3.

    Inputs : [blh_norm, t_norm]  (2-dim)
    Arch   : Linear(2→16) → Tanh → Linear(16→1) → Softplus + K_MIN
    Output : K_base ∈ [K_MIN, ~K_MAX_V3] m²/s
    Params : (2×16+16) + (16×1+1) = 48 + 17 = 65

    Physical motivation: daytime convective BL (BLH~1500m → blh_norm~0.75)
    gives K~50–150 m²/s; nocturnal stable BL (BLH~100m → blh_norm~0.05)
    gives K~1–10 m²/s (Stull 1988, Ch. 1). This 1–2 order of magnitude range
    is the dominant driver of K and is trivially learnable from a 2-input MLP.
    Capturing it here frees K_aniso to learn spatial terrain modulation only.

    Bias init: softplus(b) + K_MIN ≈ 10 m²/s → b = log(exp(10-K_MIN)-1).
    """
    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
    except ImportError:
        raise ImportError("PyTorch required")

    k_min = K_MIN_MS2

    class _KBaseNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(2, 16)
            self.fc2 = nn.Linear(16, 1)
            nn.init.xavier_normal_(self.fc1.weight); nn.init.zeros_(self.fc1.bias)
            nn.init.xavier_normal_(self.fc2.weight)
            # init so K_base ≈ 10 m²/s initially
            bias_init = math.log(math.exp(10.0 - k_min) - 1.0)
            nn.init.constant_(self.fc2.bias, bias_init)

        def forward(self, blh_n: "torch.Tensor", t_n: "torch.Tensor") -> "torch.Tensor":
            """
            Args:
                blh_n : (N, 1) normalised BLH = BLH_m / 2000.0
                t_n   : (N, 1) normalised time ∈ [0, 1]
            Returns:
                K_base : (N, 1) ∈ [K_MIN, ~150] m²/s
            """
            inp = torch.cat([blh_n, t_n], dim=1)
            h   = torch.tanh(self.fc1(inp))
            return F.softplus(self.fc2(h)) + k_min

    return _KBaseNet()


def _build_k_aniso_net():
    """
    Terrain-modulated anisotropy factors. City-specific — reinitialise Stage 2→3.

    Inputs : [x_norm, y_norm, elev_norm]  (3-dim)
    Arch   : Linear(3→32) → Tanh → Linear(32→32) → Tanh → Linear(32→2)
             → Sigmoid × (K_RATIO_MAX − 1) + 1
    Output : [gx, gy] ∈ [1.0, K_RATIO_MAX]  (spatial modulation, dimensionless)
    Params : (3×32+32) + (32×32+32) + (32×2+2) = 128 + 1056 + 66 = 1,250

    Physical motivation: terrain channelling enhances diffusivity along the NE-SW
    valley axis (Kandy), while ridgelines suppress cross-ridge transport.
    Sigmoid output enforces gx, gy ∈ [1, 5] — K is always ≥ K_base (terrain
    cannot reduce diffusivity below the BLH-driven scale).
    Valley axis anisotropy (gx ≠ gy) is NOT hardcoded; it emerges from the PDE
    residual given the DEM-driven wind heterogeneity field.
    """
    try:
        import torch.nn as nn
        import torch.nn.functional as F
    except ImportError:
        raise ImportError("PyTorch required")

    ratio_max = K_RATIO_MAX

    class _KAnisoNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(3, 32)
            self.fc2 = nn.Linear(32, 32)
            self.fc3 = nn.Linear(32, 2)
            for m in self.modules():
                if isinstance(m, nn.Linear):
                    nn.init.xavier_normal_(m.weight)
                    nn.init.zeros_(m.bias)

        def forward(self, x_n: "torch.Tensor",
                    y_n: "torch.Tensor",
                    elev_n: "torch.Tensor") -> Tuple["torch.Tensor", "torch.Tensor"]:
            """
            Args:
                x_n    : (N, 1) normalised longitude ∈ [-1, 1]
                y_n    : (N, 1) normalised latitude  ∈ [-1, 1]
                elev_n : (N, 1) normalised elevation ∈ [0, 1]
            Returns:
                gx : (N, 1) x-direction anisotropy factor ∈ [1, K_RATIO_MAX]
                gy : (N, 1) y-direction anisotropy factor ∈ [1, K_RATIO_MAX]
            """
            import torch
            inp = torch.cat([x_n, y_n, elev_n], dim=1)
            h   = torch.tanh(self.fc1(inp))
            h   = torch.tanh(self.fc2(h))
            out = self.fc3(h)                                 # (N, 2) unconstrained
            # Sigmoid maps to (0,1), scale to [1, K_RATIO_MAX]
            gx = torch.sigmoid(out[:, 0:1]) * (ratio_max - 1.0) + 1.0
            gy = torch.sigmoid(out[:, 1:2]) * (ratio_max - 1.0) + 1.0
            return gx, gy

    return _KAnisoNet()


class DiffusionSubNetV3:
    """
    Factored anisotropic diffusivity:
        Kx = K_base(blh_norm, t_norm) × gx(x_norm, y_norm, elev_norm)
        Ky = K_base(blh_norm, t_norm) × gy(x_norm, y_norm, elev_norm)

    K_MIN  = 1.0 m²/s     (enforced by Softplus + K_MIN in K_base)
    K_MAX  = 150.0 m²/s   (soft bound penalty; Pe=300 at u=3m/s over 15km)
    K_RATIO_MAX = 5.0      (maximum anisotropy ratio)

    The factored form separates the two physical mechanisms:
      - K_base: BLH-driven diffusivity scale (universal, transferable)
      - K_aniso: terrain modulation (city-specific, reinitialise at Stage 3)

    bound_penalty(Kx, Ky): soft quadratic penalty for K > K_MAX.
    K_MIN is exactly enforced by the architecture; only upper bound needs penalty.
    """

    def __new__(cls):
        try:
            import torch
            import torch.nn as nn
            import torch.nn.functional as F
        except ImportError:
            raise ImportError("PyTorch required")

        k_max = K_MAX_V3

        class _DiffV3(nn.Module):
            def __init__(self):
                super().__init__()
                self.k_base  = _build_k_base_net()
                self.k_aniso = _build_k_aniso_net()

            def forward(self,
                        x_n: "torch.Tensor", y_n: "torch.Tensor",
                        t_n: "torch.Tensor", blh_n: "torch.Tensor",
                        elev_n: "torch.Tensor") -> Tuple["torch.Tensor", "torch.Tensor"]:
                """
                Args:
                    x_n, y_n, t_n : (N, 1) normalised spatial + time coords
                    blh_n          : (N, 1) BLH / 2000.0
                    elev_n         : (N, 1) normalised elevation ∈ [0,1]; 0.5 if unavailable
                Returns:
                    Kx, Ky : (N, 1) diffusivity [m²/s] each ∈ [K_MIN, K_MAX × K_RATIO_MAX]
                """
                K_base    = self.k_base(blh_n, t_n)          # (N, 1)
                gx, gy    = self.k_aniso(x_n, y_n, elev_n)   # (N, 1) each
                return K_base * gx, K_base * gy

            def bound_penalty(self,
                               Kx: "torch.Tensor",
                               Ky: "torch.Tensor") -> "torch.Tensor":
                """Soft quadratic penalty for K > K_MAX (upper bound only)."""
                high = F.relu(Kx - k_max) ** 2 + F.relu(Ky - k_max) ** 2
                return torch.mean(high)

        return _DiffV3()


# ═══════════════════════════════════════════════════════════════════════════════
# ALPHA NET — diurnal source amplitude (Stage 3)
# ═══════════════════════════════════════════════════════════════════════════════

class AlphaNet:
    """
    Scalar diurnal emission amplitude. Stage 3 only.

    Inputs : [sin(2π·h/24), cos(2π·h/24)]  (2-dim)
    Arch   : Linear(2→16) → Tanh → Linear(16→1) → Softplus
    Output : α(t) ≥ 0  (temporal emission amplitude)
    Params : (2×16+16) + (16×1+1) = 48 + 17 = 65

    Day-of-week removed vs v2 SourceSubNet: Stage 3 target is daily-mean PM2.5;
    the 7-day cycle averages to constant over a calendar day.

    The full source term is: S(x,y,t) = α(t) × R(x,y)
    where R(x,y) is the fixed OSM road kernel (registered buffer in FourierPINNV3).

    t_max_hours is a non-trainable buffer (set to 24.0 for Stage 3 quasi-steady-state).
    """

    def __new__(cls, t_max: float = 24.0):
        try:
            import torch
            import torch.nn as nn
            import torch.nn.functional as F
        except ImportError:
            raise ImportError("PyTorch required")

        t_max_val = float(t_max)

        class _Alpha(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc1 = nn.Linear(2, 16)
                self.fc2 = nn.Linear(16, 1)
                nn.init.xavier_normal_(self.fc1.weight); nn.init.zeros_(self.fc1.bias)
                nn.init.xavier_normal_(self.fc2.weight); nn.init.zeros_(self.fc2.bias)
                self.register_buffer("t_max_hours", torch.tensor(t_max_val, dtype=torch.float32))

            def forward(self, t_n: "torch.Tensor") -> "torch.Tensor":
                """
                Args:
                    t_n : (N, 1) normalised time ∈ [0, 1] (= h/24 in Stage 3)
                Returns:
                    alpha : (N, 1) emission amplitude ≥ 0
                """
                h_day  = (t_n * self.t_max_hours) % 24.0     # hour-of-day ∈ [0, 24)
                pi2    = 2.0 * math.pi
                sin_h  = torch.sin(pi2 * h_day / 24.0)       # (N, 1)
                cos_h  = torch.cos(pi2 * h_day / 24.0)       # (N, 1)
                inp    = torch.cat([sin_h, cos_h], dim=1)    # (N, 2)
                h_feat = torch.tanh(self.fc1(inp))            # (N, 16)
                return F.softplus(self.fc2(h_feat))           # (N, 1), α ≥ 0

        return _Alpha()


# ═══════════════════════════════════════════════════════════════════════════════
# FOURIER PINN V3  (public interface)
# ═══════════════════════════════════════════════════════════════════════════════

class FourierPINNV3:
    """
    FourierPINN v3 — redesigned for Kandy Stage 3.

    forward(xyt, blh=None, elev=None) → C (N,1), (Kx (N,1), Ky (N,1), S (N,1))

    All outputs physically constrained:
      C ≥ 0 (Softplus on head_C)
      Kx, Ky ≥ K_MIN = 1.0 m²/s (enforced by architecture)
      S ≥ 0 (α ≥ 0 × R ≥ 0)
    """

    def __new__(cls, road_kernel_path=None):
        return _FourierPINNV3Module(road_kernel_path=road_kernel_path)


class _FourierPINNV3Module:
    def __new__(cls, road_kernel_path=None):
        try:
            import torch
            import torch.nn as nn
            import torch.nn.functional as F
        except ImportError:
            raise ImportError("PyTorch not installed.")

        if road_kernel_path is None:
            road_kernel_path = PINN_INPUT_DIR / "kandy_road_kernel_100m.npz"

        spatial_emb  = SpatialEmbedding()
        trunk_in_dim = spatial_emb.out_dim + TemporalEncoding.out_dim + 2  # 512+3+1+1=517

        class Module(nn.Module):
            def __init__(self):
                super().__init__()
                # Embedding components (no learned params)
                self.spatial_emb = spatial_emb

                # Trunk network (BLH and elev enter here directly)
                self.trunk  = _build_trunk_v3(in_dim=trunk_in_dim, hidden=256, bottleneck=128)
                self.head_C = nn.Linear(128, 1)
                nn.init.xavier_uniform_(self.head_C.weight)
                nn.init.zeros_(self.head_C.bias)

                # DiffusionSubNet v3 (factored K_base × K_aniso)
                self.diffusion_subnet = DiffusionSubNetV3()

                # AlphaNet source term
                self.alpha_net = AlphaNet(t_max=24.0)

                # Road kernel R(x,y) — B4: fixed spatial emission pattern
                _rk_loaded = False
                try:
                    _rk_data   = np.load(str(road_kernel_path))
                    _rk        = torch.tensor(_rk_data["R"], dtype=torch.float32)
                    _rk_loaded = True
                    log.info(
                        f"[v3] Road kernel loaded: shape={_rk.shape}, "
                        f"non-zero={float((_rk > 0.01).sum()) / _rk.numel() * 100:.1f}% "
                        f"(K-S degeneracy broken)"
                    )
                except Exception as exc:
                    _rk = torch.ones(150, 150, dtype=torch.float32)
                    log.warning(
                        f"[v3] Road kernel not found ({exc}) — uniform R=1 fallback. "
                        "K-S degeneracy NOT broken."
                    )
                self.register_buffer("road_kernel", _rk)
                self._road_kernel_loaded = _rk_loaded

            def _interp_road_kernel(self,
                                    x_n: "torch.Tensor",
                                    y_n: "torch.Tensor") -> "torch.Tensor":
                """
                Bilinear-interpolate R(x,y) from (150×150) buffer to N arbitrary points.
                Same grid_sample logic as v2 (align_corners=True, padding_mode='border').
                x_n ∈ [-1,1] → W/lon direction, y_n ∈ [-1,1] → H/lat direction.
                """
                grid = torch.stack([x_n.squeeze(-1), y_n.squeeze(-1)], dim=-1)   # (N, 2)
                grid = grid.unsqueeze(0).unsqueeze(2)                              # (1, N, 1, 2)
                kernel = self.road_kernel.unsqueeze(0).unsqueeze(0)               # (1, 1, 150, 150)
                R_interp = F.grid_sample(
                    kernel, grid,
                    mode='bilinear', padding_mode='border', align_corners=True,
                )                                                                  # (1, 1, N, 1)
                return R_interp[0, 0, :, 0].unsqueeze(-1)                         # (N, 1)

            def forward(self,
                        xyt:  "torch.Tensor",
                        blh:  Optional["torch.Tensor"] = None,
                        elev: Optional["torch.Tensor"] = None,
                        ) -> Tuple["torch.Tensor", Tuple]:
                """
                Args:
                    xyt  : (N, 3) [x_norm ∈ [-1,1], y_norm ∈ [-1,1], t_norm ∈ [0,1]]
                    blh  : (N, 1) BLH_m / 2000.0 ∈ [0, 1]; default 0.5
                    elev : (N, 1) normalised elevation ∈ [0, 1]; default 0.5
                Returns:
                    C        : (N, 1) PM2.5 concentration [µg/m³]
                    Kx, Ky   : (N, 1) anisotropic diffusivity [m²/s]
                    S        : (N, 1) source term = α(t) × R(x,y) [µg/m³/s]
                """
                N, device = xyt.shape[0], xyt.device
                if blh  is None: blh  = torch.full((N, 1), 0.5, dtype=xyt.dtype, device=device)
                if elev is None: elev = torch.full((N, 1), 0.5, dtype=xyt.dtype, device=device)

                x_n = xyt[:, 0:1]
                y_n = xyt[:, 1:2]
                t_n = xyt[:, 2:3]

                # Trunk: separate spatial + temporal encodings + BLH + elev
                xy_emb   = self.spatial_emb.embed(xyt[:, 0:2])   # (N, 512)
                t_enc    = TemporalEncoding.encode(t_n)           # (N, 3)
                trunk_in = torch.cat([xy_emb, t_enc, blh, elev], dim=1)  # (N, 517)
                feat = self.trunk(trunk_in)                               # (N, 128)
                C    = F.softplus(self.head_C(feat))                      # (N, 1)

                # Factored K: K_base(BLH, t) × K_aniso(x, y, elev)
                Kx, Ky = self.diffusion_subnet(x_n, y_n, t_n, blh, elev) # (N,1) each

                # Source: α(t) × R(x,y)
                alpha    = self.alpha_net(t_n)                            # (N, 1)
                R_interp = self._interp_road_kernel(x_n, y_n)            # (N, 1)
                S        = alpha * R_interp                               # (N, 1)

                return C, (Kx, Ky, S)

            def count_parameters(self) -> int:
                return sum(p.numel() for p in self.parameters() if p.requires_grad)

            def parameter_breakdown(self) -> dict:
                def _c(m): return sum(p.numel() for p in m.parameters() if p.requires_grad)
                return {
                    "trunk":                 _c(self.trunk),
                    "head_C":                _c(self.head_C),
                    "diffusion_subnet":      _c(self.diffusion_subnet),
                    "  k_base":              _c(self.diffusion_subnet.k_base),
                    "  k_aniso":             _c(self.diffusion_subnet.k_aniso),
                    "alpha_net":             _c(self.alpha_net),
                    "total":                 self.count_parameters(),
                }

        instance  = Module()
        bd        = instance.parameter_breakdown()
        rk_status = "road_kernel=OSM" if instance._road_kernel_loaded else "road_kernel=UNIFORM(fallback)"
        log.info(
            f"FourierPINN v3 built: multi-scale Fourier (σ={_SPATIAL_SIGMA_LO}/{_SPATIAL_SIGMA_HI}), "
            f"trunk={bd['trunk']:,}+head_C={bd['head_C']:,}, "
            f"DiffSubNetV3={bd['diffusion_subnet']:,} "
            f"(K_base={bd['  k_base']:,}, K_aniso={bd['  k_aniso']:,}), "
            f"AlphaNet={bd['alpha_net']:,}, total={bd['total']:,} trainable params, "
            f"{rk_status}"
        )
        return instance


# ═══════════════════════════════════════════════════════════════════════════════
# BACKBONE LOADING UTILITY
# ═══════════════════════════════════════════════════════════════════════════════

def load_partial_backbone(model, v2_state_dict: dict) -> Tuple[int, int]:
    """
    Attempt partial transfer from v8 Stage 2 backbone (v2 architecture) into v3.

    v2 → v3 compatibility map:
      head_C.{weight,bias}       : Linear(128→1)    COMPATIBLE — transfer
      net.input_proj.*           : Linear(512→128)  INCOMPATIBLE (517→256 in v3)
      net.layers.{0-5}.*        : Linear(128→128)  INCOMPATIBLE (256→256 in v3)
      diffusion_subnet.fc{1,2,3}: different arch    ATTEMPT (log result)
      source_subnet.*            : reinitialise      SKIP (always reinit)

    In practice, only head_C transfers. This provides output scale calibration
    (~PM2.5 magnitude range) without needing relearning.

    Args:
        model          : FourierPINNV3 instance
        v2_state_dict  : state dict from v8 Stage 2 checkpoint

    Returns:
        (n_loaded, n_skipped) : counts of state dict keys loaded vs skipped
    """
    import torch
    import torch.nn as nn

    model_state = model.state_dict()
    v3_keys     = set(model_state.keys())

    # Map v2 key prefixes to v3 equivalents
    key_map = {
        "head_C.weight": "head_C.weight",
        "head_C.bias":   "head_C.bias",
    }

    n_loaded  = 0
    n_skipped = 0
    loaded_keys   = []
    skipped_keys  = []

    for v2_key, v3_key in key_map.items():
        if v2_key in v2_state_dict and v3_key in v3_keys:
            v2_tensor = v2_state_dict[v2_key]
            v3_shape  = model_state[v3_key].shape
            if v2_tensor.shape == v3_shape:
                model_state[v3_key] = v2_tensor
                n_loaded   += 1
                loaded_keys.append(f"{v2_key} → {v3_key} {tuple(v3_shape)}")
            else:
                n_skipped += 1
                skipped_keys.append(
                    f"{v2_key} shape mismatch: v2={tuple(v2_tensor.shape)} vs v3={tuple(v3_shape)}"
                )
        else:
            if v2_key in v2_state_dict:
                n_skipped += 1
                skipped_keys.append(f"{v2_key} (no matching v3 key)")

    # Count unmatched trunk keys from v2 (informational only)
    trunk_v2_keys = [k for k in v2_state_dict if k.startswith("net.") or
                     k.startswith("diffusion_subnet.") or k.startswith("source_subnet.")]
    n_skipped += len(trunk_v2_keys)
    for k in trunk_v2_keys:
        skipped_keys.append(f"{k} (architecture change — reinit)")

    model.load_state_dict(model_state)

    log.info(f"Backbone transfer (v2→v3): {n_loaded} keys loaded, {n_skipped} skipped/reinit")
    for s in loaded_keys:
        log.info(f"  LOADED:  {s}")
    log.info(f"  SKIPPED: {n_skipped} keys (trunk: dim mismatch; subnets: reinit)")

    return n_loaded, n_skipped


def reinit_diffusion_subnet_v3(model) -> None:
    """Reinitialise DiffusionSubNetV3 (KBaseNet + KAnisoNet) to Xavier random."""
    import torch.nn as nn
    for m in model.diffusion_subnet.modules():
        if isinstance(m, nn.Linear):
            nn.init.xavier_normal_(m.weight)
            nn.init.zeros_(m.bias)
    n = sum(p.numel() for p in model.diffusion_subnet.parameters())
    log.info(f"[v3] DiffusionSubNetV3 reinitialised: {n} params reset (K_base + K_aniso).")


def reinit_alpha_net(model) -> None:
    """Reinitialise AlphaNet to Xavier random."""
    import torch.nn as nn
    for m in model.alpha_net.modules():
        if isinstance(m, nn.Linear):
            nn.init.xavier_normal_(m.weight)
            nn.init.zeros_(m.bias)
    n = sum(p.numel() for p in model.alpha_net.parameters())
    log.info(f"[v3] AlphaNet reinitialised: {n} params reset.")
