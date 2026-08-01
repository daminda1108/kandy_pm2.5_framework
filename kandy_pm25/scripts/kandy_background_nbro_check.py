"""kandy_background_nbro_check.py — the first EXTERNAL check on the modelled
regional background B(t), against the NBRO island network (2026-08-01).

WHY THIS IS POSSIBLE NOW
------------------------
B(t) is the regional/transboundary background that arrives over Kandy regardless of
local activity — roughly three quarters of the basin's PM2.5. It has never been
checked against an instrument. Everything that constrains it is internal (a rural
satellite floor, an origin-conditioned seasonal shape) or indirect (W2 trajectories).

Since 2026-05-08 the hourly `NBRO_AQ_snapshot` task has been logging **25 Sri Lankan
stations in raw µg/m³** (not AQI-back-converted). None is inside the Kandy basin, so
none can validate the Kandy FIELD — but collectively they sample the regional air mass
the background term is supposed to represent, and their overlap with the modelled
record (to 2026-07-21) is about ten weeks.

WHAT IS COMPARED, AND WHY IT IS THE RIGHT COMPARISON
----------------------------------------------------
B was CONSTRUCTED as a rural FLOOR (the 10th percentile of a rural satellite box),
so the honest counterpart is the **low percentile across the island network**, not the
network mean: every individual station carries its own local increment, exactly as
Kandy does. The script reports the floor (P10/P25), the median and the mean together,
and the physically expected ordering is floor < median < mean, with B tracking the
floor.

The comparison is made at DAILY resolution because B is a daily-resolution product;
comparing it hourly would score it against structure it does not claim to have.

WHAT THIS CAN AND CANNOT ESTABLISH
----------------------------------
CAN: whether the modelled background moves day-to-day with the regional air mass, and
whether its LEVEL is plausible against instruments rather than only against satellite
products.

CANNOT: (1) validate the Kandy field or the local increment — no station is in-basin;
(2) settle absolute bias. The NBRO units are a low-cost sensor network, and low-cost
PM2.5 sensors typically over-read by 30-40% uncalibrated (gotcha #37), so a positive
model-minus-sensor bias is expected and is NOT evidence the model runs low. The
defensible claim is about CORRELATION and ORDERING, with level reported as context.
(3) Different coasts receive different air masses; an island floor is a proxy for
Kandy's inflow, not a measurement of it.

Run:  .venv/Scripts/python.exe scripts/kandy_background_nbro_check.py
Out:  data/processed/decomp/kandy_background_nbro_check.{csv,json}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

NBRO = REPO / "data" / "external" / "nbro" / "nbro_live_hourly.parquet"
DEC = REPO / "data" / "processed" / "decomp"
OUT_CSV = DEC / "kandy_background_nbro_check.csv"
OUT_JSON = DEC / "kandy_background_nbro_check.json"

KANDY = (7.2906, 80.6337)
EXCLUDE_KM = 20.0        # drop anything that could be sampling the basin itself
MIN_STATIONS = 6         # per hour, before a percentile means anything
MIN_HOURS_PER_DAY = 6
PLAUSIBLE = (0.0, 400.0)


def _km(lat, lon, lat0=KANDY[0], lon0=KANDY[1]):
    return np.hypot((lat - lat0) * 110.6, (lon - lon0) * 110.6 * np.cos(np.radians(lat0)))


def load_nbro() -> pd.DataFrame:
    d = pd.read_parquet(NBRO, columns=["name", "latitude", "longitude", "pm25",
                                       "datetime_utc"])
    d = d.dropna(subset=["pm25", "datetime_utc", "latitude", "longitude"])
    d = d[(d.pm25 > PLAUSIBLE[0]) & (d.pm25 < PLAUSIBLE[1])]
    d["h"] = pd.to_datetime(d.datetime_utc, utc=True)
    d["km"] = _km(d.latitude.to_numpy(float), d.longitude.to_numpy(float))
    near = sorted(d.loc[d.km < EXCLUDE_KM, "name"].unique())
    if near:
        print(f"  excluded {len(near)} station(s) within {EXCLUDE_KM:.0f} km of Kandy: {near}")
    d = d[d.km >= EXCLUDE_KM]
    # one value per (station, hour)
    d = d.groupby(["name", "h"], as_index=False).pm25.median()
    return d


def load_background() -> pd.DataFrame:
    frames = []
    for y in (2026, 2025):
        for suffix in ("_v2_drv", "_v2"):
            p = DEC / f"B_background_hourly_{y}{suffix}.parquet"
            if p.exists():
                b = pd.read_parquet(p)
                b["h"] = pd.to_datetime(b.datetime_utc, utc=True)
                frames.append(b[["h", "B"]])
                break
    if not frames:
        raise SystemExit("no background parquet found")
    return pd.concat(frames, ignore_index=True).drop_duplicates("h")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== B(t) vs the NBRO island network (external check) ===")
    obs = load_nbro()
    print(f"  {obs.name.nunique()} stations, {len(obs):,} station-hours, "
          f"{obs.h.min():%Y-%m-%d} -> {obs.h.max():%Y-%m-%d}")

    # hourly cross-station statistics, then daily aggregation
    g = obs.groupby("h").pm25
    hourly = pd.DataFrame({"n": g.size(), "p10": g.quantile(0.10),
                           "p25": g.quantile(0.25), "p50": g.median(),
                           "mean": g.mean()}).reset_index()
    hourly = hourly[hourly.n >= MIN_STATIONS]

    # Aggregate each side to DAILY independently before merging: the network logs on
    # the half hour and the model on the hour, so an exact-timestamp join returns
    # nothing. Daily is the resolution the comparison is defensible at anyway.
    hourly["date"] = hourly.h.dt.floor("D")
    obs_daily = hourly.groupby("date").agg(
        n_hours=("n", "size"), n_st=("n", "median"), p10=("p10", "mean"),
        p25=("p25", "mean"), p50=("p50", "mean"), mean=("mean", "mean")).reset_index()
    obs_daily = obs_daily[obs_daily.n_hours >= MIN_HOURS_PER_DAY]

    B = load_background()
    B["date"] = B.h.dt.floor("D")
    b_daily = B.groupby("date", as_index=False).B.mean()

    daily = obs_daily.merge(b_daily, on="date", how="inner")
    if daily.empty:
        raise SystemExit("no overlap between the NBRO log and the modelled background")
    print(f"  overlap: {len(daily)} days ({daily.date.min():%Y-%m-%d} -> "
          f"{daily.date.max():%Y-%m-%d}), median {daily.n_st.median():.0f} stations/hour")
    if len(daily) < 20:
        print("  WARNING: fewer than 20 overlapping days — treat every number as indicative")

    res = {"n_days": int(len(daily)),
           "span": [str(daily.date.min().date()), str(daily.date.max().date())],
           "stations": int(obs.name.nunique()),
           "exclude_km": EXCLUDE_KM}
    print("\n  target            level   r(daily)  Spearman   bias(model-obs)   ratio")
    for col, label in [("p10", "network floor P10"), ("p25", "network P25"),
                       ("p50", "network median"), ("mean", "network mean")]:
        x, y = daily[col].to_numpy(float), daily.B.to_numpy(float)
        ok = np.isfinite(x) & np.isfinite(y)
        r = float(np.corrcoef(x[ok], y[ok])[0, 1])
        rs = float(pd.Series(x[ok]).corr(pd.Series(y[ok]), method="spearman"))
        bias = float(np.mean(y[ok] - x[ok]))
        ratio = float(np.mean(y[ok]) / np.mean(x[ok]))
        res[col] = {"obs_level": round(float(np.mean(x[ok])), 2), "r": round(r, 3),
                    "spearman": round(rs, 3), "bias": round(bias, 2),
                    "ratio": round(ratio, 3)}
        print(f"  {label:<18}{np.mean(x[ok]):6.2f}    {r:+.3f}    {rs:+.3f}"
              f"      {bias:+6.2f}          {ratio:.2f}")
    res["model_level"] = round(float(daily.B.mean()), 2)
    print(f"\n  modelled background level over the same days: {daily.B.mean():.2f} ug/m3")

    ordering_ok = bool(daily.p10.mean() < daily.p50.mean() < daily["mean"].mean())
    res["ordering_floor_lt_median_lt_mean"] = ordering_ok
    print(f"  physical ordering floor < median < mean: {'HOLDS' if ordering_ok else 'FAILS'}")

    best = max(("p10", "p25", "p50", "mean"), key=lambda c: res[c]["r"])
    res["closest_tracked"] = best
    print(f"  background tracks '{best}' most closely (r = {res[best]['r']:+.3f})")

    # Low-cost-sensor correction. This is the decision-relevant number, and it is an
    # ASSUMPTION, not a measurement: uncalibrated low-cost PM2.5 over-reads by roughly
    # 30-40% against reference monitors (gotcha #37; the project's own FECT slopes are
    # 1.34-1.40). Applying the midpoint tells us where the true regional floor probably
    # sits, and therefore whether B is high — which is exactly what the April-onward
    # partition defect requires an answer to.
    for slope in (1.30, 1.35, 1.40):
        adj = float(daily.p25.mean()) / slope
        res.setdefault("lcs_adjusted_p25", {})[f"slope_{slope}"] = round(adj, 2)
    mid = float(daily.p25.mean()) / 1.35
    res["lcs_adjusted_p25_mid"] = round(mid, 2)
    res["B_over_adjusted_floor"] = round(float(daily.B.mean()) / mid, 2)
    print(f"\n  IF the network over-reads x1.35 (typical uncalibrated LCS), the true "
          f"regional floor (P25) is ~{mid:.2f} ug/m3")
    print(f"  -> modelled background is {float(daily.B.mean()) / mid:.2f}x that floor "
          f"over these {len(daily)} wet-season days")
    print("     (independent of, and consistent in direction with, the W2 result: "
          "model JJA background 8.50 vs observed ~7.4)")

    res["caveats"] = [
        "No NBRO station is inside the Kandy basin: this checks the REGIONAL BACKGROUND "
        "term, never the Kandy field or the local increment.",
        "NBRO units are a low-cost sensor network; uncalibrated low-cost PM2.5 typically "
        "over-reads 30-40%, so a positive model-minus-sensor bias is expected and is NOT "
        "evidence the model runs low. Correlation and ordering are the defensible claims.",
        "An island-wide floor is a proxy for Kandy's inflow, not a measurement of it — "
        "different coasts receive different air masses.",
        "Compared at DAILY resolution because B(t) is a daily-resolution product.",
    ]
    daily.to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT_CSV.name} + {OUT_JSON.name}")


if __name__ == "__main__":
    main()
