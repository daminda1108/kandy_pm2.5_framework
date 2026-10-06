"""Figure and diagram captions, keyed by the tag used in {{fig:tag}} / {{dia:tag}}.

Moved out of assemble.py unchanged on 2026-09-18 so the assembler is readable.
"""
from __future__ import annotations

# tag -> (file stem, caption). The file is looked up in thesis/diagrams then thesis/figures.
#
# A token ALONE ON A LINE places the image with its caption. The same token inline becomes
# just the label, so "as {{dia:protocol}} shows" reads as "as Figure 7.1 shows". This is the
# convention the project's manuscript already uses and it removes the whole class of error
# where prose says Figure 4 and the image is Figure 5.
VISUALS: dict[str, tuple[str, str]] = {
    # Chapter 1
    "obsdensity": (
        "F1_1_observing_density",
        "Every location worldwide that publishes fine particulate measurements openly, and "
        "the same locations counted by absolute latitude. Reference-grade instruments are "
        "marked separately from low-cost ones. The deficit is not random: it falls hardest "
        "towards the tropics, which include some of the most polluted and most populous "
        "regions on Earth [@vanDonkelaar2021; @Martin2019]. The star marks Kandy."),
    # Chapter 2
    "valley": (
        "D11_valley",
        "The setting, taken from a digital elevation model rather than from a photograph. "
        "The left panel is the modelled domain on a projected grid, so distances are true, "
        "with hillshade, 100 metre contours, the Mahaweli Ganga, the two low-cost sensors "
        "and a locator for Sri Lanka; the right is a section running "
        "south to north through the city centre, from the Hantana range that closes the basin "
        "to the Mahaweli corridor that ventilates it. The relief along that line and across "
        "the whole domain are both given, because they differ and the larger figure is the "
        "one quoted elsewhere in this thesis."),
    "refbyband": (
        "F2_2_reference_by_band",
        "Cities worldwide carrying ten or more concurrent reference monitors, counted by "
        "latitude band. This is the population from which any validation panel must be "
        "drawn, and it is the reason the association between instrument class and latitude "
        "cannot be removed by sampling more carefully."),
    # Chapter 3
    "transect": (
        "F3_2_transect",
        "A roadside survey of Kandy against the model at the same locations. The survey "
        "measured PM10, which includes the fine fraction, over three midday hours and mostly at "
        "the roadside, and the model reports "
        "fine particulate as a cell mean, so the two have no common scale and each series is "
        "shown relative to its own median. Open markers are sites censored at a common upper "
        "value, which are lower bounds and not measurements. What the comparison establishes "
        "is a difference in spread, not a difference in level."),
    # Chapter 4
    "pipeline": (
        "D1_pipeline",
        "The construction end to end. Blue marks information available everywhere at no cost, "
        "red marks information that has to be bought locally. The temporal anchor carries the "
        "level, the background carries the regional contribution, and the pattern decides only "
        "where the local increment sits. Because the pattern has unit spatial mean it cannot "
        "change how much material there is."),
    "panel": (
        "F4_3_panel",
        "The cities whose monitoring networks supply the borrowed ground truth, sized by the "
        "number of monitors withheld from the model at each. The star marks the target city, "
        "which contributes no training data of any kind."),
    # Chapter 5
    "taxonomy": (
        "D8_failure_taxonomy",
        "Eight approaches that did not work, placed by whether an expectation was recorded "
        "before the run and whether the failure produced a bounded claim. The attempts lie "
        "close to the diagonal, which is the argument of {{ref:ch-eight-approaches-did-work}}: "
        "an approach yields about as "
        "much when it fails as it declared before it started."),
    "timeline": (
        "D12_timeline",
        "What was attempted and how each attempt ended, in the order the work was done. "
        "Dates are from the project's own dated record."),
    # Chapter 8
    "paired": (
        "F1_paired",
        "The spatial limit, measured rather than asserted. Two survey sites three hundred "
        "metres apart, sampled by the same method over the same three midday hours (on "
        "different days), fall inside a "
        "single model cell: support is held fixed and only location varies. The first panel "
        "gives the observed contrast against the model as delivered and after the physics is "
        "re-run ten times finer in area. The second sweeps resolution, which converts an "
        "anecdote about one pair of sites into a test of the hypothesis that resolution is the "
        "problem. The third follows the contrast through each stage of the build, and shows it "
        "is relocated rather than destroyed."),
    "withinpixel": (
        "F5_withinpixel",
        "What survives the limit. The spread inside a typical cell exceeds the spread between "
        "cells across the whole map, so most within-city variation is sub-grid by the model's "
        "own structure. This is simultaneously the explanation for the paired-site result and "
        "the reason a pointwise product is not offered. The second panel reports a check that "
        "was uninformative, and says so: because the predicted within-cell spread is far "
        "smaller than the observed range, every high site saturates at the top quantile and "
        "every low one at the bottom, so the test re-detects the amplitude gap rather than "
        "testing ordering."),
    "scales": (
        # 2026-09-18: previously pointed at F9_scales, a different figure (temporal variation
        # and the ventilation index) that shared the file name. Built by
        # src/f_chapters.py f8_contrast_window from decomp/kandy_contrast_by_window.csv.
        "F8_contrast_window",
        "Spatial contrast against the averaging window, as the ratio of the 90th to the 10th "
        "percentile. The blue line is the Kandy model across cells; the grey lines are the "
        "spread across stations in three panel cities with dense networks, measured in this "
        "work. Observed contrast falls as the window lengthens and the model's rises, so the "
        "model is most under-contrasted at the hourly window. The two are spreads over "
        "different things, cells against stations, and {{ref:s-test-holds-support-fixed}} is "
        "the test that holds support fixed."),
    "nullpower": (
        "F12_null_power",
        "What the earlier spatial nulls could have detected. At the sample sizes available, "
        "the smallest residual correlation each test could have found at eighty per cent power "
        "is far above zero. They therefore excluded a large learnable signal and said nothing "
        "about a moderate one, which is the defect the pre-registered test of "
        "{{ref:s-six-negative-results-their}} was "
        "designed to remove."),
    "bound": (
        "F3_information_bound",
        "Three independent lines on the same limit. A rigid physical form fitted jointly across "
        "cities drives two of its six parameters onto their bounds, which is identifiability "
        "failure rather than a result. A flexible neural model reaches a modest cross-city "
        "correlation and no more. And the memorisation signature runs the wrong way for a model "
        "that had learned the field, with agreement far higher near a sensor than away from it. "
        "That the limit appears in model families sharing almost nothing is the strongest form "
        "this kind of argument can take."),
    "dispersion": (
        "F5_5_dispersion_costs",
        "The step intended to place the local increment, scored on two independently selected "
        "sets of cities. Each line is one city, from its source emission surface to the same "
        "surface after the terrain solver has redistributed it. Green improves and pink "
        "worsens. Both frames agree that the redistribution removes rank."),
    # Chapter 6
    "decomposition": (
        "D2_decomposition",
        "The decomposition drawn as a section across the basin. The background is spatially "
        "uniform, so all of the structure in the delivered field belongs to the local "
        "increment, and the increment is the only part a local intervention can change. "
        "Because the pattern integrates to unity, the shaded area is fixed whatever shape the "
        "pattern takes. A schematic, not model output."),
    "tiers": (
        "D3_budget_tiers",
        "The information budget. Each tier admits one further observation stream and can "
        "constrain one further quantity. The tiers are nested, so a lower tier is the same "
        "model with a stream withheld and not a different model, which is the property that "
        "turns an ablation into a measurement. The spatial tier is drawn in grey because it "
        "is a declared design assumption rather than a validated rung."),
    "obsoperator": (
        "D4_observation_operator",
        "Why an areal model and a point monitor cannot be compared directly. The model "
        "reports a cell mean and the instrument samples one location inside that cell, so a "
        "systematic offset and a representativeness error must both be carried explicitly. "
        "Without them a centring error is misread as a failure of interval width. A "
        "schematic, not model output."),
    # Chapter 7
    "protocol": (
        "D5_validation_protocol",
        "Budget matched validation. A city with a dense network is reduced to the target "
        "city's information budget and then scored against the monitors withheld from it. "
        "Blue marks what the model is permitted to see; red marks what is held back. The "
        "budget match is what makes the test informative, because a model that has seen "
        "thirty monitors measures a capability the target city will never have."),
    "ladder": (
        "F2_ladder",
        "What each increment of information buys, as the median across cities of the per-city "
        "reduction in daily error. The pooled ladder is coloured by whether a stream is free "
        "everywhere, a local instrument, or regional. Free static geography is worth about as "
        "much as the first local instrument, and monitors three to six are "
        "indistinguishable from zero. The second panel stratifies the two decisive rungs by "
        "latitude band with the number of cities on the axis, and the ordering inverts in the "
        "deep tropics."),
    "streams": (
        "F3_streams",
        "Two results about what is being measured rather than about the model. The same two "
        "monitors priced by four estimators: the three non-linear learners agree closely while "
        "ridge regression, unable to exploit sixty-eight sensorless predictors, reports the "
        "monitor as worth far more. The second panel replaces a fused product with raw "
        "satellite retrievals; the satellite rung itself barely moves, so the fused product was "
        "not inflating its own score, but the rung above it roughly doubles."),
    "confounds": (
        "F4_confounds",
        "The confound that cannot be sampled away. Instrument class is strongly associated with "
        "latitude band, and the population of candidate cities does not contain a balanced "
        "draw, so results are reported stratified by class throughout rather than corrected."),
    "scorecard": (
        "F7_scorecard",
        "Ten cities scored on the same protocol. Seasonal agreement is high everywhere, diurnal "
        "agreement is regime-dependent, and the fine spatial rank is estimable at nine of the "
        "ten and significant at six. The three axes are reported separately because averaging "
        "them would hide exactly the variation that matters."),
    "kathmandu": (
        "F8_kathmandu",
        "The transfer at its most favourable: a city with a dense network, scored against "
        "monitors withheld from the fit. It is shown because it is the best case and is "
        "labelled as such, not because it is typical."),
    "cycles": (
        "F_cycles",
        "Seasonal and diurnal cycles against the two Kandy sensors. This comparison is "
        "reported for completeness and cannot be read as validation: the temporal anchor is "
        "trained on the residual of these sensors and then amplitude-sharpened to their "
        "observed swing, so agreement here measures the calibration rather than skill."),
    "uncertainty": (
        "F11_uncertainty",
        "Interval calibration at the two Kandy sensors. Coverage falls below nominal, but the "
        "misses are almost all on one side, which is a centring problem and not a width "
        "problem. Removing each sensor's own median offset restores coverage, which is the "
        "diagnosis an explicit observation operator makes available."),
    "chemistry": (
        "F6_chemistry",
        "A chemical check on the decomposition's load-bearing assumption, using back-trajectory "
        "sector to classify air-mass origin independently of the composition product. "
        "Continental air is measurably more secondary-rich, and therefore more aged, than "
        "marine air, which is the ordering the decomposition requires. The registered "
        "prediction that recirculated local air would be freshest is refuted, because "
        "stagnation gives local precursors time to age in place."),
    "claimsgate": (
        "D7_claims_gate",
        "How a number reaches the text, and what stops it reaching the text any other way. "
        "Every numeric claim is recomputed from its scored file at build time and compared "
        "against the stored value; a disagreement refuses the build rather than warning about "
        "it."),
    "burden": (
        "F_burden",
        "Population-weighted exposure and the attributable burden that follows from it. The "
        "unweighted basin mean under-states what people actually breathe, because population "
        "concentrates in the higher-concentration core. The burden is a projection of the "
        "delivered field through a published response function rather than an epidemiological "
        "result of this work, and its interval reflects only the published uncertainty in that "
        "function."),
    "prereg": (
        "D6_prereg_workflow",
        "Pre-registration as a procedure. The branch that matters is the one distinguishing a "
        "defect found before scoring, which may be amended and dated, from a criterion "
        "changed once the result is known, which may not."),
    # 2026-09-14: the six figures of the figure and map plan
    "partition": (
        "F6_partition",
        "The local fraction along the three axes on which it can move, drawn apart because "
        "they measure different things and were once conflated. Anchored years and the "
        "filled sweep come from the production code path; the open markers come from an "
        "independent reimplementation of the constraint, which reads slightly higher "
        "throughout and is the version the text quotes. The shaded band spans every value "
        "shown, and the dashed line is the production fraction."),
    "stationcount": (
        "F7_station_count",
        "What each additional local station buys. The first panel is the median across "
        "cities of the per-city reduction in daily error at each station count, pooled in "
        "black with the four latitude bands behind it and the number of cities in each; the "
        "interval at one station is a bootstrap over cities. The second panel pairs each "
        "count against a single station within city, which is the comparison that decides "
        "whether a further station helps."),
    "clusterboot": (
        "F7_cluster_bootstrap",
        "Intervals for the three decisive steps when the resampling unit is the city and "
        "when it is the monitoring network. Each row has its own scale, because the middle "
        "step is two orders of magnitude smaller than the others. Every interval widens and "
        "none of the three conclusions changes."),
    "losses": (
        "F7_losses",
        "The ladder re-scored under four losses. The first panel gives the three decisive "
        "steps under each loss with intervals over cities. The second gives, for the "
        "deep-tropical band only, the paired advantage of two local sensors over the "
        "background proxy, with the number of cities each loss could be scored on; filled "
        "markers are intervals that exclude zero. The sign changes between average-day and "
        "episode losses."),
    "tournament": (
        "F8_tournament",
        "Every admissible model family, and the foundation-model embeddings of the "
        "registered test, against the single best free raster, paired within city with "
        "intervals over cities and the registered detection limit an improvement would have "
        "had to reach. The second panel gives median rank correlations, including three "
        "oracle families that see the target city's own stations and are therefore "
        "inadmissible for a city without monitors."),
    "pairedtrap": (
        "F9_paired_trap",
        "The siting experiment read two ways. On the left each line is one city, joining "
        "the rank correlation from a convenience subset to that from a deliberately spread "
        "subset, green where spreading helped and pink where it hurt, with the median of "
        "each arm marked. On the right the same cities as within-city differences, with the "
        "paired median and its interval over cities. The medians suggest a near doubling; "
        "the paired reading finds no advantage."),
    # Chapter 9
    "acquisition": (
        "F9_1_acquisition",
        "What each of the two decisive instruments is worth, pooled across all cities and "
        "within the latitude band the demonstration city belongs to. The ordering reverses, "
        "so the recommendation derived from the global average is the wrong recommendation "
        "for the tropics."),
    "learnedbar": (
        "F9_2_learned_bar",
        "The pre-registered test of a learned spatial pattern. The bar was fixed before the "
        "model was written, as the benchmark plus the smallest improvement the frame could "
        "detect at eighty per cent power. Nothing learned reaches it, and the per-city panel "
        "shows the learned pattern is indistinguishable from the single best predictor."),
    "radius": (
        "F9_3_radius",
        "Predictor skill against the radius of the buffer the predictor is measured over. For "
        "the two strongest families skill rises with radius and peaks coarser than the cell "
        "the model reports on. Read together with the within-cell result of "
        "{{ref:s-reason-change-support}}, the "
        "band of usable spatial information is bounded from both directions at once."),
    "decisiontree": (
        "D9_acquisition",
        "The acquisition decision as a procedure, with the branch that inverts between "
        "latitude bands."),
    # The reconstructed Kandy field (added 2026-09-18 for thesis A). All three read the shipped
    # additive_v3 field and the post-cap background (gotcha #86), built by
    # kandy_pm25/scripts/paper2026_figures_d.py and paper2026_fig_cycles_episode_burden.py.
    "field": (
        "F_field",
        "The reconstructed field over the Kandy domain. (a) The annual mean for "
        "{{claim:exposure.year}}. (b) The local increment, the part of the concentration above "
        "the regional background, which carries all of the spatial structure. (c) The annual "
        "basin mean split into background and increment for each anchored year, with the local "
        "share printed above each bar. Thin lines are elevation contours."),
    "spatiotemporal": (
        "F_spatiotemporal",
        "The field averaged by season (upper row) and by time of day (lower row), with the "
        "basin mean printed in the corner of each panel. The north-east monsoon months carry "
        "the highest concentrations and the south-west monsoon the lowest; within the day the "
        "morning and evening traffic peaks stand above a midday trough that is lower than the "
        "night. Thin lines are elevation contours."),
    "episode": (
        "F_episode",
        "The December 2022 transboundary episode. (a) The field at the hour of the highest "
        "basin mean. (b) The basin mean across the 48 hours of the episode, averaging "
        "{{claim:kandy.episode_mean}} micrograms per cubic metre with a peak of "
        "{{claim:kandy.episode_peak}}. The dashed and dotted lines are the World Health "
        "Organization 24-hour interim targets 1 and 2; they are daily values drawn against an "
        "hourly trace for scale, not an hourly standard."),
}

