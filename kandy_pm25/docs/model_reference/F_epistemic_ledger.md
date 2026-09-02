# Appendix F — The Epistemic Ledger

> The model's conscience in one table. Every quantity that enters the reconstruction,
> with its **provenance** (🔵 OBSERVED / 🟢 LEARNED / 🟠 IMPOSED), its value, its
> uncertainty, and — the column that matters most — **the specific observation that
> would confirm or refute it.** This is what makes the model auditable: anyone can
> see, at a glance, exactly how much of the answer is earned versus assumed.
>
> Rule of reading: a result is only as trustworthy as the *weakest-provenance* link
> in its causal chain. The headline **level** and **temporal/seasonal behaviour**
> rest on 🔵/🟢 links; the **fine-scale spatial magnitude** rests on 🟠 links — which
> is the whole reason for the honesty framing.
>
> *(Seeded in Batch 1 from Part IV; finalised in Batch 4 once Parts III/V add the
> data-source and physics quantities.)*

---

## F.1 Headline reconstruction

| Quantity | Symbol | Value (2019–2023) | Prov. | Uncertainty | Confirm / refute (falsifier) | §|
|---|---|---|---|---|---|---|
| Basin annual mean | $\langle\mathrm{PM}\rangle$ | 19.7 / 19.0 / 17.0 / 18.7 / 20.9 | 🔵 | ±~3 (two-product spread) | independent area product disagreeing >15 % | IV.7 |
| Basin-mean = anchor | — | Δ = 0.000 | derived | exact (theorem) | non-zero G1 ⇒ normalisation bug | IV.1.2 |
| Fine-scale core/edge magnitude | — | ~1.2× annual / ~1.4× night | 🟠 | **unquantified** | floor-to-ridge concurrent sensors | IV.5, IX |

---

## F.2 Temporal anchor $T(t)$

| Quantity | Symbol | Value | Prov. | Uncertainty | Falsifier | §|
|---|---|---|---|---|---|---|
| Residual target | $y$ | $\mathrm{pm25}-c_\text{prior,anch}$ | 🟢 | — | — | IV.2.1 |
| GEOS-CF ratio | $\rho$ | 0.5360 | 🔵 | from KOALA/GEOS means | re-derivation from new ground mean | IV.2.1 |
| Per-sensor offsets | $b_\text{FECT}$ | −9.105 (Ak), −13.749 (Han) | 🔵 | per-sensor fit | recalibration vs reference monitor | IV.2.1 |
| Pooled skill | R² | 0.583 | 🟢 | LOMO | more sensors lifting/lowering it | IV.2.3 |
| Coverage | cov90 | 0.865 | 🟢 | ∈[0.85,0.95] | held-out coverage outside envelope | IV.2.3 |
| Diurnal corr (post-sharpen) | r | ≈1.0 (vs FECT) | 🟢/🔵 | — | new sensor with a different diurnal shape | IV.2.5 |

---

## F.3 Background $B(t)$ and the split

| Quantity | Symbol | Value | Prov. | Uncertainty | Falsifier | §|
|---|---|---|---|---|---|---|
| Seasonal shape | $s_\text{GEOS}$ | GEOS-CF daily, mean 1 | 🔵 | GHAP r≈0.91 | independent product breaking Mar-peak/Aug-trough | IV.3.2 |
| Local fraction | $f$ | {.28,.25,.21,.20,.27}, ~0.24 mean | 🟠 | bracket [15 %, <50 %] | local PMF / paired urban–rural sensors | IV.3.3 |
| Background level | $B_\text{annual}$ | $(1-f)\cdot$VanD ; 2019 ≈14.8 | 🟠/🔵 | bracket [10.5, rural P25] | rural sensor measuring the floor directly | IV.3.3 |
| Background bracket | $B_\text{lo},B_\text{hi}$ | 10.5 ; rural P25 | 🔵/🔵 | hard floor = ridge obs | — | IV.3.3 |

---

## F.4 Spatial pattern $P_\text{local}=S\cdot M\cdot A$

| Quantity | Symbol | Value | Prov. | Uncertainty | Falsifier | §|
|---|---|---|---|---|---|---|
| Satellite surface | $S_\text{emit}$ | mean 1, ±10 % | 🔵 | weak contrast | finer surface product | IV.4.1 |
| Traffic source | $S_\text{traffic}$ | core ≈3.3× mean | 🟠 | **magnitude prior** | measured traffic counts / flow | IV.4.2 |
| Vehicular share | $\nu$ | 0.90 | 🟠 | tunable | local emission inventory | IV.4.3 |
| Emission clock | $e(t)$ | bimodal, mean 1 | 🟠 | EDGAR profile | local traffic-count diurnal | IV.4.3 |
| Confinement coeff | $\kappa$ | 0.15 | 🟠 | **uncalibrated** | floor-vs-ridge hourly contrast | IV.5 |
| Ridge height | $H_\text{ridge}$ | 300 m | 🟠 | **uncalibrated** | observed trapping-height threshold | IV.5 |
| Enclosure field | $c(x,y)$ | zscore$(-\Delta z)$, mean 0 | 🔵→🟠 | DEM-exact geometry | — (geometry is observed) | IV.5 |
| Wind field | $\mathbf u$ | WindNinja library | 🟠 | shape r=0.49 cross-city | basin wind-profiler/sonic | IV.6.1 |
| Transport amplitude | $a(t)$ | clip(…,0,0.5) | 🟠 | **amplitude prior** | drainage-sink test at Katugastota | IV.6 |
| Diffusivity / deposition | $K, v_d$ | solver constants | 🟠 | literature range | tracer/flux measurement | IV.6 |

---

## F.5 Level anchor and health

| Quantity | Symbol | Value | Prov. | Uncertainty | Falsifier | §|
|---|---|---|---|---|---|---|
| Level | $L=$VanD area | per-year, β≡1 | 🔵 | two-product triangulated | new area product | IV.7 |
| KOALA reference | — | ~24.5 (2019 floor/core; derived from monthlies, not printed in the source) | 🔵 | single site/year; 4 s.f. unsupported | re-measurement 2020–23 | IV.7 |
| GEMM params | $\theta,\alpha,\mu,\nu,C_0$ | 0.143, 1.6, 15.5, 36.8, 2.4 | 🟠 lit. | Burnett 2018 CIs | updated CRF | IV.8.2 |
| SL baseline | CDR, $f_\text{NCD+LRI}$ | 6.6/1000, 0.85 | 🔵 lit. | WB/WHO | age-stratified local rates | IV.8.2 |
| Population | pop | WorldPop, 422 314 | 🔵 | model-pop uncertainty | census | IV.8.1 |
| Attributable burden | — | ≈423/yr [231–616] | derived | from PM + CRF | local epidemiology | IV.8.2 |
| Dynamic exposure | $E_\text{dyn}$ | ≈24 (core ≈ KOALA) | derived | +7 % over area | personal-monitoring study | IV.8.1 |

---

## F.6 The one honest sentence

> **Everything about *when* and *how much* (the level, the diurnal/seasonal cycle, the year-to-year change) rests on observed or learned quantities and is corroborated by independent data. Everything about the fine-scale *where* (the within-basin floor-to-ridge magnitude) is imposed from physics and literature priors, because no public network samples that gradient. The model is honest exactly to the degree that this table is kept current.**

---

## F.7 Data-source provenance (retrieval-level)

| Source | Prov. | Retrieval uncertainty | Role | §|
|---|---|---|---|---|
| VanD V6 | 🔵 | AOD→PM₂.₅ conversion; sparse-monitor S-Asia | level + $S_\text{emit}$ | III.A.1 |
| GHAP | 🔵 | ML ensemble; quasi-independent | corroboration only | III.A.2 |
| GEOS-CF | 🔵m | tropical over-prediction (ρ<1) | prior + B shape | III.B.1 |
| ERA5 | 🔵m | 25 km; BLH over terrain uncertain | met backbone | III.C.1 |
| MAIAC | 🔵 | 84.5 % cloud-gapped | feature | III.D.1 |
| TROPOMI NO₂ | 🔵 | coarse; placement not magnitude | cross-check | III.D.2 |
| SRTM | 🔵 | near-exact at this scale | confinement + winds | III.E.1 |
| OSM | 🔵/🟠 | geometry obs; volumes inferred | $S_\text{traffic}$ | III.E.2 |
| KOALA/FECT | 🔵 | LCS over-read (calibrated); 2 floor points + 1 site-yr | $T$ labels + anchor | III.F |
| WindNinja | 🟠 | diagnostic; amplitude prior | winds | III.G.1 |
| COPERT/EDGAR | 🟠 | European/global factors at Kandy | $S_\text{traffic}$ mag., $e(t)$ | III.H.1 |

## F.8 Status

This ledger is **complete** for v1.0 of the model. It is the single artifact to keep current: any new Kandy measurement that calibrates an 🟠 ASSUMED quantity moves its row to 🟢/🔵, narrows its uncertainty, and resolves its falsifier — at which point the corresponding claims in Part IX move from CORROBORATED/ASSUMED toward PROVEN. The model's honesty is, operationally, the upkeep of this table.

---

## F.9 Addendum — falsifiers *tested* by the post-v1.0 transfer-validation arc (2026-06-13)

The v1.0 rows above are unchanged (they describe the released model). This addendum records where
the **transfer-validation / GeoAQ-Zero arc (Part XI)** has now *tested* a falsifier listed above —
**by cross-city transfer (LOCO), not by a Kandy measurement.** No production value changed; these
are status moves on the conscience, with the regime-gap caveat (panel cities are local-dominated;
Kandy is regional-dominated — see XI.1) attached to every row. Evidence on OSF `6puk9`.

| Quantity (row) | v1.0 falsifier | What the arc did | Status move |
|---|---|---|---|
| $T(t)$ skill (F.2) | "more sensors lifting/lowering it" + (implicit) can it work *sensorless*? | anchor-free $T(t)$, LOCO over 196 cities | **🟢 strengthened** — 97 % beat zero-GT baseline, seasonal r 0.95; Kandy sensorless level +4 % vs FECT. *Sensorless temporal anchor validated.* (XI.3 T-a, XI.4) |
| cov90 / conformal (F.2) | "held-out coverage outside envelope" | cross-city (shift-aware) conformal, LOCO | **🟢 strengthened** — cov90 0.91, Kandy-regime 92 % in-band; transfer-failure (0.769) fixed. (XI.3 U) |
| Local fraction $f$ (F.3) | "local PMF / paired urban–rural sensors" | SBI from satellite-only summaries (grid-ABC) | **🟠→🟠/🟢** — Kandy **posterior 0.18 [0.10,0.27]**; imposed year values sit at or above the posterior centre and **2019's 0.28 is just outside the upper bound**; data mildly prefer lower. SBC-calibrated. *Inferred, not just asserted; bracket unchanged in production pending promotion.* (XI.3 I) |
| Background $B(t)$ seasonal shape (F.3) | "independent product breaking Mar-peak/Aug-trough" | W2 trajectory verdict + B(t) v2 candidate | **context added** — transboundary share quantified as **seasonal** (JJA/DJF obs 0.39); v1.0 shape shown too flat (B>total in JJA); origin-conditioned B(t) v2 candidate fixes it (0.82→0.50), **not promoted**. (XI.2) |
| Confinement $\kappa$ (F.4) | "floor-vs-ridge hourly contrast" | panel ablation (F0.3) + SBI (I-3) | **🟠 confirmed UNIDENTIFIABLE from public data** — κ=0 beat κ=0.15 at 3/3 floor-sited panel cities; SBI κ posterior simulator-dependent/conflicting. Falsifier still requires a **Kandy vertical transect**; horizontal support is weak, vertical support unmeasurable. (XI.3 I, XI.3 Phase-0) |
| Fine-scale spatial magnitude / $P_\text{local}$ (F.1, F.4) | "floor-to-ridge concurrent sensors" | PatternNet (learned within-city pattern), LOCO 199 cities | **🟠 reinforced** — within-city pattern **not learnable** from public covariates (ρ 0.14, amplitude SD-ratio 0.34). The physics-imposed choice is *vindicated*; amplitude remains the open problem only sensors close. (XI.3 S) |
| $S_\text{emit}$ circularity (F.7 VanD) | (new, surfaced by the arc) | F0.1 audit: VanD V6 is monitor-fused (Shen 2024) | **caveat added** — partial circularity at monitored cities; **station-blind S_emit still clears the spatial gate** → zero-GT spatial-rank claim survives, bounded. (XI.3 Phase-0) |

**Net:** the *temporal* axis (the "when/how much") moved from corroborated to **transfer-validated
sensorless**; the *spatial* axis (the "where") is **unchanged in production** and its imposed status
is now *vindicated* (learning does not beat it) rather than merely assumed; $\kappa$ and the vertical
gradient remain the **permanent public-data fence**. The one-honest-sentence (F.6) still holds —
this arc tightened both halves of it without moving any production number.

---

## F.10 Addendum — the increment split (2026-07-09, production form change)

The one post-v1.0 change to the **assembly equation itself** (IV.1 → IV.1b): the additive form
inverted the spatial pattern whenever the hourly total dipped below the daily background
($T<B$, 38.5 % of Kandy hours — deep midday mixing), rendering the core *cleaner* than the rural
edge. Production now splits the increment by sign — $\mathrm{PM}=B+\max(T-B,0)\,P+\min(T-B,0)$ —
so the local pattern structures only accumulation; ventilation is spatially uniform.

| Property | Status | Evidence |
|---|---|---|
| T-lock under split | exact, both branches | theorem + G1 Δ = 0.000; `test_split_form_preserves_tlock` |
| Inversion removal | 38.2 % → 0.0 % midday core<periphery | webapp v2 audit; `test_split_form_removes_core_periphery_inversion` |
| Accumulation hours | **bit-identical to IV.1** | $\max/\min$ reduce to the plain form when $T\ge B$ |
| Provenance | 🟠 IMPOSED (physical argument: mixing dilutes the basin together) | falsifier: concurrent core+edge sensors on a ventilated midday hour showing a *preserved* spatial gradient |
| Alternatives tested | diurnally-shaped $B$ **rejected** (relocates inversion, 37.6 %) | webapp_v2 plan doc |
| Propagation | Kandy builder · multi-city `xichang_prod` · webapp export/reconstruction · release repo `kandymodel` | commits 75c2349, c642d30, c28d785 |

No headline number moved (T-lock exact; 2023 burden 425 unchanged); the change is in *where*
the ventilated-hour field puts its (now flat) spatial structure.

## F.11 Addendum — the ventilated-hour pattern floor (additive_v3, 2026-07-21)

The split (F.10) fixed the inversion but rendered ventilated hours **perfectly flat** — and
ground truth says that overcorrects. On the Medellín network the 220 hours where the model's
increment is ≤ 0.5 µg m⁻³ keep station spread σ ≈ 5.7 µg m⁻³ (relative 0.68 > 0.42 for structured
hours): near-source plumes persist through ventilation. Production adds a **bounded, mean-zero
pattern floor** $\varepsilon(t)(P-1)$, $\varepsilon(t)=\max(0,\varepsilon_0-\max(T-B,0))$ (IV.1c),
active only where the accumulation amplitude is below $\varepsilon_0$.

| Property | Status | Evidence |
|---|---|---|
| T-lock under the floor | exact ($(P-1)$ is mean-zero) | Δ = 0.000000 all years; webapp QA reconstruction 0.0012 µg m⁻³ |
| No re-inverted core | 0.0 % core<periphery | $\varepsilon_0\ge0$, accumulation-side $P$ mutes toward flat, never flips |
| Structured hours | **bit-identical to IV.1b** | floor inactive when $T-B\ge\varepsilon_0$ |
| Paper figures | unchanged | annual-mean spatial field 99.99 % corr v2↔v3 (floor averages out) |
| $\varepsilon_0$ (Kandy) | 🟠 METHOD-TRANSFER: 2.573 µg m⁻³ = 0.398 × mean accum. amplitude 6.465 | Medellín fit (slope 5.65, holdout-6 flat-hour RMSE 8.53→7.99) + cross-city no-degrade (KTM, ChiMai); relative form transferred (no Kandy network) |
| Distinct from rejected A2 | additive mean-zero ≠ multiplicative $1+a(P-1)$ | A2 inflated the *level* (monitors on high-$P$ side), cross-city 0/4 — the floor touches neither level nor structured hours |
| Provenance | 🟠 IMPOSED at Kandy (validated at Medellín, ported) | **falsifier: a Kandy mobile/transect campaign measuring real spatial spread on ventilated hours** |
| Propagation | fit+gate `flat_hour_residual_fit.py` · build `build_additive_field_v3.py` · webapp export/`store.js` · canonical `assemble_year()` param `EPS_FLOOR` (release + framework) · reference IV.1.3c | — |

Measured Kandy effect: flat-field hours 56.6 %→45.3 %, median spread 0.60→1.25, **annual means and
pop-weighted exposure unchanged** (+0.2 %). Like F.10, no headline number moved; the change is the
muted spatial texture the model now shows on ventilated hours instead of a featureless field.

## F.12 Addendum — the forecast tier (demonstration, 2026-07-27)

A **display tier, not a change to the model.** The frozen area-anchored anchor GBM is driven by
NASA GEOS-CF *forecast* fields instead of reanalysis, producing a +120 h basin-mean level that the
public explorer offers as selectable future hours. The locked 2019–2023 headline and the
2024–2026 extension tier are untouched.

| Property | Status | Evidence |
|---|---|---|
| Driver substitution costs little | **validated, off-target** | F-M2 at Medellín, clean split (train ≤2022, score 2023) vs 15 withheld stations: RMSE **5.71** vs 24 h persistence **6.49**, skill **+0.120**; seasonal r 0.974, diurnal r 0.965 |
| Anchor is satellite-independent | validated | F-K1: retraining without the 5 forecast-absent satellite features costs Δ −0.004 residual R² |
| Skill at **Kandy** | **not estimable** | no public in-basin station; nothing to score against. Displayed as a demonstration with borrowed evidence, never as a checked product |
| Interval calibration | **imposed, measured off the daily anchor** | sensorless anchor's nominal 90 % PI covers **70.7 %** (n=1215 d); k = **1.35** restores 90.0 % (direct search and split-conformal agree to 0.000); applied to the hourly forecast PI as a disclosed transfer |
| Forecast spatial pattern | **does not exist** | only the level is forecast; the map uses the (month, local-hour) `P_local` climatology of the most recent reconstructed year, banner-labelled |
| Background for forecast hours | inherited | $B = T\cdot(B/T)_{\text{month}}$ from the locked 2019–2023 chain — the extension-tier rule; a flat $B$ would flatten the monsoon field (gotcha #61) |
| Propagation | derivation `kandy_forecast_ood_widening.py` · constants `kandy_forecast_pack_update.py` · runner `kandy_webapp/live/kandy_live.py` · client `store.initForecast` · reference F.12 | — |

**Numbers discipline.** An earlier F-M2 run reported skill **+0.223** / RMSE 5.04 and a 12–36 h lead
sweep of +0.22…+0.44. That run trained on hours inside its own evaluation year while the persistence
baseline received no look-ahead; the clean split roughly halves the headline. Those figures must not
be displayed or quoted. Separately, under the clean split the forecast-driven anchor edges the
*analysis*-driven one (5.71 vs 5.96); this is **amplitude calibration, not forecast skill** —
correlation is identical (0.590 vs 0.592) and the analysis anchor's extra hour-to-hour variance is
unskillful at unchanged correlation. It is never to be described as beating reanalysis.

### F.12b — closing the record→forecast seam (2026-07-27)

The forecast tier exposed a structural discontinuity that had always existed and was
simply never visible: the reconstructed record can only reach about **now − 5 days**
(ERA5-Land latency), while the forecast begins at the newest model run, leaving a band
that **no dataset can fill retrospectively**. GEOS-CF serves analysis for a rolling
**25 h window only** (dated CFAPI requests are rejected) and its OPeNDAP replay archive
lags by months (verified 2026-07-27: coverage ends 2026-01-02).

Resolution — three tiers past the end of the anchored record, each labelled separately
rather than merged:

| Tier | Drivers | Lead | Completeness |
|---|---|---|---|
| extension (record) | ERA5-Land, rebuilt on demand | past | full field + met |
| **recent (nowcast)** | GEOS-CF **analysis**, 25 h rolling window logged hourly | 0 | full field + met |
| forecast | GEOS-CF forecast | +1…+120 h | full field + met |
| **level only** | forecast issued earlier, met not retained | past | field only — wind and weather **withheld** |

The nowcast step is the permanent fix: logged every hour, the rolling analysis window
accumulates into continuous coverage and the seam cannot re-form. `level_only` exists
only for the one-off band that predates it; those hours reconstruct a field (which needs
$T$, $B$ and $P$, not meteorology) but the wind layer and weather panel are hidden rather
than back-filled from a different met product.

Two defects were found closing this and are worth stating because both are recurrences:
**(1)** rebuilding `additive_v2` without rebuilding `additive_v3` left the exporter reading
a stale field against fresh anchors — the QA gate caught it at 5.61 µg m⁻³ (tol 0.25), the
same anchor-desync family as gotcha #65, and the fix is to rebuild the tier the exporter
actually reads. **(2)** payload JSON/gzip requests carried **no cache-busting**, so a
returning visitor kept the previous export while running the new code; data URLs are now
stamped with the module version read from `import.meta.url`.

## F.13 — the daily-B seam, quantified; and a seasonal re-level tried and REJECTED (2026-07-27)

Triggered by a user report that the webapp shows no emission structure "since April".
It does not, and the cause is not the extension tier or the forecast: it is the seam
between an **hourly** T(t) and a **daily-resolution** B(t), present in every year of
the record since 2019.

**Measured over all 66,193 shipped hours (2019-2026):**

| Quantity | Value |
|---|---|
| hours with $B>T$ (background exceeds the total) | **28.5%** |
| by month | ~2-13% Jan-Mar, **27-48% from April**, high through November |
| hours below the SBI posterior's own bound $f\ge0.10$ | 35.1% |
| monthly-mean $B/T$, locked years | Jan-Mar 0.53-0.63 · **Apr 0.89 · May 0.97 · Sep 1.11 · Oct 1.01 · Nov 0.96** |
| displayed local share | **negative** in Sep/Oct/Nov of most years (Sep 2022: −0.49) |
| median map spread | 5.7 µg m⁻³ (Mar) → **0.6-0.9 (May-Sep)** |

In May, September, October and November the **monthly mean** background exceeds 90% of
the monthly mean total, so this is not an hourly sampling artefact — the seasonal
partition itself is incoherent. Under the increment split every such hour renders
spatially uniform by construction, which is exactly the reported symptom. Independent
corroboration that the wet-season background runs high: W2 (D2) puts the observed JJA
level near the pristine marine floor at ~7.4 µg m⁻³ while the model's JJA **background
alone** is 8.50.

**The re-level (`scripts/kandy_background_relevel.py`) — built, gated, rejected.**
Bound monthly $B/T\le0.89$ and hourly $B\le0.9\,T$, redistributing multiplicatively so
each year's mean of $B$ is preserved exactly (hence the disclosed $f$ untouched).

| Property | Result |
|---|---|
| annual mean of B | preserved to 7e-15 µg m⁻³ |
| $B>T$ | 28.5% → **0.13%** (residual = hours where raw T itself is <0) |
| negative local shares | eliminated |
| W2 JJA/DJF background ratio | 0.544 → 0.490 (observed 0.53) — passes a 0.03 gate |
| **dry-season structure** | **2022 Mar local share 0.287 → 0.112; map spread 3.92 → 2.61** |
| **wet-season structure** | **little gained; 2023 May spread 1.11 → 0.62** |

**Rejected on that last pair.** Annual mass conservation means every month *below* the
ceiling is scaled UP to absorb what the capped months give back, and those months
outnumber the capped ones — so the season that currently renders well pays for the one
that does not, and the net effect is *less* spatial structure. A first redistribution
variant (proportional to headroom rather than multiplicative) was rejected earlier by
the W2 gate, which caught it driving the transboundary ratio to 0.447.

The three constraints — a coherent monthly partition, the disclosed annual $f\approx0.24$,
and the W2 seasonal background shape — **cannot all hold with a daily background**. That
is the case for Consolidation v3 (an hourly semi-mechanistic B), and this is now the
quantified argument for it rather than a stylistic preference. Code retained with
`RELEVEL = False` in `build_additive_field_v2.py`.

**Process note.** The first application was written as a separate post-processing step
and was silently discarded, because `build_additive_field_v2.py` regenerates B from
scratch. A fix to a derived artefact must live inside the code that derives it.

## F.14 — B(t) checked against instruments for the first time (NBRO network, 2026-08-01)

The regional background carries ~three quarters of Kandy's PM2.5 and had never been compared
with a measurement: everything constraining it was internal (a rural satellite floor, an
origin-conditioned seasonal shape) or indirect (W2 trajectories). The hourly `NBRO_AQ_snapshot`
task has since 2026-05-08 been logging **25 Sri Lankan stations in raw µg m⁻³**, giving a
~10-week overlap with the modelled record.

Method (`scripts/kandy_background_nbro_check.py`): exclude anything within 20 km of Kandy
(one station, "Kandy", dropped — it cannot be allowed to leak into a check of the background);
require ≥6 stations per hour; compare at **daily** resolution because B(t) is a daily product;
score B against the network's low percentiles, since B was *constructed* as a rural floor and
every individual station carries its own local increment.

| Target | Level (µg m⁻³) | r (daily) | Spearman | model − obs | ratio |
|---|---|---|---|---|---|
| network floor P10 | 5.35 | +0.293 | +0.236 | +3.38 | 1.63 |
| network P25 | 7.78 | +0.366 | +0.301 | +0.95 | 1.12 |
| network median | 11.49 | +0.367 | +0.371 | −2.76 | 0.76 |
| network mean | 14.18 | +0.270 | +0.349 | −5.45 | 0.62 |

n = 44 days (2026-05-10 → 07-21), median 13 stations/hour; modelled B = **8.73**.

| Property | Status | Evidence |
|---|---|---|
| Background **level** plausible | **corroborated** | B sits between the network's P10 and median, ratio 1.12 to P25 — where a regional floor belongs |
| Physical ordering | holds | floor < median < mean, as construction requires |
| Background **day-to-day variability** | **weakly verified** | r ≈ 0.37 daily (p ≈ 0.014 at n=44) — it tracks the regional air mass, but loosely. First quantification |
| Wet-season level | **runs HIGH** | applying a x1.35 low-cost-sensor correction puts the true regional floor near **5.76**, making B **1.51x** it |

**The wet-season result is the important one, and it is a THIRD independent line** on the
same conclusion, from an instrument rather than from the model's own internals:
(1) internal coherence — B > T in 28.5% of hours, monthly B/T to 1.14 (F.13);
(2) W2 D2 — model JJA background 8.50 vs observed ~7.4;
(3) **this** — B is ~1.5x the calibrated island floor over 44 wet-season days.

This changes the standing of the rejected re-level (F.13). That fix was rejected because
annual mass conservation forced the dry season to pay; but the constraint being conserved —
the annual f — now has external evidence against it in the wet season specifically. A
**non**-mass-conserving reduction of the wet-season background may simply be correct, with f
rising accordingly. It is the anchor Consolidation v3 should be built against, rather than
the model's own prior.

**Cannot establish:** no station is in-basin, so nothing here validates the Kandy field or
the local increment; the x1.35 correction is a literature assumption, not a measurement; all
44 days are wet-season, so DJF — when the transboundary background matters most — is
untested; an island floor proxies Kandy's inflow rather than measuring it.

## F.15 — Consolidation v3 built in two forms, both REFUTED; the seam is a LEVEL problem (2026-08-01)

F.13 quantified the daily-B seam and rejected a bounded re-level. F.15 attacks the same
defect architecturally, as the roadmap intended — an **hourly semi-mechanistic background**
(`scripts/kandy_background_v3.py`). Both formulations fail, and the failures localise the
problem precisely.

**Form 1 — rebuild B from local physics.** $B=L_{\text{class}}\cdot D\cdot W$ with dilution
$D=(H_{ref}/H)^{\alpha}$ and wet removal $W=e^{-\kappa R}$, $\alpha,\kappa,\tau$ fitted to
the NBRO regional floor.

| Diagnostic | Result |
|---|---|
| fitted $\alpha$ | **0.80 — bound-saturated** (cf. SharedTerrainAnsatz, all 6 params bound-hit) |
| coherence | B > T 28.5% → **21.8%**, still FAIL |
| W2 JJA/DJF | **0.427** vs observed 0.53, FAIL |
| agreement with NBRO floor | **r = −0.07**, against **+0.37 for the v2 daily background it replaced** |

The last row is a genuine finding: **the regional background's day-to-day variation is set by
what is advected in — chemistry and transport, which the GEOS-CF daily shape carries — not by
local dilution and washout.** That is what a background *should* do; it is determined upwind.
Rebuilding it from local meteorology discards real information.

**Form 2 — add only the missing diurnal physics.** $B_{v3}=B_{v2}\cdot D/\overline{D}_{\text{day}}$,
normalised within each calendar day so every daily mean is preserved exactly — hence $f$, the
W2 ratio and every seasonal quantity are invariant *by construction*, and only the diurnal
distribution changes.

| $\alpha$ | 0.0 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| B > T | 28.6% | 28.1% | 27.8% | 28.0% | 28.5% | **29.1%** |
| background diurnal swing (µg m⁻³) | 3.65 | 9.27 | 14.73 | 19.70 | 24.18 | **28.19** |

**Coherence is flat in $\alpha$ and worse at the top end**, even at a physically absurd 28 µg m⁻³
background swing. B and T already share their diurnal driver, so adding a BLH response to B moves
it up at night and down at midday exactly as T does — $B/T$ barely changes — and at large $\alpha$
the background's night peak overshoots T, creating new incoherent hours to replace the fixed ones.

**Conclusion — the seam is a LEVEL problem, not a phase problem.** Three independent attempts:

1. mass-conserving seasonal re-level → fixes coherence, costs dry-season structure (F.13)
2. background rebuilt from local physics → external agreement collapses, two gates fail
3. diurnal dilution added to v2 → coherence unchanged at every $\alpha$

The only remaining lever is the **low-season level of B**, and lowering it necessarily raises $f$
above its disclosed band. F.14 says that lowering is probably right *in the wet season* (B is
1.51× the LCS-corrected island floor). But annual conservation makes the dry-season background
rise to compensate, and **no external measurement covers DJF yet** — the NBRO log began
2026-05-08, so its overlap is wet-season only. W2 makes a *higher* DJF background plausible (DJF
is 82% Bay-of-Bengal Indian outflow, IGP-origin FECT 27 µg m⁻³), so the compensating rise may
itself be correct.

**This is now blocked on a measurement rather than on a method, and the measurement is dated:**
the NBRO network accumulates DJF coverage from December 2026, at which point re-running
`kandy_background_nbro_check.py` decides between (a) lower wet-season B and accept f ≈ 0.30, and
(b) the F.13 re-level, whose dry-season cost may be a correction rather than damage. Until then
the shipped v2 background stands, with the defect disclosed.

## F.16 — A2: the anomaly target does NOT retire the sharpening patch, and A4 closes on evidence (2026-08-01)

The sharpening patches (`sharpen_T_diurnal`, `sharpen_to_locked`) exist because the lag-free
GBM regresses to the mean and damps the diurnal swing. A2's premise was that predicting the
**departure from a climatology** would put the amplitude in the climatology and retire the
patch at its cause — and, if the climatology could be made sensorless, would also shrink the
A4 disclosure gap. Both halves were tested on a clean temporal split (train ≤ 2022, score on
2023 hours never seen; gotcha #68), `scripts/kandy_anomaly_target_test.py`.

| variant | RMSE | diurnal r | **swing ratio** | seasonal r | level bias |
|---|---|---|---|---|---|
| a. direct GBM, no sharpening | 12.588 | 0.882 | **0.579** | 0.408 | +4.97% |
| b. direct + post-hoc sharpen (production) | 12.741 | 0.895 | **0.787** | 0.390 | +4.97% |
| c. **anomaly target**, FECT climatology | **12.373** | **0.902** | 0.696 | **0.420** | **+1.79%** |
| d. anomaly target, **sensorless** climatology | 12.847 | 0.874 | 0.609 | 0.376 | +6.45% |
| e. anomaly + post-hoc sharpen | 12.455 | 0.895 | 0.763 | 0.390 | +1.79% |

**Row (a) confirms the defect out-of-sample: the raw anchor reproduces only 58% of the observed
diurnal amplitude.** The patch is not cosmetic.

**The premise is refuted.** The anomaly target lifts the amplitude only to 0.696, short of the
post-hoc patch's 0.787, and combining both (e) still does not beat (b) on amplitude. Predicting
anomalies does *not* retire the patch family; the patch remains the best amplitude repair.

**Its apparent accuracy win does not survive production.** (c) improves level bias 4.97% → 1.79%
and RMSE 12.74 → 12.37, but production **re-anchors T(t) to the VanD area mean every year**, which
absorbs annual level bias entirely. What survives the re-anchor is shape: seasonal r +0.03,
diurnal r +0.007, and swing ratio **−0.09 (worse)** — i.e. marginal, and negative on the very axis
the patch exists for. **Not adopted; the locked anchor is unchanged.**

**A4 now closes on evidence rather than wording.** Row (d) replaces the FECT climatology with a
genuinely sensorless one — the cross-city panel-donor solar-time diurnal shape × a chemistry-prior
seasonal shape — and it is worse on *every* metric (swing 0.609, diurnal r 0.874, level bias
+6.45%, worst RMSE). So the shipped diurnal/seasonal shape's dependence on the two local sensors
is **real and necessary, not a presentational choice**. The preprint's §2 disclosure stands as
written, and can now cite a measurement: a sensorless shape was constructed and performs
measurably worse.

Note for interpretation: out-of-sample the production-style patch itself recovers only 0.787 of
the amplitude, because it maps onto the *training* climatology. In production it is fitted on the
full record, so the in-sample appearance is near-perfect — another instance of gotcha #68's family,
and a reason the shipped swing should not be quoted as validated skill.

## F.17 — the decomposition is OVER-DETERMINED: f, coherence and an independent background cannot all hold (2026-08-02)

Commissioned to (a) establish the background/local split from evidence rather than prior and
(b) build a true hourly background. Both were done. The result is structural, and it is more
important than either deliverable.

### The defect is year-round, not April
`scripts/kandy_f_reconciliation.py` introduces a bound nobody had computed: a background that
is flat within a day cannot exceed that day's MINIMUM total, so the shipped `T(t)` alone puts a
**hard floor** under f, with no external input at all.

| month | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| f shipped | .442 | .469 | .368 | .110 | .034 | .222 | .206 | .174 | **−.115** | −.013 | .043 | .369 |
| f floor | .375 | .349 | .321 | .362 | .406 | .395 | .440 | .455 | .446 | .460 | .473 | .434 |

**The shipped split is below its own coherence floor in 9 of 12 months — April through
December** — and annually **0.244 against a floor of 0.410**. April is merely where it becomes
visible. The seasonality is also inverted: the wet season needs the LARGEST local share (clean
marine inflow, so what is present is mostly local) and the model gives it the smallest. The
NBRO instrument agrees from outside — wet-season f = **0.446**.

### The over-determination
`scripts/kandy_background_v4.py` rebuilt B hourly with the level set by the NBRO instrument
(marine floor 5.76, measured), the day-to-day shape kept from GEOS-CF (the only term with
external support, r = +0.37), and a genuine diurnal dilution response. Sweeping the two free
parameters shows three constraints that cannot be jointly satisfied:

| choose | outcome |
|---|---|
| independent background dynamics + f ≈ 0.25 | **B > T in 28.5% of hours** — the shipped v2 defect |
| independent background dynamics + coherence | **f = 0.65–0.71**, outside the literature bracket [0.15, 0.50) |
| coherence + f ≈ 0.25 | B must track T day-to-day, i.e. B ≈ (1−f)·T — a background with no independent dynamics, making the split definitional rather than physical |

Solving instead against the W2 JJA/DJF ratio (0.53) forces the continental level to 19.45,
giving f = 0.182 and coherence 32.9% — worse than what it replaces. **W2's 0.53 is the outlier
among the three lines**, and it is the softest: it is a background ratio *inferred* from FECT
totals by air-mass origin, and that inference itself assumes a local share, so a larger true f
biases it.

### Two residuals worth recording
* **~1.8% of hours have T(t) below the measured regional floor of 5.76** — no background level
  can make those coherent. Either the wet-season T runs low, or the island P25 overstates
  Kandy's inflow (plausible: 24 stations including coastal towns, while Kandy is inland and
  elevated). **This is the most likely single point of failure and the cheapest thing to test
  next** — an in-basin or upwind rural station would settle it.
* Normalising the dilution term within each day, which an earlier version did to protect the
  daily series, makes the term inert: a daily-neutral factor cannot lower the midday background,
  which is the entire purpose. A real background's daily mean must be an OUTPUT.

### Status
No background was adopted. `kandy_background_v4.py` is retained as the assessment instrument.
The honest reading is that the additive decomposition, as currently posed, has one more
constraint than free function — and the resolution is a measurement (what is the actual regional
inflow over Kandy?), not a reparameterisation. Four rebuild attempts across F.13, F.15 and F.17
now agree on that.

## F.18 — the Lenschow envelope background: built, and rejected on the same gate as its predecessors (2026-08-03)

The last remaining reformulation. Rather than levelling the background independently and
hoping it stays under the total, estimate it the way the project's stated framework
(Lenschow 2001) actually prescribes: as the persistent LOWER ENVELOPE of the total.

    B(t) = L(month) . G(day) . D(hour),  L = a low quantile of hourly T within the month

Coherence then stops being a constraint to satisfy and becomes a property of the
construction. `scripts/kandy_background_v5.py`, swept over the envelope quantile and the
dilution exponent:

| envelope | f annual | B > T | JJA/DJF |
|---|---|---|---|
| P05 | 0.517 | 3.6% | 0.324 |
| **P10** | **0.438** | **7.4%** | **0.349** |
| P15 | 0.379 | 11.4% | 0.360 |
| P20 | 0.330 | 15.5% | 0.365 |
| P25 | 0.284 | 19.8% | 0.370 |

The P10 envelope is attractive on two axes: **f = 0.438 independently matches the NBRO
instrument (0.446) and clears the hard coherence floor (0.410)**, and coherence improves
roughly fourfold (28.5% → 7.4%).

**Rejected on the W2 gate.** It drives the JJA/DJF background ratio to **0.349** against an
observed **0.53** — a clear degradation of a validated transboundary result. The F.13
re-level was rejected for moving the same ratio to 0.447; applying a weaker standard here
because this attempt is more elaborate would be motivated reasoning. **Not adopted.**

### Why every reformulation fails the same way
Five attempts now (F.13, F.15 ×2, F.17, F.18). The pattern is consistent and is the finding:
a background with genuinely independent dynamics, pointwise coherence with the total, an f
inside the literature bracket, and the W2 seasonal shape are **four constraints on three
degrees of freedom**. Each attempt satisfies three and breaks the fourth, and which one
breaks depends only on which is left unconstrained.

The binding evidence gap is specific and cheap to close: **1.8% of hours have T(t) below the
measured regional floor of 5.76 µg/m³**, and the island P25 that supplies that floor pools 24
stations including coastal towns while Kandy is inland and elevated. **One in-basin or upwind
rural monitor would determine whether the wet-season total is too low or the regional floor
too high, and that single measurement collapses the over-determination.** No amount of
reformulation substitutes for it.

**Shipped model unchanged.** The visible consequence is handled at the display layer instead
(F.19): hours where the model cannot resolve a local increment now say so, rather than
rendering a flat field and a zero or negative local share with no explanation.

## F.19 — the split limitation is now stated where the viewer meets it (2026-08-03)

Display-layer consequence of F.13/F.15/F.17/F.18. On hours where the estimated background
is at or above the modelled total the increment is zero or negative, the field is spatially
uniform **by construction**, and the app previously printed "0%" local beside a flat map —
which reads as "there are no local emissions here". It is not that; it is that the split
cannot be made.

Those hours now say so, and link to a new method-page section that gives the frequency
(~28% of all hours, 2-13% Jan-Mar rising to 27-48% from April), the cause (a daily-resolution
background against an hourly total), what was attempted (five reformulations, each rejected
by a measurement), and what would actually resolve it (one in-basin or upwind monitor).

No model quantity changes. This is the only intervention in the whole arc that improves the
product without trading one validated result for another.

## F.20 — city-graph donor weighting: small, real, and bounded by extrapolation (2026-08-06)

`scripts/panel_city_graph_donor.py`. The donor diurnal shape is currently an UNWEIGHTED
MEAN over 199 CNEMC cities. This replaces it with a learned similarity kernel over city
descriptors — the GAGNN/HighAir construction, with cities as nodes, which is the only
graph formulation that applies at Kandy's sensor density (GraPhy loses to IDW below
~0.16 sensors/mi²; Kandy is 0.023).

