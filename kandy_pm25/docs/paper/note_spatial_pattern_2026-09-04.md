# A pre-registered null on learned within-city PM2.5 pattern, with a stated detection limit

**Methods note.** Draft 2026-09-04. Companion to the model paper (`docs/paper/`), which argues
in §5 that the spatial rung of the information budget is a *declared design assumption*. This
note is the test of that assumption. Pre-registered at
[osf.io/2jyfg](https://osf.io/2jyfg/) before the model was written.

---

## Abstract

Gridded PM2.5 products are increasingly used to rank neighbourhoods within a city, and the
literature offers little evidence that they can. We pre-registered a test: can a spatial pattern
learned from a multi-city panel place the within-city increment better than the single best
globally available predictor? On **46 cities and 630 stations**, the best single predictor —
built-up land-cover fraction within 2.4 km — reaches a median per-city rank correlation of
**0.309**. A learned pattern reaches **0.286**, a median paired difference of **+0.022**
(25 of 46 cities, *p* = 0.94) against a pre-registered detection limit of **0.130**. We report
this as **undetectable at this power**, which is the form the registration required.

Two results survive the null. First, skill is **not uniform across latitude bands**: within a
single monitoring network, temperate cities reach 0.575 against 0.155 elsewhere (*p* = 0.002).
Second, the pattern is constructed so that its spatial mean is exactly one, which we verify to
3×10⁻¹⁶ across degenerate cases — so a learned pattern can misplace material but cannot create
it. We argue that this conservation property, not the learning, is what such a model should be
judged on.

---

## 1. Why a null needs a number

This programme has produced five previous nulls on within-city spatial pattern. All five were
reported without a detection limit, and a later power analysis established that they could only
have detected residual partial correlations of **0.65 to 0.96**. They therefore excluded a large
learnable signal and said nothing about a moderate one — while being written up as though they
had settled the question.

A null without a stated detection limit converts a limit of the experiment into a property of
the atmosphere. This note exists to do the same experiment properly: state the benchmark, state
what the frame can detect, register both, and then report whatever happens.

## 2. The benchmark, and a correction

An earlier, eight-city version of this comparison identified night lights as the best available
proxy at ρ ≈ 0.34. That figure does not survive a wider frame and is withdrawn. On 46 cities:

| predictor | median ρ | positive in |
|---|---:|---:|
| built-up land cover, 2.4 km | **+0.309** | 35/46 |
| built-up land cover, 1 km | +0.291 | 38/46 |
| population, 2.4 km | +0.252 | 33/46 |
| night lights, 300 m | +0.197 | 30/46 |
| non-residential built volume, 300 m | +0.177 | 31/46 |
| **NDVI, 300 m** | **−0.270** | 10/46 |

Two features of this table matter more than the ordering.

**NDVI is the most consistent predictor in the set.** At −0.270 it is nearly as strong as the
best positive proxy and more consistent in sign — negative in 36 of 46 cities. *Absence of
vegetation* discriminates better than the presence of any single modelled source.

**Skill rises with buffer radius and peaks at the coarsest available.** For built-up land cover:
+0.240 at 100 m, +0.216 at 300 m, +0.291 at 1 km, **+0.309 at 2.4 km**. The information that
ranks stations lives at scales *larger* than the 1 km cell these products report on. Read
alongside the established result that within-cell spread (1.218) exceeds between-cell spread
(1.049), the usable band is bracketed from both sides: finer than a cell is unrecoverable, and
what remains is coarser than a cell.

## 3. What was registered

| quantity | value |
|---|---:|
| benchmark | 0.309 |
| minimum detectable paired improvement, 80 % power, n = 46 | 0.130 |
| **the bar** | **ρ ≥ 0.44** |

We registered that a result below 0.44 would be reported as undetectable rather than as a modest
success, and we registered **L1: the bar will not be cleared**, noting that 0.44 is the bottom
edge of published land-use regression, which is achieved on campaigns that site monitors
deliberately across land-use contrast. Regulatory and low-cost networks are sited for compliance
and access; our frame is a convenience sample with coordinates.

Also fixed in advance: latitude, longitude and city identifiers are inadmissible inputs; no
fused monitor-trained PM2.5 product may be used as a covariate; the estimator order is MLP
before anything convolutional; and one frame, one metric, one bar, with no re-scoping after
seeing the result.

## 4. The model

The pattern is constrained rather than free:

```
ℓ(x,y,t) = f_θ(static geography, drivers, time)
P(x,y,t) = N · softmax_cells(ℓ)          ⇒  mean_cells(P) ≡ 1
PM       = B(t) + max(inc,0)·P + min(inc,0) + ε(t)(P−1)
```

Both features and target are standardised **within each city**, so the model learns ordering and
not level, and cannot exploit between-city level differences to appear skilful. Feature
standardisation uses only that city's predictors — globally available static geography, no local
observation — so it remains admissible for a city with no monitors.

The softmax is monotone within a city and therefore cannot change a rank correlation. We say so
explicitly: **the primary metric is invariant to the gauge**, and claiming the gauge through the
scoring would be claiming credit the scoring cannot see. The gauge is verified separately, in §6.

## 5. Result: the bar is not cleared

Leave-one-city-out, five seeds:

| learner | median ρ | positive in |
|---|---:|---:|
| random forest | **+0.286** | 37/46 |
| MLP | +0.236 | 36/46 |
| ridge | +0.221 | 38/46 |
| benchmark | +0.309 | 35/46 |

Median paired difference **+0.022**, better in **25 of 46**, *p* = 0.94.

⚠ The two natural summaries disagree in sign — median of paired differences +0.022, difference
of medians −0.023 — because medians are not linear. Both are reported; both support the same
conclusion, which is that there is **no detectable difference**.

**L1 held.** Achieved 0.286 against a bar of 0.44. Per the registration this is undetectable at
this power. **L2 held**: the learned pattern does beat the dispersed physical field (0.274),
which is consistent with the separate finding that the dispersion step *lowers* rank correlation
on two independent frames.

## 6. What survives the null

### 6.1 The gauge is exact, and that is the point

| case | \|mean(P) − 1\| | max P |
|---|---:|---:|
| typical, 256×256 | 0 | 68.8 |
| wide logits (sd 12) | 3.3e−16 | 3995 |
| saturated, one cell +40 | 0 | 4096 |
| extreme (sd 200) | 0 | 4096 |
| dead, all equal | 0 | 1.0 |

The field's spatial mean returns the temporal anchor to 7×10⁻¹⁵, and a ventilated hour
(increment < 0) renders exactly flat. **A learned pattern can misplace material; it cannot
create it.**

We think this is the property such a model should be judged on, and it is not standard practice.
An unconstrained downscaler that improves rank correlation while perturbing the areal mean has
traded a quantity the observations constrain for one they do not. Here the trade is impossible
by construction, so the cost of being wrong about placement is bounded and legible.

### 6.2 Skill is not uniform across latitude bands

| band | n | median ρ |
|---|---:|---:|
| temperate | 11 | **+0.457** |
| deep tropical | 12 | +0.236 |
| subtropical | 10 | +0.204 |
| tropical | 13 | +0.201 |

Temperate against the rest: *p* = 0.006. **And this survives de-confounding by network**, which
matters because monitoring network is associated with latitude in any global panel. Within the
larger network alone (35 cities, all four bands): temperate **+0.575** against **+0.155**
elsewhere, *p* = 0.002.

⚠ **We do not claim the mechanism.** The second network in the panel runs the other way — its
tropical cities score +0.546 against its temperate +0.323 — but it contributes 11 cities from a
single country across three bands, with cells of three and four. It is too thin to adjudicate,
and its tropical cities carry a dense reference network unlike tropical monitoring generally. So
the defensible statement is that **skill is lower outside the temperate band within the network
that can test it**, and whether the driver is latitude or network character is unresolved.

The consequence is the same either way, and it is the practical one: a pattern learned from the
world's monitored cities performs worst in the regime that most needs it.

### 6.3 The most informative input is vegetation

NDVI at 2.4 km is the single most important feature in the fitted model (importance 0.086, more
than double the next), corroborating §2 from inside the model rather than from a univariate
screen.

⚠ Coarse-radius inputs take 52.1 % of radius-tagged importance against 47.9 % fine — a ratio of
1.09. We registered that coarse radii would dominate; the direction is not refuted and it is not
meaningfully supported either, and we report it as uninformative.

## 7. What this licenses, and what it does not

> On 46 cities and 630 stations, a learned within-city pattern does not beat the best single
> globally available predictor by more than 0.13 in rank correlation, and that predictor reaches
> 0.309.

That is a bounded claim, and it is the first of the six nulls in this programme that is one.

**It does not show that within-city structure is unlearnable.** It shows that an effect larger
than 0.13 is not present on this frame, with these predictors, at this support. A campaign that
sited monitors deliberately across land-use contrast would be a different experiment, and §2's
radius result suggests the limiting factor is support rather than method.

**It does not license a neighbourhood-scale product.** Within-cell spread exceeds between-cell
spread; the question a 1 km field can answer is how wide a cell's distribution is, not which
part of it is worst.

The model paper's position is therefore unchanged: the spatial rung is a **declared design
assumption**, now resting on a test that could have overturned it.

---

## Drafting notes, to remove before submission

- Figure candidates: the ladder of predictors by radius (§2), the band-stratified result with
  the network stratification beside it (§6.2), and the gauge table as a panel rather than a
  table (§6.1). Three figures, which is right for a note.
- ⚠ §6.2's within-network test was **not pre-registered** — L4 registered only the band
  comparison, and the de-confounding was added after the band result appeared. It must be
  labelled exploratory. The registered L4 comparison stands on its own.
- Decide the venue. This is too small for a full paper and too specific for a letter; a methods
  note or a registered-report style short communication fits.
