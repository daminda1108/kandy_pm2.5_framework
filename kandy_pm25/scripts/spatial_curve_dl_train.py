"""spatial_curve_dl_train.py -- deep arm E11 (TNP-D) and the registered deep positive control.

OSF amendment 26hp8. E10 (ConvGNP, deepsensor) is added to this file once E11 is proven; the two
share the task sampler, the scalers and the evaluator, so they differ in architecture alone.

MODEL. TNP-D (Nguyen & Grover, ICML 2022), vendored from the authors' MIT-licensed code with three
documented, behaviour-preserving adaptations (src/vendor/tnp_pytorch/ADAPTATIONS.md), at the
authors' own defaults: d_model 64, emb_depth 4, feed-forward 128, 4 heads, dropout 0, 6 layers.

INPUT PER POINT: x_km/10, y_km/10 and the seven registered covariates, standardised with a scaler
fitted on the TRAINING folds only. TARGET: PM2.5, standardised per task with the CONTEXT's own mean
and spread, and unstandardised for scoring. Nothing about a held-out site enters its own scaling.

TRAINING TASKS, exactly as registered (amendment Section 3): a training-fold city and day, k drawn
from the registered sizes the day supports, k present sites as context and ALL the remaining
present sites as targets. The tasks in one batch share the city-day and k, so their target counts
match and they stack with no padding. (A first version kept a fixed 10 targets per task for
batching; it was corrected before any registered run.)

POSITIVE CONTROL (registered, Section 3 of the amendment): synthetic cities, each an exponential
Gaussian random field with its own KNOWN correlation length. Train on some, score on unseen ones,
and compare against ORACLE kriging given each test city's true variogram, on identical splits. The
arm must come within 0.05 of the oracle at 35 context sites, or it is reported as a failure to
train and its real-data results are not interpreted.

Usage:
  python scripts/spatial_curve_dl_train.py control --steps 300              # local smoke
  python scripts/spatial_curve_dl_train.py control --steps 40000 --device cuda
  python scripts/spatial_curve_dl_train.py real --fold 0 --seed 0 --steps 40000 --device cuda
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src.vendor.tnp_pytorch._attrdict import AttrDict                      # noqa: E402
from src.vendor.tnp_pytorch.tnpd import TNPD                               # noqa: E402

import os                                                                   # noqa: E402
SC = REPO / "data" / "processed" / "modular" / "spatial_curve"
# Overridable so the same code runs on Kaggle, where the repo is read-only and outputs go to
# /kaggle/working. Unset, both default to the project's own directories.
DL = Path(os.environ.get("SPATIAL_DL_DATA", SC / "dl"))
OUT = Path(os.environ.get("SPATIAL_DL_OUT", SC / "dl_out"))
COVARS = ["lc_built_2400", "lc_built_300", "ntl_1000", "pop_1000", "ndvi_1000",
          "road_major_300", "dist_major_km"]
KS = (3, 5, 8, 12, 18, 25, 35, 50, 70)
N_MIN_TARGETS = 5                # a task keeps at least this many targets
N_TARGETS = N_MIN_TARGETS        # legacy name, still imported by the E10 module
BATCH = 16
LR = 5e-4
TNPD_HP = dict(d_model=64, emb_depth=4, dim_feedforward=128, nhead=4, dropout=0.0,
               num_layers=6, bound_std=True)
CONTROL_PASS_MARGIN = 0.05
CONTROL_K = 35


# ── model plumbing ────────────────────────────────────────────────────────────────────────────
def make_model(dim_x: int, device: str) -> TNPD:
    return TNPD(dim_x=dim_x, dim_y=1, **TNPD_HP).to(device)


def task_tensors(Xc, yc, Xt, yt, device):
    """One task. y standardised by the CONTEXT's mean and spread only."""
    mu, sd = float(np.mean(yc)), float(np.std(yc)) or 1.0
    t = lambda a: torch.as_tensor(np.asarray(a, np.float32), device=device)
    b = AttrDict(xc=t(Xc)[None], yc=t((yc - mu) / sd)[None, :, None],
                 xt=t(Xt)[None], yt=t((yt - mu) / sd)[None, :, None])
    return b, mu, sd


def stack(tasks):
    """Batch tasks that share k and N_TARGETS."""
    return AttrDict(**{key: torch.cat([b[key] for b in tasks], 0) for key in ("xc", "yc", "xt", "yt")})


def train(model, sample_task, steps, device, log_every=100):
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps)
    model.train()
    t0 = time.time()
    for step in range(1, steps + 1):
        tasks = sample_task(BATCH)
        loss = model(stack(tasks)).loss
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % log_every == 0 or step == steps:
            print(f"  step {step:6d}/{steps} | loss {float(loss.detach()):.4f} | "
                  f"{(time.time() - t0) / 60:.1f} min", flush=True)
    model.eval()
    return model


