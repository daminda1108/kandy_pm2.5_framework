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
    c.add("frame.unbanded", int(c0.band.isna().sum()), stat="count", n=len(c0),
          source="ladder_revalidated.csv", ledger="F.85",
          note="the CNEMC cluster, which is scored in every POOLED result and carries no "
               "latitude band, so a band-stratified table sums to frame.bands and not to "
               "frame.cities. An external reader read that gap as an inconsistency, which is "
               "the reason both counts are now published and the band table says so on its face")

    # Countries, resolved by joining the scored cities to the frame that named them. The paper
    # asserted 32 for a year; that was the pre-F.84 47-city frame and never re-derived (C4's
    # third sibling). Every other frame statistic in this group was corrected in September and
    # this one was missed because nothing computed it.
    v = pd.read_csv(MOD / "validation_frame.csv", dtype={"slug": str})
    m = v.drop_duplicates("slug").set_index("slug").country
    hit = c0.city.astype(str).map(m)
    if hit.notna().all():
        c.add("frame.countries", int(hit.nunique()), stat="distinct countries", n=len(c0),
              source="ladder_revalidated.csv + validation_frame.csv", ledger="F.85",
              note="C4's third sibling: the retired figure was 32, from the 47-city frame")

        # Why the band table's COUNTRY column does not sum to frame.countries. A per-band
        # distinct count double-counts any country present in more than one band, and the
        # unbanded cluster's country appears in no band row at all. Both numbers are generated
        # so the table's note can state the arithmetic instead of asserting it.
        cc = c0[["city", "band"]].copy()
        cc["country"] = cc.city.astype(str).map(m)
        banded = cc[cc.band.notna()]
        per_band = banded.groupby("band").country.nunique()
        spanning = banded.groupby("country").band.nunique()
        c.add("frame.band_country_sum", int(per_band.sum()),
              stat="sum of per-band distinct country counts", n=len(banded),
              source="ladder_revalidated.csv + validation_frame.csv", ledger="F.85",
              note="what the band table's country column adds up to. It exceeds "
                   "frame.countries and is NOT an inconsistency: the column cannot be summed")
        c.add("frame.countries_multiband", int((spanning > 1).sum()),
              stat="countries present in more than one latitude band", n=len(banded),
              source="ladder_revalidated.csv + validation_frame.csv", ledger="F.85",
              note="each is counted once per band it appears in, which is the whole of the "
                   "gap between frame.band_country_sum and the banded country total")


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
        # The per-cell n belongs in the figure and the table, not only in a caption: a reader
        # who has to hunt for a sample size is entitled to assume it was hidden.
        c.add(f"band.{band}.n", len(grp), stat="cities in the band", n=len(grp),
              source="ladder_revalidated.csv", ledger="F.85")
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
        c.add(f"coastal.{lab}.n", len(grp), stat="cities", n=len(x),
              source="ladder_revalidated.csv", ledger="F.85",
              note="§7 asserted the panel spans 21 coastal cities; this is where that is counted")
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


def s1(c: Claims) -> None:
    """F.89. The registered sub-grid test: refuted, and it refutes its own premise too."""
    p = MOD / "s1_subgrid_placement.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    for _, r in d[d.kind == "contrast_budget"].iterrows():
        # Keep tags strictly [A-Za-z0-9_.] -- the manuscript's token regex excludes anything
        # else, and a tag it cannot match survives into the PDF as literal text instead of
        # raising. Found exactly that way: "solve_at_238_m_(production)".
        tag = (r.label.split(". ", 1)[1].replace(" ", "_").replace("+_", "")
               .replace(",", "").replace("(", "").replace(")", ""))
        c.add(f"s1.contrast.{tag}", float(r.value), stat="p90/p10 over positive cells", n=None,
              source="s1_subgrid_placement.csv", ledger="F.89")
    pr = d[d.kind == "paired"]
    if len(pr):
        bg = pr[pr.label == "botanical garden"].iloc[0]
        c.add("s1.paired_fine_94m", float(bg["fine N=160 tempered"]), stat="ratio", n=2,
              source="s1_subgrid_placement.csv", ledger="F.89",
              note="against 27.5x observed -- S1a REFUTED; 94 m does not place the contrast")
        c.add("s1.paired_production_238m", float(bg["production N=64 tempered"]), stat="ratio", n=2,
              source="s1_subgrid_placement.csv", ledger="F.89")
    for _, r in d[d.kind == "rank"].iterrows():
        c.add(f"s1.rank_{r.label}", float(r.value), stat="Spearman rho", n=12,
              source="s1_subgrid_placement.csv", ledger="F.89",
              note="n=12 with 7 distinct observed values -- heavy ties, weak by construction")
    held = d[(d.kind == "prediction") & (d.value == 1)].label.tolist()
    ref = d[(d.kind == "prediction") & (d.value == 0)].label.tolist()
    c.add("s1.predictions_held", ",".join(held), stat="registered outcome", n=4,
          source="s1_subgrid_placement.csv", ledger="F.89", note="osf.io/bkpyr")
    c.add("s1.predictions_refuted", ",".join(ref), stat="registered outcome", n=4,
          source="s1_subgrid_placement.csv", ledger="F.89",
          note="S1a refuted closes the spatial question per the registration; S1c likewise")


def r2(c: Claims) -> None:
    """F.90. A_transport scored for the first time: it does not improve spatial rank."""
    p = MOD / "r2_atransport.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    m = d[d.city == "MEDIAN"]
    if not len(m):
        return
    m = m.iloc[0]
    c.add("r2.rho_emission_surface", float(m.rho_S), stat="median across panel", n=int(m.n),
          source="r2_atransport.csv", ledger="F.90",
          note="the raw emission surface, undispersed -- ABOVE the 0.2-0.28 ceiling quoted "
               "elsewhere, which was measured on fields already through this machinery")
    c.add("r2.rho_with_atransport", float(m.rho_C), stat="median across panel", n=int(m.n),
          source="r2_atransport.csv", ledger="F.90",
          note="R2a REFUTED: dispersing the surface COSTS rank")
    c.add("r2.delta", float(m.delta), stat="median of per-city deltas", n=int(m.n),
          source="r2_atransport.csv", ledger="F.90")
    body = d.dropna(subset=["delta"])
    body = body[body.city != "MEDIAN"]
    c.add("r2.cities_improved", int((body.delta > 0).sum()), stat="count", n=len(body),
          source="r2_atransport.csv", ledger="F.90",
          note="A_transport helps in a minority of panel cities")


def s2(c: Claims) -> None:
    """F.91. The within-pixel distribution."""
    p = MOD / "s2_within_pixel.csv"
    if not p.exists():
        return
    d = pd.read_csv(p).set_index("label")
    g = lambda k: float(d.loc[k, "value"])
    c.add("s2.between_pixel_p90p10", g("between_pixel_p90p10"), stat="p90/p10", n=256,
          source="s2_within_pixel.csv", ledger="F.91",
          note="MIDDAY ONLY -- not the 1.232x annual figure quoted elsewhere; midday is "
               "ventilated and therefore flatter")
    c.add("s2.within_pixel_p90p10", g("within_pixel_p90p10_median"), stat="median over cells",
          n=256, source="s2_within_pixel.csv", ledger="F.91",
          note="S2a HELD: the spread INSIDE a typical pixel exceeds the spread BETWEEN pixels, "
               "so most midday spatial variation is sub-grid by the model's own structure")
    c.add("s2.cell_mean_drift", g("max_cell_mean_drift"), stat="max abs", n=256,
          source="s2_within_pixel.csv", ledger="F.91",
          note="S2c: P1 survives one level down, exactly")


def chemistry(c: Claims) -> None:
    """F.93. The decomposition's first chemical corroboration."""
    p = MOD / "chemistry_origin_test.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    sec = d[d.kind == "sector"].set_index("label")
    for s_ in sec.index:
        c.add(f"chem.sec_frac.{s_}", float(sec.loc[s_, "sec_frac"]), stat="median",
              n=int(sec.loc[s_, "n"]), source="chemistry_origin_test.csv", ledger="F.93")
    c.add("chem.oc_bc_min_monthly", 13.2, stat="min of monthly medians", n=1826,
          source="chemistry_origin_test.csv", ledger="F.93",
          note="C-H4: traffic-dominated aerosol runs ~1-2. Third independent line refuting "
               "'Kandy ~90% vehicular', after the PMF (F.66) and the PM2.5-NO2 decoupling")
    pr = d[d.kind == "prediction"].set_index("label").sec_frac
    c.add("chem.predictions_held", ",".join(sorted(pr[pr == 1].index)), stat="registered outcome",
          n=4, source="chemistry_origin_test.csv", ledger="F.93",
          note="osf.io/kx23c. C-H3 held only nominally (+0.021 vs +0.019) and is uninformative")
    c.add("chem.predictions_refuted", ",".join(sorted(pr[pr == 0].index)), stat="registered outcome",
          n=4, source="chemistry_origin_test.csv", ledger="F.93",
          note="C-H2: local_recirc is NOT the freshest sector -- stagnation ages air in place, "
               "so 'local increment = fresh primary' is too simple")


def c1_satellite(c: Claims) -> None:
    """F.95. The honest satellite stream."""
    p = MOD / "c1_satellite_ladder.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    st = d[d.kind == "step"].set_index("label").value
    rg = d[d.kind == "rung"].set_index("label").value
    c.add("c1.step_raw_aod", float(st["raw_aod"]), stat="median of per-city ratios", n=47,
          source="c1_satellite_ladder.csv", ledger="F.95",
          note="MAIAC, an actual radiometric retrieval -- not trained on monitors")
    c.add("c1.step_fused_ghap", float(st["fused_ghap"]), stat="median of per-city ratios", n=47,
          source="c1_satellite_ladder.csv", ledger="F.95")
    c.add("c1.fused_excess_pp", float(st["fused_excess_pp"]), stat="difference of medians", n=47,
          source="c1_satellite_ladder.csv", ledger="F.95",
          note="P3 REFUTED: the fused product shows NO excess over raw AOD, so its apparent "
               "value is satellite information rather than recycled information")
    for k in ("Bud0b", "Bud0c-raw", "Bud0c-fused"):
        c.add(f"c1.rmse_{k.replace('-', '_').lower()}", float(rg[k]), stat="median", n=47,
              source="c1_satellite_ladder.csv", ledger="F.95")
    pr = d[d.kind == "prediction"].set_index("label").value
    c.add("c1.predictions_held", ",".join(sorted(pr[pr == 1].index)), stat="registered outcome",
          n=5, source="c1_satellite_ladder.csv", ledger="F.95", note="osf.io/bkpyr")
    c.add("c1.predictions_refuted", ",".join(sorted(pr[pr == 0].index)), stat="registered outcome",
          n=5, source="c1_satellite_ladder.csv", ledger="F.95",
          note="P3 refuted usefully; P4 refuted as flagged weak in advance")


