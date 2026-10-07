## Deliberate siting, tested on the dense networks {#s-deliberate-siting-tested-dense}

Every null in {{ref:s-six-negative-results-their}} was measured on networks sited for compliance and access, while the
land-use regression studies that report high coefficients of determination site their monitors
across land-use contrast on purpose [@Hoek2008]. The null could therefore be a property of how the
panel's networks were sited rather than of the information available to a city without monitors.
**That is testable without a new instrument.** Every city with a dense network can be made into
both designs by choosing which of its own stations to fit on, so the question is answerable on
{{claim:site.cities}} cities and {{claim:site.stations}} stations at no cost beyond computation.

Four fitting subsets were drawn from each city, the same model fitted on each, and every one
scored against stations held out of it. A subset chosen across the covariate space reaches a
median rank correlation of {{claim:site.rho_deliberate}} against
{{claim:site.rho_convenience}} for one chosen the way compliance networks are sited, which looks
decisive and is not.

**Paired within city, deliberate siting scores {{claim:site.paired_median}} against convenience
siting**, with an interval of {{claim:site.paired_lo}} to {{claim:site.paired_hi}}, and it wins
in {{claim:site.wins}} of {{claim:site.cities}} cities. Fewer than half.

The apparent advantage is the difference-of-medians artefact again. The gap between the two
medians is {{claim:site.diff_of_medians}} while the paired median is negative, because the city
sitting at the median is not the same city in the two arms. {{ref:s-marginal-predictive-value-each}} records the same trap in
the station-count sweep, and on both occasions the difference of medians was the flattering
reading. Reporting it here would have claimed that deliberate siting nearly doubles spatial skill.

The trap is easier to see than to describe, and it has caught this project more than once, so
{{fig:pairedtrap}} draws the same experiment both ways. On the left every city is a line from its
convenience score to its deliberate score. The lines cross in both directions and the two medians
still sit well apart, because a different city is at the middle of each column. On the right the
same cities become differences, and the distribution sits across zero.

{{fig:pairedtrap}}

**The robustness check could not be run on this panel.** Scoring every method against one common
held-out set would remove the confound that each design leaves a different remainder. On this
panel it is arithmetically impossible: the median city has twelve stations, so a held-out third is
{{claim:site.fixed_median_held}}, and a rank correlation on that many points can only take values
{{claim:site.fixed_quantisation}} apart. Every paired median collapsed to exactly zero. The check
was run and returned nothing, and that is a limit of the panel rather than a confirmation.

The registered spatial learning curve of {{ref:s-what-stations-buy-map}} supplied the fixed
design this panel could not. It restricted itself to the densest networks, held out at least ten
sites or a third of each network, whichever was larger, and compared fitting sites chosen to span
the covariates with sites chosen at random at each station count. Most of its full-record cities
are scored on exactly ten held-out sites, so each per-city rank correlation is itself noisy. Its
registered siting statistic was reported as exactly zero with a zero-width interval, which was an
error of construction and not a measurement: the summary pooled every estimator, including those
that never use the fitting stations and therefore differ between designs by exactly zero. Computed
for kriging alone, deliberate minus random siting is:

| frame | three stations | five stations | eight stations |
|---|---:|---:|---:|
| registered, one-year records | {{claim:v2.curve.reg.x5_e3_k3.median}} [{{claim:v2.curve.reg.x5_e3_k3.lo}}, {{claim:v2.curve.reg.x5_e3_k3.hi}}] | {{claim:v2.curve.reg.x5_e3_k5.median}} [{{claim:v2.curve.reg.x5_e3_k5.lo}}, {{claim:v2.curve.reg.x5_e3_k5.hi}}] | {{claim:v2.curve.reg.x5_e3_k8.median}} [{{claim:v2.curve.reg.x5_e3_k8.lo}}, {{claim:v2.curve.reg.x5_e3_k8.hi}}] |
| full records | {{claim:v2.curve.full.x5_e3_k3.median}} [{{claim:v2.curve.full.x5_e3_k3.lo}}, {{claim:v2.curve.full.x5_e3_k3.hi}}] | {{claim:v2.curve.full.x5_e3_k5.median}} [{{claim:v2.curve.full.x5_e3_k5.lo}}, {{claim:v2.curve.full.x5_e3_k5.hi}}] | {{claim:v2.curve.full.x5_e3_k8.median}} [{{claim:v2.curve.full.x5_e3_k8.lo}}, {{claim:v2.curve.full.x5_e3_k8.hi}}] |

Every interval spans zero, and the registered verdict, that siting by design does not beat random
siting by a resolvable amount, stands with intervals that now mean something. The two tests are
separate: the one above compares subsets of the panel's networks under one model, and the curve
compares fitting designs under a fixed held-out set. They agree.

What this establishes is bounded in the same way as the nulls of {{ref:s-six-negative-results-their}}. The interval does
not exclude an advantage as large as {{claim:site.paired_hi}}, so deliberate siting is
undetectable here rather than refuted. What it removes is the easy explanation: on these
networks, the spatial null does not look like an artefact of where the stations happen to stand.
