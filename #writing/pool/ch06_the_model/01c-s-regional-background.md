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

The resulting background averages {{claim:partition.B_mean}} micrograms per cubic metre over the
anchored years, from {{claim:partition.B_2021}} in 2021 to {{claim:partition.B_2023}} in 2023. Because the background is uniform and the pattern has unit mean,
every choice made in building it changes the **division** of the field into regional and local
parts, and none of them changes the field's city mean, which is fixed by *T*(*t*).

**The daily series against the regional network.** The background's day-to-day variation has one
direct check. The regulatory agency's network carries low-cost units in {{claim:bgr.n_sites}} towns
within 150 kilometres of Kandy outside the Colombo area, calibrated against the reference monitor
they share a site with near Colombo ({{ref:s-local-fraction-measured}}). They report only from
mid-2024, after the delivered years, so what can be scored is the construction above applied to 2024
and 2025, not the delivered series itself. Against the towns' daily median the constructed
background correlates at {{claim:bgr.bmeth.r}} ({{claim:bgr.bmeth.r_lo}} to {{claim:bgr.bmeth.r_hi}},
{{claim:bgr.bmeth.days}} days), and at {{claim:bgr.bmeth.anom}} ({{claim:bgr.bmeth.anom_lo}} to
{{claim:bgr.bmeth.anom_hi}}) once each month's mean is removed, against {{claim:bgr.kst.anom}} for the
Kandy regulatory station itself. The background therefore carries a real share of the regional
day-to-day signal, but less of it than Kandy's own air shares with the region. All of that share comes
from the composition prior, which scores the same alone ({{claim:bgr.geos.anom}}), so the air-mass
classification adds nothing measurable to the daily sequence; its role is the level of marine days.
The towns are themselves small urban areas, so their level is not the background's, and only the
correlations are read. The check was made after the other results, with its reading written down
before it was scored.
