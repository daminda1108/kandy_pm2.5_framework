"""
ingest_cams_hourly_v3.py — Interpolate CAMS EAC4 3-hourly NetCDFs to 1-hourly.

Reads data/raw/cams/cams_pm25_{year}.nc, extracts the Kandy grid cell,
linearly interpolates to hourly cadence (with a small staleness flag for
the 3-hour gap), and writes data/processed/stage1_v3/cams_hourly_interpolated.parquet.

CAMS native cadence: 3-hourly. Units: kg m⁻³ -> ×1e9 -> µg m⁻³.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

CAMS_DIR = HERE / "data" / "raw" / "cams"
OUT = HERE / "data" / "processed" / "stage1_v3" / "cams_hourly_interpolated.parquet"
OUT.parent.mkdir(parents=True, exist_ok=True)

KANDY_LAT = 7.2906
KANDY_LON = 80.6337
KG_M3_TO_UG_M3 = 1e9


def main():
    frames = []
    for nc_path in sorted(CAMS_DIR.glob("cams_pm25_*.nc")):
        year = nc_path.stem.split("_")[-1]
        ds = xr.open_dataset(nc_path)

        # nearest grid cell to Kandy
        ds_pt = ds.sel(latitude=KANDY_LAT, longitude=KANDY_LON, method="nearest")
        df = ds_pt.to_dataframe().reset_index()

        # normalise time + var name
        time_col = "valid_time" if "valid_time" in df.columns else "time"
        df = df[[time_col, "pm2p5"]].rename(
            columns={time_col: "datetime_utc", "pm2p5": "cams_pm25_raw_kg_m3"}
        )
        df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True)
        df["cams_pm25_raw"] = df["cams_pm25_raw_kg_m3"] * KG_M3_TO_UG_M3
        df = df.drop(columns="cams_pm25_raw_kg_m3")

        frames.append(df)
        print(f"  {nc_path.name}: {len(df):4d} 3-hourly rows, "
              f"mean={df['cams_pm25_raw'].mean():6.2f} µg/m³")

    if not frames:
        print("No CAMS NCs found.")
        return

    cams = pd.concat(frames, ignore_index=True).drop_duplicates("datetime_utc")
    cams = cams.sort_values("datetime_utc").reset_index(drop=True)
    print(f"\nConcat: {len(cams):,} 3-hourly rows, "
          f"{cams['datetime_utc'].min()} -> {cams['datetime_utc'].max()}")

    # reindex to hourly + linear interp + staleness
    cams = cams.set_index("datetime_utc")
    hourly_idx = pd.date_range(cams.index.min(), cams.index.max(),
                               freq="1h", tz="UTC")
    cams_h = cams.reindex(hourly_idx)
    cams_h["cams_pm25_raw"] = cams_h["cams_pm25_raw"].interpolate(
        method="time", limit=3
    )
    cams_h["hours_since_cams_obs"] = (
        cams_h["cams_pm25_raw"]
        .notna()  # use original-grid presence flag from re-index
        .pipe(lambda s: s.where(s).cumsum())  # placeholder
    )
    # cleaner staleness: distance to nearest 3-hourly tick
    cams_h["hours_since_cams_obs"] = (
        ((cams_h.index.hour % 3) <= 1).astype(int) * 0
        + ((cams_h.index.hour % 3) == 1).astype(int) * 1
        + ((cams_h.index.hour % 3) == 2).astype(int) * 2
    )

    cams_h = cams_h.reset_index().rename(columns={"index": "datetime_utc"})
    cams_h["datetime_utc"] = pd.to_datetime(cams_h["datetime_utc"], utc=True)

    n_nan = cams_h["cams_pm25_raw"].isna().sum()
    print(f"Hourly reindex: {len(cams_h):,} rows; "
          f"{n_nan:,} NaN ({n_nan / len(cams_h) * 100:.2f}%)")
    print(f"Hourly mean: {cams_h['cams_pm25_raw'].mean():.2f} µg/m³ "
          f"(range {cams_h['cams_pm25_raw'].min():.2f} – "
          f"{cams_h['cams_pm25_raw'].max():.2f})")

    cams_h.to_parquet(OUT, index=False)
    print(f"\nWrote {OUT} ({len(cams_h):,} rows × {len(cams_h.columns)} cols)")


if __name__ == "__main__":
    main()
