# 5. Where the model stops, and why

*New section per `rewrite_plan_2026-08-22.md` §5. Leads with the paired-site result (F.76/F.89);
the four-rung support ladder is demoted to a confounded secondary observation.*

---

A model of this kind is usually reported with its skill and a list of caveats. We report
something more specific: **the resolution at which it stops working, the reason, and the
quantity that survives.** The distinction matters because "our data was inadequate" and "the
question was mis-specified" call for different responses, and only one of them is true here.

## 5.1 The observation that sets the problem

Kandy's within-city gradient is not small. A 25-site roadside survey conducted across the city
in 2004–06 records concentrations falling from 110 to 4 µg m⁻³ over 300 m inside a single
botanical garden, with an R² of 0.82 against traffic intensity at the site [@Elangasinghe2008]. Across the whole
survey the observed spread is {{claim:spatial.obs_spread}}×. The shipped 1 km field spans
{{claim:spatial.model_spread}}×.

Two orders of magnitude separate them, and the naive reading is that the model has failed. That
reading is wrong, and showing why is the substance of this section.

## 5.2 The paired-site test

The survey contains a pair of sites that isolates the question. The botanical garden entrance
and a point 300 m inside it were sampled with the same instrument, over the same 3-hour window,
on the same protocol. **They fall inside a single {{claim:subgrid.coarse_res_m}} m model cell.**
Support is held fixed; only location varies.

| | entrance | 300 m inside | ratio |
|---|---:|---:|---:|
| observed | 110 | 4 | **{{claim:spatial.paired_obs_ratio}}×** |
| model, as shipped | — | — | **{{claim:spatial.paired_model_ratio}}×** |

{{fig:paired}}a shows the pair. The model returns exactly unity because it is being asked about one pixel twice. This is the
cleanest available statement of the limit: **the model's entire dynamic range across Kandy is
smaller than the difference between two points 300 m apart in one garden.**

⚠ Three limitations, stated before they are asked for. The observed values are PM10 and the
model is PM2.5, so only *ratios* are meaningful. Of the survey's {{claim:spatial.transect_sites}}
mapped sites, {{claim:spatial.transect_censored}} are censored at a common upper value and
several more are binned, leaving only {{claim:spatial.transect_distinct_obs}} distinct
observations — so the rank correlation across all sites
({{claim:s1.rank_production_238m}}, not significant) is a weak test and we do not lean on it.
And a second apparent pair in the survey — a school junction and its grounds — proves on
inspection to carry **a single coordinate for both sites**, so the model's unit ratio there is
an artefact of the question, not a result. We withdraw it. **The garden pair is the evidence.**

## 5.3 Is it resolution? A registered test says no

The obvious diagnosis is that 1 km is too coarse. We pre-registered a test of it before running.

The model's own emission surface is computed at {{claim:subgrid.fine_res_m}} m and aggregated to
{{claim:subgrid.coarse_res_m}} m before anything is rendered — so a finer field already exists
inside the build. At the paired microsites the fine surface gives
{{claim:subgrid.paired_efine_entrance}} against {{claim:subgrid.paired_efine_inside_300m}}, a
ratio of {{claim:subgrid.paired_efine_ratio}}× in the correct direction, where the shipped
product gives unity. That is a real signal, and the registered hypothesis was that dispersing it
at {{claim:subgrid.fine_res_m}} m would recover a material fraction of the observed contrast.

**It does not.** Running the calibrated terrain solver at {{claim:subgrid.fine_res_m}} m, forced
with the survey's own midday climatology and with nothing fitted:

| | production, 238 m | fine, {{claim:subgrid.fine_res_m}} m |
|---|---:|---:|
| paired-site ratio | {{claim:s1.paired_production_238m}}× | **{{claim:s1.paired_fine_94m}}×** |
| rank across the survey | {{claim:s1.rank_production_238m}} | {{claim:s1.rank_fine_94m}} |

{{fig:paired}}b plots the same ratio against resolution. A tenfold refinement in area moves the paired ratio by 0.03 and the rank correlation by 0.002.
Registered predictions {{claim:s1.predictions_refuted}} are refuted. Resolution is not the
binding constraint, and per the registration **we treat the question as closed rather than
re-scoping it**.

## 5.4 What is actually lost, and where

The refutation also disposes of the premise that motivated it. Contrast is not destroyed by
coarsening — it is **relocated**. Tracking the spread through the build ({{fig:paired}}c):

| stage | p90/p10 |
|---|---:|
| raw emission surface at {{claim:subgrid.fine_res_m}} m | {{claim:s1.contrast.raw_E_fine_94_m}}× |
| after tempering | {{claim:s1.contrast.log1p_tempering}}× |
| after dispersion at {{claim:subgrid.fine_res_m}} m | {{claim:s1.contrast.dispersion_94_m}}× |
| after solving at 238 m | {{claim:s1.contrast.solve_at_238_m_production}}× |
| reported at {{claim:subgrid.coarse_res_m}} m | {{claim:s1.contrast.report_at_998_m}}× |

