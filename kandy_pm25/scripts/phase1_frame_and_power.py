"""PHASE 1 — is the frame big enough to answer the question, and what is the real benchmark?

Plan: docs/learned_pattern_plan_2026-09-04.md §4. Phase 0 established that no engineered source
surface beats night lights, but it ran on 8 cities and could not have detected an improvement
below delta rho = 0.35. That is not a frame you can register an experiment on. This script asks
two things on the 47-city LUR frame instead:

  1. WHICH single globally available predictor ranks stations best, per city? That is the
     benchmark a learned pattern has to clear, and it should be estimated on the widest frame
     available rather than on the nine valley cities that happen to have terrain rasters.

  2. WHAT could a paired test on this frame actually detect? Computed here, before any model is
     built, because a null with an unstated detection limit converts a limit of the experiment
     into a property of the atmosphere (F.92).

Every predictor here is static geography, globally available, and admissible at Bud0 -- no
observation of the target city enters, so nothing in this file leaks.

⚠ `nres` is non-residential built volume, the closest thing this frame has to an industrial
proxy. It is included deliberately: Phase 0 found OSM industrial land use to be the best single
proxy at two of six cities, on a frame too small to trust. This tests the same idea at 47.

Usage: .venv/Scripts/python.exe scripts/phase1_frame_and_power.py
Out:   data/processed/modular/phase1_predictor_ranking.csv
       data/processed/paper_figures/phase1_frame.json
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from figdata import emit  # noqa: E402

MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "phase1_predictor_ranking.csv"
MIN_STATIONS = 8          # below this a per-city rank correlation is not worth computing
N_BOOT = 4000


def per_city_rho(d: pd.DataFrame, col: str) -> pd.DataFrame:
    rows = []
    for city, g in d.groupby("city"):
        g = g[["pm", col]].dropna()
        if len(g) < MIN_STATIONS or g[col].std() < 1e-12 or g.pm.std() < 1e-12:
            continue
        rows.append(dict(city=city, n=len(g), rho=float(spearmanr(g[col], g.pm)[0])))
    return pd.DataFrame(rows)


def mde(sd: float, n: int, rng) -> float:
    """Smallest paired improvement detectable at 80 per cent power, by simulation."""
    for eff in np.arange(0.01, 1.01, 0.01):
        hits = 0
        for _ in range(N_BOOT):
            x = rng.normal(eff, sd, n)
            try:
                if wilcoxon(x)[1] < 0.05 and np.median(x) > 0:
                    hits += 1
            except Exception:                                               # noqa: BLE001
                pass
        if hits / N_BOOT >= 0.80:
            return round(float(eff), 3)
    return float("nan")


def main() -> int:
    d = pd.read_csv(MOD / "lur_predictors.csv")
    cand = [c for c in d.columns
            if c not in ("city", "band", "src", "station_id", "lat", "lon", "pm")]
    n_city = d.groupby("city").size()
    keep = n_city[n_city >= MIN_STATIONS].index
    d = d[d.city.isin(keep)]
    print(f"PHASE 1 -- {d.city.nunique()} cities, {len(d)} stations, "
          f"{len(cand)} candidate predictors")
    print(f"  (cities with >= {MIN_STATIONS} stations; median "
          f"{int(d.groupby('city').size().median())} stations per city)\n")

    rows = []
    per_city = {}
    for col in cand:
        r = per_city_rho(d, col)
        if len(r) < 20:
            continue
        per_city[col] = r.set_index("city").rho
        rows.append(dict(predictor=col, cities=len(r), median_rho=float(r.rho.median()),
                         mean_rho=float(r.rho.mean()),
                         positive=int((r.rho > 0).sum())))
    R = pd.DataFrame(rows).sort_values("median_rho", ascending=False)

    print("  best single predictors, by median per-city rank correlation")
    print(f"    {'predictor':<18}{'cities':>7}{'median':>9}{'mean':>8}{'pos':>7}")
    for r in R.head(12).itertuples():
        print(f"    {r.predictor:<18}{r.cities:>7}{r.median_rho:>+9.3f}"
              f"{r.mean_rho:>+8.3f}{r.positive:>5}/{r.cities}")
    print("\n  worst three, for scale")
    for r in R.tail(3).itertuples():
        print(f"    {r.predictor:<18}{r.cities:>7}{r.median_rho:>+9.3f}"
              f"{r.mean_rho:>+8.3f}{r.positive:>5}/{r.cities}")

    best = R.iloc[0]
    R.to_csv(OUT, index=False)

    # ── power on THIS frame ───────────────────────────────────────────────────────────────
    # The relevant spread is the between-city spread of the DIFFERENCE between two arms, so
    # it is estimated from two real arms rather than assumed: the best predictor against the
    # night-lights baseline the project has been quoting.
    rng = np.random.default_rng(0)
    ref = "ntl_1000" if "ntl_1000" in per_city else R.predictor.iloc[1]
    pair = pd.concat([per_city[best.predictor].rename("a"),
                      per_city[ref].rename("b")], axis=1).dropna()
    sd, n = float((pair.a - pair.b).std(ddof=1)), len(pair)
    m = mde(sd, n, rng)

    print(f"\n  POWER on this frame")
    print(f"    paired arms: {best.predictor} against {ref}")
    print(f"    n = {n} cities, between-city sd of the difference = {sd:.3f}")
    print(f"    smallest improvement detectable at 80% power: delta rho = {m:.3f}")

    # what Phase 0 could do, for contrast, at its own n and sd
    m8 = mde(0.250, 8, np.random.default_rng(0))
    print(f"    Phase 0, for comparison (n = 8, sd 0.250): delta rho = {m8:.3f}")
    print(f"    -> the wider frame improves the detection limit by "
          f"{m8 / m:.1f}x" if m == m else "")

    emit("phase1_frame",
         cities=int(d.city.nunique()),
         stations=int(len(d)),
         predictors=int(len(R)),
         best_predictor=str(best.predictor),
         best_median_rho=round(float(best.median_rho), 3),
         best_positive=int(best.positive),
         ntl_median_rho=round(float(R[R.predictor == ref].median_rho.iloc[0]), 3),
         paired_n=int(n),
         paired_sd=round(sd, 3),
         min_detectable_delta=m,
         min_detectable_delta_phase0=m8)
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
