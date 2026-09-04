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

**Phase 0 gate:** if the sector-weighted surface alone closes a material part of the 0.371 → we
report that and the learned-P work starts from a higher baseline. If it does not, we have
established that the source-mix mis-specification is not what is limiting placement — which is
itself worth knowing before spending a month on a network.

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