# Source credits, appended to the captions of figures that DISPLAY third-party data: maps drawn
# on external geography, and observations made by someone else. The departmental format
# requires any figure drawn from another source to be cited. Figures that are analyses of the
# panel's data are the project's own work; the panel's archives are cited where the panel is
# described. Each entry was checked against the builder that reads the data (2026-09-18).
CREDITS: dict[str, str] = {
    "obsdensity": "Monitoring locations from OpenAQ [@OpenAQ]; coastlines from Natural Earth "
                  "[@NaturalEarth].",
    "refbyband": "Monitor counts from OpenAQ [@OpenAQ].",
    "panel": "Monitoring networks from OpenAQ [@OpenAQ] and the China National Environmental "
             "Monitoring Centre [@CNEMC]; coastlines from Natural Earth [@NaturalEarth].",
    "valley": "Elevation from the Shuttle Radar Topography Mission [@Farr2007]; river from "
              "OpenStreetMap [@OpenStreetMap]; country outline from Natural Earth "
              "[@NaturalEarth].",
    "transect": "Survey observations from [@Elangasinghe2008].",
    "paired": "Observed contrast from the survey of [@Elangasinghe2008].",
    "field": "Elevation contours from the Shuttle Radar Topography Mission [@Farr2007].",
    "spatiotemporal": "Elevation contours from the Shuttle Radar Topography Mission "
                      "[@Farr2007].",
    "cycles": "Sensor records obtained through PurpleAir [@PurpleAir].",
    "uncertainty": "Sensor records obtained through PurpleAir [@PurpleAir].",
    "scorecard": "Station records from OpenAQ [@OpenAQ] and the China National Environmental "
                 "Monitoring Centre [@CNEMC].",
    "kathmandu": "Station records from OpenAQ [@OpenAQ].",
    "chemistry": "Composition from the GEOS-CF reanalysis [@Keller2021].",
    "burden": "Population from WorldPop [@Tatem2017]; response function from [@Burnett2018].",
}
for _tag, _credit in CREDITS.items():
    _stem, _caption = VISUALS[_tag]
    VISUALS[_tag] = (_stem, f"{_caption} {_credit}")
