# Pre-registration — a chemical test of the decomposition's load-bearing claim

**Drafted 2026-09-01, before any directional test is scored.** Companion to
[`prereg_subgrid_and_streams_2026-09-01.md`](prereg_subgrid_and_streams_2026-09-01.md)
(OSF [`bkpyr`](https://osf.io/bkpyr/)).
**OSF: [`kx23c`](https://osf.io/kx23c/)** — registered 2026-09-01T22:55:44Z, Open-Ended
Registration, project [`zvqp4`](https://osf.io/zvqp4/).

> **How OSF approval works — no action is required.** A new registration sits at
> `pending_registration_approval` for **48 hours**, and per OSF's own documentation *"after 48
> hours, the submission will automatically be approved"*. **The window is a CANCELLATION window,
> not an approval requirement**: if every admin does nothing, the registration goes public by
> itself. Acting early is possible only through the notification email's Approve / Cancel
> buttons — there is no dashboard equivalent — and rejecting returns the registration to draft
> for editing and resubmission.
>
> This one auto-approves at **2026-09-03 22:55 UTC**.
>
> ⚠ The scientific value does not depend on approval. What makes a pre-registration meaningful
> is the **timestamp**, and that is fixed at creation, so tests scored against this document are
> properly pre-registered whatever happens at the deadline.

---

## 1. The claim under test, and why it has never been tested

The production model is `PM = B(t) + local increment`, where `B` is asserted to be the
**regional / transboundary background** and the increment **local**. That assertion is the
load-bearing physical claim of the entire formulation. Every support it has is statistical — a
rural-satellite floor, the F.43 coherence cap, a source-apportionment prior, an NBRO
corroboration of its *level*. **Nothing has ever tested whether the two terms are chemically
what the model says they are.**

Composition can, because aged and fresh aerosol differ:

| | species | timescale | what it marks |
|---|---|---|---|
| **secondary** | sulphate, nitrate, secondary organic | hours to days | an **aged, transported** air mass |
| **primary carbonaceous** | black carbon, primary organic carbon | emitted directly, short-lived | **local, fresh** combustion |

Data pulled and on disk: `data/processed/decomp/kandy_geoscf_speciation_daily.csv` — GEOS-CF
v1 replay, 7 species, **1,826 days, 2019–2023, no gaps**.

---

## 2. 🔴 The circularity that rules out the obvious test

The obvious test is *"does `B(t)` track the secondary fraction?"*. **It is inadmissible.**

`build_additive_field_v2.py` builds `B` via `geoscf_daily_shape` — **`B`'s seasonal shape comes
from GEOS-CF**, and so does the speciation. Correlating them would measure GEOS-CF's internal
consistency and return a confident, meaningless positive. This is exactly the C1 defect (a
stream presented as independent that is not) and it is recorded here **before** running, not
after.

**The admissible test uses an independent classifier of air-mass origin.**
`data/processed/decomp/w2/d1_trajectories_850.parquet` holds 11,676 back-trajectory arrivals
classified into sectors — `BoB_marine` (4,330), `SW_marine` (3,382), `other` (2,628),
`local_recirc` (687), `Penin_India` (492), `IGP_E_India` (157). Sector is derived from
trajectory geometry, **not** from GEOS-CF chemistry.

⚠ Independence is **partial, not complete**: GEOS-CF's chemistry runs on its own meteorology,
which is related to the trajectories. What is *not* shared is the **chemical** prediction — that
continental Indian air should be secondary-rich is an atmospheric-chemistry claim, not a
meteorological one. Stated so the result is not over-read.

---

## 3. Registered predictions

Scored on daily secondary fraction `sec = (SO4 + NO3 + SOA) / (SO4 + NO3 + SOA + BC + OC)`.

| # | prediction | refuted if |
|---|---|---|
| **C-H1** | `sec` is **higher on continental-Indian arrival days** (`Penin_India`, `IGP_E_India`) than on marine days (`BoB_marine`, `SW_marine`) | continental ≤ marine |
| **C-H2** | `sec` is **lowest on `local_recirc` days** — recirculated local air is freshest | `local_recirc` is not the minimum among sectors |
| **C-H3** | the continental–marine gap is **larger in DJF–MAM** than in JJA, matching the seasonal transboundary picture (W2) | no seasonal modulation of the gap |
| **C-H4** | **OC/BC stays high (> 5) year-round**, a biomass-burning rather than traffic signature, corroborating F.66 independently of the PMF study | OC/BC ≤ 5, i.e. traffic-like |

**Descriptive, already computed, NOT a test:** mean composition 2019–2023 is organic carbon
55.4%, nitrate 14.8%, secondary organic 13.0%, sulphate 9.5%, black carbon 4.0%, dust 2.4%,
sea salt 0.8% — secondary **37.3%**, primary carbonaceous **59.4%**, **OC/BC 13.8**. The
secondary fraction peaks Jan–Mar (0.41) and troughs Jun–Sep (0.31). These are reported as
description; C-H1–C-H4 are what get scored.

**Analysis.** Per-sector medians with bootstrap intervals; Mann–Whitney for the
continental-vs-marine contrast, reported with n per sector. ⚠ `IGP_E_India` has **n = 157
arrivals** and `Penin_India` **n = 492**, against 7,712 marine — the continental cells are small
and the test is correspondingly weak. **Said in advance**, per gotcha #74 and the standing rule
to check n before believing a comparison.

---

## 4. What each outcome licenses, and what it does not

🟢 **If C-H1 and C-H2 hold:** the decomposition's terms are *chemically consistent* with what
the model calls them. That is corroboration from a direction the project has never used, and it
is the strongest available support for the additive form's physical interpretation.

🔴 **If they are refuted:** the background and the increment are not chemically distinguishable
by origin, and the model's physical story is weaker than its statistics suggest. **This is the
more informative outcome** and it must be reported as prominently as the alternative.

⚠ **What no outcome licenses.** GEOS-CF is a **model** at ~25 km, not an observation. It cannot
*validate* the decomposition — it can corroborate or contradict it. Its bands are `RH35` dry
reference, so these are composition **shares**, never ambient masses, and must never be compared
to a wet observation as a level. And a 25 km cell cannot resolve the within-basin increment at
all: this tests the **temporal** claim about air-mass origin, not the **spatial** claim about
where the local increment sits.

⚠ **The honest ceiling on the whole exercise.** Confirming that transported air is secondary-rich
would be unsurprising atmospheric chemistry. Its value here is not novelty — it is that the
decomposition has never been checked against anything chemical, so a *contradiction* would be a
genuine finding and a confirmation removes a standing "never tested" from the limitations list.
Do not oversell a positive.

---

## 5. Two hypotheses already closed, recorded so they are not re-run

- 🔴 **The hygroscopic explanation for W11 is refuted by inspection.** LCS optical sensors
  over-read at high humidity, which would explain three of four Kandy point records sitting
  below the model. The data says the opposite: observed PM2.5 **rises as it gets drier** at both
  FECT sensors (Akurana 14.30 → 18.70, Hantana 8.14 → 12.69 across humidity quintiles). Wet
  scavenging and monsoon air masses dominate the humidity signal; there is no instrument
  artefact to find. **W11 stays open.**
- 🔴 **PM2.5 at Kandy does not track the NO₂ column.** r = **+0.084** restricted to hours within
  1 h of the TROPOMI overpass (n = 726), +0.104 within 3 h — so it is not overpass-staleness
  attenuation. Local combustion NO_x and PM2.5 are **decoupled**, independent support for F.66.
