# Continuation research: testing the Kandy PM2.5 reconstruction against observations designed to refute it

**REFERENCE DRAFT (AI-written, 2026-10-11).** For the author to rewrite in his own words before it goes to anyone
(standing rule: the user writes all prose). It joins the external reviewer's four-step recommendation with this
project's information-value results (the ladder, F.115–F.124) and the sensor-placement design (F.99–F.103, OSF
`ad3py`), and is written to follow the submission of Thesis A, not to change it. Supervisor direction (2026-10): the
method part first; the sensor proposal waits. This document is that waiting proposal, re-founded.

---

## 1. The idea in one paragraph

Thesis A delivers an hourly one-kilometre reconstruction of Kandy's PM2.5 and establishes, line by line, which parts of
it are supported: the seasonal cycle and day-to-day sequence are, the level now rests on one regulatory station, the
local fraction is plausible but not identified, the nights are too high, and the neighbourhood pattern is a hypothesis.
The next phase does **not** build a better model. It **locks the current model as a hypothesis** — every prediction
written down and registered before any instrument is bought — and collects observations chosen because they could prove
it wrong. Any of the three outcomes the reviewer names is a result: spatial differences that survive (keep or improve the
map), broad patterns that hold but fail at one kilometre (a defensible resolution limit), or errors that turn out to be
temporal, instrumental or in the background assumption (the exact component to redesign).

## 2. What the thesis leaves open, and what is already known about testing it

| open question (thesis section) | what this project has already measured about testing it |
|---|---|
| Is the level right beyond one station? (3.2.3) | one regulatory station; level factor 0.80 [0.70, 0.92]; held-out 11 months, −1 % [−21, +20] |
| Are the nights too high, and why? (3.2.3, 3.2.6) | at the reference the night is 0.71 of midday, the model 1.17; humidity correction explains part only |
| Is the local fraction ~0.48? (3.2.4) | town-based urban increment 0.36 (lower bound), tracer 0.53 (two-sided); no rural reference exists |
| Does the 1 km pattern rank neighbourhoods? (3.3) | six independent nulls; within-cell spread exceeds between-cell; ρ ≈ 0.1–0.3 at 3–8 stations |
| What is a station worth? (ladder, Appendix A) | one station read daily −42 %, two −53 %, five −58 % daily error; as calibration only ~11 % |
| Does deliberate siting help? (F.103) | 43 dense networks, 601 stations: paired −0.044 [−0.095, +0.118] — undetectable |
| Can a campaign beat the free built-up layer at 1 km? (F.100) | needs a gain of +0.30 to +0.47 with 18 fitting sites; 96–304 sites to match the benchmark in one city |

The last three rows decide the design. A network of a few dozen sites **cannot be powered to show that the map is good**
at one kilometre; it **can** be powered to show where the map fails, and to measure quantities that resolve quickly
(the level at several points, the within-cell ratio, the night-time drainage, the diurnal shape). The design below is
built around tests with stated power, and states in advance which ones can only detect gross failure.

## 3. Phase 1 — provenance and model consistency (no new money)

Goal: make the existing evidence defensible before collecting more.

1. **CEA metadata and quality control.** Request through the R&D agreement: the AAQMS PM2.5 method and model,
   inlet height and siting, calibration and audit records, data-flag definitions, and the underlying record for
   2019–2026 (compare with the public AirShare values the thesis used). Settle the "manipulation" clause in writing.
2. **A calibration-versus-validation register.** One table listing every observation stream and what it did: trained
   the anchor (FECT sensors), sharpened the cycle (FECT), set the level (CEA 2019 → mid-2021), checked the level (CEA
   2022 →), checked the local fraction (CEA + AirShare IQAir), checked the season (NBRO), checked transfer (ten cities).
   Already largely in the ledger; the register makes it one auditable page.
3. **Final-model consistency.** Done for Thesis A (tag r11): field, figures and claims regenerated from one model
   vintage; local-fraction estimand reconciled (F.133). Carry the same rule forward: every figure rebuilt from its
   builder at each release, checksums in the verification report.
4. **The 2024–2026 discrepancy.** The station reads much higher after 2023 (partly because those days are mostly high-season) and the extension tier ~40 % low; settle with
   CEA whether the post-2023 record changed instrument, method or processing before any new campaign is calibrated to it.

