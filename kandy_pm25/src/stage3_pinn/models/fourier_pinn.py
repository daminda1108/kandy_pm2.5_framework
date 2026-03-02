# Architecture: ablation winner C_medium selected 2026-03-01
# fourier_m=256, hidden_units=128
# See results/ablation/WINNER.txt for full ablation results.
"""
fourier_pinn.py — v2 — FourierPINN: Terrain+BLH-aware PINN for Kandy PM2.5.

Architecture v2 (§2.10 of RESEARCH_PROJECT_DESIGN.md):

    Input: [x, y, t] ∈ [-1,1]³   (normalised space-time coordinates)
       ↓
    Fourier embedding B (σ=1.0, m=256 frequencies)
    [sin(2πBx), cos(2πBx)] ∈ ℝ^512
       ↓
    Residual MLP: 6 × 256 hidden units, Tanh activation
    With skip connections every 2 layers
       ↓  (feat)
    head_C (256→1): C concentration [µg/m³] — softplus (C ≥ 0)
       ├── DiffusionSubNet([x, y, t, blh_norm, elev_norm]) → [Kx, Ky]
       │     3-layer MLP (5→32→32→2), softplus + K_MIN, K_MAX bound penalty
       └── SourceSubNet([x, y, sin_h, cos_h, sin_d, cos_d]) → S
             4-layer MLP (6→48→48→48→1), cyclic time encoding, softplus

Fourier features rationale: standard MLPs fail to learn high-frequency
spatial patterns (spectral bias, Rahaman et al. 2019). Random Fourier
features cure the spectral bias by embedding the input in a rich frequency
space before the MLP sees it.

DiffusionSubNet rationale: Kx and Ky are the dominant physical parameters
governing PM2.5 dispersion. They depend primarily on boundary layer height
(BLH) and terrain channelling — neither of which is captured by normalised
(x,y,t) alone. Without BLH input, K collapses to K_MIN throughout the domain
(spatial collapse). BLH is the most important ERA5 variable for dispersion
in Kandy's nocturnal inversion valley environment.

SourceSubNet rationale: Emission sources (traffic, brick kilns, biomass burning)
have strong diurnal and weekly rhythms that raw normalised t ∈ [0,1] cannot
capture. Cyclic sin/cos encoding of hour-of-day and day-of-week allows the
network to learn "every Monday morning has high kiln emissions" without
also learning spurious temporal trends.

Upgrade history:
  v1 (2026-03-01): Shared trunk → 4 separate linear heads (C, Kx, Ky, S).
                   K heads blind to BLH and terrain → Kx=Ky=K_MIN spatial collapse.
  v2 (2026-03-01): DiffusionSubNet (BLH+elev inputs) + SourceSubNet (cyclic time).
                   Backward-compatible: forward(xyt) still works (blh/elev default 0.5).
                   load_state_dict(strict=False) carries trunk+head_C from v1 backbone.

State dict changes vs v1:
  Removed (in v1 backbone, absent in v2): head_Kx.*, head_Ky.*, head_S.*
  Added (new, randomly initialised)     : diffusion_subnet.fc{1,2,3}.*,
                                          source_subnet.fc{1,2,3,4}.*,
                                          source_subnet.t_max_hours
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
    PINN_HIDDEN_LAYERS, PINN_HIDDEN_UNITS, PINN_FOURIER_FEATURES,
    PINN_FOURIER_SIGMA, K_MIN_MS2, K_MAX_MS2,
    PINN_DIFFUSION_HIDDEN, PINN_SOURCE_HIDDEN,
    PINN_INPUT_DIR,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("fourier_pinn")


# ═══════════════════════════════════════════════════════════════════════════
# FOURIER EMBEDDING  (unchanged from v1)
# ═══════════════════════════════════════════════════════════════════════════

class FourierEmbedding:
    """
    Random Fourier feature embedding (Tancik et al. 2020).

    Maps input x ∈ ℝ^d → [sin(2π B x), cos(2π B x)] ∈ ℝ^{2m}
    where B ~ N(0, σ²) is a fixed (non-trained) random matrix.

    σ controls frequency: larger σ = higher-frequency features.
    σ=1.0 works well for normalised [-1,1] domains.
    """

    def __init__(self, in_dim: int = 3, m: int = None, sigma: float = None, seed: int = 42):
        m     = m     or PINN_FOURIER_FEATURES
        sigma = sigma or PINN_FOURIER_SIGMA
        rng   = np.random.default_rng(seed)
        self.B = rng.normal(0, sigma, size=(m, in_dim)).astype(np.float32)
        self.out_dim = 2 * m

    def embed(self, x: "torch.Tensor") -> "torch.Tensor":
        """
        Apply Fourier embedding to input tensor.

        Args:
            x : (N, d) input tensor
        Returns:
            (N, 2m) embedding tensor
        """
        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch required")

        B = torch.tensor(self.B, dtype=x.dtype, device=x.device)
        proj = 2.0 * np.pi * x @ B.T      # (N, m)
        return torch.cat([torch.sin(proj), torch.cos(proj)], dim=-1)


# ═══════════════════════════════════════════════════════════════════════════
# RESIDUAL MLP  (unchanged from v1 — must match Medellín backbone exactly)
# ═══════════════════════════════════════════════════════════════════════════

def _build_mlp(in_dim: int, hidden: int, n_layers: int):
    """Build a Tanh MLP with skip connections every 2 layers.

    Output dimension equals `hidden` — the output heads project directly
    from the final hidden state (no separate output linear layer).
    This matches the Medellín pre-trained backbone exactly.
    """
    try:
        import torch.nn as nn
    except ImportError:
        raise ImportError("PyTorch required")

    class ResidualMLP(nn.Module):
        def __init__(self):
            super().__init__()
            self.input_proj = nn.Linear(in_dim, hidden)
            self.layers = nn.ModuleList([nn.Linear(hidden, hidden) for _ in range(n_layers)])
            self.activation = nn.Tanh()

        def forward(self, x):
            h = self.activation(self.input_proj(x))
            for i, layer in enumerate(self.layers):
                h_new = self.activation(layer(h))
                if i % 2 == 1:
                    h = h + h_new   # skip connection every 2 layers
                else:
                    h = h_new
            return h

    return ResidualMLP()


# ═══════════════════════════════════════════════════════════════════════════
# DIFFUSION SUBNET  (v2 — Upgrade 1)
# ═══════════════════════════════════════════════════════════════════════════

class DiffusionSubNet:
    """
    Terrain+BLH-aware 3-layer MLP for anisotropic diffusivity prediction.

    Inputs  : [x_norm, y_norm, t_norm, blh_norm, elev_norm]  (5 features)
    Output  : [Kx, Ky]  with softplus + K_MIN floor
    Arch    : Linear(5→32) → Tanh → Linear(32→32) → Tanh → Linear(32→2)
    Params  : 192 + 1056 + 66 = 1,314

    Bias of final layer initialised to log(exp(10 - K_MIN) - 1) so that
    initial Kx = Ky ≈ 10 m²/s (physically plausible mid-range estimate).

    blh_norm : BLH / PINN_BLH_NORM_SCALE  (passed pre-normalised by caller)
    elev_norm: (elevation − domain_min_elev) / (domain_max − domain_min)
               Use 0.5 as neutral placeholder when DEM unavailable
               (Medellín pre-training, where 11 stations are spatially aggregated).

    Bound penalty: soft squared penalty for K outside [K_MIN, K_MAX].
    Keeps gradients alive at boundaries without hard clipping.
    """

    def __new__(cls, k_min: float = K_MIN_MS2, k_max: float = K_MAX_MS2,
                hidden: int = PINN_DIFFUSION_HIDDEN):
        try:
            import torch
            import torch.nn as nn
            import torch.nn.functional as F
        except ImportError:
            raise ImportError("PyTorch required")

        k_min_ = k_min
        k_max_ = k_max

        class _Sub(nn.Module):
            def __init__(self):
                super().__init__()
                self._k_min = k_min_
                self._k_max = k_max_
                self.fc1 = nn.Linear(5, hidden)
                self.fc2 = nn.Linear(hidden, hidden)
                self.fc3 = nn.Linear(hidden, 2)
                # Xavier normal init throughout
                for m in self.modules():
                    if isinstance(m, nn.Linear):
                        nn.init.xavier_normal_(m.weight)
                        nn.init.zeros_(m.bias)
                # Override final layer bias so K_initial ≈ 10 m²/s
                # softplus(b) + k_min = 10  →  b = log(exp(10 - k_min) - 1)
                bias_init = math.log(math.exp(10.0 - k_min_) - 1.0)
                nn.init.constant_(self.fc3.bias, bias_init)

            def forward(self,
                        x_n: "torch.Tensor",
                        y_n: "torch.Tensor",
                        t_n: "torch.Tensor",
                        blh_n: "torch.Tensor",
                        elev_n: "torch.Tensor") -> Tuple["torch.Tensor", "torch.Tensor"]:
                """
                Args:
                    x_n, y_n, t_n : (N, 1) normalised spatial + time coords
                    blh_n          : (N, 1) BLH / 2000.0 ∈ [0, 1]
                    elev_n         : (N, 1) normalised elevation ∈ [0, 1]; 0.5 if unavailable
                Returns:
                    Kx : (N, 1) along-valley diffusivity [m²/s]
                    Ky : (N, 1) cross-valley diffusivity [m²/s]
                """
                inp = torch.cat([x_n, y_n, t_n, blh_n, elev_n], dim=1)  # (N, 5)
                h = torch.tanh(self.fc1(inp))
                h = torch.tanh(self.fc2(h))
                out = self.fc3(h)                               # (N, 2)
                Kx = F.softplus(out[:, 0:1]) + self._k_min
                Ky = F.softplus(out[:, 1:2]) + self._k_min
                return Kx, Ky

            def bound_penalty(self,
                               Kx: "torch.Tensor",
                               Ky: "torch.Tensor") -> "torch.Tensor":
                """
                Soft squared penalty for K outside [K_MIN, K_MAX].
                Keeps gradients alive at the boundaries without hard clipping.
                Weight by lambda_k_bound in the total loss.
                """
                low  = F.relu(self._k_min - Kx) ** 2 + F.relu(self._k_min - Ky) ** 2
                high = F.relu(Kx - self._k_max) ** 2 + F.relu(Ky - self._k_max) ** 2
                return torch.mean(low + high)

        return _Sub()


# ═══════════════════════════════════════════════════════════════════════════
# SOURCE SUBNET  (v2 — Upgrade 2)
# ═══════════════════════════════════════════════════════════════════════════

class SourceSubNet:
    """
    Temporal-only source amplitude MLP with cyclic time encoding (B4).

    Inputs  : [sin(2π·h/24), cos(2π·h/24), sin(2π·d/7), cos(2π·d/7)]  (4 features)
    Output  : α(t) ≥ 0  (temporal amplitude, softplus)
    Arch    : Linear(4→48) → Tanh → Linear(48→48) → Tanh
              → Linear(48→48) → Tanh → Linear(48→1) → Softplus
    Params  : 240 + 2352 + 2352 + 49 = 4,993

    The full source term is S(x,y,t) = α(t) × R(x,y), where R(x,y) is the
    fixed OSM road kernel loaded as a registered buffer in FourierPINN.
    Removing x,y from SourceSubNet prevents it from overriding the road kernel's
    spatial structure — only the temporal amplitude is free to learn.

    B4 change: x_norm, y_norm removed from inputs (was 6-feature, now 4-feature).
    Stage 2 backbone loading: source_subnet is always reinitialised at Stage 3 start
    (gap A4), so this input-dimension change does NOT break backbone transfer.

    t_max_hours is stored as a non-trainable buffer. Update it when
    transferring the model to a new city's time domain:
        model.source_subnet.t_max_hours = torch.tensor(new_t_max)
    Stage 3 sets t_max_hours = 24.0 so that t_norm = h/24 maps to h_day = h.
    """

    def __new__(cls, t_max: Optional[float] = None,
                hidden: int = PINN_SOURCE_HIDDEN):
        try:
            import torch
            import torch.nn as nn
            import torch.nn.functional as F
        except ImportError:
            raise ImportError("PyTorch required")

        t_max_val = float(t_max) if t_max is not None else 8760.0  # default 1 year

        class _Sub(nn.Module):
            def __init__(self):
                super().__init__()
                # B4: 4-input (temporal only — x,y removed, spatial structure from road kernel)
                self.fc1 = nn.Linear(4, hidden)
                self.fc2 = nn.Linear(hidden, hidden)
                self.fc3 = nn.Linear(hidden, hidden)
                self.fc4 = nn.Linear(hidden, 1)
                # Xavier normal init
                for m in self.modules():
                    if isinstance(m, nn.Linear):
                        nn.init.xavier_normal_(m.weight)
                        nn.init.zeros_(m.bias)
                # t_max stored as a non-trainable buffer — updated when model is
                # transferred to a new city (set externally before fine-tuning)
                self.register_buffer(
                    "t_max_hours",
                    torch.tensor(t_max_val, dtype=torch.float32)
                )

            def forward(self, t_n: "torch.Tensor") -> "torch.Tensor":
                """
                Args:
                    t_n : (N, 1) normalised time ∈ [0, 1] (= h/24 in Stage 3)
                Returns:
                    alpha : (N, 1) temporal amplitude ≥ 0
                            Full source term: S(x,y,t) = alpha(t) × R(x,y)
                            R(x,y) is the road kernel in FourierPINN.
                """
                t_h   = t_n * self.t_max_hours          # hours since t_origin (N, 1)
                h_day = t_h % 24.0                      # hour-of-day ∈ [0, 24)
                d_wk  = (t_h / 24.0) % 7.0             # day-of-week ∈ [0, 7)
                pi2   = 2.0 * math.pi

                sin_h = torch.sin(pi2 * h_day / 24.0)
                cos_h = torch.cos(pi2 * h_day / 24.0)
                sin_d = torch.sin(pi2 * d_wk  / 7.0)
                cos_d = torch.cos(pi2 * d_wk  / 7.0)

                inp   = torch.cat([sin_h, cos_h, sin_d, cos_d], dim=1)  # (N, 4)
                h     = torch.tanh(self.fc1(inp))
                h     = torch.tanh(self.fc2(h))
                h     = torch.tanh(self.fc3(h))
                alpha = F.softplus(self.fc4(h))         # (N, 1), alpha ≥ 0
                return alpha

        return _Sub()


# ═══════════════════════════════════════════════════════════════════════════
# FOURIER PINN  (public interface)
# ═══════════════════════════════════════════════════════════════════════════

class FourierPINN:
    """
    Fourier Feature Physics-Informed Neural Network for Kandy PM2.5.

    Forward pass returns: (C, (Kx, Ky, S))
    All outputs are physically constrained (non-negative, bounded).

    Usage:
        model = FourierPINN()
        xyt  = torch.tensor([[0.1, 0.2, 0.5], ...])  # normalised coords
        C, (Kx, Ky, S) = model(xyt)                  # blh/elev default to 0.5

        # With BLH and elevation (recommended for Kandy):
        blh_norm = blh_m / 2000.0
        C, (Kx, Ky, S) = model(xyt, blh=blh_norm, elev=elev_norm)
    """

    def __new__(cls, *args, **kwargs):
        """
        Returns a torch.nn.Module. Defined as __new__ so that isinstance(model, nn.Module)
        works correctly even though the class logic is in _FourierPINNModule.
        """
        return _FourierPINNModule(*args, **kwargs)


def build_fourier_pinn(
    in_dim:          int   = 3,
    n_fourier:       int   = None,
    fourier_sigma:   float = None,
    hidden_units:    int   = None,
    hidden_layers:   int   = None,
    k_min:           float = None,
    k_max:           float = None,
    t_max:           float = None,
    diff_hidden:     int   = None,
    src_hidden:      int   = None,
    road_kernel_path = None,
) -> "_FourierPINNModule":
    """Factory function to build a FourierPINN v2 with explicit hyperparameters.

    Args:
        road_kernel_path : Path to kandy_road_kernel_100m.npz (B4).
                           None → default PINN_INPUT_DIR / kandy_road_kernel_100m.npz.
                           If file not found, uniform R=1 fallback is used automatically.
    """
    return _FourierPINNModule(
        in_dim=in_dim,
        n_fourier=n_fourier or PINN_FOURIER_FEATURES,
        fourier_sigma=fourier_sigma or PINN_FOURIER_SIGMA,
        hidden_units=hidden_units or PINN_HIDDEN_UNITS,
        hidden_layers=hidden_layers or PINN_HIDDEN_LAYERS,
        k_min_ms2=k_min or K_MIN_MS2,
        k_max_ms2=k_max or K_MAX_MS2,
        t_max=t_max,
        diff_hidden=diff_hidden or PINN_DIFFUSION_HIDDEN,
        src_hidden=src_hidden or PINN_SOURCE_HIDDEN,
        # resolve None → default path so kwargs.get() returns the right thing
        road_kernel_path=(
            road_kernel_path
            if road_kernel_path is not None
            else PINN_INPUT_DIR / "kandy_road_kernel_100m.npz"
        ),
    )


class _FourierPINNModule:
    """
    Internal torch.nn.Module implementation for FourierPINN v2.
    Instantiated by FourierPINN.__new__ and build_fourier_pinn.

    State dict keys (v2, B4 update):
      net.input_proj.{weight,bias}               ← carried from Stage 2 backbone
      net.layers.{0..5}.{weight,bias}            ← carried from Stage 2 backbone
      head_C.{weight,bias}                       ← carried from Stage 2 backbone
      diffusion_subnet.fc{1,2,3}.{weight,bias}   ← reinitialised at Stage 3 start
      source_subnet.fc{1,2,3,4}.{weight,bias}    ← reinitialised at Stage 3 start
      source_subnet.t_max_hours                  ← buffer (set to 24.0 for Stage 3)
      road_kernel                                ← B4: (150,150) buffer (non-trainable)

    Loading Stage 2 backbone at Stage 3 start (strict=False):
      Carried: net.*, head_C.*
      Reinitialised (discarded from backbone): diffusion_subnet.*, source_subnet.*
      New (not in backbone): road_kernel buffer (loaded from NPZ, not from checkpoint)

    B4 note: source_subnet.fc1 changed from Linear(6, hidden) to Linear(4, hidden).
    Load with strict=False; source_subnet is always reinitialised anyway (gap A4).
    """

    def __new__(cls, *args, **kwargs):
        try:
            import torch
            import torch.nn as nn
            import torch.nn.functional as F
        except ImportError:
            raise ImportError("PyTorch not installed. Run: pip install torch")

        in_dim           = kwargs.get("in_dim",           3)
        n_fourier        = kwargs.get("n_fourier",        PINN_FOURIER_FEATURES)
        fourier_sigma    = kwargs.get("fourier_sigma",    PINN_FOURIER_SIGMA)
        hidden_units     = kwargs.get("hidden_units",     PINN_HIDDEN_UNITS)
        hidden_layers    = kwargs.get("hidden_layers",    PINN_HIDDEN_LAYERS)
        k_min_ms2        = kwargs.get("k_min_ms2",        K_MIN_MS2)
        k_max_ms2        = kwargs.get("k_max_ms2",        K_MAX_MS2)
        t_max_val        = kwargs.get("t_max",            None)
        diff_hidden      = kwargs.get("diff_hidden",      PINN_DIFFUSION_HIDDEN)
        src_hidden       = kwargs.get("src_hidden",       PINN_SOURCE_HIDDEN)
        road_kernel_path = kwargs.get(
            "road_kernel_path",
            PINN_INPUT_DIR / "kandy_road_kernel_100m.npz",
        )

        embedding = FourierEmbedding(in_dim, n_fourier, fourier_sigma)
        embed_dim = embedding.out_dim

        class Module(nn.Module):
            def __init__(self):
                super().__init__()
                self.embedding = embedding
                self.net       = _build_mlp(embed_dim, hidden_units, hidden_layers)
                # C head (shared trunk → concentration)
                self.head_C    = nn.Linear(hidden_units, 1)
                # V2: dedicated physics subnets replace trunk heads for Kx, Ky, S
                self.diffusion_subnet = DiffusionSubNet(
                    k_min=k_min_ms2, k_max=k_max_ms2, hidden=diff_hidden
                )
                # B4: temporal-only source subnet (x,y removed — spatial from road kernel)
                self.source_subnet = SourceSubNet(
                    t_max=t_max_val, hidden=src_hidden
                )
                # Xavier init for head_C (subnets handle their own init)
                nn.init.xavier_uniform_(self.head_C.weight)
                nn.init.zeros_(self.head_C.bias)

                # B4: OSM road kernel R(x,y) — fixed spatial emission pattern.
                # S(x,y,t) = alpha(t) × R(x,y). Fixes the spatial source structure
                # so K(x,y) cannot trade off with S spatially (K–S degeneracy broken).
                # Stored as non-trainable buffer; moved to device with model.to(device).
                # Fallback: uniform R=1 if NPZ not found (Stage 2, Kaggle pre-training).
                _rk_loaded = False
                try:
                    _rk_data = np.load(str(road_kernel_path))
                    _rk = torch.tensor(_rk_data["R"], dtype=torch.float32)
                    _rk_loaded = True
                    log.info(
                        f"Road kernel loaded: {_rk.shape}, "
                        f"non-zero={float((_rk > 0.01).sum()) / _rk.numel() * 100:.1f}% "
                        f"(K-S degeneracy broken)"
                    )
                except Exception as _rk_exc:
                    _rk = torch.ones(150, 150, dtype=torch.float32)
                    log.warning(
                        f"Road kernel not found ({_rk_exc}) — using uniform R=1 fallback. "
                        "K-S degeneracy NOT broken. Acceptable for Stage 2 pre-training; "
                        "run source_kernel.py before Stage 3 training."
                    )
                self.register_buffer("road_kernel", _rk)
                self._road_kernel_loaded = _rk_loaded

            def _interp_road_kernel(self,
                                    x_n: "torch.Tensor",
                                    y_n: "torch.Tensor") -> "torch.Tensor":
                """
                Bilinear-interpolate R(x,y) from the 150×150 road kernel buffer to
                arbitrary normalised collocation points (x_n, y_n) ∈ [-1, 1]².

                Coordinate mapping (align_corners=True):
                    grid_sample grid[..., 0] = x (W/lon direction):  -1=lon_min, +1=lon_max
                    grid_sample grid[..., 1] = y (H/lat direction):  -1=lat_min, +1=lat_max
                Road kernel stored as R[row_lat, col_lon] with lat ascending
                (row 0 = lat_min, row 149 = lat_max) — matches grid_sample convention.

                Args:
                    x_n : (N, 1) normalised longitude ∈ [-1, 1]
                    y_n : (N, 1) normalised latitude  ∈ [-1, 1]
                Returns:
                    R_interp : (N, 1) interpolated kernel values ∈ [0, 1]
                """
                N = x_n.shape[0]
                # grid_sample expects (N_batch, H_out, W_out, 2)
                # Reshape N arbitrary points as (1, N, 1, 2)
                grid = torch.stack([x_n.squeeze(-1), y_n.squeeze(-1)], dim=-1)  # (N, 2)
                grid = grid.unsqueeze(0).unsqueeze(2)                            # (1, N, 1, 2)
                # Road kernel as (1, 1, H, W)
                kernel = self.road_kernel.unsqueeze(0).unsqueeze(0)             # (1, 1, 150, 150)
                # Interpolate: output shape (1, 1, N, 1)
                R_interp = F.grid_sample(
                    kernel, grid,
                    mode='bilinear',
                    padding_mode='border',   # clamp to edge outside [-1, 1]
                    align_corners=True,
                )
                return R_interp[0, 0, :, 0].unsqueeze(-1)                      # (N, 1)

            def forward(self,
                        xyt:  "torch.Tensor",
                        blh:  Optional["torch.Tensor"] = None,
                        elev: Optional["torch.Tensor"] = None,
                        ) -> Tuple["torch.Tensor", Tuple]:
                """
                Forward pass.

                Args:
                    xyt  : (N, 3) normalised [x, y, t] tensor, t ∈ [0, 1]
                    blh  : (N, 1) normalised BLH = BLH_m / 2000.0, ∈ [0, 1].
                           None → defaults to 0.5 (neutral mid-range).
                    elev : (N, 1) normalised elevation ∈ [0, 1].
                           None → defaults to 0.5 (use when DEM unavailable).

                Returns:
                    C   : (N, 1) PM2.5 concentration [µg/m³]
                    Kx  : (N, 1) along-valley diffusivity [m²/s]
                    Ky  : (N, 1) cross-valley diffusivity [m²/s]
                    S   : (N, 1) source strength [µg/m³/s] = alpha(t) × R(x,y)
                """
                N, device = xyt.shape[0], xyt.device
                if blh  is None: blh  = torch.full((N, 1), 0.5, dtype=xyt.dtype, device=device)
                if elev is None: elev = torch.full((N, 1), 0.5, dtype=xyt.dtype, device=device)

                # Main trunk: Fourier embedding → ResidualMLP
                emb  = self.embedding.embed(xyt)
                feat = self.net(emb)

                # Concentration head (from trunk features)
                C = F.softplus(self.head_C(feat))

                # Diffusivity from terrain+BLH-aware subnet
                x_n, y_n, t_n = xyt[:, 0:1], xyt[:, 1:2], xyt[:, 2:3]
                Kx, Ky = self.diffusion_subnet(x_n, y_n, t_n, blh, elev)

                # B4: S(x,y,t) = alpha(t) × R(x,y)
                # alpha: temporal amplitude from cyclic-time MLP
                # R: fixed spatial emission kernel (OSM roads + WorldCover)
                alpha = self.source_subnet(t_n)           # (N, 1)
                R_interp = self._interp_road_kernel(x_n, y_n)  # (N, 1)
                S = alpha * R_interp                      # (N, 1)

                return C, (Kx, Ky, S)

            def count_parameters(self) -> int:
                return sum(p.numel() for p in self.parameters() if p.requires_grad)

            def parameter_breakdown(self) -> dict:
                """Return per-component trainable parameter counts."""
                def _count(module):
                    return sum(p.numel() for p in module.parameters() if p.requires_grad)
                return {
                    "net (main trunk)":  _count(self.net),
                    "head_C":            _count(self.head_C),
                    "diffusion_subnet":  _count(self.diffusion_subnet),
                    "source_subnet":     _count(self.source_subnet),
                    "total":             self.count_parameters(),
                }

        instance  = Module()
        breakdown = instance.parameter_breakdown()
        kernel_status = "road_kernel=OSM" if instance._road_kernel_loaded else "road_kernel=UNIFORM(fallback)"
        log.info(
            f"FourierPINN v2 built: {n_fourier} Fourier features (sigma={fourier_sigma}), "
            f"{hidden_layers}x{hidden_units} ResidualMLP, "
            f"{breakdown['total']:,} total trainable params "
            f"(trunk={breakdown['net (main trunk)']:,}, "
            f"head_C={breakdown['head_C']:,}, "
            f"DiffSubNet={breakdown['diffusion_subnet']:,}, "
            f"SrcSubNet={breakdown['source_subnet']:,}), "
            f"{kernel_status}"
        )
        return instance


# ═══════════════════════════════════════════════════════════════════════════
# REINITIALISATION UTILITIES  (Upgrade 3)
# ═══════════════════════════════════════════════════════════════════════════

def reinit_source_subnet(model) -> None:
    """
    Reinitialise SourceSubNet weights to Xavier random.

    Call at the start of Stage 3 Kandy fine-tuning to discard
    city-specific emission patterns learned during Medellín pre-training.
    Medellín traffic spatial patterns carry NO information about Kandy's
    emission hotspots (vehicles, brick kilns, incense burning).

    The main trunk, head_C, and DiffusionSubNet are NOT touched.

    Args:
        model : FourierPINN instance (must have .source_subnet attribute)
    """
    try:
        import torch.nn as nn
    except ImportError:
        raise ImportError("PyTorch required")

    for m in model.source_subnet.modules():
        if isinstance(m, nn.Linear):
            nn.init.xavier_normal_(m.weight)
            nn.init.zeros_(m.bias)
    n = sum(p.numel() for p in model.source_subnet.parameters())
    log.info(f"SourceSubNet reinitialised: {n} parameters reset to Xavier random.")


def reinit_diffusion_subnet(model) -> None:
    """
    Reinitialise DiffusionSubNet weights to Xavier random.

    Call when transferring to a city with substantially different terrain
    from the pre-training city (e.g., Kandy amphitheatre bowl vs Medellín
    linear valley). The learned K(x,y,blh) spatial structure will not transfer.

    Note: After reinit, K_initial ≈ softplus(0) + K_MIN ≈ 1.7 m²/s.
    To restore K≈10 initialisation after reinit:
        import math
        nn.init.constant_(model.diffusion_subnet.fc3.bias,
                          math.log(math.exp(10.0 - K_MIN_MS2) - 1.0))

    The main trunk, head_C, and SourceSubNet are NOT touched.

    Args:
        model : FourierPINN instance (must have .diffusion_subnet attribute)
    """
    try:
        import torch.nn as nn
    except ImportError:
        raise ImportError("PyTorch required")

    for m in model.diffusion_subnet.modules():
        if isinstance(m, nn.Linear):
            nn.init.xavier_normal_(m.weight)
            nn.init.zeros_(m.bias)
    n = sum(p.numel() for p in model.diffusion_subnet.parameters())
    log.info(f"DiffusionSubNet reinitialised: {n} parameters reset to Xavier random.")
