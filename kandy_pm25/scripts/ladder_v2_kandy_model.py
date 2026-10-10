"""ladder_v2_kandy_model.py -- the deployed Kandy model's temporal anchor scored as a rung of the ladder.

EXPLORATORY. Spec fixed before scoring: docs/kandy_model_rung_spec_2026-10-10.md (git a45cf0c + amendment).
Frozen modules (ladder_v2, ladder_v2_confirm, transfer_validation.t_anchor) are imported, never edited.

The field's city mean is T(t) exactly (P has unit spatial mean), so scoring the daily city mean scores T(t).
Arms per city x split, all on the identical set of scored days:
  Bud0      ladder sensorless rung (cached LOCO bag-of-5)
  Bud0cal2  Bud0 + intercept/slope fitted to the first two pool stations
  K0        Kandy chain, no stations: GEOS-CF daily, per-year additive shift to van Donkelaar
  K2        Kandy chain as deployed (daily), anchors = first two pool stations
  L2same    first two stations read on the day (fit on pool[2:6], as review sym L2s, no shrinkage)
Uses: reconstruction (fit over the scored period) and prospective (fit before the midpoint).

Usage: python scripts/ladder_v2_kandy_model.py [--splits 21] [--workers 4] [--limit K] [--boot 4000]
Out:   data/processed/modular/ladder_v2/kandy_model_{splits,percity_*,summary}.*
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
warnings.filterwarnings("ignore")

import ladder_v2 as L                                                   # noqa: E402
from ladder_frames import SEED                                          # noqa: E402
from modular_validation_all import _affine                              # noqa: E402
from src.transfer_validation.t_anchor import CLIP_SHARPEN, LGBM_PARAMS  # noqa: E402

KM = REPO / "data" / "processed" / "modular" / "kandy_model_rung"
OUTD = L.OUTD
LAST_DAY = pd.Timestamp("2025-12-31")
ALPHA, N_FOLDS = 0.10, 5
ARMS = ("Bud0", "Bud0cal2", "K0", "K2", "L2same")
MET = {"t2m": "temperature_2m", "u10": "u_component_of_wind_10m", "v10": "v_component_of_wind_10m",
       "blh": "boundary_layer_height"}
FEATS = ["sin_doy", "cos_doy", "dow", "blh", "u10", "v10", "wspd", "t2m", "prior_scaled"]
PARAMS = {**LGBM_PARAMS, "n_jobs": 1}


# ── inputs ──────────────────────────────────────────────────────────────────────────────────
def load_priors():
    g = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(KM / "raw" / "kmr_geoscf_*.csv")))],
                  ignore_index=True)
    g = g.rename(columns={"mean": "prior"}).dropna(subset=["prior"])
    g["city"] = g.city.astype(str); g["date"] = pd.to_datetime(g.date)
    g = g[(g.n_hours >= 18) & (g.date <= LAST_DAY)].drop_duplicates(["city", "date"])
    v = pd.read_csv(KM / "vand_annual.csv"); v["city"] = v.city.astype(str)
    return g[["city", "date", "prior"]], v.dropna(subset=["vand"])


def vand_level(v_city: pd.Series, year: int) -> float:
    y = min(year, int(v_city.index.max()))
    return float(v_city.get(y, v_city.iloc[-1]))


# ── the Kandy chain at daily resolution ─────────────────────────────────────────────────────
def reanchor(df, col_list, v_city):
    """Per calendar year, shift so the year's mean of q50 equals the van Donkelaar level (all days of the year)."""
    yr = df.date.dt.year
    for y in yr.unique():
        m = (yr == y).to_numpy()
        shift = vand_level(v_city, int(y)) - float(df.loc[m, col_list[0]].mean())
        for c in col_list:
            df.loc[m, c] = df.loc[m, c] + shift
    return df


def k0(drv, v_city):
    d = drv[["date", "prior"]].copy()
    d["K0"] = d.prior
    return reanchor(d, ["K0"], v_city).set_index("date").K0


