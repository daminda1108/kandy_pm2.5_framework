## Future work: testing the reconstruction against observations designed to refute it {#a-future}

The limits identified in {{ref:a-results}} do not call for a larger model or more satellite covariates: a model can
only redistribute the information in its inputs, and no model family tested here recovered structure the inputs did not
encode ({{ref:s-six-negative-results-their}}). They call for observations. The research that follows this thesis
therefore treats the delivered reconstruction as a **locked hypothesis**. Its predictions for every site and hour of a
planned network are frozen and registered before any instrument is bought, and the observations are chosen because they
could prove it wrong. Three outcomes would each advance the work: spatial differences that survive, giving grounds to
keep or refine the map; broad patterns that hold but fail at one kilometre, establishing a defensible resolution limit;
or errors that prove to be temporal, instrumental or in the background assumption, identifying the component to
redesign. The programme has four phases, in this order, and the author intends to pursue it.

### Phase 1: provenance and the calibration record {#s-future-provenance}

Before any new money is spent, the existing evidence is made fully auditable. The regulatory authority's metadata and
quality-control records for the Kandy station (method, inlet height, siting, audits, data flags) and its underlying
record are to be obtained through the formal agreement ({{ref:s-data-requested-but-obtained}}) and compared with the
public values used here, including the higher readings after 2023 that the extension tier misses
({{ref:s-cea-reference}}). A single register records which observations calibrate the model and which only check it:
the two low-cost sensors train and sharpen the temporal anchor, the regulatory record to mid-2021 sets the level, its
later record and the regional sensors check it, and the ten analogue cities check the construction. If the authority's
station can serve as the reference for Phase 2, the largest cost of the network costed below, a reference instrument
at {{claim:cost.ref_lo_usd}} to {{claim:cost.ref_hi_usd}} US dollars, falls away.

### Phase 2: low-cost sensors evaluated against the reference {#s-future-collocation}

A network of low-cost sensors can test the reconstruction only once it is known what such a sensor measures in Kandy's
humidity. Several units are to be co-located with the regulatory monitor for at least thirty days in each of two
contrasting seasons, the north-east monsoon and the south-west monsoon, with the last third of each period sealed and
used once to score the calibration fitted on the rest. The quantities are bias, slope, unit-to-unit spread, drift
(repeated at the end of the network deployment) and the response to humidity. The last decides between the two
humidity corrections the thesis carries ({{ref:s-rh-scenario}}): the prediction, to be registered in advance, is that the
hourly correction brings the sensors' night-to-midday ratio close to the reference's
{{claim:cea.hourly.station.night_over_midday}}, which the delivered constant-humidity correction does not. The same
step settles the calibration of the two sensors the temporal anchor is trained on.

### Phase 3: a distributed network as a test of the field {#s-future-network}

The network re-uses a design prepared during this work: {{claim:net.total}} sites in five strata, namely an anchor
at the reference, {{claim:net.design}} sites spanning the model's predicted contrasts, {{claim:net.paired}} sites as
{{claim:camp.n_pair_locations}} triplets of three, each triplet inside a single model cell,
{{claim:net.vertical}} sites from {{claim:net.vertical_lo}} to {{claim:net.vertical_hi}} metres above the valley floor
along the axis no network samples, and {{claim:net.receptor}} sites at schools and hospitals held out of everything;
the night-time drainage test adds {{claim:cost.n_drainage}} sites at the predicted drainage sink and in the core. The
anchor is the reference instrument, so the low-cost requirement is {{claim:cost.n_lcs}} units, with
{{claim:cost.spares}} spares. Its purpose changes from learning the pattern to testing it, and the design analysis says what each
test can show before any data exist.

{{tbl:T5_continuation}}

The power figures in the table rest on stated assumptions, set before any data exist and kept in the design
analysis (`campaign_power.py`, registered at the Open Science Framework, `ad3py`). Every test uses a significance
level of {{claim:camp.alpha}} and power of {{claim:camp.power}}. The within-cell ratio's precision assumes an
hour-to-hour coefficient of variation of {{claim:camp.cv_site}} at a site, pooled over the
{{claim:camp.n_pair_locations}} triplets over one week of hourly data; it is the hours averaged, not the number of sites, that make it
precise. The drainage test is a one-sided sign test with the night as its unit. The rank test compares two
correlations that share the observations [@Steiger1980], against the built-up layer's {{claim:camp.benchmark_rho}},
with the correlation between the two predictors assumed to lie between {{claim:camp.rpp_lo}} and {{claim:camp.rpp_hi}};
the detectable gain is reported across that range because it cannot be known in advance.

