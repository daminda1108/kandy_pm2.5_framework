## Fine-tuning on the two sensors that exist {#s-fine-tuning-two-sensors}

**What was expected.** If a model transferred from other cities is smooth, fine-tuning it on
Kandy's own two sensors should sharpen it. The sensors are the only local information available
and using them is the obvious next step.

What happened. After fine-tuning, agreement at the exact sensor coordinates went from a
correlation of 0.43 to 0.9999, and the error at those points fell to 0.12 micrograms per cubic
metre [ledger sim2real]. On the grid, the annual mean rose from 22.1 to 37.0 micrograms per
cubic metre, which is a physically impossible response to fitting two points more closely.

What it cost. Little in time. A great deal in what it revealed.

What it established. The model had been given latitude and longitude as inputs. With two
sensors and coordinates available, the cheapest way to fit the training data is to memorise the
two coordinate pairs as identity keys and predict the sensor value at those keys. Everywhere
else the network is unconstrained, and the field it produces there is arbitrary.

This is the origin of the admissibility rule that {{ref:s-admissibility-asserted-code}} enforces in code: **a model may not
receive an input that identifies the location it is predicting**. Latitude and longitude are the
obvious case. The subtler cases took longer to find, and one of them is in {{ref:s-defects-found-audit-rather}}.

It also established the diagnostic. A metric evaluated at the training points cannot detect
memorisation, because memorisation is what makes that metric good. Only a quantity evaluated
away from the training points can, and here the grid mean was that quantity.
