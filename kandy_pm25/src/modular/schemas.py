"""Structural contracts for the budget-ladder frames (pandera).

`require_covers`, `require_covers_units` and `require_stream_coverage` (budgets.py) check the
DESIGN, the ROWS and the VALUES of a stream. None of them checks the frame's STRUCTURE, and
three of the silent failures in the gotchas were structural:

  - a join that duplicates rows (a stream file with a repeated key multiplies city-days, and
    every downstream median is then weighted by the accident),
  - a stream whose DATE SPAN does not cover the frame's -- the root cause of gotcha #85,
    visible before the merge, where `require_stream_coverage` only sees its consequence after,
  - a city missing from a static stream (C7), which arrives as NaN on every row of that city.

Every check raises `pandera.errors.SchemaErrors` listing ALL failures at once (lazy=True), so a
broken frame reports its whole problem rather than the first symptom.

Usage (see scripts/ladder_maiac.py):
    from src.modular.schemas import validate_static_stream, validate_daily_stream,
        require_span_covers, validate_ladder_frame
"""
from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera import Check, Column

# Plausible physical ranges. Deliberately wide: these catch unit errors and sentinel values
# (-999, 1e20, a x10 scale applied twice), not unusual weather.
PM25_RANGE = (0.0, 1000.0)          # ug/m3, daily city mean
AOD_RANGE = (0.0, 7.0)              # MAIAC 550 nm; > 5 is rare but real in dust/smoke
BLH_RANGE = (0.0, 6000.0)           # m, daily mean
T2M_RANGE = (180.0, 340.0)          # K; a Celsius column would fail here
WIND_ABS = 60.0                     # m/s
# m/day, ERA5-Land daily sum (1 m/day is far beyond any record). The lower bound tolerates the
# product's float32 rounding: real values reach -1.9e-8 m (0.00002 mm), which is noise, not a sign
# error. Anything below -1e-6 m (0.001 mm) is a real defect and fails.
PRECIP_RANGE = (-1e-6, 1.0)

# Declared, not tolerated: NaN here is CENSORED, not missing. build_lur_predictors.py:168 writes
# NaN when no major road exists in the Overpass query extent (city 2168: zero major-road length
# at every radius). HistGradientBoosting routes NaN to its own branch, i.e. treats it as "far".
GEO_CENSORED = {"dist_major_km": "censored: no major road within the Overpass query extent"}


def _unique_key(*cols: str) -> Check:
    return Check(lambda df: ~df.duplicated(list(cols)), element_wise=False,
                 error=f"duplicate key {cols}: a join on this frame will multiply rows")


def _check_allow(allow_null: dict[str, str] | None) -> dict[str, str]:
    """A declared exception needs a reason, exactly as `require_covers(allow=...)` does."""
    allow_null = allow_null or {}
    for col, why in allow_null.items():
        if not isinstance(why, str) or len(why.strip()) < 15:
            raise ValueError(f"allow_null[{col!r}] needs a written reason, got {why!r}")
    return allow_null


def validate_static_stream(df: pd.DataFrame, *, name: str, unit: str = "city",
                           allow_null: dict[str, str] | None = None) -> pd.DataFrame:
    """One row per unit, every feature finite. A NaN here becomes a NaN on every row of that
    unit after the merge -- C7's failure, caught at the source file.

    `allow_null` = {column: reason} declares a column whose NaN is MEANINGFUL (e.g. censored),
    so the exception is visible at the call site rather than silently tolerated."""
    allow_null = _check_allow(allow_null)
    feats = [c for c in df.columns if c != unit]
    schema = pa.DataFrameSchema(
        {unit: Column(str, unique=True, nullable=False),
         **{c: Column(float, Check(lambda s: pd.Series(s).abs() < 1e12,
                                   error="non-finite or sentinel value"),
                      nullable=c in allow_null, coerce=True) for c in feats}},
        name=name, strict=False)
    return schema.validate(df, lazy=True)


def validate_daily_stream(df: pd.DataFrame, *, name: str, column: str,
                          value_range: tuple[float, float], unit: str = "city") -> pd.DataFrame:
    """(unit, date) unique, dates parse, values in a physical range (NaN allowed: cloud)."""
    lo, hi = value_range
    schema = pa.DataFrameSchema(
        {unit: Column(str, nullable=False),
         "date": Column("datetime64[ns]", nullable=False, coerce=True),
         column: Column(float, Check.in_range(lo, hi), nullable=True, coerce=True)},
        checks=[_unique_key(unit, "date")], name=name, strict=False)
    return schema.validate(df, lazy=True)


