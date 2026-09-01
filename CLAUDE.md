# Kandy PM2.5 — Satellite-ML and Cross-City Spatial Estimation

Undergrad thesis (Daminda Alahakoon, U. Peradeniya). **Redesigned 2026-05-08** — see [`docs/REDESIGN_2026-05-08.md`](docs/REDESIGN_2026-05-08.md) and [`docs/AUDIT_2026-05-08.md`](docs/AUDIT_2026-05-08.md).

**Deployment pipeline (two stages):**
- **Stage A — Temporal anchor.** Satellite-ML over Kandy. v1 daily XGBoost (2003–2025, KOALA-anchored) + v3 hourly LGBM/CatBoost/XGB blend with CV+ Mondrian conformal UQ (2018–2026, per-sensor FECT-anchored residual target).
- **Stage B — Cross-city spatial residual learner.** ConvCNP (deepsensor) trained on N=3 source cities (Medellín, Chiang Mai, Kathmandu), predicts `pm25 − c_prior_scaled` against a per-city scaled GEOS-CF prior. Student-t(df=5) likelihood + per-(city × hour-of-day) Mondrian conformal UQ. Applied zero-shot at Kandy.

Native resolution **1 km hourly**. Single target: **Kandy**.

**Supporting experiments (documented, not in deployment pipeline):**
- Cross-continental PINN transfer (Mel → ChiMai, FourierPINNV3 TD-PDE). Code in `src/stage2_transfer/`.
- SharedTerrainAnsatz identifiability diagnostic (rigid Whiteman ansatz, all 6 params bound-saturated). Code in `src/stage3_pinn/models/shared_terrain_ansatz.py`.
- PVAF v1 — Physics-based Valley Analogue Finder, source-city expansion tool. Code in `src/pvaf/`.

> **🟢 [`CONTEXT.md`](CONTEXT.md) — read this first.** One page (<250 lines) of the load-bearing
> facts: the model in one equation, the numbers you may quote, the numbers that are **retired**,
> the evidence state per axis, the open questions, and the data situation. It is the fast path;
> this file, `PROJECT.md` and the ledger stay authoritative. **Update it whenever a headline
> number, a refutation or an open question changes.**

## Session Protocol (READ FIRST)

**Session start:** Output this briefing before responding:
```
Model: additive decomposition, [tiers current] | T-lock [state], QA [value]
Partition: f ≈ [value], [how set]
Shipped: preprint [state] | webapp [state] | release repo [state]
Pending: [top 2 — mark user action vs model work]
Git: [last commit message]
```
Quote from the NEWEST `## Current State` block only — the ones below it are archived
narrative. **Never brief Stage A/B metrics as project status:** the ConvCNP zero-shot maps
and the PINN work are supporting experiments with no production role, and the v1/v3 anchor
R² is an internal component number, not the deliverable. **f ≈ 0.48**, not 0.244.
Skip if first message is a quick question (<10 words) or `/session-start`.

**Expert input:** When user pastes >200-word analytical block, list planned changes and confirm before coding.

**Interruption recovery:** When [Request interrupted by user] occurs, stop and wait.

**Session end:** When user signals done, say: "Want me to run /update-docs before we close?"

**Skills:** `/session-start` `/update-docs` `/kaggle-status` `/kaggle-train [dir]` `/stage-report [1|2|3]` `/pop-sci [1|2|3]` `/handoff`

## Context Hygiene

1. Never read CLAUDE.md in full mid-session — Grep for specific sections.
2. Cap all Bash output with `| head -100`. Training logs: last 20 lines only.
3. Delegate to subagents for any task needing >3 file reads or >200 lines of output.
4. Compact proactively at task boundaries, not reactively.
5. Start fresh sessions for distinct task types. Use `/handoff` between sessions.
6. **This file holds CURRENT state only.** When a `## Current State` block's conclusions have
   been absorbed into a newer block, the gotchas, `PROJECT.md`/`PROJECT_ARCHITECTURE.md` or the
   epistemic ledger, move it to the archived-state index (one table row + the SESLOG date) —
   the narrative already lives in SESLOG and does not need to be here twice. Audited and
   enforced 2026-08-06: the file had reached 1,301 lines against a ~250-line rule because ten
   months of blocks had stacked up. Target: **keep it under ~900 lines and falling.**

### ⏸️ DEFERRED — carry forward (2026-08-12)
| item | state | blocker / next action |
|---|---|---|
| **Commit-trailer strip** | backups exist: `backup/pre-trailer-strip-20260811-0029` (framework `e87d2ba` · release `b659f65` · webapp `725dd87`) | `git filter-branch` **blocked by the permission classifier**. Needs a Bash permission rule, or the user runs the three commands in SESLOG. Scope 63/64 · 10/10 · 46/301. |
| **Zenodo DOI badge** | release `v1.1.0` published, integration enabled | Zenodo had **not indexed** at last check. Verify at `zenodo.org/account/settings/github/`; if the webhook did not fire, delete + recreate the release. Then add the badge to README + `doi:` to CITATION.cff. |
| **Forecast drivers** | documented, not built | Add **ECMWF open data** (free, 0.25°, real-time, **includes precipitation** — the current CFAPI driver set has none) as a second driver; then Aurora's air-pollution checkpoint for a 3-member ensemble. Paper 2. |
| **Supervisor email** | drafted | Name corrected to **Ranatunga**. User to send. |
| **Data letters** | **ALL 3 SENT 2026-08-12** | FECT · MOSDAC awaiting reply (follow up 2026-09-02). |
| 🟢 **CEA REPLIED 2026-08-12 — THE DATA EXISTS AND IS FREE FOR ACADEMIC USE** | formal process required | **Kandy regulatory AQMS, HOURLY, 2019 → 2026-05**: PM2.5, PM10, gases, and **full met including a rain gauge and wind speed/direction**. Known gap **2021-07 → 2022-10** (no funds to operate). Needs a letter on **university letterhead to the Director General**, copy DDG (Environmental Protection), scans emailed to dg@ / chedus@ / randd@ / AQ@cea.lk, then a **signed agreement via the R&D Unit**. Conditions: notify CEA in writing of any data "manipulation" and obtain authorisation first; cite CEA; send final outputs. Contact: Akila Jayasundara (SEO), Air Quality, Noise & Vibration Monitoring. |
| 🔴 **PDN Uni runs its own islandwide microsensor network** | unexploited — and it is the user's OWN university | CEA named it alongside NBRO. Internal access should be far faster than any external request. **Chase this first.** |
| ⚖️ **"Manipulation" clause** | needs clarifying with R&D | The model applies bias correction, gap handling and aggregation. Ask R&D explicitly whether routine QA/analysis counts, so the agreement is not breached by ordinary work. |
| **W5 — FECT calibration** | **CORROBORATED 2026-08-22 (F.64)** | Akurana full-record mean 17.8 against a BAM-anchored published study's ~18–19. The calibration slopes are no longer wholly unchecked. |

## Current State (updated 2026-08-14, 📄 **NEW PAPER BUILT END TO END, 28 pp**)

The preprint is superseded. A new manuscript was defined, evidence-frozen, drafted, figured,
adversarially reviewed and built. It lives in `kandy_pm25/docs/paper/`, targets **ACP via
EGUsphere**, and stands at **28 pp, 11,753 words, 11 figures, 61 references, 3 CHECK flags**.

- **How it is built** → `PROJECT_ARCHITECTURE.md` § "Manuscript build".
  **Edit `draft_s*.md`, never `manuscript_kandy.md`** — the latter is a build product.
- **What the checking produced** (14 numerical corrections, 12 review findings) → `PROJECT.md`
  § "2026 manuscript". Narrative → SESLOG 2026-08-13/14.
- Phases 0 to 8 complete. **Phase 9, circulation to the four readers, is the user's step.**

### 🔴 Three corrections that change how things must be SAID
1. **f = 0.4828**, from `kandy_partition_v2.json`. `additive_partition.csv` is stale at 25.3%
   and renamed `_v1_superseded`. Never quote it.
2. **The gauge is not exact.** The field runs **+0.39 to +0.56%** above the anchor every year.
   Say "to within 0.6 per cent". The old G1 check compared two fields sharing the drift.
3. **eps0 for Kandy is 3.69**, not 2.573; it scales with mean accumulation, which the cap moved.