def k2(drv, anchor, v_city, fit_before=None):
    """t_anchor.fit_and_build at daily resolution (hour features and hour sharpening dropped)."""
    from lightgbm import LGBMRegressor
    a = anchor.rename("a")
    j = drv.set_index("date").join(a, how="inner").dropna(subset=["a", "prior"])
    if fit_before is not None:
        j = j[j.index < fit_before]
    if len(j) < 120:
        return None
    ratio = float(j.a.mean() / j.prior.mean())                          # row-mean (gotcha #39)
    D = drv.copy(); D["prior_scaled"] = D.prior * ratio
    tr = D.set_index("date").join(a, how="inner").dropna(subset=FEATS + ["a"])
    if fit_before is not None:
        tr = tr[tr.index < fit_before]
    tr = tr.sort_index()
    X, y = tr[FEATS], tr.a - tr.prior_scaled
    heads, oof = {}, {}
    fold = np.arange(len(tr)) * N_FOLDS // len(tr)
    for q in (0.05, 0.50, 0.95):
        heads[q] = LGBMRegressor(alpha=q, **PARAMS).fit(X, y)
        pr = np.full(len(tr), np.nan)
        for k in range(N_FOLDS):
            t, e = fold != k, fold == k
            if e.sum() == 0 or t.sum() < 60:
                continue
            pr[e] = LGBMRegressor(alpha=q, **PARAMS).fit(X[t], y[t]).predict(X[e])
        oof[q] = pr
    cal = pd.DataFrame({"m": tr.index.month, "lo": oof[0.05] - y.to_numpy(),
                        "hi": y.to_numpy() - oof[0.95]}).dropna()
    qq = 1 - ALPHA / 2
    tab = cal.groupby("m")[["lo", "hi"]].quantile(qq)
    glo, ghi = float(cal.lo.quantile(qq)), float(cal.hi.quantile(qq))
    inf = D.dropna(subset=FEATS).copy()
    p05, p50, p95 = (heads[q].predict(inf[FEATS]) for q in (0.05, 0.50, 0.95))
    p05, p95 = np.minimum(p05, p50), np.maximum(p95, p50)
    clo = inf.date.dt.month.map(tab.lo).fillna(glo).to_numpy()
    chi = inf.date.dt.month.map(tab.hi).fillna(ghi).to_numpy()
    base = inf.prior_scaled.to_numpy()
    T = pd.DataFrame({"date": inf.date.to_numpy(), "q50": base + p50,
                      "q05": base + p05 - np.maximum(clo, 0), "q95": base + p95 + np.maximum(chi, 0)})
    obs = tr.a
    tq = T.set_index("date").q50
    fm = ((obs.groupby(obs.index.month).mean() / obs.mean())
          / (tq.groupby(tq.index.month).mean() / tq.mean())).clip(*CLIP_SHARPEN)
    fac = T.date.dt.month.map(fm).fillna(1.0).to_numpy()
    for c in ("q50", "q05", "q95"):
        T[c] = T[c] * fac
    return reanchor(T, ["q50", "q05", "q95"], v_city).set_index("date")


