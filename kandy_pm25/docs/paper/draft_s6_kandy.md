# 6. The model at Kandy

Sections 2 to 5 described a construction, measured what each stream of information is worth to
it, and established where it stops. This section runs it. Kandy is not a case study appended to
a methods paper; it is the configuration the construction was designed for — a city with two
low-cost sensors, no reference monitor, no regional background station and no spatial network —
and it is therefore the place where the budget argument either delivers a usable field or does
not. We show the field, we show it across the two axes it is supported on, we show it under the
conditions that matter most, and we then set against it every external check that exists,
including the ones that disagree.

## 6.1 The city, and what the model was allowed

Kandy sits on the floor of a steep valley in the central highlands of Sri Lanka, a city of about
400,000 in a basin closed to the south by the Hantana range and venting to the north-west along
the Mahaweli corridor. The geometry matters to the formulation and not only to the narrative:
the confinement term of §2.1 is a function of height above the local drainage floor, so a basin
with {{claim:kandy.relief_m}} m of relief across 15 km gives that term something to act on, and the ventilation
corridor gives the model a physical reason to place its minimum where it does. The city's
monitoring record is two low-cost sensors and a single published year from a research campaign
[@Senarathna2024; @Ileperuma2020], against a documented respiratory-health burden
[@Priyankara2021]. {{fig:studyarea}} shows the setting with no model output on it at all —
terrain, drainage and settlement only — because everything that follows is a claim about this
domain and a reader should be able to see the domain before seeing a claim about it.

The budget is `Bud1`: reanalysis drivers, static geography, an annual satellite level, and two
low-cost sensors at different elevations. No reference monitor, no regional background, no
spatial network. Every statement in this section is bounded by that, and the tier is stated
rather than implied so that a reader can locate each result on the ladder of §4. The delivered
field is hourly at 1 km for 2019–2026, with 2019–2023 satellite-anchored and the later years
carried as a separately labelled extension tier.

## 6.2 The delivered field

The first thing to establish is what the model actually produces, because a decomposition can be
described correctly and still deliver a field that does not look like anything. {{fig:field}}
shows the annual-mean surface, the local increment on its own, and the partition between them.
Three things in it are worth stating carefully. The total field is smooth: a factor of
{{claim:kandy.contrast_maxmin}} separates its highest cell from its lowest across the whole
domain, which is a small contrast for a city with this much relief, and §5 is the explanation
for that rather than an excuse for it — the sharp structure is real but it lives below 1 km. The
increment panel is where all of the spatial information in the model sits; the background is
spatially uniform by construction, so removing it removes nothing structural and leaves exactly
the component a local intervention could act on. And the partition panel carries a number that
moved: with the regional background at {{claim:kandy.background_annual}} µg m⁻³ against a basin
mean of {{claim:kandy.mean_max}}, roughly half of the annual mean is generated inside the basin.
An earlier construction of the background, which allowed the regional term to exceed the total
on some hours, put this near a quarter. Imposing the physical constraint that local sources
cannot emit negatively — §2.6 — is what moved it, and the constraint is not a tuning choice.

Basin annual means run {{claim:kandy.mean_min}} to {{claim:kandy.mean_max}} µg m⁻³ across
2019–2023, above the WHO annual guideline throughout [@WHO2021]. The local fraction is
{{claim:partition.f}}, derived in §2.6 and not fitted here.

## 6.3 The field across the two axes it is supported on

A single annual mean hides the two things this model is actually for. Section 4 established that
the level and the seasonal cycle are the well-supported axes and §5 established that the fine
spatial pattern is not; the field should therefore be read across time, where it carries
information, rather than across space at a single instant, where it carries less than a reader
would assume. {{fig:spatiotemporal}} puts both temporal axes side by side on the same product.
The seasonal row spans a factor of {{claim:kandy.season_swing}}, from
{{claim:kandy.season_djf}} µg m⁻³ in the stagnant north-east monsoon down to
{{claim:kandy.season_jja}} in the ventilated south-west — and the maximum falls in the
inter-monsoon and the north-east monsoon rather than in any burning season, because Kandy has
none; the elevated season is associated with long-range transport [@Abeyratne2006;
@Jayalath2023]. The diurnal row spans {{claim:kandy.phase_swing}} and resolves both traffic
peaks, {{claim:kandy.phase_morning}} µg m⁻³ in the morning window and
{{claim:kandy.phase_evening}} in the evening.

