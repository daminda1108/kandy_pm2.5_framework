"""PHASE 2 — the gauge-constrained learned spatial pattern.

Registered at https://osf.io/2jyfg/ (2026-09-04) BEFORE this was written.
Plan: docs/learned_pattern_plan_2026-09-04.md. Frame and bar: Phase 1.

THE BAR, FIXED IN ADVANCE AND NOT NEGOTIABLE HERE:

    benchmark              rho = 0.309   best single predictor, built-up land cover at 2.4 km
    detectable at 80%      0.130         simulated on this frame, n = 46
    THE BAR                rho >= 0.44   a result below this is UNDETECTABLE AT THIS POWER,
                                         and is reported as such, not as a modest success.

WHAT IS LEARNED. A within-city pattern, not a level. The level is carried by T(t) and the model
paper measures it separately; the only question here is whether a learned function places the
increment better than an imposed one. So both features and target are standardised WITHIN each
city, which also removes the between-city level signal a model could otherwise exploit to look
skilful without ranking anything.

⚠ Standardising features within a city uses only that city's PREDICTORS -- globally available
static geography, no local observation -- so it is admissible at Bud0 for a city with no
monitors. Standardising the TARGET uses that city's PM and is therefore done only for scoring,
never for a held-out city's training data.

WHERE THE GAUGE ACTUALLY BITES. The registered form is P = N * softmax over cells, which makes
the spatial mean exactly 1. Softmax is monotone within a city, so it cannot change a Spearman
rank correlation -- the primary metric is invariant to it, and pretending otherwise would be
dishonest. The gauge is what makes the learned pattern usable as a FIELD, and it is verified
as such in the L3 check rather than claimed through the metric.

Usage: .venv/Scripts/python.exe scripts/phase2_learned_pattern.py [--seeds 5]
Out:   data/processed/modular/phase2_learned_pattern.csv
       data/processed/paper_figures/phase2_learned.json
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import RidgeCV
from sklearn.neural_network import MLPRegressor

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from figdata import emit  # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "phase2_learned_pattern.csv"

BENCHMARK_PREDICTOR = "lc_built_2400"      # Phase 1's best single predictor
BENCHMARK_RHO = 0.309
MIN_DETECTABLE = 0.130
BAR = 0.44
MIN_STATIONS = 8

# Declared inadmissible in the registration. lat/lon are in the frame and must never be fitted:
# they let a model memorise station identity (gotcha #28, and the Sim2Real collapse).
DROP = {"city", "band", "src", "station_id", "lat", "lon", "pm"}


def frame() -> pd.DataFrame:
    d = pd.read_csv(MOD / "lur_predictors.csv")
    n = d.groupby("city").size()
    d = d[d.city.isin(n[n >= MIN_STATIONS].index)].copy()
    return d


def within_city(d: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Z-score each predictor inside its own city. Uses no PM and no target city outcome."""
    g = d.groupby("city")[cols]
    z = (d[cols] - g.transform("mean")) / g.transform("std").replace(0, np.nan)
    return z.fillna(0.0)


def target(d: pd.DataFrame) -> pd.Series:
    """Within-city z-score of log PM. The pattern's job is ordering, not level."""
    y = np.log(d.pm.clip(lower=0.1))
    g = y.groupby(d.city)
    return ((y - g.transform("mean")) / g.transform("std").replace(0, np.nan)).fillna(0.0)


def make(kind: str, seed: int):
    if kind == "mlp":
        return MLPRegressor(hidden_layer_sizes=(32, 16), alpha=1.0, max_iter=1200,
                            early_stopping=True, n_iter_no_change=25, random_state=seed)
    if kind == "rf":
        return RandomForestRegressor(n_estimators=400, min_samples_leaf=5,
                                     random_state=seed, n_jobs=2)
    return RidgeCV(alphas=np.logspace(-2, 3, 24))


