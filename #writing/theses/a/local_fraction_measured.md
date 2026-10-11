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
come mainly from local combustion. Within each month the particulate concentration was regressed on the tracer, and the
level predicted at the tracer's background (its fifth percentile) was taken as the non-local part. Over
{{claim:lfs.e2.months}} months of 2019 to 2023 this gives a local share of {{claim:lfs.e2.co_p5.f}}
({{claim:lfs.e2.co_p5.lo}} to {{claim:lfs.e2.co_p5.hi}}) with carbon monoxide and {{claim:lfs.e2.no2_p5.f}} with
nitrogen dioxide, and {{claim:lfs.e2.co_p10.f}} with the tenth percentile as the background for either tracer. Its biases run
both ways: local dust and locally formed secondary aerosol do not follow the tracers and are counted as background,
while regional plumes that also carry the tracers change the slope.

{{tbl:T3_local_fraction}}

Two further records give context but not a bound. During the curfew of spring 2020 the station's concentration fell by
{{claim:lfs.e3.D}} ({{claim:lfs.e3.lo}} to {{claim:lfs.e3.hi}}) after adjustment for weather, against
{{claim:lfs.e3.raw}} unadjusted; that combines the local response with a regional one, because neighbouring countries
were also under restrictions, so it cannot isolate the local share. The source apportionment at Katugastota
[@Seneviratne2017] identifies about three tenths of fine mass as local primary sources, which is a floor, because the
model's increment also contains locally formed secondary material.

**What the measurements establish.** At the city-centre station the local share lies between about
{{claim:lfs.e1min.f}}, the urban increment over the cleanest regional town and a lower bound, and
{{claim:lfs.e2.co_p5.f}}, the tracer intercept. The model gives {{claim:lfs.model.e2_cell}} at that cell on the tracer
route's hours and {{claim:lfs.model.ext_cell}} on the urban-increment days, at the upper end of that range. Under the
rule fixed in advance, the model is classed as high against the urban-increment route; that route's known bias runs in
the direction that would explain the gap, and the tracer route agrees with the model. The basin value of
{{claim:partition.f}} is therefore within the measured range but may be somewhat high. An exact value would need a
reference monitor at a clean rural site upwind of Kandy, which no public network provides.