def maiac_ladder(c: Claims) -> None:
    """F.96. The ladder re-derived on the honest stream, and where the leakage actually was."""
    p = MOD / "ladder_maiac.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    x = d[d.bottom == "Bud0c"]
    f = lambda a, b: round(float((100 * (a - b) / a).median()), 1)
    c.add("maiac.step_bud0c_bud1", f(x.rmse_Bud0, x.rmse_Bud1),
          stat="median of per-city ratios", n=len(x), source="ladder_maiac.csv", ledger="F.96",
          note="on raw MAIAC. GHAP gave 17.8 -- a monitor-trained stream DEFLATES the measured "
               "value of the monitors it was trained on")
    c.add("maiac.step_bud2_bud3", f(x.rmse_Bud2, x.rmse_Bud3),
          stat="median of per-city ratios", n=len(x), source="ladder_maiac.csv", ledger="F.96")
    dt = x[x.band == "deep_tropical"]
    c.add("maiac.deep_tropical_first2", f(dt.rmse_Bud0, dt.rmse_Bud1),
          stat="median of per-city ratios", n=len(dt), source="ladder_maiac.csv", ledger="F.96",
          note="Kandy's band. GHAP gave 21.9 -- the honest stream roughly DOUBLES the measured "
               "value of the first two local stations")
    c.add("maiac.deep_tropical_background", f(dt.rmse_Bud2, dt.rmse_Bud3),
          stat="median of per-city ratios", n=len(dt), source="ladder_maiac.csv", ledger="F.96")
    c.add("maiac.deep_tropical_local_advantage",
          round(f(dt.rmse_Bud0, dt.rmse_Bud1) / f(dt.rmse_Bud2, dt.rmse_Bud3), 1),
          stat="ratio of medians", n=len(dt), source="ladder_maiac.csv", ledger="F.96",
          note="F.92 re-derived: CEA local stations outrank an NBRO background station for "
               "Kandy by this factor, up from 2.6x on the fused stream")


def partition(c: Claims) -> None:
    """F.43. The local fraction, and the sweep showing it is set by the constraint not the knob."""
    p = DEC / "kandy_partition_v2.json"
    if not p.exists():
        return
    d = json.loads(p.read_text(encoding="utf-8"))["summary"]
    c.add("partition.f", round(float(d["f_anchored_mean"]), 4), stat="mean over anchored years",
          n=len(d["anchored_years"]), source="decomp/kandy_partition_v2.json", ledger="F.43",
          note="the coherence cap. Supersedes ~0.25 from source-apportionment literature")
    lo, hi = d["f_anchored_range"]
    c.add("partition.f_lo", round(float(lo), 3), stat="min over anchored years",
          n=len(d["anchored_years"]), source="decomp/kandy_partition_v2.json", ledger="F.43")
    c.add("partition.f_hi", round(float(hi), 3), stat="max over anchored years",
          n=len(d["anchored_years"]), source="decomp/kandy_partition_v2.json", ledger="F.43")
    c.add("partition.f_min_parameter", float(d["f_min_parameter"]), stat="parameter value", n=1,
          source="decomp/kandy_partition_v2.json", ledger="F.43",
          note="chosen as the smallest that removes the defect, BEFORE the resulting f was known")
    c.add("partition.residual_b_gt_t_pct", round(float(d["max_hours_B_gt_T_pct"]), 2),
          stat="max over years", n=len(d["anchored_years"]),
          source="decomp/kandy_partition_v2.json", ledger="F.43",
          note="after the cap; every remaining case is an hour where the anchor itself is negative")


def kandy_field(c: Claims) -> None:
    """Shipped-field descriptives, read from the SHIPPED PARQUETS.

    An earlier version of this group read `decomp_summary_*.csv`, which is dated 2026-06-05 and
    predates the additive_v3 build by three months. It gave an annual range of 17.0-20.9 against
    the shipped field's 17.1-21.0, and a gauge drift an order of magnitude too small. A summary
    file is a convenience, not a source; the field is the source.
    """
    import glob
    v = pd.read_csv(REPO / "data/processed/stage1_v3/vandonkelaar_kandy_annual.csv")
    v = v.set_index("year")
    means, drifts = {}, []
    for y in range(2019, 2024):
        p = DEC / f"kandy_decomp_predictions_{y}_additive_v3.parquet"
        if not p.exists():
            continue
        m = float(pd.read_parquet(p, columns=["pm25_q50"]).pm25_q50.mean())
        means[y] = m
        if y in v.index:
            drifts.append(100.0 * (m - float(v.loc[y, "basin_mean"])) / float(v.loc[y, "basin_mean"]))
    if not means:
        return
    c.add("kandy.mean_min", round(min(means.values()), 1), stat="min over anchored years",
          n=len(means), source="decomp/kandy_decomp_predictions_*_additive_v3.parquet",
          ledger="production", note="the SHIPPED field, not the 2026-06 summary file")
    c.add("kandy.mean_max", round(max(means.values()), 1), stat="max over anchored years",
          n=len(means), source="decomp/kandy_decomp_predictions_*_additive_v3.parquet",
          ledger="production")

    # Annual contrast, from the ANNUAL-MEAN field: the per-cell mean over the year, then its
    # p90/p10. Not the same as the midday between-cell figure in section 5.6, which is flatter
    # because midday is ventilated -- the two are reported separately for that reason.
    p23 = DEC / "kandy_decomp_predictions_2023_additive_v3.parquet"
    if p23.exists():
        f = pd.read_parquet(p23, columns=["lat", "lon", "pm25_q50"])
        cell = f.groupby(["lat", "lon"]).pm25_q50.mean()
        c.add("kandy.annual_contrast",
              round(float(np.percentile(cell, 90) / np.percentile(cell, 10)), 3),
              stat="p90/p10 of the annual-mean field", n=int(cell.size),
              source="decomp/kandy_decomp_predictions_2023_additive_v3.parquet",
              ledger="production",
              note="ANNUAL, not the midday between-cell figure of section 5.6")
    if drifts:
        c.add("gauge.drift_lo_pct", round(min(drifts), 2), stat="min over anchored years",
              n=len(drifts), source="shipped field vs vandonkelaar_kandy_annual.csv",
              ledger="P1 / section 2.1",
              note="the field sits consistently ABOVE the anchor; the gauge holds by "
                   "construction and to within 0.6 per cent in practice")
        c.add("gauge.drift_hi_pct", round(max(drifts), 2), stat="max over anchored years",
              n=len(drifts), source="shipped field vs vandonkelaar_kandy_annual.csv",
              ledger="P1 / section 2.1")


def blh_confound(c: Claims) -> None:
    """F.51. Driver completeness x band -- re-run without boundary-layer height."""
    a, b = MOD / "ladder_all_blh.csv", MOD / "ladder_all_noblh.csv"
    if not (a.exists() and b.exists()):
        return
    A, B = pd.read_csv(a), pd.read_csv(b)
    for d, tag in ((A, "with_blh"), (B, "without_blh")):
        g = _gain(d.rmse_Bud0, d.rmse_Bud1).median()
        c.add(f"confound.blh.{tag}_step1", round(float(g), 2),
              stat="median of per-city ratios", n=len(d), source=f"{a.name} / {b.name}",
              ledger="F.51")
    d1 = float(_gain(A.rmse_Bud0, A.rmse_Bud1).median())
    d2 = float(_gain(B.rmse_Bud0, B.rmse_Bud1).median())
    c.add("confound.blh.delta", round(abs(d1 - d2), 3), stat="absolute difference",
          n=len(A), source="ladder_all_blh.csv vs ladder_all_noblh.csv", ledger="F.51",
          note="removing the driver with uneven coverage across bands moves the first rung by "
               "this much -- the ordering flips only within this margin")


def dilution(c: Claims) -> None:
    """F.62. The fitted boundary-layer dilution exponent, against 1.0 for pure inverse-BLH."""
    p = MOD / "diurnal_decomposition.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    if "a" not in d.columns:
        return
    c.add("dilution.exponent", round(float(d.a.median()), 3), stat="median across cities",
          n=len(d), source="diurnal_decomposition.csv", ledger="F.62",
          note="against 1.0 for pure inverse-BLH dilution. A ~40-fold diurnal swing in mixing "
               "depth produces almost no swing in city-mean concentration, because only the "
               "local increment dilutes while the background is already well mixed")


def lur_extra(c: Claims) -> None:
    """F.61. The total station count behind the land-use regression."""
    p = MOD / "lur_r2.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    c.add("lur.total_stations", int(d.n.sum()), stat="sum", n=len(d), source="lur_r2.csv",
          ledger="F.61", note="the draft carried 636; the scored file says otherwise")


def domain_and_resolution(c: Claims) -> None:
    """Physical descriptors of the demonstration domain, and the resolutions §5 compares.

    These were prose constants for a year. Each is cheap to derive and none of them had ever
    been derived, which is the same shape as every other defect this file exists to prevent.
    """
    z = REPO / "data" / "processed" / "pinn_inputs" / "kandy_elev_grid_100m.npz"
    if z.exists():
        e = np.load(z)["elev"]
        c.add("kandy.relief_m", int(round(float(e.max() - e.min()), -1)),
              stat="max minus min elevation over the modelled domain, rounded to 10 m",
              n=int(e.size), source="pinn_inputs/kandy_elev_grid_100m.npz", ledger="production",
              note="the paper said '800 m of relief'; this is the value from the raster")

    # The production solve resolution, against which the §5 refinement test is measured. The
    # fine resolution is already a claim (subgrid.fine_res_m); its counterpart was hardcoded.
    c.add("subgrid.production_res_m", 238, stat="declared production solve resolution", n=1,
          source="src/stage1_satml/decomp/terrain_transport.py", ledger="S1 / F.89",
          note="a configuration constant, not a measurement -- recorded here so the two "
               "resolutions §5 compares are quoted from one place")

    # The refinement deltas. §5 states these as bare numbers; they are differences between two
    # claims that already exist, so they must be derived rather than typed.
    if "s1.paired_production_238m" in c.rows and "s1.paired_fine_94m" in c.rows:
        c.add("s1.paired_delta_on_refinement",
              round(c.rows["s1.paired_production_238m"]["value"]
                    - c.rows["s1.paired_fine_94m"]["value"], 3),
              stat="paired ratio at 238 m minus at 94 m", n=2,
              source="derived from s1.paired_* claims", ledger="F.89",
              note="a TENFOLD refinement in area moves the paired ratio by this much")
    if "s1.rank_production_238m" in c.rows and "s1.rank_fine_94m" in c.rows:
        c.add("s1.rank_delta_on_refinement",
              round(abs(c.rows["s1.rank_production_238m"]["value"]
                        - c.rows["s1.rank_fine_94m"]["value"]), 3),
              stat="absolute change in rank correlation on refinement", n=2,
              source="derived from s1.rank_* claims", ledger="F.89")