The dispersed field still spans {{claim:s1.contrast.report_at_998_m}}× at the shipped
resolution. There is no shortage of contrast. **It is in different places from where the survey
measured it** — which is a failure of *placement*, not of dynamic range and not of support.

An independent line agrees from the opposite direction. Scored across ten monitored cities, the
raw emission surface ranks neighbourhoods at ρ = {{claim:r2.rho_emission_surface}}; passing it
through the dispersion solver *lowers* that to {{claim:r2.rho_with_atransport}}, improving only
{{claim:r2.cities_improved}} of ten. The step that redistributes contrast is the step that
misplaces it.

⚠ This qualifies a number quoted throughout the literature on this model, including our own
earlier work. The undispersed emission surface achieves ρ = {{claim:r2.rho_emission_surface}},
**above** the ρ ≈ 0.2–0.28 ceiling we and others have reported. That ceiling was always measured
on fields already through this machinery. It is a property of the *construction*, not a bound on
what the emission proxy can support.

## 5.5 Five nulls that are not five confirmations

The spatial limit has been probed five times in this programme — a learned-pattern test, a
dynamic-transport test, an earth-observation embedding test, a full land-use regression, and the
sub-grid test above. All returned nulls, and it is tempting to read five agreeing tests as
strong evidence.

They are not independent. **All five score an areal model field against point stations**, and
therefore share one defect. Five tests that share a defect are one test repeated. The
attribution splits three ways and only the residual is an information limit:

- **Sample size.** Isolated by the point-to-point land-use regression [@Hoek2008], which fails on its own
  terms at a median of {{claim:lur.median_stations_per_city}} stations per city across {{claim:lur.cities}} cities with {{claim:lur.predictors}} predictors — far below what such designs require.
- **Change of support.** Measured, and the subject of §5.6.
- **An information limit.** What remains after the first two, and smaller than the raw null
  count suggests.

We report this because the alternative — presenting five nulls as five confirmations — would
have been the stronger-sounding and less defensible claim.

## 5.6 What survives: the distribution, not the location

A distribution does not need placement. The model cannot say which corner of a cell is dirty,
but it can say **how wide the distribution inside that cell is** — and that quantity is both
well-posed and, it turns out, the more informative one.

Structuring only the increment within each cell, with unit-mean weights so the cell mean is
preserved exactly (drift {{claim:s2.cell_mean_drift}} µg m⁻³, against a gate of 0.05):

| | p90/p10 |
|---|---:|
| **between** cells, midday | {{claim:s2.between_pixel_p90p10}}× |
| **within** a typical cell | **{{claim:s2.within_pixel_p90p10}}×** |

**The spread inside a typical pixel exceeds the spread across the map.** Most of the city's
midday spatial variation is sub-grid — which is simultaneously the explanation for §5.2, the
reason a pointwise product is not available, and a quantity no shipped field of this kind
currently reports.

⚠ The between-pixel figure is midday-only and is not the annual {{claim:spatial.model_spread}}×
quoted in §5.1; midday is ventilated and therefore flatter. ⚠ We tested whether observed sites
fall in the predicted quantiles of their own cell and record the test as **uninformative**: the
predicted within-cell spread is ~1.2× while observations span {{claim:spatial.obs_spread}}×, so
every high site saturates at the top quantile and every low one at the bottom. It re-detects the
amplitude gap rather than testing ordering, and the single non-saturated case runs the other way.

Validating a *distributional* claim properly needs observations at several supports within one
city, which is a rare and specific kind of campaign. Kandy has the beginnings of one — a 3-hour
kerbside survey [@Elangasinghe2008] and an 8-hour area-representative survey
[@Wickramasinghe2011] sample different quantiles of the same underlying distribution — but they
were conducted two decades and one decade ago respectively, and neither was designed for this
purpose. We name the requirement rather than claim to have met it: **a within-cell distribution
is testable, and testing it needs a campaign that samples supports deliberately.**

## 5.7 What this licenses

At matched support and matched statistic the model is close to right: annual p90/p10 of
{{claim:kandy.annual_contrast}} against 1.26–1.47 observed at comparable cities. The failure in
§5.1 is a comparison between quantities defined at different supports, not a skill deficit.

So the operational statement is narrow and, we think, honest. **Can a user rank neighbourhoods
against what a monitor would read there? No** — ρ ≈ 0.2–0.28 stands, and §5.5 explains what it
measures. **Can a user be told the range their cell spans? Yes**, and §5.6 supplies it. The
number is retained; what it is said to measure changes.

---

## Drafting notes, to remove before submission

- Needs the paired-site figure (`{{fig:paired}}`), the money figure, once the panel is drawn.
- ⚠ The 110 → 4 µg m⁻³ transect and its R² 0.82 are LITERATURE values and must stay as cited
  text — putting them in `claims.json` would fake provenance for someone else's measurement.
  The same applies to the 1.26–1.47 matched-support range until we recompute it ourselves.
- The stations-per-city figure is now tokenised from `lur_r2.csv`.
- §5.5's five nulls each need a citation to their ledger entry in the final reference pass.
