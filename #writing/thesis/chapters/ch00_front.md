# An information-tiered decomposition for hourly kilometre-scale urban PM2.5: what it reconstructs, and what each further observation is worth, demonstrated at Kandy

**A thesis submitted in partial fulfilment of the requirements for the degree of Bachelor of
Science**

Daminda Alahakoon

University of Peradeniya

2026

---

<!-- lint:off a declaration of originality and an acknowledgement are first person by convention; a declaration that avoids saying my own is not a declaration -->

## Declaration

The work presented in this thesis is my own, carried out under the supervision named in the
acknowledgements. Where the work of others has been used it is cited. Where results from earlier
stages of this project have been superseded or corrected, the correction is stated rather than
the earlier result quietly replaced, and every numeric claim in this document is regenerated
from its source at build time by the machinery described in Chapter 10.

Signed: ..........................................    Date: ..........................

---

## Abstract

Most of the world's population breathes air that nobody measures, and the shortage of instruments
is worst in the regions where concentrations are highest. Models fill the gap where instruments do
not exist, and they are good. But a model is tested where monitors are dense and then used where
monitors are absent, so the one transfer that matters is the one that cannot be scored.

This thesis changes the question instead of attempting the impossible test. Rather than asking how
accurate a model is where its accuracy cannot be measured, it asks what the model is entitled to
claim from the observations it already has, and then measures what each further observation would
be worth. Worth is given a precise meaning: the amount by which out-of-sample daily error falls
when that observation is added, at a fixed point in a fixed order of adding them. This is a
practical stand-in for value. It is not the decision-theoretic value of information, because no
decision problem is specified.

The model separates fine particulate concentration into two parts. A regional background is the
same everywhere in the city at a given hour. A locally generated increment sits on top of it and
varies from place to place, following a spatial pattern whose average across the city is one. Two
design properties make the measurement possible. The average of the map always returns the
city-wide estimate, so an error in the pattern moves material to the wrong place without creating
any more of it. And the model states which observations each tier is permitted to use, with removal
implemented so that taking one away reproduces the simpler tier exactly rather than approximately.
That is what turns an ablation into a measurement of information, because the difference between
two tiers is then the effect of the data and not of a changed model.

Running that measurement across {{claim:frame.cities}} cities in {{claim:frame.countries}}
countries and {{claim:frame.city_days}} city days gives results the field's intuition does not
predict. Freely available geography, meaning terrain, roads, land cover, night lights and
population, is worth {{claim:step.geography}} per cent in daily error, which is comparable to the
first local instrument a city could buy. The third through sixth monitors are worth
{{claim:step.bud1_bud2}} per cent, and counting upward from a single station shows the saturation
arriving earlier still: the first station buys {{claim:stn.one_gain}} per cent and the second adds
{{claim:stn.second_adds}} points.

The largest single gain comes from a background series measured outside the urban core, at
{{claim:step.bud2_bud3}} per cent. That series is not a rural monitor. It is a stand-in built from
each city's own outermost monitors, so it was rebuilt using a donor city the target never sees. An
independent network recovers {{claim:donor.gain_reproduced_pct}} per cent of the gain, which puts
an upper bound on how much of it could be an artefact of the stand-in, and recovery falls to
{{claim:donor.reproduced_deep_tropical}} per cent in the group the demonstration city belongs to.
What the panel establishes is that a background measurement carries substantial transferable
information, not that a rural station would deliver this figure at Kandy.

Two things qualify every figure above. Each is what an observation is worth at one position in one
workable order of adding them, not a fixed property of that observation, and Section 7.2 shows that
reordering leaves the conclusions intact while moving one of the magnitudes by a factor of twenty.
The ordering also reverses between groups of cities. Within the deep tropics the panel supports an
ordering in which local observations outperform the background stand-in, so the recommendation
drawn from all cities pooled is the wrong recommendation for the group the demonstration city
belongs to. That group holds thirteen cities, and the type of instrument used in it is closely tied
to its latitude, so how much of the reversal reflects the atmosphere rather than the instruments is
unresolved.

The ordering depends on what is being measured as well. Local observation wins on average daily
error. The background stand-in wins on the dirtiest ten per cent of days, and on whether the World
Health Organization guideline is exceeded, where the interval excludes zero. The recommendation is
therefore a statement about daily city-mean accuracy and not about detecting episodes, and this
thesis names both as reasons a city might want a model at all.

