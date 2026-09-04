# CONTEXT — the load-bearing facts

**Read this first.** One page of what is true, what is refuted, and what is open.
Everything here is distilled from `CLAUDE.md`, `PROJECT.md`, the epistemic ledger
(`kandy_pm25/docs/model_reference/F_epistemic_ledger.md`) and `memory/SESLOG.md` — those stay
authoritative. **Keep this file under 250 lines.** Last updated **2026-08-22**.

---

## 1. What the model is

An **information-tiered grey-box decomposition** for urban PM2.5 in data-scarce cities.
Hourly, 1 km, single production target: **Kandy, Sri Lanka**.

```
PM(x,y,t) = B(t)  +  max(T(t)−B(t), 0)·P_local(x,y,t)  +  min(T(t)−B(t), 0)  +  ε(t)·(P−1)
            ↑                ↑                                  ↑                  ↑
        regional      local accumulation              uniform ventilation    ventilated-hour
        background    structured by emissions         (never re-inverts       pattern floor
        (daily)                                        the core)              (mean-zero)
```

- **T(t)** — temporal anchor. GBM on exogenous drivers, conformal-wrapped, re-anchored per year
  to Van Donkelaar, then amplitude-sharpened to the observed FECT swing.
- **B(t)** — regional/transboundary background. Rural-VanD floor × GEOS-CF seasonal shape.
- **P_local** — unit-mean local pattern = normalised `S_emit · M` (`A_transport` = scenario).
- **ε(t)** — bounded, mean-zero floor so ventilated hours are not perfectly flat.

**Four guaranteed properties:** P1 conservation (T-lock) · P2 monotone skill under added data ·
P3 exact/bit-exact nesting between tiers · P4 declared identifiability.

