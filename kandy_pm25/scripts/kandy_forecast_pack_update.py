"""kandy_forecast_pack_update.py — bake the constants the live forecast runner
needs into kandy_webapp/live/model/pack.json (2026-07-27).

The GitHub Action that issues the live forecast runs in the WEBAPP repo, which
carries no model data. Anything it needs from the locked chain has to be a
constant in pack.json. This script derives those constants HERE, from the locked
artifacts, so they are traceable rather than transcribed.

What it writes:

  bt_ratio_month[12]   Monthly B/T ratio of the LOCKED chain (2019-2023). The
                       forecast background is B = T_forecast * ratio[month], the
                       same rule the 2024-2026 extension tier already uses. A FLAT
                       background silently kills the local field in the monsoon
                       (gotcha #61): with the increment-split form the pattern only
                       structures hours where T > B, so an unseasonal B pushes the
                       field featureless exactly when Kandy is cleanest.

  wind_calib           The B2 thermal valley-circulation parameters (disclosed
                       method-transfer prior at Kandy) so the runner applies the
                       SAME wind the shipped payload does.

  wind_lib             dirs/speeds of the WindNinja library, so the runner can
                       compute the blend indices (i0, wd0, cs0, wn) with the same
                       math as webapp_export._wind_blend_params. Parity matters:
                       the browser blends the shipped library with these weights,
                       and a forecast hour must not use a second implementation.

  eps_floor            The additive_v3 ventilated-hour pattern floor, so a forecast
                       hour reconstructs through the identical field equation.

Run:  .venv/Scripts/python.exe scripts/kandy_forecast_pack_update.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
STG = REPO / "data" / "processed" / "stage1_v3"
DEC = REPO / "data" / "processed" / "decomp"
PINN = REPO / "data" / "processed" / "pinn_inputs"
PACK = REPO.parent / "kandy_webapp" / "live" / "model" / "pack.json"
WIND_CALIB = REPO / "results" / "figures" / "kandy_extension" / "b2_kandy_wind_prior.json"
WIDEN = DEC / "kandy_forecast_ood_widening.json"
EPS_FLOOR = 2.573          # additive_v3, transferred relative form (see gotcha #65)


def bt_ratio_month() -> list[float]:
    """Monthly B/T of the locked chain — identical definition to
    kandy_driver_tier_build._locked_b_over_t()."""
    rows = []
    for y in range(2019, 2024):
        tf = STG / "T_anchor" / f"T_kandy_hourly_{y}.parquet"
        bf = DEC / f"B_background_hourly_{y}_v2.parquet"
        if not (tf.exists() and bf.exists()):
            raise SystemExit(f"missing locked artifact for {y}: {tf.name} / {bf.name}")
        T = pd.read_parquet(tf); T["t"] = pd.to_datetime(T.datetime_utc, utc=True)
        B = pd.read_parquet(bf); B["t"] = pd.to_datetime(B.datetime_utc, utc=True)
        rows.append(T[["t", "T_q50"]].merge(B[["t", "B"]], on="t"))
    d = pd.concat(rows)
    gm = d.groupby(d.t.dt.month).agg(Tm=("T_q50", "mean"), Bm=("B", "mean"))
    r = (gm["Bm"] / gm["Tm"]).reindex(range(1, 13)).ffill().bfill()
    return [round(float(v), 5) for v in r]


def wind_lib() -> dict:
    lib = np.load(PINN / "windninja_library.npz")
    return {"dirs": [float(v) for v in lib["dirs"]],
            "speeds": [float(v) for v in lib["speeds"]]}


def main() -> None:
    pack = json.loads(PACK.read_text(encoding="utf-8"))

    pack["bt_ratio_month"] = bt_ratio_month()
    pack["bt_ratio_note"] = (
        "Monthly B/T ratio of the locked 2019-2023 chain. The forecast background is "
        "B = T * ratio[month] — the seasonal partition the extension tier inherits. A "
        "flat background would leave the monsoon months with T < B and flatten the "
        "local field (gotcha #61).")
    pack["wind_lib"] = wind_lib()
    pack["eps_floor"] = EPS_FLOOR
    if WIND_CALIB.exists():
        pack["wind_calib"] = json.loads(WIND_CALIB.read_text(encoding="utf-8"))["params"]
    if WIDEN.exists():
        w = json.loads(WIDEN.read_text(encoding="utf-8"))
        pack.setdefault("ood_widen", {})["k"] = w["k"]
        pack["ood_widen"]["measured_coverage_unwidened"] = w["measured_coverage_unwidened"]
        pack["ood_widen"]["n_days"] = w["n_days"]

    PACK.write_text(json.dumps(pack, indent=1, ensure_ascii=False), encoding="utf-8")
    print("bt_ratio_month:", pack["bt_ratio_month"])
    print("wind_lib      :", pack["wind_lib"])
    print("wind_calib    :", "yes" if "wind_calib" in pack else "MISSING")
    print(f"wrote {PACK}")


if __name__ == "__main__":
    main()