def ladder_order(c: Claims) -> None:
    """F.97. Is the ladder measuring the information, or the order it was added in?

    Every gain is a marginal at a POSITION in a fixed order, so the estimand is a path-dependent
    marginal rather than an intrinsic property of a stream. `ladder_order_and_bootstrap.py`
    re-runs the chain with the background moved one step earlier and reports both endpoints.

    It also bootstraps over CITIES rather than city-days, because days within a city are not
    independent and 28,930 city-days is not n=28,930.
    """
    import json as _json
    f = MOD / "ladder_order_summary.json"
    if not f.exists():
        return
    with open(f, encoding="utf-8") as fh:
        s = _json.load(fh)
    src = "ladder_order_summary.json"

    c.add("order.cities", s["order_cities"], stat="count of cities scored in both orderings",
          n=s["order_cities"], source=src, ledger="F.97")
    c.add("order.bg_after_8stn", s["order_bg_after_8stn"],
          stat="median per-city % RMSE reduction, production position", n=s["order_cities"],
          source=src, ledger="F.97")
    c.add("order.bg_after_2stn", s["order_bg_after_2stn"],
          stat="median per-city % RMSE reduction, background moved one step earlier",
          n=s["order_cities"], source=src, ledger="F.97",
          note="the background is large in BOTH positions, so its rank on the ladder is not an "
               "artefact of where it was placed")
    c.add("order.stn3to8_no_bg", s["order_stn3to8_no_bg"],
          stat="median per-city % RMSE reduction, production position", n=s["order_cities"],
          source=src, ledger="F.97")
    c.add("order.stn3to8_with_bg", s["order_stn3to8_with_bg"],
          stat="median per-city % RMSE reduction, measured with a background already present",
          n=s["order_cities"], source=src, ledger="F.97",
          note="20x the production figure and still small. The redundancy of monitors 3-8 is "
               "order-DEPENDENT in magnitude and order-robust in conclusion. Part of the "
               "difference is that more stations sharpen the fitted background coefficient "
               "rather than adding local information")
    c.add("order.endpoint_gap", s["order_endpoint_gap"],
          stat="absolute difference in median final RMSE, micrograms per cubic metre",
          n=s["order_cities"], source=src, ledger="F.97",
          note="both orderings end at the SAME information set and do not reach the same "
               "skill, because the shrinkage estimator is itself path-dependent. This is the "
               "size of that effect, and it is reported rather than assumed away")

    for lad in ("ghap", "maiac"):
        if f"inv_{lad}_median" not in s:
            continue
        # one decimal place throughout: a table mixing 3.6 with 33.34 and 7.0 reads as though
        # the precision differed between rows, and it does not.
        c.add(f"inv.{lad}.median", round(float(s[f"inv_{lad}_median"]), 1),
              stat="paired median advantage, first two sensors minus background, percentage points",
              n=s[f"inv_{lad}_n"], source=src, ledger="F.97")
        c.add(f"inv.{lad}.lo", round(float(s[f"inv_{lad}_lo"]), 1),
              stat="2.5th percentile, bootstrap over cities",
              n=s[f"inv_{lad}_n"], source=src, ledger="F.97")
        c.add(f"inv.{lad}.hi", round(float(s[f"inv_{lad}_hi"]), 1),
              stat="97.5th percentile, bootstrap over cities",
              n=s[f"inv_{lad}_n"], source=src, ledger="F.97")
        c.add(f"inv.{lad}.frac_cities", s[f"inv_{lad}_frac_cities"],
              stat="per cent of deep-tropical cities where sensors beat the background",
              n=s[f"inv_{lad}_n"], source=src, ledger="F.97")

    b = pd.read_csv(MOD / "ladder_bootstrap.csv")
    for lad in ("ghap", "maiac"):
        for step, tag in (("first two sensors", "first2"),
                          ("sensors three to eight", "stn3to8"),
                          ("a background series", "bg")):
            for stratum, stag in (("pooled", "pooled"), ("deep_tropical", "deep_tropical")):
                r = b[(b.ladder == lad) & (b.step == step) & (b.stratum == stratum)]
                if r.empty:
                    continue
                r = r.iloc[0]
                c.add(f"boot.{lad}.{stag}.{tag}.lo", round(float(r.lo95), 1),
                      stat="2.5th percentile of the median, bootstrap over cities",
                      n=int(r.n_cities), source="ladder_bootstrap.csv", ledger="F.97")
                c.add(f"boot.{lad}.{stag}.{tag}.hi", round(float(r.hi95), 1),
                      stat="97.5th percentile of the median, bootstrap over cities",
                      n=int(r.n_cities), source="ladder_bootstrap.csv", ledger="F.97")


def chemistry_deepening(c: Claims) -> None:
    """F.98. Three chemistry strands run 2026-09-05, two of which returned nothing usable.

    (a) Does composition explain what latitude band only labels? Pre-registered at
        docs/prereg_chemistry_mechanism_2026-09-05.md. Answer: undetectable at this power, and
        the exploratory correlation that motivated it dissolves into a between-network artefact.
    (b) Is the local/regional split chemically coherent species by species? The test is INVALID:
        its negative controls fail, so it is reported as untested rather than as a refutation.
    (c) What can an intervention actually remove? Frechet bounds, and this one works.
    """
    import json as _json
    mj = MOD / "chemistry_mechanism_summary.json"
    sj = REPO / "data" / "processed" / "decomp" / "species_partition_summary.json"

    if mj.exists():
        with open(mj, encoding="utf-8") as fh:
            m = _json.load(fh)
        src = "chemistry_mechanism_summary.json"
        c.add("chem.mech.n", m["n_cities"], stat="cities in the band-controlled analysis",
              n=m["n_cities"], source=src, ledger="F.98",
              note="the registration expected 46. Controlling for band DROPS the 11 cities of "
                   "the single national network, which carry no band, and that deviation is "
                   "what raised the detection limit and dissolved the exploratory signal")
        c.add("chem.mech.registered_n", m["registered_n"], stat="cities expected at registration",
              n=m["registered_n"], source=src, ledger="F.98")
        c.add("chem.mech.mde", round(float(m["mde_confirmatory_nominal"]), 3),
              stat="minimum detectable partial rho, 80% power, one-sided, band-controlled",
              n=m["n_cities"], source=src, ledger="F.98",
              note="computed from n and alpha before the analysis, never from the outcome")
        c.add("chem.mech.largest_rho", round(float(m["largest_confirmatory_abs_rho"]), 3),
              stat="largest absolute partial rho across the confirmatory family",
              n=m["n_cities"], source=src, ledger="F.98",
              note="against a detection limit of chem.mech.mde: an order of magnitude short")
        c.add("chem.mech.undetectable", m["confirmatory_undetectable"],
              stat="count of confirmatory hypotheses returning undetectable", n=3,
              source=src, ledger="F.98")
        cd = m.get("cluster_diagnostic", {})
        for lab, tag in (("pooled", "pooled"), ("banded", "banded"),
                         ("single_network", "single_network")):
            if lab in cd:
                c.add(f"chem.cluster.{tag}.rho", round(float(cd[lab]["rho"]), 3),
                      stat="Spearman rho, OC/BC against the local-over-background advantage",
                      n=int(cd[lab]["n"]), source=src, ledger="F.98",
                      note="the pooled value survives in NEITHER group on its own: it is a "
                           "between-cluster difference, a network effect wearing a chemical "
                           "variable's name")
                c.add(f"chem.cluster.{tag}.n", int(cd[lab]["n"]), stat="cities",
                      n=int(cd[lab]["n"]), source=src, ledger="F.98")

    if sj.exists():
        with open(sj, encoding="utf-8") as fh:
            s = _json.load(fh)
        src = "species_partition_summary.json"
        c.add("chem.species.f_black_carbon", round(float(s["f_black_carbon"]), 3),
              stat="one common floor-based estimator applied per species", n=int(s["days"]),
              source=src, ledger="F.98")
        c.add("chem.species.f_sulphate", round(float(s["f_sulphate"]), 3),
              stat="same estimator", n=int(s["days"]), source=src, ledger="F.98")
        c.add("chem.species.f_dust", round(float(s["f_dust"]), 3), stat="same estimator",
              n=int(s["days"]), source=src, ledger="F.98",
              note="NEGATIVE CONTROL. An inland valley has no dust source of consequence, so "
                   "the true value is near zero. The estimator returns the HIGHEST value of "
                   "any species, which is what invalidates the test")
        c.add("chem.species.f_sea_salt", round(float(s["f_sea_salt"]), 3), stat="same estimator",
              n=int(s["days"]), source=src, ledger="F.98",
              note="NEGATIVE CONTROL. Kandy has no local sea-salt source at all")
        c.add("chem.species.verdict", "invalid, negative controls fail",
              stat="declared outcome", n=int(s["days"]), source=src, ledger="F.98",
              note="the species prediction is NEITHER held NOR refuted. Reporting the reversal "
                   "as a chemical refutation would report an instrument failure as a finding")
        c.add("chem.secondary_share", round(float(s["secondary_share"]), 3),
              stat="sulphate + nitrate + secondary organic, share of modelled PM2.5",
              n=int(s["days"]), source=src, ledger="F.98",
              note="GEOS-CF, a MODEL at ~25 km. Never present as measured speciation")
        c.add("chem.intervention_lo", round(100 * float(s["intervention_lo"]), 1),
              stat="Frechet lower bound on the locally emitted primary share, per cent",
              n=int(s["days"]), source=src, ledger="F.98",
              note="responds IMMEDIATELY to local emission control")
        c.add("chem.intervention_hi", round(100 * float(s["intervention_hi"]), 1),
              stat="Frechet upper bound, per cent", n=int(s["days"]), source=src, ledger="F.98",
              note="requires every locally formed secondary particle to disappear too. Equals "
                   "the local share f, so the bound's upper end is the withdrawn claim and its "
                   "lower end is what can actually be asserted")


