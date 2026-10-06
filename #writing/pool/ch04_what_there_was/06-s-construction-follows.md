## The construction that follows {#s-construction-follows}

The streams described in {{this:ch-available-data-deliberate-constraint}} do not combine in a single step, and the order in which they
enter matters to every result reported later. The figure below traces one path from raw inputs to
delivered field: which archives are read, which quantities are computed from them, where the
satellite anchor and the ground sensors enter, and what is written out at the end. Two features are
worth noting before reading it. The temporal and spatial parts of the model are computed
separately and joined only at the last step, which is what allows {{ref:ch-validation-without-local-ground}} to score them
independently. And every arrow leaving a box is a file on disk rather than a value held in memory,
which is what makes the regeneration chain of {{ref:ch-reproducibility-machinery-catches-errors}} possible.

{{dia:pipeline}}

What follows describes how these streams are combined. The temporal anchor takes the
drivers and the satellite level and produces a basin-mean concentration for every hour. The
background term takes the same drivers and produces a regional contribution. The spatial pattern
takes the static geography and produces a unit-mean surface. {{ref:ch-model}} sets out the formulation
and {{ref:s-marginal-predictive-value-each}} measures what each stream contributes.

The order in which those three are described is not the order in which they were built, and
{{ref:ch-eight-approaches-did-work}} gives the actual sequence, which involved abandoning two complete architectures before
arriving at this one.
