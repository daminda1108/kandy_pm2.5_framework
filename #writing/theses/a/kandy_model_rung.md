### The deployed model on the ladder {#s-kandy-model-rung}

The deployed model's temporal anchor was scored as a rung of the ladder in
{{claim:v2.km.cities_scored}} cities, against the ladder's own rungs on identical days and
withheld stations ({{ref:s-validation-ladder}}). {{tbl:T3_km_rung}} gives the result. It has to be
read in two uses, because they answer different questions about Kandy.

{{tbl:T3_km_rung}}

**Where the two anchor stations observed the period being reconstructed**, the deployed chain is
the strongest of the estimates tested that do not read stations on the day. It reduces daily error by
{{claim:v2.km.reco.unio.gK2_rmse.median}} per cent relative to the generic sensorless learner
[{{claim:v2.km.reco.unio.gK2_rmse.lo}}, {{claim:v2.km.reco.unio.gK2_rmse.hi}}], which is
{{claim:v2.km.reco.unio.K2mBud0cal2_rmse.median}} points more than the same two stations achieve
when they only recalibrate that learner
[{{claim:v2.km.reco.unio.K2mBud0cal2_rmse.lo}}, {{claim:v2.km.reco.unio.K2mBud0cal2_rmse.hi}}], and
its daily series correlates with the withheld city mean at
{{claim:v2.km.reco.unio.K2_r.median}}. Reading the same two stations on the day still does better,
by {{claim:v2.km.reco.unio.L2samemK2_rmse.median}} points
[{{claim:v2.km.reco.unio.L2samemK2_rmse.lo}}, {{claim:v2.km.reco.unio.L2samemK2_rmse.hi}}]. Part
of the chain's advantage in this use comes from having been trained on the anchor stations' own
record for the days being scored, which is exactly the position of Kandy's reconstruction on the
days its sensors reported.

**Where the stations did not observe the period**, the advantage disappears. Trained on the first
half of each record and scored on the second, the chain's reduction in error is
{{claim:v2.km.pros.unio.gK2_rmse.median}} per cent
[{{claim:v2.km.pros.unio.gK2_rmse.lo}}, {{claim:v2.km.pros.unio.gK2_rmse.hi}}], no better than the
recalibrated learner (difference {{claim:v2.km.pros.unio.K2mBud0cal2_rmse.median}} points
[{{claim:v2.km.pros.unio.K2mBud0cal2_rmse.lo}}, {{claim:v2.km.pros.unio.K2mBud0cal2_rmse.hi}}]),
and its correlation falls to {{claim:v2.km.pros.unio.K2_r.median}}. This is the position of Kandy
on the many hours and days that neither sensor recorded.

Three further results bear directly on Kandy. The **level** taken from the satellite surface sits
above the withheld city mean by a median of {{claim:v2.km.reco.unio.K2_bias.median}} per cent in
reconstruction and {{claim:v2.km.pros.unio.K2_bias.median}} per cent prospectively, the same sign as
the offset between the field and three of the four independent Kandy records. The chain's **nominal
ninety per cent interval** covers a fraction {{claim:v2.km.reco.unio.K2_cov90.median}} of withheld
daily means in reconstruction, close to its coverage of {{claim:kandy.cov90}} per cent at the Kandy
sensors, so the under-coverage found at Kandy ({{ref:s-interval-calibration}}) is not peculiar to
the Kandy sensors; it recurs where the truth is known. And the chain **without any station**, the composition
prior shifted to the satellite level, follows the daily sequence more closely than the generic
learner (correlation {{claim:v2.km.reco.unio.K0_r.median}} against
{{claim:v2.km.reco.unio.Bud0_r.median}}) but overstates its swings, so its reduction in error is
negative, {{claim:v2.km.reco.unio.gK0_rmse.median}} per cent: the composition prior carries the
timing, and the two stations are what scale it.

Two qualifications apply. The anchor in the panel cities used the composition prior and
meteorology only, at daily resolution, not the full predictor set used at Kandy. And the test is
exploratory: its design was fixed before scoring but was not registered.