def sensor_design(c: Claims) -> None:
    """F.99. The proposed Kandy network, and why it beats the designs a programme would pick.

    `design_sensor_network.py` builds it; `design_comparison.py` scores it against the
    alternatives. The comparison is here because proposing a design and asserting it is good is
    not an argument, and because the comparison produced the most useful result: the textbook
    criterion ranks the two designs already known to produce nulls ABOVE the proposed one.
    """
    import json as _json
    js = REPO / "data" / "processed" / "decomp" / "sensor_design_summary.json"
    cmp_f = REPO / "data" / "processed" / "decomp" / "design_comparison.csv"
    sat_f = REPO / "data" / "processed" / "decomp" / "design_saturation.csv"
    if not js.exists():
        return
    with open(js, encoding="utf-8") as fh:
        S = _json.load(fh)
    src = "sensor_design_summary.json"

    c.add("net.total", S["n_total"], stat="count of proposed sites", n=S["n_total"],
          source=src, ledger="F.99")
    for k, tag in (("n_anchor", "anchor"), ("n_design", "design"), ("n_paired", "paired"),
                   ("n_vertical", "vertical"), ("n_receptor", "receptor")):
        if k in S:
            c.add(f"net.{tag}", S[k], stat="sites in the stratum", n=S["n_total"],
                  source=src, ledger="F.99")
    c.add("net.cells_total", S["cells_total"], stat="candidate cells at 94 m",
          n=S["cells_total"], source=src, ledger="F.99")
    c.add("net.cells_feasible", S["cells_feasible"],
          stat="cells within the servicing distance of a road", n=S["cells_total"],
          source=src, ledger="F.99",
          note="logistics enters as a CONSTRAINT on the candidate set, never as an objective: "
               "making access an objective is how convenience sampling happens")
    c.add("net.feasible_pct", int(round(100 * S["cells_feasible"] / S["cells_total"])),
          stat="per cent of the domain that is serviceable", n=S["cells_total"],
          source=src, ledger="F.99")
    c.add("net.existing_pct_lo", int(S["existing_pct_lo"]),
          stat="lowest emission percentile any existing in-domain record samples", n=2,
          source=src, ledger="F.99",
          note="the entire range below this is unsampled, and one of the two low-cost sensors "
               "sits outside the modelled domain altogether")
    c.add("net.design_pct_lo", round(S["design_pct_lo"], 1),
          stat="lowest emission percentile the design stratum reaches", n=S["n_design"],
          source=src, ledger="F.99")
    c.add("net.design_pct_hi", round(S["design_pct_hi"], 1),
          stat="highest emission percentile the design stratum reaches", n=S["n_design"],
          source=src, ledger="F.99")
    c.add("net.design_below_61", S["design_below_61"],
          stat="design sites in the previously unsampled range", n=S["n_design"],
          source=src, ledger="F.99")
    c.add("net.vertical_lo", int(round(S["vertical_zaf_lo"])),
          stat="metres above the local valley floor, lowest transect site", n=S["n_vertical"],
          source=src, ledger="F.99")
    c.add("net.vertical_hi", int(round(S["vertical_zaf_hi"])),
          stat="metres above the local valley floor, highest transect site", n=S["n_vertical"],
          source=src, ledger="F.99",
          note="the axis no monitoring network samples: stations worldwide sit on the valley "
               "floor, which is why the dynamic-transport null could not be interpreted")
    c.add("net.pair_contrast_hi", S["pair_contrast_hi"],
          stat="modelled within-cell emission contrast across a paired triplet",
          n=S["n_paired"], source=src, ledger="F.99",
          note="the model predicts this; the one Kandy observation at 300 m suggests 27.5x, so "
               "the paired stratum has the largest expected effect in the design")
    # TWO BASES, both published and both named, because they differ and a reader who meets one
    # number in the prose and the other on the figure would be right to distrust both. The
    # design file counts receptors AFTER collapsing institutions within 150 m, since two schools
    # on one street are one site for a sensor. The map counts every mapped receptor.
    rank_f = REPO / "data" / "processed" / "decomp" / "kandy_receptors_ranked.csv"
    if rank_f.exists():
        rk = pd.read_csv(rank_f)
        rk = rk[rk.E_pct.notna()]
        c.add("net.receptors_mapped", int(len(rk)), stat="receptors mapped in the domain",
              n=int(len(rk)), source="kandy_receptors_ranked.csv", ledger="F.99",
              note="OpenStreetMap; completeness is not measurable from the data, so this is a "
                   "LOWER BOUND. A missing school is invisible here")
        n90 = int((rk.E_pct >= 90).sum())
        c.add("net.receptors_above_p90", n90,
              stat="mapped receptors above the 90th percentile of the emission proxy",
              n=int(len(rk)), source="kandy_receptors_ranked.csv", ledger="F.99")
        c.add("net.receptors_above_p90_pct", int(round(100 * n90 / len(rk))),
              stat="per cent of mapped receptors", n=int(len(rk)),
              source="kandy_receptors_ranked.csv", ledger="F.99",
              note="susceptible groups are concentrated where the model's least validated axis "
                   "matters most. A statement about a PROXY, which is the argument for "
                   "measuring rather than asserting it")
        c.add("net.receptors_median_pct", round(float(rk[rk.group == "school"].E_pct.median()), 1)
              if (rk.group == "school").any() else None,
              stat="median emission percentile of a mapped school", n=int((rk.group == "school").sum()),
              source="kandy_receptors_ranked.csv", ledger="F.99")
    c.add("net.receptors_distinct", S["receptors_total"],
          stat="distinct receptor LOCATIONS after collapsing institutions within 150 m",
          n=S["receptors_total"], source=src, ledger="F.99",
          note="the selection pool for the receptor stratum. Lower than net.receptors_mapped "
               "by construction: two institutions on one street are one site for a sensor")

    if cmp_f.exists():
        d = pd.read_csv(cmp_f)
        for name, tag in (("clhs", "proposed"), ("d_optimal", "doptimal"),
                          ("road_proximity", "road"), ("existing", "existing"),
                          ("population", "population"), ("random_mean", "random")):
            r = d[d.design == name]
            if r.empty:
                continue
            r = r.iloc[0]
            c.add(f"net.deff.{tag}", round(float(r.D_eff_rel), 2),
                  stat="relative D-efficiency for a land-use regression", n=int(r.n),
                  source="design_comparison.csv", ledger="F.99")
            if np.isfinite(r.cover_pct):
                c.add(f"net.cover.{tag}", int(round(float(r.cover_pct))),
                      stat="percentiles of the emission gradient sampled", n=int(r.n),
                      source="design_comparison.csv", ledger="F.99")
            c.add(f"net.ks.{tag}", round(float(r.ks_mean), 3),
                  stat="mean KS distance from the domain covariate distribution, lower better",
                  n=int(r.n), source="design_comparison.csv", ledger="F.99")
        cl = d[d.design == "clhs"]
        if not cl.empty:
            c.add("net.deff_cost_pct", int(round(100 * (1 - float(cl.D_eff_rel.iloc[0])))),
                  stat="per cent of D-efficiency given up against the D-optimal design",
                  n=int(cl.n.iloc[0]), source="design_comparison.csv", ledger="F.99",
                  note="the price paid for coverage and representativeness. The criterion that "
                       "would reject this design is the one that endorses the networks already "
                       "known to produce nulls")

    if sat_f.exists():
        s = pd.read_csv(sat_f)
        s = s.assign(gain=-s.ks_mean.diff())
        thresh = 0.01
        small = s[(s.gain.notna()) & (s.gain < thresh)]
        c.add("net.saturation_threshold", thresh,
              stat="improvement in representativeness below which a further site is not bought",
              n=len(s), source="design_saturation.csv", ledger="F.99",
              note="an analysis parameter, not a measurement. Published as a claim so the "
                   "number in the prose is the number the selection actually used")
        # The threshold lands ON the boundary between two site counts whose measured
        # representativeness is INDISTINGUISHABLE, so quoting a single n is over-precise. The
        # saturation point is reported as the range whose members sit within one seed standard
        # deviation of the best value.
        sd = float(s.ks_mean.std()) if "ks_sd" not in s else float(s.ks_sd.mean())
        best = float(s.ks_mean.min())
        tied = s[s.ks_mean <= best + sd]
        if len(small):
            c.add("net.saturation_n", int(small.n.iloc[0]),
                  stat="site count beyond which representativeness improves by less than the "
                       "threshold",
                  n=len(s), source="design_saturation.csv", ledger="F.99",
                  note="averaged over 5 seeds. A single seed invents a knee that is not there. "
                       "⚠ The threshold falls on a boundary: see net.saturation_lo/hi, which "
                       "report the range of site counts that are statistically indistinguishable")
        # Which site counts are INDISTINGUISHABLE FROM THE DESIGN POINT, not from the range
        # minimum. Anchoring on the minimum returns only the largest n, which answers a
        # question nobody asked and reads as though 16 were the recommendation.
        design_n = 12
        if design_n in set(s.n):
            ref = float(s.loc[s.n == design_n, "ks_mean"].iloc[0])
            near = s[(s.ks_mean - ref).abs() <= sd]
            c.add("net.saturation_lo", int(near.n.min()),
                  stat="smallest site count whose representativeness is within one seed SD of "
                       "the 12-site design",
                  n=len(s), source="design_saturation.csv", ledger="F.99",
                  note="10 and 12 differ by 0.0005 against a seed standard deviation of about "
                       "0.009. Specifying one rather than the other is not supported by the "
                       "curve, and the figure's single dashed line at 12 is over-precise")
            c.add("net.saturation_hi", int(near.n.max()),
                  stat="largest such site count", n=len(s),
                  source="design_saturation.csv", ledger="F.99")
        c.add("net.saturation_seed_sd", round(sd, 4),
              stat="seed-to-seed standard deviation of the representativeness measure",
              n=len(s), source="design_saturation.csv", ledger="F.99",
              note="the reason a single site count cannot be specified from this curve")


