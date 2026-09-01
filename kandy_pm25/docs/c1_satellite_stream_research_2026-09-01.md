# C1 — the satellite stream is not a satellite stream

**Research note, 2026-09-01.** Phase 1 item C1 of
[`improvement_plan_2026-09-01.md`](improvement_plan_2026-09-01.md). Contains the finding and a
draft pre-registration for the test it implies.

---

## 1. The question I was sent to answer, and why it was the wrong one

C1 opened as: *`build_bud0_streams.py` pulls `GHAP_Y1K_PM25`, an annual scalar, and the ladder
concludes static geography (10.8%) beats the satellite level (7.6%) on daily RMSE. A daily 1 km
product exists. Either re-run with it, or write the leakage argument.*

The primary source settles it in a direction neither branch anticipated. **Switching to the
daily product would make the problem worse, and the annual product does not escape it.** The
defect is not the temporal resolution of the stream. It is that the stream is not an independent
observation at all.

Source: Wei, Li et al., *First close insight into global daily gapless 1 km PM2.5 pollution,
variability, and health impact*, **Nature Communications** 14, 8349 (2023) — the GHAP /
GlobalHighPM2.5 methods paper.

---

## 2. What GHAP actually is

| | |
|---|---|
| **Training data** | ~**9,500** ground monitoring stations, 2017–2022. Named sources include **OpenAQ**, **China National Environmental Monitoring Centre**, US EPA, Canadian NAPS, European Air Quality e-Reporting, and the South African, New Zealand and Brazilian national networks. ~74% of stations carry ≥2 years. |
| **Algorithm** | 4-Dimensional Space-Time Extra-Trees (4D-STET). |
| **Predictors (19)** | satellite AOD · **GEOS-CF PM2.5** · **CAMS emissions** · boundary-layer height · temperature · humidity · wind · pressure · precipitation · evaporation · **NDVI** · **night-time lights** · **elevation** · **population density**. |
| **Ground data at prediction time** | **No.** Training only; inference runs on gap-filled AOD and the auxiliary variables. |
| **Cross-validation** | sample-based R² 0.91 · **station-based 0.87** · grid-based 0.79 · day-based 0.81 · continent-stratified 0.54–0.89. |

---

## 3. Two findings, and the second is the serious one

### 3.1 The leakage is real, and the annual product does not escape it
GHAP's training set includes **OpenAQ and CNEMC** — *precisely* the two sources of our 48-city
panel (37 OpenAQ + 11 CNEMC). Our panel cities are multi-year monitored cities, which is exactly
the population GHAP trains on.

Ground measurements are training-only, not assimilated at inference, so this is not direct
assimilation. It is indirect: the fitted model encodes the stations it was fitted to. A
`Bud0` tier that consumes GHAP at a monitored city therefore has **indirect access to the very
monitors the ladder exists to price**.

⚠ **The annual product is the same model's output, averaged.** Averaging a contaminated
quantity does not decontaminate it. The original C1 framing — that the annual choice might be a
deliberate conservative hedge — is not available.

The concern has precedent in the literature: circularity is a recognised problem when
satellite-derived products scaled against regulatory monitors are then evaluated against those
same monitors ([GeoHealth, 2023](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10169548/) —
full citation to be confirmed before use). What is new here is applying it to a *value-of-
information* design, where the contaminated quantity sits in the **baseline** rather than the
prediction.

### 3.2 🔴 `SATELLITE_LEVEL` is mostly our own other two streams, recombined

This is the finding that matters. Set our `Bud0` streams beside GHAP's predictors:

| our stream | our variables | also a GHAP predictor? |
|---|---|---|
| `DRIVERS_REANALYSIS` | `temperature_2m`, `u/v_component_of_wind_10m`, `wind`, `boundary_layer_height`, `doy_sin`, `doy_cos` | **yes — all of them** |
| `STATIC_GEO` | NDVI, tree/water/built fractions, population, night lights, land cover, roads at 5 radii, distance-to-road | **NDVI, night lights, population, elevation — yes** |
| `SATELLITE_LEVEL` | GHAP `b1` | — |

GHAP additionally carries **humidity, pressure, precipitation, evaporation, GEOS-CF PM2.5 and
CAMS emissions**, which our `Bud0a` does **not**.

So `Bud0c` is not *drivers + geography + an independent satellite observation*. It is:

> drivers + geography + **a non-linear recombination of drivers and geography, plus AOD, plus
> extra drivers we do not carry, plus the panel's own monitors** — all pre-computed by somebody
> else's Extra-Trees model.

**Three consequences.**

1. **The 7.6% is a mixture, not a measurement of satellite information.** It bundles genuine AOD
   information, drivers we lack, a non-linear recombination of information the tier already had,
   and indirect monitor leakage. It cannot be attributed to "a satellite level" — which is the
   same class of error as C2, where a combined step was reported under one stream's name.
