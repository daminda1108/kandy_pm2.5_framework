"""build_additive_field_v2.py — assemble the B(t) v2 (origin-conditioned) additive field.

Promotes the BV1-validated B(t) v2 into the additive field, WITHOUT touching the locked
v1 outputs. For each year:
  1. build B_background_hourly_{year}_v2.parquet — the origin-conditioned background:
     daily air-mass class (Kandy 850-hPa back-trajectories, d1_trajectories_850) →
     marine days → marine floor 6.5; continental days → level solved so the annual mean
     equals v1's (1-f(year))*VanD_basin EXACTLY (G1 preserved); × within-class GEOS daily
     modulation; broadcast to the hourly T-anchor clock. Bracket = proportional band.
  2. assemble kandy_decomp_predictions_{year}_additive_v2.parquet from the 4factor field +
     the v2 background (closed form identical to build_additive_field.assemble_year).

v1 files (`..._additive.parquet`, `B_background_hourly_{year}.parquet`) are NOT overwritten.
The figure suite reads the v2 field via paperfig kind="additive_v2".

In:  kandy_decomp_predictions_{year}_4factor.parquet, T_anchor, d1_trajectories_850,
     vandonkelaar_kandy_annual.csv, background_b_annual.csv
Out: kandy_decomp_predictions_{year}_additive_v2.parquet (+ B_background_hourly_{year}_v2.parquet)
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src.stage1_satml.decomp.build_additive_background import geoscf_daily_shape

DEC = REPO / "data" / "processed" / "decomp"
TANCHOR = REPO / "data" / "processed" / "stage1_v3" / "T_anchor"
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Seasonal background re-level — BUILT, MEASURED, AND NOT ADOPTED (2026-07-27).
#
# It fixes a real defect: B is a daily-resolution background against an hourly total,
# and in the low season it lands ABOVE the total (B > T in 28.5% of all hours, monthly
# B/T reaching 1.14 in September), which renders those hours spatially flat and shows a
# zero or negative local share. The re-level bounds monthly B/T and hourly B while
# preserving the YEAR's mean of B, so the disclosed f partition is untouched.
#
# Measured on the rebuilt payload it is NOT worth shipping. Annual mass conservation
# means every month BELOW the ceiling is scaled UP to absorb what the capped months give
# back, and those months outnumber the capped ones — so the dry season, which currently
# renders well, pays for the low season:
#
#     2022 March: local share 0.287 -> 0.112, map spread 3.92 -> 2.61 ug/m3
#     2023 May:   local share 0.353 -> 0.101 (May 2023 sits UNDER the ceiling, so it
#                 is scaled up rather than capped — the ceiling is per year, and a
#                 month can be on either side of it depending on the year)
#
# It buys coherence (B > T: 28.5% -> 0.13%, no negative local shares) at the cost of
# less spatial structure in most months. That is the opposite of the reported symptom.
# Kept, defaulted OFF, because the diagnosis and the machinery are both worth having:
# the real fix is an hourly background (Consolidation v3), not a bound on a daily one.
RELEVEL = False
F_MIN = 0.02      # minimum local share at every hour (coherence cap; see build_B_v2).
# Chosen as the SMALLEST value that removes the zero-local-share defect (0.08% of hours
# residual, against 2.57% at F_MIN=0), not tuned to a target f. The resulting annual f is
# almost independent of it -- 0.477 at F_MIN=0.00 through 0.502 at 0.08 -- so f is set by
# the coherence constraint itself, not by this parameter.


def relevel_background(B: pd.DataFrame, year: int) -> pd.DataFrame:
    """Apply the seasonal/hourly background re-level (kandy_background_relevel).

    Keeps the YEAR's mean of B exactly, so the disclosed f partition is untouched;
    bounds monthly B/T at CAP_BT and hourly B at (1-F_MIN)*T so the partition stays
    physically coherent. Preserves the pre-fix series as `B_uncapped`.
    """
    import kandy_background_relevel as rl
    T = pd.read_parquet(TANCHOR / f"T_kandy_hourly_{year}.parquet",
                        columns=["datetime_utc", "T_q50"])
    m = B.merge(T, on="datetime_utc", how="left")
    if m.T_q50.isna().any():
        raise SystemExit(f"{year}: {int(m.T_q50.isna().sum())} background hours have no T")
    raw = m["B"].to_numpy(float)
    Tv = m.T_q50.to_numpy(float)
    month = pd.to_datetime(m.datetime_utc, utc=True).dt.month.to_numpy()
    b1, _ = rl._monthly_relevel(raw, Tv, month)
    b2 = rl._hourly_cap(b1, Tv, month)
    ratio = np.where(raw > 0, b2 / raw, 1.0)
    return pd.DataFrame({"datetime_utc": m.datetime_utc.to_numpy(), "B": b2,
                         "B_lo": m.B_lo.to_numpy(float) * ratio,
                         "B_hi": m.B_hi.to_numpy(float) * ratio,
                         "B_uncapped": raw})
GEOS = REPO / "data" / "raw" / "geos_cf"
TRAJ = DEC / "w2" / "d1_trajectories_850.parquet"
YEARS = list(range(2019, 2024))
B_MARINE = 6.5
MARINE_SECTORS = {"SW_marine"}

# W1 of docs/prereg_hourly_background_and_learnable_decomp_2026-08-18.md.
# The trajectory archive is 6-HOURLY (arrivals at 00/06/12/18 UTC, 11,676 rows over 2,919
# days) and daily_class() collapsed it with .mode() to one class per day. Measured on the
# archive: the sector changes within the day on 24.8% of days, and the binary marine flag
# that actually sets B's level flips within the day on 11.3%. On roughly one day in nine the
# background genuinely steps mid-day and the model held it flat by construction.
#
# SCOPE, stated so this is not over-claimed: the marine rate is flat across arrival hours
# (0.292/0.293/0.292/0.287), so this adds EPISODIC sub-daily transitions, NOT a diurnal
# cycle. It makes B step when the air mass steps. It does not make B breathe with the
# boundary layer -- that component is collinear with the local increment's own driver and
# is not identifiable from a total-only series (ledger F.41).
#
# No new free parameter: B_MARINE, the continental-level solve, the annual-mean lock and the
# F.43 coherence cap are unchanged in form. False reproduces the daily-mode behaviour exactly.
SUBDAILY_ORIGIN = True
# Local fraction f, per year. STATUS: a PRIOR, not fitted — the weakest number in
# the chain and disclosed as such in the preprint (Section 8). Source-apportionment
# literature gives the level; the year-to-year variation is REASONED (2020 pandemic
# and 2021-22 fuel-crisis reductions in local traffic), not inferred. The independent
# SBI posterior is f=0.181 [0.10,0.27] (track_i_posteriors.csv), so these sit at or
# above its centre and 2019 (0.28) lies just outside its upper bound; we keep the
# prior because the same SBI runs low against the literature bracket at every
# locally-dominated panel city where it can be checked. Consequence is small by
# construction: the field is T-locked so the area mean is EXACTLY invariant to f,
# and exposure/burden move <2% across the plausible band (sensitivity_analysis.py).
FRAC_LOCAL_YEAR = {2019: 0.28, 2020: 0.25, 2021: 0.21, 2022: 0.20, 2023: 0.27}  # = v1


def _is_marine(sector: str, month: int) -> bool:
    return (sector in MARINE_SECTORS) or (sector == "BoB_marine" and month in (6, 7, 8, 9))


def daily_class() -> pd.DataFrame:
    t = pd.read_parquet(TRAJ)
    t["date"] = pd.to_datetime(t["date"])
    dom = t.groupby("date").sector.agg(lambda s: s.mode().iloc[0]).rename("sector").reset_index()
    dom["month"] = dom.date.dt.month
    dom["marine"] = [_is_marine(s, m) for s, m in zip(dom.sector, dom.month)]
    return dom[["date", "marine"]]


def subdaily_class() -> pd.DataFrame:
    """The trajectory class at its native 6-hourly arrival, keyed for a floor('6h') join."""
    t = pd.read_parquet(TRAJ)
    t["arrival"] = pd.to_datetime(t["arrival"])
    t["month"] = t.arrival.dt.month
    t["marine"] = [_is_marine(s, m) for s, m in zip(t.sector, t.month)]
    return (t[["arrival", "marine"]]
            .drop_duplicates("arrival")
            .sort_values("arrival")
            .reset_index(drop=True))


def geos_daily(year) -> pd.Series:
    df = pd.read_csv(GEOS / f"kandy_geos_cf_{year}.csv", parse_dates=["datetime"]).rename(
        columns={"PM25_RH35_GCC": "g"})
    df["date"] = df.datetime.dt.floor("D")
    return df.groupby("date").g.mean()


def build_B_v2(year, b_annual, T_override: pd.DataFrame | None = None) -> pd.DataFrame:
    """origin-conditioned hourly B(t) v2 on the T-anchor clock; annual mean = b_annual.

    T_override -- optional (datetime_utc, T_q50) frame used IN PLACE of the on-disk anchor
    when evaluating the F.43 coherence cap. Sensitivity analysis only (the diurnal-amplitude
    sweep); production passes None and reads the anchor from disk unchanged.
    """
    t = pd.read_parquet(TANCHOR / f"T_kandy_hourly_{year}.parquet", columns=["datetime_utc"])
    t["date"] = pd.to_datetime(t["datetime_utc"]).dt.tz_localize(None).dt.floor("D")
    g = geos_daily(year).rename("g").reset_index()

    if SUBDAILY_ORIGIN:
        # Same construction, but the air-mass class is carried at its native 6-hourly
        # arrival instead of being collapsed to the daily mode. The GEOS-CF modulation
        # stays DAILY (it is a daily product); only the class -- and therefore the level
        # -- is allowed to step within the day.
        h = t[["date"]].copy()
        h["arrival"] = pd.to_datetime(t["datetime_utc"]).dt.tz_localize(None).dt.floor("6h")
        h = h.merge(subdaily_class(), on="arrival", how="left").merge(g, on="date", how="left")
        h["marine"] = h.marine.fillna(False)
        h["g"] = h.g.fillna(h.g.mean())
        fm = h.marine.mean()                              # hour-weighted marine fraction
        b_cont = (b_annual - fm * B_MARINE) / (1 - fm) if fm < 1 else b_annual
        h["level"] = np.where(h.marine, B_MARINE, b_cont)
        h["gz"] = h.groupby("marine").g.transform(lambda s: s / s.mean())
        Bh = (h.level * h.gz).to_numpy(float)
        B = Bh * (b_annual / Bh.mean())                   # exact annual mean
        flips = int((h.marine.to_numpy()[:-1] != h.marine.to_numpy()[1:]).sum())
        print(f"    sub-daily origin: {flips:,} class transitions on the hourly clock "
              f"(marine fraction {fm:.3f})")
    else:
        cls = daily_class()
        day = t[["date"]].drop_duplicates().merge(cls, on="date", how="left").merge(g, on="date", how="left")
        day["marine"] = day.marine.fillna(False)
        day["g"] = day.g.fillna(day.g.mean())
        fm = day.marine.mean()
        b_cont = (b_annual - fm * B_MARINE) / (1 - fm) if fm < 1 else b_annual
        day["level"] = np.where(day.marine, B_MARINE, b_cont)
        # within-class GEOS modulation (mean 1 per class)
        day["gz"] = day.groupby("marine").g.transform(lambda s: s / s.mean())
        day["Bd"] = day.level * day.gz
        day["Bd"] *= b_annual / day.Bd.mean()             # exact annual mean
        bmap = dict(zip(day.date, day.Bd))
        B = t.date.map(bmap).to_numpy()

    # ── COHERENCE CAP (2026-08-09) ────────────────────────────────────────────
    # Physical constraint, raised by an external reviewer and correct: local sources
    # (traffic, cooking, waste burning) emit continuously, so at an emitting location the
    # local increment is strictly positive at EVERY hour -- rain changes removal, not
    # emission. Therefore B <= T always, and a background at or above the total is not a
    # physical state: it means B is over-estimated for that hour.
    #
    # Uncapped this was violated in ~25% of hours (63% in October), rendering the field
    # exactly flat and reporting a zero local share at the traffic core. The cap is the
    # coherence bound already derived in ledger F.17: a background held FLAT WITHIN A DAY
    # cannot exceed that day's MINIMUM total, so cap each day's B at (1-F_MIN) x min_hour(T)
    # for that day. That keeps B daily-flat (its defining structure), guarantees a local
    # share of at least F_MIN at every hour, and is a DERIVED constraint rather than a new
    # free parameter.
    #
    # NOTE this necessarily raises the annual local fraction -- that is the point. The
    # shipped f of 0.244 sat BELOW its own coherence floor in nine months of twelve, and
    # three independent lines (floor >= 0.41, hierarchical 0.392, network 0.446) place it
    # near 0.4. The T-lock means basin means, exposure and burden are unchanged.
    Tq = (T_override.copy() if T_override is not None else
          pd.read_parquet(TANCHOR / f"T_kandy_hourly_{year}.parquet",
                          columns=["datetime_utc", "T_q50"]))
    Tq["date"] = pd.to_datetime(Tq["datetime_utc"]).dt.tz_localize(None).dt.floor("D")
    tmin = Tq.groupby("date").T_q50.min()
    cap = (1.0 - F_MIN) * t.date.map(tmin).to_numpy()
    n_capped = int(np.sum(B > cap))
    B = np.minimum(B, cap)
    if n_capped:
        print(f"    coherence cap: {n_capped:,} of {len(B):,} hours "
              f"({100 * n_capped / len(B):.1f}%) had B > (1-{F_MIN}) x daily-min T")
    return pd.DataFrame({"datetime_utc": t.datetime_utc, "B": B,
                         "B_lo": 0.70 * B, "B_hi": 1.25 * B})  # proportional bg band


def assemble_v2(year):
    m = pd.read_parquet(DEC / f"kandy_decomp_predictions_{year}_4factor.parquet")
    b = pd.read_parquet(DEC / f"B_background_hourly_{year}_v2.parquet")
    b["time"] = pd.to_datetime(b.datetime_utc); m["time"] = pd.to_datetime(m.time)
    g = m.groupby("time")
    m["T50"] = g["pm25_q50"].transform("mean")
    m["T05"] = g["pm25_q05"].transform("mean")
    m["T95"] = g["pm25_q95"].transform("mean")
    bmap = b.set_index("time")
    m["B"] = m.time.map(bmap["B"]); m["B_lo"] = m.time.map(bmap["B_lo"]); m["B_hi"] = m.time.map(bmap["B_hi"])
    P = m["pm25_q50"] / m["T50"]
    out = m[["time", "lat", "lon"]].copy()

    # Increment-SPLIT assembly (2026-07-09 core-vs-periphery fix). The plain form
    # PM = B + (T-B)*P inverts the spatial pattern whenever the hourly total T dips
    # below the daily-resolution background B (deep midday mixing, ~38% of hours):
    # multiplying a core-high pattern (P>1) by a negative increment makes the core
    # the MOST-subtracted pixel, so the core renders cleaner than the rural edge --
    # physically wrong. Fix: the local pattern structures only the ACCUMULATION above
    # background; ventilation below background is spatially UNIFORM (mixing cleans the
    # whole basin together, not the core preferentially):
    #     PM = B + max(T-B,0)*P + min(T-B,0)
    # This preserves the basin mean exactly (mass), collapses to a flat field = T when
    # well-ventilated (correct), and is identical to the old form whenever T>=B.
    def split(Tq, Bq):
        inc = Tq - Bq
        return Bq + np.maximum(inc, 0.0) * P + np.minimum(inc, 0.0)
    out["pm25_q50"] = split(m["T50"], m["B"])
    out["pm25_q05"] = split(m["T05"], m["B"]).clip(lower=0.0)
    out["pm25_q95"] = split(m["T95"], m["B"])
    out["pm25_blo"] = split(m["T50"], m["B_hi"])
    out["pm25_bhi"] = split(m["T50"], m["B_lo"])
    out.to_parquet(DEC / f"kandy_decomp_predictions_{year}_additive_v2.parquet", index=False)
    return float(out["pm25_q50"].mean()), float(m["pm25_q50"].mean())


def main():
    vand = pd.read_csv(REPO / "data" / "processed" / "stage1_v3" /
                       "vandonkelaar_kandy_annual.csv").set_index("year")
    # Information-budget declaration (src/modular/production.py). The locked chain runs at
    # Bud1: satellite level + reanalysis drivers + static geography + the FECT sensor pair.
    # This asserts the builder is not reaching for a stream that budget does not admit.
    from src.modular import production as _prod, budgets as _bd
    _budget = _prod.require("build_additive_field_v2",
                            _bd.SATELLITE_LEVEL, _bd.DRIVERS_REANALYSIS,
                            _bd.STATIC_GEO, _bd.SENSOR_PAIR)
    print(f"    [budget {_budget.id}] estimates={sorted(_budget.estimates)} "
          f"imposes={sorted(_budget.imposes)}")
    print("=== B(t) v2 additive field (origin-conditioned; v1 untouched) ===")
    for y in YEARS:
        b_annual = (1 - FRAC_LOCAL_YEAR[y]) * float(vand.loc[y, "basin_mean"])
        B = build_B_v2(y, b_annual)
        # Seasonal re-level (2026-07-27). build_B_v2 sets the ANNUAL mean but nothing
        # constrains its seasonal shape against T, and in the low season it lands above
        # the hourly total: B > T in 28.5% of all hours, monthly B/T reaching 1.14 in
        # September. Those hours render spatially flat by construction, which is the
        # "no emission structure from April" defect. The re-level is applied HERE, right
        # after B is built and before the field consumes it, because it is a property of
        # B — applying it as a separate later step is an ordering trap: this builder
        # regenerates B from scratch and silently discarded an externally applied fix.
        if RELEVEL:
            B = relevel_background(B, y)
        B.to_parquet(DEC / f"B_background_hourly_{y}_v2.parquet", index=False)
        add, mult = assemble_v2(y)
        print(f"  {y}: B_annual {b_annual:5.2f} | additive_v2 basin {add:6.3f} "
              f"| 4factor basin {mult:6.3f} | G1 Δ {abs(add-mult):.3f} "
              f"{'OK' if abs(add-mult) < 0.05 else 'CHECK'}")
    print("\nwrote kandy_decomp_predictions_{2019..2023}_additive_v2.parquet")
    print("next: paperfig kind='additive_v2' → regenerate figure suite into paper_figures_v2/")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
