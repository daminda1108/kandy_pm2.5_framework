# Rewrite plan — methods-primary paper, Kandy as demonstration

**Decided 2026-08-22 (user):** one paper, methods-primary, Kandy as the demonstration case.
Exposure, burden and the detailed Kandy application defer to a second paper written once CEA
data lands. **Journal target deferred until the outline is agreed.**

Supersedes `preprint_plan_2026-06-30.md` and the Phase-0–9 build of 2026-08-13/14 as the active
plan. Companion: `claims_audit_2026-08-22.md` (what changed and why). The existing 28-page
`manuscript_kandy.md` is **not** discarded — §4 below maps what survives.

---

## 1. The claim chain

Everything in the paper serves one of these six links. Anything that serves none is cut.

1. **The problem.** Most cities that need a PM2.5 field have no monitors to build or check one
   with. Models get built anyway, and almost none state what information they would need to be
   trustworthy.
2. **Contribution 1 — a formulation in which the information budget is declared.** Tiers `Bud0`
   (sensorless) to `Bud4`, with four properties that are asserted and tested, not hoped for:
   **P1** conservation, **P2** monotone skill under added data, **P3** exact (bit-exact) nesting
   between tiers, **P4** declared identifiability.
3. **Contribution 2 — the value of each increment of information is measured**, not asserted:
   47 cities, 32 countries, 4 latitude bands, 32,396 city-days, gates registered before running.
4. **Contribution 3 — two axes have measured ceilings**, and the spatial one is **a limit of
   definition, not of data**: within-city contrast collapses monotonically with averaging support
   (85× → 4.0× → 3.0× → 1.23×) across four independent campaigns in a single city.
5. **Demonstration.** The whole apparatus run at a city with two low-cost sensors, and checked
   against records that played no part in building it.
6. **What the evidence forbids.** Nulls, refuted priors, a retracted claim, and the bounds.

**What this paper no longer claims:** a validated neighbourhood-scale map for Kandy; a health
burden; that the spatial nulls isolate an information limit.

---

## 2. Section architecture

Target ~30–35 pp. Word budgets are guides, tightened once the target journal is fixed.

| § | title | words | status |
|---|---|---:|---|
| 1 | The problem: modelling where you cannot check | 1,200 | rewrite |
| 2 | Formulation: an information-tiered grey-box decomposition | 2,600 | **major new material** |
| 3 | Design: budget-matched validation across 47 cities | 1,800 | rewrite + expand |
| 4 | The value of information | 2,000 | **new** |
| 5 | Where the model stops, and why | 2,200 | **new — the novel section** |
| 6 | Demonstration: Kandy | 1,800 | condense from existing |
| 7 | What the evidence forbids | 1,600 | condense + de-manifesto |
| 8 | Discussion and conclusions | 1,200 | rewrite |

### §2 — the formulation (the part that answers the reviewer structurally)

Carries the decomposition, **the observation model** (`y_k = H_k[C] + b_k + e_k`, with `σ_rep`),
the budget registry, and P1–P4 with the evidence for each. The observation model is not a
technicality here: it is what lets the paper say which claims rest on the two low-cost sensors
and which rest on satellite and reanalysis. **That is the reviewer's own proposed fix for their
single biggest objection, and the tier structure delivers it by construction rather than by
assurance.**

⚠ **`Bud4` is labelled a declared design assumption, not a validated rung** (F.60/F.61), in
every place it appears.

⚠ The **coherence cap** gets a proper derivation here, not a passing mention. A reviewer read it
as "an ad-hoc patch to force `inc ≥ 0`". The substance is a mass-balance argument — local sources
emit continuously, therefore `B ≤ T` always, therefore a background at or above the total is an
over-estimate rather than a physical state — and it is demonstrably not a tuned knob: **f moves
only 0.477 → 0.502 across a fourfold sweep** of the single free parameter. The reviewer is wrong
on the substance and right that we failed to convey it.

⚠ `A_transport` is stated plainly as **a topographically-steered spatial redistribution filter,
not forward fluid dynamics**, and as **unscored**. Steady-state per hour cannot represent
recirculating valley eddies or multi-hour stagnation; say so in the text rather than waiting to
be told.

### §5 — where the model stops (the novel section)

The section the paper is worth publishing for. Three parts:

1. **The support-scaling result.** Four independent campaigns in one city at four averaging
   supports; monotone collapse; a decay length of order 10² m against a 10³ m grid.
2. **The reattribution.** The five spatial nulls are all scored model-field-against-point-station
   and therefore **share a defect**; five agreeing tests are not five independent confirmations
   when they share one. The attribution splits three ways — sample size (isolated by the
   point-to-point LUR, which fails on its own terms at a median 12 stations/city), change of
   support (measured), and only the residual as an information limit.
3. **What survives operationally.** ρ ≈ 0.2–0.28 stands as an answer to *"can a user rank
   neighbourhoods against what a monitor would read there?"* — no. The number is kept; what it is
   said to measure changes.

This is also the honest answer to the reviewer's third strike (spatial rank fails precisely in
Kandy-like regimes). It replaces a disclaimer with an explanation.

### §6 — Kandy, condensed

Field, the four external point records, **W11 stated as an open discrepancy**, the support ladder
as measured *in this city*. **Cut to the second paper:** exposure weighting, GEMM burden, the
health block, and the detailed acquisition discussion.

---

## 3. Cross-cutting fixes

