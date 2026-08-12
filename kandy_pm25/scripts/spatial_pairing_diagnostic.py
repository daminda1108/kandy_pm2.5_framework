"""spatial_pairing_diagnostic.py — how much of the reported spatial rank is an artefact
of hour-matching? (2026-08-06)

WHY THIS EXISTS
---------------
`spatial_resolution_tests.py` computes each station's modelled and observed mean over the
SAME hours (an inner join on (hour, station)). The headline scorecard
(`city_validation_scorecard.py`) averages predictions over all modelled hours and
observations over all observed hours SEPARATELY, without aligning them.

The two disagree by a lot, and not in a consistent direction:

    Xichang     scorecard +0.07  ->  paired +0.75
    Chiang Mai  scorecard -0.06  ->  paired +0.82
    Bazhong     scorecard +0.10  ->  paired -0.22

That is a swing of 0.3 to 0.9 attributable to an undocumented sampling convention. It
is not a hidden reserve of skill -- it moves both ways -- it is INSTABILITY in the
statistic the paper's central negative result rests on.

WHAT THIS SCRIPT ESTABLISHES
----------------------------
1. ISOLATION. Compute both statistics from ONE merged frame, so the only difference is
   pairing. If the unpaired version reproduces the scorecard, the cause is isolated to
   hour-matching and nothing else (station set, domain filter, year span are shared).
2. NO JOIN DEFECT. Assert the merge is one-to-one on (loct, station_id) -- a
   many-to-many join would inflate a rank correlation for free.
3. THE MECHANISM. Report per-station observed-hour coverage and its dispersion. The
   hypothesis is that stations reporting over different periods acquire observed means
   that encode WHEN they reported rather than WHERE they are; if so, cities with uneven
   coverage should be the ones where the two statistics diverge most.
4. WHICH IS CORRECT. Paired is the like-for-like comparison and is defensible on its
   face. But it is not automatically right: it can reduce a city to few hours. Report
   the retained fraction so that trade-off is visible rather than assumed.

Run:  .venv/Scripts/python.exe scripts/spatial_pairing_diagnostic.py
Out:  results/figures/multicity/spatial_pairing_diagnostic.{csv,json}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import xichang_paper_figures as xf                       # noqa: E402

OUT = REPO / "results" / "figures" / "multicity"
CITIES = ["xichang", "chiangmai", "bazhou", "chandigarh", "kathmandu",
          "baoji", "taian", "yichang", "medellin", "bogota"]
MIN_ST = 4


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from scipy.stats import spearmanr
    sc = pd.read_csv(OUT / "validation_scorecard.csv")
    sc["key"] = sc.city.map(lambda s: s.split(" (")[0].strip())
    ref = dict(zip(sc.key, sc.spatial))

    print("=== is the spatial rank an artefact of hour-matching? ===\n")
    print("  city          scorecard   unpaired    paired    kept%   cov CV   n")
    rows = []
    for city in CITIES:
        try:
            xf._setup(city)
            st, anc = xf._stations_split()
            vault = [s for s in st.index if int(s) not in anc]
            P, O = [], []
            for y in xf.xp.YEARS:
                try:
                    P.append(xf._pred_at_stations(y)); O.append(xf._obs(y))
                except Exception:
                    continue
            P = pd.concat(P).dropna(subset=["pred"]); O = pd.concat(O)
            P = P[P.station_id.isin(vault)]; O = O[O.station_id.isin(vault)]

            # (2) one-to-one check BEFORE merging
            dupP = int(P.duplicated(["loct", "station_id"]).sum())
            dupO = int(O.duplicated(["loct", "station_id"]).sum())
            J = P.merge(O[["loct", "station_id", "pm25"]],
                        on=["loct", "station_id"], how="inner", validate="one_to_one"
                        if (dupP == 0 and dupO == 0) else "many_to_many")

            # (1) both statistics from the same frame
            up_p = P.groupby("station_id").pred.mean()
            up_o = O.groupby("station_id").pm25.mean()
            cu = up_p.index.intersection(up_o.index)
            rho_unpaired = (spearmanr(up_p[cu], up_o[cu])[0]
                            if len(cu) >= MIN_ST else np.nan)
            pp = J.groupby("station_id").pred.mean()
            po = J.groupby("station_id").pm25.mean()
            cp_ = pp.index.intersection(po.index)
            rho_paired = (spearmanr(pp[cp_], po[cp_])[0]
                          if len(cp_) >= MIN_ST else np.nan)

            # (3) coverage dispersion + (4) retained fraction
            cov = J.groupby("station_id").size()
            cov_cv = float(cov.std() / cov.mean()) if len(cov) > 1 else np.nan
            kept = 100.0 * len(J) / max(1, len(O))
            key = xf.CFG["name"].split(" (")[0].strip()
            rows.append(dict(city=key, scorecard=ref.get(key), unpaired=rho_unpaired,
                             paired=rho_paired, kept_pct=kept, cov_cv=cov_cv,
                             n_ranked=len(cp_), dup_pred=dupP, dup_obs=dupO,
                             n_paired_rows=int(len(J))))
            print(f"  {key:<13}"
                  f"{'' if ref.get(key) is None or not np.isfinite(ref.get(key, np.nan)) else f'{ref[key]:+.2f}':>9}"
                  f"{'' if not np.isfinite(rho_unpaired) else f'{rho_unpaired:+.2f}':>11}"
                  f"{'' if not np.isfinite(rho_paired) else f'{rho_paired:+.2f}':>10}"
                  f"{kept:>8.0f}{cov_cv:>9.2f}{len(cp_):>5}"
                  + ("   <-- DUPLICATE KEYS" if (dupP or dupO) else ""))
        except Exception as e:                                       # noqa: BLE001
            print(f"  {city:<13} SKIP ({type(e).__name__}: {e})")

    R = pd.DataFrame(rows)
    R.to_csv(OUT / "spatial_pairing_diagnostic.csv", index=False)

    ok = R.dropna(subset=["scorecard", "unpaired"])
    repro = float(np.nanmax(np.abs(ok.scorecard - ok.unpaired))) if len(ok) else np.nan
    d = (R.paired - R.scorecard).dropna()
    res = {
        "reproduces_scorecard_within": None if not np.isfinite(repro) else round(repro, 4),
        "isolated_to_pairing": bool(np.isfinite(repro) and repro < 0.05),
        "any_duplicate_keys": bool(R[["dup_pred", "dup_obs"]].to_numpy().sum() > 0),
        "delta_paired_minus_scorecard": {
            "values": {r.city: None if not np.isfinite(r.paired - (r.scorecard or np.nan))
                       else round(float(r.paired - r.scorecard), 3)
                       for r in R.itertuples()},
            "mean_abs": None if d.empty else round(float(d.abs().mean()), 3),
            "max_abs": None if d.empty else round(float(d.abs().max()), 3),
            "both_directions": bool((d > 0).any() and (d < 0).any())},
        "coverage_cv": {r.city: None if not np.isfinite(r.cov_cv) else round(float(r.cov_cv), 3)
                        for r in R.itertuples()}}
    if len(d) >= 4:
        cv = R.dropna(subset=["cov_cv"]).set_index("city").cov_cv
        j = pd.concat([d.rename("delta"), cv], axis=1).dropna()
        if len(j) >= 4:
            res["corr_absdelta_vs_coverage_cv"] = round(
                float(np.corrcoef(j.delta.abs(), j.cov_cv)[0, 1]), 3)

    print("\n" + "=" * 66)
    print(f"  unpaired reproduces the scorecard to within {repro:.3f}"
          f"  -> cause {'ISOLATED to hour-matching' if res['isolated_to_pairing'] else 'NOT isolated -- something else differs too'}")
    print(f"  duplicate merge keys anywhere: {res['any_duplicate_keys']}")
    print(f"  |paired - scorecard|: mean {res['delta_paired_minus_scorecard']['mean_abs']}, "
          f"max {res['delta_paired_minus_scorecard']['max_abs']}, "
          f"both directions {res['delta_paired_minus_scorecard']['both_directions']}")
    if "corr_absdelta_vs_coverage_cv" in res:
        print(f"  corr(|shift|, coverage unevenness) = {res['corr_absdelta_vs_coverage_cv']}"
              "   (the mechanism predicts positive)")
    res["verdict"] = (
        ("The spatial rank statistic is UNSTABLE to an undocumented sampling convention. "
         "It shifts in BOTH directions, so this is not understated skill; it is a defect "
         "in the measurement on which the paper's central spatial result rests. The "
         "bootstrap intervals of F.26 hold the convention fixed and therefore understate "
         "the true uncertainty."
         if res["delta_paired_minus_scorecard"]["both_directions"] else
         "The shift is one-directional; investigate further before interpreting.")
        + (" Hour-matched (paired) means are the like-for-like comparison and are the "
           "defensible default, but the retained-hour fraction must be reported alongside, "
           "because pairing can reduce a city to few hours."))
    print(f"\n  VERDICT: {res['verdict']}")
    (OUT / "spatial_pairing_diagnostic.json").write_text(
        json.dumps(res, indent=1, default=float), encoding="utf-8")
    print("\nwrote spatial_pairing_diagnostic.{csv,json}")


if __name__ == "__main__":
    main()