Two features of that figure are easy to misread and both are worth stating explicitly. The
ventilated panels — the south-west monsoon, and midday — look almost uniform. That is a property
of the model rather than of the rendering: in an additive decomposition the entire spatial
pattern is carried by the increment, so when the total falls towards the background the
structure goes to zero with it, and a ventilated hour genuinely is close to spatially flat. And
the diurnal minimum is at **midday**, not at night: deep night runs a factor of
{{claim:kandy.night_over_midday}} above the midday trough, at
{{claim:kandy.phase_night}} against {{claim:kandy.phase_midday}} µg m⁻³. This inverts the
expectation for a valley city, where nocturnal drainage and a collapsed boundary layer are
usually assumed to give the daily maximum. We flag it because our own earlier documentation
described the deep night as the daily minimum, and that error caused a correct model behaviour
to be read as a defect for several months.

## 6.4 The regime the model is for

The annual and seasonal views understate the case, because the operational value of a field like
this is concentrated in the small number of hours when the air is worst and nobody is measuring.
{{fig:episode}} takes the December 2022 stagnation episode: the field at its peak hour, and the
basin-mean trace across 48 hours against the WHO 24-hour interim target. The episode reaches
{{claim:kandy.episode_peak}} µg m⁻³ at its peak with a 48-hour mean of
{{claim:kandy.episode_mean}}, and it is reproduced with no local observation of the episode
itself: the conditions that produce it — a shallow boundary layer, weak flow, and an advected
regional load — are all present in the reanalysis drivers, which is precisely the mechanism the
`Bud0` rung is built on. This is also where the model's interval is widest, and the reader
should hold that alongside the peak value rather than after it.

⚠ One qualification belongs with this figure and not in a limitations list. A driver-anchored
tier of this kind reproduces **how often** episodes occur and not reliably **when** a particular
one occurs; the episode shown is anchored in a year the satellite level constrains, and we do
not claim event-level timing skill.

## 6.5 What can be used as a check, and what cannot

The two local sensors cannot validate this model, and the reason is structural rather than a
matter of degree: the temporal anchor is trained on their residual and then amplitude-sharpened
to their observed swing, so any agreement with them measures the calibration and not skill.
{{fig:cycles}} shows that comparison anyway, at seasonal correlation
{{claim:kandy.cycles_seasonal_r}} and diurnal {{claim:kandy.cycles_diurnal_r}}, and it is
labelled in sample on its face. It earns its place for two reasons. A reader is entitled to see
that the calibration took, since a fitted model that fails to reproduce its own fitting target
has a different problem. And these numbers must never be differenced against an out-of-sample
correlation to produce an apparent improvement, which is an error this project made once and
records so that a reader can check we are not making it here.

The checks that do carry weight were recovered from the literature rather than collected. Four
independent point records exist for this city:

| record | instrument | observed | model | difference |
|---|---|---:|---:|---:|
| NBRO Kandy, 2021 [@Nirmani2025] | undocumented | 19.6 | 19.74 | **+0.7%** |
| NBRO Kandy, 2022 [@Nirmani2025] | undocumented | 22.7 | 22.11 | **−2.6%** |
| calibrated low-cost, 2022–24 | LCS, BAM-anchored | 19.49 | 25.01 | +28% |
| research sensor, full record | LCS | 17.8 | — | corroborates a BAM-anchored ~18–19 [@Dhammapala2022] |

