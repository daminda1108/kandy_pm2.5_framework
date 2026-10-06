"""bud0_learners_kaggle.py -- out-of-city Bud0 predictions from L1 (TabPFN) and L2 (GRU), for
ladder_v2_learners.py. Runs on a Kaggle T4. Settings are those of the registration draft
(docs/prereg_learner_robustness_2026-09-28_DRAFT.md, section 4); nothing here is tuned on the data.

Input : frame_{synthetic|real}.parquet + frame_{...}_columns.json (from ladder_v2_learners.py --export)
Output: pred_{L1|L2}_{tag}.parquet  (city, date, bud0 = median over 5 seeds), plus a run log
Usage : python bud0_learners_kaggle.py --learner L1|L2 --tag synthetic|real --data DIR --out DIR
        [--shard k --n-shards m]   (disjoint subsets of target cities; merged afterwards)
        [--repeat-check]           (refit the first fold twice to report run-to-run agreement)
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

SEEDS = [20260823, 1, 2, 3, 4]          # the confirmed ladder's five learner seeds (ladder_frames.SEED, 1..4)
TABPFN_ROWS = 10_000
WIN = 14


# ── L1 TabPFN ─────────────────────────────────────────────────────────────────────────────
def fit_tabpfn(tr, te, feats, seed):
    import torch
    from tabpfn import TabPFNRegressor
    rng = np.random.default_rng(seed)
    per = TABPFN_ROWS // tr.city.nunique()
    idx = np.concatenate([rng.choice(g.index.to_numpy(), min(per, len(g)), replace=False)
                          for _, g in tr.groupby("city")])
    sub = tr.loc[idx]
    m = TabPFNRegressor(random_state=seed, device="cuda" if torch.cuda.is_available() else "cpu",
                        inference_precision=torch.float32, ignore_pretraining_limits=True)
    m.fit(sub[feats].to_numpy(np.float32), sub.pm25_city.to_numpy(np.float32))
    return m.predict(te[feats].to_numpy(np.float32))


# ── L2 GRU over 14-day windows ────────────────────────────────────────────────────────────
def windows(df, daily, static, mu, sd):
    """For every row: the previous WIN days (t-13..t) of daily features on the city's calendar;
    missing days -> 0 with a missing indicator per feature. Standardised with training stats."""
    X, S, keys = [], [], []
    for c, g in df.groupby("city", sort=False):
        g = g.sort_values("date")
        cal = pd.date_range(g.date.min() - pd.Timedelta(days=WIN - 1), g.date.max(), freq="D")
        D = g.set_index("date")[daily].reindex(cal)
        Z = ((D - mu[daily]) / sd[daily]).to_numpy(np.float32)
        M = np.isnan(Z).astype(np.float32)
        Z = np.nan_to_num(Z)
        pos = cal.get_indexer(g.date)
        for i, pidx in enumerate(pos):
            X.append(np.concatenate([Z[pidx - WIN + 1:pidx + 1], M[pidx - WIN + 1:pidx + 1]], axis=1))
        st = ((g[static].iloc[0] - mu[static]) / sd[static]).fillna(0).to_numpy(np.float32)
        S.append(np.repeat(st[None, :], len(g), axis=0))
        keys.append(g[["city", "date"]])
    return np.stack(X), np.concatenate(S), pd.concat(keys, ignore_index=True)


def fit_gru(tr, te, daily, static, seed, dev):
    import torch
    import torch.nn as nn
    torch.manual_seed(seed); np.random.seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    mu = tr[daily + static].mean(); sd = tr[daily + static].std().replace(0, 1).fillna(1)
    ym, ys = tr.pm25_city.mean(), tr.pm25_city.std()
    rng = np.random.default_rng(seed)
    cities = tr.city.unique()
    val_c = set(rng.choice(cities, max(1, len(cities) // 10), replace=False))   # 10 % of TRAINING cities
    parts = {k: v for k, v in (("fit", tr[~tr.city.isin(val_c)]), ("val", tr[tr.city.isin(val_c)]))}
    data = {}
    for k, d in parts.items():
        X, S, K = windows(d, daily, static, mu, sd)
        y = ((K.merge(d[["city", "date", "pm25_city"]], on=["city", "date"]).pm25_city - ym) / ys)
        data[k] = (torch.tensor(X), torch.tensor(S), torch.tensor(y.to_numpy(np.float32)))
    Xt, St, Kt = windows(te, daily, static, mu, sd)

    class Net(nn.Module):
        def __init__(s, nd, ns):
            super().__init__()
            s.gru = nn.GRU(nd, 64, num_layers=2, batch_first=True)
            s.st = nn.Sequential(nn.Linear(ns, 64), nn.ReLU())
            s.out = nn.Sequential(nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 1))

        def forward(s, x, st):
            h, _ = s.gru(x)
            return s.out(torch.cat([h[:, -1], s.st(st)], 1)).squeeze(1)
    net = Net(data["fit"][0].shape[2], data["fit"][1].shape[1]).to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    best, best_state, bad = np.inf, None, 0
    g = torch.Generator().manual_seed(seed)
    Xf, Sf, yf = data["fit"]
    for ep in range(40):
        net.train()
        perm = torch.randperm(len(yf), generator=g)
        for b in range(0, len(yf), 512):
            i = perm[b:b + 512]
            opt.zero_grad()
            loss = ((net(Xf[i].to(dev), Sf[i].to(dev)) - yf[i].to(dev)) ** 2).mean()
            loss.backward(); opt.step()
        net.eval()
        with torch.no_grad():
            Xv, Sv, yv = data["val"]
            vl = float(((net(Xv.to(dev), Sv.to(dev)) - yv.to(dev)) ** 2).mean())
        if vl < best - 1e-4:
            best, bad = vl, 0
            best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}
        else:
            bad += 1
            if bad >= 5:
                break
    net.load_state_dict(best_state); net.eval()
    with torch.no_grad():
        p = net(torch.tensor(Xt).to(dev), torch.tensor(St).to(dev)).cpu().numpy() * ys + ym
    return Kt.assign(pred=p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--learner", choices=("L1", "L2"), required=True)
    ap.add_argument("--tag", choices=("synthetic", "real"), required=True)
    ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--shard", type=int, default=0); ap.add_argument("--n-shards", type=int, default=1)
    ap.add_argument("--repeat-check", action="store_true")
    a = ap.parse_args()
    import torch
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    if a.learner == "L2":
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    info = {"torch": torch.__version__, "device": dev,
            "gpu": torch.cuda.get_device_name(0) if dev == "cuda" else None}
    if a.learner == "L1":
        import tabpfn
        info["tabpfn"] = tabpfn.__version__
        assert tabpfn.__version__ == "8.5.0", f"registered TabPFN 8.5.0, found {tabpfn.__version__}"
    print(info, flush=True)
    D = Path(a.data)
    p = pd.read_parquet(D / f"frame_{a.tag}.parquet"); p["date"] = pd.to_datetime(p.date)
    p["city"] = p.city.astype(str)
    cols = json.load(open(D / f"frame_{a.tag}_columns.json"))
    daily, static = cols["met"] + cols["sat"], cols["geo"]
    feats = daily + static
    cities = sorted(p.city.unique())
    mine = [c for i, c in enumerate(cities) if i % a.n_shards == a.shard]
    out, t0 = [], time.time()
    for n, c in enumerate(mine):
        tr, te = p[p.city != c], p[p.city == c]
        if len(tr) < 1000 or len(te) < 100:                 # same rule as ladder_frames.fit_loco
            continue
        preds = []
        for s in SEEDS:
            if a.learner == "L1":
                preds.append(fit_tabpfn(tr, te, feats, s))
            else:
                r = fit_gru(tr, te, daily, static, s, dev)
                preds.append(te[["city", "date"]].merge(r, on=["city", "date"], how="left").pred.to_numpy())
        P = np.vstack(preds)
        assert np.isfinite(P).all(), f"non-finite predictions for {c}"
        out.append(pd.DataFrame({"city": c, "date": te.date.values, "bud0": np.median(P, axis=0),
                                 **{f"seed{k}": P[k] for k in range(len(SEEDS))}}))
        print(f"  [{n + 1}/{len(mine)}] {c}: {len(te)} days ({time.time() - t0:.0f} s)", flush=True)
        if a.repeat_check and n == 0:
            again = (fit_tabpfn(tr, te, feats, SEEDS[0]) if a.learner == "L1" else
                     te[["city", "date"]].merge(fit_gru(tr, te, daily, static, SEEDS[0], dev),
                                                on=["city", "date"]).pred.to_numpy())
            info["repeat_check_max_abs_diff"] = float(np.max(np.abs(again - P[0])))
            print(f"  repeat check, max |diff| = {info['repeat_check_max_abs_diff']:.3g}", flush=True)
        o = Path(a.out); o.mkdir(parents=True, exist_ok=True)
        pd.concat(out, ignore_index=True).to_parquet(
            o / f"pred_{a.learner}_{a.tag}_shard{a.shard}.parquet", index=False)
    json.dump(info, open(Path(a.out) / f"info_{a.learner}_{a.tag}_shard{a.shard}.json", "w"), indent=1)
    print("done", flush=True)


if __name__ == "__main__":
    main()
