# Literature positioning — where this work actually sits

Written 2026-08-23, after Dr. Ranatunga's steer to focus the paper on the final model.
Companion to `rewrite_plan_2026-08-22.md` and `novelty_and_figures_2026-08-22.md`.

The method is **not new**, and the paper is stronger for saying so plainly. What follows is the
lineage, the gap, and the defensible claim in each of five strands.

---

## 1. The decomposition lineage — our direct ancestor

**Lenschow et al. (2001), *Atmos. Environ.*, "Some ideas about the sources of PM10", Berlin.**
The canonical three-level split: **regional background + urban background increment + local
traffic increment**, obtained by differencing a rural site, an urban background site and a
kerbside site. Found ~50% of Berlin's urban background PM10 to be long-range transport, and
kerbside up to 40% above urban background. The method has been applied across European cities
ever since and is the standard framing for "urban increment".

**Our model is a Lenschow decomposition.** Say so in the first paragraph of the formulation —
claiming novelty for the split would be false and a reviewer would catch it instantly.

🟢 **The defensible difference, and it is a real one:**

> Lenschow's decomposition is a **measurement protocol**: it *requires* a monitor at each level —
> rural, urban background, kerbside — and returns the split by subtraction. Ours **reconstructs**
> the same decomposition where those monitors do not exist, from globally available fields, and
> **declares what it needed to do so**.

That is the sentence. Lenschow needs three monitors sited by design; we need between zero and
two, sited wherever they happen to be. The novelty is not the decomposition — it is performing it
under a **declared and validated information budget**.

## 2. Monitoring network design — the field our main result speaks to

**"Optimal design of air quality monitoring networks: a systematic review"** (*Stoch. Environ.
Res. Risk Assess.*, 2022) surveys the field from statistical/geostatistical methods through
heuristic and evolutionary optimisation, and states the gap explicitly:

> 🔴 **"there is a lack of rigorous methods to determine the *number* of monitoring sites"**

The literature overwhelmingly optimises **placement given a number**. The number itself is
asserted — "small and medium-size urban areas may only require one monitoring station" — rather
than measured.

🟢 **This is the single most useful finding of the search.** Our budget ladder measures the
**marginal skill of the nth station across 47 cities in 32 countries**, which is precisely the
stated gap, from a recent review we can cite. It converts our result from "an interesting
sensitivity analysis" into "an answer to a question the field has named and not solved".

No precedent was found for measuring skill as a function of station count across a multi-city
panel. That absence is consistent with the review's own statement of the gap.

## 3. LUR transferability — context for the spatial axis

Well-established and consistent with what we measured:

- **Direct transfer** of a LUR to a new city causes a **significant** performance drop;
  **recalibrated** transfer drops only minor-to-moderately.
- London ultrafine particles: transferred MSE-R² **−18 to 0** uncalibrated; **21–41%** when
  recalibrated locally.
- European multi-city (ESCAPE-family): within-area median R² **59/48/70%**; transferred
  **59/42/67%**.

🟢 **Our contribution here is not the failure — it is the diagnosis.** The literature reports the
drop and attributes it to differing predictor–outcome relationships between cities. We add a
**change-of-support** explanation, measured in the target city: a paired site 300 m apart inside
one 1 km pixel reads **27.5×** in observation and **1.000×** in the model. That reframes part of
the transfer penalty as a **definitional** limit rather than a modelling one, and it applies to
every 1 km product scored against point monitors.

⚠ Do not overclaim: our R2 test also showed a genuine **sample-size** limit (median 12
stations/city against 40–80 in published LUR designs). Both mechanisms operate.

## 4. Satellite PM2.5 in data-scarce regions — where the level anchor comes from

van Donkelaar and colleagues' CTM-based approach exists **precisely because** statistical
satellite–PM2.5 models need dense ground data and therefore fail "in vast regions outside
developed countries". Their global 1 km product is the level anchor in our chain.

⚠ **A reported tendency worth flagging against W11:** satellite-derived PM2.5 estimates "tended
to be slightly **lower** than ground-level readings". Our model reads **high** against three of
four Kandy point records. The directions disagree, which strengthens the case for reporting W11
as open rather than resolving it.

## 5. Physics-informed / hybrid ML for air quality — a crowded field we should not enter

Very active and dominated by architecture papers: CNN-LSTM hybrids, wavelet-CNN-BiLSTM stacks,
physics-informed multimodal frameworks, bio-inspired transfer for data-sparse cities. Almost all
are **forecasting** papers competing on skill.

🟢 **We should explicitly not compete here, and should say why.** Our grey-box is deliberately
simple, and **a Ridge regression reproduces our headline ladder** (F.81: 24.2% vs 23.6%). In a
literature crowded with unfalsifiable deep-learning claims, demonstrating that the result does
**not** depend on model capacity is a differentiator, not a weakness. It also makes the finding
about **information**, which is what the paper is about.

---

## 6. The resulting claim, in one paragraph

> The urban-increment decomposition is standard and dates to Lenschow (2001), but it has always
> been a measurement protocol requiring a purpose-sited network. We reconstruct it where that
> network does not exist, from globally available fields, under an information budget that is
> declared rather than assumed — and we measure what each increment of observation is worth
> across 47 cities in 32 countries, which the network-design literature has identified as an open
> problem. We report where the method stops: a change-of-support limit on spatial skill, and a
> pre-registered failure at a coastal city outside the regime the panel sampled.

## 7. Reconciling with "focus on the paper on the final model"

Dr. Ranatunga's steer and the measurement framing are **compatible**, and the reconciliation is
this:

> The paper is about the model. **The model's defining property is that it declares what it
> needs.** The 47-city ladder is not a separate contribution competing with the model — it is the
> evidence that the declaration is true, and the reason the model is worth publishing rather than
> being one more PM2.5 estimator.

So: model in the title, model in the formulation, model as the deliverable — with the budget
ladder as its validation and its distinguishing feature, not as a rival subject.
