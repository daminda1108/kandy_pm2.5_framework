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

**Two records do carry weight**, because the model played no part in producing them and they
played no part in producing the model.

{{tbl:T3_2}}

The published record from the national research organisation gives annual means at a site that is
neither of the two sensors. The model at that cell reads {{claim:nbro.model_pixel_2021}} in the first year, a
difference of {{claim:nbro.diff_pct_2021}} per cent from the observed annual mean, and
{{claim:nbro.model_pixel_2022}} in the second, a difference of {{claim:nbro.diff_pct_2022}} per
cent.

An off-the-shelf alternative gives the comparison a baseline. The global satellite-derived surface
of Wei and colleagues [@Wei2023], read at the same cell, sits below the observed annual mean in
both years and by clearly more than the model does, so at the one reference-like record available
the constructed field is closer to the observation than the free product it could have been
replaced with. That is one site and two years, from an instrument whose type is not documented,
and it is a comparison of levels rather than of spatial skill.

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

**A level question remains open and is not resolved here.** Of four independent point records
at Kandy, three sit below the model and one matches it. The three low ones are all low-cost sensors
carrying a downward calibration correction; the one that matches has an undocumented instrument.
The interval coverage at the two local sensors points the same way: when observations fall outside
the interval they fall below it in {{claim:kandy.miss_below}} per cent of hours and above it in
only {{claim:kandy.miss_above}} per cent ({{ref:s-interval-calibration}}).

Two readings fit this pattern. The first is a change of support: the field is an area mean, the
records are points, and low-cost points may sit systematically below the cell they fall in. The
second is an upward level bias in the model at these points, and the external review of the chain
read the one-sided coverage together with the three low records as evidence for it. A candidate
mechanism is the humidity correction of the sensor record, which used a constant relative
humidity; recomputed with hourly humidity, the ratio of the normalised morning peak to the
afternoon trough falls from {{claim:v2.rh.constant_rh80.peak_to_trough}} to
{{claim:v2.rh.barkjohn_hourly_rh.peak_to_trough}}, which changes the diurnal shape imposed on the
anchor. The record that matches the model argues against a general bias, and it is the only one
not from a low-cost sensor. This is a level question on the axis this thesis calls well
supported, and it is stated as open rather than settled by choosing the record that agrees. A
co-located reference monitor would settle both the level and the diurnal shape.
