# Improvement plan — corrections, the sub-grid reopening, and propagation

**Opened 2026-09-01.** Scope: everything surfaced by the 2026-09-01 adversarial audit, plus the
deliberate omissions the user has agreed to reopen. Companion to
[`paper/rewrite_plan_2026-08-22.md`](paper/rewrite_plan_2026-08-22.md), which remains the active
plan for the manuscript itself — this document is what must be true **before** that plan can be
executed on correct numbers.

**Ordering principle.** Corrections first, because nothing downstream is safe to write while a
headline number is wrong. Then the anti-drift machinery, because three of the four corrections
below are the *same* failure and it will recur. Then the science. Then propagation. Then prose.

---

## 0. The pre-registration boundary

Two classes of work appear below and they have different rules. Getting this wrong is what
produced F.84.

| class | rule | items |
|---|---|---|
| **Correction** — re-deriving an existing quantity, or fixing an implementation defect | no registration; the result replaces the old one and the ledger records the delta | C2, C3, C4, C5, C6 |
| **New test** — any question with a directional expectation whose answer could change a claim | **register on OSF before running**, with priors stated and a refutation criterion | C1, S1, S2, R2, R3 |

⚠ The registration must state what result would make us *abandon* the hypothesis, not only what
would confirm it. Five of eight priors were refuted in the last registered round; that is the
process working, and it only works if the priors are written down first.

---

## Phase 1 — Close the numbers  ·  1–2 days  ·  **blocks everything**

Every item is a number, and numbers do not improve by being written around.

### C1 — The satellite stream is an annual scalar 🔴 *new test, register first*
`scripts/build_bud0_streams.py:26` pulls `GHAP_Y1K_PM25` — one scalar per city, invariant in
time — and the ladder then reports that this stream buys **7.6%** on *daily* RMSE and concludes
static geography (10.8%) is worth more. `GHAP_D1K_PM25` (daily, 1 km) exists in the same asset
family and is named in gotcha #50.

This is the F.84 failure mode one level down: `require_covers()` asserts a stream is *used*, and
cannot see that it was implemented in its weakest available form.

- **Register** the prediction: a daily satellite stream raises the `Bud0b→Bud0c` step from 7.6%
  to *X*, and either does or does not overturn "geography beats satellite".
- **Then decide and record which of two worlds we are in:**
  - **(a) admissible** — re-pull daily GHAP, re-run `Bud0c`, report both the annual and daily
    variants, and let the ladder say which stream wins.
  - **(b) inadmissible** — GHAP is itself a fusion product trained partly on ground monitors, so
    a daily value at a monitored city plausibly leaks the monitors we are pricing. If this is the
    call, it is a **finding**, it goes in §3 as a stated admissibility decision, and the annual
    product is labelled as the deliberately conservative choice.
- ⚠ Note the leakage argument applies to the annual product too, merely averaged. Whatever we
  conclude must be consistent across both.

**Gate:** the paper can state, in one sentence with a reason, why the satellite stream is the
form it is. Silence is not an option — this is the first question a GMD reviewer asks.

### C2 — Coastal gain is misattributed 🟡 *correction*
The reported "satellite helps coastal cities 4× more (24.4% vs 6.2%)" is measured
`Bud0a→Bud0c` — **geography and satellite together** — and reported under the satellite's name.
Decomposed from `ladder_revalidated.csv`:

| step | coastal (n=21) | inland (n=27) | ratio |
|---|---:|---:|---:|
| geography only `0a→0b` | 21.0% | 6.8% | 3.1× |
| satellite only `0b→0c` | 13.3% | 7.3% | **1.8×** |
| as currently reported `0a→0c` | 24.4% | 6.2% | 3.9× |

**Restate as:** place-describing data (geography + satellite level) is worth ~4× more at coastal
cities than inland, and the geography component carries most of it. The finding survives and
gets stronger, because it now says something about *why*.

### C3 — Stratified numbers were never re-derived after the re-validation 🔴 *correction*
Documented median `w_Bud2`: reference **0.000**, LCS **0.900**. Recomputed from the re-validated
file: reference **0.350**, LCS **0.575**. Direction survives; the strong claim that reference
networks gain nothing from stations 3–8 does not.

- Re-derive **every** stratified statistic from `ladder_revalidated.csv`, not just those in the
  headline table. Band, instrument class, coastal, and every cross-tabulation.
