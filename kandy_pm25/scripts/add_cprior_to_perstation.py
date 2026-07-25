"""add_cprior_to_perstation.py — attach the GEOS-CF prior to a per-station parquet.

WHY. `t_anchor._anchor_series` reads a `c_prior` column from the city's per-station
parquet and uses it for one thing: the ROW-MEAN prior ratio
(`pm25.mean() / c_prior.mean()`, gotcha #39 — row-mean, not timestamp-mean, because a
growing network otherwise drifts the ratio). Cities rebuilt through
`rebuild_perstation_extended.py` already carry it; older `*_stage3_perstation.parquet`
files (Bogotá, Mexico City) predate that schema and do not, which fails as
`ArrowInvalid: No match for FieldRef.Name(c_prior)`.

This attaches the column from the same area-mean GEOS-CF table the rest of the
pipeline uses (`drivers.geos_cf_prior`), joined on the hour. Idempotent: it refuses to
run twice unless --force. Only ADDS a column; nothing existing is modified.

Usage:  python scripts/add_cprior_to_perstation.py --city bogota
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    from city_config import citypack
    from src.transfer_validation import drivers

    cp = citypack(a.city)
    p = cp.station_parquet()
    df = pd.read_parquet(p)
    print(f"{a.city}: {p.name}  {len(df):,} rows")
    if "c_prior" in df.columns and not a.force:
        n = int(df.c_prior.notna().sum())
        print(f"  c_prior already present ({n:,} non-null) — nothing to do (--force to redo)")
        return

    g = drivers.geos_cf_prior(cp)          # area-mean hourly prior, column pm25_prior
    g["hr"] = pd.to_datetime(g.datetime, errors="coerce").dt.tz_localize(None).dt.floor("h")
    gp = g.dropna(subset=["hr"]).groupby("hr")["pm25_prior"].mean()

    hr = (pd.to_datetime(df["datetime_utc"], errors="coerce", utc=True)
            .dt.tz_localize(None).dt.floor("h"))
    df["c_prior"] = hr.map(gp).to_numpy(dtype=float)
    ok = int(np.isfinite(df.c_prior).sum())
    print(f"  GEOS-CF prior hours: {len(gp):,}  -> matched {ok:,}/{len(df):,} rows "
          f"({100*ok/max(len(df),1):.1f}%)")
    if ok == 0:
        raise SystemExit("no rows matched the prior — check the driver year coverage")
    # sanity: the ratio this column exists to produce
    both = df.dropna(subset=["pm25", "c_prior"])
    print(f"  row-mean ratio pm25/c_prior = "
          f"{both.pm25.mean()/both.c_prior.mean():.4f}  (gotcha #39 convention)")
    df.to_parquet(p, index=False)
    print(f"  wrote {p.name} (+c_prior)")


if __name__ == "__main__":
    main()
