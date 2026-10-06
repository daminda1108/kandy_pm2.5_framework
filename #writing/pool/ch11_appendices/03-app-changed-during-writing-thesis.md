# What changed during the writing of this thesis {#app-changed-during-writing-thesis}

Preparing this document required regenerating quantities that had been recorded earlier in the
project. Several of them moved. They are listed here rather than silently corrected, because the
pattern in them is the subject of {{ref:ch-eight-approaches-did-work}} and the machinery in {{ref:ch-reproducibility-machinery-catches-errors}} exists because of
them.

<!-- lint:off the recorded column lists values this project has RETIRED; they are the subject of the table -->

| quantity | recorded | regenerated | why it moved |
|---|---|---|---|
| countries in the panel | 32 | {{claim:frame.countries}} | never re-derived after the panel was corrected from 47 to {{claim:frame.cities}} cities |
| relief across the domain | 800 m | {{claim:kandy.relief_m}} m | a prose estimate; now taken from the elevation model |
| interval coverage after re-centring | 91.5 per cent | {{claim:kandy.cov90_recentred}} per cent | recomputed against the rebuilt field |
| donor benchmark correlation | 0.923 | {{claim:donor.benchmark_median}} | the recorded value was the single nearest pair, quoted as though it were a median |
| separation to the donor city | 93 km | {{claim:donor.colombo_km}} km | measured city centre to city centre, the convention every other pair uses |
| hours where the background exceeded the total | stated three ways | {{claim:field.precap_excess_mean}} per cent | one quantity had been reported as 38.5, as 38.2 of midday hours, and as 29.9 |
| parameters saturating their bounds | six of six | two of six | the project ledger carried the overstatement; the regenerated figure reports two |
| reference-dense cities, tropics against temperate | 5 and 32 | {{claim:census.deep_tropical}} and {{claim:census.temperate}} | pulled fresh from the global archive rather than recalled |
| population-weighted exposure uplift | 7 per cent | {{claim:exposure.uplift_pct}} per cent | the exposure file predated the field rebuild |
| attributable deaths per year | 427 | {{claim:burden.deaths}} | the same stale input |
| share of the background gain an independent network recovers | 79 per cent | {{claim:donor.gain_reproduced_pct}} per cent | re-run on the corrected bottom rung, which leaves less headroom for any background to recover |

<!-- lint:on -->

Two features of that table are worth stating.

**None of these was found by reading.** Every one was found by recomputing a quantity and
comparing, which is why the machinery of {{ref:ch-reproducibility-machinery-catches-errors}} exists and why it runs on every build rather
than at the end.

Four of them made an argument weaker and were kept anyway. The donor benchmark, the bound
saturation, the countries count and the independent-background recovery all made the surrounding
claim less impressive once corrected. The last of those was regenerated specifically because an
external reader identified the background rung as the thesis's most vulnerable claim, so it is
the clearest case of the pattern: the check was run in the place where the result was most wanted
to hold, and it came back smaller. A number that strengthens an argument is the least likely
number to be checked, and that is the argument for checking all of them mechanically rather than
selectively.
