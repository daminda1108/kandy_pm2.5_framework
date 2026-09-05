"""species_partition_kandy.py -- is the local/regional split CHEMICALLY coherent, and what does
it license about intervention?

THE PREDICTION IS STATED HERE, IN THIS DOCSTRING, AND THIS FILE IS COMMITTED BEFORE THE SCRIPT
IS RUN. That is the same device pull_panel_speciation.py used on 2026-09-01, and it is what
makes a direction citable later as having been fixed in advance. It is weaker than a lodged
pre-registration and is not called one.

────────────────────────────────────────────────────────────────────────────────────────────
PART B -- the decomposition makes a chemical prediction, and chemistry can falsify it
────────────────────────────────────────────────────────────────────────────────────────────

The model splits concentration into a spatially uniform background B(t) and a locally generated
increment. Chapter 6 justifies B as AGED, REGIONALLY TRANSPORTED material and the increment as
FRESHER, LOCALLY GENERATED material. That is a chemical claim and it has never been tested
species by species.

Atmospheric chemistry orders the species unambiguously and the ordering was not chosen to fit
any result:

  * BLACK CARBON is emitted directly, is chemically inert, and has no secondary source at all.
    It is the purest available tracer of fresh LOCAL combustion.
  * SULPHATE is overwhelmingly secondary, formed from SO2 over hours to days, which is long
    enough to travel hundreds of kilometres. It is the purest available tracer of AGED REGIONAL
    material.
  * SECONDARY ORGANIC sits with sulphate by construction.
  * ORGANIC CARBON is mixed: a primary combustion component plus a secondary one.
  * NITRATE is secondary but semi-volatile and can form closer to source.
  * DUST and SEA SALT are natural and predominantly regional in this basin.

PREDICTION (fixed here, before running): applying ONE estimator to every species,
`f_black_carbon` is substantially greater than `f_sulphate`, and the species order by f follows
the primary-to-secondary order above.

  * If it holds, the decomposition's central assumption is CHEMICALLY COHERENT. The split is
    tracking something real about origin rather than only satisfying an arithmetic constraint.
  * If f is flat across species, the split is chemically arbitrary and the thesis must say so.
  * If it INVERTS, the assumption is refuted.

⚠ WHAT THIS IS NOT. `f` per species here is NOT the production partition and does not replace
it. It is one consistent estimator applied across species so that the ORDERING can be read. The
absolute values are estimator-dependent and are reported only to make the ordering legible.

────────────────────────────────────────────────────────────────────────────────────────────
PART C -- bounding what an intervention could actually remove
────────────────────────────────────────────────────────────────────────────────────────────

The thesis WITHDREW the claim that removing every local source would remove about half of
Kandy's concentration, because the model has no chemistry and part of the local increment is
material formed in the atmosphere rather than emitted into it. Withdrawal leaves a policy reader
with nothing. Chemistry can replace it with a bound.

With f the local share and S the secondary share of total mass, the locally emitted PRIMARY
share L is constrained from both directions without any further assumption (Frechet bounds):

    L <= min(f, 1 - S)          it cannot exceed the local material, nor the primary material
    L >= max(0, f - S)          local secondary cannot exceed all secondary

The lower bound is what responds IMMEDIATELY to local emission control. The upper bound is what
would respond if every locally formed secondary particle also disappeared. The gap between them
is exactly what cannot be resolved without speciated local measurement, which is the measurement
Chapter 9 already asks for.

Usage: python scripts/species_partition_kandy.py
Out:   data/processed/decomp/species_partition_kandy.csv
       data/processed/decomp/species_partition_summary.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
MOD = REPO / "data" / "processed" / "modular"
SPEC = DEC / "kandy_geoscf_speciation_daily.csv"
OUT = DEC / "species_partition_kandy.csv"
OUT_JSON = DEC / "species_partition_summary.json"

# The species, in the PREDICTED order from most local-primary to most regional-secondary.
# Fixed in the docstring above before running.
SPECIES = ["black_carbon", "organic_carbon", "nitrate", "secondary_organic", "sulphate",
           "dust", "sea_salt"]
PREDICTED_ORDER = ["black_carbon", "organic_carbon", "nitrate", "secondary_organic", "sulphate"]

# ONE estimator, applied identically to every species. The background floor is a rolling low
# quantile: material that is present even on the cleanest days of a season is what arrives from
# outside, and what rises above it is what the basin generated. WINDOW is centred and long
# enough to carry a season without tracking a synoptic event.
WINDOW_DAYS = 61
FLOOR_Q = 0.10


def local_fraction(x: pd.Series) -> float:
    """f = 1 - (rolling regional floor) / mean. Identical for every species."""
    floor = x.rolling(WINDOW_DAYS, center=True, min_periods=WINDOW_DAYS // 2).quantile(FLOOR_Q)
    return float(1.0 - (floor.mean() / x.mean()))


def main() -> None:
    d = pd.read_csv(SPEC, parse_dates=["date"]).sort_values("date").set_index("date")
    print("=== species-resolved partition at Kandy ===")
    print(f"    {len(d)} days, {d.index.min().date()} to {d.index.max().date()}")
    print(f"    estimator: f = 1 - (centred {WINDOW_DAYS}-day rolling p{int(FLOOR_Q*100)}) / mean,"
          f" identical for every species\n")

    rows = []
    for s in SPECIES:
        if s not in d.columns:
            continue
        rows.append(dict(species=s, mean=round(float(d[s].mean()), 4),
                         share_of_total=round(float(d[s].mean() / d["total"].mean()), 4),
                         f=round(local_fraction(d[s]), 4)))
    r = pd.DataFrame(rows).sort_values("f", ascending=False).reset_index(drop=True)
    r["f_total_reference"] = round(local_fraction(d["total"]), 4)
    r.to_csv(OUT, index=False)

    print(f"    {'species':<19}{'mean':>8}{'share':>8}{'f':>9}")
    for x in r.itertuples():
        print(f"    {x.species:<19}{x.mean:8.3f}{x.share_of_total:8.3f}{x.f:9.3f}")
    print(f"    {'(total, reference)':<19}{d['total'].mean():8.3f}{1.0:8.3f}"
          f"{local_fraction(d['total']):9.3f}")

    f_bc = float(r.loc[r.species == "black_carbon", "f"].iloc[0])
    f_so4 = float(r.loc[r.species == "sulphate", "f"].iloc[0])
    gap = f_bc - f_so4
    ranked = [s for s in r.species if s in PREDICTED_ORDER]
    conc = float(pd.Series(range(len(PREDICTED_ORDER)), index=PREDICTED_ORDER)
                 .reindex(ranked).corr(pd.Series(range(len(ranked)), index=ranked),
                                       method="spearman"))

    print(f"\n    PREDICTION: f(black_carbon) > f(sulphate).")
    print(f"    RESULT    : {f_bc:.3f} vs {f_so4:.3f}, gap {gap:+.3f} -> "
          f"{'HELD' if gap > 0 else 'REFUTED'}")
    print(f"    Rank agreement with the predicted primary-to-secondary order "
          f"(5 species): rho = {conc:+.3f}")

    # ── PART C ────────────────────────────────────────────────────────────────────────────
    sec_species = ["sulphate", "nitrate", "secondary_organic"]
    S = float(d[sec_species].sum(axis=1).mean() / d["total"].mean())
    claims = json.load(open(MOD / "claims.json", encoding="utf-8"))["claims"]
    f_prod = float(claims["partition.f"]["value"])
    lo = max(0.0, f_prod - S)
    hi = min(f_prod, 1.0 - S)

    print(f"\n=== what an intervention could remove (Frechet bounds) ===")
    print(f"    local share f (production)        : {f_prod:.4f}")
    print(f"    secondary share S (GEOS-CF, model): {S:.4f}")
    print(f"    locally emitted PRIMARY share     : {lo:.4f} to {hi:.4f}")
    print(f"    -> at least {100*lo:.1f}% of concentration is local primary material and")
    print(f"       responds immediately; at most {100*hi:.1f}% responds, and only if every")
    print(f"       locally formed secondary particle disappears too.")

    summary = dict(
        days=int(len(d)), window_days=WINDOW_DAYS, floor_q=FLOOR_Q,
        f_black_carbon=round(f_bc, 4), f_sulphate=round(f_so4, 4),
        f_gap_bc_minus_so4=round(gap, 4),
        prediction_held=bool(gap > 0),
        rank_rho_vs_predicted=round(conc, 4) if np.isfinite(conc) else None,
        f_total_reference=round(local_fraction(d["total"]), 4),
        secondary_share=round(S, 4), f_production=round(f_prod, 4),
        intervention_lo=round(lo, 4), intervention_hi=round(hi, 4),
        species_f={x.species: x.f for x in r.itertuples()},
    )
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\n-> {OUT.name}, {OUT_JSON.name}")
    print("\n⚠ GEOS-CF is a MODEL at ~25 km. These are modelled composition shares, never "
          "measured speciation, and must not be presented as measurement.")


if __name__ == "__main__":
    main()
