"""design_comparison.py -- is the proposed network actually better than the obvious alternatives?

WHY THIS EXISTS. Proposing a sensor design and asserting it is good is not an argument. Five
designs are compared on the same candidate grid, with the same covariates and the same metrics,
including the two designs a programme would most plausibly choose instead. If the proposed design
does not win, this script says so and the plan changes.

THE DESIGNS

  existing        the two fixed records now inside the domain. The baseline to beat.
  road_proximity  sites nearest the major road network. What an air quality network is
                  conventionally sited for, and what produces the convenience sample this
                  project has measured six nulls against.
  population      sites drawn proportional to population. What "serve the most people" gives,
                  and a genuinely reasonable objective.
  clhs            conditioned Latin hypercube: reproduce the covariate distribution.
  d_optimal       Fedorov exchange: maximise the determinant of the information matrix for a
                  land-use regression. Textbook optimal design.

THE METRICS, and each answers a different question

  D_eff       relative D-efficiency for a LUR-type model. "How precisely could this design
              estimate the coefficients of the model we would fit?" Higher is better.
  cover_pct   span of the emission percentile range actually sampled. "Does the network
              straddle the gradient at all?"
  ks_mean     mean Kolmogorov-Smirnov distance between the design's covariate distribution and
              the domain's, averaged over covariates. "Is the sample representative?" LOWER is
              better. This is what cLHS optimises and what D-optimal explicitly does not.
  min_sep_m   smallest distance between two sites. Guards against a design that looks
              informative on paper because it stacked sensors on one street corner.

⚠ D-efficiency is defined relative to a MODEL. It rewards a design for the model it assumes, and
this project's central finding is that the right spatial model is not known. That is the argument
for not selecting on D-efficiency alone, and it is why the recommendation is a hybrid rather than
the winner of one column.

Usage: python scripts/design_comparison.py [--n 12] [--boot 200]
Out:   data/processed/decomp/design_comparison.csv
       data/processed/decomp/design_saturation.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
DEC = REPO / "data" / "processed" / "decomp"
OUT = DEC / "design_comparison.csv"
OUT_SAT = DEC / "design_saturation.csv"
SEED = 20260905
N_CAND = 4000        # candidate subsample for the exchange algorithm; 25,600 is needless


def build_frame():
    from design_sensor_network import load_layers, m_per_deg
    L = load_layers()
    lat, lon = L["lat"], L["lon"]
    LON, LAT = np.meshgrid(lon, lat)
    from design_sensor_network import DESIGN_COVARS
    ok = np.isfinite(L["E"]) & np.isfinite(L["Z"])
    for k in DESIGN_COVARS:
        ok &= np.isfinite(L[k])
    df = pd.DataFrame({k: L[k][ok] for k in DESIGN_COVARS})
    df["lat"], df["lon"], df["Z"] = LAT[ok], LON[ok], L["Z"][ok]
    df["E_pct"] = 100 * df.E.rank(pct=True)
    # distance to the emission spine: a cheap, honest stand-in for distance-to-major-road,
    # since the emission proxy IS road-network centrality
    df["road_rank"] = df.E.rank(pct=True)
    mlat, mlon = m_per_deg(float(lat.mean()))
    return df.reset_index(drop=True), mlat, mlon


def design_matrix(sub: pd.DataFrame, cols) -> np.ndarray:
    X = sub[cols].to_numpy(float)
    X = (X - X.mean(0)) / (X.std(0) + 1e-12)
    return np.column_stack([np.ones(len(X)), X])


def d_eff(sub, cols, ref_logdet=None):
    """Relative D-efficiency: (det X'X)^(1/p) / n, reported against the best design found."""
    X = design_matrix(sub, cols)
    p = X.shape[1]
    s = np.linalg.svd(X, compute_uv=False)
    if s.min() <= 1e-9:
        return 0.0, -np.inf
    logdet = 2.0 * np.log(s).sum()
    val = np.exp(logdet / p) / len(X)
    return val, logdet


def ks_mean(sub, pool, cols):
    from scipy.stats import ks_2samp
    return float(np.mean([ks_2samp(sub[c], pool[c]).statistic for c in cols]))


def min_sep(sub, mlat, mlon):
    la, lo = sub.lat.to_numpy(), sub.lon.to_numpy()
    if len(la) < 2:
        return np.nan
    d = np.hypot((la[:, None] - la[None, :]) * mlat, (lo[:, None] - lo[None, :]) * mlon)
    np.fill_diagonal(d, np.inf)
    return float(d.min())


def fedorov(pool: pd.DataFrame, n: int, cols, seed: int, n_iter: int = 400):
    """D-optimal design by Fedorov exchange on a candidate subsample."""
    rng = np.random.default_rng(seed)
    cand = pool.sample(min(N_CAND, len(pool)), random_state=seed).reset_index(drop=True)
    idx = list(rng.choice(len(cand), n, replace=False))
    _, best = d_eff(cand.iloc[idx], cols)
    for _ in range(n_iter):
        improved = False
        for i in range(n):
            trial = rng.choice(len(cand), 40, replace=False)
            for t in trial:
                if t in idx:
                    continue
                alt = idx.copy()
                alt[i] = int(t)
                _, ld = d_eff(cand.iloc[alt], cols)
                if ld > best + 1e-9:
                    idx, best, improved = alt, ld, True
        if not improved:
            break
    return cand.iloc[idx].copy()


def make_designs(pool, n, cols, mlat, mlon, seed):
    from design_sensor_network import clhs
    rng = np.random.default_rng(seed)
    out = {}

    # existing: the two in-domain fixed records, snapped to the nearest candidate cell
    ex = []
    for la, lo in [(7.265, 80.625), (7.2731, 80.6117)]:
        j = int(np.argmin(np.hypot((pool.lat - la) * mlat, (pool.lon - lo) * mlon)))
        ex.append(j)
    out["existing"] = pool.iloc[ex].copy()

    # road_proximity: the n highest road-centrality cells, thinned so they are not one street
    r = pool.sort_values("road_rank", ascending=False)
    keep = []
    for i in r.index:
        if len(keep) >= n:
            break
        if all(np.hypot((r.loc[i].lat - pool.loc[k].lat) * mlat,
                        (r.loc[i].lon - pool.loc[k].lon) * mlon) > 400 for k in keep):
            keep.append(i)
    out["road_proximity"] = pool.loc[keep].copy()

    # population-weighted draw
    w = np.clip(pool.POP.to_numpy(float), 0, None)
    w = w / w.sum() if w.sum() > 0 else None
    out["population"] = pool.iloc[rng.choice(len(pool), n, replace=False, p=w)].copy()

    # cLHS: the proposed design
    X = pool[cols].to_numpy(float)
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-12)
    out["clhs"] = pool.iloc[clhs(Xs, n, seed)].copy()

    # D-optimal
    out["d_optimal"] = fedorov(pool, n, cols, seed)

    # HYBRID: half the sites D-optimally, half by cLHS on what remains.
    # The two criteria disagree, and the disagreement is the reason to split rather than to
    # pick. D-optimality pins the coefficients of a model we have assumed; cLHS samples the
    # distribution so the data can show that the assumed model is wrong. This project's six
    # spatial nulls are precisely a record of assumed models being wrong, so buying only
    # coefficient precision would be buying the wrong thing.
    nd = n // 2
    dopt = fedorov(pool, nd, cols, seed)
    rest = pool.drop(index=dopt.index, errors="ignore")
    Xr = rest[cols].to_numpy(float)
    Xrs = (Xr - Xr.mean(0)) / (Xr.std(0) + 1e-12)
    from design_sensor_network import clhs as _clhs
    hyb = pd.concat([dopt, rest.iloc[_clhs(Xrs, n - nd, seed + 1)]])
    out["hybrid"] = hyb
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--boot", type=int, default=200)
    a = ap.parse_args()

    pool, mlat, mlon = build_frame()
    from design_sensor_network import DESIGN_COVARS
    cols = list(DESIGN_COVARS)
    print("=== design comparison ===")
    print(f"    {len(pool):,} candidate cells, {len(cols)} covariates, n = {a.n} sites\n")

    designs = make_designs(pool, a.n, cols, mlat, mlon, SEED)

    # random designs give the null distribution any proposal must beat
    rng = np.random.default_rng(SEED)
    rnd = [pool.iloc[rng.choice(len(pool), a.n, replace=False)] for _ in range(a.boot)]
    rnd_d = np.array([d_eff(s, cols)[0] for s in rnd])
    rnd_k = np.array([ks_mean(s, pool, cols) for s in rnd])

    rows = []
    for name, sub in designs.items():
        dv, _ = d_eff(sub, cols)
        rows.append(dict(design=name, n=len(sub), D_eff=dv,
                         cover_pct=float(sub.E_pct.max() - sub.E_pct.min()),
                         pct_lo=float(sub.E_pct.min()), pct_hi=float(sub.E_pct.max()),
                         ks_mean=ks_mean(sub, pool, cols),
                         min_sep_m=min_sep(sub, mlat, mlon)))
    rows.append(dict(design="random_mean", n=a.n, D_eff=float(rnd_d.mean()),
                     cover_pct=np.nan, pct_lo=np.nan, pct_hi=np.nan,
                     ks_mean=float(rnd_k.mean()), min_sep_m=np.nan))
    d = pd.DataFrame(rows)
    d["D_eff_rel"] = d.D_eff / d.D_eff.max()
    d = d.sort_values("D_eff_rel", ascending=False)
    d.to_csv(OUT, index=False)

    print(f"    {'design':<16}{'D_eff':>8}{'rel':>7}{'cover':>8}{'ks':>8}{'min_sep_m':>11}")
    for r in d.itertuples():
        cov = f"{r.cover_pct:.0f}" if np.isfinite(r.cover_pct) else "  -"
        sep = f"{r.min_sep_m:.0f}" if np.isfinite(r.min_sep_m) else "  -"
        print(f"    {r.design:<16}{r.D_eff:8.3f}{r.D_eff_rel:7.2f}{cov:>8}"
              f"{r.ks_mean:8.3f}{sep:>11}")
    print(f"\n    random baseline over {a.boot} draws: D_eff {rnd_d.mean():.3f} "
          f"[{np.percentile(rnd_d,2.5):.3f}, {np.percentile(rnd_d,97.5):.3f}], "
          f"ks {rnd_k.mean():.3f}")

    # ── how many sites are enough? ────────────────────────────────────────────────────────
    print("\n=== saturation: how much does the n+1-th site add? ===")
    from design_sensor_network import clhs
    # Averaged over seeds. cLHS is a stochastic optimiser, so a single-seed curve is noisy
    # enough to invent a knee that is not there -- the first version of this table showed
    # D_eff going 0.46, 0.34, 0.68, 0.78, 0.65 with n, which is sampling noise, not structure.
    X = pool[cols].to_numpy(float)
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-12)
    sat = []
    for n in [4, 6, 8, 10, 12, 16, 20, 24, 30]:
        dvs, kss, cvs = [], [], []
        for sd_i in range(5):
            s = pool.iloc[clhs(Xs, n, SEED + 97 * sd_i)]
            dvs.append(d_eff(s, cols)[0])
            kss.append(ks_mean(s, pool, cols))
            cvs.append(float(s.E_pct.max() - s.E_pct.min()))
        sat.append(dict(n=n, D_eff=float(np.mean(dvs)), ks_mean=float(np.mean(kss)),
                        ks_sd=float(np.std(kss)), cover_pct=float(np.mean(cvs))))
    sd = pd.DataFrame(sat)
    sd["ks_gain"] = -sd.ks_mean.diff()
    sd.to_csv(OUT_SAT, index=False)
    print(f"    {'n':>4}{'D_eff':>9}{'ks_mean':>10}{'cover':>8}{'ks gain vs prev':>18}")
    for r in sd.itertuples():
        g = f"{r.ks_gain:+.4f}" if np.isfinite(r.ks_gain) else "-"
        print(f"    {r.n:>4}{r.D_eff:9.3f}{r.ks_mean:10.3f}{r.cover_pct:8.0f}{g:>18}")

    knee = sd[sd.ks_gain.notna()]
    if len(knee):
        k = knee.loc[knee.ks_gain.idxmax()]
        print(f"\n    largest single improvement in representativeness arrives at n = "
              f"{int(k.n)}")
        small = knee[knee.ks_gain < 0.01]
        if len(small):
            print(f"    improvement falls below 0.01 from n = {int(small.n.iloc[0])} onward")
    print(f"\n-> {OUT.name}, {OUT_SAT.name}")


if __name__ == "__main__":
    main()