Three findings of this thesis set that design. A network of a few dozen sites cannot show that the map is good at one
kilometre: with {{claim:camp.n_fit}} sites available to fit, only a gain of {{claim:camp.h1_gain_lo}} to
{{claim:camp.h1_gain_hi}} over the free built-up layer would be detectable, against the {{claim:camp.panel_limit}} the
whole panel resolved. Choosing sites deliberately does not improve what a network learns
({{ref:s-deliberate-siting-tested-dense}}). And what a station is worth for the daily city level comes from reading it
every day, not from the size of the network ({{ref:s-measurement-priority-ordering}}). The network is therefore built
around the tests that resolve quickly (the level at many points, the within-cell ratio, the night-time drainage and the
daily cycle by site), states in advance that the rank test can detect only a gross failure, and reports the anchor and a
few contrast sites continuously so that they improve the daily estimate while the spatial tests run. The instruments
cost about {{claim:cost.lcs_total_usd}} US dollars for those {{claim:cost.n_lcs}} units and
{{claim:cost.spares}} spares; mounting, power,
connectivity, import duty and servicing remain to be priced locally.

### Phase 4: the regional background and composition {#s-future-background}

The urban-increment estimate of the local share is a lower bound only because every regional sensor stands in a town
({{ref:s-local-fraction-measured}}). A reference site in clean country upwind of Kandy for each monsoon would turn that
bound into an estimate and test the background term day by day. A surface weather station inside the basin would
replace the priors behind the wind layer. If resources allow, parallel filter sampling at the city-centre and rural
sites for mass, organic and elemental carbon, ions and elements would separate locally emitted primary material from
material formed locally and material carried in: the locally emitted primary share now lies between
{{claim:chem.intervention_lo}} and {{claim:chem.intervention_hi}} per cent, a range set entirely by not knowing how much
of the local increment is secondary ({{ref:s-independent-chemical-check}}). The nearest reference city cannot stand in
for a regional station: Colombo's daily correlation with Kandy is {{claim:donor.colombo_r}} against a benchmark of
{{claim:donor.benchmark_median_matched}} at comparable separation, consistent with the finding of [@Senarathna2026] that
sensor calibrations do not transfer between the two climatic zones.

### How the outcomes feed back {#s-future-outcomes}

If the within-cell ratio stays near one, the level holds across strata and the rank test is positive, the pattern is
kept and its confinement amplitude refitted on the network. If the broad pattern holds but the within-cell ratio is far
from one and the rank test is null, the result is a measured resolution limit, and the field is delivered at the scale
that survives. If the daily cycle by site or the background test fails, or the collocation reverses the humidity
verdict, the temporal anchor or the background is redesigned before the pattern is revisited. None of these requires
the model to look good, and the parts of the field that survive are the only ones a later exposure or risk assessment
should carry forward.

### Alongside the programme {#s-future-alongside}

**A fresh, pre-specified like-for-like test of the ladder.** The finding that the kind of station matters little rests
on a post hoc re-analysis of registered data ({{ref:s-like-for-like}}); it should be confirmed by a test registered
before scoring, on cities or networks that played no part in any earlier panel, including the deployed model's rung
({{ref:s-kandy-model-rung}}). The same test should sort cities by the amplitude of the regional seasonal cycle rather
than by latitude, and include dense tropical networks, because whether the panels' ordering transfers to a city like
Kandy may depend on a variable the panels do not span ({{ref:s-recommendation-inverts-tropics}}); the low-cost sensors'
own error structure, the other candidate, is what Phase 2 measures.

**The temporal model.** The coherence cap should be evaluated on local days with a robust daily floor; the panel
version of the anchor should be scored with its full predictor set; and a second reanalysis family and precipitation in
the forecast drivers would remove two structural dependencies. A transport calculation that beats the undispersed
pattern on held-out stations is the construction step most worth revisiting, since the dispersion step lowered rank
agreement from {{claim:r2.rho_emission_surface}} to {{claim:r2.rho_with_atransport}} ({{ref:s-spatial-contrast-lost}});
the free built-up layer is the benchmark it would have to beat.

**An independent reproduction.** Every number in this thesis is regenerated from source files at each build, but no one
outside the project has yet re-run the chain from the source datasets.

**What would not help.** A larger model; a finer grid, because the variation lives inside the cell
({{ref:s-implications-radius-result}}); and more stations for a neighbourhood map at the counts a city like Kandy could
afford, or stations sited deliberately across land-use contrast ({{ref:s-what-stations-buy-map}},
{{ref:s-deliberate-siting-tested-dense}}).