@torch.no_grad()
def predict(model, Xc, yc, Xt, device):
    b, mu, sd = task_tensors(Xc, yc, Xt, np.zeros(len(Xt)), device)
    return model.predict(b.xc, b.yc, b.xt).mean[0, :, 0].cpu().numpy() * sd + mu


def srho(p, o):
    if not np.all(np.isfinite(p)) or np.std(p) < 1e-12 or np.std(o) < 1e-12:
        return np.nan
    return float(spearmanr(p, o).statistic)


# ── positive control ──────────────────────────────────────────────────────────────────────────
def synthetic_cities(n_cities, n_sites, days, seed, informative=False):
    """Each city: its own correlation length (known), fixed sites and covariates, `days`
    independent field realisations. y = 25 + 5 * field.

    PRIMARY CONTROL (informative=False): every covariate is pure noise, so the only route to the
    oracle is to learn spatial interpolation from the context sites. DIAGNOSTIC
    (informative=True): the first covariate carries the field plus noise, as in the analysis
    script's positive control. A model can then approach the oracle through that covariate alone,
    which is why this variant cannot serve as the registered control."""
    import gstools as gs
    rng = np.random.default_rng(seed)
    out = []
    for c in range(n_cities):
        ls = float(rng.uniform(2.0, 6.0))
        xy = rng.random((n_sites, 2)) * 20.0
        model = gs.Exponential(dim=2, var=1.0, len_scale=ls)
        fields = np.stack([gs.SRF(model, seed=int(rng.integers(1 << 30)))((xy[:, 0], xy[:, 1]))
                           for _ in range(days)])
        cov = rng.normal(0, 1, (n_sites, len(COVARS)))
        if informative:        # diagnostic only: lets a model reach the oracle through a covariate
            cov[:, 0] = fields.mean(0) + rng.normal(0, 1.0, n_sites)
        out.append(dict(xy=xy, cov=cov, y=25 + 5 * fields, len_scale=ls))
    return out


def synth_X(city, mu, sd):
    return np.c_[city["xy"] / 10.0, (city["cov"] - mu) / sd]


