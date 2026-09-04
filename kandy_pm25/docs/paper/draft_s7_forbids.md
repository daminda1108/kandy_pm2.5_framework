# 7. What the evidence forbids

*Condensed and de-manifestoed from the previous §7 per `rewrite_plan_2026-08-22.md`.*

---

A model is characterised as much by what its evidence rules out as by what it supports. This
section collects the negative results, the refuted predictions and the bounds, because each of
them constrains what may be claimed from work of this kind — including by us.

## 7.1 Registered predictions that failed

Every test in §4 and §5 was registered with a refutation criterion before it ran. The outcomes:

| prediction | outcome |
|---|---|
| a finer grid recovers within-city contrast | **refuted** ({{claim:s1.predictions_refuted}}) |
| the dispersion layer improves spatial rank | **refuted** |
| a fused satellite product shows excess skill from leakage | **refuted** ({{claim:c1.predictions_refuted}}) |
| leakage scales with monitor density | **refuted** |
| recirculated local air is the freshest | **refuted** ({{claim:chem.predictions_refuted}}) |
| raw satellite AOD is worth less than the fused product | held ({{claim:c1.predictions_held}}) |
| geography still beats the satellite level on an honest stream | held |
| within-pixel spread exceeds between-pixel spread | held |
| continental air is more secondary-rich than marine | held ({{claim:chem.predictions_held}}) |

Two of the refutations changed conclusions rather than merely failing. The leakage refutation
(§4.5) redirected the search to the rung above, where the effect was large. The recirculation
refutation (§6.4) forced the abandonment of a clean chemical story in favour of a correct
untidy one.

## 7.2 Nulls

**Spatial pattern learning fails, five ways** — a learned-pattern test [@Gordon2020], dynamic
transport, earth-observation embeddings, a full land-use predictor set [@Hoek2008] at
{{claim:lur.total_stations}} stations across the panel, and sub-grid refinement. §5.5 shows these are not five independent confirmations; they share a
defect, and the attribution splits three ways.

**The dilution term is approximately zero.** The fitted exponent on boundary-layer dilution is
{{claim:dilution.exponent}} against 1.0 for pure inverse-BLH behaviour [@Stull1988; @DeWekker2015]. A ~40-fold diurnal swing in mixing depth
produces almost no swing in city-mean concentration, because only the local increment dilutes
while the background is already well mixed. There is consequently no physical dilution component
to peel off and transfer.

**The sub-daily shape does not transfer outside the deep tropics.** Pooled across the panel, a
transferred diurnal cycle is *worse* than assuming no cycle at all. It transfers within the deep
tropics — the demonstration city's own regime — and nowhere else.

**A nearby coastal city is not a usable background donor.** Sri Lanka's only reference-grade
record inside the admissible 30–300 km window is in Colombo, {{claim:donor.colombo_km}} km away,
so if it tracked Kandy the largest rung on the ladder would already be free. It does not. The
daily correlation is {{claim:donor.colombo_r}} ({{claim:donor.colombo_r_rank}} by rank, so this
is not a tail artefact), against a benchmark of {{claim:donor.benchmark_median}} across the
{{claim:donor.pairs}} panel donor pairs and {{claim:donor.benchmark_median_matched}} among the
pairs at comparable separation. It is the weakest pair in its distance band —
{{claim:donor.colombo_rank_in_band}} of the {{claim:donor.benchmark_band_pairs}} matched pairs
score below it.

⚠ Kandy's series is two low-cost sensors while the panel's targets are mostly reference
networks, so its correlation is attenuated by measurement error the comparison pairs do not
carry. Kandy's own between-sensor correlation is
{{claim:donor.kandy_sensor_reliability}}, which is the ceiling any donor could reach; correcting
for it lifts Colombo to {{claim:donor.colombo_r_disattenuated}}. Even on that generous reading
the pair sits below the distance-matched benchmark, which is why we state the conclusion at all.
The central highlands decouple the coast from the interior, and no free substitute for a
regional station exists.

## 7.3 Corrections to our own prior claims

We list these because several are in the published record under our names.

| claim | status |
|---|---|
| "~90% of local PM2.5 is vehicular" | **refuted as a mass share** [@Seneviratne2017], three independent ways; it is a *timing* statement |
| local fraction ≈ 0.25 | **refuted** by a physical constraint; it is ≈ 0.48 (§2.6) |
| "four guaranteed properties" | **two** guarantees, one enforced mechanism, one discharged (§2.4) |
| reference networks gain nothing from added stations | **not supported**; the contrast is {{claim:class.w_bud2_contrast}}×, not infinite |
| a linear model reproduces the ladder | **refuted**; Ridge reports {{claim:learner.ridge_linear.step_bud0c_bud1}}% (§4.4) |
| the panel spans no coastal cities | stale; it spans {{claim:coastal.coastal.n}} |
| an undefined spatial statistic reported as a measured null | corrected to "—" (§3.4) |
| the four-rung support-scaling ladder | **confounded**; support and siting design move together across its rungs |

## 7.4 Bounds on what this design can detect

The spatial nulls exclude only large effects. At 80% power the earth-observation test could
detect partial correlations well above those actually measured, so the null constrains the
effect to be small rather than establishing it is zero.

The deep-tropical cell is {{claim:band.deep_tropical.n}} cities; the subtropical and temperate cells are {{claim:band.subtropical.n}} each. The
instrument-class confound cannot be sampled away at all (§4.6). The demonstration city's external
checks are four point records from three papers, two of which disagree with each other by more
than either disagrees with the model.

## 7.5 What may not be concluded from this work

- That the field is accurate at neighbourhood scale. It is not, and §5 measures by how much.
- That the ladder's pooled ordering is a global recommendation. It inverts by band (§4.2).
- That the transport layer improves the map. It does not (§5.4).
- That the model captures atmospheric chemistry. It contains none; §6.4 is a check *on* the
  decomposition using an external chemical product, not chemistry inside the model.
- That `Bud4` is validated. It is a declared design assumption (§2.3).
- That agreement between this model and another gridded product constitutes validation, where
  both are trained on overlapping ground networks (§4.5).

---

## Drafting notes, to remove before submission

- §7.1's table should be generated from the registered-outcome records rather than typed.
- The dilution exponent and the LUR station count are now tokenised (and the count was 613,
  not the 636 the draft carried).
- Still needing generating scripts: the 93 km / 0.604 / 0.923 donor figures and the
  80%-power bound.
- Check that every "refuted" here is cross-referenced to the section that refutes it.
- Untokenised numbers in this section are inventoried in `TOKENISATION_BACKLOG.md`, which separates external values (correctly cited) from ones this project computed and still types by hand.
