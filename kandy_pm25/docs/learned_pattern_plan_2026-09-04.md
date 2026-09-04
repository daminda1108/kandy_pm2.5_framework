# A gauge-constrained learned spatial pattern — plan

**Status:** proposed 2026-09-04. Paper 2. Not part of the model paper, whose §5 argues the
spatial rung is a *declared design assumption*; this is the work that tests that assumption.

---

## 1. The question, stated so it can fail

Can a pattern learned from a multi-city panel place PM2.5 within a city better than the imposed
pattern the current model uses — **without breaking the conservation property that makes the
budget ladder measurable**?

Two things make this worth doing despite five prior nulls.

**There is measured headroom, and it is in an unexpected place.** The raw emission surface ranks
neighbourhoods at ρ = **0.371**. Passing it through the calibrated dispersion solver *lowers*
that to **0.274**, improving only 3 of 10 cities. The current construction destroys spatial
skill it already had. The benchmark to beat is therefore **0.371, not 0.274** — and framing it
against 0.274, as the "ρ ≈ 0.2–0.28 ceiling" language does, understates the target by a third.

**The five nulls had no power to see a moderate effect.** F.92's power analysis puts the minimum
detectable partial correlation at **0.65 to 0.96**. They exclude a large learnable residual and
say nothing about a moderate one.

## 2. What caps it before we start

Stated now so the result is not over-read later.

- **Within-cell spread (1.218) exceeds between-cell spread (1.049).** A pattern at 1 km can only
  ever address the smaller half. No architecture changes this; it is change of support.
- **Two sites 300 m apart inside one cell read 27.5× apart.** Refining the physics tenfold in
  area recovers 1.135×. Resolution is not the binding constraint (registered, refuted, F.89).
- **Station siting is a convenience sample.** Regulatory and low-cost networks are sited for
  compliance and access, not across land-use contrast. Published LUR reaches R² 0.43–0.83
  because those campaigns site deliberately; ours cannot.
- **The reference-dense cities are in the wrong bands.** 6 deep-tropical clusters carry ≥10
  concurrent reference stations against 65 temperate. Anything learned will be learned mostly
  from temperate cities and applied to tropical ones.

**Success is therefore not "a good spatial map". It is "a better-placed increment than the
imposed pattern, measured out of sample, with the gauge intact".**

## 3. Phase 0 — fix the baseline first (mandatory)

🔴 **Without this the experiment tests the wrong thing.** Every city in the panel currently gets
the *same* spatial source proxy: a road-network centrality × emission-factor surface
(`S_traffic_{city}.npz`). The per-city source mix `emix` in `city_config.py` is used **only for
the diurnal timing profile `e(t)`** — time, never space. So Kathmandu declares 50 % brick-kiln
and biomass burning in *time* and receives 100 % roads in *space*; Chiang Mai declares 55 %
burning and receives 100 % roads; Xichang declares 70 % domestic heating and receives 100 %
roads.

A learned P compared against that baseline would be beating a mis-specified proxy, not beating
learning. `src/modular/emission.py` already implements the fix —
`S = norm(Σ w_k · norm(proxy_k))` with the declared `emix` weights, 74 tests, `vehic=1.0`
reproduces the traffic surface bit-exactly — and it is **not wired into production**.

**Phase 0 tasks**
1. Wire `emission.compose()` into the production surface behind a flag; default off until scored.
2. Score the sector-weighted surface against withheld stations on the same frame. This is a
   result either way, and it is cheap.
3. ⚠ Two sectors have no admissible proxy: Kathmandu returns **zero FIRMS detections** (kilns are
   continuous combustion, not open flame) and industry has none anywhere. Kandy has the same
   problem — incense, oil lamps and domestic burning are invisible to FIRMS. Declare the gap;
   do not substitute a placeholder and call it a sector.

**Phase 0 gate:** if the sector-weighted surface alone closes a material part of the gap we
report that and the learned-P work starts from a higher baseline. If it does not, we have
established that the source-mix mis-specification is not what is limiting placement — which is
itself worth knowing before spending a month on a network.

### 🔴 Phase 0 RESULT (run 2026-09-04, `scripts/phase0_sector_surface.py`)

Nine cities attempted, **8 scored**, all arms on the same held-out stations.

