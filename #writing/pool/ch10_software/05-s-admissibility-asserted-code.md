## Admissibility, asserted in code {#s-admissibility-asserted-code}

{{ref:s-information-budget}} described the information budget. Its enforcement is in code rather than in discipline,
and it checks three things, each of which exists because the corresponding failure occurred.

A tier may not use a stream it is not entitled to. This was implemented first and is the obvious
direction.

A tier must use every stream it **is** entitled to. This was missing, and {{ref:ch-eight-approaches-did-work}} records what
its absence cost: a tier silently using one of three admitted streams, inflating every gain
measured above it.

And every scored unit must carry every stream its tier admits, because a single city missing a
stream is invisible in a pooled median and shifts it.

A deliberate omission is permitted but must be declared at the call site, so that it appears in
the code and not in someone's memory.
