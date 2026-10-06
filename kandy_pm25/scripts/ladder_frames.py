"""ONE builder for the ladder's Bud0 frame, shared by every ladder analysis.

Why (verification pass 2026-09-25): six ladder scripts each carried their own copy of the frame
assembly. The C7 fix (exclude a city missing from a static stream, F.113) reached three copies
and not the others, and the band/class labels came from an OpenAQ-only manifest in all of them
(CNEMC cities unbanded and classed LCS). A fix applied to one copy of duplicated code does not
reach the rest; the cure is to have one copy.

``build_bud0_frame(stream)`` returns the validated frame for either satellite stream:
  * ``"maiac"`` -- raw MAIAC AOD, daily, missing days left missing (the headline stream);
  * ``"ghap"``  -- GHAP 2019-2022 mean, one value per city (the contaminated comparison stream).

``fit_loco`` is the leave-one-city-out bottom-rung fitter all scripts used (identical copies:
HGB max_iter=300, learning_rate=0.06, random_state=SEED; train >= 1000 rows, target >= 100).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from modular_validation_all import FEATS, build_frame                    # noqa: E402
from src.modular.budgets import require_stream_coverage                  # noqa: E402
from src.modular.schemas import (AOD_RANGE, GEO_CENSORED, require_span_covers,  # noqa: E402
                                 restrict_to_stream_complete, validate_bud0_frame,
                                 validate_daily_stream, validate_static_stream)

MOD = REPO / "data" / "processed" / "modular"
SEED = 20260823
STREAMS = ("maiac", "ghap")


def _cnemc_drivers_pullcity(pool: pd.DataFrame) -> pd.DataFrame:
    """Replace the CNEMC cities' driver columns by the pull_city versions (ladder v2, 2026-09-26),
    so every city carries drivers from ONE function. Refuses if a CNEMC city has no file."""
    d = MOD / "drivers_cnemc_pullcity"
    drv = ["temperature_2m", "u_component_of_wind_10m", "v_component_of_wind_10m", "wind",
           "boundary_layer_height"]
    cn = pool[pool.src == "CNEMC"].drop(columns=[c for c in drv if c in pool.columns])
    parts = []
    for slug in cn.city.unique():
        f = d / f"{slug}.csv"
        if not f.exists():
            raise SystemExit(f"pull_city drivers missing for CNEMC city {slug}: run "
                             "scripts/cnemc_drivers_pullcity.py")
        x = pd.read_csv(f)
        x["date"] = pd.to_datetime(x.date)
        parts.append(x.assign(city=str(slug))[["city", "date", *drv]])
    new = pd.concat(parts, ignore_index=True).drop_duplicates(["city", "date"])
    cn = cn.merge(new, on=["city", "date"], how="left")
    return pd.concat([pool[pool.src != "CNEMC"], cn[pool.columns]], ignore_index=True)


def _drivers_v2(pool: pd.DataFrame) -> pd.DataFrame:
    """Ladder v2 (2026-09-27): EVERY city's driver columns from drivers_v2/{city}.csv, pulled by
    the fixed pull_city (window head and tail no longer dropped). Refuses on a missing file."""
    d = MOD / "drivers_v2"
    drv = ["temperature_2m", "u_component_of_wind_10m", "v_component_of_wind_10m", "wind",
           "boundary_layer_height"]
    parts = []
    for city in pool.city.unique():
        f = d / f"{city}.csv"
        if not f.exists():
            raise SystemExit(f"drivers_v2 missing for {city}: run scripts/drivers_v2_pull.py "
                             "--panel discovery")
        x = pd.read_csv(f)
        x["date"] = pd.to_datetime(x.date)
        parts.append(x.assign(city=str(city))[["city", "date", *drv]])
    new = pd.concat(parts, ignore_index=True).drop_duplicates(["city", "date"])
    out = pool.drop(columns=[c for c in drv if c in pool.columns]).merge(
        new, on=["city", "date"], how="left")
    return out[list(pool.columns)]


def build_bud0_frame(stream: str = "maiac", verbose: bool = True, cnemc_drivers: str = "met_raw"):
    """Return (st, p, met, geo_f, sat_feats).

    st        -- {city: station frame}, restricted to the cities left in ``p``
    p         -- the validated city-day frame with drivers, static geography and the satellite stream
    met       -- reanalysis driver columns
    geo_f     -- static-geography columns
    sat_feats -- ["aod"] for MAIAC, ["sat_level"] for GHAP
    """
    if stream not in STREAMS:
        raise ValueError(f"stream must be one of {STREAMS}")
    st, pool = build_frame(pd.read_csv(MOD / "validation_sample.csv"),
                           pd.read_csv(MOD / "openaq_manifest.csv"))
    pool = pool.copy()
    pool["date"] = pd.to_datetime(pool.date)
    pool["city"] = pool.city.astype(str)
    if cnemc_drivers == "v2":
        pool = _drivers_v2(pool)                    # all cities, fixed pull (2026-09-27)
    elif cnemc_drivers == "pull_city":
        pool = _cnemc_drivers_pullcity(pool)
    elif cnemc_drivers != "met_raw":
        raise ValueError("cnemc_drivers must be 'met_raw' (v1), 'pull_city' or 'v2'")
    doy = pool.date.dt.dayofyear
    pool["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    pool["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    met = [c for c in FEATS if c in pool.columns]
    pool = pool.dropna(subset=met + ["pm25_city"]).copy()
    pool["city"] = pool.city.astype(str)

    geo = pd.read_csv(MOD / "bud0_static_geo.csv"); geo["city"] = geo.city.astype(str)
    geo = validate_static_stream(geo, name="bud0_static_geo", allow_null=GEO_CENSORED)
    geo_f = [c for c in geo.columns if c not in ("city", "geo_n_stations")]
    sat = pd.read_csv(MOD / "bud0_satellite_level.csv"); sat["city"] = sat.city.astype(str)

    # C7 / F.113: a city absent from an admitted static stream is excluded by name.
    pool = restrict_to_stream_complete(pool, geo=geo, sat=sat if stream == "ghap" else None)
    p = pool.merge(geo, on="city", how="left")

    if stream == "maiac":
        aod = pd.read_csv(MOD / "bud0_maiac_aod.csv")
        aod["city"] = aod.city.astype(str); aod["date"] = pd.to_datetime(aod.date)
        aod = validate_daily_stream(aod, name="bud0_maiac_aod", column="aod",
                                    value_range=AOD_RANGE)
        require_span_covers(aod, p, name="bud0_maiac_aod")            # gotcha #85
        p = p.merge(aod[["city", "date", "aod"]], on=["city", "date"], how="left")
        require_stream_coverage(p, "aod", unit="city", min_unit_fraction=0.10,
                                min_units_covered=0.90)
        sat_feats = ["aod"]
        p = validate_bud0_frame(p, geo=geo, sat=None, met=met, static=geo_f,
                                daily={"aod": AOD_RANGE})
    else:
        p = p.merge(sat, on="city", how="left")
        sat_feats = ["sat_level"]
        p = validate_bud0_frame(p, geo=geo, sat=sat, met=met, static=geo_f + ["sat_level"])

    keep = set(p.city)
    st = {str(k): v for k, v in st.items() if str(k) in keep}
    if verbose:
        print(f"    [{stream}] frame {len(p):,} city-days, {p.city.nunique()} cities, "
              f"{len(met) + len(geo_f) + len(sat_feats)} Bud0c predictors", flush=True)
    return st, p, met, geo_f, sat_feats


def fit_loco(pool: pd.DataFrame, feats: list[str], seed: int = SEED,
             label: str | None = None) -> pd.DataFrame:
    """Leave-one-city-out prediction of the city-daily mean from ``feats``."""
    out = []
    for city in sorted(pool.city.unique()):
        tr, te = pool[pool.city != city], pool[pool.city == city]
        assert city not in set(tr.city), "LOCO violated"
        if len(tr) < 1000 or len(te) < 100:
            continue
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, random_state=seed)
        m.fit(tr[feats], tr.pm25_city)
        out.append(pd.DataFrame({"city": city, "date": te.date.values,
                                 "bud0": m.predict(te[feats])}))
    d = pd.concat(out, ignore_index=True)
    if label:
        print(f"    {label:<28} {d.city.nunique()} cities, {len(feats)} features", flush=True)
    return d
