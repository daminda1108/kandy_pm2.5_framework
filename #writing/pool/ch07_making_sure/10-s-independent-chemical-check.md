## An independent chemical check {#s-independent-chemical-check}

The decomposition assumes that the regional background is aged air arriving from outside the
basin and the local increment is fresher material generated inside it. That assumption is
load-bearing and had never been tested against composition.

{{fig:chemistry}}

Classifying air-mass origin by back-trajectory sector, which is independent of the composition
product used to measure it [@Keller2021], continental air is measurably more secondary-rich and therefore more
aged than marine air: {{claim:chem.sec_frac.IGP_E_India}} against
{{claim:chem.sec_frac.SW_marine}}. That is the ordering the decomposition requires and it is the
first chemical support the construction has.

A second registered prediction was refuted usefully. Recirculated local air was expected to be
the freshest, and it is not, because stagnation gives local precursors time to age in place. The
consequence is that treating the local increment as fresh primary aerosol is too simple, and
{{ref:s-measurement-would-settle-most}} lists the composition measurement that would settle it.

### Three chemical tests and their outcomes {#s-three-chemical-tests-their}

Composition is the one axis on which this model makes a claim it does not model. That invites a
deeper test, and three were run. **Two returned nothing usable, and the reasons differ in a way
worth recording.**

**Does composition explain what latitude band only labels?** The test was designed when the
discovery panel appeared to show the ordering of the ladder reversing in the deep tropics, a
result since retracted ({{ref:s-marginal-predictive-value-each}}). Latitude band was then treated
as a stratifying label standing in for some physical cause, and a chemical cause was a candidate: a city whose particulate is mostly secondary is chemically a regional problem, so a
background observation should be worth more there and a local monitor less. That direction was
fixed in a script committed four days before any correlation was computed, which is why it could
be tested one-sided. It was pre-registered with its detection limit before the analysis ran.

The result is undetectable at this power. All {{claim:chem.mech.undetectable}} confirmatory
hypotheses return correlations far below what the design could see: the largest is
{{claim:chem.mech.largest_rho}} against a detection limit of {{claim:chem.mech.mde}}. That is not
a near miss, it is an order of magnitude short.

The reason is worth more than the result. The registration expected
{{claim:chem.mech.registered_n}} cities and the analysis scored {{claim:chem.mech.n}}, because
**controlling for band removed the cities that carried no band**, which in the frame used at the
time were exactly the cities of the Chinese national network. Those cities have since been assigned
to their bands, so the exclusion reflects the frame of the time rather than a property of the
network. The registered result stands as computed. The deviation is what makes the following table
possible, and the table is the finding:

| group | cities | correlation of composition with the acquisition advantage |
|---|---:|---:|
| pooled | {{claim:chem.cluster.pooled.n}} | {{claim:chem.cluster.pooled.rho}} |
| excluding the single network | {{claim:chem.cluster.banded.n}} | {{claim:chem.cluster.banded.rho}} |
| that network alone | {{claim:chem.cluster.single_network.n}} | {{claim:chem.cluster.single_network.rho}} |

**A correlation of {{claim:chem.cluster.pooled.rho}} survives in neither group on its own.** It
is produced entirely by the gap between two clusters that differ in network, instrument class and
country as well as in chemistry. This is the confound of {{ref:s-three-confounds-pooled-numbers}} reappearing wearing a
chemical variable's name, and the only reason it was caught is that the registered design
controlled for band rather than pooling.

Is the split chemically coherent species by species? The decomposition asserts that the
background is aged and the increment fresher. Chemistry orders the species without ambiguity:
black carbon is emitted directly and has no secondary source, so it is the purest available
tracer of fresh local material, while sulphate forms over hours to days and is the purest tracer
of aged regional material. Applying one common estimator to each species predicts that the local
fraction of black carbon should exceed that of sulphate.

It does not: {{claim:chem.species.f_black_carbon}} against {{claim:chem.species.f_sulphate}}.
**That reversal is not reported as a refutation, because the test does not work.** Dust and sea
salt act as negative controls, since an inland valley has no local source of either and their
true local fraction is near zero. The estimator returns {{claim:chem.species.f_dust}} for dust
and {{claim:chem.species.f_sea_salt}} for sea salt, the two highest values of any species. An
estimator that ranks material with no local source above the purest local tracer is measuring
something other than local origin, and what it is measuring is episodic temporal variability:
dust and sea salt arrive in transport events and are the most episodic species present.

**The species prediction is therefore untested rather than refuted.** Reporting the reversal as a
chemical result would be reporting an instrument failure as a finding. The controls were read after the run rather than declared before
it, which is a weakness in the design and not a defence of it.

What an intervention could remove. The third attempt is the one that works, and it repairs a
claim {{ref:s-partition-constraint-rather-than}} withdraws. With the local share and the secondary share both known, the
locally emitted primary share is bounded from both directions without further assumption. At
Kandy it lies between **{{claim:chem.intervention_lo}} and {{claim:chem.intervention_hi}} per
cent** of concentration. The lower figure is material that is both local and primary, and
responds immediately to local emission control. The upper figure is the whole local increment, so it moves with the local fraction across the
choices examined in {{ref:s-partition-constraint-rather-than}}, and it requires every locally
formed secondary particle to disappear as well. The gap between them
is precisely what cannot be resolved without speciated measurement in the city.
