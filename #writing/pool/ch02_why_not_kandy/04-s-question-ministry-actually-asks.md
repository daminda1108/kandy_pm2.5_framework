## Monitoring priorities for a city without a network {#s-question-ministry-actually-asks}

Much of the modelling literature asks which model is most accurate. An environmental authority in
a city such as Kandy faces a different question, and it is the question that motivates this
study: which observations should be acquired, and in what order, to obtain an estimate that can
be trusted?

The options differ in cost and in what they provide. A reference monitor costs tens of thousands
of dollars to install and requires trained staff and consumables indefinitely. A pair of low-cost
sensors costs a few hundred dollars [@Morawska2018], but introduces a calibration problem that must
then be solved. A background station outside the city costs about as much as an urban one but
serves no local constituency, which is likely to make it the most difficult of the three to fund.
A mobile campaign requires staff time rather than capital, and produces a snapshot rather than a
record. The options also differ in how their observations can be used: a fixed station that
reports continuously can enter an estimate every day, whereas a campaign can only calibrate it
once, and {{ref:s-marginal-predictive-value-each}} shows that this difference matters more than the kind of station.

The literature on monitoring-network design mostly addresses where to place sensors of one kind
within a region, often one that is already monitored [@Verghese2022; @Choi2026], and provides
little that would allow an authority with no monitors to rank different kinds of observation.
The reason is methodological, and it motivates the construction described in {{ref:ch-model}}.
Ranking observations requires knowing what a model would produce without a given observation.
For most model families this is not well posed: removing an input and refitting produces a
different model, so the difference between the two confounds the loss of information with the
change of model. The statistical fusion models used for urban air quality therefore rarely
recover this quantity, although numerical weather prediction measures it routinely with
data-denial experiments [@Samrat2025].

{{ref:ch-model}} describes a construction in which the quantity can be recovered, and
{{ref:s-marginal-predictive-value-each}} reports the measurement. For Kandy's climatic band
nothing in that measurement is confirmed separately, and the evidence does not rank a local
station network against a regional background series: the two are complementary, and what
matters most is that their readings reach the estimate daily.