| | fix |
|---|---|
| **Vehicular share** | "roughly 90 per cent to vehicles" is refuted as a mass share (F.66). Replace with the graded, measured picture (F.71). Draft text in `claims_audit` §3b. |
| **FECT calibration** | soften from "never verified" to "corroborated at one sensor, at the level, not at the shape" (F.64). Draft in `claims_audit` §3c. |
| **Level axis** | qualify while W11 is open. Draft in `claims_audit` §3d. |
| **"No retrievable record"** | narrow to "no continuous retrievable series"; cite the two published point records as external checks — a gain, not a concession. |
| **§7.5 source limitation** | now quantitative: traffic 7.6%, biomass 14.1%, soil 3.8%, sea salt 3.2%. |
| **Transboundary citation** | [Abeyratne2006] is a spatial falsification test, not a passing mention (F.72). |
| **Tone** | strip the aphorisms. Keep the pre-registrations, the nulls and the power bounds; delete the lines that lecture the field. Target: no more than one rhetorical flourish per section, and none in §5. |
| **Build hygiene** | raw `assemble_manuscript.py` markers, broken math operators in §4.1, unformatted vectors in §4.3, and **figure numbering ("Figure 1. Figure 3.")**. Pandoc does not resolve `\ref{}` (gotcha #58) so every number is hardcoded and shifts when a figure moves. **Editors bounce on this — make it a blocking gate before submission.** |

---

## 4. Reuse map — what survives from the 28-page draft

| existing file | lines | disposition |
|---|---:|---|
| `draft_s1_s2_intro.md` | 170 | **rewrite.** Kandy setting shrinks to motivation; the gap statement changes from "no field for a Sri Lankan city" to "no model declares its information budget". |
| `draft_s3_information_bound.md` | 176 | **highest reuse.** Closest to the new spine; feeds §2 and §4. |
| `draft_s4_formulation.md` | 243 | **reuse with a new layer on top** → §2. Add the observation model, the budget registry, P1–P4, the cap derivation. |
| `draft_s5_validation.md` | 131 | **rewrite** → §3. 10 → 47 cities; add the three confounds caught by registered gates; **reframe the spatial estimator honestly** (this is claims-audit item A). |
| `draft_s6_results.md` | 157 | **split.** Ladder → §4; Kandy field → §6. |
| `draft_s7_forbids.md` | 213 | **split.** Spatial material is promoted into §5 and rewritten; the rest condenses into §7 with the tone pass. |
| `draft_s8_s9_discussion.md` | 154 | **rewrite** → §8. |
| `table1.md`, `abstract.md` | — | rewrite last, from the finished body. |

---

## 5. Figures

**Keep and update:** the Kandy field; the protocol diagram (10 → 47 cities); the decomposition
schematic.

**New, in priority order:**

1. 🔴 **The support-scaling ladder** — four campaigns, four supports, monotone collapse. *This is
   the paper's money figure* and it does not exist yet.
2. 🔴 **The budget ladder** — step gain per tier, stratified by band and by instrument class.
3. 🟡 **The three confounds** — what the pooled numbers hid.
4. 🟡 **The paired-site panel** — the botanical garden at 300 m, observation vs model.

**Cut with the health block:** exposure weighting and burden figures.

⚠ Figures are numbered by first appearance of `{{fig:tag}}` tokens; every reorder renumbers
everything downstream.

---

## 6. Phases

| phase | work | gate |
|---|---|---|
| 0 | Freeze the claim set: every numeric claim traced to a ledger entry or a script | no claim without provenance |
| 1 | §2 formulation, including the cap derivation and the observation model | P1–P4 each have stated evidence |
| 2 | §3 + §4 — design and the ladder | the three confounds appear in the text, not just the appendix |
| 3 | **§5** — support scaling and the reattribution | the three-way attribution is explicit |
| 4 | §6 Kandy, condensed; health block excised to the Paper-B stub | W11 stated as open |
| 5 | §1, §7, §8; tone pass | aphorism count per section ≤ 1, zero in §5 |
| 6 | Figures 1–4 new, others updated | every `{{fig:}}` token resolves |
| 7 | Build, then a **mechanical gate**: no raw markers, no broken operators, every figure number correct | zero `??`, zero `Fig.~`, zero `ef{fig` |
| 8 | Target chosen, formatted to house style, abstract and title last | — |

---

## 7. Open decisions

1. **Journal target** — deferred by agreement. My reading: the contribution is a model
   formulation plus its evaluation, with a released implementation and published evidence, which
   is squarely **GMD**'s remit; **ACP** suits it if the paper is pitched as an atmospheric result
   about a real airshed. The rewrite makes it *less* atmospheric and *more* methodological, which
   moves the balance toward GMD — but this should be the supervisor's call and it does not block
   phases 0–6.
2. **Does the support-scaling result stay inside §5, or become a standalone short note?** It
   generalises well beyond this project — any 1 km product scored against point monitors carries
   the same penalty. It is stronger inside the paper as the *explanation* for the ceiling, and
   weaker but more visible alone. Recommend: keep it in, revisit if §5 overruns.
3. **How much Kandy stays.** Current plan cuts exposure, burden and health. If the second paper
   slips, the demonstration may look thin — but padding it re-creates the two-spine problem.
4. **Second-paper stub** — create `paper_b_kandy_stub.md` when the health block is excised, so
   the material is parked rather than orphaned.