| arm | median ρ |
|---|---:|
| night lights | **+0.338** |
| road centrality × emission factor (production) | +0.319 |
| **sector-weighted composite** | +0.098 |
| night lights + terrain solver | +0.189 |
| sector + terrain solver | +0.080 |

**Sector weighting does not help.** Median Δ against the production traffic surface is
**−0.011**, better in 4 of 8 cities, p = 0.64. Against night lights it is −0.097. Excluding the
one city whose burn sector falls back to the placeholder proxy, sector scores +0.110 against
traffic's +0.331.

**But the test is severely underpowered and that is the more important output.** With 8 cities
and a between-city delta standard deviation of 0.250, the smallest improvement detectable at 80
per cent power is **Δρ = 0.35** — larger than the entire rank correlation of most cities in the
frame. This excludes a transformative gain from sector weighting and says nothing about a
moderate one.

🔴 **A methodological error was caught in this run and it invalidated the first version.** The
night-lights surface is built over the *station* footprint while the traffic surface is built
over the narrower *modelling* box, so interpolating the traffic surface at an outside station
returned the fill value of zero — 21 of 33 stations at Chiang Mai, 7 of 24 at Medellín. The
traffic and sector arms were partly scored on padding. All arms are now restricted to stations
inside every proxy's footprint. Same family as gotcha #43.

### Industry — added 2026-09-04 after the first run

The first Phase 0 run tested a **three-sector** composite, and the sector most likely to be
spatially decoupled from roads was the one it did not contain. `emission.py` defines an
`industry` proxy that deliberately raises, no city declares an industry share, and every mix
sums to 1.00 over vehic/heat/burn — so industrial mass is implicitly placed on roads. Yichang is
the measured consequence: the production traffic surface scores **−0.091** there, anti-correlated
with its own stations.

Industrial land use was therefore pulled from OpenStreetMap (`landuse=industrial`,
`landuse=quarry`, `man_made=works`, `power=plant`), rasterised as fractional cell area, and
scored as a **standalone arm** — weight-free, because no city declares an industry share and any
weight would be invented.

| city | traffic | industry |
|---|---:|---:|
| Tai'an | +0.543 | **+0.655** |
| Medellín | +0.331 | **+0.625** |
| Yichang | **−0.091** | **+0.177** |
| Baoji | +0.647 | +0.381 |
| Kathmandu | +0.307 | −0.141 |
| Chiang Mai | −0.685 | −0.296 |

🟢 **Industrial land use is a genuine spatial predictor.** It is the best single proxy at Tai'an
and Medellín, and it rescues Yichang, where the production surface points the wrong way. On the
six cities that have a mapped industrial surface it is better than traffic, night lights *and*
the sector composite in **4 of 6** each.

⚠ **But its median is not better** — +0.279 against traffic's +0.319 and night lights' +0.363 on
those same six. Median and win-count disagree, which at n = 6 means the frame cannot separate
them. Adding industry to the composite lifts it from +0.098 to +0.166 at a 30 % weight (full
sweep reported, not its best), and that composite still loses to both simple proxies.

⚠ Xichang and Bazhou have too few and too small OSM industrial polygons to survive interpolation
onto the model grid. That is a limit of the proxy's resolution and of OSM completeness, **not**
evidence that those cities have no industry.

### What this changes for Phases 1–3

1. **The benchmark for a learned pattern is night lights at ρ ≈ 0.34**, not the production
   traffic surface and not the dispersed field at 0.274. **No engineered source surface tried
   here beats a single free global raster** — not the congestion-weighted centrality surface,
   not a three-sector composite, not a four-sector composite carrying OSM industrial land use.
   That is itself a result worth reporting, and it sets the bar a learned pattern must clear.
2. 🔴 **The frame is too small for the question.** If a paired test across 8 cities cannot see
   anything below Δρ = 0.35, Phase 3 will produce another uninterpretable null on the same
   frame. **Phase 1 must widen the frame before Phase 2 is worth starting** — more cities, or
   many more stations per city, and the power calculation decides which.
3. **Dispersion costs rank again**, −0.124 median and better in only 2 of 8 cities, on a wider
   and differently selected frame than the one where this was first measured. That is now two
   independent frames agreeing, and it strengthens the case that the solver step — not the
   source surface — is where placement is lost.
4. The source-mix mis-specification is **real but is not the binding constraint**, so wiring
   `emission.compose()` into production is a correctness fix with no expected skill gain, and
   should be described that way if it is adopted at all.

