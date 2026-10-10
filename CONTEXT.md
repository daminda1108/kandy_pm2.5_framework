# CONTEXT — the load-bearing facts

**Read this first.** One page of what is true, what is refuted, and what is open.
Everything here is distilled from `CLAUDE.md`, `PROJECT.md`, the epistemic ledger
(`kandy_pm25/docs/model_reference/F_epistemic_ledger.md`) and `memory/SESLOG.md` — those stay
authoritative. **Keep this file under 250 lines.** Last updated **2026-10-06** (external review, F.124).

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

**Two guarantees (P1 T-lock, P3 exact nesting), one enforced mechanism (P2 monotone skill: shrinkage
means a stream can prove unusable, never harmful, F.97), one discharged obligation (P4 identifiability).**
Never write "four guaranteed properties".

**Information budgets:** `Bud0` sensorless → `Bud1` (2 stations, Kandy's budget) → `Bud2` (stations
**3–6**, not "3–8") → `Bud3` (+background) → `Bud4` (spatial network). A second station adds **+0.93**
over one; stations 3–8 about 1.3 (F.116 addendum).
Package: `kandy_pm25/src/modular/` (68 tests). Spec: `kandy_pm25/docs/MODEL_SPECIFICATION.md`.

**The contribution is the declared budget with guaranteed nesting** — not the physics, not the ML.

---

## 🔴 READ FIRST — external review 2026-10-06 (F.124)
The registered rungs were **not like for like**: first two / six stations enter only as an intercept+slope calibration of
Bud0, the background enters with its **same-day** reading. Put on equal terms (`ladder_v2_review.py`, parity 2.8e-14):
first two same-day **+58.8 % [44.9, 69.0]**, background +57.7, background − first two **−0.22 [−0.60, +0.04]** (n 100).
**Never say a background is worth more than local stations.** H1–H5 are quoted "as constructed". The robust result is
**same-day observation ≈ +58 % vs calibration-only ≈ +9–14 %**; kind does not matter; on full networks a ~10-station background adds +2.5 [1.1, 3.7] over two same-day stations (count).
Spatial curve: X5 interval was a bug; only **3/23** cities cross after Holm (not 15/23); tropical − other −0.22
[−0.45, +0.02]; detection limit 0.35/0.51; GHAP ≈ built-up raster. f: **0.433–0.492** across cap choices.
Plan + log: `kandy_pm25/docs/review_remediation_plan_2026-10-06.md`.
Registry (`#writing/registrations.json`): **17 lodged, 14 run, 105 predictions: 66 held, 23 refuted, 6 not tested, 10
two-sided/descriptive**; `mhgna`, `fu59b` awaiting OSF approval.

## 🔬 Second review (2026-10-10, F.126, exploratory)
Humidity scenario: f 0.483→0.488; morning-peak/midday 1.93→1.68; **night/midday 1.16→0.95** (calibration-dependent); daily r and
level unchanged. Dispersion on identical sites: raw 0.371, dispersed 0.274, built-up 0.393 → dispersion is NOT validated.
Quote f as 0.483 (0.433–0.492 cap choices; 0.547 at 48 h) — a decomposition property, never a confidence interval.
**Burden withdrawn** (no number; method only — never quote 431/300). Kandy s_rep factor 16.9 is confounded, NOT a lower
bound. Dec 2022 = model-inferred regional episode.

## 🔬 The deployed model on the ladder (2026-10-10, F.125, exploratory)
Kandy's T(t) chain (daily, 2 anchor stations, VanD level) scored on the ladder, 104 cities: **reconstruction +32.7 %
[25.9, 41.9]** vs the sensorless learner (+17.0 pts over calibration-only; −22 pts short of same-day), r 0.86;
**prospective +4.8 [−2.8, 25.8]** (no better than calibration), r 0.67. Level +8 / +18 % high; 90 % interval covers 0.70.
Thesis A is now built on three validation lines (Kandy records · 10-city transfer · this rung). Never quote the
reconstruction gain as skill on days the sensors did not observe.

## 🟢 The ladder: CONFIRMED on 72 fresh cities (2026-09-28, OSF `ueyfr`, F.117; discovery F.115/F.116) — ordering superseded by F.124

