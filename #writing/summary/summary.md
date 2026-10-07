---
title: "An hourly kilometre-scale fine particulate matter reconstruction for Kandy, Sri Lanka: construction, validation without local ground truth, and measurement priorities"
author: "A. M. D. W. B. Alahakoon, Department of Environmental and Industrial Sciences, University of Peradeniya, Sri Lanka"
date: "2026"
geometry: margin=1.0cm
fontsize: 12pt
mainfont: "Times New Roman"
sansfont: "Times New Roman"
monofont: "Times New Roman"
colorlinks: false
header-includes: |
  \usepackage{titling}
  \setlength{\droptitle}{-1.75cm}
  \pretitle{\begin{center}\large\bfseries}
  \posttitle{\par\end{center}\vspace{0.35em}}
  \preauthor{\begin{center}\normalsize}
  \postauthor{\par\end{center}\vspace{0.1em}}
  \predate{\begin{center}\normalsize}
  \postdate{\par\end{center}\vspace{0.35em}}
  \usepackage{titlesec}
  \titlespacing*{\section}{0pt}{0.18em}{0.06em}
  \setlength{\parskip}{0.06em}
  \linespread{0.90}
  \setlength{\parindent}{0pt}
---

**Undergraduate research project report (ENS4998), 2026.** The report runs to
{{claim:meta.words}} words, {{claim:meta.figures}} figures and {{claim:meta.tables}} tables, and
rests on {{claim:meta.registrations}} pre-registrations lodged before the analyses they cover.

## The problem

Fine particulate matter (PM2.5) carries the largest estimated burden of disease of any air
pollutant, and monitoring is sparsest where concentrations are highest. Kandy is such a city: a
valley settlement in the central highlands of Sri Lanka with 98,828 residents inside its municipal
boundary (2012 census) and nearly 389,000 commuters entering on a typical weekday (World Bank,
2020), so that most of those exposed to its air during the day do not live in it. It has no
reference-grade PM2.5 monitor in operation and two low-cost sensors with public records. Estimating
surface PM2.5 where it is not measured is harder than estimating the meteorological state: the
observing network is thin, emissions are poorly quantified and independent inventories disagree,
and a substantial fraction of the mass forms in the atmosphere rather than being emitted. Any PM2.5
field for Kandy is therefore a model output that almost no local observation can evaluate.

## Aim

To reconstruct PM2.5 over the Kandy basin at hourly and one-kilometre resolution for 2019 to 2023
from data available everywhere; to establish what that reconstruction can and cannot be trusted to
say; to determine the spatial scale below which it is no longer supported; and to rank the
measurements that would most improve it.

## What was tried first, and why it was abandoned

The work began as a machine-learning problem: learn the city-mean level from satellite and
reanalysis data, and learn the within-city spatial pattern from cities that have dense networks. The
second half did not survive testing. A cross-city neural model produced fields that were defensible
in aggregate but spatially featureless; fine-tuning it on Kandy's two sensors reproduced those two
points almost exactly while inflating the rest of the grid, having learned the sensor coordinates
rather than the basin; a physics-informed network transferred between two distant cities but never
became a usable component; five successive rebuilds of the regional background were each rejected
against their own criteria; and a terrain-steered dispersion step, built specifically to place the
local increment, was found to lower the ranking of neighbourhoods from
{{claim:r2.rho_emission_surface}} to {{claim:r2.rho_with_atransport}} and is not used. Eight such
approaches are documented in full, with what each one still established. Their common lesson set
the design that followed: the information needed to place pollution inside a city is not present in
the data available for a city like Kandy, so it must be imposed from physical reasoning and
declared as an assumption rather than fitted and presented as a result.

## The model

Concentration on the kilometre grid is represented as a regional background, spatially uniform at
any hour, plus a locally generated increment redistributed by a pattern of unit spatial mean:

$$\mathrm{PM}(x,y,t) = B(t) + \max(\Delta,0)\,P(x,y,t) + \min(\Delta,0) + \varepsilon(t)\,[P(x,y,t)-1], \qquad \Delta(t) = T(t) - B(t)$$

$T$, the basin-mean concentration, is a gradient-boosted model over reanalysis meteorology,
re-anchored annually to a satellite-derived mean and shaped to the cycles of the two local sensors;
$B$ is a rural floor with a seasonal shape; $P$ combines an emission proxy with a
terrain-confinement term. Two properties follow by construction: the field averages to $T$, so
misplacing material cannot create more of it, and each component declares which observations it may
use, so withholding a data source reproduces the corresponding simpler model exactly. That second
property is what turns the model into an instrument for measuring the worth of an observation.

Because Kandy cannot evaluate its own field, the construction was tested on monitored valley and
basin cities by withholding their observations and supplying only the data Kandy has. Across ten
cities the seasonal cycle transfers well (correlations {{claim:scorecard.seasonal_r_lo}} to
{{claim:scorecard.seasonal_r_hi}}), the daily cycle transfers unevenly
({{claim:scorecard.diurnal_r_lo}} to {{claim:scorecard.diurnal_r_hi}}), and the median absolute
level error is {{claim:scorecard.level_bias_median}} per cent. What transfers is the procedure;
applying it to Kandy is an argument from resemblance, since Kandy is by construction the kind of
city the test set excludes.

