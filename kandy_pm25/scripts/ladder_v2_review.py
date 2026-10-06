"""ladder_v2_review.py -- EXPLORATORY arms answering the 2026-10-06 external review (R1, R3, R4, R5).

Plan: docs/review_remediation_plan_2026-10-06.md, steps L1-L3. Nothing here is registered; the frozen
modules (ladder_v2, ladder_v2_confirm, ladder_frames) are imported and never edited.

The registered ladder uses the first two / six stations only to fit an intercept and slope to Bud0
(their reading never enters that day's prediction) but uses the background's SAME-DAY reading, and
from more stations. This script puts the streams on equal terms. For every city x split, with the
registered shuffle (held-out set and pool identical to ladder_v2.rungs):

    local  = pool[0:2]      target = pool[2:6]      reg = pool[6:]      reg2 = pool[6:8]

and each arm X regresses the daily mean of `target` on (1, Bud0, x_t), predicts the held-out mean,
falls back to the affine Bud0 map on days x_t is missing, and is shrunk toward Bud0 with a weight
cross-fitted from the other cities (as E3):

    L2s    x = daily mean of `local`            (first two stations, same-day)
    BGall  x = daily P10 of `reg`               (registered background construction)
    BG2    x = daily P10 of `reg2`              (background from two stations: count-matched)
    M2     x = daily mean of `reg2`             (two non-local stations as a mean: type-matched to L2s)

Arms: reconstruction (coefficients over the scored period) and SYMMETRIC prospective (coefficients on the
earlier half, every stream keeps reporting, later half scored). The registered chain is recomputed on the
same city x split for parity with ueyfr (registered union) and for a like-for-like subset comparison.
Needs pool >= 8 (cities with >= 12 stations).

--bud0 lono   Bud0 fitted leave-one-NETWORK-out (cluster as in the bootstrap) instead of leave-one-city-out (R5).
--frame full  the full-network mirror of test A (mhgna) instead of the registered union.

Usage: python scripts/ladder_v2_review.py [--frame registered|full] [--bud0 loco|lono] [--splits 21]
       [--bag 5] [--boot 4000] [--limit K]
Out:   data/processed/modular/ladder_v2/review_{frame}_{bud0}_{splits,percity_*,summary}.*
"""
from __future__ import annotations

import argparse
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
from src.modular import shrinkage as sh                                 # noqa: E402

OUTD = L.OUTD
ARMS = ("L2s", "BGall", "BG2", "M2")
LOSSES = ("rmse", "tail", "exceed")
FN = REPO / "data" / "processed" / "modular" / "fullnet"


