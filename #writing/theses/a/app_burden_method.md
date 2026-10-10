# Attributable burden: method, and why no estimate is given {#app-attributable-burden-projection}

{{ref:ch-kandy-setting-record-stakes}} names health as one of the two stakes of this work, so the
question of how many deaths the delivered field implies has to be addressed. {{This:app-attributable-burden-projection}} sets out
how that estimate would be made and why this thesis does not report one. An earlier draft did report
a number, with an interval; it was withdrawn because neither the number nor its interval could be
defended, and a figure of the form "N deaths per year" is quotable in a way its caveats are not.

**The method.** The population-weighted exposure of {{ref:s-exposure-weighting}} would be passed
through the Global Exposure Mortality Model for non-communicable disease and lower respiratory
infection [@Burnett2018], which gives the relative risk of death at each concentration. Combined with
the baseline mortality from those causes, the relative risk gives the attributable deaths, and the
same calculation with concentrations at the World Health Organization guideline [@WHO2021] gives the
share that would be avoidable.

**Why no estimate is reported.** Three requirements are not met.

The response function is defined for adults of twenty-five and older, with baseline mortality taken
by age group. Age-specific baseline mortality for Sri Lanka by cause, from the Global Burden of
Disease study, had not been obtained when this thesis was written. Applying the function to all ages
with an all-age crude death rate does not reproduce the age-structured calculation, and the
direction and size of the difference have not been established.

The concentration level is unresolved ({{ref:s-checks-kandy-carry-weight}}). Three of the four
independent Kandy records sit below the field, and across the ladder's cities the satellite level
used to anchor it sits above the withheld city means. If the field reads high, any burden computed
from it is over-stated by an amount this thesis cannot bound.

The uncertainty cannot yet be propagated. A defensible interval would carry the uncertainty of the
response function's parameters, of the mortality baseline, of the population weighting and of the
concentration field itself, including the level question and the omissions of the delivered
interval set out in {{ref:s-interval-calibration}}. Passing only the bounds of the field's nominal
interval through the central response function, as the withdrawn draft did, leaves out most of it.

**What a defensible estimate requires.** Age-specific baseline mortality by cause; a concentration
level checked against a reference instrument at Kandy; Monte Carlo propagation of the response
function's published parameter uncertainty together with the field's level and interval; and a
stated population domain. The field covers a fifteen kilometre square that holds more people than
the municipality of Kandy, so an estimate must say whether it refers to the domain or to the city.