def run_control(a):
    dev = a.device
    torch.manual_seed(a.seed)
    inf = a.control_covariates == "informative"
    tr = synthetic_cities(a.train_cities, 60, a.days, seed=1000 + a.seed, informative=inf)
    te = synthetic_cities(a.test_cities, 60, 1, seed=9000, informative=inf)
    allcov = np.concatenate([c["cov"] for c in tr])
    mu, sd = allcov.mean(0), allcov.std(0) + 1e-9               # fitted on TRAINING cities
    rng = np.random.default_rng(a.seed)

    def sample(B):
        # registered sampler: one city-day, k context sites, ALL remaining sites as targets
        k = int(rng.choice([k for k in KS if k <= 60 - N_MIN_TARGETS]))
        c = tr[int(rng.integers(len(tr)))]
        d = int(rng.integers(c["y"].shape[0]))
        X = synth_X(c, mu, sd)
        tasks = []
        for _ in range(B):
            perm = rng.permutation(60)
            C, T = perm[:k], perm[k:]
            tasks.append(task_tensors(X[C], c["y"][d, C], X[T], c["y"][d, T], dev)[0])
        return tasks

    model = train(make_model(2 + len(COVARS), dev), sample, a.steps, dev)

    from pykrige.ok import OrdinaryKriging
    res = []
    for ci, c in enumerate(te):
        X = synth_X(c, mu, sd)
        y = c["y"][0]
        for rep in range(10):
            r2 = np.random.default_rng([ci, rep])
            T = r2.choice(60, 20, replace=False)
            P = np.setdiff1d(np.arange(60), T)
            F = r2.permutation(P)[:CONTROL_K]
            p_nn = predict(model, X[F], y[F], X[T], dev)
            ok = OrdinaryKriging(c["xy"][F, 0], c["xy"][F, 1], y[F], variogram_model="exponential",
                                 variogram_parameters=[25.0, 3.0 * c["len_scale"], 0.0],
                                 enable_plotting=False, verbose=False)
            p_or = np.asarray(ok.execute("points", c["xy"][T, 0], c["xy"][T, 1])[0])
            res.append(dict(city=ci, rep=rep, tnpd=srho(p_nn, y[T]), oracle=srho(p_or, y[T])))
    R = pd.DataFrame(res)
    med_nn, med_or = float(R.tnpd.median()), float(R.oracle.median())
    passed = med_nn >= med_or - CONTROL_PASS_MARGIN
    summary = dict(arm="E11 TNP-D", control_covariates=a.control_covariates,
                   primary_control=(a.control_covariates == "noise"), steps=a.steps, train_cities=a.train_cities, days=a.days,
                   test_cities=a.test_cities, k=CONTROL_K, median_rho_tnpd=round(med_nn, 4),
                   median_rho_oracle=round(med_or, 4), margin=CONTROL_PASS_MARGIN,
                   passed=bool(passed), seed=a.seed, device=dev)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"control_tnpd_{a.control_covariates}_seed{a.seed}_steps{a.steps}.json").write_text(
        json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0 if passed else 5


# ── real data ─────────────────────────────────────────────────────────────────────────────────
def run_real(a):
    dev = a.device
    torch.manual_seed(a.seed)
    S = pd.read_parquet(DL / "sites.parquet").drop_duplicates("site").set_index("site")
    D = pd.read_parquet(DL / "daily.parquet").drop_duplicates(["site", "day"])
    train_sites = S[(S.fold != a.fold) & S.cov_complete]
    mu = train_sites[COVARS].to_numpy(float).mean(0)
    sd = train_sites[COVARS].to_numpy(float).std(0) + 1e-9      # TRAINING folds only

    def feats(idx):
        s = S.loc[idx]
        return np.c_[s[["x_km", "y_km"]].to_numpy(float) / 10.0,
                     (s[COVARS].to_numpy(float) - mu) / sd]

    Dtr = D[D.site.isin(train_sites.index)]
    by_cd = {key: g for key, g in Dtr.groupby(["cluster", "day"])}
    keys = [key for key, g in by_cd.items() if len(g) >= 3 + N_MIN_TARGETS]
    rng = np.random.default_rng(a.seed)
    print(f"fold {a.fold}: {train_sites.cluster.nunique()} training cities, "
          f"{len(keys):,} usable city-days", flush=True)

    def sample(B):
        # registered sampler: one city-day, k present sites as context, ALL the remaining present
        # sites as targets; the B tasks share the city-day and k, so they stack exactly
        g = by_cd[keys[int(rng.integers(len(keys)))]]
        k = int(rng.choice([kk for kk in KS if kk <= len(g) - N_MIN_TARGETS]))
        F, v = feats(g.site), g.pm25.to_numpy(float)
        tasks = []
        for _ in range(B):
            perm = rng.permutation(len(g))
            C, T = perm[:k], perm[k:]
            tasks.append(task_tensors(F[C], v[C], F[T], v[T], dev)[0])
        return tasks

    model = train(make_model(2 + len(COVARS), dev), sample, a.steps, dev)
    OUT.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), OUT / f"tnpd_fold{a.fold}_seed{a.seed}.pt")

    rows = []
    test_clusters = set(S[S.fold == a.fold].cluster)
    static = pd.read_parquet(DL / "static.parquet")
    for frame, sub in (("registered", "analysis"), ("s70", "analysis_s70")):
        f1 = DL / f"{sub}_splits_q1_primary.parquet"
        if f1.exists():
            st = static[static.frame == frame].drop_duplicates("site").set_index("site").static_mean
            for r in pd.read_parquet(f1).itertuples():
                if r.cluster not in test_clusters:
                    continue
                F, T = r.fit.split("|"), r.held.split("|")
                p = predict(model, feats(F), st.loc[F].to_numpy(float), feats(T), dev)
                rows.append(dict(frame=frame, design="Q1", cluster=r.cluster, rep=r.rep, k=r.k,
                                 day=-1, est="E11", rho=srho(p, st.loc[T].to_numpy(float))))
        f2 = DL / f"{sub}_splits_q2.parquet"
        if f2.exists():
            Dd = D.set_index(["site", "day"]).pm25
            for r in pd.read_parquet(f2).itertuples():
                if r.cluster not in test_clusters:
                    continue
                Fk, T = r.fit.split("|"), r.held.split("|")
                for pos, day in enumerate(r.days.split("|")):
                    dts = pd.Timestamp(day, tz="UTC")
                    vF = pd.Series({s: Dd.get((s, dts), np.nan) for s in Fk}).dropna()
                    vT = np.array([Dd.get((s, dts), np.nan) for s in T], float)
                    if len(vF) < 3 or not np.all(np.isfinite(vT)):
                        continue
                    p = predict(model, feats(vF.index), vF.to_numpy(float), feats(T), dev)
                    rows.append(dict(frame=frame, design="Q2", cluster=r.cluster, rep=r.rep, k=r.k,
                                     day=pos, est="E11", rho=srho(p, vT)))
    out = pd.DataFrame(rows)
    out["fold"], out["seed"] = a.fold, a.seed
    out.to_parquet(OUT / f"pred_tnpd_fold{a.fold}_seed{a.seed}.parquet", index=False)
    print(f"scored {len(out):,} task(s) on fold {a.fold}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["control", "real"])
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--fold", type=int, default=0)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--train-cities", type=int, default=200)
    ap.add_argument("--test-cities", type=int, default=30)
    ap.add_argument("--days", type=int, default=20)
    ap.add_argument("--control-covariates", choices=["noise", "informative"], default="noise",
                    help="noise is the primary control: covariates carry NO field information, "
                         "so matching oracle kriging requires learning interpolation from context")
    a = ap.parse_args()
    return run_control(a) if a.mode == "control" else run_real(a)


if __name__ == "__main__":
    sys.exit(main())