# ── one city x split ────────────────────────────────────────────────────────────────────────
def split_rows(city, st, b0c, drv, v_city, seed):
    rng = np.random.default_rng(seed)                                   # identical to ladder_v2.rungs
    ids = np.array(sorted(st.station_id.unique()))
    rng.shuffle(ids)
    n_hold = max(3, len(ids) // 3)
    held, pool = ids[:n_hold], ids[n_hold:]
    if len(pool) < 2:
        return [], "pool < 2"
    daily = lambda k: st[st.station_id.isin(k)].groupby("date").pm25.mean()
    anchor = daily(pool[:2])
    fr = pd.concat([b0c, daily(held).rename("obs")], axis=1).dropna()
    fr = fr[fr.index <= LAST_DAY]
    fr = fr[fr.index.isin(set(drv.date))].sort_index()
    if len(fr) < 120:
        return [], "scored days < 120"
    cut = fr.index[len(fr) // 2]
    out = []
    for use, fb in (("reconstruction", None), ("prospective", cut)):
        K2 = k2(drv, anchor, v_city, fit_before=fb)
        if K2 is None:
            return [], "anchor days < 120"
        K0 = k0(drv, v_city)
        sel = (lambda j: j[j.index < fb]) if fb is not None else (lambda j: j)
        ja = sel(pd.concat([b0c, anchor.rename("fit")], axis=1).dropna())
        if len(ja) < 30:
            return [], "calibration days < 30"
        a0, a1 = _affine(ja.fit.to_numpy(), ja.bud0.to_numpy())
        f = fr.join(K2[["q50", "q05", "q95"]], how="inner").join(K0.rename("K0"), how="inner")
        pred = {"Bud0": f.bud0.to_numpy(), "Bud0cal2": a0 + a1 * f.bud0.to_numpy(),
                "K0": f.K0.to_numpy(), "K2": f.q50.to_numpy()}
        if len(pool) >= 6:
            x, yt = anchor.rename("x"), daily(pool[2:6]).rename("y")
            j = sel(pd.concat([b0c, x, yt], axis=1).dropna())
            if len(j) > 60:
                A = np.vstack([np.ones(len(j)), j.bud0, j.x]).T
                c, *_ = np.linalg.lstsq(A, j.y.to_numpy(), rcond=None)
                jy = sel(pd.concat([b0c, yt], axis=1).dropna())
                b0_, b1_ = _affine(jy.y.to_numpy(), jy.bud0.to_numpy())
                xs = x.reindex(f.index).to_numpy()
                pred["L2same"] = np.where(np.isfinite(xs), c[0] + c[1] * f.bud0 + c[2] * np.nan_to_num(xs),
                                          b0_ + b1_ * f.bud0)
        sm = np.ones(len(f), bool) if fb is None else (f.index >= fb)
        obs = f.obs.to_numpy()[sm]
        row = {"city": city, "seed": seed, "use": use, "n_days": int(sm.sum())}
        for arm, x in pred.items():
            xs = np.asarray(x)[sm]
            for k, val in L.losses(xs, obs).items():
                row[f"{arm}_{k}"] = val
            row[f"{arm}_r"] = float(np.corrcoef(xs, obs)[0, 1])
            row[f"{arm}_bias"] = float(100 * (xs.mean() - obs.mean()) / obs.mean())
        row["K2_cov90"] = float(((obs >= f.q05.to_numpy()[sm]) & (obs <= f.q95.to_numpy()[sm])).mean())
        out.append(row)
    return out, "ok"


def city_job(args):
    city, st, b0c, drv, v_city, seeds = args
    rows, why = [], {}
    for sd in seeds:
        r, w = split_rows(city, st, b0c, drv, v_city, sd)
        rows += r; why[w] = why.get(w, 0) + 1
    return city, rows, why


# ── summary ─────────────────────────────────────────────────────────────────────────────────
def summarise(C, rng, nboot):
    out = {}
    for col in C.columns:
        if col in ("band", "cluster", "frac_reference", "lat"):
            continue
        s = C[[col, "cluster"]].dropna()
        if len(s) < 4:
            continue
        v, g = s[col].to_numpy(float), s.cluster.astype(str).to_numpy()
        bk = L.boot_cluster(v, g, rng, nboot)
        out[col] = dict(n=int(len(v)), n_clusters=int(len(np.unique(g))), median=float(np.median(v)),
                        cluster=[float(np.percentile(bk, 2.5)), float(np.percentile(bk, 97.5))],
                        positive=int((v > 0).sum()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", type=int, default=21)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--boot", type=int, default=4000)
    a = ap.parse_args()
    t0 = time.time()
    import ladder_v2_confirm as lvc
    frame, meta, conf_cities, dropped = lvc.union("maiac")
    st, p, met, geo_f, sat = frame
    b0 = pd.read_parquet(OUTD / "review_bud0_registered_loco_b5.parquet"); b0["date"] = pd.to_datetime(b0.date)
    g, v = load_priors()
    tag = "kandy_model" + (f"_smoke{a.limit}" if a.limit else "")
    seeds = [SEED] + [SEED + 1000 * (k + 1) for k in range(a.splits - 1)]
    jobs, missing = [], {}
    for c in st:
        if c not in set(b0.city):
            missing[c] = "no Bud0"; continue
        gc, vc = g[g.city == c], v[v.city == c].set_index("year").vand.sort_index()
        if gc.empty or vc.empty:
            missing[c] = "no GEOS-CF or van Donkelaar"; continue
        pc = p[p.city == c][["date"] + list(MET.values())].rename(columns={v_: k for k, v_ in MET.items()})
        drv = gc.merge(pc, on="date", how="inner").sort_values("date").reset_index(drop=True)
        drv["wspd"] = np.hypot(drv.u10, drv.v10)
        doy = drv.date.dt.dayofyear
        drv["sin_doy"] = np.sin(2 * np.pi * doy / 365.25); drv["cos_doy"] = np.cos(2 * np.pi * doy / 365.25)
        drv["dow"] = drv.date.dt.dayofweek
        b0c = b0[b0.city == c].set_index("date").bud0
        jobs.append((c, st[c], b0c, drv, vc, seeds))
    if a.limit:
        jobs = jobs[: a.limit]
    print(f"[{tag}] {len(jobs)} cities to score, {len(missing)} without inputs: {missing}", flush=True)

    rows, why_all = [], {}
    if a.workers > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(a.workers) as ex:
            for i, (c, r, why) in enumerate(ex.map(city_job, jobs)):
                rows += r; why_all[c] = why
                print(f"  {i + 1}/{len(jobs)} {c}: {why} ({time.time() - t0:.0f}s)", flush=True)
    else:
        for i, j in enumerate(jobs):
            c, r, why = city_job(j); rows += r; why_all[c] = why
            print(f"  {i + 1}/{len(jobs)} {c}: {why} ({time.time() - t0:.0f}s)", flush=True)
    S = pd.DataFrame(rows)
    for Ls in ("rmse", "tail", "exceed"):
        for arm in ARMS[1:]:
            S[f"g{arm}_{Ls}"] = 100 * (S[f"Bud0_{Ls}"] - S[f"{arm}_{Ls}"]) / S[f"Bud0_{Ls}"]
        S[f"K2mBud0cal2_{Ls}"] = S[f"gK2_{Ls}"] - S[f"gBud0cal2_{Ls}"]
        S[f"L2samemK2_{Ls}"] = S[f"gL2same_{Ls}"] - S[f"gK2_{Ls}"]
    S = S.replace([np.inf, -np.inf], np.nan)
    tmp = OUTD / f"{tag}_splits.tmp.csv"; S.to_csv(tmp, index=False); os.replace(tmp, OUTD / f"{tag}_splits.csv")

    rng = np.random.default_rng(SEED)
    meta2 = meta[["band", "cluster", "frac_reference", "lat"]]
    res = {"config": vars(a), "spec": "docs/kandy_model_rung_spec_2026-10-10.md", "missing_inputs": missing,
           "eligibility": why_all, "cities_scored": int(S.city.nunique())}
    num = [c for c in S.columns if c not in ("city", "seed", "use")]
    for use in ("reconstruction", "prospective"):
        C = S[S.use == use].groupby("city")[num].median().join(meta2)
        C.to_csv(OUTD / f"{tag}_percity_{use}.csv")
        for scope, keep in (("confirmation", set(conf_cities)), ("union", None)):
            sub = C if keep is None else C[C.index.isin(keep)]
            res[f"{use}.{scope}"] = summarise(sub, rng, a.boot)
    jp = OUTD / f"{tag}_summary.json"; tmp = jp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(res, indent=2, default=str), encoding="utf-8"); os.replace(tmp, jp)
    for k in ("reconstruction.union", "prospective.union", "reconstruction.confirmation"):
        print(f"  {k}")
        for col in ("Bud0_rmse", "K0_rmse", "K2_rmse", "gBud0cal2_rmse", "gK0_rmse", "gK2_rmse", "gL2same_rmse",
                    "K2mBud0cal2_rmse", "L2samemK2_rmse", "Bud0_r", "K2_r", "K2_bias", "K2_cov90"):
            x = res[k].get(col)
            if x:
                print(f"    {col:<18} n={x['n']:>3} {x['median']:+8.3f} [{x['cluster'][0]:+.3f}, "
                      f"{x['cluster'][1]:+.3f}]", flush=True)
    print(f"-> {jp}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
