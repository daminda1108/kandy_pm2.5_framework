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
             "110 at a garden entrance to about 4 ug/m3 300 m inside it; R2 0.82 against traffic "
             "at 20 roadside sites",
             "ambient concentration; sites chosen for contrast, not representativeness"],
            # A row "Premasiri 2010, PM10 and PM2.5, 5 fixed sites" was removed 2026-09-19: the
            # paper it named is a Colombo study (Fort and Colombo 7, around 2000), not Kandy.
            ["Wickramasinghe 2011 [@Wickramasinghe2011]", "PM10 and bound PAHs",
             "20 sites, 8 h each, 2008 to 2009",
             "PM10 of 55 to 221 ug/m3, a spread of about 4 times across sites",
             "sub-daily variation; daytime 8 h samples only"],
            ["Seneviratne 2017 [@Seneviratne2017]", "PM2.5 composition and sources",
             "Katugastota, positive matrix factorisation",
             "traffic 7.6 per cent, biomass burning 14.1 per cent of mass",
             "spatial distribution; a single site"],
            ["Senarathna 2024 [@Senarathna2024]", "PM2.5, low-cost sensor",
             "one site (NIFS), 2019",
             "morning and evening peaks, afternoon minimum; weekly and monthly patterns",
             "spatial field; one location and one low-cost instrument"],
            ["Priyankara 2021 [@Priyankara2021]", "respiratory admissions",
             "hospital records",
             "a measurable health signal in the district",
             "exposure; no concurrent PM field"],
            ["Dhammapala 2022 [@Dhammapala2022]", "PM2.5, low-cost sensors",
             "island wide, including Akurana; anchored to the Colombo reference monitor",
             "a reference-anchored check on low-cost records near Kandy",
             "the reference monitor is in Colombo, not Kandy"],
            ["Nirmani 2025 [@Nirmani2025]", "PM2.5, daily",
             "NBRO record, 360 days per year, 2021 and 2022",
             "annual means of 19.6 and 22.7 ug/m3",
             "meteorology was model output (Open-Meteo), not station observations"],
            ["Attanayake 2025 [@Attanayake2025]", "PM2.5, machine learning",
             "24 low-cost sensors island wide, calibrated against reference monitors in Colombo and "
             "at Torrington Park, Kandy",
             "a learned surface for Sri Lanka",
             "a national surface; the Torrington Park monitor is no longer operating"],
        ],
        note="No study in this record delivers a continuous field over the city. Each is a "
             "point, a campaign, or a national surface, which is the gap the rest of this "
             "thesis addresses.")


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

REGISTRY = Path(__file__).resolve().parents[1] / "registrations.json"

_WORDS = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
          "fourteen fifteen sixteen seventeen eighteen nineteen twenty").split()
_TENS = {20: "twenty", 30: "thirty", 40: "forty", 50: "fifty", 60: "sixty"}


def _spell(n: int) -> str:
    if n >= 100:                     # house style: numerals from 100 up
        return str(n)
    if n < len(_WORDS):
        return _WORDS[n]
    t, u = divmod(n, 10)
    return _TENS[t * 10] + ("" if u == 0 else "-" + _WORDS[u])


