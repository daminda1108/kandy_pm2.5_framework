# CONTEXT — the load-bearing facts

**Read this first.** One page of what is true, what is refuted, and what is open.
Everything here is distilled from `CLAUDE.md`, `PROJECT.md`, the epistemic ledger
(`kandy_pm25/docs/model_reference/F_epistemic_ledger.md`) and `memory/SESLOG.md` — those stay
authoritative. **Keep this file under 250 lines.** Last updated **2026-09-06**.

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

**Two guarantees, one enforced mechanism, one discharged obligation.** ⚠ **Never write "four
 guaranteed properties".** P1 conservation (T-lock) and P3 exact/bit-exact nesting are
**guarantees**; P2 monotone skill under added data is an **enforced mechanism** (the estimator
shrinks back, so it cannot discover a stream is *harmful*, only unusable — F.97); P4 declared
identifiability is a **discharged obligation**.

**Information budgets:** `Bud0` sensorless → `Bud1` (2 stations — **Kandy's BUDGET, not a
measured optimum; saturation is at ONE, F.102**) → `Bud2` (stations **3–6**, not "3–8") →
`Bud3` (+regional background) → `Bud4` (spatial network).
Package: `kandy_pm25/src/modular/` (68 tests). Spec: `kandy_pm25/docs/MODEL_SPECIFICATION.md`.

**The contribution is the declared budget with guaranteed nesting** — not the physics, not the ML.

---

## 🟢 The ladder was RE-VALIDATED (2026-08-23, F.84–F.87), then re-derived twice more

The scored `Bud0` had used **one of the three streams its budget admits**, inflating every gain
above it. Fixed in code (`require_covers()`), re-registered at https://osf.io/g6hqb/ **before**
re-running, rebuilt, and the bottom rung decomposed so each global stream is measured against a
monitor's worth:

| step | value | 95% over CITIES (F.97) |
|---|---:|---|
| `Bud0a→Bud0b` static geography | **10.8%** | — |
| `Bud0b→Bud0c` satellite level | **7.6%** | — |
| **`Bud0c→Bud1`** (+2 stations) | **17.8%** | [4.6, 23.5] |
| `Bud1→Bud2` (+stations **3–6**) | **0.1%** | **[0.0, 0.9]** ← tightest |
| `Bud2→Bud3` (+background) | **40.6%** | [26.7, 45.2] |

🔴 **AND THE FIRST RUNG'S SIZE WAS KANDY'S BUDGET, NOT A MEASURED OPTIMUM (F.102).**
`SENSOR_PAIR` is literally *"<= 2 local low-cost sensors (the Kandy budget)"*. Sweeping k = 1..8:
**one station buys 17.02% [4.57, 21.83]; the second adds 0.01 pp paired**, and no count 2–8 beats
one by more than 0.15 pp. **Saturation is at ONE station.** Deep tropical agrees (one 20.01%,
second **+0.22 pp [0.00, +2.90]**, 6/13) ⚠ but both bands are **underpowered rather than null**.
🔴 The second rung is `pool[:6]` — stations **3 to 6**, not "three to eight"; the two
ranges have **opposite signs** (+0.75 vs −0.49 pp).

