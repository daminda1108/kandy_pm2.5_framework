# Appendix A. Constants and configuration

Values that are configuration rather than measurement. They are wrong only if the model changes,
in which case the code changes with them.

| quantity | value | what it is |
|---|---|---|
| modelled domain | 15 by 15 km | the extent over which the field is delivered |
| reporting resolution | 1 km, hourly | the grid the field is published on |
| solve resolution | {{claim:subgrid.production_res_m}} m | the grid the transport solver runs on |
| fine emission grid | {{claim:subgrid.fine_res_m}} m | the grid the emission surface is computed on |
| coverage | 2019 to 2026 | satellite-anchored to 2023, extension tier thereafter |
| interval level | 90 per cent | nominal coverage of the delivered interval |
| sensorless predictors | {{claim:bud0c.n_features}} | of which {{claim:bud0c.n_geo_features}} are static geography |
| local share floor | {{claim:partition.f_min_parameter}} | the one free parameter in the coherence constraint |

# Appendix B. Registered predictions and their outcomes

Five pre-registrations were lodged before the corresponding analyses ran. Each stated its
predictions and the condition under which each would be abandoned.

{{tbl:T7_5}}

The registrations are held by a third-party service and are timestamped at creation rather than
by the author. Their identifiers appear in the chapters that use them.

⚠ One registration was superseded rather than withdrawn. It was run and reported, and the reason
it was superseded is itself a finding: the tier it scored had been using one of the three
information streams its budget admitted, so the comparison it made was against an artificially
weak baseline. It is cited as run, reported and superseded, because concealing it would remove
the evidence for the correction.

# Appendix C. Reproducing this work

The analysis code, the generating script for every numeric claim, the figure and table scripts,
and the pre-registration documents are held in a version-controlled repository.

The document is produced by four steps, each of which refuses to proceed if the one before it
failed:

1. regenerate every claim from the scored files, and compare against the stored values
2. generate the figures and tables
3. assemble the chapters, resolving claim, figure and table tokens and numbering by chapter
4. render to the output format against a reference document that carries the typography

Two limitations are stated rather than glossed.

The observational inputs are third-party and are not redistributed here. Their sources and
identifiers are given in Chapter 4 so that they can be obtained, but one of them requires an
institutional agreement and none of them is instantaneous.

The earliest experiments described in Chapter 5 are not reproducible from this repository. Their
model checkpoints and input frames have been superseded, and the honest position is that those
results are recorded rather than reproducible. They are marked as such wherever they appear.

# Appendix D. What changed during the writing of this thesis

Preparing this document required regenerating quantities that had been recorded earlier in the
project. Several of them moved. They are listed here rather than silently corrected, because the
pattern in them is the subject of Chapter 5 and the machinery in Chapter 10 exists because of
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
comparing, which is why the machinery of Chapter 10 exists and why it runs on every build rather
than at the end.

**Four of them made an argument weaker and were kept anyway.** The donor benchmark, the bound
saturation, the countries count and the independent-background recovery all made the surrounding
claim less impressive once corrected. The last of those was regenerated specifically because an
external reader identified the background rung as the thesis's most vulnerable claim, so it is
the clearest case of the pattern: the check was run in the place where the result was most wanted
to hold, and it came back smaller. A number that strengthens an argument is the least likely
number to be checked, and that is the argument for checking all of them mechanically rather than
selectively.
