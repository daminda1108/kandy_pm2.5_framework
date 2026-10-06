"""spatial_curve_dl_convgnp.py -- deep arm E10: a convolutional Gaussian neural process.

OSF amendment 26hp8. deepsensor's ConvNP with likelihood="gnp", trained ACROSS cities and applied
to an unseen city conditioned on its k fitting sites. E10 shares the task design, the splits and
the positive control with E11 (spatial_curve_dl_train.py), so the two differ in architecture only.

CONSTRUCTION, verified by probe on 2026-09-11 before any real data were used:
  * deepsensor requires at least one GRIDDED input: a context of point frames alone fails in its
    coordinate normalisation. Context set 1 is therefore a raster of the benchmark covariate
    (built-up land cover within 2.4 km) over the city.
  * Context set 2 is the fitting sites, carrying PM2.5 and the seven covariates as columns.
  * The target set is the held-out sites. Covariates at held-out sites reach E10 only through the
    gridded channel, because target sites carry no inputs of their own.
  * Each split gets its own context and target FRAMES, sampled "all". Exact-coordinate sampling
    was probed first and rejected: it demands a bit-exact float match against the loader's index.

A LEAK THE PROJECT'S EARLIER CONVCNP HAD, CLOSED HERE. src/stage3_pinn/training/train_convcnp.py
fits each city's DataProcessor on the context AND target frames, so a held-out city's PM2.5
normalisation was computed partly from the values being predicted. Here every task's processor is
fitted on the grid and the CONTEXT sites only, and the targets are mapped through it: the same
rule as E11's context-only standardisation.

SCORING needs no un-normalisation. Every estimator is scored by Spearman correlation, which is
invariant to the affine map deepsensor applies, so E10's mean is read in normalised space. That
also avoids a second trap: ConvNP.predict un-normalises with the processor the MODEL was built
with (the reference city's), not the split's own.

Usage:
  python scripts/spatial_curve_dl_convgnp.py control --steps 200 --device cpu        # smoke
  python scripts/spatial_curve_dl_convgnp.py real --fold 0 --seed 0 --steps 20000
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import spatial_curve_dl_train as base                                       # noqa: E402

import deepsensor.torch                                                     # noqa: E402,F401
from deepsensor.data import DataProcessor, TaskLoader                      # noqa: E402
from deepsensor.model import ConvNP                                        # noqa: E402

COVARS, KS, N_TARGETS = base.COVARS, base.KS, base.N_TARGETS
LR = 5e-5                        # deepsensor's own Trainer default
BATCH = 8                        # tasks per step, loss averaged (loss_fn takes one task)
INTERNAL_DENSITY = 100
GRID_N = 24
PSEUDO_TIME = pd.Timestamp("2000-01-01")   # static window means as a single time slice


# ── frames ────────────────────────────────────────────────────────────────────────────────────
def station_frame(lat, lon, pm25, cov=None, time=PSEUDO_TIME):
    d = {"time": time, "lat": np.asarray(lat, float), "lon": np.asarray(lon, float),
         "pm25": np.asarray(pm25, float)}
    if cov is not None:
        for j, c in enumerate(COVARS):
            d[c] = np.asarray(cov, float)[:, j]
    return pd.DataFrame(d).set_index(["time", "lat", "lon"]).sort_index()


DYADIC = 2.0 ** -12              # coordinate maps are exact multiples of this


def square_maps(aux):
    """Equal-length lat and lon ranges covering the grid, in exactly representable numbers.

    deepsensor normalises both coordinates by ONE scale, so it requires x1_map and x2_map to have
    identical ranges, and it tests that with exact float equality. When they differ it tries to
    raise, and its own error message then crashes with "only 0-dimensional arrays can be converted
    to Python scalars": the misleading error behind every failed probe of 2026-09-11, including
    the first E10 smoke run. A box built naively from a centre and a half-width can still fail on
    rounding, so both ranges are snapped to multiples of 2**-12, where the subtraction is exact.
    """
    la, lo = np.asarray(aux["lat"], float), np.asarray(aux["lon"], float)
    w = np.ceil(max(np.ptp(la), np.ptp(lo)) / DYADIC + 2) * DYADIC
    a = np.floor(((la.min() + la.max()) / 2 - w / 2) / DYADIC) * DYADIC
    b = np.floor(((lo.min() + lo.max()) / 2 - w / 2) / DYADIC) * DYADIC
    x1, x2 = (float(a), float(a + w)), (float(b), float(b + w))
    assert np.diff(x1) == np.diff(x2), "square maps not exactly equal"
    return x1, x2


SD_FLOOR = 1e-12


def preset_norm(dp, frames):
    """Register every variable's mean/std on `dp` BEFORE it maps anything, with the spread floored.

    deepsensor divides by the std of whatever it is fitted on. With k = 3 context sites a covariate
    can be identical at all three (no major road within 300 m of any of them), and the division
    raises ZeroDivisionError: the E10 smoke run of 2026-09-11 died exactly there. The rule is E2's
    own (`_std` in the analysis script): a spread below 1e-12 becomes 1, so the variable is centred
    and left unscaled. Everything else is what deepsensor would have computed itself: the same
    frames, the same statistics (pandas std for station columns, xarray std for the grid), so no
    value that previously normalised changes.
    """
    import xarray as xr
    for f in frames:
        cols = {f.name: f} if isinstance(f, xr.DataArray) else {c: f[c] for c in f.columns}
        for var, s in cols.items():
            mu, sd = float(s.mean()), float(s.std())
            if not np.isfinite(sd) or sd < SD_FLOOR:
                sd = 1.0
            dp.add_to_config(var, method="mean_std", params={"mean": mu, "std": sd})


def make_task(aux, lat, lon, cov, y, C, T, time=PSEUDO_TIME):
    """One task. The DataProcessor is fitted on the grid and the CONTEXT only."""
    ctx = station_frame(lat[C], lon[C], y[C], cov[C], time)
    tgt = station_frame(lat[T], lon[T], y[T], None, time)
    x1_map, x2_map = square_maps(aux)
    dp = DataProcessor(x1_name="lat", x2_name="lon", x1_map=x1_map, x2_map=x2_map,
                       verbose=False)
    preset_norm(dp, [aux, ctx])
    aux_n, ctx_n = dp([aux, ctx])
    tgt_n = dp(tgt)
    tl = TaskLoader(context=[aux_n, ctx_n], target=tgt_n)
    return dp, tl, tl(time, context_sampling=["all", "all"], target_sampling="all")


def grid_da(lat, lon, values):
    import xarray as xr
    return xr.DataArray(np.asarray(values, float), coords={"lat": lat, "lon": lon},
                        dims=("lat", "lon"), name="aux")


def mean_at_targets(model, task):
    """Normalised-space mean at the targets. Spearman is invariant to the affine un-normalisation."""
    m = model.mean(task)
    m = m[0] if isinstance(m, (list, tuple)) else m
    return np.asarray(m, float).ravel()


def train_steps(model, sample_task, steps, device, log_every=50, batch=BATCH):
    opt = torch.optim.Adam(model.model.parameters(), lr=LR)
    model.model.train()
    t0 = time.time()
    for step in range(1, steps + 1):
        # a batch of tasks with the loss averaged: deepsensor's loss_fn scores one task at a time
        loss = sum(model.loss_fn(sample_task(), normalise=True) for _ in range(batch)) / batch
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.model.parameters(), 1.0)
        opt.step()
        if step % log_every == 0 or step == steps:
            print(f"  step {step:6d}/{steps} | loss {float(loss.detach()):.4f} | "
                  f"{(time.time() - t0) / 60:.1f} min", flush=True)
    model.model.eval()
    return model


VAL_TASKS = 64                   # fixed validation tasks, drawn once per fold
EVAL_EVERY = 100                 # steps between validation checks
PATIENCE = 5                     # checks without improvement before stopping


def val_loss(model, tasks) -> float:
    model.model.eval()
    with torch.no_grad():
        v = float(np.mean([float(model.loss_fn(t, normalise=True)) for t in tasks]))
    model.model.train()
    return v


def train_steps_es(model, sample_task, max_steps, val_tasks, batch=BATCH, max_minutes=0.0):
    """train_steps with EARLY STOPPING, registered in 26hp8 Section 3: validation on cities drawn
    from the training folds only. Stops after PATIENCE checks without improvement and restores the
    best weights. Returns the model and a record of the stopping path.

    WALL-CLOCK CAP (max_minutes > 0), declared 2026-09-11 before any real run: training also stops
    at the first validation check past the cap, so a run fits Kaggle's session and weekly quota.
    The record says which of the three rules stopped it: patience, max_steps or wall clock."""
    import copy
    opt = torch.optim.Adam(model.model.parameters(), lr=LR)
    model.model.train()
    t0 = time.time()
    best, best_step, bad, hist = np.inf, 0, 0, []
    best_state = copy.deepcopy(model.model.state_dict())
    step, stopped_by = 0, "max_steps"
    for step in range(1, max_steps + 1):
        loss = sum(model.loss_fn(sample_task(), normalise=True) for _ in range(batch)) / batch
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.model.parameters(), 1.0)
        opt.step()
        if step % EVAL_EVERY == 0 or step == max_steps:
            v = val_loss(model, val_tasks)
            hist.append([step, round(v, 5)])
            if v < best - 1e-4:
                best, best_step, bad = v, step, 0
                best_state = copy.deepcopy(model.model.state_dict())
            else:
                bad += 1
            print(f"  step {step:6d}/{max_steps} | train {float(loss.detach()):.4f} | val {v:.4f} "
                  f"| best {best:.4f} @ {best_step} | {(time.time() - t0) / 60:.1f} min", flush=True)
            if bad >= PATIENCE:
                stopped_by = "patience"
                break
            if max_minutes and (time.time() - t0) / 60 >= max_minutes:
                stopped_by = "wall clock"
                break
    model.model.load_state_dict(best_state)
    model.model.eval()
    return model, dict(stopped_by=stopped_by, max_minutes=max_minutes,
                       best_step=best_step, best_val=round(float(best), 5), stopped_at=step,
                       max_steps=max_steps, eval_every=EVAL_EVERY, patience=PATIENCE,
                       val_tasks=len(val_tasks), history=hist, minutes=round((time.time() - t0) / 60, 1))


def city_loader(aux, lat, lon, cov, Y):
    """One TRAINING city: a processor fitted ONCE on the grid and every site, which is legitimate
    because a training city is training data, and a loader whose linked "split" sampling draws
    disjoint context and targets from one station set. Verified by probe on 2026-09-11: a
    split_frac of k/n gives exactly k context stations and n - k targets. Building a processor per
    task, the first version, cost about 0.9 s a task on CPU; this costs 0.01 s once per city.
    Held-out cities are NEVER handled this way: they keep make_task's context-only processor."""
    days = pd.date_range(PSEUDO_TIME, periods=Y.shape[0], freq="D")
    st = pd.concat([station_frame(lat, lon, Y[d], cov, days[d]) for d in range(Y.shape[0])]).sort_index()
    x1_map, x2_map = square_maps(aux)
    dp = DataProcessor(x1_name="lat", x2_name="lon", x1_map=x1_map, x2_map=x2_map, verbose=False)
    preset_norm(dp, [aux, st])
    aux_n, st_n = dp([aux, st])
    tl = TaskLoader(context=[aux_n, st_n], target=st_n[["pm25"]], links=[(1, 0)])
    return dp, tl, list(days)