The first two are the strongest external check the model has and they are genuinely
out-of-sample: the pixel concerned sits 15.6% above the basin mean, and that lift is imposed
physics never fitted to any Kandy station.

🔴 **We do not resolve the discrepancy between them, and we decline to.** Three of the four
records sit below the model and one matches it. The three low ones are all low-cost sensors
carrying a downward calibration correction; the one that matches has an undocumented instrument.
There is no basis in these data for preferring either, and selecting the record that agrees
would be the least defensible move available to us. It is reported as an open discrepancy on the
axis this work otherwise calls its strongest, and it is the clearest single argument for the
acquisition in §6.9.

## 6.6 The same construction, out of sample

Kandy cannot test its own model, so the transferable question — does this construction work
where it was not fitted — has to be asked somewhere else. {{fig:kathmandu}} does it at
Kathmandu, a city with a dense enough network to be scored properly and one the model was never
built for. It is given two stations, matching Kandy's budget exactly, and scored against the
{{claim:ktm.scored_stations}} withheld. The seasonal cycle reproduces at
{{claim:ktm.seasonal_r}} and the diurnal at {{claim:ktm.diurnal_r}}, with a level bias of
{{claim:ktm.level_bias_pct}} per cent — and this is the out-of-sample counterpart to the
in-sample comparison two subsections above, which is why the two are reported in the same
section rather than in separate ones where the distinction could blur. ⚠ Kathmandu is the
panel's most favourable city and is shown as such, not as typical.

The panel behind that single city is the honest version. {{fig:scorecard}} scores all
{{claim:scorecard.cities}} cities on four axes against withheld monitors, and it is the figure
that most constrains what this paper is allowed to claim. The level transfers everywhere, with a
median bias of {{claim:scorecard.level_bias_median}} per cent and a worst case of
{{claim:scorecard.level_bias_hi}}. The seasonal cycle transfers everywhere, from
{{claim:scorecard.seasonal_r_lo}} to {{claim:scorecard.seasonal_r_hi}}. The diurnal cycle does
**not**: it runs from {{claim:scorecard.diurnal_r_lo}} to {{claim:scorecard.diurnal_r_hi}}, and
the failures are not scattered — they are outside the deep tropics, so this is a regime
statement and not an average one, which is why no pooled diurnal number appears anywhere in this
paper. The fine spatial rank is estimable in {{claim:scorecard.spatial_estimable}} of the ten
cities, with a median of {{claim:scorecard.spatial_rho_median}} and a best of
{{claim:scorecard.spatial_rho_hi}}; Kathmandu, the showcase city, scores
{{claim:scorecard.kathmandu_spatial_rho}} on this axis. The tenth city is blank because the rank
could not be computed at its sample size, and a blank cell is not a measured zero — an earlier
draft of this work described that city's spatial skill as vanishing, which was a description of
a missing value.

## 6.7 Uncertainty: width is not the same as centring

A calibration failure is usually reported as a single coverage number, and a single coverage
number is almost always the wrong diagnosis. {{fig:uncertainty}} decomposes ours. The nominal 90
per cent interval covers {{claim:kandy.cov90}} per cent of sensor hours, which on its face says
the intervals are too narrow and should be widened. They should not. The misses are one-sided —
{{claim:kandy.miss_below}} per cent of hours fall below the lower bound against
{{claim:kandy.miss_above}} per cent above — with a median offset of
{{claim:kandy.median_offset}} µg m⁻³, and removing each sensor's own median offset while
changing nothing whatever about the width restores coverage to
{{claim:kandy.cov90_recentred}} per cent. The width was right and the centring was wrong.

That is not a repair, it is a diagnosis, and it points at the observation operator of §2.2: the
model reports an areal mean over a 1 km cell and the sensor samples a point inside it, so a
systematic per-sensor offset is expected and has to be carried as a parameter rather than
absorbed into the interval. Widening the interval to cover it would have produced a
well-calibrated model that was wrong for a stated reason, and would have hidden the change of
support that §5 spends its length establishing.

