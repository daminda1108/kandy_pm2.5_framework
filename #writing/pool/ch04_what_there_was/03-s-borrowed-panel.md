## The borrowed panel {#s-borrowed-panel}

The validation of {{ref:s-borrowed-ground-truth}} requires cities with dense monitoring, and Sri Lanka has none that
qualify. Cities are therefore borrowed from two open archives [@OpenAQ; @CNEMC], and they enter the
thesis as two different panels that are chosen by different rules and must not be confused.

**The analogue panel** is used to score the full model, with its terrain, transport and emission
layers, against dense ground truth ({{ref:s-model-across-ten-cities}}). It has ten cities, and every
member is a valley or a basin, chosen so that the physical setting resembles the target. No
coastal regime is represented.

**The ladder panels** are used to measure what each information source is worth
({{ref:s-marginal-predictive-value-each}}). They were selected on network metadata alone: a city
enters if it has at least ten monitoring locations with sufficient records, lies far enough from
every city already drawn, and does not exceed a cap on the number of cities per country. There is no
terrain rule, so these panels are not valley panels. The discovery panel covers
{{claim:frame.cities}} cities in {{claim:frame.countries}} countries and is treated as exploratory.
The confirmation panel was drawn by a registered rule before any concentration data were retrieved:
seventy-six fresh cities in thirty countries, of which {{claim:v2.conf.n_cities}} could be scored.
A further registered test re-ran the confirmation on the full monitoring networks of seventy-five
cities.

Which cities those are matters as much as how many, because no panel is a sample of the world's
cities. Each is the set of cities that publish enough open data to be scored, which is a different
population and a selected one. The figure below shows where the discovery cities are. Two things
are worth reading from it. The distribution is heavily weighted towards the mid-latitudes and
towards a small number of national networks, which is the dependence
{{ref:s-marginal-predictive-value-each}} has to correct for. And the tropical members, the ones
that most resemble Kandy, are the sparsest group on the map, which is the constraint
{{ref:ch-kandy-setting-record-stakes}} describes and no amount of careful sampling can remove. The
confirmation panel has the same shape: it is mainly temperate and subtropical, holds only four
tropical or deep-tropical cities, and is dominated by regulatory reference networks, which make up
sixty-three of its seventy-six cities.

{{fig:panel}}

Three properties of these panels constrain what {{ref:s-summary-established-results}} can conclude, and all three are stated
there as well as here.

They are not random samples of cities. Cities enter by having published dense monitoring, which
is correlated with income, with latitude and with the kind of institution that operates a
network.

Only the analogue panel is selected for physical similarity to the target, and it is the one used
to score the full model. That makes the transfer of the model's skill more credible, and it means
those results are not established for coastal regimes. The ladder panels make no such selection,
so the measured value of each information source applies to the population of monitored cities
they represent, which is mainly temperate and regulatory, and Kandy lies outside its bulk.

And the association between instrument class and latitude band cannot be removed by sampling
more carefully, for the reason {{ref:ch-kandy-setting-record-stakes}} gave: the population of
candidate cities does not contain a balanced draw. In the discovery panel, once the Chinese
national network is correctly classed as reference monitoring, thirty-one cities are
reference-dominated and sixteen are dominated by low-cost sensors.