- Revisit the **Kandy-analogue argument**, which rested on a contrast that is now ~1.6×, not
  infinite. It may still hold; it must be re-argued, not inherited.
- Update the hard rule in `CLAUDE.md` that was built on the retired split.

### C4 — Frame statistics are the superseded run's 🟡 *correction*
Claimed **47 cities / 32,396 city-days**. Actual, from the scored file: **48 cities / 28,930
city-days** — scale overstated by 10.7%. Regenerate from the file; hardcode nothing a script can
compute.

### C5 — P4 reports grid artefacts as "identified" 🔴 *correction*
`p4_identifiability.csv` marks parameters `identified` where `lo95 == hi95 == mle` and
`box_fraction = 0.0` — a single grid cell, not a profile-likelihood interval. Medellín's `s_exp`
is 0.708 at `Bud1` and 1.167 at `Bud2`, both zero-width; two non-overlapping point estimates for
one parameter is the signature of non-identifiability being labelled its opposite.

- Refine the profile grid until intervals have non-zero width, **or** report coarse cases as
  `grid-limited` rather than `identified`.
- The genuinely honest results are in the same file and are the interesting ones — Kathmandu's
  `kappa`, `eps0`, `w_evening` all `UNIDENTIFIED` with `box_fraction = 1.0`. Lead with those.
- ⚠ P4 is the property called *declared identifiability*. Declaring something identified on a
  grid artefact is the one error this specific claim cannot survive.

### C6 — Documentation staleness 🟢 *correction*
- `MODEL_SPECIFICATION.md` §9 says P4 is "not run" (F.75 ran it) and `theta` is "not yet fitted
  on the panel" (F.77 fitted `s_exp`). Understates the project by two completed pieces of work.
- `CLAUDE.md` Key Paths points at `data/processed/modular/elangasinghe_spatial_test.csv`; the
  file is in `data/processed/decomp/`.
- The coastal caveat — "the panel is 10 cities, all valley/basin, zero coastal" — describes the
  old frame. The ladder has **21 coastal cities** and Colombo is zero-shot tested. The caveat now
  *understates* our own coverage.

**PHASE GATE.** A single script regenerates every frame, pooled and stratified statistic from the
scored files and emits one machine-readable claims file. No number in any document is quoted from
prose.

---

## Phase 2 — Make prose mechanically unable to drift from data  ·  2–3 days

C2, C3 and C4 are the same failure three times, and F.84 was the fourth. The cause is structural:
the audit trail lives in prose and the numbers live in CSVs, and nothing connects them.

- Every numeric claim in the manuscript becomes a `{{claim:tag}}` token resolved at build time
  from the Phase-1 claims file — the same discipline already applied to `{{fig:tag}}`.
