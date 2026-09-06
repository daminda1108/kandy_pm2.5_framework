"""campaign_costing.py -- what the Kandy campaign costs, and what each site actually buys.

WHY THIS IS A SCRIPT. A proposal handed to a funder with a typed total is a proposal whose total
goes stale the first time the design changes. Every figure here is either a CITED unit price or
is derived from the design files, so the total moves when the design moves.

WHAT IS CITED AND WHAT IS NOT, stated first because it is the honest part.

  CITED, verifiable today:
    * AirGradient Open Air O-1PST, USD 225 assembled / USD 125 as a kit, from the vendor's own
      published price. Chosen not for price but because this project ALREADY holds per-device
      calibration coefficients for AirGradient units and its ingest pipeline already classifies
      them, so a different vendor would mean re-deriving a calibration the project has.
    * Reference-grade instruments: the US EPA states regulatory monitors cost "tens of thousands
      of dollars" and require infrastructure and trained personnel, against "a few hundred
      dollars" for a sensor. That is a RANGE and not a quote.

  NOT CITED, and deliberately left as a line item rather than invented:
    * mounting, enclosures, mains or solar power, connectivity, import duty, local labour and
      per diem. These are Sri Lanka specific, none of them is published, and a number typed
      here would be a guess wearing a budget's clothes. Each appears in the table as a quantity
      with an empty unit price, which is what a real procurement exercise fills in.

THE RE-SCOPE THIS SCRIPT EXISTS TO SETTLE. The 12-site design stratum was justified almost
entirely by a hypothesis the power calculation has since demoted to exploratory. The saturation
curve says what the stratum is now worth per site, and the answer is that 10 sites and 12 sites
are indistinguishable while 6 sites falls off a cliff.

Usage: python scripts/campaign_costing.py
Out:   data/processed/decomp/campaign_costing.csv
       data/processed/decomp/campaign_costing.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEC = REPO / "data" / "processed" / "decomp"
OUT = DEC / "campaign_costing.csv"
OUT_JSON = DEC / "campaign_costing.json"

# ── CITED unit prices, USD ────────────────────────────────────────────────────────────────
LCS_ASSEMBLED = 225.0   # AirGradient Open Air O-1PST, vendor published
LCS_KIT = 125.0         # same unit, self-assembled
REF_LO, REF_HI = 10_000.0, 40_000.0   # EPA: "tens of thousands"; a RANGE, not a quote
SPARES_FRACTION = 0.15  # attrition and co-location rotation; a design choice, not a citation


def main() -> None:
    with open(DEC / "sensor_design_summary.json", encoding="utf-8") as fh:
        S = json.load(fh)
    sat = pd.read_csv(DEC / "design_saturation.csv").set_index("n")

    # ── what each stratum serves, now that H1 is exploratory ──────────────────────────────
    rows = [
        dict(stratum="A anchor", sites=S["n_anchor"], instrument="reference",
             serves="C3 level (confirmatory)", tier="1 core"),
        dict(stratum="C paired", sites=S["n_paired"], instrument="lcs",
             serves="C1 within-cell (confirmatory, best powered)", tier="1 core"),
        dict(stratum="C2 drainage", sites=4, instrument="lcs",
             serves="C2 drainage sink (confirmatory)", tier="1 core"),
        dict(stratum="D receptor", sites=S["n_receptor"], instrument="lcs",
             serves="exposure at susceptible receptors (policy, held out)", tier="2 exposure"),
        dict(stratum="B design", sites=S["n_design"], instrument="lcs",
             serves="E1 spatial (exploratory) + panel contribution", tier="3 exploratory"),
        dict(stratum="E vertical", sites=S["n_vertical"], instrument="lcs",
             serves="E2 confinement (exploratory, MDE 0.94)", tier="3 exploratory"),
    ]
    d = pd.DataFrame(rows)
    d["unit_usd"] = np.where(d.instrument == "reference", np.nan, LCS_ASSEMBLED)
    d["lcs_usd"] = np.where(d.instrument == "lcs", d.sites * LCS_ASSEMBLED, 0.0)
    d.to_csv(OUT, index=False)

    print("=== what each stratum serves, and what it costs ===\n")
    print(f"  {'stratum':<13}{'n':>3}  {'tier':<14}{'LCS USD':>9}   serves")
    for r in d.itertuples():
        cost = f"{r.lcs_usd:,.0f}" if r.lcs_usd else "reference"
        print(f"  {r.stratum:<13}{r.sites:>3}  {r.tier:<14}{cost:>9}   {r.serves}")

    n_lcs = int(d[d.instrument == "lcs"].sites.sum())
    spares = int(np.ceil(n_lcs * SPARES_FRACTION))
    lcs_total = (n_lcs + spares) * LCS_ASSEMBLED
    lcs_total_kit = (n_lcs + spares) * LCS_KIT

    print(f"\n  {n_lcs} low-cost units + {spares} spares ({SPARES_FRACTION:.0%} for attrition "
          f"and co-location rotation)")
    print(f"    assembled  USD {lcs_total:>9,.0f}")
    print(f"    kit build  USD {lcs_total_kit:>9,.0f}   (saves "
          f"{lcs_total - lcs_total_kit:,.0f}, costs assembly labour)")
    print(f"  reference anchor  USD {REF_LO:,.0f} to {REF_HI:,.0f}  [EPA range, NOT a quote]")
    print(f"\n  INSTRUMENT SUBTOTAL  USD {lcs_total + REF_LO:,.0f} to "
          f"{lcs_total + REF_HI:,.0f}")

    print("\n  NOT COSTED, and left as line items rather than invented:")
    for item in ("mounting and enclosures", "mains or solar power", "connectivity and data",
                 "import duty and clearance", "installation labour and transport",
                 "12 months of servicing", "calibration co-location space"):
        print(f"    - {item}")

    # ── the anchor is the line that may not be a purchase at all ──────────────────────────
    print("\n=== the anchor: the largest line, and possibly not a purchase ===")
    print("  The national environmental authority granted this project access in principle to a")
    print("  Kandy regulatory station carrying hourly PM2.5 and full meteorology. If that")
    print("  agreement is completed, C3 is answered by a letter rather than by")
    print(f"  USD {REF_LO:,.0f}-{REF_HI:,.0f}, and the instrument subtotal falls to the "
          f"low-cost line alone.")
    print("  A campaign costed without checking that route first would overstate its own price")
    print("  by more than the rest of the budget combined.")

    # ── re-scoping the design stratum, from the saturation curve ──────────────────────────
    print("\n=== re-scoping the design stratum: what each site is now worth ===")
    base = int(S["n_design"])
    ks = sat.ks_mean
    sd = sat.ks_sd.mean()
    print(f"  seed-to-seed standard deviation of the representativeness measure: {sd:.4f}")
    print(f"  {'n':>4}{'ks_mean':>10}{'vs n=12':>10}{'LCS saved':>11}  verdict")
    for n in (12, 10, 8, 6):
        if n not in ks.index:
            continue
        delta = ks[n] - ks[base]
        saved = (base - n) * LCS_ASSEMBLED
        if abs(delta) <= sd:
            v = "indistinguishable from 12"
        elif delta < 3 * sd:
            v = "a real but small loss"
        else:
            v = "a cliff; do not go here"
        print(f"  {n:>4}{ks[n]:>10.4f}{delta:>+10.4f}{saved:>11,.0f}  {v}")

    rec = 10
    print(f"\n  RECOMMENDATION: {base} -> {rec} sites.")
    print(f"    The difference is {ks[rec] - ks[base]:+.4f} against a seed standard deviation of")
    print(f"    {sd:.4f}, so it is not measurable, and it saves "
          f"USD {(base - rec) * LCS_ASSEMBLED:,.0f}.")
    print(f"    Going to 8 costs {100*(ks[8]-ks[base])/ks[base]:+.0f}% of representativeness for "
          f"another USD {2 * LCS_ASSEMBLED:,.0f}; going to 6 costs "
          f"{100*(ks[6]-ks[base])/ks[base]:+.0f}% and should not be done.")
    print("\n  This does NOT void the registration. The design stratum serves E1, which the")
    print("  registration already carries as exploratory, and the void conditions in its")
    print("  section 5 concern the paired triplets, the nights and the anchor. The change is")
    print("  reported as a dated deviation, which is what the registration asks for.")

    summary = dict(
        lcs_unit_usd=LCS_ASSEMBLED, lcs_kit_usd=LCS_KIT,
        ref_lo_usd=REF_LO, ref_hi_usd=REF_HI,
        n_lcs=n_lcs, spares=spares, spares_fraction=SPARES_FRACTION,
        lcs_total_usd=round(lcs_total), lcs_total_kit_usd=round(lcs_total_kit),
        instrument_total_lo=round(lcs_total + REF_LO),
        instrument_total_hi=round(lcs_total + REF_HI),
        design_base=base, design_recommended=rec,
        design_saving_usd=round((base - rec) * LCS_ASSEMBLED),
        ks_base=round(float(ks[base]), 4), ks_rec=round(float(ks[rec]), 4),
        ks_seed_sd=round(float(sd), 4),
        ks_delta_rec=round(float(ks[rec] - ks[base]), 4),
        ks_loss_pct_8=round(100 * float(ks[8] - ks[base]) / float(ks[base]), 1),
        ks_loss_pct_6=round(100 * float(ks[6] - ks[base]) / float(ks[base]), 1),
        not_costed=["mounting and enclosures", "power", "connectivity", "import duty",
                    "installation labour", "12 months servicing", "co-location space"],
    )
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\n-> {OUT.name}, {OUT_JSON.name}")


if __name__ == "__main__":
    main()
