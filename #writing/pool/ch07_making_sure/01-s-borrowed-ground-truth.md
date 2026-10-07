## Borrowed ground truth {#s-borrowed-ground-truth}

Kandy has two low-cost sensors and no reference monitor, so no local dataset exists against which
the field can be scored. The procedure adopted here borrows the ground truth from elsewhere. A
city with a dense monitoring network is deliberately reduced to the information Kandy actually
has, and the model is then scored against the monitors that were taken away from it.

{{dia:protocol}}

The reduction is what makes the test informative. Scoring a model that has seen thirty monitors
measures a capability the target city will never possess, and reporting that number as though it
described the target is the most common way this class of model is oversold.

The procedure is applied to the panels described in {{ref:s-borrowed-panel}}. The discovery panel
comprises {{claim:frame.cities}} cities across {{claim:frame.countries}} countries; where those
cities are is mapped in {{fig:panel}}. Its results were used to design the tests and are reported
as exploratory. The registered confirmation scored {{claim:v2.conf.n_cities}} fresh cities grouped
into thirty clusters, and each city's effect is the median over between six and twenty-one random
choices of which stations are withheld and which are used. A further registered test repeated the
confirmation on the full networks of seventy-five cities, with a median of seventeen stations each.

Kandy contributes nothing to any of these panels. It supplies no training data at any tier, which
is what allows the measurement to be applied to it.

The table below describes the discovery panel by latitude band as it was first scored. Two of its
features have since been corrected: the cities of the Chinese national network, shown there
without a band, are now assigned to their bands, and that network is classed as reference
monitoring rather than low-cost, which changes the class composition of the bands.

{{tbl:T4_3}}

### Transferability of the panel result to Kandy {#s-transferability-panel-result-kandy}

Independence is necessary for the transfer and it is not sufficient. A panel that Kandy is absent
from is also a panel Kandy may not resemble, and the question of what licenses carrying a number
from one to the other has to be answered rather than assumed.

**The panel is not a sample of the world's cities.** It is the set of cities that publish enough
concurrent monitoring to be scored, which selects for institutional capacity, income and
monitoring history. {{ref:ch-kandy-setting-record-stakes}} gives the reason this cannot be fixed by sampling harder: the
regime with the least reference monitoring is the regime that most needs a sensorless method, so
the cities that could best represent Kandy are the cities least able to appear. Where a claim
depends on the panel being representative, it is not made.

What transfers is an ordering, not a magnitude, and only an ordering that was confirmed. The
quantity carried to Kandy is which observation is worth more than which, and orderings survive
shifts in level that would invalidate a transferred number. No statement in
{{ref:s-measurement-priority-ordering}} depends on Kandy's own error falling by any particular
percentage. The confirmed orderings are, moreover, orderings of the rungs **as constructed**: the
first local stations enter the registered ladder only as a recalibration of the sensorless
estimate, while the background is read on the day. {{ref:s-marginal-predictive-value-each}}
reports what happens when the two are used the same way, and the answer is that they are worth
about the same.

An earlier draft transferred the result within a matched group of cities: the deep-tropical
band, which was then thought to reverse the pooled ordering, and the cities whose instruments are
low-cost. Neither match survives. The deep-tropical reversal rested on one random split of the
stations and one learner seed, and averaged over splits it is not distinguishable from zero; the
registered confirmation found the dependence of the effects on latitude undetectable. The
class-of-instrument argument rested on a classification that counted the Chinese national
reference network as low-cost. No band-specific or class-specific ordering is established, and
none is carried to Kandy.

The transfer therefore rests on the confirmation population, and Kandy lies outside its bulk.
Only four of the confirmation cities are tropical, and most are served by regulatory reference
networks, while Kandy is deep-tropical and has only low-cost sensors. Nothing in the confirmation
contradicts the pooled orderings for a city like Kandy, and nothing confirms them there either.

Only the ten-city analogue panel used to score the full model ({{ref:s-model-across-ten-cities}})
was selected for physical similarity: every member is a valley or basin, which is the feature the
construction depends on, and this is a selection criterion rather than a finding. The ladder
panels were selected on network metadata, with no terrain rule. No panel contains a valley-floor
city in the deep tropics with only low-cost monitoring, and the analogue panel contains no coastal
city, so nothing here supports a coastal application.

What would break the transfer is stated so that it can be checked. If the value of a same-day
reading at Kandy is governed by something the confirmation population does not span, such as the
amplitude of the regional seasonal cycle or the error structure of low-cost sensors, the pooled
ordering may not hold there. {{ref:s-measurement-would-settle-most}} gives the measurement that
would test it directly. Until then the transfer is an assumption with evidence behind it and not a
demonstration.
