# 6. Demonstration: Kandy

*Condensed from the previous §6 per `rewrite_plan_2026-08-22.md`. Exposure weighting, the GEMM
burden calculation and the health block are excised to the second paper.*

---

Kandy is a city of about 400,000 in a steep valley in the central highlands of Sri Lanka
[@Whiteman2000; @Chemel2016]. Its
monitoring record is two low-cost sensors and a single published year from a research campaign
[@Senarathna2024; @Ileperuma2020].
The city carries a documented respiratory-health burden [@Priyankara2021].
It is the condition the model was built for, and it is a demonstration rather than a validation —
the distinction is maintained throughout.

## 6.1 What the model was given

`Bud1`: reanalysis drivers, static geography, a satellite level, and two low-cost sensors at
different elevations. No reference monitor, no regional background, no spatial network. Every
claim below is bounded by that budget.

The delivered field is hourly at 1 km for 2019–2026, with 2019–2023 satellite-anchored and the
later years a labelled extension tier.

## 6.2 Checks that carry weight, and one that does not

⚠ **The two local sensors cannot validate this model.** The temporal anchor is trained on their
residual and amplitude-sharpened to their observed swing, so agreement with them measures the
calibration, not skill. We report the comparison for the shape it carries and label it in-sample.

Four independent point records exist, recovered from the literature rather than collected:

| record | instrument | observed | model | difference |
|---|---|---:|---:|---:|
| NBRO Kandy, 2021 [@Nirmani2025] | undocumented | 19.6 | 19.74 | **+0.7%** |
| NBRO Kandy, 2022 [@Nirmani2025] | undocumented | 22.7 | 22.11 | **−2.6%** |
| calibrated low-cost, 2022–24 | LCS, BAM-anchored | 19.49 | 25.01 | +28% |
| research sensor, full record | LCS | 17.8 | — | corroborates a BAM-anchored ~18–19 [@Dhammapala2022] |

The first two are the strongest external check the model has, and they are genuinely
out-of-sample: the pixel sits 15.6% above the basin mean, and that lift is imposed physics never
fitted to any Kandy station.

🔴 **We do not resolve the discrepancy, and we decline to.** Three of four records sit below the
model and one matches. The three low ones are all low-cost sensors carrying a downward
calibration; the one that matches has an undocumented instrument. There is no basis in these
data for preferring either, and choosing the record that agrees would be the least defensible
move available. **It is reported as an open discrepancy on the axis this work otherwise calls
strong**, and it is the single clearest argument for the acquisition in §6.5.

## 6.3 What the field says

Basin annual means run {{claim:kandy.mean_min}} to {{claim:kandy.mean_max}} µg m⁻³ across 2019–2023, above the WHO annual guideline
throughout [@WHO2021]. The seasonal maximum falls in the inter-monsoon, not in a burning season — Kandy has
none; the elevated season is associated with long-range transport [@Abeyratne2006; @Jayalath2023]. The diurnal cycle is bimodal with rush-hour peaks and, counter-intuitively, a **midday
minimum** rather than a nocturnal one: the deep-night hours run about 15% above the midday
trough, which the model reproduces and which we flag because it inverts the expectation for a
valley city.

The local fraction is derived in §2.6: **{{claim:partition.f}}** of the annual mean is generated
inside the basin, the remainder arriving as regional background.

## 6.4 A chemical check on the decomposition's premise

The decomposition asserts that `B` is transported and the increment is local. That is its
load-bearing physical claim and it had never been tested against composition.

{{fig:chemistry}} classifies days by back-trajectory sector — independent of the chemistry — and takes the
secondary fraction (sulphate, nitrate, secondary organics: species that form over hours to days
and therefore mark aged air) from a composition reanalysis [@Keller2021]:

| air-mass origin | secondary fraction |
|---|---:|
| Indian Ocean, south-west | {{claim:chem.sec_frac.SW_marine}} |
| local recirculation | {{claim:chem.sec_frac.local_recirc}} |
| Bay of Bengal | {{claim:chem.sec_frac.BoB_marine}} |
| peninsular India | {{claim:chem.sec_frac.Penin_India}} |
| Indo-Gangetic Plain | **{{claim:chem.sec_frac.IGP_E_India}}** |

Continental-Indian air is measurably more secondary-rich than marine air (0.410 against 0.365,
p = 3.1 × 10⁻⁹), and the ordering runs the way the decomposition requires. **This is the first
chemical support the formulation has had**, and it comes from a direction — composition — that
none of its other evidence uses.

⚠ Two qualifications. The registered prediction that recirculated local air would be the
*freshest* was **refuted**: it is not, because stagnation gives local precursors time to age in
place. So *"local increment = fresh primary"* is too simple, and the decomposition partitions
correctly by origin without the clean chemical story we expected. And the composition product is
a model at ~25 km, so it corroborates or contradicts; it cannot validate.

🟢 One incidental result carries weight beyond this section. The organic-to-black-carbon ratio
exceeds {{claim:chem.oc_bc_min_monthly}} in every month, against ~1–2 for traffic-dominated
aerosol. That is a biomass-burning signature, and it is the third independent line — after a
local source-apportionment study [@Seneviratne2017; @Hopke2016] and the absence of any
correlation with the satellite NO₂ column [@Veefkind2012]
— refuting the "predominantly vehicular" characterisation this city has carried in the
literature and in our own earlier work.

## 6.5 What one instrument would change

The ladder gives a quantitative answer for this city, and it is not the one the pooled result
would suggest.

| acquisition | expected RMSE reduction |
|---|---:|
| two local stations | **{{claim:maiac.deep_tropical_first2}}%** |
| a regional background station | {{claim:maiac.deep_tropical_background}}% |
| stations three to eight | ≈ {{claim:step.bud1_bud2}}% |

Local stations are worth **{{claim:maiac.deep_tropical_local_advantage}}×** the regional
background here — the inverse of the pooled recommendation, because Kandy sits in the band where
the ordering flips (§4.2). A reference monitor in Kandy would additionally close §6.2's
discrepancy and make `b_k` estimable for the first time (§2.2), moving the city from `Bud1` to
`Bud2`.

We state this as the paper's practical recommendation for this city, with the caveat that it
rests on a 13-city band.

---

## Drafting notes, to remove before submission

- Still wanted: a study-area map and the Kandy field panel. The 2026-08 `F_cycles` figure
  predates the current field build by a day and must be regenerated before reuse, not assumed.
- Annual means and the local fraction are now tokenised.
- ⚠ The 400,000 population and the WHO guideline are EXTERNAL values and stay as cited text.
- Still needing generating scripts: the 15.6% pixel lift and the midday-trough ratio.
- The four external records need their citations attached; two are 2025 papers.
- Cross-check §6.3's local fraction sentence against §2.6 so the number appears once, not twice.
