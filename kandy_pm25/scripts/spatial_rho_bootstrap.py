"""spatial_rho_bootstrap.py — bootstrap confidence intervals on the held-out spatial
rank correlation, per city (2026-08-06, reviewer point 5).

WHY
---
The scorecard reports Spearman rho from 0.78 down to -0.06 on between 4 and 39
stations, with no intervals, and the paper builds a substantive ordering on those
differences. At n=9 a rho of 0.07 and a rho of 0.10 are not distinguishable from each
other or from zero. This script attaches a station-resampled bootstrap interval to
every rho, plus the exact permutation p-value, so the table can state what is and is
not resolvable.

It also reports n_common -- the number of held-out stations that actually fall inside
the modelled domain and therefore enter the rank -- which is NOT the same as the
scorecard's n (held-out station count). Those two numbers differ and the paper prints
only one of them.

Run:  .venv/Scripts/python.exe scripts/spatial_rho_bootstrap.py
Out:  results/figures/multicity/spatial_rho_bootstrap.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
import xichang_paper_figures as xf  # noqa: E402

OUT = REPO / "results" / "figures" / "multicity" / "spatial_rho_bootstrap.csv"
CITIES = ["xichang", "chiangmai", "bazhou", "chandigarh", "kathmandu",
          "baoji", "taian", "yichang", "medellin", "bogota"]
NBOOT = 10000
SEED = 20260806


def station_means(city: str):
    """Per-station modelled and observed annual means over the held-out set."""
    xf._setup(city)
    st, anc = xf._stations_split()
    vault = [s for s in st.index if int(s) not in anc]
    P, O = [], []
    for y in xf.xp.YEARS:
        try:
            P.append(xf._pred_at_stations(y)); O.append(xf._obs(y))
        except Exception:
            continue
    P = pd.concat(P).dropna(subset=["pred"]); O = pd.concat(O)
    P = P[P.station_id.isin(vault)]; O = O[O.station_id.isin(vault)]
    ps = P.groupby("station_id").pred.mean()
    os_ = O.groupby("station_id").pm25.mean()
    common = ps.index.intersection(os_.index)
    return xf.CFG["name"], len(vault), ps[common].values, os_[common].values


def boot(x, y, nboot=NBOOT, seed=SEED):
    """Station-resampled bootstrap + exact-ish permutation p, on Spearman rho."""
    from scipy.stats import spearmanr
    n = len(x)
    if n < 4:
        return np.nan, np.nan, np.nan, np.nan
    rho = spearmanr(x, y)[0]
    rng = np.random.default_rng(seed)
    bs = np.empty(nboot)
    for i in range(nboot):
        k = rng.integers(0, n, n)
        if len(np.unique(k)) < 3:
            bs[i] = np.nan; continue
        bs[i] = spearmanr(x[k], y[k])[0]
    bs = bs[np.isfinite(bs)]
    lo, hi = np.percentile(bs, [5, 95])
    # permutation null
    perm = np.empty(nboot)
    for i in range(nboot):
        perm[i] = spearmanr(x, rng.permutation(y))[0]
    p = float((np.abs(perm) >= abs(rho)).mean())
    return float(rho), float(lo), float(hi), p


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rows = []
    for c in CITIES:
        try:
            name, n_vault, x, y = station_means(c)
        except Exception as e:                                    # noqa: BLE001
            print(f"  {c:<12} SKIP ({type(e).__name__}: {e})")
            continue
        rho, lo, hi, p = boot(np.asarray(x, float), np.asarray(y, float))
        rows.append(dict(slug=c, city=name, n_heldout=n_vault, n_ranked=len(x),
                         rho=rho, ci5=lo, ci95=hi, p_perm=p))
        if np.isnan(rho):
            print(f"  {name:<24} n_ranked={len(x):>3}  rho NOT ESTIMABLE (<4 ranked)")
        else:
            print(f"  {name:<24} n_ranked={len(x):>3}  rho {rho:+.2f} "
                  f"[{lo:+.2f}, {hi:+.2f}]  p={p:.3f}"
                  f"{'' if p < 0.05 else '   (not distinguishable from 0)'}")
    R = pd.DataFrame(rows)
    R.to_csv(OUT, index=False)

    est = R.dropna(subset=["rho"])
    sig = est[est.p_perm < 0.05]
    print(f"\n  {len(est)} of {len(R)} cities estimable; "
          f"{len(sig)} distinguishable from zero at p<0.05: "
          f"{', '.join(c.split(' (')[0] for c in sig.city)}")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