| evaluation | unweighted mean | geographic kernel | learned kernel | gain |
|---|---|---|---|---|
| plain LOCO | 0.8216 | 0.8785 (100 km) | 0.8833 | +0.062 |
| **block CV > 500 km** | **0.8044** | 0.8245 (400 km) | **0.8359** | **+0.032** |
| block CV, **transferable descriptors only** | 0.8044 | — | **0.8213** | **+0.017** |

**Three findings, in order of importance.**

**(1) Plain LOCO is the wrong evaluation and overstates the gain by ~2×.** Every Chinese
panel city has close neighbours; Kandy has none. Spatial-block CV, which withholds all
donors within 500 km, is the evaluation that matches the use case, and it halves the gain.
Note that the learned kernel *overtakes* the geographic one under block CV — when nearby
donors are unavailable, descriptors are what is left.

**(2) The panel does not bracket the target.** The CNEMC panel spans 84.9–130.4 °E and
Kandy sits at 80.6 °E: **zero of 199 panel cities lie west of it.** Longitude is the
dominant fitted descriptor under block CV, so the +0.032 figure rests on extrapolating
the one feature that cannot transfer. Restricted to physically transferable descriptors
the honest gain is **+0.017**, and among those **relief dominates** (bandwidth 0.87 against
0.77 for magnitude and 0.00 for latitude) — terrain shapes the diurnal cycle through
boundary-layer confinement, which is physically the right answer.

**(3) A leak was caught and removed.** The first run included `peakiness`, derived from the
target city's *own* diurnal shape, and `log_stations`, a property of the monitoring
programme rather than the atmosphere. Neither is obtainable for an unmonitored target.
Removing them dropped plain LOCO from 0.860 to the values above. The admissibility rule is
now stated in the script: **a descriptor may be used only if it exists for a target with no
local observations.**

**Verdict: adopt as a method contribution for the panel work; it does not change Kandy.**
+0.017 on a donor shape that only enters the sensorless comparison is immaterial to the
shipped product, exactly as predicted before running. Its real value is the second finding,
which is an argument for the non-Chinese panel expansion.

## F.21 — a hierarchical estimate of f, and four independent lines converging (2026-08-06)

`scripts/kandy_f_hierarchical.py`. The project kept its hand-set `FRAC_LOCAL_YEAR` over the
SBI posterior on an INFORMAL argument: that the inference "runs low against the literature
bracket at every locally dominated panel city". With four cities that is estimable rather
than assertable.

The shortfall at the three locally dominated cities is not a constant offset (0.34, 0.50,
0.45) but a roughly stable RATIO (0.50, 0.34, 0.44). The distinction decides the answer:
an additive correction applied to Kandy gives f ≈ 0.61, outside every bracket, while a
multiplicative one lands near two independent estimates.

    f_c   ~ N(mu, tau)              population of cities, partial pooling
    SBI_c ~ N(rho . f_c, s_c)       the inference attenuates the true fraction
    lit_c ~ N(f_c, w_c)             literature bracket as a soft observation

Fitted on Xichang, Kathmandu and Medellín; **Kandy is held out of the fit**, so it never
informs the correction applied to it.

| quantity | result |
|---|---|
| SBI attenuation | **rho = 0.426 ± 0.066** — the inference recovers ~43% of the true fraction |
| **Kandy f** | **0.392, 90% CI [0.258, 0.525]** |
| shipped prior | 0.244 (0.20–0.28 by year) |
| raw SBI | 0.181 |

**Four independent routes now converge, and three of them were held out of this model:**

| line | value | used as input? |
|---|---|---|
| hierarchical estimate (this) | 0.392 [0.258, 0.525] | — |
| coherence floor, shipped anchor alone (F.17) | 0.410 | **no** — inside the CI |
| NBRO island network, wet season (F.14) | 0.446 | **no** — inside the CI |
| literature bracket | [0.15, 0.50] | soft |

**The shipped f = 0.244 is now positively refuted rather than merely "below a floor".** The
informal bias argument is confirmed and quantified: the SBI inference is attenuated by a
factor of about 0.43, which is why it looked low everywhere it could be checked.

**Caveats, and they are real.** Three fitting cities — this is the regime partial pooling
exists for, but the population parameters are weakly identified and the interval is
indicative. The literature bracket is an expert range treated as a normal likelihood, so its
tails are optimistic. `rho` is assumed common across cities; regime-varying attenuation is
not identifiable at n=3.

**What this does and does not change.** It does NOT resurrect any of the five rejected
background rebuilds: F.18 showed that a background built to deliver f ≈ 0.44 breaks the W2
seasonal ratio, and that remains true. What it changes is the STATUS of f — from a prior the
project distrusted to an estimate with an interval and four converging lines. The preprint
should carry this number, its interval, and the attenuation finding.

## F.22 — holiday natural experiments: a fifth, direct line on f, and the Sunday conflict resolves (2026-08-06)

`scripts/kandy_holiday_experiment.py`. A meteorology-controlled Sunday test had implied a
locally generated share of only 0.14-0.23, against four converging lines near 0.40 (F.21).
Sri Lanka supplies a better instrument: **Poya days**, monthly full-moon public holidays
that fall on a DIFFERENT WEEKDAY each month, so a holiday effect is identifiable while day
of week is held fixed — which the weekend test cannot do. Transboundary transport is
indifferent to Sri Lankan holidays, so any drop is local by construction.

Residuals are taken against (month × hour × ventilation-quintile) cell means; effects are
measured against ordinary working days. Poya dates are astronomical full moons in local
time (`ephem`); a gazette mismatch of one day dilutes rather than biases.

| instrument | n hours | effect | % of mean | p |
|---|---|---|---|---|
| Sunday | 2,517 | −1.077 | **−7.8%** | 4.2e-08 |
| **Poya (lunar public holiday)** | 603 | −1.626 | **−11.7%** | 1.7e-05 |
| Poya, *within* day-of-week | 558 | −1.422 | −10.3% | — |
| other fixed public holidays | 198 | −2.167 | **−15.6%** | 1.5e-03 |
| Sinhala/Tamil New Year (13–14 Apr) | 143 | +0.255 | +1.8% | 0.79 (null) |

**The ordering is the result.** Sunday (partial reduction) < Poya (full public holiday) <
other fixed holidays (full shutdown) is monotone in the degree of activity removed, which
is what a genuine local-activity signal must look like and what a confounder would not
produce.

**The apparent conflict was an artefact of using the weakest instrument.** Converting under
a 30–50% activity reduction:

| instrument | implied f |
|---|---|
| Sunday | 0.155 – 0.259 |
| Poya (within day-of-week) | 0.205 – 0.342 |
| Poya | 0.235 – 0.391 |
| other fixed public holidays | 0.313 – 0.521 |

The stronger instruments reach and overlap the four converging lines (hierarchical 0.392,
coherence floor 0.410, NBRO 0.446). **f ≈ 0.40 is now supported by a fifth line that
measures local activity directly**, and the earlier Sunday-based objection is withdrawn:
Sunday is a partial-activity day and understates the share.

**One unexplained anomaly, reported not explained away.** The Sinhala/Tamil New Year shows
**no effect at all** (+1.8%, p = 0.79) despite being the largest annual shutdown. Candidate
causes — April is the inter-monsoon transboundary peak, which may swamp the local signal;
large-scale holiday travel replaces commuting; celebratory burning offsets traffic — are
untested. n = 143 hours over few years is also thin. This is flagged as open.

**Standing caveats.** The effect sizes are assumption-free; the conversion to f is not, and
the 30–50% activity-drop assumption is unverified for Kandy and dominates the width. The
outcome is FECT point sensors, not the basin mean. Sources with no holiday cycle — domestic
cooking, waste burning, road dust — are invisible to this design and fall to the regional
side, so every figure here is a **lower bound** on the total local share.

## F.23 — the ~90% vehicular assumption, tested at last (2026-08-06)

The emission-timing profile e(t), the traffic-centrality emission surface, and hence the
shipped diurnal shape all rest on Kandy being roughly nine-tenths vehicular. That figure
came from an EDGAR sector prior and had **never been tested**. The holiday instrument
(F.22) tests it directly: if local emissions are vehicular, the holiday effect must
concentrate at rush hours; if they are cooking, waste burning or dust, it must be flat.

| window | mean holiday effect |
|---|---|
| rush (06–09, 17–20) | **−2.893 µg m⁻³** |
| off-peak (00–04, 11–14) | −0.789 µg m⁻³ |
| **ratio** | **3.67×** |

Hour by hour the effect peaks at **07:00 (−3.38)** and across **17:00–20:00 (−3.35, −3.26,
−3.42, −4.34)**, and is indistinguishable from zero at 00:00 (+0.10). **The assumption is
corroborated**: the local, activity-responsive component of Kandy's PM2.5 is strongly
bimodal and rush-hour timed, which is what a vehicle-dominated local source must look like
and what a 7-day-cycle source such as domestic cooking cannot.

Two consequences. First, e(t) moves from *imposed prior* to *prior with local observational
support*, which upgrades its claim tier. Second, a refinement is now visible: the observed
evening peak is **larger than the morning peak and later than e(t) places it** (maximum at
20:00 rather than 18:00). Adjusting e(t)'s evening lobe is cheap and is the one concrete
improvement this test identifies.

Caveats as F.22: FECT point sensors rather than the basin mean; the control is
month × hour × ventilation quintile rather than a full meteorological model; and sources
with no holiday cycle remain invisible, so this bounds the *timing* of the local component
without bounding its total magnitude.

## F.24 — does the anchor choice flatter the transfer validation? Partly, and not where expected (2026-08-06)

`scripts/anchor_choice_sensitivity.py`. Every headline transfer number comes from running
the model at a "two-sensor budget matching Kandy's scarcity", but the two anchors are not
drawn at random — the rule picks the **dirtiest and cleanest well-sampled stations**, with
full knowledge of every station's mean. Kandy's two sensors are simply wherever FECT put
them. If the extremal choice outperforms an arbitrary pair, the panel flatters Kandy.

Tested at Medellín (16 well-sampled stations, 2023, clean temporal split): the shipped
extremal pair against 30 random pairs, each scored on the stations it is not using.

| metric | shipped | random median | random p10–p90 | shipped beats |
|---|---|---|---|---|
| RMSE | 6.240 | 5.909 | 5.504–6.235 | **10%** |
| abs. level bias | 14.42% | 9.06% | 0.95–16.68% | **23%** |
| **seasonal r** | **0.970** | 0.960 | 0.944–0.968 | **97%** |
| diurnal r | 0.967 | 0.960 | 0.872–0.980 | 60% |
| hourly r | 0.588 | 0.588 | 0.549–0.608 | 47% |

**Two opposite effects, which an average across metrics would hide** — and the first
version of this script did exactly that, reporting a meaningless "47%, representative".

**Level and RMSE are PENALISED, not flattered.** The extremal pair is worse than 77–90% of
random pairs. The reason is a genuine estimator property: averaging the two extremes of a
skewed station distribution is a **biased estimator of the network mean**, whereas a random
pair is closer to an unbiased sample of it. **The panel's level claim is therefore
conservative rather than optimistic** — the opposite of the concern.

**Seasonal shape IS flattered**, at the 97th percentile. An arbitrary two-sensor city
should expect **seasonal r ≈ 0.960 (p10 0.944)** rather than the ~0.97 the extremal pair
achieves. The margin is about **+0.01**, so it does not overturn the seasonal claim, but the
scorecard's seasonal figures should be read as the favourable end of the achievable range,
and that qualification belongs in the paper.

**Scope.** Only the temporal anchor depends on sensor choice; `P_local` never sees a sensor,
so spatial rank is untouched. Absolute values here are not comparable to the scorecard
(clean temporal split, no amplitude sharpening, no full field build) — only the POSITION of
the shipped pair within the random distribution is meaningful. One city, 30 pairs; repeating
at Kathmandu (45 stations) would strengthen it.

## F.25 — the shipped interval, coverage-tested for the first time; and a pre-registered prediction (2026-08-06)

