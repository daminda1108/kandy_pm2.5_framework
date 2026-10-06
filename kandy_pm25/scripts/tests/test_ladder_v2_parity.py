"""ladder_v2 at v1 settings must reproduce the stored v1 MAIAC ladder exactly (Bud0c bottom).

Slow (one leave-one-city-out fit, ~3-5 min): run explicitly,
    .venv/Scripts/python.exe -m pytest -q scripts/tests/test_ladder_v2_parity.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

from ladder_v2 import run   # noqa: E402


def test_v2_at_v1_settings_reproduces_v1():
    S, _, _ = run(stream="maiac", splits=1, bag=1, w_mode="cv", complete=False, geo="sites",
                  nboot=200, prospective=False, cnemc_drivers="met_raw")
    v1 = pd.read_csv(REPO / "data/processed/modular/ladder_maiac.csv", dtype={"city": str})
    v1 = v1[v1.bottom == "Bud0c"].set_index("city")
    v2 = S[S.arm == "reconstruction"].set_index("city")
    common = v1.index.intersection(v2.index)
    assert len(common) == len(v1) == 47
    for r in ("Bud0", "Bud1", "Bud2", "Bud3"):
        a, b = v1.loc[common, f"rmse_{r}"].to_numpy(), v2.loc[common, f"{r}_rmse"].to_numpy()
        ok = np.isfinite(a) | np.isfinite(b)
        np.testing.assert_allclose(a[ok], b[ok], rtol=0, atol=1e-9, err_msg=r)
