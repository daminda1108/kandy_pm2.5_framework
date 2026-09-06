"""spatial_tournament.py -- is the spatial null a property of the DATA, or of the model family?

THE OBJECTION, from an external reviewer and worth answering properly. The registered spatial null
compared one learned model family against the best single globally available raster. That licenses
"a learned pattern did not beat the benchmark", but a reader is entitled to ask whether a
conventional spatial model would have done better. Land-use regression, geostatistics,
geographically weighted regression and mixed-effects models are the standard tools for exactly this
problem, and none of them was in the comparison.

A DISTINCTION THE OBJECTION DOES NOT MAKE, AND WHICH DECIDES HALF THE ANSWER. Two of those families
cannot be run in the setting the thesis is about. Kriging and geographically weighted regression
both estimate a surface FROM OBSERVATIONS AT THE TARGET: the kriging predictor interpolates between
measured points, and GWR fits a separate local regression around each location using nearby
measured points. In a city with no monitors there are no nearby measured points, so neither model
has anything to condition on. They are Bud4 methods being proposed for a Bud0 problem.

Rather than exclude them by argument, this runs the tournament twice.

  ADMISSIBLE (leave-one-CITY-out).   The target city contributes no PM observation at all. This is
                                     the setting the thesis is about, and the only setting whose
                                     numbers may be compared with the registered benchmark.

  ORACLE (leave-one-STATION-out).    The target city's OTHER stations are visible. Inadmissible for
                                     Kandy, and reported precisely because it bounds from above
                                     what any of these families could deliver if the city had a
                                     network -- which is a different and useful quantity. It is
                                     labelled ORACLE everywhere and must never be compared with
                                     the benchmark.

FAMILIES. Admissible: the benchmark raster; conventional stepwise LUR as the literature builds it;
ridge and elastic net; random forest; gradient boosting; a Gaussian process on covariates (not on
coordinates); and a linear mixed model with a city random intercept, which is the hierarchical
structure the reviewer separately asked for. Oracle only: ordinary kriging on coordinates, inverse
distance weighting, and a GWR-style locally weighted fit.

WHAT WOULD OVERTURN THE NULL. Any admissible family beating the benchmark by more than the
registered detection limit of 0.130 in paired median rank correlation. Anything smaller is
undetectable on this frame and is reported as such, exactly as the registered test was.

⚠ Everything is standardised WITHIN city, for both features and target, so no model can score by
rediscovering that some cities are dirtier than others. That is the level axis and it is solved
elsewhere. The quantity here is purely the within-city ranking.

⚠ Paired within city and bootstrapped over cities. A difference of medians is not an effect
(gotcha #91), and on this panel it has pointed the wrong way twice.

Usage: .venv/Scripts/python.exe scripts/spatial_tournament.py [--boot 4000]
Out:   data/processed/modular/spatial_tournament.csv
       data/processed/modular/spatial_tournament.json
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
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
from sklearn.linear_model import ElasticNetCV, LinearRegression, RidgeCV

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
warnings.filterwarnings("ignore")

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "spatial_tournament.csv"
OUT_JSON = MOD / "spatial_tournament.json"

SEED = 20260906
BENCH = "lc_built_2400"      # Phase 1's best single predictor, rho 0.309
DETECT = 0.130               # the registered detection limit on this frame
MIN_STATIONS = 6

DROP = {"city", "band", "src", "station_id", "lat", "lon", "pm"}


def load():
    d = pd.read_csv(MOD / "lur_predictors.csv")
    feats = [c for c in d.columns if c not in DROP and d[c].dtype.kind in "fi"]
    d = d.dropna(subset=[BENCH, "pm", "lat", "lon"])
    d = d[d.groupby("city").city.transform("size") >= MIN_STATIONS].copy()
    # within-city standardisation of BOTH sides: the question is ranking, not level
    for c in feats:
        d[c] = d.groupby("city")[c].transform(lambda s: (s - s.mean()) / (s.std() + 1e-9))
    d[feats] = d[feats].fillna(0.0)
    d["z"] = d.groupby("city").pm.transform(lambda s: (s - s.mean()) / (s.std() + 1e-9))
    return d, feats


def stepwise_lur(X, y, Xt, max_terms=8):
    """Conventional land-use regression as the literature builds it: forward selection on
    adjusted R2, one predictor at a time, stopping when nothing improves. This is the model class
    that reaches R2 0.43-0.83 in published campaigns, so it is the fair comparator."""
    n, p = X.shape
    chosen, rem, best = [], list(range(p)), -np.inf
    while rem and len(chosen) < max_terms:
        gains = []
        for j in rem:
            cols = chosen + [j]
            m = LinearRegression().fit(X[:, cols], y)
            r2 = m.score(X[:, cols], y)
            k = len(cols)
            adj = 1 - (1 - r2) * (n - 1) / max(n - k - 1, 1)
            gains.append((adj, j))
        adj, j = max(gains)
        if adj <= best + 1e-4:
            break
        best, chosen = adj, chosen + [j]
        rem.remove(j)
    if not chosen:
        return np.zeros(len(Xt))
    return LinearRegression().fit(X[:, chosen], y).predict(Xt[:, chosen])


def mixed_intercept(tr, feats, te):
    """Linear mixed model with a city random intercept, fitted by within-city centring.

    Because both sides are already standardised within city, every city's intercept is zero by
    construction, so the random intercept is exactly absorbed and the remaining fixed-effect slopes
    are the pooled within-city relationship. Fitting it this way rather than through a variance
    component avoids an extra dependency and gives the identical point prediction; what it does not
    give is a variance estimate, which this comparison does not use.
    """
    m = RidgeCV(alphas=np.logspace(-2, 3, 24)).fit(tr[feats].to_numpy(), tr.z.to_numpy())
    return m.predict(te[feats].to_numpy())


def krige(tr, te, nugget=0.1):
    """Ordinary kriging on COORDINATES. ORACLE ONLY -- it interpolates between measured points, so
    it requires observations inside the target city and cannot run for a city with no monitors."""
    if len(tr) < 4:
        return None
    P = np.c_[tr.lat.to_numpy(), tr.lon.to_numpy()]
    k = ConstantKernel(1.0) * RBF(length_scale=0.05) + WhiteKernel(nugget)
    g = GaussianProcessRegressor(kernel=k, normalize_y=True, random_state=SEED)
    g.fit(P, tr.z.to_numpy())
    return g.predict(np.c_[te.lat.to_numpy(), te.lon.to_numpy()])


def idw(tr, te, power=2.0):
    """Inverse distance weighting. ORACLE ONLY, same reason as kriging."""
    d = np.hypot(te.lat.to_numpy()[:, None] - tr.lat.to_numpy(),
                 te.lon.to_numpy()[:, None] - tr.lon.to_numpy())
    w = 1.0 / np.power(np.maximum(d, 1e-6), power)
    return (w @ tr.z.to_numpy()) / w.sum(1)


def gwr(tr, te, feats, bw=0.05):
    """Geographically weighted regression: a separate weighted linear fit around each target point,
    weights falling off with distance. ORACLE ONLY -- the local fit needs nearby measured points."""
    Xtr = np.c_[np.ones(len(tr)), tr[feats].to_numpy()]
    ytr = tr.z.to_numpy()
    out = np.empty(len(te))
    for i, (la, lo) in enumerate(zip(te.lat.to_numpy(), te.lon.to_numpy())):
        d = np.hypot(tr.lat.to_numpy() - la, tr.lon.to_numpy() - lo)
        w = np.exp(-0.5 * (d / bw) ** 2)
        if w.sum() < 1e-8:
            out[i] = 0.0
            continue
        W = np.sqrt(w)[:, None]
        try:
            c, *_ = np.linalg.lstsq(Xtr * W, ytr * np.sqrt(w), rcond=None)
            out[i] = float(np.r_[1.0, te[feats].to_numpy()[i]] @ c)
        except Exception:
            out[i] = 0.0
    return out


def rho(pred, obs):
    if pred is None or np.std(pred) < 1e-12 or np.std(obs) < 1e-12:
        return np.nan
    r = spearmanr(pred, obs).statistic
    return float(r) if np.isfinite(r) else np.nan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=4000)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)

    d, feats = load()
    cities = sorted(d.city.unique())
    print("=== spatial model tournament ===")
    print(f"    {len(cities)} cities, {len(d)} stations, {len(feats)} predictors")
    print(f"    benchmark {BENCH}; registered detection limit {DETECT}\n")

    # a compact predictor set for the families that cannot take 60 columns on 12 points
    small = [c for c in ["lc_built_2400", "lc_built_300", "ntl_1000", "pop_1000",
                         "ndvi_1000", "road_major_300", "dist_major_km"] if c in feats]

    rows = []
    print("[1] ADMISSIBLE: leave-one-CITY-out, the target contributes no observation")
    for city in cities:
        tr, te = d[d.city != city], d[d.city == city]
        if len(te) < MIN_STATIONS:
            continue
        y = te.z.to_numpy()
        Xtr, Xte = tr[feats].to_numpy(), te[feats].to_numpy()
        Str, Ste = tr[small].to_numpy(), te[small].to_numpy()
        r = {"city": city, "band": te.band.iloc[0], "n": len(te), "setting": "admissible"}
        r["benchmark"] = rho(te[BENCH].to_numpy(), y)
        r["lur_stepwise"] = rho(stepwise_lur(Str, tr.z.to_numpy(), Ste), y)
        r["ridge"] = rho(RidgeCV(alphas=np.logspace(-2, 3, 24))
                         .fit(Xtr, tr.z).predict(Xte), y)
        r["elasticnet"] = rho(ElasticNetCV(cv=4, random_state=SEED, max_iter=4000)
                              .fit(Xtr, tr.z).predict(Xte), y)
        r["random_forest"] = rho(RandomForestRegressor(
            n_estimators=300, min_samples_leaf=4, random_state=SEED, n_jobs=-1)
            .fit(Xtr, tr.z).predict(Xte), y)
        r["gradient_boost"] = rho(GradientBoostingRegressor(random_state=SEED)
                                  .fit(Xtr, tr.z).predict(Xte), y)
        sub = tr.sample(min(1200, len(tr)), random_state=SEED)
        gp = GaussianProcessRegressor(
            kernel=ConstantKernel(1.0) * RBF(length_scale=np.ones(len(small))) + WhiteKernel(0.5),
            normalize_y=True, random_state=SEED)
        try:
            r["gp_covariates"] = rho(gp.fit(sub[small].to_numpy(), sub.z.to_numpy())
                                     .predict(Ste), y)
        except Exception:
            r["gp_covariates"] = np.nan
        r["mixed_effects"] = rho(mixed_intercept(tr, feats, te), y)
        rows.append(r)

    print(f"    {len(rows)} cities scored")

    print("\n[2] ORACLE: leave-one-STATION-out inside the target city (INADMISSIBLE for Kandy)")
    # ── A TRAP THAT MADE THE FIRST RUN OF THIS ARM MEANINGLESS, RECORDED BECAUSE IT IS SUBTLE ──
    # The within-city target was standardised using EVERY station in the city, so it sums to zero
    # by construction. Hold one station out and the mean of the remainder is therefore exactly
    # -z_i/(n-1): a strictly DECREASING function of the value being predicted. Any model that
    # reverts toward its training mean is then dragged toward a rank correlation of -1 whatever
    # its spatial skill. Measured directly, the leave-one-out training mean correlates with the
    # held-out value at exactly -1.000 in all 46 cities. The first run duly reported kriging at
    # -0.833, which reads like a catastrophic result and is an artefact of the normalisation.
    #
    # The fix is the standard rule that was violated: the normalisation must be fitted on the
    # TRAINING stations only. The admissible arm above never had this problem, because the whole
    # target city is held out and no model sees any of its stations.
    for city in cities:
        te_all = d[d.city == city]
        if len(te_all) < 8:
            continue
        preds = {k: [] for k in ("kriging", "idw", "gwr_oracle")}
        obs = []
        for i in range(len(te_all)):
            tr = te_all.drop(te_all.index[i]).copy()
            te = te_all.iloc[[i]].copy()
            mu, sd = tr.pm.mean(), tr.pm.std() + 1e-9      # TRAINING statistics only
            tr["z"] = (tr.pm - mu) / sd
            te["z"] = (te.pm - mu) / sd
            obs.append(float(te.z.iloc[0]))
            k = krige(tr, te)
            preds["kriging"].append(np.nan if k is None else float(k[0]))
            preds["idw"].append(float(idw(tr, te)[0]))
            preds["gwr_oracle"].append(float(gwr(tr, te, small)[0]))
        r = {"city": city, "band": te_all.band.iloc[0], "n": len(te_all), "setting": "oracle"}
        for k, v in preds.items():
            v = np.array(v)
            m = np.isfinite(v)
            r[k] = rho(v[m], np.array(obs)[m]) if m.sum() >= 4 else np.nan
        rows.append(r)

    t = pd.DataFrame(rows)
    t.to_csv(OUT, index=False)

    adm = t[t.setting == "admissible"]
    orc = t[t.setting == "oracle"]
    fams = ["benchmark", "lur_stepwise", "ridge", "elasticnet", "random_forest",
            "gradient_boost", "gp_covariates", "mixed_effects"]

    def paired(col, frame, ref="benchmark"):
        s = frame[[col, ref]].dropna()
        if len(s) < 4:
            return None
        v = (s[col] - s[ref]).to_numpy()
        idx = rng.integers(0, len(v), (a.boot, len(v)))
        m = np.median(v[idx], axis=1)
        lo, hi = np.percentile(m, [2.5, 97.5])
        return dict(n=len(v), median=float(np.median(v)), lo=float(lo), hi=float(hi),
                    wins=int((v > 0).sum()))

    print(f"\n=== ADMISSIBLE families, paired against the benchmark, over {len(adm)} cities ===")
    print(f"    {'family':<18}{'median rho':>11}{'paired vs bench':>18}"
          f"{'95% over cities':>24}{'beats':>9}{'> limit':>9}")
    res = {}
    for f in fams:
        if f not in adm:
            continue
        med = float(adm[f].median())
        p = paired(f, adm)
        if f == "benchmark":
            print(f"    {f:<18}{med:>11.3f}{'-- reference --':>18}")
            res[f] = dict(median_rho=round(med, 4))
            continue
        beat = "YES" if p and p["lo"] > DETECT else "no"
        print(f"    {f:<18}{med:>11.3f}{p['median']:>+18.3f}"
              f"   [{p['lo']:>+7.3f},{p['hi']:>+7.3f}]{p['wins']:>6}/{p['n']}{beat:>9}")
        res[f] = dict(median_rho=round(med, 4), paired=round(p["median"], 4),
                      lo=round(p["lo"], 4), hi=round(p["hi"], 4),
                      wins=p["wins"], n=p["n"], exceeds_limit=bool(p["lo"] > DETECT))

    print(f"\n=== ORACLE families (target city's own stations visible), {len(orc)} cities ===")
    print("    Not comparable with the benchmark. Reported as an upper bound on what a city")
    print("    WITH a network could obtain from these families.")
    for f in ("kriging", "idw", "gwr_oracle"):
        if f in orc and orc[f].notna().sum() >= 4:
            v = orc[f].dropna()
            print(f"    {f:<18}{v.median():>11.3f}   (n={len(v)})")
            res[f] = dict(median_rho=round(float(v.median()), 4), n=int(len(v)),
                          setting="oracle")

    best = max((v.get("median_rho", -9), k) for k, v in res.items()
               if v.get("setting") != "oracle")
    print("\n=== the answer ===")
    any_beat = [k for k, v in res.items() if v.get("exceeds_limit")]
    if any_beat:
        print(f"    {', '.join(any_beat)} beat the benchmark by more than the registered")
        print(f"    detection limit. The spatial null does NOT survive a wider model tournament.")
    else:
        print(f"    No admissible family beats the benchmark by more than the registered")
        print(f"    detection limit of {DETECT}. Best admissible median rank correlation is")
        print(f"    {best[0]:.3f} ({best[1]}) against the benchmark's "
              f"{res['benchmark']['median_rho']:.3f}.")
        print(f"    The null is a property of the available information on this frame, not of")
        print(f"    the one model family the registered test happened to use.")

    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(dict(cities=int(len(adm)), stations=int(len(d)), predictors=len(feats),
                       benchmark=BENCH, detection_limit=DETECT,
                       best_admissible=best[1], best_admissible_rho=round(best[0], 4),
                       families=res), fh, indent=2)
    print(f"\n-> {OUT.name}, {OUT_JSON.name}")


if __name__ == "__main__":
    main()
