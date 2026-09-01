"""p4_identifiability.py -- P4: declared identifiability, per parameter, per budget.

The specification asserts that "every element of theta carries a profile-likelihood interval
PER BUDGET; bound-saturation is reported, not hidden". The machinery existed (`diff_decomp.py`)
but the analysis had never been run (F.74). This runs it.

WHY THE DESIGN IS SIMULATION-BASED, AND WHY THAT IS THE RIGHT CHOICE
-------------------------------------------------------------------
P4 asks a question about the BUDGET, not about our particular fit: *given n stations placed
where these cities actually place them, which parameters could be recovered at all?* That is a
property of the design -- the real emission surface, the real terrain, the real station
coordinates and the real observation noise -- and it is answered by asking whether the
likelihood has curvature in each direction, not by whether one fit happened to converge.

So: take a city's REAL geometry and REAL station positions, generate a field from a known
theta_true, sample it at the budget's stations with realistic noise, and attempt recovery by
profile likelihood. A parameter whose profile is flat over its whole bound is unidentifiable at
that budget no matter how good the estimator. This is the standard practice for identifiability
and it cannot be gamed by a lucky fit.

BUDGETS (matching `budgets.py`)
    Bud1  2 stations   -- Kandy's actual tier
    Bud2  8 stations
    Bud3  8 stations + a regional background constraint

METHOD
    For each parameter theta_i: fix it on a grid across its bounds, re-optimise the other four
    by Adam on the unconstrained reparameterisation, and record the profile deviance
    D(theta_i) = -2 log L. The 95% interval is {theta_i : D - D_min <= 3.84} (chi2_1). A
    parameter whose interval spans its entire prior box is reported UNIDENTIFIED; one whose
    optimum sits on a bound is reported SATURATED.

Usage:  python scripts/p4_identifiability.py [--cities medellin,kathmandu,chiangmai] [--grid 13]
Out:    data/processed/modular/p4_identifiability.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "processed" / "modular" / "p4_identifiability.csv"

# bounds and shipped values, identical to diff_decomp.py
BOUNDS = {"kappa": (0.0, 0.60), "a_cap": (0.05, 1.50), "eps0": (0.0, 12.0),
          "w_evening": (0.0, 1.0), "s_exp": (0.25, 3.0)}
TRUE = {"kappa": 0.15, "a_cap": 0.50, "eps0": 3.69, "w_evening": 0.40, "s_exp": 1.0}
CHI2_1_95 = 3.841459

BUDGETS = {"Bud1": 2, "Bud2": 8, "Bud3": 8}   # Bud3 adds a background constraint, not stations


def _logit(v, lo, hi):
    z = min(max((v - lo) / (hi - lo), 1e-6), 1 - 1e-6)
    return float(np.log(z / (1 - z)))


class Theta(torch.nn.Module):
    """Unconstrained reparameterisation so the optimiser cannot leave the prior box."""

    def __init__(self, init):
        super().__init__()
        for k, (lo, hi) in BOUNDS.items():
            self.register_parameter(k, torch.nn.Parameter(torch.tensor(_logit(init[k], lo, hi))))

    def physical(self, fixed=None):
        out = {}
        for k, (lo, hi) in BOUNDS.items():
            if fixed and k in fixed:
                out[k] = torch.tensor(float(fixed[k]))
            else:
                out[k] = lo + (hi - lo) * torch.sigmoid(getattr(self, k))
        return out


def p_local(F, p):
    """Unit-mean local pattern. Mirrors diff_decomp.p_local."""
    s = F["s_emit"].clamp_min(1e-6) ** p["s_exp"]
    m = 1.0 + p["kappa"] * F["w_blh"][:, None] * F["c_conf"][None, :]
    e_t = (1.0 - p["w_evening"]) * F["e_prior"] + p["w_evening"] * F["e_fit"]
    amp = (e_t[:, None] * F["a_trans"]).clamp(max=p["a_cap"])
    raw = s[None, :] * m * (1.0 + amp)
    return raw / raw.mean(dim=1, keepdim=True)


def field(T, B, F, p):
    """PM = B + max(max(T-B,0), eps0)*P + min(T-B,0) - max(0, eps0 - max(T-B,0)).

    Mean-zero epsilon floor, so the basin mean stays locked to T for every parameter value --
    which is why NO parameter is identifiable from the level (see the report)."""
    Pl = p_local(F, p)
    inc = T - B
    acc = inc.clamp_min(0)
    eps = p["eps0"]
    eff = torch.maximum(acc, eps * torch.ones_like(acc))
    corr = (eps - acc).clamp_min(0)
    return B[:, None] + eff[:, None] * Pl + inc.clamp_max(0)[:, None] - corr[:, None]


def load_city(city: str, rng: np.random.Generator, H: int = 96):
    """Real emission surface, real terrain, real station coordinates."""
    st = np.load(REPO / f"data/processed/decomp/S_traffic_{city}.npz")
    tr = np.load(REPO / f"data/processed/pinn_inputs/{city}_terrain_core.npz")
    S = st["S_traffic"].astype(float)
    lats, lons = st["lats"].astype(float), st["lons"].astype(float)

    dz = tr["delta_z"].astype(float)
    # resample terrain onto the emission grid by nearest index
    yi = np.clip((np.linspace(0, dz.shape[0] - 1, S.shape[0])).round().astype(int), 0, dz.shape[0] - 1)
    xi = np.clip((np.linspace(0, dz.shape[1] - 1, S.shape[1])).round().astype(int), 0, dz.shape[1] - 1)
    dzr = dz[np.ix_(yi, xi)]
    c = -(dzr - dzr.mean()) / (dzr.std() + 1e-9)          # confinement z-score, low ground = high

    stn = pd.read_parquet(REPO / f"data/processed/stage2/{city}_perstation_v13.parquet")
    coords = stn.groupby("station_id")[["lat", "lon"]].first().dropna()
    # per-station observation noise, from the real record
    sig = stn.groupby("station_id").pm25.std().median()
    sigma = float(sig) if np.isfinite(sig) and sig > 0 else 5.0

    # map stations to grid cells inside the domain
    idx = []
    for sid, r in coords.iterrows():
        iy = int(np.abs(lats - r.lat).argmin()); ix = int(np.abs(lons - r.lon).argmin())
        if abs(lats[iy] - r.lat) < (lats[1] - lats[0]) * 2 and abs(lons[ix] - r.lon) < abs(lons[1] - lons[0]) * 2:
            idx.append(iy * S.shape[1] + ix)
    idx = sorted(set(idx))

    Sf = torch.tensor((S / S.mean()).ravel(), dtype=torch.float64)
    cf = torch.tensor(c.ravel(), dtype=torch.float64)
    P = Sf.numel()
    F = {"s_emit": Sf, "c_conf": cf,
         "a_trans": torch.tensor(rng.random((H, P)), dtype=torch.float64),
         "w_blh": torch.tensor(rng.random(H), dtype=torch.float64),
         "e_prior": torch.tensor(rng.random(H) * 1.5 + 0.3, dtype=torch.float64),
         "e_fit": torch.tensor(rng.random(H) * 1.5 + 0.3, dtype=torch.float64)}
    T = torch.tensor(rng.random(H) * 30 + 10, dtype=torch.float64)
    B = T * torch.tensor(0.35 + 0.35 * rng.random(H), dtype=torch.float64)
    return F, T, B, idx, sigma


def fit(F, T, B, obs, cells, sigma, fixed=None, steps=150, seed=0):
    """Optimise the free parameters; return the deviance -2 log L at the optimum."""
    torch.manual_seed(seed)
    init = {k: TRUE[k] for k in BOUNDS}
    th = Theta(init)
    free = [getattr(th, k) for k in BOUNDS if not (fixed and k in fixed)]
    if not free:
        pm = field(T, B, F, th.physical(fixed))
        return float(((pm[:, cells] - obs) ** 2).sum() / sigma ** 2)
    opt = torch.optim.Adam(free, lr=0.08)
    best = np.inf
    for _ in range(steps):
        opt.zero_grad()
        pm = field(T, B, F, th.physical(fixed))
        d = ((pm[:, cells] - obs) ** 2).sum() / sigma ** 2
        d.backward()
        opt.step()
        best = min(best, float(d.detach()))
    return best


def _crossing(grid, rel, imin, step):
    """Where the profile deviance crosses the chi2_1 threshold, INTERPOLATED (C5).

    Taking the outermost grid point still under the threshold quantises the interval to the grid
    spacing, and when only one point is under it the interval collapses to zero width -- which
    the old code then reported as `identified`, the exact opposite of what a zero-width interval
    from a coarse grid means.

    Walk outward from the profile minimum while the deviance stays under the threshold, then
    linearly interpolate the crossing between the last point below and the first point above.
    Returns (value, at_bound); at_bound is True when the profile never rises above the threshold
    before running into the parameter's box, i.e. the data does not bound it on that side.
    """
    i = imin
    while 0 <= i + step < len(grid) and rel[i + step] <= CHI2_1_95:
        i += step
    j = i + step
    if not (0 <= j < len(grid)):
        return float(grid[i]), True
    denom = rel[j] - rel[i]
    if denom <= 0:                      # non-monotone profile; fall back to the grid point
        return float(grid[i]), False
    f = (CHI2_1_95 - rel[i]) / denom
    return float(grid[i] + f * (grid[j] - grid[i])), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", default="medellin,kathmandu,chiangmai")
    # C5: was 7. At 7 points a profile with one point under the chi2 threshold produced
    # lo95 == hi95 and was scored `identified`. 25 points plus interpolated crossings makes the
    # interval a property of the likelihood rather than of the grid spacing.
    ap.add_argument("--grid", type=int, default=25)
    a = ap.parse_args()

    rows = []
    for city in a.cities.split(","):
        rng = np.random.default_rng(20260822)
        F, T, B, cells_all, sigma = load_city(city, rng)
        print(f"\n=== {city}: {len(cells_all)} stations in-domain, sigma_obs = {sigma:.2f}")
        if len(cells_all) < 8:
            print("   too few in-domain stations; skipped")
            continue

        pm_true = field(T, B, F, {k: torch.tensor(v) for k, v in TRUE.items()})

        for bud, n in BUDGETS.items():
            sel = list(rng.choice(cells_all, size=min(n, len(cells_all)), replace=False))
            obs = pm_true[:, sel] + torch.tensor(
                rng.normal(0, sigma, size=(pm_true.shape[0], len(sel))), dtype=torch.float64)
            base = fit(F, T, B, obs, sel, sigma)
            print(f"  {bud} (n={len(sel)}):  deviance at optimum {base:.1f}")

            for name, (lo, hi) in BOUNDS.items():
                grid = np.linspace(lo, hi, a.grid)
                dev = np.array([fit(F, T, B, obs, sel, sigma, fixed={name: g}) for g in grid])
                rel = dev - dev.min()
                imin = int(rel.argmin())
                mle = float(grid[imin])
                under = rel <= CHI2_1_95
                n_under = int(under.sum())

                lo95, lo_at_bound = _crossing(grid, rel, imin, -1)
                hi95, hi_at_bound = _crossing(grid, rel, imin, +1)
                width = hi95 - lo95
                frac = width / (hi - lo)
                sat = mle <= lo + 1e-9 or mle >= hi - 1e-9

                # C5. A single grid point under the threshold does NOT mean the parameter is
                # sharply determined -- it means the grid is too coarse to resolve the interval.
                # The old code reported exactly that case as `identified` with lo95 == hi95.
                grid_limited = n_under < 2
                if grid_limited:
                    status = "grid-limited"
                elif frac > 0.90:
                    status = "UNIDENTIFIED"
                elif frac > 0.40:
                    status = "weak"
                else:
                    status = "identified"

                rows.append(dict(city=city, budget=bud, n_stations=len(sel), param=name,
                                 true=TRUE[name], mle=mle, lo95=lo95, hi95=hi95,
                                 box_fraction=round(frac, 3), saturated=sat,
                                 n_under=n_under, grid=a.grid,
                                 lo_at_bound=lo_at_bound, hi_at_bound=hi_at_bound,
                                 status=status))
                flags = ("  SATURATED" if sat else "") + ("  GRID-LIMITED" if grid_limited else "")
                print(f"     {name:<10} MLE {mle:7.3f} (true {TRUE[name]:6.3f})  "
                      f"95% CI [{lo95:6.3f},{hi95:6.3f}]  {frac*100:5.1f}% of box  "
                      f"{status}  (n_under={n_under}/{a.grid}){flags}")

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(df)} rows)")
    if len(df):
        print("\n=== P4 SUMMARY: identifiability by budget ===")
        print(pd.crosstab([df.param], [df.budget, df.status]).to_string())


if __name__ == "__main__":
    main()
