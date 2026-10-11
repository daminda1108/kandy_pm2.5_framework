## The checks at Kandy that carry weight, and the ones that do not {#s-checks-kandy-carry-weight}

**The two local sensors cannot validate this model**, and the reason is structural rather than a
matter of degree. They enter the model three times: the temporal anchor is trained on their
residual, the width of its conformal interval is set from them, and it is then amplitude-sharpened
to their observed swing. The satellite surface of van Donkelaar sets both the annual level and the
background. Agreement with any of these inputs measures the calibration and not skill. The global
satellite product used as a level cross-check is quasi-independent, since it draws on overlapping
inputs. The records that are independent of all of them are the regional station series and a
published neural-network record, and the regional series is the one used below as a check on the
field.

{{fig:cycles}}

The comparison is shown for completeness, at a seasonal correlation of
{{claim:kandy.cycles_seasonal_r}} and a diurnal correlation of
{{claim:kandy.cycles_diurnal_r}}, and those numbers should be read as confirming that the
calibration was applied rather than as evidence that the model works.

**Three records do carry weight.** Two of them are independent of the model in both directions: the
national research organisation's station and a calibrated low-cost record. The third, the regulatory
station in the city centre ({{ref:s-cea-reference}}), is independent only for its record after June
2021: its earlier record sets the field's level.

{{tbl:T3_2}}

The published record from the national research organisation gives annual means at a site that is
neither of the two sensors. The model at that cell reads {{claim:nbro.model_pixel_2021}} in the first year, a
difference of {{claim:nbro.diff_pct_2021}} per cent from the observed annual mean, and
{{claim:nbro.model_pixel_2022}} in the second, a difference of {{claim:nbro.diff_pct_2022}} per
cent: the field sits below this record in both years. The field before the dispersion step was
removed ({{ref:s-spatial-pattern}}) placed more of the local increment in the city core, where the
station is, and matched these annual means more closely; at this one site the dispersion step
helped, whereas across ten monitored cities it lowered agreement with held-out stations, and the
delivered field follows the larger test.

An off-the-shelf alternative gives the comparison a baseline. The global satellite-derived surface
of Wei and colleagues [@Wei2023], read at the same cell, also sits below the observed annual mean in
both years. The field at the satellite level was closer to this record than that free product; the
re-anchored field is further below it, because the re-anchoring follows the regulatory station
({{ref:s-cea-reference}}), which reads lower than this record. The two Kandy records therefore
disagree with each other by more than either disagrees with the model. This one is a single site and
two years, from an instrument whose type is not documented
(the network's present Kandy unit also reports carbon dioxide and fine-mode counts, which suggests
a multi-sensor instrument), and it is a comparison of levels rather than of spatial skill.

The reason that comparison is genuinely external deserves stating rather than asserting. The
anchor is calibrated to the two low-cost sensors, so the model's basin **mean** is not
independent of Kandy observations. The spatial pattern is independent, because it is an emission
proxy multiplied by a confinement term, both imposed and neither fitted to anything measured in
this city. What the comparison therefore tests is the **lift**, meaning how far the field rises
from the basin mean to that particular cell, and the lift is {{claim:nbro.lift_pct_2021}} per
cent in the first year and {{claim:nbro.lift_pct_2022}} per cent in the second. Had the lift been
near zero the comparison would have collapsed into a check on the anchor and carried no spatial
information at all. The station sits {{claim:nbro.station_offset_km}} kilometres from the centre
of the cell it falls in, so the pairing is not marginal.

**The level at Kandy, as first built, was too high.** With the level taken from the satellite
surface, the regulatory station ({{ref:s-cea-reference}}) sat {{claim:cea.sat.all.bias_pct}} per cent
below the model and the national research organisation's record above it. The delivered field is
re-anchored to the regulatory station, after which the calibrated low-cost record differs from it
by {{claim:attan.diff_pct}} per cent. Only the last has an undocumented
instrument, and only the first is a regulatory monitor. The interval coverage at the two local sensors still points the same way after the re-anchoring: when observations fall outside the interval they fall below it in
{{claim:kandy.miss_below}} per cent of hours and above it in only {{claim:kandy.miss_above}} per cent
({{ref:s-interval-calibration}}).

Two readings remain possible. The first is a change of support: the field is an area mean, the
records are points, and points may sit below the cell they fall in. That is harder to sustain at a
station in the city centre, where the cell is among the highest in the basin. The second is an
upward bias in the level the field inherits from the satellite surface, which in the tropical
cities of the panel overstates the mean of withheld stations by a median of
{{claim:lvl.tropical.bias_p50}} per cent and by {{claim:lvl.tropical.bias_p75}} per cent or more in a
quarter of them ({{ref:s-kandy-field-level}}); an excess of the size seen at the regulatory station
is therefore not unusual. The station's comparison with the corrected low-cost record favours the second
({{ref:s-cea-reference}}), and the level was re-anchored at that step with a check on years not used
for the fit. A single station still cannot separate a level bias from a local siting effect, and its
method and siting are undocumented, so the delivered level is as good as that one station. A co-located reference
monitor with documented siting would settle the level, and the hourly record of the same station
bears on the diurnal shape ({{ref:s-rh-scenario}}).
