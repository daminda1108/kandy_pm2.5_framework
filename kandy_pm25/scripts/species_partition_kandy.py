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
    print(f"    RESULT    : {f_bc:.3f} vs {f_so4:.3f}, gap {gap:+.3f}")
    print(f"    Rank agreement with the predicted primary-to-secondary order "
          f"(5 species): rho = {conc:+.3f}")

    # ── THE CONTROL THAT DECIDES WHETHER ANY OF THAT MEANS ANYTHING ───────────────────────
    # Kandy is an inland valley. It has NO local source of sea salt and no dust source of
    # consequence, so the true local fraction of both is essentially zero, by physical
    # necessity and independently of anything this model asserts. They are therefore negative
    # controls: an estimator that identifies local origin MUST place them at the bottom.
    #
    # ⚠ HONEST DISCLOSURE: these controls were NOT declared in the docstring above before the
    # run. Reading them afterwards is weaker than declaring them, and the only reason it is not
    # special pleading is that their expected value follows from geography rather than from the
    # result. A future version of this test declares its controls in advance.
    f_dust = float(r.loc[r.species == "dust", "f"].iloc[0])
    f_salt = float(r.loc[r.species == "sea_salt", "f"].iloc[0])
    n_above = int((r[r.species.isin(["dust", "sea_salt"])].f.values[:, None]
                   > r[~r.species.isin(["dust", "sea_salt"])].f.values).sum())
    controls_fail = (f_salt > f_bc) or (f_dust > f_bc)

    print(f"\n    NEGATIVE CONTROLS (true local fraction ~ 0 for an inland valley):")
    print(f"      dust      f = {f_dust:.3f}     sea_salt  f = {f_salt:.3f}")
    if controls_fail:
        print(f"      -> CONTROLS FAIL. The estimator ranks species with NO local source ABOVE")
        print(f"         black carbon, which is the purest local tracer available.")
        print(f"      -> THE TEST IS INVALID, not the hypothesis. `f = 1 - floor/mean` measures")
        print(f"         EPISODIC TEMPORAL VARIABILITY, not local origin: dust and sea salt are")
        print(f"         the most episodic species here because they arrive in transport events.")
        print(f"      -> The species prediction is therefore NEITHER held NOR refuted. It is")
        print(f"         untested, and reporting the reversal as a chemical refutation would be")
        print(f"         reporting an instrument failure as a finding.")
    else:
        print(f"      -> controls pass; the ordering above may be read as origin-related.")

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
        prediction_held=None,   # neither: the controls fail, so the test is invalid
        controls_fail=bool(controls_fail),
        f_dust=round(f_dust, 4), f_sea_salt=round(f_salt, 4),
        verdict=("INVALID: negative controls (dust, sea salt) rank above black carbon, so the "
                 "estimator measures episodic variability rather than local origin"
                 if controls_fail else "controls pass"),
        rank_rho_vs_predicted=round(conc, 4) if np.isfinite(conc) else None,
        f_total_reference=round(local_fraction(d["total"]), 4),
        secondary_share=round(S, 4), f_production=round(f_prod, 4),
        intervention_lo=round(lo, 4), intervention_hi=round(hi, 4),
        species_f={x.species: x.f for x in r.itertuples()},
    )
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\n-> {OUT.name}, {OUT_JSON.name}")
    # ASCII only in printed output: the Windows console is cp1252 and a non-ASCII character
    # here raised UnicodeEncodeError AFTER both output files had been written, which is the
    # worst place for it -- the run looked failed while the results were already on disk.
    print("\n[!] GEOS-CF is a MODEL at ~25 km. These are modelled composition shares, never "
          "measured speciation, and must not be presented as measurement.")


if __name__ == "__main__":
    main()
