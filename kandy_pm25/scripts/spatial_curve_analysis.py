"""spatial_curve_analysis.py -- scoring for the spatial learning curve (OSF rqn4y, 2026-09-10).

Implements Sections 4 and 5 of docs/prereg_spatial_learning_curve_2026-09-11.md on the frame that
spatial_curve_freeze.py froze, with the predictors spatial_curve_predictors.py attached.

QUESTIONS
  Q1  static:          held-out Spearman of window-mean site values, against fitting-set size k
  Q2  spatiotemporal:  per-day held-out Spearman, median across days, against k
  Q3  reach:           held-out standardised error against distance to the nearest fitting site
  Q4  design:          cLHS and convenience ordering against random, matched k, same held-out set
  Q5  band:            band-arm curves against the envelope of primary-frame curves

ESTIMATORS
  E0 uniform city (floor)      E1 benchmark lc_built_2400      E2 ridge on 7 covariates
  E3 ordinary kriging (PyKrige)   E4 inverse-distance weighting   E5 regression kriging
  E6 GWR (mgwr), k >= 25       E7 grey-box pattern, where supplied

DEVIATIONS FROM THE REGISTRATION, declared in this file before any real result was seen
  D-1  cLHS ordering is NOT nested. The registration defines every fitting set as a prefix of an
       ordering, but a conditioned Latin hypercube is an optimal SUBSET for a given size and has
       no nested form. It is therefore drawn independently at each k. Q4 compares orderings at
       matched k on the same held-out set, which does not require nesting. Random and convenience
       orderings remain nested exactly as registered.
  D-2  Q2 runs at a reduced budget. At full scale it is about 32 million kriging fits. It runs
       Q2_REPS replicates, a fixed random sample of Q2_DAYS eligible days per replicate shared by
       every estimator and every k (so comparisons stay paired), random ordering and random
       held-out only, and without E6, whose bandwidth search per day is prohibitive.
  D-3  E6 (GWR) and the blocked held-out variant run on random ordering only, for compute. Both
       were registered as secondary to the random-ordering, random-held-out primary analysis.
  D-4  Which estimator defines Q3's reach is not stated in the registration. E3 is primary, as
       the density family the reach is about; E4 is reported beside it.

TWO SAFEGUARDS NOT REQUIRED BY THE REGISTRATION
  * --synthetic: a positive control. A simulated city carrying a known smooth field is scored
    first. If kriging cannot recover it, the machinery is wrong and no real result is trusted.
  * Composition. Large k exists only in large cities, so a pooled median curve changes which
    cities it averages as k grows. Every increment is paired WITHIN city and is unaffected; every
    pooled level is reported with its city count, and is never read as a within-city trend.

Usage:
  .venv/Scripts/python.exe scripts/spatial_curve_analysis.py --synthetic
  .venv/Scripts/python.exe scripts/spatial_curve_analysis.py --leakage-test
  .venv/Scripts/python.exe scripts/spatial_curve_analysis.py [--workers 8] [--cities N]
Out: data/processed/modular/spatial_curve/analysis/*.parquet, *.csv, summary.json
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon
from sklearn.linear_model import RidgeCV

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
SC = REPO / "data" / "processed" / "modular" / "spatial_curve"
RAW = SC / "raw"
OUTD = SC / "analysis"

# ── registered constants ──────────────────────────────────────────────────────────────────────
SEED = 20260911
REPS = 100
KS = (3, 5, 8, 12, 18, 25, 35, 50, 70)
COVARS = ["lc_built_2400", "lc_built_300", "ntl_1000", "pop_1000", "ndvi_1000",
          "road_major_300", "dist_major_km"]
BENCH = "lc_built_2400"
GWR_MIN_K = 25
DIST_BINS = [0, 0.5, 1, 2, 3, 5, 8, 12, np.inf]
SAT_MEDIAN = 0.02
N_BOOT = 5000
MDE_SD = 0.20
MIN_HELD = 10
LEAK_THRESHOLD = 0.1
CROSS_K_MAX = 35
REACH_KM_MAX = 5.0
# ── declared deviations (see docstring) ───────────────────────────────────────────────────────
Q2_REPS = 20
Q2_DAYS = 60
Q2_TAB_REPS = 10                 # amendment 26hp8, Section 4: E8/E9 in Q2
Q2_TAB_DAYS = 20
E7_MIN_HELD = 8                  # D-5: minimum held-out sites inside the grey-box grid
DEVIATIONS = ["D-1 cLHS drawn independently per k (not nested)",
              f"D-2 Q2 at {Q2_REPS} replicates x {Q2_DAYS} shared days, random ordering, no E6",
              "D-3 E6 and blocked held-out on random ordering only",
              "D-4 Q3 reach defined on E3, with E4 reported beside it",
              "D-5 E7 scored on held-out sites inside the grey-box model grid only (Medellin: 14 of 16 sites), and every estimator re-scored on that same subset as est|e7sub, so E7 comparisons stay paired; nothing is extrapolated outside the grid",
              "D-6 OSM road covariates (road_major_300, dist_major_km) read from one set of Geofabrik extracts (downloaded 2026-09-11, MD5-verified) instead of live Overpass, which queued ~20 min per city. Same highway values, classes, midpoint rule and haversine; a segment enters a city by its midpoint tile rather than as a whole way, which leaves every road_* value unchanged by construction (tiles reach 4.2 km past every site, the widest buffer is 1 km). Every city is computed from the extracts; the two cities Overpass finished are kept as a cross-check",
              "D-7 Leakage self-test implementation corrected, criterion unchanged (E3 standardised error < 0.1 with the twin in the fitting set). The first implementation compared each member's mean over its OWN days and read raw hourly files without the freeze's QC; 23 of 47 merged pairs share fewer than 30 days (5 share none: replaced instruments, not twins), so it measured seasonal difference between records and failed at 2.03. Corrected: the freeze's qc_hourly on each member, and both members compared on the days both report (>= 30). Diagnosis before the fix: concurrent twins agree to 0.01 SD and E3 reproduces the twin to 0.011 SD (leakage_diagnosis.csv)",
              "S-1 DECLARED SENSITIVITY, 2026-09-11, before any real data were scored: the frame is also frozen at 70 per cent day coverage (tag s70) and scored identically. It is reported BESIDE the registered 75 per cent result and never instead of it. Reason: at 75 per cent Bangkok, the only dense deep-tropical network, misses the band arm by one site, and both German clusters have every station between 70 and 75 per cent.",
              "D-8 DECLARED 2026-09-15, before any E8/E9 verdict was computed: E8/E9 (TabPFN) are scored on CPU ONLY. The registration fixes TabPFN to its package defaults but not the device, and the default inference_precision='auto' enables mixed-precision autocast on CUDA while CPU runs float32 -- so the defaults are a different numerical estimator per device. Measured: 48 GPU-scored E8/E9 values re-scored on CPU (same tabpfn 8.5.0, same v3 default weights, same seed) matched 8/48 exactly, median |d rho| 0.073, max 0.376; CPU against itself was 48/48 bit-identical. CPU is chosen for determinism, reproducibility on any machine, and no quota. The 27 cities scored on GPU (19 registered, 8 S-1) are archived and NOT merged; every E8/E9 task is re-scored on CPU."]
FRAME_TAG = ""                   # "" is the registered frame; "s70" is sensitivity S-1

EST_ALL = ["E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10", "E11"]


# ── geometry ──────────────────────────────────────────────────────────────────────────────────
def to_km(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    lat0, lon0 = float(np.mean(lat)), float(np.mean(lon))
    return np.c_[111.32 * (lon - lon0) * np.cos(np.radians(lat0)), 110.57 * (lat - lat0)]


def nearest_km(cT: np.ndarray, cF: np.ndarray) -> np.ndarray:
    d = np.hypot(cT[:, None, 0] - cF[None, :, 0], cT[:, None, 1] - cF[None, :, 1])
    return d.min(1)


# ── estimators ────────────────────────────────────────────────────────────────────────────────
def _std(XF, XT):
    mu, sd = XF.mean(0), XF.std(0)
    sd = np.where(sd < 1e-12, 1.0, sd)
    return (XF - mu) / sd, (XT - mu) / sd


def ridge(XF, yF, XT):
    """E2. Standardisation fitted on the fitting sites only."""
    Xf, Xt = _std(XF, XT)
    m = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(Xf, yF)
    return m.predict(Xt), m.predict(Xf)


def krige(cF, zF, cT):
    """E3. Ordinary kriging, exponential variogram fitted on the fitting sites only."""
    if np.std(zF) < 1e-12:
        return np.full(len(cT), float(np.mean(zF)))
    from pykrige.ok import OrdinaryKriging
    ok = OrdinaryKriging(cF[:, 0], cF[:, 1], zF, variogram_model="exponential",
                         nlags=int(max(2, min(6, len(zF) - 1))),
                         enable_plotting=False, verbose=False)
    z, _ = ok.execute("points", cT[:, 0], cT[:, 1])
    return np.asarray(z, dtype=float)


def idw(cF, zF, cT, power=2.0):
    """E4. Inverse-distance weighting, power 2."""
    d = np.hypot(cT[:, None, 0] - cF[None, :, 0], cT[:, None, 1] - cF[None, :, 1])
    w = 1.0 / np.maximum(d, 1e-6) ** power
    return (w @ zF) / w.sum(1)


def gwr(cF, yF, XF, cT, XT):
    """E6. Geographically weighted regression, adaptive bisquare, bandwidth by AICc."""
    from mgwr.gwr import GWR
    from mgwr.sel_bw import Sel_BW
    Xf, Xt = _std(XF, XT)
    y = yF.reshape(-1, 1)
    # Adaptive bandwidth is a NEIGHBOUR COUNT, so it cannot exceed the number of fitting sites.
    # mgwr's default golden-section bounds ignore that and tried 65 neighbours on 30 sites,
    # which is why E6 returned NaN on every fit of the first positive control (2026-09-11).
    n, p = len(yF), Xf.shape[1] + 1
    # n_jobs=1: mgwr defaults to a joblib/loky pool over the local fits. Inside our own worker
    # processes that pool SEGFAULTED on Kaggle (probe kandy-probe-hang-c24, 2026-09-15) and, when a
    # pool worker died, left its parent waiting forever -- clusters 7, 13 and 24 ran 11+ h twice.
    # Serial execution runs the same _local_fit per location: verified BIT-IDENTICAL (bandwidth and
    # every prediction) on 8 real fitting sets, so no city is scored differently for it.
    bw = Sel_BW(cF, y, Xf, fixed=False, kernel="bisquare", n_jobs=1).search(bw_min=p + 2, bw_max=n)
    res = GWR(cF, y, Xf, bw, fixed=False, kernel="bisquare", n_jobs=1).predict(cT, Xt)
    return np.asarray(res.predictions, dtype=float).ravel()


def tabpfn_fit_predict(Ftr, ytr, Fte):
    """E8/E9 core: TabPFN regressor, the package's default weights and settings, no tuning."""
    from tabpfn import TabPFNRegressor
    m = TabPFNRegressor(random_state=SEED)
    m.fit(np.asarray(Ftr, float), np.asarray(ytr, float))
    return np.asarray(m.predict(np.asarray(Fte, float)), dtype=float)


