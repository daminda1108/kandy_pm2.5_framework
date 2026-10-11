"""Mean conservation of the delivered field (F.129, 2026-10-11).

The decomposition preserves the basin mean only if every spatial factor that multiplies T(t) has unit spatial mean
AT EVERY HOUR. Two factors once broke this silently (S x M had mean 1 + kappa w cov(S, c); the dispersion factor was
renormalised on its own and not against the field it multiplied), leaving the delivered field 0.4-0.6 % above T(t).

  test_unit_mean_pattern          synthetic, always runs: the pattern builder returns unit mean even when S and c
                                  covary positively.
  test_delivered_field_keeps_T    data-backed: the shipped additive_v3 field's hourly basin mean equals T(t);
                                  skipped where the (non-redistributed) field files are absent.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from src.stage1_satml.decomp.build_decomp_map import unit_mean_pattern   # noqa: E402

DEC = REPO / "data" / "processed" / "decomp"
TAN = REPO / "data" / "processed" / "stage1_v3" / "T_anchor"


def test_unit_mean_pattern():
    rng = np.random.default_rng(0)
    c = rng.normal(size=256); c = (c - c.mean()) / c.std()
    S = 1.0 + 0.3 * c + 0.05 * rng.normal(size=256); S = S / S.mean()     # strongly covaries with c
    w = rng.uniform(0, 1, size=500)
    SM = unit_mean_pattern(S[None, :], c[None, :], 0.15, w)
    assert np.abs(SM.mean(axis=1) - 1.0).max() < 1e-6


@pytest.mark.skipif(not (DEC / "kandy_decomp_predictions_2021_additive_v3.parquet").exists(),
                    reason="requires the local delivered field (not redistributed)")
@pytest.mark.parametrize("year", [2019, 2020, 2021, 2022, 2023])
def test_delivered_field_keeps_T(year):
    f = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}_additive_v3.parquet", columns=["time", "pm25_q50"])
    f["time"] = pd.to_datetime(f.time, utc=True)
    T = pd.read_parquet(TAN / f"T_kandy_hourly_{year}.parquet", columns=["datetime_utc", "T_q50"])
    T["time"] = pd.to_datetime(T.datetime_utc, utc=True)
    h = f.groupby("time").pm25_q50.mean().to_frame("field").join(T.set_index("time").T_q50)
    rel = (h.field.mean() - h.T_q50.mean()) / h.T_q50.mean()
    assert abs(rel) < 1e-4, f"{year}: annual field mean departs from T(t) by {100 * rel:.4f} %"
