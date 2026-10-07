## Aim and approach {#s-aim-approach}

The response taken here is not to build a better fusion product. It is to change the question.
Rather than asking how accurate a model is in a place where accuracy cannot be measured, this
thesis asks what a model is entitled to claim given the observations it actually has, and then
measures what each additional observation would be worth.

That reframing is what makes the problem tractable. The value of an observation can be measured
where observations are plentiful, by withholding them deliberately and scoring what is lost.
Provided the withholding is exact, so that the reduced model is the same model with less
information rather than a different model altogether, the measurement transfers to a city where
the observation was never available in the first place. {{ref:ch-model}} describes the construction
that makes withholding exact, and {{ref:s-marginal-predictive-value-each}} reports what the measurement found.

The results differ in places from what the field's intuition suggests, and in one place from
what this work itself first concluded. A station's value to a daily city-mean estimate depends
mainly on how its reading is used. Read into the estimate every day, one station reduces daily
error by {{claim:v2.review.k.day1.median}} per cent and two by {{claim:v2.review.k.day2.median}}
per cent; used only to calibrate a sensorless estimate, the same stations reduce it by about
{{claim:v2.review.k.cal2.median}} per cent, whatever their number. Used the same way, stations of
different kinds are worth about the same, so the choice between a local station and a background
series is not the decision it first appeared to be. A comparison registered before it was run had
ranked a background series above the first local stations; a later review found that the two
rungs had been built differently, the stations entering only as a calibration and the background
with its daily reading, and the ranking does not survive a like-for-like comparison. That
correction is reported in full rather than hidden, because it is itself a finding about how such
measurements should be designed.

Two further results belong in this summary because both cut against the work itself. The model's
own dispersion step, the part that redistributes emissions through terrain-steered flow, makes
neighbourhood ranking worse than the raw emission surface it starts from. And a handful of
stations does not rescue the spatial pattern: on the cities with dense networks, interpolation
from three to eight stations ranks neighbourhoods little better than a single free land-cover
layer. The measurement framework works better than the spatial model it was built to evaluate.

Each of those findings is bounded rather than general, and {{ref:s-summary-established-results}} states the bounds alongside
the numbers. The panel is the set of cities that publish enough data to be scored, which is not a
sample of the world's cities; the registered panel is mostly temperate and mostly served by
regulatory monitors, whereas the city this thesis is about is tropical and has only low-cost
sensors; and whether the value of an observation differs between climate bands could not be
tested, because the public record holds too few dense tropical networks.