def campaign_power(c: Claims) -> None:
    """F.100. What the proposed campaign could detect, computed BEFORE deployment.

    The uncomfortable result, and the reason this belongs in the thesis rather than only in a
    plan: the campaign's HEADLINE question is the one it cannot answer. Matching the 46-city
    panel's detection limit in a single city would need roughly a hundred to three hundred
    fitting sites. The physics tests are the opposite, and they become the confirmatory set.
    """
    import json as _json
    f = REPO / "data" / "processed" / "decomp" / "campaign_power.json"
    if not f.exists():
        return
    with open(f, encoding="utf-8") as fh:
        P = _json.load(fh)
    src = "campaign_power.json"

    c.add("camp.n_fit", P["n_fit"], stat="sites available to fit a spatial pattern",
          n=P["n_fit"], source=src, ledger="F.100",
          note="anchor plus design plus vertical. The paired offsets are within-cell replicates "
               "rather than independent locations, and the receptor stratum is held out")
    c.add("camp.n_heldout", P["n_receptor_heldout"], stat="receptor sites held out of fitting",
          n=P["n_receptor_heldout"], source=src, ledger="F.100")

    h1 = P["h1_spatial"][str(P["n_fit"])]
    gains = [v - P["benchmark_rho"] for k, v in h1.items() if k.startswith("vs_benchmark")]
    c.add("camp.h1_gain_lo", round(min(gains), 2),
          stat="smallest detectable gain over the benchmark rank correlation, best case",
          n=P["n_fit"], source=src, ledger="F.100")
    c.add("camp.h1_gain_hi", round(max(gains), 2),
          stat="smallest detectable gain over the benchmark, worst case", n=P["n_fit"],
          source=src, ledger="F.100",
          note="against the 46-city panel's 0.130. The campaign's headline question is the one "
               "it cannot answer, and this was computed before any money was committed")
    c.add("camp.panel_limit", P["panel_detection_limit_for_comparison"],
          stat="detection limit the 46-city panel achieved, for comparison", n=46,
          source=src, ledger="F.100")
    c.add("camp.h3_vertical_mde", P["h3_vertical_mde"],
          stat="minimum detectable correlation with height, 5 transect sites", n=5,
          source=src, ledger="F.100",
          note="only a nearly perfect monotone relationship is visible, so the vertical test is "
               "registered as exploratory rather than as a test of the confinement term")
    if "168" in P["h2_ratio_precision"]:
        c.add("camp.h2_ratio_7d", P["h2_ratio_precision"]["168"],
              stat="factor to which a within-cell ratio is resolved after 7 days", n=3,
              source=src, ledger="F.100",
              note="the competing hypotheses are 1.58 and 27.5, so this test is decisive in "
                   "weeks and its power comes from HOURS averaged, not from the number of sites")
    if "90" in P["h4_sign_test"]:
        c.add("camp.h4_nights90", round(100 * P["h4_sign_test"]["90"], 1),
              stat="per cent of nights the drainage sink must exceed the core, over 90 nights",
              n=90, source=src, ledger="F.100",
              note="the unit is the NIGHT, not the site, which is why this is well powered")


def campaign_cost(c: Claims) -> None:
    """F.101. What the campaign costs, and the re-scope that turns out not to be worth doing.

    The useful result is a negative one: the design stratum, whose justification the power
    calculation removed, costs 450 dollars to halve. The dominant line is one reference
    instrument that may not need buying at all.
    """
    import json as _json
    f = REPO / "data" / "processed" / "decomp" / "campaign_costing.json"
    if not f.exists():
        return
    with open(f, encoding="utf-8") as fh:
        K = _json.load(fh)
    src = "campaign_costing.json"

    # Currency claims are stored PRE-FORMATTED with thousands separators. Their only consumer
    # is prose, and "49900 dollars" reads as a typo where "49,900" reads as money. The
    # underlying numbers stay in campaign_costing.json for anything that needs to compute.
    def usd(x):
        return f"{int(round(x)):,}"

    c.add("cost.lcs_unit_usd", int(K["lcs_unit_usd"]),
          stat="published vendor price, one assembled low-cost outdoor monitor, USD", n=1,
          source=src, ledger="F.101",
          note="AirGradient Open Air O-1PST. Chosen because this project already holds "
               "per-device calibration coefficients for AirGradient units, not because it is "
               "cheapest: a different vendor means re-deriving a calibration already in hand")
    c.add("cost.lcs_kit_usd", int(K["lcs_kit_usd"]),
          stat="same unit as a self-assembly kit, USD", n=1, source=src, ledger="F.101")
    c.add("cost.n_lcs", K["n_lcs"], stat="low-cost units the full design requires",
          n=K["n_lcs"], source=src, ledger="F.101")
    c.add("cost.spares", K["spares"],
          stat="spare units for attrition and co-location rotation", n=K["n_lcs"],
          source=src, ledger="F.101")
    c.add("cost.lcs_total_usd", usd(K["lcs_total_usd"]),
          stat="all low-cost units including spares, assembled, USD", n=K["n_lcs"],
          source=src, ledger="F.101")
    c.add("cost.ref_lo_usd", usd(int(K["ref_lo_usd"])),
          stat="lower end of the published range for a regulatory-grade monitor, USD", n=1,
          source=src, ledger="F.101",
          note="the US EPA describes regulatory monitors as costing tens of thousands of "
               "dollars. A RANGE from a public statement, never a quote")
    c.add("cost.ref_hi_usd", usd(int(K["ref_hi_usd"])), stat="upper end of that range, USD", n=1,
          source=src, ledger="F.101")
    c.add("cost.total_lo_usd", usd(K["instrument_total_lo"]),
          stat="instrument subtotal at the low end, USD", n=1, source=src, ledger="F.101",
          note="INSTRUMENTS ONLY. Mounting, power, connectivity, import duty, labour and "
               "servicing are line items with no unit price here, because none is published "
               "for Sri Lanka and a typed number would be a guess wearing a budget's clothes")
    c.add("cost.total_hi_usd", usd(K["instrument_total_hi"]),
          stat="instrument subtotal at the high end, USD", n=1, source=src, ledger="F.101")
    c.add("cost.design_saving_usd", K["design_saving_usd"],
          stat="saved by cutting the design stratum to the recommended size, USD",
          n=1, source=src, ledger="F.101",
          note="the re-scope is not worth doing on cost grounds: this is under three per cent "
               "of the low-end instrument subtotal, and the stratum it cuts is the one whose "
               "hypothesis was demoted. The dominant line is the anchor")
    c.add("cost.ks_loss_pct_8", K["ks_loss_pct_8"],
          stat="per cent of representativeness lost cutting the design stratum to 8", n=1,
          source=src, ledger="F.101")
    c.add("cost.ks_loss_pct_6", K["ks_loss_pct_6"],
          stat="per cent lost cutting it to 6", n=1, source=src, ledger="F.101",
          note="a cliff. The stratum can be trimmed but not gutted")


def colombo_donor(c: Claims) -> None:
    """F.63, re-run 2026-09-04 by scripts/colombo_donor_test.py.

    Three numbers were quoted from a test whose output was never written to a file. Re-running
    it reproduced one exactly and corrected two. The conclusion is unchanged and better founded:
    Colombo does not track Kandy well enough to serve as its regional background.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    from figdata import load  # noqa: E402
    d = load("colombo_donor")
    if not d:
        return

    c.add("donor.colombo_km", d["d_km"], stat="great-circle, city centre to donor", n=1,
          source="colombo_donor_test.csv", ledger="F.63",
          note="CITY centre, the convention every panel pair uses. The two FECT sensors sit at "
               "91.7 and 96.4 km; averaging their positions would redefine the statistic")
    c.add("donor.colombo_r", d["r_daily"], stat="Pearson r, daily means on common days",
          n=d["common_days"], source="colombo_donor_test.csv", ledger="F.63",
          note="reproduces the recorded value exactly")
    c.add("donor.colombo_r_rank", d["r_rank"], stat="Spearman rho, daily",
          n=d["common_days"], source="colombo_donor_test.csv", ledger="F.63",
          note="reported so a low Pearson cannot be dismissed as a tail artefact; it is not one")
    c.add("donor.colombo_r_disattenuated", d["r_disattenuated"],
          stat="Pearson r divided by the square root of Kandy's between-sensor reliability",
          n=d["common_days"], source="colombo_donor_test.csv", ledger="F.63",
          note="the GENEROUS reading: Kandy's series is two low-cost sensors and the panel's "
               "targets are reference networks, so the raw r is attenuated. The conclusion has "
               "to survive this number, and it does")
    c.add("donor.kandy_sensor_reliability", d["sensor_reliability"],
          stat="between-sensor Pearson r on common days", n=d["common_days"],
          source="colombo_donor_test.csv", ledger="F.63",
          note="Kandy's own ceiling: no donor correlation can exceed what its sensors achieve "
               "against each other")
    c.add("donor.benchmark_median", d["benchmark_median"],
          stat="median daily target-donor r across scored panel pairs", n=d["benchmark_pairs"],
          source="colombo_donor_test.csv", ledger="F.63",
          note="the retired figure was 0.923, which is not a median of anything -- it is the "
               "single NEAREST pair's value. See donor.benchmark_nearest_r")
    c.add("donor.benchmark_median_matched", d["benchmark_median_distance_matched"],
          stat=f"median r among pairs within +/-{d['benchmark_band_km']:.0f} km of Kandy's "
               "separation", n=d["benchmark_band_pairs"],
          source="colombo_donor_test.csv", ledger="F.63",
          note="the like-for-like comparison, since donor skill decays with distance")
    c.add("donor.benchmark_nearest_r", d["nearest_pair_r"],
          stat="r of the single panel pair closest in separation to Kandy-Colombo", n=1,
          source="colombo_donor_test.csv", ledger="F.63",
          note=f"at {d['nearest_pair_km']} km. This is what the retired 0.923 actually was")
    c.add("donor.benchmark_band_pairs", d["benchmark_band_pairs"],
          stat=f"panel pairs within +/-{d['benchmark_band_km']:.0f} km of Kandy's separation",
          n=d["benchmark_pairs"], source="colombo_donor_test.csv", ledger="F.63")
    c.add("donor.colombo_rank_in_band", d["pairs_below_kandy_in_band"],
          stat="panel pairs in the distance band scoring BELOW Kandy-Colombo",
          n=d["benchmark_band_pairs"], source="colombo_donor_test.csv", ledger="F.63",
          note="zero: Kandy-Colombo is the weakest pair at comparable separation. Across all "
               "distances one pair at 285 km scores lower, so 'weakest of all 20' is wrong")


def learned_pattern(c: Claims) -> None:
    """Paper 2 / thesis Chapter 5, from the pre-registered run at osf.io/2jyfg (2026-09-04).

    Registered BEFORE the model was written: the benchmark, the detection limit, and the bar.
    The result is a null, and it is the first of six spatial nulls in this programme that
    carries a stated detection limit, which is what makes it a bounded claim rather than an
    absence of evidence.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    from figdata import load  # noqa: E402

    p1, p2 = load("phase1_frame"), load("phase2_learned")
    if p1:
        c.add("phase1.best_predictor", p1["best_predictor"],
              stat="best single globally available predictor by median per-city rho",
              n=p1["cities"], source="phase1_predictor_ranking.csv", ledger="paper 2",
              note="built-up land-cover fraction at 2.4 km, a buffer COARSER than the 1 km "
                   "cell the model reports on")
        c.add("phase1.best_rho", p1["best_median_rho"],
              stat="median per-city Spearman rho", n=p1["cities"],
              source="phase1_predictor_ranking.csv", ledger="paper 2",
              note="the benchmark a learned pattern has to beat")
        c.add("phase1.cities", p1["cities"], stat="cities with at least 8 stations",
              n=p1["cities"], source="lur_predictors.csv", ledger="paper 2")
        c.add("phase1.stations", p1["stations"], stat="stations in the frame", n=1,
              source="lur_predictors.csv", ledger="paper 2")
        c.add("phase1.min_detectable", p1["min_detectable_delta"],
              stat="smallest paired improvement detectable at 80 per cent power",
              n=p1["paired_n"], source="phase1_frame_and_power.py", ledger="paper 2",
              note="simulated on this frame BEFORE the model was built")
    if p2:
        c.add("phase2.bar", p2["bar"], stat="registered bar: benchmark plus detection limit",
              n=1, source="prereg_learned_pattern_2026-09-04.md", ledger="OSF 2jyfg",
              note="a result below this is reported as undetectable at this power, NOT as a "
                   "modest success")
        c.add("phase2.rho_learned", p2["rho_learned"],
              stat="median per-city rho, best learner, leave-one-city-out", n=p2["cities"],
              source="phase2_learned_pattern.csv", ledger="OSF 2jyfg")
        c.add("phase2.delta", p2["delta"],
              stat="median paired difference against the benchmark", n=p2["cities"],
              source="phase2_learned_pattern.csv", ledger="OSF 2jyfg")
        c.add("phase2.better_in", p2["better_in"],
              stat="cities where the learned pattern beats the benchmark", n=p2["cities"],
              source="phase2_learned_pattern.csv", ledger="OSF 2jyfg")
        c.add("phase2.p_value", p2["p_value"], stat="Wilcoxon signed-rank on paired deltas",
              n=p2["cities"], source="phase2_learned_pattern.csv", ledger="OSF 2jyfg")
        for k in ("rho_rf", "rho_mlp", "rho_ridge", "rho_baseline"):
            c.add(f"phase2.{k}", p2[k], stat="median per-city rho", n=p2["cities"],
                  source="phase2_learned_pattern.csv", ledger="OSF 2jyfg")

    g = load("phase2_gauge")
    if g:
        c.add("phase2.gauge_drift", g["worst_pattern_drift"],
              stat="worst |mean(P) - 1| across seven degenerate cases", n=g["cases"],
              source="phase2_gauge_check.py", ledger="OSF 2jyfg, L3",
              note="includes a saturated pattern and an overflow-range logit field. A learned "
                   "pattern can misplace material; it cannot create it")

    s0 = load("phase0_sector")
    if s0:
        c.add("phase0.rho_sector", s0["rho_sector"],
              stat="median per-city rho, sector-weighted emission surface", n=s0["cities"],
              source="phase0_sector_surface.csv", ledger="paper 2")
        c.add("phase0.rho_traffic", s0["rho_traffic"],
              stat="median per-city rho, production traffic surface", n=s0["cities"],
              source="phase0_sector_surface.csv", ledger="paper 2")
        c.add("phase0.dispersion_cost", s0["dispersion_cost_delta"],
              stat="median change in rho from applying the dispersion solver", n=s0["cities"],
              source="phase0_sector_surface.csv", ledger="paper 2 / F.90",
              note="negative: the step meant to place the increment removes rank")


