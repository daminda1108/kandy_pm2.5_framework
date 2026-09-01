"""Regenerate every numeric claim in the manuscript from the scored files.

PHASE 1 GATE of docs/improvement_plan_2026-09-01.md.

WHY THIS EXISTS. Three headline claims in the project documentation did not reproduce against
`ladder_revalidated.csv` on 2026-09-01, and all three were the SAME failure: the re-validation
(F.84/F.85) updated the pooled ladder and left every stratified and frame statistic at its
pre-revalidation value. The audit trail lived in prose and the numbers lived in CSVs, and
nothing connected them.

  C2  the coastal gain is measured Bud0a->Bud0c -- geography AND satellite -- and was reported
      under the satellite's name. Satellite alone is 1.8x, not 4x.
  C3  median w_Bud2 is 0.350 (reference) / 0.575 (LCS), not 0.000 / 0.900. "Reference networks
      gain nothing from more stations" is no longer supported.
  C4  the frame is 48 cities and 28,930 city-days, not 47 and 32,396.

Every claim emitted here carries its value, the STATISTIC used (median vs mean -- never averaged
across metrics, gotcha #74), n, the source file, this script, and a ledger reference. Phase 2
resolves `{{claim:tag}}` tokens in the manuscript against the emitted JSON, and the build fails
on any token whose stored value disagrees with a fresh run.

Run:  .venv/Scripts/python.exe scripts/build_claims.py [--check]

  --check   recompute and compare against the stored claims.json; exit 1 on any drift.
            This is the gate Phase 2 wires into the manuscript build.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "data" / "processed" / "modular"
DEC = REPO / "data" / "processed" / "decomp"
OUT = MOD / "claims.json"

# Tolerance for --check. Tight: these are deterministic recomputations from static files, so
# any real drift means an input changed, which is exactly what we want to catch.
RTOL = 1e-9


class Claims:
    """Accumulator that forces every claim to declare its provenance."""

    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def add(self, tag: str, value, *, stat: str, n, source: str, ledger: str, note: str = "") -> None:
        if tag in self.rows:
            raise KeyError(f"duplicate claim tag {tag!r}")
        if isinstance(value, (np.floating, np.integer)):
            value = value.item()
        self.rows[tag] = dict(
            value=value, stat=stat, n=int(n) if n is not None else None,
            source=source, script="scripts/build_claims.py", ledger=ledger, note=note,
        )


# ── loaders ───────────────────────────────────────────────────────────────────────────────

def _ladder() -> pd.DataFrame:
    """The re-validated ladder: 3 bottom rungs x 48 cities = 144 rows."""
    d = pd.read_csv(MOD / "ladder_revalidated.csv")
    want = {"Bud0a", "Bud0b", "Bud0c"}
    got = set(d.bottom.unique())
    if got != want:
        raise ValueError(f"expected bottom rungs {want}, found {got}")
    return d


def _gain(a: pd.Series, b: pd.Series) -> pd.Series:
    """Per-city percentage RMSE reduction from a to b. Median of ratios, never a ratio of medians."""
    return 100.0 * (a - b) / a


# ── claim groups ──────────────────────────────────────────────────────────────────────────

def frame(c: Claims, d: pd.DataFrame) -> None:
    """C4. The scale sentence in the abstract."""
    c0 = d[d.bottom == "Bud0c"]
    c.add("frame.cities", c0.city.nunique(), stat="count", n=c0.city.nunique(),
          source="ladder_revalidated.csv", ledger="F.85",
          note="C4: the retired figure was 47, from the superseded pre-F.84 run")
    c.add("frame.city_days", int(c0.n_days.sum()), stat="sum", n=c0.city.nunique(),
          source="ladder_revalidated.csv", ledger="F.85",
          note="C4: the retired figure was 32,396 -- overstated by 10.7%")
    c.add("frame.med_held_stations", float(c0.n_held.median()), stat="median", n=len(c0),
          source="ladder_revalidated.csv", ledger="F.85")
    c.add("frame.med_days_per_city", float(c0.n_days.median()), stat="median", n=len(c0),
          source="ladder_revalidated.csv", ledger="F.85")
    c.add("frame.bands", int(c0.band.notna().sum()), stat="count", n=len(c0),
          source="ladder_revalidated.csv", ledger="F.85",
          note="cities carrying a latitude band; the remainder are the CNEMC cluster")


def bottom_rung(c: Claims, d: pd.DataFrame) -> None:
    """The decomposed sensorless rung. Each stream measured against a monitor's worth."""
    a = d[d.bottom == "Bud0a"].set_index("city").rmse_Bud0
    b = d[d.bottom == "Bud0b"].set_index("city").rmse_Bud0
    cc = d[d.bottom == "Bud0c"].set_index("city").rmse_Bud0
    n = len(cc)

    for tag, s, lab in [("bud0a", a, "reanalysis drivers only"),
                        ("bud0b", b, "+ static geography"),
                        ("bud0c", cc, "+ satellite level")]:
        c.add(f"rung.{tag}.rmse", round(float(s.median()), 2), stat="median", n=n,
              source="ladder_revalidated.csv", ledger="F.85", note=lab)

    c.add("step.geography", round(float(_gain(a, b).median()), 1), stat="median of per-city ratios",
          n=n, source="ladder_revalidated.csv", ledger="F.85",
          note="Bud0a->Bud0b; static geography beats the satellite level")
    c.add("step.satellite", round(float(_gain(b, cc).median()), 1), stat="median of per-city ratios",
          n=n, source="ladder_revalidated.csv", ledger="F.85",
          note="Bud0b->Bud0c; an ANNUAL satellite level -- see C1, the stream may be under-powered")


