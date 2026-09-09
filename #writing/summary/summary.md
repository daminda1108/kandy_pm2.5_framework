---
title: "An information-tiered decomposition for hourly kilometre-scale urban PM2.5: what it reconstructs, and what each further observation is worth, demonstrated at Kandy"
author: "Daminda Alahakoon, University of Peradeniya, Sri Lanka"
date: "2026"
geometry: margin=1.25cm
fontsize: 12pt
mainfont: "Times New Roman"
sansfont: "Times New Roman"
monofont: "Times New Roman"
colorlinks: false
header-includes: |
  \usepackage{titling}
  \setlength{\droptitle}{-1.6cm}
  \pretitle{\begin{center}\large\bfseries}
  \posttitle{\par\end{center}\vspace{-0.8em}}
  \preauthor{\begin{center}\normalsize}
  \postauthor{\par\end{center}\vspace{-0.9em}}
  \predate{\begin{center}\normalsize}
  \postdate{\par\end{center}}
  \usepackage{titlesec}
  \titlespacing*{\section}{0pt}{0.45em}{0.15em}
  \setlength{\parskip}{0.18em}
  \linespread{0.95}
  \setlength{\parindent}{0pt}
---

**Undergraduate thesis, 2026.** Full thesis: 40,000 words, 35 figures, 10 chapters, with eight OSF
pre-registrations lodged before the corresponding analyses were run.

## The problem

Most of the world's population breathes air nobody measures, and the shortage of instruments is
worst where the air is dirtiest. Models fill the gap, and they are good. But they are tested where
monitors are dense and then used where monitors are absent, so **the one transfer that matters is
the one that cannot be scored**, and the usual answer to that doubt needs exactly the measurements
whose absence created it.

This thesis changes the question. Instead of asking how accurate a model is where its accuracy
cannot be checked, it asks what the model may claim from the data it already has, then measures
what each further source of data would be worth. Worth is defined concretely: how
much the model's day-to-day error falls when that source is added, at a fixed point in a fixed
order of adding them. This is a practical stand-in for value rather than a formal
decision-theoretic calculation, and the thesis says so.

## How the model is built

Concentration is split in two: a regional background that is the same everywhere in the city at any
given hour, and a local increment on top of it that varies from place to place. Two design choices
make the measurement possible.

**Conservation.** The map's spatial average always equals the city-wide estimate. If the model
puts pollution in the wrong neighbourhood it cannot also invent more of it, so being wrong about
location has a bounded cost.

**Exact removal.** The model is built in tiers, each told which data sources it may use. Taking a
source away reproduces the simpler tier exactly rather than approximately, because the model and
the fitting procedure stay fixed and only the data changes. The gap between two tiers is therefore
the effect of that data, not of having quietly changed the model as well.

## Three results

Measured across **{{claim:frame.cities}} cities in {{claim:frame.countries}} countries and
{{claim:frame.city_days}} city-days**, each scored against monitors kept out of its own fit. Every
panel city is a valley or basin publishing enough data to be scored, so the findings are bounded by
that panel.

**1. Free data is worth about as much as the first monitor a city buys.** Terrain, roads, land
cover, night lights and population are free and available anywhere, and together they cut daily
error by {{claim:step.geography}} per cent. The third through sixth monitors cut it by
{{claim:step.bud1_bud2}} per cent, which is not a small effect but an absent one, and it is the
finding that survives best when the learning algorithm is changed. Counting from one station up to
eight shows the saturation arriving earlier still: the first station buys {{claim:stn.one_gain}}
per cent and the second adds {{claim:stn.second_adds}} points.

The largest single gain comes from elsewhere. A background series measured outside
the urban core cuts error by {{claim:step.bud2_bud3}} per cent, and it is the instrument air
quality programmes are least likely to fund. That series is a stand-in, built from each city's own
outermost monitors rather than a true rural station, so it was rebuilt using a donor city the
target never sees. An independent network recovers {{claim:donor.gain_reproduced_pct}} per cent of
the gain, falling to {{claim:donor.reproduced_deep_tropical}} per cent in the group Kandy belongs
to. What that establishes is that a background measurement carries real transferable information,
not that a rural station would deliver this particular figure at Kandy. Two cautions apply to all
of these figures: each is what a source is worth at one position in one order of adding them, and
the cities are not independent, since {{claim:clust.largest_n}} share a national network.
Resampling whole networks widens every interval by about half again and changes no conclusion.

