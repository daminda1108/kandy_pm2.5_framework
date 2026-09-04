# Chapter 7. Making sure it works

A model that cannot be checked where it is used is not obviously worth more than a plausible
guess. This chapter sets out the procedure that makes the checking possible, reports what it
measured, and states the three confounds it caught before they reached print.

## 7.1 Borrowed ground truth

Kandy has two low cost sensors and no reference monitor, so there is no local dataset against
which the field can be scored. The procedure adopted here borrows the ground truth from
elsewhere. A city with a dense monitoring network is deliberately reduced to the information
Kandy actually has, and the model is then scored against the monitors that were taken away from
it.

{{dia:protocol}}

The reduction is what makes the test informative. Scoring a model that has seen thirty monitors
measures a capability the target city will never possess, and reporting that number as though it
described the target is the most common way this class of model is oversold. The panel comprises
{{claim:frame.cities}} cities across {{claim:frame.countries}} countries and
{{claim:frame.city_days}} city days, with a median of {{claim:frame.med_held_stations}} withheld
stations per city.

## 7.2 What each increment of information is worth

The measurement is possible because the tiers are nested: a lower tier is not a different model,
it is the same model with a stream removed, so the difference between two tiers is information
loss and nothing else.

Reported as the median across cities of the per city percentage reduction in daily root mean
square error, never as a ratio of medians:

| step | median reduction |
|---|---:|
| add static geography | {{claim:step.geography}} per cent |
| add a satellite level | {{claim:step.satellite}} per cent |
| add two local sensors | {{claim:step.bud0c_bud1}} per cent |
| add six more sensors | {{claim:step.bud1_bud2}} per cent |
| add a regional background | {{claim:step.bud2_bud3}} per cent |

Three features of that table matter more than its ordering. Static geography, which is free
everywhere on Earth, is worth about as much as the first local instrument. The second through
eighth monitors are worth {{claim:step.bud1_bud2}} per cent, which is not a small effect but an
absent one. And the largest single gain in the study comes from a regional background station,
which is the instrument most air quality programmes never buy, because a rural monitor serves no
constituency.

## 7.3 The recommendation inverts in the tropics

The pooled table is misleading if read as advice. Stratified by latitude band, the ordering
reverses in the band Kandy belongs to: local sensors buy
{{claim:band.deep_tropical.step_bud0c_bud1}} per cent there against
{{claim:band.deep_tropical.step_bud2_bud3}} per cent for the regional background, which is the
opposite of the pooled result. A programme following the pooled recommendation in Colombo or
Kampala would buy the wrong instrument first.
