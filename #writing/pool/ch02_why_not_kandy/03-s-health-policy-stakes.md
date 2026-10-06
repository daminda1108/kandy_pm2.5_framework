## Health and policy relevance {#s-health-policy-stakes}

The problem is relevant to Kandy in two distinct ways.

*Health.* Exposure to fine particulate matter is associated with cardiovascular and respiratory
mortality across a wide range of concentrations, and no threshold has been identified below which
the association disappears [@Burnett2018; @WHO2021]. In Kandy, each 10 micrograms per cubic
metre of same-day fine particulate matter was associated with 1.95 per cent more hospital
admissions for respiratory disease in 2019 [@Priyankara2021]. The annual mean concentration over
the basin ranges from {{claim:kandy.mean_min}} to {{claim:kandy.mean_max}} micrograms per cubic
metre across the anchored years, above the World Health Organization annual guideline of 5
micrograms per cubic metre throughout [@WHO2021]. {{ref:s-exposure-weighting}} gives the
population exposure implied by the delivered field, and {{ref:app-attributable-burden-projection}}
the burden projection with its interval.

*Policy.* Prioritising interventions requires a spatially resolved field. A municipality deciding
whether to reroute heavy vehicles, restrict open burning or relocate a bus terminus needs to know
how much of the concentration at a given place is generated locally and how much arrives from
outside the basin. These two components respond largely to different interventions, and no
single point measurement separates them. A field that reports only a total is of limited use for
such decisions, however accurate the total.

The decomposition described in {{ref:ch-model}} is designed for this purpose. It separates a
regional background from a locally generated increment, of which only the increment can be
influenced by a local authority. For Kandy, under the background and minimum-increment
assumptions set out in {{ref:s-partition-constraint-rather-than}}, the constrained decomposition
assigns {{claim:partition.f}} of modelled concentration to the local increment and the remainder
to the regional background. This fraction is derived from a physical constraint rather than
assumed. It is a property of the decomposition, not a measurement of where material was emitted:
the increment is defined by spatial structure and timing, so it includes particulate mass formed
inside the basin from any precursors and excludes regionally formed mass whatever its origin.

The fraction therefore implies a larger scope for local action than the value of about one
quarter assumed in earlier versions of this work. It does not imply that eliminating every local
source would remove about half the concentration, because the model contains no chemistry and
part of the increment is formed in the atmosphere rather than emitted. The decomposition is a
constrained split, not a source apportionment, and {{ref:s-partition-constraint-rather-than}}
states in full what it does and does not support.