def ladder_steps(c: Claims, d: pd.DataFrame) -> None:
    """The spine of the paper. These three reproduce the documentation exactly."""
    x = d[d.bottom == "Bud0c"]
    n = len(x)
    for tag, a, b, lab, led in [
        ("bud0c_bud1", x.rmse_Bud0, x.rmse_Bud1, "+2 stations", "F.85"),
        ("bud1_bud2", x.rmse_Bud1, x.rmse_Bud2, "+6 stations", "F.85"),
        ("bud2_bud3", x.rmse_Bud2, x.rmse_Bud3, "+regional background", "F.85"),
    ]:
        c.add(f"step.{tag}", round(float(_gain(a, b).median()), 1), stat="median of per-city ratios",
              n=n, source="ladder_revalidated.csv", ledger=led, note=lab)


def by_band(c: Claims, d: pd.DataFrame) -> None:
    x = d[d.bottom == "Bud0c"].copy()
    x["g1"] = _gain(x.rmse_Bud0, x.rmse_Bud1)
    x["g3"] = _gain(x.rmse_Bud2, x.rmse_Bud3)
    for band, grp in x.groupby("band"):
        c.add(f"band.{band}.step_bud0c_bud1", round(float(grp.g1.median()), 1),
              stat="median of per-city ratios", n=len(grp),
              source="ladder_revalidated.csv", ledger="F.85")
        c.add(f"band.{band}.step_bud2_bud3", round(float(grp.g3.median()), 1),
              stat="median of per-city ratios", n=len(grp),
              source="ladder_revalidated.csv", ledger="F.85")


def coastal(c: Claims, d: pd.DataFrame) -> None:
    """C2. The three steps reported separately, because the combined one was misattributed."""
    a = d[d.bottom == "Bud0a"].set_index("city").rmse_Bud0
    b = d[d.bottom == "Bud0b"].set_index("city").rmse_Bud0
    x = d[d.bottom == "Bud0c"].set_index("city").copy()
    x["g_geo"] = _gain(a, b)
    x["g_sat"] = _gain(b, x.rmse_Bud0)
    x["g_both"] = _gain(a, x.rmse_Bud0)

    for flag, lab in [(True, "coastal"), (False, "inland")]:
        grp = x[x.coastal == flag]
        for col, tag in [("g_geo", "geography"), ("g_sat", "satellite"), ("g_both", "place_data")]:
            c.add(f"coastal.{lab}.{tag}", round(float(grp[col].median()), 1),
                  stat="median of per-city ratios", n=len(grp),
                  source="ladder_revalidated.csv", ledger="F.85")

    cst, inl = x[x.coastal], x[~x.coastal]
    c.add("coastal.ratio_satellite", round(float(cst.g_sat.median() / inl.g_sat.median()), 1),
          stat="ratio of medians", n=len(x), source="ladder_revalidated.csv", ledger="F.85",
          note="C2: SATELLITE ALONE. The retired '4x' was the combined geography+satellite step "
               "reported under the satellite's name.")
    c.add("coastal.ratio_place_data", round(float(cst.g_both.median() / inl.g_both.median()), 1),
          stat="ratio of medians", n=len(x), source="ladder_revalidated.csv", ledger="F.85",
          note="C2: place-describing data overall (geography + satellite). Geography carries most of it.")


