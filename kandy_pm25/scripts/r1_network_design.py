"""R1 -- turn the budget ladder into a siting recommendation.

We measured what each increment of information is worth across 48 cities and never turned it
into the question a ministry actually asks: **where should the next monitor go, and what will it
buy?** That falls straight out of the ladder and costs no new modelling.

🔴 THE POINT OF THIS SCRIPT IS THAT THE POOLED ANSWER IS WRONG FOR KANDY.

Pooled, the ladder says the regional-background rung is the largest gain in the programme
(40.6%) and the first two in-city stations buy 17.9%. That has been the project's standing
acquisition advice: chase NBRO before anything else.

Stratified by latitude band it inverts. In the **deep tropics** -- Kandy's own band -- the first
two stations buy **21.9%** and the background rung buys only **8.5%**, the smallest of the four
bands. Recommending a regional background station to Kandy on the strength of a pooled number
computed mostly from other climate zones is precisely the error this programme keeps making:
a quantity attributed to the wrong stratum.

⚠ AND THE BAND RESULT IS ITSELF CONDITIONAL ON C1. The recorded explanation for the deep-tropical
background collapse (28.1% -> 8.5%) is that *the satellite level substitutes for the background
there*. But C1 established that the satellite stream is GHAP, a fused product trained on the very
monitor networks this panel is built from. If a contaminated satellite stream is standing in for
a background station, the substitution may be leakage rather than physics. **This recommendation
is provisional until C1 re-runs with raw MAIAC AOD.** Said here rather than discovered later.

Usage:  .venv/Scripts/python.exe scripts/r1_network_design.py
Out:    data/processed/modular/r1_network_design.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "data" / "processed" / "modular"
OUT = MOD / "r1_network_design.csv"
KANDY_BAND = "deep_tropical"          # 7.29 N
KANDY_LEVEL = 21.0                    # basin annual mean, ug/m3 (CONTEXT.md section 2)


def gain(a, b):
    return 100.0 * (a - b) / a


def main() -> None:
    d = pd.read_csv(MOD / "ladder_revalidated.csv")
    x = d[d.bottom == "Bud0c"].copy()
    x["g1"] = gain(x.rmse_Bud0, x.rmse_Bud1)
    x["g2"] = gain(x.rmse_Bud1, x.rmse_Bud2)
    x["g3"] = gain(x.rmse_Bud2, x.rmse_Bud3)

    rows = []
    print("R1 -- what does each instrument buy, and where?\n")
    print(f"  {'stratum':<16}{'n':>4}{'+2 stns':>10}{'+6 more':>10}{'+background':>13}")
    print("  " + "-" * 53)
    for lab, sub in [("POOLED", x)] + [(b, g) for b, g in x.groupby("band")]:
        if len(sub) < 3:
            continue
        r = dict(stratum=lab, n=len(sub),
                 step_first2=round(float(sub.g1.median()), 1),
                 step_next6=round(float(sub.g2.median()), 1),
                 step_background=round(float(sub.g3.median()), 1))
        rows.append(r)
        star = "  <- Kandy" if lab == KANDY_BAND else ""
        print(f"  {lab:<16}{len(sub):>4}{r['step_first2']:>9.1f}%{r['step_next6']:>9.1f}%"
              f"{r['step_background']:>12.1f}%{star}")

    k = next(r for r in rows if r["stratum"] == KANDY_BAND)
    p = next(r for r in rows if r["stratum"] == "POOLED")

    print("\n=== the inversion ===")
    print(f"  pooled          : background {p['step_background']:.1f}% > first stations "
          f"{p['step_first2']:.1f}%   -> chase a background station")
    print(f"  Kandy's band    : first stations {k['step_first2']:.1f}% > background "
          f"{k['step_background']:.1f}%   -> chase LOCAL stations")
    print("  The standing advice comes from the pooled row, computed mostly from other bands.")

    # ── what it means in ug/m3 at Kandy's level ───────────────────────────────────────────
    print(f"\n=== expected RMSE reduction at Kandy (level {KANDY_LEVEL} ug/m3, "
          f"{KANDY_BAND} band) ===")
    order = [("2 local stations (CEA Kandy AQMS)", k["step_first2"], "granted in principle 2026-08-12"),
             ("a regional background station (NBRO)", k["step_background"], "no free substitute (F.63)"),
             ("stations 3-8 in-city", k["step_next6"], "measured ~zero in every stratum")]
    for name, pct, note in sorted(order, key=lambda t: -t[1]):
        print(f"  {name:<38} {pct:5.1f}%   ~{KANDY_LEVEL * pct / 100:4.1f} ug/m3   ({note})")
        rows.append(dict(stratum="kandy_recommendation", n=k["n"], instrument=name,
                         step_pct=pct, abs_ug_m3=round(KANDY_LEVEL * pct / 100, 2), note=note))

    # ── instrument class ──────────────────────────────────────────────────────────────────
    print("\n=== which instrument class, if stations are added ===")
    for cls, g in x.groupby("cls"):
        w = float(g.w_Bud2.median())
        print(f"  {cls:<10} median shrinkage weight on the extra stations {w:.3f}  (n={len(g)})")
        rows.append(dict(stratum="instrument_class", n=len(g), instrument=cls, step_pct=w))
    print("  Low-cost sensors gain more from extra units because per-device error averages down;")
    print("  a reference monitor's third-to-eighth unit still buys close to nothing.")

    print("\n=== caveats that travel with this recommendation ===")
    print(f"  - the deep-tropical cell is n={k['n']} cities; subtropical and temperate are n=7.")
    print("  - PROVISIONAL pending C1: the deep-tropical background collapse is explained by the")
    print("    satellite level substituting for a background station, and C1 established that")
    print("    stream is a fused product trained on this panel's own monitors. If that")
    print("    substitution is leakage, the background rung is undervalued here.")
    print("  - 'stations 3-8 buy nothing' is robust across every learner tested (F.88, spread")
    print("    0.46 pp) and is the single most estimator-stable result in the ladder.")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
