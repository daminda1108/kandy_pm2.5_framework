"""
boundary_conditions.py — Boundary conditions for the Kandy PINN.

Two types of boundary conditions (§2.10 of RESEARCH_PROJECT_DESIGN.md):

1. DIRICHLET BC (valley rim) — Stage 1 Sat-ML predictions at the domain boundary.
   C(x_bnd, y_bnd, t) = C_Stage1(x_bnd, y_bnd, t) ± σ_Stage1
   Stage 1 provides 1 km PM2.5 predictions along the rim; the PINN enforces these
   as Dirichlet conditions. Stage 1 uncertainty σ propagates into the PINN via
   a weighted loss term: w = 1 / (1 + σ²).

2. ZERO-FLUX NEUMANN BC (terrain walls) — No PM2.5 flux through the valley walls.
   ∂C/∂n = 0 on solid terrain boundaries.
   Implemented by penalising the normal gradient of the PINN prediction.

Rationale: Using Stage 1 predictions as boundary conditions is the key
data-assimilation interface between the two pipeline stages.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[3]))
from config import KANDY_PINN_BBOX, LOG_FORMAT, LOG_DATEFMT

logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, level=logging.INFO)
log = logging.getLogger("boundary_conditions")


class DirichletBC:
    """
    Dirichlet boundary condition from Stage 1 predictions along the valley rim.

    At each boundary point (x_bnd, y_bnd, t), the BC value is the Stage 1
    PM2.5 prediction interpolated to the PINN grid. The loss weight is
    inversely proportional to Stage 1 uncertainty:

        L_bc = Σ_i w_i × (C_PINN(x_i, y_i, t_i) - C_Stage1_i)²

    where w_i = 1 / (1 + σ²_Stage1_i)
    """

    def __init__(self, stage1_predictions: pd.DataFrame, domain_bbox: dict = None):
        """
        Args:
            stage1_predictions : DataFrame with columns: date, lat, lon,
                                 pm25_pred, pm25_q05, pm25_q95
            domain_bbox        : Bounding box dict (defaults to KANDY_PINN_BBOX)
        """
        self.bbox  = domain_bbox or KANDY_PINN_BBOX
        self.df    = stage1_predictions.copy()
        self._validate()
        log.info(f"DirichletBC: loaded {len(self.df)} Stage 1 boundary points")

    def _validate(self) -> None:
        required = ["date", "lat", "lon", "pm25_pred"]
        missing  = [c for c in required if c not in self.df.columns]
        if missing:
            raise ValueError(f"Stage 1 predictions missing columns: {missing}")

    def _is_boundary(self, lat: float, lon: float, tol: float = 0.01) -> bool:
        """Check if a point is on or near the domain boundary."""
        return (
            abs(lat - self.bbox["lat_min"]) < tol or
            abs(lat - self.bbox["lat_max"]) < tol or
            abs(lon - self.bbox["lon_min"]) < tol or
            abs(lon - self.bbox["lon_max"]) < tol
        )

    def get_boundary_points(self, date: str) -> pd.DataFrame:
        """
        Return Stage 1 boundary points for a given date, with uncertainty weights.

        Returns:
            DataFrame with: lat, lon, x_norm, y_norm, C_bc, weight
        """
        df_day = self.df[self.df["date"].astype(str) == date].copy()

        # Filter to boundary pixels
        bnd_mask = df_day.apply(
            lambda r: self._is_boundary(r["lat"], r["lon"]), axis=1
        )
        df_bnd = df_day[bnd_mask].copy()

        if df_bnd.empty:
            log.warning(f"No boundary Stage 1 pixels found for {date}")
            return pd.DataFrame()

        # Compute uncertainty weights
        if "pm25_q05" in df_bnd.columns and "pm25_q95" in df_bnd.columns:
            sigma2 = ((df_bnd["pm25_q95"] - df_bnd["pm25_q05"]) / 3.29) ** 2
            df_bnd["weight"] = 1.0 / (1.0 + sigma2)
        else:
            df_bnd["weight"] = 1.0

        # Normalise coordinates to [-1, 1]
        df_bnd["x_norm"] = (
            2.0 * (df_bnd["lon"] - self.bbox["lon_min"]) /
            (self.bbox["lon_max"] - self.bbox["lon_min"]) - 1.0
        )
        df_bnd["y_norm"] = (
            2.0 * (df_bnd["lat"] - self.bbox["lat_min"]) /
            (self.bbox["lat_max"] - self.bbox["lat_min"]) - 1.0
        )
        df_bnd = df_bnd.rename(columns={"pm25_pred": "C_bc"})
        return df_bnd[["lat", "lon", "x_norm", "y_norm", "C_bc", "weight"]]

    def compute_bc_loss(self, model, date: str, device=None) -> "torch.Tensor":
        """
        Compute weighted Dirichlet BC loss for one date.

            L_bc = Σ_i w_i × (C_PINN(x_i, y_i, t) - C_bc_i)²

        Args:
            model  : FourierPINN model
            date   : Date string YYYY-MM-DD
            device : torch.device

        Returns:
            Scalar loss tensor (requires_grad=True)
        """
        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch required")

        bnd_df = self.get_boundary_points(date)
        if bnd_df.empty:
            return torch.zeros(1, requires_grad=True)

        dev  = device or torch.device("cpu")
        x    = torch.tensor(bnd_df["x_norm"].values, dtype=torch.float32, device=dev).unsqueeze(1)
        y    = torch.tensor(bnd_df["y_norm"].values, dtype=torch.float32, device=dev).unsqueeze(1)
        t    = torch.zeros_like(x)   # Normalised time — filled by caller
        cbc  = torch.tensor(bnd_df["C_bc"].values,    dtype=torch.float32, device=dev)
        w    = torch.tensor(bnd_df["weight"].values,  dtype=torch.float32, device=dev)

        xyt  = torch.cat([x, y, t], dim=1)
        c_pred, _ = model(xyt)
        loss = torch.mean(w * (c_pred.squeeze() - cbc) ** 2)
        return loss


class NeumannBC:
    """
    Zero-flux Neumann boundary condition on terrain walls.

    Penalises the normal gradient of C at grid boundaries:
        ∂C/∂n|_wall = 0

    In practice: penalise ∂C/∂x at x=±1 walls and ∂C/∂y at y=±1 walls.
    This is computed via automatic differentiation in the training loop.
    """

    @staticmethod
    def get_wall_points(n: int = 50) -> np.ndarray:
        """
        Sample points uniformly on all four domain walls.

        Returns array shape (4n, 2) of normalised [x, y] on the wall.
        """
        wall_arr  = np.linspace(-1, 1, n)
        south_pts = np.column_stack([wall_arr, np.full(n, -1.0)])   # y = -1 (south)
        north_pts = np.column_stack([wall_arr, np.full(n,  1.0)])   # y = +1 (north)
        west_pts  = np.column_stack([np.full(n, -1.0), wall_arr])   # x = -1 (west)
        east_pts  = np.column_stack([np.full(n,  1.0), wall_arr])   # x = +1 (east)
        return np.vstack([south_pts, north_pts, west_pts, east_pts])

    @staticmethod
    def compute_neumann_loss(model, n_wall: int = 50, t_norm: float = 0.0, device=None):
        """
        Compute zero-flux Neumann penalty at domain walls via autograd.

        ∂C/∂x = 0 at x=+1 and x=-1 walls
        ∂C/∂y = 0 at y=+1 and y=-1 walls

        Returns:
            Scalar loss tensor
        """
        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch required")

        dev = device or torch.device("cpu")
        wall = NeumannBC.get_wall_points(n_wall)
        x = torch.tensor(wall[:, 0:1], dtype=torch.float32, device=dev, requires_grad=True)
        y = torch.tensor(wall[:, 1:2], dtype=torch.float32, device=dev, requires_grad=True)
        t = torch.full_like(x, t_norm)

        xyt = torch.cat([x, y, t], dim=1)
        c_pred, _ = model(xyt)

        dc_dx = torch.autograd.grad(c_pred, x, grad_outputs=torch.ones_like(c_pred),
                                    create_graph=True)[0]
        dc_dy = torch.autograd.grad(c_pred, y, grad_outputs=torch.ones_like(c_pred),
                                    create_graph=True)[0]

        loss = torch.mean(dc_dx ** 2) + torch.mean(dc_dy ** 2)
        return loss