def field_diagnostics(c: Claims) -> None:
    """§2.5, §2.6 and §5.7, from scripts/kandy_field_diagnostics.py (2026-09-04).

    🔴 WHAT THIS PASS FOUND. The manuscript carried THREE different literals for what is one
    quantity -- how often the background exceeded the total before the coherence constraint.
    §2.5 said 38.5 per cent of hours, §2.5 said 38.2 per cent of midday hours, and §2.6 said
    24.8 to 36.1 per cent averaging 29.9. Recomputed against the uncapped background retained
    on disk and the shipped anchor, it is 38.8 per cent of all hours and 53.9 per cent of midday
    hours. The first reproduces; the other two do not.

    ⚠ The historical figures were computed against background generations that have since been
    superseded -- there were three -- so they are not reproducible rather than wrong, and the
    fix is to define the quantity once and derive it once. The "after" numbers, which are what
    the argument actually rests on, reproduce exactly: the residual is under a fifth of one per
    cent and the midday inversion is zero.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    from figdata import load  # noqa: E402
    d = load("kandy_diagnostics")
    if not d:
        return

    c.add("field.precap_excess_mean", d["precap_excess_mean"],
          stat="mean over years of the share of hours with B > T, uncapped background",
          n=5, source="decomp/kandy_field_diagnostics.csv", ledger="F.43 / gotcha #57",
          note="ONE definition for a quantity the manuscript previously stated three ways")
    c.add("field.precap_excess_lo", d["precap_excess_lo"], stat="min over years", n=5,
          source="decomp/kandy_field_diagnostics.csv", ledger="F.43")
    c.add("field.precap_excess_hi", d["precap_excess_hi"], stat="max over years", n=5,
          source="decomp/kandy_field_diagnostics.csv", ledger="F.43")
    c.add("field.precap_excess_midday", d["precap_excess_midday"],
          stat="mean over years of the share of MIDDAY hours with B > T, uncapped background",
          n=5, source="decomp/kandy_field_diagnostics.csv", ledger="gotcha #57",
          note="the inversion rate the increment split repairs; the manuscript said 38.2")
    c.add("field.postcap_excess_max", d["postcap_excess_max"],
          stat="worst year's share of hours with B > T after the constraint", n=5,
          source="decomp/kandy_field_diagnostics.csv", ledger="F.43",
          note="the repair, which does reproduce")
    c.add("field.postcap_inversion_midday", d["ventilated_midday_pct"],
          stat="share of midday hours still inverted after the split and the cap", n=5,
          source="decomp/kandy_field_diagnostics.csv", ledger="gotcha #57")

    # The sweep. An INDEPENDENT reimplementation, not the production code path, so it is
    # labelled as such: it lands within 0.01 of the originally reported values everywhere and
    # supports the same conclusion, which is the point of reporting it at all.
    c.add("field.f_sweep_lo", d["f_sweep_lo"],
          stat="local fraction at F_min = 0, independent reimplementation", n=5,
          source="decomp/kandy_field_diagnostics.csv", ledger="F.43",
          note="the originally reported sweep ran 0.477 to 0.502 and left no artefact; this "
               "reimplementation gives 0.482 to 0.509 and is the reproducible one")
    c.add("field.f_sweep_hi", d["f_sweep_hi"],
          stat=f"local fraction at F_min = {d['f_sweep_param_hi']}, same reimplementation", n=5,
          source="decomp/kandy_field_diagnostics.csv", ledger="F.43")
    c.add("field.f_sweep_param_hi", d["f_sweep_param_hi"], stat="top of the parameter sweep",
          n=1, source="decomp/kandy_field_diagnostics.csv", ledger="F.43")
    c.add("field.f_form_calendar", d["f_form_calendar"],
          stat="local fraction with a calendar-day minimum, the production form", n=5,
          source="decomp/kandy_field_diagnostics.csv", ledger="F.43")
    c.add("field.f_form_roll24", d["f_form_roll24"],
          stat="local fraction with a centred 24-hour rolling minimum", n=5,
          source="decomp/kandy_field_diagnostics.csv", ledger="F.43",
          note="quoting the value beats quoting a bound on the difference: a reader can see "
               "how small it is without being told")
    c.add("field.f_form_roll48", d["f_form_roll48"],
          stat="local fraction with a 48-hour rolling minimum instead of a calendar day", n=5,
          source="decomp/kandy_field_diagnostics.csv", ledger="F.43",
          note="the most sensitive constraint form tried, and the honest upper end")

    # Contrast by averaging window, so §5.7 compares like with like.
    c.add("field.contrast_monthly", d["contrast_monthly"],
          stat="median over months of the between-cell p90/p10 of the shipped field", n=60,
          source="decomp/kandy_contrast_by_window.csv", ledger="F.71",
          note="§5.7 was comparing an ANNUAL model contrast against observed values taken at "
               "mixed windows; this is the window-matched figure")
    c.add("field.contrast_hourly", d["contrast_hourly"],
          stat="median over hours of the between-cell p90/p10 of the shipped field", n=43824,
          source="decomp/kandy_contrast_by_window.csv", ledger="F.71")

    # How wide the sensorless tier actually is. §4.4's argument is that a linear model cannot
    # exploit this many predictors, so the width is part of the claim and not decoration.
    try:
        sys.path.insert(0, str(REPO))
        from modular_validation_all import FEATS  # noqa: E402
        geo = pd.read_csv(MOD / "bud0_static_geo.csv")
        geo_f = [x for x in geo.columns if x not in ("city", "geo_n_stations")]
        c.add("bud0c.n_features", len(FEATS) + len(geo_f) + 1,
              stat="meteorological drivers + static geography + the satellite level",
              n=1, source="modular_validation_all.FEATS + bud0_static_geo.csv", ledger="F.88",
              note="7 drivers, 60 geography columns, 1 satellite level")
        c.add("bud0c.n_geo_features", len(geo_f), stat="static-geography columns", n=1,
              source="bud0_static_geo.csv", ledger="F.88")
    except Exception:                                                   # noqa: BLE001
        pass

    # The global census behind §4.6's "cannot be sampled away". A property of the world's
    # published network, not of our panel, and now pulled rather than remembered.
    g = load("global_census")
    if g:
        for b in ("deep_tropical", "tropical", "subtropical", "temperate"):
            c.add(f"census.{b}", g[b],
                  stat=f"clusters with >= {g['min_stations']} concurrent reference PM2.5 "
                       f"stations overlapping >= {g['min_overlap_days']} days",
                  n=g["reference_locations"],
                  source="modular/global_reference_census.csv", ledger="F.53",
                  note="OpenAQ global pull, clustered at "
                       f"{g['cluster_km']:.0f} km; reference class is OpenAQ's own isMonitor flag")
        c.add("census.temperate_over_deep_tropical",
              round(g["temperate"] / max(g["deep_tropical"], 1), 1),
              stat="ratio of counts", n=g["reference_locations"],
              source="modular/global_reference_census.csv", ledger="F.53",
              note="the retired pair was 5 and 32; an independent census gives "
                   f"{g['deep_tropical']} and {g['temperate']}, so the disparity is LARGER "
                   "than previously reported, not smaller")
        c.add("census.locations_total", g["total_locations"],
              stat="OpenAQ locations reporting PM2.5, worldwide", n=1,
              source="openaq/discovery/global_locations.csv", ledger="F.53")
        c.add("census.locations_reference", g["reference_locations"],
              stat="of those, reference-grade with usable start and end dates", n=1,
              source="openaq/discovery/global_locations.csv", ledger="F.53")


def exposure_burden(c: Claims) -> None:
    """Population-weighted exposure and attributable burden, regenerated 2026-09-04.

    🔴 WHY THESE ARE HERE. The exposure and burden files were dated 2026-07-25, which is before
    both the coherence cap and the field rebuild, and the figure drawing them had been
    regenerated in September while its inputs had not. That is gotcha #86 exactly: a figure is
    a consumer like any other. Regenerating from the shipped field moved the exposure uplift
    from 7 to 9 per cent and the attributable burden from 427 to 431.

    ⚠ The burden rests on a published concentration-response function and a national mortality
    baseline, neither of which this project estimated. The value is a projection of the
    delivered field through somebody else's epidemiology, and the interval reflects only the
    published uncertainty in that function.
    """
    e = pd.read_csv(DEC / "exposure_weighting.csv")
    h = pd.read_csv(DEC / "health_burden.csv")
    if e.empty or h.empty:
        return
    last = int(h.year.max())
    er = e[e.year == last].iloc[0]
    hr = h[h.year == last].iloc[0]

    c.add("exposure.year", last, stat="most recent anchored year", n=1,
          source="decomp/exposure_weighting.csv", ledger="production")
    for col, tag, lab in [("area_mean", "area", "unweighted basin mean"),
                          ("residential", "residential", "residential-weighted"),
                          ("dynamic", "dynamic", "population-weighted, dynamic")]:
        c.add(f"exposure.{tag}", round(float(er[col]), 1),
              stat=f"{lab} concentration, micrograms per cubic metre", n=1,
              source="decomp/exposure_weighting.csv", ledger="production")
    c.add("exposure.uplift_pct", int(hr.exposure_uplift_pct),
          stat="population-weighted exposure above the unweighted area mean, per cent", n=1,
          source="decomp/health_burden.csv", ledger="production",
          note="the area mean UNDER-states exposure because population concentrates in the "
               "higher core; was 7 per cent on the pre-rebuild field")
    c.add("burden.deaths", int(hr.attributable_deaths_per_yr),
          stat="attributable deaths per year, dynamic exposure", n=1,
          source="decomp/health_burden.csv", ledger="production",
          note="projection of the delivered field through a published response function")
    c.add("burden.ci_low", int(hr.ci_low), stat="lower bound", n=1,
          source="decomp/health_burden.csv", ledger="production")
    c.add("burden.ci_high", int(hr.ci_high), stat="upper bound", n=1,
          source="decomp/health_burden.csv", ledger="production")
    c.add("burden.avoidable", int(hr.avoidable_vs_WHO_AQG5),
          stat="deaths per year avoidable against the WHO guideline", n=1,
          source="decomp/health_burden.csv", ledger="production")
    c.add("burden.fraction_pct", round(float(hr.attributable_fraction_pct), 1),
          stat="attributable fraction, per cent", n=1,
          source="decomp/health_burden.csv", ledger="production")


def nbro_pixel(c: Claims) -> None:
    """F.65, re-derived 2026-09-04 by scripts/nbro_pixel_check.py.

    The paper's only external check on the model's FIELD rather than its basin mean. The
    observed values stay cited (Nirmani et al., Table 1); everything the model contributes is
    regenerated here. The lift is the load-bearing quantity: without it the comparison reduces
    to a check on the anchor, which is calibrated to Kandy sensors and therefore not external.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    from figdata import load  # noqa: E402
    d = load("nbro_pixel")
    if not d:
        return

    for y in (2021, 2022):
        c.add(f"nbro.model_pixel_{y}", d[f"model_pixel_{y}"],
              stat="annual mean of the shipped field at the station's cell", n=1,
              source="decomp/nbro_pixel_check.csv", ledger="F.65")
        c.add(f"nbro.lift_pct_{y}", d[f"lift_pct_{y}"],
              stat="pixel annual mean over basin annual mean, as a percentage", n=1,
              source="decomp/nbro_pixel_check.csv", ledger="F.65",
              note="imposed physics: emission proxy times confinement, never fitted to any "
                   "Kandy station, which is what makes the comparison out of sample")
        c.add(f"nbro.diff_pct_{y}", d[f"diff_pct_{y}"],
              stat="model pixel against the observed annual mean, as a percentage", n=1,
              source="decomp/nbro_pixel_check.csv", ledger="F.65",
              note="the observed value is EXTERNAL (Nirmani et al. Table 1) and stays cited")
    c.add("nbro.station_offset_km", d["station_offset_km"],
          stat="distance from the station to the centre of the cell it falls in", n=1,
          source="decomp/nbro_pixel_check.csv", ledger="F.65",
          note="reported so a reader can confirm the cell really contains the station")


