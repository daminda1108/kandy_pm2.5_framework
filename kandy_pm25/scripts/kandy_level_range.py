"""kandy_level_range.py -- an evidence-based range for Kandy's absolute level (2026-10-11, ledger F.128). EXPLORATORY.

The field's annual level is the van Donkelaar satellite area mean. Across the ladder's cities the same chain run
with no stations (K0: the composition prior shifted each year to the satellite level; ladder_v2_kandy_model.py)
measures how far that satellite level sits from the withheld city mean, city by city. Assuming Kandy's satellite
level errs like a typical city of that distribution, the true basin mean is model / (1 + bias). Reported for all
cities and for the tropical cities, at the median and the quartiles (and 10th/90th percentiles), for each anchored
year. It is a transfer of an error distribution from other cities, not a measurement at Kandy.

Out: data/processed/decomp/kandy_level_range.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
L2 = REPO / "data" / "processed" / "modular" / "ladder_v2"
DEC = REPO / "data" / "processed" / "decomp"
WHO = 5.0


def main():
    C = pd.read_csv(L2 / "kandy_model_percity_reconstruction.csv", index_col=0)
    years = {}
    for y in range(2019, 2024):
        f = pd.read_parquet(DEC / f"kandy_decomp_predictions_{y}_additive_v3.parquet", columns=["pm25_q50"])
        years[y] = float(f.pm25_q50.mean())
    out = {"model_annual_mean": years}
    for scope, sub in (("all", C), ("tropical", C[C.band.isin(["deep_tropical", "tropical"])])):
        b = sub.K0_bias.dropna().to_numpy() / 100.0
        q = {p: float(np.percentile(b, p)) for p in (10, 25, 50, 75, 90)}
        rng = {}
        for y, m in years.items():
            rng[y] = {f"p{p}": m / (1 + v) for p, v in q.items()}
        lo = min(r["p75"] for r in rng.values()); hi = max(r["p25"] for r in rng.values())
        lo90 = min(r["p90"] for r in rng.values()); hi90 = max(r["p10"] for r in rng.values())
        out[scope] = dict(n=int(len(b)), bias_pct={k: round(100 * v, 1) for k, v in q.items()}, by_year=rng,
                          iqr_range=[round(lo, 1), round(hi, 1)], p10_p90_range=[round(lo90, 1), round(hi90, 1)],
                          iqr_range_times_who=[round(lo / WHO, 1), round(hi / WHO, 1)])
    tmp = DEC / "kandy_level_range.tmp.json"
    tmp.write_text(json.dumps(out, indent=2), encoding="utf-8"); os.replace(tmp, DEC / "kandy_level_range.json")
    print(json.dumps({k: (v if k == "model_annual_mean" else {kk: v[kk] for kk in ("n", "bias_pct", "iqr_range", "p10_p90_range", "iqr_range_times_who")}) for k, v in out.items()}, indent=1))


if __name__ == "__main__":
    main()
