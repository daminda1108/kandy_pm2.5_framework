## The partition, a bound under a non-negativity constraint {#s-partition-constraint-rather-than}

The decomposition is only useful to a decision if the split between local and regional is
credible, and for most of this project's history it was not. The value was taken from source
apportionment literature and sat near a quarter.

The argument that replaced it is short. Local sources emit continuously, and rain changes removal
rather than emission, so at an emitting location some locally generated material is present at
every hour. The decomposition's increment is then required to be non-negative, the background can
never reach the total, and **a background at or above the total is not an unusual hour but an
over-estimated background**. Since *B* is flat within a day, the constraint has a closed form: cap
each day at (1 − *F*~min~) times that day's minimum hourly total. In the production code the day is
a UTC day, which runs from 05:30 to 05:29 local time and therefore splits the Kandy night between
two days; the consequence is quantified below.

**This is a non-negative local-contribution constraint, and it should be called that rather than a
physical theorem.** Continuous emission is a statement about sources; *T* − *B* is a statement about
a constructed decomposition, and the two are not the same object. Transport, mixing, deposition,
secondary formation and a background that is itself built rather than measured all sit between
them, so continuous emission does not by itself prove that this particular residual must be
positive in every hour. What it does is make a negative residual far more readily explained by an
over-estimated background than by a real state of the atmosphere, which is enough to justify the
constraint as a modelling choice. It is imposed on those grounds, and the rest of
{{this:s-partition-constraint-rather-than}} reports how much the resulting fraction moves when the
choice is varied.

Before the constraint, the background exceeded the total in
{{claim:field.precap_excess_lo}} to {{claim:field.precap_excess_hi}} per cent of hours, averaging
{{claim:field.precap_excess_mean}}. In each such hour the field rendered flat and reported a zero
local fraction at the traffic core. After the constraint the residual is at worst
{{claim:field.postcap_excess_max}} per cent in any year, and every remaining case is an hour
where the anchor itself returned a negative total, which no constraint on the background can
repair.

Across the anchored years the local fraction is **{{claim:partition.f}}**, ranging
{{claim:partition.f_lo}} to {{claim:partition.f_hi}}.

**This is a property of the decomposition, not a measured share.** Under the baseline
specification the local increment accounts for {{claim:partition.f}} of the modelled
concentration. The fraction ranges from {{claim:v2.f.cap_min}} to {{claim:v2.f.cap_max}} under the
tested choices of day boundary (local or UTC) and daily-floor statistic (the single lowest hour or
a robust low statistic), and reaches {{claim:field.f_form_roll48}} when the background is
estimated over a 48-hour window. These values describe the sensitivity of the result to how the
decomposition is specified; they are not a confidence interval for the true locally emitted
fraction of PM2.5. It is also a function of the anchor's daily amplitude, because the cap
binds at the daily minimum of *T*. And it is a decomposition of modelled concentration, not a
source apportionment: the local increment contains locally formed secondary aerosol and excludes
regionally formed aerosol, so it is not established that removing every local source would remove
half the concentration. {{ref:s-partition-detail}} gives what sets the number, its sensitivity to
each choice, and the bound on the locally emitted primary share that replaces the intervention
claim.