**2. The right advice flips between climate zones.** In the deep tropics, two local sensors cut
error by {{claim:maiac.deep_tropical_first2}} per cent against
{{claim:maiac.deep_tropical_background}} per cent for the background series, reversing the order
found by pooling all cities together. Comparing the two within each city and resampling over
cities, the advantage is {{claim:inv.maiac.median}} points
[{{claim:inv.maiac.lo}}, {{claim:inv.maiac.hi}}], favouring sensors in
{{claim:inv.maiac.frac_cities}} per cent of that group. A programme following the pooled advice
would buy the wrong instrument first. The defensible version is narrow: within this panel, local
measurements beat the background stand-in in the tropical group, and how much of that reflects the
atmosphere rather than the instruments used there is unresolved. The group holds thirteen cities,
instrument type is closely tied to latitude, and this comparison was not pre-registered.

**3. A satellite product trained on monitors hides what monitors are worth, and not where anyone
would look for it.** Swapping a published product that had itself been fitted to ground monitors
for a raw satellite retrieval barely moved the satellite's own contribution,
{{claim:c1.step_fused_ghap}} against {{claim:c1.step_raw_aod}} per cent, but roughly doubled the
step above it. **The contamination does not inflate the step it sits in. It deflates the step
above.** A pre-registered test looking for extra skill inside the contaminated stream found none
and would have called the problem harmless, because the signal had moved rather than grown. On the
contaminated product the reversal in result 2 measures {{claim:inv.ghap.median}} points with an
interval spanning zero, so the contamination had not shifted that finding, it had erased it.

## Where the model stops, and why that is itself a result

Two survey sites three hundred metres apart fall inside a single model cell. Measured, they differ
by a factor of {{claim:spatial.paired_obs_ratio}}. The model says they are identical, because it is
being asked about the same pixel twice. The obvious explanation is a grid that is too coarse, and a
pre-registered test **refuted** it: making the cells ten times finer moves the ratio by
{{claim:s1.paired_delta_on_refinement}}. The variation lives inside cells rather than between them.
Across the whole map, the spread within a typical cell,
{{claim:s2.within_pixel_p90p10}}, is larger than the spread between cells,
{{claim:s2.between_pixel_p90p10}}. No kilometre-scale product can say which part of a cell is
worst, however it is built. What it can honestly report is the range a cell spans, which is the
larger quantity and one that no gridded product currently publishes.

That limit was then tested rather than asserted. A learned spatial pattern was run with the
benchmark, the detection limit and the pass mark all fixed before the model was written: benchmark {{claim:phase1.best_rho}}, smallest effect the
experiment could detect {{claim:phase1.min_detectable}}, pass mark {{claim:phase2.bar}}. It reached
{{claim:phase2.rho_learned}}. This is the sixth negative result on the question in this project and
the first where the detection limit was fixed beforehand, so it bounds the answer instead of merely
reporting an absence. The previous five could only have detected effects of
{{claim:null.min_detectable_lo}} to {{claim:null.min_detectable_hi}}, which is why they said
nothing. {{claim:tour.families}} further model families were then run on the same data, among them
conventional land-use regression, a Gaussian process and a mixed model, and none beats the
benchmark by more than the detection limit. Kriging and geographically weighted regression need
measurements at the target city, and score below it even when handed that city's own stations. The
limit belongs to the available information, not to one family of models.

## Demonstration

Kandy, Sri Lanka: a valley city of 400,000 with two low-cost sensors and no working reference
monitor. Under the stated assumptions the model assigns **{{claim:partition.f}}** of concentration
to the local increment, fixed by a physical constraint rather than assumed and against an earlier,
now retired figure of about a quarter. It moves between {{claim:field.f_form_calendar}} and
{{claim:field.f_form_roll48}} depending on how the background window is defined. This is a split
imposed by the model, not a measurement of sources: the
increment is the part that varies across the map, which is not the same as material emitted inside
Kandy, and the model has no chemistry that could tell them apart. Against two published records
that played no part in building it, the field agrees to {{claim:nbro.diff_pct_2021}} and
{{claim:nbro.diff_pct_2022}} per cent in two separate years. Those checks cover the city-wide level
only: the model's timing is calibrated against Kandy's own sensors, so they test the modelled
variation on top of an already anchored average, not the whole field.
**The neighbourhood-scale map is not validated, and this thesis does not claim that it is**, for
the reason the previous section gives.

## How the work is done, and where it stands

Every number is regenerated from its source file when the document is built, and the build fails if
the prose and the data disagree. Writing the thesis moved eleven recorded quantities, four of which
made the argument weaker and were kept anyway. Eight pre-registrations, fourteen of thirty
predictions refuted, and one chapter on eight approaches that did not work.

**Contact:** 11daminda08@gmail.com  ·  s20005@sci.pdn.ac.lk