### 🟢 NBRO is a live data route
Nirmani et al. (2025) obtained **daily Kandy PM2.5 for 2021–2022 from NBRO on official
request**. Letter drafted (`docs/EMAILS_TO_SEND.md` #4), alongside a Met Department letter (#5)
for station meteorology. NBRO is cheaper than CEA: no R&D agreement, no manipulation clause.
**Their Table 1 has now been read directly — see the 2026-08-22 block below.**

## 🆕 Literature-recovered Kandy ground truth (2026-08-22, ledger F.64–F.67)

Three papers supplied by the user were read. They produced **the first independent checks on the
Kandy field in the project's history**, one corroboration, one contradiction, and one live
acquisition lead.

| finding | ledger |
|---|---|
| 🟢 **W5 CORROBORATED** — FECT Akurana full-record mean **17.8** against a BAM-anchored published study's **~18–19** | F.64 |
| 🟢 **NBRO Kandy (KAN), 24-h, N=360/yr**: obs **19.6** (2021) / **22.7** (2022) vs model at that pixel **19.74 / 22.11** — **+0.7% / −2.6%** | F.65 |
| ⚠ **A BAM-calibrated LCS at Kandy** (7.2731, 80.6117) reads **19.49** where the model says **25.01** — **+28% high** | F.65 |
| ⚫ **A reference-grade BAM-1020 stood at Torrington Park, KANDY** — **but it is DEFUNCT (user, 2026-08-22)**. Provenance for the published records; **not** a data route. **CEA is the only route to a Kandy reference monitor.** | F.65 |
| 🔴 **W6 REOPENED** — Kandy PMF: **traffic 7.6%**, **biomass burning 14.1%** of PM2.5 mass | F.66 |
| ⚠ Nirmani's meteorology is **Open-Meteo/ERA5 reanalysis**, not station data — their Kandy CBPF source attribution is weak evidence | F.67 |
| 🟢 **A 25-site Kandy PM10 transect measures the spatial ceiling's CAUSE** — **110 → 4 µg/m³ over 300 m**, R² **0.82** vs traffic. The signal is huge but **sub-grid**: decay length tens–hundreds of metres against a 1 km cell | F.68 |
| 🔴 **Scored: observed spread across Kandy 85×, model spread 1.23×.** Paired microsites 300 m apart: **27.5× observed vs 1.000× modelled** (same pixel). Rank ρ +0.44, n.s. **First within-Kandy spatial test ever run** | F.69 |

### 🔴 The level discrepancy this opens
Of four independent Kandy point records, **three sit below the model** and **one matches it**.
The three low ones are all low-cost sensors carrying a downward calibration correction; the one
that matches has an **undocumented instrument**. This is not resolvable from the literature and
it is a **level** question — the axis the programme calls strong. **State it as an open
discrepancy; do not resolve it by picking the record that agrees.**

### 🔴 What must no longer be said
**"Kandy ~90% vehicular" is refuted as a mass share.** The defensible statement is: *traffic
dominates the local increment's sub-daily **timing** (measured, F.23); it is a **minority of
local PM2.5 mass** (measured, F.66).* This is the strongest case yet for wiring the
sector-weighted `S_emit` — but as a **correctness fix, not an expected skill gain** (the spatial
ceiling F.56/F.61 means it will not move ρ), and Kandy's burning sector has **no admissible
FIRMS proxy** (incense, oil lamps and domestic burning are invisible to FIRMS, exactly as
Kathmandu's kilns are).

## Model formulation (target architecture, 2026-08-18)

The model is being restated as an **information-tiered grey-box decomposition**: a hierarchical
latent-process model with an explicit **observation operator**, **declared information budgets**
(`Bud0` sensorless → `Bud4` spatial network), and four guaranteed properties — **P1**
conservation, **P2** monotone skill under added data, **P3** exact degradation between tiers,
**P4** declared identifiability. Spec: [`kandy_pm25/docs/MODEL_SPECIFICATION.md`](kandy_pm25/docs/MODEL_SPECIFICATION.md);
reasoning `model_formulation_2026-08-18.md`; ML placement `model_formulation_ml_map_2026-08-18.md`.

- **The largest gap is that there is NO observation model.** Point sensors are compared to an
  areal field by naive co-location — the origin of gotcha #75. `H_k`, `b_k`, `sigma_rep` must
  exist **before** any CEA/NBRO/Met data is ingested, or the first comparison repeats it by hand.
- **Second gap: no tier registry.** Tiers live in filename suffixes and scattered flags, so
  admissibility is enforced by discipline, not construction (gotchas #68 and #73 were both
  caught by audit after the fact).
- ⚠ **Three claims NOT to make:** "every layer is ML" (B's dilutive part and P's shape are
  *measured* unlearnable) · "fully captures atmospheric physics" (no chemistry, no secondary
  aerosol, no deposition, no vertical structure; `A_transport` unscored) · "works coastal"
  (the panel is 10 cities, **all valley/basin, zero coastal**). "Forecasting" in a title
  requires a per-lead skill curve first.
- Defensible framing: *an information-tiered grey-box decomposition for urban PM2.5 in
  data-scarce cities, with exact degradation between tiers and monotone skill under added
  observation.* The contribution is the **declared budget with guaranteed nesting**, not the
  physics and not the ML.

## Budget-ladder validation — RE-VALIDATED 2026-08-23 (ledger F.50–F.53, **corrected by F.84–F.87**)

**Modular decomposition built** (`src/modular/`: budgets · observation model · constraints ·
shrinkage · tier harness · production bindings · sector emission surface; **68 tests**).
Spec [`kandy_pm25/docs/MODEL_SPECIFICATION.md`](kandy_pm25/docs/MODEL_SPECIFICATION.md);
registration `docs/prereg_modular_validation_v2_2026-08-18.md` (option C + 2 amendments).

**Frame: 47 cities scored, 4 latitude bands, 32 countries, 32,396 city-days.** OpenAQ ingest
46/46 attempted → 37 retained (9 excluded, named, never replaced) + 11 CNEMC. All six gates run.

🔴 **THE 2026-08-19 STEP GAINS ARE RETIRED (F.84).** The scored `Bud0` used **one of the
three streams its budget admits** — drivers only, no satellite level, no static geography — so
every gain above it was measured against an artificially weak baseline. Fixed in code by
`Budget.require_covers()`; re-registered at **https://osf.io/g6hqb/** and re-run.

**THE BOTTOM RUNG IS NOW DECOMPOSED**, so each globally available stream is measured on the same
footing as a monitor (median RMSE across cities):

| rung | median RMSE | step |
|---|---:|---:|
| `Bud0a` reanalysis drivers only | 21.94 | — |
| `Bud0b` + static geography | 20.31 | **10.8%** |
| **`Bud0c`** + satellite level — *the spec-compliant `Bud0`* | 19.99 | **7.6%** |

🟢 **Static geography (10.8%) beats the satellite level (7.6%)** — an annual satellite level
cannot touch day-to-day variance, which is what daily RMSE is made of.

**Step gains from `Bud0c` (median % RMSE reduction) — QUOTE THESE:**

| step | pooled | deep-trop | tropical | subtrop | temperate |
|---|---:|---:|---:|---:|---:|
| `Bud0c→Bud1` (+2 stn) | **17.9** | 21.9 | 6.7 | 29.7 | 33.5 |
| `Bud1→Bud2` (+6 stn) | **0.1** | 0.9 | 0.1 | 0.3 | 1.1 |
| `Bud2→Bud3` (+background) | **40.6** | 8.5 | 39.8 | 36.0 | 31.6 |

⚠ The **band ordering flipped**: the first two stations now buy most in the **temperate** band
(33.5) and least in the **tropical** (6.7), where previously the deep tropics led at 38.5. And in
the deep tropics the background rung **collapses from 28.1 to 8.5** once a satellite level is
present — the satellite substitutes for the background there. ⚠ Subtropical and temperate cells
are **n=7**; small.

🔴 **THREE CONFOUNDS CAUGHT BY REGISTERED GATES, not by review** — each invisible in the pooled
numbers and each would have reached a paper:
1. **country × latitude** (Amendment 2) — the min-GEE design made the mid-latitude arm 33
   cities all Chinese, aliasing band with network.
2. **driver completeness × band** (F.51) — BLH coverage differs 5.1 pp; re-ran without BLH,
   only the top-two ordering flips (a 0.013 gap), the temperate deficit survives.
3. **instrument class × band** (F.52) — the deep-tropical cell is 69% LCS, the rest
   reference-dominated.

🔴 **"More in-city stations buy nothing" is a REFERENCE-NETWORK result.** Median `w_Bud2`:
reference **0.000**, LCS **0.900**. LCS carry per-device error, so averaging more of them cuts
noise. **Never state V4 unconditionally.** The pilot's 2.9% (F.50) must not be quoted — its
`Bud0` had lat/lon and could identify the city.

🔴 **Two registered priors REFUTED**: `Bud0→Bud1` does NOT dominate (background does); and
`Bud0` is worst in the **temperate** band (normalised 1.194), not the deep tropics (0.792).

🔴 **And five of eight re-validation priors refuted (F.85)** — including my headline one: I
registered the satellite level as the largest step below the ground rungs at 25–45%; it is
**7.6%**. 🟢 **The coastal test held strongly:** a satellite level helps coastal cities **four
times** as much as inland (24.4% vs 6.2%, n=21 vs 27; **not** confounded with instrument class,
Fisher p=0.38).

🔴 **F.53 — the class/band confound CANNOT be sampled away.** Worldwide only **5** deep-tropical
clusters have ≥10 concurrent reference stations, against 32 temperate. *The regime that most
needs a sensorless method is where reference monitoring is scarcest* — a finding in its own
right. Decision: report class-stratified throughout; treat the **LCS stratum as the Kandy
analogue** (Kandy's sensors are low-cost); do not chase a de-aliased draw.

⚠ **Unchanged caveat:** `Bud3`'s background is an outer-ring proxy from the SAME network in
every city, so its large gains partly measure "more of the same network". Only a true regional
network settles it — **which is exactly what NBRO would be at Kandy.**

**Sector-weighted `S_emit`** (`src/modular/emission.py`): `S = norm(Σ w_k · norm(proxy_k))`
using the `emix` already declared per city — which previously fed only `e(t)`, so Kathmandu
asserted 50% burning in TIME and 100% roads in SPACE. Population + FIRMS surfaces pulled for all
11 panel cities. `vehic=1.0` reproduces the traffic surface bit-exactly. **Built and tested, NOT
wired into production.** ⚠ Kathmandu returns **zero FIRMS detections** (kilns are continuous
combustion, not open flame) → its burn sector falls back to a flagged placeholder; industry has
no proxy and no admissible fallback. **⚠ F.66 shows Kandy has the same problem.**

**GEE cost assumption was WRONG** and is corrected: daily/static pulls are **minutes, not days**
(ERA5-Land daily 5.3 s/city via `getRegion`; GHS-POP 5 s; FIRMS 26 s). The multi-day rule
applies to hourly Drive exports only. Two real traps: gotcha #44 memory limit on 2-yr hourly
BLH (fixed by quarterly chunking) and **ERA5-Land has NO DATA OVER WATER** — 4 coastal/island
cities failed until falling back to global ERA5.

## The three axes — measured evidence state (2026-08-19, ledger F.55–F.62)

The model reconstructs an hourly 1 km field, but its **evidence is anisotropic**. All three axes
have now been tested on the widened frame, and two have measured ceilings.

| axis | evidence | status |
|---|---|---|
| **level, daily** | 47 cities, 4 bands, 32 countries; monotone under added data; background gain 75% reproduced by an INDEPENDENT network 89 km away (F.54) | **strong** |
| **sub-daily shape** | transfers in the **deep tropics** (+25.8% vs flat, r 0.63, ~1 h phase error) and **nowhere else**; pooled it is 5.5% WORSE than assuming no cycle (F.55) | **regime-limited** |
| **spatial pattern** | **rho ~ 0.2–0.28 ceiling**, unmoved by four successive attempts (F.56/F.58/F.59/F.61) | **ceiling measured** |

🟢 **2026-08-22 — the ceiling's CAUSE is now measured in Kandy itself (F.68).** A 25-site
PM10 transect with per-site traffic counts (Elangasinghe & Shanthini 2008, 2004–06) records
**110 → 4 µg/m³ over 300 m** inside one botanical garden, and **R² = 0.82** against traffic
intensity. Kandy's within-city signal is *enormous*; its **decay length is tens to hundreds of
metres**, and a 1 km cell integrates over exactly that decay. **The pattern is sub-grid by
construction, not missing from the data.** This upgrades the ceiling from "our networks are
inadequate" to a **change-of-support** statement, and retrospectively justifies `Bud4`'s
demotion. ⚠ It does NOT resolve W6 — roadside PM10 *spatial variance explained* and ambient
PM2.5 *mass share* are different quantities.

🔴 **The spatial ceiling survived proper instrumentation.** A full LUR predictor set — road
length by class at 50/100/300/500/1000 m, distance-to-road, NDVI, tree cover, water, land-cover
fractions, built volume, population, night lights at 4 radii, 636 stations, 47 cities — moved
pooled rho from **+0.273 to +0.275**. The literature's strongest predictor ("major roads within
100 m") buys nothing here. Published LUR reaches R² 0.43–0.83 because those campaigns **site
monitors deliberately across land-use contrast**; regulatory and LCS networks are sited for
compliance, so ours is a convenience sample with coordinates, not a LUR design.

🔴 **`Bud4` is UNSUPPORTED as specified.** A spatial network does NOT make `P` estimable:
inverse-distance interpolation between a city's own stations is **worse than assuming the city
is uniform** (F.60), and a transferred LUR barely beats a population raster (F.61). Every other
rung of the ladder is validated; this one is a declared design assumption and must be labelled
as such.

🔴 **The diurnal dilution term is ~zero.** Fitted exponent **0.054** against 1.0 for pure
inverse-BLH dilution — a ~40× diurnal swing in boundary-layer height produces almost no swing in
city-mean PM2.5, because in `PM = B + local` only the local increment dilutes while `B` is
already well mixed. So there is no physical component to peel off and transfer (F.62). The
civil-vs-solar-time sub-hypothesis is **refuted by construction**: true offsets are median
+0.29 h, max +1.87 h, against a 7.5–8 h phase error.

**⚠ ACQUISITION CONSEQUENCE — this changes the CEA/NBRO priority.** Do **not** request the CEA
passive NO₂ network as a fix for `P_local`; its value is the `f` partition and local activity
tracing (F.45). **NBRO (regional background) is the acquisition that pays** — the background rung
is the largest measured gain in the programme and 75% of it survives an independent network.
**⚫ 2026-08-22 correction: the Torrington Park BAM is DEFUNCT** (user). It anchored the
published RF-CNN calibration and Dhammapala's correction, but it is not a data route. **CEA is
the only route to a Kandy reference monitor**, and it alone would settle the level discrepancy
(W11) and the W6 source-mix question.

🔴 **AND THERE IS NO FREE SUBSTITUTE (F.63).** Sri Lanka has three OpenAQ locations, all inside
the admissible 30–300 km donor window — Colombo at **93 km, reference-grade, already on disk**.
Tested: Kandy–Colombo daily **r = 0.604** (≈0.70 attenuation-corrected) against a benchmark
median of **0.923** at that distance — **the weakest of all 20 donor pairs**. The central
highlands decouple coastal Colombo from inland Kandy, especially in the SW monsoon.
**Do not re-propose Colombo as a background donor.**

Docs: [`docs/spatial_diurnal_remediation_plan_2026-08-19.md`](kandy_pm25/docs/spatial_diurnal_remediation_plan_2026-08-19.md)
(plan + outcomes) · `MODEL_SPECIFICATION.md` §10.3 · ledger F.55–F.62.

## Archived state — the 2026-06 → 2026-08-11 arc (narrative in SESLOG)

These were separate `## Current State` blocks. Their narrative is in `memory/SESLOG.md` at the
dates given; the durable outcomes are already folded into the live blocks above, the gotchas,
`PROJECT.md`, `PROJECT_ARCHITECTURE.md` and the epistemic ledger (`F_epistemic_ledger.md`).
Kept as an index so nothing is silently lost.

| Arc | Outcome that survived | SESLOG |
|---|---|---|
| Webapp narrative surface + mobile defects fixed | 904 px overflow was a LATCH not a styling slip; gotchas #78/#79 | 2026-08-11 |
| **THE PARTITION RESOLVED BY PHYSICS — f ≈ 0.48** | coherence cap, ledger **F.43**; not tunable (0.477–0.502) | 2026-08-10 |
| Partition route closes — capability stated, no sixth attempt | hourly split declared unidentifiable; **F.40/F.41** | 2026-08-07 |
| Extension tier could not produce episodes — found, fixed | tail correction **F.37/F.39**; gotcha #76 | 2026-08-07 |
| Both re-measurement routes closed; a shipped assumption contradicted | fuel crisis has the WRONG SIGN; **F.35/F.36** | 2026-08-07 |
| The spatial estimator was wrong — found, fixed, validated | per-hour estimator, 6 of 9 significant; **F.32–F.34** | 2026-08-07 |
| W7 closed, emails drafted, NBRO check refreshed | eps0 does NOT transfer; **F.30/F.31** | 2026-08-06 |
| W10 closed, forecast intervals adaptive, INSAT reopens diurnal | e(t) evening lobe FITTED; **F.29** | 2026-08-06 |
| Reviewer pass — 8 major defects fixed | floor ≥0.41 vs headline 0.25; **F.26–F.28** | 2026-08-06 |
| A spatial ground truth for Kandy exists (CEA NO2 network) | 10 sites 2013–17; **F.23–F.25**, W4 closed | 2026-08-06 |
| f estimated not assumed — five converging lines | hierarchical 0.392 [0.258,0.525]; **F.21/F.22** | 2026-08-06 |
| Background arc closes — 5 rebuilds rejected, limitation surfaced | **F.18/F.19**; the gap is a MEASUREMENT | 2026-08-03 |
| Decomposition shown over-determined | 4 constraints on 3 DOF; **F.17** | 2026-08-02 |
| B(t) externally checked for the first time | NBRO ratio 1.12 to P25, daily r 0.37; **F.14** | 2026-08-01 |
| A2 anomaly target tested — premise REFUTED; A4 closes on evidence | swing 0.696 < patch 0.787; **F.16** | 2026-08-01 |
| Consolidation v3 built twice, both rejected — the seam is a LEVEL problem | **F.15**; background day-to-day is advected, not local | 2026-08-01 |
| Literature sweep — GNN closed with an external number, competitor found | GraPhy < 0.16 sensors/mi2 (Kandy 0.023); EGU26-9786 to cite | 2026-08-01 |
| Daily-B seam quantified; re-level built + REJECTED | `B > T` in 28.5% of hours; ledger **F.13** | 2026-07-27 |
| Kandy webapp forecast tier shipped | demonstration tier, OOD ×1.35, seam closed; **F.12** | 2026-07-27 |
| Panel expansion pre-registered + forecast leakage found | quote **+0.120**, never +0.223; gotcha #68 | 2026-07-27 |
| Preprint claim audit — 13 defects | A4 → Option 3; gotchas #68/#69 | 2026-07-26 |
| Weak-point pass — f disclosed as a prior | superseded 2026-08-06 by the five-line estimate | 2026-07-26 |
| Audit arc — N=10 Bogotá, 5th spatial null, GEMS rejected | N=10 panel; gotchas #66/#67 | 2026-07-26 |
| additive_v3 ε-floor shipped + UI U1/U3 | v3 = shipped tier; gotcha #65 | 2026-07-21 |
| Rain arbitration — IMERG ships, ERA5-Land rejected | gotchas #63/#64 | 2026-07-21 |
| Phase 5 Kandy propagation complete | extension tier 2024–26, B2 wind port; gotchas #61/#62 | 2026-07-21 |
| Medellín "ideal deliverable" improvement loop | B2 wind = validated method; A2 rejected | 2026-07-19, 07-16 |
| Forecast expansion validated at Medellín | F-K1/F-M0/F-M2 PASS | 2026-07-11 |
| Public webapp v2 — core<periphery inversion FIXED | the **increment split**; gotcha #57 sibling | 2026-07-10 |
| Public webapp shipped + engine audit | QA gate, reconstruction parity 0.0014 | 2026-07-05 |
| Preprint rewrite + N=9 Medellín + presentation pass | spatial skill-law NULL; gotchas #58/#59 | 2026-07-02 |
| Evidence-hardening round (sensitivity, ablation, N=8) | S1–S4 artefacts; additive vindicated +26% vs −0% | 2026-07-01 |
| Kathmandu full-model validation + preprint built | best-in-panel showcase; gotcha #57 | 2026-06-30 |
| Multi-city ground-truth validation (N=5) | the transfer design itself; gotcha #56 | 2026-06-27 |
| SERENDIB / GeoAQ-Zero four-track ML arc | T-a PASS, U PASS, I partial, **S NULL** | 2026-06-13 (pts 1–5) |
| W2 transboundary verdict | regional share is SEASONAL, not chronic | 2026-06-13 |
| Deliverables: reports, release repo, model bible | the FOUR-target propagation rule; gotcha #55 | 2026-06-07 |

**Do not re-derive these.** If a question here looks open, check `§ 4 Closed — do NOT re-litigate`
and the ledger before spending anything on it.

## Model & Stage Reference (stable — not session state)

### 🎯 PRODUCTION — Additive background+increment decomposition ✅ HEADLINE (2026-06-05)
**The deployable Kandy PM2.5 model.** Replaces the held ConvCNP zero-shot maps as the production spatial product. Full plan: `docs/kandy_production_plan_2026-05-29.md`; **additive reframe `docs/additive_background_increment_plan_2026-06-04.md`**; post-mortem `docs/post_mortem_2026-05-27.md`.

- **🆕 HEADLINE MODEL (additive Lenschow 2001, 2026-06-05):** `PM(x,y,t) = B(t) + [T(t)−B(t)]·P_local(x,y,t)`. **B(t)** = regional/transboundary background = rural-VanD floor (P10 of ±0.45° box) × GEOS-CF daily seasonal shape (diurnally flat; GHAP seasonal r=0.86). **P_local** = unit-mean local pattern = normalised S_emit·M (headline) [·A_transport = scenario]. **Local fraction f=0.25** ⚠ **SUPERSEDED — see the top blocks: the coherence cap places f at 0.48 and refutes 0.244; the shipped model is unchanged but the claim is not** (B_annual=(1−f)·VanD_basin, 2019 B≈14.8) set from SOURCE APPORTIONMENT (World Bank 2022 >50% transboundary in S.Asia + Seneviratne 2017 Kandy PMF regional-dominated + rural-satellite ~15% lower bound; bracket [15%,<50%]) — NOT GHAP-calibrated → GHAP decile 1.18× independently CORROBORATES additive 1.12×. **Basin mean preserved exactly** (=VanD per year, G1 Δ=0.000). UQ: PI width = P_local·(T95−T05) [background shifts centre not width] + background bracket [ridge 10.5…rural P25]. Scripts `decomp/build_additive_background.py` (Phase 0 B), `decomp/build_additive_field.py` (Phase 1+2), output `data/processed/decomp/kandy_decomp_predictions_{year}_additive.parquet` + `additive_partition.csv`. **Why additive:** multiplicative T·S·M wrongly modulated the transboundary background by the local pattern; additive adds B uniformly, structures only the local quarter → honest intervention partition. G3 seasonal-contrast discriminator REFUTED (both forms grow contrast at the stable inter-monsoon peak) — additive adopted for physics+framing, not a field test. Exposure +6% (flatter), burden 2023 ≈423/yr [231–616], 291 avoidable.
- **(superseded) multiplicative v1:** `PM = T·S_emit·M` (·A_transport scenario) + Mondrian conformal PI — now the ablation/scenario; the smooth T·S·M is retired as the headline.
- **📊 CANONICAL FIGURE SUITE (LOCKED 2026-06-06, restyled YlOrRd 2026-06-06): `src/stage1_satml/decomp/paper_figures.py`** (+ `paperfig.py` helpers, `pubfig.py` style) → **`results/figures/paper_figures/` (F1–F13, png 400dpi + pdf).** THE publication figure set; supersedes `figure_suite.py`/`final_model_suite/` and the older `monograph/` figures (history). 13-figure narrative (setting→mechanism→spatiotemporal→validation/burden→episode). Locked conventions (user 2026-06-06): **YlOrRd** PM heatmaps on ONE shared **PowerNorm(γ=1.3) 10–40** scale (`pf.pm_norm()`); **inferno** reserved for pure emission-source maps; signed=RdBu, UQ=magma; **WindNinja quiver** + green **emission-intensity contours** (S_traffic); accumulation diagnostics (ventilation index VI=BLH·|u|, flux convergence −∇·(Cu)); SciencePlots+STIX; **A4-sized**. **F6 = per-season ERA5→WindNinja winds; F13 = average-vs-stagnation-episode side-by-side.** Per-season + episode fields precomputed by **`scripts/build_seasonal_episodic_fields.py`** → `data/processed/decomp/seasonal_episodic_fields.npz` (rebuild after any 4factor change). **CANONICAL STYLING: all heatmaps SQUARE** (`pf.square_heatmaps(fig)`) + **opaque legends** (framealpha 0.92) + **heatmaps carry NO location pins at all** — markers/labels live ONLY on F1. **F1 = full OSM reference map** (`_osm_layers()` via osmnx, cached `data/processed/decomp/osm_kandy/*.geojson`; hillshade + graticule + scale bar + N-arrow + Sri Lanka locator inset) and IS the one figure that keeps the **sensor pins** (NIFS/KOALA, FECT-Hantana). Deps: osmnx/geopandas/contextily/cartopy. **Single-timestamp nowcast: `scripts/nowcast_figure.py --ts "YYYY-MM-DD HH:MM" [--label "episode"]`** → `paper_figures/NOWCAST_*.png`; panel (a) scale **AUTO-SWITCHES by pollution level**: decider = field 98th-pct; if ≥ **35 µg/m³ (WHO IT-1)** → **turbo + FIXED universal 8–90**; else → **YlOrRd + per-hour adaptive**. Panel **(b) upper bound = ALWAYS YlOrRd**. **(c) overlays FECT Akurana ground obs**. `EPISODE_PM=35` tunable. **Validated against 3 documented Kandy-relevant transboundary episodes:** Nov 3–5 2019 → model basin 45/core 63; Dec 7–8 2022 → 56/67; Feb 28–Mar 3 2023 → 34/37. **F7/F8 read `_additive` (headline)**. Plan `kandy_pm25/docs/paper_figures_plan_2026-06-05.md`. Run `paper_figures.py --figs all`. Regen requires the data chain current (gotcha #53).
  - **T(t)** = Stage A v3 **lag-free** GBM (LGBM-only) on exogenous drivers, conformal-wrapped, re-anchored per-year to bias-corrected Van Donkelaar, **+ diurnal+seasonal amplitude sharpening to the observed FECT swing (`scripts/sharpen_T_diurnal.py`)** — the lag-free GBM damps the swing to ~85%/72% (regression to mean); sharpening maps T(t)'s climatology onto the observed FECT bimodal diurnal (1.91×, 07/18 rush, deep-night low) + seasonal (Mar 1.68/Aug 0.55), annual mean preserved. Lag-free chosen because 2024 FECT coverage is 30.5% Akurana-only. Script `models/predict_T_anchor_v3.py` → **sharpen_T_diurnal.py**; output `data/processed/stage1_v3/T_anchor/T_kandy_hourly_{year}.parquet`.
  - **S_emit(x,y)** = observed VanD V6.GL02.04 PM2.5 surface (2019–2023 mean), normalised to mean 1. Correct signs (city 1.09>1, highland<1) but weak ±10% contrast. Script `decomp/build_s_emit.py`.
  - **M(x,y,t)** = `1 + κ·w(BLH_t)·c(x,y)`, confinement c=z-score(−delta_z), κ=0.15, H_ridge=300m (physical priors, uncalibrated). Script `decomp/build_m_confinement.py`.
- **Level anchor (AREA-ANCHORED 2026-06-04 — area-vs-floor correction):** `L(year) = VanD_basin(year)` directly, **β≡1** (NO scale-up). KOALA 24.5 is a valley-**FLOOR** diagnostic (NIFS verified 7.2839/80.6322, ~27m above floor, near-core), NOT the basin-mean target. The old `β=1.2472` forced the AREA mean to a FLOOR point → double-counted floor enhancement, over-predicted the ventilated ridge ~2×. Two independent area products agree (VanD ~19.7, GHAP ~17.0, 2019) below KOALA-floor 24.5; FECT-Hantana ridge 10.5 → vertical gradient floor>area>ridge. Confinement M reproduces KOALA at NIFS pixel (~23.5 vs 24.5, **unforced**). Headline basin fell **26→~21**. Module `features/vandonkelaar.py` (`bias_factor`→1.0); regen chain `predict_T_anchor_v3`→`build_decomp_map`→`build_overlay_predictions`→`build_spatial_uq`. Fig `decomp/figure_area_anchor.py`.
- **2023 results (headline year; 2024=proxy):** annual AREA mean **~21** (2019 19.7 / 2020 19.0 / 2021 17.0 COVID / 2022 18.7 / 2023 20.9), seasonal MAM>DJF>SON≈JJA, diurnal **6–7 LT peak / 13–14 LT trough** (Senarathna diurnal r=0.756, monthly r=0.836 PRESERVED), **night contrast 1.24× > day 1.11×**, 4factor core/edge 1.20× annual / 1.41× night, annual max ~30 / nocturnal ~32, neg q50 <0.5%, mean PI ~29. Assembly `decomp/build_decomp_map.py` (2.25M rows). Figures `decomp/figure_final_deliverable.py`, `heatmaps.py`.
- **Exposure metrics (health framing, 2026-06-04):** area mean UNDER-states exposure — population clusters in the higher core. NTL-weighted (2023): area **21.0** → residential **21.5** → **dynamic/population-weighted 22.5** (health CSV 22.4, +7% uplift) → populated-core **21.9**. Health statements use the dynamic pop-weighted figure, NOT the area mean. Script `decomp/exposure_weighting.py` → `data/processed/decomp/exposure_weighting.csv`.
- **Parallel floor-anchored constants (checked 2026-06-04):** (a) `KANDY_GEOS_CF_RATIO=0.536` (=24.5/45.7) is a FLOOR ratio but **firewalled** in the decomp — T(t) level is set by the additive VanD re-anchor, b_FECT absorbs ρ. No fix needed. (b) `CAMS_BIAS_FACTOR_FLAT=0.5984` (v1 22-yr daily XGBoost chronology) IS floor-anchored to KOALA → that superseded 2003–2025 series over-states the AREA level ~25%; flag if ever cited as area PM. (c) PVAF used "Kandy AREA mean 24.5" for source selection — also the floor value; superseded/exploratory.
- **Senarathna 2019 (decomp@NIFS):** diurnal r=0.75, monthly r=**0.83**, March peak, evening 21 LT. Script `decomp/decomp_vs_senarathna.py`.
- **Validation (`decomp/validate_decomp.py`):** **U5 independent PASS** — vs VIIRS NTL r=+0.68, vs delta_z −0.70; **U6 signs 2/2 PASS**; FECT pointwise documents over-prediction at elevated Hantana (obs 10.5 vs pred 19.9) — real, not a temporal error.
- **🆕 U7 independent-product cross-check vs GHAP (2026-06-01):** GHAP/GlobalHighPM2.5 (Wei et al., 1 km, methodologically independent of VanD). **SEASONAL r=+0.909** [+0.75,+0.98] → STRONG independent corroboration; **LEVEL:** decomp(area) 17–20 ≈ GHAP(area) 17–19 **within 6%**, both BELOW KOALA-floor 24.5; **INTER-ANNUAL r≈0** → trend NOT corroborated (low-confidence); **fine-spatial r=+0.13**. **Lever 2 (M κ-calibration) = honest NEGATIVE** — δz-confinement ⟂ NTL-source collinear on valley floor → κ empirically unidentifiable → κ=0.15 kept as PRIOR. **Lever 3 spatial UQ** (`*_spuq.parquet`): fine ±13% gradient is only ~1.1σ at the tails. **Lever 4** robustness: spatial pattern corr ≥0.956 across κ/H_ridge envelope.
- **DECISION (FINAL 2026-06-02, `docs/validation_arc_and_model_framing_2026-06-02.md`):** **ship the smooth `PM = T·S·M` field as the HEADLINE** (magnitude GHAP/KOALA-validated, diurnal Senarathna/GHAP-validated); present the **transport overlay `A_transport` as a physically-motivated SCENARIO, not a validated layer.** **Why:** across 300+ monitored valleys NO public network densely+deeply samples the floor-to-ridge gradient (monitors are floor-sited globally); the pooled confinement test on genuine-δz valleys gives floor/elevated ≈0.97 absolute with only a **weak ~10% morning-peaked diurnal modulation** — overlay DIRECTION weakly right, MAGNITUDE (1.25–1.41×) unsupported/overstated. City-centre/NBRO elevation-transect sensor is the ONLY validation path.
- **Bowatte deliverables:** `decomp/compare_versions.py` → `results/figures/kandy_decomp/version_comparison.png`; 1-pager `docs/bowatte_meeting_brief.md`.
- **🌬️ A_transport WIND from WindNinja diagnostic model (2026-06-05, [[project-windninja-transport]]):** the hand-rolled channelling+katabatic-drainage in `terrain_transport.py` is REPLACED by **WindNinja 3.12.2** mass-consistent diagnostic winds. Install `tools/wn/` (**gitignored**). Wind-class library (16 dir × 2 speed × day/night, 64×64) `scripts/build_windninja_library.py` → `data/processed/pinn_inputs/windninja_library.npz`; `terrain_transport.windninja_wind()` blends it, `solve_terrain` uses it (`USE_WINDNINJA=True`, analytical fallback kept). DEM `scripts/export_kandy_dem_utm.py`. Annual contrast **1.20–1.25×** (basin preserved). **KEY: drainage shifts the nocturnal MAX down-valley (N, Katugastota sink ~28 vs core ~26) — testable.** ERA6 unusable till 2027.
- **🎯 Terrain transport overlay — CROSS-CITY CALIBRATED 2026-06-01** ([`reports/terrain_solver_calibration.md`](reports/terrain_solver_calibration.md)). The Tier-B terrain-aware advection-dispersion solver (`decomp/terrain_transport.py`) was calibrated against the dense station networks of **10 monitored valleys** — physics fixed, ML calibrates ~3 params only. **Cross-city spatial Pearson +0.49 ± 0.17**; calibration barely moved the hand-set priors (K0 120→124.88, DRAIN 8.0→8.14, SLOPE_K 0.060→0.062). **KEY: terrain-learnability ≠ regime-match.** **Overlay SHIPPED (2026-06-02) as the four-factor `A_transport`, smooth as ablation**; annual 1.27×/night 1.41× core/edge, basin-preserving. **A_transport carries a DIURNAL EMISSION-TIMING factor `e(t)`** (`src/stage1_satml/decomp/emission_profile.py`): amplitude `a(t)=clip(e(t)·18/(wind·BLH),0,0.5)`. e(t) = bimodal EDGAR road-transport profile (Crippa 2020), **Kandy `vehic`=0.85** ⚠ **the "~90% vehicular" provenance is REFUTED as a mass share — see F.66**; the measured PMF split at Katugastota is traffic 7.6%, biomass burning 14.1% (vs Colombo ~55–60%) + 10% domestic; morning(~07)/evening(~18) rush peaks ~2× overnight. **Fixes the met-only defect**. **Final 4-factor product BUILT** via `scripts/build_overlay_predictions.py` → `data/processed/decomp/kandy_decomp_predictions_{2019..2023}_4factor.parquet`. Demo `scripts/emission_timing_demo.py`; design+lit `docs/enhancement_diurnal_emissions_2026-06-02.md`.
- **🚦 Congestion-weighted traffic EMISSION source (2026-06-04):** A_transport's source S(x,y) upgraded to a **bottom-up centrality-AADT × COPERT-EF** surface (`decomp/build_traffic_emission.py` → `S_traffic_kandy.npz`, core ~3.3× mean, log-tempered). Method = network-centrality traffic-volume estimate **betweenness (pass-by, r≈0.77 vs flow) + closeness (O-D trip-ends)** × class/speed emission factor lifted under congestion (Lowry 2014, Kazerani&Winter 2009, Borge 2017, Gately 2013, Plejdrup ESSD 2024 — in `references.bib`). Wired into `terrain_transport.py _grid_fields`. **MEASURED calibration NOT possible: TomTom verified to have ZERO traffic-flow coverage for Sri Lanka** → magnitude stays a literature-bounded prior in UQ. Figs `figX3_traffic_emission.png`.
- **Dynamic-transport learning — TESTED, NULL (2026-06-01).** 3 independent diagnostics all refute a learnable dynamic-confinement signal. **Why (not missing data):** monitored stations are all urban-valley-FLOOR (δz 8–141m) → don't sample the vertical gradient. Chandigarh (only city w/ 700m station relief) shows the expected signs → physics right, data must SAMPLE the gradient. **Verdict: dynamic transport IMPOSED from the calibrated physics solver, NOT learned.** Scripts `scripts/diagnostic_transport_dynamics{,2}.py`, `diagnostic_elevation_contrast.py`. **Full arc synthesis: [`docs/findings_synthesis_post_convcnp_2026-06-01.md`](docs/findings_synthesis_post_convcnp_2026-06-01.md)** + [`docs/valley_pm25_variation_research.md`](docs/valley_pm25_variation_research.md). KEY META: physics-transfer > ML-transfer at this scale; binding constraint = data CONTENT, not volume/model.

### ⚠ Research audit (2026-05-29) — `docs/audit_2026-05-29.md`
Full Tier 1–3 sweep. **5 errors found, none corrupted the model** (bbox-shared features + b_FECT offset-absorption firewalled it): E1 FECT elevations (1538/1698→460/738), E2 Hantana coord (→7.265/80.625), E3 Akurana out-of-bbox, E4 "highland" narrative false, E5 Senarathna monthly coeffs May–Nov mis-transcribed (fixed → monthly r 0.73→0.83). **Verified sound:** T(t) core, b_FECT, GEOS ratio, β, KOALA 24.5, hourly+weekly coeffs, all 10 source-city coords. See gotcha #49.

### Stage A v1 — Daily XGBoost temporal anchor — SUPERSEDED by v3 (retained as 22-yr chronology)
- XGBoost, 44 features, 8,279 days (2003–2025). **LOMO R²=0.631**, RMSE=4.82, 90% PI=89.4%.
- Methodological weakness: KOALA used both to calibrate labels (×0.598) AND to validate (r=0.515) → circular.
- Models on disk: `results/models/xgboost_kandy_pm25.ubj`, `xgboost_q05/q50/q95.ubj`. Pixel model ORPHANED.

### Stage A v3 — Hourly RECAP residual learning ✅ COMPLETE (locked 2026-05-20)
- **Architecture**: hourly residual target `pm25 − c_prior_anchored` where `c_prior_anchored = ρ·GEOS-CF + b_FECT[sensor]`. Per-sensor offset in `data/processed/stage1_v3/v3_station_constants.json` (Akurana b_FECT=−9.105, Hantana b_FECT=−13.749). Residual centred on −0.028 µg m⁻³ (H8 PASS by construction).
- **Dataset**: 19,686 hourly rows × 43 cols (`data/processed/stage1_v3/dataset_v3_hourly.parquet`). 33 trainable features. NaN map: GEOS-CF 1.1%, ERA5 0.8%, CAMS 0.8%, MAIAC 84.5%, t925 100% (deferred).
- **v3.0 production**: linear blend of LightGBM+CatBoost+XGBoost-quantile (0.46/0.48/0.06) + **CV+ Mondrian conformal**. Outputs `data/processed/stage1_v3/training/predictions_blend_v3.parquet`.
- **Pooled hourly LOMO** (60 folds, 53 non-empty, 19,388 obs): **RMSE 7.76, R² 0.583, cov90 0.865, PI width 22.3, CRPS 2.9**.
- **v3-extended (39 feat)**: RMSE 7.78, R² 0.581, cov90 0.867. Tier-1 features did NOT lift R². **Path A negative result.**
- **Pre-reg gates**: H1 PASS (60% RMSE reduction); H2 cov90 **PASS (0.867)**; H3 R²≥0.60 **CLOSED AS HONEST NEAR-MISS at 0.581**; H4 (Embassy daily) PASS at 0.861; H7 **PASS**; H8 residual mean −0.028 **PASS**.
- **Senarathna 2024 reproduction**: diurnal r=+0.865, morning peak 07 LT match, evening 18–19 LT (1h drift); weekly r=+0.783; monthly r=+0.41. Figures `results/figures/stage1_v3/`.
- **TFT smoke (Val 2024)**: R² 0.447 — does not beat GBM blend. **Removed from production stack** (amendment #9).
- **v3.1 lag-dropout**: R² 0.571 — **rejected as production**; retained as ablation.
- **Pre-reg amendments**: #7 v3 lock; #8 H7 metric + CV+ Mondrian; **#9 (`docs/osf_prereg_stage1_v3_amendment_9.md`) locks v3.0 as production.**
- **Key scripts**: `src/stage1_satml/features/build_dataset_v3_hourly.py`; `models/train_{lgbm,catboost,xgb}_v3.py`; `models/blend_v3.py`; `scripts/process_kandy_era5_t925_to_parquet.py`; `scripts/ingest_v3_gee_drive.py`; `scripts/gee_export_v3_kandy.py`.
- **H3 closure path**: more ground sensor data. Architectural / feature-engineering levers exhausted within current data envelope.

### Stage A v2.1 — Daily RECAP (SUPERSEDED by v3; retained as baseline)
- **Reframe:** CAMS + GEOS-CF as FEATURES (residual learning); FECT-calibrated PurpleAir as LABELS. Pre-reg `docs/osf_prereg_stage1_v2.md`, 6 amendments locked 2026-05-17.
- **Data:** 1,550 sensor-day rows (Akurana **~460m**, ~6km N of Kandy/out-of-bbox + Hantana TR4 **~738m**, 7.265N/80.625E), 2018-10 → 2026-05. Both **valley/suburban, NOT highland** (see `docs/audit_2026-05-29.md` E1–E3). 28 mechanistic features.
- **v2.1 LOMO:** pooled **RMSE 5.73, R² +0.689, cov90 0.88** (62 non-empty folds).
- **Baselines:** persistence 6.39, doy_clim 10.13, cams_scaled 12.67, geos_scaled 14.24.
- **🎯 Pre-reg H1 SATISFIED: 60% RMSE reduction vs GEOS-CF×0.536** (threshold ≥15%).
- **Surprising finding:** AOD + GEOS-CF added only +1.4% over v2.0. Meteorology + CAMS_raw carry most signal.
- **§6.4 + §6.5 ablations DONE:** ΔRMSE ranking: **G temporal +13.1%** > E reanalysis +8.0% > C wet scavenging +5.6% > E cams-only +3.1% > E geos-only +1.4% > STATION +0.7%. Vector valley TBI (B) and AOD (D) add essentially zero.
- **NGBoost Student-t variant:** `train_ngboost_v2.py`. Switched to `TFixedDf(df=5)` due to gradient instability (documented pre-reg deviation). XGBoost-quantile is primary (CRPS 2.65 < NGBoost 3.86).
- **Embassy Colombo OOD (§6.6): H4 SATISFIED.** `results/models/xgboost_v2_full_kandy.ubj`. 1,661 Embassy daily rows: **cov90 0.861, RMSE 9.51, bias −4.92, R² +0.452, CRPS 3.76.** Honest finding: **point estimates degrade OOD but calibrated UQ transfers.**
- **§6.1 anchor sensitivity:** R² invariant +0.689 across KOALA ∈ {20,22,24.5225,27,29}. **§6.2 OOY holdout:** asymmetric — beats persistence forward, loses backward. **§6.3 cross-product triangulation:** v2 ~14 vs VanD ~19 vs GEOS/CAMS ~24. Paper hook: "calibrated to station ≠ calibrated to area".
- **Models on disk:** `data/processed/stage1_v2/dataset_v2_multistation_daily.parquet`, `training/{predictions_lomo_v2.parquet, summary_v2.csv}`.

### Reanalysis prior (preprocessing inside Stage B, not a standalone stage)
- GEOS-CF PM25_RH35_GCC × per-city row-mean scaling. **Kandy ratio = 0.536** (= 24.5 / 45.7). Locked in `config.py` as `KANDY_GEOS_CF_RATIO`.
- v11 row-mean per-city ratios: Mel 0.8070, ChiMai 0.5933, KTM 0.5601, Kandy 0.536. Bogotá 0.807, MexCity 0.217 retained for reproducibility only.
- Used inside Stage B as `c_prior_scaled = c_prior × city_ratio` to form the residual target `pm25 − c_prior_scaled`.

### Stage B — Cross-city ConvCNP residual learner ✅ CAPABILITY LOCKED (v14 + conformal); Kandy production maps HELD (2026-05-23)
- **Target: `pm25 − c_prior_scaled`.** deepsensor 0.4.2 ConvNP, UNet (32,64,128), 625,989 params, heteroscedastic Gaussian likelihood.
- **N=3 source cities (LOOCV):** Mel, ChiMai, KTM. Bogotá + MexCity DROPPED. Title is **"supervised cross-city ConvCNP"**.
- **Training data:** 100 stations × 1.24 M hourly rows (OpenAQ S3 + AirNow Embassy, per-LCS calibrated).
- **Cascade (locked 2026-05-21):** v12 OSM road density → v13 + VIIRS NTL + wider terrain → **v14 UQ restoration (Student-t / σ-floor)** → v15 + EDGAR sector.
- **v13 COMPLETE**: KTM r **0.590**, ChiMai **0.820**, Mel **0.280**. **Mean r 0.563** (+0.120 vs v12). **KTM bias +6.48**. **G1/G6 PASS for first time**. **G4 FAIL across all cities** (cov90 collapsed). Kernel `damindaalahakoon/kandy-convcnp-loocv-v13`.
- **v14 COMPLETE (Student-t df=5)**: KTM r **0.682**, ChiMai 0.795, Mel **0.321**, **mean r 0.599** (best ever). **KTM bias +0.14** (G6 PASS by an order of magnitude). Cov90 KTM 0.754, ChiMai 0.508, Mel 0.518 — **G4 still FAILS.**
- **v14 interpretation (physics correction):** Student-t encourages *tighter* σ, not wider. Best-ever median estimator, worse interval estimator — opposite of what the v14 plan predicted.
- **v14-conformal COMPLETE**: q̂ Mel 6.33±2.82, ChiMai 5.95±1.28, KTM **3.13±0.11**. **Calibrated cov90: Mel 93.0%, ChiMai 89.5%, KTM 91.5% — G4 fully satisfied.** Script `scripts/conformal_calibrate_v14.py`.
- **Final UQ pipeline (locked)**: Student-t(df=5) NLL during training + split-conformal scaling at inference. Paper framing: "robust point estimation + calibrated intervals via post-hoc conformal" (Vovk 2005, Romano 2019).
- **Kandy zero-shot inference RUN (2026-05-23, full year 2024, 2.25M predictions)** — pipeline + outputs work; consistency anchors pass; **maps technically defensible but spatially smoothed-out**. Checkpoint `convcnp_v13_holdout_medellin_seed3.pt`. σ scaled by KTM analogue q̂ = 3.13 or per-hour Mondrian q̂ ∈ [2.13, 3.54]. **Result HELD as preliminary, NOT for publication.**
- **Three consistency anchors PASS** (NOT called validation): annual mean 22.1 vs KOALA 24.5 ✅; seasonal DJF 27.7 / MAM 26.3 / JJA 11.5 / SON 23.0 ✅; diurnal nocturnal plateau ~37, midday trough ~7 ✅
- **Known limitations:** diurnal morning peak phase off by ~4 hr; negative-value floor (−12 in tail extremes, clipped at 0 for plotting only); PI widths ~20 annual mean up to 60 nocturnal. **Stage B transfer claim remains "exploratory cross-city" not "validated".**
- **Sim2Real Phase 2 (N=2 FECT) NEGATIVE RESULT**: fine-tuned on Kandy 2018-2023; held-out eval at the *exact* FECT (lat,lon): r 0.43 → **0.9999**, RMSE 15.39 → **0.12**. But on the 1 km grid annual mean inflates 22.1 → 37.0. The model memorised the *exact* sensor (lat,lon) as identity keys, not Kandy basin physics. **Documented as the §6 ablation motivating the ≥5-sensor data-acquisition agenda.**
- **Mondrian (per-hour) conformal COMPLETE**: test cov90 ChiMai 91.4%, KTM 87.0%, Mel 89.6%. Kandy mean PI width 20.5 → 18.9 (8% tighter). Script `scripts/conformal_per_grid_v15.py`.
- **🎯 PVAF v2 "Expansion-E" — source-set RE-SELECTED 2026-06-01.** Fixes the documented v15 failure (magnitude-blindness selected 3–4×-dirtier industrial basins). Added **magnitude (E1, w0.24)** + **pattern (E2, w0.12)**; Kandy ref = **bias-corrected AREA mean 24.5** (NOT FECT 13.6). **Selected source set (N=9):** Xichang, Bazhou, **Kathmandu, Medellín, Chiang Mai**, Puebla, León, Sandton, Hyderabad. **Valley-grade core: Xichang, Bazhou, Kathmandu, Medellín, Chiang Mai.** Caveat: Sandton anti-phased (pattern 0.45) — recommend drop. Output `data/processed/pvaf/expansion_e_ranked.csv`.
- **PVAF v15 source-set LOCKED 2026-05-24 (N=10) — SUPERSEDED.** Magnitude-blind.
- **Room for improvement (deferred):** more source cities via PVAF; Sim2Real with ≥5 spatially-diverse sensors; per-pixel σ inflation from terrain uncertainty.
- **Kaggle dataset**: `damindaalahakoon/kaggle-dataset-kandy-stage3`.
- **Source tree:** `src/stage3_pinn/models/convcnp_terrain.py`, `data/convcnp_loader.py`, `training/train_convcnp.py`, `training/loocv_convcnp.py`.
- **Data invariants:** `scripts/validate_perstation_parquets.py --version v13 --strict` (13 checks/city). v13 PASS 39/39.
- **Data dictionary:** `docs/stage_c_data_dictionary.md` (v11 — refresh pending).

### Supporting experiment 1 — Cross-continental PINN transfer (Mel → ChiMai) ✅ COMPLETE
- TD-PDE: Medellín (R²=0.932, ep1400) → ChiangMai (R²=0.765, bias=−0.59, ep2200).
- Canonical ckpts: `results/models/stage2_medellin_pinn/td_pinn_v1/checkpoints/epoch_01400.pt`, `stage2_chiangmai_pinn/td_pinn_v1/checkpoints/epoch_02200.pt`.
- FourierPINNV3, **76,261 params**. v7 curriculum: Phase 1 λ_pde=0; Phase 2 ramp 0→0.15; Phase 3 0.15.
- Status: standalone methodology study. NOT a feeder for Stage B.

### Supporting experiment 2 — SharedTerrainAnsatz identifiability diagnostic
- All 6 rigid-Whiteman parameters hit bound constraints across Mel + ChiMai + KTM. LOOCV: ChiMai r=0.323, KTM r=0.863. Status: documented diagnostic motivating the move to ConvCNP. No further iteration planned.

### Tooling
- **Kaggle kernel log** (MANDATORY): `docs/kaggle_kernel_log.md` — read at start of Kaggle sessions, update after every push/download.
- **GPU protocol**: After every push → Kaggle UI → Edit → Accelerator → **GPU T4 x2** → Save.
- **Kaggle tokens**: KGAT_ tokens in `d:/ProjectCD/API.txt`. Install: `echo -n "KGAT_..." > ~/.kaggle/access_token`. Push: `PYTHONUTF8=1 PYTHONIOENCODING=utf-8 .venv/Scripts/kaggle.exe kernels push -p <dir>/`
- **409 Conflict**: metadata `id` doesn't match Kaggle slug.
- W&B: `WANDB_PROJECT="kandy-pinn"`. Kaggle secret: `"wandb"`.
- Plot style: `src/utils/plot_style.py`. `apply_style("ieee")`. STIX fonts.

## Key Paths

All paths are relative to `d:\ProjectCD\kandy_pm25\` unless stated otherwise.

**Deliverables (2026-06-07; webapp 2026-07-05)**
- **Public webapp (Kandy): `d:\ProjectCD\kandy_webapp\`** (own repo `daminda1108/kandy-pm25-explorer`, gitignored by parent) → https://daminda1108.github.io/kandy-pm25-explorer/. Static site (index.html/method.html/css + js/{app,store,field,overlay,timeline,wind,panels,download,util,**mapview**,**cities**,**showcase**}.js + data/ payload). Exporter `kandy_pm25/scripts/webapp_export.py --city` (re-run + QA gate after any additive_v2 change). **First-party JS/CSS URLs are versioned `?v=<ts>` — bump on each deploy** (browser module cache). Plans + audit: `kandy_pm25/docs/{deployment_plan_public_webapp_2026-07,webapp_v2_plan_2026-07-09,webapp_engine_audit_2026-07-05}.md`.
- **Medellín deliverable app: `d:\ProjectCD\medellin_webapp\`** (own repo `daminda1108/medellin-pm25`, gitignored by parent) → https://daminda1108.github.io/medellin-pm25/. Standalone public-first app sharing the Kandy engine (`js/cities.js` + `window.CITY_ID`); payload at `data/` (built by `webapp_export.py --city medellin`); live forecast in `live/` + `.github/workflows/medellin-live.yml` (WAQI_TOKEN repo secret set). Plans `kandy_pm25/docs/medellin_{deliverable_plan_2026-07-14,first_improvement_plan_2026-07-13,showcase_plan_2026-07-11}.md`. Improvement scripts `kandy_pm25/scripts/medellin_{vandfree_level_test,a1_spatial_audit,b1_wind_diagnosis,b2_wind_recalibration,weather_validation,data_value_curve,showcase_s0,showcase_figures}.py` + `build_medellin_v16.py` + `score_convcnp_assim.py`; artifacts `results/figures/medellin_showcase/`.
- Standalone release model: `d:\ProjectCD\kandy_pm25_release\` (own repo `daminda1108/kandy_pm25_model`, package `kandymodel/`, gitignored by parent). Entry points: `kandymodel/viz/paper_figures.py`, `scripts/nowcast.py`, `scripts/regenerate_all.py`.
- Supervisor reports: `kandy_pm25/docs/reports/{kandy_model_briefing,kandy_model_technical_report}.{md,pdf}` + `_report_style.tex` (gitignored).
- **Flagship preprint (2026-06-30, 22 pp):** `kandy_pm25/docs/reports/preprint_kandy.{md,pdf}` + style `_preprint_style.tex` + figures staged in `docs/reports/fig_preprint/` + builder `docs/reports/build_report.js` (`--src/--style`). Plans `docs/paper/{preprint_plan,evidence_hardening_plan}_2026-06-30.md`. China-arc doc `docs/reports/china_validation_arc.pdf`.
- **Evidence-hardening artifacts (all `scripts/`, gitignored):** `sensitivity_analysis.py` (→S1), `ablation_scorecard.py` (→S2; ABLATE hook in `xichang_prod.build_field`), `independent_visibility.py` (→S3, VCBI METAR), `spatial_skill_law.py` (→S4, tested-NULL), `w2_transboundary_figure.py`, `regenerate_city.py` + `docs/REPRODUCE.md`. N=9 scorecard `results/figures/multicity/validation_scorecard.{png,csv}`. New cities in `city_config.py`: baoji/taian/yichang/**medellin**.
- **Medellín analogue (2026-07-02, N=9):** `city_config.py` entry + `data/processed/pinn_inputs/medellin_terrain_core.npz` + `data/processed/decomp/S_traffic_medellin.npz` + `data/processed/decomp_medellin/`; ground `data/processed/stage2/medellin_perstation_v13.parquet` (24 stn), DEM `data/external/medellin/dem/medellin_dem.tif`. Run via `NO_WINDNINJA=1 xichang_prod.py --city medellin`. Held-out: 0.99/0.88/+6%/**ρ 0.78**.
- **Audit arc + N=10 (2026-07-25/26, `scripts/`, whitelisted in `.gitignore`):** `score_additive_v3.py` · `alphaearth_spatial_test.py` · `panel_donor_solartime.py` · `add_cprior_to_perstation.py` · `build_additive_field_v3.py` (`--city`, `eps_mode: fitted|relative`). Bogotá assets: `data/processed/{decomp_bogota/, pinn_inputs/bogota_terrain_core.npz, decomp/S_traffic_bogota.npz}`. Docs: `docs/{production_audit_2026-07-25, data_and_ml_frontier_2026-07-25, sensorless_product_scope_2026-07-25}.md` + `docs/paper/a4_anchor_provenance_audit_2026-07-25.md`.
- **Rain arbitration (2026-07-21, `scripts/`, gitignored):** `imerg_rain_arbitration.py` · `gee_export_imerg_gapfill.py` (Drive folders `MedellinIMERG`/`KandyIMERG`) · `download_gee_drive_outputs.py` (`_find_folder_ids` multi-folder scan). Exporter: `_imerg_hourly_rain()` + `_prefer_imerg_rain()` + per-city `imerg=` and `network_obs=` keys. IMERG archives: `data/external/tier_c/gpm_imerg/gpm_imerg_{2018..2026}.csv` (Kandy), `data/external/medellin/tier_c/med_gpm_imerg_{2018..2026}.csv`.
- **Kandy Phase-5 propagation (2026-07-20/21, `scripts/`, gitignored):** `kandy_driver_tier_build.py` (extension T+B, FULL vs ERA5_ONLY, `sharpen_to_locked`, `_locked_b_over_t`) → `kandy_extension_fields.py` (→ `..._{2024,2025,2026}_additive_v2_drv.parquet`) → `b2_kandy_wind_prior.py` (θ=344.5° drainage axis). Exporter: `_apply_wind_calib()`. Frontend: `kandy_webapp/js/cities.js` `windCaveat` + `index.html` `#weather-note`. Bookend: `validation_scorecard.csv` + `validation_scorecard_prev_20260716.csv`.
- **Forecast tier + background arc (2026-07-27 → 08-03, `scripts/`, ALL WHITELISTED):** `kandy_forecast_ood_widening.py` (k=1.35) · `kandy_forecast_pack_update.py` · `kandy_era5land_refresh.py` · `kandy_background_nbro_check.py` (B(t)'s first external check) · `kandy_f_reconciliation.py` (the coherence floor) · `kandy_background_{cap,relevel,v3,v4,v5}.py` (five rejected rebuilds; `build_additive_field_v2.py` carries `RELEVEL=False`) · `kandy_anomaly_target_test.py`. Webapp: `kandy_webapp/live/kandy_live.py` + `live/model/pack.json`. Ledger: **F.12–F.19**.
- **Forecast arc (2026-07-11, `scripts/`, gitignored):** `forecast_native_t_retrain.py` (F-K1) · `gee_export_geoscf_forecast.py` (F-M0, Drive folder `GEOSCF_FCST`) · `forecast_backtest_m2.py` (F-M2). Docs `docs/forecast_{from_decomposition_research,expansion_exploration}_2026-07-10.md`.
- **Pre-submission plan:** `docs/paper/pre_submission_fixes_and_spatial_roadmap_2026-07.md`. Prior expansion backlog `docs/paper/expansion_roadmap_2026-07.md`.
- **Kathmandu full-model validation:** products `data/processed/decomp_kathmandu/`; figures `results/figures/kathmandu_paper_figures_v2/`; assets `data/processed/pinn_inputs/kathmandu_{windninja_library.npz,dem_utm90m.tif,terrain_core.npz}` + `data/processed/decomp/S_traffic_kathmandu.npz`.
- Complete technical reference ("model bible"): `kandy_pm25/docs/model_reference/` (20 parts) + `kandy_pm25/docs/MODEL_REFERENCE_COMBINED.md`. Standing rule: keep in sync with every confirmed model addition (+ Appendix F ledger). See [[project-model-technical-reference]].
- **🆕 Modular grey-box package (2026-08-19):** `src/modular/` (budgets · observation · constraints · shrinkage · tiers · production · emission) + `scripts/tests/test_modular*.py` (**68 tests**). Spec `docs/MODEL_SPECIFICATION.md`; preregs `docs/prereg_modular_validation_v2_2026-08-18.md`; remediation `docs/spatial_diurnal_remediation_plan_2026-08-19.md`. Validation scripts: `modular_validation_all.py`, `build_lur_predictors.py`, `lur_fit.py`, `pull_hourly_blh.py`, `diff_decomp.py`.
- **🆕 Re-validation + evidence scripts (2026-08-22/23, `scripts/`, whitelisted):** `build_bud0_streams.py` (STATIC_GEO city aggregate + GHAP SATELLITE_LEVEL pull) · `revalidate_ladder.py` (the `Bud0a/b/c` decomposed ladder) · `learner_sensitivity_bud0c.py` · `colombo_zeroshot_test.py` + `colombo_zeroshot_bud0c.py` · `p4_identifiability.py` · `fit_s_exp.py` · `support_collapse_test.py` · `elangasinghe_spatial_test.py` · `ladder_support_test.py` · `tier2_robustness.py` · `bootstrap_v3_r2.py` · `palette_cvd_check.py` · `scripts/tests/test_budget_covers.py` (**74 tests**). Products in `data/processed/modular/`: `ladder_revalidated.csv`, `bud0_static_geo.csv`, `bud0_satellite_level.csv`, `p4_identifiability.csv`, `support_collapse.csv`, `s_exp_fit.csv`, `learner_sensitivity_bud0c.csv`, `colombo_zeroshot*.csv`, `lur_predictors_colombo.csv`, `elangasinghe_spatial_test.csv` (⚠ written to `data/processed/decomp/`, not `modular/`).
- **🆕 Paper-planning docs (2026-08-22/23, `docs/paper/`):** `rewrite_plan_2026-08-22.md` (**the active plan**) · `claims_audit_2026-08-22.md` (8 claims that moved + drafted replacement text) · `novelty_and_figures_2026-08-22.md` · `literature_positioning_2026-08-23.md`. Re-validation: `docs/revalidation_plan_2026-08-23.md`. Preregs: `docs/prereg_colombo_zeroshot_2026-08-22.md` (**OSF `nxqgb`**), `docs/prereg_revalidation_2026-08-23.md` (**OSF `g6hqb`**), `docs/prereg_subgrid_and_streams_2026-09-01.md` (**OSF `bkpyr`**, project `h8m9j` — C1/S3, S1, S2, R2, R3). **All 11 preregs are now git-tracked.**
- **🆕 Papers read 2026-08-22:** `D:\ProjectCD\references\papers\` — `aaqr-21-10-oa-0266.pdf` (Dhammapala 2022, F.64) · `CLEAN Soil Air Water - 2025 - Nirmani...pdf` (F.65/F.67) · `1-s2.0-S2772416625001937-main.pdf` (Attanayake RF-CNN, F.65) · `aaqr-16-03-2015aac-0123.pdf` (Seneviratne 2017 Kandy PMF, F.66).

**Infrastructure**
- Root: `d:\ProjectCD\kandy_pm25\`
- Config: `config.py` (all constants, paths, params)
- Venv: `.venv\Scripts\python.exe` — always use this, not system Python
- GEE project: `kandypinn`

**Source code (narrative → directory mapping)**
- Stage A (temporal anchor): `src/stage1_satml/` (features, models, visualization)
- Stage B (cross-city ConvCNP): `src/stage3_pinn/{data,models,training}/`
- Supporting cross-continental PINN: `src/stage2_transfer/`
- Supporting SharedTerrainAnsatz diagnostic: `src/stage3_pinn/models/shared_terrain_ansatz.py`
- Modular grey-box tiers: `src/modular/`
- Utils: `src/utils/plot_style.py`

Directory numbers (`stage1`, `stage2`, `stage3`) are workstream codes preserved to avoid breaking imports and Kaggle kernel paths. They do NOT line up 1-to-1 with narrative stage letters.

**Stage A data & models**
- Domain dataset: `data/processed/merged/dataset_daily.parquet` (8,401 rows × 49 features, 2003–2025)
- Pixel dataset: `data/processed/merged/dataset_pixel_daily.parquet` (413,950 × 45 features)
- PM2.5 predictions: `data/processed/merged/pm25_predictions_daily.parquet`
- XGBoost models: `results/models/xgboost_kandy_pm25.ubj`, `xgboost_pixel_pm25.ubj`, `xgboost_q05/q50/q95.ubj`
- Validation tables: `results/tables/koala_monthly_validation_2019.csv`, `model_benchmark_comparison.csv`, `monthly_cov_skill_table.csv`
- Publication figures: `results/figures/publication/`

**Decomposition production** — `PM = B + max(T−B,0)·P + min(T−B,0)` (+ ε-floor)
- Source: `src/stage1_satml/decomp/{build_s_emit,build_m_confinement,build_decomp_map,heatmaps,decomp_vs_senarathna,validate_decomp,compare_versions}.py`; `src/stage1_satml/features/vandonkelaar.py`; `src/stage1_satml/models/predict_T_anchor_v3.py`
- **Product advancement (2026-06-01):** `scripts/{gee_export_ghap_kandy,compare_decomp_ghap,calibrate_m_confinement,build_spatial_uq}.py`. Data: `data/processed/decomp/{ghap_kandy_monthly_2019_2022.parquet, u7_ghap_crosscheck.csv, m_confinement_calibration.json, kandy_decomp_predictions_{year}_spuq.parquet}`.
- T(t): `data/processed/stage1_v3/T_anchor/T_kandy_hourly_{year}.parquet`; lag-free boosters `results/models/stage1_v3/lgbm_lagfree_q{05,50,95}.txt`; inference grid `data/processed/stage1_v3/inference_grid_{year}_s12451.parquet`
- VanD levels: `data/processed/stage1_v3/vandonkelaar_kandy_annual.csv`; spatial `data/processed/decomp/S_emit_kandy.npz`; confinement `data/processed/decomp/M_confinement_kandy.npz`
- Map: `data/processed/decomp/kandy_decomp_predictions_{year}_additive_v3.parquet` + `decomp_summary_{year}.csv`
- Figures: `results/figures/kandy_decomp/{2019,2024}/` + `version_comparison.png` + `validation_fect_pointwise.csv`
- Docs: `docs/kandy_production_plan_2026-05-29.md`, `docs/audit_2026-05-29.md`, `docs/post_mortem_2026-05-27.md`, `docs/bowatte_meeting_brief.md`

**Supporting cross-continental PINN data & models**
- Parquets: `data/processed/stage2/`
- Medellín TD-PDE v1: `results/models/stage2_medellin_pinn/td_pinn_v1/checkpoints/epoch_01400.pt`
- ChiangMai TD-PDE v1: `results/models/stage2_chiangmai_pinn/td_pinn_v1/checkpoints/epoch_02200.pt`
- ChiangMai PINN v5 (QSS reference): `results/models/stage2_chiangmai_pinn/v5/checkpoints/epoch_04000.pt`

**Stage B Tier C+ data & kernels**
- Tier C merged: `data/processed/tier_c/kandy_tier_c_merged.parquet` (70,128 rows, 21 cols)
- PINN inputs: `data/processed/pinn_inputs/kandy_elev_grid_100m.npz`, `kandy_terrain_wind_100m.npz`, `kandy_road_kernel_100m.npz`, `kandy_stage1_pixel_preds.npz`, `kandy_terrain_tpi_svf_100m.npz`
- Kaggle kernels: `data/processed/stage2/kaggle_kernel_kandy_td_pinn_v*/`; logs `kaggle_logs/kandy_td_v*/`; dataset dir `kaggle_dataset_kandy_stage3/`

**Stage B multi-city per-station data (N=5 historical, N=3 active)**
- Medellín: `data/processed/stage2/medellin_stage2_perstation.parquet` (59,138 rows, 11 stations)
- ChiangMai: `chiangmai_stage3_perstation.parquet` (87,791 rows, 8 stations)
- Kathmandu: `kathmandu_stage3_perstation.parquet` (122,046 rows, 45 stations)
- Bogotá: `bogota_stage3_perstation.parquet` (145,586 rows, 19 stations)
- Mexico City: `mexico_city_stage3_perstation.parquet` (354,651 rows, 32 stations)
- Terrain NPZs: `data/processed/pinn_inputs/{medellin,chiangmai,kathmandu,kandy,bogota,mexico_city}_terrain_tpi_svf_100m.npz`
- **v13 per-station parquets (canonical)**: `data/processed/stage2/{kathmandu,chiangmai,medellin}_perstation_v13.parquet` + `v13_city_constants.json`
- Wide-footprint road kernels: `{city}_road_kernel_stations_100m.npz`; wide terrain `{city}_terrain_stations.npz`; VIIRS NTL `{city}_viirs_ntl_stations.npz`
- **Kandy zero-shot pipeline (2026-05-23)**: `scripts/kandy_zero_shot_inference.py` · `conformal_calibrate_v14.py` · `kandy_heatmaps.py`; predictions `data/processed/kandy_zero_shot/kandy_predictions_20240101_0000_n8784.parquet`; figures `results/figures/kandy_zero_shot/`
- Builders: `rebuild_perstation_extended.py --version v11` · `build_road_kernel_for_city.py --city` (needs User-Agent, gotcha #41) · `build_station_road_kernels.py` · `add_road_density_to_perstation.py --version v12` · `gee_export_source_cities.py` · `gee_export_source_city_terrain.py` · `merge_source_city_gee_met.py` · `download_gee_drive_outputs.py`

**PVAF v1 (Physics Valley Analogue Finder)**
- Pre-reg: `docs/osf_prereg_pvaf_v1.md` (OSF guid `ykdb9`, locked 2026-05-23)
- Plan: `docs/pvaf_v1_plan.md`; source `src/pvaf/`; CLI `scripts/pvaf/`
- Features `data/processed/pvaf/{city}_features.json`; pool `candidate_pool.csv`; rankings `tier1_rankings.csv`
- Reports: `reports/pvaf_tier1_summary.md`, `reports/pvaf_tier1_sanity_n4.md`

**Raw data**
- CAMS EAC4: `data/raw/cams/` (23 years)
- ERA5 pressure levels: `data/raw/era5/pressure_levels/` (23 years, t925)
- MERRA-2: `data/raw/merra2/merra2_pm25_daily.csv`
- Van Donkelaar: `data/raw/van_donkelaar/`
- Tier C raw: `data/external/tier_c/` (6 datasets)
- ERA5 BLH hourly: `data/external/kandy/era5_hourly/kandy_era5_blh_hourly.parquet`

**Project-level docs** (at `d:\ProjectCD\`)
- `CLAUDE.md` — session instructions (this file)
- `PROJECT.md` — detailed stage results, architecture, data inventory
- `RESEARCH_PROJECT_DESIGN.md` — full research design, victory conditions
- **🟢 `docs/README.md`** — **CANONICAL DOC INDEX. Read first to find current vs historical docs; holds the Open-threads ledger.**
- `memory/SESLOG.md` — session history, all version results
- `docs/kaggle_kernel_log.md` — all Kaggle kernel runs
- `docs/research_sanity_check.md` — *(historical foundation, 2026-05-06)* now encoded in HARD RULES below.
- *(historical, bannered: `docs/tier_c_hybrid_pinn_plan.md`, `docs/compass_artifact_*`, ~50 other pre-decomposition docs — see `docs/README.md`.)*

## Key Commands

```bash
# Stage A v1 — train XGBoost + quantile models (from kandy_pm25/)
python src/stage1_satml/models/train_xgboost.py --no-shap

# Supporting cross-continental PINN — local training (testing only — production on Kaggle)
python src/stage3_pinn/training/train.py --model v3 --epochs 1000 --wandb

# Push Kaggle kernel
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 .venv/Scripts/kaggle.exe kernels push -p data/processed/stage2/kaggle_kernel_kandy_td_pinn_v7/

# Regenerate publication figures
python src/comparison/publication_figures.py --all
```

## Critical Gotchas (READ BEFORE CODING)

1. **Target column**: `pm25_observed`, NOT `pm25`.
2. **Date is the index**: parquet files use `date` as DataFrame index, NOT a column.
3. **CAMS on ADS not CDS**: `ads.atmosphere.copernicus.eu/api`. NetCDF dims: `valid_time`, `latitude`/`longitude`.
4. **GEE date range**: never hardcode day-31. Use first-of-next-month pattern.
5. **TROPOMI**: GEE L3 is pre-filtered — no `qa_value` band.
6. **sys.path**: `src/stageN_*/subdir/file.py` needs `parents[3]`. `reports/` uses `parent.parent`. `scripts/` are standalone.
7. **CAMS never as feature**: it's the training label (y), never a predictor (X).
8. **KOALA bias correction**: `apply_koala_monthly_correction()` = flat annual ×0.5984 (NOT monthly despite name). Labels: mean 36.7→21.9 µg/m³. Anchor: Senarathna et al. 2024, CJS 53(2):197-206 = **24.5225 µg/m³**.
9. **Spatial CV R²=0.911 is an artefact** (naive baseline=0.994). Report ONLY as BC generation step.
10. **Hantana ridge**: S/SSW (175-195°), 5-7 km. NOT SW (225°). Open corridor: WNW-NW (230-320°). TBI column: `terrain_blocking_idx`.
11. **enso_mei dropped**: counterproductive (−0.009 R²). Only `mei_month_sin`/`cos` active. Do not re-add.
12. **Pre-2003 rows intentionally dropped**: `year < 2003` filter in build_dataset.py. Do not restore.
13. **Kaggle PINN inference**: ALWAYS on Kaggle. NEVER run FourierPINNV3 inference locally.
14. **blh_norm = BLH_m / 2000.0** everywhere. `t_norm = h/24` (hour-of-day, NOT training fraction).
15. **grid_sampler_2d_backward**: not differentiable for 2nd-order autograd. All `_interp_grid` outputs must be `.detach()`-ed before PDE residual calls.
16. **KANDY has NO burning season.** Mar–Apr peaks = inter-monsoon stability + transboundary transport.
17. **MERRA-2 as label rejected**: r(CAMS,MERRA-2)=0.177 over Kandy. Use ONLY as validation diagnostic.
18. **FourierPINN v2 backbone incompatible with FourierPINNV3**: 0 keys transfer. Do not attempt to load.
19. **409 Conflict on Kaggle push**: update `id` in kernel-metadata.json to match `kernels list` slug.
20. **NPZ dates**: numpy.str_ — use `pd.Timestamp(str(d_str))` not `pd.Timestamp(d_str)`.
21. **SVF is near-uniform across all cities** (~0.977–0.984): ridges are 5-10 km away, beyond the 2 km scan radius. **Drop SVF from SharedTerrainAnsatz** — use delta_z alone for F_valley. Do not re-add SVF.
22. **CityConfig _REPO path**: `_REPO = Path(__file__).parents[3]` → resolves to `kandy_pm25/`. NOT parents[4]. File is at `src/stage3_pinn/data/city_config.py`.
23. **Medellín spatial gradient anti-correlated with terrain**: r(delta_z, pm25_station_mean)=−0.328. High-elevation SIATA stations are cleaner (suburban, less traffic). Medellín is "out-of-regime control" — do not expect positive height-PM slope here.
24. **Kathmandu GD Labs network**: dense 52-station network went live Oct 2025 only. Training window = Oct 2025–May 2026 (8 months). Covers post-monsoon + winter + pre-monsoon — sufficient for trapping-season physics.
25. **P100 incompatible with Kaggle PyTorch** (sm_60 < sm_70 required). Use T4×2 or CPU fallback. All kernels include `_get_device()` capability check.
26. **Kaggle dataset versions re-upload ALL files** (no incremental diff) AND **a version silently DROPS any file not in the bundle dir** — the May-26 v15.1 re-upload lost the v13 per-station parquets, so a 2026-07 kernel failed `FileNotFoundError` until `medellin_perstation_v13.parquet` was re-added. Keep large NPZs/parquets in one dataset; small CSVs in a separate lean dataset. **Mount path (2026-07): datasets mount at `/kaggle/input/datasets/<owner>/<slug>/`** — probe the dated path first + full-walk fallback. `datasets version -p` also needs an ABSOLUTE `-p`.
27. **Medellin GEOS-CF gap**: station data Aug 2018–Aug 2019, but GEOS-CF only from Jan 2019. Filter Medellin to Jan 2019 onwards in any kernel using c_prior. Loses 34% of rows.
28. **CorrectionNet inputs = physics features, NO (lat, lon)**: (sin_h, cos_h, sin_doy, cos_doy, blh_norm, delta_z_norm). lat/lon enable station memorisation → LOOCV collapses. blh_norm+delta_z_norm are OK because they're physics features, not location identifiers.
29. **c_prior (GEOS-CF) systematically overestimates all cities**: Mel ×0.82, ChiMai ×0.53, KTM ×0.79. Formula `F_eff = 1 + positive` can only scale UP — degenerates when c_prior > city_mean. **Always scale c_prior before ansatz**: `c_prior_scaled = c_prior × (station_mean / c_prior_mean)`.
30. **GEE GEOS-CF 2026 latency**: ~2–3 months. Completed GEE task does NOT mean data was available. Check EECU: full year ≈ 36–50 EECU. If EECU < 1.0 the collection had no data.
31. **gitignore `data/` catches `src/stage3_pinn/data/`**: the `data/` rule matches any directory named `data` anywhere in the tree. Add `!src/stage3_pinn/data/` after the `data/` line before committing city_config.py and multicity_loader.py.
32. **Kaggle `dataset_sources` in kernel-metadata.json is NOT applied via CLI push for existing kernels.** Always change the attached dataset via the Kaggle UI. CLI push only updates code. Sentinel in `_find_data_dir()` must point to a file unique to the target dataset.
33. **Bogotá GEOS-CF city_ratio = 0.807** (16.5/20.4). **Mexico City ratio = 0.217** (21.2/97.4). Hardcoded in `GEOS_CITY_MEANS`/`STATION_CITY_MEANS`. MexCity 0.217 is real.
34. **GEE ERA5-Land task description truncation**: `u_component_of_wind_10m` → `u_compon`. Files named `{city}_u_compon_{year}.csv`. `merge_source_city_gee_met.py` handles both prefixes. Do not rename.
35. **OpenAQ S3 archive is public** — bucket `s3://openaq-data-archive/` accepts unsigned boto3. NO AWS credentials needed. The REST API key is for `/v3/locations` discovery only. Use `scripts/ingest_openaq_s3.py`. ⚠ **LIST keys — do not construct filenames** (they are daily, not monthly).
36. **OpenAQ /v3/locations radius capped at 25 km** — use `bbox`. KTM (85.15,27.55,85.55,27.85), ChiMai (98.70,18.50,99.20,19.10), Medellin (−75.78,5.95,−75.35,6.55).
37. **AirGradient LCS over-reads PM2.5 by 30–40%** vs reference monitors. Per-LCS coefficients in `data/external/openaq/processed/eda/{city}/calibration_coefficients.csv`. Apply `pm25_calibrated = (pm25_raw − intercept)/slope`. Median slopes: KTM 1.34, ChiMai 1.40. Drop LCS with calib r<0.5.
38. **Reference vs LCS sensor types** in OpenAQ: AirNow + Air4Thai + Medellin (SIATA) = `reference`. AirGradient + PurpleAir = `lcs`. σ_obs should differ: reference ≈1.5, LCS ≈ obs × 0.30.
39. **c_prior ratio MUST be row-mean, not timestamp-mean**: timestamp-mean weights every hour equally regardless of station count; for cities with growing station counts (KTM 9× growth) this drifts the ratio ~12% and inflates c_prior_scaled ~5 µg/m³. Use row-mean. v11: Mel 0.8070, ChiMai 0.5933, KTM **0.5601**.
40. **deepsensor 0.4.2 has NO Student-t likelihood** as a config knob. Keep `het` likelihood but replace the Gaussian NLL with `-StudentT(df=5, loc=μ, scale=σ).log_prob(y).mean()`.
41. **Overpass API rejects requests without a User-Agent**: returns 406. Set `headers={"User-Agent": "kandy-pm25-research/1.0 (academic; contact: <email>)"}` on every `requests.post`.
42. **ConvCNP terrain bbox does NOT constrain station inclusion**: stations outside the terrain raster still train via per-station context. Wider rasters improve encoder coverage but are NOT required.
43. **Road density must be sampled from a station-footprint kernel**, not the 15×15 km PINN grid — most stations fall outside it → road_density=0 by default. Use `{city}_road_kernel_stations_100m.npz`.
44. **GEE "User memory limit exceeded" on 10-yr hourly ERA5 reductions**: use `tileScale=4`, per-image point-sample → `fc.reduceColumns(reducer.group(groupField=0))`, or a shorter window. **Critical sub-gotcha**: `groupField` is a SELECTOR INDEX, NOT a column name. Quarterly chunking is the standard fix.
45. **FECT Kandy data is via PurpleAir API, NOT OpenAQ /v3**: Sri Lankan PurpleAir nodes are not federated. PVAF Block D correctly returns `n_stations_25km=0, monitoring_tier=M3` for Kandy. Check PurpleAir map before discarding M3 candidates.
46. **CNEMC HeQinWill timestamp format changed mid-archive**: `2022-2023` ISO; `2024-2026` compact `2024-01-15T0000`. `pd.to_datetime(errors='coerce')` silently drops ~50% of rows. Regex-normalise first.
47. **CNEMC `area` field ≠ city name for prefecture-level entries**: Xichang stations are tagged `凉山彝族自治州`. The v15 "Datong" cluster is actually Jincheng (renamed 2026-05-26 across all scripts). GEE tasks submitted with `datong_*` auto-route to `jincheng/`.
48. **GitHub codeload tarball `curl -C -` resume is unreliable**: dynamic tarballs per request → truncated gzip despite "resumed successfully". Download fresh in one stream with `--retry 5 --retry-delay 10`, verify gzip integrity end-to-end.
49. **FECT sensors are VALLEY/SUBURBAN, not highland** (audit 2026-05-29). SRTM-verified: Akurana 12451 = **~460 m, 7.366N/80.618E (OUT of the PINN bbox)**; Hantana TR4 33495 = **~738 m, 7.265N/80.625E**. NEVER describe FECT as "highland" or cite 1538/1698 m. `build_dataset_v3_hourly.py` corrects these at source.
50. **GHAP PM2.5 on GEE — band `b1` is ALREADY µg/m³, do NOT apply the 0.1 scale.** Asset `projects/sat-io/open-datasets/GHAP/GHAP_{D1K,M1K,Y1K}_PM25`. GHAP is the **independent** 1 km reference for U7; quasi-independent → agreement = corroboration NOT validation.
51. **Level anchor is AREA-not-FLOOR (2026-06-04): never force the basin MEAN to KOALA 24.5.** KOALA/NIFS is a valley-FLOOR/near-core point (7.2839 N/80.6322 E, ~27 m above floor), NOT the basin area mean. `features/vandonkelaar.py` `bias_factor`→**1.0**, β≡1. Evidence: two independent AREA products agree (VanD ~19.7, GHAP ~17.0) ~25–30% BELOW KOALA; FECT-Hantana RIDGE reads 10.5 → gradient floor 24.5 > area ~17–20 > ridge 10.5. Shape is β-invariant. Regen chain after any anchor change: `predict_T_anchor_v3`→`build_decomp_map`→`build_overlay_predictions`→`build_spatial_uq`.
52. **KOALA 24.5 is the Jan–Dec 2019 NIFS annual mean ONLY — never propagate it as a per-year reference line.** It was NOT re-measured 2020–2023. In any per-year plot/CSV show KOALA as a single 2019 marker, not an axhline. FECT-Hantana ridge 10.5 is a 2018–23 sensor mean (a horizontal line is defensible there).
53. **Additive-headline regen chain:** `predict_T_anchor_v3.py` → **`scripts/sharpen_T_diurnal.py`** (diurnal+seasonal amplitude bias-correction; preserves annual mean) → `build_decomp_map.py --year Y` → `scripts/build_overlay_predictions.py` → `scripts/build_spatial_uq.py` → `build_additive_field.py` → `exposure_weighting.py` + `health_burden.py` → figures (`paper_figures.py --figs all`). Basin mean preserved (verify G1 Δ<0.05). **sharpen_T_diurnal MUST run after predict_T_anchor (it overwrites the T_anchor parquets in place).**
54. **Kandy is bimodal-rush; deep night is NOT the minimum — the MIDDAY trough is (CORRECTED 2026-08-07, ledger F.38).** Observed FECT diurnal, normalised 2019–2023: morning peak 07 (1.41), evening 18–19 (1.25), **midday trough 14 (0.725)**, deep night 00–04 (0.865). **Night runs ~15% ABOVE midday**, and the model reproduces it (1.110 vs observed 1.145). The previous wording — "deep-night ≈ daily MINIMUM" — is **WRONG** and caused a correct model behaviour to be read as a defect. In figures use deep-night `[0-5]` and morning-rush `[6-9]` separately. Kathmandu is NOT a Kandy analog.
55. **Standalone release repo lives at `d:/ProjectCD/kandy_pm25_release/`** (own git repo `daminda1108/kandy_pm25_model`, gitignored by parent). Package `kandymodel/`. Imports are `kandymodel.*`, root depth `parents[1|2]` (NOT `parents[3]`). To PORT a confirmed change: copy the local file, rewrite imports `src.stage1_satml.* → kandymodel.*`, fix `parents[3]→parents[1|2]`, retest (`paper_figures.py --figs f3,f13` + `scripts/nowcast.py` must stay byte-identical), commit to BOTH repos. Release `data/`+`results/` are gitignored → clone needs `regenerate_all.py`. GitHub metadata via stored cred: `printf "protocol=https\nhost=github.com\n\n" | git credential fill` → PAT → `curl api.github.com`.
56. **`build_station_terrain.resample_dem` returns NORTH-up arrays (row 0 = north).** The multi-city pipeline pairs it with ASCENDING lat + `origin="lower"` → every terrain-derived layer flips N–S. **Fix: `[::-1]` row-flip at each `resample_dem` call site.** Applied in `build_xichang_core_terrain`, `xichang_prod._solver_grids`, `xichang_paper_figures._elev_grid`. Affects only the city-generalised pipeline, NOT the locked Kandy decomp.
57. **Additive form goes slightly NEGATIVE under extreme emission contrast (Kathmandu).** When a clean season drives [T−B]→0 and P_local is very high-contrast (KTM `S_traffic` core/edge **8.27×** vs Kandy ~1.2×), the lowest-emission ridge pixels go slightly negative. Station/floor pixels stay positive → station-level skill unaffected. **Fix = physical floor: clip at 0 at RENDER time** (`xichang_paper_figures.field()`). Cities with >~3× contrast want a non-negative-increment formulation. SEPARATE bug same run: `_pred_at_stations` used `RegularGridInterpolator(fill_value=None)` → a far out-of-box station extrapolated to −15,000; fixed to `fill_value=np.nan`+dropna.
   - **SIBLING FIX — core<periphery INVERSION under NEGATIVE increment (2026-07-09, supervisor-flagged).** When hourly T dips BELOW daily B (**38.5% of Kandy hours**), [T−B]<0 and multiplying a core-high pattern by a negative number makes the CORE render CLEANER than the rural edge. **Fix = increment SPLIT**: `PM = B + max(T−B,0)·P_local + min(T−B,0)` — the local pattern structures only the accumulation above background; ventilation below background is spatially UNIFORM. Basin mean preserved EXACTLY (G1 Δ=0.000); midday core<periphery **38.2%→0.0%**. Also applied to the webapp reconstruction. **Diurnal-B investigated + REJECTED as insufficient.** Propagation COMPLETE 2026-07-16 (paper figures → `paper_figures_v2/`; release `kandymodel/` c28d785; model reference §IV.1.3b + ledger F.10; 8 cities re-scored, no regression; split invariants tested).
   - **V3 EXTENSION — the ventilated-hour pattern FLOOR (additive_v3, 2026-07-21).** The split rendered ventilated hours PERFECTLY FLAT; Medellín ground truth shows they aren't. Production adds a bounded, mean-zero floor `+ε(t)(P−1)`, `ε(t)=max(0,ε0−max(T−B,0))`. Mean-zero ⇒ **T-lock EXACT**; ε0≥0 + accumulation-side P ⇒ **cannot re-invert the core**; structured hours BYTE-IDENTICAL to the split; ε0=0 recovers v2 (**re-verified 2026-08-18, F.47: 5.7e-14**). **Fundamentally ≠ the rejected A2.** ε0 fitted at Medellín → Kandy **ε0 = 3.69** (⚠ the older 2.573 is superseded — it scales with mean accumulation, which the coherence cap moved). Kandy effect: flat hours 56.6%→45.3%, annual means + pop-weighted exposure unchanged (+0.2%), inversion 0.0%. **Paper figures NOT regenerated — unnecessary** (annual-mean field 99.99% corr v2↔v3). Canonical `assemble_year()` param **`EPS_FLOOR`**. Three impl traps in `docs/model_accuracy_plan_2026-07-21.md` §2 (P from q95 not q50; bounded-climatology substitution on flat hours; **never clip the parquet at 0** — gotcha #65).
58. **Pandoc `\ref{}` does NOT resolve in the preprint build — use hardcoded figure numbers.** pandoc-crossref is NOT installed. In-text callouts use hardcoded numbers, so **removing/inserting any figure shifts all later callouts** — re-map them. After any figure change verify the PDF has zero `Fig.~`/`??`/`ef{fig` artifacts. Also: heredoc `\rho`/`\ref` in bash gets `\r`-mangled — edit those strings via the Edit tool.
59. **Emission surface is a PROXY for the local-emission spatial pattern, NOT a source inventory — and the model does not cap total PM at traffic.** `S_emit`/`S_traffic` only sets the SHAPE of the local increment; the LEVEL is carried by T(t), pinned to total observed PM (all sources). Diurnal timing e(t) is source-mix-aware (per-city `emix`). The traffic-centrality proxy assumes local combustion co-locates with the road network — ⚠ **the Kandy "~90% vehicular" justification is REFUTED (F.66): traffic is 7.6% of measured PM2.5 mass, biomass burning 14.1%; what IS measured is that traffic dominates the local increment's sub-daily TIMING (F.23)** — the proxy empirically recovers held-out rank across mixed-source cities (Medellín 0.78, Tai'an 0.68), but **misplaces fine hotspots where a major source is spatially decoupled** (Yichang). A source-resolved (sector-weighted) surface exists in `src/modular/emission.py` but is NOT wired into production.
60. **ERA5-Land `total_precipitation` on GEE is ACCUMULATED since 00 UTC (daily reset), not per-hour — de-accumulate before any hourly use.** Summing raw hourly values gives ~12× true rainfall. Correct: `tp[h] − tp[h−1]` within each UTC day, `tp[00h]` as-is, clipped ≥0. (ERA5 non-Land hourly tp is already per-hour.) Even de-accumulated, ERA5-Land is NOT gauge-accurate for a steep-valley area mean — see #63.
61. **A driver-anchored EXTENSION tier must inherit the LOCKED monthly B/T ratio — a flat background silently kills the local field (user-caught).** With a flat `(1−f)×annual` background, Kandy July-2026 came out at B/T **1.34** with only **18.6%** of hours above background (locked years: 0.79 / **70.2%**) → the field renders almost featureless. Fix: `_locked_b_over_t()` in `kandy_driver_tier_build.py` → 92.3% accumulation hours. Sibling: the driver GBM **damps the diurnal amplitude** → apply `sharpen_to_locked`. Check BOTH on every new extension year.
62. **A self-checking live system needs its own liveness check — silence reads as "no data yet".** The Medellín live scoreboard logged 10 issuances and **0 observations for ~a week** without erroring: WAQI's SIATA mirror drifted to a ~6 h delay and the 3 h staleness filter rejected every station. Fix: window **12 h** (safe because each value is keyed to its own measurement hour) + log every station-hour with ≥3 reporters + emit obs AGE diagnostics on every skip. Rule: any scheduled ingest needs an alarm on "N consecutive runs with zero rows", not just on exceptions.
63. **GPM IMERG is the rain source, NOT ERA5-Land tp — and a "gauge" reference must match the geometry you are checking.** Settles #60. IMERG V07 (`precipitation` = a RATE in mm/hr on 30-min steps → hourly mm = mean of the two rates) lands at **0.98×** the DoM representative station (Katugastota 2108 mm) at Kandy; de-accumulated ERA5-Land is **2.10×** there, 3.6× at Medellín, and **1.8× IMERG on the SAME box** → a model wet bias, not just geometry. TWO traps: (a) the project record's Medellín "gauge ~2,000 mm" was WRONG (floor gauge = 1,500–1,800) — **verify a reference before it drives a ship/no-ship call**; (b) at Medellín the reference is a valley-FLOOR gauge while IMERG is an AREA mean → ratio >1 is EXPECTED (same area-vs-floor confound as #51). Medellín ships IMERG labelled **basin average**; Kandy ships it plainly. **Where IMERG is absent the exporter ships JSON `null` and the panel omits the row** — never fall back to the rejected product. (Bare `NaN` is invalid JSON — emit `None`.)
64. **`_find_folder_id` returning `files[0]` silently loses exports — Drive allows duplicate folder names.** GEE writes successive exports into *different* same-named folders. `download_gee_drive_outputs.py` now scans EVERY matching folder (`_find_folder_ids`, first copy wins on duplicate filenames). Also: `Export.table.toDrive` names the file from `fileNamePrefix`, so a per-city prefix will NOT match a consumer glob — check the glob after any new export.
65. **Never clip a field at 0 in the parquet when a downstream consumer derives its ANCHORS from that field.** The webapp exporter sets T05/T50/T95 = the shipped field's per-hour basin mean, so a clipped parquet hands it an anchor that no longer matches the one the field was built with — the client reconstruction then cannot reproduce the field (surfaced as a stubborn 0.55 µg/m³ QA failure that survived three unrelated "fixes", and it bit **q05** on deep-ventilation hours). Every consumer already clamps at render, so store RAW values: that keeps `mean(field) == anchor` exactly. Siblings: recovering P by inverting the split **explodes** where the increment is tiny → invert only where the increment is healthy and substitute a bounded (month, hour) climatology elsewhere; and recover P from the **q95** side, never q50.
66. **"Inside the field of regard" ≠ usable — for any geostationary sensor check the VIEWING GEOMETRY and the SCAN-WINDOW/local-hour overlap BEFORE pursuing access (GEMS rejected).** GEMS sits at **128.2°E** vs Kandy **80.6°E** → **VZA 55.1°**, AOD pixel **~13 km**, so the entire 15×15 km domain is **≈1.1 pixels**; and its scan window overlaps Kandy's sunlit hours only **07:30–13:15 LT** — missing the 14 LT trough, the 18 LT evening peak and the whole night. Compute both from orbital geometry (`cos γ = cos φ · cos Δλ`, then `tan VZA = R_s sin γ / (R_s cos γ − R_e)`) and the target's solar-zenith window — minutes, and decisive. Fine at Chiang Mai (VZA 40°) and Xichang (43°).
67. **Selecting a regional data tile BY CITY NAME is a landmine; select it by geography.** `citypack.vand_tile` read `VAND_SA if self.slug == "medellin" else VAND_ASIA` — silently wrong the moment a second American city was added. The Asia tile spans lat −10..60 N, so a tropical American city's LATITUDE selection succeeds and only LONGITUDE is empty; it dies six frames later inside scipy as `ValueError: cannot reshape array of size 0`. Fixes: (a) choose the tile from the city's **own longitude**; (b) make the selector **raise on an empty result**, printing tile vs requested bounds. Any `if slug == "..."` in a data-resolution path is the same bug waiting. Sibling: older `*_stage3_perstation` parquets lack `c_prior` → `scripts/add_cprior_to_perstation.py`.
68. **A model calibrated on a record cannot be scored against that record — check provenance BEFORE quoting any "improvement".** Production `T(t)` is trained on the FECT residual target AND amplitude-sharpened to FECT, so its agreement with FECT (seasonal **0.976**, daily **0.682**) is **in-sample fit against its own calibration target**. The sensorless anchor (0.78 / 0.41) is out-of-sample. Differencing them measures the calibration, not the information gain. **Rule: before quoting a delta between two model variants, establish for EACH whether the scoring data was used to fit it.**
69. **NaN is not a measured null — never report an uncomputed metric as a confirmed negative.** The preprint claimed Chandigarh's spatial skill "duly vanishes", but `rho` is computed only `if len(common) >= 4` and Chandigarh (n=4) → **NaN**. The **−0.80** in the older project record is an N=4/N=5-era value and must not be resurrected. **When a table says "—" and the prose says "vanishes", the prose is wrong.** Sibling: the entire exposure/health block was quoting v1-era numbers while the pipeline had moved to v3 — **re-read the CSV before every submission, never trust the prose**.
70. **A fix to a DERIVED artefact must live inside the code that derives it.** The background re-level was applied as a standalone pass over the B parquets, then the rebuild chain regenerated B from scratch and silently discarded it. Nothing errored; it surfaced only because the LOCKED years came back bit-identical. The fix now lives inside the builder behind a `RELEVEL` flag. **Rule: before writing a correction to a file, ask which script owns that file's contents; if any script regenerates it, the correction belongs there.** Same family as #65 — and rebuilding `additive_v2` without `additive_v3` left the exporter reading a stale field against fresh anchors and **failed the QA gate at 5.61 µg/m³** against a 0.25 tolerance. Never ship on a partial rebuild.
71. **`git fetch` before declaring a scheduled job dead.** Across an entire session I reported the hourly Kandy live Action as "not committing since 2026-07-25" and reasoned from that. The Action was fine — the remote had live-bot commits through 2026-08-01T17:27Z. I was reading a **local clone that had never been fetched**. Any claim about remote state — commits, CI, releases, issues — requires a fetch first.
72. **A build flag must not change the physics; and a "neutral" normalisation can make a term inert.** (a) Running the extension build as `--years 2026` left the driver frame holding only 2026, whose 36 GEOS-CF rows tripped a `len(ref) < 1000` fallback to `shape = ones` — the background lost its daily modulation and the year jumped to **100% accumulation hours in every month**. A CLI flag meant to select *which years to build* changed *how they were built*. `_prior_reference()` now loads the reference years independently and **raises instead of silently flattening**. (b) The dilution factor was normalised **within each day**, which makes it arithmetically incapable of lowering the midday background — the one thing it was added for. **If a modulation is normalised over the same window it is meant to redistribute within, it does nothing.**
73. **A descriptor derived from the target's own outcome LEAKS, even when the target is held out of the prediction.** The city-graph donor kernel scored 0.860 with `peakiness` — the amplitude of the city's *own* diurnal shape — among its similarity features. LOO excluded the target's shape from the *prediction* but not from the *descriptor used to choose donors*. Removing it, plus `log_stations`, cut the honest gain to +0.017. **Admissibility rule: a descriptor may be used only if it exists for a target with NO local observations.** Sibling of #68.
74. **Never average a skill-vs-baseline percentile across metrics.** The anchor-sensitivity script first reported "beats 47% of random pairs → REPRESENTATIVE". That was the mean of **10%** (RMSE), **23%** (level bias) and **97%** (seasonal r): two opposite effects cancelling to a meaningless middle. **Report per metric, always.**
75. **Before concluding "the intervals are too narrow", separate CENTRING from WIDTH.** The shipped 90% interval covers 72.4% at the FECT pixels. Observations fall below the lower bound in 25.7% of hours and above the upper in 1.9% — a one-sided failure with a median offset of +5.85. Removing each sensor's own median offset restores **91.5%**. The width was right; the field is an area mean and the sensors are points (#51 geometry). ⚠ **2026-08-22 (F.65): the NBRO Kandy record does NOT show this offset** — the standing prediction that any Kandy point measurement will read ~40% below the model held for three LCS records and failed for one non-LCS record. Treat the direction as open.
76. **A tier can pass every AGGREGATE check and still be unusable — always test the TAIL separately.** The 2024–2026 driver tier matched the anchored years on annual mean, monthly means, seasonal shape, diurnal swing and phase. It was nonetheless broken: hours above 55 µg/m³ fell from ~85/yr to **0.5/yr**, with a hard ceiling at the **99.2nd percentile**. A user spotted it from the maps because **every diagnostic in the suite was a mean**. Causes compound: a quantile GBM predicts **leaf averages** and **cannot extrapolate**; the tier is **lag-free** so multi-day episodes cannot build; and `sharpen_to_locked()` corrects only the climatologies. **Fix:** measure the damping by leave-one-year-out, then invert it **indexed by quantile**. Validated: p99 44.6→54.9 vs truth 54.9; hours>55 1.8→88.2 vs 84.8. ⚠ It fixes **how often** episodes occur, **not when**.
77. **Never report an outward-facing action as done without verifying the artifact — and confirm you are in the right repository.** In one session I reported a push as successful **three times** when it had not happened: twice because `cmd; echo "pushed"` runs the echo regardless of exit status, and once because the `cd` had not persisted so I verified the **framework repo** while believing I was in the webapp. **The check is `git rev-list --count origin/main..HEAD` (0 = pushed) plus grepping `origin/main` for the specific commit subject, run with `git -C <path>`.** Related: setting `core.compression 0` while diagnosing a slow upload makes every subsequent upload *larger*.
78. **A canvas with an explicit pixel width can LATCH wide and never shrink.** `fitCanvas()` writes `cv.style.width` from the parent's measured width; if it ever measures while the parent is wide, that width sticks and can never come back down. On the live explorer: **904 px of horizontal overflow at a 375 px viewport** after any viewport change, while a *fresh* mobile load was fine. **Fix belt-and-braces: `canvas { max-width: 100% }` AND clamp the measured target to `document.documentElement.clientWidth`.** Sibling lesson: audit a responsive layout by *changing* the viewport, not by loading at each size.
79. **Measure a saving before quoting it.** I reported that de-duplicating in-flight `getScalars` fetches would recover "~1.3 MB". After shipping, requests fell 15 → 8 and total transfer was **unchanged at 4053 KB** — the duplicates had been served from browser cache. The fix is still right but the headline number was invented from a request count. **A count is not a cost.** In the same audit I also called eager year-loading a defect when `app.js` already deferred it — read the code before reporting the diagnosis.
80. **[RESOLVED 2026-08-18 by the F.49 paired rebuild — reproducibility now 0.000e+00. The lesson stands.] A stored product can go stale against its own builder, and every gate we own is blind to it (F.47).** Re-running `build_v3_from_v2` for 2022 from the STORED inputs reproduced the model bit-exactly — and differed from the **shipped** parquet by up to **2.06 µg/m³ on 2,370 of 8,760 hours**. **Why nothing caught it:** the discrepancy is a **mean-preserving spatial redistribution**, so the T-lock holds *exactly*, and the G1 gate, the exporter QA, the 18 invariant tests and every annual/seasonal/diurnal diagnostic are invariant to precisely this class of error. **The determinism claim was verified for the RELEASE repo and never for the framework's own products.** Fix: a reproducibility check that rebuilds from stored inputs and diffs against disk. ⚠ Repairing this needs a **v2+v3 rebuild together** with the exporter QA re-run. Sibling of #70: **I also spent a round diagnosing the stale artefact as if it were the code, published a wrong cause (the pattern clip — inert), edited four files including the public README, and reverted them. Run the builder; do not reason about it.**
81. **🔴 NEVER open a file in truncating mode as part of a read-modify-write (2026-08-22 — this wiped CLAUDE.md).** `io.open(path, "w", ...)` truncates the file the instant it is opened. In a one-liner of the form `io.open(p,"w",...).write(transform(s))`, Python evaluates the `open` **before** the argument, so if the transform or the encode raises, the file is already empty and the content is gone. That is exactly how `CLAUDE.md` — untracked, with no backup and no shadow copy — went to **0 bytes**. It was recoverable only because its full text happened to be in the session context. **Rules: (a) write to a temp file and `os.replace()` it in; (b) never use the Bash/Python route for an in-place edit when the Edit tool will do it; (c) `errors="surrogateescape"` on the read AND the write when a file may hold lone surrogates.** And **git-track the context files** so the next slip is a `git checkout` away.
82. **🔴 An admissibility check that only prevents CHEATING UP is half a check — a rung that UNDER-uses its budget inflates every gain above it (2026-08-23, F.84).** `Budget.require()` raised when a tier touched a stream it did not admit, and said nothing when a tier quietly failed to use what it had. The scored `Bud0` used **one of the three streams its budget admits** (7 meteorological drivers; no satellite level, no static geography) while the spec AND its own pre-registration both said otherwise. Because every ladder gain is measured against the rung below, the headline `Bud0→Bud1` was inflated **25.6% → 17.9%** and the Colombo test was scored against a strawman. **Fix shipped: `Budget.require_covers()`** asserts a tier uses every stream it admits; omissions must be declared via `allow=` at the call site. **Rule: for any tiered/ablation design, assert coverage in BOTH directions, and check the implementation against the registration — not just against the spec.**
83. **`q50_blend` in `predictions_blend_v3.parquet` is ALREADY the absolute prediction, not the residual (2026-08-23, F.82).** The v3 architecture is residual learning (`pm25 − c_prior_anchored`), so the natural reconstruction is `q50_blend + c_prior_anchored` — which gives **R² = −3.56**. The stored column is post-reconstruction: `q50_blend` alone gives **0.5814**, matching the recorded 0.581. **Verify any recomputed v3 metric against 0.581 before trusting it.**
84. **Windows Python cannot resolve `/tmp` even though Git Bash can — and `cmd; echo done` masks the real exit status.** A patch script written to `/tmp` and run through the venv python silently no-ops (file not found from Python's view) while bash reports success. Two consequences hit in one session: an edit appeared to apply and did not, and a killed background job reported exit 0 because a trailing `echo` followed it. **Use the scratchpad or a repo path for anything Python must read, and never put a bare `echo` after a command whose status you need** (the sibling of gotcha #77).

## Pending Tasks (updated 2026-08-22)

Narrative/history for everything below lives in `memory/SESLOG.md`.
This section is the FORWARD list only.

### 0. 🔴 IMMEDIATE (2026-08-23)
0. **WRITE THE PAPER.** Testing is finished. Plan `docs/paper/rewrite_plan_2026-08-22.md` (methods-primary, Kandy as demonstration), claims audit + drafted replacement passages `docs/paper/claims_audit_2026-08-22.md`, positioning `docs/paper/literature_positioning_2026-08-23.md`. **Start with §2, the formulation.** ⚠ **Do not run more tests** — the remaining candidates are low-value and each risks delay without changing a conclusion.
0b. **Decide on OSF `nxqgb`** (the first, superseded Colombo registration) — recommendation: **let it stand**, cite it as run/reported/superseded, because *why* it was superseded is itself the finding. User's call.
0c. **Two submission blockers:** figure-numbering hygiene (editors desk-reject on it, gotcha #58) and swapping **`turbo` off the episode scale** (F.83 — it is the only palette that fails the colour-vision check, and it is used on the most consequential maps).
1. **Re-export the webapp payload and commit** — already QA-passed at 0.0014 µg/m³ (tolerance 0.25), wind parity 0.0005 m/s, **not yet deployed**. `kandy_webapp/` is a separate repo. ⚠ Bump the `?v=<ts>` cache-bust; ⚠ verify the push with `git -C <path> rev-list --count origin/main..HEAD` (gotcha #77).
2. **Send the CEA letter** — with the Torrington Park BAM defunct, CEA is the **only** route to a Kandy reference monitor, and it is the one acquisition that settles both W11 and W6. University letterhead → Director General, copy DDG (Environmental Protection), then the R&D agreement.
3. **Decide what to do about `emix`** — `vehic = 0.85` is now known to misstate the mass split (F.66). Either wire `src/modular/emission.py` with a burning sector, or declare the weight as a *timing* prior in the docs. **Do not claim a skill gain from it.**

### 1. Preprint / manuscript — critical path, ENTIRELY USER ACTION ★★★★★
The 28 pp manuscript in `kandy_pm25/docs/paper/` is built and adversarially reviewed.
**Phase 9, circulation to the four readers, is the user's step.** Then Zenodo DOI → submit.
- **🆕 BEFORE SUBMISSION (mandatory):** (a) **cite and position EGU26-9786** (CICERO/HISP/MoH/Oslo — Sri Lanka 1 km *daily* PM2.5, 2020–2023); (b) **name CEA explicitly** in the public-data survey; (c) **🆕 add Nirmani 2025 and Attanayake 2025** — they now carry the only independent Kandy checks the paper has (F.65).
- **Uncommitted:** `scripts/spatial_skill_law.py` has the Bogotá slug fix.
- **Optional:** one genuine tropical **South/SE-Asian** analogue would dent the China-heavy critique more than Bogotá did.
- **Audit boundary (not re-verified):** Kandy descriptive claims (0.4 M residents, ~500 m elevation) and the OSF prereg text itself.

### 1b. Two papers, not one (2026-08-22 publication view)
**(A)** the methods / value-of-information paper — 47 cities, budget ladder, three confounds caught by registered gates, two measured ceilings. **Needs no Sri Lankan data; strong and novel.**
**(B)** the Kandy application — weaker alone, strong once A exists.
The current manuscript sits between them and should be **split rather than defended**.

### 2. Post-preprint engineering ★★☆☆☆ — the top three are CLOSED BY MEASUREMENT
~~Anomaly-target GBMs~~ **DONE, NOT ADOPTED (F.16).** ~~Consolidation v3~~ **BUILT FIVE TIMES, ALL REJECTED (F.13/F.15/F.17/F.18)** — do not attempt a sixth reformulation. ~~f-partition~~ **RESOLVED BY PHYSICS (F.43), f ≈ 0.48.**
4. **UI U3 remainder / U4** — date-time picker, timeline redesign, mobile sheet, chart kit, guided tour (`docs/webapp_ui_overhaul_plan_2026-07-21.md`).
5. **FNO WindNinja emulator** — methods contribution; improves an *unscored* layer, so it cannot move a validated number.
6. **Forecast polish (paper 2):** clean per-lead skill curve (needs the archived GEOS-CF forecast pull extended to Oct2022–Sep2024) · per-lead k(lead) instead of one 1.35 · score the forecast's **B component** against the logged NBRO regional stations · Aurora as a benchmarked alternative driver.

### 2b. 🔬 WEAK-POINT REGISTER (opened 2026-08-06)
| | item | status |
|---|---|---|
| ~~W1~~ | shipped interval never coverage-tested | **CLOSED** (F.25) width correct, centring by design |
| ~~W2~~ | anchor pair hand-picked → flatters panel? | **CLOSED** (F.24) level conservative, seasonal +0.01 optimistic |
| ~~W3~~ | 7-source data survey never re-verified | **CLOSED** — and found the NO₂ spatial network |
| ~~W4~~ | `KOALA_ANCHOR` 4 s.f. unsupported | **CLOSED** — prose corrected in 5 places |
| ~~W5~~ | FECT calibration itself unvalidated | **CLOSED / CORROBORATED 2026-08-22 (F.64)** — Akurana 17.8 vs a BAM-anchored ~18–19 |
| 🟡 **W6** | **REOPENED then NARROWED 2026-08-22 (F.66 → F.71).** F.23 corroborated the vehicular **timing** (3.67× rush ratio) and said so; the **mass** share was never tested. Katugastota PMF gives traffic **7.6%** / biomass **14.1%**, but a 20-site study resolves it by geography: traffic **predominant in the urban core**, firewood **co-dominant there, dominant rurally**. **Never restate "~90% vehicular"**; defensible core `emix` is **`vehic ≈ 0.5–0.6`, `burn ≈ 0.3–0.4`**. | narrowed |
| ~~W7~~ | ε-floor transferred from n=1 city | **CLOSED as a measured limitation** (F.30) — eps0 does NOT transfer; Kandy's value sits inside a pooled bracket, not contradicted but not determined |
| ~~W8~~ | f a distrusted prior | **CLOSED** (F.21/F.22, then F.43) |
| 🔴 **W11** | **NEW 2026-08-22 (F.65)** — three of four independent Kandy point records sit **below** the model (LCS, all carrying a downward calibration), one matches (undocumented instrument). A **level** discrepancy on the axis called strong. **Report as open; do not resolve by picking the agreeing record.** | OPEN |
| ~~W10~~ | e(t) evening lobe misplaced | **CLOSED** (F.29) — fitted; prior's evening/morning ratio 0.97 REFUTED (measured 2.14) |
Also standing, by design not oversight: `A_transport` entirely unscored · panel selected by similarity not data quality · panel does not bracket Kandy · **`Bud4` is a declared design assumption, not a validated rung (F.60/F.61)**.

### 3. 🎯 THE ONE THING THAT UNBLOCKS EVERYTHING — a local measurement
Routes, **re-ordered 2026-08-22 by measured value**:
- **⚫ Torrington Park BAM-1020, Kandy (F.65) — DEFUNCT (user, 2026-08-22).** It anchored two published Kandy records but no longer operates. **Do not re-propose it.**
- **🔴 NBRO regional background** — the background rung is the largest measured gain in the programme (F.51/F.54) and **has no free substitute** (F.63 ruled out Colombo at r 0.60 vs a 0.92 benchmark). NBRO also supplied the Kandy series in F.65, so the channel demonstrably works.
- **CEA Kandy AQMS** — granted in principle 2026-08-12, hourly 2019→2026-05 incl. full met; blocked on a letter + R&D agreement. Gap 2021-07→2022-10.
- **⚠ CEA passive NO₂ — DEMOTED.** It will **not** fix `P_local`: the spatial ceiling is measured and information-limited (F.56/F.61). Its value is the `f` partition and local activity tracing only.
- **Mobile campaign** — 4–8 drive days per segment (~34 calendar days full-domain) and it **still needs one fixed reference to anchor to**.

### 3b. Parked by dependency
- **SIATA portal registration** (user email) for Medellín ground data past Sep-2024.
- ~~Medellín health panel~~ — **DROPPED** 2026-07-25 (user: Kandy only).

### 4. Closed — do NOT re-litigate (each has a recorded reason)
Spatial-skill ceiling is **information-limited**, now established **six** independent ways:
tiny within-city signal (~±10% at Kandy) · emission≠concentration vs ground truth ·
Track-S learned-pattern null (ρ≈0.14) · dynamic-transport null (monitors floor-sited) ·
**AlphaEarth EO-embedding null** · **a full LUR predictor set moving pooled ρ from +0.273 to +0.275 (F.61)**.
Also closed: **GEMS** (viewing geometry + scan window, #66) · A2 multiplicative amplitude ·
diurnal-B · κ calibration · ConvCNP assimilator · **GNN/PINN *at* Kandy** (GraPhy loses to IDW
below ~0.16 sensors/mi²; Kandy sits at 0.023) · diffusion downscaling · **Colombo as a
background donor (F.63)** · **the civil-vs-solar-time diurnal hypothesis (F.62, refuted by
construction)**.

### 5. Genuinely open housekeeping
1. **`docs/stage_c_data_dictionary.md`** — still documents the v11 schema; add `road_density`, `ntl_log` + provenance/QC. Low value now that ConvCNP is retired, but stale.
2. **Bootstrap CIs on the v3-extended pooled R²** — still a single-run point estimate (0.581).
3. **Senarathna comparison figures** — refresh against v3-extended numbers.
4. **`config.py` constants** — locked (`KOALA_ANCHOR=24.5225`, `KANDY_GEOS_CF_RATIO=0.536`, `STATION_CITY_MEANS`, `GEOS_CITY_MEANS`, `CITY_RATIOS`); verify periodically. Quote KOALA as "about 24.5", never as a figure Senarathna 2024 prints.
5. **The monograph** (`docs/paper/monograph/`) — complete main text, halted by choice. Resume only if a thesis-length document is required.

Foundational reading: [`docs/REDESIGN_2026-05-08.md`](docs/REDESIGN_2026-05-08.md) ·
[`docs/AUDIT_2026-05-08.md`](docs/AUDIT_2026-05-08.md) · doc index [`docs/README.md`](docs/README.md).

## HARD RULES

- **No workarounds for missing tools — get the optimal thing.** If a task needs a library, dataset, font, or tool we don't have, INSTALL/ACQUIRE it rather than substituting a degraded stand-in. Only fall back when the proper thing genuinely cannot be made to work — and say so explicitly. Default to the optimal result, not the convenient one.
- **When in doubt, VERIFY — never guess.** If uncertain about a fact, parameter, method, constant, API, or whether a claim is correct, do NOT fabricate or assume. Surface the doubt (a one-line note), then resolve it with web research against authoritative sources before proceeding. Guessing on numbers/methods is a correctness failure; an extra search is cheap. Applies especially to literature values, emission/health/physics parameters, and "is this the right approach" questions.
- **🆕 Git-track the context files.** `CLAUDE.md`, `PROJECT.md`, `PROJECT_ARCHITECTURE.md`, `README.md`, `memory/SESLOG.md` and `kandy_pm25/docs/model_reference/F_epistemic_ledger.md` are **tracked and committed** (user directive, 2026-08-22, after CLAUDE.md was destroyed by a bad in-place write — gotcha #81). Data, results, figures and checkpoints stay out of git. Commit context-file changes at the end of any session that edits them.
- **Single target: Kandy.** Nuwara Eliya and Badulla are NOT in the deployment pipeline.
- **NEVER report Spatial CV R²=0.911** as a spatial modelling result — it is a label-construction artefact.
- **PyTorch raw autograd** for the supporting cross-continental PINN experiment. Never suggest DeepXDE.
- **TD-PDE only for the cross-continental PINN experiment** (∂C/∂t + u·∇C = ∇·(K∇C) − v_d·C + S). QSS abandoned. Never revert.
- **Stage B is ConvCNP residual learner (deepsensor)** — predicts `pm25 − c_prior_scaled`, NOT pm25 directly. **No PDE constraint at the spatial step.** SharedTerrainAnsatz iteration cancelled. PINN spatial work cancelled.
- **Native resolution: 1 km hourly.** No 100 m / 30 min headline. No presentation disaggregation step.
- **KANDY_PINN_BBOX** ≠ **KANDY_BBOX**. Always use KANDY_PINN_BBOX (15×15 km). Never the 40 km satellite bbox.
- **Supporting cross-continental PINN experiment** is NOT a feeder for Stage B.
- **Anchor framing at Kandy:** "consistency anchors pending field validation," NEVER "validation." KOALA/Senarathna/MAIAC double as upstream calibration anchors → not independent. ⚠ **The NBRO and RF-CNN records (F.65) ARE independent** — they may be called checks, with their caveats attached.
- **3-seed runs with bootstrap CIs on every reported r.** Single-run point estimates are uninterpretable.
- **Coverage / calibration reported alongside every r/RMSE.** UQ is a contribution.
- **"Few-shot transfer" framing, not "meta-learning."** N=3 is too small for a meta-learning claim.
- **"Sim2Real" only if Phase 1 actually runs (decision gate).**
- **No PINN spatial work after 2026-05-08.** Cut definitively.
- **README.md, PROJECT.md, CLAUDE.md are single-source-of-truth.** All other docs cross-reference; no number is restated.
- **NEVER use "sequential data assimilation"** — correct term if used: "multi-fidelity cascaded framework" (Peherstorfer et al. 2018), but verify it actually applies before citing.
- **Stage B framing:** ALWAYS "exploratory cross-city transfer," NEVER "validated spatial model."
- **Persistence-dominance defence:** when SHAP (56.8% lags) is raised, the canonical rebuttal is the Senarathna diurnal r=+0.865 — lag-1h has no hour-of-day phase, so persistence-only cannot produce that pattern. Plus +8.0% reanalysis ablation.
- **Sensor expansion is THE binding constraint going forward.** Architectural and feature-engineering levers are exhausted within N=2.
- **🆕 An admissible descriptor must exist for a target with NO local observations** (gotcha #73). Anything derived from the target's own outcome — including for donor selection — leaks.
- **🆕 Admissibility is checked in BOTH directions (2026-08-23, F.84).** `require()` stops a tier using a stream it is not entitled to; **`require_covers()` stops a tier silently under-using its budget**, which inflates every gain measured above it. Any new tier or ablation asserts both, and any deliberate omission is declared via `allow=` at the call site. **And the implementation is checked against the PRE-REGISTRATION, not only against the spec** — all three disagreed and nobody noticed for five days.
- **🆕 Value of information is a property of the information AND the estimator (2026-08-23, F.88).** Never write "even a linear model reproduces it". On the 68-feature `Bud0c` a linear baseline collapses and the first rung reads 50% instead of 12%. The defensible claim is **robust across non-linear estimators**.
- **🆕 A tier's claim tier is set by its evidence, not its position in the ladder.** `Bud0`–`Bud3` are validated; **`Bud4` is a declared design assumption** and must be labelled as such wherever it appears.

## Doc Update Protocol (what goes where)

When running `/update-docs`, route information as follows:

| Information type | Destination |
|---|---|
| **A headline number, a refutation, or an open question changing** | **CONTEXT.md** *(tracked, <250 lines — keep it tight; prune as hard as you add)* |
| Current stage status (1-line summary per stage) | **CLAUDE.md** Current State |
| Pending tasks (active only, top 7) | **CLAUDE.md** Pending Tasks |
| New gotcha / hard rule discovered | **CLAUDE.md** Gotchas or Hard Rules |
| Session narrative (what happened, decisions made) | **SESLOG.md** new dated entry |
| Kernel run result (gates, metrics, root cause) | **SESLOG.md** + `docs/kaggle_kernel_log.md` |
| **How** a component is built (maths, module map, flow, invariants, tests) | **PROJECT_ARCHITECTURE.md** *(tracked)* |
| **What** came out (stage results, metrics, epistemic status) | **PROJECT.md** |
| Completed version results (v1–vN history) | **SESLOG.md** only (not CLAUDE.md) |
| Data inventory, download status | **PROJECT.md** |
| New file paths created this session | **CLAUDE.md** Key Paths (if actively used) |
| Model/claim change a reader of the paper would need | **model reference + ledger `F_*`**, then rebuild COMBINED |
| Anything a stranger reading the repo would see | **README.md** *(tracked — check it for refuted claims)* |
| A doc becoming current or historical | **`docs/README.md`** index |
| User preference / workflow feedback | `memory/` auto-memory (feedback type) |

**Rule**: CLAUDE.md shows only *current* state; history lives in SESLOG. `PROJECT_ARCHITECTURE.md`
owns *how it is built*, `PROJECT.md` owns *what came out* — where a number appears in both,
PROJECT.md wins.

**`README.md` and `PROJECT_ARCHITECTURE.md` are public.** A claim that changes internally has to
be checked against them in the same pass, or the repo ends up publicly asserting something the
project has already refuted. That is exactly what happened to the local/regional partition
between 2026-06-08 and the 2026-08-06 doc audit.

## Compact Instructions

**Before compacting** (always, no exceptions): append a compact-checkpoint entry to `memory/SESLOG.md`:
```
### COMPACT CHECKPOINT — YYYY-MM-DD HH:MM
**Decisions made:**
- [list key architectural/strategic decisions from this conversation]
**Current kernel:** [slug, status, last known gate values]
**Blocker / next action:** [one line]
```
Then compact. This ensures no decision context is lost across compactions.

When prioritizing what to keep in context: current kernel gate results, pending tasks, decisions. Drop: file exploration outputs, verbose training logs, resolved bugs, version history.

## Directory Rules

1. Model source code → `kandy_pm25/src/`. Utility scripts → `scripts/`. Reports → `reports/`.
2. Data → `kandy_pm25/data/`. Results/figures → `kandy_pm25/results/`. Never outside these.
3. Papers → `references/papers/`. Design docs → `docs/`. Old artifacts → `archive/`.
4. Never put loose `.py` files in `kandy_pm25/` root.