def t7_5_registrations():
    """Every registered prediction and its outcome, read from registrations.json.

    The list used to be typed here, and it went stale twice: it stopped at six registrations
    when there were eleven, and its note said fourteen refuted where its own rows gave eleven.
    Every count now comes from the registry, and the note is composed from the same numbers, so
    the table and its note cannot disagree with each other or with the record.
    """
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if not reg.get("verified_against_osf"):
        raise RuntimeError("registrations.json is not marked verified against OSF; "
                           "refusing to print a registration table from an unchecked list")
    recs = reg["registrations"]
    run = [r for r in recs if r["refuted"] is not None]
    pending = [r for r in recs if r["refuted"] is None]
    for r in run:
        other = r["predictions"] - r["held"] - r["refuted"]
        if other < 0 or (r.get("not_tested") or 0) > other:
            raise ValueError(f"{r['osf']}: held + refuted + not tested exceeds predictions")
        if "descriptive" in r and r["held"] + r["refuted"] + (r.get("not_tested") or 0) + r["descriptive"]                 != r["predictions"]:
            raise ValueError(f"{r['osf']}: held + refuted + not tested + descriptive != predictions")

    rows = []
    for r in recs:
        label = f"{r.get('label', r['name'])} ({r['osf']})"
        if r["refuted"] is not None:
            rows.append([label, r["date"], str(r["predictions"]), str(r["held"]),
                         str(r["refuted"]), str(r["predictions"] - r["held"] - r["refuted"])])
            continue
        conf = r.get("confirmatory")
        if r["predictions"] == 0:
            preds = "none; exploratory analysis only"
        elif conf is not None:
            preds = f"{r['predictions']} ({conf} confirmatory)"
        else:
            preds = str(r["predictions"])
        state = r.get("pending_as", "not yet run")
        rows.append([label, r["date"], preds, state, state, state])

    n_pred = sum(r["predictions"] for r in run)
    n_ref = sum(r["refuted"] for r in run)
    zero = [r for r in run if r["refuted"] == 0]
    tot = reg.get("_totals_over_analyses_that_have_run")
    if tot and (tot["with_outcomes"], tot["predictions"], tot["refuted"]) != (
            len(run), n_pred, n_ref):
        raise ValueError("registrations.json: _totals block disagrees with its own rows")

    campaign = [r for r in pending if r.get("kind") == "campaign"]
    curve = [r for r in pending if r.get("kind") == "spatial_curve"]
    if len(campaign) + len(curve) != len(pending):
        raise ValueError("a pending registration has no 'kind'; the note cannot describe it")

    note = (f"{_spell(len(recs)).capitalize()} registrations were lodged. In the "
            f"{_spell(len(run))} whose analyses have run, {_spell(n_ref)} of "
            f"{_spell(n_pred)} predictions were refuted, including several headline ones. "
            f"{_spell(len(zero)).capitalize()} refuted nothing because what they predicted "
            f"was a null, and the null held. A programme that never refuted anything would "
            f"be recording hopes rather than testing predictions.")
    if campaign:
        note += (" The Kandy measurement design is still under development and is not "
                 "reported in this thesis.")
    if curve:
        note += (f" {_spell(len(curve)).capitalize()} amendments to the spatial learning curve "
                 "carry no outcome of their own; their analyses are scored within the curve's "
                 "registrations. The last column counts predictions that were not tested or were "
                 "registered as two-sided or descriptive.")
    write(
        "T7_5_registrations",
        "Registered predictions, and their outcomes where the analysis has run",
        ["registration", "date", "predictions", "held", "refuted", "not tested or two-sided"],
        rows, note=note)


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
               f"{tok('frame.city_days')} city days in total. The cities column sums to the "
               f"panel total. The countries column reaches {tok('frame.band_country_sum')} "
               f"because {tok('frame.countries_multiband')} countries span more than one band "
               f"and are counted once in each; a per-band distinct count is not additive. The "
               f"cities of the national network of China are assigned to their bands and counted "
               f"as reference monitoring. Every deep-tropical city comes from the open archive, "
               f"where low-cost sensors dominate, which is a confound that cannot be sampled "
               f"away.")


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


