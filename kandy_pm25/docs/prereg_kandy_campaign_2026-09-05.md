# Pre-registration — the Kandy measurement campaign

**Registered 2026-09-05, before deployment and before any campaign observation exists.**

Unlike the two registrations lodged earlier today, **this one is genuinely blind**: the
instruments have not been bought, the sites have not been visited, and there is no data to have
peeked at. The design is fixed in
`data/processed/decomp/sensor_design_kandy.csv`; the power calculation is
`scripts/campaign_power.py` → `campaign_power.json`; the design rationale is
`docs/sensor_placement_plan_2026-09-05.md` and thesis section 9.7.

---

## 0. The finding that changes the campaign, and it arrived before deployment

The campaign was conceived to answer one headline question: **is the spatial ceiling a sampling
artefact rather than an information limit?** Six searches for within-city spatial structure have
returned nulls, and every network they used was a convenience sample. A deliberately contrasted
network was supposed to settle it.

**The power calculation says this campaign cannot settle it, and the calculation was run before
any money was committed.**

To beat the benchmark of rho = 0.309 that a single free raster already achieves, with 18 sites
available to fit a spatial pattern, the campaign would need to reach rho between 0.61 and 0.78
depending on how strongly the campaign-informed pattern correlates with the benchmark predictor.
That is a required gain of **+0.30 to +0.47**. The 46-city panel study this campaign is meant to
follow up resolved a gain of **0.130**.

**Matching that in one city would need between 96 and 304 fitting sites**, against the 18
proposed and the 12 at which the design's representativeness stops improving. Those are different
criteria answering different questions, and the campaign satisfies the second, not the first.

Three consequences are registered rather than discovered later.

**H1 is demoted to exploratory before the campaign runs.** It will be computed and reported with
its bound attached, and it may not be described as a test of the ceiling under any outcome.

**The campaign must not be proposed, funded or written up as resolving the spatial question.**
Doing so would repeat, with instruments and money, the exact error this project has already
documented: an experiment that cannot see the effect it is looking for, reporting its silence as
evidence.

**What the campaign is well powered for is the physics and the level**, and those become the
confirmatory set. That is a smaller claim than the campaign began with and it is the one the
design can actually support.

---

## 1. The design, fixed before registration

| stratum | sites | role |
|---|---:|---|
| A anchor | 1 | reference-grade; calibrates the network |
| B design | 12 | spans emission and flow physics |
| C paired | 9 | 3 triplets, 0/100/300 m, inside single cells |
| E vertical | 5 | 8 to 291 m above the local valley floor |
| D receptor | 8 | **held out of all model fitting** |

Sites available to fit a spatial pattern: **18** (A, B, E). The paired offsets are within-cell
replicates rather than independent locations. The receptor stratum is held out by design.

---

## 2. Confirmatory hypotheses

### C1. The within-cell distribution exceeds the model's

**The best-powered test in the campaign, and it reports within weeks.**

The model's fine surface predicts a within-triplet contrast of **1.58 times**. The one existing
Kandy observation at 300 m separation suggests **27.5 times**. The two hypotheses are separated by
more than an order of magnitude.

Averaging 168 hours resolves a ratio to about a factor of **1.044**; 720 hours to **1.021**.

- **Held** if the observed within-triplet ratio exceeds 1.58 by more than the resolution at the
  hours actually collected, in at least 2 of 3 triplets.
- **Refuted** if the ratio is at or below 1.58 within that resolution.
- This test cannot fail for want of power. If it returns nothing, that is a result about Kandy.

### C2. Nocturnal drainage produces a down-valley concentration maximum

The model predicts a nocturnal sink down-valley of the core. **No instrument has ever tested it.**

A sign test over paired site-nights, where the unit is the **night** and not the site, which is
why this is the second-best-powered test in the design. With 90 nights the sink must read higher
on **63.1 per cent** of them; with 365 nights, **56.5 per cent**.

- **Held** if the down-valley site exceeds the core site on more nights than that threshold,
  for the number of nights actually collected.
- **Refuted** if it does not, or if the sign runs the other way.

### C3. The delivered field's level is consistent with a reference instrument

The open discrepancy: three of four independent Kandy point records sit below the model and one
matches, and the one that matches carries an undocumented instrument.

- **Held** if the annual mean at the anchor cell falls within the model's delivered interval.
- **Refuted** if it falls outside, in which case the direction is reported and the level chapter
  is rewritten rather than the record discounted.
- Registered in advance: **if the reference reads below the model, the three low-cost records
  were right and the model reads high.** That outcome is not to be explained away by preferring
  the record that agrees, which is the failure mode the thesis names.

---

## 3. Exploratory, reported with bounds and never as confirmatory

### E1. Spatial rank against the benchmark  *(demoted; see section 0)*

Rank correlation of a campaign-informed pattern against held-out sites, compared with the
benchmark rho = 0.309.

**Reported with the detection limit stated beside it in every instance.** At 18 fitting sites,
only a gain of +0.30 or larger is detectable, so any smaller result is *undetectable at this
power* and not evidence of absence. A result exceeding the limit would be a strong finding and
would still require replication, because a single city cannot establish it.

### E2. The vertical gradient

Concentration against height above the local valley floor, 5 transect sites. **The detection
limit is |rho| >= 0.942**, so only a nearly perfect monotone relationship is visible. This is
registered as exploratory for that reason and is not a test of the confinement term.

⚠ Adding transect sites is the cheapest way to make this confirmatory in a later campaign, and
that is noted here so the option is visible rather than rediscovered.

---

## 4. Analysis, fixed now

1. Per-device calibration from the pre-deployment co-location; drift from the post-recovery
   co-location. A unit recovered without a closing co-location has its record **flagged, not
   corrected by assumption**.
2. Humidity logged with every measurement and used in the calibration.
3. Hourly resolution retained throughout. Daily means destroy the diurnal structure that
   distinguishes local traffic from regional background.
4. All tests are one-sided in the registered direction. A result in the wrong direction is
   reported as such and never as a two-sided success.
5. The receptor stratum enters no model fit. It is used for exposure reporting and as an
   out-of-sample check.
6. Every site that fails its ground visit is replaced by **the nearest candidate cell in the same
   covariate stratum**, never by the nearest convenient building, and every substitution is
   logged with its reason.

---

## 5. What would make this registration void

Stated so that a reader can check rather than trust.

If the campaign collects fewer than 3 paired triplets or fewer than 30 usable nights, C1 and C2
lose their stated power and must be reported as underpowered rather than as nulls.

If the anchor is not secured, **the campaign should not proceed as designed**. Every low-cost
record depends on it, and 34 uncalibrated units measure 34 unknown offsets.

If sites are relocated for convenience rather than within-stratum, the design's coverage claim no
longer holds and the analysis reverts to the exploratory tier throughout.

---

## 6. What this campaign cannot do

It cannot settle the spatial question, for the reason in section 0.

It cannot narrow the intervention bound of 9.1 to 48.3 per cent, which needs filter sampling and
chemical analysis rather than optical particle counters.

It under-samples residential biomass burning, because the design stratifies on a road-centrality
surface while burning is 14.1 per cent of measured mass against traffic's 7.6.

And it says nothing about outdoor workers, who are among the most exposed people in the city and
have no fixed location.
