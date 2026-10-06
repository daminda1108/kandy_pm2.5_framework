## A conditional neural process trained across cities {#s-conditional-neural-process-trained}

**What was expected.** A neural process trained on several cities with dense monitoring
[@Gordon2020] should learn to map from covariates to a spatial field, and could then be
applied to a city it had never seen. This is the most direct machine-learning attack on the problem and it is what most
readers would try first.

What happened. The model was built, trained across three source cities, and applied to Kandy
producing a full year of hourly fields. Cross-city correlation reached 0.599 on average
[ledger v14]. Calibrated intervals were obtained by conformal post-processing
[@Vovk2005; @Romano2019] and covered close to their nominal rate at all three source cities.

Then the output was examined. The fields were smooth. They were consistent with the annual mean,
they reproduced the seasonal cycle, and the diurnal cycle had roughly the right shape. They
contained almost no spatial structure. The model had learned to produce a plausible city-mean
concentration and to vary it gently in space in a way that was not wrong so much as
uninformative.

**What it cost.** The largest single block of work in the project, and it produced deliverable
output that was held back rather than published.

What it established. Three things, and the third is the one that mattered.

A model can be right on every aggregate diagnostic and still fail at the task it was built for.
Annual mean, seasonal cycle, diurnal cycle and interval coverage were all acceptable, and none of
them is sensitive to whether the spatial field carries information.

A learned field is not automatically an informative field. Smoothness is what a flexible model
produces when the covariates do not constrain the output, and it is difficult to distinguish
from appropriate regularisation by inspection.

And the assessment problem of {{ref:ch-weather-known-air}} applies to the assessment itself. There was no
measurement at Kandy against which the fields could be scored, so the decision to hold them back
was a judgement, not a test. {{ref:ch-model-stops}} finally converted that judgement into a measurement, four
months later.