## 3b. 🟢 Phase 1 RESULT — the frame, the real benchmark, and the detection limit

Run 2026-09-04, `scripts/phase1_frame_and_power.py`, on the LUR frame: **46 cities, 630
stations**, median 12 stations per city, 60 candidate predictors. Every predictor is globally
available static geography and admissible at `Bud0`; no observation of the target city enters.

### The benchmark is NOT night lights, and it is not 0.34

Phase 0's "night lights at ρ ≈ 0.34" was an eight-city figure and it does not survive the wider
frame. Median per-city rank correlation across 46 cities:

| predictor | median ρ | positive in |
|---|---:|---:|
| **built-up land cover, 2.4 km** | **+0.309** | 35/46 |
| built-up land cover, 1 km | +0.291 | 38/46 |
| population, 2.4 km | +0.252 | 33/46 |
| night lights, 300 m | +0.197 | 30/46 |
| non-residential built volume, 300 m | +0.177 | 31/46 |
| major roads, 500 m | +0.165 | — |
| **NDVI, 300 m** | **−0.270** | 10/46 |

🔴 **The benchmark a learned pattern must beat is +0.309, from built-up land-cover fraction.**
Night lights lands at +0.197 here, materially below what the eight-city frame suggested, so the
figure quoted after Phase 0 was optimistic and is withdrawn.

🟢 **NDVI is the most consistent predictor in the set.** At −0.270 it is nearly as strong as the
best positive proxy and more consistent in sign (36 of 46 negative). Absence of vegetation
discriminates better than any single presence-of-source proxy — which is a statement about how
little source-specific information survives at this support.

### The scale that survives is COARSER than the grid cell

| family | 100 m | 300 m | 1 km | 2.4 km |
|---|---:|---:|---:|---:|
| built-up land cover | +0.240 | +0.216 | +0.291 | **+0.309** |
| population | +0.138 | +0.141 | +0.243 | **+0.252** |
| night lights | +0.181 | **+0.197** | +0.161 | +0.154 |
| non-residential built | +0.124 | **+0.177** | +0.144 | +0.119 |

For the two strongest families, skill **rises monotonically with radius** and peaks at the
coarsest buffer available — 2.4 km, which is larger than the 1 km cell the model reports on.

This is the sub-grid finding arriving from the opposite direction. §5 established that
within-cell spread exceeds between-cell spread, so fine structure cannot be placed. Phase 1 adds
that the information which *does* rank stations lives at scales **larger** than a grid cell.
Together they bracket the usable band tightly: too fine is unrecoverable, and what remains is
nearly coarse enough to be the city-mean question the model already answers well.

### Power: the frame is now adequate, and the bar is high

| frame | n | sd of paired difference | detectable at 80 % power |
|---|---:|---:|---:|
| Phase 0 (valley cities) | 8 | 0.250 | Δρ = 0.320 |
| **Phase 1 (LUR frame)** | **46** | 0.290 | **Δρ = 0.130** |

A 2.5× improvement, and 0.130 is a limit an experiment can be registered against.

🔴 **But note what it implies.** To be *detectable*, a learned pattern must reach ρ ≈ **0.44**
pooled — 0.309 plus 0.130. That is at the bottom edge of what published LUR achieves (R²
0.43–0.83) on campaigns that site monitors deliberately across land-use contrast, which ours do
not. **The bar is reachable in principle and demanding in practice, and it should be written
into the registration as the number the work has to clear.**

## 4. Phase 1 — registration

Pre-register on OSF before any scoring, per project norm. Must contain:

- **The frame**: cities with ≥ 8 stations and ≥ 365 concurrent days. Realistically the LUR frame
  — 44 cities, 613 stations — minus cities failing the concurrency test.
- **The baselines**, all three: uniform `P ≡ 1`; raw emission surface; sector-weighted surface
  from Phase 0; and the shipped dispersed field.
- **A power calculation done first.** F.92's lesson: a null without a detection limit converts a
  limit of the experiment into a property of the atmosphere. State the minimum detectable Δρ at
  80 % power for the frame *before* running.
- **The refutation criterion**: if the learned pattern does not beat the better of the two
  emission surfaces, pooled and out of sample, the spatial rung stays a declared assumption and
  we say so.

## 5. Phase 2 — the model

**The gauge is the design constraint, not an afterthought.**

