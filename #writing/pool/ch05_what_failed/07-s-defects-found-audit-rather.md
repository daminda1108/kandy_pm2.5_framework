## Defects found by audit rather than by review {#s-defects-found-audit-rather}

**What was expected.** That the model's own numbers were what the documentation said they were.

What happened. They were not, repeatedly, and the discrepancies were found by recomputing
rather than by anyone noticing.

The most serious concerned the sensorless tier. Its specification admits three information
streams, and its registration said the same. The implementation used one of them. Because every
gain on the ladder of {{ref:s-marginal-predictive-value-each}} is measured against the tier below it, every reported gain above
that tier had been measured against an artificially weakened baseline. The headline first rung
fell substantially when this was corrected, and it fell again in each later check: the
verification pass described below lowered it once more, and the registered confirmation on fresh
cities put the first two stations, used as the ladder used them, at
{{claim:v2.conf.reco.first2_rmse.median}} per cent
[{{claim:v2.conf.reco.first2_rmse.lo}}, {{claim:v2.conf.reco.first2_rmse.hi}}], well below the
discovery estimate.

Others followed once the numbers were being recomputed systematically. A gain measured across two
information streams had been reported under the name of one of them. A statistic describing
instrument classes had never been recomputed after the run it described was replaced. The panel
size and the number of city-days were both stale. One city had been scored in a tier whose data
it did not have. A published fused product had been used as an independent satellite observation
when it is trained on the very monitors the study prices.

The largest audit came later, as a verification pass over the whole ladder before its
confirmation was registered [ledger F.115; ledger F.116]. It found that one national network had
been left out of the climate-band assignment and classed as low-cost although its monitors are
reference grade; that a city excluded for a data fault was still present in two scripts; that
several loops caught every exception silently, so a failed fit returned a missing value rather
than an error; that four verdicts had been stated from unpaired medians; that the routine which
requested meteorological drivers in quarterly chunks never requested the partial quarters at the
head and tail of each city's window, silently losing about one city-day in twenty; and that the
sensorless geography had been averaged over the monitoring sites themselves, which describes the
scoring sites rather than a city without monitors, since monitor sites are markedly denser than
their urban surroundings. **The most consequential finding was that every headline number had come
from one random station split and one learner seed.** Across twenty splits the interval of the
earlier deep-tropical result excluded zero in only three, and the learner seed alone moved the
first-rung gain by a large fraction of its value. Every effect is now averaged over splits and
seeds before cities are bootstrapped, and the deep-tropical result is reported as exploratory.

An external review after the confirmation found three more defects, none of which any automated
gate could see [ledger F.124]. The registered rungs did not use their observations in the same
way: the first stations entered only as a recalibration of the sensorless estimate, while the
background was read on the day, so the registered ordering of the two was a construction
artefact. The registered siting interval of the spatial learning curve was exactly zero because
its summary pooled estimators that never use the fitting stations. And the coherence cap that
bounds the partition was evaluated on days in universal time rather than local time.

**What it cost.** A full development cycle, and the retraction of several statements that had
been made confidently.

What it established. Two things that changed how the work is done.

The first is that admissibility must be checked in both directions. A check that a tier does not
use information it is not entitled to is half a check. The other half is that a tier does use
everything it is entitled to, because a tier that quietly under-uses its budget inflates every
measurement taken above it. Both assertions now exist in code.

The second is the machinery this thesis is written with. Every number in this document is
generated from a scored file at build time, and the build refuses to complete if the prose and
the data disagree. {{ref:ch-reproducibility-machinery-catches-errors}} describes it. It was written because nine numbers in an earlier
draft had gone stale against their own sources, including one quantity that was stated three
different ways in a single document without anyone noticing.