# T9_2 (the proposed Kandy network, by stratum) was removed 2026-09-17: the measurement design is
# still under development and is not presented in the thesis. Its source is in git history.


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
           ["A network sited deliberately across land-use contrast",
            "whether the spatial limit is support or siting",
            f"REGISTERED NULL on a learned pattern, bounded at the detection limit and not at "
            f"zero; and a panel test in which deliberate siting scores "
            f"{tok('site.paired_median')} against convenience siting, paired within city. "
            f"Not ranked as an acquisition"],
           ["Precipitation in the forecast drivers",
            "wet removal, absent from the current driver set",
            f"REGISTERED NULL: adding it moves the sensorless rung by "
            f"{tok('precip.p1')} per cent and the gains above it by "
            f"{tok('precip.first2.paired')} points. The gap is now measured, not unexamined"],
           ["More monitors beyond the first", "nothing this model can use for a daily city mean",
            f"LADDER: {tok('step.bud1_bud2')} per cent"]],
          note="The evidence column names the KIND of argument as well as its content, because "
               "the two are not interchangeable. A row marked LADDER carries a marginal "
               "predictive value measured on this panel; a row marked MEASUREMENT DESIGN does "
               "not, and must not borrow one. In particular the ladder measured low-cost "
               "sensors, so it ranks a local observation above a regional one without saying "
               "anything about instrument grade. The last row is included because it is the "
               "acquisition most often proposed and the one the measurement does not support.")


# ── v2 tables (2026-10-06): registered confirmation + the post-hoc like-for-like review (F.117, F.124) ──
# The tables above read superseded ladder-v1 claims; these read `v2.*` claims. Both build, so the current
# thesis still assembles while the author rewrites ch07/ch09 (docs/thesis_change_list_2026-10-06.md).

def _ci(tag: str) -> str:
    return f"{tok(tag + '.median')} [{tok(tag + '.lo')}, {tok(tag + '.hi')}]"


def t7_1_ladder_v2():
    c = "v2.conf.reco."
    write("T7_1_ladder_v2", "Registered confirmation on 72 fresh cities, as constructed",
          ["endpoint", "what the rung does", "median (two-level cluster 95 % interval)"],
          [["H1 first two stations", "recalibrate the free estimate (intercept and slope)",
            _ci(c + "first2_rmse") + " per cent"],
           ["H2 stations three to six", "the same recalibration from six stations",
            _ci(c + "s36_rmse") + " points"],
           ["H3 background series", "the daily 10th percentile of the other stations, read on the day",
            _ci(c + "bg_rmse") + " per cent"],
           ["H4 background minus first two", "a comparison of the two rungs as built",
            _ci(c + "bgm2_rmse") + " points"],
           ["H5 the same, exceedance days", "as H4, balanced error at 15 µg m⁻³",
            _ci(c + "bgm2_exceed") + " points"]],
          note="Verdicts stand as registered (OSF ueyfr). The rungs use their stations differently: "
               "the local stations never enter a day's prediction, the background does. H4 and H5 "
               "therefore compare uses, not observations; {{ref:s-like-for-like}} compares them on equal terms.")


def t7_2_like_for_like_v2():
    r = "v2.review.registered_loco.reco."
    k = "v2.review.k."
    write("T7_2_like_for_like_v2", "What a station is worth when it is read on the day (post hoc)",
          ["comparison", "median % reduction in daily RMSE, or paired points"],
          [["first two stations, read on the day", _ci(r + "gL2s_rmse")],
           ["background as registered, read on the day", _ci(r + "gBGall_rmse")],
           ["background minus first two, both read on the day", _ci(r + "BGallmL2s_rmse")],
           ["one station read daily", _ci(k + "day1")],
           ["two stations read daily", _ci(k + "day2")],
           ["five stations read daily", _ci(k + "day5")],
           ["two stations used only as a recalibration", _ci(k + "cal2")]],
          note="Exploratory re-analysis of the registered data (ledger F.124): every stream regressed "
               "with the free estimate against stations not otherwise used, same-day, with shrinkage "
               "weights cross-fitted from other cities. The registered numbers are reproduced exactly "
               "in the same run. Station-count rows: full networks, 86 cities.")