```
logits  ℓ(x,y,t) = f_θ(static geography, driver fields, time encodings)
pattern P(x,y,t) = N · softmax_cells( ℓ )        ⇒  mean_cells(P) ≡ 1 exactly
field   PM       = B(t) + max(inc,0)·P + min(inc,0) + ε(t)(P−1)
```

The softmax normalisation makes P1 (conservation) hold **by construction, in floating point**,
not approximately. The level stays where the observations constrain it; the network can only
move material around. That is what keeps this inside the budget framework rather than replacing
it, and it means a badly learned P degrades placement without ever corrupting the basin mean.

**Inputs**
- static: the 60 LUR predictors already built (road length by class at 50/100/300/500/1000 m,
  distance-to-road, NDVI, tree cover, water, land cover, built volume, population, night lights
  at four radii)
- dynamic: BLH, wind speed and direction, stability proxy, precipitation
- time: hour-of-day and day-of-year sin/cos
- terrain: elevation, height above local drainage floor, slope, sky-view

**🔴 Never lat/lon, and never a city identifier.** Gotcha #28. The Sim2Real run fine-tuned on two
Kandy sensors reached r = 0.9999 *at those sensors* while the grid annual mean inflated from
22.1 to 37.0 — it learned coordinates as identity keys. Any descriptor that exists only for a
city with local observations is inadmissible (gotcha #73).

**🔴 No fused PM2.5 product as an input.** F.96: a monitor-trained covariate deflates the measured
value of monitors by roughly half. Raw AOD and GEOS-CF are clean; GHAP-style products are not.

**Architecture**: start with a per-cell MLP on the covariate stack, then a small CNN or ConvCNP
if the MLP shows signal. Deliberately in that order — the ladder work showed a linear model
collapses on 68 features while three non-linear learners agree within 2.5 points, so capacity is
not the scarce resource here and a large model risks memorising 44 cities.

**Loss**: at each withheld station, compare `H_k[PM] + b_k` to the observation, with `H_k` the
observation operator and `b_k` the per-sensor offset from §2.2 of the model paper. Fitting P
against raw co-located values would re-import the change-of-support error the whole paper is
about — and would show up exactly as the 72.4 % coverage that re-centres to 92.2 % once offsets
are removed.

## 6. Phase 3 — scoring

- **Leave-one-city-out**, always. A model that has seen a city is not informative about a city it
  has not.
- **Budget-matched**: give the model what the target city's tier allows, score against every
  station withheld. Matching the *budget* and not merely the *city* is what made the ladder
  interpretable and applies identically here.
- **Primary metric**: per-city Spearman ρ across withheld stations on the network-mean-removed
  anomaly, reported as a distribution and never pooled into one number.
- **Report per band and per instrument class.** The class × band confound cannot be sampled away.
- **Report the paired-site diagnostic** at Kandy alongside ρ: a model can improve rank and still
  be unable to separate two points inside one cell, and the reader needs both.

## 7. Phase 4 — what would make it publishable either way

| outcome | what is written |
|---|---|
| beats both emission surfaces out of sample | the spatial rung moves from *declared* to *validated*; `Bud4` gets evidence |
| beats the dispersed field but not the raw surface | **"learning recovers what the solver destroys"** — replace the dispersion step, report honestly that the gain is a repair rather than new information |
| beats nothing | a sixth null, but the **first with a stated detection limit** — which is what the previous five lacked |

All three are results. The third is the most likely and is still worth the work, because it
converts "we could not find it" into "an effect larger than Δρ = *x* is not there".

## 7b. 🔴 PHASE 2 RESULT — the bar is not cleared

Run 2026-09-04, `scripts/phase2_learned_pattern.py` + `phase2_gauge_check.py`.
Registered at [osf.io/2jyfg](https://osf.io/2jyfg/) **before the model was written**.

| learner | median ρ | positive in |
|---|---:|---:|
| random forest | **+0.286** | 37/46 |
| MLP | +0.236 | 36/46 |
| ridge | +0.221 | 38/46 |
| **benchmark** (built-up land cover, 2.4 km) | **+0.309** | 35/46 |

**The learned pattern is indistinguishable from a single predictor.** Median paired delta
**+0.022**, better in **25 of 46** cities, **p = 0.94**.

⚠ **The two summaries disagree in sign and both are reported.** The median of the paired
differences is +0.022; the difference of the medians is −0.023. Medians are not linear, so this
is not a contradiction, but quoting either alone would misrepresent the result. The defensible
statement is that there is **no detectable difference**, which both agree on.

### The registered verdict

| | prediction | outcome |
|---|---|---|
| **L1** | does **not** reach ρ ≥ 0.44 | 🟢 **HELD** — achieved 0.286 |
| **L2** | beats the shipped dispersed field (0.274) | 🟢 **HELD** — 0.286 > 0.274 |
| **L3** | conservation holds to floating point | 🟢 **HELD** — worst drift 3.3e-16 |
| **L4** | skill lower in the deep tropics than temperate | 🟢 **HELD** — 0.236 vs 0.457 |
| **L5** | coarse-radius inputs dominate | 🟡 held by the letter only — 52.1 % vs 47.9 % |

Per the registration: the gain over the benchmark is **+0.022 against a detection limit of
0.130**, so this is reported as **undetectable at this power**, not as a modest success.

### What is worth keeping

🟡 **Skill is not uniform across bands — but the mechanism is NOT established.** Temperate
**+0.457**, deep tropical +0.236, subtropical +0.204, tropical +0.201; temperate against the
rest gives p = 0.006, and it survives de-confounding within the larger network (temperate +0.575
against +0.155, p = 0.002, 35 cities, all four bands).

⚠ **I overstated this on first reading and am correcting it.** I wrote that "the transfer
problem is now measured". It is not. The second network runs the *other* way — its tropical
cities score +0.546 against its temperate +0.323 — and while it is far too thin to adjudicate
(11 cities, one country, cells of 3 and 4), it is enough to block the causal story that the gap
is *because* tropical monitoring is sparse. Its tropical cities carry a dense reference network,
unlike tropical monitoring generally, which is a plausible explanation and not a tested one.

The defensible claim is narrower: **skill is lower outside the temperate band within the network
that can test it**, and whether the driver is latitude or network character is unresolved. The
practical consequence survives either way — a pattern learned from the world's monitored cities
performs worst in the regime that most needs it — but that is a consequence, not a mechanism.

⚠ The within-network test was **not pre-registered**; L4 registered only the band comparison.
It is exploratory and must be labelled so.

🟢 **The gauge is exact and survives abuse.** Worst |mean(P) − 1| is 3.3e-16 across seven cases
including a saturated pattern where one cell takes 4096× the mean, an overflow-range logit field
(sd 200), and a dead constant field. The field's spatial mean returns the anchor to 7e-15, and a
ventilated hour renders exactly flat. **A learned pattern can misplace material; it cannot
create it.** That property is what would make this safe to ship if it ever did work.

🟢 **NDVI at 2.4 km is the single most important feature** (importance 0.086, more than double
the next), corroborating Phase 1 from inside the model. Absence of vegetation carries more
usable spatial information than any presence-of-source proxy.

⚠ **L5 is technically held and substantively uninformative.** Coarse radii take 52.1 % of
radius-tagged importance against 47.9 % fine — a ratio of 1.09. It does not refute the
registered direction and it does not support it either, and it should be reported that way
rather than as confirmation.

### The conclusion this licenses

This is the **sixth null on within-city spatial pattern in this programme, and the first with a
detection limit stated in advance**. It converts "we could not find it" into a bounded claim:

> On 46 cities and 630 stations, a learned within-city pattern does not beat the best single
> globally available predictor by more than 0.13 in rank correlation, and the best single
> predictor reaches 0.309.

The model paper's §5 position — that the spatial rung is a **declared design assumption** — is
unchanged and now rests on a test that could have overturned it. `Bud4` stays declared.

## 8. Sequencing

| phase | work | gate |
|---|---|---|
| 0 | wire and score the sector-weighted emission surface | is the traffic-only proxy the limit? |
| 1 | frame, power calculation, OSF registration | detection limit stated before running |
| 2 | gauge-constrained learner, MLP first | P1 holds to floating point; no lat/lon anywhere |
| 3 | LOCO scoring against four baselines | out of sample, budget-matched, stratified |
| 4 | write up whichever of the three outcomes occurred | — |

**Do not start Phase 2 before Phase 0 has a number.** The most likely way this work goes wrong is
spending a month on a network that turns out to be competing against a traffic surface in cities
that mostly burn biomass.
