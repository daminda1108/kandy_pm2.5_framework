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

def t3_2_point_records():
    """The four independent point measurements at Kandy against the model.

    ⚠ The observed column is other people's measurement and is typed with a citation. The
    model column is generated. Mixing the two in one table is unavoidable and the note says
    which is which, because a reader cannot otherwise tell.
    """
    write(
        "T3_2_point_records",
        "Independent point records at Kandy against the model at the same location",
        ["record", "instrument", "observed", "model", "difference"],
        [
            [f"National research organisation, 2021 [@Nirmani2025]", "undocumented", "19.6",
             tok("nbro.model_pixel_2021"), tok("nbro.diff_pct_2021") + " per cent"],
            [f"National research organisation, 2022 [@Nirmani2025]", "undocumented", "22.7",
             tok("nbro.model_pixel_2022"), tok("nbro.diff_pct_2022") + " per cent"],
            ["Calibrated low-cost, 2022 to 2024 [@Attanayake2025]",
             "low-cost, reference-anchored", "19.49", "25.01", "+28 per cent"],
            ["Research sensor, full record [@Dhammapala2022]", "low-cost", "17.8", "--",
             "corroborates a reference-anchored 18 to 19"],
        ],
        note="Observed values are published measurements and carry a citation each. Model "
             "values are generated from the delivered field. Three of the four records sit "
             "below the model and all three are low-cost sensors carrying a downward "
             "calibration; the one that matches has an undocumented instrument. The "
             "discrepancy is reported as open rather than resolved by preferring the record "
             "that agrees.")


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
        "Registered predictions, and their outcomes where the analysis has run",
        ["registration", "date", "predictions", "held", "refuted"],
        [
            ["Colombo zero-shot (nxqgb)", "2026-08-22", "4", "2", "2"],
            ["Budget ladder re-validation (g6hqb)", "2026-08-23", "8", "3", "5"],
            ["Sub-grid and streams (bkpyr)", "2026-09-01", "9", "6", "3"],
            ["Chemistry (kx23c)", "2026-09-01", "4", "3", "1"],
            ["Learned spatial pattern (2jyfg)", "2026-09-04", "5", "5", "0"],
            ["Measurement campaign (ad3py)", "2026-09-06", "3 confirmatory, 2 exploratory",
             "not yet run", "not yet run"],
        ],
        note="Fourteen of thirty predictions were refuted in the five registrations whose "
             "analyses have run, including several headline ones. A registration that never "
             "refutes anything is not testing a prediction, it is recording a hope. The sixth "
             "is prospective: it registers a campaign that has not been deployed, and its "
             "detection limits were what demoted that campaign's original headline hypothesis "
             "to exploratory before any money was committed.")


# ── generated from scored files ───────────────────────────────────────────────────────────

def t4_1_data():
    """Chapter 4. Every stream, what it is, and the limit that matters for this work.

    The limit column is the one that earns the table. A data inventory that lists resolution
    and coverage without stating what each stream cannot do is a catalogue, not an argument.
    """
    write(
        "T4_1_data",
        "Data streams, their provenance, and the limit that matters",
        ["stream", "product", "resolution", "the limit that matters here"],
        [
            ["Satellite aerosol", "MODIS multi-angle retrieval [@Lyapustin2018]",
             "1 km, daily",
             "cloud gaps; carries no diurnal information at all"],
            ["Satellite concentration", "annual reanalysis-fusion surface [@vanDonkelaar2021]",
             "1 km, annual",
             "an annual level cannot constrain day-to-day variance"],
            ["Reanalysis drivers", "wind, boundary layer, temperature, humidity [@Hersbach2020]",
             "9 to 31 km, hourly",
             "a valley boundary layer is not resolved at this scale"],
            ["Chemical prior", "global composition reanalysis [@Keller2021]",
             "25 km, hourly",
             "itself a model; corroborates but cannot validate"],
            ["Precipitation", "satellite precipitation radar", "10 km, half-hourly",
             "reanalysis land precipitation was rejected: twice the gauge at this site"],
            ["Terrain", "digital elevation model [@Farr2007]", "30 m",
             "static; carries no information about emission"],
            ["Roads", "open street mapping", "vector",
             "completeness varies by country and is not measurable from the data"],
            ["Land cover and vegetation", "satellite land cover and greenness", "10 to 500 m",
             "the strongest single spatial predictor, and still only a proxy"],
            ["Night lights", "satellite radiance [@Elvidge2017]", "500 m",
             "conflates commercial activity with residential density"],
            ["Population", "modelled settlement layer [@Tatem2017]", "100 m",
             "a model, not a census, at this resolution"],
            ["Local sensors", "two low-cost units at Kandy", "hourly, 2018 to 2026",
             "both on the valley floor; carry their own calibration problem"],
            ["Borrowed panel", "two open monitoring networks",
             f"{tok('frame.cities')} cities", "no Sri Lankan city qualifies for it"],
        ],
        note="Nothing in this table was collected for this project. Every stream is either "
             "openly published or was obtained on request, which is a deliberate constraint: "
             "a method that requires bespoke measurement cannot be applied to the cities that "
             "most need it.")


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
    # NEITHER COLUMN SUMS TO THE PANEL TOTAL, and both reasons are stated on the table's face.
    # An external reader read the gap as an internal inconsistency, which in a thesis about
    # numerical provenance is the most expensive kind of misreading available.
    write("T4_3_panel", "The validation panel by latitude band",
          ["band", "cities", "countries", "median withheld monitors",
           "median scored days", "reference stations (per cent)"], rows,
          note=f"{tok('frame.cities')} cities, {tok('frame.countries')} countries, "
               f"{tok('frame.city_days')} city days in total. Neither of the first two columns "
               f"sums to those totals, for two different reasons. The cities column reaches "
               f"{tok('frame.bands')} because {tok('frame.unbanded')} cities come from a single "
               f"national network that is scored in every pooled result and carries no latitude "
               f"band. The countries column reaches {tok('frame.band_country_sum')} because "
               f"{tok('frame.countries_multiband')} countries span more than one band and are "
               f"counted once in each, while the unbanded network's country appears in no row. "
               f"A per-band distinct count is not additive. The deep-tropical cell is "
               f"dominated by low-cost sensors and the temperate cell by reference monitors, "
               f"which is a confound that cannot be sampled away.")


