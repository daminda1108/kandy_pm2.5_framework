"""siting_experiment.py -- does DELIBERATE siting actually beat CONVENIENCE siting?

THE QUESTION THIS RESOLVES. The campaign design rests on a premise the power calculation said a
single city cannot test: that siting monitors across the covariate space recovers spatial pattern
that a convenience-sited network cannot. One city has too few sites to detect it. But the panel
has 47 cities whose networks are already dense, and each of them can be MADE into both designs by
choosing which of its own stations to fit on.

That is the resolution. Instead of arguing from D-efficiency about which design ought to be
better, take a city with many stations, select a fitting subset four different ways, fit the same
model on each, and score every one of them against the SAME held-out stations. Whatever wins,
wins on measured out-of-sample skill.

  clhs         conditioned Latin hypercube over the station covariates. The proposed design.
  convenience  the stations with the most road nearby. What compliance networks actually do,
               and what produced every frame this project has measured a null on.
  spread       maximin geographic separation. The naive "cover the map" design.
  random       the baseline any proposal has to beat.

WHY THE MODEL MUST BE MULTI-COVARIATE. If the spatial prediction were a monotone function of one
covariate, the choice of fitting stations could not change the RANKING of the held-out ones, and
the experiment would be vacuous by construction. A multi-covariate fit is what makes the fitting
set matter, and it is also what a land-use regression actually is.

⚠ A CONFOUND THIS DESIGN CARRIES, stated before the result is known. Each method chooses its own
fitting stations, so each is scored on a DIFFERENT held-out set. A method could therefore win by
leaving an easier remainder rather than by fitting better. That is defensible as the practical
comparison, because siting a network really does determine both what you fit on and what you are
later judged against, but it is not a clean estimate of fitting quality alone. If a method wins
here, the difference has to be re-checked against a FIXED held-out set before it is believed.

WHAT A POSITIVE RESULT WOULD MEAN. Published land-use regression reaches R2 0.43 to 0.83 while
this project's convenience-sampled frames reach a rank correlation near 0.3. If deliberate siting
wins here, that gap is a sampling artefact and the campaign is justified. If it does not, the gap
is information and the campaign should be re-scoped. **Either way the answer is measured rather
than argued, on 44 cities rather than on one.**

Usage: python scripts/siting_experiment.py [--reps 40]
Out:   data/processed/modular/siting_experiment.csv
       data/processed/modular/siting_experiment.json
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import RidgeCV

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
warnings.filterwarnings("ignore")
from design_sensor_network import clhs  # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "siting_experiment.csv"
OUT_JSON = MOD / "siting_experiment.json"

MIN_STATIONS = 10
SEED = 20260906

# A small, fixed covariate set. Deliberately short: the fitting subsets are 5 to 24 stations, and
# a 60-predictor fit on five points would measure the regulariser rather than the siting.
COVARS = ["lc_built_2400", "lc_built_300", "ntl_1000", "pop_1000",
          "ndvi_1000", "road_major_300", "dist_major_km"]


def pick(method, X, Xs, sub, k, rng):
    """Choose k fitting stations by one of the four strategies."""
    n = len(sub)
    if method == "random":
        return list(rng.choice(n, k, replace=False))
    if method == "clhs":
        return list(clhs(Xs, k, int(rng.integers(1 << 30))))
    if method == "convenience":
        # most road nearby: what a compliance network is sited for
        return list(np.argsort(-sub["road_major_300"].to_numpy())[:k])
    if method == "spread":
        # maximin: greedily take the station furthest from those already chosen
        la = sub.lat.to_numpy(); lo = sub.lon.to_numpy()
        chosen = [int(rng.integers(n))]
        while len(chosen) < k:
            d = np.min(np.hypot(la[:, None] - la[chosen], lo[:, None] - lo[chosen]), axis=1)
            d[chosen] = -1
            chosen.append(int(np.argmax(d)))
        return chosen
    raise ValueError(method)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=40)
    ap.add_argument("--fixed-holdout", action="store_true",
                    help="score every method on the SAME held-out third")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()

    d = pd.read_csv(MOD / "lur_predictors.csv")
    cols = [c for c in COVARS if c in d.columns]
    d = d.dropna(subset=cols + ["pm", "lat", "lon"])
    counts = d.groupby("city").size()
    cities = counts[counts >= MIN_STATIONS].index
    print("=== does deliberate siting beat convenience siting? ===")
    print(f"    {len(cities)} cities with at least {MIN_STATIONS} stations, "
          f"{int(counts[cities].sum())} stations, {len(cols)} covariates")
    print(f"    half of each city's stations are fitted on, half held out, "
          f"{a.reps} repeats per city\n")

    rng = np.random.default_rng(SEED)
    rows = []
    for city in cities:
        sub = d[d.city == city].reset_index(drop=True)
        n = len(sub)
        k = max(4, n // 2)
        if n - k < 4:
            continue
        X = sub[cols].to_numpy(float)
        Xs = (X - X.mean(0)) / (X.std(0) + 1e-12)
        y = sub["pm"].to_numpy(float)
        for rep in range(a.reps):
            # FIXED-HOLDOUT MODE. Every method is scored on the SAME held-out third and picks
            # its fitting set from the same remaining two thirds, which removes the confound
            # that a method could win by leaving an easier remainder. Promised in the docstring
            # as the check any winner had to survive; run because the paired and unpaired
            # answers disagreed, which is a reason to remove a confound whichever way it points.
            # [!] ON THIS PANEL THIS MODE IS UNINFORMATIVE, and the reason is arithmetic. The
            # median city has 12 stations, so a held-out third is 4, and a Spearman correlation
            # on 4 points is quantised to steps of 0.1 with only a handful of attainable values
            # (the observed run's three commonest were exactly 0.4, 0.8 and -0.4). Every paired
            # median then collapses to exactly zero with a zero-width interval. The check was
            # promised and it was run; it returned nothing usable, which is a limit of the
            # panel's city sizes and NOT a confirmation of the primary result. Settling it would
            # need cities of 24 or more stations to leave a held-out set of 8, and about five
            # such cities exist.
            if a.fixed_holdout:
                perm = rng.permutation(n)
                n_hold = max(4, n // 3)
                held_fixed = list(perm[:n_hold])
                pool_idx = list(perm[n_hold:])
                kk = max(4, len(pool_idx) // 2)
                if len(pool_idx) < kk or len(held_fixed) < 4:
                    continue
                psub = sub.iloc[pool_idx].reset_index(drop=True)
                pXs = Xs[pool_idx]
            for method in ("clhs", "convenience", "spread", "random"):
                if a.fixed_holdout:
                    sel = pick(method, X[pool_idx], pXs, psub, kk, rng)
                    idx = [pool_idx[i] for i in sel]
                    held = held_fixed
                else:
                    idx = pick(method, X, Xs, sub, k, rng)
                    held = [i for i in range(n) if i not in set(idx)]
                if len(held) < 4 or len(set(idx)) < 4:
                    continue
                try:
                    m = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(Xs[idx], y[idx])
                    pred = m.predict(Xs[held])
                except Exception:
                    continue
                if np.std(pred) < 1e-9 or np.std(y[held]) < 1e-9:
                    continue
                rho = spearmanr(pred, y[held]).statistic
                if np.isfinite(rho):
                    rows.append(dict(city=city, band=sub.band.iloc[0], method=method,
                                     rep=rep, k=len(idx), n_held=len(held),
                                     rho=float(rho)))
    r = pd.DataFrame(rows)
    tag = ("_" + a.tag) if a.tag else ""
    out_csv = OUT.with_name(OUT.stem + tag + OUT.suffix)
    out_json = OUT_JSON.with_name(OUT_JSON.stem + tag + OUT_JSON.suffix)
    r.to_csv(out_csv, index=False)

    # median over repeats within city first, so a city with many repeats does not dominate
    per_city = r.groupby(["city", "band", "method"]).rho.median().reset_index()
    piv = per_city.pivot_table(index=["city", "band"], columns="method", values="rho")
    print(f"=== held-out rank correlation, median across {piv.shape[0]} cities ===")
    print(f"    {'method':<14}{'median rho':>12}{'cities best':>14}")
    best = piv.idxmax(axis=1).value_counts()
    for m in ("clhs", "convenience", "spread", "random"):
        if m in piv:
            print(f"    {m:<14}{piv[m].median():>12.3f}{best.get(m, 0):>14}")

    print(f"\n=== paired against convenience siting, bootstrap over cities ===")
    out = {}
    for m in ("clhs", "spread", "random"):
        if m not in piv or "convenience" not in piv:
            continue
        s = piv[[m, "convenience"]].dropna()
        v = (s[m] - s["convenience"]).to_numpy()
        idx = rng.integers(0, len(v), (4000, len(v)))
        mm = np.median(v[idx], axis=1)
        lo, hi = np.percentile(mm, [2.5, 97.5])
        out[m] = dict(median=round(float(np.median(v)), 4), lo=round(float(lo), 4),
                      hi=round(float(hi), 4), n=int(len(v)),
                      wins=int((v > 0).sum()))
        flag = "YES" if lo > 0 else ("worse" if hi < 0 else "no")
        print(f"    {m:<14}{np.median(v):>+8.4f}   [{lo:>+7.4f}, {hi:>+7.4f}]   "
              f"beats in {int((v > 0).sum())}/{len(v)}   detectable: {flag}")

    cl = out.get("clhs", {})
    print(f"\n=== the answer ===")
    if cl and cl["lo"] > 0:
        print(f"    Deliberate siting BEATS convenience siting by {cl['median']:+.3f} in rank")
        print(f"    correlation, and the interval excludes zero. The campaign's premise holds,")
        print(f"    and the spatial gap is partly a SAMPLING artefact.")
    elif cl and cl["hi"] < 0:
        print(f"    Deliberate siting is WORSE than convenience siting. The premise is refuted")
        print(f"    and the design stratum should be re-scoped or dropped.")
    else:
        print(f"    NOT DETECTABLE on this frame: {cl.get('median')} "
              f"[{cl.get('lo')}, {cl.get('hi')}].")
        print(f"    Deliberate siting does not measurably beat convenience siting for spatial")
        print(f"    prediction, which is evidence that the spatial gap is INFORMATION rather")
        print(f"    than sampling, and the design stratum cannot be justified by this route.")

    summary = dict(cities=int(piv.shape[0]), stations=int(counts[cities].sum()),
                   covariates=cols, min_stations=MIN_STATIONS, reps=a.reps,
                   median_rho={m: round(float(piv[m].median()), 4)
                               for m in piv.columns},
                   best_counts={str(k): int(v) for k, v in best.items()},
                   paired_vs_convenience=out)
    summary["fixed_holdout"] = bool(a.fixed_holdout)
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    # Print what was actually WRITTEN, not the default names. The first fixed-holdout run
    # reported "siting_experiment.json" while writing "siting_experiment_fixed.json", which
    # for a few minutes looked as though it had overwritten the primary result.
    print(f"\n-> {out_csv.name}, {out_json.name}")


if __name__ == "__main__":
    main()
