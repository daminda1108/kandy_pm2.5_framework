## A paired comparison inside one model cell {#s-test-holds-support-fixed}

The survey contains one pair of sites that bears directly on the question. The garden entrance and
a point three hundred metres inside it were sampled with the same instrument and protocol, over the
same three midday hours of the clock but on different days, and **they fall inside a single
{{claim:subgrid.coarse_res_m}} metre model cell**. The pair therefore holds the model's support
fixed. It does not hold the atmosphere fixed: because the two sites were measured on different
days, their contrast mixes the effect of location with day-to-day variation in the air arriving
over the city, and the measurement is of coarse particulate (PM10), not of the fine particulate the
model estimates. The pair illustrates the potential size of variation inside one cell; it does not
isolate location as its only cause, and it does not validate any modelled PM2.5 contrast.

| | observed | model as delivered |
|---|---:|---:|
| ratio between the two sites | {{claim:spatial.paired_obs_ratio}} times | {{claim:spatial.paired_model_ratio}} times |

{{fig:paired}}

The model returns exactly unity, for the unavoidable reason that it is being asked about one
pixel twice. The observed ratio is larger than the model's entire dynamic range across Kandy. Read
with the caveats above, that is evidence that variation inside a cell can be large, not a measured
contrast attributable to location alone.

Two further limitations apply. Of the survey's
{{claim:spatial.transect_sites}} mapped sites, {{claim:spatial.transect_censored}} are censored
at a common upper value and several more are binned, leaving only
{{claim:spatial.transect_distinct_obs}} distinct observations, so the rank correlation across all
sites is a weak test and {{this:ch-model-stops}} does not lean on it. And a second apparent pair in the
survey, a school junction and its grounds, proves on inspection to carry a single coordinate for
both sites, so the model's unit ratio there is an artefact of the question, not a result.
That pair is withdrawn.
