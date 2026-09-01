"""Observation operators, instrument bias and representativeness error.

Implements MODEL_SPECIFICATION.md section 4:

    y_k(t) = H_k[C](t) + b_k + e_k ,   e_k ~ N(0, sigma_meas^2 + sigma_rep^2)

WHY THIS MODULE EXISTS. The model produces an AREAL field on a 1 km grid; a monitor measures a
POINT. Comparing them by naive co-location is a change-of-support error, and it is the reason
the shipped 90% interval measured 72.4% empirical coverage -- observations fell BELOW the lower
bound in 25.7% of hours and above the upper in only 1.9%, a one-sided offset of about
+5.85 ug/m3. Removing each sensor's own median offset restored 91.5%. The width was correct all
along; the comparison was not.

Two distinct quantities are needed and they are NOT the same thing:

  b_k        a SYSTEMATIC offset for instrument k -- siting bias (a kerbside monitor inside a
             1 km cell reads systematically above the cell mean) plus device calibration.
             This is where the low-cost-sensor calibration lives.

  sigma_rep  a RANDOM error from sub-grid variability the model cannot resolve. Estimated from
             the local spatial variability of the field itself, so it grows in structured
             hours and shrinks when the field is well mixed -- which is the physically correct
             behaviour and is free, because the model already carries the pattern.

Nothing here fits anything. These are the operators; estimating b_k and sigma_rep from data is
a Bud2 activity (it needs a reference monitor).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


# ── operators ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PointOperator:
    """A point instrument inside a grid cell.

    `mode="nearest"` takes the containing cell. `mode="bilinear"` interpolates, which is the
    better choice when the sensor sits near a cell boundary.
    """

    lat: float
    lon: float
    mode: str = "nearest"

    def apply(self, field: np.ndarray, lats: np.ndarray, lons: np.ndarray) -> float:
        """field (ny, nx) on ascending `lats`, `lons` -> scalar."""
        if self.mode == "nearest":
            i = int(np.abs(lats - self.lat).argmin())
            j = int(np.abs(lons - self.lon).argmin())
            return float(field[i, j])
        if self.mode == "bilinear":
            return _bilinear(field, lats, lons, self.lat, self.lon)
        raise ValueError(f"unknown mode {self.mode!r}")


@dataclass(frozen=True)
class AreaOperator:
    """An areal product (satellite retrieval, model cell): the mean over a footprint."""

    mask: np.ndarray | None = None   # boolean (ny, nx); None = whole domain

    def apply(self, field: np.ndarray, lats=None, lons=None) -> float:
        if self.mask is None:
            return float(np.nanmean(field))
        return float(np.nanmean(field[self.mask]))


@dataclass(frozen=True)
class TimeIntegratedOperator:
    """A passive sampler: a point in space, integrated over an exposure window.

    Kandy's only identified route to a SPATIAL constraint is a passive NO2/SO2 network, whose
    samplers integrate over weeks. Comparing such a value to an instantaneous field is the same
    class of error as comparing a point to an area -- hence a distinct operator.
    """

    lat: float
    lon: float
    mode: str = "nearest"

    def apply(self, fields: Sequence[np.ndarray], lats: np.ndarray,
              lons: np.ndarray, weights: Sequence[float] | None = None) -> float:
        pt = PointOperator(self.lat, self.lon, self.mode)
        vals = np.array([pt.apply(f, lats, lons) for f in fields], dtype=float)
        if weights is None:
            return float(np.nanmean(vals))
        w = np.asarray(weights, dtype=float)
        if len(w) != len(vals):
            raise ValueError("weights and fields differ in length")
        return float(np.nansum(vals * w) / np.nansum(w))


def _bilinear(field, lats, lons, lat, lon) -> float:
    i = int(np.clip(np.searchsorted(lats, lat) - 1, 0, len(lats) - 2))
    j = int(np.clip(np.searchsorted(lons, lon) - 1, 0, len(lons) - 2))
    dy = (lat - lats[i]) / (lats[i + 1] - lats[i])
    dx = (lon - lons[j]) / (lons[j + 1] - lons[j])
    dy = float(np.clip(dy, 0, 1)); dx = float(np.clip(dx, 0, 1))
    return float(
        field[i, j] * (1 - dy) * (1 - dx) + field[i + 1, j] * dy * (1 - dx)
        + field[i, j + 1] * (1 - dy) * dx + field[i + 1, j + 1] * dy * dx
    )


# ── error model ───────────────────────────────────────────────────────────────────────────

def representativeness_sigma(field: np.ndarray, lats: np.ndarray, lons: np.ndarray,
                             lat: float, lon: float, radius_cells: int = 1) -> float:
    """Sub-grid variability proxy: the local standard deviation around the sensor cell.

    A point inside a cell can differ from the cell mean by roughly the amount the field varies
    over the neighbourhood. This is a PROXY for true sub-grid variance -- the model has no
    sub-kilometre information -- and it is deliberately conservative: it reports zero when the
    field is locally flat, which is exactly when a point and an area agree.
    """
    i = int(np.abs(lats - lat).argmin())
    j = int(np.abs(lons - lon).argmin())
    i0, i1 = max(0, i - radius_cells), min(field.shape[0], i + radius_cells + 1)
    j0, j1 = max(0, j - radius_cells), min(field.shape[1], j + radius_cells + 1)
    patch = field[i0:i1, j0:j1]
    return float(np.nanstd(patch))


@dataclass
class Instrument:
    """An observing instrument: an operator, a bias and a noise model.

    b_k and sigma_meas are PRIORS until a reference monitor makes them identifiable (Bud2).
    Defaults encode what is currently known: a reference monitor is near-unbiased with small
    measurement noise; a low-cost sensor carries an unknown offset and roughly 30% relative
    noise.
    """

    name: str
    operator: object
    b_k: float = 0.0
    sigma_meas: float = 1.5
    kind: str = "reference"

    @classmethod
    def reference(cls, name, lat, lon, **kw):
        return cls(name, PointOperator(lat, lon, "bilinear"), b_k=0.0, sigma_meas=1.5,
                   kind="reference", **kw)

    @classmethod
    def low_cost(cls, name, lat, lon, b_k=0.0, **kw):
        return cls(name, PointOperator(lat, lon, "bilinear"), b_k=b_k, sigma_meas=4.0,
                   kind="lcs", **kw)

    def predict(self, field: np.ndarray, lats: np.ndarray, lons: np.ndarray) -> tuple[float, float]:
        """Return (expected reading, total sigma) for this instrument given the field."""
        mu = self.operator.apply(field, lats, lons) + self.b_k
        s_rep = 0.0
        op = self.operator
        if isinstance(op, (PointOperator, TimeIntegratedOperator)):
            s_rep = representativeness_sigma(field, lats, lons, op.lat, op.lon)
        sigma = float(np.sqrt(self.sigma_meas ** 2 + s_rep ** 2))
        return mu, sigma


def compare(instrument: Instrument, observed: float, field: np.ndarray,
            lats: np.ndarray, lons: np.ndarray) -> dict:
    """Model-vs-observation comparison THROUGH the observation operator.

    Returns the standardised residual alongside the raw one. The standardised residual is the
    quantity that should be reported: a raw residual conflates a genuine model error with a
    change-of-support artefact, which is precisely the mistake that produced the 72.4% coverage
    result.
    """
    mu, sigma = instrument.predict(field, lats, lons)
    resid = observed - mu
    return {
        "instrument": instrument.name,
        "observed": float(observed),
        "expected": mu,
        "sigma": sigma,
        "residual": float(resid),
        "z": float(resid / sigma) if sigma > 0 else np.nan,
        "areal_mean": float(np.nanmean(field)),
        "point_minus_areal": mu - float(np.nanmean(field)),
    }
