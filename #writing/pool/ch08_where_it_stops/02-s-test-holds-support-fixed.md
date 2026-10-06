## A test that holds support fixed {#s-test-holds-support-fixed}

The survey contains one pair of sites that isolates the question. The garden entrance and a point
three hundred metres inside it were sampled with the same instrument, over the same three-hour
window, on the same protocol. **They fall inside a single {{claim:subgrid.coarse_res_m}} metre
model cell.** Support is held fixed; only location varies.

| | observed | model as delivered |
|---|---:|---:|
| ratio between the two sites | {{claim:spatial.paired_obs_ratio}} times | {{claim:spatial.paired_model_ratio}} times |

{{fig:paired}}

The model returns exactly unity, for the unavoidable reason that it is being asked about one
pixel twice. The cleanest statement of the limit is that **the model's entire dynamic range
across Kandy is smaller than the difference between two points three hundred metres apart inside
one garden.**

Three limitations belong with that statement rather than after it. The observed values are coarse
particulate and the model is fine particulate, so only ratios are meaningful. Of the survey's
{{claim:spatial.transect_sites}} mapped sites, {{claim:spatial.transect_censored}} are censored
at a common upper value and several more are binned, leaving only
{{claim:spatial.transect_distinct_obs}} distinct observations, so the rank correlation across all
sites is a weak test and {{this:ch-model-stops}} does not lean on it. And a second apparent pair in the
survey, a school junction and its grounds, proves on inspection to carry a single coordinate for
both sites, so the model's unit ratio there is an artefact of the question, not a result.
That pair is withdrawn. The garden pair is the evidence.