def instrument_class(c: Claims, d: pd.DataFrame) -> None:
    """C3. The claim that reference networks gain nothing from stations 3-8."""
    x = d[d.bottom == "Bud0c"]
    for cls, grp in x.groupby("cls"):
        c.add(f"class.{cls}.w_bud2", round(float(grp.w_Bud2.median()), 3), stat="median", n=len(grp),
              source="ladder_revalidated.csv", ledger="F.85",
              note="C3: retired values were reference 0.000 / LCS 0.900, from the pre-F.84 run")
        c.add(f"class.{cls}.w_bud1", round(float(grp.w_Bud1.median()), 3), stat="median", n=len(grp),
              source="ladder_revalidated.csv", ledger="F.85")
        g = _gain(grp.rmse_Bud1, grp.rmse_Bud2)
        c.add(f"class.{cls}.step_bud1_bud2", round(float(g.median()), 2),
              stat="median of per-city ratios", n=len(grp),
              source="ladder_revalidated.csv", ledger="F.85")
    ref = x[x.cls == "reference"].w_Bud2.median()
    lcs = x[x.cls == "LCS"].w_Bud2.median()
    c.add("class.w_bud2_contrast", round(float(lcs / ref), 2), stat="ratio of medians", n=len(x),
          source="ladder_revalidated.csv", ledger="F.85",
          note="C3: the Kandy-analogue argument rested on an infinite contrast; it is now finite "
               "and must be re-argued, not inherited.")


def stream_coverage(c: Claims, d: pd.DataFrame) -> None:
    """C7. require_covers() is asserted at the BUDGET level, not per city.

    `revalidate_ladder.py` merges the geography and satellite streams with how="left" and never
    drops the misses, so a city missing an entire admitted stream is still scored as `Bud0c`.
    HistGradientBoostingRegressor accepts NaN natively, so it trains and predicts without
    complaint. This is the F.84 family a fourth time: F.84 was a TIER under-using its budget;
    this is a CITY inside that tier not carrying the streams the tier is defined by.

    `learner_sensitivity_bud0c.py` does filter for coverage -- it has to, because Ridge cannot
    take NaN -- which is why the two scripts report different values for the same quantity.
    """
    geo = pd.read_csv(MOD / "bud0_static_geo.csv"); geo["city"] = geo.city.astype(str)
    sat = pd.read_csv(MOD / "bud0_satellite_level.csv"); sat["city"] = sat.city.astype(str)
    x = d[d.bottom == "Bud0c"].copy()
    x["city"] = x.city.astype(str)
    bad = set(x.city) - set(geo.city) | set(x.city) - set(sat.city)
    ok = x[~x.city.isin(bad)]

    c.add("coverage.bud0c_cities_scored", len(x), stat="count", n=len(x),
          source="ladder_revalidated.csv", ledger="C7 / plan 2026-09-01")
    c.add("coverage.bud0c_cities_missing_a_stream", len(bad), stat="count", n=len(x),
          source="bud0_static_geo.csv + bud0_satellite_level.csv", ledger="C7 / plan 2026-09-01",
          note=f"scored in Bud0c without all three admitted streams: {sorted(bad)}")
    c.add("step.bud0c_bud1_stream_complete",
          round(float(_gain(ok.rmse_Bud0, ok.rmse_Bud1).median()), 1),
          stat="median of per-city ratios", n=len(ok),
          source="ladder_revalidated.csv", ledger="C7 / plan 2026-09-01",
          note="C7: the headline first rung restricted to cities that actually carry all three "
               "Bud0c streams. Compare step.bud0c_bud1 -- the headline is NOT stable to this.")
    c.add("rung.bud0c.rmse_stream_complete", round(float(ok.rmse_Bud0.median()), 2),
          stat="median", n=len(ok), source="ladder_revalidated.csv", ledger="C7 / plan 2026-09-01")