**Status.** Ladder v2 (frozen `e6b744b`; 21 station splits, 5 learner seeds, cross-fitted shrinkage,
urban-centre geography, ≥ 18 h station-days, cluster bootstrap) was scored ONCE on 76 fresh cities
registered before their PM2.5 was retrieved; 72 scored (4 excluded by rule). Results
`kandy_pm25/docs/confirmation_results_2026-09-28.md`. **Quote the CONFIRMATION numbers; discovery
(47 cities) is exploratory.**

| step (reconstruction, RMSE, median [cluster 95 %]) | confirmation | verdict | discovery |
|---|---|---|---|
| first two stations (H1) | **+8.5 % [3.1, 25.1]** | supported | +21.8 [10.5, 52.9] |
| stations 3–6 (H2) | **+0.22 [0.12, 0.50]** | supported (inside ±1) | +0.54 |
| same-network background (H3) | **+41.1 % [26.8, 62.8]** | supported | +34.4 |
| background minus first two (H4) | **+24.6 [4.1, 47.8]** | **ordering: background > first two** | +4.8 [−23.6, +52.1] |
| the same, exceedance loss (H5) | **+59.3 [33.9, 67.7]** | supported | +34.5 |
| latitude slope (M1) | +0.53 /° [−1.79, +1.49] | **undetectable** (4 low-latitude cities) | +1.09 |

Prospective arm reproduces every verdict. First stations do nothing detectable on high days or for
exceedances (tail −2.7 [−10.3, +3.7]). Exploratory: H4 holds without CNEMC (OpenAQ only +11.5 [1.4, 33.3]).
**Scope:** 50/72 temperate, 63/76 reference-dominated. **The deep-tropical inversion (discovery −27.4
[−47.8, +11.8], n 12) stays EXPLORATORY** — no public data can confirm it; never quote "4.2×".
⚠ The background rung is the **daily 10th percentile of the same network's other stations** — never call it a
rural or regional monitor. An independent network 30–300 km away recovers **71 % [44, 82]** of it per city.
🟢 **Robust to baseline (`b379r`, F.118: +CAMS/terrain/fires/NO2/rain, Bud0 +13 %, all verdicts survive) and learner (`jea58`, F.120: TabPFN/GRU/physics, all 12 directional verdicts hold, none beats HGB; H4 unresolved under TabPFN).** 🟢 **Robust to the station cap (`mhgna`, F.122, 2026-10-05): full networks (median 17 stations, 75 cities) — every verdict holds; background +46.0, background − first two +32.0 [11.6, 50.5].**

## 2. Numbers you may quote

| quantity | value | source |
|---|---|---|
| local fraction **f** | **≈0.48** (production); **0.433–0.492 across cap day/statistic choices** (F.124) and **0.489–0.547** across window forms — a bound under the coherence cap, not identified by data | coherence cap, F.43. ⚠ **A constrained decomposition, NOT observed source apportionment**, and **local increment ≠ locally emitted primary material** (no chemistry). **Never say "removing local sources would remove half the problem".** |
| ε-floor `eps0`, Kandy | **3.69** | F.57 (scales with mean accumulation) |
| T-lock accuracy | field runs **+0.39 to +0.56%** above anchor → say *"to within 0.6 per cent"* | 2026-08-14 build |
| basin annual means | 2019 **19.75** · 2020 **19.09** · 2021 **17.08** · 2022 **18.76** · 2023 **21.04** | `scalars_*.json` |
| pop-weighted exposure uplift | **+9%** over the area mean (21.0 → 23.0) | `exposure_weighting.csv`, regenerated 2026-09-04 (the retired figure was +7%, computed on a pre-rebuild field) |
| burden 2023 | **431/yr** [237–632], 300 avoidable — **illustrative** | `health_burden.py`. ⚠ **Corrected 2026-10-07:** the interval is the field's q05/q95 exposure through the CENTRAL GEMM (`health_burden.py:91–104`), so it carries **no** response-function uncertainty, nor population, W11 or structural uncertainty; GEMM is also applied to all ages (should be 25+). Never call it a total uncertainty interval. |
| KOALA anchor | *"about 24.5"* — a valley-**FLOOR** point, never the basin mean | Senarathna 2024 |
| diurnal (FECT, normalised) | morning **07 = 1.41** · evening **18–19 = 1.25** · **midday trough 14 = 0.725** · night 00–04 = 0.865 | F.38 |
| exporter QA | reconstruction **0.0014** µg/m³ (tol 0.25) · wind parity **0.0005** m/s | 2026-08-22 |
| spatial ceiling | pooled **ρ ≈ 0.2–0.28** | F.56/F.58/F.59/F.61 |
| diurnal dilution exponent | **0.054** (vs 1.0 for pure inverse-BLH) | F.62 |
| Kandy population | **98,828** residents in the Kandy MC (2012 census, `DCS2012Census`); **nearly 389,000 weekday commuters**, more than twice the residents (World Bank PID PIDA28437, 2020, `WorldBank2020KMTT`). ⚠ **422,314** is the WorldPop count of the **15 km domain**, not the city. Never ">150,000 + 100,000 a day" (no census basis) or "about four hundred thousand" (unsourced) | fact-check 2026-09-19 |
| WHO 2021 interim targets, 24 h | IT-1 **75**, IT-2 **50**, AQG **15** µg/m³ (a 55 line is NOT IT-1) | 2026-09-19 |