def t3_km_rung():
    """The deployed Kandy temporal anchor on the ladder (exploratory, F.125)."""
    r, p = "v2.km.reco.unio.", "v2.km.pros.unio."
    rows = []
    for arm, lab, use in (("Bud0", "Sensorless learner (the ladder's own rung)", "none"),
                          ("K0", "Kandy chain, no stations", "none"),
                          ("Bud0cal2", "Sensorless learner, recalibrated", "two, calibration only"),
                          ("K2", "Kandy chain as deployed", "two, training and calibration"),
                          ("L2same", "Sensorless learner, stations read on the day", "two, read daily")):
        g = "" if arm == "Bud0" else _ci(r + f"g{arm}_rmse")
        gp = "" if arm == "Bud0" else _ci(p + f"g{arm}_rmse")
        rows.append([lab, use, g or "reference", gp or "reference",
                     tok(r + f"{arm}_r.median"), tok(r + f"{arm}_bias.median")])
    write("T3_km_rung", "The deployed model's temporal anchor placed on the ladder (exploratory)",
          ["rung", "local stations", "reduction in daily RMSE, reconstruction (per cent)",
           "reduction in daily RMSE, prospective (per cent)", "correlation with held-out daily mean",
           "level bias (per cent)"], rows,
          note=f"Median over {tok('v2.km.cities_scored')} cities of the per-city median over up to "
               f"21 random station splits; intervals from a cluster bootstrap over monitoring networks. "
               f"Reductions are relative to the sensorless learner on the same days. Correlation and "
               f"bias are for the reconstruction use. The deployed chain's nominal 90 per cent interval "
               f"covered a fraction {tok(r + 'K2_cov90.median')} of held-out daily means in reconstruction and "
               f"{tok(p + 'K2_cov90.median')} prospectively. Specified before scoring "
               f"and committed to the project record; not registered.")


def t3_rh_scenario():
    """Humidity-correction scenario (exploratory, F.126)."""
    rows = []
    for tag, lab in (("f", "local fraction"), ("peak_trough", "morning peak over midday level"),
                     ("night_midday", "night over midday"), ("season_swing", "highest over lowest month"),
                     ("daily_r", "daily correlation with the sensors"),
                     ("daily_rmse", "daily RMSE against the sensors (micrograms per cubic metre)"),
                     ("cov90", "nominal 90 per cent interval coverage"), ("cov90_rec", "coverage, sensor offsets removed")):
        rows.append([lab, tok(f"rh2.production.{tag}"), tok(f"rh2.hourly_rh.{tag}")])
    write("T3_rh_scenario", "The delivered series under the two humidity corrections (exploratory)",
          ["quantity", "constant humidity (delivered)", "hourly humidity"], rows,
          note="Means over 2019 to 2023. The annual level is identical by construction. Skill and "
               "coverage are against the sensor record corrected the same way; the sensors calibrated "
               "the anchor, so these are consistency measures, not validation.")


