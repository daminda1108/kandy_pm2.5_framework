## The measurement-priority ordering {#s-measurement-priority-ordering}

The practical question behind this thesis is what a city with almost no monitoring should obtain
first. The answer is not a single instrument, because it depends on what the city already has and
on which group of cities it resembles. The figure below sets that out as the decision it actually
is: start from what is already available at no cost, then branch on whether the city has any local
observation at all, and then branch again on the group it belongs to, because {{ref:s-recommendation-inverts-tropics}} shows the
ordering reverses between those groups. Each endpoint names the measurement to obtain and the
section that prices it. The diagram encodes ordering only. It does not encode cost, and the
distinction is the subject of the paragraph that follows.

{{dia:decisiontree}}

This section ranks measurements by the marginal predictive value defined in {{ref:s-marginal-predictive-value-each}}, and that
is not the same thing as a procurement optimum. No cost enters the ladder, and neither does
maintenance, calibration burden, instrument reliability, compliance value, temporal or spatial
coverage, nor the consequence of a decision made on the output. What follows therefore **informs**
procurement rather than optimising it: it says which measurement this model can use most, not
which purchase a programme should make once its own costs and obligations are counted. The
distinction matters most where the two could diverge, and a reference-grade instrument is the
clearest case: no rung of the ladder priced one, the measurement-design argument below favours it,
and {{ref:ch-kandy-setting-record-stakes}} notes that it costs tens of thousands of dollars to install.

**Take the free data first.** Terrain, roads, land cover, vegetation, night lights, population,
reanalysis meteorology and satellite retrievals cost nothing and are available for every city.
Together they buy {{claim:step.geography}} per cent on the ladder, comparable to the first
instrument a city could purchase. A programme that has not exhausted them is leaving the cheapest
available improvement unused.

Then buy according to the group of cities the target belongs to, not according to the global
average.

{{fig:acquisition}}

Pooled across the panel, a regional background station is the largest single gain at
{{claim:step.bud2_bud3}} per cent and two local sensors buy {{claim:step.bud0c_bud1}} per cent.
Within the deep tropical band, which is the band Kandy belongs to, the ordering reverses: local
sensors buy {{claim:maiac.deep_tropical_first2}} per cent against
{{claim:maiac.deep_tropical_background}} per cent for the background, a local advantage of
{{claim:maiac.deep_tropical_local_advantage}} times.

For Kandy specifically, therefore, **the first purchase is a local observation rather than a
regional one**. {{ref:s-recommendation-inverts-tropics}} shows that conclusion survives a paired interval over cities on the
clean satellite stream, favouring local sensors in {{claim:inv.maiac.frac_cities}} per cent of
the band, and that it does **not** survive on the contaminated stream.

The scope of that recommendation should be stated exactly, because it is the sentence most likely
to be lifted out of this thesis. What is established is that **within this panel, the
deep-tropical group is the closest available analogue to Kandy, and within that group a local
observation outranks the background stand-in.** It is not established that tropical cities in
general should buy local monitors first. The group contains thirteen cities, band travels with
instrument class and five other things, and {{ref:s-recommendation-inverts-tropics}} sets out why a latitude label is not a
mechanism. A city that resembles Kandy in the ways this panel can measure should read the band
row; a city that does not has been given a method for pricing its own options, which is the more
transferable product of the two.

**And the ordering holds for one loss, not for all of them.** {{ref:s-ordering-under-four-loss}} re-scores the ladder
under four scoring rules. Under daily and absolute error the local advantage is
{{claim:loss.inv.rmse}} and {{claim:loss.inv.mae}} points. On days in the observed top decile it
is {{claim:loss.inv.tail}} points and on exceedance at the World Health Organization guideline
{{claim:loss.inv.exceedance}} points
[{{claim:loss.inv.exceedance.lo}}, {{claim:loss.inv.exceedance.hi}}], both favouring the
background proxy, with the exceedance interval excluding zero. **A programme whose purpose is a
daily city-mean field should buy the local observation first. A programme whose purpose is
exceedance detection or health alerting should not**, and the background series is worth
{{claim:loss.bg.tail}} per cent on episode days, its largest value under any loss. {{ref:ch-kandy-setting-record-stakes}} names
both purposes, so the ordering has to be stated with its loss attached and not as a single
recommendation.

Two separate arguments then point at a reference-grade instrument, and they should not be
merged. The ladder measured two low-cost sensors, so it establishes that a local observation
outranks a regional one in this band. It does not establish the value of a reference monitor,
which was never a rung. The case for making that local observation reference-grade stands on its own as a
measurement-design argument. A reference instrument would settle the level discrepancy of
{{ref:s-checks-kandy-carry-weight}}, where three of four independent records sit below the model and the one that matches
carries an undocumented instrument. It would also anchor the calibration of any low-cost sensors
deployed afterwards, against which their performance can be assessed on a published protocol
[@Duvall2021]. That case is strong, and the
{{claim:maiac.deep_tropical_first2}} per cent figure is not evidence for it.

Do not expand the local network as a way of improving this model, and the redundancy starts
earlier than the ladder's rungs suggest. {{ref:s-marginal-predictive-value-each}} sweeps the station count from one to
eight: a single station buys {{claim:stn.one_gain}} per cent, the second adds
{{claim:stn.second_adds}} percentage points paired within city, and no count between two and
eight beats one station by more than {{claim:stn.max_extra}}. **For a daily city mean under this
model, on networks sited as these are, one local observation captures essentially everything a
further local observation could add**, which makes this the most estimator-robust result in the
study. The qualifiers are load-bearing and belong inside the sentence rather than after it: the
quantity is a daily city mean and not an episode or an exceedance, the model is this one, and the
stations sit where each city's programme happened to put them. {{ref:s-ordering-under-four-loss}} shows the finding
surviving three further losses, including the two that ask about episodes. Declining to buy something is also the only
recommendation here whose cost consequence is unambiguous, since no cost model is needed to
price an instrument that is not purchased.

Two qualifications travel with it. This concerns monitors as networks actually place them, and
whether placing them deliberately across land-use contrast changes the spatial picture is a
separate question, which {{ref:s-six-negative-results-their}} tests on the panel's own dense networks. And a pair buys something the ladder does not score: a second sensor is what
makes a between-sensor comparison possible, which is how the calibration checks of {{ref:s-checks-kandy-carry-weight}} were
obtained at all. The advice is that a second station does not improve the model, not that it is
worthless.

{{tbl:T9_1}}
