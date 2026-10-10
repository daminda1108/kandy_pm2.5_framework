## Validation without local ground truth {#ch-validation-without-local-ground}

Kandy has two low-cost sensors and no reference monitor, so no local dataset exists against which
the field can be scored, and the two sensors cannot serve: the temporal anchor is trained on them,
its interval is calibrated on them and its amplitude is sharpened to them
({{ref:s-temporal-anchor}}). Agreement with them measures the calibration, not the model.

The validation therefore rests on three lines of evidence. Each answers a different question, and
none of them alone would be sufficient.

### Independent records at Kandy {#s-validation-kandy-records}

The first line asks whether the field's **level** agrees with measurements at Kandy that played no
part in building it. Four published records qualify: annual means from a monitor of the national
research organisation for two years, and three records from low-cost sensors, each carrying its
own calibration. The model is read at the cell containing each site and compared with the
published annual mean. The comparison is of an area mean with a point, so it is governed by the
observation model of {{ref:s-comparing-areal-model-point}}. These records test the level at a few
points. They cannot test the timing of the field, its spatial pattern, or any other part of the
city.

{{include:pool/ch06_the_model/02-s-comparing-areal-model-point.md shift=1}}

### Budget-matched transfer to analogue cities {#s-borrowed-ground-truth}

The second line asks whether the **construction** works, by borrowing ground truth from cities
that have it. Ten valley and basin cities with dense monitoring networks were chosen for their
physical resemblance to Kandy, the feature the construction depends on. In each, the complete
model was built as at Kandy but given only what Kandy has: two anchor stations, the same free
satellite and reanalysis inputs, and the same spatial factors. It was then scored against the
stations withheld from it. One difference is deliberate and declared: in these cities the annual
level is set by the two anchor stations rather than by the satellite surface, so the level score
here does not test the satellite level that Kandy uses. The third line below does.

{{dia:protocol}}

The reduction is what makes the test informative. Scoring a model that has seen thirty monitors
measures a capability the target city will never possess, and reporting that number as though it
described the target is the most common way this class of model is oversold. Three axes are
scored separately and never combined: the seasonal cycle (the correlation of monthly means), the
daily cycle (the correlation of the mean for each hour of the day) and the annual level. The
pattern's rank against the withheld stations is scored as a fourth. These are climatological
scores; day-to-day skill is measured by the third line.

### The deployed model on a ladder of information {#s-validation-ladder}

The third line asks how good the deployed model is **relative to what is achievable** at Kandy's
information budget, and it uses many more cities than the second. A cross-city experiment,
described in full in {{ref:a-app-panel}}, defines a sequence of information budgets: a sensorless
tier that uses only inputs available everywhere, then the same tier with a small number of local
stations added, either as a calibration or read on the day. Each tier is scored in every city
against monitors withheld from it, so the gain from each added stream is a measurement rather than
an assertion. The thesis calls the sequence the **ladder** and each tier a **rung**. The registered
confirmation of the ladder scored {{claim:v2.conf.n_cities}} cities that had played no part in its
design, and Kandy contributes nothing to any of its panels.

The ladder's own sensorless rung is a generic learner of the daily city mean, not the model
deployed at Kandy. To make the ladder a validation of the deployed model, the model's temporal
anchor was added to it as two further rungs. Only the anchor is needed, because the field's city
mean is *T*(*t*) to within {{claim:gauge.drift_hi_pct}} per cent. The first rung runs the anchor's chain with no stations at all: the
composition prior, shifted each year to the satellite level. The second runs it as deployed at
Kandy, with two stations of each city as its anchor pair, used for training, interval calibration
and amplitude correction but never read on the day being predicted. Both are scored on the same
days, the same withheld stations and the same random choices of stations as the ladder's own
rungs, so the deployed model is placed directly against the generic sensorless learner, against
the same two stations used only as a calibration of that learner, and against the same two stations
read on the day. The design was fixed and committed before any of it was scored, and it is
reported as exploratory rather than registered. One difference from Kandy is declared: in the
panel cities the anchor uses the composition prior and reanalysis meteorology only, at daily
resolution, because the remaining predictors of {{ref:s-temporal-anchor}} were not assembled for
every city. Results are summarised as the median over cities of the per-city median over random
splits, with intervals from a bootstrap over monitoring networks.

### What licenses a transfer to Kandy {#s-transferability-panel-result-kandy}

Independence is necessary for the transfer and it is not sufficient. A panel that Kandy is absent
from is also a panel Kandy may not resemble.

**The panels are not a sample of the world's cities.** They are the cities that publish enough
concurrent monitoring to be scored, which selects for institutional capacity, income and
monitoring history. {{ref:ch-kandy-setting-record-stakes}} gives the reason this cannot be fixed by
sampling harder: the regime with the least reference monitoring is the regime that most needs a
sensorless method, so the cities that could best represent Kandy are the cities least able to
appear. Where a claim depends on a panel being representative, it is not made.

Only the ten-city analogue panel was selected for physical similarity. The ladder panels were
selected on network metadata with no terrain rule, and only four of the confirmation cities are
tropical. No panel contains a valley-floor city in the deep tropics with only low-cost monitoring,
and the analogue panel contains no coastal city. What transfers to Kandy is therefore a
**procedure** shown to work in cities of the same physical kind, and **orderings** of information
sources confirmed across many cities, not a number for Kandy's own error. An earlier draft
transferred the ladder's results within a matched group of deep-tropical cities; that match did not
survive averaging over random splits, and no band-specific ordering is carried to Kandy
({{ref:s-recommendation-inverts-tropics}}).

What would break the transfer is stated so that it can be checked. If the value of a same-day
reading at Kandy is governed by something the panels do not span, such as the amplitude of the
regional seasonal cycle or the error structure of low-cost sensors, the transferred ordering may not
hold there. {{ref:s-measurement-would-settle-most}} gives the measurement that would test it
directly.