def learners(c: Claims) -> None:
    """F.88. Robust across NON-LINEAR estimators only."""
    p = MOD / "learner_sensitivity_bud0c.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    for _, r in d.iterrows():
        key = (r.learner.lower().replace("(", "").replace(")", "")
               .replace(" ", "_").replace("-", "_"))
        c.add(f"learner.{key}.step_bud0c_bud1", round(float(r.gain_0c_1), 1), stat="see source",
              n=int(r.n_cities), source="learner_sensitivity_bud0c.csv", ledger="F.88",
              note=f"{r.learner}; monotone on {r.monotone_pct:.1f}% of cities")
    nonlin = d[~d.learner.str.contains("Ridge")]
    c.add("learner.nonlinear_spread_bud0c_bud1",
          round(float(nonlin.gain_0c_1.max() - nonlin.gain_0c_1.min()), 1), stat="range",
          n=len(nonlin), source="learner_sensitivity_bud0c.csv", ledger="F.88",
          note="NEVER write 'even a linear model reproduces it' -- Ridge collapses on 68 features")
    c.add("learner.all_spread_bud1_bud2",
          round(float(d.gain_1_2.max() - d.gain_1_2.min()), 2), stat="range", n=len(d),
          source="learner_sensitivity_bud0c.csv", ledger="F.88",
          note="the ladder's most estimator-robust result; survives even Ridge")


def colombo(c: Claims) -> None:
    """F.86/F.87. The re-run with a spec-compliant Bud0c and Colombo's real geography."""
    p = MOD / "colombo_zeroshot_bud0c_realgeo.csv"
    if not p.exists():
        return
    r = pd.read_csv(p).iloc[0]
    n = int(r.n)
    for col, tag in [("bias_pct", "bias_pct"), ("seasonal_r", "seasonal_r"),
                     ("r2_plain", "r2_plain"), ("r2_clim", "r2_clim"), ("rmse", "rmse")]:
        c.add(f"colombo.{tag}", round(float(r[col]), 3), stat="point estimate", n=n,
              source="colombo_zeroshot_bud0c_realgeo.csv", ledger="F.87")
    c.rows["colombo.r2_clim"]["note"] = (
        "the residual failure: matches level and season, adds no day-to-day skill against a "
        "day-of-year climatology. A LOCATED deficiency, not a failure to transfer.")


