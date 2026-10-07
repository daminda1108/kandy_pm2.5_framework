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
Kandy, a valley city in Sri Lanka's central highlands with about 99,000 residents and nearly 389,000 weekday commuters, has no publicly reporting reference monitor for fine particulate matter (PM2.5) and two low-cost sensors. This study reconstructs PM2.5 over the Kandy basin at hourly and one-kilometre resolution for 2019 to 2023 from satellite retrievals, reanalysis meteorology and free geography, and asks what such a field can be trusted to say where it cannot be checked. The field is a regional background, uniform across the city, plus a local increment that carries all spatial structure and whose city-wide average is fixed. The annual basin mean runs from {{claim:kandy.mean_min}} to {{claim:kandy.mean_max}} micrograms per cubic metre, above the World Health Organization guideline every year, with a north-east monsoon maximum and morning and evening peaks above a midday trough. Without local ground truth, the construction is scored on {{claim:scorecard.cities}} monitored valley and basin cities by withholding their own observations, and the field is compared with every independent Kandy record: a national record agrees to within {{claim:nbro.diff_pct_2021}} and {{claim:nbro.diff_pct_2022}} per cent in two years, while three low-cost records sit below the field, so the absolute level remains open. The spatial pattern is imposed, not measured: more within-city variation lies inside a cell than between cells, and no free covariate places it. The share assigned to the local increment, {{claim:partition.f}}, is a bound under a non-negativity constraint, {{claim:v2.f.cap_min}} to {{claim:v2.f.cap_max}} across forms of that constraint, not a source apportionment. Measurement priorities come from a cross-city measurement of what each observation is worth. A station's value to a daily city-mean estimate lies in its reading reaching the estimate every day: one station read daily reduces daily error by {{claim:v2.review.k.day1.median}} per cent and two by {{claim:v2.review.k.day2.median}} per cent, against {{claim:v2.review.k.cal2.median}} per cent when the same stations only calibrate the estimate. The kind of station hardly matters, and a handful of stations fixes the level and the daily sequence, not a neighbourhood map. For Kandy this favours continuously reporting stations read daily; a reference-grade instrument among them would also settle the level.
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
