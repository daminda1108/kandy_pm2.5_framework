"""One estimand, one value (2026-10-11). The local fraction f = 1 - mean(B)/mean(T) is computed by three scripts:
the partition report (the headline), the cap-specification sweep and the humidity scenario. A fifth external review
found the thesis quoting 0.483 from one and 0.442 from another: the scenario built B from the raw satellite level while
T(t) had been re-anchored (F.132), and the headline file predated three model changes. This test fails if the
production value disagrees between them. Skipped where the derived files are absent (not redistributed).

2026-10-12 (F.137): the humidity scenario is defined on the anchor as sharpened to the FECT sensors, i.e. the products
before the daily cycle was refitted to the CEA station, kept in decomp/backup_fect_diurnal_2026-10-12. Its production arm
must therefore agree with the partition of THAT backup, while the current headline must agree with the cap sweep."""
import json
from pathlib import Path

import pandas as pd
import pytest

DEC = Path(__file__).resolve().parents[2] / "data" / "processed" / "decomp"
BAK = DEC / "backup_fect_diurnal_2026-10-12"
FILES = [DEC / "kandy_partition_v2.json", DEC / "rh_scenario.csv", DEC / "f_sensitivity.csv",
         BAK / "kandy_partition_v2.json"]


@pytest.mark.skipif(not all(f.exists() for f in FILES), reason="requires the local derived files")
def test_production_f_agrees():
    head = json.load(open(FILES[0], encoding="utf-8"))["summary"]["f_anchored_mean"]
    sw = pd.read_csv(FILES[2])
    base = sw[(sw.day == "utc") & (sw.stat == "min")].f.mean()
    assert abs(head - base) < 1e-3, (head, base)
    head_before = json.load(open(FILES[3], encoding="utf-8"))["summary"]["f_anchored_mean"]
    rh = pd.read_csv(FILES[1])
    scen = rh[rh.scenario == "production"].f.mean()
    assert abs(head_before - scen) < 1e-3, (head_before, scen)