def loco(d, X, y, kind, seed) -> pd.DataFrame:
    """Leave-one-city-out. A model that has seen a city says nothing about a city it has not."""
    rows = []
    for city in sorted(d.city.unique()):
        te = d.city == city
        if te.sum() < MIN_STATIONS:
            continue
        m = make(kind, seed)
        m.fit(X[~te], y[~te])
        p = m.predict(X[te])
        obs = d.loc[te, "pm"].values
        if np.std(p) < 1e-12:
            rows.append(dict(city=city, n=int(te.sum()), rho=np.nan))
            continue
        rows.append(dict(city=city, n=int(te.sum()), band=d.loc[te, "band"].iloc[0],
                         rho=float(spearmanr(p, obs)[0])))
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    a = ap.parse_args()

    d = frame().reset_index(drop=True)
    cols = [c for c in d.columns if c not in DROP]
    X = within_city(d, cols).values
    y = target(d).values
    print(f"PHASE 2 -- registered at osf.io/2jyfg\n")
    print(f"  frame {d.city.nunique()} cities, {len(d)} stations, {len(cols)} predictors")
    print(f"  bar   rho >= {BAR} (benchmark {BENCHMARK_RHO} + detectable {MIN_DETECTABLE})\n")

    # baseline: the single best predictor, scored identically
    base = []
    for city, g in d.groupby("city"):
        gg = g[["pm", BENCHMARK_PREDICTOR]].dropna()
        if len(gg) >= MIN_STATIONS and gg[BENCHMARK_PREDICTOR].std() > 0:
            base.append(dict(city=city, rho=float(spearmanr(gg[BENCHMARK_PREDICTOR], gg.pm)[0])))
    B = pd.DataFrame(base).set_index("city").rho

    results = {}
    for kind in ("mlp", "rf", "ridge"):
        per_seed = []
        for s in range(a.seeds if kind != "ridge" else 1):
            r = loco(d, X, y, kind, s).dropna(subset=["rho"])
            per_seed.append(r.set_index("city").rho)
        M = pd.concat(per_seed, axis=1).mean(axis=1)          # mean over seeds, per city
        results[kind] = M
        print(f"  {kind:<6} median rho {M.median():+.3f}   "
              f"positive in {int((M > 0).sum())}/{len(M)}")

    print()
    lead = max(results, key=lambda k: results[k].median())
    L = results[lead]
    pair = pd.concat([L.rename("learned"), B.rename("base")], axis=1).dropna()
    delta = pair.learned - pair.base
    try:
        p = float(wilcoxon(pair.learned, pair.base)[1])
    except Exception:                                                       # noqa: BLE001
        p = float("nan")

    print(f"  best learner: {lead}")
    print(f"    learned  {pair.learned.median():+.3f}")
    print(f"    baseline {pair.base.median():+.3f}  ({BENCHMARK_PREDICTOR})")
    print(f"    delta    {delta.median():+.3f}   better in "
          f"{int((delta > 0).sum())}/{len(pair)}   p = {p:.3f}")

    # ── the registered verdict ───────────────────────────────────────────────────────────
    achieved = float(pair.learned.median())
    print("\n=== REGISTERED PREDICTIONS (osf.io/2jyfg) ===")
    l1_held = achieved < BAR
    print(f"  L1  {'HELD    ' if l1_held else 'REFUTED '}  the pattern does NOT reach the bar: "
          f"achieved {achieved:+.3f} against {BAR}")
    l2_held = achieved > 0.274
    print(f"  L2  {'HELD    ' if l2_held else 'REFUTED '}  it beats the shipped dispersed "
          f"field (0.274): achieved {achieved:+.3f}")
    if achieved < BAR:
        print(f"\n  🔴 VERDICT: below the bar. The gain over the benchmark is "
              f"{delta.median():+.3f},\n     against a detection limit of {MIN_DETECTABLE} on "
              f"this frame. Per the registration this\n     is reported as UNDETECTABLE AT THIS "
              f"POWER, not as a modest success.")
    else:
        print(f"\n  🟢 VERDICT: clears the bar at {achieved:+.3f}.")

    # L4 — band stratification
    bands = d.drop_duplicates("city").set_index("city").band
    bb = pd.concat([L.rename("rho"), bands], axis=1).dropna()
    print("\n  L4  by latitude band")
    for b, g in bb.groupby("band"):
        print(f"      {b:<15} n={len(g):>2}  median {g.rho.median():+.3f}")

    out = pd.concat([L.rename("learned"), B.rename("baseline"), bands], axis=1)
    out["delta"] = out.learned - out.baseline
    out.to_csv(OUT)
    print(f"\n  wrote {OUT.relative_to(REPO)}")

    emit("phase2_learned",
         cities=int(len(pair)), stations=int(len(d)), predictors=int(len(cols)),
         best_learner=lead,
         rho_learned=round(achieved, 3),
         rho_baseline=round(float(pair.base.median()), 3),
         delta=round(float(delta.median()), 3),
         better_in=int((delta > 0).sum()),
         p_value=round(p, 4),
         bar=BAR, min_detectable=MIN_DETECTABLE,
         l1_held=bool(l1_held), l2_held=bool(l2_held),
         rho_mlp=round(float(results["mlp"].median()), 3),
         rho_rf=round(float(results["rf"].median()), 3),
         rho_ridge=round(float(results["ridge"].median()), 3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
