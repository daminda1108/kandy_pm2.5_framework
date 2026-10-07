## The registered confirmation on fresh cities {#s-registered-confirmation}

The confirmation is reported first among the results because it is the only test in
{{this:a-app-panel}} whose endpoints were fixed before the data existed on the project's side.
Everything measured on the discovery panel is read in its light.

Of the seventy-six registered cities, {{claim:v2.conf.n_cities}} were scored. Four were excluded by
the registered rules and not replaced: one had too few stations with data, and three had too few
days matched to the reanalysis drivers. The background rung could be formed in sixty-eight cities;
in the other four too few stations remained once the held-out and rung stations had been drawn.

{{tbl:T7_1_ladder_v2}}

{{fig:confirmation}}

Four of the five directional hypotheses were supported and the moderator was not. The first two
stations, used as a recalibration of the sensorless estimate, reduce daily error by
{{claim:v2.conf.reco.first2_rmse.median}} per cent [{{claim:v2.conf.reco.first2_rmse.lo}},
{{claim:v2.conf.reco.first2_rmse.hi}}]. Stations three to six add
{{claim:v2.conf.reco.s36_rmse.median}} points [{{claim:v2.conf.reco.s36_rmse.lo}},
{{claim:v2.conf.reco.s36_rmse.hi}}], inside the equivalence bound of one point fixed in advance. The
background series adds {{claim:v2.conf.reco.bg_rmse.median}} per cent
[{{claim:v2.conf.reco.bg_rmse.lo}}, {{claim:v2.conf.reco.bg_rmse.hi}}]. The registered two-sided
comparison of the two rungs resolves an ordering, the background ahead of the first two stations, by
{{claim:v2.conf.reco.bgm2_rmse.median}} points [{{claim:v2.conf.reco.bgm2_rmse.lo}},
{{claim:v2.conf.reco.bgm2_rmse.hi}}] on daily error and by {{claim:v2.conf.reco.bgm2_exceed.median}}
[{{claim:v2.conf.reco.bgm2_exceed.lo}}, {{claim:v2.conf.reco.bgm2_exceed.hi}}] on the exceedance loss.
The prospective arm reproduces every verdict: the first two stations
{{claim:v2.conf.pros.first2_rmse.median}} per cent, the background {{claim:v2.conf.pros.bg_rmse.median}}
per cent, and the background minus the first two {{claim:v2.conf.pros.bgm2_rmse.median}} points
[{{claim:v2.conf.pros.bgm2_rmse.lo}}, {{claim:v2.conf.pros.bgm2_rmse.hi}}].

The first-station gain is less than half of what the discovery panel had suggested, and the
difference is not a contradiction. The gain of any rung is measured against the rung below it, so
it tracks how weak the sensorless estimate is, and the confirmation panel is dominated by temperate
cities, where that estimate is strongest. {{ref:s-dependence-estimator}} shows the same dependence
from the side of the learner.

**Every verdict is quoted as constructed.** The two rungs being compared use their stations in
different ways ({{ref:s-rungs-how-each-uses}}): the first stations only recalibrate the sensorless
estimate, while the background is read on the day being predicted. H4 and H5 therefore compare a
calibration with a same-day reading, not one kind of station with another, and
{{ref:s-like-for-like}} shows that this difference of use produces the whole of the ordering. The
verdicts stand as registered and are read throughout as statements about the rungs as built. H2 is
close to guaranteed by the same construction. Two stations already determine a two-parameter
recalibration over hundreds of days, so four more cannot add much to it. The small value means
that more stations do not improve a recalibration, not that they carry no information.

**The moderator is undetectable.** The registered slope of the ordering on absolute latitude is
{{claim:v2.conf.m1_abslat.median}} points per degree [{{claim:v2.conf.m1_abslat.lo}},
{{claim:v2.conf.m1_abslat.hi}}]. With four scored cities below the Tropic of Cancer, the registration
declared the test underpowered and fixed in advance that a null would be reported as undetectable.
Nothing in the confirmation therefore bears on the deep tropics, the band Kandy belongs to
({{ref:s-recommendation-inverts-tropics}}).

### The ordering under other losses {#s-ordering-under-four-loss}

Daily root mean square error is the loss the estimator optimises, and an average-day loss can hide
what matters for episode warning, where the loss is concentrated in a few days a year. The
registered secondary endpoints re-score the same rungs on the days at or above each city's
ninetieth percentile, and on the balanced error of classifying exceedances of the guideline.

As constructed, the background rung ranks above the first two stations under every one of these
losses, and more clearly for exceedances than on the average day. The first two stations, used as a
recalibration, change nothing detectable on high days. Stations three to six change no exceedance
classification at all in most cities, so their exceedance effect is exactly zero at the median.

None of this survives a like-for-like use of the stations. Read on the day, the background minus
the first two on the exceedance loss is {{claim:v2.review.registered_loco.reco.BGallmL2s_exceed.median}}
points [{{claim:v2.review.registered_loco.reco.BGallmL2s_exceed.lo}},
{{claim:v2.review.registered_loco.reco.BGallmL2s_exceed.hi}}] ({{ref:s-like-for-like}}). What the
exceedance endpoints show is that a recalibration cannot see an episode as it happens, which a
same-day reading can, whichever stations supply it. An earlier version of this work reported that
the ordering changed sign between the average day and episode days in the deep tropics. That
result was one station split and one learner seed, and it is retracted with the rest of the
deep-tropical comparison.

### What the background series is, and an independent donor network {#s-test-using-independent-donor}

The background rung is built from the city's own network, so part of its value could be more of the
same network rather than air arriving from outside the city. The question is answerable without new
instruments. The background can be rebuilt from **a different city entirely**, thirty to three
hundred kilometres away, whose monitors the target never sees, and passed through an identical chain
so that only the background differs. Below thirty kilometres a donor is really the same urban area;
beyond three hundred it is a different air mass and should stop helping.

On the discovery panel, paired within city, a donor network at a median distance of
{{claim:donor.median_km}} kilometres recovers {{claim:donor.gain_reproduced_pct}} per cent of the
background rung's gain. Recovery falls with distance, from {{claim:donor.reproduced_near}} per cent at
{{claim:donor.km_near}} kilometres to {{claim:donor.reproduced_far}} per cent at
{{claim:donor.km_far}}. The rung therefore carries regional information and is not mostly a
same-network artefact.

Three limits apply. The test bounds the same-network component from above and does not measure it,
because the donors sit far outside the city while the own-network stations sit inside it, so the
residual gap conflates *same network* with *much closer*. Only {{claim:donor.pairs}} discovery cities
have a donor in range, concentrated where urban monitoring is dense, and the deep tropics hold too
few to report separately. And the test is exploratory. The background rung must therefore be named
as what it is, a same-network background series, and a measured regional monitor such as those of the
national building research network remains outside anything the ladder has priced.

### Scope {#s-confirmation-scope}

The confirmed population is mainly temperate and mainly regulatory: fifty of the scored cities are
temperate, four lie below the Tropic of Cancer, and sixty-three of the seventy-six registered cities
are dominated by reference monitors. Kandy is deep-tropical and monitored only by low-cost sensors, so
it lies outside the bulk of the population the verdicts describe. What transfers to Kandy is a
statement about how observations are used, which {{ref:s-like-for-like}} shows is the same for every
kind of station the panel holds, and not an ordering specific to its climate or instruments.
