## Defects found by audit rather than by review {#s-defects-found-audit-rather}

**What was expected.** That the model's own numbers were what the documentation said they were.

What happened. They were not, repeatedly, and the discrepancies were found by recomputing
rather than by anyone noticing.

The most serious concerned the sensorless tier. Its specification admits three information
streams, and its registration said the same. The implementation used one of them. Because every
gain on the ladder of {{ref:s-marginal-predictive-value-each}} is measured against the tier below it, every reported gain above
that tier had been measured against an artificially weakened baseline. The headline first rung
fell from a superseded value to {{claim:step.bud0c_bud1}} per cent when this was corrected.

Others followed once the numbers were being recomputed systematically. A gain measured across two
information streams had been reported under the name of one of them. A statistic describing
instrument classes had never been recomputed after the run it described was replaced. The panel
size and the number of city-days were both stale. One city had been scored in a tier whose data
it did not have. A published fused product had been used as an independent satellite observation
when it is trained on the very monitors the study prices.

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
