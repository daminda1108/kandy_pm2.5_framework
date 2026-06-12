"""drivers.py — area-mean meteorological / prior driver loaders per CityPack.

The transfer-validation recipe needs three things at the *area* level (not just at
stations):
  * GEOS-CF area-mean hourly PM2.5 prior  → B(t) seasonal/daily shape + T(t) prior
  * ERA5 boundary-layer height (BLH)       → M confinement modulation w(BLH),
                                             A_transport ventilation
  * ERA5-Land 10 m winds + T2m             → A_transport advection, T(t) features

For Xichang and Chandigarh these were already exported by the v15 pipeline to
`data/external/{slug}/{geos_cf,zpbl_gee,era5_land_gee}/{slug}_*_{year}.csv`
(area-mean time series over the city bbox). This module concatenates the per-year
CSVs into tidy hourly frames, schema-tolerant to the small naming differences
across export vintages. NO network, NO GEE — pure read of on-disk artifacts.

CSV schemas (verified 2026-06-10):
  geos_cf:      datetime, PM25_RH35_GCC
  zpbl_gee:     datetime, boundary_layer_height
  era5_land:    datetime, u_component_of_wind_10m, v_component_of_wind_10m,
                temperature_2m, dewpoint_temperature_2m, total_precipitation_hourly

Cities whose area-mean CSVs are absent (Kathmandu, Medellin) fall back to the
station-mean of the per-station parquet's merged columns as an area proxy — flagged
in the returned frame's `.attrs['source']` so the caller knows the provenance.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[2]
EXT = REPO / "data" / "external"

# canonical output column ← accepted source column names (first match wins)
_GEOS_PM = ("PM25_RH35_GCC", "pm25", "PM25", "geos_cf_pm25")
_BLH = ("boundary_layer_height", "blh", "zpbl", "pbl")
_U10 = ("u_component_of_wind_10m", "u10", "u_compon")
_V10 = ("v_component_of_wind_10m", "v10", "v_compon")
_T2M = ("temperature_2m", "t2m")


def _read_years(folder: Path, pattern: str):
    """Concat all per-year CSVs matching pattern, parse datetime, sort. Empty → None."""
    import pandas as pd
    files = sorted(folder.glob(pattern)) if folder.exists() else []
    if not files:
        return None
    frames = []
    for f in files:
        df = pd.read_csv(f)
        dt = next((c for c in df.columns if c.lower() in ("datetime", "time", "date")), df.columns[0])
        df = df.rename(columns={dt: "datetime"})
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        frames.append(df.dropna(subset=["datetime"]))
    out = pd.concat(frames, ignore_index=True).drop_duplicates("datetime").sort_values("datetime")
    return out.reset_index(drop=True)


def _pick(df, names: tuple[str, ...]) -> Optional[str]:
    low = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    return None


def geos_cf_prior(cp) -> "object":
    """Area-mean GEOS-CF hourly PM2.5 prior → frame[datetime, pm25_prior].

    Falls back to station-mean c_prior from the per-station parquet if no area CSV
    exists (Kathmandu/Medellin). Sets .attrs['source'].
    """
    import pandas as pd
    df = _read_years(EXT / cp.slug / "geos_cf", f"{cp.slug}_geos_cf_*.csv")
    if df is not None:
        col = _pick(df, _GEOS_PM)
        out = df[["datetime", col]].rename(columns={col: "pm25_prior"})
        out.attrs["source"] = "geos_cf_area_csv"
        return out
    # fallback: station-mean of merged c_prior
    st = pd.read_parquet(cp.station_parquet(), columns=["datetime_utc", "c_prior"])
    st["datetime"] = pd.to_datetime(st["datetime_utc"], errors="coerce").dt.tz_localize(None)
    out = (st.dropna(subset=["datetime", "c_prior"]).groupby("datetime")["c_prior"]
             .mean().reset_index().rename(columns={"c_prior": "pm25_prior"}))
    out.attrs["source"] = "station_mean_cprior_PROXY"
    return out


def blh(cp) -> "object":
    """Area-mean ERA5 boundary-layer height → frame[datetime, blh_m]."""
    import pandas as pd
    df = _read_years(EXT / cp.slug / "zpbl_gee", f"{cp.slug}_zpbl_*.csv")
    if df is not None:
        col = _pick(df, _BLH)
        out = df[["datetime", col]].rename(columns={col: "blh_m"})
        out.attrs["source"] = "zpbl_area_csv"
        return out
    st = pd.read_parquet(cp.station_parquet(), columns=["datetime_utc", "blh"])
    st["datetime"] = pd.to_datetime(st["datetime_utc"], errors="coerce").dt.tz_localize(None)
    out = (st.dropna(subset=["datetime", "blh"]).groupby("datetime")["blh"]
             .mean().reset_index().rename(columns={"blh": "blh_m"}))
    out.attrs["source"] = "station_mean_blh_PROXY"
    return out


def era5_winds(cp) -> "object":
    """Area-mean ERA5-Land 10 m winds + T2m → frame[datetime, u10, v10, t2m]."""
    import pandas as pd
    df = _read_years(EXT / cp.slug / "era5_land_gee", f"{cp.slug}_era5land_*.csv")
    if df is not None:
        u, v, t = _pick(df, _U10), _pick(df, _V10), _pick(df, _T2M)
        out = df[["datetime", u, v, t]].rename(columns={u: "u10", v: "v10", t: "t2m"})
        out.attrs["source"] = "era5land_area_csv"
        return out
    st = pd.read_parquet(cp.station_parquet(), columns=["datetime_utc", "u10", "v10", "t2m"])
    st["datetime"] = pd.to_datetime(st["datetime_utc"], errors="coerce").dt.tz_localize(None)
    out = (st.dropna(subset=["datetime"]).groupby("datetime")[["u10", "v10", "t2m"]]
             .mean().reset_index())
    out.attrs["source"] = "station_mean_era5_PROXY"
    return out


def _selftest() -> int:
    from .citypack import get
    ok = True
    for slug in ("xichang", "chandigarh", "kathmandu", "medellin"):
        cp = get(slug)
        row = {"slug": slug}
        for label, fn in (("geos", geos_cf_prior), ("blh", blh), ("wind", era5_winds)):
            try:
                d = fn(cp)
                row[label] = f"{len(d):>6} rows [{d.attrs.get('source','?')}] " \
                             f"{d.datetime.min().date()}..{d.datetime.max().date()}"
            except Exception as e:  # noqa: BLE001
                row[label] = f"ERR {type(e).__name__}: {e}"
                ok = False
        print(row["slug"])
        for k in ("geos", "blh", "wind"):
            print(f"   {k:5s} {row[k]}")
    print("\nDRIVERS SELFTEST", "PASS" if ok else "ERRORS")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())
