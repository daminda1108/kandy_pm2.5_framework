::: {custom-style="Title Page Title"}
AN HOURLY KILOMETRE-SCALE FINE PARTICULATE MATTER RECONSTRUCTION FOR KANDY, SRI LANKA: CONSTRUCTION, VALIDATION WITHOUT LOCAL GROUND TRUTH, AND MEASUREMENT PRIORITIES
:::

::: {custom-style="Title Page Text"}
An undergraduate research project report submitted by
:::

::: {custom-style="Title Page Name"}
A. M. D. W. B. Alahakoon
:::

::: {custom-style="Title Page Name"}
(S/20/005)
:::

::: {custom-style="Title Page Text"}
to Department of Environmental and Industrial Sciences

Faculty of Science

University of Peradeniya

In partial fulfilment of
:::

::: {custom-style="Title Page Bold"}
B.Sc. Degree (Honours) in Environmental Science,

University of Peradeniya,

Sri Lanka

2026
:::

{{section:front}}

{{include:pool/front/declaration.md}}

# Abstract {.front}

::: {custom-style="Abstract Text"}
Kandy, a valley city in Sri Lanka's central highlands with about 99,000 residents and nearly 389,000 weekday commuters, has no publicly reporting reference monitor for fine particulate matter (PM2.5) and two low-cost sensors. This study reconstructs PM2.5 over the Kandy basin hourly at one kilometre for 2019 to 2023 from satellite retrievals, reanalysis meteorology and free geography, and asks what such a field can be trusted to say. The field is a uniform regional background plus a local increment carrying all spatial structure, with a fixed city-wide average. The annual basin mean, {{claim:kandy.mean_min}} to {{claim:kandy.mean_max}} micrograms per cubic metre, exceeds the World Health Organization guideline every year, peaking in the north-east monsoon and in the morning and evening. Without local ground truth, the field is validated three ways. The construction is scored on {{claim:scorecard.cities}} monitored valley and basin cities by withholding their own observations. The deployed temporal model, placed on a cross-city ladder of information budgets in {{claim:v2.km.cities_scored}} cities, reduces daily error by {{claim:v2.km.reco.unio.gK2_rmse.median}} per cent against a generic sensorless estimate where its two anchor stations observed the period, but not where they did not. At Kandy a national record agrees to within {{claim:nbro.diff_pct_2021}} and {{claim:nbro.diff_pct_2022}} per cent in two years, while three low-cost records sit below the field, so the absolute level remains open. The spatial pattern is imposed, not measured: more within-city variation lies inside a cell than between cells, and no free covariate places it. The local share, {{claim:partition.f}}, is a bound under a non-negativity constraint ({{claim:v2.f.cap_min}} to {{claim:v2.f.cap_max}}), not a source apportionment. The same ladder ranks measurements. A station's value to a daily city-mean estimate lies in its reading reaching the estimate every day: one station read daily reduces daily error by {{claim:v2.review.k.day1.median}} per cent and two by {{claim:v2.review.k.day2.median}} per cent, against {{claim:v2.review.k.cal2.median}} per cent when the same stations only calibrate the estimate. A handful of stations of any kind fixes the level and the daily sequence, not a neighbourhood map. For Kandy this favours continuously reporting stations read daily; a reference-grade instrument among them would also settle the level.
:::

{{include:pool/front/acknowledgements.md}}

{{section:body}}

# Table of Contents {.front}

{{toc}}

# List of Figures {.front}

{{listoffigures}}

# List of Tables {.front}

{{listoftables}}

{{include:pool/front/abbreviations.md}}

{{include:pool/front/symbols.md}}
