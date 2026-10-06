# Eight approaches that did not work {#ch-eight-approaches-did-work}

{{This:ch-eight-approaches-did-work}} is longer than the one describing the model that did work, and it is placed before
it, not in an appendix. The reason is that the pattern across these eight attempts turned
out to be more useful than any of them individually, and the model in {{ref:ch-model}} is largely a
consequence of that pattern rather than of a design decision taken at the start.

Each section states what was expected, what happened, what it cost, and what it established.
The last of those is the column that matters, and it varies enormously between the eight.

{{dia:timeline}}

The eight are not of equal weight and the chapter does not present them as though they were. Four
changed the design of the model that followed. Four established something narrower, either
closing a question or exposing a defect in how the work was being checked. A reader who wants the
argument and not the record can take the first group and {{ref:s-pattern-across-eight}}.

**The four that changed the design.** {{ref:s-physics-informed-network-transferred}} found that in the one transfer tested, between
two cities on different continents, an imposed physical description survived the move while a
fitted parameterisation did not. That is a single comparison rather than a general property of
physics, and it is reported as the observation that motivated a design decision and not as a
law: it is why the final construction imposes its physics and learns only the temporal behaviour. {{ref:s-conditional-neural-process-trained}} established that a learned spatial
field trained across cities does not recover within-city structure. {{ref:s-fine-tuning-two-sensors}} established that
a model given coordinates will memorise them, which produced the admissibility rule governing
every tier in {{ref:s-information-budget}}. {{ref:s-learned-spatial-pattern-pre}} supplied the bounded spatial null that {{ref:ch-model-stops}} is devoted
to explaining.

The four that established something narrower, or nothing. {{ref:s-rigid-physical-form-fitted}} is an identifiability
diagnostic that closed a modelling direction. {{ref:s-five-reconstructions-regional-background}} records five reconstructions of the
background, all rejected, which is the origin of the constraint in {{ref:s-partition-constraint-rather-than}}. {{ref:s-defects-found-audit-rather}}
records defects found by audit rather than by review, and is the reason {{ref:ch-reproducibility-machinery-catches-errors}} exists. None
of the three produced a better model and each prevented a wrong claim.

{{ref:s-five-attempts-find-spatial}} belongs in this second group for a different reason, and it is the one section whose
placement is itself an argument. It consumed the most time of any entry here and established the
least, and {{ref:s-pattern-across-eight}} explains why. A reader short of patience should still read it, because the
contrast with {{ref:s-learned-spatial-pattern-pre}} is the chapter's conclusion.