`scripts/kandy_interval_coverage.py`. Three coverage numbers circulate in this project and
refer to different objects: 0.865 (Stage A v3 LOMO, the hourly *anchor*), 0.707 (the
*sensorless* daily anchor, the basis for the forecast's 1.35× widening), and the coverage
of the interval the webapp and paper actually **ship** — which had never been computed.

Measured at the only place Kandy has observations, the two FECT sensor pixels (19,585
matched hours, 2019–2026):

| | coverage |
|---|---|
| **shipped 90% interval, as displayed** | **72.4%** |
| anchored tier 2019–2023 | 71.6% |
| extension tier 2024+ | 76.9% |
| by season | DJF 77.3 · MAM 81.7 · **JJA 61.7** · SON 65.4 |

That looks damning, and the first reading was that the intervals are too narrow. **They are
not.** The failure is almost entirely one-sided — observations fall *below* the lower bound
in 25.7% of hours and above the upper bound in only 1.9% — with a model-minus-observation
median of **+5.85 µg m⁻³ (+43%)**. That is a CENTRING offset, not a width problem, and it is
the documented area-versus-point geometry: a 1 km pixel mean sits above a point sensor
inside it, which is the same effect that makes the KOALA figure a valley-floor value rather
than a basin mean (gotcha #51), and which the residual-stage `b_FECT` constants (−9.105,
−13.749) already encode.

**Removing each sensor's own median offset restores nominal coverage:**

| sensor | offset | coverage after offset removal |
|---|---|---|
| Akurana (12451) | +5.16 | 87.2% |
| Hantana TR4 (33495) | +6.38 | 97.4% |
| **pooled** | | **91.5%** (nominal 90%) |

**The interval width is correct; the interval is not centred for a point comparison.** Both
statements should be made, because only stating the first would be misleading and only
stating the second would be alarming.

### A pre-registered prediction, and the reason it matters
The project's highest-value pending action is obtaining a local measurement — the CEA
archive, NBRO "Kandy 1", or a mobile campaign. **When that arrives, a naive comparison of
the shipped field against it will show the model roughly 40% high, and will look like a
catastrophic failure.** It is not: it is the expected area-versus-point offset, of order
**+5 to +6 µg m⁻³ at a valley-floor or ridge site**, and it must be removed before any
coverage or bias statement is made. Recording this in advance turns a future false alarm
into a confirmation, and makes the prediction falsifiable: an offset far outside that range
would indicate a genuine level error.

**Caveats.** The comparison is in-sample — T(t) is trained on and sharpened to these
sensors (gotcha #68) — so 91.5% is an optimistic bound on width calibration, not a
validation. Offsets are each sensor's own median, which is also in-sample. Two sensors,
one of them (Akurana) 0.93 km from its nearest pixel and outside the model's bounding box.
The seasonal pattern (JJA worst at 61.7%) is consistent with the wet-season high bias
already seen from three other directions (F.14, F.17, F.22) and is not explained away here.

---

## F.26 — spatial rank: bootstrap intervals, and the panel splits in two

`scripts/spatial_rho_bootstrap.py` → `results/figures/multicity/spatial_rho_bootstrap.csv`.
The scorecard reported Spearman ρ from 0.78 down to −0.06 with **no intervals**, and the
preprint built a substantive ordering on those differences. Station-resampled bootstrap
(10,000 draws) + permutation test:

| city | n_ranked | ρ | 90% CI | p |
|---|---:|---:|---|---:|
| Medellín | 16 | 0.78 | [0.49, 0.93] | 0.0006 |
| Tai'an | 11 | 0.68 | [0.16, 0.97] | 0.023 |
| Bogotá | 17 | 0.67 | [0.35, 0.87] | 0.003 |
| Baoji | 16 | 0.59 | [0.12, 0.91] | 0.020 |
| Kathmandu | 38 | 0.39 | [0.10, 0.64] | 0.016 |
| Yichang | 10 | 0.13 | [−0.63, 0.75] | 0.73 |
| Bazhong | 9 | 0.10 | [−0.58, 0.70] | 0.81 |
| Xichang | 9 | 0.07 | [−0.68, 0.94] | 0.87 |
| Chiang Mai | 11 | −0.06 | [−0.62, 0.47] | 0.86 |
| Chandigarh | **2** | — | — | not estimable |

- **The finding is bimodality, not an ordering: 5 of 9 estimable cities are resolvable,
  4 are indistinguishable from zero** (p > 0.7, intervals spanning nearly the whole range).
  Never again interpret the rank order among Yichang/Bazhong/Xichang/ChiangMai.
- **🔴 A REPORTING DEFECT FOUND: `n` in the scorecard is the HELD-OUT count, but ρ is
  computed on the subset falling inside the modelled domain**, and they differ a lot —
  Chiang Mai 31 → **11**, Medellín 22 → **16**, Bogotá 20 → **17**, Chandigarh 4 → **2**.
  The paper printed the larger number beside the spatial column. Both are now reported.
- Chandigarh's n_ranked = 2 independently confirms "not estimable" (gotcha #69).

## F.27 — the visibility corroboration IS independent (tested, not asserted)

`scripts/visibility_partial_correlation.py` → `decomp/visibility_partial_correlation.{csv,json}`.
The preprint called VCBI visibility "a fully independent check" because the variable is not
a model input. **That reasoning is incomplete**: visibility is driven by humidity and rain,
and ERA5 humidity and rain ARE model drivers, so the raw r = −0.46 could be a shared cause.
Tested by partialling out humidity (from the same METAR) and rain + BLH (from **the model's
own ERA5 drivers** — the conservative choice, since it removes exactly the variance the
model consumes):

| control | r | p |
|---|---:|---:|
| none (raw) | −0.456 | 5e-20 |
| station RH | −0.515 | 9e-24 |
| RH + ERA5 rain | −0.508 | 4e-18 |
| RH + rain + BLH + T | −0.448 | 7e-14 (n=257) |

- **SURVIVES, and strengthens slightly.** Context: visibility↔RH r = −0.40 while model
  PM↔RH r = −0.07, so the two are not sharing that pathway.
- ⚠ **VCBI reports NO precipitation** in the ASOS archive (same defect as SKMD, gotcha #60),
  so a METAR-only rain control is vacuous — the ERA5 substitution is not optional.

## F.28 — two claims cut down to size: embedding power, and the Yichang "regime boundary"

`scripts/reviewer_response_stats.py` → `results/figures/multicity/reviewer_response_stats.json`.
- **The AlphaEarth null is underpowered and the preprint over-claimed it.** Minimum
  detectable partial ρ at 80% power: **0.65** (Medellín n=17), **0.82** (ChiMai n=10),
  **0.96** (KTM n=6). The test excludes only a LARGE independent embedding signal. It was
  described as "most directly" supporting the information ceiling; it cannot carry that.
  **The five "independent lines" are honestly three** — two pairs were restatements.
- **No selection-time descriptor predicts the Yichang failure.** Its emission mix is
  *identical* to Tai'an's and Bazhong's (0.45/0.55/0.00) and its climate/emission/magnitude
  scores sit inside the passing range; only topographic similarity falls marginally outside
  (0.63 vs [0.66, 0.74]) — and that threshold would also flag **Medellín (0.65), the
  panel's best city**. ⇒ **the applicability map is DESCRIPTIVE on the diurnal axis, not
  predictive.** A screen built now would be post hoc; deliberately not done.
- **Level bias is systematic, not symmetric:** median **+7.6%**, median |bias| 7.6%,
  IQR [+2.5, +12.1]%, 7/10 within ±10%, and only Baoji (−4%) below observed. "−4% to +30%"
  is a range, not a summary; the model runs high nearly everywhere, and that belongs in the
  health caveat.

---

## F.29 — W10: the emission clock e(t) is FITTED, not assumed (evening lobe)

`scripts/kandy_emission_clock_fit.py` → `decomp/kandy_emission_clock_fit.{csv,json}`;
implemented in `src/stage1_satml/decomp/emission_profile.py` behind `EVENING_FIT`.

A public holiday removes local activity and leaves transboundary transport untouched, so
the holiday-minus-working-day difference **at hour h** estimates the local emission clock
at hour h. Met and season are controlled by differencing against (month × hour ×
ventilation-quintile) cells, so the comparison is *within* hour-of-day and cannot
manufacture a diurnal shape. 971 treated sensor-hours, 2018–2025.

| quantity | EDGAR prior | measured (bootstrap 90% CI) | verdict |
|---|---|---|---|
| morning peak hour | 08:00 | 08:00 | **prior CONFIRMED** |
| evening peak hour | 17:00 | 19:00 [17, 21] | shifted later |
| evening/morning ratio | 0.97 | 2.14 [1.17, 4.35] | **prior REJECTED** (CI excludes it) |

- The prior said morning ≈ evening; **the data say the evening lobe is roughly twice the
  morning one.** The CI excludes the prior value, so this is not merely uncertainty.
- **Correction is deliberately partial:** evening lobe only, +1 h shift and ×1.479 gain,
  **shrunk toward the prior** (w = 0.40) in proportion to the CI width, because ~40 treated
  hours per bin is thin. Morning lobe, night floor and overall shape stay EDGAR.
  Agreement with the measured clock rises **r = 0.49 → 0.755**.
- **e(t) moves from an imposed prior to a prior with a local observational correction.**
- ⚠ Every holiday figure is a **lower bound** on local emission: sources with no holiday
  cycle (cooking, waste burning, road dust) are invisible to the instrument.
- ⚠ Implementation trap found and fixed: shifting the lobe with `np.roll` **wraps** the
  tail back onto the window start and punches a hole at 14:00. The shift is in *time*, not
  a rotation — use index clamping.

**Rebuild + propagation.** `build_overlay_predictions` → `build_spatial_uq` →
`build_additive_field_v2` → `_v3` → `webapp_export`. G1 T-lock **exact (Δ 0.000)** every
year; exporter **QA PASS at 0.0017 µg/m³** (tol 0.25); wind parity 0.0005 m/s.

**🔴 ONE CONSEQUENCE NEEDING A DECISION.** The locked additive_v2 annual means move in the
third decimal: **19.750 → 19.752 · 19.092 → 19.092 · 17.077 → 17.079 · 18.754 → 18.755 ·
21.036 → 21.038** (max **+0.002 µg/m³**, 0.01%). This is 100× below the QA tolerance and
far below the precision at which any number is published (the paper quotes 19.8 … 21.0),
and no exposure, burden or figure changes at quoted precision. But the standing rule is
that the **locked 2019–2023 headline is untouched**, and this touches it. Either the rule
is relaxed for a change of this size, or `EVENING_FIT = False` restores the previous
profile exactly. **Recorded rather than absorbed silently.**

---

## F.30 — W7: the ventilated-hour floor eps0 does NOT transfer (and the relative form is the worse of the two)

`scripts/eps_floor_hierarchical.py` → `decomp/eps_floor_hierarchical.json`, on the per-city
slopes `flat_hour_residual_fit.py` already produced.

`additive_v3`'s floor was fitted at **one** city and carried to Kandy in **relative** form
(a fraction of the city's own mean accumulation amplitude), because that seemed the more
physical normalisation — never because it was tested. With three cities it is testable.

| city | own eps0 (µg/m³) | mean accumulation | relative | Spearman ρ | n |
|---|---:|---:|---:|---:|---:|
| Medellín | 5.65 | 14.20 | 0.398 | 0.31 | 1,751 |
| Kathmandu | 0.93 | 29.40 | 0.032 | **0.03** | 4,429 |
| Chiang Mai | 16.68 | 12.77 | 1.306 | 0.21 | 14,016 |

Hierarchical fit (same machinery as F.21; per-city SE from the slope t-statistic implied by
ρ and n, so a city whose flat-hour structure is not emission-shaped is shrunk hard):

| form | population µ | between-city τ | τ / median within-city SE | max/min |
|---|---:|---:|---:|---:|
| absolute | 7.74 | 6.57 | **14** | 18× |
| relative | 0.577 | 0.534 | **18** | **41×** |

- **eps0 is NOT a transferable constant in either form.** Between-city variation dominates
  within-city uncertainty by more than an order of magnitude, so a value fitted at one city
  predicts another's only weakly.
- **🔴 The relative normalisation the shipped model uses is WORSE behaved than the absolute
  one** (41× spread vs 18×) — the opposite of the assumption that justified choosing it.
- **Kandy: shipped 2.573 vs pooled 3.73, 90% predictive [0.00, 9.40].** The shipped value is
  **inside** the interval, so it is not contradicted — but it is one draw from a wide
  distribution, not a determined quantity, and must be described that way.
- ⚠ Kathmandu's ρ = 0.03 means its slope is essentially **unidentified**: there is no
  emission-shaped structure in its flat hours to fit. Its 0.93 is noise, not an estimate,
  and the pooling treats it accordingly.

**No code change follows, and that is the point.** The floor's *safety* was never in
question: the no-degrade gates pass at all three cities, the form is mean-zero so T-lock
stays exact, and `EPS_FLOOR = 0` recovers `additive_v2` byte-identically. What changes is
the **claim tier** — the floor's magnitude at Kandy is a weakly-determined transfer, and the
paper should say so rather than presenting 2.573 as fitted. W7 closes as a measured
limitation, not a fix.

## F.31 — B(t) vs NBRO refreshed: the binding constraint is the SEASON, not the sample

Re-ran `kandy_background_nbro_check.py` with the NBRO log now at **90 days**
(2026-05-08 → 08-06), double the 44 in F.14. Overlap with the model is **unchanged at 44
days**, because the *model record* ends 2026-07-21 (ERA5-Land latency), not because the
observations are short. Every number reproduces exactly: modelled B = 8.73 sits between the
network P10 (5.35) and median (11.49), ratio 1.12 to P25, daily r ≈ +0.37, ordering
floor < median < mean holds, and B is 1.51× the ×1.35-corrected floor.

**Consequence for the plan:** extending the driver record would add ~11 days of *wet-season*
overlap and cannot change the conclusion. The gate that matters is **DJF**, when the
transboundary background dominates and no external check exists at all. From **December
2026** this script becomes decisive; before then, more days are not more information.

---

## F.32 — 🔴 the spatial rank statistic is UNSTABLE to an undocumented sampling convention

`scripts/spatial_pairing_diagnostic.py` → `results/figures/multicity/spatial_pairing_diagnostic.json`.

The published spatial column averages modelled values over all modelled hours and observed
values over all observed hours **separately**. Averaging both over the *same* hours instead
(an inner join on `(hour, station)`) changes the answer by **0.404 on average and 0.882 at
worst**, in **both directions**.

| city | published | hour-matched | shift |
|---|---:|---:|---:|
| Chiang Mai | −0.06 | +0.82 | **+0.88** |
| Yichang | +0.13 | +0.95 | +0.82 |
| Xichang | +0.07 | +0.75 | +0.68 |
| Kathmandu | +0.39 | +0.93 | +0.54 |
| Bazhong | +0.10 | −0.22 | **−0.32** |
| Medellín | +0.78 | +0.78 | −0.00 |
| Bogotá | +0.67 | +0.63 | −0.04 |

**Verified, not assumed.** The unpaired route reproduces the published scorecard to
**0.000** on the same stations, years and domain filter, so the cause is **isolated to
hour-matching alone**; and the merge is strictly one-to-one (`any_duplicate_keys: false`),
so no join defect inflates it.

**Mechanism, supported but not established.** The two cities with the most *even* station
coverage move least (Medellín CV 0.30 → −0.003; Bogotá CV 0.34 → −0.039) while the most
uneven move most (Kathmandu CV 1.15 → +0.54; Bazhong CV 1.01 → −0.32). Uneven reporting
periods let a station's observed mean encode **when** it reported rather than where it is.

**⚠ Neither statistic is trustworthy.** Unpaired lets sampling periods contaminate the
observed means; **paired hands every station the temporal weighting of its own
observations**, so a model with strong temporal skill and *zero* spatial skill would still
score well — and this model's seasonal *r* is 0.94–1.00.

**Consequence: F.26's bootstrap intervals understate the true uncertainty**, because they
resample stations while holding the convention fixed. The paper's central spatial result
rests on a measurement choice nobody documented.

## F.33 — the anomaly estimator, and why its favourable result was NOT adopted

`scripts/spatial_common_hours_test.py`, pre-registered in
`docs/prereg_common_hours_spatial_2026-08-07.md` **with the author's prior published in
advance** (that the corrected number would come out *lower*).

E1 removes each hour's network mean from both series **within that hour**, so season,
diurnal cycle, episodes and the entire temporal skill of the anchor are differenced away
before any station mean is taken.

| pooled | published | hour-matched | **E1 anomaly** |
|---|---:|---:|---:|
| spatial rank | +0.372 | +0.696 | **+0.621** |

| gate | outcome |
|---|---|
| C1 validity (E1 vs common-hours) | **FAIL — unevaluable**: the 80% quorum is reachable at only 3 of 9 cities. Where computable, agreement was **0.011**, sign 3/3 |
| C2 E1 < paired − 0.10 | **FAIL** (+0.621 vs +0.696) — **the author's contamination hypothesis is refuted at pooled level** |
| C3 permutation control | **PASS** (null centred +0.001; E1 above null p95 +0.520) |
| C4 branch | 8 of 9 ≥ 0.40 → "revise upward" |
| C5 analogues | Chiang Mai **+0.22**, Kathmandu **+0.43** — the two most Kandy-like cities are the panel's weakest |

**NOT ADOPTED, for two reasons.** The registered validity gate did not pass, and rewriting
a rule after seeing a result one likes is the exact behaviour this project criticised in
its own manuscript (the Yichang screen). More substantively, **the permutation null's p95
is +0.520**: at 4–17 stations a rank of 0.5 arises by chance easily, so "8 of 9 above 0.40"
is arithmetic, not significance — per-city p-values were never registered.

**The author's prior was WRONG** (E1 landed well *above* the published values, not below)
and is recorded as such. Per-city significance and a sparse-network estimator are
registered in `docs/prereg_spatial_significance_2026-08-07.md`; C1's design error — a gate
unreachable on the coverage this panel has — is the lesson applied there.

**Standing consequence either way:** three defensible estimators give +0.372, +0.696 and
+0.621 on identical data. That instability is now a reportable limitation of the spatial
claim, independent of which value is eventually adopted.

---

## F.34 — ✅ the spatial estimator is FIXED and VALIDATED; the claim stands, restated

`scripts/spatial_significance_test.py`, pre-registered in
`docs/prereg_spatial_significance_2026-08-07.md` (prior published in advance: *middle
branch expected, Chiang Mai expected to fail significance* — **both correct**).

| city | E1 ρ | p | null p95 | E1 τ | **E3 τ** | pairs | n |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baoji | **+0.83** | 0.000 | +0.43 | +0.67 | +0.67 | 55 | 16 |
| Bogotá | **+0.80** | 0.000 | +0.41 | +0.63 | +0.58 | 134 | 17 |
| Xichang | **+0.78** | 0.016 | +0.58 | +0.67 | +0.73 | 15 | 9 |
| Tai'an | **+0.72** | 0.016 | +0.52 | +0.56 | +0.57 | 23 | 11 |
| Medellín | **+0.66** | 0.007 | +0.43 | +0.50 | +0.56 | 119 | 16 |
| Yichang | +0.60 | 0.080 | +0.55 | +0.47 | +0.52 | 21 | 10 |
| Bazhong | +0.54 | 0.308 | +0.77 | +0.33 | +0.17 | 12 | 6 |
| Kathmandu | **+0.43** | 0.007 | +0.27 | +0.33 | +0.29 | 675 | 38 |
| Chiang Mai | +0.22 | 0.512 | +0.53 | +0.16 | +0.23 | 47 | 11 |
| Chandigarh | not estimable (<4 ranked stations) | | | | | | |

| gate | outcome |
|---|---|
| **D2 validity** — E3 vs E1_τ | **PASS**, and emphatically: pooled \|d\| = **0.002**, sign **9/9** |
| **D3** small-n inflation | **PASS**: r(E1, n) = **−0.175** — if anything *negative*, so skill is not an artefact of network size |
| D1 significant at p<0.05 | **6 of 9** |
| **D4 decision** | **6 of 9** significant *and* ≥0.40 → **middle branch: the claim STANDS, restated on a corrected estimator** |
| D5 analogues | Chiang Mai **+0.22, p = 0.51 (not significant)** · Kathmandu +0.43, p = 0.007 |

- **The estimator is now sound.** Two constructions that remove the temporal confound by
  different routes — per-hour network-mean removal, and pairwise concordance on co-observed
  hours only — agree to **0.002** across all nine cities. E3 needs no global quorum, which
  is precisely the design error that made C1 unevaluable (F.33) and is not repeated.
- **The headline claim does not change: partial and regime-bounded.** What changes is that
  it now rests on a statistic that cannot launder temporal skill, with per-city
  significance attached. The tally moves from *4 of 9 clearing the 0.40 gate* to
  **6 of 9 significant and above 0.40**.
- **Bazhong (+0.54, p=0.31) and Yichang (+0.60, p=0.08) are NOT significant** despite
  respectable ρ — small networks (n=6, n=10) with null p95 of +0.77 and +0.55. Reporting ρ
  without its own null would have overstated both.
- **🔴 The Kandy-relevant reading is unchanged or slightly worse.** Kandy's closest
  climatic analogue, Chiang Mai, is **not significant**; Kathmandu is significant but the
  weakest of the six. The cities most like Kandy remain the ones where the spatial pattern
  is least recoverable, and that is the line the transfer argument depends on.

**ACTION — the paper's spatial column should be replaced** by E1 with per-city p-values,
the tally restated as 6 of 9, and the sampling instability of F.32 disclosed as a
limitation. The qualitative conclusion the manuscript already draws survives intact.

---

## F.35 — 🔴 the fuel crisis has the WRONG SIGN: a shipped assumption is contradicted

`scripts/kandy_activity_shocks.py`, pre-registered in
`docs/prereg_activity_shocks_2026-08-07.md` (prior published: S1–S3 expected to hold, S4
least confident). Same estimator as F.22 — residuals against (month × hour × ventilation)
cells, ordinary working days only, controls are the **same calendar weeks in 2019 and 2023**.

| shock | n | effect | implied f | p |
|---|---:|---:|---|---:|
| COVID lockdown (2020-03-20 → 05-11) | 911 | **−57.8%** | 0.72–0.96 | <1e-4 |
| Fuel crisis, peak (2022-03 → 09) | 294 | **+18.0%** | — | 0.001 |
| Fuel crisis, full (2021-11 → 2022-09) | 522 | **+34.6%** | — | <1e-4 |

- **S1 PASS.** The lockdown effect (−57.8%) dwarfs the fixed-holiday effect (−15.6%),
  which is what must happen if the holiday instrument measures local activity.
  **This retrospectively supports F.22.**
- **S4 FAIL, as registered in advance.** Implied f of 0.72–0.96 is far above the converging
  band [0.26, 0.53]. The registered caveat fires: in 2020 lockdowns across India suppressed
  the **transboundary** source too, so this is not a clean local experiment. **Upper bound
  only; it says little about f.**
- **🔴 S2 FAIL, and this is the finding. The fuel crisis has the OPPOSITE SIGN.**
  Concentrations were **higher** during severe fuel scarcity, not lower. The mechanism is
  fuel **substitution**, not activity reduction: Sri Lanka's 2022 crisis brought daily
  multi-hour power cuts (diesel generators) and cooking-fuel scarcity (biomass and waste
  burning). Less traffic, more dirty combustion — and the second dominated.
- **CONSEQUENCE FOR A SHIPPED QUANTITY.** `FRAC_LOCAL_YEAR` hand-lowers f for **2021
  (0.21)** and **2022 (0.20)** on the reasoning that the fuel crisis cut local emissions,
  and the manuscript defends those values as "reasoned rather than fitted". **The data
  contradict the reasoning for those two years** — local emissions plausibly *rose*. The
  2020 lowering (0.25) is untouched by this and remains defensible.
- ⚠ **MY OWN GATE ERROR, again.** S3 compared |Sunday| < |fuel| < |lockdown| on
  **magnitudes without checking sign**, so a *positive* fuel effect satisfied an ordering
  test meant to require a negative one. It printed PASS; it is **void**, and reported as
  failed on inspection. Same class as the A2 error (F.33 arc) — **a directional gate must
  test direction.**
- **Bounds:** n = 294 on the peak window; the cell control removes meteorology and season
  but **not** year-to-year changes in the regional background, so part of the +18% could be
  a dirtier 2022 inflow rather than local substitution.

**Net:** 2 of 4 predictions met. The holiday line of evidence for f **survives and is
strengthened** by S1; the fuel-crisis rationale in `FRAC_LOCAL_YEAR` **does not survive**
and should be withdrawn from the manuscript's defence of the year-to-year variation.

---

## F.36 — Test B re-run on the corrected estimator: 2/3, and the gate that mattered FAILED

`scripts/zone_contrast_corrected.py`. Test B (zone contrast on terciles of the traffic
emission surface) passed **3/3** on hour-matched means. Those means are contaminated
(F.32–F.34), so the test was re-run on per-hour network-mean-removed anomalies. **Gates
unchanged** — only the contaminated input was replaced.

| city | obs Δ | model Δ | sign |
|---|---:|---:|---|
| Bogotá | +7.20 | +2.78 | agree |
| Baoji | +6.50 | +5.99 | agree |
| Xichang | +3.18 | +2.73 | agree |
| Bazhong | +2.93 | +0.69 | agree |
| Tai'an | +1.95 | +0.49 | agree |
| Medellín | +1.49 | +1.39 | agree |
| Kathmandu | +1.21 | +4.54 | agree |
| Yichang | +0.97 | −0.13 | **disagree** |
| Chiang Mai | −0.17 | −0.08 | agree |

| gate | result |
|---|---|
| B1 slope > 0, CI excludes 0 | **PASS** — +0.720 [+0.070, +1.591] |
| B2 sign agreement ≥ 7 of 9 | **PASS** — 8 of 9 |
| **B3 recovers ≥ 2 station-null cities** | **FAIL** — only Bazhong |

- **B3 was the point of the test**, and it failed. The motivation for reporting zones was
  that aggregation might recover structure where per-station ranking finds none. It does
  not: of the three cities not significant under the corrected estimator, Bazhong recovers,
  **Chiang Mai's contrast is negligible (|Δ_obs| = 0.17)** and **Yichang disagrees in sign**.
- **What survives is real but redundant.** Zone contrast is genuine (B1, B2) — but it adds
  no information where the station rank is already absent, so it is a coarser restatement of
  the same signal, not a rescue. **It must not be presented as a validated replacement for
  the station rank**, and the paper's spatial claim stays as F.34 left it.
- B1's interval is wide and its lower bound is barely positive (+0.07); the slope of 0.72
  again indicates the model's zone contrast is **under-dispersed by roughly a third**,
  consistent with the amplitude deficit found independently at Medellín.
- **Prior scored:** I predicted a lower slope (wrong — +0.643 → +0.720), sign agreement
  below 9/9 (right — 8/9), B1 surviving (right) and B2 marginal (wrong — it passed cleanly).
  Two of four elements correct.

**Consequence:** the "measure at a coarser resolution" idea is closed. Combined with Test A's
falsification (pooled stagnant−ventilated gap −0.001), **neither re-measurement route
rescues spatial skill at the cities that lack it.** The ceiling survives both attempts to
argue it away, which is a stronger statement of it than before they were tried.

---

## F.37 — 🔴🔴 THE EXTENSION TIER (2024–2026) CANNOT REPRESENT THE EPISODE REGIME

`scripts/extension_tier_audit.py` → `decomp/extension_tier_audit.{csv,json}`.
Triggered by a user report of "physically implausible" estimates after 2023. **The report
is correct, the defect is structural, and it had never been tested for.**

**What is fine.** Annual means, monthly means (within ±12% of the locked climatology, with
the seasonal shape intact), diurnal swing (ratio 0.99 to locked), diurnal phase (peak 07,
trough 14), background ratio and accumulation fraction. On every *aggregate* diagnostic the
extension tier looks healthy — which is why this survived a year of review.

**What is broken: the tail.**

| threshold | locked (hours/yr) | extension (hours/yr) | ratio |
|---|---:|---:|---:|
| > 35 µg/m³ (WHO IT-1) | 955 | 635 | 0.66 |
| > 45 | 310 | 108 | **0.35** |
| > 55 | 84.8 | **0.5** | **0.01** |
| > 65 | 21.8 | **0** | **0.00** |
| > 75 | 6.0 | **0** | **0.00** |

The extension T maxes at **56.5 µg/m³ across all three years** (2024 56.5 · 2025 54.8 ·
2026 56.0) — a ceiling at the **99.2nd percentile of the locked distribution**. Roughly
**69 hours per year that the locked years do produce are unrepresentable**. Three
consecutive years capping within 1.7 µg/m³ of each other is the signature of a structural
ceiling, not of weather.

**Root cause, confirmed in the code.** `sharpen_to_locked()` in
`kandy_driver_tier_build.py` corrects the GBM's regression-to-the-mean by multiplicative
(hour-of-day) and (month) **climatological** factors. Its own docstring states the limit
plainly: *"Phase and synoptic variability are untouched."* The synoptic scale — which is
exactly where episodes live — was never corrected. Three compounding mechanisms:
1. a quantile GBM predicts **leaf averages**, which shrinks the tail at every timescale;
2. tree ensembles **cannot extrapolate** beyond training targets, so the locked maximum is
   a hard ceiling and the achieved ceiling sits well below even that;
3. the tier is **lag-free**, removing the persistence by which multi-day episodes build.

**Secondary defect (audit check E).** Mean 90% interval width is **27.3 µg/m³ in the
extension against 29.4 in the locked years** — *narrower* on the tier that is *more*
uncertain. The `infl` coverage inflation is fitted on the locked period and the q05/q95
heads are damped by the same GBM, so the interval neither widens for extrapolation nor
compensates for the damped centre.

**Tertiary (2026 only).** 2026 is built **ERA5-ONLY**: no GEOS-CF chemistry prior and
**no boundary-layer height**. BLH is the primary driver of stagnation, so 2026 has no direct
information about the mechanism that produces episodes. The fallback was validated on level,
monthly *r* (0.996) and hourly *r* (0.807) — **never on the tail**, the same blind spot.

**Also: 2026 is a PARTIAL year** (January–July, 4,825 h). Its record mean of 20.68 must not
be compared with a full-year mean; on the common Jan–Jul window the locked years average
20.97, so 2026 is unremarkable rather than high.

**CONSEQUENCE.** Anything the extension tier says about **episodes, exceedance hours, or
health burden after 2023 is wrong and wrong in a specific direction — too clean.** A user
browsing 2024–2026 in the explorer would reasonably conclude Kandy stopped having haze
events. Aggregate/annual statements from the tier remain defensible.

**RECOMMENDED FIX (not yet implemented).** Quantile delta mapping: map the extension T's
empirical distribution onto the locked distribution per month, which restores the tail while
preserving the GBM's ranking of which hours are dirty. It is the standard tool for exactly
this bias and can be **validated by holding out a locked year**. It fixes the *distribution*,
not necessarily event *timing*, and that distinction must be stated. Until then the tier
should be labelled **"climatological — does not resolve episodes"** wherever it is shown.

---

## F.38 — the nocturnal hotspots and flat daytime: what is real, and what is a hand-set constant

User report: "midnight high pollution ... daytime pollution very low." Investigated at three
levels. **Two of the three findings exonerate the model; the third does not.**

**1. The basin-mean diurnal shape is CORRECT — verified against observation.** Normalised
against the FECT record (2019–2023), model and observed agree to <0.07 at every hour:

| | night 00–04 | midday 12–15 | night/midday |
|---|---:|---:|---:|
| observed | 0.865 | 0.756 | **1.145** |
| model | 0.847 | 0.763 | **1.110** |

**Kandy's nights genuinely are dirtier than its middays**, and the model is if anything
slightly *flatter* at night than the measurements. ⚠ **This refutes gotcha #54**, which
states deep-night 00–05 is "≈ the daily MINIMUM". It is not: the observed minimum is at
14:00 (0.725) and deep night sits ~15% above it. **Gotcha #54 must be corrected.**

**2. Daytime flatness is largely real.** The transport amplitude
`a(t)=clip(e(t)·18/(wind·BLH), 0, 0.5)` has a median of **0.007–0.013 at 10:00–15:00** —
essentially zero — so midday fields are near-uniform at the basin mean. Deep convective
mixing genuinely homogenises a basin this size; the `additive_v3` ε-floor exists precisely
because *perfectly* flat was wrong, and midday max/min is now 1.13 rather than 1.00.

**3. 🔴 The extreme hourly contrasts are set by a HAND-CHOSEN CONSTANT, not by physics.**
Per-hour spatial statistics (2023) show maximum pixels reaching **100–203 µg/m³ on nights
and rush hours whose basin mean is only 20–30**, with max/min ratios of **3.5–4.7 at
06–07 and 18–23** against **1.13 at midday**. The cause is the cap:

| hours | % of hours where a(t) SATURATES at 0.5 | median raw a(t) |
|---|---:|---:|
| 06–07 | 8.9 – 12.7% | 0.09 – 0.10 |
| 18–21 | 8.1 – 15.6% | 0.09 – 0.12 |
| 10–15 | 0.0% | 0.007 – 0.013 |
| all | 3.6% | 0.031 |

On the ~4% of hours that saturate — calm, shallow boundary layer, rush-hour emissions — the
amplitude is **not determined by the meteorology at all**; it is pinned at the constant
`0.5`, which is roughly **10× the median** and was hand-set, never calibrated. **Those are
exactly the hours a user notices**, and their spatial amplitude has no empirical support.
This is `A_transport`, the layer the paper already ships as an unvalidated scenario — but
the paper quotes the *annual* core/edge contrast (1.20–1.25×) while the hourly maps reach
**4×**, and that gap is nowhere disclosed.

**⚠ Our own W10 change interacts with this.** The measured evening-lobe correction raised
e(t) at 20:00–23:00 by **+42%** (and lowered 00:00–04:00 by 17%), which raises the
late-evening amplitude further. The correction is evidence-based (F.29) and was already
shrunk toward the prior, so it stands — but it makes disclosure of the nocturnal amplitude
more pressing, not less.

**ACTIONS.** (a) correct gotcha #54; (b) disclose that hourly contrast reaches ~4× where the
annual figure is 1.2×, and that the cap is a prior; (c) consider deriving the cap from the
zone-contrast slope (F.36 measured the model under-dispersed at 0.72 on *annual* zone
contrast, which is the only empirical handle on amplitude the project has); (d) the ε-floor
and the cap are the two hand-set constants that shape every hourly map and neither is
calibrated.

---

## F.39 — ✅ the extension tail is CORRECTED and validated; disclosure added

`scripts/extension_tail_correction.py` (+ `extension_interval_widening`), fixing F.37.

**Method.** Not a naive remap of the extension distribution onto the locked one — that
would erase genuine interannual differences. Instead the estimator's **own damping
signature** is measured and inverted: leave-one-year-out over 2019–2023 gives out-of-sample
driver-GBM predictions for years where truth is known; per month, the gap between predicted
and true quantiles gives a multiplicative factor **indexed by quantile**; that factor is
applied to the extension years by the quantile each hour occupies within its own month. The
ranking of hours is untouched, so real year-to-year differences survive (2025 remains the
cleanest year).

**Validation — leave-one-year-out, fit on four, correct the fifth:**

| | raw | corrected | truth | corrected/truth |
|---|---:|---:|---:|---:|
| mean | 18.71 | 19.07 | 19.05 | **1.00** |
| p99 | 44.60 | 54.89 | 54.85 | **1.00** |
| max | 55.76 | 79.54 | 84.84 | 0.94 |
| hours > 55 | **1.8** | **88.2** | **84.8** | **1.04** |

Both gates pass (p99 within 10%, level within 5%). Applied:

| year | mean | p99 | max | h>55 |
|---|---|---|---|---|
| 2024 | 19.13 → 19.48 | 46.5 → 56.1 | 56.5 → **91.7** | 1 → **101** |
| 2025 | 17.72 → 18.09 | 44.9 → 54.9 | 54.8 → **75.3** | 0 → **88** |
| 2026 | 20.68 → 21.01 | 45.3 → 55.3 | 56.0 → **79.4** | 2 → **50** |

Interval widening applied in the same pass: extension mean 90% width **27.3 → 41–49 µg/m³**
against 28–30 locked, so the less-certain tier is now the wider one. **All five audit flags
cleared**; T-lock exact; exporter **QA PASS 0.0015**; 18 invariant tests pass.

**🔴 THE LIMITATION, and it must travel with the number.** This corrects the **marginal
distribution** of episodes, **not their timing**. Hourly correlation with truth is unchanged
by construction (0.836–0.890) — the correction cannot improve the GBM's ranking of which
hours are dirty. A specific hour in 2024–2026 is indicative of conditions, not a reading.
Weakest year is 2022 (corrected 101 vs 154 true hours >55; max 71.6 vs 102.8): it contained
an exceptional episode beyond the reach of a quantile correction.

⚠ **Process defect caught during the rebuild:** `kandy_extension_fields.py` defaults to
`--years 2024 2025`, so the first rebuild silently left **2026's field stale against its
corrected anchor** — the gotcha #65/#70 family again (a partial rebuild desyncs a consumer).
Verified fixed: 2026 basin now 21.01, matching its corrected T.

**Disclosure shipped**, not just recorded: the exporter's `tier_note` and the public method
page now state that the estimator under-produced episodes, that the correction fixes
frequency and not timing, and — separately — that the hourly spatial *sharpness* is set by an
uncalibrated bounded constant (F.38), so the annual ~1.2× contrast is the defensible figure
and a single dramatic hour is not.

---

## F.40 — the partition plan STOPS at step 1 (as registered) — but confirms the premise and adds a fourth line on f

`scripts/panel_reference_partition.py`, pre-registered in
`docs/prereg_partition_identification_2026-08-07.md`. The plan was to make the local fraction
an **estimated, time-varying** quantity, validated by transfer the way every other claim is.
Step 1 built the thing an estimator would be scored against: a reference partition at the
panel cities, using their dense networks and a leakage-free core/periphery split by traffic-
emission percentile, with an hourly Lenschow lower envelope across peripheral stations.

**Gate outcome: 3 of 10 cities pass; P4 required 5. THE PLAN STOPS.**

| gate | result |
|---|---|
| P1 periphery genuinely peripheral (sep ≥ 0.25) | **8 of 8** — separation 0.62–0.68 everywhere |
| P3 not a network-geometry artefact | **8 of 8** |
| **P2 reference physically ordered (≥95%)** | **3 of 8** — the binding failure |
| **P4 ≥5 cities pass** | **3 of 10 → FAIL** |

Passing: Kathmandu (98% ordered), Medellín (97%), Bogotá (99%). Failing on P2: Yichang (75%),
Chiang Mai (78%), Tai'an (86%), Bazhong (87%), Baoji (95%, just short). Not estimable:
Xichang (0 usable hours), Chandigarh (1 peripheral station).

**🔴 The most interesting result is WHY P2 fails, and it is not a detail.** P2 fails when the
peripheral 10th percentile *exceeds the network mean* — i.e. the periphery is not cleaner
than the core. That happens in **13–25% of hours at five cities with real, dense networks**.
This is the same pathology as Kandy's `B > T` in 28.5% of hours (F.17), which we have been
treating as an artefact of our own background construction. **It is not.** An
observation-based background, built from actual peripheral monitors, incurs it too.
Background/increment decomposition at *hourly* resolution appears to be intrinsically
ill-posed a fifth to a quarter of the time, whatever the background is built from.

Note the confound, which is why this is not stated more strongly: the passing cities are the
three with the largest peripheral groups (13, 6, 5 stations) and the failures cluster at 4.
With four peripheral stations a 10th percentile is a noisy statistic. So P2's failure is part
physics and part sampling, and this design cannot separate them.

**✅ The descriptive output — the reason step 1 was worth running anyway.**

| quantity | value |
|---|---|
| mean `f_ref` across passing cities | **0.398** |
| mean seasonal swing in `f` | **0.196** (median month_max/month_min **1.66×**) |
| mean diurnal swing in `f` | **0.170** |

- **The user's physical premise is CONFIRMED by measurement.** The partition moves by a
  factor of ~1.7 within a year and by 0.17 across the day. **A per-year constant is
  inadequate**, and that is now measured at real cities rather than argued.
- ~~**A FOURTH independent line lands on ~0.4.**~~ **⚠ WITHDRAWN — see F.41.** `f_ref = 0.398` was reported here as corroborating the ~0.4 estimates. The daily-resolution re-run gives **0.243** from the same method, same cities, same stations — differing only in averaging window. The reference is **resolution-dependent across nearly the whole disputed range**, so neither value may be used as evidence on the level. The claim should not have been made before its robustness was tested. The three genuinely independent lines (coherence floor, hierarchical fit, NBRO) are unaffected — none depends on this reference.

**What is NOT permitted from here.** Relaxing P4 to 3, or loosening the reference definition,
after seeing that exactly three cities passed, would be the post-hoc screening this project
criticised in its own review. Any follow-up — restricting to dense networks and accepting
N=3, or defining the reference at daily rather than hourly resolution — is a **new
pre-registration** with its prior published in advance, and must state that the earlier design
failed first.

**Prior scored:** I predicted P1–P4 would pass (**wrong** — P2 fails at 5 cities) and that
`f_ref` would vary roughly two-fold by regime (**right** — 1.66×).

---

## F.41 — the partition route CLOSES: both references fail, the coarse-CTM alternative fails, and the capability is now stated

### The daily reference also fails (`prereg_partition_daily_2026-08-07.md`)

Registered as a second attempt with **thresholds unchanged**, testing whether the hourly
failure (F.40) was sampling noise. **Q4: 4 of 10 pass, 5 required. As registered there is no
third attempt; the route is abandoned.**

| city | peri n | hourly ordered | daily ordered | Δ |
|---|---:|---:|---:|---:|
| Bogotá | 6 | 99% | 100% | +1 |
| Medellín | 5 | 97% | 100% | +3 |
| Baoji | 6 | 95% | **99%** | +4 |
| Kathmandu | 13 | 98% | 98% | +0 |
| Bazhong | 4 | 87% | 93% | +6 |
| Tai'an | 4 | 86% | 89% | +3 |
| Chiang Mai | 4 | 78% | 83% | +5 |
| Yichang | 4 | 75% | **75%** | **+0** |

**D1 — noise or physics? Mostly PHYSICS.** Sparse networks improved +4 points, dense +2, but
**every sparse city stayed below the gate** and Yichang did not move at all. The Lenschow
reference requires local sources concentrated in the core; where the dominant source is
**regional biomass smoke (Chiang Mai)** or **peri-urban industry (Yichang)**, the periphery is
not background — it is a source region. 🔴 **Chiang Mai, Kandy's closest analogue, fails at
both resolutions**, so even a passing panel would not have contained the cities that resemble
the target.

**🔴 The registered falsifier fired.** The prereg stated: *"If the daily mean f_ref moves far
from the 0.398 measured hourly, the reference is resolution-dependent and NEITHER version
should be trusted."* It moved to **0.243** — spanning nearly the whole disputed range, from
the shipped 0.244 to the ~0.4 the other lines support. **F.40's "fourth independent line" is
withdrawn** (corrected in place). What IS robust across both resolutions is the **shape**:
seasonal swing **1.66× hourly, 1.67× daily**.

**Prior scored:** Q2 improving (right, but insufficient), Q4 passing with 5–7 (**wrong**, 4),
D1 mostly noise (**wrong**, mostly physics).

### The coarse-CTM urban-increment alternative also fails, and instructively

The EMEP/GAINS/uEMEP family is the closest established analogue: a coarse CTM supplies the
regional background, a finer model the urban increment. GEOS-CF at 0.25° physically cannot
resolve a 15 km city, so its cell over Kandy *is* regional air. Tested over 16,090 hours:

| | mean | ratio to T | B < T | daily r |
|---|---:|---:|---:|---:|
| GEOS-CF raw | 46.3 | 2.35× | 15.7% | 0.445 |
| GEOS-CF × 0.536 | 24.9 | 1.26× | **39.9%** | 0.445 |

Implied `f` by month: **+0.18 (Feb) to −1.75 (Oct)**, annual mean **−0.61**. The background
exceeds the total 60% of the time. **Why it fails is the point:** EMEP's regional level is
trusted because it is validated against a continent of rural monitors; GEOS-CF's level at
Kandy is not, and our only scaling factor (0.536) was calibrated to match **total** observed
PM, not background. A total-calibrated number used as a background guarantees incoherence.
The method is sound; its critical ingredient — a trusted rural level — is precisely what
Kandy lacks. A remaining variant (learn GEOS-CF's *rural* bias at panel cities and transfer
it) is **not attempted**: the monsoon months are where the bias is worst and where transfer
is least likely to hold.

### ✅ CAPABILITY STATEMENT — what this project can and cannot claim about the split

- **CAN: the annual level, to roughly ±0.1.** Three independent lines converge — coherence
  floor **≥0.41**, hierarchical fit **0.392 [0.258, 0.525]**, NBRO instrument **0.446**. None
  depends on the failed reference. The shipped 0.244 is refuted.
- **CAN: the seasonal shape, qualitatively.** ~1.66× swing within a year, measured at panel
  cities and stable across resolution.
- **CANNOT: a validated time-varying f.** Not for want of an estimator — for want of anything
  credible to score one against. Two reference designs failed; the coarse-CTM route failed.
- **PROBABLY CANNOT AT ALL: an hourly split.** `B > T` in 28.5% of hours at Kandy was assumed
  to be our construction's defect. **It is not** — observation-based references at cities with
  real networks incur 13–25% hourly and 7–25% daily. Hourly background/increment decomposition
  appears close to ill-posed however the background is built. **This is a transferable finding
  worth publishing**, and it is stronger than the caveat it replaces.
- **The decisive input is unchanged:** one monitor upwind of or inside the basin.

**Standing rule from here: no sixth background reformulation.** Five rebuilds, two reference
designs and one coarse-CTM route have now failed on gates set in advance. The partition is
reported as an annual bound with an interval, its seasonal variation described qualitatively,
and its hourly form declared unidentifiable.

---

## F.42 — external reviewer, two claims: one real defect in the locked tier, one stale UI text

An external reviewer reported that the local fraction reaches zero in 2019 and questioned
whether the model obeys advection–diffusion–deposition. Both checked against code and data.

### Claim 1 — zero local fraction. CORRECT, and the framing was wrong on our side.
`T ≤ B` in **24.9% of 2019 hours** (2% in January to **63% in October**; 34% of midday
hours). The reviewer's physical argument is the decisive one and we had not stated it:
**traffic, cooking and waste burning are continuous, so the local increment at an emitting
location is strictly positive at every hour, including in rain** — rain changes removal, not
emission. Therefore `B ≥ T` **is not a physical state**; it is evidence that **B is
over-estimated for that hour**. Reporting "0% local" describes the atmosphere incorrectly;
the defect is in the background estimate, not in the emissions.

| tier | spatial spread on `B ≥ T` hours | fully flat |
|---|---:|---:|
| `additive_v2` (locked, paper) | **0.00 µg/m³** | **100%** |
| `additive_v3` (shipped, app) | 1.33 µg/m³ (max/min 1.225) | 0% |

- 🔴 **The locked paper tier renders exactly flat on a quarter of 2019.** The ε-floor (F.11)
  already fixes this in the served tier; the scored tier still carries it and the manuscript
  should say so.
- 🔴 **A STALE UI STRING was found and fixed:** the app said *"the map is uniform by
  construction"* — true of v2, **false of the v3 tier actually served**, where the pattern
  floor keeps structure. The text described a tier the user was not looking at.
- **Fixed:** the app no longer prints a zero. It states that the background is over-estimated
  for that hour, that local emissions continue, that the true local share is above zero and
  unquantified, and that the map still carries the local pattern.

### Claim 2 — "does not follow advection–diffusion–deposition". HALF WRONG, and the other half matters.
`terrain_transport.py` **does** solve `u·∇C − ∇·(K∇C) + λC = S` on the SRTM terrain, with
channelled flow, katabatic drainage, ridge-suppressed diffusivity, a first-order deposition
loss (`LAM = 3e-6 s⁻¹`) and a road-network source; its three parameters were calibrated
across ten monitored valleys. So the claim that there is no such physics is wrong.

**But the shipped field is not a solution of that equation**, for four reasons now stated
publicly on the method page:
1. the solve is **steady-state** — no `∂C/∂t`, so the field has **no memory** and cannot
   accumulate an episode (the same structural gap as F.37);
2. only the **shape** is used — `C / C.mean()` clipped to [0.4, 4.0]; the solver's
   concentrations are discarded;
3. the **level is imposed**, not conserved — the T-lock replaces mass conservation with a
   statistical constraint;
4. the framework is a **source-apportionment decomposition**, not a chemical transport model.

**Actions taken:** new public `#physics-status` section stating all four points and the
design reason; the split section rewritten around the "background over-estimated, not
emissions absent" framing. **Action outstanding:** the manuscript should carry the same
statement, and should disclose that the *locked* tier is exactly flat on ~25% of hours.

---

## F.43 — ✅ THE COHERENCE CAP: the partition is fixed by physics, and f is ~0.48

An external reviewer supplied the argument that eight internal attempts had missed: **local
sources emit continuously, so at an emitting location the local increment is strictly
positive at every hour** — rain changes removal, not emission. Therefore `B ≤ T` always, and
a background at or above the total **is not a physical state**; it is an over-estimated
background. Reporting "0% local" described the atmosphere incorrectly.

**Implementation.** The background is daily-flat, so the constraint has a closed form — it is
the coherence bound already derived in F.17: cap each day's `B` at `(1 − F_MIN) ×
min_hour(T)` for that day. Daily-flat structure is preserved, a local share of at least
`F_MIN` is guaranteed at every hour, and it is a **derived** constraint, not a new degree of
freedom. Fires on 50–77% of hours.

**F_MIN is not a tuning knob, and the sweep proves it:**

| F_MIN | pooled f | zero-local hours | B_JJA/B_DJF |
|---:|---:|---:|---:|
| 0.00 | 0.477 | 2.57% | 0.390 |
| **0.02** | **0.483** | **0.08%** | **0.388** |
| 0.05 | 0.492 | 0.08% | 0.385 |
| 0.08 | 0.502 | 0.08% | 0.382 |

`f` moves by 0.025 across a fourfold change in the parameter. **The coherence constraint
alone forces f ≈ 0.48.** F_MIN = 0.02 was chosen as the smallest value that removes the
defect (0.08% residual vs 2.57% at zero), not to hit a target.

**f = 0.483 is consistent with every independent line**: above the coherence floor (≥0.41),
inside the hierarchical interval (0.392 [0.258, 0.525]), near the NBRO instrument (0.446),
inside the literature bracket [0.15, 0.50). The shipped 0.244 was below its own floor in
nine months of twelve and is now retired.

**Nothing else moves.** T-lock holds exactly: basin means 19.752 / 19.092 / 17.079 / 18.755 /
21.038 are unchanged, as are exposure and burden. Only the partition label changes — from
~25/75 to **~48/52**. Exporter QA PASS 0.0015; 18 invariant tests pass.

**🔴 The cost, stated plainly.** The wet/dry background ratio moves to **0.388** against an
observed reference of 0.53, and F.18 rejected a rebuild at 0.349 on exactly this gate. This
is the four-constraints-on-three-degrees-of-freedom problem resolving, and it is resolved in
favour of physics for a stated reason: the reviewer's constraint is **absolute**, whereas
W2's 0.53 is by our own record *"the softest line — inferred from FECT totals by origin, and
that inference itself assumes a local share, so a larger true f biases it."* **A reference
derived under an assumed f cannot adjudicate against changing f.** W2 is therefore
reclassified from a gate to a diagnostic, and the tension is disclosed rather than hidden.

**This supersedes the standing rule against a sixth background reformulation.** That rule was
written to stop re-deriving the background's *level* by fiat. This is not that: it imposes a
physical constraint the construction was violating, with the free parameter shown to be
inconsequential.

## F.44 — the background's advective half: the trajectory archive is 6-hourly and the builder was throwing that away

Registered in `docs/prereg_hourly_background_and_learnable_decomp_2026-08-18.md` (W1) before
running, with gates and a prior published in advance.

**The defect.** `d1_trajectories_850.parquet` holds 11,676 rows over 2,919 days — arrivals at
00/06/12/18 UTC. `build_additive_field_v2.daily_class()` collapsed it with `.mode()` to one
class per day. Measured on the archive:

| quantity | value |
|---|---:|
| days on which the trajectory **sector** changes within the day | **24.8%** |
| days on which the binary **marine flag that sets B's level** flips within the day | **11.3%** |
| marine rate by arrival hour (00 / 06 / 12 / 18) | 0.292 / 0.293 / 0.292 / 0.287 |

So on roughly one day in nine the background genuinely steps mid-day and the model held it
flat by construction — and the discarded signal carries **no diurnal cycle**, only episodic
transitions. That bounds the claim honestly: this makes `B` step when the air mass steps; it
does not make `B` breathe with the boundary layer.

**Why this is not a sixth background reformulation.** It introduces no new free parameter and
does not re-derive the level. `B_MARINE`, the continental-level solve, the annual-mean lock and
the F.43 cap are unchanged in form. `SUBDAILY_ORIGIN = False` reproduces the daily-mode path.

**Dry-run result (`scripts/w1_subdaily_origin_check.py`, no product written).**

| year | f shipped | f sub-daily | Δf | hours changed | mean \|ΔB\| | max \|ΔB\| |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 0.4702 | 0.4710 | +0.0008 | 42.3% | 0.06 | 5.78 |
| 2020 | 0.4660 | 0.4670 | +0.0009 | 40.0% | 0.08 | 12.22 |
| 2021 | 0.4985 | 0.4985 | −0.0001 | 28.3% | 0.07 | 7.31 |
| 2022 | 0.5014 | 0.5013 | −0.0001 | 25.8% | 0.10 | 17.33 |
| 2023 | 0.4776 | 0.4760 | −0.0016 | 52.7% | 0.20 | 13.04 |

- **W1-G3 PASS** — max |Δf| = 0.0016 against a registered 0.02.
- **🔴 W1-G4 FAILS AS REGISTERED.** The gate said coherence-cap activation must not increase.
  It rises in every year: 72.6→73.2%, 74.8→75.3%, 48.8→49.7%. Mechanically expected — letting
  `B` step within the day sends some blocks above the daily-flat value, so the cap binds more
  often — but the gate is the gate, and it is recorded as failed rather than reinterpreted.
  **Decision escalated, not taken.**

**🔴 THE STRUCTURAL FINDING, which is larger than W1 itself: `B` is CAP-DOMINATED.** The F.43
coherence cap fires on **49–75% of hours**. Over most of the record the shipped background is
not the origin-conditioned construction at all — it is `(1 − F_MIN) × min_hour(T)`. That
explains why a real 6-hourly signal (72–76 class transitions a year, 26–53% of hours changed,
single-hour differences up to 17 µg/m³ **before** capping) moves the annual partition by
0.0016: the cap absorbs almost all of it. Any future work on `B` should treat the cap, not the
origin construction, as the operative term.

## F.45 — ❌ NULL: the entrainment signature is a month-composition artefact, and the dilutive half of the hourly split is now closed BY MEASUREMENT

Registered as W2 in the same document, with the prior published in advance
(**"~55–60% that the sign is as predicted, and the effect is small"**) and the gate written as
directional, following the F.35 recorded gate error.

**Hypothesis.** Local emissions accumulate at the surface, so a deepening boundary layer
dilutes them. A regional layer advected *aloft* is entrained downward as the boundary layer
deepens, so the surface background *rises*. If Kandy's transboundary load arrives lofted, the
two components carry opposite-signed BLH responses — a second identifying dimension, and the
only route by which the dilutive half stops being ill-posed without new instruments.

**Design.** Observed FECT PM2.5 against ERA5 BLH, cell-demeaned within
(sensor × month × hour-of-day) so day-to-day BLH variation is compared at a fixed clock time
and the emission clock `e(t)` is held constant. Elasticity = slope of demeaned log PM on
demeaned log BLH, stratified by the 6-hourly 850 hPa class. Rain excluded, bootstrap over days.

**Result: W2-G1 passes and W2-G2 kills it.**

| stratum | n hours | slope continental | slope marine | difference | 90% CI |
|---|---:|---:|---:|---:|---|
| primary, 07–13 LT, co-occurring months | 1,717 | −0.312 | −0.785 | **+0.473** | [+0.129, +0.855] |
| **placebo, composition-matched** | 1,717 | — | — | **+0.390** | [+0.139, +0.737] |
| placebo, balanced 50/50 | 1,717 | — | — | **−0.025** | [−0.328, +0.337] |
| JJA only (both classes genuinely present) | 680 | −0.998 | −1.098 | +0.101 | [−0.540, +0.918] |
| DJF only | 996 | — | — | not estimable | marine n = 10 |

*Provenance:* all rows from `scripts/entrainment_signature_test.py` (seed 20260818, 200 placebo
draws), outputs `data/processed/decomp/entrainment_signature.{csv,json}`. The placebo pair was
added after the registered single placebo fired, to identify *why*; that made the test stricter,
not looser. A seed-7 mechanism diagnostic run first gave +0.430 / +0.018 for the two placebos
against the script's +0.390 / −0.025 — seed noise on 200–300 draws, no change to any verdict.

The two placebos are the whole result. A **balanced** random label gives ≈ 0, so the estimator
is unbiased. A label that merely preserves **each month's observed marine frequency** recovers
+0.430 — almost the entire observed +0.473 — with no air-mass information in it at all. The
contrast is therefore a **month-composition effect**: marine blocks are drawn disproportionately
from monsoon months, and those months have steeper elasticities for reasons unrelated to
entrainment. Cell-demeaning removes month differences in the *level* but not in the *slope*.
And in JJA, the one block where both air masses genuinely co-occur, the contrast is +0.10 with
a CI spanning zero.

**Verdict: NULL.** No evidence that the surface background carries an entrainment signature
distinguishable from the local increment's own BLH response.

**Why this is worth more than the argument it replaces.** F.41 declared the hourly split
"probably unidentifiable" on the strength of failed constructions. The dilutive half is now
closed **by measurement**, with a mechanism: `T(t) ≈ [A + E(t)] / BLH(t)` — two terms, one
driver, one observable. This is a sixth entry in the same family as the five spatial nulls, and
it is transferable: any city attempting a background/increment split from a total-only series
faces the same collinearity.

**What would reopen it** is unchanged and specific: an independent tracer with a different
source signature. Hourly NO₂/CO from the CEA Kandy AQMS is the identified route — short-lived,
near-purely local, and *not* collinear with boundary-layer dilution in the way PM2.5 is.

**Per the registered stopping rule, this was not iterated into a pass.**

## F.46 — what actually sets f: the anchor's DIURNAL AMPLITUDE, not F_MIN. The 0.48 is right; its stated precision is not

`scripts/f_diurnal_amplitude_sweep.py`. Prompted by F.44's finding that the F.43 coherence cap
sets `B` on **49.7–75.3%** of hours (reproduced independently here). If the cap is
`(1 − F_MIN) × min_hour(T)` and it binds most of the time, then `f` is largely a function of
`mean(daily-min T) / mean(T)` — **the anchor's diurnal range** — and F.43's sweep varied the
wrong quantity.

**Sweep of the diurnal amplitude, with every daily mean preserved exactly** (so the annual
level and the T-lock are untouched and only the within-day swing changes):

| amplitude | 2019 | 2020 | 2021 | 2022 | 2023 | **pooled f** |
|---:|---:|---:|---:|---:|---:|---:|
| 0.7 | 0.412 | 0.405 | 0.423 | 0.417 | 0.426 | **0.417** |
| 0.8 | 0.430 | 0.425 | 0.446 | 0.443 | 0.442 | **0.437** |
| 0.9 | 0.449 | 0.445 | 0.471 | 0.471 | 0.458 | **0.459** |
| **1.0 (shipped)** | 0.471 | 0.467 | 0.499 | 0.501 | 0.476 | **0.483** |
| 1.1 | 0.495 | 0.491 | 0.528 | 0.534 | 0.495 | **0.509** |
| 1.2 | 0.522 | 0.515 | 0.559 | 0.569 | 0.516 | **0.536** |
| 1.3 | 0.551 | 0.542 | 0.592 | 0.606 | 0.538 | **0.566** |

**f moves 0.0995 across ±20% amplitude — four times the 0.025 that F.43's fourfold `F_MIN`
sweep produced.** The insensitivity F.43 reported is real and remains true; it is simply
insensitivity to the parameter that was varied, not to the quantity that carries `f`.

`dailymin_over_mean` at amplitude 1.0 is 0.562–0.639 by year, and `f` tracks it directly.

**🟢 THE HEADLINE SURVIVES; THE PRECISION DOES NOT.** Even at amplitude 0.7 — a 30% reduction
in the diurnal swing — `f = 0.417`, still above the F.17 coherence floor (0.410), inside the
hierarchical interval (0.392 [0.258, 0.525]) and near the NBRO instrument (0.446). **The
shipped 0.244 is not reachable anywhere in the sweep**, so its retirement is robust. What
changes is the interval: **anchor-amplitude uncertainty alone contributes about ±0.05 to `f`**,
and that term is currently absent from every reported figure.

**Where the amplitude comes from, and what it therefore inherits.** `sharpen_T_diurnal.py` maps
`T` onto the observed FECT diurnal swing, so the amplitude is an **observation, not a hand-set
constant** — a materially better position than a free parameter, and F.38 verified the shape
against observation (model night/midday 1.110 vs observed 1.145). But it is an observation from
two low-cost sensors whose calibration is **W5-open**. A purely multiplicative calibration error
preserves the diurnal ratio and so would not move `f`; an **additive offset error would**, since
it changes the ratio. `f` therefore carries a W5 dependency that has never been stated.

**Reported for completeness, and explicitly NOT a live uncertainty:** a uniform rescale of `T`
(0.8× → 1.25×) moves pooled `f` 0.442 → 0.535. This cannot occur in the shipped chain — `T` is
re-anchored per year to van Donkelaar and `b_annual` is derived from the same van Donkelaar, so
the ratio is pinned by construction. Included as a consistency check on the sweep machinery.

**Recommendation (not applied — the change bears on a shipped headline number):** report `f` as
**≈0.48 with a stated ±0.05 anchor-amplitude term**, and add the amplitude dependency to F.43's
sensitivity statement so it is not read as parameter-free.

**W1-G4 waiver (recorded 2026-08-18).** F.44's W1-G4 failed as registered: sub-daily origin
raises coherence-cap activation by 0.5–0.9 pp per year. Waived with disclosure rather than
reinterpreted, on the following grounds — (a) the rise is mechanically entailed, since letting
`B` step within the day sends some blocks above the daily-flat value; (b) F.46 shows the cap is
already setting `B` on 49.7–75.3% of hours, so a sub-percentage-point change in activation is
immaterial to any reported quantity; (c) W1-G3 passed with max |Δf| = 0.0016 against a
registered 0.02. **The gate is recorded as FAILED, not as passed** — the waiver is a decision
taken above the gate, not a redefinition of it. The case for shipping W1 is correctness (the
archive is 6-hourly and was being discarded), not effect size.

## F.47 (step 1 of 3) — the decomposition is differentiable, and T-lock is structural under autodiff

`scripts/diff_decomp.py`. W4 of the 2026-08-18 registration. This entry covers the forward
model and its registered invariant only; fitting against held-out city networks (W4-G2) and the
profile-likelihood identifiability pass (W4-G3) are not yet run.

Five hand-set constants are re-expressed as parameters, each stored unconstrained and mapped
through a bijection into its physical box so an optimiser never has to respect a hard bound:
`kappa` (0.15), `a_cap` (the hard-coded transport amplitude cap, 0.50), `eps0` (2.573),
`w_evening` (the F.29 shrinkage weight, 0.40) and `s_exp` (the emission-surface exponent,
implicitly 1.0 and never tested).

| check | result |
|---|---|
| **W4-G1 — T-lock under autodiff**, 12 random draws across the full parameter box | max \|basin mean − T\| = **5.7e-06** against a registered tolerance of 0.05 → **PASS** |
| `eps0 = 0` recovers additive_v2 | max difference **1.9e-05** (float32) |
| gradient of the basin mean w.r.t. every parameter | max **3.9e-06** — the level is parameter-independent |
| 18 invariant tests after the builder edits | **pass** |

**Why W4-G1 passing matters more than it looks.** `P_local` is normalised to unit spatial mean
*inside* the graph, so the basin mean returns `T(t)` for **any** parameter values. T-lock is
therefore not a property that survives fitting — it is a property no parameter setting can
break, and the third row makes that explicit: the level carries no gradient at all. That is what
makes fitting these constants safe, and it is the reason a differentiable version is worth
having rather than a free-form learned field.

**🔴 A bug in my own prototype, caught by the registered gradient check.** `w_evening` was
declared as a parameter and never wired into the forward model, so it received no gradient. The
check that found it exists only because the plan called for gradient flow to *every* parameter.
Fixed by forming `e(t) = (1−w)·e_prior + w·e_fit` inside the graph — the F.29 shrinkage — rather
than accepting a pre-blended clock. The self-test now **raises** on any parameter absent from
the graph, so a dead parameter cannot silently be reported as unidentified later.

**Early identifiability signal, on synthetic fields only.** Gradients of spatial spread:
`s_exp` **+1.73**, `eps0` +0.236, `a_cap` +0.146, `kappa` +0.142, **`w_evening` +0.00096** —
three orders of magnitude below `s_exp`. This is a property of the equation, not of Kandy: the
draws are random fields, whereas real inputs carry the `s_emit`/`c_conf` collinearity that made
`kappa` unidentifiable at N=1 (2026-06-01). It should not be quoted as an identifiability
result. It does align with the registered prior that `s_exp` and `a_cap` are the best
candidates to identify, and it predicts `w_evening` will not.

## F.47 (step 2a) — the differentiable assembly reproduces additive_v2 EXACTLY; v3 does not, and the reason is a documented invariant that does not hold

`scripts/diff_decomp_reproduce.py`. Before fitting anything, the differentiable re-expression
must reproduce the shipped product at shipped parameters — otherwise a fit optimises a different
equation than the one the project ships.

| tier | result (150 sampled hours x 256 pixels, 2022) |
|---|---|
| **additive_v2**, `eps0 = 0` | max \|diff\| **0.000000** µg/m³ · T-lock 1.5e-06 · **exact** |
| **additive_v3**, `eps0 = 2.573` | max \|diff\| **1.469** · mean 0.013 · p99 0.207 · **not reproduced** |

**The v2 result is the one that matters for W4:** the increment split, the mean-zero floor and
the T-lock are verified bit-exact against the shipped product, so the assembly layer of the
differentiable model is correct.

**Chasing the v3 gap found something else.** Comparing the two *shipped* products directly over
the full 2022 field (2.24 M pixel-hours):

| hours | n | max \|v3 − v2\| | mean |
|---|---:|---:|---:|
| `acc50 > eps0` — **floor provably inactive** | 1,802,240 | **1.313** | 0.0028 |
| `acc50 <= eps0` — floor active | 440,320 | 5.676 | 0.1308 |

The second row is the floor doing its job. The first row should be **zero** — and the reason it
is not turned out to have nothing to do with the field equation. **See F.47 (step 2b) below: the
shipped v3 artefact is stale, and every documented claim about v3 is correct.**

🔴 **A WRONG DIAGNOSIS I PUBLISHED AND THEN RETRACTED, recorded because the retraction is the
useful part.** On the strength of the table above I concluded that the pattern clip to
`[0.30, 3.20]` broke the documented "structured hours are byte-identical" claim, and I edited
that claim in four files — `README.md` (git-tracked and public), `CLAUDE.md` gotcha #57, model
reference §IV.1.3c and the COMBINED build. The clip explanation was **false**: measurement shows
the recovered pattern never leaves `[0.30, 3.20]` (0.0000% of 2.24 M pixel-hours), so the clip
is inert. All four edits were **reverted** once the real cause was found. The lesson is the
gotcha-#70 family in a new dress: **I diagnosed a stored artefact as if it were the code that
produces it.**

**Cause, and it is deliberate rather than a defect.** `build_additive_field_v3.py` clips the
recovered pattern to `[0.30, 3.20]` and renormalises (its own comment: bounding stops an extreme
injected value from driving a pixel negative). That clip applies to **every** hour, not only the
ventilated ones it was reasoned about, so wherever the true pattern leaves the box — which the
F.38 transport-cap saturation makes routine at 06:00 and 19:00, where core pixels reach 100–203
µg/m³ on a 20–30 basin — v3 departs from v2. The mean deviation is 0.0028 µg/m³, far inside the
0.25 QA tolerance, so nothing shipped is wrong. **The claim is what is wrong**, and it appears
in a git-tracked public file.

## F.47 (step 2b) — ✅ GAP CLOSED: the differentiable model is exact, and the SHIPPED additive_v3 artefact is STALE

Resolved by running the builder instead of reasoning about it. `build_v3_from_v2` was re-run for
2022 from the **stored** `additive_v2` and `B_background_hourly_2022_v2` into a temporary file,
and everything was compared over the full year (2,242,560 pixel-hours):

| comparison | max \|diff\| | mean | hours affected |
|---|---:|---:|---:|
| differentiable reconstruction **vs freshly built v3** | **0.000e+00** | 0.000e+00 | 0 |
| freshly built v3 **vs shipped v3 parquet** | **2.059** | 0.0139 | **2,370 of 8,760** |
| freshly built v3 vs v2, **floor-inactive** hours | **5.7e-14** | 1.3e-15 | 0 (float noise) |
| freshly built v3 vs v2, floor-active hours | 3.744 | 0.0716 | — (the floor working) |

**Row 1 closes W4 step 2a for v3.** The differentiable re-expression reproduces the builder
bit-exactly, including the q95 inversion, the (month, local-hour) climatology substitution, the
clip and the renormalisation. Both tiers are now verified: v2 exact, v3 exact.

**Row 3 vindicates the documented claim.** Against a *freshly built* v3, structured hours are
byte-identical to `additive_v2`. The four documentation edits made on the opposite conclusion
were reverted.

**Row 2 is the real finding: the shipped 2022 `additive_v3` parquet cannot be reproduced from
its own stated inputs by its own code.** It differs on 27% of hours, by up to 2.06 µg/m³.

**Why nothing caught it, which is the transferable part.** The T-lock holds *exactly* for the
stale file (per-hour basin mean vs `additive_v2`: max difference **0.000000** over all 8,760
hours), because the discrepancy is a **mean-preserving spatial redistribution**. Every guard the
project owns — the G1 basin-mean gate, the exporter QA (which derives its anchors from whichever
field it is handed), the 18 invariant tests, annual/seasonal/diurnal diagnostics — is invariant
to exactly this class of error. File timestamps look correct and ordered (`v2` and `B` at
00:31, `v3` at 01:00 on 2026-08-10, the F.43 coherence-cap rebuild). **A stale artefact that
preserves the invariant is undetectable by any check currently in the suite.**

**Consequence, scoped honestly.** Basin means, exposure, burden and every annual or seasonal
figure are untouched (T-lock). What differs is the hourly spatial pattern on 27% of hours, at a
mean of 0.014 µg/m³ and a maximum of 2.06. The webapp payload is exported from v3, so the live
explorer is serving the stale pattern on those hours. **Not repaired here** — a rebuild is the
obvious fix but `SUBDAILY_ORIGIN` is now live in the v2 builder, so rebuilding v3 alone would
desync the pair (gotcha #65/#70). The correct repair is a full v2+v3 rebuild with the exporter
QA re-run, which is a shipping decision.

**New guard needed (gotcha #80):** a reproducibility check that rebuilds a product from its
stored inputs and diffs it against the artefact on disk. The determinism the model reference
leans on (Part VII-b.8, Part X: *"the same artifacts produce byte-identical outputs"*) is
asserted for the release repo but never verified for the framework's own products.


## F.48 — P2 (monotone skill under added data) DEMONSTRATED on real networks, and the first value-of-information curve

`src/modular/{budgets,observation,constraints,shrinkage}.py` + `scripts/budget_ladder_demo.py`.
Implements MODEL_SPECIFICATION.md sections 5-6. Tests: 41 passing (18 existing + 23 new).

**Method.** A densely monitored city is a **budget simulator**: the information budgets are
synthesised by withholding stations. Each rung is fitted ONLY on its own admissible stations and
every rung is scored on a common set of stations that no rung ever saw. Richer rungs enter
through cross-validated shrinkage `x = x_parent + w (x_child - x_parent)`, with folds grouped by
DAY (hours within a day are not independent).

**Result — held-out RMSE, ug/m3:**

| city | held-out stns | `Bud0` sensorless | `Bud1` 2 sensors | `Bud2` 6 sensors | `Bud3` + background |
|---|---:|---:|---:|---:|---:|
| Medellin (seed 0) | 8 | 14.28 | **8.94** | 8.94 | **3.99** |
| Medellin (seeds 1-3) | 8 | 14.0-14.5 | 9.2-9.6 | 9.2-9.6 | 4.9-5.7 |
| Kathmandu | 14 | 48.96 | 47.67 | 47.52 | **45.42** |
| Chiang Mai | 11 | 18.58 | 17.29 | 16.98 | **8.56** |

**P2 PASS in all six runs** — RMSE never rises as the budget grows.

**The `Bud2` row is the mechanism working.** At Medellin seed 0 the six-sensor rung was *worse*
than its two-sensor parent (9.35 vs 8.94 raw), and the shrinkage weight went to **w = 0.000**,
collapsing it to the parent **exactly**. That is P3 appearing as the limiting case of P2, on real
data rather than in a unit test — and it is the structural guard the Sim2Real N=2 failure lacked.

**The value-of-information finding, which is the substantive result:**

1. **The first two sensors buy the most** (Medellin -5.3 RMSE; ChiMai -1.3; KTM -1.3).
2. **Going from two sensors to six buys almost nothing** (-0.00 to -0.30 everywhere). Sharp
   diminishing returns *within an information type*.
3. **A different KIND of information — background — buys another large step** (Medellin -4.9,
   ChiMai -8.4, KTM -2.1), the largest single gain in two of three cities.

This directly informs the data-acquisition priority: **more local sensors of the same kind are
not the lever; a background/regional constraint is.** It agrees with the project's independently
reached conclusion that `B(t)` is the binding constraint.

**Caveats, stated because they bound the claim:**
- `Bud3`'s "regional" stream is the **outer ring of in-city stations**, a proxy. True rural
  stations correlate less with in-city held-out stations, so this likely **overstates** what a
  real regional network buys. The number is a mechanism demonstration, not a calibrated estimate.
- This is a **level/temporal** result at network-mean scale. It says nothing about spatial skill,
  where five independent tests found no signal.
- The affine correction standing in for each rung is deliberately crude; what is demonstrated is
  the **ladder mechanism**, not a specific estimator.
- Kathmandu gains little at every rung (48.96 -> 45.42), consistent with its extreme seasonal
  smoke regime and heterogeneous low-cost network.
- Single seed at Kathmandu and Chiang Mai.


## F.49 — the paired v2+v3 rebuild: gotcha #80 CLOSED, W1 landed, published quantities unmoved

Backup taken first (`data/processed/decomp/_prerebuild_20260818/`, 15 products, 828 MB) because
W1-G5 registered a condition on the locked tier.

**What was rebuilt and why together.** `SUBDAILY_ORIGIN` (W1, F.44) was live in the v2 builder
and the shipped v3 artefact was stale against its own builder (gotcha #80, F.47). Both are
fixed by one paired rebuild; rebuilding either alone desyncs the pair (gotcha #65/#70).

| check | result |
|---|---|
| G1 / T-lock, all 5 locked years | **Δ = 0.000** |
| basin means | **19.752 / 19.092 / 17.079 / 18.755 / 21.038** — identical to the F.43 record |
| **W1-G5** (locked-tier annual means) | **PASS — delta 0.000000** on every year and both tiers |
| **gotcha #80 reproducibility** | rebuild-from-stored-inputs vs artefact on disk: **max 0.000e+00**, 0 of 8,760 hours differ → **REPRODUCIBLE** |
| invariant suite | **59 passed** |

**`eps0` moved 2.573 -> 3.692** as expected and previously recorded: it is `0.398 x` the mean
accumulation amplitude, and the F.43 coherence cap raised that amplitude from 6.465 to 9.276.
This is the shipped tier's floor, not a free parameter.

**What actually changed, stated at full strength.** Annual, seasonal and every published mean
are **untouched** (T-lock). Individual pixel-hours moved by up to **26.7 ug/m3** (mean 0.015,
2022), concentrated on the ~11% of days where the air mass flips mid-day — which is precisely
what W1 was built to do. Anyone who has previously inspected a specific hour in the explorer
will now see a different value for it; nobody reading an annual or seasonal figure will.

**Still outstanding after this rebuild:** the webapp payload is exported from v3 and has NOT
been re-exported, so the live explorer still serves the pre-rebuild field. Re-export plus the
QA gate, then deploy, is a separate step and a shipping decision — deliberately not taken here.


## F.50 — the budget-ladder PILOT: P2 holds, and the biggest step is NOT the one I predicted

⚠ **SUPERSEDED IN PART BY F.84–F.85 (2026-08-23).** The step gains here were measured against a `Bud0` that used one of its three admitted streams. Re-validated numbers: **17.9 / 0.1 / 40.6** from `Bud0c`.

`scripts/modular_validation.py`, 39 CNEMC cities with >= 10 stations, 1,095 days each, scored on
held-out stations no rung ever sees. Registered in `prereg_modular_validation_2026-08-18.md`
(v1) — **superseded by v2 before these results were read, so this is a PILOT and is labelled as
such everywhere.**

### Result

| rung step | median RMSE reduction | IQR | median shrinkage weight |
|---|---:|---|---:|
| `Bud0 -> Bud1` (+2 stations) | **2.9%** | 0.4 - 6.6 | 0.825 |
| `Bud1 -> Bud2` (+6 stations) | **0.0%** | 0.0 - 0.1 | 0.050 (zero in 17 of 39 cities) |
| `Bud2 -> Bud3` (+background ring) | **43.6%** | 37.8 - 44.9 | **1.000** (>0.9 in 33 of 39) |
| `Bud0 -> Bud3` total | **44.3%** | | |

Per stratum (relief x level), the pattern is identical in every estimable cell — e.g. the
largest, moderate-relief/mid-level (n = 10): **19.04 -> 15.29 -> 15.23 -> 8.61**. In
flat/high (n = 3) the two station rungs do *nothing at all* (20.64 -> 20.64 -> 20.64) and the
background rung still cuts 38%. `confined/low` (n = 2) is **not estimable** and is reported as
such, never pooled (V3).

### Gates

- **V1 (P2 monotonicity, >= 90%): PASS at 97%** — 38 of 39. The one violation is named as
  registered: **city038**, where `Bud2` is worse than `Bud1` by 7e-4 ug/m3 — numerical, not
  substantive, and reported rather than rounded away.
- **V2 (Bud0 sensorless): PASS**, asserted in code per city.
- **V3 (per-stratum): honoured**, including the non-estimable cell.
- **V4 (diminishing returns): CONFIRMED, and more sharply than registered.**

### 🔴 My published prior was WRONG, and the direction matters

I registered: *"`Bud0 -> Bud1` will be the largest step in most cities."* It is not. It is worth
**2.9%**, the second station rung is worth **nothing**, and the background rung is worth
**43.6%** — an order of magnitude more than both station rungs combined.

**More local sensors in the basin buy almost nothing; a background constraint buys nearly
everything.** That is the quantified form of a conclusion this project reached qualitatively and
repeatedly — the binding gap is an upwind/regional measurement, not more in-basin instruments —
and it is now measured on 39 independent city networks rather than argued. It also reorders the
data-acquisition priorities: **NBRO (regional network, `Bud3`) outranks additional in-basin
sensors**, and the CEA reference monitor's value is mostly in identifying `b_k`, not in level.

### Caveats that keep this a pilot

1. **Frame is CNEMC-only** — 39 cities, one country, one network, latitude 20-47.7 N. **No
   Kandy-relevance or cross-regime claim may be drawn from it** (v2 gate V5).
2. **`Bud3`'s background is a proxy, not an independent instrument**: the outer-ring 10th
   percentile of the *same* network. Some of the 43.6% is therefore "more of the same network"
   rather than "genuinely regional information". The v2 OpenAQ arm cannot fix this either; only
   a true rural/regional network can, which is exactly what NBRO is.
3. P2 passing is partly **by construction** (`w = 0` is in the search space). The informative
   quantity is the weight distribution above, not the pass rate.


## F.51 — the budget ladder on the WIDENED frame: 47 cities, 4 latitude bands, 32 countries

⚠ **SUPERSEDED IN PART BY F.84–F.85 (2026-08-23).** Step gains re-measured against a spec-compliant `Bud0c`; the band ordering flipped. The **confound findings stand** — only the magnitudes changed.

`scripts/modular_validation_all.py`, registered in `prereg_modular_validation_v2_2026-08-18.md`
(option C, Amendment 2). 48 cities usable, **47 scored**, 32,396 city-days. Both arms share an
identical feature set; `lat/lon` are EXCLUDED from `Bud0` because band IS latitude and a model
given latitude could learn the band contrast it is meant to be tested on.

### Step gains (median % RMSE reduction, per band)

| step | deep-tropical | tropical | subtropical | temperate |
|---|---:|---:|---:|---:|
| `Bud0 -> Bud1` (+2 stations) | **38.5** | 16.0 | 22.7 | 24.9 |
| `Bud1 -> Bud2` (+6 stations) | **1.6** | 0.1 | **0.0** | **0.0** |
| `Bud2 -> Bud3` (+background) | 28.1 | 49.1 | **52.5** | 41.4 |

**V4 confirmed on the wide frame, and it is the most robust result here: a second tranche of
in-city stations buys essentially nothing, in every latitude band, on two continents and 32
countries.** The background rung is the largest single step in three bands of four.

`Bud0 -> Bud1` is much larger here (16-38%) than in the CNEMC pilot (2.9%, F.50). The cause is a
deliberate design change, not a contradiction: the pilot's `Bud0` had `lat/lon` among its
features and this one does not, so this `Bud0` is weaker and leaves more for local stations to
recover. **The pilot's 2.9% should not be quoted; it was measured against a `Bud0` that could
identify the city.**

### 🔴 A second registered prior REFUTED

I registered: *"`Bud0` will be materially worse in the deep tropics than in the temperate band,
because the LOCO training pool is dominated by mid-latitude cities."*

Normalised skill (`RMSE / city mean PM2.5`, so bands with different pollution levels compare):

| band | n | median PM2.5 | normalised `Bud0` | normalised `Bud3` | total gain |
|---|---:|---:|---:|---:|---:|
| subtropical | 10 | 32.4 | 0.695 | 0.295 | 61.6% |
| tropical | 13 | 27.1 | 0.708 | 0.323 | 58.9% |
| **deep-tropical** | **13** | **23.4** | **0.792** | **0.348** | **52.5%** |
| temperate | 11 | 26.2 | **1.194** | 0.371 | 55.6% |

**The temperate band is the WORST for the sensorless rung, not the deep tropics** — 1.194
against 0.792, i.e. `Bud0`'s error there exceeds the city's own mean concentration. The deep
tropics sit mid-pack. The prior was wrong in direction.

### BLH sensitivity, run because coverage differs by band

BLH completeness is 0.898-0.948 by band (max gap 5.1 pp, smaller than the within-band spread),
so the ladder was run twice. Dropping BLH **flips the top-two ordering** (subtropical 0.695 vs
tropical 0.708 - a 0.013 gap, not a real distinction) but leaves the load-bearing statements
untouched: temperate remains clearly worst (1.248), deep-tropical remains mid-pack, and every
step gain moves by under 3 points. **Reported: the temperate deficit is regime, not driver
completeness. Not reported: any ranking among the three better bands.**

### Gates

- **V1 (P2 monotonicity, >= 90%): PASS at 98%** - 46/47. Violation named as registered:
  **cluster 3147** (South Africa).
- **V2**: asserted in code, per city.
- **V3**: every number above is per band; nothing pooled without its cell.
- **V4**: confirmed (above).
- **V5**: any Kandy-relevance claim rests on the **deep-tropical cell alone, n = 13**, 13
  countries. Its numbers are the bolded row; they may not be pooled with the rest.
- **V6**: OpenAQ cities are low-cost-sensor-heavy; sensor class is in the manifest and the
  split-by-class report is still outstanding.

### What this does NOT establish

The `Bud3` background is still an outer-ring proxy from the SAME network in every city, so the
large background gains measure "more of the same network" as well as genuinely regional
information. That confound is unchanged from F.50 and only a true rural/regional network can
settle it - which is exactly what NBRO would be at Kandy.


## F.52 — 🔴 V6 FIRES: sensor class is aliased with latitude band, and it changes the F.51 reading

⚠ **Magnitudes superseded by F.85 (2026-08-23).** The instrument-class confound itself **stands**.

The registered LCS-honesty gate (V6) was the last one run and it found the third confound of
this workstream.

### Sensor class is not balanced across bands

| band | LCS | mixed | reference |
|---|---:|---:|---:|
| **deep-tropical** | **9** | 1 | 3 |
| tropical | 2 | 1 | 10 |
| subtropical | 1 | 1 | 8 |
| temperate | 2 | 1 | 8 |

The deep-tropical cell is **69% low-cost-sensor**; every other band is reference-dominated.
**Band and instrument class are therefore aliased**, exactly as latitude and country were before
Amendment 2 — a different axis, the same defect.

### And class changes the headline

| class | n | normalised `Bud0` | normalised `Bud3` | **median `w_Bud2`** |
|---|---:|---:|---:|---:|
| reference | 29 | 0.754 | 0.300 | **0.000** |
| LCS | 14 | 0.829 | 0.348 | **0.900** |
| mixed | 4 | 1.161 | 0.358 | 0.775 |

**"A second tranche of in-city stations buys nothing" is a REFERENCE-NETWORK result.** At
low-cost-sensor cities the second tranche carries a shrinkage weight of **0.900** — it helps
substantially. The mechanism is unsurprising once seen: LCS carry large per-device error, so
averaging more of them cuts noise, whereas reference monitors are already precise and a second
tranche adds little. The deep-tropical band's anomalous `Bud1 -> Bud2` gain (1.6% against 0.0%
elsewhere, F.51) is the same effect, not a latitude effect.

### What this does to the F.51 claims

- **The V4 finding stands but must be conditioned**: more in-city stations buy nothing *on a
  reference network*. On an LCS network they buy real skill. Stated unconditionally it is wrong.
- **The V5 deep-tropical claim is confounded**: that cell differs from the others in latitude
  AND in instrument class, and this analysis cannot separate them at n = 13 (9 LCS / 3 ref).
- The temperate `Bud0` deficit (1.194) is NOT explained by class -- temperate is
  reference-dominated like its neighbours -- so that finding survives.

### The one place this helps

**Kandy's own sensors are low-cost (FECT PurpleAir).** The LCS stratum is therefore the *more
appropriate* analogue for Kandy at `Bud1` than the reference-dominated bands, and the honest
framing conditions on instrument class rather than latitude alone. That reframing is available
precisely because the gate was registered in advance.

### Method note

Three confounds have now been caught by registered gates rather than by review: country x
latitude (Amendment 2), driver completeness x band (the BLH sensitivity, F.51), and instrument
class x band (here). Each was invisible in the pooled numbers and each would have survived into
a paper. The gates are the reason this workstream is trustworthy, not the results.


## F.53 — the class/band confound CANNOT be sampled away: reference monitoring barely exists in the deep tropics

⚠ **Magnitudes superseded by F.85 (2026-08-23).** The scarcity argument itself **stands**.

Follow-up to F.52, checked against the full OpenAQ census (715 clusters) rather than the drawn
sample, using `is_monitor` — which is known BEFORE ingest, so this is a property of the world,
not of the draw.

**Clusters with >= 10 concurrent stations, by band and instrument class:**

| band | LCS | mixed | reference |
|---|---:|---:|---:|
| **deep-tropical** | 9 | 3 | **5** |
| tropical | 3 | 2 | 11 |
| subtropical | 11 | 12 | 16 |
| temperate | 18 | 69 | 32 |

**Five.** Worldwide, five deep-tropical city clusters have >= 10 concurrent reference-grade
PM2.5 stations: Medellin (1.00), an Indian cluster (1.00), Bogota (0.91), Lima (0.90), a second
Indian cluster (0.82). Against 32 in the temperate band.

**So the class x band aliasing in F.52 is not a defect of my sampling — it is the structure of
global air-quality monitoring.** A de-aliased deep-tropical cell cannot be drawn at n > 5, and
even that would be 2 of 5 from one country, trading the instrument imbalance for the country
imbalance Amendment 2 removed. (Bogota is also already an ingest exclusion: 18 concurrent
stations in the census, 1 retrievable in the window — census concurrency overstates usable
coverage.)

**This is worth reporting as a finding in its own right.** The regime that most needs a
sensorless method is the regime where reference monitoring is scarcest; the project's own
motivation, quantified from an independent global census. It also means any cross-regime
validation of this kind — by anyone — inherits the same confound, and a paper claiming clean
latitude-band transfer without addressing instrument class should be read sceptically.

**Decision: do NOT chase a de-aliased draw.** Adding cities after seeing the confound is the
forking-paths risk the registration exists to prevent, the ceiling is n = 5, and the trade is
one confound for another. Instead:

1. report every ladder result **stratified by instrument class**, never pooled across it;
2. state the class x band aliasing as a limitation with the census counts above;
3. treat the **LCS stratum as the appropriate Kandy analogue** (Kandy's sensors are low-cost),
   which sidesteps the confound rather than pretending it was resolved.

Any future expansion of the deep-tropical reference cell must be registered BEFORE ingest.


## F.54 — the Bud3 background gain is REAL regional information, not a same-network artefact

`scripts/independent_background.py`. The open caveat on F.50-F.52 was that `Bud3`'s background
came from the target city's OWN outer-ring stations, which share its instruments, calibration,
siting conventions and operator. The test rebuilds the background from a **different city**,
30-300 km away, whose stations the target never sees, and runs it through an **identical**
`Bud0 -> Bud1 -> Bud2 -> Bud3` chain.

| band | n | median donor distance | own-network gain | independent gain | recovered |
|---|---:|---:|---:|---:|---:|
| tropical | 6 | 72 km | 58.4% | **49.3%** | 84% |
| subtropical | 5 | 83 km | 58.5% | **47.8%** | 82% |
| temperate | 5 | 99 km | 41.9% | **26.0%** | 62% |
| deep-tropical | 4 | 221 km | 41.5% | **21.0%** | 51% |
| **pooled** | **20** | **89 km** | **51.4%** | **38.8%** | **75%** |

**An entirely independent network ~89 km away recovers three quarters of the effect.** The
background rung is therefore carrying genuine regional information, and the F.50-F.52 headline
stands rather than needing restatement.

**The residual quarter is bounded, not attributed.** Recovery tracks donor DISTANCE (84% at
72 km, 51% at 221 km), and the own-network ring sits ~5-15 km out against donors at 72-221 km.
So the gap conflates "same network" with "much closer", and this test only shows the artefact is
**at most** 25% -- most likely less. Claiming the artefact IS 25% would over-read it.

**Coverage limit, reported not hidden:** only **20 of 47** targets have a donor in range;
26 have none and 1 has no temporal overlap. The usable subsample is biased toward regions with
dense city coverage (China, India, Thailand, Europe), and the deep-tropical cell is the
thinnest (n = 4, donors twice as far) -- the same sparsity F.53 documented, reappearing.

**Method note.** The first version of this test compared an independent gain measured against a
climatological constant with an own-network gain measured against `Bud2` -- different baselines,
not a comparison. It was caught before reporting by asking what each number was relative to.
`modular_validation_all.ladder()` now takes a `bg_override` so both arms are forced through the
identical chain.

**For Kandy this is the strongest argument yet for NBRO**: a regional network ~90 km out
recovers most of the single largest skill gain available to the model, and Kandy currently has
none.


## F.55 — the diurnal cycle transfers in the DEEP TROPICS and nowhere else

`scripts/diurnal_transfer_test.py`, 46 cities. The budget ladder tested the LEVEL axis at daily
resolution; the sub-daily axis had **no out-of-sample test anywhere in the project** -- at Kandy
it comes from `sharpen_T_diurnal` fitted to the same FECT sensors it is later compared against
(gotcha #68). The ingested data is hourly and was aggregated away for the ladder, so this cost
nothing new.

Leave-one-city-out: predict a city's unit-mean 24-h shape (local SOLAR time, since the cycle is
driven by the sun and not by time-zone legislation) from other cities only.

| band | n | observed amplitude | r (global shape) | RMSE flat | RMSE transferred | vs flat |
|---|---:|---:|---:|---:|---:|---|
| **deep-tropical** | 13 | **1.729** | **0.665** | 0.156 | **0.116** | **26% BETTER** |
| tropical | 13 | 1.328 | 0.620 | 0.083 | 0.084 | no gain |
| subtropical | 10 | 1.311 | 0.137 | 0.077 | 0.099 | **worse** |
| temperate | 10 | 1.289 | 0.223 | 0.076 | 0.092 | **worse** |
| pooled | 46 | 1.37 | 0.515 | 0.0956 | 0.1008 | **5.5% WORSE** |

**Pooled, a transferred diurnal shape is WORSE than assuming no cycle at all**, and it beats
flat in only 57% of cities -- barely above a coin flip. The pooled number is the honest headline
and it is a null.

**But the effect is entirely regime-dependent, and the regime where it works is Kandy's.**
Deep-tropical cities have a large, consistent cycle (amplitude 1.73 against ~1.29 at
mid-latitudes), so there is real shape to transfer; mid-latitude cycles are weak and a
transferred shape mostly injects noise. Selecting donors by latitude band does NOT help
(`same_band` is no better than `global`), so what matters is that the target HAS a strong cycle,
not that the donors are nearby in latitude.

**Two limits that stop this replacing local sensors:**
1. **Phase error: 2.0 h median, NOT the 4 h first reported** -- see the correction below.
2. **Amplitude is damped in transfer** (1.26 against 1.37 observed) -- the same
   regression-to-the-mean that `sharpen_T_diurnal` exists to undo, now measured across 46
   cities rather than inferred at one.

**Consequences.**
- The project's insistence that `Bud0` supplies no usable diurnal cycle is **vindicated for
  mid-latitudes and softened for the deep tropics**: a sensorless Kandy could get r ~ 0.67 and
  26% better than flat, but with a 4-hour phase error and a damped swing.
- **This bears directly on F.46.** `f` depends on the anchor's diurnal AMPLITUDE, and transfer
  damps amplitude by ~8%. A sensorless Kandy would therefore land at a different `f` than the
  FECT-sharpened one -- so the sensorless and two-sensor tiers do not merely differ in
  precision, they differ in the partition they report.
- Gotcha #68 stands: the local sensors are doing real work on the diurnal axis, and no amount
  of cross-city transfer replaces them.


### F.55 correction — the "4-hour phase error" was mostly a metric artefact

Diagnosed on request rather than left standing. `argmax` is the wrong phase statistic here:
**45 of 46 cities are bimodal**, with a median secondary/primary peak ratio of **0.933**, and in
**27 cities the two peaks are within 10%** of each other. `argmax` therefore flips between the
morning and evening peak on the slightest perturbation and reports a large "phase error" that is
really a peak-selection artefact.

Circular cross-correlation is the right statistic. Re-measured:

| statistic | value |
|---|---:|
| median \|argmax error\| (as first reported) | 4.0 h |
| **median \|cross-correlation lag\|** | **2.0 h** |
| median r at lag 0 | 0.515 |
| **median r at best lag** | **0.808** |

So the transferred shape has close to the right FORM (r = 0.81 once aligned) and a modest timing
offset -- not a shape that lands a rush peak in the afternoon.

**And the phase error is regime-split as sharply as everything else:**

| band | \|argmax err\| | **\|xcorr lag\|** | r at lag 0 |
|---|---:|---:|---:|
| **deep-tropical** | 1.0 h | **1.0 h** | 0.67 |
| tropical | 4.0 h | **1.0 h** | 0.62 |
| subtropical | 8.5 h | **7.5 h** | 0.14 |
| temperate | 3.5 h | **8.0 h** | 0.22 |

**In the tropics phase transfers to within an hour. At mid-latitudes it is 7.5-8 h out -- close
to anti-phase.** The physical reading: mid-latitude diurnal PM2.5 is heating- and
boundary-layer-driven with strong seasonality, so a two-year mean shape is weak (amplitude 1.29)
and its phase is near-arbitrary. That, not a failure of transfer, is what produces the pooled
null in F.55.

**Revised consequence for Kandy.** A sensorless deep-tropical diurnal cycle carries roughly a
**1-hour** phase error and r ~ 0.67, not a 4-hour error. That is materially better than F.55
first stated, and it moves the sensorless tier from "supplies no usable diurnal cycle" to
"supplies a usable one with a damped swing". The amplitude damping (~8%) and its knock-on to
`f` via F.46 are unchanged and remain the binding limitation.


## F.56 — ❌ the SECTOR-WEIGHTED emission surface does NOT rank stations better. Not adopted.

`scripts/spatial_pattern_test.py`. The gate was stated before running: the sector surface goes
into production only if it demonstrably ranks a city's own stations better than the shipped
traffic-centrality surface. Swapping one imposed pattern for another is not justified otherwise.

Spearman rank of station mean PM2.5 against the surface at each station's cell; each city tested
against ITS OWN permutation null (2,000 shuffles), never pooled.

| city | n | rho traffic | p | rho sector | p | mix used |
|---|---:|---:|---:|---:|---:|---|
| baoji | 19 | **+0.565** | 0.007 | +0.544 | 0.011 | vehic .35 / heat .65 |
| medellin | 17 | **+0.444** | 0.035 | +0.147 | 0.281 | vehic .85 / burn .15 |
| bogota | 22 | **+0.383** | 0.044 | +0.331 | 0.065 | vehic .80 / burn .20 |
| taian | 12 | +0.363 | 0.125 | −0.004 | 0.511 | vehic .45 / heat .55 |
| kathmandu | 35 | **+0.324** | 0.022 | +0.298 | 0.044 | vehic .40 / heat .10 / burn .50 |
| bazhou | 11 | +0.303 | 0.188 | **+0.413** | 0.115 | vehic .45 / heat .55 |
| xichang | 11 | +0.257 | 0.244 | **+0.395** | 0.117 | vehic .30 / heat .70 |
| yichang | 12 | −0.092 | 0.628 | **+0.232** | 0.246 | vehic .45 / heat .55 |
| chiangmai | 12 | **−0.623** | 0.984 | −0.546 | 0.966 | vehic .35 / heat .10 / burn .55 |

**Traffic-only: median rho +0.324, significant in 4 of 9. Sector: median +0.298, significant in
2 of 9.** The sector surface ranks better in 4 of 9 cities, median delta **−0.021**.

**VERDICT: the gate FAILS. The sector surface is NOT wired into production.** It is neutral on
median and it costs significance at two cities (Medellin 0.035 -> 0.281, Bogota 0.044 -> 0.065).
Held behind `src/modular/emission.py`, tested, unused.

**But it is not worthless, and the pattern of where it helps is informative.** It improves the
three heating-dominated Chinese cities (bazhou +0.11, xichang +0.14, yichang +0.32 -- and
yichang, the recorded industry-misplacement failure, flips from anti-correlated to positive) and
degrades the two Latin American cities where a modest declared burn share (15-20%) dilutes a
traffic pattern that was already working. That is consistent with the `emix` weights themselves
being wrong at Medellin and Bogota rather than with the sector method being wrong -- but `emix`
is a hand-declared prior and this test cannot separate the two.

**Two things this run also establishes:**
- **The spatial axis remains weak on its own terms.** Even traffic-only reaches significance in
  only 4 of 9 cities, consistent with the five prior spatial nulls.
- 🔴 **Chiang Mai is strongly ANTI-correlated (rho −0.62, p 0.98) under BOTH surfaces.** Its PM
  is regional biomass smoke, so proximity to the road network genuinely does not predict a
  dirtier station. This is a second documented anti-correlated city alongside Medellin
  (gotcha #23) and it belongs in the limitations: where the regional term dominates, the local
  emission surface can invert.
- **Kandy is not testable** (2 stations with >= 500 observations) -- which is the project's
  founding condition restated as a measurement.

**What would change the verdict:** inventory-derived `emix` (EDGAR/CAMS sector shares) instead
of hand-declared weights, an industrial proxy for the sector that currently has none, and real
fire data where the FIRMS placeholder is standing in.


## F.57 — DIAGNOSIS of the two weak axes, with the fixable and unfixable parts separated

Run so the model can be improved recursively rather than re-litigated. Hypotheses were tested,
not asserted; two of my own were refuted and one of my tests was degenerate.

### Spatial pattern — the defect is OVER-DISPERSION, and it is calibratable

| city | n | obs CV | pred CV | ratio | rho |
|---|---:|---:|---:|---:|---:|
| bogota | 22 | 0.312 | 0.244 | **0.78** | +0.383 |
| medellin | 17 | 0.195 | 0.279 | **1.43** | +0.444 |
| kathmandu | 35 | 0.186 | 0.267 | **1.44** | +0.324 |
| baoji | 19 | 0.123 | 0.408 | 3.33 | +0.565 |
| taian | 12 | 0.125 | 0.451 | 3.61 | +0.363 |
| chiangmai | 12 | 0.130 | 0.517 | 3.98 | −0.623 |
| bazhou | 11 | 0.093 | 0.386 | 4.16 | +0.303 |
| yichang | 12 | 0.056 | 0.259 | 4.64 | −0.092 |
| xichang | 11 | 0.113 | 0.712 | **6.31** | +0.257 |

**The emission surface predicts 3.6x more between-station contrast than exists** (median
predicted CV 0.386 against observed 0.125), and **`corr(rho, dispersion ratio) = −0.733`** --
the strongest relationship in the diagnosis. The three best-ranking cities are the three least
over-dispersed. This is a **calibration defect, not a structural one**, and it maps onto a
parameter that is already differentiable: the `S^s_exp` exponent in `src/modular/diff_decomp.py`,
whose synthetic gradient (+1.73) was the largest of the five. **Fitting `s_exp` so predicted
dispersion matches observed is a concrete, testable recursive improvement.**

Two further, smaller causes:
- **`corr(rho, observed CV) = +0.467`.** The pattern ranks well only where there IS spatial
  signal to rank. Yichang's stations span a CV of 0.056 -- essentially a flat city -- and no
  pattern can be validated against a flat truth. **Observed between-station CV should be an
  ADMISSIBILITY criterion: below some threshold the spatial claim is not testable, and saying so
  is better than reporting a null.**
- **30 of 151 stations share a grid cell** (20%), which imposes rank ties by construction and
  attenuates Spearman. A finer grid or per-cell aggregation removes it.
- **`corr(rho, n stations) = +0.570`** -- small-n cities are noisy, i.e. the test is
  underpowered at n = 9 cities. See the expansion note below.

### Sub-daily shape — mostly an INFORMATION limit, not a defect

Two hypotheses tested:

1. **Seasonal smearing — REFUTED.** Splitting the annual mean shape into DJF and JJA does not
   rescue mid-latitude transfer: subtropical r goes 0.097 (annual) -> 0.193 (DJF) -> −0.092
   (JJA); temperate 0.009 -> 0.124 -> 0.269. RMSE stays worse than flat in every season. The
   annual mean is not hiding two opposing seasonal cycles.
2. **Solar vs civil time — NOT TESTED; my test was degenerate.** I compared solar time against
   `round(lon/15)`, which is by construction within 30 minutes of solar, so the two agreed
   (r +0.411 vs +0.412) and nothing was learned. A real test needs actual time-zone data, where
   whole countries sit hours off their meridian (all of China on UTC+8, India on UTC+5:30).
   **The hypothesis stands open.**

What remains is an information limit: mid-latitude shapes deviate from flat by only ~7.6%
(flat RMSE 0.076) and are idiosyncratic between cities. There is little transferable signal
because there is little signal.

**The fixable part is the transfer METHOD.** Averaging raw curves across cities with different
phases and peak spacings smears them -- which is precisely why amplitude damps ~8% and 45 of 46
cities are bimodal with near-equal peaks. Transferring **parameters** (amplitude, phase,
peak spacing, morning/evening ratio) and reconstructing the curve, rather than averaging curves,
is the recursive improvement. Predicting amplitude from a covariate (the BLH diurnal range is
the obvious candidate, and it is already in the driver table) rather than by averaging is the
second.

### On expanding the test panels

**Spatial: yes, and it is the binding constraint.** `rho` correlates with station count at
+0.570 and the panel is only 9 cities, so the axis with the least evidence also has the smallest
test. Expansion requires a traffic-centrality surface per city
(`build_xichang_traffic_emission.py --city`), which is an OSM/Overpass build -- bounded work, not
new data. Going from 9 to ~40 cities would make the spatial claim defensible for the first time.

**Diurnal: no.** It already runs on all 46 ingested cities and the answer is clear and
regime-split. More cities would sharpen the mid-latitude null, which is not the useful direction.


## F.58 — spatial test expanded 9 -> 47 cities: NO single emission proxy works everywhere

`scripts/spatial_proxy_scan.py`. Rather than replicate the OSM traffic-centrality build for 37
more cities -- which would enlarge the test of ONE proxy already known to be 3.6x over-dispersed
(F.57) -- four global source proxies were sampled directly at **636 station coordinates across
47 cities**, at the station point and over a 2 km neighbourhood. No grid, no Overpass, minutes
rather than hours.

### Pooled: every proxy is weak

| proxy | median rho | positive in | \|rho\| > 0.5 in | estimable |
|---|---:|---:|---:|---:|
| **population 2 km** | **+0.207** | 70% | 17% | 47 |
| built 2 km | +0.197 | 64% | 13% | 44 |
| population point | +0.152 | 66% | 23% | 47 |
| ntl point | +0.143 | 62% | 17% | 47 |
| built point | +0.124 | 64% | 21% | 47 |
| ntl 2 km | +0.119 | 64% | 17% | 47 |
| fire 2 km | −0.013 | 19% | 4% | 18 |
| fire point | −0.032 | 13% | 4% | 13 |

The best single proxy reaches **rho +0.207**, and no proxy exceeds \|rho\| > 0.5 in more than a
quarter of cities. **The traffic surface's +0.32 on the 9-city panel now looks optimistic** --
that panel was small, valley-selected and mid-latitude-weighted.

### The result that matters: the best proxy is REGIME-SPECIFIC

| band | n | best proxy | rho | worst proxy | rho |
|---|---:|---|---:|---|---:|
| deep-tropical | 13 | population 2 km | **+0.210** | fire point | −0.160 |
| subtropical | 10 | built 2 km | **+0.230** | fire 2 km | −0.320 |
| temperate | 11 | ntl point | **+0.441** | fire point | +0.018 |
| tropical | 13 | fire 2 km | **+0.494** | ntl point | −0.073 |

**Fire is the BEST predictor in the tropical band (+0.494) and the WORST in the subtropical
(−0.320). Night lights are best in temperate (+0.441) and worst in tropical (−0.073).** No fixed
surface can be right in all four.

**This vindicates the multi-source premise and condemns the current implementation at the same
time.** A traffic-only surface is wrong by construction for most regimes; but so is any single
fixed sector weighting, which is why the hand-declared `emix` did not help in F.56. The
weights need to be regime-dependent and evidence-based, not declared per city by hand.

### Caveats, stated at full strength

- **Fire is estimable in only 18 of 47 cities** (13 at point scale) -- most cities have no FIRMS
  detections at all, the same gap that made Kathmandu fall back to a placeholder. The tropical
  +0.494 therefore rests on a handful of cities and should be treated as a lead, not a result.
- Band-level "best proxy" differences come from 10-13 cities each with 6-35 stations. They are
  suggestive of regime-dependence, not a quantification of it.
- All of this is between-station rank on time-averaged means. It says nothing about whether the
  pattern is right hour by hour.

### What it changes

1. The **`emix` weights should be fitted per regime** against exactly this kind of held-out
   station rank, not hand-declared. That is a concrete, registrable next experiment and it now
   has a 47-city frame to run on.
2. **Fire should not be used as a spatial proxy** on current evidence -- it is negative pooled
   and unavailable in 60% of cities. The burn SECTOR may still be real; the FIRMS SURFACE is not
   a usable spatial allocator for it.
3. The honest ceiling for the spatial axis, on the largest frame the project has assembled,
   is **rho ~ 0.2 pooled**. Any claim of fine-scale spatial skill must live inside that number.


## F.59 — ❌ S1: fitted regime-specific emission weights do NOT beat a single proxy. Not adopted.

Registered as experiment S1 in `prereg_modular_validation_v2_2026-08-18.md` before running, with
the prior published: *"modest or no gain is the expected outcome... a null would be consistent
with the five prior spatial nulls."*

Leave-one-city-out **within band**, weights non-negative and summing to one, scored on the
held-out city's stations.

| band | n | fitted | population 2 km | equal-weight | fitted − pop2 |
|---|---:|---:|---:|---:|---:|
| temperate | 11 | **0.434** | 0.169 | **0.434** | +0.265 |
| subtropical | 10 | **0.248** | 0.108 | 0.178 | +0.140 |
| deep-tropical | 12 | 0.165 | **0.266** | 0.248 | **−0.101** |
| tropical | 12 | −0.046 | 0.019 | **0.145** | **−0.065** |
| **pooled** | **45** | **0.203** | **0.207** | **0.202** | **−0.004** |

- **S1-G1 FAIL** — fitted (0.203) does not beat population 2 km (0.207) pooled.
- **S1-G2 FAIL** — deep-tropical loses 0.101 and tropical 0.065, both beyond the 0.05 bound.
- **S1-G3** — weights reported in full below; none collapses onto a single proxy, all are
  diffuse (0.03-0.34), which is itself the diagnosis: there is little signal to apportion.

**The decisive comparison is fitted vs EQUAL-WEIGHT, not fitted vs population.** Pooled they are
0.203 and 0.202 -- identical. In the temperate band, equal weights score **exactly** what the
fit scores (0.434 both). So where multi-proxy helps, what helps is *using more than one proxy at
all*, not *choosing the weights*. And in the two tropical bands fitting is actively worse than
equal weights (0.165 vs 0.248; −0.046 vs 0.145) -- it overfits 6 weights to 10-12 cities.

**Per the registered stopping rule the fitted weighting is NOT adopted.** The hand-declared
`emix` stays and F.56's verdict stands.

**A limitation that bears on the one band with a real lead.** Fire had to be dropped from the
fit: only **27 of 47** cities have all eight proxies finite, against 45 without fire. So the
tropical band -- where F.58 found fire the best single proxy at +0.494 -- was fitted *without*
the proxy that mattered there, and it is also the band where the fit did worst. That is not
evidence against regime-specific weighting; it is evidence that the fire surface's 60%
unavailability blocks the test.

**Published prior, scored honestly:** I predicted modest-or-no gain (**correct**) and that
temperate was the most likely band to gain (**correct**, +0.265). The pooled null was expected,
not discovered.

**Where this leaves the spatial axis.** Three surfaces have now been tested on this frame --
traffic-centrality (rho +0.32 on 9 valley cities, F.56), single global proxies (rho +0.21 on 47
cities, F.58), and fitted regime weights (rho +0.20, here). **They agree on a ceiling near
rho ~ 0.2 and none of them moves it.** The constraint is not the surface; five nulls, plus these
three, now say the same thing from different directions.


## F.60 — 🔴 A LOCAL SPATIAL NETWORK DOES NOT PREDICT ITS OWN HELD-OUT STATIONS

Prompted by the question "do cities that HAVE a local spatial network work as expected?" -- and
it exposed that `Bud4`, the rung where the registry says `P` becomes estimable, had been
declared but **never exercised**. The ladder only ever ran `Bud0` to `Bud3`.

**The test.** 30 cities with >= 12 stations. Leave-one-station-out: predict each station's mean
PM2.5 from the OTHER stations of the same city by inverse-distance weighting -- a local network
used as a network, no physics, pure observation. Compared against the city mean (flat) and
against the imposed population proxy.

| predictor | median rho | notes |
|---|---:|---|
| **imposed population proxy** | **+0.188** | external, no local observation |
| IDW from the city's own stations | **+0.059** | a real local network |
| nearest-neighbour station | +0.014 | |

| | |
|---|---:|
| RMSE skill of IDW vs assuming the city mean | **−0.092** (WORSE than flat) |
| cities where the network beats flat | **7 of 30** |
| median nearest-station spacing | **4.1 km** |

**At 4 km spacing, one station's long-term mean cannot be predicted from its neighbours.** The
observational network performs WORSE than assuming the city is spatially uniform, and worse than
an imposed global population raster that never saw a single local measurement.

### Why this reframes the whole spatial axis

Between-station differences in long-term mean PM2.5 are **not a smooth field sampled at points**.
They are dominated by micro-siting -- kerbside against courtyard against rooftop -- which is
sub-grid at 1 km and not spatially interpolable at 4 km. That single fact retrospectively
explains a long list of separate puzzles:

- the five spatial nulls;
- Medellin's anti-correlation with terrain (gotcha #23) and Chiang Mai's rho −0.62 (F.56);
- the rho ~ 0.2 ceiling that three unrelated surfaces converged on (F.56, F.58, F.59);
- and F.47's observation-operator finding that the point-vs-area offset is **sub-grid**, not
  resolved-scale.

They are all the same phenomenon seen from different angles.

### 🔴 This weakens a recommendation I have made repeatedly

I have been arguing that a local spatial network -- the CEA passive NO2 archive -- is THE lever
for the spatial axis. **On this evidence a network of point monitors at kilometre spacing would
not deliver a coherent spatial field**, because such networks do not do so anywhere in the
47-city frame. The recommendation needs qualifying: NO2 remains valuable for the `f` partition
and as a local activity tracer (F.45), but it should not be sold as the fix for `P_local`.

### Caveats, and they are real

- This tests **2-year station means**. Daily or hourly spatial coherence could be higher, since
  a synoptic episode lifts every station together. The model's `P_local` is however
  predominantly a time-averaged pattern, so the time-averaged test is the right first one.
- The comparison is not symmetric: the population proxy carries external information while IDW
  sees only ~11 neighbouring points.
- **It is not universal.** 7 of 30 cities do beat flat, some strongly (rho 0.81 with 42% RMSE
  skill; 0.76 with 39%). Something distinguishes them and it is not obviously station count or
  spread. Worth a follow-up: if the distinguishing feature is identifiable in advance, it
  becomes an admissibility condition for claiming spatial skill at all.

### Consequence for the specification

`Bud4` in `src/modular/budgets.py` asserts that a spatial network makes `P` estimable. **That
assertion is now unsupported and must be marked as such** -- it was a design assumption, and the
first test of it fails. The budget ladder's other rungs are validated; this one is not.


## F.61 — R2/R3: adding the LUR predictor set, ROADS INCLUDED, does not move the spatial ceiling

Full predictor set built as R1 of the remediation plan: **636 stations, 47 cities, 67 columns** --
road length by class at 50/100/300/500/1000 m, distance to nearest major road, NDVI, Hansen tree
cover, JRC water, ESA land-cover fractions, GHS built volume (total and non-residential),
population and night lights, each at 100/300/1000/2400 m. GEE 47/47, OSM 47/47, zero failures.

### R3 — transferable LUR (leave-one-CITY-out), the question that matters for Kandy

| band | n | LUR | population baseline |
|---|---:|---:|---:|
| temperate | 11 | **0.458** | 0.275 |
| deep-tropical | 13 | 0.236 | **0.259** |
| subtropical | 10 | 0.234 | 0.212 |
| tropical | 13 | 0.145 | 0.105 |
| **pooled** | **47** | **+0.275** | **+0.245** |

Difference **+0.025**, 95% CI **[−0.014, +0.164]** -> **R3-G1 FAIL**.

**🔴 The decisive number: adding roads moved pooled rho from +0.273 to +0.275.** The
GEE-only run (no roads) and the full run are indistinguishable. The literature's strongest
predictor -- "major roads within 100 m" -- **buys essentially nothing here**, even though forward
selection does pick road variables first (`road_minor_50` and `road_major_500` are among the six
most-selected).

**This substantially refutes the missing-predictor hypothesis I raised in the remediation plan**,
and correspondingly **restores support for the ceiling**: rho ~ 0.2-0.28 now survives the
addition of the predictor set that was supposed to break it. The ceiling moves back from
"hypothesis" to "supported finding" -- this time on adequate instrumentation.

One exception worth keeping: the **temperate** band gains materially (0.458 vs 0.275). The
**deep-tropical band -- Kandy's -- is the one band where LUR LOSES to a plain population raster**
(0.236 vs 0.259).

### R2 — local LUR is NOT ANSWERABLE on this frame, by either method

| variant | pooled median held-out R2 | rho |
|---|---:|---:|
| ridge, full predictor set | **−0.194** | −0.191 |
| forward selection, <= 3 predictors | **−2.350** | +0.004 |
| forward selection, cities with >= 20 stations (n = 5) | −0.158 | |

Both are catastrophically negative, and the classical forward-selection variant is *worse* than
ridge -- selection instability on 11 training points. **R2-G1 fails, and it fails for reasons of
power, not atmosphere.** I set that gate at 0.30 by importing a threshold from studies using
40-80 sites per city without checking our frame supports it; our median is 12 and only 5 cities
reach 20. **R2 as specified was unanswerable from the start.**

### The structural reason our frame is weaker than the LUR literature's

Published LUR campaigns **site monitors deliberately across land-use contrast** -- that is the
design. Regulatory and low-cost networks are sited for compliance and population exposure, not
to span a predictor space. So our 636 stations are not a LUR design; they are a convenience
sample that happens to have coordinates. That limits R2 and R3 in a way no additional predictor
can fix, and it should be stated whenever the comparison with published R2 = 0.43-0.83 is made.

### Standing corrections, updated

- The **ceiling claim (F.56/F.58/F.59) is REINSTATED** as supported, having survived a
  proper predictor set. My downgrade of it in the remediation plan was the right call on the
  evidence then available and is now reversed by the evidence.
- **F.60's withdrawal STANDS**: interpolation and regression are still different things, and
  the LUR literature still shows regression works where interpolation does not -- on
  purpose-designed networks. Ours is not one.
- **R4 (`Bud4` as recalibration) is now much less promising.** If a transferred LUR barely beats
  a population raster, local recalibration of it has little to recalibrate. The CEA NO2
  recommendation stays qualified for spatial purposes; its value for `f` and as an activity
  tracer (F.45) is unaffected.


## F.62 — ❌ R5: decomposing the diurnal cycle does not rescue it. The dilution term is ~zero.

Final item of the 2026-08-19 remediation plan. 46 cities with both a PM2.5 diurnal shape and a
24-point ERA5 boundary-layer climatology (48 pulled, 0 failures).

Model, in logs because the BLH cycle spans ~40x:
`log P(h) = a * log(BLH_ref / BLH(h)) + e(h) + const`, fitted leave-one-CITY-out, with the
target supplying its OWN BLH curve (reanalysis, no local measurement, so Bud0-admissible).

| band | n | flat | whole-shape | decomposed | r(decomposed) |
|---|---:|---:|---:|---:|---:|
| deep-tropical | 13 | 0.1563 | **0.1159** | 0.1192 | 0.627 |
| tropical | 13 | 0.0832 | 0.0838 | 0.0845 | 0.599 |
| subtropical | 10 | **0.0769** | 0.0991 | 0.1010 | 0.130 |
| temperate | 10 | **0.0759** | 0.0917 | 0.1021 | 0.210 |
| pooled | 46 | **0.0956** | 0.1008 | 0.1010 | — |

- **R5-G1 FAIL** — decomposed is **5.6% worse than flat**, against the whole-shape method's
  5.5% worse. No improvement whatsoever.
- **R5-G2 FAIL** — deep-tropical degrades from +25.8% to +23.7% better than flat.
- Both methods beat flat in the same **26 of 46** cities.

### 🔴 The diagnostic that explains it: the fitted dilution exponent is 0.054

`a = 0.054` against 1.0 for pure inverse-BLH dilution. **The boundary layer's ~40-fold diurnal
swing produces almost no diurnal swing in city-mean PM2.5** (observed amplitude ~1.37x). So
there is no large physical component to peel off and transfer -- the premise of the
decomposition is empirically absent.

**Why this is coherent with the project's own model rather than a surprise.** In the additive
decomposition `PM = B + local`, only the LOCAL increment is diluted by the local boundary layer;
the regional background `B` is already well-mixed through a deep layer and does not dilute with
it. Where `B` is the larger term -- which F.43's `f ~ 0.48` says is roughly half of Kandy and
more elsewhere -- the diurnal dilution signal is buffered by construction. Emissions also peak
when the boundary layer is shallowest (morning and evening), so the two effects partly cancel in
the observed cycle.

### The remediation programme is now complete, and it is a set of nulls

| item | outcome |
|---|---|
| R1 predictor build | done: 636 stations, 47 cities, roads + 14 GEE predictors at 4-5 radii |
| R2 local LUR | **not answerable** -- median 12 stations vs 40-80 in published LUR |
| R3 transferable LUR | **FAIL** -- roads moved pooled rho from +0.273 to +0.275 |
| R4 `Bud4` recalibration | deprioritised -- nothing left to recalibrate |
| R5 diurnal decomposition | **FAIL** -- dilution exponent 0.054, no physical component to transfer |

**Both weak axes now have ceilings that survive proper instrumentation**, which is a stronger
statement than the project could make before: the spatial ceiling (rho ~ 0.2-0.28) survived the
addition of the literature's strongest predictors, and the diurnal ceiling survived a physically
motivated decomposition using each city's own boundary-layer physics.

**What remains true and useful:** the deep-tropical diurnal cycle DOES transfer (+25.8% better
than flat, r 0.63, ~1 h phase error) -- and that is Kandy's regime. The failure is at
mid-latitudes, where the cycle is weak (amplitude 1.29) and idiosyncratic.


## F.63 — ❌ Colombo does NOT substitute for a regional network at Kandy: the highlands decouple them

Tested because F.54 measured that an independent network at a median **89 km** recovers **75%**
of the background rung -- the largest gain in the whole programme -- and Sri Lanka turns out to
have three OpenAQ locations, all inside that admissible window:

| location | distance from Kandy | class | record ends |
|---|---:|---|---|
| Colombo (AirNow) | **93.4 km** | reference | 2025-04 |
| US Diplomatic Post, Colombo | 95.9 km | reference | 2025-03 |
| Jaffna (Clarity) | 272.8 km | low-cost | 2026-05 (live) |

Colombo sits almost exactly at the F.54 median donor distance, is reference-grade, and **its
data was already on disk** (1,661 daily rows, 2019-01 to 2025-04, from the old Embassy
out-of-domain test). If a donor were going to work anywhere, it was this one.

### It does not work

A skill test at Kandy would be circular -- `T(t)` is FECT-calibrated (gotcha #68) -- so the
question tested is the one prior to skill: **does a donor 93 km away share air-mass variability
with Kandy?** Observations only, no model.

| | |
|---|---:|
| Kandy (FECT) vs Colombo, daily | **r = 0.604** (Spearman 0.651, monthly 0.673), 937 days |
| benchmark: 20 donor/target pairs in the 47-city frame | median **r = 0.909** |
| benchmark at 60-130 km (n = 10) | median **r = 0.923** |
| Kandy-Colombo percentile | **0th -- below every benchmark pair** |

**Attenuation checked, because the comparison is not like-for-like.** Benchmark pairs are 10+
station city-means on both sides; Kandy is a 2-sensor low-cost mean. The two FECT sensors
correlate at r = 0.603 with each other (Spearman-Brown reliability 0.752), so the corrected
upper bound is **r ~ 0.70** -- still the weakest pair in the set. ⚠ That correction rests on
only **35 overlapping sensor-days** and is therefore imprecise; it is the right adjustment, not
a precise one.

**The physical reading.** Colombo is coastal and at sea level with marine inflow; Kandy is
inland and elevated behind the central highlands, and during the south-west monsoon the two sit
on opposite sides of that barrier -- Colombo windward and wet, Kandy leeward. The highlands
decouple them. F.54's 75% recovery was measured on pairs correlating at ~0.92; at 0.60-0.70 far
less should be expected. Jaffna is worse on both axes: 273 km (where F.54 recovery had already
fallen to ~51%) and low-cost rather than reference.

### Consequence

**There is no free substitute for a regional network near Kandy.** The background rung stays
imposed rather than observed, and **NBRO remains the highest-value acquisition with no local
alternative** -- which is worth knowing precisely because the formal data routes are slow.

Do not re-propose Colombo as a background donor. It is admissible by distance and useless by
correlation, and the reason is topographic rather than fixable.

**Ranking of the blocked data, now measured rather than assumed:**
1. **NBRO (regional background)** -- highest value, no substitute (F.54, this entry).
2. **CEA reference monitor** -- closes W5, tightens `f`'s +/-0.05 (F.46), and adjudicates the
   pre-registered F.25 prediction. Bounded but real.
3. **CEA passive NO2 (spatial)** -- **demoted**: F.60/F.61 show a local spatial network does not
   make `P_local` estimable. Its value is the `f` partition and activity tracing (F.45), not
   the spatial field.


## F.64 — 🟢 W5 CORROBORATED at Akurana by a BAM-anchored study, and three further constraints extracted

Source: **Dhammapala, Basnayake, Premasiri, Chathuranga, Mera (2022)**, *PM2.5 in Sri Lanka:
Trend Analysis, Low-cost Sensor Correlations and Spatial Distribution*, AAQR 22(5), 210266
(open access). Read in full from `references/papers/aaqr-21-10-oa-0266.pdf`.

**This is the first time the project's own ground truth has been checked against a
reference-grade instrument.**

### 1. The FECT Akurana sensor appears IN this paper, BAM-anchored

The authors co-located PurpleAir and Atmos sensors with the **US Embassy BAM** (a Federal
Equivalent Monitor) in Colombo, derived correction factors, and applied them to six other
PurpleAir sensors around Sri Lanka -- **one of which is Akurana**, the project's own sensor 12451.

| source | Akurana daily PM2.5 |
|---|---|
| Dhammapala, BAM-anchored PA correction (2019-06..2021-07) | **~18-19** (read from Fig. 9a boxplot) |
| **project FECT 12451, full record** (2018-07..2026-04, 884 days) | **median 15.0, mean 17.8** |

**These agree.** W5 -- the largest unverified link in the chain -- moves from *unvalidated* to
*corroborated at Akurana*. ⚠ Caveats: different periods, and the paper's value is read off a
boxplot, not a printed number.

**🔴 A false alarm I nearly recorded.** Restricting to the paper's exact window gave a project
Akurana median of **9.5** against their ~18-19, which looked like a 2x calibration failure. That
window contains only **35 overlapping days** for this sensor. The full record removes the
discrepancy entirely. **Second time this session a ~35-day sample nearly produced a wrong
conclusion** (the other was the FECT inter-sensor reliability in F.63). Thin overlap windows in
this project are a recurring trap.

### 2. Their published PurpleAir correction, for Sri Lanka, BAM-anchored (their Table 2)

    PurpleAir daily   PM = 0.517 x SensorPM - 0.162 x RH% + 13.5
    PurpleAir hourly  PM = 0.525 x SensorPM - 0.191 x RH% - 0.154 x T degC + 20
    Atmos daily       PM = 0.913 x SensorPM - 3.6

They also report that PurpleAir's selectable **"Woodsmoke" (Australian) conversion** lands within
**4.2%** N-RMSE of their own factor, and US EPA's within 5.9%. A usable, citable, locally-derived
alternative to the project's transferred LCS slopes.

### 3. 🔴 The Kandy source mix is contradicted by their Table 1

They tabulate a **Kandy (Katugastota) source-apportionment study** (Seneviratne *et al.*, 2017,
covering 2012-2014):

| source | Kandy |
|---|---|
| **traffic** | **8%** |
| biomass burning | identified, not quantified |
| industry | identified, not quantified |
| sea salt | 3% |
| road dust / soil | 4% |

The project's `emix` for Kandy is **`vehic = 0.85`**, and CLAUDE.md states "Kandy ~90% vehicular"
with W6 recorded as **CLOSED / corroborated** (F.23). **A published PMF study at Kandy puts
traffic at 8%.** The column is incomplete -- biomass and industry are unquantified, so the
percentages do not sum -- and the study predates the record by a decade. But the tension is
large enough that **W6 should be REOPENED**, and the ~90% figure should not be restated until
its provenance is re-checked against this source.

### 4. Two further usable constraints

- **Nawalapitiya** (rural Central Province, ~25 km from Kandy, "little urban influence") reports
  **~13 ug/m3** with the lowest diurnal profile of the six PA sites. This is the closest thing to
  a **rural background reference in Kandy's own airshed** the project has found -- relevant to
  F.63, which established that coastal Colombo cannot serve that role.
- **Long-range transport adds ~8 ug/m3** on average at Colombo (trajectory-cluster difference),
  with Bangladesh/India air masses up to 45 ug/m3 -- an independent external number for the
  transboundary contribution.

Also noted: Colombo BAM annual means **31.9 (2018), 23.5 (2019), 19.5 (2020)**; NBRO operated a
temporary BAM at Colombo Municipal Council Nov 2020-Mar 2021; and the paper publishes a kriged
**1 km annual PM2.5 map of Sri Lanka** with an interactive supplement.

**What this does NOT provide:** daily time series. The regional-background rung (F.54/F.63)
remains open -- Nawalapitiya is a lead, not a dataset.

## F.65 — 🟢 TWO independent Kandy point records recovered from the literature; the model is bracketed by them (2026-08-22)

Two of the three papers the user supplied carry **PM2.5 measured in Kandy**, at sites that are
neither of the FECT sensors. Until now the only non-FECT Kandy observation in the project was
the single KOALA year (2019). This raises that count to three, and covers **2021–2024**.

### Record 1 — NBRO, Kandy (KAN), 24-h, 2021 and 2022

Nirmani *et al.* (2025), *CLEAN — Soil, Air, Water* 10.1002/clen.70051, Table 1. Obtained from
NBRO by official request; **N = 360 days in each year**, i.e. near-complete.

| | 2021 | 2022 |
|---|---:|---:|
| observed mean | **19.6** | **22.7** |
| observed median | 18.0 | 21.0 |
| observed max | 44 | 75 |
| **model, NBRO-Kandy-1 pixel** | **19.74** | **22.11** |
| model area mean | 17.08 | 18.76 |

**The model reproduces the observed annual mean at that pixel to +0.7% (2021) and −2.6% (2022)**,
and reproduces the observed interannual step (+2.4 modelled vs +3.1 observed). This is the first
time the model's *field* — not its basin mean — has been checked against a Kandy observation at
a location that played no part in building it. The pixel value is 15.6% above the area mean; the
whole of that lift comes from imposed physics (`S_emit` × confinement), never fitted to any Kandy
station, so the agreement is a genuine out-of-sample test of the spatial pattern's **magnitude**
at the core. It is consistent with the area-vs-floor geometry of gotcha #51.

**Three caveats, all material.**
1. ⚠ **The station coordinate is an assumption.** The paper gives no coordinates. I used NBRO
   "Kandy 1" (7.2939 N, 80.6414 E) from the live-network record. Sensitivity: every pixel within
   3 km of the city centre lies in **15.8–20.8** (2021) and **17.2–23.3** (2022), so the
   observation sits at the upper end of the plausible-pixel range in both years but the match is
   not knife-edge. A non-core station would make the model too low.
2. ⚠ **Instrumentation is unknown** — the paper states explicitly that NBRO supplied no
   instrument or protocol details. It cannot be called reference-grade.
3. Two numbers, not a series. **No daily r is possible from this source.**

**Seasonal cross-check:** Nirmani reports KAN's 2021 maximum monthly mean in **April (29.4)**;
the model's peak month at that pixel is **March (33.3)**, with April 23.9. Gross shape agrees
(Feb–Apr high, Jun–Sep low ~10) with the peak **one month early** in the model.

### Record 2 — a low-cost sensor at Kandy, BAM-calibrated, Nov 2022 – Feb 2024

Attanayake, Senarathna, … Bowatte (2025), *J. Hazard. Mater. Adv.* 19:100782, Table 1.
**Kandy site 7.2731 N, 80.6117 E**, 164 daily points, **mean 19.49**, SD 9.32, range 4.99–52.09.

| | obs | model, that pixel | model area |
|---|---:|---:|---:|
| 2022-11-02 → 2024-02-29 | **19.49** | **25.01** | 22.16 |
| anchored portion only (→2023-12) | — | 24.07 | — |

**Here the model runs +28% high.** The two observational records therefore **disagree with each
other by more than the model disagrees with either**: the LCS window is seasonally loaded toward
the high season yet reads *below* NBRO's 2022 annual mean. The model puts the two sites within
**2–3%** of one another (matched windows), so this is not a spatial-pattern failure the model
could repair — it is a disagreement between two observation records.

⚠ The 164 points are a **clear-sky subset** of 485 calendar days (PlanetScope cloud filtering),
and Table 1's two-row-per-site layout leaves the train/test split ambiguous (a second row reads
12.41). Treat 19.49 as indicative, not as a period mean.

### 🔴 The standing picture this creates

Of four independent Kandy point records, **three sit below the model** (FECT Hantana ~+44%,
FECT Akurana per F.64, RF-CNN LCS +28%) **and one matches it** (NBRO). The three low ones are
all low-cost sensors carrying a downward calibration correction (gotcha #37; Dhammapala's
`0.517 × sensor − 0.162 × RH + 13.5`); the one that matches has an undocumented instrument. This
is **not** resolvable from the literature, and it is a **level** question — the axis the
programme calls strong. It should be stated as an open discrepancy, not resolved by choosing the
record that agrees.

### ⚫ ACQUISITION LEAD — WITHDRAWN THE SAME DAY: the Kandy BAM is defunct

Attanayake *et al.* calibrate their network against **BAM-1020 monitors at the American Club,
Colombo and at Torrington Park, Kandy**. A regulatory-grade instrument in Kandy city appears in
no previous data survey in this project. It is operated within the Peradeniya/NIFS–Duke
collaboration (Bowatte, Senarathna, Bhave, Bergin, Carlson) — **the user's own university**.
Data availability is "on request". This is a **cheaper and closer route than CEA**, and unlike
NBRO it would supply an instrument-documented series at a known Kandy location.

**⚫ CORRECTION, same day (user):** the Torrington Park instrument is **no longer operating**.
The lead is withdrawn. It remains valuable as **provenance** — it is why the RF-CNN Kandy series
and Dhammapala's PurpleAir correction are traceable to a reference standard at all — but it is
not a data route. **CEA is the only route to a Kandy reference monitor**, which promotes the CEA
letter from one option among several to the single acquisition that can close **W11** (the level
discrepancy this entry opened) and **W6** (F.66) together. Recorded so the lead is not
re-proposed from this entry later.

## F.66 — 🔴 W6 REOPENED: traffic is 7.6% of Kandy's PM2.5 mass, and biomass burning is 14.1% (2026-08-22)

F.64 flagged a secondary table putting Kandy traffic at 8%. **The primary source has now been
read** — Seneviratne *et al.* (2017), *AAQR* 17:476–484, doi:10.4209/aaqr.2016.03.0123, the same
study CLAUDE.md already cites in support of the regional-dominated partition.

GENT stacked-filter sampler, ~137 fine-fraction samples, weekdays, **23 Jun 2012 – 20 Oct 2014**,
at the Department of Meteorology station in **downtown Katugastota** (~4 km N of Kandy centre).
EDXRF + smoke-stain-reflectometer BC, EPA PMF v5, five factors:

| PMF factor | share of mean fine mass |
|---|---:|
| soil / crustal | 3.8% |
| sea salt | 3.2% |
| **automobile traffic** (S, Br, Zn, Pb, BC) | **7.6%** |
| **biomass burning** (K, Si, BC, organic) | **14.1%** |
| metallurgical industry (Kandy brassware) | identified; share not stated in text |

### What this does and does not contradict

**It does not contradict F.23.** F.23 measured the *timing* of the activity-responsive local
component via the holiday instrument (rush/off-peak effect ratio **3.67×**, peaks at 07:00 and
17:00–20:00) and stated in its own caveats that it "bounds the **timing** of the local component
without bounding its total magnitude". A vehicular *timing* signature and a modest vehicular
*mass* share are compatible: traffic can dominate the part of the signal that responds to human
activity while contributing a minority of the mass.

**It does contradict the way the figure has been stated.** "Kandy ~90% vehicular" appears in
CLAUDE.md, in the `emix` entry (`vehic = 0.85`), and in the diurnal-profile provenance. Read as a
share of PM2.5 mass it is **wrong by an order of magnitude**, and it is wrong in a specific
direction: **biomass burning is roughly twice traffic** at Kandy, and the CPF points south toward
the Temple of the Tooth — incense and oil lamps — plus open burning, neither of which follows the
road network.

Arithmetic worth stating: with the coherence-capped partition **f ≈ 0.48**, traffic at 7.6% of
total mass is about **16% of the local increment**, not 85%.

### Consequences

1. **W6 moves from CLOSED/corroborated to OPEN, with a corrected reading.** The defensible
   statement is: *traffic is the dominant driver of the local increment's sub-daily **timing**
   (measured, F.23); it is a minority of local PM2.5 **mass** (measured, this entry).* The
   "~90% vehicular" phrasing must not be restated anywhere.
2. **This is the strongest case yet for wiring the sector-weighted `S_emit`** (built and tested,
   F.50, not in production). Kandy's `emix` should carry a substantial burning sector rather than
   `vehic ≈ 0.85`. ⚠ But note the measured spatial ceiling (F.56/F.61): three emission-surface
   variants have already failed to move ρ, so this is a **correctness and honesty fix, not an
   expected skill gain** — and it must not be sold as one.
3. **Kandy's FIRMS problem is the Kathmandu problem.** F.50 recorded that Kathmandu returns zero
   FIRMS detections because kilns burn continuously rather than as open flame. Incense, oil lamps
   and domestic open burning at Kandy are equally invisible to FIRMS, so a burning sector here
   has **no admissible proxy** either. That is a limitation to declare, not to engineer around.

### ⚠ The site is Katugastota, not the urban core — raised by the user, and it matters

The PMF apportions the mass measured **at one fixed point**: the Department of Meteorology
station in downtown Katugastota, roughly 4 km north of the Kandy core. It is not a district
aggregate, but neither is it the congested core the model's `S_emit` peak represents (Kandy
lake, the Temple of the Tooth, the bus stands). A core-sited PMF would plausibly return a
**higher** traffic share, and the study's own CPF for the traffic factor points to main roads
within 5 km of the site.

Two things stop this from rescuing the ~90% figure. First, the gap is an order of magnitude, and
no plausible core-vs-suburb gradient closes it — the model's own measured within-city contrast
is only about ±10%. Second, the **biomass factor's CPF points south, toward the Temple of the
Tooth**, and the paper attributes it to incense, oil lamps and open burning: the burning source
is being traced *toward the core*, not away from it into the rural district. So the correct
reading is that **7.6% bounds Katugastota rather than the core**, while the direction of the
error is more likely to raise traffic somewhat than to raise it sixfold.

This is now the clearest argument for the acquisition in F.65 — a core-sited instrument would
settle both the level discrepancy and this source-mix question at once.

**Further caveats, stated so they are not lost:** 2012–2014, a decade before the modelled
record; weekday-only sampling; the paper itself notes the traffic contribution "dropped
substantially" after January 2013 following a change to Kandy traffic regulations; and the
quantified factors sum to well under 100%, so an unapportioned remainder exists, part of which
the authors attribute to long-range transport landing inside the biomass factor.

## F.67 — ⚠ provenance: Nirmani's meteorology is reanalysis, not Sri Lankan station data (2026-08-22)

The user supplied the meteorological dataset Nirmani *et al.* (2025) cite (Kaggle
`rasulmah/sri-lanka-weather-dataset`). Inspected: **30 cities, 2010-01-01 → 2023-06-17**, with
the **Open-Meteo / ERA5 daily schema** (`weathercode`, `et0_fao_evapotranspiration`,
`shortwave_radiation_sum`, sunrise/sunset) and coordinates snapped to a 0.1° grid — Kandy at
**7.3 N, 80.6 E, elevation 510 m**.

It is **reanalysis, not observations**. Two consequences:

1. **No new information for this project.** ERA5 is already ingested natively at finer resolution,
   with WindNinja providing the terrain-resolved wind field. Nothing here is additive.
2. **It weakens Nirmani's local-source attribution at Kandy specifically.** Their CBPF analysis
   assigns local sources by wind speed and direction; for a station in a steep valley basin, a
   0.1° reanalysis wind cannot resolve channelled or drainage flow — the precise deficiency that
   motivated WindNinja here (gotcha family around `A_transport`). Their **concentration** numbers
   (F.65) stand on their own; their **directional source inference** for Kandy should be treated
   as weak evidence.

This does not affect F.65: Table 1's PM2.5 statistics come from NBRO, not from this dataset.

## F.68 — 🟢 A 25-site Kandy transect measured the spatial ceiling's CAUSE: the traffic signal is real and it is SUB-GRID (2026-08-22)

`references/papers/162-1-1080-1-10-20090108.pdf` — Elangasinghe & Shanthini (2008),
*J. Natl. Sci. Found. Sri Lanka* **36**(3):245–249. High-volume sampler (Envirotech APM 460,
cyclone attachment), PM10 on glass microfibre, **25 sites in and around Kandy**, 3-hour samples
**11:00–14:00**, dry days, **Jan 2004 – Jun 2006**, inlet at 1.5 m breathing height, with a
**traffic count taken at every site**.

This is the **densest spatial sampling of Kandy that exists**, and the project had never seen it.

### The measurement

| site | context | traffic (veh/h) | PM10 (µg/m³) |
|---|---|---:|---:|
| 4.2 Katugastota junction | A9, congested | **2640** | **340** |
| 3.1 Gatambe temple | Kandy–Peradeniya road | 1785 | 230 |
| 4.1 Kadugannawa bend | A1, climbing, uncongested | 1260 | 220 |
| 3.2 Botanical Gardens **entrance** | on the road | — | **110** |
| 2.1–2.3 in-city, inside school grounds | off-road, urban | — | **25–40** |
| 5.1–5.3 rural schools | <1 veh/min | — | **10–20** |
| 5.5 Botanical Gardens, **300 m from the road** | off-road, same garden | — | **4** |

**PM10 vs traffic intensity: R² = 0.82.** Seven of 25 sites exceed the 150 µg/m³ USEPA daily
standard on a 3-hour midday sample.

### 🟢 Why this matters more than any other Kandy record found this year

**110 → 4 µg/m³ over 300 metres, inside one botanical garden.** That is a ~27× decay across less
than a third of one model grid cell.

The programme has established a spatial ceiling of **ρ ≈ 0.2–0.28** six independent ways
(F.56/F.58/F.59/F.61) and explained it as *"regulatory and low-cost networks are convenience
samples, not a LUR design"*. That explanation was inferred from a 47-city panel. **This is the
first direct, local, quantitative measurement of the actual cause**, and it is a stronger and
more defensible statement:

> Kandy's within-city PM signal is **enormous** — a factor of tens — but its decay length is
> **tens to hundreds of metres**. A 1 km grid cell integrates over exactly that decay. The
> spatial pattern the model cannot recover is not absent from the city; it is **sub-grid by
> construction**, and no predictor at 1 km can recover it.

This converts the ceiling from *"our data are inadequate"* to *"the quantity is not defined at
the resolution we model"* — a change-of-support statement, which is precisely what the
observation operator in `MODEL_SPECIFICATION.md` §10.1 exists to express. It also retrospectively
justifies `Bud4`'s demotion (F.60/F.61): a spatial network of roadside monitors cannot make a
1 km `P` estimable, because the monitors and the grid cell are not measuring the same thing.

### ⚠ This does NOT resolve W6 — and must not be used to

Traffic explains **82% of the roadside PM10 spatial variance** here; Seneviratne 2017 puts
traffic at **7.6% of ambient PM2.5 mass** at a fixed suburban site (F.66). These are **not in
conflict and not the same quantity**: different pollutant (PM10 carries a large coarse road-dust
fraction that PM2.5 does not), different geometry (kerbside at 1.5 m vs ambient), and different
measurand (**variance explained across sites** vs **share of mass at one site**). Anyone tempted
to close W6 by citing R² = 0.82 is comparing a spatial-variance statistic with a mass fraction.

### A second, weaker use: an ambient bracket

The authors nominate their off-road urban sites as background: **25–40 PM10** in-city, **10–20**
rural. At a typical Sri Lankan urban PM2.5/PM10 of ~0.5–0.6 that implies roughly **13–24 µg/m³
PM2.5 in-city** and **5–12 rural** — which brackets the model's 17–21 basin mean. ⚠ Treat as
indicative only: the ratio is assumed rather than measured here, and the record is 2004–2006,
roughly fifteen years before the modelled period.

### Caveats, stated so they are not lost

PM10, not PM2.5 · **3-hour midday samples only** — and 11:00–14:00 spans the model's measured
diurnal **trough** (F.38), so these roadside values are high despite being drawn from the
cleanest hours of the day · dry days only · 2004–2006 · single 3-h sample per site, so no
temporal statistics and no formal uncertainty · site coordinates are given as descriptions, not
lat/lon, so a pixel-level comparison would require geocoding 25 place names.

### One agreement worth recording without overclaiming

The paper's **maximum is Katugastota**. The WindNinja drainage solver independently places the
model's **nocturnal** maximum down-valley at Katugastota (~28 vs core ~26). The agreement is
real but the mechanisms are different — a midday roadside traffic peak against a nocturnal
drainage sink — so this is a coincidence of location, **not** a validation of the transport
overlay, which remains unscored.

## F.69 — 🔴 THE SPATIAL AXIS TESTED AT KANDY FOR THE FIRST TIME: the model's whole dynamic range is 1.23×, the city's is 85× (2026-08-22)

F.68 recovered a 25-site PM10 transect of Kandy. This entry **geocodes it and scores the model
against it** — the first time the model's spatial pattern has been tested against a
within-Kandy observation set at all. `/tmp/elan_test.py`, result in `/tmp/elan_result.csv`.

**Geocoding** used OSM Overpass (the database, not Nominatim's search index, which mis-resolved
Kandy's Girls' High School to *Trincomalee*). 12 of the 25 sites carry a stated value or a stated
cluster range and fall inside the model bbox; Kadugannawa (obs 220) is 5 km west of the domain
and was dropped. Model = `additive_v3` q50, **2019–2023, hours 11–13 LT** to match the paper's
11:00–14:00 sampling window. Grid is **16×16 at 998 × 999 m**.

| id | site | obs PM10 | model PM2.5 | pixel |
|---|---|---:|---:|---|
| 4.2 | Katugastota junction | **340** | 25.06 | 7.3219, 80.6295 |
| 3.1 | Gatambe temple | 230 | 24.51 | 7.2680, 80.6023 |
| 1.1/1.2/1.4/1.7 | city roadside | **>150** | 23.6–25.4 | — |
| 3.2 | **Botanical Gardens ENTRANCE** | **110** | **23.90** | 7.2680, 80.5932 |
| 2.1/2.2/2.3 | city, inside school grounds | 25–40 | 24.0–25.4 | — |
| 5.1 | Gannoruwa school (rural) | 15 | **20.72** | 7.2859, 80.5932 |
| 5.5 | **Botanical Gardens, 300 m INSIDE** | **4** | **23.90** | 7.2680, 80.5932 |

### The paired-site test — this is the result

Two of the paper's sites are, by its own design, the **same place sampled at two microsites**.

| pair | separation | same pixel? | **observed ratio** | **model ratio** |
|---|---:|:---:|---:|---:|
| Bot. Gardens entrance vs 300 m inside | **303 m** | **yes** | **27.50×** | **1.000×** |
| Girls' High School junction vs inside grounds | 0 m | **yes** | **4.62×** | **1.000×** |

The model returns **identical values by construction**. The geocoding independently corroborates
the paper: the A1 passes **298 m** from the garden centroid against the paper's stated "about
300 m".

### 🔴 The headline number

| | spread across the 12 sites |
|---|---|
| **observed** | 4 → 340 µg/m³ = **85×** |
| **model** | 20.72 → 25.43 µg/m³ = **1.23×** |

**The model's entire dynamic range across Kandy is smaller than the difference between two points
300 metres apart inside one botanical garden.**

Rank correlation is **ρ = +0.44** (n=12, p=0.16) and **+0.58** on the 8 uncensored sites
(p=0.13) — **neither significant**, and consistent with the ρ ≈ 0.2–0.28 ceiling measured on the
47-city panel (F.56/F.61). What the model *does* get right is the coarse ordering: the rural
Gannoruwa site is its minimum (20.72) and Katugastota its near-maximum (25.06). **The ordering is
not wrong; the amplitude is compressed by a factor of ~70.**

### What this establishes, and what it does not

**Establishes.** The spatial ceiling is a **change-of-support limit, not a data-quality
complaint**. Kandy's within-city signal is enormous and its decay length is ~10²  m; the model
integrates over 1 km. No predictor, no network, and no learner operating on a 1 km grid can
recover a contrast that is averaged away inside a single cell. This is the strongest available
support for the F.60/F.61 demotion of `Bud4`, and it should be the way the limitation is stated
in the manuscript — a *definition* problem, not a *skill* problem.

**Does not establish.** That the model is wrong. Every site here is a **3-hour kerbside or
grounds sample at 1.5 m**; the model reports a **1 km areal mean**. Those are different
measurands, and the observation operator (`MODEL_SPECIFICATION.md` §10.1) exists precisely to
say so. A 1 km mean *should* sit near the middle of a distribution running 4 → 340, and it does.

### ⚠ Caveats, stated so they are not lost

**PM10, not PM2.5** — the 85× spread is inflated by coarse road dust that PM2.5 carries far less
of, so it is an **upper bound** on the PM2.5 contrast. ⚠ The paired ratios are within-pollutant
and unaffected. · 3-hour single samples, dry days, midday only, **2004–2006**, ~15 years before
the modelled record. · Four sites enter as **censored at ">150"**, which compresses the observed
rank at the top and biases ρ; the uncensored subset is n=8. · Cluster values 25–40 and 10–20 are
entered at their midpoints. · Site coordinates are geocoded from place descriptions, not
surveyed; the paired test is robust to this (both members move together) but the rank test is
not. · **n = 12 of 25** — the remaining 13 sites have no stated value, so a fuller test would
need the underlying Figure 1 data from the authors.

## F.70 — 🟢 A SECOND within-Kandy survey (NBRO, 30 sites) and the support-scaling ladder (2026-08-22)

Mining the reference lists of the Kandy papers (the Dhammapala method) produced a **second
spatial survey of Kandy**, retrievable free.

**Premasiri, Samarasinghe & Lakmali (2010)**, *Population exposure risk assessment to air
pollution in Kandy city area*, **National Building Research Organisation**, symposium volume.
⚠ **The NBRO domain has moved: `nbro.gov.lk` now 301-redirects to `nbri.gov.lk`.** Every NBRO
URL in this project's notes and letters should be updated.

**What it contains.** Active sampling of **PM10, NO₂ and SO₂ at 5 locations** (1 h / 8 h / 24 h),
plus **passive NO₂ and SO₂ at 28 locations in 2010 and 15 in 2011** (weekly, two weeks), across
the Kandy Municipal Council area (26 km², 120,000 residents plus ~100,000 daily visitors),
GIS-interpolated to a spatial AQI surface.

| site | PM10, 24 h (µg/m³) |
|---|---:|
| **Good Shed** (bus stand) | **89** |
| Trinity College | 65 |
| Tennis Court | 56 |
| Dalada Maligawa | 42 |
| **Wells Park** | **30** |

Their spatial conclusion: **AQI > 50 over less than 1% of the KMC land area** — "the core of
Kandy town covering two bus stands and its immediate surroundings" — with **99% of the
population** in AQI < 50. They attribute the pattern to vehicular emission and note evening
levels above morning, consistent with F.38 and with the accumulation mechanism.

### 🟢 The support-scaling ladder — this is the useful result

Three independent Kandy datasets now measure the *same city's* spatial contrast at three
different averaging supports:

| measurement | support | observed spread |
|---|---|---:|
| Elangasinghe 2008, 25 sites | **3 h, kerbside, 1.5 m** | **85×** |
| Premasiri 2010, 5 sites | **24 h, fixed sites** | **3.0×** |
| this model | **1 km, hourly→annual** | **1.23×** |

**The contrast collapses monotonically as the averaging support grows** — 85× → 3.0× → 1.23×.
That is exactly the behaviour a change-of-support argument predicts, and it converts F.69 from a
single striking comparison into a **quantitative scaling relationship measured in one city**.
It also reframes the model's 1.23× as *approaching the right answer for its own support* rather
than as a failure: at 24-h fixed-site support the true contrast is already down to 3×, and a
1 km areal mean must sit below that again.

⚠ **This does not make the model's 1.23× correct** — 3.0× at 24 h against 1.23× at 1 km is still
a gap, and these five sites all sit within roughly 1.5 km of one another in the core, so they
likely span only one or two model pixels. **Pending:** geocode the five sites and score the model
against them, as F.69 did for Elangasinghe. Overpass was unavailable when this entry was written;
the test is small and should be run.

### Caveats

2010; PM10 not PM2.5; **n = 5** for PM10 (the 28-site network measured NO₂ and SO₂ only, not
particulates); a symposium paper rather than a journal article, with no stated instrument model
or detection limits; and the AQI surface is GIS interpolation between sparse points, which F.60
established is a weak estimator. The **28-site passive NO₂ network is nonetheless the densest
Kandy air-quality sampling on record** and would be the natural target if the passive-sampler
route is ever revisited — noting F.45's demotion of passive NO₂ for `P_local`.

## F.71 — 🟢 A 20-site Kandy study completes the support ladder, sharpens W6, and fixes my PM2.5/PM10 assumption (2026-08-22)

Five further papers, supplied by the user after the reference-list sweep.

### 1. A fourth rung, and the ladder is now monotone across four supports

**Wickramasinghe, Karunaratne & Sivakanesan (2011)**, *Atmos. Environ.* **45**:2642–2650.
High-volume sampler, **8-hour** PM10 at **20 sites in Kandy**, stratified by land use *and* by
source strength — the only Kandy study that samples a designed spatial contrast.

| stratum | PM10 (µg/m³) | range |
|---|---:|---|
| **U/HT** urban heavy traffic | **167** | 92–221 |
| S/HT suburban heavy traffic | 143 | 117–153 |
| S/LT suburban light traffic | 104 | 82–126 |
| R/B/HF rural, high firewood | 90 | 55–134 |
| U/LT urban light traffic | 86 | (n=1) |
| **R/B/LOF** rural, low firewood | **83** | 65–101 |
| overall | 129 | 55–221 |

Stratum means span **2.0×**; individual sites span **4.0×**.

**The support-scaling ladder, now four rungs:**

| measurement | support | spread |
|---|---|---:|
| Elangasinghe 2008, 25 sites | 3 h, kerbside, 1.5 m | **85×** |
| Wickramasinghe 2011, 20 sites | 8 h, area-representative | **4.0×** (sites) / **2.0×** (strata) |
| Premasiri 2010, 5 sites | 24 h, fixed | **3.0×** |
| this model | 1 km, hourly→annual | **1.23×** |

Monotone collapse with increasing support, across four independent datasets in one city. The
**stratum means** are the closest analogue to what a 1 km cell represents — an areal average over
a land-use type — and at **2.0×** they are the nearest thing to a fair target the literature
offers. The model's 1.23× is below that, but by a factor of 1.6, not a factor of 70.

### 2. 🔴 W6 — the evidence now supports a GRADED emix, and both extremes are wrong

Wickramasinghe's source apportionment, from PAH signatures across the 20 sites:

- **"in the urban and suburban areas automobile emissions are the predominant daytime source"**
- **"domestic firewood burning is the major in rural areas, its commercial use has played a
  significant role in U/HT sites"**
- U/HT is "attributed principally by automobile emissions **and significant contribution from
  firewood combustion as well**"

This is the first evidence that **resolves the F.66 tension by geography rather than by choosing
a side**, and it vindicates the user's objection that Katugastota need not represent the core:

| | claim | verdict |
|---|---|---|
| `emix vehic = 0.85` ("~90% vehicular") | traffic overwhelmingly dominant everywhere | **REFUTED** (F.66) |
| traffic = 7.6% of mass (Katugastota) | traffic marginal | **bounds one suburban site**, not the core |
| **traffic predominant in the urban core, firewood co-dominant there and dominant rurally** | graded by land use | **supported** (this entry) |

⚠ **PAHs are a combustion tracer, not PM2.5 mass.** "Predominant source of PAHs" does not mean
"predominant share of PM2.5 mass" — PAH mass is a vanishing fraction of PM. What this licenses is
the **ordering and its spatial gradient**, not a percentage.

**Recommendation for `emix`:** Kandy's urban core is defensibly **traffic-led with a substantial
burning sector** — of order `vehic ≈ 0.5–0.6`, `burn ≈ 0.3–0.4` — rather than 0.85 or 0.08. ⚠ As
F.66 already noted, this is a **correctness fix with no expected skill gain** (the spatial ceiling
is a support limit, F.69/F.70), and the burning sector still has **no admissible FIRMS proxy**.

### 3. ⚠ CORRECTION to F.68 — my PM2.5/PM10 conversion was too high

F.68 converted Elangasinghe's PM10 to PM2.5 "at a typical Sri Lankan urban ratio of ~0.5–0.6".
**Measured Sri Lankan value: 0.40** — "40% of the PM10 fraction is composed of PM2.5 particles"
(Seneviratne *et al.* 2004, via Ileperuma 2020). The F.68 bracket was optimistic by ~25–50%.

Restated with 0.40: Elangasinghe's off-road in-city sites (PM10 25–40) imply **PM2.5 10–16**, and
his rural controls (10–20) imply **4–8**. Both now sit *below* the model's 17–21 basin mean rather
than bracketing it — which is expected, since those are the paper's *cleanest* sites, not areal
means. **The F.68 "ambient bracket" should be treated as withdrawn**, not tightened; it was the
weakest use of that paper and it is now the wrong sign.

⚠ A second source, **Premasiri *et al.*, "Particulate pollution and ratio of SPM:PM10:PM2.5 in
Colombo atmosphere"** (NBRO), **contradicts itself**: its abstract gives SPM:PM10:PM2.5 = **4:3:2**
(ratio 0.67) and says "65% is PM2.5", while its own results section says "**35% is PM2.5**". The
paper also notes sea spray sits in the coarse fraction, which pushes the ratio *down* and favours
the 0.35 reading. **Use 0.40, cite Seneviratne 2004, and do not cite the 4:3:2 figure.**
Colombo Fort annual PM10 **84**, Met Dept background **54** — an urban/background contrast of
1.56× at 24-h support, consistent with the ladder.

### 4. 🟢 CEA's Kandy station is confirmed, and its 2019 data is already published as a FIGURE

Ileperuma (2020), *Ceylon J. Sci.* **49**:225–238: **"In 2018, two automated air quality monitoring
stations were installed at Battaramulla and Kandy."** His **Figure 6 plots PM2.5 and PM10 at
Battaramulla and Kandy for 2019, sourced to the Central Environmental Authority.**

Two consequences. First, it **corroborates CEA's own account** of the Kandy AQMS (F.-block,
2026-08-12: hourly from 2019). Second, **a reference-grade Kandy PM2.5 series for the KOALA year
already exists in the published literature** — as a figure, so the numbers are not extractable
from the text, and I have **not** read values off it.

🔴 He also states the values "most … exceeded the Sri Lanka standards" and that **"the data for
Kandy are often higher than the corresponding values for Colombo."** ⚠ **Do not convert this into
a number.** It is ambiguous whether "most values" refers to PM10, PM2.5 or both, and if it means
24-h PM2.5 above the 50 µg/m³ standard it would be far above KOALA's 24.5 and the model's ~19.7.
That is a **flag on W11, not a measurement.** It should be resolved by the CEA data request, which
is now the only route (the Torrington Park BAM being defunct), and not by reading a figure.

### 5. Minor

**Meegahakotuwa & Nianthi (2018)**: **48 rain-gauge stations in Kandy District, 1981–2010**;
district annual mean **1840 mm**; and a **Katugastota (Kandy) Meteorological station record back
to 1875**. Consistent with gotcha #63, where IMERG landed at 0.98× the DoM Katugastota gauge.
Not additive to the model, but it names a long gauge record inside the domain.

⚠ **`airpollutionKandyVilani.pdf` is a scanned image** (CCITT stencil, no text layer) and was not
read. It needs OCR before it can be assessed.

## F.72 — 🟢 W2's founding citation READ AT LAST: it corroborates "seasonal, not chronic", and names a rural background site 8 km from Kandy (2026-08-22)

`references/papers/airpollutionKandyVilani.pdf` — **Abeyratne & Ileperuma (2006)**, *J. Natn.
Sci. Found. Sri Lanka* **34**(3):137–141. A scanned image with no text layer; read visually.

The project has cited this paper since the beginning as the origin of the transboundary framing
(`[Abeyratne2006]` in the manuscript) **without anyone having read it**. It is a stronger source
than assumed.

### Design

Passive diffusion samplers (Ferm 1991 type) for **NO₂, SO₂ and O₃**, weekly, exposed 4–6 days at
1.5 m, analysed colorimetrically/turbidimetrically. **Three sites:**

| site | role |
|---|---|
| **Bogambara** | congested Kandy city site |
| **King's Street** | Kandy city, 1 km away, less congested |
| 🟢 **Arambekade** | **rural background, 8 km from Kandy** |

**Feb 2002 – Dec 2004** for the two city sites; the background site to **July 2003**. Method
validated against the Colombo Fort automatic station over nine paired occasions per pollutant:
deviations **−10.45% (NO₂), +1.92% (SO₂), +5.88% (O₃)** — i.e. the passive method was checked
against a reference instrument, which is more than can be said for the FECT slopes (W5).

### 🟢 The transboundary result — and why it corroborates W2

Weekly means binned by monsoon (their Table 1, per-cent contribution):

| monsoon | SO₂ | NO₂ | O₃ |
|---|---:|---:|---:|
| south-west | 31 | 28 | 28 |
| **north-east** | **46** | **43** | **39** |
| inter-monsoon | 23 | 28 | 33 |

Their argument is a **spatial falsification test**, and it is a good one: Sri Lanka's major
domestic pollution source is the Western Province, **south-west** of Kandy, so a locally-driven
signal must peak in the SW monsoon. **The opposite is observed** — the maximum is in the NE
monsoon, when air arrives from the north-east, where Sri Lanka has no appreciable local sources.
The residual explanation is long-range transport from India and China, and SO₂ carries it most
strongly (46%) because those regions burn high-sulphur coal.

**This independently corroborates the project's W2 verdict** ([[project-w2-transboundary-verdict]]:
*Kandy is intrinsically clean and episodically loaded; the regional share is SEASONAL, not
chronic*), from a different decade, different pollutants and an argument the project did not use.
W2 was previously supported by our own decomposition plus trajectory work; it now has an external,
independent, published line.

### 🟢 A named rural background site in Kandy's own airshed

**Arambekade, 8 km out**, read **consistently lower for all three pollutants** than both city
sites. F.63 established that coastal Colombo (93 km) cannot serve as Kandy's background donor
(r 0.604 against a 0.923 benchmark), and F.64 flagged Nawalapitiya as a lead. Arambekade is a
second such site, and unlike Nawalapitiya it has a **published record of being operated as a
background station**. ⚠ Gas-phase only, 2002–03, passive weekly — **not** a PM background series.
It is a *siting* lead for any future campaign, not a dataset.

### ⚠ W6: this does NOT re-close it, and the reason matters

The paper states: **"Since there are no power plants or major industries around the Kandy city,
vehicular emissions are the main source for SO₂ in Kandy"** — with 65,000 vehicles/day entering
Kandy in 2003 and 85,000/day in 2004, and a fall in SO₂ after March 2004 tracking Ceylon
Petroleum's diesel sulphur cut from 0.50% to 0.25%. That last point is a genuine attribution: a
**fuel-composition change moved the signal**, which is about as clean a causal link to vehicles
as observational work gets.

**But SO₂ is not PM2.5 mass.** Wood is a low-sulphur fuel, so biomass burning produces little SO₂
and a great deal of particulate. "Vehicles dominate Kandy's SO₂" is therefore **fully compatible**
with "biomass burning contributes a large share of Kandy's PM2.5 mass" (F.66: 14.1% vs traffic's
7.6% at Katugastota). Reading this paper as vehicular dominance *of PM* would repeat exactly the
tracer-for-mass error F.71 warned about. **W6 stays as F.71 left it — narrowed to a graded
`emix`, not closed.**

### Two further numbers worth keeping

- **Kandy runs dirtier than Colombo in the gas phase.** Annual mean NO₂ **0.031 ppm** at Kandy vs
  **0.026 ppm** Colombo (2001); SO₂ **0.032 ppm** vs **0.018 ppm** — Kandy ~**1.8×** Colombo. This
  is a third independent statement of the same thing (Ileperuma 2020 says Kandy "often higher than
  Colombo"; Premasiri's NBRO study says the same), and it is relevant to **W11**: if Kandy really
  does sit above Colombo, a model that reads ~19.7 against Colombo's US-Embassy record deserves
  scrutiny. ⚠ Gases, not PM, and 2001 — a flag, not a measurement.
- Exceedance rates over the study: **NO₂ 14%, SO₂ 41%, O₃ 28%** of occasions above the Sri Lankan
  ambient standard; SO₂ 43% on the monthly averages.

## F.73 — 🟢 The budget ladder is NOT contaminated by change-of-support, and the bias runs the safe way (2026-08-22)

The claims audit raised that the panel's **spatial** arm compares a 1 km areal field with point
monitors. The obvious follow-up — *does the same defect contaminate the budget ladder, which is
the paper's second contribution?* — was asserted to be safe rather than tested. It has now been
tested. `/tmp/support_test2.py`.

### 1. The ladder's target is an aggregate, not a point

`modular_validation_all.py:119` — the scored quantity is
`s.groupby("date").pm25.mean()`, the **city-daily network mean over the withheld stations**, and
the tier inputs at line 177 are means over the selected stations. A network mean over *n*
stations approximates the areal mean far better than any single monitor, with a
representativeness error falling roughly as `1/sqrt(n)`. The mismatch is therefore **structurally
smaller than in the spatial arm**, where a single station is compared with a single pixel.

### 2. The residual bias is CONSERVATIVE — it understates our own claim

A support error enters as a common floor `s` added in quadrature to every tier's RMSE. Because
the ladder reports a **fractional** reduction, that floor **compresses** the measured gain:

| true gain | s=0 | s=2 | s=4 | s=6 |
|---|---:|---:|---:|---:|
| 30% | 30.0 | 28.6 | 25.1 | **20.9** |
| 50% | 50.0 | 47.2 | 40.5 | **33.0** |

**The reported step gains are a lower bound on the true value of information.** A reviewer
raising change-of-support against the ladder is arguing that our numbers are too *small*.

### 3. Empirically, rungs 1 and 2 show no dependence on target quality

If support error mattered, cities whose target is better estimated (more withheld stations)
should show systematically different gains.

| step | ρ vs `n_held` | p | many (n≥4) | few | Δ |
|---|---:|---:|---:|---:|---:|
| `Bud0→Bud1` | −0.207 | 0.162 | 22.3% | 22.8% | −0.5 pp |
| `Bud1→Bud2` | −0.136 | 0.363 | 0.0% | 0.0% | 0.0 pp |
| **`Bud2→Bud3`** | **+0.344** | **0.019** | **43.1%** | **28.1%** | **+15.0 pp** |

⚠ **The background rung does depend on network size**, significantly. But the natural explanation
is **not** support: `Bud3`'s background is an **outer-ring proxy drawn from the same network**, so
a city with more stations can build a genuinely better background — an effect already on record
as the standing caveat on that rung. Support and proxy-quality are confounded here and this test
cannot separate them. **State the caveat; do not claim the rung is clean.** Rungs 1 and 2 are
clean.

### 4. Consequence for the paper

§4 (the value of information) stands, with one added sentence stating that the reported gains are
a lower bound. **The change-of-support reframe is confined to the spatial arm**, exactly as the
claims audit assumed — but it is now measured rather than assumed.

## F.74 — 🔴 "Four guaranteed properties" is wrong: two guarantees, one mechanism, one unrun (2026-08-22)

`MODEL_SPECIFICATION.md` §132–137 and §179–185 were read against what has actually been run,
because a reviewer will go straight here.

| | claim | reality | how it must be stated |
|---|---|---|---|
| **P1** conservation | "C1 holds at every budget and every parameter value" | analytic, plus `T1` across the parameter box. ⚠ But the built field runs **+0.39 to +0.56% above the anchor** | **a guarantee of the formulation**, realised in the build "to within 0.6 per cent" |
| **P2** monotonicity | "skill does not decrease as budget increases" | **not a theorem** — it is *enforced* by CV-selected shrinkage and then *demonstrated*: **46/47 cities (97.9%)**, and **47/47 (100%)** if the `Bud3` rung is excluded. The single violation is city 3147 | **a design mechanism with measured support**, never "guaranteed" |
| **P3** exact nesting | bit-exact reduction of `Bud_i` to `Bud_{i-1}` | **genuinely proven and tested** — parameterised byte-comparison over every adjacent tier pair | **the strongest claim in the set**; lead with it |
| **P4** declared identifiability | profile-likelihood interval per parameter per budget | **machinery ready, NOT RUN** | **a commitment, not a property.** Either run it before submission or demote it explicitly |

🔴 **"Four guaranteed properties" must not appear in the paper.** The defensible statement is
**two guarantees (P1, P3), one enforced-and-measured mechanism (P2, 97.9%), and one commitment
not yet discharged (P4)**. P4 is the exposed one: presenting an unrun analysis alongside a
bit-exact test in a list headed "guaranteed" is the kind of thing that costs a reviewer's trust
across the whole paper.

**Recommended action before submission:** run P4. The machinery exists (`src/modular/`), and a
profile-likelihood sweep per budget is cheap next to what has already been spent. If it is not
run, P4 must be reworded as a declared design intent and dropped from any list of properties.

## F.75 — 🟢 P4 RUN AT LAST: identifiability per parameter per budget, and the one identifiable parameter was never fitted (2026-08-22)

F.74 found P4's machinery "ready, not run" and recommended running it before submission. Done:
`scripts/p4_identifiability.py`, three fitting cities (Medellín, Kathmandu, Chiang Mai), real
emission surfaces, real terrain, real station coordinates, real observation noise. Profile
likelihood per parameter per budget; 95% interval from `Δ(−2 log L) ≤ 3.84`; a parameter whose
interval spans its whole prior box is UNIDENTIFIED. Output
`data/processed/modular/p4_identifiability.csv` (45 rows).

**Median fraction of the prior box covered by the 95% interval (1.00 = wholly unidentified):**

| parameter | `Bud1` (2 stn) | `Bud2` (8 stn) | `Bud3` (+background) |
|---|---:|---:|---:|
| **`s_exp`** emission-surface exponent | **0.00** | **0.00** | **0.00** |
| `a_cap` transport amplitude cap | 0.33 | 0.00 | 0.00 |
| `kappa` terrain confinement | **1.00** | 0.33 | 0.67 |
| `eps0` ventilated-hour floor | **1.00** | 0.50 | 0.50 |
| `w_evening` e(t) evening lobe | **1.00** | 0.67 | **1.00** |

**12 of 45 fits saturate a bound** — reported here rather than hidden, as the specification
requires.

### Three standing project claims independently corroborated

This analysis shares no method, no data and no code path with the results it reproduces.

- **`kappa` is unidentifiable at a two-sensor budget.** The U7 cross-check reached the same
  conclusion by a completely different route (δz-confinement is collinear with NTL-source on the
  valley floor) and κ was kept as a prior at 0.15. **P4 confirms it, and quantifies the budget at
  which it changes: 8 stations.**
- **`eps0` is not determined.** W7/F.30 closed as "inside a pooled bracket, not contradicted but
  not determined". P4 says the same: wholly unidentified at `Bud1`, still only half-constrained
  at `Bud2`.
- **`w_evening` is weak everywhere.** F.29 set it by shrinkage at 0.40 rather than fitting it.
  P4 says it could not have been fitted at any budget tested.

### 🔴 The finding that is new, and awkward

**`s_exp` is identified at *every* budget including Kandy's own — and it has never been
estimated.** `diff_decomp.py` documents it as "implicitly 1.0, never tested", and production
carries it at 1.0 by default.

So the single parameter the data can actually constrain is the one the project never fitted,
while three of the four that were argued over at length are the ones the data cannot constrain.
That is exactly the inversion a declared-identifiability analysis exists to catch, and it is an
argument for P4 belonging in the paper rather than in an appendix.

**Action:** fit `s_exp` at Kandy's `Bud1` and report it with its profile interval. ⚠ Expect the
spatial *rank* to be unmoved — `s_exp` is a monotone transform of `S_emit`, so it cannot change
Spearman ρ (a trap already recorded once). What it can change is the **contrast amplitude**,
which is precisely the quantity F.69/F.71 showed is too compressed (1.23× against a fair target
of ~2.0×). **This is the first concrete, evidence-backed route to the amplitude problem.**

### Caveats

Simulation-based recovery on real geometry, not a fit to real observations — which is the correct
design for a question about the *budget* rather than about one fit, but it assumes the model is
correctly specified and so gives an **optimistic** bound: a parameter unidentifiable here is
unidentifiable in practice, while one identified here may still fail against real data.
`H = 96` hours, grid of 7, 150 Adam steps per profile point; `a_trans`, `w_blh`, `e_prior` and
`e_fit` are drawn as realistic surrogates rather than loaded per city.

## F.76 — 🔴 The support-collapse mechanism is REAL but MODEST; my four-rung "ladder" framing is confounded and must be restated (2026-08-22)

Run to defend F.71's support ladder against the obvious objection that its four rungs come from
four incompatible studies. `scripts/support_collapse_test.py`, three cities with dense networks,
same instrument class and era within each city. Across-station contrast (p90/p10, median over
time steps, ≥5 concurrent stations) as a function of averaging window.

| window | Medellín | Kathmandu | Chiang Mai |
|---|---:|---:|---:|
| 1 h | **2.53** | **1.84** | **1.82** |
| 3 h | 2.16 | 1.72 | 1.76 |
| 8 h | 1.91 | 1.54 | 1.65 |
| 24 h | 1.71 | 1.38 | 1.56 |
| weekly | 1.57 | 1.29 | 1.48 |
| monthly | 1.51 | 1.26 | 1.49 |
| annual | **1.50** | — | — |

**Monotone in Medellín and Kathmandu; Chiang Mai breaks by +0.01 at one step (within noise).**

### 1. 🟢 The mechanism is confirmed

Contrast does fall monotonically with averaging support in real, internally consistent,
same-instrument data. That was the thing to establish and it is established.

### 2. 🔴 But the effect is SMALL, and that refutes my framing of F.71

Total collapse from 1 h to the longest window: **1.69× (Medellín), 1.46× (Kathmandu),
1.22× (Chiang Mai)**. The Kandy ladder runs **85× → 1.23×, a factor of 69**.

**Temporal averaging therefore explains only a small fraction of the Kandy ladder.** I presented
that ladder as a clean "collapse with averaging support" and proposed it as the paper's headline
figure. That framing is **confounded**: across its four rungs, *support* and *siting design* move
together. Elangasinghe deliberately sampled from a bus terminus to the inside of a botanical
garden — the extremes — while the 8-hour, 24-hour and model rungs progressively do not. Most of
the 69× is **siting contrast**, not averaging.

**This is the same error the remediation plan recorded in its own §1** — several measurements
agreeing is not confirmation when they share a structure — and I made it again, one level up. The
test was run to catch exactly this, and it caught it.

### 3. 🟢 What survives, and it is stronger than the ladder

**F.69's paired-site result is unconfounded and it carries the argument alone.** Two microsites
**300 m apart, both 3-hour samples, both in one 998 m pixel**: observed **27.5×**, modelled
**1.000×**. Support is held fixed; only location varies; the model cannot represent the
difference *by construction*. That is a direct demonstration that the signal is sub-grid, and it
needs no scaling law.

### 4. 🟢 And a genuinely new number: at MATCHED support the model is close to right

The fair comparison is like-for-like — annual, network-scale contrast:

| | annual p90/p10 |
|---|---:|
| Medellín observed | **1.50** |
| Kathmandu observed (monthly) | 1.26 |
| Chiang Mai observed (monthly) | 1.49 |
| **Kandy, this model** | **1.23** |

**At matched averaging support the model's within-city contrast sits inside the observed range.**
The apparent catastrophic failure (1.23× against 85×) was almost entirely an artefact of
comparing an annual areal mean with 3-hour kerbside samples. ⚠ The model is at the **low end** —
1.23 against 1.26–1.50 — so it is plausibly still slightly under-contrasted, which is consistent
with the `s_exp` route in F.75. But it is not out by a factor of 70, and the paper must not imply
it is.

### 5. What the paper must now say

- **Lead with the paired-site test**, not the ladder. It is clean, visual, and unconfounded.
- **Report the temporal collapse as a verified secondary mechanism** with its real magnitude
  (1.2–1.7×), not as the explanation for the whole gap.
- **Report the matched-support comparison** — this is the honest statement of the model's spatial
  amplitude, and it is far more favourable than anything previously claimed.
- **State plainly that the Kandy literature rungs confound support with siting design**, and that
  the siting component is the larger one. That is a limitation of the *literature*, not of the
  model, and saying so pre-empts the reviewer who spots it.

⚠ The spatial half of the support effect — what happens when a point is averaged over 1 km —
**cannot be measured from point networks at all**. That is why the Kandy literature, which samples
at 300 m separations, is needed for it, and why F.69 remains the load-bearing evidence.

## F.77 — 🟢 THE AMPLITUDE QUESTION CLOSES: the shipped field is already right for its support, and `s_exp` must not be changed (2026-08-22)

F.75 found `s_exp` identifiable but never fitted, and flagged it as "the first evidence-backed
route to the amplitude problem". Fitting it settles the amplitude problem in the opposite
direction to the one expected. `scripts/fit_s_exp.py`.

### 1. `s_exp` cannot be fitted at Kandy, by construction

**Akurana (7.366 N) is outside the 15 × 15 km domain** (gotcha #49). Only Hantana is in-domain,
so Kandy has **one** usable sensor and a spatial-contrast parameter is unfittable there. It must
be fitted on the panel and transferred — the eps0 situation exactly (W7/F.30).

### 2. Fitted on the panel, it does not transfer — and it points the wrong way

Matching the model's across-station contrast to the observed, at matched support:

| city | stations | observed p90/p10 | model at `s_exp=1` | fitted `s_exp` |
|---|---:|---:|---:|---:|
| Medellín | 20 | 1.469 | **2.059** | **0.45** |
| Chiang Mai | 10 | 1.349 | **3.844** | **0.25** (saturated) |

Kathmandu had only 6 in-domain stations and was skipped. Fitted values span **0.25–0.45, a
ratio of 1.8×** — **does not transfer**, the same verdict as eps0.

And the sign is the opposite of the expectation: I predicted `s_exp > 1` to *raise* amplitude.
The data say **< 1** — the traffic surface needs damping, not sharpening.

### 3. 🔴 The reason: the two candidate surfaces bracket observation by orders of magnitude

| surface | p90/p10 | max/min |
|---|---:|---:|
| **`S_emit`** (VanD satellite — the **headline** `P_local`) | **1.11** | 1.18 |
| *observed annual network contrast* | *1.26 – 1.47* | — |
| **`S_traffic`** (centrality × EF — used in `A_transport`) | **22.7** | **2,168,202** |

The satellite surface is far too flat; the traffic-centrality surface is far too sharp. ⚠ That
max/min of 2.2 million is a near-zero minimum at unroaded pixels — a numerical property of
log-tempered centrality worth knowing about, and a reason the surface is only ever used
multiplicatively inside a normalised, capped amplitude term.

**The panel fit was measuring `S_traffic`, not the headline surface.** That is why it demanded
damping.

### 4. 🟢 And the shipped field is already close to right, like for like

| | annual p90/p10 |
|---|---:|
| **Kandy, shipped field** | **1.232** (max/min 1.392) |
| Kathmandu observed | ~1.26 |
| Chiang Mai observed | 1.35 |
| Medellín observed | 1.47 |

Statistic, support and averaging period all matched. **The shipped field sits just below the
observed range, not outside it.**

⚠ This also corrects a statistic mismatch in **F.76**, which compared the model's *max/min*
(1.23, from F.69's 12 site pixels) against observed *p90/p10*. The like-for-like model value is
**p90/p10 = 1.232** — numerically almost identical by coincidence, so F.76's conclusion is
unaffected, but the comparison there was not strictly like for like and this entry supersedes it.

### 5. Verdict

**There is no amplitude crisis, and `s_exp` stays at 1.0.**

The apparent catastrophe of F.69 — 1.23× modelled against 85× observed — was a change-of-support
and siting artefact. F.76 removed most of it; this removes the rest. The model's spatial
**amplitude** is approximately correct for the support it reports at. What it cannot do is place
that contrast correctly, which is the measured ρ ≈ 0.2–0.28 ceiling and a separate, genuine,
already-documented limitation.

**Do not change `s_exp` in production.** Report it as *identifiable, fitted on the panel, found
non-transferable (0.25–0.45), and therefore held at its prior of 1.0* — which is a complete and
honest P4 disclosure, and the same treatment eps0 already receives.

## F.78 — 🔴 THE COLOMBO ZERO-SHOT TEST FAILS, and every registered prior was wrong (2026-08-22)

🔴 **RETRACTED AS STATED; see F.86/F.87 (2026-08-23).** Scored against the under-powered `Bud0` of F.84. With a spec-compliant `Bud0c` the level bias goes **+31.3% → −4.4%** and seasonal r **0.55 → 0.93**. What survives: no day-to-day skill beyond climatology.

Pre-registered at **https://osf.io/nxqgb/**, registered `2026-08-22T17:29:53Z` — **before
`scripts/colombo_zeroshot_test.py` existed**. This is the project's only third-party-verifiable
registration. Design, gates and priors were fixed there and are unchanged here.

### The technical pre-check passed, so this is a real result

The pre-registration's §7 required that Colombo's driver distributions fall inside the panel's
per-feature ranges before any scoring, precisely so a units or aggregation mismatch could not be
mistaken for a regime failure. **All seven features passed** (temperature 300.8 K inside
[265.6, 308.8]; BLH 553 m inside [51, 1601]; etc.). The failure below is not an artefact.

### Result — 1,661 days against the US Embassy BAM

| gate | value | criterion | |
|---|---:|---|---|
| **C-G1** daily RMSE | **17.68** | within [13.43, 45.54] | **PASS** |
| **C-G2** seasonal r | **0.550** | ≥ 0.60 | **FAIL** |
| **C-G3** level bias | **+31.3%** | \|bias\| ≤ 40% | **PASS** |
| **C-G4** R² vs day-of-year climatology | **−4.069** | > 0 | 🔴 **FAIL** |

Plain R² against the mean: **−0.896**. Observed mean 20.54, modelled **26.96**.

**C-G4 was registered as the decisive gate and it fails catastrophically.** The sensorless tier
is roughly **five times worse than simply knowing the date**, and worse than predicting the
long-run mean. The two passes are hollow: C-G1 passes only because the band was calibrated on a
panel containing far dirtier tropical cities, and C-G3 passes only because +31.3% happens to sit
under an arbitrary 40%.

### 🔴 All three registered priors refuted, one with the wrong sign

| prior | outcome |
|---|---|
| seasonal r ≥ 0.6 | **0.550 — refuted** |
| level **15–40% LOW** (sea salt unrepresented) | **+31.3% HIGH — refuted, wrong sign** |
| "survives on seasonal and daily, fails on level" | **exactly inverted — refuted** |

I reasoned that unmodelled marine aerosol would make the model read low. The opposite happened.
The likely mechanism is the reverse: the panel's tropical arm is dominated by much dirtier South
Asian and African cities, so the learner maps tropical-monsoon drivers onto high concentrations,
while Colombo is a **well-ventilated coastal city that is clean for its band**. Sea-breeze
ventilation is invisible to the seven drivers.

### What this bounds

🔴 **"The sensorless tier works anywhere" is refuted.** It fails at a coastal city **in the same
country and monsoon as the target**. Any claim of general applicability must now be stated as
**valley and basin regimes**, which is what the panel that supports it actually sampled.

🟢 **It does not invalidate Kandy**, which is a valley basin, in regime, and — importantly — is
**not run at `Bud0`**. Kandy's production chain is `Bud1`: it has two local sensors and a
satellite level anchor.

🟢 **And it is arguably the strongest demonstration in the programme of why the budget ladder
matters.** The registered ladder result is that `Bud0→Bud1` buys a **38.5% median RMSE reduction
in the deep tropics**. Colombo shows what `Bud0` alone is worth out of regime: less than
climatology. The paper's thesis is that the information budget must be declared and its value
measured — and here is a city where the sensorless budget is simply **not sufficient**, stated
with the threshold written down beforehand.

### Caveats

One city, one point monitor. The change-of-support limit (F.69/F.77) applies to this comparison
as to every other. Higher rungs could not be tested — Sri Lanka has too few OpenAQ stations to
populate `Bud1`+ — so **this bounds the sensorless tier only**, and the natural follow-up (does
`Bud1` rescue Colombo?) is unanswerable with public data. ⚠ The pool built 48 cities against the
ladder's 47; one city yielded drivers but no ladder row. Immaterial to this result, worth a check.

**Per the stopping rule, this is reported once, as run. No re-specification.**

## F.79 — 🟢 P2 is NOT violated: the "46/47" was our own gate counting a missing rung as a failure (2026-08-23)

F.74 recorded P2 (monotone skill under added data) as holding at **46/47 cities, 97.9%**, with
one unexplained violation. Chasing the exception dissolved it.

**City 3147** (subtropical, OpenAQ, `n_held=3`, 282 days):

| rung | RMSE |
|---|---:|
| `Bud0` | 17.973 |
| `Bud1` | 12.679 |
| `Bud2` | 12.665 |
| `Bud3` | **NaN** |

**Every rung it has improves.** It has only three because with `n_held = 3` there are too few
stations to form `Bud3`'s outer-ring background proxy, so that rung is *undefined*, not worse.

🔴 **The gate counted it as a failure because it fills a missing rung with `+inf`** —
`modular_validation_all.py:268`, `L.rmse_Bud3.fillna(np.inf) <= L.rmse_Bud2`. A city that cannot
form a tier is treated as a city where more data made things worse.

**Corrected:**

| statement | value |
|---|---|
| monotone on `Bud0→Bud1→Bud2`, all cities | **47/47** |
| monotone on every rung that **exists** | **47/47** |
| monotone among the 46 cities with all four rungs | **46/46** |

**P2 holds at 47/47.** The 97.9% figure understated it and must not be quoted again. ⚠ The same
`fillna(np.inf)` sits in the production gate and should be corrected there, or the V1 gate will
keep reporting a violation that does not exist.

This is a strengthening found only by chasing an exception rather than reporting it as noise —
and it is the second time this session that a "failure" turned out to be an artefact of our own
measurement (cf. F.73, where a support penalty proved to bias the ladder conservatively).

## F.80 — ⚠ The P1 drift explained: the stored pattern's mean is ~1.004, not exactly 1 (2026-08-23)

The shipped field runs **+0.39 to +0.56%** above its anchor every year and the project reports
conservation "to within 0.6 per cent" **without knowing what consumes the 0.5%**. Diagnosed.

| year | field basin mean | `T_q50` | drift |
|---|---:|---:|---:|
| 2019 | 19.7517 | 19.6614 | **+0.459%** |
| 2020 | 19.0923 | 19.0188 | +0.386% |
| 2021 | 17.0786 | 16.9976 | +0.477% |
| 2022 | 18.7550 | 18.6509 | **+0.558%** |
| 2023 | 21.0377 | 20.9328 | +0.501% |

### It is systematic, one-sided, and proportional to accumulation

- **100.00% of hours drift positive. Not one hour is exact.**
- Absolute drift: median +0.011, mean +0.105, max +2.39 µg/m³.
- `corr(absolute drift, T) = +0.494` — the drift scales with concentration.
- Cleanest decile of hours **+0.052%**; dirtiest decile **+0.810%**.
- 🔴 **Not a quantile artefact.** q05, q50 and q95 all drift alike (+0.27, +0.37, +0.37%), so
  this is not "mean of a median field ≠ median"; the whole field sits above its anchor.

### Mechanism

The formulation is analytically exact: with `mean(P) = 1`, `mean(PM) = T` in both the
`acc ≥ eps0` and `acc < eps0` branches. But if `mean(P) = 1 + e`, then
**`mean(PM) − T = acc · e`** — always positive for `e > 0`, and proportional to accumulation.
That is exactly the observed signature.

**Implied `mean(P_local) ≈ 1.004`, not 1.000.**

The most likely source is the pattern-recovery step: gotcha #65 records that `P` is recovered by
inverting the split (from the **q95** side) and that a **bounded (month, hour) climatology is
substituted where the increment is too small to invert**. A substituted climatology has no reason
to carry a mean of exactly 1, and injecting it on a subset of hours would produce precisely this
small, one-sided, accumulation-proportional excess.

### What to say, and what to do

**Say:** P1 is a guarantee of the *formulation*, realised in the *build* to **within 0.6 per
cent**, and the residual is a normalisation drift of the stored pattern (~0.4%), not a failure of
the conservation identity. That is a stronger and more honest statement than the current silent
"to within 0.6%".

**Do (optional, low priority):** renormalise `P` to unit mean after the climatology substitution.
⚠ Expect the basin means to move by ~0.4% — which would change every published annual figure by
that amount, so it must not be done casually before submission. **Recommend documenting rather
than fixing**, since the effect is smaller than every uncertainty the paper reports.

## F.81 — 🟢 The budget ladder is a property of the INFORMATION, not the estimator: even a linear model reproduces it (2026-08-23)

🔴 **RE-RUN AND REFUTED at `Bud0c` — see F.88 (2026-08-23).** On the spec-compliant 68-feature bottom rung the linear model **collapses** (RMSE 35.0 vs 18.9) and the first-rung spread goes from 1.8 pp to **38.5 pp**. The surviving claim is *robust across NON-LINEAR estimators*, never *"even a linear model reproduces it"*.

The whole value-of-information result rests on one `HistGradientBoostingRegressor` with one
hyperparameter setting. If the step gains moved when the estimator changed, the ladder would be a
property of that learner rather than of the observations. Tested with four estimators spanning
boosting, bagging and a plain linear model. `scripts/tier2_robustness.py`.

| `Bud0` learner | median `Bud0` RMSE | `Bud0→Bud1` | `Bud1→Bud2` | `Bud2→Bud3` |
|---|---:|---:|---:|---:|
| HistGBM (shipped) | 20.96 | 23.6% | 0.0% | 40.1% |
| HistGBM shallow (depth 3) | 20.25 | 24.1% | 0.0% | 37.9% |
| RandomForest | 20.74 | 22.4% | 0.1% | 39.6% |
| **Ridge (linear)** | 20.56 | **24.2%** | 0.0% | **36.8%** |
| **spread** | 0.7 | **1.8 pp** | **0.1 pp** | **3.3 pp** |

### 🟢 A linear model reproduces the ladder

This is stronger than the robustness check it was meant to be. **Ridge regression on seven
drivers recovers the same step gains as gradient boosting** — 24.2% vs 23.6% on the first rung,
36.8% vs 40.1% on the background rung — and reproduces the flat middle rung exactly.

The consequence for the paper: **the value of each observation increment is a property of the
information, not of model capacity.** The ladder cannot be dismissed as an artefact of a
particular learner or of over-fitting, and the contribution does not depend on any ML
sophistication at all. That is a considerably more durable claim than "our GBM improves when we
give it more data".

It also reinforces the standing conclusion that the binding constraint is **data content, not
model class** — the same finding the dynamic-transport and spatial nulls reached from the other
direction.

⚠ Median `Bud0` RMSE here is 20.96 against `ladder_all.csv`'s 21.19: this run's pool built 48
cities to the ladder's 47 (one city yields drivers but no ladder row, noted in F.78). Immaterial
to the comparison, since all four learners share the same pool.

⚠ The monotone percentages printed by this script (91–96%) carry the **`fillna(np.inf)` defect of
F.79** and understate P2. Corrected: P2 holds on every rung that exists.

## F.82 — 🟡 The v3 R² finally has an interval, and H3's "near-miss" is not distinguishable from a pass (2026-08-23)

The Stage A v3 pooled LOMO R² of **0.581** has been a single-run point estimate since 2026-05 and
was listed as open housekeeping. Bootstrapped.

**Cluster bootstrap over the 53 non-empty LOMO folds** (B = 2000) — clustered because rows inside
a station-month fold are not independent:

| | point | 95% CI |
|---|---:|---|
| **R²** | **0.5814** | **[0.4849, 0.6441]** |
| RMSE | 7.784 | [7.079, 8.511] |

### 🟡 The consequence for H3

The pre-registered gate was **R² ≥ 0.60**, closed as an "honest near-miss at 0.581".
**The 95% interval includes 0.60.** The data therefore **do not distinguish a pass from a
failure** on this gate. Calling it a near-miss was directionally right and is now quantified: the
point estimate misses, the interval covers.

The paper should state it that way — *0.581, 95% CI [0.485, 0.644], not separable from the 0.60
threshold at this sample size* — rather than either claiming the gate or conceding it.

### ⚠ A methodological point worth carrying

A **naive i.i.d.** bootstrap gives **[0.563, 0.597]** — **4.7× narrower**, and it would have
*excluded* 0.60 and licensed the confident claim "significantly below the gate". Ignoring the
fold structure would have produced exactly the wrong conclusion with apparent precision.

⚠ Caught en route: `q50_blend` in `predictions_blend_v3.parquet` is already the **absolute**
prediction, not the residual. Adding `c_prior_anchored` to it (the natural reading of the v3
architecture) gives **R² = −3.56**. The column is post-reconstruction. Anyone recomputing v3
metrics should verify against the recorded 0.581 before trusting a number.

## F.83 — 🔴 Colour-vision check, never run before: three palettes pass, `turbo` fails (2026-08-23)

The locked palette set has never been checked for colour-vision deficiency, which affects roughly
8% of male readers. Simulated deuteranopia, protanopia and tritanopia and tested each map for
**monotone lightness** — the property that lets a reader with CVD still read high from low.

| palette | role | monotone under all three simulations? |
|---|---|---|
| **YlOrRd** | PM heatmaps (headline) | ✅ yes |
| **inferno** | emission surfaces | ✅ yes |
| **magma** | uncertainty | ✅ yes |
| **RdBu** | signed/diverging | ✅ non-monotone *by design*; both arms stay distinguishable — red–blue is CVD-safe where red–green is not |
| 🔴 **turbo** | **episode scale** | ❌ **NOT monotone — under normal vision or any simulation** |

**`turbo` is the only failure, and it is used for the episode scale** — the nowcast panel switches
to it whenever the field's 98th percentile exceeds 35 µg/m³ (WHO IT-1). So the palette chosen for
the *most consequential* maps in the product is the one a reader cannot reliably order. Its
lightness range also collapses from 0.768 under normal vision to **0.542 under tritanopia**.

Turbo is a rainbow-family map; non-monotone lightness is a known property of the family and is not
specific to CVD — even a normal-sighted reader can misread ordering in it.

**Recommendation:** replace `turbo` on the episode scale with **inferno**, which is already in the
locked set, passes every simulation, and remains visually distinct from YlOrRd so the "this is an
episode" signal is preserved. ⚠ Cheap to change, but it alters published figures — do it once,
deliberately, as part of the figure rebuild rather than piecemeal.

**Still pending:** the Premasiri 5-site pixel test. Overpass was unavailable on both attempts. Its
value fell after F.76 showed the four-rung ladder confounds support with siting, so a fifth rung
adds little; what it would still give is a second within-Kandy check at 24-h support.

## F.84 — 🔴🔴 THE VALIDATED `Bud0` IS NOT THE SPECIFIED `Bud0`: the ladder's bottom rung is under-powered by two of its three admitted streams (2026-08-23)

**Raised by the user from first principles, verified, and confirmed.** This is the most serious
defect found in the programme, and it reaches the headline number.

### The three layers disagree

| layer | what `Bud0` is |
|---|---|
| **specification** — `budgets.py:81`, `_BASE` | `SATELLITE_LEVEL` + `DRIVERS_REANALYSIS` + `STATIC_GEO` |
| **pre-registration** — `prereg_modular_validation_v2`, §2 table | "drivers **+ static covariates**, no observation of this city" |
| 🔴 **implementation** — `modular_validation_all.py:43`, `FEATS` | `temperature_2m`, `u/v` wind, `wind`, `boundary_layer_height`, `doy_sin`, `doy_cos` — **drivers only** |

**The scored `Bud0` uses one of its three admitted streams.** It has no satellite level, no
terrain, no population, no road network, no emission proxy. It is not "sensorless"; it is
**meteorology-only**, and it knows nothing about the place beyond its weather.

### What this invalidates

🔴 **The headline `Bud0→Bud1` gain of ~24% is inflated**, because the baseline it is measured
against is artificially weak. A `Bud0` carrying a satellite level anchor starts far closer to the
truth, so the marginal value of the first two stations must be **smaller** — possibly much
smaller.

🔴 **The `Bud2→Bud3` background gain (~38–40%) is also suspect**, and in the same direction: a
satellite level product already carries regional information, so part of what the background rung
currently "buys" may simply be information `Bud0` was entitled to and never given.

🔴 **The Colombo failure (F.78) was scored against this strawman.** Its diagnosis stands —
the tier has no information about the place — but that is now revealed as an *implementation*
deficiency rather than a property of sensorless estimation, which is a materially different
claim. **F.78 must be re-run before it is reported.**

🔴 **The production Kandy chain is not the panel's `Bud1`.** Production re-anchors to Van
Donkelaar annually; the panel's `Bud1` is meteorology + two sensors. The tier validated and the
tier shipped are different objects.

### What survives untouched

- **P3** bit-exact nesting — structural, independent of feature content.
- **The change-of-support results** (F.68/F.69/F.76/F.77) — a different axis entirely.
- **P4 identifiability** (F.75) — run on the decomposition parameters, not the ladder.
- **The qualitative finding that the background rung is the largest step** may well survive, but
  its *magnitude* cannot be quoted until re-run.
- **Learner-independence** (F.81) survives as a statement about estimator choice, but it was
  measured on the wrong `Bud0` and should be re-run alongside.

### 🔴 The deeper architectural finding

**The admissibility machinery is one-sided.** `budgets.require()` raises when a tier *touches a
stream it does not admit* — it prevents cheating upward. **Nothing checks that a tier uses what it
is entitled to.** A rung can silently under-use its budget, which inflates every gain measured
above it, and the registry will pass it.

Gate **V2** asked only whether `Bud0` was *genuinely sensorless* (LOCO excludes the target city's
stations — it does). Nobody asked whether `Bud0` was *genuinely `Bud0`*.

**Fix:** add the dual check — assert that each tier's fitted feature set **covers** its admitted
streams, not merely that it does not exceed them. This is the same class of error as gotcha #73
(admissibility enforced by discipline rather than construction) and belongs in `budgets.py`.

### Remediation

1. Rebuild `Bud0` with **`STATIC_GEO`** — available now for all 47 cities from
   `lur_predictors.csv` (roads at five radii, NDVI, tree cover, water, land cover, built volume,
   population, night lights, 636 stations).
2. Add **`SATELLITE_LEVEL`** — needs a per-city satellite PM2.5 pull; not currently on disk for
   the full panel.
3. Re-run the ladder, the learner-sensitivity check, and **Colombo**.
4. Re-register before re-running Colombo, since the design has changed materially.

⚠ **Expect the ladder to flatten.** If it does, that is a finding — *a satellite level anchor
substitutes for local stations* — and arguably a more useful one for the network-design audience
than the current numbers. It must not be presented as a disappointment, and the current numbers
must not be quoted in the interim.

## F.85 — 🟡 THE RE-VALIDATED LADDER: the old numbers were inflated but the story survives; five of eight registered priors refuted (2026-08-23)

Pre-registered at **https://osf.io/g6hqb/** (2026-08-23T04:21:32Z), before the satellite pull and
before any number existed. `scripts/revalidate_ladder.py`, `ladder_revalidated.csv`.

**R-G3 passed in the live pipeline, and `require_covers()` correctly rejected `Bud0a` as
under-powered** — the F.84 fix works against the real defect, not only in a unit test.
**R-G5 passed: 57/57 cities have a satellite level.**

### The decomposed bottom rung

| rung | median RMSE | step |
|---|---:|---|
| `Bud0a` drivers only | 21.944 | — |
| `Bud0b` + static geography | 20.312 | **10.81%** |
| `Bud0c` + satellite level | 19.987 | **7.62%** |

### The ground rungs, from each bottom

| bottom | →`Bud1` | →`Bud2` | →`Bud3` |
|---|---:|---:|---:|
| `Bud0a` (the old, under-powered rung) | **25.57%** | 0.26% | 43.34% |
| `Bud0b` | 17.32% | 0.12% | 39.04% |
| **`Bud0c`** (spec-compliant) | **17.85%** | **0.10%** | **40.56%** |

### 🔴 Registered priors: three held, five refuted

| prior | predicted | actual | |
|---|---|---:|---|
| geography step | 5–15% | **10.81%** | ✅ held |
| **satellite step** | **25–45%, the largest step below the ground rungs** | **7.62%** | ❌ **badly refuted** |
| `Bud0c→Bud1` | 5–15% | **17.85%** | ❌ refuted (it *is* below 24%, but not by what I claimed) |
| `Bud1→Bud2` | ~0% | 0.10% | ✅ held |
| `Bud2→Bud3` | 15–30% | **40.56%** | ❌ **refuted — essentially unchanged** |
| **overall: the ladder flattens** | flattens | **modest only** | ❌ largely refuted |
| coastal (a): `Bud0a` worse at coastal | worse | **better**, 19.55 vs 26.56 | ❌ refuted |
| **coastal (b): satellite helps coastal more** | larger | **24.38% vs 6.18% — 4×** | ✅✅ **strongly held** |

### What this means

🟡 **The old headline was inflated, but only moderately, and the qualitative story survives.**
`Bud0→Bud1` falls from **25.6% to 17.9%** — a real ~30% relative correction that had to be made —
while `Bud2→Bud3` is essentially unchanged (43.3 → 40.6). **The background rung remains the
largest step in the programme**, in-city stations beyond the first two still buy nothing, and the
first two stations still buy a great deal. F.84 was a genuine defect and it did **not** overturn
the finding.

🔴 **The satellite level is worth far less than I predicted, and that is the interesting result.**
7.6%, against a registered 25–45%. ⚠ **Post-hoc explanation, flagged as such:** GHAP supplies an
**annual** level while the target is a **daily** city mean, and daily RMSE is dominated by
day-to-day variance that an annual constant cannot touch. If so, a *daily* satellite product
would be a different test — and that is a hypothesis for a future registration, not a rescue of
this one.

🟢 **Static geography (10.8%) beats the satellite level (7.6%).** Population, built volume and
night lights carry more usable information about a city's daily PM2.5 than an annual satellite
level does. Unexpected, and directly useful for the network-design framing.

### 🟢 The coastal test: half the F.78 diagnosis confirmed, half refuted

| | n | `Bud0a` RMSE | `Bud0c` RMSE | gain |
|---|---:|---:|---:|---:|
| inland | 27 | 26.56 | 26.14 | **6.18%** |
| **coastal (<50 km)** | **21** | **19.55** | **12.91** | **24.38%** |

**Satellite level helps coastal cities four times as much as inland ones.** That is the registered
prediction (b), confirmed at n=21 vs 27 — and it supports the F.78 reading that the failure mode
is *a tier with no information about the place beyond its weather*, since coastal cities are
exactly where meteorology least predicts concentration.

⚠ **Prediction (a) is refuted:** coastal cities are *easier* at `Bud0a` (19.55 vs 26.56), not
harder. So coastal cities are not intrinsically hard — they are **intrinsically mis-levelled** by
a meteorology-only tier, and a level anchor fixes it.

⚠ **Checked before reporting:** coastal is **not** confounded with instrument class (Fisher exact
**p = 0.382**; the matching n=21 in both strata was coincidence — the sets share only 11 cities).
It **is** partially associated with band (9 of 13 deep-tropical cities are coastal), so the
coastal claim must be reported alongside the band stratification, never instead of it.

### R-G2 monotonicity, on every rung that exists (F.79 convention)

`Bud0a` 47/48 · `Bud0b` **45/48** · **`Bud0c` 48/48**. The spec-compliant bottom rung is the only
one that is perfectly monotone — a small point in favour of the corrected design, and the three
`Bud0b` violations should be named if that rung is reported.

### Consequence

**The suspension of F.50–F.53 is lifted with corrected numbers**: quote **17.9% / 0.1% / 40.6%**
from `Bud0c`, never the old 24%/0%/38–40%. Colombo (F.78) must still be re-run against `Bud0c`
before its conclusion is restated.

## F.86 — 🟢 COLOMBO RE-RUN: the F.78 diagnosis was RIGHT, the level failure vanishes, and the residual failure is now precisely located (2026-08-23)

Pre-registered gates R-G6, https://osf.io/g6hqb/. Re-run against the spec-compliant `Bud0c`.
`data/processed/modular/colombo_zeroshot_bud0c.csv`.

| gate | F.78 (`Bud0a`) | **now (`Bud0c`)** | criterion | |
|---|---:|---:|---|---|
| C-G1 daily RMSE | 17.68 | **10.10** | in [13.43, 45.54] | ⚠ outside, **on the favourable side** |
| C-G2 seasonal r | 0.550 | **0.950** | ≥ 0.60 | ✅ **PASS** |
| C-G3 level bias | **+31.3%** | **−1.8%** | ≤ 40% | ✅ **PASS** |
| C-G4 R² vs climatology | −4.069 | **−0.655** | > 0 | ❌ **FAIL** |
| plain R² | −0.896 | **+0.381** | — | — |

Observed mean 20.54; modelled **20.16**.

### 🟢 The diagnosis in F.78 was correct

F.78 attributed the Colombo failure to *a tier carrying no information about the place beyond its
weather*. Giving it a satellite level anchor **fixes almost exactly what that predicted**: level
bias collapses from **+31.3% to −1.8%**, seasonal correlation rises from **0.550 to 0.950**, and
plain R² goes from **−0.896 to +0.381**. The registered prior "bias falls below 15%" **holds**.

This also confirms, from the target's own regime, the panel finding that a satellite level is
worth four times more at coastal cities (F.85).

### 🔴 But C-G4 still fails, and the failure is now precisely located

R² against day-of-year climatology remains negative (**−0.655**), so the registered prior "turns
positive" is **refuted**. The precise statement is now available and is much more useful than
F.78's blunt one:

> At Colombo the model reproduces the **annual level** (−1.8%) and the **seasonal cycle**
> (r = 0.95) well, and adds **no day-to-day skill beyond the seasonal climatology**. Daily
> variation there is driven by sea-breeze onset, which the seven meteorological drivers do not
> resolve.

Failing to beat a day-of-year climatology while matching level and season is a *specific*
deficiency, not a general failure to transfer.

### ⚠ C-G1 "fails" by being too good — the gate was mis-specified

RMSE 10.10 falls **below** the band's lower bound of 13.43. The registered interpretation of a
C-G1 failure was "Colombo is an outlier against the panel, so the generality claim narrows"; that
reading **does not apply** when the model is better than the panel's 10th percentile. The concern
was one-sided and the gate was written two-sided. **Reported as a technical failure with the
registered interpretation explicitly withdrawn** — not reinterpreted as a pass.

### 🔴 DEVIATION FROM THE REGISTRATION, declared

**Colombo has no entry in `lur_predictors.csv`**, so its `STATIC_GEO` block was filled with the
**panel median**. Colombo's `Bud0c` therefore carries real drivers and a real satellite level but
**substituted geography** — it sits between `Bud0b` and `Bud0c`, not at `Bud0c`.

⚠ This is uncomfortably close to the very defect F.84 is about, and it matters: static geography
was worth **10.8%** on the panel. The registration did not anticipate that an out-of-panel city
would lack the predictor set.

**Consequence:** this is a **partial** `Bud0c` test. The level and seasonal results are unlikely
to be affected — they are driven by the satellite anchor — but C-G4 might be. **Pulling Colombo's
real LUR predictors and re-running is the honest follow-up**, and until then C-G4's failure should
be stated as *provisional*.

### Net

F.78's headline — "the sensorless tier fails at Colombo" — **must be retracted as stated**. What
survives is narrower and better evidenced: a **meteorology-only** tier fails badly out of regime;
adding a globally available satellite level repairs the level and the seasonal cycle almost
completely; and what remains unrecovered is **day-to-day variation at a coastal site**, provisional
on the geography substitution above.

## F.87 — 🟢 The F.86 deviation is closed: Colombo's real geography changes nothing, so C-G4's failure is confirmed (2026-08-23)

F.86 declared a deviation — Colombo has no entry in `lur_predictors.csv`, so its `STATIC_GEO`
block was filled with the panel median, making it a *partial* `Bud0c` test and C-G4's failure
**provisional**. Colombo's real predictors have now been pulled with the **same `gee_city()` and
`osm_city()` functions that built the panel's**, at the US Embassy monitor (6.909 N, 79.875 E).
All 67 columns returned; none missing. `data/processed/modular/lur_predictors_colombo.csv`.

### The substitution was materially wrong — and it made no difference

Colombo's real geography differs from the panel median on every predictor that matters:

| predictor | Colombo | panel median |
|---|---:|---:|
| `ndvi_1000` | **0.462** | 0.334 |
| `ntl_1000` (night lights) | **18.5** | 29.1 |
| `built_1000` | **42,419** | 31,908 |
| `road_major_300` | **1.789** | 0.000 |
| `dist_major_km` | **0.170** | 0.354 |

The Embassy site is greener, darker, more built, and sits **170 m from a major road** against a
panel median of 354 m. So the median substitution was not a harmless stand-in.

### The result is unchanged

| gate | median geo (F.86) | **real geo** | criterion | |
|---|---:|---:|---|---|
| C-G1 RMSE | 10.10 | **10.23** | in [13.43, 45.54] | ⚠ outside, favourable side |
| C-G2 seasonal r | 0.950 | **0.931** | ≥ 0.60 | ✅ PASS |
| C-G3 level bias | −1.8% | **−4.4%** | ≤ 40% | ✅ PASS |
| **C-G4 R² vs climatology** | −0.655 | **−0.699** | > 0 | ❌ **FAIL** |
| plain R² | 0.381 | **0.365** | — | — |

Every metric moves by a trivial amount. **C-G4's failure is confirmed and no longer provisional.**

### What this settles

**The residual deficiency at Colombo is real**: with a correct, spec-compliant `Bud0c` carrying
real drivers, real satellite level and real geography, the model reproduces the **annual level**
(−4.4%) and the **seasonal cycle** (r = 0.93) but adds **no day-to-day skill beyond a day-of-year
climatology**. That is a specific, located deficiency — sea-breeze-driven daily variation the
seven meteorological drivers cannot resolve — and it is not an artefact of any substitution.

It also mildly reinforces F.85's surprise that static geography is worth less than expected for a
*city-mean daily* target: swapping a whole geography block for another changed daily RMSE by
**0.13 µg/m³**.

⚠ **Minor inconsistency, recorded:** the GHAP satellite level was sampled at 6.9271 N, 79.8612 E
(city centroid) while the LUR predictors were sampled at the Embassy monitor 6.909 N, 79.875 E —
about 2 km apart. Immaterial for an annual level averaged over a 5 km buffer, but the two should
be reconciled to a single coordinate if this is repeated.

## F.88 — 🔴 F.81 IS REFUTED at `Bud0c`: the linear model collapses, and the first rung is NOT estimator-independent (2026-08-23)

F.81 concluded that the budget ladder is *"a property of the INFORMATION, not the estimator"*
because four learners — including plain Ridge regression — gave step gains within 1.8 pp. I
described that as one of the most durable claims in the programme. **It was measured on the
pre-F.84 `Bud0` (7 meteorological features) and it does not survive the correction.**

`scripts/learner_sensitivity_bud0c.py`, re-run against the spec-compliant `Bud0c` (68 features).

| learner | `Bud0c` RMSE | `Bud0c→Bud1` | `Bud1→Bud2` | `Bud2→Bud3` |
|---|---:|---:|---:|---:|
| HistGBM (shipped) | **18.91** | **11.7%** | 0.3% | 40.8% |
| HistGBM shallow | 19.76 | 14.2% | 0.3% | 40.3% |
| RandomForest | 19.92 | 14.0% | 0.6% | 43.4% |
| 🔴 **Ridge (linear)** | 🔴 **35.01** | 🔴 **50.2%** | 0.1% | 38.8% |
| **spread** | **16.09** | **38.5 pp** | **0.46 pp** | **4.60 pp** |

*F.81 on the old `Bud0` gave spreads of 1.8 / 0.1 / 3.3 pp.*

### Why it breaks, and why that is the interesting part

Ridge kept up on **seven meteorological drivers**. On **68 features** — including population,
built volume, night lights, road density and a satellite level — a linear model cannot exploit
the information, so its `Bud0c` is nearly **twice as bad** (35.0 vs 18.9). The first two stations
then appear to "buy" **50%** rather than **12%**, because they are correcting a badly wrong
baseline rather than adding to a good one.

🟢 **The corrected claim is more useful than the one it replaces:**

> **The measured value of a monitor depends on how well you can exploit the data you already have
> for free.** A model unable to use satellite and geography makes monitors look four times more
> valuable than they are. Value of information is not a property of the information alone — it is
> a property of the information *and the estimator's capacity to use it*.

For a network-design audience that is a sharper and more actionable message than
estimator-independence would have been: *before buying a monitor, check whether your model is
already leaving free information on the table.*

### What survives

- **Among learners that can represent non-linearity** — the two GBMs and the random forest —
  the ladder is robust: 11.7 / 14.2 / 14.0%, a spread of **2.5 pp**. The claim is therefore
  *"robust across non-linear estimators"*, **not** *"even a linear model reproduces it"*.
- 🟢 **`Bud1→Bud2` ≈ 0 holds under every learner including Ridge** (0.1–0.6%, spread **0.46 pp**).
  This is now the most estimator-robust result in the ladder.
- 🟢 **`Bud2→Bud3` is robust** at 38.8–43.4%, spread 4.6 pp.

### ⚠ Two things to state whenever these numbers are used

1. **This run uses complete cases** (Ridge cannot take NaN), so it scores **46 cities**, while
   F.85's ladder scores 48 with a NaN-tolerant learner. HistGBM's `Bud0c→Bud1` is therefore
   **11.7%** here against **17.9%** there. The **cross-learner comparison within this run is
   valid**; the two runs' absolute gains are not directly comparable and must not be mixed.
2. The RandomForest was **deliberately capped** (100 trees, `n_jobs=2`, depth 14) after
   `n_jobs=-1` was killed for memory on 68 features × 46 LOCO fits. A larger forest might close
   a little of its gap to HistGBM; it would not change the Ridge conclusion.

**F.81's banner is upgraded from "should be re-run" to "re-run and refuted at `Bud0c`".**

## F.89 — 🔴 S1 REFUTED: the sub-grid field exists, carries contrast, and still does not place it (2026-09-01)

**Registered at https://osf.io/bkpyr/ before running.** Script `scripts/s1_subgrid_placement.py`;
product `data/processed/modular/s1_subgrid_placement.csv`.

**What opened it.** `S_traffic_kandy.npz` ships `E_fine` at 160×160 (**94 m**) beside the 16×16
(**998 m**) surface the shipped product reports on. At the paired botanical-garden microsites the
shipped field gives **1.000×** and raw `E_fine` gives **2.25×**, correctly signed, against
**27.5×** observed. The model therefore contains sub-grid structure it discards, and the
question was whether that structure survives physics.

**It does not place the contrast.** A pure forward run of the calibrated terrain solver at 94 m,
forced with the transect's own 11–13 LT climatology (u +0.62, v −0.27 m/s, BLH 1015 m), nothing
fitted:

| | observed | production 238 m | **fine 94 m** |
|---|---:|---:|---:|
| botanical garden pair | **27.5×** | 1.165× | **1.135×** |
| transect rank ρ (n=12) | — | +0.385 | **+0.383** |

**Registered outcomes: S1a REFUTED, S1b HELD, S1c REFUTED, S1d HELD.** Going from 238 m to 94 m
changes the paired ratio from 1.165 to 1.135 and the rank correlation from +0.385 to +0.383 —
i.e. **nothing**. This is the strongest available form of the ceiling claim and, per the
registration, **the question is now closed**: the model cannot place within-city contrast even at
94 m with its own high-contrast emission field.

🟢 **But the contrast is not lost to resolution — that premise is refuted too.** The field-wide
budget, p90/p10 over positive cells:

| stage | p90/p10 | lost |
|---|---:|---:|
| raw `E_fine`, 94 m | 63.85× | — |
| + `log1p` tempering | 47.61× | ×1.34 |
| + dispersion at 94 m | 35.70× | ×1.33 |
| + solve at 238 m | 26.01× | ×1.37 |
| + report at 998 m | 18.70× | ×1.91 |

The dispersed field still spans **18.7× at the shipped 998 m resolution**. So there is plenty of
contrast; it is simply **in different places than the transect measured**. The limitation is one
of *placement*, not of *dynamic range* or of *support* — which sharpens, and partly corrects, the
change-of-support framing of F.68/F.70/F.76.

⚠ **Why the shipped field nonetheless spans only 1.23×.** `A_transport` is the unscored scenario
layer; the **headline** `P_local` uses `S_emit` (VanD satellite, p90/p10 **1.11**), not the
traffic surface (22.7×). The shipped field's flatness is a consequence of **which surface was
chosen for the headline**, not of resolution. F.77 already bracketed observation between the two;
S1 shows the high-contrast option would not have helped, because its contrast is misplaced.

🔴 **A data defect found in passing, and it weakens a published-facing claim.** The
"school junction vs its grounds" pair — reported in F.69 as 4.6× observed against 1.000×
modelled — **has a single coordinate for both sites** (7.2870, 80.6262). The model returns
1.000× because it is being asked about *the same point twice*. That pair is **not a spatial
test** and must be withdrawn; only the botanical-garden pair (7.2682/80.5974 vs 7.2707/80.5963,
~304 m apart) is genuine. The paper's money figure survives on one pair, not two.

## F.90 — 🔴 R2 REFUTED: `A_transport`, scored at last, does not improve spatial rank — it costs it (2026-09-01)

**Registered at https://osf.io/bkpyr/ before running.** Script `scripts/r2_score_atransport.py`;
product `data/processed/modular/r2_atransport.csv`.

`A_transport` has shipped as an unscored "scenario" since 2026-06-02 and was the most attackable
thing in the paper. The registration allowed two outcomes: score it, or state in the abstract
that the headline field excludes it. It is now scored.

**The counterfactual.** The layer's entire job is to redistribute an emission surface through
terrain-steered advection and dispersion, so the honest control is that same surface,
undispersed. Both scored identically against the same held-out stations, nothing fitted, the
solver's cross-city calibrated parameters, stable-calm regime.

| | median across the panel |
|---|---:|
| `rho_S` — raw emission surface | **+0.371** |
| `rho_C` — after the terrain solver (`A_transport`) | **+0.274** |
| delta | **−0.026** |

**Improves rank in 3 of 10 cities; Wilcoxon on the paired deltas p = 0.496.** So the layer is not
significantly harmful either — it is simply **not doing the job it is in the model to do**.

**R2a REFUTED · R2b HELD.** Per the registration this resolves the item: **the abstract must
state that the headline field excludes `A_transport`**, and now with evidence rather than as a
hedge.

🟢 **And it agrees with F.89 from the opposite direction.** S1 found the dispersed field's
contrast is real but *misplaced*; R2 measures what that misplacement costs — dispersing the
emission surface moves the panel median rank **down** from +0.371 to +0.274. Two independent
lines, one conclusion: **the dispersion step relocates contrast to the wrong places.**

⚠ **A consequence for the spatial-ceiling framing.** The *undispersed emission surface* scores
**+0.371**, which is **above** the 0.2–0.28 ceiling quoted throughout. The ceiling was measured
on model fields that had already been through this machinery. The honest statement is that the
ceiling applies to the *shipped construction*, not to every possible use of the emission proxy.

⚠ **Scope, stated plainly.** This tests the layer's SPATIAL contribution under the stable-calm
regime it was calibrated for. It does not test the diurnal timing factor `e(t)` and cannot —
panel scoring is on station means. Chandigarh flips sign (+0.486 → −0.486) at n=6; gotcha #69
already warns that Chandigarh's n is too small to carry a conclusion, and it is not driving the
median.

## F.91 — 🟢 S2: a within-pixel distribution exists, is gauge-exact, and says most spatial variation is SUB-GRID (2026-09-01)

**Registered at https://osf.io/bkpyr/ before running.** Script
`scripts/s2_within_pixel_distribution.py`; product `data/processed/modular/s2_within_pixel.csv`.

**Why it is the right product.** F.89 killed the pointwise version: at 94 m the model still
cannot say *which* corner of a cell is dirty. A distribution does not need placement — *"this
cell spans roughly this range"* is defensible where *"it is worse at your corner"* is not.

**Construction.** The model is additive and `B` is spatially uniform, so only the increment may
be structured: `PM_fine = B(t) + increment_cell(t) · w_fine`, with `mean(w) = 1` inside every
cell. That is the specification's own gauge argument (C1/C4) applied one level down, and it
makes the cell mean exactly preserved.

| | value |
|---|---:|
| between-pixel p90/p10, midday 2023 | **1.049×** |
| **within-pixel p90/p10, median cell** | **1.218×** |
| within-pixel p90/p10, 90th-percentile cell | 2.075× |
| max cell-mean drift | **7.11e-15** µg/m³ (gate 0.05) |

🟢 **S2a HELD, and it is the finding.** The spread *inside* a typical pixel (1.218×) is larger
than the spread *between* pixels (1.049×). By the model's own structure, **most of Kandy's
midday spatial variation is sub-grid** — which is what F.68/F.89 imply and what no shipped
product has ever expressed.

🟢 **S2c HELD exactly** (7.11e-15). P1 survives the extra level; the distribution is a
decomposition, not a re-level.

🔴 **S2b HELD but the test is near-degenerate, and it must not be quoted as validation.**
Predicted within-cell spread is ~1.2× while the observed sites span 85×, so every high site
saturates at quantile 1.00 and every low site at 0.00. The scored contrast (kerbside 0.88 vs
quiet 0.00) therefore **re-detects the known amplitude gap rather than testing within-cell
ordering**. The single non-saturated case runs the *other* way: Botanical Gardens entrance,
observed 110, sits at quantile **0.17** of its own cell. **Report S2b as uninformative.**

⚠ Two scope notes. The 1.049× between-pixel figure is **midday-only** and must not be confused
with the **1.232×** annual figure quoted elsewhere; midday is ventilated and therefore flatter.
And per-site values exist only for Elangasinghe — Wickramasinghe (4.0×) and Premasiri (3.0×)
are published spreads only, so the support-ordering half of S2b could not be tested at all.

## F.92 — 🔴 R1: the standing acquisition advice is a POOLED number, and Kandy's own band inverts it (2026-09-01)

Script `scripts/r1_network_design.py`; product `data/processed/modular/r1_network_design.csv`.
No new modelling — this is the ladder turned into the question a ministry actually asks.

**The programme's standing advice** has been *chase the regional background first*: the
`Bud2→Bud3` rung is the largest measured gain anywhere in the study (**40.6%** pooled) against
**17.8%** for the first two in-city stations. That advice is written into `CLAUDE.md` §3 and into
the improvement plan.

**Stratified, it inverts in Kandy's own band:**

| stratum | n | +2 stations | +6 more | +background |
|---|---:|---:|---:|---:|
| POOLED | 48 | 17.8% | 0.1% | **40.6%** |
| **deep_tropical (Kandy)** | 13 | **21.9%** | 0.9% | **8.5%** |
| tropical | 10 | 6.7% | 0.1% | 39.8% |
| subtropical | 7 | 29.7% | 0.3% | 36.0% |
| temperate | 7 | 33.5% | 1.1% | 31.6% |

**In the deep tropics the first two local stations are worth 2.6× the regional background rung**,
and the pooled row that says otherwise is computed mostly from bands Kandy is not in. Recommending
NBRO to Kandy on the strength of the pooled number is the same error this programme keeps
making — a quantity attributed to the wrong stratum (F.84, C2, C7, C1).

**At Kandy's level (21 µg/m³):** 2 local stations ≈ **4.6 µg/m³** of RMSE · a regional background
station ≈ **1.8** · stations 3–8 ≈ **0.2**.

🔴 **PROVISIONAL, and the caveat is load-bearing.** The recorded explanation for the deep-tropical
background collapse (28.1% → 8.5%) is that *the satellite level substitutes for a background
station there*. C1 established that the satellite stream is **GHAP — a fused product trained on
this panel's own OpenAQ and CNEMC monitors**. If a contaminated satellite stream is standing in
for a background station, the substitution is **leakage, not physics**, and the background rung is
undervalued in this band. **This recommendation must be re-derived once C1 re-runs with raw MAIAC
AOD.** Recorded before the re-run, not after.

⚠ n = 13 for the deep-tropical cell; subtropical and temperate are n = 7.
🟢 "Stations 3–8 buy nothing" is unaffected — robust across every learner tested (F.88, spread
0.46 pp) and the single most estimator-stable result in the ladder.

**Instrument class, if stations are added:** median `w_Bud2` LCS **0.575** vs reference **0.350** —
low-cost units gain more from extra devices because per-device error averages down, while a
reference monitor's third-to-eighth unit still buys close to nothing.

## F.93 — 🟢 THE DECOMPOSITION GETS ITS FIRST CHEMICAL CORROBORATION — and one prediction fails usefully (2026-09-01)

**Registered at https://osf.io/kx23c/ before running.** Script `scripts/chemistry_origin_test.py`;
product `data/processed/modular/chemistry_origin_test.csv`. 1,826 days of GEOS-CF speciation
against 11,676 back-trajectory arrivals; sector is derived from trajectory geometry, **not** from
GEOS-CF chemistry, which is what makes the test admissible (the obvious test — `B(t)` against the
secondary fraction — is circular, because `B`'s shape is itself `geoscf_daily_shape`).

**Secondary fraction by air-mass origin, and the ordering is clean:**

| sector | n | median `sec_frac` | 95% CI | OC/BC |
|---|---:|---:|---|---:|
| SW_marine | 546 | **0.324** | [0.316, 0.329] | 14.2 |
| other | 380 | 0.340 | [0.334, 0.344] | 14.2 |
| local_recirc | 82 | 0.387 | [0.375, 0.405] | 14.1 |
| BoB_marine | 719 | 0.395 | [0.390, 0.400] | 13.7 |
| Penin_India | 84 | 0.405 | [0.387, 0.427] | 13.8 |
| IGP_E_India | 15 | **0.447** | [0.412, 0.512] | 12.4 |

🟢 **C-H1 HELD, strongly.** Continental-Indian air is more secondary-rich than marine:
**0.410 vs 0.365**, Mann–Whitney **p = 3.1e-09**, and it survives the pre-declared sensitivity to
days where all four arrivals agree (0.426 vs 0.365, p = 4e-08, n = 40 vs 995).

**This is the first chemical support the decomposition has ever had.** Air the trajectories call
transported is measurably aged; air they call marine is not. The claim that `B` represents
transported aerosol is no longer statistics-only.

🔴 **C-H2 REFUTED, and this is the finding.** `local_recirc` is **not** the freshest sector
(0.387); **SW_marine is** (0.324). Recirculated local air is *more* secondary-rich than clean
monsoon air. Two mechanisms, both physical: SW monsoon air is wet, and sulphate and nitrate are
hygroscopic and efficiently scavenged; and **stagnation gives local precursors time to age in
place**. So *"local increment = fresh primary"* is too simple — under stagnation the local
increment itself acquires secondary mass. The decomposition still partitions correctly by
*origin*, but its chemical story needs this qualification.

⚠ **C-H3 HELD only nominally and must be reported as uninformative.** The continental–marine gap
is **+0.021** in DJF–MAM against **+0.019** in JJA. The registered criterion was "larger", and
0.021 > 0.019 satisfies it arithmetically while being indistinguishable from noise. **There is no
seasonal modulation of the gap worth claiming.**

🟢 **C-H4 HELD decisively.** OC/BC exceeds 5 in **every month**, minimum monthly median **13.2**,
against ~1–2 for traffic-dominated aerosol. A biomass-burning signature year-round — the **third**
independent line refuting "Kandy ~90% vehicular", after the Katugastota PMF (F.66) and the
PM2.5–NO₂ decoupling.

⚠ **"Marine" is not homogeneous** and the pooling in C-H1 is cruder than it looks: SW_marine
(0.324, Indian Ocean) against BoB_marine (0.395, Bay of Bengal, downwind of India). The Bay of
Bengal sector sits *above* local recirculation. Future work should split them.

⚠ **Scope.** GEOS-CF is a model at ~25 km: this corroborates or contradicts, it cannot validate.
It tests the **temporal** origin claim, not the spatial one. `IGP_E_India` is n = 15.

## F.94 — ⚫ R3 BLOCKED on data availability, and the attempt settles how to position the competitor (2026-09-01)

**Registered at https://osf.io/bkpyr/ §5.** R3 proposed benchmarking the Kandy field against
EGU26-9786 (Aunan, Amarakoon, Jayawardena et al., CICERO / Oslo), *"the first high-resolution
(1 × 1 km, daily) PM2.5 dataset for Sri Lanka"* — a free external check on the **level** axis,
which is where W11 is open.

**It cannot be run.** The conference abstract carries **no DOI, no repository and no download
link**, and no peer-reviewed version exists yet. Routes tried: the Copernicus abstract itself, a
search for a published or preprint version, and a check for any dataset landing page. The only
remaining route is **contacting the authors**, which is the user's action, not mine.

🟢 **But the abstract answers the question R3's own caveat raised.** The dataset is built by
*"combining in-situ measurements, satellite retrievals, and reanalysis products using a hybrid
modeling framework"* — i.e. **the same class of monitor-trained fusion as GHAP** (C1). The
pre-registration said in advance: *"agreement is not validation — if it is also a monitor-trained
fusion it shares GHAP's contamination and much of our driver set, so agreement partly measures
shared inputs."* That caveat is now **confirmed as applicable rather than hypothetical**, and it
was recorded before any comparison, so a favourable result could not have been over-read.

**Consequence for positioning, which is the useful outcome.** The competitor is a *fused product*;
this work is a *tier-declared decomposition*. They answer different questions — theirs is "what
was the concentration", ours is "what information would you need to trust an answer". The paper
should cite EGU26-9786 as the state of the art for a Sri Lankan field and distinguish on
**method and claim**, not compete on accuracy against a dataset we cannot obtain.

⚠ Their reported finding that **relative humidity is a key confounder and precipitation modifies
the PM2.5–hospitalisation relationship** is independently interesting: it is consistent with the
scavenging signal found here today (PM2.5 *rises* as it gets drier at both FECT sensors), from a
different dataset and a different endpoint.

## F.95 — 🟢 C1 RESOLVED: an honest satellite stream is worth as much as the fused one, and "geography beats satellite" survives (2026-09-01)

**Registered at https://osf.io/bkpyr/ §1 before running.** Script
`scripts/c1_satellite_stream_ladder.py`; product `data/processed/modular/c1_satellite_ladder.csv`.
⚠ The first execution was **invalid and discarded** — the MAIAC stream had been pulled for
2019–2022 against a frame that is 86% post-2023, so the rung was fitted on an all-NaN column
(gotcha #85). Re-pulled 2019–2026; post-merge coverage median **49.5%**, and
`require_stream_coverage` now asserts it before the fit.

Three rungs, identical frame (47 stream-complete cities), learner, seed and LOCO folds:

| rung | median RMSE | step from `Bud0b` |
|---|---:|---:|
| `Bud0b` drivers + geography | **19.35** | — |
| `Bud0c-raw` + MAIAC AOD | **19.37** | **+5.97%** |
| `Bud0c-fused` + GHAP level | **20.94** | **+5.37%** |

**P1 HELD · P2 HELD · P3 REFUTED · P4 REFUTED · P5 HELD.**

🟢 **P3's refutation is the finding, and it is good news.** I registered that the fused product
would show a measurable **excess** over raw AOD — the signature of the extra drivers and the
indirect monitor leakage it carries. **It does not. Raw MAIAC AOD is marginally BETTER
(+5.97% vs +5.37%, an excess of −0.61 pp.)** So the value GHAP appeared to add at a monitored
city is **not** recycled information showing up as skill; it is simply satellite information that
raw AOD supplies just as well.

**The consequence is that C1's methodological problem has a free fix.** The circularity objection
was real — GHAP trains on this panel's own OpenAQ and CNEMC monitors — but it costs nothing to
avoid. **Switch `SATELLITE_LEVEL` to raw MAIAC AOD**: admissible, no leakage, no shared drivers,
and it performs at least as well. The paper can state its satellite stream is an actual
radiometric observation without giving anything up.

🟢 **P5 HELD — the headline survives an honest stream.** Static geography (10.8%) still beats the
satellite level (5.97%). That claim was in doubt precisely because the 7.6% was a mixture; it is
now measured against a clean stream and stands.

⚠ **P4 refuted, exactly as flagged in advance.** No association between the fused excess and
station count (rho = −0.089, p = 0.551, n = 47). Per the registration this means the leakage is
reported as **an argued methodological risk, not a measured effect** — and P3 now shows it does
not manifest as skill either way.

⚠ **Two metrics disagree in direction and both are reported (gotcha #74).** `Bud0c-fused` has a
**higher median RMSE** (20.94 vs 19.35) while showing a **positive median per-city gain**
(+5.37%). Most cities improve slightly, but the fused stream evidently hurts some badly enough to
move the median value. That is a further mark against GHAP and should be looked at before it is
ever reinstated.

⚠ **11 of 47 cities carry AOD on fewer than 30% of days** — genuine cloud, not a broken merge.
That an honest satellite stream is *unavailable half the time in the tropics* is a real limit on
sensorless methods, and it rhymes with F.53: the regime that most needs them is the regime where
the inputs are thinnest.

## F.96 — 🔴🟢 F.92 RE-DERIVED ON THE HONEST STREAM: the inversion is not just confirmed, it DOUBLES — and the leakage was hiding somewhere else entirely (2026-09-01)

Script `scripts/ladder_maiac.py`; products `ladder_maiac.csv`, `ladder_maiac_comparison.csv`.
`ladder_revalidated.csv` is **not** overwritten — it is what F.85 and OSF `g6hqb` rest on, and
the C1 registration called for the ladder to be reported both ways.

F.95 fixed the bottom rung; every rung **above** it was still computed on GHAP, so F.92's
acquisition recommendation was still resting on a monitor-trained stream. Re-run end to end with
raw MAIAC AOD, identical learner, seed and folds:

| stream | n | +2 stations | +6 more | +background |
|---|---:|---:|---:|---:|
| GHAP (fused) | 48 | 17.8% | 0.1% | **40.6%** |
| **MAIAC (raw)** | 47 | **23.6%** | 0.1% | 37.1% |

**Deep tropics — Kandy's own band:**

| stream | n | +2 stations | +background | verdict |
|---|---:|---:|---:|---|
| GHAP (fused) | 13 | 21.9% | 8.5% | local wins 2.6× |
| **MAIAC (raw)** | 13 | **43.7%** | **10.3%** | **local wins 4.2×** |

🟢 **F.92's inversion survives and roughly doubles.** On an honest satellite stream the first two
local stations buy **43.7%** in Kandy's band against **10.3%** for a regional background. The
provisional caveat is discharged: **CEA outranks NBRO for Kandy, and by more than we thought.**

🔴 **AND THIS IS WHERE THE LEAKAGE WAS.** C1's P4 looked for GHAP's contamination as an *excess
in the satellite's own skill* and found none (rho = −0.089, p = 0.551), so F.95 reported the
leakage as an argued risk rather than a measured effect. **P4 was looking in the wrong place.**
The contamination does not inflate the satellite rung — it **deflates the rung above it**.
A monitor-trained product at a monitored city already encodes part of what that city's own
monitor would tell you, so adding the monitor appears to buy less: **17.8% against 23.6% pooled,
and 21.9% against 43.7% in the deep tropics.** GHAP was suppressing the measured value of a
local station by roughly **half** in the band that matters most.

**The general lesson, which is the publishable one.** A fused product used as a covariate does
not flatter itself — it flatters the *baseline*, and so **understates the value of the
observations it was trained on**. Any value-of-information study that prices monitors against a
monitor-trained product will under-price them. That is a methodological result about a practice
the whole field engages in, and it was invisible until the ladder was re-run on a stream with
clean provenance.

⚠ n = 47 rather than 48 (one city lacks usable AOD); the two ladders are otherwise identical in
learner, seed, folds and frame construction. ⚠ MAIAC is daily where GHAP was an annual scalar, so
provenance and temporal resolution both differ — the comparison is "honest stream vs fused
stream" as registered, not a controlled test of provenance alone.