def kandy_application(c: Claims) -> None:
    """Everything section 7 quotes about the model's own output.

    Numbers here come from the figure scripts themselves, via `figdata.emit`, or from the JSON
    and CSV artefacts those scripts read. The figure and the sentence beside it therefore
    resolve to one value, and the build breaks if they ever stop agreeing. Nothing in this
    group is typed from a console log.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    from figdata import load  # noqa: E402

    # ── the field itself ──────────────────────────────────────────────────────────────────
    if (d := load("F_field")):
        c.add("kandy.background_annual", d["background_annual"], stat=f"annual mean of B, {d['year']}",
              n=8760, source="decomp/B_background_hourly_2023_v2.parquet", ledger="F.43",
              note="the POST-CAP background; the pre-cap file gives 15.3 and the retired ~25% split")
        c.add("kandy.contrast_maxmin", d["annual_contrast_maxmin"],
              stat="max/min of the annual-mean field", n=256,
              source="decomp/kandy_decomp_predictions_2023_additive_v3.parquet",
              ledger="production", note="the MODEL's contrast; its amplitude is section 6's subject")

    if (d := load("F_spatiotemporal")):
        for k in ("djf", "mam", "jja", "son"):
            c.add(f"kandy.season_{k}", d[f"season_{k.upper()}"] if f"season_{k.upper()}" in d
                  else d[f"season_{k}"], stat="basin mean over the season, 2023", n=1,
                  source="figdata/F_spatiotemporal.json", ledger="production")
        for k in ("night", "morning", "midday", "evening"):
            c.add(f"kandy.phase_{k}", d[f"phase_{k}"],
                  stat="basin mean over the diurnal window, 2023", n=1,
                  source="figdata/F_spatiotemporal.json", ledger="production")
        c.add("kandy.season_swing", d["season_swing"], stat="max/min of the seasonal means", n=4,
              source="figdata/F_spatiotemporal.json", ledger="production")
        c.add("kandy.phase_swing", d["phase_swing"], stat="max/min of the diurnal means", n=4,
              source="figdata/F_spatiotemporal.json", ledger="production")
        c.add("kandy.night_over_midday", d["night_over_midday"], stat="ratio of window means",
              n=2, source="figdata/F_spatiotemporal.json", ledger="F.38 / gotcha #54",
              note="deep night sits ABOVE the midday trough; the older 'night is the minimum' "
                   "wording was wrong and made a correct behaviour look like a defect")

    # ── temporal cycles, IN SAMPLE by construction ────────────────────────────────────────
    if (d := load("F_cycles")):
        c.add("kandy.cycles_seasonal_r", d["seasonal_r"], stat="Pearson r, monthly means",
              n=12, source="figdata/F_cycles.json", ledger="gotcha #68",
              note="IN SAMPLE: the anchor is sharpened to these sensors, so this measures the "
                   "calibration and not skill. Never difference it against an out-of-sample r.")
        c.add("kandy.cycles_diurnal_r", d["diurnal_r"], stat="Pearson r, hour-of-day means",
              n=24, source="figdata/F_cycles.json", ledger="gotcha #68",
              note="IN SAMPLE, as above")

    # ── the December 2022 episode ─────────────────────────────────────────────────────────
    if (d := load("F_episode")):
        c.add("kandy.episode_mean", d["mean_ug"], stat="basin mean over the episode",
              n=d["hours"], source="figdata/F_episode.json", ledger="production")
        c.add("kandy.episode_peak", d["peak_ug"], stat="max hourly basin mean",
              n=d["hours"], source="figdata/F_episode.json", ledger="production")

    # ── interval calibration: WIDTH against CENTRING ──────────────────────────────────────
    p = DEC / "kandy_interval_coverage.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        cen = d["centring"]
        c.add("kandy.cov90", round(float(d["pooled_coverage"]) * 100, 1),
              stat="pooled coverage of the nominal 90% interval", n=int(d.get("n", 0)) or None,
              source="decomp/kandy_interval_coverage.json", ledger="F.25 / gotcha #75",
              note="a ONE-SIDED miss, not a width failure -- see the re-centred value")
        c.add("kandy.miss_below", round(float(cen["miss_below"]) * 100, 1),
              stat="fraction of hours below the lower bound", n=int(d.get("n", 0)) or None,
              source="decomp/kandy_interval_coverage.json", ledger="F.25")
        c.add("kandy.miss_above", round(float(cen["miss_above"]) * 100, 1),
              stat="fraction of hours above the upper bound", n=int(d.get("n", 0)) or None,
              source="decomp/kandy_interval_coverage.json", ledger="F.25")
        c.add("kandy.median_offset", round(float(cen["median_offset_ug"]), 2),
              stat="median model-minus-sensor offset", n=int(d.get("n", 0)) or None,
              source="decomp/kandy_interval_coverage.json", ledger="F.25")
        c.add("kandy.cov90_recentred", round(float(cen["coverage_offset_removed"]) * 100, 1),
              stat="coverage after removing each sensor's own median offset, SAME width",
              n=int(d.get("n", 0)) or None, source="decomp/kandy_interval_coverage.json",
              ledger="F.25 / gotcha #75",
              note="separates centring from width: the width was right, the field is an areal "
                   "mean and the sensors are points")

    # ── the cross-city scorecard ──────────────────────────────────────────────────────────
    p = REPO / "results/figures/multicity/validation_scorecard.csv"
    if p.exists():
        sc = pd.read_csv(p)
        col = lambda *names: next((n for n in names if n in sc.columns), None)
        cs, cd = col("seasonal", "seasonal_r"), col("diurnal", "diurnal_r")
        csp, clv = col("spatial", "spatial_rho"), col("level", "level_bias_pct")
        if cs:
            c.add("scorecard.cities", len(sc), stat="count", n=len(sc),
                  source="multicity/validation_scorecard.csv", ledger="F.9")
            c.add("scorecard.seasonal_r_lo", round(float(sc[cs].min()), 3), stat="min across cities",
                  n=len(sc), source="multicity/validation_scorecard.csv", ledger="F.9")
            c.add("scorecard.seasonal_r_hi", round(float(sc[cs].max()), 3), stat="max across cities",
                  n=len(sc), source="multicity/validation_scorecard.csv", ledger="F.9")
        if cd:
            c.add("scorecard.diurnal_r_lo", round(float(sc[cd].min()), 3), stat="min across cities",
                  n=len(sc), source="multicity/validation_scorecard.csv", ledger="F.55",
                  note="the diurnal shape transfers in the deep tropics and NOT elsewhere; the "
                       "minimum here is the evidence for that, not a coding fault")
            c.add("scorecard.diurnal_r_hi", round(float(sc[cd].max()), 3), stat="max across cities",
                  n=len(sc), source="multicity/validation_scorecard.csv", ledger="F.55")
        if csp:
            est = sc[csp].dropna()
            c.add("scorecard.spatial_estimable", len(est),
                  stat="cities with enough withheld stations to estimate a rank", n=len(sc),
                  source="multicity/validation_scorecard.csv", ledger="gotcha #69",
                  note="the rest are NaN, which is an uncomputed metric and NOT a measured null")
            c.add("scorecard.spatial_rho_hi", round(float(est.max()), 3), stat="max across cities",
                  n=len(est), source="multicity/validation_scorecard.csv", ledger="F.56")
            c.add("scorecard.spatial_rho_median", round(float(est.median()), 3),
                  stat="median across cities with an estimable rank", n=len(est),
                  source="multicity/validation_scorecard.csv", ledger="F.56")
            k = sc[sc.city.str.contains("Kathmandu", case=False, na=False)]
            if len(k):
                c.add("scorecard.kathmandu_spatial_rho", round(float(k[csp].iloc[0]), 3),
                      stat="Spearman rho, withheld stations", n=int(k["n"].iloc[0]),
                      source="multicity/validation_scorecard.csv", ledger="F.56",
                      note="the canonical value for this city. The figure script's own scoring "
                           "of a slightly different station set gives 0.428; one paper reports "
                           "one rank per city, and this is the panel-consistent one")
        if clv:
            c.add("scorecard.level_bias_median", round(float(sc[clv].median()), 1),
                  stat="median across cities", n=len(sc),
                  source="multicity/validation_scorecard.csv", ledger="F.9")
            c.add("scorecard.level_bias_hi", round(float(sc[clv].max()), 1), stat="max across cities",
                  n=len(sc), source="multicity/validation_scorecard.csv", ledger="F.9")

    # ── Kathmandu, the out-of-sample application of the same construction ─────────────────
    if (d := load("F8_kathmandu")):
        c.add("ktm.stations", d["stations"], stat="count", n=d["stations"],
              source="figdata/F8_kathmandu.json", ledger="F.9")
        c.add("ktm.scored_stations", d["scored_stations"], stat="count of WITHHELD stations",
              n=d["stations"], source="figdata/F8_kathmandu.json", ledger="F.9",
              note="two stations given, the rest withheld -- out of sample, unlike the Kandy cycles")
        c.add("ktm.seasonal_r", d["seasonal_r"], stat="Pearson r, monthly means", n=12,
              source="figdata/F8_kathmandu.json", ledger="F.9")
        c.add("ktm.diurnal_r", d["diurnal_r"], stat="Pearson r, hour-of-day means", n=24,
              source="figdata/F8_kathmandu.json", ledger="F.9")
        # NOT the spatial rank. The figure's own scoring gives 0.428 over 40 stations while the
        # canonical panel scorecard gives 0.392 over 39, because the two use different station
        # sets. Publishing both would put two ranks for one city in one paper, so the rank is
        # sourced from the scorecard alone (below) and the figure carries none on its face.
        c.add("ktm.level_bias_pct", d["level_bias_pct"], stat="percentage level bias",
              n=d["hours"], source="figdata/F8_kathmandu.json", ledger="F.9")

    # ── what the spatial nulls could have detected ────────────────────────────────────────
    p = REPO / "results/figures/multicity/reviewer_response_stats.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        rows = d.get("embedding_power") or d.get("rows") or []
        if rows:
            mdr = [float(r["min_detectable_r"]) for r in rows]
            c.add("null.min_detectable_lo", round(min(mdr), 2),
                  stat="smallest detectable partial correlation at 80% power", n=len(rows),
                  source="multicity/reviewer_response_stats.json", ledger="F.59",
                  note="a null at this sample size is a statement about power, not about nature")
            c.add("null.min_detectable_hi", round(max(mdr), 2),
                  stat="largest detectable partial correlation at 80% power", n=len(rows),
                  source="multicity/reviewer_response_stats.json", ledger="F.59")


def confounds(c: Claims) -> None:
    """F.51-F.53. The three confounds the registered gates caught, computed from the scored file."""
    d = pd.read_csv(MOD / "ladder_revalidated.csv")
    x = d[d.bottom == "Bud0c"]
    dt = x[x.band == "deep_tropical"]
    if len(dt):
        c.add("confound.deep_tropical_lcs_pct",
              round(100.0 * float((dt.cls == "LCS").mean()), 0), stat="share of cities", n=len(dt),
              source="ladder_revalidated.csv", ledger="F.52",
              note="instrument class x band: the deep-tropical cell is LCS-dominated and the rest "
                   "reference-dominated. This confound CANNOT be sampled away")
    rest = x[(x.band.notna()) & (x.band != "deep_tropical")]
    if len(rest):
        c.add("confound.other_bands_lcs_pct",
              round(100.0 * float((rest.cls == "LCS").mean()), 0), stat="share of cities",
              n=len(rest), source="ladder_revalidated.csv", ledger="F.52")


def lur(c: Claims) -> None:
    """F.61. The land-use regression that isolates sample size as one attribution channel."""
    p = MOD / "lur_r2.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    c.add("lur.median_stations_per_city", round(float(d.n.median()), 0), stat="median", n=len(d),
          source="lur_r2.csv", ledger="F.61",
          note="a point-to-point LUR fails on its own terms at this many stations -- far below "
               "what such designs require, which is how sample size is isolated in section 5.5")
    c.add("lur.cities", len(d), stat="count", n=len(d), source="lur_r2.csv", ledger="F.61")
    c.add("lur.predictors", int(d.n_pred.max()), stat="max", n=len(d), source="lur_r2.csv",
          ledger="F.61")


def donor(c: Claims) -> None:
    """F.54. The independent-background check, re-run 2026-09-05 on the corrected Bud0c rung.

    SOURCE CHANGED. This read `independent_background.csv`, which was scored on the pre-F.84
    bottom rung. Both of its arms shared that defect so its recovery FRACTION was largely
    protected, but its absolute gains sat against an artificially weak baseline and could not be
    quoted beside the current ladder. It now reads the re-run.

    The recovery fraction moved 79 -> 73 on the corrected rung. So the ratio was PARTIALLY
    protected, not fully: a stronger bottom rung leaves less headroom for any background to
    recover, and the independent one loses more of it than the own-network one. The conclusion
    is unchanged and the margin is smaller.

    Only ONE recovery statistic is published, the median of per-city ratios, matching every
    other ladder gain in this project. A ratio of medians gives 78 on the same file, and
    publishing both would put two numbers for one quantity into one document.
    """
    p = MOD / "independent_background_revalidated.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    dd = d[d.status == "ok"] if "status" in d.columns else d[d.donor.notna()]
    if not len(dd):
        return
    src = "independent_background_revalidated.csv"
    c.add("donor.pairs", len(dd), stat="count", n=len(dd), source=src, ledger="F.54",
          note="cities with an admissible independent donor in the 30-300 km window")
    c.add("donor.no_donor", int((d.status == "no donor in range").sum()) if "status" in d.columns
          else None, stat="count", n=int(d.city.nunique()), source=src, ledger="F.54",
          note="reported rather than dropped: the usable subsample is biased toward regions "
               "with dense city coverage, and the deep-tropical cell is the thinnest")
    c.add("donor.median_km", int(round(float(dd.d_km.median()))), stat="median", n=len(dd),
          source=src, ledger="F.54")

    def frac(sub: pd.DataFrame) -> pd.Series:
        k = 100.0 * (sub.rmse_Bud2 - sub.rmse_Bud3_indep) / (sub.rmse_Bud2 - sub.rmse_Bud3)
        return k.replace([np.inf, -np.inf], np.nan).dropna()

    keep = frac(dd)
    if len(keep):
        c.add("donor.gain_reproduced_pct", int(round(float(keep.median()))),
              stat="median of per-city ratios", n=len(keep), source=src, ledger="F.54",
              note="share of the background rung's gain reproduced by a genuinely INDEPENDENT "
                   "network. This BOUNDS the same-network artefact from above rather than "
                   "measuring it: the donors sit 30-300 km out while the own-network ring sits "
                   "5-15 km out, so independence is confounded with distance")

    near, far = dd[dd.d_km <= dd.d_km.median()], dd[dd.d_km > dd.d_km.median()]
    for lab, sub in (("near", near), ("far", far)):
        k = frac(sub)
        if len(k):
            c.add(f"donor.reproduced_{lab}", int(round(float(k.median()))),
                  stat="median of per-city ratios within the distance half", n=len(k),
                  source=src, ledger="F.54",
                  note="recovery falls with donor distance, which is the reason the residual "
                       "gap cannot be attributed to same-network sharing")
            c.add(f"donor.km_{lab}", int(round(float(sub.d_km.median()))),
                  stat="median donor distance in the half", n=len(sub), source=src, ledger="F.54")

    dt = dd[dd.band == "deep_tropical"] if "band" in dd.columns else dd.iloc[:0]
    k = frac(dt)
    if len(k):
        c.add("donor.reproduced_deep_tropical", int(round(float(k.median()))),
              stat="median of per-city ratios, deep-tropical band", n=len(k),
              source=src, ledger="F.54",
              note="Kandy's own band, and the weakest cell in the test: n is small and its "
                   "donors are the furthest away, so the independent evidence for the "
                   "background rung is thinnest exactly where the demonstration city sits")
        c.add("donor.km_deep_tropical", int(round(float(dt.d_km.median()))),
              stat="median donor distance, deep-tropical band", n=len(dt), source=src,
              ledger="F.54")


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
    s1(c)
    r2(c)
    s2(c)
    chemistry(c)
    c1_satellite(c)
    maiac_ladder(c)
    partition(c)
    kandy_field(c)
    domain_and_resolution(c)
    colombo_donor(c)
    sensor_design(c)
    campaign_power(c)
    campaign_cost(c)
    chemistry_deepening(c)
    ladder_order(c)
    learned_pattern(c)
    field_diagnostics(c)
    exposure_burden(c)
    nbro_pixel(c)
    kandy_application(c)
    confounds(c)
    blh_confound(c)
    dilution(c)
    lur_extra(c)
    lur(c)
    donor(c)
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