Deliverable: a provenance note and the register; the decision whether the CEA station can serve as the reference anchor
for Phase 2 (if yes, the largest budget line of the earlier costing, a reference monitor at 10,000–40,000 USD, falls
away).

## 4. Phase 2 — reference-backed sensor evaluation (collocation)

Goal: know exactly what a low-cost unit measures in Kandy's humidity before trusting a network of them.

- **Where:** beside the CEA Kandy AAQMS (or, failing access, a rented reference instrument). One site, all units.
- **What:** 6–8 low-cost units (the sensor type planned for Phase 3), plus a temperature/humidity logger.
- **How long:** at least **30 days** per season (the US EPA performance-target minimum; the earlier plan was corrected
  to this from two weeks), in **two contrasting seasons** — north-east monsoon (high, dry) and south-west monsoon (low,
  wet) — because humidity response is the known failure and the thesis's night-time defect is humidity-sensitive.
- **Locked evaluation block:** the last third of each season's collocation is sealed (hash committed) and used only
  once, to score the calibration fitted on the first two thirds.
- **Quantities:** bias, slope and intercept against reference; hourly humidity response (fit hourly-RH correction vs
  constant-RH, the two scenarios the thesis carries); unit-to-unit spread; drift (repeat collocation at the end of
  Phase 3); the diurnal shape each correction produces against the reference night/midday ratio (0.71).
- **Registered predictions:** the hourly-humidity correction brings the corrected night/midday ratio within ±0.1 of the
  reference; the constant-humidity correction does not (thesis prediction). Either outcome decides the correction.

Deliverable: a Kandy-specific calibration with uncertainty, the humidity verdict, and the drift rate that sets the
recalibration interval for Phase 3. This also settles the FECT sensors' calibration that the anchor is trained on.

## 5. Phase 3 — a distributed network as a falsification test of the 1 km field

Goal: discover which parts of the field survive genuinely independent testing.

**Locked hypothesis.** Before deployment, freeze the model version (release tag), and for every planned site and hour
write down the model's prediction and its interval; register the file's checksum and the tests below (OSF).

**Network.** Re-use the registered 35-site design (`ad3py`), re-purposed from "learn the pattern" to "test the pattern":

| stratum | sites | purpose under the falsification design |
|---|---:|---|
| anchor (at the reference) | 1 | ties the network to the reference continuously; drift check |
| contrast (cLHS over physics covariates) | 12 | spans the model's predicted range (emission surface 65× p10→p90), so a failure to rank is informative |
| paired within-cell | 9 (pairs) | measures sub-kilometre variation directly — the quantity the thesis says dominates |
| vertical (8–291 m above the local floor) | 5 | samples the floor-to-ridge axis no network has sampled; tests confinement |
| receptor (schools, hospitals), held out | 8 | an untouched exposure-relevant test set |

