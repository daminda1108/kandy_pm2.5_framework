"""
fourier_pinn.py — FourierPINN: the core neural network for Stage 3 Kandy PINN.

Architecture (§2.10 of RESEARCH_PROJECT_DESIGN.md):

    Input: [x, y, t] ∈ [-1,1]³   (normalised space-time coordinates)
       ↓
    Fourier embedding B (σ=1.0, m=256 frequencies)
    [sin(2πBx), cos(2πBx)] ∈ ℝ^512
       ↓
    Residual MLP: 6 × 256 hidden units, Tanh activation
    With skip connections every 2 layers
       ↓
    Four output heads (4 × separate linear layers):
      C   (concentration, µg/m³) — softplus activation (C ≥ 0)
      Kx  (along-valley diffusivity, m²/s) — softplus + K_MIN
      Ky  (cross-valley diffusivity, m²/s) — softplus + K_MIN
      S   (source strength, µg/m³/s) — OSM-structured softplus

Fourier features rationale: standard MLPs fail to learn high-frequency
spatial patterns (spectral bias, Rahaman et al. 2019). Random Fourier
features cure the spectral bias by embedding the input in a rich frequency
space before the MLP sees it.
"""

import logging
import sys
from pathlib import Path
from typing import Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import (
    LOG_FORMAT, LOG_DATEFMT,
    PINN_HIDDEN_LAYERS, PINN_HIDDEN_UNITS, PINN_FOURIER_FEATURES,
    PINN_FOURIER_SIGMA, K_MIN_MS2, K_MAX_MS2,
)

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("fourier_pinn")


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


def _build_mlp(in_dim: int, hidden: int, n_layers: int, out_dim: int):
    """Build a Tanh MLP with skip connections every 2 layers."""
    try:
        import torch.nn as nn
    except ImportError:
        raise ImportError("PyTorch required")

    class ResidualMLP(nn.Module):
        def __init__(self):
            super().__init__()
            self.input_proj = nn.Linear(in_dim, hidden)
            self.layers = nn.ModuleList([nn.Linear(hidden, hidden) for _ in range(n_layers)])
            self.output = nn.Linear(hidden, out_dim)
            self.activation = nn.Tanh()

        def forward(self, x):
            h = self.activation(self.input_proj(x))
            for i, layer in enumerate(self.layers):
                h_new = self.activation(layer(h))
                if i % 2 == 1:
                    h = h + h_new   # skip connection every 2 layers
                else:
                    h = h_new
            return self.output(h)

    return ResidualMLP()


class FourierPINN:
    """
    Fourier Feature Physics-Informed Neural Network for Kandy PM2.5.

    Forward pass returns: (C, (Kx, Ky, S))
    All outputs are physically constrained (non-negative, bounded).

    Usage:
        model = FourierPINN()
        xyt  = torch.tensor([[0.1, 0.2, 0.5], ...])  # normalised coords
        C, (Kx, Ky, S) = model(xyt)
    """

    def __new__(cls, *args, **kwargs):
        """
        Returns a torch.nn.Module. Defined as __new__ so that isinstance(model, nn.Module)
        works correctly even though the class logic is in _FourierPINNModule.
        """
        return _FourierPINNModule(*args, **kwargs)


def build_fourier_pinn(
    in_dim:        int   = 3,
    n_fourier:     int   = None,
    fourier_sigma: float = None,
    hidden_units:  int   = None,
    hidden_layers: int   = None,
    k_min:         float = None,
) -> "_FourierPINNModule":
    """Factory function to build a FourierPINN with explicit hyperparameters."""
    return _FourierPINNModule(
        in_dim=in_dim,
        n_fourier=n_fourier or PINN_FOURIER_FEATURES,
        fourier_sigma=fourier_sigma or PINN_FOURIER_SIGMA,
        hidden_units=hidden_units or PINN_HIDDEN_UNITS,
        hidden_layers=hidden_layers or PINN_HIDDEN_LAYERS,
        k_min_ms2=k_min or K_MIN_MS2,
    )


class _FourierPINNModule:
    """
    Internal torch.nn.Module implementation for FourierPINN.
    Instantiated by FourierPINN.__new__ and build_fourier_pinn.
    """

    def __new__(cls, *args, **kwargs):
        try:
            import torch
            import torch.nn as nn
            import torch.nn.functional as F
        except ImportError:
            raise ImportError("PyTorch not installed. Run: pip install torch")

        in_dim        = kwargs.get("in_dim", 3)
        n_fourier     = kwargs.get("n_fourier", PINN_FOURIER_FEATURES)
        fourier_sigma = kwargs.get("fourier_sigma", PINN_FOURIER_SIGMA)
        hidden_units  = kwargs.get("hidden_units",  PINN_HIDDEN_UNITS)
        hidden_layers = kwargs.get("hidden_layers", PINN_HIDDEN_LAYERS)
        k_min_ms2     = kwargs.get("k_min_ms2",     K_MIN_MS2)

        embedding = FourierEmbedding(in_dim, n_fourier, fourier_sigma)
        embed_dim = embedding.out_dim

        class Module(nn.Module):
            def __init__(self):
                super().__init__()
                self.embedding = embedding
                self.net = _build_mlp(embed_dim, hidden_units, hidden_layers, hidden_units)
                # Four output heads
                self.head_C  = nn.Linear(hidden_units, 1)
                self.head_Kx = nn.Linear(hidden_units, 1)
                self.head_Ky = nn.Linear(hidden_units, 1)
                self.head_S  = nn.Linear(hidden_units, 1)
                self._k_min = k_min_ms2

                # Weight init: Xavier uniform
                for m in self.modules():
                    if isinstance(m, nn.Linear):
                        nn.init.xavier_uniform_(m.weight)
                        nn.init.zeros_(m.bias)

            def forward(self, xyt: torch.Tensor) -> Tuple[torch.Tensor, Tuple]:
                """
                Forward pass.

                Args:
                    xyt : (N, 3) normalised [x, y, t] tensor

                Returns:
                    C   : (N, 1) PM2.5 concentration [µg/m³]
                    Kx  : (N, 1) along-valley diffusivity [m²/s]
                    Ky  : (N, 1) cross-valley diffusivity [m²/s]
                    S   : (N, 1) source strength [µg/m³/s]
                """
                emb  = self.embedding.embed(xyt)
                feat = self.net(emb)

                C  = F.softplus(self.head_C(feat))
                Kx = F.softplus(self.head_Kx(feat)) + self._k_min
                Ky = F.softplus(self.head_Ky(feat)) + self._k_min
                S  = F.softplus(self.head_S(feat))
                return C, (Kx, Ky, S)

            def count_parameters(self) -> int:
                return sum(p.numel() for p in self.parameters() if p.requires_grad)

        instance = Module()
        n_params = instance.count_parameters()
        log.info(
            f"FourierPINN built: {n_fourier} Fourier features (σ={fourier_sigma}), "
            f"{hidden_layers}×{hidden_units} ResidualMLP, {n_params:,} trainable params"
        )
        return instance
