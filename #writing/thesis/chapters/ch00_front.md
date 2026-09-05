# An information-tiered model for urban fine particulate matter in a city that cannot check it

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

Most of the world's population breathes air that nobody measures, and the deficit falls hardest
in the regions where concentrations are highest. Models supply a field where instruments do not,
but they are validated where monitors are dense and applied where monitors are absent, so the
transfer that matters cannot be scored. This thesis addresses that problem by changing the
question. Rather than asking how accurate a model is where accuracy cannot be measured, it asks
what a model is entitled to claim given the observations it has, and measures what each further
observation would be worth.

The model is an additive decomposition of fine particulate concentration into a spatially uniform
regional background and a locally generated increment redistributed by a unit-mean pattern. Two
properties make the measurement possible. The spatial mean of the field returns the temporal
anchor exactly, so an error in the pattern misplaces material without creating it. And the model
declares which observation streams each tier may use, with withholding implemented so that a
lower tier is reproduced bit-for-bit rather than approximately, which turns an ablation into a
measurement of information.

Running that measurement across {{claim:frame.cities}} cities in {{claim:frame.countries}}
countries and {{claim:frame.city_days}} city days gives results that are not what the field's
intuition suggests. Freely available static geography is worth {{claim:step.geography}} per cent
in daily error, comparable to the first local instrument. The second monitor through the eighth
are worth {{claim:step.bud1_bud2}} per cent. A regional background series is worth
{{claim:step.bud2_bud3}} per cent, the largest single gain measured, and rebuilding it from a
donor city the target has never seen recovers {{claim:donor.gain_reproduced_pct}} per cent of
that, which bounds how much of it could be an artefact of the proxy used. The ordering reverses
between latitude bands, so the recommendation derived from the pooled panel is the wrong
recommendation in the band the demonstration city belongs to.

The model is demonstrated at Kandy, Sri Lanka, a valley city with two low-cost sensors and no
operating reference monitor. The local share of concentration is {{claim:partition.f}}, derived
from a physical constraint rather than assumed. The field is checked against records that played
no part in building it, agreeing at {{claim:nbro.diff_pct_2021}} and
{{claim:nbro.diff_pct_2022}} per cent in two independent years.

The thesis also reports where the model stops. Two sites three hundred metres apart inside one
model cell differ by a factor of {{claim:spatial.paired_obs_ratio}} observationally while the
model returns unity, and a pre-registered test establishes that finer resolution does not close
the gap. The reason is a change of support: spread within a cell exceeds spread between cells.
A pre-registered test of a learned spatial pattern, with its detection limit fixed in advance,
reached {{claim:phase2.rho_learned}} against a registered bar of {{claim:phase2.bar}}, giving a
bounded null where five earlier unregistered nulls gave none.

What is established at Kandy is therefore narrower than the delivered field might suggest, and
the distinction is stated here so that it cannot be missed. The city-mean level and its seasonal
behaviour are checked against records the model played no part in producing. **The
neighbourhood-scale map is not validated, and this thesis does not claim it is**, because the
observations that would validate it do not exist in the city. What the work establishes is what
the model is entitled to claim given the observations available, together with a measurement of
what each further observation would be worth.

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
