## The information budget {#s-information-budget}

An information budget is a statement of which observations a given tier of the model is allowed to
use. The code that builds each tier checks itself against that statement, so a tier cannot reach a
data source it is not entitled to. The restriction is enforced by the program rather than by the
author remembering to honour it.

{{dia:tiers}}

The tiers are nested, and the nesting is asserted at import time so that a malformed budget
cannot be registered. Each tier declares, in one machine-readable object, what it admits, what it
estimates, what it imposes, and which tier it degrades to.

Because each tier admits everything the tier below it admits and one thing more, the tiers form a
sequence that a city can climb as it acquires observations. This thesis calls that sequence **the
ladder**, and each step from one tier to the next **a rung**. The value of an observation is then
simply the improvement measured across the rung that admits it, and the rest of {{ref:s-marginal-predictive-value-each}} is
written in those terms.

The check runs in three directions, and each one is there because that particular failure actually
happened during this project.

The first stops a tier reaching for information it was not granted. This is the obvious
direction and it was implemented first.

The second stops a tier **quietly failing to use what it has**. This is the direction that was
missing, and {{ref:s-defects-found-audit-rather}} describes what its absence cost: the sensorless tier used one of the
three streams its budget admits, so every gain measured above it was measured against an
artificially weak baseline.

The third stops a tier being scored on units that lack one of its streams. A single city missing
a stream is invisible in a pooled median and shifts it.

The sensorless tier as finally specified carries {{claim:bud0c.n_features}} predictors, of which
{{claim:bud0c.n_geo_features}} are static geography. {{ref:s-dependence-estimator}} shows that this width is not
incidental to the results.
