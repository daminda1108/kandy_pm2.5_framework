"""Size, network structure and detection limit of the candidate spatial frame.

Power uses the project's own method (phase1_frame_and_power.mde): the smallest paired
improvement a one-sided Wilcoxon signed-rank test detects at 80% power, by simulation.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).parent
C = pd.read_csv(HERE / "concurrent_density.csv")

print("CANDIDATE FRAME (concurrent one-year reference stations):")
for thr in (15, 20, 30):
    f = C[C.conc_365 >= thr]
    print(f"  >= {thr}: {len(f):3d} cities | {int(f.conc_365.sum()):5d} stations | "
          f"{f.country.nunique():2d} countries | cities per country: "
          f"{dict(f.country.value_counts().head(6))}")

N_BOOT = 400


def mde(sd, n, rng):
    for eff in np.arange(0.01, 1.01, 0.01):
        hits = 0
        for _ in range(N_BOOT):
            x = rng.normal(eff, sd, n)
            try:
                if wilcoxon(x)[1] < 0.05 and np.median(x) > 0:
                    hits += 1
            except Exception:
                pass
        if hits / N_BOOT >= 0.80:
            return round(float(eff), 3)
    return float("nan")


print("\nDETECTION LIMIT for a paired across-city effect (80% power, Wilcoxon, alpha 0.05):")
print("  sd = between-city spread of the per-city effect. 0.20 is the siting experiment's")
print("  observed spread; 0.10 is what averaging many splits within a city should approach.")
rng = np.random.default_rng(20260911)
for n in (9, 14, 28, 56):
    row = [f"n={n:2d}"]
    for sd in (0.10, 0.15, 0.20, 0.25):
        row.append(f"sd {sd:.2f}: {mde(sd, n, rng):.3f}")
    print("   " + " | ".join(row))

print("\nPER-SPLIT NOISE of a held-out Spearman correlation (n_held points, true rho 0.4):")
from scipy.stats import spearmanr
for nh in (4, 6, 8, 10, 15, 20):
    r = []
    for _ in range(3000):
        x = rng.normal(size=nh)
        y = 0.4 * x + np.sqrt(1 - 0.16) * rng.normal(size=nh)
        r.append(spearmanr(x, y).statistic)
    r = np.array(r)
    print(f"   n_held {nh:2d}: sd {np.nanstd(r):.3f} | distinct values attainable "
          f"{len(np.unique(np.round(r, 6)))}")
