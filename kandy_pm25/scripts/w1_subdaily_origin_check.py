"""w1_subdaily_origin_check.py — DRY RUN for W1 of the 2026-08-18 pre-registration.

Computes B(t) both ways -- daily-mode class (shipped) and native 6-hourly class (W1) -- and
reports the registered gates WITHOUT writing any product. Nothing downstream is touched until
the gates are read.

  W1-G3  annual f moves by < 0.02
  W1-G4  coherence-cap activation does not increase
  W1-G5  if the locked tier moves beyond the QA tolerance, W1 is confined to the shipped tier

Usage: python scripts/w1_subdaily_origin_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_additive_field_v2 as bld  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
TANCHOR = REPO / "data" / "processed" / "stage1_v3" / "T_anchor"


def t_series(year: int) -> pd.Series:
    t = pd.read_parquet(TANCHOR / f"T_kandy_hourly_{year}.parquet",
                        columns=["datetime_utc", "T_q50"])
    return t.set_index("datetime_utc").T_q50


def run(year: int, subdaily: bool) -> pd.DataFrame:
    bld.SUBDAILY_ORIGIN = subdaily
    vand = pd.read_csv(REPO / "data" / "processed" / "stage1_v3" /
                       "vandonkelaar_kandy_annual.csv", index_col=0)
    b_annual = (1 - bld.FRAC_LOCAL_YEAR[year]) * float(vand.loc[year, "L_corrected"])   # the level T(t) is anchored to (F.132)
    return bld.build_B_v2(year, b_annual)


def main() -> None:
    rows = []
    for y in bld.YEARS:
        T = t_series(y)
        print(f"\n--- {y} ---")
        print("  [shipped, daily mode]")
        b0 = run(y, False).set_index("datetime_utc").B.reindex(T.index)
        print("  [W1, 6-hourly]")
        b1 = run(y, True).set_index("datetime_utc").B.reindex(T.index)

        d = (b1 - b0).abs()
        rows.append({
            "year": y,
            "B_mean_shipped": b0.mean(), "B_mean_w1": b1.mean(),
            "f_shipped": 1 - b0.mean() / T.mean(), "f_w1": 1 - b1.mean() / T.mean(),
            "hours_changed_pct": 100 * (d > 1e-9).mean(),
            "max_abs_dB": d.max(), "mean_abs_dB": d.mean(),
            "zero_local_pct_shipped": 100 * (b0 >= T).mean(),
            "zero_local_pct_w1": 100 * (b1 >= T).mean(),
        })

    r = pd.DataFrame(rows)
    r["df"] = r.f_w1 - r.f_shipped
    pd.set_option("display.width", 200, "display.max_columns", 30)
    print("\n=== W1 dry run: sub-daily origin vs daily mode ===")
    print(r.round(4).to_string(index=False))

    g3 = bool(r.df.abs().max() < 0.02)
    g4 = bool((r.zero_local_pct_w1 <= r.zero_local_pct_shipped + 1e-9).all())
    print(f"\nW1-G3 (|df| < 0.02):                       "
          f"{'PASS' if g3 else 'FAIL'}  max |df| = {r.df.abs().max():.4f}")
    print(f"W1-G4 (cap activation does not increase):  {'PASS' if g4 else 'FAIL'}")
    print(f"annual B mean preserved (max drift):       {(r.B_mean_w1 - r.B_mean_shipped).abs().max():.2e}")


if __name__ == "__main__":
    main()