def t4_ledger():
    """Evidence ledger: what each model quantity may be used for (second external review)."""
    km_r, km_p = "v2.km.reco.unio.", "v2.km.pros.unio."
    write("T4_ledger", "What each part of the reconstruction can be used for",
          ["model quantity", "evidential status", "permitted interpretation"],
          [["Seasonal behaviour",
            f"supported in the ten analogue cities (seasonal correlation {tok('scorecard.seasonal_r_lo')} to "
            f"{tok('scorecard.seasonal_r_hi')})",
            "broad seasonal comparisons, subject to the limits of transfer"],
           ["Day-to-day sequence",
            f"conditionally supported: daily correlation {tok(km_r + 'K2_r.median')} where the anchor stations "
            f"observed the period, {tok(km_p + 'K2_r.median')} where they did not",
            "better supported on days the sensors reported"],
           ["Depth of the daily cycle",
            f"calibration-sensitive: morning peak over midday {tok('rh2.production.peak_trough')} or "
            f"{tok('rh2.hourly_rh.peak_trough')} depending on the humidity correction",
            "scenario-dependent until a reference instrument settles the correction"],
           ["Absolute level",
            f"unresolved: a national record within {tok('nbro.diff_pct_2021')} and {tok('nbro.diff_pct_2022')} "
            f"per cent, three low-cost records below, the satellite level {tok(km_r + 'K2_bias.median')} per cent "
            f"above withheld city means",
            "a model estimate, not an independently established exposure"],
           ["Uncertainty interval",
            f"under-covers: {tok('kandy.cov90')} per cent at the Kandy sensors, a fraction "
            f"{tok(km_r + 'K2_cov90.median')} across the ladder's cities, against a nominal 90",
            "indicative only; not calibrated for the basin field"],
           ["Spatial pattern at the kilometre scale",
            f"not validated: rank correlation {tok('r2b.rho_C')} as delivered, below a free built-up layer "
            f"({tok('r2b.rho_BU')})",
            "a hypothesis to test, not a ranking of neighbourhoods"],
           ["Regional and local partition",
            f"specification-dependent: {tok('partition.f')} at baseline, {tok('v2.f.cap_min')} to "
            f"{tok('v2.f.cap_max')} across cap choices, {tok('field.f_form_roll48')} with a 48-hour window",
            "a property of the decomposition, not a source apportionment"],
           ["Value of daily observations",
            f"supported across the panel: one station read daily {tok('v2.review.k.day1.median')} per cent, "
            f"two used only to calibrate {tok('v2.review.k.cal2.median')} per cent (post hoc re-analysis)",
            "evidence for continuous use of readings, not an ordering of station types"]],
          note="Each row summarises evidence reported in the results; none of it is new.")


def t3_validation_summary():
    """Validation by evaluation condition (second external review)."""
    km_r, km_p = "v2.km.reco.unio.", "v2.km.pros.unio."
    write("T3_validation_summary", "Validation results by evaluation condition",
          ["condition", "evidence", "result", "caveat"],
          [["Seasonal aggregation", "ten analogue cities, withheld stations",
            f"seasonal correlation {tok('scorecard.seasonal_r_lo')} to {tok('scorecard.seasonal_r_hi')}; level "
            f"bias median {tok('scorecard.level_bias_median')} per cent",
            "climatological; level there set by two stations, not the satellite"],
           ["Shape of the daily cycle", "ten analogue cities",
            f"diurnal correlation {tok('scorecard.diurnal_r_lo')} to {tok('scorecard.diurnal_r_hi')}",
            "regime-dependent; depth also calibration-dependent at Kandy"],
           ["Daily, anchor stations reporting", f"ladder, {tok('v2.km.cities_scored')} cities",
            f"error {tok(km_r + 'gK2_rmse.median')} per cent below the sensorless estimate; correlation "
            f"{tok(km_r + 'K2_r.median')}; bias {tok(km_r + 'K2_bias.median')} per cent",
            "includes training on the anchor stations' own record"],
           ["Daily, anchor stations not reporting", "ladder, prospective",
            f"error {tok(km_p + 'gK2_rmse.median')} per cent below [{tok(km_p + 'gK2_rmse.lo')}, "
            f"{tok(km_p + 'gK2_rmse.hi')}]; correlation {tok(km_p + 'K2_r.median')}; bias "
            f"{tok(km_p + 'K2_bias.median')} per cent",
            "no resolvable gain over the sensorless estimate"],
           ["Hourly, at Kandy", "one month of one sensor withheld at a time",
            f"coefficient of determination {tok('v2.tanchor.lagfree.r2')}; RMSE {tok('v2.tanchor.lagfree.rmse')}",
            "the same sensors calibrate the anchor's amplitude"],
           ["Interval coverage", "Kandy sensors; ladder cities",
            f"{tok('kandy.cov90')} per cent; a fraction {tok(km_r + 'K2_cov90.median')}",
            "nominal 90; misses one-sided at Kandy"],
           ["Independent Kandy records", "national organisation, two years; three low-cost records",
            f"{tok('nbro.diff_pct_2021')} and {tok('nbro.diff_pct_2022')} per cent; low-cost records below the field",
            "point against cell; instruments differ"]],
          note="A high seasonal correlation does not imply accurate daily or hourly values; each "
               "condition is reported separately for that reason.")