## 6.8 A chemical check on the load-bearing assumption

The decomposition asserts that the background is transported and the increment is local. That is
its central physical claim, everything else in the construction rests on it, and until recently
it had never been tested against anything chemical — every other line of evidence in this paper
is statistical or dynamical, so a check from composition is worth more than its sample size
suggests. {{fig:chemistry}} classifies days by back-trajectory sector, which is independent of
the composition product, and takes the secondary fraction — sulphate, nitrate and secondary
organics, species that form over hours to days and therefore mark aged air — from a composition
reanalysis [@Keller2021]:

| air-mass origin | secondary fraction |
|---|---:|
| Indian Ocean, south-west | {{claim:chem.sec_frac.SW_marine}} |
| local recirculation | {{claim:chem.sec_frac.local_recirc}} |
| Bay of Bengal | {{claim:chem.sec_frac.BoB_marine}} |
| peninsular India | {{claim:chem.sec_frac.Penin_India}} |
| Indo-Gangetic Plain | **{{claim:chem.sec_frac.IGP_E_India}}** |

Continental-Indian air is measurably more secondary-rich, and therefore more aged, than marine
air, and the ordering runs the way the decomposition requires. This is the first chemical support
the formulation has had, and it arrives from a direction none of its other evidence uses.

⚠ Two qualifications. The registered prediction that recirculated local air would be the
*freshest* was **refuted**: it is not, because stagnation gives local precursors time to age in
place. So *"local increment = fresh primary aerosol"* is too simple, and the decomposition
partitions correctly by origin without the clean chemical story we predicted. And the
composition product is itself a model at roughly 25 km, so it can corroborate or contradict; it
cannot validate.

🟢 One incidental result carries weight beyond this section. The organic-to-black-carbon ratio
exceeds {{claim:chem.oc_bc_min_monthly}} in every month, against roughly 1–2 for
traffic-dominated aerosol. That is a biomass-burning signature, and it is the third independent
line — after a local source-apportionment study [@Seneviratne2017; @Hopke2016] and the absence
of any correlation with the satellite NO₂ column [@Veefkind2012] — refuting the "predominantly
vehicular" characterisation this city has carried both in the literature and in our own earlier
work. What survives is narrower and still useful: traffic dominates the *timing* of the local
increment within a day, and is a minority of its *mass*.

## 6.9 What one instrument would change

The ladder of §4 gives a quantitative answer for this city, and it is not the answer the pooled
result would give.

| acquisition | expected RMSE reduction |
|---|---:|
| two local stations | **{{claim:maiac.deep_tropical_first2}}%** |
| a regional background station | {{claim:maiac.deep_tropical_background}}% |
| stations three to eight | ≈ {{claim:step.bud1_bud2}}% |

Local stations are worth {{claim:maiac.deep_tropical_local_advantage}}× the regional background
here — the inverse of the pooled recommendation, because Kandy sits in the band where the
ordering flips (§4.2). A reference monitor in the city would additionally close §6.5's
discrepancy and make the per-sensor offset `b_k` estimable for the first time (§2.2), moving the
city from `Bud1` to `Bud2`. We state this as the paper's practical recommendation for this city,
with the caveat that it rests on a {{claim:band.deep_tropical.n}}-city band.

---

## Drafting notes, to remove before submission

- Eight figures now carry this section, each preceded by its own explanatory paragraph.
- ⚠ The 400,000 population, the WHO guideline and the four literature records are EXTERNAL
  values and stay as cited text — putting them in `claims.json` would fake provenance.
- Still needing generating scripts: the 15.6% pixel lift, and the 800 m relief figure in §6.1.
- Kathmandu's spatial rank is quoted from the panel scorecard, NOT from the figure script, which
  scores a slightly different station set and gives 0.428. One rank per city per paper.
- Untokenised numbers in this section are inventoried in `TOKENISATION_BACKLOG.md`, which separates external values (correctly cited) from ones this project computed and still types by hand.
