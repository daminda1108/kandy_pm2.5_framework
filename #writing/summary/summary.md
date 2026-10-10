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
reference-grade PM2.5 monitor in operation and two low-cost sensors with public records. Any PM2.5
field for Kandy is therefore a model output that almost no local observation can evaluate.

## Aim

To reconstruct PM2.5 over the Kandy basin at hourly and one-kilometre resolution for 2019 to 2023
from data available everywhere; to establish how far each part of that reconstruction can be
trusted; to determine the spatial scale below which it is no longer supported; and to identify the
measurements that would most improve it.

## The model

Concentration on the kilometre grid is a regional background, uniform across the city at any hour,
plus a local increment redistributed by a pattern of unit spatial mean:

$$\mathrm{PM}(x,y,t) = B(t) + \max(\Delta,0)\,P(x,y,t) + \min(\Delta,0) + \varepsilon(t)\,[P(x,y,t)-1], \qquad \Delta(t) = T(t) - B(t)$$

$T$, the basin-mean concentration, is a gradient-boosted model of the residual between the two local
sensors and a composition-model prior, driven by reanalysis meteorology and satellite retrievals,
shifted each year to a satellite-derived area mean and shaped to the sensors' daily and seasonal
cycles. $B$ is a regional-background estimate built from the same satellite level, the composition
model and an air-mass classification, capped so that it never reaches the hourly total. $P$ combines
a satellite surface, a terrain-confinement term and a road-traffic emission surface carried through a
terrain-steered dispersion step. The field averages to $T$ (to within {{claim:gauge.drift_hi_pct}}
per cent in practice), so misplacing material cannot create more of it, and each component declares
which observations it may use. The local increment is a residual of this decomposition, not the mass
emitted inside the city.

## Validation without local ground truth

The two Kandy sensors trained and shaped $T$, so they cannot validate it. Three other lines of
evidence are used, and their results are graded rather than combined. The complete model was built
in ten monitored valley and basin cities with only two anchor stations, as at Kandy, and scored
against withheld stations: the seasonal cycle transfers everywhere (correlation
{{claim:scorecard.seasonal_r_lo}} to {{claim:scorecard.seasonal_r_hi}}), the daily cycle unevenly
({{claim:scorecard.diurnal_r_lo}} to {{claim:scorecard.diurnal_r_hi}}). The deployed temporal model
was placed on a cross-city ladder of information budgets in {{claim:v2.km.cities_scored}} cities
(exploratory, specified before scoring): where its anchor stations observed the period it cut daily
error by {{claim:v2.km.reco.unio.gK2_rmse.median}} per cent against a generic sensorless estimate
(correlation {{claim:v2.km.reco.unio.K2_r.median}}); where they did not, by
{{claim:v2.km.pros.unio.gK2_rmse.median}} per cent, not distinguishable from zero. Its
satellite-derived level sat {{claim:v2.km.reco.unio.K2_bias.median}} per cent above the withheld city
means and its nominal 90 per cent interval covered a fraction
{{claim:v2.km.reco.unio.K2_cov90.median}}. At Kandy an independent national record differs from the
field by {{claim:nbro.diff_pct_2021}} and {{claim:nbro.diff_pct_2022}} per cent in two years, while
three low-cost records sit below it.

## The reconstructed field, and how far it can be trusted

The modelled annual basin mean is {{claim:kandy.mean_min}} to {{claim:kandy.mean_max}} micrograms per
cubic metre over 2019 to 2023, above the World Health Organization guideline of 5 in every year;
because the absolute level is unresolved, this describes the modelled field rather than an
established exposure. The seasonal cycle is the best-supported property, with the maximum in the
north-east monsoon ({{claim:kandy.season_djf}} in December to February of {{claim:exposure.year}}) and
the minimum in the south-west monsoon ({{claim:kandy.season_jja}}). The day-to-day sequence is
supported on days the sensors reported. Morning and evening peaks either side of a midday dip are
robust in timing, but their depth depends on the humidity correction of the sensor record: with
hourly rather than constant humidity the morning-peak-to-midday ratio falls from
{{claim:rh2.production.peak_trough}} to {{claim:rh2.hourly_rh.peak_trough}} and the night falls below
midday, while the level, the daily sequence and the local fraction barely move. The interval covers
{{claim:kandy.cov90}} per cent of sensor hours with misses almost all on one side, which points to a
calibration bias at the sensors rather than proving the width right. Under the baseline decomposition
the local increment is {{claim:partition.f}} of the modelled total, {{claim:v2.f.cap_min}} to
{{claim:v2.f.cap_max}} across the tested ways of applying the cap and {{claim:field.f_form_roll48}}
with a 48-hour background window: a property of the decomposition, not a source apportionment.

## What each additional observation is worth

Because every component declares its inputs, an observation can be withheld and the loss measured
across monitored cities. A registered confirmation on {{claim:v2.conf.n_cities}} fresh cities found
two stations used only to recalibrate a free estimate worth {{claim:v2.conf.reco.first2_rmse.median}}
per cent and a background series read daily worth {{claim:v2.conf.reco.bg_rmse.median}} per cent. A
later review showed the comparison was not like for like. In a post hoc re-analysis that used every
source on the day, one station read daily reduced daily error by {{claim:v2.review.k.day1.median}} per
cent, two by {{claim:v2.review.k.day2.median}} and five by {{claim:v2.review.k.day5.median}}, against
about {{claim:v2.review.k.cal2.median}} per cent for stations used only as a calibration, and no
ordering of station types was established. For Kandy the priority is continuously reporting stations
whose readings reach the estimate every day, with one of reference grade to settle the level and the
humidity correction.

## Limitations

The field is not supported below the kilometre scale. Two sites three hundred metres apart inside one
model cell differ in measured PM10 by a factor of {{claim:spatial.paired_obs_ratio}}, though on
different days, so the pair illustrates sub-grid variation without isolating location; on densely
monitored cities the spread inside a cell ({{claim:s2.within_pixel_p90p10}}) exceeds the spread
between cells ({{claim:s2.between_pixel_p90p10}}). The dispersion step meant to place the local
increment ranks held-out stations at {{claim:r2b.rho_C}}, below the undispersed surface
({{claim:r2b.rho_S}}) and a free built-up layer ({{claim:r2b.rho_BU}}), so it is a declared choice,
not a validated improvement, and three to eight stations do not rank neighbourhoods usefully either.
The map is a hypothesis for testing, not a ranking of neighbourhoods. The chemical check is a
consistency check within a composition model, not a chemical measurement at Kandy.

## Ongoing work and verification

The regulatory monitor at Kandy, once its record is released, will allow the level, the humidity
correction and the daily shape to be checked against a reference instrument. A fresh pre-registered
like-for-like test and an independent reproduction are the next steps for the cross-city results.
Every value in the report is regenerated from source at build time by a gate that refuses to build
when prose and data disagree (github.com/daminda1108/kandy_pm2.5_framework);
{{claim:meta.refuted}} registered predictions were refuted and are reported as such.

**Contact:** 11daminda08@gmail.com  ·  s20005@sci.pdn.ac.lk