- Each claim entry carries: value, statistic (median/mean — never averaged across metrics,
  gotcha #74), n, source file, generating script, and ledger reference.
- **The build fails** on an unresolved token, or on a claim whose provenance script no longer
  runs, or on a stored value that disagrees with a fresh recomputation.
- Extend the mechanical pre-submission gate to: figure numbering (gotcha #58), city counts,
  palette colour-vision check (F.83 — `turbo` must come off the episode maps), zero raw
  `assemble_manuscript.py` markers, zero `??` / `Fig.~` / `ef{fig`.

**Gate:** deleting a row from the claims file breaks the build. This is itself a methods
contribution and earns a paragraph in §3.

---

## Phase 3 — The sub-grid reopening  ·  the largest scientific opportunity

### The finding that opened it
`data/processed/decomp/S_traffic_kandy.npz` ships two arrays. The model uses `S_traffic`,
16×16 at **998 m**. Beside it in the same file is `E_fine`, 160×160 at **94 m**.

At the two botanical-garden microsites — the paper's money figure:

| | entrance | 300 m inside | ratio |
|---|---:|---:|---:|
| observed (Elangasinghe, PM10) | 110 | 4 | **27.5×** |
| shipped 1 km surface | 1.7719 | 1.7719 | **1.000×** |
| **`E_fine`, 94 m** | **0.1026** | **0.0455** | **2.25×** |

Domain-wide, `E_fine` has p90/p10 = **63.8×** against the transect's observed 85×; the shipped
1 km field has **1.23×**.

**The model carries correctly-signed sub-grid structure of roughly the right dynamic range, and
discards it at the aggregation step.** The paper currently states the model has no information at
this scale. That is true of the *product* and false of the *model*.

⚠ Emission is not concentration — dispersion will damp 63.8× substantially, and "emission ≠
concentration" is already one of the six ceiling arguments. It will not damp to 1.23×.

### S1 — Does the fine field place the contrast? 🔴 *new test, register first*
Register both outcomes as publishable before running:

- **If yes** — a dispersed 94 m field reproduces the paired-site ordering and a material fraction
  of the observed contrast. §5 changes from a limitation into a result, and the spatial axis moves
  off "no".
- **If no** — the ceiling claim gets its strongest possible test: the model cannot place
  within-city contrast *even at 94 m with its own emission field*, which is a far stronger
  statement than the current one and closes the question permanently.

**Method.** Disperse `E_fine` (the existing `A_transport` solver already operates on a grid;
this is a resolution change, not a new physics component), score against the Elangasinghe
transect and the two paired sites, and report at matched support.

⚠ **Admissibility:** the Elangasinghe transect must be held out of any fitting. It is the only
within-Kandy spatial ground truth that exists; using it to tune and then to score repeats
gotcha #68.

### S2 — The within-pixel distributional product 🔴 *new test, register first*
The shipped parquet carries `pm25_q50/q05/q95/blo/bhi` — all uncertainty on the **areal mean**.
There is no within-pixel quantity at all, which is why "where in the basin is it bad" is
structurally unanswerable.

Build a within-pixel distribution: given a cell's mean and its 94 m emission composition, predict
the *quantiles inside that cell* rather than a point value. This is a change-of-support product,
it directly answers the user-facing question, and it converts the project's largest measured
negative into a contribution.

**Validation data already exists and is unusable for anything else:** the Elangasinghe transect
(25 sites, 3 h, kerbside), Wickramasinghe (20 sites, 8 h, area-representative) and Premasiri /
NBRO (5 sites, 24 h) are useless for a *pointwise* claim and are exactly right for a
*distributional* one, because each measures a different quantile of a within-city distribution at
a different support.

⚠ This is **not** re-litigating the closed spatial nulls. All five asked *"can we rank stations
against point observations?"*. This asks *"what is the distribution inside a cell?"* — different
question, different data, different validation design. Say so explicitly in the registration, or
it will be read as a sixth attempt.

---

## Phase 4 — Reopened omissions  ·  ranked by leverage

### R1 — Network design output 🟢 *no new modelling, highest citation value*
We measured what each increment of information is worth across 48 cities and never turned it into
*"where should Sri Lanka put its next five monitors, and what would each one buy?"* It falls
straight out of the ladder, costs almost nothing, and is the natural headline for a country whose
regulator has just confirmed the data is free for academic use.

Output: a ranked siting recommendation with the expected RMSE reduction per instrument, stratified
by instrument class, with the `Bud2→Bud3` regional-background rung leading — it is the largest
measured gain in the programme and has no free substitute (F.63).

### R2 — Score `A_transport` 🟡 *new test, register first*
A whole layer ships as a "scenario" with **zero** evidence. Two acceptable outcomes: score it
against the panel, or state in the abstract that the headline field excludes it. Continuing to
ship an unscored layer without saying so in the abstract is the most attackable thing in the
paper.

### R3 — Benchmark against the direct competitor 🟡 *new test, register first*
**EGU26-9786** (CICERO / HISP / MoH / Oslo) is a Sri Lanka 1 km **daily** PM2.5 product for
2020–2023. The current plan is to cite and position it. Scoring our Kandy field against it is a
free external check on the **level** axis, which is exactly where W11 is open. Register the
prediction before looking.

### R4 — Multi-pollutant ⏸ *blocked on CEA*
The CEA record carries PM10 and gases. PM10/PM2.5 ratio is a source-mix diagnostic bearing
directly on W6, and we are modelling one species from a dataset with five. Parked until the data
lands; listed so it is not forgotten.

### R5 — Vertical structure and `kappa` ⏸ *paper B or later*
The model is 2D, yet `M` is *about* vertical mixing and its one parameter is measurably
unidentifiable at `Bud1` (F.75). Those two facts are connected and neither is currently
discussed. At minimum, say so in §2 — the honest sentence costs nothing and pre-empts the
question.

### R6 — Chemistry ⏸ *long horizon, paper B+*
The largest scientific omission and the cheapest to climb given the user's background. No
secondary aerosol, no gas-particle partitioning, no deposition. Out of scope for paper A; it is
the difference between *estimating* PM2.5 and *understanding* it, and it belongs in the research
programme that follows.

---

## Phase 5 — Evidence hygiene on what already exists

- **Disclose the transect's censoring.** Of the 12 sites, four are censored at 150 and three
  binned at 32.5 — roughly six distinct values. The Spearman ρ = +0.44, p = 0.16 is a much weaker
  test than it reads. **Both paired-site results survive intact** (110 vs 4; 150 vs 32.5 at the
  Girls' HS) because they use distinct uncensored values — which is precisely why the rewrite
  plan was right to promote the paired result and demote the ladder.
- **Label the units.** Observed is **PM10**, modelled is **PM2.5**. Defensible for a ratio claim
  and indefensible if unstated.
- **Put per-cell n in the ladder figure itself**, not the caption. Subtropical and temperate are
  n = 7. A reviewer who has to hunt for the sample size assumes it was hidden.

---

## Phase 6 — Propagation  ·  after every gate above has passed

Nothing propagates until it is tested. Then it propagates to **all** targets in the same pass, or
the repo ends up publicly asserting something already refuted internally.

| target | what changes |
|---|---|
| **Framework** (`kandy_pm25/`) | code, scored products, the claims file |
| **Release repo** (`kandy_pm25_release/`) | port confirmed changes; rewrite imports `src.stage1_satml.* → kandymodel.*`, fix `parents[3] → parents[1\|2]`, retest (gotcha #55) |
| **Model reference + ledger** | new `F.*` entries for C1, C3, C5, S1, S2, R2, R3; rebuild `MODEL_REFERENCE_COMBINED.md` |
| **Context files** | `CONTEXT.md` (headline numbers, retired list), `CLAUDE.md` (state, gotchas, hard rules), `PROJECT.md`, `PROJECT_ARCHITECTURE.md`, `README.md` |
| **Webapp** (`kandy_webapp/`) | only if a shipped field changes. Re-export, pass the QA gate (tol 0.25 µg/m³), bump `?v=<ts>`, and verify the push with `git -C <path> rev-list --count origin/main..HEAD` (gotcha #77) |

⚠ **Never ship on a partial rebuild** (gotcha #70). If `additive_v2` is rebuilt, `additive_v3`
rebuilds with it and the exporter QA re-runs.

⚠ **`README.md` and `PROJECT_ARCHITECTURE.md` are public.** A claim that changes internally is
checked against them in the same pass.

---

## Phase 7 — Then, and only then, write

Resume [`paper/rewrite_plan_2026-08-22.md`](paper/rewrite_plan_2026-08-22.md) from its Phase 0,
now on numbers that reproduce, with two changes of emphasis this plan has earned:

1. **Sell P3 harder.** Exact nesting is not an engineering nicety — it is *why our ablation is a
   measurement and everyone else's is a comparison of two different models*. That single argument
   is the paper's strongest and it is currently a table row.
2. **§5 leads with the sub-grid result**, whichever way S1 falls. Both outcomes are stronger than
   the current text.

---

## Dependency order, at a glance

```
Phase 1 (numbers) ──┬─→ Phase 2 (claims pipeline) ──┐
                    │                                │
Phase 0 (registrations) ─→ Phase 3 (sub-grid) ──────┼─→ Phase 6 (propagate) ─→ Phase 7 (write)
                         └─→ Phase 4 (R1,R2,R3) ────┘
                                                     
Phase 5 (hygiene) ─── independent, do alongside ─────┘
R4, R5, R6 ─── parked, not in this cycle
```

**Critical path:** Phase 1 → Phase 3/S1 → Phase 6 → Phase 7. Phases 2, 4 and 5 are parallelisable
and none of them blocks the paper.

**What is NOT in this plan, deliberately:** the six closed spatial nulls, GEMS, Colombo as a
background donor, civil-vs-solar time, the five background rebuilds, the `f` partition, GNN/PINN
at Kandy, diffusion downscaling. Each has a recorded measurement behind it. See
`CLAUDE.md` § 4 *Closed — do NOT re-litigate* before spending anything on them.
