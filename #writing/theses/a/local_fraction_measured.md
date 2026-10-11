### The local fraction against measurements {#s-local-fraction-measured}

The local fraction of {{ref:s-partition-constraint-rather-than}} is a property of the decomposition, and no
instrument observes it directly. Two measurement routes come close enough to test it, and both became possible only
with the regulatory record of {{ref:s-cea-reference}} and the regional sensors served on the same platform. The analysis
was specified in writing, including the rule for judging the model, and committed to the version-control record
before any value was computed. It is exploratory. Each route is compared with the model computed in the same way, at
the station's cell and on the same days or hours, because a city-centre station is expected to carry more local
increment than the basin as a whole.

**Urban increment over the regional network.** The standard way to separate a city's own contribution is to subtract
a regional background measured outside it [@Lenschow2001]. The authority's platform serves daily records from
low-cost sensors at {{claim:lfs.e1.sites}} towns within 150 kilometres of Kandy. They were calibrated against the
reference monitor beside which one of them stands in Colombo (correlation {{claim:lfs.cal.r}} over
{{claim:lfs.cal.days}} days). On the {{claim:lfs.e1.days}} days from late 2024 on which Kandy and at least two regional
towns reported, the Kandy station exceeds the median of the towns by a local share of {{claim:lfs.e1med.f}}
({{claim:lfs.e1med.lo}} to {{claim:lfs.e1med.hi}}), and the cleanest town each day by {{claim:lfs.e1min.f}}
({{claim:lfs.e1min.lo}} to {{claim:lfs.e1min.hi}}). Every regional sensor is in a town with its own local emissions,
which this route counts as regional, so both values are lower bounds on Kandy's local share.

**Combustion-tracer intercept.** The regulatory station also measures carbon monoxide and nitrogen dioxide, which
come mainly from local combustion. This route is a separate diagnostic rather than an independent validation: its
particulate record for January 2019 to June 2021 is the one that sets the field's level ({{ref:s-cea-reference}}),
although the level factor corrects only the mean while this route uses the relation between particulate matter and
the tracers. Within each month the particulate concentration was regressed on the tracer, and the
level predicted at the tracer's background (its fifth percentile) was taken as the non-local part. Over
{{claim:lfs.e2.months}} months of 2019 to 2023 this gives a local share of {{claim:lfs.e2.co_p5.f}}
({{claim:lfs.e2.co_p5.lo}} to {{claim:lfs.e2.co_p5.hi}}) with carbon monoxide and {{claim:lfs.e2.no2_p5.f}} with
nitrogen dioxide, and {{claim:lfs.e2.co_p10.f}} with the tenth percentile as the background for either tracer. Its biases run
both ways: local dust and locally formed secondary aerosol do not follow the tracers and are counted as background,
while regional plumes that also carry the tracers change the slope, so it is an estimate with biases in both
directions, not an upper bound. Restricted to the station's record from October 2022, which was not used to fit the
level, the same estimator gives {{claim:lfs.e2.co_p5_heldout.f}} ({{claim:lfs.e2.co_p5_heldout.lo}} to
{{claim:lfs.e2.co_p5_heldout.hi}}) over {{claim:lfs.e2.heldout.months}} months, against
{{claim:lfs.model.e2_heldout_cell}} for the model on the same hours; this check was added after the specification, at
an external reviewer's suggestion.

{{tbl:T3_local_fraction}}

Two further records give context but not a bound. During the curfew of spring 2020 the station's concentration fell by
{{claim:lfs.e3.D}} ({{claim:lfs.e3.lo}} to {{claim:lfs.e3.hi}}) after adjustment for weather, against
{{claim:lfs.e3.raw}} unadjusted; that combines the local response with a regional one, because neighbouring countries
were also under restrictions, so it cannot isolate the local share. The source apportionment at Katugastota
[@Seneviratne2017] identifies about three tenths of fine mass as local primary sources, which is a floor, because the
model's increment also contains locally formed secondary material.

**What the measurements establish.** The two routes are not the ends of an identified interval. The urban
increment over the cleanest regional town, {{claim:lfs.e1min.f}}, is a lower-bound estimate. The tracer intercept,
{{claim:lfs.e2.co_p5.f}}, is a separate estimate whose biases run in both directions, so it does not bound the share
from above. The model gives {{claim:lfs.model.e2_cell}} at the station's cell on the tracer route's hours and
{{claim:lfs.model.ext_cell}} on the urban-increment days: it is broadly consistent with the tracer estimate, and the
urban-increment comparison indicates that it may be high. Under the
rule fixed in advance, the model is classed as high against the urban-increment route; that route's known bias runs in
the direction that would explain the gap, and the tracer route agrees with the model. The basin value of {{claim:partition.f}} is therefore
plausible but not established, and may be somewhat high. An exact value would need a
reference monitor at a clean rural site upwind of Kandy, which no public network provides.