def loo_krige(cF, zF):
    """Kriging prediction at each fitting site from the OTHER fitting sites.

    Registered for E9: in-sample kriging reproduces a site's own value, which would place the
    target inside its own feature. Leave-one-out removes that leak.
    """
    out = np.empty(len(zF))
    for i in range(len(zF)):
        keep = np.arange(len(zF)) != i
        out[i] = krige(cF[keep], zF[keep], cF[i:i + 1])[0]
    return out


def predict_all(cF, yF, XF, cT, XT, bT, greyT, with_gwr, with_tab=False):
    """Every estimator for one fitting set. A failure returns None, is counted, never guessed."""
    out = {"E0": np.full(len(cT), float(np.mean(yF))), "E1": bT.astype(float)}
    try:
        e2, e2_in = ridge(XF, yF, XT)
        out["E2"] = e2
    except Exception:                                                      # noqa: BLE001
        out["E2"], e2_in = None, None
    try:
        out["E3"] = krige(cF, yF, cT)
    except Exception:                                                      # noqa: BLE001
        out["E3"] = None
    out["E4"] = idw(cF, yF, cT)
    try:
        out["E5"] = (out["E2"] + krige(cF, yF - e2_in, cT)) if e2_in is not None else None
    except Exception:                                                      # noqa: BLE001
        out["E5"] = None
    if with_gwr:
        try:
            out["E6"] = gwr(cF, yF, XF, cT, XT)
        except Exception:                                                  # noqa: BLE001
            out["E6"] = None
    if greyT is not None:
        out["E7"] = greyT.astype(float)
    if with_tab:
        try:
            out["E8"] = tabpfn_fit_predict(np.c_[XF, cF], yF, np.c_[XT, cT])
        except Exception:                                                  # noqa: BLE001
            out["E8"] = None
        try:
            pF, pT = loo_krige(cF, yF), krige(cF, yF, cT)
            out["E9"] = tabpfn_fit_predict(np.c_[XF, cF, pF], yF, np.c_[XT, cT, pT])
        except Exception:                                                  # noqa: BLE001
            out["E9"] = None
    return out


def srho(pred, obs) -> float:
    if pred is None or not np.all(np.isfinite(pred)):
        return np.nan
    if np.std(pred) < 1e-12 or np.std(obs) < 1e-12:
        return np.nan
    return float(spearmanr(pred, obs).statistic)