The model is demonstrated at Kandy, Sri Lanka, a valley city with two low-cost sensors and no
working reference monitor. The decomposition assigns {{claim:partition.f}} of modelled
concentration to the local increment, a figure fixed by a physical consistency constraint rather
than assumed. Across the anchored years it ranges from {{claim:partition.f_lo}} to
{{claim:partition.f_hi}}, and alternative definitions of the background window give
{{claim:field.f_form_calendar}} to {{claim:field.f_form_roll48}}, the upper end belonging to a
window longer than the timescale on which the background is defined. This is a split imposed by the
model and not a measurement of sources. The increment is the part that varies across the map, which
is not the same thing as material physically emitted in Kandy, and the model carries no chemistry
that could separate them. The city-mean level is checked against two published records that played
no part in producing the spatial pattern, agreeing to {{claim:nbro.diff_pct_2021}} and
{{claim:nbro.diff_pct_2022}} per cent in two independent years. Because the model's timing is
calibrated against Kandy's own low-cost sensors, those checks test the modelled variation on top of
an already anchored average rather than the field as a whole.

The clearest negative result concerns the model's own spatial machinery. The step that
redistributes the emission surface through terrain-steered flow makes neighbourhood ranking worse,
lowering it from {{claim:r2.rho_emission_surface}} to {{claim:r2.rho_with_atransport}} across ten
monitored cities and improving only {{claim:r2.cities_improved}} of them. The measurement framework
therefore works better than the spatial model it was built to evaluate, which is an uncomfortable
result to report and the most directly actionable one in the thesis.

The thesis also reports where the model stops. Two sites three hundred metres apart fall inside one
model cell and differ by a factor of {{claim:spatial.paired_obs_ratio}} when measured, while the
model says they are identical. A pre-registered test established that a finer grid does not close
the gap. The reason is that the variation lives inside cells rather than between them, since the
spread within a typical cell is larger than the spread between cells. A second pre-registered test,
of a learned spatial pattern with the smallest detectable effect fixed in advance, reached
{{claim:phase2.rho_learned}} against a registered pass mark of {{claim:phase2.bar}}. Because that
detection limit was set beforehand, the negative result carries a stated size, which five earlier
unregistered negative results did not.

What is established at Kandy is therefore narrower than the delivered field might suggest, and the
distinction is stated here so that it cannot be missed. The city-mean level and its seasonal
behaviour are checked against records the model played no part in producing. **The
neighbourhood-scale map is not validated, and this thesis does not claim that it is**, because the
observations that would validate it do not exist in the city. What the work establishes is what the
model may claim from the observations available, together with a measurement of what each further
observation would be worth.

---

## Acknowledgements

To my supervisors, for allowing a project to change shape three times when the evidence required
it. To the researchers whose published measurements at Kandy made external checking possible at
all, and whose work is the only reason any claim in Chapter 7 can be called independent. To the
maintainers of the open archives on which this work depends entirely, none of whom will ever know
it was used this way.

<!-- lint:on -->

---

## List of figures

{{listoffigures}}

---

## List of tables

{{listoftables}}

---

## Abbreviations

| | |
|---|---|
| AOD | aerosol optical depth, a satellite retrieval of column loading |
| BAM | beta attenuation monitor, a reference-grade instrument |
| BLH | boundary layer height |
| CRF | concentration-response function |
| DEM | digital elevation model |
| LCS | low-cost sensor |
| LOCO | leave-one-city-out cross-validation |
| LUR | land-use regression |
| PM2.5 | particulate matter below 2.5 micrometres aerodynamic diameter |
| PM10 | particulate matter below 10 micrometres aerodynamic diameter |
| RMSE | root mean square error |

## Symbols

| | |
|---|---|
| `T(t)` | basin-mean concentration at hour t, the temporal anchor |
| `B(t)` | regional and transboundary background, spatially uniform |
| `P(x, y, t)` | local pattern, normalised to unit spatial mean |
| `inc(t)` | local increment, `T(t) - B(t)` |
| `H_k` | observation operator for instrument k |
| `b_k` | systematic offset for instrument k |
| `s_rep` | representativeness error from unresolved sub-grid structure |
| `f` | local fraction of concentration, the partition |
| `F_min` | floor on the local share imposed by the coherence constraint |
| `rho` | Spearman rank correlation |