⚠ **Intervals are over CITIES, not city-days.** ⚠ Every gain is a **path-dependent marginal**:
reordering moves the background only 40.6→38.0% but moves monitors 3–6 from 0.13% to **2.81%**
(F.97). ⚠ A background is **only priceable given some local observation** — the "background
first" rung cannot be built. 🟢 Geography beats satellite because an *annual* level cannot touch
day-to-day variance; a satellite level helps **coastal** cities **1.8×** more than inland (the
retired "4×" was the combined geography+satellite step under the satellite's name).

🔴 **A linear baseline does NOT reproduce the ladder (F.88).** On the 68-feature `Bud0c` Ridge
collapses and its first rung reads **50%** against HistGBM's 12%. The claim is *robust across
**non-linear** estimators*, never "even a linear model reproduces it". **The measured value of a
monitor depends on how well you exploit the free data.** 🟢 `Bud1→Bud2` ≈ 0 survives under every
learner including Ridge — the ladder's most estimator-robust result.

⚠ Numbers regenerate from `scripts/build_claims.py`; the manuscript build **fails** if prose and
data disagree. Registrations: `g6hqb` (re-validation), `bkpyr` (sub-grid/streams), `kx23c`
(chemistry), `2jyfg` (learned pattern). Full history: `docs/improvement_plan_2026-09-01.md`.

## 2. Numbers you may quote

| quantity | value | source |
|---|---|---|
| local fraction **f** | **0.4828** (≈0.48); honest range across constraint forms **0.482–0.547** | coherence cap, F.43. ⚠ **A constrained decomposition, NOT observed source apportionment**, and **local increment ≠ locally emitted primary material** (no chemistry). **Never say "removing local sources would remove half the problem".** |
| ε-floor `eps0`, Kandy | **3.69** | F.57 (scales with mean accumulation) |
| T-lock accuracy | field runs **+0.39 to +0.56%** above anchor → say *"to within 0.6 per cent"* | 2026-08-14 build |
| basin annual means | 2019 **19.75** · 2020 **19.09** · 2021 **17.08** · 2022 **18.76** · 2023 **21.04** | `scalars_*.json` |
| pop-weighted exposure uplift | **+9%** over the area mean (21.0 → 23.0) | `exposure_weighting.csv`, regenerated 2026-09-04 (the retired figure was +7%, computed on a pre-rebuild field) |
| burden 2023 | **431/yr**, **response-function-conditional** interval [237–632], 300 avoidable | `health_burden.py`. ⚠ The interval carries ONLY the published CRF uncertainty: **not** the field, the population weighting or the W11 level discrepancy. Never call it a total uncertainty interval. |
| KOALA anchor | *"about 24.5"* — a valley-**FLOOR** point, never the basin mean | Senarathna 2024 |
| diurnal (FECT, normalised) | morning **07 = 1.41** · evening **18–19 = 1.25** · **midday trough 14 = 0.725** · night 00–04 = 0.865 | F.38 |
| exporter QA | reconstruction **0.0014** µg/m³ (tol 0.25) · wind parity **0.0005** m/s | 2026-08-22 |
| spatial ceiling | pooled **ρ ≈ 0.2–0.28** | F.56/F.58/F.59/F.61 |
| diurnal dilution exponent | **0.054** (vs 1.0 for pure inverse-BLH) | F.62 |

## 3. Numbers that are RETIRED — never quote these

| retired | why | use instead |
|---|---|---|
| **f = 0.244 / 25.3%** | superseded by the coherence cap | **f ≈ 0.48** |
| `eps0 = 2.573` | pre-cap | **3.69** |
| **"Kandy ~90% vehicular"** | **REFUTED as a mass share (F.66)** | *traffic dominates local **timing**; it is a minority of local **mass*** |
| "deep night is the daily minimum" | wrong — **midday** is | F.38 |
| Spatial CV **R² = 0.911** | label-construction artefact | never report as a spatial result |
| Chandigarh spatial **−0.80** | N=4/N=5-era; current value is **NaN**, not a measured null | report "—" |
| Colombo as a background donor | **r 0.604** vs a **0.846** pooled / **0.822** matched benchmark | NBRO regional network |
| donor benchmark **0.923** | it was the single NEAREST pair (0.928), quoted as a median | **0.846** pooled, **0.822** distance-matched |
| panel spans **32 countries** | never re-derived after 47→48 cities | **29** |
| B > T pre-cap **29.9% / 38.2%** | one quantity stated three ways in one document | **38.8%** of hours, **53.9%** of midday |
| **5** deep-tropical vs **32** temperate reference clusters | never computed; fresh OpenAQ census | **6 vs 65** — the disparity is LARGER, 10.8x |
| "night lights is the best spatial proxy, rho 0.34" | an 8-city figure | **built-up land cover at 2.4 km, rho 0.309** on 46 cities |
| background gain **75%** reproduced independently | pre-F.84 rung; re-run on corrected `Bud0c` | **73%** (F.54 re-run) |
| **F.92** deep-tropical inversion (21.9 vs 8.5, GHAP) | paired over cities it is **+3.6 pp [-14.3, +36.3]**, a coin flip at 54% of cities | **F.96/MAIAC only: +33.3 pp [+7.0, +50.1]**, 77% of cities |
| "removing every local source removes half the problem" | no chemistry, so **local increment is not locally emitted primary material** | *the decomposition ASSIGNS ~0.48 to a local increment*; honest range **0.482-0.547** |
| "a reference monitor is worth 43.7%" | the ladder measured **two LOW-COST sensors** | local > regional in this band; reference grade is a SEPARATE design argument |
| monitors 3-8 buy **0.1%**, full stop | order-dependent: **2.81%** with a background present | small under both orders; **never a fixed quantity** |
| **"monitors three to eight"** | the code is `pool[:6]`; the two ranges have OPPOSITE signs (+0.75 vs -0.49 pp) | **stations three to six** (F.102) |
| **"two sensors is where the ladder saturates"** | 2 was the Kandy BUDGET; the second station adds **0.01 pp** | **saturation is at ONE station** (F.102) |
| **"deliberate siting recovers pattern a convenience network cannot"** | 43 cities, 601 stations, **paired -0.044 [-0.095, +0.118]**, winning 19/43. The +0.114 difference-of-medians points the other way | **undetectable**; the LUR gap is INFORMATION, not siting (F.103) |
| **f sensitivity quoted as one range** | there are **THREE** axes: anchored years **0.466-0.501** · `F_min` sweep **0.482-0.509** · **window form 0.489-0.547** | name the axis with the range (F.108) |
| **intervals bootstrapped over CITIES** | cities share networks; 11 of 48 are one — clustering widens every interval by 1.34-1.97x | **cluster-bootstrap intervals** (F.104); no conclusion changes |
| **the model's own `s_rep`** | estimated from the FIELD's neighbourhood gradient; instruments sharing a cell disagree **2.6x** more on the panel and **17x** more at Kandy | take it from **co-located instruments** (F.106) |
| **"a learned pattern did not beat the benchmark"** (one family) | 7 admissible families tested; best is **+0.018** vs a 0.130 limit | **no admissible family beats it** (F.105) |
| **"the campaign will test the spatial ceiling"** | dead twice over: it cannot DETECT a siting effect (F.100, needs 96-304 sites) and there is probably none TO detect (F.103) | the campaign settles the **level**, the **within-cell ratio** and the **drainage sign** |

---

## 4. Evidence state, by axis

| axis | status | evidence |
|---|---|---|
| **level (daily)** | **strong** — but see §5 W11 | 48 cities, 29 countries, 4 bands; monotone under added data; background gain **73%** reproduced by an independent network at a median 89 km (F.54 re-run 2026-09-05; **bounds the same-network artefact from above, does not measure it**) |
| **sub-daily shape** | **regime-limited** | transfers in the **deep tropics** (+25.8% vs flat, r 0.63, ~1 h phase error) — Kandy's regime — and **nowhere else**; pooled it is 5.5% *worse* than assuming no cycle (F.55) |
| **spatial pattern** | **ceiling measured** | ρ ≈ 0.2–0.28, unmoved by four attempts **plus a full LUR predictor set** (636 stations, roads at 5 radii): pooled ρ **+0.273 → +0.275** (F.61) |

**Why the spatial ceiling is real, SEVEN ways:** tiny within-city signal at 1 km (±10% at
Kandy) · emission ≠ concentration vs ground truth · Track-S learned-pattern null ·
dynamic-transport null (monitors floor-sited) · AlphaEarth EO-embedding null · a full LUR
predictor set moving pooled ρ **+0.273 → +0.275** (F.61) · 🆕 **deliberate siting failing to beat
convenience siting on 43 dense-network cities (F.103)** — which removes the last "our sample is
the problem" explanation.

🟢 **The CAUSE is measured in Kandy itself (F.68).** A 25-site PM10 transect (Elangasinghe &
Shanthini 2008) records **110 → 4 µg/m³ over 300 m** inside one botanical garden, R² **0.82**
against traffic. The signal is *enormous*; its decay length is **tens to hundreds of metres** and
a 1 km cell integrates over exactly that. **Sub-grid by construction** — a change-of-support
statement, not a data-quality complaint. ⚠ It does **not** resolve W6 (roadside PM10 *variance*
≠ ambient PM2.5 *mass*).

🔴 **Scored against the model (F.69), the first within-Kandy spatial test ever run.** 12 sites,
11–13 LT: observed spread **85×**, model **1.23×**; paired sites 300 m apart are **27.5× observed,
1.000× modelled** (same pixel). Rank ρ +0.44 (n=12, p=0.16), **not significant**. ⚠ A second
apparent pair carried **one coordinate for both sites** and is withdrawn.

🔴 **`Bud4` is an unsupported design assumption**, not a validated rung — but a **tested** one
(2026-09-04, OSF [`2jyfg`](https://osf.io/2jyfg/)), which is a different epistemic object.
Interpolation between a city's own stations is worse than assuming the city uniform (F.60) and a
transferred LUR barely beats a population raster (F.61). Benchmark = best single free predictor,
**built-up land cover at 2.4 km, ρ 0.309** (46 cities, 630 stations); detection limit **0.130**;
registered bar **0.44**; learned pattern reached **0.286** (Δ +0.022, 25/46, p = 0.94) → **L1
held**, reported as *undetectable at this power*. **Sixth null on within-city spatial pattern and
the first with a detection limit stated in advance** — the previous five could only have detected
0.65–0.96. 🟢 Gauge exact to **3.3e-16**: a learned pattern can *misplace* material, never *create* it.
🟡 The band difference is real (temperate +0.457 vs +0.225, p = 0.006) but the mechanism is **not
established** and the test was **not pre-registered** — exploratory. ⚠ **No engineered emission
surface beats a single free raster**, including one carrying OSM industrial land use (a real
predictor that rescues Yichang, where the traffic surface scores **−0.091**).
**Label `Bud4` as a declared assumption wherever it appears.**

---

## 5. Open questions

| | question | state |
|---|---|---|
| 🟡 **W6** | **Kandy's source mix — now resolved by GEOGRAPHY (F.71).** A 20-site study finds traffic **predominant in the urban core**, firewood **co-dominant there and dominant rurally**. So `emix vehic = 0.85` is refuted (F.66) *and* Katugastota's 7.6% bounds one suburban site, not the core. **Defensible core value: `vehic ≈ 0.5–0.6`, `burn ≈ 0.3–0.4`.** ⚠ PAHs are a combustion tracer, not mass — this licenses the ordering, not a percentage. | **narrowed, not closed** |
| 🔴 **W11** | **The level discrepancy.** Of four independent Kandy point records, **three sit below the model** (FECT Hantana ~+44%, FECT Akurana, RF-CNN LCS +28%) and **one matches** (NBRO, +0.7%/−2.6%). The three low ones are all LCS carrying a downward calibration; the one that matches has an **undocumented instrument**. | **OPEN** |
| 🟡 **generality** | **F.78's "the sensorless tier fails at Colombo" is RETRACTED as stated** — it was scored against the under-powered `Bud0` (F.84). Re-run with a spec-compliant `Bud0c` and Colombo's **real** geography (F.86/F.87): level bias **+31.3% → −4.4%**, seasonal r **0.55 → 0.93**, plain R² **−0.90 → +0.37**. 🔴 **What survives:** R² against a day-of-year climatology is still **−0.70**, so the model matches Colombo's level and season but adds **no day-to-day skill** — sea-breeze variation the seven drivers cannot resolve. A *located* deficiency, not a failure to transfer. | **narrowed** |
| ⚪ | `A_transport` is entirely unscored; the panel is 10 cities, **all valley/basin, zero coastal**; the panel does not bracket Kandy. | by design |

**Do not resolve W11 by picking the record that agrees.** State it as an open discrepancy.

### 🔴 The support-scaling ladder is CONFOUNDED — never quote it as a scaling law (F.76)

Support and siting design moved together across its rungs; a direct test on three dense networks
finds temporal averaging collapses contrast by only **1.2–1.7×**, not 69×. **Most of the apparent
ladder is siting contrast, not averaging.** What survives is stronger: the **paired-site test is
unconfounded** (27.5× observed, 1.000× modelled), and **at matched support AND window the model
is close to right** (F.77: monthly p90/p10 **1.175** modelled vs **1.26–1.51** observed; ⚠ the
observed spreads are across *stations*, the model's across *cells*). 🟢 **The amplitude question
is CLOSED** — `s_exp` stays at 1.0. There is no amplitude crisis; what the model cannot do is
*place* the contrast.

### 🟢 Chemistry: ANSWERED, and it is not a fourth pillar (2026-09-06, F.98)

Deepened by the tractable route — species-resolved testing against reanalysis already on disk,
**no CTM**. Three strands, one usable:

- 🟢 **Fréchet bounds** put the locally emitted primary share at Kandy between **9.1% and 48.3%**.
  This replaces the withdrawn *"removing local sources removes half the problem"* — and shows
  that claim sat at the **top** of the admissible range.
- 🔴 **Registered null.** All three confirmatory hypotheses **undetectable** (largest partial ρ
  **0.135** vs MDE **0.431**). The deviation is the finding: the exploratory signal that motivated
  it (pooled 46 cities **+0.388**, p = 0.008) **survives in neither group** — banded 35 **+0.093**,
  CNEMC 11 **+0.036**. **A network effect wearing a chemical variable's name.**
- ⚠ **INVALID, neither held nor refuted.** The species partition ranks **dust 0.806 and sea salt
  0.645 above black carbon 0.387**; an inland valley has no local sea-salt source, so the
  estimator measures episodic variability, not origin. **Never report the reversal.**

**Chemistry is a supporting discipline with one measured bound.** The thesis says so.

### 🔴 The Kandy campaign — designed, costed, registered, and its spatial premise refuted (F.99–F.103)

**35 sites, 5 strata**, over an emission surface spanning **65×** p10→p90 of which the existing
records occupy only the **61st–100th percentile**. Registered blind at **OSF [`ad3py`](https://osf.io/ad3py/)**
before deployment. Plan: `kandy_pm25/docs/sensor_placement_plan_2026-09-05.md`; thesis §9.7.

🔴 **What the campaign can no longer claim.** Its spatial ambition is dead twice over:
**F.100** — beating the 0.309 benchmark with 18 fitting sites needs a gain of +0.30 to +0.47 while
the 46-city panel resolved **0.130**, and matching it in one city needs **96–304 sites**;
**F.103** — on 43 dense-network cities deliberate siting does **not** measurably beat convenience
siting (**paired −0.044 [−0.095, +0.118]**, 19/43). **The LUR gap is information, not siting.**

🟢 **What it still settles, well powered:** the **level** (the anchor alone); the
**within-cell ratio**, which resolves to **1.044 in seven days** against competing predictions of
1.58 and 27.5; and the **drainage sign test**, whose unit is the night (63.1% over 90).

**Cost: 19,900–49,900 USD** — instruments 9,900, reference anchor 10,000–40,000. ⚠ Mounting,
power, **import duty**, labour and servicing carry **empty unit prices**; none is published for
Sri Lanka. 🔴 **The largest line may be a letter** — CEA has granted access in principle.
🔴 **Re-scoping is not worth doing:** trimming the design stratum 12→10 saves **450 USD**,
under 3%. ⚠ D-efficiency **ranks the wrong designs first** (road-sited 0.70, existing 0.88,
proposal 0.35) — it endorses the two designs already known to produce nulls.

**The open decision is what the campaign CLAIMS, not what it costs.**

---

## 6. The independent Kandy checks (F.64–F.72; pixel re-derived 2026-09-04)

The **first external checks on the Kandy field** in the project's history.

- 🟢 **NBRO Kandy (KAN)**, 24-h, N=360/yr: obs **19.6** (2021) / **22.7** (2022) vs model at that
  pixel **19.74 / 22.11** → **+0.7% / −2.6%**. Out of sample because the *lift* above the basin
  mean (15.6% / 17.9%) is imposed physics never fitted to a Kandy station. ⚠ Instrument
  undocumented.
- 🟢 **W5 corroborated** — FECT Akurana **17.8** vs a BAM-anchored **~18–19** (Dhammapala 2022).
- ⚠ **BAM-calibrated LCS** (7.2731, 80.6117): **19.49** where the model says **25.01**. *The two
  observation records disagree with each other by more than the model disagrees with either.*
- 🟢 **W2 externally corroborated (F.72)** — Abeyratne & Ileperuma 2006 find the gas-phase
  maximum in the **NE** monsoon, not the SW where Sri Lanka's own sources are.
- ⚠ Nirmani's meteorology is reanalysis → their CBPF attribution is weak. ⚠ Three sources say
  Kandy reads dirtier than Colombo in the *gas* phase: a flag on **W11**, not a measurement.

---

## 7. Data situation

| route | state |
|---|---|
| 🔴 **CEA Kandy AQMS** | **FIRST AND ONLY route to a Kandy reference monitor — and now also the highest-value acquisition by measurement (F.92), ahead of NBRO.** Granted in principle 2026-08-12: hourly 2019→2026-05, PM2.5/PM10/gases plus full met incl. rain gauge and wind. Needs a letter on university letterhead to the DG + a signed R&D agreement. Gap 2021-07→2022-10. |
| ⚠ **NBRO regional background** | **DEMOTED for Kandy (F.92 → F.96 → F.97).** The "largest gain in the programme" is a POOLED number; in Kandy's band local stations win. 🔴 **F.97: quote the MAIAC version only.** Paired over cities the advantage is **+33.3 pp [+7.0, +50.1]**, 77% of cities, on raw MAIAC; on fused GHAP it is **+3.6 pp [−14.3, +36.3]**, a coin flip. **F.92's numbers alone did not support the recommendation.** Still no free substitute (F.63), the channel works, second priority. 🟢 A donor network at ~89 km recovers **73%** of the background rung (F.54 re-run), so the rung is real regional information. |
| ⚫ **Torrington Park BAM-1020, Kandy** | **DEFUNCT (user, 2026-08-22).** The instrument that anchored the RF-CNN calibration and Dhammapala's correction is **no longer operating**. It is provenance for the published records, not a data route. |
| ⚠ **NBRO domain moved** | `nbro.gov.lk` → **`nbri.gov.lk`** (301). Update every NBRO URL in notes and letters. |
| **PDN Uni's own islandwide sensor network** | Unexploited, and it is the user's own institution. Chase internally. |
| ⚠ **CEA passive NO₂** | **DEMOTED** — will *not* fix `P_local` (the ceiling is information-limited). Its value is the `f` partition and activity tracing only. |
| **Mobile campaign** | 4–8 drive days per segment, and it still needs one fixed reference to anchor to. |

**In hand:** FECT (2 low-cost sensors, 2018–2026) · KOALA/NIFS 2019 · OpenAQ + CNEMC archives
(48-city panel) · GEE reanalysis and satellite stack · IMERG rain.

---

## 8. Hard rules, short list

- **Verify, never guess.** A doubt costs one search; a fabricated constant costs the result.
- **No degraded substitutes** for missing tools or data — acquire the right thing, or say plainly why not.
- **Pair within unit.** Any A-vs-B comparison across the panel is the median of the *within-city*
  difference, bootstrapped over cities. A difference of medians is not an effect (#91) — it went
  the wrong way twice in one session. And **report per metric, never averaged across metrics** (#74).
- **Read a tier's size out of the code** before writing it in prose (#92).
- **Git-track the context files** — `CLAUDE.md`, `PROJECT.md`, `PROJECT_ARCHITECTURE.md`,
  `README.md`, this file, the ledger (#81: CLAUDE.md was destroyed by a bad in-place write).
- **A descriptor must exist for a target with NO local observations**, or it leaks (#73); **a
  model calibrated on a record cannot be scored against it** (#68).
- **Check `n` before believing a comparison** — thin overlap produced two false alarms (F.63/F.64).
- **A fix to a derived artefact belongs inside the code that derives it** (#70), and **a build
  that CONSUMES a derived artefact must REGENERATE it** — the gate checks a table's numbers, not
  that the table is current (#90). **Never clip a field at 0 in a parquet** whose consumers derive
  anchors from it (#65).
- **Verify outward-facing actions landed** — `git -C <path> rev-list --count origin/main..HEAD`
  must be 0 (#77); and **an HTTP error is not evidence nothing happened** (#89).
- **Anchor framing:** KOALA/Senarathna/MAIAC are calibration anchors → "consistency anchors",
  never "validation". The NBRO and RF-CNN records **are** independent and may be called checks.
- **PINN inference always on Kaggle**, never locally.

---

## 9. Where to go for more

| you want | read |
|---|---|
| session instructions, gotchas #1–92, current state | `CLAUDE.md` |
| **how** a component is built (maths, modules, invariants) | `PROJECT_ARCHITECTURE.md` |
| **what** came out (stage results, data inventory) | `PROJECT.md` |
| every finding, gate, prior and recorded error | `kandy_pm25/docs/model_reference/F_epistemic_ledger.md` (**F.1–F.103**) |
| what happened when | `memory/SESLOG.md` (reverse-chronological) |
| the formal model statement | `kandy_pm25/docs/MODEL_SPECIFICATION.md` |
| doc index — current vs historical | `kandy_pm25/docs/README.md` |
| the manuscript | `kandy_pm25/docs/paper/` — **edit `draft_s*.md`, never `manuscript_kandy.md`** |
| **the thesis** | `#writing/` — **edit `thesis/chapters/ch*.md`, never `build/thesis.md`** |

**Publication view:** two papers, not one — the methods/VoI paper (strong, needs no Sri
Lankan data) and the Kandy application (weaker alone). See `CLAUDE.md` §1b.