# ── design ────────────────────────────────────────────────────────────────────────────────────
def held_out(rng, c, n, kind):
    H = max(MIN_HELD, n // 3)
    if kind == "random":
        T = rng.choice(n, H, replace=False)
    else:                                   # blocked: the H sites nearest a random point
        lo, hi = c.min(0), c.max(0)
        p = lo + rng.random(2) * (hi - lo)
        T = np.argsort(np.hypot(c[:, 0] - p[0], c[:, 1] - p[1]))[:H]
    P = np.setdiff1d(np.arange(n), T)
    return np.sort(T), P


def clhs_set(Xs_pool, k, seed):
    from design_sensor_network import clhs                                 # noqa: E402
    return np.asarray(clhs(Xs_pool, k, seed), dtype=int)


def ceiling_rho(c, y) -> float:
    """Within-cell ceiling: every site predicted by the mean of the OTHER sites in its 1 km cell."""
    cell = [tuple(v) for v in np.floor(c).astype(int)]
    df = pd.DataFrame({"cell": cell, "y": y})
    g = df.groupby("cell").y
    tot, cnt = g.transform("sum"), g.transform("size")
    mask = cnt >= 2
    if mask.sum() < 8:
        return np.nan
    pred = (tot[mask] - df.y[mask]) / (cnt[mask] - 1)
    return srho(pred.to_numpy(), df.y[mask].to_numpy())


# ── one city ──────────────────────────────────────────────────────────────────────────────────
def _score_rows(prefix, pr, yT, grey_T):
    """Rows for one fitting set: every estimator on the full held-out set, then (D-5) every
    estimator AND E7 on the held-out sites inside the grey-box grid, so E7 is compared paired."""
    rows = []
    for est, p in pr.items():
        rows.append(prefix + (est, 0.0 if est == "E0" else srho(p, yT)))
    if grey_T is not None:
        m = np.isfinite(grey_T)
        if m.sum() >= E7_MIN_HELD:
            for est, p in pr.items():
                r = 0.0 if est == "E0" else (srho(p[m], yT[m]) if p is not None else np.nan)
                rows.append(prefix + (f"{est}|e7sub", r))
            rows.append(prefix + ("E7", srho(grey_T[m], yT[m])))
    return rows


def run_city(payload: dict) -> dict:
    cl = payload["cluster"]
    S = payload["sites"].reset_index(drop=True)
    n = len(S)
    H = max(MIN_HELD, n // 3)
    klist = [k for k in KS if k <= n - H]
    if not klist:
        return dict(cluster=cl, skipped=f"n={n} leaves no registered k")
    c = to_km(S.lat.to_numpy(), S.lon.to_numpy())
    y = S.static_mean.to_numpy(float)
    X = S[COVARS].to_numpy(float)
    b = S[BENCH].to_numpy(float)
    grey = (S["greybox"].to_numpy(float)
            if "greybox" in S and S.greybox.notna().any() else None)
    Xs_all = _std(X, X)[0]
    road = S["road_major_300"].to_numpy(float)
    splits_only = payload.get("splits_only", False)
    with_tab = payload.get("tabpfn", False)
    ids = S.site.astype(str).to_numpy()

    q1, q3, splits = [], [], []
    for rep in range(payload.get("reps", REPS)):
        rng = np.random.default_rng([SEED, int(cl), rep])
        for hk in ("random", "blocked"):
            T, P = held_out(rng, c, n, hk)
            orders = {"random": rng.permutation(P)}
            if hk == "random":
                tie = rng.random(len(P))
                orders["convenience"] = P[np.lexsort((tie, -road[P]))]
                orders["clhs"] = None
            for oname, order in orders.items():
                for k in klist:
                    if oname == "clhs":
                        seed_k = int(rng.integers(1 << 30))        # consumed in every mode
                        F = None if splits_only else P[clhs_set(Xs_all[P], k, seed_k)]
                    else:
                        F = order[:k]
                    primary = (oname == "random" and hk == "random")
                    if primary:
                        splits.append(dict(cluster=int(cl), rep=rep, k=int(k),
                                           fit="|".join(ids[F]), held="|".join(ids[T])))
                    if splits_only:
                        continue
                    with_gwr = (k >= GWR_MIN_K and primary)
                    pr = predict_all(c[F], y[F], X[F], c[T], X[T], b[T], None, with_gwr,
                                     with_tab=(with_tab and primary))
                    q1 += _score_rows((cl, rep, hk, oname, k), pr, y[T],
                                      None if grey is None else grey[T])
                    if primary:
                        dist = nearest_km(c[T], c[F])
                        sd = float(np.std(y[F])) or 1.0
                        for est in ("E0", "E3", "E4"):
                            p = pr.get(est)
                            if p is None:
                                continue
                            err = np.abs(p - y[T]) / sd
                            for dd, ee in zip(dist, err):
                                q3.append((cl, rep, k, est, float(dd), float(ee)))

    q2, q2_splits = run_city_q2(payload, S, c, X, b, grey, klist, splits_only, with_tab) \
        if payload.get("q2", True) else ([], [])
    return dict(cluster=cl, n=n, H=H, klist=klist, ceiling=ceiling_rho(c, y),
                q1=q1, q2=q2, q3=q3, splits=splits, q2_splits=q2_splits)


def run_city_q2(payload, S, c, X, b, grey, klist, splits_only=False, with_tab=False):
    """Per-DAY rows, so any day subset can be compared exactly paired (E8/E9 run on the first
    Q2_TAB_DAYS days of the first Q2_TAB_REPS replicates, per the amendment's declared budget)."""
    D = payload["daily"]
    if D is None or D.empty:
        return [], []
    W = D.pivot_table(index="day", columns="site", values="pm25").reindex(columns=S.site)
    V = W.to_numpy(float)
    day_index = W.index
    n = len(S)
    ids = S.site.astype(str).to_numpy()
    out, spl = [], []
    for rep in range(payload.get("q2_reps", Q2_REPS)):
        rng = np.random.default_rng([SEED, int(payload["cluster"]), 10_000 + rep])
        T, P = held_out(rng, c, n, "random")
        order = rng.permutation(P)
        full_T = np.isfinite(V[:, T]).all(1)
        days = np.flatnonzero(full_T)
        if len(days) == 0:
            continue
        days = rng.choice(days, min(Q2_DAYS, len(days)), replace=False)
        for k in klist:
            Fk = order[:k]
            spl.append(dict(cluster=int(payload["cluster"]), rep=rep, k=int(k),
                            fit="|".join(ids[Fk]), held="|".join(ids[T]),
                            days="|".join(str(day_index[d].date()) for d in days)))
            if splits_only:
                continue
            for pos, di in enumerate(days):
                v = V[di]
                F = Fk[np.isfinite(v[Fk])]
                if len(F) < 3:
                    continue
                tab = with_tab and rep < Q2_TAB_REPS and pos < Q2_TAB_DAYS
                pr = predict_all(c[F], v[F], X[F], c[T], X[T], b[T], None, with_gwr=False,
                                 with_tab=tab)
                for row in _score_rows((payload["cluster"], rep, k), pr, v[T],
                                       None if grey is None else grey[T]):
                    out.append(row[:3] + (int(pos),) + row[3:])
    return out, spl


# ── inference ─────────────────────────────────────────────────────────────────────────────────
def cluster_boot(vals: pd.Series, country: pd.Series, seed=SEED, n=N_BOOT):
    """Median of per-city values; 95% interval from a two-level bootstrap, countries then cities."""
    v = vals.dropna()
    if len(v) < 3:
        return (float(v.median()) if len(v) else np.nan, np.nan, np.nan, len(v))
    ctry = country.reindex(v.index)
    groups = [v[ctry == g].to_numpy() for g in ctry.unique()]
    rng = np.random.default_rng(seed)
    meds = np.empty(n)
    for i in range(n):
        pick = rng.integers(len(groups), size=len(groups))
        draw = np.concatenate([rng.choice(groups[j], len(groups[j]), replace=True) for j in pick])
        meds[i] = np.median(draw)
    return float(v.median()), float(np.quantile(meds, .025)), float(np.quantile(meds, .975)), len(v)


def mde_for(n_units: int) -> float:
    """Registered method: smallest paired effect, one-sided Wilcoxon, 80% power, sd 0.20."""
    rng = np.random.default_rng(SEED)
    for eff in np.arange(0.01, 1.01, 0.01):
        hits = 0
        for _ in range(400):
            x = rng.normal(eff, MDE_SD, n_units)
            try:
                if wilcoxon(x)[1] < 0.05 and np.median(x) > 0:
                    hits += 1
            except Exception:                                              # noqa: BLE001
                pass
        if hits / 400 >= 0.80:
            return round(float(eff), 3)
    return float("nan")


# ── data ──────────────────────────────────────────────────────────────────────────────────────
def load_frame():
    sfx = f"_{FRAME_TAG}" if FRAME_TAG else ""
    cities = pd.read_csv(SC / f"frame_cities{sfx}.csv")
    sites = pd.read_csv(SC / f"frame_sites{sfx}.csv")
    pred_f = SC / "frame_predictors.csv"
    if not pred_f.exists():
        raise SystemExit("frame_predictors.csv missing: run spatial_curve_predictors.py (D4) first")
    preds = pd.read_csv(pred_f)
    miss = [c for c in COVARS if c not in preds]
    if miss:
        raise SystemExit(f"predictors missing columns {miss}")
    sites = sites.merge(preds[["site"] + COVARS], on="site", how="left")
    gb = SC / "frame_greybox.csv"
    if gb.exists():
        sites = sites.merge(pd.read_csv(gb)[["site", "greybox"]], on="site", how="left")
    daily = pd.read_parquet(SC / f"frame_daily{sfx}.parquet") \
        if (SC / f"frame_daily{sfx}.parquet").exists() \
        else pd.DataFrame(columns=["cluster", "site", "day", "pm25"])
    return cities, sites, daily


# ── leakage self-test (registered) ────────────────────────────────────────────────────────────
def leakage_test() -> dict:
    """Registered: with merging disabled, a held-out site whose co-located twin is in the fitting
    set must be predicted by E3 with standardised error below 0.1.

    Uses sites that the freeze MERGED from two or more instruments. Each member's own window mean
    is rebuilt from its raw hourly file with the freeze's day rule, one member is placed in the
    fitting set beside every other site of the city, the other is held out, and E3 predicts it.
    The same prediction WITHOUT the twin is reported beside it, because the contrast between the
    two is what shows the guard is doing something.
    """
    from spatial_curve_freeze import qc_hourly                             # the freeze's own QC
    cities, sites, _ = load_frame()
    multi = sites[sites.n_members >= 2]
    rows, not_concurrent = [], 0
    for s in multi.itertuples():
        city = cities[cities.cluster == s.cluster].iloc[0]
        w0, w1 = pd.Timestamp(city.window_start, tz="UTC"), pd.Timestamp(city.window_end, tz="UTC")
        mem = []
        for loc in str(s.member_location_ids).split("|")[:2]:
            f = RAW / f"{loc}.parquet"
            if not f.exists():
                break
            h = pd.read_parquet(f)
            h = qc_hourly(h[(h.datetime_utc >= w0) & (h.datetime_utc < w1 + pd.Timedelta(days=1))])
            d = h.groupby(h.datetime_utc.dt.floor("D")).pm25.agg(["mean", "size"])
            d = d[d["size"] >= 18]
            if len(d) < 30:
                break
            mem.append(d["mean"])
        if len(mem) < 2:
            continue
        # D-7: a twin is CONCURRENT. Members are compared on the days both report, so a replaced
        # instrument (one record ends, the next begins) is not scored as a co-located twin.
        common = mem[0].index.intersection(mem[1].index)
        if len(common) < 30:
            not_concurrent += 1
            continue
        mem = [float(m.loc[common].mean()) for m in mem]
        others = sites[(sites.cluster == s.cluster) & (sites.site != s.site)]
        if len(others) < 5:
            continue
        cF_o = others[["lat", "lon"]].to_numpy()
        allc = to_km(np.r_[cF_o[:, 0], s.lat, s.lat], np.r_[cF_o[:, 1], s.lon, s.lon + 1e-6])
        cF, cTwin, cHeld = allc[:-2], allc[-2:-1], allc[-1:]
        yF = others.static_mean.to_numpy(float)
        sd = float(np.std(np.r_[yF, mem[0]]))
        try:
            with_twin = krige(np.r_[cF, cTwin], np.r_[yF, mem[0]], cHeld)[0]
            without = krige(cF, yF, cHeld)[0]
        except Exception:                                                  # noqa: BLE001
            continue
        rows.append(dict(cluster=s.cluster, site=s.site,
                         err_with_twin=abs(with_twin - mem[1]) / sd,
                         err_without_twin=abs(without - mem[1]) / sd,
                         twin_gap=abs(mem[0] - mem[1]) / sd))
    R = pd.DataFrame(rows)
    OUTD.mkdir(parents=True, exist_ok=True)
    R.to_csv(OUTD / "leakage_test.csv", index=False)
    if R.empty:
        res = dict(ran=False, reason="no merged multi-instrument site with usable member records")
    else:
        med = float(R.err_with_twin.median())
        res = dict(ran=True, pairs=len(R), cities=int(R.cluster.nunique()),
                   pairs_skipped_not_concurrent=not_concurrent,
                   median_err_with_twin=round(med, 4),
                   median_err_without_twin=round(float(R.err_without_twin.median()), 4),
                   median_twin_gap=round(float(R.twin_gap.median()), 4),
                   threshold=LEAK_THRESHOLD, passed=bool(med < LEAK_THRESHOLD))
    print(json.dumps(res, indent=2))
    return res


# ── positive control ──────────────────────────────────────────────────────────────────────────
def synthetic_city(seed=7, n=60) -> dict:
    """A city with a KNOWN smooth field. E3 must recover it; if it cannot, nothing real is trusted."""
    import gstools as gs
    rng = np.random.default_rng(seed)
    xy = rng.random((n, 2)) * 20.0
    srf = gs.SRF(gs.Exponential(dim=2, var=1.0, len_scale=4.0), seed=seed)
    f = srf((xy[:, 0], xy[:, 1]))
    lat = 10 + xy[:, 1] / 110.57
    lon = 100 + xy[:, 0] / (111.32 * np.cos(np.radians(10)))
    S = pd.DataFrame({"site": [f"syn_{i}" for i in range(n)], "lat": lat, "lon": lon,
                      "static_mean": 25 + 5 * f})
    for i, cv in enumerate(COVARS):
        S[cv] = (f + rng.normal(0, 1.0, n)) if cv == BENCH else rng.normal(0, 1, n)
    # a large positive id: SeedSequence rejects negative integers, and -1 crashed the first run
    return dict(cluster=990_001, sites=S, daily=None, reps=10, q2=False)


def positive_control(reps: int = 40) -> bool:
    """Judged against ORACLE kriging, which is given the synthetic field's true variogram.

    The first version required E3 to exceed 0.5 at the largest k. That number was a guess, and
    oracle kriging itself reaches only about 0.57 on this 60-site field, so it tested the guess
    and not the machinery. What working machinery must do is this:
      * fitted-variogram kriging comes within 0.05 of the oracle at the largest k,
      * E3 rises from the smallest k to the largest,
      * E3 beats the uniform-city floor at the largest k, and
      * GWR (E6) returns finite predictions wherever it is scheduled.
    40 replicates: at 10 the same configuration read 0.484 and 0.556 in two runs, too unstable
    for a check that gates everything downstream.
    """
    from pykrige.ok import OrdinaryKriging
    p = synthetic_city()
    p["reps"] = reps
    r = run_city(p)
    q = pd.DataFrame(r["q1"], columns=["cluster", "rep", "holdout", "ordering", "k", "est", "rho"])
    q = q[(q.holdout == "random") & (q.ordering == "random")]
    m = q.groupby(["est", "k"]).rho.median().unstack()

    # oracle on the SAME splits: exponential, sill 25 (field var 1 x scale 5^2), practical
    # range 12 km (PyKrige uses range/3 as the e-folding length; the field's is 4 km)
    S = p["sites"].reset_index(drop=True)
    c = to_km(S.lat.to_numpy(), S.lon.to_numpy())
    y = S.static_mean.to_numpy(float)
    kmax = max(r["klist"])
    orc = []
    for rep in range(reps):
        rng = np.random.default_rng([SEED, int(p["cluster"]), rep])
        T, P = held_out(rng, c, len(S), "random")
        F = rng.permutation(P)[:kmax]
        ok = OrdinaryKriging(c[F, 0], c[F, 1], y[F], variogram_model="exponential",
                             variogram_parameters=[25.0, 12.0, 0.0],
                             enable_plotting=False, verbose=False)
        orc.append(srho(np.asarray(ok.execute("points", c[T, 0], c[T, 1])[0]), y[T]))
    oracle = float(np.nanmedian(orc))

    print(f"positive control, {reps} replicates, median held-out rho (rows estimator, columns k):")
    print(m.round(3).to_string())
    e3_lo, e3_hi = m.loc["E3", min(r["klist"])], m.loc["E3", kmax]
    e6 = m.loc["E6"].dropna() if "E6" in m.index else pd.Series(dtype=float)
    checks = {
        f"E3 within 0.05 of oracle at k={kmax} ({e3_hi:.3f} vs {oracle:.3f})": e3_hi >= oracle - 0.05,
        f"E3 rises with k ({e3_lo:.3f} -> {e3_hi:.3f})": e3_hi > e3_lo,
        f"E3 beats the floor at k={kmax}": e3_hi > m.loc["E0", kmax],
        f"E6 finite where scheduled ({len(e6)} k values)": len(e6) > 0,
    }
    for k, ok_ in checks.items():
        print(f"  {'PASS' if ok_ else 'FAIL'}  {k}")
    ok_all = all(checks.values())
    print(f"\npositive control: {'PASS' if ok_all else 'FAIL'}")
    return bool(ok_all)


# ── summary and verdicts ──────────────────────────────────────────────────────────────────────
# ── deep arms (amendment 26hp8) ───────────────────────────────────────────────────────────────
# E10 and E11 are trained and scored on Kaggle, on the splits this script exported, and arrive as
# pred_*.parquet files. Directories are given by SPATIAL_DL_PRED_DIRS (os.pathsep-separated).
DEEP_DIRS = [Path(p) for p in os.environ.get("SPATIAL_DL_PRED_DIRS", "").split(os.pathsep) if p] \
    or [SC / "dl_out"]
CONTROL_LABEL = {"E10": "E10 ConvGNP", "E11": "E11 TNP-D"}


def merge_deep(Q1, Q2):
    """Append E10/E11 rows as the MEDIAN OVER SEEDS per task (registered), with the seed spread
    reported; and read the registered positive controls that gate their interpretation."""
    frame = FRAME_TAG or "registered"
    files = [f for d in DEEP_DIRS if d.exists() for f in d.rglob("pred_*.parquet")]
    info = dict(dirs=[str(d) for d in DEEP_DIRS], files=len(files))
    ctl = {}
    for d in DEEP_DIRS:
        if not d.exists():
            continue
        for f in d.rglob("control_*.json"):
            j = json.loads(f.read_text())
            if j.get("primary_control"):
                ctl.setdefault(j["arm"], []).append(bool(j["passed"]))
    info["controls"] = {a: dict(runs=len(v), passed_all=all(v)) for a, v in ctl.items()}
    if not files:
        info["note"] = "no deep predictions found; E10/E11 not merged"
        return Q1, Q2, info
    # D-8 guard (2026-09-23): E8/E9 may enter ONLY from the consolidated CPU file written by
    # spatial_curve_tabpfn_consolidate.py. The default DEEP_DIRS (dl_out/) still holds a GPU-era
    # pred_tabpfn_fold4.parquet, which this function used to merge without a word.
    parts = []
    for f in files:
        d = pd.read_parquet(f)
        if d.est.isin(["E8", "E9"]).any() and not f.name.startswith("pred_tabpfn_consolidated_"):
            raise RuntimeError(f"D-8: E8/E9 rows in {f} -- only pred_tabpfn_consolidated_*.parquet "
                               "(CPU-only, one source per city) may be merged")
        if f.name.startswith("pred_tabpfn_consolidated_") and not (
                "device" in d.columns and bool((d["device"] == "cpu").all())):
            raise RuntimeError(f"D-8: {f.name} lacks device == 'cpu' on every row")
        d["_src"] = str(f); parts.append(d)
    P_ = pd.concat(parts, ignore_index=True)
    P_ = P_[P_.frame == frame]
    key = ["design", "cluster", "rep", "k", "day", "est"]
    # One scoring per (task, seed): a second source of the same task would be silently averaged
    # by the median below. Byte-identical copies (dl_out/fold* vs e10_fold*) are collapsed, any
    # disagreement is refused.
    dupk = key + ["seed"]
    P_ = P_.drop_duplicates(dupk + ["rho"])
    clash = int(P_.duplicated(dupk).sum())
    if clash:
        raise RuntimeError(f"{clash} (task, seed) keys scored differently in two files: pass one "
                           "source per arm via SPATIAL_DL_PRED_DIRS")
    info["sources"] = sorted(P_._src.map(lambda s: Path(s).name).unique().tolist())
    P_ = P_.drop(columns="_src")
    g = P_.groupby(key).rho
    med = g.median().rename("rho").reset_index()
    iqr = (g.quantile(.75) - g.quantile(.25)).rename("iqr").reset_index()
    info["seeds"] = {e: int(P_[P_.est == e].seed.nunique()) for e in P_.est.unique()}
    info["seed_iqr_median"] = {e: float(iqr[iqr.est == e].iqr.median()) for e in P_.est.unique()}
    q1 = med[med.design == "Q1"]
    Q1 = pd.concat([Q1, pd.DataFrame({"cluster": q1.cluster, "rep": q1.rep, "holdout": "random",
                                      "ordering": "random", "k": q1.k, "est": q1.est,
                                      "rho": q1.rho})], ignore_index=True)
    q2 = med[med.design == "Q2"]
    Q2 = pd.concat([Q2, pd.DataFrame({"cluster": q2.cluster, "rep": q2.rep, "k": q2.k,
                                      "day": q2.day, "est": q2.est, "rho": q2.rho})],
                   ignore_index=True)
    return Q1, Q2, info


def summarise(cities, results) -> dict:
    Q1 = pd.DataFrame([x for r in results for x in r.get("q1", [])],
                      columns=["cluster", "rep", "holdout", "ordering", "k", "est", "rho"])
    Q2 = pd.DataFrame([x for r in results for x in r.get("q2", [])],
                      columns=["cluster", "rep", "k", "day", "est", "rho"])
    pd.DataFrame([x for r in results for x in r.get("splits", [])]).to_parquet(
        OUTD.parent / (OUTD.name + "_splits_q1.parquet"), index=False)
    Q3 = pd.DataFrame([x for r in results for x in r.get("q3", [])],
                      columns=["cluster", "rep", "k", "est", "dist_km", "err"])
    Q1, Q2, deep_info = merge_deep(Q1, Q2)
    OUTD.mkdir(parents=True, exist_ok=True)
    Q1.to_parquet(OUTD / "q1.parquet", index=False)
    Q2.to_parquet(OUTD / "q2.parquet", index=False)
    Q3.to_parquet(OUTD / "q3.parquet", index=False)

    C = cities.set_index("cluster")
    prim = C.index[C.primary.astype(bool)]
    arm = C.index[C.band_arm.astype(bool)]
    ctry = C.country
    n_ctry = int(C.loc[prim, "country"].nunique())
    mde = mde_for(n_ctry)
    ceil = pd.Series({r["cluster"]: r.get("ceiling", np.nan) for r in results})

    base = Q1[(Q1.holdout == "random") & (Q1.ordering == "random")]
    city_k = base.groupby(["cluster", "est", "k"]).rho.median().rename("rho").reset_index()
    city_k.to_csv(OUTD / "curve_q1_city.csv", index=False)

    # pooled level curve, with its city count at every k (composition caveat)
    pooled = []
    for (est, k), g in city_k[city_k.cluster.isin(prim)].groupby(["est", "k"]):
        med, lo, hi, nn = cluster_boot(g.set_index("cluster").rho, ctry)
        pooled.append(dict(est=est, k=k, median=med, lo=lo, hi=hi, cities=nn))
    pd.DataFrame(pooled).to_csv(OUTD / "curve_q1_pooled.csv", index=False)

    # paired within-city increments between consecutive registered k (nested orderings)
    inc_rows = []
    for est in EST_ALL:
        e = base[base.est == est]
        for k0, k1 in zip(KS[:-1], KS[1:]):
            a = e[e.k == k0].set_index(["cluster", "rep"]).rho
            b2 = e[e.k == k1].set_index(["cluster", "rep"]).rho
            d = (b2 - a).dropna()
            if d.empty:
                continue
            per_city = d.groupby(level=0).median()
            per_city = per_city[per_city.index.isin(prim)]
            med, lo, hi, nn = cluster_boot(per_city, ctry)
            inc_rows.append(dict(est=est, k0=k0, k1=k1, median=med, lo=lo, hi=hi, cities=nn))
    INC = pd.DataFrame(inc_rows)
    INC.to_csv(OUTD / "increments.csv", index=False)

    def kstar(est):
        e = INC[INC.est == est].sort_values("k0")
        for r in e.itertuples():
            if np.isfinite(r.lo) and r.lo <= 0 <= r.hi and r.median < SAT_MEDIAN:
                return int(r.k0)
        return None

    # per-city crossover over E1, bootstrapped over replicates within city
    def city_crossover(est):
        out = {}
        for cl in prim:
            e = base[base.cluster == cl]
            adv = (e[e.est == est].set_index(["rep", "k"]).rho
                   - e[e.est == "E1"].set_index(["rep", "k"]).rho).dropna()
            kx = None
            for k in sorted(adv.index.get_level_values("k").unique()):
                v = adv.xs(k, level="k").to_numpy()
                if len(v) < 10:
                    continue
                rng = np.random.default_rng(SEED)
                bs = np.median(rng.choice(v, (2000, len(v))), axis=1)
                if np.quantile(bs, .025) > 0:
                    kx = int(k)
                    break
            out[cl] = kx
        return out

    cross = {e: city_crossover(e) for e in ("E3", "E5")}
    pd.DataFrame(cross).to_csv(OUTD / "crossover_city.csv")

    # Q3 reach, E3 primary and E4 beside it (D-4)
    Q3["bin"] = pd.cut(Q3.dist_km, DIST_BINS, right=False)
    reach = {}
    for est in ("E3", "E4"):
        rc = {}
        for cl in prim:
            q = Q3[Q3.cluster == cl]
            bins = q.bin.cat.categories
            val = None
            for bn in bins:
                qe = q[(q.bin == bn) & (q.est == est)].groupby("rep").err.median()
                q0 = q[(q.bin == bn) & (q.est == "E0")].groupby("rep").err.median()
                j = pd.concat([qe, q0], axis=1, keys=["e", "z"]).dropna()
                if len(j) < 10:
                    continue
                d = (j.z - j.e).to_numpy()
                rng = np.random.default_rng(SEED)
                bs = np.median(rng.choice(d, (2000, len(d))), axis=1)
                if np.quantile(bs, .025) <= 0:          # no longer better than the uniform city
                    val = float(bn.left)
                    break
            rc[cl] = val
        reach[est] = rc
    pd.DataFrame(reach).to_csv(OUTD / "reach_city.csv")

    # ── verdicts, exactly as registered ──
    v = {}
    x1 = {}
    for est in ("E3", "E4"):
        e = INC[(INC.est == est) & (INC.cities >= 3)]
        x1[est] = bool((e["median"] > 0).all()) if len(e) else None
    v["X1"] = dict(holds=(all(x1.values()) if all(x is not None for x in x1.values()) else None),
                   detail=x1)

    frac = {e: float(np.mean([(kx is not None and kx <= CROSS_K_MAX) for kx in cross[e].values()]))
            for e in cross}
    per_city_any = [any(cross[e][cl] is not None and cross[e][cl] <= CROSS_K_MAX for e in cross)
                    for cl in prim]
    v["X2"] = dict(holds=bool(np.mean(per_city_any) >= 0.5) if len(prim) else None,
                   share_of_primary_cities=float(np.mean(per_city_any)) if len(prim) else None,
                   share_by_estimator=frac)

    ks2 = kstar("E2")
    x3_diff = None
    if ks2 is not None:
        g = city_k[(city_k.k == ks2) & city_k.cluster.isin(prim)].pivot(
            index="cluster", columns="est", values="rho")
        if {"E2", "E1"} <= set(g.columns):
            x3_diff = float((g.E2 - g.E1).median())
    v["X3"] = dict(holds=bool(ks2 is not None and ks2 <= 12 and x3_diff is not None
                              and abs(x3_diff) < mde),
                   k_star_E2=ks2, paired_E2_minus_E1_at_k_star=x3_diff)

    over = []
    for cl in prim:
        if not np.isfinite(ceil.get(cl, np.nan)):
            continue
        g = city_k[city_k.cluster == cl]
        over.append(bool((g.rho - ceil[cl] > mde).any()))
    v["X4"] = dict(holds=(not any(over)) if over else None, cities_with_ceiling=len(over))

    q4 = Q1[(Q1.holdout == "random")]
    cr = (q4[q4.ordering == "clhs"].set_index(["cluster", "rep", "k", "est"]).rho
          - q4[q4.ordering == "random"].set_index(["cluster", "rep", "k", "est"]).rho).dropna()
    per_city = cr.groupby(level=0).median()
    med4, lo4, hi4, n4 = cluster_boot(per_city[per_city.index.isin(prim)], ctry)
    v["X5"] = dict(holds=(bool(med4 < mde) if n4 >= 3 and np.isfinite(med4) else None),
                   clhs_minus_random=dict(median=med4, lo=lo4, hi=hi4, cities=n4))

    if not Q2.empty:
        q2r = Q2.groupby(["cluster", "rep", "k", "est"]).rho.median().reset_index()
        c2 = q2r.groupby(["cluster", "est", "k"]).rho.median().rename("rho2")
        both = city_k.set_index(["cluster", "est", "k"]).join(c2, how="inner").reset_index()
        below = {e: bool((both[both.est == e].rho2 < both[both.est == e].rho).mean() > 0.5)
                 for e in both.est.unique() if e != "E0"}
        v["X6"] = dict(holds=bool(all(below.values())), q2_below_q1=below)
    else:
        v["X6"] = dict(holds=None, reason="Q2 produced no eligible days")

    rv = [x for x in reach["E3"].values() if x is not None]
    v["X7"] = dict(holds=bool(rv and np.median(rv) < REACH_KM_MAX) if rv else None,
                   median_reach_km=float(np.median(rv)) if rv else None, cities=len(rv))

    env = city_k[(city_k.est == "E3") & city_k.cluster.isin(prim)].groupby("k").rho.agg(["min", "max"])
    inside = {}
    for cl in arm:
        g = city_k[(city_k.cluster == cl) & (city_k.est == "E3")].set_index("k").rho
        j = g.to_frame().join(env, how="inner")
        inside[int(cl)] = bool(((j.rho >= j["min"]) & (j.rho <= j["max"])).all()) if len(j) else None
    v["X8_exploratory"] = dict(inside_envelope=inside)

    # ── X9-X13, amendment 26hp8, exactly as registered ──
    deep = [e for e in ("E8", "E9", "E10", "E11") if e in set(city_k.est)]
    ks_all = sorted(city_k.k.unique())

    def paired_k(a, b, k):
        g = city_k[(city_k.k == k) & city_k.cluster.isin(prim)].pivot(
            index="cluster", columns="est", values="rho")
        if a not in g or b not in g:
            return None
        d = (g[a] - g[b]).dropna()
        # a primary-frame claim needs at least 3 cities, the floor cluster_boot uses for intervals
        return cluster_boot(d, ctry) if len(d) >= 3 else None

    x9 = {}
    for e in deep:
        adv = [paired_k(e, "E5", k) for k in ks_all]
        adv = [r[0] for r in adv if r and np.isfinite(r[0])]
        x9[e] = max(adv) if adv else None
    ev9 = [w for w in x9.values() if w is not None]
    # no evaluable comparison is NOT a confirmation: all() over nothing would return True
    v["X9"] = dict(holds=(all(w <= mde for w in ev9) if ev9 else None),
                   max_paired_advantage_over_E5=x9)
    x10 = {}
    for k in [k for k in ks_all if k >= 12]:
        r = paired_k("E9", "E8", k)
        if r:
            x10[int(k)] = dict(median=r[0], lo=r[1], hi=r[2])
    v["X10"] = dict(holds=(all(np.isfinite(d["lo"]) and d["lo"] > 0 for d in x10.values())
                           if x10 else None), by_k=x10)
    x11 = {}
    for e in ("E10", "E11"):
        if e not in deep:
            continue
        vals = []
        for cl in prim:
            g = city_k[city_k.cluster == cl].pivot(index="k", columns="est", values="rho")
            if e not in g or "E3" not in g:
                continue
            adv = (g[e] - g["E3"]).dropna().sort_index()
            small, big = adv[adv.index.isin([3, 5])], adv.iloc[-2:]
            if len(small) and len(big) and not set(small.index) & set(big.index):
                vals.append(float(small.mean() - big.mean()))
        x11[e] = dict(median_small_minus_large=float(np.median(vals)) if vals else None,
                      cities=len(vals))
    v["X11"] = dict(holds={e: (None if d["median_small_minus_large"] is None or d["cities"] < 3
                               else bool(d["median_small_minus_large"] > 0))
                           for e, d in x11.items()} or None, detail=x11)
    x12 = {}
    for k in ks_all:
        r = paired_k("E10", "E11", k)
        if r and np.isfinite(r[0]):
            x12[int(k)] = r[0]
    v["X12"] = dict(holds=all(abs(x) < mde for x in x12.values()) if x12 else None,
                    paired_E10_minus_E11=x12)
    x13 = {}
    for e in ("E10", "E11"):
        env_e = city_k[(city_k.est == e) & city_k.cluster.isin(prim)].groupby("k").rho.agg(["min", "max"])
        for cl in arm:
            g = city_k[(city_k.cluster == cl) & (city_k.est == e)].set_index("k").rho
            j = g.to_frame().join(env_e, how="inner")
            x13[f"{e}@{int(cl)}"] = (bool(((j.rho >= j["min"]) & (j.rho <= j["max"])).all())
                                     if len(j) else None)
    v["X13_exploratory"] = dict(inside_envelope=x13)
    gate = {}
    for e in ("E10", "E11"):
        c = deep_info.get("controls", {}).get(CONTROL_LABEL[e])
        gate[e] = ("control not found" if c is None else
                   "PASSED: interpretable" if c["passed_all"] else
                   "FAILURE TO TRAIN: positive control not passed; results NOT interpreted")
    v["deep_gate"] = gate

    summary = dict(registration="OSF rqn4y + amendment 26hp8", deviations=DEVIATIONS,
                   deep=deep_info,
                   primary_cities=len(prim), primary_countries=n_ctry,
                   detection_limit_at_countries=mde, band_arm=[int(x) for x in arm],
                   k_star={e: kstar(e) for e in EST_ALL}, verdicts=v)
    (OUTD / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--cities", type=int, default=0, help="limit, for a smoke run")
    ap.add_argument("--synthetic", action="store_true", help="positive control only")
    ap.add_argument("--leakage-test", action="store_true", help="registered self-test only")
    ap.add_argument("--with-tabpfn", action="store_true",
                    help="score E8/E9 (needs TABPFN_TOKEN)")
    ap.add_argument("--defer-dl-arms", action="store_true",
                    help="acknowledge that E8/E9 are NOT scored in this run")
    ap.add_argument("--export-splits", action="store_true",
                    help="write the exact splits for the Kaggle arms, score nothing")
    ap.add_argument("--frame-tag", default="",
                    help="\"\" = registered frame; s70 = declared sensitivity S-1")
    ap.add_argument("--city-cache", default="",
                    help="directory of per-city results; a city already there is not re-scored")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--n-shards", type=int, default=1)
    ap.add_argument("--require-cache", action="store_true",
                    help="summary run: refuse if any city is missing from --city-cache")
    ap.add_argument("--score-only", action="store_true",
                    help="score and cache cities, then stop without summarising")
    ap.add_argument("--only-clusters", default="",
                    help="comma-separated cluster ids to score; selects work, never changes scoring")
    a = ap.parse_args()
    global FRAME_TAG, OUTD
    FRAME_TAG = a.frame_tag
    OUTD = SC / ("analysis" + (f"_{FRAME_TAG}" if FRAME_TAG else ""))
    print(f"frame: {'registered (75 per cent)' if not FRAME_TAG else 'SENSITIVITY ' + FRAME_TAG}"
          f" -> {OUTD.name}")

    if a.synthetic:
        return 0 if positive_control() else 1
    if a.leakage_test:
        r = leakage_test()
        return 0 if (not r.get("ran") or r.get("passed")) else 1

    print("=== positive control ===")
    if not positive_control():
        print("\nThe machinery failed its positive control. Stopping.")
        return 1
    print("\n=== registered leakage self-test ===")
    lt = leakage_test()
    if lt.get("ran") and not lt.get("passed"):
        print("\nRegistered self-test FAILED. Scoring does not proceed (registration Section 4).")
        return 2

    if not (a.with_tabpfn or a.defer_dl_arms or a.export_splits or a.cities):
        print("E8/E9 are registered (amendment 26hp8). Pass --with-tabpfn to score them or "
              "--defer-dl-arms to acknowledge they are not in this run.")
        return 3
    if a.with_tabpfn:
        # NO `import os` HERE. `os` is imported at module level, and a function-local import makes
        # it a LOCAL for the whole of main() -- so when this branch does not run, every later
        # `os.replace` raises UnboundLocalError. That cost 9.6 hours across eight Kaggle processes
        # on 2026-09-14: each finished its city, wrote the cache temp file, and died on the rename.
        if not os.environ.get("TABPFN_TOKEN"):
            # fall back to the untracked credentials file; set before the pool so workers inherit it
            cred = REPO.parent / "API.txt"
            if cred.exists():
                for ln in cred.read_text(encoding="utf-8", errors="replace").splitlines():
                    if ln.strip().startswith("TABPFN_TOKEN="):
                        os.environ["TABPFN_TOKEN"] = ln.split("=", 1)[1].strip()
        if not os.environ.get("TABPFN_TOKEN"):
            print("--with-tabpfn needs TABPFN_TOKEN (Prior Labs licence). Not set.")
            return 3
    cities, sites, daily = load_frame()
    use = cities[(cities.primary.astype(bool)) | (cities.secondary.astype(bool))
                 | (cities.band_arm.astype(bool))]
    if a.cities:
        use = use.nlargest(a.cities, "sites")
    if a.only_clusters:
        # Named cities, for re-running exactly the ones still missing: a shard slice mixed a
        # 44-site city with an 18-site one, and the small one waited a whole session (2026-09-15).
        want = {int(x) for x in a.only_clusters.split(",") if x.strip()}
        unknown = want - set(use.cluster.astype(int))
        if unknown:
            print(f"--only-clusters: not in this frame: {sorted(unknown)}")
            return 4
        use = use[use.cluster.astype(int).isin(want)]
    if a.n_shards > 1:
        # Cities are scored independently, so they can be split across sessions. Needed because a
        # Kaggle session is killed at 12 h, and a 2026-09-13 run reached that wall with NOT ONE of
        # 37 cities finished -- twelve hours discarded, because nothing was written to disk until
        # the whole frame was done.
        # Balanced by SIZE, not by cluster id. Cost rises steeply with site count (a 13-site city
        # scores in 1.3 min, and the frame's largest hold 75, 114 and 120 sites), and a plain
        # `cluster % n_shards` put all three of those in one kernel -- which would have been the
        # only shard at risk of the wall. Dealing the cities out largest-first spreads the tail.
        # Deterministic: ties broken by cluster id, so every process derives the same partition.
        order = use.sort_values(["sites", "cluster"], ascending=[False, True]).cluster.tolist()
        mine = {c for i, c in enumerate(order) if i % a.n_shards == a.shard}
        use = use[use.cluster.isin(mine)]
        print(f"shard {a.shard} of {a.n_shards}: {len(use)} cities "
              f"({int(use.sites.sum())} sites)")
    print(f"=== scoring {len(use)} cities with {a.workers} workers ===")
    payloads = [dict(cluster=int(cl), sites=sites[sites.cluster == cl],
                     daily=daily[daily.cluster == cl], tabpfn=a.with_tabpfn,
                     splits_only=a.export_splits) for cl in use.cluster]

    cache = Path(a.city_cache) if a.city_cache else None
    if cache:
        cache.mkdir(parents=True, exist_ok=True)

    def cache_file(cl):
        return cache / f"city_{FRAME_TAG or 'registered'}_{cl}.pkl"

    results, todo = [], []
    for pay in payloads:
        cf = cache_file(pay["cluster"]) if cache else None
        if cf is not None and cf.exists():
            try:
                results.append(pickle.loads(cf.read_bytes()))
                continue
            except Exception as ex:                                          # noqa: BLE001
                print(f"  cache unreadable for cluster {pay['cluster']} ({ex}); re-scoring")
        todo.append(pay)
    if cache:
        print(f"  {len(results)} cities from cache, {len(todo)} to score", flush=True)
    if a.require_cache and todo:
        # The summary run must summarise the scored cities, never quietly re-score a missing one.
        print(f"REFUSING (--require-cache): {len(todo)} cities not in the cache: "
              f"{sorted(int(p['cluster']) for p in todo)}", flush=True)
        return 6

    t0 = time.time()
    if todo:
        with ProcessPoolExecutor(a.workers) as ex:
            futs = {ex.submit(run_city, pp): pp["cluster"] for pp in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                r = fut.result()
                results.append(r)
                if cache:
                    # temp file + os.replace: a truncating open here would destroy a finished
                    # city's result if the session were killed mid-write
                    dst = cache_file(r["cluster"])
                    tmp = dst.with_suffix(".pkl.tmp")
                    tmp.write_bytes(pickle.dumps(r))
                    os.replace(tmp, dst)
                print(f"  {i}/{len(todo)} cluster {r['cluster']} "
                      f"{'skipped: ' + r['skipped'] if 'skipped' in r else 'n=' + str(r['n'])} "
                      f"| {(time.time() - t0) / 60:.1f} min", flush=True)
    if a.score_only:
        print(f"scored and cached {len(results)} cities; not summarising (--score-only)")
        return 0
    if a.export_splits:
        OUTD.mkdir(parents=True, exist_ok=True)
        sp1 = pd.DataFrame([x for r in results for x in r.get('splits', [])])
        sp2 = pd.DataFrame([x for r in results for x in r.get('q2_splits', [])])
        sp1.to_parquet(OUTD / 'splits_q1_primary.parquet', index=False)
        sp2.to_parquet(OUTD / 'splits_q2.parquet', index=False)
        print(f'exported {len(sp1):,} Q1 primary splits and {len(sp2):,} Q2 splits to {OUTD}')
        return 0
    s = summarise(cities, results)
    print(json.dumps(s, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
