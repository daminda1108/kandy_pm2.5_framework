"""Structural contracts on the ladder frames (src/modular/schemas.py).

Each negative test replays a failure the project actually had, on a small synthetic frame, and
asserts the schema rejects it. The positive control is the real MAIAC frame, which must pass
(checked by running scripts/ladder_maiac.py:build_maiac_frame, not here: it reads 30k rows).
"""
import numpy as np
import pandas as pd
import pandera.errors as pe
import pytest

from src.modular.schemas import (AOD_RANGE, require_span_covers, validate_daily_stream,
                                 validate_ladder_frame, validate_static_stream)

MET = ["temperature_2m", "boundary_layer_height", "wind"]
STATIC = ["ndvi_100", "dist_major_km"]
WHY = {"dist_major_km": "censored: no major road within the query extent"}


def _frame(n_city=3, n_day=120, start="2023-01-01"):
    rng = np.random.default_rng(0)
    rows = []
    for c in range(n_city):
        d = pd.date_range(start, periods=n_day, freq="D")
        rows.append(pd.DataFrame({
            "city": str(c), "date": d, "pm25_city": rng.uniform(5, 60, n_day),
            "temperature_2m": rng.uniform(280, 305, n_day),
            "boundary_layer_height": rng.uniform(200, 2000, n_day),
            "wind": rng.uniform(0, 8, n_day),
            "ndvi_100": 0.1 * (c + 1), "dist_major_km": 0.5 + c,
            "aod": rng.uniform(0.1, 1.5, n_day)}))
    return pd.concat(rows, ignore_index=True)


def _ok(df, **kw):
    return validate_ladder_frame(df, met=MET, static=STATIC, daily={"aod": AOD_RANGE}, **kw)


def test_clean_frame_passes():
    _ok(_frame())


def test_join_that_duplicates_rows_is_caught():
    """A stream file with a repeated key multiplies city-days on merge."""
    df = _frame()
    with pytest.raises(pe.SchemaErrors, match="duplicate key"):
        _ok(pd.concat([df, df.iloc[:5]], ignore_index=True))


def test_gotcha_85_wrong_period_stream_is_caught_before_merge():
    """MAIAC pulled 2019-2022 against a frame spanning 2023+: merge would be ~0% covered."""
    frame = _frame(start="2023-01-01")
    stream = _frame(start="2019-01-01")[["city", "date", "aod"]]
    with pytest.raises(pe.SchemaError, match="gotcha #85"):
        require_span_covers(stream, frame, name="maiac")


def test_matching_period_stream_passes_span_check():
    frame = _frame()
    require_span_covers(frame[["city", "date", "aod"]], frame, name="maiac")


def test_c7_city_missing_from_static_stream_is_caught():
    """A city absent from the static stream arrives as NaN on every one of its rows."""
    df = _frame()
    df.loc[df.city == "1", "ndvi_100"] = np.nan
    with pytest.raises(pe.SchemaErrors, match="ndvi_100"):
        _ok(df, allow_null=WHY)


def test_static_feature_varying_within_city_means_wrong_join_key():
    df = _frame()
    df.loc[df.index[:10], "ndvi_100"] = 0.9
    with pytest.raises(pe.SchemaErrors, match="wrong join key"):
        _ok(df)


def test_celsius_temperature_is_caught():
    df = _frame()
    df["temperature_2m"] -= 273.15
    with pytest.raises(pe.SchemaErrors, match="temperature_2m"):
        _ok(df)


def test_aod_sentinel_is_caught():
    df = _frame()
    df.loc[3, "aod"] = -999.0
    with pytest.raises(pe.SchemaErrors, match="aod"):
        _ok(df)


def test_aod_cloud_gaps_are_allowed():
    """NaN AOD is cloud, not a defect -- coverage is require_stream_coverage's job."""
    df = _frame()
    df.loc[df.index[::2], "aod"] = np.nan
    _ok(df)


def test_censored_static_needs_a_declared_reason():
    df = _frame()
    df.loc[df.city == "2", "dist_major_km"] = np.nan
    with pytest.raises(pe.SchemaErrors, match="dist_major_km"):
        _ok(df)                                    # undeclared -> rejected
    _ok(df, allow_null=WHY)                        # declared -> accepted
    with pytest.raises(ValueError, match="written reason"):
        _ok(df, allow_null={"dist_major_km": "ok"})


def test_static_stream_file_duplicate_city_is_caught():
    geo = pd.DataFrame({"city": ["1", "1", "2"], "ndvi_100": [0.1, 0.2, 0.3]})
    with pytest.raises(pe.SchemaErrors):
        validate_static_stream(geo, name="geo")


def test_daily_stream_duplicate_key_is_caught():
    s = _frame()[["city", "date", "aod"]]
    with pytest.raises(pe.SchemaErrors, match="duplicate key"):
        validate_daily_stream(pd.concat([s, s.iloc[:2]]), name="aod", column="aod",
                              value_range=AOD_RANGE)


def test_city_with_too_few_rows_is_caught():
    df = _frame()
    df = df[~((df.city == "0") & (df.index % 120 > 40))]
    with pytest.raises(pe.SchemaErrors, match="< 100 rows"):
        _ok(df)


def test_c7_city_absent_from_geo_file_is_caught_by_bud0_helper():
    """The real 2026-09-21 finding: city 3147 is in the pool but not in bud0_static_geo.csv,
    so a left merge gives it NaN geography on every row. validate_bud0_frame must refuse."""
    from src.modular.schemas import validate_bud0_frame
    df = _frame()
    geo = df.groupby("city")[STATIC].first().reset_index()
    sat = pd.DataFrame({"city": df.city.unique(), "sat_level": [10.0, 12.0, 14.0]})
    p = df.drop(columns=STATIC).merge(geo[geo.city != "2"], on="city", how="left")
    with pytest.raises(pe.SchemaErrors, match="ndvi_100"):
        validate_bud0_frame(p, geo=geo[geo.city != "2"], sat=sat, met=MET, static=STATIC)
    ok = df.drop(columns=STATIC).merge(geo, on="city", how="left")
    validate_bud0_frame(ok, geo=geo, sat=sat, met=MET, static=STATIC)
