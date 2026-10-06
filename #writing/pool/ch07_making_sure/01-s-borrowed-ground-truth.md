## Borrowed ground truth {#s-borrowed-ground-truth}

Kandy has two low-cost sensors and no reference monitor, so no local dataset exists against which
the field can be scored. The procedure adopted here borrows the ground truth from elsewhere. A
city with a dense monitoring network is deliberately reduced to the information Kandy actually
has, and the model is then scored against the monitors that were taken away from it.

{{dia:protocol}}

The reduction is what makes the test informative. Scoring a model that has seen thirty monitors
measures a capability the target city will never possess, and reporting that number as though it
described the target is the most common way this class of model is oversold. The panel comprises
{{claim:frame.cities}} cities across {{claim:frame.countries}} countries and
{{claim:frame.city_days}} city days, with a median of {{claim:frame.med_held_stations}} withheld
stations and {{claim:frame.med_days_per_city}} scored days per city. Where those cities are is
mapped in {{fig:panel}}, in {{ref:s-borrowed-panel}}.

Kandy contributes nothing to this panel. It supplies no training data at any tier, which is what
allows the measurement to be applied to it.

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

What transfers is an ordering, not a magnitude. The quantity carried to Kandy is which
observation is worth more than which, and orderings survive shifts in level that would invalidate
a transferred number. No statement in {{ref:s-measurement-priority-ordering}} depends on Kandy's own error falling by any
particular percentage.

The transfer is made within a matched group of cities, not from the pool. Kandy is matched on the
variables that plausibly govern the ordering rather than against the panel as a whole. It is read
against the deep-tropical band, which {{ref:s-recommendation-inverts-tropics}} shows reverses the pooled result, and against the
group of cities whose instruments are low-cost, since Kandy's are low-cost and {{ref:s-three-confounds-pooled-numbers}} shows
that the class of instrument changes what an added sensor is worth. A pooled number would be the wrong number twice over.

The panel matches Kandy on the one structural variable it was selected for and on no others by
design. Every panel city is a valley or basin, which is the feature the construction depends
on, and this is a selection criterion rather than a finding. The panel contains no coastal city,
so nothing here supports a coastal application.

What would break the transfer is stated so that it can be checked. If Kandy's ordering is
governed by something the band does not capture, the recommendation is wrong. {{ref:s-recommendation-inverts-tropics}} names
the candidate, the amplitude of the regional seasonal cycle, and {{ref:s-measurement-would-settle-most}} gives the analysis that
would test whether the band is standing in for it. Until that is run, the transfer rests on Kandy
resembling its band, which is an assumption with evidence behind it and not a demonstration.