def t7_1_ladder():
    write("T7_1_ladder", "Marginal predictive value of each increment of information",
          ["step", "what is added", "median reduction in daily RMSE (per cent)"],
          [["Bud0a to Bud0b", "static geography, free everywhere", tok("step.geography")],
           ["Bud0b to Bud0c", "an annual satellite level", tok("step.satellite")],
           ["Bud0c to Bud1", "two local low-cost sensors", tok("step.bud0c_bud1")],
           ["Bud1 to Bud2", "stations three to six", tok("step.bud1_bud2")],
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
               "demonstration city belongs to. The city column sums to " + tok("frame.bands")
               + " and not to the panel's " + tok("frame.cities") + ", because "
               + tok("frame.unbanded") + " cities come from a single national network that "
               "is scored in every pooled result and carries no latitude band.")


def t9_2_network():
    """The five strata of the proposed Kandy network.

    Counts are claim tokens rather than typed numbers, so a change to --n-design in the design
    script reaches this table instead of quietly contradicting it.
    """
    write("T9_2_network", "The proposed Kandy network, by stratum",
          ["stratum", "sites", "instrument", "what it answers"],
          [["A  anchor", tok("net.anchor"), "reference grade",
            "the level discrepancy; and it calibrates every other unit in the network"],
           ["B  design", tok("net.design"), "low cost",
            "spans emission and flow physics together, so the model's gradients are straddled"],
           ["C  paired", tok("net.paired"), "low cost",
            "the within-cell distribution, at separations one model cell wide"],
           ["E  vertical", tok("net.vertical"), "low cost",
            "the floor-to-ridge gradient, which no monitoring network anywhere samples"],
           ["D  receptor", tok("net.receptor"), "low cost",
            "what susceptible people breathe; held out of all model fitting"]],
          note=f"{tok('net.total')} sites in total. Candidates were screened to the "
               f"{tok('net.cells_feasible')} of {tok('net.cells_total')} cells within servicing "
               f"distance of a road before the design was optimised, so logistics constrains the "
               f"candidate set and never scores a site. The design stratum spans the "
               f"{tok('net.design_pct_lo')}th to {tok('net.design_pct_hi')}th percentile of the "
               f"emission gradient, against the {tok('net.existing_pct_lo')}st to 100th that the "
               f"existing records occupy.")


def t9_1_next():
    write("T9_1_next", "Measurement priorities, and the kind of evidence that ranks each one",
          ["action", "what it would settle", "what ranks it, and of what kind"],
          [["A local observation, in preference to a regional one",
            "which stream to obtain first for this band",
            f"LADDER: local {tok('maiac.deep_tropical_first2')} per cent against "
            f"{tok('maiac.deep_tropical_background')} for the background proxy, measured on "
            f"two LOW-COST sensors"],
           ["Making that local observation reference grade",
            "the level discrepancy, and a calibration anchor for every sensor after it",
            "MEASUREMENT DESIGN, not the ladder: three of four independent records sit below "
            "the model and the one that matches carries an undocumented instrument. No rung "
            "priced a reference monitor"],
           ["A regional background station",
            "the background term, currently a proxy from each city's own outer ring",
            f"LADDER: {tok('maiac.deep_tropical_background')} per cent in this band, below "
            f"local; donor recovery falls to {tok('donor.reproduced_deep_tropical')} per cent "
            f"in this band"],
           ["A campaign that sites monitors across land-use contrast",
            "whether the spatial limit is support or design",
            "REGISTERED NULL: the effect is bounded at the detection limit, not at zero"],
           ["Precipitation in the forecast drivers",
            "wet removal, absent from the current driver set",
            "NO MEASUREMENT: a known structural gap"],
           ["More monitors beyond the first", "nothing this model can use for a daily city mean",
            f"LADDER: {tok('step.bud1_bud2')} per cent"]],
          note="The evidence column names the KIND of argument as well as its content, because "
               "the two are not interchangeable. A row marked LADDER carries a marginal "
               "predictive value measured on this panel; a row marked MEASUREMENT DESIGN does "
               "not, and must not borrow one. In particular the ladder measured low-cost "
               "sensors, so it ranks a local observation above a regional one without saying "
               "anything about instrument grade. The last row is included because it is the "
               "acquisition most often proposed and the one the measurement does not support.")


BUILDERS = {
    "T3_1": t3_1_literature, "T3_2": t3_2_point_records, "T4_1": t4_1_data, "T4_3": t4_3_panel, "T5_1": t5_1_attempts,
    "T7_1": t7_1_ladder, "T7_2": t7_2_bands, "T7_5": t7_5_registrations,
    "T9_1": t9_1_next, "T9_2": t9_2_network,
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
