"""spatial_curve_reanalysis.py -- review steps S-b and S-c (docs/review_remediation_plan_2026-10-06.md).
EXPLORATORY; reads the stored registered outputs only.

S3  Is the between-city spread of (E3 - E1), kriging minus the built-up raster, larger than the sampling
    noise of a Spearman correlation on a city's sites? Random-effects meta-analysis on the Fisher-z scale.
    Sampling variance per city: Var(z_E3 - z_E1) = 2 * 1.06/(n - 3) * (1 - r12), with n = the city's sites
    (OPTIMISTIC: every site is held out in some replicate, so n is an upper bound on the effective sample)
    and r12 = the across-replicate correlation of the two estimators' rho within the city. Cochran Q, I^2,
    tau, and the share of cities whose own 95 % interval excludes 0 under that variance.
S6  Tropical minus temperate: difference in mean Fisher-z E3 and in E3 - E1 at each k, with a two-level
    country bootstrap interval, replacing the min-max envelope rule.
S7  The empirical SD of per-city paired differences, and the detection limit recomputed with it.
S4  Crossover with a Holm correction over the k grid, per city, using the meta-analytic variance.

Output: data/processed/modular/{frame}/analysis/reanalysis.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import spatial_curve_analysis as sca   # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
TROP = {"tropical", "deep_tropical"}
Z = lambda r: np.arctanh(np.clip(r, -0.999, 0.999))


def boot_diff(a: pd.Series, b: pd.Series, ca: pd.Series, cb: pd.Series, n=4000, seed=20260927):
    """Mean(a) - mean(b), two-level bootstrap: countries then cities, within each group."""
    rng = np.random.default_rng(seed)
    def draw(v, c):
        groups = [v[c == g].to_numpy() for g in c.unique()]
        pick = rng.integers(len(groups), size=len(groups))
        return np.concatenate([rng.choice(groups[j], len(groups[j])) for j in pick]).mean()
    d = np.array([draw(a, ca) - draw(b, cb) for _ in range(n)])
    return float(a.mean() - b.mean()), float(np.quantile(d, .025)), float(np.quantile(d, .975))


def run(frame: str) -> dict:
    d = MOD / frame
    C = pd.read_csv(d / "frame_cities.csv").set_index("cluster")
    q = pd.read_parquet(d / "analysis" / "q1.parquet")
    q = q[(q.holdout == "random") & (q.ordering == "random") & q.est.isin(["E1", "E3"])]
    w = q.pivot_table(index=["cluster", "rep", "k"], columns="est", values="rho").dropna().reset_index()
    w["d"] = Z(w.E3) - Z(w.E1)
    out = {"frame": frame}
    prim = set(C.index[C.primary.astype(bool)])
    rows = []
    for (cl, k), g in w.groupby(["cluster", "k"]):
        n = int(C.loc[cl, "sites"])
        r12 = float(np.corrcoef(g.E3, g.E1)[0, 1]) if g.E3.std() > 0 and g.E1.std() > 0 else 0.0
        var = 2 * 1.06 / max(n - 3, 1) * max(1 - r12, 0.05)
        rows.append(dict(cluster=cl, k=int(k), n=n, d=float(np.median(g.d)), zE3=float(Z(g.E3.median())),
                         var=var, r12=r12, band=C.loc[cl, "band"], country=C.loc[cl, "country"],
                         primary=cl in prim))
    R = pd.DataFrame(rows)
    R.to_csv(d / "analysis" / "reanalysis_city.csv", index=False)

    # S3 heterogeneity and S4 Holm crossover (primary cities)
    het, cross = {}, {}
    P = R[R.primary]
    for k, g in P.groupby("k"):
        if len(g) < 4:
            continue
        wi = 1 / g["var"]
        mu = float((wi * g.d).sum() / wi.sum())
        Q = float((wi * (g.d - mu) ** 2).sum()); df = len(g) - 1
        tau2 = max(0.0, (Q - df) / (wi.sum() - (wi ** 2).sum() / wi.sum()))
        own_excl = ((g.d - 1.96 * np.sqrt(g["var"])) > 0) | ((g.d + 1.96 * np.sqrt(g["var"])) < 0)
        het[int(k)] = dict(cities=len(g), fixed_mean_dz=mu, Q=Q, df=df, p_Q=float(stats.chi2.sf(Q, df)),
                           I2=float(max(0.0, (Q - df) / Q)) if Q > 0 else 0.0, tau_z=float(np.sqrt(tau2)),
                           median_sampling_sd_z=float(np.sqrt(g["var"]).median()),
                           cities_own_interval_excludes_0=int(own_excl.sum()),
                           cities_positive_excluding_0=int(((g.d - 1.96 * np.sqrt(g["var"])) > 0).sum()))
    for cl, g in P.groupby("cluster"):
        g = g.sort_values("k")
        p = pd.Series(stats.norm.sf(g.d / np.sqrt(g["var"])))  # one-sided: kriging > raster
        order = np.argsort(p.to_numpy()); m = len(p); passed = []
        for i, j in enumerate(order):                        # Holm step-down
            if p.to_numpy()[j] <= 0.05 / (m - i):
                passed.append(int(g.k.to_numpy()[j]))
            else:
                break
        cross[int(cl)] = min(passed) if passed else None
    out["S3_heterogeneity_by_k"] = het
    out["S4_holm_crossover"] = dict(cities=len(cross), crossing=sum(v is not None for v in cross.values()),
                                    at_k3=sum(v == 3 for v in cross.values()), per_city=cross)

    # S6 tropical vs non-tropical (all scored cities with a band; tropical arm included)
    trop = {}
    for k, g in R.groupby("k"):
        a, b = g[g.band.isin(TROP)], g[~g.band.isin(TROP) & g.primary]
        if len(a) < 3 or len(b) < 3:
            continue
        e = boot_diff(a.zE3, b.zE3, a.country, b.country)
        e2 = boot_diff(a.d, b.d, a.country, b.country)
        trop[int(k)] = dict(n_trop=len(a), n_other=len(b),
                            zE3_diff=dict(est=e[0], lo=e[1], hi=e[2]),
                            dz_kriging_minus_raster_diff=dict(est=e2[0], lo=e2[1], hi=e2[2]))
    out["S6_tropical_minus_other"] = trop

    # S7 empirical SD of per-city paired differences (rho scale, as the registered limit), k=3
    cq = pd.read_csv(d / "analysis" / "curve_q1_city.csv")
    piv = cq[cq.k == 3].pivot(index="cluster", columns="est", values="rho")
    dd = (piv["E3"] - piv["E1"]).dropna()
    dd = dd[dd.index.isin(prim)]
    sd = float(dd.std())
    n_ctry = int(C.loc[list(prim), "country"].nunique())
    sca.MDE_SD = sd
    out["S7"] = dict(registered_sd=0.20, empirical_sd_k3=sd, countries=n_ctry,
                     registered_limit=json.load(open(d / "analysis" / "summary.json"))["detection_limit_at_countries"],
                     limit_with_empirical_sd=sca.mde_for(n_ctry))
    return out


def main():
    for frame in ("spatial_curve", "spatial_curve_full"):
        r = run(frame)
        p = MOD / frame / "analysis" / "reanalysis.json"
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(r, indent=2, default=float), encoding="utf-8"); os.replace(tmp, p)
        print(f"== {frame}")
        for k, v in r["S3_heterogeneity_by_k"].items():
            print(f"  S3 k={k:>2} n={v['cities']:>2} Q={v['Q']:.1f}/{v['df']} p={v['p_Q']:.3f} I2={v['I2']:.2f} "
                  f"tau={v['tau_z']:.3f} samp_sd={v['median_sampling_sd_z']:.3f} own-excl={v['cities_own_interval_excludes_0']} "
                  f"pos={v['cities_positive_excluding_0']}")
        h = r["S4_holm_crossover"]
        print(f"  S4 Holm crossover: {h['crossing']}/{h['cities']} cities, {h['at_k3']} at k=3")
        for k, v in r["S6_tropical_minus_other"].items():
            a, b = v["zE3_diff"], v["dz_kriging_minus_raster_diff"]
            print(f"  S6 k={k:>2} trop {v['n_trop']} vs {v['n_other']}: zE3 {a['est']:+.3f} [{a['lo']:+.3f}, {a['hi']:+.3f}]"
                  f"  dz {b['est']:+.3f} [{b['lo']:+.3f}, {b['hi']:+.3f}]")
        print(f"  S7 {r['S7']}")
        print(f"-> {p}")


if __name__ == "__main__":
    main()
