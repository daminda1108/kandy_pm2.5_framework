## Methodological lessons beyond this problem {#s-methodological-lessons-beyond-problem}

Three of the findings here are not about air quality.

**A value-of-information analysis must not price observations against a covariate that was trained
on those same observations.** {{ref:s-effect-monitor-trained-covariate}} showed that a
monitor-trained covariate in the sensorless rung tilts the measured ordering toward the
background, while its effect on the value of the first stations is unresolved. Fused products are
now the default covariate in this field. That such products leak is established and guarded
against in evaluation practice [@Just2020]; what {{ref:s-position-literature-claims-novelty}}
argues is unreported is that the leakage need not appear as excess skill inside the contaminated
stream, so the obvious diagnostic can report it as immaterial while the comparison above it moves.

A null result without a stated detection limit converts a limitation of the experiment into a
claim about the world. {{ref:ch-eight-approaches-did-work}} records five nulls that did this and one that did not, and the
difference between them is the difference between a belief and a bounded claim. The cost of
stating a detection limit in advance is a power calculation. The cost of not stating one, in this
project, was four months.

**Registration fixes how a comparison is run, not whether it compares like with like.** The
ladder's registered confirmation was frozen in code, scored once on cities whose data had not been
retrieved, paired within city, averaged over random station splits and learner seeds, and gated
for parity with the discovery code. Every one of those safeguards passed, and the registered
ordering of a background above the first local stations was still an artefact of construction:
the first stations entered only as a recalibration of the sensorless estimate, while the
background was read on the day. Put on the same footing the two were equal [ledger F.124]. The
same review found a pooled siting interval of exactly zero that arose from averaging estimators
which cannot differ, and a crossing count that fell from fifteen of twenty-three cities to
{{claim:v2.curve.full.holm_crossing}} once multiple testing was corrected. The lesson is
procedural. Before a comparison is registered, each arm should be written down with the data it
sees and the time at which it sees them, and the arms should be checked to differ only in the
factor under test. A pooled interval of exactly zero should be read as a symptom to inspect, never
as a result.