# ── Bud0 ────────────────────────────────────────────────────────────────────────────────────
def bud0_lono(p, feats, bag, meta):
    """Leave-one-NETWORK-out: the scored city's whole cluster is removed from training."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    cl = p.city.map(meta.cluster.astype(str))
    assert cl.notna().all(), "cluster missing for some cities"
    preds = []
    for k in range(bag):
        seed = SEED if k == 0 else k
        out = []
        for g in sorted(cl.unique()):
            tr, te = p[cl != g], p[cl == g]
            if len(tr) < 1000 or len(te) < 100:
                continue
            m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, random_state=seed)
            m.fit(tr[feats], tr.pm25_city)
            out.append(pd.DataFrame({"city": te.city.values, "date": te.date.values,
                                     "bud0": m.predict(te[feats])}))
        d = pd.concat(out, ignore_index=True).sort_values(["city", "date"]).reset_index(drop=True)
        preds.append(d)
        print(f"    Bud0 LONO seed {k}: {d.city.nunique()} cities, {cl.nunique()} networks", flush=True)
    b0 = preds[0][["city", "date"]].copy()
    for d in preds[1:]:
        assert (d[["city", "date"]].to_numpy() == b0[["city", "date"]].to_numpy()).all()
    b0["bud0"] = np.median(np.vstack([d.bud0.to_numpy() for d in preds]), axis=0)
    return b0


# ── symmetric arms, one city x split ────────────────────────────────────────────────────────
def sym(city, st, bud0, seed, calib_before=None):
    rng = np.random.default_rng(seed)                          # identical to ladder_v2.rungs
    ids = np.array(sorted(st.station_id.unique()))
    rng.shuffle(ids)
    n_hold = max(3, len(ids) // 3)
    held, pool = ids[:n_hold], ids[n_hold:]
    if len(pool) < 8:
        return None
    local, tgt, reg, reg2 = pool[:2], pool[2:6], pool[6:], pool[6:8]
    daily = lambda k: st[st.station_id.isin(k)].groupby("date").pm25.mean()
    p10 = lambda k: st[st.station_id.isin(k)].groupby("date").pm25.quantile(0.10)
    p0 = bud0[bud0.city == city].set_index("date").bud0
    fr = pd.concat([p0, daily(held).rename("obs")], axis=1).dropna().sort_index()
    if len(fr) < 120:
        return None
    sel = (lambda j: j[j.index < calib_before]) if calib_before is not None else (lambda j: j)
    y = daily(tgt).rename("y")
    ja = sel(pd.concat([p0, y], axis=1).dropna())
    a0, a1 = _affine(ja.y.to_numpy(), ja.bud0.to_numpy())
    aff = a0 + a1 * fr.bud0.to_numpy()
    pred = {"Bud0": fr.bud0.to_numpy()}
    for arm, x in (("L2s", daily(local)), ("BGall", p10(reg)), ("BG2", p10(reg2)), ("M2", daily(reg2))):
        j = sel(pd.concat([p0, x.rename("x"), y], axis=1).dropna())
        if len(j) <= 60:
            continue
        A = np.vstack([np.ones(len(j)), j.bud0.to_numpy(), j.x.to_numpy()]).T
        c, *_ = np.linalg.lstsq(A, j.y.to_numpy(), rcond=None)
        xs = x.reindex(fr.index).to_numpy()
        pr = c[0] + c[1] * fr.bud0.to_numpy() + c[2] * np.nan_to_num(xs)
        pred[arm] = np.where(np.isfinite(xs), pr, aff)
        pred[f"cov_{arm}"] = float(np.isfinite(xs).mean())
    return fr, pred


def own_w(fr, pred, seed):
    obs = fr.obs.to_numpy(); days = fr.index.astype(str).to_numpy()
    return {a: sh.optimal_weight(pred["Bud0"], pred[a], obs, groups=days, seed=seed).w
            for a in ARMS if a in pred}


def score_arms(fr, pred, w, score=None):
    obs = fr.obs.to_numpy()
    sm = np.ones(len(obs), bool) if score is None else score
    row = {f"Bud0_{k}": v for k, v in L.losses(pred["Bud0"][sm], obs[sm]).items()}
    for a in ARMS:
        if a not in pred or not np.isfinite(w.get(a, np.nan)):
            row.update({f"{a}_{k}": np.nan for k in LOSSES}); continue
        x = sh.combine(pred["Bud0"], pred[a], float(w[a]))
        row.update({f"{a}_{k}": v for k, v in L.losses(x[sm], obs[sm]).items()})
        row[f"w_{a}"] = float(w[a]); row[f"cov_{a}"] = pred[f"cov_{a}"]
    return row


def effects(d):
    for Ls in LOSSES:
        gain = lambda a: 100 * (d[f"Bud0_{Ls}"] - d[f"{a}_{Ls}"]) / d[f"Bud0_{Ls}"]
        for a in ARMS:
            d[f"g{a}_{Ls}"] = gain(a)
        d[f"BGallmL2s_{Ls}"] = d[f"gBGall_{Ls}"] - d[f"gL2s_{Ls}"]
        d[f"BG2mL2s_{Ls}"] = d[f"gBG2_{Ls}"] - d[f"gL2s_{Ls}"]
        d[f"M2mL2s_{Ls}"] = d[f"gM2_{Ls}"] - d[f"gL2s_{Ls}"]
        d[f"BGallmBG2_{Ls}"] = d[f"gBGall_{Ls}"] - d[f"gBG2_{Ls}"]
    return d.replace([np.inf, -np.inf], np.nan)


def summarise(C, rng, nboot, cols):
    out = {}
    for col in cols:
        s = C[[col, "cluster"]].dropna()
        if len(s) < 4:
            continue
        v, g = s[col].to_numpy(), s.cluster.astype(str).to_numpy()
        bk = L.boot_cluster(v, g, rng, nboot)
        out[col] = dict(n=int(len(v)), n_clusters=int(len(np.unique(g))), median=float(np.median(v)),
                        cluster=[float(np.percentile(bk, 2.5)), float(np.percentile(bk, 97.5))],
                        positive=int((v > 0).sum()))
    return out


# ── main ────────────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", choices=["registered", "full"], default="registered")
    ap.add_argument("--bud0", choices=["loco", "lono"], default="loco")
    ap.add_argument("--splits", type=int, default=21)
    ap.add_argument("--bag", type=int, default=5)
    ap.add_argument("--boot", type=int, default=4000)
    ap.add_argument("--limit", type=int, default=0, help="smoke test: first K eligible cities")
    a = ap.parse_args()
    t0 = time.time()
    if a.frame == "full":
        import ladder_v2_fullnet as lf
        lf._point(FN / "mirror_full")
    import ladder_v2_confirm as lvc
    frame, meta, conf_cities, dropped = lvc.union("maiac")
    st, p, met, geo_f, sat = frame
    feats = met + geo_f + sat
    tag = f"review_{a.frame}_{a.bud0}" + (f"_smoke{a.limit}" if a.limit else "")
    print(f"[{tag}] union {len(st)} cities, confirmation {len(conf_cities)}", flush=True)

    cache = OUTD / f"review_bud0_{a.frame}_{a.bud0}_b{a.bag}.parquet"
    if cache.exists() and not a.limit:
        b0 = pd.read_parquet(cache); b0["date"] = pd.to_datetime(b0.date)
        print(f"  Bud0 from cache {cache.name}", flush=True)
    else:
        b0 = L.bagged_bud0(p, feats, a.bag) if a.bud0 == "loco" else bud0_lono(p, feats, a.bag, meta)
        if not a.limit:
            tmp = cache.with_suffix(".tmp.parquet"); b0.to_parquet(tmp); os.replace(tmp, cache)
    print(f"  Bud0 ready ({time.time() - t0:.0f}s)", flush=True)

    seeds = [SEED] + [SEED + 1000 * (k + 1) for k in range(a.splits - 1)]
    cities = [c for c in st if c in set(b0.city)]
    if a.limit:
        cities = [c for c in cities if st[c].station_id.nunique() >= 12][: a.limit]

    # pass 1: raw predictions; own weights (registered chain and symmetric arms)
    reg_cache, sym_cache, w_reg, w_sym = {}, {}, [], []
    for i, c in enumerate(cities):
        for sd in seeds:
            rr = L.rungs(c, st[c], b0, sd)
            if rr is not None:
                reg_cache[(c, sd)] = rr
                row = L.chain(*rr, sd, "cv")
                w_reg.append({"city": c, **{r: row[f"w_{r}"] for r in L.RUNGS}})
            ss = sym(c, st[c], b0, sd)
            if ss is not None:
                sym_cache[(c, sd)] = ss
                w_sym.append({"city": c, **own_w(*ss, sd)})
        if i % 20 == 0:
            print(f"  pass1 {i + 1}/{len(cities)} ({time.time() - t0:.0f}s)", flush=True)
    Wr = pd.DataFrame(w_reg).set_index("city")
    Ws = pd.DataFrame(w_sym).set_index("city") if w_sym else None

    rows = []
    for (c, sd), (fr, pred) in reg_cache.items():
        wg = Wr.drop(index=c, errors="ignore").median()
        rows.append({"city": c, "seed": sd, "arm": "reconstruction", "set": "registered",
                     **L.chain(fr, pred, sd, "crossfit", w_given=wg)})
    for (c, sd), (fr, pred) in sym_cache.items():
        wg = Ws.drop(index=c, errors="ignore").median().to_dict()
        rows.append({"city": c, "seed": sd, "arm": "reconstruction", "set": "symmetric",
                     **score_arms(fr, pred, wg)})
        cut = fr.index[len(fr) // 2]
        sp = sym(c, st[c], b0, sd, calib_before=cut)
        if sp is not None:
            fr2, pred2 = sp
            rows.append({"city": c, "seed": sd, "arm": "prospective", "set": "symmetric",
                         **score_arms(fr2, pred2, wg, score=(fr2.index >= cut))})
    S = pd.DataFrame(rows)
    R = L.add_effects(S[S.set == "registered"].copy())
    Y = effects(S[S.set == "symmetric"].copy())
    S2 = pd.concat([R, Y], ignore_index=True)
    S2.to_csv(OUTD / f"{tag}_splits.csv", index=False)

    rng = np.random.default_rng(SEED)
    meta2 = meta[["band", "cluster", "frac_reference", "lat"]]
    res = {"config": vars(a), "dropped": dropped, "cities_union": len(cities)}
    reg_cols = [f"{e}_{Ls}" for e in ("first2", "s36", "bg", "bgm2") for Ls in LOSSES]
    sym_cols = [f"{e}_{Ls}" for e in ([f"g{x}" for x in ARMS] +
                ["BGallmL2s", "BG2mL2s", "M2mL2s", "BGallmBG2"]) for Ls in LOSSES]
    Cr = R.groupby("city")[reg_cols].median().join(meta2)
    sym_cities = set(Y.city)
    for arm in ("reconstruction", "prospective"):
        Cy = Y[Y.arm == arm].groupby("city")[sym_cols + [f"cov_{x}" for x in ARMS]].median().join(meta2)
        Cy.to_csv(OUTD / f"{tag}_percity_symmetric_{arm}.csv")
        for scope, keep in (("confirmation", set(conf_cities)), ("union", None)):
            sub = Cy if keep is None else Cy[Cy.index.isin(keep)]
            res[f"{arm}.{scope}.symmetric"] = summarise(sub, rng, a.boot, sym_cols)
    Cr.to_csv(OUTD / f"{tag}_percity_registered.csv")
    for scope, keep in (("confirmation", set(conf_cities)), ("union", None)):
        sub = Cr if keep is None else Cr[Cr.index.isin(keep)]
        res[f"reconstruction.{scope}.registered_all"] = summarise(sub, rng, a.boot, reg_cols)
        res[f"reconstruction.{scope}.registered_samecities"] = summarise(
            sub[sub.index.isin(sym_cities)], rng, a.boot, reg_cols)

    # parity with ueyfr (registered union, LOCO, full splits only)
    if a.frame == "registered" and a.bud0 == "loco" and a.splits == 21 and a.bag == 5 and not a.limit:
        U = pd.read_csv(OUTD / "confirm_REGISTERED_percity_reconstruction.csv", index_col=0)
        common = [c for c in U.index if c in Cr.index]
        cols = [c for c in reg_cols if c in U.columns]
        diff = float((Cr.loc[common, cols] - U.loc[common, cols]).abs().max().max())
        res["parity_vs_ueyfr"] = dict(cities=[len(common), len(U)], max_abs_diff=diff)
        print(f"  PARITY vs ueyfr: {len(common)}/{len(U)} cities, max |diff| {diff:.3g}", flush=True)

    jp = OUTD / f"{tag}_summary.json"; tmp = jp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(res, indent=2, default=str), encoding="utf-8"); os.replace(tmp, jp)
    for k in ("reconstruction.confirmation.symmetric", "reconstruction.union.symmetric",
              "prospective.union.symmetric"):
        print(f"  {k}")
        for col in ("gL2s_rmse", "gBGall_rmse", "gBG2_rmse", "gM2_rmse", "BGallmL2s_rmse",
                    "BG2mL2s_rmse", "M2mL2s_rmse", "BGallmL2s_exceed"):
            v = res[k].get(col)
            if v:
                print(f"    {col:<18} n={v['n']:>3} {v['median']:+7.2f} [{v['cluster'][0]:+.2f}, "
                      f"{v['cluster'][1]:+.2f}]", flush=True)
    for k in ("reconstruction.union.registered_samecities", "reconstruction.confirmation.registered_all"):
        v = res[k]
        if "bgm2_rmse" not in v or "first2_rmse" not in v:
            continue
        print(f"  {k}: first2 {v['first2_rmse']['median']:+.2f}  bg {v['bg_rmse']['median']:+.2f}  "
              f"bgm2 {v['bgm2_rmse']['median']:+.2f} (n {v['bgm2_rmse']['n']})", flush=True)
    print(f"-> {jp}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