**Information budgets:** `Bud0` sensorless → `Bud1` (2 stations, Kandy's locked tier) →
`Bud2` (+6) → `Bud3` (+regional background) → `Bud4` (spatial network).
Package: `kandy_pm25/src/modular/` (68 tests). Spec: `kandy_pm25/docs/MODEL_SPECIFICATION.md`.

**The contribution is the declared budget with guaranteed nesting** — not the physics, not the ML.

---

## 🟢 The ladder was RE-VALIDATED (2026-08-23, F.84–F.87), then re-derived twice more

The scored `Bud0` had used **one of the three streams its budget admits**, inflating every gain
above it. Fixed in code (`require_covers()`), re-registered at https://osf.io/g6hqb/ **before**
re-running, rebuilt, and the bottom rung decomposed so each global stream is measured against a
monitor's worth:

| step | value |
|---|---:|
| `Bud0a→Bud0b` static geography | **10.8%** |
| `Bud0b→Bud0c` satellite level | **7.6%** |
| **`Bud0c→Bud1`** (+2 stations) | **17.8%** |
| `Bud1→Bud2` (+6 stations) | **0.1%** |
| `Bud2→Bud3` (+background) | **40.6%** |

🟢 Geography beats satellite — an *annual* level cannot touch the day-to-day variance daily RMSE
is made of. 🟢 A satellite level helps **coastal** cities **1.8×** more than inland (satellite
ALONE; the retired "4×" was the combined geography+satellite step under the satellite's name).

🔴 **A linear baseline does NOT reproduce the ladder (F.88).** On the 68-feature `Bud0c` Ridge
collapses and its first rung reads **50%** against HistGBM's 12%. The claim is *robust across
**non-linear** estimators*, never "even a linear model reproduces it". The useful reading: **the
measured value of a monitor depends on how well you exploit the free data.** 🟢 `Bud1→Bud2` ≈ 0
survives under every learner including Ridge and is the ladder's most estimator-robust result.

⚠ Numbers regenerate from `scripts/build_claims.py`; the manuscript build **fails** if prose and
data disagree. Registrations: `g6hqb` (re-validation), `bkpyr` (sub-grid/streams), `kx23c`
(chemistry), `2jyfg` (learned pattern). Full history: `docs/improvement_plan_2026-09-01.md`.

## 2. Numbers you may quote

| quantity | value | source |
|---|---|---|
| local fraction **f** | **0.4828** (≈0.48) | coherence cap, F.43 · `kandy_partition_v2.json` |
| ε-floor `eps0`, Kandy | **3.69** | F.57 (scales with mean accumulation) |
| T-lock accuracy | field runs **+0.39 to +0.56%** above anchor → say *"to within 0.6 per cent"* | 2026-08-14 build |
| basin annual means | 2019 **19.75** · 2020 **19.09** · 2021 **17.08** · 2022 **18.76** · 2023 **21.04** | `scalars_*.json` |
| pop-weighted exposure uplift | **+7%** over the area mean | `exposure_weighting.csv` |
| burden 2023 | **≈423/yr [231–616]**, 291 avoidable | `health_burden.py` |
| KOALA anchor | *"about 24.5"* — a valley-**FLOOR** point, never the basin mean | Senarathna 2024 |
| diurnal (FECT, normalised) | morning **07 = 1.41** · evening **18–19 = 1.25** · **midday trough 14 = 0.725** · night 00–04 = 0.865 | F.38 |
| exporter QA | reconstruction **0.0014** µg/m³ (tol 0.25) · wind parity **0.0005** m/s | 2026-08-22 |
| spatial ceiling | pooled **ρ ≈ 0.2–0.28** | F.56/F.58/F.59/F.61 |
| diurnal dilution exponent | **0.054** (vs 1.0 for pure inverse-BLH) | F.62 |

## 3. Numbers that are RETIRED — never quote these

| retired | why | use instead |
|---|---|---|
| **f = 0.244 / 25.3%** | superseded by the coherence cap | **f ≈ 0.48** |
| `additive_partition.csv` | stale; renamed `_v1_superseded` | `kandy_partition_v2.json` |
| `eps0 = 2.573` | pre-cap | **3.69** |
| **"Kandy ~90% vehicular"** | **REFUTED as a mass share (F.66)** | *traffic dominates local **timing**; it is a minority of local **mass*** |
| "deep night is the daily minimum" | wrong — **midday** is | F.38 |
| Spatial CV **R² = 0.911** | label-construction artefact | never report as a spatial result |
| Chandigarh spatial **−0.80** | N=4/N=5-era; current value is **NaN**, not a measured null | report "—" |
| pilot **2.9%** step gain | its `Bud0` had lat/lon and could identify the city | the 47-city ladder |
| Colombo as a background donor | **r 0.604** vs a **0.846** pooled / **0.822** matched benchmark | NBRO regional network |
| donor benchmark **0.923** | it was the single NEAREST pair (0.928), quoted as a median | **0.846** pooled, **0.822** distance-matched |
| "Colombo is the weakest of 20 donor pairs" | one pair at 285 km scores lower | **weakest at comparable separation** (0 of 8 below it) |
| panel spans **32 countries** | never re-derived after 47→48 cities | **29** |
| Kandy relief **800 m** | prose guess | **850 m**, from the DEM |
| interval re-centres to **91.5%** | recomputed against the current field | **92.2%** |
| B > T pre-cap **29.9% / 38.2%** | one quantity stated three ways in one document | **38.8%** of hours, **53.9%** of midday |
| **5** deep-tropical vs **32** temperate reference clusters | never computed; fresh OpenAQ census | **6 vs 65** — the disparity is LARGER, 10.8x |
| "night lights is the best spatial proxy, rho 0.34" | an 8-city figure | **built-up land cover at 2.4 km, rho 0.309** on 46 cities |

---

## 4. Evidence state, by axis

| axis | status | evidence |
|---|---|---|
| **level (daily)** | **strong** — but see §5 W11 | 47 cities, 32 countries, 4 bands; monotone under added data; background gain 75% reproduced by an independent network 89 km away (F.54) |
| **sub-daily shape** | **regime-limited** | transfers in the **deep tropics** (+25.8% vs flat, r 0.63, ~1 h phase error) — Kandy's regime — and **nowhere else**; pooled it is 5.5% *worse* than assuming no cycle (F.55) |
| **spatial pattern** | **ceiling measured** | ρ ≈ 0.2–0.28, unmoved by four attempts **plus a full LUR predictor set** (636 stations, roads at 5 radii): pooled ρ **+0.273 → +0.275** (F.61) |

**Why the spatial ceiling is real, six ways:** tiny within-city signal at 1 km (±10% at Kandy) ·
emission ≠ concentration vs ground truth · Track-S learned-pattern null · dynamic-transport null
(monitors are floor-sited) · AlphaEarth EO-embedding null · the LUR predictor set.

🟢 **And the CAUSE is now measured in Kandy itself (F.68).** A 25-site PM10 transect
(Elangasinghe & Shanthini 2008) records **110 → 4 µg/m³ over 300 m** inside one botanical
garden, and **R² = 0.82** against traffic intensity. Kandy's within-city signal is *enormous*,
but its decay length is **tens to hundreds of metres** — a 1 km cell integrates over exactly
that decay. **The pattern is not absent from the city; it is sub-grid by construction.** That is
a change-of-support statement, not a data-quality complaint, and it is the strongest form of
the ceiling claim. ⚠ It does **not** resolve W6: 82% of roadside PM10 *spatial variance* and
7.6% of ambient PM2.5 *mass* are different quantities.

🔴 **Scored against the model (F.69) — the first within-Kandy spatial test ever run.**
12 sites geocoded via OSM Overpass, model hours 11–13 LT to match the sampling window:

| | spread across the 12 sites |
|---|---|
| **observed** | 4 → 340 µg/m³ = **85×** |
| **model** | 20.72 → 25.43 µg/m³ = **1.23×** |

Two sites are the *same place at two microsites*: the garden entrance vs 300 m inside is
**27.5× observed, 1.000× modelled** (same pixel, 998 m); the school junction vs its grounds is
**4.6× observed, 1.000× modelled**. Rank ρ = +0.44 (n=12, p=0.16), **not significant**.
**The model's whole dynamic range across Kandy is smaller than the gap between two points
300 m apart in one garden.** The coarse ordering is right (rural = minimum, Katugastota =
near-maximum); the **amplitude is compressed ~70×**. State the limitation as a *definition*
problem, not a *skill* problem — and note the model is **not thereby wrong**: a 1 km areal mean
*should* sit mid-distribution against kerbside 3-h samples.

🔴 **`Bud4` is an unsupported design assumption**, not a validated rung. A spatial network does
NOT make `P` estimable: interpolation between a city's own stations is worse than assuming the
city is uniform (F.60), and a transferred LUR barely beats a population raster (F.61).
**Label it as such wherever it appears.**

---

## 4b. 🟢 The spatial rung was TESTED under pre-registration (2026-09-04, OSF `2jyfg`)

`Bud4` remains a **declared design assumption** — but it is now a tested one, which is a
different epistemic object from an untested one.

- **Benchmark**: best single globally available predictor = built-up land cover at 2.4 km,
  **rho 0.309** (46 cities, 630 stations).
- **Detection limit**: **0.130** at 80% power on that frame. **Registered bar: rho >= 0.44.**
- **Result**: learned pattern **0.286**; median paired delta **+0.022**, 25/46, p = 0.94.
  **L1 held — the bar is not cleared**, and per the registration this is reported as
  *undetectable at this power*, not as a modest success.
- 🟢 **The sixth null on within-city spatial pattern, and the FIRST with a detection limit
  stated in advance.** The previous five could only have detected effects of 0.65–0.96.
- 🟢 The gauge (P = N·softmax over cells) holds to **3.3e-16** across saturated, overflow-range
  and dead-constant fields. **A learned pattern can misplace material; it cannot create it.**
- 🟡 Skill is lower outside the temperate band (temperate +0.457 vs +0.225, p = 0.006; survives
  within-network de-confounding, p = 0.002) — but the **mechanism is not established** and that
  test was **not pre-registered**. Exploratory.
- ⚠ Also measured: **no engineered emission surface beats a single free raster** — not
  congestion-weighted road centrality, not a sector-weighted composite, not one carrying OSM
  industrial land use. Industrial land use IS a real predictor (it rescues Yichang, where the
  production traffic surface scores **−0.091**) but does not win overall.

---

## 5. Open questions

| | question | state |
|---|---|---|
| 🟡 **W6** | **Kandy's source mix — now resolved by GEOGRAPHY (F.71).** A 20-site study finds traffic **predominant in the urban core**, firewood **co-dominant there and dominant rurally**. So `emix vehic = 0.85` is refuted (F.66) *and* Katugastota's 7.6% bounds one suburban site, not the core. **Defensible core value: `vehic ≈ 0.5–0.6`, `burn ≈ 0.3–0.4`.** ⚠ PAHs are a combustion tracer, not mass — this licenses the ordering, not a percentage. | **narrowed, not closed** |
| 🔴 **W11** | **The level discrepancy.** Of four independent Kandy point records, **three sit below the model** (FECT Hantana ~+44%, FECT Akurana, RF-CNN LCS +28%) and **one matches** (NBRO, +0.7%/−2.6%). The three low ones are all LCS carrying a downward calibration; the one that matches has an **undocumented instrument**. | **OPEN** |
| 🟡 **generality** | **F.78's "the sensorless tier fails at Colombo" is RETRACTED as stated** — it was scored against the under-powered `Bud0` (F.84). Re-run with a spec-compliant `Bud0c` and Colombo's **real** geography (F.86/F.87): level bias **+31.3% → −4.4%**, seasonal r **0.55 → 0.93**, plain R² **−0.90 → +0.37**. 🔴 **What survives:** R² against a day-of-year climatology is still **−0.70**, so the model matches Colombo's level and season but adds **no day-to-day skill** — sea-breeze variation the seven drivers cannot resolve. A *located* deficiency, not a failure to transfer. | **narrowed** |
| ⚪ | `A_transport` is entirely unscored; the panel is 10 cities, **all valley/basin, zero coastal**; the panel does not bracket Kandy. | by design |

**Do not resolve W11 by picking the record that agrees.** State it as an open discrepancy.

### 🔴 The support-scaling ladder is CONFOUNDED — do NOT quote it as a scaling law (F.76)

Across its rungs, *support* and *siting design* moved together: Elangasinghe deliberately
sampled bus-terminus-to-botanical-garden extremes, the later rungs progressively did not. A
direct test on three dense networks finds temporal averaging collapses contrast by only
**1.2–1.7×**, not 69×. **Most of the apparent ladder is siting contrast, not averaging.**

🟢 **What survives is stronger.**
- **The paired-site test is unconfounded**: two microsites **300 m apart, both 3-h samples, one
  998 m pixel** — **27.5× observed, 1.000× modelled**. Support fixed, only location varies.
- **At matched support AND matched window the model is close to right** (F.77, window-matched
  2026-09-04): monthly p90/p10 **1.175** modelled against **1.26–1.51** observed across three
  cities at the same window. ⚠ A residual mismatch remains — observed spreads are across
  *stations*, the model's across *cells*.
- 🟢 **The amplitude question is CLOSED (F.77).** `s_exp` does not transfer and points the
  opposite way to expectation; the two candidate surfaces **bracket** observation. **`s_exp`
  stays at 1.0.** There is no amplitude crisis — what the model cannot do is *place* the
  contrast, which is the separate, now pre-registered and re-tested, ρ limit (§4b).

---

## 6. The independent Kandy checks (2026-08-22, F.64–F.67; pixel re-derived 2026-09-04)

The **first external checks on the Kandy field** in the project's history. Full detail: ledger
F.64–F.72.

- 🟢 **NBRO Kandy (KAN)**, 24-h, N=360/yr: obs **19.6** (2021) / **22.7** (2022); model at that
  pixel **19.74 / 22.11** → **+0.7% / −2.6%**. Genuinely out of sample because the *lift* above
  the basin mean (**15.6%** in 2021, **17.9%** in 2022) is imposed physics never fitted to any
  Kandy station. Station sits 0.33 km from its cell centre. ⚠ Instrument undocumented.
- 🟢 **W5 corroborated** — FECT Akurana **17.8** vs a BAM-anchored **~18–19** (Dhammapala 2022).
- ⚠ **BAM-calibrated LCS** (7.2731, 80.6117): **19.49** where the model says **25.01**. The two
  observation records disagree with each other by more than the model disagrees with either.
- 🟢 **W2 externally corroborated (F.72)** — Abeyratne & Ileperuma 2006 bin three gases by
  monsoon and find the maximum in the **NE**, not the SW where Sri Lanka's sources are.
  Long-range transport is **seasonal, not chronic**.
- ⚠ **Nirmani's meteorology is reanalysis**, not station data → their CBPF attribution is weak.
- ⚠ **Three sources say Kandy reads dirtier than Colombo** in the *gas* phase. A flag on **W11**,
  not a measurement.

---

## 7. Data situation

| route | state |
|---|---|
| 🔴 **CEA Kandy AQMS** | **FIRST AND ONLY route to a Kandy reference monitor — and now also the highest-value acquisition by measurement (F.92), ahead of NBRO.** Granted in principle 2026-08-12: hourly 2019→2026-05, PM2.5/PM10/gases plus full met incl. rain gauge and wind. Needs a letter on university letterhead to the DG + a signed R&D agreement. Gap 2021-07→2022-10. |
| ⚠ **NBRO regional background** | **DEMOTED for Kandy 2026-09-01 (F.92).** The "largest gain in the programme" is a POOLED number; in Kandy's own band local stations buy 21.9% and the background 8.5%. Still no free substitute (F.63) and the channel works — but second priority, not first. 🟢 **Confirmed on the honest satellite stream (F.96): local stations 43.7% vs background 10.3%, a 4.2× advantage.** |
| ⚫ **Torrington Park BAM-1020, Kandy** | **DEFUNCT (user, 2026-08-22).** The instrument that anchored the RF-CNN calibration and Dhammapala's correction is **no longer operating**. It is provenance for the published records, not a data route. |
| ⚠ **NBRO domain moved** | `nbro.gov.lk` → **`nbri.gov.lk`** (301). Update every NBRO URL in notes and letters. |
| **PDN Uni's own islandwide sensor network** | Unexploited, and it is the user's own institution. Chase internally. |
| ⚠ **CEA passive NO₂** | **DEMOTED** — will *not* fix `P_local` (the ceiling is information-limited). Its value is the `f` partition and activity tracing only. |
| **Mobile campaign** | 4–8 drive days per segment, and it still needs one fixed reference to anchor to. |

**In hand:** FECT (2 low-cost sensors, 2018–2026) · KOALA/NIFS 2019 · OpenAQ + CNEMC archives
(47-city panel) · GEE reanalysis and satellite stack · IMERG rain.

---

## 8. Hard rules, short list

- **Verify, never guess.** A doubt costs one search; a fabricated constant costs the result.
- **No degraded substitutes** for missing tools/data — acquire the right thing or say plainly why not.
- **Git-track the context files.** `CLAUDE.md`, `PROJECT.md`, `PROJECT_ARCHITECTURE.md`,
  `README.md`, this file and the ledger are versioned (gotcha #81 — CLAUDE.md was destroyed by a
  bad in-place write with no backup).
- **PINN inference always on Kaggle**, never locally.
- **Report per metric, never averaged across metrics** (gotcha #74).
- **A descriptor must exist for a target with NO local observations**, or it leaks (gotcha #73).
- **A model calibrated on a record cannot be scored against it** (gotcha #68).
- **Check `n` before believing a comparison** — thin overlap windows produced two false alarms in
  one session (F.63, F.64).
- **Never clip a field at 0 in a parquet** whose consumers derive anchors from it (gotcha #65).
- **A fix to a derived artefact belongs inside the code that derives it** (gotcha #70).
- **Verify outward-facing actions landed**: `git -C <path> rev-list --count origin/main..HEAD`
  must be 0 (gotcha #77).
- **Anchor framing:** KOALA/Senarathna/MAIAC are calibration anchors → "consistency anchors",
  never "validation". The NBRO and RF-CNN records **are** independent and may be called checks.

---

## 9. Where to go for more

| you want | read |
|---|---|
| session instructions, gotchas #1–81, current state | `CLAUDE.md` |
| **how** a component is built (maths, modules, invariants) | `PROJECT_ARCHITECTURE.md` |
| **what** came out (stage results, data inventory) | `PROJECT.md` |
| every finding, gate, prior and recorded error | `kandy_pm25/docs/model_reference/F_epistemic_ledger.md` (**F.1–F.67**) |
| what happened when | `memory/SESLOG.md` (reverse-chronological) |
| the formal model statement | `kandy_pm25/docs/MODEL_SPECIFICATION.md` |
| doc index — current vs historical | `kandy_pm25/docs/README.md` |
| the manuscript | `kandy_pm25/docs/paper/` — **edit `draft_s*.md`, never `manuscript_kandy.md`** |

**Publication view:** two papers, not one. **(A)** the methods / value-of-information paper —
47 cities, the budget ladder, three confounds caught by registered gates, two measured ceilings;
needs no Sri Lankan data, and is the strong one. **(B)** the Kandy application — weaker alone,
strong once A exists. The current 28-page manuscript sits between them and should be **split
rather than defended**.
