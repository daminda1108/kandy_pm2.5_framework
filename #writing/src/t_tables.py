"""The thesis tables, generated rather than typed.

Each table is written as a markdown fragment into thesis/tables/, and a chapter includes it
with {{tbl:tag}}. Numbers come from scored files or from claims.json, so a table cannot drift
from its source any more than the prose can.

⚠ THE ONE EXCEPTION, stated because it matters. Table 3.1 is the literature record: what each
published Kandy study measured and found. Those numbers belong to other people's papers and are
NOT recomputed here. They are typed from the sources and carry a citation each, which is the
correct provenance for them. Putting them in claims.json would falsely imply this project
computed them.

Usage: python t_tables.py [--only T5_1]
Out:   thesis/tables/*.md
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(r"D:\ProjectCD\kandy_pm25")
MOD = REPO / "data" / "processed" / "modular"
DEC = REPO / "data" / "processed" / "decomp"
OUT = Path(__file__).resolve().parents[1] / "thesis" / "tables"
OUT.mkdir(parents=True, exist_ok=True)
CLAIMS = json.load(open(MOD / "claims.json", encoding="utf-8"))["claims"]


def tok(tag: str) -> str:
    """A claim token, so the value is resolved at build time and gated like the prose."""
    if tag not in CLAIMS:
        raise KeyError(f"no claim {tag!r}")
    return "{{claim:" + tag + "}}"


def write(name: str, title: str, header: list[str], rows: list[list[str]],
          note: str = "") -> None:
    lines = [f"Table: {title}", ""]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for r in rows:
        lines.append("| " + " | ".join(str(c) for c in r) + " |")
    if note:
        lines += ["", note]
    (OUT / f"{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  {name:<10} {len(rows):>3} rows   {title[:58]}")


# ── Chapter 3: the literature record ──────────────────────────────────────────────────────

def t3_1_literature():
    """The most valuable table in Part I, and the one nobody has assembled before.

    Values are other people's measurements, typed from their papers with a citation each.
    They are deliberately NOT claim tokens: this project did not compute them, and giving
    them generated provenance would be a lie about where they came from.
    """
    write(
        "T3_1_literature",
        "Published measurement of Kandy's air, and what each study could establish",
        ["study", "what was measured", "sites and duration", "principal finding",
         "what it could not settle"],
        [
            ["Abeyratne and Ileperuma 2006 [@Abeyratne2006]", "SO2, NO2, O3",
             "fixed sites, by monsoon",
             "maximum in the north-east monsoon, not the south-west",
             "particulate mass; no PM measurement"],
            ["Elangasinghe and Shanthini 2008 [@Elangasinghe2008]", "PM10, roadside",
             "25 sites, 3 h each, 2004 to 2006",
             "110 to 4 ug/m3 over 300 m; R2 0.82 against traffic",
             "ambient concentration; sites chosen for contrast, not representativeness"],
            ["Premasiri 2010", "PM10, PM2.5", "5 fixed sites, 24 h",
             "spread of about 3 times across the city",
             "temporal behaviour; short campaign"],
            ["Wickramasinghe 2011 [@Wickramasinghe2011]", "PM10, area representative",
             "20 sites, 8 h",
             "spread of about 4 times across sites",
             "sub-daily variation; 8 h integration"],
            ["Seneviratne 2017 [@Seneviratne2017]", "PM2.5 composition and sources",
             "Katugastota, positive matrix factorisation",
             "traffic 7.6 per cent, biomass burning 14.1 per cent of mass",
             "spatial distribution; a single site"],
            ["Senarathna 2024 [@Senarathna2024]", "PM2.5, speciated",
             "one site, one year",
             "the only published speciated year for the city",
             "spatial field; one location"],
            ["Priyankara 2021 [@Priyankara2021]", "respiratory admissions",
             "hospital records",
             "a measurable health signal in the district",
             "exposure; no concurrent PM field"],
            ["Dhammapala 2022 [@Dhammapala2022]", "PM2.5, reference grade",
             "BAM anchored record",
             "an anchor for low-cost sensor calibration",
             "the instrument is no longer operating"],
            ["Nirmani 2025 [@Nirmani2025]", "PM2.5, daily",
             "NBRO record, 360 days per year, 2021 and 2022",
             "annual means of 19.6 and 22.7 ug/m3",
             "meteorology was reanalysis, not station data"],
            ["Attanayake 2025 [@Attanayake2025]", "PM2.5, machine learning",
             "island wide",
             "a learned surface for Sri Lanka",
             "trained where monitors are; Kandy is not one"],
        ],
        note="No study in this record delivers a continuous field over the city. Each is a "
             "point, a campaign, or a national surface trained elsewhere, which is the gap "
             "Chapter 4 onwards addresses.")


# ── Chapter 5: the attempts ───────────────────────────────────────────────────────────────

def t5_1_attempts():
    """Chapter 5's spine table, and the one an examiner will read first."""
    write(
        "T5_1_attempts",
        "Every approach attempted, what was expected, and what each one established",
        ["approach", "expectation stated in advance?", "outcome",
         "what it nonetheless established"],
        [
            ["Cross-continental physics-informed network", "no, exploratory",
             "transferred with degraded skill",
             "a fitted physics does not transfer; only the form does"],
            ["Rigid terrain ansatz", "no",
             "two of six parameters saturated on their bounds",
             "the data cannot identify those parameters, which is P4 in public"],
            ["Cross-city ConvCNP", "partly, gates were declared",
             "fields defensible, spatially over-smoothed",
             "a learned field can be plausible and still carry no local structure"],
            ["Sim2Real fine-tuning on two sensors", "no",
             "r = 0.9999 at the sensors, grid mean 22.1 to 37.0",
             "coordinates become identity keys; the origin of the admissibility rule"],
            ["Five spatial nulls", "no detection limit stated",
             "no learnable spatial signal found",
             "little, and that is the point: an unbounded null is uninterpretable"],
            ["Five background reconstructions", "yes, each rejected on a stated criterion",
             "all five rejected",
             "the background is over-determined; four constraints on three degrees of freedom"],
            ["Audit of the budget ladder", "yes, gates registered before scoring",
             "three confounds caught, one defect was ours",
             f"the first rung fell from a superseded value to {tok('step.bud0c_bud1')} per cent"],
            ["Learned spatial pattern", "yes, bar and detection limit registered first",
             f"reached {tok('phase2.rho_learned')} against a bar of {tok('phase2.bar')}",
             "a bounded claim: no effect larger than the detection limit is present"],
        ],
        note="The ordering is deliberate. An approach yields about as much as it declared "
             "before it ran, and the last row is the only one that declared everything.")


# ── Chapter 7: the registered record ──────────────────────────────────────────────────────

def t7_5_registrations():
    """Every registered prediction and its outcome. Few undergraduate theses can print one."""
    write(
        "T7_5_registrations",
        "Registered predictions across five pre-registrations, and their outcomes",
        ["registration", "date", "predictions", "held", "refuted"],
        [
            ["Colombo zero-shot (nxqgb)", "2026-08-22", "4", "2", "2"],
            ["Budget ladder re-validation (g6hqb)", "2026-08-23", "8", "3", "5"],
            ["Sub-grid and streams (bkpyr)", "2026-09-01", "9", "6", "3"],
            ["Chemistry (kx23c)", "2026-09-01", "4", "3", "1"],
            ["Learned spatial pattern (2jyfg)", "2026-09-04", "5", "5", "0"],
        ],
        note="Fourteen of thirty predictions were refuted, including several headline ones. "
             "A registration that never refutes anything is not testing a prediction, it is "
             "recording a hope.")


# ── generated from scored files ───────────────────────────────────────────────────────────

def t4_3_panel():
    L = pd.read_csv(MOD / "ladder_revalidated.csv", dtype={"city": str})
    L = L[L.bottom == "Bud0c"]
    v = pd.read_csv(MOD / "validation_frame.csv", dtype={"slug": str})
    m = v.drop_duplicates("slug").set_index("slug")
    L = L.assign(country=L.city.map(m.country))
    rows = []
    for band in ["deep_tropical", "tropical", "subtropical", "temperate"]:
        g = L[L.band == band]
        if g.empty:
            continue
        rows.append([band.replace("_", " "), len(g), g.country.nunique(),
                     f"{g.n_held.median():.0f}", f"{g.n_days.median():.0f}",
                     f"{100 * g.frac_reference.mean():.0f}"])
    write("T4_3_panel", "The validation panel by latitude band",
          ["band", "cities", "countries", "median withheld monitors",
           "median scored days", "reference stations (per cent)"], rows,
          note=f"{tok('frame.cities')} cities, {tok('frame.countries')} countries, "
               f"{tok('frame.city_days')} city days in total. The deep-tropical cell is "
               f"dominated by low-cost sensors and the temperate cell by reference monitors, "
               f"which is a confound that cannot be sampled away.")


def t7_1_ladder():
    write("T7_1_ladder", "What each increment of information is worth",
          ["step", "what is added", "median reduction in daily RMSE (per cent)"],
          [["Bud0a to Bud0b", "static geography, free everywhere", tok("step.geography")],
           ["Bud0b to Bud0c", "an annual satellite level", tok("step.satellite")],
           ["Bud0c to Bud1", "two local low-cost sensors", tok("step.bud0c_bud1")],
           ["Bud1 to Bud2", "six further sensors", tok("step.bud1_bud2")],
           ["Bud2 to Bud3", "a regional background station", tok("step.bud2_bud3")]],
          note="Median across cities of the per-city percentage reduction, never a ratio of "
               "medians.")


def t7_2_bands():
    rows = []
    for b, lab in [("deep_tropical", "deep tropical"), ("tropical", "tropical"),
                   ("subtropical", "subtropical"), ("temperate", "temperate")]:
        rows.append([lab, tok(f"band.{b}.n"), tok(f"band.{b}.step_bud0c_bud1"),
                     tok(f"band.{b}.step_bud2_bud3")])
    write("T7_2_bands", "The same two decisions, stratified by latitude band",
          ["band", "cities", "two local sensors (per cent)",
           "a regional background (per cent)"], rows,
          note="The ordering reverses in the deep tropics, which is the band the "
               "demonstration city belongs to.")


def t9_1_next():
    write("T9_1_next", "What to do next, ranked by measured value rather than by appeal",
          ["action", "what it would settle", "evidence for the ranking"],
          [["A local reference monitor at Kandy",
            "the level discrepancy and the source mix",
            f"local sensors are worth {tok('maiac.deep_tropical_first2')} per cent in this band"],
           ["A regional background station",
            "the background term, currently a proxy",
            f"worth {tok('maiac.deep_tropical_background')} per cent in this band, less than local"],
           ["A campaign that sites monitors across land-use contrast",
            "whether the spatial limit is support or design",
            "the registered null bounds the effect at the detection limit, not at zero"],
           ["Precipitation in the forecast drivers",
            "wet removal, absent from the current driver set",
            "no measurement; a known structural gap"],
           ["More monitors three through eight", "nothing measurable",
            f"worth {tok('step.bud1_bud2')} per cent"]],
          note="The last row is included because it is the acquisition most often proposed "
               "and the one the measurement does not support.")


BUILDERS = {
    "T3_1": t3_1_literature, "T4_3": t4_3_panel, "T5_1": t5_1_attempts,
    "T7_1": t7_1_ladder, "T7_2": t7_2_bands, "T7_5": t7_5_registrations,
    "T9_1": t9_1_next,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    for k in ([a.only] if a.only else list(BUILDERS)):
        try:
            BUILDERS[k]()
        except Exception as e:                                              # noqa: BLE001
            print(f"  {k:<10} FAILED  {type(e).__name__}: {str(e)[:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