def spatial(c: Claims) -> None:
    """F.69/F.76/F.77 plus the E_fine finding that opened Phase 3."""
    p = DEC / "elangasinghe_spatial_test.csv"
    if p.exists():
        d = pd.read_csv(p)
        c.add("spatial.transect_sites", len(d), stat="count", n=len(d),
              source="decomp/elangasinghe_spatial_test.csv", ledger="F.69")
        c.add("spatial.transect_censored", int(d.cens.sum()), stat="count", n=len(d),
              source="decomp/elangasinghe_spatial_test.csv", ledger="F.69",
              note="Phase 5: four sites censored at 150 and three binned at 32.5, so the 12-point "
                   "rank test runs on ~6 distinct values. The PAIRED results survive intact.")
        c.add("spatial.transect_distinct_obs", int(d.obs.nunique()), stat="count", n=len(d),
              source="decomp/elangasinghe_spatial_test.csv", ledger="F.69")
        c.add("spatial.obs_spread", round(float(d.obs.max() / d.obs.min()), 1), stat="max/min",
              n=len(d), source="decomp/elangasinghe_spatial_test.csv", ledger="F.69",
              note="observed is PM10; the model is PM2.5. Valid for a RATIO claim only -- label it.")
        c.add("spatial.model_spread", round(float(d.model.max() / d.model.min()), 2), stat="max/min",
              n=len(d), source="decomp/elangasinghe_spatial_test.csv", ledger="F.69")

        bg = d[d.name.str.contains("Bot.Gardens")]
        if len(bg) == 2:
            hi, lo = bg.obs.max(), bg.obs.min()
            c.add("spatial.paired_obs_ratio", round(float(hi / lo), 1), stat="ratio", n=2,
                  source="decomp/elangasinghe_spatial_test.csv", ledger="F.69",
                  note="the money figure: two microsites ~300 m apart inside one 998 m pixel")
            c.add("spatial.paired_model_ratio",
                  round(float(bg.model.max() / bg.model.min()), 3), stat="ratio", n=2,
                  source="decomp/elangasinghe_spatial_test.csv", ledger="F.69",
                  note="same pixel -> exactly 1.000 in the SHIPPED product")

    q = DEC / "S_traffic_kandy.npz"
    if q.exists():
        z = np.load(q, allow_pickle=True)
        S, E = z["S_traffic"], z["E_fine"]
        fla, flo = z["fine_lat"], z["fine_lon"]
        res = float(np.diff(fla).mean() * 111000)
        c.add("subgrid.fine_res_m", round(res), stat="mean grid spacing", n=E.size,
              source="decomp/S_traffic_kandy.npz", ledger="Phase 3 / plan 2026-09-01",
              note="E_fine ships alongside the 998 m surface the model uses and is discarded")
        c.add("subgrid.coarse_res_m", round(float(np.diff(z["lats"]).mean() * 111000)),
              stat="mean grid spacing", n=S.size,
              source="decomp/S_traffic_kandy.npz", ledger="Phase 3 / plan 2026-09-01")
        Ep = E[E > 0]
        c.add("subgrid.fine_p90_p10", round(float(np.percentile(Ep, 90) / np.percentile(Ep, 10)), 1),
              stat="p90/p10 over positive cells", n=int(Ep.size),
              source="decomp/S_traffic_kandy.npz", ledger="Phase 3 / plan 2026-09-01",
              note="against the transect's observed 85x; the shipped 1 km field spans 1.23x. "
                   "EMISSION, not concentration -- dispersion will damp this substantially.")
        # the two paired microsites, on the fine grid
        pts = {"entrance": (7.2682, 80.5974), "inside_300m": (7.2707, 80.5963)}
        vals = {}
        for nm, (la, lo) in pts.items():
            i, j = int(np.abs(fla - la).argmin()), int(np.abs(flo - lo).argmin())
            vals[nm] = float(E[i, j])
            c.add(f"subgrid.paired_efine_{nm}", round(vals[nm], 5), stat="cell value", n=1,
                  source="decomp/S_traffic_kandy.npz", ledger="Phase 3 / plan 2026-09-01")
        c.add("subgrid.paired_efine_ratio",
              round(vals["entrance"] / vals["inside_300m"], 2), stat="ratio", n=2,
              source="decomp/S_traffic_kandy.npz", ledger="Phase 3 / plan 2026-09-01",
              note="correctly signed and non-degenerate where the shipped product gives 1.000. "
                   "This is what S1 tests after dispersion.")


