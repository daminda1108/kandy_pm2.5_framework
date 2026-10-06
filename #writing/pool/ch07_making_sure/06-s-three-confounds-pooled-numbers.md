## Three confounds the pooled numbers hid {#s-three-confounds-pooled-numbers}

Each was caught by a gate declared before the run and not by review, and each would otherwise
have reached print.

**Country crossed with latitude.** A minimum-cost sampling design drew the entire mid-latitude
arm from a single national network, aliasing band with network so completely that no
band-stratified result could have been interpreted. It was corrected by a registered amendment
before any scoring took place, which is the only reason it appears here as a methodological note
rather than as a retraction.

Driver completeness crossed with band. Boundary-layer height coverage is uneven across bands,
so the ladder was re-run without it. The first rung moves from
{{claim:confound.blh.with_blh_step1}} to {{claim:confound.blh.without_blh_step1}} per cent, a
shift of {{claim:confound.blh.delta}} percentage points, which bounds what the uneven coverage
can be doing. The band ordering is unchanged.

Instrument class crossed with band. The deep-tropical cell is
{{claim:confound.deep_tropical_lcs_pct}} per cent low-cost sensors against
{{claim:confound.other_bands_lcs_pct}} per cent in the other bands, and this one cannot be
sampled away for the reason {{ref:ch-kandy-setting-record-stakes}} gave.

This is the confound that most limits the band result, and it deserves more than a note. Low-cost
sensor response depends on humidity, aerosol composition, sensor age and the duration and design
of the calibration, and there is no universal calibration procedure that removes this
[@Zhang2025]. A band that is mostly low-cost is therefore not only a different climate regime, it
is a different measurement regime, with a different error structure in both the fitting data and
the held-out target. Some part of what the band contrast measures is instrument behaviour rather
than atmosphere, and no analysis in this thesis can separate the two.

The consequence is carried into the recommendation rather than left here. Kandy's own instruments
are low-cost, so the low-cost group is the right analogue for it, and reading Kandy against a
band that happens to share its instrument class is a better match than reading it against the
pool. That is a defence of the recommendation and not of the mechanism: it makes the advice
appropriate for Kandy while leaving open what the band contrast is actually made of.

There is now a named route by which the confound could operate, which is more than this thesis
could offer when the confound was first recorded. [@Senarathna2026] calibrated low-cost sensors
against reference monitors in two Sri Lankan climatic zones and found that a calibration fitted in
the wet season, applied to dry-season data, produces a mean absolute percentage error of 26.57 per
cent. Seasonal calibration drift of that size in a group of cities that is
{{claim:confound.deep_tropical_lcs_pct}} per cent low-cost, against
{{claim:confound.other_bands_lcs_pct}} per cent elsewhere, is a concrete mechanism by which part of a
band difference could be instrument behaviour rather than atmospheric behaviour. It does not
overturn the inversion, and it is not evidence that the inversion is spurious. It converts the
confound from something this thesis could only label into something a future study can measure,
which is the more useful state for it to be in.

{{fig:confounds}}

The gain from additional sensors depends on what they are, and the class matters. Median
shrinkage weight placed on sensors three through six is {{claim:class.LCS.w_bud2}} for low-cost
units against {{claim:class.reference.w_bud2}} for reference monitors, a contrast of
{{claim:class.w_bud2_contrast}} times. Low-cost units gain more from replication because
per-device error averages down.

An earlier version of this work reported that contrast as infinite and concluded that reference
networks gain nothing at all from added stations. That was computed on a superseded run. The
direction survives, the magnitude does not, and any argument resting on the strong form has to be
re-made rather than inherited.