2. **It explains the otherwise puzzling smallness of the step.** A strong global product should
   buy more than 7.6%. It buys little precisely because most of its information was already in
   the tier — and that is a *better* story than the one currently written, provided we say why.
3. **The headline "geography beats satellite" is not safe as stated.** Geography's 10.8% is
   cleanly ours. The satellite step is not clean, so the comparison is between a measured
   quantity and a mixture.

---

## 4. What to do — and the version worth publishing

The minimal fix is a disclosure. The defensible fix is a genuine stream. **The impressive one is
to measure the difference between them**, because that difference is a general result about a
practice the whole field engages in.

**Replace / supplement `SATELLITE_LEVEL` with raw satellite AOD** — MAIAC / MODIS, already in
the project's GEE stack. AOD is an actual radiometric observation. It is not trained on
monitors, it does not contain our drivers, and it is available everywhere `Bud0` claims to
operate.

Then report the ladder **both ways**:

| variant | what the stream is | what it measures |
|---|---|---|
| `Bud0c-fused` | GHAP (as now) | what a practitioner gets by reaching for the best published product |
| `Bud0c-raw` | MAIAC/MODIS AOD | what an actual independent satellite observation is worth |

**The gap between them is the quantity nobody has published: how much of a fused product's
apparent value at a monitored city is recycled information rather than new observation.** It is
directly relevant to every study that uses a fused PM2.5 product as a covariate or a baseline,
and it falls out of a design we already have.

---

## 5. Draft pre-registration — C1/S3

To be lodged on OSF **before** any re-run, per the correction/new-test boundary in
`improvement_plan_2026-09-01.md` §0 and the F.84 lesson.

**Title.** Is the value of a satellite stream in a sensorless air-quality tier a measurement of
satellite information, or of recycled information?

**Background.** The scored `SATELLITE_LEVEL` stream is GHAP, a fused ML product trained on
~9,500 stations including the OpenAQ and CNEMC networks that supply this study's panel, and
predicted from a feature set that substantially overlaps the tier's other two streams.

**Design.** Re-run the decomposed bottom rung three ways on the identical stream-complete frame
(n = 47 after C7), identical learner, identical seed, identical LOCO folds:
`Bud0b` (drivers + geography) → `Bud0c-raw` (+ MAIAC AOD) → `Bud0c-fused` (+ GHAP).

**Registered predictions**, with refutation criteria stated first:

| # | prediction | refuted if |
|---|---|---|
| P1 | `Bud0c-raw` buys **less** than the 7.6% currently attributed to GHAP | raw AOD ≥ 7.6% |
| P2 | `Bud0c-raw` is nonetheless **> 0** — AOD carries genuine information | raw AOD ≤ 0 on the median city |
| P3 | `Bud0c-fused` − `Bud0c-raw` > 0, i.e. the fused product's excess is real and measurable | the fused product does not beat raw AOD |
| P4 | the excess is **larger at cities with more monitors**, the signature of leakage rather than of better physics | no association between excess and station count |
| P5 | `step.geography` (10.8%) exceeds `Bud0c-raw`, so "geography beats satellite" survives with an honest stream | raw AOD ≥ geography |

**What would change our conclusion.** If P1 is refuted, the current framing stands and the note
in §3.2 is a caveat rather than a correction. If P4 is refuted, the leakage is not detectable at
this sample size and must be reported as an argued risk, not a measured one — ⚠ with n = 47 and
a crude station count, P4 is the weakest test here and we say so in advance.

**Analysis.** Median of per-city RMSE ratios throughout, reported per metric, never averaged
across metrics (gotcha #74). Per-city stream coverage asserted with
`Budget.require_covers_units` (C7). Stratified by instrument class and by coastal/inland, both
of which were confounders in the previous round.

**Admissibility.** MAIAC AOD is admissible at `Bud0`: it is a satellite observation available
for a target with no local monitors. GHAP's admissibility is **the question under test** and it
is scored as a separate, explicitly labelled variant — not silently swapped in.

---

## 6. Knock-on items

- **`budgets.py`** — the `SATELLITE_LEVEL` comment reads *"van Donkelaar / GHAP annual level
  products"*. Both named products are monitor-trained fusions. The stream needs splitting into
  `SATELLITE_AOD` (an observation) and `SATELLITE_FUSED` (a derived product), with the latter's
  admissibility declared per use rather than assumed.
- **Van Donkelaar** anchors the production Kandy field's level. It is the same class of product
  as GHAP. This does **not** invalidate the Kandy anchor — Kandy has essentially no monitors in
  those networks, so there is little there to leak — but the asymmetry must be stated: the
  anchor is comparatively clean *because Kandy is unmonitored*, which is a point in the paper's
  favour and should be made deliberately rather than left implicit.
- **§3 of the manuscript** gains a paragraph on stream independence. A budget that admits a
  "satellite" stream must say whether it means an observation or somebody else's model.