def ta_ladder_status():
    """Status of each ladder result: registered, post hoc, retracted or exploratory."""
    write("TA_ladder_status", "Status of each result from the information ladder",
          ["result", "status", "how it may be quoted"],
          [["Confirmation on fresh cities (H1 to H5)", "registered (OSF ueyfr)",
            "as constructed: the rungs use their stations differently"],
           ["Richer sensorless rung; other learners; full networks", "registered (OSF b379r, jea58, mhgna)",
            "as robustness of the confirmation, as constructed"],
           ["Every station used the same way", "post hoc re-analysis of registered data",
            "kind of station makes no resolvable difference; awaits a fresh registered test"],
           ["Stations read daily against calibration only", "post hoc re-analysis",
            "daily use has demonstrated value in the panel"],
           ["Leave one network out", "post hoc", "the sensorless rung was flattered slightly"],
           ["Deep-tropical reversal", "retracted", "not distinguishable from zero across splits"],
           ["Deployed model as a rung", "exploratory; design committed before scoring, not registered",
            "conditional on whether the anchor stations reported"]],
          note="No post hoc result is presented as a registered confirmation anywhere in this thesis.")


def t9_1_next_v2():
    write("T9_1_next_v2", "Measurement priorities for Kandy, and the kind of evidence behind each",
          ["action", "what it would settle", "what ranks it, and of what kind"],
          [["Continuous stations whose readings reach the estimate daily (CEA, NBRO, the university "
            "network), of whatever kind are available",
            "the daily city level",
            f"RE-ANALYSIS (post hoc): one station read daily {tok('v2.review.k.day1.median')} per cent, "
            f"two {tok('v2.review.k.day2.median')}; as a calibration only, "
            f"{tok('v2.review.k.cal2.median')}. Kind of station: "
            f"{tok('v2.review.registered_loco.reco.BGallmL2s_rmse.median')} points"],
           ["Making one of them reference grade",
            "the level discrepancy, and a calibration anchor for the low-cost sensors",
            "MEASUREMENT DESIGN, not the ladder: three of four independent Kandy records sit below the "
            "model, and the diurnal shape depends on the humidity correction"],
           ["More than three to five stations for the daily mean",
            "little: the daily curve flattens",
            f"RE-ANALYSIS: five stations {tok('v2.review.k.day5.median')} per cent against "
            f"{tok('v2.review.k.day2.median')} for two"],
           ["A network for a neighbourhood map",
            "where in the basin pollution is highest",
            f"SPATIAL CURVE: at three to eight stations no method ranked neighbourhoods usefully; "
            f"{tok('v2.curve.full.holm_crossing')} cities crossed a free layer after correction; a "
            f"satellite surface ranked at {tok('v2.curve.full.ghap.median')}"],
           ["Precipitation in the drivers", "wet removal",
            f"REGISTERED NULL: {tok('precip.p1')} per cent on the sensorless rung"]],
          note="The first row rests on the like-for-like re-analysis, not on the registered rung "
               "construction, and no ordering specific to the deep tropics is used.")


BUILDERS = {
    "T7_1v2": t7_1_ladder_v2, "T7_2v2": t7_2_like_for_like_v2, "T9_1v2": t9_1_next_v2, "T3_km": t3_km_rung, "T3_rh": t3_rh_scenario, "T4_ledger": t4_ledger, "T3_val": t3_validation_summary, "TA_status": ta_ladder_status,
    "T3_1": t3_1_literature, "T3_2": t3_2_point_records, "T4_1": t4_1_data, "T4_3": t4_3_panel, "T5_1": t5_1_attempts,
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
