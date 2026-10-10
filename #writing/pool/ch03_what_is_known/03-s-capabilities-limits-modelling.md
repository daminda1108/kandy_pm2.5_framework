## Machine learning and data fusion: capabilities and limits {#s-capabilities-limits-modelling}

The main response of the last decade to gaps of this kind has been statistical and
machine-learning fusion of satellite retrievals, chemical transport models and reanalysis data,
with substantial results. Global surfaces now exist at kilometre scale, some at daily resolution
[@vanDonkelaar2021; @Hammer2020; @Wei2023], and they perform well where they can be tested.
Three aspects of this development bear on the present study.

*Combining weak predictors.* The principal contribution of machine learning is the ability to
exploit weak, numerous and mutually redundant predictors. Satellite aerosol retrievals,
reanalysis meteorology, terrain, road networks, population and night lights each carry a small
amount of information about concentration, and none individually supports a useful prediction.
Combining several dozen such predictors is a task that linear regression performed poorly on this
panel and that modern non-linear estimators performed well. {{ref:s-dependence-estimator}}
quantifies this and finds that the choice of estimator matters in a specific way: the value
measured for an observation is a property of the observation and of the estimate it is added to,
so a weaker sensorless estimate makes the first stations appear more valuable. The registered
directional verdicts held across the non-linear estimators tested, which is the sense in which they are
robust; they are not claimed to hold for any estimator whatever.

*Information content.* A model cannot recover structure that its inputs do not encode. It can
only redistribute the information present in its predictors, so where the spatial structure of a
city is not represented in the available covariates, no change of architecture will recover it.
{{ref:ch-model-stops}} turns this constraint into a measurement. The result is stated as a
finding of this study rather than a general theorem: the information and the model classes tested
here did not recover the within-city spatial structure, within a detection limit fixed in advance.
{{ref:s-six-negative-results-their}} sets out the tests, pre-registered with detection limits
stated in advance, including tests of further model families and of interpolation from a small
number of monitoring stations.

*Validation.* Machine learning does not remove the validation problem described in
{{ref:s-consequence-stated-plainly}}. A more capable model cannot be assessed where it is applied
any more than a simpler one, and a more flexible model may aggravate the problem, because it
produces more plausible output whose accuracy still cannot be checked.

The approach taken here therefore uses machine learning where it is effective, for the temporal
behaviour of the city-mean concentration from many weak predictors, and does not use it where no
check is available. The spatial pattern is imposed from physical reasoning and declared as an
assumption rather than fitted, and {{ref:s-six-negative-results-their}} reports the test of that
decision.