def identifiability(c: Claims) -> None:
    """C5. P4. Report the honest cases; flag the grid artefacts rather than calling them identified."""
    p = MOD / "p4_identifiability.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    zero_width = (np.isclose(d.lo95, d.hi95)) & (d.status == "identified")
    c.add("p4.rows", len(d), stat="count", n=len(d), source="p4_identifiability.csv", ledger="F.75")
    c.add("p4.zero_width_identified", int(zero_width.sum()), stat="count", n=len(d),
          source="p4_identifiability.csv", ledger="F.75",
          note="C5 DEFECT: lo95 == hi95 is a single grid cell, not a profile-likelihood interval. "
               "These must be relabelled 'grid-limited' or the grid refined before P4 is claimed.")
    c.add("p4.unidentified", int((d.status == "UNIDENTIFIED").sum()), stat="count", n=len(d),
          source="p4_identifiability.csv", ledger="F.75",
          note="the honest results, and the interesting ones -- lead with these")
    c.add("p4.saturated", int(d.saturated.sum()), stat="count", n=len(d),
          source="p4_identifiability.csv", ledger="F.75")
    if "grid" in d.columns:
        c.add("p4.grid", int(d.grid.max()), stat="profile grid points", n=len(d),
              source="p4_identifiability.csv", ledger="C5 / plan 2026-09-01",
              note="C5: was 7. At 7 points a profile with one point under the chi2 threshold "
                   "gave lo95 == hi95 and was scored `identified`.")
    if "grid_limited" in set(d.status):
        c.add("p4.grid_limited", int((d.status == "grid-limited").sum()), stat="count", n=len(d),
              source="p4_identifiability.csv", ledger="C5 / plan 2026-09-01",
              note="profiles whose interval is narrower than the grid can resolve -- reported "
                   "as such rather than as `identified`")
    c.add("p4.identified", int((d.status == "identified").sum()), stat="count", n=len(d),
          source="p4_identifiability.csv", ledger="C5 / plan 2026-09-01",
          note="C5: 19 at grid 7, of which 11 rested on a zero-width interval")

    # s_exp carries F.77's conclusion that the panel cannot justify moving it off 1.0. At grid 7
    # that rested on zero-width intervals; the refined profiles make it a real result.
    se = d[d.param == "s_exp"]
    if len(se):
        holds = int(((se.lo95 <= 1.0) & (se.hi95 >= 1.0)).sum())
        c.add("p4.s_exp_intervals_containing_1", holds, stat="count", n=len(se),
              source="p4_identifiability.csv", ledger="F.77 / C5",
              note="every profile interval for s_exp contains 1.0, so keeping s_exp = 1.0 is "
                   "supported by an interval rather than by a grid artefact")
        c.add("p4.s_exp_median_box_fraction", round(float(se.box_fraction.median()), 3),
              stat="median", n=len(se), source="p4_identifiability.csv", ledger="F.77 / C5",
              note="the narrowest parameter in the model -- F.77's 'the one the data can "
                   "constrain' survives the grid refinement")


# ── driver ────────────────────────────────────────────────────────────────────────────────

def build() -> dict:
    d = _ladder()
    c = Claims()
    frame(c, d)
    bottom_rung(c, d)
    ladder_steps(c, d)
    by_band(c, d)
    coastal(c, d)
    stream_coverage(c, d)
    instrument_class(c, d)
    learners(c)
    colombo(c)
    spatial(c)
    identifiability(c)
    return dict(
        generated=str(date.today()),
        gate="Phase 1 of docs/improvement_plan_2026-09-01.md",
        rule="No number in any document is quoted from prose. Every claim resolves here.",
        claims=c.rows,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="recompute and diff against the stored file; exit 1 on drift")
    a = ap.parse_args()

    fresh = build()

    if a.check:
        if not OUT.exists():
            print(f"FAIL  {OUT.name} does not exist -- run without --check first")
            return 1
        stored = json.loads(OUT.read_text(encoding="utf-8"))["claims"]
        drift = []
        for tag, row in fresh["claims"].items():
            if tag not in stored:
                drift.append(f"  NEW      {tag} = {row['value']}")
            elif isinstance(row["value"], float) and isinstance(stored[tag]["value"], (int, float)):
                if not np.isclose(row["value"], stored[tag]["value"], rtol=RTOL):
                    drift.append(f"  DRIFT    {tag}: stored {stored[tag]['value']} -> fresh {row['value']}")
            elif row["value"] != stored[tag]["value"]:
                drift.append(f"  DRIFT    {tag}: stored {stored[tag]['value']} -> fresh {row['value']}")
        for tag in stored:
            if tag not in fresh["claims"]:
                drift.append(f"  DROPPED  {tag}")
        if drift:
            print(f"FAIL  {len(drift)} claim(s) disagree with {OUT.name}:")
            print("\n".join(drift))
            return 1
        print(f"OK    {len(fresh['claims'])} claims reproduce exactly")
        return 0

    OUT.write_text(json.dumps(fresh, indent=2), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}  --  {len(fresh['claims'])} claims\n")
    for tag, row in fresh["claims"].items():
        note = f"   # {row['note'][:64]}" if row["note"] else ""
        print(f"  {tag:<42} {str(row['value']):>12}  [{row['stat']}, n={row['n']}]{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
