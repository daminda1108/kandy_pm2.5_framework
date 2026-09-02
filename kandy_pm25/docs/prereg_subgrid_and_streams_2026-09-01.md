# Pre-registration — sub-grid structure, stream independence, and two unscored layers

**Lodged 2026-09-01, before any of the runs below.** Covers the five new tests opened by
[`improvement_plan_2026-09-01.md`](improvement_plan_2026-09-01.md): **C1/S3** (stream
independence), **S1** (sub-grid placement), **S2** (the within-pixel distribution), **R2**
(`A_transport`), **R3** (external benchmark).

**OSF: [`bkpyr`](https://osf.io/bkpyr/)** — registered 2026-09-01T11:44:45Z, Open-Ended
Registration, project [`h8m9j`](https://osf.io/h8m9j/). Prior registrations in this programme:
`nxqgb` (Colombo, superseded), `g6hqb` (re-validation).

> **How OSF approval works — no action is required.** A new registration sits at
> `pending_registration_approval` for **48 hours**, and per OSF's own documentation *"after 48
> hours, the submission will automatically be approved"*. **The window is a CANCELLATION window,
> not an approval requirement**: if every admin does nothing, the registration goes public by
> itself. Acting early is possible only through the notification email's Approve / Cancel
> buttons — there is no dashboard equivalent — and rejecting returns the registration to draft
> for editing and resubmission.
>
> This one auto-approves at **2026-09-03 11:44 UTC**.
>
> ⚠ The scientific value does not depend on approval. What makes a pre-registration meaningful
> is the **timestamp**, and that is fixed at creation, so tests scored against this document are
> properly pre-registered whatever happens at the deadline.

---

## 0. Why this exists, and what it is guarding against

Five of eight priors were refuted in the last registered round, including the headline one. That
is the process working. It only works if the priors are written down first, and if each carries
a stated condition under which we abandon it.

⚠ **The specific failure this document guards against.** Four times now a quantity has been
attributed to the wrong source: F.84 (a tier under-using its budget), C2 (a combined step
reported under one stream's name), C7 (a city scored in a rung whose streams it lacks), and
C1 (a fused product presented as an independent satellite observation). Every one was invisible
in the pooled numbers. **Each test below therefore names, in advance, what its measured quantity
is a mixture of.**

⚠ **Standing analysis rules for every test here.** Median of per-city ratios, never a ratio of
medians; reported per metric and never averaged across metrics (gotcha #74); per-unit stream
coverage asserted with `Budget.require_covers_units` (C7); stratified by instrument class and by
coastal/inland, both of which were confounders in the previous round; `n` reported in the figure
itself, not the caption.

---

## 1. C1/S3 — is a satellite stream measuring satellite information?

Full reasoning: [`c1_satellite_stream_research_2026-09-01.md`](c1_satellite_stream_research_2026-09-01.md).

**Background.** `SATELLITE_LEVEL` is GHAP, which trains on ~9,500 stations including OpenAQ and
CNEMC — the two sources of this study's panel — and predicts from a feature set that
substantially overlaps the tier's other two streams (all seven of our drivers; NDVI, night
lights, population, elevation from our geography; plus GEOS-CF, CAMS, humidity, pressure,
precipitation and evaporation, which we do not carry).

**Design.** Identical stream-complete frame (n = 47), learner, seed and LOCO folds throughout:
`Bud0b` → `Bud0c-raw` (+ MAIAC/MODIS AOD) → `Bud0c-fused` (+ GHAP).

| # | prediction | refuted if |
|---|---|---|
| P1 | `Bud0c-raw` buys **less** than the 7.6% attributed to GHAP | raw AOD ≥ 7.6% |
| P2 | `Bud0c-raw` is nonetheless **> 0** | raw AOD ≤ 0 at the median city |
| P3 | fused − raw **> 0**: the fused product's excess is real and measurable | fused does not beat raw |
| P4 | the excess is **larger where there are more monitors** — the signature of leakage rather than better physics | no association with station count |
| P5 | geography (10.8%) still exceeds `Bud0c-raw`, so "geography beats satellite" survives with an honest stream | raw AOD ≥ geography |

⚠ **P4 is the weakest test here and we say so in advance:** n = 47, a crude station count, and
leakage and genuine skill both plausibly rise with monitor density. If P4 is refuted the leakage
is reported as an argued risk, not a measured one.

**What the quantity is a mixture of.** `Bud0c-fused` − `Bud0b` bundles: AOD information,
drivers we lack, a non-linear recombination of information already in the tier, and indirect
monitor leakage. The point of `Bud0c-raw` is that it bundles only the first.

---

## 2. S1 — does the model's own sub-grid field place within-city contrast?

**Background.** `S_traffic_kandy.npz` ships `E_fine` at 160×160 (**94 m**) beside the 16×16
(**998 m**) surface the model uses. At the paired botanical-garden microsites the shipped field
gives **1.000×** and `E_fine` gives **2.25×**, correctly signed, against **27.5×** observed.
Domain-wide `E_fine` spans **63.8×** (p90/p10) against the transect's observed 85×; the shipped
1 km field spans 1.23×.

**Design.** Disperse `E_fine` through the existing `A_transport` solver at 94 m — a resolution
change, not a new physics component — and score against the Elangasinghe transect and the two
paired sites, at matched support and matched hours (11–13 LT).

| # | prediction | refuted if |
|---|---|---|
| S1a | the dispersed 94 m field separates the paired sites by **> 1.5×** | ≤ 1.5×, i.e. dispersion erases what the emission surface has |
| S1b | it recovers **< 27.5×** — dispersion damps emission contrast substantially | ≥ 27.5× |
| S1c | rank correlation against the transect **exceeds** the 1 km field's ρ = +0.44 | ρ does not improve |
| S1d | the p90/p10 of the dispersed field lands **between** 1.23× and 63.8× | outside that interval |

**Both outcomes are registered as publishable.** If S1a holds, §5 changes from a limitation into
a result and the spatial axis moves off "no". If S1a is refuted, the ceiling claim gets its
strongest possible form — the model cannot place within-city contrast *even at 94 m with its own
emission field* — and the question closes permanently.

🔴 **Admissibility.** The Elangasinghe transect is **held out of all fitting**. It is the only
within-Kandy spatial ground truth in existence; using it to tune and then to score would repeat
gotcha #68. No parameter is re-fitted for this test; `s_exp` stays at 1.0 (F.77).

⚠ **This is not a sixth attempt at the closed spatial nulls.** All five asked *"can we rank
stations against point observations?"*. S1 asks whether a finer field, dispersed, reproduces a
contrast measured at matched support between two points inside one pixel. Different question,
different data, different validation design.

⚠ **Known limitation, stated first:** observed values are **PM10** and the model is **PM2.5**,
so only ratio comparisons are valid. Four of the twelve transect sites are censored at 150 and
three binned at 32.5, leaving ~6 distinct values — the rank test (S1c) is correspondingly weak
and the **paired-site tests are the primary evidence**.

---

## 3. S2 — a within-pixel distribution

**Background.** The shipped parquet carries `pm25_q50/q05/q95/blo/bhi`, every one of which is
uncertainty on the **areal mean**. There is no within-pixel quantity, so "is it bad where I
live?" is structurally unanswerable.

**Design.** Predict the distribution of concentration *inside* each 1 km cell from the cell mean
and its 94 m emission composition. Validate against three datasets that are useless for a
pointwise claim and appropriate for a distributional one, because each samples a different
quantile at a different support: Elangasinghe (25 sites, 3 h, kerbside), Wickramasinghe (20
sites, 8 h, area-representative), Premasiri/NBRO (5 sites, 24 h).

| # | prediction | refuted if |
|---|---|---|
| S2a | the predicted within-pixel p90/p10 **exceeds** the between-pixel p90/p10 of 1.232 | within ≤ between |
| S2b | kerbside 3-h samples fall in the **upper** predicted quantiles, area-representative 8-h samples nearer the median | no ordering by support |
| S2c | the cell **mean is preserved** — the distribution is a decomposition, not a re-level | mean drifts > 0.05 µg/m³ (the P1 gate) |

⚠ S2c is a construction requirement, not a finding: if it fails the implementation is wrong.
It is registered so that it cannot be quietly relaxed.

---

## 4. R2 — score `A_transport`, which has never been scored

**Background.** A whole layer of the production field ships as a "scenario" with **zero**
evidence. It is the most attackable thing in the paper.

| # | prediction | refuted if |
|---|---|---|
| R2a | including `A_transport` improves held-out station rank correlation on the panel | ρ does not improve |
| R2b | any improvement is **small** — below the 0.2–0.28 spatial ceiling already measured | it exceeds the ceiling, which would itself be a major result |

**Either outcome resolves the item.** If R2a holds, the layer is scored and stays. If refuted,
the abstract states that the headline field excludes it. Continuing to ship an unscored layer
*without saying so in the abstract* is not among the outcomes.

⚠ `A_transport` is a topographically-steered redistribution filter, **not forward fluid
dynamics**. Steady-state per hour cannot represent recirculating valley eddies or multi-hour
stagnation. Stated in the text, not left to be pointed out.

---

## 5. R3 — external benchmark against a competing product

**Background.** EGU26-9786 (CICERO / HISP / MoH / Oslo) is a Sri Lanka 1 km **daily** PM2.5
product for 2020–2023. It is a free external check on the **level** axis, which is where W11 is
open.

| # | prediction | refuted if |
|---|---|---|
| R3a | the two products agree on Kandy's **annual level** within 20% | they differ by more |
| R3b | they agree better on **seasonal shape** (r > 0.8) than on day-to-day variation | seasonal r ≤ day-to-day r |
| R3c | where they disagree, ours reads **higher** — consistent with W11, where three of four point records sit below us | ours reads lower |

⚠ **Agreement is not validation.** If it is also a monitor-trained fusion it shares GHAP's
contamination and much of our driver set, so agreement partly measures shared inputs. This is
recorded **before** the comparison so a favourable result cannot be over-read.

---

## 6. What we commit to reporting regardless of outcome

- Every prediction above, marked held or refuted, in a single table.
- The refuted ones **in the paper**, not an appendix. Five of eight were refuted last round and
  saying so is what makes the held ones worth anything.
- Any test abandoned for reasons other than its stated refutation criterion, with the reason.
- ⚠ If S1 is refuted, we do **not** re-scope it into a different question and re-run. The
  spatial ceiling has absorbed five attempts; this is the sixth and the last.
