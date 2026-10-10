## The regional background {#s-regional-background}

The background *B*(*t*) is the part of the concentration that arrives from outside the basin. It
is uniform across the domain ({{ref:s-uniform-background-assumption}}) and has daily resolution,
broadcast to every hour of the day. It is built in three steps.

**An annual level.** Each year's background mean is a fraction of the same satellite area level
that anchors *T*(*t*). That fraction was first taken from source-apportionment studies of South
Asian cities and of Kandy itself [@Seneviratne2017], which place the regional contribution at
roughly three quarters. It is only a starting value: the constraint in the next step
lowers the background wherever it is inconsistent with the hourly total, and it is that
constraint, not the literature value, that sets the local fraction reported in
{{ref:s-partition-constraint-rather-than}}.

**A daily series conditioned on air-mass origin.** Back-trajectories at 850 hPa classify each
six-hourly arrival as marine or continental. Marine arrivals, which have crossed open ocean,
take a fixed clean floor ({{ref:app-constants-configuration}} lists the value); the continental level is then solved so
that the annual mean of the background is preserved exactly. Within each class, the day-to-day
variation follows the daily mean of the composition prior over the basin, normalised to unit
mean within the class. The background therefore rises on days when the composition model sees
regional pollution arriving, and falls on marine days, without its annual mean moving.

**A cap from the hourly total.** The background may never reach the total. Each day it is capped
at a fixed fraction just below that day's lowest hourly value of *T*(*t*). The reasoning, the
consequence for the local fraction and the sensitivity of the result to how the cap is defined
are given in {{ref:s-partition-constraint-rather-than}}.

The resulting background averages {{claim:kandy.background_annual}} micrograms per cubic metre
across the anchored years. Because the background is uniform and the pattern has unit mean,
every choice made in building it changes the **division** of the field into regional and local
parts, and none of them changes the field's city mean, which is fixed by *T*(*t*).
