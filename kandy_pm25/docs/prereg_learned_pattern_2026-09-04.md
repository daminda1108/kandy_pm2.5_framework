# Pre-registration — a gauge-constrained learned spatial pattern

**Lodged 2026-09-04, before any model is fitted.** Covers the experiment planned in
[`learned_pattern_plan_2026-09-04.md`](learned_pattern_plan_2026-09-04.md). Phases 0 and 1 of
that plan are already run and are **reported here as prior work, not as tests** — their numbers
set the benchmark and the detection limit this registration is written around.

**OSF: [`2jyfg`](https://osf.io/2jyfg/)** — registered 2026-09-04T08:00:43Z, Open-Ended
Registration, project [`dgtuq`](https://osf.io/dgtuq/), which carries this full text in its wiki.
Auto-approves at **2026-09-06 08:00 UTC**.

Prior registrations in this programme: `nxqgb` (Colombo, superseded), `g6hqb` (re-validation),
`bkpyr` (sub-grid and streams), `kx23c` (chemistry).

⚠ **A note on how this was posted, because it nearly went wrong.** The OSF API returned 500 and
502 on five consecutive attempts and then 403 on three more. One of the 500s had in fact
succeeded. The registration existed while the client was reporting failure, and the later 403s
were the already-consumed draft. Checking `/nodes/{id}/registrations/` is what established it —
an error response is not evidence that nothing happened (gotcha #77).

> **How OSF approval works — no action is required.** A new registration sits at
> `pending_registration_approval` for 48 hours and then auto-approves. The window is a
> *cancellation* window. The scientific value rests on the **timestamp**, which is fixed at
> creation.

---

## 0. Why this exists

This programme has produced **five nulls on within-city spatial pattern**, and §5 of the model
paper argues from them that the spatial rung is a *declared design assumption* rather than a
validated one. That argument is only honest if the assumption is testable, and this is the test.

⚠ **The specific failure this document guards against.** All five prior nulls were reported
without a detection limit. F.92 later established that they could only have detected residual
partial correlations of **0.65 to 0.96** — so they excluded a large learnable signal and said
nothing about a moderate one, while being written up as though they had settled the question. A
null without a stated detection limit converts a limit of the experiment into a property of the
atmosphere. **This registration states its detection limit before the experiment runs, and the
limit is the reason the frame was widened first.**

⚠ **Standing analysis rules.** Median of per-city rank correlations, never a ratio of medians;
reported per metric and never averaged across metrics (gotcha #74); stratified by latitude band
and instrument class, both of which were confounders in previous rounds; `n` reported in the
figure itself, not the caption; leave-one-city-out throughout.

---

## 1. What is already known, and is therefore not under test

Reported here so that nothing below can be presented as a discovery it is not.

**Phase 0 (run 2026-09-04).** On nine valley cities, no engineered emission surface beat a
single free raster. Sector-weighting the source by the declared per-city source mix scored
**+0.098** against the production traffic surface's **+0.319**; adding OSM industrial land use
lifted the composite to +0.166 and it still lost. Industrial land use *is* a genuine predictor —
best single proxy at Tai'an and Medellín, and it rescues Yichang, where the production surface
is anti-correlated with its own stations — but its median does not beat the simple proxies. That
frame could not have detected an improvement below **Δρ = 0.320**.

**Phase 1 (run 2026-09-04).** On 46 cities and 630 stations, the best single globally available
predictor is **built-up land-cover fraction at 2.4 km, median ρ = +0.309**, positive in 35 of 46
cities. Night lights reaches only +0.197, so the "night lights at 0.34" figure taken from the
eight-city frame is withdrawn. NDVI at −0.270 is the most *consistent* predictor in the set.

**Phase 1's structural finding.** For the two strongest predictor families, skill rises
monotonically with buffer radius and peaks at the coarsest buffer available (2.4 km) — larger
than the 1 km cell the model reports on. Combined with the established result that within-cell
spread (1.218) exceeds between-cell spread (1.049), the usable band is bracketed from both
sides: finer than a cell is unrecoverable, and what remains is coarser than a cell.

**We register the expectation that this bracketing is the binding constraint**, and that it is
more likely than not to defeat the experiment below. Stating that in advance is the point.

---

## 2. The question

Can a spatial pattern learned from a multi-city panel rank withheld stations within a city
better than the best single imposed predictor, **without breaking the conservation property that
makes the budget ladder measurable**?

---

## 3. The model

```
logits  ℓ(x,y,t) = f_θ(static geography, driver fields, time encodings)
pattern P(x,y,t) = N · softmax_cells( ℓ )        ⇒  mean_cells(P) ≡ 1 exactly
field   PM       = B(t) + max(inc,0)·P + min(inc,0) + ε(t)(P−1)
```

The softmax normalisation makes **P1 (conservation) hold in floating point, not
approximately**. The level stays where observations constrain it; the network can only move
material around. A badly learned pattern therefore degrades placement and can never corrupt the
basin mean. This is what keeps the work inside the budget framework rather than replacing it.

**Inputs.** The 60 static-geography predictors of the Phase 1 frame; BLH, wind speed and
direction, a stability proxy, precipitation; hour-of-day and day-of-year encodings; elevation,
height above local drainage floor, slope.

**🔴 Inadmissible by construction, declared in advance:** latitude/longitude, any city
identifier, and any descriptor that exists only for a city with local observations (gotcha #73).
No fused PM2.5 product (F.96 — a monitor-trained covariate deflates the measured value of
monitors). Fitting is on the observation operator `H_k[PM] + b_k`, never on raw co-located
values.

**Estimator order, fixed now so it cannot be chosen after seeing results:** per-cell MLP first;
a convolutional model only if the MLP shows signal. Capacity is not the scarce resource — three
non-linear learners agree within 2.5 points on the ladder — and a large model risks memorising
46 cities.

---

## 4. 🔴 The bar: ρ = 0.44

**Primary outcome:** median across cities of the per-city Spearman rank correlation between
predicted and observed station means, leave-one-city-out, on the Phase 1 frame.

| quantity | value | source |
|---|---:|---|
| benchmark to beat | **0.309** | best single predictor, Phase 1 |
| minimum detectable improvement at 80 % power | **0.130** | simulated, n = 46, paired sd 0.290 |
| **the bar** | **ρ ≥ 0.44** | benchmark + detection limit |

**A learned pattern that does not reach ρ ≈ 0.44 pooled has not been shown to work**, because at
this frame size we could not distinguish a smaller gain from noise. We register that number now
so that a result of, say, 0.36 is reported as *undetectable at this power* rather than as a
modest success.

⚠ **We note in advance that 0.44 is the bottom edge of published land-use regression** (R²
0.43–0.83), achieved on campaigns that site monitors deliberately across land-use contrast.
Regulatory and low-cost networks are sited for compliance and access, so our frame is a
convenience sample with coordinates. **We consider it more likely than not that the bar is not
cleared.**

---

## 5. Registered predictions

| # | prediction | refuted if |
|---|---|---|
| **L1** | The learned pattern does **not** reach ρ ≥ 0.44 | it does |
| **L2** | It **does** beat the shipped dispersed field (ρ = 0.274), because the dispersion step demonstrably destroys skill on two independent frames | it does not |
| **L3** | Conservation holds to floating-point precision: \|mean(P) − 1\| < 1e-9 at every hour | any hour exceeds it |
| **L4** | Skill is **not** uniform across bands; it is lower in the deep tropics, where reference monitoring is scarcest (6 clusters against 65 temperate) | deep-tropical skill matches or exceeds temperate |
| **L5** | The learned pattern's most informative inputs are the **coarse-radius** ones (≥ 1 km), mirroring Phase 1 | fine-radius predictors dominate |

L1 is stated as a null prediction deliberately. If it is refuted, that is the strongest possible
outcome and it was registered as a possibility rather than claimed afterwards.

---

## 6. What each outcome licenses

| outcome | what may be written |
|---|---|
| ρ ≥ 0.44 | the spatial rung moves from *declared assumption* to *validated*; `Bud4` gains evidence; §5 of the model paper is revised |
| 0.274 < ρ < 0.44 | **"learning recovers what the solver destroys"** — replace the dispersion step, and report explicitly that the gain is a repair and is below this frame's detection limit |
| ρ ≤ 0.274 | a sixth null — but the **first with a stated detection limit**, which converts "we could not find it" into "an effect larger than Δρ = 0.130 is not there" |

All three are publishable. The third is the most likely and is the reason the frame was widened
before the model was built.

---

## 7. Stopping rule

One frame, one primary metric, one bar. **No re-scoping after seeing the result**: if the bar is
missed we report the miss and the detection limit, and we do not re-cut the frame, change the
metric, or introduce a post-hoc stratification to find a subgroup where it worked. Stratified
results by band and instrument class are reported because they were registered here, not because
they were searched for afterwards.

If a defect is found in the machinery *before* scoring, it is fixed and this document is amended
with the amendment dated — the procedure followed for Amendment 2 of the ladder registration.
