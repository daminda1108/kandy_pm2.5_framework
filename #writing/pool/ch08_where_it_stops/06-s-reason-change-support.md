## The reason, which is a change of support {#s-reason-change-support}

The deeper explanation is not about method at all. It is about which quantity the model and the
observations are each reporting. A model cell reports an average over a square kilometre. A monitor
reports a value at one point inside that square. If most of the variation in a city happens between
one cell and the next, then a kilometre-scale map can capture it and a finer map would help. If
most of it happens inside a single cell, no kilometre-scale product can capture it however it is
built, and refining the grid is answering a question that was never the obstacle.

The figure below settles which of those two worlds this is. It compares the spread of concentration
found within a typical cell against the spread found between cells across the whole domain, on the
same measure so the two are directly comparable. The comparison needs no model skill to interpret:
whichever bar is taller names where the variation lives.

{{fig:withinpixel}}

The spread within a typical model cell is {{claim:s2.within_pixel_p90p10}}, and the spread
between cells across the whole map is {{claim:s2.between_pixel_p90p10}}. **Most of the within-city
variation is inside a cell, not between cells.** The cell mean is conserved through the
comparison to {{claim:s2.cell_mean_drift}}, so this is a statement about the field's structure
and not about a numerical artefact.

A second line points the same way from the opposite end. {{ref:s-implications-radius-result}} reports that predictor skill
rises with the radius of the buffer the predictor is measured over, and peaks at
{{claim:phase1.best_radius_km}} kilometres,
which is coarser than the cell the model reports on. Taken together the two results bracket the
usable band from both sides: finer than a cell is unrecoverable, and what remains informative is
coarser than a cell.

That is a change-of-support statement rather than a data-quality statement, and it has a
consequence the field does not generally acknowledge. A one kilometre product cannot answer
"which part of this cell is worst" for any city with this structure, however the product is
built and however much data is used to build it. The approaches that do reach below the grid,
street-scale dispersion modelling [@Cimorelli2005] and sub-grid downscaling of a chemistry
transport model [@Denby2020], get there by requiring a local emissions inventory, which is
what a city in this position does not have.

### Three things called resolution, and which of them {{this:ch-model-stops}} measures {#s-three-things-called-resolution}

The statement above is easy to over-read, and separating the concepts it touches shows what the
evidence does and does not reach.

**The scale at which the atmosphere actually varies.** This is a property of the city. {{ref:s-two-decades-measurement}}
establishes that it is fine and the variation is large, because a single instrument on a single
protocol recorded a factor of {{claim:spatial.paired_obs_ratio}} over three hundred metres
[@Elangasinghe2008]. Nothing in {{this:ch-model-stops}} contradicts that, and nothing in it should be read
as claiming that Kandy's air is uniform below a kilometre. The opposite is measured.

The scale at which the reporting grid is defined. This is a choice, and {{ref:s-resolution-tested-refuted}} tested
changing it. A tenfold refinement in cell area moved the paired-site ratio by
{{claim:s1.paired_delta_on_refinement}}, so the choice is not what is binding.

The scale at which the available predictors carry information. This is the constraint, and it
is the only one of the three {{this:ch-model-stops}} measures. {{ref:s-implications-radius-result}} reports that predictor skill
rises with the radius over which a predictor is averaged and peaks above the cell size, and
{{ref:s-six-negative-results-their}} bounds what a learned pattern adds over the best single predictor. Both are
statements about a predictor set, not about the atmosphere.

Read together the three give a conditional claim, not a universal one, and the condition is
worth carrying: **given the globally available covariates that a city with no monitors can
obtain, sub-kilometre structure cannot be placed, even though it exists and is large.** A
campaign that measured the structure directly would not be bound by this
[@Schneider2017; @Gressent2020; @Kamigauti2024], although {{ref:s-deliberate-siting-tested-dense}} finds that siting the
fitting stations deliberately, without measuring the structure itself, does not escape it. The
claim is a limit on inference from a particular information set and not a
statement about the ultimate predictability of urban air.

The station-based side of the same question points the same way. In the registered spatial
learning curve of {{ref:s-what-stations-buy-map}}, a station informs roughly the kilometre around
it, beyond which a held-out site is predicted no better than by the city mean. That kilometre is
the width of the analysis's first distance bin, so it bounds the resolution of the statement from
above and is not a measured correlation length. On full station records the registered prediction
that no estimator would exceed a city's within-cell ceiling was refuted, because in two cities
stations sharing one cell predicted each other worse than chance. Neighbouring points inside a
cell can disagree strongly, which is the change-of-support statement seen from the stations.