def require_span_covers(stream: pd.DataFrame, frame: pd.DataFrame, *, name: str,
                        unit: str = "city", min_overlap: float = 0.5) -> None:
    """The stream's date span must overlap each unit's frame span -- checked BEFORE the merge.

    Gotcha #85: MAIAC was pulled for 2019-2022 against a frame spanning 2021-2026. The merge
    succeeded, the column existed, and median coverage was 0%. This fails that case by name,
    per unit, instead of reporting it afterwards as low coverage.
    """
    s = stream.groupby(unit).date.agg(["min", "max"])
    f = frame.groupby(unit).date.agg(["min", "max"])
    j = f.join(s, lsuffix="_frame", rsuffix="_stream", how="left")
    span = (j.max_frame - j.min_frame).dt.days.clip(lower=1)
    inter = (j[["max_frame", "max_stream"]].min(axis=1)
             - j[["min_frame", "min_stream"]].max(axis=1)).dt.days.clip(lower=0)
    j["overlap"] = (inter / span).fillna(0.0)
    bad = j[j.overlap < min_overlap]
    if len(bad):
        raise pa.errors.SchemaError(
            schema=None, data=bad,
            message=(f"{name}: date span covers < {min_overlap:.0%} of the frame for "
                     f"{len(bad)}/{len(j)} {unit}s -- the stream was pulled for the wrong "
                     f"period (gotcha #85). Worst:\n"
                     f"{bad.sort_values('overlap').head(8).to_string()}"))


def validate_ladder_frame(df: pd.DataFrame, *, met: list[str], static: list[str],
                          daily: dict[str, tuple[float, float]], unit: str = "city",
                          min_rows_per_unit: int = 100,
                          allow_null: dict[str, str] | None = None) -> pd.DataFrame:
    """The merged frame a ladder is fitted on.

    - (unit, date) unique: the merge did not multiply rows;
    - target and drivers present and in range (drivers were dropna'd upstream, so any NaN
      here means a later merge re-introduced rows);
    - static features non-null AND constant within each unit (a varying 'static' column means
      the join key was wrong);
    - daily streams in range, nulls allowed (coverage is require_stream_coverage's job);
    - every unit has enough rows to be scored.
    """
    ranges = {"temperature_2m": T2M_RANGE, "boundary_layer_height": BLH_RANGE,
              "u_component_of_wind_10m": (-WIND_ABS, WIND_ABS),
              "v_component_of_wind_10m": (-WIND_ABS, WIND_ABS), "wind": (0.0, WIND_ABS),
              "doy_sin": (-1.0, 1.0), "doy_cos": (-1.0, 1.0)}
    cols = {unit: Column(str, nullable=False),
            "date": Column("datetime64[ns]", nullable=False),
            "pm25_city": Column(float, Check.in_range(*PM25_RANGE), nullable=False)}
    for c in met:
        chk = [Check.in_range(*ranges[c])] if c in ranges else []
        cols[c] = Column(float, chk, nullable=False, coerce=True)
    allow_null = _check_allow(allow_null)
    for c in static:
        cols[c] = Column(float, nullable=c in allow_null, coerce=True)
    for c, rng in daily.items():
        cols[c] = Column(float, Check.in_range(*rng), nullable=True, coerce=True)

    def _static_constant(d: pd.DataFrame) -> bool:
        return bool((d.groupby(unit)[static].nunique(dropna=False) <= 1).all().all()) \
            if static else True

    def _enough_rows(d: pd.DataFrame) -> bool:
        return bool((d.groupby(unit).size() >= min_rows_per_unit).all())

    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise pa.errors.SchemaError(schema=None, data=df,
                                    message=f"ladder frame lacks columns {missing}: a merge did not happen")
    schema = pa.DataFrameSchema(
        cols, strict=False, name="ladder_frame",
        checks=[_unique_key(unit, "date"),
                Check(_static_constant, error="a static feature varies within a unit: wrong join key"),
                Check(_enough_rows, error=f"a unit has < {min_rows_per_unit} rows")])
    return schema.validate(df, lazy=True)


def validate_bud0_frame(p: pd.DataFrame, *, geo: pd.DataFrame, sat: pd.DataFrame | None,
                        met: list[str], static: list[str],
                        daily: dict[str, tuple[float, float]] | None = None,
                        allow_null: dict[str, str] | None = None) -> pd.DataFrame:
    """One call for the Bud0c frame every ladder script builds: validate the static source
    files, then the merged frame. `allow_null` defaults to GEO_CENSORED."""
    allow_null = GEO_CENSORED if allow_null is None else allow_null
    validate_static_stream(geo, name="bud0_static_geo", allow_null=allow_null)
    if sat is not None:
        validate_static_stream(sat, name="bud0_satellite_level")
    p = p.copy()
    p["date"] = pd.to_datetime(p.date)
    return validate_ladder_frame(p, met=met, static=static, daily=daily or {},
                                 allow_null=allow_null)


def restrict_to_stream_complete(pool: pd.DataFrame, *, geo: pd.DataFrame,
                                sat: pd.DataFrame | None = None, unit: str = "city") -> pd.DataFrame:
    """Keep only units present in EVERY static stream the rung admits, and say which were dropped.

    C7 / bkpyr: a unit scored in a rung whose streams it lacks gets NaN for that stream on every
    row, and gradient boosting fits it without a word (city 3147, found 2026-09-23). This is the
    filter ladder_maiac.py already applied; it is loud so a dropped unit is never a surprise.
    """
    keep = set(geo[unit].astype(str))
    if sat is not None:
        keep &= set(sat[unit].astype(str))
    units = set(pool[unit].astype(str))
    dropped = sorted(units - keep)
    if dropped:
        n = int(pool[unit].astype(str).isin(dropped).sum())
        print(f"    stream-complete filter (C7): dropping {len(dropped)} {unit}(s) {dropped}, "
              f"{n:,} rows -- not in every admitted static stream", flush=True)
    return pool[pool[unit].astype(str).isin(keep)].copy()
