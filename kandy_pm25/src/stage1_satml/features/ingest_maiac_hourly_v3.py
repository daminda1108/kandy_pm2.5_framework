"""
ingest_maiac_hourly_v3.py — MAIAC AOD overpass-resampled to hourly grid.

Reads data/external/tier_c/maiac/maiac_aod_{year}.csv (timestamped overpass
observations from Terra ~10:30 LT + Aqua ~13:30 LT, NaN on cloud-masked passes),
forward-fills onto a strict hourly UTC grid with a staleness companion column.

Output: data/processed/stage1_v3/maiac_hourly_ffilled.parquet
  columns: datetime_utc, aod_maiac, hours_since_aod_overpass
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parents[3]
sys.path.insert(0, str(HERE))

MAIAC_DIR = HERE / "data" / "external" / "tier_c" / "maiac"
OUT = HERE / "data" / "processed" / "stage1_v3" / "maiac_hourly_ffilled.parquet"
OUT.parent.mkdir(parents=True, exist_ok=True)

FFILL_LIMIT_HOURS = 48   # AOD beyond 2 days stale = drop


def main():
    csvs = sorted(MAIAC_DIR.glob("maiac_aod_*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No MAIAC CSVs in {MAIAC_DIR}")

    frames = []
    for p in csvs:
        df = pd.read_csv(p)
        df["datetime_utc"] = pd.to_datetime(df["datetime"], utc=True)
        df = df[["datetime_utc", "aod_055"]].rename(
            columns={"aod_055": "aod_maiac"}
        )
        frames.append(df)
        n_valid = df["aod_maiac"].notna().sum()
        print(f"  {p.name}: {len(df):,} rows, {n_valid:,} valid retrievals "
              f"({n_valid / len(df) * 100:.1f}%), "
              f"mean AOD={df['aod_maiac'].mean():.3f}")

    raw = pd.concat(frames, ignore_index=True).drop_duplicates("datetime_utc")
    raw = raw.sort_values("datetime_utc").reset_index(drop=True)
    print(f"\nConcat: {len(raw):,} rows, "
          f"{raw['datetime_utc'].min()} -> {raw['datetime_utc'].max()}")

    # Round timestamps to nearest hour (Terra/Aqua passes are at xx:30, xx:55 etc.)
    raw["hour_utc"] = raw["datetime_utc"].dt.floor("h")
    obs_per_hour = (raw.dropna(subset=["aod_maiac"])
                       .groupby("hour_utc")["aod_maiac"].mean()
                       .reset_index().rename(columns={"hour_utc": "datetime_utc"}))
    print(f"Valid retrievals collapsed to hourly: {len(obs_per_hour):,} hours "
          f"with at least one AOD observation")

    # Strict hourly grid + ffill ≤ 48 h + staleness counter
    full_idx = pd.date_range(raw["datetime_utc"].min().floor("h"),
                             raw["datetime_utc"].max().ceil("h"),
                             freq="1h", tz="UTC")
    df = pd.DataFrame({"datetime_utc": full_idx}).merge(
        obs_per_hour, on="datetime_utc", how="left"
    )
    obs_present = df["aod_maiac"].notna()
    df["hours_since_aod_overpass"] = (
        (~obs_present).astype(int)
        .groupby(obs_present.cumsum()).cumsum()
    )
    df["aod_maiac"] = df["aod_maiac"].ffill(limit=FFILL_LIMIT_HOURS)

    n_total = len(df)
    n_valid = df["aod_maiac"].notna().sum()
    print(f"\nHourly grid: {n_total:,} rows; "
          f"after ffill ≤{FFILL_LIMIT_HOURS}h: {n_valid:,} valid "
          f"({n_valid / n_total * 100:.1f}%)")
    print(f"Mean AOD (post-ffill): {df['aod_maiac'].mean():.3f}")
    print(f"Median staleness: {df['hours_since_aod_overpass'].median():.0f}h, "
          f"P95: {df['hours_since_aod_overpass'].quantile(0.95):.0f}h")

    df.to_parquet(OUT, index=False)
    print(f"\nWrote {OUT} ({len(df):,} rows × {len(df.columns)} cols)")


if __name__ == "__main__":
    main()