## The reconstructed field, and what the checks at Kandy show

The annual basin mean ranges from {{claim:kandy.mean_min}} to {{claim:kandy.mean_max}} micrograms
per cubic metre over 2019 to 2023, above the World Health Organization annual guideline of 5 in
every year. In {{claim:exposure.year}} it is {{claim:kandy.season_djf}} in December to February and
{{claim:kandy.season_jja}} in June to August, the maximum falling in the north-east monsoon.
Concentrations peak in the morning ({{claim:kandy.phase_morning}}) and evening
({{claim:kandy.phase_evening}}) about a midday minimum ({{claim:kandy.phase_midday}}), with night
values {{claim:kandy.night_over_midday}} times the midday level. In a regional episode in December
2022 the basin mean averaged {{claim:kandy.episode_mean}} and peaked at
{{claim:kandy.episode_peak}}, the whole domain rising together. Under the stated assumptions the
decomposition assigns {{claim:partition.f}} of the concentration to the local increment. That share
is a bound set by a physical constraint, that local sources emit at every hour, and it ranges from
{{claim:v2.f.cap_min}} to {{claim:v2.f.cap_max}} across reasonable forms of the constraint; it is a
constrained split, not a source apportionment.
Weighting by residential population raises exposure {{claim:exposure.uplift_pct}} per cent above the
area mean. The timing is supported by an independent national record, which differs from the field
by {{claim:nbro.diff_pct_2021}} and {{claim:nbro.diff_pct_2022}} per cent in two separate years. The
absolute level remains open: three low-cost records sit below the field, each carrying a downward
calibration correction, and the discrepancy is reported rather than resolved. The uncertainty
intervals are of the right width but wrongly centred, covering {{claim:kandy.cov90}} per cent of
hours at the two sensors and {{claim:kandy.cov90_recentred}} per cent once each sensor's own offset
is removed, because the field is an areal mean and a sensor is a point.

## What each additional observation is worth

Because every component declares its inputs, an observation can be withheld and the loss measured.
The design was developed on {{claim:frame.cities}} monitored cities and then tested once on
{{claim:v2.conf.n_cities}} fresh cities registered before their data were retrieved. Two stations
used only to recalibrate the free estimate reduced daily error by
{{claim:v2.conf.reco.first2_rmse.median}} per cent; a background series read day by day reduced it by
{{claim:v2.conf.reco.bg_rmse.median}} per cent; both held under a richer free baseline, other learners
and full station networks. A later review of the design found that this comparison was not like for
like. Read on the day, two stations of any kind reduced error by
{{claim:v2.review.registered_loco.reco.gL2s_rmse.median}} per cent and the background's advantage
vanished ({{claim:v2.review.registered_loco.reco.BGallmL2s_rmse.median}} points). One station read
daily is worth {{claim:v2.review.k.day1.median}} per cent, two {{claim:v2.review.k.day2.median}} and
five {{claim:v2.review.k.day5.median}}, against about {{claim:v2.review.k.cal2.median}} per cent for any
number used only as a calibration. For Kandy the priority is therefore continuous stations whose
readings reach the estimate every day, of whatever kind the regulatory agencies operate, with one of
reference grade to fix the absolute level and to anchor every low-cost sensor deployed thereafter.

## Limitations

The field is not supported below the kilometre scale. Two Kandy sites three hundred metres apart
differ in measured PM10 by a factor of {{claim:spatial.paired_obs_ratio}} while falling within one
model cell, and on cities with dense networks the spread inside a single cell
({{claim:s2.within_pixel_p90p10}}) exceeds the spread between cells
({{claim:s2.between_pixel_p90p10}}). A further {{claim:tour.families}} model families built on free
covariates exceed a single land-cover layer ({{claim:phase1.best_rho}}) by no more than the
detection limit of {{claim:phase1.min_detectable}}. A registered experiment adding stations one at a
time found that three to eight stations rank neighbourhoods no better than free surfaces, and after a
correction for multiple testing interpolation clearly overtook a land-cover layer in only
{{claim:v2.curve.full.holm_crossing}} of 23 cities. The limitation is one of available information,
not of the model class chosen. The study therefore claims neither a validated neighbourhood-scale
map, nor a representation of atmospheric chemistry, nor an independently validated absolute level
at Kandy: what is validated is a procedure, tested on monitored cities and applied to Kandy by
analogy.

## Ongoing work and verification

Three strands continue. The regulatory monitor at Kandy, once its data are released, will allow the
level, the humidity correction of the low-cost sensors and the daily shape to be checked against a
reference instrument. Four institutional data requests are in progress, of which two have
been answered, one granting access in principle subject to a formal agreement. A measurement
campaign for Kandy has been designed, costed and pre-registered, but remains under development and
is not presented here as a recommendation. Every value in the report is regenerated from source at
build time by a gate that refuses to build when prose and data disagree, and predictions were
pre-registered before each analysis: {{claim:meta.refuted}} registered predictions were refuted.

**Contact:** 11daminda08@gmail.com  ·  s20005@sci.pdn.ac.lk
