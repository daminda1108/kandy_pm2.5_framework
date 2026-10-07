## The effect of a monitor-trained covariate {#s-effect-monitor-trained-covariate}

The satellite stream of the sensorless rung was initially a published fused concentration product
[@Wei2023]. Products of that kind are trained on ground monitors, in this case on networks that
supply part of this study's own panel, so the stream was not an independent observation and its
measured value could be a mixture of satellite information and recycled monitor information. Every
headline in {{this:a-app-panel}} therefore uses a raw satellite aerosol retrieval
[@Lyapustin2018; @Levy2013], which is a radiometric product trained on no monitor at all. This
section records what the substitution changed. Everything in it is exploratory unless marked.

**The satellite rung itself.** A registered test on the first version of the ladder asked whether
the fused product inflated its own rung [OSF bkpyr]. It did not: the fused product's rung was worth
{{claim:c1.step_fused_ghap}} per cent and the raw retrieval's {{claim:c1.step_raw_aod}} per cent, a
difference of {{claim:c1.fused_excess_pp}} points. The fused product's apparent value was satellite
information that a raw retrieval supplies equally well. The pre-registered prediction was the
opposite.

**The rungs above it.** On the redesigned discovery ladder, paired within city, the fused product
tilts the measured ordering toward the background series: the background-minus-first-two difference
is larger under the fused product (MAIAC minus GHAP, {{claim:v2.ghap.maiac_minus_ghap_bgm2.median}} points
[{{claim:v2.ghap.maiac_minus_ghap_bgm2.lo}}, {{claim:v2.ghap.maiac_minus_ghap_bgm2.hi}}], positive in
{{claim:v2.ghap.share_positive}} per cent of cities), and the background's own gain is larger with it. Whether it also lowers the value of the
first local stations is not resolved, because that paired difference excludes neither sign. An earlier
version of this work reported that the fused product roughly halved the measured value of a local
station, and concluded that contamination deflates the rung above the contaminated one rather than
inflating its own. That conclusion rested on a difference of medians from one station split, and it
is retired.

Two qualifications apply to what remains. The tilt is a statement about the registered rungs, which
use their stations differently ({{ref:s-like-for-like}}), so it describes how a monitor-trained
covariate shifts a comparison between a calibration and a same-day reading, not between two kinds of
observation. And the claim needs its boundary stated, which {{ref:s-position-literature-claims-novelty}}
states: that such products leak is known, and evaluation practice already guards against it
[@Just2020]. What this study adds is narrow. When the quantity being estimated is the marginal value
of an observation, contamination need not appear in the contaminated rung, where a test aimed at it
would look, and the registered test in this study looked there and found nothing. The practical rule
the thesis follows is simpler: a covariate meant to stand in for a city without monitors is taken from
a product that has seen no monitors.
