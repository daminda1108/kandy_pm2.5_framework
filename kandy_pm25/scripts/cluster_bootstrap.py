"""cluster_bootstrap.py -- are the panel's cities independent units? Almost certainly not.

THE OBJECTION, raised by an external reviewer and correct. The ladder's intervals are bootstrapped
over CITIES, which already fixed the worse error of treating 28,930 city-days as 28,930
observations. But cities are not independent of one another either. They share national monitoring
programmes, instrument procurement, siting conventions, calibration practice, operators and
processing chains. Eleven of the forty-eight belong to a single national network. Resampling
cities independently therefore understates the uncertainty, because a draw that happens to include
many cities from one network is not really the diverse sample its size suggests.

WHAT THIS DOES. A two-level (hierarchical) cluster bootstrap. Clusters are resampled with
replacement first, then cities are resampled with replacement inside each drawn cluster. That is
the standard construction when the sampling unit is a group rather than an individual, and it
propagates both sources of variation instead of only the second.

The cluster is defined as (network, country). CNEMC is one cluster covering eleven cities, because
those cities share an instrument fleet, an operator and a processing pipeline. OpenAQ cities are
clustered by country, which is the coarsest grouping the metadata supports and the one most likely
to carry shared calibration practice.

WHAT WOULD FALSIFY WHAT. Stated before running, because the point of the exercise is to find out
whether a headline survives, not to decorate it:

  * If the background rung's interval still excludes small values, the largest measured gain in
    the project survives the objection.
  * If `Bud1 -> Bud2` still sits against a tight upper bound, the redundancy null survives, and a
    null that survives a WIDER interval is strictly stronger than one that does not.
  * If the deep-tropical inversion's paired interval crosses zero under clustering, then the
    procurement recommendation for Kandy's own band rests on the assumption of city independence,
    and the thesis has to say so.

A DESIGN EFFECT is reported alongside, as the ratio of the cluster-bootstrap interval width to the
city-bootstrap width. A ratio near one means clustering costs nothing and the cities are behaving
independently for that quantity. A ratio well above one means the effective sample size is smaller
than the city count, and the city count should not be quoted as though it were the sample size.

Usage: python scripts/cluster_bootstrap.py [--boot 4000]
Out:   data/processed/modular/cluster_bootstrap.csv
       data/processed/modular/cluster_bootstrap.json
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
warnings.filterwarnings("ignore")

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "cluster_bootstrap.csv"
OUT_JSON = MOD / "cluster_bootstrap.json"
SEED = 20260906


def gain(a: pd.Series, b: pd.Series) -> pd.Series:
    return 100.0 * (a - b) / a


def attach_clusters(L: pd.DataFrame) -> pd.DataFrame:
    """Give every ladder city its network and country.

    [!] The join key is `slug`, not `cluster`. `cluster` is stored as a float in
    validation_sample.csv and as a string in the ladder outputs, so a naive merge on it matches
    NOTHING and returns a frame of NaN countries rather than an error. That silent-empty-merge
    failure is the same family as gotcha #85, and it is why the match count is asserted below.
    """
    s = pd.read_csv(MOD / "validation_sample.csv")
    s["slug"] = s.slug.astype(str)
    L = L.copy()
    L["city"] = L.city.astype(str)
    j = L.merge(s[["slug", "country", "src"]].drop_duplicates("slug"),
                left_on="city", right_on="slug", how="left")
    miss = int(j.country.isna().sum())
    assert miss == 0, f"{miss} of {len(j)} cities carry no country; the merge key is wrong"
    # CNEMC is ONE cluster regardless of the country column: one operator, one fleet, one
    # pipeline. OpenAQ cities cluster by country, the coarsest grouping the metadata supports.
    j["cluster_id"] = np.where(j.src.eq("CNEMC"), "CNEMC", j.src + "/" + j.country)
    return j


def boot_city(v: np.ndarray, rng, n: int):
    idx = rng.integers(0, len(v), size=(n, len(v)))
    return np.median(v[idx], axis=1)


def boot_cluster(v: np.ndarray, g: np.ndarray, rng, n: int):
    """Two-level bootstrap: draw clusters with replacement, then cities within each drawn cluster.

    The resample is NOT forced to the original length. A draw of large clusters legitimately
    yields more cities than a draw of small ones, and pinning the size back would suppress exactly
    the variation the cluster structure introduces.
    """
    keys = np.unique(g)
    members = {k: v[g == k] for k in keys}
    out = np.empty(n)
    for i in range(n):
        drawn = keys[rng.integers(0, len(keys), len(keys))]
        parts = []
        for k in drawn:
            m = members[k]
            parts.append(m[rng.integers(0, len(m), len(m))])
        out[i] = np.median(np.concatenate(parts))
    return out


def icc(v: np.ndarray, g: np.ndarray, multi_only: bool = False) -> float:
    """Fraction of variance lying BETWEEN clusters.

    [!] THIS STATISTIC IS MECHANICALLY INFLATED ON THIS PANEL AND MUST NOT BE QUOTED RAW.
    Twenty-three of the twenty-nine clusters contain a single city. A singleton cluster has zero
    within-cluster variance by construction, so its entire deviation from the grand mean is booked
    as BETWEEN-cluster variance. Running it over all cities therefore returns something close to
    one no matter how weak the real network dependence is, which is a property of the grouping and
    not a finding about the panel. `multi_only=True` restricts the calculation to cities that sit
    in a cluster with at least one sibling, which is the only version that carries information.
    The honest headline diagnostic is the interval WIDTH RATIO, which is computed from resampling
    and has no such artefact.
    """
    if multi_only:
        keys, counts = np.unique(g, return_counts=True)
        keep = np.isin(g, keys[counts >= 2])
        if keep.sum() < 4 or len(np.unique(g[keep])) < 2:
            return float("nan")
        v, g = v[keep], g[keep]
    keys = np.unique(g)
    if len(keys) < 2:
        return float("nan")
    grand = v.mean()
    between = sum((v[g == k].mean() - grand) ** 2 * (g == k).sum() for k in keys)
    total = ((v - grand) ** 2).sum()
    return float(between / total) if total > 0 else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=4000)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)

    print("=== hierarchical cluster bootstrap: are cities independent units? ===\n")

    frames = {}
    for name, f in (("ghap", "ladder_revalidated.csv"), ("maiac", "ladder_maiac.csv")):
        L = pd.read_csv(MOD / f)
        L = L[L.bottom == "Bud0c"].copy()
        L = attach_clusters(L)
        L["g_first2"] = gain(L.rmse_Bud0, L.rmse_Bud1)
        L["g_stn3to6"] = gain(L.rmse_Bud1, L.rmse_Bud2)
        L["g_bg"] = gain(L.rmse_Bud2, L.rmse_Bud3)
        frames[name] = L

    L = frames["ghap"]
    cl = L.groupby("cluster_id").size().sort_values(ascending=False)
    print(f"    {len(L)} cities fall into {len(cl)} clusters (network x country)")
    print(f"    largest: " + ", ".join(f"{k} n={v}" for k, v in cl.head(5).items()))
    print(f"    {(cl == 1).sum()} clusters contain a single city\n")

    rows = []
    for ladder, F in frames.items():
        for label, col in (("first two sensors", "g_first2"),
                           ("sensors three to six", "g_stn3to6"),
                           ("a background series", "g_bg")):
            for stratum, sub in [("pooled", F)] + list(F.groupby("band")):
                d = sub[[col, "cluster_id"]].dropna()
                if len(d) < 3:
                    continue
                v = d[col].to_numpy()
                g = d.cluster_id.to_numpy()
                mc = boot_city(v, rng, a.boot)
                mk = boot_cluster(v, g, rng, a.boot)
                clo, chi = np.percentile(mc, [2.5, 97.5])
                klo, khi = np.percentile(mk, [2.5, 97.5])
                deff = (khi - klo) / (chi - clo) if chi > clo else np.nan
                rows.append(dict(
                    ladder=ladder, stratum=stratum, step=label,
                    n_cities=len(v), n_clusters=int(len(np.unique(g))),
                    median=round(float(np.median(v)), 3),
                    city_lo=round(float(clo), 3), city_hi=round(float(chi), 3),
                    clust_lo=round(float(klo), 3), clust_hi=round(float(khi), 3),
                    width_ratio=round(float(deff), 2),
                    icc_naive=round(icc(v, g), 3),
                    icc_multi=round(icc(v, g, multi_only=True), 3)))
    r = pd.DataFrame(rows)
    r.to_csv(OUT, index=False)

    print("=== pooled, both satellite streams: city interval vs cluster interval ===")
    print(f"    {'ladder':<7}{'step':<24}{'median':>8}{'city 95%':>20}{'cluster 95%':>22}"
          f"{'x wider':>9}{'ICC*':>7}")
    for _, x in r[r.stratum == "pooled"].iterrows():
        print(f"    {x.ladder:<7}{x.step:<24}{x['median']:>8.2f}"
              f"   [{x.city_lo:>6.2f},{x.city_hi:>6.2f}]"
              f"   [{x.clust_lo:>6.2f},{x.clust_hi:>6.2f}]"
              f"{x.width_ratio:>9.2f}{x.icc_multi:>7.2f}")

    # ── the headline: the deep-tropical inversion, PAIRED within city, under clustering ──
    # Paired because both gains are measured on the same city, and a difference of medians would
    # discard the pairing (gotcha #91, which went the wrong way twice in one session).
    print("\n=== the deep-tropical inversion, paired within city, under clustering ===")
    inv = {}
    for ladder, F in frames.items():
        dt = F[F.band == "deep_tropical"][["g_first2", "g_bg", "cluster_id"]].dropna()
        if len(dt) < 3:
            continue
        v = (dt.g_first2 - dt.g_bg).to_numpy()
        g = dt.cluster_id.to_numpy()
        mc = boot_city(v, rng, a.boot)
        mk = boot_cluster(v, g, rng, a.boot)
        clo, chi = np.percentile(mc, [2.5, 97.5])
        klo, khi = np.percentile(mk, [2.5, 97.5])
        verdict = "EXCLUDES 0" if klo > 0 else ("excludes 0 by cities only" if clo > 0 else "no")
        inv[ladder] = dict(n_cities=int(len(v)), n_clusters=int(len(np.unique(g))),
                           median=round(float(np.median(v)), 2),
                           city_lo=round(float(clo), 2), city_hi=round(float(chi), 2),
                           clust_lo=round(float(klo), 2), clust_hi=round(float(khi), 2),
                           width_ratio=round(float((khi - klo) / (chi - clo)), 2),
                           favours_sensors_pct=round(100.0 * float((v > 0).mean()), 1),
                           survives_clustering=bool(klo > 0))
        print(f"    {ladder:<7} n={len(v):>2} in {len(np.unique(g)):>2} clusters   "
              f"paired {np.median(v):>+7.2f} pp   city [{clo:>+7.2f},{chi:>+7.2f}]   "
              f"cluster [{klo:>+7.2f},{khi:>+7.2f}]   {verdict}")

    summary = dict(boot=a.boot, seed=SEED,
                   n_cities=int(len(L)), n_clusters=int(len(cl)),
                   largest_cluster=str(cl.index[0]), largest_cluster_n=int(cl.iloc[0]),
                   singleton_clusters=int((cl == 1).sum()),
                   inversion=inv,
                   pooled={f"{x.ladder}.{x.step}": dict(
                       median=x["median"], city=[x.city_lo, x.city_hi],
                       cluster=[x.clust_lo, x.clust_hi], width_ratio=x.width_ratio,
                       icc_multi=x.icc_multi)
                       for _, x in r[r.stratum == "pooled"].iterrows()})
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\n-> {OUT.name}, {OUT_JSON.name}")


if __name__ == "__main__":
    main()
