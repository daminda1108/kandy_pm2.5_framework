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
| Colombo as a background donor | **r 0.60** vs a 0.92 benchmark (F.63) | NBRO regional network |

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

## 5. Open questions

| | question | state |
|---|---|---|
| 🔴 **W6** | **Kandy's source mix.** PMF at Katugastota: **traffic 7.6%, biomass burning 14.1%** of PM2.5 mass (Seneviratne 2017, 2012–14). `emix vehic = 0.85`. F.23 measured the vehicular **timing** (3.67× rush ratio) and explicitly did not bound the magnitude. | **REOPEN** |
| 🔴 **W11** | **The level discrepancy.** Of four independent Kandy point records, **three sit below the model** (FECT Hantana ~+44%, FECT Akurana, RF-CNN LCS +28%) and **one matches** (NBRO, +0.7%/−2.6%). The three low ones are all LCS carrying a downward calibration; the one that matches has an **undocumented instrument**. | **OPEN** |
| ⚪ | `A_transport` is entirely unscored; the panel is 10 cities, **all valley/basin, zero coastal**; the panel does not bracket Kandy. | by design |

**Do not resolve W11 by picking the record that agrees.** State it as an open discrepancy.

---

## 6. The independent Kandy checks (2026-08-22, F.64–F.67)

Three papers produced the **first external checks on the Kandy field** in the project's history.

- 🟢 **W5 corroborated** — FECT Akurana full-record mean **17.8** vs a BAM-anchored published
  study's **~18–19** (Dhammapala 2022). First reference-grade corroboration the project has had.
- 🟢 **NBRO Kandy (KAN)**, 24-h, N=360/yr: obs **19.6** (2021) / **22.7** (2022);
  model at that pixel **19.74 / 22.11**. ⚠ Station coordinate is *assumed* (NBRO "Kandy 1");
  ⚠ instrument undocumented; ⚠ two numbers, no daily r.
- ⚠ **BAM-calibrated LCS at Kandy** (7.2731, 80.6117): **19.49** where the model says **25.01**.
  The two observation records disagree with each other by more than the model disagrees with
  either — the model puts the two sites within 2–3%.
- ⚠ **Nirmani's meteorology is Open-Meteo/ERA5 reanalysis**, not station data → their Kandy CBPF
  source attribution is weak evidence (a 0.1° wind cannot resolve valley flow).

---

## 7. Data situation

| route | state |
|---|---|
| 🔴 **CEA Kandy AQMS** | **FIRST AND ONLY route to a Kandy reference monitor.** Granted in principle 2026-08-12: hourly 2019→2026-05, PM2.5/PM10/gases plus full met incl. rain gauge and wind. Needs a letter on university letterhead to the DG + a signed R&D agreement. Gap 2021-07→2022-10. |
| 🔴 **NBRO regional background** | The background rung is the largest measured gain in the programme, and it has **no free substitute**. NBRO already supplied the F.65 series, so the channel works. |
| ⚫ **Torrington Park BAM-1020, Kandy** | **DEFUNCT (user, 2026-08-22).** The instrument that anchored the RF-CNN calibration and Dhammapala's correction is **no longer operating**. It is provenance for the published records, not a data route. |
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