# ── positive control ──────────────────────────────────────────────────────────────────────────
def synth_geo(city):
    """Synthetic km coordinates to lat/lon around (10 N, 100 E), and a covariate raster."""
    lat = 10 + city["xy"][:, 1] / 110.57
    lon = 100 + city["xy"][:, 0] / (111.32 * np.cos(np.radians(10)))
    glat = np.linspace(lat.min() - 0.02, lat.max() + 0.02, GRID_N)
    glon = np.linspace(lon.min() - 0.02, lon.max() + 0.02, GRID_N)
    # the raster carries the same information as covariate 0 at the sites: noise in the primary
    # control, the field in the diagnostic variant. Nearest-site fill keeps it consistent.
    GLA, GLO = np.meshgrid(glat, glon, indexing="ij")
    d = (GLA[..., None] - lat) ** 2 + (GLO[..., None] - lon) ** 2
    raster = city["cov"][:, 0][np.argmin(d, axis=-1)]
    return lat, lon, grid_da(glat, glon, raster)


def run_control(a):
    torch.manual_seed(a.seed)
    inf = a.control_covariates == "informative"
    tr = base.synthetic_cities(a.train_cities, 60, a.days, seed=1000 + a.seed, informative=inf)
    te = base.synthetic_cities(a.test_cities, 60, 1, seed=9000, informative=inf)
    geo_tr = [synth_geo(c) for c in tr]
    rng = np.random.default_rng(a.seed)

    loaders = [city_loader(aux, lat, lon, c["cov"], c["y"]) for c, (lat, lon, aux) in zip(tr, geo_tr)]

    def sample():
        # registered sampler: one city-day, k context sites, ALL remaining sites as targets
        _, tl, times = loaders[int(rng.integers(len(loaders)))]
        k = int(rng.choice([kk for kk in KS if kk <= 60 - base.N_MIN_TARGETS]))
        return tl(times[int(rng.integers(len(times)))], context_sampling=["all", "split"],
                  target_sampling="split", split_frac=k / 60)

    dp0, tl0, _ = loaders[0]
    model = ConvNP(dp0, tl0, likelihood="gnp", internal_density=INTERNAL_DENSITY)
    model = train_steps(model, sample, a.steps, a.device)

    from pykrige.ok import OrdinaryKriging
    res = []
    for ci, c in enumerate(te):
        lat, lon, aux = synth_geo(c)
        y = c["y"][0]
        for rep in range(10):
            r2 = np.random.default_rng([ci, rep])
            T = r2.choice(60, 20, replace=False)
            P = np.setdiff1d(np.arange(60), T)
            F = r2.permutation(P)[:base.CONTROL_K]
            task = make_task(aux, lat, lon, c["cov"], y, F, T)[2]
            p_nn = mean_at_targets(model, task)
            ok = OrdinaryKriging(c["xy"][F, 0], c["xy"][F, 1], y[F], variogram_model="exponential",
                                 variogram_parameters=[25.0, 3.0 * c["len_scale"], 0.0],
                                 enable_plotting=False, verbose=False)
            p_or = np.asarray(ok.execute("points", c["xy"][T, 0], c["xy"][T, 1])[0])
            # the target frame is sorted by (lat, lon); align observed values to that order
            order = np.lexsort((lon[T], lat[T]))
            res.append(dict(city=ci, rep=rep, convgnp=base.srho(p_nn, y[T][order]),
                            oracle=base.srho(p_or, y[T])))
    R = pd.DataFrame(res)
    med_nn, med_or = float(R.convgnp.median()), float(R.oracle.median())
    passed = med_nn >= med_or - base.CONTROL_PASS_MARGIN
    summary = dict(arm="E10 ConvGNP", control_covariates=a.control_covariates,
                   primary_control=(a.control_covariates == "noise"), steps=a.steps,
                   train_cities=a.train_cities, days=a.days, test_cities=a.test_cities,
                   k=base.CONTROL_K, median_rho_convgnp=round(med_nn, 4),
                   median_rho_oracle=round(med_or, 4), margin=base.CONTROL_PASS_MARGIN,
                   passed=bool(passed), seed=a.seed, device=a.device)
    base.OUT.mkdir(parents=True, exist_ok=True)
    (base.OUT / f"control_convgnp_{a.control_covariates}_seed{a.seed}_steps{a.steps}.json"
     ).write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0 if passed else 5


