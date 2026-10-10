## Comparing an areal model to a point instrument {#s-comparing-areal-model-point}

The model gives an average over a square kilometre. A monitor gives a reading at one point inside
that square. Comparing the two as though they were the same quantity is called a change-of-support
error, and it is the most common way a model of this kind is scored wrongly.

{{dia:obsoperator}}

For each instrument *k*,

$$y_k(t) = H_k[C](t) + b_k + e_k, \qquad e_k \sim \mathcal{N}\!\left(0,\; s_{\mathrm{meas},k}^2 + s_{\mathrm{rep},k}^2\right)$$

with *H*~*k*~ an observation operator, *b*~*k*~ a systematic offset and *s*~rep~ a representativeness
error arising from sub-grid variability the model cannot resolve. The operators differ by
instrument class. A reference monitor and a low-cost sensor are near-delta in space. A satellite
product is already an areal average. A passive sampler integrates in time rather than space, and
a mobile campaign integrates along a path.

Two quantities here are distinct and are routinely conflated. *b*~*k*~ is **systematic**: siting
bias plus device calibration. A kerbside monitor inside a kilometre cell reads systematically
above the cell mean, and this is also where a low-cost sensor's calibration error lives
[@Barkjohn2021; @Morawska2018]. *s*~rep~ is **random**, arising from unresolved structure, and it
is estimated from the local spatial variability of the field itself, so it grows in structured
hours and shrinks when the basin is well mixed.

This level of description is not decoration, and the clearest demonstration is a diagnosis it
makes available. The interval is nominal at ninety per cent by construction and empirically
checked here, which is the distinction that matters: conformal calibration earns its coverage
under exchangeability [@Vovk2005; @Angelopoulos2023], and hourly air quality in a monsoon
climate is not exchangeable, so the
nominal level is a design target and the measured coverage is the evidence. It covers
{{claim:kandy.cov90}} per cent of
observations at the two Kandy sensors. Read alone, that suggests the interval is too narrow, but
the misses are not symmetric. Observations fall below the lower bound in {{claim:kandy.miss_below}} per cent of hours
and above the upper bound in {{claim:kandy.miss_above}} per cent, which is a one-sided failure
rather than a width failure. Removing each sensor's own median offset restores coverage to
{{claim:kandy.cov90_recentred}} per cent. That pattern is a diagnostic of a possible calibration
bias at these two sensors, and only an explicit *b*~*k*~ makes it visible at all. It is not evidence
that the interval's width is correct for the basin field: the re-centred coverage is measured on the
same two sensors that calibrated the anchor, and the interval omits several sources of uncertainty
listed below.

Two readings of the offset remain open. The first is the change of support described above: the
field is an area mean and the sensors are points, so a systematic offset between them is expected.
The second is that the model is biased upward at these points. The second reading is supported by
the independent Kandy records of {{ref:s-checks-kandy-carry-weight}}, three of which also sit below
the model, and opposed by the one record from a non-low-cost instrument, which agrees with it. The
humidity correction of the sensor record, which uses a constant relative humidity
({{ref:s-excluded-processes-known-limits}}), is one candidate mechanism for such a bias. The
offset is reported as a level question that a co-located reference monitor would settle.

The interval is also incomplete in a way the coverage figure cannot reveal. It carries the
conformal uncertainty of the anchor and the spread of the local pattern, and the background enters
through a fixed band rather than an estimated distribution. It does not carry the uncertainty of
the confinement strength, of the local fraction ({{ref:s-partition-constraint-rather-than}}), of
the emission proxy or of the sensor calibration slope. Its nominal level is therefore a lower bound
on the uncertainty a user should attach to any one cell.

A limitation follows immediately and is stated rather than left to be inferred. The operators
are implemented and tested, and *b*~*k*~ and *s*~rep~ are estimated at panel cities that have
reference monitors. At Kandy they are **not estimated**, because estimating them requires a
reference monitor and Kandy has none. The observation model therefore disciplines the comparison
at the demonstration city without correcting it.