## 3. Numbers that are RETIRED — never quote these

| retired | why | use instead |
|---|---|---|
| **"background outranks the first two stations"** (H4 +24.6, H5 +59.3) | rung construction: calibration-only vs same-day (F.124) | like for like −0.22 [−0.60, +0.04]; quote H4/H5 "as constructed" |
| **"cities split: 15/23 cross the raster"**, **"tropical inside the temperate envelope"**, X5 **[0.00, 0.00]**, limit **0.24/0.28** | crossing labels within sampling noise; envelope rule uninformative; pooling bug; SD assumed | **3/23** after Holm; tropical − other −0.22 [−0.45, +0.02]; per-k X5; limit **0.35/0.51** (F.124) |
| **T(t) skill "R² 0.581"** | that is the LAGGED blend (observed-PM lags), a nowcaster | deployed lag-free T(t): **R² 0.33**, daily r 0.69, monthly r 0.89 (review 2026-10-07) |
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
| background gain **75%** / **73%** reproduced independently | 75 % pre-F.84; 73 % was a RATIO OF MEDIANS | **71 % [44, 82]** per city, paired (F.115) |
| **F.96** "GHAP deflates the value of a local station by about half" | v2 paired MAIAC − GHAP, first two: **+2.3 [−0.6, +16.9]** (65 % of cities); excludes neither sign | GHAP **tilts the ordering toward the background** (−5.5 [−16.8, −1.5]); exploratory (F.117 addendum) |
| **F.92/F.96** deep-tropical inversion, **+33.3 [+7.0, +50.1]** and "4.2×" | ONE station split and ONE learner seed; over 20 splits the interval excludes 0 in 3/20; under ladder v2 **−27.4 [−47.8, +11.8]** and the sign reverses prospectively (F.115/F.116) | **directional, exploratory**; never "robust" |
| "removing every local source removes half the problem" | no chemistry, so **local increment is not locally emitted primary material** | *the decomposition ASSIGNS ~0.48 to a local increment*; honest range **0.482-0.547** |
| "a reference monitor is worth 43.7%" | the ladder measured **two LOW-COST sensors** | local > regional in this band; reference grade is a SEPARATE design argument |
| monitors 3-8 buy **0.1%**, full stop | order-dependent: **2.97%** with a background present (F.113) | small under both orders; **never a fixed quantity** |
| **"monitors three to eight"** | the code is `pool[:6]` (F.102) | **stations three to six** |
| **"two sensors is where the ladder saturates"** / **"saturation is at ONE station"** | 2 was the Kandy budget; v1 put the second station at 0.01–0.09 pp because in-sample shrinkage zeroed it | v2: one station **+14.5 %**, a second **+0.93 [0.37, 1.50]** paired, 3–8 add ~1.3 over one (F.116 addendum) |
| **"deliberate siting recovers pattern a convenience network cannot"** | 43 cities, 601 stations, **paired -0.044 [-0.095, +0.118]**, winning 19/43. The +0.114 difference-of-medians points the other way | **undetectable**; the LUR gap is INFORMATION, not siting (F.103) |
| **"precipitation is an unmeasured gap"** | registered and tested: bottom rung **-1.04% [-5.5, +4.3]**, gains above paired **-0.30 [-2.1, +3.2]** | a **measured null** (F.112, corrected by F.113); no F.84 repeat |
| **the deep-tropical margin as a stable quantity** | moves with stream, loss, driver set, station split, learner seed, cleaning rule and use (F.115/F.116) | **exploratory**; direction only |
| **F.112 P4 "the background stays largest": HOLDS** | a difference of medians; paired it is **+0.02 [-8.6, +7.2]** (and was -0.99 before the fix) | **NOT SUPPORTED** (F.113, gotcha #91 fifth time) |
| **F.109 "fragility" explained by city 3147** | 3147 was part of it; the rest is split and design sensitivity (F.115) | the inversion is **exploratory** (F.116) |
| **"a background series is the largest single gain"** | pooled medians; paired under v2 **+4.8 [−23.6, +52.1]** | **no pooled ordering** (F.116) |
| **"AlphaEarth embeddings are one of the spatial nulls"** | that test resolved only **0.65-0.96** on 17/10/6 stations | re-run on 47 cities resolves **0.130** (F.111) |
| **embeddings' median rho 0.327 > benchmark 0.301** | unpaired; **paired it is -0.028**, 21/47 | the paired value is the effect (F.111, gotcha #91 third time) |
| **f = 0.4828** | the 4th digit is unsupported: f moves 0.035 across anchored years and 0.058 across window forms | **0.483**, three significant figures (F.110) |
| **the dispersion step as a working component** | it LOWERS neighbourhood rank from **0.371** to **0.274**, 3/10 cities improve | the measurement framework works better than the spatial model (F.110) |
| **the burden figure as a result** | its interval is field q05/q95 through the central response function only (corrected 2026-10-07); GEMM applied to all ages | **Appendix E**, an illustrative projection (F.110) |
| **"unit mean makes level and pattern separately identifiable"** | the gauge holds for **every** admissible `B`: set `P'=(C-B')/(T-B')` | it identifies the ANCHOR; `B` needs §6.6's constraints (F.108/blocker) |
| **"buy a local sensor first" stated without a loss** | flips sign on episodes: tail **-20.8**, exceedance **-15.9 [-38.1, -1.54]** (F.113) | true for a **daily city mean**; the background wins on exceedance (F.109) |
| **f sensitivity quoted as one range** | there are **THREE** axes: anchored years **0.466-0.501** · `F_min` sweep **0.482-0.509** · **window form 0.489-0.547** | name the axis with the range (F.108) |
| **intervals bootstrapped over CITIES**; widening "1.45–1.97×" | cities share networks; recomputed on corrected ladders: 47 cities in **28** clusters, widening **1.15–2.21×** | **cluster bootstrap is primary** (F.115) |
| **the model's own `s_rep`** | estimated from the FIELD's neighbourhood gradient; instruments sharing a cell disagree **2.6x** more on the panel and **17x** more at Kandy | take it from **co-located instruments** (F.106) |
| **"a learned pattern did not beat the benchmark"** (one family) | 7 admissible families tested; best is **+0.018** vs a 0.130 limit | **no admissible family beats it** (F.105) |
| **"the campaign will test the spatial ceiling"** | dead twice over: it cannot DETECT a siting effect (F.100, needs 96-304 sites) and there is probably none TO detect (F.103) | the campaign settles the **level**, the **within-cell ratio** and the **drainage sign** |
| **"11 registrations, 13 of 38 refuted"** | the registry omitted bkpyr C1/R3 and two g6hqb priors, and counted nxqgb gates not priors | **12 lodged; 48 / 26 held / 17 refuted / 5 not tested** (F.115) |
| **one station 17.02 % [4.57, 21.83]**; first two "17.8 %" | GHAP, 3147 in training, one split | confirmation (F.117): first two **+8.5 % [3.1, 25.1]**; discovery +21.8 is exploratory |
| **one detection limit, δ = 0.130, for every spatial test** | δ depends on each test's paired spread | per test: 0.080–0.180 (F.115) |
---

## 4. Evidence state, by axis

| axis | status | evidence |
|---|---|---|
| **level (daily)** | **strong** — but see §5 W11 | confirmed on 72 fresh cities (F.117) after 46 discovery cities; monotone under added data; an independent network 30–300 km away recovers **71 % [44, 82]** of the background gain per city (F.115; **bounds the same-network artefact from above, does not measure it**) |
| **sub-daily shape** | **regime-limited** | transfers in the **deep tropics** (+25.8% vs flat, r 0.63, ~1 h phase error) — Kandy's regime — and **nowhere else**; pooled it is 5.5% *worse* than assuming no cycle (F.55) |
| **spatial pattern** | **ceiling measured** | ρ ≈ 0.2–0.28, unmoved by four attempts **plus a full LUR predictor set** (636 stations, roads at 5 radii): pooled ρ **+0.273 → +0.275** (F.61) |
| **spatial, per added sensor** | 🟢 **SCORED 2026-09-28 (F.119)** | 18 cities, δ 0.28: cities SPLIT — kriging/RK beats the free raster in 11/18 (5 already at 3 stations), never in 7; ConvGNP flat; siting (cLHS vs random) nothing resolvable; reach ~1 km. **No station count for a Kandy map follows** (1 tropical city). 🔬 **Full records (`fu59b`, F.123, 2026-10-05): 23 primary cities incl. Bangkok (deep tropical); 15/23 cross (8 at 3 stations); X4 refuted (negative within-cell ceilings); 8 tropical cities sit inside the temperate envelope (δ 0.28) → "a handful of stations", still no specific Kandy number.** |

**Why the spatial ceiling is real, EIGHT ways:** tiny within-city signal at 1 km (±10% at
Kandy) · emission ≠ concentration vs ground truth · Track-S learned-pattern null ·
dynamic-transport null (monitors floor-sited) · AlphaEarth EO-embedding null · a full LUR
predictor set moving pooled ρ **+0.273 → +0.275** (F.61) · 🆕 **deliberate siting failing to beat
convenience siting on 43 dense-network cities (F.103)** — which removes the last "our sample is
the problem" explanation.

🟢 **Cause measured in Kandy (F.68/F.69):** a PM10 transect falls **110 → 4 µg/m³ over 300 m**, so a 1 km
cell averages away the signal (sub-grid by construction); scored against the model, paired sites 300 m
apart differ **27.5×** observed vs **1.000×** modelled. 🔴 **`Bud4` is a declared design assumption,
tested and not supported** (OSF `2jyfg`: learned pattern +0.022 vs benchmark 0.309, δ 0.130). Detail:
`docs/claude_md_archive/CONTEXT_moved_2026-09-28.md`.

---

## 5. Open questions

| | question | state |
|---|---|---|
| 🟡 **W6** | **Kandy's source mix — now resolved by GEOGRAPHY (F.71).** A 20-site study finds traffic **predominant in the urban core**, firewood **co-dominant there and dominant rurally**. So `emix vehic = 0.85` is refuted (F.66) *and* Katugastota's 7.6% bounds one suburban site, not the core. **Defensible core value: `vehic ≈ 0.5–0.6`, `burn ≈ 0.3–0.4`.** ⚠ PAHs are a combustion tracer, not mass — this licenses the ordering, not a percentage. | **narrowed, not closed** |
| 🔴 **W11** | **The level discrepancy.** Of four independent Kandy point records, **three sit below the model** (FECT Hantana ~+44%, FECT Akurana, RF-CNN LCS +28%) and **one matches** (NBRO, +0.7%/−2.6%). The three low ones are all LCS carrying a downward calibration; the one that matches has an **undocumented instrument**. | **OPEN** |
| 🟡 **generality** | **F.78's "the sensorless tier fails at Colombo" is RETRACTED as stated** — it was scored against the under-powered `Bud0` (F.84). Re-run with a spec-compliant `Bud0c` and Colombo's **real** geography (F.86/F.87): level bias **+31.3% → −4.4%**, seasonal r **0.55 → 0.93**, plain R² **−0.90 → +0.37**. 🔴 **What survives:** R² against a day-of-year climatology is still **−0.70**, so the model matches Colombo's level and season but adds **no day-to-day skill** — sea-breeze variation the seven drivers cannot resolve. A *located* deficiency, not a failure to transfer. | **narrowed** |
| ⚪ | `A_transport` is entirely unscored; the panel is 10 cities, **all valley/basin, zero coastal**; the panel does not bracket Kandy. | by design |

**Do not resolve W11 by picking the record that agrees.** State it as an open discrepancy.

**Closed topics (detail in the archive file above):** the support-scaling ladder is **confounded** by
siting, never a scaling law (F.76; amplitude question closed, `s_exp` = 1.0) · chemistry is a supporting
discipline with one bound: locally emitted primary share **9.1–48.3 %** (F.98; registered null) · the
Kandy campaign (OSF `ad3py`, 35 sites, **19,900–49,900 USD**) is **excluded from the thesis** (user,
2026-09-17); its spatial premise is refuted (F.100/F.103) and it settles only level, within-cell ratio
and drainage sign.

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
| ⚠ **NBRO regional background** | 🔴 **RE-RANKED 2026-09-27 (F.116).** The evidence no longer ranks local stations above a background in Kandy's band: under ladder v2 the deep-tropical difference is **−27.4 [−47.8, +11.8]** (direction local, interval crosses zero) and reverses prospectively. Confirmed on 72 fresh cities (F.117): both help (first two **+8.5 %**, background **+41.1 %**) and in that mainly temperate, regulatory population the **background outranks the first two** (+24.6 [4.1, 47.8]; exceedances +59.3) — but latitude dependence is undetectable, so this does **not** settle Kandy's band. The ladder's background is a same-network proxy; an independent network 30–300 km away recovers **71 % [44, 82]** of it. Still no free substitute (F.63); the channel works. **Treat CEA local stations and an NBRO background as complementary, not ranked.** |
| ⚫ **Torrington Park BAM-1020, Kandy** | **DEFUNCT (user, 2026-08-22).** The instrument that anchored the RF-CNN calibration and Dhammapala's correction is **no longer operating**. It is provenance for the published records, not a data route. |
| ⚠ **NBRO domain moved** | `nbro.gov.lk` → **`nbri.gov.lk`** (301). Update every NBRO URL in notes and letters. |
| **PDN Uni's own islandwide sensor network** | Unexploited, and it is the user's own institution. Chase internally. |
| ⚠ **CEA passive NO₂** | **DEMOTED** — will *not* fix `P_local` (the ceiling is information-limited). Its value is the `f` partition and activity tracing only. |
| **Mobile campaign** | 4–8 drive days per segment, and it still needs one fixed reference to anchor to. |

**In hand:** FECT (2 low-cost sensors, 2018–2026) · KOALA/NIFS 2019 · OpenAQ + CNEMC (123 cities) · GEE stack · IMERG.
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
| session instructions, gotchas #1–100, current state | `CLAUDE.md` |
| **how** a component is built (maths, modules, invariants) | `PROJECT_ARCHITECTURE.md` |
| **what** came out (stage results, data inventory) | `PROJECT.md` |
| every finding, gate, prior and recorded error | `kandy_pm25/docs/model_reference/F_epistemic_ledger.md` (**F.1–F.123**) |
| what happened when | `memory/SESLOG.md` (reverse-chronological) |
| the formal model statement | `kandy_pm25/docs/MODEL_SPECIFICATION.md` |
| doc index — current vs historical | `kandy_pm25/docs/README.md` |
| the manuscript | `kandy_pm25/docs/paper/` — **edit `draft_s*.md`, never `manuscript_kandy.md`** |
| **the thesis** | `#writing/` — **edit `thesis/chapters/ch*.md`, never `build/thesis.md`**. Titled *"An information-tiered decomposition for hourly kilometre-scale urban PM2.5: what it reconstructs, and what each further observation is worth, demonstrated at Kandy"*; the summary carries the same title, at 12pt Times New Roman. **43,713 words, 41 figures, 10 tables, 566 claims, 0 lint errors** (2026-09-14). Figure plan executed: six new figures, projected maps. Registrations: see §1b (from `#writing/registrations.json`). ⚠ The old thesis is frozen and still carries the retired count. Table 7.5 is generated from `#writing/registrations.json` — never type a registration count |
**Publication view:** Paper 1 (methods/VoI, strong) first; Paper 2 (Kandy) once CEA data arrive.