# ── real data ─────────────────────────────────────────────────────────────────────────────────
def city_grid(cl):
    """The benchmark raster D4 wrote for this city, as the gridded context deepsensor requires."""
    g = pd.read_parquet(base.DL / "grids" / f"{cl}.parquet")
    lats, lons = np.sort(g.lat.unique()), np.sort(g.lon.unique())
    arr = g.pivot_table(index="lat", columns="lon", values="lc_built_2400").reindex(
        index=lats, columns=lons).to_numpy(float)
    if np.isnan(arr).any():
        arr = np.where(np.isnan(arr), np.nanmean(arr), arr)     # GEE edge cells, if any
    return grid_da(lats, lons, arr)


def run_real(a):
    torch.manual_seed(a.seed)
    S = pd.read_parquet(base.DL / "sites.parquet").drop_duplicates("site").set_index("site")
    S = S[S.cov_complete]
    D = pd.read_parquet(base.DL / "daily.parquet").drop_duplicates(["site", "day"])
    D = D[D.site.isin(S.index)]
    D["day"] = pd.to_datetime(D.day, utc=True).dt.tz_localize(None)

    # TRAINING cities: one processor and loader each, built once (training data, no leak)
    loaders = []
    for cl in sorted(S[S.fold != a.fold].cluster.unique()):
        s = S[S.cluster == cl]
        d = D[D.cluster == cl].merge(s[COVARS + ["lat", "lon"]], left_on="site", right_index=True)
        if d.empty:
            continue
        st = (d.rename(columns={"day": "time"})[["time", "lat", "lon", "pm25"] + COVARS]
              .set_index(["time", "lat", "lon"]).sort_index())
        aux = city_grid(cl)
        x1_map, x2_map = square_maps(aux)
        dp = DataProcessor(x1_name="lat", x2_name="lon", x1_map=x1_map, x2_map=x2_map, verbose=False)
        preset_norm(dp, [aux, st])
        aux_n, st_n = dp([aux, st])
        tl = TaskLoader(context=[aux_n, st_n], target=st_n[["pm25"]], links=[(1, 0)])
        per_day = d.groupby("day").size()
        days = list(per_day[per_day >= 3 + base.N_MIN_TARGETS].index)
        if days:
            loaders.append((dp, tl, days, per_day))
    # EARLY-STOPPING cities (26hp8 Section 3): every fifth training city in cluster order is held
    # out for validation. Drawn from the TRAINING folds only, and the same for every seed, so seeds
    # differ only in initialisation and in the training tasks drawn.
    val_idx = set(range(2, len(loaders), 5))
    train_l = [x for i, x in enumerate(loaders) if i not in val_idx]
    val_l = [x for i, x in enumerate(loaders) if i in val_idx]
    print(f"fold {a.fold}: {len(train_l)} training + {len(val_l)} validation cities", flush=True)
    rng = np.random.default_rng(a.seed)

    def draw(pool, r):
        # registered sampler: a city-day, k present sites as context, ALL remaining as targets
        _, tl, days, per_day = pool[int(r.integers(len(pool)))]
        day = days[int(r.integers(len(days)))]
        n = int(per_day[day])
        k = int(r.choice([kk for kk in KS if kk <= n - base.N_MIN_TARGETS]))
        return tl(day, context_sampling=["all", "split"], target_sampling="split", split_frac=k / n)

    def sample():
        return draw(train_l, rng)

    vr = np.random.default_rng(1000 + a.fold)
    val_tasks = [draw(val_l, vr) for _ in range(VAL_TASKS)]

    dp0, tl0, _, _ = train_l[0]
    model = ConvNP(dp0, tl0, likelihood="gnp", internal_density=INTERNAL_DENSITY)
    model, es = train_steps_es(model, sample, a.steps, val_tasks, max_minutes=a.max_minutes)
    base.OUT.mkdir(parents=True, exist_ok=True)
    (base.OUT / f"es_convgnp_fold{a.fold}_seed{a.seed}.json").write_text(json.dumps(es, indent=2))
    torch.save(model.model.state_dict(), base.OUT / f"convgnp_fold{a.fold}_seed{a.seed}.pt")

    # EVALUATION on the held-out fold, on the analysis script's own splits, with a processor
    # fitted on the grid and the CONTEXT only (make_task). deepsensor returns target predictions
    # in sorted (lat, lon) order, so observed values are sorted the same way before scoring.
    Sall = pd.read_parquet(base.DL / "sites.parquet").drop_duplicates("site").set_index("site")
    static = pd.read_parquet(base.DL / "static.parquet")
    test = set(Sall[Sall.fold == a.fold].cluster)
    grids = {}
    rows = []

    def score(cl, F, T, yF, yT, time=PSEUDO_TIME):
        if cl not in grids:
            grids[cl] = city_grid(cl)
        sF, sT = Sall.loc[F], Sall.loc[T]
        lat = np.r_[sF.lat, sT.lat]; lon = np.r_[sF.lon, sT.lon]
        cov = np.r_[sF[COVARS].to_numpy(float), sT[COVARS].to_numpy(float)]
        y = np.r_[yF, yT]
        C, Tt = np.arange(len(F)), np.arange(len(F), len(F) + len(T))
        task = make_task(grids[cl], lat, lon, cov, y, C, Tt, time)[2]
        order = np.lexsort((lon[Tt], lat[Tt]))
        return base.srho(mean_at_targets(model, task), yT[order])

    for frame, sub in (("registered", "analysis"), ("s70", "analysis_s70")):
        f1 = base.DL / f"{sub}_splits_q1_primary.parquet"
        if f1.exists():
            st = static[static.frame == frame].drop_duplicates("site").set_index("site").static_mean
            for r in pd.read_parquet(f1).itertuples():
                if r.cluster not in test:
                    continue
                F, T = r.fit.split("|"), r.held.split("|")
                rows.append(dict(frame=frame, design="Q1", cluster=r.cluster, rep=r.rep, k=r.k,
                                 day=-1, est="E10",
                                 rho=score(r.cluster, F, T, st.loc[F].to_numpy(float),
                                           st.loc[T].to_numpy(float))))
        f2 = base.DL / f"{sub}_splits_q2.parquet"
        if f2.exists():
            Dd = D.set_index(["site", "day"]).pm25
            for r in pd.read_parquet(f2).itertuples():
                if r.cluster not in test:
                    continue
                Fk, T = r.fit.split("|"), r.held.split("|")
                for pos, day in enumerate(r.days.split("|")):
                    dt = pd.Timestamp(day)
                    vF = pd.Series({x: Dd.get((x, dt), np.nan) for x in Fk}).dropna()
                    vT = np.array([Dd.get((x, dt), np.nan) for x in T], float)
                    if len(vF) < 3 or not np.all(np.isfinite(vT)):
                        continue
                    rows.append(dict(frame=frame, design="Q2", cluster=r.cluster, rep=r.rep, k=r.k,
                                     day=pos, est="E10",
                                     rho=score(r.cluster, list(vF.index), T, vF.to_numpy(float), vT, dt)))
    out = pd.DataFrame(rows)
    out["fold"], out["seed"] = a.fold, a.seed
    out.to_parquet(base.OUT / f"pred_convgnp_fold{a.fold}_seed{a.seed}.parquet", index=False)
    print(f"scored {len(out):,} task(s) on fold {a.fold}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["control", "real"])
    ap.add_argument("--fold", type=int, default=0)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-minutes", type=float, default=0.0,
                    help="real mode: wall-clock cap on training, checked at validation points")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--train-cities", type=int, default=40)
    ap.add_argument("--test-cities", type=int, default=6)
    ap.add_argument("--days", type=int, default=5)
    ap.add_argument("--control-covariates", choices=["noise", "informative"], default="noise")
    a = ap.parse_args()
    if str(a.device).startswith("cuda"):
        # ConvNP lives on torch's DEFAULT device; --device was parsed and never applied before
        # 2026-09-11, so the E10 positive control ran on the Kaggle CPU at 7.44 s per step. The
        # control's pass stands (device does not change the method); real runs must use the GPU.
        from deepsensor.train.train import set_gpu_default_device
        set_gpu_default_device()
        print("device: cuda (deepsensor default device set)", flush=True)
    return run_control(a) if a.mode == "control" else run_real(a)


if __name__ == "__main__":
    sys.exit(main())
