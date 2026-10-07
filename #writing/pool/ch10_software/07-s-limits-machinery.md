## Limits of the machinery {#s-limits-machinery}

It does not check that a number is meaningful, only that it is current. A claim can be
regenerated faithfully from a file and still be the wrong statistic, computed on the wrong
subset, answering a question nobody asked. {{ref:ch-eight-approaches-did-work}} records several errors of exactly that kind
and none of them would have been caught by any gate described here. They were caught by
recomputing a quantity a second way and finding two answers.

The strongest examples came late. The headline of the information ladder, as first reported,
rested on one random choice of withheld stations and one learner seed; repeating the analysis over
many splits showed that a deep-tropical reversal, then the thesis's central recommendation for
Kandy, was not distinguishable from zero. A pooled interval for one registered spatial prediction
was reported as exactly zero at both ends because the pooling combined estimators that cannot
differ at a site, which no gate could flag because the interval was faithfully regenerated from
the file that held it. And the constraint that sets the local fraction was found to run on UTC
days rather than local days. Each passed every gate described in
{{this:ch-reproducibility-machinery-catches-errors}}.

Registration has a limit of the same kind. It fixes how a comparison is run; it does not check
that the comparison is like for like. In the registered information ladder the rung that adds the
first local stations used them only to recalibrate the sensorless estimate, while the rung that
adds a background read the background on the day. Frozen code, parity checks, averaging over
splits and pairing within city all passed, and the registered ordering of the two rungs was
nevertheless a product of how they were built: used the same way, they are worth about the same.
The rule that follows is to write down, for every arm of a registered comparison, which data it
sees and when it sees them, and to confirm that the arms differ only in the factor under test.

It does not check figures for their content, only for their currency and their placement.

It does not run itself. The build refuses to complete when a token does not resolve, but a refusal
is only seen when someone builds. When a set of claim keys was renamed during a correction to the
ladder, the thesis still cited the old names, and the document did not build for about two weeks
without anyone noticing, because nothing in the analysis workflow ran the build. The rule adopted
afterwards is that any change to the claim keys or to the registry is followed at once by a build
of every document that cites them.

### The external review {#s-external-review-practice}

In October the analysis and the Kandy chain were given an adversarial review written as an
outside referee would write it, at the level of the code, and every finding was answered by
computation rather than by argument. It produced the like-for-like comparison of the ladder's
rungs, the station-count curve read on the day, a multiple-comparison correction and empirical
detection limits for the spatial learning curve, the sensitivity of the local fraction to the day
boundary and the daily-minimum statistic, the hourly-humidity recalculation of the sensor
correction, and the off-the-shelf baseline at the regional station. It narrowed several claims
that had passed every internal gate, and {{ref:app-changed-during-writing-thesis}} records what
changed. The review did not add a registered test of its own; its analyses are reported as
exploratory.

And it does not remove the need for a reader. The most serious errors in this project were found
by a person deciding to check something, and the machinery's contribution is that it makes the
checking cheap enough to do repeatedly rather than once.