**Tests, with what each can and cannot show** (power from F.100/F.103 and the thesis's detection limits):

| test | statistic | power | outcome it decides |
|---|---|---|---|
| T1 level | model − observed at each site, pooled and by stratum | high: tens of site-months | level at many points, not one; site-to-cell relation behind the CEA correction |
| T2 within-cell ratio | paired-site ratio vs model (1.0 within a cell) and alternatives | high: resolves in about **7 days** (earlier analysis: 1.044 vs competing 1.58 and 27.5) | outcome 2 directly — how much variation a 1 km cell hides |
| T3 drainage sign | night-time floor > slope sign per night | high: unit is the night (63 % over 90 nights) | whether the confinement term's physics is right |
| T4 diurnal shape | night/midday ratio by site | high with Phase 2 calibration | whether the night defect is everywhere or site-specific |
| T5 rank at 1 km | Spearman, model vs observed across contrast sites | **low**: detects only a gross failure (detection limit ~0.35–0.51); cannot show the map beats the built-up layer | outcome 1 vs 2 only if the result is extreme; stated in advance |
| T6 background | rural/upwind sites (Phase 4) vs model B(t) | moderate | outcome 3 — background assumption |

The decision rule is registered with the tests: each test's pass, fail and inconclusive regions are fixed in advance,
and the component each failure points to (anchor, background, pattern, instrument) is named in advance.

**Information value as the design principle.** The ladder shows that the dominant gain for the daily city level comes
from stations **read every day**, not from network size: one daily-read station cuts daily error by about 42 %, five by
58 %, and calibration-only use gives about 11 % whatever the number. So: (a) the anchor and two to three contrast sites
should report continuously and be assimilated daily (a temporal benefit independent of the spatial test); (b) the
remaining sites are justified by the spatial and vertical tests, not by the daily mean; (c) siting choice should not be
expected to improve what the network can learn (F.103), so sites are chosen to span the model's predicted contrasts and
the logistics constraint, not optimised for fitting.

## 6. Phase 4 — the regional background and composition

Goal: test whether the decomposition's background and local increment have a physical interpretation.

- **A rural, upwind reference.** The thesis's urban-increment estimate is a lower bound only because every regional
  sensor sits in a town (F.134). One clean rural site upwind of Kandy for the prevailing monsoon (north-east and
  south-west, so possibly two seasonal positions) turns that bound into an estimate of the local share at the city
  centre, and checks B(t) day by day (test T6).
- **Meteorology.** A surface station with wind and rain inside the basin (Kandy has no public wind record; the wind
  layer's parameters are priors) and, if possible, a ceilometer or radiosonde days for the boundary layer.
- **Composition (if resources allow).** Filter sampling at the city-centre and rural sites in parallel for PM2.5 mass,
  OC/EC, water-soluble ions and elements. Secondary inorganic aerosol and regional tracers at both sites separate the
  locally emitted primary share from locally formed and regional material — the distinction the thesis bounds but does
  not identify (its chemistry is a model-based consistency check).

## 7. How the outcomes feed back

| outcome | evidence | model change |
|---|---|---|
| 1 — spatial differences survive | T5 positive and T2 near 1, T1 consistent across strata | keep the pattern; refit κ and the confinement scale on the network |
| 2 — broad pattern holds, fails at 1 km | T2 far from 1, T5 null, T1/T3 consistent | publish a resolution limit; deliver the field at the scale that survives |
| 3 — errors are temporal/instrumental/background | T4 or T6 fail, Phase 2 humidity verdict | redesign the anchor's correction or the background; the pattern question is premature |

Each is a publishable result; none requires the model to look good.

## 8. Budget and time (to be refreshed with local quotes)

From F.101 (published prices; import duty, mounting, power, connectivity and labour still unpriced for Sri Lanka):
low-cost units 38 + 6 spares ≈ **9,900 USD**; a reference anchor **10,000–40,000 USD** — **zero if the CEA AAQMS can
serve** (Phase 1 decides). Phase 4 adds a rural unit, a met station and, optionally, filter sampling and laboratory
analysis (to be quoted). Re-scoping the network saves little (trimming the contrast stratum 12 → 10 saves ~450 USD), so
the decision is what the network claims, not what it costs.

Indicative sequence: Phase 1, 2–3 months (mostly waiting on CEA); Phase 2, two collocation seasons (~6–8 months
elapsed, can overlap Phase 3 preparation); Phase 3, at least 12 months to span both monsoons; Phase 4 alongside
Phase 3.

## 9. Outputs

- A registered falsification protocol (OSF), lodged before any instrument is bought, with the frozen model hash.
- Paper: Kandy low-cost sensor performance against a regulatory reference in a humid tropical valley (Phase 2).
- Paper: which parts of a sparse-data PM2.5 reconstruction survive an independent network (Phases 3–4), reporting all
  three outcome types.
- The information-budget paper (already drafted) cites this as its prospective test in a city of the kind its panel
  under-represents.
- Basis for later exposure and policy work: only the parts of the field that survive are carried into risk assessment.

## 10. Risks

- **CEA access or metadata not granted** → rent or borrow a reference instrument for Phase 2; the post-2023 record
  question stays open.
- **Sensor failure and drift in monsoon humidity** → spares, repeat collocation, drift budget from Phase 2.
- **T5 inconclusive** (expected, given its power) → stated in advance; T2/T3/T4 carry the spatial conclusions.
- **Site access and security** → logistics screen before optimisation (19,467 of 25,600 cells within 400 m of a road).
- **Data conditions** (CEA notification of processing, citation, sharing outputs) → agreement first.
